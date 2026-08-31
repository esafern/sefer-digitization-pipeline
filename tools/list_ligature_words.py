#!/usr/bin/env python3
# [STANDALONE] Every corpus word set with the alef-lamed ligature `ﭏ`, and every
# word where that sort appears to have FAILED.
#
# WHY THE FIRST LIST MATTERS. This printing sets א+ל as a single sort, and that
# one worn sort is behind more confirmed corpus damage than any other single
# cause in this project: Lesson 24 (three engines producing the identical wrong
# reading, because they are all reading the same broken ink), the dropped-lamed
# corruption purged from lexicon.txt in 2026-08-15, `שמול`->`שמואל`, and the
# three `&` characters found in Part 1 on 2026-08-26 - where the sort lost BOTH
# its letters and DocAI read an ampersand. Any word containing `אל` was set with
# it and is therefore in the at-risk population, whether or not it is wrong now.
#
# THE LIGATURE CODEPOINT IS NEVER TRANSCRIBED. U+FB4F appears zero times in
# part1/2/3.json and zero times in the DocAI token stream - checked, not assumed.
# The sort reaches the corpus as the two letters `אל` when read correctly, and
# otherwise as one of the failure modes below. So "words with the ligature" is a
# question about the PRINT, answered here by the letter sequence.
#
# THE FAILURE MODES, all three observed in this corpus:
#   dropped lamed   `אליבא` -> `איבא`, `ושמואל` -> `ושמוא`   (Lesson 24)
#   dropped alef    `שמואל` -> `שמול`                        (found 2026-08-26)
#   both lost       `אל`    -> `&`                           (found 2026-08-26)
#
# The failure lists are CANDIDATES, not confirmed errors: a form is listed when
# restoring the missing letter yields a word attested in the independent
# reference corpus and the stored form is not. That is evidence, not proof - read
# the context. The `&` list is the exception and is exhaustive: an ampersand is
# never Hebrew.
#
# Usage:
#   python3 tools/list_ligature_words.py                 # -> ligature_words.json
#   python3 tools/list_ligature_words.py --part part1.json
import argparse
import collections
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pipeline"))

import corpus_io as cio  # noqa: E402
from repair_filters import docai_filter as df  # noqa: E402

OUT_PATH = cio.repo_path("ligature_words.json")

# Candidates already resolved by reading the context, kept keyed by exact
# position so a DIFFERENT word in the same klal is never silently suppressed -
# the same convention check_klal_token_orphans.py uses for its own allowlist.
# Listing them here stops each new run re-proposing a settled question.
KNOWN_FALSE_POSITIVES = {
    # Psalms 16:9, `לכן שמח לבי ויגל` - `ויגל` (and rejoiced) is correct;
    # `ויגאל` (and redeemed) would be a different verse. Checked 2026-08-26.
    (7, 677): "ויגל is correct - Psalms 16:9, not ויגאל",
    # `אוף` is ordinary Aramaic for 'also' and has its own Jastrow entries
    # (אוֹף I, אוֹף II); the corpus uses it twice. `אלוף` (chief) is a different
    # word entirely. Confirmed against the dictionary 2026-08-26.
    (150, 443): "אוף is real Aramaic ('also'), not a collapsed אלוף",
}
LIGATURE_CODEPOINT = "ﭏ"


def scan(part_paths):
    ref = df.reference_frequencies()
    intact = collections.Counter()
    intact_where = collections.defaultdict(list)
    dropped_lamed, dropped_alef, both_lost = [], [], []
    literal = []

    for path in part_paths:
        for k in cio.load_klalim(path) or []:
            kid = k["klal_id"]
            for i, raw in enumerate(cio.words_of(k)):
                n = cio.hebrew_letters_only(raw)
                if LIGATURE_CODEPOINT in raw:
                    literal.append({"klal_id": kid, "word_index": i, "word": raw})
                if "אל" in n:
                    intact[n] += 1
                    if len(intact_where[n]) < 12:
                        intact_where[n].append([kid, i])
                    continue
                if any(c.isascii() and c.isalpha() for c in raw) or "&" in raw:
                    both_lost.append({"klal_id": kid, "word_index": i, "word": raw})
                    continue
                if not n or ref.get(n, 0):
                    continue          # attested as it stands: not a failed ligature
                repaired = df.repair_word(raw, ref)
                if not repaired:
                    continue
                rn = cio.hebrew_letters_only(repaired)
                j = next((x for x in range(min(len(n), len(rn))) if n[x] != rn[x]), len(n))
                row = {"klal_id": kid, "word_index": i, "word": raw,
                       "repaired": repaired, "repaired_ref_count": ref.get(rn, 0)}
                fp = KNOWN_FALSE_POSITIVES.get((kid, i))
                if fp:
                    row["resolved_false_positive"] = fp
                (dropped_lamed if rn[j] == "ל" else dropped_alef).append(row)
    return {
        "intact": [{"word": w, "count": c, "occurrences": intact_where[w]}
                   for w, c in intact.most_common()],
        "dropped_lamed": dropped_lamed,
        "dropped_alef": dropped_alef,
        "both_lost": both_lost,
        "literal_ligature_codepoint": literal,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--part", action="append",
                    help="a part*.json to scan (repeatable; default: all three)")
    args = ap.parse_args()
    paths = ([cio.repo_path(p) for p in args.part] if args.part
             else [cio.repo_path(f"part{n}.json") for n in (1, 2, 3)])
    out = scan(paths)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.flush()
    total = sum(r["count"] for r in out["intact"])
    print(f"Wrote {OUT_PATH}")
    print(f"  words set with the ligature (contain `אל`): {len(out['intact'])} distinct, "
          f"{total} occurrences")
    print(f"  candidate FAILURES of that sort:")
    print(f"      dropped lamed  {len(out['dropped_lamed']):>4}   (אליבא -> איבא)")
    print(f"      dropped alef   {len(out['dropped_alef']):>4}   (שמואל -> שמול)")
    print(f"      both lost      {len(out['both_lost']):>4}   (אל -> &)")
    fps = sum(1 for key in ("dropped_lamed", "dropped_alef")
              for r in out[key] if r.get("resolved_false_positive"))
    print(f"  literal U+FB4F in the corpus: {len(out['literal_ligature_codepoint'])}")
    print(f"  of the candidates, {fps} are already-resolved false positives, marked as such")
    print("  The failure lists are CANDIDATES - read the context. `both_lost` is exhaustive.")


if __name__ == "__main__":
    main()
