#!/usr/bin/env python3
"""
tools/analyze_decision_ledger.py

[STANDALONE] What the review ledger says about the engines, the reviewer, and
the corpus - re-derived from review_decisions.jsonl on every run.

Written 2026-09-04 at the reviewer's request ("review all decisions in the
ledger. look for patterns of all kinds"). A tool rather than a one-off analysis
because every number here moves as review continues, and a figure quoted from a
conversation is a figure nobody can check (Lesson 32, and the reason
PROJECT-STATUS carries "re-measure, don't quote from here").

THE GROUND TRUTH IS THE HUMAN'S RULING, and its limits are the first thing to
state. A ruling is one person reading a crop; it is the best signal available
and it is not infallible. More important, THE SAMPLE IS SELECTED, and in a
different way for each engine:

  * A position only EXISTS in this analysis because something disputed it. No
    engine's accuracy over the whole corpus can be read off these numbers.
  * DocAI is worst hit. Candidates are GENERATED from DocAI's disagreements
    with the stored text, so DocAI appears here almost exclusively where it
    dissented - and a dissent that survived to a human is usually a dissent
    that was wrong. Its "12% accurate" below is a statement about the
    selection, not about DocAI.
  * tools/estimate_consensus_posterior.py refuses this sample entirely for
    exactly this reason and uses the vision arbiter instead. Its 26-41% and
    the consensus ladder below are NOT the same quantity; see the note there.

The unbiased comparisons are the head-to-head ones: given two engines that both
read a position and read it DIFFERENTLY, the human's ruling picks a winner, and
neither engine's presence caused the position to be selected.
"""
import collections
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
INSTALL_DIR = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(INSTALL_DIR, "pipeline"))

import corpus_io as cio  # noqa: E402
import identity as idn  # noqa: E402
import review_decisions as rd  # noqa: E402

N = cio.hebrew_letters_only
SCORED_TYPES = ("disputed_choice", "candidate_choice")
RULING_TYPES = SCORED_TYPES + ("manual_correction", "witness_choice",
                               "title_correction", "punctuation_choice")
ENGINES = {"docai": "docai_reading", "docai_repaired": "docai_repaired",
           "vlm": "vlm_reading", "surya": "surya_reading",
           "dicta": "dicta_reading", "vision": "vision_transcription"}


def load(path=None):
    return rd.all_records(path) if hasattr(rd, "all_records") else [
        json.loads(l) for l in open(path or rd.DECISIONS_PATH, encoding="utf-8")]


def current_scored(rows):
    """The CURRENT human ruling at each position that carries engine readings.

    Current, because a superseded ruling is not a second verdict; human, because
    a script's `manual_correction` is not an adjudication (item 0AT)."""
    cur = {}
    for r in rows:
        if (r["decision_type"] in SCORED_TYPES and r.get("candidate_snapshot")
                and r.get("word_index") is not None):
            cur[(r["klal_id"], r["word_index"])] = r
    return [r for r in cur.values() if idn.is_human(idn.actor_of(r))]


def _reading(snap, engine):
    v = snap.get(ENGINES[engine])
    return N(v) if v else None


def per_engine(scored):
    out = collections.defaultdict(collections.Counter)
    for r in scored:
        s, truth = r["candidate_snapshot"], N(r.get("chosen_text") or "")
        stored = N(s.get("final_text") or "")
        if not truth:
            continue
        for e in ENGINES:
            v = _reading(s, e)
            if v is None:
                continue
            c = out[e]
            c["seen"] += 1
            c["right" if v == truth else "wrong"] += 1
            if v != stored:
                c["differed"] += 1
                if v == truth:
                    c["differed_right"] += 1
        if stored:
            out["(stored corpus)"]["seen"] += 1
            out["(stored corpus)"]["right" if stored == truth else "wrong"] += 1
    return out


def head_to_head(scored, a, b):
    """Contests where both engines read the position and DISAGREED."""
    aw = bw = nw = 0
    for r in scored:
        s, truth = r["candidate_snapshot"], N(r.get("chosen_text") or "")
        x, y = _reading(s, a), _reading(s, b)
        if not truth or x is None or y is None or x == y:
            continue
        if x == truth:
            aw += 1
        elif y == truth:
            bw += 1
        else:
            nw += 1
    return aw, bw, nw


def consensus_ladder(scored):
    """How often the reading k agreeing engines propose turns out correct."""
    by_k = collections.defaultdict(collections.Counter)
    for r in scored:
        s, truth = r["candidate_snapshot"], N(r.get("chosen_text") or "")
        stored = N(s.get("final_text") or "")
        if not truth or not stored:
            continue
        alt = collections.defaultdict(list)
        for e in ("docai", "vlm", "surya", "dicta"):
            v = _reading(s, e)
            if v and v != stored:
                alt[v].append(e)
        if not alt:
            continue
        reading, who = max(alt.items(), key=lambda kv: len(kv[1]))
        d = by_k[len(who)]
        d["n"] += 1
        d["right" if reading == truth else "wrong"] += 1
    return by_k


def error_signature(scored, engine):
    kinds, pairs, n = collections.Counter(), collections.Counter(), 0
    for r in scored:
        s, truth = r["candidate_snapshot"], N(r.get("chosen_text") or "")
        v = _reading(s, engine)
        if not truth or v is None or v == truth:
            continue
        n += 1
        if len(v) == len(truth):
            d = [(x, y) for x, y in zip(v, truth) if x != y]
            kinds["one letter" if len(d) == 1 else f"{len(d)} letters"] += 1
            if len(d) == 1:
                pairs[frozenset(d[0])] += 1
        elif len(truth) == len(v) + 1:
            kinds["dropped a letter"] += 1
        elif len(v) == len(truth) + 1:
            kinds["added a letter"] += 1
        else:
            kinds["other"] += 1
    return n, kinds, pairs


