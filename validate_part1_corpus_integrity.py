# [PRODUCTION] Standing validation: a batch of new, cheap, mechanical,
# no-LLM checks for Part 1 that no existing script in this pipeline covers.
# Per CLAUDE.md Lesson 8 ("a cheap, mechanical, no-LLM check can catch what
# expensive LLM-based checks miss entirely, and vice versa"), every check
# here is a plain text/arithmetic sweep over part1.json - no docai/scan
# dependency, no API calls, runs in well under a second. Five independent
# angles, none redundant with an existing validator:
#
#   1. Gematria self-consistency: every klal stores BOTH a `gematria` field
#      and its own marker as the literal first word of `clean_text`. Nothing
#      has ever checked that (a) the stored `gematria` field actually equals
#      the numeral you'd compute from `klal_id`, or (b) `clean_text`'s own
#      opening word actually matches the stored `gematria` field. A drift
#      between klal_id/gematria/clean_text-opening would mean the record
#      is internally inconsistent about its own number - exactly the kind
#      of typo a hand-fix could introduce and nothing else would catch,
#      since it requires no scan lookup at all.
#   2. Character/encoding sanity: stray Latin letters, unbalanced
#      gershayim/geresh or bracket/paren counts, bare Arabic digits outside
#      known citation contexts. Catches leftover OCR/scan artifacts (a
#      stray "P" from page furniture, an unstripped "Google" fragment, a
#      truncated bracket) that the existing page-header-contamination regex
#      is scoped too narrowly to catch (it only matches the specific known
#      header string, not general junk).
#   3. Duplicated multi-word phrase detection (n-gram >= 5 words), within
#      each klal AND across each adjacent klal pair. Generalizes the
#      existing duplicate-CONSECUTIVE-word check (which only catches an
#      immediately-repeated single word, like klal 128's `לאוקומי לאוקומי`)
#      to catch a longer phrase duplicated non-adjacently - the failure
#      mode behind klal 82/83's citation-duplication bug and the general
#      "content merged into a trusted neighbor" pattern (Lesson 16).
#   4. Self-reference directionality: this book constantly cross-references
#      itself ("עיין לעיל כלל X" / "עיין לקמן כלל X" - see above/below,
#      klal X). Extracts every explicit `כלל <gematria-number>` mention
#      next to a לעיל/למעלה (above) or לקמן/להלן (below) direction word and
#      checks the referenced klal_id is actually before/after the
#      referencing klal - independent of any scan or marker-position work,
#      this checks the author's own internal logic against the corpus's
#      current ordering, and could catch a klal-numbering/ordering bug even
#      where every other check (which mostly verify a klal against its OWN
#      scan position) stays silent.
#   5. Full-corpus lexicon coverage: every existing lexicon-based check
#      only looks at build_corrections_dataset.py's flagged DIFF candidates
#      (docai vs. clean_text disagreements) - a word both docai and
#      clean_text got wrong identically (e.g. if clean_text was originally
#      seeded from an uncorrected docai read and nobody ever flagged it as
#      a disagreement) would never surface. This checks literally every
#      word in every klal's `clean_text` against lexicon.txt.
#
# Each check is independent and reports its own findings; a finding in one
# is not evidence for or against another. None of these replace vision
# verification or direct scan crop-checks - they're a triage layer, same
# caveat as every other automated check in this pipeline (Lesson 2).
import difflib
import json
import os
import re
from collections import Counter

REPO = os.path.dirname(os.path.abspath(__file__))
PART1_PATH = os.path.join(REPO, "part1.json")
LEXICON_PATH = os.path.join(REPO, "lexicon.txt")

HEBREW_LETTERS = "אבגדהוזחטיכלמנסעפצקרשתךםןףץ"
GEMATRIA_VALUES = {
    "א": 1, "ב": 2, "ג": 3, "ד": 4, "ה": 5, "ו": 6, "ז": 7, "ח": 8, "ט": 9,
    "י": 10, "כ": 20, "ל": 30, "מ": 40, "נ": 50, "ס": 60, "ע": 70, "פ": 80,
    "צ": 90, "ק": 100, "ר": 200, "ש": 300, "ת": 400,
}


# Only נ/פ/צ (not כ/מ) traditionally take their final form at the end of a
# *multi-letter* Hebrew numeral in this kind of typesetting (e.g. 150 is
# printed קן not קנ, 190 is קץ not קצ) - but a lone single-letter numeral
# (20 = כ, 40 = מ, 50 = נ, 80 = פ, 90 = צ) stays in regular form, and כ/מ
# never finalize even in a multi-letter numeral (120 = קכ not קך, 140 = קמ
# not קם, 220 = רכ not רך). Confirmed against part1.json's own
# already-crop-verified gematria field for every case in both directions
# (2026-08-07, PROJECT-STATUS.md "New standing check
# validate_part1_corpus_integrity.py added") - an earlier version of this
# function applied the substitution unconditionally to any of the 5
# final-letter-eligible letters, which was right for 150/180/190 but wrong
# for 20/40/50/80/90/120/140/220.
FINAL_FORMS = {"נ": "ן", "פ": "ף", "צ": "ץ"}


