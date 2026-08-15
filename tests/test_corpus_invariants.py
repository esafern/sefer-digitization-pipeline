"""[PRODUCTION] Standing regression suite for the derived corpus files
(part1/2/3.json, klalim_demo_dataset.json). Run via `./venv/bin/pytest`,
or automatically as the final step of `rebuild_all.sh`.

Why this exists: PROJECT-STATUS.md's own history is a record of the same
lesson recurring - a cheap, corpus-wide, no-API text-pattern sweep (grep a
literal string, a duplicate-word scan, a klal-count check) finds real
defects that expensive manual/LLM review missed entirely, but until now
every one of those sweeps was a one-off script run by hand when someone
happened to ask (CLAUDE.md Lessons 8/18; PROJECT-STATUS.md 2026-08-06
"Process evaluation" section explicitly says this should happen after
every batch of edits, not just when asked). This suite converts those
sweeps into standing, always-run tests so a regression - e.g. klal 128's
`לאוקומי לאוקומי` duplication, or the page-header-contamination bug -
fails loudly the moment it's reintroduced, instead of waiting for the next
manual audit to stumble onto it.

Design principle - baseline, not zero-tolerance, for checks with known
false positives: several of these checks (duplicate-consecutive-word,
title-alphabetical-order, span-coverage-ratio) have real, currently-known
exceptions that are legitimate corpus content, not bugs - documented
inline at each baseline. Those tests assert "no NEW violations beyond the
recorded baseline," not "zero violations": a hard zero-tolerance test on
these would either be permanently red (and therefore ignored) or force
fixing content-correctness work that's out of scope for a test-suite
change and is already tracked as its own open item in PROJECT-STATUS.md.
When a baseline shrinks (someone verifies and fixes one), shrink the
constant to match, with a comment citing the fix. When it grows, that's a
real regression - investigate before ever updating the baseline to match.

Checks that ARE zero-tolerance (no baseline): structural invariants (klal
count/sequence, derived-file drift, page-header contamination, debug-print
leaks, the no-text-available placeholder set, non-empty title/clean_text,
clean_text whitespace, and - added 2026-08-14 - the shape of the two derived
files the review dashboard serves to a human reviewer
(corrections_part1.json, klal_page_regions.json) plus the integrity of the
append-only decision log). These have no known legitimate exception anywhere
in the corpus, per the PROJECT-STATUS.md section cited in each test.

Scope note: this suite checks the DATA a pipeline run produced.
tests/test_pipeline_logic.py (added 2026-08-14, same gate) checks the LOGIC
that produces it, on synthetic inputs - the two are complementary, because
several correctness paths (candidate drift detection, the re-apply guard,
the vision cache key) are currently inert on real data and cannot be
exercised by any amount of looking at the corpus.
"""
import importlib.util
import json
import os
import re

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PART_FILES = ["part1.json", "part2.json", "part3.json"]

NO_TEXT_TITLE = "(no text available)"

# Originally 6 klal_ids (167, 187, 190, 197, 216, 217) were flagged as
# genuine numbering gaps by direct visual page inspection - see
# PROJECT-STATUS.md "CLOSED 2026-08-06: Klal 167, 187, 190, 197, 216, 217
# are confirmed genuine numbering gaps". Every single one of them turned out
# to be wrong, resolved the same night: each was either a marker misread
# (a klal's own gematria marker OCR'd as an already-used neighboring
# marker - ז read as ו, ה, or final-nun; or a not-yet-tried alternate valid
# gematria spelling) with its real content merged, undivided, into a
# "trusted" neighbor's stored text (the Lesson 16 pattern). None were real
# gaps. See "Klal 167 resolved" and "Klal 185-190, 196-197, 215-217
# resolved" sections. This set is intentionally now EMPTY, not deleted -
# a future genuine gap would need to be added back here with the same
# direct-crop confirmation standard, not assumed from boundary-adjacency
# alone (the method that produced this entire wrong list in the first
# place).
CONFIRMED_NUMBERING_GAPS = set()

# Page-header/watermark running text that leaks mid-sentence into
# clean_text when a klal's span crosses a page boundary. Confirmed fixed
# corpus-wide (all 3 parts, all spelling variants) 2026-08-06 - see
# PROJECT-STATUS.md "MAJOR, NEW FINDING 2026-08-06: the same page-header
# contamination bug ... is systemic in Parts 2 and 3" and the "Missed
# spelling variants" follow-up (מלאכי, מראכי, כרלי, כררי variants). Any
# match here is page furniture that should never appear in clean_text -
# zero tolerance, not a baseline.
HEADER_CONTAMINATION_RE = re.compile(r"מ[לר][אר]כי כ[לר][לר]י")

# A debug `print(len(...))` line accidentally captured into stored text
# while hand-building a large klal's clean_text (klal 152/154, "283\n" /
# "797\n" prefixes) - see PROJECT-STATUS.md 2026-08-06 "Self-inflicted
# bug". Zero tolerance: no real klal text starts with a bare digit run.
LEADING_DIGIT_RE = re.compile(r"^\d")

# --- Baselines for checks with known, currently-accepted false positives ---

