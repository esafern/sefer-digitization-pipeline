"""Propose editorial punctuation insertions for Part 1 klalim.

Scoped to Part 1 only (see PROJECT-STATUS.md 2026-08-10 "corpus-wide
punctuation pass" scoping). The print itself is punctuated very sparsely
(one existing mark roughly every 77 words); this proposes additional
sentence/clause-break points for readability, each to be inserted as a
literal "[.]" token (the same square-bracket editorial-insertion
convention already used for the 95 existing title/explanation-boundary
markers - see CLAUDE.md "Single source of truth").

This is a CANDIDATE-generation step only. It never touches part1.json.
Output (punctuation_candidates_part1.json) is meant for full human
read-through review via the review dashboard before anything is applied -
see apply_punctuation_decisions.py for the separate, deliberate promotion
step, mirroring apply_reviewer_decisions.py's existing pattern.

Usage:
  python3 propose_punctuation_part1.py                  # all 222 klalim
  python3 propose_punctuation_part1.py --klal 1 2 3      # specific klalim (pilot)
"""
import os
import sys
import json
import time
import hashlib
import sqlite3
import argparse

# genai itself is no longer imported here: client construction moved to
# vision_adjudication_common.make_client (see build_client below). `types` is
# still needed for the GenerateContentConfig on the call itself.
from google.genai import types

# UPGRADED 2026-08-16 (moved into tools/) from three bare relative filenames
# (cwd-dependent - worked only because this script always happened to be
# invoked from the repo root) to the REPO-anchored pattern every sibling
# script already uses, for the same robustness and consistency reasons -
# a bare filename silently writes/reads the wrong place if this is ever
# invoked with a different working directory.
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pipeline"))
import corpus_io as cio  # noqa: E402
import vision_adjudication_common as vac  # noqa: E402

CACHE_DB = os.path.join(REPO, "punctuation_cache.db")
PART1_PATH = cio.PART1_PATH
OUT_PATH = os.path.join(REPO, "punctuation_candidates_part1.json")

# FIXED 2026-08-17 (bug, code): gemini-2.5-flash was removed from this list.
# It has permanently 404'd since 2026-08-05 ("no longer available to new
# users") - not a transient condition - and was removed from the vision
# scripts' candidate list then, for the concrete reason that a dead model
# silently eats a retry slot on every fallback path instead of ever helping.
# This script's copy of the list was written independently and never got that
# fix: exactly the drift class this round's refactor exists to close, found a
# second time in this one file (see build_client below for the first).
MODELS_TO_TRY = ["gemini-3.6-flash", "gemini-3.5-flash"]


def build_client(api_key):
    """FIXED 2026-08-17 (bug, code): this was an inline
    `genai.Client(api_key=api_key)` in main(), missing the explicit
    request-timeout (`http_options=types.HttpOptions(timeout=60000)`) that
    verify_corrections_vision.py, verify_witness_vision.py and (as of the
    round-4 audit) verify_flagged_candidates_vision.py all carry after the
    2026-08-06 incident where a hung call blocked a run for 20+ minutes at
    zero CPU with no retry ever triggering - the retry loop below only fires
    on a caught exception, so a call that never returns and never raises
    hangs forever.

    This is the FOURTH independent instance of that same missing fix, and the
    first one outside the vision trio - direct evidence that the drift class
    CLAUDE.md Lesson 13 describes was not confined to the three files
    vision_adjudication_common.py was extracted from. Routed through that
    module's make_client() rather than patched inline again, so a fifth copy
    cannot be written."""
    return vac.make_client(api_key)


def init_cache():
    conn = sqlite3.connect(CACHE_DB)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, response_json TEXT)"
    )
    conn.commit()
    conn.close()


