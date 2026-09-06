#!/usr/bin/env python3
"""
tools/seed_word_identity.py

[STANDALONE] Create or check `word_identity.json` - the stable word-id sidecar.

WHAT AN ID IS FOR. `word_index` dies on any earlier edit and `(word,
occurrence)` dies when the word's own text is corrected, which is what a ruling
DOES - measured on the live ledger 2026-09-06, 543 of 594 current rulings do not
resolve, and 517 of those are unresolvable precisely because they were applied
successfully. See pipeline/word_identity.py's header for the full argument.

SEEDING IS A ONE-WAY DOOR FOR CONTINUITY, so it is deliberate and reported.
Ids are only meaningful relative to when they were handed out: re-seeding a klal
throws away every existing id for it, so any ruling that recorded one is
silently re-pointed at whatever word now sits at that ordinal. This script will
not re-seed a klal that already has ids unless you pass --reseed and name what
you are giving up.

  --verify   report whether the sidecar agrees with the corpus, change nothing
  --apply    write it (new klalim only, unless --reseed)
  --reseed   also re-number klalim that already have ids - destroys continuity

Dry run by default.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
INSTALL_DIR = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(INSTALL_DIR, "pipeline"))

import corpus_io as cio  # noqa: E402
import word_identity as wid  # noqa: E402


def corpus_klalim(all_parts):
    """Part 1 only by default. The sidecar CAN cover all 667 and the invariant
    only checks what it is given; seeding Parts 2-3 writes no corpus text and is
    outside the Parts 2-3 gate either way, but it is opt-in so a run cannot
    quietly take on 445 klalim nobody asked about."""
    if all_parts:
        return cio.load_demo_dataset()
    return cio.load_part1_sorted()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="write the sidecar")
    ap.add_argument("--verify", action="store_true",
                    help="check the sidecar against the corpus and exit non-zero on a mismatch")
    ap.add_argument("--reseed", action="store_true",
                    help="re-number klalim that already have ids (destroys continuity)")
    ap.add_argument("--all-parts", action="store_true",
                    help="cover klalim 1-667 rather than Part 1 only")
    args = ap.parse_args()

    klalim = corpus_klalim(args.all_parts)
    state = wid.load_for_update()

    if args.verify:
        problems = wid.verify(klalim, state)
        print(f"{len(klalim)} klal(im) checked against {wid.path()}")
        if not problems:
            print("  consistent - every klal has one unique id per word")
            return 0
        print(f"  {len(problems)} problem(s):")
        for p in problems:
            print(f"    {p}")
        return 1

    fresh, existing = [], []
    for k in klalim:
        (existing if k["klal_id"] in state else fresh).append(k)

    print(f"{len(klalim)} klal(im) in scope")
    print(f"  {len(fresh):>4} with no ids yet - will be seeded")
    print(f"  {len(existing):>4} already have ids - "
          f"{'WILL BE RE-NUMBERED' if args.reseed else 'left alone'}")
    if existing and args.reseed:
        print("  re-seeding discards the ids those klalim already handed out; any "
              "ruling that recorded one will point at whatever word now sits at "
              "that ordinal.")

    targets = fresh + (existing if args.reseed else [])
    for k in targets:
        state[k["klal_id"]] = wid.seed_klal(cio.words_of(k))

    if not args.apply:
        print("\nDRY RUN - nothing written. Re-run with --apply.")
        return 0

    wid.save(state)
    print(f"\nWrote {wid.path()} - {len(targets)} klal(im) seeded, "
          f"{sum(len(wid.ids_for(state, k['klal_id'])) for k in klalim)} words addressed")
    problems = wid.verify(klalim, state)
    if problems:
        print(f"  WARNING: {len(problems)} problem(s) remain after seeding:")
        for p in problems:
            print(f"    {p}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
