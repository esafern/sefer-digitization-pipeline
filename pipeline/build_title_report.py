#!/usr/bin/env python3
# [PRODUCTION] Regenerate the TITLE defect report: everything this pipeline can
# say, mechanically, about the `title` field of every klal in Part 1.
#
# WHY THIS EXISTS. Until 2026-09-03 the `title` field had never been read by any
# detector, witness, validator or invariant in this repo - all of them read
# `clean_text`. Item 39 found the consequence by accident, because a reviewer
# happened to read one heading: six OCR errors sat in titles whose BODIES were
# already correct, one of them the same alef-lamed ligature sort as items 26 and
# 32. Lesson 1, in a place nobody had looked - a check never run over a field has
# verified nothing about it.
#
# WHAT IT REPORTS, in two independent classes:
#
#   1. PREFIX DIVERGENCE. The body reprints the heading verbatim before
#      continuing, so a title must be a prefix of its own body. Where it is not,
#      exactly one of the two carries an error the other does not - which is a
#      much sharper signal than any frequency test, because it needs no corpus
#      statistics at all. This is the class that found all six of item 39's.
#
#   2. DETECTOR CANDIDATES over the title field, from the same substitution and
#      insertion/deletion detectors stage 4b runs over bodies, via
#      `--field title`.
#
# WHAT IT DELIBERATELY DOES NOT DO, same as stage 4b: it writes no `klal_flag`
# rows. These are candidates with real false positives - two of the three found
# on the first run are words the body spells identically and spells correctly -
# and the ledger is append-only and permanent. Promoting one to a flag stays a
# separate, deliberate act.
#
# THE EXTENT CLASS IS NOT IN HERE AND CANNOT BE. A title that has swallowed body
# text still agrees with its body over its own length, so no textual check can
# see it; only the printed type size says where a heading stops (item 39 (iv)).
# The report says so in its own header rather than letting a clean run read as
# "titles are fine".
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pipeline"))
sys.path.insert(0, os.path.join(REPO, "tools"))

import corpus_io as cio  # noqa: E402
import detect_real_word_substitution as sub  # noqa: E402
import detect_insertion_deletion as ins  # noqa: E402

OUT_PATH = cio.repo_path("title_defect_report.json")

# The pipeline inserts these into a body and never into a title, so they are
# skipped on both sides of the prefix comparison - it is about WORDS.
COMPARISON_MARKS = {"•", "[.]", "[,]", ".", ":", ",", ";"}


def prefix_divergences(klalim):
    """[(klal_id, index, title_word, body_word)] - the FIRST divergence per klal.

    The rest of a title usually diverges as a consequence of the first, so
    listing them all buries the finding. Same rule as the gated invariant
    `test_every_title_is_a_prefix_of_its_own_body`, which is the enforcement
    half of this report.
    """
    out = []
    for k in klalim:
        title = cio.strip_title_terminal_period(
            [w for w in cio.title_words_of(k) if w not in COMPARISON_MARKS])
        # body[0] is the klal's gematria marker, which no title repeats.
        body = [w for w in cio.words_of(k)[1:] if w not in COMPARISON_MARKS]
        if not title:
            continue
        for i in range(min(len(title), len(body))):
            if title[i] != body[i]:
                out.append({"klal_id": k["klal_id"], "word_index": i,
                            "title_word": title[i], "body_word": body[i],
                            "klass": "prefix_divergence"})
                break
    return out


def detector_candidates(part_path):
    """The 4b detectors, pointed at `title` instead of `clean_text`.

    The frequency table stays the BODY's (load_klal_words with no field): the
    title field is 1,287 words, so counting rare-ness inside it would make every
    title word a hapax and the gate would stop gating - see
    corpus_io.load_klal_words.
    """
    indep = sub.load_independent_frequency()
    if not indep:
        return None
    title_words = cio.load_klal_words(part_path, field=cio.TITLE_FIELD)
    own = sub.build_own_frequency_table(cio.load_klal_words(part_path))
    rows = []
    for detector, name in ((sub, "substitution"), (ins, "insertion_deletion")):
        hi, amb = detector.find_candidates(title_words, own, indep)
        for it in hi:
            rows.append({"klal_id": it[0], "word_index": it[1], "title_word": it[2],
                         "proposal": it[3], "ref_count": next(
                             (x for x in it[4:] if isinstance(x, int)), None),
                         "detector": name, "ambiguous": False,
                         "klass": "detector_candidate"})
        for it in amb:
            rows.append({"klal_id": it[0], "word_index": it[1], "title_word": it[2],
                         "proposal": [c[0] for c in it[3]], "ref_count": None,
                         "detector": name, "ambiguous": True,
                         "klass": "detector_candidate"})
    rows.sort(key=lambda r: (r["klal_id"], r["word_index"]))
    return rows


def build(part_path=None):
    part_path = part_path or cio.PART1_PATH
    klalim = cio.load_klalim(part_path)
    candidates = detector_candidates(part_path)
    return {
        "field": cio.TITLE_FIELD,
        "klalim_scanned": len(klalim),
        "title_words": sum(len(cio.title_words_of(k)) for k in klalim),
        "prefix_divergences": prefix_divergences(klalim),
        # None (not []) when the gitignored reference cache is absent, so an
        # unrunnable detector never reads as "no defects found" (Lesson 26).
        "detector_candidates": candidates,
        "not_checked": (
            "EXTENT: whether a title has swallowed body text. A title that has "
            "still agrees with its body over its own length, so nothing here can "
            "see it - only the printed type size can. Item 39 (iv), unmeasured."
        ),
    }


def main():
    report = build()
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
        f.flush()
    n_div = len(report["prefix_divergences"])
    cands = report["detector_candidates"]
    print(f"Wrote {OUT_PATH}: {report['klalim_scanned']} titles, "
          f"{report['title_words']} words")
    print(f"  {n_div} title(s) not a prefix of their own body"
          + (": " + ", ".join(f"klal {d['klal_id']} w{d['word_index']} "
                              f"{d['title_word']}/{d['body_word']}"
                              for d in report["prefix_divergences"]) if n_div else ""))
    if cands is None:
        print("  WARNING: sefaria_reference_corpus/word_freq.json is absent - the lexical "
              "detectors CANNOT RUN over titles. This is not 'zero defects'; see SETUP.md.")
    else:
        print(f"  {len(cands)} detector candidate(s) in titles - NOT flags and NOT fixes, "
              f"a triage queue; the body often spells the same word the same way.")
    print("  NOT CHECKED: title EXTENT (item 39 (iv)) - needs the printed page.")


if __name__ == "__main__":
    main()
