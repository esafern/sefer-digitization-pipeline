# [PRODUCTION] Does tests/fixtures/build_fixture_corpus.py actually produce
# what its own docstring and fixture_book.py's header claim it does? A
# fixture nobody verifies against its own claims is exactly Lesson 1's shape
# one level up: a check that exists but was never run has verified nothing,
# and a GENERATOR nobody checked the output of is the same defect in the
# thing meant to make every other check book-independent.
#
# Pure-Python and structural (via `use_fixture_corpus` - no server, no
# browser): these assert the ON-DISK SHAPE the generator produced, one test
# per condition in fixture_book.py's own list, in the same order.
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pipeline"))

import corpus_io as cio  # noqa: E402
import review_decisions as rd  # noqa: E402
import review_counts as rcount  # noqa: E402


def test_a_klal_spans_a_page_break(use_fixture_corpus):
    regions = cio.load_json(cio.repo_path("klal_page_regions.json"))
    assert regions["1"]["page"] == 1
    assert regions["1"]["continuations"][0]["page"] == 2


def test_a_word_on_a_continuation_page_is_not_on_its_klals_start_page(use_fixture_corpus):
    klal1 = cio.load_part1_by_id()[1]
    words = cio.words_of(klal1)
    # words 5-7 ("גימל", "דלת", "הא") are the page-2 continuation.
    assert words[5:8] == ["גימל", "דלת", "הא"]
    regions = cio.load_json(cio.repo_path("klal_page_regions.json"))
    assert regions["1"]["page"] == 1
    assert regions["1"]["continuations"][0]["page"] == 2


def test_two_identical_adjacent_words(use_fixture_corpus):
    klal1 = cio.load_part1_by_id()[1]
    words = cio.words_of(klal1)
    assert words[2] == words[3] == "בית"


def test_an_editorial_mark(use_fixture_corpus):
    klal1 = cio.load_part1_by_id()[1]
    assert cio.words_of(klal1)[4] == "[.]"


def test_every_title_has_a_terminal_period(use_fixture_corpus):
    for k in cio.load_part1():
        assert (k.get("title") or "").endswith("."), k


def test_a_human_decision_manual_correction(use_fixture_corpus, fixture_decisions_path):
    rec = rd.all_current("manual_correction", path=fixture_decisions_path).get((2, 3))
    assert rec is not None
    assert rec["reviewer"] == "local"
    assert rec["chosen_text"] == "חית"


def test_a_punctuation_candidate(use_fixture_corpus):
    candidates = cio.load_json(cio.repo_path("punctuation_candidates_part1.json"))
    assert candidates["2"][0]["before_word_index"] == 2


def test_both_machine_resolved_flags(use_fixture_corpus):
    corrections = cio.load_json(cio.repo_path("corrections_part1.json"))
    flags = {row["flag"] for row in corrections["2"]}
    assert "current_text_confirmed" in flags
    assert "docai_ligature_artifact" in flags
    for row in corrections["2"]:
        if row["flag"] in rcount.MACHINE_RESOLVED_FLAGS:
            # NOT docai_reading == final_text - checked against the real corpus
            # while building this fixture: "current_text_confirmed" means
            # vision confirmed the STORED text over docai's actual (different)
            # reading, not that docai read the stored word back verbatim. An
            # engine genuinely not consulted reads null, never the corpus's
            # own word - test_no_corrections_item_attributes_the_stored_text_
            # to_an_engine is the gated version of this same assertion.
            assert row["docai_reading"] not in (None, row["final_text"])
            assert row["vision_selected"] is not None


def test_a_word_level_ai_flag_left_open(use_fixture_corpus, fixture_decisions_path):
    flags = rd.all_current("klal_flag", path=fixture_decisions_path)
    rec = flags.get((3, 2))
    assert rec is not None and rec["needs_revisit"] is True
    decided = rd.all_current("candidate_choice", path=fixture_decisions_path)
    manual = rd.all_current("manual_correction", path=fixture_decisions_path)
    assert rcount.flag_still_open(3, 2, rec, decided, manual) is True


def test_an_answered_flag_standing_alone(use_fixture_corpus, fixture_decisions_path):
    flags = rd.all_current("klal_flag", path=fixture_decisions_path)
    rec = flags.get((3, 3))
    assert rec is not None
    decided = rd.all_current("candidate_choice", path=fixture_decisions_path)
    manual = rd.all_current("manual_correction", path=fixture_decisions_path)
    assert rcount.flag_still_open(3, 3, rec, decided, manual) is False, (
        "the manual_correction recorded after this flag must answer it"
    )


def test_a_possible_omission_at_len_words(use_fixture_corpus):
    klal3 = cio.load_part1_by_id()[3]
    n = len(cio.words_of(klal3))
    corrections = cio.load_json(cio.repo_path("corrections_part1.json"))
    row = next(r for r in corrections["3"] if r["flag"] == "possible_omission")
    assert row["word_index"] == n, "the omission must sit exactly at the end of the klal"
    assert row["opcode"] == "delete"


def test_two_candidates_collide_at_one_index(use_fixture_corpus):
    """See build_fixture_corpus.py's own comment on this pair: ONE delete, one
    replace, not two deletes - a gated invariant (item 0AU) forbids two GAPS
    ever sharing a key, and tripping it was how this shape got corrected."""
    corrections = cio.load_json(cio.repo_path("corrections_part1.json"))
    at_index_1 = [r for r in corrections["3"] if r["word_index"] == 1]
    assert len(at_index_1) == 2
    assert {r["opcode"] for r in at_index_1} == {"delete", "replace"}


def test_witness_rows_with_and_without_a_word_index(use_fixture_corpus):
    queue = cio.load_json(cio.repo_path("reconstruction_witness_queue.json"))["queue"]
    klal4 = [r for r in queue if r["klal_id"] == 4]
    assert any("word_index" in r for r in klal4)
    assert any("word_index" not in r for r in klal4)


def test_the_fixture_corpus_passes_its_own_preflight(fixture_server):
    """The one end-to-end check that everything above actually assembles into
    a server that starts and answers - not just that the files are individually
    well-shaped."""
    import urllib.request
    with urllib.request.urlopen(fixture_server + "/api/klalim") as resp:
        klalim = json.loads(resp.read())
    assert {k["klal_id"] for k in klalim} == {1, 2, 3, 4}
