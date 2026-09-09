#!/usr/bin/env python3
"""
tools/extract_pdf_text_layer.py

Recover the OCR text layer embedded in a scanned PDF, one file per page.

WHY THIS EXISTS (item 0ED, 2026-09-09). A Google Books PDF ships with Google's
own OCR inside it. For Yad Malachi that is ~1,005,824 Hebrew characters over 332
of 337 pages, free, no API and no key - and this project never read it. Nothing
in `pipeline/`, `tools/` or `tests/` called `get_text(` even once.

Worse, the copies the pipeline actually uses cannot supply it. Both
`berlin_square_corrected.pdf` and `berlin_square_original_transposed.pdf` were
re-saved through macOS Quartz, which kept the layer's WHITESPACE SKELETON and
discarded every Hebrew character. They still report 334 of 337 pages as "having
text", so a naive `page.get_text().strip()` check says the layer is present when
it holds nothing but spaces. **Check for Hebrew characters, not for text** -
`--report` does exactly that, and refuses to pretend a whitespace layer is a
layer.

WHAT THE RECOVERED LAYER IS WORTH, AND WHAT IT IS NOT. Measured against
`part1.json` over klalim 13-23: 97.2% word accuracy, second only to DocAI's
98.6% and far above Dicta-on-square's 78.1%. But its error profile is DocAI's,
near identically - `ה->ח x6`, `∅->י x4`, `∅->יי x4`, `כ->ב x3` against DocAI's
`ה->ח x6`, `∅->יי x4`, `∅->י x4`, `ב->כ x3`. Two Google OCR systems reading one
sheet of ink fail the same way: Lesson 24 SHARED INK, SHARED ERROR compounded by
Lesson 23 AN ENGINE, NOT A SAMPLE.

So this layer is a RELIABILITY GATE on DocAI, never a third vote. Counted as a
vote it manufactures false 2-of-3 agreement on precisely the glyphs DocAI
already gets wrong.

TWO TRAPS THIS TOOL HANDLES, both found by measurement:

1. **Reading order is per-file and the two conventions look equally plausible.**
   Google Books stores Hebrew in VISUAL order - `get_text()` returns each line
   reversed, characters AND word order together - while HebrewBooks stores it in
   LOGICAL order. Reversing a logical-order file (or failing to reverse a visual
   one) yields fluent-looking Hebrew in the wrong order, which nothing
   downstream will flag. `--order detect` scores both readings against a lexicon
   and says which it picked; do not guess.

2. **Page order can differ from the pipeline's.** Yad Malachi's source binding
   has two transposed leaves, fixed in `berlin_square_corrected.pdf` by moving
   0-indexed page 37 to position 36 - so text pulled from a PRE-fix PDF (which
   the original Google download is) is off by that swap around pages 37/38.
   `--swap A:B` applies it in 1-indexed page numbers, matching how
   `docai_word_boxes/page_N.json` is named.

Usage:
  # what is actually in there?
  python3 tools/extract_pdf_text_layer.py --pdf book.pdf --report

  # recover Yad Malachi's layer into the pipeline's own page numbering
  python3 tools/extract_pdf_text_layer.py \
      --pdf ~/Downloads/ספר_יד_מלאכי\\ Berlin.pdf \
      --out-dir google_books_layer --swap 37:38

  # confirm the page numbering against an independently-indexed cache
  python3 tools/extract_pdf_text_layer.py --pdf ... --out-dir ... \
      --verify-against docai_word_boxes
"""

import argparse
import json
import os
import re
import sys

import fitz

# Bootstrap only - deliberately NOT bound to a name like REPO, which is the
# seam bypass tests/test_pipeline_logic.py's bypass guard exists to catch. Every
# real path below goes through corpus_io, which resolves $SEFER_CORPUS_ROOT at
# call time.
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "pipeline"))
import corpus_io as cio  # noqa: E402

HEBREW = re.compile(r"[֐-׿]")


def page_lines(page):
    return [l for l in page.get_text().split("\n") if l.strip()]


def hebrew_chars(text):
    return len(HEBREW.findall(text))


def load_lexicon():
    path = cio.repo_path("lexicon.txt")
    if not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8") as fh:
        return {l.strip() for l in fh if l.strip()}


