#!/usr/bin/env python3
"""
tools/verify_nli_page_offset.py

Prove, page by page, that NLI image index = PDF page + OFFSET across the whole
book BEFORE any paid OCR run pairs them. Items `0FZ`/`0GA`: the -40 offset was
content-verified over pages 58-92 only, NLI has 656 images to the PDF's 651
pages, and a drifting offset silently pairs text with the wrong page - the
failure `0FU` caught by hand.

TWO SIGNALS, per Lesson 9 (TWO SIGNALS OR NONE):

  text  Tesseract (heb, local, free) on the NLI image, compared by Hebrew
        letter-trigram Jaccard against the Google Books text layer of PDF pages
        p-W .. p+W. It passes when p scores best AND beats the runner-up by
        --margin. The neighbours are the built-in negative control (Lesson 25,
        A SIGNAL THAT CANNOT DISAGREE): prototyped 2026-09-13 on pages 58, 75,
        92, 400 and 640, the right page scored 0.72-0.85 and every neighbour
        0.04-0.21.
  ink   `experiment_scan_source.find_nli_page`'s vertical-ink-profile search,
        which must land on the same NLI index independently. Correlation alone
        is NOT evidence - facing pages of solid text correlate well (`0FU`) -
        which is why it is the second signal and not the first.

A page with no usable text layer (a plate, a blank) is INCONCLUSIVE, never PASS.
The Google Books layer is DocAI's twin (`0ED`), but here it is only used to
identify WHICH page an image shows, which its errors cannot change.

Output: one JSON line per page, flushed as written; a rerun resumes.

Usage:
  SEFER_CORPUS_ROOT=~/work/hashorashim python3 tools/verify_nli_page_offset.py \\
      --out ~/work/hashorashim/nli_page_offset_check.jsonl
  ... --summary-only        # re-print the summary from an existing --out
"""

import argparse
import glob
import json
import os
import re
import subprocess
import sys
import tempfile

from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "pipeline"))
sys.path.insert(0, _HERE)
import fitz  # noqa: E402
import corpus_io as cio  # noqa: E402
from experiment_scan_source import find_nli_page  # noqa: E402

HEB = re.compile(r"[א-ת]")
MIN_TEXT_SCORE = 0.30   # below this the right page is not recognisably itself
INK_WINDOW = 6          # the ink search looks this far either side of --offset


def trigrams(text):
    s = "".join(HEB.findall(text))
    return {s[i:i + 3] for i in range(len(s) - 2)}


def jaccard(a, b):
    return len(a & b) / len(a | b) if a and b else 0.0


def tesseract_heb(path):
    im = Image.open(path)
    im.thumbnail((1600, 2400))
    with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
        im.convert("L").save(tmp.name)
        return subprocess.run(["tesseract", tmp.name, "stdout", "-l", "heb"],
                              capture_output=True, text=True, check=True).stdout


def classify(rec, margin):
    """PASS / TEXT_ONLY / FAIL / INCONCLUSIVE from a record's stored scores.

    A DRIFT IS TESTED FIRST (code review 2026-09-13, finding 1). When the image
    shows a neighbouring page, the RIGHT page scores low - so the old order,
    which asked "is the right page below the bar?" first, filed exactly the
    failure this tool exists to catch as INCONCLUSIVE and exited 0. p48 was
    that: INCONCLUSIVE while p49's text scored 0.594 against its image.
    summarize() re-judges every stored record with this rule, so a record
    written by an older rule cannot hide behind the status it was given.
    """
    if "text_scores" not in rec:
        return rec.get("status", "NO_IMAGE")
    scores = {int(q): v for q, v in rec["text_scores"].items()}
    page = rec["page"]
    best = max(scores, key=scores.get)
    own = scores.get(page, 0.0)
    runner_up = max((v for q, v in scores.items() if q != page), default=0.0)
    if best != page and scores[best] >= MIN_TEXT_SCORE:
        return "FAIL"            # the image reads as ANOTHER page: a drift
    if own < MIN_TEXT_SCORE:
        return "INCONCLUSIVE"    # no page in the window reads clearly: plate, blank
    text_ok = own - runner_up >= margin
    ink_ok = rec.get("ink_index") == rec.get("nli_index")
    if text_ok and ink_ok:
        return "PASS"
    if text_ok:
        return "TEXT_ONLY"       # content agrees; the ink search does not
    return "FAIL"


