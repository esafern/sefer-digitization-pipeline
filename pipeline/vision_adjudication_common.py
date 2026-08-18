# [PRODUCTION] Shared crop/cache/JSON-recovery/retry machinery for this
# project's Gemini vision-adjudication scripts: pipeline/verify_corrections_
# vision.py, tools/verify_witness_vision.py, and tools/verify_flagged_
# candidates_vision.py (which already reused verify_corrections_vision.py's
# functions directly rather than duplicating them, per its own module
# docstring).
#
# Extracted 2026-08-17 (revalidation/refactor audit round 4), picking up an
# opportunity round 3 (2026-08-16) identified and deliberately deferred: a
# live budget-sensitive Gemini job was running in the main checkout at the
# time, and this module's main client touches verify_corrections_vision.py,
# the file that job most plausibly depended on - a structural refactor of a
# live paid-API script shouldn't be attempted blind. No such job is running
# this round.
#
# Round 3 also found DIRECT, CONCRETE PROOF the duplication this module
# removes was already causing drift, not just theoretical risk: the
# missing-`prompt_hash` cache-key bug (CLAUDE.md Lesson 12) had already been
# found and fixed TWICE independently in two of these files (verify_
# corrections_vision.py 2026-08-14, propose_punctuation_part1.py 2026-08-16)
# before round 3 found it a THIRD time, still present, in verify_witness_
# vision.py's own hand-maintained copy. A second, independent instance of the
# same drift class was found in THIS round: verify_flagged_candidates_
# vision.py's own `genai.Client(...)` construction was missing the explicit
# request-timeout fix (`http_options=types.HttpOptions(timeout=60000)`)
# already applied to verify_corrections_vision.py and verify_witness_vision.py
# after a 2026-08-06 incident where a hung call blocked a run for 20+ minutes
# at zero CPU with no retry ever triggering. Routing all three scripts'
# client construction through this module's `make_client()` closes that gap
# at its root instead of as a one-off patch.
#
# Deliberately NOT extracted here: each script's own PROMPT_TEMPLATE (the
# actual question wording differs per script - corrections asks "DocAI raw
# reading vs currently adjudicated text", witness asks "DocAI vs Tesseract
# reading", each with its own None-side handling) and each script's own
# cache table NAME/SCHEMA details beyond what's genuinely identical
# (corrections_cache carries a `model` provenance column that witness_cache
# never had - a real, deliberate difference, controlled here via
# `has_model_column` rather than papered over). What IS identical byte-for-
# byte across every call site is extracted: sanitize_json/
# unescape_json_fragment (JSON-escape recovery), crop_pdf_bounding_box (scan
# cropping), a cache-table init/migrate/get/put factory keyed the way every
# one of these caches must be keyed (crop_hash + word_a + word_b +
# context_hash + prompt_hash, CLAUDE.md Lesson 12), and the model-fallback/
# retry/backoff loop around the actual Gemini call.
#
# Every function here is parameterized (db path, table name, prompt hash
# passed explicitly) rather than reading module-level globals, so each
# caller's own CACHE_DB/PROMPT_HASH module attributes remain the single
# source of truth for that script - including staying monkeypatchable in
# tests exactly as before this extraction (a caller module's thin wrapper
# function reads its own global at call time and passes it in here).
import hashlib
import sqlite3
import time
import re

import fitz  # PyMuPDF
from google import genai
from google.genai import types


def sanitize_json(text):
    # Gemini occasionally emits invalid JSON escapes (e.g. \' around a
    # geresh); strip a backslash unless it precedes a valid JSON escape
    # character.
    return re.sub(r'\\(?!["\\/bfnrtu])', '', text)


_JSON_ESCAPES = {'"': '"', "\\": "\\", "/": "/", "b": "\b", "f": "\f",
                 "n": "\n", "r": "\r", "t": "\t"}


