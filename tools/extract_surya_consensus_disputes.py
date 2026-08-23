#!/usr/bin/env python3
"""
tools/extract_surya_consensus_disputes.py

SUPERSEDED 2026-08-23 by pipeline/synthesize_multi_witness.py. DO NOT RUN.

This script wrote new dispute items directly into corrections_part1.json - a
DERIVED file that pipeline/assemble_corrections_dataset.py truncates and
rewrites on every ./rebuild_all.sh run (stage 4/6). Between the two extractors
1,108 items lived there, and every one of them - along with any human review
time spent on them - was one rebuild away from being destroyed. That is the
single-source-of-truth rule in START_HERE.md Part 2, and Lesson 13.

Two further defects found in the same 2026-08-23 code review, both fixed in the
replacement rather than here:

  * It set "docai_reading" to the STORED BASE TEXT on every item it emitted,
    for positions where DocAI was never consulted, and the dashboard rendered
    that as a "DocAI reading" card agreeing with the corpus.
  * extract_vlm_consensus_disputes.py treated VLM Pass A == Pass B as
    two-witness consensus. Both passes are the same gemini model (measured
    self-consistency 87.43%). Of the 1,051 disputes it emitted on that basis,
    290 had Surya - a genuinely different engine - agreeing with the stored
    corpus text against the VLM.

The replacement writes its own source artifact (consensus_disputes_part1.json)
which stage 4 merges, counts witnesses by ENGINE rather than by sample, and
reports each engine's real reading or None. It runs as stage 4a of
rebuild_all.sh. Kept here, non-executable, for the evidence trail only.
"""
import sys

print(__doc__.strip(), file=sys.stderr)
print("\nRun `python3 pipeline/synthesize_multi_witness.py` instead "
      "(or just ./rebuild_all.sh, which now includes it as stage 4a).",
      file=sys.stderr)
sys.exit(2)
