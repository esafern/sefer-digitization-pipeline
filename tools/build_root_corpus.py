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
import collections
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
import fitz  # noqa: E402
from detect_root_entries import match_heading, root_order_key, ALEPHBET  # noqa: E402

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

# THE APPARATUS CUT, FROM LAYOUT RATHER THAN TYPE SIZE (item 0GF, 2026-09-14).
# On NLI's full-tone crops apparatus type measures 0.80-1.08 of the body median,
# not 0.52-0.80 as on the bitonal scan, so the bottom-up small-type scan below
# stopped at the first larger line and left ~1,370 words of Bacher's apparatus
# in the body - the variant notes (`לא יצמח . נער מוסיף : ...`) always, and on
# p99 the whole citation list, abandoned because its LAST line measured 0.77.
# Two signals, tried in order; type size is consulted by neither:
#   1. A PRINTED RULE - the hairline Bacher sets above the apparatus: a pixel
#      row whose ink is ONE long run (>= RULE_MIN_WIDTH of the page and >=
#      RULE_CONCENTRATION of the row's dark pixels) with paper just above and
#      below. A text baseline also forms long runs, but spread over many
#      letters and never isolated. Found on 49 of 94 pages; every one of seven
#      known body lines kept. It misses rules the eye sees (p69, p95, p104) and
#      is deliberately NOT loosened further (Lesson 31: retuned once already).
#   2. A GAP AND A MARKER - a gap >= GAP_PITCH_RATIO line pitches below
#      FOOT_MIN_Y whose next line STARTS as apparatus starts: a note letter
#      (DocAI reads the superscript alef as `ל`: `ל`, `לא`, `לב`, `לע`, `לבע`,
#      `לעק`) or a citation numeral. A heading after a gap (p91 `האלף והפא`,
#      p102 `והפעולה החמשית`) does not start that way and is passed over; the
#      scan goes on to the next gap. On the 44 pages with no detected rule the
#      first marked gap was apparatus on every one checked.
RULE_MIN_WIDTH = 0.10
RULE_CONCENTRATION = 0.7
GAP_PITCH_RATIO = 1.35
APPARATUS_START = re.compile(r"^\s*(?:\d|ל[א-ת]{0,3}(?:\s|$)|ל\s+b\b)")


def _longest_run(row, gap=2):
    """Longest run of True in a pixel row, bridging holes of up to `gap`."""
    best = cur = holes = 0
    for v in row:
        if v:
            cur += 1 + holes
            holes = 0
        elif cur and holes < gap:
            holes += 1
        else:
            best = max(best, cur)
            cur = holes = 0
    return max(best, cur)


def find_rule_y(doc, page):
    """y (0-1) of the printed rule above the apparatus, or None (APPARATUS CUT)."""
    import numpy as np
    from PIL import Image
    if doc is None or not 0 < page <= doc.page_count:
        return None
    pix = doc.load_page(page - 1).get_pixmap(dpi=150)
    a = np.asarray(Image.frombytes("RGB" if pix.n >= 3 else "L", (pix.width, pix.height),
                                   pix.samples).convert("L"), dtype=np.int16)
    height, width = a.shape
    mask = a < np.percentile(a, 95) - 25       # slightly darker than paper: a hairline is grey
    frac = mask.mean(axis=1)
    for yy in range(int(FOOT_MIN_Y * height), height - 8):
        dark = int(mask[yy].sum())
        if dark < 0.08 * width:
            continue
        run = _longest_run(mask[yy])
        if run < RULE_MIN_WIDTH * width or run < RULE_CONCENTRATION * dark:
            continue
        if frac[yy - 7:yy - 3].max() < 0.03 and frac[yy + 4:yy + 8].max() < 0.03:
            return yy / height
    return None


def gap_cut_index(rows):
    """Index of the first apparatus line by gap + marker, or None (APPARATUS CUT)."""
    ys = [r[1] for r in rows]
    upper = [ys[i] - ys[i - 1] for i in range(1, len(ys)) if ys[i] < FOOT_MIN_Y]
    if not upper:
        return None
    pitch = statistics.median(upper)
    for i in range(1, len(rows)):
        if (ys[i] > FOOT_MIN_Y and ys[i] - ys[i - 1] >= GAP_PITCH_RATIO * pitch
                and APPARATUS_START.match(rows[i][3])):
            return i
    return None


FOOTNOTE_REF = cio.FOOTNOTE_REF    # one copy, in corpus_io (item 0GO)


