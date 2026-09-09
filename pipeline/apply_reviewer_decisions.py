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
#   - Before applying, re-fetches the CURRENT review_queue_part1.json entry
#     at that (klal_id, word_index) and compares it against the decision's
#     own candidate_snapshot - if they DISAGREE, the corpus/candidate data
#     moved since the decision was made (e.g. a rebuild reshuffled indices);
#     skip and report, never guess.
#   - If that entry is simply GONE, the check falls back to the corpus
#     itself (snapshot_still_matches_corpus). The queue legitimately drops a
#     dispute the moment a human rules on it, so "entry missing" is the
#     NORMAL state of an unapplied decision, not evidence of drift - reading
#     it as drift stranded 43 rulings between 2026-08-22 and 2026-08-27.
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
#     review_queue_part1.json entry behind these) instead of a candidate
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
import datetime
import json
import os

import corpus_io as cio
import review_decisions as rd
import word_identity as widentity

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
    return cio.load_json(os.path.join(REPO, "review_queue_part1.json"))


def snapshot_matches(snapshot, live_entry, ignore_index=False):
    if snapshot is None or live_entry is None:
        return False
    # `word_index` drops out of the comparison when the position was resolved by
    # a stable id: the id's whole purpose is that the word MOVED, so requiring the
    # recorded index to still match would refuse precisely the rulings it rescues.
    # The identity-bearing fields are still compared, so this is narrower than it
    # looks - what is dropped is the address, not the evidence.
    keys = ("opcode", "docai_reading", "final_text")
    if not ignore_index:
        keys += ("word_index",)
    return all(snapshot.get(k) == live_entry.get(k) for k in keys)


def snapshot_still_matches_corpus(snapshot, klal, at=None):
    """Fallback drift check for a decision whose review_queue_part1.json entry
    is GONE rather than changed.

    The candidate queue is regenerated by every rebuild, and
    synthesize_multi_witness.active_human_decisions() deliberately DROPS any
    dispute a human has already ruled on, so the reviewer is not shown a
    resolved dispute again. Correct for the queue - but it made the decision
    permanently unappliable here: snapshot_matches() reads a live entry that no
    longer exists, returns False, and main() reports "drifted" forever. Decide
    a dispute, rebuild before applying it, and the ruling is stranded. Measured
    2026-08-30: 43 decisions from 2026-08-22..27 in exactly that state, 24 of
    them real edits still sitting uncorrected in part1.json (`&` among them).

    What the corrections entry was ever for is proving the CORPUS has not moved
    under the decision. That question is answerable from the corpus directly,
    which is what this does - and it is the same standard
    apply_manual_correction has always used, those decisions having never had a
    candidate entry behind them at all.

    Deliberately narrower than snapshot_matches: only a snapshot carrying a
    non-empty final_text qualifies, i.e. one naming a span that must still be
    present at word_index. A 'delete'-opcode decision (docai saw a word
    clean_text lacks; applying INSERTS it) names no such span - there is
    nothing in the corpus to check it against - so it keeps requiring the live
    entry and is never recovered by this path."""
    if snapshot is None or klal is None:
        return False
    span = (snapshot.get("final_text") or "").split()
    # `at` is the position resolved_position() settled on. It differs from the
    # snapshot's own only when a stable id said the word moved - and then the
    # snapshot's index is the STALE one, so checking against it would refuse the
    # ruling for having succeeded at exactly what the id is for.
    word_index = snapshot.get("word_index") if at is None else at
    if not span or not isinstance(word_index, int) or word_index < 0:
        return False
    words = klal["clean_text"].split()
    return words[word_index:word_index + len(span)] == span


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
# --- Keeping the flag queue honest when the corpus moves -----------------------
# Applying a decision has side effects on the REVIEW state that nothing used to
# carry out, so every correction quietly degraded the queue it came from
# (PROJECT-STATUS open items 0C / 0D). Two of those are closed here; the third
# (a corrected word losing its DocAI scan alignment) is not fixable from this
# script.

def open_word_flags(klal_id):
    """{word_index: record} for every OPEN, word-indexed klal_flag in this klal.

    Latest row per word wins, then the still-open ones are kept - the same
    reading review_server._word_level_ai_flags() applies, so what this closes is
    exactly what the dashboard was still lighting up."""
    by_word = {}
    for r in rd.history_for(klal_id, decision_type="klal_flag"):
        wi = r.get("word_index")
        if wi is not None:
            by_word[wi] = r
    return {wi: r for wi, r in by_word.items() if r.get("needs_revisit")}


def close_flag_satisfied_by(klal_id, word_index, decision, kind, applied_ts=None):
    """Close the open flag at a position a decision was just applied to.

    A flag says "a human should look at this word". A decision applied at that
    exact word IS a human having looked - including a confirmed-no-op, where they
    looked and said the text stands. Nothing used to close it, and the two
    clearing controls are per-flag, so a satisfied flag stayed lit until someone
    clicked it individually: klal 66 alone was showing four whose words had
    already been corrected, one of them flagging a `!` that no longer existed in
    the text (reviewer 2026-08-30: "i cleared the flag but it still shows as
    set").

    Returns True if a flag was closed."""
    rec = open_word_flags(klal_id).get(word_index)
    if rec is None:
        return False
    # A flag RAISED AFTER the decision was applied is not answered by it - somebody
    # deliberately re-opened the position knowing the decision had landed, and
    # closing it would erase that. Two real cases: klal 66 w0, flagged three
    # minutes after its own apply was found to be wrong and reverted, and klal 91
    # w191, restored by hand after being cleared as a smoke test.
    if applied_ts and (rec.get("ts") or "") > applied_ts:
        return False
    first_line = (rec.get("note") or "").split("|")[0].strip()
    rd.append_decision(
        "klal_flag", klal_id=klal_id, word_index=word_index, needs_revisit=False,
        applied_decision_id=decision["id"],
        note=(f"CLOSED BY APPLY {datetime.date.today().isoformat()}: decision {decision['id']} "
              f"({kind}) was applied at this exact word, which is a human having ruled here - "
              f"the flag has been answered. Superseded flag was raised by "
              f"{rec.get('reviewer')} on {rec.get('ts', '')[:10]}: {first_line[:120]}"))
    return True


UNVERIFIED_SHIFTS_PATH = os.path.join(REPO, "unverified_flag_shifts.jsonl")


# WHY A MOVE WAS REFUSED. Two reasons now, and they need different actions from
# the reviewer, so the file says which rather than making them guess from the
# indices (item 0BX, 2026-09-08).
REFUSAL_NOTES = {
    "text": ("the word at the old index is not the word at the shifted index, "
             "so the record was left alone rather than moved onto a guess"),
    "collision": ("the shifted index is already occupied by another ruling or flag "
                  "in this klal, and all_current() keys on (klal_id, word_index) - "
                  "moving onto it would make one of the two invisible to the applier, "
                  "the dashboard and the counts, with nothing recording the loss"),
}


