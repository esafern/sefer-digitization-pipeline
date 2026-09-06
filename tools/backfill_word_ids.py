#!/usr/bin/env python3
"""
tools/backfill_word_ids.py

[STANDALONE] Attach a stable word id to rulings recorded before ids existed.

WHY THIS IS TIME-SENSITIVE, which is the whole argument for running it. Ids began
2026-09-06. Every ruling before that names its word by INDEX, and an index rots
the moment an earlier edit changes its klal's word count. Right now most of those
rulings still resolve - the word is where they said, or `drift_recovery` can say
where it went. After the next few applies, some of them will not. **Backfilling
freezes an identity while it is still derivable**; waiting throws away the
evidence that makes it derivable.

WHAT IT WRITES, AND WHY NOT A SUPERSEDING COPY. A `word_id_backfill` annotation:
one row naming the ruling and the word id, with the basis that established it. It
is NOT a superseding copy of the ruling, and the difference was MEASURED rather
than argued. 582 of the 601 rulings here are already APPLIED. A superseding copy
takes a new decision id, so it drops out of `applied_decision_ids()` and the
applier stops seeing those 582 as settled: run against a ledger built that way it
reports **226 to apply** - 47 manual re-writes and 179 no-op re-confirmations -
where today it reports 4, and the drift worklist goes 22 to 380. An annotation
carries no `chosen_text` and no opcode, so no apply path can pick it up.

HOW A POSITION IS ESTABLISHED - the same resolvers the rest of the pipeline uses,
never a private copy, and the applied/unapplied split decides which:

  1. `review_decisions.resolve_word_index` - "index" (the recorded index still
     holds the recorded word) or "occurrence" (the ruling recorded WHICH
     occurrence and that occurrence exists). Both exact.
  2. For an APPLIED ruling, the word at its position is now the text the reviewer
     CHOSE, not the original - so `drift_recovery.word_identities_of(applied=True)`
     is what names it. Checked at the recorded index only; no searching.
  3. `drift_recovery.recover_klal` for the rest, which requires a shift that is
     unambiguous AND corroborated by another ruling in the klal or by the word
     being unique there.

Anything else is REFUSED and reported. "unique" is deliberately not accepted:
`resolve_word_index`'s own docstring calls it a hint for a human re-point and
never an authority, and an id asserted on it would be a guess wearing an
identity's clothes.

Every annotation records its basis, so a later reader can tell an id that was
recorded when the ruling was made from one inferred afterwards, and on what.

Dry run by default. `--apply` writes.
"""
import argparse
import collections
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
INSTALL_DIR = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(INSTALL_DIR, "pipeline"))

import corpus_io as cio  # noqa: E402
import drift_recovery as dr  # noqa: E402
import identity as idn  # noqa: E402
import review_decisions as rd  # noqa: E402
import word_identity as wid  # noqa: E402

RULING_TYPES = ("candidate_choice", "disputed_choice", "manual_correction")


def current_rulings(rows):
    """Latest ruling per (klal, word, type). Keyed with the TYPE included, unlike
    all_current(): this annotates records, and two types at one index are two
    records that each need their own id."""
    out = {}
    for r in rows:
        if r["decision_type"] in RULING_TYPES and r.get("word_index") is not None:
            out[(r["klal_id"], r["word_index"], r["decision_type"])] = r
    return out


def resolve(rec, words, klal_rulings, state, applied, backfilled):
    """(word_id, basis) for one ruling, or (None, why-refused)."""
    idx, how = rd.resolve_word_index(rec, words, id_state=state, backfilled=backfilled)
    if how in ("index", "occurrence"):
        got = wid.id_at(state, rec["klal_id"], idx)
        return (got, f"{how}: the ruling's own address still resolves, to w{idx}") \
            if got is not None else (None, "no id exists at that position")

    is_applied = rec["id"] in applied
    names = dr.word_identities_of(rec, is_applied)
    at = rec["word_index"]
    if names and 0 <= at < len(words) and words[at] in names:
        got = wid.id_at(state, rec["klal_id"], at)
        basis = ("applied: the text this ruling chose is still at its recorded index"
                 if is_applied else
                 "the word this ruling names is still at its recorded index")
        return (got, f"{basis} w{at}") if got is not None else (None, "no id there")

    stale = [r for r in klal_rulings
             if dr.stale_against(words, r, r["id"] in applied)]
    recovered, _refused = dr.recover_klal(words, stale, applied)
    if rec["id"] in recovered:
        new_at, _off, why = recovered[rec["id"]]
        got = wid.id_at(state, rec["klal_id"], new_at)
        return (got, f"drift_recovery: {why}") if got is not None else (None, "no id there")
    return None, "no exact, corroborated address - nothing to attach an id to"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="write the annotations")
    args = ap.parse_args()

    rows = rd.all_records()
    applied = rd.applied_decision_ids()
    already = rd.backfilled_word_ids()
    state = wid.load()
    if not state:
        print("no word_identity.json - run tools/seed_word_identity.py --apply first")
        return 1
    words = {k["klal_id"]: cio.words_of(k) for k in cio.load_part1()}

    rulings = current_rulings(rows)
    by_klal = collections.defaultdict(list)
    for r in rulings.values():
        by_klal[r["klal_id"]].append(r)

    todo, refused, skipped = [], [], 0
    for r in rulings.values():
        snap = r.get("candidate_snapshot") or {}
        if snap.get("word_id") is not None or r["id"] in already:
            skipped += 1
            continue
        klal_words = words.get(r["klal_id"])
        if klal_words is None:
            refused.append((r, "klal is not in part1.json (Parts 2-3 are not seeded)"))
            continue
        got, basis = resolve(r, klal_words, by_klal[r["klal_id"]], state, applied,
                             already)
        (todo if got is not None else refused).append((r, basis) if got is None
                                                      else (r, got, basis))

    print(f"{len(rulings)} current ruling(s); {skipped} already carry an id")
    print(f"  {len(todo):>4} can be given one on an exact, corroborated address")
    print(f"  {len(refused):>4} cannot - reported, never guessed at")
    kinds = collections.Counter(b.split(":")[0] for _r, _g, b in todo)
    for k, n in kinds.most_common():
        print(f"        {n:>4}  {k}")
    why = collections.Counter(b for _r, b in refused)
    for k, n in why.most_common(4):
        print(f"        {n:>4}  REFUSED: {k}")

    if not args.apply:
        print("\nDRY RUN - nothing written. Re-run with --apply.")
        return 0

    for rec, got, basis in todo:
        rd.append_decision(
            "word_id_backfill", klal_id=rec["klal_id"], word_index=rec["word_index"],
            applied_decision_id=rec["id"],
            candidate_snapshot={"word_id": got, "basis": basis,
                                "word_id_source": "backfill"},
            actor=idn.tool_actor("pipeline-script", via="backfill_word_ids"),
            reviewer="tools/backfill_word_ids.py",
            note=(f"STABLE ID {got} attached to ruling {rec['id']}, which was recorded "
                  f"before word ids existed. Established by: {basis}. This annotation "
                  f"changes no ruling and applies no text - it records WHICH WORD the "
                  f"ruling names, so the address survives future edits to this klal. "
                  f"Inferred after the fact, not recorded at ruling time, which is what "
                  f"`word_id_source: backfill` marks."))
    print(f"\nWrote {len(todo)} annotation(s). No ruling and no corpus text changed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
