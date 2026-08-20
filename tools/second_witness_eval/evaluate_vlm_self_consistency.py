#!/usr/bin/env python3
"""
tools/second_witness_eval/evaluate_vlm_self_consistency.py

Compares two independent VLM baseline transcription passes (Pass A vs Pass B)
word-by-word across all 222 klalim in Part 1 to compute:
1. Overall Self-Consistency Agreement %
2. Exact locations where model sampling variance occurred
"""

import os
import sys
import re
from difflib import SequenceMatcher

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "pipeline"))
import corpus_io


def parse_vlm_pass(filepath):
    if not os.path.exists(filepath):
        return None
    klalim_text = {}
    current_klal = None
    lines = []

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^===\s*KLAL\s+(\d+)", line)
            if m:
                if current_klal is not None:
                    klalim_text[current_klal] = " ".join(lines).strip()
                    lines = []
                current_klal = int(m.group(1))
            elif current_klal is not None:
                lines.append(line.strip())
        if current_klal is not None and lines:
            klalim_text[current_klal] = " ".join(lines).strip()

    return klalim_text


def evaluate_self_consistency():
    pass_a_file = os.path.join(REPO, "tools", "second_witness_eval", "vlm_part1_full_baseline.txt")
    pass_b_file = os.path.join(REPO, "tools", "second_witness_eval", "vlm_part1_full_baseline_passB.txt")

    pass_a = parse_vlm_pass(pass_a_file)
    pass_b = parse_vlm_pass(pass_b_file)

    if not pass_a or not pass_b:
        print("Waiting for both Pass A and Pass B output files to complete...")
        return

    common_klalim = sorted(set(pass_a.keys()) & set(pass_b.keys()))
    print("=" * 85)
    print(f"EVALUATING VLM SELF-CONSISTENCY (PASS A vs PASS B Across {len(common_klalim)} Klalim)")
    print("=" * 85)

    total_words_a = 0
    total_words_b = 0
    total_matches = 0
    disagreements = []

    for k in common_klalim:
        words_a = pass_a[k].split()
        words_b = pass_b[k].split()
        sm = SequenceMatcher(None, words_a, words_b)
        matches = sum(triple.size for triple in sm.get_matching_blocks())

        total_words_a += len(words_a)
        total_words_b += len(words_b)
        total_matches += matches

        acc = (matches / max(len(words_a), 1)) * 100
        if len(words_a) != len(words_b) or acc < 95.0:
            disagreements.append((k, len(words_a), len(words_b), matches, acc))

    overall_acc = (total_matches / max(total_words_a, 1)) * 100
    print(f"Total Words (Pass A): {total_words_a}")
    print(f"Total Words (Pass B): {total_words_b}")
    print(f"Exact Sequence Matches: {total_matches}")
    print(f"Self-Consistency Agreement Rate: {overall_acc:.2f}%\n")

    if disagreements:
        print("Klalim with Sampling Differences (<95% match or word count mismatch):")
        print(f"| Klal | Pass A Words | Pass B Words | Matches | Agreement % |")
        print(f"|:----:|:------------:|:------------:|:-------:|:-----------:|")
        for k, wa, wb, m, acc in disagreements[:20]:
            print(f"| {k:4d} | {wa:12d} | {wb:12d} | {m:7d} | {acc:10.2f}% |")

    print("=" * 85)


if __name__ == "__main__":
    evaluate_self_consistency()
