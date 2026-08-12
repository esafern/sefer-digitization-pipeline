# [PRODUCTION] Crop each Part-1 correction candidate from the Berlin scan and ask
# Gemini (vision) to select between the DocAI raw reading and the final adjudicated
# text, recording a real confidence score + paleographic rationale. Mirrors
# orchestrator.py's adjudicate_conflict_with_gemini, scoped to the small candidate
# set from build_corrections_dataset.py instead of a full page scan.
import json
import os
import sys
import time
import hashlib
import sqlite3

import re

import fitz  # PyMuPDF
from google import genai
from google.genai import types


def sanitize_json(text):
    # Gemini occasionally emits invalid JSON escapes (e.g. \' around a geresh);
    # strip a backslash unless it precedes a valid JSON escape character.
    return re.sub(r'\\(?!["\\/bfnrtu])', '', text)


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
        return m.group(1) if m else None

    selected = re.search(r'"selected_option"\s*:\s*"(A|B|UNCERTAIN)"', text)
    transcription = field("transcription_found", r'(?="confidence")')
    confidence = re.search(r'"confidence"\s*:\s*([\d.]+)', text)
    reasoning = field("reasoning", r'\}\s*$')

    if not (selected and confidence):
        return None
    return {
        "selected_option": selected.group(1),
        "transcription_found": transcription,
        "confidence": float(confidence.group(1)),
        "reasoning": reasoning,
    }

REPO = os.path.dirname(os.path.abspath(__file__))
PDF_PATH = os.path.join(REPO, "berlin_square_corrected.pdf")
CANDIDATES_PATH = os.path.join(REPO, "corrections_candidates_part1.json")
OUT_PATH = os.path.join(REPO, "corrections_verified_part1.json")
CACHE_DB = os.path.join(REPO, "adjudication_cache.db")
DEMO_DATASET = os.path.join(REPO, "klalim_demo_dataset.json")


# Uses its own table (not orchestrator.py's `cache`) and keys on the full
# (crop_hash, word_a, word_b) triple, not crop_hash alone. A bare crop_hash key
# is wrong here: the same crop gets re-cropped across sessions to answer
# different A/B comparisons as `clean_text` changes (fixes, reverts), and a
# crop_hash-only cache silently returns a decision for the *wrong* word pair -
# confirmed 2026-08-05: migrating the old table found 217 word-pair rows
# collapsed onto only 140 unique (crop_hash, word_a, word_b) triples, i.e. 77
# decisions had already been silently overwritten by an unrelated comparison
# that happened to share a crop.
def init_cache():
    conn = sqlite3.connect(CACHE_DB)
    # WAL mode lets readers and the writer proceed concurrently instead of
    # blocking on SQLite's default rollback-journal lock - this script opens
    # a fresh connection per cache read/write and was seeing frequent
    # "database is locked" errors under the default journal mode, each one
    # discarding an already-successful API response and forcing a re-call.
    conn.execute("PRAGMA journal_mode=WAL")
    # context_hash added 2026-08-10 (PROJECT-STATUS.md "sends the wrong
    # surrounding sentence context"): the cache key used to be just
    # (crop_hash, word_a, word_b), but the prompt the model actually saw also
    # includes `context` - once context was fixed to be a real local window
    # instead of a fixed head-of-klal slice, a key that doesn't cover context
    # would keep silently returning the OLD wrong-context decision forever,
    # the exact cache-key-must-cover-everything-that-changes-the-answer bug
    # this project already fixed once for adjudication_cache.db (see
    # CLAUDE.md "Single source of truth" / Lesson 12). Old rows under the
    # pre-fix 3-column schema are incompatible and were dropped, not
    # migrated - this is a fully regenerable cache, not source data.
    conn.execute(
        "CREATE TABLE IF NOT EXISTS corrections_cache ("
        "crop_hash TEXT NOT NULL, word_a TEXT NOT NULL, word_b TEXT NOT NULL, "
        "context_hash TEXT NOT NULL, "
        "decision_json TEXT, PRIMARY KEY (crop_hash, word_a, word_b, context_hash))"
    )
    conn.commit()
    conn.close()


_NONE_SENTINEL = "\x00NONE\x00"  # word_a/word_b is NOT NULL; opcode delete/insert
                                  # legitimately has one side as None (e.g. "X" vs
                                  # nothing) - coerce rather than relax the schema.


def get_cached_decision(crop_bytes, word_a, word_b, context):
    crop_hash = hashlib.sha256(crop_bytes).hexdigest()
    context_hash = hashlib.sha256(context.encode("utf-8")).hexdigest()
    conn = sqlite3.connect(CACHE_DB, timeout=10.0)
    row = conn.execute(
        "SELECT decision_json FROM corrections_cache WHERE crop_hash = ? AND word_a = ? AND word_b = ? AND context_hash = ?",
        (crop_hash, word_a or _NONE_SENTINEL, word_b or _NONE_SENTINEL, context_hash),
    ).fetchone()
    conn.close()
    return row[0] if row else None


