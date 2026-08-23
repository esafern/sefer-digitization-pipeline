#!/usr/bin/env python3
# [STANDALONE] Estimate P(the consensus reading is correct | two distinct
# engines agree against the stored text) for this corpus.
#
# Built 2026-08-23 for MULTI-WITNESS-REPAIR-AND-SYNTHESIS-PLAN.md §8 item 1.
# That document's §2.B originally claimed the posterior exceeds 99.9999%; the
# revision retracted the derivation as false for this corpus but left the real
# number unquantified, which blocks any auto-approval decision. This measures it.
#
# WHY THE OBVIOUS SAMPLE IS UNUSABLE. Human review decisions look like ground
# truth, and there are 40 consensus positions carrying one. But that sample is
# adversarially selected: a reviewer looked at those words and confirmed the
# corpus, so a consensus proposing a change there loses almost by construction
# (measured: 39 of 40). That is a real operational finding - consensus must not
# reopen human-confirmed positions, which is why synthesize_multi_witness.py
# skips them - but it says nothing about the UNDECIDED positions auto-approval
# would actually act on.
#
# WHAT THIS USES INSTEAD. Stage 3's crop-level vision adjudication, on undecided
# consensus positions that also carry one. Vision is not ground truth; it is a
# fourth opinion, and a fallible one. It is used here because it is the only
# independent per-word judgement available at scale, and because this pipeline
# already trusts it to classify every candidate it serves - if it is not good
# enough to arbitrate here, it is not good enough to be doing that either.
#
# THE CIRCULARITY SPLIT MATTERS AND IS REPORTED SEPARATELY. The adjudicator is
# Gemini, and so is witness 2 (PROPOSED_PIPELINE_ARCHITECTURE.md Directive #1,
# still violated). Where the VLM is one of the agreeing engines, the arbiter
# shares a model family with a witness it is arbitrating - so the "VLM-free"
# subset (docai+surya agreements) is the only estimate that is not partly
# marking its own homework. The gap between the two is itself a measurement of
# how much circularity inflates apparent agreement.
import argparse
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pipeline"))

import corpus_io as cio  # noqa: E402
import review_decisions as rd  # noqa: E402
import synthesize_multi_witness as syn  # noqa: E402
import typography  # noqa: E402


def load():
    part1 = cio.load_part1()
    verified = cio.load_json(syn.VERIFIED_PATH, default=[]) or []
    agreements, _ = syn.synthesize(
        part1, verified,
        syn.load_baseline(syn.VLM_A_PATH), syn.load_baseline(syn.VLM_B_PATH),
        syn.load_baseline(syn.SURYA_PATH), decided=None)
    decided = {(k, w) for t in ("disputed_choice", "manual_correction")
               for (k, w) in rd.all_current(t) if w is not None}
    vision = {(c["klal_id"], c["word_index_in_final_text"]): c for c in verified}
    return agreements, decided, vision


def tally(items, vision, min_conf=0.0, drop_artifacts=False):
    """(backed, contradicted) - how often the vision arbiter sides with the
    consensus reading rather than the stored text."""
    norm = cio.hebrew_letters_only
    backed = contradicted = 0
    for a in items:
        c = vision.get((a["klal_id"], a["word_index"]))
        if not c or c.get("vision_selected") not in ("A", "B"):
            continue
        if (c.get("vision_confidence") or 0) < min_conf:
            continue
        if drop_artifacts and typography.ligature_artifact(
                a["final_text"], a["consensus_reading"]):
            continue
        if c["vision_selected"] == "A" and norm(c.get("original_word") or "") == norm(a["consensus_reading"]):
            backed += 1
        elif c["vision_selected"] == "B":
            contradicted += 1
    return backed, contradicted


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--min-confidence", type=float, default=0.9)
    args = ap.parse_args()

    agreements, decided, vision = load()
    undecided = [a for a in agreements if (a["klal_id"], a["word_index"]) not in decided]
    vlm_free = [a for a in undecided if "vlm" not in a["agreeing_engines"]]
    unanimous = [a for a in undecided if len(a["agreeing_engines"]) == 3]

    # The adversarially-selected sample, reported so nobody re-derives it as if
    # it were the answer.
    norm = cio.hebrew_letters_only
    kept = reopened = 0
    for a in agreements:
        key = (a["klal_id"], a["word_index"])
        if key not in decided:
            continue
        rec = (rd.current_for(key[0], key[1], "disputed_choice")
               or rd.current_for(key[0], key[1], "manual_correction"))
        chosen = norm((rec or {}).get("chosen_text") or "")
        if chosen == norm(a["consensus_reading"]):
            reopened += 1
        elif chosen == norm(a["final_text"]):
            kept += 1

    print(f"{len(agreements)} consensus agreements; {len(undecided)} undecided\n")
    print("A. Human-decided positions (ADVERSARIALLY SELECTED - not the posterior):")
    print(f"   human kept the stored text: {kept}   human adopted the consensus: {reopened}")
    print("   ^ a reviewer already confirmed these words, so consensus loses by")
    print("     construction. Useful only as: do not reopen decided positions.\n")

    print("B. Undecided positions, arbitrated by crop-level vision:")
    hdr = f"   {'subset':<40} {'n':>4} {'backed':>7} {'posterior':>10}"
    print(hdr); print("   " + "-" * (len(hdr) - 3))
    rows = [
        ("all undecided consensus", undecided, 0.0, False),
        (f"  + vision confidence >= {args.min_confidence}", undecided, args.min_confidence, False),
        ("  + catalogued artifacts dropped", undecided, args.min_confidence, True),
        ("VLM-free (arbiter independent)", vlm_free, 0.0, False),
        ("  + conf gate + artifacts dropped", vlm_free, args.min_confidence, True),
        ("unanimous 3-of-3", unanimous, 0.0, False),
    ]
    for name, items, mc, da in rows:
        ok, bad = tally(items, vision, mc, da)
        n = ok + bad
        print(f"   {name:<40} {n:>4} {ok:>7} {(f'{ok/n:.0%}' if n else '-'):>10}")

    ok, bad = tally(vlm_free, vision, args.min_confidence, True)
    n = ok + bad
    print("\nHEADLINE: the least-circular estimate is the VLM-free row.")
    if n:
        print(f"   P(consensus correct | 2 distinct engines agree) ~= {ok/n:.0%}  (n={n})")
    print("   MULTI-WITNESS-REPAIR-AND-SYNTHESIS-PLAN.md §2.B originally claimed >99.9999%.")

    print("""
LIMITS - these bound what the number means:
  1. Vision is a fourth OPINION, not ground truth. A better arbiter (a scholar,
     or a genuinely independent engine) could move this substantially.
  2. Only consensus positions that ALSO carry a vision verdict are measurable,
     and a candidate exists only where DocAI disagreed with the corpus - so this
     covers the DocAI-involved subset. Those are arguably the STRONGEST
     consensus cases (DocAI is the most accurate engine here), which makes the
     result more damning for the surya+vlm-only majority, not less.
  3. Small n, especially for the VLM-free subset. Treat as an order of
     magnitude, not a calibrated probability.
  4. Re-run this as review decisions accumulate; the estimate improves with
     every genuinely undecided position a human resolves.""")


if __name__ == "__main__":
    main()