def unreviewed_machine_corrections(rows):
    """Machine-written manual_corrections APPLIED to the corpus that no person
    has ruled on - item 0AT's class, counted as it stands today."""
    applied = rd.applied_decision_ids()
    cur = {}
    for r in rows:
        if r["decision_type"] in RULING_TYPES and r.get("word_index") is not None:
            cur[(r["klal_id"], r["word_index"], r["decision_type"])] = r
    human_pos = {(r["klal_id"], r["word_index"]) for r in cur.values()
                 if idn.is_human(idn.actor_of(r))}
    flags = {}
    for r in rows:
        if r["decision_type"] == "klal_flag":
            flags[(r["klal_id"], r.get("word_index"))] = r
    out = []
    for r in cur.values():
        if (r["decision_type"] == "manual_correction"
                and not idn.is_human(idn.actor_of(r))
                and r["id"] in applied
                and (r["klal_id"], r["word_index"]) not in human_pos):
            f = flags.get((r["klal_id"], r["word_index"])) or {}
            out.append((r, bool(f.get("needs_revisit"))))
    return out


def main():
    rows = load()
    scored = current_scored(rows)
    print(f"LEDGER: {len(rows)} records, {rows[0]['ts'][:10]} to {rows[-1]['ts'][:10]}")
    print(f"SCORED: {len(scored)} positions with a current HUMAN ruling and engine readings")
    print("        (selected sample - see this file's header before quoting any rate)\n")

    print("PER SOURCE, against the human's ruling")
    print(f"  {'source':>16} {'seen':>5} {'acc':>6} | {'differed':>8} {'right':>6} {'precision':>10}")
    for e, c in sorted(per_engine(scored).items(), key=lambda kv: -kv[1]["seen"]):
        acc = c["right"] / c["seen"] if c["seen"] else 0
        d, dr = c["differed"], c["differed_right"]
        p = f"{dr / d:.0%}" if d else "-"
        print(f"  {e:>16} {c['seen']:>5} {acc:>5.0%} | {d:>8} {dr:>6} {p:>10}")

    print("\nHEAD-TO-HEAD (both read it, and read it differently - the fair comparison)")
    import itertools
    for a, b in itertools.combinations(["docai", "vlm", "surya", "dicta"], 2):
        aw, bw, nw = head_to_head(scored, a, b)
        if aw + bw + nw == 0:
            continue
        dec = aw + bw
        rate = f"{aw / dec:.0%}" if dec else "-"
        print(f"  {a:>6} vs {b:<7} n={aw+bw+nw:>4}  {a} {aw:>3} / {b} {bw:>3} / neither {nw:>3}"
              f"   {a} wins {rate} of decided")

    print("\nCONSENSUS LADDER: k engines agreeing on the same alternative")
    for k, d in sorted(consensus_ladder(scored).items()):
        print(f"  {k} engine(s): n={d['n']:>4}  the proposed reading was correct "
              f"{d['right']:>3} ({d['right'] / d['n']:.0%})")
    print("  NOT comparable to estimate_consensus_posterior.py's 26-41%: that uses the")
    print("  vision arbiter on UNDECIDED positions, precisely because this sample is selected.")

    print("\nERROR SIGNATURES")
    for e in ("docai", "vlm", "surya", "dicta"):
        n, kinds, pairs = error_signature(scored, e)
        if not n:
            continue
        print(f"  {e:>6}: {n:>3} errors | " + ", ".join(f"{k} {v}" for k, v in kinds.most_common(4)))
        if pairs:
            print("          confusions: " + ", ".join(
                f"{''.join(sorted(p))}x{v}" for p, v in pairs.most_common(5)))

    print("\nTHE VISION ARBITER")
    right = wrong = ch_r = ch_w = 0
    conf = collections.defaultdict(list)
    for r in scored:
        s, truth = r["candidate_snapshot"], N(r.get("chosen_text") or "")
        vt, stored = s.get("vision_transcription"), N(s.get("final_text") or "")
        if not truth or not vt:
            continue
        ok = N(vt) == truth
        right, wrong = right + ok, wrong + (not ok)
        if N(vt) != stored:
            ch_r, ch_w = ch_r + ok, ch_w + (not ok)
        if s.get("confidence") is not None:
            conf[ok].append(s["confidence"])
    if right + wrong:
        print(f"  agrees with the human {right}/{right+wrong} ({right/(right+wrong):.0%})")
    if ch_r + ch_w:
        print(f"  WHEN IT PROPOSES A CHANGE: {ch_r}/{ch_r+ch_w} correct ({ch_r/(ch_r+ch_w):.0%})")
    for ok in (True, False):
        if conf[ok]:
            print(f"  mean stated confidence when {'right' if ok else 'wrong':>5}: "
                  f"{statistics.mean(conf[ok]):.3f}  (n={len(conf[ok])})")
    print("  A threshold on `confidence` cannot separate the two.")

    print("\nUNREVIEWED MACHINE CORRECTIONS ALREADY IN THE CORPUS (item 0AT)")
    un = unreviewed_machine_corrections(rows)
    flagged = sum(1 for _, f in un if f)
    print(f"  applied, still current, never ruled on by a person: {len(un)}")
    print(f"    ...carrying an open revisit flag: {flagged}")
    print(f"    ...with NO open flag, invisible in every queue: {len(un) - flagged}")
    by = collections.Counter(r.get("reviewer") for r, _ in un)
    for k, v in by.most_common():
        print(f"    {v:>4}  {k}")


if __name__ == "__main__":
    main()
