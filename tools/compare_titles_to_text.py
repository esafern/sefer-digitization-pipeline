#!/usr/bin/env python3
# [STANDALONE] Compare every klal's `title` against the opening of its own
# `clean_text`, and report how the two relate.
#
# WHY. The `title` field has never had an OCR pass - no detector, witness,
# validator or adjudicator in this repo reads it (PROJECT-STATUS item 39). Its
# only structural property is that a title should be a PREFIX of its own body
# after the gematria marker, because the printed heading IS the opening of the
# klal, set in larger type. Anything else is one of three things:
#
#   DIVERGES  the title and the body disagree on a word - one of them carries an
#             OCR error the other does not. The body is the better witness (it
#             has been adjudicated; the title has not), but NOT automatically
#             right - klal 36 was a case where both spellings were legitimate.
#   OFFSET    the title starts at a different body word than the first, so the
#             prefix test is answering the wrong question. Benign on its own.
#   ABSORBED  the title is a clean prefix but a LONG one, i.e. it may have
#             swallowed body text. This is a SUSPICION, never a finding: this
#             book's genuine headings run to 24 words. Only the scan decides,
#             because only the printed type size says where a heading stops.
#
# The report is deliberately advisory. It writes no flags and edits nothing.
#
# Usage:
#   python3 tools/compare_titles_to_text.py                 # part 1, summary
#   python3 tools/compare_titles_to_text.py --all           # all three parts
#   python3 tools/compare_titles_to_text.py --show diverges
#   python3 tools/compare_titles_to_text.py --json out.json
import argparse
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pipeline"))

import corpus_io as cio  # noqa: E402

# A title this long is worth a human look. Chosen from the measured distribution
# (Part 1 mean 6.2 words, median 6, p90 11) - not from taste. It is a triage
# threshold, not a rule: klal 92's legitimate title is 24 words.
LONG_TITLE_WORDS = 11


def classify(klal):
    """(kind, detail) for one klal. `kind` is one of prefix/diverges/offset/empty."""
    title = (klal.get("title") or "").strip()
    body = klal.get("clean_text", "").split()
    if not title or not body:
        return "empty", {}
    tw = title.split()
    norm = cio.hebrew_letters_only
    # Drop the gematria marker, then drop the editorial punctuation tokens the
    # body carries and the heading does not (`,` `.` `[.]` `•`). Without this,
    # klalim 105 and 134 read as OCR divergences when the only difference is a
    # comma the punctuation pass inserted into the body - a false positive that
    # would have sent someone looking for a misread letter that is not there.
    bw = [w for w in body[1:] if norm(w) or any(c.isalnum() for c in w)]

    matched = 0
    for t, b in zip(tw, bw):
        if norm(t) != norm(b):
            break
        matched += 1

    detail = {"title_words": len(tw), "matched_words": matched,
              "title": title, "body_opening": " ".join(bw[:max(len(tw), 8) + 2])}

    if matched == len(tw):
        detail["long"] = len(tw) >= LONG_TITLE_WORDS
        return "prefix", detail

    # Does the title appear a little further into the body? Then the mismatch is
    # an OFFSET, not an OCR divergence, and saying so keeps the two apart.
    for start in range(1, min(6, len(bw))):
        if all(norm(t) == norm(b) for t, b in zip(tw, bw[start:])) and len(bw) - start >= len(tw):
            detail["offset"] = start
            return "offset", detail

    detail["first_diff"] = {"index": matched,
                            "title_word": tw[matched] if matched < len(tw) else None,
                            "body_word": bw[matched] if matched < len(bw) else None}
    return "diverges", detail


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--all", action="store_true", help="all three part files (default: part 1)")
    ap.add_argument("--show", choices=("diverges", "offset", "long", "prefix", "all"),
                    help="print the klalim in this bucket")
    ap.add_argument("--json", help="also write the full per-klal result here")
    args = ap.parse_args()

    names = ("part1.json", "part2.json", "part3.json") if args.all else ("part1.json",)
    klalim = []
    for n in names:
        klalim += cio.load_klalim(cio.repo_path(n))

    buckets = {"prefix": [], "diverges": [], "offset": [], "empty": [], "long": []}
    rows = []
    for k in sorted(klalim, key=lambda x: x["klal_id"]):
        kind, detail = classify(k)
        buckets[kind].append(k["klal_id"])
        if detail.get("long"):
            buckets["long"].append(k["klal_id"])
        rows.append({"klal_id": k["klal_id"], "kind": kind, **detail})

    total = len(klalim)
    print(f"{total} klalim over {', '.join(names)}\n")
    print(f"  clean prefix of their own body : {len(buckets['prefix']):>4}")
    print(f"    ...of which LONG (>= {LONG_TITLE_WORDS} words) : {len(buckets['long']):>4}  "
          f"<- suspicion only, the scan decides")
    print(f"  DIVERGES (an OCR error in one)  : {len(buckets['diverges']):>4}")
    print(f"  offset (title starts later)     : {len(buckets['offset']):>4}")
    print(f"  no title or no text             : {len(buckets['empty']):>4}")

    if args.show:
        want = ("prefix", "diverges", "offset", "empty") if args.show == "all" else (args.show,)
        print()
        for r in rows:
            if args.show == "long":
                if not r.get("long"):
                    continue
            elif r["kind"] not in want:
                continue
            print(f"--- klal {r['klal_id']} [{r['kind']}] "
                  f"{r.get('title_words', 0)} title words, {r.get('matched_words', 0)} matched ---")
            print(f"    title: {r.get('title', '')}")
            print(f"    body : {r.get('body_opening', '')}")
            if r.get("first_diff"):
                d = r["first_diff"]
                print(f"    DIFF at title word {d['index']}: "
                      f"title {d['title_word']!r} vs body {d['body_word']!r}")
            if r.get("offset"):
                print(f"    title begins at body word {r['offset']}, not 0")
            print()

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=1)
            f.flush()
        print(f"\nwrote {args.json}")


if __name__ == "__main__":
    main()
