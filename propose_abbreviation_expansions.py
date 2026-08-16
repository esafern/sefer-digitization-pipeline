#!/usr/bin/env python3
# [STANDALONE] Candidate expansions for Part 1's abbreviation-marked tokens.
# It re-derives that token list from part1.json directly, using the SAME
# is_abbreviation() rule as extract_abbreviation_forms.py (which prints the
# canonical list, with per-klal attribution, and is the file to read for the
# definition's rationale) - it does not read that script's output.
# tests/test_pipeline_logic.py asserts the two rules still agree, since they
# are two copies of one definition (CLAUDE.md Lesson 13).
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
#   (truncated/numeral/artifact/unresolved are separate, non-dictionary
#   paths - see below and the category labels in main())
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
# CORRECTED 2026-08-16 (code audit) - the completion above gets its OWN
# category, "truncated", and is NOT merged into "expand". It appends exactly
# ONE letter, so its candidate space structurally cannot contain a
# multi-letter truncation, and the "one clear winner" test it applies is a
# question about FREQUENCY, not about correctness: it cannot tell "the right
# answer dominates" from "the right answer isn't on the ballot and some other
# real word won by default." Two confirmed misses, both previously reported
# under "EXPAND (propose this expansion)" with no visible difference from a
# hand-checked dictionary entry:
#   בפי' -> proposed בפיו ("in his mouth"); all 10 Part-1 occurrences are
#           בפירוש ("in the commentary of ..."): "בפי' רש"י על החומש",
#           "בפי' המשנה", "בפי' המצות".
#   בחי' -> proposed בחיי; all 4 occurrences are בחידושי ("in the novellae
#           of the Rashba / Ritva"): "בחי' הרשב"א", "בחי' יבמות שלו".
# Both now have dictionary roots (פי', חי'). The category split is the
# durable fix: the NEXT such form must not be presented as a peer of an
# editorially-confirmed expansion (Lesson 2 - a passing score is a triage
# signal, not a checked result).
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
# The subset of QUOTE_CHARS that can mark a SINGLE-word abbreviation by
# sitting last (ASCII apostrophe, and the real Hebrew geresh U+05F3 it is
# normalised from). part1.json today contains only the ASCII forms (6399 x
# '"', 3219 x "'", 0 x U+05F3/U+05F4, counted 2026-08-16), but the geresh
# member is not decoration: without it, a future normalisation pass to real
# Hebrew punctuation would silently switch off every geresh-shaped path in
# this file (numeral detection AND truncated-word completion) while
# is_abbreviation() kept matching, i.e. the forms would not disappear, they
# would all land in UNRESOLVED with no error.
GERESH_CHARS = {"'", "׳"}
SEFARIA_FREQ_CACHE = os.path.join(REPO, "sefaria_reference_corpus", "word_freq.json")

