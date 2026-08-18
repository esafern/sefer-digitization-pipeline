"""[PRODUCTION] Build a `gematria_trace`-shaped JSON for a section of a
printed Hebrew work: for every klal, where its marginal numeral marker
actually sits on the scan (page + index into that page's DocAI token array),
and whether the text following that marker agrees with the text the corpus
stores for that klal.

WHY THIS EXISTS. `gematria_trace_part1.json` is tracked, load-bearing
(`build_klal_page_regions.py` anchors every region on it,
`check_klal_token_orphans.py` reads it, `build_corrections_dataset.py`
depends on the page attribution it feeds), and hand-corrected in a dozen
places - but NOTHING regenerated it. Whatever produced it originally is lost
or archived, so Parts 2 and 3 have had no scan linkage of any kind (their
stored `page` field is confirmed wrong - part2.json's klal 223 claims page
30, which is Part 1 content). This script is the missing generator.

GENERIC BY CONSTRUCTION, per CLAUDE.md's reusable-pipeline directive
(2026-08-17). Nothing below is specific to Yad Malachi or to any part
number: the caller supplies the corpus file(s), the DocAI token directory,
the page range, and - if the next work's print has different margins - the
marker x-band. The only knowledge baked in is the SHAPE of the problem
(a numeral marker in a margin, followed by the klal's opening words), which
is the thing worth reusing.

    python3 pipeline/build_gematria_trace.py \
        --part part2.json:gematria_trace_part2.json \
        --part part3.json:gematria_trace_part3.json \
        --pages 76-249

Multiple --part pairs are traced as ONE continuous klal sequence sharing one
monotonic cursor (Parts 1/2/3 are editorial divisions of a single continuous
printed sequence - see PROJECT-STATUS.md 2026-08-17), then split back out to
one trace file per source. A single --part works for a self-contained
section.

--- FOUR FAILURE MODES THIS IS DESIGNED AROUND, each backed by a real,
    already-confirmed instance in this corpus, not a hypothetical ---

1. MARKERS SIT OUT OF READING ORDER IN THE RAW TOKEN ARRAY. A marker glyph
   lives in the right-hand margin and routinely gets array-indexed among the
   PREVIOUS line's tokens despite sitting visually below them. Confirmed
   three separate times (klal 3/4, klal 17/18, klal 65/66 - the latter two
   were real DATA issues in part1.json found by this artifact). So this
   script never uses array order for anything: `reading_order()` re-derives
   visual order by clustering tokens into lines on bbox-CENTER Y (not y1 - a
   marker and the taller bold word beside it on the same line do not share a
   y1; confirmed 0.007 apart on klal 3/4) and sorting each line right-to-
   left. `marker_position` in the output is still the ARRAY index, because
   that is what every existing consumer indexes with.

2. THE MARKER GLYPH ITSELF IS MISREAD. Measured over the 206 confirmed
   marker positions in gematria_trace_part1.json: 13 of them (6.3%) hold a
   token whose text is NOT the expected numeral. Every one is a single-letter
   confusion, and the confusions are not arbitrary - see CONFUSION_PAIRS,
   which is derived from those 13 measured cases rather than guessed. Exact
   matching alone would therefore silently lose ~6% of markers, which is
   most of what the old trace's twelve `marker_not_found_in_window` entries
   are.

3. A FIXED-WIDTH LOOKAHEAD WINDOW SILENTLY FAILS. klal 198 sat as
   `marker_not_found_in_window` in the tracked trace until 2026-08-17, when
   a manual search found it correctly read, one full page past wherever the
   original window stopped. There is no lookahead window here: the search
   runs from the monotonic cursor to the last page of the range. Cost is
   irrelevant (this runs once per section); being wrong is not.

4. A WRONG `ok` IS WORSE THAN AN HONEST FLAG. The output of this script is
   the input to a later klal-BOUNDARY verification pass, and Parts 2-3 are
   already known to carry page-furniture contamination in ~17% of their
   klalim. So every tier below "exact numeral, right margin, opening words
   agree" is either flagged or sent to vision - never quietly upgraded.

--- HOW A MARKER IS ACCEPTED ---

Three independent signals, in the spirit of CLAUDE.md Lesson 9 (never trust
one confident-sounding signal):

  POSITION   the token's bbox must lie in the marker x-band. Derived
             empirically, not guessed: across all 206 confirmed Part-1
             markers, x1 spans [0.818, 0.892] and x2 spans [0.851, 0.908].
             MARKER_X_BAND widens that by ~0.02 on each side. This band is
             what rejects a same-numeral collision in running text - the
             exact false positive that put klal 3's marker at the `ג` inside
             the citation "בפרק ג'" until it was hand-corrected in 2026-08-05.

  TEXT       exact expected numeral, else a single documented-confusion
             substitution (CONFUSION_PAIRS), else the corpus's own stored
             `gematria` string if it differs from the canonical spelling
             (part2/part3 store non-final forms - רנ where the canonical
             numeral and the print both use רן).

  CONTENT    the next CONTENT_WORDS tokens in reading order, compared
             against the klal's own stored opening AND its stored title,
             whichever agrees better. Both are legitimate printed openings:
             220 of 222 Part-1 klalim open with their own title, but where a
             group of klalim shares one printed heading (klal 65/66/67) the
             corpus repeats the shared heading in each `clean_text` while the
             print shows the klal's own distinctive line, and only the title
             comparison recovers that.

  Thresholds are measured, not picked. Scoring all 206 confirmed Part-1
  markers this way: the minimum is 0.75 for 205 of them, and the single
  outlier is klal 34 at 0.375 - a klal whose surrounding OCR is so garbled
  that CLAUDE.md Lesson 15 names it by number as structurally unalignable.
  OK_RATIO is set at 0.5, comfortably below the observed floor of genuine
  markers and far above a coincidental collision (which scores ~0).
  VISION_RATIO_FLOOR at 0.15 is the bottom of the band where a real but
  badly-OCR'd marker like klal 34 still lives.
"""
import argparse
import difflib
import hashlib
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pipeline"))

