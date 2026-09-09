#!/usr/bin/env python3
"""
tools/build_root_corpus.py

Build a `part*.json` corpus for a root-dictionary from the DocAI token stream,
splitting it at the entry headings `tools/detect_root_entries.py` finds.

WHY THE TOKEN STREAM AND NOT THE PDF TEXT LAYER. The recovered Google Books
layer is free and covers the whole book, and it is DocAI's TWIN - measured on
Yad Malachi, its top four substitutions are DocAI's, same errors and same counts
(item 0ED). Building the corpus from it would bake DocAI's mistakes in while
looking like corroboration. The layer's job is the reliability gate in
`tools/gate_docai_against_layer.py`; the corpus comes from DocAI, whose tokens
also carry the bounding boxes every later crop and alignment needs.

HOW THE PAGE IS SEPARATED. The FOOTNOTE apparatus separates geometrically; the
RUNNING HEADS do not, and assuming they did cost 30 contaminated entries on the
first build - see RUNNING_HEAD below. Bacher's
footnote apparatus is dense and is one of the three things Sefaria named
explicitly, but it does not need judgement to FIND - it is physically smaller
type in a block at the foot of the page. Measured on PDF page 121:

    line 0      y 0.072  h 0.0127   `72 ספר השרשים`          running head
    lines 1-32  y 0.105  h 0.0176-0.0213                      BODY
    line 33     y 0.790  h 0.0123   `לב וישטפני .`            catchword
    lines 34-39 y 0.813  h 0.0102-0.0127                      APPARATUS
    line 40     y 0.959  h 0.0237   `Google by Digitized`     watermark

So body type is ~0.019 and apparatus type ~0.011, a 1.7x gap that holds across
sampled pages. Classification uses the PER-PAGE median line height rather than a
fixed constant, because page images vary in size by 10-20% (the book is
hand-placed for each shot) and a fixed threshold would drift with them.

Token height alone does NOT work and was tried first: a short word like `מה`
has a smaller box for want of ascenders regardless of its type size, so 29-31%
of tokens read as "small" scattered through the body. The signal is only clean
once tokens are clustered into LINES and the line's median height is used.

WHAT THIS DOES NOT DO. The superscript footnote REFERENCE numbers sit inline in
the body (`בצקו 16`, `בציר 24`) and are left there. Separating them is the same
problem as item `0CY` and it is deliberately deferred - Sefaria's own dataset
may already carry the apparatus, and duplicating that work before seeing it
would be wasteful (item 0EE). Every entry therefore carries its reference
numerals in the running text, and that is a known, recorded defect rather than
an oversight.

Usage:
  python3 tools/build_root_corpus.py --pages 58-151 --out part1.json
  python3 tools/build_root_corpus.py --pages 58-151 --dry-run --show 3
"""

import argparse
import json
import os
import re
import difflib
import statistics
import sys

# Bootstrap only - deliberately NOT bound to a name like REPO, which is the
# seam bypass tests/test_pipeline_logic.py's bypass guard exists to catch.
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "pipeline"))
sys.path.insert(0, _HERE)
import corpus_io as cio  # noqa: E402
from detect_root_entries import match_heading, ALEPHBET  # noqa: E402

LINE_TOL = 0.006          # y distance within which tokens share a line
SMALL_RATIO = 0.75        # a line is "small type" below this fraction of the page median
HEAD_MAX_Y = 0.10         # running head sits above this
FOOT_MIN_Y = 0.60         # nothing above this is ever apparatus
# The apparatus is found as the BOTTOM-UP RUN of small-type lines, not by a fixed
# y cutoff. A cutoff of 0.75 looked right on p121, where the block starts at
# 0.790 - and on p139 the apparatus begins at y=0.727 with the numbered
# references at 0.748, so two lines of scripture citations were classified as
# body and landed inside klal 262's text:
#   `תהלים עב ו . 2 עמוס ז א . 3 יחזקאל יח יח . 4 ויקרא ה כג`
# Their HEIGHT said apparatus all along (ratio 0.59 and 0.67 against a body
# range of 0.90-1.08); only the y test failed. Found by
# tools/detect_repeated_words.py flagging `יח יח` and `כח כח` - a cheap
# mechanical sweep catching what the geometric filter missed (Lesson 8).
WATERMARK = re.compile(r"Google|Digitized", re.I)

