#!/usr/bin/env python3
# [STANDALONE] Survey the corpus->consensus transformations behind every
# multi-witness agreement, and separate INK defects from ENGINE confusions.
#
# Built 2026-08-23 to answer MULTI-WITNESS-REPAIR-AND-SYNTHESIS-PLAN.md's §8
# item 2. The plan's §2.B independence proof was refuted by 37 measured cases of
# two or three engines agreeing on the same wrong reading, all of them the
# alef-lamed ligature dropping its lamed. That raised the obvious worry: all 37
# came from the ONE printer's sort that happens to be catalogued, which says
# more about what has been looked for than about what exists. This script is the
# systematic look.
#
# THE DISCRIMINATOR. Two different things produce multi-engine agreement, and
# they need different remedies:
#
#   * An INK defect (a damaged, wrong or ligatured type sort) is upstream of
#     every engine. All engines see the same wrong glyph, so agreement is
#     expected, carries no independent corroboration, and the STORED TEXT is
#     usually right. Signature: strongly CONTEXT-LOCKED (the same preceding
#     letter almost every time, because the defect lives in one specific sort or
#     letter pair) and a raised rate of UNANIMOUS 3-of-3 agreement.
#
#   * An ENGINE confusion (two letters that are genuinely similar in this
#     typeface) is a per-model visual judgement. Engines fail independently and
#     inconsistently. Signature: scattered context, near-zero unanimity, and
#     often a matching reverse transformation of similar size.
#
# The two are not distinguishable by frequency, which is why counting
# disagreements alone cannot answer the question.
#
# WHAT THIS CANNOT SEE, and it is the most dangerous class: a sort defect that
# corrupted the CORPUS itself. part1.json is partly derived from DocAI, so if a
# defect made every engine read the same wrong thing AND that reading was
# accepted into the corpus, there is no disagreement left to detect and this
# survey is blind to it by construction (Lesson 15 - silence where a check
# cannot operate is not evidence). tools/detect_ligature_corruption.py attacks
# that direction, using corpus word frequencies rather than engine agreement.
import argparse
import collections
import difflib
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pipeline"))

import corpus_io as cio  # noqa: E402
import synthesize_multi_witness as syn  # noqa: E402
import typography  # noqa: E402

# A transformation is reported as a candidate ink defect only if it clears both
# bars. Thresholds are triage aids, not verdicts (Lesson 2) - anything they
# surface still needs a render, and anything they miss is not thereby clean.
MIN_INSTANCES = 4
CONTEXT_LOCK_FRACTION = 0.90


def single_edit(stored, reading):
    """(kind, from, to, index) for a one-edit difference, else None.

    Only single-edit transformations are classified. A word differing by two or
    more edits tells us little about any single sort, and lumping it in would
    dilute the context signal the discriminator depends on."""
    sm = difflib.SequenceMatcher(None, stored, reading, autojunk=False)
    ops = [(t, i1, i2, j1, j2) for t, i1, i2, j1, j2 in sm.get_opcodes() if t != "equal"]
    if len(ops) != 1:
        return None
    t, i1, i2, j1, j2 = ops[0]
    if t == "delete" and i2 - i1 == 1:
        return ("del", stored[i1], "", i1)
    if t == "insert" and j2 - j1 == 1:
        return ("ins", "", reading[j1], i1)
    if t == "replace" and i2 - i1 == 1 and j2 - j1 == 1:
        return ("sub", stored[i1], reading[j1], i1)
    return None


def survey(agreements):
    rows = collections.defaultdict(
        lambda: {"n": 0, "unanimous": 0, "context": collections.Counter(), "examples": []})
    for a in agreements:
        edit = single_edit(a["final_text"], a["consensus_reading"])
        if edit is None:
            continue
        kind, frm, to, idx = edit
        r = rows[(kind, frm, to)]
        r["n"] += 1
        if len(a["agreeing_engines"]) == 3:
            r["unanimous"] += 1
        r["context"][a["final_text"][idx - 1] if idx > 0 else "^"] += 1
        if len(r["examples"]) < 4:
            r["examples"].append((a["klal_id"], a["word_index"],
                                  a["final_text"], a["consensus_reading"]))
    return rows


def classify(key, r):
    """'ink' | 'engine' | 'unclear' - see the module header's discriminator."""
    if r["n"] < MIN_INSTANCES:
        return "unclear"
    top_frac = r["context"].most_common(1)[0][1] / r["n"]
    if top_frac >= CONTEXT_LOCK_FRACTION:
        return "ink"
    return "engine"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--min-instances", type=int, default=MIN_INSTANCES)
    ap.add_argument("--show-unanimous", action="store_true",
                    help="list every 3-of-3 agreement, the likeliest place an "
                         "un-catalogued ink defect shows up")
    args = ap.parse_args()

    part1 = cio.load_part1()
    verified = cio.load_json(syn.VERIFIED_PATH, default=[]) or []
    agreements, _ = syn.synthesize(
        part1, verified,
        syn.load_baseline(syn.VLM_A_PATH), syn.load_baseline(syn.VLM_B_PATH),
        syn.load_baseline(syn.SURYA_PATH),
        decided=None)  # deliberately NOT skipping human-decided positions:
                       # a defect a reviewer already corrected is still a defect,
                       # and those are the clearest instances of one.

    rows = survey(agreements)
    total_single = sum(r["n"] for r in rows.values())
    print(f"{len(agreements)} multi-witness agreements against the corpus; "
          f"{total_single} are a single-edit transformation\n")

    header = f"{'transform':<14} {'n':>4} {'3of3':>5} {'ctx-lock':>9}  verdict    dominant context"
    print(header); print("-" * len(header))
    for key, r in sorted(rows.items(), key=lambda kv: -kv[1]["n"]):
        if r["n"] < args.min_instances:
            continue
        kind, frm, to = key
        lab = f"{kind} {frm or 'Ø'}->{to or 'Ø'}"
        top_char, top_n = r["context"].most_common(1)[0]
        frac = top_n / r["n"]
        print(f"  {lab:<12} {r['n']:>4} {r['unanimous']:>5} {frac:>8.0%}  "
              f"{classify(key, r):<9}  {top_char!r} x{top_n}")

    ink = [k for k, r in rows.items() if classify(k, r) == "ink"]
    print(f"\nCandidate INK defects (context-locked): {len(ink)}")
    for key in ink:
        kind, frm, to = key
        r = rows[key]
        known = "CATALOGUED" if (kind == "del" and frm == "ל") else "NOT in pipeline/typography.py"
        print(f"  {kind} {frm or 'Ø'}->{to or 'Ø'}  n={r['n']}  {known}")
        for kid, wi, a, b in r["examples"][:3]:
            print(f"      klal {kid} w{wi}: {a!r} -> {b!r}")

    unanimous = [a for a in agreements if len(a["agreeing_engines"]) == 3]
    unexplained = [a for a in unanimous
                   if not typography.ligature_artifact(a["final_text"], a["consensus_reading"])]
    print(f"\nUnanimous 3-of-3 agreements: {len(unanimous)}; "
          f"explained by a catalogued sort: {len(unanimous) - len(unexplained)}; "
          f"UNEXPLAINED: {len(unexplained)}")
    if args.show_unanimous or unexplained:
        for a in unexplained:
            print(f"   klal {a['klal_id']:>3} w{a['word_index']:<5} "
                  f"{a['final_text']!r} -> {a['consensus_reading']!r}")
        print("   ^ every one of these needs a render before any conclusion "
              "(Lesson 14). Three engines agreeing is what an ink defect looks "
              "like, and also what a genuine corpus error looks like.")


if __name__ == "__main__":
    main()
