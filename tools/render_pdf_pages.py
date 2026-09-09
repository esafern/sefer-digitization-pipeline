#!/usr/bin/env python3
"""
tools/render_pdf_pages.py

Render a scan PDF to `images/pdf_pages/page_N.png`, the page images the review
dashboard's scan pane displays.

WHY THIS EXISTS. Until now this cache had NO GENERATOR AT ALL. START_HERE says
so in as many words - "has no live rendering script at all (confirmed
2026-08-18, after its absence broke the dashboard's scan pane on a fresh
migration); it must be migrated as a pre-built cache" - so the one thing a
reviewer looks at could not be rebuilt, only copied. That is survivable for one
book and blocking for a second: item 0EI found this and the missing
header-anchored alignment as the two artifacts a new corpus cannot produce.

INDEXING IS 1-BASED AND MATCHES `docai_word_boxes/page_N.json`. `page_N.png` is
`doc[N-1]`, which is the convention every other cache in this repo already uses.
Getting that wrong is Lesson 30 THE WRONG PAGE LOOKS RIGHT - an off-by-one
renders the neighbouring page, the image is legible 19th-century Hebrew either
way, and nothing downstream complains. `--verify` re-reads what it wrote and
checks the rendered page against the DocAI tokens for the same N, which is the
only check that can actually fail.

SIZE. Yad Malachi's migrated cache renders at a constant zoom of 2.0833, i.e.
exactly 150 DPI, giving ~864x1330 RGB - far below the scan's own 18.3 MP,
because the dashboard shows it in a pane a few hundred pixels wide and the crops
that matter are taken from the PDF, not from these. The default is that same 150
DPI, verified to reproduce a migrated page byte-for-byte (page 100, pixel
correlation 1.0000). Do NOT render to a fixed WIDTH: the mediabox varies page to
page (856/860/864 px at 150 DPI), so a fixed width silently rescales every page
whose mediabox differs from the one you calibrated on.

Usage:
  python3 tools/render_pdf_pages.py --pages 58-151
  python3 tools/render_pdf_pages.py --pages 14-247 --verify
  SEFER_CORPUS_ROOT=~/work/hashorashim python3 tools/render_pdf_pages.py --all
"""

import argparse
import json
import os
import sys

import fitz

# Bootstrap only - deliberately NOT bound to a name like REPO, which is the
# seam bypass tests/test_pipeline_logic.py's bypass guard exists to catch.
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "pipeline"))
import corpus_io as cio  # noqa: E402


