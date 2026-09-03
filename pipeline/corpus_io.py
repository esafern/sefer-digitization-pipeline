# [PRODUCTION] Shared file-location and data-loading machinery for every
# script in pipeline/ and tools/ that reads this project's corpus, its
# derived artifacts, or its DocAI scan cache.
#
# Extracted 2026-08-17, the same round (and for the same reason) as
# pipeline/vision_adjudication_common.py: the vision trio's consolidation was
# triggered by finding ONE bug class three separate times in three
# hand-maintained copies of the same logic, and a survey of the wider
# pipeline/ + tools/ directories found the identical shape at a larger scale
# outside the vision code. Concrete, checked evidence per item extracted -
# not "these look similar":
#
#   * The DocAI page-token loader. Nine call sites independently wrote
#     `os.path.join(DOCAI_DIR, f"page_{n}.json")` + an exists-check +
#     json.load, four of them wrapped in a hand-rolled page cache with
#     identical get-or-load bodies (build_corrections_dataset.py,
#     build_klal_page_regions.py, check_klal_token_orphans.py,
#     validate_catchword_continuity.py, validate_klal_span_coverage.py,
#     verify_flagged_candidates_vision.py, verify_reconstruction_witness.py,
#     verify_witness_vision.py, review_server.py). Two of the nine differed
#     in a way that mattered and nobody had reconciled: some returned None
#     for a missing page, one returned [], and verify_reconstruction_
#     witness.py had no exists-check at all and would raise. Those
#     differences are now an explicit `default=` argument at each call site
#     instead of an accident of which copy you happened to read.
#
#   * `clean_word()` - `"".join(c for c in w if c.isalnum())` - byte-identical
#     in build_corrections_dataset.py, build_klal_page_regions.py and
#     validate_catchword_continuity.py. This is the normalization the
#     docai-token-vs-stored-text diff is built on; three copies of it is
#     three chances for one to be "improved" alone.
#
#   * `hebrew_letters_only()` - the SAME function written three different
#     ways: `"".join(c for c in s if c in HEB)` with a 27-character literal
#     (verify_witness_vision.py, verify_reconstruction_witness.py),
#     `re.sub(r"[^א-ת]", "", text)` (check_klal_token_orphans.normalize), and
#     a filter over validate_part1_corpus_integrity.HEBREW_LETTERS. Verified
#     equivalent, not assumed: the literal, the regex range U+05D0-U+05EA and
#     HEBREW_LETTERS are the same 27 code points (22 letters + 5 final
#     forms). Kept as one implementation with the constant beside it.
#
#   * `PART1_MAX_KLAL = 222` - three independent copies whose own comments
#     already named the drift risk ("Same literal, independently written, in
#     ... see the longer note at build_corrections_dataset.py's copy for what
#     each one silently does wrong if they ever disagree") and pushed the
#     problem onto a test that asserts all three agree. One definition is the
#     actual fix; the test now asserts the single constant against the corpus,
#     which is the part of it that was ever load-bearing.
#
#   * The corpus loaders. `load_klalim()` tolerates a `{"klalim": [...]}`
#     wrapper as well as a bare list - build_klalim_demo_dataset.py and
#     validate_title_alphabetical_order.py both carried that tolerance while
#     ten other readers of the same files did a bare `json.load(open(...))`,
#     so the wrapper shape was handled or not depending on which script you
#     came in through. `save_part1()` was byte-identical in
#     apply_reviewer_decisions.py and apply_punctuation_decisions.py - two
#     independent copies of the one function in this repo allowed to WRITE
#     the hand-edited source of truth, which is the last place a silent
#     divergence in serialization (ensure_ascii, indent) should be able to
#     happen.
#
#   * `trusted_klal_pages()` - build_corrections_dataset.py and
#     build_klal_page_regions.py had the same alignment-file filter loop
#     twice, differing only in that one also collected the untrusted ids.
#     That is a real difference in what the caller needs, not in the logic,
#     so it is a second return value here rather than two functions
#     (the same treatment vision_adjudication_common.py gives its
#     `has_model_column` parameter).
#
# Deliberately NOT extracted, having looked and decided against it:
#
#   * The three "page furniture" word sets (build_corrections_dataset.
#     WATERMARK_WORDS, check_klal_token_orphans.FURNITURE_WORDS,
#     validate_catchword_continuity.HEADER_WORDS + FURNITURE_RE). They LOOK
#     like the same concept and are not: they match by different rules
#     (lowercased-through-clean_word vs. exact raw-token equality vs. a
#     case-insensitive regex plus a gershayim guard) over deliberately
#     different contents. build_corrections_dataset.py's own comment already
#     records this as examined-and-left-alone 2026-08-15, with the reason: a
#     single shared set would silently change what each script strips. That
#     reasoning still holds; unifying them would be a data-affecting change
#     wearing a refactor's clothes.
#
#   * `tools/propose_punctuation_part1.py`'s sqlite cache. It is a
#     single-opaque-key table, not the five-column composite key
#     vision_adjudication_common.init_cache_table builds, and its own
#     docstring explains why the re-key it needed was a value-level
#     migration rather than that module's rename-and-recreate. Same
#     Lesson-12 discipline, genuinely different schema - forcing them
#     together would mean migrating a real cache of paid-for answers to
#     serve a refactor.
#
#   * The `REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))`
#     line itself, in all 27 scripts. It cannot be moved here: a tools/
#     script must compute the repo root BEFORE it can put pipeline/ on
#     sys.path to import this module at all. What can be removed is
#     everything DERIVED from it that was being re-derived per script -
#     DOCAI_DIR, PART1_PATH, PART1_MAX_KLAL, the loaders above - and that is
#     what this module does. Scripts that need nothing else from here keep
#     their own REPO line; adding a sys.path bootstrap purely to import a
#     one-line constant would be more boilerplate, not less.
#
#   * Per-script argparse setup. Nine scripts build an ArgumentParser; only
#     `--dry-run` appears in more than one, and the two that share it are
#     the two apply scripts, which already mirror each other deliberately.
#     Nothing here is copy-pasted-then-independently-patched - it is nine
#     different command-line interfaces that resemble each other because
#     argparse has one shape.
#
# Every function is parameterized (path/dir/default passed explicitly, with
# the canonical repo location as the default) rather than reading a caller's
# module-level globals, so a caller's own PART1_PATH/DOCAI_DIR attribute
# stays that script's single source of truth and stays monkeypatchable in
# tests exactly as before.
import difflib
import json
import os
import re
import sys


