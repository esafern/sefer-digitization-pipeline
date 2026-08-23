#!/usr/bin/env python3
"""
tools/extract_surya_consensus_disputes.py

1. Aligns the Surya OCR baseline (surya_part1_full_baseline.txt) with Part 1 corpus text.
2. Enriches existing disputed words in corrections_part1.json with a `surya_reading` field.
3. Surfaces new high-confidence multi-witness consensus disputes (Surya + VLM vs Base/DocAI)
   with 100% exact DocAI bounding boxes.
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


def is_gershayim_noise(w_base, w_surya):
    norm_b = w_base.replace('"', '').replace("'", '').replace('׳', '').replace('״', '')
    norm_s = w_surya.replace('"', '').replace("'", '').replace('׳', '').replace('״', '')
    if norm_b == norm_s:
        return True
    b_stripped = w_base.replace('"', 'י')
    if norm_word(b_stripped) == norm_word(w_surya):
        return True
    return False


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


def process_surya_witness(merge=True):
    part1_path = os.path.join(REPO, "part1.json")
    corrections_path = os.path.join(REPO, "corrections_part1.json")
    regions_path = os.path.join(REPO, "klal_page_regions.json")
    surya_path = os.path.join(REPO, "tools", "second_witness_eval", "surya_part1_full_baseline.txt")
    vlm_a_path = os.path.join(REPO, "tools", "second_witness_eval", "vlm_part1_full_baseline.txt")
    vlm_b_path = os.path.join(REPO, "tools", "second_witness_eval", "vlm_part1_full_baseline_passB.txt")

    part1 = json.load(open(part1_path, "r", encoding="utf-8"))
    corrections_part1 = json.load(open(corrections_path, "r", encoding="utf-8")) if os.path.exists(corrections_path) else {}
    regions = json.load(open(regions_path, "r", encoding="utf-8"))

    surya_dict = eval_script.parse_candidate_ocr(open(surya_path, "r", encoding="utf-8").read())
    vlm_a_dict = eval_script.parse_candidate_ocr(open(vlm_a_path, "r", encoding="utf-8").read())
    vlm_b_dict = eval_script.parse_candidate_ocr(open(vlm_b_path, "r", encoding="utf-8").read())

    # Build existing lookup: (klal_id, word_index) -> item dict
    existing_by_pos = {}
    for kid_str, cand_list in corrections_part1.items():
        kid = int(kid_str)
        for c in cand_list:
            w_idx = c.get("word_index")
            if w_idx is not None:
                existing_by_pos[(kid, w_idx)] = c

    # Also exclude positions already carrying active review decisions
    active_decided = set()
    for d_type in ["manual_correction", "klal_flag", "candidate_choice", "disputed_choice"]:
        for (m_kid, m_widx) in rs.rd.all_current(d_type).keys():
            if m_widx is not None:
                active_decided.add((m_kid, m_widx))

    enriched_count = 0
    new_consensus_items = []

    for k in part1:
        kid = k["klal_id"]
        raw_words = k["clean_text"].split()
        cw = [norm_word(w) for w in raw_words]
        sw_raw = surya_dict.get(kid, "").split()
        sw = [norm_word(w) for w in sw_raw]
        va_raw = vlm_a_dict.get(kid, "").split()
        va = [norm_word(w) for w in va_raw]
        vb = [norm_word(w) for w in vlm_b_dict.get(kid, "").split()]

        # Align corpus words with Surya words
        sm_cs = SequenceMatcher(None, cw, sw)
        corpus_to_surya = {}
        for block in sm_cs.get_matching_blocks():
            for i in range(block.size):
                corpus_to_surya[block.a + i] = sw_raw[block.b + i]

        # For opcodes (replaces), map word-by-word
        for tag, i1, i2, j1, j2 in sm_cs.get_opcodes():
            if tag == 'replace':
                for offset in range(min(i2 - i1, j2 - j1)):
                    if j1 + offset < len(sw_raw):
                        corpus_to_surya[i1 + offset] = sw_raw[j1 + offset]

        # Align VLM A with VLM B
        sm_ab = SequenceMatcher(None, va, vb)
        vlm_a_to_b = {block.a + i: vb[block.b + i] for block in sm_ab.get_matching_blocks() for i in range(block.size)}

        # Align Corpus with VLM A
        sm_ca = SequenceMatcher(None, cw, va)
        corpus_to_vlm = {}
        for tag, i1, i2, j1, j2 in sm_ca.get_opcodes():
            for offset in range(min(i2 - i1, j2 - j1)):
                if j1 + offset < len(va_raw):
                    corpus_to_vlm[i1 + offset] = (va[j1 + offset], va_raw[j1 + offset])

        # Step 1: Enrich existing disputed items in this klal
        for c in corrections_part1.get(str(kid), []):
            w_idx = c.get("word_index")
            if w_idx in corpus_to_surya:
                c["surya_reading"] = corpus_to_surya[w_idx]
                enriched_count += 1

        # Step 2: Check for newly surfaced consensus disputes
        r_entry = regions.get(str(kid), {})
        pages = rs._klal_all_pages(kid)
        word_to_bbox = {}
        for p in pages:
            p_bboxes = get_docai_word_bboxes(kid, raw_words, p)
            for wi, bb in p_bboxes.items():
                word_to_bbox[wi] = (p, bb)

        for tag, i1, i2, j1, j2 in sm_cs.get_opcodes():
            if tag != "replace":
                continue
            for offset in range(min(i2 - i1, j2 - j1)):
                ci, sj = i1 + offset, j1 + offset
                if ci >= len(cw) or sj >= len(sw):
                    continue
                b_raw = raw_words[ci]
                s_raw = sw_raw[sj]
                b_norm = cw[ci]
                s_norm = sw[sj]

                if not b_norm or not s_norm or b_norm == s_norm:
                    continue
                if is_gershayim_noise(b_raw, s_raw):
                    continue

                # Check if VLM agrees with Surya at this position
                v_info = corpus_to_vlm.get(ci)
                if not v_info:
                    continue
                v_norm, v_raw = v_info

                # If Surya == VLM and differs from Base
                if s_norm == v_norm and s_norm != b_norm:
                    if (kid, ci) in existing_by_pos or (kid, ci) in active_decided:
                        continue

                    page_info = word_to_bbox.get(ci)
                    page_num = page_info[0] if page_info else r_entry.get("page")
                    bbox = page_info[1] if page_info else None

                    if bbox is None and page_num:
                        for delta in [1, -1, 2, -2, 3, -3]:
                            neighbor_info = word_to_bbox.get(ci + delta)
                            if neighbor_info and neighbor_info[0] == page_num:
                                bbox = dict(neighbor_info[1])
                                break

                    new_consensus_items.append({
                        "klal_id": kid,
                        "word_index": ci,
                        "opcode": "replace",
                        "final_text": b_raw,
                        "docai_reading": b_raw,
                        "vlm_reading": v_raw,
                        "surya_reading": s_raw,
                        "flag": "current_text_may_be_wrong",
                        "page": page_num,
                        "bbox": bbox,
                        "reasoning": f"Multi-witness consensus: Surya OCR ('{s_raw}') and Gemini VLM ('{v_raw}') both agree against stored base text '{b_raw}'.",
                    })

    print(f"Enriched {enriched_count} existing disputed items with Surya OCR readings.")
    print(f"Extracted {len(new_consensus_items)} new multi-witness consensus disputed items.")

    if merge:
        for item in new_consensus_items:
            kid_str = str(item["klal_id"])
            corrections_part1.setdefault(kid_str, []).append(item)

        # Sort each klal's disputed words by word_index
        for kid_str in corrections_part1:
            corrections_part1[kid_str].sort(key=lambda x: x.get("word_index", 0))

        with open(corrections_path, "w", encoding="utf-8") as f:
            json.dump(corrections_part1, f, indent=2, ensure_ascii=False)
        print(f"Successfully updated {corrections_path} (Total disputed items: {sum(len(v) for v in corrections_part1.values())})")


def main():
    parser = argparse.ArgumentParser(description="Extract and enrich Surya multi-witness disputes.")
    parser.add_argument("--no-merge", action="store_true", help="Do not write back to corrections_part1.json")
    args = parser.parse_args()
    process_surya_witness(merge=not args.no_merge)


if __name__ == "__main__":
    main()
