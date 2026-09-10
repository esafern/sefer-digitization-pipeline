#!/usr/bin/env python3
"""
tools/ocr_pages_cloud_vision.py

Read the same pages with the same real OCR engine from two different scans.

WHY THIS AND NOT THE VLM RUN. Item `0FU` re-read the reviewed slice from the
full-tone scan and moved TWO variables at once: the scan (bitonal -> full tone)
and the engine (DocAI -> a generative VLM). The nun/gimel class improved 83 -> 16
and the running text got worse, 0.970 -> 0.913 on entries the VLM transcribed
completely. Those pull in opposite directions and the experiment could not
separate them.

Cloud Vision is a dedicated OCR engine, needs no processor to be provisioned,
and can be pointed at either scan. Running it on both leaves exactly one
variable - the pixels - which is what decides whether this corpus should be
rebuilt from NLI's images.

WHAT IS BEING CONTROLLED. Same engine, same version, same 35 pages, same
segmentation, same ground truth (Sefaria's 100 reviewed entries). The only
difference is which file the bytes came from.

NO BINARIZATION on the full-tone side, per `0FS`: thresholding it ourselves cost
30 points on the class this is about.

Usage:
  SEFER_CORPUS_ROOT=~/work/hashorashim python3 tools/ocr_pages_cloud_vision.py \
      --pages 58-92 --source nli --out-dir ~/work/hashorashim/nli_cv_layer
  ... --source pdf --out-dir ~/work/hashorashim/gb_cv_layer
"""

import argparse
import glob
import io
import os
import sys

from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "pipeline"))
sys.path.insert(0, _HERE)
import fitz  # noqa: E402
import corpus_io as cio  # noqa: E402
from experiment_scan_source import inkbox  # noqa: E402


def vision_text(client, png, hints=("he",)):
    from google.cloud import vision
    image = vision.Image(content=png)
    ctx = vision.ImageContext(language_hints=list(hints))
    resp = client.document_text_detection(image=image, image_context=ctx)
    if resp.error.message:
        raise RuntimeError(resp.error.message)
    return resp.full_text_annotation.text or ""


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pages", required=True)
    ap.add_argument("--source", choices=("nli", "pdf"), required=True)
    ap.add_argument("--nli-glob", default="~/work/hashorashim/dedupmrg*/*.jpg")
    ap.add_argument("--offset", type=int, default=-40,
                    help="NLI index = page + offset; established over several "
                         "pages and stronger than a per-page correlation (0FU)")
    ap.add_argument("--dpi", type=int, default=400, help="pdf source render dpi")
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    from google.cloud import vision
    client = vision.ImageAnnotatorClient()
    lo, hi = (int(x) for x in args.pages.split("-"))
    out_dir = os.path.expanduser(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)
    nli_files = sorted(glob.glob(os.path.expanduser(args.nli_glob)))
    doc = fitz.open(cio.SCAN_PDF_PATH)

    done = 0
    for page in range(lo, hi + 1):
        dest = os.path.join(out_dir, f"page_{page}.txt")
        if os.path.exists(dest):
            done += 1
            continue
        if args.source == "pdf":
            pix = doc.load_page(page - 1).get_pixmap(dpi=args.dpi)
            im = Image.frombytes("RGB" if pix.n >= 3 else "L",
                                 (pix.width, pix.height), pix.samples)
        else:
            idx = page + args.offset
            if not (0 <= idx < len(nli_files)):
                print(f"  p{page}: no NLI image at index {idx}")
                continue
            im = Image.open(nli_files[idx])
            box = inkbox(im, 150, 0.02, inset=0.06)
            if box:
                pad = 40
                im = im.crop((max(0, box[0] - pad), max(0, box[1] - pad),
                              min(im.width, box[2] + pad), min(im.height, box[3] + pad)))
        buf = io.BytesIO()
        im.convert("RGB").save(buf, format="PNG", optimize=True)
        png = buf.getvalue()
        # Cloud Vision caps a request at 20 MB; a 600 dpi bitonal page can exceed
        # that as PNG, so step down rather than fail the page silently.
        while len(png) > 19_000_000 and im.width > 1200:
            im = im.resize((int(im.width * 0.8), int(im.height * 0.8)), Image.LANCZOS)
            buf = io.BytesIO()
            im.convert("RGB").save(buf, format="PNG", optimize=True)
            png = buf.getvalue()
        try:
            text = vision_text(client, png)
        except Exception as exc:                             # noqa: BLE001
            print(f"  p{page}: FAILED {exc}")
            continue
        with open(dest, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        done += 1
        print(f"  p{page}: {args.source} {im.size[0]}x{im.size[1]} "
              f"{len(png)//1024}KB -> {len(text)} chars")
    print(f"\n  pages available in {out_dir}: {done}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
