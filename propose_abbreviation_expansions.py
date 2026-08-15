#!/usr/bin/env python3
# [STANDALONE] Candidate expansions for Part 1's abbreviation-marked tokens
# (see extract_abbreviation_forms.py for the canonical list this reads).
#
# REBUILT 2026-08-16 after comparing two Machon Yerushalayim critical-
# edition sample pages (klal 1-2, user-supplied JPGs, gitignored, reference
# only per Success Criterion #1) against this corpus's own text word by
# word. The FIRST version of this script assumed every gershayim/geresh-
# marked token was a candidate to expand. That assumption was wrong, and
# the crops (see PROJECT-STATUS.md 2026-08-16 for the exact before/after
# pairs) show a real, non-uniform pattern:
#
#   NEVER expanded, confirmed repeatedly: person/work-name acronyms
#   (רש"י, הרא"ש, הר"ן, הרשב"א, רי"ף stay abbreviated every time - nobody
#   turns רש"י into "Rabbi Shlomo Yitzchaki" inline), formulaic markers
#   (ז"ל, ד"ה, וכו', ע"כ, ודו"ק, ולענ"ד, הנ"ל, מ"מ), and citation-format
#   tokens (folio+side, chapter+number: י"ט ב', ל"א ב', בפ"ב, בפ"ג).
#
#   Genuinely expanded, confirmed by direct part1.json comparison: single-
#   word GERESH-TRUNCATED forms restored to their full ending (בהדי'->
#   בהדיא, תני'->תניא, נרא'->נראה, אחרי'->אחריה - the geresh here just
#   marks a dropped word-ending, not a formulaic acronym), bare פ' used as
#   an ordinary noun (not part of a number-citation) -> פרק, and ע"ש
#   specifically -> עיין שם (confirmed twice) even though sibling
#   formulas ע"כ/וכו'/מ"מ in the same paragraphs did NOT expand - this is
#   a per-abbreviation editorial choice, not a rule that generalizes.
#
#   A THIRD, HIGHER-RISK case found by this comparison, not present in the
#   first version at all: ambiguous multi-referent acronyms (ר"י could be
#   Rabbi Yehuda / Rabbi Yosi / Rabbeinu Yitzchak) get resolved to ONE
#   specific full name by Machon Yerushalayim's editors - `אליבא דר"י` in
#   our text became `אליבא דרבי יהודה` in theirs, i.e. someone read the
#   actual sugya and decided which sage was meant. That is real scholarly
#   research, not a lexical lookup - listing multiple options (the first
#   version's approach) is the right stance, but this file now says so
#   explicitly (category "scholarly") rather than filing it next to
#   ordinary ambiguous phrase-abbreviations.
#
# Five categories, tagged on every ROOT_ENTRIES value:
#   "expand"    - propose this expansion (single string, or a tuple ONLY
#                 when standard convention itself has >1 meaning - e.g.
#                 the punctuation- or context-independent case, not the
#                 scholarly-attribution case below)
#   "stays"     - confirmed or strongly-analogous NOT to expand; kept in
#                 the dictionary (not just omitted) so a reader can see it
#                 was considered, not missed
#   "name"      - a person or work acronym; never propose expansion
#   "scholarly" - an ambiguous multi-referent acronym; resolving it needs
#                 someone to read the actual passage, not a dictionary -
#                 never propose expansion, flagged distinctly from "stays"
#                 so it's clear WHY (not "convention keeps it short" but
#                 "we don't know which one without reading the sugya")
#   (numeral/artifact/unresolved remain separate, non-dictionary paths -
#   unchanged from the first version)
#
# TRUNCATED-WORD COMPLETION reuses this project's own infrastructure
# instead of guessing: for a single-geresh form with no dictionary root,
# try appending each common Hebrew word-final letter to the stem and check
# the independent Sefaria reference corpus (sefaria_reference_corpus/, via
# fetch_sefaria_reference_corpus.py / validate_lexicon_independent.py's
# frequency cache) for a single, clearly-dominant completion - the same
# method detect_ligature_corruption.py already uses for the dropped-lamed
# bug, applied to a different problem (a missing WORD-ENDING instead of a
# missing LETTER). If the frequency cache isn't built yet, this step is
# skipped (not an error) and those forms fall through to UNRESOLVED.
#
# STILL A CANDIDATE LIST, NOT A CORRECTION: nothing here writes part1.json.
# Follows the same shape as punctuation_candidates_part1.json (propose ->
# human review -> a separate apply step, not built here) - this script
# only does the propose step.
#
# Usage: python3 propose_abbreviation_expansions.py [--json out.json]
import argparse
import json
import os
from collections import Counter