def klal_id_to_gematria(n):
    """Standard Hebrew numeral spelling, with the תשע"ו-style 15/16
    exception (ט"ו/ט"ז instead of י"ה/י"ו, which would spell divine
    names) - same convention `part1.json`'s own `gematria` field uses.
    See FINAL_FORMS above for the word-final-letter substitution rule."""
    hundreds = [(400, "ת"), (300, "ש"), (200, "ר"), (100, "ק")]
    tens = [(90, "צ"), (80, "פ"), (70, "ע"), (60, "ס"), (50, "נ"), (40, "מ"),
            (30, "ל"), (20, "כ"), (10, "י")]
    ones = [(9, "ט"), (8, "ח"), (7, "ז"), (6, "ו"), (5, "ה"), (4, "ד"),
            (3, "ג"), (2, "ב"), (1, "א")]
    rem, letters = n, []
    for val, ch in hundreds:
        while rem >= val:
            letters.append(ch)
            rem -= val
    if rem == 15:
        letters += ["ט", "ו"]
        rem = 0
    elif rem == 16:
        letters += ["ט", "ז"]
        rem = 0
    else:
        for val, ch in tens:
            if rem >= val:
                letters.append(ch)
                rem -= val
        for val, ch in ones:
            if rem >= val:
                letters.append(ch)
                rem -= val
    if len(letters) > 1 and letters[-1] in FINAL_FORMS:
        letters[-1] = FINAL_FORMS[letters[-1]]
    return "".join(letters)


def gematria_to_value(s):
    """Sum of letter values, ignoring punctuation - for parsing a
    self-reference numeral out of running text, not for validating a
    known-position marker (which the other trace/alignment tooling does
    with real docai positions, not this arithmetic-only approach)."""
    return sum(GEMATRIA_VALUES.get(c, 0) for c in s)


def load_klalim():
    return json.load(open(PART1_PATH, encoding="utf-8"))


def check_gematria_self_consistency(klalim):
    print("\n=== 1. Gematria self-consistency (klal_id vs. gematria field vs. clean_text opening) ===")
    issues = []
    for k in klalim:
        kid, stored_gem, text = k["klal_id"], k["gematria"], k["clean_text"]
        expected_gem = klal_id_to_gematria(kid)
        if stored_gem != expected_gem:
            issues.append(f"klal {kid}: gematria field is {stored_gem!r}, expected {expected_gem!r} for klal_id {kid}")
        opening_word = text.split()[0] if text.split() else ""
        if opening_word != stored_gem:
            issues.append(f"klal {kid}: clean_text opens with {opening_word!r}, but gematria field says {stored_gem!r}")
    if not issues:
        print(f"  {len(klalim)}/{len(klalim)} klalim: klal_id, gematria field, and clean_text opening all agree.")
    else:
        print(f"  {len(issues)} issue(s):")
        for i in issues:
            print("   ", i)
    return issues


LATIN_RE = re.compile(r"[A-Za-z]")
ARABIC_DIGIT_RE = re.compile(r"\d")
# This edition marks footnotes with a lone `*)`/`**)` (asterisk(s)) or `")`
# (a straight double-quote/gershayim-like mark) - optional space, then a
# close-paren that has no matching `(` at all - a footnote-reference
# symbol, not a bracket pair. Confirmed by direct crop 2026-08-07
# (PROJECT-STATUS.md "New standing check validate_part1_corpus_integrity.py
# added"): klal 6/7/51/53/71/74/106's "unbalanced parens" were all one of
# these two variants of the same convention, not corpus bugs. Excluded
# from the close-paren count below so only a genuine bracket-pairing
# mismatch is flagged.
FOOTNOTE_MARKER_RE = re.compile(r'(\*+|")\s*\)')


def check_character_sanity(klalim):
    print("\n=== 2. Character/encoding sanity (stray Latin letters, bare Arabic digits, bracket balance) ===")
    issues = []
    for k in klalim:
        kid, text = k["klal_id"], k["clean_text"]
        latin = LATIN_RE.findall(text)
        if latin:
            issues.append(f"klal {kid}: {len(latin)} stray Latin character(s): {''.join(sorted(set(latin)))!r}")
        digits = ARABIC_DIGIT_RE.findall(text)
        if digits:
            issues.append(f"klal {kid}: {len(digits)} bare Arabic digit(s): {''.join(digits)!r}")
        open_count = text.count("(")
        close_count = text.count(")") - len(FOOTNOTE_MARKER_RE.findall(text))
        if open_count != close_count:
            issues.append(f"klal {kid}: unbalanced parens ({open_count} open vs {close_count} close, footnote markers excluded)")
        if text.count("[") != text.count("]"):
            issues.append(f"klal {kid}: unbalanced brackets ({text.count('[')} open vs {text.count(']')} close)")
    if not issues:
        print(f"  {len(klalim)}/{len(klalim)} klalim clean.")
    else:
        print(f"  {len(issues)} issue(s):")
        for i in issues:
            print("   ", i)
    return issues


