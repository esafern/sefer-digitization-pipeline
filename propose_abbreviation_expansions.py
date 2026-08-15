#!/usr/bin/env python3
# [STANDALONE] Candidate expansions for Part 1's abbreviation-marked tokens
# (see extract_abbreviation_forms.py for the canonical list this reads).
#
# WHY THIS IS LOWER-RISK THAN THE PUNCTUATION PASS: punctuation insertion is
# a judgment call about where a sentence break belongs, which the ink itself
# doesn't mark - genuinely ambiguous, per CLAUDE.md the riskier of the two.
# Abbreviation expansion is different in kind: the abbreviated form is
# already correctly transcribed (verified against the scan the normal way),
# and what it stands for is a matter of ESTABLISHED RABBINIC CONVENTION, the
# same few hundred standard forms used across the entire Rabbinic literature
# - not a per-instance reading of the ink. That said, "lower-risk" is not
# "risk-free": a real minority of these forms are genuinely ambiguous even
# under the convention (same orthographic form, different standard meanings
# depending on context) - flagged explicitly below, never silently resolved.
#
# METHOD: ROOT_EXPANSIONS is a hand-built dictionary of ~140 standard
# abbreviation roots (gershayim/geresh position as printed, no prefix). Each
# entry is either a single confident expansion, or a tuple of options when
# the form is genuinely ambiguous under standard convention (both listed,
# neither guessed at). Every form actually found by
# extract_abbreviation_forms.py is resolved by: (1) direct root match; (2)
# stripping a standard Hebrew prefix (ו/ב/ה/מ/כ/ל/ש/ד, singly or paired,
# e.g. וב-) and retrying; (3) if neither matches and the form LOOKS like a
# bare gematria numeral (a single Hebrew letter + geresh, or a short
# letter-run consistent with a citation number) - flagged NUMERAL, a
# different category entirely, not a word to expand (see the "~386 of 395"
# citation-numeral finding elsewhere in this project's history - the same
# confusion, avoided here on purpose). Anything left is UNRESOLVED - listed,
# not guessed at.
#
# STILL A CANDIDATE LIST, NOT A CORRECTION: nothing here writes part1.json.
# Follows the same shape as punctuation_candidates_part1.json (propose ->
# human review -> a separate apply step, not built here) - this script only
# does the propose step, and only for the KNOWN/root-resolvable slice.
#
# Usage: python3 propose_abbreviation_expansions.py [--json out.json]
import argparse
import json
import os
from collections import Counter

REPO = os.path.dirname(os.path.abspath(__file__))
QUOTE_CHARS = set('"\'׳״')

# Standard Hebrew prefixes this print attaches directly to a word with no
# space (ordinary Hebrew morphology, not an OCR artifact) - checked longest
# combination first so e.g. "וב-" doesn't get mis-stripped as just "ו-".
PREFIXES = ["וב", "ומ", "וכ", "ול", "וה", "וד", "ושב", "מש",
            "ו", "ב", "ה", "מ", "כ", "ל", "ש", "ד"]

