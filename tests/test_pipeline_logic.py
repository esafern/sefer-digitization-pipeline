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
# Root reorganized 2026-08-16 into pipeline/ and tools/ (see CLAUDE.md
# "Directory layout") - both added to sys.path so every `import X as Y`
# below keeps working unchanged regardless of which of the two a given
# script now lives in, rather than rewriting every import site to
# `from pipeline import X` / `from tools import X`.
sys.path.insert(0, os.path.join(REPO, "pipeline"))
sys.path.insert(0, os.path.join(REPO, "tools"))

import apply_reviewer_decisions as ard  # noqa: E402
import assemble_corrections_dataset as acd  # noqa: E402
import audit_applied_decisions as aad  # noqa: E402
import build_corrections_dataset as bcd  # noqa: E402
import build_gematria_trace as bgt  # noqa: E402
import build_klal_page_regions as bkpr  # noqa: E402
import check_klal_token_orphans as ckto  # noqa: E402
import check_next_marker_and_title as cnmt  # noqa: E402
import corpus_io as cio  # noqa: E402
import vision_adjudication_common as vac  # noqa: E402
import verify_flagged_candidates_vision as vfcv  # noqa: E402
import detect_ligature_corruption as dlc  # noqa: E402
import detect_real_word_substitution as drws  # noqa: E402
import extract_abbreviation_forms as eaf  # noqa: E402
import propose_abbreviation_expansions as pae  # noqa: E402
import propose_punctuation_part1 as ppp  # noqa: E402
import validate_lexicon_independent as vli  # noqa: E402
import review_lexicon_gaps as rlg  # noqa: E402
import review_decisions as rd  # noqa: E402
import review_server as rs  # noqa: E402
import validate_catchword_continuity as vcc  # noqa: E402
import validate_part1_corpus_integrity as vpci  # noqa: E402
import validate_title_alphabetical_order as vtao  # noqa: E402
import detect_repeated_words as drw  # noqa: E402
import detect_insertion_deletion as did  # noqa: E402
import detect_split_merge as dsm  # noqa: E402
import detect_cross_klal_errors as dcke  # noqa: E402


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


def test_apply_replace_refuses_a_snapshot_with_no_text_to_replace():
    """Added 2026-08-16 (code audit). With final_text empty the span is [] and
    `n` fell back to 1, so for an out-of-range word_index the drift check
    compared `words[wi:wi+1]` - which is [] in Python, not an IndexError -
    against that empty span, PASSED, and the slice assignment then APPENDED
    the chosen text to the end of the klal at a position the decision never
    named. apply_insert_removal() has had the equivalent `n == 0` guard since
    it was written; this one never did."""
    text = "אלף בית גימל"
    assert ard.apply_replace(text, 99, "", "דלת") is None, "must not append at the end of the klal"
    assert ard.apply_replace(text, 99, None, "דלת") is None
    assert ard.apply_replace(text, 1, "", "דלת") is None
    # Positive control: a real replace at a real index still works.
    assert ard.apply_replace(text, 1, "בית", "דלת") == "אלף דלת גימל"


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


def test_every_mutator_refuses_a_negative_word_index():
    """Added 2026-08-15 (hard-wired-value audit). Python does not raise on a
    negative index - `words[-1]` is the LAST word and `words[-1:-1] = span`
    inserts before it - so without an explicit check a decision recorded at a
    negative index edits a real word at a position it never meant, in the one
    place that writes part1.json. The same half-a-bounds-check gap was fixed
    in audit_applied_decisions.py's checkers 2026-08-14 and guarded in
    check_drift, but the mutators still had only the upper end. Not reachable
    from today's producers (both are structurally non-negative); this is
    defence-in-depth on the corpus-mutating path.
    """
    text = "אלף בית גימל"
    # Each index below is chosen so the call would SUCCEED without the guard -
    # a -1 against a 1-word span is refused by the span check anyway, and a
    # test that passes for that reason would prove nothing (verified by
    # mutation: dropping the guards leaves such a test green).
    #   -3 wraps onto word 0 for the two span-based mutators: an edit at a
    #      position the decision never named, and one every drift checker in
    #      this project already classifies as MISMATCH.
    #   -1 is worse for the other three - it edits/deletes/inserts at the
    #      klal's LAST word while the recorded index says something else.
    assert ard.apply_replace(text, -3, "אלף", "דלת") is None
    assert ard.apply_insert_removal(text, -3, "אלף") is None
    assert ard.apply_manual_correction(text, -1, "גימל", "דלת") is None
    assert ard.apply_manual_deletion(text, -1, "גימל") is None
    assert ard.apply_delete_insertion(text, -1, "דלת") is None
    # Positive control: the same calls at the real index still work, so a
    # mutation making every mutator refuse everything cannot pass this test.
    assert ard.apply_replace(text, 2, "גימל", "דלת") == "אלף בית דלת"
    assert ard.apply_delete_insertion(text, 2, "דלת") == "אלף בית דלת גימל"


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


# --- apply_reviewer_decisions.main(): the per-run safety model ---------------
# The individual mutators above are pure; main() is where the guards live
# (never re-apply, never exceed one word-count change per klal per run, never
# treat "keep the current text" as an edit). Exercised end to end against
# throwaway copies of part1.json / corrections / the decisions log - nothing
# here touches a tracked file.

@pytest.fixture
def apply_harness(tmp_path, monkeypatch, decisions_path):
    """Point apply_reviewer_decisions at synthetic data. rd's module-level
    functions are rebound to the temp log (binding the originals first, since
    the replacements share their names)."""
    part1_path = tmp_path / "part1.json"

    def setup(klalim, corrections):
        part1_path.write_text(json.dumps(klalim, ensure_ascii=False), encoding="utf-8")
        monkeypatch.setattr(ard, "PART1_PATH", str(part1_path))
        monkeypatch.setattr(ard, "load_current_corrections", lambda: corrections)
        for name in ("all_current", "applied_decision_ids", "append_decision", "history_for"):
            real = getattr(rd, name)
            monkeypatch.setattr(ard.rd, name,
                                lambda *a, _f=real, **kw: _f(*a, **{**kw, "path": decisions_path}))
        monkeypatch.setattr(sys, "argv", ["apply_reviewer_decisions.py"])

    def run():
        ard.main()
        return {k["klal_id"]: k["clean_text"]
                for k in json.loads(part1_path.read_text(encoding="utf-8"))}

    setup.run = run
    return setup


def _correction(word_index, opcode, docai, final):
    return {"word_index": word_index, "opcode": opcode, "docai_reading": docai,
            "final_text": final, "flag": "ambiguous"}


def test_confirming_the_current_text_of_an_insert_candidate_deletes_nothing(apply_harness, decisions_path):
    """PROJECT-STATUS.md finding ★1: an 'insert'-opcode candidate's
    final_text IS the span apply_insert_removal would delete, so a reviewer
    voting "keep this text" fell through to the removal path and silently
    deleted exactly what they voted to keep."""
    entry = _correction(1, "insert", None, "בית")
    apply_harness([{"klal_id": 1, "clean_text": "אלף בית גימל"}], {"1": [entry]})
    rd.append_decision("candidate_choice", klal_id=1, word_index=1, chosen_source="final_text",
                       chosen_text="בית", candidate_snapshot=entry, path=decisions_path)

    assert apply_harness.run()[1] == "אלף בית גימל"
    events = [r for r in rd.history_for(1, 1, "apply_event", path=decisions_path)]
    assert len(events) == 1 and "no change" in (events[0]["note"] or ""), (
        "a confirmed-no-op is still a reviewed decision and must be recorded as applied"
    )


def test_only_one_word_count_changing_decision_is_applied_per_klal_per_run(apply_harness, decisions_path):
    """Every insert/delete shifts every later word_index in the same klal, so
    a second one in the same run would be applied against indices the first
    one just invalidated."""
    first = _correction(1, "delete", "חדש", None)
    second = _correction(3, "delete", "נוסף", None)
    apply_harness([{"klal_id": 1, "clean_text": "אלף בית גימל"}], {"1": [first, second]})
    for entry in (first, second):
        rd.append_decision("candidate_choice", klal_id=1, word_index=entry["word_index"],
                           chosen_source="docai_reading", chosen_text=entry["docai_reading"],
                           candidate_snapshot=entry, path=decisions_path)

    text = apply_harness.run()[1]
    assert text.split().count("חדש") + text.split().count("נוסף") == 1, (
        f"exactly one of the two insertions may land in a single run, got {text!r}"
    )


def test_a_decision_already_marked_applied_is_never_applied_twice(apply_harness, decisions_path):
    entry = _correction(1, "delete", "חדש", None)
    apply_harness([{"klal_id": 1, "clean_text": "אלף בית גימל"}], {"1": [entry]})
    decision = rd.append_decision("candidate_choice", klal_id=1, word_index=1,
                                  chosen_source="docai_reading", chosen_text="חדש",
                                  candidate_snapshot=entry, path=decisions_path)
    rd.append_decision("apply_event", klal_id=1, word_index=1,
                       applied_decision_id=decision["id"], path=decisions_path)

    assert apply_harness.run()[1] == "אלף בית גימל", (
        "an apply_event on record means this decision is already in the corpus - re-applying it "
        "is how `יגעתי 1 1 1 ולא` happened (PROJECT-STATUS.md 2026-08-11)"
    )


def test_a_decision_whose_candidate_has_drifted_is_skipped_not_guessed_at(apply_harness, decisions_path):
    live = _correction(1, "replace", "בות", "בית")
    stale_snapshot = _correction(1, "replace", "בות", "דלת")  # candidate moved since the decision
    apply_harness([{"klal_id": 1, "clean_text": "אלף בית גימל"}], {"1": [live]})
    rd.append_decision("candidate_choice", klal_id=1, word_index=1, chosen_source="docai_reading",
                       chosen_text="בות", candidate_snapshot=stale_snapshot, path=decisions_path)

    assert apply_harness.run()[1] == "אלף בית גימל"
    assert rd.history_for(1, 1, "apply_event", path=decisions_path) == [], (
        "a skipped decision must not be recorded as applied"
    )


def test_a_clean_replace_decision_is_applied_and_recorded(apply_harness, decisions_path):
    """The positive control for the three refusals above - without it, a
    mutation that made main() skip EVERYTHING would still pass them all."""
    entry = _correction(1, "replace", "בות", "בית")
    apply_harness([{"klal_id": 1, "clean_text": "אלף בית גימל"}], {"1": [entry]})
    decision = rd.append_decision("candidate_choice", klal_id=1, word_index=1,
                                  chosen_source="docai_reading", chosen_text="בות",
                                  candidate_snapshot=entry, path=decisions_path)

    assert apply_harness.run()[1] == "אלף בות גימל"
    events = rd.history_for(1, 1, "apply_event", path=decisions_path)
    assert [e["applied_decision_id"] for e in events] == [decision["id"]]


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


def test_foreign_character_check_fires_and_respects_the_allowed_repertoire():
    """Proves check_foreign_characters() CAN fail, on synthetic input.

    tests/test_corpus_invariants.py gates it against the real corpus with a
    baseline, and that gate alone would stay green if the check were neutered
    to find nothing (`found - baseline` is empty either way) - per CLAUDE.md
    Lesson 2, a gate that cannot fail is indistinguishable from one that
    passes. Same reasoning that put the three older gated integrity checks
    under their own can-it-fire tests (2026-08-14).
    """
    def klal(kid, text):
        return {"klal_id": kid, "clean_text": text}

    # Everything in the documented repertoire must stay silent: Hebrew, the
    # gershayim/geresh abbreviation marks, the bullet, the editorial [.]
    # convention, footnote asterisks, citation parens.
    clean = [klal(1, 'רש"י אמר וכו\' • [.] (סימן ה\') *) ודו"ק - כן, כך: כך.')]
    assert vpci.check_foreign_characters(clean) == [], (
        "a legitimate Part-1 character was flagged - PART1_ALLOWED_NON_HEBREW is too narrow"
    )

    # The real-corpus cases, reproduced synthetically.
    greek = vpci.check_foreign_characters([klal(39, "דבכולהן Π דבכולהו")])
    assert len(greek) == 1 and "U+03A0" in greek[0] and "klal 39 word 1" in greek[0], greek
    assert "GREEK CAPITAL LETTER PI" in greek[0]

    # The specific blind spot this check exists to close: a Latin 'P' is
    # caught by check_character_sanity's LATIN_RE, its Greek homoglyph is not.
    assert vpci.check_character_sanity([klal(39, "דבכולהן P דבכולהו")]), (
        "sanity precondition: LATIN_RE does catch a Latin P"
    )
    assert vpci.check_character_sanity([klal(39, "דבכולהן Π דבכולהו")]) == [], (
        "this is the blind spot being closed: check_character_sanity is structurally "
        "unable to see the Greek homoglyph, which is why check_foreign_characters exists"
    )

    for ch in ("&", "!", ";", "@", "5"):
        hits = vpci.check_foreign_characters([klal(7, f"פנים {ch} פנים")])
        assert len(hits) == 1, f"{ch!r} should be reported as outside the repertoire: {hits}"

    # Reported per OCCURRENCE with its own position, not once per klal - the
    # baseline is keyed by (klal_id, word_index, char) and needs that precision.
    multi = vpci.check_foreign_characters([klal(9, "אא & בב ! גג")])
    assert len(multi) == 2 and "word 1" in multi[0] and "word 3" in multi[1], multi


def test_reassigning_DECISIONS_PATH_redirects_calls_that_pass_no_explicit_path(
        tmp_path, monkeypatch):
    """Every OTHER test in this file passes `path=` explicitly, which is
    exactly why this trap survived three audit rounds unexercised.

    review_decisions.py's functions used to declare `path=DECISIONS_PATH` as a
    DEFAULT ARGUMENT. Python evaluates that once, at import time, so
    reassigning the module attribute afterwards did nothing to any call that
    omitted `path=` - the write still went to the real, git-tracked
    review_decisions.jsonl. monkeypatch.setattr on a module constant is this
    suite's standard redirection idiom (PART1_PATH, RAW_DIR, FREQ_CACHE,
    CACHE_DB, SEFARIA_FREQ_CACHE all rely on it and all work); this module was
    the one place it silently failed, and it is the module guarding the one
    file CLAUDE.md says no pipeline run may ever clobber.

    Not hypothetical: it has already produced two accidental writes to the
    tracked log, one in the round-1 audit and one while confirming this
    finding in round 2. Both were caught by a byte-comparison afterwards, not
    by the code refusing.
    """
    redirected = str(tmp_path / "redirected.jsonl")
    monkeypatch.setattr(rd, "DECISIONS_PATH", redirected)

    record = rd.append_decision("klal_flag", klal_id=424242, needs_revisit=True,
                                note="round-2 redirection probe")

    assert os.path.exists(redirected), (
        "append_decision() with no explicit path must honour the CURRENT value of "
        "rd.DECISIONS_PATH. If this fails, the write went somewhere else - which for a "
        "default-argument binding means the real, tracked review_decisions.jsonl."
    )
    with open(redirected, encoding="utf-8") as f:
        rows = [json.loads(l) for l in f if l.strip()]
    assert [r["id"] for r in rows] == [record["id"]]

    # The readers must follow the same reassignment, or a redirected write
    # becomes invisible to the very code meant to read it back.
    assert rd.flagged_klalim() == [424242]
    assert rd.find_by_id(record["id"])["note"] == "round-2 redirection probe"
    assert rd.current_for(424242, decision_type="klal_flag")["id"] == record["id"]
    assert list(rd.all_current("klal_flag")) == [(424242, None)]


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


# --- propose_abbreviation_expansions: how a form gets classified -------------
# Added 2026-08-16 (code audit). This script writes nothing: it proposes
# expansions for a human review/apply stage that does not exist yet. That is
# exactly why its output has to be right BEFORE anything is built on it - a
# wrong proposal here is a fidelity defect (Success Criterion 1) waiting for a
# consumer, and every failure below was silent in the printed report, not
# loud. None of it needs the Sefaria frequency cache: `freq` is passed
# explicitly so the classification logic is testable with no network, no
# gitignored cache, and no dependence on what today's reference corpus
# happens to contain.

def test_a_prefixed_expansion_keeps_the_prefix_it_stripped():
    """The proposal used to be the ROOT's expansion verbatim, so `דר'` was
    reported as `רבי` - a proposal that DELETES the ד. 113 forms / 642
    occurrences, printed in the same column and format as an unprefixed
    dictionary hit."""
    assert pae.resolve("דר'", None)["expansion"] == "דרבי"
    assert pae.resolve("התוס'", None)["expansion"] == "התוספות"
    assert pae.resolve("ובס'", None)["expansion"] == "ובספר"
    # A list-valued expansion must keep the prefix on every alternative.
    assert pae.resolve('ושכ"כ', None)["expansion"] == ["ושכן כתב", "ושכך כתב", "ושכל כך"]
    # ... and the root/prefix must be reported, not left to be parsed back out
    # of the human-readable `method` string.
    assert pae.resolve("דר'", None)["root"] == "ר'"
    assert pae.resolve("דר'", None)["prefix"] == "ד"


