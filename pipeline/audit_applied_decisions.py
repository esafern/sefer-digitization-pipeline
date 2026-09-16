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
import os

import corpus_io as cio
import review_decisions as rd
import scan_alignment as sa

# Loaded once: word_bboxes_resolved() re-reads the 187 KB regions file otherwise,
# and this runs per failed decision.
_REGIONS = sa.load_regions()

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
    words = cio.words_of(klal)
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
    # FIXED 2026-08-23: this compared the whole chosen_text against
    # words[word_index], a SINGLE word, so every multi-word manual correction
    # reported a false MISMATCH - "expected 'איידי דקתני במתניתין ...' at
    # word_index 23, found 'איידי'". It had been crying wolf on klal 9 word 23
    # since the 2026-08-21 klal 9/10 boundary fix introduced the multi-word
    # manual-insert case, and did it again on klal 16 word 163. That is worse
    # than a cosmetic bug in THIS script specifically: its only job is to
    # report applied decisions that stopped being reflected in the corpus, and
    # a check that routinely fires on correctly-applied data is a check people
    # learn to scroll past. Compare the full span, the same way
    # apply_reviewer_decisions.apply_replace/apply_delete_insertion write it.
    span = chosen.split()
    live_span = words[word_index:word_index + len(span)]
    if live_span == span:
        return "ok"
    return (f"MISMATCH: expected {chosen!r} at word_index {word_index}, "
            f"found {' '.join(live_span)!r}")


def check_punctuation_choice(decision, klal):
    if decision["chosen_source"] != "accept":
        return "unverifiable_word_count_change"  # reject never inserts anything to verify
    words = cio.words_of(klal)
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
# The decision types that REPLACE the word at their word_index. A later applied
# one of these legitimately moves the corpus past an earlier one's claim at the
# same word, whichever UI recorded it - which is what supersession means.
#
# `punctuation_choice` is deliberately NOT here. An accepted one INSERTS a `[.]`
# at that index and pushes the rest along; it never overwrites the word. Letting
# it suppress a replacement decision would mask a genuinely reverted correction,
# and that is the one case this script exists to catch (klal 1 w97).
REPLACEMENT_TYPES = frozenset({"candidate_choice", "disputed_choice", "manual_correction"})


def check_witness_choice(decision, klal):
    """ADDED 2026-09-16 (item 0HE finding 1). `witness_choice` was not in
    CHECKERS, so every witness ruling fell through the bare `continue` below and
    was not counted either - and on the second book EVERY ruling is a witness
    ruling, so this script printed "Checked 0 applied decisions ... no ruling
    carries a stale address" over a corpus holding four applied ones. That is
    the same shape as the `disputed_choice` omission recorded above, a type
    later.

    Read exactly as apply_reviewer_decisions.witness_choice_edit() writes one:
    * the position is the SNAPSHOT's `word_index`, never the ruling's key, which
      holds the OCR token index (item 0GW's field trap, which already cost one
      false alarm);
    * the words it replaced are the snapshot's `master_reading`, else its
      `docai_reading`;
    * `unreadable` writes nothing, `remove` and a gap insertion change the word
      count, and so does a replace whose chosen text is a different length -
      none of those is verifiable by position afterwards, which is the same
      answer the checkers beside this one give for the same shapes.
    A confirmation (chosen == what was there) IS verifiable: it claims that text
    is still standing.
    """
    snap = decision.get("candidate_snapshot") or {}
    chosen = (decision.get("chosen_text") or "").split()
    seen = (snap.get("master_reading") or snap.get("docai_reading") or "").split()
    if (decision.get("chosen_source") in ("unreadable", "remove") or snap.get("gap")
            or not chosen or len(chosen) != len(seen)):
        return "unverifiable_word_count_change"
    words = cio.words_of(klal)
    word_index = snap.get("word_index")
    if word_index is None or word_index < 0 or word_index + len(chosen) > len(words):
        return (f"MISMATCH: the ruling's snapshot names word_index {word_index} "
                f"(klal now has {len(words)} words)")
    live = words[word_index:word_index + len(chosen)]
    if live == chosen:
        return "ok"
    return f"MISMATCH: expected {chosen!r} at word_index {word_index}, found {live!r}"


