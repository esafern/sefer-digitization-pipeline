#!/usr/bin/env python3
"""
tools/measure_correction_overlap.py

What our OCR reads at every place a human corrected the witness. Item `0GH`.

Three texts per reviewed entry: the witness's raw OCR (T), the same witness after
its human review (C), and one or more of our corpora (O). Every difference T -> C
is one of THEIR edits, classified by kind:

    reading    the letters change                  - an OCR correction
    division   same letters, word boundaries move
    citation   a parenthesised reference added or removed inline
    editorial  a bracketed [..] insertion or removal
    note       a run of their own words added (no counterpart in T)

and each reading correction by what O reads there, located through the words
where O and T agree on either side:

    HAD        O reads their correction            - we already had it
    SHARED     O reads their uncorrected OCR       - we made their original error
    THIRD      O reads something else              - we disagree with both
    UNALIGNED  O's text there cannot be isolated

Letters only - points deleted, punctuation separating - which is
build_witness_disputes.text_words(), the normalisation the review queue uses. A
correction that only moves punctuation is not counted.

It also counts the positions where O differs from T (the dispute surface a
reviewer would be shown) and where O differs from C.

A THIRD or SHARED row is a place where our text disagrees with a human's
correction. That is a question for the ink, not a verdict: on 2026-09-14 the 12
such rows on the NLI build were read off the scan - 5 were our own footnote
markers glued to the right word, 4 our misreads, and 3 places where the page
prints what we read and the correction departs from it.

Usage:
  SEFER_CORPUS_ROOT=~/work/hashorashim python3 tools/measure_correction_overlap.py \\
      --corpus "NLI=~/work/hashorashim/part1.json" --corpus "bitonal=/tmp/bitonal/part1.json" \\
      --list NLI
"""

import argparse
import collections
import difflib
import json
import os
import sys
import unicodedata

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "pipeline"))
sys.path.insert(0, _HERE)
import corpus_io as cio  # noqa: E402
import build_witness_disputes as bwd  # noqa: E402


def _letters(span):
    return "".join(w for w, _r, _p in span)


def _raw(text, span):
    toks = cio.words_of(text)
    return " ".join(cio.strip_points(unicodedata.normalize("NFKC", toks[p])) for _w, _r, p in span)


def join_homograph_halves(corrected):
    """The reviewed export splits a homograph pair (`אלה a`, `אלה b`) where the
    raw OCR and our root groups hold ONE text per root: join the halves in order."""
    out = {}
    for k, v in corrected.items():
        base = k[:-2] if k[-2:] in (" a", " b") else k
        out[base] = (out[base] + " " + v) if base in out else v
    return out


def _our_words(entries):
    out = []
    for k in entries:
        out += [(w, r, (k["klal_id"], p, k["clean_text"]))
                for w, r, p in bwd.text_words(k["clean_text"])]
    return out


def _kind(tspan, cspan, T, C):
    if _letters(tspan) == _letters(cspan):
        return "division"
    raw = ([cio.words_of(C)[p] for _w, _r, p in cspan]
           + [cio.words_of(T)[p] for _w, _r, p in tspan])
    if any("(" in t or ")" in t for t in raw):
        return "citation"
    if any("[" in t or "]" in t for t in raw):
        return "editorial"
    if not tspan and len(cspan) > 6:
        return "note"
    return "reading"


