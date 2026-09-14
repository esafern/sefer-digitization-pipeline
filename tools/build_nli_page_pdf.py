#!/usr/bin/env python3
"""
tools/build_nli_page_pdf.py

Assemble a book's page PDF with NLI's full-tone photographs in place of the
base scan's pages, so the page image and the OCR tokens share one coordinate
space. Item `0GC`, option (a), chosen by the reviewer 2026-09-13.

WHY. `tools/ocr_pages_docai.py` sends DocAI the NLI photograph cropped to its
text block (`experiment_scan_source.nli_text_crop`), so every token it returns
is normalised to THAT crop. The dashboard's scan pane and the vision
adjudicator's crops are both drawn from `book.json`'s `scan_pdf`. With the
Google Books PDF there, the same word on p58 sat at y1 0.218 in the page image
and 0.019 in the tokens - every box and every crop would have been misplaced.
Embedding exactly the crop DocAI saw makes the two agree by construction, and
gives the reviewer and the adjudicator the full-tone scan `0FS` measured at 90%
against 18% on nun/gimel.

WHAT IT REFUSES. Every page in --pages must be in the offset check
(`tools/verify_nli_page_offset.py`) with an accepted status AT the NLI index
this run would use. A page substituted without that is a photograph of some
page, which is `0FU`'s failure. Pages outside --pages are copied from the base
PDF unchanged, so page numbering - which every cache here is keyed on - does
not move. Substitute only pages whose tokens also come from NLI: an NLI image
under Google-space tokens is the same defect in the other direction, and
`render_pdf_pages.py --verify` checks exactly that.

PAGE SIZE. The mediabox is the crop's pixel size at --nominal-dpi (150), so the
dashboard's 150 DPI render shows the photograph's native pixels.

Built in memory and saved once, atomically: it is local, deterministic and
seconds long, so there is nothing for per-item flushing to protect.

Usage:
  SEFER_CORPUS_ROOT=~/work/hashorashim python3 tools/build_nli_page_pdf.py \\
      --base-pdf ~/work/hashorashim/Sefer_hashorashim_berlin_1896.pdf \\
      --check ~/work/hashorashim/nli_page_offset_check.jsonl \\
      --pages 58-151 --out ~/work/hashorashim/Sefer_hashorashim_nli_fulltone.pdf
"""

import argparse
import glob
import io
import json
import os
import sys

from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "pipeline"))
sys.path.insert(0, _HERE)
import fitz  # noqa: E402
from experiment_scan_source import nli_text_crop  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-pdf", required=True)
    ap.add_argument("--check", required=True, help="verify_nli_page_offset.py output")
    ap.add_argument("--pages", required=True, help="PDF pages to substitute, e.g. 58-151")
    ap.add_argument("--out", required=True)
    ap.add_argument("--offset", type=int, default=-40)
    ap.add_argument("--nli-glob", default="~/work/hashorashim/dedupmrg*/*.jpg")
    ap.add_argument("--accept", default="PASS,TEXT_ONLY")
    ap.add_argument("--nominal-dpi", type=float, default=150.0)
    ap.add_argument("--jpeg-quality", type=int, default=92)
    ap.add_argument("--sources-out", default=None,
                    help="default: page_image_sources.json beside --out")
    args = ap.parse_args()

    base_path = os.path.abspath(os.path.expanduser(args.base_pdf))
    out_path = os.path.abspath(os.path.expanduser(args.out))
    if base_path == out_path:
        raise SystemExit("--out must not be --base-pdf")
    accept = set(args.accept.split(","))
    lo, hi = (int(x) for x in args.pages.split("-"))
    nli_files = sorted(glob.glob(os.path.expanduser(args.nli_glob)))
    with open(os.path.expanduser(args.check), encoding="utf-8") as fh:
        check = {r["page"]: r for r in map(json.loads, fh)}

    refused = []
    for n in range(lo, hi + 1):
        r = check.get(n)
        idx = n + args.offset
        here = os.path.basename(nli_files[idx]) if 0 <= idx < len(nli_files) else None
        # The FILE, not only the index (code review 2026-09-13, finding 6): a
        # different --nli-glob or image folder puts a different photograph at
        # the same index, and the index check alone would embed it.
        if (r is None or r["status"] not in accept or r.get("nli_index") != idx
                or here is None or r.get("nli_file") != here):
            refused.append((n, None if r is None else r["status"]))
    if refused:
        raise SystemExit(f"refusing: {len(refused)} page(s) in {lo}-{hi} are not verified "
                         f"at offset {args.offset}: {refused[:20]}")

    base = fitz.open(base_path)
    out = fitz.open()
    sources = {}
    for n in range(1, base.page_count + 1):
        if lo <= n <= hi:
            path = nli_files[n + args.offset]
            im = nli_text_crop(Image.open(path)).convert("RGB")
            buf = io.BytesIO()
            im.save(buf, format="JPEG", quality=args.jpeg_quality)
            scale = 72.0 / args.nominal_dpi
            page = out.new_page(width=im.width * scale, height=im.height * scale)
            page.insert_image(page.rect, stream=buf.getvalue())
            sources[str(n)] = {"source": "nli_fulltone", "nli_file": os.path.basename(path),
                               "crop_px": [im.width, im.height],
                               "offset_check": check[n]["status"]}
        else:
            out.insert_pdf(base, from_page=n - 1, to_page=n - 1)
    if out.page_count != base.page_count:
        raise SystemExit(f"page count {out.page_count} != base {base.page_count}")

    tmp = out_path + ".tmp"
    out.save(tmp, garbage=3, deflate=True)
    os.replace(tmp, out_path)

    sources_path = args.sources_out or os.path.join(os.path.dirname(out_path),
                                                    "page_image_sources.json")
    with open(sources_path, "w", encoding="utf-8") as fh:
        json.dump({"base_pdf": os.path.basename(base_path),
                   "offset": args.offset, "nominal_dpi": args.nominal_dpi,
                   "substituted": sources}, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print(f"  {len(sources)} pages from NLI ({lo}-{hi}), "
          f"{base.page_count - len(sources)} from {os.path.basename(base_path)}")
    print(f"  wrote {out_path} ({os.path.getsize(out_path) // (1024 * 1024)} MB)")
    print(f"  wrote {sources_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
