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
# NOTE: deliberately no cache imports. See cache_for() below - Pass B must not
# replay Pass A's answers, or the stability gate it feeds becomes tautological.

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

    # REVERTED 2026-08-24, and the reasoning is worth keeping because the first
    # version looked like an obvious win.
    #
    # On 2026-08-23 this script's no-op cache stubs were "fixed" to use the same
    # persistent table as vlm_witness.py, on the grounds that a script whose
    # whole purpose is re-running a SUBSET of klalim should not re-pay for crops
    # it has already answered. That is true of cost and fatal to correctness.
    #
    # Pass A and Pass B exist to be two INDEPENDENT SAMPLES of the same model.
    # That independence is the entire measurement: it is what
    # synthesize_multi_witness.vlm_verdicts() gates on (where the two passes
    # disagree, the VLM abstains) and what the 87.43% self-consistency figure
    # reports. A cache keyed on (crop bytes, prompt hash) replays Pass A's
    # stored answer for Pass B, so every replayed position agrees with itself BY
    # CONSTRUCTION and sails through the stability gate. The sibling scripts
    # install no-op stubs deliberately, not by oversight.
    #
    # The cost problem is real and unsolved here. A Pass-B-private table, or a
    # per-run component in the key, would fix it without collapsing the sample;
    # neither is worth building until this script is actually needed again.
    def cache_for(_crop_bytes):
        def cache_get():
            return None

        def cache_put(text, model):
            pass
        return cache_get, cache_put

    def flush(all_blocks):
        """Rewrite the whole pass file from the current block set.

        FIXED 2026-08-23 (finding H8): this used to happen ONCE, after every
        klal had been transcribed, holding the entire run in memory - the exact
        violation of the standing incremental-disk-flushing rule that was fixed
        in run_vlm_witness_sample.py on 2026-08-21 and codified in
        .gemini/rules/incremental_disk_flushing.md the day before that, and
        exactly what loses a paid multi-klal run to one 429/503. This file is a
        read-modify-write splice rather than an append, so the flush rewrites
        the full set - but it now runs after EVERY klal, so a kill at any point
        keeps everything already paid for."""
        tmp = output_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            for kid in sorted(all_blocks.keys()):
                header, body = all_blocks[kid]
                f.write(header)
                f.write(body)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, output_path)  # atomic - never a half-written baseline

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
            cache_get, cache_put = cache_for(crop_bytes)
            resp = vision_adjudication_common.adjudicate_with_retry(
                client,
                crop_bytes,
                UNCONDITIONED_OCR_PROMPT,
                cache_get,
                cache_put,
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
        # Splice and flush THIS klal before moving to the next one.
        blocks[kid] = (header, body)
        flush(blocks)
        print(f"    flushed to disk ({len(blocks)} klalim on disk)")

    print(f"Done: {len(new_blocks)} klal(im) re-transcribed, "
          f"{len(blocks)} total in {output_path}")

    print("Pass B patch complete!")


if __name__ == "__main__":
    main()
