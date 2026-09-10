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


PARA = re.compile(r"<w:p[ >].*?</w:p>", re.S)
RUN = re.compile(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>|<w:footnoteReference w:id=\"(-?\d+)\"\s*/>",
                 re.S)


def token_stream(docx_dir):
    """The whole witness as (tokens, [(token index, note text)]).

    EXTRACTED HERE RATHER THAN INHERITED. The first pass at this lived in a
    scratch script that deleted the whole U+0591-U+05C7 block while tokenising,
    which takes the MAQAF with it - so `כל־תפש` arrived as the single token
    `כלתפש`. That is invisible until something checks the text against a verse:
    `tools/validate_quotations.py` then reports the glued form as a word absent
    from the verse, and hundreds of correct quotations look like OCR errors.
    Splitting is left to corpus_io.hebrew_words downstream; what matters here is
    that the maqaf SURVIVES into the token, so the information still exists.
    """
    tokens, notes = [], []
    for path in sorted(glob.glob(os.path.join(docx_dir, "*.docx"))):
        zf = zipfile.ZipFile(path)
        by_id = footnote_texts(zf)
        body = zf.read("word/document.xml").decode("utf-8")
        for para in PARA.findall(body):
            # Build the paragraph text first and remember each marker's CHARACTER
            # offset. Flushing the buffer at the marker instead would split the
            # token the marker sits inside - `אֶגְלֵי־טָל` + marker + `.` becomes
            # two tokens where the text has one - and every downstream count then
            # disagrees with the entry texts by an amount that varies per entry.
            buf, marks = "", []
            for m in RUN.finditer(para):
                if m.group(1) is not None:
                    buf += html.unescape(m.group(1))
                else:
                    marks.append((len(buf), by_id.get(m.group(2), "")))
            base = len(tokens)
            for off, text in marks:
                notes.append((base + len(buf[:off].split()), text))
            tokens.extend(buf.split())
    return tokens, notes


def segment(tokens, notes, entry_texts):
    """Cut the global stream into entries, using the known entry texts in order.

    MATCHED AS A SUBSEQUENCE, not as a contiguous block. The .docx carries
    material the entry list does not: a table of contents, section heads, and a
    bracketed headword marker before each entry (`[שׁום]`), 2,021 of them. A
    contiguous match aborts on the first one; a subsequence walk steps over them
    and counts them, so "text belonging to no entry" stays a reported number.

    An anchor landing on a skipped token belongs to the entry token that follows
    it - a footnote on the headword marker annotates the entry it opens.

    Order is still enforced: each entry is found after the previous one ends, so
    the anchors cannot be assigned to the wrong entry however much is skipped.
    """
    out, cursor, note_i, skipped = {}, 0, 0, 0
    for root, text in entry_texts.items():
        want = text.split()
        if not want:
            continue
        lo = None
        for i in range(cursor, len(tokens)):
            if tokens[i] == want[0]:
                lo = i
                break
        if lo is None:
            raise SystemExit(
                f"  ABORT: entry {root!r} was not found after offset {cursor}. "
                f"Expected to start {want[:6]}. The entry list and the .docx set "
                f"must be the same export.")
        skipped += lo - cursor      # material BETWEEN entries counts too
        # walk both, letting the stream carry extras
        pos = {}          # entry-token index -> stream index
        i, k = lo, 0
        while i < len(tokens) and k < len(want):
            if tokens[i] == want[k]:
                pos[k] = i
                k += 1
            else:
                skipped += 1
            i += 1
        if k < len(want):
            raise SystemExit(
                f"  ABORT: entry {root!r} ran off the end of the stream with "
                f"{len(want) - k} tokens unmatched.")
        hi = i
        anchors, texts = [], []
        stream_to_entry = {v: kk for kk, v in pos.items()}
        while note_i < len(notes) and notes[note_i][0] <= hi:
            si = notes[note_i][0]
            if si >= lo:
                e = stream_to_entry.get(si)
                if e is None:            # landed on a skipped token
                    e = next((stream_to_entry[x] for x in sorted(stream_to_entry)
                              if x >= si), len(want))
                anchors.append(e)
                texts.append(notes[note_i][1])
            note_i += 1
        out[root] = {"tokens": want, "anchors": anchors, "notes": texts}
        cursor = hi
    print(f"  tokens outside any entry {skipped:,}  (front matter, section heads, "
          f"headword markers)")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--docx-dir", required=True)
    ap.add_argument("--entries", required=True,
                    help="{root: text} for the witness, in document order")
    ap.add_argument("--out", required=True)
    ap.add_argument("--show", type=int, default=6)
    args = ap.parse_args()

    tokens, notes = token_stream(os.path.expanduser(args.docx_dir))
    with open(os.path.expanduser(args.entries), encoding="utf-8") as fh:
        entry_texts = json.load(fh)

    print(f"  tokens in the .docx set {len(tokens):,}")
    print(f"  footnotes               {len(notes):,}")
    leaked = [n for _p, n in notes if "<" in n]
    print(f"  notes containing markup {len(leaked):,}   (must be 0; see the <w:tab/> trap)")
    print(f"  maqaf preserved         {sum(t.count(chr(0x5be)) for t in tokens):,}")

    merged = segment(tokens, notes, entry_texts)
    placed = sum(len(v["anchors"]) for v in merged.values())
    print(f"  entries                 {len(merged):,}")
    print(f"  anchors placed          {placed:,}")
    if placed != len(notes):
        print(f"  footnotes outside every entry span: {len(notes) - placed}")

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