def footnote_refs(text):
    """Word positions of Bacher's inline reference numerals.

    RECORDED, NOT REMOVED. Sefaria named footnotes explicitly as a demarcation
    requirement, and this pipeline's fidelity rule is that nothing is silently
    deleted from the text - so these are reported as structure and `clean_text`
    is left exactly as it is. What representation they should finally take is a
    decision for the reviewer and for Sefaria, not for the extractor.

    The rule is safe because this book cannot contain a legitimate Arabic
    numeral: 19th-century Hebrew numbers with letters (`יח יז`), and every one
    of the 2,085 standalone numeric tokens in the corpus sits exactly where a
    reference sits - after a biblical quotation, before the commentary on it:

        ולא אבה י"י אלהיך 11 כבר נזכר
        בשאול ואבדו לא תשבענה 10

    They range 1..~50 per page, matching the printed apparatus, with a handful of
    OCR-garbled outliers (624). This does NOT catch the harder half of the same
    problem - a numeral DocAI fused into the preceding word as Hebrew letters
    (`החכם` + superscript 29 + `ג` -> `החכסייג`), which needs the ink; those are
    246 known cases in the witness queue (item 0ES).
    """
    return [i for i, w in enumerate(text.split()) if FOOTNOTE_REF.match(w)]


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


# MERGED ROWS. page_lines() chains a token onto the current line while its top
# is within LINE_TOL of the previous token's, and on pages 58-151 that chain ran
# two printed lines together and interleaved their words (item 0GF):
#   p116, a photograph tilted ~0.75 deg - one line's tops climb 0.012 across the
#     width, and the chain walked off the end of the heading line `הבית והמם .`
#     into the line below, so the root במ merged into its neighbour;
#   p87, where DocAI returned the printed second line with every box starting
#     inside the first and half again as tall (tops 0.6485 against 0.6425,
#     heights 0.0345 against 0.0230) - the heading `האלף והמם והריש ,` never
#     reached the matcher and אמר merged into אמצ.
# Two DIFFERENT words cannot occupy the same stretch of one printed line, so a
# line whose words overlap horizontally is two rows. It is cut at the largest gap
# between its words' centres, measured on the page's deskewed level so a tilted
# pair separates, and the cut stands only if at least STACK_MIN_WORDS clashing
# words sit on EACH side. That guard keeps a printed line whole when DocAI emits
# two readings of one stretch of ink (p74 `אי`/`אין`, p92 `באפיו`/`באפין`, p103
# `חבורותי`/`תי`) or one over-wide token (p72): a clash or two, never a row of
# them. A word emitted twice with the SAME text (p121 `אם`/`אם`) is no clash.
#
# DESKEW IS USED ONLY FOR THAT CUT. Grouping every line on the deskewed level was
# tried first and measured: it fixed p116 and split six lines that had been
# right - a raised numeral (p68 `31`), a line-end word (p95 `והם`), the first
# word of a heading (p103 `הבית`, which loses the root באש). p103's slope is
# only -0.001: the chain's hard threshold turns ANY shift in a token's level
# into a split, so moving every line's level moves some line across it. Cutting
# only lines that are demonstrably two rows leaves every other line as it was.
SKEW_MAX = 0.03           # steepest slope searched, dy per unit x (~1.7 deg)
SKEW_STEP = 0.001
SKEW_BIN = 0.003          # row-sharpness histogram bin, in page heights
STACK_MIN_WORDS = 3


def page_slope(tokens):
    """The page's skew as dy per unit x; 0 for a level page."""
    n = int(round(SKEW_MAX / SKEW_STEP))
    best, best_score = 0.0, -1
    # Ties go to the smaller tilt, so a level page reads as level.
    for s in sorted((k * SKEW_STEP for k in range(-n, n + 1)), key=abs):
        rows = collections.Counter(
            round(((t["y1"] + t["y2"]) / 2 - s * ((t["x1"] + t["x2"]) / 2 - 0.5)) / SKEW_BIN)
            for t in tokens)
        score = sum(v * v for v in rows.values())
        if score > best_score:
            best, best_score = s, score
    return best


def _overlap(a, b):
    return (min(a["x2"], b["x2"]) - max(a["x1"], b["x1"])
            > 0.5 * min(a["x2"] - a["x1"], b["x2"] - b["x1"]))


def _split_merged_rows(line, slope):
    """[line] unchanged, or the printed rows it holds - see MERGED ROWS."""
    words = [t for t in line if len(cio.hebrew_letters_only(t["text"])) >= 2]
    clashes = [(a, b) for i, a in enumerate(words) for b in words[i + 1:]
               if a["text"] != b["text"] and _overlap(a, b)]
    if len(clashes) < STACK_MIN_WORDS:
        return [line]
    mid = lambda t: (t["y1"] + t["y2"]) / 2 - slope * ((t["x1"] + t["x2"]) / 2 - 0.5)
    centres = sorted(mid(t) for t in words)
    _gap, i = max((centres[j + 1] - centres[j], j) for j in range(len(centres) - 1))
    cut = (centres[i] + centres[i + 1]) / 2
    across = [(a, b) for a, b in clashes if (mid(a) < cut) != (mid(b) < cut)]
    upper = {id(t) for pair in across for t in pair if mid(t) < cut}
    lower = {id(t) for pair in across for t in pair if mid(t) >= cut}
    if min(len(upper), len(lower)) < STACK_MIN_WORDS:
        return [line]
    return (_split_merged_rows([t for t in line if mid(t) < cut], slope)
            + _split_merged_rows([t for t in line if mid(t) >= cut], slope))


