#!/usr/bin/env python3
# [PRODUCTION] Reconstruct klalim whose real text spans MORE THAN ONE page
# boundary - the case scratch/reconstruct_crosspage_v4.py structurally could not
# handle (its predecessor hard-asserts `next_page == page + 1`, and the scoping
# script that fed it wrote `continue  # spans more than one page boundary -
# handle separately`; it never was). See PROJECT-STATUS.md 2026-08-11.
#
# Two things make this different from v4, both deliberate:
#
# 1. APPEND/INSERT, NEVER WHOLESALE REPLACE. v4 rebuilt clean_text from raw
#    docai tokens outright, which was fine when 93% of a klal was missing but is
#    destructive here: 6-25% of each of these klalim is existing text that has
#    already been through months of correction passes. This script keeps every
#    stored word and splices ONLY the missing page(s) into place, so no prior
#    human correction can be lost. The one exception is a trailing catchword
#    (see below), which is page furniture that should never have been stored.
#
# 2. INTERMEDIATE PAGES NEED FURNITURE STRIPPED AT BOTH ENDS. v4 only ever saw
#    a first page (strip its tail) and a last page (strip its head). A page
#    wholly inside a klal has a running header at the top AND a
#    catchword/signature/watermark at the bottom.
#
# Catchword handling: this print repeats the next page's first word at the
# bottom of the current page as a printer's catchword. It is furniture. At every
# junction the duplicate is dropped exactly once, keeping the occurrence that
# belongs to the running text (the one at the START of the next page).
#
# --dry-run (default) writes nothing and prints every junction for inspection.
# --apply writes part1.json. Run ./rebuild_all.sh afterwards.
import argparse
import difflib
import json
import os
import re

REPO = os.path.dirname(os.path.abspath(__file__))
DOCAI_DIR = os.path.join(REPO, "docai_word_boxes")
PART1_PATH = os.path.join(REPO, "part1.json")
TRACE_PATH = os.path.join(REPO, "gematria_trace_part1.json")

BOOK_WORD = "מלאכי"
SINGLE_LETTER_RE = re.compile(r"^[א-ת]$")
WATERMARK = ("Digitized", "by", "Google")
PUNCT = {"'", '"', ":", ".", ")", "(", "*", "•", ","}


def get_page(cache, page):
    if page not in cache:
        cache[page] = json.load(open(os.path.join(DOCAI_DIR, f"page_{page}.json"), encoding="utf-8"))
    return cache[page]


def clean_word(w):
    return "".join(c for c in w if c.isalnum())


# Every token that can legitimately appear in a running header. A fixed
# "book word + 3" offset (v4's approach) is not safe here: page 24's header is
# `יר מלאכי : כללי האלף ۱` - an extra colon token - and page 40's is
# `יך מלאכי כללי הבית יך`, where the repeated folio mark is TWO letters, not the
# single letter v4 tested for. Both slipped header fragments into the body text
# on the first run of this script. Consuming a known vocabulary instead of
# counting tokens handles every header variant in Part 1.
HEADER_VOCAB = {"יד", "יר", "יך", "מלאכי", "כללי",
                "האלף", "הבית", "הגימל", "הדלת", "ההא"}
HEADER_SCAN_LIMIT = 10


