#!/usr/bin/env python3
# [PRODUCTION] Vision-adjudicate the independent-witness queue (DocAI vs
# Tesseract disagreements on the reconstructed pages 24/37/40 - see
# verify_reconstruction_witness.py) the same way verify_corrections_vision.py
# adjudicates ordinary corrections: crop each item's bbox from the scan,
# send it to Gemini with surrounding raw-OCR context, and record a real
# confidence score + reasoning. This is a TRIAGE layer, same as corrections'
# vision pass - it does NOT record witness_choice decisions itself. A human
# still makes the final call via the dashboard; this just makes that call
# fast by front-loading the crop-reading work, the same relationship
# corrections_part1.json's vision flags already have to actual
# candidate_choice decisions.
#
# Output: reconstruction_witness_queue.json gains vision_selected/
# vision_transcription/vision_confidence/vision_reasoning per item - an
# additional, independent triage signal alongside the existing lexicon-based
# tier. (CORRECTED 2026-08-14: this used to also claim a vision_tier field;
# nothing ever wrote one - confirmed by grep against a completed 419/419
# run. Removed the false claim rather than adding the field just to match
# stale documentation - CLAUDE.md Lesson "General standing caution.")
#
# Usage: python3 verify_witness_vision.py [--page 24 37 40]
import argparse
import json
import os
import re
import sqlite3
import time
import hashlib

import fitz  # PyMuPDF
from google import genai
from google.genai import types

# Moved one level deeper (pipeline/ or tools/) 2026-08-16 - REPO now goes up
# two levels, not one, to keep resolving to the actual repo root where
# part1.json/docai_word_boxes/etc. live.
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_PATH = os.path.join(REPO, "berlin_square_corrected.pdf")
QUEUE_PATH = os.path.join(REPO, "reconstruction_witness_queue.json")
CACHE_DB = os.path.join(REPO, "witness_vision_cache.db")
DOCAI_DIR = os.path.join(REPO, "docai_word_boxes")

CONTEXT_WINDOW = 12  # raw docai tokens on each side, matching api_witness_context()
HEB = "אבגדהוזחטיכלמנסעפצקרשתךםןףץ"


def norm(s):
    return "".join(c for c in s if c in HEB)


# Hoisted out of adjudicate() so it can be hashed into the cache key - see
# init_cache() below. The per-item values (context/option_a_desc/
# option_b_desc) are substituted in at call time; everything else here is
# the fixed "question" every cached answer was an answer to. Mirrors
# pipeline/verify_corrections_vision.py's PROMPT_TEMPLATE/PROMPT_HASH
# precedent exactly (added there 2026-08-14, and to
# propose_punctuation_part1.py 2026-08-16) - editing ANY character below (a
# constraint, the JSON shape, the option wording) must change PROMPT_HASH
# and correctly invalidate prior answers.
PROMPT_TEMPLATE = """
You are an expert Talmudic and Rabbinic textual verification engine analyzing a Hebrew manuscript raster crop.

Surrounding raw OCR context (unverified, may include misreads on either side): "{context}"

Two independent OCR engines disagree about what is printed at the target position:
Option A (DocAI OCR reading): {option_a_desc}
Option B (Tesseract OCR reading): {option_b_desc}

CONSTRAINTS:
1. Perform Rabbinic acronym and semantic analysis using the surrounding context.
2. Recognize standard Rabbinic acronyms and abbreviations.
3. Do NOT mistake Rabbinic acronyms for the literal spelled-out Hebrew letter name when context indicates an abbreviation.
4. If NEITHER option matches the pixels precisely, transcribe what you actually see in "transcription_found" and set selected_option to "NEITHER".
5. Output "UNCERTAIN" only if the crop is illegible or too ambiguous to read at all.

Respond ONLY with JSON using this structure:
{{
  "selected_option": "A" or "B" or "NEITHER" or "UNCERTAIN",
  "transcription_found": "exact text visible in image",
  "confidence": 0.0 to 1.0,
  "reasoning": "contextual Rabbinic paleographic explanation"
}}
"""
PROMPT_HASH = hashlib.sha256(PROMPT_TEMPLATE.encode("utf-8")).hexdigest()[:16]


