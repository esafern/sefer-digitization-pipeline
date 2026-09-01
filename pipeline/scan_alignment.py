# [PRODUCTION] Scan geometry: where a corpus word sits on the printed page.
#
# EXTRACTED from pipeline/review_server.py 2026-09-01, closing finding C4 (filed
# 2026-08-25, restated by the 2026-08-27 review and by PROJECT-STATUS item 37(a))
# and taking the first real bite out of S1, the 1,981-line God Object.
#
# C4's complaint was precise: pipeline/synthesize_multi_witness.py - a BATCH
# stage in rebuild_all.sh - did `import review_server as rs` at module scope and
# then called `rs._word_bboxes_resolved()`, `rs._load_regions()`. A rebuild
# stage depended on the live HTTP server module, through its PRIVATE names, so
# any refactor inside the server could break the corpus build with no warning.
# Item 37(a) found the dependency was four times wider than the finding said:
# four non-test modules import review_server, at five private-helper call sites.
#
# This module is the answer for the three of those five that are geometry. The
# other two are not: tools/validate_suppression_filters.py wants
# _load_witness_queue() and tools/patch_witness_word_indices.py wants
# _load_klalim() - a queue reader and a corpus reader, neither of which belongs
# here. They are still open C4 instances and are recorded as such; do not read
# this extraction as having closed C4 entirely.
#
# Why these functions and not others: everything here is PURE COMPUTATION over
# files on disk. No HTTP, no request state, no decision-ledger reads. They were
# also the most algorithmically dense code in the server - the multi-page
# recurring-word resolution alone is ~60 lines of careful proportional-position
# arithmetic that had already been hand-written TWICE in the same file, which is
# how finding C3's last-page-wins bug happened. One implementation, one place to
# fix, one place to test.
#
# Names are PUBLIC here, deliberately. The importers above were reaching for
# underscore-prefixed names, which is the part that made the coupling fragile
# rather than merely present. review_server.py keeps its private aliases so its
# own ~40 internal call sites and the existing tests read unchanged.
import difflib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import corpus_io as cio  # noqa: E402


_regions_cache = {}  # (mtime_ns, size) -> parsed klal_page_regions.json

def load_regions():
    """klal_page_regions.json, re-parsed whenever the file on disk changes.

    MEMOIZED 2026-08-26 (code review, 2026-08-26 H13). This 187 KB file is
    re-read many times inside a single request - `klal_all_pages()` takes an
    optional `regions` argument precisely so callers can avoid that, and
    `word_scan_position()` never passes it. Profiled after the review_decisions
    memo landed: 6 parses per GET /api/page/73, 4.6 ms of a 14.8 ms request.
    Caching the loader fixes every caller at once rather than threading the
    parameter through two of them.

    Keyed on (st_mtime_ns, st_size), so a `rebuild_all.sh` run that regenerates
    the file invalidates it - the "fresh off disk every call" contract at the top
    of this section is about not going stale across a rebuild, and this does not.
    Verified before landing: replaying api_page/api_klal/api_klalim over a shared
    regions dict mutated none of its 623 entries. This is deliberately NOT
    applied to _load_corrections(), whose entries api_page() and api_klal() DO
    mutate in place (`entry["klal_id"] = kid`, `entry["current_decision"] = ...`);
    caching that would leak one request's overlays into the next.
    """
    path = cio.repo_path("klal_page_regions.json")
    try:
        st = os.stat(path)
        stamp = (st.st_mtime_ns, st.st_size)
    except OSError:
        return cio.load_repo_json("klal_page_regions.json", {})
    if _regions_cache.get("stamp") != stamp:
        _regions_cache["stamp"] = stamp
        _regions_cache["data"] = cio.load_repo_json("klal_page_regions.json", {})
    return _regions_cache["data"]

