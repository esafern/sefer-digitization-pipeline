#!/usr/bin/env python3
"""
tools/build_witness_review_queue.py

Turn `witness_disputes.json` into the queue file the review dashboard reads.

WHY THE DASHBOARD IS EMPTY FOR THIS BOOK. `review_server.py` builds its flag
overlay from `review_queue_part1.json`, which comes from the DocAI-vs-corpus
diff - and for Sefer HaShorashim that diff is vacuous (item `0ER`): the corpus
was BUILT from DocAI, so it cannot disagree with itself. The dashboard would
open, render the scan, highlight nothing, and look like a clean book.

The server does have a second route - `reconstruction_witness_queue.json`,
served as `opcode: "witness"` - and that is what this writes. It was built for
Tesseract-vs-DocAI on Yad Malachi's reconstructed pages, but nothing in the
shape is Tesseract-specific.

WHAT EACH ROW CARRIES (item 0GC, reviewer 2026-09-13):

  docai_reading       OUR OCR - read from the frozen OCR baseline through the
                      stable word id, so it stays DocAI's after rulings change
                      the master. Falls back to the master word, and says so in
                      `docai_reading_source`, when no baseline exists.
  master_reading      what part1.json holds at that position now.
  tesseract_reading   the witness's reading (the key name is historical).
  corrected_reading   the witness's own CORRECTED text at that position, for an
                      entry it has reviewed (`--corrected`); `entry_reviewed`
                      says whether it has.

TIERS SAY WHAT THE DISAGREEMENT IS, NOT A BLANKET CLAIM. Until 2026-09-13 the
last tier was the fallback for every row where OUR word was in the lexicon, and
its note told the reviewer "both readings are real Hebrew words" - including for
`טתאוה`, which is not. Of its 502 rows, 272 were the same word spelled with or
without a vav/yod, 11 were a footnote numeral read into our word, 16 were their
markup, and 203 were genuinely different readings. Each is its own tier now, and
each tier's agreement with the witness's corrected text is MEASURED on the
reviewed entries and written into the file (`tier_stats`) for the dashboard to
state, instead of a hardcoded rate that went stale on the first rebuild.

Usage:
  SEFER_CORPUS_ROOT=~/work/hashorashim python3 tools/build_witness_review_queue.py \\
      --disputes ~/work/hashorashim/witness_disputes.json \\
      --witness-name "Sefaria (Ibn Janah digitization)" --witness-accuracy 0.992 \\
      --corrected Sefaria=~/work/hashorashim/gold100_text.json \\
      --out-name reconstruction_witness_queue.json
"""

import argparse
import collections
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
import word_identity as wid  # noqa: E402
# The ONE alignment, shared with the disputes builder - a second copy of it here
# would drift from the positions the queue is keyed on (Lesson 13).
from build_witness_disputes import BRACKET, group_disputes, root_groups  # noqa: E402
import scan_alignment as sa  # noqa: E402

HEB = re.compile(r"[א-ת]")


def letters(text):
    """Hebrew letters only - what a reading IS, with markup and points gone."""
    return "".join(HEB.findall(unicodedata.normalize("NFKC", text or "")))


def load_lexicon():
    path = cio.LEXICON_PATH
    if not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8") as fh:
        return {l.strip() for l in fh if l.strip()}


def only_vav_yod(a, b):
    """Do two readings differ ONLY by inserted vav/yod - one word, two spellings?"""
    a, b = letters(a), letters(b)
    if a == b or not a or not b or abs(len(a) - len(b)) > 2:
        return False
    short, long_ = (a, b) if len(a) < len(b) else (b, a)
    i, extra = 0, []
    for ch in long_:
        if i < len(short) and short[i] == ch:
            i += 1
        else:
            extra.append(ch)
    return i == len(short) and all(c in "וי" for c in extra)


def _subsequence(short, long_):
    """Is `short` what is left of `long_` after deleting some of its letters?"""
    it = iter(long_)
    return all(c in it for c in short)