# ---------- cache: keyed on everything that changes the actual question
# asked (Lesson 12 - a crop-hash-only or word-pair-only key silently reuses
# a stale answer for a different question on the same crop). FIXED
# 2026-08-16: this table's key used to omit prompt_hash entirely - the
# exact gap already found and fixed in verify_corrections_vision.py
# (2026-08-14) and propose_punctuation_part1.py (2026-08-16), missed here
# in this third sibling script with the identical crop/adjudicate/cache
# shape. A future wording edit to PROMPT_TEMPLATE above would have
# silently kept serving pre-edit answers forever. Migrated, not dropped:
# existing rows are real, already-paid-for Gemini calls (419/419 per this
# module's own docstring). ----------
def init_cache():
    conn = sqlite3.connect(CACHE_DB)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS witness_cache ("
        "crop_hash TEXT NOT NULL, word_a TEXT NOT NULL, word_b TEXT NOT NULL, "
        "context_hash TEXT NOT NULL, prompt_hash TEXT NOT NULL, decision_json TEXT, "
        "PRIMARY KEY (crop_hash, word_a, word_b, context_hash, prompt_hash))"
    )
    _migrate_add_prompt_hash(conn)
    conn.commit()
    conn.close()


def _migrate_add_prompt_hash(conn):
    """Rebuild a pre-fix 4-column witness_cache into the 5-column
    prompt-hash-keyed schema, back-filling the CURRENT PROMPT_HASH rather
    than dropping every row - mirrors verify_corrections_vision.py's
    _migrate_add_prompt_hash exactly (see that function's docstring for the
    full reasoning). Back-filling is sound here: PROMPT_TEMPLATE above is
    unchanged from when this script was originally written - only the
    cache KEY is changing in this fix, not the question any existing row
    was an answer to."""
    cols = {r[1] for r in conn.execute("PRAGMA table_info(witness_cache)")}
    if "prompt_hash" in cols:
        return
    conn.execute("ALTER TABLE witness_cache RENAME TO witness_cache_pre_prompt_hash")
    conn.execute(
        "CREATE TABLE witness_cache ("
        "crop_hash TEXT NOT NULL, word_a TEXT NOT NULL, word_b TEXT NOT NULL, "
        "context_hash TEXT NOT NULL, prompt_hash TEXT NOT NULL, decision_json TEXT, "
        "PRIMARY KEY (crop_hash, word_a, word_b, context_hash, prompt_hash))"
    )
    conn.execute(
        "INSERT INTO witness_cache "
        "(crop_hash, word_a, word_b, context_hash, prompt_hash, decision_json) "
        "SELECT crop_hash, word_a, word_b, context_hash, ?, decision_json "
        "FROM witness_cache_pre_prompt_hash",
        (PROMPT_HASH,),
    )
    n = conn.execute("SELECT COUNT(*) FROM witness_cache").fetchone()[0]
    print(f"  cache migrated to prompt-hash-keyed schema: {n} row(s) carried over "
          f"under prompt_hash {PROMPT_HASH} (old table kept as "
          f"witness_cache_pre_prompt_hash)")


_NONE_SENTINEL = "\x00NONE\x00"


def get_cached(crop_bytes, word_a, word_b, context):
    crop_hash = hashlib.sha256(crop_bytes).hexdigest()
    context_hash = hashlib.sha256(context.encode("utf-8")).hexdigest()
    conn = sqlite3.connect(CACHE_DB, timeout=10.0)
    row = conn.execute(
        "SELECT decision_json FROM witness_cache WHERE crop_hash=? AND word_a=? "
        "AND word_b=? AND context_hash=? AND prompt_hash=?",
        (crop_hash, word_a or _NONE_SENTINEL, word_b or _NONE_SENTINEL, context_hash, PROMPT_HASH),
    ).fetchone()
    conn.close()
    return row[0] if row else None