def unescape_json_fragment(s):
    # A response only reaches a lenient field-by-field extractor because SOME
    # gershayim in it were emitted raw; the same response routinely escapes
    # OTHER occurrences correctly as \", and a regex capture returns both
    # verbatim. Returning the group as-is therefore bakes a literal backslash
    # into the data wherever the model got it right - e.g. 'כ\"ה' where the
    # text is 'כ"ה'. A raw unescaped " has no backslash to match and is left
    # alone; \uXXXX is not handled (no observed case needs it and it's
    # unlikely in Hebrew source text emitted as raw UTF-8, not escapes).
    return re.sub(r"\\(.)", lambda m: _JSON_ESCAPES.get(m.group(1), m.group(1)), s, flags=re.DOTALL)


def crop_pdf_bounding_box(doc, page_num_1indexed, bbox, padding=0.02, dpi=300):
    # Per CLAUDE.md Lesson 14, a crop that clips its own anchor word can
    # silently invert a reading - the padding argument is load-bearing, not
    # cosmetic; callers that need a wider margin (e.g. a band-estimate crop
    # from a coarser locator) pass a larger value explicitly.
    page = doc.load_page(page_num_1indexed - 1)
    rect_page = page.rect
    width, height = rect_page.width, rect_page.height

    xmin = max(0.0, bbox["x1"] - padding) * width
    ymin = max(0.0, bbox["y1"] - padding) * height
    xmax = min(1.0, bbox["x2"] + padding) * width
    ymax = min(1.0, bbox["y2"] + padding) * height

    crop_rect = fitz.Rect(xmin, ymin, xmax, ymax)
    pix = page.get_pixmap(clip=crop_rect, dpi=dpi)
    return pix.tobytes("png")


def make_client(api_key, timeout_ms=60000):
    # Explicit request timeout: a hung call (observed 2026-08-06 - one crop's
    # request never returned and never raised, blocking a whole run for 20+
    # minutes at zero CPU with no retry ever triggering, since the retry
    # logic only fires on a caught exception) needs to fail loudly so the
    # retry/backoff loop can actually run instead of hanging forever.
    return genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=timeout_ms))


_NONE_SENTINEL = "\x00NONE\x00"  # word_a/word_b is NOT NULL; opcode delete/insert
                                  # legitimately has one side as None (e.g. "X" vs
                                  # nothing) - coerce rather than relax the schema.


def _cache_columns_sql(has_model_column):
    model_col = "model TEXT, " if has_model_column else ""
    return (
        "crop_hash TEXT NOT NULL, word_a TEXT NOT NULL, word_b TEXT NOT NULL, "
        f"context_hash TEXT NOT NULL, prompt_hash TEXT NOT NULL, {model_col}"
        "decision_json TEXT, PRIMARY KEY (crop_hash, word_a, word_b, context_hash, prompt_hash)"
    )


def init_cache_table(db_path, table_name, prompt_hash, has_model_column=True):
    """Create `table_name` in the sqlite database at `db_path` if it doesn't
    exist yet, keyed on (crop_hash, word_a, word_b, context_hash,
    prompt_hash) - every component of "the question" a cached decision is an
    answer to (CLAUDE.md Lesson 12: a cache key must cover everything that
    changes the right answer, not just the expensive part - crop-only
    (fixed 2026-08-05), no context_hash (fixed 2026-08-10), and no
    prompt_hash (fixed 2026-08-14, then again 2026-08-16 in a third sibling
    script) were each a real, confirmed bug in this project, not
    hardening). Also migrates a pre-prompt_hash 4-column schema into today's
    5-column keyed schema, back-filling the given prompt_hash rather than
    dropping existing rows (a fully regenerable cache is one thing; these
    rows are real, already-paid-for Gemini answers). Idempotent - safe to
    call on every run.
    """
    assert re.fullmatch(r"[a-z_]+", table_name), \
        f"table_name must be a plain lowercase identifier, got {table_name!r}"
    conn = sqlite3.connect(db_path)
    # WAL mode lets readers and the writer proceed concurrently instead of
    # blocking on SQLite's default rollback-journal lock.
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({_cache_columns_sql(has_model_column)})")
    _migrate_add_prompt_hash(conn, table_name, prompt_hash, has_model_column)
    conn.commit()
    conn.close()