import corpus_io as cio  # noqa: E402


# ---------------------------------------------------------------- geometry --

# Tokens whose bbox CENTERS fall within this much of each other in Y are one
# printed line. This print runs ~49-57 lines to the page, i.e. ~0.018 of page
# height per line, so 0.008 separates lines with margin while still gathering
# a marker and the tall bold word beside it (measured 0.007 apart at y1, much
# closer at center) onto the same line.
LINE_TOL = 0.008

# (min x1, max x2) a marker glyph's bbox must fall inside. Measured across all
# 206 confirmed marker positions in gematria_trace_part1.json: x1 in
# [0.818, 0.892], x2 in [0.851, 0.908]. Widened ~0.02 each way so a slightly
# differently-registered page is not silently dropped, while still excluding
# running text (this band holds ~5% of a page's tokens - essentially the
# line-initial word of each line - and combining it with an exact numeral
# match is what makes it selective).
#
# A different print will need a different band; that is why it is a parameter
# everywhere below and a --x-band CLI flag, and why --report-x-band prints the
# observed distribution of whatever this run accepted, so the next text can
# calibrate from its own data instead of inheriting this one's margins.
MARKER_X_BAND = (0.80, 0.93)

# Words compared after the marker. 8 is what the original (lost) trace used -
# every content_match_ratio in gematria_trace_part1.json is a multiple of
# 0.125 - and re-scoring the confirmed markers at 8 reproduces a clean
# separation, so there is no reason to move it.
CONTENT_WORDS = 8

# See the module docstring's "Thresholds are measured, not picked."
OK_RATIO = 0.5
VISION_RATIO_FLOOR = 0.15

# Tier 2 (content-anchored recovery) asks nothing of the numeral at all, so it
# has to ask more of the content: 0.75 is 6 of CONTENT_WORDS opening words
# agreeing. Measured against the Part-1 klalim tiers 0-1 could not place:
# klal 16/22/63 anchor at 1.00, klal 50 at 0.88, klal 182 at 0.75, while
# klal 10/57 - the two whose markers DocAI genuinely did not emit at all -
# have no marker-band token before their anchor and are correctly left
# unplaced by the position half of the test rather than by this threshold.
CONTENT_ANCHOR_RATIO = 0.75

# Fewer usable opening words than this and the content signal is not weak,
# it is absent - see has_comparable_opening(). Half of CONTENT_WORDS.
MIN_COMPARABLE_WORDS = 4

# A printed klal numeral in this work is at most 4 letters (תרסז = 667). The
# guard matters because tier 2 accepts whatever token precedes the anchored
# opening: without it, an ordinary line-initial word (which shares the
# marker's x-band, since RTL lines start at the right) could be recorded as a
# marker.
MAX_MARKER_LETTERS = 4
# Two candidates this close together, both otherwise acceptable, are not
# distinguishable by content score alone - send them to vision rather than
# taking the first. 0.125 is exactly one word out of CONTENT_WORDS.
AMBIGUITY_MARGIN = 0.125

# How far ahead of the cursor a candidate may sit and still be accepted on
# POSITION ALONE (right numeral, right margin, but the following words do not
# agree with what the corpus stores).
#
# This bound is not optional tidiness - the first version of this script had
# no bound and it destroyed the run. klal 10's marker genuinely is not in
# DocAI's tokens for its page; the unbounded search found an unrelated `י` in
# the right margin 37 pages later, scored it 0.0, accepted it on position
# alone and moved the monotonic cursor there - after which 201 of 222 klalim
# reported `marker_not_found_in_window` because the cursor had jumped past
# them. That is CLAUDE.md Lesson 6's cascading-position failure, reproduced
# exactly.
#
# A candidate whose CONTENT agrees (ratio >= ok_ratio) is exempt from this
# bound: content agreement is independent evidence, and forbidding a distant
# jump on strong evidence would re-create failure mode 3 (klal 198's real
# marker sat a full page past where the old trace looked). The bound applies
# only where position is the ONLY evidence.
#
# 2 pages, plus one further page of slack for every consecutive klal already
# unplaced: this print runs ~3.5 klalim to the page, so a klal whose
# predecessors were all found sits within a page or two of the cursor, while
# a run of n unplaced klalim can legitimately have carried the text n/3.5
# pages further on. One page per unplaced klal is deliberately generous in
# the direction of looking, since the alternative failure (not looking far
# enough) is the one this corpus has actually suffered.
UNSUPPORTED_MAX_PAGE_GAP = 2


# ------------------------------------------------------------ glyph confusion --

# Single-letter substitutions DocAI is measurably prone to in this typeface.
# Derived from data, in three groups, each traceable:
#
#   (a) The 13 confirmed Part-1 markers whose stored token text differs from
#       the expected numeral: ז->ו six times (klal 107/147/167/187/197/217),
#       ז->ן three times (klal 116/127/216), ד->ו once (klal 34), ד->ר once
#       (klal 124). Written here as unordered pairs because the substitution
#       runs both directions (what is printed vs. what DocAI emitted).
#   (b) Confusions this project has separately confirmed by scan crop in body
#       text: ר/ה (klal 167 w877, דרוא -> דהוא, 2026-08-17) and ד/ה (the same
#       investigation's neighbouring candidates).
#   (c) Final/non-final forms of the same letter. Not an OCR error at all but
#       a real orthographic variation between the print, the canonical
#       numeral spelling, and what the corpus stores (part2/part3 store רנ
#       where klal_id_to_gematria and the print both give רן).
#
# Deliberately NOT a general edit-distance-1 search: an unbounded fuzzy retry
# over a 27-letter alphabet turns a precise anchor into a guess, which is
# exactly the failure CLAUDE.md Lesson 5 warns about. Adding a pair here
# should mean someone measured it.
# Gematria-marker confusions — letters commonly misread in marginal Hebrew
# numeral position (empirically derived from the 13 misread markers across
# gematria_trace_part1.json's 206 confirmed positions). Adding a pair here
# should mean someone measured it. See also tools/detect_real_word_substitution.py's
# CONFUSION_PAIRS for a related but distinct set covering content-word-level
# letter confusions (frozenset keyed, different scope).
CONFUSION_PAIRS = (
    ("ז", "ו"), ("ז", "ן"), ("ו", "ן"),          # (a) + the third edge implied by them
    ("ד", "ו"), ("ד", "ר"),                       # (a)
    ("ר", "ה"), ("ד", "ה"),                       # (b)
    ("נ", "ן"), ("פ", "ף"), ("צ", "ץ"),          # (c)
    ("כ", "ך"), ("מ", "ם"),                       # (c)
)


