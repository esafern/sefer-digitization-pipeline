#!/usr/bin/env python3
"""
tools/build_header_alignment.py

Produce `part1_header_anchored_alignment.json` - which scan page each section of
the corpus actually sits on, and how much that mapping should be trusted.

WHY THIS EXISTS. The file had **no producer at all**. Nothing in `pipeline/` or
`tools/` wrote it; it was a migrated cache, like `images/pdf_pages/` before
`tools/render_pdf_pages.py`. Item `0EI` found both as the two artifacts a second
book cannot generate, and this is the second one. It matters more than it looks:
`build_corrections_dataset.py` SKIPS any klal whose alignment is not trusted
rather than manufacture disagreements against an unreliable page, so without
this file a new corpus produces no correction candidates at all - silently, and
looking exactly like a clean book (Lesson 26).

TWO STRATEGIES, BECAUSE TWO BOOKS ANCHOR DIFFERENTLY.

`--strategy section-header` (Yad Malachi): each klal declares the alphabetical
section it belongs to (`כללי האלף`), and the page carries that section's name in
its running head. Match the expected string against the head, walking forward.

`--strategy root-range` (Sefer HaShorashim): the recto running head prints the
range of roots on the spread - `אבח - אגד` - so the check is not string
similarity but CONTAINMENT: does this entry's root sort between the two bounds?
That is a far stronger signal than matching a section letter, because it
brackets the entry rather than naming its chapter, and it is checkable against
the book's own alphabetical order.

**A printed range governs the page it appears on AND THE ONE BEFORE IT** - so an
entry on page P is checked against the ranges printed on P and P+1. Measured, not
assumed, across the א-ב-ג slice: ranges on {P} alone put 85.3% of entries inside,
{P, P-1} 44.8%, and {P, P+1} 86.5%. The verso of a spread carries
`NN ספר השרשים` instead of a range, so the recto's range is the one that governs
both halves. Coding this backwards drops the trusted rate from 86% to 44%, which
is what the first run of this tool did.

WHAT `trusted` MEANS HERE. Not "this is right" - "downstream may compare against
this page". An entry whose root falls outside every nearby printed range is
either on the wrong page or sitting behind a garbled head, and in both cases
comparing OCR against that page manufactures disagreements. It is reported, not
repaired.

Usage:
  SEFER_CORPUS_ROOT=~/work/hashorashim python3 tools/build_header_alignment.py \
      --strategy root-range --pages 58-151
  python3 tools/build_header_alignment.py --strategy section-header --dry-run
"""

import argparse
import difflib
import json
import os
import re
import sys
import unicodedata

# Bootstrap only - deliberately NOT bound to a name like REPO, which is the
# seam bypass tests/test_pipeline_logic.py's bypass guard exists to catch.
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "pipeline"))
sys.path.insert(0, _HERE)
import corpus_io as cio  # noqa: E402
from build_root_corpus import page_lines, classify  # noqa: E402

ALEPHBET = "אבגדהוזחטיכלמנסעפצקרשת"
FINALS = str.maketrans("ךםןףץ", "כמנפצ")
POINTS = re.compile(r"[֑-ׇ]")
RANGE = re.compile(r"([א-ת]{2,5})\s*[-–]\s*([א-ת]{2,5})")
# A page below this is gibberish OCR whatever its head says - a floor against a
# damaged or badly-scanned page, not a quality dial.
#
# IT HAS NEVER FIRED AND IS UNTESTED ON REAL DATA. Measured over the א-ב-ג slice
# (94 pages): min 0.844, 5th percentile 0.864, median 0.912, max 0.965. Nothing
# comes within 0.29 of the threshold, so every `trusted: false` in this book's
# alignment is the root-range test, never this one. Recorded rather than removed
# or retuned: a guard that has not fired is an unanswered question (Lesson 42),
# and the honest answer here is that this slice contains no page it was meant to
# catch - not that the guard works. Do not cite it as a passing check.
MIN_LEX = 0.55