def cache_decision(crop_bytes, word_a, word_b, context, decision_json):
    crop_hash = hashlib.sha256(crop_bytes).hexdigest()
    context_hash = hashlib.sha256(context.encode("utf-8")).hexdigest()
    conn = sqlite3.connect(CACHE_DB, timeout=10.0)
    conn.execute(
        "INSERT OR REPLACE INTO corrections_cache (crop_hash, word_a, word_b, context_hash, decision_json) VALUES (?, ?, ?, ?, ?)",
        (crop_hash, word_a or _NONE_SENTINEL, word_b or _NONE_SENTINEL, context_hash, decision_json),
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

    crop_rect = fitz.Rect(xmin, ymin, xmax, ymax)
    pix = page.get_pixmap(clip=crop_rect, dpi=300)
    return pix.tobytes("png")


def adjudicate(client, crop_bytes, option_a, option_b, full_context):
    cached = get_cached_decision(crop_bytes, option_a, option_b, full_context)
    if cached:
        print("  -> cache hit")
        return cached

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

    prompt = f"""
You are an expert Talmudic and Rabbinic textual verification engine analyzing a Hebrew manuscript raster crop.

Surrounding Talmudic/Rabbinic Sentence Context: "{full_context}"

Evaluate the target raster crop against candidate strings:
Option A (DocAI raw OCR reading): "{option_a}"
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

    # gemini-2.5-flash removed 2026-08-05: permanently 404s ("no longer
    # available to new users"), not transient - it was silently eating a
    # retry slot on every fallback path instead of ever actually helping.
    models_to_try = ["gemini-3.6-flash", "gemini-3.5-flash"]
    max_retries = 3
    last_err = None
    for model_name in models_to_try:
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                        types.Part.from_bytes(data=crop_bytes, mime_type="image/png"),
                        prompt,
                    ],
                    config=types.GenerateContentConfig(response_mime_type="application/json"),
                )
                print(f"  -> live call to {model_name} ok")
                cache_decision(crop_bytes, option_a, option_b, full_context, response.text)
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
    init_cache()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("GEMINI_API_KEY not set")
    # Explicit request timeout: a hung call (observed 2026-08-06 - one crop's
    # request never returned and never raised, blocking the whole run for
    # 20+ minutes at zero CPU with no retry ever triggering, since the retry
    # logic only fires on a caught exception) needs to fail loudly so the
    # existing retry/backoff loop can actually run instead of hanging forever.
    client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=60000))

    candidates_path = sys.argv[1] if len(sys.argv) > 1 else CANDIDATES_PATH
    out_path = sys.argv[2] if len(sys.argv) > 2 else OUT_PATH
    candidates = json.load(open(candidates_path))["corrections"]
    final_by_id = {k["klal_id"]: k for k in json.load(open(DEMO_DATASET))}
    doc = fitz.open(PDF_PATH)

    results = []
    for c in candidates:
        if not c["bbox"]:
            results.append({**c, "vision_confidence": None, "vision_reasoning": "no bbox (insertion) - not vision-cropped", "vision_selected": None})
            continue

        k = final_by_id.get(c["klal_id"], {})
        # Local window AROUND the actual word, not a fixed head-of-klal slice.
        # Bug found 2026-08-10 (PROJECT-STATUS.md "sends the wrong surrounding
        # sentence context"): this used to be clean_text[:400] unconditionally,
        # so any word past ~65 words into a klal got the klal's OPENING lines
        # as "surrounding sentence context" - unrelated to the real sentence
        # around it. 112 of 244 (45.9%) of then-vision-checked words were
        # affected. word_index_in_final_text is the word's position in the
        # unfiltered clean_text.split(" ") array (see build_corrections_
        # dataset.py's page_word_origin comment) - use it directly.
        words = k.get("clean_text", "").split(" ")
        wi = c.get("word_index_in_final_text")
        if isinstance(wi, int) and 0 <= wi < len(words):
            ctx_start = max(0, wi - 35)
            ctx_end = min(len(words), wi + 36)
            context = " ".join(words[ctx_start:ctx_end])
        else:
            context = k.get("clean_text", "")[:400]

        try:
            crop_bytes = crop_pdf_bounding_box(doc, c["page"], c["bbox"])
            print(f"Klal {c['klal_id']} page {c['page']}: {c['original_word']!r} vs {c['corrected_word']!r}")
            decision_text = adjudicate(client, crop_bytes, c["original_word"], c["corrected_word"], context)
            try:
                decision = json.loads(decision_text)
            except json.JSONDecodeError:
                try:
                    decision = json.loads(sanitize_json(decision_text))
                except json.JSONDecodeError:
                    decision = extract_json_fields(decision_text)
                    if decision is None:
                        raise
        except Exception as e:
            print(f"  !! failed: {e}")
            decision = {"selected_option": "ERROR", "transcription_found": None, "confidence": None, "reasoning": str(e)}

        results.append({
            **c,
            "vision_selected": decision.get("selected_option"),
            "vision_transcription": decision.get("transcription_found"),
            "vision_confidence": decision.get("confidence"),
            "vision_reasoning": decision.get("reasoning"),
        })

    doc.close()
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nWrote {len(results)} results to {out_path}")


if __name__ == "__main__":
    main()