def resolve_klal_page(alignment, regions, klal_id):
    """(page, trusted) for a klal's scan-start page - the source of the
    top-level "page"/"page_trusted" fields api_klalim()/api_klal() serve.

    FIXED 2026-08-21 (data-integrity finding, see PROJECT-STATUS.md "Parts
    2-3's matched_page looks systematically wrong"): this used to be
    `_trusted_page()`, sourcing the page from the header-anchored alignment
    file's `matched_page` alone (trusted only when that file's own `trusted`
    flag said so). That flag turned out to be unreliable for Parts 2-3 -
    391 of 445 klalim disagree with klal_page_regions.json's own,
    independently-computed page (gematria-trace marker position + Y-band
    against real DocAI tokens) by up to 177 pages, despite the alignment
    file marking every single one of them "trusted": true. Directly
    verified against real DocAI token content (not just comparing two
    numbers): klal 663's alignment claims page 336, and page 336's tokens DO
    open with klal 663's exact text - so the text match itself is real, but
    page 234 has the SAME opening text preceded by a running-header
    fragment ("יך מלאכי") marking it as the genuine body page, while 336 is
    apparently some other, non-body occurrence (a back-of-book index is
    suspected, not yet confirmed) - the header matcher found *a* match, not
    the *right* one. Part 1's two sources agree in all 222 cases, so this is
    specific to whatever built Parts 2-3's alignment files (no generator
    script for them exists in this repo to fix directly - see
    PROJECT-STATUS.md), not a flaw in the header-anchored method in general.

    klal_page_regions.json now covers all 667 klalim (was Part 1 only, also
    fixed today) and its own page has been directly verified reliable, so
    prefer it; fall back to the alignment file's matched_page only for a
    klal with no region at all (region-building covers every klal in the
    corpus today, so this fallback is not currently expected to fire, but is
    kept for robustness rather than assuming that stays true forever)."""
    region = regions.get(str(klal_id))
    if region and region.get("page") is not None:
        return region["page"], True
    r = alignment.get(klal_id, {})
    return (r.get("matched_page"), True) if r.get("trusted") else (None, False)

def klal_all_pages(klal_id, regions=None):
    """All pages a klal appears on (start + continuations), in print order."""
    if regions is None:
        regions = load_regions()
    region = regions.get(str(klal_id), {})
    pages = []
    start = region.get("page")
    if start is not None:
        pages.append(start)
    for cont in region.get("continuations", []):
        pages.append(cont["page"])
    return pages

def klals_on_page(page_num, alignment, regions=None):
    """All klal_ids whose scan content (start or continuation) is on page_num.

    Combines the alignment's start-page mapping with klal_page_regions.json's
    continuation data so api_page() can serve corrections for klals that
    continue onto this page, not just klals that start here."""
    if regions is None:
        regions = load_regions()
    klals = set()
    for kid, r in alignment.items():
        if r.get("trusted") and r.get("matched_page") == page_num:
            klals.add(kid)
    for kid_str, region in regions.items():
        kid = int(kid_str)
        for cont in region.get("continuations", []):
            if cont["page"] == page_num:
                klals.add(kid)
    return klals

bbox_cache = {}  # (corpus_stamp, klal_id, page) -> {word_index -> bbox_dict}

def corpus_stamp():
    """A cheap fingerprint of the corpus files, for cache keys.

    ADDED 2026-08-27 (audit finding, verified). bbox_cache was keyed on
    (klal_id, page) alone and never invalidated, but the alignment it stores is
    computed FROM the klal's words - so applying a decision and rebuilding while
    the server ran left every later request reading boxes derived from text that
    no longer exists. That contradicts this section's own "fresh off disk every
    call" contract, and the reviewer does exactly that sequence routinely.
    """
    out = []
    for name in ("part1.json", "part2.json", "part3.json"):
        try:
            st = os.stat(cio.repo_path(name))
            out.append((st.st_mtime_ns, st.st_size))
        except OSError:
            out.append(None)
    return tuple(out)

def docai_page_stamp(page):
    """(mtime_ns, size) of one docai_word_boxes/page_N.json, or None.

    ADDED 2026-08-31, closing the half of finding S3 that the 2026-08-27 fix
    left open and that PROJECT-STATUS item 37 recorded as still open: the
    cached alignment is computed from TWO inputs - the klal's corpus words and
    that page's DocAI tokens - but the key only stamped the corpus. So
    re-extracting a page (which this project does; `docai_word_boxes/` is a
    build product, and the transposed-leaf fix rewrote pages wholesale) left
    every later request in a long-lived server serving boxes aligned against
    tokens that no longer exist, with no error and no way for the reviewer to
    tell. The original S3 finding named `docai_word_boxes/*.json` explicitly;
    only the part*.json half got stamped.

    Stat'ing one small file per cache miss is the whole cost, and it is paid
    only on a miss - a hit still returns without touching the filesystem.
    """
    try:
        st = os.stat(cio.docai_page_path(page, cio.DOCAI_DIR))
        return (st.st_mtime_ns, st.st_size)
    except OSError:
        return None

def corpus_bbox_cache_key(klal_id, page, exact_only=False):
    """The cache key, exposed so tests that pre-seed bbox_cache with
    synthetic alignments build it the same way this module does.

    `exact_only` is part of the key because the two modes answer differently:
    the exact-only pass is what decides WHICH page a recurring word lives on,
    and it must not be served a cached map that includes paired matches."""
    return (corpus_stamp(), docai_page_stamp(page), klal_id, page, exact_only)