def check_title_correction(decision, klal):
    """ADDED 2026-09-16 with the above, and for the same reason: `title_correction`
    was not in CHECKERS either, so the 7 applied heading rulings on the live
    ledger were 7 of 1,005 applied and the script reported 998 checked.

    `title` is its own address space - `title.split(' ')`, not the body's - so
    this reads cio.title_words_of() and nothing here may be compared against
    clean_text. A whole-heading ruling (`whole`) replaces the field outright, so
    the whole string is what it claims.
    """
    snap = decision.get("candidate_snapshot") or {}
    chosen = decision.get("chosen_text") or ""
    if snap.get("whole"):
        live = klal.get("title") or ""
        return "ok" if live == chosen else f"MISMATCH: expected heading {chosen!r}, found {live!r}"
    if chosen == "":
        return "unverifiable_word_count_change"
    words = cio.title_words_of(klal)
    word_index = decision["word_index"]
    if word_index is None or word_index < 0 or word_index >= len(words):
        return (f"MISMATCH: title word_index {word_index} out of range "
                f"(heading now has {len(words)} words)")
    span = chosen.split()
    live = words[word_index:word_index + len(span)]
    if live == span:
        return "ok"
    return f"MISMATCH: expected {chosen!r} at title word_index {word_index}, found {' '.join(live)!r}"


CHECKERS = {
    "disputed_choice": check_candidate_choice,
    "candidate_choice": check_candidate_choice,
    "manual_correction": check_manual_correction,
    "punctuation_choice": check_punctuation_choice,
    "witness_choice": check_witness_choice,
    "title_correction": check_title_correction,
}

# The types whose position is a BODY word index, which is the only space the
# relocation machinery below (find_span / _bbox_word_index, both reading
# clean_text) can speak about. A heading ruling's index is a position in
# `title.split(' ')`, and the heading is a PREFIX of the body - so searching the
# body for its words finds them and would report a real mismatch as a benign
# shift. It is reported as a mismatch instead.
RELOCATABLE_TYPES = frozenset(set(CHECKERS) - {"title_correction"})


def reported_position(decision):
    """The word index to REPORT a ruling at. For `witness_choice` the ruling's
    own `word_index` is an OCR token number and naming it would send the reader
    to the wrong word (item 0GW); the corpus position is in the snapshot."""
    if decision["decision_type"] == "witness_choice":
        return (decision.get("candidate_snapshot") or {}).get("word_index")
    return decision["word_index"]


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
    # WIDENED 2026-09-01, on the reviewer's ruling. This passed
    # decision["decision_type"], so a manual_correction superseded by a later,
    # also-applied disputed_choice AT THE SAME WORD was not recognised and was
    # reported as a mismatch - klal 66 w29 (`מהדיא` then the correct `מההיא`)
    # and klal 39 w242 (`ור` then the correct `ור'`). Two decisions that replace
    # the same word describe the same word; which UI recorded them does not
    # change whether the corpus has legitimately moved on. Widened across the
    # REPLACEMENT types only - see REPLACEMENT_TYPES for why punctuation_choice
    # must keep being checked against its own type alone.
    kind = decision["decision_type"]
    group = REPLACEMENT_TYPES if kind in REPLACEMENT_TYPES else {kind}
    history = [r for r in rd.history_for(decision["klal_id"], decision["word_index"])
               if r.get("decision_type") in group]
    seen_self = False
    for r in history:
        if r["id"] == decision["id"]:
            seen_self = True
            continue
        if seen_self and r["id"] in already_applied:
            return True
    return False


