#!/usr/bin/env python3
"""
tools/second_witness_eval/run_part1_vlm_second_witness.py

Runs VlmWitnessEngine - a BLIND, independent, single-word-crop transcription
(no A/B framing, no context, just "what does this crop say") - against every
Part 1 correction candidate in corrections_part1.json that has a bbox, and
compares it against:
  - docai_reading   (option A - DocAI's original OCR reading)
  - final_text      (option B - what part1.json currently stores)
  - vision_selected (the EXISTING single-witness adjudication's own A/B pick,
                      from verify_corrections_vision.py's forced-choice call)

This is the concrete "run VlmWitnessEngine for real" step named as an open
item in PROJECT-STATUS.md (previously only done for Parts 2-3's now-purged,
fabricated candidates) - scoped here to Part 1's real, already-adjudicated
539 candidates, where an independent second opinion is actually meaningful:
does a blind read corroborate the existing single-witness decision, or
contradict it? Per CLAUDE.md Lesson 9, two independent signals agreeing is
real corroboration; a confident-sounding single signal alone is not.

Outputs a per-candidate JSONL report (append+flush per item, per the standing
incremental-disk-flushing rule) plus a summary table printed at the end.
Does NOT modify corrections_part1.json or part1.json - this is an
investigative comparison, not a pipeline stage.
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "pipeline"))

import corpus_io as cio
from second_witness_eval.vlm_witness import VlmWitnessEngine
from second_witness_eval.abstract_witness import BoundingBox

OUT_PATH = os.path.join(HERE, "part1_second_witness_report.jsonl")


def _contains_reading(vlm_tokens_norm, reading):
    """Does every word of `reading` (may be multi-word, e.g. a 2-word
    'replace' span) show up somewhere among the VLM's individually-
    normalized tokens?

    VlmWitnessEngine's prompt asks for a blind, whole-crop, line-by-line
    transcription (not "transcribe only this one word") - even a tight
    single-word bbox+padding crop routinely comes back with the rest of
    that printed line too (confirmed live: a candidate crop for klal 1 word
    85 returned 10 tokens, the target word among them, not just the target
    word alone). A whole-string equality check would then almost always
    report THIRD_READING/UNREADABLE even on a clean corroboration - check
    per-word token membership instead. Order/adjacency is NOT checked (an
    approximation, not an exact-position claim per CLAUDE.md Lesson 5) - all
    words present is treated as a corroboration for this comparison's
    purposes; multi-word candidates are a minority (opcode counts: 457
    replace / 42 insert / 40 delete, most replace/insert spans are 1 word)."""
    words = [w for w in (cio.hebrew_letters_only(w) for w in reading.split(" ")) if w]
    return bool(words) and all(w in vlm_tokens_norm for w in words)


def classify(vlm_tokens_norm, docai_reading, final_text):
    if not vlm_tokens_norm:
        return "UNREADABLE"
    a_hit = bool(docai_reading) and _contains_reading(vlm_tokens_norm, docai_reading)
    b_hit = bool(final_text) and _contains_reading(vlm_tokens_norm, final_text)
    if a_hit and b_hit:
        return "MATCHES_BOTH"
    if a_hit:
        return "MATCHES_A_DOCAI"
    if b_hit:
        return "MATCHES_B_CORPUS"
    return "THIRD_READING"


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable not set.")
        sys.exit(1)

    pdf_path = os.path.join(REPO, "berlin_square_corrected.pdf")
    corrections = cio.load_json(os.path.join(REPO, "corrections_part1.json"))

    items = []
    for klal_id_str, candidates in corrections.items():
        for c in candidates:
            if c.get("bbox") and c.get("page"):
                items.append({**c, "klal_id": int(klal_id_str)})
    items.sort(key=lambda c: (c["klal_id"], c["word_index"]))

    print("=" * 80)
    print(f"RUNNING VLM SECOND WITNESS ON {len(items)} PART 1 CANDIDATES "
          f"(of {sum(len(v) for v in corrections.values())} total; "
          f"{sum(len(v) for v in corrections.values()) - len(items)} skipped, no bbox)")
    print("=" * 80)

    engine = VlmWitnessEngine()

    # Truncate once up front, then append+flush per candidate below.
    open(OUT_PATH, "w", encoding="utf-8").close()

    counts = {}
    for i, c in enumerate(items, 1):
        klal_id = c["klal_id"]
        word_index = c["word_index"]
        bbox = BoundingBox(**c["bbox"])
        print(f"[{i}/{len(items)}] Klal {klal_id:3d} word {word_index:4d} "
              f"(page {c['page']})...", end="", flush=True)
        try:
            tokens = engine.transcribe_region(pdf_path, c["page"], bbox)
            vlm_text = " ".join(t.text for t in tokens)
            vlm_tokens_norm = {cio.hebrew_letters_only(t.text) for t in tokens
                                if cio.hebrew_letters_only(t.text)}
        except Exception as e:
            print(f" FAILED: {e}")
            vlm_text = ""
            vlm_tokens_norm = set()
        verdict = classify(vlm_tokens_norm, c.get("docai_reading"), c.get("final_text"))
        counts[verdict] = counts.get(verdict, 0) + 1

        existing_pick = c.get("vision_selected")  # "A" (docai) or "B" (final_text) from the original single-witness adjudication
        existing_reading = c.get("docai_reading") if existing_pick == "A" else c.get("final_text")
        corroborates_existing = (
            bool(existing_reading) and _contains_reading(vlm_tokens_norm, existing_reading)
        )

        record = {
            "klal_id": klal_id,
            "word_index": word_index,
            "opcode": c.get("opcode"),
            "docai_reading": c.get("docai_reading"),
            "final_text": c.get("final_text"),
            "existing_vision_selected": existing_pick,
            "existing_confidence": c.get("confidence"),
            "vlm_second_witness_reading": vlm_text,
            "verdict": verdict,
            "corroborates_existing_pick": corroborates_existing,
        }
        with open(OUT_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        print(f" -> {verdict}" + ("" if not existing_pick else
              f" (existing pick {existing_pick}: {'corroborated' if corroborates_existing else 'NOT corroborated'})"))
        time.sleep(0.15)

    print("=" * 80)
    print("SUMMARY")
    for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {k}: {v} ({100*v/len(items):.1f}%)")
    print(f"Report written to: {OUT_PATH}")
    print("=" * 80)


if __name__ == "__main__":
    main()
