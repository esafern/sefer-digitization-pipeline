#!/usr/bin/env python3
# [STANDALONE] Detects candidate instances of a single-letter-SUBSTITUTION OCR
# confusion class, distinct from the alef-lamed ligature bug that
# detect_ligature_corruption.py already covers. Found 2026-08-16 while
# incidentally reading context during the lexicon-gap triage
# (review_lexicon_gaps.py): 13 corruption candidates where the corrupt form is
# ITSELF a real Hebrew word already sitting in lexicon.txt, so no lexicon-
# membership check (validate_part1_corpus_integrity.py check 5,
# review_lexicon_gaps.py) can ever catch it - the same structural blind spot
# already documented for the ligature bug ("lexicon.txt cannot catch the
# ligature corruption - it contains it"), now confirmed for a second, unrelated
# corruption class. All 13 were found by accident, not by any repeatable
# method - this script is the systematic version that finding's own "NOT
# DONE: a systematic sweep... needs a different detector" note asked for.
#
# SCOPE, stated plainly, not overclaimed: this catches single-letter
# SUBSTITUTION errors only, restricted to 8 empirically-observed confusion
# PAIRS (ב/כ, ד/ר, ה/ר, ה/ד, ה/ח, ט/מ, ס/פ, ג/נ - every pair actually seen
# across today's findings, not a theoretical full letter-confusion matrix,
# which would be far noisier and slower for no evidence-backed reason). Of
# the 13 known incidental instances, ~10 are this exact shape (שמה->שמח,
# אכל->אבל, לדם->להם, שרוא->שהוא, לדו->להו, גכ->גב, דיא->היא, כין->בין,
# טרור->טהור, שכתכו->שכתבו); 3 are NOT (ישרץ->ישראל, ליבא->אליבא, ארת->את
# are insertion/deletion errors - a missing or extra letter, a DIFFERENT
# shape this script does not attempt). Matching detect_ligature_
# corruption.py's own precedent: state the scope honestly, don't claim
# completeness this method can't deliver.
#
# METHOD, the same "one clear winner" shape as detect_ligature_corruption.py
# and propose_abbreviation_expansions.resolve_truncated_word() - one
# restricted, evidence-bounded search, not a general spell-checker:
#   1. Restrict to words RARE in Part 1's own text (<= RARE_THRESHOLD
#      occurrences) - a corruption is not going to be the print's own common
#      spelling of anything.
#   2. For each confusion-pair letter the word contains, try substituting the
#      pair's other letter at that position.
#   3. A substituted candidate counts only if the ORIGINAL word has ZERO
#      independent-corpus attestation (not merely low relative to the
#      candidate - see _resolve()'s own comment for why that distinction
#      mattered in practice, measured, not assumed: requiring only a
#      DOMINANCE_RATIO-beats-original test produced 348 "high-confidence"
#      hits on first run, most of them false - ordinary rare-but-real words
#      losing a frequency contest to an extremely common neighbour, e.g.
#      אמה ("cubit"/"maidservant") -> אמר just because אמר is one of the
#      most common words in the language. Requiring zero attestation cut
#      that to 83 candidates + 1 ambiguous, of which spot-checking against
#      real klal context found no further false positive beyond one already-
#      known one (see KNOWN_FALSE_POSITIVES)) and the substituted candidate
#      itself clears MIN_INDEPENDENT_FREQUENCY.
#   4. If more than one substitution position/letter clears the bar, the word
#      is ambiguous and is reported separately, not as high-confidence -
#      mirrors detect_ligature_corruption.py's ambiguous-candidate handling.
#
# KNOWN LIMIT this method cannot solve, stated up front rather than
# discovered the hard way: a confusion pair where BOTH readings are common
# independently (context decides, not frequency) is invisible to a pure
# frequency test. klal 107's כל->בל (found 2026-08-16 by incidental context
# reading, NOT reproducible by this script) is the concrete counterexample:
# כל is far MORE common than בל, so a frequency test either never fires or
# fires in the wrong direction. Closing that gap needs contextual/semantic
# reading - the semantic-plausibility spot-check passes already do this,
# just not at 100% corpus coverage - not a sharper frequency threshold.
#
# This script only READS part*.json and the independent reference corpus
# frequency table, and REPORTS. It never edits anything and never records a
# decision itself - see review_lexicon_gaps.py for the propose -> triage ->
# flag pattern this script's output is meant to feed into as a separate,
# deliberate step, exactly like every other candidate-generation script in
# this project.
#
# Usage: python3 detect_real_word_substitution.py [part1.json]
#   Defaults to part1.json. Safe to point at part2.json/part3.json (read-
#   only) but per CLAUDE.md's standing directive, do not start or scope any
#   Parts 2-3 correction work from its output without the user's explicit
#   sign-off - Parts 2-3 remain out of scope until Part 1 is independently
#   confirmed clean.
import os
import sys
from collections import Counter

