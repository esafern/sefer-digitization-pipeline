#!/usr/bin/env python3
# [STANDALONE] Canonical list of every abbreviation-marked token in Part 1.
#
# Convention (matches detect_ligature_corruption.py's QUOTE_CHARS /
# has_gershayim, the existing project-wide definition - not invented here):
# an abbreviation token is one that CONTAINS a gershayim/geresh character
# anywhere (U+05F4 ״, U+05F3 ׳, or the ASCII " / ' this OCR pipeline
# sometimes normalizes them to), not strictly one that ENDS in it. A
# multi-letter acronym (rashei tevot) places the gershayim before its LAST
# letter, e.g. רש"י (Rashi) = ר-ש-"-י - the mark is second-to-last, not
# final. A single-word abbreviation places a geresh truly last, e.g. וכו'.
# Prefixed forms (ו/ב/ה/מ/כ/ל/ש/ד attached directly, standard Hebrew
# morphology) push the mark further from either edge, e.g. בכנה"ג. This
# script counts a token as abbreviation-marked whenever ANY of those
# characters appear in it, matching that established convention exactly.
#
# Output: prints the full frequency-sorted list. Read-only, never touches
# part1.json.
#
# Usage: python3 extract_abbreviation_forms.py [--json out.json]
import argparse
import json
import os
from collections import Counter

REPO = os.path.dirname(os.path.abspath(__file__))
QUOTE_CHARS = set('"\'׳״')


def is_abbreviation(word):
    return any(c in word for c in QUOTE_CHARS)


def extract(part1):
    counts = Counter()
    klalim_by_form = {}
    for k in part1:
        seen_this_klal = set()
        for w in k["clean_text"].split():
            if is_abbreviation(w):
                counts[w] += 1
                if w not in seen_this_klal:
                    klalim_by_form.setdefault(w, []).append(k["klal_id"])
                    seen_this_klal.add(w)
    return counts, klalim_by_form


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="also write {form: {count, klalim}} to this path")
    args = ap.parse_args()

    part1 = json.load(open(os.path.join(REPO, "part1.json"), encoding="utf-8"))
    counts, klalim_by_form = extract(part1)
    total = sum(counts.values())
    if not counts:
        print("No abbreviation-marked tokens found in part1.json.")
        return

    print(f"{len(counts)} unique abbreviation-marked forms, {total} total occurrences "
          f"across Part 1's {sum(len(k['clean_text'].split()) for k in part1)} words.\n")
    singles = sum(1 for n in counts.values() if n == 1)
    print(f"{singles} forms ({singles/len(counts):.1%}) occur exactly once - mostly rare "
          f"proper-name acronyms and one-off citations.\n")

    for w, n in counts.most_common():
        print(f"  {n:4d}  {w}")

    if args.json:
        out = {w: {"count": n, "klalim": klalim_by_form[w]} for w, n in counts.items()}
        json.dump(out, open(args.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"\nWrote {args.json}")


if __name__ == "__main__":
    main()