def expected_span(decision):
    """The word(s) an applied decision claims it wrote, as a list."""
    if decision["decision_type"] == "punctuation_choice":
        return ["[.]"]
    return (decision.get("chosen_text") or "").split()


# How far a legitimately-shifted decision can have moved before its relocation
# stops being credible.
#
# ADDED 2026-09-01 (code review finding #1). find_span() searches the WHOLE
# klal, so the relocation below accepted a hit at any distance - and one did:
# klal 10's applied candidate_choice claims `כתבו` at w85, the corpus has `למד`
# there and `כתבו` at w74, ELEVEN words away and a plainly different occurrence
# in a klal whose applies shift by one. It was being reported as "reflected at
# word_index 74 (-11)" and, because the drift list only printed under an env
# var, printed nowhere. That single reclassification moved the headline from
# 57 MISMATCH to 1 - so the one thing this script exists to catch, a correction
# that silently stopped being true, was being absorbed by the feature meant to
# reduce noise around it.
#
# Measured over all 56 relocations on the live corpus: legitimate shifts span
# -3..+2, and 44 of them are exactly ±1. The outlier is -11, alone beyond ±3.
#
# Uniqueness was tried first as the discriminator and is WRONG - it was measured
# rather than assumed, which is the only reason it did not ship: klal 10's false
# relocation is the one case whose span occurs EXACTLY ONCE in its klal, while
# 36 of the legitimate ones match a word appearing 2-6 times (`אלהים` six times
# in klal 69, `אליבא` six times in klal 159). Requiring a unique occurrence
# would have rejected two thirds of the true relocations and kept the false one.
#
# A shift bound derived from the LEDGER was also tried and is unsound: klalim
# 159 and 163 show real ±1 shifts while every applied decision in them is
# word-count-neutral, because the pipeline's own editorial-mark insertions move
# indices without any decision recording it. The ledger cannot see every edit,
# so it cannot bound the shift.
#
# 5 rather than 3 leaves headroom for one more edit in either direction.
#
# CORRECTED 2026-09-02, ONE DAY LATER, BY BETTER EVIDENCE. The bound above was
# derived from shift MAGNITUDE alone, which is the weakest thing available - and
# it was wrong about the very case it was written for. Mapping each decision's
# snapshot BBOX onto the word standing at that scan position now (the same
# geometry the dashboard highlights with) shows klal 10's `כתבו` really is at
# w74: the ink and the letters agree, at a shift of -11, and the ruling was
# honoured rather than lost. Genuine shifts corroborated that way reach -31.
#
# So the magnitude bound is now the FALLBACK, used only where no scan position
# was recorded. Where a bbox exists it decides, because "which word is at this
# place on the page" is a question about the page, and a shift count is a guess
# about a number. This is Lesson 9 applied to the audit itself: prefer two
# independent signals over one confident-sounding one.
MAX_EXPLAINABLE_SHIFT = 5


def find_span(klal, span):
    """Every index where `span` appears in the klal, EXACT match only.

    Deliberately not fuzzy (Lesson 5: subsequence matching cannot settle an
    exact-position claim). This does not loosen the audit - the exact check at
    the decision's own word_index still has to pass or fail on its own. It only
    classifies a FAILURE: is the text absent from the corpus, or present at a
    different index because a later apply in the same klal shifted everything
    after it (Lesson 35)?
    """
    if not span:
        return []
    words = cio.words_of(klal)
    n = len(span)
    return [i for i in range(len(words) - n + 1) if words[i:i + n] == span]


# Per-klal cache for the alignment `_bbox_word_index` needs.
#
# main() iterates decisions sorted by UUID, not grouped by klal, so a klal with
# several stale rulings re-ran the full per-page SequenceMatcher alignment once
# PER DECISION. tools/repoint_stale_decisions.py - written the same week, doing
# the same lookup - already carried exactly this {klal_id: resolved} cache; this
# file did not. Found by the 2026-09-03 ultra review.
#
# Keyed by klal_id alone: `words` is derived from the same klal object and
# nothing mutates the corpus during an audit, which is read-only by design.
_RESOLVED_CACHE = {}


