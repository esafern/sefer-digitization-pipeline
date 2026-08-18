#!/usr/bin/env python3
# [STANDALONE] Detects candidate insertion/deletion OCR errors: a rare word
# that is one letter shorter or longer than a common word in the independent
# reference corpus.
#
# ERROR CLASS: detect_real_word_substitution.py explicitly excludes this shape
# (its own header: "ישרץ->ישראל, ליבא->אליבא, ארת->את are insertion/deletion
# errors - a missing or extra letter, a DIFFERENT shape this script does not
# attempt"). This detector covers that gap.
#
# METHOD:
#   1. For each word in Part 1 that has zero independent-corpus attestation
#      and occurs <= RARE_THRESHOLD times in Part 1 itself:
#   2. DELETION check: for each position in the word, does inserting any
#      Hebrew letter there produce a word attested >= MIN_INDEPENDENT_FREQUENCY
#      times in the reference corpus?
#   3. INSERTION check: for each position, does deleting the letter at that
#      position produce a word attested >= MIN_INDEPENDENT_FREQUENCY times?
#   4. Gershayim-bearing tokens are excluded (abbreviations, not vocabulary).
#   5. If exactly one candidate clears the bar, high-confidence. If multiple,
#      ambiguous.
#
# SCOPE, stated plainly: catches single-character insertion or deletion errors
# only. Multi-character differences (e.g. ישרץ->ישראל is a 2-char gap) are
# NOT covered. Does NOT catch errors where the corrupt form is itself
# attested in the reference corpus (same blind spot as detect_real_word_
# substitution.py, by the same logic: nonzero attestation is treated as real).
#
# FALSE-POSITIVE RATE (estimated from Part 1 spot-check of 10 high-confidence
# hits): ~30-40%. Common false positives: Aramaic emphatic forms with trailing
# alef that don't appear in the reference corpus, legitimate rare grammatical
# forms, proper nouns. The zero-attestation requirement is the main filter,
# but Rabbinic Hebrew has many legitimate forms the Sefaria reference corpus
# (Talmud Bavli + Shulchan Arukh, 2.58M words) doesn't cover. Of the 139
# high-confidence hits on Part 1, 106 are unique (not caught by
# detect_real_word_substitution.py), making this detector complementary.
#
# Read-only: never edits any corpus file. Safe to run on part2.json/part3.json
# but per CLAUDE.md scope rules, do not start Parts 2-3 correction work from
# its output without the user's explicit sign-off.
#
# Usage: python3 detect_insertion_deletion.py [part1.json|part2.json|part3.json]
import os
import sys
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pipeline"))
sys.path.insert(0, os.path.join(REPO, "tools"))
import corpus_io as cio  # noqa: E402

RARE_THRESHOLD = 2
MIN_INDEPENDENT_FREQUENCY = 200
# Minimum word length (Hebrew letters only) to consider. Short words have too
# many one-edit neighbours to be informative.
MIN_WORD_LENGTH = 4
# How many times more frequent the candidate must be than any competing
# candidate to be considered unambiguous.
DOMINANCE_RATIO = 5

KNOWN_FALSE_POSITIVES = {
}


def load_independent_frequency():
    """Load the Sefaria reference corpus frequency table via the same loader
    detect_real_word_substitution.py uses."""
    import propose_abbreviation_expansions as pae
    return pae.load_independent_frequency()


def find_candidates(klal_words, own_counts, indep_freq):
    """Returns (high_confidence, ambiguous).
    high_confidence: [(klal_id, word_index, corrupt, corrected, edit_type, freq)]
    ambiguous: [(klal_id, word_index, corrupt, [(corrected, edit_type, freq), ...])]
    """
    high_confidence, ambiguous = [], []
    seen_forms = {}

    for klal_id, words in klal_words.items():
        for i, w in enumerate(words):
            if cio.has_gershayim(w) or own_counts.get(w, 0) > RARE_THRESHOLD:
                continue
            if (klal_id, i, w) in KNOWN_FALSE_POSITIVES:
                continue
            if w not in seen_forms:
                seen_forms[w] = _resolve(w, indep_freq)
            result = seen_forms[w]
            if result is None:
                continue
            is_ambiguous, options = result
            if is_ambiguous:
                ambiguous.append((klal_id, i, w, options))
            else:
                corrected, edit_type, freq = options[0]
                high_confidence.append((klal_id, i, w, corrected, edit_type, freq))
    return high_confidence, ambiguous


