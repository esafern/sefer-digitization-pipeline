#!/usr/bin/env python3
# [PRODUCTION] Regenerate the lexical-defect report: every single-letter
# SUBSTITUTION and every INSERTION/DELETION candidate the two detectors find,
# in one JSON artifact, refreshed on every rebuild.
#
# WHY THIS IS A PIPELINE STAGE AND NOT A SCRIPT SOMEONE REMEMBERS TO RUN.
# tools/detect_real_word_substitution.py and tools/detect_insertion_deletion.py
# were [STANDALONE]: they printed to stdout, were in no chain, and wrote nothing.
# On 2026-08-26 the reviewer hand-repaired `בחרא`->`בחדא` in klal 84 that nothing
# had flagged - and the substitution detector had been finding that exact
# candidate all along. Correct output, shown to nobody: Lesson 29 at the level of
# a whole tool. Both run in about a tenth of a second on the full corpus, so
# there is no cost argument for leaving them out - the same argument that put
# synthesize_multi_witness.py into the chain on 2026-08-23.
#
# ============================================================================
# READ THIS BEFORE PUTTING ANY OF THIS IN FRONT OF A HUMAN.
#
# **THESE DETECTORS ARE NEARLY USELESS ON THEIR OWN, AND THAT IS MEASURED, NOT
# AN OPINION. A CANDIDATE MUST BE VISION-ADJUDICATED AGAINST THE INK BEFORE IT
# IS SURFACED TO A REVIEWER.** Reviewer directive, 2026-09-09.
#
# Both detectors argue from FREQUENCY: a word that is rare here and one edit
# away from a word that is common in an independent corpus. That is evidence
# about THE LANGUAGE. It is not evidence about THIS PAGE, and the two come apart
# constantly, because a 19th-century Livorno/Berlin printing of a halachic
# reference is full of forms that are rare in Sefaria's corpus and perfectly
# correct on the sheet.
#
# THE NUMBERS, both measured on this corpus:
#   * 2026-08-26 - of 262 merged positions the independent witnesses CONTRADICT
#     149, and detect_insertion_deletion proposes `בחרא`->`ברא` for the very word
#     whose correct reading is `בחדא`.
#   * 2026-09-09 (item 0DU) - every candidate BELOW the review tier was cropped
#     and put to the vision adjudicator: **166 of 166 hypotheses across 126
#     positions came back as the STORED text**, confidence median 0.98. Including
#     all 28 whose proposal is attested >=1,000x in the reference corpus. The
#     top-ranked finding in the entire report, `דהלא`->`דלא` at 12,899x, is a
#     false positive the reviewer spotted by eye before the pass confirmed it.
#     The adjudicator was checked for its ability to disagree first (Lesson 25):
#     on a control where the ink is known to differ, it chose the other reading.
#
# So the report is a place to LOOK, and the tier in
# assemble_corrections_dataset.merge_lexical_defects() is what decides what a
# human sees. **Do not widen that tier to surface more of this.** If more of it
# should reach a reviewer, the way is to adjudicate it by vision first and
# surface only what the ink supports - tools/verify_flagged_candidates_vision.py
# --source lexical does exactly that, and its verdicts can be recorded here with
# --acknowledge-from-vision.
# ============================================================================
#
# WHAT THIS DELIBERATELY DOES NOT DO: it does not write klal_flag rows. The
# ledger is append-only and permanent, and these detectors carry real false
# positives - measured 2026-08-26, of 262 merged positions the independent
# witnesses CONTRADICT 149, and `detect_insertion_deletion` proposes
# `בחרא`->`ברא` for the very word whose correct reading is `בחדא`. This is a
# triage queue for a human, not a fix list. Promoting an entry to a flag stays a
# deliberate, separate act, exactly like every other decision in this pipeline.
import argparse
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pipeline"))
sys.path.insert(0, os.path.join(REPO, "tools"))

import corpus_io as cio  # noqa: E402
import triage_ack as ack  # noqa: E402
import detect_real_word_substitution as sub  # noqa: E402
import detect_insertion_deletion as ins  # noqa: E402

OUT_PATH = cio.repo_path("lexical_defect_report.json")
# Its own store, same mechanism as the structural, title and ligature reports -
# see pipeline/triage_ack.py (items 0DN, 0DV).
ACK_PATH = cio.repo_path("lexical_defect_acknowledged.json")


