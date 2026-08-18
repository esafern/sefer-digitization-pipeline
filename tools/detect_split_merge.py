#!/usr/bin/env python3
# [STANDALONE] Detects candidate word-split and word-merge OCR errors.
#
# ERROR CLASS: OCR sometimes reads one word as two (e.g. "ב ית" for "בית"),
# or two words as one (e.g. "כלומר" for "כל" + "ומר"). These are invisible
# to single-word substitution/insertion/deletion detectors because each
# fragment may be a real word on its own.
#
# METHOD:
#   1. MERGE candidates (two words read as one): for each word in the corpus
#      that has zero independent attestation and is at least MIN_MERGE_LENGTH
#      letters, try splitting it at every position into two halves. If both
#      halves are independently attested (each >= MIN_HALF_FREQUENCY), flag it.
#   2. SPLIT candidates (one word read as two): for each adjacent pair of
#      short tokens (each < MAX_SHORT_TOKEN letters, at least one rare in
#      Part 1), does their concatenation (Hebrew letters only) appear in the
#      independent reference corpus at >= MIN_CONCAT_FREQUENCY?
#
# SCOPE: catches single-boundary splits/merges only. Does NOT catch:
#   - Multi-word merges (three words fused into one)
#   - Splits where one fragment is empty (that's a space insertion, not a split)
#   - Cases where both the split and merged forms are common words
#
# FALSE-POSITIVE RATE (estimated from Part 1):
#   - Merge candidates: ~30-40%. Hebrew's agglutinative morphology means many
#     legitimate words split into two attested halves by coincidence.
#   - Split candidates: ~40-50%. Adjacent short words whose concatenation is
#     common are often legitimate (e.g. "של" + "הם" looks like "שלהם" but
#     both forms are independently correct in context).
#
# Read-only: never edits any corpus file. Safe to run on part2.json/part3.json
# but per CLAUDE.md scope rules, do not start Parts 2-3 correction work from
# its output without the user's explicit sign-off.
#
# Usage: python3 detect_split_merge.py [part1.json|part2.json|part3.json]
import os
import sys
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pipeline"))
sys.path.insert(0, os.path.join(REPO, "tools"))
import corpus_io as cio  # noqa: E402

# Merge detection thresholds
MIN_MERGE_LENGTH = 7       # minimum Hebrew-letter length to try splitting
MIN_HALF_FREQUENCY = 300   # each half must be this common independently
RARE_IN_CORPUS = 2         # the merged form must be this rare in Part 1

# Split detection thresholds
MAX_SHORT_TOKEN = 3        # both tokens must be this short (Hebrew letters)
MIN_CONCAT_FREQUENCY = 500 # the concatenation must be this common independently
RARE_FOR_SPLIT = 3         # at least one token must be this rare in Part 1

KNOWN_FALSE_POSITIVES = {
}


def load_independent_frequency():
    import propose_abbreviation_expansions as pae
    return pae.load_independent_frequency()


def find_merge_candidates(klal_words, own_counts, indep_freq):
    """Detect words that might be two words fused together."""
    results = []
    seen_forms = {}

    for klal_id, words in klal_words.items():
        for i, w in enumerate(words):
            if cio.has_gershayim(w):
                continue
            heb = cio.hebrew_letters_only(w)
            if len(heb) < MIN_MERGE_LENGTH:
                continue
            if own_counts.get(w, 0) > RARE_IN_CORPUS:
                continue
            if indep_freq.get(heb, 0) > 0:
                continue  # word is independently attested

            if heb not in seen_forms:
                seen_forms[heb] = _resolve_merge(heb, indep_freq)
            best = seen_forms[heb]
            if best is not None:
                left, right, left_freq, right_freq = best
                results.append((klal_id, i, w, left, right, left_freq, right_freq))
    return results


def _resolve_merge(heb, indep_freq):
    """Try splitting heb at every position. Return the best split or None.
    Each half must be >= 3 letters to avoid prefix-noise (2-letter prefixes
    like של, וה, כש etc. match nearly everything)."""
    best = None
    for j in range(3, len(heb) - 2):  # each half must be >= 3 letters
        left, right = heb[:j], heb[j:]
        lf = indep_freq.get(left, 0)
        rf = indep_freq.get(right, 0)
        if lf >= MIN_HALF_FREQUENCY and rf >= MIN_HALF_FREQUENCY:
            score = min(lf, rf)
            if best is None or score > best[4]:
                best = (left, right, lf, rf, score)
    if best is None:
        return None
    return best[:4]


def find_split_candidates(klal_words, own_counts, indep_freq):
    """Detect adjacent token pairs that might be one word split in two."""
    results = []
    seen_pairs = {}

    for klal_id, words in klal_words.items():
        for i in range(len(words) - 1):
            w1, w2 = words[i], words[i + 1]
            if cio.has_gershayim(w1) or cio.has_gershayim(w2):
                continue
            h1, h2 = cio.hebrew_letters_only(w1), cio.hebrew_letters_only(w2)
            if not h1 or not h2:
                continue
            if len(h1) > MAX_SHORT_TOKEN or len(h2) > MAX_SHORT_TOKEN:
                continue
            # At least one must be rare
            if own_counts.get(w1, 0) > RARE_FOR_SPLIT and own_counts.get(w2, 0) > RARE_FOR_SPLIT:
                continue

            pair_key = (h1, h2)
            if pair_key not in seen_pairs:
                concat = h1 + h2
                freq = indep_freq.get(concat, 0)
                seen_pairs[pair_key] = freq if freq >= MIN_CONCAT_FREQUENCY else 0
            freq = seen_pairs[pair_key]
            if freq > 0:
                results.append((klal_id, i, w1, w2, h1 + h2, freq))
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

    klal_words = cio.load_klal_words(part_path)
    own_counts = Counter()
    for words in klal_words.values():
        for w in words:
            if not cio.has_gershayim(w):
                own_counts[w] += 1

    merge_results = find_merge_candidates(klal_words, own_counts, indep_freq)
    split_results = find_split_candidates(klal_words, own_counts, indep_freq)

    total_words = sum(len(w) for w in klal_words.values())
    print(f"Scanned {os.path.basename(part_path)}: {len(klal_words)} klalim, "
          f"{total_words} words.\n")

    print(f"--- {len(merge_results)} merge candidate(s) "
          f"(one rare word that splits into two common halves) ---")
    for kid, idx, w, left, right, lf, rf in sorted(merge_results, key=lambda e: (e[0], e[1])):
        words = klal_words[kid]
        lo, hi = max(0, idx - 3), min(len(words), idx + 4)
        context = " ".join(words[lo:hi])
        print(f"  klal {kid} word {idx}: {w!r} -> {left!r} + {right!r} "
              f"(left {lf}x, right {rf}x independently)  context: {context}")

    print(f"\n--- {len(split_results)} split candidate(s) "
          f"(two short adjacent tokens whose concatenation is common) ---")
    for kid, idx, w1, w2, concat, freq in sorted(split_results, key=lambda e: (e[0], e[1])):
        words = klal_words[kid]
        lo, hi = max(0, idx - 2), min(len(words), idx + 5)
        context = " ".join(words[lo:hi])
        print(f"  klal {kid} words {idx}-{idx+1}: {w1!r} + {w2!r} -> {concat!r} "
              f"({freq}x independently)  context: {context}")

    if not merge_results and not split_results:
        print("\nNone found.")


if __name__ == "__main__":
    main()
