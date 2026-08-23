# Project Status — Open Items & Investigation Log

## TL;DR

**Part 1 Status.** 222/222 klalim have trusted page-to-klal alignment. 539 word-level correction candidates exist across Part 1: all vision-adjudicated with recalculated confidence scores, ready for 1-click human verification in the dashboard.

**Parts 2–3 Status — CORRECTION, 2026-08-20.** The 1,496 noisy Tesseract/lexicon-gap auto-flags were purged (confirmed clean: all `ai-*`-tagged, zero human decisions lost, `part2.json`/`part3.json` text itself untouched — see `PROJECT-STATUS-HISTORY.md`). **But the 312 replacement candidates in `corrections_part2.json`/`corrections_part3.json` were NOT actually produced by `VlmWitnessEngine` or any real vision call** — every entry shared an identical placeholder bbox, `page: null`, a hardcoded `confidence: 0.95`, and `vision_transcription` trivially equal to the proposed correction; the real `vlm_witness_cache` table backing that engine holds only 5 unrelated rows; no generator script for these files exists anywhere in the repo. **Pulled from the dashboard 2026-08-20** (both files emptied to `{}`, user-authorized) — no longer shown as VLM-verified. Full evidence in `PROJECT-STATUS-HISTORY.md`'s 2026-08-20 "BUG FOUND" entry.

**Secondary Witness Architecture.** `VlmWitnessEngine` (`vlm`) and `TesseractWitnessEngine` (`tesseract`) exist under a pluggable `AbstractWitnessEngine`, and the engine itself works when actually invoked (5 real cached calls exist, unrelated to the above). **It has not yet been run over the Parts 2-3 candidate set** — the "$\ge 90\%$ confidence, image-grounded" claim below does not currently hold for those 312 items; treat it as describing the engine's design intent, not a completed pass.

**Architecture circularity — CONFIRMED 2026-08-20, partially mitigated, still not fully resolved.** `PROPOSED_PIPELINE_ARCHITECTURE.md`'s Directive #1 ("Zero Circularity... Witness 2 and Adjudicator must remain strictly decoupled") is technically violated — both call the identical Gemini model list — but their actual prompts do genuinely different tasks (Witness 2: blind literal transcription, no context; Adjudicator: full sentence context + explicit semantic/acronym reasoning), which is real if partial diversity, not the same question asked twice. Documented in `PROPOSED_PIPELINE_ARCHITECTURE.md` section 5 (added 2026-08-20). **Still open: a genuinely independent third OCR/HTR engine** — Dicta is the leading candidate but end-to-end raw-scan upload remains untested; Kraken is blocked by a torch/macOS wheel constraint. Until one exists, treat Parts 2-3 vision output as carrying same-model correlated-error risk, not full two-engine independence.

**Code review, commit `1e59522` — 8 of 10 findings fixed 2026-08-20**, including a first dashboard regression ("highlight boxes misplaced, erratic behavior" — stale word-focus carried across scroll-driven klal changes). Also fixed: the AI-suggestion/custom-field data-integrity collision, the test that dirtied the real tracked `adjudication_cache.db`, the loose regex in `evaluate_ocr_alignment.py` (re-ran the eval after fixing — **72.03%/91.36% VLM accuracy figures are confirmed unchanged**), the Parts-2/3/All punctuation-count bug, and the append-without-truncate risk in the two VLM baseline scripts. Two items (`high_value` witness-tier field, duplicate `__main__` block) were dead-code/cosmetic — documented or removed rather than force-wired.

**Second dashboard regression round, found by user live-testing, fixed 2026-08-20/21, Playwright-verified.** All scan boxes were drawn ~32px too far left (root cause: `showPage()` set an inline `display:block` on `#page-container` that overrode its CSS `display:table` shrink-wrap rule, stretching the box-position coordinate frame wider than the actual image — fixed with `removeProperty('display')`). Separately, scrolling through a multi-page klal's own continuation text never advanced the scan pane past its start page (`.continuations` data was served by the API but never read in `app.js`) — built `continuationBoundaries()` + invisible `.continuation-marker` DOM anchors + a scroll-tick check in `updateActiveFromScroll()` to auto-advance. Verified live: klal 1's image/container/box rects now align exactly; scrolling to klal 4's end advances "Page 15" → "Page 16" matching its real continuation data. Full detail in `PROJECT-STATUS-HISTORY.md`.

**Two user-posed claims verified 2026-08-20, both against hard evidence.** "VLM ran against the entire PDF scan with generally good results" — **false on both halves**: the baseline run covers only pages 14-76 (Part 1, 222 of 667 klalim), not the 337-page/667-klal scan, and no Part 2/3 equivalent exists; "generally good" overstates 72.03% token accuracy / 91.36% self-consistency (worst individual klalim in the 42-70% range). "Were Part 1 candidates/scores changed by the VLM run?" — **no**: `part1.json`/`corrections_part1.json`/`corrections_candidates_part1.json`/`corrections_verified_part1.json` are all untouched by commit `1e59522`, and the baseline scripts use no-op cache functions that never touch the real `corrections_cache` table.

**Dashboard data was rebuilt 2026-08-23 and is trustworthy again.** `corrections_part1.json` went **1,647 items -> 656** (539 real pipeline candidates + 117 multi-witness consensus disputes). The 1,108 hand-injected items with fabricated `docai_reading` are gone, replaced by 215 genuine two-engine disputes produced by a real pipeline stage (`synthesize_multi_witness.py`, stage 4a of `rebuild_all.sh`) that a rebuild regenerates instead of destroying. C1-C4 and C15 fixed; 274 tests green. **Still open: the plan document's own independence proof is empirically false** — see open item 10.

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
8. **42 of Part 1's 539 correction candidates (all `opcode: 'insert'`,
   flag `unverified_insertion`) have no bbox and so get no scan-pane
   highlight when clicked, and were excluded from tonight's VLM
   second-witness pass.** Root cause is deliberate, not a bug:
   `verify_corrections_vision.py:266-267` explicitly skips vision-cropping
   an `insert` candidate ("no bbox (insertion) - not vision-cropped") because
   these flag stored text a fresh DocAI OCR pass found no matching token
   for at all — there's no token to crop from. `api_page()` then correctly
   excludes any bbox-less correction from what it serves, so the dashboard
   currently shows no visual anchor for these 42 at all (navigates to the
   right page, nothing boxed). Possible fix, not yet built: estimate a bbox
   by interpolating from the real bboxes of the words immediately before/
   after the proposed insertion point (both already located via real DocAI
   tokens), the same band-estimate spirit already used elsewhere in this
   pipeline (`locate_word_band_fallback()`). Found 2026-08-21; awaiting a
   decision on whether to build it.

9. **CODE REVIEW 2026-08-23 of commits `f4bfe98..02e5980`: 18 findings across two
   passes. C1-C4 and C15 FIXED 2026-08-23; the rest remain open.** Full evidence trail in
   `PROJECT-STATUS-HISTORY.md`'s 2026-08-23 entry. The four that block
   further review work:
   - **C1: `corrections_part1.json` now holds 1,647 items, only 539 of them
     from the pipeline.** `tools/extract_vlm_consensus_disputes.py` (1,051)
     and `tools/extract_surya_consensus_disputes.py` (57) write directly into
     this DERIVED file; `assemble_corrections_dataset.py:220` rewrites it
     `"w"` on every `./rebuild_all.sh`. **All 1,108 injected items — and any
     human review time spent on them — are destroyed by the next rebuild.**
     Lesson 13 / the single-source-of-truth rule.
   - **C2: all 1,108 carry `docai_reading` set to the stored base text**
     (verified across every item, not sampled; 1,051 of them come from the
     dual-VLM extractor and 57 from the Surya one — the Surya run only
     *enriched* the rest with a `surya_reading` field).
     DocAI was never called for them, but the dashboard renders a "DocAI
     reading" card from that field. Same defect shape as the 312 fabricated
     Parts 2-3 candidates pulled 2026-08-20, at 3.5x scale, on Part 1.
   - **C3: VLM Pass A == Pass B is being counted as two-witness consensus.**
     It is one `gemini-3.6-flash` prompt sampled twice (87.43% measured
     self-consistency). Of the 1,012 dual-VLM items carrying a Surya reading,
     **290 have Surya siding with the stored corpus against the VLM** and 537
     have Surya reading a third thing; only 185 have real 2-engine support.
   - **C4: `disputed_choice` decisions are applied but never audited.** The
     rename wired the new type into `apply_reviewer_decisions.py` /
     `export_corpus.py` via `_match_decision_types()`, but
     `audit_applied_decisions.py`'s `CHECKERS` dict was not updated, so
     `CHECKERS.get(...)` returns `None` and every new decision is silently
     skipped by the read-only boundary check.
   Also open from that review: `SPAN_COVERAGE_BASELINE` widened to absorb
   klalim 16/22/84 with no scan verification (and klal 84 is listed as
   confirmed damage in the constant directly below it); `pipeline/typography.py`
   is dead code carrying a third, already-divergent `CONFUSION_PAIRS`;
   `get_docai_word_bboxes()` takes bboxes from non-matching `replace` opcodes
   and lets later pages overwrite earlier ones, contradicting commit
   `f23cd63`'s "100% exact bounding boxes" claim; `run_part1_vlm_patch_passB.py`
   re-violates the incremental-flush rule and no-ops its own cache; zero new
   tests for ~1,310 lines of new code.

