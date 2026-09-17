#!/usr/bin/env python3
"""
tools/validate_quotations.py

Check every quotation in a witness dataset against the verse its own apparatus
cites, and report the words that do not belong.

WHAT THIS IS FOR. Sefer HaShorashim is mostly biblical quotation, and Bacher's
apparatus says which verse each quotation comes from. That makes a large part of
the text self-checking WITHOUT a second OCR, without vision, and without a
human: take the run of words before a footnote marker, look up the cited verse,
and any word sitting inside an otherwise-matching run that is absent from the
verse is a suspect - almost always an OCR error, occasionally a wrong citation.

Sefaria asked for exactly this and shelved it ("ensuring the relevant quote is
indeed found in the referenced citation"). It is cheap, so it should not be
shelved.

WHY "INSIDE AN OTHERWISE-MATCHING RUN" IS THE WHOLE TRICK. Asking "is this word
in the verse?" on its own flags every word of Ibn Janah's prose, which has no
source and is most of the book. The signal only exists where the surrounding
words ARE in the verse: `רמה ונוש עפר` against a verse reading `רמה וגוש עפר`
identifies `ונוש` precisely, because its neighbours anchor it. So a run must
corroborate first - `--min-anchor` words matching - and only then are its
non-matching members reported.

WHAT IT CANNOT DO. It is silent on prose, on abbreviated or paraphrased
quotations, and wherever the citation does not resolve. It reports suspects, not
errors: a printing may legitimately differ from the Masoretic text, and a word
absent from the verse may be Ibn Janah's own comment inside the quotation. Every
row carries the verse link so a human decides in one glance.

Usage (the command that writes the files sent to Sefaria, item 0FM):
  SEFER_CORPUS_ROOT=~/work/hashorashim python3 tools/validate_quotations.py \
      --footnotes ~/work/hashorashim/witness_footnotes.json --find-better \
      --review ~/work/hashorashim/citation_review.json \
      --csv ~/work/hashorashim/citation_corrections.csv \
      --out ~/work/hashorashim/quotation_suspects.json
"""

import argparse
import collections
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "pipeline"))
sys.path.insert(0, _HERE)
import corpus_io as cio  # noqa: E402
from adjudicate_against_verse import (Tanakh, verse_words, entry_refs,  # noqa: E402
                                      flatten, iso, VERSE_SPAN)


# The divine name is written `ה'` or `י"י` in this edition and `יהוה` in the
# verse. Without this every quotation containing it reports a false suspect.
DIVINE = {"ה", "יי", "ייי", "יהוה", "אדני"}


def matches(word, vwords):
    return word in vwords or (word in DIVINE and vwords & DIVINE)


def ends_in_cited(flat, floor, end, vwords, other=None):
    """Do the two words right before the marker belong to the cited verse, and
    not also to `other` - the verse the run was found to match instead?

    Then the note is right however little of the run matched: the window grew
    back into an EARLIER quotation and found that one's verse. Read by eye on
    2026-09-14 (item 0FM), 9 of the 158 "misplaced" citations were this -
    `הנחמים באלים` (Isaiah 57:5) behind `ותחפרו מהגנות אשר בחרתם` (Isaiah 1:29),
    `אחזה בסנסניו` (Song of Songs 7:9) behind 2:13. The words must single the
    cited verse out: a formula such as `נאם ה'` stands in Jeremiah 31:31 and
    31:32 alike, and without `other` it passed the note for 31:31 as right when
    the quotation is 31:32's."""
    tail = [w for w, _t in flat[max(floor, end - 2):end]]
    if len(tail) != 2 or not all(matches(w, vwords) for w in tail):
        return False
    return other is None or not all(matches(w, other) for w in tail)


