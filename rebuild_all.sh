#!/bin/bash
# [PRODUCTION] Single entrypoint that regenerates every derived artifact from
# part1.json / part2.json / part3.json (the only hand-edited source of truth
# for corpus text). Run this after ANY edit to a part*.json file - a fix that
# only touches part1.json and stops there is not "done," it's half-applied;
# klalim_demo_dataset.json will silently keep showing the old text until
# this runs, and so will the review server's live views (review_server.py
# reads its source files fresh per request, so it never needs restarting -
# but it still needs THIS to have run for those files to be current).
#
# Pipeline, each stage's output feeding the next:
#   part1/2/3.json
#     -> build_klalim_demo_dataset.py  -> klalim_demo_dataset.json
#     -> build_corrections_dataset.py  -> corrections_candidates_part1.json
#     -> verify_corrections_vision.py  -> corrections_verified_part1.json   (Gemini calls, cached)
#     -> assemble_corrections_dataset.py -> corrections_part1.json
#     -> build_klal_page_regions.py    -> klal_page_regions.json
#     -> pytest tests/test_corpus_invariants.py + tests/test_pipeline_logic.py
#        -> pass/fail gate (regression suites: the derived DATA, and the
#           pure decision LOGIC that produced it - the second added
#           2026-08-14 because several correctness paths, e.g. candidate
#           drift detection and the vision cache key, are inert on current
#           data and cannot be exercised by checking the corpus alone)
#
# tests/test_review_server.py is deliberately NOT part of this gate - it
# needs a live server subprocess + a real browser (Playwright), unlike the
# fast no-API/no-network corpus-data checks above. Run it on demand:
#   ./venv/bin/python -m pytest tests/test_review_server.py -v
#
# review.html/build_review_html.py were retired 2026-08-07 in favor of
# review_server.py + review_frontend/ (a live local server, not a
# regenerated static file) - see PROJECT-STATUS.md "Review dashboard
# rearchitecture". Run it with `python3 pipeline/review_server.py`.
#
# Root reorganized 2026-08-16 into pipeline/ (the scripts this file calls,
# plus the live review tool) and tools/ (everything run manually/
# standalone - validators, lexicon/abbreviation/punctuation/witness
# scripts) - see CLAUDE.md "Directory layout". This file's own stage
# scripts all live in pipeline/ now; nothing it calls moved to tools/.
#
# The vision-verification step is the only one that costs API calls, and it's
# cached in adjudication_cache.db's corrections_cache table, keyed on
# (crop_hash, word_a, word_b, context_hash, prompt_hash). Every one of those
# beyond crop_hash was added after a real bug, not as hardening:
#   - crop_hash alone (fixed 2026-08-05) silently reused decisions from
#     unrelated word comparisons that happened to share a crop.
#   - no context_hash (fixed 2026-08-10) ignored that the surrounding-sentence
#     context sent to the model is part of "the question" - see
#     PROJECT-STATUS.md "sends the wrong surrounding sentence context".
#   - no prompt_hash (fixed 2026-08-14) ignored that the PROMPT TEMPLATE is
#     too. The template was edited 2026-08-12 and that fix only landed because
#     the context_hash change had already dropped every row; the same edit
#     today would have been a silent no-op.
# With the full key, only candidates whose word pair, context OR prompt
# actually changed trigger a fresh API call; everything else is a legitimate
# cache hit. That means it's safe and cheap to run this in full every time -
# you do not need to remember which stage is "dirty."
#
# Usage: ./rebuild_all.sh [--skip-vision]
#   --skip-vision   skip the Gemini re-verification step (fast, free) and
#                    reuse whatever corrections_verified_part1.json already
#                    has on disk. Use this for quick iteration on text fixes
#                    when you don't need fresh flag classifications yet.

set -euo pipefail
cd "$(dirname "$0")"

SKIP_VISION=0
for arg in "$@"; do
  case "$arg" in
    --skip-vision) SKIP_VISION=1 ;;
    *) echo "Unknown argument: $arg" >&2; exit 1 ;;
  esac
done

echo "== 1/6 build_klalim_demo_dataset.py =="
./venv/bin/python pipeline/build_klalim_demo_dataset.py

echo "== 2/6 build_corrections_dataset.py =="
./venv/bin/python pipeline/build_corrections_dataset.py

if [ "$SKIP_VISION" = "1" ]; then
  echo "== 3/6 verify_corrections_vision.py SKIPPED (--skip-vision) =="
else
  echo "== 3/6 verify_corrections_vision.py (may call the Gemini API for new/changed word pairs) =="
  ./venv/bin/python pipeline/verify_corrections_vision.py
fi

