#!/usr/bin/env python3
# [PRODUCTION] Promotes accepted review-dashboard decisions into part1.json.
# Deliberately a separate, manually-run step from recording a decision in
# the review UI - see PROJECT-STATUS.md "Review dashboard rearchitecture"
# for why (this project's standing rule: nothing silently mutates
# part1.json; every change is a deliberate, verified, logged step).
#
# Usage: python3 apply_reviewer_decisions.py [--dry-run]
#
# Safety model:
#   - Only the LATEST candidate_choice decision per (klal_id, word_index)
#     is considered (review_decisions.all_current) - a decision that was
#     itself later overridden by a newer one is not re-applied.
#   - Before applying, re-fetches the CURRENT corrections_part1.json entry
#     at that (klal_id, word_index) and compares it against the decision's
#     own candidate_snapshot - if they don't match, the corpus/candidate
#     data moved since the decision was made (e.g. a rebuild reshuffled
#     indices); skip and report, never guess.
#   - 'replace'-opcode decisions (equal word-count spans, guaranteed by
#     build_corrections_dataset.py's own generator) apply freely: locate
#     the exact word-index span in part1.json's clean_text, verify it
#     still equals the snapshot's final_text, replace it with the chosen
#     text.
#   - 'delete'-opcode decisions (docai saw a word clean_text is missing -
#     applying means INSERTING it) and 'insert'-opcode decisions
#     (clean_text has a word docai never saw - applying means REMOVING it,
#     chosen_text=='' by convention) both change word COUNT for that klal,
#     which invalidates every OTHER pending decision's word_index in the
#     same klal until ./rebuild_all.sh regenerates fresh indices. At most
#     ONE such decision is applied per klal per run; a clear instruction is
#     printed to re-run rebuild_all.sh before re-running this script for
#     another one in the same klal.
#   - Every applied decision gets its own apply_event row in the same
#     decisions log, so "decided" and "applied" stay two distinct,
#     separately-auditable events - including a no-op "confirmed current
#     text is correct" decision, which changes nothing in part1.json but
#     is still worth recording as reviewed.
#   - Never invokes rebuild_all.sh itself.
import argparse
import json
import os

import review_decisions as rd

REPO = os.path.dirname(os.path.abspath(__file__))
PART1_PATH = os.path.join(REPO, "part1.json")


