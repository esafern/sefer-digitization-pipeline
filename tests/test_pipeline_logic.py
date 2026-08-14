"""[PRODUCTION] Unit-level regression suite for the main pipeline's decision
logic - the pure functions that decide what a reviewer is shown, what gets
written into part1.json, and what a cache is allowed to reuse.

Complementary to tests/test_corpus_invariants.py, which checks the DATA a
finished pipeline run produced. This file checks the LOGIC that produces it,
on synthetic inputs, so a regression fails here even when today's real corpus
happens not to exercise the broken path. That distinction is not academic:
several of the functions covered here (assemble_corrections_dataset.
check_drift, review_server's stale_candidate label, apply_reviewer_decisions'
re-apply guard) are currently inert on real data - 0 drifted candidates, 0
stale flags - and were each fixed AFTER an incident in which they silently did
the wrong thing. A test that only looks at current data cannot see any of
them (CLAUDE.md Lesson 1: a check that isn't run on the case that matters has
verified nothing).

Every test here is zero-tolerance and hermetic: no network, no API key, no
scan cache, no writes to any tracked file (temp dirs/files only, via
review_decisions.py's own `path=` parameter). Fast enough to run in
rebuild_all.sh's gate alongside the corpus suite, which is where it runs.
"""
import json
import os
import sqlite3
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

import apply_reviewer_decisions as ard  # noqa: E402
import assemble_corrections_dataset as acd  # noqa: E402
import audit_applied_decisions as aad  # noqa: E402
import build_klal_page_regions as bkpr  # noqa: E402
import check_klal_token_orphans as ckto  # noqa: E402
import review_decisions as rd  # noqa: E402
import review_server as rs  # noqa: E402
import validate_catchword_continuity as vcc  # noqa: E402
import validate_part1_corpus_integrity as vpci  # noqa: E402
import validate_title_alphabetical_order as vtao  # noqa: E402


# --- assemble_corrections_dataset: candidate drift detection -----------------
# Added 2026-08-14 after the reindexing incident (PROJECT-STATUS.md): a
# candidate is generated against a snapshot of part1.json, and if the corpus
# moves under it, its word_index/corrected_word start describing a different
# word than the one the reviewer is looking at. Currently 0 candidates drift,
# so nothing on real data exercises any of this.

def test_check_drift_accepts_a_candidate_still_matching_live_text():
    words = "אלף בית גימל דלת".split()
    c = {"opcode": "replace", "word_index_in_final_text": 2, "corrected_word": "גימל"}
    assert acd.check_drift(c, words) is False


def test_check_drift_flags_a_replace_candidate_whose_word_changed():
    words = "אלף בית גימל דלת".split()
    c = {"opcode": "replace", "word_index_in_final_text": 2, "corrected_word": "הא"}
    assert acd.check_drift(c, words) is True


def test_check_drift_flags_a_candidate_whose_index_shifted():
    """The exact shape of the 2026-08-13 reindexing incident: the candidate's
    own word is still in the klal, one position off from where it points."""
    c = {"opcode": "replace", "word_index_in_final_text": 2, "corrected_word": "גימל"}
    assert acd.check_drift(c, "אלף חדש בית גימל דלת".split()) is True


def test_check_drift_handles_multi_word_spans_on_both_sides():
    words = "אלף בית גימל דלת".split()
    ok = {"opcode": "replace", "word_index_in_final_text": 1, "corrected_word": "בית גימל"}
    moved = {"opcode": "replace", "word_index_in_final_text": 1, "corrected_word": "גימל דלת"}
    assert acd.check_drift(ok, words) is False
    assert acd.check_drift(moved, words) is True


def test_check_drift_flags_out_of_range_and_negative_indices():
    words = "אלף בית".split()
    past_end = {"opcode": "replace", "word_index_in_final_text": 5, "corrected_word": "אלף"}
    span_past_end = {"opcode": "insert", "word_index_in_final_text": 1, "corrected_word": "בית גימל"}
    negative = {"opcode": "replace", "word_index_in_final_text": -1, "corrected_word": "בית"}
    assert acd.check_drift(past_end, words) is True
    assert acd.check_drift(span_past_end, words) is True
    # A negative index would otherwise read backwards from the end in Python
    # and could "match" the klal's last word - the same forgiving-indexing
    # trap fixed in audit_applied_decisions.py's checkers.
    assert acd.check_drift(negative, words) is True


def test_check_drift_bounds_checks_delete_candidates_only():
    """A delete candidate's corrected_word is null by definition (the corpus
    has no text there), so there is nothing at word_index to compare - but
    its append position may legitimately be one past the last word."""
    words = "אלף בית".split()
    at_end = {"opcode": "delete", "word_index_in_final_text": 2, "corrected_word": None}
    past_end = {"opcode": "delete", "word_index_in_final_text": 3, "corrected_word": None}
    negative = {"opcode": "delete", "word_index_in_final_text": -1, "corrected_word": None}
    assert acd.check_drift(at_end, words) is False
    assert acd.check_drift(past_end, words) is True
    assert acd.check_drift(negative, words) is True


