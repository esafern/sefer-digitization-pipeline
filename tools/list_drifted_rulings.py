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
import drift_recovery as drec  # noqa: E402
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


def describe(rec):
    """What this ruling was ABOUT, in words a reviewer can act on.

    WHY THIS IS NOT JUST `original_word`. 16 of the 39 rows read
    `ruled on None -> chose ''` and were unactionable - no word, no choice, so
    nothing to judge. Every one turned out to be a `delete` OPCODE: DocAI read a
    word the corpus does not have and the candidate proposed INSERTING it, so
    `final_text` and `original_word` are null BY DEFINITION - there is no stored
    span, which is the entire point of that opcode. The evidence was in the
    record the whole time, one field over, in `docai_reading`; the worklist
    simply never rendered it. Lesson 29: a field nothing displays is not a field
    the reviewer has.

    So: name the opcode, and quote the reading the proposal is about.
    """
    snap = rec.get("candidate_snapshot") or {}
    opcode = snap.get("opcode")
    chosen = rec.get("chosen_text")
    if opcode == "delete":
        seen = snap.get("docai_reading")
        answer = ("REJECTED it" if chosen in ("", None)
                  else f"accepted it as `{chosen}`")
        return (f"insertion proposal - DocAI reads `{seen}` here and the corpus "
                f"does not have it; the reviewer {answer}")
    was = rd.original_word(rec)
    if opcode == "insert":
        return (f"removal proposal - the corpus has `{was}` and DocAI does not; "
                + ("the reviewer REJECTED the removal" if chosen == was
                   else f"the reviewer chose `{chosen}`"))
    if was is None and chosen is None:
        return f"{rec['decision_type']} recording no original and no choice"
    return f"ruled on `{was}` -> chose `{chosen}`"


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
    ap.add_argument("--hebrew", choices=("visual", "logical"), default="visual",
                    help="visual (default): reorder Hebrew so it reads correctly in a "
                         "viewer that runs no bidi algorithm, at the cost of being "
                         "copy-unsafe. logical: storage order, copy-safe, correct only "
                         "in a bidi-aware renderer. Matches tools/preview_dicta_disputes.py.")
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

    # THE SHIFT SIGNAL, added 2026-09-06. Both existing signals are per-ruling:
    # the ink reads one recorded bbox, the text searches for one word. Neither
    # can use the fact that the OTHER rulings in the same klal moved by a known
    # amount, which is the cheapest evidence available here and needs no bbox at
    # all - see pipeline/drift_recovery.py. It settles 11 of these outright, so
    # they stop being hand judgements.
    applied_ids = rd.applied_decision_ids()
    recovered = {}
    by_klal = collections.defaultdict(list)
    for kid, wi in positions:
        rec = rows_by_key.get((kid, wi))
        if rec:
            by_klal[kid].append(rec)
    for kid, recs in by_klal.items():
        klal = part1.get(kid)
        if not klal:
            continue
        words = cio.words_of(klal)
        stale = [r for r in recs if drec.stale_against(words, r, r["id"] in applied_ids)]
        got, _refused = drec.recover_klal(words, stale, applied_ids)
        for rid, (new_wi, off, why) in got.items():
            recovered[rid] = (new_wi, off, why)

    buckets = collections.defaultdict(list)
    for kid, wi in positions:
        rec = rows_by_key.get((kid, wi))
        klal = part1.get(kid)
        if not rec or not klal:
            continue
        words = cio.words_of(klal)
        ink, text = signals(rec, kid, words, regions, cache)
        live = words[wi] if wi < len(words) else "(past the end of the klal)"
        shift = recovered.get(rec["id"])
        row = {"klal_id": kid, "word_index": wi, "rec": rec, "live": live,
               "ink": ink, "text": text, "shift": shift,
               "what": describe(rec),
               "chose": rec.get("chosen_text")}
        if shift is not None:
            buckets["shift"].append(row)
        elif ink is not None and text and ink in text:
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

    order = [("shift", "SETTLED by the shift the rest of the klal moved by - no judgement needed",
              "These need no reading. Every other ruling in the same klal moved "
              "by one known amount, or the word is unique in the klal, so the "
              "position is determined arithmetically (pipeline/drift_recovery.py, "
              "which states its bar and refuses everything that does not meet "
              "it). Re-point them with `tools/repoint_stale_decisions.py` or "
              "confirm them in the dashboard; they are listed so the move is "
              "visible, not because they need a decision."),
             ("conflict", "The ink and the text point at DIFFERENT words",
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
        # ONE ROW PER QUESTION, not per ruling. klal 210 filed w66, w67 and w68
        # as three separate judgement calls that all resolve to w65 with the
        # identical `כקמייתא -> כקמייתא`, and w132/w133 both to w108 - five rows
        # for two questions. Rulings that land on the same word with the same
        # answer are one question, and are shown as one.
        groups = collections.OrderedDict()
        for r in sorted(rows, key=lambda x: (x["klal_id"], x["word_index"])):
            at = (r["shift"][0] if r["shift"] is not None
                  else r["ink"] if r["ink"] is not None
                  else (r["text"][0] if r["text"] else r["word_index"]))
            groups.setdefault((r["klal_id"], at, r["what"]), []).append(r)
        for (kid, at, what), members in groups.items():
            first = members[0]
            where = ", ".join(f"w{m['word_index']}" for m in members)
            L.append(
                f"- [klal {kid} · {where}]"
                f"({base}/klal/{kid}/word/{at}) — {what}; that index now holds "
                f"`{first['live']}`"
                + (f"; **the klal shifted {first['shift'][1]:+d}** here "
                   f"({first['shift'][2]}) → **w{first['shift'][0]}**"
                   if first["shift"] is not None else "")
                + (f"; ink says **w{first['ink']}**" if first["ink"] is not None else "")
                + (f"; text finds it at {', '.join('w'+str(i) for i in first['text'][:4])}"
                   if first["text"] else "")
                + (f"  _({len(members)} rulings, same word, same answer)_"
                   if len(members) > 1 else ""))
        L.append("")

    if args.hebrew == "visual":
        L = [L[0], "", cio.VISUAL_WARNING] + L[1:]
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(cio.render_hebrew(L, args.hebrew)) + "\n")
        f.flush()
    print(f"Wrote {args.out}: {len(positions)} ruling(s)")
    for key, title, _ in order:
        if buckets.get(key):
            print(f"  {len(buckets[key]):>3}  {title}")


if __name__ == "__main__":
    main()