# ---------- where the corpus lives: the one runtime seam ----------
#
# THE PROBLEM THIS SOLVES, stated as item 0AR states it: the test-independence
# problem and the general-purpose problem are the SAME problem. This pipeline is
# meant to work on any historical Hebrew text, but the corpus location was a
# function of where THIS source file sits on disk - `dirname(dirname(__file__))`
# - so it could not be pointed at another book, and therefore could not be
# pointed at a test fixture either. 64 modules compute that same expression for
# themselves, and ~35 constants derive from it.
#
# Resolution order, and it is resolved at CALL time, never at import:
#   1. an explicit root set by set_corpus_root() - what `--corpus` uses
#   2. $SEFER_CORPUS_ROOT
#   3. the source-relative default (this file lives one level below the root),
#      which is what every existing caller gets when neither is set
#
# CALL TIME IS THE WHOLE POINT and it is not a style preference. The constants
# below were module-level assignments evaluated at import, so a caller that set
# the root afterwards changed nothing and got no error - silently the old path.
# That is the exact bug `review_decisions._resolve()` exists to document, and
# the reason this module now resolves its paths through PEP 562 `__getattr__`:
# `cio.PART1_PATH` is a fresh lookup every time. Nothing in this repo does
# `from corpus_io import PART1_PATH` (checked: zero occurrences), which is what
# makes that safe - a from-import would bind the value once and reintroduce the
# defect, so don't add one.
_CORPUS_ROOT_OVERRIDE = None

# The source-relative default: this module lives in pipeline/, one level below
# the repo root, where part1.json / docai_word_boxes / etc. live.
_DEFAULT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CORPUS_ROOT_ENV = "SEFER_CORPUS_ROOT"


def corpus_root():
    """The directory holding part1.json and the caches, resolved NOW."""
    if _CORPUS_ROOT_OVERRIDE:
        return _CORPUS_ROOT_OVERRIDE
    return os.environ.get(CORPUS_ROOT_ENV) or _DEFAULT_ROOT


def set_corpus_root(root):
    """Point every path in this module at `root` (None restores the default).

    Returns the previous override so a caller can restore it - tests use that
    rather than leaving a process-wide setting behind them.
    """
    global _CORPUS_ROOT_OVERRIDE
    previous = _CORPUS_ROOT_OVERRIDE
    _CORPUS_ROOT_OVERRIDE = os.path.abspath(root) if root else None
    return previous


def repo_path(*parts):
    return os.path.join(corpus_root(), *parts)


# Resolved on every attribute access, not at import - see the note above. The
# names and their meanings are unchanged; only the moment of resolution moved.
_LAZY_PATHS = {
    "REPO": lambda: corpus_root(),
    "DOCAI_DIR": lambda: repo_path("docai_word_boxes"),
    "PART1_PATH": lambda: repo_path("part1.json"),
    "PART_PATHS": lambda: [repo_path(n) for n in ("part1.json", "part2.json", "part3.json")],
    "DEMO_DATASET_PATH": lambda: repo_path("klalim_demo_dataset.json"),
    "ALIGNMENT_PATH": lambda: repo_path("part1_header_anchored_alignment.json"),
    "TRACE_PATH": lambda: repo_path("gematria_trace_part1.json"),
    "LEXICON_PATH": lambda: repo_path("lexicon.txt"),
}


def __getattr__(name):
    """PEP 562 module-level attribute hook: `cio.PART1_PATH` resolves here."""
    if name in _LAZY_PATHS:
        return _LAZY_PATHS[name]()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(list(globals()) + list(_LAZY_PATHS))

# max(klal_id) in part1.json. Part 1 is the only section with scan-linked
# correction/region data, so several scripts slice the combined 667-klal
# dataset down with this. Asserted against the live corpus by
# tests/test_corpus_invariants.py - the assertion is the load-bearing part
# and survives this consolidation; what does not survive (deliberately) is
# three separate literals having to agree with each other first.
PART1_MAX_KLAL = 222

# max(klal_id) in part2.json and part3.json. ADDED 2026-08-31, closing the
# oldest surviving finding of the 2026-08-25 review (S5, restated as the
# 2026-08-27 review's #6): `223`, `444` and `445` were inline literals in
# review_server.py's _get_part_num_for_klal() and _load_klalim(), with no
# constant and no test tying them to the data - so a klal added to or removed
# from part2/part3 would silently misclassify, and the review UI would serve
# the wrong part with no error anywhere.
#
# Measured against the live corpus, not copied from the review: part1 = 222
# klalim (1-222), part2 = 222 (223-444), part3 = 223 (445-667), contiguous,
# no gaps. The three ranges partition 1..667 exactly, which is what lets
# _get_part_num_for_klal use `<=` cutoffs at all.
#
# These get the same treatment PART1_MAX_KLAL gets and for the same reason:
# the assertion against the live corpus in tests/test_corpus_invariants.py is
# the load-bearing part, not the literal.
PART2_MAX_KLAL = 444
PART3_MAX_KLAL = 667

# First klal of each later part. Derived, never typed twice - the `223`/`445`
# literals were a second encoding of "one past the previous part's max", and
# an off-by-one between them and the max constants is exactly the silent
# misclassification this is here to prevent.
PART2_MIN_KLAL = PART1_MAX_KLAL + 1
PART3_MIN_KLAL = PART2_MAX_KLAL + 1