def test_check_drift_flags_a_candidate_for_a_klal_that_no_longer_exists():
    c = {"opcode": "replace", "word_index_in_final_text": 0, "corrected_word": "אלף"}
    assert acd.check_drift(c, None) is True


def test_classify_requires_confidence_before_trusting_a_vision_selection():
    """FIXED 2026-08-13 (PROJECT-STATUS.md finding 8): 'replace' used to trust
    an A/B selection at ANY confidence while 'delete' gated at 0.7. Inert on
    current data (every live replace candidate scores >= 0.7), so only a test
    like this keeps the asymmetry from coming back."""
    def replace(sel, conf):
        return acd.classify({"opcode": "replace", "vision_selected": sel, "vision_confidence": conf})

    assert replace("A", 0.9) == "current_text_may_be_wrong"
    assert replace("B", 0.9) == "current_text_confirmed"
    assert replace("A", 0.5) == "ambiguous"
    assert replace("B", 0.5) == "ambiguous"
    assert replace("A", None) == "ambiguous"
    assert replace("UNCERTAIN", 0.99) == "ambiguous"
    assert replace(None, 0.99) == "error"

    def delete(sel, conf):
        return acd.classify({"opcode": "delete", "vision_selected": sel, "vision_confidence": conf})

    assert delete("A", 0.9) == "possible_omission"
    assert delete("A", 0.5) == "ambiguous"
    assert delete("ERROR", None) == "error"


def test_every_flag_classify_or_check_drift_can_produce_has_a_dashboard_label():
    """review_frontend/app.js renders `FLAGS[corr.flag] || ['Flagged']`, so a
    flag with no review_server.FLAG_LABELS entry is displayed as an
    indistinguishable generic "Flagged" - silently, and exactly when the
    reviewer most needs to know what the machine concluded. That is not
    hypothetical: "stale_candidate" shipped without a label and was caught in
    code review, not by any check (PROJECT-STATUS.md 2026-08-14). Enumerated
    by exercising classify() over its whole input grid rather than by reading
    the source, so a NEW flag string added to it also has to be labelled.
    """
    produced = {"stale_candidate"}  # forced by check_drift, never by classify
    for opcode in ("replace", "insert", "delete", "something_unexpected"):
        for selected in ("A", "B", "UNCERTAIN", "ERROR", None):
            for confidence in (None, 0.0, 0.5, 0.7, 1.0):
                produced.add(acd.classify({
                    "opcode": opcode,
                    "vision_selected": selected,
                    "vision_confidence": confidence,
                }))
    unlabelled = sorted(produced - set(rs.FLAG_LABELS))
    assert not unlabelled, (
        f"flag(s) {unlabelled} can be produced by assemble_corrections_dataset.py but have no "
        f"review_server.FLAG_LABELS entry - the dashboard would render them as a generic "
        f"'Flagged' word with no colour or meaning. Add a label (and restart review_server.py, "
        f"which does not hot-reload Python constants)."
    )


def test_flag_labels_are_well_formed_label_and_colour_pairs():
    for flag, value in rs.FLAG_LABELS.items():
        assert isinstance(value, list) and len(value) == 2, f"FLAG_LABELS[{flag!r}] must be [label, colour]"
        label, colour = value
        assert label and isinstance(label, str), f"FLAG_LABELS[{flag!r}] has an empty label"
        assert isinstance(colour, str) and colour.startswith("#") and len(colour) == 7, (
            f"FLAG_LABELS[{flag!r}] colour {colour!r} is not a #rrggbb string - app.js uses it "
            "directly as a CSS colour, so a malformed value renders as no colour at all"
        )


# --- apply_reviewer_decisions: the only code that mutates part1.json ---------

def test_apply_replace_rewrites_only_the_snapshotted_span():
    text = "אלף בית גימל דלת"
    assert ard.apply_replace(text, 1, "בית", "בות") == "אלף בות גימל דלת"
    assert ard.apply_replace(text, 1, "בית גימל", "בות") == "אלף בות דלת"


def test_apply_replace_refuses_when_live_text_no_longer_matches_the_snapshot():
    """Second, independent drift guard behind snapshot_matches() (Lesson 9) -
    it compares against the corpus itself, not against the candidate file."""
    assert ard.apply_replace("אלף בית גימל", 1, "דלת", "הא") is None
    assert ard.apply_replace("אלף בית גימל", 0, "בית", "הא") is None


def test_apply_delete_insertion_never_duplicates_an_already_applied_insertion():
    """Reproduced 2026-08-11: three runs of this script produced
    `יגעתי 1 1 1 ולא`, each reporting success, because inserting text has no
    span to verify against the way replace does."""
    text = "יגעתי ולא מצאתי"
    once = ard.apply_delete_insertion(text, 1, "1")
    assert once == "יגעתי 1 ולא מצאתי"
    assert ard.apply_delete_insertion(once, 1, "1") is None


def test_apply_delete_insertion_allows_appending_past_the_last_word():
    text = "אלף בית"
    assert ard.apply_delete_insertion(text, 2, "גימל") == "אלף בית גימל"
    assert ard.apply_delete_insertion(text, 3, "גימל") is None
    assert ard.apply_delete_insertion(text, 1, "") is None


