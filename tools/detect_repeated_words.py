#!/usr/bin/env python3
# [STANDALONE] Detects consecutive repeated words (dittography) in corpus text.
#
# ERROR CLASS: OCR or transcription sometimes duplicates a word, producing
# "word word" where only one "word" was intended. This is a purely structural
# check requiring no corpus frequency data or reference corpus.
#
# METHOD: For each klal, walk adjacent word pairs. Flag any case where the
# same word appears twice consecutively (after stripping quote chars). Some
# repeated words are legitimate in Hebrew (e.g. "איש איש" = "each person",
# "מה מה" in certain constructions, "דין דין" = "this law, this law"). These
# are listed in LEGITIMATE_REPEATS and excluded.
#
# SCOPE: Catches exact consecutive duplicates only. Does NOT catch:
#   - Near-duplicates (one letter different)
#   - Non-adjacent duplicates (same phrase repeated with gap)
#   - Repeated phrases longer than one word (covered by
#     validate_part1_corpus_integrity.py check 3/3b)
#
# FALSE-POSITIVE RATE (estimated from Part 1): after building the
# LEGITIMATE_REPEATS set from Part 1's own output, approximately 50-60% of
# remaining hits are legitimate (citation references like "ע"ב ע"ב" or
# "ע"ד ע"ד", deliberate repetitions, quoted material). The remaining hits
# include genuine candidates worth scan-checking (e.g. "פסקא פסקא",
# "הניזקין הניזקין", "המלך המלך").
#
# Read-only: never edits any corpus file. Safe to run on part2.json/part3.json
# but per CLAUDE.md scope rules, do not start Parts 2-3 correction work from
# its output without the user's explicit sign-off.
#
# Usage: python3 detect_repeated_words.py [part1.json|part2.json|part3.json]
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pipeline"))
import corpus_io as cio  # noqa: E402

# Words that legitimately appear consecutively in Hebrew/Rabbinic text.
# Each entry is the hebrew_letters_only form. Built empirically from Part 1
# spot-checking, not from a theoretical list - every entry was read in
# context and confirmed as a real construction, not a corpus error.
LEGITIMATE_REPEATS = {
    # Distributive construction: "איש איש" = "each person"
    "איש",
    # "דין דין" = repeated reference, common in halachic indexing style
    "דין",
    # "תניא תניא" = "if it was taught, it was taught" - standard Talmudic phrase
    "תניא",
    # "לה לה" = standard gezerah shavah derivation phrase ("from her, from her")
    "לה",
    # "שור שור" = Torah repetition cited explicitly as deliberate
    "שור",
    # "צדק צדק" = "justice, justice" (Deut. 16:20, commonly quoted)
    "צדק",
    # "הן הן" = "they are they" = "these are the same" - standard Talmudic idiom
    "הן",
    # "לא לא" = emphasis/repetition in halachic discourse
    "לא",
    # "עשה עשה" = "a positive commandment is a positive commandment" - halachic usage
    "עשה",
    # "דאיידי דאיידי" = "because of the incidental" - repeated in Talmudic dialectic
    "דאיידי",
    # "ואם ואם" = "and if... and if..." - quoting consecutive Torah clauses
    "ואם",
    # "ואידך ואידך" = "and the other, and the other" - standard Talmudic exchange
    "ואידך",
    # "ולית ולית" = "and there is no... and there is no..." - doubled negation
    "ולית",
    # "על על" = artifact of citation reference ("על על" in context of Talmudic page ref)
    "על",
    # "בר בר" = patronymic chain "son of son of" (e.g. "רבה בר בר חנה")
    "בר",
}

# (klal_id, word_index, word) for confirmed non-errors discovered during testing.
KNOWN_FALSE_POSITIVES = {
}


def find_repeated_words(klal_words):
    """Returns list of (klal_id, word_index, word) for consecutive duplicates."""
    results = []
    for klal_id, words in klal_words.items():
        for i in range(len(words) - 1):
            w = cio.hebrew_letters_only(words[i])
            w_next = cio.hebrew_letters_only(words[i + 1])
            if not w or not w_next:
                continue
            if w == w_next:
                if w in LEGITIMATE_REPEATS:
                    continue
                if (klal_id, i, words[i]) in KNOWN_FALSE_POSITIVES:
                    continue
                results.append((klal_id, i, words[i], words[i + 1]))
    return results


def main():
    part_path = sys.argv[1] if len(sys.argv) > 1 else cio.PART1_PATH
    if not os.path.isabs(part_path):
        part_path = os.path.join(REPO, part_path)

    klal_words = cio.load_klal_words(part_path)
    results = find_repeated_words(klal_words)

    total_words = sum(len(w) for w in klal_words.values())
    print(f"Scanned {os.path.basename(part_path)}: {len(klal_words)} klalim, "
          f"{total_words} words.\n")

    print(f"--- {len(results)} consecutive repeated word(s) ---")
    for klal_id, idx, w1, w2 in sorted(results):
        # Show context
        words = klal_words[klal_id]
        lo = max(0, idx - 3)
        hi = min(len(words), idx + 5)
        context = " ".join(words[lo:hi])
        print(f"  klal {klal_id} word {idx}: {w1!r} {w2!r}  context: {context}")

    if not results:
        print("  None found.")


if __name__ == "__main__":
    main()