def test_a_non_expand_category_keeps_its_gloss_unprefixed():
    """"name"/"scholarly"/"stays" values are explanatory text, not proposals -
    prefixing them would produce `הרבי שלמה יצחקי (Rashi)`."""
    r = pae.resolve('הרא"ש', None)
    assert r["category"] == "name" and r["root"] == 'רא"ש'
    assert r["expansion"] == pae.ROOT_ENTRIES['רא"ש'][1]


def test_prefix_decomposition_prefers_the_longest_surviving_root():
    """Was "longest prefix first", which prefers eating the most of the word -
    backwards, since a longer root is the more specific dictionary match.
    Each case below flipped a category or an expansion on real Part-1 data."""
    maharash = pae.resolve('ומוהר"ש', None)
    assert maharash["root"] == 'מוהר"ש' and maharash["category"] == "name", (
        "ומ- + וה- + ר\"ש re-analyses the word's own letters מוה as prefixes and lands on "
        "the generic scholarly ר\"ש, when the name מוהר\"ש is a root"
    )
    assert pae.resolve('ומהר"י', None)["category"] == "name"
    lamed = pae.resolve('ולמ"ד', None)
    assert lamed["root"] == 'למ"ד' and lamed["expansion"] == "ולמאן דאמר", (
        "ול- + מ\"ד swallows the ל that is part of the abbreviation itself"
    )
    assert pae.resolve('ובפ"ק', None)["root"] == 'בפ"ק'


def test_no_prefix_may_stack_on_a_copy_of_itself():
    """No Hebrew proclitic doubles. Without the guard the 2-level stripper
    invents roots from the word's own letters: דדחי' -> ד-ד- + חי' ->
    "דדחידושי"."""
    assert all(p1 != p2 for p, _ in pae.prefix_decompositions("דדחי'")
               for p1, p2 in [(p[:1], p[1:2])] if len(p) == 2)
    assert pae.resolve("דדחי'", None)["category"] != "expand"
    # The single-level ד- + a real root is untouched by the guard.
    assert pae.resolve('דא"כ', None)["expansion"] == "דאם כן"


def test_a_long_geresh_final_word_is_never_filed_as_a_citation_numeral():
    """looks_like_bare_numeral() had no upper bound while its docstring
    promised "a single Hebrew letter or short letter-run", and resolve() falls
    back to it after truncated-word completion declines - so 187 forms / 249
    occurrences of plain Hebrew prose were reported under a heading that says
    they are numbers and need no attention (Lesson 15)."""
    assert pae.resolve("ובקדושין'", None)["category"] == "unresolved"
    assert pae.resolve("דתלמידי'", None)["category"] == "unresolved"
    # The real numerals still classify as numerals - a fix that emptied the
    # category would pass the two assertions above and prove nothing.
    assert pae.resolve("ב'", None)["category"] == "numeral"
    assert pae.resolve("מה'", None)["category"] == "expand"  # a root wins over the shape


def test_the_two_readings_of_the_geresh_shape_partition_stem_length_exactly():
    """Numeral and truncated-word are the same SHAPE with one cut between
    them. If the two bounds ever drift apart, some stem length is either
    claimed by both or dropped by both, silently."""
    assert pae.MAX_NUMERAL_STEM_LETTERS + 1 == pae.MIN_TRUNCATION_STEM_LETTERS
    # Cover well past the defined boundaries so a future threshold increase
    # does not escape the test's range.
    for stem_len in range(1, max(pae.MAX_NUMERAL_STEM_LETTERS, pae.MIN_TRUNCATION_STEM_LETTERS) + 3):
        word = "א" * stem_len + "'"
        numeral = pae.looks_like_bare_numeral(word)
        truncatable = (pae.ends_in_bare_geresh(word)
                       and stem_len >= pae.MIN_TRUNCATION_STEM_LETTERS)
        assert numeral != truncatable, f"stem length {stem_len} is claimed by both or neither"


def test_geresh_shape_detection_accepts_the_real_hebrew_geresh_too():
    """part1.json holds only the ASCII forms today, so this path is inert on
    real data - which is the point: a later normalisation to U+05F3 would
    switch off numeral detection AND truncated-word completion while
    is_abbreviation() kept matching, i.e. no error, just a silently emptied
    category (Lesson 1)."""
    assert pae.ends_in_bare_geresh("נרא׳") is True
    assert pae.looks_like_bare_numeral("ב׳") is True
    # A gershayim-marked acronym is never the bare-geresh shape, either form.
    assert pae.ends_in_bare_geresh('רש"י') is False
    assert pae.ends_in_bare_geresh("רש״י") is False


def test_a_frequency_completion_is_not_reported_as_a_dictionary_expansion():
    """It appends exactly ONE letter, so a multi-letter truncation has no
    correct candidate on the ballot and a merely-common word wins by default -
    confirmed on real data (בפי' -> בפיו for בפירוש, בחי' -> בחיי for
    בחידושי). It gets its own category so the next such form cannot be read
    as a peer of an editorially-confirmed expansion."""
    freq = {"נראה": 5000, "נראו": 10, "נראי": 3}
    r = pae.resolve("נרא'", freq)
    assert r["category"] == "truncated" and r["expansion"] == "נראה"
    assert "truncated" in pae.CATEGORY_LABELS and "expand" != r["category"]
    # The two confirmed misses now resolve through the dictionary instead.
    assert pae.resolve("בפי'", freq)["expansion"] == "בפירוש"
    assert pae.resolve("בחי'", freq)["expansion"] == "בחידושי"


def test_truncated_completion_answers_only_on_a_single_clear_winner():
    stem = "נרא"
    assert pae.resolve_truncated_word(stem + "'", {"נראה": 5000, "נראו": 10}) == "נראה"
    tie = {"נראה": 200, "נראו": 199}
    assert pae.resolve_truncated_word(stem + "'", tie) is None, (
        "two comparably-attested completions are an unanswered question, not a proposal"
    )
    below_floor = {"נראה": pae.MIN_COMPLETION_FREQUENCY}
    assert pae.resolve_truncated_word(stem + "'", below_floor) is None
    assert pae.resolve_truncated_word("דר'", {"דרך": 9999}) is None, (
        "a 2-letter stem is a title/prefix shape (דר' = ד + ר'), not a truncated word"
    )
    assert pae.resolve_truncated_word("נרא'", None) is None  # no frequency cache built
    assert pae.resolve_truncated_word('רש"י', {"רשיה": 9999}) is None  # not the geresh shape


def test_every_category_resolve_can_produce_is_labelled_in_the_report():
    """Same guard as FLAG_LABELS above, same reason: main() prints one line
    per CATEGORY_ORDER entry, so an unlabelled category vanishes from the
    summary while still sitting in --json. Enumerated from ROOT_ENTRIES plus
    the dynamically-assigned ones rather than read off the source."""
    produced = {"truncated", "numeral", "artifact", "unresolved", "expand"}
    for category, _ in pae.ROOT_ENTRIES.values():
        produced.add(category)
    unlabelled = sorted(produced - set(pae.CATEGORY_LABELS))
    assert not unlabelled, f"unlabelled categories: {unlabelled}"
    assert set(pae.CATEGORY_ORDER) == set(pae.CATEGORY_LABELS)


def test_root_entries_are_well_formed_for_the_report_that_renders_them():
    for root, entry in pae.ROOT_ENTRIES.items():
        assert isinstance(entry, tuple) and len(entry) == 2, f"{root!r}: {entry!r}"
        category, expansion = entry
        assert category in pae.CATEGORY_LABELS, f"{root!r} has unknown category {category!r}"
        assert category != "truncated", (
            f"{root!r}: 'truncated' means the frequency guess, never a dictionary entry"
        )
        if category == "scholarly":
            assert isinstance(expansion, list) and len(expansion) > 1, (
                f"{root!r}: main() renders scholarly entries with ', '.join(...) - a bare string "
                "would be printed one character at a time, and a single option is not ambiguous"
            )
        assert expansion, f"{root!r} has an empty expansion"
        for option in (expansion if isinstance(expansion, list) else [expansion]):
            assert isinstance(option, str) and option.strip(), f"{root!r}: {option!r}"


def test_the_two_abbreviation_scripts_still_share_one_definition():
    """propose_abbreviation_expansions.py re-derives the token list rather
    than reading extract_abbreviation_forms.py's output, so the two copies of
    is_abbreviation() are a second-copy-of-the-truth (Lesson 13) - cheap to
    pin, silent if it drifts."""
    assert pae.QUOTE_CHARS == eaf.QUOTE_CHARS
    for word in ['רש"י', "וכו'", "מלה", "נרא׳", "רש״י", "'", '"', ""]:
        assert pae.is_abbreviation(word) == eaf.is_abbreviation(word), word


def test_extract_reports_each_klal_once_per_form_however_often_it_repeats():
    counts, klalim = eaf.extract([
        {"klal_id": 1, "clean_text": 'רש"י אמר רש"י ועוד'},
        {"klal_id": 2, "clean_text": 'רש"י בלבד'},
        {"klal_id": 3, "clean_text": "אין כאן קיצור"},
    ])
    assert counts['רש"י'] == 3, "the count is per occurrence"
    assert klalim['רש"י'] == [1, 2], "the klal list is per klal, deduplicated and in order"
    assert set(counts) == {'רש"י'}


# --- review_server: the manual-correction display drift check ----------------

def test_manual_correction_drift_check_bounds_both_ends():
    """Added 2026-08-16 (code audit). Both render paths for a
    manual_correction (api_klal's synthetic entry, api_klalim's per-klal
    count) checked only the UPPER bound - the same half-a-bounds-check gap
    fixed in audit_applied_decisions.py's checkers (2026-08-14) and
    apply_reviewer_decisions.py's mutators (2026-08-15), never revisited on
    the display path. `words[-1]` is the klal's LAST word in Python, so a
    decision recorded at -1 whose original_word matched that last word
    rendered as a live "Human-Decided" correction on a word it never
    described, and counted toward the klal's badges."""
    words = "אלף בית גימל".split()
    assert rs._word_matches(words, 1, "בית") is True
    assert rs._word_matches(words, 1, "דלת") is False, "a moved word is drift"
    # -1 with the klal's real LAST word is the case that passed before: it is
    # exactly what a wrapped index resolves to, so a test using any other
    # word would go green with the guard removed and prove nothing.
    assert rs._word_matches(words, -1, "גימל") is False
    assert rs._word_matches(words, 9, "אלף") is False


def test_a_manual_correction_cannot_be_recorded_at_a_negative_index(monkeypatch):
    """The log is append-only by design, so a bad row can only ever be
    superseded, never removed - which makes the write site the right place to
    refuse one.

    append_decision is stubbed out rather than merely asserting the raise:
    api_post_manual_correction() calls rd.append_decision with no `path`, i.e.
    the REAL git-tracked review_decisions.jsonl. A first draft of this test
    left it unstubbed and, while mutation-testing the very guard it covers,
    appended a junk row to that file (caught by the byte-identical hash check
    at the end of the audit and reverted). Stubbing makes the test state the
    stronger property anyway - nothing is written at all, not just "an
    exception was raised somewhere" - and keeps this file's no-writes-to-a-
    tracked-file rule true even when the code under test is broken, which is
    exactly when a test is most likely to write something.
    """
    appended = []
    monkeypatch.setattr(rs.rd, "append_decision",
                        lambda *a, **kw: appended.append((a, kw)) or {"id": "stub"})
    with pytest.raises(ValueError):
        rs.api_post_manual_correction({"klal_id": 1, "word_index": -1, "chosen_text": "אלף"})
    with pytest.raises(ValueError):
        rs.api_post_manual_correction({"klal_id": 1, "word_index": 0, "chosen_text": None})
    assert appended == [], "a rejected manual correction must never reach the decisions log"
    # Positive control: a valid one does reach it, so a guard that refused
    # everything could not pass this test.
    rs.api_post_manual_correction({"klal_id": 1, "word_index": 0, "chosen_text": "אלף",
                                   "original_word": "בית"})
    assert len(appended) == 1


# --- review_server: word-level AI flags must be discoverable, and must never
# --- leak into the klal's general flag panel --------------------------------

def test_general_klal_flag_ignores_word_level_entries(tmp_path, monkeypatch):
    """FIXED 2026-08-17 (user bug report on klal 1 w446: an AI pass named a
    disputed word in free-text prose inside a klal_flag note, but nothing
    highlighted it - review_decisions.py's own history_for() docstring had
    assumed klal_flag rows always carry word_index=None). The general panel
    (api_klal_flag / the klal-level "needs a second look" note) must keep
    ignoring any klal_flag that DOES carry a word_index - it is about one
    specific word, not the klal as a whole, and must never be shown as if it
    were the general note."""
    path = str(tmp_path / "decisions.jsonl")
    monkeypatch.setattr(rd, "DECISIONS_PATH", path)
    rd.append_decision("klal_flag", 1, needs_revisit=True, note="general note", path=path)
    rd.append_decision("klal_flag", 1, word_index=5, needs_revisit=True,
                        note="word-level note", path=path)
    current = rs._general_klal_flag_current(1)
    assert current["note"] == "general note"
    history = rs._general_klal_flag_history(1)
    assert len(history) == 1 and history[0]["note"] == "general note"


def test_word_level_ai_flags_synthesizes_a_highlightable_entry(tmp_path, monkeypatch):
    path = str(tmp_path / "decisions.jsonl")
    monkeypatch.setattr(rd, "DECISIONS_PATH", path)
    rd.append_decision("klal_flag", 1, word_index=2, needs_revisit=True,
                        note="w2 'ומידו' -> 'ומיהו' (corrupt 1x, correction 201x)", path=path)
    words = "אלף בית גימל דלת הא".split()
    flags = rs._word_level_ai_flags(1, words)
    assert len(flags) == 1
    assert flags[0]["word_index"] == 2
    assert flags[0]["opcode"] == "ai_flag"
    assert "ומידו" in flags[0]["reasoning"]


def test_word_level_ai_flags_skips_closed_and_out_of_bounds(tmp_path, monkeypatch):
    """A closed (needs_revisit: false) word-level flag has already been
    resolved and must stop being highlighted, the same way a satisfied
    manual_correction does. An out-of-bounds word_index (the klal's text
    shrank since the flag was written, the same drift class _word_matches
    guards against for manual_correction) must never be handed to the
    frontend as a real array index."""
    path = str(tmp_path / "decisions.jsonl")
    monkeypatch.setattr(rd, "DECISIONS_PATH", path)
    rd.append_decision("klal_flag", 1, word_index=1, needs_revisit=True, note="open", path=path)
    rd.append_decision("klal_flag", 1, word_index=1, needs_revisit=False, note="closed now", path=path)
    rd.append_decision("klal_flag", 1, word_index=99, needs_revisit=True, note="out of bounds", path=path)
    words = "אלף בית גימל".split()
    assert rs._word_level_ai_flags(1, words) == []


def test_word_level_ai_flag_yields_to_a_manual_correction_on_the_same_word(monkeypatch):
    """A human already acting on this exact word (manual_correction) makes
    the AI's earlier flag redundant - api_klal must not show both."""
    monkeypatch.setattr(rs, "_load_klalim",
                        lambda: ({1: {"klal_id": 1, "clean_text": "אלף בית גימל", "page": 1}}, [1]))
    monkeypatch.setattr(rs, "_load_alignment", lambda: {})
    monkeypatch.setattr(rs, "_load_corrections", lambda: {})
    monkeypatch.setattr(rs, "_load_regions", lambda: {})
    monkeypatch.setattr(rs, "_load_punctuation_candidates", lambda: {})
    monkeypatch.setattr(rs.rd, "all_current",
                        lambda dtype: ({(1, 1): {"candidate_snapshot": {"original_word": "בית"},
                                                  "chosen_text": "בין", "word_index": 1}}
                                       if dtype == "manual_correction" else {}))
    monkeypatch.setattr(rs, "_word_level_ai_flags",
                        lambda klal_id, words: [{"word_index": 1, "opcode": "ai_flag",
                                                  "reasoning": "should not appear"}])
    monkeypatch.setattr(rs, "_general_klal_flag_current", lambda klal_id: None)
    result = rs.api_klal(1)
    opcodes_at_1 = [c["opcode"] for c in result["corrections"] if c["word_index"] == 1]
    assert opcodes_at_1 == ["manual"], "manual_correction must win over a redundant AI flag on the same word"


# --- detect_ligature_corruption: word indices must mean what everything else
# --- means by them ----------------------------------------------------------

def test_ligature_detector_indexes_words_the_same_way_the_corpus_mutators_do(tmp_path):
    """It reported a word_index from `split(" ")`, which keeps an empty string
    for every run of consecutive spaces; a correction made from its output is
    recorded and applied against apply_reviewer_decisions.py's `split()`
    indexing. One double space anywhere in a klal shifted every later index by
    one - silently, in the one direction that edits the corpus at a position
    nobody chose. Inert on today's data (0 klalim in any part file where the
    two splits disagree), so only a synthetic fixture can hold the line."""
    part = tmp_path / "part_fixture.json"
    part.write_text(json.dumps(
        [{"klal_id": 1, "clean_text": " אלף  בית גימל "}], ensure_ascii=False), encoding="utf-8")
    words = dlc.load_klal_words(str(part))[1]
    assert words == ["אלף", "בית", "גימל"]
    assert words == " אלף  בית גימל ".split(), "must match the corpus mutators' own splitting"


