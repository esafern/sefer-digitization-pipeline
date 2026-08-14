#!/usr/bin/env python3
# [STANDALONE] Read-only audit: for every review-dashboard decision the
# audit trail claims was "applied" (has an apply_event referencing its own
# id, per review_decisions.applied_decision_ids()), does part1.json's LIVE
# content still actually reflect it?
#
# Built 2026-08-14 (PROJECT-STATUS.md audit item 1: "an apply_event is
# never invalidated when its underlying decision is later reverted outside
# the normal flow"). applied_decision_ids()'s own docstring says this
# deliberately: "an applied decision is identified by id, not inferred from
# whether the text happens to still look un-applied" - sound design AS LONG
# AS part1.json is only ever mutated through apply_reviewer_decisions.py /
# apply_punctuation_decisions.py. If it's ever hand-reverted outside that
# flow instead (documented precedent: klal 1 word 97, 2026-08-10 - an
# accepted punctuation decision was applied, then explicitly hand-reverted
# and the reversal recorded as a fresh "reject" decision rather than
# through the apply script, see review_decisions.jsonl ids 784b22672ac0/
# 4759be432a2c/4e6b53d98d36), the apply_event becomes a permanent claim
# that stopped being true, and nothing in the pipeline ever re-checks it.
# This script is that re-check - it changes nothing, only reports.
#
# Only checks the LATEST decision per (klal_id, word_index, decision_type)
# key, and only when THAT decision itself has an apply_event (a "pending,
# not yet applied" latest decision - e.g. a reject with nothing to apply,
# or a genuinely queued-but-unrun decision - is not a claim about the
# corpus and is correctly not checked here).
#
# LIMITATION, stated rather than papered over: word-count-changing
# decisions (insert/delete opcodes, a manual deletion, an accepted
# punctuation mark) shift every later word_index in the same klal for every
# OTHER decision applied after them. Verifying one such decision's position
# in isolation, long after the fact, can't distinguish "silently reverted"
# from "correctly applied, then shifted by a later legitimate edit" -
# doing so would produce false positives, not real findings. Those are
# reported separately as unverifiable-by-position, not silently treated as
# passing.
import json
import os

import review_decisions as rd

REPO = os.path.dirname(os.path.abspath(__file__))
PART1_PATH = os.path.join(REPO, "part1.json")


def load_part1():
    with open(PART1_PATH, encoding="utf-8") as f:
        return {k["klal_id"]: k for k in json.load(f)}


def check_candidate_choice(decision, klal):
    snapshot = decision.get("candidate_snapshot") or {}
    opcode = snapshot.get("opcode")
    word_index = decision["word_index"]
    if opcode != "replace":
        return "unverifiable_word_count_change"
    words = klal["clean_text"].split()
    final_text = snapshot.get("final_text")
    span_len = len(final_text.split()) if final_text else 1
    chosen = decision["chosen_text"]
    expected = chosen.split() if chosen else []
    n = len(expected) if expected else span_len
    live = words[word_index:word_index + n]
    if live == expected:
        return "ok"
    return f"MISMATCH: expected {expected!r} at word_index {word_index}, found {live!r}"


def check_manual_correction(decision, klal):
    if decision["chosen_text"] == "":
        return "unverifiable_word_count_change"
    words = klal["clean_text"].split(" ")
    word_index = decision["word_index"]
    chosen = decision["chosen_text"]
    if word_index >= len(words):
        return f"MISMATCH: word_index {word_index} out of range (klal now has {len(words)} words)"
    live = words[word_index]
    if live == chosen:
        return "ok"
    return f"MISMATCH: expected {chosen!r} at word_index {word_index}, found {live!r}"


def check_punctuation_choice(decision, klal):
    if decision["chosen_source"] != "accept":
        return "unverifiable_word_count_change"  # reject never inserts anything to verify
    words = klal["clean_text"].split(" ")
    word_index = decision["word_index"]
    if word_index >= len(words):
        return f"MISMATCH: word_index {word_index} out of range (klal now has {len(words)} words)"
    live = words[word_index]
    if live == "[.]":
        return "ok"
    return f"MISMATCH: expected '[.]' at word_index {word_index}, found {live!r}"


CHECKERS = {
    "candidate_choice": check_candidate_choice,
    "manual_correction": check_manual_correction,
    "punctuation_choice": check_punctuation_choice,
}


def main():
    part1 = load_part1()
    already_applied = rd.applied_decision_ids()

    n_ok = n_mismatch = n_unverifiable = n_missing_klal = 0
    mismatches = []

    for decision_type, checker in CHECKERS.items():
        current = rd.all_current(decision_type)
        for (klal_id, word_index), decision in sorted(current.items()):
            if decision["id"] not in already_applied:
                continue  # latest decision at this key was never applied - nothing to verify
            klal = part1.get(klal_id)
            if klal is None:
                n_missing_klal += 1
                mismatches.append(f"klal {klal_id} word {word_index} ({decision_type}): "
                                   f"klal_id not found in part1.json at all")
                continue
            result = checker(decision, klal)
            if result == "ok":
                n_ok += 1
            elif result == "unverifiable_word_count_change":
                n_unverifiable += 1
            else:
                n_mismatch += 1
                mismatches.append(f"klal {klal_id} word {word_index} ({decision_type}, "
                                   f"decision {decision['id']}): {result}")

    print(f"Checked {n_ok + n_mismatch + n_unverifiable + n_missing_klal} applied decisions "
          f"across candidate_choice/manual_correction/punctuation_choice:")
    print(f"  {n_ok} confirmed still reflected in part1.json")
    print(f"  {n_unverifiable} word-count-changing, not position-verifiable post-hoc (see docstring)")
    print(f"  {n_mismatch + n_missing_klal} MISMATCH - applied decision no longer reflected in the corpus")
    if mismatches:
        print()
        for m in mismatches:
            print(f"  {m}")


if __name__ == "__main__":
    main()