def confusion_map(pairs=CONFUSION_PAIRS):
    """letter -> set of letters it is measurably confusable with."""
    m = {}
    for a, b in pairs:
        m.setdefault(a, set()).add(b)
        m.setdefault(b, set()).add(a)
    return m


def near_miss_variants(gematria, pairs=CONFUSION_PAIRS):
    """Every string one documented confusion-substitution away from
    `gematria`, in a stable order, excluding `gematria` itself."""
    m = confusion_map(pairs)
    out = []
    seen = {gematria}
    for i, ch in enumerate(gematria):
        for alt in sorted(m.get(ch, ())):
            v = gematria[:i] + alt + gematria[i + 1:]
            if v not in seen:
                seen.add(v)
                out.append(v)
    return out


# ------------------------------------------------------------ reading order --

center_y = cio.center_y


def reading_order(tokens, line_tol=LINE_TOL):
    """Array indices of `tokens` in VISUAL reading order: lines top to
    bottom, each line right to left (RTL).

    This is the whole defence against failure mode 1. Clustering is on bbox
    CENTER Y and greedy against the previous token in the cluster, so a line
    whose glyph heights vary (a bold opening word beside a small marginal
    numeral) still gathers into one line.
    """
    idx = sorted(range(len(tokens)), key=lambda i: center_y(tokens[i]))
    lines, cur = [], []
    for i in idx:
        if cur and center_y(tokens[i]) - center_y(tokens[cur[-1]]) <= line_tol:
            cur.append(i)
            continue
        if cur:
            lines.append(cur)
        cur = [i]
    if cur:
        lines.append(cur)
    out = []
    for line in lines:
        out.extend(sorted(line, key=lambda i: -tokens[i]["x2"]))
    return out


def in_marker_band(tok, x_band=MARKER_X_BAND):
    return tok["x1"] >= x_band[0] and tok["x2"] <= x_band[1]


# ---------------------------------------------------------- content matching --

def following_words(tokens, order, rank, n=CONTENT_WORDS):
    """The next `n` Hebrew-bearing tokens after reading-order position
    `rank`, normalized. Punctuation-only tokens are skipped rather than
    counted - they carry no comparison signal and this print emits a lot of
    them."""
    got = []
    for r in range(rank + 1, len(order)):
        w = cio.hebrew_letters_only(tokens[order[r]]["text"])
        if not w:
            continue
        got.append(w)
        if len(got) >= n:
            break
    return got


def opening_forms(klal, n=CONTENT_WORDS):
    """The printed openings this klal could legitimately show, as
    (label, normalized words) pairs - see the module docstring's CONTENT
    signal for why the title is a second legitimate form and not a fallback
    hack."""
    forms = []
    # clean_text's first word is the klal's own numeral (221 of 222 Part-1
    # klalim, 222/222 and 223/223 in Parts 2/3), i.e. the marker itself -
    # drop it, we are comparing what comes AFTER the marker.
    body = klal.get("clean_text", "").split()[1:]
    forms.append(("clean_text", body))
    if klal.get("title"):
        forms.append(("title", klal["title"].split()))
    out = []
    for label, words in forms:
        norm = [w for w in (cio.hebrew_letters_only(x) for x in words) if w][:n]
        if norm:
            out.append((label, norm))
    return out


def has_comparable_opening(klal, n=CONTENT_WORDS, min_words=MIN_COMPARABLE_WORDS):
    """False when the corpus stores no usable opening for this klal, so the
    content signal cannot decide anything - not "the content disagrees", but
    "there is nothing to compare".

    This is not a Yad-Malachi special case dressed up as a general rule; it
    is the general rule, and this corpus happens to exercise it hard. 115 of
    the 445 Parts 2-3 klalim (70 in Part 2, 45 in Part 3, none in Part 1)
    store `clean_text` as literally "<numeral> כלל <klal_id>" with the title
    "כלל <klal_id>" - placeholders for text that was never extracted. That
    figure and the full id list are already documented in
    PROJECT-STATUS-HISTORY.md; it is quantified here only because it is what
    a content-driven tracer runs into first.

    Without this test those klalim look identical to a klal whose stored text
    genuinely contradicts the scan, which is a completely different finding.
    """
    return any(len(words) >= min_words for _, words in opening_forms(klal, n))


def content_match(got, klal, n=CONTENT_WORDS):
    """(ratio, which_form) for the best-agreeing legitimate opening, or
    (0.0, None) if nothing to compare. difflib on WORD lists, not characters:
    the question is "are these the same opening words", and a character-level
    ratio would reward incidental letter overlap between unrelated Hebrew."""
    best, which = 0.0, None
    for label, want in opening_forms(klal, n):
        if not got:
            continue
        r = difflib.SequenceMatcher(None, got, want, autojunk=False).ratio()
        if r > best:
            best, which = r, label
    return best, which


# ------------------------------------------------------------- the search ----

