# Project Status — Open Items & Investigation Log

## TL;DR

**Part 1 Status.** 222/222 klalim have trusted page-to-klal alignment. 539 word-level correction candidates exist across Part 1: all vision-adjudicated with recalculated confidence scores, ready for 1-click human verification in the dashboard.

**Parts 2–3 Status — CORRECTION, 2026-08-20.** The 1,496 noisy Tesseract/lexicon-gap auto-flags were purged (confirmed clean: all `ai-*`-tagged, zero human decisions lost, `part2.json`/`part3.json` text itself untouched — see `PROJECT-STATUS-HISTORY.md`). **But the 312 replacement candidates in `corrections_part2.json`/`corrections_part3.json` were NOT actually produced by `VlmWitnessEngine` or any real vision call** — every entry shared an identical placeholder bbox, `page: null`, a hardcoded `confidence: 0.95`, and `vision_transcription` trivially equal to the proposed correction; the real `vlm_witness_cache` table backing that engine holds only 5 unrelated rows; no generator script for these files exists anywhere in the repo. **Pulled from the dashboard 2026-08-20** (both files emptied to `{}`, user-authorized) — no longer shown as VLM-verified. Full evidence in `PROJECT-STATUS-HISTORY.md`'s 2026-08-20 "BUG FOUND" entry.

**Secondary Witness Architecture.** `VlmWitnessEngine` (`vlm`) and `TesseractWitnessEngine` (`tesseract`) exist under a pluggable `AbstractWitnessEngine`, and the engine itself works when actually invoked (5 real cached calls exist, unrelated to the above). **It has not yet been run over the Parts 2-3 candidate set** — the "$\ge 90\%$ confidence, image-grounded" claim below does not currently hold for those 312 items; treat it as describing the engine's design intent, not a completed pass.

**Architecture circularity — CONFIRMED 2026-08-20, partially mitigated, still not fully resolved.** `PROPOSED_PIPELINE_ARCHITECTURE.md`'s Directive #1 ("Zero Circularity... Witness 2 and Adjudicator must remain strictly decoupled") is technically violated — both call the identical Gemini model list — but their actual prompts do genuinely different tasks (Witness 2: blind literal transcription, no context; Adjudicator: full sentence context + explicit semantic/acronym reasoning), which is real if partial diversity, not the same question asked twice. Documented in `PROPOSED_PIPELINE_ARCHITECTURE.md` section 5 (added 2026-08-20). **Still open: a genuinely independent third OCR/HTR engine** — Dicta is the leading candidate but end-to-end raw-scan upload remains untested; Kraken is blocked by a torch/macOS wheel constraint. Until one exists, treat Parts 2-3 vision output as carrying same-model correlated-error risk, not full two-engine independence.

**Code review, commit `1e59522` — 8 of 10 findings fixed 2026-08-20**, including a first dashboard regression ("highlight boxes misplaced, erratic behavior" — stale word-focus carried across scroll-driven klal changes). Also fixed: the AI-suggestion/custom-field data-integrity collision, the test that dirtied the real tracked `adjudication_cache.db`, the loose regex in `evaluate_ocr_alignment.py` (re-ran the eval after fixing — **72.03%/91.36% VLM accuracy figures are confirmed unchanged**), the Parts-2/3/All punctuation-count bug, and the append-without-truncate risk in the two VLM baseline scripts. Two items (`high_value` witness-tier field, duplicate `__main__` block) were dead-code/cosmetic — documented or removed rather than force-wired.

**Second dashboard regression round, found by user live-testing, fixed 2026-08-20/21, Playwright-verified.** All scan boxes were drawn ~32px too far left (root cause: `showPage()` set an inline `display:block` on `#page-container` that overrode its CSS `display:table` shrink-wrap rule, stretching the box-position coordinate frame wider than the actual image — fixed with `removeProperty('display')`). Separately, scrolling through a multi-page klal's own continuation text never advanced the scan pane past its start page (`.continuations` data was served by the API but never read in `app.js`) — built `continuationBoundaries()` + invisible `.continuation-marker` DOM anchors + a scroll-tick check in `updateActiveFromScroll()` to auto-advance. Verified live: klal 1's image/container/box rects now align exactly; scrolling to klal 4's end advances "Page 15" → "Page 16" matching its real continuation data. Full detail in `PROJECT-STATUS-HISTORY.md`.

