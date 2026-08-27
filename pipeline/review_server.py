#!/usr/bin/env python3
# [PRODUCTION] Local review-dashboard server for Part 1: JSON API + static
# frontend (review_frontend/). Replaces the old single-file, all-data-
# inlined review.html (see PROJECT-STATUS.md "Review dashboard
# rearchitecture") - that file embedded all 222 klalim's text and all 762
# correction candidates into one <script> tag and built every klal's DOM +
# listeners synchronously on load, which is the likely cause of both its
# sluggish feel and of the Chrome extension never successfully loading it
# all session.
#
# This server reads corrections_part1.json / klalim_demo_dataset.json /
# part1_header_anchored_alignment.json / klal_page_regions.json fresh off
# disk on every request and merges in review_decisions.jsonl's current
# human-decision state at serve time - it never needs restarting after
# ./rebuild_all.sh regenerates those files, and a pipeline rebuild can
# never clobber a human decision (that file lives entirely outside the
# corpus-build pipeline).
#
# Every write endpoint only INSERTs (via review_decisions.append_decision) -
# there is no update/delete anywhere in this API surface. Nothing here ever
# writes to part1.json; promoting an accepted decision into the corpus text
# is a separate, manually-run step (apply_reviewer_decisions.py).
#
# Run: python3 review_server.py [--port 8420]
# Then open http://127.0.0.1:8420/ in a browser.
import argparse
import difflib
import json
import os
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

import corpus_io as cio
import review_decisions as rd

# Moved one level deeper (pipeline/ or tools/) 2026-08-16 - REPO now goes up
# two levels, not one, to keep resolving to the actual repo root where
# part1.json/docai_word_boxes/etc. live.
REPO = cio.REPO
FRONTEND_DIR = os.path.join(REPO, "review_frontend")
IMAGES_DIR = os.path.join(REPO, "images", "pdf_pages")
# max(klal_id) in part1.json - this dashboard is Part-1 only, and _load_klalim
# filters klalim_demo_dataset.json (all 667) down with it. Still deliberately
# NOT derived at request time (that would mean reading part1.json on every
# single HTTP request on top of the demo dataset this server already re-reads
# per request, by design). Until 2026-08-17 this was the same literal written
# out independently here, in build_corrections_dataset.py and in
# build_klal_page_regions.py, with the drift risk of three copies pushed onto
# tests/test_corpus_invariants.py::test_part1_max_klal_constants_agree_with_
# the_corpus. There is now one definition, and that test still asserts it
# equals max(klal_id) in the live part1.json.
PART1_MAX_KLAL = cio.PART1_MAX_KLAL

# Flags that mean "the machine settled this; no reading is in dispute". Kept as
# a set rather than an equality test because a SECOND such flag was added
# 2026-08-24 (docai_ligature_artifact) and the equality tests scattered through
# the count/label code were not updated - the same word then rendered green in
# the text pane, "Machine-Disputed" in the nav and legend, and
# "Machine-Disputed" in the panel header. Three verdicts on one screen.
MACHINE_RESOLVED_FLAGS = ("current_text_confirmed", "docai_ligature_artifact")

FLAG_LABELS = {
    "current_text_may_be_wrong": ["Disputed", "#e53e3e"],
    "possible_omission": ["Possibly missing", "#805ad5"],
    "current_text_confirmed": ["Machine-Resolved", "#38a169"],
    "unverified_insertion": ["Unverified addition", "#a0aec0"],
    "ambiguous": ["Ambiguous", "#dd6b20"],
    "error": ["Check failed", "#718096"],
    # ADDED 2026-08-25. Word-level klal_flags are served with flag "ai_flag" and
    # had no entry here, so app.js's `FLAGS[corr.flag] || ['Flagged']` fallback
    # rendered all 299 of them with the same generic word as a flag name that
    # doesn't exist - the exact defect the stale_candidate note below records,
    # live on the corpus rather than latent. tests/test_review_server.py's
    # end-to-end label check could not see it: it runs against an isolated,
    # empty decisions file, where no word-level flag exists to serve (Lesson 1 -
    # the check ran, just not on the case that mattered). It surfaced only when
    # a new test seeded a real flag record through the API.
    "ai_flag": ["Flagged for revisit", "#d69e2e"],
    # ADDED 2026-08-14: assemble_corrections_dataset.py's drift check
    # (see PROJECT-STATUS.md) forces this flag when a candidate's
    # word_index/corrected_word no longer matches live part1.json. Without
    # an entry here, review_frontend/app.js's `FLAGS[corr.flag] || ['Flagged']`
    # fallback rendered it as the same generic "Flagged" label as any
    # unrecognized flag - indistinguishable from a real bug in the flag
    # name itself, silent exactly when a reviewer most needs to know NOT
    # to trust this candidate's position. 0 candidates are currently
    # drifted, so this had never rendered - caught in code review before
    # it ever did.
    "stale_candidate": ["Stale - re-verify against scan", "#e53e3e"],
    # ADDED 2026-08-14 (found by tests/test_pipeline_logic.py's
    # exercise-classify()-over-its-whole-input-grid label check, the same
    # gap as "stale_candidate" above one step earlier): classify() ends in
    # a `return "unverified"` fallback for any opcode that isn't
    # replace/insert/delete. Unreachable today - build_corrections_dataset.py
    # only ever emits difflib's three opcodes - but the fallback exists
    # precisely for the unexpected case, which is exactly when rendering it
    # as an anonymous "Flagged" would be worst.
    "unverified": ["Unclassified (unexpected opcode)", "#718096"],
    # ADDED: witness flag for independent-witness (DocAI vs Tesseract) disagreements
    # on reconstructed continuation pages (reconstruction_witness_queue.json).
    "witness": ["Witness disagreement", "#805ad5"],
    # ADDED 2026-08-24: DocAI's reading differs from the corpus ONLY by the
    # alef-lamed ligature's dropped lamed - restoring it makes the two
    # identical, so there is no reading to choose between. Machine-resolved,
    # not open; green, and visibly named so a reviewer can tell it apart from a
    # vision-adjudicated confirmation.
    "docai_ligature_artifact": ["Ligature artifact (resolved)", "#38a169"],
}

MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".png": "image/png",
    ".json": "application/json; charset=utf-8",
}


# ---------- data loading (fresh off disk every call, deliberately no cache) ----------

# Repo-root-relative JSON read; body moved to corpus_io 2026-08-17, where the
# same exists-check-then-load was written out nine times across pipeline/ and
# tools/ (see that module's docstring).
_load_json = cio.load_repo_json


def _get_part_num_for_klal(klal_id):
    if klal_id <= PART1_MAX_KLAL:
        return 1
    elif klal_id <= 444:
        return 2
    else:
        return 3


def _load_klalim(part_num=1):
    demo = _load_json("klalim_demo_dataset.json", [])
    part_str = str(part_num).lower()
    if part_str in ("all", "0"):
        klalim = demo
    elif part_str == "2":
        klalim = [k for k in demo if 223 <= k["klal_id"] <= 444]
    elif part_str == "3":
        klalim = [k for k in demo if k["klal_id"] >= 445]
    else:
        klalim = [k for k in demo if k["klal_id"] <= PART1_MAX_KLAL]
    klalim.sort(key=lambda k: k["klal_id"])
    return {k["klal_id"]: k for k in klalim}, klalim


def _parts_for(part_num):
    # Same string-normalization convention as _load_klalim above (part_num
    # arrives as either an int, from a Python call site that already knows
    # the part, or a raw query-string value like "2"/"3"/"all"). FIXED
    # 2026-08-20 (code review): _load_alignment/_load_corrections used to
    # accept part_num and silently ignore it, always merging all three
    # parts - correct but wasteful (3x the JSON parses this request
    # actually needs). _load_punctuation_candidates separately compared
    # this same value with `== 1` (an int), which is never true for the
    # string values "2"/"3"/"all" the query path passes, and built a
    # nonexistent "punctuation_candidates_partall.json" filename - Parts
    # 2/3/All silently showed punctuation_count=0 for every klal.
    part_str = str(part_num).lower() if part_num is not None else "all"
    if part_str in ("all", "0", "none"):
        return (1, 2, 3)
    if part_str in ("2", "3"):
        return (int(part_str),)
    return (1,)


def _load_alignment(part_num=None):
    fnames = {1: "part1_header_anchored_alignment.json",
              2: "part2_header_anchored_alignment.json",
              3: "part3_header_anchored_alignment.json"}
    align = []
    for p in _parts_for(part_num):
        align += _load_json(fnames[p], [])
    return {r["klal_id"]: r for r in align}


def _load_corrections(part_num=None):
    fnames = {1: "corrections_part1.json", 2: "corrections_part2.json", 3: "corrections_part3.json"}
    combined = {}
    for p in _parts_for(part_num):
        c = _load_json(fnames[p], {})
        if isinstance(c, dict):
            combined.update(c)
    return combined


_regions_cache = {}  # (mtime_ns, size) -> parsed klal_page_regions.json


