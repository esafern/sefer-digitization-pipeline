#!/usr/bin/env python3
# [STANDALONE] Measure what every live suppression filter HIDES from the
# reviewer, and what independent evidence says about it.
#
# Built 2026-08-24. MULTI-WITNESS-REPAIR-AND-SYNTHESIS-PLAN.md §3.5 required
# this before any filter is trusted; it was then deprioritised on the reasoning
# that "it only matters once a filter rewrites text, and none does". That
# reasoning was wrong, and this file exists because it was wrong.
#
# The filters are the reason the reviewer's queue is usable at all - they exist
# to keep engine-specific artifacts from becoming disputes. That is also exactly
# why they need validating: a filter standing between the corpus and a human is
# deciding what that human is allowed to see. Measured on the day this was
# written, the live filters suppress ~12,400 items against ~216 disputes that
# actually reach a reviewer. They decide roughly 98% of the review surface.
#
# A wrong REWRITE produces visible wrong text. A wrong SUPPRESSION produces
# silence, and silence where a check cannot operate is not evidence of
# correctness (Lesson 15, Lesson 26). Suppression is the harder failure to
# catch, not the softer one.
#
# WHAT THIS DOES AND DOES NOT DO. It reports each filter's suppression volume,
# its measurable false negatives (things hidden that an INDEPENDENT signal says
# were real), and the composition of what it hides. It does NOT declare a filter
# correct: several suppressions are genuinely right, and the numbers here are a
# trade-off to be read, not a score to be passed. Where no independent signal
# exists, that is reported as unmeasured rather than as clean.
import argparse
import collections
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pipeline"))

import corpus_io as cio  # noqa: E402
import review_server as rs  # noqa: E402
import synthesize_multi_witness as syn  # noqa: E402
import typography  # noqa: E402
from repair_filters import docai_filter  # noqa: E402

norm = cio.hebrew_letters_only


def load():
    part1 = cio.load_part1()
    verified = cio.load_json(syn.VERIFIED_PATH, default=[]) or []
    return (part1, verified,
            syn.load_baseline(syn.VLM_A_PATH), syn.load_baseline(syn.VLM_B_PATH),
            syn.load_baseline(syn.SURYA_PATH))


def vlm_gate_false_negatives(part1, verified, va, vb, sy):
    """Positions the Pass-A/Pass-B stability gate silenced, where ANOTHER engine
    independently produced the same reading the VLM was gated out of casting.

    This is the gate's genuine blind spot. The gate's premise - a witness that
    disagrees with itself across two runs is unreliable here - is sound in
    isolation. But it is applied to the VLM BEFORE consensus, so it also discards
    the cases where a DIFFERENT engine independently converged on the same
    reading. Cross-engine convergence is evidence that does not depend on the
    VLM's run-to-run stability at all."""
    docai = syn.docai_verdicts(verified)
    hidden = []
    for k in part1:
        kid, words = k["klal_id"], k["clean_text"].split()
        if not (va.get(kid) and vb.get(kid)):
            continue
        ungated = cio.align_witness(words, va[kid])
        gated = syn.vlm_verdicts(words, va[kid], vb[kid])
        surya = cio.align_witness(words, sy[kid]) if sy.get(kid) else {}
        for wi, (reading, verdict) in ungated.items():
            if wi in gated or verdict != "differs":
                continue
            partners = []
            s = surya.get(wi)
            if s and s[1] == "differs" and norm(s[0]) == norm(reading):
                partners.append("surya")
            d = docai.get((kid, wi))
            if d is not None and norm(d) == norm(reading):
                partners.append("docai")
            if partners:
                hidden.append({"klal_id": kid, "word_index": wi, "stored": words[wi],
                               "reading": reading, "engines": sorted(partners + ["vlm"])})
    return hidden


def load_reference_freq():
    """Word frequencies from sefaria_reference_corpus - 6.18M words of Talmud,
    Rashi, Rambam, Tur and Shulchan Arukh with NO editorial or data lineage
    connection to this project. Returns {} if the cache is absent (it is
    gitignored).

    FIXED 2026-08-31. This was the SECOND of the two private copies the
    2026-08-26 review's finding #2 named - and it names this file and this line
    outright ("validate_suppression_filters.py:87 is a second copy"). The
    other copy, in reconstruct_placeholder_klalim.py, was consolidated on
    2026-08-26; this one was not, and both the 2026-08-27 review and the
    2026-08-31 sweep then recorded #2 as "Fixed" on the strength of the first
    file alone. Lesson 34: the sibling was written down in the finding itself.

    Behaviourally identical today, measured not assumed - this module's `norm`
    IS `cio.hebrew_letters_only`, the same normalisation the canonical loader
    applies, so the two returned the same dict. What the copy lacked was the
    canonical path constant and the lru_cache; what it risked was the exact
    failure the original finding describes, the day word_freq.json is rebuilt
    keeping geresh/gershayim.
    """
    return docai_filter.reference_frequencies()


