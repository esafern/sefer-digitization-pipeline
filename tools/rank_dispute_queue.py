#!/usr/bin/env python3
"""
tools/rank_dispute_queue.py

[STANDALONE] Order the open dispute queue by P(the consensus reading is the one
a reviewer will adopt), estimated per dispute rather than for the queue as a
whole.

WHY PER-DISPUTE. tools/estimate_consensus_posterior.py answers "what is
P(consensus correct | two distinct engines agree)" for the corpus - one number,
~31%, and it is the right number for the question it asks (should consensus
EVER auto-approve: no). It cannot order a queue. A reviewer working through 453
open disputes needs to know which of them are worth opening first, and the
answer is not uniform: measured below, it ranges from 11% to 100% depending on
WHICH engines agree.

THE CALIBRATION SAMPLE, and where it comes from. `consensus_disputes_part1.json`
holds only UNDECIDED positions - synthesize_multi_witness.py drops a dispute the
moment a human rules on it - so the live file contains, by construction, zero
examples of what reviewers actually do. The sample has to come from the ledger:
168 `disputed_choice` rulings whose snapshot recorded `consensus_reading`, where
"adopted" means the reviewer's chosen text equals what the consensus proposed.

WHAT THE MEASUREMENT SAYS, and it is not what the engine COUNT suggests:

    docai,surya .......  11%   (n=9)     surya,vlm .........  79%  (n=100)
    docai,vlm .........  14%   (n=7)     dicta,surya .......  87%  (n=15)
    docai,surya,vlm ...  25%   (n=8)     dicta,surya,vlm ... 100%  (n=16)

Every set containing DocAI is low; every set without it is high. That is mostly
SELECTION, not accuracy, and reading it as "DocAI is wrong" would be the error:
candidates are GENERATED from DocAI's disagreements with the corpus, and those
disagreements are exactly the positions that have already been through vision
adjudication and human review, so the corpus has usually already been fixed or
already confirmed there. A DocAI-involved consensus is disproportionately
re-litigating a settled word. The ranking uses the number; the reason it is low
matters for how you read it.

HOW A RATE BECOMES A SCORE. Raw rates lie at small n - one stratum here is 1 for
1, and "100%" is not what a single observation means. Each stratum gets a
Beta(1,1) posterior over the adoption rate, so the score is (adopted + 1) /
(n + 2) and a 1-of-1 stratum scores 67%, not 100%. The 90% credible interval is
reported beside it, and a stratum thin enough that its interval spans most of
[0,1] is marked as such rather than being quietly trusted.

THE LIMIT THAT MATTERS MOST (Lesson 27). This sample is positions a human RULED
ON, so it measures what reviewers decided about the disputes they chose to work
through - not what is true about the ones they have not opened. That is a
weaker selection effect than estimate_consensus_posterior's 39-of-40 case (there
the reviewer had confirmed the word BEFORE consensus proposed anything, so
consensus lost by construction), but it is not zero: if the easy disputes were
worked first, the untouched queue is harder than this sample. Treat the ordering
as a triage heuristic, which is all a posterior can ever be here - the ink still
decides every one of them.
"""
import argparse
import collections
import functools
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
INSTALL_DIR = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(INSTALL_DIR, "pipeline"))

import corpus_io as cio  # noqa: E402
import review_decisions as rd  # noqa: E402

DEFAULT_BASE = "http://127.0.0.1:8420"
# A stratum needs this many observations before its rate is used on its own.
# Below it the score falls back to the next-coarser stratum, which is always
# better evidenced - never to a raw rate over three examples.
MIN_STRATUM_N = 8


def _beta_mean(adopted, n):
    """Posterior mean under Beta(1,1) - Laplace's rule.

    Not the raw rate: 1-of-1 is 67% here, not 100%, which is what one
    observation actually licenses."""
    return (adopted + 1.0) / (n + 2.0)


@functools.lru_cache(maxsize=None)
def _beta_interval(adopted, n, mass=0.90):
    """A 90% equal-tailed credible interval for the same posterior.

    MEMOIZED, and not as a micro-optimisation. There are eight distinct strata
    and 453 disputes, so the uncached version integrated the same eight
    posteriors 453 times: 15.3 seconds for a report whose whole argument for
    being in rebuild_all.sh is that it is cheap. 0.3s cached.

    Computed by bisection on the regularized incomplete beta function, so this
    needs no scipy - the repo's dependency set does not carry it and a ranking
    tool is not a reason to add one.
    """
    a, b = adopted + 1.0, n - adopted + 1.0
    lo_p, hi_p = (1 - mass) / 2, 1 - (1 - mass) / 2

    def cdf(x):
        # Regularized incomplete beta via its continued-fraction-free series;
        # n here is at most a few hundred, so a direct sum is exact enough.
        import math
        if x <= 0:
            return 0.0
        if x >= 1:
            return 1.0
        total, term = 0.0, 0.0
        ln_beta = (math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b))
        steps = 2000
        prev = 0.0
        for i in range(1, steps + 1):
            t = i / steps
            dens = math.exp((a - 1) * math.log(t) + (b - 1) * math.log(1 - t) - ln_beta) \
                if 0 < t < 1 else 0.0
            total += (prev + dens) / 2 * (1 / steps)
            prev = dens
            if t >= x:
                break
        term = total
        return min(1.0, max(0.0, term))

    def invert(target):
        lo, hi = 0.0, 1.0
        for _ in range(40):
            mid = (lo + hi) / 2
            if cdf(mid) < target:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2

    return invert(lo_p), invert(hi_p)