def _load_regions():
    """klal_page_regions.json, re-parsed whenever the file on disk changes.

    MEMOIZED 2026-08-26 (code review, 2026-08-26 H13). This 187 KB file is
    re-read many times inside a single request - `_klal_all_pages()` takes an
    optional `regions` argument precisely so callers can avoid that, and
    `_word_scan_position()` never passes it. Profiled after the review_decisions
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
        return _load_json("klal_page_regions.json", {})
    if _regions_cache.get("stamp") != stamp:
        _regions_cache["stamp"] = stamp
        _regions_cache["data"] = _load_json("klal_page_regions.json", {})
    return _regions_cache["data"]


def _load_punctuation_candidates(part_num=1):
    # Only Part 1 has punctuation candidates generated as of 2026-08-20 -
    # parts 2/3 correctly return {} (no file) rather than erroring, so this
    # stays forward-compatible if punctuation_candidates_part{2,3}.json are
    # ever built.
    fnames = {1: "punctuation_candidates_part1.json",
              2: "punctuation_candidates_part2.json",
              3: "punctuation_candidates_part3.json"}
    combined = {}
    for p in _parts_for(part_num):
        c = _load_json(fnames[p], {})
        if isinstance(c, dict):
            combined.update(c)
    return combined


# The vision verdicts that keep a witness item in the reviewer's queue. "A"
# means the vision pass sided with DocAI against Tesseract, which on this
# corpus is the overwhelmingly common and overwhelmingly correct outcome
# (DocAI 91.2% vs Tesseract 3.8% across the 419 items).
WITNESS_PRIORITY_VERDICTS = ("B", "NEITHER")
WITNESS_QUEUE_FILTERED = True


def _load_witness_queue():
    """Independent-witness (Tesseract vs DocAI) disagreements for the
    reconstructed continuation pages - see verify_reconstruction_witness.py.

    These are anchored on the SCAN (page + bbox), not on a corpus word index,
    which is deliberate: it means they can be reviewed by reading the ink even
    though the reconstructed text is NOT in part1.json yet. Reviewing and
    committing text to the corpus stay separate steps, the same way recording a
    candidate decision is separate from apply_reviewer_decisions.py.

    Every read/write site below (api_klal's decided-count, api_witness_summary,
    api_witness_context, api_post_witness_decision's snapshot lookup) matches
    items by (klal_id, docai_token_index) alone - NOT page, even though
    docai_token_index is page-relative (an index into that page's own filtered
    token list, per verify_reconstruction_witness.py). That is only safe
    because PAGE_TO_KLAL there currently maps each of its 3 pages to a
    DIFFERENT klal_id (24->30, 37->75, 40->88) - investigated 2026-08-16 as
    the standing "risk 2" open item. If a klal_id ever needed a second
    witness-processed page (e.g. klal 30 spanning two reconstructed pages),
    that page's items would silently collide with the first page's under the
    same (klal_id, token_index) key - `next(...)` lookups would return
    whichever item happens to come first, and a decision recorded against one
    page's word could get attributed to a different page's word entirely, with
    no error. Asserting it here, not fixing the matching logic itself: no
    current data triggers it (checked below), and a real fix (adding page to
    every match site + the decision key + the frontend's request payload) is a
    bigger, currently-unmotivated change - this turns a hypothetical future
    silent misattribution into an immediate loud failure instead."""
    q = _load_json("reconstruction_witness_queue.json", {})
    items = q.get("queue", []) if isinstance(q, dict) else []
    seen = {}
    for w in items:
        key = (w["klal_id"], w["docai_token_index"])
        if key in seen and seen[key] != w.get("page"):
            raise RuntimeError(
                f"witness queue: (klal_id, docai_token_index) {key} appears on "
                f"both page {seen[key]} and page {w.get('page')} - the "
                f"page-less matching used throughout this file can no longer "
                f"tell these apart. See this function's docstring."
            )
        seen[key] = w.get("page")

    # ADDED 2026-08-23, implementing the triage decided (and left unbuilt) on
    # 2026-08-19: work this queue by VISION VERDICT, not in full.
    #
    # Tesseract was right in only 16 of 419 disagreements (3.8%) against
    # DocAI's 91.2% - it fails structurally, being a weaker engine on the SAME
    # scan rather than an independent signal. Cutting to the items where the
    # vision pass did NOT side with DocAI leaves 37 of 419 and loses zero of
    # the recorded findings.
    #
    # Filtering here rather than in the queue FILE is deliberate: the file is
    # the complete evidence trail and stays complete (it is also derived, so a
    # hand-edit would be the Lesson 13 defect this repo keeps re-finding). This
    # is a view; flip WITNESS_QUEUE_FILTERED to False to serve everything again.
    #
    # The union with already-decided items is not defensive padding - it is
    # load-bearing. Measured before shipping: 7 of the 10 recorded decisions
    # sit OUTSIDE the priority cut, so a naive filter would have erased every
    # one of them from the dashboard. This is the same trap that got tier-D
    # deletion rejected on 2026-08-19.
    #
    # CAVEAT, per Lesson 2: all 419 verdicts came back at >= 0.9 confidence, so
    # the 37 are a PRIORITY QUEUE, not proof the other 382 are clean.
    if not WITNESS_QUEUE_FILTERED:
        return items
    decided = {k for k in rd.all_current("witness_choice")}
    return [w for w in items
            if w.get("vision_selected") in WITNESS_PRIORITY_VERDICTS
            or (w["klal_id"], w["docai_token_index"]) in decided]


def _resolve_klal_page(alignment, regions, klal_id):
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


def _klal_all_pages(klal_id, regions=None):
    """All pages a klal appears on (start + continuations), in print order."""
    if regions is None:
        regions = _load_regions()
    region = regions.get(str(klal_id), {})
    pages = []
    start = region.get("page")
    if start is not None:
        pages.append(start)
    for cont in region.get("continuations", []):
        pages.append(cont["page"])
    return pages


def _klals_on_page(page_num, alignment, regions=None):
    """All klal_ids whose scan content (start or continuation) is on page_num.

    Combines the alignment's start-page mapping with klal_page_regions.json's
    continuation data so api_page() can serve corrections for klals that
    continue onto this page, not just klals that start here."""
    if regions is None:
        regions = _load_regions()
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


def _word_matches(words, word_index, expected_word):
    """Is `expected_word` still the word sitting at `word_index`?

    The shared drift check behind both manual_correction render paths
    (api_klal's synthetic entries and api_klalim's per-klal count). It was
    written out twice, and BOTH copies bounds-checked only the upper end -
    the same half-a-bounds-check gap already fixed in
    audit_applied_decisions.py's three checkers (2026-08-14, finding 9) and
    in apply_reviewer_decisions.py's five corpus mutators (2026-08-15,
    finding 8); the display path was simply never revisited. Python does not
    raise on a negative index: `words[-1]` is the klal's LAST word, so a
    decision recorded at word_index -1 whose original_word happened to equal
    that last word passed the check and rendered as a live "Human-Decided"
    correction attached to a word it never described, and counted toward
    that klal's decided/total badges.

    Not reachable from today's UI (app.js only ever sends a real index) and
    0 of the 136 recorded manual_correction decisions carry a negative
    index - defence-in-depth on the display path, matching what the
    write-side and corpus-mutating paths already do.
    """
    return 0 <= word_index < len(words) and words[word_index] == expected_word


# FIXED 2026-08-17 (user bug report: "I saw klal 1 was flagged for review...
# the questionable word was not highlighted, I needed to find it myself").
# klal_flag decisions were architecturally assumed to always be about the
# KLAL AS A WHOLE (word_index None - see review_decisions.py's history_for()
# docstring, which said as much) - true for the reviewer-facing flag panel,
# but several AI passes (detect_real_word_substitution.py and similar) name
# one specific disputed word in free-text prose inside the note and never
# set word_index, even though append_decision() has always accepted it. The
# result: a real candidate word sat undiscoverable except by reading prose
# and searching the text by eye - confirmed live on klal 1 w446 (real fix,
# same session: ומידו->ומיהו). Two distinct concerns, kept structurally
# separate so a word-level AI flag can never be mistaken for the klal's
# general note:
#   - _general_klal_flag_*(): word_index IS None - the reviewer-facing
#     "needs a second look" panel, unchanged behavior.
#   - the word-level synthesis loop in api_klal() below: word_index IS NOT
#     None - synthesized into `corrections` (the same shape manual_
#     correction entries already use to get highlighted) so these render
#     exactly like any other flagged word, GOING FORWARD for any script
#     that starts setting word_index (detect_real_word_substitution.py
#     fixed the same session, see its own diff) - this does NOT retroactively
#     help already-recorded flags that never set word_index; that's a
#     separate backfill decision, not made here.
def _general_klal_flag_history(klal_id):
    return [r for r in rd.history_for(klal_id, decision_type="klal_flag")
            if r.get("word_index") is None]


def _general_klal_flag_current(klal_id):
    h = _general_klal_flag_history(klal_id)
    return h[-1] if h else None


_corpus_bbox_cache = {}  # (klal_id, page) -> {word_index -> bbox_dict}


def _corpus_word_bboxes(klal_id, words, page):
    """Map corpus word_index -> scan bbox for words on a given page.

    Uses the same SequenceMatcher alignment as
    tools/patch_witness_word_indices.py (corpus-to-DocAI token matching)
    but in the reverse direction: given a corpus word_index, find the
    DocAI token it aligns to and return that token's bounding box.
    Cached per (klal_id, page) since the alignment is deterministic."""
    key = (klal_id, page)
    if key in _corpus_bbox_cache:
        return _corpus_bbox_cache[key]

    norm = cio.hebrew_letters_only
    toks = cio.load_docai_page(page, cio.DOCAI_DIR)
    if not toks:
        _corpus_bbox_cache[key] = {}
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
    dtoks = [t for i, t in enumerate(toks) if norm(t["text"]) and i not in furniture]
    dwords = [norm(t["text"]) for t in dtoks]
    corpus_norm = [norm(w) for w in words]

    sm = difflib.SequenceMatcher(None, corpus_norm, dwords, autojunk=False)
    result = {}
    for corpus_start, dtok_start, size in sm.get_matching_blocks():
        for offset in range(size):
            tok = dtoks[dtok_start + offset]
            if tok.get("x1") is not None:
                result[corpus_start + offset] = {
                    "x1": tok["x1"], "y1": tok["y1"],
                    "x2": tok["x2"], "y2": tok["y2"],
                }
    _corpus_bbox_cache[key] = result
    return result


def _word_pages_map(klal_id, words, region_entry):
    """word_index -> page for every word aligned to a DocAI token on any
    page this klal touches, real DocAI alignment (via _corpus_word_bboxes),
    not an approximation.

    FIXED 2026-08-21 (code review, on the day-of fix for the word_pages
    field itself): _corpus_word_bboxes() runs a fresh SequenceMatcher
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
        for wi in _corpus_word_bboxes(klal_id, words, page):
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


def _flag_answered_by_a_later_decision(klal_id, word_index, flag_rec,
                                       candidate_decisions=None,
                                       manual_decisions=None):
    """True when a human recorded a decision at this exact word AFTER the flag
    was raised.

    ADDED 2026-08-25, reviewer report on klal 163: "i cleared the flag but it
    still shows in the middle and right." They had cleared the KLAL-level flag,
    but three word-level flags stayed open on words they had already decided
    that same afternoon - so the klal stayed lit, the words stayed marked, and
    the panel still announced an open revisit flag. A flag says "come back and
    look at this word"; a decision recorded at that word afterwards IS the
    reviewer having looked. Requiring a second, separate click to say so is the
    friction, not the safeguard.

    ORDER IS THE WHOLE POINT: only a decision NEWER than the flag answers it. A
    flag raised after a decision is a fresh concern about an already-decided
    word (a later detector pass finding something the reviewer did not address)
    and must stay open.

    Swept 2026-08-25: 331 open word-level flags across 110 klalim, of which 23
    across 7 klalim are answered this way - klal 88 (12), klal 163 (3), klal 91
    (3), 29 (2), and one each in 2, 4, 8. The other 308 are genuinely
    unanswered and are untouched by this.

    Nothing is written to the ledger. The flag record stands exactly as
    recorded; this only decides whether it is still asking for something.
    """
    if candidate_decisions is None:
        candidate_decisions = rd.all_current("candidate_choice")
    if manual_decisions is None:
        manual_decisions = rd.all_current("manual_correction")
    flag_ts = flag_rec.get("ts") or ""
    for source in (candidate_decisions, manual_decisions):
        decision = source.get((klal_id, word_index))
        if decision and (decision.get("ts") or "") > flag_ts:
            return True
    return False


def _word_bboxes_resolved(klal_id, words, regions=None):
    """{word_index: (bbox, page)} for every word aligned to a DocAI token,
    with multi-page collisions resolved the ONE way.

    ADDED 2026-08-26 (code review, 2026-08-25 C3). _corpus_word_bboxes() runs a
    fresh SequenceMatcher per page against the klal's full word list, so a word
    whose text recurs can align on more than one of the klal's pages - 943 words
    across the 175 multi-page klalim do. Three functions in this file resolved
    that collision three different ways: _word_pages_map() proportionally (the
    one that was actually thought about, and the one with the FIXED comment
    explaining why), _word_level_ai_flags() last-page-wins, and
    _word_scan_position() first-page-wins. They disagree on 657 and 293 of those
    943 words respectively.

    Nothing a reviewer sees is wrong today - measured before landing this: of the
    331 open word-level flags, exactly ONE sits on a colliding index and
    last-wins happens to agree there; zero of the 203 manual corrections sit on
    one at all. That is luck about where the flags fell, not a property of the
    code, which is the reason to collapse the three into one now rather than
    after it costs something.
    """
    if regions is None:
        regions = _load_regions()
    region_entry = regions.get(str(klal_id), {})
    pages = _klal_all_pages(klal_id, regions)
    word_pages = _word_pages_map(klal_id, words, region_entry)
    out = {}
    for page in pages:
        for wi, bbox in _corpus_word_bboxes(klal_id, words, page).items():
            # word_pages is the authority on WHICH page a recurring word is on;
            # fall back to this page only for a word it has no opinion about.
            if word_pages.get(wi, page) == page:
                out[wi] = (bbox, page)
    return out


def _word_scan_position(klal_id, words, word_index, regions=None):
    """(bbox, page) for one corpus word, from the DocAI alignment.

    Extracted 2026-08-25 from _word_level_ai_flags(), which had been doing this
    for ai_flag entries only. A klal can span pages, so every page it touches is
    searched; returns (None, None) when the word has no aligned token (an OCR
    gap), which callers must handle rather than assume a box exists.

    Multi-page collisions now go through _word_bboxes_resolved() - this used to
    take the FIRST page that matched, which is a third answer to a question two
    other functions here already answered differently. `regions` is threaded so
    callers that already hold it do not re-read the 187 KB regions file.
    """
    return _word_bboxes_resolved(klal_id, words, regions).get(word_index, (None, None))


def _word_level_ai_flags(klal_id, words):
    """klal_flag decisions naming a specific word_index, synthesized into
    corrections-shaped entries so the frontend highlights them. Only the
    latest decision per word_index, and only if still open - a closed
    (needs_revisit: false) word-level flag has already been resolved (see
    e.g. today's klal 167 closures) and should stop being highlighted, the
    same way a satisfied manual_correction does."""
    by_word = {}
    for r in rd.history_for(klal_id, decision_type="klal_flag"):
        widx = r.get("word_index")
        if widx is not None:
            by_word[widx] = r  # later (later-appended) wins
    if not by_word:
        return []

    # Look up scan bboxes from DocAI tokens for ai_flag words. A klal may
    # span multiple pages (start + continuations); look up bboxes on each
    # page so continuation-page words get bboxes too.
    # Collisions resolved the one way - this loop used to be last-page-wins.
    # See _word_bboxes_resolved().
    bboxes = _word_bboxes_resolved(klal_id, words)  # word_index -> (bbox, page)

    candidate_decisions = rd.all_current("candidate_choice")
    manual_decisions = rd.all_current("manual_correction")
    out = []
    for word_index, rec in sorted(by_word.items()):
        if not rec.get("needs_revisit"):
            continue
        if not (0 <= word_index < len(words)):
            continue
        # ANSWERED flags are still SERVED, deliberately. Dropping them here was
        # the first shape of this fix and
        # tests/test_corpus_invariants.py::test_every_open_word_level_flag_has_a_
        # control_that_can_clear_it caught it: the record stays open in the
        # append-only log, so a flag nothing renders is a flag nobody can ever
        # clear - 24 of them, the exact defect that test exists for. Serve it,
        # mark it answered, and let the panel say so; the counts and the nav
        # pennant are what stop treating it as outstanding.
        answered = _flag_answered_by_a_later_decision(
            klal_id, word_index, rec, candidate_decisions, manual_decisions)
        bbox_page = bboxes.get(word_index)
        bbox = bbox_page[0] if bbox_page else None
        page = bbox_page[1] if bbox_page else None
        out.append({
            "word_index": word_index,
            "opcode": "ai_flag",
            "flag_answered": answered,
            "docai_reading": None,
            "final_text": None,
            "page": page,
            "bbox": bbox,
            "vision_selected": None,
            "vision_transcription": None,
            "confidence": None,
            "reasoning": rec.get("note"),
            "flag": "ai_flag",
            "current_decision": rec,
        })
    return out


def _claim_word_index(corrections, word_index, overlay_key=None, overlay=None):
    """Return the entry already serving `word_index`, after optionally
    overlaying extra data onto it - or None if the index is free.

    THE RULE THIS ENFORCES, and why it is a helper rather than three copies:
    review_frontend/app.js builds its word map as
    `corrections.forEach(c => byIndex[c.word_index] = c)` - LAST WRITE WINS. So
    two entries at one word_index means the reviewer silently sees only the
    second, losing whatever the first carried: its bbox (no scan highlight at
    all), its readings, its vision verdict and confidence.

    api_klal() builds `corrections` from FOUR sources - machine candidates,
    manual_correction decisions, word-level klal_flags, and witness
    disagreements - and every source after the first must therefore check
    whether the index is already taken. Found 2026-08-24 by live review of klal
    91 (manual over machine), then by sweeping every klal, which turned up four
    more `replace+witness` collisions and one `ai_flag+witness`. Each source had
    grown its own partial guard (the flag and witness paths both checked
    `manual_word_indices` but not machine candidates), which is exactly the
    shape that leaves one combination uncovered.
    """
    existing = next((c for c in corrections
                     if c.get("word_index") == word_index and c.get("opcode") != "delete"),
                    None)
    if existing is not None and overlay_key is not None:
        existing[overlay_key] = overlay
    return existing


def _merge_decision(entry, klal_id, decided):
    """Overlay the current human decision (if any) on top of a raw
    corrections_part1.json entry - never mutates the source data, this is
    a display-time merge only.

    `decided` is one all_current("candidate_choice") map, built once by the
    caller. This used to call rd.current_for() per entry, and every such
    call re-reads and re-parses the WHOLE review_decisions.jsonl - so a
    klal with 11 candidates cost 11 full parses of the append-only log on
    every single /api/klal request, growing with the log forever. Same
    semantics either way (current_for and all_current both resolve a key to
    the last matching line in file order), just resolved once."""
    entry = dict(entry)
    entry["current_decision"] = decided.get((klal_id, entry["word_index"]))
    return entry


# ---------- API payload builders ----------

def api_flags():
    return FLAG_LABELS


def api_klalim(part_num=1):
    klalim_by_id, klalim = _load_klalim(part_num=part_num)
    alignment = _load_alignment(part_num=part_num)
    regions = _load_regions()
    corrections = _load_corrections(part_num=part_num)
    punct_candidates = _load_punctuation_candidates(part_num=part_num)
    # Pre-load klal_flag decisions once for all 222 klalim. The old code
    # called _word_level_ai_flags() per klal inside the loop; that function
    # calls rd.history_for() which re-reads the full log each time - 222
    # extra reads per request. Loading all_current("klal_flag") here once
    # covers both the 'flagged' set and the per-klal ai_flag counts below.
    all_klal_flags = rd.all_current("klal_flag")  # {(klal_id, word_index): record}
    decided = rd.all_current("candidate_choice")  # {(klal_id, word_index): record}
    _manual_for_flags = rd.all_current("manual_correction")

    def _flag_still_open(kid, widx, rec):
        """A klal-level flag (word_index None) is open until someone clears it.
        A WORD-level flag is also answered by a human decision recorded at that
        word after it was raised - see _flag_answered_by_a_later_decision().
        Without this, clearing the klal-level flag could never turn the nav's
        pennant off while any word-level flag remained, which is what the
        reviewer hit on klal 163: cleared twice, still lit, no explanation."""
        if not rec.get("needs_revisit"):
            return False
        if widx is None:
            return True
        return not _flag_answered_by_a_later_decision(kid, widx, rec, decided,
                                                      _manual_for_flags)

    flagged = {kid for (kid, widx), r in all_klal_flags.items()
               if _flag_still_open(kid, widx, r)}
    punct_decided = rd.all_current("punctuation_choice")

    # Manual corrections (2026-08-13, "flag any word and replace it") are
    # born already-decided - there's no machine-detected "open" phase to
    # move out of, unlike candidate_choice/witness_choice. Each one adds
    # exactly 1 to BOTH total_count and decided_count below, contributing
    # 0 to machine_disputed/machine_resolved - matching exactly what the
    # frontend's own incremental counter patch does on save (see app.js
    # openManualCorrectionPanel), so client and server never disagree.
    # Drift check, added 2026-08-14 (same incident/reasoning as api_klal()'s
    # - see PROJECT-STATUS.md): only count a manual_correction decision if
    # its word still matches what it was decided against; otherwise a
    # stale decision from before a reindexing edit inflates this klal's
    # count for a word it no longer actually describes.
    # Same map as _manual_for_flags above, not a second query. FIXED 2026-08-26
    # (code review: 2026-08-25 C2, 2026-08-26 H11 - both runs found it) - it was
    # a copy-paste artifact from the two features landing in different commits,
    # and it re-derived an identical result 32 lines from where it already sat.
    manual_decided = _manual_for_flags  # {(klal_id, word_index): record}
    manual_count_by_klal = {}
    manual_indices_by_klal = {}
    for (kid, wi), rec in manual_decided.items():
        k = klalim_by_id.get(kid)
        if not k:
            continue
        words = (k.get("clean_text") or "").split(" ")
        original_word = rec.get("candidate_snapshot", {}).get("original_word")
        if not _word_matches(words, wi, original_word):
            continue
        manual_count_by_klal[kid] = manual_count_by_klal.get(kid, 0) + 1
        manual_indices_by_klal.setdefault(kid, set()).add(wi)

    # Witness items fold into the SAME tri-state counts as corrections
    # (2026-08-12, user request: "put the witness flags in as
    # machine-disputed same as the others") - an undecided witness item is
    # exactly as much an open dispute as an undecided correction is, it
    # just came from a different comparison (DocAI vs Tesseract instead of
    # DocAI vs stored text). There is no "machine-resolved" state for a
    # witness item - nothing auto-resolves it, so it is either open
    # (machine-disputed) or human-decided, never machine-resolved.
    witness_queue = _load_witness_queue()
    witness_by_klal = {}
    for w in witness_queue:
        witness_by_klal.setdefault(w["klal_id"], []).append(w)
    witness_decided = rd.all_current("witness_choice")

    out = []
    for k in klalim:
        kid = k["klal_id"]
        entries = corrections.get(str(kid), [])
        w_entries = witness_by_klal.get(kid, [])

        # Word-level ai_flag corrections (bug #1 fix, earlier today) were
        # highlighted in the text pane but never counted here - a klal could
        # show "0 open" in the nav while its text pane had a highlighted,
        # undecided AI flag (flagged 2026-08-17, code review). Every
        # synthesized ai_flag entry is by construction still open (see
        # _word_level_ai_flags' own needs_revisit filter) and machine-raised
        # (no human decision, no vision-resolved state), so it always adds
        # to total/open/machine_disputed together, the same as an
        # undecided correction - never to decided_count. Excludes any
        # word_index a valid manual_correction already covers, matching
        # api_klal()'s own dedup so the two endpoints never disagree.
        words = (k.get("clean_text") or "").split(" ")
        n_words = len(words)
        manual_indices = manual_indices_by_klal.get(kid, set())
        manual_indices_for_count = manual_indices
        # One comprehension, two consumers - these were two copies of the same
        # condition and the count could drift from the set it was meant to
        # describe. `_flag_still_open` keeps both in step with what
        # _word_level_ai_flags() actually renders.
        ai_flag_indices_for_count = {
            fwidx for (fkid, fwidx), rec in all_klal_flags.items()
            if fkid == kid and fwidx is not None
            and _flag_still_open(fkid, fwidx, rec)
            and fwidx not in manual_indices and 0 <= fwidx < n_words
        }
        ai_flag_count = len(ai_flag_indices_for_count)
        # An ANSWERED flag still renders - it has to, or nothing on screen can
        # clear it - and it renders as human-decided, since a decision at that
        # word is what answered it. It usually overlays a richer entry and adds
        # nothing here; it only stands alone when that entry is gone, which
        # happens routinely: synthesize_multi_witness.py drops a consensus
        # dispute once a human has decided the position, so the next rebuild
        # removes the host. Measured on the 2026-08-25 rebuild: 14 entries
        # removed, and 7 answered flags across klalim 2/4/88/163/167 were
        # left standing alone. Counted as DECIDED to match what renders.
        answered_flag_indices = {
            fwidx for (fkid, fwidx), rec in all_klal_flags.items()
            if fkid == kid and fwidx is not None and rec.get("needs_revisit")
            and not _flag_still_open(fkid, fwidx, rec)
            and fwidx not in manual_indices and 0 <= fwidx < n_words
        }

        # api_klal() MERGES colliding entries via _claim_word_index() -
        # manual-over-candidate, flag-over-candidate, witness-over-candidate - so
        # ONE entry per word_index survives to be rendered. These counts must
        # describe that surviving entry.
        #
        # FIXED 2026-08-24 (code review): the totals used to add every source
        # independently, counting items the text pane never renders - nav 1201 vs
        # 1061 rendered across 88 klalim.
        # FIXED 2026-08-25 (user report: "klal 88 shows -1 even though a few are
        # outstanding"): that fix made only the NUMERATOR distinct and left
        # decided_count and machine_disputed_count summing their sources, so a
        # word claimed by two of them - a witness decision at a position a
        # manual_correction already covers, klal 88 w327 - was counted once in
        # the total and twice in decided, and open_count went NEGATIVE. Swept the
        # corpus: 3 klalim (30, 88, 91) carried 6 such phantom decisions; only 88
        # had enough of them to cross zero. Two of klal 88's three came from
        # witness rows whose word_index is None: never rendered, still counted.
        #
        # Classify the surviving entry instead, in api_klal()'s own source order.
        # The tri-state then sums to the total BY CONSTRUCTION, not by
        # coincidence - which is the property
        # tests/test_corpus_invariants.py asserts.
        DECIDED, RESOLVED, DISPUTED = "decided", "machine_resolved", "machine_disputed"

        def _machine_state(entry):
            # A human decision always wins (wordState() in app.js), otherwise a
            # machine-resolved flag, otherwise nobody has looked at it yet.
            if (kid, entry["word_index"]) in decided:
                return DECIDED
            return RESOLVED if entry.get("flag") in MACHINE_RESOLVED_FLAGS else DISPUTED

        state = {}
        for e in entries:                                   # 1. machine candidates
            if e.get("opcode") == "delete":
                continue                                    # no word_index slot of its own
            state[e["word_index"]] = _machine_state(e)
        for wi in manual_indices_for_count:                 # 2. born decided
            state[wi] = DECIDED
        for wi in ai_flag_indices_for_count:                # 3. only when standalone;
            state.setdefault(wi, DISPUTED)                  #    otherwise it just overlays
        for wi in answered_flag_indices:                    # 3b. answered: renders green
            state.setdefault(wi, DECIDED)
        for w in w_entries:                                 # 4. witness disagreements
            wi = w.get("word_index")
            if wi is None or not (0 <= wi < n_words) or wi in manual_indices:
                continue                                    # not rendered - see api_klal()
            if wi in state:
                continue                                    # overlaid onto a richer entry
            # A witness item the vision pass called (A or B) renders GREEN in
            # the text pane - app.js's wordState() treats a vision verdict on a
            # witness exactly as it treats `current_text_confirmed` on a
            # candidate. This function used to call every undecided witness
            # DISPUTED, which put klalim 30 and 75 on screen with more green
            # words than the nav badge admitted (6 and 2). Same divergence class
            # as `docai_ligature_artifact` in 2026-08-24's finding F2: the screen
            # is the ground truth, so the count follows it.
            if (kid, w["docai_token_index"]) in witness_decided:
                state[wi] = DECIDED
            elif w.get("vision_selected") in ("A", "B"):
                state[wi] = RESOLVED
            else:
                state[wi] = DISPUTED

        all_states = list(state.values()) + [
            _machine_state(e) for e in entries if e.get("opcode") == "delete"
        ]
        total_count = len(all_states)
        decided_count = all_states.count(DECIDED)
        machine_resolved_count = all_states.count(RESOLVED)
        machine_disputed_count = all_states.count(DISPUTED)

        punct_entries = punct_candidates.get(str(kid), [])
        punct_decided_count = sum(
            1 for p in punct_entries if (kid, p["before_word_index"]) in punct_decided
        )
        _page, _page_trusted = _resolve_klal_page(alignment, regions, kid)
        out.append({
            "klal_id": kid,
            "title": k.get("title", ""),
            # The klal's own gematria marker, e.g. `סו` for 66. ADDED 2026-08-26
            # (reviewer: "add the gematria form of the klal to the context
            # header") - api_klal has always carried it, but the nav//api/klalim
            # payload did not, so anything working from klalById (the hover card,
            # the nav) had no way to name a klal the way the BOOK does.
            "gematria": k.get("gematria", ""),
            "section": k.get("section", ""),
            "page": _page,
            "page_trusted": _page_trusted,
            "correction_count": total_count,
            # split so the nav badge can distinguish "still needs a look"
            # from "already decided" instead of one undifferentiated count
            # (2026-08-07, PROJECT-STATUS.md "review dashboard feedback").
            "decided_count": decided_count,
            # Served but no longer rendered: the nav badge switched to
            # machine_disputed_count on 2026-08-25 (see app.js's own note). NOT
            # Lesson 29's dead field, and deliberately kept - it is the arithmetic
            # canary for this function's count logic, asserted by
            # test_corpus_invariants.py::test_nav_tristate_matches_what_each_word_actually_renders_as, which is
            # what caught the klal 88 "-1" fix-on-fix arc. If you remove it,
            # remove that test's subject too, not just the key.
            "open_count": total_count - decided_count,
            "machine_disputed_count": machine_disputed_count,
            "machine_resolved_count": machine_resolved_count,
            "ai_flag_count": ai_flag_count,
            "punctuation_count": len(punct_entries),
            "punctuation_decided_count": punct_decided_count,
            "punctuation_open_count": len(punct_entries) - punct_decided_count,
            "needs_revisit": kid in flagged,
            # lets the frontend size an unmounted placeholder block
            # proportionally instead of a fixed guess, so lazy-loading a
            # klal's real content doesn't cause a large layout jump.
            "text_length": len(k.get("clean_text", "")),
        })
    return out


def api_klal(klal_id):
    part_num = _get_part_num_for_klal(klal_id)
    klalim_by_id, _ = _load_klalim(part_num=part_num)
    k = klalim_by_id.get(klal_id)
    if not k:
        return None
    alignment = _load_alignment(part_num=part_num)
    corrections = _load_corrections(part_num=part_num).get(str(klal_id), [])
    decided = rd.all_current("candidate_choice")
    corrections = [_merge_decision(c, klal_id, decided) for c in corrections]
    # Manual corrections (2026-08-13) as SYNTHETIC entries in the same
    # `corrections` list the frontend already knows how to render - they
    # carry no corrections_part1.json entry of their own (there was never a
    # machine-detected candidate here), so build one shaped like a
    # 'replace' opcode with docai_reading=null and final_text=the word the
    # reviewer originally saw, and attach `current_decision` directly
    # (skipping _merge_decision, which looks up 'candidate_choice' - the
    # wrong decision_type for this). current_decision is always set, so
    # wordState() in app.js always renders it Human-Decided - correct,
    # since a manual correction IS the decision, there's no separate
    # machine-disputed phase for it to have come from.
    #
    # DRIFT CHECK, added 2026-08-14 (found live during the 2026-08-13
    # geresh-spacing reindex incident - see PROJECT-STATUS.md): unlike
    # candidate_choice/punctuation_choice above and below, which only ever
    # look up a decision for a word_index that ALREADY has a live
    # candidate/punctuation entry (so a stale decision at an abandoned
    # position simply never surfaces), this loop used to render EVERY
    # recorded manual_correction decision unconditionally. After any edit
    # that shifts word positions in this klal, an old decision's
    # word_index can land on a completely different, unrelated word - the
    # dashboard would show that word as "Human-Decided" with someone
    # else's chosen_text attached to it. Skip (don't render) a decision
    # whose original_word no longer matches what's actually at that
    # position now; only a still-valid decision renders.
    words = (k.get("clean_text") or "").split(" ")
    manual_word_indices = set()
    for (kid, word_index), rec in rd.all_current("manual_correction").items():
        if kid != klal_id:
            continue
        original_word = rec.get("candidate_snapshot", {}).get("original_word")
        if not _word_matches(words, word_index, original_word):
            continue
        manual_word_indices.add(word_index)
        # FIXED 2026-08-24 (found by live review of klal 91, and by
        # tests/test_corpus_invariants.py::test_no_rendered_manual_correction_
        # hides_a_machine_candidate firing for the first time). If a MACHINE
        # candidate already exists at this word_index, MERGE the human decision
        # onto it instead of appending a second entry.
        #
        # app.js builds its word map as last-write-wins and this loop appends
        # after the machine candidates, so a second entry at the same index
        # silently replaced the real dispute - taking its bbox (no scan
        # highlight at all), its docai_reading and consensus_reading (nothing
        # for the panel to compare), and its vision verdict and confidence with
        # it. The reviewer saw a word marked Human-Decided with no readings and
        # no box. That test's docstring predicted exactly this class would
        # resurrect the moment a still-valid manual decision landed on a live
        # candidate's position; klal 91 w453/w524 is that moment.
        # Keep whichever decision is NEWER. _merge_decision() has already set
        # current_decision from all_current("candidate_choice") (aliased to
        # disputed_choice); overwriting it unconditionally means an older
        # manual_correction silently masks a newer disputed_choice. Measured
        # 2026-08-24: 19 positions carry both, and in all 19 the manual record
        # is the older one (klal 91 w109: manual 2026-08-15, disputed_choice
        # 2026-08-24). Their chosen_text agrees today, so nothing is visibly
        # wrong yet - but the next re-decision from the disputed panel would be
        # recorded and then not displayed, with the panel still showing the
        # stale choice.
        _existing = _claim_word_index(corrections, word_index)
        if _existing is not None:
            _prior = _existing.get("current_decision")
            if not _prior or (rec.get("ts") or "") >= (_prior.get("ts") or ""):
                _existing["current_decision"] = rec
            continue
        # FIXED 2026-08-25 (reviewer, klal 4: "clicking on word 95 does not
        # highlight that word"). These synthetic entries shipped page=None and
        # bbox=None, so a manually-corrected word was the one kind of flagged
        # word with no scan geometry at all - api_page() drops any bbox-less
        # correction, and the click handler had no page to navigate to. The
        # geometry was always available: _word_level_ai_flags() has looked the
        # same words up from the DocAI alignment since ai_flags were added.
        _bbox, _page = _word_scan_position(klal_id, words, word_index)
        corrections.append({
            "word_index": word_index,
            "opcode": "manual",
            "docai_reading": None,
            "final_text": rec.get("candidate_snapshot", {}).get("original_word"),
            "page": _page,
            "bbox": _bbox,
            "vision_selected": None,
            "vision_transcription": None,
            "confidence": None,
            "reasoning": None,
            "flag": "manual_correction",
            "current_decision": rec,
        })
    # A manual correction means a human already acted on this exact word -
    # an AI flag on the same word_index is now redundant, don't also show it.
    #
    # FIXED 2026-08-24, same defect as the manual-correction merge above and
    # found while fixing it: a word-level flag at a position that ALREADY has a
    # machine candidate also appended a second entry and shadowed it under
    # app.js's last-write-wins map. It only escaped notice at klal 91 because a
    # manual correction happened to pre-empt the flag there. Merge instead:
    # attach the flag to the live candidate as `word_flag` so the reviewer sees
    # the dispute AND that it is flagged, and so the panel can offer to clear it.
    # ORDER MATTERS HERE, and getting it wrong is what left klal 91's four open
    # flags unclearable (reported 2026-08-24: "still shows a flag in the middle
    # pane but there's nothing to clear in the right pane").
    #
    # The `manual_word_indices` skip below predates the ability to clear a
    # word-level flag: when a flag could only ever be set, dropping a redundant
    # one at an already-decided word was right. Now that the disputed panel
    # offers "Clear revisit flag", dropping the flag ALSO drops the only control
    # that can close it - the flag stays open in the log, keeps the word
    # highlighted, and is unreachable. So the OVERLAY must happen first and
    # unconditionally; the skip only governs whether a STANDALONE entry is
    # appended.
    for f in _word_level_ai_flags(klal_id, words):
        # The overlay carries the flag record PLUS whether a later decision has
        # already answered it, so the panel can say "answered by your decision"
        # instead of "carries an open revisit flag" for a word the reviewer has
        # already ruled on (reviewer report on klal 163, 2026-08-25).
        _flag_overlay = dict(f.get("current_decision") or {})
        _flag_overlay["answered"] = bool(f.get("flag_answered"))
        if _claim_word_index(corrections, f["word_index"], "word_flag",
                             _flag_overlay) is not None:
            continue
        if f["word_index"] in manual_word_indices:
            continue  # defensive: a manual decision always yields an entry above
        # Same shape as the overlay above, not the raw record. FIXED 2026-08-26
        # (code review): this path handed the panel `current_decision` with no
        # `answered` key, so a standalone answered flag - the one case that
        # reaches this branch at all - was announced as "carries an open revisit
        # flag" for a word the reviewer had already ruled on. That is the klal
        # 163 report the overlay branch was written to fix, still live on the
        # path the overlay does not cover.
        f["word_flag"] = dict(f.get("current_decision") or {},
                              answered=bool(f.get("flag_answered")))
        corrections.append(f)

    # Witness disagreements that have a corpus word_index (patched in by
    # tools/patch_witness_word_indices.py) are added as 'witness' entries so
    # the text pane can highlight them alongside other flagged words.
    # word_index=None items (9/419 unmapped) are scan-only and stay that way.
    witness_decided = rd.all_current("witness_choice")
    klal_witness = []
    for w in _load_witness_queue():
        if w["klal_id"] != klal_id:
            continue
        klal_witness.append(w)
        wi = w.get("word_index")
        if wi is None or not (0 <= wi < len(words)):
            continue
        if wi in manual_word_indices:
            continue
        # A witness disagreement at a position that already carries a machine
        # candidate or a word-level flag must NOT be appended as a second entry -
        # it would shadow the richer one under app.js's last-write-wins map.
        # Measured 2026-08-24: 4 replace+witness collisions (klal 30 w828/w907,
        # klal 75 w853, klal 88 w310) and 1 ai_flag+witness (klal 88 w327).
        # The machine candidate is the more valuable of the two by a wide
        # margin - it carries a bbox, both readings, a vision verdict and a
        # confidence, whereas this project measured Tesseract correct in only
        # 16 of 419 witness disagreements (3.8%). So overlay the witness data
        # onto the existing entry rather than replacing it, and keep the item in
        # klal_witness either way so the witness count and the scan pane are
        # unaffected.
        if _claim_word_index(corrections, wi, "witness_overlay", {
                "docai_token_index": w["docai_token_index"],
                "tier": w.get("tier"),
                "docai_reading": w.get("docai_reading"),
                "tesseract_reading": w.get("tesseract_reading"),
                "current_decision": witness_decided.get((klal_id, w["docai_token_index"])),
        }) is not None:
            continue
        corrections.append({
            "word_index": wi,
            "opcode": "witness",
            "klal_id": klal_id,
            "docai_token_index": w["docai_token_index"],
            "tier": w.get("tier"),
            "docai_reading": w.get("docai_reading"),
            "tesseract_reading": w.get("tesseract_reading"),
            "vision_selected": w.get("vision_selected"),
            "vision_transcription": w.get("vision_transcription"),
            "final_text": None,
            "page": w.get("page"),
            "bbox": w.get("bbox"),
            "confidence": w.get("vision_confidence"),
            "reasoning": None,
            "flag": "witness",
            "current_decision": witness_decided.get((klal_id, w["docai_token_index"])),
        })

    regions = _load_regions()
    region_entry = regions.get(str(klal_id), {})
    _klal_page, _klal_page_trusted = _resolve_klal_page(alignment, regions, klal_id)
    flag_state = _general_klal_flag_current(klal_id)

    # Real (DocAI-alignment-based) word_index -> page map, covering every
    # word on every page this klal touches - not an approximation. FIXED
    # 2026-08-21 (user report: klal 2 word 185 stayed on page 15 instead of
    # jumping back to 14, and highlighted the wrong word). The frontend
    # previously had no per-word page data for plain (unflagged) words and
    # fell back to a client-side heuristic (continuationBoundaries() in
    # app.js, built from a continuation's token_count - a DocAI-page word
    # count, explicitly documented there as "a same-neighborhood
    # approximation, not an exact boundary"). That approximation put the
    # page-14/15 split at word_index 151; the real split (per this same
    # SequenceMatcher alignment _word_level_ai_flags already trusts for
    # ai_flag words) is elsewhere, so words in the gap between the two
    # estimates navigated to the wrong page. See _word_pages_map()'s own
    # docstring for a second, since-fixed bug in this same field (a
    # duplicate-text-across-pages collision).
    word_pages = _word_pages_map(klal_id, words, region_entry)

    # FIXED 2026-08-21 (code review): every sibling loader in this function
    # (_load_klalim, _load_alignment, _load_corrections) threads part_num
    # through; this one didn't, defaulting to Part 1's punctuation file for
    # every klal regardless of which part it's actually in. Currently silent
    # (only punctuation_candidates_part1.json exists), but
    # _load_punctuation_candidates()'s own docstring anticipates
    # punctuation_candidates_part{2,3}.json being added later - once they
    # are, this would keep reading Part 1's file for every Part 2/3 klal.
    punct_candidates = _load_punctuation_candidates(part_num=part_num).get(str(klal_id), [])
    # One all_current() map rather than a per-candidate current_for() - the
    # same fix _merge_decision() already carries and for the same reason:
    # every current_for() call re-reads and re-parses the WHOLE, permanently
    # growing review_decisions.jsonl, so this loop cost one full parse per
    # proposed punctuation break on every /api/klal request. Same semantics
    # (both resolve a key to the last matching line in file order).
    punct_decided = rd.all_current("punctuation_choice")
    punctuation = []
    for p in punct_candidates:
        idx = p["before_word_index"]
        decision = punct_decided.get((klal_id, idx))
        punctuation.append({
            "before_word_index": idx,
            "reasoning": p.get("reasoning", ""),
            "current_decision": (
                {"accepted": decision["chosen_source"] == "accept", "note": decision.get("note")}
                if decision else None
            ),
        })

    return {
        "klal_id": k["klal_id"],
        "title": k.get("title", ""),
        "section": k.get("section", ""),
        "gematria": k.get("gematria", ""),
        "clean_text": k.get("clean_text", ""),
        "page": _klal_page,
        "page_trusted": _klal_page_trusted,
        "region": region_entry.get("bbox"),
        # klal's content continues onto one or more later pages (e.g. klal 4:
        # starts on page 15's last line, most of its text is on page 16) -
        # a per-page bbox for each, so the scan-pane highlight can follow
        # the klal when the reviewer manually flips pages.
        "continuations": region_entry.get("continuations", []),
        "word_pages": word_pages,
        "corrections": corrections,
        "punctuation": punctuation,
        "needs_revisit": bool(flag_state and flag_state.get("needs_revisit")),
        "flag_note": flag_state.get("note") if flag_state else None,
        # Witness disagreements have no corpus word_index - they live on the
        # scan's continuation pages only and are never highlighted in the text
        # pane. Expose the count + pages so renderKlalBody can show an
        # informational banner instead of silently showing 0 text highlights
        # for a klal whose nav badge is driven entirely by these scan items.
        "witness_count": len(klal_witness),
        "witness_pages": sorted({w["page"] for w in klal_witness if w.get("page")}),
    }


def api_klal_flag(klal_id):
    # General klal-level flag panel only (word_index is None) - a word-level
    # AI flag (word_index set) must never surface here as if it were the
    # klal's own note; see _general_klal_flag_current()'s docstring above.
    current = _general_klal_flag_current(klal_id)
    history = _general_klal_flag_history(klal_id)
    return {
        "needs_revisit": bool(current and current.get("needs_revisit")),
        "note": current.get("note") if current else None,
        "history": history,
    }


def api_decision_history(klal_id, word_index):
    # Three decision types can share a (klal_id, word_index) key -
    # candidate_choice (machine-flagged), manual_correction (2026-08-13,
    # reviewer-flagged), and klal_flag with a word_index set (bug #1 fix,
    # earlier today - an ai_flag word's own history) - merge all three so
    # the frontend's one generic history panel works for any of them
    # without needing to know which kind of word it's looking at. In
    # practice a given word_index only ever carries one of the three (a
    # manual flag is only offered on a word with no machine candidate, an
    # ai_flag is skipped once a manual_correction covers the same word -
    # see review_frontend/app.js's renderKlalBody and
    # _word_level_ai_flags() above), but merging costs nothing and doesn't
    # assume that.
    #
    # FIXED 2026-08-17 (code review): before this, "Show decision history"
    # on an ai_flag word reported "No decisions recorded yet" even though
    # the flag itself IS a recorded decision - klal_flag was entirely
    # absent from this merge. history_for()'s own word_index filter (None
    # never matches a specific index) keeps this from ever leaking a
    # klal's GENERAL note in here, so no separate exclusion is needed.
    history = rd.history_for(klal_id, word_index, "candidate_choice") + \
        rd.history_for(klal_id, word_index, "manual_correction") + \
        rd.history_for(klal_id, word_index, "klal_flag")
    history.sort(key=lambda r: r["ts"])
    return history


def api_page(page_num):
    _, klalim = _load_klalim("all")
    klalim_by_id = {k["klal_id"]: k for k in klalim}
    alignment = _load_alignment()
    regions = _load_regions()
    corrections = _load_corrections()
    decided = rd.all_current("candidate_choice")
    # All klals whose scan content (start or continuation) touches this page.
    page_klals = _klals_on_page(page_num, alignment, regions)
    out = []
    for kid in page_klals:
        # Filter corrections by their own page field - a klal spanning pages
        # 15-16 has corrections with page=15 and page=16; only serve the ones
        # belonging to the requested page.
        for c in corrections.get(str(kid), []):
            if not c.get("bbox") or c.get("page") != page_num:
                continue
            entry = _merge_decision(c, kid, decided)
            entry["klal_id"] = kid
            entry["kind"] = "correction"
            out.append(entry)

    # Witness disagreements for this page. Keyed by docai_token_index, a
    # different index space from corrections' word_index - safe because
    # all_current() is scoped to one decision_type, so the two never collide.
    # Resolved from one map rather than a per-item current_for(), the same
    # fix _merge_decision() already carries: a witness page carries ~140
    # items, and each current_for() re-parsed the whole decisions log.
    witness_decided = rd.all_current("witness_choice")
    # Same last-write-wins hazard as api_klal()'s corrections list, on the scan
    # side: a witness item whose (klal_id, word_index) already has a correction
    # box would draw a SECOND box at the same coordinates, and the pane's click
    # and focus handling keys on that pair. Found 2026-08-24 by sweeping all 63
    # pages after fixing the text-pane collisions - the same four positions turn
    # up here (klal 30 w828/w907, klal 75 w853, klal 88 w310), because this
    # function builds its list independently and repeats the defect.
    # Note the ordering: this dedupe must consider only the CORRECTION boxes
    # appended above, which is why it is computed here rather than reusing the
    # `served_keys` set below (that one is built after this loop, for the
    # plain-word pass). Witness items with word_index=None are scan-only by
    # design and always render.
    correction_keys = {(x["klal_id"], x["word_index"]) for x in out
                       if x.get("word_index") is not None}
    for w in _load_witness_queue():
        if w.get("page") != page_num or not w.get("bbox"):
            continue
        wi = w.get("word_index")
        if wi is not None and (w["klal_id"], wi) in correction_keys:
            continue
        entry = dict(w)
        entry["kind"] = "witness"
        entry["current_decision"] = witness_decided.get(
            (w["klal_id"], w["docai_token_index"]))
        out.append(entry)

    # Word-level AI flags and manual corrections, which have no entry in
    # corrections_part1.json and so never reached this endpoint.
    #
    # FIXED 2026-08-25 (reviewer, klal 218: "has only one red item in the right
    # pane" while the text pane shows two flagged words). api_klal() synthesizes
    # entries for both kinds so the TEXT pane can highlight them; this function
    # built its list independently from the corrections file, the witness queue
    # and plain words, so a flagged word with no machine candidate behind it
    # reached the SCAN pane as an anonymous `plain` box - same colourless
    # treatment as ordinary prose. Measured: **187 word-level flags and 8 manual
    # corrections across 88 klalim** were invisible as flagged on the scan.
    # Two functions drawing the same picture from different sources is the same
    # defect shape as the 2026-08-24 collision sweep; the precedence below
    # mirrors api_klal()'s exactly.
    correction_keys |= {(x["klal_id"], x["word_index"]) for x in out
                        if x.get("word_index") is not None}
    manual_current = rd.all_current("manual_correction")
    for kid in page_klals:
        k = klalim_by_id.get(kid)
        if not k:
            continue
        words = (k.get("clean_text") or "").split(" ")
        for (mkid, wi), rec in manual_current.items():
            if mkid != kid or (kid, wi) in correction_keys:
                continue
            original_word = rec.get("candidate_snapshot", {}).get("original_word")
            if not _word_matches(words, wi, original_word):
                continue
            bbox, bpage = _word_scan_position(kid, words, wi)
            if not bbox or bpage != page_num:
                continue
            out.append({"klal_id": kid, "word_index": wi, "bbox": bbox, "page": page_num,
                        "kind": "correction", "opcode": "manual", "flag": "manual_correction",
                        "final_text": original_word, "current_decision": rec})
            correction_keys.add((kid, wi))
        for f in _word_level_ai_flags(kid, words):
            wi = f["word_index"]
            if (kid, wi) in correction_keys or f.get("page") != page_num or not f.get("bbox"):
                continue
            entry = dict(f)
            entry["klal_id"] = kid
            entry["kind"] = "correction"
            out.append(entry)
            correction_keys.add((kid, wi))

    # Word-level bboxes for all words on the page (looked up from DocAI tokens).
    # Ensures that clicking ANY word (flagged or unflagged) highlights its exact
    # bounding box on the scan image.
    served_keys = {(x["klal_id"], x["word_index"]) for x in out if "word_index" in x}
    for kid in page_klals:
        k = klalim_by_id.get(kid)
        if not k:
            continue
        words = (k.get("clean_text") or "").split(" ")
        page_bboxes = _corpus_word_bboxes(kid, words, page_num)
        for wi, bbox in page_bboxes.items():
            if (kid, wi) not in served_keys:
                out.append({
                    "klal_id": kid,
                    "word_index": wi,
                    "bbox": bbox,
                    "page": page_num,
                    "kind": "plain"
                })
                served_keys.add((kid, wi))
    return out


def api_post_disputed_decision(body):
    klal_id = int(body["klal_id"])
    word_index = int(body["word_index"])
    if body.get("chosen_text") is None:
        # FIXED 2026-08-26 (code review). api_post_manual_decision() has carried
        # this exact check, with this exact rationale, since it was written; this
        # handler never got it. app.js's saveDisputedDecision() falls back to
        # `source = 'final_text'` when no option is selected, and a `delete`
        # (omission) candidate or a synthesized `ai_flag` entry has no
        # final_text - so a Save with nothing chosen POSTed chosen_text: null.
        # Four such rows are in review_decisions.jsonl already (klal 90 w4,
        # 88 w1149, 164 w55, 2 w632). They mark the word decided and answer its
        # revisit flag while being impossible to apply, and the log is
        # append-only, so they can be superseded but never removed. Guarded at
        # the write site as well as in the client, because the client is not the
        # only thing that can POST here.
        raise ValueError("chosen_text is required (pass '' explicitly to reject)")
    corrections = _load_corrections().get(str(klal_id), [])
    snapshot = next((c for c in corrections if c["word_index"] == word_index), None)
    record = rd.append_decision(
        "disputed_choice",
        klal_id=klal_id,
        word_index=word_index,
        chosen_source=body.get("chosen_source"),
        chosen_text=body.get("chosen_text"),
        candidate_snapshot=snapshot,
        note=body.get("note"),
    )
    return record


api_post_candidate_decision = api_post_disputed_decision


def api_post_punctuation_decision(body):
    klal_id = int(body["klal_id"])
    word_index = int(body["before_word_index"])
    accepted = bool(body["accepted"])
    # FIXED 2026-08-21 (code review, same omission as api_klal()'s own
    # _load_punctuation_candidates() call above): must thread part_num
    # through so a Part 2/3 candidate's snapshot isn't silently looked up
    # against Part 1's punctuation file once punctuation_candidates_part{2,
    # 3}.json exist.
    part_num = _get_part_num_for_klal(klal_id)
    candidates = _load_punctuation_candidates(part_num=part_num).get(str(klal_id), [])
    snapshot = next((p for p in candidates if p["before_word_index"] == word_index), None)
    record = rd.append_decision(
        "punctuation_choice",
        klal_id=klal_id,
        word_index=word_index,
        chosen_source="accept" if accepted else "reject",
        chosen_text="[.]" if accepted else None,
        candidate_snapshot=snapshot,
        note=body.get("note"),
    )
    return record


def api_witness_summary():
    """Pages carrying witness items + tier counts. Needed because these are
    CONTINUATION-ONLY pages (no klal marker of their own), so they are absent
    from the nav's klal->page map and the scan pane's page-stepper would skip
    straight over them - the reviewer could not reach the very pages the queue
    is about."""
    q = _load_witness_queue()
    decided = rd.all_current("witness_choice")
    pages, tiers = {}, {}
    for w in q:
        pg = w.get("page")
        d = (w["klal_id"], w["docai_token_index"]) in decided
        e = pages.setdefault(pg, {"page": pg, "klal_id": w.get("klal_id"), "total": 0, "decided": 0})
        e["total"] += 1
        e["decided"] += 1 if d else 0
        tiers[w.get("tier")] = tiers.get(w.get("tier"), 0) + 1
    return {"pages": [pages[k] for k in sorted(pages)], "by_tier": tiers, "total": len(q)}


def api_post_witness_decision(body):
    klal_id = int(body["klal_id"])
    token_index = int(body["docai_token_index"])
    queue = _load_witness_queue()
    snapshot = next((w for w in queue
                     if w["klal_id"] == klal_id and w["docai_token_index"] == token_index), None)
    return rd.append_decision(
        "witness_choice",
        klal_id=klal_id,
        word_index=token_index,
        chosen_source=body.get("chosen_source"),   # docai_reading | tesseract_reading | custom | unreadable
        chosen_text=body.get("chosen_text"),
        candidate_snapshot=snapshot,
        note=body.get("note"),
    )


WITNESS_CONTEXT_WINDOW = 12  # docai tokens shown on each side of a witness item
# Must match verify_reconstruction_witness.py's HEB/norm() exactly:
# `docai_token_index` in reconstruction_witness_queue.json is an index into
# THAT script's `dtoks` list (raw page tokens filtered to `norm(text)`
# truthy - i.e. digits and pure punctuation dropped), not the raw per-page
# array. Bug found 2026-08-12: an earlier version of this function indexed
# the raw array directly, which happened to look plausible but silently
# pointed 1 token early on page 37 (raw index 13 "דתנא" instead of the real
# target, raw index 14 "נינהו") - confirmed by cross-checking against
# verify_reconstruction_witness.py's own source. Any fix must re-derive the
# same filtered sequence, not guess an offset.
#
# "Must match ... exactly" was enforced by hand until 2026-08-17: this file,
# verify_reconstruction_witness.py and verify_witness_vision.py each held
# their own copy of the same 27-character literal and the same one-line
# filter. Now all three call corpus_io.hebrew_letters_only, so the
# must-match-exactly requirement is structural rather than a comment asking
# the next editor to remember.
WITNESS_HEB = cio.HEBREW_LETTERS
_witness_norm = cio.hebrew_letters_only


def api_witness_context(page, token_index):
    """Docai tokens surrounding a witness item, for the review panel - see
    WITNESS_HEB comment above for why this can't just slice the raw page
    array. Added 2026-08-12 per direct user feedback while reviewing klal
    30's witness queue: a bare image crop with no surrounding text is hard
    to place in context ("it is hard to review the image in a vacuum... use
    the text you have - it is better than nothing"). Deliberately the raw
    OCR token stream for the page, NOT the not-yet-applied reconstruction
    draft from reconstruct_multipage_klalim.py (that text only exists
    in-memory inside that script's dry run and isn't cached anywhere -
    integrating it would mean re-deriving which klal/segment a given
    (page, token_index) falls into, a bigger job). This is simpler, always
    available for any witness item, and the frontend presents it plainly as
    raw OCR context, not a vetted reading - it can still include furniture
    words (header vocabulary normalizes to non-empty Hebrew text too, so it
    isn't filtered out here any more than it was in the original script) and
    either engine's own misreads."""
    tokens = cio.load_docai_page(page)
    if not tokens:
        return {"words": [], "target_index": None}
    dtoks = [t for t in tokens if _witness_norm(t["text"])]
    if token_index < 0 or token_index >= len(dtoks):
        return {"words": [], "target_index": None}
    lo = max(0, token_index - WITNESS_CONTEXT_WINDOW)
    hi = min(len(dtoks), token_index + WITNESS_CONTEXT_WINDOW + 1)
    return {"words": [t["text"] for t in dtoks[lo:hi]], "target_index": token_index - lo}


def api_post_klal_flag(body):
    """Record a klal-level OR word-level revisit flag.

    FIXED 2026-08-24 (user report: "i can't clear the revisit flag"). This used
    to ignore word_index entirely, so it could only ever write a KLAL-level
    flag. But _word_level_ai_flags() keys word-level flags on word_index and
    stops rendering one only when a later record at THAT SAME (klal_id,
    word_index) sets needs_revisit false - which this endpoint had no way to
    write. Word-level flags (e.g. klal 91 w453/w524, klal 167's) were therefore
    settable by script and un-clearable from the dashboard.

    word_index is optional and absent means klal-level, preserving the previous
    behaviour exactly for every existing caller."""
    klal_id = int(body["klal_id"])
    word_index = body.get("word_index")
    record = rd.append_decision(
        "klal_flag",
        klal_id=klal_id,
        word_index=int(word_index) if word_index is not None else None,
        needs_revisit=bool(body.get("needs_revisit")),
        note=body.get("note"),
    )
    return record


def api_post_manual_correction(body):
    """A reviewer flagging/replacing ANY word, not just one the machine
    pipeline already flagged (2026-08-13). candidate_snapshot captures the
    word actually seen at word_index at flagging time, since there's no
    corrections_part1.json entry to snapshot instead - apply_reviewer_
    decisions.py's manual-correction pass drift-checks against this
    directly against the live part1.json text.

    chosen_text == "" (explicitly, not missing) means DELETE the word
    entirely (2026-08-13, "need ability to delete selected word, not just
    change it") - apply_manual_deletion there handles that case, sharing
    the insert/delete word-count-change guard since removing a word
    shifts every later index in the klal. A missing chosen_text field
    (None) is still rejected - that's a client bug, not an intentional
    empty replacement."""
    klal_id = int(body["klal_id"])
    word_index = int(body["word_index"])
    if word_index < 0:
        # Refuse at the write site as well as guarding the two read sites
        # (_word_matches): a negative index is never a valid position in
        # clean_text.split(' '), and letting one into the append-only log
        # means it is there permanently - the log is deliberately never
        # rewritten, so a bad row can only ever be superseded, not removed.
        raise ValueError(f"word_index must be >= 0, got {word_index}")
    chosen_text = body.get("chosen_text")
    if chosen_text is None:
        raise ValueError("chosen_text is required (pass '' explicitly to delete)")
    chosen_text = chosen_text.strip()
    record = rd.append_decision(
        "manual_correction",
        klal_id=klal_id,
        word_index=word_index,
        chosen_source="custom" if chosen_text else "delete",
        chosen_text=chosen_text,
        candidate_snapshot={"word_index": word_index, "original_word": body.get("original_word")},
        note=body.get("note"),
    )
    return record


# ---------- HTTP plumbing ----------

ROUTE_KLAL = re.compile(r"^/api/klal/(\d+)$")
# Shareable, terminal-safe deep links. `/#klal=66&word=135` is the form the
# frontend actually routes on, but it travels badly: a terminal will not
# hyperlink Markdown link syntax at all, and many that DO linkify a bare URL
# stop at the `&` - producing a link that opens the right klal at the wrong
# word, which is worse than one that plainly fails. A path has no `#` and no
# `&`, so it survives being pasted anywhere. ADDED 2026-08-26 (reviewer: "sadly
# those links you shared here in the chat are not clickable").
ROUTE_SHARE = re.compile(r"^/klal/(\d+)(?:/word/(\d+))?/?$")
ROUTE_KLAL_FLAG = re.compile(r"^/api/klal/(\d+)/flag$")
ROUTE_DECISIONS = re.compile(r"^/api/decisions/(\d+)/(\d+)$")
ROUTE_PAGE = re.compile(r"^/api/page/(\d+)$")
ROUTE_WITNESS_CONTEXT = re.compile(r"^/api/witness/context/(\d+)/(\d+)$")


_ASSET_VERSION_RE = re.compile(rb"/(app\.(?:js|css))\?v=[^\"']*")


def _stamp_asset_versions(html, base_dir):
    """Rewrite `/app.js?v=N` to a version derived from the file itself.

    ADDED 2026-08-25. `index.html` carried a hand-maintained `?v=6` that was last
    bumped in commit 1e59522 and never again, through every app.js change since -
    a convention that rots the moment anyone forgets, and nobody remembers to
    bump a cache-buster while fixing a bug. The reviewer hit exactly that: after
    the manual-panel auto-close fix landed they reported "still doesn't autoclose
    when i save decision" on a page whose tab had been open since before the fix,
    running the old file.

    `Cache-Control: no-cache, must-revalidate` (below) means a plain reload
    already picks up new bytes, so this is not a correctness fix - it removes a
    step a human has to remember, and it fails closed: if the file cannot be
    stat'd the original markup is served untouched.
    """
    def _sub(match):
        name = match.group(1).decode()
        try:
            st = os.stat(os.path.join(base_dir, name))
        except OSError:
            return match.group(0)
        stamp = f"{int(st.st_mtime)}-{st.st_size}"
        return f"/{name}?v={stamp}".encode()
    return _ASSET_VERSION_RE.sub(_sub, html)


class Handler(BaseHTTPRequestHandler):
    server_version = "YadMalachiReview/1.0"

    def log_message(self, fmt, *args):
        sys.stderr.write(f"[{self.log_date_time_string()}] {self.address_string()} - {fmt % args}\n")
        sys.stderr.flush()

    def _send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error_json(self, status, message):
        self._send_json({"error": message}, status=status)


    def _serve_static(self, base_dir, rel_path, default_file=None):
        if rel_path in ("", "/"):
            rel_path = default_file or "index.html"
        rel_path = rel_path.lstrip("/")
        full_path = os.path.realpath(os.path.join(base_dir, rel_path))
        base_real = os.path.realpath(base_dir)
        if not full_path.startswith(base_real + os.sep) and full_path != base_real:
            self._send_error_json(403, "forbidden")
            return
        if not os.path.isfile(full_path):
            self._send_error_json(404, "not found")
            return
        ext = os.path.splitext(full_path)[1]
        content_type = MIME_TYPES.get(ext, "application/octet-stream")
        with open(full_path, "rb") as f:
            body = f.read()
        if os.path.basename(full_path) == "index.html":
            body = _stamp_asset_versions(body, base_dir)
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache, must-revalidate")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        try:
            if path == "/api/flags":
                return self._send_json(api_flags())
            if path == "/api/witness":
                return self._send_json(api_witness_summary())
            if path == "/api/klalim":
                part_val = query.get("part", ["1"])[0]
                return self._send_json(api_klalim(part_num=part_val))
            m = ROUTE_SHARE.match(path)
            if m:
                target = "/#klal=" + m.group(1)
                if m.group(2) is not None:
                    target += "&word=" + m.group(2)
                self.send_response(302)
                self.send_header("Location", target)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            m = ROUTE_KLAL_FLAG.match(path)
            if m:
                return self._send_json(api_klal_flag(int(m.group(1))))
            m = ROUTE_KLAL.match(path)
            if m:
                payload = api_klal(int(m.group(1)))
                if payload is None:
                    return self._send_error_json(404, "klal not found")
                return self._send_json(payload)
            m = ROUTE_DECISIONS.match(path)
            if m:
                return self._send_json(api_decision_history(int(m.group(1)), int(m.group(2))))
            m = ROUTE_PAGE.match(path)
            if m:
                return self._send_json(api_page(int(m.group(1))))
            m = ROUTE_WITNESS_CONTEXT.match(path)
            if m:
                return self._send_json(api_witness_context(int(m.group(1)), int(m.group(2))))
            if path.startswith("/images/pdf_pages/"):
                return self._serve_static(IMAGES_DIR, path[len("/images/pdf_pages"):])
            if path.startswith("/api/"):
                return self._send_error_json(404, "unknown endpoint")
            return self._serve_static(FRONTEND_DIR, path)
        except Exception as e:  # noqa: BLE001 - surface as JSON, don't crash the server thread
            self._send_error_json(500, f"{type(e).__name__}: {e}")

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b"{}"
            body = json.loads(raw.decode("utf-8"))

            if path in ("/api/decisions/disputed", "/api/decisions/candidate"):
                return self._send_json(api_post_disputed_decision(body), status=201)
            if path == "/api/decisions/punctuation":
                return self._send_json(api_post_punctuation_decision(body), status=201)
            if path == "/api/decisions/witness":
                return self._send_json(api_post_witness_decision(body), status=201)
            if path == "/api/decisions/klal_flag":
                return self._send_json(api_post_klal_flag(body), status=201)
            if path == "/api/decisions/manual":
                return self._send_json(api_post_manual_correction(body), status=201)
            return self._send_error_json(404, "unknown endpoint")
        except (KeyError, ValueError, TypeError) as e:
            return self._send_error_json(400, f"bad request: {e}")
        except Exception as e:  # noqa: BLE001
            self._send_error_json(500, f"{type(e).__name__}: {e}")


def _preflight_check():
    """Fail loudly at startup if required data files are missing or unreadable,
    rather than letting the first API request throw an opaque exception.
    Returns a list of problem strings (empty = all good)."""
    problems = []
    required = [
        (rd.DECISIONS_PATH, "review_decisions.jsonl (append-only audit log)"),
        (cio.repo_path("klalim_demo_dataset.json"), "klalim_demo_dataset.json (corpus text)"),
        (cio.repo_path("corrections_part1.json"), "corrections_part1.json (machine candidates)"),
        (cio.repo_path("part1_header_anchored_alignment.json"), "page alignment"),
        (cio.repo_path("klal_page_regions.json"), "klal page regions"),
    ]
    for path, label in required:
        if not os.path.exists(path):
            problems.append(f"  MISSING: {label}\n    → {path}")
        elif not os.access(path, os.R_OK):
            problems.append(f"  NOT READABLE: {label}\n    → {path}")
    return problems


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8420)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    problems = _preflight_check()
    if problems:
        print("ERROR: required files are missing or unreadable:")
        print("\n".join(problems))
        sys.exit(1)

    try:
        server = ThreadingHTTPServer((args.host, args.port), Handler)
    except OSError as e:
        if e.errno in (48, 98):  # EADDRINUSE on macOS (48) and Linux (98)
            print(f"ERROR: port {args.port} is already in use.")
            print(f"  Is another instance of review_server.py already running?")
            print(f"  To find it:  lsof -i :{args.port}")
            print(f"  To stop it:  kill $(lsof -t -i :{args.port})")
            print(f"  Or start on a different port:  python3 review_server.py --port 8421")
        else:
            print(f"ERROR: could not bind to {args.host}:{args.port}: {e}")
        sys.exit(1)

    print(f"Yad Malachi review server: http://{args.host}:{args.port}/")
    print(f"Decisions log: {rd.DECISIONS_PATH}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.shutdown()


if __name__ == "__main__":
    main()
