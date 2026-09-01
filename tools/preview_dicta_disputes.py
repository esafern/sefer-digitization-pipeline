#!/usr/bin/env python3
"""
tools/preview_dicta_disputes.py

Show what a NEW witness would add to the review queue, as a markdown file of
dashboard links — WITHOUT wiring it into the pipeline or writing a single
byte into `consensus_disputes_part1.json`.

Written 2026-08-31 for the Dicta Rashi-edition witness (PROJECT-STATUS.md items
0N/0P). Deliberately a preview, not an integration: a witness earns its way into
stage 4a by having a human look at what it would actually say, and this is the
artifact they look at. Re-run it as more of the edition is OCR'd; the output is
regenerated wholesale, never appended to.

It reuses `synthesize_multi_witness`'s own loaders and vote rules rather than
re-deriving them, so a preview cannot drift from what the real synthesizer
would do — the standing shared-library rule, and the reason the numbers here
can be quoted.

Two categories, and the difference matters:

  * NEW      - no consensus exists at this position today; the candidate
               witness supplies the second engine that creates one. This is
               what the witness ADDS to a reviewer's queue.
  * JOINS    - a consensus already exists and the candidate agrees with it.
               This is corroboration (Lesson 9), and it changes no queue depth.

A position where the candidate differs ALONE is neither, and is deliberately
not listed: one witness disagreeing is not a dispute, and for a cross-edition
witness it is usually an edition variant rather than a misread.

Usage:
  python3 tools/preview_dicta_disputes.py \
      --witness dicta_output/dicta_jerusalem_p0022-p0050.txt \
      --label dicta --klalim 2-62 --out DICTA-NEW-DISPUTES.md
"""

import argparse
import collections
import difflib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "pipeline"))

import corpus_io as cio
import synthesize_multi_witness as smw

# The PATH form of the dashboard deep link, not the `#klal=N&word=M` hash form:
# review_frontend/app.js uses this one for anything copied out, because `&`
# gets truncated when a link is pasted into a terminal or a chat window. The
# server 302s it to the hash route (review_server.ROUTE_SHARE).
DEFAULT_BASE = "http://127.0.0.1:8420"

# Hebrew inside a Markdown file sits in an LTR-base document, so a bare Hebrew
# run gets reordered against the Latin, digits and punctuation around it and
# reads backwards. The repo's own answer everywhere it renders Hebrew beside
# Latin is `direction: rtl; unicode-bidi: isolate` (review_frontend/app.css,
# tools/render_report.py). Markdown has no stylesheet, so use the character
# form of exactly that: RIGHT-TO-LEFT ISOLATE ... POP DIRECTIONAL ISOLATE.
# Isolate rather than embed (RLE/PDF): an isolate also stops the Hebrew from
# reordering the URL and the digits sharing its table row.
RLI, PDI = "\u2067", "\u2069"
HEBREW_RE = re.compile(r"[\u0590-\u05ff]")


def rtl(text, isolate=True):
    """Wrap a Hebrew run so a BIDI-AWARE renderer sets it right-to-left and it
    cannot disturb its neighbours. Empty stays empty.

    `isolate=False` in visual mode: there, the reordering has already been
    baked into the characters and an isolate would only confuse a reader that
    DOES implement bidi."""
    text = (text or "").strip()
    return f"{RLI}{text}{PDI}" if (text and isolate) else text


def to_visual(lines):
    """Bake the bidi reordering into the bytes, for a renderer that does none.

    Measured 2026-08-31: `glow` emits Hebrew byte-for-byte as it reads it
    (KAF,VAV,TAV,BET in, KAF,VAV,TAV,BET out), so the terminal is expected to
    run the Unicode bidi algorithm and the ones in use here do not. Logical
    order therefore displays backwards, and RLI/PDI isolates are inert because
    nothing reads them. The only remaining lever is to reorder the characters
    themselves.

    Uses `python-bidi`'s implementation of the real algorithm rather than a
    hand-rolled reverse: naive reversal gets gershayim, mixed digits and
    embedded Latin wrong, and this text is full of `דף ג' ב'`. Base direction
    stays L, so URLs and ASCII are untouched (asserted in the tests below).

    The cost, and it is the reason this is not the default: text from a visual
    file is REVERSED if copied back into anything that expects logical order.
    """
    from bidi.algorithm import get_display
    return [get_display(l, base_dir="L") if HEBREW_RE.search(l) else l
            for l in lines]


