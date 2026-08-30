#!/usr/bin/env python3
# [STANDALONE, ONE-TIME BACKFILL] Close every open word-level klal_flag sitting
# at a position a decision was ALREADY applied to.
#
# WHY. Until 2026-08-30 nothing closed the flag a correction answered:
# apply_reviewer_decisions.py wrote the corpus edit and the apply_event and
# stopped there. Both clearing controls in the dashboard are per-flag, so a
# satisfied flag stayed lit until somebody clicked it individually - and nobody
# did, 51 times. The reviewer hit it as "klal 66 i cleared the flag but it still
# shows as set in the middle pane": the klal-level flag they cleared was not what
# the pane was counting; four word-level flags were, all of them on words already
# corrected, one flagging a `!` that no longer exists in the text.
#
# apply_reviewer_decisions.close_flag_satisfied_by() now does this at apply time.
# That fixes the FUTURE; this clears the backlog that accumulated before it, and
# should not need running again.
#
# It reuses that same function rather than reimplementing the rule (CLAUDE.md
# Lesson 13: a hand-maintained second copy of a rule is a rule that will drift).
# In particular it inherits the guard that matters most here: a flag RAISED AFTER
# the apply is not answered by it - somebody re-opened that position knowing the
# decision had landed. klal 66 w0 (flagged three minutes after its own apply was
# found wrong and reverted) and klal 91 w191 (restored by hand after a smoke
# test) are both left open by that rule, which is the whole reason it exists.
#
# Nothing is edited: the ledger is append-only, so each close is a new
# klal_flag row with needs_revisit false naming the decision that answered it.
#
# Usage:
#   python3 tools/close_flags_already_answered.py --dry-run
#   python3 tools/close_flags_already_answered.py
import argparse
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pipeline"))

import corpus_io as cio          # noqa: E402
import review_decisions as rd    # noqa: E402
import apply_reviewer_decisions as ard  # noqa: E402


def applied_positions():
    """(klal_id, word_index) -> (apply_event ts, the decision it promoted)."""
    out = {}
    records = {}
    for r in rd.all_records() if hasattr(rd, "all_records") else _read_ledger():
        records[r["id"]] = r
        if r["decision_type"] == "apply_event" and r.get("word_index") is not None:
            out[(r["klal_id"], r["word_index"])] = (r["ts"], r.get("applied_decision_id"))
    return {k: (ts, records.get(did)) for k, (ts, did) in out.items() if records.get(did)}


def _read_ledger():
    with open(os.path.join(REPO, "review_decisions.jsonl"), encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="report what would close, change nothing")
    args = ap.parse_args()

    applied = applied_positions()
    closed, kept = [], []
    for klal in cio.load_part1_sorted():
        kid = klal["klal_id"]
        for wi, rec in sorted(ard.open_word_flags(kid).items()):
            if (kid, wi) not in applied:
                continue
            ts, decision = applied[(kid, wi)]
            if args.dry_run:
                (kept if (rec.get("ts") or "") > ts else closed).append((kid, wi, rec, ts))
                continue
            if ard.close_flag_satisfied_by(kid, wi, decision, "backfill", applied_ts=ts):
                closed.append((kid, wi, rec, ts))
            else:
                kept.append((kid, wi, rec, ts))

    tag = "[DRY RUN] " if args.dry_run else ""
    print(f"{tag}closed {len(closed)} flag(s) already answered by an applied decision")
    for kid, wi, rec, ts in closed:
        print(f"  klal {kid} w{wi}  (applied {ts[:10]}) {(rec.get('note') or '')[:60]}")
    if kept:
        print(f"\n{len(kept)} left OPEN - the flag is NEWER than the apply, so it was "
              f"deliberately re-raised after the decision landed:")
        for kid, wi, rec, ts in kept:
            print(f"  klal {kid} w{wi}  flag {rec.get('ts', '')[:10]} > apply {ts[:10]}")
    if not args.dry_run and closed:
        print("\nNEXT: restart nothing - review_server reads the ledger fresh per request.")


if __name__ == "__main__":
    main()
