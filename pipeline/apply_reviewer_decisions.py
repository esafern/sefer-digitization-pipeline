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
#   - 'manual_correction' decisions (2026-08-13: a reviewer flagging/
#     replacing ANY word, not just a machine-detected candidate) apply the
#     same way as 'replace', but drift-check against the word actually
#     seen at word_index when the decision was made (there's no
#     corrections_part1.json entry behind these) instead of a candidate
#     snapshot. chosen_text=='' means DELETE the word instead - that
#     changes word count for the klal, so it shares the insert/delete
#     one-per-klal-per-run limit below; an ordinary replace (non-empty
#     chosen_text) doesn't need it, same position in, same position out.
#   - Every applied decision gets its own apply_event row in the same
#     decisions log, so "decided" and "applied" stay two distinct,
#     separately-auditable events - including a no-op "confirmed current
#     text is correct" decision, which changes nothing in part1.json but
#     is still worth recording as reviewed.
#   - Never invokes rebuild_all.sh itself.
import argparse
import os

import corpus_io as cio
import review_decisions as rd

# Moved one level deeper (pipeline/ or tools/) 2026-08-16 - REPO now goes up
# two levels, not one, to keep resolving to the actual repo root where
# part1.json/docai_word_boxes/etc. live.
REPO = cio.REPO
PART1_PATH = cio.PART1_PATH


# Thin wrappers over corpus_io so this module's own PART1_PATH stays what they
# read (and stays monkeypatchable in tests). tools/apply_punctuation_
# decisions.py had a byte-identical private copy of both until 2026-08-17 -
# these two scripts are the only code in the repo allowed to WRITE the
# hand-edited source of truth, so a silent divergence in how they serialize it
# is the last thing that should be possible.
def load_part1():
    return cio.load_part1(PART1_PATH)


def save_part1(data):
    cio.save_part1(data, PART1_PATH)


def load_current_corrections():
    return cio.load_json(os.path.join(REPO, "corrections_part1.json"))


def snapshot_matches(snapshot, live_entry):
    if snapshot is None or live_entry is None:
        return False
    keys = ("opcode", "docai_reading", "final_text", "word_index")
    return all(snapshot.get(k) == live_entry.get(k) for k in keys)


# Every mutator below rejects a negative word_index explicitly. Python does
# not raise on one: `words[-1]` reads the LAST word and `words[-1:-1] = span`
# inserts before it, so a negative index that happens to satisfy the drift
# check would edit a real word at a position the decision never meant. Added
# 2026-08-15 (hard-wired-value audit) - the identical half-a-bounds-check gap
# was found and fixed in audit_applied_decisions.py's three checkers
# 2026-08-14 (PROJECT-STATUS.md finding 9) and guarded in
# assemble_corrections_dataset.check_drift, but the scripts that actually
# WRITE part1.json still only checked the upper end. No live decision has a
# negative word_index (both producers - build_corrections_dataset.py and the
# dashboard's click handler - are structurally non-negative), so this is
# defence-in-depth on the one code path that mutates the corpus, not a fix for
# an observed corruption.
def apply_replace(clean_text, word_index, final_text, chosen_text):
    words = clean_text.split()
    span = final_text.split() if final_text else []
    if not span:
        # A 'replace' with no stored text to replace is not a replace, and
        # falling through here is not harmless: `n` would be 1, and for an
        # out-of-range word_index `words[wi:wi+1]` is [] in Python, which
        # equals the empty span - so the drift check PASSES and the slice
        # assignment on the next line APPENDS chosen_text to the end of the
        # klal, at a position the decision never named. Added 2026-08-16
        # (code audit); apply_insert_removal() has had this exact `n == 0`
        # guard since it was written, apply_replace() never did. Not
        # reachable today - tests/test_corpus_invariants.py::
        # test_correction_entries_have_the_field_shape_their_opcode_implies
        # rejects a replace candidate with a null reading, and
        # snapshot_matches() has to agree with the live entry first -
        # defence-in-depth on the corpus-mutating path, same standing as the
        # negative-index guards.
        return None
    n = len(span)
    if word_index < 0 or words[word_index:word_index + n] != span:
        return None  # live drift beyond what the snapshot check caught
    words[word_index:word_index + n] = chosen_text.split()
    return " ".join(words)


def apply_manual_correction(clean_text, word_index, original_word, chosen_text):
    """'manual_correction' decision (2026-08-13): a reviewer flagged and
    replaced a word the machine pipeline never generated a candidate for,
    so there is no corrections_part1.json entry to drift-check against -
    only the word actually seen at word_index when the decision was made
    (candidate_snapshot["original_word"]). Same-position replace only (no
    word-count change), so unlike insert/delete this needs no per-klal-
    per-run limit.

    Deliberately clean_text.split(' ') - SPACE-ONLY, not clean_text.split()
    - because review_frontend/app.js computes word_index the same way
    (`(k.clean_text || '').split(' ')`) and this decision's word_index came
    from that exact click. Using the whitespace-collapsing .split() that
    the rest of this file uses for machine candidates would silently
    misalign on any klal where the two schemes disagree (documented open
    risk, see PROJECT-STATUS.md)."""
    words = clean_text.split(' ')
    if word_index < 0 or word_index >= len(words) or words[word_index] != original_word:
        return None  # live drift beyond what the snapshot check caught
    words[word_index] = chosen_text
    return " ".join(words)


