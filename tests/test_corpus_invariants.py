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
import collections
import json
import os
import re
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# pipeline/ and tools/ modules use bare `import corpus_io` etc. - they need
# their directories on sys.path for importlib's exec_module to resolve those
# imports. Same approach as test_pipeline_logic.py.
sys.path.insert(0, os.path.join(REPO, "pipeline"))
sys.path.insert(0, os.path.join(REPO, "tools"))
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
# klal 65 ADDED 2026-08-17: NOT truncation, a marker-position extraction
# artifact. Fixed a real klal-boundary bug that day (see PROJECT-STATUS.md
# "klal 65/66 boundary fix"): part1.json had klal 65's clean_text wrongly
# absorbing klal 66's entire title-phrase ("ב"ד יכול לבטל דברי ב"ד חבירו
# אא"כ גדול ממנו בחכמה ובמנין • נלע"ד דהיינו דוקא", 15 words) plus a
# duplicated copy of klal 66's own "סו" marker, moved (scan-verified, 600
# and 4800 DPI crops of berlin_square_corrected.pdf p.34) to the front of
# klal 66 where it belongs. gematria_trace_part1.json's marker_position for
# klal 66 (81) is itself a raw-docai-extraction-order artifact: the bold
# marginal "סו" glyph was tokenized AFTER the full line of body text
# ("ב"ד יכול...דוקא") it visually precedes, rather than before it - the
# rendered page shows "סו" plainly at the START of its own line, not
# interposed mid-sentence after "דוקא" as raw token order implies. That
# same artifact is almost certainly what fooled the original chunker into
# duplicating the marker in the first place. Because build_spans() measures
# marker-to-marker using this same mis-ordered position, klal 65's now-
# CORRECT 60-word length reads as short against a 76-token expected span
# that was never real - the span math has no way to know the marker token
# it anchored on was extracted out of visual order. Not wired as a general
# fix (a systemic mis-ordering check is future work, not scoped here);
# baselined as an explained false positive for this one instance, scan-
# verified directly, not inferred.
# klalim 22 and 84 ADDED 2026-08-23, and klal 15 REMOVED, with the
# verification that the 2026-08-23 widening of this set skipped (code review,
# finding H5 - the set was widened to absorb three newly-failing klalim with no
# recorded reason, inside a constant whose whole contract is "scan-verified
# false positive, not inferred").
#
# What actually happened: `decc73a` added (ט, פ) to CONFUSION_PAIRS, which let
# build_gematria_trace.py finally resolve the markers for klalim 16, 22 and 84
# (all three went marker_not_found_in_window -> ok). They did not newly BREAK;
# they became MEASURABLE for the first time. Klal 15 correctly left this set for
# the same reason - its span used to run past klal 16's missing marker all the
# way to klal 17, inflating its expected token count; now it is bounded
# correctly.
#
# Klalim 22 (ratio 0.84) and 84 (0.80) are genuine false positives, and the
# cause is mechanical: validate_klal_span_coverage.py's get_page() does NOT
# strip page furniture (its module docstring describes the furniture-stripping
# in an ARCHIVED script, reconstruct_crosspage_v4.py, not in itself), so every
# cross-page span counts one page's running header and section header as body
# tokens. Checked directly by diffing each span's tokens against stored text:
# klal 22's 7 unaccounted tokens are ['כך','סיי','כייה','יר','מלאכי','כללי',
# 'האלף'] and klal 84's 6 are ['פר','בעיא','יך','מלאכי','כללי','הבית'] - i.e.
# the misread marker plus `יד מלאכי` (the running header, its ד read as ר/ך,
# which is why an exact-match furniture list would never catch it) plus the
# `כללי האלף`/`כללי הבית` section header. No body text is missing from either.
# This is also exactly why the cross-page mean ratio sits at 0.91 against the
# same-page 1.11 the 0.85 threshold was tuned on.
#
# Klal 16 is NOT here - it was in this set from 2026-08-23 until the same
# verification found real missing text. See SPAN_COVERAGE_KNOWN_REAL_GAPS.
SPAN_COVERAGE_BASELINE = {22, 65, 83, 84, 106, 123, 130, 175, 195}

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
#   {} -> {16} 2026-08-23. The next one turned up, and it turned up because a
#     code review asked why this set's SIBLING (SPAN_COVERAGE_BASELINE) had
#     silently grown by three klalim (finding H5). Klal 16 was put in the
#     false-positive baseline; it is not a false positive.
#
#     Klal 16's stored clean_text ENDS MID-SENTENCE on the connective `אהא`
#     ("regarding this"), which demands a continuation. The continuation is
#     printed, and it is the first two body lines of page 20:
#       אף על גב דלא שייך כלל אברייתא דמייתי מדכתבו דר"י ור"ל בסברא בעלמא
#       פליגי ולא תליא מלתייהו כלל בהלכה דקאמר ראב"ע ודוק :
#     (The last two words were first transcribed `ראב"י דוק:` from a first-pass
#     render and corrected to `ראב"ע ודוק :` after re-rendering that line at 5x -
#     the raw DocAI tokens had it right and the first visual read did not.
#     Lesson 17: a borderline reading is a reason to render bigger, not to settle
#     it from the first look. review_decisions.jsonl is append-only, so the
#     correction is a superseding klal_flag, a31c9a08f8fe, not an edit.)
#     ~24 words, terminating in a colon, immediately before klal 17's own bold
#     `יז` marker and its unrelated opening ("אין הלכה כתלמיד במקום הרב").
#
#     VERIFIED TWO INDEPENDENT WAYS, per Lesson 4 (raw data is not
#     automatically right) and Lesson 14 (render and read, do not infer):
#       1. Raw DocAI tokens - the run appears contiguous at page 20 tokens
#          6..23, y 0.086-0.118, x 0.121-0.829, i.e. a full-width first body
#          line directly under the running header.
#       2. A direct render of images/pdf_pages/page_20.png, read visually:
#          running header, then those two body lines, then klal 17's marker.
#     Ruled out the klal 9/10 failure mode (text stored in the NEIGHBOUR
#     rather than missing): klal 17 begins cleanly with its own marker and a
#     different topic, and `מלתייהו` occurs nowhere in part1.json at all.
#
#     NOT FIXED HERE. This is a DATA ISSUE, not a bug - per START_HERE.md it
#     is fixed through the review-decision pipeline against the scan, never a
#     direct part1.json hand-edit, and applying it needs its own go-ahead
#     (same two-step rule as every correction this pipeline has applied).
#     Flagged through the pipeline (klal_flag dcd9c031b83c, superseded by
#     a31c9a08f8fe for the corrected tail), then APPLIED the same day under
#     explicit user authorization - see this constant's own {16} -> {} entry
#     below and PROJECT-STATUS.md.
#
#     The rest of SPAN_COVERAGE_BASELINE was swept the same way on 2026-08-23
#     (tools/check_span_shortfall.py, built for this) and every other member
#     came back an artifact - klal 83's shortfall is klal 82's tail landing in
#     its span via the klal 65/66 marker-order artifact (8 of its 11 unaccounted
#     tokens are stored verbatim in klal 82, and a render of page 38 shows
#     `פב בשל ... קפ"ג :` closing klal 82 before `פג בשל` opens klal 83);
#     klalim 106/123/130/195 are page furniture plus single-token alignment
#     misses whose words are all present in stored text as exact or one-character
#     variants. Klal 16 is the only real gap the sweep found.
#   {16} -> {} 2026-08-23, same day, FIXED. The 23 missing words were applied
#     through the review-decision pipeline (manual_correction 60a17ad89fb2,
#     insert at word_index 163 after klal 16's last stored word `אהא`), not
#     hand-edited. Klal 16 went 163 -> 186 words and DROPPED OFF
#     validate_klal_span_coverage.py's flagged list entirely (10 spans -> 9),
#     which is the check that found it. Independently corroborated: a fresh
#     build_corrections_dataset.py pass generates ZERO new candidates anywhere
#     at word_index >= 163, i.e. the DocAI-vs-stored diff finds no disagreement
#     in any of the 23 inserted words - the transcription matches the scan's own
#     tokens exactly.
# This set must SHRINK as content is reconstructed and must never grow
# silently - a klal arriving here is real missing text, not a measurement
# artifact. Keep this mechanism (not delete it) for the next one that turns up.
SPAN_COVERAGE_KNOWN_REAL_GAPS = set()