REPO = os.path.dirname(os.path.abspath(__file__))
QUOTE_CHARS = set('"\'׳״')
SEFARIA_FREQ_CACHE = os.path.join(REPO, "sefaria_reference_corpus", "word_freq.json")

# Standard Hebrew prefixes this print attaches directly to a word with no
# space (ordinary Hebrew morphology, not an OCR artifact) - checked longest
# combination first so e.g. "וב-" doesn't get mis-stripped as just "ו-".
PREFIXES = ["וב", "ומ", "וכ", "ול", "וה", "וד", "ושב", "מש",
            "ו", "ב", "ה", "מ", "כ", "ל", "ש", "ד"]

# root -> (category, expansion_or_None). Built from established Rabbinic/
# Talmudic convention (and the two-page comparison above), deliberately NOT
# fitted to what this corpus happens to contain (Lesson 3, same reasoning
# as lexicon.txt's independence problem).
ROOT_ENTRIES = {
    # ---- NAME: person/work acronyms. Confirmed by direct comparison to
    # NEVER expand (רש"י/הרא"ש/הר"ן/הרשב"א/רי"ף each checked against the
    # sample pages); the rest follow the same convention by strong analogy
    # (all are the identical class of thing - a Rishon/Acharon's standard
    # acronym, or a work cited by its own title). ----
    "רש\"י": ("name", "רבי שלמה יצחקי (Rashi)"),
    "רשב\"ם": ("name", "רבי שמואל בן מאיר (Rashbam)"),
    "רמב\"ם": ("name", "רבי משה בן מיימון (Rambam)"),
    "רמב\"ן": ("name", "רבי משה בן נחמן (Ramban)"),
    "רשב\"א": ("name", "רבי שלמה בן אדרת (Rashba)"),
    "ריטב\"א": ("name", "רבי יום טוב בן אברהם (Ritva)"),
    "רי\"ף": ("name", "רבי יצחק אלפסי (Rif)"),
    "רא\"ש": ("name", "רבינו אשר (Rosh)"),
    "ר\"ן": ("name", "רבינו נסים (Ran)"),
    "רשב\"ץ": ("name", "רבי שמעון בן צמח (Rashbatz)"),
    "רשב\"י": ("name", "רבי שמעון בר יוחאי"),
    "רשב\"ג": ("name", "רבן שמעון בן גמליאל"),
    "רי\"ד": ("name", "רבי ישעיה די טראני"),
    "ריב\"ש": ("name", "רבי יצחק בר ששת (Rivash)"),
    "רמ\"א": ("name", "רבי משה איסרלש (Rema)"),
    "רב\"י": ("name", "רבי יוסף קארו (author of the Beit Yosef/Shulchan Arukh)"),
    "ב\"י": ("name", "בית יוסף (R. Yosef Karo's work)"),
    "מהר\"ם": ("name", "מורנו הרב רבי מאיר (Maharam, various)"),
    "מהרש\"א": ("name", "מורנו הרב רבי שמואל אליעזר (Maharsha)"),
    "מהרש\"ל": ("name", "מורנו הרב רבי שלמה לוריא (Maharshal)"),
    "מהרי\"ק": ("name", "מורנו הרב רבי יוסף קולון (Maharik)"),
    "מהריק\"ש": ("name", "מורנו הרב רבי יעקב קאסטרו"),
    "מהרי\"ט": ("name", "מורנו הרב רבי יוסף טראני (Maharit)"),
    "מוהר\"ש": ("name", "מורנו הרב רבי שמואל (name-dependent Maharash)"),
    "מהר\"י": ("name", "מורנו הרב רבי [שם] (a specific Maharai, name-dependent)"),
    "כנ\"הג": ("name", "כנסת הגדולה (Knesset HaGedolah, R. Chaim Benveniste) - "
               "confirmed EXPANDED once in the sample pages when referring to "
               "the author by his work's title (\"להרב בכנסת הגדולה\"), unlike "
               "every person-acronym checked - kept as \"name\" pending more "
               "evidence, not moved to \"expand\" on a single instance"),
    "הכ\"מ": ("name", "הכסף משנה (Kesef Mishneh, on the Rambam)"),
    "ט\"ז": ("name", "Taz - Turei Zahav (R. David HaLevi Segal). Also reads as "
             "gematria 17 in a folio/siman position - either way, not a "
             "prose word to expand"),
    "ש\"ך": ("name", "Shakh - Siftei Kohen (R. Shabtai HaKohen)"),
    "מג\"א": ("name", "מגן אברהם (Magen Avraham)"),
    "ב\"ח": ("name", "Bach - Bayit Chadash (R. Yoel Sirkis)"),

    # ---- SCHOLARLY: ambiguous multi-referent acronym. Confirmed by direct
    # comparison that Machon Yerushalayim resolves these to ONE specific
    # name (אליבא דר"י -> אליבא דרבי יהודה) via context/scholarship, not a
    # dictionary. Never propose an expansion here - listing candidates
    # would invite picking one mechanically, which is exactly the wrong
    # move. ----
    "ר\"י": ("scholarly", ["רבי יוסי", "רבי יהודה", "רבינו יצחק"]),
    "ר\"ש": ("scholarly", ["רבי שמעון", "רש\"י (rare, some prints)"]),
    "ר\"א": ("scholarly", ["רבי אליעזר", "רבי אבהו", "רבי אמי"]),
    "ר\"ח": ("scholarly", ["ראש חודש", "רבינו חננאל"]),
    "ר\"פ": ("scholarly", ["ריש פרק (the start of a chapter)",
                            "רבי פלוני (a specific sage's title in some prints)"]),
    "ר\"ת": ("scholarly", ["רבינו תם (Rabbeinu Tam)", "ראשי תיבות (an acronym, generic)"]),
    "ד\"מ": ("scholarly", ["דרכי משה (R. Moshe Isserles' work)", "דרך משל"]),
    "כ\"מ": ("scholarly", ["כל מקום", "ככה מצאתי"]),
    "כ\"א": ("scholarly", ["כי אם", "כך אמר"]),
    "ר\"ה": ("scholarly", ["ראש השנה (a Talmud tractate)", "רב האי (Rav Hai Gaon)"]),
    "ב\"ה": ("scholarly", ["ברוך הוא", "בית הלל",
                            "בסייעתא דשמיא / בעזרת השם (letterhead use)"]),

    # ---- STAYS: confirmed (ז"ל, ד"ה, וכו', ע"כ, ודו"ק, ולענ"ד, הנ"ל, מ"מ,
    # citation-format chapter/folio+number) or strongly analogous (every
    # other citation-format/section-name entry - same shape as the
    # confirmed ones, not a guess about a different shape of thing). Kept
    # in the dictionary, not omitted, so it's visible this was checked. ----
    "ז\"ל": ("stays", "זכרונו לברכה"),
    "זצ\"ל": ("stays", "זכר צדיק לברכה"),
    "זצוק\"ל": ("stays", "זכר צדיק וקדוש לברכה"),
    "ד\"ה": ("stays", "דבור המתחיל"),
    "וכו'": ("stays", "וכולי"),
    "כו'": ("stays", "כולי"),
    "ע\"כ": ("stays", "עד כאן"),
    "מ\"מ": ("stays", "מכל מקום"),
    "הנ\"ל": ("stays", "הנזכר לעיל"),
    "כנ\"ל": ("stays", "כנזכר לעיל"),
    "ולענ\"ד": ("stays", "ולפי עניות דעתי"),
    "לענ\"ד": ("stays", "לפי עניות דעתי"),
    "נלע\"ד": ("stays", "נראה לי עניות דעתי"),
    "ודו\"ק": ("stays", "וידוק"),
    # citation format: chapter/perek + number, or "kama" (=first)
    "פ\"א": ("stays", "פרק א"), "פ\"ב": ("stays", "פרק ב"),
    "פ\"ג": ("stays", "פרק ג"), "פ\"ד": ("stays", "פרק ד"),
    "פ\"ה": ("stays", "פרק ה"), "פ\"ק": ("stays", "פרק קמא"),
    "בפ\"א": ("stays", "בפרק א"), "בפ\"ב": ("stays", "בפרק ב"),
    "בפ\"ג": ("stays", "בפרק ג"), "בפ\"ק": ("stays", "בפרק קמא"),
    "ס\"פ": ("stays", "סוף פרק"), "בס\"פ": ("stays", "בסוף פרק"),
    "סי'": ("stays", "סימן"), "ססי'": ("stays", "סוף סימן"),
    "בסי'": ("stays", "בסימן"),
    "ע\"א": ("stays", "עמוד א"), "ע\"ב": ("stays", "עמוד ב"),
    "ע\"ג": ("stays", "עמוד ג"), "ע\"ד": ("stays", "עמוד ד"),
    # Shulchan Arukh section names - proper-noun-like citation labels, same
    # treatment as a person/work name, not prose vocabulary
    "או\"ח": ("stays", "אורח חיים (a Shulchan Arukh section)"),
    "יו\"ד": ("stays", "יורה דעה (a Shulchan Arukh section)"),
    "י\"ד": ("stays", "יורה דעה (a Shulchan Arukh section) - or gematria 14; "
             "either reading is a citation label, not prose to expand"),
    "חו\"מ": ("stays", "חושן משפט (a Shulchan Arukh section)"),
    "אה\"ע": ("stays", "אבן העזר (a Shulchan Arukh section)"),
    "ש\"ס": ("stays", "ששה סדרים (i.e. the Talmud)"),
    "בש\"ס": ("stays", "בששה סדרים (i.e. in the Talmud)"),
    "ב\"ק": ("stays", "בבא קמא (a Talmud tractate)"),
    "ב\"מ": ("stays", "בבא מציעא (a Talmud tractate)"),
    "ב\"ב": ("stays", "בבא בתרא (a Talmud tractate)"),
    "מס'": ("stays", "מסכת"),

    # ---- EXPAND: confirmed (ע"ש -> עיין שם, twice; בפ' bare -> בפרק) or
    # the same class of ordinary-prose functional phrase (not a citation
    # label, not a name) - lower confidence than the confirmed two, listed
    # separately in the report. ----
    "ע\"ש": ("expand", "עיין שם"),
    "יע\"ש": ("expand", "יעוין שם"),
    "וע\"ש": ("expand", "ועיין שם"),
    "וע\"ע": ("expand", "ועיין עוד"),
    "ע\"ע": ("expand", "עיין עוד"),
    "עי'": ("expand", "עיין"),
    "בפ'": ("expand", "בפרק"),
    "ובפ'": ("expand", "ובפרק"),
    "וכ\"כ": ("expand", "וכן כתב"),
    "כמ\"ש": ("expand", "כמו שכתב"),
    "וכמ\"ש": ("expand", "וכמו שכתב"),
    "וז\"ל": ("expand", "וזה לשונו"),
    "עכ\"ל": ("expand", "עד כאן לשונו"),
    "עכ\"ד": ("expand", "עד כאן דבריו"),
    "אפי'": ("expand", "אפילו"),
    "מתני'": ("expand", "מתניתין"),
    "אמרי'": ("expand", "אמרינן"),
    "תוס'": ("expand", "תוספות"),
    "קי\"ל": ("expand", "קיימא לן"),
    "דקי\"ל": ("expand", "דקיימא לן"),
    "ס\"ל": ("expand", "סבירא ליה"),
    "צ\"ע": ("expand", "צריך עיון"),
    "צ\"ל": ("expand", "צריך לומר"),
    "נ\"ל": ("expand", "נראה לי"),
    "י\"ל": ("expand", "יש לומר"),
    "וי\"ל": ("expand", "ויש לומר"),
    "י\"מ": ("expand", "יש מפרשים"),
    "וי\"מ": ("expand", "ויש מפרשים"),
    "ק\"ו": ("expand", "קל וחומר"),
    "ח\"ו": ("expand", "חס ושלום"),
    "כ\"ש": ("expand", "כל שכן"),
    "מכ\"ש": ("expand", "מכל שכן"),
    "ג\"כ": ("expand", "גם כן"),
    "א\"כ": ("expand", "אם כן"),
    "וא\"כ": ("expand", "ואם כן"),
    "וא\"ת": ("expand", "ואם תאמר"),
    "וכ\"ת": ("expand", "ואם תאמר"),
    "ד\"א": ("expand", "דבר אחר"),
    "ת\"ל": ("expand", "תלמוד לומר"),
    "ב\"ד": ("expand", "בית דין"),
    "ר\"ל": ("expand", "רצה לומר"),
    "ל\"פ": ("expand", "לא פליג"),
    "אע\"ג": ("expand", "אף על גב"),
    "אע\"פ": ("expand", "אף על פי"),
    "אפ\"ה": ("expand", "אף על פי כן"),
    "ל\"ל": ("expand", "למאי לן"),
    "ל\"ד": ("expand", "לאו דוקא"),
    "מ\"ל": ("expand", "מנא לן"),
    "ה\"ל": ("expand", "הוה ליה"),
    "מ\"ד": ("expand", "מאן דאמר"),
    "למ\"ד": ("expand", "למאן דאמר"),
    "ה\"ק": ("expand", "הכי קאמר"),
    "ה\"פ": ("expand", "הכי פירושו"),
    "ה\"ה": ("expand", "הוא הדין"),
    "ה\"נ": ("expand", "הכי נמי"),
    "ה\"מ": ("expand", "הני מילי"),
    "כ\"ה": ("expand", "כך הוא"),
    "וכ\"ה": ("expand", "וכן הוא"),
    "כ\"ז": ("expand", "כל זה"),
    "וכ\"ז": ("expand", "וכל זה"),
    "וכ\"נ": ("expand", "וכן נראה"),
    "ע\"מ": ("expand", "על מנת"),
    "וע\"פ": ("expand", "ועל פי"),
    "עפ\"י": ("expand", "על פי"),
    "ד\"ז": ("expand", "דבר זה"),
    "ט\"ס": ("expand", "טעות סופר"),
    "בד\"א": ("expand", "במה דברים אמורים"),
    "וכה\"ג": ("expand", "וכהאי גוונא"),
    "כה\"ג": ("expand", "כהאי גוונא"),
    "כיו\"ב": ("expand", "כיוצא בזה"),
    "וכיו\"ב": ("expand", "וכיוצא בזה"),
    "כה\"ק": ("expand", "כתבי הקודש"),
    # Bare title before a name that already follows spelled out in full
    # (e.g. "ר' עקיבא") - safe to expand without choosing WHICH sage,
    # unlike ר"י/ר"א/etc. above where the name itself is fused into the
    # acronym. Added after the truncated-word mechanism below mis-resolved
    # its prefixed forms (דר'/ור', 64+44 occurrences) against unrelated
    # independent-corpus words (דרך, ורן) - this root entry, checked before
    # that fallback, fixes both at once.
    "ר'": ("expand", "רבי"),
    "בזה\"ל": ("expand", "בזה הלשון"),
    "בזה\"ז": ("expand", "בזמן הזה"),
    "כו\"ע": ("expand", "כולי עלמא"),
    "לכ\"ע": ("expand", "לכולי עלמא"),
    "בכ\"מ": ("expand", "בכל מקום"),
    "מש\"ה": ("expand", "משום הכי"),
    "מש\"כ": ("expand", "מה שכתב"),
    "כד\"א": ("expand", "כדאיתא"),
    "כדאי'": ("expand", "כדאיתא"),
    "וגו'": ("expand", "וגומר"),
    "כת\"ר": ("expand", "כבוד תורתו"),
    "בס'": ("expand", "בספר"),
    "ג\"ש": ("expand", "גזירה שוה"),
    "שו\"ת": ("expand", "שאלות ותשובות"),
    "ב\"ש": ("expand", "בית שמאי"),
    "כ\"י": ("expand", "כתב יד"),
    "הר\"ב": ("expand", "הרב"),
    "כ\"כ": ("expand", ["כן כתב", "כך כתב", "כל כך"]),

    # Not actually abbreviations - full words that happen to carry an
    # apostrophe/quote in this corpus's text (kept so the resolver has
    # somewhere to route them instead of silently mis-flagging as unresolved)
    "מיהו": ("stays", "מיהו (not an abbreviation - full word, \"however\")"),
    "מיהת": ("stays", "מיהת (not an abbreviation - full word)"),
    "דהיינו": ("stays", "דהיינו (not an abbreviation - full word)"),
    "איתא": ("stays", "איתא (not an abbreviation - full word)"),
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
    abbreviation and belong in ROOT_ENTRIES as an explicit "stays" entry,
    not silently classified either way."""
    return len(word) >= 2 and word[-1] == "'" and all(c not in QUOTE_CHARS for c in word[:-1])


# Common Hebrew word-final letters a single-geresh truncation could be
# standing in for - checked in this order because ה/ו/א/ן cover the large
# majority of real word endings in this register (feminine/construct nouns,
# 3rd-person suffixes, plural), tried before the rarer ones.
WORD_FINAL_CANDIDATES = list("הואיןםךרלת")


def load_independent_frequency():
    if not os.path.exists(SEFARIA_FREQ_CACHE):
        return None
    return json.load(open(SEFARIA_FREQ_CACHE, encoding="utf-8"))


def resolve_truncated_word(word, freq):
    """For a single-geresh form (word[-1]=="'", no gershayim), try
    appending each candidate final letter to the stem and see whether
    EXACTLY ONE completion is well-attested in the independent Sefaria
    corpus, at a frequency meaningfully higher than treating the geresh
    form as final - the same one-clear-winner method
    detect_ligature_corruption.py already uses for the dropped-lamed bug,
    reused here for a missing WORD-ENDING instead of a missing LETTER."""
    if freq is None or not looks_like_bare_numeral(word):
        return None
    stem = word[:-1]
    if len(stem) < 3:
        # Length-2 stems are where this went wrong in testing: "דר'"
        # (stem "דר", 64 occurrences) matched "דרך" and "ור'" (stem "ור",
        # 44 occurrences) matched "ורן" - both real independent-corpus
        # words, both almost certainly WRONG here, because "ר'" (Rabbi) is
        # itself a hyper-common standalone title-abbreviation this text
        # attaches prefixes to, not a truncated single word - now handled
        # by the "ר'" root entry above instead, which is checked first.
        # Every length>=3 stem that surfaced in testing (תני', נרא', בפי',
        # משו', בחי') was correct; excluding shorter stems trades a
        # handful of lower-confidence hits (שר'->שרי, וס'->וסת) for not
        # repeating the same failure mode on the next short stem.
        return None
    options = []
    for letter in WORD_FINAL_CANDIDATES:
        candidate = stem + letter
        f = freq.get(candidate, 0)
        if f > 50:  # a real, well-attested word, not a coincidental hit
            options.append((candidate, f))
    options.sort(key=lambda x: -x[1])
    if len(options) == 1 or (len(options) > 1 and options[0][1] > 5 * options[1][1]):
        return options[0][0]
    return None


def resolve(word, freq):
    if word.strip("".join(QUOTE_CHARS)) == "":
        # A "word" that's ONLY gershayim/geresh character(s), nothing else -
        # not an abbreviation at all, almost certainly a stray/orphaned
        # punctuation token (a missing-space or tokenization artifact - the
        # same DATA-issue class as the compound-token dropped-lamed finding
        # from the lexicon cross-check, not something to expand).
        return None, "artifact", None
    if word in ROOT_ENTRIES:
        category, expansion = ROOT_ENTRIES[word]
        return expansion, category, "root"
    # Try stripping up to 2 prefix LEVELS (e.g. ל then ה, for "to the Rosh"
    # -> "ל" + "ה" + "רא"ש"), not just one - a single-level check alone
    # misses stacked prefixes even when the bare root IS in the dictionary.
    for p1 in PREFIXES:
        if not word.startswith(p1):
            continue
        rest1 = word[len(p1):]
        if rest1 in ROOT_ENTRIES:
            category, expansion = ROOT_ENTRIES[rest1]
            return expansion, category, f"prefix {p1}- + root"
        for p2 in PREFIXES:
            if rest1.startswith(p2):
                rest2 = rest1[len(p2):]
                if rest2 in ROOT_ENTRIES:
                    category, expansion = ROOT_ENTRIES[rest2]
                    return expansion, category, f"prefix {p1}-{p2}- + root"
    truncated = resolve_truncated_word(word, freq)
    if truncated:
        return truncated, "expand", "truncated-word completion (independent corpus)"
    if looks_like_bare_numeral(word):
        return None, "numeral", None
    return None, "unresolved", None


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

    freq = load_independent_frequency()
    if freq is None:
        print("NOTE: sefaria_reference_corpus/word_freq.json not found - run "
              "fetch_sefaria_reference_corpus.py + validate_lexicon_independent.py "
              "first for truncated-word completion. Continuing without it.\n")

    report = {}
    for w, n in counts.items():
        expansion, category, method = resolve(w, freq)
        report[w] = {"count": n, "category": category, "method": method, "expansion": expansion}

    by_cat = {}
    for w, r in report.items():
        by_cat.setdefault(r["category"], {})[w] = r

    total = sum(counts.values())
    print(f"{len(counts)} unique forms, {total} occurrences.\n")
    labels = {
        "expand": "EXPAND (propose this expansion)",
        "stays": "STAYS (confirmed/analogous convention - do NOT propose expanding)",
        "name": "NAME (person/work acronym - do NOT propose expanding)",
        "scholarly": "SCHOLARLY (ambiguous referent - needs reading the passage, not a lexical candidate)",
        "numeral": "NUMERAL (citation/folio number, not a word)",
        "artifact": "ARTIFACT (stray geresh-only token - likely a data issue)",
        "unresolved": "UNRESOLVED (no dictionary entry - not guessed at)",
    }
    for cat in ["expand", "stays", "name", "scholarly", "numeral", "artifact", "unresolved"]:
        forms = by_cat.get(cat, {})
        n_occ = sum(r["count"] for r in forms.values())
        print(f"{labels[cat]}: {len(forms)} forms, {n_occ} occurrences ({n_occ/total:.1%})")

    print("\n--- Top 40 EXPAND, by frequency (the actual candidate list) ---")
    for w, r in sorted(by_cat.get("expand", {}).items(), key=lambda x: -x[1]["count"])[:40]:
        exp = r["expansion"]
        exp_str = " / ".join(exp) if isinstance(exp, list) else exp
        src = "" if r["method"] in ("root",) or (r["method"] and r["method"].startswith("prefix")) \
            else f"  [{r['method']}]"
        print(f"  {r['count']:4d}  {w:<10} -> {exp_str}{src}")

    print("\n--- SCHOLARLY forms (never auto-expand - flag for human/expert review per instance) ---")
    for w, r in sorted(by_cat.get("scholarly", {}).items(), key=lambda x: -x[1]["count"]):
        print(f"  {r['count']:4d}  {w:<10} -> one of: {', '.join(r['expansion'])}")

    print("\n--- Top 30 UNRESOLVED, by frequency ---")
    for w, r in sorted(by_cat.get("unresolved", {}).items(), key=lambda x: -x[1]["count"])[:30]:
        print(f"  {r['count']:4d}  {w}")

    if args.json:
        def ser(r):
            return {"count": r["count"], "category": r["category"], "method": r["method"],
                    "expansion": r["expansion"]}
        json.dump({w: ser(r) for w, r in report.items()}, open(args.json, "w", encoding="utf-8"),
                   ensure_ascii=False, indent=1)
        print(f"\nWrote {args.json}")


if __name__ == "__main__":
    main()