class Candidate:
    __slots__ = ("page", "rank", "index", "text", "tier", "seq", "ratio", "which_form")

    def __init__(self, page, rank, index, text, tier, seq=0):
        self.page = page
        self.rank = rank
        self.index = index
        self.text = text
        self.tier = tier              # 0 = exact numeral, 1 = near-miss variant
        # Document-order position among this klal's candidates. `rank` alone
        # cannot order candidates ACROSS pages (every page restarts at 0), and
        # sorting by (page, rank) in three places is one place too many to get
        # wrong.
        self.seq = seq
        self.ratio = 0.0
        self.which_form = None

    def __repr__(self):  # pragma: no cover - debugging aid only
        return (f"Candidate(page={self.page}, index={self.index}, text={self.text!r}, "
                f"tier={self.tier}, ratio={self.ratio:.3f})")


def wanted_forms(klal_id, klal, pairs=CONFUSION_PAIRS):
    """(exact_forms, near_forms) - the numeral spellings worth searching for,
    split by how much weight a hit deserves.

    Exact tier: the canonical numeral, plus the corpus's own stored spelling
    when it differs (Parts 2/3 store non-final forms; the print uses final
    forms - a stored-spelling hit is still an exact glyph match on the page,
    just against a different transliteration convention, so it does not
    deserve the weaker near-miss treatment).
    """
    expected = cio.klal_id_to_gematria(klal_id)
    exact = [expected]
    stored = cio.hebrew_letters_only(klal.get("gematria", "") or "")
    if stored and stored != expected:
        exact.append(stored)
    near = [v for v in near_miss_variants(expected, pairs) if v not in exact]
    return exact, near


def scan_page(tokens, order, start_rank, exact_forms, near_forms, page, x_band):
    """Every marker-band token on this page at or after `start_rank` whose
    normalized text is one of the wanted spellings, in reading order."""
    exact_set = set(exact_forms)
    near_set = set(near_forms)
    found = []
    for rank in range(start_rank, len(order)):
        i = order[rank]
        tok = tokens[i]
        if not in_marker_band(tok, x_band):
            continue
        text = cio.hebrew_letters_only(tok["text"])
        if text in exact_set:
            found.append(Candidate(page, rank, i, text, 0))
        elif text in near_set:
            found.append(Candidate(page, rank, i, text, 1))
    return found


def collect_candidates(klal_id, klal, cursor, page_end, page_loader, order_cache,
                       x_band=MARKER_X_BAND, pairs=CONFUSION_PAIRS,
                       content_words=CONTENT_WORDS):
    """All candidates from the cursor forward to `page_end`, scored.

    `cursor` is (page, rank) - the reading-order position of the last
    CONFIRMED marker. Never searches behind it (failure mode 3's monotonic
    half) and never stops early (failure mode 3's unbounded half).
    """
    exact_forms, near_forms = wanted_forms(klal_id, klal, pairs)
    cursor_page, cursor_rank = cursor
    out = []
    for page in range(cursor_page, page_end + 1):
        tokens = page_loader(page)
        if not tokens:
            continue
        if page not in order_cache:
            order_cache[page] = reading_order(tokens)
        order = order_cache[page]
        start = cursor_rank + 1 if page == cursor_page else 0
        for cand in scan_page(tokens, order, start, exact_forms, near_forms, page, x_band):
            cand.ratio, cand.which_form = content_match(
                following_words(tokens, order, cand.rank, content_words), klal, content_words)
            cand.seq = len(out)
            out.append(cand)
    return out, exact_forms, near_forms


def content_anchored_candidates(klal, cursor, near_limit, page_loader, order_cache,
                                x_band=MARKER_X_BAND, content_words=CONTENT_WORDS,
                                anchor_ratio=CONTENT_ANCHOR_RATIO,
                                max_marker_letters=MAX_MARKER_LETTERS):
    """TIER 2 - find the marker by anchoring on the klal's OPENING WORDS and
    taking whatever token sits in the margin immediately before them.

    Tiers 0 and 1 both start from "what should the numeral look like", so both
    are blind to a marker DocAI misread in a way nobody has catalogued.
    Measured on Part 1: of the 8 klalim tiers 0-1 leave unplaced, 5 have a
    perfectly real marker token sitting in the margin, misread as `פז` for
    `טז` (klal 16), `כך` for `כב` (22), `ג` for `נ` (50), `סוג` for `סג` (63,
    a spurious inserted letter rather than a substitution at all) and `קפכ`
    for `קפב` (182). Widening the substitution catalogue to cover those would
    be exactly the unbounded fuzzy numeral search CLAUDE.md Lesson 5 warns
    against, and would weaken every other klal's anchor to rescue five.

    Anchoring the other way round costs nothing in precision: the numeral is
    not consulted, but two independent signals still have to agree (CLAUDE.md
    Lesson 9) - the opening words must match at `anchor_ratio` (a higher bar
    than tiers 0-1 use, since the glyph contributes no evidence here), AND the
    token immediately before them must be a short token inside the marker
    x-band. The two klalim whose markers DocAI truly did not emit (10 and 57)
    fail the second test and stay unplaced, which is the correct answer.

    Searched only from the cursor to `near_limit`: a missing marker is a
    local problem, and the sliding window here is far more expensive than the
    exact-token scan.
    """
    want = None
    for _label, words in opening_forms(klal, content_words):
        want = words
        break
    if not want:
        return []
    cursor_page, cursor_rank = cursor
    out = []
    for page in range(cursor_page, near_limit + 1):
        tokens = page_loader(page)
        if not tokens:
            continue
        if page not in order_cache:
            order_cache[page] = reading_order(tokens)
        order = order_cache[page]
        start = cursor_rank + 1 if page == cursor_page else 0
        # (reading rank, normalized text) for content-bearing tokens only, so
        # the sliding window compares words to words.
        stream = [(r, cio.hebrew_letters_only(tokens[order[r]]["text"]))
                  for r in range(start, len(order))]
        stream = [(r, w) for r, w in stream if w]
        for i in range(len(stream)):
            seg = [w for _, w in stream[i:i + content_words]]
            if len(seg) < content_words:
                break
            # The window must start ON the opening's first word, not merely
            # overlap the opening. Without this pin, a window starting ONE
            # word late still scores 7/8 = 0.875 - and its "preceding token"
            # is then the opening's own first word, which (being line-initial
            # in an RTL column) sits in the marker x-band and is often short
            # enough to pass for a numeral. Found 2026-08-17 by the two tests
            # named for it: the rule recorded אין, the first word of klal 10's
            # own text, as klal 10's marker, and recorded klal 65's marker as
            # klal 66's.
            if seg[0] != want[0]:
                continue
            ratio = difflib.SequenceMatcher(None, seg, want, autojunk=False).ratio()
            if ratio < anchor_ratio:
                continue
            anchor_rank = stream[i][0]
            # The marker is the token immediately before the opening in
            # READING order - including punctuation, which is skipped in
            # `stream` but is a real token on the page.
            marker_rank = anchor_rank - 1
            if marker_rank < 0 or (page == cursor_page and marker_rank <= cursor_rank):
                continue
            tok = tokens[order[marker_rank]]
            text = cio.hebrew_letters_only(tok["text"])
            if not text or len(text) > max_marker_letters:
                continue
            if not in_marker_band(tok, x_band):
                continue
            cand = Candidate(page, marker_rank, order[marker_rank], text, 2)
            cand.ratio, cand.which_form = ratio, "anchor"
            out.append(cand)
    return out