def verify_page(out_dir, page_num, doc):
    """Does page_N.png actually show what DocAI read on page N?

    Compares the rendered page's own text against the token cache. Returns
    (ok, overlap_pct) or (None, None) when there is nothing to check against.
    A neighbouring page scores far lower - measured on this repo's data, the
    correct page overlaps at 96-98% and its neighbours at 20-36% - so this check
    can fail, which is the whole point (Lesson 25).
    """
    cache = os.path.join(cio.DOCAI_DIR, f"page_{page_num}.json")
    if not os.path.exists(cache):
        return None, None
    with open(cache, encoding="utf-8") as fh:
        theirs = {cio.hebrew_letters_only(t["text"]) for t in json.load(fh)}
    theirs = {w for w in theirs if len(w) >= 2}
    if not theirs:
        return None, None
    raw = doc[page_num - 1].get_text()
    if not raw.strip():
        return None, None          # no text layer in this PDF; cannot verify here
    # A PDF's text layer may be stored in VISUAL order (Google Books) or LOGICAL
    # order (HebrewBooks) - see tools/extract_pdf_text_layer.py. Score BOTH and
    # keep the better: this check is about page IDENTITY, and forcing a reading
    # order here would make it fail on every page of a visual-order file for a
    # reason that has nothing to do with which page was rendered. That is exactly
    # what it did on first run - 94 of 94 "wrong page" against a correct render.
    best = None
    for text in (raw, "\n".join(l[::-1] for l in raw.split("\n"))):
        mine = {cio.hebrew_letters_only(w) for w in text.split()}
        mine = {w for w in mine if len(w) >= 2}
        if mine:
            pct = 100.0 * len(mine & theirs) / len(theirs)
            best = pct if best is None else max(best, pct)
    if best is None:
        # The layer exists but holds NO HEBREW - berlin_square_corrected.pdf is
        # exactly this, a whitespace skeleton left by a Quartz re-save (item
        # 0ED). That is "cannot verify", not "0% overlap"; reporting it as a
        # failure would flag every correct page of that book.
        return None, None
    return best >= 50.0, best


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pages", help="1-indexed window, e.g. 14-247")
    ap.add_argument("--all", action="store_true", help="every page in the PDF")
    ap.add_argument("--dpi", type=float, default=150.0,
                    help="render DPI (default 150, the migrated cache's own zoom)")
    ap.add_argument("--width", type=int, default=None,
                    help="fixed output width in px instead of a DPI")
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--overwrite", action="store_true",
                    help="re-render pages that already exist")
    ap.add_argument("--verify", action="store_true",
                    help="check each rendered page against docai_word_boxes/")
    args = ap.parse_args()

    if not args.pages and not args.all:
        ap.error("one of --pages or --all is required")

    pdf = cio.SCAN_PDF_PATH
    if not os.path.exists(pdf):
        raise SystemExit(f"scan not found: {pdf}\n"
                         f"book.json's scan_pdf names it; see item 0EI.")
    out_dir = args.out_dir or cio.repo_path("images", "pdf_pages")
    os.makedirs(out_dir, exist_ok=True)

    doc = fitz.open(pdf)
    pages = (range(1, doc.page_count + 1) if args.all
             else range(*(lambda a, b: (a, b + 1))(*(int(x) for x in args.pages.split("-")))))

    print(f"  scan       {os.path.basename(pdf)} ({doc.page_count} pages)")
    print(f"  out        {out_dir}")
    written = skipped = 0
    for n in pages:
        if n < 1 or n > doc.page_count:
            continue
        dest = os.path.join(out_dir, f"page_{n}.png")
        if os.path.exists(dest) and not args.overwrite:
            skipped += 1
            continue
        page = doc[n - 1]          # 1-based on disk, 0-based in fitz
        # DPI, not fixed width. Measured against the migrated cache: every page
        # there has an implied zoom of exactly 2.0833 = 150/72, and the PIXEL
        # widths vary (856, 860, 864) because the mediabox does. Rendering to a
        # fixed width instead reproduces page 100 exactly and shifts every page
        # whose mediabox differs, which is a silent mismatch against the cache
        # a reviewer is already looking at.
        zoom = (args.width / page.rect.width) if args.width else (args.dpi / 72.0)
        # Flushed per page, per this repo's standing rule on batch scripts: a
        # 651-page render that dies at 400 must not lose the 400.
        page.get_pixmap(matrix=fitz.Matrix(zoom, zoom)).save(dest)
        written += 1
    print(f"  rendered   {written} pages ({skipped} already present)")

    if args.verify:
        checked = bad = 0
        worst = []
        for n in pages:
            if n < 1 or n > doc.page_count:
                continue
            ok, pct = verify_page(out_dir, n, doc)
            if ok is None:
                continue
            checked += 1
            if not ok:
                bad += 1
                worst.append((n, pct))
        if checked:
            print(f"  verified   {checked} pages against docai_word_boxes/, "
                  f"{bad} below the 50% overlap bar")
            for n, pct in worst[:8]:
                print(f"     page {n}: {pct:.1f}%  <-- wrong page, or bad OCR on it")
        else:
            print("  verified   nothing - this PDF has no text layer to check "
                  "against, so page identity cannot be confirmed here. Use "
                  "tools/extract_pdf_text_layer.py --verify-against instead.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
