#!/usr/bin/env python3
# [PRODUCTION] Stage 4a of rebuild_all.sh. Multi-witness consensus synthesis:
# find word positions where two INDEPENDENT engines agree on a reading that
# differs from what part1.json currently stores, and write them to
# consensus_disputes_part1.json for assemble_corrections_dataset.py to merge.
#
# Built 2026-08-23 to replace tools/extract_vlm_consensus_disputes.py and
# tools/extract_surya_consensus_disputes.py, which produced the same KIND of
# finding but delivered it by writing directly into corrections_part1.json -
# a DERIVED file that assemble_corrections_dataset.py truncates and rewrites
# on every ./rebuild_all.sh. 1,108 items and every human review minute spent
# on them were one rebuild away from being destroyed (code review 2026-08-23,
# finding C1). This script writes its own SOURCE artifact instead, and stage 4
# merges it, so a rebuild regenerates consensus disputes rather than deleting
# them. Same principle as the VLM baseline: a witness contributes a file the
# pipeline reads, never an edit to the pipeline's own output.
#
# Three rules this script exists to enforce, each one a defect the extractors
# it replaces actually had:
#
#   1. A WITNESS IS AN ENGINE, NOT A SAMPLE. VLM Pass A and Pass B are the
#      same gemini model run twice (measured self-consistency 87.43%).
#      extract_vlm_consensus_disputes.py counted "Pass A == Pass B" as
#      two-witness consensus and emitted 1,051 disputes on that basis; 290 of
#      them had Surya - a genuinely different engine - agreeing with the
#      stored corpus text against the VLM. Here Pass A/Pass B agreement is a
#      STABILITY GATE on the single VLM witness (disagree with yourself and
#      you get no vote at this position), never a second vote. Consensus
#      requires two distinct engines from {docai, vlm, surya}.
#
#   2. A WITNESS FIELD MUST REPORT WHAT THAT WITNESS ACTUALLY SAID. The
#      extractors set "docai_reading" to the stored base text on all 1,108
#      items, for positions where DocAI was never consulted at all, and the
#      dashboard rendered that as a "DocAI reading" card agreeing with the
#      corpus. Here every witness reading is either what the engine really
#      produced or None, and `witnesses` records each engine's verdict
#      explicitly so "agrees", "differs" and "no reading" stay distinguishable.
#
#   3. NO GUESSED POSITIONS. Alignment goes through corpus_io.align_witness,
#      which reports a substitution only for an unambiguous 1:1 replace block
#      and drops ragged ones rather than pairing words positionally (Lesson 5).
#      Bboxes come from review_server._corpus_word_bboxes / _word_pages_map,
#      which use matching blocks only and already resolve the multi-page
#      recurring-word collision - the extractors hand-rolled both and got
#      260 of 16,026 bboxes from a non-matching `replace` token.
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import corpus_io as cio
import review_server as rs
import typography

sys.path.insert(0, os.path.join(REPO, "tools", "second_witness_eval"))
import evaluate_ocr_alignment as eval_script

VERIFIED_PATH = os.path.join(REPO, "corrections_verified_part1.json")
VLM_A_PATH = cio.repo_path("tools", "second_witness_eval", "vlm_part1_full_baseline.txt")
VLM_B_PATH = cio.repo_path("tools", "second_witness_eval", "vlm_part1_full_baseline_passB.txt")
SURYA_PATH = cio.repo_path("tools", "second_witness_eval", "surya_part1_full_baseline.txt")
OUT_PATH = os.path.join(REPO, "consensus_disputes_part1.json")

# Engines that can vote. DocAI's vote comes from the corrections pipeline's own
# candidates (it is the primary extraction, already diffed against the corpus by
# build_corrections_dataset.py) rather than from a re-derivation here.
ENGINES = ("docai", "vlm", "surya")


def load_baseline(path):
    """{klal_id: [words]} from a witness baseline text file, or {} if the file
    doesn't exist (a fresh clone, or before the paid-API baseline has ever
    run) - missing witness data must degrade to "no vote", never crash."""
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        by_klal = eval_script.parse_candidate_ocr(f.read())
    return {kid: text.split() for kid, text in by_klal.items()}


