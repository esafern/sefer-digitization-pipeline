# [PRODUCTION] Crop each Part-1 correction candidate from the Berlin scan and ask
# Gemini (vision) to select between the DocAI raw reading and the final adjudicated
# text, recording a real confidence score + paleographic rationale. Scoped to the
# small candidate set from build_corrections_dataset.py instead of a full page
# scan. (It was originally written to mirror orchestrator.py's
# adjudicate_conflict_with_gemini; orchestrator.py was archived 2026-08-11 as
# dead code carrying 4 real bugs, so this is now the only live vision
# adjudicator - do not treat it as a copy of anything.)
#
# Crop/cache/JSON-recovery/retry machinery shared with tools/verify_witness_
# vision.py moved to vision_adjudication_common.py 2026-08-17 (revalidation
# round 4) - see that module's docstring for why (round 3 found the
# missing-prompt_hash cache-key bug, already fixed here and in
# propose_punctuation_part1.py, had to be independently re-fixed a THIRD time
# in verify_witness_vision.py's own hand-maintained copy of this same
# machinery - direct proof of the drift CLAUDE.md Lesson 13 warns about).
# sanitize_json/unescape_json_fragment/crop_pdf_bounding_box are re-exported
# here (not just imported privately) so `import verify_corrections_vision as
# vcv; vcv.unescape_json_fragment(...)` - the pattern tools/verify_flagged_
# candidates_vision.py and this file's own tests already use - keeps working
# unchanged.
import json
import os
import sys
import hashlib

import re

import fitz  # PyMuPDF

import corpus_io as cio
import vision_adjudication_common as vac
from vision_adjudication_common import (  # noqa: F401 - re-exported, see above
    normalize_selected_option,
    sanitize_json,
    unescape_json_fragment,
)


def extract_json_fields(text):
    # Fallback for a DIFFERENT failure mode than sanitize_json handles: the
    # response content itself is Hebrew text containing gershayim ("), and
    # Gemini sometimes emits that quote mark literally unescaped inside a
    # JSON string value (e.g. "transcription_found": "סי' כ"ה" - note the
    # unescaped " before ה) even in response_mime_type=application/json
    # mode. That's not a fixable single-character bug like the backslash
    # case; strict json.loads can't recover the intended string boundary.
    # The 4 fields are always emitted in the same fixed order per the
    # prompt, so extract each by matching up to the next known field key
    # (or the closing brace for the last one) instead of relying on the
    # embedded value having no stray quotes.
    def field(name, next_pattern):
        m = re.search(rf'"{name}"\s*:\s*"(.*?)"\s*,?\s*{next_pattern}', text, re.S)
        return unescape_json_fragment(m.group(1)) if m else None

    # Accept whatever the model wrote and normalise it, rather than matching
    # only the three literal forms - a compliant-in-substance answer like
    # "Option A" used to fail this regex entirely (2026-08-23; see
    # vision_adjudication_common.normalize_selected_option for the live case).
    _sel_raw = re.search(r'"selected_option"\s*:\s*"([^"]*)"', text)
    _sel = normalize_selected_option(_sel_raw.group(1)) if _sel_raw else None
    selected = _sel_raw if _sel else None
    transcription = field("transcription_found", r'(?="confidence")')
    # Optional quotes around the number: a model that emits "confidence": "0.95"
    # used to fall through to `return None` and be recorded as a hard ERROR,
    # discarding an otherwise-complete decision over its JSON type alone. Same
    # leniency verify_witness_vision.py's parse_decision_lenient got 2026-08-14.
    confidence = re.search(r'"confidence"\s*:\s*"?([\d.]+)"?', text)
    reasoning = field("reasoning", r'\}\s*$')

    if not (selected and confidence):
        return None
    return {
        "selected_option": _sel,
        "transcription_found": transcription,
        "confidence": float(confidence.group(1)),
        "reasoning": reasoning,
    }

# Moved one level deeper (pipeline/ or tools/) 2026-08-16 - REPO now goes up
# two levels, not one, to keep resolving to the actual repo root where
# part1.json/docai_word_boxes/etc. live.
REPO = cio.REPO
PDF_PATH = os.path.join(REPO, "berlin_square_corrected.pdf")
CANDIDATES_PATH = os.path.join(REPO, "corrections_candidates_part1.json")
OUT_PATH = os.path.join(REPO, "corrections_verified_part1.json")
CACHE_DB = os.path.join(REPO, "adjudication_cache.db")
DEMO_DATASET = cio.DEMO_DATASET_PATH