def pick(candidates, tier, ok_ratio=OK_RATIO):
    """(best, clearing) for one tier: the EARLIEST candidate that clears
    `ok_ratio` (and the full list of clearing candidates, for ambiguity
    checking), else the highest-scoring one with document order as tie-break.

    Earliest-clearing rather than globally-best on purpose. The text is
    sequential and the cursor is monotonic, so taking a later, marginally
    better-scoring hit over an earlier convincing one would step over content
    that belongs to this klal and desynchronize everything after it -
    CLAUDE.md Lesson 6's cascading-position failure.
    """
    tiered = [c for c in candidates if c.tier == tier]
    if not tiered:
        return None, []
    clearing = [c for c in tiered if c.ratio >= ok_ratio]
    if clearing:
        return clearing[0], clearing
    return max(tiered, key=lambda c: (c.ratio, -c.seq)), []


def resolve_klal(klal_id, klal, cursor, page_end, page_loader, order_cache,
                 x_band=MARKER_X_BAND, pairs=CONFUSION_PAIRS,
                 content_words=CONTENT_WORDS, ok_ratio=OK_RATIO,
                 vision_floor=VISION_RATIO_FLOOR, ambiguity_margin=AMBIGUITY_MARGIN,
                 vision_confirm=None, unplaced_run=0,
                 unsupported_max_page_gap=UNSUPPORTED_MAX_PAGE_GAP):
    """Decide this klal's marker. Returns (record, new_cursor_or_None).

    `vision_confirm(klal, candidate, page_tokens)` is injected rather than
    imported so the decision logic here stays pure and testable with no API
    key, no network and no PDF - the same separation tests/test_pipeline_
    logic.py already relies on elsewhere. It returns True (confirmed),
    False (denied) or None (could not tell / not available).

    `unplaced_run` is how many consecutive klalim before this one could not be
    placed, which widens how far a position-only candidate may sit from the
    cursor - see UNSUPPORTED_MAX_PAGE_GAP.
    """
    expected = cio.klal_id_to_gematria(klal_id)
    stored = klal.get("gematria")
    base = {
        "klal_id": klal_id,
        "expected_gematria": expected,
        "stored_gematria": stored,
    }

    candidates, exact_forms, near_forms = collect_candidates(
        klal_id, klal, cursor, page_end, page_loader, order_cache,
        x_band, pairs, content_words)

    # Candidates beyond this page may only be accepted on CONTENT agreement,
    # never on position alone. See UNSUPPORTED_MAX_PAGE_GAP.
    near_limit = cursor[0] + unsupported_max_page_gap + unplaced_run
    near = [c for c in candidates if c.page <= near_limit]

    notes = []
    chosen, tier_label = None, None

    # --- the corpus stores no text for this klal ----------------------------
    # Every tier below weighs the numeral against the stored opening, and here
    # there is no stored opening to weigh it against. Falling through would
    # report `marker_not_found_in_window` for a marker sitting in plain sight,
    # which is the opposite of useful to the pass that has to reconstruct
    # these klalim's text from the scan. Located on the three signals that do
    # still exist - exact numeral, marker x-band, position after the cursor -
    # and NEVER promoted past marker_found_content_mismatch, because the one
    # thing "ok" asserts is exactly the thing that cannot be checked here.
    if not has_comparable_opening(klal, content_words):
        positional = [c for c in near if c.tier == 0]
        how = "exact numeral"
        if not positional and vision_confirm:
            # A MISREAD numeral plus a margin position is two signals, not
            # three - not enough on its own. Vision supplies the third by
            # reading the glyph directly, so this branch exists only when a
            # vision adjudicator is available.
            for cand in [c for c in near if c.tier == 1]:
                if vision_confirm(klal, cand, page_loader(cand.page)) is True:
                    positional, how = [cand], f"numeral read as {cand.text!r}, confirmed by vision crop"
                    break
        if positional:
            cand = positional[0]
            record = {
                **base,
                "page": cand.page,
                "content_match_ratio": None,
                "marker_position": cand.index,
                "status": "marker_found_content_mismatch",
            }
            record["note"] = (
                f"positional-only ({how}) at page {cand.page} token {cand.index}: the corpus "
                f"stores no text for this klal (placeholder clean_text), so the marker was "
                f"located by numeral, marker x-band and sequence alone and the stored text "
                f"could not be checked at all - this is NOT a content disagreement")
            return record, (cand.page, cand.rank)
        record = {
            **base,
            "page": cursor[0],
            "content_match_ratio": None,
            "status": "marker_not_found_in_window",
        }
        record["note"] = (
            f"the corpus stores no text for this klal (placeholder clean_text), and no "
            f"exact {expected!r} in the marker x-band was found between the cursor and page "
            f"{near_limit} - with no stored opening there is no second signal to fall back on")
        return record, None

    # --- tier 0, full content agreement: accepted anywhere in the range -----
    exact_best, exact_clearing = pick(candidates, 0, ok_ratio)
    if exact_best is not None and exact_best.ratio >= ok_ratio:
        chosen, tier_label = exact_best, "mechanical-exact"
        rivals = [c for c in exact_clearing
                  if c is not exact_best and abs(c.ratio - exact_best.ratio) <= ambiguity_margin]
        if rivals:
            pages = sorted({c.page for c in [exact_best] + rivals})
            if vision_confirm:
                notes.append(f"{len(rivals) + 1} exact candidates within {ambiguity_margin} "
                             f"of each other (pages {pages}); sent to vision to disambiguate")
                for cand in [exact_best] + rivals:
                    if vision_confirm(klal, cand, page_loader(cand.page)) is True:
                        chosen, tier_label = cand, "vision-assisted"
                        break
            else:
                notes.append(f"{len(rivals) + 1} exact candidates within {ambiguity_margin} "
                             f"of each other (pages {pages}); NOT disambiguated - no vision "
                             "adjudicator available, earliest taken")

    # --- tier 1, full content agreement: also accepted anywhere -------------
    if chosen is None:
        near_best_any, _ = pick(candidates, 1, ok_ratio)
        if near_best_any is not None and near_best_any.ratio >= ok_ratio and (
                exact_best is None or near_best_any.ratio > exact_best.ratio):
            chosen, tier_label = near_best_any, "mechanical-near-miss"
            notes.append(f"marker read as {near_best_any.text!r}, one documented-confusion "
                         f"substitution from expected {expected!r}")

    # --- tier 2, content-anchored recovery ----------------------------------
    # Runs only when no numeral-anchored candidate cleared the content check,
    # and its own bar is higher (CONTENT_ANCHOR_RATIO). Deliberately placed
    # ABOVE the weak/position-only paths below: a marker-band token preceded
    # by 6-of-8 matching opening words is better evidence than a correctly
    # spelled numeral whose following text does not match at all.
    if chosen is None:
        anchored = content_anchored_candidates(
            klal, cursor, near_limit, page_loader, order_cache, x_band, content_words)
        if anchored:
            chosen, tier_label = anchored[0], "content-anchored"
            notes.append(
                f"numeral not found by exact or documented-confusion match; recovered by "
                f"anchoring on the stored opening ({chosen.ratio:.3f}) and taking the "
                f"marker-band token before it, which DocAI read as {chosen.text!r} "
                f"(expected {expected!r})")

    # --- weak evidence: only inside the near window -------------------------
    # Everything below is a candidate the content check did NOT clear, so the
    # page-gap bound applies.
    exact_weak, _ = pick(near, 0, ok_ratio)
    if exact_weak is not None and exact_weak.ratio >= ok_ratio:
        exact_weak = None  # already handled above

    if chosen is None and exact_weak is not None and exact_weak.ratio >= vision_floor:
        # Real-looking position, weak content agreement - exactly the middle
        # band vision exists for (klal 34's own marker scores 0.375 here
        # because its surrounding OCR is garbled, not because it is the wrong
        # token).
        verdict = vision_confirm(klal, exact_weak, page_loader(exact_weak.page)) if vision_confirm else None
        if verdict is True:
            chosen, tier_label = exact_weak, "vision-assisted"
            notes.append(f"content agreement {exact_weak.ratio:.3f} below {ok_ratio}; "
                         "marker confirmed by vision crop")
        elif verdict is False:
            notes.append(f"exact numeral at page {exact_weak.page} token {exact_weak.index} "
                         f"(content agreement {exact_weak.ratio:.3f}) DENIED by vision crop")
            exact_weak = None
        else:
            notes.append(f"content agreement {exact_weak.ratio:.3f} below {ok_ratio}; "
                         + ("vision could not decide" if vision_confirm
                            else "no vision adjudicator available"))

    if chosen is None and exact_weak is None:
        near_weak, _ = pick(near, 1, ok_ratio)
        # A near-miss glyph is weaker evidence than an exact one, so without
        # content agreement it is NEVER accepted mechanically - vision is the
        # only route, and silence from vision leaves it unplaced.
        if near_weak is not None and vision_floor <= near_weak.ratio < ok_ratio and vision_confirm:
            if vision_confirm(klal, near_weak, page_loader(near_weak.page)) is True:
                chosen, tier_label = near_weak, "vision-assisted"
                notes.append(f"marker read as {near_weak.text!r} (one documented-confusion "
                             f"substitution from {expected!r}); confirmed by vision crop")

    if chosen is not None:
        record = {
            **base,
            "page": chosen.page,
            "content_match_ratio": round(chosen.ratio, 3),
            "marker_position": chosen.index,
            "status": "ok" if chosen.ratio >= ok_ratio or tier_label == "vision-assisted"
                      else "marker_found_content_mismatch",
        }
        note = f"{tier_label}: matched {chosen.text!r} at page {chosen.page} token {chosen.index}"
        if chosen.which_form:
            note += f", opening agreed with stored {chosen.which_form} ({chosen.ratio:.3f})"
        record["note"] = "; ".join([note] + notes)
        return record, (chosen.page, chosen.rank)

    if exact_weak is not None:
        # An exact numeral in the marker band, close to the cursor, with
        # almost no content support is still a real position - and a klal
        # whose stored text disagrees with the scan at its own marker is
        # precisely what the downstream boundary pass needs to see. Recorded,
        # flagged, and the cursor advanced (the POSITION is trusted; the TEXT
        # is what is in doubt).
        record = {
            **base,
            "page": exact_weak.page,
            "content_match_ratio": round(exact_weak.ratio, 3),
            "marker_position": exact_weak.index,
            "status": "marker_found_content_mismatch",
        }
        record["note"] = "; ".join(
            [f"mechanical-exact: matched {exact_weak.text!r} at page {exact_weak.page} "
             f"token {exact_weak.index}, but the following {content_words} tokens agree with "
             f"the stored opening at only {exact_weak.ratio:.3f} - marker position trusted, "
             "stored text NOT confirmed"] + notes)
        return record, (exact_weak.page, exact_weak.rank)

    record = {
        **base,
        "page": cursor[0],
        "content_match_ratio": None,
        "status": "marker_not_found_in_window",
    }
    record["note"] = "; ".join(
        [f"no marker-band token matching {expected!r} (or any documented-confusion variant) "
         f"found in pages {cursor[0]}-{page_end} from the last confirmed marker forward, with "
         f"content agreement >= {ok_ratio}, nor on position alone within {near_limit}; "
         "`page` here is the SEARCH START, not an observed position"]
        + notes)
    # Cursor deliberately NOT advanced: a klal we could not place must not
    # move the floor for the klalim after it.
    return record, None