def test_ligature_detector_still_finds_a_planted_corruption(tmp_path):
    """Positive control for the two negatives above and for _resolve()'s
    dominance rule: a detector that found nothing would satisfy an
    index-shape test just as well."""
    part = tmp_path / "part_fixture.json"
    frequent = " ".join(["אלמא"] * 5)
    part.write_text(json.dumps([
        {"klal_id": 1, "clean_text": f"{frequent} אמא"},
        {"klal_id": 2, "clean_text": 'א"א אינו מועמד'},
    ], ensure_ascii=False), encoding="utf-8")
    klal_words = dlc.load_klal_words(str(part))
    counts = dlc.build_frequency_table(klal_words)
    high, ambiguous = dlc.find_candidates(klal_words, counts)
    assert [(kid, idx, bad, good) for kid, idx, bad, good, _ in high] == [(1, 5, "אמא", "אלמא")]
    assert ambiguous == []


def test_abbreviations_are_kept_out_of_the_frequency_evidence():
    """The load-bearing gershayim exclusion is in the frequency table, not in
    the candidate loop: `א"ה` (Even HaEzer), `א"א` (eshet ish) and friends are
    real, unrelated tokens, and letting them count as corpus words is the
    false-positive class the original investigation had to remove (the
    "~620 ambiguous" estimate that turned out to be 228)."""
    counts = dlc.build_frequency_table({1: ["אלמא", 'א"א', 'א"א', 'א"ה']})
    assert counts["אלמא"] == 1
    assert not [w for w in counts if dlc.has_gershayim(w)], (
        f"abbreviations reached the frequency table: {[w for w in counts if dlc.has_gershayim(w)]}"
    )


# --- detect_real_word_substitution: a rare word one confusable letter away
# --- from a common real word, restricted to zero-independent-attestation
# --- candidates only ---------------------------------------------------------

def test_substitution_detector_requires_zero_attestation_not_just_low(tmp_path):
    """The load-bearing fix, mutation-verified here rather than just described:
    an earlier draft accepted a candidate whenever it merely beat the
    original's frequency by DOMINANCE_RATIO, which produced 348 "high-
    confidence" hits on real Part-1 data, most of them ordinary rare-but-real
    words losing a frequency contest to a common neighbour. Requiring the
    ORIGINAL word to have ZERO independent attestation cut that to 83 + 1
    ambiguous. A word with even one independent hit must be refused
    regardless of how much more frequent the substituted neighbour is."""
    part = tmp_path / "part_fixture.json"
    part.write_text(json.dumps(
        [{"klal_id": 1, "clean_text": "אמה ואמה ואמה"}], ensure_ascii=False), encoding="utf-8")
    klal_words = drws.load_klal_words(str(part))
    own_counts = drws.build_own_frequency_table(klal_words)
    # אמה has real independent attestation (it means "cubit"/"maidservant"),
    # even though אמר (confusable via ה<->ר? no - not a confusion pair here;
    # use a word that IS one substitution from a common word but genuinely
    # attested itself).
    indep_freq = {"אמה": 50, "אמר": 45266}
    result = drws._resolve("אמה", indep_freq)
    assert result is None, "a word with nonzero independent attestation must never be flagged"


def test_substitution_detector_finds_a_planted_corruption_with_zero_attestation(tmp_path):
    """Positive control: a word absent from the independent corpus, one
    confusable substitution away from a well-attested real word, with no
    competing option, resolves as high-confidence."""
    indep_freq = {"אכל": 0, "אבל": 5000}  # אכל = ORIGINAL (corrupt), אבל = corrected
    result = drws._resolve("אכל", indep_freq)
    assert result is not None
    is_ambiguous, options = result
    assert not is_ambiguous
    assert options == [("אבל", 5000)]


def test_substitution_detector_ambiguous_case_returns_every_qualifying_option():
    """FIXED during this script's own construction, before it ever shipped:
    an early draft kept only the highest-frequency option even in the
    ambiguous bucket, which silently discarded the linguistically correct
    answer in real spot-checking - klal 30 word 1206 'וטכל' scored 'ומכל'
    (103x, wrong) ahead of 'וטבל' (66x, right - "and immersed," standard
    conversion terminology, confirmed by reading the actual sentence). A
    reviewer working from a truncated list would never see the right answer.
    This test reproduces that exact shape synthetically: two qualifying
    substitutions where the higher-frequency one is not dominant enough to
    settle it alone."""
    # 'וטכל' -> 'ומכל' (ט->מ) and 'וטבל' (כ->ב) both qualify; neither
    # dominates the other by DOMINANCE_RATIO (103 <= 5 * 66 = 330).
    indep_freq = {"וטכל": 0, "ומכל": 103, "וטבל": 66}
    result = drws._resolve("וטכל", indep_freq)
    assert result is not None
    is_ambiguous, options = result
    assert is_ambiguous, "neither option dominates the other - must not be reported as settled"
    assert set(options) == {("ומכל", 103), ("וטבל", 66)}, (
        "BOTH qualifying options must be returned, not just the top-frequency one"
    )


def test_substitution_detector_single_dominant_option_is_not_ambiguous():
    """The mirror case: when one option dominates the runner-up by
    DOMINANCE_RATIO, it must be reported as high-confidence, not ambiguous -
    otherwise every candidate would end up in the low-trust bucket."""
    indep_freq = {"אכל": 0, "אבל": 5000, "אבד": 10}  # 5000 > 5 * 10
    result = drws._resolve("אכל", indep_freq)
    is_ambiguous, options = result
    assert not is_ambiguous
    assert options[0] == ("אבל", 5000)


def test_substitution_detector_known_false_positive_is_excluded(tmp_path):
    """klal 88 word 423 'רתם' is already scan-verified (900 DPI) as print-
    faithful, not a corruption - the standing proof in this project that a
    confusable-letter/frequency signal can point at real broken type. Must
    never resurface as a fresh "finding.\""""
    part_data = [{"klal_id": 88, "clean_text": " ".join(["x"] * 423 + ["רתם"])}]
    path = tmp_path / "part_fixture.json"
    path.write_text(json.dumps(part_data, ensure_ascii=False), encoding="utf-8")
    klal_words = drws.load_klal_words(str(path))
    own_counts = drws.build_own_frequency_table(klal_words)
    indep_freq = {"רתם": 0, "התם": 2415}
    high, ambiguous = drws.find_candidates(klal_words, own_counts, indep_freq)
    assert high == [] and ambiguous == [], (
        "klal 88 word 423 'רתם' must be excluded via KNOWN_FALSE_POSITIVES"
    )


def test_substitution_detector_respects_rare_threshold():
    """A word occurring MORE than RARE_THRESHOLD times in Part 1's own text
    is not a candidate no matter what the independent corpus says - a
    corruption is not the print's own common spelling of anything."""
    words = ["אכל"] * (drws.RARE_THRESHOLD + 1)
    klal_words = {1: words}
    own_counts = drws.build_own_frequency_table(klal_words)
    indep_freq = {"אכל": 0, "אבל": 5000}
    high, ambiguous = drws.find_candidates(klal_words, own_counts, indep_freq)
    assert high == [] and ambiguous == [], "a word common in Part 1 itself must not be flagged"


# --- validate_lexicon_independent: the independent reference corpus ----------
# Added 2026-08-16 (code audit). This is the ONE check in the pipeline whose
# reference data has no lineage to this project's own OCR, so a silent gap in
# it is worse than a gap anywhere else: it is the signal every other check is
# measured against. Nothing here touches the real (gitignored) corpus - all
# inputs are synthetic and all writes go to tmp_path.

def test_flatten_strings_reaches_text_held_in_a_dict_not_only_a_list():
    """Most Sefaria books' `text` is a nested list; a book with named
    sub-sections is a DICT, and dicts used to fall through silently.
    Shulchan Arukh, Even HaEzer is one ("", "Seder HaGet", "Seder Halitzah"):
    106,474 words - 4.3% of the corpus, one of the four chelekim - counted as
    downloaded, named in the docstring, contributing exactly nothing."""
    out = []
    vli.flatten_strings({"": [["אלף", "בית"]], "Seder HaGet": [["גימל"]]}, out)
    assert out == ["אלף", "בית", "גימל"]
    # ... and nested the other way round, which is the real shape.
    out = []
    vli.flatten_strings([{"א": ["אלף"]}, ["בית"]], out)
    assert out == ["אלף", "בית"]
    # Non-text leaves must still be ignored rather than stringified.
    out = []
    vli.flatten_strings({"a": [1, None, "אלף"]}, out)
    assert out == ["אלף"]


def test_clean_words_keeps_only_hebrew_letters_and_drops_markup_and_niqqud():
    assert vli.clean_words('<b>אלף</b> בית') == ["אלף", "בית"]
    assert vli.clean_words("אָלֶף") == ["אלף"]
    assert vli.clean_words('רש"י') == ["רשי"], (
        "gershayim are stripped and the letters joined, so the table holds no abbreviation "
        "forms - consumers scoring a candidate against it are matching letter-runs only"
    )
    assert vli.clean_words("123 !!! ") == []


def test_the_frequency_cache_is_rejected_unless_its_provenance_matches(tmp_path, monkeypatch):
    """The cache is a bare {word: count} file: the version missing Even HaEzer
    was byte-shaped exactly like a correct one and would have been reused
    forever, by this script AND by propose_abbreviation_expansions.py.
    Lesson 12 applied to a derived table - the key must cover the extractor
    and the inputs, not just "a file exists"."""
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "Book.json").write_text(json.dumps({"text": ["אלף בית"]}), encoding="utf-8")
    monkeypatch.setattr(vli, "RAW_DIR", str(raw))
    monkeypatch.setattr(vli, "FREQ_CACHE", str(tmp_path / "word_freq.json"))
    monkeypatch.setattr(vli, "FREQ_META", str(tmp_path / "word_freq.meta.json"))

    assert vli.cache_is_current() is False, "no cache yet"
    counts = vli.build_or_load_frequency_table()
    assert counts["אלף"] == 1 and vli.cache_is_current() is True

    # A book appearing (or disappearing) invalidates it - the inputs changed.
    (raw / "Second.json").write_text(json.dumps({"text": ["אלף"]}), encoding="utf-8")
    assert vli.cache_is_current() is False
    assert vli.build_or_load_frequency_table()["אלף"] == 2
    assert vli.cache_is_current() is True

    # So does a change to the extraction rule itself, which is what the Even
    # HaEzer fix was - same books in, different words out.
    monkeypatch.setattr(vli, "EXTRACTOR_VERSION", vli.EXTRACTOR_VERSION + 1)
    assert vli.cache_is_current() is False


def test_a_book_contributing_zero_words_is_reported_not_absorbed(tmp_path, monkeypatch, capsys):
    """The totals line cannot show a missing book; only a per-book check can.
    An unhandled `text` shape and a bad download look identical from the sum."""
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "Good.json").write_text(json.dumps({"text": ["אלף בית"]}), encoding="utf-8")
    (raw / "Empty.json").write_text(json.dumps({"text": []}), encoding="utf-8")
    monkeypatch.setattr(vli, "RAW_DIR", str(raw))
    monkeypatch.setattr(vli, "FREQ_CACHE", str(tmp_path / "word_freq.json"))
    monkeypatch.setattr(vli, "FREQ_META", str(tmp_path / "word_freq.meta.json"))
    vli.build_or_load_frequency_table()
    out = capsys.readouterr().out
    assert "ZERO words" in out and "Empty.json" in out and "Good.json" not in out


def test_the_abbreviation_proposer_refuses_a_frequency_cache_it_cannot_vouch_for(
        tmp_path, monkeypatch):
    """propose_abbreviation_expansions.py is a consumer of the same file. It
    must not answer from a table of unknown provenance - a completion scored
    against a corpus quietly missing a quarter of the Shulchan Arukh is worse
    than no completion, because it is indistinguishable from a good one."""
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "Book.json").write_text(json.dumps({"text": ["אלף"]}), encoding="utf-8")
    cache = tmp_path / "word_freq.json"
    cache.write_text(json.dumps({"נראה": 9999}), encoding="utf-8")
    meta = tmp_path / "word_freq.meta.json"
    monkeypatch.setattr(pae, "SEFARIA_FREQ_CACHE", str(cache))
    monkeypatch.setattr(vli, "RAW_DIR", str(raw))
    monkeypatch.setattr(vli, "FREQ_CACHE", str(cache))
    monkeypatch.setattr(vli, "FREQ_META", str(meta))
    assert pae.load_independent_frequency() is None, "no provenance record at all"

    meta.write_text(json.dumps({"extractor_version": vli.EXTRACTOR_VERSION - 1,
                                "source_files": ["Book.json"]}), encoding="utf-8")
    assert pae.load_independent_frequency() is None, "built by an older extractor"

    meta.write_text(json.dumps({"extractor_version": vli.EXTRACTOR_VERSION,
                                "source_files": ["Book.json"]}), encoding="utf-8")
    assert pae.load_independent_frequency() == {"נראה": 9999}, (
        "a cache whose provenance DOES match must still be used - a guard that refuses "
        "everything would pass the assertion above and disable the feature outright"
    )


# --- verify_corrections_vision: response parsing + cache-key coverage --------

VISION_IMPORT_ERROR = None
try:
    import verify_corrections_vision as vcv  # noqa: E402
except ImportError as exc:  # PyMuPDF / google-genai are pipeline deps, not test deps
    vcv = None
    VISION_IMPORT_ERROR = str(exc)

# Skips only these tests, not the whole module - everything above needs
# nothing beyond the standard library, and losing all of it because one
# optional import is missing would be the "quietly narrowed coverage" this
# project's Lesson 1 is about.
requires_vision_deps = pytest.mark.skipif(
    vcv is None, reason=f"verify_corrections_vision.py not importable: {VISION_IMPORT_ERROR}")

WITNESS_VISION_IMPORT_ERROR = None
try:
    import verify_witness_vision as vwv  # noqa: E402
except ImportError as exc:  # same optional deps as verify_corrections_vision.py
    vwv = None
    WITNESS_VISION_IMPORT_ERROR = str(exc)

requires_witness_vision_deps = pytest.mark.skipif(
    vwv is None, reason=f"verify_witness_vision.py not importable: {WITNESS_VISION_IMPORT_ERROR}")


@requires_vision_deps
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


@requires_vision_deps
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


@requires_vision_deps
def test_extract_json_fields_accepts_a_quoted_confidence_number():
    text = '{"selected_option": "B", "transcription_found": "אלף", "confidence": "0.95", "reasoning": "x"}'
    assert vcv.extract_json_fields(text)["confidence"] == 0.95


@requires_vision_deps
def test_extract_json_fields_returns_none_rather_than_a_partial_decision():
    assert vcv.extract_json_fields('{"transcription_found": "אלף", "confidence": 0.9}') is None
    assert vcv.extract_json_fields('{"selected_option": "A", "reasoning": "no confidence here"}') is None
    assert vcv.extract_json_fields("not json at all") is None


@pytest.fixture
def vision_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(vcv, "CACHE_DB", str(tmp_path / "cache.db"))
    vcv.init_cache()
    return vcv.CACHE_DB


@requires_vision_deps
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


@requires_vision_deps
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


@requires_vision_deps
def test_vision_cache_stores_a_null_side_rather_than_failing_the_not_null_schema(vision_cache):
    """delete/insert-opcode candidates legitimately have one side as None
    ("X" vs nothing) - coerced to a sentinel, not stored as SQL NULL, which
    would never compare equal on lookup."""
    vcv.cache_decision(b"PNG", "אלף", None, "ctx", '{"selected_option": "A"}')
    assert vcv.get_cached_decision(b"PNG", "אלף", None, "ctx") == '{"selected_option": "A"}'
    assert vcv.get_cached_decision(b"PNG", "אלף", "בית", "ctx") is None


@requires_vision_deps
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


# --- verify_witness_vision: cache-key coverage + migration -------------------
# FOUND 2026-08-16 (revalidation/refactor audit round 3): witness_cache's
# PRIMARY KEY was (crop_hash, word_a, word_b, context_hash) - missing
# prompt_hash, the exact gap already found and fixed in
# verify_corrections_vision.py (2026-08-14) and propose_punctuation_part1.py
# (2026-08-16). This is the third sibling script with the identical
# crop/adjudicate/cache shape; the fix and its tests mirror those two
# directly (CLAUDE.md Lesson 12).

@pytest.fixture
def witness_vision_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(vwv, "CACHE_DB", str(tmp_path / "witness_cache.db"))
    vwv.init_cache()
    return vwv.CACHE_DB