def independent_scan():
    """The scan the photographs are checked AGAINST - never the assembled
    full-tone PDF, whose substituted pages ARE those photographs, so the ink
    search would compare each one with itself (code review 2026-09-13,
    finding 7). build_nli_page_pdf.py records its base PDF; use that."""
    src = cio.repo_path("page_image_sources.json")
    if os.path.exists(src):
        with open(src, encoding="utf-8") as fh:
            return cio.repo_path(json.load(fh)["base_pdf"])
    return cio.SCAN_PDF_PATH


def check_page(page, idx, nli_files, doc, layer_dir, n_pages, window, margin):
    rec = {"page": page, "nli_index": idx}
    if not 0 <= idx < len(nli_files):
        rec["status"] = "NO_IMAGE"
        return rec
    rec["nli_file"] = os.path.basename(nli_files[idx])

    def layer(q):
        f = os.path.join(layer_dir, f"page_{q}.txt")
        if not os.path.exists(f):
            return set()
        with open(f, encoding="utf-8") as fh:
            return trigrams(fh.read())

    g = trigrams(tesseract_heb(nli_files[idx]))
    scores = {q: round(jaccard(g, layer(q)), 3)
              for q in range(max(1, page - window), min(n_pages, page + window) + 1)}
    ranked = sorted(scores, key=scores.get, reverse=True)
    best = ranked[0]
    runner_up = scores[ranked[1]] if len(ranked) > 1 else 0.0
    rec.update(text_scores=scores, text_best=best,
               text_margin=round(scores[page] - runner_up, 3))

    pix = doc.load_page(page - 1).get_pixmap(dpi=110)
    gb = Image.frombytes("RGB" if pix.n >= 3 else "L",
                         (pix.width, pix.height), pix.samples)
    # Searched AROUND the offset under test: find_nli_page's default window is
    # -45..-33, so any other --offset could never agree (finding 7).
    off = idx - page
    path, corr = find_nli_page(gb, nli_files, page, lo=off - INK_WINDOW, hi=off + INK_WINDOW)
    ink_idx = nli_files.index(path) if path else None
    rec.update(ink_index=ink_idx, ink_corr=round(float(corr), 3))
    rec["status"] = classify(rec, margin)
    return rec


def summarize(out, margin):
    rows = {}
    with open(out, encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            r["status"] = classify(r, margin)
            rows[r["page"]] = r
    by = {}
    for r in rows.values():
        by.setdefault(r["status"], []).append(r["page"])
    print(f"\n  {len(rows)} pages checked")
    for status in ("PASS", "TEXT_ONLY", "INCONCLUSIVE", "FAIL", "NO_IMAGE"):
        pages = sorted(by.get(status, []))
        print(f"  {status:13} {len(pages):4}")
        if status != "PASS" and pages:
            print(f"      {pages if len(pages) <= 60 else pages[:60] + ['...']}")
    return 1 if by.get("FAIL") else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--pages", help="PDF page range, default every page")
    ap.add_argument("--offset", type=int, default=-40)
    ap.add_argument("--nli-glob", default="~/work/hashorashim/dedupmrg*/*.jpg")
    ap.add_argument("--window", type=int, default=3)
    ap.add_argument("--margin", type=float, default=0.20)
    ap.add_argument("--summary-only", action="store_true")
    ap.add_argument("--base-pdf", default=None,
                    help="the scan to check against; default: the base PDF "
                         "page_image_sources.json records, else book.json's scan_pdf")
    args = ap.parse_args()
    out = os.path.expanduser(args.out)
    if args.summary_only:
        return summarize(out, args.margin)

    nli_files = sorted(glob.glob(os.path.expanduser(args.nli_glob)))
    base_pdf = os.path.expanduser(args.base_pdf) if args.base_pdf else independent_scan()
    doc = fitz.open(base_pdf)
    layer_dir = cio.repo_path("google_books_layer")
    lo, hi = (int(x) for x in args.pages.split("-")) if args.pages else (1, len(doc))
    done = set()
    if os.path.exists(out):
        with open(out, encoding="utf-8") as fh:
            done = {json.loads(line)["page"] for line in fh}
    print(f"  {len(nli_files)} NLI images, {len(doc)} pages of {os.path.basename(base_pdf)}, "
          f"offset {args.offset}")

    with open(out, "a", encoding="utf-8") as fh:
        for page in range(lo, hi + 1):
            if page in done:
                continue
            rec = check_page(page, page + args.offset, nli_files, doc, layer_dir,
                             len(doc), args.window, args.margin)
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            if rec["status"] != "PASS":
                print(f"  p{page}: {rec['status']} {rec.get('text_best')} "
                      f"margin {rec.get('text_margin')} ink {rec.get('ink_index')}")
    return summarize(out, args.margin)


if __name__ == "__main__":
    sys.exit(main())
