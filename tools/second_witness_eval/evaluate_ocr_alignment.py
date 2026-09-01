#!/usr/bin/env python3
"""
dicta_eval/evaluate_ocr_alignment.py

Evaluates candidate second-witness OCR text (e.g. Dicta, Kraken, TrOCR)
against ground truth for klalim 8-22.

Requires the candidate to carry `--- klal N` / `=== KLAL N` headers; a raw
engine dump has none and scores 0% here. Use tools/compare_ocr_engines.py
for those - it anchors on content instead.

NOTE 2026-08-31: klalim 8-22 are Berlin pages 18-20, but they are NOT the
pages in yad-malachi-berlin-sample.pdf, which is pages 19-21 / klalim 12-24
(PROJECT-STATUS.md item 0K).

Usage:
  python3 dicta_eval/evaluate_ocr_alignment.py --ocr-file <path_to_candidate_ocr_text>
"""

import argparse
import json
import os
import re
import sys
from difflib import SequenceMatcher

# Ensure pipeline modules are importable
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "pipeline"))

import corpus_io


def parse_groundtruth(use_part1=False):
    if use_part1:
        part1_data = corpus_io.load_json("part1.json")
        klalim_text = {}
        for item in part1_data:
            klal_id = item.get("klal_id")
            if klal_id:
                klalim_text[klal_id] = item.get("clean_text", "")
        return klalim_text

    gt_path = os.path.join(REPO, "tools", "second_witness_eval", "groundtruth_klal_8_22.txt")
    if not os.path.exists(gt_path):
        raise FileNotFoundError(f"Ground truth file not found at {gt_path}")

    klalim_text = {}
    current_klal = None
    lines = []

    with open(gt_path, "r", encoding="utf-8") as f:
        for line in f:
            match = re.match(r"^---\s*klal\s+(\d+)", line)
            if match:
                if current_klal is not None:
                    klalim_text[current_klal] = " ".join(lines).strip()
                    lines = []
                current_klal = int(match.group(1))
            elif current_klal is not None:
                lines.append(line.strip())

        if current_klal is not None and lines:
            klalim_text[current_klal] = " ".join(lines).strip()

    return klalim_text


def parse_candidate_ocr(ocr_text):

    klalim_ocr = {}
    current_klal = None
    lines = []

    for line in ocr_text.splitlines():
        # FIXED 2026-08-20 (code review): the optional '(?:---|===)?' plus
        # unanchored re.search matched "klal <digits>" ANYWHERE on any line,
        # not just a genuine header - splitting/truncating the preceding
        # klal's text on a false hit and skewing the accuracy numbers this
        # script reports. Both real formats (vlm_klal_8_22_ocr.txt's
        # "--- klal N", vlm_part1_full_baseline*.txt's "=== KLAL N (...)")
        # always start the line with the marker, so anchor like
        # parse_groundtruth's own ^---\s*klal\s+(\d+) does, just accepting
        # either marker.
        match = re.match(r"^(?:---|===)\s*klal\s+(\d+)", line, re.IGNORECASE)
        if match:
            if current_klal is not None:
                klalim_ocr[current_klal] = " ".join(lines).strip()
                lines = []
            current_klal = int(match.group(1))
        elif current_klal is not None:
            lines.append(line.strip())

    if current_klal is not None and lines:
        klalim_ocr[current_klal] = " ".join(lines).strip()

    # Fallback if no klal headers found: store under klal 0 for global alignment
    if not klalim_ocr:
        klalim_ocr[0] = ocr_text.strip()

    return klalim_ocr


def load_candidates():
    candidates_path = os.path.join(REPO, "corrections_verified_part1.json")
    if not os.path.exists(candidates_path):
        return []
    with open(candidates_path, "r", encoding="utf-8") as f:
        all_candidates = json.load(f)
    return [c for c in all_candidates if 8 <= c.get("klal_id", 0) <= 22]


import unicodedata


def normalize_text_punct(text):
    """
    Normalizes Hebrew punctuation and symbols:
    - Normalizes Hebrew gershayim/geresh Unicode variants to standard ASCII ' and "
    - Normalizes bullet points '•', mid-dots, colons, periods
    - Strips outer punctuation around words
    - Preserves internal quotes in abbreviations (e.g. רש"י, ע"ש, וכו')
    """
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