# Standard Hebrew prefixes this print attaches directly to a word with no
# space (ordinary Hebrew morphology, not an OCR artifact). ORDER HERE IS NOT
# THE PRIORITY ORDER - see prefix_decompositions(), which sorts candidates by
# LONGEST REMAINING ROOT. This list only has to contain each prefix cluster;
# multi-letter entries earn their place for words the 2-level stripper cannot
# reach (e.g. "ושב"), not for precedence.
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
    # MOVED from "expand" 2026-08-16 (code audit). It was proposing רצה לומר
    # unconditionally for 47 occurrences (ר"ל 28 + ור"ל 11 + דר"ל 8), but BOTH
    # referents are demonstrably live in Part 1's own text, and only reading
    # the passage separates them - the exact ר"י case this category exists for:
    #   ריש לקיש (the sage): klal 16 "ר' יוחנן אמר עשירי כתשיעי ר"ל אמר עשירי
    #     כי"א", klal 74 "אמר ר' יוחנן אמר ר"ל", klal 75 "תלמידו של ר"ל משום
    #     ר"ל", klal 39 "ר"ל או רבה או רב יוסף".
    #   רצה לומר (the phrase): klal 30 "אין היקש למחצה ר"ל דלית לן למילף".
    "ר\"ל": ("scholarly", ["רצה לומר", "ריש לקיש (the sage, esp. paired with ר' יוחנן)"]),

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
    "ל\"פ": ("expand", "לא פליג"),
    "אע\"ג": ("expand", "אף על גב"),
    "אע\"פ": ("expand", "אף על פי"),
    "אפ\"ה": ("expand", "אף על פי כן"),
    "ל\"ל": ("expand", "למאי לן"),
    "ל\"ד": ("expand", "לאו דוקא"),
    # CORRECTED 2026-08-16 (code audit): was "מנא לן", which is מנ"ל (added
    # below), not מ"ל. All 3 Part-1 occurrences are klal 54's Talmudic
    # "מ"ל חומרא רבא מ"ל חומרא זוטא" - "what difference to me a great
    # stringency, what difference a small one" - i.e. מה לי, a rhetorical
    # comparison, not a source-question.
    "מ\"ל": ("expand", "מה לי"),
    # Added with it: מנ"ל was resolving as prefix מ- + root נ"ל, giving
    # "מנראה לי". Both occurrences (klal 2 "טומאה בעזרה מנ"ל", klal 54
    # "לא תעשה שיש בו כרת מנ"ל דדחי") are the standard source-question.
    "מנ\"ל": ("expand", "מנא לן"),
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

    # ---- ADDED 2026-08-16 (code audit). Each of these was previously
    # mis-routed, and every one is verified against its own Part-1 contexts
    # (counts and the distributional evidence are in the audit entry in
    # PROJECT-STATUS.md), not assumed from convention. ----
    # Was resolving as prefix "מש-" + root א"כ -> "אם כן". משא"כ is a single
    # fixed phrase; "מש" is not a prefix on it. All 5 occurrences read
    # "...unlike in X" (klal 3/25/167/177/178), never "...if so".
    "משא\"כ": ("expand", "מה שאין כן"),
    # These four were falling through to NUMERAL, whose label asserts
    # "citation/folio number, not a word". They are ordinary single-word
    # abbreviations, and three of them are frequent:
    #   מה' (122x) is always a perek citation + a Rambam laws-topic:
    #     "בפרק ג' מה' עבודה זרה", "פ"ה מה' תרומות" - i.e. מהלכות.
    #   גמ' (2x) is "אבל גמ' דידן", "בכוליה גמ'" - i.e. גמרא.
    #   בפי' (10x) is unambiguously the noun with its ב: "בפי' רש"י על
    #     החומש", "בפי' המשנה", "בפי' המצות" - i.e. בפירוש. It gets its own
    #     entry rather than riding on פי' below, because the bare form is
    #     NOT unambiguous.
    #   חי' is not attested bare, only prefixed - it is here so בחי' (4x,
    #     "בחי' הרשב"א"/"בחי' יבמות") resolves to בחידושי rather than to the
    #     completion's בחיי. That repair is the prefix path working, which is
    #     why it is a root and not a hard-coded prefixed form.
    "מה'": ("expand", "מהלכות"),
    "גמ'": ("expand", "גמרא"),
    "בפי'": ("expand", "בפירוש"),
    "חי'": ("expand", "חידושי"),
    # Also rescued from NUMERAL, but two-way, so scholarly rather than expand
    # - the reading is a real textual difference, and nothing in the token
    # decides it:
    #   פי' (24x) is the noun פירוש in "בפי' המשנה"-type citations but the
    #     VERB פירש in "ואתה תחזה שפי' אין ג"ש", "בערך ער שפי' כן בשם גאון",
    #     "פי' ר' בצלאל בשיטתו המקובצת" ("R. Betzalel explained").
    #   הל' (14x) is singular הלכה before a letter-numeral ("מה' מילה הל'
    #     ז'") but plural הלכות as a work-title ("בפירושו להל' גיטין",
    #     klal 93).
    "פי'": ("scholarly", ["פירוש (the noun)", "פירש (the verb, 'he explained')"]),
    "הל'": ("scholarly", ["הלכה (singular, before a numeral)",
                           "הלכות (plural, as a section title: להל' גיטין)"]),
    # Genuinely two-way, so "scholarly" rather than "expand" even though the
    # header's Machon Yerushalayim comparison confirmed the prose reading:
    # the editorial rule it confirmed was "bare פ' used as an ordinary noun,
    # NOT part of a number-citation", and which one a given token is cannot
    # be decided from the token. Both readings occur in Part 1:
    #   פ' (31x): "פ' אין דורשין", "ריש פ' במה מדליקין" -> פרק ... but the
    #     same shape is gematria 80 in a folio position.
    #   ס' (41x): "הגיע לידי ס' מוצל מאש" -> ספר; "ובפרק ארבע מיתות ס' ב'"
    #     -> folio 60, side 2. Same token, both in Part 1.
    # Listing them here (rather than leaving them in NUMERAL) is the point:
    # they were being silently counted as numbers.
    "פ'": ("scholarly", ["פרק (as an ordinary noun before a chapter name)",
                          "gematria 80 (a folio/siman number)"]),
    "ס'": ("scholarly", ["ספר", "gematria 60 (a folio number)"]),

    # Not actually abbreviations - full words that happen to carry an
    # apostrophe/quote in this corpus's text (kept so the resolver has
    # somewhere to route them instead of silently mis-flagging as unresolved)
    "מיהו": ("stays", "מיהו (not an abbreviation - full word, \"however\")"),
    "מיהת": ("stays", "מיהת (not an abbreviation - full word)"),
    "דהיינו": ("stays", "דהיינו (not an abbreviation - full word)"),
    "איתא": ("stays", "איתא (not an abbreviation - full word)"),
}