def compare(groups, corrected, witness):
    """(rows, stats). `groups` is bwd.root_groups(our entries); `corrected` maps a
    root to C; `witness` maps a root_key to T."""
    rows, stats = [], collections.Counter()
    for root, C in corrected.items():
        rk = cio.root_key(root)
        if rk not in groups or rk not in witness:
            stats["root not matched"] += 1
            continue
        T = witness[rk]
        tw, cw, ow = bwd.text_words(T), bwd.text_words(C), _our_words(groups[rk])
        tl, cl, ol = [w[0] for w in tw], [w[0] for w in cw], [w[0] for w in ow]
        tmap = {}
        for a, b, n in difflib.SequenceMatcher(None, tl, ol, autojunk=False).get_matching_blocks():
            for k in range(n):
                tmap[a + k] = b + k
        indexed = [(w, r, i) for i, (w, r, _x) in enumerate(ow)]
        stats["entries"] += 1
        stats["O~T positions"] += len(bwd.disputes_for(indexed, tw))
        stats["O~C positions"] += len(bwd.disputes_for(indexed, cw))
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, tl, cl, autojunk=False).get_opcodes():
            if tag == "equal":
                continue
            tspan, cspan = tw[i1:i2], cw[j1:j2]
            kind = _kind(tspan, cspan, T, C)
            left = next((t for t in range(i1 - 1, -1, -1) if t in tmap), None)
            right = next((t for t in range(i2, len(tl)) if t in tmap), None)
            o1 = tmap[left] + 1 if left is not None else 0
            o2 = tmap[right] if right is not None else len(ol)
            t1 = left + 1 if left is not None else 0
            t2 = right if right is not None else len(tl)
            oreg = ow[o1:o2]
            creg_words = [w[0] for w in tw[t1:i1]] + [w[0] for w in cspan] + [w[0] for w in tw[i2:t2]]
            if (o2 - o1) > (t2 - t1) + 3:
                status = "UNALIGNED"
            elif _letters(oreg) == "".join(creg_words):
                status = "HAD"
            elif _letters(oreg) == _letters(tw[t1:t2]):
                status = "SHARED"
            else:
                # the region may also hold an unrelated difference: judge the
                # edit's own words inside it
                sm = difflib.SequenceMatcher(None, [w[0] for w in oreg], creg_words, autojunk=False)
                lo, hi = i1 - t1, i1 - t1 + len(cspan)
                covered = sum(1 for a, b, n in sm.get_matching_blocks()
                              for q in range(b, b + n) if lo <= q < hi)
                status = "HAD" if cspan and covered == len(cspan) else "THIRD"
            if oreg:
                kid, pos, text = oreg[0][2]
                ours = " ".join(cio.words_of(text)[w[2][1]] for w in oreg)
            else:
                kid, pos, _t = ow[min(o1, len(ow) - 1)][2] if ow else (None, None, "")
                ours = ""
            stats[kind] += 1
            stats[f"{kind}:{status}"] += 1
            rows.append({"root": root, "kind": kind, "status": status, "klal_id": kid,
                         "word_index": pos, "ours": ours, "their_ocr": _raw(T, tspan),
                         "their_corrected": _raw(C, cspan)})
    return rows, stats


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpus", action="append", help="name=path to a part1.json (default: this root's)")
    ap.add_argument("--corrected", default=None, help="default: gold100_text.json in the corpus root")
    ap.add_argument("--witness", default=None, help="default: witness_entries_flat.json in the corpus root")
    ap.add_argument("--list", default=None, help="corpus name whose disagreements to print")
    ap.add_argument("--url-base", default="http://127.0.0.1:8421")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    with open(args.corrected or cio.repo_path("gold100_text.json"), encoding="utf-8") as fh:
        corrected = join_homograph_halves(json.load(fh))
    with open(args.witness or cio.repo_path("witness_entries_flat.json"), encoding="utf-8") as fh:
        witness = {cio.root_key(k): v for k, v in json.load(fh).items()}
    allrows = {}
    for spec in args.corpus or [f"corpus={cio.PART1_PATH}"]:
        name, path = spec.split("=", 1)
        rows, st = compare(bwd.root_groups(cio.load_klalim(os.path.expanduser(path))),
                           corrected, witness)
        allrows[name] = rows
        print(f"\n=== {name}: {st['entries']} reviewed roots ({st['root not matched']} not matched)")
        print(f"  their edits: reading {st['reading']}, division {st['division']}, citation "
              f"{st['citation']}, editorial {st['editorial']}, note {st['note']}")
        for s in ("HAD", "SHARED", "THIRD", "UNALIGNED"):
            print(f"    reading, ours {s:<10} {st['reading:' + s]}")
        print(f"  positions where ours differs from their OCR:       {st['O~T positions']}")
        print(f"  positions where ours differs from their corrected: {st['O~C positions']}")
    if args.list:
        for r in allrows[args.list]:
            if r["kind"] == "reading" and r["status"] != "HAD":
                print(f"{r['status']:<9} {r['root']:<6} {args.url_base}/entry/{r['klal_id']}/word/"
                      f"{r['word_index']}  ours [{r['ours']}]  their OCR [{r['their_ocr']}]  "
                      f"corrected [{r['their_corrected']}]")
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(allrows, fh, ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