def union_bbox(tokens):
    """The single bounding box enclosing every token in `tokens`.

    MOVED HERE 2026-08-31 (finding H3, restated as the 2026-08-27 review's #8).
    This exact body lived byte-identically in build_corrections_dataset.py and
    build_klal_page_regions.py - two pipeline STAGES, both of which turn token
    runs into the boxes the reviewer clicks. That is the shared-module rule's
    own example case (Lesson 13): the copies agreed, which is what a second
    copy of the truth does right up until it doesn't.

    Assumes every token carries x1/y1/x2/y2 and that `tokens` is non-empty -
    both copies did, and both callers already guard for the empty case.
    """
    return {
        "x1": min(t["x1"] for t in tokens),
        "y1": min(t["y1"] for t in tokens),
        "x2": max(t["x2"] for t in tokens),
        "y2": max(t["y2"] for t in tokens),
    }


# ---------- THE word list for anything carrying a word_index ----------

def words_of(klal_or_text):
    """The canonical word list of a klal, for every caller that indexes it.

    ADDED 2026-08-31, the remedy finding S2 asked for on 2026-08-25 (restated
    as the 2026-08-27 review's S2 and as PROJECT-STATUS item 37(b), where the
    real count was measured at 27 sites across 14 files - and still growing:
    one of the 27 was written the same day as the sweep that counted them).

    **Space-only, deliberately, and this is the load-bearing sentence.** A
    `word_index` in this project means an index into `clean_text.split(' ')`,
    because that is what the dashboard's own click handler computes
    (`(k.clean_text || '').split(' ')`) and every decision in the append-only
    ledger was recorded against it. `str.split()` with no argument COLLAPSES
    runs of whitespace, so on a text with a double space it renumbers every
    word after that point - which silently points a stored decision, a deep
    link or a highlight at the wrong word. tools/build_open_items_report.py
    hit exactly that and its comment says so.

    Note the direction: the 2026-08-25 review proposed unifying on `.split()`.
    That recommendation is **wrong for this corpus** and is deliberately not
    followed - it would invalidate the word_index of every decision ever
    recorded. The scheme to converge on is the one the data is already in.

    This does NOT merge the two schemes. Machine candidate generation
    legitimately uses `.split()` (whitespace-collapsing) because it is
    diffing token streams, not addressing stored positions; those sites stay
    as they are. What this ends is the *unmarked* use of the space-only split
    in fourteen files, where the two schemes were told apart only by reading
    each call site and knowing which one it meant.

    Today the two agree - measured: 0 of 667 klalim have a double, leading or
    trailing space, which `test_no_double_spaces_in_clean_text` gates. That
    test guards the DATA. This function is what makes the CODE say which
    scheme it means, so the day a text with unusual whitespace does get in,
    the divergence is one function's problem instead of fourteen files'.

    Accepts a klal dict or a raw string, so callers holding either can ask
    the same question.
    """
    text = klal_or_text.get("clean_text") if isinstance(klal_or_text, dict) else klal_or_text
    return (text or "").split(" ")


def occurrence_of(words, index):
    """Which occurrence of `words[index]` this position is, 1-based.

    THE STABLE HALF OF A WORD'S ADDRESS. A `word_index` is invalidated by ANY
    edit earlier in the klal - measured over Part 1, an insertion or deletion at
    a random point invalidates 100% of the positions after it, which is what
    items 0AB (105 stale rulings), 0AP (40 re-pointed by hand) and Lesson 35 are
    all about. `(word, occurrence)` is invalidated only by an edit that adds or
    removes THE SAME WORD earlier in the same klal: 0.3% of later positions,
    averaged over every edit point in Part 1. That is 318x more edits survived.

    Why the ordinal and not the word alone: the bare word is not an address at
    all here. 47% of Part 1's word positions hold a word that repeats inside its
    own klal - klal 54 has 44 `לא`, klal 74 has 39 `אמר` - so `(klal, word)`
    names one position for barely half the corpus.

    And why this is not the "search the text for it" recovery that
    review_server._manual_snapshot explicitly REJECTS: that one asks "where does
    this word occur", and a unique match is not evidence of position. This
    records WHICH occurrence was ruled on at ruling time, so recovery is a
    lookup rather than a search. It is a second independent signal beside the
    snapshot's bbox (Lesson 9), not a replacement for it.

    Returns None for an out-of-range index rather than raising: a snapshot is an
    audit record and must never be the thing that stops a ruling being written.
    """
    if not (0 <= index < len(words)):
        return None
    target = words[index]
    return sum(1 for w in words[:index + 1] if w == target)


def index_of_occurrence(words, word, occurrence):
    """The index of the `occurrence`-th `word` in `words`, or None.

    The inverse of occurrence_of. None means the address no longer resolves -
    the word was corrected away, or the klal now holds fewer of them - which is
    a REPORTABLE state, not a reason to guess at a nearby position.
    """
    if not word or not occurrence or occurrence < 1:
        return None
    seen = 0
    for i, w in enumerate(words):
        if w == word:
            seen += 1
            if seen == occurrence:
                return i
    return None


def word_count_of(klal_or_text):
    """len(words_of(...)), for the callers that only compare counts."""
    return len(words_of(klal_or_text))


# `title` is corpus text too, and until 2026-09-03 nothing in this repo read it.
# Item 39 measured the consequence: six OCR errors sat in titles whose BODY was
# already correct, including the same alef-lamed ligature sort as items 26/32,
# because every detector, witness, validator and invariant here reads
# `clean_text` and only `clean_text`. A field no check has ever looked at has
# been verified about nothing (Lesson 1).
TITLE_FIELD = "title"
TEXT_FIELD = "clean_text"
CORPUS_TEXT_FIELDS = (TEXT_FIELD, TITLE_FIELD)