# Every category resolve() can return, with the wording the report uses. Kept
# module-level (not inline in main()) so tests/test_pipeline_logic.py can
# assert that resolve()'s whole output range is labelled - the same guard
# tests/test_pipeline_logic.py already applies to review_server.FLAG_LABELS,
# for the same reason: an unlabelled classification is invisible rather than
# loud.
CATEGORY_LABELS = {
    "expand": "EXPAND (propose this expansion)",
    "stays": "STAYS (confirmed/analogous convention - do NOT propose expanding)",
    "name": "NAME (person/work acronym - do NOT propose expanding)",
    "scholarly": "SCHOLARLY (ambiguous referent - needs reading the passage, not a lexical candidate)",
    "truncated": ("TRUNCATED (single-letter completion from the independent corpus - a FREQUENCY "
                  "guess, weaker evidence than every category above)"),
    "numeral": "NUMERAL (geresh-final short letter-run - reads as a citation/folio number)",
    "artifact": "ARTIFACT (stray geresh-only token - likely a data issue)",
    "unresolved": "UNRESOLVED (no dictionary entry - not guessed at)",
}
CATEGORY_ORDER = ["expand", "stays", "name", "scholarly", "truncated",
                  "numeral", "artifact", "unresolved"]


def is_abbreviation(word):
    return any(c in word for c in QUOTE_CHARS)


def ends_in_bare_geresh(word):
    """A letter-run plus ONE trailing geresh and no other quote mark - the
    shape shared by a citation numeral (ב') and a truncated word (נרא').
    Gershayim-marked forms are excluded here even when their gematria value
    would also read as a number (e.g. י"ד), because those are exactly the
    cases genuinely ambiguous with a real word abbreviation and belong in
    ROOT_ENTRIES as an explicit entry, not silently classified either way."""
    return (len(word) >= 2 and word[-1] in GERESH_CHARS
            and all(c not in QUOTE_CHARS for c in word[:-1]))


# The stem-length boundary that splits the one geresh-final SHAPE into its two
# readings. It is a single cut, deliberately: at or below it a form is treated
# as a citation numeral, above it as a truncated word offered to
# resolve_truncated_word(). 2 is the widest a bare gematria numeral gets here
# without gershayim - 15/16 and everything from 100 up take the gershayim form
# (ט"ו, ת"ק), which ends_in_bare_geresh() already excludes.
#
# FIXED 2026-08-16 (code audit): looks_like_bare_numeral() had NO upper bound,
# contradicting its own docstring ("a single Hebrew letter or short letter-
# run"). Because resolve() falls back to it after truncated-word completion
# declines, every long geresh-final word the completion could not answer was
# labelled "NUMERAL (citation/folio number, not a word)" - 187 forms / 249
# occurrences of obvious Hebrew prose: ובקדושין', וכדכתיבנ', דתלמידי',
# התוספו', ולכאורי'. They now land in UNRESOLVED, which is where a human
# looks. This is Lesson 15's shape: the pipeline was not scoring them low, it
# was filing them under a heading that says they need no attention at all.
MAX_NUMERAL_STEM_LETTERS = 2
MIN_TRUNCATION_STEM_LETTERS = 3


