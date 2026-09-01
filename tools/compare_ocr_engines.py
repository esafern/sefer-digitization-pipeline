#!/usr/bin/env python3
"""
tools/compare_ocr_engines.py

Compare several OCR/HTR engines' readings of the SAME scan span against the
adjudicated corpus, on one table.

Written 2026-08-31 for the Dicta samples, but deliberately not Dicta- or
Yad-Malachi-specific: it takes any number of labelled plain-text OCR outputs
and any klal window of any `part*.json`, so the next engine (or the next book)
reuses it unchanged.

Why not `tools/second_witness_eval/evaluate_ocr_alignment.py`: that script
segments a candidate by `--- klal N` / `=== KLAL N` headers, which only its
own VLM/Surya baseline files carry. A raw engine dump is page-oriented (or has
no structure at all), so it falls through that script's fallback and scores
0% on every klal. This one anchors the candidate's token stream against the
corpus token stream instead, which needs no headers - and, when a file DOES
carry klal headers, slices it to the requested window first so a full-corpus
baseline can be compared against a three-page sample fairly.

Three independent signals, per Lesson 8/9 (a cheap mechanical check catches a
different class of error than an expensive one, and no single signal is
enough):

  1. Word accuracy - aligned against the corpus. Needs the same edition to
     mean "accuracy"; across editions it also carries real textual variance.
  2. Lexicon hit rate - the candidate's own words against `lexicon.txt`.
     Edition-independent, corpus-independent: the metric that rejected
     HebrewBooks' fastocr at 44.0% (PROJECT-STATUS-HISTORY.md, 2026-08-19).
  3. Letter-frequency signature - per-letter rate vs the corpus. Diagnoses
     WHICH letters an engine collapses, which is what identified fastocr's
     failure as a square model reading Rashi rather than as noise.

Deliberately NOT in `rebuild_all.sh` (cf. Lesson 32, which says cheap
repeatable checks belong in the chain): this one is not repeatable on its
own, because its inputs are OCR dumps that arrive from outside the pipeline
- there is nothing for a scheduled run to re-read. It writes its JSON
artifact so a result outlives the session that produced it.

Usage:
  python3 tools/compare_ocr_engines.py \
      --klalim 12-24 \
      --ocr "Dicta (square)=yad-malachi-berlin-sample_ocr.txt" \
      --ocr "DocAI=yad-malachi-berlin-sample.docai.raw.txt" \
      --out ocr_engine_comparison.json
"""

import argparse
import collections
import difflib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "pipeline"))

import corpus_io as cio

# Header/furniture lines emitted by the various engines' own wrappers. These
# are the file's structure, not the book's text, and must not be scored.
PAGE_HEADER_RE = re.compile(
    r"^\s*(?:===\s*עמוד\s*\d+\s*===|-{2,}\s*Page\s+\d+\s*-{2,}|\s*Page\s+\d+\s*)\s*$"
)
KLAL_HEADER_RE = re.compile(r"^\s*(?:={2,}|-{2,})\s*klal\s+(\d+)", re.IGNORECASE)

# Above this, difflib's quadratic CER stops being worth waiting for.
CER_MAX_CHARS = 120_000


def load_lexicon():
    """The same validated word list every other checker in this repo uses."""
    if not os.path.exists(cio.LEXICON_PATH):
        return set()
    with open(cio.LEXICON_PATH, encoding="utf-8") as f:
        return set(w.strip() for w in f if w.strip())


def tokenize(text):
    """Hebrew-letters-only tokens - corpus_io's own cross-engine normalization.

    Engines disagree about gershayim (Dicta writes `רש"י`, sofer.ai writes
    `רש'י`, DocAI sometimes splits the geresh off as its own token) and about
    punctuation. Scoring those differences would measure transcription
    convention, not reading accuracy, so they are dropped for every candidate
    alike - including the corpus itself.
    """
    out = []
    for raw in text.split():
        w = cio.hebrew_letters_only(raw)
        if w:
            out.append(w)
    return out


def read_candidate(path, klal_lo=None, klal_hi=None):
    """Text of one OCR file, with wrapper furniture removed.

    If the file carries `=== KLAL N ===` headers AND a window was requested,
    only the blocks inside the window are kept; otherwise the whole file is
    taken as covering the window.
    """
    with open(path, encoding="utf-8") as f:
        raw = f.read()

    has_klal_headers = any(KLAL_HEADER_RE.match(ln) for ln in raw.splitlines())
    kept, current = [], None
    for line in raw.splitlines():
        m = KLAL_HEADER_RE.match(line)
        if m:
            current = int(m.group(1))
            continue
        if PAGE_HEADER_RE.match(line):
            continue
        if has_klal_headers and klal_lo is not None:
            if current is None or not (klal_lo <= current <= klal_hi):
                continue
        kept.append(line)
    return "\n".join(kept), has_klal_headers