def engine_key(record):
    engines = record.get("agreeing_engines") or record.get("consensus_engines") or []
    return ",".join(sorted(engines))


def calibration_sample():
    """[(features, adopted)] from every ledger ruling that recorded a consensus."""
    out = []
    for r in rd.all_records():
        if r["decision_type"] != "disputed_choice":
            continue
        snap = r.get("candidate_snapshot") or {}
        proposed = (snap.get("consensus_reading") or "").strip()
        if not proposed:
            continue
        adopted = (r.get("chosen_text") or "").strip() == proposed
        out.append((snap, adopted))
    return out


def build_model(sample):
    """{level: {key: (adopted, n)}} for the two strata, coarse to fine."""
    by_engines = collections.defaultdict(lambda: [0, 0])
    by_count = collections.defaultdict(lambda: [0, 0])
    overall = [0, 0]
    for snap, adopted in sample:
        key = engine_key(snap)
        n_engines = len(snap.get("consensus_engines") or [])
        for bucket, k in ((by_engines, key), (by_count, n_engines)):
            bucket[k][0] += 1 if adopted else 0
            bucket[k][1] += 1
        overall[0] += 1 if adopted else 0
        overall[1] += 1
    return {"engines": dict(by_engines), "count": dict(by_count), "overall": overall}


def score(model, record):
    """(posterior, low, high, basis) for one dispute."""
    key = engine_key(record)
    stats = model["engines"].get(key)
    basis = f"engine set `{key}`"
    if not stats or stats[1] < MIN_STRATUM_N:
        n_engines = len(record.get("agreeing_engines") or [])
        coarser = model["count"].get(n_engines)
        if coarser and coarser[1] >= MIN_STRATUM_N:
            stats, basis = coarser, (
                f"{n_engines} engines (engine set `{key}` has too few examples)")
        else:
            stats, basis = model["overall"], "the whole calibration sample"
    adopted, n = stats
    lo, hi = _beta_interval(adopted, n)
    return _beta_mean(adopted, n), lo, hi, f"{basis}: {adopted}/{n} adopted"


