#!/usr/bin/env python3
"""
tools/build_witness_disputes.py

Build a review queue from an INDEPENDENT witness, for a corpus whose own
extractor cannot check it.

WHY THIS EXISTS. `build_corrections_dataset.py` diffs DocAI's fresh OCR against
what the corpus stores, which is a real comparison for a corpus that came from
somewhere else and has been corrected. Sefer HaShorashim's corpus IS DocAI's
output, so that diff produced 346 candidates containing **zero reading
differences** - 227 deletions, 119 insertions, not one substitution, because a
substitution is impossible when the two sides are the same artifact (item 0ER,
Lesson 25 A SIGNAL THAT CANNOT DISAGREE).

A corpus built from engine X cannot be checked by engine X. The first witness a
newly-ingested book needs is not a better version of its own extractor.

WHAT COUNTS AS A WITNESS HERE. A JSON map of `{root: text}` from a source that
did not produce the corpus. Two exist for this book:

  * Sefaria's digitization (item 0EM) - independent and HUMAN-SUPERVISED, which
    no OCR witness is. 76.4% token agreement over 306 shared entries.
  * Cloud Vision (item 0EH) - a different engine whose dominant error, `ו->ן`,
    DocAI does not make. NOT the Google Books text layer, which is DocAI's twin
    error-for-error and is a reliability gate only (item 0ED).

WHAT IT DOES NOT DO. It proposes nothing and applies nothing. Every row says
"these two readings differ here", never which is right - that needs the ink, and
for this project it needs the vision adjudicator and then a human. Agreement is
not recorded as evidence either: two sources agreeing tells you they agree.

NORMALISATION IS PER-PURPOSE AND MIXING THEM UP COSTS 16 POINTS. Root
identifiers fold final letters, because a root is written non-final; running
text must NOT, because folding turns `אלהים` into `אלהימ`, which is in no
lexicon and matches nothing. Both sides are NFKC-normalised first: this dataset
writes shin as U+FB2A, the precomposed presentation form, which sits outside
`[א-ת]` and silently drops every shin-bearing word without it (item 0EO).

Usage:
  SEFER_CORPUS_ROOT=~/work/hashorashim python3 tools/build_witness_disputes.py \
      --witness sefaria=~/work/hashorashim/witness_entries_flat.json --out witness_disputes.json
"""

import argparse
import collections
import difflib
import json
import os
import re
import sys
import unicodedata

# Bootstrap only - deliberately NOT bound to a name like REPO, which is the
# seam bypass tests/test_pipeline_logic.py's bypass guard exists to catch.
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "pipeline"))
import corpus_io as cio  # noqa: E402

EDITORIAL = re.compile(r"[\[\]]")

# One copy, in corpus_io, since 2026-09-13: the server now matches entries to
# another digitization's texts with it too (item 0GC).
root_key = cio.root_key


def text_words(text):
    """Running text: NFKC, points deleted, PUNCTUATION SEPARATES, finals kept.

    The maqaf is the reason this goes through corpus_io rather than a local
    regex. The witness is a POINTED text and writes `אֶת־כָּל־הָעַמִּים`; our
    corpus is unpointed and writes the same phrase with spaces. Deleting the
    maqaf instead of splitting on it produced the single token `אתכלהעמים`,
    which then aligned against three of ours and was emitted as a dispute - a
    typography difference presented to a human as a disagreement about letters.
    """
    out = []
    # SPLIT ON SPACES FIRST - through corpus_io.words_of(), the one
    # sanctioned space split - so every kept word carries its index in
    # `clean_text.split(' ')` - the one index space the dashboard, the decision
    # ledger and corpus_io.words_of() all use. Splitting the whole text on
    # punctuation first (as this did until 2026-09-13) made `word_index` an
    # index into THIS function's filtered list instead, which drops
    # punctuation-only tokens and one-letter words. Every such token before a
    # dispute shifted it: on klal 1 the queue sent the reviewer to word 74,
    # `הפרחה`, while the scan box sat on `הרמונים` - three places later, one per
    # period. The scan and the text each looked plausible alone.
    for pos, tok in enumerate(cio.words_of(text)):
        normed = unicodedata.normalize("NFKC", tok)
        for raw in cio.HEBREW_PUNCT.sub(" ", cio.strip_points(normed)).split():
            w = cio.hebrew_letters_only(raw)
            if len(w) >= 2:
                out.append((w, raw, pos))
    return out


