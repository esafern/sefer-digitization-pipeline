#!/usr/bin/env python3
"""
tools/build_witness_review_queue.py

Turn `witness_disputes.json` into the queue file the review dashboard reads.

WHY THE DASHBOARD IS EMPTY FOR THIS BOOK. `review_server.py` builds its flag
overlay from `review_queue_part1.json`, which comes from the DocAI-vs-corpus
diff - and for Sefer HaShorashim that diff is vacuous (item `0ER`): the corpus
was BUILT from DocAI, so it cannot disagree with itself. The dashboard would
open, render the scan, highlight nothing, and look like a clean book.

The server does have a second route - `reconstruction_witness_queue.json`,
served as `opcode: "witness"` - and that is what this writes. It was built for
Tesseract-vs-DocAI on Yad Malachi's reconstructed pages, but nothing in the
shape is Tesseract-specific.

WHAT THIS FILE ALONE WILL NOT FIX, AND WHY IT MATTERS. Two things downstream are
calibrated on the OTHER witness and are wrong for this one:

  * `review_frontend/app.js` names the witness "Tesseract" in four places and
    tells the reviewer "Tesseract was measured correct in only 3.8%". Sefaria's
    transcription is correct in 99.2% of words (item `0FK`). Showing their
    readings under that label and that warning would push a reviewer to dismiss
    corrections that are almost always right.
  * `review_data.load_witness_queue` filters to items where the VISION pass did
    not side with the corpus. That cut was calibrated on a witness that is right
    3.8% of the time, and item `0FQ` measured the vision pass at 18% on this
    book's dominant error class - worse than guessing. Applying it here would
    hide most of the real corrections behind a signal we know is broken.

Both need a per-witness label and a per-witness cut. This tool writes honest
data and records the witness's own name and measured reliability IN the file so
that a fixed frontend has something to read.

Usage:
  SEFER_CORPUS_ROOT=~/work/hashorashim python3 tools/build_witness_review_queue.py \
      --disputes ~/work/hashorashim/witness_disputes.json \
      --witness-name "Sefaria (Ibn Janah digitization)" --out-name reconstruction_witness_queue.json
"""

import argparse
import json
import os
import sys
import unicodedata

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "pipeline"))
import corpus_io as cio  # noqa: E402


def page_tokens(page):
    path = os.path.join(cio.DOCAI_DIR, f"page_{page}.json")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--disputes", required=True)
    ap.add_argument("--witness-name", required=True)
    ap.add_argument("--witness-accuracy", type=float, default=None,
                    help="the witness's measured word accuracy, 0-1, for the UI note")
    ap.add_argument("--out-name", default="reconstruction_witness_queue.json")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    with open(os.path.expanduser(args.disputes), encoding="utf-8") as fh:
        raw = json.load(fh)
    disputes = raw["disputes"] if isinstance(raw, dict) else raw

    cache, out = {}, []
    located = ambiguous = missing = 0
    for d in disputes:
        if d.get("editorial"):
            continue
        page = int(d["page"])
        if page not in cache:
            cache[page] = page_tokens(page)
        toks = cache[page]
        if not toks:
            missing += 1
            continue
        ours = cio.hebrew_letters_only(unicodedata.normalize("NFKC", d["corpus"]))
        if not ours:
            missing += 1
            continue
        hits = [i for i, t in enumerate(toks)
                if cio.hebrew_letters_only(t["text"]) == ours]
        if len(hits) != 1:
            # A repeated word cannot be anchored to ONE token, and the server
            # matches items by (klal_id, docai_token_index) alone - guessing here
            # would attach a reviewer's ruling to the wrong occurrence.
            ambiguous += 1 if hits else 0
            missing += 0 if hits else 1
            continue
        i = hits[0]
        t = toks[i]
        located += 1
        out.append({
            "klal_id": int(d["klal_id"]),
            "docai_token_index": i,
            "word_index": d.get("word_index"),
            "page": page,
            "bbox": {k: t[k] for k in ("x1", "y1", "x2", "y2")},
            "docai_reading": d["corpus"],
            "tesseract_reading": d["witness_reading"],
            "witness_reading": d["witness_reading"],
            "witness_name": args.witness_name,
            "tier": d.get("class"),
            "vision_selected": None,
            "vision_transcription": None,
            "vision_confidence": None,
        })

    doc = {
        "what_this_is": "Positions where the corpus and an independent witness "
                        "read differently, shaped for review_server.py's witness "
                        "route. Nothing here says which is right.",
        "witness_name": args.witness_name,
        "witness_word_accuracy": args.witness_accuracy,
        "vision_verdicts_present": False,
        "warning": "review_data.load_witness_queue filters by vision verdict, a "
                   "cut calibrated on a 3.8%-accurate witness. This witness is "
                   "far more accurate and the vision pass scores 18% on this "
                   "book's dominant error class (item 0FQ). Serving this file "
                   "through that filter would hide most real corrections.",
        "queue": out,
    }
    print(f"  disputes in            {len(disputes):,}")
    print(f"  anchored to one token  {located:,}")
    print(f"  word repeats on page   {ambiguous:,}  (cannot be anchored safely)")
    print(f"  no usable token        {missing:,}")
    dest = cio.repo_path(args.out_name)
    if args.dry_run:
        print(f"  would write            {dest}")
        return 0
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
        fh.flush()
        os.fsync(fh.fileno())
    print(f"  wrote                  {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
