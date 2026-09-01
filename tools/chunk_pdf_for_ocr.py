#!/usr/bin/env python3
"""
tools/chunk_pdf_for_ocr.py

Split a scan PDF into small, upload-sized chunks for a third-party OCR service,
and write a manifest a submission script can RESUME from.

Written 2026-08-31 for the Dicta Rashi endpoint (<https://rashiocr.dicta.org.il/>),
but service-agnostic: it knows about page ranges and file sizes, not about Dicta.

**Why chunks at all.** The endpoint is a free service run by a research
institute. A 491-page book is not something to hand it in one request, and it is
not something to hammer with 491 either. Chunking makes the job resumable, keeps
each request small, and - with the delay the submitter applies - keeps the whole
run to a rate a human user would plausibly generate. Standing rule and the
user's directive are recorded in PROJECT-STATUS.md item 5.

**Re-saving matters.** A naive per-page `insert_pdf` carries the source's whole
resource tree into every chunk: this repo's own 3-page Berlin sample came out at
109 MB that way and needed re-saving to 1.0 MB with no re-compression and no
loss of image dimensions. Every chunk here is written with
`garbage=4, deflate=True, clean=True` for that reason, and the manifest records
each chunk's real size so an oversized one is visible before it is sent.

Usage:
  python3 tools/chunk_pdf_for_ocr.py --pdf book.pdf --pages 8 --out-dir chunks/
  python3 tools/chunk_pdf_for_ocr.py --pdf book.pdf --pages 8 --first 20 --last 27
"""

import argparse
import json
import os
import sys

import fitz

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "pipeline"))

import corpus_io as cio

# The service's real ceiling is unknown (see PROJECT-STATUS.md item 5's caveat).
# This is a self-imposed warning line, not a measured limit - it exists so an
# oversized chunk is caught here rather than by the endpoint.
SOFT_MAX_MB = 12.0


def chunk_ranges(first, last, per_chunk):
    """Inclusive 1-based page ranges. 1-based because that is how a person
    reads a page number off a scan, and how this repo numbers pages elsewhere
    (Lesson 30: `doc[N-1]` is page N - the conversion happens once, here)."""
    out = []
    p = first
    while p <= last:
        end = min(p + per_chunk - 1, last)
        out.append((p, end))
        p = end + 1
    return out


