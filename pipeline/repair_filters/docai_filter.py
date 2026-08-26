#!/usr/bin/env python3
"""
pipeline/repair_filters/docai_filter.py

DocAI alef-lamed ligature repair. MULTI-WITNESS-REPAIR-AND-SYNTHESIS-PLAN.md
§3.2, specified since the first draft and unbuilt until 2026-08-24.

WHY THIS IS THE HIGHEST-VALUE FILTER, measured rather than assumed. A reviewer
worked klal 91 end to end and recorded 22 word decisions. Scored against them,
DocAI agreed on **0 of 18** words - dead last of every witness. Applying only
this repair takes it to **17 of 18 (94%)**, ahead of every other signal
including the vision adjudicator (72%) and the stored corpus (59%).

DocAI is not a bad witness. It reads the ink correctly and faithfully reports
what the 19th-century `ﭏ` sort actually prints - a bare `א` - and nothing
downstream expands it, so its CORRECT readings are discarded as errors. The
repair is the missing half of the read.

THE ARBITER, and why the two obvious choices are unusable here:

  * `lexicon.txt` CANNOT be used. It was built from this corpus's own OCR
    output and, in this project's own words, "absorbed and then validated the
    alef-lamed ligature corruption" (see tools/validate_lexicon_independent.py).
    Asking it whether a ligature-collapsed form is a word is circular by
    construction - it contains them.
  * The vision adjudicator cannot be used either. It is a fourth reader of the
    same pixels, and a defect in the ink is upstream of every reader (Lesson 24).

  * `sefaria_reference_corpus/word_freq.json` CAN: 6.18M words of Talmud, Rashi,
    Rambam, Tur and Shulchan Arukh, with no editorial or data lineage connection
    to this scan. `איבא` occurs ZERO times there; `אליבא` occurs 848.

CONSERVATISM, deliberately, because this rewrites a witness before it votes:
a repair is proposed only when exactly ONE insertion position yields an attested
word, the collapsed form is itself unattested or far rarer, and the result clears
a frequency floor. Where two positions both produce real words the word is left
alone - a wrong expansion fabricates a reading that then carries an engine's
authority into consensus, which is worse than leaving a known artifact visible.
"""
import functools
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, "pipeline"))

import corpus_io as cio  # noqa: E402

REFERENCE_FREQ_PATH = os.path.join(REPO, "sefaria_reference_corpus", "word_freq.json")

# A repaired form must occur at least this often in the reference corpus. Guards
# against expanding into a word that exists but is vanishingly rare, where the
# collapsed form is likelier to be a different word entirely.
MIN_REPAIRED_FREQ = 5
# ...and must be at least this many times commoner than the collapsed form, so a
# collapsed form that is itself a real, common word (e.g. `אא`, 1,145) is not
# rewritten on thin evidence.
MIN_FREQ_RATIO = 3.0


@functools.lru_cache(maxsize=1)
def reference_frequencies(path=REFERENCE_FREQ_PATH):
    """{normalized word: count} from the independent reference corpus, or {} if
    the cache is absent (it is gitignored - see SETUP.md). Absent means the
    filter proposes NOTHING rather than falling back to a circular arbiter."""
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return {cio.hebrew_letters_only(w): c for w, c in json.load(f).items()}


# The gershayim characters, as opposed to the geresh ones. A gershayim sits
# BETWEEN letters and marks a multi-word abbreviation (`א"ה` = אבן העזר); a
# geresh trails and marks one truncated word (`תוס'` = תוספות).
_GERSHAYIM_CHARS = set('"״')


def _is_multiword_abbreviation(word):
    """True when a token carries an internal gershayim, i.e. its letters are
    initials of several words rather than the spelling of one."""
    if not word:
        return False
    inner = word[1:-1] if len(word) > 2 else ""
    return any(c in _GERSHAYIM_CHARS for c in inner)


