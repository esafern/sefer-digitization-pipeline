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
POINTS = re.compile(r"[\u0591-\u05BD\u05BF\u05C1\u05C2\u05C4\u05C5\u05C7]")
PUNCT = re.compile(r"[\u05BE\u05C0\u05C3\u05C6\u05F3\u05F4]")
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

    Points and accents are deleted, punctuation SEPARATES (see POINTS above),
    markup and HTML entities go, and ketiv/qere both survive - a printing may
    legitimately follow either, so both are readings worth matching.

    Final forms are NOT folded. This is running text, and folding finals turns
    `אלהים` into `אלהימ` - the per-purpose normalization rule that cost 16 points
    on both sides of a measurement once already.
    """
    t = ENTITY.sub(" ", TAGS.sub(" ", text))
    t = unicodedata.normalize("NFKC", t)
    t = POINTS.sub("", PUNCT.sub(" ", t))
    return [w for w in NON_HEB.split(t) if w]


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


def parse_citation(note, last_book):
    """`(book chapter, verse)` -> ((book, ch, verse), last_book).

    The comma separates chapter from VERSE, not book from reference. Parsing it
    the other way maps nothing at all - checked against `(במדבר יד, לט)` on
    `ויתאבלו העם`, which is Numbers 14:39 and has no 39:14 to be.

    `שם` is ibid and inherits the running book, which is why this takes and
    returns `last_book` rather than being a pure function of the note.
    """
    m = re.match(r"^\(([^,)]+),\s*([^)]+)\)", note.strip())
    if not m:
        return None, last_book
    head, verse = m.group(1).strip(), m.group(2).strip()
    parts = head.split()
    if not parts:
        return None, last_book
    if parts[0].startswith("שם"):
        book = last_book
        ch = gematria(parts[1]) if len(parts) > 1 else None
    else:
        name = " ".join(parts[:-1]) if len(parts) > 1 else parts[0]
        clean = re.sub(r"[\"'׳״]", "", name).strip()
        book = BOOKS.get(clean) or ABBREV.get(clean) or BOOKS.get(name)
        ch = gematria(parts[-1]) if len(parts) > 1 else None
        if book:
            last_book = book
    if not book or not ch:
        return None, last_book
    return (book, ch, gematria(verse)), last_book


def entry_refs(info):
    """[(anchor position, ref or None)] for one entry, ibid resolved in order."""
    out, last = [], None
    for pos, note in zip(info["anchors"], info.get("notes", [])):
        ref, last = parse_citation(note, last)
        out.append((pos, ref, note))
    return out


def find_span(tokens, needle_words, hint):
    """Where does the witness's own reading sit in its own token stream?

    Disputes carry an index into OUR text, and the anchors index THEIRS, so the
    two cannot be compared directly. Locating the witness reading inside the
    witness tokens puts the dispute into anchor space without needing the
    alignment - and when the phrase occurs more than once, the occurrence nearest
    the proportional hint wins rather than the first, which would silently pick
    the wrong quotation in a long entry.
    """
    n = len(needle_words)
    if not n:
        return None
    hits = [i for i in range(len(tokens) - n + 1)
            if all(bare(tokens[i + k]) == needle_words[k] for k in range(n))]
    if not hits:
        return None
    return min(hits, key=lambda i: abs(i - hint))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--disputes", required=True)
    ap.add_argument("--footnotes", required=True)
    ap.add_argument("--tanakh", default=os.path.join(os.path.dirname(_HERE),
                                                     "sefaria_reference_corpus", "raw"))
    ap.add_argument("--min-corroboration", type=float, default=0.5,
                    help="fraction of the quotation's words that must appear in "
                         "the cited verse before the verse may rule")
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

        pos = find_span(info["tokens"], theirs, d.get("word_index", 0))
        if pos is None:
            skipped["witness reading not located"] += 1
            continue

        key = id(info)
        if key not in refs_cache:
            refs_cache[key] = entry_refs(info)
        marks = refs_cache[key]

        after = [(p, r, n) for p, r, n in marks if p > pos]
        if not after:
            skipped["no footnote after the word"] += 1
            continue
        anchor, ref, note = after[0]
        before = [p for p, _, _ in marks if p <= pos]
        start = max(before) if before else 0
        if not ref:
            skipped["citation unparsed"] += 1
            continue

        book, ch, v = ref
        text = tanakh.verse(book, ch, v)
        transposed = False
        if text is None and v:
            skipped["verse not in reference corpus"] += 1
            continue

        quote = words(" ".join(info["tokens"][start:anchor]))
        def corroboration(txt):
            if not txt or not quote:
                return 0.0
            vw = verse_words(txt)
            return sum(1 for w in quote if w in vw) / len(quote)

        score = corroboration(text)
        # The transposed-citation case: try chapter and verse the other way round
        # and take it only if it corroborates decisively better.
        if score < args.min_corroboration and v:
            alt = tanakh.verse(book, v, ch)
            if alt and corroboration(alt) >= max(args.min_corroboration, score + 0.25):
                text, score, transposed = alt, corroboration(alt), True
                ch, v = v, ch

        vw = verse_words(text) if text else set()
        in_ours = any(w in vw for w in ours)
        in_theirs = any(w in vw for w in theirs)
        if score < args.min_corroboration:
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
            "quotation": " ".join(info["tokens"][start:anchor])[-90:],
            "note": note, "book": book, "chapter": ch, "verse": v,
            "transposed_citation": transposed,
            "corroboration": round(score, 3),
            "sefaria": "https://www.sefaria.org/{}.{}{}".format(
                book.replace(" ", "_"), ch, f".{v}" if v else ""),
            "verdict": verdict,
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
                       "min_corroboration": args.min_corroboration,
                       "counts": dict(tally), "rows": rows,
                       "maqaf_artifacts": artifacts}, fh,
                      ensure_ascii=False, indent=1)
            fh.flush()
            os.fsync(fh.fileno())
        print(f"\n  wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
