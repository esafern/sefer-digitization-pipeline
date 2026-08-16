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
import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

import review_decisions as rd

REPO = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(REPO, "review_frontend")
IMAGES_DIR = os.path.join(REPO, "images", "pdf_pages")
# max(klal_id) in part1.json - this dashboard is Part-1 only, and _load_klalim
# filters klalim_demo_dataset.json (all 667) down with it. Same literal,
# independently written, in build_corrections_dataset.py and
# build_klal_page_regions.py; deliberately NOT derived at request time (that
# would mean reading part1.json on every single HTTP request on top of the
# demo dataset this server already re-reads per request, by design). The drift
# risk of three copies is covered instead by
# tests/test_corpus_invariants.py::test_part1_max_klal_constants_agree_with_
# the_corpus, which asserts all three equal max(klal_id) in part1.json.
PART1_MAX_KLAL = 222

FLAG_LABELS = {
    "current_text_may_be_wrong": ["Disputed", "#e53e3e"],
    "possible_omission": ["Possibly missing", "#805ad5"],
    "current_text_confirmed": ["Machine-Resolved", "#38a169"],
    "unverified_insertion": ["Unverified addition", "#a0aec0"],
    "ambiguous": ["Ambiguous", "#dd6b20"],
    "error": ["Check failed", "#718096"],
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
}

MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".png": "image/png",
    ".json": "application/json; charset=utf-8",
}


# ---------- data loading (fresh off disk every call, deliberately no cache) ----------

def _load_json(name, default=None):
    path = os.path.join(REPO, name)
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _load_klalim():
    demo = _load_json("klalim_demo_dataset.json", [])
    klalim = [k for k in demo if k["klal_id"] <= PART1_MAX_KLAL]
    klalim.sort(key=lambda k: k["klal_id"])
    return {k["klal_id"]: k for k in klalim}, klalim


def _load_alignment():
    align = _load_json("part1_header_anchored_alignment.json", [])
    return {r["klal_id"]: r for r in align}


def _load_corrections():
    return _load_json("corrections_part1.json", {})


def _load_regions():
    return _load_json("klal_page_regions.json", {})


def _load_punctuation_candidates():
    return _load_json("punctuation_candidates_part1.json", {})


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
    return items


def _trusted_page(alignment, klal_id):
    r = alignment.get(klal_id, {})
    return r.get("matched_page") if r.get("trusted") else None


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