def test_apply_insert_removal_deletes_the_span_or_refuses():
    assert ard.apply_insert_removal("אלף בית גימל", 1, "בית") == "אלף גימל"
    assert ard.apply_insert_removal("אלף בית גימל", 1, "בית גימל") == "אלף"
    assert ard.apply_insert_removal("אלף בית גימל", 1, "דלת") is None
    assert ard.apply_insert_removal("אלף בית גימל", 1, None) is None


def test_apply_manual_correction_and_deletion_drift_check_the_original_word():
    text = "אלף בית גימל"
    assert ard.apply_manual_correction(text, 1, "בית", "בות") == "אלף בות גימל"
    assert ard.apply_manual_correction(text, 1, "דלת", "בות") is None
    assert ard.apply_manual_correction(text, 9, "בית", "בות") is None
    assert ard.apply_manual_deletion(text, 1, "בית") == "אלף גימל"
    assert ard.apply_manual_deletion(text, 1, "דלת") is None


def test_snapshot_matches_compares_every_field_that_identifies_a_candidate():
    live = {"opcode": "replace", "docai_reading": "אלף", "final_text": "בית",
            "word_index": 3, "flag": "current_text_may_be_wrong"}
    assert ard.snapshot_matches(dict(live), live) is True
    # A differing flag alone is not drift - the vision pass legitimately
    # re-classifies a candidate on every rebuild without moving it.
    assert ard.snapshot_matches({**live, "flag": "ambiguous"}, live) is True
    for field in ("opcode", "docai_reading", "final_text", "word_index"):
        assert ard.snapshot_matches({**live, field: "CHANGED"}, live) is False, (
            f"a changed {field} must count as drift - applying past it would edit the wrong word"
        )
    assert ard.snapshot_matches(None, live) is False
    assert ard.snapshot_matches(live, None) is False


# --- review_decisions: the append-only human-decision audit trail ------------

@pytest.fixture
def decisions_path(tmp_path):
    return str(tmp_path / "decisions.jsonl")


def test_decisions_log_is_append_only_and_resolves_latest_per_key(decisions_path):
    first = rd.append_decision("candidate_choice", klal_id=1, word_index=5,
                               chosen_source="docai_reading", chosen_text="אלף", path=decisions_path)
    second = rd.append_decision("candidate_choice", klal_id=1, word_index=5,
                                chosen_source="custom", chosen_text="בית", path=decisions_path)
    other = rd.append_decision("candidate_choice", klal_id=1, word_index=6,
                               chosen_text="גימל", path=decisions_path)

    with open(decisions_path, encoding="utf-8") as f:
        lines = [json.loads(l) for l in f if l.strip()]
    assert [l["id"] for l in lines] == [first["id"], second["id"], other["id"]], (
        "recording a decision must only ever APPEND - the earlier decision at the same key "
        "must still be on disk verbatim (this file is the only record a rebuild cannot clobber)"
    )
    assert rd.current_for(1, 5, "candidate_choice", path=decisions_path)["id"] == second["id"]
    assert [r["id"] for r in rd.history_for(1, 5, "candidate_choice", path=decisions_path)] == \
        [first["id"], second["id"]]
    assert set(rd.all_current("candidate_choice", path=decisions_path)) == {(1, 5), (1, 6)}
    assert rd.find_by_id(first["id"], path=decisions_path)["chosen_text"] == "אלף"


def test_decision_types_are_validated_before_anything_is_written(decisions_path):
    with pytest.raises(ValueError):
        rd.append_decision("not_a_real_type", klal_id=1, path=decisions_path)
    assert not os.path.exists(decisions_path), "a rejected decision must not create/append to the log"


def test_klal_flag_and_applied_ids_resolve_independently_of_word_index(decisions_path):
    rd.append_decision("klal_flag", klal_id=7, needs_revisit=True, note="look again", path=decisions_path)
    rd.append_decision("klal_flag", klal_id=8, needs_revisit=True, path=decisions_path)
    rd.append_decision("klal_flag", klal_id=8, needs_revisit=False, path=decisions_path)
    assert rd.flagged_klalim(path=decisions_path) == [7], (
        "a klal un-flagged by a later decision must drop out of the flagged set"
    )

    decision = rd.append_decision("candidate_choice", klal_id=7, word_index=1,
                                  chosen_text="אלף", path=decisions_path)
    assert rd.applied_decision_ids(path=decisions_path) == set()
    rd.append_decision("apply_event", klal_id=7, word_index=1,
                       applied_decision_id=decision["id"], path=decisions_path)
    assert rd.applied_decision_ids(path=decisions_path) == {decision["id"]}


# --- audit_applied_decisions: the check on "applied" claims staying true -----

def _klal(text):
    return {"klal_id": 1, "clean_text": text}


