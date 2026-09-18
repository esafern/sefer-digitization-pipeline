#!/usr/bin/env python3
"""
tools/check_draft.py

Check an email draft before it is handed to the reviewer to send. Two checks,
each a failure that already reached a real correspondent or nearly did:

1. HEBREW THAT RENDERS BACKWARDS (tools/check_mixed_direction.py, item 0IF):
   two pieces of Hebrew divided only by punctuation are drawn in reverse order
   in a left-to-right email.

2. A PROMISED ATTACHMENT (item 0IJ, reviewer 2026-09-18: "you need to remind me
   when i need to attach a file b/c the body says I will"). A draft that says a
   file is attached must carry, at the top, one line per file:

       ATTACH: citation_corrections.csv  (~/work/hashorashim/citation_corrections.csv ...)

   and the path in the parentheses - or the bare name, beside the draft - must
   exist. The body is copied into an email by hand; the ATTACH line is the part
   that cannot be missed, and the reminder the reviewer asked for travels with
   the draft rather than with a chat reply that is gone by the time it is sent.

Usage:
  python3 tools/check_draft.py DRAFT [DRAFT ...]
Exit status 1 if either check finds anything.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_mixed_direction as cmd  # noqa: E402

MENTIONS = re.compile(r"\battach(ed|ment|ments|ing)?\b", re.I)
ATTACH_LINE = re.compile(r"^ATTACH:\s*(\S+)(?:\s*\(([^)\s]+))?", re.M)


def attachment_problems(text, draft_dir="."):
    """[str] - what is wrong with the draft's attachments, empty if nothing."""
    out = []
    declared = ATTACH_LINE.findall(text)
    body = ATTACH_LINE.sub("", text)
    if MENTIONS.search(body) and not declared:
        line = body[:MENTIONS.search(body).start()].count("\n") + 1
        out.append(f"the body mentions an attachment (near line {line}) but there is no "
                   "'ATTACH: <file>' line at the top")
    for name, path in declared:
        candidates = [os.path.expanduser(path)] if path else []
        candidates.append(os.path.join(draft_dir, name))
        if not any(os.path.exists(c) for c in candidates):
            out.append(f"ATTACH names {name!r} but no such file exists "
                       f"({', '.join(candidates)})")
    return out


def main(paths):
    bad = 0
    for p in paths:
        with open(p, encoding="utf-8") as fh:
            text = fh.read()
        for n, ex in cmd.problems(text):
            print(f"{p}:{n}: Hebrew runs together: {ex}")
            bad += 1
        for msg in attachment_problems(text, os.path.dirname(os.path.abspath(p))):
            print(f"{p}: {msg}")
            bad += 1
        for name, path in ATTACH_LINE.findall(text):
            print(f"{p}: REMEMBER TO ATTACH {name}" + (f"  <- {path}" if path else ""))
    print(f"{bad} problem(s)" if bad else "clean")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