def looks_like_bare_numeral(word):
    return ends_in_bare_geresh(word) and len(word) - 1 <= MAX_NUMERAL_STEM_LETTERS


# Common Hebrew word-final letters a single-geresh truncation could be
# standing in for. ORDER IS NOT SIGNIFICANT - every candidate is scored and
# the survivors are sorted by frequency below. (The order used to carry a
# comment claiming ה/ו/א/ן were "tried before the rarer ones"; they are not
# tried in any order, and the list did not match that claim anyway.)
# COVERAGE, which is significant: this is a proper subset of the alphabet,
# and only ONE letter is ever appended, so a form truncated by two or more
# letters (בפי' -> בפירוש) has no correct candidate to find. See the
# TRUNCATED-WORD note in the header for why that failure is silent.
WORD_FINAL_CANDIDATES = list("הואיןםךרלת")

# A completion must clear MIN_COMPLETION_FREQUENCY occurrences in the
# independent Sefaria reference corpus (Shulchan Arukh + Talmud Bavli, ~10^6
# words) to count as attested at all, and beat the runner-up by
# DOMINANCE_RATIO to count as the single clear winner. Both are uncalibrated
# triage cut-offs chosen to be visibly strict rather than derived from a
# labelled sample - there is no labelled sample. They bound how often the
# mechanism answers, NOT how often it is right (the בפי'/בחי' misses in the
# header both cleared these thresholds comfortably), which is why the whole
# category is reported separately from the dictionary.
MIN_COMPLETION_FREQUENCY = 50
DOMINANCE_RATIO = 5


def load_independent_frequency():
    if not os.path.exists(SEFARIA_FREQ_CACHE):
        return None
    return json.load(open(SEFARIA_FREQ_CACHE, encoding="utf-8"))


def resolve_truncated_word(word, freq):
    """For a geresh-final form with no dictionary root, try appending each
    candidate final letter to the stem and see whether EXACTLY ONE completion
    is well-attested in the independent Sefaria corpus (or dominates the
    others by DOMINANCE_RATIO) - the same one-clear-winner shape
    detect_ligature_corruption.py uses for the dropped-lamed bug, reused for a
    missing WORD-ENDING instead of a missing LETTER.

    Returns a completion or None. A returned completion is a FREQUENCY
    finding, not a verified reading - see MIN_COMPLETION_FREQUENCY and the
    header's בפי'/בחי' counterexamples for why its caller files it under its
    own category rather than under "expand".
    """
    if freq is None or not ends_in_bare_geresh(word):
        return None
    stem = word[:-1]
    if len(stem) < MIN_TRUNCATION_STEM_LETTERS:
        # Short stems are where this went wrong in testing: "דר'"
        # (stem "דר", 64 occurrences) matched "דרך" and "ור'" (stem "ור",
        # 44 occurrences) matched "ורן" - both real independent-corpus
        # words, both almost certainly WRONG here, because "ר'" (Rabbi) is
        # itself a hyper-common standalone title-abbreviation this text
        # attaches prefixes to, not a truncated single word - now handled
        # by the "ר'" root entry above instead, which is checked first.
        # Excluding shorter stems trades a handful of lower-confidence hits
        # (שר'->שרי, וס'->וסת) for not repeating the same failure mode on
        # the next short stem. The cut-off is shared with
        # MAX_NUMERAL_STEM_LETTERS so the two readings of one shape partition
        # exactly, with no stem length falling to both or to neither.
        return None
    options = []
    for letter in WORD_FINAL_CANDIDATES:
        candidate = stem + letter
        f = freq.get(candidate, 0)
        if f > MIN_COMPLETION_FREQUENCY:
            options.append((candidate, f))
    options.sort(key=lambda x: -x[1])
    if len(options) == 1 or (len(options) > 1 and options[0][1] > DOMINANCE_RATIO * options[1][1]):
        return options[0][0]
    return None