def test_check_candidate_choice_verifies_the_chosen_text_is_still_in_place():
    d = {"candidate_snapshot": {"opcode": "replace"}, "chosen_text": "בות", "word_index": 1}
    assert aad.check_candidate_choice(d, _klal("אלף בות גימל")) == "ok"
    assert aad.check_candidate_choice(d, _klal("אלף בית גימל")).startswith("MISMATCH")


def test_check_candidate_choice_reports_out_of_range_indices_rather_than_silently_passing():
    """Python's forgiving slicing returns [] for an out-of-range span, so
    without an explicit bounds check an empty/short expectation compares
    [] == [] and reports a confident "ok" having verified nothing (fixed
    2026-08-14, code review finding 10)."""
    high = {"candidate_snapshot": {"opcode": "replace"}, "chosen_text": "בות", "word_index": 99}
    low = {"candidate_snapshot": {"opcode": "replace"}, "chosen_text": "בות", "word_index": -1}
    assert aad.check_candidate_choice(high, _klal("אלף בית")).startswith("MISMATCH")
    assert aad.check_candidate_choice(low, _klal("אלף בית")).startswith("MISMATCH")
    empty = {"candidate_snapshot": {"opcode": "replace"}, "chosen_text": "", "word_index": 99}
    assert aad.check_candidate_choice(empty, _klal("אלף בית")) == "unverifiable_word_count_change"
    insertion = {"candidate_snapshot": {"opcode": "delete"}, "chosen_text": "בות", "word_index": 0}
    assert aad.check_candidate_choice(insertion, _klal("אלף בית")) == "unverifiable_word_count_change"


def test_check_manual_correction_and_punctuation_bounds_check_both_ends():
    manual = {"chosen_text": "בות", "word_index": 1}
    assert aad.check_manual_correction(manual, _klal("אלף בות גימל")) == "ok"
    assert aad.check_manual_correction(manual, _klal("אלף בית גימל")).startswith("MISMATCH")
    assert aad.check_manual_correction({**manual, "word_index": -1}, _klal("אלף בות")).startswith("MISMATCH")
    assert aad.check_manual_correction({**manual, "word_index": 9}, _klal("אלף בות")).startswith("MISMATCH")
    assert aad.check_manual_correction({"chosen_text": "", "word_index": 1}, _klal("אלף בות")) == \
        "unverifiable_word_count_change"

    accept = {"chosen_source": "accept", "word_index": 1}
    assert aad.check_punctuation_choice(accept, _klal("אלף [.] בית")) == "ok"
    assert aad.check_punctuation_choice(accept, _klal("אלף בית")).startswith("MISMATCH")
    assert aad.check_punctuation_choice({**accept, "word_index": -1}, _klal("אלף [.]")).startswith("MISMATCH")
    assert aad.check_punctuation_choice({"chosen_source": "reject", "word_index": 1},
                                        _klal("אלף בית")) == "unverifiable_word_count_change"


@pytest.fixture
def audit_reads_temp_log(decisions_path, monkeypatch):
    """audit_applied_decisions.py calls rd.history_for() with no `path`, so
    it always reads the real, git-tracked decisions log. Point it at the
    temp one for the duration of a test - binding the ORIGINAL function
    first, since the replacement lives at the same name it would otherwise
    call back into."""
    real_history_for = rd.history_for
    monkeypatch.setattr(aad.rd, "history_for",
                        lambda k, w=None, t=None: real_history_for(k, w, t, path=decisions_path))
    return decisions_path


def test_a_later_decision_only_suppresses_the_check_if_it_was_itself_applied(audit_reads_temp_log):
    """The klal 1 word 97 precedent (PROJECT-STATUS.md 2026-08-14): an applied
    decision superseded at its key by a never-applied one is still the
    standing claim about the corpus and MUST stay checked - the first version
    of this script skipped it and reported "0 mismatches" while structurally
    unable to see its own motivating case. A later decision that WAS applied
    is ordinary supersession and is correctly skipped."""
    decisions_path = audit_reads_temp_log
    applied_first = rd.append_decision("candidate_choice", klal_id=1, word_index=97,
                                       chosen_text="אלף", path=decisions_path)
    never_applied_later = rd.append_decision("candidate_choice", klal_id=1, word_index=97,
                                             chosen_text="בית", path=decisions_path)
    assert aad.is_superseded_by_later_applied(applied_first, {applied_first["id"]}) is False
    assert aad.is_superseded_by_later_applied(
        applied_first, {applied_first["id"], never_applied_later["id"]}) is True
    # The newest decision at a key can never be superseded by anything.
    assert aad.is_superseded_by_later_applied(
        never_applied_later, {applied_first["id"], never_applied_later["id"]}) is False


def test_supersession_does_not_leak_across_keys(audit_reads_temp_log):
    decisions_path = audit_reads_temp_log
    target = rd.append_decision("candidate_choice", klal_id=1, word_index=5,
                                chosen_text="אלף", path=decisions_path)
    elsewhere = rd.append_decision("candidate_choice", klal_id=1, word_index=6,
                                   chosen_text="בית", path=decisions_path)
    other_type = rd.append_decision("manual_correction", klal_id=1, word_index=5,
                                    chosen_text="גימל", path=decisions_path)
    assert aad.is_superseded_by_later_applied(
        target, {target["id"], elsewhere["id"], other_type["id"]}) is False, (
        "only a later decision at the SAME (klal_id, word_index, decision_type) key describes "
        "the same word - anything else must not suppress the check"
    )