def artifact_tag_check(agreements, ref):
    """Check each ligature tag against an INDEPENDENT LINGUISTIC signal.

    WHY NOT VISION, and why not lexicon.txt - both were tried first and both are
    circular for this specific question:

      * Vision (the crop adjudicator) is a fourth reader of the SAME PIXELS. An
        ink defect is upstream of every reader, so asking a pixel-based arbiter
        whether a pixel-level defect is real is Lesson 24 applied to one's own
        validation method. It "disagreed" with 14 of 37 tags - not because the
        tags were wrong, but because it too read the corrupted glyph.
      * lexicon.txt was built from THIS corpus's own OCR output and, in this
        project's own words, "absorbed and then validated the alef-lamed
        ligature corruption" - see tools/validate_lexicon_independent.py's
        header. It is not independent for exactly this defect class.

    The reference corpus has neither problem: it never saw this scan.
    A tag is CORROBORATED when the stored form is well attested there and the
    consensus form is not."""
    out = {"corroborated": [], "contradicted": [], "unattested": []}
    for a in agreements:
        if not typography.ligature_artifact(a["final_text"], a["consensus_reading"]):
            continue
        stored_n, cons_n = norm(a["final_text"]), norm(a["consensus_reading"])
        fs, fc = ref.get(stored_n, 0), ref.get(cons_n, 0)
        if fs == 0 and fc == 0:
            out["unattested"].append((a, fs, fc))   # e.g. a proper name
        elif fs > fc:
            out["corroborated"].append((a, fs, fc))
        else:
            out["contradicted"].append((a, fs, fc))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--list", action="store_true", help="list each hidden item")
    args = ap.parse_args()

    part1, verified, va, vb, sy = load()
    agreements, stats = syn.synthesize(part1, verified, va, vb, sy, decided=None)

    print(f"Disputes reaching a reviewer: {len(agreements)}\n")
    print("=" * 74)
    print("FILTER 1 — VLM Pass-A/Pass-B stability gate")
    print("=" * 74)
    fn = vlm_gate_false_negatives(part1, verified, va, vb, sy)
    by_eng = collections.Counter("+".join(h["engines"]) for h in fn)
    print(f"  suppressed (total abstentions):        {stats['vlm_abstained']}")
    print(f"  FALSE NEGATIVES - another engine independently agreed: {len(fn)}")
    for k, v in by_eng.most_common():
        print(f"      {k}: {v}")
    art = sum(1 for h in fn if typography.ligature_artifact(h["stored"], h["reading"]))
    print(f"  of those, explained by a catalogued ink artifact: {art} "
          f"({'would be tagged, not trusted' if art else '-'})")
    print("  READ THIS AS A TRADE-OFF, NOT A VERDICT: much of what the gate hides is")
    print("  the engine noise it exists to suppress (Surya's geresh->yod, kaf/bet).")
    print("  The measured cost of the gate is that it also hides the cases above,")
    print("  where cross-engine convergence did not depend on VLM stability at all.")
    if args.list:
        for h in fn:
            print(f"      klal {h['klal_id']:>3} w{h['word_index']:<5} "
                  f"{h['stored']!r} -> {h['reading']!r} ({'+'.join(h['engines'])})")

    print()
    print("=" * 74)
    print("FILTER 2 — ligature-artifact tagging")
    print("=" * 74)
    tagged = [a for a in agreements
              if typography.ligature_artifact(a["final_text"], a["consensus_reading"])]
    ref = load_reference_freq()
    print(f"  tagged as a shared ink defect:         {len(tagged)}")
    if not ref:
        print("  UNMEASURED: sefaria_reference_corpus/word_freq.json absent "
              "(gitignored cache - see SETUP.md).")
    else:
        res = artifact_tag_check(agreements, ref)
        n = sum(len(v) for v in res.values())
        print(f"  arbiter: {len(ref):,} distinct words from a corpus that never saw this scan")
        print(f"  CORROBORATED (stored form better attested): {len(res['corroborated'])}/{n}")
        print(f"  CONTRADICTED (consensus form better attested): {len(res['contradicted'])}/{n}")
        print(f"  unattested either way (proper names etc.):   {len(res['unattested'])}/{n}")
        for a, fs, fc in res["contradicted"]:
            print(f"      ! klal {a['klal_id']} w{a['word_index']}: {a['final_text']!r} "
                  f"({fs:,}) -> {a['consensus_reading']!r} ({fc:,})")
    print("  NOTE: tagging does not hide the item, it labels it - a reviewer still")
    print("  sees the word. A wrong tag biases the reviewer rather than silencing.")

    print()
    print("=" * 74)
    print("FILTER 3 — witness-queue vision filter")
    print("=" * 74)
    import json
    full = json.load(open(os.path.join(REPO, "reconstruction_witness_queue.json")))["queue"]
    served = rs._load_witness_queue()
    print(f"  suppressed: {len(full) - len(served)} of {len(full)}")
    print("  EVIDENCE: Tesseract measured right in 16 of 419 disagreements (3.8%)")
    print("  vs DocAI's 91.2%. PARTIAL - all 419 vision verdicts scored >= 0.9, so")
    print("  the confidence signal cannot separate the hidden from the served.")

    print()
    print("=" * 74)
    print("FILTER 4 — align_witness ragged-block drop")
    print("=" * 74)
    dropped = total = 0
    for k in part1:
        kid, words = k["klal_id"], k["clean_text"].split()
        for base in (va, sy):
            if not base.get(kid):
                continue
            total += len(words)
            dropped += len(words) - len(cio.align_witness(words, base[kid]))
    print(f"  suppressed: {dropped} witness word-slots ({dropped/total:.0%} of all)")
    print("  UNMEASURED. By construction this drops positions where no unambiguous")
    print("  1:1 correspondence exists, so there is no reading to check it against -")
    print("  the same property that makes it safe makes it unfalsifiable here.")
    print("  Closing it needs a hand-checked sample, not another derived signal.")

    print("\n" + "=" * 74)
    print("SUMMARY: filters 1 and 2 now have a measured rate against an independent")
    print("signal. Filters 3 and 4 remain justified by argument, not measurement.")


if __name__ == "__main__":
    main()
