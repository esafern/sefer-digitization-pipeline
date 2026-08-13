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
# vision_transcription/vision_confidence/vision_reasoning per item, plus a
# vision_tier ("A"/"B"/"UNCERTAIN") the dashboard can use as an additional,
# independent triage signal alongside the existing lexicon-based tier.
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

REPO = os.path.dirname(os.path.abspath(__file__))
PDF_PATH = os.path.join(REPO, "berlin_square_corrected.pdf")
QUEUE_PATH = os.path.join(REPO, "reconstruction_witness_queue.json")
CACHE_DB = os.path.join(REPO, "witness_vision_cache.db")
DOCAI_DIR = os.path.join(REPO, "docai_word_boxes")

CONTEXT_WINDOW = 12  # raw docai tokens on each side, matching api_witness_context()
HEB = "אבגדהוזחטיכלמנסעפצקרשתךםןףץ"


def norm(s):
    return "".join(c for c in s if c in HEB)


# ---------- cache: keyed on everything that changes the actual question
# asked (Lesson 12 - a crop-hash-only or word-pair-only key silently reuses
# a stale answer for a different question on the same crop) ----------
def init_cache():
    conn = sqlite3.connect(CACHE_DB)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS witness_cache ("
        "crop_hash TEXT NOT NULL, word_a TEXT NOT NULL, word_b TEXT NOT NULL, "
        "context_hash TEXT NOT NULL, decision_json TEXT, "
        "PRIMARY KEY (crop_hash, word_a, word_b, context_hash))"
    )
    conn.commit()
    conn.close()


_NONE_SENTINEL = "\x00NONE\x00"


def get_cached(crop_bytes, word_a, word_b, context):
    crop_hash = hashlib.sha256(crop_bytes).hexdigest()
    context_hash = hashlib.sha256(context.encode("utf-8")).hexdigest()
    conn = sqlite3.connect(CACHE_DB, timeout=10.0)
    row = conn.execute(
        "SELECT decision_json FROM witness_cache WHERE crop_hash=? AND word_a=? AND word_b=? AND context_hash=?",
        (crop_hash, word_a or _NONE_SENTINEL, word_b or _NONE_SENTINEL, context_hash),
    ).fetchone()
    conn.close()
    return row[0] if row else None


def cache_put(crop_bytes, word_a, word_b, context, decision_json):
    crop_hash = hashlib.sha256(crop_bytes).hexdigest()
    context_hash = hashlib.sha256(context.encode("utf-8")).hexdigest()
    conn = sqlite3.connect(CACHE_DB, timeout=10.0)
    conn.execute(
        "INSERT OR REPLACE INTO witness_cache (crop_hash, word_a, word_b, context_hash, decision_json) VALUES (?,?,?,?,?)",
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
    pix = page.get_pixmap(clip=fitz.Rect(xmin, ymin, xmax, ymax), dpi=300)
    return pix.tobytes("png")


def sanitize_json(text):
    return re.sub(r'\\(?!["\\/bfnrtu])', "", text)


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

    prompt = f"""
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
                decision = json.loads(sanitize_json(decision_text))
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