def trace(klalim, page_start, page_end, page_loader, x_band=MARKER_X_BAND,
          pairs=CONFUSION_PAIRS, content_words=CONTENT_WORDS, ok_ratio=OK_RATIO,
          vision_floor=VISION_RATIO_FLOOR, ambiguity_margin=AMBIGUITY_MARGIN,
          vision_confirm=None, progress=None):
    """Trace every klal in `klalim` (any iterable of corpus klal dicts) in
    klal_id order over pages [page_start, page_end]. Returns the record list.
    """
    order_cache = {}
    cursor = (page_start, -1)
    unplaced_run = 0
    records = []
    for klal in sorted(klalim, key=lambda k: k["klal_id"]):
        record, new_cursor = resolve_klal(
            klal["klal_id"], klal, cursor, page_end, page_loader, order_cache,
            x_band, pairs, content_words, ok_ratio, vision_floor, ambiguity_margin,
            vision_confirm, unplaced_run=unplaced_run)
        if new_cursor is not None:
            cursor = new_cursor
            unplaced_run = 0
        else:
            unplaced_run += 1
        records.append(record)
        if progress:
            progress(record)
    return records


# ------------------------------------------------------ vision adjudication --

# Hoisted so it can be hashed into the cache key, per CLAUDE.md Lesson 12 and
# the identical fix already made three times in this project's sibling
# scripts: editing any character here changes the question and must invalidate
# every previously cached answer.
VISION_PROMPT_TEMPLATE = """
You are an expert Hebrew paleographer examining a raster crop from an 18th-century printed Hebrew halachic work.

In this print, each numbered section ("klal") is introduced by a small Hebrew NUMERAL set in the right-hand margin, next to the first line of that section's text.

Question: does the marginal numeral highlighted by this crop read "{expected}"?

The token DocAI extracted at this position reads "{observed}".
For context, the section's stored opening text is: "{opening}"

CONSTRAINTS:
1. Judge only what the pixels show. Do not infer the numeral from the surrounding text's meaning.
2. Hebrew numerals here may use final letter forms (ן ף ץ) where the standard spelling uses נ פ צ - treat those as the same numeral.
3. Answer "A" if the marginal numeral reads {expected} (allowing rule 2), "B" if it clearly reads something else, "UNCERTAIN" if the crop does not let you tell.

Respond ONLY with JSON using this structure:
{{
  "selected_option": "A" or "B" or "UNCERTAIN",
  "transcription_found": "exact numeral visible in the margin",
  "confidence": 0.0 to 1.0,
  "reasoning": "paleographic explanation"
}}
"""
VISION_PROMPT_HASH = hashlib.sha256(VISION_PROMPT_TEMPLATE.encode("utf-8")).hexdigest()[:16]

