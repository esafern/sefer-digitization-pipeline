#!/usr/bin/env python3
"""
tools/anchors_from_inline_citations.py

Turn a text whose citations are INLINE into the same anchored shape the .docx
footnotes produce, so one adjudicator serves both.

WHY IT IS NEEDED. `tools/extract_witness_footnotes.py` recovers the apparatus
from Word footnotes, and those anchors index the .docx token stream - which is
Sefaria's UNCORRECTED text. Their manually corrected entries are a different
text of the same entry: where the .docx reads `נורי`, the corrected layer reads
`פרי`. Locating a corrected reading inside the uncorrected token stream is
therefore not reliable, and a citation looked up through the wrong stream can
point at the wrong quotation.

The corrected export does not need that hop. It carries each citation inline at
the position the footnote marker occupied - `... הָרִמֹּנִים (שה"ש ו, יא) ואלו
היה ...` - so the text anchors itself. This reads those parentheticals out,
records the word position each sat at, and emits `{root: {tokens, anchors,
notes}}`, identical to the footnote extractor's output.

ONLY PARENTHETICALS THAT PARSE AS A CITATION ARE TAKEN. Bacher uses parentheses
for other things too, and a bracket of ordinary prose removed as though it were
apparatus would silently shorten the text it is meant to describe. Anything the
citation parser rejects stays in the text as words, and the run reports how many
were kept so the split is visible rather than assumed.

Usage:
  python3 tools/anchors_from_inline_citations.py \
      --sample ~/work/hashorashim/ibn_janah_sample.json --which corrected_sample \
      --out ~/work/hashorashim/gold_footnotes.json --text-out /tmp/ibnj_gold.json
"""

import argparse
import json
import os
import re
import sys
import unicodedata

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "pipeline"))
sys.path.insert(0, _HERE)
import corpus_io as cio  # noqa: E402
from adjudicate_against_verse import parse_citation  # noqa: E402

TAG = re.compile(r"<[^>]+>")
PAREN = re.compile(r"\([^)]*\)")


def split_citations(text):
    """(text without citations, [(word position, citation)]).

    The position is counted in WORDS of the emitted text, so it means the same
    thing as a footnote anchor: the citation belongs to what precedes it.
    """
    body, notes, last, running = [], [], 0, None
    kept = 0
    for m in PAREN.finditer(text):
        ref, running = parse_citation(m.group(0), running)
        if not ref:
            kept += 1
            continue
        body.append(text[last:m.start()])
        last = m.end()
        notes.append((len(cio.hebrew_words(" ".join(body))), m.group(0)))
    body.append(text[last:])
    return re.sub(r"\s+", " ", " ".join(body)).strip(), notes, kept


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sample", required=True)
    ap.add_argument("--which", default="corrected_sample")
    ap.add_argument("--out", required=True, help="anchored shape, for the adjudicator")
    ap.add_argument("--text-out", help="citation-free text, for the dispute builder")
    args = ap.parse_args()

    with open(os.path.expanduser(args.sample), encoding="utf-8") as fh:
        sample = json.load(fh)
    entries = sample[args.which]

    anchored, plain, kept_total = {}, {}, 0
    for e in entries:
        head = unicodedata.normalize("NFKC", e["headword"])
        raw = re.sub(r"\s+", " ", TAG.sub(" ", unicodedata.normalize("NFKC", e["html"])))
        body, notes, kept = split_citations(raw)
        kept_total += kept
        plain[head] = body
        anchored[head] = {"tokens": body.split(),
                          "anchors": [p for p, _n in notes],
                          "notes": [n for _p, n in notes]}

    n_notes = sum(len(v["anchors"]) for v in anchored.values())
    print(f"  entries                      {len(anchored)}")
    print(f"  citations recovered          {n_notes:,}")
    print(f"  parentheticals kept as text  {kept_total:,}  (did not parse as a citation)")

    out = os.path.expanduser(args.out)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(anchored, fh, ensure_ascii=False)
        fh.flush()
        os.fsync(fh.fileno())
    print(f"  wrote                        {out}")
    if args.text_out:
        t = os.path.expanduser(args.text_out)
        with open(t, "w", encoding="utf-8") as fh:
            json.dump(plain, fh, ensure_ascii=False, indent=1)
            fh.flush()
            os.fsync(fh.fileno())
        print(f"  wrote                        {t}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