def _resolved_bboxes(klal, words):
    kid = klal["klal_id"]
    if kid not in _RESOLVED_CACHE:
        _RESOLVED_CACHE[kid] = sa.word_bboxes_resolved(kid, words, _REGIONS)
    return _RESOLVED_CACHE[kid]


def _bbox_word_index(decision, klal):
    """Which word occupies this decision's recorded scan position now, or None.

    ADDED 2026-09-02. `candidate_choice`/`disputed_choice` snapshots carry the
    crop's bbox and page; mapping that onto the current alignment answers "where
    did this word GO" from the page rather than from a shift count.
    `manual_correction` recorded no scan position before this date, so this
    returns None for those and the magnitude bound still governs them.
    """
    snap = decision.get("candidate_snapshot") or {}
    bbox, page = snap.get("bbox"), snap.get("page")
    if not bbox or page is None:
        return None
    words = cio.words_of(klal)
    resolved = _resolved_bboxes(klal, words)
    here = [(i, bb) for i, (bb, pg) in resolved.items() if bb and pg == page]
    if not here:
        return None

    def centre(b):
        return ((b["x1"] + b["x2"]) / 2, (b["y1"] + b["y2"]) / 2)

    ax, ay = centre(bbox)
    return min(here, key=lambda kv: (centre(kv[1])[0] - ax) ** 2
                                    + (centre(kv[1])[1] - ay) ** 2)[0]