# Root form (gershayim/geresh position as printed, no prefix) -> expansion,
# or a tuple of (option_a, option_b, ...) when genuinely ambiguous under
# standard convention. Built from established Rabbinic/Talmudic abbreviation
# usage, not derived from this corpus - the same reason lexicon.txt can't be
# trusted (Lesson 3), this dictionary is deliberately NOT built by looking
# at what part1.json happens to contain.
ROOT_EXPANSIONS = {
    # People (Rishonim/Acharonim acronyms) - unambiguous, each names one person
    "רש\"י": "רבי שלמה יצחקי (Rashi)",
    "רשב\"ם": "רבי שמואל בן מאיר (Rashbam)",
    "ר\"ת": ("רבינו תם (Rabbeinu Tam)", "ראשי תיבות (an acronym, generic)"),
    "רמב\"ם": "רבי משה בן מיימון (Rambam)",
    "רמב\"ן": "רבי משה בן נחמן (Ramban)",
    "רשב\"א": "רבי שלמה בן אדרת (Rashba)",
    "ריטב\"א": "רבי יום טוב בן אברהם (Ritva)",
    "רי\"ף": "רבי יצחק אלפסי (Rif)",
    "רא\"ש": "רבינו אשר (Rosh)",
    "ר\"ן": "רבינו נסים (Ran)",
    "רשב\"ץ": "רבי שמעון בן צמח (Rashbatz)",
    "מהר\"ם": "מורנו הרב רבי מאיר (Maharam, various)",
    "מהרש\"א": "מורנו הרב רבי שמואל אליעזר (Maharsha)",
    "מהרש\"ל": "מורנו הרב רבי שלמה לוריא (Maharshal)",
    "מהרי\"ק": "מורנו הרב רבי יוסף קולון (Maharik)",
    "כנ\"הג": "כנסת הגדולה (Knesset HaGedolah, R. Chaim Benveniste)",
    "הכ\"מ": "הכסף משנה (Kesef Mishneh, on the Rambam)",
    "ט\"ז": ("Taz - Turei Zahav (R. David HaLevi Segal)", "gematria 17 (a folio/siman number)"),
    "ש\"ך": "Shakh - Siftei Kohen (R. Shabtai HaKohen)",
    "מג\"א": "מגן אברהם (Magen Avraham)",
    "ב\"ח": "Bach - Bayit Chadash (R. Yoel Sirkis)",

    # Formulaic phrases, high-confidence single meaning
    "ז\"ל": "זכרונו לברכה",
    "זצ\"ל": "זכר צדיק לברכה",
    "זצוק\"ל": "זכר צדיק וקדוש לברכה",
    "וכו'": "וכולי",
    "כו'": "כולי",
    "וגו'": "וגומר",
    "וז\"ל": "וזה לשונו",
    "עכ\"ל": "עד כאן לשונו",
    "עכ\"ד": "עד כאן דבריו",
    "כמ\"ש": "כמו שכתב",
    "וכ\"כ": "וכן כתב",
    "כ\"כ": ("כן כתב / כך כתב", "כל כך"),
    "אפי'": "אפילו",
    "מתני'": "מתניתין",
    "אמרי'": "אמרינן",
    "תוס'": "תוספות",
    "קי\"ל": "קיימא לן",
    "דקי\"ל": "דקיימא לן",
    "ס\"ל": "סבירא ליה",
    "ה\"ה": "הוא הדין",
    "ה\"נ": "הכי נמי",
    "ה\"מ": "הני מילי",
    "צ\"ע": "צריך עיון",
    "צ\"ל": "צריך לומר",
    "נ\"ל": "נראה לי",
    "י\"ל": "יש לומר",
    "י\"מ": "יש מפרשים",
    "ק\"ו": "קל וחומר",
    "ח\"ו": "חס ושלום / חלילה",
    "כנ\"ל": "כנזכר לעיל",
    "כ\"ש": "כל שכן",
    "מ\"ש": "מה שכתב / מה שאמר",
    "ד\"ה": "דבור המתחיל",
    "ד\"א": "דבר אחר",
    "ת\"ל": "תלמוד לומר",
    "ב\"ד": "בית דין",
    "ג\"כ": "גם כן",
    "א\"כ": "אם כן",
    "ע\"כ": ("עד כאן", "על כרחך"),
    "ע\"ש": "עיין שם",
    "עי'": "עיין",
    "יע\"ש": "יעוין שם",
    "וע\"ע": "ועיין עוד",
    "וע\"ש": "ועיין שם",
    "בס\"פ": "בסוף פרק",
    "ס\"פ": "סוף פרק",
    "פ\"ק": "פרק קמא",
    "פי'": ("פירוש", "פירש"),
    "סי'": "סימן",
    "ססי'": "סוף סימן",
    "בפ'": "בפרק",
    "ובפ'": "ובפרק",
    "ר\"ל": "רצה לומר",
    "ל\"פ": "לא פליג",
    "מ\"מ": ("מכל מקום", "מגיד משנה (Maggid Mishneh, on the Rambam)"),
    "ש\"ס": "ששה סדרים (i.e. the Talmud)",
    "בש\"ס": "בששה סדרים (i.e. in the Talmud)",
    "ב\"ה": ("ברוך הוא", "בית הלל", "בסייעתא דשמיא / בעזרת השם (letterhead use)"),
    "או\"ה": "אומות העולם",
    "ע\"ז": ("עבודה זרה", "על זה"),
    "ע\"א": ("עמוד א", "עובד אלילים / עבודה זרה"),
    "ע\"ב": "עמוד ב",
    "ע\"ג": ("עמוד ג", "על גבי"),
    "ע\"ד": ("עמוד ד", "על דרך"),
    "אע\"ג": "אף על גב",
    "אע\"פ": "אף על פי",
    "מיהו": "מיהו (not an abbreviation - full word, \"however\")",
    "י\"ד": ("יורה דעה (a Shulchan Arukh section)", "gematria 14 (a folio/siman number)"),
    "חו\"מ": "חושן משפט (a Shulchan Arukh section)",
    "אה\"ע": "אבן העזר (a Shulchan Arukh section)",
    "או\"ח": "אורח חיים (a Shulchan Arukh section)",
    "יו\"ד": "יורה דעה (a Shulchan Arukh section)",
    "ל\"ל": "למאי לן / למה לי",
    "ל\"ד": "לאו דוקא",
    "ל\"מ": "לית מאן דפליג / לא מיבעיא",
    "מ\"ל": "מנא לן",
    "ה\"ל": "הוה ליה",
    "מ\"ד": "מאן דאמר",
    "למ\"ד": "למאן דאמר",
    "ה\"ק": "הכי קאמר",
    "ה\"פ": "הכי פירושו",
    "ר\"ה": "ראש השנה (a Talmud tractate) / רב האי (Rav Hai Gaon)",
    "ב\"ק": "בבא קמא (a Talmud tractate)",
    "ב\"מ": "בבא מציעא (a Talmud tractate)",
    "ב\"ב": "בבא בתרא (a Talmud tractate)",
    "ר\"פ": ("ריש פרק (the start of a chapter)", "רבי פלוני (a specific sage's title in some prints)"),
    "ר\"י": "רבי יוסי / רבי יהודה / רבינו יצחק (context-dependent which Rabbi)",
    "ר\"ג": "רבן גמליאל",
    "ר\"ע": "רבי עקיבא",
    "רב\"י": "רבי יוסף קארו (author of the Beit Yosef/Shulchan Arukh)",
    "ב\"י": "בית יוסף (R. Yosef Karo's work)",
    "ד\"מ": ("דרכי משה (R. Moshe Isserles' work)", "דרך משל"),
    "רמ\"א": "רבי משה איסרלש (Rema)",
    "מהריק\"ש": "מורנו הרב רבי יעקב קאסטרו",
    "פ\"ב": "פרק ב",
    "פ\"ג": "פרק ג",
    "בפ\"ב": "בפרק ב",
    "בפ\"ק": "בפרק קמא",
    "בסי'": "בסימן",
    "בס'": "בספר",
    "מס'": "מסכת",
    "פ\"א": ("פרק א", "פרק אחד"),
    "מהר\"י": "מורנו הרב רבי [שם] (a specific Maharai, name-dependent)",
    "מהרי\"ט": "מורנו הרב רבי יוסף טראני (Maharit)",
    "וכ\"ה": "וכן הוא",
    "כ\"ה": "כך הוא / כן הוא",
    "כ\"א": ("כי אם", "כך אמר"),
    "כ\"ז": "כל זה",
    "כ\"מ": ("כל מקום", "ככה מצאתי"),
    "מ\"כ": "מה שכתב (inverted order, less common)",
    "וכ\"ת": "ואם תאמר",
    "כת\"ר": "כתב תשובתו רבינו (varies) / כבוד תורתו",
    "ע\"מ": "על מנת",
    "ע\"ע": "עיין עוד",
    "וע\"פ": "ועל פי",
    "עפ\"י": "על פי",
    "ד\"ז": "דבר זה",
    "ט\"ס": "טעות סופר",
    "בד\"א": "במה דברים אמורים",
    "מיהת": "מיהת (not an abbreviation - full word)",
    "וכה\"ג": "וכהאי גוונא",
    "כה\"ג": "כהאי גוונא",
    "וא\"ת": "ואם תאמר",
    "וי\"ל": "ויש לומר",
    "וי\"מ": "ויש מפרשים",
    "וכ\"נ": "וכן נראה",
    "וכ\"ז": "וכל זה",
    "וא\"כ": "ואם כן",
    "דהיינו": "דהיינו (not an abbreviation - full word)",
    "כו\"ע": "כולי עלמא",
    "בכ\"מ": "בכל מקום",
    "לכ\"ע": "לכולי עלמא",
    "מכ\"ש": "מכל שכן",
    "וכמ\"ש": "וכמו שכתב",
    "מש\"ה": "משום הכי",
    "מש\"כ": "מה שכתב",
    "כד\"א": "כדאיתא",
    "כדאי'": "כדאיתא",
    "איתא": "איתא (not an abbreviation - full word)",
    "וכיו\"ב": "וכיוצא בזה",
    "כיו\"ב": "כיוצא בזה",
    "כה\"ק": "כתבי הקודש",
    "בזה\"ל": "בזה הלשון",
    "בזה\"ז": "בזמן הזה",

    # Added after the first coverage pass, chasing the top of the
    # UNRESOLVED list (see module usage) - same standard, not corpus-fitted.
    "הר\"ב": "הרב (the master/author - in Mishnah-commentary citations, usually R. Ovadiah of Bertinoro)",
    "ר\"ש": ("רבי שמעון", "רש\"י (rare, some prints)"),
    "אפ\"ה": "אף על פי כן",
    "ג\"ש": "גזירה שוה",
    "שו\"ת": "שאלות ותשובות",
    "נלע\"ד": "נראה לי עניות דעתי",
    "רשב\"ג": "רבן שמעון בן גמליאל",
    "ר\"א": ("רבי אליעזר", "רבי אבהו", "רבי אמי"),
    "מוהר\"ש": "מורנו הרב רבי שמואל (name-dependent Maharash)",
    "ב\"ש": "בית שמאי",
    "כ\"י": "כתב יד",
    "פ\"ד": "פרק ד",
    "פ\"ה": "פרק ה",
    "פ\"ג": "פרק ג",
    "ר\"ח": ("ראש חודש", "רבינו חננאל"),
    "רשב\"י": "רבי שמעון בר יוחאי",
    "רי\"ד": "רבי ישעיה די טראני",
    "ריב\"ש": "רבי יצחק בר ששת (Rivash)",
}


