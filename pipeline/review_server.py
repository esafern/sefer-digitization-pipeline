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
import scan_alignment as sa
import review_counts as rcount
import review_data as rdata
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

# Word-state rule and the counts over it live in review_counts.py as of
# 2026-09-01 (finding S1, second half; finding #6's "shared word_state()").
# Aliased for the same reason scan_alignment's names are - existing call sites
# and two tests read review_server.MACHINE_RESOLVED_FLAGS and friends directly.
MACHINE_RESOLVED_FLAGS = rcount.MACHINE_RESOLVED_FLAGS

# Per-part corpus/queue loading lives in review_data.py as of 2026-09-01,
# closing finding C4 - see that module's header. Aliased like the other two
# extractions: api_klal/api_klalim look these up as globals of THIS module, so
# the many tests that monkeypatch review_server._load_klalim and friends keep
# working unchanged.
BadRequest = rdata.BadRequest
_get_part_num_for_klal = rdata.get_part_num_for_klal
_normalize_part = rdata.normalize_part
_parts_for = rdata.parts_for
_load_klalim = rdata.load_klalim
_load_alignment = rdata.load_alignment
_load_corrections = rdata.load_corrections
_load_punctuation_candidates = rdata.load_punctuation_candidates
_load_witness_queue = rdata.load_witness_queue
WITNESS_PRIORITY_VERDICTS = rdata.WITNESS_PRIORITY_VERDICTS
WITNESS_QUEUE_FILTERED = rdata.WITNESS_QUEUE_FILTERED

_word_matches = rcount.word_matches
_flag_answered_by_a_later_decision = rcount.flag_answered_by_a_later_decision
_claim_word_index = rcount.claim_word_index
_merge_decision = rcount.merge_decision


# ---------------------------------------------------------------------------
# Scan geometry lives in scan_alignment.py as of 2026-09-01 (finding C4 / S1).
#
# These aliases are not ceremony. The names below are used at ~40 call sites in
# this file and by a dozen tests that reach for review_server._word_scan_position
# and friends; re-pointing them here keeps the extraction a MOVE rather than a
# rewrite, so a regression in this commit can only come from the move itself.
#
# They are also what keeps the existing monkeypatch-based tests working:
# api_klal() and api_page() look these up as module globals of THIS module, so
# a test patching review_server._load_regions still intercepts. Code inside
# scan_alignment calls its own module-level names, so a test that needs to
# intercept THOSE must patch scan_alignment.load_regions instead - one such
# test exists and says so.
#
# New callers - in this file or anywhere else - should use the public
# scan_alignment names directly. These aliases exist for the code that predates
# the split, not as the preferred spelling.
_load_regions = sa.load_regions
_resolve_klal_page = sa.resolve_klal_page
_klal_all_pages = sa.klal_all_pages
_klals_on_page = sa.klals_on_page
_corpus_stamp = sa.corpus_stamp
_docai_page_stamp = sa.docai_page_stamp
corpus_bbox_cache_key = sa.corpus_bbox_cache_key
_corpus_word_bboxes = sa.corpus_word_bboxes
_word_pages_map = sa.word_pages_map
_word_bboxes_resolved = sa.word_bboxes_resolved
_word_scan_position = sa.word_scan_position
# The SAME dict object, not a copy - tests pre-seed it through this name and
# scan_alignment reads it through its own. A rebinding here would silently
# split them in two.
_corpus_bbox_cache = sa.bbox_cache
# ---------------------------------------------------------------------------


# Same treatment for the Part 2/3 bounds, ADDED 2026-08-31 (finding S5/#6):
# these two functions below carried `223`/`444`/`445` as bare literals, which
# is the same three-copies-must-agree problem PART1_MAX_KLAL was consolidated
# to end, minus the test that made it safe.
PART2_MAX_KLAL = cio.PART2_MAX_KLAL
PART3_MAX_KLAL = cio.PART3_MAX_KLAL
PART2_MIN_KLAL = cio.PART2_MIN_KLAL
PART3_MIN_KLAL = cio.PART3_MIN_KLAL


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






# ---------- API payload builders ----------

def api_flags():
    return FLAG_LABELS


