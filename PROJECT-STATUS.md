# Project Status — Open Items & Investigation Log

## TL;DR

**Part 1 is nearly closed.** 222/222 klalim have a trusted page-to-klal
alignment. 387 word-level correction candidates exist across 149 klalim: 237
machine-resolved, 25 human-decided, **125 still open** — and 91 of those 125
already carry a vision verdict (90 at ≥0.9 confidence). The remaining gate is
outside human confirmation, not more machine work.

**Parts 2–3 are built but invisible and unapplied.** The infrastructure ran
over their full page range and found real issues — **916 klalim carry an open
review flag** — but `review_server.py` only loads `part1.json`, so none of it
is reviewable in the dashboard, and no `part2.json`/`part3.json` edit has been
applied. Both of those are deliberate states, and both are open item 1 and 2
below.

**The witness queue is parked, on purpose.** 419 flagged items across klal
30/75/88; 8 decided, **411 open**. Machine pass done, human pass explicitly
deferred by the user. Not a gate on anything else.

**Three things to know if you're picking this up cold:** read this file before
making any claim about corpus quality; the Parts 2-3 gate in `START_HERE.md`
is binding; and every finding you confirm gets written here immediately, not
mentioned in chat.

---

**This file holds the current, live state only** — what's fixed, what's open,
what to do next — kept short enough to read in full every session, per
`START_HERE.md`'s "read `PROJECT-STATUS.md` first, every session, no
exceptions." **Split 2026-08-12**, then **re-split 2026-08-18** after 65 dated
entries had re-accumulated here over the following six days (5,102 lines —
past the point a single `Read` call can load, the exact problem the 2026-08-12
split was meant to prevent). All of that detailed dated log, byte-identical,
nothing deleted or rewritten, now lives at the top of
`PROJECT-STATUS-HISTORY.md` (newest-first). Read that file for the evidence
trail behind any specific finding referenced here.

**New dated entries with detailed fix/verification prose go there, not here** —
prepend them right after `PROJECT-STATUS-HISTORY.md`'s header. **This file
should only ever hold a compact current summary, re-written (not just appended
to) as state changes** — that discipline is what drifted last time.

## Open items

1. **Parts 2–3 findings aren't visible anywhere actionable.** 916 klalim in
   Parts 2–3 currently carry a `needs_revisit` flag (out of 1,502 flag records
   written there, from 2,088 append-only decisions), and thousands of
   lexicon-gap candidates (`unresolved`/`weakly_attested` buckets) remain
   untriaged — but `pipeline/review_server.py` only ever loads `part1.json`,
   so none of it shows up in the dashboard. Extending the dashboard to Parts
   2–3 is a real, standing gap, not done.
2. **Parts 2–3 corrections are investigated but not applied — correctly, by
   design.** Scan-linkage/verification infrastructure (extraction,
   marker/trace-building, vision-adjudication) is built and has been run over
   the full page range; real data issues have been found and confirmed by
   direct scan-crop verification. Per the standing Parts 2-3 gate (see
   `START_HERE.md`), no actual `part2.json`/`part3.json` edit has been applied
   yet — needs its own explicit go-ahead, same two-step principle as the rest
   of this pipeline.
3. **The witness queue is still open**: 419 items across klal 30/75/88 (160 /
   119 / 140), of which 8 are decided and **411 remain** — the only real
   second opinion (DocAI vs. Tesseract) on those three page-crossing
   reconstructions, covering 2,673 DocAI words at 0.76–0.86 agreement. The
   machine vision pass is done; the human review-in-dashboard pass was
   explicitly deferred by the user as a future step (not forgotten, not a gate
   on anything else).
