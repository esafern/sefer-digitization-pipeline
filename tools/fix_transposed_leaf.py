#!/usr/bin/env python3
"""Move a single PDF leaf to a new position - a generic fix for a scan
whose source binding had leaves out of order, not specific to any one work.

Worked example this script was built for: Yad Malachi's Berlin scan had two
leaves transposed in the SOURCE SCAN ITSELF (not an extraction bug) - found
via a catchword-chain sweep across the whole book, confirmed by rendering
both pages directly. See PROJECT-STATUS.md's 2026-08-18 entry for the full
finding, including which OTHER page-indexed caches (OCR token boxes,
rendered page images, alignment/gematria-trace files) had to be updated in
lockstep - this script only fixes the PDF's own physical page order; it does
not know about any derived cache built from the PDF before the fix.

Usage:
    python3 tools/fix_transposed_leaf.py --pdf path/to/scan.pdf \\
        --from-index 37 --to-index 36 --output path/to/scan_fixed.pdf

--from-index / --to-index are 0-indexed PDF page positions (not printed
folio numbers - check which convention any evidence you're using follows).
The operation is its own inverse: re-running with the two indices swapped
restores the original order.
"""
import argparse
import sys

import fitz  # pymupdf


def move_leaf(pdf_path, from_index, to_index, output_path):
    doc = fitz.open(pdf_path)
    if not (0 <= from_index < doc.page_count):
        sys.exit(f"--from-index {from_index} out of range (document has {doc.page_count} pages)")
    if not (0 <= to_index < doc.page_count):
        sys.exit(f"--to-index {to_index} out of range (document has {doc.page_count} pages)")
    before = doc.page_count
    doc.move_page(from_index, to_index)
    if doc.page_count != before:
        sys.exit(f"page count changed ({before} -> {doc.page_count}) during move - aborting, not saving")
    doc.save(output_path)
    print(f"Moved leaf {from_index} -> {to_index}. Saved {output_path} ({doc.page_count} pages, unchanged).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pdf", required=True, help="source PDF to read")
    parser.add_argument("--from-index", type=int, required=True, help="0-indexed page to move")
    parser.add_argument("--to-index", type=int, required=True, help="0-indexed destination position")
    parser.add_argument("--output", required=True, help="path to save the corrected PDF (must differ from --pdf)")
    args = parser.parse_args()
    if args.output == args.pdf:
        sys.exit("--output must differ from --pdf - this script never overwrites the source in place")
    move_leaf(args.pdf, args.from_index, args.to_index, args.output)