# TWO SIGNALS FOR THE APPARATUS, because neither works alone (Lesson 9).
# HEIGHT alone fails at the block's top edge: apparatus lines run 0.52-0.80 of
# the page median and short BODY lines dip to 0.76-0.80 too, because a line's
# median token height depends on which letters it happens to contain. A 0.75 cut
# therefore stopped the bottom-up scan early and left two lines of scripture
# citations inside klal 237 and klal 272.
# PERIOD DENSITY separates what height cannot: every citation ends in one, so
# apparatus lines measure 0.20-0.24 periods per token against body's 0.00-0.17.
# Requiring both keeps a short body line out of the block and pulls the block's
# top edge in.
APPARATUS_MAX_RATIO = 0.85
APPARATUS_MIN_PERIOD_FRAC = 0.19


def _period_frac(text):
    toks = text.split()
    return (text.count(".") / len(toks)) if toks else 0.0

# A RUNNING HEAD IS IDENTIFIED BY CONTENT, NOT BY TYPE SIZE. This book sets two
# kinds: the verso `73 ספר השרשים`, which IS small type, and the recto root-range
# `בצק - בקר 73`, which is NOT - measured at 0.90-1.08x the page median, i.e.
# indistinguishable from body by height. The first version of this classifier
# used size alone and kept 32 of them, contaminating 30 of 299 entries with page
# furniture: Yad Malachi's item 20 defect class, reproduced on day one of a new
# book. The whole line must match, and it must sit at the top of the page.
RUNNING_HEAD = re.compile(
    r"^\s*(?:\d+\s*)?(?:ספר\s+השרשים|הקדמה|[א-ת]{2,5}\s*[-\u2013]\s*[א-ת]{2,5})\s*(?:\d+)?\s*$")


def page_lines(tokens):
    """Tokens -> lines, each ordered RIGHT TO LEFT.

    Order is rebuilt rather than trusted: this sorts by y then by descending x,
    so the result does not depend on the order DocAI happened to serialise.
    """
    toks = sorted(tokens, key=lambda t: t["y1"])
    lines, cur = [], [toks[0]]
    for t in toks[1:]:
        if abs(t["y1"] - cur[-1]["y1"]) < LINE_TOL:
            cur.append(t)
        else:
            lines.append(cur)
            cur = [t]
    lines.append(cur)
    for ln in lines:
        ln.sort(key=lambda t: -t["x1"])
    return lines


def classify(lines):
    """Label each line body / head / apparatus / watermark.

    Returns [(label, y, height, text, tokens)]. The per-page median is taken over
    FULL-WIDTH lines only (>=6 tokens), so a page whose body is mostly short
    lines cannot drag the threshold down onto itself.
    """
    heights = [statistics.median([t["y2"] - t["y1"] for t in ln])
               for ln in lines if len(ln) >= 6]
    page_median = statistics.median(heights) if heights else 0.019
    rows = []
    for ln in lines:
        h = statistics.median([t["y2"] - t["y1"] for t in ln])
        y = ln[0]["y1"]
        text = " ".join(t["text"] for t in ln)
        rows.append([None, y, h, text, ln, h < SMALL_RATIO * page_median])

    # Bottom-up: the trailing run of small-type lines is the apparatus (plus the
    # catchword, which is also small and sits immediately above it). Stops at the
    # first full-size line, and never climbs above FOOT_MIN_Y.
    for r in reversed(rows):
        label, y, _h, text, _ln, small = r
        if WATERMARK.search(text) or y > 0.94:
            r[0] = "watermark"
            continue
        if y > FOOT_MIN_Y and (
                small or (_h < APPARATUS_MAX_RATIO * page_median
                          and _period_frac(text) >= APPARATUS_MIN_PERIOD_FRAC)):
            r[0] = "apparatus"
            continue
        break

    out = []
    for label, y, h, text, ln, small in rows:
        if label is None:
            if y < HEAD_MAX_Y and (small or RUNNING_HEAD.match(text)):
                label = "head"
            else:
                label = "body"
        out.append((label, y, h, text, ln))
    return out