def _load_klalim(path):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
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
    with open(os.path.join(REPO, "corrections_part1.json"), encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def regions():
    with open(os.path.join(REPO, "klal_page_regions.json"), encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def alignment():
    with open(os.path.join(REPO, "part1_header_anchored_alignment.json"), encoding="utf-8") as f:
        align = json.load(f)
    return {r["klal_id"]: r for r in align}


@pytest.fixture(scope="session")
def all_alignment():
    """Part 1 + 2 + 3's own header-anchored alignment files, merged - klal_id
    ranges are disjoint (1-222 / 223-444 / 445-667) so a plain dict update
    never collides. klal_page_regions.json was generalized to cover all
    three parts 2026-08-21 (see PROJECT-STATUS.md); this fixture lets the
    region-coverage test below check against all 667 klalim, not just
    Part 1's 222."""
    combined = {}
    for fname in ("part1_header_anchored_alignment.json",
                  "part2_header_anchored_alignment.json",
                  "part3_header_anchored_alignment.json"):
        with open(os.path.join(REPO, fname), encoding="utf-8") as f:
            for r in json.load(f):
                combined[r["klal_id"]] = r
    return combined


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


def test_no_scan_watermark_in_clean_text(all_klalim):
    """The Google Books footer is not corpus content, and Latin script is the
    cheapest possible way to say so in a Hebrew work.

    ADDED 2026-08-26. This invariant did not exist, and its absence is why
    `Digitized by Google` sat inside the text of **12 klalim** (250, 290, 333,
    357, 380, 385, 414, 442, 553, 580, 616, 665) with all 289 gated tests
    passing - test_no_page_header_contamination above only matches the HEBREW
    running header, and the watermark is Latin, so nothing looked. The 12 shipped
    into `sefaria_export/version_hebrew.json` under real citation addresses.
    tools/reconstruct_placeholder_klalim.py wrote them by walking a page seam
    straight through the footer, because `strip_page_furniture()` keys on
    `hebrew_letters_only()`, which maps every Latin token to "". See
    PROJECT-STATUS.md item 20. Zero tolerance, not a baseline: no klal of this
    work contains a Latin character.
    """
    offenders = [k["klal_id"] for k in all_klalim if re.search(r"[A-Za-z]", k["clean_text"])]
    assert not offenders, (
        f"Latin script in clean_text for klal(im) {offenders} - this is the Google "
        "Books scan watermark ('Digitized by Google'), never real content. It "
        "reaches the corpus through a page-seam reconstruction; see "
        "PROJECT-STATUS.md item 20 and tools/reconstruct_placeholder_klalim.py's "
        "_is_scan_furniture()."
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
    """PART1_MAX_KLAL = 222 is max(klal_id) in part1.json, i.e. data, not a
    chosen number. Added 2026-08-15 during the hard-wired-value audit, when it
    was written out independently in three live files
    (build_corrections_dataset.py, build_klal_page_regions.py,
    review_server.py) with no shared definition and nothing tying any of the
    three back to the corpus: if Part 1's klal count ever moves (a split/merge,
    Success Criterion #2's own failure mode) and only some copies are updated,
    every failure is silent - a klal simply stops getting candidates, stops
    getting a scan region, or stops being served to the dashboard, with no
    error anywhere.

    UPDATED 2026-08-17: the three copies are gone - all three modules (and
    corpus_io itself, checked here too) now read one definition,
    corpus_io.PART1_MAX_KLAL. That removes the "three literals must agree with
    each other" half of this test's job structurally, which is the better fix
    than a test policing it. The half that still matters and is still checked
    here is the one a shared constant cannot fix by itself: the constant must
    agree with the LIVE corpus. Each module is still read through its own
    attribute rather than corpus_io's, so a module re-introducing a private
    literal is caught rather than silently passing.
    Zero tolerance: derive-or-assert, not "usually agrees" (CLAUDE.md
    Lesson 13's argument, applied to a constant rather than a file).
    """
    part1_max = max(k["klal_id"] for k in part_klalim["part1.json"])
    modules = {
        "corpus_io.py": None,
        "build_corrections_dataset.py": None,
        "build_klal_page_regions.py": None,
        "review_server.py": None,
    }
    for name in modules:
        mod = _import_from_path(name.removesuffix(".py"), os.path.join(REPO, "pipeline", name))
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


def test_part23_max_klal_constants_agree_with_the_corpus(part_klalim):
    """The Part 2/3 bounds are data, exactly like PART1_MAX_KLAL above.

    ADDED 2026-08-31, the remedy finding S5 asked for on 2026-08-25 and the
    2026-08-27 review restated as #6. Until now `223`, `444` and `445` were
    inline literals in review_server.py's _get_part_num_for_klal() and
    _load_klalim() - the one part-classifying pair in the codebase - with no
    constant and, unlike PART1_MAX_KLAL, nothing tying them to the corpus at
    all. The failure mode is the silent one this file's sibling test above
    describes: a klal added to or removed from part2/part3 and the dashboard
    serves the wrong part, or drops a klal from every part, with no error.

    Checks the same two properties the Part 1 test checks, for the same
    reasons: the constants equal the live max, and each part is a contiguous
    block - because `klal_id <= PART2_MAX_KLAL` only means "in Part 2" if the
    ranges partition without gaps.
    """
    part2_max = max(k["klal_id"] for k in part_klalim["part2.json"])
    part3_max = max(k["klal_id"] for k in part_klalim["part3.json"])

    modules = {}
    for name in ("corpus_io.py", "review_server.py"):
        mod = _import_from_path(name.removesuffix(".py"), os.path.join(REPO, "pipeline", name))
        modules[name] = (mod.PART2_MAX_KLAL, mod.PART3_MAX_KLAL,
                         mod.PART2_MIN_KLAL, mod.PART3_MIN_KLAL)

    expected = (part2_max, part3_max,
                max(k["klal_id"] for k in part_klalim["part1.json"]) + 1,
                part2_max + 1)
    disagreeing = {n: v for n, v in modules.items() if v != expected}
    assert not disagreeing, (
        f"Part 2/3 constants disagree with the live corpus "
        f"(PART2_MAX/PART3_MAX/PART2_MIN/PART3_MIN should be {expected}): "
        f"{disagreeing}."
    )

    # Contiguity, per part and across the seam - the `<=` cutoffs in
    # _get_part_num_for_klal depend on it.
    p2 = sorted(k["klal_id"] for k in part_klalim["part2.json"])
    p3 = sorted(k["klal_id"] for k in part_klalim["part3.json"])
    assert p2 == list(range(expected[2], part2_max + 1)), "part2.json is not a contiguous block"
    assert p3 == list(range(expected[3], part3_max + 1)), "part3.json is not a contiguous block"


def test_every_klal_classifies_into_the_part_whose_file_it_came_from(part_klalim):
    """_get_part_num_for_klal() must agree with which file the klal is IN.

    The constants test above checks the numbers; this checks the function that
    uses them, against all 667 klalim rather than against the boundaries alone.
    An off-by-one at a seam (`<` for `<=`) passes a boundary-value test written
    from the same wrong assumption and fails here.
    """
    rs = _import_from_path("review_server", os.path.join(REPO, "pipeline", "review_server.py"))
    wrong = []
    for fname, expected_part in (("part1.json", 1), ("part2.json", 2), ("part3.json", 3)):
        for k in part_klalim[fname]:
            got = rs._get_part_num_for_klal(k["klal_id"])
            if got != expected_part:
                wrong.append((k["klal_id"], fname, got))
    assert not wrong, f"klalim classified into the wrong part: {wrong[:10]} ({len(wrong)} total)"


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


def test_no_rendered_manual_correction_hides_a_machine_candidate(corrections, part1_by_id):
    """review_frontend/app.js builds its word map as
    `k.corrections.forEach(c => { if (c.opcode !== 'delete') byIndex[c.word_index] = c })`
    - a last-write-wins dict. review_server.api_klal() appends synthetic
    manual_correction entries AFTER the machine candidates, so a manual entry
    at the same word_index silently replaces the machine candidate: the
    reviewer sees a green Human-Decided word and never learns the vision pass
    disputed it. review_server.py's own comment asserts the collision "only
    ever" happens one way or the other, on the grounds that app.js offers the
    manual panel only on an unflagged word.

    That holds going FORWARD, but it is not a property of the data: measured
    2026-08-16, 78 (klal_id, word_index) positions in the decisions log
    already collide with a live machine candidate - the manual decisions were
    recorded first and a later rebuild generated candidates at those
    positions. All 78 are invisible today only because api_klal()'s drift
    check drops a manual decision whose original_word has moved (they were
    applied, so it has), leaving exactly 1 manual decision rendering at all
    and 0 collisions. A future rebuild that produced a candidate at a
    still-valid manual decision's position would resurrect the whole class,
    silently. This test is the check that assumption never had (Lesson 8: a
    cheap mechanical sweep catches what an argument about the UI cannot).

    ASSERTION CHANGED 2026-08-24, and STRENGTHENED rather than relaxed.

    The predicted moment arrived: a reviewer working klal 91 recorded manual
    corrections at w453 and w524, both live machine-candidate positions, and
    this test fired for the first time. The reported symptom matched exactly -
    "the last two disputes weren't properly highlighted" - because the manual
    entry replaced the machine one and took its bbox, its docai/consensus
    readings and its vision verdict with it.

    Forbidding the collision was never the right fix: a human deciding a word
    the machine also flagged is NORMAL and will keep happening. api_klal() now
    MERGES the decision onto the existing candidate instead of appending a
    second entry, so the collision is safe by construction. This test therefore
    stops asserting "no collision" (which would now fail on correct behaviour)
    and starts asserting the property that actually matters: at a collision
    position, exactly ONE entry is served and it still carries the machine
    candidate's data.
    """
    review_server = _import_from_path("review_server", os.path.join(REPO, "pipeline", "review_server.py"))
    machine = {
        (int(kid), c["word_index"])
        for kid, entries in corrections.items() for c in entries if c.get("opcode") != "delete"
    }
    collisions = []
    for (klal_id, word_index), record in review_server.rd.all_current("manual_correction").items():
        klal = part1_by_id.get(klal_id)
        if klal is None:
            continue
        words = (klal.get("clean_text") or "").split(" ")
        original_word = (record.get("candidate_snapshot") or {}).get("original_word")
        # Only a decision that still RENDERS can hide anything.
        if not review_server._word_matches(words, word_index, original_word):
            continue
        if (klal_id, word_index) in machine:
            collisions.append((klal_id, word_index))

    offenders = []
    for klal_id, word_index in collisions:
        served = [c for c in review_server.api_klal(klal_id)["corrections"]
                  if c.get("word_index") == word_index and c.get("opcode") != "delete"]
        if len(served) != 1:
            offenders.append((klal_id, word_index, f"{len(served)} entries served, expected 1"))
            continue
        entry = served[0]
        if entry.get("current_decision") is None:
            offenders.append((klal_id, word_index, "merged entry lost the human decision"))
        elif entry.get("opcode") == "manual" or entry.get("docai_reading") is None:
            offenders.append((klal_id, word_index,
                              "machine candidate's data was replaced, not merged"))
    assert not offenders, (
        f"{len(offenders)} collision position(s) do not merge correctly: {offenders}. "
        "app.js's word map is last-write-wins, so two entries at one index means the "
        "machine candidate - its bbox, its readings, its vision verdict - is silently "
        "not shown to the reviewer."
    )


def test_every_served_flag_has_a_dashboard_label(corrections):
    """review_frontend/app.js falls back to a bare 'Flagged' for any flag
    review_server.FLAG_LABELS doesn't know, which is indistinguishable from a
    typo'd flag name. tests/test_pipeline_logic.py checks the same property
    against every flag classify() CAN emit; this checks the ones actually on
    disk right now, which also covers a flag introduced by hand-editing.
    """
    review_server = _import_from_path("review_server", os.path.join(REPO, "pipeline", "review_server.py"))
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
            if op == "replace" and final is None:
                offenders.append((int(kid), c["word_index"], "replace with no stored text"))
            elif op == "replace" and docai is None:
                # BROADENED 2026-08-23, deliberately and narrowly. Until the
                # multi-witness synthesizer existed, every 'replace' came from
                # the DocAI-vs-stored diff, so "docai_reading is null" and "this
                # item offers the reviewer nothing to choose against" were the
                # same statement. They no longer are: a consensus dispute
                # (pipeline/synthesize_multi_witness.py) is a position where
                # DocAI AGREED with the corpus and two OTHER engines agree it is
                # wrong - genuinely null docai_reading, genuinely a real
                # alternative reading. That case is the whole point of
                # multi-witness synthesis, and it is exactly what a
                # DocAI-vs-stored diff cannot see.
                #
                # What this test actually protects is unchanged and still
                # enforced below: the UI must never render an option card with
                # nothing in it. So a replace still has to offer a real
                # alternative from SOME engine - it just no longer has to be
                # DocAI specifically. Anything with no alternative at all is
                # still an offender.
                # EXTENDED 2026-08-26 for lexical defects (stage 4b): a proposal
                # that comes from a frequency table and a dictionary rather than
                # from any engine. It still has to be renderable and it still has
                # to be attributable - `lexical_source` plays exactly the role
                # `consensus_engines` plays above. What this test protects is
                # unchanged: never an option card with nothing in it, and never a
                # reading that cannot be traced to whatever produced it.
                alternative = (c.get("consensus_reading") or c.get("vlm_reading")
                               or c.get("surya_reading") or c.get("vision_transcription")
                               or c.get("lexical_proposal"))
                if not alternative:
                    offenders.append((int(kid), c["word_index"],
                                      "replace with no alternative reading from any engine"))
                elif not (c.get("consensus_engines") or c.get("lexical_source")):
                    offenders.append((int(kid), c["word_index"],
                                      "replace with a null docai_reading but no consensus "
                                      "or lexical attribution - untraceable to its source"))
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


def test_every_trusted_klal_has_exactly_one_well_formed_scan_region(regions, all_alignment, all_klalim, part1_by_id):
    """klal_page_regions.json drives the "you are here" highlight on the scan
    pane for every klal, including the majority with no flagged correction.
    A missing region means the reviewer gets no highlight at all; a malformed
    or fabricated one means they are pointed at the wrong ink - the defect
    that got SEFARIA-VLM-DEMO.html archived (14 placeholder bounding boxes
    served under a "Precise Geometric Bounds" heading, CLAUDE.md).

    Generalized to all three parts 2026-08-21 when klal_page_regions.json
    itself was generalized (previously Part 1 only, see PROJECT-STATUS.md).
    The region-page-vs-alignment-matched_page agreement check below stays
    scoped to Part 1 only, deliberately: that same day's investigation found
    391 of 445 Parts 2-3 klalim where klal_page_regions.json's own
    independently-computed page (gematria-trace marker + Y-band against real
    DocAI tokens) disagrees with the alignment file's matched_page by up to
    177 pages - real evidence points at the ALIGNMENT file being wrong there
    (Part 1's two sources agree in all 222 cases; the alignment method isn't
    inherently unreliable), not at klal_page_regions.json - but this is
    logged as an open, unresolved finding, not something to force this test
    to silently assert as correct for Parts 2-3 before it's actually fixed.

    A "trusted" klal with genuinely no real text (clean_text is exactly
    "{gematria} כלל {klal_id}" - an auto-generated placeholder, no real
    transcription) is excluded from the "must have a region" side of this
    check - found 2026-08-21 via klal 422, whose only prior region
    (klal_page_regions.json, pre-DocAI-fix) turned out to be a spurious
    heuristic match sourced from one of the 48 corrupted docai_word_boxes
    pages (see PROJECT-STATUS.md); once that page was re-extracted cleanly,
    the spurious match correctly disappeared. 115 of 667 klalim corpus-wide
    are this kind of placeholder (0 in Part 1, all in Parts 2-3) - a real
    corpus-completeness gap, not a scan-linkage bug, and out of this test's
    scope. A placeholder CAN still legitimately have a region from the
    marker-anchored strategy (a real printed marker's position is meaningful
    independent of whether the body text has been transcribed yet - 71 of
    667 placeholder klalim get one this way) - only the "must-have-a-region"
    direction is relaxed for placeholders, not "any region implies a real,
    trusted klal_id", which still applies to placeholders too."""
    def is_placeholder(k):
        parts = (k.get("clean_text") or "").strip().split(" ")
        return len(parts) == 3 and parts[1] == "כלל" and parts[2] == str(k["klal_id"])

    all_by_id = {k["klal_id"]: k for k in all_klalim}
    trusted = {kid for kid, r in all_alignment.items()
               if r.get("trusted") and kid in all_by_id}
    must_have_region = {kid for kid in trusted if not is_placeholder(all_by_id[kid])}
    have = {int(k) for k in regions}
    assert not (must_have_region - have), f"trusted klal(im) with no scan region: {sorted(must_have_region - have)}"
    assert not (have - trusted), (
        f"scan region(s) for klalim that are not trusted klalim: {sorted(have - trusted)}"
    )

    offenders = []
    for kid, region in regions.items():
        kid = int(kid)
        boxes = [(region["page"], region["bbox"])] + \
            [(c["page"], c["bbox"]) for c in region.get("continuations", [])]
        for page, b in boxes:
            if not (0 <= b["x1"] < b["x2"] <= 1 and 0 <= b["y1"] < b["y2"] <= 1):
                offenders.append((kid, page, f"not a normalised rectangle: {b}"))
        if region.get("token_count", 0) < 1:
            offenders.append((kid, region["page"], "region covers zero tokens"))
        if kid in part1_by_id and region["page"] != all_alignment[kid].get("matched_page"):
            offenders.append((kid, region["page"],
                              f"region page disagrees with the klal's aligned page "
                              f"{all_alignment[kid].get('matched_page')}"))
        cont_pages = [c["page"] for c in region.get("continuations", [])]
        if cont_pages != sorted(set(cont_pages)) or any(p <= region["page"] for p in cont_pages):
            offenders.append((kid, region["page"],
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
    review_decisions = _import_from_path("review_decisions", os.path.join(REPO, "pipeline", "review_decisions.py"))
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
        # RELAXED 2026-08-17 (user bug report on klal 1: an AI pass's note
        # named a disputed word in prose, but nothing highlighted it - see
        # review_server.py's _word_level_ai_flags()). klal_flag can now be
        # EITHER klal-level (word_index None, the reviewer-facing "needs a
        # second look" panel) OR name one specific word (an AI pass flagging
        # a single candidate, synthesized into a highlight the same way a
        # manual_correction is) - append_decision() has always accepted
        # word_index on any type; only klal_flag actually varies. Every
        # OTHER type is still always about one specific word/token and must
        # never have word_index=None.
        if r["decision_type"] != "klal_flag" and r.get("word_index") is None:
            problems.append(f"line {lineno}: {r['decision_type']} with word_index=None")
        # The shape the relaxation above newly ADMITS was otherwise entirely
        # ungated: nothing on the write side constrains a word_index that a
        # script sets by calling append_decision() directly (api_post_klal_
        # flag never sets one, and only api_post_manual_correction rejects a
        # negative). Same reasoning as the klal_id int check above - a
        # non-int index matches no lookup - plus the negative-index case
        # review_server._word_matches() and _word_level_ai_flags() both
        # guard on the DISPLAY side, where a bad row is merely hidden. This
        # log is append-only and tracked, so a bad row written here can only
        # ever be superseded, never removed; catch it at write time instead.
        widx = r.get("word_index")
        if widx is not None and (not isinstance(widx, int) or isinstance(widx, bool) or widx < 0):
            problems.append(f"line {lineno}: {r['decision_type']} with word_index={widx!r} - "
                            "must be a non-negative int to address a real word position")

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
        os.path.join(REPO, "tools", "validate_part1_corpus_integrity.py"),
    )


def test_part1_gematria_self_consistency(part_klalim, part1_integrity_validator):
    issues = part1_integrity_validator.check_gematria_self_consistency(part_klalim["part1.json"])
    assert not issues, f"Part-1 gematria self-consistency issue(s): {issues}"


def test_part1_character_sanity(part_klalim, part1_integrity_validator):
    issues = part1_integrity_validator.check_character_sanity(part_klalim["part1.json"])
    assert not issues, f"Part-1 character/encoding sanity issue(s): {issues}"


# The 7 characters outside Part 1's documented repertoire that are ALREADY in
# the corpus as of 2026-08-16, when check_foreign_characters() was added. Each
# is a DATA issue (per CLAUDE.md's terminology): it must be resolved against
# the scan through the human review pipeline, never by a code-side rewrite or
# a blind find-replace - so they are baselined here, exactly like
# DUPLICATE_WORD_BASELINE above, rather than silently tolerated or "fixed".
#
# Keyed by (klal_id, word_index, character) so, per the PASS3_KNOWN_FALSE_
# POSITIVES precedent (2026-08-14, risk 4), only these exact positions are
# suppressed - the same character appearing anywhere ELSE in Part 1 still
# fires. Shrinking this set as instances get scan-verified and corrected is
# progress; a NEW entry appearing is a regression to investigate.
#
# Why these were invisible until now: check_character_sanity()'s stray-letter
# test is LATIN_RE = [A-Za-z], so a Greek Π (U+03A0) - a homoglyph of the
# "stray P from page furniture" its own docstring names as the motivating
# example - passed it, as did every non-Latin, non-digit, non-bracket
# character. See check_foreign_characters()'s docstring.
#
# NOT corrected here, and deliberately so, but worth recording for whoever
# scan-verifies them: all three `&` instances sit exactly where `אל` would
# read naturally - klal 69 `כגון אל אלהים ה'` (the biblical אֵל אֱלֹהִים
# יְהוָה), klal 77 `נוטה אל הודאי`, klal 167 `פנים אל פנים`. That is the same
# two-letter sequence as the confirmed alef-lamed ligature (U+FB4F) bug this
# project has already corrected 131 instances of, which raises the question
# of whether `&` is a THIRD substitution DocAI makes for that one glyph
# (alongside the bare `א` already confirmed and the bare `לא` the VLM
# produced). One frequency/semantic signal only - per Lesson 9 that is not
# enough to act on, and per Success Criterion #1 nothing may be changed
# without reading the ink.
# INDEX-KEYED, and indexes move. Every entry here shifts when a word is inserted
# or deleted earlier in its klal - apply_reviewer_decisions reindexes the FLAGS
# and the pending DECISIONS after such a change, but nothing can reindex a
# literal in a test file. When this fails after an apply, check whether the same
# character is simply at a new position before treating it as new damage.
FOREIGN_CHARACTER_BASELINE = {
    (77, 11, "&"),
}




def test_part1_no_new_characters_outside_the_documented_repertoire(
        part_klalim, part1_integrity_validator):
    """The general case that check_character_sanity()'s three narrow tests
    (Latin letters, Arabic digits, bracket balance) structurally cannot see.

    Added 2026-08-16 (round-2 audit) after a full character inventory of
    part1.json found 7 foreign-character tokens across 6 klalim that no check
    in this pipeline had ever reported - CLAUDE.md Lesson 8: the cheap
    mechanical sweep catches a different class than the expensive vision and
    semantic passes, and Lesson 18: run it as a matter of course.
    """
    issues = part1_integrity_validator.check_foreign_characters(part_klalim["part1.json"])
    found = set()
    for issue in issues:
        parts = issue.split()
        kid, widx = int(parts[1]), int(parts[3].rstrip(":"))
        ch = issue.split("'")[1]
        found.add((kid, widx, ch))

    # Guard against a parsing failure that silently empties `found`: if the
    # check produced issues but parsing extracted nothing, the "no new"
    # assertion below would vacuously pass (empty - baseline == empty), hiding
    # every real finding behind a broken parser.
    assert len(found) == len(issues), (
        f"check_foreign_characters returned {len(issues)} issue(s) but parsing extracted "
        f"{len(found)} - the output format may have changed, breaking the parser above"
    )

    new = sorted(found - FOREIGN_CHARACTER_BASELINE)
    assert not new, (
        f"{len(new)} character(s) outside Part 1's documented repertoire that are NOT in "
        f"FOREIGN_CHARACTER_BASELINE: {new}. These are DATA issues - verify against the scan "
        f"through the review dashboard and correct via apply_reviewer_decisions.py, or add to "
        f"the baseline with evidence. Never fix one by editing part1.json directly."
    )
    stale = sorted(FOREIGN_CHARACTER_BASELINE - found)
    if stale:
        print(f"\nNote: FOREIGN_CHARACTER_BASELINE has {len(stale)} entry/entries no longer "
              f"present (resolved - shrink the baseline): {stale}")


# ADDED 2026-08-17 alongside the klal 65/66 boundary fix (see PROJECT-STATUS.md
# and SPAN_COVERAGE_BASELINE's klal-65 entry above for the full scan-verified
# diagnosis). klal 65, 66, 67 are a genuine 3-klal same-topic cluster on one
# rule ("אין ב"ד יכול לבטל דברי ב"ד חבירו אא"כ גדול ממנו בחכמה ובמנין" - "a
# court cannot annul another court's ruling unless greater in wisdom and
# number"): klal 65 states it, klal 67 restates it verbatim as ITS OWN title
# too (same-title-cluster, already auto-excluded by check_duplicate_phrases'
# own same-title check) - but klal 66, sandwiched between them, has its OWN
# distinct title ("אין ביטול ממש אבל להוסיף...") even though its body opens by
# quoting the same rule verbatim before qualifying it ("...דוקא ביטול ממש
# אבל..." - "this is only when [it is] an actual annulment, but..."), so the
# same-title check can't catch this pair. This is exactly the rhetorical
# device INTRA_KLAL_DUPLICATE_PHRASE_BASELINE's klal-65 comment already
# documents (a rule restated verbatim before the author's own gloss) - before
# the boundary fix that phrase sat wrongly duplicated INSIDE klal 65 alone
# (caught by the intra-klal test below); the fix moved it to where it
# belongs, at the start of klal 66, which correctly turns it into a CROSS-
# klal duplicate against both neighbors instead.
DUPLICATE_PHRASE_ADJACENT_PAIR_BASELINE = {(65, 66), (66, 67)}


def test_part1_no_new_duplicated_phrases(part_klalim, part1_integrity_validator):
    issues = part1_integrity_validator.check_duplicate_phrases(part_klalim["part1.json"], n=10)
    new = [i for i in issues if tuple(int(x) for x in i.split(":")[0].replace("klal ", "").split("/"))
           not in DUPLICATE_PHRASE_ADJACENT_PAIR_BASELINE]
    assert not new, f"Part-1 unexplained duplicated 10+-word phrase(s): {new}"


# check_intra_klal_duplicate_phrases (added 2026-08-12, closing the docstring
# overclaim the module always had - see validate_part1_corpus_integrity.py)
# originally had 4 known-genuine hits: klal 65 (a rule restated verbatim
# before the author's own gloss - "ב"ד יכול לבטל דברי ב"ד חבירו אא"כ גדול
# ממנו בחכמה ובמנין" - visually confirmed as the klal's own title restated
# in its body, a common rhetorical device in this book, not corruption),
# klal 189, klal 198. klal 65 REMOVED from this baseline 2026-08-17: the
# klal 65/66 boundary fix (see PROJECT-STATUS.md and
# DUPLICATE_PHRASE_ADJACENT_PAIR_BASELINE above) moved the erroneously-
# duplicated phrase out of klal 65 entirely, to where it belongs at the
# start of klal 66 - so the duplicate is no longer intra-klal, it is now
# correctly a cross-klal duplicate against klal 65/66's shared rule
# (caught by DUPLICATE_PHRASE_ADJACENT_PAIR_BASELINE instead). Confirmed by
# re-running check_intra_klal_duplicate_phrases() directly: klal 65 no
# longer appears in its output.
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
# klal 66 added 2026-08-30. Not new text and not a scramble: the klal OPENS
# with the maxim `אין ב"ד יכול לבטל דברי ב"ד חבירו אא"כ גדול ממנו בחכמה ובמנין`
# and quotes it again at word 105 under `והתנן` ("and we learned in the
# mishnah"), continuing `וכו'` - a verbatim restatement of its own source, which
# is the style this check's own failure message anticipates. It became visible
# only because a stray OCR `!` sitting between `ב"ד` and `חבירו` in the second
# occurrence was deleted this run (decision at w112), making the two copies
# contiguous for the first time. The second occurrence is also what independently
# confirms the `אין` at w1 belongs there - see PROJECT-STATUS open item 0B.
INTRA_KLAL_DUPLICATE_PHRASE_BASELINE = {66, 189, 198, 217}


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
        os.path.join(REPO, "tools", "validate_title_alphabetical_order.py"),
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
        os.path.join(REPO, "tools", "validate_klal_span_coverage.py"),
    )
    with open(trace_path, encoding="utf-8") as f:
        trace = {x["klal_id"]: x for x in json.load(f)}

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


def test_every_corrections_item_is_traceable_to_a_pipeline_source(corrections):
    """REGRESSION 2026-08-23 (code review, finding C1). corrections_part1.json
    is DERIVED - assemble_corrections_dataset.py truncates and rewrites it on
    every ./rebuild_all.sh. Two tools/ scripts appended 1,108 items into it
    directly; the file grew from 539 items to 1,647 and the whole suite stayed
    green, because nothing asserted that its contents are reproducible from the
    pipeline's own inputs. Every item must trace to one of exactly three sources:
    a vision-verified candidate (stage 3), a multi-witness consensus dispute
    (stage 4a), or a lexical defect (stage 4b, added 2026-08-26). An item matching
    none of them is a hand-injection that the next rebuild will silently destroy,
    taking any human review of it with it.

    Adding a source to this list is the deliberate act - each one is a FILE the
    pipeline reads and regenerates, never an append into this stage's own output.
    If you find yourself wanting to extend it to cover rows someone wrote by hand,
    that is the bug this test exists to catch."""
    verified_path = os.path.join(REPO, "corrections_verified_part1.json")
    consensus_path = os.path.join(REPO, "consensus_disputes_part1.json")
    lexical_path = os.path.join(REPO, "lexical_defect_report.json")

    with open(verified_path, encoding="utf-8") as f:
        verified = json.load(f)
    from_pipeline = {(c["klal_id"], c["word_index_in_final_text"]) for c in verified}

    from_consensus = set()
    if os.path.exists(consensus_path):
        with open(consensus_path, encoding="utf-8") as f:
            for kid_str, items in json.load(f).items():
                for d in items:
                    from_consensus.add((int(kid_str), d["word_index"]))

    from_lexical = set()
    if os.path.exists(lexical_path):
        with open(lexical_path, encoding="utf-8") as f:
            for d in json.load(f):
                from_lexical.add((d["klal_id"], d["word_index"]))

    orphans = [
        (int(kid_str), item["word_index"])
        for kid_str, items in corrections.items()
        for item in items
        if (int(kid_str), item["word_index"]) not in from_pipeline
        and (int(kid_str), item["word_index"]) not in from_consensus
        and (int(kid_str), item["word_index"]) not in from_lexical
    ]
    assert not orphans, (
        f"{len(orphans)} item(s) in corrections_part1.json trace to neither "
        f"corrections_verified_part1.json, consensus_disputes_part1.json nor "
        f"lexical_defect_report.json - "
        f"they were written into a derived file by hand and the next "
        f"./rebuild_all.sh will delete them. First few: {orphans[:5]}"
    )


def test_no_corrections_item_attributes_the_stored_text_to_an_engine(corrections):
    """REGRESSION 2026-08-23 (code review, finding C2). The superseded
    extractors set docai_reading to the stored base text on all 1,108 items
    they injected, at positions where DocAI was never consulted, and
    review_frontend/app.js renders that field as a selectable "DocAI reading"
    card - so the reviewer was shown a fabricated witness that always agreed
    with the corpus. A candidate exists BECAUSE an engine disagreed; an engine
    reading identical to final_text is either a contradiction or a fabrication."""
    bad = [
        (int(kid_str), item["word_index"])
        for kid_str, items in corrections.items()
        for item in items
        if item.get("docai_reading") is not None
        and item["docai_reading"] == item.get("final_text")
    ]
    assert not bad, (
        f"{len(bad)} item(s) report a docai_reading identical to the stored text. "
        f"An engine that was not consulted must read null, never the corpus's own "
        f"word. First few: {bad[:5]}"
    )


def test_no_word_index_is_served_twice_in_either_pane(part1_by_id):
    """REGRESSION 2026-08-24, generalising two bugs found by live review.

    review_frontend/app.js builds its word map as
    `corrections.forEach(c => byIndex[c.word_index] = c)` - LAST WRITE WINS -
    and the scan pane keys click/focus handling on (klal_id, word_index). So a
    second entry at the same key means the reviewer silently sees only one of
    them, losing whatever the other carried: a bbox (no scan highlight at all),
    both engine readings, a vision verdict and confidence.

    api_klal() builds its list from FOUR sources (machine candidates,
    manual_correction decisions, word-level klal_flags, witness disagreements)
    and api_page() builds its own from three. Every source after the first must
    check whether the index is taken, and each had grown its OWN partial guard -
    the flag and witness paths both checked `manual_word_indices` but not
    machine candidates - which is exactly the shape that leaves one combination
    uncovered.

    Found: manual-over-machine at klal 91 w453/w524 (reported as "the last two
    disputes weren't properly highlighted"), then by sweep, 4 replace+witness
    and 1 ai_flag+witness in the text pane and the same 4 again in the scan
    pane, which repeats the defect independently. This test covers every source
    and both panes at once, so a fifth source cannot reintroduce it quietly."""
    review_server = _import_from_path("review_server", os.path.join(REPO, "pipeline", "review_server.py"))

    text_dupes = []
    for klal_id in part1_by_id:
        counts = collections.Counter(
            c["word_index"] for c in review_server.api_klal(klal_id)["corrections"]
            if c.get("opcode") != "delete")
        text_dupes += [(klal_id, wi, n) for wi, n in counts.items() if n > 1]
    assert not text_dupes, (
        f"{len(text_dupes)} position(s) serve more than one text-pane entry: "
        f"{text_dupes[:8]}. app.js keeps only the last, so the other is invisible.")

    pages = set()
    for klal_id in part1_by_id:
        pages.update(review_server._klal_all_pages(klal_id))
    # `delete` entries are EXCLUDED here, exactly as they already are from the
    # text half above. A gap is text the scan HAS and the corpus lacks, addressed
    # by the index it would be inserted BEFORE - so it shares that index with the
    # word standing there while pointing at different ink, and the two are
    # different objects that both need drawing. 40 such pairs exist across 35
    # klalim.
    #
    # WIDENED 2026-09-03. api_page used to let the gap's key SUPPRESS the word, so
    # only one box was drawn and this test passed - by drawing the wrong one.
    # Klal 17 w308 is `בסתם` at x=0.62 and its omission sits at x=0.86; clicking
    # the word boxed the omission (reviewer: "highlights the wrong word"). Both
    # are served now, and app.js's focus test branches on the gap opcode so a
    # click still resolves to exactly one. What this invariant protects is that
    # no TWO ENTRIES OF THE SAME KIND share a key, which is still asserted.
    scan_dupes = []
    for page in sorted(pages):
        counts = collections.Counter(
            (i.get("klal_id"), i.get("word_index")) for i in review_server.api_page(page)
            if i.get("word_index") is not None and i.get("opcode") != "delete")
        scan_dupes += [(page, k[0], k[1], n) for k, n in counts.items() if n > 1]
    assert not scan_dupes, (
        f"{len(scan_dupes)} position(s) draw more than one scan box: {scan_dupes[:8]}. "
        f"Two boxes at one (klal_id, word_index) confuse the pane's click and focus handling.")

    # ...and a gap must never share its key with ANOTHER gap, which the focus
    # test genuinely could not tell apart.
    gap_dupes = []
    for page in sorted(pages):
        counts = collections.Counter(
            (i.get("klal_id"), i.get("word_index")) for i in review_server.api_page(page)
            if i.get("word_index") is not None and i.get("opcode") == "delete")
        gap_dupes += [(page, k[0], k[1], n) for k, n in counts.items() if n > 1]
    assert not gap_dupes, (
        f"{len(gap_dupes)} position(s) draw more than one GAP box: {gap_dupes[:8]}. "
        "Two gaps at one index cannot be told apart by the focus test, which branches "
        "only on gap-vs-word.")


def test_every_open_word_level_flag_has_a_control_that_can_clear_it(part1_by_id):
    """REGRESSION 2026-08-24. A word-level klal_flag is cleared only by a later
    record at the same (klal_id, word_index), which the dashboard can write only
    from the disputed panel's "Clear revisit flag" control - and that control
    renders only if the served entry carries `word_flag`.

    api_klal() dropped the flag entirely whenever a manual_correction existed at
    the same word ("an AI flag on the same word_index is now redundant"). That
    was right when a flag could only ever be SET; once clearing existed it made
    the flag unreachable - open in the log, still highlighting the word, with no
    way to close it. Reported as "still shows a flag in the middle pane but
    there's nothing to clear in the right pane".

    Corpus sweep at the time of the fix: **325 open word-level flags across 104
    klalim, every one of them unclearable** - klal 91's four were the visible
    tip. Any state the UI can set must have a path back (Lesson 26/28); this
    test asserts it for the whole corpus rather than the one klal that surfaced
    it."""
    review_server = _import_from_path("review_server", os.path.join(REPO, "pipeline", "review_server.py"))
    open_by_klal = collections.defaultdict(list)
    for (klal_id, word_index), rec in review_server.rd.all_current("klal_flag").items():
        if word_index is not None and rec.get("needs_revisit"):
            open_by_klal[klal_id].append(word_index)

    unreachable = []
    for klal_id, indices in open_by_klal.items():
        if klal_id not in part1_by_id:
            continue
        # CORRECTED 2026-08-24: this used to check only for a `word_flag` field,
        # which is the condition the DISPUTED panel's button renders on. But
        # renderKlalBody routes opcode 'ai_flag' and 'manual' words to the
        # MANUAL panel instead, so the original assertion passed while 197 of
        # 325 open flags had no reachable control. Testing the served field
        # rather than the reachable control is exactly the mistake this file
        # exists to catch.
        clearable = {c["word_index"] for c in review_server.api_klal(klal_id)["corrections"]
                     if c.get("word_flag") or c.get("opcode") == "ai_flag"}
        unreachable += [(klal_id, wi) for wi in indices if wi not in clearable]

    assert not unreachable, (
        f"{len(unreachable)} open word-level flag(s) are served without a `word_flag` "
        f"field, so the dashboard renders no control that can clear them: "
        f"{sorted(unreachable)[:10]}. They stay open in the log and keep highlighting "
        f"their word forever.")


def test_nav_tristate_matches_what_each_word_actually_renders_as(part1_by_id):
    """REGRESSION 2026-08-25, reported by the reviewer: "there were more words
    highlighted than the count so it is now -1 even though a few are outstanding."

    2026-08-24's fix made `correction_count` count DISTINCT word_indexes, mirroring
    api_klal()'s merge - but left `decided_count` and `machine_disputed_count`
    adding up their sources independently. A word claimed by two sources (klal 88
    w327: a witness decision at a position a manual_correction already covers) was
    counted once in the total and twice in decided, so `open_count = total -
    decided` went NEGATIVE. Two more of klal 88's phantom decisions came from
    witness rows whose word_index is None - never rendered, still counted. Swept:
    3 klalim (30, 88, 91), 6 phantom decisions.

    The total matching is not enough on its own; each of the three states has to
    match too, or the legend and the nav badge describe a screen that isn't there.
    This transcribes app.js's `wordState()`, which is the only thing that decides
    what colour a reviewer actually sees. (The flag list it depends on is kept in
    sync by test_machine_resolved_flags_agree_between_server_and_frontend.)"""
    review_server = _import_from_path("review_server", os.path.join(REPO, "pipeline", "review_server.py"))
    machine_resolved = set(review_server.MACHINE_RESOLVED_FLAGS)

    def word_state(c):
        # app.js wordState(), in the same order - an ai_flag carries the AI's
        # own flag record rather than a human decision, so it is open UNLESS the
        # server marked it answered (a human ruled on that word after the flag
        # was raised); then a human decision wins, then a machine-resolved flag,
        # then a witness's own vision verdict.
        if c.get("opcode") == "ai_flag":
            return "human" if c.get("flag_answered") else "open"
        # An unanswered word-level flag overlaid on a richer entry makes the word
        # open whatever the entry's own verdict is - added 2026-08-30 alongside
        # the same rule in app.js, after seven words carried an open flag and
        # rendered AMBER off a `current_text_confirmed` candidate.
        wf = c.get("word_flag")
        if wf and not wf.get("answered"):
            return "open"
        if c.get("current_decision"):
            return "human"
        if c.get("flag") in machine_resolved:
            return "machine"
        if c.get("opcode") == "witness":
            return "machine" if c.get("vision_selected") in ("A", "B") else "open"
        return "open"

    listing = review_server.api_klalim(1)
    rows = listing if isinstance(listing, list) else listing.get("klalim", [])
    offenders, negative, unbalanced, miscounted = [], [], [], []
    for row in rows:
        corrections = review_server.api_klal(row["klal_id"])["corrections"]
        # The TOTAL check (2026-08-24's finding F1) folded in here 2026-08-25:
        # it walked the same 222 klalim in its own loop, and two full passes over
        # api_klal() in one pytest process was enough to starve the Playwright
        # tests that run after it - two of them began failing on a 15s page load
        # against a server that answers in 0.01s. One pass, both properties.
        rendered_total = (
            len({c["word_index"] for c in corrections if c.get("opcode") != "delete"})
            + len([c for c in corrections if c.get("opcode") == "delete"]))
        if row["correction_count"] != rendered_total:
            miscounted.append((row["klal_id"], row["correction_count"], rendered_total))
        states = [word_state(c) for c in corrections]
        rendered = (states.count("human"), states.count("machine"), states.count("open"))
        nav = (row["decided_count"], row["machine_resolved_count"], row["machine_disputed_count"])
        if rendered != nav:
            offenders.append((row["klal_id"], nav, rendered))
        if row["open_count"] < 0:
            negative.append((row["klal_id"], row["correction_count"], row["decided_count"]))
        if row["correction_count"] != sum(nav):
            unbalanced.append((row["klal_id"], row["correction_count"], nav))

    assert not negative, (
        f"open_count went negative - decided is being counted more times than the "
        f"word is rendered (klal_id, total, decided): {negative}")
    assert not unbalanced, (
        f"the tri-state does not add up to correction_count (klal_id, total, "
        f"(decided, resolved, disputed)): {unbalanced[:8]}")
    assert not miscounted, (
        f"{len(miscounted)} klal(im) whose nav TOTAL disagrees with what the text pane "
        f"renders (klal_id, nav, rendered): {miscounted[:8]}")
    assert not offenders, (
        f"{len(offenders)} klal(im) whose nav tri-state disagrees with what the text "
        f"pane renders (klal_id, nav, rendered): {offenders[:8]}")



def test_the_word_list_behind_a_legend_count_is_exactly_what_that_count_counts():
    """/api/word-states must ENUMERATE precisely what /api/klalim COUNTS.

    ADDED 2026-09-01, with the legend's click-through. The legend has shown four
    totals since it was built with no way to reach the words inside them; it now
    opens a list, and a list of a different length from the number that opened it
    is the same defect class this file already carries three regressions for -
    the nav saying 1,201 where the pane rendered 1,061, then klal 88's "-1", then
    klal 73's missing badge. Each one was two encodings of one rule disagreeing.

    The two answers are built in ONE pass (api_klalim's `on_klal_states`
    callback), which is what makes them agree; this asserts the property that
    arrangement exists to provide, so that replacing it with a second traversal
    fails here rather than in front of a reviewer.

    Deliberately pins no COUNT - only the equality - per Lesson 36: the numbers
    move every time the corpus improves or a decision is recorded, and a test
    that fails when the text gets better is testing the defect.
    """
    review_server = _import_from_path("review_server", os.path.join(REPO, "pipeline", "review_server.py"))
    rows = review_server.api_klalim(part_num=1)
    lists = review_server.api_word_states(part_num=1)
    for bucket, field in (("machine_disputed", "machine_disputed_count"),
                          ("machine_resolved", "machine_resolved_count"),
                          ("decided", "decided_count"),
                          ("ai_flag", "ai_flag_count"),
                          # The senior-review list behind "of N recorded". Same
                          # property, same reason: the control is labelled with
                          # the number, so opening a list of another length
                          # would be a control that lies about itself.
                          ("recorded", "recorded_decision_count")):
        assert len(lists[bucket]) == sum(r[field] for r in rows), (
            f"the legend's {field} and the list behind it disagree: "
            f"{sum(r[field] for r in rows)} counted, {len(lists[bucket])} listed")
    # Every listed word must be addressable - the list's whole purpose is that a
    # row is a working deep link. A row missing either half of (klal, word) is a
    # link to nowhere, which renders as a list item that silently does nothing.
    for bucket, items in lists.items():
        if not isinstance(items, list):
            continue
        for item in items:
            assert isinstance(item.get("klal_id"), int) and isinstance(item.get("word_index"), int), (
                f"{bucket} carries an unaddressable row: {item}")

    # Every recorded row must carry a status a reviewer can act on, and
    # `rendered` must agree with the decided list rather than being a third
    # opinion about the same word - it was computed from the wrong structure
    # first and reported 39 against a legend showing 51.
    statuses = {"confirmed", "applied", "pending", "drifted", "unplaced", "unknown"}
    unknown_status = [r for r in lists["recorded"] if r.get("status") not in statuses]
    assert not unknown_status, f"recorded rows with an unrecognised status: {unknown_status[:5]}"

    # `confirmed` must be its OWN bucket and not be folded back into `applied`.
    # It was, until 2026-09-01: `applied` meant nothing more than
    # `corpus == chosen_text`, which is trivially true for a ruling that keeps
    # the stored reading - the commonest decision in this corpus. That reported
    # 27 of 54 drawn-green words as applied when the real figure was 1, and it is
    # what the reviewer's "so green words are applied but not rebuilt? why?"
    # was actually asking about.
    for row in lists["recorded"]:
        kept_stored = (row.get("chosen_text") is not None
                       and row.get("chosen_text") == row.get("original_word"))
        if kept_stored and row["status"] not in ("unplaced",):
            assert row["status"] == "confirmed", (
                f"a ruling that kept the stored reading is reported as "
                f"{row['status']!r}, which claims something was promoted: {row}")

    # `index_stale` is a SECOND, independent fact - what happened to the ruling's
    # ADDRESS, not to the ruling. Collapsing the two is what made open item 0AB
    # count 105 "orphaned" rulings when 79 of those had in fact been honoured and
    # only had a stale index. A stale address is still a defect (Lesson 35); it
    # is just not the same defect.
    for row in lists["recorded"]:
        assert isinstance(row.get("index_stale"), bool), row
    assert any(r["status"] == "applied" and r["index_stale"] for r in lists["recorded"]) or \
           not any(r["index_stale"] for r in lists["recorded"]), (
        "index_stale is being treated as a synonym for a lost ruling - no applied "
        "ruling carries one, which is not what the audit script measures")
    marked_rendered = {(r["klal_id"], r["word_index"]) for r in lists["recorded"] if r["rendered"]}
    assert marked_rendered <= {(r["klal_id"], r["word_index"]) for r in lists["decided"]}, (
        "a recorded ruling marked `rendered` is not in the decided list")


def test_recorded_decision_count_is_every_ruling_not_only_the_rendered_ones():
    """The legend's second Human-Decided number - every ruling on record.

    ADDED 2026-09-01 (reviewer: "count for human decisions is 51 - not
    correct"). `decided_count` counts words rendered GREEN, and a decision stops
    rendering the moment it is settled - the rebuild drops the candidate entry,
    and an applied manual_correction fails the display drift check because the
    word it names is no longer there. Part 1 read 51 against 463 rulings on
    record.

    This asserts the two are DIFFERENT MEASURES, not that either is a particular
    number (Lesson 36 - both move every time the corpus improves or a decision is
    recorded): recorded must cover at least what renders, since a rendered
    decision is by definition recorded, and it must equal the ledger's own union
    of candidate/disputed, manual and witness positions. The drift check that
    governs `decided_count` must NOT govern this one, which is the entire point
    of it.
    """
    review_server = _import_from_path("review_server", os.path.join(REPO, "pipeline", "review_server.py"))
    rd = _import_from_path("review_decisions", os.path.join(REPO, "pipeline", "review_decisions.py"))
    rows = review_server.api_klalim(part_num=1)
    by_klal = {r["klal_id"]: r for r in rows}

    # A ruling a later record explicitly REPLACES is not a second ruling. Added
    # 2026-09-02 with tools/repoint_stale_decisions.py: the log is append-only,
    # so a re-pointed ruling lands at the correct word_index while its stale
    # original stays put at the old one and remains the newest record THERE.
    # Without this the reviewer would be shown both, and the count would climb
    # every time a stale address was repaired.
    superseded = rd.superseded_ids()
    expected = {}
    for dmap in (rd.all_current("candidate_choice"), rd.all_current("manual_correction")):
        for (kid, wi), rec in dmap.items():
            if kid in by_klal and rec.get("id") not in superseded:
                expected.setdefault(kid, set()).add(wi)
    # The witness leg, re-derived here rather than trusted: witness_choice keys
    # on docai_token_index, so it has to be mapped through the witness queue's
    # own word_index to join the other two in ONE index space. Leaving it out is
    # what made the first cut of this count serve klal 30 recorded=3 against
    # decided=9.
    witness_decided = rd.all_current("witness_choice")
    for w in review_server._load_witness_queue():
        kid, wi = w.get("klal_id"), w.get("word_index")
        rec = witness_decided.get((kid, w.get("docai_token_index")))
        if kid in by_klal and wi is not None and rec and rec.get("id") not in superseded:
            expected.setdefault(kid, set()).add(wi)

    wrong = [(kid, r["recorded_decision_count"], len(expected.get(kid, ())))
             for kid, r in by_klal.items()
             if r["recorded_decision_count"] != len(expected.get(kid, ()))]
    assert not wrong, (
        f"recorded_decision_count does not match the ledger (klal_id, served, "
        f"ledger): {wrong[:8]}")

    short = [(kid, r["recorded_decision_count"], r["decided_count"])
             for kid, r in by_klal.items()
             if r["recorded_decision_count"] < r["decided_count"]]
    assert not short, (
        "a word rendering as human-decided must also be counted as recorded "
        f"(klal_id, recorded, decided): {short[:8]}")



def test_witness_rows_served_without_a_word_index_are_never_counted(part1_by_id):
    """A witness row with `word_index: None` cannot be highlighted - api_klal()
    skips it explicitly ("scan-only and stay that way"). Six such rows are served
    today and three of them carry a human decision, which the old count added to
    `decided_count` for a word the reviewer could never have clicked. Counting
    what cannot be reached is how klal 88's badge went to -1."""
    review_server = _import_from_path("review_server", os.path.join(REPO, "pipeline", "review_server.py"))
    unmapped = [w for w in review_server._load_witness_queue() if w.get("word_index") is None]
    if not unmapped:
        return  # patched away upstream - nothing to guard
    by_klal = {}
    for w in unmapped:
        by_klal.setdefault(w["klal_id"], []).append(w)
    for kid, rows in by_klal.items():
        served = review_server.api_klal(kid)["corrections"]
        token_indexes = {c.get("docai_token_index") for c in served}
        for w in rows:
            assert w["docai_token_index"] not in token_indexes or any(
                c.get("word_index") is not None for c in served
                if c.get("docai_token_index") == w["docai_token_index"]), (
                f"klal {kid}: witness token {w['docai_token_index']} has no word_index "
                "but is served as a standalone entry")


def test_every_flagged_word_in_the_text_pane_has_a_flagged_box_on_the_scan(part1_by_id):
    """REGRESSION 2026-08-25 (reviewer, klal 218: "has only one red item in the
    right pane" while the text pane showed two flagged words).

    api_klal() and api_page() build the same picture from different sources:
    the text pane's list is candidates + manual corrections + word-level flags +
    witness items, while the scan pane's was candidates + witness + every plain
    word. A flagged word with no machine candidate behind it therefore reached
    the scan as an anonymous `plain` box - the same colourless treatment as
    ordinary prose. Measured before the fix: 187 word-level flags and 8 manual
    corrections across 88 klalim.

    Two functions drawing one picture from two sources is this project's most
    repeated defect shape; this asserts they agree."""
    review_server = _import_from_path("review_server", os.path.join(REPO, "pipeline", "review_server.py"))
    listing = review_server.api_klalim(1)
    rows = listing if isinstance(listing, list) else listing.get("klalim", [])
    by_page = {}
    offenders = []
    for row in rows[:60]:   # 60 klalim is ~20 pages, enough to cover every entry kind
        klal_id = row["klal_id"]
        for c in review_server.api_klal(klal_id)["corrections"]:
            page, wi = c.get("page"), c.get("word_index")
            if page is None or wi is None or not c.get("bbox") or c.get("opcode") == "delete":
                continue
            if page not in by_page:
                by_page[page] = {
                    (x.get("klal_id"), x.get("word_index"))
                    for x in review_server.api_page(page)
                    if x.get("kind") != "plain"
                }
            if (klal_id, wi) not in by_page[page]:
                offenders.append((klal_id, wi, page, c.get("opcode"), c.get("flag")))
    assert not offenders, (
        f"{len(offenders)} word(s) the text pane flags but the scan pane serves as plain "
        f"prose (klal, word, page, opcode, flag): {offenders[:8]}")


def test_end_of_klal_gap_marker_is_rendered_exactly_once():
    """REGRESSION 2026-08-26. A `delete` candidate can sit at
    word_index == len(words) - text the scan has AFTER the klal's last stored
    word. Two blocks in renderKlalBody() rendered it: an older one-liner
    (`gapsBefore[words.length]`) and the newer sorted block that supersedes it,
    whose filter is `idx >= words.length` and therefore INCLUDES that index. So
    the candidate was drawn twice - once with its accepted insert text, once bare
    - in the 12 klalim that have one (84, 88, 106, 114, 138, 159, 164, 171, 175,
    193, 211, 219, including klal 219, the klal the newer block was written for).
    The reviewer saw a duplicate proposed insertion at the end of the klal.

    Scraped from source in the same spirit as the MACHINE_RESOLVED_FLAGS check
    below: the defect is one renderer too many, which is visible in the text."""
    with open(os.path.join(REPO, "review_frontend", "app.js"), encoding="utf-8") as f:
        js = f.read()
    renders = re.findall(r"gapsBefore\[words\.length\]\.forEach", js)
    assert len(renders) <= 1, (
        f"review_frontend/app.js renders gapsBefore[words.length] {len(renders)} times; "
        "the sorted `idx >= words.length` block already covers that index, so a second "
        "renderer draws every end-of-klal omission candidate twice.")


def test_no_corpus_word_is_aligned_to_page_furniture():
    """REGRESSION 2026-08-26 (reviewer: "clicking on klal 7 word 497 highlights
    the wrong word").

    _corpus_word_bboxes() aligns the klal's words against a page's DocAI tokens
    to find each word's scan box. The running header, the folio and the Google
    Books watermark are stripped from clean_text by construction - so if they are
    left in the token list, SequenceMatcher is free to capture a corpus word with
    one of them. Klal 7's `י"ר` matched page 18's header `יר` at relative-y 0.000
    instead of its real occurrence at the foot of page 17 (rel-y 0.870), and
    clicking it rang the running header on the wrong page. Eight Part-1 words
    across eight klalim were boxed on a header token before the fix."""
    import corpus_io as cio
    review_server = _import_from_path("review_server", os.path.join(REPO, "pipeline", "review_server.py"))
    if not os.path.isdir(cio.DOCAI_DIR):
        pytest.skip("docai_word_boxes/ is gitignored and migrated separately")
    by_id, _ = review_server._load_klalim(1)
    regions = review_server._load_regions()
    offenders = []
    for klal_id, k in sorted(by_id.items()):
        words = (k.get("clean_text") or "").split(" ")
        for page in review_server._klal_all_pages(klal_id, regions):
            toks = cio.load_docai_page(page, cio.DOCAI_DIR) or []
            if not toks:
                continue
            furniture = {(round(toks[i]["x1"], 6), round(toks[i]["y1"], 6))
                         for i in cio.header_furniture_indices(toks)}
            if not furniture:
                continue
            for wi, b in review_server._corpus_word_bboxes(klal_id, words, page).items():
                if (round(b["x1"], 6), round(b["y1"], 6)) in furniture:
                    offenders.append((klal_id, wi, page))
    assert not offenders, (
        f"{len(offenders)} corpus word(s) have a scan box that is a page-header, folio or "
        f"watermark token (klal, word_index, page): {offenders[:8]}")


def test_reject_omission_option_does_not_read_a_field_that_cannot_exist():
    """REGRESSION 2026-08-26 (reviewer: klal 66 word 17, "can't save decision
    current text (no word)").

    A `delete`-opcode candidate says the scan has text the corpus lacks. The
    reviewer's two choices are "accept the inserted word" and "keep current text
    (no word)" - and the second one is a real, common answer, because many of
    these proposals are junk (`בעיא 4`, `४`, `ג` among the four already
    recorded). That option used `source: 'final_text'`, but a delete candidate has
    NO final_text by definition, so saveDisputedDecision() resolved it to
    undefined and POSTed a null. When the null guard landed the same day, the
    option became unsaveable for all 40 omission candidates across 35 klalim -
    a data-corrupting bug traded for a dead control.

    The option must resolve to an explicit empty string, which
    apply_delete_insertion() already treats as "insert nothing"."""
    with open(os.path.join(REPO, "review_frontend", "app.js"), encoding="utf-8") as f:
        js = f.read()
    pushes = [ln for ln in js.splitlines()
              if "options.push" in ln and "Keep current text (no word)" in ln]
    assert pushes, "app.js must still offer a 'Keep current text (no word)' option"
    for ln in pushes:
        assert "'final_text'" not in ln, (
            "the 'Keep current text (no word)' option resolves to corr.final_text, which is "
            "always absent on a delete-opcode candidate - it will POST null and be refused "
            "by the write-site guard, leaving the control dead. Give it a source that "
            f"yields an explicit empty string. Offending line: {ln.strip()}")


# The ten words that carry no Hebrew letter at all, so hebrew_letters_only()
# reduces them to "" and the aligner drops them from both sides. Fixing them
# needs punctuation tokens back in the sequence, which was tried on 2026-08-30
# and reverted: it moved 41 correct boxes and lost 2. See _corpus_word_bboxes().
# The flagged words carrying no Hebrew letter at all (hebrew_letters_only()
# reduces them to "", so the aligner drops them from both sides) plus a handful
# of run-together words - `שתישההולאחם` is `שתי הלחם` fused, `ראיתי'להתוס'` two
# words with the space lost. Those are a TEXT repair, not an alignment problem;
# three already carry the right reading in their flag note. Fixing the
# punctuation-only ones needs punctuation tokens back in the sequence, tried
# 2026-08-30 and reverted (it moved 41 correct boxes and lost 2).
# INDEX-KEYED - see the note on FOREIGN_CHARACTER_BASELINE.
UNLOCATABLE_FLAGGED_WORD_BASELINE = {
    (77, 11), (144, 598), (182, 5), (189, 461),
    (198, 570), (209, 16), (216, 136),
    # (105, 4) added 2026-08-31: a flag on the `,` that the printer set as a
    # raised `•` (item 47). Same reason as the seven above - the token carries no
    # Hebrew letter, so the corpus-to-DocAI aligner has nothing to match it on.
    # Matching non-Hebrew words on their raw text was tried on 2026-08-30 and
    # reverted: it works and costs too much, moving 41 correct boxes and losing 2.
    (105, 4),
}




# The 21 words whose box already sat out of reading order before the aligner
# learned to pair `replace` runs on 2026-08-30 - the change introduced none of
# them and fixed none of them, measured both ways. 13 of the 21 sit immediately
# beside an IDENTICAL word: the corpus has the word doubled where the page prints
# it once, so SequenceMatcher maps both copies onto the same token and the two
# boxes coincide. Several are already flagged as duplicated-word candidates
# (klal 29 w99 `צדה`, klal 3 w224 `ואם`), so fixing the text is what retires
# these, not tuning the aligner.
# Boxes already out of reading order before the aligner learned to pair
# `replace` runs on 2026-08-30 - measured both ways, the change introduced none
# and fixed none. Most sit beside an IDENTICAL word: the corpus has it doubled
# where the page prints it once, so SequenceMatcher maps both copies onto the
# same token and the boxes coincide. Several are already flagged as
# duplicated-word candidates, so fixing the TEXT is what retires these, not
# tuning the aligner. INDEX-KEYED - see FOREIGN_CHARACTER_BASELINE.
BOX_READING_ORDER_BASELINE = {
    (3, 224), (3, 225), (29, 9), (29, 99),
    (29, 100), (30, 1521), (30, 1522), (41, 10),
    (41, 11), (57, 15), (57, 16), (68, 28),
    (68, 29), (82, 25), (82, 26), (94, 189),
    (147, 406), (147, 407), (158, 50), (158, 51),
    (167, 68), (167, 69),
}




def test_a_words_scan_box_sits_between_its_neighbours_in_reading_order(part1_by_id):
    """The aligner pairs equal-length `replace` runs positionally (0D(a)), which
    is inference, not a match - so it needs a check that can FAIL if the inference
    is wrong. "Did the box count go up" cannot: a box on arbitrary ink would raise
    it just as happily.

    Reading order can. The page is RTL, so word k's box must start left of word
    k-1's box on the same line, or lower down the page - and the same for word k+1
    relative to it. A box paired onto an unrelated token lands outside that
    ordering and this fails loudly.

    Applied to EVERY boxed word with both neighbours boxed on the same page, not
    only the paired ones, so it also guards the exact-match path it inherited."""
    review_server = _import_from_path("review_server", os.path.join(REPO, "pipeline", "review_server.py"))
    import corpus_io as cio
    if not os.path.isdir(cio.DOCAI_DIR):
        pytest.skip("docai_word_boxes/ is gitignored and migrated separately")
    out_of_order = []
    for klal_id, klal in sorted(part1_by_id.items()):
        words = klal["clean_text"].split(" ")
        boxes = review_server._word_bboxes_resolved(klal_id, words)
        for word_index in sorted(boxes):
            prev, nxt = boxes.get(word_index - 1), boxes.get(word_index + 1)
            if not prev or not nxt:
                continue
            (pbox, ppage), (nbox, npage), (box, page) = prev, nxt, boxes[word_index]
            if ppage != page or npage != page:
                continue          # a page seam has its own geometry; not this check
            # A small tolerance: neighbouring tokens on one line overlap slightly,
            # and a line break is a y jump, not an x one.
            after_prev = (box["y1"] > pbox["y1"] + 0.005) or (box["x2"] <= pbox["x1"] + 0.01)
            before_next = (nbox["y1"] > box["y1"] + 0.005) or (nbox["x2"] <= box["x1"] + 0.01)
            if not (after_prev and before_next):
                out_of_order.append((klal_id, word_index, words[word_index]))
    new = [o for o in out_of_order if (o[0], o[1]) not in BOX_READING_ORDER_BASELINE]
    assert not new, (
        f"{len(new)} word(s) have a scan box that does not sit between their neighbours' "
        f"boxes in RTL reading order, so the alignment put them on the wrong token: "
        f"{new[:8]}. Verify against the scan before adding to BOX_READING_ORDER_BASELINE.")
    stale = sorted(BOX_READING_ORDER_BASELINE - {(o[0], o[1]) for o in out_of_order})
    if stale:
        print(f"\nNote: BOX_READING_ORDER_BASELINE has {len(stale)} entries that now order "
              f"correctly (safe to remove): {stale}")


def test_every_open_flag_can_actually_be_found_on_the_scan(part1_by_id):
    """REGRESSION 2026-08-30, reviewer: "clicking on 69 w338 does not snap the
    reading pane to the word".

    THE SIBLING TEST BELOW DOES NOT COVER THIS, which is why it stayed green
    through the whole thing: it opens `if c.get("opcode") in ("delete",
    "ai_flag", "manual"): continue` - and `ai_flag` is precisely what a flagged
    word is - and it only fires on the INVERSE case, an entry lacking a position
    though the alignment has one. Nothing asserted that the alignment has one.

    It did not, for 63 of 306 open flags (21%). A word gets a box only where the
    corpus and DocAI agree, so repairing a word removed its box - the corrected
    form no longer equals the token still holding the error - and 16 of the 63
    were made by that day's own corrections. Klal 69's were every alef-lamed word
    in the klal, DocAI reading the ﭏ ligature as a bare alef.

    A baseline, not a hard zero: ten flagged words carry no Hebrew letter at all
    and cannot be aligned without a change that costs more than it buys."""
    review_server = _import_from_path("review_server", os.path.join(REPO, "pipeline", "review_server.py"))
    ard = _import_from_path("apply_reviewer_decisions",
                            os.path.join(REPO, "pipeline", "apply_reviewer_decisions.py"))
    import corpus_io as cio
    if not os.path.isdir(cio.DOCAI_DIR):
        pytest.skip("docai_word_boxes/ is gitignored and migrated separately")
    unlocatable = []
    for klal_id, klal in sorted(part1_by_id.items()):
        words = klal["clean_text"].split(" ")
        for word_index in sorted(ard.open_word_flags(klal_id)):
            if not (0 <= word_index < len(words)):
                continue        # an out-of-range flag is item 0C's problem, not this one
            bbox, page = review_server._word_scan_position(klal_id, words, word_index)
            if not bbox or page is None:
                unlocatable.append((klal_id, word_index, words[word_index]))
    new = [u for u in unlocatable if (u[0], u[1]) not in UNLOCATABLE_FLAGGED_WORD_BASELINE]
    assert not new, (
        f"{len(new)} open flag(s) have no scan position, so clicking the word highlights nothing "
        f"and the focus-zoom has nothing to zoom to: {new[:8]}. Verify against the scan before "
        f"adding to UNLOCATABLE_FLAGGED_WORD_BASELINE."
    )
    stale = sorted(UNLOCATABLE_FLAGGED_WORD_BASELINE - {(u[0], u[1]) for u in unlocatable})
    if stale:
        print(f"\nNote: UNLOCATABLE_FLAGGED_WORD_BASELINE has {len(stale)} entries that now "
              f"resolve (safe to remove): {stale}")


def test_every_flagged_word_can_be_located_on_the_scan(part1_by_id):
    """REGRESSION 2026-08-26 (reviewer: "klal 179 word 267 - clicking does not
    highlight word in scan page").

    A correction entry that carries no `page` cannot be placed on a scan page by
    api_page(), so it falls through to the plain-word pass and renders as
    ordinary prose instead of as the flagged word it is - and the click falls
    back to the klal's START page, which is wrong for any word past a page break.
    Klal 179 w267 sits on page 67 in a klal that starts on 66, so the scan pane
    showed 66 and had nothing to highlight.

    A `delete` (omission) candidate is exempt: it marks a gap where the corpus
    has no word at all, so there is nothing to align."""
    import corpus_io as cio
    review_server = _import_from_path("review_server", os.path.join(REPO, "pipeline", "review_server.py"))
    if not os.path.isdir(cio.DOCAI_DIR):
        pytest.skip("docai_word_boxes/ is gitignored and migrated separately")
    offenders = []
    for klal_id in sorted(part1_by_id):
        served = review_server.api_klal(klal_id)
        words = (served.get("clean_text") or "").split(" ")
        for c in served.get("corrections", []):
            if c.get("opcode") in ("delete", "ai_flag", "manual"):
                continue        # gaps and reviewer-raised entries have their own paths
            if c.get("page") is not None and c.get("bbox"):
                continue
            # only an offender if the alignment DOES know where the word is
            bbox, page = review_server._word_scan_position(klal_id, words, c["word_index"])
            if bbox and page is not None:
                offenders.append((klal_id, c["word_index"], c.get("opcode")))
    assert not offenders, (
        f"{len(offenders)} machine correction(s) carry no scan position although the DocAI "
        f"alignment has one, so they render as plain prose and click to the wrong page "
        f"(klal, word_index, opcode): {offenders[:8]}")


def test_no_klal_marker_ends_in_a_resh_that_should_be_a_dalet(all_klalim):
    """ד and ר are near-identical in this fount and are a confirmed confusion
    pair here. In a Hebrew numeral that difference is 4 vs 200, and position
    makes it decidable: numerals are written high-to-low (hundreds, tens, units),
    so a TRAILING letter is the units digit and must come from א-ט - unless the
    number is round and simply stops at a higher place.

    Within 1-667 there are exactly two numbers that legitimately end in ר:
    **200 (`ר`) and 600 (`תר`)**, and this corpus contains both. Every other
    trailing ר is arithmetically impossible - `רמר` would be 200+40+200 - and is
    therefore a ד misread, e.g. `רמר` for `רמד` (244).

    Raised by the reviewer 2026-08-26. Currently zero violations; this exists so a
    future marker misread cannot pass silently, which is what a cheap mechanical
    invariant is for (Lesson 8)."""
    import corpus_io as cio
    VALUES = dict(zip("אבגדהוזחטיכלמנסעפצקרשת",
                      [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 30, 40, 50, 60, 70, 80, 90,
                       100, 200, 300, 400]))
    LEGITIMATE_TRAILING_RESH = {200, 600}   # ר and תר; nothing else in this range

    offenders = []
    for k in all_klalim:
        g = cio.hebrew_letters_only(k.get("gematria") or "")
        if not g or not g.endswith("ר"):
            continue
        if not all(c in VALUES for c in g):
            continue                        # not a pure numeral: a different question
        value = sum(VALUES[c] for c in g)
        if value in LEGITIMATE_TRAILING_RESH:
            continue
        offenders.append((k["klal_id"], k.get("gematria"), value,
                          k.get("gematria", "")[:-1] + "ד"))
    assert not offenders, (
        f"{len(offenders)} klal marker(s) end in ר at a position where only א-ט can stand, "
        f"so the ר is a misread ד (klal_id, stored, its value, likely reading): {offenders}")


def test_lexicon_does_not_whitelist_a_known_corrupt_form():
    """`lexicon.txt` was built from THIS corpus's own OCR output, so it absorbs
    the errors and then vindicates them - the structural hole documented for the
    ligature bug ("lexicon.txt cannot catch the ligature corruption - it contains
    it") and measured on 2026-08-26 at 22% of its entries having zero attestation
    in 6.18M words of independent text.

    It was purged twice by hand (24 dropped-lamed forms on 2026-08-15; 79 rows on
    2026-08-26) and NOTHING prevented re-contamination either time, because the
    file has no generator in this repo. This test is the gate that was missing:
    a form confirmed corrupt must never be in the dictionary that decides whether
    a word looks wrong.

    Adding to this list is how you keep a purge from silently undoing itself -
    when a reading is confirmed against the scan, put the corrupt form here."""
    corrupt = {
        # confirmed 2026-08-26, each read in context; see PROJECT-STATUS item 23
        "כסכתא", "בחרא", "כרתב", "שרוא", "בסרק", "בישרץ", "מקטי", "כתרייתא",
        "מאיין", "למיפך", "בתריתא", "זלזה", "איידו", "במשרו",
    }
    if not os.path.exists(os.path.join(REPO, "lexicon.txt")):
        pytest.skip("lexicon.txt not present")
    with open(os.path.join(REPO, "lexicon.txt"), encoding="utf-8") as f:
        lexicon = {w.strip() for w in f if w.strip()}
    offenders = sorted(corrupt & lexicon)
    assert not offenders, (
        f"lexicon.txt whitelists {len(offenders)} form(s) confirmed to be OCR corruption: "
        f"{offenders}. A word in the lexicon can never be flagged as not-a-word, so every "
        f"occurrence of these becomes invisible to check 5 of "
        f"validate_part1_corpus_integrity.py. Remove them, or - if one turns out to be a "
        f"real word after all - take it out of this test with the evidence.")


def test_machine_resolved_flags_agree_between_server_and_frontend():
    """A flag counted as machine-RESOLVED by the server but not by the frontend
    (or vice versa) renders the same word with two different verdicts on one
    screen - green in the text pane, "Machine-Disputed" in the nav and the panel
    header. That is what happened when `docai_ligature_artifact` was added as a
    second resolved flag and only `wordState()` learned about it."""
    review_server = _import_from_path("review_server", os.path.join(REPO, "pipeline", "review_server.py"))
    with open(os.path.join(REPO, "review_frontend", "app.js"), encoding="utf-8") as f:
        js = f.read()
    m = re.search(r"const MACHINE_RESOLVED_FLAGS = \[([^\]]*)\]", js)
    assert m, "review_frontend/app.js must define MACHINE_RESOLVED_FLAGS"
    frontend = {v.strip().strip("'\"") for v in m.group(1).split(",") if v.strip()}
    assert frontend == set(review_server.MACHINE_RESOLVED_FLAGS), (
        f"server {sorted(review_server.MACHINE_RESOLVED_FLAGS)} != frontend {sorted(frontend)}")


def test_no_open_flag_names_a_word_that_is_not_at_its_index(part1_by_id):
    """PROJECT-STATUS item 0C. ./rebuild_all.sh reindexes the CANDIDATE files
    when a klal's word count changes; review_decisions.jsonl is append-only and
    nothing reindexes it, so an open flag past the change keeps pointing at what
    is now a different word - a note attached to the wrong word, the same defect
    the reviewer caught by hand on 2026-08-18's spot-check batch.

    These notes name their own word ("בססחים w30 -> ...", "'!' w112 -> ..."), so
    the ledger can be checked against the corpus directly. That is what found
    klal 43 w14, whose `ממטונא` had drifted three words to w17, and klal 66 w135
    after a `!` was deleted from the same klal earlier in the run.

    apply_reviewer_decisions.reindex_flags_after_shift() now moves these at apply
    time; this is the check that says so. Only a MATCHED pair of quotes is a
    quote - a trailing geresh is part of the word (`סי'`, `בס'`), and stripping
    it makes three sound flags look moved."""
    ard = _import_from_path("apply_reviewer_decisions",
                            os.path.join(REPO, "pipeline", "apply_reviewer_decisions.py"))
    named = re.compile(r"^\s*(?:'([^']+)'|\"([^\"]+)\"|(\S+))\s+w(\d+)\b")
    offenders = []
    for klal_id, klal in sorted(part1_by_id.items()):
        words = klal["clean_text"].split(" ")
        for word_index, rec in sorted(ard.open_word_flags(klal_id).items()):
            m = named.match(rec.get("note") or "")
            if not m or int(m.group(4)) != word_index:
                continue        # the note does not name its own index; nothing to check
            word = m.group(1) or m.group(2) or m.group(3)
            live = words[word_index] if 0 <= word_index < len(words) else None
            if live != word:
                offenders.append((klal_id, word_index, word, live,
                                  words.index(word) if word in words else None))
    assert not offenders, (
        f"{len(offenders)} open flag(s) name a word that is not at their index, so the note is "
        f"attached to the wrong word (klal, index, note's word, word actually there, where the "
        f"named word is now): {offenders[:6]}")


def test_no_candidate_re_raises_a_word_an_applied_decision_already_settled(part1_by_id):
    """REGRESSION 2026-08-31, reviewer: "klal 61 I decided the dispute but the
    reading pane still shows red and yellow boxes".

    Correcting a word is exactly what makes part1.json disagree with the DocAI
    token stream there - the token still carries the error the reviewer just
    fixed - so every applied correction grew a brand-new candidate at its own
    position on the next rebuild, undecided, asking for a ruling on a settled
    word. 279 of them, 46% of the whole queue, and 39 rendered RED: the pipeline
    proposing to UNDO an applied fix (`שבועה` back to `שכועה`, `אבל` to `אכל`,
    `עמו` to `עטו`). It would have grown with every correction ever applied.

    The condition is deliberately narrow on both halves - APPLIED (a decision
    still awaiting promotion must keep the entry its ruling hangs on) and STILL
    MATCHING (if the corpus later moves off what they chose, the disagreement is
    real again and the candidate belongs). See
    build_corrections_dataset.settled_by_an_applied_decision()."""
    review_server = _import_from_path("review_server", os.path.join(REPO, "pipeline", "review_server.py"))
    records = {}
    with open(os.path.join(REPO, "review_decisions.jsonl"), encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                records[r["id"]] = r
    settled = {}
    for r in records.values():
        if r["decision_type"] != "apply_event":
            continue
        d = records.get(r.get("applied_decision_id"))
        if not d or d.get("word_index") is None or d["klal_id"] not in part1_by_id:
            continue
        words = part1_by_id[d["klal_id"]]["clean_text"].split(" ")
        chosen = (d.get("chosen_text") or "").split()
        if chosen and words[d["word_index"]:d["word_index"] + len(chosen)] == chosen:
            settled[(d["klal_id"], d["word_index"])] = d.get("chosen_text")

    corrections = review_server.cio.load_json(os.path.join(REPO, "corrections_part1.json")) or {}
    offenders = []
    for klal_id, entries in corrections.items():
        for e in entries:
            key = (int(klal_id), e["word_index"])
            if key in settled:
                offenders.append((key[0], key[1], e.get("flag"), settled[key]))
    assert not offenders, (
        f"{len(offenders)} candidate(s) sit on a word an applied human decision already settled, so "
        f"the reviewer is asked to rule again on their own applied fix (klal, word, flag, what they "
        f"chose): {offenders[:8]}")

def test_no_test_file_defines_the_same_test_name_twice():
    """REGRESSION 2026-08-31 (Lesson 37). `tests/test_review_server.py` defined
    `test_deep_link_lands_on_the_klal_and_rings_the_word` and
    `test_clicking_a_word_puts_it_in_the_address_bar` TWICE each. Python rebinds a
    name on the second `def`, so the first body was discarded at import - no
    error, no skip, no warning. 38 definitions collected as 36 tests, and the
    discarded copy was the STRICTER one in both cases (`len(ringed) == 1` against
    a bare `assert ringed`, plus a klal-only route the survivor never visited).

    The suite was green the whole time, which is the point: a shadowed test looks
    exactly like a passing one. This is the cheap check that makes the two numbers
    agree, and it is gated because nothing else in the chain compares them."""
    import ast
    offenders = {}
    tests_dir = os.path.join(REPO, "tests")
    for name in sorted(os.listdir(tests_dir)):
        if not (name.startswith("test_") and name.endswith(".py")):
            continue
        path = os.path.join(tests_dir, name)
        with open(path, encoding="utf-8") as fh:
            tree = ast.parse(fh.read(), filename=path)
        seen, dupes = set(), []
        for node in tree.body:      # module level only - a nested def is not collected
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                    and node.name.startswith("test_"):
                if node.name in seen:
                    dupes.append(f"{node.name} (line {node.lineno})")
                seen.add(node.name)
        if dupes:
            offenders[name] = dupes
    assert not offenders, (
        "a test name is defined twice, so the earlier body is silently discarded "
        f"and never runs: {offenders}"
    )

def test_every_part1_title_ends_with_exactly_one_period(part1_by_id):
    """ADDED 2026-08-31 (reviewer): "each title should end with one period - no
    more no less. no other punct acceptable."

    SCOPE IS PART 1 BY DESIGN. Parts 2-3 titles are machine truncations (`…`, and
    some are literally `כלל 447`) rather than transcribed headings, and they are
    under the Parts 2-3 gate - normalising their punctuation would be both
    forbidden and meaningless.

    `"` and `'` are deliberately NOT treated as punctuation here. They are
    gershayim and geresh, which belong to Hebrew ABBREVIATIONS - `ב"ד` (בית דין),
    `וכו'` - and stripping them would corrupt 121 and 80 occurrences. Five Part 1
    titles legitimately end `וכו'.`, keeping the geresh that is part of the word.
    """
    import re
    offenders = []
    for klal_id, klal in sorted(part1_by_id.items()):
        title = (klal.get("title") or "").strip()
        if not title:
            offenders.append((klal_id, "empty title", title))
        elif not title.endswith("."):
            offenders.append((klal_id, "no terminal period", title))
        elif title.endswith(".."):
            offenders.append((klal_id, "more than one terminal period", title))
        elif re.search(r"\.(?!$)", title):
            offenders.append((klal_id, "period before the end", title))
        elif re.search(r"[:,;•\[\]…]", title):
            offenders.append((klal_id, "punctuation other than the terminal period", title))
    assert not offenders, f"{len(offenders)} title(s) break the punctuation rule: {offenders[:6]}"