def api_numerals(max_n=400):
    """{n: Hebrew numeral} for 1..max_n, so the frontend can render a page or a
    klal the way the BOOK writes it without carrying its own gematria table.

    ADDED 2026-08-31 (reviewer: the scan header should carry the same reference
    in Hebrew). Served rather than reimplemented in JS deliberately: a second
    copy of `klal_id_to_gematria` in app.js would be Lesson 13 exactly, and this
    one has real edge cases a reimplementation would miss - the 15/16 exception
    (ט"ו/ט"ז, not י"ה/י"ו, which would spell divine names) and the word-final
    letter substitution. One fetch at init covers every page and klal id.

    NOTE FOR THE CALLER: for a scan page this is OUR page index written in
    Hebrew letters, NOT the folio the book prints on that leaf. The printed
    folio is stripped as furniture and is not stored anywhere in this repo.
    """
    return {n: cio.klal_id_to_gematria(n) for n in range(1, max_n + 1)}


def api_klalim(part_num=1, on_klal_states=None):
    """The nav payload for one part.

    `on_klal_states` is an optional callback invoked once per klal with
    a context dict (klal, words, states, ai_flag_indices, entries, recorded) -
    everything /api/word-states
    needs to ENUMERATE the words this endpoint COUNTS. It is a callback rather
    than a second function because the two answers must come from one pass: the
    counts in the legend and the list behind each count are the same set, and
    the way this file has produced disagreeing numbers before is by computing
    them in two places (see review_counts.py's header). Nothing about the JSON
    payload changes when it is passed.
    """
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
        # rcount.flag_still_open() with this request's two decision maps bound.
        return rcount.flag_still_open(kid, widx, rec, decided, _manual_for_flags)

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
        words = cio.words_of(k)
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

    # RECORDED word-level decisions, per klal - deliberately NOT drift-checked
    # and deliberately NOT limited to what still renders.
    #
    # ADDED 2026-09-01 (reviewer: "count for human decisions is 51 - not
    # correct"). The legend's Human-Decided total is decided_count, which counts
    # words currently rendered GREEN, and a decision stops being rendered the
    # moment it is settled: assemble_corrections_dataset.py drops the candidate
    # entry, and the manual_correction drift check above skips a decision whose
    # `original_word` is no longer at that index - which is precisely what
    # applying it does. So the reviewer's 463 recorded decisions in Part 1
    # displayed as 51, and the number read as "you have decided 51 words".
    #
    # Both numbers are wanted and they answer different questions: decided_count
    # is "how much green is on screen", this is "how much have I ruled on". The
    # legend shows them together rather than replacing one with the other -
    # swapping them would have broken the tri-state identity
    # (decided + resolved + disputed == total) that
    # test_nav_tristate_matches_what_each_word_actually_renders_as asserts.
    #
    # ALL THREE decision types that can turn a word green are folded in, keyed to
    # one index space so the union deduplicates (63 Part 1 positions carry both a
    # manual correction and a candidate/disputed ruling):
    #   - candidate_choice, which review_decisions._match_decision_types aliases
    #     to disputed_choice, so `decided` already covers both;
    #   - manual_correction, which shares the word_index space directly;
    #   - witness_choice, which does NOT - it keys on docai_token_index - and so
    #     is mapped through the witness queue's own word_index, exactly as
    #     review_counts.word_states() maps it before colouring the word.
    #
    # That third one is not tidiness. It was left out of the first cut of this
    # count and klal 30 immediately served recorded=3 against decided=9: six
    # witness rulings that colour a word green while the number claiming to
    # count rulings did not see them, so the "of N recorded" figure was SMALLER
    # than the count it was meant to give context to. Caught by
    # test_recorded_decision_count_is_every_ruling_not_only_the_rendered_ones,
    # which asserts recorded >= decided for every klal. klalim 30 and 75 are the
    # same two that word_states()' own witness branch was written for.
    #
    # punctuation_choice (20 in Part 1) stays out: before_word_index addresses
    # the GAP between two words, not a word, and no punctuation decision renders
    # a word human-decided - including it would inflate a word count with
    # something that is not a word.
    # {klal_id: {word_index: the decision record}} - the RECORD, not just the
    # index, so /api/word-states can serve the senior-reviewer view (what was
    # ruled, by which panel, when, and whether the corpus reflects it) without
    # re-deriving "what counts as recorded" a second time. Newest ruling wins
    # where a word carries more than one.
    recorded_by_klal = {}
    # Rulings a later record explicitly replaces (review_decisions.append_decision's
    # `supersedes`). A re-pointed ruling lands at the CORRECT word_index, but the
    # log is append-only so the stale original still sits at the old one and is
    # still the newest record THERE - so without this the reviewer sees both, and
    # the stale-address count barely moves.
    _superseded = rd.superseded_ids()

    def _remember(kid, wi, rec):
        if rec.get("id") in _superseded:
            return
        slot = recorded_by_klal.setdefault(kid, {})
        prior = slot.get(wi)
        if prior is None or (rec.get("ts") or "") >= (prior.get("ts") or ""):
            slot[wi] = rec

    for _dmap in (decided, _manual_for_flags):
        for (kid, wi), rec in _dmap.items():
            _remember(kid, wi, rec)
    for kid, w_rows in witness_by_klal.items():
        for w in w_rows:
            wi = w.get("word_index")
            # A witness row with no word_index is never rendered and never
            # counted - see test_witness_rows_served_without_a_word_index_are_
            # never_counted, which exists because counting one put klal 88's
            # badge at -1.
            if wi is None:
                continue
            # NB the witness decision's own `word_index` field holds a
            # docai_token_index, not a word index - which is exactly why it has
            # to be re-keyed through the queue row here.
            rec = witness_decided.get((kid, w.get("docai_token_index")))
            if rec is not None:
                _remember(kid, wi, rec)

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
        words = cio.words_of(k)
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
            and 0 <= fwidx < n_words
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

        # The word-state rule and the counts over it now live in
        # review_counts.py (2026-09-01, finding S1 / finding #6). This loop used
        # to carry ~90 lines classifying each word inline, which is the third
        # encoding of a rule app.js and api_klal() also express; the history of
        # what each branch is defending against moved with it, into the
        # docstrings there.
        states = rcount.word_states(
            kid, n_words, entries, w_entries,
            manual_indices=manual_indices_for_count,
            open_flag_indices=ai_flag_indices_for_count,
            answered_flag_indices=answered_flag_indices,
            decided=decided,
            witness_decided=witness_decided,
        )
        counts = rcount.count_row(kid, states, entries, decided)
        if on_klal_states is not None:
            on_klal_states({
                "klal": k, "words": words, "states": states,
                "ai_flag_indices": ai_flag_indices_for_count, "entries": entries,
                "recorded": recorded_by_klal.get(kid, {}),
            })

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
            # split so the nav badge can distinguish "still needs a look"
            # from "already decided" instead of one undifferentiated count
            # (2026-08-07, PROJECT-STATUS.md "review dashboard feedback").
            # correction_count / decided_count / open_count /
            # machine_disputed_count / machine_resolved_count all come from
            # rcount.count_row() as one block - they are one arithmetic
            # identity, and splitting them across the payload is how they
            # drifted apart before.
            **counts,
            "ai_flag_count": ai_flag_count,
            # Sits OUTSIDE the `counts` block on purpose: those five are one
            # arithmetic identity over what renders, and this is not part of it.
            "recorded_decision_count": len(recorded_by_klal.get(kid, {})),
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