def open_disputes():
    raw = cio.load_repo_json("consensus_disputes_part1.json", {}) or {}
    out = []
    for kid, items in raw.items():
        for d in items:
            out.append(dict(d, klal_id=int(kid)))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=None, help="markdown worklist path")
    ap.add_argument("--json-out", default=None, help="machine-readable ranking path")
    ap.add_argument("--top", type=int, default=40, help="rows to list in the markdown")
    ap.add_argument("--base-url", default=DEFAULT_BASE)
    args = ap.parse_args()
    out_path = args.out or cio.repo_path("DISPUTE-QUEUE-BY-POSTERIOR.md")
    json_path = args.json_out or cio.repo_path("dispute_queue_ranked.json")
    base = args.base_url.rstrip("/")

    sample = calibration_sample()
    model = build_model(sample)
    disputes = open_disputes()

    ranked = []
    for d in disputes:
        posterior, lo, hi, basis = score(model, d)
        ranked.append(dict(d, posterior=round(posterior, 4),
                           ci_low=round(lo, 4), ci_high=round(hi, 4), basis=basis))
    ranked.sort(key=lambda r: (-r["posterior"], r["klal_id"], r["word_index"]))

    # ONE LINE PER DISPUTE - same reasoning as word_identity.json's writer: this
    # is regenerated by rebuild_all.sh on every run and tracked, so a pretty
    # printed 15,820-line file would put an unreadable diff in front of whoever
    # reviews the rebuild. Per-row lines keep a re-rank legible.
    with open(json_path, "w", encoding="utf-8") as f:
        f.write("[\n")
        for i, row in enumerate(ranked):
            f.write("  " + json.dumps(row, ensure_ascii=False, separators=(",", ":")))
            f.write(",\n" if i < len(ranked) - 1 else "\n")
        f.write("]\n")
        f.flush()

    bands = collections.Counter()
    for r in ranked:
        p = r["posterior"]
        bands[">=0.75" if p >= .75 else ">=0.50" if p >= .50
              else ">=0.25" if p >= .25 else "<0.25"] += 1

    L = ["# The open dispute queue, ordered by posterior", "",
         f"{len(ranked)} open dispute(s), scored by "
         f"`tools/rank_dispute_queue.py`. **Regenerate after any apply** - the "
         f"queue and the calibration both move.", "",
         "`posterior` is P(a reviewer adopts the consensus reading), estimated "
         "from the stratum this dispute falls in, under a Beta(1,1) posterior so "
         "a thin stratum cannot read as a certainty. The interval is 90% "
         "credible. **This orders attention; it decides nothing** - every row "
         "still needs the ink.", "",
         f"Calibrated on **{model['overall'][1]} ledger rulings** that recorded "
         f"a consensus reading; {model['overall'][0]} of them adopted it, a base "
         f"rate of {_beta_mean(model['overall'][0], model['overall'][1]):.0%}. "
         f"That base rate is the FALLBACK only - the strata below differ from it "
         f"by more than 60 points, which is the whole reason this file exists.",
         "",
         "## What each stratum is worth", "",
         "| engines agreeing | n | adopted | posterior | 90% CI |",
         "|---|---:|---:|---:|---|"]
    for key, (adopted, n) in sorted(model["engines"].items(),
                                    key=lambda kv: -_beta_mean(kv[1][0], kv[1][1])):
        lo, hi = _beta_interval(adopted, n)
        # A thin stratum's own posterior is shown for completeness, but scoring
        # does NOT use it - score() falls back to the engine count, or to the
        # whole sample. Saying so in the row that displays the number, because a
        # table column called "posterior" beside a row the ranker ignores is
        # exactly how a reader concludes the ranker used it.
        note = "" if n >= MIN_STRATUM_N else (
            f" ⚠ thin (n<{MIN_STRATUM_N}); ranking falls back to the engine count")
        L.append(f"| `{key}` | {n} | {adopted} | {_beta_mean(adopted, n):.0%} | "
                 f"{lo:.0%}–{hi:.0%}{note} |")
    L += ["",
          "**Every set containing DocAI scores low and that is mostly SELECTION.** "
          "Candidates are generated from DocAI's disagreements with the corpus, so "
          "a DocAI-involved consensus is disproportionately re-proposing a word "
          "that vision adjudication or a human has already settled. Read it as "
          "\"this position has probably been looked at already\", not as \"DocAI "
          "is unreliable\".", "",
          "## The queue, by band", "",
          "| posterior | disputes |", "|---|---:|"]
    for band in (">=0.75", ">=0.50", ">=0.25", "<0.25"):
        L.append(f"| {band} | {bands[band]} |")
    L += ["", f"## The top {min(args.top, len(ranked))}", "",
          "Highest posterior first - the disputes most likely to be genuine "
          "corpus errors, and so the cheapest place for a reviewer to start.", ""]
    for r in ranked[:args.top]:
        marks = []
        if r.get("cross_edition"):
            marks.append(f"cross-edition (**{r.get('same_edition_agreeing')}** "
                         f"Berlin engine(s) dissent)")
        if r.get("abbreviation_shape"):
            marks.append(f"`{r['abbreviation_shape']}`")
        if r.get("ligature_artifact"):
            marks.append(f"ligature `{r['ligature_artifact']}`")
        L.append(
            f"- **{r['posterior']:.0%}** [klal {r['klal_id']} · w{r['word_index']}]"
            f"({base}/klal/{r['klal_id']}/word/{r['word_index']}) — corpus "
            f"`{r.get('final_text')}` → consensus `{r.get('consensus_reading')}` "
            f"({', '.join(r.get('agreeing_engines') or [])})"
            + (f"; {'; '.join(marks)}" if marks else ""))
    L += ["", "## Limits", "",
          "1. The calibration is positions a human RULED ON. If the easy disputes "
          "were worked first, the untouched queue is harder than this sample "
          "says (Lesson 27).",
          "2. A stratum marked thin has fewer than "
          f"{MIN_STRATUM_N} observations and falls back to the engine COUNT, or "
          "to the whole sample, rather than being trusted on its own.",
          "3. This is not `tools/estimate_consensus_posterior.py`'s number and "
          "does not replace it. That one arbitrates UNDECIDED positions with "
          "vision to ask whether consensus may ever auto-approve (it may not, "
          "~31%). This one asks a different question - what should a human open "
          "first - and answers it from what humans actually did."]

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
        f.flush()

    print(f"Wrote {out_path} and {json_path}")
    print(f"  {len(ranked)} open disputes, calibrated on {model['overall'][1]} rulings")
    for band in (">=0.75", ">=0.50", ">=0.25", "<0.25"):
        print(f"    {bands[band]:>4}  posterior {band}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