@requires_witness_vision_deps
def test_witness_vision_cache_key_covers_every_input_that_changes_the_right_answer(witness_vision_cache):
    crop, word_a, word_b, ctx = b"PNG-A", "אלף", "בית", "context one"
    vwv.cache_put(crop, word_a, word_b, ctx, '{"selected_option": "A"}')
    assert vwv.get_cached(crop, word_a, word_b, ctx) == '{"selected_option": "A"}'

    assert vwv.get_cached(b"PNG-B", word_a, word_b, ctx) is None, "crop image not in the key"
    assert vwv.get_cached(crop, "גימל", word_b, ctx) is None, "docai reading not in the key"
    assert vwv.get_cached(crop, word_a, "גימל", ctx) is None, "tesseract reading not in the key"
    assert vwv.get_cached(crop, word_a, word_b, "context two") is None, "context not in the key"


@requires_witness_vision_deps
def test_witness_vision_cache_key_covers_the_prompt_template(witness_vision_cache, monkeypatch):
    """Editing PROMPT_TEMPLATE must invalidate prior answers - before this
    fix, witness_cache's key had no prompt_hash column at all, so this
    could never have discriminated no matter what PROMPT_TEMPLATE said."""
    crop, word_a, word_b, ctx = b"PNG-A", "אלף", "בית", "context"
    real_prompt_hash = vwv.PROMPT_HASH
    vwv.cache_put(crop, word_a, word_b, ctx, '{"selected_option": "A"}')
    monkeypatch.setattr(vwv, "PROMPT_HASH", "a-different-prompt")
    assert vwv.get_cached(crop, word_a, word_b, ctx) is None
    vwv.cache_put(crop, word_a, word_b, ctx, '{"selected_option": "B"}')
    assert vwv.get_cached(crop, word_a, word_b, ctx) == '{"selected_option": "B"}'
    # Restore only PROMPT_HASH - monkeypatch.undo() would also revert the
    # temp CACHE_DB this test's fixture set, pointing the next lookup at the
    # real cache database.
    monkeypatch.setattr(vwv, "PROMPT_HASH", real_prompt_hash)
    assert vwv.get_cached(crop, word_a, word_b, ctx) == '{"selected_option": "A"}', (
        "the two prompts' answers must coexist as separate rows, not overwrite each other"
    )


@requires_witness_vision_deps
def test_witness_vision_cache_stores_a_null_side_rather_than_failing_the_not_null_schema(witness_vision_cache):
    """An 'insert' opcode item legitimately has docai_reading as None (DocAI
    found nothing at that position) - coerced to a sentinel, not stored as
    SQL NULL, which would never compare equal on lookup."""
    vwv.cache_put(b"PNG", None, "בית", "ctx", '{"selected_option": "B"}')
    assert vwv.get_cached(b"PNG", None, "בית", "ctx") == '{"selected_option": "B"}'
    assert vwv.get_cached(b"PNG", "אלף", "בית", "ctx") is None


@requires_witness_vision_deps
def test_witness_vision_cache_migration_is_lossless_and_idempotent(tmp_path, monkeypatch):
    """The prompt_hash migration back-fills rather than dropping (419 real
    answers per the module's own docstring, 0 API calls to redo them)."""
    db = str(tmp_path / "old_witness.db")
    monkeypatch.setattr(vwv, "CACHE_DB", db)
    conn = sqlite3.connect(db)
    conn.execute(
        "CREATE TABLE witness_cache (crop_hash TEXT NOT NULL, word_a TEXT NOT NULL, "
        "word_b TEXT NOT NULL, context_hash TEXT NOT NULL, decision_json TEXT, "
        "PRIMARY KEY (crop_hash, word_a, word_b, context_hash))"
    )
    conn.executemany("INSERT INTO witness_cache VALUES (?, ?, ?, ?, ?)",
                     [(f"crop{i}", "אלף", "בית", "ctx", '{"selected_option": "A"}') for i in range(5)])
    conn.commit()
    conn.close()

    vwv.init_cache()
    conn = sqlite3.connect(db)
    rows = conn.execute("SELECT crop_hash, prompt_hash, decision_json FROM witness_cache").fetchall()
    assert len(rows) == 5, "migration must carry every cached answer over, not drop the table"
    assert {r[1] for r in rows} == {vwv.PROMPT_HASH}
    assert conn.execute("SELECT COUNT(*) FROM witness_cache_pre_prompt_hash").fetchone()[0] == 5, (
        "the pre-migration table must be kept, not deleted"
    )
    conn.close()

    vwv.init_cache()  # second run: nothing left to migrate
    conn = sqlite3.connect(db)
    assert conn.execute("SELECT COUNT(*) FROM witness_cache").fetchone()[0] == 5
    conn.close()


def test_punctuation_cache_key_covers_the_prompt_template(tmp_path, monkeypatch):
    """FIXED 2026-08-16 (round-2 follow-up, risk 3): propose_punctuation_
    part1.py's cache key used to be sha256(klal_id|clean_text) only - the
    PROMPT_TEMPLATE wrapped around that content wasn't part of the key, so
    editing the template (a real instruction/constraint change) would have
    silently kept serving answers cached under the OLD question forever.
    Identical gap already fixed in verify_corrections_vision.py 2026-08-14;
    this is the same discipline applied here. Two different prompt_hash
    values must produce two different keys for identical klal content."""
    key_a = ppp.cache_key_for(1, "some clean text", "hash_a")
    key_b = ppp.cache_key_for(1, "some clean text", "hash_b")
    assert key_a != key_b, "changing prompt_hash must change the cache key"

    key_same = ppp.cache_key_for(1, "some clean text", "hash_a")
    assert key_a == key_same, "the same inputs must produce the same key"


def test_punctuation_cache_migration_carries_over_matching_rows_losslessly(
        tmp_path, monkeypatch):
    """The migration must back-fill a pre-existing (klal_id|clean_text)-keyed
    row onto the new (klal_id|clean_text|prompt_hash) key when the klal's
    CURRENT clean_text still matches what was cached - not drop it, per this
    project's standing "never silently discard a paid API answer" discipline
    (CLAUDE.md, verify_corrections_vision.py's own migration). It must also
    be idempotent (a second run finds nothing new to migrate) and must NOT
    fabricate a row for a klal whose text has since drifted - which is
    exactly what happened on the REAL punctuation_cache.db (klal 1/2/3's
    text changed since the 2026-08-14 pilot that populated it, so 0 of its 3
    real rows migrate - verified separately by hand against a scratch copy,
    not asserted here since this test uses synthetic data)."""
    import hashlib
    import sqlite3

    db = str(tmp_path / "punct_test.db")
    monkeypatch.setattr(ppp, "CACHE_DB", db)
    ppp.init_cache()

    klal_a = {"klal_id": 1, "clean_text": "אלף בית גימל"}
    klal_b = {"klal_id": 2, "clean_text": "דלת הא וו"}  # no cached row for this one

    old_key_a = hashlib.sha256(
        f"{klal_a['klal_id']}|{klal_a['clean_text']}".encode("utf-8")
    ).hexdigest()
    ppp.cache_response(old_key_a, '{"insertions": []}')

    ppp.migrate_add_prompt_hash([klal_a, klal_b])

    new_key_a = ppp.cache_key_for(klal_a["klal_id"], klal_a["clean_text"], ppp.PROMPT_HASH)
    assert ppp.get_cached(new_key_a) == '{"insertions": []}', (
        "a matching old-style row must be carried over under the new key"
    )
    # The old row itself is left in place (harmless, and this is a value-level
    # re-key, not a schema migration - nothing renames or drops the table).
    assert ppp.get_cached(old_key_a) == '{"insertions": []}'

    # klal_b never had a cached row - nothing to fabricate.
    new_key_b = ppp.cache_key_for(klal_b["klal_id"], klal_b["clean_text"], ppp.PROMPT_HASH)
    assert ppp.get_cached(new_key_b) is None

    conn = sqlite3.connect(db)
    count_after_first = conn.execute("SELECT COUNT(*) FROM cache").fetchone()[0]
    conn.close()

    ppp.migrate_add_prompt_hash([klal_a, klal_b])  # idempotence
    conn = sqlite3.connect(db)
    count_after_second = conn.execute("SELECT COUNT(*) FROM cache").fetchone()[0]
    conn.close()
    assert count_after_second == count_after_first, (
        "a second migration run must find nothing new to migrate"
    )


def test_is_running_header_matches_the_exact_token_not_a_substring():
    """FIXED 2026-08-16 (round-2 follow-up): is_running_header() used to be a
    substring test (`"מלאכי" in orig_word`) on the whole joined diff-span
    text. A real word that merely CONTAINS those four letters as a substring
    (a prefix glued on the front, or an adjacent token fused into the same
    span) would have been silently treated as header furniture and dropped -
    never surfacing as a correction candidate, with no flag or log to notice
    by. This is the exact-token-equality replacement, tested directly rather
    than through the full DocAI/page-word pipeline."""
    def tok(text):
        return {"text": text}

    # The real running header: its own standalone token.
    assert bcd.is_running_header([tok("מלאכי")]) is True
    assert bcd.is_running_header([tok("יד"), tok("מלאכי")]) is True

    # A longer real word that merely CONTAINS "מלאכי" as a substring must NOT
    # be treated as the header - this is the bug itself, reproduced.
    assert bcd.is_running_header([tok("ולמלאכיו")]) is False

    # An unrelated span, and an empty span.
    assert bcd.is_running_header([tok("בהדיא")]) is False


# --- check_next_marker_and_title: next-klal marker + title-vs-opening ------

def test_find_next_klal_marker_only_fires_on_a_real_trailing_marker():
    """The regex must anchor to the END of the text (a colon-then-short-word
    ANYWHERE would false-positive on ordinary mid-sentence abbreviations like
    ' : ')  and must not fire when there's no marker at all."""
    assert cnmt.find_next_klal_marker("דברי הטקסט עד כאן : טו") == "טו"
    assert cnmt.find_next_klal_marker("דברי הטקסט עד כאן : סוג") == "סוג"
    # No trailing marker - an ordinary sentence with no colon+short-word tail.
    assert cnmt.find_next_klal_marker("דברי הטקסט עד כאן ולא יותר") is None
    # A colon appears, but the tail after it is too long to be a marker.
    assert cnmt.find_next_klal_marker("דברי הטקסט : זהו משפט ארוך מדי") is None


def test_check_next_klal_marker_flags_a_planted_mismatch():
    """Positive control: klal 1's marker doesn't match gematria(2), klal 2's
    does - only klal 1 should be reported."""
    klalim = [
        {"klal_id": 1, "clean_text": "א דברי הטקסט עד כאן : ג"},  # ג != expected ב
        {"klal_id": 2, "clean_text": "ב דברי הטקסט עד כאן : ג"},  # correct
        {"klal_id": 3, "clean_text": "ג דברי הטקסט בלי סימון בסוף"},
    ]
    mismatches = cnmt.check_next_klal_marker(klalim)
    assert [m[0] for m in mismatches] == [1]
    assert mismatches[0][1:] == ("ג", "ב")


def test_opening_phrase_strips_gematria_and_stops_at_first_boundary():
    assert cnmt.opening_phrase("א שלום עולם . עוד טקסט", "א") == "שלום עולם"
    assert cnmt.opening_phrase("א שלום עולם [.] עוד טקסט", "א") == "שלום עולם"
    # klal 166's own convention: a geresh glued directly onto the gematria
    # numeral before the opening word starts.
    assert cnmt.opening_phrase("קסו' שלום עולם . עוד", "קסו") == "שלום עולם"


def test_check_title_vs_opening_tolerates_prefix_in_either_direction():
    """A title that's a clean prefix of the opening (ordinary editorial
    shortening, e.g. klal 83's short title for a long sentence) or whose
    opening-extraction was cut short by an internal comma (klal 105/134's
    shape) must NOT be reported - only a genuine divergence should be."""
    klalim = [
        # Title is a legitimate shorter label - not a finding.
        {"klal_id": 1, "gematria": "א",
         "clean_text": "א בשל תורה הלך אחר המחמיר ולא עוד", "title": "בשל תורה"},
        # Opening-extraction cut short at an internal comma; title is longer
        # but starts with the extracted (truncated) opening - not a finding.
        {"klal_id": 2, "gematria": "ב",
         "clean_text": "ב שלאחריהם אמרו , קי\"ל כוותייהו", "title": "שלאחריהם אמרו קי\"ל כוותייהו"},
        # Real divergence: the title has dropped the opening word the body
        # keeps (the klal 101/102/103/104 shape) - must be flagged.
        {"klal_id": 3, "gematria": "ג",
         "clean_text": 'ג ב"ד מתנין לעקור דבר [.] עוד', "title": "מתנין לעקור דבר"},
    ]
    mismatches = cnmt.check_title_vs_opening(klalim)
    assert [m[0] for m in mismatches] == [3]
    assert mismatches[0][1:] == ("מתנין לעקור דבר", 'ב"ד מתנין לעקור דבר')


# --- verify_flagged_candidates_vision: note parsing + word location --------

def test_unescape_strips_literal_backslash_artifact():
    """Several notes were composed with a literal backslash before an
    embedded gershayim (the stored note text is literally 'ר\\"ס', not
    'ר"ס') - confirmed by reading the raw JSONL, not assumed. No real corpus
    word contains a backslash, so stripping it unconditionally is safe and
    is what let 19 otherwise-unparseable candidates resolve correctly."""
    assert vfcv._unescape('ר\\"ס') == 'ר"ס'
    assert vfcv._unescape("רגיל") == "רגיל"


def test_parse_real_word_sub_handles_semicolon_separated_multi_candidates():
    note = ("... Candidates in this klal: w213 'המאן'->'דמאן' (corrupt 1x); "
            "w313 'מיר'->'מיד' (corrupt 1x)")
    out = vfcv.parse_real_word_sub(note, 217)
    assert out == [(217, 213, "המאן", "דמאן"), (217, 313, "מיר", "מיד")]


def test_parse_real_word_sub_skips_ambiguous_entry():
    """klal 30's AMBIGUOUS entry is deliberately handled via
    AMBIGUOUS_OVERRIDES, not the regex parser - the regex has no way to
    extract a single (original, candidate) pair from a genuinely two-way
    ambiguous note, and must not silently pick one."""
    note = "Candidates in this klal: w1206 'וטכל'->AMBIGUOUS: 'ומכל' (103x) or 'וטבל' (66x)"
    assert vfcv.parse_real_word_sub(note, 30) == []


def test_parse_semantic_spotcheck2_handles_pipe_separated_and_overlap_suffix():
    note = ("... Candidates: w95 'כתכו' -> 'כתבו': כ for ב; 'context' | "
            "w403 'איהן' -> 'איהו': final nun for vav || OVERLAP: w38 already flagged.")
    out = vfcv.parse_semantic_spotcheck2(note, 4)
    assert out == [(4, 95, "כתכו", "כתבו"), (4, 403, "איהן", "איהו")]


def test_parse_semantic_spotcheck2_tolerates_embedded_gershayim_in_either_quote_style():
    """The regex must find the closing delimiter that matches the OPENER,
    not just any quote character - an earlier draft used a bare `["']` for
    both ends and silently truncated 'הנז'' one character early wherever it
    was wrapped in double quotes (the corpus's abbreviation mark IS the
    ASCII double-quote, so 'ר"ס' inside a "..." wrapper is exactly this
    collision, not a hypothetical edge case)."""
    note = 'Candidates: w74 "ר"ס" -> "ר"פ": ס for פ'
    out = vfcv.parse_semantic_spotcheck2(note, 12)
    assert out == [(12, 74, 'ר"ס', 'ר"פ')]


def test_parse_semantic_spotcheck2_tolerates_plausibly_between_arrow_and_target():
    note = "Candidates: w461 ':לוקי' -> plausibly 'חילוקי': a colon is glued to a truncated word"
    out = vfcv.parse_semantic_spotcheck2(note, 189)
    assert out == [(189, 461, ":לוקי", "חילוקי")]


def test_locate_word_searches_continuation_pages_not_just_the_first():
    """FIXED during this script's own construction: 54 of Part 1's 222
    klalim span a page break via klal_page_regions.json's `continuations`
    list, and an earlier draft only ever searched the primary `page` -
    silently failing to locate every candidate whose word landed on the
    continuation (confirmed real case: klal 12 w237). Reproduced here
    synthetically rather than trusting the real-data fix without a test."""
    regions = {
        "1": {
            "page": 100,
            "bbox": {"x1": 0.0, "y1": 0.0, "x2": 1.0, "y2": 0.5},
            "continuations": [
                {"page": 101, "bbox": {"x1": 0.0, "y1": 0.0, "x2": 1.0, "y2": 0.5}},
            ],
        }
    }
    token_cache = {
        100: [{"text": "אלף", "x1": 0.1, "y1": 0.1, "x2": 0.2, "y2": 0.12}],
        101: [{"text": "יעד", "x1": 0.1, "y1": 0.1, "x2": 0.2, "y2": 0.12}],
    }
    result = vfcv.locate_word(1, 5, "יעד", regions, 10, token_cache)
    assert result is not None
    page, token, _ = result
    assert page == 101, "the target word lives on the continuation page, not the primary one"