def load_part1():
    with open(PART1_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_part1(data):
    with open(PART1_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_current_corrections():
    path = os.path.join(REPO, "corrections_part1.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def snapshot_matches(snapshot, live_entry):
    if snapshot is None or live_entry is None:
        return False
    keys = ("opcode", "docai_reading", "final_text", "word_index")
    return all(snapshot.get(k) == live_entry.get(k) for k in keys)


def apply_replace(clean_text, word_index, final_text, chosen_text):
    words = clean_text.split()
    span = final_text.split() if final_text else []
    n = len(span) or 1
    if words[word_index:word_index + n] != span:
        return None  # live drift beyond what the snapshot check caught
    words[word_index:word_index + n] = chosen_text.split()
    return " ".join(words)


def apply_insert_removal(clean_text, word_index, final_text):
    """'insert'-opcode decision: remove the span clean_text has that docai
    doesn't (chosen_text=='' by convention means "accept the omission")."""
    words = clean_text.split()
    span = final_text.split() if final_text else []
    n = len(span)
    if n == 0 or words[word_index:word_index + n] != span:
        return None
    del words[word_index:word_index + n]
    return " ".join(words)


def apply_delete_insertion(clean_text, word_index, chosen_text):
    """'delete'-opcode decision: insert the word(s) docai saw that
    clean_text is missing, before word_index."""
    words = clean_text.split()
    if word_index > len(words) or not chosen_text:
        return None
    words[word_index:word_index] = chosen_text.split()
    return " ".join(words)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="report what would happen, change nothing")
    args = parser.parse_args()

    decisions = rd.all_current("candidate_choice")
    corrections = load_current_corrections()
    part1 = load_part1()
    by_klal = {k["klal_id"]: k for k in part1}

    applied = []
    skipped_drift = []
    word_count_changed_klalim = set()
    n_replace = n_insert_delete = n_noop = 0

    for (klal_id, word_index), decision in sorted(decisions.items()):
        live_list = corrections.get(str(klal_id), [])
        live_entry = next((c for c in live_list if c["word_index"] == word_index), None)
        snapshot = decision.get("candidate_snapshot")

        if not snapshot_matches(snapshot, live_entry):
            skipped_drift.append((klal_id, word_index))
            continue

        opcode = snapshot["opcode"]
        klal = by_klal.get(klal_id)
        if klal is None:
            skipped_drift.append((klal_id, word_index))
            continue

        if opcode == "replace" and decision["chosen_text"] == snapshot.get("final_text"):
            n_noop += 1
            applied.append((klal_id, word_index, "confirmed-no-op"))
            if not args.dry_run:
                rd.append_decision("apply_event", klal_id=klal_id, word_index=word_index,
                                    applied_decision_id=decision["id"],
                                    note="confirmed current text, no change made")
            continue

        if opcode == "replace":
            new_text = apply_replace(klal["clean_text"], word_index, snapshot.get("final_text"), decision["chosen_text"])
            if new_text is None:
                skipped_drift.append((klal_id, word_index))
                continue
            klal["clean_text"] = new_text
            n_replace += 1
            applied.append((klal_id, word_index, "replace"))
            if not args.dry_run:
                rd.append_decision("apply_event", klal_id=klal_id, word_index=word_index,
                                    applied_decision_id=decision["id"])
            continue

        # insert/delete change word count for the whole klal - at most one
        # such change per klal per run, see module docstring.
        if klal_id in word_count_changed_klalim:
            print(f"  SKIP klal {klal_id} word {word_index}: another insert/delete decision "
                  f"already applied for this klal this run - run ./rebuild_all.sh, then this "
                  f"script again, to pick up the next one.")
            continue

        if opcode == "insert":
            new_text = apply_insert_removal(klal["clean_text"], word_index, snapshot.get("final_text"))
        elif opcode == "delete":
            new_text = apply_delete_insertion(klal["clean_text"], word_index, decision["chosen_text"])
        else:
            skipped_drift.append((klal_id, word_index))
            continue

        if new_text is None:
            skipped_drift.append((klal_id, word_index))
            continue

        klal["clean_text"] = new_text
        word_count_changed_klalim.add(klal_id)
        n_insert_delete += 1
        applied.append((klal_id, word_index, opcode))
        if not args.dry_run:
            rd.append_decision("apply_event", klal_id=klal_id, word_index=word_index,
                                applied_decision_id=decision["id"])

    if not args.dry_run and (n_replace or n_insert_delete):
        save_part1(part1)

    tag = "[DRY RUN] " if args.dry_run else ""
    print(f"\n{tag}Applied: {len(applied)} ({n_replace} replace, {n_insert_delete} insert/delete, "
          f"{n_noop} confirmed-no-op)")
    for kid, widx, kind in applied:
        print(f"  klal {kid} word {widx}: {kind}")

    if skipped_drift:
        print(f"\n{len(skipped_drift)} decision(s) skipped - candidate data has drifted since "
              f"the decision was made (a rebuild changed the corpus/indices), needs a human "
              f"look before applying:")
        for kid, widx in skipped_drift:
            print(f"  klal {kid} word {widx}")

    if n_replace or n_insert_delete:
        print("\nNEXT STEPS:")
        print("  1. Review the diff: git diff part1.json")
        print("  2. Run ./rebuild_all.sh to regenerate derived files and fresh word indices.")
        print("  3. Log applied changes to PROJECT-STATUS.md.")
        if n_insert_delete:
            print("  4. Any remaining insert/delete decisions in an already-touched klal need "
                  "another run of this script AFTER step 2's rebuild.")
    elif not args.dry_run:
        print("\nNo changes made to part1.json.")


if __name__ == "__main__":
    main()