def corpus_word_bboxes(klal_id, words, page, exact_only=False):
    """Map corpus word_index -> scan bbox for words on a given page.

    Uses the same SequenceMatcher alignment as
    tools/patch_witness_word_indices.py (corpus-to-DocAI token matching)
    but in the reverse direction: given a corpus word_index, find the
    DocAI token it aligns to and return that token's bounding box.
    Cached per (klal_id, page) since the alignment is deterministic."""
    key = corpus_bbox_cache_key(klal_id, page, exact_only)
    if key in bbox_cache:
        return bbox_cache[key]

    norm = cio.hebrew_letters_only
    toks = cio.load_docai_page(page, cio.DOCAI_DIR)
    if not toks:
        bbox_cache[key] = {}
        return {}

    # Page furniture is NOT matchable. FIXED 2026-08-26 (reviewer: "clicking on
    # klal 7 word 497 highlights the wrong word"). The running header, folio and
    # watermark are stripped from clean_text by construction, but they were still
    # in the token list this aligns against - so SequenceMatcher was free to
    # capture a corpus word with a header token. Klal 7's `י"ר` matched page 18's
    # header `יר` at relative-y 0.000 instead of its real occurrence at the foot
    # of page 17 (rel-y 0.870), and clicking it rang the running header on the
    # wrong page. Swept before fixing: 8 Part-1 words across 8 klalim were
    # aligned to a header token (klalim 5, 7, 25, 30, 54, 59, 144, 154 - the
    # captured words are `כללי`, `י"ר`, `האלף`, `יד`, `י"ד`, exactly the header's
    # own vocabulary). The band test in header_furniture_indices() is what makes
    # this safe: `כללי` is ordinary vocabulary here, and only the copy at the very
    # top of the page is furniture.
    furniture = cio.header_furniture_indices(toks)
    # A word with no Hebrew letters normalizes to "" and is dropped from both
    # sides, so it can never be aligned - which orphans exactly the words whose
    # flags most need a click: the stray `&` (an ﭏ ligature DocAI mangled), `Π`
    # (a printed folio), `!`, `.`. Ten open flags sit on such words.
    #
    # TRIED AND REVERTED 2026-08-30: falling back to the raw text as the match key
    # so a `&` could match a `&`. It works, and it costs too much - putting
    # punctuation tokens back into the sequence changed how SequenceMatcher aligns
    # the REAL words around them: 41 boxes moved and 2 were lost, including runs
    # of ordinary words shifting to a different box on the same page (klal 47
    # w1-w4, klal 67 w1-w7). Trading 41 correct boxes for 10 is not a trade.
    # Left unlocatable deliberately; see PROJECT-STATUS 0D(a).
    dtoks = [t for i, t in enumerate(toks) if norm(t["text"]) and i not in furniture]
    dwords = [norm(t["text"]) for t in dtoks]
    corpus_norm = [norm(w) for w in words]

    sm = difflib.SequenceMatcher(None, corpus_norm, dwords, autojunk=False)
    result = {}

    def _place(corpus_index, tok):
        if tok.get("x1") is not None:
            result[corpus_index] = {"x1": tok["x1"], "y1": tok["y1"],
                                    "x2": tok["x2"], "y2": tok["y2"]}

    # 'equal' runs are the words the corpus and the OCR agree on, and they used
    # to be the ONLY words that got a box - the function read get_matching_blocks()
    # and nothing else. So a word the corpus and DocAI DISAGREE about had no scan
    # position, could not be highlighted, and a click on it did nothing.
    #
    # Which is precisely backwards. A word is flagged BECAUSE the two disagree,
    # and it stops being locatable the moment somebody repairs it - the corrected
    # form no longer equals the token still holding the OCR error. Measured
    # 2026-08-30 (reviewer: "clicking on 69 w338 does not snap the reading pane to
    # the word"): 63 of 306 open flags, 21%, unlocatable - 16 of them created by
    # that day's own corrections, and klal 69's misses were every alef-lamed word
    # in the klal, DocAI holding `אהים` where the corpus has `אלהים`, the ﭏ
    # ligature read as a bare alef. Repairing the text was blinding the reviewer
    # to it.
    #
    # An EQUAL-LENGTH 'replace' run is exactly that case: n corpus words against n
    # tokens, between two anchors the alignment already agrees on, so corpus word
    # k is token k. That is what a letter-substitution repair, a dropped-lamed
    # ligature and a stray `&` all look like here. Unequal runs are NOT paired -
    # there the correspondence genuinely is unknown, and a box on a guessed token
    # would point the reviewer at the wrong ink, which is worse than no box.
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for offset in range(i2 - i1):
                _place(i1 + offset, dtoks[j1 + offset])
        elif tag == "replace" and not exact_only and (i2 - i1) == (j2 - j1):
            for offset in range(i2 - i1):
                _place(i1 + offset, dtoks[j1 + offset])
    bbox_cache[key] = result
    return result