def main():
    part1 = load_part1()
    already_applied = rd.applied_decision_ids()

    n_ok = n_mismatch = n_unverifiable = n_missing_klal = n_superseded = 0
    n_drifted = 0
    mismatches, drifted = [], []
    # WHAT THIS RUN DID NOT LOOK AT. Item 0HE finding 1: the `continue` below
    # was bare and the skipped ruling never reached `total`, so a type missing
    # from CHECKERS was invisible in the output as well as unchecked - twice,
    # `disputed_choice` after the rename and then `witness_choice` and
    # `title_correction`. An unchecked type is now named in the summary, so the
    # next one announces itself instead of being found by arithmetic.
    unchecked = {}

    for decision_id in sorted(already_applied):
        decision = rd.find_by_id(decision_id)
        if decision is None:
            continue  # defensive: an apply_event referencing an id not in the log at all
        decision_type = decision["decision_type"]
        checker = CHECKERS.get(decision_type)
        if checker is None:
            unchecked[decision_type] = unchecked.get(decision_type, 0) + 1
            continue
        klal_id, word_index = decision["klal_id"], reported_position(decision)

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
            # A failed exact check is not automatically a lost correction. If
            # the text this decision wrote is still in the klal at a different
            # index, a later apply shifted it and the decision IS still
            # reflected - the stale number is the decision's word_index, not
            # the corpus. Counting those as "no longer reflected in the corpus"
            # is what made this script report 75 and be scrolled past.
            # Only for a ruling addressed in the BODY - see RELOCATABLE_TYPES.
            hits = (find_span(klal, expected_span(decision))
                    if decision_type in RELOCATABLE_TYPES else [])
            nearest = (min(hits, key=lambda i: abs(i - word_index))
                       if hits and word_index is not None else None)
            # The ink outranks the magnitude: where the decision recorded a scan
            # position AND the word now standing there is one of the hits, the
            # relocation is corroborated by two independent signals and the
            # distance does not matter.
            by_bbox = _bbox_word_index(decision, klal)
            corroborated = by_bbox is not None and hits and by_bbox in hits
            if corroborated:
                nearest = by_bbox
            if nearest is not None and (corroborated
                                        or abs(nearest - word_index) <= MAX_EXPLAINABLE_SHIFT):
                n_drifted += 1
                drifted.append(f"klal {klal_id} word {word_index} ({decision_type}, "
                               f"decision {decision_id}): reflected at word_index "
                               f"{nearest} ({nearest - word_index:+d})")
            else:
                # Either the text is gone, or it is present so far away that it
                # is a different occurrence of the same word rather than the one
                # this decision wrote. Both are MISMATCHES - a relocation this
                # script cannot explain must be handed to a human, not absorbed.
                n_mismatch += 1
                far = ("" if nearest is None else
                       f" (nearest occurrence of {' '.join(expected_span(decision))!r} is at "
                       f"word_index {nearest}, {nearest - word_index:+d} - too far to be a shift, "
                       f"see MAX_EXPLAINABLE_SHIFT)")
                mismatches.append(f"klal {klal_id} word {word_index} ({decision_type}, "
                                   f"decision {decision_id}): {result}{far}")

    total = (n_ok + n_mismatch + n_unverifiable + n_missing_klal
             + n_superseded + n_drifted)
    print(f"Checked {total} applied decisions across "
          f"{'/'.join(sorted(CHECKERS))}:")
    print(f"  {n_ok} confirmed still reflected in part1.json")
    print(f"  {n_superseded} superseded by a later, also-applied decision at the same key (expected, not checked)")
    print(f"  {n_unverifiable} word-count-changing, not position-verifiable post-hoc (see docstring)")
    print(f"  {n_drifted} reflected, but at a SHIFTED index - a later apply in the "
          f"same klal moved them (the decision's word_index is stale, not the corpus)")
    print(f"  {n_mismatch + n_missing_klal} MISMATCH - applied decision no longer reflected in the corpus")
    if unchecked:
        print(f"  {sum(unchecked.values())} NOT CHECKED - no checker is registered for their "
              f"decision type, so this run says nothing about them: "
              f"{', '.join(f'{t} {n}' for t, n in sorted(unchecked.items()))}")
    if mismatches:
        print()
        for m in mismatches:
            print(f"  {m}")
    # PRINTED BY DEFAULT since 2026-09-01 (same review finding). These were
    # behind AUDIT_SHOW_DRIFT, and the hint string said "set AUDIT_SHOW_DRIFT=
    # to hide" - which could only ever be read by someone who had already set it.
    # A row moved out of the MISMATCH count has to be visible somewhere, or the
    # reclassification is just a smaller number with the evidence deleted; that
    # is Lesson 32's shape, a correct finding that reaches nobody.
    if drifted and not os.environ.get("AUDIT_HIDE_DRIFT"):
        print("\n  shifted, NOT lost - the decision's word_index is stale, not the corpus")
        print("  (set AUDIT_HIDE_DRIFT=1 to suppress this list):")
        for d in drifted:
            print(f"  {d}")

    report_stale_addresses()