def _record_unverified_shifts(rows, path=None):
    """Append the flags a shift could not be verified for, so they survive the run.

    One JSON object per line, flushed per row (the standing incremental-flush
    rule in START_HERE.md), carrying enough to act on it later: which klal, the
    index the flag is still recorded at, the index the shift would have moved it
    to, and when. Read it with `cat`; nothing consumes it automatically, because
    what to do about a flag that may name the wrong word is a human judgement.
    """
    path = path or UNVERIFIED_SHIFTS_PATH
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with open(path, "a", encoding="utf-8") as f:
        for kid, recorded_at, would_have_been, reason in rows:
            f.write(json.dumps({
                "ts": stamp, "klal_id": kid,
                "still_recorded_at_word_index": recorded_at,
                "shift_would_have_moved_it_to": would_have_been,
                "reason": reason,
                "note": REFUSAL_NOTES[reason],
            }, ensure_ascii=False) + "\n")
            f.flush()


def reindex_pending_decisions_after_shift(klal_id, position, delta, old_words, new_words):
    """Move UNAPPLIED decisions past a word-count change onto the words they name.

    reindex_flags_after_shift() covers flags; nothing covered decisions, and they
    have it worse. A stale flag points at the wrong word and a human notices. A
    stale decision is refused by the drift guard on every future run - correctly,
    since the corpus no longer holds what it was recorded against - so it is
    stranded exactly the way 0A stranded a decided dispute, and for a reason this
    script itself created one run earlier.

    Measured 2026-08-31 on klal 74: deleting a page-seam catchword at w416 left
    the decisions at w417 (`רבא`, the duplicate the same flag named) and w443
    (`!`) pointing one word past their targets. The corpus was left reading
    `אמר רבא רבא אמר` - half a repair, with the other half unappliable.

    Same verified-move rule as the flag version: the word the decision named must
    be the word at the shifted index, or it is left alone and reported. Nothing is
    edited - a superseding decision is appended, carrying the original's own
    chosen_text and snapshot rewritten to the new index."""
    already = rd.applied_decision_ids()
    moved, unverified = [], []
    # SLOTS THAT WILL STILL BE OCCUPIED AFTER THE SHIFT - item 0BX.
    #
    # rd.all_current() keys on (klal_id, word_index) and takes the LAST row per
    # key, so appending a re-pointed ruling at an index another ruling already
    # holds makes one of the two invisible to every consumer of that map: the
    # applier, the dashboard's display maps, and the tri-state counts. Nothing
    # records the displacement. Measured 2026-09-06: 94 keys already carry
    # rulings about more than one word, hiding 115 - 105 of them harmless
    # (applied) and 2 deliberately superseded, but 3 of the remaining 8 are
    # exactly this, reindexing collisions in klal 210 (w65, w66, w131). Nothing
    # is lost today only because the collisions happened to land on duplicates.
    #
    # POLICY: REFUSE AND REPORT, which is the choice this function already makes
    # for a move it cannot verify against the text one line below. "Record it and
    # move anyway" needs somewhere to put the displaced ruling and a reader that
    # looks there; refusing needs neither and cannot lose anything.
    #
    # Only rulings at or before `position` are seeded: everything after it moves
    # by the same delta, so movers keep their relative order and cannot collide
    # with each other. The real case is delta < 0 landing on a ruling that is not
    # moving. Targets are added as they are written, so two movers cannot be sent
    # to one slot either.
    # `disputed_choice` added 2026-08-31. It was missing, and it is the type that
    # needs this MOST: a decided dispute is dropped from the candidate queue
    # (synthesize_multi_witness.active_human_decisions), so it is drift-checked
    # against part1.json itself - which is exactly the check a shifted index
    # fails. Leaving it out stranded a ruling the same way item 0A did. Found by
    # inserting the heading separators, which shifted 4 pending decisions by +1
    # and only one of them was a type this function moved.
    for d_type in ("candidate_choice", "manual_correction", "disputed_choice"):
        current = rd.all_current(d_type)
        # EVERY OCCUPIED SLOT, and a slot is freed only when its occupant
        # ACTUALLY MOVES. Corrected 2026-09-08 (item 0DS) - the first cut seeded
        # only `wi <= position`, on the stated premise that "everything after it
        # moves by the same delta". THAT PREMISE IS FALSE: this loop declines to
        # move three sets of rulings that sit PAST `position`, and none of them
        # was in the set -
        #   * already applied (`decision["id"] in already`),
        #   * no text to verify a move against (`not named`),
        #   * refused by the text check (appended to `unverified`).
        # So a mover could land on an applied ruling and win the key, and
        # rd.all_current() takes the LAST row per (klal_id, word_index) - the
        # applied one goes invisible to the applier, the display maps and the
        # counts. That is the exact loss this guard was added to prevent, left
        # reachable by the guard itself.
        occupied = {wi for (kid, wi) in current if kid == klal_id and wi is not None}
        # DIRECTION MATTERS once vacating is modelled: with delta > 0 a mover's
        # target may be held by a HIGHER mover that has not moved yet, so walk
        # descending; with delta < 0, ascending. Same ordering problem item 0DA
        # hit reverting the diplomatic edition.
        for (kid, wi), decision in sorted(current.items(),
                                          key=lambda kv: kv[0][1] if kv[0][1] is not None else -1,
                                          reverse=delta > 0):
            if kid != klal_id or wi is None or wi <= position:
                continue
            if decision["id"] in already:
                continue                       # already in the corpus, not pending
            # NO ID SKIP HERE EITHER, removed 2026-09-08 with the flag
            # reindexer's (item 0DE findings 1 and 2). It read: "ADDRESSED BY ID,
            # so there is nothing here to reindex... resolved_position() asks the
            # sidecar first."
            #
            # TRUE OF THE APPLIER, NOT OF THE QUEUE. resolved_position() does
            # id-resolve, so an unmoved ruling still applies to the right word.
            # But the reviewer's SCREEN never asks the sidecar:
            # review_counts.merge_decision() sets
            # `entry["current_decision"] = decided.get((klal_id,
            # entry["word_index"]))` and machine_state()/word_states() test
            # `(klal_id, entry["word_index"]) in decided`, all against a map keyed
            # on the RECORDED index - while review_queue_part1.json is rebuilt
            # from scratch each rebuild against FRESH indices. So a ruling left at
            # a stale index stops matching its own candidate entry: it vanishes
            # from the word it was made on, and can colour a different word
            # decided.
            #
            # LATENT, MEASURED, AND FIXED ANYWAY. 2026-09-08: 39 pending rulings,
            # 4 carry an id, 0 of the 4 resolve to a different index than the one
            # recorded - so nothing is wrong on screen today. The alternative fix
            # was to teach the display to id-resolve, which is a change to what
            # the reviewer sees across four endpoints; keeping the index correct
            # costs one superseding row per shift and touches no rendering.
            #
            # THE RETIREMENT REFUSAL SURVIVES, structurally rather than by this
            # skip. The old comment kept it to avoid moving a ruling whose word
            # was REMOVED onto whatever slid into its slot. The text check below
            # already refuses exactly that: `new_words[new_wi:...] != span` fails
            # when the word is gone, and the ruling is reported as unverified
            # instead of moved.
            #
            # SAFE UNDER LESSON 46 because of the line above this one - a ruling
            # already in `already` (applied) is skipped before we get here, so no
            # superseding copy is ever written over an applied ruling.
            snapshot = decision.get("candidate_snapshot") or {}
            named = snapshot.get("final_text") or snapshot.get("original_word")
            if not named:
                continue                       # nothing to verify a move against
            span = named.split()
            new_wi = wi + delta
            if not (0 <= wi < len(old_words) and 0 <= new_wi <= len(new_words) - len(span)):
                unverified.append((wi, new_wi, "text")); continue
            if old_words[wi:wi + len(span)] != span or new_words[new_wi:new_wi + len(span)] != span:
                unverified.append((wi, new_wi, "text")); continue
            if new_wi in occupied:
                unverified.append((wi, new_wi, "collision")); continue
            occupied.discard(wi)          # this ruling vacates its old slot...
            occupied.add(new_wi)          # ...and takes the new one
            moved_snapshot = dict(snapshot, word_index=new_wi)
            rd.append_decision(
                d_type, klal_id=klal_id, word_index=new_wi,
                chosen_source=decision.get("chosen_source"),
                chosen_text=decision.get("chosen_text"),
                candidate_snapshot=moved_snapshot,
                reviewer=decision.get("reviewer") or "local",
                note=(f"[reindexed from w{wi} on {datetime.date.today().isoformat()}: a word-count "
                      f"change at w{position} in this klal shifted every later index by {delta:+d}, "
                      f"and {named!r} now sits at w{new_wi}. Carries decision {decision['id']}'s own "
                      f"ruling unchanged - only the position moved.] "
                      + (decision.get("note") or "")))
            moved.append((wi, new_wi))
    return moved, unverified


