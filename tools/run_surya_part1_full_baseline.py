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
import build_gematria_trace as bgt


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

    NOTE (2026-08-23, code review finding C18): the nearest-region fallback below
    never returns None, so a block enclosed by NO klal region is force-attached
    to whichever region happens to be closest. Small in practice on pages 14-76
    (2 blocks / 4 words) but silent by construction. Left as-is deliberately:
    tightening it changes which text every klal gets, which is a data-affecting
    change that needs its own measurement, not a drive-by.
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


def _marker_forms(klal_id):
    """The gematria numeral for klal_id plus its documented near-miss misreads.

    Reuses build_gematria_trace's own near_miss_variants/CONFUSION_PAIRS rather
    than hand-rolling a second confusion list - that constant is the measured
    one ("adding a pair here should mean someone measured it") and a private
    copy is exactly the Lesson 13 defect this repo keeps finding.
    """
    expected = corpus_io.klal_id_to_gematria(klal_id)
    return [expected] + bgt.near_miss_variants(expected)


def split_block_across_klalim(text, block_y1, block_y2, page_klalim, y_center):
    """Split one Surya layout block's text among the klalim its Y-SPAN covers.

    Returns [(klal_id, text_fragment), ...].

    WHY THIS EXISTS (code review finding C16, and Phase 1 of
    MULTI-WITNESS-REPAIR-AND-SYNTHESIS-PLAN.md, which specified it and left it
    unbuilt). Surya returns LAYOUT blocks, and it routinely groups two
    consecutive short klalim into a single <p>. The assembler assigned each
    block by its Y-CENTRE alone, so a merged block went entirely to whichever
    klal contained that centre and the other klal got NOTHING - producing an
    empty body that both downstream consumers then read as "Surya agrees with
    every word here" rather than "Surya has no reading here". 10 of Part 1's
    222 klalim were empty for this reason.

    The documented example is exact: on page 29 a single block spans
    y 0.452-0.902, covering klal 43 (0.453-0.557) AND klal 44 (0.559-0.983).
    Its centre 0.677 sits in klal 44, so klal 44 took the lot - even though the
    block's own text OPENS with `מג`, klal 43's marker.

    That marker is the split point. For every klal whose region the block
    overlaps, look for its gematria numeral (or a documented near-miss misread
    of it) as a standalone token, and cut there. If the markers are not found,
    fall back to the old centre-based assignment rather than guessing at a
    proportional split - a wrong cut invents text for two klalim instead of
    starving one, which is worse (Lesson 5).
    """
    # Overlap must be GENUINE, not a touching edge. klal_page_regions.json's
    # trim pass leaves adjacent klalim butted right up against each other
    # (klal 42 ends at y 0.452, klal 43 starts at 0.453), and a block beginning
    # exactly on that seam would otherwise "cover" the klal above it and steal
    # the head of the block - which is what misfiled klal 43's whole body under
    # klal 42 on the first attempt. EPS is a hair under one trim gap.
    EPS = 0.002
    covered = [k for k in page_klalim
               if min(k["bbox"]["y2"], block_y2) - max(k["bbox"]["y1"], block_y1) > EPS]
    covered.sort(key=lambda k: k["bbox"]["y1"])
    if len(covered) < 2:
        return [(match_block_to_klal(y_center, page_klalim), text)]

    words = text.split()
    norm = corpus_io.hebrew_letters_only

    # The FIRST covered klal is anchored at the block's start, not on a marker.
    # A block routinely begins part-way through a klal (its continuation text),
    # in which case that klal's marker is on an earlier block or an earlier page
    # and demanding one here would drop the head of the block entirely.
    #
    # Every LATER klal must be anchored on its own marker. Searching is strictly
    # forward from the previous cut, and - important - a marker that is not found
    # does NOT advance the cursor, so one missing numeral cannot swallow the
    # klalim after it. Lesson 6: a cursor-based search cascades if one bad match
    # corrupts the position everything after it searches from. That cascade is
    # what left klal 201 empty on the first attempt: its own marker `רא` sits at
    # the very start of the block, but klal 200's single-letter `ר` was searched
    # for first across the whole block, matched something spurious further in,
    # and pushed the cursor past `רא`.
    # If the block's very first token is itself one of the covered klalim's
    # markers, that klal - not merely the topmost one - owns the head. Belt and
    # braces with the EPS fix above: a block can legitimately begin exactly on a
    # marker, and anchoring the head to the wrong klal misfiles an entire body.
    head_owner = 0
    first_tok = norm(words[0]) if words else ""
    for idx, k in enumerate(covered):
        if first_tok and first_tok in {norm(f) for f in _marker_forms(k["klal_id"])}:
            head_owner = idx
            break

    # A marker match must also land roughly WHERE that klal's region sits inside
    # the block. Without this the near-miss variants (which exist so a misread
    # numeral still anchors) widen the match set enough to hit a stray token deep
    # in the body text and cut there - measured: klalim 12, 74 and 210 each lost
    # 30-360 words to exactly that before the guard, because a numeral-shaped
    # word occurs in ordinary prose far more often than a marker does. The block
    # is a vertical strip of one page, so a klal starting at fraction f of the
    # block's height should start near word f*len(words); allow generous slack
    # (line lengths vary) but not "anywhere".
    span_y = max(block_y2 - block_y1, 1e-6)
    POSITION_SLACK = 0.25  # fraction of the block's words

    cuts, cursor = [(covered[head_owner]["klal_id"], 0)], 0
    for k in covered[head_owner + 1:]:
        forms = {norm(f) for f in _marker_forms(k["klal_id"])}
        frac = (k["bbox"]["y1"] - block_y1) / span_y
        expected = frac * len(words)
        slack = max(POSITION_SLACK * len(words), 8)
        found = next(
            (i for i in range(cursor + 1, len(words))
             if norm(words[i]) in forms and abs(i - expected) <= slack),
            None)
        if found is None:
            continue  # no anchor for this klal - leave the cursor where it was
        cuts.append((k["klal_id"], found))
        cursor = found

    if len(cuts) < 2:
        # Not enough anchors to cut on - do not invent a boundary.
        return [(match_block_to_klal(y_center, page_klalim), text)]

    out = []
    for idx, (kid, start) in enumerate(cuts):
        end = cuts[idx + 1][1] if idx + 1 < len(cuts) else len(words)
        frag = " ".join(words[start:end]).strip()
        if frag:
            out.append((kid, frag))
    return out


