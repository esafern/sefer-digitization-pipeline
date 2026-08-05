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

REPO = os.path.dirname(os.path.abspath(__file__))
PDF_PATH = os.path.join(REPO, "berlin_square.pdf")
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
    conn.execute(
        "CREATE TABLE IF NOT EXISTS corrections_cache ("
        "crop_hash TEXT NOT NULL, word_a TEXT NOT NULL, word_b TEXT NOT NULL, "
        "decision_json TEXT, PRIMARY KEY (crop_hash, word_a, word_b))"
    )
    conn.commit()
    conn.close()


_NONE_SENTINEL = "\x00NONE\x00"  # word_a/word_b is NOT NULL; opcode delete/insert
                                  # legitimately has one side as None (e.g. "X" vs
                                  # nothing) - coerce rather than relax the schema.


def get_cached_decision(crop_bytes, word_a, word_b):
    crop_hash = hashlib.sha256(crop_bytes).hexdigest()
    conn = sqlite3.connect(CACHE_DB, timeout=10.0)
    row = conn.execute(
        "SELECT decision_json FROM corrections_cache WHERE crop_hash = ? AND word_a = ? AND word_b = ?",
        (crop_hash, word_a or _NONE_SENTINEL, word_b or _NONE_SENTINEL),
    ).fetchone()
    conn.close()
    return row[0] if row else None


def cache_decision(crop_bytes, word_a, word_b, decision_json):
    crop_hash = hashlib.sha256(crop_bytes).hexdigest()
    conn = sqlite3.connect(CACHE_DB, timeout=10.0)
    conn.execute(
        "INSERT OR REPLACE INTO corrections_cache (crop_hash, word_a, word_b, decision_json) VALUES (?, ?, ?, ?)",
        (crop_hash, word_a or _NONE_SENTINEL, word_b or _NONE_SENTINEL, decision_json),
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
    cached = get_cached_decision(crop_bytes, option_a, option_b)
    if cached:
        print("  -> cache hit")
        return cached

    prompt = f"""
You are an expert Talmudic and Rabbinic textual verification engine analyzing a Hebrew manuscript raster crop.

Surrounding Talmudic/Rabbinic Sentence Context: "{full_context}"

Evaluate the target raster crop against candidate strings:
Option A (DocAI raw OCR reading): "{option_a}"
Option B (current adjudicated text): "{option_b}"

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
                cache_decision(crop_bytes, option_a, option_b, response.text)
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
    client = genai.Client(api_key=api_key)

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
        context = k.get("clean_text", "")[:400]

        try:
            crop_bytes = crop_pdf_bounding_box(doc, c["page"], c["bbox"])
            print(f"Klal {c['klal_id']} page {c['page']}: {c['original_word']!r} vs {c['corrected_word']!r}")
            decision_text = adjudicate(client, crop_bytes, c["original_word"], c["corrected_word"], context)
            try:
                decision = json.loads(decision_text)
            except json.JSONDecodeError:
                decision = json.loads(sanitize_json(decision_text))
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