def witness_by_klal(path, part1):
    """{klal_id: [raw words]} from a page-oriented OCR dump of ANOTHER EDITION.

    Segmentation by content-anchoring: each witness token inherits the klal of
    the corpus token it aligns to, unaligned tokens join the preceding klal.
    This decides BOUNDARIES only - every reading stays the witness's own word,
    and align_witness re-aligns inside each klal afterwards, so nothing here
    can make the witness agree with the corpus that would not have anyway.

    A same-edition witness with `=== KLAL N ===` headers does not need this;
    load it with smw.load_baseline() instead.
    """
    txt = re.sub(r"^===\s*עמוד.*$", "", open(path, encoding="utf-8").read(), flags=re.M)
    raw = [w for w in txt.split() if cio.hebrew_letters_only(w)]
    norm = [cio.hebrew_letters_only(w) for w in raw]

    ctoks, owner = [], []
    for k in sorted(part1, key=lambda x: x["klal_id"]):
        for w in k["clean_text"].split():
            n = cio.hebrew_letters_only(w)
            if n:
                ctoks.append(n)
                owner.append(k["klal_id"])

    sm = difflib.SequenceMatcher(None, ctoks, norm, autojunk=False)
    assign = {}
    for b in sm.get_matching_blocks():
        for i in range(b.size):
            assign[b.b + i] = owner[b.a + i]

    out, cur = collections.defaultdict(list), None
    for j, w in enumerate(raw):
        cur = assign.get(j, cur)
        if cur is not None:
            out[cur].append(w)
    return dict(out)


def consensus_of(readings, stored_norm):
    """The synthesizer's own rule: >= 2 DISTINCT engines agreeing on the same
    alternative reading. Two engines each reading something different is a
    three-way split and a human-review case, not a consensus."""
    by = {}
    for engine, txt in readings.items():
        by.setdefault(cio.hebrew_letters_only(txt), []).append(engine)
    for norm, engines in by.items():
        if len(engines) >= 2 and norm != stored_norm:
            return norm, sorted(engines), readings[engines[0]]
    return None


def collect(part1, klal_lo, klal_hi, witness, label):
    verified = cio.load_json(os.path.join(REPO, "corrections_verified_part1.json"), []) or []
    vlm_a = smw.load_baseline(smw.VLM_A_PATH)
    vlm_b = smw.load_baseline(smw.VLM_B_PATH)
    surya = smw.load_baseline(smw.SURYA_PATH)
    decided = smw.active_human_decisions()
    docai = smw.docai_verdicts(
        verified, {k["klal_id"]: k["clean_text"].split() for k in part1})

    new, joins = [], []
    covered = voted = agreed = 0

    for k in sorted(part1, key=lambda x: x["klal_id"]):
        kid = k["klal_id"]
        if not (klal_lo <= kid <= klal_hi):
            continue
        words = k["clean_text"].split()
        covered += len(words)

        s_al = cio.align_witness(words, surya.get(kid) or []) if surya.get(kid) else {}
        v_al = (smw.vlm_verdicts(words, vlm_a.get(kid) or [], vlm_b.get(kid) or [])
                if (vlm_a.get(kid) and vlm_b.get(kid)) else {})
        w_al = cio.align_witness(words, witness.get(kid) or []) if witness.get(kid) else {}
        voted += len(w_al)
        agreed += sum(1 for v in w_al.values() if v[1] == "agrees")

        for wi, stored in enumerate(words):
            stored_norm = cio.hebrew_letters_only(stored)
            readings = {}
            if docai.get((kid, wi)) is not None:
                readings["docai"] = docai[(kid, wi)]
            if wi in v_al and v_al[wi][1] == "differs":
                readings["vlm"] = v_al[wi][0]
            if wi in s_al and s_al[wi][1] == "differs":
                readings["surya"] = s_al[wi][0]
            if wi in w_al and w_al[wi][1] == "differs":
                readings[label] = w_al[wi][0]

            without = consensus_of({e: t for e, t in readings.items() if e != label},
                                   stored_norm)
            with_it = consensus_of(readings, stored_norm)
            if with_it is None:
                continue
            row = {
                "klal_id": kid, "word_index": wi, "stored": stored,
                "reading": with_it[2], "engines": with_it[1],
                "context": " ".join(words[max(0, wi - 5):wi + 6]),
                "decided": decided.get((kid, wi)),
                "title": (k.get("title") or "").strip(),
            }
            if without is None:
                new.append(row)
            elif label in with_it[1]:
                joins.append(row)

    return new, joins, {"corpus_words": covered, "witness_votes": voted,
                        "witness_agrees": agreed}