# --- build_klal_page_regions: the heuristic fallback path --------------------
# ~22 klalim get their scan-pane box from heuristic_regions() rather than the
# marker-anchored path. It is a content-diff heuristic with no marker to
# anchor on ("good enough for a page-crop box, not word-position accuracy" per
# its own design note), so there is no ground truth to assert against here -
# only internal consistency, which is what a regression would break.

def _tok(text, x1, y1, x2=None, y2=None):
    return {"text": text, "x1": x1, "y1": y1, "x2": x2 if x2 is not None else x1 + 0.05,
            "y2": y2 if y2 is not None else y1 + 0.02}


def _heuristic_fixture():
    docai = {1: [_tok("אלף", 0.10, 0.10), _tok("בית", 0.20, 0.10),
                 _tok("גימל", 0.30, 0.30), _tok("דלת", 0.40, 0.30)]}
    final = {1: {"klal_id": 1, "clean_text": "אלף בית"},
             2: {"klal_id": 2, "clean_text": "גימל דלת"}}
    return {1: [1, 2]}, docai, final


def test_heuristic_regions_gives_each_klal_one_region_bounding_its_own_tokens():
    klal_pages, docai, final = _heuristic_fixture()
    regions = bkpr.heuristic_regions(klal_pages, docai, final, already_done=set())
    assert set(regions) == {1, 2}
    assert regions[1]["page"] == 1 and regions[2]["page"] == 1
    # Each klal's box must cover its own two tokens and nothing of the other's.
    assert regions[1]["bbox"] == pytest.approx({"x1": 0.10, "y1": 0.10, "x2": 0.25, "y2": 0.12})
    assert regions[2]["bbox"] == pytest.approx({"x1": 0.30, "y1": 0.30, "x2": 0.45, "y2": 0.32})
    assert regions[1]["token_count"] == 2 and regions[2]["token_count"] == 2


def test_heuristic_regions_never_overrides_a_marker_anchored_region():
    """The two strategies are merged as {**anchored, **heuristic}, so a
    heuristic region for a klal the marker-anchored path already resolved
    would silently replace the more precise box."""
    klal_pages, docai, final = _heuristic_fixture()
    regions = bkpr.heuristic_regions(klal_pages, docai, final, already_done={1})
    assert set(regions) == {2}


def test_heuristic_regions_skips_pages_and_klalim_it_has_no_data_for():
    klal_pages, docai, final = _heuristic_fixture()
    assert bkpr.heuristic_regions({9: [1, 2]}, docai, final, already_done=set()) == {}
    # A klal_id listed for the page but absent from the corpus contributes no
    # words, so it can never claim tokens belonging to its page-neighbours.
    regions = bkpr.heuristic_regions({1: [1, 2, 3]}, docai, final, already_done=set())
    assert 3 not in regions


def test_heuristic_regions_bbox_always_encloses_every_token_it_counted():
    klal_pages, docai, final = _heuristic_fixture()
    regions = bkpr.heuristic_regions(klal_pages, docai, final, already_done=set())
    for klal_id, region in regions.items():
        b = region["bbox"]
        assert b["x1"] < b["x2"] and b["y1"] < b["y2"], f"klal {klal_id} has a degenerate bbox: {b}"
        assert region["token_count"] >= 1


# --- check_klal_token_orphans: the Pass-3 false-positive allowlist ----------
# Changed 2026-08-14 from a bare {4, 18, 34} klal_id set, which suppressed
# EVERY Pass-3 gap in those klalim, to a (klal_id, normalised span) key. The
# whole point is that a NEW, different gap in the same klal still surfaces -
# a property no amount of running the script against today's data can
# demonstrate, since today's data has exactly the 3 cleared gaps and nothing
# else.

KNOWN_KLAL_4_GAP = 'ואפ"ה חשיב ליה שם בזבחים למד מלמד והניח הדבר בתימה וגדולה היא אלי וצ"ע :'


def test_the_exact_investigated_span_is_still_suppressed():
    assert ckto.is_known_pass3_false_positive(4, KNOWN_KLAL_4_GAP.split()) is True
    # Tokenisation/punctuation differences must not matter - the key is the
    # normalised Hebrew letters, and Pass 3 feeds it raw OCR tokens.
    assert ckto.is_known_pass3_false_positive(4, KNOWN_KLAL_4_GAP.replace(" ", "").split()) is True


def test_a_different_gap_in_an_allowlisted_klal_is_not_suppressed():
    """The regression this guards: reverting to a klal_id-only allowlist
    would silently swallow a genuinely new missing-content finding in klal
    4/18/34 - the same klalim whose spans were cleared for unrelated
    reasons (out-of-reading-order tokens, a citation collision, garbled
    source OCR)."""
    assert ckto.is_known_pass3_false_positive(4, "טקסט חדש לגמרי שלא נבדק מעולם".split()) is False
    assert ckto.is_known_pass3_false_positive(18, KNOWN_KLAL_4_GAP.split()) is False, (
        "a cleared span must be cleared for its OWN klal only"
    )


