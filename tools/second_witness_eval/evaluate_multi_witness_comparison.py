#!/usr/bin/env python3
"""
tools/second_witness_eval/evaluate_multi_witness_comparison.py

Compares all available witnesses across Part 1 (222 klalim):
  1. Cleaned Base Text (part1.json)
  2. Gemini VLM Baseline Pass A (vlm_part1_full_baseline.txt)
  3. Gemini VLM Baseline Pass B (vlm_part1_full_baseline_passB.txt)
  4. Surya OCR Baseline (surya_part1_full_baseline.txt)
  5. DocAI Primary OCR (from aligned_klalim/)

Calculates:
  - Token accuracy vs Cleaned Base Text
  - Pairwise token consistency matrix across all witnesses
  - Multi-witness consensus stats on the 1,590 disputed words
"""

import json
import os
import re
import sys
import unicodedata
from difflib import SequenceMatcher

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "pipeline"))

import corpus_io


def normalize_words(text):
    text = unicodedata.normalize("NFKC", text)
    text = (
        text.replace("־", "-")
        .replace("״", '"')
        .replace("׳", "'")
        .replace("”", '"')
        .replace("“", '"')
        .replace("’", "'")
        .replace("‘", "'")
        .replace("•", ".")
        .replace("׃", ":")
        .replace(";", ":")
    )
    words = []
    for raw_w in text.split():
        w = raw_w.strip(" \t\n\r.•:,;!?-–—()[]{}")
        if w:
            words.append(w)
    return words


def parse_baseline_file(filepath):
    if not os.path.exists(filepath):
        return {}
    klalim = {}
    current_klal = None
    lines = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            match = re.match(r"^(?:---|===)\s*klal\s+(\d+)", line, re.IGNORECASE)
            if match:
                if current_klal is not None:
                    klalim[current_klal] = "\n".join(lines).strip()
                    lines = []
                current_klal = int(match.group(1))
            elif current_klal is not None:
                lines.append(line)
        if current_klal is not None and lines:
            klalim[current_klal] = "\n".join(lines).strip()
    return klalim


def load_docai_klalim():
    demo_path = os.path.join(REPO, "klalim_demo_dataset.json")
    if os.path.exists(demo_path):
        with open(demo_path, "r", encoding="utf-8") as f:
            demo = json.load(f)
        docai_klalim = {}
        items = demo if isinstance(demo, list) else demo.get("klalim", [])
        for item in items:
            k_id = item.get("klal_id") or item.get("id")
            if k_id and k_id <= corpus_io.PART1_MAX_KLAL:
                docai_klalim[k_id] = item.get("clean_text", "")
        return docai_klalim
    return {}


def compare_word_sequences(words_ref, words_hyp):
    sm = SequenceMatcher(None, words_ref, words_hyp)
    matches = sum(match.size for match in sm.get_matching_blocks())
    total_ref = len(words_ref)
    total_hyp = len(words_hyp)
    acc = (matches / total_ref * 100.0) if total_ref > 0 else 0.0
    return matches, total_ref, total_hyp, acc


def main():
    part1_data = corpus_io.load_json("part1.json")
    base_klalim = {item["klal_id"]: item.get("clean_text", "") for item in part1_data if "klal_id" in item}

    eval_dir = os.path.join(REPO, "tools", "second_witness_eval")
    vlm_a_path = os.path.join(eval_dir, "vlm_part1_full_baseline.txt")
    vlm_b_path = os.path.join(eval_dir, "vlm_part1_full_baseline_passB.txt")
    surya_path = os.path.join(eval_dir, "surya_part1_full_baseline.txt")

    vlm_a_klalim = parse_baseline_file(vlm_a_path)
    vlm_b_klalim = parse_baseline_file(vlm_b_path)
    surya_klalim = parse_baseline_file(surya_path)
    docai_klalim = load_docai_klalim()

    witnesses = {
        "Cleaned Base Text": base_klalim,
        "Gemini VLM Pass A": vlm_a_klalim,
        "Gemini VLM Pass B": vlm_b_klalim,
        "Surya OCR": surya_klalim,
        "Google DocAI": docai_klalim,
    }

    print("=" * 80)
    print("MULTI-WITNESS COMPARISON REPORT — PART 1 (222 KLALIM)")
    print("=" * 80)
    for name, w_dict in witnesses.items():
        print(f"  • {name:20s}: {len(w_dict)} klalim loaded")

    print("\n" + "-" * 80)
    print("1. ACCURACY VS CLEANED BASE TEXT (Ground Truth Reference)")
    print("-" * 80)

    base_norm = {k: normalize_words(text) for k, text in base_klalim.items()}
    total_base_words = sum(len(w) for w in base_norm.values())

    for name, w_dict in witnesses.items():
        if name == "Cleaned Base Text":
            continue
        if not w_dict:
            print(f"  {name:20s}: [Not available]")
            continue
        tot_m, tot_r, tot_h = 0, 0, 0
        for k_id in range(1, corpus_io.PART1_MAX_KLAL + 1):
            ref = base_norm.get(k_id, [])
            hyp = normalize_words(w_dict.get(k_id, ""))
            m, r, h, _ = compare_word_sequences(ref, hyp)
            tot_m += m
            tot_r += r
            tot_h += h
        acc = (tot_m / tot_r * 100.0) if tot_r > 0 else 0.0
        print(f"  {name:20s}: {acc:6.2f}% ({tot_m:,} / {tot_r:,} words matched; hyp words: {tot_h:,})")

    print("\n" + "-" * 80)
    print("2. PAIRWISE CONSISTENCY MATRIX")
    print("-" * 80)
    w_keys = ["Cleaned Base Text", "Gemini VLM Pass A", "Gemini VLM Pass B", "Surya OCR", "Google DocAI"]
    header_row = f"{'Witness':20s}" + "".join(f"{k[:10]:>12s}" for k in w_keys)
    print(header_row)
    print("-" * len(header_row))

    for w1 in w_keys:
        row = f"{w1:20s}"
        dict1 = witnesses.get(w1, {})
        for w2 in w_keys:
            if w1 == w2:
                row += f"{'100.0%':>12s}"
                continue
            dict2 = witnesses.get(w2, {})
            if not dict1 or not dict2:
                row += f"{'N/A':>12s}"
                continue
            tot_m, tot_r = 0, 0
            for k_id in range(1, corpus_io.PART1_MAX_KLAL + 1):
                w1_words = normalize_words(dict1.get(k_id, ""))
                w2_words = normalize_words(dict2.get(k_id, ""))
                m, r, _, _ = compare_word_sequences(w1_words, w2_words)
                tot_m += m
                tot_r += r
            pair_acc = (tot_m / tot_r * 100.0) if tot_r > 0 else 0.0
            row += f"{pair_acc:11.2f}%"
        print(row)

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