def disputes_for(entry_words, witness_words):
    """Aligned differences as (opcode, corpus_index, corpus_span, witness_span),
    an equal-length replace split into one row per differing word.

    `corpus_index` is a position in `clean_text.split(' ')` (see text_words),
    not in the filtered word list the alignment runs over.
    """
    a = [w[0] for w in entry_words]
    b = [w[0] for w in witness_words]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    rows = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        # ONE ROW PER WORD when both sides have the same number of words
        # (item 0GE, reviewer 2026-09-14). A two-word replace bundled two
        # independent differences: klal 21 w127 `בארם לעולם` / `באדם לעלם` is a
        # misread dalet AND a plene/defective spelling, the page prints `באדם
        # לעולם`, and no offered reading could be right - 51 queue rows were
        # that shape. Pieces sharing one corpus position (a maqaf-joined word)
        # stay together: two rows at one word would claim one token.
        if tag == "replace" and i2 - i1 == j2 - j1 and i2 - i1 > 1:
            pieces = {}
            for k in range(i2 - i1):
                ci, wj = entry_words[i1 + k], witness_words[j1 + k]
                if ci[0] == wj[0]:
                    continue
                cs, ws = pieces.setdefault(ci[2], ([], []))
                cs.append(ci[1])
                ws.append(wj[1])
            for pos in sorted(pieces):
                rows.append(("replace", pos, pieces[pos][0], pieces[pos][1]))
            continue
        if i1 < len(entry_words):
            pos = entry_words[i1][2]
        else:                                   # insertion after the last word
            pos = entry_words[-1][2] + 1 if entry_words else 0
        rows.append((tag, pos,
                     [entry_words[i][1] for i in range(i1, i2)],
                     [witness_words[j][1] for j in range(j1, j2)]))
    return rows


FOOTNOTE_TAIL = re.compile(r'^[יו"\']{1,3}$')


def classify_dispute(corpus, witness):
    """Triage class for one disagreement. The queue is not uniform and treating
    it as uniform wastes the reviewer.

    `footnote_numeral` is the big one and it is OURS, not the witness's: this
    edition prints superscript reference numerals inline (`בצקו 16`) and DocAI
    reads them as yods glued to the preceding word. 232 rows where our reading is
    the witness's plus a trailing `י`/`יי`/`"י`. Item 0EJ deferred separating the
    footnote APPARATUS; this is the same problem's other half, inside the line.
    """
    a = corpus.replace(" ", "")
    b = witness.replace(" ", "")
    if a == b:
        return "join_split"          # same letters, different word division
    if not a or not b:
        return "one_side_empty"
    if a.startswith(b) and FOOTNOTE_TAIL.match(a[len(b):]):
        return "footnote_numeral"    # ours carries a superscript read as a letter
    if abs(len(a) - len(b)) <= 1 and sum(x != y for x, y in zip(a, b)) <= 1:
        return "one_letter"
    return "other"


def root_groups(klalim):
    """{root_key: [entries sharing that root, in corpus order]}.

    Sefer HaShorashim has HOMOGRAPH entries - two headings on one root (`אלה`,
    `ארש`, `בכה`, `בלה`, `גרש`; root_entries.json confirms each pair) - and the
    witness keys its texts by root, so it holds ONE text for both, running the
    two headings together. A {root: entry} dict kept only the last of each pair,
    so 5 entries were never compared (code review 2026-09-13, finding 3).
    """
    groups = {}
    for k in klalim:
        groups.setdefault(root_key(k.get("gematria") or ""), []).append(k)
    return groups