def is_abbreviation(word):
    return any(c in word for c in QUOTE_CHARS)


def looks_like_bare_numeral(word):
    """A single Hebrew letter (or short letter-run) plus a trailing geresh,
    with nothing else - the shape used for citation/folio/siman numbers, not
    for a word abbreviation. Deliberately conservative (only the SIMPLE
    geresh-final shape) - gershayim-marked forms are never flagged here even
    if their gematria value would also make sense as a number (e.g. י"ד),
    because those are exactly the cases genuinely ambiguous with a real word
    abbreviation and belong in ROOT_EXPANSIONS as an explicit ambiguous
    entry, not silently classified either way."""
    return len(word) >= 2 and word[-1] == "'" and all(c not in QUOTE_CHARS for c in word[:-1])


def resolve(word):
    if word.strip(''.join(QUOTE_CHARS)) == "":
        # A "word" that's ONLY gershayim/geresh character(s), nothing else -
        # not an abbreviation at all, almost certainly a stray/orphaned
        # punctuation token (a missing-space or tokenization artifact - the
        # same DATA-issue class as the compound-token dropped-lamed finding
        # from the lexicon cross-check, not something to expand).
        return None, "artifact"
    if word in ROOT_EXPANSIONS:
        return ROOT_EXPANSIONS[word], "root"
    # Try stripping up to 2 prefix LEVELS (e.g. ל then ה, for "to the Rosh"
    # -> "ל" + "ה" + "רא"ש"), not just one - a single-level check alone
    # misses stacked prefixes even when the bare root IS in the dictionary
    # (found while testing: "להרא"ש" has "ל" stripped by the single-level
    # version, leaving "הרא"ש" - itself not a dict key, since "רא"ש" is the
    # stored root and "ה" is handled as ITS OWN prefix layer, not baked in).
    for p1 in PREFIXES:
        if not word.startswith(p1):
            continue
        rest1 = word[len(p1):]
        if rest1 in ROOT_EXPANSIONS:
            return ROOT_EXPANSIONS[rest1], f"prefix {p1}- + root"
        for p2 in PREFIXES:
            if rest1.startswith(p2):
                rest2 = rest1[len(p2):]
                if rest2 in ROOT_EXPANSIONS:
                    return ROOT_EXPANSIONS[rest2], f"prefix {p1}-{p2}- + root"
    if looks_like_bare_numeral(word):
        return None, "numeral"
    return None, "unresolved"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="write the full per-form report to this path")
    args = ap.parse_args()

    part1 = json.load(open(os.path.join(REPO, "part1.json"), encoding="utf-8"))
    counts = Counter()
    for k in part1:
        for w in k["clean_text"].split():
            if is_abbreviation(w):
                counts[w] += 1

    report = {}
    for w, n in counts.items():
        expansion, method = resolve(w)
        report[w] = {"count": n, "method": method, "expansion": expansion}

    resolved = {w: r for w, r in report.items()
                if r["method"] == "root" or r["method"].startswith("prefix")}
    numerals = {w: r for w, r in report.items() if r["method"] == "numeral"}
    artifacts = {w: r for w, r in report.items() if r["method"] == "artifact"}
    unresolved = {w: r for w, r in report.items() if r["method"] == "unresolved"}
    ambiguous = {w: r for w, r in resolved.items() if isinstance(r["expansion"], tuple)}

    total = sum(counts.values())
    print(f"{len(counts)} unique forms, {total} occurrences.\n")
    print(f"RESOLVED (root or prefix+root match): {len(resolved)} forms, "
          f"{sum(r['count'] for r in resolved.values())} occurrences "
          f"({sum(r['count'] for r in resolved.values())/total:.1%})")
    print(f"  of which AMBIGUOUS (>1 standard meaning, both listed): {len(ambiguous)} forms, "
          f"{sum(r['count'] for r in ambiguous.values())} occurrences")
    print(f"NUMERAL (bare geresh-marked letter/letters, not a word to expand): "
          f"{len(numerals)} forms, {sum(r['count'] for r in numerals.values())} occurrences")
    print(f"ARTIFACT (token is ONLY a gershayim/geresh character - likely a stray "
          f"punctuation/missing-space DATA issue, not a real abbreviation): "
          f"{len(artifacts)} forms, {sum(r['count'] for r in artifacts.values())} occurrences")
    print(f"UNRESOLVED (no dictionary entry - not guessed at): {len(unresolved)} forms, "
          f"{sum(r['count'] for r in unresolved.values())} occurrences "
          f"({sum(r['count'] for r in unresolved.values())/total:.1%})")

    print("\n--- Top 30 RESOLVED, by frequency ---")
    for w, r in sorted(resolved.items(), key=lambda x: -x[1]["count"])[:30]:
        exp = r["expansion"]
        exp_str = " / ".join(exp) if isinstance(exp, tuple) else exp
        flag = "  [AMBIGUOUS]" if isinstance(exp, tuple) else ""
        print(f"  {r['count']:4d}  {w:<10} -> {exp_str}{flag}")

    print("\n--- Top 30 UNRESOLVED, by frequency (candidates for the dictionary to grow) ---")
    for w, r in sorted(unresolved.items(), key=lambda x: -x[1]["count"])[:30]:
        print(f"  {r['count']:4d}  {w}")

    if args.json:
        def ser(r):
            return {"count": r["count"], "method": r["method"],
                    "expansion": list(r["expansion"]) if isinstance(r["expansion"], tuple) else r["expansion"]}
        json.dump({w: ser(r) for w, r in report.items()}, open(args.json, "w", encoding="utf-8"),
                   ensure_ascii=False, indent=1)
        print(f"\nWrote {args.json}")


if __name__ == "__main__":
    main()
