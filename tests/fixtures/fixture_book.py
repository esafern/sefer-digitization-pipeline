# [PRODUCTION] The tiny synthetic book itself, as data. No path-resolution,
# no I/O - build_fixture_corpus.py turns this into files, tests/conftest.py
# hands the built directory to the test suite.
#
# WHY THIS MODULE EXISTS AT ALL, separately from the generator. Item 0AR:
# "I want to test the code not the material because this will be a general
# purpose util." The book here has NOTHING to do with Yad Malachi - four
# invented klalim, two invented pages, alphabet-letter placeholder words
# (same convention test_pipeline_logic.py already uses: "אלף בית גימל") - and
# every condition below is named for the CODE PATH it exists to exercise, not
# for anything a real reviewer would read. If this module ever needs a fact
# about the real corpus to stay correct, that is itself a bug: the point of a
# fixture is that it owes the real book nothing.
#
# ONE OF EACH CONDITION the review UI branches on, per 0AR's own list, and
# where each one lives:
#   - a klal spanning a page break ................. klal 1 (page 1 -> 2)
#   - a word whose page != its klal's start page .... klal 1 words 5-7
#   - two identical adjacent words ................... klal 1 words 2-3 ("בית בית")
#   - an editorial mark ............................... klal 1 word 4 ("[.]")
#   - a title with a terminal period .................. every title (book convention)
#   - a human decision (manual_correction) ............ klal 2 word 3
#   - a punctuation candidate .......................... klal 2, before word 2
#   - both machine-resolved flags ...................... klal 2 words 4-5 (injected, see generator)
#   - a word-level ai_flag, left OPEN .................. klal 3 word 2
#   - an answered flag standing alone .................. klal 3 word 3
#   - a `possible_omission` at len(words) .............. klal 3, after its last word (injected)
#   - two candidates colliding at one index ........... klal 3 word 1 (injected;
#       delete + replace, not two deletes - see build_fixture_corpus.py's
#       comment on why two GAPS specifically is a currently-forbidden state)
#   - witness rows with and without a word_index ....... klal 4 (both rows)
#
# Nothing here calls a paid API (Gemini vision verification, Tesseract-vs-
# DocAI witness generation) - those stages are either skipped or their output
# is fabricated directly, in the exact schema the real stage produces, with
# the substitution named at the point it happens. See build_fixture_corpus.py
# for which pieces are RUN (the real pipeline scripts, on this data) and which
# are INJECTED (and why each one is).

WORK_TITLE = "Fixture Sefer"
WORK_TITLE_HE = "ספר הבדיקה"
SECTION = "Fixture Section"
SECTION_HE = "פרק הבדיקה"

# --- Page 1 -------------------------------------------------------------
# Klal 1 opens here and runs through its editorial mark; its last three words
# are on page 2 (the continuation).
PAGE1_KLAL1_WORDS = ["א", "אלף", "בית", "בית", "[.]"]

# --- Page 2 ---------------------------------------------------------------
# Klal 1's continuation, then klal 2 in full, then klal 3 in full, then klal 4
# (klal 4 carries no body defect of its own - it exists only to anchor the
# witness-queue rows, which are addressed by page/bbox, not by corpus index).
PAGE2_KLAL1_CONT_WORDS = ["גימל", "דלת", "הא"]  # klal 1 words 5-7
PAGE2_KLAL2_WORDS = ["ב", "וו", "זין", "חית", "טית", "יוד"]
PAGE2_KLAL3_WORDS = ["ג", "כף", "למד", "מם", "נון"]
PAGE2_KLAL4_WORDS = ["ד", "סמך", "עין", "פא"]

KLALIM = [
    {
        "klal_id": 1,
        "title": "אלף בית.",
        "section": SECTION,
        "gematria": "א",
        "page": 1,
        "clean_text": " ".join(PAGE1_KLAL1_WORDS + PAGE2_KLAL1_CONT_WORDS),
    },
    {
        "klal_id": 2,
        "title": "וו.",
        "section": SECTION,
        "gematria": "ב",
        "page": 2,
        "clean_text": " ".join(PAGE2_KLAL2_WORDS),
    },
    {
        "klal_id": 3,
        "title": "כף.",
        "section": SECTION,
        "gematria": "ג",
        "page": 2,
        "clean_text": " ".join(PAGE2_KLAL3_WORDS),
    },
    {
        "klal_id": 4,
        "title": "סמך.",
        "section": SECTION,
        "gematria": "ד",
        "page": 2,
        "clean_text": " ".join(PAGE2_KLAL4_WORDS),
    },
]

# --- The DocAI reading of each page, in reading order -----------------------
# Deliberately differs from the stored text in exactly one place: klal 2's
# "חית" is misread as "חתי", an ordinary letter-transposition replace a real
# difflib-based diff finds on its own - no book-specific heuristic involved.
# It is also the position the human manual_correction (below) is recorded
# against, so the pipeline's own correction candidate and the human's
# decision address the SAME word, on purpose.
#
# Klal 1's continuation (page 2) reads back EXACTLY what is stored, with no
# typo here. That correction, and the region `continuations` entry that lets
# a reviewer reach it at all, are INJECTED by build_fixture_corpus.py instead
# of earned through the real diff/region pipeline - see that module's header
# for why: attributing a klal's continuation onto a later page is done by
# Y-COORDINATE banding against a page's actual printed layout
# (marker_anchored_regions() in build_klal_page_regions.py), which is exactly
# the kind of print-specific geometry heuristic a two-line synthetic page has
# no realistic version of. Forcing it to fire here would make this fixture a
# test OF that heuristic, not a test of what CONSUMES its output.
PAGE1_DOCAI_WORDS = list(PAGE1_KLAL1_WORDS)
PAGE2_DOCAI_WORDS = (
    list(PAGE2_KLAL1_CONT_WORDS)
    + ["ב", "וו", "זין", "חתי", "טית", "יוד"]  # "חתי" for "חית"
    + PAGE2_KLAL3_WORDS
    + PAGE2_KLAL4_WORDS
)