def detect_order(doc, lexicon, sample=12):
    """Is this layer stored in VISUAL order (needs whole-line reversal) or LOGICAL?

    Scores both readings against the lexicon. Returns (order, as_is, reversed_).
    A layer with no Hebrew returns ("none", 0, 0) rather than a coin flip -
    silence must not be answered with a confident guess (Lesson 26).
    """
    pages = [i for i in range(doc.page_count) if hebrew_chars(doc[i].get_text())]
    if not pages or not lexicon:
        return "none", 0.0, 0.0
    step = max(1, len(pages) // sample)
    hits = {"as_is": 0, "rev": 0}
    total = 0
    for i in pages[::step][:sample]:
        for line in page_lines(doc[i]):
            for variant, text in (("as_is", line), ("rev", line[::-1])):
                for w in text.split():
                    w = cio.hebrew_letters_only(w)
                    if len(w) >= 2 and w in lexicon:
                        hits[variant] += 1
            total += len([w for w in line.split() if len(w) >= 2])
    a = hits["as_is"] / max(total, 1)
    r = hits["rev"] / max(total, 1)
    return ("visual" if r > a else "logical"), a, r


def build_swap(specs, page_count):
    """1-indexed swap pairs -> a mapping output_page -> source_page (0-indexed)."""
    mapping = {i: i for i in range(page_count)}
    for spec in specs:
        a, b = (int(x) for x in spec.split(":"))
        ai, bi = a - 1, b - 1
        mapping[ai], mapping[bi] = mapping[bi], mapping[ai]
    return mapping


def verify_against(out_dir, cache_dir, pages_to_check):
    """Token overlap between each extracted page and an independently-indexed cache.

    This is the Lesson 30 check (THE WRONG PAGE LOOKS RIGHT): a page-order error
    produces legible Hebrew from the neighbouring page and nothing says so. The
    only thing that catches it is content.
    """
    rows = []
    for n in pages_to_check:
        tp = os.path.join(out_dir, f"page_{n}.txt")
        cp = os.path.join(cache_dir, f"page_{n}.json")
        if not (os.path.exists(tp) and os.path.exists(cp)):
            continue
        with open(tp, encoding="utf-8") as fh:
            mine = {cio.hebrew_letters_only(w) for w in fh.read().split()}
        with open(cp, encoding="utf-8") as fh:
            theirs = {cio.hebrew_letters_only(t["text"]) for t in json.load(fh)}
        mine = {w for w in mine if len(w) >= 2}
        theirs = {w for w in theirs if len(w) >= 2}
        if not theirs:
            continue
        rows.append((n, 100.0 * len(mine & theirs) / len(theirs), len(theirs)))
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--out-dir", help="write page_N.txt here (1-indexed, post-swap)")
    ap.add_argument("--order", choices=("detect", "visual", "logical"), default="detect",
                    help="visual = reverse each line; detect = measure and say")
    ap.add_argument("--swap", action="append", default=[], metavar="A:B",
                    help="swap 1-indexed pages A and B, e.g. 37:38 for the transposed leaf")
    ap.add_argument("--report", action="store_true",
                    help="say what the layer holds and exit, writing nothing")
    ap.add_argument("--verify-against", metavar="DIR",
                    help="cross-check page numbering against docai_word_boxes/")
    args = ap.parse_args()

    doc = fitz.open(os.path.expanduser(args.pdf))
    heb_pages = sum(1 for i in range(doc.page_count) if hebrew_chars(doc[i].get_text()))
    heb_total = sum(hebrew_chars(doc[i].get_text()) for i in range(doc.page_count))
    nonblank = sum(1 for i in range(doc.page_count) if doc[i].get_text().strip())
    producer = (doc.metadata or {}).get("producer", "")

    print(f"{os.path.basename(args.pdf)}")
    print(f"  producer            {producer}")
    print(f"  pages               {doc.page_count}")
    print(f"  non-blank text      {nonblank}   <- what a naive check counts")
    print(f"  pages WITH HEBREW   {heb_pages}")
    print(f"  Hebrew characters   {heb_total:,}")
    if heb_total == 0:
        print("\n  NO HEBREW TEXT LAYER. If non-blank text is high, this PDF has a")
        print("  whitespace skeleton only - typically a re-save that dropped the")
        print("  characters. Go back to the original download (item 0ED).")
        return 1

    lexicon = load_lexicon()
    order, as_is, rev = args.order, None, None
    if args.order == "detect":
        order, as_is, rev = detect_order(doc, lexicon)
        print(f"  reading order       {order.upper()}  "
              f"(lexicon hit as-is {as_is:.1%} vs reversed {rev:.1%})")
    if args.report:
        return 0
    if not args.out_dir:
        ap.error("--out-dir is required unless --report")

    out_dir = os.path.abspath(os.path.expanduser(args.out_dir))
    os.makedirs(out_dir, exist_ok=True)
    mapping = build_swap(args.swap, doc.page_count)
    if args.swap:
        print(f"  page swaps applied  {', '.join(args.swap)} (1-indexed)")

    written = 0
    for out_idx in range(doc.page_count):
        src = mapping[out_idx]
        lines = page_lines(doc[src])
        if order == "visual":
            lines = [l[::-1] for l in lines]
        path = os.path.join(out_dir, f"page_{out_idx + 1}.txt")
        # Flushed per page, per this repo's standing rule on batch scripts.
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))
            fh.flush()
            os.fsync(fh.fileno())
        written += 1
    print(f"  wrote               {written} files -> {out_dir}")

    if args.verify_against:
        checks = sorted({1, 20, 36, 37, 38, 39, 100, 200, doc.page_count - 1})
        rows = verify_against(out_dir, os.path.expanduser(args.verify_against),
                              [c for c in checks if 1 <= c <= doc.page_count])
        if rows:
            print(f"\n  page-numbering check vs {args.verify_against} "
                  f"(token overlap; the transposed leaf is 37/38)")
            for n, pct, ntok in rows:
                mark = "  <-- LOW" if pct < 50 else ""
                print(f"    page {n:>3}   {pct:5.1f}%  of {ntok} cache tokens{mark}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