def write_md(path, new, joins, stats, label, klal_lo, klal_hi, base, witness_file,
              hebrew="visual"):
    """Emit the report.

    **No URL ever shares a line with anything else, and there are no tables.**
    Measured 2026-08-31 with `glow -w 80`, which is how this file actually gets
    read: a URL in a table cell is wrapped MID-STRING
    (`.../klal/5/word/8` + `6` on the next line), which destroys both the link
    and copy-paste, and the same narrow cells chop the Hebrew into vertical
    fragments (`\u2067\u05d5\u05db\u05db` / `\u05ea\u05d5\u05d1` / `\u05d5\u05ea\u2069`). A URL alone on its own line
    survives at any width down to ~40 columns. That is the whole layout rule
    here; readability came second to it deliberately."""
    pct = (stats["witness_agrees"] / stats["witness_votes"] * 100
           if stats["witness_votes"] else 0.0)
    iso = (hebrew == "logical")
    L = []
    L.append(f"# New disputes a `{label}` witness would add")
    L.append("")
    if hebrew == "visual":
        L.append("> **Hebrew below is in VISUAL order**, reordered so it reads "
                 "correctly in a terminal renderer that does no bidi (`glow`). "
                 "**Do not copy Hebrew out of this file** — it will paste "
                 "reversed. Regenerate with `--hebrew logical` for a "
                 "copy-safe version.")
        L.append("")
    L.append(f"Preview only — **nothing has been written into the pipeline.** "
             f"`{os.path.basename(witness_file)}` scored against `part1.json` "
             f"klalim {klal_lo}–{klal_hi} under the live stage-4a consensus rules.")
    L.append("")
    L.append("| | |")
    L.append("|---|---:|")
    L.append(f"| corpus words in scope | {stats['corpus_words']:,} |")
    L.append(f"| positions `{label}` votes at | {stats['witness_votes']:,} |")
    L.append(f"| …agreeing with the corpus | {stats['witness_agrees']:,} ({pct:.1f}%) |")
    L.append(f"| **new disputes it would create** | **{len(new)}** |")
    L.append(f"| existing disputes it corroborates | {len(joins)} |")
    L.append("")
    L.append("Links open the review dashboard "
             f"(`python3 pipeline/review_server.py`, {base}). "
             "A position where only this witness differs is **not** listed — one "
             "engine disagreeing is not a dispute, and across editions it is "
             "usually a textual variant rather than a misread.")
    L.append("")
    L.append(f"## New disputes ({len(new)})")
    L.append("")
    if not new:
        L.append("_None._")
    for r in new:
        flag = "  ⚠️ **a reviewer already ruled here**" if r["decided"] else ""
        L.append(f"### klal {r['klal_id']} · word {r['word_index']}{flag}")
        L.append("")
        L.append(f"- corpus reads **{rtl(r['stored'], iso)}** → "
                 f"`{'+'.join(r['engines'])}` read **{rtl(r['reading'], iso)}**")
        if r["decided"]:
            L.append(f"- reviewer's standing choice: **{rtl(r['decided'], iso)}**")
        L.append(f"- context: {rtl('…' + r['context'] + '…', iso)}")
        L.append(f"- {base}/klal/{r['klal_id']}/word/{r['word_index']}")
        L.append("")
    L.append(f"## Corroborated — already disputed, `{label}` agrees ({len(joins)})")
    L.append("")
    L.append("These change no queue depth; they are the independent second "
             "opinion Lesson 9 asks for.")
    L.append("")
    for r in joins:
        L.append(f"**klal {r['klal_id']} · word {r['word_index']}** — "
                 f"{rtl(r['stored'], iso)} → {rtl(r['reading'], iso)} "
                 f"(`{'+'.join(r['engines'])}`)")
        L.append("")
        L.append(f"{base}/klal/{r['klal_id']}/word/{r['word_index']}")
        L.append("")

    # Bare list last, in a fence: the form to copy out or pipe somewhere. A
    # fenced block is also the one context a renderer will not reflow.
    L.append("## Every link, bare")
    L.append("")
    L.append("```")
    for r in new + joins:
        L.append(f"{base}/klal/{r['klal_id']}/word/{r['word_index']}")
    L.append("```")
    L.append("")
    if hebrew == "visual":
        L = to_visual(L)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
        f.flush()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--witness", required=True, help="candidate OCR text file")
    ap.add_argument("--label", default="dicta", help="engine name used in the vote")
    ap.add_argument("--klalim", help="window LO-HI; omit to use the witness's own span")
    ap.add_argument("--out", default="DICTA-NEW-DISPUTES.md")
    ap.add_argument("--urls-out", default=None,
                    help="also write a bare newline-separated URL list here "
                         "(nothing but links - for piping, or for a reader that "
                         "mangles anything richer)")
    ap.add_argument("--base-url", default=DEFAULT_BASE)
    ap.add_argument("--hebrew", choices=("visual", "logical"), default="visual",
                    help="visual (default): reorder Hebrew so it reads correctly "
                         "in a terminal that does no bidi, e.g. glow - but do not "
                         "copy Hebrew out of it. logical: canonical order, correct "
                         "in any bidi-aware reader and safe to copy.")
    args = ap.parse_args()

    part1 = cio.load_part1_sorted()
    witness = witness_by_klal(args.witness, part1)
    if args.klalim:
        m = re.match(r"^\s*(\d+)\s*-\s*(\d+)\s*$", args.klalim)
        if not m:
            ap.error("--klalim wants LO-HI")
        lo, hi = int(m.group(1)), int(m.group(2))
    else:
        ks = sorted(witness)
        # Drop the first and last klal: a page-bounded dump almost always cuts
        # them mid-klal, and a partial klal scores as an error rather than one.
        lo, hi = (ks[1], ks[-2]) if len(ks) > 3 else (ks[0], ks[-1])

    new, joins, stats = collect(part1, lo, hi, witness, args.label)
    write_md(args.out, new, joins, stats, args.label, lo, hi,
             args.base_url.rstrip("/"), args.witness, hebrew=args.hebrew)

    print(f"klalim {lo}-{hi}: {len(new)} new disputes, {len(joins)} corroborated")
    print(f"  {args.label} votes at {stats['witness_votes']}/{stats['corpus_words']} "
          f"positions, agrees at {stats['witness_agrees']}")
    print(f"Wrote {args.out}")
    if args.urls_out:
        base = args.base_url.rstrip("/")
        with open(args.urls_out, "w", encoding="utf-8") as f:
            for r in new + joins:
                f.write(f"{base}/klal/{r['klal_id']}/word/{r['word_index']}\n")
            f.flush()
        print(f"Wrote {args.urls_out} ({len(new) + len(joins)} links, "
              f"{len(new)} new first, then {len(joins)} corroborated)")


if __name__ == "__main__":
    main()
