#!/usr/bin/env python3
"""
tools/extract_witness_footnotes.py

Pull Bacher's apparatus out of the witness .docx set as TEXT, positioned.

WHAT THIS ADDS OVER THE ANCHOR EXTRACTION. The witness (Sefaria's digitization
of Ibn Janah, ed. Bacher) carries the apparatus as real Word footnotes: 20,450
of them, each anchored at a position in the token stream. An earlier pass took
the POSITIONS only, which was enough to answer "do the two datasets merge"
(98.8% land within one word). It threw the note TEXT away, and the note text is
where the citations live - `(שה"ש ו, יא)`, `(איוב ז, ה)`. Those citations are
the only external ground truth this book has, so they are worth more than the
positions.

THE `<w:tab/>` TRAP. The obvious regex for a Word text run, `<w:t[^>]*>`, also
matches the self-closing `<w:tab/>` element - `<w:t` + `ab/` + `>`. When it does,
the scan for the closing `</w:t>` runs past the end of the run and swallows raw
XML into the note text. This was not hypothetical: it corrupted the second and
third notes in the very first file, and the corruption is silent because a note
that contains markup still looks like a populated field. The pattern below
requires whitespace or `>` after `w:t`, and `--verify` counts notes that still
contain a `<` as a check that it held.

ORDER IS THE JOIN. Notes come out in document order, and the anchor list they
are being merged onto was built in the same single pass over the same files in
the same sorted order. That is what licenses a positional zip, and it is checked
rather than assumed: the run aborts unless the two counts match exactly.

Usage:
  python3 tools/extract_witness_footnotes.py \
      --docx-dir ~/work/hashorashim/IbnJanachShorashim \
      --anchors /tmp/ibnj_anchored.json --out ~/work/hashorashim/witness_footnotes.json
"""

import argparse
import glob
import html
import json
import os
import re
import sys
import zipfile

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "pipeline"))
import corpus_io as cio  # noqa: E402

# `<w:t>` or `<w:t xml:space="preserve">` - but NOT `<w:tab/>`. See the docstring.
W_T = re.compile(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>", re.S)
FOOTNOTE = re.compile(r'<w:footnote[^>]*w:id="(-?\d+)"[^>]*>(.*?)</w:footnote>', re.S)
FN_REF = re.compile(r'<w:footnoteReference w:id="(-?\d+)"\s*/>')


def footnote_texts(zf):
    """{footnote id: plain text} for one .docx."""
    xml = zf.read("word/footnotes.xml").decode("utf-8")
    out = {}
    for m in FOOTNOTE.finditer(xml):
        body = "".join(html.unescape(t) for t in W_T.findall(m.group(2)))
        out[m.group(1)] = re.sub(r"\s+", " ", body).strip()
    return out


def ordered_notes(docx_dir):
    """Every footnote's text, in document order across the sorted file set."""
    notes = []
    for path in sorted(glob.glob(os.path.join(docx_dir, "*.docx"))):
        zf = zipfile.ZipFile(path)
        by_id = footnote_texts(zf)
        body = zf.read("word/document.xml").decode("utf-8")
        for m in FN_REF.finditer(body):
            notes.append({"file": os.path.basename(path), "id": m.group(1),
                          "text": by_id.get(m.group(1), "")})
    return notes


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--docx-dir", required=True)
    ap.add_argument("--anchors", required=True,
                    help="{root: {tokens, anchors}} from the anchor pass")
    ap.add_argument("--out", required=True)
    ap.add_argument("--show", type=int, default=6)
    args = ap.parse_args()

    notes = ordered_notes(os.path.expanduser(args.docx_dir))
    with open(os.path.expanduser(args.anchors), encoding="utf-8") as fh:
        anchored = json.load(fh)
    total_anchors = sum(len(v["anchors"]) for v in anchored.values())

    print(f"  footnotes in docx set   {len(notes):,}")
    print(f"  anchors in anchor file  {total_anchors:,}")
    if len(notes) != total_anchors:
        raise SystemExit("  ABORT: counts differ, so a positional zip would be "
                         "silently off-by-N. Re-run the anchor pass over the "
                         "same file set before merging.")

    leaked = [n for n in notes if "<" in n["text"]]
    empty = [n for n in notes if not n["text"]]
    print(f"  notes containing markup {len(leaked):,}   (must be 0; see the <w:tab/> trap)")
    print(f"  empty notes             {len(empty):,}")

    merged, i = {}, 0
    for root, v in anchored.items():
        n = len(v["anchors"])
        merged[root] = {"tokens": v["tokens"], "anchors": v["anchors"],
                        "notes": [notes[j]["text"] for j in range(i, i + n)]}
        i += n

    out = os.path.expanduser(args.out)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(merged, fh, ensure_ascii=False)
        fh.flush()
        os.fsync(fh.fileno())
    print(f"  wrote                   {out}")

    for root in list(merged)[:args.show]:
        v = merged[root]
        if not v["notes"]:
            continue
        pos, note = v["anchors"][0], v["notes"][0]
        before = " ".join(v["tokens"][max(0, pos - 4):pos])
        print(f"    {root:<5} ...{before}  ->  {note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
