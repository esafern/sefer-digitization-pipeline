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
# Checks EVERY id in applied_decision_ids(), not just the latest decision
# per (klal_id, word_index, decision_type) key. FIXED 2026-08-14 (code
# review found this the same day the script was written): the first
# version iterated all_current(decision_type) and only checked a decision
# if IT was the latest at its key AND had an apply_event - which meant an
# OLDER applied decision superseded by a NEWER, never-applied one (a
# reject, or a decision still pending) was silently skipped entirely. That
# is EXACTLY the klal 1 word 97 precedent this script's docstring names as
# its motivation: the accept (784b22672ac0) was applied, then super-
# seded-at-key by a reject (4e6b53d98d36) that was itself never applied -
# the old logic checked neither, so the "0 mismatches" the first version
# reported on real data was not evidence that precedent was fine; the
# script structurally could not see it. Now resolves every applied id via
# find_by_id and checks it UNLESS a STRICTLY LATER decision at the same
# key has ALSO been applied (is_superseded_by_later_applied) - that case
# is a normal, expected supersession (a legitimate later apply changed the
# text away from the older claim, not a bug), so checking the older one
# there would always "mismatch" for the ordinary reason a newer value
# overwrote it. A later decision that was never itself applied does NOT
# suppress the check - the older applied decision's claim is still
# standing and gets verified, which is what correctly catches the klal 1
# word 97 case now (part1.json has no [.] there; the accept's apply_event
# claim no longer holds).
#
# LIMITATION, stated rather than papered over: word-count-changing
# decisions (insert/delete opcodes, an empty-chosen_text replace/manual
# deletion, an accepted punctuation mark) shift every later word_index in
# the same klal for every OTHER decision applied after them. Verifying one
# such decision's position in isolation, long after the fact, can't
# distinguish "silently reverted" from "correctly applied, then shifted by
# a later legitimate edit" - doing so would produce false positives, not
# real findings. Those are reported separately as unverifiable-by-position,
# not silently treated as passing.
import corpus_io as cio
import review_decisions as rd

# Moved one level deeper (pipeline/ or tools/) 2026-08-16 - REPO now goes up
# two levels, not one, to keep resolving to the actual repo root where
# part1.json/docai_word_boxes/etc. live.
REPO = cio.REPO
PART1_PATH = cio.PART1_PATH


def load_part1():
    return cio.load_part1_by_id(PART1_PATH)


def check_candidate_choice(decision, klal):
    """FIXED 2026-08-14 (code review, finding 10): an empty chosen_text
    (the reviewer's "remove this word" answer, recorded as chosen_source
    "custom" with text "") used to fall through to the normal position
    check with expected=[] and no bounds check - words[word_index:...] on
    an out-of-range index returns [] in Python (no IndexError), so it
    silently compared [] == [] and reported "ok" having verified nothing.
    An empty chosen_text is a word-count change like insert/delete, not a
    same-position replace - route it to unverifiable_word_count_change
    like check_manual_correction already does for the same case. The
    explicit bounds check below is defense-in-depth, not just reliant on
    this routing to avoid the slicing trap. (Both other checkers had only
    the upper half of that bounds check until 2026-08-14, despite this
    docstring already claiming parity with them - a negative index silently
    reads backwards from the end in Python rather than raising.)"""
    snapshot = decision.get("candidate_snapshot") or {}
    opcode = snapshot.get("opcode")
    chosen = decision["chosen_text"]
    if opcode != "replace" or not chosen:
        return "unverifiable_word_count_change"
    words = klal["clean_text"].split()
    word_index = decision["word_index"]
    expected = chosen.split()
    if word_index < 0 or word_index >= len(words):
        return f"MISMATCH: word_index {word_index} out of range (klal now has {len(words)} words)"
    live = words[word_index:word_index + len(expected)]
    if live == expected:
        return "ok"
    return f"MISMATCH: expected {expected!r} at word_index {word_index}, found {live!r}"