def strip_head_header(tokens):
    """Drop the running header ('<folio> יד מלאכי כללי <section> <folio>') from
    a page's start, anchored on the book word and then consuming header
    vocabulary, folio numerals and punctuation until real body text begins."""
    idx = next((i for i, t in enumerate(tokens[:8]) if BOOK_WORD in t["text"]), None)
    if idx is None:
        return 0, "NO_HEADER_FOUND"
    SECTIONS = {"האלף", "הבית", "הגימל", "הדלת", "ההא"}
    HEB = "אבגדהוזחטיכלמנסעפצקרשתךםןףץ"
    i = idx + 1
    eaten = []
    saw_section = False
    took_folio = False
    while i < min(len(tokens), idx + HEADER_SCAN_LIMIT):
        w = tokens[i]["text"].strip()
        cw = clean_word(w)
        is_vocab = cw in HEADER_VOCAB
        is_filler = (not cw) or cw.isdigit() or all(ch not in HEB for ch in cw)
        # A 1-2 letter Hebrew token directly after the section name is the folio
        # numeral (e.g. `יג` on leaf B, `יך` on page 40) - allowed exactly once,
        # and only in that position, so a genuine short body word elsewhere is
        # never eaten.
        is_folio = (saw_section and not took_folio and 1 <= len(cw) <= 2
                    and all(ch in HEB for ch in cw))
        if not (is_vocab or is_filler or is_folio):
            break
        if cw in SECTIONS:
            saw_section = True
        if is_folio and not is_vocab:
            took_folio = True
        eaten.append(w)
        i += 1
    return i, ("clean" if not eaten else f"ate_header:{eaten}")


def strip_tail_furniture(tokens, next_first_word):
    """Drop the Google watermark, then any trailing signature digits/asterisks,
    then the catchword if it matches the next page's first real word."""
    notes = []
    idx = next((i for i, t in enumerate(tokens) if t["text"] == "Digitized"), None)
    if idx is not None:
        trailing = [t["text"] for t in tokens[idx + 3:]]
        tokens = tokens[:idx]
        if trailing:
            notes.append(f"dropped_after_watermark:{trailing}")
    else:
        notes.append("NO_WATERMARK_FOUND")
    changed = True
    while changed and tokens:
        changed = False
        last = tokens[-1]["text"].strip()
        if last.isdigit() or last in ("*", "•"):
            notes.append(f"stripped_signature:{last!r}")
            tokens = tokens[:-1]
            changed = True
        elif next_first_word and difflib.SequenceMatcher(
                None, clean_word(last), clean_word(next_first_word)).ratio() > 0.6:
            notes.append(f"stripped_catchword:{last!r}~{next_first_word!r}")
            tokens = tokens[:-1]
            changed = True
    return tokens, ";".join(notes) if notes else "clean"


def page_body(cache, page, next_first_word):
    """A page that lies wholly inside one klal: strip header AND tail furniture."""
    toks = get_page(cache, page)
    start, hnote = strip_head_header(toks)
    body, tnote = strip_tail_furniture(toks[start:], next_first_word)
    return body, f"head[{hnote}] tail[{tnote}]"