# ADDED 2026-08-23 (code review, finding C1). Pure local computation - no API
# calls, no cost - so it belongs in the gated chain rather than being run by
# hand. It reads the witness baselines and writes consensus_disputes_part1.json,
# which stage 4 then merges. Running it HERE, before stage 4, is what makes
# multi-witness disputes a regenerated pipeline product instead of a hand-append
# into stage 4's own output that the next rebuild silently destroys.
echo "== 4a/6 synthesize_multi_witness.py =="
./venv/bin/python pipeline/synthesize_multi_witness.py

# ADDED 2026-08-26. Same argument that put 4a in this chain: pure local
# computation, ~0.1s on the full corpus, no API calls. The two lexical detectors
# were [STANDALONE] scripts that printed to stdout and wrote nothing - and the
# reviewer hand-repaired a word in klal 84 that one of them had been finding all
# along. A detector nobody runs has not detected anything.
#
# It runs BEFORE stage 4 because stage 4 MERGES its sharpest tier into the review
# queue (see merge_lexical_defects). A witness contributes a source file the
# pipeline reads; it never edits the pipeline's own product - the same rule
# finding C1 established for the multi-witness synthesizer.
echo "== 4b/6 build_lexical_defect_report.py =="
./venv/bin/python pipeline/build_lexical_defect_report.py

# 4c: the TITLE field, which no stage read at all until 2026-09-03.
#
# Item 39: every detector, witness, validator and invariant in this repo read
# `clean_text`, so `title` - which is corpus text under the single-source-of-
# truth rule - had never been checked by anything. Six OCR errors were sitting
# in headings whose bodies were already correct, found only because a reviewer
# read one. This stage runs the prefix check (a title must be a prefix of its
# own body) and the 4b detectors over `--field title`, and writes
# title_defect_report.json.
#
# Same discipline as 4b: it writes a triage report and never a flag. Two of the
# three candidates its first run produced are words the body spells identically
# and spells correctly.
echo "== 4c/6 build_title_report.py =="
./venv/bin/python pipeline/build_title_report.py

# 4d: the ONLY stage whose output is deliberately not actionable.
#
# Dicta reads a DIFFERENT PRINTING (Jerusalem 1975/6) than every other witness,
# so its disagreements are not all misreads - some are real differences between
# the two editions. This stage reports the subset that is verifiable by shape
# (Berlin abbreviates with a geresh, Jerusalem spells the same word out) into
# collation_report.json, and NOTHING downstream consumes it. Applying a row here
# would edit the Berlin text to match Jerusalem - the exact thing item 0AQ ruled
# against. It runs before stage 4 only to keep the witness stages together;
# stage 4 does not read it.
echo "== 4d/6 build_collation_report.py =="
./venv/bin/python pipeline/build_collation_report.py

echo "== 4/6 assemble_corrections_dataset.py =="
./venv/bin/python pipeline/assemble_corrections_dataset.py

echo "== 5/6 build_klal_page_regions.py =="
./venv/bin/python pipeline/build_klal_page_regions.py

# 5b: the two STANDALONE corpus reports, folded into the chain 2026-08-31.
#
# WHY THEY ARE HERE NOW. Both read the corpus and write a JSON report, and
# neither was in any chain - so each kept whatever numbers it had from the last
# time somebody remembered to run it. Measured that day: `ligature_words.json`
# still claimed `both_lost: 3` when two of those three ampersands had been
# repaired to `אל` and only klal 77 w11 survived. Nothing was wrong with either
# tool; the reports had simply aged out of agreement with the text they describe,
# silently, and a stale count in a report is the kind of number that ends up
# quoted in a status entry as if it were measured today.
#
# This is Lesson 32 in its milder form - not a detector nobody runs, but a report
# nobody re-runs - and Lesson 13's shape besides: a file fully computable from the
# corpus is a second copy of the truth until something rebuilds it. Together they
# cost ~0.5s on the full corpus, which is why the reason for leaving them out
# never really existed.
#
# Both are pure readers: they write only their own report and never a flag, a
# decision or corpus text. review_lexicon_only_words.py needs the gitignored
# sefaria_reference_corpus cache and exits 0 with an explicit message when it is
# absent, so a fresh clone is not broken by this stage.
echo "== 5b/6 standalone corpus reports (ligature + lexicon-only) =="
./venv/bin/python tools/list_ligature_words.py
./venv/bin/python tools/review_lexicon_only_words.py

echo "== 6/6 tests/ (corpus + pipeline-logic regression suites) =="
./venv/bin/python -m pytest tests/test_corpus_invariants.py tests/test_pipeline_logic.py -q

echo "== done =="