def _migrate_add_prompt_hash(conn, table_name, prompt_hash, has_model_column):
    cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table_name})")}
    if "prompt_hash" in cols:
        return
    old_table = f"{table_name}_pre_prompt_hash"
    conn.execute(f"ALTER TABLE {table_name} RENAME TO {old_table}")
    conn.execute(f"CREATE TABLE {table_name} ({_cache_columns_sql(has_model_column)})")
    if has_model_column:
        conn.execute(
            f"INSERT INTO {table_name} "
            "(crop_hash, word_a, word_b, context_hash, prompt_hash, model, decision_json) "
            f"SELECT crop_hash, word_a, word_b, context_hash, ?, NULL, decision_json FROM {old_table}",
            (prompt_hash,),
        )
    else:
        conn.execute(
            f"INSERT INTO {table_name} "
            "(crop_hash, word_a, word_b, context_hash, prompt_hash, decision_json) "
            f"SELECT crop_hash, word_a, word_b, context_hash, ?, decision_json FROM {old_table}",
            (prompt_hash,),
        )
    n = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    print(f"  cache migrated to prompt-hash-keyed schema: {n} row(s) carried over "
          f"under prompt_hash {prompt_hash} (old table kept as {old_table})")


def get_cached_decision(db_path, table_name, prompt_hash, crop_bytes, word_a, word_b, context):
    crop_hash = hashlib.sha256(crop_bytes).hexdigest()
    context_hash = hashlib.sha256(context.encode("utf-8")).hexdigest()
    conn = sqlite3.connect(db_path, timeout=10.0)
    row = conn.execute(
        f"SELECT decision_json FROM {table_name} WHERE crop_hash=? AND word_a=? "
        "AND word_b=? AND context_hash=? AND prompt_hash=?",
        (crop_hash, word_a or _NONE_SENTINEL, word_b or _NONE_SENTINEL, context_hash, prompt_hash),
    ).fetchone()
    conn.close()
    return row[0] if row else None


def put_cached_decision(db_path, table_name, prompt_hash, crop_bytes, word_a, word_b, context,
                         decision_json, model=None, has_model_column=True):
    crop_hash = hashlib.sha256(crop_bytes).hexdigest()
    context_hash = hashlib.sha256(context.encode("utf-8")).hexdigest()
    conn = sqlite3.connect(db_path, timeout=10.0)
    if has_model_column:
        conn.execute(
            f"INSERT OR REPLACE INTO {table_name} "
            "(crop_hash, word_a, word_b, context_hash, prompt_hash, model, decision_json) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (crop_hash, word_a or _NONE_SENTINEL, word_b or _NONE_SENTINEL, context_hash,
             prompt_hash, model, decision_json),
        )
    else:
        conn.execute(
            f"INSERT OR REPLACE INTO {table_name} "
            "(crop_hash, word_a, word_b, context_hash, prompt_hash, decision_json) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (crop_hash, word_a or _NONE_SENTINEL, word_b or _NONE_SENTINEL, context_hash,
             prompt_hash, decision_json),
        )
    conn.commit()
    conn.close()


def _retry_loop(call_fn, models_to_try, max_retries):
    """Try call_fn(model_name) for each model/attempt with exponential backoff
    on 503/429. Returns the result of the first successful call. Raises
    RuntimeError if every model/attempt combination fails.

    Extracted so image-based adjudicate_with_retry() and text-only callers
    (propose_punctuation_part1.py) can share the same retry discipline without
    duplicating it.
    """
    last_err = None
    for model_name in models_to_try:
        for attempt in range(max_retries):
            try:
                return call_fn(model_name)
            except Exception as e:
                last_err = e
                print(f"  -> {model_name} attempt {attempt} failed: {e}")
                if "503" in str(e) or "429" in str(e):
                    time.sleep((2 ** attempt) * 2)
                else:
                    break
    raise RuntimeError(f"All models failed: {last_err}")