4. **The public-domain citation tier is only partly itemized.**
   `CORPUS-COMPARISON.md` gives the tier totals (21 works / 939 citations) and
   per-work counts *only* for works its wider sweep newly surfaced. The 15
   already-known public-domain works are counted in the totals but never
   listed individually — and arithmetic shows they average ~40 citations each,
   so the tier's #2–#5 are genuinely unknown. `CASE-YAD-MALACHI.md`'s
   public-domain table states this limit explicitly rather than implying a
   ranking. Closing it means re-running the underlying Halachipedia survey,
   whose raw output is not in this repo. Found 2026-08-19.

## Recent work (2026-08-19)

- **Documentation pass across every `.md` at root**, plus
  `VERIFIED-AGAINST-THE-INK.html`'s stat ledger. TL;DR sections added to each
  doc; stale facts corrected against live data (open-candidate count 127 →
  125; test count 199 → 236; Parts 2–3 described as "adjudication not started"
  when the infrastructure has in fact been built and run); seven stale
  `CLAUDE.md` cross-references in `PIPELINE-DATA-REFERENCE.md` and two in this
  file repointed to `START_HERE.md` after the 2026-08-18 split;
  `CASE-YAD-MALACHI.md` gained a public-domain-tier citation table (and open
  item 4 above, which writing it surfaced); `competition.md` + `more
  competition.md` merged into `COMPETITIVE-LANDSCAPE.md` with their
  contradictions resolved and their inaccurate claims about this pipeline
  corrected.
- **Undocumented `tools/` scripts added to `START_HERE.md`'s directory
  layout** — `export_corpus.py`, `build_part1_freq.py`,
  `detect_cross_klal_errors.py`, `detect_insertion_deletion.py`,
  `detect_repeated_words.py`, `detect_split_merge.py`,
  `patch_witness_word_indices.py`, plus `pipeline/build_gematria_trace.py`,
  were all live but missing from the map. Same defect class as the
  2026-08-14/16 directory-layout drift recorded in `DOCS-HISTORY.md`.
- **`PIPELINE-DATA-REFERENCE.md` gained the files it was missing** —
  `reconstruction_witness_queue.json` (which `review_server.py` loads),
  `lexicon.txt`, and the four sqlite decision caches.

## Recent work (2026-08-18)

Full detail in `PROJECT-STATUS-HISTORY.md`'s newest entries. Headlines only:

- Repo migrated to a second machine and pushed to GitHub
  (`esafern/sefer-digitization-pipeline`, public); `requirements.txt`,
  `pytest.ini`, `direnv` auto-activation, and `tools/verify_local_setup.py`
  added to make setup reproducible and verifiable.
- `CLAUDE.md` split into `START_HERE.md` (Human/LLM parts) + a short redirect
  stub + `DOCS-HISTORY.md`.
- Berlin scan's printing date corrected to a primary-source-confirmed 1851/2
  CE (was a secondhand "~1857/8" estimate); the Google Books URL and NLI
  catalog record for the scan both found and verified; NLI validated as a
  genuine alternative source but NOT adopted (even its best anonymous tier is
  ~4x fewer pixels than the Google-sourced PDF this pipeline uses).
- `images/pdf_pages/` migration gap found and fixed (was breaking the
  dashboard's scan pane on the new machine); `tools/fix_transposed_leaf.py`
  added and verified two independent ways.
- A `.gitignore` anchoring bug fixed (two PDF exceptions were un-ignoring
  same-named files anywhere in the tree, not just at root).
- This file itself re-split back down from 5,102 lines.
- DocAI extraction promoted from `archive/scripts/extend_docai_ocr.py` to
  `tools/extract_docai_pages.py`: now goes through `corpus_io.py` for paths,
  defaults to the current `berlin_square_corrected.pdf`, and takes
  `--project-id`/`--location`/`--processor-id` overrides instead of hardcoded
  constants, for reuse on a different digitization work.

## Everything before that

See `PROJECT-STATUS-HISTORY.md` — 65 dated entries from 2026-08-14 through
2026-08-17 covering the Part 1 correction/review work, the Parts 2–3
infrastructure build-out, multiple independent code-review/refactor passes,
and the lexicon/reference-corpus work behind open item 1 above.