def test_locate_word_disambiguates_across_a_page_break_not_just_within_one_page():
    """FIXED (round-3 audit): when the same text matches on BOTH the primary
    page and a continuation page, an earlier draft tracked only the LAST
    page's token list for ranking, so any match on an EARLIER page was
    unconditionally penalized (not in that list) and always lost, regardless
    of which occurrence was actually closer to word_index - confirmed on
    real data (klal 30's 'גכי', klal 41's 'כתכו', each duplicated across a
    page break). Reproduced synthetically: word_index is chosen to fall
    early in the klal (proportionally on the FIRST page), and the primary
    page's match must win, not the continuation page's."""
    regions = {
        "1": {
            "page": 100,
            "bbox": {"x1": 0.0, "y1": 0.0, "x2": 1.0, "y2": 1.0},
            "continuations": [
                {"page": 101, "bbox": {"x1": 0.0, "y1": 0.0, "x2": 1.0, "y2": 1.0}},
            ],
        }
    }
    # 10 filler tokens on the primary page, the target text once near its
    # start; 10 filler tokens on the continuation, the SAME target text once
    # near ITS start too - word_index=1 should resolve to the PRIMARY page's
    # occurrence (global rank ~1 of 20), not the continuation's (~global rank 11).
    def filler_line(y):
        return {"text": "x", "x1": 0.5, "y1": y, "x2": 0.6, "y2": y + 0.01}

    primary_tokens = [{"text": "יעד", "x1": 0.5, "y1": 0.01, "x2": 0.6, "y2": 0.02}]
    primary_tokens += [filler_line(0.02 + i * 0.01) for i in range(9)]
    cont_tokens = [{"text": "יעד", "x1": 0.5, "y1": 0.01, "x2": 0.6, "y2": 0.02}]
    cont_tokens += [filler_line(0.02 + i * 0.01) for i in range(9)]
    token_cache = {100: primary_tokens, 101: cont_tokens}

    page, token, match_count = vfcv.locate_word(1, 1, "יעד", regions, 20, token_cache)
    assert match_count == 2
    assert page == 100, "word_index=1 is early in the klal - must resolve to the PRIMARY page's match"


def test_locate_word_band_fallback_refuses_a_footer_only_band():
    """FIXED during this script's own construction: klal 167's region entry
    claims 990 tokens on one page for a 1369-word klal with no
    `continuations` listed (a real gap in klal_page_regions.json). A naive
    proportional estimate for a late word_index lands past the klal's real
    content, in the page-footer 'Digitized by Google' strip - confirmed on
    real data. The fallback must recognize a token-free-of-Hebrew-letters
    band as a non-answer, not hand back a crop of a footer."""
    regions = {
        "1": {"page": 50, "bbox": {"x1": 0.0, "y1": 0.0, "x2": 1.0, "y2": 1.0}, "token_count": 3},
    }
    token_cache = {
        50: [
            {"text": "Digitized", "x1": 0.3, "y1": 0.9, "x2": 0.5, "y2": 0.92},
            {"text": "by", "x1": 0.5, "y1": 0.9, "x2": 0.55, "y2": 0.92},
            {"text": "Google", "x1": 0.55, "y1": 0.9, "x2": 0.7, "y2": 0.92},
        ],
    }
    result = vfcv.locate_word_band_fallback(1, 900, regions, 1000, token_cache)
    assert result is None, "a footer-only band must be refused, not returned as a crop location"
    assert bcd.is_running_header([]) is False


# --- vision_adjudication_common + round-4 fixes -----------------------------
# Extracted 2026-08-17 (revalidation/refactor audit round 4): verify_
# corrections_vision.py and verify_witness_vision.py used to each
# hand-maintain nearly-identical crop/cache/JSON-recovery/retry machinery -
# round 3 found direct, concrete proof this already caused drift (the
# missing-prompt_hash cache-key bug, already fixed twice elsewhere, had to be
# independently re-fixed a THIRD time in verify_witness_vision.py's own
# copy). The cache-key/migration logic itself is already covered end-to-end
# by the existing test_vision_cache_*/test_witness_vision_cache_* tests
# above (both keep passing unchanged post-extraction, since vcv.init_cache/
# get_cached_decision/cache_decision and vwv.init_cache/get_cached/cache_put
# are now thin wrappers over the same shared functions those tests already
# exercise). What's new here is the genuinely NEW logic this round added:
# vcv.parse_decision_text() (a named, reusable strict-then-lenient parse
# chain), and two round-4 bug fixes in verify_flagged_candidates_vision.py
# (a missing client timeout, and a single candidate's total failure crashing
# the whole batch).

@requires_vision_deps
def test_shared_cache_table_respects_has_model_column(tmp_path):
    """verify_corrections_vision.py's corrections_cache carries a `model`
    provenance column; verify_witness_vision.py's witness_cache never did -
    a real, pre-existing schema difference, not accidental drift. The shared
    factory in vision_adjudication_common.py must keep distinguishing the
    two via has_model_column rather than silently converging them."""
    db = str(tmp_path / "cache.db")
    vcv.vac.init_cache_table(db, "with_model", "hash1", has_model_column=True)
    vcv.vac.init_cache_table(db, "without_model", "hash1", has_model_column=False)
    conn = sqlite3.connect(db)
    with_cols = {r[1] for r in conn.execute("PRAGMA table_info(with_model)")}
    without_cols = {r[1] for r in conn.execute("PRAGMA table_info(without_model)")}
    conn.close()
    assert "model" in with_cols
    assert "model" not in without_cols


@requires_vision_deps
def test_shared_cache_get_put_roundtrip_without_model_column(tmp_path):
    db = str(tmp_path / "cache.db")
    vcv.vac.init_cache_table(db, "witness_cache", "hashA", has_model_column=False)
    vcv.vac.put_cached_decision(db, "witness_cache", "hashA", b"PNG", "x", "y", "ctx",
                                 '{"a":1}', has_model_column=False)
    got = vcv.vac.get_cached_decision(db, "witness_cache", "hashA", b"PNG", "x", "y", "ctx")
    assert got == '{"a":1}'
    assert vcv.vac.get_cached_decision(db, "witness_cache", "hashB", b"PNG", "x", "y", "ctx") is None, (
        "prompt_hash must still be part of the key when routed through the shared factory"
    )


@requires_vision_deps
def test_make_client_sets_an_explicit_request_timeout(monkeypatch):
    """Regression for the 2026-08-06 hung-call incident: a request with no
    timeout can hang forever with no retry ever triggering, since the retry
    loop only fires on a caught exception. Every vision-adjudication
    script's client construction must set
    http_options=types.HttpOptions(timeout=...) - this is the ONE place
    that now does, shared by all three scripts."""
    captured = {}

    class FakeClient:
        def __init__(self, api_key, http_options):
            captured["api_key"] = api_key
            captured["timeout"] = http_options.timeout

    monkeypatch.setattr(vcv.vac.genai, "Client", FakeClient)
    vcv.vac.make_client("test-key", timeout_ms=12345)
    assert captured == {"api_key": "test-key", "timeout": 12345}


@requires_vision_deps
def test_parse_decision_text_prefers_strict_json_first():
    """Strict json.loads must be tried before the regex-based lenient
    extractor: extract_json_fields's unescape doesn't handle a \\uXXXX
    escape (see its own docstring) and would corrupt it into literal text
    (\\u05d0 -> the 5 literal characters 'u05d0') where strict json.loads
    decodes it correctly to the real character. A well-formed response is
    the common case and must never silently take the lossy path - this is
    the exact gap round 4 found in verify_flagged_candidates_vision.py,
    which used to call extract_json_fields directly and skip this tier."""
    text = '{"selected_option": "A", "transcription_found": "test \\u05d0 escape", "confidence": 0.9, "reasoning": "y"}'
    parsed = vcv.parse_decision_text(text)
    assert parsed == json.loads(text)
    assert parsed["transcription_found"] == "test א escape"


@requires_vision_deps
def test_parse_decision_text_falls_back_to_lenient_extraction_on_embedded_quotes():
    text = '''{
      "selected_option": "A",
      "transcription_found": "סי' כ"ה",
      "confidence": 0.93,
      "reasoning": "the crop shows כ\\"ה clearly"
    }'''
    with pytest.raises(json.JSONDecodeError):
        json.loads(text)
    parsed = vcv.parse_decision_text(text)
    assert parsed["selected_option"] == "A"
    assert parsed["transcription_found"] == '''סי' כ"ה'''


@requires_vision_deps
def test_parse_decision_text_raises_when_nothing_recovers_a_decision():
    with pytest.raises(ValueError):
        vcv.parse_decision_text("not json at all, and no recognizable fields either")


@requires_vision_deps
def test_build_client_delegates_to_the_shared_timeout_fixed_constructor(monkeypatch):
    """FOUND round 4: verify_flagged_candidates_vision.py's own client
    construction used to be a bare `genai.Client(api_key=api_key)`, missing
    the explicit request-timeout fix every sibling vision script carries
    (see vision_adjudication_common.make_client) - a second, independent
    instance of the drift class CLAUDE.md Lesson 13 / round 3's
    shared-module finding already documents once (the missing-prompt_hash
    cache-key bug). FIXED by routing through vcv.vac.make_client()."""
    calls = []
    monkeypatch.setattr(vcv.vac, "make_client", lambda api_key: calls.append(api_key) or "the-client")
    result = vfcv.build_client("my-key")
    assert calls == ["my-key"]
    assert result == "the-client"


@requires_vision_deps
def test_adjudicate_one_parses_a_successful_response(monkeypatch):
    monkeypatch.setattr(vcv, "crop_pdf_bounding_box", lambda doc, page, bbox, padding=0.03: b"PNG")
    monkeypatch.setattr(
        vcv, "adjudicate",
        lambda client, crop, a, b, ctx: '{"selected_option":"B","transcription_found":"x",'
                                        '"confidence":0.8,"reasoning":"r"}')
    klalim_by_id = {1: {"clean_text": "א ב ג ד ה"}}
    c = {"klal_id": 1, "word_index": 2, "original": "א", "candidate": "ב", "page": 1, "bbox": {}}
    result = vfcv.adjudicate_one(None, None, klalim_by_id, c)
    assert result["vision_fields"]["selected_option"] == "B"
    assert "error" not in result


@requires_vision_deps
def test_adjudicate_one_records_an_error_instead_of_crashing_the_batch(monkeypatch):
    """FOUND round 4: main()'s loop used to call crop/adjudicate/parse with
    no try/except at all - a single candidate's total failure (e.g. every
    model/retry exhausted) crashed the whole batch and discarded every
    already-adjudicated (already-paid-for) result accumulated so far, since
    results are only written to disk after the loop completes.
    adjudicate_one() must catch that and record an error entry instead."""
    monkeypatch.setattr(vcv, "crop_pdf_bounding_box", lambda doc, page, bbox, padding=0.03: b"PNG")

    def boom(*a, **k):
        raise RuntimeError("All models failed: timeout")

    monkeypatch.setattr(vcv, "adjudicate", boom)
    klalim_by_id = {1: {"clean_text": "א ב ג ד ה"}}
    c = {"klal_id": 1, "word_index": 2, "original": "א", "candidate": "ב", "page": 1, "bbox": {}}
    result = vfcv.adjudicate_one(None, None, klalim_by_id, c)
    assert result["vision_fields"] is None
    assert "All models failed" in result["error"]


# --- corpus_io: the shared file-location/data-loading module ------------------
# Added 2026-08-17 with the module itself. Every test below covers a specific
# divergence that existed between the hand-maintained copies this module
# replaced, not just "the function returns something".

def test_load_klalim_accepts_both_stored_shapes(tmp_path):
    """The wrapper tolerance existed in 2 of 12 readers of these files; the
    other 10 would have raised TypeError on a wrapped file. One
    implementation means the shape is handled the same way everywhere."""
    bare = tmp_path / "bare.json"
    bare.write_text(json.dumps([{"klal_id": 1}]), encoding="utf-8")
    wrapped = tmp_path / "wrapped.json"
    wrapped.write_text(json.dumps({"klalim": [{"klal_id": 1}]}), encoding="utf-8")
    assert cio.load_klalim(str(bare)) == [{"klal_id": 1}]
    assert cio.load_klalim(str(wrapped)) == [{"klal_id": 1}]


def test_save_part1_writes_the_tracked_on_disk_format(tmp_path):
    """ensure_ascii=False + indent=2 is the format part1.json is tracked in,
    not a style choice: a writer that disagreed would rewrite the entire file
    as a diff on every apply. Two scripts (apply_reviewer_decisions.py,
    apply_punctuation_decisions.py) are allowed to write the corpus and each
    had its own copy of this until 2026-08-17."""
    p = tmp_path / "part1.json"
    cio.save_part1([{"klal_id": 1, "clean_text": "\u05d0\u05dc\u05e3 \u05d1\u05d9\u05ea"}], str(p))
    raw = p.read_text(encoding="utf-8")
    assert "\u05d0\u05dc\u05e3" in raw, "Hebrew must be written literally, not escaped"
    assert '\n    "klal_id": 1' in raw, "2-space indent, nested one level inside the list"
    assert json.loads(raw) == [{"klal_id": 1, "clean_text": "\u05d0\u05dc\u05e3 \u05d1\u05d9\u05ea"}]


def test_save_then_load_part1_roundtrips(tmp_path):
    p = tmp_path / "part1.json"
    data = [{"klal_id": 2, "clean_text": "\u05d2 \u05d3"}, {"klal_id": 1, "clean_text": "\u05d0 \u05d1"}]
    cio.save_part1(data, str(p))
    assert cio.load_part1(str(p)) == data, "file order preserved - writers must not reorder"
    assert [k["klal_id"] for k in cio.load_part1_sorted(str(p))] == [1, 2]
    assert set(cio.load_part1_by_id(str(p))) == {1, 2}


def test_load_docai_page_returns_the_callers_default_for_a_missing_page(tmp_path):
    """The nine hand-written copies of this loader disagreed on the
    missing-page answer - some None, one [], one no exists-check at all (it
    raised). Making it an explicit argument is the point of the extraction; a
    caller that branches on `is None` must not silently start seeing []."""
    assert cio.load_docai_page(999, str(tmp_path)) is None
    assert cio.load_docai_page(999, str(tmp_path), default=[]) == []
    (tmp_path / "page_7.json").write_text(json.dumps([{"text": "\u05d0"}]), encoding="utf-8")
    assert cio.load_docai_page(7, str(tmp_path)) == [{"text": "\u05d0"}]


def test_docai_page_cache_loads_each_page_once(tmp_path):
    """The cached variant existed in 4 scripts with identical get-or-load
    bodies. Caching a MISSING page matters as much as caching a present one -
    the naive version re-stats the filesystem for every span that touches a
    page that was never extracted."""
    (tmp_path / "page_3.json").write_text(json.dumps([{"text": "\u05d1"}]), encoding="utf-8")
    cache = cio.DocaiPageCache(str(tmp_path))
    assert cache.get(3) == [{"text": "\u05d1"}]
    (tmp_path / "page_3.json").write_text(json.dumps([{"text": "CHANGED"}]), encoding="utf-8")
    assert cache.get(3) == [{"text": "\u05d1"}], "second get must come from the cache, not disk"
    assert cache.get(99) is None
    assert 99 in cache._pages, "a missing page must be cached too, not re-checked every call"


def test_hebrew_letters_only_matches_the_three_forms_it_replaced():
    """The merged copies were written three different ways - a 27-character
    literal, `re.sub(r"[^<alef>-<tav>]", "", s)`, and a filter over
    validate_part1_corpus_integrity.HEBREW_LETTERS. Equivalence was asserted
    when they were merged; this keeps asserting it, so a future edit to the
    literal that breaks the correspondence fails here rather than silently
    changing what witness-queue indices mean (review_server.py's
    _witness_norm must stay byte-compatible with the stored
    docai_token_index values)."""
    import re as _re
    sample = "\u05d0\u05d1\u05d2 \u05d3\"\u05d4 12 abc \u05df,\u05e5 \u05ea"
    assert cio.hebrew_letters_only(sample) == _re.sub(r"[^\u05d0-\u05ea]", "", sample)
    assert set(cio.HEBREW_LETTERS) == {chr(c) for c in range(0x05D0, 0x05EA + 1)}
    assert set(cio.HEBREW_LETTERS) == set(vpci.HEBREW_LETTERS)


def test_clean_word_keeps_latin_and_digits():
    """Not a Hebrew-only filter, deliberately: the Google Books watermark and
    printed folio numerals must survive clean_word() in order to be
    recognized as page furniture downstream (build_corrections_dataset.
    is_watermark lowercases the result and looks it up)."""
    assert cio.clean_word("Digitized") == "Digitized"
    assert cio.clean_word("\u05e1\u05d9'") == "\u05e1\u05d9"
    assert cio.clean_word("...") == ""
    assert cio.clean_word("41") == "41"


