#!/usr/bin/env python3
"""
tools/build_dicta_baseline.py

Concatenate the per-chunk Dicta OCR outputs into the ONE tracked witness
baseline, in page order, from the chunk manifests.

Why this is a script and not a `cat`. The baseline is a derived file - it is
fully computable from the per-chunk outputs - and a hand-typed `cat` puts its
correctness in whoever typed the argument order (Lesson 13). That was tolerable
at five chunks in one range; pages 51-114 arrive as five more, in a second
directory, and "which order did I list them in" is exactly where a silent defect
enters. Page order comes from the manifests here, never from the command line.

What is tracked and what is not (PROJECT-STATUS.md item 0W): the per-chunk
outputs in `dicta_output/` stay untracked - they are intermediates, and tracking
them put ~7,100 lines of machine output into a diff. THIS file is tracked,
beside `surya_part1_full_baseline.txt` and `vlm_part1_full_baseline.txt`, which
it is the peer of. Dicta's output is the only witness baseline that cannot be
regenerated on demand: Surya runs locally, the VLM runs against an API we
control, and Dicta needs a free third-party service that rate-limits us.

Usage:
  python3 tools/build_dicta_baseline.py
  python3 tools/build_dicta_baseline.py --check   # verify without writing
"""

import argparse
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DEFAULT_OUT = os.path.join(REPO, "tools", "second_witness_eval",
                           "dicta_jerusalem_part1_baseline.txt")


def collect_chunks():
    """Every completed chunk across all manifests, ordered by first page.

    Ordered by PAGE, not by chunk id or filename: the calibration chunk is
    `c0001` in its own manifest and covers pages 29-32, which sits inside the
    range `c0001` covers in another. Sorting on anything but the page number
    interleaves the book.
    """
    chunks = []
    for man_path in sorted(glob.glob(os.path.join(REPO, "dicta_chunks*", "manifest.json"))):
        with open(man_path, encoding="utf-8") as f:
            man = json.load(f)
        for c in man.get("chunks", []):
            out = c.get("output_file")
            if c.get("status") != "done" or not out:
                continue
            chunks.append({
                "first_page": c["first_page"], "last_page": c["last_page"],
                "path": os.path.join(REPO, out),
                "manifest": os.path.relpath(man_path, REPO),
            })
    chunks.sort(key=lambda c: c["first_page"])
    return chunks


def check_coverage(chunks):
    """Gaps and overlaps are silent corruption: a missing page drops text from
    the middle of the baseline, and a repeated one duplicates it. Either would
    show up downstream as a mysterious alignment failure rather than as an
    error, so say so here."""
    problems = []
    for prev, cur in zip(chunks, chunks[1:]):
        if cur["first_page"] > prev["last_page"] + 1:
            problems.append(f"GAP: pages {prev['last_page'] + 1}-{cur['first_page'] - 1} "
                            f"missing between {os.path.basename(prev['path'])} and "
                            f"{os.path.basename(cur['path'])}")
        elif cur["first_page"] <= prev["last_page"]:
            problems.append(f"OVERLAP: {os.path.basename(prev['path'])} and "
                            f"{os.path.basename(cur['path'])} both cover page "
                            f"{cur['first_page']}")
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--check", action="store_true",
                    help="report coverage and exit non-zero on a gap; write nothing")
    args = ap.parse_args()

    chunks = collect_chunks()
    if not chunks:
        raise SystemExit("no completed chunks found in any dicta_chunks*/manifest.json")

    missing = [c["path"] for c in chunks if not os.path.exists(c["path"])]
    if missing:
        raise SystemExit("manifest claims done but the output is not on disk:\n  "
                         + "\n  ".join(missing))

    problems = check_coverage(chunks)
    first, last = chunks[0]["first_page"], chunks[-1]["last_page"]
    print(f"{len(chunks)} completed chunk(s), pages {first}-{last}:")
    for c in chunks:
        print(f"  p{c['first_page']:>4}-{c['last_page']:<4} {os.path.basename(c['path'])}")
    for p in problems:
        print(f"  {p}")

    if args.check:
        raise SystemExit(1 if problems else 0)
    if problems:
        raise SystemExit("refusing to write a baseline with a gap or overlap; "
                         "fix the manifests or fetch the missing chunk first")

    # ASCII-only header. Every consumer of this file tokenizes to
    # Hebrew-bearing words (corpus_io.hebrew_letters_only), so a Latin header is
    # dropped before alignment - asserted by tests. It is here because a tracked
    # baseline whose coverage is not stated IN the file is a stale artifact
    # waiting to be quoted as if it were complete.
    complete = first <= 22 and last >= 114
    header = (f"# Dicta RashiOCR baseline - Jerusalem 1975/6 edition\n"
              f"# Scan pages {first}-{last} of "
              f"yad-malachi-jerusalem-rashi-Hebrewbooks_org_14122.pdf\n"
              # Gated, not unconditional: a finished baseline that still says
              # PARTIAL trains the reader to ignore the line.
              + (f"# COMPLETE for Part 1 (pages 22-114).\n" if complete else
                 f"# PARTIAL - Part 1 is pages 22-114; this stops at {last}.\n")
              + f"# Built by tools/build_dicta_baseline.py - do not hand-edit.\n")
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(header)
        for c in chunks:
            with open(c["path"], encoding="utf-8") as src:
                # Exactly one newline at every seam. Dicta's outputs do not end
                # with one, so a bare concatenation fuses the last word of chunk
                # N to the `=== עמוד 1 ===` marker opening chunk N+1
                # (`תורה=== עמוד 1 ===`). That defeats the line-anchored strip
                # every consumer uses (`^===\s*עמוד.*$`) and leaks one phantom
                # `עמוד` token into the witness stream per seam - at the chunk
                # boundary, which is exactly where alignment is most fragile.
                f.write(src.read().rstrip("\n") + "\n")
            f.flush()
    print(f"\nWrote {os.path.relpath(args.out, REPO)} "
          f"({os.path.getsize(args.out):,} bytes)")
    if last < 114:
        print(f"NOTE: Part 1 runs to page 114; this baseline stops at {last}. "
              f"{114 - last} pages still to OCR.")


if __name__ == "__main__":
    main()
