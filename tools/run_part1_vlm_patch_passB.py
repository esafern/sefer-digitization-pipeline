#!/usr/bin/env python3
"""
tools/run_part1_vlm_patch_passB.py

Patches the 9 corrupted/truncated klalim in Pass B (vlm_part1_full_baseline_passB.txt):
Klalim: 74, 75, 76, 77, 78, 88, 89, 90, 91.

Re-runs Gemini Flash 3.6 unconditioned transcription for all pages/continuations
of these 9 klalim and splices them cleanly into the file.
"""

import json
import os
import re
import sys
import time
import fitz

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "pipeline"))
import corpus_io
import vision_adjudication_common

UNCONDITIONED_OCR_PROMPT = (
    "You are a literal OCR reader for 19th-century Hebrew typography. "
    "Transcribe the Hebrew text visible in this image crop verbatim line-by-line. "
    "Do not assume or infer text outside this image. Output only the raw Hebrew characters."
)

TARGET_KLAL_IDS = [74, 75, 76, 77, 78, 88, 89, 90, 91]


def parse_pass_file_blocks(path):
    """Parses a pass file into {klal_id: (header_line, body_text)}."""
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = {}
    pattern = re.compile(r"^(=== KLAL (\d+)[^\n]*\n)(.*?)(?=(?:^=== KLAL |\Z))", re.MULTILINE | re.DOTALL)
    for m in pattern.finditer(content):
        kid = int(m.group(2))
        header = m.group(1)
        body = m.group(3)
        blocks[kid] = (header, body)
    return blocks


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

    output_path = os.path.join(REPO, "tools", "second_witness_eval", "vlm_part1_full_baseline_passB.txt")
    blocks = parse_pass_file_blocks(output_path)
    print(f"Loaded {len(blocks)} existing klal blocks from {output_path}")

    def dummy_cache_get():
        return None

    def dummy_cache_put(text, model):
        pass

    new_blocks = {}
    for kid in TARGET_KLAL_IDS:
        val = regions.get(str(kid))
        if not val:
            print(f"ERROR: Klal {kid} not found in regions.")
            continue

        pages = [{"page": val["page"], "bbox": val["bbox"]}]
        pages += [{"page": c["page"], "bbox": c["bbox"]} for c in val.get("continuations", [])]
        pages_str = ",".join(str(p["page"]) for p in pages)

        print(f"--> Transcribing Klal {kid} ({len(pages)} page crop(s): {pages_str})...")
        transcriptions = []
        for p in pages:
            crop_bytes = vision_adjudication_common.crop_pdf_bounding_box(
                doc, p["page"], p["bbox"], padding=0.01, dpi=300
            )
            resp = vision_adjudication_common.adjudicate_with_retry(
                client,
                crop_bytes,
                UNCONDITIONED_OCR_PROMPT,
                dummy_cache_get,
                dummy_cache_put,
                models_to_try=["gemini-3.6-flash", "gemini-3.5-flash"],
                max_retries=5,
                response_mime_type="text/plain",
            )
            cleaned = resp.strip() if resp else ""
            if cleaned:
                transcriptions.append(cleaned)
            time.sleep(0.5)

        full_klal_text = "\n".join(transcriptions).strip()
        word_count = len(full_klal_text.split())
        print(f"    Klal {kid} done: {word_count} words extracted.")

        header = f"=== KLAL {kid} (Pages {pages_str}) ===\n"
        body = full_klal_text + "\n\n"
        new_blocks[kid] = (header, body)

    # Splice new blocks in
    for kid, block in new_blocks.items():
        blocks[kid] = block

    # Write out all blocks in sorted order
    print(f"Writing updated pass file to {output_path} with {len(blocks)} klalim...")
    with open(output_path, "w", encoding="utf-8") as f:
        for kid in sorted(blocks.keys()):
            header, body = blocks[kid]
            f.write(header)
            f.write(body)

    print("Pass B patch complete!")


if __name__ == "__main__":
    main()