def title_words_of(klal):
    """The title's word list, addressed the same way `words_of` addresses a body.

    Space-only for the identical reason (see words_of): a `word_index` in a
    title_correction decision is an index into `title.split(' ')`, and the
    ledger is append-only, so the scheme has to be fixed before the first
    ruling is recorded rather than after.

    A title index and a body index are DIFFERENT ADDRESSES in the same klal -
    klal 39 word 2 is one word in the heading and another in the text - which
    is why a title ruling is its own decision type (`title_correction`) rather
    than a `manual_correction` carrying a field tag: `all_current()` keys on
    (klal_id, word_index), so a shared namespace would have let one silently
    overwrite the other.
    """
    return ((klal or {}).get(TITLE_FIELD) or "").split(" ")


# ---------- text normalization shared by readers of DocAI tokens ----------

def clean_word(w):
    """Punctuation/whitespace-stripped form used to compare a DocAI token
    against stored corpus text. Alphanumerics only - deliberately keeps Latin
    letters and digits (the Google Books watermark and printed folio numerals
    have to survive this in order to be recognized and filtered as furniture
    downstream)."""
    return "".join(c for c in w if c.isalnum())


# ---------- what work this corpus IS ----------
#
# ADDED 2026-09-01 (reviewer: "on index pane header should show book title also
# scan pane"). Here rather than in the frontend because this project's stated
# goal is to generalize beyond one work: the dashboard should NAME the book it
# has loaded, not have one book's name baked into its markup. A second text run
# through this pipeline changes these five lines and nothing else.
#
# The edition matters enough to carry: START_HERE.md warns at length against
# conflating the Livorno 1766-7 original with the Berlin reprint this pipeline
# actually OCRs, and the scan pane is the one place a reviewer is looking at
# that specific printing.
WORK_TITLE = "Yad Malachi"
WORK_TITLE_HE = "יד מלאכי"
WORK_SECTION = "Klalei HaGemara"
WORK_SECTION_HE = "כללי הגמרא"
WORK_EDITION = "Berlin, 1851/2 - the second printing, not the Livorno 1766-7 original"

# 22 Hebrew letters + the 5 final forms, i.e. exactly U+05D0-U+05EA. Written
# out rather than range-generated so it is greppable and so a reader can see
# what is in it; equivalence to the regex range the merged copies used is
# asserted in tests/test_pipeline_logic.py.
HEBREW_LETTERS = "אבגדהוזחטיכלמנסעפצקרשתךםןףץ"


# The generated stub a klal carries when the chunker created it but never filled
# it: the gematria marker plus a synthesised "כלל N" title, e.g. "רנ כלל 250".
#
# MOVED HERE 2026-08-26 (code review, flagged independently by both runs). This
# rule was written twice, byte-identical, in tools/export_corpus.py (_STUB_RE)
# and tools/reconstruct_placeholder_klalim.py (PLACEHOLDER_RE) - and the two are
# the two halves of ONE decision: which klalim get rebuilt, and which ship to
# Sefaria as an empty segment rather than as fabricated text under a real
# citation address. If they ever drift, either a real klal is dropped from the
# deliverable or a stub is published as text.
PLACEHOLDER_RE = re.compile(r"^\S+\s+כלל\s+\d+\s*$")


def is_placeholder(clean_text):
    """True when a klal stores only the generated placeholder, not real text."""
    return bool(PLACEHOLDER_RE.match(" ".join((clean_text or "").split())))


# The Google Books scan watermark ("Digitized by Google"), which sits at the
# foot of many pages of this scan. It is page furniture, never corpus content.
#
# MOVED HERE 2026-08-26 (code review): this lived only in
# build_corrections_dataset.py, so the filter existed but the one tool that
# writes corpus text from the raw token stream
# (tools/reconstruct_placeholder_klalim.py) did not use it - and wrote the
# watermark into 12 klalim. That is the standing rule's exact failure mode: the
# fix already existed in a sibling file which never got it.
WATERMARK_WORDS = {"digitized", "by", "google"}


def is_watermark(tok_text):
    """True when a raw OCR token is part of the scan watermark."""
    return clean_word(tok_text).lower() in WATERMARK_WORDS


def hebrew_letters_only(s):
    """Drop everything that is not a Hebrew letter - the normalization used
    when comparing two OCR engines' readings, or a reading against the
    lexicon, where gershayim/geresh/punctuation/spacing differences are noise
    rather than signal."""
    return "".join(c for c in s if c in HEBREW_LETTERS)


# Gershayim/geresh characters (real Unicode forms + ASCII surrogates this
# pipeline's OCR sometimes normalises them to). Consolidated here 2026-08-18:
# detect_ligature_corruption.py, detect_real_word_substitution.py,
# extract_abbreviation_forms.py, and propose_abbreviation_expansions.py each
# had their own copy.
QUOTE_CHARS = set('"\'׳״')


def has_gershayim(w):
    """True if w contains any gershayim/geresh character (abbreviation marker)."""
    return any(c in w for c in QUOTE_CHARS)