def cache_put(crop_bytes, word_a, word_b, context, decision_json):
    crop_hash = hashlib.sha256(crop_bytes).hexdigest()
    context_hash = hashlib.sha256(context.encode("utf-8")).hexdigest()
    conn = sqlite3.connect(CACHE_DB, timeout=10.0)
    conn.execute(
        "INSERT OR REPLACE INTO witness_cache "
        "(crop_hash, word_a, word_b, context_hash, prompt_hash, decision_json) VALUES (?,?,?,?,?,?)",
        (crop_hash, word_a or _NONE_SENTINEL, word_b or _NONE_SENTINEL, context_hash,
         PROMPT_HASH, decision_json),
    )
    conn.commit()
    conn.close()


def crop_pdf_bounding_box(doc, page_num_1indexed, bbox, padding=0.02):
    page = doc.load_page(page_num_1indexed - 1)
    rect_page = page.rect
    width, height = rect_page.width, rect_page.height
    xmin = max(0.0, bbox["x1"] - padding) * width
    ymin = max(0.0, bbox["y1"] - padding) * height
    xmax = min(1.0, bbox["x2"] + padding) * width
    ymax = min(1.0, bbox["y2"] + padding) * height
    pix = page.get_pixmap(clip=fitz.Rect(xmin, ymin, xmax, ymax), dpi=300)
    return pix.tobytes("png")


def sanitize_json(text):
    return re.sub(r'\\(?!["\\/bfnrtu])', "", text)


_JSON_ESCAPES = {'"': '"', "\\": "\\", "/": "/", "b": "\b", "f": "\f", "n": "\n", "r": "\r", "t": "\t"}


def unescape_json_fragment(s):
    """Undo JSON string escape sequences (\\" -> ", \\n -> newline, etc.) in a
    raw regex-captured substring that was extracted WITHOUT going through
    json.loads. FIXED 2026-08-14: parse_decision_lenient used to return
    captured groups verbatim, which is wrong whenever the SAME response
    escaped some gershayim occurrences correctly (as '\\"') and left others
    raw (as '"') - the raw ones are why we're in this fallback at all, but
    the correctly-escaped ones need unescaping same as strict json.loads
    would do, and returning them verbatim left literal backslashes baked
    into the data. Confirmed real: klal 30 tok 750/835 and klal 75 tok 555's
    already-recovered `reasoning` fields had '\\"' (backslash+quote, two
    literal characters) where the correct text has a single '"' - e.g.
    'הרא\\"ש' instead of 'הרא"ש'. A raw unescaped '"' has no backslash to
    match, so it's untouched and stays correct; a properly-escaped '\\"'
    becomes '"'. Unrecognized backslash sequences drop the backslash,
    matching sanitize_json's existing behavior; \\uXXXX is not handled -
    no observed case needs it and it's unlikely in Hebrew source text."""
    return re.sub(r"\\(.)", lambda m: _JSON_ESCAPES.get(m.group(1), m.group(1)), s, flags=re.DOTALL)


def parse_decision_lenient(text):
    """Field-by-field recovery for responses that are unparseable as strict
    JSON because a string value contains a literal, unescaped double-quote -
    e.g. Hebrew gershayim inside transcription_found/reasoning such as
    ז"ל or הרא"ש. json.loads (and sanitize_json's backslash fix) can't
    handle that: the model emits {"transcription_found": "ז"ל", ...} where
    the quote mark that's PART of the Hebrew text terminates the JSON string
    early, corrupting everything after it. selected_option is a closed
    vocabulary (A/B/NEITHER/UNCERTAIN) so it can't contain a stray quote;
    only transcription_found/reasoning need the lenient extraction (and the
    unescape pass above). Raises ValueError if the expected shape isn't
    found at all (a genuinely different failure, not this bug).

    confidence and transcription_found are read leniently too (FIXED
    2026-08-14): confidence accepts an optionally-quoted number (a bare
    `0.95` previously required - a model that quotes it, e.g. `"0.95"`,
    silently produced `confidence: None` instead of erroring, which is
    worse than raising since it looks like a scored-but-uncertain item
    rather than a parse failure). transcription_found accepts a JSON
    `null` as well as a quoted string - a genuinely illegible crop is a
    normal, valid model answer, and treating it as ERROR discarded an
    otherwise-usable selected_option/confidence/reasoning for no reason."""
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


_dtoks_cache = {}


