# [PRODUCTION] Combine the vision-verified Part-1 correction candidates into the
# per-klal dataset the review dashboard consumes (review_server.py's /api/klal
# flag overlay - the static review.html this used to name was retired
# 2026-08-07): one entry per flagged word, with a human-readable flag
# classifying what the vision check implies.
import difflib
import json
import os
import re

import corpus_io as cio

# Moved one level deeper (pipeline/ or tools/) 2026-08-16 - REPO now goes up
# two levels, not one, to keep resolving to the actual repo root where
# part1.json/docai_word_boxes/etc. live.
REPO = cio.REPO
IN_PATH = os.path.join(REPO, "corrections_verified_part1.json")
OUT_PATH = os.path.join(REPO, "corrections_part1.json")
PART1_PATH = cio.PART1_PATH
# ADDED 2026-08-21 (PROJECT-STATUS.md, "surface the VLM baseline into the
# dashboard for review" - user-requested, "just enrich"): a THIRD,
# genuinely independent reading for every candidate this stage already
# serves - VlmWitnessEngine's blind, whole-klal transcription, diffed
# against the klal's own current clean_text (the same word-index space
# every candidate here already uses). Optional input: a fresh clone or a
# machine that hasn't run tools/run_part1_vlm_full_baseline.py (a paid API
# script, not part of rebuild_all.sh) simply gets vlm_reading: null
# everywhere rather than a crash - see load_vlm_baseline()'s own docstring.
VLM_BASELINE_PATH = os.path.join(REPO, "tools", "second_witness_eval", "vlm_part1_full_baseline.txt")
SURYA_BASELINE_PATH = os.path.join(REPO, "tools", "second_witness_eval", "surya_part1_full_baseline.txt")
# Written by pipeline/synthesize_multi_witness.py (stage 4a). Absent on a
# fresh clone or before the synthesizer has run - merged if present, skipped
# if not, never a hard dependency.
CONSENSUS_PATH = os.path.join(REPO, "consensus_disputes_part1.json")

# Minimum vision confidence before classify() treats Gemini's A/B selection as
# a machine resolution rather than "ambiguous, a human still has to look".
# Named 2026-08-15: it was the bare literal 0.7 written out three separate
# times inside classify(), and the one place it was MISSING (the 'replace'
# branch, which trusted any confidence at all) is exactly the asymmetry bug
# fixed 2026-08-13, PROJECT-STATUS.md finding 8. Three independent copies of a
# threshold is how one of them gets updated and the others don't.
# Per CLAUDE.md Lesson 2 this is a triage threshold, not a certificate: a
# candidate scoring above it has been prioritised, not proven correct.
MIN_VISION_CONFIDENCE = 0.7


def load_vlm_baseline(path=VLM_BASELINE_PATH):
    """{klal_id: [word, ...]} from tools/run_part1_vlm_full_baseline.py's
    output - a blind, whole-klal transcription per klal, genuinely
    independent of the DocAI-vs-stored-text comparison every candidate here
    already comes from (see PROJECT-STATUS.md, 2026-08-21, "the VLM A/B
    passes... surface the better readings into the dashboard"). Same header
    format both baseline passes (A and B) write: "=== KLAL N (...) ===".
    Returns {} - not an error - if the file doesn't exist, so a fresh clone
    or a machine that hasn't run the (paid-API, not rebuild_all.sh-gated)
    baseline script yet still assembles correctly, just without VLM
    enrichment."""
    if not os.path.exists(path):
        return {}
    by_klal = {}
    current_klal = None
    lines = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^===\s*KLAL\s+(\d+)", line)
            if m:
                if current_klal is not None:
                    by_klal[current_klal] = " ".join(lines).split()
                    lines = []
                current_klal = int(m.group(1))
            elif current_klal is not None:
                lines.append(line.strip())
        if current_klal is not None:
            by_klal[current_klal] = " ".join(lines).split()
    return by_klal


def build_vlm_alignment(klal_words, vlm_words):
    """clean_text word_index -> the witness's own word at that position.

    FIXED 2026-08-23 (code review, finding C15). This used to walk
    SequenceMatcher.get_matching_blocks() alone - and a matching block is BY
    DEFINITION a run where the two sequences are equal, so every value it
    returned was just the corpus's own word handed back. Measured before the
    fix: 49,138 aligned VLM words and 34,892 aligned Surya words, ZERO
    divergent in either. The `vlm_reading`/`surya_reading` fields this feeds
    were therefore structurally incapable of ever showing the disagreement
    they were added to surface, and review_frontend/app.js's "only offer it if
    it says something new" dedupe then dropped every one of them, so the
    option never rendered at all.

    Now delegates to corpus_io.align_witness, which additionally reports an
    unambiguous 1:1 substitution as a real differing reading while still
    refusing to pair words positionally inside a ragged replace block
    (Lesson 5). Kept as a named wrapper because three call sites and the
    existing unit tests refer to it, and because "the alignment used by the
    corrections assembler" is worth a name of its own."""
    return {wi: reading for wi, (reading, _verdict)
            in cio.align_witness(klal_words, vlm_words).items()}