def adjudicate_with_retry(client, crop_bytes, prompt, cache_get, cache_put,
                           models_to_try=("gemini-3.6-flash", "gemini-3.5-flash"),
                           max_retries=3):
    """Generic model-fallback/retry/backoff loop shared by every caller: check
    `cache_get()` first (a zero-arg closure so each caller's own cache key
    shape - which fields it hashes - stays entirely caller-side); on a miss,
    try each model in `models_to_try` up to `max_retries` times, backing off
    only on 503/429 (a genuinely transient condition) and giving up
    immediately on anything else; on success, call `cache_put(response_text,
    model_name)` (also caller-supplied, so a table with no `model` column can
    just ignore the second argument) and return the raw response text.
    Raises RuntimeError if every model/attempt combination failed.

    gemini-2.5-flash was removed from the candidate list 2026-08-05:
    permanently 404s ("no longer available to new users"), not transient -
    it was silently eating a retry slot on every fallback path instead of
    ever actually helping.
    """
    cached = cache_get()
    if cached:
        print("  -> cache hit")
        return cached

    def call_fn(model_name):
        response = client.models.generate_content(
            model=model_name,
            contents=[
                types.Part.from_bytes(data=crop_bytes, mime_type="image/png"),
                prompt,
            ],
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        print(f"  -> live call to {model_name} ok")
        cache_put(response.text, model_name)
        return response.text

    return _retry_loop(call_fn, models_to_try, max_retries)


def parse_decision_lenient(text):
    """Field-by-field recovery for responses that are unparseable as strict
    JSON because a string value contains a literal, unescaped double-quote -
    e.g. Hebrew gershayim inside transcription_found/reasoning such as
    ז"ל or הרא"ש. json.loads (and sanitize_json's backslash fix) can't
    handle that: the model emits {"transcription_found": "ז"ל", ...} where
    the quote mark that's PART of the Hebrew text terminates the JSON string
    early, corrupting everything after it. selected_option is a closed
    vocabulary (A/B/NEITHER/UNCERTAIN) so it can't contain a stray quote;
    only transcription_found/reasoning need the lenient extraction.
    Raises ValueError if the expected shape isn't found at all.

    Moved here 2026-08-18 from tools/verify_witness_vision.py, where it was
    the only caller-local copy. verify_corrections_vision.py has a sibling
    extract_json_fields() with slightly different error semantics (returns
    None vs. raises) and a tighter selected_option regex (A/B/UNCERTAIN only,
    not NEITHER) — kept separate there since callers already depend on those
    semantics.
    """
    opt = re.search(r'"selected_option"\s*:\s*"([^"]*)"', text)
    conf = re.search(r'"confidence"\s*:\s*"?([0-9.]+)"?', text)
    transcription_str = re.search(
        r'"transcription_found"\s*:\s*"(.*?)"\s*,\s*\n?\s*"confidence"', text, re.DOTALL
    )
    transcription_null = re.search(r'"transcription_found"\s*:\s*null\s*,\s*\n?\s*"confidence"', text)
    reasoning = re.search(r'"reasoning"\s*:\s*"(.*)"\s*\n?}\s*$', text, re.DOTALL)
    if not (opt and (transcription_str or transcription_null) and reasoning):
        raise ValueError("lenient JSON recovery: expected fields not found")
    return {
        "selected_option": opt.group(1),
        "transcription_found": unescape_json_fragment(transcription_str.group(1)) if transcription_str else None,
        "confidence": float(conf.group(1)) if conf else None,
        "reasoning": unescape_json_fragment(reasoning.group(1)),
    }