def manual_correction_changes_word_count(chosen_text):
    """True when a manual_correction replaces one word with SEVERAL.

    apply_manual_correction's docstring says "same-position replace only (no
    word-count change), so unlike insert/delete this needs no per-klal-per-run
    limit" - but nothing enforced it. The dashboard's custom box accepts any
    text, and `words[word_index] = "two words"` re-joins into a LONGER list,
    shifting every later index in the klal. A second decision in the same klal
    and run would then land one word off.

    Verified 2026-08-27 (audit finding): 0 such decisions exist today, so this is
    a guard against the next one, not a repair. Callers must fold it into the
    same word_count_changed_klalim gate the insert/delete opcodes use."""
    return bool(chosen_text) and len(chosen_text.split()) > 1


def apply_manual_deletion(clean_text, word_index, original_word):
    """'manual_correction' decision with chosen_text=='' (2026-08-13: "need
    ability to delete selected word, not just change it") - remove the
    word entirely rather than replace it. Unlike apply_manual_correction,
    this changes word COUNT for the whole klal, so it shares the same
    word_count_changed_klalim per-klal-per-run guard as the insert/delete
    opcodes below - see their comment for why. Same space-only split as
    apply_manual_correction, for the same reason."""
    words = clean_text.split(' ')
    if word_index < 0 or word_index >= len(words) or words[word_index] != original_word:
        return None
    del words[word_index]
    return " ".join(words)


def apply_insert_removal(clean_text, word_index, final_text):
    """'insert'-opcode decision: remove the span clean_text has that docai
    doesn't (chosen_text=='' by convention means "accept the omission")."""
    words = clean_text.split()
    span = final_text.split() if final_text else []
    n = len(span)
    if n == 0 or word_index < 0 or words[word_index:word_index + n] != span:
        return None
    del words[word_index:word_index + n]
    return " ".join(words)