def align_witness(corpus_words, witness_words, normalize=hebrew_letters_only):
    """Map corpus word_index -> (witness's own word, verdict) for a second
    OCR/VLM reading of the same klal.

    verdict is "agrees" (the two align as an exact normalized match) or
    "differs" (an unambiguous one-for-one substitution at this position).
    A word_index absent from the result means this witness has NO usable
    reading there - either it dropped/added words around that point, or the
    disagreement is ragged enough that no single witness word corresponds to
    this one corpus word.

    ADDED 2026-08-23 (code review, finding C15). The function this replaces
    (assemble_corrections_dataset.build_vlm_alignment) walked only
    SequenceMatcher.get_matching_blocks(), and a matching block is BY
    DEFINITION a run where the two sequences are equal - so its output could
    only ever echo the corpus's own word back. Measured before the fix: 49,138
    aligned VLM words and 34,892 aligned Surya words, ZERO divergent in
    either. The `vlm_reading`/`surya_reading` fields it fed were therefore
    structurally incapable of reporting the disagreement they existed to
    surface.

    Why only 1:1 replace blocks count as a substitution, and everything else
    is dropped rather than guessed: inside a ragged replace block (n corpus
    words against m witness words, n != m) there is no principled way to say
    which witness word corresponds to which corpus word - pairing them
    positionally is exactly the "fuzzy match is not precise enough for an
    exact-position claim" failure Lesson 5 names, and it is the same defect
    the 2026-08-23 review found in tools/extract_*_consensus_disputes.py's
    get_docai_word_bboxes (260 of 16,026 bboxes taken from a replace opcode,
    i.e. from a token that is a DIFFERENT word). Anchor on the exact match
    first; report nothing rather than a guess.

    Comparison is on `normalize`d forms (Hebrew letters only by default, so
    gershayim/geresh/punctuation differences are not treated as disagreement),
    but the returned word is the witness's own RAW text - the reviewer needs
    to see what the engine actually produced, not a normalized form of it."""
    corpus_norm = [normalize(w) for w in corpus_words]
    witness_norm = [normalize(w) for w in witness_words]

    sm = difflib.SequenceMatcher(None, corpus_norm, witness_norm, autojunk=False)
    out = {}
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for offset in range(i2 - i1):
                out[i1 + offset] = (witness_words[j1 + offset], "agrees")
        elif tag == "replace" and (i2 - i1) == 1 and (j2 - j1) == 1:
            # Exactly one corpus word against exactly one witness word: the
            # correspondence is unambiguous even though the readings differ.
            out[i1] = (witness_words[j1], "differs")
    return out


def detector_args(argv, default_part=None):
    """Parse the argv every `tools/detect_*.py` sweep shares: an optional part
    file, and `--field clean_text|title`.

    ONE parser, six callers, added 2026-09-03 with the title pass. All six had
    written `sys.argv[1] if len(sys.argv) > 1 else PART1_PATH` - identical, and
    each would have needed its own `--field` handling. It also gives them a
    `--help` that does not run the sweep, which is the cheap half of item 0Z's
    lesson: `tools/patch_witness_word_indices.py` had no argument parsing at
    all and rewrote the witness queue when it was invoked with `--help`. These
    detectors only print, so nothing was at risk here - but the shape was the
    same, in six files.

    Returns (part_path, field). Raises SystemExit on `--help` or a bad field.
    """
    part_path, field = None, TEXT_FIELD
    args = list(argv)
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("-h", "--help"):
            raise SystemExit(
                f"usage: {os.path.basename(sys.argv[0] if sys.argv else 'detector')} "
                f"[part_file] [--field {'|'.join(CORPUS_TEXT_FIELDS)}] [--corpus DIR]\n"
                f"  part_file   defaults to part1.json\n"
                f"  --field     which corpus text to sweep; `title` is item 39's "
                f"title pass and addresses title.split() indices, NOT body ones.\n"
                f"  --corpus    the book to read (default ${CORPUS_ROOT_ENV}, else this repo)"
            )
        if a == "--corpus":
            if i + 1 >= len(args):
                raise SystemExit("--corpus needs a directory")
            set_corpus_root(args[i + 1])
            i += 2
            continue
        if a.startswith("--corpus="):
            set_corpus_root(a.split("=", 1)[1])
            i += 1
            continue
        if a == "--field":
            if i + 1 >= len(args):
                raise SystemExit("--field needs a value")
            field = args[i + 1]
            i += 2
            continue
        if a.startswith("--field="):
            field = a.split("=", 1)[1]
            i += 1
            continue
        if a.startswith("-"):
            raise SystemExit(f"unknown option {a!r}")
        part_path = a
        i += 1
    if field not in CORPUS_TEXT_FIELDS:
        raise SystemExit(f"unknown --field {field!r}; expected one of {', '.join(CORPUS_TEXT_FIELDS)}")
    part_path = part_path or default_part or repo_path("part1.json")
    if not os.path.isabs(part_path):
        part_path = os.path.join(corpus_root(), part_path)
    return part_path, field


def load_klal_words(part_path, field=TEXT_FIELD):
    """Load a part file and return {klal_id: [words]}, split the same way
    every index-bearing pipeline script does (str.split() with no argument,
    whitespace-collapsing). Consolidated here 2026-08-18 from identical
    copies in detect_ligature_corruption.py and detect_real_word_substitution.py.

    `field` added 2026-09-03 for item 39's title pass. Six detectors call this
    function and none of them could see the `title` field; parameterising the
    ONE loader gives all six title coverage in a single place, which is the
    point of this module existing (START_HERE's shared-module rule). A klal with
    no title yields an empty list rather than being dropped, so callers that
    index by klal_id still find every klal.

    Note the split: whitespace-collapsing here, because these callers diff token
    streams rather than address stored positions. `title_words_of` is the
    space-only one, for anything that records an index. Same two schemes, same
    reason, spelled out in words_of.
    """
    if field not in CORPUS_TEXT_FIELDS:
        raise ValueError(f"unknown corpus text field {field!r}; expected one of {CORPUS_TEXT_FIELDS}")
    klalim = load_klalim(part_path)
    out = {}
    for k in klalim:
        words = (k.get(field) or "").split()
        if field == TITLE_FIELD:
            words = strip_title_terminal_period(words)
        out[k["klal_id"]] = words
    return out


def strip_title_terminal_period(words):
    """Drop the sentence period every title in this corpus ends with.

    Measured 2026-09-03 across Part 1: **all 222 titles end in `.` and none
    contains one anywhere else**, so this is a display convention of the field
    (item 45 - the reviewer asked for the period to be SHOWN), not part of the
    last word. Without stripping it, every title's final token is a form that
    occurs exactly once in the corpus, which is precisely the trigger condition
    for the rare-form detectors - the first title run produced
    `מעצמנו.` -> `מעצמו` on klal 144 purely because of the glued period, on a
    word the body spells the same way and spells correctly.

    Index-preserving: it edits the last element, never removes one, so a
    `word_index` into the result still addresses the same word as
    `title_words_of`.
    """
    if words and words[-1].endswith(".") and len(words[-1]) > 1:
        words = words[:-1] + [words[-1][:-1]]
    return words


