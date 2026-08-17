#!/usr/bin/env python3
# [STANDALONE] Detects candidate instances of the alef-lamed ligature
# extraction bug (see PROJECT-STATUS.md / PROJECT-STATUS-HISTORY.md,
# 2026-08-14/15): this print sets the letter pair א+ל as a single ligature
# glyph (Unicode U+FB4F), and DocAI reads that glyph as a bare א, silently
# dropping the lamed. 130 real instances were found and fixed in Part 1
# this way, across two review passes (a mechanical exact/prefix sweep, then
# a manual context review of the short forms that are also legitimate
# words on their own).
#
# WHY THIS IS A DETECTION SCRIPT, NOT AN INGEST-LEVEL FIX: the natural
# instinct is "map the ligature codepoint to אל in the extraction path."
# That is not possible - `docai_word_boxes/` (DocAI's raw OCR output)
# contains ZERO U+FB4F characters anywhere. DocAI's own recognition model
# already collapses the ligature to a bare א before this repo ever sees the
# text; the lamed is lost at the OCR stage, not in anything this pipeline's
# ingest code does. A true fix would require a different DocAI
# configuration/model that preserves the ligature glyph, or a different OCR
# engine entirely for the affected regions - neither achievable from this
# codebase without live experimentation against the DocAI API. This script
# is the practical alternative: find likely instances after the fact, the
# same way the original investigation did, so this class of bug doesn't
# require a fresh one-off investigation every time it needs checking again.
#
# METHOD (two passes, mirroring how the 130 real instances were found):
#   1. Mechanical: for a word W and any position where W has an א, does
#      inserting ל right after it produce a real word elsewhere in the SAME
#      file, more often than W itself occurs? If exactly one insertion
#      position qualifies, it's a candidate.
#
#      COVERAGE, corrected 2026-08-16 (code audit) - this used to claim the
#      pass "covers bare forms and all single/double-letter Hebrew prefixes
#      (ו/ה/ב/כ/ל/מ/ש/ד and their 2-letter combinations)", backed by two
#      module constants (PREFIX1, ALL_PREFIXES) that NOTHING in the file ever
#      read. There is no prefix logic here and there never was. What the
#      position scan does give for free is that a prefix is not an א, so a
#      prefixed corrupt form is scanned like any other word - but its
#      CORRECTED form is then looked up WITH the prefix attached, so a real
#      instance whose prefixed correction is rare or unattested in this file
#      is missed. That gap is real (PROJECT-STATUS.md records 5 instances the
#      original mechanical scan missed and a prefix sweep caught), and it is
#      NOT closed here: a prefix-stripping variant was measured during this
#      audit and produces 74 forms / 2,646 occurrences on Part 1, headed by
#      לא->לאל (699), הוא->הואל (381), דלא->דלאל (251) - i.e. it drowns the
#      signal, because stripping a prefix also strips the frequency evidence
#      that makes the bare comparison meaningful. Anyone closing the gap
#      needs a different discriminator, not this one with prefixes bolted on.
#
#      Second known limit, same class: the frequency table is built from the
#      part file being scanned, so the corpus is validating itself - the
#      exact independence problem PROJECT-STATUS.md records for lexicon.txt.
#      sefaria_reference_corpus/ (2026-08-16) is an independent table that
#      could be cross-checked against; it is deliberately not wired in here,
#      since doing so changes what this detector reports and that needs its
#      own verification pass, not a drive-by.
#   2. NOT automated - context review of "the candidate is also a
#      legitimate standalone word" cases (א, או, אי, איהו, וא and similar
#      short, common words). The 2026-08-15 group-3 review of exactly this
#      class in Part 1 found ~228 such occurrences, of which only 8 were
#      genuine (the rest were legitimate independent usage - a citation
#      numeral, a klal's own opening marker, ordinary disjunctions, etc.).
#      This script flags candidates in this category SEPARATELY from the
#      high-confidence ones and does not attempt to resolve them - that
#      needs a human (or an LLM) reading each in context, the way the
#      2026-08-15 pass did. See PROJECT-STATUS-HISTORY.md for that
#      method and results if repeating it.
#
# Gershayim-bearing tokens are excluded throughout: `א"ה` (Even HaEzer),
# `א"א` (eshet ish) and similar abbreviations are real, unrelated tokens
# that happen to normalize to a corrupt-looking bare form if punctuation
# isn't accounted for - this exact false-positive class was caught and
# fixed during the original investigation (see PROJECT-STATUS-HISTORY.md,
# "the `~620 ambiguous` estimate was itself wrong").
#
# This script only READS part*.json and REPORTS. It never edits anything -
# a real correction always goes through the normal manual_correction ->
# apply_reviewer_decisions.py pipeline, with a scan-verification pass
# recommended before trusting a mechanical-only hit (23 of the 130 real
# fixes were individually confirmed against the ink; the rest rested on
# the strength of the confirmed mechanism plus their own high-confidence
# frequency signal - see the two decision-note styles in
# review_decisions.jsonl for the language this project uses to keep that
# distinction honest in the audit trail).
#
# Usage: python3 detect_ligature_corruption.py [part1.json|part2.json|part3.json]
#   Defaults to part1.json. Pointing this at part2.json/part3.json is safe
#   (read-only) but per CLAUDE.md's standing directive, do not start or
#   scope any Parts 2-3 correction work from its output without the user's
#   explicit sign-off - Parts 2-3 remain out of scope until Part 1 is
#   independently confirmed clean.
import json
import os
import re
import sys
from collections import Counter