def repair_word(word, freqs=None):
    """The alef-lamed-expanded form of `word`, or None to leave it alone.

    Returns None - not the input - when no repair is warranted, so callers must
    decide explicitly what an un-repaired word means to them."""
    freqs = reference_frequencies() if freqs is None else freqs
    if not word or not freqs:
        return None
    if _is_multiword_abbreviation(word):
        # An abbreviation is not a collapsed word, and this filter's whole
        # evidence base does not apply to one. FIXED 2026-08-26 (code review).
        # hebrew_letters_only() strips the marks, so `א"ה` (אבן העזר, which the
        # corpus prints as `ובחלק א"ה סימן ל"ה`) was arbitrated as the letters
        # `אה` against `אלה` and "repaired" to `א"לה` - a string that is not a
        # word, an abbreviation, or anything DocAI read. The frequency comparison
        # is against the wrong object entirely: the letters are initials, not a
        # spelling. Measured on the live DocAI stream (287,390 tokens): **97
        # tokens** rewrite this way - `א"ה` x73, `א"א` x20, `ש"א` x3, `וא"ה` x1.
        # None reaches the review queue today (0 of the current verified
        # candidates), but this feeds `docai_repaired`, which app.js offers as a
        # SELECTABLE reading - so one click would write a fabricated word into
        # the corpus carrying an engine's authority, which this module's own
        # docstring calls worse than leaving the artifact visible.
        # Deliberately NARROWER than cio.has_gershayim(), which also matches a
        # TRAILING geresh - that marks a single truncated word (`תוס'`), where
        # the letters still are a spelling and a dropped-lamed repair is a
        # sensible question. test_ligature_repair_preserves_abbreviation_marks
        # asserts that case still repairs, and it still does.
        return None
    letters = cio.hebrew_letters_only(word)
    # Either surviving half of the `ﭏ` sort is a reason to look. This used to
    # require an `א`, which silently excluded the whole dropped-alef direction
    # added below - the surviving letter there is the `ל`, and the `א` is
    # precisely what is missing.
    if "א" not in letters and "ל" not in letters:
        return None
    if len(letters) < 2:
        # A single glyph carries no evidence about what it used to be. Measured
        # 2026-08-26: without this, the bare token `ל` "repairs" to `אל` **83
        # times** in the DocAI stream - two thirds of the new dropped-alef
        # direction's entire output - purely because `אל` (4,624) happens to be
        # four times commoner than standalone `ל` (1,154) in the reference
        # corpus, which clears MIN_FREQ_RATIO by accident. `ל` is a legitimate
        # standalone token here (the preposition, an abbreviation letter, a
        # numeral). Two letters is the floor and not one more, because the
        # shortest genuine repair this filter makes is `אא`->`אלא`.
        return None

    collapsed_freq = freqs.get(letters, 0)
    candidates = []
    for i, ch in enumerate(letters):
        # The `ﭏ` sort can lose EITHER of its two letters, and this filter only
        # ever modelled one of them. ADDED 2026-08-26 (reviewer: hand-repaired
        # `לא`->`אלא` in klal 84 and asked why the pass had not found it). The
        # documented failure (Lesson 24) is the ligature dropping its `ל`
        # - `אליבא`->`איבא`, `ושמואל`->`ושמוא` - and the loop below only ever
        # inserted a `ל` AFTER an `א`. The same worn sort also prints as a bare
        # `ל`, dropping its `א`: `שמואל`->`שמול` is live in klal 143 w684
        # (`רב פפא בר שמול`). Both directions are now tried, and the "exactly one
        # candidate" rule below still arbitrates between them, so a word that
        # could be repaired either way is refused rather than guessed.
        if ch == "א":
            expanded = letters[:i + 1] + "ל" + letters[i + 1:]
        elif ch == "ל":
            expanded = letters[:i] + "א" + letters[i:]
        else:
            continue
        f = freqs.get(expanded, 0)
        if f >= MIN_REPAIRED_FREQ:
            candidates.append((expanded, f))
    candidates = list(dict.fromkeys(candidates))

    # Exactly one position may produce an attested word. Two means the evidence
    # does not identify WHICH lamed was lost, and guessing would fabricate a
    # reading that carries DocAI's authority into consensus (Lesson 5).
    if len(candidates) != 1:
        return None
    expanded, f = candidates[0]
    if collapsed_freq and f < collapsed_freq * MIN_FREQ_RATIO:
        return None

    # Re-attach whatever non-letter characters the raw token carried (gershayim,
    # geresh, punctuation) by rebuilding around the letter sequence, so a repair
    # never silently strips an abbreviation mark from the corpus's own text.
    return _reinsert_nonletters(word, letters, expanded)


def _reinsert_nonletters(raw, letters, expanded):
    """Rebuild `expanded` carrying `raw`'s non-letter characters in place.

    The inserted ל shifts every later position by one, so the marks are placed
    relative to the LETTER index they followed rather than the raw index."""
    if letters == expanded:
        return raw
    # The first LETTER index at which the two differ is where the lamed goes.
    # Comparing prefixes instead is off by one - it first differs at index+1 -
    # which put the lamed one place late and produced `אילבא` for `אליבא` and
    # `אאל` for `אלא`. Caught by the module's own smoke test before any use.
    insert_at = next((i for i in range(len(letters)) if letters[i] != expanded[i]),
                     len(letters))
    # The restored letter is whatever `expanded` has at the insertion point - NOT
    # always a `ל`. FIXED 2026-08-26: this was hardcoded to "ל", which was true
    # while the filter only modelled the ligature dropping its lamed. With the
    # dropped-ALEF direction added, the letter to restore is an `א`, and the
    # hardcoded version produced `שמול`->`שמולל` instead of `שמואל`.
    inserted = expanded[insert_at]
    out, seen = [], 0
    for ch in raw:
        if ch in cio.HEBREW_LETTERS:
            if seen == insert_at:
                out.append(inserted)
            out.append(ch)
            seen += 1
        else:
            out.append(ch)
    if seen == insert_at:
        # The lamed belongs after the LAST letter - which is not necessarily the
        # end of the raw token. FIXED 2026-08-26 (code review): appending here
        # put it after any trailing non-letter, so `בצלא.` repaired to `בצלא.ל`
        # and `בצלא'` to `בצלא'ל` instead of `בצלאל.` / `בצלאל'`. Downstream
        # comparisons normalise the marks away, so `_ligature_artifact_flag` was
        # unaffected - but the malformed string is exactly what `docai_repaired`
        # shows a reviewer and what one click can select. No live occurrence in
        # the current stream (0 of 893 repaired tokens), so this was latent.
        cut = len(out)
        while cut > 0 and out[cut - 1] not in cio.HEBREW_LETTERS:
            cut -= 1
        out.insert(cut, inserted)
    return "".join(out)


def repair_stream(words, freqs=None):
    """Apply repair_word across a witness's word list.

    Returns (repaired_words, repairs) where `repairs` is
    [(index, original, repaired), ...] - the audit trail. A filter that changes
    what a reviewer sees must be able to say exactly what it changed (§3.5)."""
    freqs = reference_frequencies() if freqs is None else freqs
    out, repairs = [], []
    for i, w in enumerate(words):
        fixed = repair_word(w, freqs)
        if fixed and fixed != w:
            repairs.append((i, w, fixed))
            out.append(fixed)
        else:
            out.append(w)
    return out, repairs
