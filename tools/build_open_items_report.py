#!/usr/bin/env python3
# [STANDALONE] Derive the reviewer's CURRENT open queue from live state and write
# it as a report render_report.py can turn into clickable dashboard links.
#
# WHY THIS EXISTS. `open_items_2026-08-30.json` was written by hand. It is fully
# computable from `review_decisions.jsonl` plus the corpus, which makes a
# hand-written copy exactly the Lesson 13 defect this repo keeps finding: a
# "derived" file that is really a second copy of the truth, agreeing until the
# day the corpus moves under it. It moved on 2026-08-31 - six of that file's 24
# flagged items had been resolved and it still listed them as open, and one
# entry ("NEEDS YOUR RULING on klal 66 w0") had been ruled on the day before.
#
# Nothing here decides anything. It reports what the ledger and the corpus
# currently say, so the list is regenerable and cannot rot.
#
# NOT YAD-MALACHI-SPECIFIC: every part file it reads comes from corpus_io, and
# klal/word are the only coordinates it knows.
#
# Usage:
#   python3 tools/build_open_items_report.py                 # -> open_items_<today>.json
#   python3 tools/build_open_items_report.py --out FILE
#   python3 tools/build_open_items_report.py --part 1        # limit to one part file
import argparse
import datetime
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pipeline"))

import corpus_io as cio          # noqa: E402
import review_decisions as rd    # noqa: E402

# The decision types that RECORD a reviewer's answer at a word. `klal_flag` is
# deliberately not here - it raises a question, it does not answer one.
ANSWER_TYPES = ("disputed_choice", "candidate_choice", "manual_correction",
                "witness_choice", "punctuation_choice")


def _first_line(note, limit=180):
    """A flag's note is a paragraph; a table cell wants its first sentence."""
    if not note:
        return ""
    text = " ".join(str(note).split())
    return text if len(text) <= limit else text[:limit - 1] + "…"


def load_corpus(parts):
    by_id = {}
    for n in parts:
        path = cio.repo_path(f"part{n}.json")
        if not os.path.exists(path):
            continue
        for k in cio.load_klalim(path):
            by_id[k["klal_id"]] = k
    return by_id


# An `insert`/`delete`-opcode position may legitimately sit at index == len(words):
# that is the append point at the END of the klal, where apply_delete_insertion
# writes. It is NOT an out-of-range index, and calling it one would put a real
# review item in the broken bucket.
END_OF_KLAL = "<end of klal>"


def word_at(klal, word_index):
    """The word currently standing at that index, END_OF_KLAL for the append
    position, or None if the index is genuinely past the text.

    Split on a single space, the same convention apply_reviewer_decisions.py
    indexes with - NOT .split(), whose whitespace collapsing would renumber
    every word after a double space and point every link one word off."""
    words = klal["clean_text"].split(" ")
    if 0 <= word_index < len(words):
        return words[word_index]
    if word_index == len(words):
        return END_OF_KLAL
    return None


def build(parts):
    by_id = load_corpus(parts)
    flags = rd.all_current("klal_flag")

    open_words, open_klalim, out_of_range = [], [], []
    for (klal_id, word_index), row in sorted(flags.items(),
                                             key=lambda kv: (kv[0][0], kv[0][1] is None,
                                                             kv[0][1] or 0)):
        if not row.get("needs_revisit"):
            continue
        klal = by_id.get(klal_id)
        if klal is None:
            continue
        note = _first_line(row.get("note"))
        if word_index is None:
            open_klalim.append({"klal_id": klal_id, "reason": note})
            continue
        stored = word_at(klal, word_index)
        entry = {"klal_id": klal_id, "word_index": word_index,
                 "stored": stored if stored is not None else "", "reason": note}
        # An out-of-range flag cannot be clicked to anything, so it is its own
        # bucket rather than a row that silently links to the klal's start.
        (open_words if stored is not None else out_of_range).append(entry)

    # A recorded answer with no text is not an answer. The write-site guard stops
    # new ones (item 21); these predate it, still read as decided, and can only be
    # cleared by a reviewer superseding them - so they belong on this list.
    # `punctuation_choice` is EXCLUDED: there `chosen_source: "reject"` with a null
    # chosen_text is the deliberate encoding of "do not insert this mark", not a
    # dropped answer. Verified against all four rows before excluding them.
    null_answers = []
    for row in rd._read_all():
        if row.get("decision_type") not in ANSWER_TYPES:
            continue
        if row.get("decision_type") == "punctuation_choice":
            continue
        if row.get("chosen_text") is not None:
            continue
        klal_id, word_index = row.get("klal_id"), row.get("word_index")
        if klal_id is None or word_index is None:
            continue
        current = rd.current_for(klal_id, word_index)
        if not current or current.get("id") != row["id"]:
            continue        # already superseded by a real answer
        klal = by_id.get(klal_id)
        stored = word_at(klal, word_index) if klal else None
        null_answers.append({
            "klal_id": klal_id, "word_index": word_index,
            "stored": stored or "",
            "reason": f"NULL DECISION recorded {row['ts'][:10]} ({row['decision_type']}) - "
                      f"marks this word decided while nothing can promote it; "
                      f"supersede it with a real ruling",
        })

    return {
        "open word-level flags": open_words,
        "open klal-level flags": open_klalim,
        "flags whose word index is out of range": out_of_range,
        "null decisions still standing": null_answers,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=None, help="output path (default open_items_<today>.json)")
    ap.add_argument("--part", type=int, action="append", choices=(1, 2, 3),
                    help="limit to this part file; repeatable (default: all three)")
    args = ap.parse_args()

    parts = args.part or (1, 2, 3)
    report = build(parts)
    out = args.out or cio.repo_path(
        f"open_items_{datetime.date.today().isoformat()}.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
        f.flush()
    for name, rows in report.items():
        print(f"  {len(rows):>4}  {name}")
    print(f"wrote {out}")
    print(f"render it with: python3 tools/render_report.py {os.path.basename(out)}")


if __name__ == "__main__":
    main()