# Moved one level deeper (pipeline/ or tools/) 2026-08-16 - REPO now goes up
# two levels, not one, to keep resolving to the actual repo root where
# part1.json/docai_word_boxes/etc. live.
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pipeline"))
import corpus_io as cio  # noqa: E402

QUOTE_CHARS = set('"\'׳״')

# Short forms that are ALSO common standalone words - a mechanical hit here
# is not trustworthy on frequency alone (see METHOD pass 2 above). Reported
# separately, not folded into the high-confidence list.
AMBIGUOUS_WITH_LAMED_INSERTED = {"אל", "אלו", "אלי", "אליהו", "ואל"}


def has_gershayim(w):
    return any(c in w for c in QUOTE_CHARS)


def load_klal_words(part_path):
    """Split exactly the way every index-bearing script in this project does
    (str.split() with no argument).

    FIXED 2026-08-16 (code audit): this was `split(" ")`, which keeps an empty
    string for each run of consecutive spaces and for a leading/trailing one.
    find_candidates() reports a word_index, and a correction made from this
    script's output is recorded and applied against
    apply_reviewer_decisions.py's `clean_text.split()` indexing - so a single
    double space anywhere in a klal would silently shift every reported index
    after it by one, in the one direction that edits the corpus at a position
    nobody chose. Inert today (verified 2026-08-16: 0 klalim in any of the
    three part files where the two splits disagree), which is exactly why it
    needed a test rather than a look."""
    klalim = cio.load_klalim(part_path)
    out = {}
    for k in klalim:
        out[k["klal_id"]] = k["clean_text"].split()
    return out


def build_frequency_table(klal_words):
    counts = Counter()
    for words in klal_words.values():
        for w in words:
            if has_gershayim(w):
                continue
            counts[w] += 1
    return counts


def find_candidates(klal_words, counts):
    """Returns (high_confidence, ambiguous): each a list of
    (klal_id, word_index, corrupt_form, corrected_form, corrected_freq)."""
    high_confidence, ambiguous = [], []
    seen_forms = {}  # corrupt_form -> resolved (corrected_form or None) - cache per unique form

    for klal_id, words in klal_words.items():
        for i, w in enumerate(words):
            if has_gershayim(w) or "א" not in w:
                continue
            if w not in seen_forms:
                seen_forms[w] = _resolve(w, counts)
            corrected = seen_forms[w]
            if corrected is None:
                continue
            entry = (klal_id, i, w, corrected, counts[corrected])
            if corrected in AMBIGUOUS_WITH_LAMED_INSERTED:
                ambiguous.append(entry)
            else:
                high_confidence.append(entry)
    return high_confidence, ambiguous


def _resolve(w, counts):
    """A word is a candidate if EXACTLY ONE position of inserting ל after
    an א produces a real corpus word, and that word is meaningfully more
    frequent than the uncorrected form itself (otherwise this is more
    likely a coincidental short-word collision than a ligature drop)."""
    options = []
    for i, ch in enumerate(w):
        if ch == "א":
            candidate = w[: i + 1] + "ל" + w[i + 1 :]
            freq = counts.get(candidate, 0)
            if freq > 0:
                options.append((candidate, freq))
    if len(options) != 1:
        return None
    candidate, freq = options[0]
    if freq <= counts.get(w, 0):
        return None
    return candidate


