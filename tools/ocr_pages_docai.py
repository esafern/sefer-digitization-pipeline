#!/usr/bin/env python3
"""
tools/ocr_pages_docai.py

Read scan pages with Document AI, from either scan.

WHY THIS IS THE ONE THAT MATTERS. Item `0FW` measured the two variables
separately and they point in opposite directions:

    Cloud Vision on bitonal      chars 0.8588   nun/gimel 39
    Cloud Vision on FULL TONE    chars 0.8788   nun/gimel  8
    DocAI on bitonal (the corpus) chars 0.9499  nun/gimel 72

Holding the engine fixed, the full-tone scan is worth +2 points of characters
and a 79% cut in the dominant error class. Holding the scan fixed, DocAI is
worth +7 points over Cloud Vision. Nobody has yet run the combination that
should carry both - DocAI on the full-tone images - because it needs a Document
AI processor provisioned, which is a console and billing decision.

This tool is that run, waiting for a processor id.

CONFIGURATION. Three values, by environment variable or flag:
    DOCAI_PROJECT     the project id, e.g. gen-lang-client-0289907848
    DOCAI_LOCATION    the processor's region: "us" or "eu" (NOT a zone)
    DOCAI_PROCESSOR   the processor id - the last path segment of
                      projects/<n>/locations/<loc>/processors/<ID>

The endpoint is derived from the location and must match it; a processor created
in `eu` is invisible to the `us` endpoint and returns a bare permission error
rather than "not found", which is a confusing hour if you have not seen it.

NO BINARIZATION on the full-tone side, per `0FS`: thresholding it ourselves cost
30 points on the class this exists to fix.

Usage:
  DOCAI_PROJECT=... DOCAI_LOCATION=us DOCAI_PROCESSOR=... \
  SEFER_CORPUS_ROOT=~/work/hashorashim \
    python3 tools/ocr_pages_docai.py --pages 58-92 --source nli \
      --out-dir ~/work/hashorashim/nli_docai_layer
  ... --source pdf --out-dir ~/work/hashorashim/gb_docai_layer
  python3 tools/ocr_pages_docai.py --check          # verify config only
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

MAX_BYTES = 19_000_000     # Document AI online processing caps a request at 20 MB


def client_and_name(project, location, processor):
    from google.cloud import documentai_v1 as documentai
    from google.api_core.client_options import ClientOptions
    client = documentai.DocumentProcessorServiceClient(
        client_options=ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com"))
    return client, client.processor_path(project, location, processor)


def check(project, location, processor):
    """Prove the configuration works before spending a run on it."""
    missing = [n for n, v in (("DOCAI_PROJECT", project),
                              ("DOCAI_LOCATION", location),
                              ("DOCAI_PROCESSOR", processor)) if not v]
    if missing:
        print("  NOT CONFIGURED - missing: " + ", ".join(missing))
        return False
    print(f"  project   {project}")
    print(f"  location  {location}")
    print(f"  processor {processor}")
    try:
        client, name = client_and_name(project, location, processor)
        p = client.get_processor(name=name)
        print(f"  OK: {p.display_name}  type={p.type_}  state={p.state.name}")
        return True
    except Exception as exc:                                  # noqa: BLE001
        msg = str(exc)
        print(f"  FAILED: {type(exc).__name__}: {msg[:220]}")
        if "IAM_PERMISSION_DENIED" in msg or "denied" in msg:
            print("  -> the service account needs roles/documentai.apiUser on the "
                  "project (see the setup notes in PROJECT-STATUS item 0FY).")
        if "not found" in msg.lower():
            print("  -> check DOCAI_LOCATION matches the region the processor was "
                  "created in; a processor in eu is invisible to the us endpoint.")
        return False


def page_png(doc, nli_files, page, source, offset, dpi):
    if source == "pdf":
        pix = doc.load_page(page - 1).get_pixmap(dpi=dpi)
        im = Image.frombytes("RGB" if pix.n >= 3 else "L",
                             (pix.width, pix.height), pix.samples)
    else:
        idx = page + offset
        if not (0 <= idx < len(nli_files)):
            return None, None
        im = Image.open(nli_files[idx])
        box = inkbox(im, 150, 0.02, inset=0.06)
        if box:
            pad = 40
            im = im.crop((max(0, box[0] - pad), max(0, box[1] - pad),
                          min(im.width, box[2] + pad), min(im.height, box[3] + pad)))
    buf = io.BytesIO()
    im.convert("RGB").save(buf, format="PNG", optimize=True)
    png = buf.getvalue()
    while len(png) > MAX_BYTES and im.width > 1200:
        im = im.resize((int(im.width * 0.8), int(im.height * 0.8)), Image.LANCZOS)
        buf = io.BytesIO()
        im.convert("RGB").save(buf, format="PNG", optimize=True)
        png = buf.getvalue()
    return im, png


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pages")
    ap.add_argument("--source", choices=("nli", "pdf"))
    ap.add_argument("--out-dir")
    ap.add_argument("--nli-glob", default="~/work/hashorashim/dedupmrg*/*.jpg")
    ap.add_argument("--offset", type=int, default=-40)
    ap.add_argument("--dpi", type=int, default=400)
    ap.add_argument("--project", default=os.environ.get("DOCAI_PROJECT"))
    ap.add_argument("--location", default=os.environ.get("DOCAI_LOCATION", "us"))
    ap.add_argument("--processor", default=os.environ.get("DOCAI_PROCESSOR"))
    ap.add_argument("--check", action="store_true", help="verify configuration and stop")
    args = ap.parse_args()

    ok = check(args.project, args.location, args.processor)
    if args.check:
        return 0 if ok else 1
    if not ok:
        return 1
    for req in ("pages", "source", "out_dir"):
        if not getattr(args, req):
            raise SystemExit(f"--{req.replace('_','-')} is required for a run")

    from google.cloud import documentai_v1 as documentai
    client, name = client_and_name(args.project, args.location, args.processor)
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
        im, png = page_png(doc, nli_files, page, args.source, args.offset, args.dpi)
        if png is None:
            print(f"  p{page}: no image")
            continue
        try:
            result = client.process_document(request=documentai.ProcessRequest(
                name=name,
                raw_document=documentai.RawDocument(content=png, mime_type="image/png")))
            text = result.document.text or ""
        except Exception as exc:                              # noqa: BLE001
            print(f"  p{page}: FAILED {type(exc).__name__}: {str(exc)[:160]}")
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