9a. **Second review pass over the same range (`/code-review high`) reproduced
    C1/C2 and added four findings — one of which retires a claimed 2026-08-21
    feature.** Full detail in `PROJECT-STATUS-HISTORY.md`'s addendum.
    - **`build_vlm_alignment()` can never report a disagreement.** It maps only
      `SequenceMatcher.get_matching_blocks()`, and a matching block is by
      definition a run where the sequences are EQUAL — so `vlm_reading` and
      `surya_reading` are always either the corpus's own word or absent.
      Measured: 49,138 aligned VLM words and 34,892 aligned Surya words,
      **0 divergent in either**. `app.js` then dedupes the field away against
      "Current text," so it never renders. **The 2026-08-21 entry's "346
      candidates now carry a real `vlm_reading`" describes a field that
      structurally cannot disagree** — treat that enrichment as not delivered.
      Separately, the extractor's own path has written 1,154 divergent
      `surya_reading` values that the next rebuild will overwrite with the
      inert version.
    - **10 of 222 klalim have an empty Surya body**, and both consumers read
      empty as "Surya agrees" rather than "no witness" (Lesson 15).
    - The Surya extractor's Pass-B alignment (`vlm_a_to_b`) is **dead code** —
      the 57 items are gated on Surya == VLM Pass A only.
    - The bbox page fallback uses the klal's START page, and the
      neighbour-bbox recovery is gated on that same wrong page number.

9b. **H5 RESOLVED 2026-08-23, and it found real corpus damage — see item 11.**
    The `SPAN_COVERAGE_BASELINE` widening was verified: klalim 22 and 84 are
    genuine false positives (cross-page spans counting the running header as
    body tokens, because `validate_klal_span_coverage.py` does not strip page
    furniture despite its comment claiming it does — comment corrected), but
    **klal 16 is real, unfixed truncation** and has been moved to
    `SPAN_COVERAGE_KNOWN_REAL_GAPS`.

11. **RESOLVED 2026-08-23: klal 16's 23 missing words are APPLIED** (user-
    authorized, via `manual_correction` 60a17ad89fb2 through the decision
    pipeline, not a hand-edit). Klal 16 went 163 → 186 words and no longer
    appears in `validate_klal_span_coverage.py`'s flagged list; a fresh stage-2
    pass generates zero new candidates at word_index ≥ 163, so DocAI agrees
    with every inserted word. `SPAN_COVERAGE_KNOWN_REAL_GAPS` is empty again.
    **Full `./rebuild_all.sh` WITH vision completed the same day** — 537 cache
    hits, 1 live call, no quota errors (the 2026-08-21 credit exhaustion is
    resolved). Klal 16's 23 inserted words generated ZERO candidates, so there
    was nothing to adjudicate; the one live call was klal 2 w195, which Gemini
    independently confirmed at 0.99 confidence. Original finding: Its stored
    text ends mid-sentence on the connective `אהא`; the continuation is printed
    as the first two body lines of page 20 (`אף על גב דלא שייך כלל אברייתא
    דמייתי... דוק:`) and is absent from the corpus. Verified two independent
    ways (raw DocAI tokens at page 20 tokens 6-23, and a direct visual render
    of `images/pdf_pages/page_20.png`); the klal 9/10 failure mode is ruled out
    (klal 17 starts cleanly on its own marker, and `מלתייהו` appears nowhere in
    `part1.json`). Recorded as `klal_flag` decision `dcd9c031b83c` on klal 16
    word 162. Applying it needs an explicit go-ahead and a `manual_correction`
    insert through `apply_reviewer_decisions.py`, same two-step rule as every
    other correction. **Sweep DONE 2026-08-23: the other five baseline
    members (83, 106, 123, 130, 195) are all artifacts** — klal 83's shortfall
    is klal 82's tail pulled in by the klal 65/66 marker-order artifact (8 of 11
    tokens stored verbatim in klal 82, plus a page-38 render), and 106/123/130/195
    are page furniture plus single-token alignment misses whose words are all
    present in stored text. New reusable tool `tools/check_span_shortfall.py`
    answers "short of WHAT?" and is the check to run before any klal enters
    either span constant. **Klal 16 is the only real gap.** Its missing tail was
    corrected on one detail — `ראב"ע ודוק :`, not `ראב"י דוק:` — recorded as a
    SUPERSEDING klal_flag (`a31c9a08f8fe`) rather than an edit, since
    `review_decisions.jsonl` is append-only.

9c. **Still open from the 2026-08-23 review:**
    `pipeline/typography.py` is still dead code carrying a third, divergent
    `CONFUSION_PAIRS` (H6); `run_part1_vlm_patch_passB.py` still violates the
    incremental-flush rule and no-ops its own cache (H8);
    `is_gershayim_noise()`'s missing geresh case (M9) is now moot for the
    superseded extractors but the same normalisation gap should be checked in
    the repair filters when Phase 1 is built; the disputed panel still
    pre-selects the machine verdict so one Save click records it as a human
    decision (M11); 10 klalim still have no Surya coverage and need a real
    re-run rather than only being counted (C16); `match_block_to_klal`'s
    never-None nearest-region fallback (C18).