def reindex_flags_after_shift(klal_id, position, delta, old_words, new_words, skip):
    """Move open flags past a word-count change onto the words they name.

    ./rebuild_all.sh regenerates the CANDIDATE files against fresh indices, but
    review_decisions.jsonl is append-only and nothing reindexes it, so every open
    flag after the change kept pointing at an index that is now a different word.
    Fired 2026-08-30: deleting a stray `!` at klal 66 w112 shortened the klal, and
    the flag on `ע"ס` at w135 came to rest on `שהניח`.

    VERIFIED, NEVER ASSUMED. A flag is moved only when the word it sat on before
    is the word at the shifted index now. If that does not hold the shift is not
    understood here, and the flag is left exactly where it is and REPORTED rather
    than moved onto a guess - a flag on the wrong word is worse than one a human
    is told to check.

    Returns (moved, unverified); unverified rows are
    (old_index, new_index, reason) where reason is "text" or "collision"."""
    moved, unverified = [], []
    open_flags = open_word_flags(klal_id)
    # SAME COLLISION GUARD AS THE DECISION REINDEXER, and here because of Lesson
    # 34 rather than because a case was reported: the sibling branch of the same
    # defect is the cheapest place to look, and two flags on one word_index is
    # the same silent loss - review_server._word_level_ai_flags() builds
    # `by_word[widx]` and the LAST row per index wins, so one flag stops being
    # rendered at all. Item 0BX measured the ruling side; this side had never
    # been measured, and the shape is identical.
    #
    # Reachable the same way: with delta < 0 a moving flag can land on one at an
    # index at or before `position`, which does not move.
    # Same correction as the decision reindexer above (item 0DS): every open
    # flag's slot, freed only when that flag actually moves. `skip` is in it too -
    # those flags were closed earlier in this run and do not move, and appending
    # an OPEN flag onto a closed one's index masks the closure behind it in
    # all_current(). Refusing costs a reported line; the alternative is silent.
    occupied = {wi for wi in open_flags} | set(skip)
    # NO ID SKIP HERE, and the asymmetry with the decision reindexer above is
    # deliberate - see item 0DE. That one may skip an id-carrying ruling because
    # its consumer RESOLVES by id: resolved_position() asks the sidecar first.
    # NO FLAG CONSUMER RESOLVES A POSITION BY ID. Be precise about which half of
    # the flag machinery this is, because one half does read the id:
    #   - WHERE THE FLAG SITS is index-only. review_server._word_level_ai_flags()
    #     builds `by_word[r.get("word_index")]` and bounds-checks that index
    #     against the word list; the nav and count sets filter on `fwidx`;
    #     review_counts.flag_still_open() takes an index. Nothing here consults
    #     the sidecar, so nothing can recover a flag whose index went stale.
    #   - WHETHER IT IS ANSWERED does consult the id -
    #     review_counts.flag_answered_by_a_later_decision() matches flag id to
    #     ruling id at :136, deliberately after the index test.
    # An unmoved flag is therefore still rendered, still counted, and still
    # highlighting whatever word slid into its old slot - the klal 66
    # `ע"ס` -> `שהניח` defect this function exists to prevent.
    #
    # THE SKIP WAS HERE AND WAS NOT INERT. Its comment said "0 of 1,367
    # word-level flags carry an id"; re-measured 2026-09-08 the ledger holds
    # 1,424 such rows, 17 carry an id, and all 17 are open (klal 54, 167, 198).
    # Two of klal 198's had already diverged - index and id naming different
    # words - which is the ambiguity the skip creates, not one it resolves.
    #
    # PUT IT BACK ONLY WITH ITS PREMISE: when a flag consumer resolves by id the
    # way resolved_position() does, this skip becomes correct and should return.
    # Until then the index is the only address a flag has, so it gets maintained.
    # IS THE SIDECAR ACTUALLY IN STEP WITH THE CORPUS WE JUST WROTE? Asked once,
    # here, because the id stamp below is only meaningful if it is - item 0DE
    # finding 4.
    #
    # The stamp's own comment names the order it depends on: save_part1(), then
    # widentity.follow_corpus() reconciles the sidecar, and only THEN this runs.
    # THE CODE DID NOT ENFORCE THAT ORDER, and there are three live ways to reach
    # here with a pre-shift sidecar, none of which raises: follow_corpus() is
    # wrapped in a bare `except Exception` that prints a WARNING and continues;
    # it SKIPS a klal not already in the sidecar (deliberately - it must not
    # silently seed Parts 2-3); and reconcile()'s ValueErrors come back in
    # `problems`, which are only printed. In any of the three, id_at(new_wi)
    # returns the id of the word that USED to sit at new_wi - a different word -
    # and the flag is stamped with a wrong identity.
    #
    # TESTED DIRECTLY RATHER THAN PLUMBED. follow_corpus() returns a COUNT, not
    # the set of klalim it reconciled, and it is called by three corpus writers,
    # so widening its contract to answer this is a bigger change than the
    # question needs. A reconciled sidecar has exactly one id per word in the
    # klal we just wrote; an unreconciled one still has the pre-shift count and
    # differs by `delta`, which is precisely the failure mode. Length is the
    # whole test.
    id_state = widentity.load()
    sidecar_in_step = len(widentity.ids_for(id_state, klal_id)) == len(new_words)
    if not sidecar_in_step:
        print(f"  WARNING: klal {klal_id}'s word-id sidecar is out of step with the "
              f"corpus ({len(widentity.ids_for(id_state, klal_id))} ids for "
              f"{len(new_words)} words) - reindexed flags will be written WITHOUT a "
              f"word id rather than with a wrong one. Run "
              f"tools/seed_word_identity.py --verify")
    for wi, rec in sorted(open_flags.items(), reverse=delta > 0):
        if wi <= position or wi in skip:
            continue
        new_wi = wi + delta
        if not (0 <= wi < len(old_words) and 0 <= new_wi < len(new_words)):
            unverified.append((wi, new_wi, "text")); continue
        if old_words[wi] != new_words[new_wi]:
            unverified.append((wi, new_wi, "text")); continue
        if new_wi in occupied:
            unverified.append((wi, new_wi, "collision")); continue
        occupied.discard(wi)
        occupied.add(new_wi)
        rd.append_decision(
            "klal_flag", klal_id=klal_id, word_index=wi, needs_revisit=False,
            note=(f"REINDEXED {datetime.date.today().isoformat()} to w{new_wi}, NOT resolved. A "
                  f"word-count change at w{position} in this klal shifted every later index by "
                  f"{delta:+d}; the word this flag names, {old_words[wi]!r}, now sits at w{new_wi}. "
                  f"Superseded by a new flag there with the original note."))
        # THE MOVED FLAG CARRIES THE ID OF THE WORD IT LANDED ON. Added
        # 2026-09-07 (item 0CK) with the same change to
        # flag_unreviewed_auto_corrections.py.
        #
        # IT IS PROVENANCE, NOT AN ADDRESS - corrected 2026-09-08 (item 0DE).
        # This stamp was written on the premise that it made the move "the LAST
        # one it needs", because the skip at the top of this loop would pass over
        # the flag on every future shift. That skip is gone: no flag consumer
        # resolves by id, so the index is still the address and still gets
        # maintained on each shift. What the id buys is the ability to SEE a
        # divergence - if the sidecar and the index ever name different words,
        # something did not reindex - which is how item 0DE found klal 198's two.
        #
        # SAFE ONLY BECAUSE OF THE ORDER HERE, which is worth naming. The corpus
        # is written at save_part1(), widentity.follow_corpus() reconciles the
        # sidecar to it, and only THEN is this function called - so `id_state`
        # describes the post-shift corpus and id_at(new_wi) is the word this flag
        # was just verified onto (old_words[wi] == new_words[new_wi], checked
        # above). Read before follow_corpus ran, the same call would return the
        # id of whatever used to sit at new_wi, which is a different word.
        #
        # AND NOW IT IS CHECKED, not merely depended on - `sidecar_in_step`,
        # computed once at the top of this function (item 0DE finding 4). No
        # stamp when the sidecar is behind: NO id is recoverable, a WRONG id is
        # not, and it would be indistinguishable from a right one forever after.
        rd.append_decision(
            "klal_flag", klal_id=klal_id, word_index=new_wi, needs_revisit=True,
            candidate_snapshot=((widentity.snapshot_fields(
                id_state, klal_id, new_wi) or None) if sidecar_in_step else None),
            # LINKED TO THE FLAG IT MOVES, added 2026-09-07 (item 0CS). Without
            # it the moved flag is a BRAND NEW record with today's timestamp, and
            # review_counts.flag_answered_by_a_later_decision only counts a
            # ruling NEWER than the flag - correctly, since a flag raised after a
            # decision is a fresh concern. So a flag the reviewer had already
            # answered came back OPEN the moment an unrelated edit shifted its
            # klal: the flag looked newer than the answer. `supersedes` says what
            # is actually true - this is the same flag, moved - and lets the
            # answered test ask when it was originally RAISED.
            supersedes=rec.get("id"),
            reviewer=rec.get("reviewer") or "local",
            note=(f"[reindexed from w{wi} on {datetime.date.today().isoformat()} after a "
                  f"word-count change at w{position}] " + (rec.get("note") or "")))
        moved.append((wi, new_wi))
    return moved, unverified


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


