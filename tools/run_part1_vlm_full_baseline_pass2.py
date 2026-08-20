#!/usr/bin/env python3
"""
tools/run_part1_vlm_full_baseline_pass2.py

Executes a SECOND independent VLM baseline transcription pass (Pass B)
for all 222 klalim in Part 1 to measure model sampling variance and establish
a Self-Consistency Consensus (Pass A vs Pass B).

Outputs result to tools/second_witness_eval/vlm_part1_full_baseline_passB.txt.
"""

import json
import os
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

    part1_items = []
    for k_str, val in regions.items():
        try:
            klal_id = int(k_str)
        except ValueError:
            continue
        if klal_id <= corpus_io.PART1_MAX_KLAL:
            if isinstance(val, list):
                for seq, r in enumerate(val, 1):
                    item = dict(r)
                    item["klal_id"] = klal_id
                    item["seq"] = seq
                    part1_items.append(item)
            elif isinstance(val, dict):
                item = dict(val)
                item["klal_id"] = klal_id
                item["seq"] = 1
                part1_items.append(item)

    part1_items.sort(key=lambda x: (x["klal_id"], x["seq"]))

    print("=" * 80)
    print(f"RUNNING VLM PASS B (SELF-CONSISTENCY PASS) FOR PART 1 ({len(part1_items)} CROPS)")
    print("=" * 80)

    output_lines = []

    def dummy_cache_get():
        return None

    def dummy_cache_put(text, model):
        pass

    for i, reg in enumerate(part1_items, 1):
        klal_id = reg["klal_id"]
        page_num = reg["page"]
        bbox = reg["bbox"]
        seq = reg.get("seq", 1)

        header_str = f"=== KLAL {klal_id} (Page {page_num}, Seq {seq}) ==="
        print(f"[PASS B {i}/{len(part1_items)}] Transcribing Klal {klal_id:3d} (Page {page_num:2d})...", end="", flush=True)

        crop_bytes = vision_adjudication_common.crop_pdf_bounding_box(
            doc, page_num, bbox, padding=0.01, dpi=300
        )

        try:
            transcription = vision_adjudication_common.adjudicate_with_retry(
                client=client,
                crop_bytes=crop_bytes,
                prompt=UNCONDITIONED_OCR_PROMPT,
                cache_get=dummy_cache_get,
                cache_put=dummy_cache_put,
                models_to_try=("gemini-3.6-flash", "gemini-3.5-flash"),
                max_retries=5,
            ).strip()
            word_count = len(transcription.split())
            print(f" OK ({word_count} words extracted)")
            time.sleep(0.2)
        except Exception as e:
            print(f" FAILED: {e}")
            transcription = ""

        output_lines.append(header_str)
        output_lines.append(transcription)
        output_lines.append("")

        output_dir = os.path.join(REPO, "tools", "second_witness_eval")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "vlm_part1_full_baseline_passB.txt")
        with open(output_path, "a", encoding="utf-8") as f:
            f.write(f"{header_str}\n{transcription}\n\n")

    doc.close()

    print("=" * 80)
    print(f"Part 1 VLM Baseline Pass B completed cleanly!")
    print(f"Output written to: {output_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