def _resolve(w, indep_freq):
    """Check if w is one insertion or deletion away from a well-attested word.
    Returns None, or (is_ambiguous, options) where options is [(word, edit_type, freq)]."""
    heb = cio.hebrew_letters_only(w)
    if not heb or len(heb) < MIN_WORD_LENGTH:
        return None
    if indep_freq.get(heb, 0) != 0:
        return None  # word is independently attested -> not flagged

    options = []
    seen = set()
    letters = cio.HEBREW_LETTERS

    # Common Hebrew prefixes that attach to words. A "deletion" that just
    # strips a standard prefix is almost always a legitimate prefixed form,
    # not an OCR error. Similarly, "inserting" a prefix letter at position 0
    # is not evidence of a deleted letter - it's evidence of a prefix the
    # reference corpus happens to store without it.
    PREFIXES = set("ובכלמשהד")

    # DELETION from corpus word (= insertion into candidate): try inserting
    # each Hebrew letter at each position in w to see if we get a common word.
    # Skip position 0 insertions of common prefix letters (those are the
    # prefix-detection problem, not insertion/deletion OCR errors).
    for i in range(len(heb) + 1):
        for ch in letters:
            if i == 0 and ch in PREFIXES:
                continue  # skip: adding a prefix is not evidence of OCR deletion
            candidate = heb[:i] + ch + heb[i:]
            if candidate in seen:
                continue
            seen.add(candidate)
            freq = indep_freq.get(candidate, 0)
            if freq >= MIN_INDEPENDENT_FREQUENCY:
                options.append((candidate, "deleted_char", freq))

    # INSERTION into corpus word (= deletion from candidate): try removing
    # each character from w to see if we get a common word.
    # Skip position 0 removals of common prefix letters.
    for i in range(len(heb)):
        if i == 0 and heb[i] in PREFIXES:
            continue  # skip: stripping a prefix is not evidence of OCR insertion
        candidate = heb[:i] + heb[i + 1:]
        if candidate in seen or len(candidate) < 2:
            continue
        seen.add(candidate)
        freq = indep_freq.get(candidate, 0)
        if freq >= MIN_INDEPENDENT_FREQUENCY:
            options.append((candidate, "extra_char", freq))

    if not options:
        return None
    options.sort(key=lambda x: -x[2])
    if len(options) == 1:
        return False, options
    # Check if top option dominates
    is_ambiguous = options[0][2] <= DOMINANCE_RATIO * options[1][2]
    return is_ambiguous, options


def main():
    part_path = sys.argv[1] if len(sys.argv) > 1 else cio.PART1_PATH
    if not os.path.isabs(part_path):
        part_path = os.path.join(REPO, part_path)

    indep_freq = load_independent_frequency()
    if indep_freq is None:
        print("Independent reference corpus not available - nothing to score against. "
              "Run fetch_sefaria_reference_corpus.py + validate_lexicon_independent.py first.")
        return

    klal_words = cio.load_klal_words(part_path)
    own_counts = Counter()
    for words in klal_words.values():
        for w in words:
            if not cio.has_gershayim(w):
                own_counts[w] += 1

    high_confidence, ambiguous = find_candidates(klal_words, own_counts, indep_freq)

    total_words = sum(len(w) for w in klal_words.values())
    print(f"Scanned {os.path.basename(part_path)}: {len(klal_words)} klalim, "
          f"{total_words} words, against {len(indep_freq)} independent-corpus forms.\n")

    print(f"--- {len(high_confidence)} high-confidence candidate(s) "
          f"(exactly one insertion/deletion clears the bar) ---")
    for kid, idx, corrupt, corrected, edit_type, freq in sorted(high_confidence, key=lambda e: (e[0], e[1])):
        own_n = own_counts.get(corrupt, 0)
        print(f"  klal {kid} word {idx}: {corrupt!r} -> {corrected!r} "
              f"({edit_type}, corrupt {own_n}x in Part 1; correction {freq}x independently)")

    print(f"\n--- {len(ambiguous)} ambiguous candidate(s) ---")
    for kid, idx, corrupt, options in sorted(ambiguous, key=lambda e: (e[0], e[1])):
        opts_str = " | ".join(f"{c!r} ({t}, {f}x)" for c, t, f in options[:5])
        if len(options) > 5:
            opts_str += f" | ... ({len(options)} total)"
        print(f"  klal {kid} word {idx}: {corrupt!r} -> {opts_str}")

    if not high_confidence and not ambiguous:
        print("\nNone found.")


if __name__ == "__main__":
    main()