def run_surya_part1(force_recompute=False, assemble_only=False, only_pages=None):
    output_dir = os.path.join(REPO, "tools", "second_witness_eval")
    surya_pages_dir = os.path.join(output_dir, "surya_pages")
    os.makedirs(surya_pages_dir, exist_ok=True)

    page_to_klalim, pages, raw_regions = load_part1_regions()
    print("=" * 80)
    print(f"RUNNING SURYA OCR FOR PART 1: {len(pages)} PAGES (Pages {min(pages)}..{max(pages)})")
    print("=" * 80)

    pages_to_process = []
    if not assemble_only:
        for p in pages:
            # --pages targets a re-OCR at specific pages. Re-running one page is
            # cheap and local; re-running all 63 to fix three is not, and it also
            # churns every other page's cached result for no reason.
            if only_pages and p not in only_pages:
                continue
            page_json = os.path.join(surya_pages_dir, f"page_{p}.json")
            if force_recompute or not os.path.exists(page_json):
                pages_to_process.append(p)

    predictor = None
    if pages_to_process:
        # Imported and loaded ONLY when there is actually a page to OCR.
        # Re-assembling the klal-aligned baseline from the cached per-page JSON
        # is free and is the common case after a change to the block->klal
        # mapping; it should not require Surya to be installed, let alone pay
        # for loading its models. --assemble-only forces that path.
        from surya.inference import SuryaInferenceManager
        from surya.recognition import RecognitionPredictor
        manager = SuryaInferenceManager()
        predictor = RecognitionPredictor(manager)

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

            bn = b["bbox_norm"]
            for klal_id, frag in split_block_across_klalim(
                    text, bn.get("y1", bn["yc"]), bn.get("y2", bn["yc"]),
                    page_klalim, bn["yc"]):
                if klal_id and 1 <= klal_id <= corpus_io.PART1_MAX_KLAL:
                    klal_texts[klal_id].append(frag)

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

    # Report coverage honestly rather than announcing success for all 222
    # (code review finding C16): an EMPTY body is "this witness has no reading
    # here", and both consumers of this file previously read it as "Surya
    # agrees with every word". Naming the empty klalim is what makes that
    # distinction visible to whoever runs this.
    empty = [k for k in range(1, corpus_io.PART1_MAX_KLAL + 1) if not klal_texts[k]]
    covered = corpus_io.PART1_MAX_KLAL - len(empty)
    print(f"Wrote {baseline_txt_path}")
    print(f"  klalim with Surya text: {covered}/{corpus_io.PART1_MAX_KLAL}")
    if empty:
        print(f"  klalim with NO Surya coverage ({len(empty)}): {empty}")
        print("  ^ these are NOT 'Surya agrees' - they are 'no reading'. "
              "Downstream must treat them as an absent witness.")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--force-recompute", action="store_true",
                    help="re-run Surya OCR even for pages already cached")
    ap.add_argument("--pages", type=str, default=None,
                    help="comma-separated page numbers to (re-)OCR, e.g. 30,48,73; "
                         "combine with --force-recompute to redo already-cached pages")
    ap.add_argument("--assemble-only", action="store_true",
                    help="rebuild the klal-aligned baseline from cached per-page "
                         "JSON without loading Surya at all (free, and the common "
                         "case after a block->klal mapping change)")
    a = ap.parse_args()
    only = {int(x) for x in a.pages.split(",")} if a.pages else None
    run_surya_part1(force_recompute=a.force_recompute, assemble_only=a.assemble_only,
                    only_pages=only)