def docai_verdicts(verified):
    """(klal_id, word_index) -> DocAI's own differing reading.

    Sourced from the real corrections pipeline: build_corrections_dataset.py
    already diffs fresh DocAI tokens against stored text, and a candidate at a
    position IS DocAI disagreeing there. `original_word` is DocAI's token,
    `corrected_word` is what the corpus stores (see
    assemble_corrections_dataset.py's own mapping of the same two fields)."""
    out = {}
    for c in verified:
        if c.get("opcode") != "replace":
            # insert/delete are word-count changes, not a substitution this
            # position-keyed consensus can compare against another engine.
            continue
        reading = c.get("original_word")
        if reading:
            out[(c["klal_id"], c["word_index_in_final_text"])] = reading
    return out


def vlm_verdicts(corpus_words, pass_a, pass_b):
    """word_index -> (reading, verdict) for the VLM as ONE witness.

    Pass B is a stability gate, not a second vote (see rule 1 in the module
    header): a position where the same model read two different things across
    two runs is a position where this witness is unreliable, so it abstains -
    it does not get to outvote a different engine with its own noise."""
    a = cio.align_witness(corpus_words, pass_a)
    b = cio.align_witness(corpus_words, pass_b)
    out = {}
    for wi, (reading, verdict) in a.items():
        if wi not in b:
            continue  # Pass B has no reading here - unstable, abstain
        b_reading, _ = b[wi]
        if cio.hebrew_letters_only(b_reading) != cio.hebrew_letters_only(reading):
            continue  # the two passes disagree with each other - abstain
        out[wi] = (reading, verdict)
    return out


def active_human_decisions():
    """(klal_id, word_index) -> the text a reviewer already chose there.

    A position a human has already ruled on is resolved; re-emitting it as an
    open dispute is noise, and it collides in the UI: review_server.api_klal()
    appends manual_correction entries AFTER machine candidates and
    review_frontend/app.js's word map is last-write-wins, so the manual entry
    silently replaces the machine one and the reviewer never learns a candidate
    existed (the exact class tests/test_corpus_invariants.py's
    test_no_rendered_manual_correction_hides_a_machine_candidate exists to
    catch - it caught this on the first synthesis run).

    Skipped, but never silently: main() reports how many skipped positions the
    consensus CORROBORATED versus CONTRADICTED, and prints every contradiction.
    A human choosing X while two independent engines agree on Y is precisely
    the case Lesson 9 says must not be buried."""
    import review_decisions as rd
    out = {}
    for d_type in ("disputed_choice", "manual_correction"):
        for (kid, wi), record in rd.all_current(d_type).items():
            if wi is not None:
                out[(kid, wi)] = record.get("chosen_text")
    return out