def test_the_allowlist_is_keyed_on_spans_not_bare_klal_ids():
    for entry in ckto.PASS3_KNOWN_FALSE_POSITIVES:
        assert isinstance(entry, tuple) and len(entry) == 2, (
            f"PASS3_KNOWN_FALSE_POSITIVES entry {entry!r} is not a (klal_id, normalised_span) pair - "
            "a bare klal_id would suppress every future gap in that klal, the exact over-suppression "
            "fixed 2026-08-14"
        )
        klal_id, span = entry
        assert isinstance(klal_id, int) and isinstance(span, str) and span, entry
        assert span == ckto.normalize(span), (
            f"the span for klal {klal_id} is not stored normalised, so it can never match the "
            "normalised span Pass 3 computes - the suppression would be silently dead"
        )


def test_best_match_owner_never_answers_with_the_klal_under_investigation():
    """Fixed 2026-08-14: `self_kid` was accepted and ignored, so klal 34's
    missing text was reported as most likely belonging to... klal 34."""
    part1 = {
        34: {"clean_text": "אלף בית גימל דלת הא"},
        36: {"clean_text": "אלף בית גימל דלת וו"},
    }
    kid, similarity = ckto.best_match_owner("אלף בית גימל דלת הא".split(), part1, self_kid=34)
    assert kid == 36 and similarity > 0


# --- Standalone validators: proof that each check can actually fire ---------
# Three of these are zero-tolerance gates in tests/test_corpus_invariants.py,
# where they currently pass on the whole corpus. CLAUDE.md Lesson 2: a
# passing score is not a checked result - a gate that CANNOT fail is
# indistinguishable from one that passes, and each of these checks has
# already had false-positive sources removed from it, any of which could have
# been over-corrected into blindness.

def test_gematria_check_catches_a_wrong_field_and_a_wrong_opening():
    ok = [{"klal_id": 1, "gematria": "א", "clean_text": "א ראשית הדברים"}]
    assert vpci.check_gematria_self_consistency(ok) == []
    wrong_field = [{"klal_id": 1, "gematria": "ב", "clean_text": "א ראשית הדברים"}]
    assert len(vpci.check_gematria_self_consistency(wrong_field)) == 2
    wrong_opening = [{"klal_id": 1, "gematria": "א", "clean_text": "ראשית הדברים"}]
    assert len(vpci.check_gematria_self_consistency(wrong_opening)) == 1
    # klal 166's print attaches its own closing geresh to the numeral.
    geresh = [{"klal_id": 166, "gematria": "קסו", "clean_text": "קסו' ראשית הדברים"}]
    assert vpci.check_gematria_self_consistency(geresh) == []


def test_character_sanity_catches_latin_digits_and_unbalanced_brackets():
    def issues(text):
        return vpci.check_character_sanity([{"klal_id": 1, "clean_text": text}])

    assert issues("אלף בית גימל") == []
    assert issues("אלף Google בית") != []
    assert issues("אלף 283 בית") != []
    assert issues("אלף (בית גימל") != []
    assert issues("אלף [בית גימל") != []
    # The two footnote-marker conventions this print uses are not brackets.
    assert issues("אלף *) בית") == []
    assert issues('אלף ") בית') == []


def test_character_sanity_does_not_mistake_a_hebrew_abbreviation_for_a_footnote_marker():
    """FOOTNOTE_MARKER_RE's `"` alternative got a lookbehind 2026-08-14: an
    abbreviation's gershayim landing directly before a close paren was
    subtracted as if it were a footnote marker, which can either manufacture
    a false "unbalanced parens" failure or cancel a real one - in a gate
    that is zero-tolerance."""
    balanced = vpci.check_character_sanity([{"klal_id": 1, "clean_text": 'אלף (עיין ז") בית'}])
    assert balanced == [], f"a real close paren after a gershayim must still count: {balanced}"
    unbalanced = vpci.check_character_sanity([{"klal_id": 1, "clean_text": 'אלף עיין ז") בית'}])
    assert unbalanced != [], "an unmatched close paren after a gershayim must still be reported"


def test_duplicate_phrase_checks_fire_and_respect_the_same_title_convention():
    phrase = " ".join(f"מלה{i}" for i in range(12))
    different_titles = [
        {"klal_id": 1, "title": "כותרת ראשונה", "clean_text": f"פתיחה {phrase} סיום"},
        {"klal_id": 2, "title": "נושא אחר לגמרי", "clean_text": f"פתיחה {phrase} סיום"},
    ]
    assert vpci.check_duplicate_phrases(different_titles, n=10) != []
    same_title = [dict(k, title="כותרת זהה") for k in different_titles]
    assert vpci.check_duplicate_phrases(same_title, n=10) == [], (
        "adjacent klalim restating the same maxim under the same title is this book's documented "
        "convention, not a corpus bug"
    )
    within_one = [{"klal_id": 1, "title": "כותרת", "clean_text": f"{phrase} מפריד {phrase}"}]
    assert vpci.check_intra_klal_duplicate_phrases(within_one, n=10) != []
    assert vpci.check_intra_klal_duplicate_phrases(
        [{"klal_id": 1, "title": "כותרת", "clean_text": phrase}], n=10) == []