def get_cached(key):
    conn = sqlite3.connect(CACHE_DB, timeout=10.0)
    cur = conn.cursor()
    cur.execute("SELECT response_json FROM cache WHERE key = ?", (key,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None


def cache_response(key, response_json):
    conn = sqlite3.connect(CACHE_DB, timeout=10.0)
    conn.execute(
        "INSERT OR REPLACE INTO cache (key, response_json) VALUES (?, ?)",
        (key, response_json),
    )
    conn.commit()
    conn.close()


def migrate_add_prompt_hash(klalim):
    """Back-fill pre-2026-08-16 cache rows (keyed on klal_id + clean_text
    only) onto the new prompt-hash-keyed lookup, rather than silently
    orphaning them - the table schema itself doesn't change (still a single
    opaque `key` column), only what gets hashed into it, so this is a
    value-level re-key, not the rename-and-recreate verify_corrections_
    vision.py needed for its multi-column composite key. Back-filling
    asserts the surviving rows were produced under today's template, which
    holds here: this pipeline has only ever run as the `--klal 1 2 3` pilot
    named in the module docstring, so there is no history of a prior prompt
    edit to worry about, unlike verify_corrections_vision.py's case."""
    conn = sqlite3.connect(CACHE_DB, timeout=10.0)
    migrated = 0
    for klal in klalim:
        old_key = hashlib.sha256(
            f"{klal['klal_id']}|{klal['clean_text']}".encode("utf-8")
        ).hexdigest()
        row = conn.execute(
            "SELECT response_json FROM cache WHERE key = ?", (old_key,)
        ).fetchone()
        if row is None:
            continue
        new_key = cache_key_for(klal["klal_id"], klal["clean_text"], PROMPT_HASH)
        cur = conn.execute(
            "INSERT OR IGNORE INTO cache (key, response_json) VALUES (?, ?)",
            (new_key, row[0]),
        )
        # rowcount is per-statement (1 if inserted, 0 if the new key already
        # existed) - conn.total_changes would be WRONG here, it accumulates
        # across the whole connection and would over-report on every
        # iteration after the first real insert.
        if cur.rowcount:
            migrated += 1
    conn.commit()
    conn.close()
    if migrated:
        print(f"  cache migrated to prompt-hash-keyed lookup: {migrated} row(s) "
              f"carried over under prompt_hash {PROMPT_HASH}")


# Hoisted out of build_prompt() 2026-08-16 (round-2 follow-up: "propose_
# punctuation_part1.py's cache key doesn't cover the prompt text or model" -
# the identical gap already found and fixed in verify_corrections_vision.py
# 2026-08-14, see PROMPT_HASH there for the full precedent and incident this
# mirrors). Editing ANY character below (a constraint, the JSON shape, the
# instructions) changes PROMPT_HASH and correctly invalidates prior answers -
# without this, the same edit would have silently kept serving answers to the
# OLD question forever, exactly as verify_corrections_vision.py's template
# edit did before ITS prompt_hash fix (and only failed to cause real damage
# there because an unrelated schema change had already dropped every cached
# row two days earlier - see that file's history for why "it happened to be
# harmless once" is not evidence the gap doesn't matter).
PROMPT_TEMPLATE = """You are an editor preparing a critical edition of Yad Malachi
(R. Malachi ben Jacob HaKohen, Livorno 1766-7), a Rabbinic-Hebrew
halachic-methodology digest, for a modern digital library (Sefaria). The
original 1766 print is punctuated very sparsely - long unbroken runs of
dense Talmudic/halachic argument with no internal punctuation at all,
only an occasional mark and a closing colon at the very end.

Below is one klal's full text, word-by-word, each word prefixed by its
0-based index in "N:word" form. Read it as a fluent Rabbinic-Hebrew
reader would, and identify EVERY natural sentence or major clause
boundary that currently has NO punctuation mark (a period ".", colon ":",
comma "," or the literal token "[.]" is already a mark - do not propose a
boundary adjacent to one of those). For each boundary you find, report
the index of the word that should come AFTER the new mark (i.e. insert
before that word).

Be thorough - a typical run in this text is 30-80+ words with zero
internal breaks, and most of those genuinely contain several complete
sentences or major clauses (e.g. "X says Y. But Z asks:" is often one
unbroken run right now). Do not merely mark the single most obvious
break; find all of them. Do not propose a break at index 0.

This is for readability only - you are never changing, adding, or
removing any actual word, only marking where a modern reader would
expect a full-stop-equivalent pause. When in doubt between a period-like
full stop and a lighter break, prefer marking it (the human reviewer will
reject any that don't hold up).

Text:
{numbered_text}

Respond ONLY with JSON in this exact structure:
{{
  "insertions": [
    {{"before_word_index": <int>, "reasoning": "<brief, one sentence>"}},
    ...
  ]
}}
"""
PROMPT_HASH = hashlib.sha256(PROMPT_TEMPLATE.encode("utf-8")).hexdigest()[:16]


def build_prompt(numbered_text):
    return PROMPT_TEMPLATE.format(numbered_text=numbered_text)


def cache_key_for(klal_id, clean_text, prompt_hash):
    """PROMPT_HASH added 2026-08-16 to what's hashed - see PROMPT_TEMPLATE's
    comment for why. Deliberately NOT keyed on which model answered
    (MODELS_TO_TRY is a fallback chain, mirroring verify_corrections_
    vision.py's identical decision - keying on the model would evict a good
    cached answer whenever the primary model came back up)."""
    return hashlib.sha256(
        f"{klal_id}|{clean_text}|{prompt_hash}".encode("utf-8")
    ).hexdigest()


def propose_for_klal(client, klal):
    words = cio.words_of(klal)
    numbered = "\n".join(f"{i}:{w}" for i, w in enumerate(words))
    cache_key = cache_key_for(klal["klal_id"], klal["clean_text"], PROMPT_HASH)

    cached = get_cached(cache_key)
    if cached:
        print(f"  klal {klal['klal_id']}: cache hit")
        return json.loads(cached)

    prompt = build_prompt(numbered)

    def call_fn(model_name):
        response = client.models.generate_content(
            model=model_name,
            contents=[prompt],
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        data = json.loads(response.text)
        cache_response(cache_key, json.dumps(data, ensure_ascii=False))
        print(f"  klal {klal['klal_id']}: {model_name} ok, "
              f"{len(data.get('insertions', []))} proposed")
        return data

    return vac._retry_loop(call_fn, MODELS_TO_TRY, max_retries=3)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--klal", type=int, nargs="*", default=None,
                         help="specific klal_ids to run (pilot); default: all Part 1 (1-222)")
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is missing.")
    client = build_client(api_key)
    init_cache()

    # The Part-1 cut-off was a bare literal 222 here - a FOURTH copy of
    # PART1_MAX_KLAL that the 2026-08-15 hard-wired-value audit missed and
    # that tests/test_corpus_invariants.py's three-module check therefore
    # never covered. Same value today; now tied to the corpus like the others.
    part1 = [k for k in cio.load_part1(PART1_PATH) if k["klal_id"] <= cio.PART1_MAX_KLAL]

    # Against the FULL Part 1 set, not the --klal-filtered subset below - a
    # pre-migration cached row could be for any klal_id, not just whichever
    # ones this particular invocation is about to run.
    migrate_add_prompt_hash(part1)

    if args.klal:
        target_ids = set(args.klal)
        part1 = [k for k in part1 if k["klal_id"] in target_ids]

    if os.path.exists(OUT_PATH):
        with open(OUT_PATH, encoding="utf-8") as f:
            out = json.load(f)
    else:
        out = {}

    for klal in part1:
        result = propose_for_klal(client, klal)
        insertions = result.get("insertions", [])
        # basic sanity filter: valid index range, sorted, deduped
        words = cio.words_of(klal)
        seen = set()
        clean_insertions = []
        for ins in insertions:
            idx = ins.get("before_word_index")
            if not isinstance(idx, int) or idx <= 0 or idx >= len(words):
                continue
            if idx in seen:
                continue
            seen.add(idx)
            clean_insertions.append({
                "before_word_index": idx,
                "reasoning": ins.get("reasoning", ""),
                # anchor for apply-time drift detection (mirrors
                # apply_reviewer_decisions.py's snapshot_matches pattern) -
                # since this candidate list isn't regenerated by
                # rebuild_all.sh, a later klal edit could shift these
                # indices; the flanking words let the apply step notice.
                "word_before": words[idx - 1],
                "word_after": words[idx],
            })
        clean_insertions.sort(key=lambda x: x["before_word_index"])
        out[str(klal["klal_id"])] = clean_insertions

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    total = sum(len(v) for v in out.values())
    print(f"\nWrote {OUT_PATH}: {total} proposed insertions across {len(out)} klalim")


if __name__ == "__main__":
    main()