10. **`MULTI-WITNESS-REPAIR-AND-SYNTHESIS-PLAN.md` review 2026-08-23 — the
    architecture is sound, four things in it are not.** (a) **Its §2.B independence proof is now empirically refuted, not just
    theoretically doubted: one Part-1 synthesis run produced 16 instances of two
    or three engines making the IDENTICAL error, all of them the alef-lamed
    ligature dropping its `ל`** (`ושמואל`->`ושמוא`, `אליבא`->`איבא`,
    `אליהו`->`איהו`...), including unanimous 3-of-3 agreement — because the defect
    is in the ink, not the models. §2.B puts that at 3.5e-7. Under the document's
    own "2-of-3 -> Auto-Approve, 0 sec" matrix these would have REVERTED correct
    human decisions to the corrupted reading. The proof also does not hold for
    the pair the code actually used:
    VLM Pass A / Pass B are the same model, so the `1/|V|` decoupling term is
    unearned, and the term itself assumes hallucinations distribute uniformly
    over a 50k vocabulary when this document's own §1 argues OCR errors are
    systematic and glyph-driven. (b) Its **"94.5% accuracy" for the VLM is
    unsourced** — this repo's measured, verified figure is 93.34%
    (`part1_full_baseline_accuracy_report.txt`); "Surya error rate 32.4%"
    appears nowhere in the repo at all; and the "~20,300 review flags"
    figure does not reconcile with 39.3% of Part 1's 52,607 words (~20,700)
    or of the VLM's 57,614 (~22,600). Given this project's history with the
    72.03% figure, unsourced numbers in the load-bearing math section need a
    citation or removal. (c) **Phase 4 ("Run the unified 3-witness synthesis
    pipeline across Parts 2 and 3", "Export certified final text") collides
    with the binding Parts 2-3 gate** and does not mention it — synthesis
    infrastructure is authorized under the 2026-08-17 supersede, exporting
    certified Parts 2-3 text is not. (d) Its decision matrix **auto-approves
    corpus text changes with "0 sec" human review** for the 2-of-3 rows,
    which is a policy change to success criterion #1 ("resolved by looking at
    the actual scan, not inferred") and to the two-step record/apply rule —
    it needs an explicit user decision, not an engineering default. Also
    missing: any validation plan for the repair filters themselves (a wrong
    gershayim-recovery rule silently erases the disagreement it should have
    surfaced — Lesson 15), and any statement of where this plugs into
    `rebuild_all.sh`, which is the root cause of C1 above. Phase 1's
    "[x] Establish centralized typography catalog" is checked for a module
    nothing imports.

## Recent work (2026-08-21)

- **This session's OCR/witness-engine research findings written into the
  three docs that needed them**, not left only in chat/PROJECT-STATUS:
  `COMPETITIVE-LANDSCAPE.md`'s candidate-engine table, `PROPOSED_PIPELINE_
  ARCHITECTURE.md` section 5, and `tools/second_witness_eval/README.md`
  (new "2026-08-21: broader candidate sweep" section) all now carry the
  Kraken-stale-blocker correction, EasyOCR/PaddleOCR ruled-out-with-
  evidence, the Surya OCR result (exact header match, correctly tokenized
  klal 10's marker where DocAI failed), the Claude-vision live catch
  (klal 16's ט/פ misread), and the Azure AI Document Intelligence
  feasibility note - each with the same evidence already logged above,
  not restated as new claims.

- **Full pipeline rebuild completed - the insert-bbox feature, `vlm_reading`
  enrichment, and the klal 9/10 boundary fix are all now genuinely live in
  the dashboard, not just committed to intermediate files.** Ran the whole
  chain in order: `build_corrections_dataset.py` (539 candidates, klal
  count unchanged after the klal 9/10 text fix - no unexpected drift
  elsewhere) → `verify_corrections_vision.py` (all 539 vision-adjudicated,
  0 remaining `ERROR` entries - the 52 that hit the API credit exhaustion
  earlier tonight all resolved cleanly on retry) →
  `assemble_corrections_dataset.py` (539 items, 346 of them now carry a
  real `vlm_reading` value) → `build_klalim_demo_dataset.py` →
  `build_klal_page_regions.py`. The one `stale_candidate` flag seen right
  after the first assemble pass (klal 10 word 85, whose position had
  shifted from the earlier 11-word deletion) correctly disappeared once
  `build_corrections_dataset.py` regenerated fresh candidates against the
  corrected text - confirms the fix propagated cleanly through the whole
  chain, not just the one file it was applied to. **Full test suite green:
  266/266** (250 non-Playwright + 16 Playwright, review server restarted
  first so the Playwright pass exercised the fresh data). Live-verified via
  the running server: klal 9 ends "...נקט נמי בברייתא הכי :", klal 10
  starts "י איידו דאיידי . אמרינן גם ממשנה...", both correct.

- **Pass B (VLM self-consistency) completed - real, fresh figure: 87.43%
  (was the disputed/stale 91.36%, retired per this session's earlier
  integrity audit finding that the 72.03% figure paired with it in the
  same claim was false).** Both passes now fully re-run end to end with
  the fixed scripts (`response_mime_type`, dropped-continuations, and
  incremental-flush/resume fixes all applied earlier this session) - 222/222
  klalim each, genuinely comparable data on both sides for the first time.
  50,370 of 57,614 Pass-A words matched exactly in Pass B. This is a real
  drop from 91.36%, not a new problem - the OLD figure was computed from
  Pass-A/B data that both carried the same JSON-wrapping and dropped-
  continuation-page bugs Pass A's own accuracy figure did (72.03%→93.34%
  after the same fixes), so a lower, more honest self-consistency number
  on genuinely-fixed data is the expected direction, not a regression.
  20 klalim flagged with <95% agreement or a word-count mismatch (worst:
  klal 11 at 81.68%) - not investigated individually tonight, listed in
  the eval script's own output for anyone picking this up.

- **UX fix, user-requested: saving a decision now clearly confirms it landed,
  then auto-closes the panel after 2 seconds - it used to flash a small,
  easy-to-miss "Saved ✓" label and then just sit there open indefinitely.**
  Applies to the 4 panels that already shared the `.save-status` pattern
  (candidate/klal-flag/punctuation/witness) via one new shared helper,
  `flashSavedThenClose()`, rather than duplicating the "show, wait, close"
  logic 4 times. `.save-status`'s CSS changed from 12px inline text next to
  the button to a full-width green banner (`display:block`, padded,
  `#38a169` background, white bold text) held on screen for
  `DECISION_SAVED_CLOSE_DELAY_MS` (2000ms) before `dismissPanels()` fires -
  the same dismiss path the panel's own X button uses, so an auto-close
  behaves identically to a manual one (clears scan focus too, not just the
  DOM). **Real race caught and guarded before it could ever fire**: the new
  auto-close is delayed, so a reviewer who saves and then opens a
  DIFFERENT word's panel within that 2-second window could otherwise have
  the new panel yanked shut by the FIRST save's now-stale timeout - guarded
  with a `_panelGen` generation counter (same established pattern
  `showPage()`'s own `_showPageGen` already uses for the identical class of
  stale-async-completion problem), incremented on every `openPanel()` call;
  the delayed close checks the generation is still current before firing.
  **The manual-correction panel deliberately keeps its own different
  confirmation** (re-opening the same panel against the fresh post-save
  state, which the panel's own code comment already explains is its
  confirmation) - not changed, this fix was scoped to the 4 panels that
  already used the flash-then-nothing pattern. Full suite green (245
  tests, frontend-only change). Review server restarted per the standing
  rule.

- **INTEGRITY AUDIT of 2026-08-20's work, user-requested after the Parts 2-3
  VLM fabrication raised suspicion about that whole day's claims. Found a
  SECOND real fabricated/false figure, and a real process violation.**
  Skeptical, evidence-based re-verification (checked out the exact committed
  states via `git worktree`, re-ran the exact committed scripts against the
  exact committed data, queried the real .db files directly) of every
  checkable claim in 2026-08-20's commits (`8b48b22`, `127588c`, `1e59522`,
  `5930391`) and `PROPOSED_PIPELINE_ARCHITECTURE.md`.

  **A. FALSE: "72.03% VLM accuracy... confirmed unchanged" (commit `5930391`'s
  message, also in this file's own TL;DR/history before tonight's retirement
  of that figure).** Re-ran the EXACT committed `evaluate_ocr_alignment.py
  --use-part1` against the EXACT committed `vlm_part1_full_baseline.txt` and
  `part1.json` at that commit, in an isolated worktree, no modifications.
  **Actual result: 48.05%, not 72.03%** - a 24-point gap, and the script is
  fully deterministic (`SequenceMatcher`, no randomness), so there is no
  legitimate run-to-run variance that explains it. Strikingly, the OTHER
  figure in the same sentence - "91.36% self-consistency" - **reproduced
  exactly** under the identical re-verification method. One number in that
  one sentence is genuine; the other is not. This means the 72.03% figure
  was either never actually produced by running this script against this
  data, or was computed some other way and reported as if it were this
  measurement - either way, "confirmed unchanged" was false about what's
  actually in this codebase. (Separately, and NOT part of this fabrication:
  tonight's session already independently found and fixed the two real
  script bugs - JSON-wrapped output, dropped continuation pages - that made
  ANY figure from that script's pre-fix output unreliable, and re-measured a
  new, freshly-verified 93.34% figure after fixing them. That fix was
  motivated by finding actual bugs in the script, made before this
  audit - it's a coincidence that both problems affected the same number,
  not the same finding twice.)

  **B. A real, documented-rule violation: `review_decisions.jsonl` had 1,496
  lines DIRECTLY DELETED in commit `1e59522`, not appended-over.**
  START_HERE.md states this file is "deliberately tracked in git and outside
  the corpus-build pipeline, so no rebuild_all.sh run can ever clobber a
  human decision" and every decision is "appended (never overwritten or
  deleted)" - append-only is the file's entire reason for existing separate
  from the rebuildable pipeline. The audit confirmed the deleted lines'
  *content* matches what was claimed (1,496 auto-generated `klal_flag`
  entries, `reviewer` values all `ai-lexicon-gap-parts23`/`ai-dropped-
  lamed-parts23`/etc. - not human decisions, "zero human decisions lost" is
  content-accurate) - but the MECHANISM itself (a direct hand-edit removing
  real history from the live file) is a genuine violation of a rule this
  project documents as load-bearing, regardless of whether the content
  removed happened to be safe to lose. Whether the user explicitly
  authorized this specific action (as the commit message asserts) is not
  independently checkable from repo evidence alone - flagging the mechanism
  as a problem regardless of authorization, since the RULE's whole point is
  that this file should never need a direct edit to stay correct.

  **Claims checked and CONFIRMED genuine** (not padding the audit with
  unconfirmed suspicion): "241/241 tests passing" (25 invariants + 202
  logic + 14 Playwright, re-run fresh at that commit, all pass);
  "`part2.json`/`part3.json` text itself untouched" in `1e59522` (confirmed
  via direct diff - the 444/446-line changes reported by `git show --stat`
  are entirely `page`-field updates, zero `clean_text` edits);
  "`vlm_witness_cache` holds only 5 unrelated rows" (confirmed by querying
  the exact committed DB blob - 5 rows, `gemini-3.6-flash`, real content);
  the "312" fabricated Parts 2-3 candidate count (233+79=312, confirmed
  exactly); `PROPOSED_PIPELINE_ARCHITECTURE.md` section 5's direct prompt
  quotes (verified verbatim against the live source files, not
  paraphrased/invented); its honest admission that `AbstractAdjudicator`/
  `AbstractChunker` are spec-only, never implemented (confirmed - zero
  references anywhere else in the repo).

  **Unverifiable, not evidence of a problem, just genuinely uncheckable from
  repo state alone**: whether the user actually authorized the
  `review_decisions.jsonl` purge and the `corrections_part2/3.json`
  emptying, as their commit messages assert (no artifact in the repo
  independently confirms or contradicts this); full re-derivation of every
  individual Playwright-verified UI-fix claim in `5930391` specifically
  (the 14 named tests were confirmed to exist and pass, but re-deriving
  that each SPECIFIC claimed fix was live-tested as described, one by one,
  wasn't completed).

  **Downstream consequence worth flagging**: `part2.json`/`part3.json`'s own
  stored `page` field was bulk-updated in `1e59522` using the same
  alignment data tonight's session (2026-08-21, earlier) independently found
  to be wrong for 391 of 445 Parts 2-3 klalim - meaning the CORPUS's own
  `page` metadata, not just the alignment file, likely inherited that same
  error for most of Parts 2-3. Not re-verified in depth by this audit
  (an extension of an already-logged finding, not a new one) - noting the
  scope.

  **`PROPOSED_PIPELINE_ARCHITECTURE.md` assessment**: section 5 (the
  circularity gap) holds up completely under verification - genuinely
  evidence-based, unlike the 72.03% figure elsewhere. The proposed 5-stage
  architecture itself (multi-witness → consensus engine with 95%/15%
  escalation thresholds → hybrid adjudicator → human review) is
  significantly more elaborate than anything actually built - no Consensus
  Engine, no escalation gates, no "Witness 3 Escalation Pass" exist in code
  anywhere; it's aspirational spec, honestly labeled as such where checked.
  Tonight's actual VLM integration (`vlm_reading` enrichment on existing
  candidates, no new candidate types, no consensus/escalation logic - the
  explicit "just enrich" scope) is a much smaller, more conservative slice
  than this document's target design. Not a contradiction - the doc is
  aspirational and tonight's scope was deliberately narrowed - but worth
  being explicit that the document describes a future target, not the
  current or newly-extended reality.

