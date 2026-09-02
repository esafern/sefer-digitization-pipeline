#!/usr/bin/env python3
# [STANDALONE] Re-point human rulings whose recorded word_index no longer
# describes the word they name (PROJECT-STATUS.md open item 0AB).
#
# THE PROBLEM. Applying a correction shifts every later word_index in that klal,
# and nothing re-points the decisions past it (Lesson 35). A ruling whose address
# has rotted is not lost - the ledger still holds what was decided - but it is
# INVISIBLE and UNSAFE: both display paths drop it rather than draw someone
# else's chosen_text on an unrelated word, and a fresh ruling at that key lands
# on the wrong word. Measured 2026-09-02: 105 of Part 1's 483 recorded rulings.
#
# WHAT THIS WILL AND WILL NOT TOUCH. Two independent signals must agree before a
# ruling is re-pointed:
#
#   1. the SNAPSHOT BBOX, mapped to whichever word occupies that place on the
#      scan now (scan_alignment.word_bboxes_resolved - the same geometry the
#      dashboard highlights with), and
#   2. the TEXT, searched for the ruling's chosen or original word.
#
# Where they agree, the position is corroborated by the ink and by the letters,
# which is this project's standing bar (Lesson 9). Where only one is available,
# or the two disagree, THIS SCRIPT REFUSES and reports.
#
# A unique text match on its own is deliberately NOT enough, and that is not
# caution for its own sake: it was measured and rejected. Of the 105, the
# text-only candidates imply shifts of -108 and -107 - the exact shape of the
# false relocation that MAX_EXPLAINABLE_SHIFT was added to
# audit_applied_decisions.py to catch, where a word's other occurrence eleven
# places away was absorbing a genuinely lost correction.
#
# HOW IT WRITES. review_decisions.jsonl is APPEND-ONLY and git-tracked. Nothing
# is edited or deleted: a corrected copy of the ruling is appended at the right
# word_index, carrying `supersedes: <original id>` and both signals in its note,
# so the record of what actually happened survives intact and is auditable.
#
# `supersedes` is what stops a corrected ruling appearing BESIDE its own stale
# predecessor. The original is still the newest record at the OLD index, so
# without an explicit forward reference the display has no way to know it has
# been answered - measured, the stale-address count moved 105 -> 102 without it.
#
# Dry run by default. `--apply` writes.
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pipeline"))

import corpus_io as cio  # noqa: E402
import review_decisions as rd  # noqa: E402
import scan_alignment as sa  # noqa: E402

# Types whose word_index addresses a corpus word. witness_choice keys on a
# docai_token_index and punctuation_choice on a gap between words; neither is a
# word position and neither is re-pointed here.
WORD_TYPES = ("candidate_choice", "disputed_choice", "manual_correction")


def _centre(b):
    return ((b["x1"] + b["x2"]) / 2, (b["y1"] + b["y2"]) / 2)


def _distance(a, b):
    ax, ay = _centre(a)
    bx, by = _centre(b)
    return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5


def original_word(rec):
    """The word a ruling was made against - see review_server._decision_original_word."""
    snap = rec.get("candidate_snapshot") or {}
    got = snap.get("original_word")
    return snap.get("final_text") if got is None else got


def bbox_signal(klal_id, words, rec, regions, cache):
    """Which word occupies this ruling's recorded scan position NOW."""
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


def text_signal(words, rec):
    """Every index whose word matches what this ruling chose, or ruled on."""
    for target in (rec.get("chosen_text"), original_word(rec)):
        if target:
            hits = [i for i, w in enumerate(words) if w == target]
            if hits:
                return hits
    return []


