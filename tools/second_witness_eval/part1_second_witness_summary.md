# Part 1 VLM Second Witness — Summary

2026-08-21. `VlmWitnessEngine` (blind, single-word-crop, independent
transcription — no A/B framing, no context) run against 497 of Part 1's 539
`corrections_part1.json` candidates (42 skipped: no bbox). Compared against
`docai_reading` (option A), `final_text` (the corpus's current/adjudicated
reading, option B), and the existing single-witness `vision_selected` pick
from `verify_corrections_vision.py`'s own A/B forced-choice adjudication.

This is the concrete "run VlmWitnessEngine for real" step, scoped to Part 1
(already-adjudicated, real candidates) rather than the fabricated/purged
Parts 2-3 set.

## Method note (read before the numbers)

`VlmWitnessEngine`'s prompt asks for a blind, whole-crop, line-by-line
transcription, not "transcribe only this one word" — even a tight
single-word bbox+padding crop routinely returns the rest of that printed
line too. Comparison therefore checks whether the target reading's words
appear among the VLM's individually-normalized tokens (containment, not
whole-string equality) for the headline classification; the two-tier
fuzzy-match breakdown below is a post-hoc refinement of the same data (no
new API calls), because a first pass at exact/contains matching flagged many
cases that turned out, on inspection, to be one-letter OCR noise on an
otherwise-agreeing reading, not real disagreement.

## Headline numbers

Raw classification (`run_part1_vlm_second_witness.py`'s own verdict field):

| Verdict | Count | % |
|---|---:|---:|
| THIRD_READING | 219 | 44.1% |
| MATCHES_B_CORPUS | 159 | 32.0% |
| MATCHES_A_DOCAI | 118 | 23.7% |
| MATCHES_BOTH | 1 | 0.2% |

Refined against the *existing single-witness pick specifically* (not just A
vs B in the abstract), with a fuzzy-match tier added post-hoc:

| Tier | Count | % |
|---|---:|---:|
| Exact match to existing pick | 213 | 42.9% |
| Near match (SequenceMatcher ratio ≥ 0.8) | 92 | 18.5% |
| Genuine disagreement (ratio < 0.8) | 182 | 36.6% |
| No existing pick to compare | 10 | 2.0% |

**61.4% combined (exact + near) corroboration.** The near-match tier is real
and material — spot-checked several: e.g. existing pick `ומדקמהדר` vs this
witness's blind read containing `ומדקמהדי` (one final letter differs, a
classic OCR ד/ר-ambiguity-adjacent slip) — plainly the same word, not a
disagreement, and would have been misclassified as THIRD_READING by exact
matching alone. Full per-candidate report:
`part1_second_witness_report.jsonl`.

## What changes in confidence

Nothing was changed in `corrections_part1.json` or `part1.json` — this is an
investigative comparison, not a pipeline stage; it does not touch the
corpus, following the same principle as `evaluate_ocr_alignment.py` and the
rest of `second_witness_eval/`. What this *would* mean if incorporated as a
real second-witness signal per Lesson 9 (two independent signals must agree
before a fix is trusted):

- The 213 exact + 92 near corroborated candidates (61.4%) would gain real
  confidence — an actually independent signal now agrees, not just the same
  Gemini-model-family adjudicator asked twice (the architecture-circularity
  concern already documented in `PROPOSED_PIPELINE_ARCHITECTURE.md`).
- The 182 genuine-disagreement candidates (36.6%) should NOT be treated as
  "probably wrong" without a closer look - some fraction are likely this
  witness's wide-crop context picking up neighboring text rather than a real
  disagreement about the target word (the same crop-scope caveat noted
  above). But this is exactly the kind of gap Lesson 9 says needs a second,
  differently-sourced signal before trusting the existing pick's confidence
  at face value - **worth a follow-up pass that spot-checks a sample of the
  182 by actually looking at the crop**, not concluded here.

## One concrete, notable disagreement

Klal 2, word 109: `docai_reading: "אטינא"`, `final_text: "אמינא"`,
existing pick: B (`"אמינא"`, confidence 1.0, reasoning: "the second letter is
a standard Hebrew מ which the OCR engine mistook for a ט"). This witness's
blind read: `...כ • והגם ש ם אטינא ש ו מאא"ע קפ...` — contains `אטינא`
(matching **option A**, not the existing B pick), ratio 0.8 against B. A
concrete case where this second, independent witness leans toward
DocAI's original reading rather than the corpus's current one - worth a
direct look at the crop before treating either as settled.
