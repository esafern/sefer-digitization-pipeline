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
# WHAT THIS DELIBERATELY DOES NOT DO: it does not write klal_flag rows. The
# ledger is append-only and permanent, and these detectors carry real false
# positives - measured 2026-08-26, of 262 merged positions the independent
# witnesses CONTRADICT 149, and `detect_insertion_deletion` proposes
# `בחרא`->`ברא` for the very word whose correct reading is `בחדא`. This is a
# triage queue for a human, not a fix list. Promoting an entry to a flag stays a
# deliberate, separate act, exactly like every other decision in this pipeline.
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pipeline"))
sys.path.insert(0, os.path.join(REPO, "tools"))

import corpus_io as cio  # noqa: E402
import detect_real_word_substitution as sub  # noqa: E402
import detect_insertion_deletion as ins  # noqa: E402

OUT_PATH = cio.repo_path("lexical_defect_report.json")


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

    def rows(items, kind, ambiguous):
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
            out.append({"klal_id": kid, "word_index": wi, "stored": corrupt,
                        "proposals": props, "detector": kind,
                        "ambiguous": bool(ambiguous)})
        return out

    report = (rows(sub_hi, "substitution", False) + rows(sub_amb, "substitution", True)
              + rows(ins_hi, "insertion_deletion", False) + rows(ins_amb, "insertion_deletion", True))
    report.sort(key=lambda r: (r["klal_id"], r["word_index"]))
    return report


def main():
    report = build()
    if report is None:
        print("  WARNING: sefaria_reference_corpus/word_freq.json is absent - the lexical "
              "detectors CANNOT RUN and no report was written.")
        print("           This is not 'zero defects'. See SETUP.md; the cache is gitignored.")
        return
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
        f.flush()
    amb = sum(1 for r in report if r["ambiguous"])
    klalim = len({r["klal_id"] for r in report})
    print(f"Wrote {OUT_PATH}: {len(report)} lexical-defect candidate(s) across {klalim} klalim "
          f"({len(report) - amb} single-answer, {amb} ambiguous)")
    print("  NOT flags and NOT fixes - a triage queue. The independent witnesses contradict "
          "many of these; read the context before acting on any of them.")


if __name__ == "__main__":
    main()
