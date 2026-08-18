#!/usr/bin/env python3
# [STANDALONE] Detects non-lexicon words that appear across multiple klalim,
# suggesting a systematic OCR confusion rather than a one-off typo.
#
# ERROR CLASS: The same misspelling appearing in >= MIN_KLALIM different klalim
# suggests a consistent OCR pattern (e.g. the same letter pair being confused
# systematically) rather than a random one-off error. These are higher-priority
# candidates because fixing them corrects multiple locations at once.
#
# METHOD:
#   1. Collect every word from the corpus.
#   2. For each word NOT in lexicon.txt AND with zero independent-corpus
#      attestation, count how many distinct klalim it appears in.
#   3. Flag words appearing in >= MIN_KLALIM klalim.
#   4. Exclude gershayim-bearing tokens (abbreviations).
#
# SCOPE: This is a broader sweep than any single-klal RARE_THRESHOLD. A word
# might appear 1x in each of 5 klalim (5 total, never triggering a per-klal
# rarity check) but still be a systematic OCR error. This detector catches
# that shape.
#
# DOES NOT CATCH: errors where the corrupt form is in lexicon.txt or has
# independent attestation (same blind spot as the lexicon-based checks, by
# the same logic). Also does not diagnose WHAT the error is - it only flags
# the form; other detectors (substitution, insertion/deletion, ligature) may
# already have a specific correction candidate for the same word.
#
# FALSE-POSITIVE RATE (estimated from Part 1): ~20-30%. Most flagged forms
# are genuine Rabbinic vocabulary that the reference corpus doesn't cover
# (period-specific terms, author names, rare grammatical forms). The zero-
# attestation + multi-klal requirement keeps the list short enough for
# manual review.
#
# Read-only: never edits any corpus file.
#
# Usage: python3 detect_cross_klal_errors.py [part1.json|part2.json|part3.json]
import os
import sys
from collections import Counter, defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pipeline"))
sys.path.insert(0, os.path.join(REPO, "tools"))
import corpus_io as cio  # noqa: E402

MIN_KLALIM = 3  # a form must appear in this many distinct klalim to be flagged

KNOWN_FALSE_POSITIVES = {
}


def load_independent_frequency():
    import propose_abbreviation_expansions as pae
    return pae.load_independent_frequency()


def find_cross_klal_suspects(klal_words, lexicon, indep_freq):
    """Returns list of (word, klal_count, total_count, klal_ids) for words
    appearing in >= MIN_KLALIM klalim, not in lexicon, not independently attested."""
    # Collect per-word stats
    word_klalim = defaultdict(set)
    word_counts = Counter()

    for klal_id, words in klal_words.items():
        for w in words:
            if cio.has_gershayim(w):
                continue
            heb = cio.hebrew_letters_only(w)
            if not heb or len(heb) < 3:
                continue
            word_klalim[heb].add(klal_id)
            word_counts[heb] += 1

    results = []
    for heb, klalim in word_klalim.items():
        if len(klalim) < MIN_KLALIM:
            continue
        if indep_freq.get(heb, 0) > 0:
            continue
        in_lexicon = heb in lexicon
        results.append((heb, len(klalim), word_counts[heb], sorted(klalim), in_lexicon))

    results.sort(key=lambda x: (-x[1], -x[2], x[0]))
    return results


def main():
    part_path = sys.argv[1] if len(sys.argv) > 1 else cio.PART1_PATH
    if not os.path.isabs(part_path):
        part_path = os.path.join(REPO, part_path)

    indep_freq = load_independent_frequency()
    if indep_freq is None:
        print("Independent reference corpus not available. "
              "Run fetch_sefaria_reference_corpus.py + validate_lexicon_independent.py first.")
        return

    lexicon_path = cio.LEXICON_PATH
    if not os.path.exists(lexicon_path):
        print("lexicon.txt not found.")
        return
    lexicon = set(w.strip() for w in open(lexicon_path, encoding="utf-8") if w.strip())

    klal_words = cio.load_klal_words(part_path)
    results = find_cross_klal_suspects(klal_words, lexicon, indep_freq)

    total_words = sum(len(w) for w in klal_words.values())
    print(f"Scanned {os.path.basename(part_path)}: {len(klal_words)} klalim, "
          f"{total_words} words.\n")

    not_in_lex = [r for r in results if not r[4]]
    in_lex = [r for r in results if r[4]]

    print(f"--- {len(not_in_lex)} cross-klal suspect(s) NOT in lexicon "
          f"(zero independent attestation, in >= {MIN_KLALIM} klalim) ---")
    for heb, klal_count, total_count, klal_ids, _ in not_in_lex:
        klal_str = ",".join(str(k) for k in klal_ids[:10])
        if len(klal_ids) > 10:
            klal_str += f"... ({len(klal_ids)} total)"
        print(f"  {heb!r}: {klal_count} klalim, {total_count} total occurrences "
              f"(klalim: {klal_str})")

    print(f"\n--- {len(in_lex)} cross-klal form(s) IN lexicon but zero independent attestation "
          f"(likely real vocabulary the reference corpus doesn't cover, "
          f"listed for completeness) ---")
    for heb, klal_count, total_count, klal_ids, _ in in_lex[:20]:
        klal_str = ",".join(str(k) for k in klal_ids[:10])
        if len(klal_ids) > 10:
            klal_str += f"... ({len(klal_ids)} total)"
        print(f"  {heb!r}: {klal_count} klalim, {total_count} total occurrences "
              f"(klalim: {klal_str})")
    if len(in_lex) > 20:
        print(f"  ... and {len(in_lex) - 20} more")

    if not results:
        print("  None found.")


if __name__ == "__main__":
    main()