def evaluate_ocr(ocr_filepath, use_part1=False, normalize_punct=False):
    with open(ocr_filepath, "r", encoding="utf-8") as f:
        ocr_raw = f.read()

    gt_klalim = parse_groundtruth(use_part1=use_part1)
    ocr_klalim = parse_candidate_ocr(ocr_raw)
    candidates = load_candidates()

    total_gt_words = 0
    total_ocr_words = 0
    total_matched_words = 0

    print("=" * 90)
    norm_label = " (Punctuation Normalized)" if normalize_punct else ""
    print(f"EVALUATING SECOND-WITNESS OCR: {os.path.basename(ocr_filepath)}{norm_label}")
    print("=" * 90)

    def tokenize(text):
        if normalize_punct:
            return normalize_text_punct(text)
        return [w for w in text.split() if w]

    print("\n### Per-Klal Word Alignment Summary\n")
    print("| Klal | GT Words | OCR Words | Matches | Token Acc % |")
    print("|:----:|:--------:|:---------:|:-------:|:-----------:|")

    aligned_tokens = {}

    target_klalim = sorted(ocr_klalim.keys()) if use_part1 else list(range(8, 23))

    for klal_id in target_klalim:
        if klal_id not in gt_klalim:
            continue
        gt_text = gt_klalim.get(klal_id, "")
        gt_words = tokenize(gt_text)
        total_gt_words += len(gt_words)

        ocr_text = ocr_klalim.get(klal_id, "")
        ocr_words = tokenize(ocr_text)

        sm = SequenceMatcher(None, gt_words, ocr_words)
        matching_blocks = sm.get_matching_blocks()
        matches = sum(b.size for b in matching_blocks)

        total_ocr_words += len(ocr_words)
        total_matched_words += matches

        pct = (matches / max(1, len(gt_words))) * 100.0
        print(f"| {klal_id:4d} | {len(gt_words):8d} | {len(ocr_words):9d} | {matches:7d} | {pct:10.2f}% |")

        # Map GT index to OCR token
        gt_to_ocr = {}
        for b in matching_blocks:
            for i in range(b.size):
                gt_to_ocr[b.a + i] = ocr_words[b.b + i]
        aligned_tokens[klal_id] = gt_to_ocr

    overall_pct = (total_matched_words / max(1, total_gt_words)) * 100.0
    print(f"| **TOTAL** | **{total_gt_words}** | **{total_ocr_words}** | **{total_matched_words}** | **{overall_pct:.2f}%** |")

    if candidates and not use_part1:
        print("\n### Candidate Verification Breakdown (23 Candidates in Klalim 8-22)\n")
        print("| Klal | Pos | Original (DocAI) | Corrected (Corpus) | Vision | Witness Reading | Witness Verdict |")
        print("|:----:|:---:|:----------------:|:------------------:|:------:|:---------------:|:---------------:|")

        for c in candidates:
            klal_id = c.get("klal_id")
            pos = c.get("word_index_in_final_text", -1)
            orig = c.get("original_word") or "None"
            corr = c.get("corrected_word") or "None"
            v_sel = c.get("vision_selected") or "N/A"

            gt_map = aligned_tokens.get(klal_id, {})
            witness_word = gt_map.get(pos, "—")

            if witness_word == corr:
                verdict = "MATCHES_CORRECTED (Opt B/Corpus)"
            elif witness_word == orig:
                verdict = "MATCHES_ORIGINAL (Opt A/DocAI)"
            elif witness_word == "—":
                verdict = "UNALIGNED / MISSING"
            else:
                verdict = "THIRD_READING"

            print(f"| {klal_id:4d} | {pos:3d} | {orig:16s} | {corr:18s} | {v_sel:6s} | {witness_word:15s} | {verdict:30s} |")

    print("\n" + "=" * 90)


def main():
    parser = argparse.ArgumentParser(description="Evaluate second-witness OCR against Berlin Klalim ground truth.")
    parser.add_argument("--ocr-file", help="Path to OCR text file to evaluate")
    parser.add_argument("--use-part1", action="store_true", help="Use all 222 klalim from part1.json as ground truth")
    parser.add_argument("--normalize-punct", action="store_true", help="Normalize Hebrew punctuation and strip outer symbols")
    args = parser.parse_args()

    if not args.ocr_file or not os.path.exists(args.ocr_file):
        print("Usage: python3 tools/second_witness_eval/evaluate_ocr_alignment.py --ocr-file <path> [--use-part1] [--normalize-punct]")
        print("Note: Ground truth file is ready at tools/second_witness_eval/groundtruth_klal_8_22.txt or --use-part1.")
        sys.exit(1)

    evaluate_ocr(args.ocr_file, use_part1=args.use_part1, normalize_punct=args.normalize_punct)


if __name__ == "__main__":
    main()