def test_trusted_klal_pages_filters_range_and_trust_and_reports_the_untrusted(tmp_path):
    """CLAUDE.md Lesson 15: an untrusted alignment entry produces SILENCE in
    the candidate pipeline, not a low-confidence flag. build_klal_page_
    regions.py's copy discarded that list; returning it is what lets the
    caller report the silence instead of it being invisible."""
    p = tmp_path / "align.json"
    p.write_text(json.dumps([
        {"klal_id": 2, "trusted": True, "matched_page": 20},
        {"klal_id": 1, "trusted": True, "matched_page": 20},
        {"klal_id": 3, "trusted": False, "matched_page": 21},
        {"klal_id": 900, "trusted": True, "matched_page": 99},
    ]), encoding="utf-8")
    pages, untrusted = cio.trusted_klal_pages(str(p), max_klal=222)
    assert pages == {20: [1, 2]}, "klal_id order within a page must match print order"
    assert untrusted == [3]
    assert 99 not in pages, "out-of-range klal_ids are not Part 1 and must be dropped"


def test_the_pipeline_modules_share_one_part1_max_klal():
    """Three private literals until 2026-08-17. tests/test_corpus_invariants.py
    checks the constant against the live corpus; this checks the sharing
    itself, which that test can no longer distinguish from three copies that
    happen to agree."""
    assert bcd.PART1_MAX_KLAL is cio.PART1_MAX_KLAL
    assert bkpr.PART1_MAX_KLAL is cio.PART1_MAX_KLAL
    assert rs.PART1_MAX_KLAL is cio.PART1_MAX_KLAL


# --- tools/propose_punctuation_part1.py: two code bugs found in the round-4
# --- survey, both instances of the drift class the shared modules exist to close.

@requires_vision_deps
def test_propose_punctuation_client_has_the_shared_request_timeout(monkeypatch):
    """FOUND 2026-08-17: this script built its Gemini client with a bare
    `genai.Client(api_key=...)`, missing the explicit request-timeout applied
    to the three vision scripts after the 2026-08-06 hung-call incident (a
    request that never returned and never raised blocked a run for 20+
    minutes at zero CPU, because the retry loop only fires on a caught
    exception). This is the FOURTH independent instance of that same missing
    fix and the first outside the vision trio - evidence the drift was not
    confined to the files vision_adjudication_common.py was extracted from.
    Routed through make_client() so a fifth copy can't be written."""
    captured = {}

    class FakeClient:
        def __init__(self, api_key, http_options):
            captured["api_key"] = api_key
            captured["timeout"] = http_options.timeout

    monkeypatch.setattr(ppp.vac.genai, "Client", FakeClient)
    ppp.build_client("test-key")
    assert captured["api_key"] == "test-key"
    assert captured["timeout"], "a client with no request timeout can hang forever"


def test_propose_punctuation_model_list_excludes_the_permanently_dead_model():
    """FOUND 2026-08-17: gemini-2.5-flash has permanently 404'd since
    2026-08-05 ("no longer available to new users") - not a transient
    condition. It was dropped from the vision scripts' fallback chain then,
    because a dead model silently eats a retry slot on every fallback path
    instead of ever helping. This script's independently-written copy of the
    list never got that fix."""
    assert "gemini-2.5-flash" not in ppp.MODELS_TO_TRY
    assert ppp.MODELS_TO_TRY == list(vac.adjudicate_with_retry.__defaults__[0]), (
        "the fallback chain should match the shared adjudication loop's, not "
        "be a fourth independently-maintained list"
    )


def test_duplicate_phrase_report_order_is_deterministic():
    """FOUND 2026-08-17 (bug, code) while proving this refactor
    behavior-preserving: check 3 iterated a SET of word tuples, so Python's
    per-process string-hash randomization reordered the report on every run.
    Confirmed empirically at the time - five runs of identical code against
    the identical corpus gave five different orderings of the same lines.
    That defeats this project's standing verification method (diff two runs
    - CLAUDE.md Lesson 19): a real change and pure noise look the same.
    Asserting sorted order here rather than "two calls agree", because two
    calls in ONE process share a hash seed and would agree even with the bug
    present."""
    words = "aa bb cc dd ee ff gg hh ii jj kk ll".split()
    shared_text = " ".join(words)
    klalim = [
        {"klal_id": 1, "title": "\u05d0", "clean_text": shared_text},
        {"klal_id": 2, "title": "\u05d1", "clean_text": shared_text},
    ]
    issues = vpci.check_duplicate_phrases(klalim, n=10)
    assert len(issues) == 3, "12 words, n=10 -> 3 shared 10-grams"
    assert issues == sorted(issues)


# --- pipeline/build_gematria_trace.py: marker location ----------------------
# Added 2026-08-17 with the script. Everything here is synthetic on purpose:
# the real docai_word_boxes/ cache is gitignored and the vision tier needs an
# API key, so a test that leaned on either would be silently skipped exactly
# where this logic is load-bearing. The three matching tiers, the monotonic
# cursor and the position-only page bound are each covered by the concrete
# failure they were written for.

def _tokens(lines, y0=0.10, line_h=0.014, line_gap=0.020,
            x_right=0.89, word_w=0.05, word_gap=0.005, marker_w=0.03):
    """A synthetic scan page: `lines` is a list of word lists, laid out
    right-to-left. The first word of a line lands inside the marker x-band
    (as a real RTL line-initial token does); everything after it does not. A
    word given as ("MARK", text) is laid out narrow, like a numeral glyph.

    Returned in a DELIBERATELY SCRAMBLED array order (reversed within each
    line), because array order is precisely what this module must never
    depend on.
    """
    out = []
    for li, words in enumerate(lines):
        y = y0 + li * line_gap
        x = x_right
        line = []
        for w in words:
            width = marker_w if isinstance(w, tuple) else word_w
            text = w[1] if isinstance(w, tuple) else w
            line.append({"text": text, "x1": round(x - width, 4), "y1": round(y, 4),
                         "x2": round(x, 4), "y2": round(y + line_h, 4)})
            x -= width + word_gap
        out.append(line)
    scrambled = []
    for line in out:
        scrambled.extend(reversed(line))
    return scrambled


def _gklal(klal_id, gematria, opening, title=None):
    return {"klal_id": klal_id, "gematria": gematria, "title": title or opening,
            "clean_text": f"{gematria} {opening}"}


OPENING_A = "אין למדים מן הכללות אפילו במקום שנאמר בהן חוץ"
OPENING_B = "הלכה כדברי המקיל באבל לא אמרינן אלא בחומרא וקולא"


def _loader(pages):
    return lambda p: pages.get(p)


def test_reading_order_ignores_array_order_and_reads_rtl_top_to_bottom():
    """The whole defence against the marker-out-of-reading-order artifact
    confirmed three times in this corpus (klal 3/4, 17/18, 65/66): a marker
    glyph gets array-indexed among the PREVIOUS line's tokens. _tokens()
    scrambles array order on purpose, so a reading_order() that leaked any
    dependence on it fails here."""
    tokens = _tokens([["aleph", "bet"], ["gimel", "dalet"]])
    order = bgt.reading_order(tokens)
    assert [tokens[i]["text"] for i in order] == ["aleph", "bet", "gimel", "dalet"]


def test_reading_order_keeps_a_short_marker_and_a_taller_word_on_one_line():
    """Clustering is on bbox CENTER Y, not y1, because a marginal numeral and
    the bold opening word beside it do not share a y1 - measured 0.007 apart
    on klal 3/4, which is a third of a line."""
    tokens = _tokens([[("MARK", "כב"), "aleph"]])
    tokens[0]["y1"] += 0.006  # the taller bold neighbour starts higher
    order = bgt.reading_order(tokens)
    assert [tokens[i]["text"] for i in order] == ["כב", "aleph"]


def test_near_miss_variants_stay_inside_the_documented_confusion_set():
    variants = set(bgt.near_miss_variants("קפז"))
    assert "קפו" in variants, "ז/ו is confirmed six times in this corpus's own markers"
    assert "קפן" in variants, "ז/ן is confirmed three times"
    assert "קפא" not in variants, (
        "an arbitrary letter substitution turns a precise anchor into a guess "
        "(CLAUDE.md Lesson 5) - only measured confusions belong here"
    )
    assert "קפז" not in variants, "the exact spelling is tier 0, not a variant"


def test_content_match_accepts_the_title_as_a_second_legitimate_opening():
    """220 of 222 Part-1 klalim open with their own title, but where klalim
    share one printed heading (65/66/67) the corpus repeats the shared heading
    in clean_text while the print shows the klal's own line. Only the title
    comparison recovers those, so both forms are scored and the better wins."""
    klal = {"klal_id": 66, "gematria": "סו", "title": OPENING_B,
            "clean_text": "סו " + OPENING_A}
    got = [cio.hebrew_letters_only(w) for w in OPENING_B.split()][:bgt.CONTENT_WORDS]
    ratio, which = bgt.content_match(got, klal)
    assert which == "title" and ratio == 1.0


def test_an_exact_marker_with_matching_opening_is_ok_and_moves_the_cursor():
    pages = {14: _tokens([[("MARK", "כב")] + OPENING_A.split()])}
    record, cursor = bgt.resolve_klal(
        22, _gklal(22, "כב", OPENING_A), (14, -1), 14, _loader(pages), {})
    assert record["status"] == "ok"
    assert record["page"] == 14 and record["content_match_ratio"] == 1.0
    assert cursor is not None
    assert "mechanical-exact" in record["note"]


def test_a_same_numeral_collision_in_running_text_is_rejected_by_the_x_band():
    """The false positive that put klal 3's marker on the `ג` inside the
    citation "בפרק ג'" until it was hand-corrected on 2026-08-05. The
    colliding token here carries the right text but sits mid-line."""
    pages = {14: _tokens([["בפרק", "ג", "filler", "filler"]])}
    record, cursor = bgt.resolve_klal(
        3, _gklal(3, "ג", OPENING_A), (14, -1), 14, _loader(pages), {})
    assert record["status"] == "marker_not_found_in_window"
    assert cursor is None


def test_a_documented_confusion_misread_is_recovered_when_the_opening_agrees():
    """klal 37/47/67/84/87/194 in the real corpus: DocAI emits לו for לז,
    מו for מז, סן for סז, פר for פד, פן for פז, קצר for קצד."""
    pages = {26: _tokens([[("MARK", "לו")] + OPENING_A.split()])}
    record, _ = bgt.resolve_klal(
        37, _gklal(37, "לז", OPENING_A), (26, -1), 26, _loader(pages), {})
    assert record["status"] == "ok"
    assert "documented-confusion" in record["note"]


def test_content_anchored_recovery_finds_a_marker_no_catalogue_covers():
    """klal 16/22/50/63/182: markers misread as פז for טז, כך for כב, ג for
    נ, סוג for סג, קפכ for קפב. Tier 2 does not consult the numeral at all -
    it anchors on the opening words and takes the short marker-band token in
    front of them."""
    pages = {19: _tokens([[("MARK", "פז")] + OPENING_A.split()])}
    record, _ = bgt.resolve_klal(
        16, _gklal(16, "טז", OPENING_A), (19, -1), 19, _loader(pages), {})
    assert record["status"] == "ok"
    assert "content-anchored" in record["note"]
    assert record["marker_position"] is not None


def test_content_anchored_recovery_declines_when_no_marker_token_exists():
    """klal 10 and 57: DocAI emitted no marker token at all. Their opening
    text is right there and matches perfectly, so a content-only rule would
    happily invent a marker out of the previous line's last word. The x-band
    half of tier 2's test is what stops it."""
    pages = {18: _tokens([["tail", "of", "previous", "line"], OPENING_A.split()])}
    record, cursor = bgt.resolve_klal(
        10, _gklal(10, "י", OPENING_A), (18, -1), 18, _loader(pages), {})
    assert record["status"] == "marker_not_found_in_window"
    assert cursor is None


def test_content_anchored_recovery_never_takes_the_previous_klals_marker():
    """A real shape in this corpus: klal 65/66/67 share one printed heading,
    so klal 66's stored clean_text opens with the SAME words that follow klal
    65's marker. Without the cursor guard, tier 2 would anchor there and
    record klal 65's own marker as klal 66's."""
    pages = {34: _tokens([[("MARK", "סה")] + OPENING_A.split()])}
    record, _ = bgt.resolve_klal(
        66, _gklal(66, "סו", OPENING_A), (34, 0), 34, _loader(pages), {})
    assert record["status"] == "marker_not_found_in_window", (
        "the token at the cursor is the PREVIOUS klal's marker and is out of bounds"
    )


def test_a_distant_candidate_is_accepted_only_on_content_not_on_position():
    """THE regression this bound exists for. The first version of this script
    had no page bound on position-only acceptance: klal 10's absent marker
    matched an unrelated margin `י` 37 pages later at content ratio 0.0, the
    monotonic cursor jumped there, and 201 of 222 klalim then reported
    not-found (CLAUDE.md Lesson 6, cascading position failure)."""
    far = {"text": "י", "x1": 0.85, "y1": 0.1, "x2": 0.88, "y2": 0.114}
    pages = {18: _tokens([["unrelated", "text"]]),
             55: [far] + _tokens([["nothing", "to", "do", "with", "klal", "ten"]])}
    record, cursor = bgt.resolve_klal(
        10, _gklal(10, "י", OPENING_A), (18, -1), 55, _loader(pages), {})
    assert record["status"] == "marker_not_found_in_window"
    assert record["page"] == 18, "an unplaced klal reports its SEARCH START, not a guess"
    assert cursor is None, "an unplaced klal must not move the floor for the klalim after it"


def test_a_distant_candidate_whose_opening_agrees_is_still_found():
    """The other half of the same bound, and the reason it is conditional
    rather than absolute: klal 198's real marker sat a full page past where
    the old trace's fixed window stopped, which is why it carried a wrong
    `marker_not_found_in_window` until 2026-08-17. Content agreement is
    independent evidence and exempts a candidate from the page bound."""
    pages = {70: _tokens([["unrelated", "text"]]),
             71: _tokens([[("MARK", "קצח")] + OPENING_B.split()])}
    record, cursor = bgt.resolve_klal(
        198, _gklal(198, "קצח", OPENING_B), (70, -1), 71, _loader(pages), {})
    assert record["status"] == "ok" and record["page"] == 71
    assert cursor is not None


def test_an_exact_marker_whose_stored_text_disagrees_is_flagged_not_blessed():
    """klal 66's real shape: the marker is unmistakably there and correctly
    read, and the corpus's stored text for that klal does not follow it. The
    position is trustworthy, the TEXT is what is in doubt - and a wrong `ok`
    here would be invisible to the boundary pass this trace feeds."""
    pages = {34: _tokens([[("MARK", "סו")]
                          + "completely different words entirely here now".split()])}
    record, cursor = bgt.resolve_klal(
        66, _gklal(66, "סו", OPENING_A), (34, -1), 34, _loader(pages), {})
    assert record["status"] == "marker_found_content_mismatch"
    assert record["marker_position"] is not None, "the position is still recorded"
    assert cursor is not None, "a trusted position still advances the cursor"


def test_the_stored_spelling_counts_as_an_exact_match_not_a_near_miss():
    """part2.json/part3.json store non-final numeral forms (רנ) where the
    canonical spelling and the print both use final forms (רן). A hit on the
    corpus's own spelling is a real glyph match, not a weaker one."""
    pages = {90: _tokens([[("MARK", "רנ")] + OPENING_A.split()])}
    record, _ = bgt.resolve_klal(
        250, _gklal(250, "רנ", OPENING_A), (90, -1), 90, _loader(pages), {})
    assert record["status"] == "ok"
    assert "mechanical-exact" in record["note"]


def test_vision_promotes_a_borderline_candidate_and_a_denial_leaves_it_unplaced():
    """klal 34's shape: a real marker (a documented ד/ו misread) whose
    surrounding OCR is so garbled the opening scores 0.375 - below OK_RATIO,
    above VISION_RATIO_FLOOR. Mocked here, never a live call: a test suite
    that spends API budget is a test suite people stop running."""
    garbled = "אין מישורון גזירה אמות מעצמו אלאס איל קבלה".split()
    pages = {26: _tokens([[("MARK", "לו")] + garbled])}
    klal = _gklal(34, "לד", "אין אדם דן גזירה שוה מעצמו אלא אכ קבלה")
    calls = []

    def confirm(k, cand, tokens):
        calls.append((k["klal_id"], cand.text))
        return True

    record, cursor = bgt.resolve_klal(
        34, klal, (26, -1), 26, _loader(pages), {}, vision_confirm=confirm)
    assert record["status"] == "ok" and "vision" in record["note"]
    assert calls == [(34, "לו")]
    assert cursor is not None

    record, cursor = bgt.resolve_klal(
        34, klal, (26, -1), 26, _loader(pages), {}, vision_confirm=lambda *a: False)
    assert record["status"] == "marker_not_found_in_window"
    assert cursor is None


def test_vision_is_never_consulted_for_an_unambiguous_mechanical_match():
    """Every vision call is real money against a paid API. A confident tier-0
    match with no rival has to be decided mechanically or a full Parts 2-3 run
    costs 445 needless calls."""
    pages = {14: _tokens([[("MARK", "כב")] + OPENING_A.split()])}

    def explode(*_args):  # pragma: no cover - the assertion is that it never runs
        raise AssertionError("vision must not be called for an unambiguous match")

    record, _ = bgt.resolve_klal(
        22, _gklal(22, "כב", OPENING_A), (14, -1), 14, _loader(pages), {},
        vision_confirm=explode)
    assert record["status"] == "ok"