def root_key(text):
    """Sort position of a root, folding finals - a root is written non-final."""
    r = POINTS.sub("", unicodedata.normalize("NFKC", text)).translate(FINALS)
    return tuple(ALEPHBET.index(c) if c in ALEPHBET else 99 for c in r)


def page_heads_and_lex(page, lexicon, head_mode="furniture"):
    """(head text, printed root range or None, lexicon hit rate) for one page.

    `head_mode` matters and getting it wrong is silent. "furniture" asks
    build_root_corpus.classify() which lines are running heads, which encodes
    HaShorashim's two head forms and finds nothing in Yad Malachi - the first run
    of the section-header strategy scored 0 of 222 trusted against a migrated
    file that is 100%, purely because the head came back empty. "topline" takes
    the page's two topmost lines whatever they look like, which is book-agnostic
    and is what a running head is by definition.
    """
    path = os.path.join(cio.DOCAI_DIR, f"page_{page}.json")
    if not os.path.exists(path):
        return None, None, 0.0
    with open(path, encoding="utf-8") as fh:
        tokens = json.load(fh)
    if not tokens:
        return None, None, 0.0
    lines = page_lines(tokens)
    if head_mode == "topline":
        head = " ".join(" ".join(t["text"] for t in ln) for ln in lines[:2])
    else:
        head = " ".join(t for lbl, _y, _h, t, _ln in classify(lines) if lbl == "head")
    words = [cio.hebrew_letters_only(t["text"]) for t in tokens]
    words = [w for w in words if len(w) >= 2]
    lex_rate = (sum(1 for w in words if w in lexicon) / len(words)) if words else 0.0
    m = RANGE.search(head)
    rng = None
    if m:
        # SORT THE BOUNDS. A printed range always ascends, but the head is RTL
        # and DocAI sometimes emits the two sides in reading order rather than
        # logical order - p79 comes out ('אלל', 'אלה'), whose end sorts before
        # its start, which is impossible in print and excludes the very entries
        # the range was meant to bracket. Sorting is safe precisely because the
        # ascending property is a fact about the book, not an assumption about
        # the OCR.
        rng = tuple(sorted((m.group(1), m.group(2)), key=root_key))
    return head, rng, lex_rate


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--strategy", choices=("root-range", "section-header"), required=True)
    ap.add_argument("--pages", help="PDF page window, e.g. 58-151 (default: every page "
                                    "any corpus record names)")
    ap.add_argument("--head-mode", choices=("furniture", "topline"), default=None,
                    help="how to find the running head; defaults to furniture for "
                         "root-range and topline for section-header")
    ap.add_argument("--out", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    klalim = cio.load_klalim(cio.PART1_PATH)
    with open(cio.LEXICON_PATH, encoding="utf-8") as fh:
        lexicon = {l.strip() for l in fh if l.strip()}

    pages = sorted({k.get("page") for k in klalim if k.get("page")})
    if args.pages:
        lo, hi = (int(x) for x in args.pages.split("-"))
        pages = [p for p in range(lo, hi + 1)]
    head_mode = args.head_mode or ("topline" if args.strategy == "section-header"
                                   else "furniture")
    info = {p: page_heads_and_lex(p, lexicon, head_mode) for p in pages}

    rows = []
    for k in klalim:
        page = k.get("page")
        head, rng, lex_rate = info.get(page, (None, None, 0.0))
        row = {"klal_id": k["klal_id"], "matched_page": page,
               "matched_page_header": (head or "")[:60],
               "lexicon_hit_rate": round(lex_rate, 3)}
        if args.strategy == "root-range":
            root = k.get("gematria", "")
            row["expected_section"] = k.get("section", "")
            # The printed range governs its own page AND the next (measured).
            candidates = [info.get(p, (None, None, 0.0))[1] for p in (page, page + 1)]
            candidates = [c for c in candidates if c]
            inside = any(root_key(a) <= root_key(root) <= root_key(b)
                         for a, b in candidates)
            row["printed_root_range"] = ["{} - {}".format(*c) for c in candidates][:1]
            row["match_ratio"] = 1.0 if inside else 0.0
            row["search_stage"] = 0 if inside else 1
            row["trusted"] = bool(inside and lex_rate >= MIN_LEX)
            row["untrusted_reason"] = (None if row["trusted"] else
                                       ("root outside every nearby printed range"
                                        if not inside else "page OCR below lexicon bar"))
        else:
            expected = k.get("section", "")
            # Best window of the head, not the whole head: the running head is
            # `יד מלאכי כללי האלף` and the expected section is `כללי האלף`, so
            # scoring the full string dilutes a perfect match with the book title.
            hd = head or ""
            ratio = max([difflib.SequenceMatcher(None, expected, hd[i:i + len(expected) + 3]).ratio()
                         for i in range(max(len(hd) - len(expected) + 4, 1))] or [0.0])
            row["expected_section"] = expected
            row["match_ratio"] = round(ratio, 3)
            row["search_stage"] = 0
            row["trusted"] = bool(ratio >= 0.5 and lex_rate >= MIN_LEX)
            row["untrusted_reason"] = (None if row["trusted"] else
                                       "header did not match the expected section")
        rows.append(row)

    trusted = sum(1 for r in rows if r["trusted"])
    print(f"  strategy        {args.strategy}")
    print(f"  klalim          {len(rows)}")
    print(f"  trusted         {trusted} ({100.0 * trusted / max(len(rows), 1):.1f}%)")
    by_reason = {}
    for r in rows:
        if not r["trusted"]:
            by_reason[r["untrusted_reason"]] = by_reason.get(r["untrusted_reason"], 0) + 1
    for reason, n in sorted(by_reason.items(), key=lambda x: -x[1]):
        print(f"     {n:>4}  {reason}")
    bad = [r for r in rows if not r["trusted"]][:8]
    if bad:
        print("  first untrusted:")
        for r in bad:
            print(f"     klal {r['klal_id']:<4} p{r['matched_page']:<5} "
                  f"head={r['matched_page_header'][:30]!r}")

    # REFUSE TO REGRESS AN EXISTING ALIGNMENT. `matched_page` here comes from the
    # corpus record's own `page` field, which is authoritative for a corpus this
    # pipeline segmented (HaShorashim: the page is where the heading line was
    # found) and NOT authoritative for Yad Malachi, whose `page` field
    # START_HERE calls "already stale/dead metadata for most of Part 1".
    #
    # Measured: against Yad Malachi's migrated alignment this tool agrees on 211
    # of 222 klalim and differs on 11 - klalim 76-84, page 37 against 38, which
    # is exactly the transposed-leaf remap that was applied to the alignment and
    # DELIBERATELY not to part1.json. Writing would have rolled that fix back
    # while reporting 100% trusted. Reproducing the original forward search is
    # the proper fix and is not done; until then this refuses rather than
    # silently regresses.
    out = args.out or cio.ALIGNMENT_PATH
    if os.path.exists(out) and not args.dry_run:
        try:
            with open(out, encoding="utf-8") as fh:
                existing = {r["klal_id"]: r.get("matched_page")
                            for r in json.load(fh)}
        except Exception:
            existing = {}
        moved = [r["klal_id"] for r in rows
                 if r["klal_id"] in existing
                 and existing[r["klal_id"]] != r["matched_page"]]
        if moved:
            print(f"\n  REFUSING TO WRITE: {len(moved)} klalim would change page against "
                  f"the existing alignment.")
            print(f"  e.g. klal {moved[0]}: {existing[moved[0]]} -> "
                  f"{[r for r in rows if r['klal_id']==moved[0]][0]['matched_page']}")
            print("  The corpus `page` field is not authoritative for this book. See "
                  "item 0EP.")
            print("  Pass --out to write elsewhere if you meant to compare.")
            return 2
    if args.dry_run:
        print(f"  would write     {out}")
        return 0
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=1)
        fh.flush()
        os.fsync(fh.fileno())
    print(f"  wrote           {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