def group_disputes(entries, witness_text):
    """disputes_for() over a root's entries JOINED IN ORDER against the
    witness's one text, each difference mapped back to (entry, word_index in
    that entry, opcode, corpus_span, witness_span).

    For a single-entry root this is exactly disputes_for(). A difference that
    straddles two entries is attributed to the entry where it starts.
    """
    ew, bases, base = [], [], 0
    for k in entries:
        bases.append((base, k))
        ew.extend((w, raw, base + pos) for w, raw, pos in text_words(k["clean_text"]))
        base += len(cio.words_of(k))
    for tag, g, corpus_span, wit_span in disputes_for(ew, text_words(witness_text)):
        b, k = next((b, k) for b, k in reversed(bases) if b <= g)
        yield k, g - b, tag, corpus_span, wit_span


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--witness", action="append", required=True, metavar="NAME=PATH",
                    help="a {root: text} JSON from a source that did NOT build the corpus")
    ap.add_argument("--out", default=None)
    ap.add_argument("--max-span", type=int, default=4,
                    help="skip differences longer than this many words - a long "
                         "run is an alignment failure, not a disputed word")
    ap.add_argument("--show", type=int, default=10)
    args = ap.parse_args()

    klalim = cio.load_klalim(cio.PART1_PATH)
    groups = root_groups(klalim)

    all_rows = []
    stats = {}
    for spec in args.witness:
        name, path = spec.split("=", 1)
        with open(os.path.expanduser(path), encoding="utf-8") as fh:
            witness = json.load(fh)
        wit_by_key = {root_key(x): (v if isinstance(v, str) else " ".join(v))
                      for x, v in witness.items()}
        shared = [key for key in groups if key in wit_by_key]
        n_disp = n_words = n_entries = 0
        for key in shared:
            n_entries += len(groups[key])
            n_words += sum(len(text_words(k["clean_text"])) for k in groups[key])
            for k, idx, tag, corpus_span, wit_span in group_disputes(groups[key], wit_by_key[key]):
                if max(len(corpus_span), len(wit_span)) > args.max_span:
                    continue
                n_disp += 1
                all_rows.append({
                    "witness": name,
                    "klal_id": k["klal_id"],
                    "root": k.get("gematria"),
                    "page": k.get("page"),
                    "word_index": idx,
                    "opcode": tag,
                    "corpus": " ".join(corpus_span),
                    "witness_reading": " ".join(wit_span),
                    # An editorial insertion is the witness's EDITOR speaking, not
                    # a reading of the ink, and must not be shown as an OCR dispute.
                    "editorial": bool(EDITORIAL.search(" ".join(wit_span))),
                    "class": classify_dispute(" ".join(corpus_span),
                                              " ".join(wit_span)),
                })
        stats[name] = {"shared_entries": n_entries, "shared_roots": len(shared),
                       "corpus_words": n_words,
                       "disputes": n_disp}

    ed = sum(1 for r in all_rows if r["editorial"])
    print(f"  witnesses       {', '.join(stats)}")
    for name, st in stats.items():
        print(f"    {name:<10} {st['shared_entries']} shared entries, "
              f"{st['corpus_words']:,} corpus words, {st['disputes']:,} disputes")
    print(f"  editorial       {ed} rows are the witness's own bracketed insertions")
    by_op = collections.Counter(r["opcode"] for r in all_rows)
    print(f"  by opcode       {dict(by_op)}")
    by_cls = collections.Counter(r["class"] for r in all_rows if not r["editorial"])
    print("  by class (non-editorial):")
    for c, n in by_cls.most_common():
        print(f"    {c:<20} {n:>5}   {100.0 * n / max(sum(by_cls.values()), 1):4.1f}%")

    live = [r for r in all_rows
            if not r["editorial"] and r["class"] not in ("join_split",)]
    print(f"\n  first {min(args.show, len(live))} disputes (corpus | witness)")
    for r in live[:args.show]:
        print(f"    klal {r['klal_id']:<4} {r['root']:<5} w{r['word_index']:<4} "
              f"{r['opcode']:<8} {r['corpus'][:24]:<24} | {r['witness_reading'][:24]}")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump({"what_this_is":
                       "Positions where the corpus and an INDEPENDENT witness "
                       "read differently. Nothing here says which is right; that "
                       "needs the scan. Agreement is deliberately not recorded.",
                       "stats": stats, "disputes": all_rows}, fh,
                      ensure_ascii=False, indent=1)
            fh.flush()
            os.fsync(fh.fileno())
        print(f"\n  wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