def write_chunk(src, first, last, out_path):
    """One chunk, garbage-collected. Returns its size in bytes."""
    dst = fitz.open()
    # from_page/to_page are 0-based; `first`/`last` are 1-based page numbers.
    dst.insert_pdf(src, from_page=first - 1, to_page=last - 1)
    dst.save(out_path, garbage=4, deflate=True, clean=True)
    dst.close()
    return os.path.getsize(out_path)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pdf", required=True, help="source scan PDF")
    ap.add_argument("--pages", type=int, default=8, help="pages per chunk (default 8)")
    ap.add_argument("--first", type=int, default=1, help="first page to include (1-based)")
    ap.add_argument("--last", type=int, help="last page to include (1-based, default: end)")
    ap.add_argument("--out-dir", default=None, help="where to write chunks "
                                                    "(default: <pdf-stem>_chunks/)")
    ap.add_argument("--label", default=None, help="chunk filename prefix (default: pdf stem)")
    args = ap.parse_args()

    if not os.path.exists(args.pdf):
        raise SystemExit(f"no such PDF: {args.pdf}")
    if args.pages < 1:
        raise SystemExit("--pages must be >= 1")

    src = fitz.open(args.pdf)
    last = args.last or src.page_count
    if not (1 <= args.first <= last <= src.page_count):
        raise SystemExit(f"--first/--last must sit inside 1..{src.page_count}")

    stem = os.path.splitext(os.path.basename(args.pdf))[0]
    label = args.label or stem
    out_dir = args.out_dir or os.path.join(os.path.dirname(os.path.abspath(args.pdf)),
                                           f"{stem}_chunks")
    os.makedirs(out_dir, exist_ok=True)

    ranges = chunk_ranges(args.first, last, args.pages)
    print(f"{os.path.basename(args.pdf)}: {src.page_count} pages")
    print(f"chunking pages {args.first}-{last} into {len(ranges)} chunks of <= {args.pages}\n")

    # MERGE, never clobber. The docstring promises a manifest a submitter can
    # RESUME from, and the manifest carries per-chunk submitted_at/status - but
    # a second partial run into the same directory used to rewrite it wholesale
    # from that run's entries only, so run 1's PDFs stayed on disk and vanished
    # from the manifest along with their "done" status. This repo hit exactly
    # that and the manifest had to be repaired by hand. Existing entries are
    # keyed by page range and preserved; a different source PDF is refused.
    manifest_path = os.path.join(out_dir, "manifest.json")
    existing = {}
    if os.path.exists(manifest_path):
        with open(manifest_path, encoding="utf-8") as f:
            prior = json.load(f)
        prior_src = prior.get("source_pdf")
        this_src = os.path.relpath(os.path.abspath(args.pdf), REPO)
        if prior_src and prior_src != this_src:
            raise SystemExit(
                f"{manifest_path} describes a different source PDF:\n"
                f"  existing: {prior_src}\n  this run: {this_src}\n"
                f"Use a different --out-dir rather than mixing two books' chunks.")
        for c in prior.get("chunks", []):
            existing[(c["first_page"], c["last_page"])] = c
        if existing:
            print(f"merging into {len(existing)} chunk(s) already in this manifest\n")

    entries, oversized = [], 0
    for i, (a, b) in enumerate(ranges, start=1):
        name = f"{label}_c{i:04d}_p{a:04d}-p{b:04d}.pdf"
        path = os.path.join(out_dir, name)
        size = write_chunk(src, a, b, path)
        mb = size / (1024 * 1024)
        flag = ""
        if mb > SOFT_MAX_MB:
            flag = f"  <-- OVER {SOFT_MAX_MB} MB, split further before sending"
            oversized += 1
        entry = {
            "chunk": i, "file": os.path.relpath(path, REPO),
            "first_page": a, "last_page": b, "pages": b - a + 1,
            "bytes": size,
            # The submitter fills these in; present from the start so the
            # manifest's shape never changes under a resuming run.
            "submitted_at": None, "output_file": None, "status": "pending",
        }
        prior = existing.pop((a, b), None)
        if prior:
            # Same pages: keep whatever the submitter recorded about them.
            for k in ("submitted_at", "output_file", "status", "job_id", "note"):
                if prior.get(k) is not None:
                    entry[k] = prior[k]
        entries.append(entry)
        print(f"  {name}  {mb:5.2f} MB{flag}")
        # Flush the manifest every chunk, not at the end - the standing
        # incremental-disk rule. A crash at chunk 40 must not lose 39.
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump({"source_pdf": os.path.relpath(os.path.abspath(args.pdf), REPO),
                       "source_pages": src.page_count,
                       "pages_per_chunk": args.pages,
                       "chunks": entries}, f, ensure_ascii=False, indent=2)
            f.flush()

    if existing:
        # Ranges this run did not cover stay in the manifest; dropping them is
        # what lost the resume state before.
        entries.extend(existing.values())
        entries.sort(key=lambda c: c["first_page"])
        for n, c in enumerate(entries, start=1):
            c["chunk"] = n
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump({"source_pdf": os.path.relpath(os.path.abspath(args.pdf), REPO),
                       "source_pages": src.page_count,
                       "pages_per_chunk": args.pages,
                       "chunks": entries}, f, ensure_ascii=False, indent=2)
            f.flush()
        print(f"\ncarried {len(existing)} untouched chunk(s) forward")

    print(f"\n{len(entries)} chunks -> {os.path.relpath(out_dir, REPO)}/")
    print(f"manifest: {os.path.relpath(os.path.join(out_dir, 'manifest.json'), REPO)}")
    if oversized:
        print(f"WARNING: {oversized} chunk(s) exceed {SOFT_MAX_MB} MB")
    print("\nNothing has been sent anywhere. Submission is a separate, "
          "deliberate step - see PROJECT-STATUS.md item 5 for the rate rule.")


if __name__ == "__main__":
    main()