def reference_tokens(klalim, klal_lo, klal_hi):
    """Corpus tokens for the window, plus each token's owning klal_id."""
    toks, owners = [], []
    for k in sorted(klalim, key=lambda x: x["klal_id"]):
        if not (klal_lo <= k["klal_id"] <= klal_hi):
            continue
        for w in tokenize(k.get("clean_text", "")):
            toks.append(w)
            owners.append(k["klal_id"])
    return toks, owners


def word_alignment(ref, cand):
    """Matched-token count and the per-reference-index matched flags.

    SequenceMatcher's matching blocks only - so this reports agreement, and
    (Lesson 25) it CAN disagree: a candidate token that differs from the
    reference is simply absent from every block.
    """
    sm = difflib.SequenceMatcher(None, ref, cand, autojunk=False)
    matched = [False] * len(ref)
    for b in sm.get_matching_blocks():
        for i in range(b.size):
            matched[b.a + i] = True
    return sum(matched), matched


def trim_to_reference(ref, cand, min_block=3):
    """Cut a candidate down to the stretch that actually overlaps the window.

    A full-corpus baseline, or a sample whose pages spill past the requested
    klalim, carries text the reference does not - and CER counts every
    character of it as an insertion, so an engine gets charged for reading
    MORE of the book. `word_accuracy` is immune (it divides by the reference),
    CER is not. Trimming to the first/last real anchor makes CER a letter-error
    rate again instead of a coverage-mismatch rate.
    """
    sm = difflib.SequenceMatcher(None, ref, cand, autojunk=False)
    blocks = [b for b in sm.get_matching_blocks() if b.size >= min_block]
    if not blocks:
        return cand
    return cand[blocks[0].b: blocks[-1].b + blocks[-1].size]


def char_error_rate(ref, cand):
    """CER over the letter stream with word boundaries REMOVED.

    Deliberately space-free: engines segment differently (DocAI splits a
    geresh off as its own token and emits ~10% more tokens than the corpus
    has words), and scoring those splits at character level measures
    tokenization convention, not letter accuracy. Word-boundary disagreement
    is already what `word_accuracy` measures; this is the letter-level signal
    beside it, and the two are meant to be read together.

    Substitutions are counted as max(len_a, len_b) so no edit is ever free.
    """
    a, b = "".join(ref), "".join(cand)
    if not a:
        return None
    # difflib is quadratic. The shipped windows are ~10k chars; a full-corpus
    # window is ~250k and would appear to hang rather than fail. Refuse instead
    # of pretending - word_accuracy carries the comparison at that size.
    if max(len(a), len(b)) > CER_MAX_CHARS:
        return None
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    errors = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        errors += max(i2 - i1, j2 - j1)
    return errors / len(a)


def lexicon_hit_rate(tokens, lexicon):
    if not lexicon or not tokens:
        return None, 0
    hits = sum(1 for t in tokens if t in lexicon)
    return hits / len(tokens), len(tokens)


