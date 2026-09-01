#!/usr/bin/env python3
"""
tools/run_vlm_witness_sample.py

Runs Gemini 3.6 Flash VLM region-level OCR transcription for Berlin scan
klalim 8-22 (Berlin pages 18-20) using unconditioned visual prompts per
.gemini/rules/vlm_ocr_transcription_discipline.md.

Outputs result to dicta_eval/vlm_klal_8_22_ocr.txt.
"""

import json
import os
import sys
import fitz

# Ensure pipeline modules are importable
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pipeline"))
import corpus_io
import vision_adjudication_common

UNCONDITIONED_OCR_PROMPT = (
    "You are a literal OCR reader for 19th-century Hebrew typography. "
    "Transcribe the Hebrew text visible in this image crop verbatim line-by-line. "
    "Do not assume or infer text outside this image. Output only the raw Hebrew characters."
)


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable not set.")
        sys.exit(1)

    pdf_path = os.path.join(REPO, "berlin_square_corrected.pdf")
    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF not found at {pdf_path}")
        sys.exit(1)

    regions_path = os.path.join(REPO, "klal_page_regions.json")
    with open(regions_path, "r", encoding="utf-8") as f:
        regions = json.load(f)

    doc = fitz.open(pdf_path)
    client = vision_adjudication_common.make_client(api_key)

    print("=" * 80)
    print("RUNNING VLM SECOND-WITNESS TRANSCRIPTION ON KLALIM 8-22 (GEMINI 3.6 FLASH)")
    print("=" * 80)

    # Truncate once up front, then append+flush per klal below - FIXED
    # 2026-08-21 (code review): this used to buffer every klal's
    # transcription in output_lines and write the whole file once at the
    # end, violating the standing incremental-disk-flushing rule
    # (START_HERE.md Part 2 / .gemini/rules/incremental_disk_flushing.md) -
    # a 429/503 partway through (this exact failure mode is cited in both
    # rules, and observed live in this same script's own log) lost every
    # prior transcription in the batch since nothing had touched disk yet.
    output_path = os.path.join(REPO, "tools", "second_witness_eval", "vlm_klal_8_22_ocr.txt")
    open(output_path, "w", encoding="utf-8").close()

    def cache_get():
        return None

    def cache_put(text, model):
        pass

    for klal_id in range(8, 23):
        r = regions.get(str(klal_id))
        if not r:
            print(f"Skipping klal {klal_id}: region not found in klal_page_regions.json")
            continue

        # Every page this klal touches (start + continuations) - FIXED
        # 2026-08-21 (code review): this used to read only the top-level
        # page/bbox, silently dropping klal 12/15/21's continuation-page
        # content (all three have one within this 8-22 sample).
        pages = [{"page": r["page"], "bbox": r["bbox"]}]
        pages += [{"page": c["page"], "bbox": c["bbox"]} for c in r.get("continuations", [])]

        print(f"Transcribing Klal {klal_id:2d} ({len(pages)} page(s): "
              f"{[p['page'] for p in pages]})...")

        page_texts = []
        for p in pages:
            try:
                crop_bytes = vision_adjudication_common.crop_pdf_bounding_box(
                    doc, p["page"], p["bbox"], padding=0.01, dpi=300
                )
                text = vision_adjudication_common.adjudicate_with_retry(
                    client=client,
                    crop_bytes=crop_bytes,
                    prompt=UNCONDITIONED_OCR_PROMPT,
                    cache_get=cache_get,
                    cache_put=cache_put,
                    models_to_try=("gemini-3.6-flash", "gemini-3.5-flash"),
                    max_retries=5,
                    # FIXED 2026-08-21 (code review) - see
                    # run_part1_vlm_full_baseline.py's identical fix comment:
                    # without this, defaults to "application/json" and the
                    # output carries literal JSON-array syntax as noise.
                    response_mime_type="text/plain",
                ).strip()
                page_texts.append(text)
            except Exception as e:
                print(f"  -> page {p['page']} FAILED: {e}")

        transcription = "\n".join(page_texts)

        with open(output_path, "a", encoding="utf-8") as f:
            f.write(f"--- klal {klal_id}\n{transcription}\n\n")

    doc.close()

    print(f"\nVLM transcription completed! Output saved to: {output_path}")


if __name__ == "__main__":
    main()