def report_stale_addresses():
    """Every ruling whose recorded word_index no longer holds its own word, and
    whether a stable address could still say where it went.

    ADDED 2026-09-03 (item 0BB) as a REPORT, not a repair. The counts here are
    the honest answer to "does content-addressing fix drift": it does, but the
    ordinal has to have been recorded at ruling time, and for every ruling made
    before this existed it was not - so most of what is stale today is stale
    permanently, and the value of the change is forward-looking.

    Note what dominates and why it is not a defect: an APPLIED ruling normally
    cannot find its own word, because applying it is what replaced that word.
    Those are honoured rulings, not lost ones - the same distinction item 0AB
    had to draw when it counted 105 "orphans" and audit_applied_decisions found
    55 shifted and 2 genuinely missing.
    """
    klalim = cio.load_part1_by_id()
    applied = rd.applied_decision_ids()
    # Read ONCE: resolve_word_index() consults it per ruling, and it is a full
    # pass over the log.
    backfilled = rd.backfilled_word_ids()
    buckets = {}
    for dtype in ("candidate_choice", "disputed_choice", "manual_correction", "title_correction"):
        for (kid, widx), rec in rd.all_current(dtype).items():
            klal = klalim.get(kid)
            if klal is None or widx is None:
                continue
            words = (cio.title_words_of(klal) if dtype == "title_correction"
                     else cio.words_of(klal))
            snap = rec.get("candidate_snapshot") or {}
            if snap.get("original_word") is None:
                continue
            idx, how = rd.resolve_word_index(rec, words, backfilled=backfilled)
            if how in ("index", "word_id"):
                # "word_id" joined "index" as a clean address 2026-09-06: the
                # ruling carries a stable id and the sidecar still knows where
                # that word is, which is a BETTER answer than the recorded index
                # rather than a worse one. Without this it would have been
                # bucketed as a stale address and reported as a problem.
                continue
            was_applied = rec["id"] in applied
            key = ("applied" if was_applied else "UNAPPLIED", how or "unresolvable")
            buckets.setdefault(key, []).append((dtype, kid, widx, snap["original_word"]))

    # witness_choice, ADDED 2026-09-16 (item 0HE finding 1). It cannot go through
    # the loop above: its KEY is an OCR token index, not a word, and its snapshot
    # carries no `original_word` - so `resolve_word_index` would read a token
    # number as a word position and `snap["original_word"] is None` would drop
    # every row before that even mattered. Its address is the snapshot's
    # `word_index` holding the snapshot's `master_reading` (item 0GW), and that
    # is what is checked here.
    #
    # An APPLIED one normally cannot find its own word, for the reason the
    # docstring gives: applying it is what replaced that word. The row that
    # matters is an UNAPPLIED one whose word has moved - which is exactly what
    # an applied witness `remove` or gap insertion does to every later ruling in
    # its entry, because reindex_pending_decisions_after_shift does not move
    # them (item 0HE finding 2). Nothing else in the repo would say so.
    for (kid, token), rec in rd.all_current("witness_choice").items():
        klal = klalim.get(kid)
        snap = rec.get("candidate_snapshot") or {}
        widx, seen = snap.get("word_index"), (snap.get("master_reading")
                                              or snap.get("docai_reading") or "")
        if klal is None or widx is None or not seen:
            continue
        words = cio.words_of(klal)
        if words[widx:widx + len(seen.split())] == seen.split():
            continue
        key = ("applied" if rec["id"] in applied else "UNAPPLIED", "unresolvable")
        buckets.setdefault(key, []).append(("witness_choice", kid, widx, seen))

    if not buckets:
        print("\n  no ruling carries a stale address.")
        return
    print("\n  rulings whose recorded word_index no longer holds their own word:")
    for (state, how) in sorted(buckets):
        rows = buckets[(state, how)]
        note = {
            "retired": "the stable id says this word was DELETED from the corpus by a "
                       "later ruling - a definite answer, not a lost address",
            "unresolvable": "word is gone - for an APPLIED ruling this is the normal, "
                            "correct outcome; for an unapplied one it needs a human",
            "occurrence": "recovered from the recorded occurrence ordinal (item 0BB)",
            "unique": "the word occurs exactly once, so there is only one thing it can "
                      "mean - a HINT for a human re-point, never an automatic move",
        }[how]
        print(f"    {state:<10} {how:<13} {len(rows):>4}  - {note}")
        # EVERY unapplied bucket is listed since 2026-09-16, `unresolvable`
        # included. Its own note says that one "needs a human", and the report
        # then named no row, so the thing needing a human reached nobody
        # (Lesson 32). Applied rows stay counted-only: for them a word that
        # cannot be found is the normal outcome of having been applied.
        if state == "UNAPPLIED":
            for dtype, kid, widx, word in rows[:10]:
                print(f"        {dtype} klal {kid} w{widx} {word!r}")


if __name__ == "__main__":
    main()
