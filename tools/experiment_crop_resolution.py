#!/usr/bin/env python3
"""
tools/experiment_crop_resolution.py

Does giving the vision adjudicator the scan's FULL resolution change its answer?

THE QUESTION. `vision_adjudication_common.crop_pdf_bounding_box` defaults to
`dpi=300` and every caller uses the default. The Google Books scan of Sefer
HaShorashim renders its native 3528 px at exactly 600 dpi, so every adjudication
this project has run has judged a half-resolution crop - a quarter of the
available pixels - including the p138 `ונוש`/`וגוש` call it got wrong while
reporting 0.95 confidence. The distinction it is being asked to make, a gimel's
leg against a nun, lives in exactly the fine strokes that halving throws away.

WHY IT IS AN EXPERIMENT AND NOT A FIX. Rendered side by side, the gimel in
`לגדלתם` (p60) is legible at BOTH resolutions to a human eye. So resolution may
not be the binding constraint at all, and raising it might change nothing. This
runs it against real ground truth instead of assuming either way.

THE DESIGN. Paired and blind. Every case is a position where our OCR read nun
and Sefaria's manually reviewed text reads gimel, so the correct answer is known
and is always the witness reading. Each case is put to the model twice, at 300
and at 600 dpi, with the SAME A/B assignment both times - the only variable is
the crop. A/B order is randomized per case from a fixed seed so the model cannot
profit from a positional habit, and so the two runs stay comparable.

WHAT IT CANNOT SETTLE. The ground truth is Sefaria's reviewed text, which is
very good but not infallible - this project has already found four positions
where the cited verse contradicts it. A tie or a small difference here is not
evidence that resolution does not matter, only that it does not matter for this
error class on this scan.

Usage:
  GEMINI_API_KEY=... SEFER_CORPUS_ROOT=~/work/hashorashim \
    python3 tools/experiment_crop_resolution.py --cases /tmp/ng_located.json \
      --dpi 300 600 --out ~/work/hashorashim/crop_resolution_experiment.json
"""

import argparse
import hashlib
import json
import os
import random
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "pipeline"))
import fitz  # noqa: E402
import corpus_io as cio  # noqa: E402
import vision_adjudication_common as vac  # noqa: E402

PROMPT = """You are reading a photograph of a page from a Hebrew book printed in
Berlin in 1896, in square Hebrew type.

The boxed region contains one Hebrew word. Two transcriptions are proposed:

Option A: {a}
Option B: {b}

Look at the letter shapes in the image and decide which transcription matches
the ink. The two options differ in a single letter. Judge only what you can see;
do not reason from what would make sense in Hebrew.

Reply with JSON only:
{{"selected_option": "A" or "B" or "UNCERTAIN",
  "transcription_found": "<what you actually read>",
  "confidence": <0.0-1.0>,
  "reasoning": "<one sentence about the letter shapes>"}}"""

TABLE = "crop_resolution_experiment"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cases", required=True)
    ap.add_argument("--dpi", type=int, nargs="+", default=[300, 600])
    ap.add_argument("--limit", type=int)
    ap.add_argument("--seed", type=int, default=17)
    ap.add_argument("--out")
    args = ap.parse_args()

    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise SystemExit("GEMINI_API_KEY is not set")
    with open(os.path.expanduser(args.cases), encoding="utf-8") as fh:
        cases = json.load(fh)
    if args.limit:
        cases = cases[:args.limit]

    doc = fitz.open(cio.SCAN_PDF_PATH)
    client = vac.make_client(key)
    prompt_hash = hashlib.sha256(PROMPT.encode("utf-8")).hexdigest()[:16]
    db = os.path.join(os.path.dirname(cio.LEXICON_PATH), "adjudication_cache.db")
    vac.init_cache_table(db, TABLE, prompt_hash)

    rng = random.Random(args.seed)
    rows = []
    for i, c in enumerate(cases, 1):
        ours, theirs = c["corpus"], c["witness_reading"]
        # SAME assignment for both resolutions - the crop is the only variable.
        ours_is_a = rng.random() < 0.5
        a, b = (ours, theirs) if ours_is_a else (theirs, ours)
        prompt = PROMPT.format(a=a, b=b)
        rec = {"page": c.get("page_used", c["page"]), "root": c.get("root"),
               "ours": ours, "truth": theirs, "ours_is_a": ours_is_a, "by_dpi": {}}
        for dpi in args.dpi:
            crop = vac.crop_pdf_bounding_box(doc, int(rec["page"]), c["bbox"],
                                             padding=0.02, dpi=dpi)
            ctx = f"dpi={dpi}"
            get = lambda: vac.get_cached_decision(db, TABLE, prompt_hash, crop, a, b, ctx)
            put = lambda text, model: vac.put_cached_decision(
                db, TABLE, prompt_hash, crop, a, b, ctx, text, model)
            print(f"[{i}/{len(cases)}] p{rec['page']} dpi={dpi} {ours} vs {theirs}")
            try:
                raw = vac.adjudicate_with_retry(client, crop, prompt, get, put)
                d = vac.parse_decision_lenient(raw)
                sel = vac.normalize_selected_option(d.get("selected_option"))
            except Exception as exc:                      # noqa: BLE001
                print(f"  -> failed: {exc}")
                sel, d = None, {}
            chose_truth = (sel == ("B" if ours_is_a else "A")) if sel in ("A", "B") else None
            rec["by_dpi"][str(dpi)] = {
                "selected": sel, "correct": chose_truth,
                "confidence": d.get("confidence"),
                "read": d.get("transcription_found"),
                "reasoning": (d.get("reasoning") or "")[:200]}
        rows.append(rec)

    print("\n" + "=" * 60)
    print(f"  cases: {len(rows)}   ground truth is always the reviewed reading\n")
    for dpi in args.dpi:
        k = str(dpi)
        got = [r for r in rows if r["by_dpi"].get(k, {}).get("correct") is not None]
        ok = sum(1 for r in got if r["by_dpi"][k]["correct"])
        print(f"  dpi {dpi:>4}: correct {ok:3d}/{len(got):3d}  "
              f"({100.0 * ok / max(1, len(got)):5.1f}%)")
    if len(args.dpi) == 2:
        lo, hi = (str(d) for d in args.dpi)
        both = [r for r in rows
                if r["by_dpi"].get(lo, {}).get("correct") is not None
                and r["by_dpi"].get(hi, {}).get("correct") is not None]
        gain = sum(1 for r in both if not r["by_dpi"][lo]["correct"] and r["by_dpi"][hi]["correct"])
        loss = sum(1 for r in both if r["by_dpi"][lo]["correct"] and not r["by_dpi"][hi]["correct"])
        print(f"\n  paired on {len(both)} cases:")
        print(f"    wrong at {lo} -> right at {hi}:  {gain}")
        print(f"    right at {lo} -> wrong at {hi}:  {loss}")
        print(f"    net: {gain - loss:+d}")
    if args.out:
        with open(os.path.expanduser(args.out), "w", encoding="utf-8") as fh:
            json.dump({"prompt": PROMPT, "rows": rows}, fh, ensure_ascii=False, indent=1)
            fh.flush()
            os.fsync(fh.fileno())
        print(f"\n  wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
