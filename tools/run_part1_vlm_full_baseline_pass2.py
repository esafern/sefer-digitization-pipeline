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


def already_completed_klal_ids(path):
    """klal_ids with a complete "=== KLAL N ..." block already in `path`,
    from an earlier, interrupted run - added 2026-08-21 after a real mid-run
    failure (Gemini API prepayment credits ran out at klal 92/222; this
    script's own dummy_cache_get/put never cache anything, by design, so a
    naive re-run would have silently RE-PAID for the 91 klalim already done,
    on top of truncating and losing their output). Every block this script
    writes is a single atomic `f.write()` after that klal's ALL pages
    finished (see the main loop below) - a kill mid-klal never leaves a
    partial header with no content, so scanning for headers alone is a safe
    way to know what's genuinely done. Returns an empty set if the file
    doesn't exist or is empty (a fresh run, not a resume)."""
    if not os.path.exists(path):
        return set()
    ids = set()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^===\s*KLAL\s+(\d+)", line)
            if m:
                ids.add(int(m.group(1)))
    return ids


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

    # Same fix as run_part1_vlm_full_baseline.py, 2026-08-21 (code review):
    # include every continuation page, not just a klal's start page - see
    # that file's own comment for why. Pass A and Pass B must cover
    # identical content for the self-consistency comparison
    # (evaluate_vlm_self_consistency.py) to mean anything.
    part1_klalim = {}
    for k_str, val in regions.items():
        try:
            klal_id = int(k_str)
        except ValueError:
            continue
        if klal_id > corpus_io.PART1_MAX_KLAL or not isinstance(val, dict):
            continue
        pages = [{"page": val["page"], "bbox": val["bbox"]}]
        pages += [{"page": c["page"], "bbox": c["bbox"]} for c in val.get("continuations", [])]
        part1_klalim[klal_id] = pages

    klal_ids = sorted(part1_klalim)

    output_dir = os.path.join(REPO, "tools", "second_witness_eval")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "vlm_part1_full_baseline_passB.txt")

    # RESUME, not truncate, when a prior run already wrote real progress -
    # see already_completed_klal_ids()'s own docstring for the real
    # incident (API credits ran out mid-run at klal 92/222) this fixes.
    # Same fix as run_part1_vlm_full_baseline.py, 2026-08-20 (code review)
    # for the ORIGINAL truncate-once-up-front behavior; this refines it
    # further for the resume case specifically.
    done_ids = already_completed_klal_ids(output_path)
    if done_ids:
        skipped = len(done_ids & set(klal_ids))
        klal_ids = [k for k in klal_ids if k not in done_ids]
        print(f"RESUMING: {skipped} klalim already completed in "
              f"{output_path} - skipping them, not re-paying for them.")
    else:
        open(output_path, "w", encoding="utf-8").close()

    print("=" * 80)
    print(f"RUNNING VLM PASS B (SELF-CONSISTENCY PASS) FOR PART 1 ({len(klal_ids)} KLALIM REMAINING, "
          f"{sum(len(part1_klalim[k]) for k in klal_ids)} PAGE CROPS)")
    print("=" * 80)

    def dummy_cache_get():
        return None

    def dummy_cache_put(text, model):
        pass

    for i, klal_id in enumerate(klal_ids, 1):
        pages = part1_klalim[klal_id]
        page_nums = [p["page"] for p in pages]
        header_str = f"=== KLAL {klal_id} (Pages {','.join(str(p) for p in page_nums)}) ==="
        print(f"[PASS B {i}/{len(klal_ids)}] Transcribing Klal {klal_id:3d} "
              f"({len(pages)} page(s): {page_nums})...", flush=True)

        page_texts = []
        any_failed = False
        for p in pages:
            try:
                crop_bytes = vision_adjudication_common.crop_pdf_bounding_box(
                    doc, p["page"], p["bbox"], padding=0.01, dpi=300
                )
                text = vision_adjudication_common.adjudicate_with_retry(
                    client=client,
                    crop_bytes=crop_bytes,
                    prompt=UNCONDITIONED_OCR_PROMPT,
                    cache_get=dummy_cache_get,
                    cache_put=dummy_cache_put,
                    models_to_try=("gemini-3.6-flash", "gemini-3.5-flash"),
                    max_retries=5,
                    # FIXED 2026-08-21 (code review) - see
                    # run_part1_vlm_full_baseline.py's identical fix comment.
                    response_mime_type="text/plain",
                ).strip()
                page_texts.append(text)
                time.sleep(0.2)
            except Exception as e:
                print(f"  -> page {p['page']} FAILED: {e}")
                any_failed = True

        transcription = "\n".join(page_texts)
        word_count = len(transcription.split())
        status = "OK" if not any_failed else "PARTIAL (one or more pages failed)"
        print(f"  -> {status}: {word_count} words extracted across "
              f"{len(page_texts)}/{len(pages)} page(s)")

        with open(output_path, "a", encoding="utf-8") as f:
            f.write(f"{header_str}\n{transcription}\n\n")

    doc.close()

    print("=" * 80)
    print(f"Part 1 VLM Baseline Pass B completed cleanly!")
    print(f"Output written to: {output_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