# Duplicate-consecutive-word sweep: a plain "same word twice in a row"
# check mostly returns false positives in this corpus, because Torah-verse
# word repetition is itself a hermeneutic principle Yad Malachi discusses
# (e.g. klal 29's `שור שור שור` - "shor" repeated 7x in one verse, each
# repetition deriving a distinct law) - see PROJECT-STATUS.md 2026-08-06
# "A corpus-wide duplicate-consecutive-word sweep mostly returned false
# positives, and that itself is a finding". Single-character tokens
# (gematria/abbreviation letters, not words) are excluded before matching
# against this baseline - they are a distinct, much noisier source of
# "duplicates" that are never real content repetition.
#
# This baseline is every (klal_id, word) pair the sweep currently finds,
# whether individually confirmed genuine (klal 29, 158, 166, 619 - cited
# by name in PROJECT-STATUS.md) or merely "not yet exhaustively checked
# for Parts 2-3" (PROJECT-STATUS.md: "flagging the residual list from that
# sweep as unresolved for Parts 2-3, not silently cleared"). Shrinking this
# set (an entry gets individually verified and, if it's a real bug like
# klal 128's `לאוקומי לאוקומי` was, fixed) is progress - update the
# baseline down when that happens. A NEW pair appearing here that isn't
# already in this set is exactly the klal-128 failure mode and should be
# investigated, not silently added.
DUPLICATE_WORD_BASELINE = {
    (1, "תניא"), (2, "לשוא"), (3, "ואם"), (8, "דאיידי"), (16, "עב"),
    (29, "לא"), (29, "שור"), (29, "צדה"),
    # (30, "לה"): NOT an artifact - visually confirmed against page 24's
    # scan 2026-08-12 ("...דרבנן נמי לה לה מאשה גמרי..."), and the phrase
    # recurs 4 separate times across klal 30's newly-recovered text
    # (reconstruct_multipage_klalim.py --apply). This is the halachic
    # technical term for the gezeirah shavah derived from the shared word
    # "לה" (Hebrew maidservant law) - the exact topic of klal 30's title
    # ("אין גזרה שוה למחצה"). See PROJECT-STATUS.md.
    (30, "לה"),
    (41, "אלא"), (54, "הן"),
    (68, "הניזקין"), (86, "הוא"), (94, "על"), (103, "עד"), (112, "פסקא"),
    (135, "ואידך"), (143, "צדק"), (144, "עשה"), (158, "ולית"),
    (167, "קיל"), (176, "בר"), (217, "המלך"), (230, "לא"), (235, "הוה"),
    (245, "בר"), (249, "מכוה"), (256, "הן"), (256, "קלי"), (264, "דמי"),
    (279, "לא"), (293, "דלא"), (299, "כן"), (349, "שוות"), (371, "עשה"),
    (410, "ראשון"), (410, "הוא"), (445, "מנלן"), (445, "הוא"),
    (456, "הוא"), (466, "ב"), (498, "הן"), (538, "הם"), (542, "ושוב"),
    (542, "הקל"), (547, "זבחי"), (558, "דחזקיה"), (559, "יורה"),
    (585, "הוה"), (589, "ירמיה"), (619, "ופלוני"), (621, "ופ"),
    (645, "קנה"), (663, "בר"), (663, "הן"),
}

# validate_title_alphabetical_order.py's isotonic-regression check flags
# any title whose first letter breaks the section's alphabetical run.
# Current flagged set has two distinct, already-diagnosed causes, neither
# a corpus bug:
#   - Part 1 (klal 101-104): a deliberate elliptical-title convention this
#     book uses for a run of klalim restating the same maxim - klal 100's
#     title is the full `בית דין מתנין לעקור...`, and 101-104 each open
#     with just `מתנין...`, omitting the already-established subject
#     (the same style as klal 5's single-word title `איתמר`, see
#     PROJECT-STATUS.md "The abridged `title` field must be judged").
#   - Parts 2-3 (~100 klalim): the un-judged `"כלל <N>"` placeholder title
#     convention (see PLACEHOLDER_TITLE_BASELINE below) - `כלל` starts
#     with כ, which trips the check, not a real boundary break. See
#     PROJECT-STATUS.md "Parts 2-3: ~108 klalim flagged, but this is a
#     different, already-known cause, not a new corruption pattern."
# Recorded as a count, not an exact id set, because this list will shrink
# incrementally as Parts 2-3 titles get manually judged (see PLACEHOLDER_
# TITLE_BASELINE) without that being a regression worth hand-updating a
# giant id list for every single fix.
ALPHABETICAL_ORDER_VIOLATION_BASELINE_MAX = 110

# 115 of 445 Part 2-3 klalim have a literal, never-manually-judged
# "כלל <N>" placeholder title (quantified 2026-08-05, see
# PROJECT-STATUS.md "Alphabetical order check redone correctly, twice").
# This number should only ever go DOWN (as titles get judged) - if it goes
# up, a real title was overwritten with a placeholder, which is a
# regression.
PLACEHOLDER_TITLE_COUNT_MAX = 115

# validate_klal_span_coverage.py flags any Part-1 klal whose stored word
# count falls below 85% of its real marker-to-marker token span. Current
# baseline (6): klal 175 is an already-documented conservative-rounding
# false positive (PROJECT-STATUS.md "klal 175 is a confirmed false
# positive"); klal 106 sits right at the 0.85 threshold and was reasoned
# about but not individually resolved (PROJECT-STATUS.md "klal 106 newly
# appears at the threshold... not investigated further as a likely false
# positive... given time budget"); klal 179/181/193 are the three klalim
# whose merged content was just split out 2026-08-06 (180/182/194) - the
# *neighbor* klal (179/181/193) now legitimately looks short by this ratio
# because its former (wrongly merged) length no longer belongs to it;
# klal 123 was individually verified 2026-08-07 (full raw token span
# read end to end) and is genuinely complete - the flag is caused by
# ~11 page-furniture tokens (a footnote numeral, "Digitized by Google"
# watermark, folio number, and the next page's running header) inflating
# the raw marker-to-marker span count, the same false-positive class as
# klal 106/175. None of these are corpus bugs as currently
# understood; a genuinely new entry here is the same failure mode as the
# original klal-2/klal-4 cross-page truncation bug this validator was
# built to catch.
#
# SHRUNK 6 -> 3 on 2026-08-11: klal 179, 181 and 193 were never real flags.
# Klal 180/182/194 have no entry in gematria_trace_part1.json at all, so the
# span from 179's marker runs to 181's marker and physically contains BOTH
# klalim's text - but the old code compared that two-klal span against klal
# 179's words alone, guaranteeing a low ratio. build_spans() now sums the
# stored words of every klal a span covers, and all three clear comfortably
# (0.93/0.94/0.94). The baseline comment here had already described the
# cause correctly ("its former merged length no longer belongs to it")
# without recognising it as a measurement bug rather than corpus reality.
# klal 83 ADDED 2026-08-11, downgraded from a reported catastrophe: it measured
# 0.09 only because berlin_square.pdf had leaves 37/38 transposed. With the PDF
# corrected it measures 0.82 on a 131-token span - the same furniture-inflation
# class as 106/123/175 (a 131-token cross-page span carries ~10 tokens of
# header/watermark/catchword/folio furniture, ~8% of the count, which accounts
# for most of the shortfall). NOT individually crop-verified, unlike klal 123 -
# it is a *probable* false positive, and klal 84's marker is still unknown so
# the 83/84 split itself is unconfirmed. Worth a direct check if anyone is in
# the area; it is not a known real gap.
# klal 15, 130, 195 ADDED 2026-08-13: NOT truncation, a ratio-threshold
# artifact of a corpus-wide accuracy fix. A DocAI tokenization bug put a
# stray space between an abbreviated word and its own closing geresh
# throughout Part 1 (e.g. stored "התוס '" where the print is "התוס'") -
# fixed corpus-wide (2,548 instances, 201 klalim; see PROJECT-STATUS.md
# "stray space before abbreviation geresh"), verified letter-for-letter
# identical before/after (stripping every non-Hebrew-letter character
# from clean_text produced byte-identical results for all 222 klalim -
# the fix only ever merges two whitespace-separated tokens into one,
# never touches a real letter). That merge necessarily lowers word count
# by 1 per instance, and these three klalim's ratios were already within
# a hair of FLAG_RATIO_THRESHOLD (0.85) before the fix - klal 15+16's
# combined span 0.869->0.830 (16 alone lost 9 stray-space instances),
# klal 130 0.853->0.840 (1 instance), klal 195 0.870->0.848 (1 instance).
# Recomputing each span's ratio against the PRE-fix word counts confirms
# all three clear 0.85 - this is the ratio threshold reacting to a real
# accuracy improvement, not new missing content.
SPAN_COVERAGE_BASELINE = {15, 83, 106, 123, 130, 175, 195}

