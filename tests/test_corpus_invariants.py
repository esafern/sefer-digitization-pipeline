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
leaks, the no-text-available placeholder set, non-empty title/clean_text).
These have no known legitimate exception anywhere in the corpus, per the
PROJECT-STATUS.md section cited in each test.
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
    (29, "לא"), (29, "שור"), (29, "צדה"), (41, "אלא"), (54, "הן"),
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
# klal 106/175. None of these six are corpus bugs as currently
# understood; a genuinely new entry here is the same failure mode as the
# original klal-2/klal-4 cross-page truncation bug this validator was
# built to catch.
SPAN_COVERAGE_BASELINE = {106, 123, 175, 179, 181, 193}


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


def test_title_and_clean_text_are_never_empty(all_klalim):
    empty_titles = [k["klal_id"] for k in all_klalim if not k.get("title", "").strip()]
    empty_text = [k["klal_id"] for k in all_klalim if not k.get("clean_text", "").strip()]
    assert not empty_titles, f"klal(im) with an empty title field: {empty_titles}"
    assert not empty_text, f"klal(im) with empty clean_text: {empty_text}"


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
    violations = validator.find_violations(all_klalim)
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


def test_no_new_span_coverage_flags():
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
    part1 = {k["klal_id"]: k for k in _load_klalim(os.path.join(REPO, "part1.json"))}
    ids = sorted(trace)
    cache = {}

    flagged = []
    for idx, kid in enumerate(ids):
        x = trace[kid]
        if x.get("marker_position") is None or idx + 1 >= len(ids):
            continue
        next_kid = ids[idx + 1]
        nx = trace[next_kid]
        if nx.get("marker_position") is None:
            continue

        page, next_page = x["page"], nx["page"]
        tokens_this = validator.get_page(cache, page)
        if tokens_this is None:
            continue

        if next_page == page:
            span_tokens = nx["marker_position"] - x["marker_position"]
        elif next_page == page + 1:
            tokens_next = validator.get_page(cache, next_page)
            if tokens_next is None:
                continue
            span_tokens = (len(tokens_this) - x["marker_position"]) + nx["marker_position"]
        else:
            continue

        if not span_tokens:
            continue
        stored_words = len(part1[kid]["clean_text"].split()) if kid in part1 else 0
        if stored_words / span_tokens < validator.FLAG_RATIO_THRESHOLD:
            flagged.append(kid)

    new = sorted(set(flagged) - SPAN_COVERAGE_BASELINE)
    assert not new, (
        f"New span-coverage flag(s) not in the known baseline: {new} - stored text "
        "is shorter than the real marker-to-marker token span would predict. This is "
        "the cross-page-truncation failure mode (PROJECT-STATUS.md 'MAJOR: cross-page "
        "klal truncation'); verify against the scan before treating as real or adding "
        "to SPAN_COVERAGE_BASELINE."
    )