def build(pages):
    """Body lines of every page in order, as (page, line_text, tokens) triples.

    The TOKENS are carried through because the entry regions the dashboard's scan
    pane needs are the union of an entry's own line boxes - this book has no
    gematria marker, so pipeline/build_klal_page_regions.py (which derives
    regions from marker positions) has nothing to work from here (item 0EQ).""" 
    stream = []
    stats = {"body": 0, "head": 0, "apparatus": 0, "watermark": 0}
    for p in pages:
        path = os.path.join(cio.DOCAI_DIR, f"page_{p}.json")
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            tokens = json.load(fh)
        if not tokens:
            continue
        for label, _y, _h, text, ln in classify(page_lines(tokens)):
            stats[label] += 1
            if label == "body":
                stream.append((p, text, ln))
    return stream, stats


def recover_missed(stream, other_entries, threshold=0.75):
    """Place boundaries DocAI missed, using the PDF text layer's headings.

    DocAI substitutes letters INSIDE the letter name - `נון`->`גון` (נ->ג) on
    p74, `טית`->`מית` (ט->מ) on p107 - so the garbled form is not in the closed
    vocabulary and the heading is invisible to the matcher. Adding each garble as
    a variant is whack-a-mole and erodes the vocabulary that makes the anchor
    safe, so the boundary is taken from the OTHER source instead: the text layer
    read the same heading correctly and knows its page.

    Selection is fuzzy ON PURPOSE and that is within Lesson 5's rule, not against
    it: FUZZY IS NOT A POSITION forbids fuzzy matching for exact-position claims,
    and permits it "to disambiguate among candidates". Here the candidates are
    the ~30 body lines of one known page and the winner must clear `threshold`,
    so the fuzziness chooses between lines rather than locating one.

    Returns {(page, line_text): root} and a log of what fired, with scores, so
    every recovered boundary is auditable rather than silent.
    """
    by_page = {}
    for i, (page, text, _toks) in enumerate(stream):
        by_page.setdefault(page, []).append((i, text))
    # GLOBAL assignment, not greedy per entry. Two roots can sit on one page with
    # near-identical headings - `הבית וההא והלמד` (בהל) and `הבית וההא והטית`
    # (בהט) on p107 differ in one letter - so scoring each entry independently
    # makes them compete for each other's line and a per-entry margin test then
    # rejects BOTH. Scoring every (entry, line) pair once and assigning best-first,
    # each line and each entry used at most once, lets the stronger claim take its
    # line and the weaker one fall to its own.
    pairs = []
    for e in other_entries:
        core = e["heading"].split(".")[0].split(",")[0].strip()
        if len(core) < 8:
            continue
        for i, text in by_page.get(e["page"], []):
            # A line that ALREADY PARSES as a heading belongs to that root and is
            # not available. Without this the assignment handed `גד` the line
            # `הגימל והדלת הכפולה . יגדו על נפש צדיק` at 0.846 - which is גדד, a
            # different root whose heading DocAI read correctly - splitting גדד's
            # entry at the wrong place under the wrong name. High similarity
            # between `הגימל והדלת` and `הגימל והדלת הכפולה` is exactly what one
            # should expect and is not evidence of anything.
            if match_heading(text):
                continue
            r = difflib.SequenceMatcher(None, core, text[:len(core) + 4]).ratio()
            if r >= threshold:
                pairs.append((r, i, e))
    pairs.sort(key=lambda x: -x[0])
    placed, log, used_roots = {}, [], set()
    for r, i, e in pairs:
        if i in placed or e["root"] in used_roots:
            continue
        # Where does the heading END on THIS line? DocAI may leave no terminator
        # at all after a garbled heading - p133 reads `הנימל , והדלת כזרע גר "`
        # with its only period at the line's end, so splitting on the first
        # period gives the whole line as a title and an empty entry. Use the
        # layer heading's own length instead, rounded out to a word boundary.
        core_len = len(e["heading"].split(".")[0].split(",")[0].strip())
        text = stream[i][1]
        cut = text.find(" ", core_len)
        placed[i] = (e["root"], cut if cut > 0 else core_len)
        used_roots.add(e["root"])
        log.append((e["root"], e["page"], round(r, 3), stream[i][1][:44]))
    log.sort(key=lambda x: (x[1], x[0]))
    return placed, log