def tier_for(ours, theirs, lexicon, dispute_class=None, ours_raw="", theirs_raw=""):
    """Which review tier a disagreement belongs in - named for what it IS.

    `ours`/`theirs` are letters-only word lists (for the lexicon); the `_raw`
    strings are the readings as stored (for markup and spelling checks). The
    order matters: the specific explanations are tested before the lexicon
    buckets, so a row is described by the most informative true statement.
    """
    ow = [w for w in ours if w]
    tw = [w for w in theirs if w]
    if not ow or not tw:
        return "one_side_empty"
    # A FOOTNOTE MARKER READ INTO OUR WORD: ours is theirs plus one or two
    # trailing characters. This edition prints superscript note markers - digits,
    # and a small raised mark that is not a digit - hard against the word, and
    # DocAI reads them as letters: `אַבִּ` + superscript 3 -> `אַבְּן` (klal 1
    # w37, reviewer 2026-09-13). The old rule caught only a trailing yod/vav/
    # quote. Checked BY EYE on 2026-09-13 over all 73 queue rows of this shape:
    # about 59 show a marker after the word; the rest are genuine readings
    # (`בחסרונו`, `כולהו`) or a geresh read as yod (`נאי`). A triage label, not
    # a verdict - one signal (Lesson 9).
    ol, tl = letters(ours_raw), letters(theirs_raw)
    if dispute_class == "footnote_numeral" or (
            tl and ol.startswith(tl) and 1 <= len(ol) - len(tl) <= 2):
        return "C_footnote_marker"
    if letters(ours_raw) == letters(theirs_raw):
        return "C_markup"
    # THEIR BRACKETED LETTERS (item 0GN). This edition prints its own
    # emendations in square brackets. Here their reading carries a bracket and
    # has every letter of ours plus more. The question is whether those letters
    # are printed, not how the word is spelled: `[ו]יש` read as `יש` is a
    # printed vav our OCR dropped, and the vav/yod test below would file it as
    # a spelling variant. (Theirs is the longer one because equal letters
    # returned C_markup above.)
    if BRACKET.search(theirs_raw) and _subsequence(ol, tl):
        return "B_bracketed_letters"
    if len(ow) == 1 and len(tw) == 1 and len(ow[0]) == len(tw[0]):
        diff = [(a, b) for a, b in zip(ow[0], tw[0]) if a != b]
        if len(diff) == 1 and set(diff[0]) == {"נ", "ג"}:
            return "A_nun_gimel"
    ours_nonword = any(w not in lexicon for w in ow)
    theirs_word = all(w in lexicon for w in tw)
    if ours_nonword and theirs_word:
        return "A_ours_not_a_word"
    if only_vav_yod(ours_raw, theirs_raw):
        return "C_spelling_vav_yod"
    if ours_nonword:
        return "B_ours_unattested"
    if not theirs_word:
        return "C_theirs_unattested"
    return "C_both_attested"


def page_tokens(page):
    path = os.path.join(cio.DOCAI_DIR, f"page_{page}.json")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def entry_token_offsets(kid, start_page, regions, cache):
    """{page: letter-bearing tokens on the entry's EARLIER pages}.

    `docai_token_index` is written ENTRY-relative - this offset plus the index on
    the page - so two rows of one entry on different pages can never share it.
    The server keys witness rows AND their rulings by (klal_id,
    docai_token_index) with no page; once rows sat on their words' own pages
    (finding 2), (132, 138) existed on both p99 and p100 and review_data's guard
    failed every entry with HTTP 500 (item 0GD, 2026-09-14). The page-relative
    index the context endpoint needs travels separately as `page_token_index`.
    """
    pages = sorted(set(sa.klal_all_pages(kid, regions) or []) | {start_page})
    out, running = {}, 0
    for pg in pages:
        out[pg] = running
        if pg not in cache:
            cache[pg] = page_tokens(pg)
        running += sum(1 for t in cache[pg] if cio.hebrew_letters_only(t["text"]))
    return out


def corrected_positions(klalim, corrected_path):
    """(reviewed klal ids, {klal_id: {word_index: corrected reading}}).

    Aligned with the SAME function the disputes builder uses, so the positions
    are the queue's own. A position with no entry here, in a reviewed entry, is
    one where the corrected text agrees with ours. Multi-word spans are keyed at
    their first word; a row that overlaps a span's tail reads as agreement,
    which is an approximation and says so.
    """
    with open(os.path.expanduser(corrected_path), encoding="utf-8") as fh:
        corr = json.load(fh)
    by_key = {cio.root_key(r): (v if isinstance(v, str) else " ".join(v))
              for r, v in corr.items()}
    reviewed, spans = set(), {}
    # A homograph pair shares ONE corrected text; align the pair against it
    # jointly, as the disputes builder does (code review 2026-09-13, finding 3).
    for key, entries in root_groups(klalim).items():
        if key not in by_key:
            continue
        for k in entries:
            reviewed.add(k["klal_id"])
            spans.setdefault(k["klal_id"], {})
        for k, idx, _tag, _cspan, wspan in group_disputes(entries, by_key[key]):
            spans[k["klal_id"]].setdefault(idx, " ".join(wspan))
    return reviewed, spans