def first_real_word(cache, page, upto=None):
    toks = get_page(cache, page)
    start, _ = strip_head_header(toks)
    seq = toks[start:upto] if upto is not None else toks[start:]
    for t in seq:
        if clean_word(t["text"]):
            return t["text"]
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write part1.json (default is dry-run)")
    ap.add_argument("--klal", type=int, nargs="*", default=[30, 75, 88])
    args = ap.parse_args()

    trace = {x["klal_id"]: x for x in json.load(open(TRACE_PATH, encoding="utf-8"))}
    part1 = json.load(open(PART1_PATH, encoding="utf-8"))
    by_id = {k["klal_id"]: k for k in part1}
    marker_ids = sorted(k for k in trace if trace[k].get("marker_position") is not None)
    cache = {}
    report = []

    for kid in args.klal:
        pos = marker_ids.index(kid)
        nxt = marker_ids[pos + 1]
        x, nx = trace[kid], trace[nxt]
        start_page, end_page = x["page"], nx["page"]
        mids = list(range(start_page + 1, end_page))
        stored = by_id[kid]["clean_text"].split(" ")

        # Two different "first word of the end page" are needed:
        #  - end_first_any: the page's first real word regardless of where the
        #    next klal's marker falls. This is what the previous page's
        #    catchword duplicates, and it must be used for catchword stripping
        #    even when the end page contributes nothing to THIS klal (klal 88:
        #    klal 89's marker sits at token 5, so the end page adds no words,
        #    but page 40's catchword `בעיא` is still furniture and must go).
        #  - end_first_owned: the first word this klal actually takes from the
        #    end page, used to locate a seam in already-stored text.
        end_first_any = first_real_word(cache, end_page)
        end_first_owned = first_real_word(cache, end_page, upto=nx["marker_position"])

        # Build the middle: every wholly-interior page, in order. Each one's
        # catchword points at the NEXT page in the chain.
        middle, notes = [], []
        for i, mp in enumerate(mids):
            nxt_word = first_real_word(cache, mids[i + 1]) if i + 1 < len(mids) else end_first_any
            body, note = page_body(cache, mp, nxt_word)
            middle.extend(t["text"] for t in body)
            notes.append(f"page {mp}: +{len(body)} tok  {note}")

        # Where does the stored text end its FIRST-page contribution? For klal
        # 30/88 that is simply its end. For klal 75 the stored text already
        # contains the final page's contribution appended directly onto the
        # first page's (v4 ran it under the transposed page order and skipped
        # the middle leaf), so the splice point is the seam between them, not
        # the end.
        seam = len(stored)
        if end_first_owned:
            etoks = get_page(cache, end_page)
            ehstart, _ = strip_head_header(etoks)
            live = " ".join(t["text"] for t in etoks[ehstart:nx["marker_position"]])
            for i in range(len(stored) - 1, 0, -1):
                if clean_word(stored[i]) == clean_word(end_first_owned):
                    tailpart = " ".join(stored[i:i + 12])
                    if difflib.SequenceMatcher(None, tailpart, live[:len(tailpart)]).ratio() > 0.7:
                        seam = i
                    break

        head_part, tail_part = stored[:seam], stored[seam:]
        # drop the first page's trailing catchword - it duplicates the first word
        # of what comes next
        first_new = middle[0] if middle else (tail_part[0] if tail_part else None)
        dup = ""
        if head_part and first_new and difflib.SequenceMatcher(
                None, clean_word(head_part[-1]), clean_word(first_new)).ratio() > 0.6:
            dup = f"dropped duplicated catchword {head_part[-1]!r} (real occurrence starts the next page)"
            head_part = head_part[:-1]

        # If the stored text had no final-page part (klal 30/88), add it now.
        if seam == len(stored):
            toks = get_page(cache, end_page)
            hstart, _ = strip_head_header(toks)
            tail_part = [t["text"] for t in toks[hstart:nx["marker_position"]]]
            if hstart >= nx["marker_position"]:
                tail_part = []  # next klal's marker is inside the header: this klal takes nothing here

        new_words = head_part + middle + tail_part
        report.append({
            "klal_id": kid, "path": f"{start_page} -> {mids} -> {end_page}",
            "old": len(stored), "new": len(new_words), "notes": notes, "dup": dup,
            "seam_index": seam if seam != len(stored) else None,
            "j1": " ".join(head_part[-6:]) + "  |||  " + " ".join(middle[:6]),
            "j2": " ".join(middle[-6:]) + "  |||  " + " ".join(tail_part[:6]),
            "text": " ".join(new_words),
        })

    for r in report:
        print(f"\n=== klal {r['klal_id']}  pages {r['path']}   {r['old']} -> {r['new']} words "
              f"(+{r['new']-r['old']}) ===")
        for n in r["notes"]:
            print(f"    {n}")
        if r["seam_index"] is not None:
            print(f"    stored text already contained the final page; splicing at seam word {r['seam_index']}")
        if r["dup"]:
            print(f"    {r['dup']}")
        print(f"    junction 1: {r['j1']}")
        print(f"    junction 2: {r['j2']}")

    if args.apply:
        for r in report:
            by_id[r["klal_id"]]["clean_text"] = r["text"]
        json.dump(part1, open(PART1_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"\nAPPLIED to {PART1_PATH}. Run ./rebuild_all.sh next.")
    else:
        print("\n[DRY RUN] nothing written. Re-run with --apply once the junctions above read correctly.")


if __name__ == "__main__":
    main()