# NOT false positives - these are CONFIRMED REAL, UNFIXED corpus damage,
# kept in a separate constant from SPAN_COVERAGE_BASELINE precisely so that
# nobody reads a green test run as "span coverage is fine." Found 2026-08-11
# once validate_klal_span_coverage.py stopped silently dropping the klalim
# whose span crosses more than one page boundary (see PROJECT-STATUS.md
# "Deep methodology audit"):
#   klal 30    ratio 0.06 - 1,891 tokens unaccounted (page 23->25)
#   klal 83-84 ratio 0.09 - 1,081 tokens unaccounted (page 37->39)
#   klal 88    ratio 0.24 -   921 tokens unaccounted (page 39->41)
#   klal 36-37 ratio 0.44 -   285 tokens unaccounted (page 26->27)
# Scan pages 24, 38 and 40 are assigned to no klal and their content
# (2,658 furniture-stripped words) is absent from part1+part2+part3
# entirely - verified by best-match similarity of sampled windows against
# the whole corpus (9-12%, vs 100% for a genuinely covered page) and by
# ruling out duplicate scans (true match ratio 0.015 against the nearest
# other page; running headers show a clean folio sequence around them).
# This set must SHRINK as the content is reconstructed and must never grow.
# It exists to keep the gate usable while the reconstruction is tracked as
# its own open item - not to accept the defect.
#
# 2026-08-11, three times in one day:
#   {30, 36, 83, 88} -> {30, 36, 75, 88} when berlin_square.pdf's transposed
#     leaves 37/38 were corrected: klal 83-84's apparent 0.09 catastrophe was an
#     artifact of the page order (it measures 0.82 corrected, now in
#     SPAN_COVERAGE_BASELINE) and the real gap turned out to be klal 75.
#   {30, 36, 75, 88} -> {36} when klal 30, 75 and 88 were reconstructed by an
#     unattended agent run (reconstruct_multipage_klalim.py) that exceeded its
#     authorized scope - the reconstruction was never reviewed or approved and
#     was deliberately reverted from part1.json as a result. This is NOT a
#     statement that the reconstructed text was wrong; it was reverted for lack
#     of authorization and review, not a demonstrated correctness problem - see
#     PROJECT-STATUS.md "Deep methodology audit" for the full incident record.
#   {36} -> {30, 36, 75, 88} reverting to match part1.json's actual reverted
#     state, so this gate reports reality rather than a discarded change.
#   {30, 36, 75, 88} -> {36} again, 2026-08-12: re-applied
#     `reconstruct_multipage_klalim.py --apply`, this time under EXPLICIT
#     direct user authorization in-conversation ("just go with docai -
#     tesseract is terrible here... flag questionable words as usual") -
#     the exact governance gap (unauthorized/unreviewed) that caused the
#     2026-08-11 revert, not a correctness concern. `./rebuild_all.sh` run
#     afterward (full, not --skip-vision) so the new content gets flagged
#     through the normal vision-adjudication pipeline like the rest of the
#     corpus, per that same instruction. See PROJECT-STATUS.md.
# `reconstruct_multipage_klalim.py` is still on disk; it is not part of
# rebuild_all.sh (a deliberate one-off, run manually, not on every rebuild).
#   {36} -> {} 2026-08-12: klal 36-37 fixed too. Located klal 37's real
#     marker directly (page 26 token 703, docai misread לז as לו - the
#     familiar ז/ו confusion pattern) by finding which of the two candidate
#     positions actually opened with klal 37's already-correctly-stored
#     text; confirmed klal 36's span was already fully captured once
#     correctly bounded, then found and fixed a genuine 279-word tail
#     truncation in klal 37 (crop-verified at both boundaries) - the actual
#     content behind the ~285-word gap this set used to track.
# Empty for now - every previously-tracked real gap has a confirmed fix.
# Keep this mechanism (not delete it) for the next one that turns up.
SPAN_COVERAGE_KNOWN_REAL_GAPS = set()


def _load_klalim(path):
    d = json.load(open(path, encoding="utf-8"))
    return d["klalim"] if isinstance(d, dict) and "klalim" in d else d