def citation_kind(cited, proposed, same_shift):
    """What a misplaced citation IS, for the CSV's `kind` column.

    `same_shift` is how many misplaced citations share this one's book, chapter
    and verse offset. A reference one verse off in a chapter where that happens
    repeatedly is the EDITION'S numbering, not a misprint: 17 in Jeremiah 31,
    8 in I Samuel 24, 7 in Exodus 20, 4 in I Chronicles 12. The printed note is
    right by its own numbering; the proposed ref is still the one a Sefaria link
    needs. Read by eye on 2026-09-14 (item 0FM): the CSV had labelled 37 such
    rows as a one-letter confusion (`א->ב`), which adjacent numerals are not."""
    (cb, c1, v1), (_pb, c2, v2) = cited, proposed
    if c1 == c2 and abs(v2 - v1) == 1:
        return "edition numbering" if same_shift > 1 else "off by one"
    return "misprint"


def suspects_in_run(flat, start, end, vwords):
    """Words with a MATCHING neighbour on both sides that are absent from the verse.

    Both sides is the whole discipline. A word that merely fails to appear in the
    verse is not evidence - most of the book is Ibn Janah's prose and none of it
    is in any verse. What carries information is a gap INSIDE a run that
    otherwise reproduces the verse: `רמה ונוש עפר` against `רמה וגוש עפר` pins
    `ונוש` exactly, because the words on either side are the verse's own.
    Requiring a match on both sides also drops the lead-in - `כמו שנאמר`,
    `בעבור אמרו` - which sits before the quotation rather than inside it, and
    which a run grown backwards will otherwise swallow.
    """
    hit = [matches(w, vwords) for w, _t in flat[start:end]]
    out = []
    for k in range(1, len(hit) - 1):
        # IMMEDIATE neighbours, not "somewhere to the left and right". A run grown
        # backwards reaches past the start of the quotation into Ibn Janah's
        # lead-in - `וכמהו`, `כמו שאמר`, `באמרו` - and one accidental match
        # further left is enough to make every one of those look enclosed. The
        # word before and the word after must BOTH be the verse's own.
        if not hit[k] and hit[k - 1] and hit[k + 1]:
            out.append((start + k, flat[start + k][0]))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--footnotes", required=True)
    ap.add_argument("--tanakh", default=os.path.join(os.path.dirname(_HERE),
                                                     "sefaria_reference_corpus", "raw"))
    ap.add_argument("--min-anchor", type=int, default=3,
                    help="matching words the run needs before its misses are reported")
    ap.add_argument("--max-window", type=int, default=12,
                    help="how far back from the marker a quotation may reach")
    ap.add_argument("--find-better", action="store_true",
                    help="for citations whose quotation does not corroborate, "
                         "search the cited book for the verse it actually matches")
    ap.add_argument("--csv", help="write the misplaced citations as CSV, the form "
                                  "a maintainer can triage in a spreadsheet and "
                                  "join back to their own records")
    ap.add_argument("--review", help="citation_review.json: a verdict per CSV row read by "
                                     "eye, applied when the CSV is written (item 0FM)")
    ap.add_argument("--out")
    ap.add_argument("--show", type=int, default=15)
    args = ap.parse_args()

    with open(os.path.expanduser(args.footnotes), encoding="utf-8") as fh:
        data = json.load(fh)
    tanakh = Tanakh(args.tanakh)

    stat = collections.Counter()
    rows, misplaced = [], []
    for root, info in data.items():
        if not info.get("notes"):
            continue
        flat = flatten(info["tokens"])
        at = {}
        for i, (_w, tok) in enumerate(flat):
            at.setdefault(tok, i)
        def word_at(tok_i):
            while tok_i not in at and tok_i < len(info["tokens"]):
                tok_i += 1
            return at.get(tok_i, len(flat))
        marks = entry_refs(info)
        prev_end = 0
        for pos, ref, note in marks:
            stat["citations"] += 1
            end = word_at(pos)
            if not ref:
                stat["citation did not parse"] += 1
                prev_end = end
                continue
            book, ch, v = ref
            text = tanakh.verse(book, ch, v)
            if not text:
                stat["verse not in reference corpus"] += 1
                prev_end = end
                continue
            vw = verse_words(text)
            floor = max(prev_end, end - args.max_window, 0)
            # grow the run backwards while the words keep matching the verse
            i, misses, matched, start = end - 1, 0, 0, end
            while i >= floor:
                if matches(flat[i][0], vw):
                    matched += 1
                    start = i
                elif misses < 2:
                    misses += 1
                    start = i
                else:
                    break
                i -= 1
            prev_end = end
            if matched < args.min_anchor:
                stat["quotation did not corroborate"] += 1
                if args.find_better:
                    # WHERE ELSE COULD THIS QUOTATION BE? A citation that does not
                    # corroborate is either a note on prose (no quotation to
                    # check), or a reference pointing at the wrong verse. Only the
                    # second is actionable, and searching the cited BOOK separates
                    # them: if the words before the marker reproduce a different
                    # verse of the same book, the reference is misplaced and the
                    # right one can be named.
                    # BOUNDED BY THE PREVIOUS MARKER. Without the floor the
                    # window reaches back over the quotation before this one and
                    # then "finds" that quotation's verse, reporting a correct
                    # citation as misplaced: `ואבדתם את שמם מן המקום ההוא` +
                    # `אשריך ישראל` are two quotations with two notes, and only
                    # the second belongs to this marker.
                    run = [w for w, _t in flat[max(floor, end - 8):end]]
                    best = None
                    chapters = tanakh._book(book) or []
                    for ci, chap in enumerate(chapters, 1):
                        if not isinstance(chap, list):
                            continue
                        for vi, vt in enumerate(chap, 1):
                            if not isinstance(vt, str):
                                continue
                            vws = verse_words(vt)
                            hitn = sum(1 for w in run if matches(w, vws))
                            if best is None or hitn > best[0]:
                                best = (hitn, ci, vi)
                    span_end = VERSE_SPAN.get((book, ch, v), v)
                    in_range = best and best[1] == ch and v <= best[2] <= (span_end or v)
                    if best and ends_in_cited(flat, floor, end, vw,
                                              verse_words(chapters[best[1] - 1][best[2] - 1])):
                        stat["quotation ends in the cited verse"] += 1
                    elif (best and best[0] >= args.min_anchor + 1
                            and (best[1], best[2]) != (ch, v) and not in_range):
                        stat["citation points elsewhere"] += 1
                        misplaced.append({
                            "root": root, "note": note,
                            "cited": f"{book} {ch}:{v}",
                            "quotation": " ".join(run),
                            "matches": best[0],
                            "actually": f"{book} {best[1]}:{best[2]}",
                            "sefaria": "https://www.sefaria.org/{}.{}.{}".format(
                                book.replace(" ", "_"), best[1], best[2])})
                continue
            stat["quotation verified"] += 1
            bad = suspects_in_run(flat, start, end, vw)
            for i, w in bad:
                stat["suspect words"] += 1
                rows.append({
                    "root": root, "word": w, "position": i,
                    "quotation": " ".join(x for x, _t in flat[start:end]),
                    "note": note, "verse": f"{book} {ch}:{v}",
                    "anchor_words": matched,
                    "sefaria": "https://www.sefaria.org/{}.{}.{}".format(
                        book.replace(" ", "_"), ch, v)})

    n = stat["citations"]
    print(f"  citations                     {n:,}")
    for k in ("citation did not parse", "verse not in reference corpus",
              "quotation did not corroborate", "quotation verified"):
        print(f"    {k:<32} {stat[k]:6,}   {100.0 * stat[k] / max(1, n):5.1f}%")
    print(f"  suspect words inside verified quotations   {stat['suspect words']:,}")
    if args.find_better:
        print(f"  citations whose quotation matches a DIFFERENT verse of the "
              f"same book: {stat['citation points elsewhere']:,}")
    print()
    for r in rows[:args.show]:
        print(f"  {iso(r['root']):<8} {iso(r['word'])}")
        print(f"      in: {iso(r['quotation'])}")
        print(f"      {iso(r['note'])}  {r['sefaria']}")
    if args.csv and misplaced:
        V = [(400,"ת"),(300,"ש"),(200,"ר"),(100,"ק"),(90,"צ"),(80,"פ"),(70,"ע"),
             (60,"ס"),(50,"נ"),(40,"מ"),(30,"ל"),(20,"כ"),(10,"י"),(9,"ט"),(8,"ח"),
             (7,"ז"),(6,"ו"),(5,"ה"),(4,"ד"),(3,"ג"),(2,"ב"),(1,"א")]
        def heb(n):
            if n == 15: return "טו"
            if n == 16: return "טז"
            out = ""
            for val, ch_ in V:
                while n >= val:
                    out += ch_
                    n -= val
            return out
        def one_letter(a, b):
            if len(a) != len(b): return ""
            d = [(x, y) for x, y in zip(a, b) if x != y]
            return f"{d[0][0]}->{d[0][1]}" if len(d) == 1 else ""
        import csv as _csv
        ref3 = lambda s: (s.rsplit(" ", 1)[0], *(int(x) for x in s.rsplit(" ", 1)[1].split(":")))
        shifts = collections.Counter()
        for r in misplaced:
            (b, c1, v1), (_b, c2, v2) = ref3(r["cited"]), ref3(r["actually"])
            if c1 == c2:
                shifts[(b, c1, v2 - v1)] += 1
        review = {}
        if args.review:
            with open(os.path.expanduser(args.review), encoding="utf-8") as fh:
                for v in json.load(fh)["rows"]:
                    review[(v["headword"], v["note_as_printed"], v["cited_ref"], v["quotation"])] = v
        kinds, dropped = collections.Counter(), 0
        with open(os.path.expanduser(args.csv), "w", encoding="utf-8", newline="") as fh:
            w = _csv.writer(fh)
            w.writerow(["headword", "note_as_printed", "cited_ref", "proposed_ref",
                        "matching_words", "verse_delta", "kind", "single_letter_confusion",
                        "checked_by_eye", "why", "quotation", "sefaria_url"])
            for r in sorted(misplaced, key=lambda x: -x["matches"]):
                (cb, c1, v1), (ab, c2, v2) = ref3(r["cited"]), ref3(r["actually"])
                delta = (v2 - v1) if c1 == c2 else ""
                kind = citation_kind((cb, c1, v1), (ab, c2, v2),
                                     shifts[(cb, c1, v2 - v1)] if c1 == c2 else 0)
                conf = "" if kind == "edition numbering" else (
                    one_letter(heb(v1), heb(v2)) if c1 == c2 else one_letter(heb(c1), heb(c2)))
                proposed, url = r["actually"], r["sefaria"]
                v = review.get((r["root"], r["note"], r["cited"], r["quotation"]))
                if v and v["verdict"] == "not an error":
                    dropped += 1
                    continue
                if v:
                    kind = v["verdict"]
                    if v.get("proposed_ref"):
                        proposed = v["proposed_ref"]
                        pb, pcv = proposed.rsplit(" ", 1)
                        url = "https://www.sefaria.org/{}.{}".format(
                            pb.replace(" ", "_"), pcv.replace(":", "."))
                        conf = ""
                kinds[kind] += 1
                # The headword is this file's only ADDRESS for a row - the
                # maintainer has no dashboard - so write it as their own data
                # writes it, with the final letter finalized. The lookup key
                # above stays folded; only what is shown changes.
                w.writerow([cio.root_display(r["root"]), r["note"], r["cited"], proposed,
                            r["matches"], delta,
                            kind, conf, "yes" if v else "no", (v or {}).get("why", ""),
                            r["quotation"], url])
        print(f"  wrote {args.csv}: {sum(kinds.values())} rows {dict(kinds)}; "
              f"{dropped} left out as read by eye to be no error")

    if args.out:
        out = os.path.expanduser(args.out)
        with open(out, "w", encoding="utf-8") as fh:
            json.dump({"counts": dict(stat), "suspects": rows,
                       "misplaced_citations": misplaced}, fh,
                      ensure_ascii=False, indent=1)
            fh.flush()
            os.fsync(fh.fileno())
        print(f"\n  wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
