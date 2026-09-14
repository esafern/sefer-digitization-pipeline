#!/usr/bin/env python3
"""
tools/snapshot_ocr_baseline.py

Freeze "our OCR": the corpus exactly as the OCR build produced it, word by word,
with each word's stable id, into `ocr_baseline_part1.json` in the corpus root
(item 0GC).

WHY. part1.json is the MASTER text: it starts as the OCR build and changes every
time a ruling is applied. The dashboard's "DocAI OCR reading" was read off
part1.json, so it would have turned into the corrected text the moment the first
ruling landed. Reviewer, 2026-09-13: "once corrections are applied, why would that
change what is seen under docai ocr reading? that should continue to show the
docai version - corrected master text should live elsewhere".

THE IDS ARE WHAT KEEP IT ADDRESSABLE. pipeline/word_identity.py gives every word
an id that survives both its index moving and its own text being corrected, so
"the OCR reading of the master word at index i" is the baseline word carrying
`id_at(master, i)` - whatever insertions and deletions happened in between.

REFUSES when the snapshot could not be what it claims to be:
  * the ledger holds an applied decision (an `apply_event`) - part1.json is then
    no longer pure OCR, and a snapshot would freeze corrections as "OCR";
  * word_identity.json does not give every word of part1.json an id;
  * a baseline already exists, unless --replace - which a fresh OCR rebuild
    legitimately needs, and nothing else does.

Usage:
  SEFER_CORPUS_ROOT=~/work/hashorashim python3 tools/snapshot_ocr_baseline.py
  ... --replace        # after rebuilding the corpus from new OCR
"""

import argparse
import datetime
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "pipeline"))
import corpus_io as cio  # noqa: E402
import review_decisions as rd  # noqa: E402
import word_identity as wid  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--replace", action="store_true",
                    help="overwrite an existing baseline (only after an OCR rebuild)")
    args = ap.parse_args()

    out = cio.repo_path(cio.OCR_BASELINE_NAME)
    if os.path.exists(out) and not args.replace:
        raise SystemExit(f"refusing: {out} exists. Pass --replace only if the corpus "
                         f"was just rebuilt from new OCR.")
    applied = [r for r in rd.all_records() if r.get("decision_type") == "apply_event"]
    if applied:
        raise SystemExit(f"refusing: the ledger holds {len(applied)} apply_event row(s), "
                         f"so part1.json is no longer the pure OCR build.")

    klalim = cio.load_klalim(cio.PART1_PATH)
    state = wid.load()
    entries, bad = {}, []
    for k in klalim:
        words = cio.words_of(k)
        ids = wid.ids_for(state, k["klal_id"])
        if len(ids) != len(words):
            bad.append((k["klal_id"], len(words), len(ids)))
            continue
        entries[str(k["klal_id"])] = {"root": k.get("gematria"), "words": words,
                                      "word_ids": ids}
    if bad:
        raise SystemExit(f"refusing: {len(bad)} entr(ies) have a word count that "
                         f"word_identity.json does not match, e.g. {bad[:3]}. Run "
                         f"tools/seed_word_identity.py --verify.")

    doc = {
        "what_this_is": "The corpus exactly as the OCR build produced it, before any "
                        "ruling was applied, each word with its stable id. 'Our OCR' "
                        "in the dashboard reads from here; part1.json is the master.",
        "made_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "scan_pdf": cio.book_field("scan_pdf"),
        "entries": entries,
    }
    tmp = out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, out)
    n_words = sum(len(e["words"]) for e in entries.values())
    print(f"  wrote {out}: {len(entries)} entries, {n_words:,} words")
    return 0


if __name__ == "__main__":
    sys.exit(main())