# ---------- DocAI token geometry ----------

def center_y(tok):
    """A token's vertical CENTER - the "are these two tokens on the same
    printed line" signal throughout this pipeline.

    Extracted 2026-08-17 from three independent copies (build_gematria_
    trace.center_y, a nested redefinition inside build_klal_page_regions.
    marker_anchored_regions, and an inline expression written twice in
    verify_reconstruction_witness.py). Not merely similar - all three exist
    for the identical measured reason, each recorded separately in its own
    comment: a marginal numeral and the taller bold word beside it on the
    SAME line do not share a y1 (measured 0.007 apart on klal 3/4, a third
    of a line), so y1 mis-sorts them and centers do not.
    """
    return (tok["y1"] + tok["y2"]) / 2


# ---------- gematria (Hebrew numeral) conversion ----------
# Moved here 2026-08-17 from tools/validate_part1_corpus_integrity.py, the
# only prior owner, so pipeline/build_gematria_trace.py (new, generic
# marker-detection script for Parts 2-3 and beyond) can reuse the same
# tested conversion instead of a second copy - directly exercising the
# "reusable pipeline" goal (CLAUDE.md) rather than deferring it.

GEMATRIA_VALUES = {
    "א": 1, "ב": 2, "ג": 3, "ד": 4, "ה": 5, "ו": 6, "ז": 7, "ח": 8, "ט": 9,
    "י": 10, "כ": 20, "ל": 30, "מ": 40, "נ": 50, "ס": 60, "ע": 70, "פ": 80,
    "צ": 90, "ק": 100, "ר": 200, "ש": 300, "ת": 400,
}

# Only נ/פ/צ (not כ/מ) traditionally take their final form at the end of a
# *multi-letter* Hebrew numeral in this kind of typesetting (e.g. 150 is
# printed קן not קנ, 190 is קץ not קצ) - but a lone single-letter numeral
# (20 = כ, 40 = מ, 50 = נ, 80 = פ, 90 = צ) stays in regular form, and כ/מ
# never finalize even in a multi-letter numeral (120 = קכ not קך, 140 = קמ
# not קם, 220 = רכ not רך). Confirmed against part1.json's own
# already-crop-verified gematria field for every case in both directions
# (2026-08-07, PROJECT-STATUS.md "New standing check
# validate_part1_corpus_integrity.py added") - an earlier version of this
# function applied the substitution unconditionally to any of the 5
# final-letter-eligible letters, which was right for 150/180/190 but wrong
# for 20/40/50/80/90/120/140/220.
FINAL_FORMS = {"נ": "ן", "פ": "ף", "צ": "ץ"}


# The running-header and section-header vocabulary, in the forms DocAI actually
# produces them - `יד מלאכי כללי <letter-section>` plus the OCR variants of both
# header words. This is page furniture: it is stripped from clean_text by
# construction, so it must never be MATCHABLE when aligning corpus text to a
# page's tokens either.
#
# MOVED HERE 2026-08-26: it lived in tools/check_span_shortfall.py, so
# review_server's own alignment could not see it, and 8 Part-1 words were
# aligned to a page header instead of their real token (klal 7 w497 among them -
# see PROJECT-STATUS.md item 23). Third instance of the same standing-rule
# failure this week, after is_watermark and is_placeholder.
FURNITURE_WORDS = {
    hebrew_letters_only(w) for w in (
        "יד", "יר", "יך",                      # running header, word 1 + OCR variants
        "מלאכי", "מלרכי", "מראכי", "מררכי",    # ...word 2 + the variants the corpus
                                                #    invariant's `מ[לר][אר]כי` admits
        "כללי",                                 # section header, word 1
        "האלף", "הבית", "הגימל", "הדלת",
        "ההא", "הוו", "הזין", "החית", "הטית",
        "היוד", "הכף", "הלמד", "המם", "הנון",
        "הסמך", "העין", "הפא", "הצדי", "הקוף",
        "הריש", "השין", "התיו",
    )
}

# A token whose centre sits in the top this-fraction of a page's vertical extent
# is in the running-header band. Measured on this scan: header tokens land at
# <=0.006, the first body line at >=0.03.
HEADER_BAND_MAX_REL_Y = 0.02


def header_furniture_indices(tokens, band=HEADER_BAND_MAX_REL_Y):
    """Indices of `tokens` that are the page's running header, folio or
    watermark - i.e. ink that is never part of any klal's text.

    The band test is what keeps this safe: `כללי` is ordinary vocabulary in this
    work (`כללי הגמרא`), and only the copy printed at the very top of the page is
    furniture.
    """
    ys = [center_y(t) for t in tokens]
    if not ys:
        return set()
    lo, hi = min(ys), max(ys)
    span = (hi - lo) or 1.0
    out = set()
    for i, t in enumerate(tokens):
        text = t.get("text") or ""
        if is_watermark(text):
            out.add(i)
            continue
        if (center_y(t) - lo) / span >= band:
            continue
        if hebrew_letters_only(text) in FURNITURE_WORDS or text.strip().isdigit():
            out.add(i)
    return out


# The five Hebrew letters that take a distinct form at the end of a word. A
# word-final plain form is not a spelling variant, it is orthographically
# impossible - so a proposed READING carrying one cannot be what the page says.
FINAL_FORMS_REQUIRED = {"כ": "ך", "מ": "ם", "נ": "ן", "פ": "ף", "צ": "ץ"}