def build(part_path=None):
    part_path = part_path or cio.PART1_PATH
    klal_words = sub.load_klal_words(part_path)
    own = sub.build_own_frequency_table(klal_words)
    indep = sub.load_independent_frequency()
    if not indep:
        # The reference cache is gitignored. Say so loudly rather than emitting
        # an empty report that reads like "no defects found" (Lesson 26).
        return None

    sub_hi, sub_amb = sub.find_candidates(klal_words, own, indep)
    ins_own = ins.build_own_frequency_table(klal_words) if hasattr(ins, "build_own_frequency_table") else own
    ins_hi, ins_amb = ins.find_candidates(klal_words, ins_own, indep)

    def rows(items, kind, ambiguous, own=own):
        """The two detectors return different tuple shapes - the
        insertion/deletion one carries an extra edit-kind field that the
        substitution one has no equivalent for - so unpack positionally and
        keep whatever is there rather than assuming a common arity."""
        out = []
        for it in items:
            kid, wi, corrupt = it[0], it[1], it[2]
            props = []
            if ambiguous:
                for cand in it[3]:
                    form, rest = cand[0], cand[1:]
                    ref = next((x for x in rest if isinstance(x, int)), None)
                    edit = next((x for x in rest if isinstance(x, str)), None)
                    props.append({"form": form, "ref_count": ref, "edit": edit})
            else:
                rest = it[3:]
                form = rest[0]
                ref = next((x for x in rest[1:] if isinstance(x, int)), None)
                edit = next((x for x in rest[1:] if isinstance(x, str)), None)
                props.append({"form": form, "ref_count": ref, "edit": edit})
            best = props[0] if props else {}
            out.append({"klal_id": kid, "word_index": wi, "stored": corrupt,
                        "proposals": props, "detector": kind,
                        "ambiguous": bool(ambiguous),
                        # `rank` is what decides whether an entry is REVIEWABLE
                        # (merged into the dashboard queue) or merely reported.
                        # It is the reference-corpus count of the best proposal:
                        # a high number means the reading being proposed is a
                        # common, well-attested word, which is the sharpest
                        # cheap signal available. See REVIEW_MIN_REF below.
                        "rank": best.get("ref_count") or 0,
                        "corpus_count": own.get(cio.hebrew_letters_only(corrupt), 0)})
        return out

    report = (rows(sub_hi, "substitution", False) + rows(sub_amb, "substitution", True)
              + rows(ins_hi, "insertion_deletion", False) + rows(ins_amb, "insertion_deletion", True))
    report.sort(key=lambda r: (r["klal_id"], r["word_index"]))
    return ack.annotate(report, ACK_PATH)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--acknowledge", metavar="KLAL:WORD", action="append", default=[],
                    help="record one candidate as checked-and-correct so it stops being "
                         "reported, e.g. --acknowledge 92:346. Repeatable.")
    ap.add_argument("--acknowledge-from-vision", metavar="REPORT",
                    help="bulk-acknowledge every position a vision pass read as the STORED "
                         "text (selected_option A) in the given lexical_vision_report.json. "
                         "This is the intended route: the ink decides, not the frequency.")
    ap.add_argument("--note", default="checked against the ink and correct as printed",
                    help="why these are being dismissed - stored with each acknowledgement")
    args = ap.parse_args()

    report = build()
    if report is None:
        print("  WARNING: sefaria_reference_corpus/word_freq.json is absent - the lexical "
              "detectors CANNOT RUN and no report was written.")
        print("           This is not 'zero defects'. See SETUP.md; the cache is gitignored.")
        return
    if args.acknowledge or args.acknowledge_from_vision:
        specs = list(args.acknowledge)
        if args.acknowledge_from_vision:
            rows = cio.load_json(args.acknowledge_from_vision, default=[]) or []
            # ONLY where the ink chose the stored text, and only where the pass
            # actually returned a verdict: a row with an `error` was never
            # adjudicated, and acknowledging it would record a check nobody made.
            agreed = {(r["klal_id"], r["word_index"]) for r in rows
                      if not r.get("error")
                      and (r.get("vision_fields") or {}).get("selected_option") == "A"}
            # ...and NOT a position where any hypothesis went the other way.
            disagreed = {(r["klal_id"], r["word_index"]) for r in rows
                         if (r.get("vision_fields") or {}).get("selected_option") == "B"}
            specs += [f"{k}:{w}" for k, w in sorted(agreed - disagreed)]
            if disagreed:
                print(f"  {len(disagreed)} position(s) the ink did NOT confirm - left open:")
                for k, w in sorted(disagreed):
                    print(f"    klal {k} word {w}")
        added = ack.record_selected(report, ACK_PATH, args.note, specs)
        print(f"Acknowledged {added} candidate(s) into {ACK_PATH}")
        report = build()

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
        f.flush()
    amb = sum(1 for r in report if r["ambiguous"])
    klalim = len({r["klal_id"] for r in report})
    print(f"Wrote {OUT_PATH}: {len(report)} lexical-defect candidate(s) across {klalim} klalim "
          f"({len(report) - amb} single-answer, {amb} ambiguous)")
    acked = sum(1 for r in report if r.get("acknowledged"))
    print(f"  {acked} acknowledged (checked against the ink), {len(report) - acked} not yet")
    print("  NOT flags and NOT fixes - a triage queue, and a WEAK one: these detectors "
          "argue from frequency, which is evidence about the language and not about this "
          "page. 166 of 166 candidates below the review tier were read as the STORED text "
          "by vision (item 0DU). Adjudicate by vision before surfacing any of this.")


if __name__ == "__main__":
    main()