# Words of surrounding text sent to the model on EACH side of the disputed
# word, and the character-count fallback used only when word_index_in_final_
# text is missing/out of range (the pre-2026-08-10 behaviour, kept for that
# case alone - see the comment in main() for why a fixed head-of-klal slice
# was wrong as a general strategy). Named 2026-08-15: these were the bare
# literals 35 / 36 / 400, and the 35-vs-36 asymmetry (an exclusive slice end)
# reads like an off-by-one waiting to be "fixed" by the next person.
# Changing either value changes the prompt's context and therefore
# context_hash, which correctly invalidates every cached answer - i.e. a full
# re-run against the paid API. Do not adjust casually.
CONTEXT_WINDOW_WORDS = 35
FALLBACK_CONTEXT_CHARS = 400

# Crop geometry for the image the model adjudicates from. Named 2026-08-15;
# same cache warning as above and then some - both feed crop_hash, so any
# change re-crops every candidate and discards all 419 cached decisions.
# CROP_PADDING is a fraction of page width/height added around the token's own
# bbox; per CLAUDE.md Lesson 14 a crop that clips its own anchor word can
# silently invert a reading, so this margin is load-bearing, not cosmetic.
CROP_PADDING = 0.02
CROP_DPI = 300

# Hoisted out of adjudicate() 2026-08-14 so it can be hashed into the cache
# key - see init_cache(). The per-candidate values are substituted in at call
# time; everything else here is the fixed "question" every cached answer was
# an answer to. Editing ANY character below (a constraint, the JSON shape, the
# option wording) changes PROMPT_HASH and correctly invalidates prior answers.
PROMPT_TEMPLATE = """
You are an expert Talmudic and Rabbinic textual verification engine analyzing a Hebrew manuscript raster crop.

Surrounding Talmudic/Rabbinic Sentence Context: "{full_context}"

Evaluate the target raster crop against candidate strings:
Option A (DocAI raw OCR reading): {option_a_desc}
Option B (current adjudicated text): {option_b_desc}

CONSTRAINTS:
1. Perform Rabbinic acronym and semantic analysis using the surrounding sentence context.
2. Recognize standard Rabbinic acronyms and abbreviations.
3. Do NOT mistake Rabbinic acronyms for the literal spelled-out Hebrew letter name when context indicates an abbreviation.
4. Output "UNCERTAIN" if neither candidate maps deterministically to the pixel array.

Respond ONLY with JSON using this structure:
{{
  "selected_option": "A" or "B" or "UNCERTAIN",
  "transcription_found": "exact text visible in image",
  "confidence": 0.0 to 1.0,
  "reasoning": "contextual Rabbinic paleographic explanation"
}}
"""
PROMPT_HASH = hashlib.sha256(PROMPT_TEMPLATE.encode("utf-8")).hexdigest()[:16]


# Uses its own table (not the `cache` table the archived orchestrator.py wrote,
# which still sits in this same .db file) and keys on everything that can
# change the right answer: (crop_hash, word_a, word_b, context_hash,
# prompt_hash) - see vision_adjudication_common.init_cache_table for the last
# two. A bare crop_hash key is wrong here: the same crop gets re-cropped
# across sessions to answer different A/B comparisons as `clean_text` changes
# (fixes, reverts), and a crop_hash-only cache silently returns a decision
# for the *wrong* word pair - confirmed 2026-08-05: migrating the old table
# found 217 word-pair rows collapsed onto only 140 unique (crop_hash, word_a,
# word_b) triples, i.e. 77 decisions had already been silently overwritten by
# an unrelated comparison that happened to share a crop.
#
# Deliberately NOT keyed on the model: models_to_try is a FALLBACK chain, so
# the same question can legitimately be answered by either model depending on
# which was reachable that minute. Keying on it would evict good answers
# whenever the primary model came back up. The model that answered is
# recorded in a non-key `model` column instead (has_model_column=True below),
# for provenance - a column verify_witness_vision.py's witness_cache never
# had, a real pre-existing schema difference the shared factory takes as a
# parameter rather than papering over.
#
# These are thin wrappers (not the cache logic itself, moved to
# vision_adjudication_common.py 2026-08-17 - see that module's docstring)
# kept as module-level functions, reading CACHE_DB/PROMPT_HASH fresh from
# this module's own globals on every call, so `monkeypatch.setattr(vcv,
# "CACHE_DB", ...)` in tests keeps working exactly as before this extraction.
CACHE_TABLE = "corrections_cache"


def init_cache():
    vac.init_cache_table(CACHE_DB, CACHE_TABLE, PROMPT_HASH, has_model_column=True)


def get_cached_decision(crop_bytes, word_a, word_b, context):
    return vac.get_cached_decision(CACHE_DB, CACHE_TABLE, PROMPT_HASH, crop_bytes, word_a, word_b, context)


def cache_decision(crop_bytes, word_a, word_b, context, decision_json, model=None):
    vac.put_cached_decision(CACHE_DB, CACHE_TABLE, PROMPT_HASH, crop_bytes, word_a, word_b, context,
                             decision_json, model=model, has_model_column=True)