def synthesize(part1, verified, vlm_a, vlm_b, surya, decided=None):
    """Every position where >= 2 distinct engines agree on the same reading
    and that reading differs from the stored corpus text."""
    docai = docai_verdicts(verified)
    decided = {} if decided is None else decided
    disputes = []
    stats = {"klalim_no_surya": 0, "klalim_no_vlm": 0, "vlm_abstained": 0,
             "skipped_corroborating_a_human": 0, "contradicting_a_human": [],
             "ligature_artifacts": 0}

    for k in part1:
        kid = k["klal_id"]
        words = k["clean_text"].split()

        surya_words = surya.get(kid) or []
        vlm_a_words = vlm_a.get(kid) or []
        vlm_b_words = vlm_b.get(kid) or []
        # An EMPTY witness body is "no coverage", not "this witness confirms
        # every word" - 10 of Part 1's 222 klalim have an empty Surya body and
        # both previous consumers silently read that as agreement (code review
        # 2026-08-23). Counted and reported, never treated as a vote.
        if not surya_words:
            stats["klalim_no_surya"] += 1
        if not vlm_a_words or not vlm_b_words:
            stats["klalim_no_vlm"] += 1

        surya_align = cio.align_witness(words, surya_words) if surya_words else {}
        vlm_align = (vlm_verdicts(words, vlm_a_words, vlm_b_words)
                     if vlm_a_words and vlm_b_words else {})
        if vlm_a_words and vlm_b_words:
            stats["vlm_abstained"] += max(
                0, len(cio.align_witness(words, vlm_a_words)) - len(vlm_align))

        for wi, stored in enumerate(words):
            stored_norm = cio.hebrew_letters_only(stored)
            readings = {}

            d = docai.get((kid, wi))
            if d is not None:
                readings["docai"] = d
            v = vlm_align.get(wi)
            if v is not None and v[1] == "differs":
                readings["vlm"] = v[0]
            s = surya_align.get(wi)
            if s is not None and s[1] == "differs":
                readings["surya"] = s[0]

            if len(readings) < 2:
                continue

            # Group the differing engines by WHAT they read. Two engines only
            # corroborate each other if they agree on the same alternative -
            # two engines each reading something different is a 3-way split,
            # which is a human-review case, not a consensus.
            by_reading = {}
            for engine, reading in readings.items():
                by_reading.setdefault(cio.hebrew_letters_only(reading), []).append(engine)

            for norm_reading, engines in by_reading.items():
                if len(engines) < 2 or norm_reading == stored_norm:
                    continue
                reading = readings[engines[0]]
                # A consensus every engine can reach by sharing ONE printing
                # artifact is not independent corroboration. Measured on the
                # first synthesis run: 16 such agreements, all the alef-lamed
                # sort losing its lamed, including unanimous 3-of-3 - and 11 of
                # them on words a human had already correctly restored. Tagged,
                # not dropped: the reviewer should still see it, but must see it
                # labelled as an artifact rather than as three engines agreeing.
                artifact = typography.ligature_artifact(stored, reading)
                if artifact:
                    stats["ligature_artifacts"] += 1
                if (kid, wi) in decided:
                    chosen = decided[(kid, wi)]
                    if cio.hebrew_letters_only(chosen or "") == norm_reading:
                        stats["skipped_corroborating_a_human"] += 1
                    else:
                        stats["contradicting_a_human"].append(
                            (kid, wi, chosen, reading, sorted(engines), artifact))
                    break
                disputes.append({
                    "klal_id": kid,
                    "word_index": wi,
                    "opcode": "replace",
                    "final_text": stored,
                    "consensus_reading": reading,
                    "agreeing_engines": sorted(engines),
                    "ligature_artifact": artifact,
                    # Every engine's own verdict at this position, so the
                    # dashboard and any later audit can tell "agrees",
                    # "differs" and "was never asked" apart. No field here
                    # ever carries the corpus's own word in place of an
                    # engine that was not consulted.
                    "witnesses": {
                        "docai": docai.get((kid, wi)),
                        "vlm": vlm_align[wi][0] if wi in vlm_align else None,
                        "surya": surya_align[wi][0] if wi in surya_align else None,
                    },
                })
                break  # at most one consensus alternative per position

    return disputes, stats