CACHE_DB = os.path.join(REPO, "gematria_trace_vision_cache.db")
CACHE_TABLE = "gematria_marker_cache"
# Generous by design, per CLAUDE.md Lesson 14: a marker crop must show the
# marker IN ITS MARGINAL CONTEXT (the margin edge on one side, the bold
# opening word on the other) or the reader cannot tell a marginal numeral from
# an ordinary word. A marker's own bbox is ~0.03 wide, so the usual 0.02
# correction-crop padding would be a tight box around three glyphs.
VISION_CROP_PADDING = 0.05
VISION_CROP_DPI = 400
# A vision confirmation is only allowed to promote a candidate if the model is
# actually sure. Matches verify_corrections_vision.py's own gate.
VISION_MIN_CONFIDENCE = 0.75


def make_vision_confirmer(pdf_path, client=None, db_path=None, dpi=VISION_CROP_DPI,
                          padding=VISION_CROP_PADDING, stats=None):
    """Build the `vision_confirm` callable `resolve_klal` takes.

    Imports fitz/genai lazily so the whole mechanical path (and the test
    suite) runs with neither installed nor an API key present.
    """
    import fitz  # noqa: PLC0415 - lazy on purpose, see docstring
    import vision_adjudication_common as vac  # noqa: PLC0415

    db_path = db_path or CACHE_DB
    vac.init_cache_table(db_path, CACHE_TABLE, VISION_PROMPT_HASH, has_model_column=True)
    if client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise SystemExit("GEMINI_API_KEY not set (needed for --vision)")
        client = vac.make_client(api_key)
    doc = fitz.open(pdf_path)

    def confirm(klal, candidate, tokens):
        tok = tokens[candidate.index]
        crop = vac.crop_pdf_bounding_box(doc, candidate.page, tok, padding=padding, dpi=dpi)
        expected = cio.klal_id_to_gematria(klal["klal_id"])
        opening = " ".join(klal.get("clean_text", "").split()[:12])
        prompt = VISION_PROMPT_TEMPLATE.format(
            expected=expected, observed=candidate.text, opening=opening)
        # word_a/word_b carry the two readings being compared, exactly as
        # every other cache in this repo keys them (CLAUDE.md Lesson 12): the
        # same crop is legitimately asked about different numerals as the
        # cursor moves, and a crop-only key would return the wrong answer.
        if stats is not None:
            stats["asked"] = stats.get("asked", 0) + 1
        raw = vac.adjudicate_with_retry(
            client, crop, prompt,
            cache_get=lambda: vac.get_cached_decision(
                db_path, CACHE_TABLE, VISION_PROMPT_HASH, crop, expected, candidate.text, opening),
            cache_put=lambda text, model_name: vac.put_cached_decision(
                db_path, CACHE_TABLE, VISION_PROMPT_HASH, crop, expected, candidate.text,
                opening, text, model=model_name, has_model_column=True),
        )
        try:
            decision = json.loads(raw)
        except json.JSONDecodeError:
            try:
                decision = json.loads(vac.sanitize_json(raw))
            except json.JSONDecodeError:
                return None
        selected = decision.get("selected_option")
        confidence = float(decision.get("confidence") or 0.0)
        if confidence < VISION_MIN_CONFIDENCE:
            return None
        if selected == "A":
            return True
        if selected == "B":
            return False
        return None

    return confirm