def classify(klal_id, words, rec, regions, cache):
    """(verdict, new_index, why) for one ruling."""
    wi = rec["word_index"]
    if not (0 <= wi < len(words)):
        current = None
    else:
        current = words[wi]
    if current is not None and current in (original_word(rec), rec.get("chosen_text")):
        return "ok", None, "the recorded index still describes its word"

    by_bbox = bbox_signal(klal_id, words, rec, regions, cache)
    by_text = text_signal(words, rec)
    if by_bbox is None and not by_text:
        return "no-evidence", None, "no scan position recorded and the word is nowhere in the klal"
    if by_bbox is None:
        if len(by_text) == 1:
            return ("text-only", by_text[0],
                    f"the text matches once, at w{by_text[0]}, but nothing corroborates it")
        return "ambiguous", None, f"the text matches at {by_text} and nothing chooses between them"
    if not by_text:
        return ("bbox-only", by_bbox,
                f"the scan position points at w{by_bbox}, but there is no text to check it against")
    if by_bbox in by_text:
        return ("recoverable", by_bbox,
                f"the scan position and the text both point at w{by_bbox} "
                f"(shift {by_bbox - wi:+d})")
    return ("conflict", None,
            f"the scan position says w{by_bbox} and the text says {by_text}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true",
                    help="append the corrected rulings (default: report only)")
    ap.add_argument("--part", type=int, default=1)
    ap.add_argument("--out", default="stale_decision_repoint_report.json")
    args = ap.parse_args()

    part1 = {k["klal_id"]: cio.words_of(k) for k in cio.load_part1()}
    regions = sa.load_regions()
    cache = {}

    # IDEMPOTENCE. `supersedes` is deliberately not honoured by all_current()
    # (see review_decisions.append_decision), so a ruling this script has already
    # re-pointed is STILL the current record at its old key and would be
    # re-pointed again on every run, appending a duplicate each time. Skip
    # anything already answered.
    already = rd.superseded_ids()
    seen, rows = {}, []
    for dtype in WORD_TYPES:
        for (kid, wi), rec in rd.all_current(dtype).items():
            if kid not in part1:
                continue
            # all_current aliases candidate_choice and disputed_choice onto one
            # another, so the same record arrives twice; keep it once.
            if rec["id"] in seen or rec["id"] in already:
                continue
            seen[rec["id"]] = True
            verdict, new_wi, why = classify(kid, part1[kid], rec, regions, cache)
            if verdict == "ok":
                continue
            rows.append({
                "decision_id": rec["id"], "decision_type": rec["decision_type"],
                "klal_id": kid, "recorded_word_index": wi, "new_word_index": new_wi,
                "verdict": verdict, "why": why,
                "ruled_on": original_word(rec), "chose": rec.get("chosen_text"),
                "word_at_recorded_index": (part1[kid][wi] if 0 <= wi < len(part1[kid]) else None),
            })

    order = ["recoverable", "bbox-only", "text-only", "conflict", "ambiguous", "no-evidence"]
    rows.sort(key=lambda r: (order.index(r["verdict"]), r["klal_id"], r["recorded_word_index"]))
    counts = {v: sum(1 for r in rows if r["verdict"] == v) for v in order}

    print(f"{len(rows)} ruling(s) whose recorded word_index no longer describes their word:\n")
    for v in order:
        if counts[v]:
            print(f"  {counts[v]:4d}  {v}")
    fixable = [r for r in rows if r["verdict"] == "recoverable"]
    print(f"\n{len(fixable)} can be re-pointed with two agreeing signals; "
          f"{len(rows) - len(fixable)} cannot and are left alone.")

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"total": len(rows), "counts": counts, "rulings": rows},
                  f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Wrote {args.out}")

    if not args.apply:
        print("\nDRY RUN - nothing written to the decision log. Re-run with --apply.")
        return

    for r in fixable:
        rec = rd.find_by_id(r["decision_id"])
        snap = dict(rec.get("candidate_snapshot") or {})
        snap["word_index"] = r["new_word_index"]
        rd.append_decision(
            rec["decision_type"],
            klal_id=r["klal_id"],
            word_index=r["new_word_index"],
            chosen_source=rec.get("chosen_source"),
            chosen_text=rec.get("chosen_text"),
            candidate_snapshot=snap,
            supersedes=r["decision_id"],
            note=(f"RE-POINTED from word_index {r['recorded_word_index']} to "
                  f"{r['new_word_index']} (open item 0AB). The original ruling "
                  f"{r['decision_id']} stands unchanged in this log; a later apply in "
                  f"this klal shifted every index after it and nothing re-pointed the "
                  f"decision, so it named a word it never described and both display "
                  f"paths dropped it. Re-pointed only because {r['why']}. "
                  f"Original note: {rec.get('note') or '(none)'}"),
        )
    print(f"\nAppended {len(fixable)} corrected ruling(s). The originals are untouched.")


if __name__ == "__main__":
    main()
