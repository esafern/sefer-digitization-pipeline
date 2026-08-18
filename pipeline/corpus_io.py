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
import json
import os


# This module lives in pipeline/, one level below the repo root, where
# part1.json / docai_word_boxes / etc. live.
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def repo_path(*parts):
    return os.path.join(REPO, *parts)


DOCAI_DIR = repo_path("docai_word_boxes")
PART1_PATH = repo_path("part1.json")
PART_PATHS = [repo_path(name) for name in ("part1.json", "part2.json", "part3.json")]
DEMO_DATASET_PATH = repo_path("klalim_demo_dataset.json")
ALIGNMENT_PATH = repo_path("part1_header_anchored_alignment.json")
TRACE_PATH = repo_path("gematria_trace_part1.json")
LEXICON_PATH = repo_path("lexicon.txt")

# max(klal_id) in part1.json. Part 1 is the only section with scan-linked
# correction/region data, so several scripts slice the combined 667-klal
# dataset down with this. Asserted against the live corpus by
# tests/test_corpus_invariants.py - the assertion is the load-bearing part
# and survives this consolidation; what does not survive (deliberately) is
# three separate literals having to agree with each other first.
PART1_MAX_KLAL = 222


# ---------- text normalization shared by readers of DocAI tokens ----------

def clean_word(w):
    """Punctuation/whitespace-stripped form used to compare a DocAI token
    against stored corpus text. Alphanumerics only - deliberately keeps Latin
    letters and digits (the Google Books watermark and printed folio numerals
    have to survive this in order to be recognized and filtered as furniture
    downstream)."""
    return "".join(c for c in w if c.isalnum())


# 22 Hebrew letters + the 5 final forms, i.e. exactly U+05D0-U+05EA. Written
# out rather than range-generated so it is greppable and so a reader can see
# what is in it; equivalence to the regex range the merged copies used is
# asserted in tests/test_pipeline_logic.py.
HEBREW_LETTERS = "אבגדהוזחטיכלמנסעפצקרשתךםןףץ"


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


def load_klal_words(part_path):
    """Load a part file and return {klal_id: [words]}, split the same way
    every index-bearing pipeline script does (str.split() with no argument,
    whitespace-collapsing). Consolidated here 2026-08-18 from identical
    copies in detect_ligature_corruption.py and detect_real_word_substitution.py.
    """
    klalim = load_klalim(part_path)
    out = {}
    for k in klalim:
        out[k["klal_id"]] = k["clean_text"].split()
    return out


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


def load_part1(path=PART1_PATH):
    """Part 1's klalim, in stored file order (NOT sorted - several callers
    write the list back out and must not reorder it; use load_part1_sorted()
    when order matters for reading)."""
    return load_klalim(path)


def load_part1_sorted(path=PART1_PATH):
    return sorted(load_part1(path), key=lambda k: k["klal_id"])


def load_part1_by_id(path=PART1_PATH):
    return {k["klal_id"]: k for k in load_part1(path)}


def save_part1(klalim, path=PART1_PATH):
    """The ONE serialization used to write the hand-edited source of truth.

    `ensure_ascii=False, indent=2` is not a style preference here - it is the
    on-disk format part1.json is tracked in, and a writer that disagreed
    would rewrite the whole file as a diff on every apply. Two independent
    copies of this existed (apply_reviewer_decisions.py,
    apply_punctuation_decisions.py); the corpus writers are the last place a
    silent divergence should be possible.
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(klalim, f, ensure_ascii=False, indent=2)


def load_demo_dataset(path=DEMO_DATASET_PATH):
    return load_klalim(path)


# ---------- DocAI scan cache (docai_word_boxes/) ----------

def docai_page_path(page, docai_dir=DOCAI_DIR):
    return os.path.join(docai_dir, f"page_{page}.json")


def load_docai_page(page, docai_dir=DOCAI_DIR, default=None):
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

    def __init__(self, docai_dir=DOCAI_DIR, default=None):
        self.docai_dir = docai_dir
        self.default = default
        self._pages = {}

    def get(self, page):
        if page not in self._pages:
            self._pages[page] = load_docai_page(page, self.docai_dir, self.default)
        return self._pages[page]


# ---------- scan-linkage data (alignment, gematria trace) ----------

def load_gematria_trace(path=TRACE_PATH, default=None):
    """The raw trace list. Callers reshape it themselves (by klal_id, or
    page -> marker positions) and filter on marker_position/status
    differently on purpose - see check_klal_token_orphans.py, which accepts
    both 'ok' and 'marker_found_content_mismatch', vs. build_klal_page_
    regions.py, which requires 'ok'."""
    return load_json(path, default)


def trusted_klal_pages(path=ALIGNMENT_PATH, max_klal=PART1_MAX_KLAL):
    """(page -> [klal_id, ...], [untrusted klal_id, ...]) from the
    header-anchored alignment, trusted entries only, klal_id order preserved
    within each page (which matches print order).

    Per CLAUDE.md Lesson 15, an untrusted alignment entry is not a
    low-confidence candidate - it is silence: no candidate is generated for
    that klal at all. The untrusted list is returned rather than discarded so
    a caller can report that silence instead of it being invisible.
    """
    alignment = load_json(path, [])
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
