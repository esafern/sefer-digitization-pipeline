#!/usr/bin/env python3
"""
tools/run_vlm_witness_sample.py

Runs Gemini 3.6 Flash VLM region-level OCR transcription for Berlin scan
pages 18-20 (klalim 8-22) using unconditioned visual prompts per
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

    output_lines = []

    print("=" * 80)
    print("RUNNING VLM SECOND-WITNESS TRANSCRIPTION ON KLALIM 8-22 (GEMINI 3.6 FLASH)")
    print("=" * 80)

    for klal_id in range(8, 23):
        r = regions.get(str(klal_id))
        if not r:
            print(f"Skipping klal {klal_id}: region not found in klal_page_regions.json")
            continue

        page_num = r["page"]
        bbox = r["bbox"]

        print(f"Transcribing Klal {klal_id:2d} (Page {page_num})...")

        # Crop region image bytes
        crop_bytes = vision_adjudication_common.crop_pdf_bounding_box(
            doc, page_num, bbox, padding=0.01, dpi=300
        )

        def cache_get():
            return None

        def cache_put(text, model):
            pass

        try:
            transcription = vision_adjudication_common.adjudicate_with_retry(
                client=client,
                crop_bytes=crop_bytes,
                prompt=UNCONDITIONED_OCR_PROMPT,
                cache_get=cache_get,
                cache_put=cache_put,
                models_to_try=("gemini-3.6-flash", "gemini-3.5-flash"),
                max_retries=5,
            ).strip()
        except Exception as e:
            print(f"  -> Failed for klal {klal_id}: {e}")
            transcription = ""

        output_lines.append(f"--- klal {klal_id}")
        output_lines.append(transcription)
        output_lines.append("")

    doc.close()

    output_path = os.path.join(REPO, "tools", "second_witness_eval", "vlm_klal_8_22_ocr.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

    print(f"\nVLM transcription completed! Output saved to: {output_path}")


if __name__ == "__main__":
    main()
