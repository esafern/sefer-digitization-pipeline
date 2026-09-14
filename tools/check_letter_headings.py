#!/usr/bin/env python3
"""
tools/check_letter_headings.py

Every entry's heading, checked name by name. Item 0GJ.

In a book whose entries open with the root spelled out as letter names - Sefer
HaShorashim: `האלף והגימל והפא .` is the root אגפ - the heading is the entry's
anchor, and each of its words must be the name of one of the root's letters in
the edition's own spelling, the doubling word `הכפולה`, or one of the qualifiers
the edition uses to part homographs (`עוד`, `הנראית`, ...). Reviewer 2026-09-14:
"any time those three words are not the name of three letters, we have a
concern." The rule itself is detect_root_entries.heading_concerns(), beside the
vocabulary it checks against.

A concern is a question for the ink, not a verdict.

Writes heading_concerns.json in the corpus root. The dashboard reads it on every
request and marks the `✎ Heading` control of each such entry - but only while
the entry's title is still the one checked, so a corrected heading does not go
on wearing an old concern. Re-run after any change to part1.json.

Usage:
  SEFER_CORPUS_ROOT=~/work/hashorashim python3 tools/check_letter_headings.py
"""

import argparse
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "pipeline"))
sys.path.insert(0, _HERE)
import corpus_io as cio  # noqa: E402
from detect_root_entries import heading_concerns  # noqa: E402


def check(klalim):
    """[{klal_id, root, title, concerns}] for every entry with a concern."""
    rows = []
    for k in klalim:
        concerns = heading_concerns(k.get("title") or "", k.get("gematria"))
        if concerns:
            rows.append({"klal_id": k["klal_id"], "root": k.get("gematria"),
                         "title": k.get("title") or "", "concerns": concerns})
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-name", default="heading_concerns.json")
    ap.add_argument("--url-base", default="http://127.0.0.1:8421")
    args = ap.parse_args()

    klalim = cio.load_klalim(cio.PART1_PATH)
    rows = check(klalim)
    doc = {"what_this_is": "Entries whose heading is not simply the root's letters "
                           "spelled out by name - one row per entry, with the reasons. "
                           "A question for the ink, not a verdict.",
           "checked": len(klalim), "rows": rows}
    dest = cio.repo_path(args.out_name)
    tmp = dest + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, dest)
    print(f"  {len(klalim)} headings checked, {len(rows)} with a concern")
    for r in rows:
        print(f"  {args.url_base}/entry/{r['klal_id']}  {r['title']}")
        for c in r["concerns"]:
            print(f"      {c}")
    print(f"  wrote {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