def crop_pdf_bounding_box(doc, page_num_1indexed, bbox, padding=CROP_PADDING):
    return vac.crop_pdf_bounding_box(doc, page_num_1indexed, bbox, padding=padding, dpi=CROP_DPI)


def parse_decision_text(decision_text):
    """Recover the JSON decision dict from a raw Gemini response robustly:
    strict JSON first (needed for correct handling of any \\uXXXX escape,
    which extract_json_fields's regex-based fallback below does not attempt -
    see its own docstring), then a backslash-sanitized retry (sanitize_json),
    then full field-by-field lenient extraction (extract_json_fields) as a
    last resort for a response with an embedded unescaped quote (Hebrew
    gershayim inside transcription_found/reasoning). Raises ValueError if
    even that fails - callers decide how to record a total parse failure.

    Factored out 2026-08-17 (revalidation round 4) from what used to be
    inline in main()'s loop, so tools/verify_flagged_candidates_vision.py -
    which already reuses this module's crop/adjudicate/cache functions
    directly per its own docstring - can reuse the SAME robust chain instead
    of calling extract_json_fields directly and skipping the strict-JSON-
    first attempt entirely (confirmed during this round: that gap meant a
    well-formed response containing a \\uXXXX escape, however unlikely in
    practice, would have been silently corrupted rather than parsed
    correctly - the exact risk this chain's ordering exists to avoid).
    """
    decision = None
    try:
        decision = json.loads(decision_text)
    except json.JSONDecodeError:
        try:
            decision = json.loads(sanitize_json(decision_text))
        except json.JSONDecodeError:
            decision = extract_json_fields(decision_text)
    if decision is None:
        raise ValueError(f"could not parse decision JSON: {decision_text[:200]!r}")
    # Normalise selected_option HERE, at the single chokepoint all three parse
    # paths funnel through, rather than in each extractor - a well-formed
    # response goes straight through json.loads and never touches the
    # fallbacks, which is exactly how `"selected_option": "Option A"` reached
    # classify() unrecognised and got a real 0.95-confidence verdict discarded
    # as an "error" (klal 163 word 503, found 2026-08-23). Preserves the raw
    # value under `selected_option_raw` so a genuinely unparseable answer stays
    # inspectable rather than being silently blanked.
    if isinstance(decision, dict) and "selected_option" in decision:
        raw = decision["selected_option"]
        normalised = normalize_selected_option(raw)
        if normalised != raw:
            decision["selected_option_raw"] = raw
        decision["selected_option"] = normalised
    return decision


def adjudicate(client, crop_bytes, option_a, option_b, full_context):
    # A delete-opcode candidate has option_b is None: the corpus has NO
    # text at all at this position, and DocAI independently proposed
    # option_a as text that belongs there. The old prompt embedded the
    # literal Python `None` as if it were a second reading to compare
    # against the pixels ('Option B (current adjudicated text): "None"'),
    # an unanswerable question the model correctly (from its own
    # perspective) resolved to UNCERTAIN regardless of what the crop
    # actually showed - confirmed 2026-08-12: 10 of 29 delete candidates
    # came back UNCERTAIN this way, including klal 4's stored reasoning
    # literally saying "Neither Option A ('1') nor Option B ('None')..."
    # (PROJECT-STATUS.md finding 7). Describe what B actually means for a
    # delete-opcode candidate instead: "confirm nothing belongs here."
    option_b_desc = (
        f'"{option_b}"' if option_b is not None
        else "(nothing - confirm no text belongs at this position; the corpus currently has none here)"
    )
    # FIXED 2026-08-21 (PROJECT-STATUS.md open item 8, "baked into the tool,
    # not a one-off"): the mirror-image case - an 'insert'-opcode candidate
    # has option_a is None (DocAI's fresh OCR pass found no matching token
    # at all; option_b is the corpus's current, possibly-unverified text).
    # Before this fix these candidates never reached adjudicate() at all
    # (main() skipped any candidate with bbox=None, which every insert
    # candidate always had - see build_corrections_dataset.py's newly added
    # estimate_insert_bbox()). Applying the identical fix option_b already
    # got, for the identical reason: the literal string "None" is not a
    # real second reading to ask the model to compare against pixels.
    option_a_desc = (
        f'"{option_a}"' if option_a is not None
        else "(nothing - DocAI's fresh OCR pass found no matching text here; "
             "confirm whether the corpus's Option B text is genuinely visible "
             "in this crop, or is an unverified addition with no basis in the ink)"
    )

    prompt = PROMPT_TEMPLATE.format(
        full_context=full_context, option_a_desc=option_a_desc, option_b_desc=option_b_desc)

    return vac.adjudicate_with_retry(
        client, crop_bytes, prompt,
        cache_get=lambda: get_cached_decision(crop_bytes, option_a, option_b, full_context),
        cache_put=lambda text, model_name: cache_decision(
            crop_bytes, option_a, option_b, full_context, text, model=model_name),
    )