def merge_consensus_disputes(by_klal, path=CONSENSUS_PATH):
    """Fold pipeline/synthesize_multi_witness.py's output into this stage's
    own, so a rebuild REGENERATES multi-witness disputes instead of deleting
    them.

    ADDED 2026-08-23 (code review, finding C1). The two scripts this replaces
    (tools/extract_{vlm,surya}_consensus_disputes.py) delivered the same kind
    of finding by opening corrections_part1.json - this stage's OUTPUT - and
    appending to it. 1,108 items lived there, and every one of them, plus any
    human review time spent on them, was destroyed by the next ./rebuild_all.sh
    run. A witness contributes a source file the pipeline reads; it never
    edits the pipeline's own product.

    Two cases, deliberately kept distinct:
      * A position that ALREADY has a candidate (DocAI disagreed there, so
        this stage built one from the verified set) is ENRICHED - it gains
        the corroborating engines, not a duplicate row.
      * A position with no candidate (DocAI agreed with the corpus, but two
        other engines agree it is wrong) becomes a NEW entry. This is the
        genuinely new signal multi-witness synthesis adds: a disagreement the
        DocAI-vs-stored diff cannot see by construction.

    Missing file is not an error - the synthesizer may not have run yet on a
    fresh clone, same contract as load_vlm_baseline()."""
    consensus = cio.load_json(path, default={}) or {}
    n_new = n_enriched = 0

    for kid_str, items in consensus.items():
        existing = {e["word_index"]: e for e in by_klal.get(kid_str, [])}
        for d in items:
            engines = d.get("agreeing_engines", [])
            witnesses = d.get("witnesses", {})
            note = (f"Multi-witness consensus: {' + '.join(engines)} agree on "
                    f"'{d['consensus_reading']}' against stored '{d['final_text']}'.")
            artifact = d.get("ligature_artifact")
            if artifact:
                # The engines agree because they share ONE printing defect, not
                # because they independently corroborate each other. Carried
                # through so the dashboard can say so rather than showing a
                # reviewer "3 engines agree" for a known ink artifact.
                note += (f" NOTE: explainable as the catalogued '{artifact}' printer "
                         f"ligature artifact - a shared ink defect, so this agreement "
                         f"is NOT independent corroboration and the stored text is "
                         f"most likely correct.")
            prior = existing.get(d["word_index"])
            if prior is not None:
                prior["consensus_engines"] = engines
                prior["consensus_reading"] = d["consensus_reading"]
                prior["ligature_artifact"] = artifact
                n_enriched += 1
                continue
            by_klal.setdefault(kid_str, []).append({
                "word_index": d["word_index"],
                "opcode": "replace",
                # C2: these are what each engine ACTUALLY read, or None where
                # it was not consulted / had no usable reading. Never the
                # corpus's own word standing in for an engine that never ran.
                "docai_reading": witnesses.get("docai"),
                "final_text": d["final_text"],
                "page": d.get("page"),
                "bbox": d.get("bbox"),
                "vision_selected": None,
                "vision_transcription": None,
                "confidence": None,
                "reasoning": note,
                "vlm_reading": witnesses.get("vlm"),
                "surya_reading": witnesses.get("surya"),
                "consensus_engines": engines,
                "consensus_reading": d["consensus_reading"],
                "ligature_artifact": artifact,
                "flag": "current_text_may_be_wrong",
            })
            n_new += 1

    for items in by_klal.values():
        items.sort(key=lambda e: e["word_index"])
    return n_new, n_enriched


def live_word_span(words, word_index, expected_text):
    """Same span logic as apply_reviewer_decisions.py's apply_replace(): a
    multi-word corrected_word occupies word_index..word_index+n in the
    whitespace-split clean_text. Returns the live span, or None if
    word_index is out of range."""
    span_len = len(expected_text.split()) if expected_text else 1
    if word_index < 0 or word_index + span_len > len(words):
        return None
    return words[word_index:word_index + span_len]


def check_drift(c, klal_words):
    """A candidate was generated against a snapshot of part1.json at build
    time. If part1.json has since changed at this position (another fix,
    a punctuation pass, a reindexing bug - see PROJECT-STATUS.md's
    reindexing incident) the candidate's word_index/corrected_word can go
    stale while corrections_verified_part1.json still serves the old
    values as if current. Only 'replace' and 'insert' have a non-null
    corrected_word to check against live text; 'delete' proposes a word
    that by definition isn't in final_text, so there's nothing at
    word_index to compare it to - only bounds-check it."""
    op = c["opcode"]
    idx = c["word_index_in_final_text"]
    if klal_words is None:
        return True  # klal_id not in current part1.json at all
    if op in ("replace", "insert"):
        expected = c["corrected_word"]
        live = live_word_span(klal_words, idx, expected)
        if live is None:
            return True
        return " ".join(live) != (expected or "")
    if op == "delete":
        return idx < 0 or idx > len(klal_words)
    return False