def page_lines(tokens):
    """Tokens -> lines, each ordered RIGHT TO LEFT.

    Order is rebuilt rather than trusted: this sorts by y then by descending x,
    so the result does not depend on the order DocAI happened to serialise. A
    chained line that holds two printed rows is cut apart (_split_merged_rows).
    Tokens are returned unmodified.
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
    slope = page_slope(tokens)
    lines = [row for ln in lines for row in _split_merged_rows(ln, slope)]
    for ln in lines:
        ln.sort(key=lambda t: -t["x1"])
    return lines


def classify(lines, rule_y=None, stats=None):
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

    # THE LAYOUT CUT FIRST - a printed rule, else a gap plus an apparatus marker
    # (see APPARATUS CUT). Everything from the cut down is apparatus.
    cut = (next((i for i, r in enumerate(rows) if r[1] > rule_y), None)
           if rule_y is not None else gap_cut_index(rows))
    if stats is not None:
        src = "none" if cut is None else ("rule" if rule_y is not None else "gap")
        stats["cut_" + src] = stats.get("cut_" + src, 0) + 1
    head_rows = rows if cut is None else rows[:cut]
    for r in ([] if cut is None else rows[cut:]):
        r[0] = "watermark" if WATERMARK.search(r[3]) else "apparatus"
    # Bottom-up over what is ABOVE the cut: the trailing run of small-type lines is
    # the apparatus (plus the catchword, which is also small and sits immediately
    # above it). Stops at the first full-size line, and never climbs above
    # FOOT_MIN_Y. On a page with no cut this is the whole page, as before.
    for r in reversed(head_rows):
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


# DOUBLED TOKENS. DocAI sometimes returns one word twice over the same ink - two
# tokens, same text, boxes overlapping 0.87-1.0 of the smaller - and both went
# into the text: `אזוב אזוב` (p68), `היאר היאר` (p103), `אם` and `במבצרים`
# (p121), and on p69 a third `האח` beside the page's own `האח האח`. 18 such
# pairs sat in the corpus on pages 58-151 (item 0GG). One is kept. The bar is
# what separates them from p87's second row, whose tokens are REAL words boxed
# onto the line above and overlap their namesakes at 0.72-0.74 (the merged-row
# cut handles those); two DIFFERENT words over one stretch of ink - two readings
# (`אי`/`אין`, p74) - are never touched here, because choosing between them is
# a reading, not a duplicate.
DUP_OVERLAP = 0.8


def _overlap_frac(a, b):
    w = min(a["x2"], b["x2"]) - max(a["x1"], b["x1"])
    h = min(a["y2"], b["y2"]) - max(a["y1"], b["y1"])
    if w <= 0 or h <= 0:
        return 0.0
    area = lambda t: (t["x2"] - t["x1"]) * (t["y2"] - t["y1"])
    return w * h / min(area(a), area(b))


def drop_doubled_tokens(tokens):
    """(kept, dropped): a token is dropped when an earlier one has the same text
    and a box overlapping it by DUP_OVERLAP or more of the smaller."""
    kept, dropped = [], []
    for t in tokens:
        if any(k["text"] == t["text"] and _overlap_frac(k, t) >= DUP_OVERLAP for k in kept):
            dropped.append(t)
        else:
            kept.append(t)
    return kept, dropped


def build(pages):
    """Body lines of every page in order, as (page, line_text, tokens) triples.

    The TOKENS are carried through because the entry regions the dashboard's scan
    pane needs are the union of an entry's own line boxes - this book has no
    gematria marker, so pipeline/build_klal_page_regions.py (which derives
    regions from marker positions) has nothing to work from here (item 0EQ).""" 
    stream = []
    stats = {"body": 0, "head": 0, "apparatus": 0, "watermark": 0,
             "cut_rule": 0, "cut_gap": 0, "cut_none": 0, "doubled": 0}
    # The page IMAGE, for the printed rule: book.json's scan_pdf, the PDF the
    # tokens' coordinates belong to.
    doc = fitz.open(cio.SCAN_PDF_PATH) if os.path.exists(cio.SCAN_PDF_PATH) else None
    for p in pages:
        path = os.path.join(cio.DOCAI_DIR, f"page_{p}.json")
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            tokens = json.load(fh)
        if not tokens:
            continue
        tokens, doubled = drop_doubled_tokens(tokens)
        stats["doubled"] += len(doubled)
        rule_y = find_rule_y(doc, p)
        for label, _y, _h, text, ln in classify(page_lines(tokens), rule_y=rule_y,
                                                stats=stats):
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


# FALSE HEADINGS (item 0GM). A line can parse as a heading and still be prose:
# PDF p61 wraps `...ואחד מהם אגם בקבוץ / האלף והגימל. אבל זה הוא`, a vowel
# description, and the wrapped half became entry 16 (`אג`). A parsed heading is
# refused only when two signals agree (Lesson 9): its root breaks the book's
# order (root_order_key), AND the line is flush where a heading is indented.
# Measured over the 318 headings of pages 58-151: heading indent median 0.082
# of the page width, body lines 0.002, this line 0.0007. The indent is taken
# from the first word with a Hebrew letter, because a footnote numeral set out
# in the margin (p109 `88 הבית והזין הכפולה`) makes a real heading look flush.
HEADING_INDENT_MIN = 0.02
COLUMN_EDGE_PCTL = 0.9    # the body column's right edge: most lines reach it


def _column_right(stream):
    """{page: right edge of the body column}, from its lines' right edges."""
    edges = {}
    for page, _text, toks in stream:
        if toks:
            edges.setdefault(page, []).append(max(t["x2"] for t in toks))
    return {p: sorted(v)[int(COLUMN_EDGE_PCTL * (len(v) - 1))] for p, v in edges.items()}


