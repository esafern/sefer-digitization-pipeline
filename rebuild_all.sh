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
#     -> pytest tests/                 -> pass/fail gate (regression suite)
#
# review.html/build_review_html.py were retired 2026-08-07 in favor of
# review_server.py + review_frontend/ (a live local server, not a
# regenerated static file) - see PROJECT-STATUS.md "Review dashboard
# rearchitecture". Run it with `python3 review_server.py`.
#
# The vision-verification step is the only one that costs API calls, and it's
# cached in adjudication_cache.db's corrections_cache table, keyed on
# (crop_hash, word_a, word_b) - not crop_hash alone (that was a real bug, see
# PROJECT-STATUS.md 2026-08-05: it silently reused decisions from unrelated
# word comparisons that happened to share a crop). With the fixed key, only
# candidates whose word pair actually changed trigger a fresh API call;
# everything else is a legitimate cache hit. That means it's safe and cheap
# to run this in full every time - you do not need to remember which stage
# is "dirty."
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
./venv/bin/python build_klalim_demo_dataset.py

echo "== 2/6 build_corrections_dataset.py =="
./venv/bin/python build_corrections_dataset.py

if [ "$SKIP_VISION" = "1" ]; then
  echo "== 3/6 verify_corrections_vision.py SKIPPED (--skip-vision) =="
else
  echo "== 3/6 verify_corrections_vision.py (may call the Gemini API for new/changed word pairs) =="
  ./venv/bin/python verify_corrections_vision.py
fi

echo "== 4/6 assemble_corrections_dataset.py =="
./venv/bin/python assemble_corrections_dataset.py

echo "== 5/6 build_klal_page_regions.py =="
./venv/bin/python build_klal_page_regions.py

echo "== 6/6 tests/ (corpus regression suite) =="
./venv/bin/python -m pytest tests/ -q

echo "== done =="
