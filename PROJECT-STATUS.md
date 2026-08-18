# Project Status — Open Items & Investigation Log

**This file holds the current, live state only** — what's fixed, what's
open, what to do next — and is kept short enough to read in full every
session, per CLAUDE.md's "read PROJECT-STATUS.md at the start of every
session, no exceptions." **Split 2026-08-12**, then **re-split 2026-08-18**
after 65 dated entries had re-accumulated here over the following six days
(5,102 lines — past the point a single `Read` call can load, the exact
problem the 2026-08-12 split was meant to prevent). All of that detailed
dated log, byte-identical, nothing deleted or rewritten, now lives at the
top of `PROJECT-STATUS-HISTORY.md` (newest-first, so it sits right after
that file's own header). Read that file for the evidence trail behind any
specific finding referenced here, or when grepping for how a past issue
was resolved. **New dated entries with detailed fix/verification prose go
there, not here** — prepend them right after `PROJECT-STATUS-HISTORY.md`'s
header. **This file should only ever hold a compact current summary,
re-written (not just appended to) as state changes** — that discipline is
what drifted last time; don't let dated entries pile up here again.

## Open items

1. **Parts 2-3 findings aren't visible anywhere actionable.** 1,350+
   textual-signal `klal_flag` decisions are recorded for Parts 2-3, and
   thousands of lexicon-gap candidates (`unresolved`/`weakly_attested`
   buckets) remain untriaged — but `pipeline/review_server.py` only ever
   loads `part1.json`, so none of it shows up in the dashboard. Extending
   the dashboard to Parts 2-3 is a real, standing gap, not done.
2. **Parts 2-3 corrections are investigated but not applied — correctly,
   by design.** Scan-linkage/verification infrastructure (extraction,
   marker/trace-building, vision-adjudication) is built and has been run
   over the full page range; real data issues have been found and
   confirmed by direct scan-crop verification. Per the standing Parts 2-3
   gate (see CLAUDE.md/`START_HERE.md`), no actual `part2.json`/
   `part3.json` edit has been applied yet — needs its own explicit
   go-ahead, same two-step principle as the rest of this pipeline.
3. **The witness queue is still open**: ~411 items across klal 30/75/88,
   the only real second opinion on ~3,800 reconstructed words. The machine
   vision pass is done; the human review-in-dashboard pass was explicitly
   deferred by the user as a future step (not forgotten, not a gate on
   anything else).
4. **DocAI extraction has no live home.** The capability only exists in
   `archive/scripts/extend_docai_ocr.py` (an "already-applied one-off" by
   this project's own classification), reused anyway whenever Parts 2-3
   extraction work has needed it. Worth promoting into a proper
   `pipeline/`/`tools/` script.

## Recent work (2026-08-18)

Full detail for all of this is in `PROJECT-STATUS-HISTORY.md`'s newest
entries (prepended today, same date). Headlines only:

- Repo migrated to a second machine and pushed to GitHub
  (`esafern/sefer-digitization-pipeline`, public); `requirements.txt`,
  `pytest.ini`, `direnv` auto-activation, and `tools/verify_local_setup.py`
  added to make setup actually reproducible and verifiable.
- `CLAUDE.md` split into `START_HERE.md` (Human/LLM parts) + a short
  redirect stub + `DOCS-HISTORY.md` (this document's own correction
  history).
- Berlin scan's printing date corrected to a primary-source-confirmed
  1851/2 CE (was a secondhand "~1857/8" estimate); the actual Google Books
  URL and NLI catalog record for the scan both found and verified; NLI
  validated as a genuine alternative source but NOT adopted (even its best
  anonymous tier is ~4x fewer pixels than the Google-sourced PDF this
  pipeline actually uses).
- `images/pdf_pages/` migration gap found and fixed (was breaking the
  dashboard's scan pane on the new machine); `tools/fix_transposed_leaf.py`
  added and verified two independent ways.
- A `.gitignore` anchoring bug fixed (two PDF exceptions were un-ignoring
  same-named files anywhere in the tree, not just at root).

## Everything before today

See `PROJECT-STATUS-HISTORY.md` — 65 dated entries from 2026-08-14 through
2026-08-17 covering the Part 1 correction/review work, the Parts 2-3
infrastructure build-out, multiple independent code-review/refactor
passes, and the lexicon/reference-corpus work behind items 1 and 4 above.