def _indent(toks, col_right):
    """How far the line's first Hebrew word stands in from the column edge."""
    first = next((t for t in toks if cio.hebrew_letters_only(t["text"])), None)
    return col_right - first["x2"] if first else 0.0


def segment(stream, forced=None, rejected=None):
    """Split the body stream into entries at each heading line.

    A parsed heading whose root breaks the book's order on a flush line is kept
    as text and, when `rejected` is a list, recorded there as (page, root, text).
    """
    forced = forced or {}
    col = _column_right(stream)
    entries, cur = [], None
    for idx, (page, text, toks) in enumerate(stream):
        hit = match_heading(text)
        if (hit and cur and idx not in forced
                and root_order_key(hit[0]) < root_order_key(cur["root"])
                and _indent(toks, col.get(page, 1.0)) < HEADING_INDENT_MIN):
            if rejected is not None:
                rejected.append((page, hit[0], text[:44]))
            hit = None
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
    false_heads = []
    entries = segment(stream, forced, rejected=false_heads)

    print(f"  pages           {lo}-{hi}")
    print(f"  lines kept      {stats['body']} body")
    print(f"  lines dropped   {stats['head']} running head, "
          f"{stats['apparatus']} apparatus, {stats['watermark']} watermark")
    print(f"  apparatus cut   {stats['cut_rule']} pages by printed rule, "
          f"{stats['cut_gap']} by gap + marker, {stats['cut_none']} none")
    print(f"  doubled tokens  {stats['doubled']} dropped (DocAI returned one word twice "
          f"over the same ink)")
    print(f"  entries         {len(entries)}")
    print(f"  false headings  {len(false_heads)} kept as text (root out of the book's "
          f"order, on a flush line - item 0GM)")
    for page, root, text in false_heads:
        print(f"     {root:<5} p{page:<4} {text}")

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
            "footnote_refs": footnote_refs(text),
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
        # A heading refused above as prose was refused on two signals, and the
        # text layer parsing the same wrapped line is the same prose, not a third
        # opinion: counting it as missed flagged all 7 entries on p61 (item 0GM).
        refused = {(page, root) for page, root, _text in false_heads}
        missed = [e for e in other
                  if lo <= e["page"] <= hi and e["root"] not in mine
                  and (e["page"], e["root"]) not in refused]
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

    nrefs = sum(len(r["footnote_refs"]) for r in records)
    with_refs = sum(1 for r in records if r["footnote_refs"])
    print(f"  footnote refs   {nrefs} inline reference numerals recorded across "
          f"{with_refs} entries (text unchanged)")

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
        # THROUGH save_part1, the corpus's one serializer (item 0IG). This wrote
        # its own `indent=1`, so Sefer HaShorashim's part1.json was committed in a
        # format no other corpus writer produces, and the first apply on it
        # re-indented every one of its 5,934 lines - an 11,864-line diff for a
        # one-word ruling (Lesson 13, THE SECOND COPY OF THE TRUTH).
        cio.save_part1(records, path=args.out)
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