def _decision_original_word(rec):
    """What the word WAS when this ruling was made.

    Three panels record it in two places: manual_correction snapshots
    `original_word`, candidate/disputed snapshot the candidate's `final_text`
    (the stored reading it was offering to change), and witness_choice snapshots
    neither - it offers `docai_reading` against `tesseract_reading` and the
    stored word is not part of the record. None where it genuinely is not known,
    rather than a guess dressed as a snapshot.
    """
    snap = rec.get("candidate_snapshot") or {}
    original = snap.get("original_word")
    if original is None:
        original = snap.get("final_text")
    return original


# Reviewer tags that mean A PERSON RULED. Everything else in the ledger was
# written by a script - `ai-dropped-lamed-correction`, `ai-semantic-spotcheck`,
# `tools/review_lexicon_gaps.py` and two dozen more.
#
# ADDED 2026-09-02, from a reviewer question that had no answer on screen: "did a
# human (me) adjudicate it? it wasn't marked in yellow or red." It was not. Those
# passes write `manual_correction` records, which this dashboard has always drawn
# GREEN as Human-Decided - so a machine ruling entered the corpus already looking
# settled and never appeared in anyone's queue. Measured that day: 1,615 of the
# ledger's 2,520 rulings were machine-written, and 102 of the 503 the dashboard
# currently counts as recorded.
#
# THE RULE ITSELF MOVED to review_decisions.py 2026-09-03 and these two names now
# delegate. It was written out twice - here for the display and there for the
# append guard - and a third consumer then needed it (the ligature invariant).
# Same answer in all three places, so it is one definition, per START_HERE's
# shared-module rule.
HUMAN_REVIEWERS = rd.HUMAN_REVIEWERS


