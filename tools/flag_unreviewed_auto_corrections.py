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
# corpus still holds the corrected word there, or when pipeline/drift_recovery.py
# can say where it moved to; the rest are reported and skipped, never guessed at.
#
# RECOVERY, ADDED 2026-09-06, and why it is not the bbox method the other
# repointing tools use. It cannot be: **0 of these 131 records carry a
# candidate_snapshot bbox** - the pass that wrote them never generated a
# candidate, so it never had a scan position to record - and both
# repoint_stale_decisions.py and close_satisfied_rulings.py return None on their
# first line without one. Item 0BO's plan said to extend those tools and would
# have produced nothing.
#
# drift_recovery.py supplies the substitute signal: within one klal an apply run
# shifts every later index by the same amount, so rulings corroborate each
# other's shift. All 26 that this tool used to skip are recovered by it, each at
# a position that holds exactly the word its ruling chose - verified in context,
# not merely by the match (e.g. klal 69 w31 -> w30, `אי אתה מוצא >>אלא<< י"א
# הויות`). The bar and every refusal path are documented in that module.
#
# Dry run by default. `--apply` writes.
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pipeline"))

import corpus_io as cio  # noqa: E402
import drift_recovery as dr  # noqa: E402
import review_decisions as rd  # noqa: E402
import scan_alignment as sa  # noqa: E402
import word_identity as widentity  # noqa: E402

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
    # HAS ANYONE ALREADY ENGAGED WITH THIS POSITION - which is the real question,
    # and it is NOT "is a flag open here now".
    #
    # This tool skips a correction that has ever been flagged. That looks like a
    # bug (a flag cleared by an unattended bulk pass would hide a correction
    # nobody reviewed) and switching it to "currently open" was tried on
    # 2026-09-06 and REVERTED, because the ledger says otherwise: 39 of these
    # positions carry a flag that was raised and later cleared, and every one was
    # closed deliberately - 36 by a person (`CLOSED BY APPLY ... a human having
    # ruled here`, and a user-authorised 2026-08-26 clearing) and 3 by this
    # tool's own withdrawal of flags on words with no DocAI alignment. Re-raising
    # them would undo 36 human decisions and reproduce the exact complaint that
    # started this - "i cleared the flag but it still shows".
    #
    # So the skip stands, and the assumption under it is CHECKED rather than
    # trusted: any flag here closed by neither a human nor an explicit withdrawal
    # is reported, because that is the case where this skip would hide something.
    ever_flagged, closed_by = {}, {}
    for r in rows:
        if r.get("decision_type") == "klal_flag" and r.get("word_index") is not None:
            key = (r["klal_id"], r["word_index"])
            ever_flagged[key] = True
            closed_by[key] = None if r.get("needs_revisit") else r
    part1 = {k["klal_id"]: cio.words_of(k) for k in cio.load_part1()}

    regions = sa.load_regions()
    todo, skipped, unlocatable, already_at_resolved = [], [], [], []
    # The RECORDED position, as a first pass. A drifted ruling is filtered again
    # below against the position its flag would actually land on - see the note
    # on `at`.
    unflagged = [r for r in corrections
                 if (r["klal_id"], r["word_index"]) not in ever_flagged]

    unattended = []
    for r in corrections:
        closer = closed_by.get((r["klal_id"], r["word_index"]))
        if closer is None:
            continue
        if not (rd.ruled_by_human(closer)
                or "Withdrawing a flag" in (closer.get("note") or "")):
            unattended.append((r, closer))

    # Where the word still sits, for every one of them at once: drift_recovery
    # needs the whole klal's rulings together, because a shift is corroborated by
    # its neighbours (see that module's bar (2b)).
    at = {}
    for kid, rs in dr.group_by_klal(unflagged).items():
        words = part1.get(kid) or []
        settled = [r for r in rs if not dr.stale_against(words, r, True)]
        for r in settled:
            at[r["id"]] = (r["word_index"], "the recorded position still holds it")
        stale = [r for r in rs if dr.stale_against(words, r, True)]
        recovered, refused = dr.recover_klal(words, stale, True)
        for rid, (new_wi, _off, why) in recovered.items():
            at[rid] = (new_wi, why)
        for rid, why in refused.items():
            rec = next(x for x in stale if x["id"] == rid)
            here = (words[rec["word_index"]] if 0 <= rec["word_index"] < len(words)
                    else "(out of range)")
            skipped.append((kid, rec["word_index"], rec.get("chosen_text"), here, why))

    # IDEMPOTENCE, and it is not free once positions are re-derived. The skip
    # above keys on the RECORDED index, but a recovered flag is written at the
    # RESOLVED one - so on a second run the recorded index is still unflagged and
    # all 26 would be raised again, as duplicates on words that already carry
    # them. Caught by re-running the tool after its own --apply, which is the
    # only thing that shows it. A position already flagged is dropped here.
    for r in unflagged:
        if r["id"] not in at:
            continue
        wi, why = at[r["id"]]
        if (r["klal_id"], wi) in ever_flagged:
            already_at_resolved.append((r, wi))
            continue
        words = part1.get(r["klal_id"]) or []
        # A flag whose word cannot be put on the scan is a dead end: clicking
        # it highlights nothing and the focus-zoom has nothing to zoom to,
        # which tests/test_corpus_invariants.py forbids outright. It is also
        # self-defeating here - the flag exists to say "check this against
        # the scan". Reported, not raised.
        bbox, _page = sa.word_scan_position(r["klal_id"], words, wi, regions)
        (todo if bbox is not None else unlocatable).append((r, wi, why))

    # EVERY correction lands in exactly one bucket and the buckets are printed as
    # a partition. The old summary computed "already flagged" as
    # `total - todo - skipped` and never subtracted `unlocatable`, so that line
    # over-reported by however many were unlocatable; it read correctly only
    # because that count happened to be 0.
    already = len(corrections) - len(unflagged) + len(already_at_resolved)
    assert already + len(todo) + len(skipped) + len(unlocatable) == len(corrections), (
        "the buckets below must partition the corrections - a count that does not "
        "add up is the summary describing something other than what ran")
    print(f"{args.reviewer}: {len(corrections)} correction(s) applied to the corpus")
    print(f"  {already:4d} already flagged (open, or deliberately closed - see above)")
    print(f"  {len(todo):4d} unflagged, and locatable - a flag will be raised")
    print(f"  {len(skipped):4d} unflagged, and the position could not be established - "
          f"skipped, not guessed at")
    print(f"  {len(unlocatable):4d} unflagged, but the word has NO scan position - a flag there "
          f"could not be acted on")
    moved = [(r, wi, why) for r, wi, why in todo if wi != r["word_index"]]
    if moved:
        print(f"\n  {len(moved)} of those had DRIFTED and were re-derived "
              f"(pipeline/drift_recovery.py):")
        for r, wi, why in moved[:10]:
            print(f"        klal {r['klal_id']} w{r['word_index']} -> w{wi}  "
                  f"{r.get('chosen_text')!r}  ({why})")
    for r, wi, why in unlocatable[:8]:
        print(f"        klal {r['klal_id']} w{wi}: {r.get('chosen_text')!r}")
    for kid, wi, chosen, now, why in skipped[:8]:
        print(f"        klal {kid} w{wi}: chose {chosen!r}, found {now!r} - {why}")
    if unattended:
        print(f"\n  WARNING: {len(unattended)} correction(s) are skipped because a flag "
              f"here was cleared by NEITHER a human NOR an explicit withdrawal, so this "
              f"tool may be hiding a correction nobody reviewed:")
        for r, closer in unattended[:10]:
            print(f"        klal {r['klal_id']} w{r['word_index']} - cleared by "
                  f"{closer.get('reviewer')!r} on {(closer.get('ts') or '')[:10]}")

    if not args.apply:
        print("\nDRY RUN - nothing written. Re-run with --apply.")
        return

    # THE ID, ATTACHED AT WRITE TIME. Added 2026-09-07 (item 0CK). Every flag
    # this tool wrote before now names its word by INDEX alone, and an index rots
    # the moment an earlier edit changes the klal's word count - which is the
    # entire reason reindex_flags_after_shift() exists. The id cannot be
    # recovered for those afterwards: a flag records no word, so there is nothing
    # to corroborate a derived address against (measured: extending
    # backfill_word_ids.RULING_TYPES to klal_flag backfills exactly ZERO). Here,
    # at write time, the answer is free - `wi` is the position this tool just
    # derived and checked, so the word is right there.
    #
    # Same seam the dashboard uses (review_server._with_word_id), not a private
    # copy: word_identity.snapshot_fields() returns {} when no sidecar or no id
    # exists, so a flag simply carries no id rather than a null that later reads
    # as "recorded and empty".
    id_state = widentity.load()
    for r, wi, why in todo:
        rd.append_decision(
            "klal_flag", klal_id=r["klal_id"], word_index=wi,
            candidate_snapshot=(widentity.snapshot_fields(id_state, r["klal_id"], wi) or None),
            needs_revisit=True, reviewer=FLAG_REVIEWER,
            note=(f"UNREVIEWED AUTOMATED CORRECTION. {args.reviewer} changed this word "
                  f"to {r.get('chosen_text')!r} on {(r.get('ts') or '')[:10]} and applied it "
                  f"to the corpus, recording it as a manual_correction - the type the "
                  f"dashboard draws as human-decided - so it never reached a review queue. "
                  f"Its own note said a human should still check it against the scan and "
                  f"that every one would be flagged; 114 of its 131 never were. This flag "
                  f"is that promise, kept late. The correction itself has NOT been reversed. "
                  f"Original ruling {r['id']}"
                  + (f", recorded at w{r['word_index']} and re-derived to this position: "
                     f"{why}." if wi != r["word_index"] else ".")),
        )
    print(f"\nRaised {len(todo)} review flag(s). No corpus text was changed.")


if __name__ == "__main__":
    main()
