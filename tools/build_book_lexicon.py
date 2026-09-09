#!/usr/bin/env python3
"""
tools/build_book_lexicon.py

Build `lexicon.txt` for the CURRENT corpus root from the Sefaria reference
corpus, choosing the register that matches the book.

WHY A BOOK NEEDS ITS OWN. `lexicon.txt` is used as a validity signal all over
this pipeline - lexicon hit rate is one of the three independent measures in
`tools/compare_ocr_engines.py`, it gates the lexical detectors, and it is what
`tools/extract_pdf_text_layer.py --order detect` scores reading order against.
The one in the Yad Malachi repo is Rabbinic Hebrew and Aramaic: Talmud, Rambam,
Tur, Shulchan Arukh, Rashi on the Talmud. That is the register Yad Malachi is
written in and about.

**Sefer HaShorashim is a dictionary OF THE BIBLE and the reference corpus
contained zero of the 39 biblical books** (checked 2026-09-10, not assumed).
Every engine measured on it therefore scored 60-67% where the same engines score
97-99% on Yad Malachi - the instrument was reading the wrong language. Because
it was wrong for every engine equally the COMPARISON between engines survived,
but no absolute number from those runs means anything, and nothing built on a
lexicon threshold could be trusted at all.

WHY TANAKH ALONE IS NOT THE ANSWER EITHER. This book is three registers at once:
Ibn Janah's argument in Ibn Tibbon's twelfth-century Hebrew, biblical quotations
in biblical Hebrew, and Arabic technical vocabulary in Hebrew characters. Tanakh
covers the quotations; the rabbinic/medieval corpus covers the prose, since
Rambam and Tur are themselves medieval Hebrew. `--register all` is the default
here for that reason. A lexicon that covers only the quotations would mark the
author's own words as errors, which is the failure mode Lesson 26 calls THE
FILTER THAT HIDES pointed the other way.

INDEPENDENCE IS THE POINT AND IT IS FRAGILE. This lexicon must not be derived
from this project's own OCR of the scan, or it will contain the very corruptions
it is supposed to detect - see PROJECT-STATUS.md, "`lexicon.txt` cannot catch the
ligature corruption - it contains it". Everything here comes from Sefaria's
published texts and nothing from any `part*.json`.

Usage:
  SEFER_CORPUS_ROOT=~/work/hashorashim python3 tools/build_book_lexicon.py
  python3 tools/build_book_lexicon.py --register tanakh --min-count 2 --dry-run
"""

import argparse
import collections
import json
import os
import sys

# Bootstrap only - deliberately NOT bound to a name like REPO, which is the
# seam bypass tests/test_pipeline_logic.py's bypass guard exists to catch.
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "pipeline"))
sys.path.insert(0, _HERE)
import corpus_io as cio  # noqa: E402
# Reused, not reimplemented: that module owns extraction and already handles the
# dict-shaped `text` nodes and the HTML the export carries (Lesson 13).
from validate_lexicon_independent import flatten_strings, clean_words  # noqa: E402
from fetch_sefaria_reference_corpus import REGISTERS  # noqa: E402

RAW_DIR_NAME = os.path.join("sefaria_reference_corpus", "raw")


def raw_dir():
    """The reference corpus is SHARED between books, so it lives beside the
    code rather than in a corpus root - unlike lexicon.txt, which is per-book."""
    return os.path.join(os.path.dirname(_HERE), RAW_DIR_NAME)


def titles_for(register):
    want = REGISTERS[register]
    present, missing = {}, []
    for title in sorted(want):
        safe = title.replace("/", "_").replace(",", "").replace("'", "")
        path = os.path.join(raw_dir(), f"{safe}.json")
        if os.path.exists(path):
            present[title] = path
        else:
            missing.append(title)
    return present, missing


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--register", choices=sorted(REGISTERS), default="all")
    ap.add_argument("--min-count", type=int, default=1,
                    help="drop word types rarer than this in the reference corpus")
    ap.add_argument("--out", default=None, help="default: the corpus root's lexicon.txt")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    present, missing = titles_for(args.register)
    print(f"  register     {args.register}")
    print(f"  source books {len(present)} present, {len(missing)} missing")
    if missing:
        print(f"    missing: {', '.join(missing[:8])}"
              f"{' ...' if len(missing) > 8 else ''}")
        print(f"    fetch them with: python3 tools/fetch_sefaria_reference_corpus.py "
              f"--register {args.register}")
    if not present:
        raise SystemExit("nothing to build from")

    freq = collections.Counter()
    per_book = {}
    for title, path in present.items():
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        strings = []
        flatten_strings(data.get("text", data), strings)
        before = len(freq)
        n = 0
        for s in strings:
            for w in clean_words(s):
                freq[w] += 1
                n += 1
        per_book[title] = n
        # A book that contributes ZERO words is the failure this repo has already
        # had once (Shulchan Arukh, Even HaEzer sat downloaded and uncounted).
        if n == 0:
            print(f"    WARNING {title}: downloaded but contributed 0 words")
        del before

    words = sorted(w for w, c in freq.items() if c >= args.min_count)
    print(f"  tokens       {sum(freq.values()):,}")
    print(f"  word types   {len(freq):,}  ({len(words):,} at count >= {args.min_count})")

    out = args.out or cio.LEXICON_PATH
    if args.dry_run:
        print(f"  would write  {out}")
        return 0
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(words) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    print(f"  wrote        {out}")
    meta = os.path.join(os.path.dirname(out), "lexicon.meta.json")
    with open(meta, "w", encoding="utf-8") as fh:
        json.dump({"register": args.register, "min_count": args.min_count,
                   "books": len(present), "types": len(words),
                   "tokens": sum(freq.values()),
                   "note": "Built from Sefaria's published texts only. Nothing here "
                           "is derived from this project's OCR of the scan - a "
                           "lexicon built from the corpus contains the corruptions "
                           "it is meant to detect."},
                  fh, ensure_ascii=False, indent=1)
    print(f"  wrote        {meta}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