def _ruled_by_human(rec):
    return rd.ruled_by_human(rec)


def _decision_index_is_stale(rec, words, word_index):
    """Does this ruling's recorded word_index still describe the word it ruled on?

    A SEPARATE question from _decision_status(), and separating them 2026-09-01
    corrected a number this file had already published. Item 0AB counted 105
    "orphaned" rulings by asking only "is the word at that index neither the
    original nor the chosen one" - which is true both for a ruling that was LOST
    and for one that was HONOURED and then had its index shifted out from under
    it by a later apply in the same klal. audit_applied_decisions.py separates
    exactly those two (55 shifted, 2 genuinely missing); this display did not,
    and reported both as the same failure.

    So: `status` is what happened to the RULING, this is what happened to its
    ADDRESS. Both matter and they are not the same defect - a stale address still
    breaks things (a re-decision at that key lands on the wrong word, and both
    display paths drop it) even when the ruling itself was honoured, which is
    what Lesson 35 is about.
    """
    if not (0 <= word_index < len(words)):
        return True
    original = _decision_original_word(rec)
    if original is None:
        return False               # nothing to compare - not a claim either way
    current = words[word_index]
    return current != original and current != rec.get("chosen_text")


def _decision_status(rec, words, word_index, applied_ids=()):
    """Does the corpus reflect this ruling? The senior-reviewer question.

    ADDED 2026-09-01 (reviewer: "add a function to show all previously decided
    words - so a sr reviewer can review a human's work"). Reviewing a ruling
    means seeing what was decided AND whether it landed, and until now neither
    was reachable: a settled decision stops rendering entirely (the rebuild drops
    its candidate entry; an applied manual correction fails the display drift
    check), so the dashboard showed 51 of 478 rulings and nothing about the rest.

      confirmed - the ruling KEPT the stored reading. There was never anything to
                  promote, and it is not evidence of anything having been applied
      applied   - the ruling changed the text and the change is in the corpus
      pending   - the ruling changes the text and the corpus does not have it yet;
                  this, and only this, is the promote-to-corpus backlog
      drifted   - the word is neither the one ruled on nor the one chosen: a later
                  apply shifted this klal and nothing re-pointed the decision
      unplaced  - word_index is outside the klal entirely
      unknown   - no original word was snapshotted (witness_choice), so there is
                  nothing to compare against

    FIXED 2026-09-01, same day, on the reviewer's question "so green words are
    applied but not rebuilt? why?". They were not applied. This function had one
    `applied` bucket meaning nothing more than `corpus == chosen_text`, which is
    TRIVIALLY TRUE for a ruling that keeps the stored reading - and that is the
    commonest decision in this corpus. It reported 27 of the 54 drawn-green words
    as applied when the real figure was 1; 46 of them were confirmations with
    nothing to apply. A status that cannot separate "confirmed, nothing to do"
    from "changed and promoted" answers the reviewer's actual question wrongly.

    `applied_ids` is review_decisions.applied_decision_ids(), and it OUTRANKS the
    text comparison. Deleting one of two identical adjacent words leaves its twin
    standing at the deleted one's index, so the corpus reads exactly as it did
    before and the inference says `pending` for a deletion that landed - klal 68
    w29 (a duplicated `הניזקין`) is that case, and the duplicate is verifiably
    gone. A recorded apply_event is a positive statement; text equality is an
    inference a duplicate defeats. Whether an apply_event's claim is still TRUE
    is audit_applied_decisions.py's job, not this display's.
    """
    if not (0 <= word_index < len(words)):
        return "unplaced"
    original = _decision_original_word(rec)
    chosen = rec.get("chosen_text")
    if original is None:
        return "unknown"
    if chosen is not None and chosen == original:
        return "confirmed"
    if rec.get("id") in applied_ids:
        return "applied"
    current = words[word_index]
    if chosen is not None and current == chosen:
        return "applied"
    if current == original:
        return "pending"
    return "drifted"


