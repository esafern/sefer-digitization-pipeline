#!/usr/bin/env python3
"""
tools/measure_against_reviewed.py

Score any number of text sources against Sefaria's manually reviewed entries,
on exactly the same entries and the same ground truth.

WHY A TOOL. The same comparison has now been re-run five times from scratch
scripts, and two of those runs carried silent defects that changed conclusions:

  * HOMOGRAPHS MERGED. Entries were keyed by folded root, so `אלה a` and
    `אלה b` - two real entries spelling one root - were concatenated into one,
    and the reviewed `אלה b` was scored against 991 words of text that belonged
    to its sibling. Sources are now kept as ORDERED lists per root and paired
    with the reviewed entries occurrence by occurrence.
  * DIFFERENT DENOMINATORS. A source missing an entry quietly shrank its own
    comparison set. Every source is now scored on the intersection only, and
    the intersection size is printed.

It also reports COVERAGE and PRECISION separately, not only the combined
similarity. That split is what exposed item 0FZ: every source reproduced 95-98%
of the reviewed text, and the differences between them were almost entirely
EXTRA text - running heads and apparatus - rather than misreadings. A single
similarity number hides which of the two you are looking at.

Sources are either a directory of page_N.txt files (segmented here with the
book's own heading detector) or a corpus JSON (a part1.json).

Usage:
  SEFER_CORPUS_ROOT=~/work/hashorashim python3 tools/measure_against_reviewed.py \\
      --gold ~/work/hashorashim/gold100_text.json \\
      --source "corpus=~/work/hashorashim/part1.json" \\
      --source "cv_full=~/work/hashorashim/nli_cv_layer"
"""

import argparse
import difflib
import glob
import json
import os
import re
import sys
import unicodedata

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "pipeline"))
sys.path.insert(0, _HERE)
import corpus_io as cio  # noqa: E402
from detect_root_entries import match_heading  # noqa: E402

FINALS = str.maketrans("ךםןףץ", "כמנפצ")
DIGITS = re.compile(r"\d+")
HOMOGRAPH_SUFFIX = re.compile(r"\s+[a-z]$")


def fold(x):
    return cio.HEBREW_PUNCT.sub("", cio.strip_points(
        unicodedata.normalize("NFKC", x))).translate(FINALS)


def words(t):
    return cio.hebrew_words(unicodedata.normalize("NFKC", t))


def from_layer(layer):
    """{root: [entry text, ...]} IN ORDER - homographs stay separate."""
    pages = sorted(int(re.search(r"page_(\d+)\.txt$", f).group(1))
                   for f in glob.glob(os.path.join(layer, "page_*.txt")))
    out, cur, buf = [], None, []
    for pg in pages:
        with open(os.path.join(layer, f"page_{pg}.txt"), encoding="utf-8") as fh:
            lines = [l for l in fh.read().split("\n") if l.strip()]
        if lines:
            lines = lines[1:]                       # running head
        while lines and len(DIGITS.findall(lines[-1])) >= 3:
            lines.pop()                             # trailing apparatus, crudely
        for line in lines:
            m = match_heading(line)
            if m:
                if cur:
                    out.append((cur, " ".join(buf)))
                cur, buf = m[0], [line[m[1]:]]
            elif cur:
                buf.append(line)
    if cur:
        out.append((cur, " ".join(buf)))
    by = {}
    for root, text in out:
        by.setdefault(fold(root), []).append(text)
    return by, len(pages)


def from_corpus(path):
    with open(path, encoding="utf-8") as fh:
        rows = json.load(fh)
    by = {}
    for r in rows:
        by.setdefault(fold(r["gematria"]), []).append(r["clean_text"])
    return by


def pair(gold, source):
    """(gold words, source words) per reviewed entry, matched occurrence by
    occurrence so `X a` meets the first X and `X b` the second."""
    seen, out = {}, {}
    for head, text in gold.items():
        k = fold(HOMOGRAPH_SUFFIX.sub("", head))
        i = seen.get(k, 0)
        seen[k] = i + 1
        lst = source.get(k, [])
        if i < len(lst):
            out[head] = lst[i]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gold", required=True)
    ap.add_argument("--source", action="append", required=True,
                    help="name=path, where path is a page_N.txt directory or a corpus json")
    args = ap.parse_args()

    with open(os.path.expanduser(args.gold), encoding="utf-8") as fh:
        gold = json.load(fh)
    paired = {}
    for spec in args.source:
        name, path = spec.split("=", 1)
        path = os.path.expanduser(path)
        if os.path.isdir(path):
            src, n = from_layer(path)
            note = f"{n} pages"
        else:
            src, note = from_corpus(path), "corpus"
        paired[name] = pair(gold, src)
        print(f"  {name:<24} {note:<10} {len(paired[name])} reviewed entries matched")
    common = set(gold)
    for p in paired.values():
        common &= set(p)
    n_words = sum(len(words(gold[h])) for h in common)
    print(f"\n  scored on the {len(common)} entries present in EVERY source "
          f"({n_words:,} reviewed words)\n")
    print(f"  {'source':<24}{'words':>8}{'chars':>8}{'cover':>8}{'prec':>8}{'len/gold':>9}{'nun/gimel':>10}")
    for name, p in paired.items():
        tw = ws = cs = 0.0
        M = LS = LG = 0
        ng = 0
        for h in common:
            G, S = words(gold[h]), words(p[h])
            g, s = "".join(G), "".join(S)
            smw = difflib.SequenceMatcher(None, S, G, autojunk=False)
            smc = difflib.SequenceMatcher(None, s, g, autojunk=False)
            mw = sum(b.size for b in smw.get_matching_blocks())
            mc = sum(b.size for b in smc.get_matching_blocks())
            tw += len(G)
            ws += len(G) * (2 * mw / (len(S) + len(G)) if (S or G) else 0)
            cs += len(G) * (2 * mc / (len(s) + len(g)) if (s or g) else 0)
            M += mc; LS += len(s); LG += len(g)
            for tag, i1, i2, j1, j2 in smw.get_opcodes():
                if tag == "replace" and i2 - i1 == 1 and j2 - j1 == 1:
                    a, b = S[i1], G[j1]
                    if len(a) == len(b):
                        d = [(x, y) for x, y in zip(a, b) if x != y]
                        if len(d) == 1 and set(d[0]) == {"נ", "ג"}:
                            ng += 1
        print(f"  {name:<24}{ws/tw:>8.4f}{cs/tw:>8.4f}{M/LG:>8.4f}{M/LS:>8.4f}"
              f"{LS/LG:>9.3f}{ng:>10d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
