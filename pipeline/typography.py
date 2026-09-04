#!/usr/bin/env python3
"""
pipeline/typography.py

Catalog of 19th-century Hebrew printer ligatures and combined glyph sorts as
they appear in the 1852 Berlin printing of Sefer Yad Malachi, plus the
predicates that let other pipeline stages RECOGNISE those artifacts rather
than just document them.

WHAT THIS MODULE IS NOT, corrected 2026-08-23 (code review, finding H6). As
first written this module (a) was imported by nothing at all and (b) defined
its own `CONFUSION_PAIRS` tuple while calling itself "the single source of
truth for typographic anomaly detection". There are two REAL confusion-pair
sets in this repo, they are deliberately different, and both are documented as
such:

  * pipeline/build_gematria_trace.py's CONFUSION_PAIRS - gematria-MARKER
    misreads, tuple-keyed, empirically derived from the misread markers in
    gematria_trace_part1.json. Its own comment: "Adding a pair here should
    mean someone measured it."
  * tools/detect_real_word_substitution.py's CONFUSION_PAIRS - CONTENT-WORD
    letter confusions, frozenset-keyed, different scope, cross-referenced to
    the other.

This module's third copy matched neither - it carried (ט,פ) and (ם,ס) while
dropping detect_real_word_substitution's (ט,מ) and (ס,פ), and it added pairs
nobody had measured, against that explicit instruction. A third copy of a
constant that "usually agrees" is Lesson 13 exactly, and this one did not even
usually agree. It is gone; use whichever of the two above matches your scope.
"""

# Known combined printer glyphs and ligatures used by the Berlin 1852 typesetter
PRINTER_LIGATURES_AND_GLYPHS = [
    {
        "id": "alef_lamed",
        "name": "Alef-Lamed Ligature (ﭏ)",
        "unicode": "U+FB4F",
        "composed_letters": ("א", "ל"),
        "target_string": "אל",
        "ocr_behavior": {
            "docai": "Collapses ligature to bare 'א', silently dropping 'ל'.",
            "tesseract": "Frequently misreads as 'א', 'ד', or splits into garbage tokens.",
            "vlm": "Usually transcribes 'אל' correctly from visual context - but NOT "
                   "reliably: measured 2026-08-23, the VLM and Surya reproduce DocAI's "
                   "dropped lamed often enough to reach 2-of-3 and even 3-of-3 consensus "
                   "on the corrupt form (see dropped_lamed_explains below).",
            "surya": "Also drops the lamed on this sort.",
        },
        "description": "Standard 19th-century Hebrew printing sort combining Alef and "
                       "Lamed into a single block.",
        "examples": [
            "אלא -> transcribed by DocAI as אא",
            "אלו -> transcribed by DocAI as או",
            "אליבא -> transcribed by DocAI as איבא",
        ],
        "detector_script": "tools/detect_ligature_corruption.py",
    },
    {
        "id": "chet_zayin",
        "name": "Chet-Zayin Combined Glyph / Ligature (ח+ז)",
        "unicode": None,
        "composed_letters": ("ח", "ז"),
        "target_string": "חז",
        "ocr_behavior": {
            "docai": "Occasionally reads correctly as 'חז' but with compressed bounding box.",
            "tesseract": "Misreads as 'הל' (e.g. 'חז\"ל' -> 'הלל').",
            "vlm": "Unconditioned VLM sometimes misjudges as bare 'ח\"ל' (assuming 'ז' was "
                   "omitted due to tight kern/fused left leg).",
        },
        "description": "Typesetter sort where the left leg of Chet is kerned/fused with the "
                       "head of Zayin, commonly seen in the abbreviation חז\"ל.",
        "examples": [
            "Klal 30, Token 49 (Word 166, Page 24): 'חז\"ל' printed with fused Chet-Zayin sort.",
        ],
        "detector_script": None,
    },
]


def get_ligatures():
    return PRINTER_LIGATURES_AND_GLYPHS


