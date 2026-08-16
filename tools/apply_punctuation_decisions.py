#!/usr/bin/env python3
# [PRODUCTION] Promotes accepted punctuation-review decisions into
# part1.json, mirroring apply_reviewer_decisions.py's separate-deliberate-
# step pattern (nothing silently mutates part1.json; every change is a
# deliberate, verified, logged step - see PROJECT-STATUS.md "Review
# dashboard rearchitecture").
#
# Usage: python3 apply_punctuation_decisions.py [--dry-run]
#
# Safety model:
#   - Only the LATEST punctuation_choice decision per (klal_id,
#     before_word_index) is considered (review_decisions.all_current) -
#     rejects and superseded decisions are never applied.
#   - Before applying, re-checks punctuation_candidates_part1.json's
#     current entry for that (klal_id, before_word_index): the flanking
#     words (word_before/word_after) must still match the decision's own
#     candidate_snapshot. If they don't, the corpus moved since the
#     decision was made - skip and report, never guess.
#   - Unlike apply_reviewer_decisions.py's insert/delete opcodes, a "[.]"
#     insertion here doesn't depend on any OTHER pending punctuation
#     decision in the same klal (each candidate was proposed independently
#     against a fixed clean_text snapshot), so ALL accepted decisions for
#     a klal can be applied in one run - just in DESCENDING word_index
#     order, so inserting one doesn't shift the position of another one
#     still to be applied in the same pass.
#   - Applying still changes word count for the klal, which DOES
#     invalidate that klal's corrections_part1.json word_index entries
#     (a completely different candidate system) until ./rebuild_all.sh
#     regenerates them fresh - printed as an explicit next step, and any
#     klal touched here is worth a second look in the corrections queue
#     after the rebuild.
#   - Every applied decision gets its own apply_event row in the same
#     decisions log.
#   - Never invokes rebuild_all.sh itself.
import argparse
import json
import os
import sys

# Moved one level deeper (pipeline/ or tools/) 2026-08-16 - REPO now goes up
# two levels, not one, to keep resolving to the actual repo root where
# part1.json/docai_word_boxes/etc. live.
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# review_decisions.py lives in pipeline/, not tools/ - this is the one
# cross-directory import in the whole reorg (apply_reviewer_decisions.py
# and audit_applied_decisions.py, this script's siblings in spirit, both
# live IN pipeline/ alongside review_decisions.py and need no such fix;
# this script stayed in tools/ with its propose-script pair per the
# approved layout, so it needs pipeline/ added to sys.path explicitly
# rather than getting it for free the way same-directory imports do).
sys.path.insert(0, os.path.join(REPO, "pipeline"))
import review_decisions as rd  # noqa: E402

PART1_PATH = os.path.join(REPO, "part1.json")
CANDIDATES_PATH = os.path.join(REPO, "punctuation_candidates_part1.json")