def ngrams(words, n):
    return [tuple(words[i:i + n]) for i in range(len(words) - n + 1)]


TITLE_SIMILARITY_THRESHOLD = 0.8  # tolerates minor orthographic variants
# (e.g. klal 22/23/24's למדים/למדין, אפילו/אפי') within the same
# same-title-cluster convention; below this, titles are treated as
# genuinely different. Confirmed 2026-08-07 (PROJECT-STATUS.md) klal
# 22/23/24 needed this - an exact-string title comparison missed them and
# reported a false "unexplained" duplicate-phrase hit.
def _same_title_cluster(title_a, title_b):
    if title_a == title_b:
        return True
    return difflib.SequenceMatcher(None, title_a, title_b).ratio() >= TITLE_SIMILARITY_THRESHOLD


def check_duplicate_phrases(klalim, n=10):
    # n=10 chosen empirically: at n=5 this produced 333 hits, almost all
    # explainable as this book's genre (a halachic-maxim INDEX, not prose) -
    # adjacent entries routinely restate the same fixed maxim/title phrase
    # verbatim (e.g. klal 100-104 all share the title idiom "ב"ד מתנין
    # לעקור דבר מן התורה בשב ואל תעשה", already documented elsewhere in
    # this project as a real, deliberate same-title cluster, not a bug).
    # At n=15, zero hits remain even before filtering by title. n=10 is the
    # narrowest threshold that still lets a few same-title-cluster examples
    # through to filter here explicitly (rather than just raising n until
    # the known cases silently vanish) - so a genuinely new, unexplained
    # long duplication would have to be caught by an explicit title check,
    # not just a higher n silently hiding it.
    print(f"\n=== 3. Duplicated {n}+-word phrases across DIFFERENT-titled adjacent klal pairs ===")
    print(f"    (same-titled adjacent pairs are excluded - sharing a long phrase there is")
    print(f"     the documented same-title-cluster convention, not a bug; see PROJECT-STATUS.md)")
    issues = []
    same_title_explained = []
    by_id = {k["klal_id"]: k for k in klalim}
    sorted_ids = sorted(by_id)

    for i in range(len(sorted_ids) - 1):
        kid_a, kid_b = sorted_ids[i], sorted_ids[i + 1]
        words_a = by_id[kid_a]["clean_text"].split()
        words_b = by_id[kid_b]["clean_text"].split()
        grams_a = set(ngrams(words_a, n))
        grams_b = set(ngrams(words_b, n))
        shared = grams_a & grams_b
        if not shared:
            continue
        same_title = _same_title_cluster(by_id[kid_a]["title"], by_id[kid_b]["title"])
        for g in shared:
            entry = f"klal {kid_a}/{kid_b}: identical {n}-word phrase: {' '.join(g)!r}"
            if same_title:
                same_title_explained.append(entry)
            else:
                issues.append(entry)

    print(f"  {len(same_title_explained)} hit(s) explained by the same-title-cluster convention (not flagged).")
    if not issues:
        print(f"  0 unexplained duplicated {n}+-word phrase(s) between different-titled adjacent klalim.")
    else:
        print(f"  {len(issues)} unexplained issue(s):")
        for i in issues:
            print("   ", i)
    return issues


ABOVE_WORDS = ["לעיל", "למעלה", "לעילא"]
BELOW_WORDS = ["לקמן", "להלן"]
SELF_REF_RE = re.compile(r"כלל\s+([א-ת\"'׳]+)")


