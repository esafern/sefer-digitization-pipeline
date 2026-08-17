#!/usr/bin/env python3
# [STANDALONE] Cross-checks lexicon.txt against a genuinely INDEPENDENT
# Rabbinic Hebrew/Aramaic word-frequency table (Shulchan Arukh + Talmud
# Bavli, ~2.6M words, via fetch_sefaria_reference_corpus.py) - not a fix,
# a read-only cross-check. The exact word/book totals are printed at
# runtime and recorded in sefaria_reference_corpus/word_freq.meta.json;
# don't take the round number here as the checked figure (it was "~2.47M"
# until 2026-08-16, when an extraction bug hiding 106,474 words was found).
#
# WHY THIS EXISTS: lexicon.txt was built from THIS corpus's own OCR output
# (archive/scripts/build_lexicon.py), so it absorbed and then "validated"
# the alef-lamed ligature corruption - see PROJECT-STATUS.md
# "`lexicon.txt` cannot catch the ligature corruption - it contains it".
# Every check this project runs against lexicon.txt is therefore only as
# independent as lexicon.txt itself, which is not independent at all. This
# script is the first check in the pipeline that compares against a source
# with NO editorial/data lineage connection to this project.
#
# TWO REPORTS, both informational - neither writes anything:
#
# 1. Sanity-check the 2026-08-15 lexicon.txt purge: for each of the 24
#    confirmed dropped-lamed corrupt forms (DROPPED_LAMED_CORRUPT_FORMS,
#    tests/test_corpus_invariants.py), how often does it appear in the
#    independent corpus, versus its corrected form? A large skew toward
#    the corrected form supports the purge; a corrupt form with real
#    independent attestation doesn't overturn the purge (Part 1's specific
#    instances were separately scan/context-verified) but IS new evidence
#    worth recording - CLAUDE.md Lesson 2, a "0 ambiguous" claim deserves
#    re-examination against a signal that wasn't available when it was made.
#
# 2. lexicon.txt words with ZERO occurrences anywhere in the independent
#    corpus: NOT a purge list. lexicon.txt legitimately contains Yad-
#    Malachi-specific proper nouns, unique word-forms, and words this
#    2.47M-word sample simply didn't happen to use - a random sample this
#    doesn't fully cover is normal for the long tail of any lexicon
#    (Lesson 1: coverage of a check is not the same as its absence of
#    output). This report exists to be READ, one candidate at a time,
#    the same way the 24 forms above were - not auto-applied.
#
# Usage: python3 fetch_sefaria_reference_corpus.py   (once, ~45MB download)
#        python3 validate_lexicon_independent.py
import glob
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

RAW_DIR = os.path.join(REPO, "sefaria_reference_corpus", "raw")
FREQ_CACHE = os.path.join(REPO, "sefaria_reference_corpus", "word_freq.json")
# Provenance for FREQ_CACHE - see cache_is_current(). Bump EXTRACTOR_VERSION
# whenever flatten_strings/clean_words changes what a book contributes, so
# every consumer of the cache rebuilds instead of silently reusing a table
# built by the older rule.
FREQ_META = os.path.join(REPO, "sefaria_reference_corpus", "word_freq.meta.json")
EXTRACTOR_VERSION = 2  # 2 = 2026-08-16, flatten_strings() handles dict-shaped `text`
LEXICON_PATH = cio.LEXICON_PATH

# Shared 2026-08-17. This one matters more than the other merged copies:
# this script's whole purpose is comparing lexicon.txt (derived from THIS
# project's OCR) against an independent reference corpus, and the comparison
# is only valid if both sides are normalized identically. A private copy of
# the letter set here could have drifted from the corpus side and turned a
# normalization mismatch into what looked like a vocabulary finding.
HEB = cio.HEBREW_LETTERS
HEB_SET = set(HEB)
NIQQUD_RE = re.compile(r"[֑-ׇ]")  # cantillation + vowel points
TAG_RE = re.compile(r"<[^>]+>")