def prefix_decompositions(word):
    """Every (prefix, root_candidate) split of `word` using up to 2 prefix
    LEVELS (e.g. ל then ה, for "to the Rosh" -> "ל" + "ה" + "רא"ש"), ordered
    by LONGEST REMAINING ROOT first.

    The order is the correctness-relevant part. It used to be "longest prefix
    first, and both levels of a given p1 before the next p1", which prefers
    the decomposition that eats the MOST of the word - the opposite of what
    identifies an abbreviation, since a longer surviving root is a more
    specific dictionary match. Confirmed wrong on real Part-1 forms
    (2026-08-16 code audit):
      ומוהר"ש -> was read as ומ- + וה- + ר"ש, i.e. the word's own letters
        מוה re-analysed as prefixes, giving SCHOLARLY ["רבי שמעון", ...];
        the root מוהר"ש (NAME, מורנו הרב רבי שמואל) is right there.
      ומהר"י  -> same shape: ומ- + ה- + ר"י (SCHOLARLY) instead of ו- +
        מהר"י (NAME).
      ולמ"ד   -> ול- + מ"ד ("מאן דאמר") instead of ו- + למ"ד ("למאן דאמר"),
        swallowing the ל that is part of the abbreviation.
    In each case the category or the expansion itself flipped, silently.
    """
    splits = []
    for p1 in PREFIXES:
        if not word.startswith(p1):
            continue
        rest1 = word[len(p1):]
        splits.append((p1, rest1))
        for p2 in PREFIXES:
            if p2 == p1:
                # No Hebrew proclitic stacks on a copy of itself (ד-ד-, ו-ו-,
                # ב-ב- ...). Without this the 2-level stripper manufactures
                # roots out of the word's own letters: דדחי' (1x, really
                # ד + a truncated דחי') was decomposed as ד-ד- + חי' and
                # proposed as "דדחידושי".
                continue
            if rest1.startswith(p2):
                splits.append((p1 + p2, rest1[len(p2):]))
    # Stable sort: within one prefix length, PREFIXES' own order still decides.
    splits.sort(key=lambda pr: len(pr[0]))
    return splits


def apply_prefix(prefix, expansion):
    """Re-attach a stripped prefix to a proposed expansion.

    FIXED 2026-08-16 (code audit). resolve() used to return the ROOT's
    expansion verbatim for a prefixed form, so the report proposed
    `דר' -> רבי` (dropping the ד), `התוס' -> תוספות` (dropping the ה),
    `ובס' -> בספר` (dropping the ו) - 113 forms / 642 occurrences, every one
    of them printed in the same column, in the same format, as an unprefixed
    root hit, with the prefix visible only in a `method` string the report
    deliberately suppressed for prefix rows. Anything built on top of this
    that substituted `expansion` for the token would have DELETED a real
    Hebrew letter from the corpus - a Success-Criterion-1 fidelity failure
    originating in a read-only proposal file.

    Only "expand" values are proposals; the other categories' strings are
    glosses ("רבי שלמה יצחקי (Rashi)"), so prefixing them would produce
    nonsense. resolve() therefore calls this for "expand" only, and reports
    `root`/`prefix` separately so no consumer has to parse `method`.

    Re-attachment is plain concatenation onto the expansion's FIRST word,
    which is correct Hebrew for a proclitic on a noun (ד + רבי -> דרבי,
    ה + תוספות -> התוספות) but can read awkwardly on a multi-word verbal
    phrase (ב + "צריך עיון" -> "בצריך עיון", 3x). That is a reviewer's call,
    and it is the point of surfacing it: the letter is now visible in the
    proposal instead of silently absent from it. Nothing here decides
    idiom - a prefixed proposal is a candidate, exactly like every other.
    """
    if isinstance(expansion, list):
        return [prefix + e for e in expansion]
    return prefix + expansion


