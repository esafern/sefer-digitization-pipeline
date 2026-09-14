#!/usr/bin/env python3
"""
tools/ocr_pages_vlm.py

Transcribe scan pages with a vision model, from whichever scan you point it at.

WHY THIS EXISTS NOW. Item `0FS` measured that on the nun/gimel class - a third
of this book's single-letter errors - the bitonal Google Books scan scores 18%
and NLI's full-tone scan scores 90%, at half the linear resolution. Every
artifact in this corpus root was built from the bitonal scan. This tool is what
lets the same pages be read from the full-tone one so the two can be compared on
running text rather than on a hand-picked error class.

NO BINARIZATION, DELIBERATELY. `0FS` also measured that thresholding the
full-tone crop ourselves costs 30 points (90% -> 61%), breaking 15 correct
readings for every 1 it fixes. The page is sent as scanned. The only image
operation is cropping away the scan border, which removes the dark gutter and
the surrounding table, not any ink.

PAGE ALIGNMENT IS EARNED, NOT ASSUMED. NLI's images are the full leaf with
margins and their own file numbering; facing pages of solid text look alike. The
offset is found per page by correlating vertical ink profiles across a window,
and a page whose best match does not clear `--min-corr` is SKIPPED and reported
rather than transcribed, because a mis-paired page produces plausible text for
the wrong page - the worst possible failure here.

Usage:
  GEMINI_API_KEY=... SEFER_CORPUS_ROOT=~/work/hashorashim \
    python3 tools/ocr_pages_vlm.py --pages 58-92 --source nli \
      --out-dir ~/work/hashorashim/nli_vlm_layer
"""

import argparse
import glob
import hashlib
import io
import json
import os
import sys

import numpy as np
from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "pipeline"))
sys.path.insert(0, _HERE)
import fitz  # noqa: E402
import corpus_io as cio  # noqa: E402
import vision_adjudication_common as vac  # noqa: E402
from experiment_scan_source import nli_text_crop, find_nli_page  # noqa: E402

PROMPT = (
    "You are a literal OCR reader for 19th-century Hebrew typography. This is a "
    "page from Sefer HaShorashim (Ibn Janah, ed. Bacher, Berlin 1896), set in "
    "square Hebrew type.\n\n"
    "Transcribe every Hebrew line you can see, verbatim, in reading order, one "
    "line per output line. Include the running head and any footnote block at the "
    "foot of the page. Transcribe what the ink shows; do not correct, complete or "
    "normalise the text, and do not add anything that is not on the page.\n\n"
    "Output only the raw Hebrew text."
)
TABLE = "vlm_page_ocr"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pages", required=True, help="PDF page range, e.g. 58-92")
    ap.add_argument("--source", choices=("nli", "pdf"), default="nli")
    ap.add_argument("--nli-glob", default="~/work/hashorashim/dedupmrg*/*.jpg")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--min-corr", type=float, default=0.80)
    ap.add_argument("--offset", type=int, default=None,
                    help="force NLI index = page + offset instead of searching. "
                         "Once the offset is established over several pages it is "
                         "STRONGER than a per-page profile correlation: facing "
                         "pages of solid text correlate well with each other, so "
                         "the search can pick a neighbour and the correlation "
                         "will look respectable while the text is a page off.")
    ap.add_argument("--dpi", type=int, default=400, help="pdf source only")
    args = ap.parse_args()

    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise SystemExit("GEMINI_API_KEY is not set")
    lo, hi = (int(x) for x in args.pages.split("-"))
    out_dir = os.path.expanduser(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)
    nli_files = sorted(glob.glob(os.path.expanduser(args.nli_glob)))
    doc = fitz.open(cio.SCAN_PDF_PATH)
    client = vac.make_client(key)
    prompt_hash = hashlib.sha256(PROMPT.encode("utf-8")).hexdigest()[:16]
    db = os.path.join(os.path.dirname(cio.LEXICON_PATH), "adjudication_cache.db")
    vac.init_cache_table(db, TABLE, prompt_hash)

    written, skipped = 0, []
    for page in range(lo, hi + 1):
        if args.source == "pdf":
            pix = doc.load_page(page - 1).get_pixmap(dpi=args.dpi)
            im = Image.frombytes("RGB" if pix.n >= 3 else "L",
                                 (pix.width, pix.height), pix.samples)
            label = f"pdf p{page}"
        else:
            pix = doc.load_page(page - 1).get_pixmap(dpi=110)
            gb = Image.frombytes("RGB" if pix.n >= 3 else "L",
                                 (pix.width, pix.height), pix.samples)
            if args.offset is not None:
                idx = page + args.offset
                path = nli_files[idx] if 0 <= idx < len(nli_files) else None
                corr = 1.0
            else:
                path, corr = find_nli_page(gb, nli_files, page)
            if path is None or corr < args.min_corr:
                skipped.append((page, round(corr, 3)))
                print(f"  p{page}: SKIPPED, best page match {corr:.2f}")
                continue
            im = nli_text_crop(Image.open(path))
            label = f"nli {os.path.basename(path)} (corr {corr:.2f})"

        buf = io.BytesIO()
        im.convert("RGB").save(buf, format="PNG")
        png = buf.getvalue()
        ctx = f"{args.source}:p{page}"
        get = lambda: vac.get_cached_decision(db, TABLE, prompt_hash, png, "", "", ctx)
        put = lambda t, m: vac.put_cached_decision(db, TABLE, prompt_hash, png,
                                                   "", "", ctx, t, m)
        print(f"  p{page}: {label}  {im.size[0]}x{im.size[1]}")
        try:
            text = vac.adjudicate_with_retry(client, png, PROMPT, get, put,
                                             response_mime_type="text/plain")
        except Exception as exc:                            # noqa: BLE001
            print(f"    -> failed: {exc}")
            skipped.append((page, "ocr failed"))
            continue
        dest = os.path.join(out_dir, f"page_{page}.txt")
        with open(dest, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        written += 1

    print(f"\n  pages written {written}   skipped {len(skipped)}")
    for p, why in skipped:
        print(f"    p{p}: {why}")
    meta = os.path.join(out_dir, "source.json")
    with open(meta, "w", encoding="utf-8") as fh:
        json.dump({"source": args.source, "pages": args.pages,
                   "binarized": False,
                   "note": "Full-tone as scanned. Item 0FS: thresholding this "
                           "costs 30 points on the nun/gimel class."}, fh, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