# Moved one level deeper (pipeline/ or tools/) 2026-08-16 - REPO now goes up
# two levels, not one, to keep resolving to the actual repo root where
# part1.json/docai_word_boxes/etc. live.
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pipeline"))
import corpus_io as cio  # noqa: E402

# QUOTE_CHARS, has_gershayim, and load_klal_words consolidated into corpus_io
# (2026-08-18) - was duplicated independently in four scripts.
QUOTE_CHARS = cio.QUOTE_CHARS
has_gershayim = cio.has_gershayim

# Content-word letter confusions — pairs observed across today's findings (13
# lexicon-invisible instances + catalogued letter-substitution classes from
# semantic-plausibility passes). Each pair is bidirectional. See also
# pipeline/build_gematria_trace.py's CONFUSION_PAIRS for a related but distinct
# set covering gematria-marker misreads (tuple keyed, different scope — if you
# add a new OCR confusion pattern here, check whether it belongs there too).
CONFUSION_PAIRS = [
    frozenset("בכ"), frozenset("דר"), frozenset("הר"), frozenset("הד"),
    frozenset("הח"), frozenset("טמ"), frozenset("ספ"), frozenset("גנ"),
    # Added 2026-08-18 from review_lexicon_gaps.py's empirically-observed
    # pairs (CONFUSABLE_PAIRS), which had already catalogued these from Part 1
    # spot-checking results. Each pair was found in actual Part 1 OCR errors,
    # not a theoretical similarity list. Tested against Part 1 before adding:
    # the 7 new pairs add 45 new candidates, including confirmed real errors
    # like עולס->עולם (ס/ם) and משוס->משום (ס/ם).
    frozenset("סם"), frozenset("וי"), frozenset("רת"), frozenset("הת"),
    frozenset("וז"), frozenset("כן"), frozenset("נן"),
]
# Flat letter -> {other letters this one is confusable with}, built once.
CONFUSABLE_WITH = {}
for _pair in CONFUSION_PAIRS:
    for _letter in _pair:
        CONFUSABLE_WITH.setdefault(_letter, set()).update(_pair - {_letter})

# A word must occur at most this many times in Part 1's own text to be
# considered for substitution - a corruption is not the print's common
# spelling of anything. Uncalibrated triage cut-off, same honesty as every
# other threshold in this project's detectors: chosen to be visibly strict,
# not derived from a labelled sample (there isn't one).
RARE_THRESHOLD = 3

# A substituted candidate must clear this many occurrences in the independent
# Sefaria reference corpus, and beat the ORIGINAL word's own independent-
# corpus frequency by this ratio, to count as the single clear winner.
# Mirrors propose_abbreviation_expansions.py's MIN_COMPLETION_FREQUENCY /
# DOMINANCE_RATIO exactly - same corpus, same shape of claim, same honesty
# about what the numbers bound (how OFTEN this answers, not how often it is
# right - see that script's header for the בפי'/בחי' counterexample of a
# threshold cleared comfortably by a wrong answer).
MIN_INDEPENDENT_FREQUENCY = 50
DOMINANCE_RATIO = 5


load_klal_words = cio.load_klal_words


# Known false positives: (klal_id, word_index, word) already individually
# resolved by a direct scan read, so re-flagging them on frequency alone would
# be re-litigating a settled question, not a new finding. Keyed this
# precisely (not by klal_id alone) per the PASS3_KNOWN_FALSE_POSITIVES
# precedent in check_klal_token_orphans.py - so a DIFFERENT word in the same
# klal is never silently suppressed.
KNOWN_FALSE_POSITIVES = {
    # klal 88 w423 'רתם': a 900 DPI crop unambiguously shows ר, not ה - the
    # standing proof in this project that a confusable-letter/frequency
    # signal can point at real, faithfully-printed broken/anomalous type,
    # not an OCR misread. See PROJECT-STATUS.md, "klal 88 - רתם/התם: no text
    # change... current text is faithful to the print."
    (88, 423, "רתם"),
}


def build_own_frequency_table(klal_words):
    counts = Counter()
    for words in klal_words.values():
        for w in words:
            if has_gershayim(w):
                continue
            counts[w] += 1
    return counts


def load_independent_frequency():
    """Reuses propose_abbreviation_expansions.py's own loader rather than a
    parallel copy (CLAUDE.md Lesson 13) - same provenance check, same refusal
    to score against a cache of unknown shape. Returns None (with a printed
    NOTE) if the independent corpus isn't available or is stale."""
    import propose_abbreviation_expansions as pae
    return pae.load_independent_frequency()


