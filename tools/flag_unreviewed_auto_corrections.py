#!/usr/bin/env python3
# [STANDALONE] Raise the human-review flags an automated correction pass
# PROMISED and never wrote (PROJECT-STATUS.md open item 0AT).
#
# THE INCIDENT. `ai-dropped-lamed-correction` applied 131 corrections to
# part1.json on 2026-08-15. Its own note on every one of them says:
#
#     "NOT individually scan-verified ... A human should still check this
#      specific instance against the scan before treating it as certain.
#      Flagging for human review per user instruction (apply the
#      mechanically-confirmed corrections, flag every one)."
#
# 114 of the 131 were never flagged. And the records were written as
# `manual_correction`, the type the dashboard renders GREEN as Human-Decided -
# so they entered the corpus looking settled, appeared in no queue, and two of
# them are now confirmed wrong against the ink. Lesson 19: describing a step in
# writing is not performing it.
#
# WHAT THIS DOES. Appends a word-level `klal_flag` (needs_revisit=True) at each
# unflagged position, which is what the instruction asked for and what a review
# queue is actually made of. It changes no corpus text and reverses no
# correction: it puts them in front of a human, which is all that was ever meant
# to happen.
#
# POSITIONS ARE RE-DERIVED, NOT TRUSTED. Later applies shifted indices in these
# klalim, so a flag written at the recorded word_index would land on an unrelated
# word - the very failure item 0AB is about. A position is used only when the
# corpus still holds the corrected word there; the rest are reported and skipped
# rather than guessed at.
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

PASS_REVIEWER = "ai-dropped-lamed-correction"
FLAG_REVIEWER = "tools/flag_unreviewed_auto_corrections.py"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--reviewer", default=PASS_REVIEWER,
                    help="which automated pass's corrections to flag")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    # The whole log, through the module's own cached accessor - not a
    # hand-rolled re-parse via the private rd._resolve(). Until 2026-09-04 this
    # was a dead `if False` statement followed by exactly that, which paid the
    # full parse cost on every run; rd.all_records() was added to close the API
    # gap that forced it. Found by the 2026-09-03 ultra review.
    rows = rd.all_records()

    corrections = [r for r in rows if r.get("reviewer") == args.reviewer
                   and r.get("decision_type") == "manual_correction"]
    flagged = {(r["klal_id"], r["word_index"]) for r in rows
               if r.get("decision_type") == "klal_flag" and r.get("word_index") is not None}
    part1 = {k["klal_id"]: cio.words_of(k) for k in cio.load_part1()}

    regions = sa.load_regions()
    todo, skipped, unlocatable = [], [], []
    for r in corrections:
        kid, wi, chosen = r["klal_id"], r["word_index"], r.get("chosen_text")
        if (kid, wi) in flagged:
            continue
        words = part1.get(kid) or []
        if 0 <= wi < len(words) and words[wi] == chosen:
            # A flag whose word cannot be put on the scan is a dead end: clicking
            # it highlights nothing and the focus-zoom has nothing to zoom to,
            # which tests/test_corpus_invariants.py forbids outright. It is also
            # self-defeating here - the flag exists to say "check this against
            # the scan". Reported, not raised.
            bbox, _page = sa.word_scan_position(kid, words, wi, regions)
            (todo if bbox is not None else unlocatable).append(r)
        else:
            skipped.append((kid, wi, chosen,
                            words[wi] if 0 <= wi < len(words) else "(out of range)"))

    print(f"{args.reviewer}: {len(corrections)} correction(s) applied to the corpus")
    print(f"  {len(corrections) - len(todo) - len(skipped):4d} already carry a review flag")
    print(f"  {len(todo):4d} unflagged, and the recorded position still holds the corrected word")
    print(f"  {len(skipped):4d} unflagged, but the position has DRIFTED - skipped, not guessed at")
    print(f"  {len(unlocatable):4d} unflagged, but the word has NO scan position - a flag there "
          f"could not be acted on")
    for r in unlocatable[:8]:
        print(f"        klal {r['klal_id']} w{r['word_index']}: {r.get('chosen_text')!r}")
    for kid, wi, chosen, now in skipped[:8]:
        print(f"        klal {kid} w{wi}: expected {chosen!r}, found {now!r}")

    if not args.apply:
        print("\nDRY RUN - nothing written. Re-run with --apply.")
        return

    for r in todo:
        rd.append_decision(
            "klal_flag", klal_id=r["klal_id"], word_index=r["word_index"],
            needs_revisit=True, reviewer=FLAG_REVIEWER,
            note=(f"UNREVIEWED AUTOMATED CORRECTION. {args.reviewer} changed this word "
                  f"to {r.get('chosen_text')!r} on {(r.get('ts') or '')[:10]} and applied it "
                  f"to the corpus, recording it as a manual_correction - the type the "
                  f"dashboard draws as human-decided - so it never reached a review queue. "
                  f"Its own note said a human should still check it against the scan and "
                  f"that every one would be flagged; 114 of its 131 never were. This flag "
                  f"is that promise, kept late. The correction itself has NOT been reversed. "
                  f"Original ruling {r['id']}."),
        )
    print(f"\nRaised {len(todo)} review flag(s). No corpus text was changed.")


if __name__ == "__main__":
    main()