def impossible_final_form(reading):
    """True when `reading` ends in a letter that Hebrew requires to be final.

    ADDED 2026-08-31, reviewer, on klal 36 w61: "why was ctc considered? cof is
    impossible here, would be cof sofit." DocAI had read `כתכ` against the stored
    `כתב`, and a vision call was spent adjudicating a string that cannot be a
    Hebrew word. This is the cheap orthographic check that settles it first.

    ABBREVIATIONS ARE EXEMPT, and that exemption is the whole subtlety - it is
    the same one item 33's trailing-resh rule needed. An abbreviation does not
    obey final-form orthography: `ה"נ` (הכי נמי) legitimately ends in a plain nun
    because the nun is an initial, not a word ending. Without this the rule
    returns a false positive on every gershayim form it meets.

    Multi-word readings are judged on their LAST word only; a garbled two-token
    reading like `חרא רבפ` is still caught by its own final letter.
    """
    if not reading:
        return False
    last = reading.split()[-1] if reading.split() else ""
    if not last or '"' in last or "'" in last or "\u05f3" in last or "\u05f4" in last:
        return False          # an abbreviation - final-form rules do not apply
    letters = hebrew_letters_only(last)
    return len(letters) > 1 and letters[-1] in FINAL_FORMS_REQUIRED


def title_word_span(title, clean_text):
    """How many words at the START of `clean_text` (after the gematria marker)
    the klal's printed HEADING occupies. 0 when the two do not agree at all.

    ADDED 2026-08-31. The heading is not a separate string in the book - it IS
    the opening of the klal, set in larger type, and `title` is a transcription
    of it. So rendering the title means styling a PREFIX of the body, and every
    surface that wants to do that needs the same answer: the review UI (which
    sets the heading in its own face inline), and
    tools/compare_titles_to_text.py (which audits the field). Defined once here
    rather than in each, per the shared-module rule.

    Editorial punctuation tokens the body carries and the heading does not
    (`,` `.` `[.]` `•`) are skipped, not counted as a mismatch - otherwise a
    comma the punctuation pass inserted truncates the span at that word.

    Returns a count of RAW body words (punctuation included), so the caller can
    index `words_of(klal)` with it directly.
    """
    tw = (title or "").split()
    words = words_of(clean_text)
    if not tw or not words:
        return 0
    matched, consumed = 0, 0
    for raw in words[1:]:                     # words[0] is the gematria marker
        consumed += 1
        if not (hebrew_letters_only(raw) or any(c.isalnum() for c in raw)):
            continue                          # editorial punctuation - skip, don't fail
        if matched >= len(tw):
            break
        if hebrew_letters_only(raw) != hebrew_letters_only(tw[matched]):
            return 0 if matched == 0 else consumed - 1
        matched += 1
        if matched == len(tw):
            return consumed
    return consumed if matched == len(tw) else 0


def klal_id_to_gematria(n):
    """Standard Hebrew numeral spelling, with the תשע"ו-style 15/16
    exception (ט"ו/ט"ז instead of י"ה/י"ו, which would spell divine
    names) - same convention part1.json's own `gematria` field uses.
    See FINAL_FORMS above for the word-final-letter substitution rule."""
    hundreds = [(400, "ת"), (300, "ש"), (200, "ר"), (100, "ק")]
    tens = [(90, "צ"), (80, "פ"), (70, "ע"), (60, "ס"), (50, "נ"), (40, "מ"),
            (30, "ל"), (20, "כ"), (10, "י")]
    ones = [(9, "ט"), (8, "ח"), (7, "ז"), (6, "ו"), (5, "ה"), (4, "ד"),
            (3, "ג"), (2, "ב"), (1, "א")]
    rem, letters = n, []
    for val, ch in hundreds:
        while rem >= val:
            letters.append(ch)
            rem -= val
    if rem == 15:
        letters += ["ט", "ו"]
        rem = 0
    elif rem == 16:
        letters += ["ט", "ז"]
        rem = 0
    else:
        for val, ch in tens:
            if rem >= val:
                letters.append(ch)
                rem -= val
        for val, ch in ones:
            if rem >= val:
                letters.append(ch)
                rem -= val
    if len(letters) > 1 and letters[-1] in FINAL_FORMS:
        letters[-1] = FINAL_FORMS[letters[-1]]
    return "".join(letters)


def gematria_to_value(s):
    """Sum of letter values, ignoring punctuation - for parsing a
    self-reference numeral out of running text, not for validating a
    known-position marker (which the trace/alignment tooling does with
    real docai positions, not this arithmetic-only approach)."""
    return sum(GEMATRIA_VALUES.get(c, 0) for c in s)


# ---------- generic JSON reads ----------

def load_json(path, default=None):
    """json.load with the exists-check every caller was writing by hand.
    `default` is returned for a missing file; pass no default (None) only
    where a missing file genuinely means "nothing", not "misconfigured"."""
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_repo_json(name, default=None):
    """load_json against a repo-root-relative name."""
    return load_json(repo_path(name), default)


# ---------- corpus text (part*.json, klalim_demo_dataset.json) ----------

def load_klalim(path):
    """Load a klal list from a part file or the combined demo dataset.

    Tolerates both stored shapes - a bare list, and a `{"klalim": [...]}`
    wrapper. Both shapes have existed in this repo's history; two scripts
    carried the tolerance and ten did not, so whether a wrapped file loaded
    depended on which reader you came in through. One implementation removes
    that.
    """
    data = load_json(path)
    if isinstance(data, dict) and "klalim" in data:
        return data["klalim"]
    return data


def load_part1(path=None):
    """Part 1's klalim, in stored file order (NOT sorted - several callers
    write the list back out and must not reorder it; use load_part1_sorted()
    when order matters for reading)."""
    return load_klalim(path or repo_path("part1.json"))


def load_part1_sorted(path=None):
    return sorted(load_part1(path), key=lambda k: k["klal_id"])