CORRECTION_ONLY = "their_correction_only"


def correction_only_disputes(klalim, corrected_path, witness_path):
    """(rows shaped as disputes, count with no word of ours to anchor to).

    Their corrections at words where our OCR reads what THEIR OCR read, so no
    dispute exists there and, until this, no row: the reviewer could not see the
    correction at all (item 0GI; reviewer 2026-09-14 on entry 69 w23, "i don't
    see sef. correction"). Taken from measure_correction_overlap.compare(), the
    three-way alignment item 0GH measured with - a reading correction whose
    status is SHARED - and shaped as disputes so the main loop anchors them like
    any other row. A correction that inserts a word both OCRs lack has no word
    of ours to anchor to; it is counted, not served.
    """
    import measure_correction_overlap as mco
    with open(os.path.expanduser(corrected_path), encoding="utf-8") as fh:
        corrected = mco.join_homograph_halves(json.load(fh))
    with open(os.path.expanduser(witness_path), encoding="utf-8") as fh:
        witness = {cio.root_key(k): v for k, v in json.load(fh).items()}
    rows, _stats = mco.compare(root_groups(klalim), corrected, witness)
    pages = {k["klal_id"]: k.get("page") for k in klalim}
    out, unanchorable = [], 0
    for r in rows:
        if r["kind"] != "reading" or r["status"] != "SHARED":
            continue
        if not r["ours"]:
            unanchorable += 1
            continue
        out.append({"klal_id": r["klal_id"], "word_index": r["word_index"],
                    "page": pages.get(r["klal_id"]), "root": r["root"],
                    "corpus": r["ours"], "witness_reading": r["their_ocr"],
                    "their_corrected": r["their_corrected"], "class": CORRECTION_ONLY})
    return out, unanchorable


def verse_record(v, ours, theirs):
    """The cited verse for one row, shaped for the panel - or None.

    `spelling_only` is the part that matters most. The Masoretic text is
    evidence about a LETTER (klal 21 w127: the verse reads `באדם`, and so does
    the page), not about how this edition spells a word (w128: the verse has
    `לעלם`, the page prints `לעולם`). Of the verse tool's 547 THEIRS verdicts on
    2026-09-14, 379 differed only by a vav/yod - shown as a verdict, they would
    have pushed the Bible's spelling onto this printing (Lesson 38).
    """
    if not v:
        return None
    ref = f"{v['book']} {v['chapter']}" + (f":{v['verse']}" if v.get("verse") else "")
    return {"ref": ref, "url": v.get("sefaria"), "note": v.get("note"),
            "text": v.get("verse_text"), "verdict": v.get("verdict"),
            "corroboration": v.get("corroboration"), "quotation": v.get("quotation"),
            "spelling_only": only_vav_yod(ours, theirs)}


def load_baseline():
    path = cio.repo_path(cio.OCR_BASELINE_NAME)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh).get("entries") or {}


def ocr_reading(baseline, state, klal_id, word_index, n_words):
    """Our OCR's reading of the master word at `word_index`, via its stable id."""
    if baseline is None or word_index is None:
        return None
    e = baseline.get(str(klal_id))
    word_id = wid.id_at(state, klal_id, word_index)
    if not e or word_id is None or word_id not in e["word_ids"]:
        return None
    j = e["word_ids"].index(word_id)
    return " ".join(e["words"][j:j + max(1, n_words)])


