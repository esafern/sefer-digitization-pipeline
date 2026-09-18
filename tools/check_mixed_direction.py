#!/usr/bin/env python3
"""
tools/check_mixed_direction.py

Find places in English prose where two separate pieces of Hebrew are divided
only by punctuation, so a reader's screen runs them together backwards.

WHY (item 0IF, reviewer 2026-09-18: "reverse hebrew mixed with english leads to
confused sentences"). In a left-to-right paragraph, the Unicode bidi algorithm
treats spaces, commas, periods and brackets BETWEEN two Hebrew runs as part of
one right-to-left run. So

    Under shoresh אבל, (שופטים ז, ככ). ככ is not a number

is drawn with the shoresh, the citation and the numeral in reverse order, and
the sentence reads as nonsense in an email client. The fix is in the writing,
not the rendering: put English between the two pieces -

    Under shoresh אבל the note reads (שופטים ז, ככ), and the numeral ככ is ...

A citation's own inner comma, `(שופטים ז, ככ)`, is one piece and is fine; so is a
Hebrew phrase whose words are separated by spaces only. What is flagged is two
pieces with a comma, period, colon, semicolon or bracket boundary between them
and no English word in between.

Usage:
  python3 tools/check_mixed_direction.py FILE [FILE ...]
Exit status 1 if anything is flagged, so it can gate a draft before it is sent.
"""

import re
import sys

HEB = "֐-׿"
# A piece of Hebrew: a parenthesised group containing Hebrew is ONE piece (a
# citation's inner comma is not a boundary), otherwise a run of Hebrew words
# joined by spaces, maqaf or the marks that live inside words.
PAREN = re.compile(r"\([^()]*[" + HEB + r"][^()]*\)")
PLACEHOLDER = ""          # private-use: stands for one parenthesised piece
PIECE = re.compile("(?:[" + HEB + PLACEHOLDER + "][" + HEB + PLACEHOLDER + r"'\"׳״\-]*)"
                   "(?:\\s+[" + HEB + PLACEHOLDER + "][" + HEB + PLACEHOLDER + r"'\"׳״\-]*)*")
BOUNDARY = re.compile(r"[,.;:()\[\]]")


def problems(text):
    """[(line number, excerpt)] for every pair of Hebrew pieces run together."""
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        groups = []
        masked = PAREN.sub(lambda m: groups.append(m.group(0)) or PLACEHOLDER, line)
        pieces = list(PIECE.finditer(masked))
        for a, b in zip(pieces, pieces[1:]):
            between = masked[a.end():b.start()]
            if re.search("[A-Za-z]", between):
                continue                     # English between them: drawn in order
            if not BOUNDARY.search(between):
                continue                     # only spaces: one phrase
            it = iter(groups)
            unmask = lambda s: re.sub(PLACEHOLDER, lambda _m: next(it, "(...)"), s)
            # re-expand placeholders for a readable excerpt
            start = max(0, a.start() - 20)
            excerpt = masked[start:b.end() + 20]
            it = iter(groups[masked[:start].count(PLACEHOLDER):])
            out.append((n, unmask(excerpt)))
    return out


def main(paths):
    bad = 0
    for p in paths:
        with open(p, encoding="utf-8") as fh:
            found = problems(fh.read())
        for n, ex in found:
            print(f"{p}:{n}: {ex}")
        bad += len(found)
    print(f"{bad} place(s) where two pieces of Hebrew run together" if bad else "clean")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