def test_trace_emits_one_record_per_klal_in_id_order_with_the_known_vocabulary():
    pages = {14: _tokens([[("MARK", "א")] + OPENING_A.split(),
                          [("MARK", "ב")] + OPENING_B.split()])}
    records = bgt.trace([_gklal(2, "ב", OPENING_B), _gklal(1, "א", OPENING_A)],
                        14, 14, _loader(pages))
    assert [r["klal_id"] for r in records] == [1, 2]
    assert {r["status"] for r in records} <= {
        "ok", "marker_found_content_mismatch", "marker_not_found_in_window"}
    for r in records:
        assert set(r) >= {"klal_id", "page", "expected_gematria", "stored_gematria",
                          "content_match_ratio", "status", "note"}
        if r["status"] == "marker_not_found_in_window":
            assert "marker_position" not in r and r["content_match_ratio"] is None
        else:
            assert isinstance(r["marker_position"], int)


def test_expected_gematria_comes_from_the_shared_conversion_not_the_stored_field():
    """gematria_trace_part1.json's own expected_gematria is stale for klal
    115/116 (קיה/קיו, from a pre-fix conversion lacking the ט"ו/ט"ז
    exception) and its stored_gematria is stale for klal 150. Deriving
    expected from corpus_io.klal_id_to_gematria on every run is what stops a
    regenerated trace from inheriting that."""
    pages = {14: _tokens([[("MARK", "קטו")] + OPENING_A.split()])}
    record, _ = bgt.resolve_klal(
        115, _gklal(115, "קיה", OPENING_A), (14, -1), 14, _loader(pages), {})
    assert record["expected_gematria"] == "קטו"
    assert record["stored_gematria"] == "קיה", "the stored field is reported, not trusted"


# --- build_gematria_trace: the placeholder-clean_text branch -----------------
# Added here 2026-08-17 (revalidation/refactor round 5). This branch - 72
# lines deciding a DIFFERENT status vocabulary from every other tier - shipped
# with no test of its own, and it is the branch that runs for 115 of the 445
# Parts 2-3 klalim, i.e. most of what a Parts 2-3 run actually exercises.


def _placeholder_klal(klal_id, gematria):
    """A klal whose corpus text was never extracted: clean_text is literally
    "<numeral> כלל <klal_id>" with a matching placeholder title. 115 of the
    445 Parts 2-3 klalim are stored this way (70 in Part 2, 45 in Part 3,
    none in Part 1)."""
    return {"klal_id": klal_id, "gematria": gematria,
            "title": f"כלל {klal_id}", "clean_text": f"{gematria} כלל {klal_id}"}


def test_a_placeholder_klal_has_no_comparable_opening_at_all():
    """"Nothing to compare" and "the content disagrees" are different
    findings. Every matching tier weighs the numeral against the stored
    opening, so without this test the two collapse into one status."""
    assert not bgt.has_comparable_opening(_placeholder_klal(250, "רנ"))
    assert bgt.has_comparable_opening(_gklal(250, "רנ", OPENING_A))


def test_a_placeholder_klals_marker_is_located_but_never_promoted_to_ok():
    """The one thing `ok` asserts - the stored text follows this marker - is
    exactly what cannot be checked when there is no stored text, so a
    placeholder klal is capped at marker_found_content_mismatch however
    convincing its numeral is. A wrong `ok` here would be invisible to the
    boundary pass this trace feeds."""
    pages = {90: _tokens([[("MARK", "רנ")] + OPENING_A.split()])}
    record, cursor = bgt.resolve_klal(
        250, _placeholder_klal(250, "רנ"), (90, -1), 90, _loader(pages), {})
    assert record["status"] == "marker_found_content_mismatch"
    assert record["marker_position"] is not None
    assert record["content_match_ratio"] is None, (
        "a null ratio says 'not comparable'; 0.0 would say 'compared and disagreed'"
    )
    assert "NOT a content disagreement" in record["note"]
    assert cursor is not None, "a located marker still advances the monotonic cursor"


def test_a_placeholder_klal_with_a_misread_numeral_is_left_to_vision():
    """A misread numeral plus a margin position is two signals, not three,
    and the content signal that would normally supply the third does not
    exist here. Mechanically that must stay unplaced; a vision crop reading
    the glyph directly is the only thing allowed to promote it."""
    # ז->ו, the confusion confirmed six times in this corpus's own markers.
    pages = {50: _tokens([[("MARK", "קו")] + OPENING_A.split()])}
    klal = _placeholder_klal(107, "קז")

    record, cursor = bgt.resolve_klal(107, klal, (50, -1), 50, _loader(pages), {})
    assert record["status"] == "marker_not_found_in_window"
    assert cursor is None
    assert "no second signal" in record["note"]

    record, cursor = bgt.resolve_klal(107, klal, (50, -1), 50, _loader(pages), {},
                                      vision_confirm=lambda *a: True)
    assert record["status"] == "marker_found_content_mismatch"
    assert "confirmed by vision crop" in record["note"]
    assert cursor is not None


def test_a_placeholder_klals_misread_numeral_stays_unplaced_when_vision_declines():
    pages = {50: _tokens([[("MARK", "קו")] + OPENING_A.split()])}
    record, cursor = bgt.resolve_klal(
        107, _placeholder_klal(107, "קז"), (50, -1), 50, _loader(pages), {},
        vision_confirm=lambda *a: None)   # could not tell
    assert record["status"] == "marker_not_found_in_window"
    assert cursor is None


# --- build_gematria_trace: two equally convincing candidates -----------------

def test_two_candidates_within_the_ambiguity_margin_go_to_vision_not_to_the_first():
    """Both readings clear OK_RATIO and score within one word of each other,
    so content cannot separate them - taking the earliest silently would be
    a coin flip recorded as a fact. Vision picks, and its pick wins even
    though it is the LATER candidate."""
    pages = {14: _tokens([[("MARK", "כב")] + OPENING_A.split()]),
             15: _tokens([[("MARK", "כב")] + OPENING_A.split()])}
    asked = []

    def confirm(_klal, cand, _tokens):
        asked.append(cand.page)
        return cand.page == 15

    record, _ = bgt.resolve_klal(
        22, _gklal(22, "כב", OPENING_A), (14, -1), 15, _loader(pages), {},
        vision_confirm=confirm)
    assert asked == [14, 15], "every rival is offered to vision in document order"
    assert record["page"] == 15 and record["status"] == "ok"
    assert "sent to vision to disambiguate" in record["note"]


def test_an_ambiguity_with_no_vision_available_says_so_instead_of_hiding_it():
    """Per CLAUDE.md Lesson 1/2, a tool that could not actually decide must
    not report the fallback as if it were a decision."""
    pages = {14: _tokens([[("MARK", "כב")] + OPENING_A.split()]),
             15: _tokens([[("MARK", "כב")] + OPENING_A.split()])}
    record, _ = bgt.resolve_klal(
        22, _gklal(22, "כב", OPENING_A), (14, -1), 15, _loader(pages), {})
    assert record["page"] == 14, "the earliest is taken, per the monotonic cursor"
    assert "NOT disambiguated" in record["note"]


# --- review_server: api_klalim must count word-level ai_flags -------------
# Added 2026-08-17 (code review, heavy-agent refactor pass finding #1): an
# open ai_flag was highlighted in the text pane but invisible to every count
# api_klalim returns - a klal could show "0 open" in the nav while its own
# text pane had a highlighted, undecided AI flag.

def _patch_klalim_deps(monkeypatch, klalim_by_id, ai_flags_by_klal=None,
                        manual_decided=None):
    monkeypatch.setattr(rs, "_load_klalim",
                        lambda: (klalim_by_id, list(klalim_by_id.values())))
    monkeypatch.setattr(rs, "_load_alignment", lambda: {})
    monkeypatch.setattr(rs, "_load_corrections", lambda: {})
    monkeypatch.setattr(rs, "_load_punctuation_candidates", lambda: {})
    monkeypatch.setattr(rs, "_load_witness_queue", lambda: [])
    monkeypatch.setattr(rs.rd, "flagged_klalim", lambda: [])
    manual_decided = manual_decided or {}
    ai_flags_by_klal = ai_flags_by_klal or {}
    # api_klalim counts ai_flags by iterating all_current("klal_flag")
    # directly (not via _word_level_ai_flags), so the "klal_flag" return
    # must carry the same word-level records the ai_flags_by_klal fixture
    # describes. Each ai_flag entry becomes a (klal_id, word_index) ->
    # record in the all_current map, with needs_revisit=True (matching what
    # _word_level_ai_flags filters for in the real code path).
    klal_flag_decided = {}
    for kid, flags in ai_flags_by_klal.items():
        for f in flags:
            klal_flag_decided[(kid, f["word_index"])] = {
                "needs_revisit": True, "word_index": f["word_index"],
            }
    def _mock_all_current(dtype):
        if dtype == "manual_correction":
            return manual_decided
        if dtype == "klal_flag":
            return klal_flag_decided
        return {}
    monkeypatch.setattr(rs.rd, "all_current", _mock_all_current)
    monkeypatch.setattr(rs, "_word_level_ai_flags",
                        lambda kid, words: ai_flags_by_klal.get(kid, []))


def test_api_klalim_counts_an_open_ai_flag_as_machine_disputed(monkeypatch):
    klalim_by_id = {1: {"klal_id": 1, "clean_text": "אלף בית גימל", "page": 1}}
    _patch_klalim_deps(monkeypatch, klalim_by_id,
                        ai_flags_by_klal={1: [{"word_index": 1, "opcode": "ai_flag"}]})
    result = rs.api_klalim()
    row = next(r for r in result if r["klal_id"] == 1)
    assert row["correction_count"] == 1
    assert row["open_count"] == 1
    assert row["machine_disputed_count"] == 1
    assert row["decided_count"] == 0, "an ai_flag has no human decision - must never count as decided"


def test_api_klalim_excludes_an_ai_flag_already_covered_by_a_manual_correction(monkeypatch):
    """Matches api_klal()'s own dedup (bug #1's fix) - once a human has
    acted on the exact word an ai_flag named, the two endpoints must agree
    it's decided, not double-count it as both open and decided."""
    klalim_by_id = {1: {"klal_id": 1, "clean_text": "אלף בית גימל", "page": 1}}
    manual_decided = {(1, 1): {"candidate_snapshot": {"original_word": "בית"},
                                "chosen_text": "בין", "word_index": 1}}
    _patch_klalim_deps(monkeypatch, klalim_by_id,
                        ai_flags_by_klal={1: [{"word_index": 1, "opcode": "ai_flag"}]},
                        manual_decided=manual_decided)
    result = rs.api_klalim()
    row = next(r for r in result if r["klal_id"] == 1)
    assert row["correction_count"] == 1, "the manual correction, not double-counted with the ai_flag it resolved"
    assert row["decided_count"] == 1
    assert row["open_count"] == 0


# --- review_server: api_decision_history must surface a word-level ai_flag's
# --- own history, not report "no decisions recorded" -----------------------

def test_api_decision_history_includes_a_word_level_klal_flag(tmp_path, monkeypatch):
    """FIXED 2026-08-17 (code review): "Show decision history" on an
    ai_flag word used to report "No decisions recorded yet" even though the
    flag itself IS a recorded decision - klal_flag was entirely absent from
    the merge. The klal's GENERAL note (word_index=None) must still never
    leak in here, only this exact word's own flag."""
    path = str(tmp_path / "decisions.jsonl")
    monkeypatch.setattr(rd, "DECISIONS_PATH", path)
    rd.append_decision("klal_flag", 1, needs_revisit=True, note="general note", path=path)
    rd.append_decision("klal_flag", 1, word_index=2, needs_revisit=True,
                        note="w2 flagged by an AI pass", path=path)
    history = rs.api_decision_history(1, 2)
    assert len(history) == 1
    assert history[0]["note"] == "w2 flagged by an AI pass"


# --- review_lexicon_gaps: a 100%-quoted form must never reach ocr_shape ----
# --- even when it also matches a known-confusable near_attested neighbor --

def _lexicon_gap_rec(surface, occurrences=1):
    from collections import Counter
    return {"occurrences": occurrences, "klal_ids": Counter({1: occurrences}),
            "surfaces": Counter({surface: occurrences}), "positions": [(1, 0)] * occurrences}


def test_a_fully_quoted_form_is_an_abbreviation_artifact_not_ocr_shape():
    """FIXED 2026-08-18 (found triaging the Parts 2-3 corpus-expansion
    re-run - see PROJECT-STATUS.md): ocr_shape used to be computed before
    checking all_surfaces_quoted, so a form where EVERY occurrence carries a
    stripped geresh/gershayim (here א"ב, normalising to אב) could still
    satisfy near_attested + known_confusable + zero-attestation - guaranteed
    near-zero, since the reference corpus stores its own abbreviations WITH
    the geresh too - and land in ocr_shape_to_read, the letter-confusion
    bucket, despite having no letter-confusion question to answer at all."""
    rec = _lexicon_gap_rec('א"ב', occurrences=2)
    result = rlg.analyse("אב", rec, lexicon=set(), freq={"אכ": 25})
    assert result["ocr_shape"] is False
    assert result["bucket"] == "abbreviation_artifact"


def test_the_same_near_attested_pattern_without_quoting_still_reaches_ocr_shape():
    """Positive control - the fix must not blunt the real signal for an
    ordinary (unquoted) misread of the same shape."""
    rec = _lexicon_gap_rec("אב", occurrences=2)
    result = rlg.analyse("אב", rec, lexicon=set(), freq={"אכ": 25})
    assert result["ocr_shape"] is True
    assert result["bucket"] == "ocr_shape_to_read"


# --- review_decisions: concurrent appends must not corrupt the file ----------
# _APPEND_LOCK was added 2026-08-18. This test verifies it actually works:
# N threads appending simultaneously must all produce complete, valid JSON lines.

def test_concurrent_appends_produce_no_corrupted_lines(tmp_path):
    """Without the lock, Python's buffered f.write() is not guaranteed to be
    a single write(2) syscall, so two simultaneous appends could interleave
    bytes mid-line. Low risk in practice (single user, browser serialises
    clicks), but a corrupted line in the append-only audit trail is
    unrecoverable and this lock costs zero."""
    import threading

    path = str(tmp_path / "concurrent.jsonl")
    n_threads = 20
    records_per_thread = 10
    errors = []

    def append_n(thread_id):
        try:
            for i in range(records_per_thread):
                rd.append_decision("klal_flag", klal_id=thread_id * 1000 + i,
                                   needs_revisit=True, note=f"t{thread_id}-{i}",
                                   path=path)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=append_n, args=(t,)) for t in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"threads raised: {errors}"

    with open(path, encoding="utf-8") as f:
        lines = [l for l in f if l.strip()]
    assert len(lines) == n_threads * records_per_thread, (
        f"expected {n_threads * records_per_thread} lines, got {len(lines)} - "
        "some appends were lost or interleaved"
    )
    malformed = []
    for i, line in enumerate(lines, 1):
        try:
            r = json.loads(line)
            assert "id" in r and "klal_id" in r
        except (json.JSONDecodeError, AssertionError) as e:
            malformed.append((i, str(e)))
    assert not malformed, f"corrupted line(s): {malformed}"


# --- corpus_io: has_gershayim, QUOTE_CHARS, load_klal_words -----------------
# Added 2026-08-18. These were consolidated from per-script copies; the tests
# verify they agree with the callers that used to define them locally.

def test_has_gershayim_detects_all_quote_forms():
    """has_gershayim must match on every character in QUOTE_CHARS and miss
    on a word with none of them."""
    assert cio.has_gershayim('רש"י') is True    # ASCII double quote
    assert cio.has_gershayim("וכו'") is True    # ASCII single quote
    assert cio.has_gershayim("רש״י") is True    # Unicode gershayim U+05F4
    assert cio.has_gershayim("נרא׳") is True    # Unicode geresh U+05F3
    assert cio.has_gershayim("אלף") is False
    assert cio.has_gershayim("") is False


def test_quote_chars_is_the_canonical_source_for_all_callers():
    """detect_ligature_corruption, detect_real_word_substitution,
    extract_abbreviation_forms, and propose_abbreviation_expansions each had
    their own QUOTE_CHARS copy until consolidation. Verify the canonical set
    matches every downstream user's imported copy."""
    assert cio.QUOTE_CHARS == dlc.QUOTE_CHARS
    assert cio.QUOTE_CHARS == drws.QUOTE_CHARS
    assert cio.QUOTE_CHARS == eaf.QUOTE_CHARS
    assert cio.QUOTE_CHARS == pae.QUOTE_CHARS