def api_corpus():
    """What work is loaded - so the dashboard can name the book it is showing.

    ADDED 2026-09-01 (reviewer: "on index pane header should show book title
    also scan pane"). Served rather than hardcoded in review_frontend/: the
    project's goal is to generalize past one text, and a title baked into
    index.html is one more place a second book would have to be edited. The
    values live in corpus_io, with every other fact about the corpus.
    """
    return {
        "title": cio.WORK_TITLE,
        "title_he": cio.WORK_TITLE_HE,
        "section": cio.WORK_SECTION,
        "section_he": cio.WORK_SECTION_HE,
        "edition": cio.WORK_EDITION,
    }


def api_word_states(part_num=1):
    """Every word the legend counts, enumerated - one list per legend row.

    ADDED 2026-09-01 (reviewer: "clicking on a flag count at the bottom of the
    index panel should pop up a list of those flags as clickable links"). The
    legend has shown four totals since it was built and there was no way to get
    from a total to the words in it; a reviewer who wanted to work through the
    518 open disputes had to open klalim one at a time looking for red.

    The lists come from the SAME pass as the counts (api_klalim's
    `on_klal_states` callback), not a second traversal, so a list can never
    disagree with the number above it. `machine_disputed`/`machine_resolved`/
    `decided` partition the words; `ai_flag` is an OVERLAY on them, exactly as
    it is in the legend - an open word-level flag renders its word disputed, so
    every ai_flag entry also appears in `machine_disputed`. That is not double
    counting, it is what the four legend rows have always meant.

    `word` is null where the index has no stored word: a `possible_omission`
    sits at len(words) by construction (text the scan has and the corpus does
    not), and that is the point of it.
    """
    buckets = {rcount.DISPUTED: [], rcount.RESOLVED: [], rcount.DECIDED: []}
    ai_flags = []
    recorded = []
    # Read ONCE, outside the callback. rd.all_current() re-reads and re-parses
    # the whole append-only log on every call, and this callback fires 222 times
    # - the same shape as the per-entry current_for() that merge_decision()'s
    # docstring records having to undo.
    decided = rd.all_current("candidate_choice")
    # Read once, like `decided` above - applied_decision_ids() walks the whole
    # append-only log, and the callback below fires 222 times.
    applied_ids = rd.applied_decision_ids()

    def collect(ctx):
        k, words = ctx["klal"], ctx["words"]
        kid = k["klal_id"]
        gem = k.get("gematria", "")

        def row(wi):
            return {
                "klal_id": kid,
                "word_index": wi,
                "word": words[wi] if 0 <= wi < len(words) else None,
                "gematria": gem,
            }

        state_rows = rcount.state_rows(kid, states=ctx["states"],
                                       entries=ctx["entries"], decided=decided)
        for wi, state in state_rows:
            buckets[state].append(row(wi))
        # From state_rows, NOT from ctx["states"]: a `delete`-opcode entry has no
        # slot in that dict (two deletes can share one index) and is carried
        # alongside it, so asking the dict alone reported 39 rendered against a
        # legend showing 51 - a third number on a screen that already has two.
        decided_indices = {wi for wi, state in state_rows if state == rcount.DECIDED}
        for wi in sorted(ctx["ai_flag_indices"]):
            ai_flags.append(row(wi))

        for wi, rec in sorted(ctx["recorded"].items()):
            item = row(wi)
            item.update({
                "decision_type": rec.get("decision_type"),
                "chosen_text": rec.get("chosen_text"),
                "chosen_source": rec.get("chosen_source"),
                "note": rec.get("note"),
                "ts": rec.get("ts"),
                "decision_id": rec.get("id"),
                "reviewer": rec.get("reviewer"),
                "by_human": _ruled_by_human(rec),
                "original_word": _decision_original_word(rec),
                "status": _decision_status(rec, words, wi, applied_ids),
                "index_stale": _decision_index_is_stale(rec, words, wi),
                "rendered": wi in decided_indices,
            })
            recorded.append(item)

    api_klalim(part_num=part_num, on_klal_states=collect)
    return {
        "part": str(part_num),
        "machine_disputed": buckets[rcount.DISPUTED],
        "machine_resolved": buckets[rcount.RESOLVED],
        "decided": buckets[rcount.DECIDED],
        "ai_flag": ai_flags,
        "recorded": recorded,
    }


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
    words = cio.words_of(k)
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
        # How many leading body words the printed HEADING occupies. The heading
        # is not separate text in the book - it IS the klal's opening, set in
        # larger type - so the UI renders it by styling a prefix of the body
        # rather than by showing `title` as a second copy above it. Computed in
        # corpus_io so the audit tool and the UI cannot drift apart.
        "title_word_count": cio.title_word_span(k.get("title", ""), k.get("clean_text", "")),
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
        words = cio.words_of(k)
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
    # A `delete`-opcode entry is a GAP - text the scan has and the corpus lacks,
    # addressed by the index it would be inserted BEFORE - so it does NOT serve
    # the word standing at that index, and must not suppress it here. FIXED
    # 2026-09-03 (reviewer: "clicking on Klal 17 (יז) · Word #308 — בסתם
    # highlights the wrong word"): the omission at klal 17 w308 claimed the key,
    # the word itself was never emitted, and the scan boxed the omission's ink at
    # x=0.86 while the word sits at x=0.62. The two share an index and are
    # different objects; both need serving, and app.js tells them apart by
    # opcode when it decides which one a click focused.
    served_keys = {(x["klal_id"], x["word_index"]) for x in out
                   if "word_index" in x and x.get("opcode") != "delete"}
    for kid in page_klals:
        k = klalim_by_id.get(kid)
        if not k:
            continue
        words = cio.words_of(k)
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
        candidate_snapshot=_manual_snapshot(klal_id, word_index, body.get("original_word")),
        note=body.get("note"),
    )
    return record