def check_manual_correction(decision, klal):
    if decision["chosen_text"] == "":
        return "unverifiable_word_count_change"
    words = klal["clean_text"].split(" ")
    word_index = decision["word_index"]
    chosen = decision["chosen_text"]
    # `word_index < 0` matters as much as the upper bound: Python indexes
    # backwards from the end rather than raising, so a negative index would
    # silently compare against the klal's LAST word and could report a
    # confident "ok". check_candidate_choice's docstring already claimed
    # this bounds check was "matching the other two checkers" - it wasn't;
    # both this and check_punctuation_choice only had the upper half.
    if word_index < 0 or word_index >= len(words):
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
    if word_index < 0 or word_index >= len(words):
        return f"MISMATCH: word_index {word_index} out of range (klal now has {len(words)} words)"
    live = words[word_index]
    if live == "[.]":
        return "ok"
    return f"MISMATCH: expected '[.]' at word_index {word_index}, found {live!r}"


# FIXED 2026-08-23 (code review, finding C4): "disputed_choice" is what
# review_server.py has recorded the dashboard's word decisions as since the
# 2026-08-23 candidate->disputed rename; "candidate_choice" is the same
# decision under its pre-rename name and both still occur in the log.
# review_decisions._match_decision_types() aliases the two for
# all_current()/history_for(), so apply_reviewer_decisions.py and
# export_corpus.py picked the new type up automatically - this dict did
# not, and CHECKERS.get() returning None hits a bare `continue` below, so
# every decision recorded after the rename was silently skipped by the one
# read-only check that exists to catch an applied decision no longer
# reflected in the corpus. Both names map to the same checker: the rename
# changed the label, not the record's shape.
CHECKERS = {
    "disputed_choice": check_candidate_choice,
    "candidate_choice": check_candidate_choice,
    "manual_correction": check_manual_correction,
    "punctuation_choice": check_punctuation_choice,
}


def is_superseded_by_later_applied(decision, already_applied):
    """True if some decision recorded AFTER `decision` at the same
    (klal_id, word_index, decision_type) key has itself been applied -
    meaning the live corpus has legitimately moved past `decision`'s claim
    via a normal, later apply step, not an out-of-band revert. Checking a
    legitimately-superseded decision's claim against live text would
    always "mismatch" for the ordinary, expected reason that a newer
    value overwrote it - not the bug this script exists to catch. A later
    decision that was never itself applied does NOT count: the older
    applied decision's claim is still the standing one and must be
    checked (this is the klal 1 word 97 case - see module docstring)."""
    history = rd.history_for(decision["klal_id"], decision["word_index"], decision["decision_type"])
    seen_self = False
    for r in history:
        if r["id"] == decision["id"]:
            seen_self = True
            continue
        if seen_self and r["id"] in already_applied:
            return True
    return False


def main():
    part1 = load_part1()
    already_applied = rd.applied_decision_ids()

    n_ok = n_mismatch = n_unverifiable = n_missing_klal = n_superseded = 0
    mismatches = []

    for decision_id in sorted(already_applied):
        decision = rd.find_by_id(decision_id)
        if decision is None:
            continue  # defensive: an apply_event referencing an id not in the log at all
        decision_type = decision["decision_type"]
        checker = CHECKERS.get(decision_type)
        if checker is None:
            continue  # not one of the 3 checkable decision types
        klal_id, word_index = decision["klal_id"], decision["word_index"]

        if is_superseded_by_later_applied(decision, already_applied):
            n_superseded += 1
            continue

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
                               f"decision {decision_id}): {result}")

    total = n_ok + n_mismatch + n_unverifiable + n_missing_klal + n_superseded
    print(f"Checked {total} applied decisions across "
          f"{'/'.join(sorted(CHECKERS))}:")
    print(f"  {n_ok} confirmed still reflected in part1.json")
    print(f"  {n_superseded} superseded by a later, also-applied decision at the same key (expected, not checked)")
    print(f"  {n_unverifiable} word-count-changing, not position-verifiable post-hoc (see docstring)")
    print(f"  {n_mismatch + n_missing_klal} MISMATCH - applied decision no longer reflected in the corpus")
    if mismatches:
        print()
        for m in mismatches:
            print(f"  {m}")


if __name__ == "__main__":
    main()
