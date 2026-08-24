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


def repair_word(word, freqs=None):
    """The alef-lamed-expanded form of `word`, or None to leave it alone.

    Returns None - not the input - when no repair is warranted, so callers must
    decide explicitly what an un-repaired word means to them."""
    freqs = reference_frequencies() if freqs is None else freqs
    if not word or not freqs:
        return None
    letters = cio.hebrew_letters_only(word)
    if "א" not in letters:
        return None

    collapsed_freq = freqs.get(letters, 0)
    candidates = []
    for i, ch in enumerate(letters):
        if ch != "א":
            continue
        expanded = letters[:i + 1] + "ל" + letters[i + 1:]
        f = freqs.get(expanded, 0)
        if f >= MIN_REPAIRED_FREQ:
            candidates.append((expanded, f))

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
    out, seen = [], 0
    for ch in raw:
        if ch in cio.HEBREW_LETTERS:
            if seen == insert_at:
                out.append("ל")
            out.append(ch)
            seen += 1
        else:
            out.append(ch)
    if seen == insert_at:      # the lamed belongs at the very end
        out.append("ל")
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