# Same 24 forms as tests/test_corpus_invariants.py::DROPPED_LAMED_CORRUPT_FORMS
# (kept as an independent literal, not imported, so this script has no
# dependency on the test file and still runs standalone).
CORRUPT_TO_CORRECT = {
    "אא": "אלא", "אגאזי": "אלגאזי", "אה": "אלה", "אהים": "אלהים",
    "איבא": "אליבא", "איביה": "אליביה", "איבייהו": "אליבייהו", "איה": "אליה",
    "איעזר": "אליעזר", "אמא": "אלמא", "אעאי": "אלעאי", "אעזר": "אלעזר",
    "אפא": "אלפא", "בצלא": "בצלאל", "דשמוא": "דשמואל", "האה": "האלה",
    "האף": "האלף", "ואהים": "ואלהים", "והאף": "והאלף", "וכאה": "וכאלה",
    "ושמוא": "ושמואל", "ישמעא": "ישמעאל", "ישרא": "ישראל", "שמוא": "שמואל",
}


def flatten_strings(node, out):
    """Collect every string in a Sefaria merged-text tree.

    FIXED 2026-08-16 (code audit): dicts used to fall through to a silent
    no-op. Most books' `text` is a nested list, but a book with named
    sub-sections is a dict keyed by section title - and Shulchan Arukh, Even
    HaEzer is one ("", "Seder HaGet", "Seder Halitzah"). It therefore
    contributed EXACTLY ZERO words to the "independent reference corpus"
    while being downloaded, counted as present by
    fetch_sefaria_reference_corpus.py, and named in this file's own
    docstring: 106,474 words, 4.3% of the total, and one of the four
    Shulchan Arukh chelekim - precisely the marriage/divorce vocabulary
    (גט, קידושין, יבום, חליצה) Yad Malachi cites constantly.

    Both reports here read as MORE confident than they were: a lexicon.txt
    word attested only in Even HaEzer was reported as having "zero
    independent attestation", and propose_abbreviation_expansions.py's
    truncated-word completion scores candidates against this same table.
    CLAUDE.md Lesson 1 in its purest form - the check ran on all 41 books and
    was structurally incapable of producing output for one of them.
    """
    if isinstance(node, str):
        out.append(node)
    elif isinstance(node, list):
        for x in node:
            flatten_strings(x, out)
    elif isinstance(node, dict):
        for x in node.values():
            flatten_strings(x, out)


def clean_words(raw_html_string):
    no_tags = TAG_RE.sub(" ", raw_html_string)
    no_niqqud = NIQQUD_RE.sub("", no_tags)
    words = []
    for tok in no_niqqud.split():
        w = "".join(c for c in tok if c in HEB_SET)
        if w:
            words.append(w)
    return words