def word_pages_map(klal_id, words, region_entry):
    """word_index -> page for every word aligned to a DocAI token on any
    page this klal touches, real DocAI alignment (via corpus_word_bboxes),
    not an approximation.

    FIXED 2026-08-21 (code review, on the day-of fix for the word_pages
    field itself): corpus_word_bboxes() runs a fresh SequenceMatcher
    against the klal's FULL word list for every page independently, so a
    word whose text recurs (a common/formulaic term) can align on more than
    one of the klal's pages. A first draft of this function collected pages
    in print order and overwrote word_pages[wi] = page unconditionally -
    last-page-wins - so a word that genuinely lives on an earlier page but
    also spuriously matches on a later page always resolved to the later
    page. This is the identical collision class already found and fixed in
    tools/verify_flagged_candidates_vision.py's locate_word() (see its own
    FIXED comment, round-3 audit 2026-08-16: klal 30 w1263/w250 'גכי' and
    klal 41 w256/w473 'כתכו' both matched on two pages). Same fix here:
    when a word_index matches on more than one page, keep whichever page's
    own token-count window actually contains that word_index's proportional
    position among the klal's total words, not whichever was processed
    last."""
    page_regions = []
    start_page = region_entry.get("page")
    if start_page is not None:
        page_regions.append((start_page, region_entry.get("token_count", 0)))
    for cont in region_entry.get("continuations", []):
        page_regions.append((cont["page"], cont.get("token_count", 0)))

    matches_by_word = {}
    for page, _ in page_regions:
        # exact_only: a paired 'replace' match is positional inference, strong
        # enough to place a box on a page already chosen but NOT to choose the
        # page. Without this, klal 114's w57-w64 were paired against the page-46
        # continuation that holds 5 of the klal's 87 tokens and moved off page 45,
        # where they belong - eight words that had a correct box before.
        for wi in corpus_word_bboxes(klal_id, words, page, exact_only=True):
            matches_by_word.setdefault(wi, []).append(page)

    total_words = len(words)
    total_tokens = sum(tc for _, tc in page_regions)
    word_pages = {}
    for wi, pages in matches_by_word.items():
        if len(pages) == 1:
            word_pages[wi] = pages[0]
            continue
        target = (wi / total_words) * total_tokens if total_words and total_tokens else 0
        running = 0
        best_page, best_dist = pages[0], float("inf")
        for page, tc in page_regions:
            if page in pages:
                dist = abs((running + tc / 2) - target)
                if dist < best_dist:
                    best_dist = dist
                    best_page = page
            running += tc
        word_pages[wi] = best_page
    return word_pages

def word_bboxes_resolved(klal_id, words, regions=None):
    """{word_index: (bbox, page)} for every word aligned to a DocAI token,
    with multi-page collisions resolved the ONE way.

    ADDED 2026-08-26 (code review, 2026-08-25 C3). corpus_word_bboxes() runs a
    fresh SequenceMatcher per page against the klal's full word list, so a word
    whose text recurs can align on more than one of the klal's pages - 943 words
    across the 175 multi-page klalim do. Three functions in this file resolved
    that collision three different ways: word_pages_map() proportionally (the
    one that was actually thought about, and the one with the FIXED comment
    explaining why), _word_level_ai_flags() last-page-wins, and
    word_scan_position() first-page-wins. They disagree on 657 and 293 of those
    943 words respectively.

    Nothing a reviewer sees is wrong today - measured before landing this: of the
    331 open word-level flags, exactly ONE sits on a colliding index and
    last-wins happens to agree there; zero of the 203 manual corrections sit on
    one at all. That is luck about where the flags fell, not a property of the
    code, which is the reason to collapse the three into one now rather than
    after it costs something.
    """
    if regions is None:
        regions = load_regions()
    region_entry = regions.get(str(klal_id), {})
    pages = klal_all_pages(klal_id, regions)
    word_pages = word_pages_map(klal_id, words, region_entry)
    out = {}
    for page in pages:
        for wi, bbox in corpus_word_bboxes(klal_id, words, page).items():
            # word_pages is the authority on WHICH page a recurring word is on;
            # fall back to this page only for a word it has no opinion about.
            if word_pages.get(wi, page) == page:
                out[wi] = (bbox, page)
    return out

def word_scan_position(klal_id, words, word_index, regions=None):
    """(bbox, page) for one corpus word, from the DocAI alignment.

    Extracted 2026-08-25 from _word_level_ai_flags(), which had been doing this
    for ai_flag entries only. A klal can span pages, so every page it touches is
    searched; returns (None, None) when the word has no aligned token (an OCR
    gap), which callers must handle rather than assume a box exists.

    Multi-page collisions now go through word_bboxes_resolved() - this used to
    take the FIRST page that matched, which is a third answer to a question two
    other functions here already answered differently. `regions` is threaded so
    callers that already hold it do not re-read the 187 KB regions file.
    """
    return word_bboxes_resolved(klal_id, words, regions).get(word_index, (None, None))