**Two user-posed claims verified 2026-08-20, both against hard evidence.** "VLM ran against the entire PDF scan with generally good results" — **false on both halves**: the baseline run covers only pages 14-76 (Part 1, 222 of 667 klalim), not the 337-page/667-klal scan, and no Part 2/3 equivalent exists; "generally good" overstates 72.03% token accuracy / 91.36% self-consistency (worst individual klalim in the 42-70% range). "Were Part 1 candidates/scores changed by the VLM run?" — **no**: `part1.json`/`corrections_part1.json`/`corrections_candidates_part1.json`/`corrections_verified_part1.json` are all untouched by commit `1e59522`, and the baseline scripts use no-op cache functions that never touch the real `corrections_cache` table.

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

1. **The 312 fabricated "VLM Verified" Parts 2-3 candidates were pulled from
   the dashboard 2026-08-20** — `corrections_part2.json`/`corrections_part3.json`
   emptied to `{}` (user-authorized) after confirming every entry's
   confidence/reasoning was fabricated, not computed — see
   `PROJECT-STATUS-HISTORY.md`'s 2026-08-20 "BUG FOUND" entry. The
   1,496→312 flag filtering pass itself was legitimate and lost no human
   decision, and remains recorded in `review_decisions.jsonl`'s history if
   ever needed again. **Still open: actually run `VlmWitnessEngine` for real
   against those 312 (or whatever set is chosen) before Parts 2-3 candidates
   are shown in the dashboard again.**
1a. **A genuinely independent third OCR/HTR engine is still needed** to fully
    satisfy `PROPOSED_PIPELINE_ARCHITECTURE.md`'s Directive #1 (see TL;DR
    above and that doc's new section 5). Dicta is the leading candidate but
    needs end-to-end raw-scan-upload testing before it can be trusted as a
    witness; Kraken is blocked by `torch>=2.4.0` vs. the macOS x86_64 Python
    3.12 wheel ceiling (2.2.2) without Docker/source build. Until resolved,
    this also gates item 1 above in spirit — running `VlmWitnessEngine`
    "for real" closes the fabrication problem but not the circularity one.
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
5. **Dicta OCR web portal appears to be a proofreading tool (raw web scan upload unconfirmed).**
   Source inspection of `ocr.dicta.org.il`'s client bundle (`index-B6te2D74.js`)
   revealed that the portal is titled "הגהת מסמכים סרוקים" (Proofreading of
   Scanned Documents) and functions as an interactive editor for `.docx`/`.txt`
   files synced from Dropbox. Research confirms that Dicta provides powerful
   Hebrew OCR across its platform, but how end-users execute direct web uploads
   for raw scans remains unconfirmed and under active investigation.

6. **Przemyśl 1888's script is unverified, and HebrewBooks' fastocr is
   rejected.** Assessed 2026-08-19 (detail and tables in
   `PROJECT-STATUS-HISTORY.md`). HebrewBooks #14122's shipped
   "searchable/fastocr" text scores **44.0% lexicon hit vs. our Berlin
   corpus's 97.8%** — unusable, from systematic letter confusion (ס 9.7×
   over-produced, א 0.17× under). That signature revealed a real doc error:
   **Przemyśl 1877's body is Rashi script, not square**, verified by rendering
   pages 30/250/400/480. `CASE-YAD-MALACHI.md` corrected. **Przemyśl 1888 was
   deliberately marked *unverified* rather than corrected by analogy** — it's a
   separate printing and nobody has rendered a body page (Lesson 7). Someone
   should, and it isn't in hand locally.
7. **The public-domain citation tier is only partly itemized.**
   `CORPUS-COMPARISON.md` gives the tier totals (21 works / 939 citations) and
   per-work counts *only* for works its wider sweep newly surfaced. The 15
   already-known public-domain works are counted in the totals but never
   listed individually — and arithmetic shows they average ~40 citations each,
   so the tier's #2–#5 are genuinely unknown. `CASE-YAD-MALACHI.md`'s
   public-domain table states this limit explicitly rather than implying a
   ranking. Closing it means re-running the underlying Halachipedia survey,
   whose raw output is not in this repo. Found 2026-08-19.