def test_title_order_check_reports_an_unrankable_first_character_instead_of_skipping_it():
    """Fixed 2026-08-14: a title whose first character isn't a Hebrew letter
    used to be silently dropped - neither validated nor flagged, invisible to
    the whole check (klal 353 is the live instance)."""
    klalim = [
        {"klal_id": 1, "title": "אלף פותח"},
        {"klal_id": 2, "title": "'. בית פותח"},
        {"klal_id": 3, "title": "בית פותח"},
    ]
    violations, skipped = vtao.find_violations(klalim)
    assert [kid for kid, _ in skipped] == [2]
    assert violations == {}


def test_title_order_check_catches_a_letter_run_that_breaks_and_resumes():
    ordered = [{"klal_id": i, "title": t} for i, t in enumerate(
        ["אלף", "אלף", "בית", "בית", "גימל", "גימל"], start=1)]
    assert vtao.find_violations(ordered)[0] == {}
    # One stray Bet-titled klal stranded inside the Alef run. Deliberately
    # shaped so overriding it is the ONLY maximal assignment: with a single
    # klal on each side of the break, two different klalim tie for "the odd
    # one out" and either answer is equally correct.
    stranded = [{"klal_id": i, "title": t} for i, t in enumerate(
        ["אלף", "אלף", "אלף", "בית", "אלף", "אלף", "בית", "בית", "בית"], start=1)]
    assert set(vtao.find_violations(stranded)[0]) == {4}, (
        "a klal whose letter reappears after its run closed is the signature of a broken klal "
        "boundary - the whole reason this check is contiguity-based"
    )


def test_running_header_words_are_only_matched_as_bare_words():
    """Fixed 2026-08-14: HEADER_WORDS matched through clean_word(), so the
    citation י"ד (Yoreh De'ah / a siman number) collapsed onto the running
    header's bare יד and was eaten as page furniture - 43 tokens across the
    scan, one of which changed a reported page boundary."""
    assert vcc.is_header_word("יד") is True
    assert vcc.is_header_word("מלאכי") is True
    assert vcc.is_header_word('י"ד') is False
    assert vcc.is_header_word("י'ד") is False
    assert vcc.is_header_word("כלל") is False, (
        "the bare word כלל ('rule') is real text, not the header token כללי"
    )


# --- verify_corrections_vision: response parsing + cache-key coverage --------

fitz = pytest.importorskip("fitz", reason="PyMuPDF not installed (pipeline dependency)")
pytest.importorskip("google.genai", reason="google-genai not installed (pipeline dependency)")
import verify_corrections_vision as vcv  # noqa: E402


def test_unescape_json_fragment_restores_escaped_quotes_without_touching_raw_ones():
    """A single Gemini response routinely mixes both escaping states: some
    Hebrew gershayim emitted raw (the reason lenient parsing exists) and
    others correctly escaped. Returning a regex capture verbatim baked a
    literal backslash into review data - it had already corrupted 3 committed
    witness-queue entries before the same fix reached this file."""
    assert vcv.unescape_json_fragment(r'\"ה') == '"ה'
    assert vcv.unescape_json_fragment('כ"ה') == 'כ"ה'
    assert vcv.unescape_json_fragment(r'a\\b') == "a\\b"
    assert vcv.unescape_json_fragment(r"line\nbreak") == "line\nbreak"


def test_extract_json_fields_recovers_a_response_with_unescaped_gershayim():
    text = '''{
      "selected_option": "A",
      "transcription_found": "סי' כ"ה",
      "confidence": 0.93,
      "reasoning": "the crop shows כ\\"ה clearly"
    }'''
    with pytest.raises(json.JSONDecodeError):
        json.loads(text)
    parsed = vcv.extract_json_fields(text)
    assert parsed["selected_option"] == "A"
    assert parsed["transcription_found"] == '''סי' כ"ה'''
    assert parsed["confidence"] == 0.93
    assert "\\" not in parsed["reasoning"], "a literal backslash must never survive into stored review data"


def test_extract_json_fields_accepts_a_quoted_confidence_number():
    text = '{"selected_option": "B", "transcription_found": "אלף", "confidence": "0.95", "reasoning": "x"}'
    assert vcv.extract_json_fields(text)["confidence"] == 0.95


def test_extract_json_fields_returns_none_rather_than_a_partial_decision():
    assert vcv.extract_json_fields('{"transcription_found": "אלף", "confidence": 0.9}') is None
    assert vcv.extract_json_fields('{"selected_option": "A", "reasoning": "no confidence here"}') is None
    assert vcv.extract_json_fields("not json at all") is None


@pytest.fixture
def vision_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(vcv, "CACHE_DB", str(tmp_path / "cache.db"))
    vcv.init_cache()
    return vcv.CACHE_DB