def api_klalim():
    klalim_by_id, klalim = _load_klalim()
    alignment = _load_alignment()
    corrections = _load_corrections()
    punct_candidates = _load_punctuation_candidates()
    flagged = set(rd.flagged_klalim())
    decided = rd.all_current("candidate_choice")  # {(klal_id, word_index): record}
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
    manual_decided = rd.all_current("manual_correction")  # {(klal_id, word_index): record}
    manual_count_by_klal = {}
    for (kid, wi), rec in manual_decided.items():
        k = klalim_by_id.get(kid)
        if not k:
            continue
        words = (k.get("clean_text") or "").split(" ")
        original_word = rec.get("candidate_snapshot", {}).get("original_word")
        if not _word_matches(words, wi, original_word):
            continue
        manual_count_by_klal[kid] = manual_count_by_klal.get(kid, 0) + 1

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
        corr_decided_count = sum(1 for c in entries if (kid, c["word_index"]) in decided)
        # Tri-state split for the legend's corpus-wide counts: a human
        # decision always wins (see wordState() in app.js), otherwise
        # 'current_text_confirmed' means the vision pass resolved it,
        # otherwise it's still an open dispute nobody has looked at.
        machine_resolved_count = sum(
            1 for c in entries
            if (kid, c["word_index"]) not in decided and c.get("flag") == "current_text_confirmed"
        )
        corr_machine_disputed_count = len(entries) - corr_decided_count - machine_resolved_count

        w_entries = witness_by_klal.get(kid, [])
        w_decided_count = sum(
            1 for w in w_entries if (kid, w["docai_token_index"]) in witness_decided
        )
        w_machine_disputed_count = len(w_entries) - w_decided_count

        manual_count = manual_count_by_klal.get(kid, 0)
        total_count = len(entries) + len(w_entries) + manual_count
        decided_count = corr_decided_count + w_decided_count + manual_count
        machine_disputed_count = corr_machine_disputed_count + w_machine_disputed_count

        punct_entries = punct_candidates.get(str(kid), [])
        punct_decided_count = sum(
            1 for p in punct_entries if (kid, p["before_word_index"]) in punct_decided
        )
        out.append({
            "klal_id": kid,
            "title": k.get("title", ""),
            "section": k.get("section", ""),
            "page": _trusted_page(alignment, kid),
            "page_trusted": kid in alignment and bool(alignment[kid].get("trusted")),
            "correction_count": total_count,
            # split so the nav badge can distinguish "still needs a look"
            # from "already decided" instead of one undifferentiated count
            # (2026-08-07, PROJECT-STATUS.md "review dashboard feedback").
            "decided_count": decided_count,
            "open_count": total_count - decided_count,
            "machine_disputed_count": machine_disputed_count,
            "machine_resolved_count": machine_resolved_count,
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
    klalim_by_id, _ = _load_klalim()
    k = klalim_by_id.get(klal_id)
    if not k:
        return None
    alignment = _load_alignment()
    corrections = _load_corrections().get(str(klal_id), [])
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
    for (kid, word_index), rec in rd.all_current("manual_correction").items():
        if kid != klal_id:
            continue
        original_word = rec.get("candidate_snapshot", {}).get("original_word")
        if not _word_matches(words, word_index, original_word):
            continue
        corrections.append({
            "word_index": word_index,
            "opcode": "manual",
            "docai_reading": None,
            "final_text": rec.get("candidate_snapshot", {}).get("original_word"),
            "page": None,
            "bbox": None,
            "vision_selected": None,
            "vision_transcription": None,
            "confidence": None,
            "reasoning": None,
            "flag": "manual_correction",
            "current_decision": rec,
        })
    regions = _load_regions()
    region_entry = regions.get(str(klal_id), {})
    flag_state = rd.current_for(klal_id, decision_type="klal_flag")

    punct_candidates = _load_punctuation_candidates().get(str(klal_id), [])
    punctuation = []
    for p in punct_candidates:
        idx = p["before_word_index"]
        decision = rd.current_for(klal_id, idx, "punctuation_choice")
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
        "page": _trusted_page(alignment, klal_id),
        "page_trusted": klal_id in alignment and bool(alignment[klal_id].get("trusted")),
        "region": region_entry.get("bbox"),
        # klal's content continues onto one or more later pages (e.g. klal 4:
        # starts on page 15's last line, most of its text is on page 16) -
        # a per-page bbox for each, so the scan-pane highlight can follow
        # the klal when the reviewer manually flips pages.
        "continuations": region_entry.get("continuations", []),
        "corrections": corrections,
        "punctuation": punctuation,
        "needs_revisit": bool(flag_state and flag_state.get("needs_revisit")),
        "flag_note": flag_state.get("note") if flag_state else None,
    }


def api_klal_flag(klal_id):
    current = rd.current_for(klal_id, decision_type="klal_flag")
    history = rd.history_for(klal_id, decision_type="klal_flag")
    return {
        "needs_revisit": bool(current and current.get("needs_revisit")),
        "note": current.get("note") if current else None,
        "history": history,
    }


def api_decision_history(klal_id, word_index):
    # Two decision types can share a (klal_id, word_index) key -
    # candidate_choice (machine-flagged) and manual_correction
    # (2026-08-13, reviewer-flagged) - merge both so the frontend's one
    # generic history panel works for either without needing to know which
    # kind of word it's looking at. In practice a given word_index only
    # ever has one or the other (a manual flag is only offered on a word
    # with no machine candidate - see review_frontend/app.js's
    # renderKlalBody), but merging costs nothing and doesn't assume that.
    history = rd.history_for(klal_id, word_index, "candidate_choice") + \
        rd.history_for(klal_id, word_index, "manual_correction")
    history.sort(key=lambda r: r["ts"])
    return history


def api_page(page_num):
    _, klalim = _load_klalim()
    alignment = _load_alignment()
    corrections = _load_corrections()
    decided = rd.all_current("candidate_choice")
    out = []
    for k in klalim:
        kid = k["klal_id"]
        if _trusted_page(alignment, kid) != page_num:
            continue
        for c in corrections.get(str(kid), []):
            if not c.get("bbox"):
                continue
            entry = _merge_decision(c, kid, decided)
            entry["klal_id"] = kid
            entry["kind"] = "correction"
            out.append(entry)

    # Witness disagreements for this page. Keyed by docai_token_index, a
    # different index space from corrections' word_index - safe because
    # current_for() filters on decision_type, so the two never collide.
    for w in _load_witness_queue():
        if w.get("page") != page_num or not w.get("bbox"):
            continue
        entry = dict(w)
        entry["kind"] = "witness"
        entry["current_decision"] = rd.current_for(
            w["klal_id"], w["docai_token_index"], "witness_choice")
        out.append(entry)
    return out


def api_post_candidate_decision(body):
    klal_id = int(body["klal_id"])
    word_index = int(body["word_index"])
    corrections = _load_corrections().get(str(klal_id), [])
    snapshot = next((c for c in corrections if c["word_index"] == word_index), None)
    record = rd.append_decision(
        "candidate_choice",
        klal_id=klal_id,
        word_index=word_index,
        chosen_source=body.get("chosen_source"),
        chosen_text=body.get("chosen_text"),
        candidate_snapshot=snapshot,
        note=body.get("note"),
    )
    return record


def api_post_punctuation_decision(body):
    klal_id = int(body["klal_id"])
    word_index = int(body["before_word_index"])
    accepted = bool(body["accepted"])
    candidates = _load_punctuation_candidates().get(str(klal_id), [])
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
WITNESS_HEB = "אבגדהוזחטיכלמנסעפצקרשתךםןףץ"


def _witness_norm(s):
    return "".join(c for c in s if c in WITNESS_HEB)


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
    tokens = _load_json(f"docai_word_boxes/page_{page}.json")
    if not tokens:
        return {"words": [], "target_index": None}
    dtoks = [t for t in tokens if _witness_norm(t["text"])]
    if token_index >= len(dtoks):
        return {"words": [], "target_index": None}
    lo = max(0, token_index - WITNESS_CONTEXT_WINDOW)
    hi = min(len(dtoks), token_index + WITNESS_CONTEXT_WINDOW + 1)
    return {"words": [t["text"] for t in dtoks[lo:hi]], "target_index": token_index - lo}


def api_post_klal_flag(body):
    klal_id = int(body["klal_id"])
    record = rd.append_decision(
        "klal_flag",
        klal_id=klal_id,
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
ROUTE_KLAL_FLAG = re.compile(r"^/api/klal/(\d+)/flag$")
ROUTE_DECISIONS = re.compile(r"^/api/decisions/(\d+)/(\d+)$")
ROUTE_PAGE = re.compile(r"^/api/page/(\d+)$")
ROUTE_WITNESS_CONTEXT = re.compile(r"^/api/witness/context/(\d+)/(\d+)$")


class Handler(BaseHTTPRequestHandler):
    server_version = "YadMalachiReview/1.0"

    def log_message(self, fmt, *args):
        pass  # keep stdout clean; errors still raise/print via BaseHTTPRequestHandler's default hooks

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
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        try:
            if path == "/api/flags":
                return self._send_json(api_flags())
            if path == "/api/witness":
                return self._send_json(api_witness_summary())
            if path == "/api/klalim":
                return self._send_json(api_klalim())
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

            if path == "/api/decisions/candidate":
                return self._send_json(api_post_candidate_decision(body), status=201)
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8420)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Yad Malachi review server: http://{args.host}:{args.port}/")
    print(f"Decisions log: {rd.DECISIONS_PATH}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.shutdown()


if __name__ == "__main__":
    main()