def corrected_status(ours, theirs, corrected):
    """What the witness's CORRECTOR did at this position, by letters.

    "unchanged" is NOT agreement. A word the corrector never touched reads the
    same in both of their layers whether or not anyone checked it against the
    page, so it cannot disagree with their OCR and carries no evidence either way
    (Lesson 25 A SIGNAL THAT CANNOT DISAGREE; reviewer 2026-09-13: "I suspect
    those are words they did *not* correct"). Only a CHANGE is a signal - and
    where they changed a disputed word, it was to OUR reading 28 times in 32
    (item 0GC).
    """
    o, t, c = letters(ours), letters(theirs), letters(corrected)
    if o == t:
        # Both OCRs read the same letters. If their corrector then changed them,
        # that is not markup: both engines misread one piece of ink, or the
        # correction departs from the page (item 0GI - entry 69 w23: both read
        # `גמרה`, the page prints `גמרה`, the correction says `גרמה`). It was
        # reported as "same_letters", and a test pinned it that way.
        return "changed_from_both" if c != t else "same_letters"
    if c == t:
        # Same LETTERS as their OCR - but a corrector who moved a comma or a
        # space did touch the word, and the reviewer sees two different strings.
        # Calling that "unchanged" was false on screen (reviewer 2026-09-13,
        # klal 18 w8: their OCR `רוח,`, corrected `רוח ,`).
        # Compared as the popup SHOWS them - points gone, spacing kept (collapsed):
        # a comma moved off the word is a visible change.
        bare = lambda s: " ".join(cio.strip_points(unicodedata.normalize("NFKC", s or "")).split())
        if bare(corrected) != bare(theirs):
            return "punctuation_only"
        return "unchanged"
    if c == o:
        return "changed_to_ours"
    return "changed_to_other"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--disputes", required=True)
    ap.add_argument("--witness-name", required=True)
    ap.add_argument("--witness-accuracy", type=float, default=None,
                    help="the witness's measured word accuracy, 0-1, for the UI note")
    ap.add_argument("--corrected", default=None, metavar="NAME=PATH",
                    help="the witness's own corrected text, {root: text}, for the "
                         "entries it has reviewed")
    ap.add_argument("--verse-verdicts", default=None,
                    help="tools/adjudicate_against_verse.py output, to show each "
                         "row's cited verse in the panel (item 0GE)")
    ap.add_argument("--witness-text", default=None,
                    help="the witness's raw OCR, {root: text}; with --corrected, also "
                         "serve their corrections at words both OCRs read alike (item 0GI)")
    ap.add_argument("--out-name", default="reconstruction_witness_queue.json")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    with open(os.path.expanduser(args.disputes), encoding="utf-8") as fh:
        raw = json.load(fh)
    disputes = raw["disputes"] if isinstance(raw, dict) else raw

    klalim = cio.load_klalim(cio.PART1_PATH)
    # The master's ACTUAL words. The disputes file stores each span with points
    # deleted, so using it here made every pointed word read as "master text
    # now differs" from our (pointed) OCR - klal 1 w37 said `אבן` against
    # `אַבְּן` when nothing had been applied (item 0GC).
    master_words = {k["klal_id"]: cio.words_of(k) for k in klalim}
    entries_by_id = {k["klal_id"]: k for k in klalim}
    regions = sa.load_regions()
    resolved = {}
    offsets = {}
    corrected_name, reviewed, corr = None, set(), {}
    if args.corrected:
        corrected_name, corrected_path = args.corrected.split("=", 1)
        reviewed, corr = corrected_positions(klalim, corrected_path)
    correction_only, unanchorable = [], 0
    if args.corrected and args.witness_text:
        correction_only, unanchorable = correction_only_disputes(
            klalim, corrected_path, args.witness_text)
    baseline = load_baseline()
    # THE CITED VERSE per row, as EVIDENCE (item 0GE). Keyed on the disputes
    # file's own (klal_id, word_index), which the verse tool read too.
    verses = {}
    if args.verse_verdicts:
        with open(os.path.expanduser(args.verse_verdicts), encoding="utf-8") as fh:
            verses = {(v["klal_id"], v["word_index"]): v for v in json.load(fh)["rows"]}
    state = wid.load() if baseline is not None else None

    lexicon = load_lexicon()
    cache, out = {}, []
    located = ambiguous = missing = by_alignment = 0
    seen, served_correction_only, correction_only_collided = set(), 0, 0
    for d in list(disputes) + correction_only:
        if d.get("bracket_only"):
            continue
        kid = int(d["klal_id"])
        wi = d.get("word_index")
        # THE WORD'S OWN PAGE AND TOKEN, from the alignment the server uses
        # (scan_alignment.word_bboxes_resolved; code review 2026-09-13, finding
        # 2). `d["page"]` is the ENTRY's start page, so a word printed on a
        # continuation page was searched for on the wrong page, and 31 of 823
        # served rows took a same-letter token there.
        if kid not in resolved:
            k = entries_by_id.get(kid)
            resolved[kid] = (sa.word_bboxes_resolved(kid, cio.words_of(k), regions)
                             if k else {})
        bbox, page = resolved[kid].get(wi, (None, None)) if wi is not None else (None, None)
        page = int(page) if page is not None else int(d["page"])
        if page not in cache:
            cache[page] = page_tokens(page)
        toks = cache[page]
        if not toks:
            missing += 1
            continue
        ours = cio.hebrew_letters_only(unicodedata.normalize("NFKC", d["corpus"]))
        if not ours:
            missing += 1
            continue
        # INDEX IN THE SERVER'S TOKEN SPACE, NOT THE RAW PAGE. The dashboard's
        # context endpoint (review_server.api_witness_context) and every
        # witness-decision lookup index `docai_token_index` into the page's
        # LETTER-BEARING tokens only - punctuation-only tokens such as the
        # heading's `.` are dropped first. The first version of this file
        # indexed the raw page, so on p58 two periods shifted the bracket from
        # `הנחלי` to `[דשא]`, two words later: the reviewer saw the wrong word
        # highlighted in the context text while the scan box, drawn from the
        # raw token's bbox, was correct - the worst kind of mismatch, because
        # each half looks right on its own.
        toks = [t for t in toks if cio.hebrew_letters_only(t["text"])]
        if bbox is not None:
            # The alignment names the token, so a word repeated on its page is
            # still anchored to ITS occurrence.
            hits = [i for i, t in enumerate(toks)
                    if (t["x1"], t["y1"], t["x2"], t["y2"])
                    == (bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"])]
            by_alignment += 1 if len(hits) == 1 else 0
        else:
            # No aligned token: fall back to letters, but demand ONE match across
            # ALL of the entry's pages, not merely the start page.
            found = []
            for pg in (sa.klal_all_pages(kid, regions) or [page]):
                if pg not in cache:
                    cache[pg] = page_tokens(pg)
                lt = [t for t in cache[pg] if cio.hebrew_letters_only(t["text"])]
                found += [(pg, i, lt) for i, t in enumerate(lt)
                          if cio.hebrew_letters_only(t["text"]) == ours]
            if len(found) == 1:
                page, i0, toks = found[0]
                hits = [i0]
            else:
                hits = [None] * len(found)
        if len(hits) != 1:
            # A repeated word cannot be anchored to ONE token, and the server
            # matches items by (klal_id, docai_token_index) alone - guessing here
            # would attach a reviewer's ruling to the wrong occurrence.
            ambiguous += 1 if hits else 0
            missing += 0 if hits else 1
            continue
        i = hits[0]
        t = toks[i]
        located += 1
        kid = int(d["klal_id"])
        wi = d.get("word_index")
        n_words = len(d["corpus"].split())
        if kid not in offsets:
            offsets[kid] = entry_token_offsets(kid, int(d["page"]), regions, cache)
        if page not in offsets[kid]:
            raise SystemExit(f"entry {kid}: page {page} is not one of its pages "
                             f"{sorted(offsets[kid])} - refusing to write an index that "
                             f"could collide")
        ocr = ocr_reading(baseline, state, kid, wi, n_words)
        mw = master_words.get(kid)
        master = (" ".join(mw[wi:wi + max(1, n_words)])
                  if mw is not None and wi is not None else d["corpus"])
        entry_reviewed = kid in reviewed
        corrected = None
        if entry_reviewed:
            corrected = d.get("their_corrected") or corr.get(kid, {}).get(wi, d["corpus"])
        key = (kid, offsets[kid][page] + i)
        if d.get("class") == CORRECTION_ONLY:
            # A dispute already on this token wins; a second row on one token
            # would make the server's key guard refuse the whole entry.
            if key in seen:
                correction_only_collided += 1
                continue
            served_correction_only += 1
        seen.add(key)
        out.append({
            "klal_id": kid,
            "docai_token_index": offsets[kid][page] + i,   # entry-relative, unique per entry
            "page_token_index": i,                          # index on `page`, for the context endpoint
            "word_index": wi,
            "page": page,
            "bbox": {k: t[k] for k in ("x1", "y1", "x2", "y2")},
            "docai_reading": ocr if ocr is not None else master,
            "docai_reading_source": "ocr_baseline" if ocr is not None else "master",
            "master_reading": master,
            "tesseract_reading": d["witness_reading"],
            "witness_reading": d["witness_reading"],
            "witness_name": args.witness_name,
            # PER ROW, because review_server.py reads it per row and the panel's
            # fallback when it is missing is Tesseract's "16 of 419 (3.8%) ...
            # not a competing reading" - said of a 99.2% witness (item 0GC).
            "witness_accuracy": args.witness_accuracy,
            "corrected_name": corrected_name,
            "entry_reviewed": entry_reviewed,
            "corrected_reading": corrected,
            "corrected_status": (corrected_status(d["corpus"], d["witness_reading"], corrected)
                                 if entry_reviewed else None),
            "verse": verse_record(verses.get((kid, wi)), d["corpus"], d["witness_reading"]),
            "tier": (CORRECTION_ONLY if d.get("class") == CORRECTION_ONLY else
                     tier_for(cio.hebrew_words(unicodedata.normalize("NFKC", d["corpus"])),
                              cio.hebrew_words(unicodedata.normalize("NFKC", d["witness_reading"])),
                              lexicon, d.get("class"), d["corpus"], d["witness_reading"])),
            "dispute_class": d.get("class"),
            "vision_selected": None,
            "vision_transcription": None,
            "vision_confidence": None,
        })

    # MEASURED per tier, on the rows that fall in entries the witness reviewed.
    tier_stats = collections.defaultdict(collections.Counter)
    for w in out:
        s = tier_stats[w["tier"]]
        s["rows"] += 1
        if w["entry_reviewed"]:
            s["reviewed"] += 1
            s[w["corrected_status"]] += 1

    doc = {
        "what_this_is": "Positions where the corpus and an independent witness "
                        "read differently, shaped for review_server.py's witness "
                        "route. Nothing here says which is right.",
        "witness_name": args.witness_name,
        "witness_word_accuracy": args.witness_accuracy,
        "corrected_name": corrected_name,
        "reviewed_entries": len(reviewed),
        "tier_stats": {k: dict(v) for k, v in tier_stats.items()},
        "tier_stats_note": "Per tier: rows in total, rows inside entries the witness "
                           "has reviewed, and there what its corrector did: left its "
                           "OCR unchanged (no evidence either way), changed it to our "
                           "reading, or changed it to something else.",
        "ocr_baseline": baseline is not None,
        "vision_verdicts_present": False,
        "warning": "review_data.load_witness_queue filters by vision verdict, a "
                   "cut calibrated on a 3.8%-accurate witness. This witness is "
                   "far more accurate and the vision pass scores 18% on this "
                   "book's dominant error class (item 0FQ). Serving this file "
                   "through that filter would hide most real corrections.",
        "queue": out,
    }
    print(f"  disputes in            {len(disputes):,}")
    print(f"  anchored to one token  {located:,}  ({by_alignment:,} by the word alignment)")
    print(f"  word repeats on page   {ambiguous:,}  (cannot be anchored safely)")
    print(f"  no usable token        {missing:,}")
    if args.corrected and args.witness_text:
        print(f"  their corrections where both OCRs read alike: {len(correction_only) + unanchorable} "
              f"({served_correction_only} served, {correction_only_collided} on a token a dispute "
              f"already holds, {unanchorable} with no word of ours)")
    print(f"  our OCR from           {'the frozen baseline' if baseline is not None else 'the MASTER (no baseline)'}")
    if verses:
        vv = collections.Counter((w["verse"]["verdict"], w["verse"]["spelling_only"])
                                 for w in out if w.get("verse"))
        print(f"  rows with a cited verse {sum(vv.values()):,}  "
              + ", ".join(f"{v}{' (spelling only)' if so else ''} {n}" for (v, so), n in sorted(vv.items())))
    if corrected_name:
        print(f"  {corrected_name} reviewed {len(reviewed)} of these entries")
    print(f"  {'tier':<22} {'rows':>5} {'reviewed':>8} {'unchanged':>9} "
          f"{'->ours':>6} {'->other':>7} {'<-both':>6}")
    for tier in sorted(tier_stats):
        s = tier_stats[tier]
        print(f"  {tier:<22} {s['rows']:5,} {s['reviewed']:8} {s['unchanged']:9} "
              f"{s['changed_to_ours']:6} {s['changed_to_other']:7} {s['changed_from_both']:6}")
    dest = cio.repo_path(args.out_name)
    if args.dry_run:
        print(f"  would write            {dest}")
        return 0
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
        fh.flush()
        os.fsync(fh.fileno())
    print(f"  wrote                  {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