def find_candidates(klal_words, own_counts, indep_freq):
    """Returns (high_confidence, ambiguous):
      high_confidence: list of (klal_id, word_index, corrupt_form,
        corrected_form, corrected_indep_freq).
      ambiguous: list of (klal_id, word_index, corrupt_form, [(corrected_form,
        freq), ...]) - ALL qualifying options, not just the top-frequency one.
        FIXED during build: an earlier draft kept only the winner even here,
        which silently discarded the linguistically correct answer at least
        once in spot-checking - klal 30 word 1206 'וטכל' scored 'ומכל'
        (103x) as the top candidate, but reading the actual sentence ('דמל
        וטכל לשם עכדו') the real word is 'וטבל' ("and immersed" - standard
        conversion/circumcision terminology), a DIFFERENT substitution
        (כ->ב) that the frequency contest merely didn't rank first. A
        reviewer choosing from a truncated list would never have seen it."""
    high_confidence, ambiguous = [], []
    seen_forms = {}  # corrupt_form -> resolve() result, cached per unique form

    for klal_id, words in klal_words.items():
        for i, w in enumerate(words):
            if has_gershayim(w) or own_counts.get(w, 0) > RARE_THRESHOLD:
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
                corrected, freq = options[0]
                high_confidence.append((klal_id, i, w, corrected, freq))
    return high_confidence, ambiguous


def _resolve(w, indep_freq):
    """A word is a candidate if substituting a confusable letter at some
    position produces a real, well-attested independent-corpus word that
    dominates the original word's own independent-corpus frequency. Exactly
    one qualifying (position, letter) pair -> high-confidence; more than one
    -> ambiguous (reported, not trusted on frequency alone), mirroring
    detect_ligature_corruption.py's _resolve() - except ALL qualifying
    options are returned in the ambiguous case, not just the winner (see
    find_candidates()'s docstring for why that distinction is load-bearing,
    not cosmetic).

    Returns None, or (is_ambiguous, options) where options is every
    qualifying (corrected_form, freq) pair, sorted by frequency descending."""
    # Requiring the CANDIDATE word to be independently zero-attested, not just
    # "low relative to the correction," turned out to matter more than the
    # ratio itself - see the module docstring's own before/after numbers.
    # A word with SOME independent attestation (even a handful of hits) is
    # much more likely to be legitimate rare/period vocabulary this 2.47M-word
    # reference corpus simply doesn't happen to contain much of (the exact
    # caveat review_lexicon_gaps.py already documents for 31.8% of
    # lexicon.txt) than an OCR letter-confusion artifact - so a nonzero count,
    # however small, is treated as real attestation, not noise to threshold
    # past.
    if indep_freq.get(w, 0) != 0:
        return None
    options = []
    for i, ch in enumerate(w):
        for alt in CONFUSABLE_WITH.get(ch, ()):
            candidate = w[:i] + alt + w[i + 1:]
            freq = indep_freq.get(candidate, 0)
            if freq > MIN_INDEPENDENT_FREQUENCY:
                options.append((candidate, freq))
    if not options:
        return None
    options.sort(key=lambda x: -x[1])
    is_ambiguous = len(options) > 1 and options[0][1] <= DOMINANCE_RATIO * options[1][1]
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

    klal_words = load_klal_words(part_path)
    own_counts = build_own_frequency_table(klal_words)
    high_confidence, ambiguous = find_candidates(klal_words, own_counts, indep_freq)

    total_words = sum(len(w) for w in klal_words.values())
    print(f"Scanned {os.path.basename(part_path)}: {len(klal_words)} klalim, "
          f"{total_words} words, against {len(indep_freq)} independent-corpus forms.\n")

    print(f"--- {len(high_confidence)} high-confidence candidate(s) "
          f"(exactly one confusable substitution clears the bar) ---")
    for kid, idx, corrupt, corrected, freq in sorted(high_confidence, key=lambda e: (e[0], e[1])):
        own_n = own_counts.get(corrupt, 0)
        print(f"  klal {kid} word {idx}: {corrupt!r} -> {corrected!r} "
              f"(corrupt form {own_n}x in Part 1; correction {freq}x independently attested)")

    print(f"\n--- {len(ambiguous)} ambiguous candidate(s) "
          f"(more than one substitution clears the bar - ALL options listed, "
          f"the highest-frequency one is NOT necessarily the right one - "
          f"needs individual context review) ---")
    for kid, idx, corrupt, options in sorted(ambiguous, key=lambda e: (e[0], e[1])):
        opts_str = " | ".join(f"{c!r} ({f}x)" for c, f in options)
        print(f"  klal {kid} word {idx}: {corrupt!r} -> {opts_str}")

    if not high_confidence and not ambiguous:
        print("\nNone found.")


if __name__ == "__main__":
    main()