def sync_heading_word(klal, word_index, original_word, chosen_text):
    """Carry a body correction across into `title` when it lands in the heading.

    THE COUPLING THIS EXISTS FOR, found the hard way 2026-09-03. `title` is not
    separate text - it is a SECOND COPY of the klal's opening words, which the
    body reprints (220 of 222 headings are an exact prefix of their own body).
    So correcting a body word inside the heading run silently desynchronises the
    two: klal 92 w7 `נסקי`->`נפקי` and klal 96 w1 `בעיו`->`בעיי` were applied,
    the gate went red, and the corpus briefly held two spellings of one printed
    word. Nobody had to think about this before, because until today nothing in
    this pipeline could write `title` at all.

    Lesson 35, exactly: when a step writes to the source of truth, enumerate
    what else describes that truth and update it in the same breath.

    NOT A NEW ADJUDICATION, which is why it needs no ruling of its own. The
    reviewer already decided this word against the ink; the heading is the same
    printed word, and propagating their decision to the second copy completes it
    rather than making a second one. A machine deciding a word on its own would
    be item 0AT's defect, and this is not that.

    Index mapping: `body[0]` is the klal's gematria marker, which no heading
    repeats, so heading word i is body word i+1.

    THE GUARD IS WHAT MAKES IT SAFE: it syncs only when the heading currently
    holds exactly the word the body was correcting away from. Where the two
    already diverge on purpose (klalim 9 and 186 - a glued stop, a geresh) it
    does nothing, so an unrelated divergence can never be overwritten by a
    correction elsewhere.

    Returns True if the heading changed.
    """
    title_words = cio.title_words_of(klal)
    i = word_index - 1
    if not (0 <= i < len(title_words)):
        return False
    # A HEADING IS PUNCTUATED DIFFERENTLY FROM THE BODY, so a body word does not
    # always equal its heading twin character for character, and the sync has to
    # know about exactly one such difference: the TERMINAL PERIOD. Measured, all
    # 222 Part 1 headings end with one glued to their last word and NONE contains
    # one anywhere else, while the body writes the stop as a separate `[.]`
    # token. So the last heading word is `שכר.` where the body has `שכר`.
    #
    # Both directions of that mattered, and each was found by a test rather than
    # by reasoning:
    #   - Copying a body stop INTO a heading is wrong. Klal 9's body carries one
    #     glued to `איידי` - one of only two such words in Part 1, itself a
    #     recorded data issue - and the first version of this function duly
    #     produced `איידי. אפשר דאמרינן ...`, a period mid-heading.
    #   - Refusing on the terminal period is also wrong: it made a correction to
    #     the LAST heading word never propagate, which the prefix invariant then
    #     fails on, since it compares with that period stripped.
    is_last = i == len(title_words) - 1
    stored = title_words[i]
    if is_last and stored.endswith(".") and len(stored) > 1:
        stored = stored[:-1]
    if stored != original_word or chosen_text == original_word:
        return False
    if "." in chosen_text and not is_last:
        return False
    replacement = chosen_text
    if is_last and not replacement.endswith("."):
        replacement += "."
    title_words[i] = replacement
    klal["title"] = " ".join(title_words)
    return True


def apply_manual_correction(clean_text, word_index, original_word, chosen_text):
    """'manual_correction' decision (2026-08-13): a reviewer flagged and
    replaced a word the machine pipeline never generated a candidate for,
    so there is no review_queue_part1.json entry to drift-check against -
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
    words = cio.words_of(clean_text)
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

    CORRECTED 2026-08-31. The 2026-08-27 audit recorded "0 such decisions exist
    today, so this is a guard against the next one, not a repair", and the
    2026-08-31 sweep repeated it. Both are wrong: **klal 57 w44 is one**
    (`לאורויילן` -> `לאורויי לן`, recorded 2026-08-30T21:13, applied
    2026-08-30T21:19), and it went through this path while it was unguarded.
    It did no damage - it was the only word-count-changing decision applied to
    klal 57 in that run, and the next one (w0) came a day later and sits BEFORE
    it - but "0 exist" was a claim about a query, not about the log. Count them
    with the applied ones included; the earlier measurement evidently did not.

    Callers must fold this into the same word_count_changed_klalim gate the
    insert/delete opcodes use - both apply_reviewer_decisions.py (:599) and
    tools/export_corpus.py (its manual-replace branch) now do."""
    return bool(chosen_text) and len(chosen_text.split()) > 1