def cache_is_current(meta_path=None):
    """Is the frequency cache on disk one THIS version of the extractor built,
    from the books currently in RAW_DIR?

    Added 2026-08-16 with the dict fix above, and the reason is that fix: the
    cache is a plain {word: count} file with no record of how it was made, so
    the version missing 106,474 words looks byte-for-byte like a correct one
    and would have been reused forever - by this script AND by
    propose_abbreviation_expansions.py, which reads the same file. A cache
    key has to cover everything that changes the right answer (Lesson 12);
    for a derived table that means the extractor version and the inputs, not
    just "a file exists".
    """
    meta_path = meta_path or FREQ_META
    if not (os.path.exists(FREQ_CACHE) and os.path.exists(meta_path)):
        return False
    try:
        meta = json.load(open(meta_path, encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    return (meta.get("extractor_version") == EXTRACTOR_VERSION
            and meta.get("source_files") == sorted(
                os.path.basename(p) for p in glob.glob(os.path.join(RAW_DIR, "*.json"))))


def build_or_load_frequency_table():
    if cache_is_current():
        return Counter(json.load(open(FREQ_CACHE, encoding="utf-8")))
    paths = sorted(glob.glob(os.path.join(RAW_DIR, "*.json")))
    if not paths:
        raise SystemExit(
            f"No files in {RAW_DIR} - run fetch_sefaria_reference_corpus.py first."
        )
    if os.path.exists(FREQ_CACHE):
        print(f"Rebuilding {os.path.basename(FREQ_CACHE)}: it was built by a different "
              f"extractor version or from a different set of books.")
    counts = Counter()
    per_book = {}
    for path in paths:
        d = json.load(open(path, encoding="utf-8"))
        strings = []
        flatten_strings(d.get("text", []), strings)
        book = Counter()
        for s in strings:
            book.update(clean_words(s))
        per_book[os.path.basename(path)] = sum(book.values())
        counts.update(book)
    empty = sorted(name for name, n in per_book.items() if not n)
    if empty:
        # Never again silently. A downloaded book that yields no words is
        # either an unhandled `text` shape or a bad download, and both look
        # identical from the totals line.
        print(f"WARNING: {len(empty)} downloaded book(s) contributed ZERO words - "
              f"the reference corpus is not what it claims to be: {', '.join(empty)}")
    json.dump(counts, open(FREQ_CACHE, "w", encoding="utf-8"), ensure_ascii=False)
    json.dump({"extractor_version": EXTRACTOR_VERSION,
               "source_files": sorted(per_book),
               "words_per_book": per_book,
               "total_words": sum(counts.values())},
              open(FREQ_META, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return counts


def load_lexicon():
    return sorted(set(w.strip() for w in open(LEXICON_PATH, encoding="utf-8") if w.strip()))


def main():
    freq = build_or_load_frequency_table()
    print(f"Independent corpus: {sum(freq.values())} words, {len(freq)} unique forms "
          f"(Shulchan Arukh + Talmud Bavli, via Sefaria's public export).\n")

    print("--- Report 1: the 24 dropped-lamed corrupt forms vs. their corrected reading ---")
    attested = []
    for corrupt, correct in CORRUPT_TO_CORRECT.items():
        fc, fr = freq.get(corrupt, 0), freq.get(correct, 0)
        if fc > 0:
            attested.append((corrupt, fc, correct, fr))
    print(f"{len(attested)}/{len(CORRUPT_TO_CORRECT)} corrupt forms have nonzero independent "
          f"attestation (i.e. are real words somewhere in this corpus, not purely artifacts):")
    for corrupt, fc, correct, fr in sorted(attested, key=lambda x: -x[1]):
        ratio = f"{fr / fc:.0f}x" if fc else "inf"
        print(f"  {corrupt!r}: {fc} occurrence(s) vs {correct!r}: {fr} ({ratio} more common) "
              f"- does NOT overturn the purge (Part 1's specific instances were individually "
              f"scan/context-verified), but was not known when the purge was made")
    zero = [c for c in CORRUPT_TO_CORRECT if freq.get(c, 0) == 0]
    print(f"{len(zero)}/{len(CORRUPT_TO_CORRECT)} corrupt forms have ZERO independent "
          f"attestation (supports the purge): {', '.join(sorted(zero))}\n")

    print("--- Report 2: lexicon.txt words with zero independent attestation ---")
    lexicon = load_lexicon()
    if not lexicon:
        raise SystemExit(f"{LEXICON_PATH} is empty - nothing to cross-check.")
    unattested = [w for w in lexicon if freq.get(w, 0) == 0]
    print(f"{len(unattested)}/{len(lexicon)} lexicon.txt words ({len(unattested)/len(lexicon):.1%}) "
          f"do not appear anywhere in the independent corpus.")
    print("NOT a purge list - read individually before acting on any entry (see module "
          "docstring). First 40 shown for a quick look:")
    for w in unattested[:40]:
        print(f"  {w}")


if __name__ == "__main__":
    main()
