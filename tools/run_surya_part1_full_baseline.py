#!/usr/bin/env python3
"""
tools/run_surya_part1_full_baseline.py

Runs Surya OCR across all Part 1 pages (pages 14-76) of the Berlin scan,
saving per-page recognition results incrementally, and maps extracted blocks
to their corresponding klalim using klal_page_regions.json.

Outputs:
  - tools/second_witness_eval/surya_pages/page_{num}.json (per-page raw layout+OCR)
  - tools/second_witness_eval/surya_part1_full_baseline.txt (klal-aligned baseline)
"""

import json
import os
import re
import sys
import time
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "pipeline"))

import corpus_io


def strip_html_tags(html_str):
    """Strips HTML tags like <p>, <b>, etc. while preserving inner text."""
    text = re.sub(r'<[^>]+>', ' ', html_str)
    # Normalize multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def load_part1_regions():
    regions_path = os.path.join(REPO, "klal_page_regions.json")
    with open(regions_path, "r", encoding="utf-8") as f:
        regions = json.load(f)

    # Map: page_num -> list of {"klal_id": int, "type": "start"|"continuation", "bbox": dict}
    page_to_klalim = {}
    part1_pages = set()

    for k_str, val in regions.items():
        try:
            klal_id = int(k_str)
        except ValueError:
            continue
        if klal_id > corpus_io.PART1_MAX_KLAL or not isinstance(val, dict):
            continue

        p_start = val["page"]
        part1_pages.add(p_start)
        page_to_klalim.setdefault(p_start, []).append({
            "klal_id": klal_id,
            "type": "start",
            "bbox": val["bbox"]
        })

        for c in val.get("continuations", []):
            p_cont = c["page"]
            part1_pages.add(p_cont)
            page_to_klalim.setdefault(p_cont, []).append({
                "klal_id": klal_id,
                "type": "continuation",
                "bbox": c["bbox"]
            })

    # Sort each page's klalim by y1
    for p in page_to_klalim:
        page_to_klalim[p].sort(key=lambda x: x["bbox"]["y1"])

    return page_to_klalim, sorted(part1_pages), regions


def match_block_to_klal(block_y_center, page_klalim):
    """
    Finds the klal region that best encloses or is closest to the block's vertical center.
    """
    # 1. Exact inclusion: y1 <= yc <= y2
    for k in page_klalim:
        if k["bbox"]["y1"] <= block_y_center <= k["bbox"]["y2"]:
            return k["klal_id"]

    # 2. Nearest region fallback
    best_k = None
    min_dist = float("inf")
    for k in page_klalim:
        dist = min(abs(block_y_center - k["bbox"]["y1"]), abs(block_y_center - k["bbox"]["y2"]))
        if dist < min_dist:
            min_dist = dist
            best_k = k["klal_id"]

    return best_k


def run_surya_part1(force_recompute=False):
    output_dir = os.path.join(REPO, "tools", "second_witness_eval")
    surya_pages_dir = os.path.join(output_dir, "surya_pages")
    os.makedirs(surya_pages_dir, exist_ok=True)

    page_to_klalim, pages, raw_regions = load_part1_regions()
    print("=" * 80)
    print(f"RUNNING SURYA OCR FOR PART 1: {len(pages)} PAGES (Pages {min(pages)}..{max(pages)})")
    print("=" * 80)

    from surya.inference import SuryaInferenceManager
    from surya.recognition import RecognitionPredictor

    manager = SuryaInferenceManager()
    predictor = RecognitionPredictor(manager)

    pages_to_process = []
    for p in pages:
        page_json = os.path.join(surya_pages_dir, f"page_{p}.json")
        if force_recompute or not os.path.exists(page_json):
            pages_to_process.append(p)

    print(f"Total pages: {len(pages)}, Cached: {len(pages) - len(pages_to_process)}, To run: {len(pages_to_process)}")

    for idx, p in enumerate(pages_to_process, 1):
        img_path = os.path.join(REPO, "images", "pdf_pages", f"page_{p}.png")
        if not os.path.exists(img_path):
            print(f"WARNING: Image not found for page {p}: {img_path}")
            continue

        t0 = time.time()
        print(f"[{idx}/{len(pages_to_process)}] Processing Page {p:3d}...", end=" ", flush=True)
        img = Image.open(img_path)
        w, h = img.size

        # Run OCR
        res = predictor([img], full_page=True)[0]

        # Extract blocks data
        blocks_data = []
        for b in res.blocks:
            ys = [pt[1] for pt in b.polygon]
            y1, y2 = min(ys) / h, max(ys) / h
            yc = (y1 + y2) / 2
            raw_text = strip_html_tags(b.html)
            blocks_data.append({
                "label": b.label,
                "confidence": getattr(b, "confidence", 1.0),
                "polygon": b.polygon,
                "bbox_norm": {"y1": y1, "y2": y2, "yc": yc},
                "html": b.html,
                "text": raw_text,
                "reading_order": getattr(b, "reading_order", 0)
            })

        page_record = {
            "page": p,
            "image_size": {"width": w, "height": h},
            "blocks": blocks_data
        }

        # Flush to disk immediately
        page_json = os.path.join(surya_pages_dir, f"page_{p}.json")
        with open(page_json, "w", encoding="utf-8") as f:
            json.dump(page_record, f, ensure_ascii=False, indent=2)

        t1 = time.time()
        print(f"done in {t1 - t0:.2f}s ({len(blocks_data)} blocks)", flush=True)

    # Now assemble surya_part1_full_baseline.txt
    print("\nAssembling klal-aligned baseline text from Surya page results...")
    klal_texts = {k: [] for k in range(1, corpus_io.PART1_MAX_KLAL + 1)}

    for p in pages:
        page_json = os.path.join(surya_pages_dir, f"page_{p}.json")
        if not os.path.exists(page_json):
            continue
        with open(page_json, "r", encoding="utf-8") as f:
            page_data = json.load(f)

        page_klalim = page_to_klalim.get(p, [])
        if not page_klalim:
            continue

        for b in page_data["blocks"]:
            # Skip page headers and footers
            if b["label"] in ("PageHeader", "PageFooter", "Header", "Footer"):
                continue
            text = b["text"].strip()
            if not text:
                continue

            yc = b["bbox_norm"]["yc"]
            klal_id = match_block_to_klal(yc, page_klalim)
            if klal_id and 1 <= klal_id <= corpus_io.PART1_MAX_KLAL:
                klal_texts[klal_id].append(text)

    baseline_txt_path = os.path.join(output_dir, "surya_part1_full_baseline.txt")
    with open(baseline_txt_path, "w", encoding="utf-8") as f:
        for klal_id in range(1, corpus_io.PART1_MAX_KLAL + 1):
            val = raw_regions.get(str(klal_id), {})
            p_start = val.get("page", 0)
            page_nums = [p_start] if p_start else []
            for c in val.get("continuations", []):
                page_nums.append(c["page"])
            header_str = f"=== KLAL {klal_id} (Pages {','.join(str(pn) for pn in page_nums)}) ==="
            body_text = "\n".join(klal_texts[klal_id])
            f.write(f"{header_str}\n{body_text}\n\n")

    print(f"Successfully generated {baseline_txt_path} for 222 klalim!")


if __name__ == "__main__":
    run_surya_part1()