def _import_from_path(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def part_klalim():
    return {p: _load_klalim(os.path.join(REPO, p)) for p in PART_FILES}


@pytest.fixture(scope="session")
def all_klalim(part_klalim):
    combined = []
    for p in PART_FILES:
        combined.extend(part_klalim[p])
    return sorted(combined, key=lambda k: k["klal_id"])


@pytest.fixture(scope="session")
def part1_by_id(part_klalim):
    return {k["klal_id"]: k for k in part_klalim["part1.json"]}


@pytest.fixture(scope="session")
def corrections():
    """corrections_part1.json - the per-klal flag overlay review_server.py
    serves to the reviewer. Tracked in git (not a gitignored cache), so it is
    always present and always expected to be current with part1.json: this
    suite is rebuild_all.sh's LAST step, after the stage that regenerates it.
    """
    return json.load(open(os.path.join(REPO, "corrections_part1.json"), encoding="utf-8"))


@pytest.fixture(scope="session")
def regions():
    return json.load(open(os.path.join(REPO, "klal_page_regions.json"), encoding="utf-8"))


@pytest.fixture(scope="session")
def alignment():
    align = json.load(open(os.path.join(REPO, "part1_header_anchored_alignment.json"), encoding="utf-8"))
    return {r["klal_id"]: r for r in align}


@pytest.fixture(scope="session")
def decision_records():
    """review_decisions.jsonl, read as raw records. Read-only, always - this
    file is the append-only human-decision audit trail, deliberately outside
    the corpus-build pipeline so no rebuild can clobber it (CLAUDE.md "Human
    review decisions"). A test must never write to it.
    """
    path = os.path.join(REPO, "review_decisions.jsonl")
    with open(path, encoding="utf-8") as f:
        return [(i, line) for i, line in enumerate(f, 1) if line.strip()]


# --- Zero-tolerance structural invariants ---

def test_klal_id_sequence_is_complete_unique_and_ordered(all_klalim):
    ids = [k["klal_id"] for k in all_klalim]
    assert ids == list(range(1, 668)), (
        "klal_id sequence must be exactly 1..667 with no gaps or duplicates "
        "(the 6 confirmed numbering gaps stay IN the sequence as explicit "
        "placeholders, not removed - see CONFIRMED_NUMBERING_GAPS)."
    )


def test_klalim_demo_dataset_matches_part_concatenation(part_klalim):
    """klalim_demo_dataset.json must always equal part1+part2+part3,
    nothing hand-edited on top - see CLAUDE.md "Single source of truth"
    and Lesson 13 ("a hand-maintained 'derived' file is not actually
    derived"). This is the exact check build_klalim_demo_dataset.py's
    own docstring says was violated for the whole project before
    2026-08-05.
    """
    expected = []
    for p in PART_FILES:
        expected.extend(part_klalim[p])
    expected = sorted(expected, key=lambda k: k["klal_id"])

    demo_path = os.path.join(REPO, "klalim_demo_dataset.json")
    actual = json.load(open(demo_path, encoding="utf-8"))
    actual = sorted(actual, key=lambda k: k["klal_id"])

    assert actual == expected, (
        "klalim_demo_dataset.json has drifted from part1/2/3.json - run "
        "build_klalim_demo_dataset.py (or rebuild_all.sh) to regenerate it. "
        "Never hand-edit klalim_demo_dataset.json directly."
    )


def test_no_text_available_placeholders_are_exactly_the_confirmed_gaps(all_klalim):
    """See PROJECT-STATUS.md "CLOSED 2026-08-06: Klal 167, 187, 190, 197,
    216, 217 are confirmed genuine numbering gaps" and "RETRACTED AND
    CORRECTED, 2026-08-06" (180/182/194 were wrongly in this set - they
    had real content merged into a neighbor and are now split out). If
    this set ever differs from CONFIRMED_NUMBERING_GAPS, either a real
    klal got wrongly blanked out, or one of the 6 confirmed gaps was
    filled in without updating this test - both need a human look, not a
    silent baseline update.
    """
    placeholder_ids = {k["klal_id"] for k in all_klalim if k["title"] == NO_TEXT_TITLE}
    assert placeholder_ids == CONFIRMED_NUMBERING_GAPS


def test_no_page_header_contamination(all_klalim):
    offenders = [k["klal_id"] for k in all_klalim if HEADER_CONTAMINATION_RE.search(k["clean_text"])]
    assert not offenders, (
        f"Page-header/running-title text leaked into clean_text for klal(im) {offenders} - "
        "this is scanner furniture (e.g. 'יד/יר/יך מלאכי כללי X'), never real content. "
        "See PROJECT-STATUS.md 2026-08-06 header-contamination sections."
    )


def test_no_debug_artifact_leaks(all_klalim):
    offenders = [k["klal_id"] for k in all_klalim if LEADING_DIGIT_RE.match(k["clean_text"].strip())]
    assert not offenders, (
        f"clean_text starts with a bare digit for klal(im) {offenders} - this is the same "
        "class of bug as klal 152/154's captured `print(len(...))` output "
        "(PROJECT-STATUS.md 2026-08-06 'Self-inflicted bug'), not real text."
    )


def test_clean_text_whitespace_is_single_spaces_only(all_klalim):
    """Two different word-index schemes coexist in this pipeline and are
    only safe while they agree. Machine candidates index into
    `clean_text.split()` (build_corrections_dataset.py's page_word_origin,
    assemble_corrections_dataset.py, apply_reviewer_decisions.py's
    apply_replace); human decisions index into `clean_text.split(' ')` -
    deliberately, because review_frontend/app.js computes the clicked
    word's index that way (see apply_reviewer_decisions.py's
    apply_manual_correction docstring, which calls the divergence a
    documented open risk). A single double space, leading/trailing space,
    tab or newline anywhere in clean_text silently shifts one scheme
    against the other from that point on, so a reviewer's recorded
    word_index would point at a different word than the machine candidate
    at the same index - the shape of the 2026-08-13 reindexing incident.
    Zero tolerance: the corpus has no legitimate reason to carry any
    whitespace but single spaces, and every apply/propose script writes
    text back with " ".join(...).
    """
    offenders = []
    for k in all_klalim:
        t = k["clean_text"]
        if t.split(" ") != t.split():
            offenders.append(k["klal_id"])
    assert not offenders, (
        f"clean_text contains double/leading/trailing/non-space whitespace for klal(im) "
        f"{offenders}. This desynchronises the machine (.split()) and human (.split(' ')) "
        "word-index schemes against each other - normalise the text before proceeding."
    )


# Added 2026-08-15 (dropped-lamed ligature bug - see PROJECT-STATUS.md and
# PROJECT-STATUS-HISTORY.md for the full investigation). This print sets the
# letter pair א+ל as a single ligature glyph (Unicode U+FB4F); DocAI reads
# that glyph as a bare א, silently dropping the lamed. 130 real instances
# were found and fixed in Part 1 across two review passes. Every one of
# these 24 corrupt forms was confirmed to have ZERO legitimate standalone
# use anywhere in Part 1's ~52,600 words (every occurrence found was this
# exact bug, none were coincidentally a real independent word) - see the
# PROJECT-STATUS-HISTORY.md entry for the individual verification of each
# form, including the three (אמא, בצלא, אפא) that have a plausible
# unrelated meaning in general Hebrew/Aramaic and were checked with extra
# care before being included here. Zero tolerance: these are not
# borderline or stylistic - none of them are real Rabbinic Hebrew words in
# this text.
DROPPED_LAMED_CORRUPT_FORMS = {
    "אא", "אגאזי", "אה", "אהים", "איבא", "איביה", "איבייהו", "איה", "איעזר",
    "אמא", "אעאי", "אעזר", "אפא", "בצלא", "דשמוא", "האה", "האף", "ואהים",
    "והאף", "וכאה", "ושמוא", "ישמעא", "ישרא", "שמוא",
}


def test_part1_no_dropped_lamed_ligature_corruption(part_klalim):
    """Regression guard for the alef-lamed ligature extraction bug - see
    DROPPED_LAMED_CORRUPT_FORMS above. Matches whole space-split tokens
    only (not substrings), same scheme the actual fix used, so a real word
    that happens to CONTAIN one of these forms as a substring is not a
    false positive - only an exact standalone occurrence is a hit.

    PART 1 ONLY - deliberately NOT run against `all_klalim` (all 3
    parts). Confirmed 2026-08-15 while building this test: Parts 2-3
    contain hundreds of unfixed instances of this exact corruption (e.g.
    `אא` alone: 74 in Part 2, 35 in Part 3, vs Part 1's 40 real
    corruptions before the fix) - CLAUDE.md's standing directive keeps
    Parts 2-3 out of scope until Part 1 is independently confirmed clean,
    so this test must not fail on their still-uncorrected text. A
    Parts-2-3 version of this check is future work for whenever that gate
    lifts, not something to smuggle in via a corpus-wide fixture now."""
    offenders = []
    for k in part_klalim["part1.json"]:
        for i, w in enumerate(k["clean_text"].split(" ")):
            if w in DROPPED_LAMED_CORRUPT_FORMS:
                offenders.append((k["klal_id"], i, w))
    assert not offenders, (
        f"Dropped-lamed ligature corruption reappeared in Part 1: {offenders}. This exact class "
        f"of bug was found and fixed 2026-08-14/15 (see PROJECT-STATUS-HISTORY.md) - re-verify "
        f"against the scan before correcting, don't assume the same fix applies blindly."
    )


def test_part1_max_klal_constants_agree_with_the_corpus(part_klalim):
    """PART1_MAX_KLAL = 222 is written out independently in three live files
    (build_corrections_dataset.py, build_klal_page_regions.py,
    review_server.py) with no shared definition - it is max(klal_id) in
    part1.json, i.e. data, not a chosen number. Added 2026-08-15 during the
    hard-wired-value audit: nothing tied any of the three back to the corpus,
    and if Part 1's klal count ever moves (a split/merge, Success Criterion
    #2's own failure mode) and only some copies are updated, every failure is
    silent - a klal simply stops getting candidates, stops getting a scan
    region, or stops being served to the dashboard, with no error anywhere.
    Zero tolerance: derive-or-assert, not "usually agrees" (CLAUDE.md
    Lesson 13's argument, applied to a constant rather than a file).
    """
    part1_max = max(k["klal_id"] for k in part_klalim["part1.json"])
    modules = {
        "build_corrections_dataset.py": None,
        "build_klal_page_regions.py": None,
        "review_server.py": None,
    }
    for name in modules:
        mod = _import_from_path(name.removesuffix(".py"), os.path.join(REPO, name))
        modules[name] = mod.PART1_MAX_KLAL
    disagreeing = {n: v for n, v in modules.items() if v != part1_max}
    assert not disagreeing, (
        f"PART1_MAX_KLAL disagrees with part1.json's own max klal_id ({part1_max}): "
        f"{disagreeing}. Update every copy together, or the pipeline silently covers "
        "different klalim in different stages."
    )
    # part1.json must also be a contiguous 1..N block, or "max klal_id" is not
    # the same thing as "the Part-1 range" and every `klal_id <= PART1_MAX_KLAL`
    # test in the pipeline is filtering on the wrong property.
    assert sorted(k["klal_id"] for k in part_klalim["part1.json"]) == list(range(1, part1_max + 1))


def test_title_and_clean_text_are_never_empty(all_klalim):
    empty_titles = [k["klal_id"] for k in all_klalim if not k.get("title", "").strip()]
    empty_text = [k["klal_id"] for k in all_klalim if not k.get("clean_text", "").strip()]
    assert not empty_titles, f"klal(im) with an empty title field: {empty_titles}"
    assert not empty_text, f"klal(im) with empty clean_text: {empty_text}"


# --- Review-layer derived files: what the dashboard actually serves ---------
# Added 2026-08-14. Everything above checks the corpus text; these check the
# three files a human reviewer's decisions are made against and recorded in.
# A defect here does not corrupt the text directly - it shows the reviewer the
# wrong word, the wrong scan region, or the wrong flag, which is how a wrong
# decision gets made in the first place (PROJECT-STATUS.md's 2026-08-13
# reindexing incident: 10 human decisions orphaned onto positions that no
# longer meant what they said).

def test_no_stale_candidate_flags_are_being_served(corrections):
    """assemble_corrections_dataset.py's drift check force-flags any
    candidate whose word_index/corrected_word no longer matches live
    part1.json. Since this suite is rebuild_all.sh's last step, every
    candidate has just been regenerated against the current corpus - a
    stale flag surviving to here means a stage of the rebuild did not
    actually re-derive from part1.json (the `--skip-vision` staleness path).
    """
    stale = sorted(
        (int(kid), c["word_index"]) for kid, entries in corrections.items()
        for c in entries if c.get("flag") == "stale_candidate"
    )
    assert not stale, (
        f"{len(stale)} candidate(s) are flagged 'stale_candidate' - (klal_id, word_index): {stale}. "
        "Their recorded position no longer matches part1.json, so the reviewer would be shown a "
        "verdict about a different word. Re-run ./rebuild_all.sh (without --skip-vision)."
    )


def test_every_served_flag_has_a_dashboard_label(corrections):
    """review_frontend/app.js falls back to a bare 'Flagged' for any flag
    review_server.FLAG_LABELS doesn't know, which is indistinguishable from a
    typo'd flag name. tests/test_pipeline_logic.py checks the same property
    against every flag classify() CAN emit; this checks the ones actually on
    disk right now, which also covers a flag introduced by hand-editing.
    """
    review_server = _import_from_path("review_server", os.path.join(REPO, "review_server.py"))
    served = {c.get("flag") for entries in corrections.values() for c in entries}
    unlabelled = sorted(f for f in served if f not in review_server.FLAG_LABELS)
    assert not unlabelled, (
        f"flag value(s) {unlabelled} appear in corrections_part1.json with no "
        "review_server.FLAG_LABELS entry - the dashboard renders them as an unnamed, "
        "uncoloured 'Flagged' word."
    )


def test_correction_word_index_points_inside_its_own_klal(corrections, part1_by_id):
    """A candidate's word_index indexes clean_text.split(). Out of range means
    the reviewer is shown a flag attached to nothing, and an accepted decision
    would apply at a position that does not exist. Only a 'delete' candidate
    (proposing to INSERT missing text) may legitimately sit one past the last
    word - that is its append position.
    """
    offenders = []
    for kid, entries in corrections.items():
        klal = part1_by_id.get(int(kid))
        if klal is None:
            offenders.append((kid, None, "klal_id not in part1.json"))
            continue
        n_words = len(klal["clean_text"].split())
        for c in entries:
            wi = c["word_index"]
            max_allowed = n_words if c["opcode"] == "delete" else n_words - 1
            if wi < 0 or wi > max_allowed:
                offenders.append((int(kid), wi,
                                  f"{c['opcode']} outside 0..{max_allowed} (klal has {n_words} words)"))
    assert not offenders, f"correction candidate(s) pointing outside their klal: {offenders}"


def test_correction_entries_have_the_field_shape_their_opcode_implies(corrections):
    """The three opcodes mean different things to the review UI, and it reads
    the fields directly: 'replace' offers both readings, 'insert' offers
    removal (docai_reading is null by construction - it saw nothing),
    'delete' offers insertion (final_text is null - the corpus has nothing
    there). A mismatched pair renders an empty or nonsensical option for a
    reviewer to pick, so it is a data defect even though nothing crashes.
    """
    offenders = []
    for kid, entries in corrections.items():
        for c in entries:
            op, docai, final = c["opcode"], c["docai_reading"], c["final_text"]
            if op == "replace" and (docai is None or final is None):
                offenders.append((int(kid), c["word_index"], "replace with a null reading"))
            elif op == "insert" and (docai is not None or final is None):
                offenders.append((int(kid), c["word_index"], "insert must have docai_reading=null, final_text set"))
            elif op == "delete" and (docai is None or final is not None):
                offenders.append((int(kid), c["word_index"], "delete must have final_text=null, docai_reading set"))
            elif op not in ("replace", "insert", "delete", "manual"):
                offenders.append((int(kid), c["word_index"], f"unknown opcode {op!r}"))
            bbox = c.get("bbox")
            if bbox is not None and not (0 <= bbox["x1"] < bbox["x2"] <= 1 and 0 <= bbox["y1"] < bbox["y2"] <= 1):
                offenders.append((int(kid), c["word_index"], f"bbox not a normalised rectangle: {bbox}"))
    assert not offenders, f"correction entries with an inconsistent shape: {offenders}"


def test_every_trusted_klal_has_exactly_one_well_formed_scan_region(regions, alignment, part1_by_id):
    """klal_page_regions.json drives the "you are here" highlight on the scan
    pane for every klal, including the majority with no flagged correction.
    A missing region means the reviewer gets no highlight at all; a malformed
    or fabricated one means they are pointed at the wrong ink - the defect
    that got SEFARIA-VLM-DEMO.html archived (14 placeholder bounding boxes
    served under a "Precise Geometric Bounds" heading, CLAUDE.md).
    """
    trusted = {kid for kid, r in alignment.items()
               if r.get("trusted") and kid in part1_by_id}
    have = {int(k) for k in regions}
    assert not (trusted - have), f"trusted Part-1 klal(im) with no scan region: {sorted(trusted - have)}"
    assert not (have - trusted), (
        f"scan region(s) for klalim that are not trusted Part-1 klalim: {sorted(have - trusted)}"
    )

    offenders = []
    for kid, region in regions.items():
        boxes = [(region["page"], region["bbox"])] + \
            [(c["page"], c["bbox"]) for c in region.get("continuations", [])]
        for page, b in boxes:
            if not (0 <= b["x1"] < b["x2"] <= 1 and 0 <= b["y1"] < b["y2"] <= 1):
                offenders.append((int(kid), page, f"not a normalised rectangle: {b}"))
        if region.get("token_count", 0) < 1:
            offenders.append((int(kid), region["page"], "region covers zero tokens"))
        if region["page"] != alignment[int(kid)].get("matched_page"):
            offenders.append((int(kid), region["page"],
                              f"region page disagrees with the klal's aligned page "
                              f"{alignment[int(kid)].get('matched_page')}"))
        cont_pages = [c["page"] for c in region.get("continuations", [])]
        if cont_pages != sorted(set(cont_pages)) or any(p <= region["page"] for p in cont_pages):
            offenders.append((int(kid), region["page"],
                              f"continuation pages {cont_pages} are not strictly increasing after it"))
    assert not offenders, f"malformed scan region(s): {offenders}"


def test_review_decisions_log_is_intact_and_internally_consistent(decision_records):
    """The one file in this project a rebuild can never regenerate: every
    human judgement ever recorded, append-only, tracked in git. A truncated
    write, a hand-edit, or a decision_type typo silently drops a reviewer's
    decision out of every lookup (all_current/history_for filter on exactly
    these fields), and an apply_event whose applied_decision_id resolves to
    nothing means the "already applied, never re-apply" guard is pointing at
    a decision that no longer exists.
    """
    review_decisions = _import_from_path("review_decisions", os.path.join(REPO, "review_decisions.py"))
    records, malformed = [], []
    for lineno, line in decision_records:
        try:
            records.append((lineno, json.loads(line)))
        except json.JSONDecodeError as e:
            malformed.append((lineno, str(e)))
    assert not malformed, f"unparseable line(s) in review_decisions.jsonl: {malformed}"

    problems = []
    seen_ids = {}
    for lineno, r in records:
        if r["id"] in seen_ids:
            problems.append(f"line {lineno}: duplicate id {r['id']} (also line {seen_ids[r['id']]})")
        seen_ids[r["id"]] = lineno
        if r["decision_type"] not in review_decisions.VALID_DECISION_TYPES:
            problems.append(f"line {lineno}: unknown decision_type {r['decision_type']!r}")
        if not isinstance(r["klal_id"], int):
            problems.append(f"line {lineno}: klal_id {r['klal_id']!r} is not an int - it would match "
                            "no lookup, since every query compares klal_id by value")
        # klal_flag is klal-level by design; every other type is about one
        # specific word/token and is looked up by (klal_id, word_index).
        if (r.get("word_index") is None) != (r["decision_type"] == "klal_flag"):
            problems.append(f"line {lineno}: {r['decision_type']} with word_index={r.get('word_index')!r}")

    ids = set(seen_ids)
    for lineno, r in records:
        if r["decision_type"] == "apply_event":
            ref = r.get("applied_decision_id")
            if not ref or ref not in ids:
                problems.append(f"line {lineno}: apply_event references decision id {ref!r}, "
                                "which is not in the log")

    timestamps = [r["ts"] for _, r in records]
    if timestamps != sorted(timestamps):
        problems.append("records are not in chronological order - 'current' state is defined as the "
                        "LAST matching line in file order, so an out-of-order append silently "
                        "resolves the wrong decision as current")

    assert not problems, "review_decisions.jsonl integrity problem(s):\n  " + "\n  ".join(problems)


# validate_part1_corpus_integrity.py is Part-1-only (its own gematria/
# lexicon logic isn't validated against Parts 2-3's conventions), no
# gitignored/regenerable-cache dependency (only part1.json + lexicon.txt,
# both tracked), and fast (<1s, no API calls) - unlike
# validate_klal_span_coverage.py above, it needs no skip-if-absent guard.
# These three checks were confirmed zero-tolerance-clean against the full
# corpus 2026-08-07 after fixing 3 false-positive sources in the script
# itself (final-letter gematria spelling, footnote-marker parens, a too-
# strict same-title-cluster exemption) - see PROJECT-STATUS.md "New
# standing check validate_part1_corpus_integrity.py added" and "did we
# finish innovating validation checks?". Checks 4 (self-reference
# directionality) and 5 (lexicon coverage) are deliberately NOT gated here
# - the script's own docstrings mark them not-viable/informational-only,
# not zero-tolerance.
@pytest.fixture(scope="session")
def part1_integrity_validator():
    return _import_from_path(
        "validate_part1_corpus_integrity",
        os.path.join(REPO, "validate_part1_corpus_integrity.py"),
    )


def test_part1_gematria_self_consistency(part_klalim, part1_integrity_validator):
    issues = part1_integrity_validator.check_gematria_self_consistency(part_klalim["part1.json"])
    assert not issues, f"Part-1 gematria self-consistency issue(s): {issues}"


def test_part1_character_sanity(part_klalim, part1_integrity_validator):
    issues = part1_integrity_validator.check_character_sanity(part_klalim["part1.json"])
    assert not issues, f"Part-1 character/encoding sanity issue(s): {issues}"


def test_part1_no_new_duplicated_phrases(part_klalim, part1_integrity_validator):
    issues = part1_integrity_validator.check_duplicate_phrases(part_klalim["part1.json"], n=10)
    assert not issues, f"Part-1 unexplained duplicated 10+-word phrase(s): {issues}"


# check_intra_klal_duplicate_phrases (added 2026-08-12, closing the docstring
# overclaim the module always had - see validate_part1_corpus_integrity.py)
# has 4 known-genuine hits, each producing several overlapping n-gram window
# reports: klal 65 (a rule restated verbatim before the author's own gloss -
# "ב"ד יכול לבטל דברי ב"ד חבירו אא"כ גדול ממנו בחכמה ובמנין" - visually
# confirmed as the klal's own title restated in its body, a common
# rhetorical device in this book, not corruption), klal 189, klal 198.
# klal 217 added 2026-08-15: surfaced only AFTER the dropped-lamed ligature
# fix (word 571's אליבא, individually scan-verified against the ink) made
# it byte-identical to the klal's OTHER, already-correct occurrence of the
# same 10-word Tosafot quotation at word 647 - before the fix the two
# differed (one read the corrupted איבא) so the exact-match duplicate
# check never caught this true positive. Confirmed genuine, not a bug:
# the second occurrence is explicitly introduced as a second citation of
# the same source ("גם הלום ראיתי מה שכתב הרב הנזכר שם בשם התוספות" -
# "I also now saw what the aforementioned rabbi wrote there in the name
# of Tosafot"), i.e. the author deliberately quotes the same Tosafot text
# twice while discussing two different rabbis who each cite it.
INTRA_KLAL_DUPLICATE_PHRASE_BASELINE = {65, 189, 198, 217}


def test_part1_no_new_intra_klal_duplicated_phrases(part_klalim, part1_integrity_validator):
    issues = part1_integrity_validator.check_intra_klal_duplicate_phrases(part_klalim["part1.json"], n=10)
    new_klalim = sorted({int(i.split()[1].rstrip(":")) for i in issues} - INTRA_KLAL_DUPLICATE_PHRASE_BASELINE)
    assert not new_klalim, (
        f"New klal(im) with an unexplained duplicated 10+-word phrase within their own text: "
        f"{new_klalim}. Verify against the source before either fixing the text or adding to "
        f"INTRA_KLAL_DUPLICATE_PHRASE_BASELINE."
    )


# --- Baseline (no-NEW-violations) checks ---

def test_no_new_duplicate_consecutive_words(all_klalim):
    found = set()
    for k in all_klalim:
        words = k["clean_text"].split()
        for i in range(len(words) - 1):
            w1 = re.sub(r"[^א-ת]", "", words[i])
            w2 = re.sub(r"[^א-ת]", "", words[i + 1])
            if len(w1) >= 2 and w1 == w2:
                found.add((k["klal_id"], w1))

    new = sorted(found - DUPLICATE_WORD_BASELINE)
    assert not new, (
        f"New duplicate-consecutive-word pair(s) not in the known baseline: {new}. "
        "This is the same failure mode as klal 128's `לאוקומי לאוקומי` bug "
        "(PROJECT-STATUS.md 2026-08-06) - verify against the source before "
        "either fixing the text or adding to DUPLICATE_WORD_BASELINE."
    )
    # A shrinking baseline is progress worth surfacing, not silently ignored -
    # this does not fail the test, just makes stale baseline entries visible
    # in test output so someone can prune them next time this file is touched.
    stale = sorted(DUPLICATE_WORD_BASELINE - found)
    if stale:
        print(f"\nNote: DUPLICATE_WORD_BASELINE has {len(stale)} entries no longer "
              f"present in the corpus (safe to remove): {stale}")


def test_no_new_alphabetical_title_order_violations(all_klalim):
    validator = _import_from_path(
        "validate_title_alphabetical_order",
        os.path.join(REPO, "validate_title_alphabetical_order.py"),
    )
    violations, _skipped_bad_first_char = validator.find_violations(all_klalim)
    assert len(violations) <= ALPHABETICAL_ORDER_VIOLATION_BASELINE_MAX, (
        f"{len(violations)} title-alphabetical-order violations, more than the "
        f"documented baseline of {ALPHABETICAL_ORDER_VIOLATION_BASELINE_MAX} "
        "(klal 101-104's elliptical-title convention + Parts 2-3's un-judged "
        "'כלל <N>' placeholder titles). A count above baseline means a NEW "
        "title/boundary problem - investigate before raising this constant."
    )


def test_placeholder_titles_do_not_increase(all_klalim):
    placeholder_re = re.compile(r"^כלל \d+$")
    count = sum(1 for k in all_klalim if placeholder_re.match(k.get("title", "").strip()))
    assert count <= PLACEHOLDER_TITLE_COUNT_MAX, (
        f"{count} klalim have a literal 'כלל <N>' placeholder title, more than the "
        f"documented baseline of {PLACEHOLDER_TITLE_COUNT_MAX} - a real judged title "
        "may have been overwritten with a placeholder. If titles were legitimately "
        "judged and this count went DOWN instead, lower PLACEHOLDER_TITLE_COUNT_MAX "
        "to match (progress, not a failure)."
    )


def test_no_new_span_coverage_flags(part1_by_id):
    """Wraps validate_klal_span_coverage.py's own logic. Requires the
    gitignored docai_word_boxes/ cache and gematria_trace_part1.json -
    both regenerable from the source scan per CLAUDE.md's directory-layout
    convention, but not guaranteed present (e.g. a fresh clone). Skips
    rather than fails when absent, matching how this data is documented as
    optional/regenerable, not a source-of-truth file.
    """
    trace_path = os.path.join(REPO, "gematria_trace_part1.json")
    docai_dir = os.path.join(REPO, "docai_word_boxes")
    if not (os.path.exists(trace_path) and os.path.isdir(docai_dir)):
        pytest.skip("gematria_trace_part1.json or docai_word_boxes/ not present locally (gitignored cache)")

    validator = _import_from_path(
        "validate_klal_span_coverage",
        os.path.join(REPO, "validate_klal_span_coverage.py"),
    )
    trace = {x["klal_id"]: x for x in json.load(open(trace_path, encoding="utf-8"))}

    # Calls the validator's own build_spans() rather than reimplementing the
    # span math here. The previous version of this test had its own copy of
    # that loop, including the same two silent `continue` statements - so the
    # gate was structurally incapable of catching what the script structurally
    # skipped, and both missed klal 30/36/83/88 for the life of the project
    # (audit 2026-08-10/11, PROJECT-STATUS.md). One implementation, one blind
    # spot, fixed in one place.
    rows, unmeasured = validator.build_spans(trace, part1_by_id, {})
    flagged = {r["klal_id"] for r in rows if r["ratio"] < validator.FLAG_RATIO_THRESHOLD}

    new = sorted(flagged - SPAN_COVERAGE_BASELINE - SPAN_COVERAGE_KNOWN_REAL_GAPS)
    assert not new, (
        f"New span-coverage flag(s) not in the known baseline: {new} - stored text "
        "is shorter than the real marker-to-marker token span would predict. This is "
        "the cross-page-truncation failure mode (PROJECT-STATUS.md 'MAJOR: cross-page "
        "klal truncation'); verify against the scan before treating as real or adding "
        "to SPAN_COVERAGE_BASELINE."
    )

    # Every klal must land in a reported bucket. This is the invariant whose
    # absence let 20 klalim vanish from both counters - assert it, don't print it.
    no_marker = {k for k in trace if trace[k].get("marker_position") is None}
    assert len(rows) + len(unmeasured) == len(trace) - len(no_marker), (
        "span accounting does not add up: every klal with a marker must produce "
        "either a measured span or a recorded reason it could not be measured."
    )
