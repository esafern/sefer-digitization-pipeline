#!/usr/bin/env python3
"""
tools/list_drifted_rulings.py

[STANDALONE] The rulings apply_reviewer_decisions.py refuses because their
address rotted - as a worklist with the evidence needed to settle each one.

Reviewer, 2026-09-05: "how do i review the 46".

WHY NOT THE DASHBOARD. It has a "stale address" chip on the recorded view, and
it is the wrong set twice over. Measured today: 83 rows carry `index_stale`, but
61 of them are ALREADY APPLIED - their address rotted after the edit landed, so
nothing is blocked and re-pointing them changes nothing a reviewer can see. Only
22 overlap the applier's refusals, and the applier refuses 46, because
`_decision_index_is_stale` (does this decision's index still name its word) and
`check_drift` (does this CANDIDATE still match live text) are different tests
that disagree on which rulings are stuck. Neither surface isolates the set that
actually blocks, and neither shows the two signals a re-point needs.

WHAT EACH ROW GIVES YOU. The ruling, what the corpus holds at its recorded index
now, and both independent signals - where the INK puts it (the snapshot bbox
resolved through scan_alignment.word_bboxes_resolved, the same geometry the
dashboard highlights with) and where the TEXT finds the word it names. Where
those agree, repoint_stale_decisions.py would already have moved it, so
everything here is a case where they disagree, only one exists, or neither does.
That is the judgement being asked for, and the row says which of the three it
is rather than making you work it out.

Links open the review dashboard at the position the ink suggests, when there is
one - that is the word to look at, not the rotted index.
"""
import argparse
import collections
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
INSTALL_DIR = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(INSTALL_DIR, "pipeline"))

import corpus_io as cio  # noqa: E402
import review_decisions as rd  # noqa: E402
import scan_alignment as sa  # noqa: E402

DEFAULT_BASE = "http://127.0.0.1:8420"
OUT_PATH = cio.repo_path("DRIFTED-RULINGS-WORKLIST.md")
RULING_TYPES = ("disputed_choice", "candidate_choice", "manual_correction",
                "witness_choice")


def refused_positions():
    """(klal_id, word_index) the applier is currently refusing for drift.

    Read from the applier's own dry run rather than re-deriving check_drift
    here: a second copy of "which rulings are stuck" would drift from the one
    that decides (Lesson 13), and this list exists to describe that decision.
    """
    out = subprocess.run(
        [sys.executable, os.path.join(INSTALL_DIR, "pipeline",
                                      "apply_reviewer_decisions.py"), "--dry-run"],
        capture_output=True, text=True, cwd=INSTALL_DIR).stdout
    tail = out.split("candidate data has drifted since the decision was made")
    if len(tail) < 2:
        return []
    pos = []
    for line in tail[1].split("\n"):
        m = re.match(r"\s*klal (\d+) word (\d+)\s*$", line)
        if m:
            pos.append((int(m.group(1)), int(m.group(2))))
        elif pos and line.strip() and not line.startswith(" "):
            break
    return pos


def _distance(a, b):
    return (abs(a["x1"] - b["x1"]) + abs(a["y1"] - b["y1"])
            + abs(a["x2"] - b["x2"]) + abs(a["y2"] - b["y2"]))