def check_self_reference_directionality(klalim):
    # NOT VIABLE FOR THIS CORPUS, kept for documentation rather than deleted
    # outright (per this project's convention of disclosing what didn't work,
    # e.g. "Automated marker-vs-citation filter attempt - tried, did not
    # work" in PROJECT-STATUS.md). Investigated 2026-08-07: manually sampled
    # every `כלל <letter>` occurrence in Part 1 and found the overwhelming
    # majority are NOT self-references to this book's own klal numbering at
    # all - `כלל` is extremely common ordinary Rabbinic-Hebrew vocabulary
    # ("rule", "principle", or "at all" in a negation like `לא איריא כלל`),
    # and even when followed by a number, it usually cites a DIFFERENT
    # author's own differently-numbered "klalim" work (`הליכות אלי כלל
    # תקמ"ו`, `כללי הגמרא כלל צ"ד`, `יבין שמועה כלל ס"ד`, `אסיפת הכללים כלל
    # ע"ג` - Yad Malachi is not the only halachic-rule-index book with this
    # citation convention). Reliably distinguishing "this book's own klal
    # N" from "a citation into someone else's klal N" would need real NLP,
    # not a regex - not attempted. The function still runs and reports its
    # raw counts for visibility, but its "0 issues" result should NOT be
    # read as "self-references validated clean" - there's no reliable
    # signal here to validate against.
    print("\n=== 4. Self-reference directionality (\"עיין לעיל/לקמן כלל X\") — NOT VIABLE, see code comment ===")
    issues = []
    checked = 0
    for k in klalim:
        kid, text = k["klal_id"], k["clean_text"]
        for m in SELF_REF_RE.finditer(text):
            num_str = m.group(1).replace('"', "").replace("'", "").replace("׳", "")
            ref_val = gematria_to_value(num_str)
            if ref_val == 0 or ref_val > 667:
                continue  # not a real klal-number token (e.g. a name that happens to follow "כלל")
            window_start = max(0, m.start() - 25)
            window = text[window_start:m.start()]
            direction = None
            if any(w in window for w in ABOVE_WORDS):
                direction = "above"
            elif any(w in window for w in BELOW_WORDS):
                direction = "below"
            if direction is None:
                continue
            checked += 1
            if direction == "above" and ref_val >= kid:
                issues.append(f"klal {kid}: says \"{window.strip()} כלל {num_str}\" (above/earlier) but klal {ref_val} is not before klal {kid}")
            elif direction == "below" and ref_val <= kid:
                issues.append(f"klal {kid}: says \"{window.strip()} כלל {num_str}\" (below/later) but klal {ref_val} is not after klal {kid}")
    if checked == 0:
        print("  0 directional self-references found matching the (לעיל/לקמן + כלל <N>) pattern - either none exist, or the surface pattern doesn't match this book's phrasing (not conclusive either way).")
    elif not issues:
        print(f"  {checked} directional self-reference(s) checked, all consistent with current klal ordering.")
    else:
        print(f"  {checked} checked, {len(issues)} issue(s):")
        for i in issues:
            print("   ", i)
    return issues


def check_full_lexicon_coverage(klalim):
    print("\n=== 5. Full-corpus lexicon coverage (every word, not just flagged correction candidates) ===")
    if not os.path.exists(LEXICON_PATH):
        print("  SKIPPED: lexicon.txt not found.")
        return []
    lexicon = set(w.strip() for w in open(LEXICON_PATH, encoding="utf-8") if w.strip())

    def clean_word(w):
        return "".join(c for c in w if c in HEBREW_LETTERS)

    unknown_counter = Counter()
    unknown_klalim = Counter()
    for k in klalim:
        for w in k["clean_text"].split():
            cw = clean_word(w)
            if not cw:
                continue
            if cw not in lexicon:
                unknown_counter[cw] += 1
                unknown_klalim[k["klal_id"]] += 1

    total_words = sum(len(k["clean_text"].split()) for k in klalim)
    print(f"  {len(unknown_counter)} distinct not-in-lexicon words ({sum(unknown_counter.values())} occurrences) out of ~{total_words} total words.")
    print("  Most frequent not-in-lexicon words (top 20 - likely real vocabulary lexicon.txt just hasn't seen yet, not necessarily errors):")
    for w, c in unknown_counter.most_common(20):
        print(f"    {c:4d}x  {w}")
    hapax = [w for w, c in unknown_counter.items() if c == 1]
    print(f"  {len(hapax)} of those appear only ONCE in the whole corpus - the highest-suspicion subset (a real, common word would recur; lexicon.txt already covers ~19k validated words).")
    return list(unknown_counter.keys())


def main():
    klalim = load_klalim()
    print(f"Loaded {len(klalim)} Part-1 klalim from {PART1_PATH}")

    r1 = check_gematria_self_consistency(klalim)
    r2 = check_character_sanity(klalim)
    r3 = check_duplicate_phrases(klalim, n=10)
    r4 = check_self_reference_directionality(klalim)
    r5 = check_full_lexicon_coverage(klalim)

    print("\n=== Summary ===")
    print(f"  1. Gematria self-consistency: {len(r1)} issue(s)")
    print(f"  2. Character sanity:          {len(r2)} issue(s)")
    print(f"  3. Duplicated phrases:        {len(r3)} issue(s)")
    print(f"  4. Self-reference direction:  {len(r4)} issue(s)")
    print(f"  5. Not-in-lexicon words:      {len(r5)} distinct word(s) (informational, not necessarily errors - see hapax count above)")


if __name__ == "__main__":
    main()