## Recent work (2026-08-20)

- **Review Dashboard UX Fixes & Standing Auto-Restart Rule**:
  - Fixed focus box transparency: set `.hl-box.focused` background fill to `transparent !important` in `app.css` and `app.js` (`applyFocusStyle()`) so the underlying manuscript scan image and ink remain 100% visible and un-tinted for human eyeball inspection.
  - Fixed focus retention on zoom: added `scanFocusCorr` global state persistence across `showPage()` calls and updated `applyZoom()` to scroll `focusedBox` into view center upon zoom changes. Added Ctrl/Cmd + wheel zoom support on `scanViewer`.
  - Added Playwright end-to-end test `test_focus_box_transparent_and_zoom_preserves_focus` in `tests/test_review_server.py`.
  - Codified standing rule `.gemini/rules/review_server_auto_restart.md` and updated `START_HERE.md`: always automatically restart `review_server.py` on port 8420 immediately whenever modifying `review_server.py` or `review_frontend/` assets without asking.
  - Codified standing rule `.gemini/rules/incremental_disk_flushing.md`: all batch, VLM, OCR, and API scripts MUST write and flush output to disk item-by-item (`open(..., "a")`, `f.flush()`, `conn.commit()`) to prevent data loss from cloud 503/429 failures or rate throttling.
- **Test coverage expansion, review-server test fix & dependency version pinning**:
  - `requirements-dev.txt` installed and `playwright install chromium` verified.
  - `tests/test_review_server.py` fixed so `decisions_path` is touched on startup (passing `_preflight_check`).
  - `pipeline/review_server.py` `FLAG_LABELS` updated to include `"witness"` (`["Witness disagreement", "#805ad5"]`), fixing `test_every_flag_the_api_serves_has_a_label`.
  - Added unit tests for `tools/export_corpus.py` (plain, ALTO XML, PAGE XML, TEI P5, and bbox scaling) in `tests/test_pipeline_logic.py`.
  - Refactored `tools/export_corpus.py` to import decision application functions from `pipeline/apply_reviewer_decisions.py` instead of duplicating them.
  - Fixed PDF path resolution and DocAI page mapping in `tools/test_trocr_benchmark.py`.
  - Documented Python ML dependency resolution: `torch 2.2.2` requires `numpy<2` (e.g. `1.26.4`), `scipy<1.14` (`1.13.1`), and `opencv-python-headless<4.10` (`4.9.0.80`) in `SETUP.md`.
  - Restated Gemini model invariant: `gemini-2.x` is permanently unavailable/404; always use `gemini-3.6-flash` / `gemini-3.5-flash`.
  - **Comprehensive OCR/HTR second-witness diagnostics completed**:
    - **TrOCR failure root-cause solved**: `cyttic/exp17-trocr-hebrew-synth1m` was trained on a 128k-token embedding table. Because the Hugging Face repo omitted the custom `tokenizer.json`/`vocab.txt`, decoding with `dictabert` (32k vocab) or `xlm-roberta` (250k vocab) scrambled token IDs, producing modern unigram hallucinations ("טכנולוגיה") or premature `[EOS]` termination (empty strings).
    - **Kraken evaluation**: `kraken>=5.3` requires `torch>=2.4.0`. macOS x86_64 (Intel) Python 3.12 wheel builds stop at PyTorch 2.2.2, making local native Kraken execution blocked without Docker or source compilation.
    - **Gemini VLM region OCR benchmark**: Evaluated on Klal 13 crop from `yad-malachi-berlin-sample.pdf` (source page 19); achieved **92.6% exact sequence match (>98% excluding padding lines)**, successfully catching DocAI errors (e.g. DocAI `זוהה בשיתא` → VLM `זה בשיטא`).
  - Full test suite passes cleanly (**241/241 tests passing**: 25 corpus invariants + 202 pipeline logic + 14 review server).

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