def segment(stream, forced=None):
    """Split the body stream into entries at each heading line."""
    forced = forced or {}
    entries, cur = [], None
    for idx, (page, text, toks) in enumerate(stream):
        hit = match_heading(text)
        if not hit and idx in forced:
            # boundary supplied by the other OCR source; the heading text itself
            # is DocAI's garbled reading, kept as-is so the record shows what the
            # primary engine actually read.
            hit = forced[idx]
        if hit:
            root, end = hit
            if cur:
                entries.append(cur)
            # Split at the heading's OWN terminator, not at the first period -
            # a comma-terminated heading otherwise takes the entry with it.
            cur = {"root": root, "page": page,
                   "title": text[:end].strip(),
                   "body": [text[end:].strip()],
                   "lines": [(page, toks)]}
        elif cur:
            cur["body"].append(text)
            cur["lines"].append((page, toks))
    if cur:
        entries.append(cur)
    return entries


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pages", required=True, help="PDF page window, e.g. 58-151")
    ap.add_argument("--out", help="write the corpus here (omit for --dry-run)")
    ap.add_argument("--regions", default=None,
                    help="also write klal_page_regions.json here")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--show", type=int, default=2)
    ap.add_argument("--cross-check", metavar="ROOT_ENTRIES_JSON",
                    help="compare against the same book's headings detected from the "
                         "PDF text layer, and FLAG entries the two OCRs disagree about")
    args = ap.parse_args()

    lo, hi = (int(x) for x in args.pages.split("-"))
    stream, stats = build(range(lo, hi + 1))
    forced, rec_log = {}, []
    if args.cross_check:
        with open(os.path.expanduser(args.cross_check), encoding="utf-8") as fh:
            other = [e for e in json.load(fh)["entries"] if lo <= e["page"] <= hi]
        provisional = set()
        for _page, text, _toks in stream:
            hit = match_heading(text)
            if hit:
                provisional.add(hit[0])
        forced, rec_log = recover_missed(stream, [e for e in other
                                                  if e["root"] not in provisional])
    entries = segment(stream, forced)

    print(f"  pages           {lo}-{hi}")
    print(f"  lines kept      {stats['body']} body")
    print(f"  lines dropped   {stats['head']} running head, "
          f"{stats['apparatus']} apparatus, {stats['watermark']} watermark")
    print(f"  entries         {len(entries)}")

    if rec_log:
        print(f"  recovered       {len(rec_log)} boundaries from the text layer "
              f"(DocAI garbled the heading)")
        for root, page, score, text in rec_log:
            print(f"     {root:<5} p{page:<4} similarity {score}  {text}")

    recovered_roots = {r for r, _cut in forced.values()}
    records = []
    for i, e in enumerate(entries, start=1):
        # clean_text INCLUDES THE HEADING, matching this pipeline's existing
        # convention: Yad Malachi's klal 1 stores title "אי תניא תניא." and
        # clean_text "א אי תניא תניא • מדברי רש\"י...", i.e. the marker and title
        # open the text and `title` is a separate copy of that opening.
        #
        # Storing only the body here made every entry heading look like text the
        # scan has and the corpus lacks: build_corrections_dataset.py diffs DocAI
        # page tokens against clean_text, so all 307 headings generated candidate
        # corrections reading `'האלף והבית והסמך' vs None`. That is ~300 spurious
        # questions aimed at a reviewer, from a formatting choice.
        body = " ".join(x for x in e["body"] if x).strip()
        text = (e["title"] + " " + body).strip()
        text = re.sub(r"\s+", " ", text)
        records.append({
            "klal_id": i,
            "gematria": e["root"],
            "section": f"המאמר של {e['root'][0]}",
            "title": e["title"],
            "clean_text": text,
            "page": e["page"],
            **({"boundary_source": "text_layer"} if e["root"] in recovered_roots else {}),
        })

    # CROSS-CHECK against the other OCR's view of the same headings. A heading
    # DocAI missed does not produce a missing entry - it produces a SILENTLY
    # MERGED one, where the next root's text is appended to the previous entry
    # with no boundary. That is a worse defect than an absence and nothing else
    # here would surface it, so the disagreement is recorded ON the affected
    # record rather than only in a report (Lesson 29: a field nobody renders is
    # not a feature - this one is read by the worklist below).
    if args.cross_check:
        with open(os.path.expanduser(args.cross_check), encoding="utf-8") as fh:
            other = json.load(fh)["entries"]
        mine = {r["gematria"] for r in records}
        pages = {r["klal_id"]: r["page"] for r in records}
        missed = [e for e in other
                  if lo <= e["page"] <= hi and e["root"] not in mine]
        by_page = {}
        for e in missed:
            by_page.setdefault(e["page"], []).append(e["root"])
        flagged = 0
        for r in records:
            hit = [root for pg, roots in by_page.items()
                   for root in roots if pg == r["page"]]
            if hit:
                r["suspect_merge"] = sorted(set(hit))
                flagged += 1
        print(f"  cross-check     {len(missed)} headings the text layer found and "
              f"DocAI did not")
        print(f"                  {flagged} entries flagged suspect_merge "
              f"(their text may run past a boundary)")
        if missed:
            print("                  " + " ".join(sorted({e["root"] for e in missed})))

    lens = [len(r["clean_text"]) for r in records]
    if lens:
        print(f"  entry length    median {int(statistics.median(lens))} chars, "
              f"min {min(lens)}, max {max(lens)}")
        empty = sum(1 for l in lens if l < 20)
        print(f"  suspiciously short (<20 chars): {empty}")

    for r in records[:args.show]:
        print(f"\n  --- entry {r['klal_id']}  {r['gematria']}  p{r['page']}")
        print(f"      title: {r['title']}")
        print(f"      text : {r['clean_text'][:150]}")

    if args.regions and not args.dry_run:
        regions = {}
        for i, e in enumerate(entries, start=1):
            by_pg = {}
            for pg, toks in e["lines"]:
                b = by_pg.setdefault(pg, {"x1": 1.0, "y1": 1.0, "x2": 0.0,
                                          "y2": 0.0, "token_count": 0})
                for t in toks:
                    b["x1"] = min(b["x1"], t["x1"]); b["y1"] = min(b["y1"], t["y1"])
                    b["x2"] = max(b["x2"], t["x2"]); b["y2"] = max(b["y2"], t["y2"])
                    b["token_count"] += 1
            pages_in_order = sorted(by_pg)
            if not pages_in_order:
                continue
            def block(pg):
                b = by_pg[pg]
                return {"page": pg,
                        "bbox": {k: b[k] for k in ("x1", "y1", "x2", "y2")},
                        "token_count": b["token_count"]}
            first = block(pages_in_order[0])
            rest = [block(pg) for pg in pages_in_order[1:]]
            if rest:
                first["continuations"] = rest
            regions[str(i)] = first
        with open(args.regions, "w", encoding="utf-8") as fh:
            json.dump(regions, fh, ensure_ascii=False, indent=1)
            fh.flush(); os.fsync(fh.fileno())
        spans = sum(1 for r in regions.values() if r.get("continuations"))
        print(f"  regions         {len(regions)} written ({spans} span a page break)"
              f" -> {args.regions}")

    if args.out and not args.dry_run:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(records, fh, ensure_ascii=False, indent=1)
            fh.flush()
            os.fsync(fh.fileno())
        print(f"\n  wrote {args.out}")

        # KEEP book.json's `parts` IN STEP. The manifest declares the klal range
        # and ~40 call sites derive PART1_MAX_KLAL from it; leaving it stale after
        # a rebuild that changed the entry count makes get_part_num_for_klal()
        # return None for the tail of the corpus, which reads downstream as "that
        # klal does not exist". tests/test_corpus_invariants.py asserts manifest
        # == live corpus for exactly this reason. Derived, not hand-maintained
        # (Lesson 13 THE SECOND COPY OF THE TRUTH).
        manifest = cio.repo_path("book.json")
        if os.path.exists(manifest) and os.path.abspath(args.out) == os.path.abspath(
                cio.repo_path(os.path.basename(args.out))):
            with open(manifest, encoding="utf-8") as fh:
                book = json.load(fh)
            parts = book.get("parts") or []
            name = os.path.basename(args.out)
            entry = next((p for p in parts if p.get("file") == name), None)
            if entry is None:
                parts.append({"file": name, "first_klal": 1, "last_klal": len(records)})
                book["parts"] = parts
            elif entry.get("last_klal") != len(records):
                was = entry.get("last_klal")
                entry["last_klal"] = len(records)
                print(f"  book.json       parts[{name}].last_klal {was} -> {len(records)}")
            with open(manifest, "w", encoding="utf-8") as fh:
                json.dump(book, fh, ensure_ascii=False, indent=2)
                fh.write("\n"); fh.flush(); os.fsync(fh.fileno())
    return 0


if __name__ == "__main__":
    sys.exit(main())