def find_compound_candidates(klal_words, counts):
    """Returns a list of (klal_id, word_index, corrupt_form, corrected_first,
    corrected_second, second_freq): a SECOND corruption shape pass 1 above
    cannot catch (PROJECT-STATUS.md, 2026-08-16 lexicon-crosscheck spot-
    check) - "אלא" (but/rather) loses its lamed AND its following space in
    the same stroke, fusing with the next word into one token ("אלא
    אמוראי" -> "אאמוראי"), not just losing a lamed within one token.
    pass 1's `_resolve()` cannot see this: it only tries inserting ל at an
    existing א position within the SAME token, never treats part of a
    token as a second, separate word.

    Scoped narrowly to the confirmed shape, not a general split search.
    Worked out empirically from the 4 known instances (PROJECT-STATUS.md),
    not assumed: splitting each at len(word) - len(known_target) puts the
    break after the FIRST character in all 4 (אאמוראי -> א + אמוראי,
    אאיזה -> א + איזה, אאביי -> א + אביי, אאידך -> א + אידך) - i.e. the
    residue left behind by "אלא" losing its ל is a single א, not "אא";
    the SECOND leading א belongs to the fused-in following word (all 4
    of which independently happen to also start with א - a real property
    of the mechanism, not coincidence: "אלא" ends in א and the next word
    starts with א, so the space between two ALREADY-IDENTICAL adjacent
    letters is exactly where a dropped space is least visually detectable).
    Pre-filtered to tokens starting with "אא" (so the split is well-
    defined and the false-positive surface stays small), but the actual
    candidate word checked against the frequency table is `word[1:]`, not
    `word[2:]`. Same frequency discriminator as `_resolve()` above: the
    candidate must be independently attested MORE often than the whole
    unsplit token itself occurs, or this is more likely a coincidental
    collision than a genuine drop.
    """
    compound = []
    for klal_id, words in klal_words.items():
        for i, w in enumerate(words):
            if has_gershayim(w) or not w.startswith("אא") or len(w) <= 2:
                continue
            remainder = w[1:]
            if has_gershayim(remainder):
                continue
            freq = counts.get(remainder, 0)
            if freq <= 0 or freq <= counts.get(w, 0):
                continue
            compound.append((klal_id, i, w, "אלא", remainder, freq))
    return compound


def main():
    part_path = sys.argv[1] if len(sys.argv) > 1 else cio.PART1_PATH
    if not os.path.isabs(part_path):
        part_path = os.path.join(REPO, part_path)

    klal_words = load_klal_words(part_path)
    counts = build_frequency_table(klal_words)
    high_confidence, ambiguous = find_candidates(klal_words, counts)
    compound = find_compound_candidates(klal_words, counts)

    print(f"Scanned {os.path.basename(part_path)}: {len(klal_words)} klalim, "
          f"{sum(len(w) for w in klal_words.values())} words.\n")

    print(f"--- {len(high_confidence)} high-confidence candidate(s) "
          f"(not ambiguous with a common standalone word) ---")
    by_form = Counter(c[2] for c in high_confidence)
    for form, n in sorted(by_form.items(), key=lambda x: -x[1]):
        corrected = next(c[3] for c in high_confidence if c[2] == form)
        print(f"  {form!r} -> {corrected!r}: {n} occurrence(s)")

    print(f"\n--- {len(ambiguous)} ambiguous candidate(s) "
          f"(the corrected form is also a common standalone word - "
          f"needs individual context review, see module docstring) ---")
    by_form_amb = Counter(c[2] for c in ambiguous)
    for form, n in sorted(by_form_amb.items(), key=lambda x: -x[1]):
        corrected = next(c[3] for c in ambiguous if c[2] == form)
        print(f"  {form!r} -> {corrected!r}: {n} occurrence(s)")

    print(f"\n--- {len(compound)} compound-token candidate(s) "
          f"(\"אלא\" fused with the following word - see find_compound_"
          f"candidates docstring) ---")
    for klal_id, idx, form, first, second, freq in sorted(compound):
        print(f"  klal {klal_id} word {idx}: {form!r} -> {first!r} + {second!r} "
              f"({freq} independent occurrence(s) of {second!r})")

    if not high_confidence and not ambiguous and not compound:
        print("\nNone found.")


if __name__ == "__main__":
    main()