def _manual_snapshot(klal_id, word_index, original_word):
    """What a manual_correction records about the word it is ruling on.

    THE SCAN POSITION IS PART OF IT, since 2026-09-02. It used to be
    `{word_index, original_word}` and nothing else, which made a manual ruling
    unrecoverable the moment a later apply shifted this klal's indices: with no
    bbox there is no way to ask the INK where the word went, only to search the
    text for it, and a unique text match is not evidence of position (measured
    and rejected - see MAX_EXPLAINABLE_SHIFT in audit_applied_decisions.py).

    Measured on the day this was added: of 105 rulings whose recorded word_index
    no longer described their word, **55 were manual_corrections** - and every
    one of those was unrecoverable from the ink for exactly this reason, while 40
    of the 50 that DID carry a bbox could be re-pointed with two independent
    signals agreeing. This does not repair the 55; it stops the next 55.

    The geometry is not new work: `_word_scan_position()` already computes it on
    every render so the scan pane can highlight the word. Best-effort - a word
    the DocAI alignment never matched has no bbox, and a snapshot without one is
    still better than no snapshot.
    """
    snapshot = {"word_index": word_index, "original_word": original_word}
    try:
        part_num = _get_part_num_for_klal(klal_id)
        klalim_by_id, _ = _load_klalim(part_num=part_num)
        klal = klalim_by_id.get(klal_id)
        if klal is not None:
            bbox, page = _word_scan_position(klal_id, cio.words_of(klal), word_index)
            if bbox is not None:
                snapshot["bbox"] = bbox
                snapshot["page"] = page
            else:
                # Not an error: 1-4% of words in a klal have no aligned DocAI
                # token (an OCR gap), and word_scan_position documents returning
                # (None, None) there. Recorded so a later recovery pass can tell
                # "never had one" from "lost it".
                snapshot["bbox_unavailable"] = "no aligned DocAI token"
    except Exception as e:  # noqa: BLE001
        # A snapshot is an audit record, not a precondition: never let a geometry
        # lookup stop a reviewer's ruling from being written down. But SAY SO -
        # a bare `pass` here would be the same silent-failure shape that made a
        # missing /api/corpus render as a blank space (item 0AL), and the whole
        # point of this snapshot is that somebody can rely on it later.
        print(f"  WARNING: no scan position recorded for klal {klal_id} w{word_index}: "
              f"{type(e).__name__}: {e}")
    return snapshot


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
            if path == "/api/numerals":
                return self._send_json(api_numerals())
            if path == "/api/klalim":
                part_val = query.get("part", ["1"])[0]
                return self._send_json(api_klalim(part_num=part_val))
            if path == "/api/corpus":
                return self._send_json(api_corpus())
            if path == "/api/word-states":
                part_val = query.get("part", ["1"])[0]
                return self._send_json(api_word_states(part_num=part_val))
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
        except BadRequest as e:
            # A malformed query value (today: ?part=<garbage>, see
            # _normalize_part) is the CLIENT's error, not the server's, and it
            # used to be neither - it was silently answered with Part 1.
            # Mirrors do_POST's existing ValueError -> 400 branch.
            self._send_error_json(400, f"bad request: {e}")
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
