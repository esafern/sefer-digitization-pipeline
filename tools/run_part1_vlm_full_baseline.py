#!/usr/bin/env python3
"""
tools/run_part1_vlm_full_baseline.py

Executes Gemini 3.6 Flash VLM full-text OCR transcription for EVERY SINGLE WORD
across all 222 klalim in Part 1 (pages 13-63 of berlin_square_corrected.pdf).

Establishes a brand-new VLM baseline and quality metric for the entire Part 1 corpus.
Outputs structured result to tools/second_witness_eval/vlm_part1_full_baseline.txt.
"""

import json
import os
import sys
import time
import fitz

# Ensure pipeline modules are importable
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

    # Filter regions for Part 1 (klal_id <= 222). Each klal's own start page
    # PLUS every continuation page - FIXED 2026-08-21 (code review): this
    # used to read only a region's top-level page/bbox, silently dropping
    # every continuation page's content from the baseline (~175 of 667
    # corpus-wide klalim span more than one physical page, e.g. klal 2: page
    # 14 body + a page-15 continuation). The `isinstance(val, list)` branch
    # below was dead code - klal_page_regions.json entries are always dicts,
    # confirmed against both this file's own build script
    # (pipeline/build_klal_page_regions.py) and every entry in the live
    # file - removed rather than left in as confusing, unexercised code.
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

    print("=" * 80)
    print(f"RUNNING VLM FULL BASELINE OCR FOR PART 1 ({len(klal_ids)} KLALIM, "
          f"{sum(len(p) for p in part1_klalim.values())} PAGE CROPS)")
    print("=" * 80)

    # Truncate once up front, then every iteration below appends+flushes
    # incrementally (per the standing incremental-disk-flushing rule). FIXED
    # 2026-08-20 (code review): this file was opened "a" with no truncation
    # anywhere, so restarting after a mid-run crash/interruption duplicated
    # every already-written "=== KLAL N ===" block; downstream parsers keep
    # only the last occurrence (dict-keyed), silently masking the corruption
    # rather than surfacing it.
    output_dir = os.path.join(REPO, "tools", "second_witness_eval")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "vlm_part1_full_baseline.txt")
    open(output_path, "w", encoding="utf-8").close()

    def dummy_cache_get():
        return None

    def dummy_cache_put(text, model):
        pass

    for i, klal_id in enumerate(klal_ids, 1):
        pages = part1_klalim[klal_id]
        page_nums = [p["page"] for p in pages]
        header_str = f"=== KLAL {klal_id} (Pages {','.join(str(p) for p in page_nums)}) ==="
        print(f"[{i}/{len(klal_ids)}] Transcribing Klal {klal_id:3d} ({len(pages)} page(s): "
              f"{page_nums})...", flush=True)

        # One transcription call PER PAGE (start + every continuation),
        # concatenated into one klal-level block below - see the
        # region-loading comment above for why this klal_id can now span
        # more than one page crop.
        page_texts = []
        any_failed = False
        for p in pages:
            try:
                # FIXED 2026-08-21: crop_pdf_bounding_box() used to be
                # called OUTSIDE this try block, so a bad bbox/PDF read on
                # any single page crashed the whole run uncaught (observed
                # live during this session: the earlier version silently
                # died after printing klal 37's header line, exit code 1, no
                # traceback ever reached the log). One bad page should skip
                # that page's text, not lose the rest of the corpus.
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
                    # FIXED 2026-08-21 (code review): adjudicate_with_retry()
                    # defaults to "application/json" (the shape every OTHER
                    # caller in this codebase needs, since they ask for a
                    # structured verdict). This prompt asks for verbatim
                    # plain text, and without this override the committed
                    # output literally contained JSON-array syntax
                    # ('[', '"word",', ']') as spurious extra tokens,
                    # corrupting every downstream word count/accuracy
                    # figure. pipeline/second_witness_eval/vlm_witness.py
                    # already gets this right; this script (and its pass-2
                    # and witness-sample siblings) did not.
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
    print(f"Part 1 VLM Baseline OCR completed cleanly!")
    print(f"Output written to: {output_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
