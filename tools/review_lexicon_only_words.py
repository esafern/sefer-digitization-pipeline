#!/usr/bin/env python3
# [STANDALONE] Which words exist in THIS corpus and in no book of the
# independent reference corpus - and, for each, the nearest attested form.
#
# WHY. `lexicon.txt` was built from this corpus's own OCR output, so it contains
# the OCR errors and then validates them: measured 2026-08-26, **22% of its
# 18,936 entries appear nowhere in the 166 reference books (6.18M words)**, and
# `כסכתא` and `בחרא` - both confirmed corruptions - were among them. Any check
# run against lexicon.txt is only as independent as lexicon.txt, which is not
# independent at all. This report is the list that hole hides.
#
# READ THE TIERS, NOT THE TOTAL. A word absent from the reference corpus is not
# thereby wrong - Yad Malachi legitimately uses vocabulary those books do not.
# The signal is absence PLUS a near neighbour that is well attested; a word with
# no near neighbour is most likely just this work's own vocabulary. The output
# carries every occurrence so a reviewer can go straight to the context, and it
# is deliberately NOT a purge list (tools/validate_lexicon_independent.py's
# header says the same thing about the same set, and it is right).
#
# Written 2026-08-26 at the reviewer's request; the report it emits was
# previously produced by a throwaway script, which is exactly the
# hand-maintained-derived-file pattern Lesson 13 forbids.
#
# Usage:
#   python3 tools/review_lexicon_only_words.py                 # -> lexicon_yad_malachi_only.json
#   python3 tools/review_lexicon_only_words.py --min-ref 40    # attestation floor for a "near" form
import argparse
import collections
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pipeline"))

import corpus_io as cio  # noqa: E402
from repair_filters import docai_filter as df  # noqa: E402

OUT_PATH = cio.repo_path("lexicon_yad_malachi_only.json")
HEB = "אבגדהוזחטיכךלמםנןסעפףצץקרשת"
MIN_LETTERS = 4          # below this, particles and numerals dominate the noise


def near_forms(word, ref, min_ref):
    """Attested forms one substitution, insertion or deletion away."""
    out = set()
    for i in range(len(word)):
        for c in HEB:
            if c != word[i]:
                cand = word[:i] + c + word[i + 1:]
                if ref.get(cand, 0) >= min_ref:
                    out.add((cand, ref[cand], "substitution"))
    for i in range(len(word) + 1):
        for c in HEB:
            cand = word[:i] + c + word[i:]
            if ref.get(cand, 0) >= min_ref:
                out.add((cand, ref[cand], "insertion"))
    for i in range(len(word)):
        cand = word[:i] + word[i + 1:]
        if ref.get(cand, 0) >= min_ref:
            out.add((cand, ref[cand], "deletion"))
    # TOTAL order, not just by count. FIXED 2026-09-01: `out` is a SET and the
    # key was `-x[1]` alone, so forms with an equal ref_count came out in set
    # iteration order - which changes between processes, because Python
    # randomises string hashing per run. The report's CONTENT was stable (same
    # words, same counts) while its ORDER was not, so every rebuild rewrote the
    # file and `git status` showed a dirty tracked artifact that no data change
    # explained. Observed as pairs swapping places on consecutive runs with an
    # otherwise untouched corpus: שחוזר/החוזר (both 97), ופרה/מסרה (both 53).
    # Tie-break on the form, then the edit kind, so the file is reproducible.
    return sorted(out, key=lambda x: (-x[1], x[0], x[2]))


def build(min_ref=40, part_path=None):
    ref = df.reference_frequencies()
    if not ref:
        return None
    lexicon = [w.strip() for w in open(cio.LEXICON_PATH, encoding="utf-8") if w.strip()]
    klalim = cio.load_klalim(part_path) if part_path else cio.load_part1_sorted()
    counts = collections.Counter()
    positions = collections.defaultdict(list)
    for k in klalim:
        for i, w in enumerate((k.get("clean_text") or "").split()):
            n = cio.hebrew_letters_only(w)
            counts[n] += 1
            positions[n].append((k["klal_id"], i))

    rows = []
    for w in lexicon:
        n = cio.hebrew_letters_only(w)
        if ref.get(n, 0) != 0 or counts.get(n, 0) == 0:
            continue                       # attested elsewhere, or not in this part
        if cio.has_gershayim(w) or len(n) <= MIN_LETTERS - 1:
            continue                       # abbreviations and particles: different question
        nb = near_forms(n, ref, min_ref)
        rows.append({
            "word": w,
            "count": counts[n],
            "occurrences": positions[n][:12],
            "nearest_attested": [{"form": a, "ref_count": b, "edit": c} for a, b, c in nb[:5]],
        })
    # Same reason as near_forms() above - `r["word"]` is the final tie-break so
    # two rows with an equal count and an equal top-neighbour ref_count cannot
    # swap between runs.
    rows.sort(key=lambda r: (r["count"],
                             -(r["nearest_attested"][0]["ref_count"] if r["nearest_attested"] else 0),
                             r["word"]))
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--min-ref", type=int, default=40,
                    help="a near form must be attested at least this often (default 40)")
    ap.add_argument("--part", default=None, help="a part*.json to scan (default: part1.json)")
    args = ap.parse_args()
    rows = build(args.min_ref, args.part)
    if rows is None:
        print("sefaria_reference_corpus/word_freq.json is absent - nothing to compare against.")
        print("This is not 'no findings'. See SETUP.md; the cache is gitignored.")
        return
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
        f.flush()
    susp = [r for r in rows if r["nearest_attested"]]
    hapax = [r for r in susp if r["count"] == 1]
    print(f"Wrote {OUT_PATH}: {len(rows)} word(s) present here and in none of the "
          f"reference books")
    print(f"  {len(susp)} sit one edit from a form attested >= {args.min_ref}x "
          f"({len(hapax)} of those occur once here - the top-suspicion tier)")
    print(f"  {len(rows) - len(susp)} have no near neighbour - most likely this work's "
          f"own vocabulary")
    print("  NOT a purge list: absence from the reference corpus is not evidence of error.")


if __name__ == "__main__":
    main()