def dtoks_for_page(page):
    if page not in _dtoks_cache:
        toks = json.load(open(os.path.join(DOCAI_DIR, f"page_{page}.json"), encoding="utf-8"))
        _dtoks_cache[page] = [t for t in toks if norm(t["text"])]
    return _dtoks_cache[page]


def build_context(page, token_index):
    dtoks = dtoks_for_page(page)
    if token_index >= len(dtoks):
        return ""
    lo = max(0, token_index - CONTEXT_WINDOW)
    hi = min(len(dtoks), token_index + CONTEXT_WINDOW + 1)
    return " ".join(t["text"] for t in dtoks[lo:hi])


def adjudicate(client, crop_bytes, docai_reading, tesseract_reading, context):
    cached = get_cached(crop_bytes, docai_reading, tesseract_reading, context)
    if cached:
        print("  -> cache hit")
        return cached

    # Same lesson as verify_corrections_vision.py finding 7: when one side
    # is None (an 'insert' opcode - DocAI has NOTHING at this position but
    # Tesseract found real text), asking the model to pick between a real
    # reading and the literal string "None" is an unanswerable question it
    # will always resolve to UNCERTAIN. Describe what a missing DocAI
    # reading actually means instead.
    if docai_reading is None:
        option_a_desc = "(nothing - DocAI's OCR pass found no text at this position at all)"
    else:
        option_a_desc = f'"{docai_reading}"'
    option_b_desc = f'"{tesseract_reading}"' if tesseract_reading else "(nothing - Tesseract found no text here either)"

    prompt = PROMPT_TEMPLATE.format(context=context, option_a_desc=option_a_desc, option_b_desc=option_b_desc)
    models_to_try = ["gemini-3.6-flash", "gemini-3.5-flash"]
    max_retries = 3
    last_err = None
    for model_name in models_to_try:
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[types.Part.from_bytes(data=crop_bytes, mime_type="image/png"), prompt],
                    config=types.GenerateContentConfig(response_mime_type="application/json"),
                )
                print(f"  -> live call to {model_name} ok")
                cache_put(crop_bytes, docai_reading, tesseract_reading, context, response.text)
                return response.text
            except Exception as e:
                last_err = e
                print(f"  -> {model_name} attempt {attempt} failed: {e}")
                if "503" in str(e) or "429" in str(e):
                    time.sleep((2 ** attempt) * 2)
                else:
                    break
    raise RuntimeError(f"All models failed: {last_err}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", type=int, nargs="*", default=None)
    args = ap.parse_args()

    init_cache()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("GEMINI_API_KEY not set")
    client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=60000))

    data = json.load(open(QUEUE_PATH, encoding="utf-8"))
    queue = data["queue"]
    doc = fitz.open(PDF_PATH)

    n_done = n_err = 0
    for i, item in enumerate(queue):
        if args.page and item["page"] not in args.page:
            continue
        if not item.get("bbox"):
            continue
        context = build_context(item["page"], item["docai_token_index"])
        try:
            crop_bytes = crop_pdf_bounding_box(doc, item["page"], item["bbox"])
            print(f"[{i+1}/{len(queue)}] klal {item['klal_id']} page {item['page']} "
                  f"tok {item['docai_token_index']}: {item['docai_reading']!r} vs {item['tesseract_reading']!r}")
            decision_text = adjudicate(client, crop_bytes, item.get("docai_reading"), item.get("tesseract_reading"), context)
            try:
                decision = json.loads(decision_text)
            except json.JSONDecodeError:
                try:
                    decision = json.loads(sanitize_json(decision_text))
                except json.JSONDecodeError:
                    decision = parse_decision_lenient(decision_text)
        except Exception as e:
            print(f"  !! failed: {e}")
            decision = {"selected_option": "ERROR", "transcription_found": None, "confidence": None, "reasoning": str(e)}
            n_err += 1

        item["vision_selected"] = decision.get("selected_option")
        item["vision_transcription"] = decision.get("transcription_found")
        item["vision_confidence"] = decision.get("confidence")
        item["vision_reasoning"] = decision.get("reasoning")
        n_done += 1

    doc.close()
    with open(QUEUE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\nVision-adjudicated {n_done} item(s), {n_err} error(s). Wrote {QUEUE_PATH}")


if __name__ == "__main__":
    main()