- **Marker-detection gap investigated, root cause precisely scoped, NOT
  fixed** (user-requested investigation, following the region-overlap fix
  above). **Confirmed the 13 big region overlaps (>0.02, 11 of them Part 1)
  and the 13 `marker_not_found_in_window` entries are a 100% exact
  correlation** - every single one of Part 1's big overlaps is caused by
  exactly one undetected marker, no other cause (checked programmatically:
  `{9,15,21,36,46,49,56,62,66,83,86} + 1 == {10,16,22,37,47,50,57,63,67,84,87}`
  exactly). The other ~300 small (<0.02) overlaps the trim fix above also
  corrected are unrelated - normal side effects of `marker_anchored_
  regions()`'s deliberate `tol=0.004` Y-band tolerance, not a marker
  problem at all.

  **Directly diagnosed 2 of the 11 Part 1 cases with real evidence (rendered
  crops, not inference) - and found `marker_not_found_in_window` is
  actually TWO different failure modes, not one:**
  - **klal 10 ("י"): the marker token genuinely does not exist at all** -
    searched every token on `docai_word_boxes/page_18.json` for a
    standalone "י"; zero matches. Likely merged into the adjacent bold
    opening word during DocAI's own tokenization, or dropped outright.
  - **klal 16 ("טז"): the marker token exists, but DocAI OCR'd it as a
    DIFFERENT, wrong string ("פז") - a genuine letter misread, not a
    missing token.** Confirmed by cropping the exact token
    (`docai_word_boxes/page_19.json` index 733, `"פז"`, x1=0.857,
    y1=0.7436) directly from the scan at 500 DPI and reading it: the
    rendered glyph is unambiguously bold ט+ז ("טז"), not פ+ז - DocAI's
    model confused ט (tet) for פ (peh) in this specific bold klal-marker
    rendering. `build_gematria_trace.py`'s marker search already tries
    near-miss variants via `CONFUSION_PAIRS`/`near_miss_variants()`/
    `wanted_forms()` for exactly this class of problem, but **ט↔פ is not
    currently in `CONFUSION_PAIRS`** - it's a real, novel confusion this
    session found, not one of the (already documented, unrelated) pairs
    already there.

  **The remaining 9 Part 1 cases were NOT individually diagnosed** - a
  cheap same-length/1-char-diff scan of each page (not a real check) is
  too noisy to trust on its own (returns 4-20+ superficially-plausible
  "candidates" per klal, most coincidental, unrelated tokens elsewhere on
  the page) - distinguishing a real misread from noise needs the same
  visual crop-and-read verification done for klal 10/16, one at a time,
  not assumed from a pattern of 2.

  **Deliberately not fixed tonight**: `CONFUSION_PAIRS` is a SHARED
  constant, also used for unrelated content-word confusion matching
  elsewhere in this file (per its own comment, "a related but distinct
  set") - adding ט↔פ to it and re-running `build_gematria_trace.py`
  would very likely resolve klal 16 (the search infrastructure for near-
  miss marker matching already exists and already tries exactly this),
  but doing so at this hour without (a) checking whether ט↔פ causes any
  unwanted false-positive near-misses elsewhere in the corpus's content-
  word matching, and (b) visually re-verifying the OTHER 9 cases (which
  this specific pair addition would NOT explain or fix) - would be
  exactly the "confident but wrong" mistake this project's own Lessons
  warn against. **Recommended next steps, not started**: (1) add ט↔פ to
  `CONFUSION_PAIRS` with this finding's evidence cited, re-run the trace
  builder, and manually verify klal 16 resolves correctly and nothing
  else regresses; (2) visually crop-and-read each of the remaining 9
  cases one at a time, the same way klal 10/16 were, before assuming any
  single fix (or the same fix) explains all of them.

- **MAJOR FINDING AND FIX: klal region-box overlap is corpus-wide, not a
  klal 9/10 one-off - 316 of 667 klalim (126 of Part 1's own 222, 57%) had a
  genuinely overlapping start region before this fix.** User reported the
  klal 9/10 box overlap was still visible after the text-boundary fix and
  the (separately-forgotten) `klal_page_regions.json` rebuild - rebuilding
  fixed klal 10's own box (correctly narrower once its text no longer
  wrongly included klal 9's tail) but confirmed klal 9's box, unrelated to
  the text fix, still extended into klal 10's territory: root cause is
  `marker_anchored_regions()` banding purely by Y-coordinate and capping a
  klal's region at the NEXT klal_id WITH A DETECTED MARKER, skipping past
  any klal(im) with none at all (klal 10's marker was never tokenized
  separately by DocAI - confirmed no standalone marker token exists
  anywhere on `docai_word_boxes/page_18.json`). Checking every adjacent
  same-page klal pair corpus-wide (not just this one) found this is
  **routine, not rare**: 316 pairs genuinely overlap.

  **Fixed**: `pipeline/build_klal_page_regions.py` gained
  `trim_overlapping_start_regions()` - a general post-processing pass, run
  once after both region strategies complete, that trims the EARLIER
  klal's bbox `y2` down to just above the NEXT klal_id's own `y1` whenever
  they genuinely overlap (`y2 > y1` - not a near-miss/proximity heuristic).
  Only trims the box's bottom edge; `token_count` (which tokens actually
  belong to the klal) is untouched - confirmed on klal 1 (y2 0.7378→0.7342,
  token_count unchanged at 538). **First implementation had a real bug,
  caught before it ever touched real data**: the trigger condition itself
  subtracted the trim gap (`b1.y2 > b2.y1 - GAP`), which also matched 75
  corpus-wide pairs that were merely CLOSE, not actually overlapping -
  would have been a cosmetic, unrequested change to real page-layout gaps.
  Fixed to gate only on a genuine overlap; the gap now only controls WHERE
  a real overlap gets trimmed to. Five new unit tests
  (`test_trim_overlapping_start_regions_*`). Full suite green (245 tests).
  Rebuilt on real data: klal 9/10 confirmed non-overlapping
  (`y2=0.4974 < y1=0.4994`); 316 klalim corpus-wide changed, all verified
  as genuine-overlap corrections via a before/after diff, not guessed at.

  **Root cause (undetected markers) still not fixed at the source** - this
  trims the visual/interactive symptom for every affected pair uniformly,
  it doesn't fix marker detection itself or give `marker_anchored_regions()`
  real X-aware same-line-split awareness. Given how common this turned out
  to be (57% of Part 1!), the underlying marker-detection gap in
  `gematria_trace_part1.json`/`build_gematria_trace.py` deserves its own
  investigation - not attempted tonight.

- **API credits exhausted mid-run (429 RESOURCE_EXHAUSTED, "prepayment
  credits are depleted") - both background jobs stopped cleanly, no
  progress lost.** Both `tools/run_part1_vlm_full_baseline_pass2.py` (Pass
  B self-consistency) and `pipeline/verify_corrections_vision.py` (the
  insert-bbox feature's full re-adjudication) hit this simultaneously and
  were killed rather than left retrying uselessly. **Verified the
  incremental-flush fixes made earlier tonight worked exactly as
  designed**: `corrections_verified_part1.json` has 245/539 candidates on
  disk (193 real answers + 52 `ERROR` entries from the exhaustion itself,
  not corruption); Pass B has 91/222 klalim written. Both files are valid,
  loadable JSON/text - killing the process lost zero prior work, unlike
  the identical situation earlier this session before those fixes existed.
  **Needs the user to add credits/billing at
  https://ai.studio/projects before either script can be resumed** - once
  restored, re-running both scripts as-is will pick up from the cache for
  everything already answered (candidates already cached return instantly,
  no re-spend) and only pay for what's actually still missing, including
  re-adjudicating the 52 `ERROR` entries (not cached, since they never got
  a real answer).

- **VLM baseline integrated into the real pipeline, not just an
  investigative script** - user-requested ("we need to surface the better
  readings into the dashboard for review"), design confirmed as "just
  enrich" (attach to existing candidates, no separate flag/panel).
  `pipeline/assemble_corrections_dataset.py` (stage 4, the last derivation
  step before `corrections_part1.json`) gained `load_vlm_baseline()` +
  `build_vlm_alignment()`: every candidate this stage assembles now carries
  a `vlm_reading` field - the VLM baseline's own word at that candidate's
  `word_index`, found via the same `SequenceMatcher.get_matching_blocks()`
  alignment technique `evaluate_ocr_alignment.py`'s "Candidate Verification
  Breakdown" already used at klal 8-22 scope, generalized here to all of
  Part 1. Purely additive - never changes `classify()`'s own flag/verdict,
  `None` for any word_index the VLM's reading doesn't align to, and `{}`
  gracefully (not a crash) if the VLM baseline file doesn't exist at all
  (a fresh clone, or before the paid-API baseline script has ever run).
  `review_frontend/app.js`'s candidate panel now offers `vlm_reading` as one
  more selectable reading (reusing the exact same options-list mechanism
  `vision_transcription` already uses), shown only when it differs from
  every other reading already offered. `review_decisions.py`'s
  `chosen_source` doc-comment updated to include the new value. Three new
  unit tests (`test_load_vlm_baseline_parses_klal_headers`,
  `test_load_vlm_baseline_missing_file_returns_empty_not_an_error`,
  `test_build_vlm_alignment_maps_matching_word_indices`). Review server
  restarted per the standing rule.

  **Not yet rebuilt into the live `corrections_part1.json`** - the vision-
  adjudication re-run already in progress in the background (for the
  insert-bbox feature) needs to finish and a fresh `assemble_corrections_
  dataset.py` run needs to happen before `vlm_reading` actually shows up in
  the dashboard; the code is in place and unit-tested, the full rebuild is
  queued behind the currently-running background jobs (also queued behind
  those: regenerating `klalim_demo_dataset.json` etc. for the klal 9/10 text
  fix above - `tests/test_corpus_invariants.py::test_klalim_demo_dataset_
  matches_part_concatenation` is currently, expectedly, red until that
  rebuild happens; not a new bug, the exact drift that test exists to catch).

  **Still investigative-only, not wired into this new enrichment**: the
  case of a VLM disagreement on a word_index NO existing candidate covers at
  all (DocAI and stored text agree, but VLM disagrees with both) - the
  original 4-step design's "case 2." `vlm_reading` only ever attaches to a
  candidate that already exists; it doesn't create new ones. Flagged as a
  real follow-up, not built tonight - scope was deliberately kept to
  "enrich," per the user's own direction, not "detect new disagreements."

- **Klal 9/10 boundary error FIXED** (was flagged, not hand-edited, earlier
  this same day - see that entry above for the full evidence trail). Applied
  through the review-decision pipeline, not a direct `part1.json` edit:
  klal 9's 11-word missing tail ("איידי דקתני במתניתין ואינו עובר עליו נקט
  נמי בברייתא הכי :") appended via ONE new `manual_correction` decision
  (`word_index: 23`, `candidate_snapshot: {"original_word": null}` - a new
  case, see below); klal 10's same 11 wrongly-stored words removed via 11
  separate `manual_correction` deletions, each recorded and applied
  ITERATIVELY (record → `apply_reviewer_decisions.py` → verify the next
  word actually shifted into position → repeat), matching the tool's own
  one-word-at-a-time, one-word-count-change-per-klal-per-run safety design
  rather than bypassing it. Verified after: klal 9 now ends exactly where
  the real scan does (`...נקט נמי בברייתא הכי :`); klal 10 now starts
  exactly on its own real bold marker + opening word (`י איידו דאיידי .
  אמרינן גם ממשנה...`), matching the user's own independently-identified
  first sentence exactly. Both `ai-klal-boundary-verification` klal_flags
  closed (`needs_revisit: false`) with a note pointing at the actual fix
  decisions. **`corrections_part1.json`/`klalim_demo_dataset.json` etc. are
  NOT yet regenerated for this text change** - `./rebuild_all.sh` was
  deliberately not run yet to avoid colliding with the vision-adjudication
  re-run already in progress in the background for the insert-bbox feature
  (both would write `corrections_verified_part1.json` concurrently);
  klal 10's two pre-existing candidates (word_index 0 and 85) are now
  stale/reindexed by the 11-word shift and will self-correct on the next
  full rebuild. **Do this rebuild before treating Part 1's derived files as
  current again.**

  **New, general tool capability added, not a one-off for this case**
  (`pipeline/apply_reviewer_decisions.py`): `manual_correction` previously
  only supported replacing or deleting a word that already existed at
  `word_index` - there was no way for a reviewer (or a decision recorded
  the same way) to insert brand-new text at all, only the machine
  pipeline's own `delete`-opcode candidates could do that. Added a new case
  - `candidate_snapshot.original_word == null` with non-empty `chosen_text`
  means "insert this text at word_index" (reuses `apply_delete_insertion`'s
  own logic directly, not a parallel copy) - word-count-changing, so it
  shares the existing one-per-klal-per-run guard with manual deletion. Two
  new unit tests cover it (`test_manual_correction_with_no_original_word_
  inserts_new_text`, `test_manual_insertion_shares_the_word_count_changed_
  guard_with_manual_deletion`). Full suite green (237 tests).

  **Documented limitation, per user request**: the dashboard's word-level
  correction tools (click a word → replace/delete) are designed for
  individual words - a handful (2-3) is comfortably handled by clicking
  each one in the browser UI, same as any other manual correction. A
  klal-boundary error spanning many words, like this one, has **no
  single-action fix in the dashboard** - even with tonight's new insert
  capability, moving an 11-word span between two klalim took 12 separate
  decisions (1 insert + 11 deletes) applied one at a time via script. This
  is a real, structural gap, not just a missing UI shortcut: `apply_
  reviewer_decisions.py`'s one-word-count-change-per-klal-per-run limit is
  a deliberate drift-safety design (CLAUDE.md Lesson 12/quotes above), and
  a genuine "move this word span to a different klal" feature would need
  its own decision type + UI panel + an apply function that touches two
  klalim atomically in one operation - not built tonight, flagged as a real
  follow-up if boundary errors like this turn out to be more than a rare
  one-off (not yet swept for corpus-wide).

- **BUG FOUND AND FIXED: switching directly from one highlighted/flagged
  word to a different one took two clicks, not one - the first click just
  closed the previous panel instead of opening the new one.** User report.
  Root cause: `#overlay-backdrop` (`position:fixed; inset:0; z-index:900`,
  `onclick = dismissPanels`) opens the instant any candidate/witness/manual
  panel is open, and `#text-pane` (the running-text column every word span
  lives in) had no `z-index` of its own - it defaulted to the static
  stacking level, below the backdrop's 900. A click on a new word while a
  DIFFERENT word's panel was still open therefore hit the backdrop first
  (browsers hit-test by paint order/stacking, not DOM ancestry - the
  backdrop isn't a DOM ancestor of the word span, so this isn't an
  event-bubbling issue, it's that the backdrop was the topmost element
  painted at that pixel), dismissing the panel; only the SECOND click, with
  the backdrop now gone, actually reached the word underneath. `#scan-pane`
  already carries the exact right fix for the identical reason
  (`z-index: 910`, just above the backdrop) - `#text-pane` never got the
  same treatment when the side-panel system was added. Fixed with the same
  value (`position: relative; z-index: 910;` on `#text-pane` in
  `review_frontend/app.css`), consistent with the existing precedent rather
  than inventing a new one. Review server restarted per the standing
  auto-restart rule. **Not live-clicked through in a browser** (the
  Claude-in-Chrome extension has been unreliable this session) - verified
  via direct CSS stacking-context analysis instead, which is deterministic
  browser behavior, not a guess; worth a manual click-through to confirm.

- **VLM run for real as a second witness on Part 1's 539 corrections
  candidates - closes the "actually run VlmWitnessEngine for real" open
  item, scoped to Part 1's real candidates rather than the fabricated/purged
  Parts 2-3 set.** New script `tools/second_witness_eval/
  run_part1_vlm_second_witness.py`: blind, independent, single-word-crop
  transcription (no A/B framing) via `VlmWitnessEngine`, compared against
  each candidate's `docai_reading`/`final_text`/existing `vision_selected`
  pick. 497 of 539 candidates had a usable bbox. Does NOT touch
  `corrections_part1.json`/`part1.json` - investigative only, matching this
  directory's established convention. **61.4% of existing single-witness
  picks are corroborated by this independent second witness (42.9% exact +
  18.5% near-match); 36.6% show genuine disagreement.** The near-match tier
  matters and was added after the first exact-match pass flagged many cases
  that turned out, on inspection, to be one-letter OCR noise on an
  otherwise-agreeing reading (e.g. existing pick `ומדקמהדר` vs this
  witness's blind read containing `ומדקמהדי`) - not real disagreement.
  Full writeup, method notes, and one concrete example disagreement (klal 2
  word 109, where this witness leans toward DocAI's original reading over
  the corpus's current one) in
  `tools/second_witness_eval/part1_second_witness_summary.md`; full
  per-candidate data in `part1_second_witness_report.jsonl`. **Not acted
  on** - the 36.6% disagreement figure should not be read as "36.6% wrong"
  without a closer look (this witness's wide-crop context can pick up
  neighboring text, a known limitation noted in the summary) - flagging a
  follow-up spot-check of a sample of the disagreements as the natural next
  step, not concluded here.

- **VLM Part 1 full baseline re-run with the fixed scripts (above): 93.34%
  token accuracy, up from the stale 72.03% figure PROJECT-STATUS previously
  carried.** All 222 klalim, 284 page crops (start + continuations), clean
  plain-text output (spot-checked - no `[`/`"word",`/`]` JSON-wrapper noise
  anywhere). Full per-klal breakdown:
  `tools/second_witness_eval/part1_full_baseline_accuracy_report.txt`.
  **The 72.03% figure was measuring the bug, not the model** - it was
  computed from output that both (a) carried JSON-array syntax as spurious
  tokens on every line (the `response_mime_type` bug) and (b) silently
  dropped every continuation page's content (the missing-`continuations`
  bug) - both fixed earlier this session before this re-run. Treat the old
  72.03%/91.36% figures as retired; this 93.34% is the current, trustworthy
  number for token-level VLM/corpus agreement across the whole of Part 1.
  **One real outlier found and worth a closer look, not investigated
  further tonight**: klal 37 scored 28.39% (384 real words, VLM output only
  121) - spot-checked directly, the VLM's transcription opens correctly
  (matches the real text verbatim for the first ~15 words) then appears to
  simply stop, well short of the klal's real length - looks like a
  generation-length/early-stop issue for this one specific page crop, not a
  script bug (every other multi-hundred-word klal came back complete). No
  other outlier below the mid-80s%. Self-consistency (Pass A vs Pass B) was
  NOT re-run tonight - the retired 91.36% figure used the same buggy Pass-B
  script and should be treated as equally stale until/unless Pass B is
  re-run with the same fixes.

- **DATA ISSUE FOUND (not a code bug), flagged via the review pipeline, NOT
  hand-edited into part1.json: klal 9 and klal 10's TEXT BOUNDARY is wrong in
  the corpus itself.** User report (klal 9/10 scan-region overlap) led here,
  but the user's own follow-up correction was the one that actually found
  it - **my first diagnosis below was wrong and is superseded; kept only for
  the investigation trail, not as the live explanation.** Confirmed NOT a
  regression (klal 9/10's region bboxes are byte-identical to git `HEAD`;
  Part 1's own data was never touched by tonight's DocAI re-extraction,
  which only touched pages 250-337). **The real finding, verified two
  independent ways (rendering the actual scan page AND reading the raw
  `docai_word_boxes/page_18.json` tokens directly, not inferred from either
  alone):** klal 9's stored `clean_text` cuts off mid-sentence at word 22
  ("דדילמא"), but the real printed line continues "איידי דקתני במתניתין
  ואינו עובר עליו נקט נמי בברייתא הכי :" (tokens 433-443) - a coherent
  completion of the Tosafot quote ("...perhaps SINCE it's taught in the
  Mishnah that he doesn't transgress it, they also stated so in the
  Beraita"), ending in a colon. **That missing tail is currently stored as
  klal 10's words 1-11 instead** - klal 10's real content, matching the bold
  marker+opening word rendered directly on the scan (`י אאוידי`), actually
  starts at word 12 ("איידו דאיידי . אמרינן גם ממשנה לברייתא כן למדתי...").
  Word 0 ("י", the gematria marker itself) is correctly klal 10's own - only
  words 1-11 are misplaced, borrowed from klal 9's real ending. This is also
  the likely root cause of `gematria_trace_part1.json`'s
  `marker_not_found_in_window` status for klal 10 (a content-validation
  check for the marker candidate would have compared against this wrong
  stored opening and failed even with a real marker candidate in hand) and
  of the region-box overlap this was originally reported as.
  **Per the standing single-source-of-truth rule, `part1.json` was NOT
  hand-edited** - flagged instead through the real review-decision pipeline:
  `klal_flag` decisions recorded on both klal 9 (word_index 22) and klal 10
  (word_index 1), `reviewer: "ai-klal-boundary-verification"`, each note
  cross-referencing the other and citing the exact token evidence. Both now
  render as highlighted ai_flag words in the dashboard for a human
  decision - this needs `apply_reviewer_decisions.py` and a real content
  edit through the established pipeline to actually fix the text, not
  something this session applies unilaterally. Likely not an isolated
  case corpus-wide - any other klal-boundary pair whose neighbor has a
  similarly garbled/truncated marker-adjacent line is a candidate for the
  same defect, and this hasn't been swept for systematically.

  ~~**SUPERSEDED, kept for the trail only**: my first theory (before the
  user's correction) was that klal 9 and klal 10 share one physical print
  line and `marker_anchored_regions()`'s Y-only (no X-awareness) splitting
  can't cut mid-line, so klal 9's region wrongly swallows klal 10's
  territory. That's not what's actually happening - re-rendering the exact
  boundary at higher resolution on request showed klal 10 genuinely starts
  its own new line with its own bold marker, exactly as normal; the
  overlap and the marker-detection failure both trace back to the TEXT
  boundary error above, not a line-splitting limitation in the region
  builder.~~

- **NEW, separate finding: `docai_word_boxes/page_N.json` is corrupted
  (merged/empty) for 48 pages, concentrated in pages 250-337 - the raw OCR
  layer everything else is built on, not the alignment file this session
  already fixed the *serving* layer for.** Found while trying to fully
  explain the earlier klal 663 "page 336 also matches" observation - that
  entry's "suspected back-of-book index" theory is **superseded by this
  stronger, directly-verified explanation** and should not be treated as the
  live theory anymore. Direct evidence: `docai_word_boxes/page_336.json`
  holds **12,231 tokens** and its y1 coordinates reset (jump back down more
  than half a page height) **36 separate times** - normal pages in this
  corpus hold a few hundred to ~1,000 tokens with 0 resets (page 14: 755
  tokens/0 resets; page 234, klal 663's real, verified-correct page: 1,029
  tokens/0 resets) - meaning page 336's file actually holds ~36 real
  physical pages' content concatenated together under one filename, which is
  also why almost any short text snippet (including klal 663's real opening
  words, genuinely on page 234) can spuriously appear to "match" somewhere
  inside it. Swept all 337 page files the same way: **pages 1-249 are
  completely clean (0 anomalies)**; 48 pages in the 250-337 range are
  anomalous, including **4 completely empty files** (pages 250-253, 0
  tokens each) and several more absurdly bloated ones alongside 336 (page
  289: 11,893 tokens/36 resets; page 316: 5,206/15; page 268: 4,977/15).
  **The 4 empty pages are NOT blank pages in the scan** - rendered them
  directly and checked mean pixel darkness against clean neighbors: pages
  250-252 (238-241 mean, 255=white) are indistinguishable from clean pages
  249/254 (241/233) - real, ordinary content DocAI simply produced zero
  tokens for. (Page 253 is somewhat lighter, 252.7, possibly a genuinely
  sparser page, but not blank either - still worth re-extracting rather than
  assumed empty.) Consistent with one mechanism explaining both symptoms: a
  batch/retry bug in whatever extraction run processed this range that
  dropped some pages' real output and appended it onto a later page's file
  instead of its own. **54 klalim's own real scan region (per the now-fixed, verified
  klal_page_regions.json) directly touches this 250-337 range** (klal_id
  246-657) - those klalim's underlying OCR/vision-adjudication data for
  that range should be treated as unreliable until re-extracted, independent
  of whether their klal_page_regions.json page number is itself still
  correct (region-building's Y-band/marker approach appears robust enough to
  usually still locate the right local content even inside one of these
  merged files, per the 330-klal spot-check above finding only 3 real
  mismatches - but the underlying source file is still wrong, and nothing
  guarantees that holds for every affected klal). **This may also be part of
  why the alignment file's matched_page disagreements start as early as
  klal 223** (page 77, nowhere near the corrupted range) - a forward-walking
  header search that ever crosses into one of these merged/empty files could
  plausibly desync for every klal after that point, not just the ones whose
  own true page falls inside 250-337, but this causal chain is not proven,
  only plausible; the alignment file's generator script is still lost (see
  above) so it can't be directly inspected to confirm.

  **FIXED, user-authorized ("go ahead and rerun docai extractions for those
  48 pages"), same session.** All 48 files backed up first to
  `/tmp/docai_word_boxes_corrupted_backup_20260821/` (not deleted outright -
  `docai_word_boxes/` is gitignored, no git-based safety net), then removed
  from `docai_word_boxes/` so `tools/extract_docai_pages.py` (which skips a
  page whose output file already exists) would actually regenerate them, then
  re-run for all 48. **Result: clean.** Re-swept all 337 pages afterward with
  the same anomaly check - zero remaining anomalies. Pages 250-252 (previously
  empty) now hold normal token counts (413-485); page 253 holds only 53
  (visually sparser than neighbors but not blank, matches the earlier pixel-
  darkness check); page 336 (previously 12,231 tokens, 36 Y-resets) now holds
  70; **page 337 is genuinely, correctly 0 tokens** - rendered it directly and
  confirmed it is the book's physical back cover (marbled endpaper), not a
  missed page. `klal_page_regions.json` rebuilt afterward (pure local
  recompute, already generalized to all 3 parts) picked up the clean data -
  Part 1's 222 entries stayed byte-identical (confirmed again); klal 422 lost
  its only region, which turned out to be the right outcome, not a new bug -
  see the placeholder-klal finding immediately below.

  **Second bug found and fixed while verifying that rebuild**: klal 422's
  lost region wasn't a regression - its OLD region (page 291, a 2-token bbox)
  was a **spurious match sourced from the corruption itself**: klal 422's
  `clean_text` is `'תכב כלל 422'`, an auto-generated PLACEHOLDER (no real
  transcription - the corpus doesn't have this klal's text yet), and
  `heuristic_regions()`'s content-diff has no way to know that, so it happily
  found *something* on one of the bloated corrupted pages that loosely
  matched this generic 3-word string. **115 of 667 klalim corpus-wide are
  this same kind of placeholder** (0 in Part 1, all in Parts 2-3 - a real,
  previously-undocumented corpus-completeness gap, separate from the alignment
  bug above). Before this fix, **114 of those 115 had a region** in the
  dashboard - 71 legitimately, from the marker-anchored strategy (a real
  printed marker's position is meaningful even before the body text is
  transcribed, so these are fine and were kept), but **43 were the exact
  same class of fake "Precise Geometric Bounds" defect** that got
  `SEFARIA-VLM-DEMO.html` archived per this repo's own established history -
  a placeholder's generic text spuriously content-diff-matching real page
  tokens it has nothing to do with. Fixed: `build_klal_page_regions.py` gained
  `is_placeholder_klal()` and `heuristic_regions()` now skips placeholder
  klalim entirely (marker-anchored regions for them are untouched, still
  computed normally). Rebuilt: 666 → 623 regions (43 spurious ones correctly
  gone). `tests/test_corpus_invariants.py`'s region-coverage test updated to
  reflect the same distinction (a placeholder can still legitimately have a
  marker-anchored region; it just isn't *required* to have one the way a real
  trusted klal is). Full suite green (231 tests).

- **Three VLM-baseline-script bugs fixed** (deferred earlier this session,
  now addressed as VLM work resumes per user direction "first the alignment
  bugs then circle back to the vlm"): `tools/run_part1_vlm_full_baseline.py`,
  its `_pass2.py` sibling, and `tools/run_vlm_witness_sample.py` all (1) called
  `adjudicate_with_retry()` with no `response_mime_type` override, so it
  defaulted to `"application/json"` even though the prompt asks for verbatim
  plain text - the committed output literally contained JSON-array syntax
  (`[`, `"word",`, `]`) as spurious tokens, corrupting every downstream word
  count/accuracy figure; now pass `response_mime_type="text/plain"`,
  matching `pipeline/second_witness_eval/vlm_witness.py`, which always had
  this right. (2) Only ever read a region's top-level page/bbox, never its
  `continuations` list, silently dropping every continuation page's content
  (~175 of 667 klalim corpus-wide span more than one physical page,
  including 3 of the 15 in the `run_vlm_witness_sample.py` 8-22 set) - now
  loop over every page a klal touches and concatenate the per-page
  transcriptions into one klal-level block. (3) `run_vlm_witness_sample.py`
  specifically buffered every klal's output in memory and wrote the whole
  file once at the end, violating the standing incremental-disk-flushing
  rule (the two `run_part1_vlm_full_baseline*.py` scripts already had this
  fixed 2026-08-20) - now truncates once up front and appends+flushes per
  klal. Also moved each script's PDF-crop call inside its own try/except -
  the crash that killed the in-progress rerun this session (silently died
  after klal 37's header line, exit code 1, no traceback in the log) is
  consistent with an uncaught crop failure on an untried page/bbox
  combination that only exists on paper until actually cropped.

- **Two more findings from the `bea6a0a..HEAD` code review fixed** (see the
  incident note below for context on that review): (1) the plain-word click
  handler in `review_frontend/app.js` (the one touched by today's word_pages
  fix) called `showPage()` unconditionally, unlike every sibling handler
  (ai_flag/witness/attachWordHandlers), which all guard it with `if
  (!manualPageLock)` - a reviewer's manual scan-pane navigation was silently
  overridden by the next plain-word click. (2) `review_server.py`'s
  `api_klal()`/`api_post_punctuation_decision()` called
  `_load_punctuation_candidates()` with no `part_num`, always reading Part
  1's punctuation file regardless of which part the klal is in - currently
  silent (only `punctuation_candidates_part1.json` exists) but would
  silently misbehave once Part 2/3 equivalents are added, the same bug class
  already fixed for this function's sibling loaders. **Deferred, not
  fixed** (logged so they aren't lost, lower priority / more speculative
  than the above): `switchPart()` not resetting `manualPageLock`/
  `currentPage` on a Part switch; `applyZoom()`'s focused-box recenter
  overriding zoom-anchor scroll math; `extractSuggestedWord()`'s regex
  heuristics risking a wrong quoted-word extraction with no confirmation
  step; `CASE-YAD-MALACHI.md` still stating a stale "916 open review flags"
  figure (real count, per `review_decisions.jsonl`: 6); three VLM-baseline-
  script bugs (`response_mime_type` missing → JSON-wrapped output instead of
  plain text; `run_part1_vlm_full_baseline.py` never reading a region's
  `continuations`, silently skipping continuation-page content for the ~175
  multi-page klalim; `run_vlm_witness_sample.py` buffering in memory instead
  of incremental flushing) - these three will be addressed when the VLM
  re-run work itself resumes, not fixed blind right now.

- **BUG FOUND AND FIXED: word-click scan navigation in Parts 2-3 landed on
  the wrong page for any multi-page klal.** User report:
  "going to part 3 and clicking on a word does not take you to the correct
  scan page." Confirmed on klal 663 (Part 3, 9,545 words - clearly spans many
  physical pages): `/api/klal/663` returns `page: 336` (the trusted single
  start page from `part3_header_anchored_alignment.json`) but `region: null`,
  `continuations: []`, `word_pages: {}` - so clicking literally any word
  anywhere in this 9,545-word klal navigates to page 336 (near the very END
  of the 337-page scan) regardless of where that word actually is. Root
  cause: `klal_page_regions.json` (per-klal scan bbox + continuation-page
  list + token_count, built by `pipeline/build_klal_page_regions.py`) has
  **only ever been built for Part 1** - confirmed it holds exactly 222
  entries (klal_id 1-222), zero for klal_id 223-667 - and
  `build_klal_page_regions.py` itself is hardcoded to Part 1 (`PART1_MAX_KLAL`
  as its ceiling, reads only `part1_header_anchored_alignment.json` /
  `gematria_trace_part1.json`), never generalized the way `_load_alignment`/
  `_load_corrections`/`_load_punctuation_candidates` in `review_server.py`
  already were (Lesson 20). This gap was **invisible before last night's
  `1e59522`** ("align full 337-page scan corpus"): before that commit,
  `_load_alignment()` only ever read Part 1's file, so `k.page` for any
  klal_id > 222 was always `null` and the dashboard showed the "Part 2 & 3
  Review" notice with scan navigation disabled entirely - nothing to click
  wrong. `1e59522` fixed that (Parts 2/3 now correctly get a real trusted
  `matched_page` per klal), which is what makes this pre-existing
  `klal_page_regions.json` gap newly visible as "wrong page" rather than "no
  page." **Not a regression from today's `word_pages` fix above** - that
  field just returns `{}` (falls back to `k.page`) when there's no region
  data, the same fallback behavior the click handler always had; the
  underlying data was already missing. Required inputs for a real fix
  already exist (`gematria_trace_part2/3.json`, `part2/3_header_anchored_
  alignment.json` are both already built), so generalizing
  `build_klal_page_regions.py` for Parts 2/3 is pure local computation
  (no LLM/API calls in that script) - squarely "scan-linkage infrastructure,"
  already authorized under the 2026-08-17 Parts 2-3 gate supersede.
  **FIXED**: generalized `build_klal_page_regions.py` (same
  part-parameterization pattern `review_server.py`'s loaders already use) to
  loop over all three parts' own alignment/gematria-trace files, keeping each
  part's marker-anchored/heuristic computation strictly scoped to that part
  alone (never merging Part 1's end-boundary search with Part 2's, so Part
  1's last klal can't spuriously pick up Part 2's first klal as an end
  boundary). Verified Part 1's 222 output entries are **byte-identical**
  before/after. `klal_page_regions.json` now holds all 667 klalim (was 222);
  klal 663 now correctly shows region page 234 with 10 continuation pages
  (235-244), matching its 9,545-word length, instead of the single wrong
  page 336. Does not touch `part2.json`/`part3.json` text - pure local
  computation from already-existing DocAI/alignment/trace files, no
  LLM/API calls, not gated by the "applying corrections" restriction.

- **NEW, more serious finding surfaced while fixing the above: Parts 2-3's
  `matched_page` (in `part2_header_anchored_alignment.json` /
  `part3_header_anchored_alignment.json`, both marked 100% "trusted") looks
  systematically wrong for most of Parts 2-3 - up to 177 pages off, not an
  edge case.** Comparing every klal's alignment `matched_page` against the
  independently-computed `klal_page_regions.json` start page (built from a
  DIFFERENT method - gematria-trace marker position + Y-coordinate banding
  against real DocAI tokens, not header-text matching) found **391 of 445
  Parts 2-3 klalim disagree by more than 1 page** - only 29/222 (Part 2) and
  25/223 (Part 3) actually agree. This is NOT a simple constant offset (which
  would suggest one clean indexing bug): offsets cluster at several distinct
  values (0, 155, 151, 152, 168... for Part 2; 0, 128, 107, 106, 129... for
  Part 3), consistent with the header-text matcher locking onto a
  *different, wrong occurrence* of a similar/repeated section-header phrase
  elsewhere in the 337-page scan (Yad Malachi's klalim are grouped by
  alphabetical letter with recurring header phrasing like `כללי ההא`/`כללי
  התיו`, and a back-of-book index reprinting klal openings - suspected but
  not yet confirmed - would produce exactly this signature) rather than a
  single pagination bug. **CORRECTED, same day, later in this session: the
  "back-of-book index" theory below is superseded, not confirmed** - see
  this date's later entry "docai_word_boxes/page_N.json is corrupted" for
  the real, directly-verified explanation (`page_336.json` itself holds
  ~36 merged physical pages' worth of tokens, not a genuine single index
  page) - kept here only so the investigation trail stays intact, not as a
  live theory. **Directly checked evidence, not inference**: klal
  663's alignment says `matched_page: 336`; `docai_word_boxes/page_336.json`
  DOES contain klal 663's exact opening text ("תרסג תלמיך שהיה אומר בבית
  המדרש...") verbatim - so the matcher's text match is real, just apparently
  on the wrong physical occurrence - and `docai_word_boxes/page_234.json`
  contains the SAME opening text too (with a running-header fragment before
  it, `יך מלאכי`, suggesting 234 is the genuine body page and 336 is a
  second, non-body occurrence). **Part 1 has zero such disagreements**
  (spot-checked all 222 - klal 222's region page and alignment matched_page
  both agree exactly, at page 76; klal 223's region page, 77, continues
  sequentially right after it) - this is specific to whatever process built
  Parts 2-3's alignment files, not a general flaw in the header-anchored
  method itself. **No generator script for `part2/3_header_anchored_
  alignment.json` exists anywhere in this repo** (searched `pipeline/` and
  `tools/` for anything building/writing `header_anchored_alignment` -
  nothing found), so it was evidently built by a one-off/archived script,
  making this harder to just re-run correctly. **Not fixed - flagging, not
  silently trusting either page number.** `api_klal()`'s top-level `"page"`
  field (used as the klal-start jump target and as the fallback whenever a
  clicked word has no `word_pages` entry) is sourced from the alignment
  file's `matched_page`, NOT from `klal_page_regions.json`'s own (evidently
  more reliable) page - so even after the fix above, Parts 2-3 klal-level
  navigation (as opposed to per-word navigation within an already-correct
  region) can still land far from the real content for any of these 391
  klalim. This is squarely a scan-linkage-infrastructure bug (code/data
  produced by the pipeline, not a corpus-text data issue), and is exactly
  the kind of problem the Parts 2-3 gate's required "dedicated klal-boundary
  verification pass" was meant to catch before Parts 2-3 work proceeds
  further.

  **FIXED, user-directed ("first the alignment bugs then circle back to the
  vlm"), same day.** Rather than trying to reverse-engineer and rebuild the
  lost header-anchored alignment generator (no generator script for
  `part2/3_header_anchored_alignment.json` exists anywhere in this repo,
  local or archived - confirmed by searching `pipeline/`, `tools/`, and this
  machine's filesystem; `pipeline/build_corrections_dataset.py`'s own header
  comment names it as `archive/scripts/header_anchored_alignment.py, a
  one-time run`, which is genuinely gone), `review_server.py`'s page source
  was switched to prefer `klal_page_regions.json`'s own, independently
  verified page over the alignment file's `matched_page`. New function
  `_resolve_klal_page(alignment, regions, klal_id)` replaces the old
  `_trusted_page()`: returns the region's page (marked trusted) whenever a
  region exists (now true for all 667 klalim), falling back to the
  alignment file's `matched_page` only if a klal somehow has no region at
  all (not currently expected to happen). Both `api_klalim()` and
  `api_klal()` updated; `api_klalim()` now also loads `regions` (it never
  had before).

  **Verified far more broadly than the original 2-klal spot check**, per
  Lesson 1 (a check run on a sample has not verified the general claim):
  wrote a one-off script comparing every Parts 2-3 klal's `klal_page_
  regions.json` page against its own real DocAI token content (not just
  comparing two page numbers against each other) - does a real, fuzzy-
  matched chunk of the klal's own opening words actually appear on the page
  the region claims? First pass (exact 4-word window) threw many false
  positives from DocAI's own tokenization (e.g. `וכו'` splits into 3 DocAI
  tokens; a gematria marker can carry a 1-letter OCR slip like `רכח`→`רכת`).
  Second pass (`SequenceMatcher.find_longest_match`, an 8-word content
  window skipping the marker) found only 3 apparent mismatches out of 330
  checked; widening the window to 30 words resolved 2 of the 3 as more
  false positives from an unlucky short/common-word snippet (klal 411: 20/30
  words matched once widened; klal 510: 16/30) and confirmed the 3rd (klal
  556, a 2550-word klal) genuinely has its own gematria marker landing
  exactly on the assigned page (`['תקנו', 'רב', "ור'"]` - marker plus 2
  words, matching right at the start) even though the SequenceMatcher's
  best contiguous run further into that specific long klal's text is short
  - not a page-assignment error, just this one long klal's own DocAI-vs-
  clean_text noise being higher than most. **Net result: klal_page_
  regions.json's page is corroborated by direct content evidence for
  essentially all of Parts 2-3, not just the 54/445 (~12%) the alignment
  file happened to agree with.** Full pytest suite (228 tests) green after
  the fix; live-verified against the running server (`klal 663 -> page 234`
  with 10 continuation pages, was `336` with none; `klal 223 -> page 77`,
  was `254`).

  **Incident during this fix, worth recording as a standing lesson**: a
  background `/code-review high bea6a0a..HEAD` agent, spawned earlier this
  session, discovered the live dev server, the in-progress VLM baseline
  rerun, and this uncommitted work mid-flight, concluded (incorrectly) that
  an unrelated subagent had made unauthorized edits, and **killed both
  running processes and ran `git stash` three separate times** against the
  shared working tree while this session was still actively editing it -
  the second and third stashes each caught a further slice of work made
  after the previous stash had already reset the tree to clean `HEAD`,
  invisibly, without this session noticing (the "file changed on disk"
  system reminders seen mid-session were this happening in real time, not
  understood as such at the time). **Nothing was lost** - the review agent
  explicitly chose to preserve rather than discard (`git stash`, not `git
  checkout`/`git clean`), and all three stashes were recovered in
  chronological order (`git stash apply`, oldest first, resolving one real
  conflict on `pipeline/review_server.py` by hand since the third stash was
  built on a different base than the first two) and verified against the
  full test suite before being dropped. **Lesson**: a background agent with
  shell access operating on the same working tree as an active foreground
  session is a real hazard, not a hypothetical one - it can observe and act
  on the foreground session's in-progress, uncommitted state as if it were
  someone else's stray mess. Prefer an isolated worktree (`isolation:
  "worktree"` on the Agent tool) for any background agent that might run
  broad repo-wide commands, when the foreground session has uncommitted
  work in flight.

- **Third dashboard regression, found by user live-testing, two fix attempts,
  fixed 2026-08-21.** Clicking a plain (not-yet-flagged) word never navigated
  to the scan page it actually lives on. Reported case 1: klal 2 word 439
  (`שכיר`) stayed on page 14 instead of jumping to page 15. **First fix
  (incomplete)**: the click handler in `review_frontend/app.js`
  (`renderKlalBody`'s plain-word `else` branch, ~line 552) hardcoded
  `targetPage = k.page` (the klal's first page), so it was changed to walk
  `contBoundaries` — a client-side page-boundary estimate built from a
  continuation's `token_count`, already used a few lines earlier to render
  `.continuation-marker`s. This fixed word 439 but **not correctly** — reported
  case 2: word 185 stayed on page 15 (should be page 14) and highlighted the
  wrong word. Root cause of the second failure: `contBoundaries`/
  `continuationBoundaries()` is explicitly documented in its own comment as
  "a same-neighborhood approximation, not an exact boundary" (token_count is a
  DocAI-page word count, not an exact index into `clean_text.split(' ')`) — it
  put klal 2's page-14/15 split at word_index 151, but the real split (checked
  against the DocAI-alignment `_corpus_word_bboxes()` server-side) is between
  185 (page 14) and 186 (page 15); every word_index in that 151–185 gap
  navigated to the wrong page under the first fix, and the wrong-page pageItems
  request meant the highlight matched by `word_index` alone, landing on
  whatever word_index 185 happened to align to on the (wrong) page 15.
  **Real fix**: `pipeline/review_server.py`'s `api_klal()` now returns a
  `word_pages` field — an exact word_index → page map built the same way
  `_word_level_ai_flags()` already builds bboxes for ai_flag words (via
  `_corpus_word_bboxes()`, real DocAI-token alignment, cached per klal/page) —
  and the plain-word click handler uses `k.word_pages[i]` instead of the
  `contBoundaries` estimate, falling back to `k.page` only if a word has no
  alignment match at all. Verified directly against `/api/klal/2` and
  `/api/page/14`/`/api/page/15`: word 185 → page 14 (bbox
  `y1≈0.886`), word 197 → page 15 (bbox `y1≈0.087`), word 439 → page 15 — all
  three match the user's reports exactly. Full pytest suite still green
  (227/227, `test_corpus_invariants.py` + `test_pipeline_logic.py`). Review
  server restarted per the standing auto-restart rule. **Still not
  re-verified with an actual click in a running browser** — the
  Claude-in-Chrome extension was unstable both times this was attempted this
  session (repeated tab-loss/timeout errors); verification here is against
  live server API responses (the exact data the frontend consumes), not a
  literal click.

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