def dropped_lamed_explains(stored, reading):
    """True if `reading` is `stored` with exactly one ל removed from directly
    after an א - i.e. the reading is explainable as the alef-lamed ligature
    losing its lamed, rather than as a genuine disagreement about the text.

    WHY THIS EXISTS, and why it points the OPPOSITE way from
    tools/detect_ligature_corruption.py. That script asks "does the CORPUS hold
    a corrupt form?" and answers it from corpus word frequencies. This asks the
    reverse: the corpus holds the CORRECT form and a witness engine read the
    corrupt one. Measured 2026-08-23 during the first multi-witness synthesis
    run: 16 positions where two or three engines agreed on a reading that
    differs from the corpus, and EVERY ONE was this artifact -
    ושמואל->ושמוא, אלא->אא, אליבא->איבא, אלגאזי->אגאזי, אליהו->איהו, ואל->וא -
    including unanimous docai+surya+vlm agreement. Eleven of them sat on words a
    human reviewer had already correctly restored.

    That matters beyond tidiness: the defect is in the INK (one printer's sort),
    not in any model, so engine independence buys nothing against it. Under
    MULTI-WITNESS-REPAIR-AND-SYNTHESIS-PLAN.md's §2.B the joint-error
    probability for such an agreement is 3.5e-7; one Part-1 run produced 16.
    A consensus that this predicate explains must NOT be treated as evidence
    against the stored text.

    Deliberately strict - exactly one deletion, and only of a ל preceded by an
    א. A general edit-distance-1 check would match unrelated single-letter
    differences and turn a precise signal into a guess (Lesson 5)."""
    if not stored or not reading or len(reading) != len(stored) - 1:
        return False
    for i, ch in enumerate(stored):
        if ch != "ל" or i == 0 or stored[i - 1] != "א":
            continue
        if stored[:i] + stored[i + 1:] == reading:
            return True
    return False


def ligature_artifact(stored, reading):
    """The catalogued ligature id explaining `reading` as a misprint-driven
    misread of `stored`, or None. Currently only the alef-lamed sort has a
    mechanical predicate; chet-zayin is catalogued but has no detector yet
    (its `detector_script` is None), and this returns None for it rather than
    pretending otherwise."""
    if dropped_lamed_explains(stored, reading):
        return "alef_lamed"
    return None


# Marks this printing uses to signal "this word is cut short here". A geresh
# after Hebrew letters is the abbreviation mark proper; the gershayim variants
# appear in the same role in the Berlin sorts.
ABBREV_MARKS = "׳'\"״"


def abbreviation_expansion(stored, reading):
    """`reading` is `stored` with its abbreviation SPELLED OUT, or None.

    `נרא׳` against `נראה` is not a disagreement about which letters are on a
    page - it is the same word, cut short in one printing and written in full
    in another. Recognising that shape matters in two places, and this is the
    single predicate both of them use (Lesson 13 - the two would drift apart
    the moment either was tuned):

      * pipeline/build_collation_report.py, where the Berlin ink is SETTLED
        (every Berlin-reading engine agrees with the corpus) and the shape is
        therefore a genuine difference between the two printings - collation,
        never a correction.
      * pipeline/synthesize_multi_witness.py, where the Berlin ink is NOT
        settled (some Berlin engine reads it differently too) and the shape is
        a warning: a consensus that would EXPAND an abbreviation is proposing
        the exact edit item 0AQ ruled against, where the reviewer restored the
        Berlin `ומתי׳` over the editorial `ומתיר`.

    Returns the base (the stored word minus its mark) so a caller can quote
    what is being expanded. Deliberately conservative - the reading must
    CONTINUE the stored letters, not merely resemble them, because the whole
    value of this test is that it needs no judgement about which is right.
    """
    if not stored or not reading:
        return None
    base = stored.rstrip(ABBREV_MARKS)
    if base == stored:
        return None  # no abbreviation mark: nothing is being expanded
    # A bare mark with no letters (`׳` alone, which occurs as a token) leaves an
    # EMPTY base, and every string startswith("") - without this guard any
    # reading at all would come back as an "expansion" of nothing.
    if not any("א" <= c <= "ת" for c in base):
        return None
    if not reading.startswith(base) or len(reading) <= len(base):
        return None
    return base