def load_part1():
    with open(PART1_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_part1(data):
    with open(PART1_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_candidates():
    if not os.path.exists(CANDIDATES_PATH):
        return {}
    with open(CANDIDATES_PATH, encoding="utf-8") as f:
        return json.load(f)


def snapshot_matches(snapshot, live_entry):
    if snapshot is None or live_entry is None:
        return False
    keys = ("before_word_index", "word_before", "word_after")
    return all(snapshot.get(k) == live_entry.get(k) for k in keys)


def corpus_matches(snapshot, words):
    """The check that actually matters: do the words CURRENTLY sitting either
    side of this index in part1.json still match what the reviewer saw?

    snapshot_matches() above compares the decision against
    punctuation_candidates_part1.json - but that file is frozen (nothing
    regenerates it) and the snapshot was copied from it, so the two agree by
    construction no matter what happened to the corpus. It is a tautology, not
    a drift check. Confirmed 2026-08-11 (PROJECT-STATUS.md "Deep methodology
    audit"): inserting an unrelated word earlier in klal 1 and then applying
    the index-97 decision reported success and placed the mark one word off,
    because nothing ever compared word_before/word_after - which the candidate
    generator stores for exactly this purpose - against the live text."""
    idx = snapshot.get("before_word_index")
    if not isinstance(idx, int) or not (0 < idx <= len(words)):
        return False
    before_ok = words[idx - 1] == snapshot.get("word_before")
    # idx == len(words) means "append at the very end": there is no word after.
    after_ok = (idx == len(words)) or (words[idx] == snapshot.get("word_after"))
    return before_ok and after_ok


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="report what would happen, change nothing")
    args = parser.parse_args()

    decisions = rd.all_current("punctuation_choice")
    candidates = load_candidates()
    part1 = load_part1()
    by_klal = {k["klal_id"]: k for k in part1}

    # only accepted decisions insert anything; group by klal, descending
    # word_index within each klal so an earlier insertion never shifts the
    # position of one still to be applied in this same run.
    already_applied = rd.applied_decision_ids()

    accepted_by_klal = {}
    skipped_not_accepted = []
    skipped_already_applied = []
    for (klal_id, word_index), decision in decisions.items():
        if decision["chosen_source"] != "accept":
            skipped_not_accepted.append((klal_id, word_index))
            continue
        # Already inserted into part1.json by an earlier run. Without this,
        # a second run re-applied every accepted decision at now-shifted
        # positions - reproduced 2026-08-11, producing `וכו' [.] ע"כ [.] הא`
        # (a mark inserted mid-clause) while reporting "Applied: 2" again.
        if decision["id"] in already_applied:
            skipped_already_applied.append((klal_id, word_index))
            continue
        accepted_by_klal.setdefault(klal_id, []).append((word_index, decision))

    applied = []
    skipped_drift = []
    touched_klalim = set()

    for klal_id, items in accepted_by_klal.items():
        klal = by_klal.get(klal_id)
        live_list = candidates.get(str(klal_id), [])
        if klal is None:
            skipped_drift.extend((klal_id, wi) for wi, _ in items)
            continue

        words = klal["clean_text"].split(" ")
        for word_index, decision in sorted(items, key=lambda x: -x[0]):
            live_entry = next((c for c in live_list if c["before_word_index"] == word_index), None)
            snapshot = decision.get("candidate_snapshot")
            # Both checks required: the candidate file must still describe the
            # same proposal AND the live corpus must still read the way the
            # reviewer saw it. The second is the one that catches real drift.
            if not snapshot_matches(snapshot, live_entry) or not corpus_matches(snapshot, words):
                skipped_drift.append((klal_id, word_index))
                continue
            words[word_index:word_index] = ["[.]"]
            applied.append((klal_id, word_index))
            touched_klalim.add(klal_id)
            if not args.dry_run:
                rd.append_decision("apply_event", klal_id=klal_id, word_index=word_index,
                                    applied_decision_id=decision["id"])
        klal["clean_text"] = " ".join(words)

    if not args.dry_run and applied:
        save_part1(part1)

    tag = "[DRY RUN] " if args.dry_run else ""
    print(f"\n{tag}Applied: {len(applied)} punctuation insertion(s) across {len(touched_klalim)} klal(im)")
    for kid, widx in sorted(applied):
        print(f"  klal {kid} before word {widx}")

    if skipped_already_applied:
        print(f"\n{len(skipped_already_applied)} decision(s) skipped - already inserted into "
              f"part1.json by an earlier run (apply_event on record), no action needed:")
        for kid, widx in sorted(skipped_already_applied):
            print(f"  klal {kid} word {widx}")

    if skipped_drift:
        print(f"\n{len(skipped_drift)} decision(s) skipped - the candidate data or the surrounding "
              f"corpus text has drifted since the decision was made, needs a human look before applying:")
        for kid, widx in skipped_drift:
            print(f"  klal {kid} word {widx}")

    if skipped_not_accepted:
        print(f"\n{len(skipped_not_accepted)} rejected decision(s) - no action needed, already correctly excluded.")

    if applied:
        print("\nNEXT STEPS:")
        print("  1. Review the diff: git diff part1.json")
        print("  2. Run ./rebuild_all.sh to regenerate derived files - this also refreshes "
              "corrections_part1.json's word indices for every touched klal, since inserting "
              "\"[.]\" tokens shifted them.")
        print("  3. Log applied changes to PROJECT-STATUS.md.")
    elif not args.dry_run:
        print("\nNo changes made to part1.json.")


if __name__ == "__main__":
    main()