def test_vision_cache_key_covers_every_input_that_changes_the_right_answer(vision_cache):
    """CLAUDE.md Lesson 12, the bug this project has now hit three times in
    this one cache (crop-only 2026-08-05, no context 2026-08-10, no prompt
    2026-08-14). Each component is verified to DISCRIMINATE: a cache that
    silently matched a different question would be worse than no cache.
    """
    crop, word_a, word_b, ctx = b"PNG-A", "אלף", "בית", "context one"
    vcv.cache_decision(crop, word_a, word_b, ctx, '{"selected_option": "A"}', model="test-model")
    assert vcv.get_cached_decision(crop, word_a, word_b, ctx) == '{"selected_option": "A"}'

    assert vcv.get_cached_decision(b"PNG-B", word_a, word_b, ctx) is None, "crop image not in the key"
    assert vcv.get_cached_decision(crop, "גימל", word_b, ctx) is None, "reading A not in the key"
    assert vcv.get_cached_decision(crop, word_a, "גימל", ctx) is None, "reading B not in the key"
    assert vcv.get_cached_decision(crop, word_a, word_b, "context two") is None, "context not in the key"


def test_vision_cache_key_covers_the_prompt_template(vision_cache, monkeypatch):
    """Editing PROMPT_TEMPLATE must invalidate prior answers. It silently did
    not until 2026-08-14: the 2026-08-12 prompt fix only landed because an
    unrelated schema change had already emptied the table, and the same edit
    made a day later would have been a no-op nobody could have noticed."""
    crop, word_a, word_b, ctx = b"PNG-A", "אלף", "בית", "context"
    real_prompt_hash = vcv.PROMPT_HASH
    vcv.cache_decision(crop, word_a, word_b, ctx, '{"selected_option": "A"}')
    monkeypatch.setattr(vcv, "PROMPT_HASH", "a-different-prompt")
    assert vcv.get_cached_decision(crop, word_a, word_b, ctx) is None
    vcv.cache_decision(crop, word_a, word_b, ctx, '{"selected_option": "B"}')
    assert vcv.get_cached_decision(crop, word_a, word_b, ctx) == '{"selected_option": "B"}'
    # Restore only PROMPT_HASH - monkeypatch.undo() would also revert the
    # temp CACHE_DB this test's fixture set, pointing the next lookup at the
    # real cache database.
    monkeypatch.setattr(vcv, "PROMPT_HASH", real_prompt_hash)
    assert vcv.get_cached_decision(crop, word_a, word_b, ctx) == '{"selected_option": "A"}', (
        "the two prompts' answers must coexist as separate rows, not overwrite each other"
    )


def test_vision_cache_stores_a_null_side_rather_than_failing_the_not_null_schema(vision_cache):
    """delete/insert-opcode candidates legitimately have one side as None
    ("X" vs nothing) - coerced to a sentinel, not stored as SQL NULL, which
    would never compare equal on lookup."""
    vcv.cache_decision(b"PNG", "אלף", None, "ctx", '{"selected_option": "A"}')
    assert vcv.get_cached_decision(b"PNG", "אלף", None, "ctx") == '{"selected_option": "A"}'
    assert vcv.get_cached_decision(b"PNG", "אלף", "בית", "ctx") is None


def test_vision_cache_migration_is_lossless_and_idempotent(tmp_path, monkeypatch):
    """The prompt_hash migration back-fills rather than dropping (419 real
    answers, 0 API calls). A regression that dropped them instead would cost
    a full re-run against the paid API, silently."""
    db = str(tmp_path / "old.db")
    monkeypatch.setattr(vcv, "CACHE_DB", db)
    conn = sqlite3.connect(db)
    conn.execute(
        "CREATE TABLE corrections_cache (crop_hash TEXT NOT NULL, word_a TEXT NOT NULL, "
        "word_b TEXT NOT NULL, context_hash TEXT NOT NULL, decision_json TEXT, "
        "PRIMARY KEY (crop_hash, word_a, word_b, context_hash))"
    )
    conn.executemany("INSERT INTO corrections_cache VALUES (?, ?, ?, ?, ?)",
                     [(f"crop{i}", "אלף", "בית", "ctx", '{"selected_option": "A"}') for i in range(5)])
    conn.commit()
    conn.close()

    vcv.init_cache()
    conn = sqlite3.connect(db)
    rows = conn.execute("SELECT crop_hash, prompt_hash, decision_json FROM corrections_cache").fetchall()
    assert len(rows) == 5, "migration must carry every cached answer over, not drop the table"
    assert {r[1] for r in rows} == {vcv.PROMPT_HASH}
    assert conn.execute("SELECT COUNT(*) FROM corrections_cache_pre_prompt_hash").fetchone()[0] == 5, (
        "the pre-migration table must be kept, not deleted"
    )
    conn.close()

    vcv.init_cache()  # second run: nothing left to migrate
    conn = sqlite3.connect(db)
    assert conn.execute("SELECT COUNT(*) FROM corrections_cache").fetchone()[0] == 5
    conn.close()
