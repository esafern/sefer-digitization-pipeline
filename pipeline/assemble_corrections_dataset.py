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
    """clean_text word_index -> the VLM's own word at that position, for
    every position where the two align (SequenceMatcher.get_matching_
    blocks() - same technique tools/second_witness_eval/evaluate_ocr_
    alignment.py's "Candidate Verification Breakdown" already uses at
    klal 8-22 scope, generalized here to every klal this stage assembles).
    A word_index with no entry means the VLM's reading didn't align there -
    either real disagreement or (per CLAUDE.md Lesson 5) an alignment gap;
    this function doesn't distinguish the two, callers just get None either
    way, same as the existing evaluation script's own convention."""
    sm = difflib.SequenceMatcher(None, klal_words, vlm_words, autojunk=False)
    alignment = {}
    for block in sm.get_matching_blocks():
        for i in range(block.size):
            alignment[block.a + i] = vlm_words[block.b + i]
    return alignment


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
    vlm_by_klal = load_vlm_baseline()
    # Built lazily, once per klal actually needed (not all 222) - the
    # alignment itself is cheap, but no reason to pay for klalim with zero
    # candidates.
    vlm_alignment_cache = {}

    def vlm_reading_for(klal_id, word_index):
        if klal_id not in vlm_by_klal:
            return None
        if klal_id not in vlm_alignment_cache:
            vlm_alignment_cache[klal_id] = build_vlm_alignment(
                words_by_klal.get(klal_id, []), vlm_by_klal[klal_id])
        return vlm_alignment_cache[klal_id].get(word_index)

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
            # ADDED 2026-08-21: a third, independent reading from the VLM
            # baseline pass (see load_vlm_baseline()/build_vlm_alignment()
            # above) - None if no VLM baseline is available, or if this
            # word_index doesn't align to anything in it. Purely additive -
            # never changes `flag`/classify()'s own verdict; a human
            # reviewer sees it as one more data point, same principle as
            # the second-witness report tonight's earlier work produced by
            # hand, now a permanent field every rebuild regenerates.
            "vlm_reading": vlm_reading_for(c["klal_id"], c["word_index_in_final_text"]),
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

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(by_klal, f, ensure_ascii=False, indent=2)

    flags = {}
    for entries in by_klal.values():
        for e in entries:
            flags[e["flag"]] = flags.get(e["flag"], 0) + 1
    print(f"Wrote {OUT_PATH}: {sum(len(v) for v in by_klal.values())} items across {len(by_klal)} klalim")
    print("By flag:", flags)
    if n_drifted:
        print(f"WARNING: {n_drifted} candidate(s) drifted from live part1.json content - "
              f"flagged 'stale_candidate', not served as their computed classification.")


if __name__ == "__main__":
    main()