def resolve(word, freq):
    """Classify one abbreviation-marked token.

    Returns a dict: expansion, category, method, root, prefix. `expansion` is
    a proposal ONLY when category == "expand"; for every other category it is
    an explanatory gloss (or a list of possible readings) and must never be
    substituted into the text.
    """
    def out(expansion, category, method, root=None, prefix=""):
        return {"expansion": expansion, "category": category, "method": method,
                "root": root, "prefix": prefix}

    if word.strip("".join(QUOTE_CHARS)) == "":
        # A "word" that's ONLY gershayim/geresh character(s), nothing else -
        # not an abbreviation at all, almost certainly a stray/orphaned
        # punctuation token (a missing-space or tokenization artifact - the
        # same DATA-issue class as the compound-token dropped-lamed finding
        # from the lexicon cross-check, not something to expand).
        return out(None, "artifact", None)
    if word in ROOT_ENTRIES:
        category, expansion = ROOT_ENTRIES[word]
        return out(expansion, category, "root", root=word)
    for prefix, root in prefix_decompositions(word):
        if root in ROOT_ENTRIES:
            category, expansion = ROOT_ENTRIES[root]
            if category == "expand":
                expansion = apply_prefix(prefix, expansion)
            return out(expansion, category, f"prefix {prefix}- + root",
                       root=root, prefix=prefix)
    truncated = resolve_truncated_word(word, freq)
    if truncated:
        return out(truncated, "truncated", "truncated-word completion (independent corpus)")
    if looks_like_bare_numeral(word):
        return out(None, "numeral", None)
    return out(None, "unresolved", None)


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
        report[w] = {"count": n, **resolve(w, freq)}

    by_cat = {}
    for w, r in report.items():
        by_cat.setdefault(r["category"], {})[w] = r

    total = sum(counts.values())
    if not total:
        print("No abbreviation-marked tokens found in part1.json.")
        return
    print(f"{len(counts)} unique forms, {total} occurrences.\n")
    for cat in CATEGORY_ORDER:
        forms = by_cat.get(cat, {})
        n_occ = sum(r["count"] for r in forms.values())
        print(f"{CATEGORY_LABELS[cat]}: {len(forms)} forms, {n_occ} occurrences ({n_occ/total:.1%})")
    # Every category must be accounted for above; a new one added to resolve()
    # without a label would otherwise vanish from the summary while still
    # appearing in --json.
    unlabelled = sorted(set(by_cat) - set(CATEGORY_ORDER))
    assert not unlabelled, f"resolve() produced unlabelled categories: {unlabelled}"

    print("\n--- Top 40 EXPAND, by frequency (the actual candidate list) ---")
    for w, r in sorted(by_cat.get("expand", {}).items(), key=lambda x: -x[1]["count"])[:40]:
        exp = r["expansion"]
        exp_str = " / ".join(exp) if isinstance(exp, list) else exp
        via = f"  [{r['prefix']}- + {r['root']}]" if r["prefix"] else ""
        print(f"  {r['count']:4d}  {w:<10} -> {exp_str}{via}")

    print("\n--- TRUNCATED (frequency-based single-letter completion, NOT a checked "
          "reading - see the header; בפי'/בחי' were both wrong) ---")
    for w, r in sorted(by_cat.get("truncated", {}).items(), key=lambda x: -x[1]["count"]):
        print(f"  {r['count']:4d}  {w:<10} -> {r['expansion']}?")

    print("\n--- SCHOLARLY forms (never auto-expand - flag for human/expert review per instance) ---")
    for w, r in sorted(by_cat.get("scholarly", {}).items(), key=lambda x: -x[1]["count"]):
        print(f"  {r['count']:4d}  {w:<10} -> one of: {', '.join(r['expansion'])}")

    print("\n--- Top 30 UNRESOLVED, by frequency ---")
    for w, r in sorted(by_cat.get("unresolved", {}).items(), key=lambda x: -x[1]["count"])[:30]:
        print(f"  {r['count']:4d}  {w}")

    if args.json:
        json.dump(report, open(args.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"\nWrote {args.json} ({len(report)} forms, every counted form included)")


if __name__ == "__main__":
    main()