def load_part1_by_id(path=None):
    return {k["klal_id"]: k for k in load_part1(path)}


def save_part1(klalim, path=None):
    """The ONE serialization used to write the hand-edited source of truth.

    `ensure_ascii=False, indent=2` is not a style preference here - it is the
    on-disk format part1.json is tracked in, and a writer that disagreed
    would rewrite the whole file as a diff on every apply. Two independent
    copies of this existed (apply_reviewer_decisions.py,
    apply_punctuation_decisions.py); the corpus writers are the last place a
    silent divergence should be possible.
    """
    path = path or repo_path("part1.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(klalim, f, ensure_ascii=False, indent=2)


def load_demo_dataset(path=None):
    return load_klalim(path or repo_path("klalim_demo_dataset.json"))


# ---------- DocAI scan cache (docai_word_boxes/) ----------

def docai_page_path(page, docai_dir=None):
    docai_dir = docai_dir or repo_path("docai_word_boxes")
    return os.path.join(docai_dir, f"page_{page}.json")


def load_docai_page(page, docai_dir=None, default=None):
    """Raw, UNFILTERED token list for one scan page, or `default` if that
    page was never extracted.

    Deliberately unfiltered: gematria_trace_part1.json's marker_position
    indexes into this exact array, so dropping punctuation-only tokens (which
    a content diff must do - see build_corrections_dataset.py, 2026-08-07)
    at load time would shift every marker index by the number of punctuation
    tokens before it. Callers that need a filtered stream filter locally,
    where the choice is visible.
    """
    return load_json(docai_page_path(page, docai_dir), default)


class DocaiPageCache:
    """Memoizing wrapper over load_docai_page for the scripts that walk many
    klal spans across the same pages. Four scripts had a hand-written
    get-or-load cache with the same body; the only real difference between
    them was what a missing page returned, which is a constructor argument
    here rather than a per-copy accident.
    """

    def __init__(self, docai_dir=None, default=None):
        self.docai_dir = docai_dir
        self.default = default
        self._pages = {}

    def get(self, page):
        if page not in self._pages:
            self._pages[page] = load_docai_page(page, self.docai_dir, self.default)
        return self._pages[page]


# ---------- scan-linkage data (alignment, gematria trace) ----------

def load_gematria_trace(path=None, default=None):
    path = path or repo_path("gematria_trace_part1.json")
    """The raw trace list. Callers reshape it themselves (by klal_id, or
    page -> marker positions) and filter on marker_position/status
    differently on purpose - see check_klal_token_orphans.py, which accepts
    both 'ok' and 'marker_found_content_mismatch', vs. build_klal_page_
    regions.py, which requires 'ok'."""
    return load_json(path, default)


def trusted_klal_pages(path=None, max_klal=None):
    """(page -> [klal_id, ...], [untrusted klal_id, ...]) from the
    header-anchored alignment, trusted entries only, klal_id order preserved
    within each page (which matches print order).

    Per CLAUDE.md Lesson 15, an untrusted alignment entry is not a
    low-confidence candidate - it is silence: no candidate is generated for
    that klal at all. The untrusted list is returned rather than discarded so
    a caller can report that silence instead of it being invisible.
    """
    alignment = load_json(path or repo_path("part1_header_anchored_alignment.json"), [])
    max_klal = PART1_MAX_KLAL if max_klal is None else max_klal
    klal_pages = {}
    untrusted_ids = []
    for r in sorted(alignment, key=lambda r: r["klal_id"]):
        if not (1 <= r["klal_id"] <= max_klal):
            continue
        if not r["trusted"]:
            untrusted_ids.append(r["klal_id"])
            continue
        klal_pages.setdefault(r["matched_page"], []).append(r["klal_id"])
    return klal_pages, untrusted_ids


def trusted_klal_pages_with_continuations(alignment_path=None,
                                          max_klal=PART1_MAX_KLAL,
                                          regions_path=None):
    """Like trusted_klal_pages(), but also maps each continuation page to its
    klal_id (from klal_page_regions.json's ``continuations`` arrays).

    Without this, build_corrections_dataset.py only diffs a klal's text
    against the DocAI tokens of the page the klal STARTS on. For the 56
    klalim that continue onto the next page (some onto two), the continuation
    words never generated correction candidates - and api_page() never served
    them.

    Returns the same (page -> [klal_id, ...], untrusted_ids) shape. klal_id
    order within a page is start-klals first (in ascending klal_id), then
    continuation-klals (in ascending klal_id) - matches print order on the
    physical scan.
    """
    klal_pages, untrusted_ids = trusted_klal_pages(alignment_path, max_klal)

    trusted_klals = set()
    for ids in klal_pages.values():
        trusted_klals.update(ids)

    if regions_path is None:
        regions_path = repo_path("klal_page_regions.json")
    # `or {}`: load_json returns None for an absent file, and this used to go
    # straight into .items() - an AttributeError from deep inside stage 2 of
    # rebuild_all.sh rather than "the regions file is missing". The file is
    # tracked, so this is a deleted-file case, not a fresh-clone one; it should
    # still degrade to "no continuations known" instead of a stack trace.
    # (2026-08-27 audit, verified 2026-08-27.)
    regions = load_json(regions_path) or {}

    for kid_str, region in regions.items():
        kid = int(kid_str)
        if kid not in trusted_klals:
            continue
        for cont in region.get("continuations", []):
            page = cont["page"]
            klal_pages.setdefault(page, [])
            if kid not in klal_pages[page]:
                klal_pages[page].append(kid)

    # Sort each page's klal list by ascending klal_id. Continuation klals
    # always have a lower klal_id than start klals on the same page (they
    # started earlier, on a previous page), so ascending klal_id matches
    # physical print order on the scan - which is what SequenceMatcher
    # needs for the word stream to align with the DocAI token stream.
    for page in klal_pages:
        klal_pages[page].sort()

    return klal_pages, untrusted_ids