def apply_manual_deletion(clean_text, word_index, original_word):
    """'manual_correction' decision with chosen_text=='' (2026-08-13: "need
    ability to delete selected word, not just change it") - remove the
    word entirely rather than replace it. Unlike apply_manual_correction,
    this changes word COUNT for the whole klal, so it shares the same
    word_count_changed_klalim per-klal-per-run guard as the insert/delete
    opcodes below - see their comment for why. Same space-only split as
    apply_manual_correction, for the same reason."""
    words = cio.words_of(clean_text)
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


def resolved_position(decision, klal, recorded_index, id_state, backfilled):
    """Where this ruling applies NOW -> (index, how) or (None, "retired").

    `how` is "word_id" when the position came from the stable id and may
    therefore DIFFER from the recorded one - which is what the drift checks below
    have to be told, because they compare against the recorded index and that is
    exactly what an id-resolved ruling has moved away from.

    THE ONE PLACE THE APPLIER ASKS "WHERE". Every loop below used the word_index
    off `all_current()`'s KEY, which is the recorded index and rots the moment an
    earlier edit changes the klal's word count. That is what
    reindex_pending_decisions_after_shift() exists to paper over, and what item
    0BX's collision risk comes out of: rulings being moved between index-shaped
    slots.

    A ruling that carries a stable word_id does not need any of that. The id
    names the word, the sidecar was updated by whichever writer moved it, and the
    answer is exact. Asking here - once per loop, rebinding the local
    `word_index` - is why this is a one-line change at each of the two body loops
    rather than an edit to the 26 places that consume the position.

    THE TITLE LOOP IS DELIBERATELY NOT CONVERTED. A title_correction's index is
    into `title.split(' ')`, a different address space from the body words the
    sidecar numbers, so an id from here would name the wrong word confidently.

    DELIBERATELY STRICTER THAN review_decisions.resolve_word_index. That function
    also answers "occurrence" and "unique", and its own docstring says those are
    hints for a human re-point and never an authority to move a correction onto a
    word nobody looked at. This is the corpus mutator; it takes only the two
    EXACT answers:

      word_id  - the sidecar knows where that word is. Survives any shift.
      index    - the recorded index still holds the recorded word.

    and refuses `retired` outright, because a ruling whose word was deleted has
    nowhere to apply.

    INERT UNTIL IDS EXIST, which is the safety property that makes this landable
    on a corpus mid-flight: no ruling recorded before 2026-09-06 carries a
    word_id, so every one of them resolves by "index" exactly as before or fails
    exactly as before. Behaviour changes only for rulings that carry an id.
    """
    idx, how = rd.resolve_word_index(decision, cio.words_of(klal),
                                     id_state=id_state, backfilled=backfilled)
    if how == "word_id":
        return idx, "word_id"
    if how == "index":
        return recorded_index, "index"
    if how == "retired":
        return None, "retired"
    # "occurrence"/"unique"/None: the address did not verify exactly. Fall back to
    # the recorded index and let the drift checks below rule on it, which is what
    # this loop did before ids existed - a refusal here would change today's
    # behaviour for every pre-id ruling.
    return recorded_index, "recorded"


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
    # A ruling whose REPLACEMENT is already in the corpus is finished, even
    # though it is still the current record at its own (rotted) key - see
    # review_decisions.superseded_by_an_applied_decision for why that happens.
    # Without this the applier retries it every run, fails the drift check, and
    # it is counted as outstanding review work forever.
    settled_by_successor = rd.superseded_by_an_applied_decision()
    # The mirror of the above: a ruling that only MOVED an applied ruling's
    # address carries a correction the corpus already holds. See
    # review_decisions.restates_an_applied_ruling for what wrote 23 of them.
    settled_by_successor |= rd.restates_an_applied_ruling()
    # The text as it stood BEFORE this run, so reindex_flags_after_shift can
    # verify a moved flag lands on the same word it named - captured here rather
    # than re-read later, because by_klal is mutated in place below.
    words_before = {k["klal_id"]: cio.words_of(k) for k in part1}
    # Read ONCE for the whole run: resolved_position() consults both per ruling,
    # and each is a full read of its file.
    id_state = widentity.load()
    backfilled = rd.backfilled_word_ids()
    # klal_id -> (position, delta). At most one word-count change per klal per
    # run (the guard below), so one entry each.
    word_count_shifts = {}

    applied = []
    skipped_drift = []
    recovered_from_dropped_entry = []
    refused_partial_span = []
    skipped_already_applied = []
    word_count_changed_klalim = set()
    n_replace = n_insert_delete = n_noop = n_manual = 0
    n_title = 0  # title_correction decisions promoted (item 39)
    # Heading mirrors of a body correction (sync_heading_word). Counted, because
    # they are appended to `applied` and `len(applied)` is what the summary
    # prints as its total: without a counter of their own the total stopped
    # equalling the sum of its own breakdown whenever one fired. Found by the
    # 2026-09-03 ultra review.
    n_heading_sync = 0
    # Word-count changes that landed inside a klal's heading run: the heading
    # is a second copy of those words and its own indices moved, so this is
    # reported for a human rather than synced by guess.
    heading_desync = []

    for (klal_id, word_index), decision in sorted(decisions.items()):
        # Already promoted into part1.json by an earlier run - never re-apply.
        if decision["id"] in already_applied or decision["id"] in settled_by_successor:
            skipped_already_applied.append((klal_id, word_index))
            continue
        snapshot = decision.get("candidate_snapshot")

        klal = by_klal.get(klal_id)
        if klal is None:
            skipped_drift.append((klal_id, word_index))
            continue
        # WHERE, asked once - see resolved_position(). Everything below reads this
        # local (the live-entry lookup, the text mutation, the apply_event, the
        # reporting), so the position is resolved here and nowhere else. That is
        # why this is one line at each loop rather than an edit to the 26 places
        # that consume it.
        word_index, _how = resolved_position(decision, klal, word_index, id_state, backfilled)
        if word_index is None:
            skipped_drift.append((klal_id, decision.get("word_index")))
            print(f"  SKIP klal {klal_id} word {decision.get('word_index')}: "
                  f"its word was deleted from the corpus by a later ruling")
            continue

        # AT THE RESOLVED INDEX, which is why this sits below and not above.
        # review_queue_part1.json is regenerated against the CURRENT corpus by
        # rebuild_all.sh, so its entries are at today's positions - looking one up
        # at the ruling's recorded index would, for a ruling the id just moved,
        # fetch the entry belonging to some other word and drift-check against it.
        live_list = corrections.get(str(klal_id), [])
        live_entry = next((c for c in live_list if c["word_index"] == word_index), None)

        # A live entry that DISAGREES is real drift and always wins the veto.
        # A live entry that is simply absent falls back to the corpus itself -
        # see snapshot_still_matches_corpus() for why the queue legitimately
        # loses the entry the moment the decision is recorded.
        # A DECLINED INSERTION IS SETTLED BEFORE THE DRIFT GATE, and this ordering
        # is the fix - item 0DX, 2026-09-09.
        #
        # `chosen_text: ""` on a `delete` opcode means "do not insert here". It
        # writes NOTHING to the corpus, so there is no position to verify and
        # nothing drift can invalidate. But the gate below runs first, and a
        # delete-opcode snapshot carries no `final_text` - which
        # snapshot_still_matches_corpus() explicitly refuses ("names no such span
        # - there is nothing in the corpus to check it against"). So a ruling that
        # needs no write could never reach the branch written to handle it, and
        # sat in the drift worklist asking a human to re-adjudicate a decision
        # they had already made and that required no action.
        #
        # Measured when found: klal 4 w35 and klal 106 w46, both `chosen_text ""`,
        # both stuck since 2026-08-11. klal 106 w46 doubly so - that klal has
        # exactly 46 words, so w46 is the append position and out of range for any
        # corpus check that could ever pass.
        #
        # ONLY the declined case moves. An ACCEPTED insertion still faces the full
        # gate below, because that one does write to the corpus.
        _snap = snapshot or {}
        if (_snap.get("opcode") == "delete"
                and not (decision["chosen_text"] or "").strip()):
            n_noop += 1
            applied.append((klal_id, word_index, "confirmed-no-op"))
            if not args.dry_run:
                rd.append_decision("apply_event", klal_id=klal_id, word_index=word_index,
                                   applied_decision_id=decision["id"],
                                   note="declined the proposed insertion, no change made "
                                        "(settled before the drift gate: it names no span for "
                                        "drift to invalidate - item 0DX)")
            continue

        by_id = (_how == "word_id")
        if not snapshot_matches(snapshot, live_entry, ignore_index=by_id):
            if live_entry is not None or not snapshot_still_matches_corpus(
                    snapshot, klal, at=word_index):
                skipped_drift.append((klal_id, word_index))
                continue
            recovered_from_dropped_entry.append((klal_id, word_index))

        opcode = snapshot["opcode"]

        # A REJECTED INSERTION IS A NO-OP TOO, and it is the branch this check
        # was never swept into (Lesson 34: when a mutator has three paths and one
        # is wrong, read the other two). A `delete` opcode proposes ADDING a word
        # DocAI read that the corpus lacks, so its snapshot has no `final_text`
        # by construction and the equality above can never fire for it. Declining
        # the insertion records an empty chosen_text - and `apply_delete_
        # insertion` then returns None on `not chosen_text`, so every one of them
        # fell into skipped_drift and was reported as "candidate data has drifted,
        # needs a human look" on every run, forever. Measured 2026-09-06: 16 such
        # rulings, 15 of them the entire "Only the ink has an answer" section of
        # DRIFTED-RULINGS-WORKLIST.md - a reviewer being asked to re-adjudicate
        # decisions they had already made, that require no write at all.
        #
        # Unambiguous in the ledger: all 16 carry chosen_source `final_text`
        # ("keep the current text", which for this opcode means "do not insert")
        # or `custom` with an empty string. The 6 delete-opcode rulings that DID
        # accept an insertion all carry the word to insert, and 4 are applied.
        # NO `rejected_insertion` HERE ANY MORE. It used to share this branch, and
        # since 0DX a declined insertion is settled ABOVE the drift gate - so the
        # test here could only ever be False by the time control reaches it. Left
        # as a comment rather than silently dropped, because the condition it
        # encoded is still true and still documented above: for a `delete` opcode,
        # an empty chosen_text means "do not insert".
        if (opcode in ("replace", "insert")
                and decision["chosen_text"] == snapshot.get("final_text")):
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
            # A `replace` whose chosen text has a DIFFERENT word count than the
            # span it answers is a word-count change wearing a same-position
            # opcode. apply_replace() substitutes the chosen text for the WHOLE
            # span, so choosing one word for a two-word span deletes the other -
            # and none of the insert/delete safeguards apply on this path: no
            # one-per-klal-per-run gate, no shift recorded, so the flags after it
            # are never reindexed.
            #
            # Third instance of one defect (klal 66 w0 was the `insert` branch,
            # ★1 the confirmed-no-op): a decision naming fewer words than its
            # span. It fired here on klal 69 w188, span `אל ואלהים`, chosen `אל` -
            # deleting a `ואלהים` this candidate's OWN vision check reads at 0.95
            # and whose flag is `current_text_confirmed`, leaving
            # `לא שם אל דליתא` where the sentence needs `לא שם אל ואלהים דליתא`.
            # Swept the whole ledger: that is the only one ever applied.
            #
            # Refused rather than gated. A same-count replace is what this opcode
            # means; anything else is a reviewer answering a different question
            # than the one asked, and the answer belongs at an explicit index.
            span_len = len((snapshot.get("final_text") or "").split())
            chosen_len = len((decision["chosen_text"] or "").split())
            if span_len and chosen_len and span_len != chosen_len:
                refused_partial_span.append((klal_id, word_index))
                continue
            new_text = apply_replace(klal["clean_text"], word_index, snapshot.get("final_text"), decision["chosen_text"])
            if new_text is None:
                skipped_drift.append((klal_id, word_index))
                continue
            klal["clean_text"] = new_text
            # Carry it into the heading if it landed there (see
            # sync_heading_word). Only for a SINGLE-word span: a multi-word
            # replace changes the heading's word count too, and that is the
            # reported case below, not the synced one.
            _orig = (snapshot.get("final_text") or "").split()
            if len(_orig) == 1 and sync_heading_word(klal, word_index, _orig[0], decision["chosen_text"]):
                applied.append((klal_id, word_index, "heading-sync"))
                n_heading_sync += 1
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
            # An 'insert'-opcode decision has exactly two coherent answers:
            # chosen_text == final_text ("keep the whole span", handled as a
            # no-op above) or chosen_text == "" ("remove the whole span").
            # Anything else names a DIFFERENT span than the one stored, and
            # apply_insert_removal cannot express that - it takes final_text
            # and deletes all of it, ignoring chosen_text entirely.
            #
            # Found 2026-08-30, after it fired: klal 66 w0 stored `סו אין`,
            # the reviewer chose the engines' `סו`, and the run deleted BOTH
            # words - dropping the klal marker AND the `אין` that negates the
            # whole klal ("a court CANNOT annul" became "a court CAN"). The
            # vision check on that very candidate reads `אין` in the print at
            # 0.95, and klal 57 w0 is the identical `נז אין` shape the
            # reviewer kept. Sibling of the ★1 finding above: same branch,
            # same cause - chosen_text was never consulted on this path.
            if decision["chosen_text"]:
                refused_partial_span.append((klal_id, word_index))
                continue
            new_text = apply_insert_removal(klal["clean_text"], word_index, snapshot.get("final_text"))
        elif opcode == "delete":
            new_text = apply_delete_insertion(klal["clean_text"], word_index, decision["chosen_text"])
        else:
            skipped_drift.append((klal_id, word_index))
            continue

        if new_text is None:
            skipped_drift.append((klal_id, word_index))
            continue

        word_count_shifts[klal_id] = (
            word_index, cio.word_count_of(new_text) - cio.word_count_of(klal))
        klal["clean_text"] = new_text
        # A word-count change inside the heading run shifts the HEADING's own
        # indices too, and there is no safe one-word mapping to sync - so this
        # is REPORTED rather than guessed at. The gated invariant
        # test_every_title_is_a_prefix_of_its_own_body will fail on it, which is
        # the intended backstop; this message is so the operator knows why.
        if word_index <= len(cio.title_words_of(klal)):
            heading_desync.append((klal_id, word_index, opcode))
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
        if decision["id"] in already_applied or decision["id"] in settled_by_successor:
            skipped_already_applied.append((klal_id, word_index))
            continue
        klal = by_klal.get(klal_id)
        if klal is None:
            skipped_drift.append((klal_id, word_index))
            continue
        # WHERE, asked once - see resolved_position(). Everything below reads this
        # local (the original_word check, the text mutation, the shift bookkeeping,
        # the apply_event, the reporting), so the position is resolved here and
        # nowhere else. That is why this is one line at each loop rather than an
        # edit to the 26 places that consume it.
        word_index, _how = resolved_position(decision, klal, word_index, id_state, backfilled)
        if word_index is None:
            skipped_drift.append((klal_id, decision.get("word_index")))
            print(f"  SKIP klal {klal_id} word {decision.get('word_index')}: "
                  f"its word was deleted from the corpus by a later ruling")
            continue
        original_word = (decision.get("candidate_snapshot") or {}).get("original_word")
        chosen_text = decision["chosen_text"]

        # Whether a PREVIOUS decision this run already moved this klal's
        # indices - captured BEFORE the multi-word block below can add this
        # klal on its own behalf. Reading the set directly in the replace
        # branch instead made a multi-word replace skip ITSELF: it adds, then
        # the branch it falls through to sees its own entry. (Caught 2026-08-31
        # by test_a_manual_replace_is_deferred_after_an_earlier_shift_in_the_
        # same_klal, which reported "Applied: 0" where it expected 1 - the same
        # self-skip the 2026-08-27 comment below predicted for the insert path.)
        klal_already_shifted = klal_id in word_count_changed_klalim

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
            # review_queue_part1.json candidate this decision type doesn't
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
            # A same-count replace does not itself shift anything, but it is
            # INDEXED, and an earlier decision in this klal this run may already
            # have shifted the position it names. Deferring it is the same
            # answer the three branches above give, for the same reason.
            #
            # WIDENED 2026-08-31. The 2026-08-27 remedy stopped at "make a
            # multi-word replace claim the per-run slot", and that is not
            # sufficient to prevent the corruption the finding itself
            # describes: the slot stops a SECOND word-count change, while the
            # decision actually at risk is the ordinary single-word one that
            # follows a shift. Usually apply_manual_correction's own drift
            # check saves it - words[word_index] no longer equals
            # original_word, so it returns None. It does NOT save the case
            # where the shifted-into position holds the SAME word: a repeated
            # word (`גימל גימל`), where the check passes and the run rewrites
            # the wrong occurrence, silently, with the reviewer's note
            # attached to a word they never looked at.
            #
            # Live exposure when written: 0 - measured over every unapplied
            # manual decision, 1 klal (74) has more than one and all three of
            # its decisions are word-count-changing, which the existing gate
            # already handles. Latent, and cheap to close.
            if klal_already_shifted:
                print(f"  SKIP klal {klal_id} word {word_index}: a word-count-changing "
                      f"decision already applied for this klal this run, so this index may "
                      f"have moved - run ./rebuild_all.sh, then this script again.")
                continue
            new_text = apply_manual_correction(klal["clean_text"], word_index, original_word, chosen_text)
            kind = "manual"

        if new_text is None:
            skipped_drift.append((klal_id, word_index))
            continue
        if kind in ("manual-delete", "manual-insert") or cio.word_count_of(new_text) != cio.word_count_of(klal):
            word_count_shifts[klal_id] = (
                word_index, cio.word_count_of(new_text) - cio.word_count_of(klal))
        klal["clean_text"] = new_text
        if kind == "manual" and sync_heading_word(klal, word_index, original_word, chosen_text):
            applied.append((klal_id, word_index, "heading-sync"))
            n_heading_sync += 1
        elif kind in ("manual-delete", "manual-insert") and word_index <= len(cio.title_words_of(klal)):
            heading_desync.append((klal_id, word_index, kind))
        if kind in ("manual-delete", "manual-insert"):
            word_count_changed_klalim.add(klal_id)
        n_manual += 1
        applied.append((klal_id, word_index, kind))
        if not args.dry_run:
            rd.append_decision("apply_event", klal_id=klal_id, word_index=word_index,
                                applied_decision_id=decision["id"])

    # ---- title_correction: item 39's missing apply path -------------------
    #
    # `title` is corpus text under the single-source-of-truth rule, but every
    # writer in this file until 2026-09-03 wrote `clean_text` and nothing else,
    # so the five title repairs of 2026-08-31 had to be HAND-EDITED into
    # part1.json as a recorded exception to that rule. This is the path they
    # should have taken.
    #
    # It reuses apply_manual_correction / apply_manual_deletion unchanged: both
    # take a TEXT and return a text, so they were already field-agnostic, and a
    # title index is `title.split(' ')` exactly as a body index is
    # `clean_text.split(' ')` (cio.title_words_of). Not a parallel copy - the
    # same two functions with a different string (Lesson 13).
    #
    # The address spaces are separate, so the per-run word-count gate is too: a
    # title replace that changes word count shifts later TITLE indices only, and
    # a body edit in the same klal shifts nothing in the heading.
    #
    # One shape to know when ruling on the LAST word of a title: every title in
    # this corpus ends with a period glued to its final word (measured: 222 of
    # 222), so `original_word` for that position is e.g. `שכר.`, period included.
    # The drift check compares exactly, so a ruling recorded without it is
    # skipped rather than misapplied.
    title_decisions = rd.all_current("title_correction")
    title_count_changed_klalim = set()
    for (klal_id, word_index), decision in sorted(title_decisions.items()):
        if decision["id"] in already_applied or decision["id"] in settled_by_successor:
            skipped_already_applied.append((klal_id, word_index))
            continue
        klal = by_klal.get(klal_id)
        if klal is None:
            skipped_drift.append((klal_id, word_index))
            continue
        snapshot = decision.get("candidate_snapshot") or {}
        original_word = snapshot.get("original_word")
        chosen_text = decision["chosen_text"]

        # A WHOLE-HEADING ruling replaces the field outright, drift-checked
        # against the entire stored string rather than one word. This is the
        # shape an EXTENT fix takes - a heading that swallowed body text, where
        # the repair removes a run of words and word-by-word deletion would cost
        # one apply/rebuild cycle per word.
        if snapshot.get("whole"):
            if (klal.get("title") or "") != (snapshot.get("original_title") or ""):
                skipped_drift.append((klal_id, word_index))
                continue
            if klal_id in title_count_changed_klalim:
                print(f"  SKIP klal {klal_id} heading: another heading decision already "
                      f"applied for this klal this run - run ./rebuild_all.sh, then this "
                      f"script again.")
                continue
            title_count_changed_klalim.add(klal_id)
            klal["title"] = chosen_text
            n_title += 1
            applied.append((klal_id, word_index, "title-whole"))
            if not args.dry_run:
                rd.append_decision("apply_event", klal_id=klal_id, word_index=word_index,
                                    applied_decision_id=decision["id"])
            continue

        if klal_id in title_count_changed_klalim:
            print(f"  SKIP klal {klal_id} title word {word_index}: another word-count-changing "
                  f"title decision already applied for this klal this run - run "
                  f"./rebuild_all.sh, then this script again.")
            continue
        changes_count = chosen_text == "" or manual_correction_changes_word_count(chosen_text)
        if chosen_text == "":
            new_title = apply_manual_deletion(klal.get("title") or "", word_index, original_word)
            kind = "title-delete"
        else:
            new_title = apply_manual_correction(
                klal.get("title") or "", word_index, original_word, chosen_text)
            kind = "title"
        if new_title is None:
            skipped_drift.append((klal_id, word_index))
            continue
        if changes_count:
            title_count_changed_klalim.add(klal_id)
        klal["title"] = new_title
        n_title += 1
        applied.append((klal_id, word_index, kind))
        if not args.dry_run:
            rd.append_decision("apply_event", klal_id=klal_id, word_index=word_index,
                                applied_decision_id=decision["id"])

    if not args.dry_run and (n_replace or n_insert_delete or n_manual or n_title):
        save_part1(part1)
        # STABLE WORD IDS FOLLOW THE CORPUS, in the same step that writes it.
        #
        # Lesson 35 is that promoting a decision has side effects on everything
        # describing the corpus, and every one has to happen in the same breath
        # or the description rots against the thing it describes. The id sidecar
        # is one more such description - and the one that exists precisely so a
        # ruling survives this edit, so leaving it a step behind would defeat it.
        #
        # DIFF-DRIVEN off `words_before`, which this function already captures
        # for flag reindexing: one code path covers replace, insert, delete,
        # manual and title, including branches added later. Instrumenting each
        # mutation site instead is how Lesson 34's defect got fixed three times
        # in three branches of one function.
        #
        # Best-effort by design: an unseeded corpus (no sidecar yet) must not
        # stop a correction from being applied. What it must not do is fail
        # SILENTLY, so a klal whose sidecar is out of step is named.
        try:
            touched, id_problems = widentity.follow_corpus(words_before, part1)
            if touched:
                print(f"  word ids reconciled for {touched} klal(im)")
            for problem in id_problems:
                print(f"  WARNING: {problem}")
        except Exception as e:  # noqa: BLE001
            print(f"  WARNING: word ids not updated ({type(e).__name__}: {e}) - "
                  f"run tools/seed_word_identity.py --verify before trusting them")

    # The review state that has to follow the corpus. Deliberately AFTER the
    # corpus is written: a flag closed against an edit that never landed would be
    # worse than one left open.
    closed_flags, moved_flags, unverified_shifts, moved_decisions = [], [], [], []
    if not args.dry_run:
        for klal_id, word_index, kind in applied:
            if close_flag_satisfied_by(klal_id, word_index,
                                       decisions.get((klal_id, word_index))
                                       or manual_decisions.get((klal_id, word_index)), kind):
                closed_flags.append((klal_id, word_index))
        for klal_id, (position, delta) in sorted(word_count_shifts.items()):
            if not delta:
                continue
            moved, unverified = reindex_flags_after_shift(
                klal_id, position, delta, words_before.get(klal_id, []),
                cio.words_of(by_klal[klal_id]),
                {w for k, w in closed_flags if k == klal_id})
            moved_flags += [(klal_id, a, b) for a, b in moved]
            unverified_shifts += [(klal_id, a, b, why) for a, b, why in unverified]
            d_moved, d_unverified = reindex_pending_decisions_after_shift(
                klal_id, position, delta, words_before.get(klal_id, []),
                cio.words_of(by_klal[klal_id]))
            moved_decisions += [(klal_id, a, b) for a, b in d_moved]
            unverified_shifts += [(klal_id, a, b, why) for a, b, why in d_unverified]

    tag = "[DRY RUN] " if args.dry_run else ""
    print(f"\n{tag}Applied: {len(applied)} ({n_replace} replace, {n_insert_delete} insert/delete, "
          f"{n_manual} manual, {n_title} title, {n_noop} confirmed-no-op, "
          f"{n_heading_sync} heading-sync)")
    for kid, widx, kind in applied:
        print(f"  klal {kid} word {widx}: {kind}")

    if heading_desync:
        print(f"\n{len(heading_desync)} edit(s) changed the word count INSIDE a klal's heading run. "
              f"`title` is a second copy of those words and was NOT adjusted - rule on the heading "
              f"itself (the \u270e Heading button) so the two agree again:")
        for kid, widx, kind in heading_desync:
            print(f"  klal {kid} word {widx} ({kind})")

    if skipped_already_applied:
        print(f"\n{len(skipped_already_applied)} decision(s) skipped - already promoted into "
              f"part1.json by an earlier run (apply_event on record), no action needed:")
        for kid, widx in skipped_already_applied:
            print(f"  klal {kid} word {widx}")

    if recovered_from_dropped_entry:
        print(f"\n{len(recovered_from_dropped_entry)} decision(s) had NO candidate entry left in "
              f"review_queue_part1.json (the queue drops a dispute once it is decided) and were "
              f"drift-checked against part1.json itself instead - see "
              f"snapshot_still_matches_corpus():")
        for kid, widx in recovered_from_dropped_entry:
            print(f"  klal {kid} word {widx}")

    if closed_flags:
        print(f"\n{len(closed_flags)} open flag(s) closed - a decision was applied at that exact "
              f"word, which answers them:")
        for kid, widx in closed_flags:
            print(f"  klal {kid} word {widx}")

    if moved_flags:
        print(f"\n{len(moved_flags)} open flag(s) REINDEXED onto the word they name, after a "
              f"word-count change shifted this klal's later indices:")
        for kid, a, b in moved_flags:
            print(f"  klal {kid} word {a} -> word {b}")

    if moved_decisions:
        print(f"\n{len(moved_decisions)} PENDING decision(s) reindexed onto the word they name, "
              f"after a word-count change shifted this klal's later indices. Re-run this script "
              f"after ./rebuild_all.sh to apply them:")
        for kid, a, b in moved_decisions:
            print(f"  klal {kid} word {a} -> word {b}")

    if unverified_shifts:
        print(f"\n{len(unverified_shifts)} record(s) sit past a word-count change and were NOT "
              f"moved, so they were LEFT WHERE THEY ARE and may now name the wrong word - check "
              f"these by hand:")
        for kid, a, b, reason in unverified_shifts:
            why = ("the shifted index is already taken" if reason == "collision"
                   else "the word there is not the word it names")
            print(f"  klal {kid} word {a} (would have been word {b}) - {why}")
        # AND TO A FILE, APPEND-ONLY. Added 2026-09-07 (item 0CU) after the
        # reviewer asked "where??" about one of these and the answer was gone:
        # this was the only actionable output of the whole run that existed
        # NOWHERE but stdout, so a piped or scrolled terminal loses it silently.
        # Lesson 32 exactly - a finding that only prints has not been delivered.
        #
        # APPEND, not overwrite, and that is the point: the next apply run that
        # verifies everything cleanly would otherwise erase a finding nobody had
        # acted on yet. Every other per-run report here is safe to overwrite
        # because it is re-derived from current state; this one is not derivable
        # after the fact at all - the shift it describes has already happened.
        _record_unverified_shifts(unverified_shifts)

    if refused_partial_span:
        print(f"\n{len(refused_partial_span)} decision(s) REFUSED - the chosen text does not "
              f"match the span it answers: an 'insert' decision that is neither the whole stored "
              f"span nor empty, or a 'replace' whose chosen text has a different WORD COUNT than "
              f"the span. Applying either would delete text the reviewer did not vote to delete. "
              f"Re-rule these against the exact word:")
        for kid, widx in refused_partial_span:
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