def signals(rec, klal_id, words, regions, cache):
    """(ink_index, text_indices) - the two independent answers to "where is it"."""
    snap = rec.get("candidate_snapshot") or {}
    ink = None
    bbox, page = snap.get("bbox"), snap.get("page")
    if bbox and page is not None:
        if klal_id not in cache:
            cache[klal_id] = sa.word_bboxes_resolved(klal_id, words, regions)
        here = [(i, bb) for i, (bb, pg) in cache[klal_id].items() if bb and pg == page]
        if here:
            ink = min(here, key=lambda kv: _distance(bbox, kv[1]))[0]
    hits = []
    for target in (snap.get("original_word") or snap.get("final_text"),
                   rec.get("chosen_text")):
        if target:
            hits = [i for i, w in enumerate(words) if w == target]
            if hits:
                break
    return ink, hits


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=OUT_PATH)
    ap.add_argument("--base-url", default=DEFAULT_BASE)
    args = ap.parse_args()
    base = args.base_url.rstrip("/")

    positions = refused_positions()
    rows_by_key = {}
    for r in rd.all_records():
        if r["decision_type"] in RULING_TYPES and r.get("word_index") is not None:
            rows_by_key[(r["klal_id"], r["word_index"])] = r
    part1 = {k["klal_id"]: k for k in cio.load_part1_sorted()}
    regions = sa.load_regions()
    cache = {}

    buckets = collections.defaultdict(list)
    for kid, wi in positions:
        rec = rows_by_key.get((kid, wi))
        klal = part1.get(kid)
        if not rec or not klal:
            continue
        words = cio.words_of(klal)
        ink, text = signals(rec, kid, words, regions, cache)
        live = words[wi] if wi < len(words) else "(past the end of the klal)"
        row = {"klal_id": kid, "word_index": wi, "rec": rec, "live": live,
               "ink": ink, "text": text,
               "ruled_on": (rec.get("candidate_snapshot") or {}).get("original_word")
                           or (rec.get("candidate_snapshot") or {}).get("final_text"),
               "chose": rec.get("chosen_text")}
        if ink is not None and text and ink in text:
            buckets["agree"].append(row)      # should not happen - repoint takes these
        elif ink is not None and text:
            buckets["conflict"].append(row)
        elif ink is not None:
            buckets["ink only"].append(row)
        elif text:
            buckets["text only"].append(row)
        else:
            buckets["no evidence"].append(row)

    L = ["# Drifted rulings - the ones the applier will not touch", "",
         f"{len(positions)} ruling(s), generated by `tools/list_drifted_rulings.py`. "
         "**Regenerate after any apply** - the addresses move.", "",
         "Each of these named a word by its position, and the position no longer "
         "names that word. The applier refuses rather than write to a place it "
         "cannot verify, and `repoint_stale_decisions.py` has already taken every "
         "case where the ink and the text agree - so everything below is a case "
         "where they disagree, only one of them exists, or neither does.", "",
         "**The ink is the stronger signal.** It is the scan position recorded "
         "with the ruling, resolved through the same geometry the dashboard "
         "highlights with. Where a link is given it opens the word the ink "
         "points at, which is the one to look at - not the rotted index.", ""]

    order = [("conflict", "The ink and the text point at DIFFERENT words",
              "Read the scan at the ink's word. If the ruling belongs there, "
              "re-rule at that index; if it belongs at the text's word, the bbox "
              "is stale and the text wins."),
             ("ink only", "Only the ink has an answer",
              "The word the ruling names is no longer anywhere in the klal - "
              "usually because a later correction changed it. The ink still knows "
              "where the ruling was made."),
             ("text only", "Only the text has an answer",
              "No usable scan position was recorded. The word is findable, but a "
              "text match is not evidence of position (Lesson 5) - confirm "
              "against the page before re-ruling."),
             ("no evidence", "Neither signal has an answer",
              "Nothing locates these but reading the klal. Cheapest treated as a "
              "fresh review of that word rather than a recovery."),
             ("agree", "The address is fine - it is the CANDIDATE that went stale",
              "Both signals point at the recorded index, and repoint_stale_"
              "decisions.py agrees: it calls these `ok`, because the word is "
              "still there. The applier refuses for a different reason - the "
              "corrections entry the ruling hangs on no longer matches live "
              "text. Nothing needs re-pointing; the question is whether the "
              "ruling still says what you want at that word. Several are also "
              "cases close_satisfied_rulings.py declined because the chosen "
              "word repeats in the klal and no bbox corroborates which instance "
              "is meant - `אליבא` occurs 11 times in klal 91.")]

    for key, title, guidance in order:
        rows = buckets.get(key) or []
        if not rows:
            continue
        L += [f"## {title} ({len(rows)})", "", guidance, ""]
        for r in sorted(rows, key=lambda x: (x["klal_id"], x["word_index"])):
            at = r["ink"] if r["ink"] is not None else (r["text"][0] if r["text"] else r["word_index"])
            L.append(
                f"- [klal {r['klal_id']} · w{r['word_index']}]"
                f"({base}/klal/{r['klal_id']}/word/{at}) — ruled on "
                f"`{r['ruled_on']}` → chose `{r['chose']}`; that index now holds "
                f"`{r['live']}`"
                + (f"; ink says **w{r['ink']}**" if r["ink"] is not None else "")
                + (f"; text finds it at {', '.join('w'+str(i) for i in r['text'][:4])}"
                   if r["text"] else ""))
        L.append("")

    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
        f.flush()
    print(f"Wrote {args.out}: {len(positions)} ruling(s)")
    for key, title, _ in order:
        if buckets.get(key):
            print(f"  {len(buckets[key]):>3}  {title}")


if __name__ == "__main__":
    main()