def main():
    init_cache()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("GEMINI_API_KEY not set")
    # Explicit request timeout (see vision_adjudication_common.make_client):
    # a hung call (observed 2026-08-06 - one crop's request never returned
    # and never raised, blocking the whole run for 20+ minutes at zero CPU
    # with no retry ever triggering, since the retry logic only fires on a
    # caught exception) needs to fail loudly so the existing retry/backoff
    # loop can actually run instead of hanging forever.
    client = vac.make_client(api_key)

    candidates_path = sys.argv[1] if len(sys.argv) > 1 else CANDIDATES_PATH
    out_path = sys.argv[2] if len(sys.argv) > 2 else OUT_PATH
    candidates = cio.load_json(candidates_path)["corrections"]
    final_by_id = {k["klal_id"]: k for k in cio.load_demo_dataset(DEMO_DATASET)}
    doc = fitz.open(PDF_PATH)

    # FIXED 2026-08-21 (found while re-running this script for the insert-
    # bbox feature, PROJECT-STATUS.md open item 8): results used to be
    # buffered in memory and written to out_path ONCE, after the whole loop
    # completed - violating the standing incremental-disk-flushing rule
    # (START_HERE.md Part 2 / .gemini/rules/incremental_disk_flushing.md),
    # the same class of bug already fixed in the VLM baseline scripts
    # 2026-08-20/21. A 429/503/network failure partway through this run (539
    # real, paid vision-adjudication calls) would lose every prior decision
    # in the batch with nothing on disk to show for it - the cache table
    # would still have them (so no API cost is truly lost), but the actual
    # output file this script exists to produce would not. Re-writes the
    # whole (small, few-hundred-KB) results list after every candidate
    # instead of appending text - out_path is a single JSON array, not a
    # line-oriented log, so this is the equivalent "always current on disk"
    # guarantee for this file shape.
    def flush_results(results):
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

    results = []
    for c in candidates:
        if not c["bbox"]:
            results.append({**c, "vision_confidence": None, "vision_reasoning": "no bbox (insertion) - not vision-cropped", "vision_selected": None})
            flush_results(results)
            continue

        k = final_by_id.get(c["klal_id"], {})
        # Local window AROUND the actual word, not a fixed head-of-klal slice.
        # Bug found 2026-08-10 (PROJECT-STATUS.md "sends the wrong surrounding
        # sentence context"): this used to be clean_text[:400] unconditionally,
        # so any word past ~65 words into a klal got the klal's OPENING lines
        # as "surrounding sentence context" - unrelated to the real sentence
        # around it. 112 of 244 (45.9%) of then-vision-checked words were
        # affected. word_index_in_final_text is the word's position in the
        # unfiltered clean_text.split() array (see build_corrections_dataset.py's
        # page_word_origin comment) - use it directly. The split MUST match that
        # generator's: this used to say .split(" "), the space-only scheme the
        # human-decision path deliberately uses (apply_reviewer_decisions.py's
        # apply_manual_correction), which is a different indexing scheme.
        # Harmless only while no klal contains double/leading/non-space
        # whitespace; tests/test_corpus_invariants.py now gates that, rather
        # than leaving the two schemes silently agreeing by luck.
        words = k.get("clean_text", "").split()
        wi = c.get("word_index_in_final_text")
        if isinstance(wi, int) and 0 <= wi < len(words):
            ctx_start = max(0, wi - CONTEXT_WINDOW_WORDS)
            ctx_end = min(len(words), wi + CONTEXT_WINDOW_WORDS + 1)  # +1: exclusive end
            context = " ".join(words[ctx_start:ctx_end])
        else:
            context = k.get("clean_text", "")[:FALLBACK_CONTEXT_CHARS]

        try:
            crop_bytes = crop_pdf_bounding_box(doc, c["page"], c["bbox"])
            print(f"Klal {c['klal_id']} page {c['page']}: {c['original_word']!r} vs {c['corrected_word']!r}", flush=True)
            decision_text = adjudicate(client, crop_bytes, c["original_word"], c["corrected_word"], context)
            decision = parse_decision_text(decision_text)
        except Exception as e:
            print(f"  !! failed: {e}", flush=True)
            decision = {"selected_option": "ERROR", "transcription_found": None, "confidence": None, "reasoning": str(e)}

        results.append({
            **c,
            "vision_selected": decision.get("selected_option"),
            "vision_transcription": decision.get("transcription_found"),
            "vision_confidence": decision.get("confidence"),
            "vision_reasoning": decision.get("reasoning"),
        })
        flush_results(results)

    doc.close()
    print(f"\nWrote {len(results)} results to {out_path}")


if __name__ == "__main__":
    main()