def attach_scan_positions(disputes, part1_by_id, regions, verified=()):
    """Fill page + bbox, preferring the corrections pipeline's own already-
    computed position and falling back to the server's alignment helpers.

    The two-source order is not arbitrary. Wherever DocAI is one of the
    agreeing engines, DocAI's token DIFFERS from the stored word, so the
    matching-block alignment below structurally cannot locate it - measured:
    92 of 96 unpositioned disputes were exactly that case. But
    build_corrections_dataset.py already located those positions when it
    created the candidate (that is what a candidate's own bbox IS), so the
    right move is to reuse that verified position rather than re-derive or
    estimate one.

    Deliberately NOT hand-rolled: _corpus_word_bboxes uses matching blocks
    only (never a `replace` opcode's non-matching token) and _word_pages_map
    already resolves the recurring-word multi-page collision that last-page-
    wins gets wrong. A dispute with no confident position gets page/bbox
    None - the dashboard can navigate without a box, but a box drawn on the
    wrong word is a reviewer reading the wrong ink (Lesson 14)."""
    from_candidate = {}
    for c in verified:
        if c.get("bbox"):
            from_candidate[(c["klal_id"], c["word_index_in_final_text"])] = (
                c.get("page"), c["bbox"])

    by_klal = {}
    for d in disputes:
        by_klal.setdefault(d["klal_id"], []).append(d)

    for kid, items in by_klal.items():
        words = part1_by_id[kid]["clean_text"].split()
        region = regions.get(str(kid), {})
        word_pages = None
        boxes_by_page = {}
        for d in items:
            known = from_candidate.get((kid, d["word_index"]))
            if known is not None:
                d["page"], d["bbox"] = known
                continue
            if word_pages is None:  # only pay for the alignment if needed
                word_pages = rs._word_pages_map(kid, words, region)
            page = word_pages.get(d["word_index"])
            d["page"] = page
            if page is None:
                d["bbox"] = None
                continue
            if page not in boxes_by_page:
                boxes_by_page[page] = rs._corpus_word_bboxes(kid, words, page)
            d["bbox"] = boxes_by_page[page].get(d["word_index"])
    return disputes


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=OUT_PATH)
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would be written, write nothing")
    args = ap.parse_args()

    part1 = cio.load_part1()
    part1_by_id = {k["klal_id"]: k for k in part1}
    verified = cio.load_json(VERIFIED_PATH, default=[]) or []
    vlm_a = load_baseline(VLM_A_PATH)
    vlm_b = load_baseline(VLM_B_PATH)
    surya = load_baseline(SURYA_PATH)

    disputes, stats = synthesize(part1, verified, vlm_a, vlm_b, surya,
                                 decided=active_human_decisions())
    disputes = attach_scan_positions(disputes, part1_by_id, rs._load_regions(), verified)

    by_klal = {}
    for d in disputes:
        by_klal.setdefault(str(d["klal_id"]), []).append(d)
    for items in by_klal.values():
        items.sort(key=lambda x: x["word_index"])

    pairs = {}
    for d in disputes:
        pairs["+".join(d["agreeing_engines"])] = pairs.get("+".join(d["agreeing_engines"]), 0) + 1
    no_box = sum(1 for d in disputes if d.get("bbox") is None)

    print(f"{len(disputes)} multi-witness consensus dispute(s) across {len(by_klal)} klalim")
    print("  by agreeing engines:", pairs or "(none)")
    print(f"  without a confident scan position: {no_box}")
    print(f"  klalim with no Surya coverage: {stats['klalim_no_surya']} "
          f"(counted as no vote, NOT as agreement)")
    print(f"  klalim with no VLM coverage: {stats['klalim_no_vlm']}")
    print(f"  agreements explainable as a known printer-ligature artifact: "
          f"{stats['ligature_artifacts']} (shared ink defect, NOT independent "
          f"corroboration - see pipeline/typography.py)")
    print(f"  VLM abstentions from Pass A/Pass B instability: {stats['vlm_abstained']}")
    print(f"  skipped, already decided by a human and CORROBORATED by the consensus: "
          f"{stats['skipped_corroborating_a_human']}")
    contra = stats["contradicting_a_human"]
    art = [c for c in contra if c[5]]
    real = [c for c in contra if not c[5]]
    print(f"  skipped, already decided by a human but CONTRADICTED by the consensus: "
          f"{len(contra)} - of which {len(art)} are a known ligature artifact "
          f"(the engines share the misread, the human is right) and {len(real)} are not")
    if art:
        print(f"    [{len(art)} ligature-artifact contradiction(s) suppressed from the list "
              f"below - the stored text is correct in each]")
    for kid, wi, chosen, reading, engines, _a in real:
        # Never buried in a count: a human choosing one reading while two
        # independent engines agree on another is a Lesson 9 case that needs
        # a person to look again, not a silently-dropped row.
        print(f"    klal {kid} w{wi}: human chose {chosen!r}, "
              f"{'+'.join(engines)} read {reading!r}")

    if args.dry_run:
        print("--dry-run: nothing written")
        return

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(by_klal, f, ensure_ascii=False, indent=2)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
