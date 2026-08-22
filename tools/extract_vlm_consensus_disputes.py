#!/usr/bin/env python3
"""
tools/extract_vlm_consensus_disputes.py

Extracts the 1,233 consensus disagreements between Corpus and Dual-VLM
(where VLM Pass A == VLM Pass B != Corpus clean_text).

Maps each word position to its exact scan page and bounding box,
and produces disputed_vlm_part1.json or merges into corrections_part1.json.
"""

import argparse
import json
import os
import re
import sys
import unicodedata
from difflib import SequenceMatcher

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "pipeline"))

import corpus_io as cio
import review_server as rs
import tools.second_witness_eval.evaluate_ocr_alignment as eval_script


def norm_word(w):
    w = unicodedata.normalize("NFKC", w)
    w = w.replace("־", "-").replace("״", '"').replace("׳", "'").replace("”", '"').replace("“", '"').replace("’", "'").replace("‘", "'")
    w = w.strip(" \t\n\r.•:,;!?-–—()[]{}")
    return w


def get_docai_word_bboxes(klal_id, words, page):
    norm = cio.hebrew_letters_only
    toks = cio.load_docai_page(page, cio.DOCAI_DIR)
    if not toks:
        return {}
    dtoks = [t for t in toks if norm(t.get("text", ""))]
    dwords = [norm(t.get("text", "")) for t in dtoks]
    corpus_norm = [norm(w) for w in words]
    sm = SequenceMatcher(None, corpus_norm, dwords, autojunk=False)
    result = {}
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ('equal', 'replace'):
            for offset in range(min(i2 - i1, j2 - j1)):
                tok = dtoks[j1 + offset]
                if tok.get("x1") is not None:
                    result[i1 + offset] = {
                        "x1": tok["x1"], "y1": tok["y1"],
                        "x2": tok["x2"], "y2": tok["y2"],
                    }
    return result


def extract_consensus_disputes():
    part1_path = os.path.join(REPO, "part1.json")
    corrections_path = os.path.join(REPO, "corrections_part1.json")
    regions_path = os.path.join(REPO, "klal_page_regions.json")
    vlm_a_path = os.path.join(REPO, "tools", "second_witness_eval", "vlm_part1_full_baseline.txt")
    vlm_b_path = os.path.join(REPO, "tools", "second_witness_eval", "vlm_part1_full_baseline_passB.txt")

    part1 = json.load(open(part1_path, "r", encoding="utf-8"))
    corrections_part1 = json.load(open(corrections_path, "r", encoding="utf-8")) if os.path.exists(corrections_path) else {}
    regions = json.load(open(regions_path, "r", encoding="utf-8"))

    with open(vlm_a_path, "r", encoding="utf-8") as f:
        vlm_a_text = f.read()
    with open(vlm_b_path, "r", encoding="utf-8") as f:
        vlm_b_text = f.read()

    vlm_a_dict = eval_script.parse_candidate_ocr(vlm_a_text)
    vlm_b_dict = eval_script.parse_candidate_ocr(vlm_b_text)

    existing_keys = set()
    for kid_str, cand_list in corrections_part1.items():
        kid = int(kid_str)
        for c in cand_list:
            w_idx = c.get("word_index")
            if w_idx is not None:
                existing_keys.add((kid, w_idx))

    # Also exclude positions already carrying an active decision of any type
    for d_type in ["manual_correction", "klal_flag", "candidate_choice", "disputed_choice"]:
        for (m_kid, m_widx) in rs.rd.all_current(d_type).keys():
            if m_widx is not None:
                existing_keys.add((m_kid, m_widx))

    new_disputed = []
    overlapping_count = 0

    for k in part1:
        kid = k["klal_id"]
        raw_words = k["clean_text"].split()
        cw = [norm_word(w) for w in raw_words]
        aw = [norm_word(w) for w in vlm_a_dict.get(kid, "").split()]
        bw = [norm_word(w) for w in vlm_b_dict.get(kid, "").split()]

        sm_ca = SequenceMatcher(None, cw, aw)
        sm_ab = SequenceMatcher(None, aw, bw)
        a_to_b = {block.a + i: bw[block.b + i] for block in sm_ab.get_matching_blocks() for i in range(block.size)}

        r_entry = regions.get(str(kid), {})
        pages = rs._klal_all_pages(kid)
        word_to_bbox = {}
        for p in pages:
            p_bboxes = get_docai_word_bboxes(kid, raw_words, p)
            for wi, bb in p_bboxes.items():
                word_to_bbox[wi] = (p, bb)

        for tag, i1, i2, j1, j2 in sm_ca.get_opcodes():
            if tag != "replace":
                continue
            for offset in range(min(i2 - i1, j2 - j1)):
                ci, aj = i1 + offset, j1 + offset
                if ci < len(cw) and aj < len(aw) and cw[ci] and aw[aj] and cw[ci] != aw[aj]:
                    if aj in a_to_b and a_to_b[aj] == aw[aj]:
                        if (kid, ci) in existing_keys:
                            overlapping_count += 1
                            continue

                        page_info = word_to_bbox.get(ci)
                        page_num = page_info[0] if page_info else r_entry.get("page")
                        bbox = page_info[1] if page_info else None

                        # Fallback bbox interpolation from neighbor words
                        if bbox is None and page_num:
                            for delta in [1, -1, 2, -2, 3, -3]:
                                neighbor_info = word_to_bbox.get(ci + delta)
                                if neighbor_info and neighbor_info[0] == page_num:
                                    bbox = dict(neighbor_info[1])
                                    break

                        new_disputed.append({
                            "klal_id": kid,
                            "word_index": ci,
                            "opcode": "replace",
                            "final_text": raw_words[ci],
                            "docai_reading": raw_words[ci],
                            "vlm_reading": aw[aj],
                            "flag": "current_text_may_be_wrong",
                            "page": page_num,
                            "bbox": bbox,
                            "reasoning": f"Dual-VLM consensus reading is '{aw[aj]}' (Pass A == Pass B), differing from stored text '{raw_words[ci]}'.",
                        })

    return new_disputed, overlapping_count


def main():
    parser = argparse.ArgumentParser(description="Extract dual-VLM consensus disputed words for Part 1.")
    parser.add_argument("--output", default="disputed_vlm_part1.json", help="Path to output json file")
    parser.add_argument("--merge", action="store_true", help="Merge directly into corrections_part1.json")
    args = parser.parse_args()

    disputed, overlapping = extract_consensus_disputes()
    print(f"Extracted {len(disputed)} brand-new dual-VLM consensus disputed words ({overlapping} overlapping with existing candidates).")

    out_path = os.path.join(REPO, args.output)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(disputed, f, indent=2, ensure_ascii=False)
    print(f"Saved dataset to {out_path}")

    if args.merge:
        corrections_path = os.path.join(REPO, "corrections_part1.json")
        existing = json.load(open(corrections_path, "r", encoding="utf-8")) if os.path.exists(corrections_path) else {}
        
        merged_count = 0
        for item in disputed:
            kid_str = str(item["klal_id"])
            existing.setdefault(kid_str, []).append(item)
            merged_count += 1
            
        # Sort each klal's entries by word_index
        for kid_str in existing:
            existing[kid_str].sort(key=lambda x: x.get("word_index", 0))
            
        with open(corrections_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
        print(f"Merged {merged_count} new disputed items into {corrections_path} (Total now: {sum(len(v) for v in existing.values())})")


if __name__ == "__main__":
    main()