def classify(c):
    op = c["opcode"]
    sel = c.get("vision_selected")
    conf = c.get("vision_confidence")

    if op == "replace":
        # FIXED 2026-08-13 (PROJECT-STATUS.md finding 8): 'delete' below
        # gates on MIN_VISION_CONFIDENCE before trusting a selection; this
        # branch used to trust A/B at any confidence, including a
        # low-confidence guess - asymmetric for no principled reason.
        # Currently inert (all 214 live replace candidates score >= 0.7),
        # but a future low-confidence replace would otherwise sail through
        # as if it were a confident machine resolution.
        if sel == "A":
            return "current_text_may_be_wrong" if conf and conf >= MIN_VISION_CONFIDENCE else "ambiguous"
        if sel == "B":
            return "current_text_confirmed" if conf and conf >= MIN_VISION_CONFIDENCE else "ambiguous"
        if sel == "UNCERTAIN":
            return "ambiguous"
        return "error"
    if op == "delete":
        if sel == "A" and conf and conf >= MIN_VISION_CONFIDENCE:
            return "possible_omission"
        if sel == "ERROR":
            return "error"
        return "ambiguous"
    if op == "insert":
        return "unverified_insertion"
    return "unverified"


def main():
    verified = cio.load_json(IN_PATH)
    part1 = cio.load_part1(PART1_PATH)
    words_by_klal = {k["klal_id"]: k["clean_text"].split() for k in part1}
    vlm_by_klal = load_vlm_baseline(VLM_BASELINE_PATH)
    surya_by_klal = load_vlm_baseline(SURYA_BASELINE_PATH)
    # Built lazily, once per klal actually needed (not all 222) - the
    # alignment itself is cheap, but no reason to pay for klalim with zero
    # candidates.
    vlm_alignment_cache = {}
    surya_alignment_cache = {}

    def vlm_reading_for(klal_id, word_index):
        if klal_id not in vlm_by_klal:
            return None
        if klal_id not in vlm_alignment_cache:
            vlm_alignment_cache[klal_id] = build_vlm_alignment(
                words_by_klal.get(klal_id, []), vlm_by_klal[klal_id])
        return vlm_alignment_cache[klal_id].get(word_index)

    def surya_reading_for(klal_id, word_index):
        if klal_id not in surya_by_klal:
            return None
        if klal_id not in surya_alignment_cache:
            surya_alignment_cache[klal_id] = build_vlm_alignment(
                words_by_klal.get(klal_id, []), surya_by_klal[klal_id])
        return surya_alignment_cache[klal_id].get(word_index)

    by_klal = {}
    n_drifted = 0
    for c in verified:
        drifted = check_drift(c, words_by_klal.get(c["klal_id"]))
        entry = {
            "word_index": c["word_index_in_final_text"],
            "opcode": c["opcode"],
            "docai_reading": c["original_word"],
            "final_text": c["corrected_word"],
            "page": c["page"],
            "bbox": c["bbox"],
            "vision_selected": c.get("vision_selected"),
            "vision_transcription": c.get("vision_transcription"),
            "confidence": c.get("vision_confidence"),
            "reasoning": c.get("vision_reasoning"),
            "vlm_reading": vlm_reading_for(c["klal_id"], c["word_index_in_final_text"]),
            "surya_reading": surya_reading_for(c["klal_id"], c["word_index_in_final_text"]),
            # A drifted candidate's flag is forced to "stale_candidate"
            # rather than whatever classify() would say - a confident
            # "current_text_confirmed" is actively misleading once the
            # candidate no longer points at the text it was verified
            # against (see PROJECT-STATUS.md's reindexing incident, the
            # exact failure this closes). review_frontend/app.js treats
            # any flag other than "current_text_confirmed" as its default
            # "open" state, so this is safe to introduce without a
            # frontend change.
            "flag": "stale_candidate" if drifted else classify(c),
        }
        if drifted:
            n_drifted += 1
        by_klal.setdefault(str(c["klal_id"]), []).append(entry)

    n_new, n_enriched = merge_consensus_disputes(by_klal)

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(by_klal, f, ensure_ascii=False, indent=2)

    flags = {}
    for entries in by_klal.values():
        for e in entries:
            flags[e["flag"]] = flags.get(e["flag"], 0) + 1
    print(f"Wrote {OUT_PATH}: {sum(len(v) for v in by_klal.values())} items across {len(by_klal)} klalim")
    print(f"  multi-witness consensus: {n_new} new dispute(s), {n_enriched} existing candidate(s) enriched")
    print("By flag:", flags)
    if n_drifted:
        print(f"WARNING: {n_drifted} candidate(s) drifted from live part1.json content - "
              f"flagged 'stale_candidate', not served as their computed classification.")


if __name__ == "__main__":
    main()
