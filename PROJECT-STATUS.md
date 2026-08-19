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

**The witness queue is also 91% smaller than it looks.** Tesseract was right in
16 of 419 disagreements (3.8%). Filtering on the vision verdict — not the tier
— cuts it to 37 items with no findings lost. Open item 4.

**Dicta OCR is queued up as a real replacement witness**, with an adjudicated
15-klal test set already prepared. Open item 5, detail in `dicta_eval/`.

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
4. **The witness queue should be filtered by vision verdict, not worked in
   full — and not pruned by tier.** Analysed 2026-08-19 (full detail and
   tables in `PROJECT-STATUS-HISTORY.md`). Tesseract was right in only **16 of
   419** disagreements (3.8%) vs. DocAI's 91.2%; it fails structurally, being a
   weaker engine on the *same* scan rather than an independent signal. Deleting
   tier D was considered and **rejected**: D holds the most findings in
   absolute terms (13 of 37) and **7 of the 8 human decisions already recorded
   sit in it**. The right cut is `vision_selected in ("B","NEITHER")` — **419 →
   37 items, 91% less work, zero findings lost.** Not implemented: the queue
   file is derived, so filtering belongs in
   `tools/verify_reconstruction_witness.py` or a separate view, never a
   hand-edit. Caveat: all 419 verdicts came back ≥0.9 confidence, so treat the
   37 as a priority queue, not proof the other 382 are clean (Lesson 2).
5. **Dicta OCR evaluation is set up and blocked on manual upload.** See
   `dicta_eval/README.md`. `yad-malachi-berlin-sample.pdf` (3 pages, 1.0 MB) =
   source pages 18–20 = klalim 8–22, confirmed by MD5 image match plus exact
   agreement across the trace, alignment and page-region files. Ground truth
   (2,356 words, 23 candidates, 11 open, 9 human decisions) is
   `dicta_eval/groundtruth_klal_8_22.txt`. Browser automation against
   `ocr.dicta.org.il` failed ~7 times across two Chrome restarts and was
   abandoned; the upload is a minute of manual work. The prize if Dicta wins on
   square type is running it over the **Rashi-script Livorno first edition**,
   which nothing has successfully OCR'd — a second edition *and* a second
   engine, which is the independent signal Tesseract never was.
6. **The public-domain citation tier is only partly itemized.**
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
  corrected. Both sources were deleted in the same commit; neither was ever
  git-tracked, so they are not recoverable from history — everything of
  substance in them is in the merged doc.
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
- **`VERIFIED-AGAINST-THE-INK.html` stat ledger refreshed** — two `127`
  references corrected to `125`, and its Parts 2–3 row rewritten: it read
  "alignment built, adjudication not started," which stopped being true once
  the Parts 2–3 infrastructure was built and run. Now states 916 klalim
  flagged, 0 applied.
- **Cross-reference sweep run over every doc.** All file references in the
  live docs resolve. The only unresolved ones are in
  `PROJECT-STATUS-HISTORY.md` and `DOCS-HISTORY.md` and are correct as-is:
  deliberately-archived scripts, `/tmp` scratch paths, and glob-style names
  (`page_N.json`, `part1/2/3.json`) that were never literal filenames.

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