def test_load_klal_words_splits_whitespace_collapsing(tmp_path):
    """load_klal_words must use str.split() (whitespace-collapsing), not
    str.split(' ') (space-only), matching every index-bearing pipeline
    script. This was consolidated from detect_ligature_corruption.py and
    detect_real_word_substitution.py."""
    p = tmp_path / "part.json"
    p.write_text(json.dumps([
        {"klal_id": 1, "clean_text": " אלף  בית  גימל "},
        {"klal_id": 2, "clean_text": "דלת הא"},
    ], ensure_ascii=False), encoding="utf-8")
    result = cio.load_klal_words(str(p))
    assert result == {1: ["אלף", "בית", "גימל"], 2: ["דלת", "הא"]}
    # Verify it agrees with the callers' own load_klal_words.
    assert result == dlc.load_klal_words(str(p))
    assert result == drws.load_klal_words(str(p))


# --- vision_adjudication_common: _retry_loop ---------------------------------
# _retry_loop was extracted 2026-08-18. These tests exercise the retry and
# model-fallback behaviour without touching the Gemini API.

@requires_vision_deps
def test_retry_loop_succeeds_on_first_attempt():
    calls = []
    def call_fn(model):
        calls.append(model)
        return f"ok-{model}"
    result = vac._retry_loop(call_fn, ["model-a"], max_retries=3)
    assert result == "ok-model-a"
    assert calls == ["model-a"]


@requires_vision_deps
def test_retry_loop_retries_on_503_and_succeeds():
    attempts = []
    def call_fn(model):
        attempts.append(model)
        if len(attempts) < 3:
            raise RuntimeError("503 Service Unavailable")
        return "recovered"
    result = vac._retry_loop(call_fn, ["model-a"], max_retries=5)
    assert result == "recovered"
    assert len(attempts) == 3


@requires_vision_deps
def test_retry_loop_falls_back_to_next_model_on_non_retryable_error():
    calls = []
    def call_fn(model):
        calls.append(model)
        if model == "model-a":
            raise RuntimeError("400 Bad Request")
        return f"ok-{model}"
    result = vac._retry_loop(call_fn, ["model-a", "model-b"], max_retries=3)
    assert result == "ok-model-b"
    assert calls == ["model-a", "model-b"]


@requires_vision_deps
def test_retry_loop_raises_when_all_models_fail():
    def call_fn(model):
        raise RuntimeError(f"fatal for {model}")
    with pytest.raises(RuntimeError, match="All models failed"):
        vac._retry_loop(call_fn, ["m1", "m2"], max_retries=2)


# --- vision_adjudication_common: table-name assertion -------------------------

@requires_vision_deps
def test_init_cache_table_rejects_sql_metacharacters_in_table_name(tmp_path):
    """The table name is interpolated into SQL (f-strings, not parameterised),
    so it MUST be validated. SQL metacharacters in a table name would allow
    injection via the cache-init call."""
    db = str(tmp_path / "test.db")
    with pytest.raises(AssertionError):
        vac.init_cache_table(db, "bad; DROP TABLE x", "hash1")
    with pytest.raises(AssertionError):
        vac.init_cache_table(db, "Bad_Name", "hash1")  # uppercase
    with pytest.raises(AssertionError):
        vac.init_cache_table(db, "has spaces", "hash1")
    with pytest.raises(AssertionError):
        vac.init_cache_table(db, "", "hash1")
    # A valid name must still work.
    vac.init_cache_table(db, "good_table_name", "hash1")


# --- vision_adjudication_common: parse_decision_lenient ----------------------

@requires_vision_deps
def test_parse_decision_lenient_recovers_valid_response():
    text = '''{
      "selected_option": "A",
      "transcription_found": "אלף בית",
      "confidence": 0.95,
      "reasoning": "clearly readable"
    }'''
    parsed = vac.parse_decision_lenient(text)
    assert parsed["selected_option"] == "A"
    assert parsed["transcription_found"] == "אלף בית"
    assert parsed["confidence"] == 0.95
    assert parsed["reasoning"] == "clearly readable"


@requires_vision_deps
def test_parse_decision_lenient_recovers_response_with_embedded_gershayim():
    """The whole reason this function exists: a raw unescaped gershayim
    inside transcription_found breaks json.loads."""
    text = '''{
      "selected_option": "B",
      "transcription_found": "סי' כ"ה",
      "confidence": 0.9,
      "reasoning": "the gershayim in כ"ה is clear"
    }'''
    parsed = vac.parse_decision_lenient(text)
    assert parsed["selected_option"] == "B"
    assert parsed["transcription_found"] == '''סי' כ"ה'''
    assert parsed["confidence"] == 0.9


@requires_vision_deps
def test_parse_decision_lenient_handles_null_transcription():
    text = '''{
      "selected_option": "UNCERTAIN",
      "transcription_found": null,
      "confidence": 0.5,
      "reasoning": "cannot determine"
    }'''
    parsed = vac.parse_decision_lenient(text)
    assert parsed["selected_option"] == "UNCERTAIN"
    assert parsed["transcription_found"] is None


@requires_vision_deps
def test_parse_decision_lenient_raises_on_unrecoverable_text():
    with pytest.raises(ValueError, match="expected fields not found"):
        vac.parse_decision_lenient("this is not json at all")
    with pytest.raises(ValueError, match="expected fields not found"):
        vac.parse_decision_lenient('{"selected_option": "A"}')  # missing other fields


# --- vision_adjudication_common: sanitize_json --------------------------------

@requires_vision_deps
def test_sanitize_json_strips_invalid_escapes_only():
    """Gemini sometimes emits \\' (invalid in JSON) around a geresh character.
    Valid JSON escapes (\\", \\n, \\\\, etc.) must be left intact."""
    assert vac.sanitize_json(r"test \' value") == "test ' value"
    assert vac.sanitize_json(r'test \" value') == r'test \" value'
    assert vac.sanitize_json(r"test \n value") == r"test \n value"
    # A lone backslash followed by a non-JSON-escape character is stripped.
    assert vac.sanitize_json(r"test \x value") == "test x value"
    assert vac.sanitize_json("no escapes here") == "no escapes here"


# --- review_decisions: all_current supersession + flagged_klalim edge cases ---

def test_all_current_later_record_supersedes_earlier_for_same_key(decisions_path):
    """A later record for the same (klal_id, word_index) must supersede an
    earlier one - the 'current' semantics documented in the module header."""
    rd.append_decision("candidate_choice", klal_id=5, word_index=3,
                       chosen_text="first", path=decisions_path)
    rd.append_decision("candidate_choice", klal_id=5, word_index=3,
                       chosen_text="second", path=decisions_path)
    rd.append_decision("candidate_choice", klal_id=5, word_index=4,
                       chosen_text="other", path=decisions_path)
    current = rd.all_current("candidate_choice", path=decisions_path)
    assert current[(5, 3)]["chosen_text"] == "second"
    assert current[(5, 4)]["chosen_text"] == "other"
    assert len(current) == 2


def test_flagged_klalim_returns_only_klalim_whose_latest_flag_is_needs_revisit(decisions_path):
    """A klal flagged then un-flagged must not appear; a klal flagged,
    un-flagged, then re-flagged must appear."""
    rd.append_decision("klal_flag", klal_id=10, needs_revisit=True, path=decisions_path)
    rd.append_decision("klal_flag", klal_id=20, needs_revisit=True, path=decisions_path)
    rd.append_decision("klal_flag", klal_id=20, needs_revisit=False, path=decisions_path)
    rd.append_decision("klal_flag", klal_id=30, needs_revisit=True, path=decisions_path)
    rd.append_decision("klal_flag", klal_id=30, needs_revisit=False, path=decisions_path)
    rd.append_decision("klal_flag", klal_id=30, needs_revisit=True, path=decisions_path)
    assert rd.flagged_klalim(path=decisions_path) == [10, 30]


def test_flagged_klalim_includes_word_level_flags(decisions_path):
    """A word-level klal_flag (word_index != None) with needs_revisit=True
    should cause the klal to appear in flagged_klalim, since all_current
    keys by (klal_id, word_index) and the function checks needs_revisit
    on every entry. This documents the actual behavior, which the nav
    sidebar relies on."""
    rd.append_decision("klal_flag", klal_id=42, word_index=5, needs_revisit=True,
                       note="word-level flag", path=decisions_path)
    assert 42 in rd.flagged_klalim(path=decisions_path)


# --- apply_reviewer_decisions: confirmed-no-op for replace opcode ------------

def test_confirming_the_current_text_of_a_replace_candidate_changes_nothing(
        apply_harness, decisions_path):
    """A replace candidate where the reviewer votes 'keep current text'
    (chosen_text == final_text) is a confirmed-no-op: the reviewer looked
    at it and decided the current reading is correct. Must NOT modify the
    text, but must record an apply_event."""
    entry = _correction(1, "replace", "בות", "בית")
    apply_harness([{"klal_id": 1, "clean_text": "אלף בית גימל"}], {"1": [entry]})
    rd.append_decision("candidate_choice", klal_id=1, word_index=1, chosen_source="final_text",
                       chosen_text="בית", candidate_snapshot=entry, path=decisions_path)

    assert apply_harness.run()[1] == "אלף בית גימל"
    events = [r for r in rd.history_for(1, 1, "apply_event", path=decisions_path)]
    assert len(events) == 1 and "no change" in (events[0]["note"] or "")


# --- apply_reviewer_decisions: apply_replace with multi-word chosen_text ------

def test_apply_replace_multi_word_replacement():
    """A replace where the chosen text has a different word count from the
    original span - the slice assignment handles this correctly."""
    text = "אלף בית גימל דלת"
    # Replace a 2-word span with a 1-word replacement.
    assert ard.apply_replace(text, 1, "בית גימל", "חדש") == "אלף חדש דלת"
    # Replace a 1-word span with a 2-word replacement.
    assert ard.apply_replace(text, 1, "בית", "חדש ישן") == "אלף חדש ישן גימל דלת"


# --- apply_reviewer_decisions: apply_delete_insertion with multi-word text ----

def test_apply_delete_insertion_multi_word():
    """Insert a multi-word span and verify the already-present guard
    works for multi-word spans too."""
    text = "אלף בית"
    once = ard.apply_delete_insertion(text, 1, "חדש ישן")
    assert once == "אלף חדש ישן בית"
    assert ard.apply_delete_insertion(once, 1, "חדש ישן") is None, (
        "a multi-word insertion already present must be refused"
    )


# --- apply_reviewer_decisions: apply_manual_correction uses space-only split --

def test_apply_manual_correction_uses_space_only_split():
    """apply_manual_correction deliberately uses split(' ') to match the
    frontend's word-index convention. This test verifies that property
    directly - if it ever switches to split(), the indices from the
    frontend's click handler would silently misalign."""
    # With a leading space, split(' ') gives ['', 'אלף', 'בית'] so
    # word_index=1 points to 'אלף'; split() gives ['אלף', 'בית'] so
    # word_index=1 would point to 'בית'. The result should use the
    # space-only split convention.
    text = " אלף בית"
    # With space-only split: words = ['', 'אלף', 'בית']
    # word_index=1 -> 'אלף'
    result = ard.apply_manual_correction(text, 1, "אלף", "חדש")
    assert result == " חדש בית"  # joined back with space-only convention
# --- detect_repeated_words: consecutive word dittography ----------------------

def test_repeated_words_finds_consecutive_duplicate():
    """Basic positive control: an immediately-repeated word is detected."""
    klal_words = {1: ["אלף", "בית", "בית", "גימל"]}
    results = drw.find_repeated_words(klal_words)
    assert len(results) == 1
    assert results[0][:3] == (1, 1, "בית")


def test_repeated_words_ignores_legitimate_repeats():
    """Words in LEGITIMATE_REPEATS must be excluded from findings."""
    klal_words = {1: ["אי", "תניא", "תניא", "מדברי"]}
    results = drw.find_repeated_words(klal_words)
    assert results == [], "תניא תניא is a legitimate Talmudic phrase"


def test_repeated_words_compares_hebrew_letters_only():
    """A gershayim difference between adjacent words must not prevent
    detection: 'ב' followed by "ב'" is still a repeated word."""
    klal_words = {1: ["דף", "ב", "ב'", "ד\"ה"]}
    results = drw.find_repeated_words(klal_words)
    assert len(results) == 1


def test_repeated_words_skips_empty_hebrew():
    """Adjacent punctuation-only tokens must not be flagged as repeats."""
    klal_words = {1: ["אלף", "[.]", "[.]", "בית"]}
    results = drw.find_repeated_words(klal_words)
    assert results == [], "punctuation-only tokens have no Hebrew content to compare"


# --- detect_insertion_deletion: single-char insertion/deletion ----------------

def test_insertion_deletion_finds_extra_char():
    """A word with zero attestation, one char deletion away from a common word,
    resolves as high-confidence extra_char."""
    indep_freq = {"הלכה": 2290, "הלכרה": 0}
    result = did._resolve("הלכרה", indep_freq)
    assert result is not None
    is_ambiguous, options = result
    assert not is_ambiguous
    assert options[0][0] == "הלכה"
    assert options[0][1] == "extra_char"


def test_insertion_deletion_finds_deleted_char():
    """A word with zero attestation, one char insertion away from a common word,
    resolves as deleted_char."""
    indep_freq = {"ילפנן": 0, "ילפינן": 500}
    result = did._resolve("ילפנן", indep_freq)
    assert result is not None
    is_ambiguous, options = result
    assert options[0][0] == "ילפינן"
    assert options[0][1] == "deleted_char"


def test_insertion_deletion_requires_zero_attestation():
    """A word with ANY independent attestation must not be flagged."""
    indep_freq = {"חזות": 5, "חזו": 312}
    result = did._resolve("חזות", indep_freq)
    assert result is None


def test_insertion_deletion_skips_short_words():
    """Words shorter than MIN_WORD_LENGTH must be skipped - too many
    coincidental single-edit neighbours for short Hebrew words."""
    indep_freq = {"אב": 0, "אבי": 500}
    result = did._resolve("אב", indep_freq)
    assert result is None, "2-letter words should be skipped"


def test_insertion_deletion_skips_prefix_position():
    """Inserting or removing a common prefix letter at position 0 should be
    skipped - that's a prefix-detection problem, not an OCR error."""
    # "אמרי" with zero attestation, "ואמרי" (with ו prefix) common - but
    # this should NOT fire because ו at position 0 is a known prefix.
    indep_freq = {"אמרי": 0, "ואמרי": 800, "האמרי": 600}
    result = did._resolve("אמרי", indep_freq)
    # Should return None because the only candidates are prefix insertions
    assert result is None, "prefix insertions at position 0 should be skipped"


# --- detect_split_merge: word-split and word-merge errors ---------------------

def test_merge_detector_finds_split():
    """A rare unattested word that splits into two common halves is detected."""
    indep_freq = {"אביי": 2973, "והא": 2500, "אבייוהא": 0}
    result = dsm._resolve_merge("אבייוהא", indep_freq)
    assert result is not None
    left, right, lf, rf = result
    assert left == "אביי" and right == "והא"


def test_merge_detector_requires_both_halves_common():
    """If only one half is common, no merge candidate should be produced."""
    indep_freq = {"אביי": 2973, "זקש": 0, "אבייזקש": 0}
    result = dsm._resolve_merge("אבייזקש", indep_freq)
    assert result is None


def test_merge_detector_requires_minimum_length():
    """Words shorter than MIN_MERGE_LENGTH should not be candidates."""
    indep_freq = {"אב": 500, "גד": 500, "אבגד": 0}
    result = dsm._resolve_merge("אבגד", indep_freq)
    assert result is None, "4-letter word is below MIN_MERGE_LENGTH=7"


def test_split_detector_finds_adjacent_short_tokens():
    """Two adjacent short tokens whose concatenation is common are detected."""
    from collections import Counter
    klal_words = {1: ["דף", "ב", "ת", "גימל"]}
    own_counts = Counter({"דף": 50, "ב": 1, "ת": 1, "גימל": 50})
    indep_freq = {"בת": 5000}
    results = dsm.find_split_candidates(klal_words, own_counts, indep_freq)
    assert len(results) == 1
    assert results[0][4] == "בת"  # the concatenation


# --- detect_cross_klal_errors: systematic patterns across klalim --------------

def test_cross_klal_finds_repeated_unattested_form():
    """A form appearing in >= MIN_KLALIM klalim with zero attestation is flagged."""
    klal_words = {1: ["טרור"], 2: ["טרור"], 3: ["טרור"], 4: ["בית"]}
    lexicon = set()
    indep_freq = {"טרור": 0, "בית": 5000}
    results = dcke.find_cross_klal_suspects(klal_words, lexicon, indep_freq)
    assert len(results) == 1
    assert results[0][0] == "טרור"
    assert results[0][1] == 3  # 3 klalim


def test_cross_klal_skips_attested_forms():
    """A form with independent attestation must not be flagged even if it
    appears in many klalim."""
    klal_words = {1: ["בית"], 2: ["בית"], 3: ["בית"]}
    lexicon = set()
    indep_freq = {"בית": 5000}
    results = dcke.find_cross_klal_suspects(klal_words, lexicon, indep_freq)
    assert results == []


def test_cross_klal_skips_gershayim_tokens():
    """Abbreviation tokens must not be counted."""
    klal_words = {1: ['א"א'], 2: ['א"א'], 3: ['א"א']}
    lexicon = set()
    indep_freq = {}
    results = dcke.find_cross_klal_suspects(klal_words, lexicon, indep_freq)
    assert results == []
