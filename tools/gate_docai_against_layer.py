#!/usr/bin/env python3
"""
tools/gate_docai_against_layer.py

Where do the TWO GOOGLE READINGS of this scan disagree? Those positions, and
only those, are what the recovered PDF text layer is good for.

WHAT THIS IS NOT (read before wiring it anywhere). The Google Books text layer
recovered by `tools/extract_pdf_text_layer.py` scores 97.2% word accuracy on
klalim 13-23 - second only to DocAI's 98.6% - and it is **not an independent
witness**. Measured on that same window, its top substitutions are DocAI's:

    Google Books layer:  ה->ח x6,  ∅->י x4,  ∅->יי x4,  כ->ב x3,  ם->ס x2
    DocAI (primary):     ה->ח x6,  ∅->יי x4, ∅->י x4,   ב->כ x3,  מ->ט x2

Same error, same count, on the top four. Two Google OCR systems reading one
sheet of ink fail the same way - Lesson 24 SHARED INK, SHARED ERROR on top of
Lesson 23 AN ENGINE, NOT A SAMPLE. Counting this layer as a third vote would
manufacture false 2-of-3 consensus on exactly the glyphs DocAI already gets
wrong, which is the failure mode item 0N and the whole witness layer exist to
avoid.

WHAT IT IS. Lesson 23's own prescription for a repeated read of one engine: use
it as a RELIABILITY GATE. Where two Google systems reading the same pixels
diverge, the ink is ambiguous enough to split them and DocAI's reading there is
less certain than its headline accuracy suggests. Where they agree, the
agreement adds almost nothing beyond DocAI's own confidence - so AGREEMENT IS
NOT EVIDENCE HERE and this tool deliberately does not report it as a score.

The output is therefore a triage surface, not a correction queue. It says "look
here", never "change this". No caller applies it, by design.

Usage:
  python3 tools/gate_docai_against_layer.py --out docai_layer_gate.json
  python3 tools/gate_docai_against_layer.py --pages 20-40 --show 25
"""

import argparse
import difflib
import json
import os
import sys

# Bootstrap only - deliberately NOT bound to a name like REPO, which is the
# seam bypass tests/test_pipeline_logic.py's bypass guard exists to catch. Every
# real path below goes through corpus_io, which resolves $SEFER_CORPUS_ROOT at
# call time.
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "pipeline"))
import corpus_io as cio  # noqa: E402


def layer_tokens(layer_dir, page):
    path = os.path.join(layer_dir, f"page_{page}.txt")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        raw = fh.read().split()
    return [cio.hebrew_letters_only(w) for w in raw]


def docai_tokens(page):
    path = os.path.join(cio.DOCAI_DIR, f"page_{page}.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return [cio.hebrew_letters_only(t["text"]) for t in json.load(fh)]


def divergences(docai, layer):
    """Opcodes where the two Google readings differ, as (kind, docai, layer)."""
    keep_d = [(i, w) for i, w in enumerate(docai) if len(w) >= 2]
    keep_l = [w for w in layer if len(w) >= 2]
    d = [w for _, w in keep_d]
    sm = difflib.SequenceMatcher(None, d, keep_l, autojunk=False)
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        out.append({
            "kind": tag,
            "docai_index": keep_d[i1][0] if i1 < len(keep_d) else None,
            "docai": " ".join(d[i1:i2]),
            "layer": " ".join(keep_l[j1:j2]),
        })
    return out, len(d)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--layer-dir", default=cio.repo_path("google_books_layer"))
    ap.add_argument("--pages", help="page window, e.g. 14-247 (default: every page "
                                    "present in BOTH sources)")
    ap.add_argument("--out", help="write the full result as JSON here")
    ap.add_argument("--show", type=int, default=15, help="example rows to print")
    args = ap.parse_args()

    if args.pages:
        lo, hi = (int(x) for x in args.pages.split("-"))
        pages = range(lo, hi + 1)
    else:
        pages = range(1, 400)

    rows = []
    per_page = []
    covered = 0
    for p in pages:
        d = docai_tokens(p)
        l = layer_tokens(args.layer_dir, p)
        if not d or not l:
            continue
        covered += 1
        divs, ntok = divergences(d, l)
        per_page.append({"page": p, "docai_tokens": ntok, "divergences": len(divs),
                         "rate_pct": round(100.0 * len(divs) / max(ntok, 1), 2)})
        for r in divs:
            r["page"] = p
            rows.append(r)

    tot_tok = sum(x["docai_tokens"] for x in per_page)
    print("DocAI vs the recovered Google Books text layer - RELIABILITY GATE")
    print("(the two readings are NOT independent; agreement is not evidence)\n")
    print(f"  pages compared        {covered}")
    print(f"  DocAI tokens          {tot_tok:,}")
    print(f"  divergent spans       {len(rows):,}"
          f"   ({100.0 * len(rows) / max(tot_tok, 1):.2f}% of tokens)")
    if per_page:
        worst = sorted(per_page, key=lambda x: -x["rate_pct"])[:5]
        print("\n  pages where the two Google readings split most")
        for w in worst:
            print(f"    page {w['page']:>3}   {w['rate_pct']:5.2f}%   "
                  f"{w['divergences']} of {w['docai_tokens']} tokens")
    if rows:
        print(f"\n  first {min(args.show, len(rows))} divergences (docai | layer)")
        for r in rows[:args.show]:
            print(f"    p{r['page']:<4}{r['kind']:<8} {r['docai'][:26]:<26} | {r['layer'][:26]}")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump({
                "what_this_is": "Positions where two GOOGLE OCR systems reading the "
                                "SAME scan disagree. A triage surface, not a queue: "
                                "the two are not independent (Lesson 23/24), so "
                                "agreement carries no information and nothing here "
                                "may be applied as a correction.",
                "pages_compared": covered,
                "docai_tokens": tot_tok,
                "divergent_spans": len(rows),
                "per_page": per_page,
                "divergences": rows,
            }, fh, ensure_ascii=False, indent=1)
            fh.flush()
            os.fsync(fh.fileno())
        print(f"\n  wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
