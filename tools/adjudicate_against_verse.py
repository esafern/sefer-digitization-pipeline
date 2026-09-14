#!/usr/bin/env python3
"""
tools/adjudicate_against_verse.py

Settle a disputed word by looking up the verse it is quoting.

WHY THIS BEATS THE INK. Most of Sefer HaShorashim is biblical quotation, and
Bacher's apparatus says which verse each quotation comes from - 20,450 anchored
citations in the witness (see tools/extract_witness_footnotes.py). So for a
disputed word inside a quotation there is a published text of that exact verse to
check against. That is not a second opinion about the pixels; it is the sentence
the compositor was setting.

IT ALREADY OVERTURNED A VERDICT. On p138 our text reads `ונוש` and the witness
reads `וגוש`. The vision adjudicator chose OURS at 0.95 confidence, reading the
glyph as a nun. Footnote 1 of that entry cites Job 7:5, and the verse reads
`רִמָּה (וגיש) [וְג֣וּשׁ] עָפָר` - gimel in both ketiv and qere, and the entry's
own headword is `גוש`. Ours is a nun/gimel confusion; the witness is right and
the model was wrong. That is Lesson 9 TWO SIGNALS OR NONE with a second signal
that is genuinely independent of the first: vision reads the ink, this reads the
source.

THE CITATION MUST BE CHECKED BEFORE IT IS TRUSTED. A cited verse settles nothing
if the citation points at the wrong verse, and this apparatus contains transposed
references: `ויתאבכו גאות עשן` is Isaiah 9:17, but its note reads
`(ישעיה יז, ט)` - 17:9. Isaiah 17:9 is a real verse, so a naive lookup gets a
real text that simply has nothing to do with the quotation, and BOTH readings
would come back absent - a silent wrong answer rather than a loud one. Every
verdict here is therefore gated on CORROBORATION: enough of the surrounding
quotation must actually appear in the cited verse before the verse is allowed to
rule on the disputed word. Uncorroborated citations are reported separately, and
transposition is tested explicitly so those cases are named rather than dropped.

WHAT IT CANNOT DO. Only quotations have a source; Ibn Janah's own argument has
none. A printing may also depart from the Masoretic text legitimately - an
abbreviated quotation, a variant, a ketiv where Sefaria prints qere - so
`neither` is a real outcome and means the position still needs the ink. This
tool narrows the queue; it does not replace it.

Usage:
  SEFER_CORPUS_ROOT=~/work/hashorashim python3 tools/adjudicate_against_verse.py \
      --disputes ~/work/hashorashim/gold_disputes.json \
      --footnotes ~/work/hashorashim/witness_footnotes.json
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
import corpus_io as cio  # noqa: E402

# Points and accents, to be DELETED. The range deliberately excludes U+05BE
# MAQAF, U+05C0 PASEQ, U+05C3 SOF PASUQ and the gereshayim: those are
# punctuation, not marks on a letter.
#
# THE MAQAF BUG THIS ENCODES. The obvious range `[\u0591-\u05C7]` swallows
# U+05BE, and a maqaf is what JOINS `אֶת־כָּל־הָעַמִּים` in Sefaria's pointed
# text. Deleting it glues three words into `אתכלהעמים`, so the verse's own words
# stop matching anything and the lookup reports the quotation absent from the
# verse it is quoting. It also manufactures disputes: our unpointed text writes
# the same phrase with spaces, so a pure typography difference was being scored
# as a disagreement about letters. Maqaf must SEPARATE, never vanish.
POINTS = cio.HEBREW_POINTS
TAGS = re.compile(r"<[^>]+>")
ENTITY = re.compile(r"&[a-zA-Z]+;|&#\d+;")
NON_HEB = re.compile(r"[^א-ת]+")
FINALS = str.maketrans("ךםןףץ", "כמנפצ")

# Sefaria's own titles, so the emitted URL resolves. Spellings are the ones this
# edition actually prints, abbreviations included.
BOOKS = {
    "בראשית": "Genesis", "שמות": "Exodus", "ויקרא": "Leviticus", "במדבר": "Numbers",
    "דברים": "Deuteronomy", "יהושע": "Joshua", "שופטים": "Judges",
    "שמואל א": "I Samuel", "שמואל ב": "II Samuel", "מלכים א": "I Kings",
    "מלכים ב": "II Kings", "ישעיה": "Isaiah", "ישעיהו": "Isaiah",
    "ירמיה": "Jeremiah", "ירמיהו": "Jeremiah", "יחזקאל": "Ezekiel",
    "הושע": "Hosea", "יואל": "Joel", "עמוס": "Amos", "עובדיה": "Obadiah",
    "יונה": "Jonah", "מיכה": "Micah", "נחום": "Nahum", "חבקוק": "Habakkuk",
    "צפניה": "Zephaniah", "חגי": "Haggai", "זכריה": "Zechariah", "מלאכי": "Malachi",
    "תהלים": "Psalms", "משלי": "Proverbs", "איוב": "Job",
    "שיר השירים": "Song of Songs", "רות": "Ruth", "איכה": "Lamentations",
    "קהלת": "Ecclesiastes", "אסתר": "Esther", "דניאל": "Daniel", "עזרא": "Ezra",
    "נחמיה": "Nehemiah", "דברי הימים א": "I Chronicles",
    "דברי הימים ב": "II Chronicles",
}
# Abbreviated forms, written with gershayim in the print. Keyed after the
# quote marks are stripped, so `שה"ש` and `שהש` both land here.
ABBREV = {
    "שא": "I Samuel", "שב": "II Samuel", "מא": "I Kings", "מב": "II Kings",
    "שהש": "Song of Songs", "דהא": "I Chronicles", "דהב": "II Chronicles",
    "יחזק": "Ezekiel", "ירמי": "Jeremiah", "ישעי": "Isaiah", "בראש": "Genesis",
    "תהל": "Psalms", "דבר": "Deuteronomy",
}
# Books with exactly one chapter, where a citation names only a verse.
SINGLE_CHAPTER = {"Obadiah"}
# (book, chapter, first verse) -> last verse, for citations written as a range.
VERSE_SPAN = {}
# Matched words needed before calling a citation transposed. See the
# transposition branch in main() for why 2 is not enough.
MIN_TRANSPOSE = 4
GEM = dict(zip("אבגדהוזחטיכלמנסעפצקרשת",
               [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 30, 40, 50, 60,
                70, 80, 90, 100, 200, 300, 400]))


def iso(text):
    """Wrap in U+2066 LRI / U+2069 PDI so a terminal cannot reorder it against
    the surrounding ASCII."""
    return f"\u2066{text}\u2069"


def gematria(s):
    s = NON_HEB.sub("", s)
    return sum(GEM.get(c, 0) for c in s) or None


def words(text):
    """Any Hebrew text -> its comparable words, in order.

    Markup and HTML entities go; the rest is corpus_io.hebrew_words(), which is
    where the points-vs-punctuation rule lives. Ketiv AND qere both survive,
    deliberately: a printing may legitimately follow either.

    Final forms are NOT folded. This is running text, and folding finals turns
    `אלהים` into `אלהימ` - the per-purpose normalization rule that cost 16 points
    on both sides of a measurement once already.
    """
    t = ENTITY.sub(" ", TAGS.sub(" ", text))
    return cio.hebrew_words(unicodedata.normalize("NFKC", t))


def bare(word):
    """One token reduced to letters. Empty when the token carries none."""
    w = words(word)
    return w[0] if len(w) == 1 else "".join(w)


def verse_words(text):
    return set(words(text))


class Tanakh:
    def __init__(self, root):
        self.dir = root
        self.cache = {}

    def _book(self, book):
        if book not in self.cache:
            path = os.path.join(self.dir, f"{book}.json")
            data = None
            if os.path.exists(path):
                with open(path, encoding="utf-8") as fh:
                    data = json.load(fh).get("text")
            self.cache[book] = data
        return self.cache[book]

    def verse(self, book, ch, v):
        t = self._book(book)
        if not t or not ch or ch > len(t):
            return None
        chap = t[ch - 1]
        if not isinstance(chap, list):
            return None
        if v is None:
            return " ".join(x for x in chap if isinstance(x, str))
        return chap[v - 1] if 0 < v <= len(chap) and isinstance(chap[v - 1], str) else None


def resolve_book(name):
    """A printed book name -> Sefaria's title, or None.

    Bacher abbreviates by TRUNCATION with a geresh - `ישע'` for ישעיה, `ברא'`
    for בראשית, `שופ'` for שופטים - so an exact-match table misses most of them.
    A truncation is resolved as a unique prefix of a real book name, and only a
    UNIQUE one: `מ` prefixes both מלכים and מיכה and מלאכי, so it resolves to
    nothing rather than to whichever happened to be first. The gershayim
    abbreviations (`שה"ש`, `דה"ב`) are not truncations and stay in their table.
    """
    clean = re.sub(r"[\"'\u05f3\u05f4]", "", name).strip()
    if clean in BOOKS:
        return BOOKS[clean]
    if clean in ABBREV:
        return ABBREV[clean]
    if name in BOOKS:
        return BOOKS[name]
    hits = {v for k, v in BOOKS.items() if k.startswith(clean)} if clean else set()
    return hits.pop() if len(hits) == 1 else None


def parse_citation(note, last_book):
    """`(book chapter, verse)` -> ((book, ch, verse), last_book).

    The comma separates chapter from VERSE, not book from reference. Parsing it
    the other way maps nothing at all - checked against `(במדבר יד, לט)` on
    `ויתאבלו העם`, which is Numbers 14:39 and has no 39:14 to be.

    `שם` is ibid and inherits the running book, which is why this takes and
    returns `last_book` rather than being a pure function of the note.
    """
    body = note.strip()
    m = re.match(r"^\(([^,)]+),\s*([^)]+)\)", body)
    if not m:
        # A SINGLE-CHAPTER BOOK HAS NO COMMA. `(עובדיה ד)` is Obadiah 1:4 - the
        # one number is the verse, because there is only one chapter to name.
        # Parsed as `book chapter` it would be chapter 4 of a book that has one.
        one = re.match(r"^\(([^\d,)]+?)\s+([^,)]+)\)$", body)
        if one:
            bk = resolve_book(one.group(1).strip())
            if bk in SINGLE_CHAPTER:
                v = gematria(one.group(2))
                if v:
                    return (bk, 1, v), (bk, 1, v)
        return None, last_book
    head, verse = m.group(1).strip(), m.group(2).strip()
    parts = head.split()
    if not parts:
        return None, last_book
    if parts[0].startswith("שם"):
        # `שם` inherits the book; `(שם, שם)` inherits the whole reference, which
        # is how the apparatus writes a second note on the same verse - 98 of
        # them, all lost while `שם` in the verse slot was read as a gematria.
        book, ch = last_book, gematria(parts[1]) if len(parts) > 1 else None
        if isinstance(last_book, tuple):
            book, prev_ch, prev_v = last_book
            if len(parts) == 1:
                ch = prev_ch
                if verse.startswith("שם"):
                    return (book, prev_ch, prev_v), last_book
    else:
        name = " ".join(parts[:-1]) if len(parts) > 1 else parts[0]
        book = resolve_book(name)
        ch = gematria(parts[-1]) if len(parts) > 1 else None
    if isinstance(book, tuple):
        book = book[0]
    if not book or not ch:
        return None, last_book
    # A RANGE is one citation over several verses - `(תהלים מ, ח—י)` is
    # Psalms 40:8-10, eleven of them in this apparatus. Collapsing `ח—י` to a
    # single gematria yields verse 18, a real verse that has nothing to do with
    # the quotation, so the citation then looks misplaced when it is exact.
    # Take the first verse; VERSE_SPAN records how far the range runs so a
    # checker can accept a match anywhere inside it.
    rng = re.split(r"[-\u2013\u2014]", verse)
    v = None if verse.startswith("שם") else gematria(rng[0])
    if len(rng) > 1 and v:
        VERSE_SPAN[(book, ch, v)] = gematria(rng[-1]) or v
    if v is None and verse.startswith("שם") and isinstance(last_book, tuple):
        v = last_book[2]
    return (book, ch, v), (book, ch, v)


def entry_refs(info):
    """[(anchor position, ref or None)] for one entry, ibid resolved in order.

    The running state is the whole previous REFERENCE, not just its book, so
    `(שם, שם)` - same chapter and same verse - can be resolved too.
    """
    out, last = [], None
    for pos, note in zip(info["anchors"], info.get("notes", [])):
        ref, last = parse_citation(note, last)
        out.append((pos, ref, note))
    return out


def flatten(tokens):
    """[(word, originating token index)] for an entry.

    A witness token can be more than one word - the text is pointed, so
    `וְלֹא־יִתֹּם` is a single whitespace token holding two. Anchors index the
    TOKEN stream, comparisons need the WORD stream, and this keeps the map
    between them rather than letting the two drift.
    """
    flat = []
    for i, tok in enumerate(tokens):
        for w in words(tok):
            flat.append((w, i))
    return flat


def find_span(flat, needle_words, hint):
    """Where does the witness's own reading sit in its own word stream?

    Disputes carry an index into OUR text and the anchors index THEIRS, so the
    two cannot be compared directly. Locating the witness reading inside the
    witness words puts the dispute into anchor space without needing the
    alignment - and when the phrase occurs more than once, the occurrence
    nearest the proportional hint wins rather than the first, which would
    silently pick the wrong quotation in a long entry.
    """
    n = len(needle_words)
    if not n or n > len(flat):
        return None
    hits = [i for i in range(len(flat) - n + 1)
            if all(flat[i + k][0] == needle_words[k] for k in range(n))]
    if not hits:
        return None
    return min(hits, key=lambda i: abs(i - hint))


def quotation_run(flat, end, vwords, skip, miss_budget=1, floor=0):
    """The quoted run immediately before a footnote marker: (start, matched).

    THE SPAN CANNOT BE "EVERYTHING SINCE THE LAST FOOTNOTE". That was the first
    attempt and it left 77% of cases uncorroborated: between two markers sits
    Ibn Janah's own argument, and a 19-word stretch containing a 4-word
    quotation scores 0.17 against the verse however right the citation is. The
    prose has no source; only the run touching the marker does.

    So the run is grown BACKWARDS from the marker while the words keep appearing
    in the cited verse, with a small miss budget for a printing that abbreviates
    or inflects. The disputed position itself is exempt from the budget - it is
    the thing in question, and if our reading is the wrong one it will not be in
    the verse, which must not be allowed to truncate the very quotation that
    proves it wrong.
    """
    i, misses, matched = end - 1, 0, 0
    start = end
    while i >= floor:
        if i == skip:
            start = i
            i -= 1
            continue
        if flat[i][0] in vwords:
            matched += 1
            start = i
        else:
            misses += 1
            if misses > miss_budget:
                break
            start = i
        i -= 1
    return start, matched


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--disputes", required=True)
    ap.add_argument("--footnotes", required=True)
    ap.add_argument("--tanakh", default=os.path.join(os.path.dirname(_HERE),
                                                     "sefaria_reference_corpus", "raw"))
    ap.add_argument("--min-matched", type=int, default=2,
                    help="how many words of the quoted run must appear in the "
                         "cited verse before the verse may rule on the dispute")
    ap.add_argument("--out")
    ap.add_argument("--show", type=int, default=25)
    args = ap.parse_args()

    with open(os.path.expanduser(args.disputes), encoding="utf-8") as fh:
        raw = json.load(fh)
    disputes = raw["disputes"] if isinstance(raw, dict) else raw
    with open(os.path.expanduser(args.footnotes), encoding="utf-8") as fh:
        witness = json.load(fh)
    tanakh = Tanakh(args.tanakh)

    fold = lambda s: bare(s).translate(FINALS)
    by_root = {fold(k): v for k, v in witness.items()}
    refs_cache = {}

    rows, artifacts = [], []
    skipped = collections.Counter()
    for d in disputes:
        if d.get("editorial"):
            skipped["editorial"] += 1
            continue
        info = by_root.get(fold(d.get("root", "")))
        if not info or not info.get("notes"):
            skipped["no witness entry"] += 1
            continue
        theirs = words(d["witness_reading"])
        ours = words(d["corpus"])
        if not theirs or not ours:
            skipped["nothing to compare"] += 1
            continue
        if theirs == ours:
            # Identical once maqaf separates rather than vanishes: a typography
            # difference between a pointed and an unpointed text, not a dispute.
            skipped["same text (maqaf/space only)"] += 1
            artifacts.append(dict(d))
            continue

        key = id(info)
        if key not in refs_cache:
            refs_cache[key] = (flatten(info["tokens"]), entry_refs(info))
        flat, marks = refs_cache[key]

        pos = find_span(flat, theirs, d.get("word_index", 0))
        if pos is None:
            skipped["witness reading not located"] += 1
            continue

        # Anchors index TOKENS; the run is grown over WORDS. Convert once.
        at = lambda tok_i: next((k for k, (_w, t) in enumerate(flat) if t >= tok_i),
                                len(flat))
        after = [(p, r, n) for p, r, n in marks if at(p) > pos]
        if not after:
            skipped["no footnote after the word"] += 1
            continue
        anchor_tok, ref, note = after[0]
        anchor = at(anchor_tok)
        prev = [at(p) for p, _, _ in marks if at(p) <= pos]
        floor = max(prev) if prev else 0
        if not ref:
            skipped["citation unparsed"] += 1
            continue

        book, ch, v = ref
        text = tanakh.verse(book, ch, v)
        if text is None:
            skipped["verse not in reference corpus"] += 1
            continue

        def run_for(txt):
            vw = verse_words(txt)
            start, matched = quotation_run(flat, anchor, vw, pos, floor=floor)
            return start, matched, vw

        start, matched, vw = run_for(text)
        transposed = False
        # The transposed-citation case: try chapter and verse the other way round
        # and take it only if the quotation corroborates it decisively better.
        if matched < args.min_matched and v:
            alt = tanakh.verse(book, v, ch)
            if alt:
                a_start, a_matched, a_vw = run_for(alt)
                # A HIGH BAR, because the output of this branch is "your citation
                # is wrong" said to the person who made it. Two matched words is
                # not evidence: `(במדבר ה, כב)` on the root אמן is Numbers 5:22,
                # `אָמֵן אָמֵן`, and exactly right - but Numbers 22:5 happens to
                # share two common words with the surrounding run, so a two-word
                # bar reported a correct citation as transposed. Require a run
                # long enough not to happen by chance AND a clear margin.
                if a_matched >= max(MIN_TRANSPOSE, matched + 2):
                    text, start, matched, vw = alt, a_start, a_matched, a_vw
                    ch, v, transposed = v, ch, True

        span = anchor - start
        score = matched / span if span else 0.0
        in_ours = any(w in vw for w in ours)
        in_theirs = any(w in vw for w in theirs)
        if matched < args.min_matched or not (start <= pos < anchor):
            verdict = "uncorroborated"
        elif in_ours and in_theirs:
            verdict = "both"
        elif in_ours:
            verdict = "OURS"
        elif in_theirs:
            verdict = "THEIRS"
        else:
            verdict = "neither"

        rows.append({
            "root": d.get("root"), "page": d.get("page"),
            "word_index": d.get("word_index"), "klal_id": d.get("klal_id"),
            "ours": d["corpus"], "theirs": d["witness_reading"],
            "quotation": " ".join(w for w, _t in flat[start:anchor]),
            "matched": matched,
            "note": note, "book": book, "chapter": ch, "verse": v,
            "transposed_citation": transposed,
            "corroboration": round(score, 3),
            "sefaria": "https://www.sefaria.org/{}.{}{}".format(
                book.replace(" ", "_"), ch, f".{v}" if v else ""),
            "verdict": verdict,
            # The verse itself, pointed, so a reviewer can read it beside the
            # readings (item 0GE); markup and entities stripped for display.
            "verse_text": " ".join(TAGS.sub("", ENTITY.sub(" ", text)).split()),
        })

    tally = collections.Counter(r["verdict"] for r in rows)
    print(f"  disputes examined            {len(disputes):,}")
    for reason, n in skipped.most_common():
        print(f"    skipped: {reason:<28} {n:,}")
    print(f"  reached a cited verse        {len(rows):,}")
    if rows:
        for k in ("OURS", "THEIRS", "both", "neither", "uncorroborated"):
            if tally[k]:
                print(f"     {k:<15} {tally[k]:4d}   {100.0 * tally[k] / len(rows):5.1f}%")
        nt = sum(1 for r in rows if r["transposed_citation"])
        print(f"  transposed citations found   {nt}")
    print()

    if artifacts:
        print(f"  NOT disputes at all: {len(artifacts)} pairs are the same words, "
              f"differing only in maqaf vs space.")
        print()

    decisive = [r for r in rows if r["verdict"] in ("OURS", "THEIRS")]
    for r in decisive[:args.show]:
        # One Hebrew field per line, each wrapped in a directional isolate.
        # Two Hebrew cells side by side in a terminal get laid out right to
        # left, which SWAPS the columns visually while the ASCII headers stay
        # put - a table that reads exactly backwards. It happened once already.
        print(f"  p{r['page']} root {iso(r['root'])}   -> {r['verdict']}")
        print(f"      ours   {iso(r['ours'])}")
        print(f"      theirs {iso(r['theirs'])}")
        print(f"      cite   {iso(r['note'])}  {r['sefaria']}  corrob "
              f"{r['corroboration']:.2f}"
              f"{'  TRANSPOSED' if r['transposed_citation'] else ''}")

    if args.out:
        out = os.path.expanduser(args.out)
        with open(out, "w", encoding="utf-8") as fh:
            json.dump({"what_this_is":
                       "Disputes settled against the verse the witness apparatus "
                       "cites. A verdict is issued only when the surrounding "
                       "quotation actually corroborates the citation.",
                       "min_matched": args.min_matched,
                       "counts": dict(tally), "rows": rows,
                       "maqaf_artifacts": artifacts}, fh,
                      ensure_ascii=False, indent=1)
            fh.flush()
            os.fsync(fh.fileno())
        print(f"\n  wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