# ------------------------------------------------------------------- CLI ----

def parse_part_arg(spec):
    """`src.json:dest.json` -> (src, dest). Split on the LAST colon so a
    Windows-style or otherwise colon-bearing path still works."""
    if ":" not in spec:
        raise argparse.ArgumentTypeError(
            f"--part expects SRC:DEST (e.g. part2.json:gematria_trace_part2.json), got {spec!r}")
    src, dest = spec.rsplit(":", 1)
    return src, dest


def parse_pages(spec):
    try:
        lo, hi = spec.split("-")
        return int(lo), int(hi)
    except ValueError:
        raise argparse.ArgumentTypeError(f"--pages expects FIRST-LAST, got {spec!r}")


def parse_band(spec):
    try:
        lo, hi = spec.split(",")
        return float(lo), float(hi)
    except ValueError:
        raise argparse.ArgumentTypeError(f"--x-band expects MIN_X1,MAX_X2, got {spec!r}")


def summarize(records):
    counts = {}
    for r in records:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    return counts


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--part", action="append", required=True, type=parse_part_arg,
                    metavar="SRC:DEST",
                    help="corpus file and the trace file to write for it; repeatable, "
                         "and repeated parts are traced as one continuous sequence")
    ap.add_argument("--pages", required=True, type=parse_pages, metavar="FIRST-LAST",
                    help="scan page range to search, inclusive")
    ap.add_argument("--docai-dir", default=cio.DOCAI_DIR,
                    help="directory of page_N.json DocAI token files")
    ap.add_argument("--x-band", type=parse_band, default=MARKER_X_BAND, metavar="MIN_X1,MAX_X2",
                    help=f"marker bbox x-band, normalized (default {MARKER_X_BAND}, measured "
                         "from this print's confirmed markers)")
    ap.add_argument("--ok-ratio", type=float, default=OK_RATIO)
    ap.add_argument("--vision", action="store_true",
                    help="resolve borderline/ambiguous candidates with a cached Gemini crop call")
    ap.add_argument("--pdf", default=os.path.join(REPO, "berlin_square_corrected.pdf"),
                    help="scan PDF, only used with --vision")
    ap.add_argument("--report-x-band", action="store_true",
                    help="print the observed x1/x2 range of accepted markers, for calibrating "
                         "--x-band on a different print")
    ap.add_argument("--dry-run", action="store_true", help="compute and report, write nothing")
    args = ap.parse_args(argv)

    page_start, page_end = args.pages
    cache = cio.DocaiPageCache(args.docai_dir, default=None)

    sources = []
    all_klalim = []
    for src, dest in args.part:
        src_path = src if os.path.isabs(src) else os.path.join(REPO, src)
        dest_path = dest if os.path.isabs(dest) else os.path.join(REPO, dest)
        klalim = cio.load_klalim(src_path)
        if not klalim:
            raise SystemExit(f"no klalim loaded from {src_path}")
        sources.append((dest_path, {k["klal_id"] for k in klalim}))
        all_klalim.extend(klalim)

    stats = {}
    vision_confirm = None
    if args.vision:
        vision_confirm = make_vision_confirmer(args.pdf, stats=stats)

    def progress(record):
        print(f"  klal {record['klal_id']:>4}  {record['status']:<32} "
              f"page {record['page']}  pos {record.get('marker_position')}")

    records = trace(all_klalim, page_start, page_end, cache.get,
                    x_band=args.x_band, ok_ratio=args.ok_ratio,
                    vision_confirm=vision_confirm, progress=progress)

    by_id = {r["klal_id"]: r for r in records}
    for dest_path, ids in sources:
        subset = [by_id[i] for i in sorted(ids) if i in by_id]
        counts = summarize(subset)
        print(f"{dest_path}: {len(subset)} klalim  {counts}")
        if not args.dry_run:
            with open(dest_path, "w", encoding="utf-8") as f:
                json.dump(subset, f, ensure_ascii=False, indent=2)

    if args.vision:
        print(f"vision adjudications requested: {stats.get('asked', 0)} "
              f"(cache hits included; see {CACHE_DB} for what was actually paid for)")

    if args.report_x_band:
        placed = [r for r in records if r.get("marker_position") is not None]
        xs = []
        for r in placed:
            tokens = cache.get(r["page"])
            if tokens and r["marker_position"] < len(tokens):
                t = tokens[r["marker_position"]]
                xs.append((t["x1"], t["x2"]))
        if xs:
            print(f"observed marker band over {len(xs)} placed markers: "
                  f"x1 [{min(x for x, _ in xs):.3f}, {max(x for x, _ in xs):.3f}]  "
                  f"x2 [{min(y for _, y in xs):.3f}, {max(y for _, y in xs):.3f}]")

    return records


if __name__ == "__main__":
    main()
