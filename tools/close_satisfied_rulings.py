#!/usr/bin/env python3
"""
tools/close_satisfied_rulings.py

[STANDALONE] Close rulings the corpus has ALREADY satisfied.

THE PROBLEM. A ruling is "unapplied" until an apply_event names it, and
apply_reviewer_decisions.py refuses to apply one whose candidate data has
drifted - it will not write to a position it can no longer verify. But some of
those rulings need no writing at all: the corpus already holds exactly what the
reviewer chose, usually because a later ruling at the same word carried it in,
or because it was a confirmation of text that never changed. They sit in the
drift list forever, and every count of "what still needs a human" is inflated by
them. Measured 2026-09-04: 39 of the 68 the applier was refusing.

Putting those in front of a reviewer is asking them to adjudicate a position a
script can settle, which is the same waste item 35 describes from the other end.

WHAT IT TAKES TO CLOSE ONE, and the bar is deliberately higher than "the word
matches". After a shift, an index can land on a DIFFERENT instance of the same
word: `אליבא` occurs 11 times in klal 91 and `מתני'` 6 times in klal 194, so
"w453 holds אליבא" is not evidence that THIS ruling's אליבא is the one there.
Three tiers, and only the first two close without corroboration:

  1. CONFIRMATION - the reviewer chose the word that was already there. Nothing
     had to happen for this to be true, so no aliasing risk exists.
  2. UNIQUE - the chosen word occurs exactly once in its klal. There is no
     other instance for a shift to alias onto.
  3. REPEATED - the chosen word occurs more than once. Requires the SNAPSHOT
     BBOX to resolve to this same index, through scan_alignment.
     word_bboxes_resolved - the ink agreeing with the letters, which is the
     standing two-signal bar (Lesson 9) and the same one
     repoint_stale_decisions.py holds itself to. No bbox, or a bbox pointing
     somewhere else, and this script REFUSES and reports.

WHAT IT WRITES. An `apply_event` naming the decision, with a note saying it was
already true rather than promoted by this run. That is honest: apply_event means
"this decision is in the corpus", which is exactly what has been verified, and
the applier's own confirmed-no-op path already writes one for a ruling that
changes nothing. It does NOT touch part1.json - there is nothing to change.

Dry run by default.
"""
import argparse
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
INSTALL_DIR = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(INSTALL_DIR, "pipeline"))

import corpus_io as cio  # noqa: E402
import identity as idn  # noqa: E402
import review_decisions as rd  # noqa: E402
import scan_alignment as sa  # noqa: E402

RULING_TYPES = ("disputed_choice", "candidate_choice", "manual_correction",
                "witness_choice")


def _distance(a, b):
    return (abs(a["x1"] - b["x1"]) + abs(a["y1"] - b["y1"])
            + abs(a["x2"] - b["x2"]) + abs(a["y2"] - b["y2"]))


def _bbox_index(klal_id, words, rec, regions, cache):
    """Which word index this ruling's recorded scan position resolves to now."""
    snap = rec.get("candidate_snapshot") or {}
    bbox, page = snap.get("bbox"), snap.get("page")
    if not bbox or page is None:
        return None
    if klal_id not in cache:
        cache[klal_id] = sa.word_bboxes_resolved(klal_id, words, regions)
    here = [(i, bb) for i, (bb, pg) in cache[klal_id].items() if bb and pg == page]
    if not here:
        return None
    return min(here, key=lambda kv: _distance(bbox, kv[1]))[0]


def current_rulings(rows):
    cur = {}
    for r in rows:
        if r["decision_type"] in RULING_TYPES and r.get("word_index") is not None:
            cur[(r["klal_id"], r["word_index"], r["decision_type"])] = r
    return cur


def classify(rec, words, regions, cache):
    """(verdict, why) - 'confirmation' / 'unique' / 'bbox' close it; others do not."""
    wi, chosen = rec["word_index"], rec.get("chosen_text")
    if not chosen:
        return None, "no chosen text"
    parts = chosen.split()
    if words[wi:wi + len(parts)] != parts:
        return None, "the corpus does not hold this text here"

    snap = rec.get("candidate_snapshot") or {}
    original = snap.get("original_word") or snap.get("final_text")
    if original is not None and " ".join(str(original).split()) == " ".join(parts):
        return "confirmation", "the reviewer chose the word that was already there"
    if len(parts) == 1 and sum(1 for w in words if w == parts[0]) == 1:
        return "unique", "the chosen word occurs once in this klal"

    at = _bbox_index(rec["klal_id"], words, rec, regions, cache)
    if at == wi:
        return "bbox", f"the ink puts this ruling at w{wi}, where its text now is"
    if at is None:
        return None, "the word repeats here and the ruling carries no usable bbox"
    return None, f"the word repeats here and the ink puts this ruling at w{at}, not w{wi}"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true",
                    help="write the apply_events (default: report only)")
    ap.add_argument("--part", type=int, default=1)
    args = ap.parse_args()

    rows = rd.all_records()
    applied = rd.applied_decision_ids()
    part1 = {k["klal_id"]: k for k in cio.load_part1_sorted()}
    regions = sa.load_regions()
    cache = {}

    closable, refused = [], []
    for rec in current_rulings(rows).values():
        if rec["id"] in applied or rec["klal_id"] not in part1:
            continue
        words = cio.words_of(part1[rec["klal_id"]])
        verdict, why = classify(rec, words, regions, cache)
        if verdict:
            closable.append((rec, verdict, why))
        elif why != "the corpus does not hold this text here" and why != "no chosen text":
            refused.append((rec, why))

    by = collections.Counter(v for _, v, _ in closable)
    print(f"{len(closable)} ruling(s) the corpus has already satisfied:")
    for k in ("confirmation", "unique", "bbox"):
        if by[k]:
            print(f"  {by[k]:>4}  {k}")
    if refused:
        print(f"\n{len(refused)} NOT closed - the word repeats and the ink does not "
              f"corroborate the position:")
        for rec, why in refused:
            print(f"     klal {rec['klal_id']:>4} w{rec['word_index']:<5} "
                  f"{str(rec.get('chosen_text'))!r:>14}  {why}")

    if not args.apply:
        print("\nDRY RUN - nothing written. Re-run with --apply.")
        return

    for rec, verdict, why in closable:
        rd.append_decision(
            "apply_event", klal_id=rec["klal_id"], word_index=rec["word_index"],
            applied_decision_id=rec["id"],
            actor=idn.tool_actor("pipeline-script", via="close_satisfied_rulings"),
            reviewer="tools/close_satisfied_rulings.py",
            note=(f"ALREADY SATISFIED ({verdict}): {why}. The corpus holds "
                  f"{rec.get('chosen_text')!r} at this position, so this ruling needed no "
                  f"write - it was carried in by a later ruling at the same word, or it "
                  f"confirmed text that never changed. Closed so it stops being counted as "
                  f"work a human still owes. part1.json was NOT modified."))
    print(f"\nWrote {len(closable)} apply_event(s). part1.json untouched.")


if __name__ == "__main__":
    main()