def confusion_pairs(ref, cand, top=8):
    """Which letters an engine actually swaps, from the alignment itself.

    A frequency ratio says a letter is over-produced; it cannot say what it
    was produced INSTEAD OF. This walks the word alignment, and inside each
    replaced word pair walks the character alignment, so the output is
    directed pairs - corpus letter -> engine letter - which is the form the
    fastocr diagnosis (2026-08-19) needed and had to be inferred from ratios.
    """
    counter = collections.Counter()
    sm = difflib.SequenceMatcher(None, ref, cand, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != "replace":
            continue
        # Only same-length runs pair up unambiguously word-for-word; longer
        # runs are resynchronization noise, not a legible substitution.
        if (i2 - i1) != (j2 - j1):
            continue
        for a_w, b_w in zip(ref[i1:i2], cand[j1:j2]):
            csm = difflib.SequenceMatcher(None, a_w, b_w, autojunk=False)
            for ctag, a1, a2, b1, b2 in csm.get_opcodes():
                if ctag == "equal":
                    continue
                counter[(a_w[a1:a2] or "\u2205", b_w[b1:b2] or "\u2205")] += 1
    return counter.most_common(top)


def letter_frequencies(tokens):
    counter = collections.Counter()
    for t in tokens:
        counter.update(t)
    total = sum(counter.values())
    if not total:
        return {}
    return {ch: n / total for ch, n in counter.items()}


def detect_span(cand_tokens, klalim, min_block=8):
    """Which klalim a headerless OCR dump actually covers - by CONTENT.

    Lesson 30: a page index that looks right is not a page index that IS
    right. Anchoring the candidate's own tokens in the corpus is a content
    check; reading a page number off a filename is not.
    """
    toks, owners = [], []
    for k in sorted(klalim, key=lambda x: x["klal_id"]):
        for w in tokenize(k.get("clean_text", "")):
            toks.append(w)
            owners.append(k["klal_id"])
    sm = difflib.SequenceMatcher(None, toks, cand_tokens, autojunk=False)
    blocks = [b for b in sm.get_matching_blocks() if b.size >= min_block]
    if not blocks:
        return None
    lo = blocks[0].a
    hi = blocks[-1].a + blocks[-1].size
    # Report the anchors, so an implausible span is visible rather than silent.
    # min_block is 8, not 3: three consecutive normalized Hebrew tokens recur by
    # coincidence in a rabbinic text, and one such hit before the true span
    # stretches klal_lo downward, inflating the reference and depressing every
    # engine's accuracy with nothing printed to say so.
    print(f"  anchored on {len(blocks)} block(s) of >= {min_block} tokens; "
          f"first {blocks[0].size}, last {blocks[-1].size}")
    return min(owners[lo:hi]), max(owners[lo:hi])


def evaluate(label, path, ref_tokens, ref_owners, lexicon, ref_letters,
             klal_lo, klal_hi):
    text, had_headers = read_candidate(path, klal_lo, klal_hi)
    cand = tokenize(text)
    matched_total, matched_flags = word_alignment(ref_tokens, cand)

    per_klal = collections.OrderedDict()
    for idx, kid in enumerate(ref_owners):
        row = per_klal.setdefault(kid, [0, 0])
        row[1] += 1
        if matched_flags[idx]:
            row[0] += 1

    hit, hit_n = lexicon_hit_rate(cand, lexicon)
    cand_letters = letter_frequencies(cand)
    ratios = {}
    # The UNION, not the reference's alphabet. Iterating the reference alone
    # made this signal blind to a letter the engine produces that the corpus
    # never uses - which is precisely a hallucinated-glyph failure, and this is
    # the signal credited with diagnosing fastocr as a square model reading
    # Rashi. An unseen candidate letter gets ratio inf and sorts to the top,
    # the same way an unproduced reference letter gets 0 and does.
    for ch in set(ref_letters) | set(cand_letters):
        ref_rate = ref_letters.get(ch, 0.0)
        cand_rate = cand_letters.get(ch, 0.0)
        ratio = (cand_rate / ref_rate) if ref_rate > 0 else float("inf")
        ratios[ch] = (ratio, cand_rate, ref_rate)

    return {
        "label": label,
        "file": os.path.relpath(path, REPO),
        "sliced_by_klal_headers": had_headers,
        "candidate_tokens": len(cand),
        "reference_tokens": len(ref_tokens),
        "matched_tokens": matched_total,
        "word_accuracy": matched_total / len(ref_tokens) if ref_tokens else None,
        "cer": char_error_rate(ref_tokens, trim_to_reference(ref_tokens, cand)),
        "cer_scope": "candidate trimmed to the reference window's anchors",
        "lexicon_hit_rate": hit,
        "lexicon_scored_tokens": hit_n,
        "per_klal": {str(k): {"matched": v[0], "reference": v[1],
                              "accuracy": v[0] / v[1] if v[1] else None}
                     for k, v in per_klal.items()},
        "letter_ratios": {ch: {"ratio": (None if r == float("inf") else r),
                               "invented": r == float("inf"),
                               "candidate": c, "reference": rr}
                          for ch, (r, c, rr) in ratios.items()},
        "confusions": [{"corpus": a, "engine": b, "count": n}
                       for (a, b), n in confusion_pairs(ref_tokens, cand)],
    }


def pct(x):
    return "—" if x is None else f"{x * 100:.1f}%"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--reference", default=cio.PART1_PATH,
                    help="corpus file the candidates are scored against (default part1.json)")
    ap.add_argument("--klalim", help="klal window, e.g. 12-24. Omit to auto-detect "
                                     "from the FIRST --ocr file's own content.")
    ap.add_argument("--ocr", action="append", default=[], metavar="LABEL=PATH",
                    help="a candidate OCR text file; repeat once per engine")
    ap.add_argument("--out", help="write the full result as JSON here")
    ap.add_argument("--letters", type=int, default=6,
                    help="how many most-distorted letters to print per engine (0 to skip)")
    args = ap.parse_args()

    if not args.ocr:
        ap.error("at least one --ocr LABEL=PATH is required")

    candidates = []
    for spec in args.ocr:
        if "=" not in spec:
            ap.error(f"--ocr needs LABEL=PATH, got {spec!r}")
        label, path = spec.split("=", 1)
        if not os.path.exists(path):
            ap.error(f"no such OCR file: {path}")
        candidates.append((label.strip(), path))

    klalim = cio.load_klalim(args.reference)
    if not klalim:
        raise SystemExit(f"{args.reference} holds no klalim")

    if args.klalim:
        m = re.match(r"^\s*(\d+)\s*-\s*(\d+)\s*$", args.klalim)
        if not m:
            ap.error("--klalim wants LO-HI, e.g. 12-24")
        klal_lo, klal_hi = int(m.group(1)), int(m.group(2))
        detected_from = None
    else:
        first_text, _ = read_candidate(candidates[0][1])
        span = detect_span(tokenize(first_text), klalim)
        if not span:
            raise SystemExit(f"could not anchor {candidates[0][1]} in {args.reference}")
        klal_lo, klal_hi = span
        detected_from = candidates[0][0]

    ref_tokens, ref_owners = reference_tokens(klalim, klal_lo, klal_hi)
    if not ref_tokens:
        raise SystemExit(f"klalim {klal_lo}-{klal_hi} are empty in {args.reference}")
    ref_letters = letter_frequencies(ref_tokens)
    lexicon = load_lexicon()

    results = [evaluate(label, path, ref_tokens, ref_owners, lexicon,
                        ref_letters, klal_lo, klal_hi)
               for label, path in candidates]

    print("=" * 78)
    print(f"OCR ENGINE COMPARISON - {os.path.basename(args.reference)} klalim {klal_lo}-{klal_hi}")
    if detected_from:
        print(f"(window auto-detected from {detected_from}'s own content)")
    print(f"reference tokens: {len(ref_tokens)}   lexicon: {len(lexicon)} words")
    print("=" * 78)
    print()
    print("| Engine | OCR words | Word acc. | CER (letters) | Lexicon hit |")
    print("|---|---:|---:|---:|---:|")
    for r in results:
        cer = "too large" if r["cer"] is None and r["candidate_tokens"] else pct(r["cer"])
        # An engine that emits far more tokens than the window holds is charged
        # for them as insertions, so its CER and its word accuracy point in
        # opposite directions (the VLM baselines: 96.1% accuracy, 20.2% CER).
        # Flag it rather than leave the reader to wonder which column to believe.
        if r["cer"] is not None and r["candidate_tokens"] > len(ref_tokens) * 1.15:
            cer += " ⚠"
        print(f"| {r['label']} | {r['candidate_tokens']} | {pct(r['word_accuracy'])} "
              f"| {cer} | {pct(r['lexicon_hit_rate'])} |")

    # Corpus baseline: what the adjudicated text itself scores on the
    # corpus-independent metric, so a candidate's lexicon hit has a ceiling
    # to be read against rather than being quoted bare.
    base_hit, _ = lexicon_hit_rate(ref_tokens, lexicon)
    print(f"| _corpus (adjudicated, ceiling)_ | {len(ref_tokens)} | 100.0% | 0.0% | {pct(base_hit)} |")
    if any(r["cer"] is not None and r["candidate_tokens"] > len(ref_tokens) * 1.15
           for r in results):
        print("\n⚠ = emits >15% more tokens than the window holds, so its CER counts "
              "that overhang as insertions and is NOT comparable with the others. "
              "Word accuracy is unaffected (it divides by the reference).")

    print("\n### Per-klal word accuracy\n")
    kids = sorted({int(k) for r in results for k in r["per_klal"]})
    print("| klal | " + " | ".join(r["label"] for r in results) + " |")
    print("|---:|" + "---:|" * len(results))
    for kid in kids:
        cells = []
        for r in results:
            row = r["per_klal"].get(str(kid))
            cells.append(pct(row["accuracy"]) if row else "—")
        print(f"| {kid} | " + " | ".join(cells) + " |")

    print("\n### Substitutions the alignment actually shows (corpus -> engine)\n")
    for r in results:
        parts = [f"{c['corpus']}->{c['engine']} x{c['count']}" for c in r["confusions"][:6]]
        print(f"- **{r['label']}**: " + (", ".join(parts) if parts else "none"))

    if args.letters:
        print("\n### Letter-frequency signature (most distorted vs corpus)\n")
        for r in results:
            worst = sorted(r["letter_ratios"].items(),
                           key=lambda kv: (float("inf") if kv[1]["ratio"] == float("inf")
                                           else abs(1.0 - kv[1]["ratio"])), reverse=True)[:args.letters]
            parts = [(f"{ch} NEW (absent from the corpus)" if v["ratio"] == float("inf")
                      else f"{ch} {v['ratio']:.2f}x") for ch, v in worst]
            print(f"- **{r['label']}**: " + ", ".join(parts))

    if args.out:
        payload = {
            "reference": os.path.relpath(args.reference, REPO),
            "klal_range": [klal_lo, klal_hi],
            "window_auto_detected_from": detected_from,
            "reference_tokens": len(ref_tokens),
            "corpus_lexicon_hit_rate": base_hit,
            "engines": results,
        }
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.flush()
        print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