def apply_delete_insertion(clean_text, word_index, chosen_text):
    """'delete'-opcode decision: insert the word(s) docai saw that
    clean_text is missing, before word_index.

    Unlike apply_replace/apply_insert_removal, this one has no span to
    verify against - it adds text rather than transforming existing text -
    so it needs its own already-applied guard, or a re-run silently inserts
    the same word again (reproduced 2026-08-11: three runs produced
    `יגעתי 1 1 1 ולא`, each reporting success). The apply_event check in
    main() is the primary defence; this is the second, independent signal
    (CLAUDE.md Lesson 9), and it also covers a decisions log that was
    truncated or replayed from a different machine."""
    words = clean_text.split()
    if word_index < 0 or word_index > len(words) or not chosen_text:
        return None
    span = chosen_text.split()
    if words[word_index:word_index + len(span)] == span:
        return None  # already present at exactly this position - do not duplicate
    words[word_index:word_index] = span
    return " ".join(words)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="report what would happen, change nothing")
    args = parser.parse_args()

    decisions = rd.all_current("candidate_choice")
    manual_decisions = rd.all_current("manual_correction")
    corrections = load_current_corrections()
    part1 = load_part1()
    # Normalize clean_text so that .split() (used by machine-candidate paths)
    # and .split(' ') (used by manual-correction paths to match the frontend's
    # own indexing) produce the same result. In practice the corpus has no
    # consecutive/leading/trailing spaces (0 klalim where they disagree,
    # verified 2026-08-16), so this is a no-op today; it closes the structural
    # risk documented in review_decisions.py's word_index comment.
    for k in part1:
        k["clean_text"] = " ".join(k["clean_text"].split())
    by_klal = {k["klal_id"]: k for k in part1}
    already_applied = rd.applied_decision_ids()

    applied = []
    skipped_drift = []
    skipped_already_applied = []
    word_count_changed_klalim = set()
    n_replace = n_insert_delete = n_noop = n_manual = 0

    for (klal_id, word_index), decision in sorted(decisions.items()):
        # Already promoted into part1.json by an earlier run - never re-apply.
        if decision["id"] in already_applied:
            skipped_already_applied.append((klal_id, word_index))
            continue
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

        if opcode in ("replace", "insert") and decision["chosen_text"] == snapshot.get("final_text"):
            # Reviewer confirmed the currently-stored text is correct - for
            # 'replace' that means "don't change this word"; for 'insert' it
            # means "don't remove this word" (final_text IS the extra span
            # apply_insert_removal would otherwise delete). Without this
            # check, every 'insert'-opcode "keep current text" decision fell
            # through to apply_insert_removal unconditionally and silently
            # deleted text the reviewer voted to keep - confirmed against
            # two real pending decisions (klal 4 word 0 'ד', klal 57 word 0
            # 'נז אין'), see PROJECT-STATUS.md finding ★1.
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

    # manual_correction decisions: chosen_text=='' means delete (2026-08-13,
    # "need ability to delete selected word, not just change it") - that
    # changes word count for the whole klal, so it shares the
    # word_count_changed_klalim guard with the insert/delete opcodes above
    # (same set, checked across both loops - a manual deletion and a
    # machine insert/delete in the same klal in the same run correctly
    # block each other). A same-position replace (non-empty chosen_text)
    # needs no such limit.
    for (klal_id, word_index), decision in sorted(manual_decisions.items()):
        if decision["id"] in already_applied:
            skipped_already_applied.append((klal_id, word_index))
            continue
        klal = by_klal.get(klal_id)
        if klal is None:
            skipped_drift.append((klal_id, word_index))
            continue
        original_word = decision.get("candidate_snapshot", {}).get("original_word")
        chosen_text = decision["chosen_text"]

        # A multi-word REPLACEMENT shifts every later index, exactly like an
        # insert/delete, so it takes the same one-per-klal-per-run gate. Scoped
        # to the replace path: the `original_word is None` insert below has its
        # own gate, and adding to the set here would make that branch skip
        # itself (caught by test_manual_correction_with_no_original_word_
        # inserts_new_text the moment this was written too broadly).
        if original_word is not None and manual_correction_changes_word_count(chosen_text):
            if klal_id in word_count_changed_klalim:
                skipped_drift.append((klal_id, word_index))
                continue
            word_count_changed_klalim.add(klal_id)

        if original_word is None and chosen_text:
            # 'manual_correction' with no existing word at word_index and
            # non-empty chosen_text: insert NEW text (a reviewer-initiated
            # append/insert, not a replace of something already there).
            # ADDED 2026-08-21 (PROJECT-STATUS.md, klal 9/10 boundary fix):
            # the dashboard's manual-correction tool only ever REPLACES or
            # DELETES a word that already exists at word_index - there was
            # no way for a reviewer to insert brand-new text at all (only
            # the machine pipeline's 'delete'-opcode candidates could, via
            # apply_delete_insertion below, which needs a matching
            # corrections_part1.json candidate this decision type doesn't
            # have). Reuses apply_delete_insertion's own logic directly -
            # it's already a pure "insert chosen_text's words at word_index"
            # operation with no candidate-shape-specific checks in its body,
            # so this is not a parallel copy (CLAUDE.md Lesson 13), just a
            # second caller. Word-count-changing, same as a manual deletion.
            if klal_id in word_count_changed_klalim:
                print(f"  SKIP klal {klal_id} word {word_index}: another word-count-changing "
                      f"decision already applied for this klal this run - run ./rebuild_all.sh, "
                      f"then this script again, to pick up the next one.")
                continue
            new_text = apply_delete_insertion(klal["clean_text"], word_index, chosen_text)
            kind = "manual-insert"
        elif chosen_text == "":
            if klal_id in word_count_changed_klalim:
                print(f"  SKIP klal {klal_id} word {word_index}: another word-count-changing "
                      f"decision already applied for this klal this run - run ./rebuild_all.sh, "
                      f"then this script again, to pick up the next one.")
                continue
            new_text = apply_manual_deletion(klal["clean_text"], word_index, original_word)
            kind = "manual-delete"
        else:
            new_text = apply_manual_correction(klal["clean_text"], word_index, original_word, chosen_text)
            kind = "manual"

        if new_text is None:
            skipped_drift.append((klal_id, word_index))
            continue
        klal["clean_text"] = new_text
        if kind in ("manual-delete", "manual-insert"):
            word_count_changed_klalim.add(klal_id)
        n_manual += 1
        applied.append((klal_id, word_index, kind))
        if not args.dry_run:
            rd.append_decision("apply_event", klal_id=klal_id, word_index=word_index,
                                applied_decision_id=decision["id"])

    if not args.dry_run and (n_replace or n_insert_delete or n_manual):
        save_part1(part1)

    tag = "[DRY RUN] " if args.dry_run else ""
    print(f"\n{tag}Applied: {len(applied)} ({n_replace} replace, {n_insert_delete} insert/delete, "
          f"{n_manual} manual, {n_noop} confirmed-no-op)")
    for kid, widx, kind in applied:
        print(f"  klal {kid} word {widx}: {kind}")

    if skipped_already_applied:
        print(f"\n{len(skipped_already_applied)} decision(s) skipped - already promoted into "
              f"part1.json by an earlier run (apply_event on record), no action needed:")
        for kid, widx in skipped_already_applied:
            print(f"  klal {kid} word {widx}")

    if skipped_drift:
        print(f"\n{len(skipped_drift)} decision(s) skipped - candidate data has drifted since "
              f"the decision was made (a rebuild changed the corpus/indices), needs a human "
              f"look before applying:")
        for kid, widx in skipped_drift:
            print(f"  klal {kid} word {widx}")

    if n_replace or n_insert_delete or n_manual:
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
