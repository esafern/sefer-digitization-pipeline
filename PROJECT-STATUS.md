# Project Status — current state

## TL;DR

_Current state only. Every claim here is measured, not remembered; the dated
evidence for each is in `PROJECT-STATUS-HISTORY.md`._

**What the corpus is.** The 667 klalim are ***Klalei HaGemara* in its entirety** —
the work's part one, scan pages 14–247, closing with `סליקו כללי הגמרא` on page
247. `part1/2/3.json` are three FILE CHUNKS of that one part (klalim 1–222,
223–444, 445–667), **not** the work's three parts. *Klalei HaPoskim* (pages
254–291) and *Klalei HaDinim* (292–329) have never been extracted — 76 pages.
Corrected 2026-08-25 against the printed page; the docs had said otherwise since
they were written.

**How much text actually exists.** **596 of 667 klalim carry real text**
(~188,000 words). The other **71 hold a generated placeholder** (`רנ כלל 250`),
all in klalim 223–667 — see open item 16. 44 were reconstructed from the DocAI
token stream and are flagged as unreviewed machine output; **12 of those carry
confirmed page-furniture damage — see open item 20**, which is the one thing in
this file that should be read before quoting the 596.

**Where the review stands** (klalim 1–222, the reviewed third):

| | |
|---|---|
| page-to-klal alignment | 222 / 222 trusted |
| flagged word positions | 1,061 across 185 klalim |
| …made of | 538 pipeline candidates + 364 consensus disputes, 72 shared |
| open / decided / machine-resolved | see the dashboard — re-measure, don't quote from here |
| witnesses read against the ink | DocAI, a VLM sampled twice, Surya at 300 DPI |

**What the witnesses are worth, measured.** VLM 93.3% token accuracy, Surya
89.9% mean agreement (222/222 coverage), Tesseract 3.8% on disagreements — the
last is why it is being retired (item 3a). **P(consensus correct | two distinct
engines agree) is 26–41%**, so agreement routes attention and the ink decides;
auto-approval on consensus is indefensible at any threshold this data supports.

**The binding constraints.** The Parts 2-3 gate (`START_HERE.md`) still holds:
no `part2.json`/`part3.json` correction may be applied. Recording a decision and
applying it to the corpus remain two separate, deliberate steps.


## Open items

00. **[ASSIGNED TO THE USER, 2026-08-24 — "I will do #2 - remind me
    periodically until I remember"] Surya block mis-assignment: 4 klalim carry a
    neighbour's text.** NOT to be attempted by an agent without the user saying
    so: three separate attempts to fix it by tuning
    `split_block_across_klalim()` have all regressed the corpus and been
    reverted, the worst costing 29 klalim their coverage and 2.3 points of mean
    agreement. **Any LLM instance reading this file should mention this open
    item to the user in its session summary until it is closed.** Details: (swept
    2026-08-24, extent documented per the standing rule). klal 162 (page 59,
    NEW - a regression from the 300-DPI re-render, 0.68 -> 0.09) and its
    knock-on klal 163; klalim 8, 88 and 202 are pre-existing. Root cause for
    162: the block opening `קסב` sits inside klal 161's recorded region, so it
    covers one klal, falls through to centre-assignment, and the whole page
    shifts by one - the marker and the derived region geometry disagree. Two fix
    attempts reverted rather than risk the 190 klalim the re-render improved;
    this wants a scoped change with its own before/after. Context: the same
    re-render cut mis-assignment from 15 klalim to 4.
    **CONFIRMED AGAINST THE INK 2026-08-25 — this item is 2 klalim, not 5.** The
    detector behind it ("the klal's Surya text opens with a neighbour's marker")
    cannot tell a mis-assigned block from a MISREAD marker glyph. Klalim 8, 88
    and 202 agree with their own stored text at 87%, 89% and 93% (genuinely
    mis-assigned klal 162 sits at 9%), and rendering all three markers at 400 DPI
    settles it: the page prints `ח`, `פח בשבת` and `רב היכא`, where Surya read
    `ה`, `פה`, `רא`. **All three are marker misreads; their blocks are correctly
    assigned.** Two are the ח/ה pair behind klal 1's `דנראח` typo. **Only klalim
    162 and 163 are really mis-assigned**, so the remaining work is a marker-read
    fix, NOT another pass at `split_block_across_klalim()` (Lesson 31). Nothing
    to review in klalim 8/88/202 on account of this item.

0. **STANDING RULE, added 2026-08-24 (user directive): never fix one instance —
   sweep the corpus for the class.** Whenever you find and fix an issue, review
   the whole corpus for other instances of the same failure, in the same turn.
   If you fix it, report how many existed and that the count is now zero. If you
   do NOT fix it, sweep anyway and document the other instances together with
   the open issue here — an open item reading "klal 91 has X" when 104 klalim
   have X looks handled and is worse than no entry. Full rule in `START_HERE.md`
   Part 2 ("Never fix one instance"); Lesson 28.

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
   on anything else). **Tesseract provenance re-confirmed 2026-08-25 from the
   code (`verify_reconstruction_witness.py:79`, `tesseract -l heb`), with a
   recommended replacement measured the same day — see item 3a.**

3a. **RECOMMENDED 2026-08-25 (user-requested, measured, not implemented):
    replace the Tesseract leg with Surya, keep the VLM as a gated second
    witness, and keep semantics as triage only.** All three klalim are already
    covered by both at 300 DPI, so this retires a generator rather than building
    one. On the same 4,286 words: Tesseract flags 419, Surya 218, the
    stability-gated VLM 85, and the two agreeing 25 (already live). On the
    queue's own adjudicated positions (anchored subset), Surya catches **7 of 10
    NEITHER cases (70%)** and 4 of 13 where Tesseract beat DocAI, while firing on
    only 15% of the 306 positions that were Tesseract noise — roughly **3× the
    signal-to-noise**. The VLM must not be primary here: it is the adjudicator's
    own model family (Directive #1; the arbiter backs consensus 52% when the VLM
    is in it vs 30% when not). A semantic pass cannot be a witness at all — the
    defect it must catch (a reconstruction stitched from the wrong place) reads
    as fluent Hebrew. **Do not delete the queue**: Surya + gated VLM would have
    missed about half the positions where the arbiter overruled DocAI, so retire
    the generator and keep the findings, filtered per item 4. Two further facts
    from that check: Tesseract read the **1.1–1.2 MP** cached page renders (the
    same starvation that cost Surya 18 points), so its 3.8% is a floor rather
    than a fair number; and **90 of the queue's 419 `word_index` values no longer
    anchor** to their `docai_reading`, so any index-keyed analysis must anchor
    first. Full tables in `PROJECT-STATUS-HISTORY.md`.

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

8. **CLOSED 2026-08-25 — insert candidates DO have scan boxes, and the ones
   they had were wrong until today.** This item asked whether to build a bbox
   estimate for `opcode: insert` candidates (stored text a fresh DocAI pass
   found no token for, so there is nothing to crop). **It was built 2026-08-21**
   — `estimate_insert_bbox()` in `build_corrections_dataset.py` — and this entry
   was never updated, which is why it still read "awaiting a decision".
   **Today it also got fixed**: it unioned the DocAI tokens either side of the
   gap, which is a tight band only when both sit on the same printed line, and
   at a klal's opening marker the gap IS a line break — so 21 of 40 insert
   candidates carried a box spanning two lines and most of the page width
   (median 0.382 of the page against 0.039 for an ordinary word box; 26 of the
   40 sit at word_index 0). Reported by the reviewer on klalim 3 and 4 as "the
   box is very large, including the bottom of klal 2". After the fix: median
   0.073, max 0.123, zero boxes wider than a quarter page.

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

12. **MEASURED 2026-08-23: P(consensus correct | 2 distinct engines agree)
    is ~26-41%, not the >99.9999% the plan claimed.** Auto-approval on consensus
    is indefensible at any threshold this data supports; consensus is a TRIAGE
    signal, not a decision procedure (`tools/estimate_consensus_posterior.py`).
    Dropping catalogued ligature artifacts barely moves it (41%→39%), so a bigger
    artifact catalogue will not rescue the rule. **Second finding: the
    circularity gap now has an effect size** — where the VLM is one of the
    agreeing engines the Gemini arbiter backs consensus 52% of the time, versus
    30% where it is not. That 22-point spread is what Directive #1's violation
    costs in practice.

16. **71 of 667 klalim still hold a placeholder instead of text** (was 115;
    **44** reconstructed by `tools/reconstruct_placeholder_klalim.py`,
    user-authorised, each flagged as unreviewed machine output — 12 of them
    rewritten 2026-08-26 after the page-furniture damage in item 20). All are in
    klalim 223–667. Re-measured 2026-08-26 from the tool's own refusal report, not
    remembered: **44 have no located gematria marker** and **13 have no next
    marker to bound them** — marker-trace work, not extraction work — while 8 are
    blocked by the corpus invariants (a catchword duplicated at the seam in 7,
    page-header furniture in 1) and 6 by the lexical gates. The reconstructions that DID land are extraction output,
    never read by a human: the gates reject a broadly-wrong span but cannot see a
    scramble buried inside an otherwise good klal.

19. **CLOSED 2026-08-26 — the review was finished in three scoped passes; see
    item 21 for what it found.** The original entry is kept below for the record
    of how it failed. The re-run followed the brief in
    `scratch/NEXT-SESSION-PROMPT.md`: source files only, three separate `high`
    passes rather than one `max` pass over 99 files, run one at a time. All
    three completed. Every parked finding was verified by running something
    before being fixed, and **two did not survive that**: `open_count` is not a
    dead field (a corpus invariant test consumes it), and the claim that 7
    klalim carry a live `needs_revisit` flag over placeholder text is false
    (their latest flag is closed).

19a. **[superseded, kept for the record] CODE REVIEW 2026-08-26 ran out of budget twice; 3 of ~10 angles finished
    and their 21 findings are parked in `CODE-REVIEW-2026-08-26.md`.** One is
    confirmed and fixed: `reconstruct_placeholder_klalim.py` sliced a
    reading-order token list with `marker_position`, a RAW array index, and **6
    of the 51 klalim written 2026-08-25 took a boundary from the wrong token**
    (commit `930ce76`; corpus reverted, tool fixed, reconstruction redone).
    **The rest are unverified angle output and no correctness angle completed**,
    so this range has had a reuse/efficiency/simplification pass and NOT a
    correctness pass. The remaining leads cluster: three more copies of the
    `word_freq.json` loader and of `is_placeholder`, a header regex that does not
    match the invariant it claims to enforce, `api_page()` re-parsing the 1.8 MB
    decision log 25× per request, and `open_count` served with nothing rendering
    it. **Do not re-run this as one max-effort review over 99 files** — see that
    file's header for why it died.

20. **CONFIRMED 2026-08-26 — the page-seam cleaner in
    `reconstruct_placeholder_klalim.py` writes the SCANNER WATERMARK into corpus
    text: `Digitized by Google` is embedded in 12 klalim** (250, 290, 333, 357,
    380, 385, 414, 442, 553, 580, 616, 665), every one of them exactly
    reproducible from the tool, so this is that tool's output and nothing
    else's. Found by a correctness pass over the 2026-08-24/25 range; **all 289
    gated tests pass with the damage in place**, because
    `test_no_page_header_contamination`'s regex only matches the HEBREW running
    header and the watermark is Latin. Swept the whole corpus per the standing
    rule: 12 klalim, all in 223-667, none in reviewed Part 1.

    Mechanism, verified step by step on klal 616 (page 220 -> 221). The Google
    Books footer `Digitized by Google` sits between the catchword at the foot of
    one page and its repetition at the head of the next. `strip_page_furniture()`
    keys on `hebrew_letters_only()`, which maps every Latin token to `""`, so the
    footer is not furniture to it and survives. Three knock-on defects follow
    from the same run:

    - **`drop_seam_duplicate()` is defeated, and separately fires on the wrong
      pair.** It compares only the two tokens either side of the seam index, and
      the watermark now sits between them, so the duplicated catchword survives
      in **3 klalim** (333 `יש ... יש`, 380 `להאמינה ... להאמינה`, 442
      `דהתם ... דהתם`; klal 665 repeats `מחבירו` around a folio). Worse, it
      compares `hebrew_letters_only()` forms, and **two different non-Hebrew
      tokens both normalise to `""` and therefore compare EQUAL** - on klal 616
      that deleted the real folio token `104` as if it were a duplicate.
    - **The folio rule deletes real text.** The token after a header run is
      dropped if it matches `[\d\u05d0-\u05ea"'׳״]{1,5}`, which is *any* Hebrew
      word of 1-5 letters, not a numeral. Traced all 12 firings: 11 removed a
      genuine folio or header word, and **1 removed real text - klal 616 lost
      `אכיל` from `ורב היכי אכיל בשרא`**, because page 221 prints its folio as
      Arabic `104` *before* the header, leaving the first body word where the
      rule expects the numeral. Token geometry settles every case cleanly and is
      the signal the rule should use: every genuine folio sits at relative-y
      <=0.006, the deleted `אכיל` at 0.032.
    - **A running-header word survives in klal 580** (`יר מראכי`), which the
      pytest invariant does not match either - it requires `כללי` to follow.

    **STILL OPEN, and deliberately untouched: 8 more klalim carry the same page
    furniture from an EARLIER extraction, not from this tool** - 279, 368, 415,
    549, 576, 663 (a bare Arabic-digit folio) and 371, 645 (a bare `מלאכי`).
    Confirmed by provenance, not inference: all 12 watermark klalim carry a
    `reconstruct_placeholder_klalim.py` revisit flag and **none of these 8 do**, so
    the reconstruction tool did not write them and re-running it cannot fix them
    (it only fills placeholders, and these hold text). They are `part2.json` /
    `part3.json` edits like any other and need their own go-ahead under the Parts
    2-3 gate. The new Latin-script invariant does NOT cover them - their furniture
    is Hebrew or digits, not Latin - so they are recorded here rather than caught
    by a test. Extent is swept and exact: 8, all in 223-667, none in Part 1.

    **THE TOOL IS FIXED; THE CORPUS IS NOT.** Landed 2026-08-26: a refusal gate on
    any Latin-script token (re-judged against the 12 - **all 12 are now refused**,
    so the fixed tool would never have written them); `drop_seam_duplicate()` no
    longer treats two different non-Hebrew tokens as equal; the folio rule now
    tests token GEOMETRY instead of spelling (**78 -> 45 deletions, 33 real words
    preserved**, every genuine folio still removed - the separation is clean, folios
    at relative-y <=0.006 against `אכיל` at 0.032); and `is_watermark()` moved to
    `corpus_io.py`, since it already existed in `build_corrections_dataset.py` and
    that is exactly why the one tool that writes corpus text from the raw stream
    never had it.

    **THE CORPUS IS FIXED TOO, 2026-08-26, user-authorised.** The user chose
    re-running the fixed tool over reverting to placeholders. Done in the
    documented two steps, the same shape as 930ce76: the 12 were reverted to
    placeholders, then `--apply` rewrote them. **All 12 came back clean** -
    watermark gone, the 6 duplicated catchwords gone, the folios gone, and klal
    616 reads `היכי אכיל בשרא` again. Yield unchanged at 596 klalim with text;
    each of the 12 carries a fresh unreviewed-machine-output revisit flag. Word
    counts moved only by what was removed (250: 242->238, 616: 994->991, 580:
    1027->1021). `rebuild_all.sh --skip-vision` and `sefaria_export/` both
    regenerated; the export now carries 0 Latin-script segments.

    Making the re-run possible needed two further fixes, both found by re-running
    the tool against these 12 rather than by reading it:
    - The watermark had to be STRIPPED, not merely refused - a refusal gate alone
      would have refused all 12 forever. Stripping a literal Latin footer is not a
      retune of the Hebrew furniture heuristic, so `_is_scan_furniture()` removes
      it before the run logic ever sees it.
    - **The folio is set at the page FOOT on some pages, not the head** - pages 86,
      126 and 246 print it at relative-y 0.93, right beside the watermark - so a
      header-band test missed three of them. A bare Arabic-digit token is now
      furniture wherever it sits: this work numbers in Hebrew letters, and the 222
      reviewed klalim of Part 1 contain zero bare Arabic-digit tokens.
    - `FURNITURE_WORDS` listed the OCR variants of the header's FIRST word
      (`יד/יר/יך`) but only the exact `מלאכי` for its second, so page 210's
      `יר מראכי` was a one-word run, fell under the run>=2 threshold, and left a
      running header in klal 580. The four forms the corpus invariant's own
      `מ[לר][אר]כי` admits are now all listed.

    **The invariant landed** (`test_no_scan_watermark_in_clean_text`): no klal text
    may contain a Latin-script token. Verified it can actually fail, per Lesson 25 -
    run against the pre-fix backup it reports all 12 offenders, against the live
    corpus 0. 319 tests pass.

21. **CODE REVIEW COMPLETED 2026-08-26 — three scoped passes, 26 findings
    triaged against the two parked reviews, 24 fixed, 2 refuted.** Method, because
    it is the part worth reusing: `/code-review high` over
    (a) `review_server.py` + `app.js`, (b) the three corpus-writing tools,
    (c) `repair_filters/` + `synthesize_multi_witness.py` — one at a time, source
    only. Every claim was reproduced by running something before being acted on.
    Findings both independent runs raised were the highest-yield; findings only
    one run raised were where the two refutations came from.

    **Fixed — correctness, in rough order of what they could have cost:**
    - `repair_word()` fabricated readings out of abbreviations. `hebrew_letters_only`
      strips gershayim, so `א"ה` (אבן העזר) was arbitrated as `אה` vs `אלה` and
      "repaired" to `א"לה` — not a word, an abbreviation, or anything DocAI read.
      **97 tokens in the live stream** (`א"ה`×73, `א"א`×20, `ש"א`×3, `וא"ה`×1). It
      feeds `docai_repaired`, which the frontend offers as a SELECTABLE reading,
      so one click would have written a fabricated word into the corpus carrying
      an engine's authority. Guarded on internal gershayim only, so the
      trailing-geresh case its own test protects still repairs. 0 reached the
      queue; 893 → 796 repairs stream-wide, all 97 of the difference being these.
    - **A Save with no option selected recorded a null decision — and had already
      done so four times** (klal 90 w4, 88 w1149, 164 w55, 2 w632; three on
      2026-08-24/25). `saveDisputedDecision()` falls back to `source='final_text'`,
      which a `delete` or `ai_flag` entry does not have, so it POSTed
      `chosen_text: null`. Those rows mark the word decided and answer its revisit
      flag while `apply_reviewer_decisions.py` can never promote them, and the log
      is append-only. Guarded in the client AND at the write site —
      `api_post_manual_decision()` has had exactly this check since it was written
      and `api_post_disputed_decision()` never got it. **The four existing rows are
      still there and still count as decisions; superseding them is a reviewer
      action, not a code fix.**
    - **`--apply` wrote the corpus and then crashed before recording a single
      revisit flag**, whenever `sefaria_reference_corpus/word_freq.json` is absent
      — which is a fresh clone, since it is gitignored. Absent cache ⇒ both lexical
      gates skipped silently ⇒ every located span written unchecked ⇒ `TypeError`
      formatting `None` into the flag note, after the write. Now refuses to
      `--apply` at all without the cache, and the notes are built before the write.
    - **12 klalim render a duplicate proposed insertion** (84, 88, 106, 114, 138,
      159, 164, 171, 175, 193, 211, 219 — including 219, the klal the newer block
      was written for): two blocks in `app.js` both rendered
      `gapsBefore[words.length]`, the newer one having superseded the older without
      removing it.
    - **An answered word-level flag rendered decided in the scan pane and nav badge
      and still open in the text pane**, on 5 standalone flags (klal 4 w199/w364,
      163 w427/w573, 167 w24) — `renderKlalBody` hardcoded the class instead of
      calling `wordState()`, so the 2026-08-25 `flag_answered` fix reached one pane
      of three. Klal 163 is the klal that fix was written for.
    - `drop_seam_duplicate()` compared `hebrew_letters_only()` forms, and two
      DIFFERENT non-Hebrew tokens both normalise to `""` and so compared equal —
      on klal 616 it deleted the real folio `104` as a "duplicate" of `Google`.
    - The folio rule deleted real body words: see item 20. Replaced with a
      token-geometry test; **78 → 45 deletions across all spans, 33 real words
      preserved** (`תלת`, `גבי`, `פליגי`, `דאית`, `רבי`, `דרב`, `היא`, `ושוב`,
      `בשם`, `דאפשר`, `היה`, `אכיל`…), every genuine folio still removed.
    - `_reinsert_nonletters()` put the restored ל after a trailing mark
      (`בצלא.` → `בצלא.ל`). Latent, 0 live occurrences.
    - `page_words()` raised `TypeError` on a DocAI page that was never extracted;
      `seam` was counted on the unfiltered token list and sliced a filtered one;
      a furniture run longer than the max was partially stripped, the opposite of
      what its comment says. All latent, all cheap.
    - The insert-bbox estimate clamped both edges at 1.0 independently, collapsing
      the box to zero width at the right page edge. Latent (0 of 40 today).
    - `docai_verdicts()`'s drift guard was **fail-open**: `words_by_klal=None`
      disabled it, and `validate_suppression_filters.py` — the harness whose whole
      job is measuring these filters — called it that way, so it was structurally
      measuring something production no longer does (Lesson 25's shape). Default
      now derives the corpus and guards; opting out is explicit.
    - The synthesizer told an operator "the stored text is correct in each" for a
      bucket that now includes positions where a reviewer's correction is recorded
      but NOT yet applied — i.e. exactly where the corpus is known to be wrong.

    **Fixed — the standing shared-module rule, which is where three of these came
    from:** `is_watermark()`/`WATERMARK_WORDS` and `is_placeholder()`/`PLACEHOLDER_RE`
    both moved to `corpus_io.py` (the watermark filter existed in
    `build_corrections_dataset.py` and nowhere else, which is precisely why the
    reconstruction tool wrote the watermark into 12 klalim; the placeholder rule was
    byte-identical in two files that are two halves of one decision — what gets
    rebuilt and what ships to Sefaria as empty). `reconstruct_placeholder_klalim.py`
    now uses `docai_filter.reference_frequencies()` instead of a third, unnormalised
    private loader (latent: 0 of 185,593 keys carry a non-letter today, fatal the day
    that cache is rebuilt keeping the marks), and `cio.save_part1()` instead of a
    third private `json.dump`. Its `HEADER_CONTAMINATION_RE` now includes the pytest
    invariant's own pattern verbatim — the two were **non-overlapping**, so the tool's
    stated contract ("a reconstruction that would fail the invariants is simply not
    written") was not enforced: `יר מראכי כללי הביח` passed the tool and failed pytest,
    i.e. damage committed first and found afterwards.

    **Fixed — the interactive hot path.** `GET /api/page/73` went **182.5 ms → 9.6 ms**;
    `/api/klal/88` 72.6 → 8.0 ms. Both parked reviews found the cause independently
    (2026-08-25 C1/C2, 2026-08-26 H9/H10/H11): the 1.8 MB decision log was re-parsed
    **25 times per request**. Memoized `_read_all()` on `(st_mtime_ns, st_size)` rather
    than restructuring two 250-line functions — the log is append-only, so any write
    changes both, and a decision recorded in one tab is still visible to the next
    request. Same treatment for the 187 KB `klal_page_regions.json` (6 parses per
    request). Verified before landing that no consumer mutates the shared records
    (0 of 2,153 rows) — and deliberately NOT applied to `_load_corrections()`, whose
    entries the API handlers DO mutate in place.

    **Fixed — three encodings of one rule.** `_word_pages_map()` (proportional),
    `_word_level_ai_flags()` (last-page-wins) and `_word_scan_position()`
    (first-page-wins) each resolved the same multi-page recurring-word collision
    differently; they disagree on **657 and 293 of the 943 colliding words**.
    Collapsed into `_word_bboxes_resolved()`. Nothing a reviewer sees was wrong
    today — 1 of 331 open flags sits on a colliding index and the answers happen to
    agree there, 0 of 203 manual corrections sit on one at all — which is luck about
    where the flags fell, not a property of the code.

    **Fixed — the Sefaria export.** `versionNotes` hardcoded "Klalim 1-222 … 223-667
    have not" even under `--part1-only`, where 223-667 are not in the file; it now
    derives from what is actually exported and **discloses the 44 machine
    reconstructions**, which for a public version file under a real citation address
    is the most load-bearing caveat there is. `--format sefaria --klal-id N` could
    never succeed (the version file addresses klalim by position in a dense 1..N
    array) and failed by blaming the corpus and recommending a flag that was already
    on; it now refuses up front for the real reason.

    **REFUTED — recorded because a wrong finding that looks handled is worse than
    none:**
    - "`open_count` is served with no consumer — Lesson 29's own pattern." It has a
      consumer: `test_nav_tristate_matches_what_each_word_actually_renders_as`
      asserts it never goes negative, which is the canary that caught the klal 88
      "−1" fix-on-fix arc. Kept, with a comment saying so.
    - "7 klalim (280, 430, 431, 432, 438, 539, 643) carry a `needs_revisit` flag
      describing a reconstruction while storing a placeholder." All 7 have a LATER
      flag with `needs_revisit: false` — they were correctly cleared when 930ce76
      withdrew their text. The finding read the flag's note without checking whether
      the flag was still open. The other half of that finding (232 ledger rows across
      51 klal ids) is true and is the append-only design working as intended.

    **Checked and left alone, with the reason:** `repair_word()` treats absence from
    the reference corpus as proof of corruption when `collapsed_freq == 0`, so
    `אוף` (Aramaic "also", 4 occurrences) repairs to `אלוף` ("chief") on the strength
    of 5 references. 13 tokens / 72 occurrences sit in that thin-evidence band and
    most are genuine repairs, so tightening it trades real repairs for this one —
    a threshold decision, not a bug, and Lesson 31 says hand it over rather than
    tune it. `synthesize_multi_witness.attach_scan_positions()` can take a box from
    an `insert` candidate whose bbox is an estimate (0 collisions today).
    `review_server.py` remains a 1,736-line module and
    `synthesize_multi_witness.py` still imports its private helpers — both real,
    both structural refactors that want their own session and their own before/after.

22. **CONFIRMED 2026-08-26 — the detectors that WOULD catch these errors are not
    wired to anything, and `lexicon.txt` cannot fail a word it learned from the
    corpus's own OCR.** Raised by the reviewer after hand-repairing three words in
    klal 84 that no dispute had flagged. Three words, three different causes, all
    verified by running the tools rather than reading them:

    **(a) `בחרא` -> `בחדא` (klal 84 w23) — the detector already finds it, today.**
    `tools/detect_real_word_substitution.py` prints exactly this candidate in its
    current output (`corrupt form 2x in Part 1; correction 331x independently
    attested`). It is `[STANDALONE]`: it prints to stdout, is not in
    `rebuild_all.sh`, and writes no `klal_flag` rows — so nothing routes it to the
    dashboard. **Of its 121 findings, 57 are invisible to a reviewer**, this one
    among them. That is Lesson 29 at the level of a whole tool: computed,
    correct, and shown to nobody. Context confirms the reviewer's reading —
    `תרי זמני או בחדא מסכתא או בתרי מסכתי` ("either in ONE tractate or in TWO")
    — so `בחדא`, not `בתרא`, despite `בתרא` being the commoner word overall
    (620x vs 331x). **Swept: klal 75 w608 carries the IDENTICAL `בחרא` error, is
    also unflagged, and is still uncorrected** (`אמר רב בחרא מלתא גופא`).

    **(b) `כסכתא` -> `מסכתא` (klal 84 w24) — two independent reasons it passed.**
    First, כ/מ is **not in `detect_real_word_substitution.py`'s `CONFUSION_PAIRS`**
    (15 empirically-observed pairs; this is not one). Adding it surfaces **20
    candidates in Part 1**, several obviously real (`אמילת`->`אכילת` 571x,
    `הבכות`->`הבמות` 114x, `עכדו'`->`עמדו` 148x). Second, and more important:
    **`כסכתא` IS IN `lexicon.txt`**, so no lexicon-membership check can ever fail
    it. `lexicon.txt` was built from THIS corpus's own OCR output, so it absorbed
    the error and now vindicates it — already documented for the ligature bug
    ("lexicon.txt cannot catch the ligature corruption - it contains it"), and this
    is the same hole in a second class. **Measured: 4,251 of its 19,015 entries
    (22.4%) have ZERO attestation in the independent reference corpus.**
    `בחרא` is in there too.

    **(c) `לא` -> `אלא` (klal 84 w8) — the ligature pass only ever ran in one
    direction, and this word is out of reach of all of them anyway.**
    `repair_filters/docai_filter.repair_word()` models the `ﭏ` sort dropping its
    **ל** (inserts a ל after an א: `אא`->`אלא`, `ושמוא`->`ושמואל`). It has no rule
    for the sort dropping its **א**, which is what happened here. A mirror sweep
    finds **3 such candidates in Part 1** — `שמול`->`שמואל` (klal 143 w684,
    `רב פפא בר שמול`, genuine, already flagged), klal 30 w1521 `תשל` (uncertain,
    unflagged), and klal 7 w677 `ויגל`, which is a **false positive**: the text is
    Psalms 16:9 `לכן שמח לבי ויגל`, where `ויגל` is correct. So the direction gap
    is real but small in Part 1 — 1 confirmed, 1 open, 1 false.
    **The harder point: no detector in this repo could have caught THIS word.**
    All three (`repair_word`, `detect_real_word_substitution`,
    `detect_insertion_deletion`) gate on the stored form having ZERO independent
    attestation, and `לא` is attested **82,442** times. A real, extremely common
    word standing where a different real word belongs is invisible to every
    frequency arbiter here by construction; only context or the scan finds it.
    This is the honest answer to "I thought we did a pass to find all those":
    the pass was one-directional AND structurally blind to this shape.

    **Not fixed — each needs a decision, none is an agent's call.**
    **ALL THREE FIXED 2026-08-26, user-authorised ("push the ones that are real -
    check them all"). See item 23 for what was pushed, and for a correction to the
    "57 unrouted" figure above, which OVERSTATED the problem.

23. **CLOSED 2026-08-26 - every detector finding triaged against the independent
    witnesses; 15 real ones pushed, and the routing gap turned out to be far
    smaller than item 22 claimed.** Ran `detect_real_word_substitution.py` +
    `detect_insertion_deletion.py`, merged them to **262 distinct (klal, word)
    positions**, and cross-checked EVERY one against Surya, both VLM passes and
    DocAI: **50** where an independent engine reads the PROPOSAL, 149 where one
    reads the STORED form, 29 split, 34 with no reading there.

    **CORRECTION to item 22's "57 of 121 reach nobody".** That counted raw
    findings. Of the 50 that survive witness cross-check, **46 were already
    visible in the dashboard** - the multi-witness consensus pipeline routes them
    already, which is what it is for. Only **4** were genuinely missing. The large
    unrouted remainder is the UNCORROBORATED tail, which the witnesses actively
    contradict (149 of 262). The tools are not "computed and shown to nobody";
    their high-confidence output is largely already routed. Item 22's framing was
    wrong and is corrected here rather than quietly dropped.

    **Pushed as word-level flags (15), each read in context first, none applied to
    the corpus:** klal 10 w1 `איידו`->`איידי` (unanimous 3/3; the next word is
    `דאיידי`); 53 w218 `במשרו`->`במשהו`/`בבשרו` (engines split, needs the scan);
    74 w659 `בסרק`->`בפרק`; 167 w739 `מקטי`->`מקמי`; 117 w43 `כרתב`->`כתב`;
    152 w98 `בסרק`->`בפרק`; 169 w1074 `שרוא`->`שהוא`; 198 w892 `זלזה`->`לזה`;
    3 w262 `מאיין`->`מניין`; 177 w340 `למיפך`->`למיפרך`; 144 w907
    `בישרץ`->**`בישראל`**; 150 w684 `מקטי`->`מקמי`/`מקרי`; 81 w16
    `בתריתא`->`בתרייתא`; 210 w133 `כתרייתא`->`בתרייתא`; **75 w608 `בחרא` - the
    TWIN of the klal 84 w23 the reviewer hand-repaired**, found by the sweep for
    that fix.

    **Rejected after reading them in context - the detectors were wrong:**
    `אאמוראי` (א+אמוראי, a legitimate prefix, 2x in Part 1), `דאיך` (ד+איך, 4x),
    `ואוף` (Aramaic `אוף` = also, 2x), `למהרר` (the stored text is `למה"רר`, a
    title abbreviation), `רבואתא` x2 (a variant of `רבוותא`, 17x attested - the
    proposed `רבותא` means something else), `בבריתא` x2 (a defective spelling of
    `בברייתא`, not a misread letter), plus 10 positions where the "correction" was
    the word minus a legitimate Hebrew prefix or suffix (`דהרוצה` = ד+הרוצה).
    **And one where the proposal was wrong but the word WAS corrupt**: `בישרץ` was
    offered as `בשרץ` ("in a creeping thing") in a passage on the thirteen
    hermeneutical rules; context gives `ורבתה מחלוקת בישראל`, which is what was
    flagged instead. Frequency alone gets these wrong; context decides.

    **Pipeline fixes closing item 22's three causes:**
    - `detect_real_word_substitution.py` gained the **כ/מ** and **ח/ת** pairs, and
      its `MIN_INDEPENDENT_FREQUENCY` floor went **50 -> 40**, because
      `כסכתא`->`מסכתא` missed by exactly five occurrences (`מסכתא` is attested 45x;
      the reference corpus mostly writes `מסכת`). Measured before changing:
      124 -> 138 findings, the 18 gained the same quality as the rest, including
      klal 1's known `דנראח`->`דנראה`. The reviewer's `כסכתא` is now caught.
    - `repair_word()` now models the `ﭏ` sort dropping **either** letter. Two bugs
      surfaced doing it: an early `if "א" not in letters: return None` guard
      excluded the entire new direction (the surviving letter there is the `ל`),
      and `_reinsert_nonletters()` hardcoded the restored letter as `ל`, turning
      `שמול` into `שמולל`. A 2-letter minimum was also needed: without it the bare
      token `ל` "repairs" to `אל` **83 times** - two thirds of the new direction's
      output - purely because `אל` (4,624) happens to be four times commoner than
      standalone `ל` (1,154), which clears MIN_FREQ_RATIO by accident. After the
      guard: dropped-lamed unchanged at **796**, dropped-alef **43**, and only
      **4** reach the review queue, all `שמואל` variants, all genuine.

24. **REVIEWED 2026-08-26 (user-requested): the words that exist in Yad Malachi
    and in none of the 166 reference books.** Written to
    `lexicon_yad_malachi_only.json` - per word, its Part 1 count, every
    occurrence, and the nearest attested forms with edit type.

    `lexicon.txt` holds 19,015 entries; **4,251 (22.4%) are absent from all 166
    books (6.18M words)** - 1,261 present in Part 1, 2,924 only in gated Parts
    2/3, and 66 in no part file at all (stale rows). Narrowing to Part 1, 4+
    letters, no gershayim: **1,162 words**, of which **536 sit one edit from a
    form attested >=40x** and **386 of those are a hapax in Part 1** - the
    top-suspicion tier. The other **626 have no near neighbour** and are most
    likely genuine Yad Malachi vocabulary. (Re-measured after the 79-row purge
    below, and now reproducible: `tools/review_lexicon_only_words.py` writes the
    report, which had been produced by a throwaway script - the
    hand-maintained-derived-file pattern Lesson 13 forbids.)

    **Why this list exists at all:** `lexicon.txt` was built from THIS corpus's
    own OCR output, so it contains the errors and then vindicates them - `כסכתא`
    and `בחרא` are both IN it. Every check run against `lexicon.txt` is only as
    independent as `lexicon.txt`, which is not independent at all. Already
    documented for the ligature bug; **22.4% is the first measurement of how wide
    the hole is.** `tools/validate_lexicon_independent.py` exists to surface
    exactly this, and is read-only, standalone and wired to nothing.

    **PURGED 2026-08-26, user-authorised ("confirm and remove those"): 79 rows,
    each individually justified, 19,015 -> 18,936.** Two sets, deliberately kept
    narrow, and NOT the 4,251:
    - **66 orphan rows** - in `lexicon.txt`, zero attestation in the reference
      corpus, AND appearing in no klal of any part file. They cannot be Yad
      Malachi vocabulary, because the work does not contain them. Visibly junk
      (`דדסומתימאא`, `הבודאבר`, `ורנעשמרת`) plus **learned page furniture**
      (`מראכי`, `כרלי`, `כררי`, `הלמר`) - header words the lexicon absorbed before
      the header contamination was cleaned out of the corpus. Count now 0.
    - **13 confirmed-corrupt forms** - the OCR errors verified in context this
      session: `כסכתא`, `בחרא`, `כרתב`, `שרוא`, `בסרק`, `בישרץ`, `מקטי`,
      `כתרייתא`, `מאיין`, `למיפך`, `בתריתא`, `זלזה`, `איידו`. Precedented by the
      2026-08-15 purge of 24 dropped-lamed forms. (`במשרו` was already absent.)

    **`לא` was deliberately NOT removed**, though the reviewer repaired it at klal
    84 w8. It is attested **82,442** times - a real word that was simply wrong in
    that one position. The rule applied throughout: remove a form only when it has
    zero independent attestation, never merely because one instance of it was
    wrong. `כתרייתא` was checked separately and does qualify - its putative base
    `תרייתא` occurs nowhere at all, so it is a ב/כ misread of `בתרייתא` (120x), not
    a legitimate `כ`+noun.

    **Effect, verified:** all 13 now surface in
    `validate_part1_corpus_integrity.py` check 5 (Part 1 not-in-lexicon: 959
    distinct words), covering **22 Part 1 positions** that the lexicon previously
    whitelisted. Swept per the standing rule: **0 of those 22 are unflagged** - the
    15 pushed above plus existing flags and the reviewer's own decisions cover
    every one. Zero-attestation share moved 22.4% -> 22.0%, which is the honest
    size of the dent: the remaining **4,172** entries are the tier
    `validate_lexicon_independent.py` explicitly warns is "NOT a purge list".

    **SEFARIA'S DICTIONARIES ADDED AS A THIRD LEXICAL SIGNAL, 2026-08-26
    (user-requested).** `tools/lookup_sefaria_dictionaries.py` queries the public
    `/api/words/` endpoint (Jastrow, Klein, BDB - no key). This is a different
    KIND of signal from `word_freq.json`: that counts occurrences in 166 books,
    this asks a lexicographer whether a form is a word at all, so a rare-but-real
    Rabbinic word can be absent from 6.18M words of running text and still have a
    Jastrow entry. Jastrow is the dictionary of Talmudic Aramaic - this text's own
    register. 1,878 forms fetched and cached (one line per lookup, resumable).

    **The method was validated against known ground truth before its output was
    used, and the first version FAILED that check.** Stripping a leading particle
    to find a headword - the obvious mitigation for the endpoint matching
    headwords only - **destroys the signal**: 8 of 13 confirmed-corrupt forms
    "resolve" that way, because stripping a letter that is not a prefix lands on a
    different real word (`כסכתא` -> `סכתא`, a peg; `בחרא` -> `חרא`; `בישרץ` ->
    `ישרץ`). Dropped. On BARE forms the signal is clean in one direction only,
    and that asymmetry is the whole usable content:
    - **0 of 13 confirmed-corrupt forms have a dictionary entry** - so *having*
      an entry is strong evidence a form is real.
    - **7 of 8 confirmed-legitimate forms have no entry either** - so *lacking*
      one means almost nothing, since most words in running text are prefixed or
      inflected.

    Applied to the 549: **54 stored forms are dictionary words** and 4 more have a
    dictionary entry where the proposal does not - **58 confidently cleared**, the
    frequency-based suspicion simply wrong. 384 have a supported proposal and an
    unlisted stored form (consistent with corruption, not proof of it), 107 give
    no signal.

    **It also caught one of this session's own flags.** klal 177 w340 was flagged
    `למיפך` -> `למיפרך`; the dictionary has **`מיפך` (`מֵיפַךְ`, to reverse) and
    nothing for `מיפרך`**, so the stored form is most likely the legitimate
    ל+מיפך. The proposal is retracted in a superseding ledger entry and the flag
    left open. Exactly what a third, differently-failing signal is for (Lesson 9).

    **REVIEWABLE 2026-08-26 (reviewer: "are the 384 words flagged? how can i
    review?" - they were not).** 374 words occupying 626 corpus positions had no
    route to a human at all: only 63 positions were visible, **563 across 143
    klalim were not**. Fixed structurally rather than by flagging them:
    `build_lexical_defect_report.py` now runs as **stage 4b, BEFORE assemble**,
    and `merge_lexical_defects()` folds its sharpest tier into the review queue -
    the same "a witness contributes a source file the pipeline reads, it never
    edits the pipeline's own product" rule finding C1 established for the
    multi-witness synthesizer.

    **Deliberately NOT flags.** These entries are regenerated by every rebuild and
    disappear when the corpus moves under them; nothing is written to the
    append-only ledger. 563 permanent flags on unread material is precisely how
    the 1,496-flag queue happened (item 1). Widening or narrowing the tier now
    costs nothing and leaves no residue.

    **The tier is a documented knob**, `REVIEW_MIN_REF` in
    `assemble_corrections_dataset.py`, currently **500** - the proposal must be
    attested >=500x and the stored form must occur once here. That yields **56
    entries across 36 klalim** on a queue of 883 (+6%). Measured alternatives:
    >=200 gives 111 positions, >=40 gives 219, no floor gives all 563 - a 53%
    larger queue of material nobody has read. Positions a human has already ruled
    on are skipped, so no entry can shadow a decision.

    Two of the repo's own gates caught real defects in this while it was being
    built, which is the system working: the provenance invariant refused entries
    from a source it did not know (they would have been destroyed by the next
    rebuild), and the entry-shape invariant refused a proposal carried in a field
    **nothing renders** - Lesson 29, in code written the same day it was cited
    repeatedly. The proposal is now its own option card in the panel, labelled
    "not an engine reading", and attributed via `lexical_source` exactly as a
    consensus dispute is attributed via `consensus_engines`.

    **Still not done:** the ~500 positions below the tier remain unread, and the
    dictionary cannot settle them - it is silent on prefixed forms by
    construction. Lower `REVIEW_MIN_REF` to surface more; frequency alone
    demonstrably gets some wrong (see `רבואתא`, `בישרץ`).

    **Noticed while here, pre-existing, NOT addressed:**
    `validate_part1_corpus_integrity.py` check 2b reports **7 non-Hebrew
    characters** sitting in Part 1 text - a Greek `Π` (klal 39 w252), three `&`
    (klal 69 w338, 77 w11, 167 w24), two `!` (klal 66 w112, 74 w443) and a `;`
    (klal 176 w694). The new `test_no_scan_watermark_in_clean_text` invariant does
    NOT catch these: it matches `[A-Za-z]`, and none of these are Latin letters.
    They are flagged as DATA issues needing scan verification, and widening the
    invariant would make `rebuild_all.sh` fail on all 7 - a decision, not a
    default.

25. **RETROSPECTIVE 2026-08-26 (user-requested): were today's fixes real, and
    were they repaired structurally or patched once?** Audited against the code,
    not against how the fixes were written up (Lesson 19). Every issue below was
    reproduced before being fixed, so "real" is not in doubt for any of them;
    the interesting column is the second one.

    **Repaired structurally - a future occurrence is now caught by something:**

    | issue | what makes it not-a-one-off |
    |---|---|
    | scan watermark in 12 klalim | new GATED invariant `test_no_scan_watermark_in_clean_text` catches the class from ANY writer, not just this tool; `is_watermark` moved to `corpus_io` |
    | corpus word boxed on a page header (8 klalim) | `header_furniture_indices()` in `corpus_io`, used by the one alignment both the server and the synthesizer share + new gated test |
    | end-of-klal gap marker drawn twice (12 klalim) | new gated test asserting only one renderer exists |
    | Save with nothing selected wrote a null decision | guard at the SERVER write site (not just the client) + new test asserting BOTH POST handlers agree |
    | `repair_word` fabricating readings from abbreviations (97 tokens) | fixed in the shared filter + new test |
    | ligature pass running in one direction only | both directions + new test covering all three sub-bugs it exposed |
    | 1.8 MB decision log parsed 25x per request | memoized at the source (`_read_all`), so every present and future caller benefits |
    | `is_placeholder` / `FURNITURE_WORDS` / `WATERMARK_WORDS` duplicated | all three consolidated into `corpus_io`, the module that exists for exactly this |
    | **detectors that found real errors and told nobody** | **now pipeline stage 5b** - `build_lexical_defect_report.py` regenerates `lexical_defect_report.json` on every rebuild (299 candidates / 96 klalim). They cost 0.1s; the reason given for leaving them out never existed. |

    **Honestly one-off, and here is what would make each structural:**
    - ~~**The lexicon purge (79 rows) is a data edit with no gate behind it.**~~
      **CLOSED in the same pass that identified it.** `lexicon.txt` has no
      generator in this repo and nothing stopped it re-absorbing the OCR errors
      it had just been purged of - the same file was purged by hand in
      2026-08-15 and again 2026-08-26, and neither purge left anything behind to
      hold. `test_lexicon_does_not_whitelist_a_known_corrupt_form` is now in the
      gated suite, listing all 14 confirmed-corrupt forms. Verified it can
      actually fail, per Lesson 25: re-appending `כסכתא` fails the suite,
      removing it passes. Adding to that list is now the documented way to make a
      confirmed reading stick.
    - **The 15 pushed flags and the 12 rewritten klalim are one-off by design** -
      they are review items and corpus content, not mechanisms. Correct as such.
    - **The folio-geometry rule and the `drop_seam_duplicate` empty-string fix
      have no regression test.** Both are inside
      `reconstruct_placeholder_klalim.py`, which no test exercises at all; the
      corpus invariants catch their OUTPUT only if a bad reconstruction is
      actually written. The refusal gate makes that unlikely, not impossible.
    - **The export's `versionNotes` scope fix has no test** either; it would be
      caught only by someone reading a shipped version file.

    **Still standing from today, not fixed:**
    - **4 null-decision rows remain in the ledger** (klal 90 w4, 88 w1149,
      164 w55, 2 w632). The guard stops new ones; it cannot remove these, because
      the log is append-only. They still mark those words decided. Superseding
      them is a reviewer action.
    - **~475 lexicon-only Part 1 words corroborated by frequency alone are
      unread** (item 24).
    - **8 klalim carry pre-existing page furniture** from an earlier extraction,
      under the Parts 2-3 gate (item 20).
    - **7 non-Hebrew characters in Part 1** that the new invariant does not match
      (item 24).

26. **RESOLVED AGAINST THE SCAN 2026-08-26: the 7 non-Hebrew characters are not
    one thing, and DELETING them would be wrong for four of them.** The reviewer
    asked whether they could simply be removed. They were rendered from
    `images/pdf_pages` at 4x and read directly (Lesson 14/30 - render and look,
    do not infer). Every one is now flagged at its word index with the reading.

    | klal / word | stored | what the page actually prints | action |
    |---|---|---|---|
    | 69 w338 | `&` | `כגון ﭏ אלהים ה'` — a list of DIVINE NAMES | replace with `אל` |
    | 77 w11 | `&` | `נוטה ﭏ הודאי` | replace with `אל` |
    | 167 w24 | `&` | `פנים ﭏ פנים` — the standard idiom | replace with `אל` |
    | 74 w443 | `!` | `ע"ב ב'.` — a geresh then a period | replace with `.` |
    | 39 w252 | `Π` | the printed FOLIO at the top of page 28 | delete |
    | 66 w112 | `!` | a short mark between `ב"ד` and `חבירו`, unidentified | needs a human eye |
    | 176 w694 | `;` | a semicolon-like mark IS printed there | probably correct as transcribed |

    **The three `&` are the alef-lamed ligature `ﭏ` losing BOTH its letters at
    once** - the same worn sort behind Lesson 24's dropped-lamed bug and behind
    `שמול`->`שמואל`, failing a third way. Its shape genuinely resembles an
    ampersand, which is why DocAI produced one. So this is not a stray-character
    problem: it is the ligature problem again, and deleting the `&` would have
    silently removed the word `אל` from three klalim.

    **Why they were not removed directly:** corpus text is never hand-edited
    (`START_HERE.md`, single-source-of-truth rule). Each is recorded as a
    word-level flag with the scan reading; `apply_reviewer_decisions.py` promotes
    them once the reviewer rules.

27. **NEW 2026-08-26 - PART 1 CARRIES PAGE-SEAM FURNITURE TOO, not just the
    reconstructions.** Found by sweeping for the class behind klal 39's `Π`
    (standing rule), which turned out to be a folio sitting next to page 27's
    CATCHWORD. Swept all of Part 1 for near-duplicate word pairs at a page
    boundary: **3 klalim**, all confirmed against the DocAI token stream at both
    pages.
    - **klal 39** w251-253: catchword `דבכולהן` + folio `Π` + the real `דבכולהו`.
    - **klal 74** w414-418: page 35's catchword `אמר` plus a duplicated `רבא אמר`
      - the corpus stores `אמר רבא אמר רבא אמר רב יהודה` where the page reads
      `אמר רבא אמר רב יהודה`. Two spurious words.
    - **klal 210** w64-67: `דהלכה : לא דהלכה כקמייתא` - the printed folio **`לא`
      (31)** between two copies of the catchword. **Note this folio is a HEBREW
      NUMERAL**, so the bare-Arabic-digit rule that cleaned the reconstructions
      cannot see it, and neither can the Latin-script invariant.
    All three are flagged. This is the same defect class as item 20's, in the
    REVIEWED third of the corpus, from an extraction that predates this session.
    The existing `validate_catchword_continuity.py` checks that catchwords MATCH
    across a seam; nothing checked whether one ended up inside `clean_text`.

28. **MEASURED 2026-08-26 - the `ai-semantic-spotcheck-round4` flag pass (242
    word-level flags, written 2026-08-18) has a real noise floor, found because
    the reviewer read one.** Report: klal 66 w67, "the suggestion is nonsensical
    and the explanation is gibberish". Both true - it proposed `אמרה` -> `נקראת`
    because of a "doubled final tav", and **`אמרה` contains no tav at all**, while
    `התורה אמרה` is a standard phrase with `אמרה` attested 1,785x. Flag retracted.

    That prompted a measurement of all 238 still-open flags from that pass,
    against the corpus and the independent reference corpus:

    | | |
    |---|---|
    | plausible or arguable | **177** |
    | suggestion is the SAME word - proposes nothing | **42** |
    | note describes a word no longer at that index | **14** |
    | suggestion unrelated AND the stored word is common | **5** |

    - The **42** self-suggestions (`איהו`->`איהו`, `דאם`->`דאם`, `עוד`->`עוד`) are
      pure noise. `suggestionIsPlausible()` already hides the SUGGESTION at display
      time, but the FLAG still lights the word red, so the reviewer is sent to a
      word with nothing to decide.
    - The **5** unrelated ones are the reported class: klal 66 w67
      `אמרה`->`נקראת`, klal 66 w120 `הרי`->`ע"פ` (**zero letters in common**, and
      `הרי` is attested 15,557x), klal 200 w144 `ועל`->`אלו`, plus klal 94 w188 and
      217 w510 which propose the literal `??`.
    - The **14** drifted ones are the good case in disguise: the note names the
      OLD reading and the corpus already holds the corrected one (`אכל` -> `אבל`,
      `ישרץ` -> `ישראל`). **But only 6 of the 14 render as answered**, so **8 flags
      are still lit red on words that were already fixed.**

    **THE "UNRELATED" BUCKET IS NOT NONSENSE - IT IS MIS-INDEXED, and that is
    worse.** The reviewer read the second one (klal 66 w120, `הרי` -> `ע"פ`,
    reason "ס for פ", citing the phrase `אף על פי שהניח`) and said "the note is on
    the following dispute - ayin-peh". Exactly right. **The note's real target is
    w135**, which stores `ע"ס` inside `אף ע"ס שהניח` - the very phrase the reason
    quotes, 15 words from where the flag was filed. Rendered page 34 at 4x and
    read it: **the page prints `אף ע"פ שהניח` with an unmistakable peh.** So the
    2026-08-18 pass FOUND a real ס/פ error, recorded it against the wrong word,
    and it then sat for eight days looking like gibberish. Recovered only because
    a human read the bad flag and recognised what it was about. w120 retracted,
    **w135 flagged and scan-confirmed**.

    **ROOT CAUSE FOUND 2026-08-26, on the reviewer asking whether I had actually
    looked for one. I had not** - I fixed the two instances and stopped at
    "mis-indexed", which is a symptom. The cause is an **OFF-BY-ONE confined to
    the 2026-08-18T20:36 batch**: some corrections were attached to the word
    BEFORE their real target. The reviewer's own words were the diagnosis - "the
    note is on the following dispute" - and I under-read them as a description
    rather than a mechanism.

    **Scope, measured per batch** (does a flag's suggestion plausibly fit its own
    word?): 20:36 = **96%** (133/139), and every later batch = **100%**. So this is
    not a broken pass; it is **6 items in one batch**, four of which landed in
    klal 66, which is why the reviewer hit two of them in a row.

    | flagged | note really belongs to | outcome |
    |---|---|---|
    | klal 92 w439 `דבבעיות` | w440 `או` -> `אלו` | **real error, now flagged** |
    | klal 200 w144 `ועל` | w145 `או` -> `אלו` | **real error, now flagged** |
    | klal 97 w387 `טועה` | w388 `דם` -> `הם` | real, already flagged |
    | klal 174 w17 `ד"ה` | w18 `אלא` | already correct - asks nothing |
    | klal 66 w67 `אמרה` | w82 `נקראתת` -> `נקראת` | re-emitted correctly at 22:11 |
    | klal 66 w120 `הרי` | w135 `ע"ס` -> `ע"פ` | **real, scan-confirmed** |

    All six retracted with a pointer to the true target. **Three real corpus
    errors were recovered from flags that read as gibberish**, and one of them
    (klal 66 w135) is confirmed against the ink.

    **What makes these unrecoverable by any detector here:** `או` is attested
    **37,981x** - a perfectly real word in the wrong place. Every lexical detector
    in this repo gates on the stored form being UNATTESTED, so this whole class is
    invisible to them by construction, exactly like the `לא`->`אלא` the reviewer
    found by eye in klal 84. The 2026-08-18 semantic pass is the only thing that
    has ever found them, which is an argument for re-running it correctly rather
    than retiring it.

    Two automatic recovery searches were tried first and **both were too noisy to
    trust** - matching the suggestion against every other word returns mostly
    punctuation artifacts, and matching the reason's cited phrase mostly finds
    legitimate citations of a CORRECT occurrence elsewhere (`משוס`->`משום` because
    `משום ר'` appears correctly at w80/90/173). What worked was the per-batch
    fit-rate above, which localises the damage instead of trying to repair it.

    **39 CLEARED 2026-08-26, user-authorised - and the count is 39, not 42,
    because I nearly repeated this repo's own bug while counting them.** The
    self-suggestion bucket was built by comparing `hebrew_letters_only()` forms,
    which STRIPS GERSHAYIM - the exact mistake fixed in `suggestionIsPlausible()`
    earlier the same day. Three of the "42" propose a real change that is invisible
    to a letters-only comparison: **klal 45 w21 `נלפ"קד` -> `נלפק"ד`** and **klal
    212 w40 `פ"יא` -> `פי"א`** (misplaced gershayim - the same two the display
    filter had been hiding, and the reason that filter was loosened), plus klal 194
    w420 `דמשסתמו` -> `דמשסתמו?`. Those three are LEFT OPEN. Only the 39 whose
    suggestion is the stored word character for character were cleared, each with
    a note stating that the word itself was not examined and is not asserted
    correct - only that the flag asked nothing.

    That pass now has **202 open flags, down from 238**. The 5 mis-indexed and the
    14 drifted are deliberately untouched: the mis-indexed ones have already
    yielded one scan-confirmed corpus error, and clearing them would destroy
    evidence.

29. **[AUDIT 2026-08-27] Heavy code review & Stage 5b / AI flag diagnostic audit.**
    Comprehensive review of the full pipeline + 28 commits (Aug 25-27) documented in
    `CODE-REVIEW-2026-08-27.md` and `LEXICAL-DEFECT-AND-FLAG-AUDIT-2026-08-27.md`.
    
    - **Confirmed Fixes from Prior Reviews**: Memoized JSONL decision loading & region caching
      (182ms -> 9.6ms latency), multi-page bbox collisions, raw token array index alignment in
      `reconstruct_placeholder_klalim.py`, scan watermark & folio geometry cleaner ($y \le 0.02$),
      abbreviation ligature guard in `docai_filter.py`, null decision POST prevention at write site.
    - **Critical Defects & Edge Cases Identified (Ready for Future Triage)**:
      1. `export_corpus.py:_apply_decisions_to_klalim()` drops manual insertions (`original_word is None`)
         which `apply_reviewer_decisions.py:320` handles via `apply_delete_insertion()`.
      2. Multi-word manual replacements (`len(chosen_text.split()) > 1`) change word count without
         setting `word_count_changed_klalim`, allowing subsequent same-run decisions in the same klal
         to apply at shifted word indices.
      3. `corpus_io.py:597` `trusted_klal_pages_with_continuations()` crashes with `AttributeError`
         if `klal_page_regions.json` is absent (`load_json` defaults to `None`).
      4. `review_server.py:453` `_corpus_bbox_cache` module-level dict is never invalidated on corpus edits.
    - **Stage 5b Lexical Defect Report Audit (`lexical_defect_report.json`)**:
      299 candidates across 96 Part-1 klalim (194 unflagged, 97 currently flagged, 8 already decided).
      True-positive examples identified against surrounding context (klal 179 w16 `יותה`->`יותר`,
      klal 30 w250/1263 `גכי`->`גבי`, klal 54 w730 `עלירם`->`עליהם`, klal 7 w252 `הלכרה`->`הלכה`,
      klal 30 w1115 `טיניה`->`מיניה`); false positives isolated (names like `זלמן`, terms like `בשרש`).
    - **Active AI Flag Alignment Audit**:
      455 active flags (144 klal-level, 311 word-level). For the 202 Round 4 flags: 187 (92.6%) are
      cleanly aligned at their exact stored word index; 12 are already resolved in stored text;
      only 1 experienced index drift (klal 43 w14 -> w17 `ממטונא`->`מממונא`); 1 is retracted (`למיפך`).

29. **DEEP LINKS ADDED 2026-08-26 (reviewer request): a URL now addresses a klal,
    or a klal and a word.**
    `http://127.0.0.1:8420/#klal=66` and `http://127.0.0.1:8420/#klal=66&word=135`.
    So a finding recorded in this file, in a report, or in a message can carry a
    link that lands on the exact word instead of "klal 66, count to 135". The part
    is derived from the klal id, not carried in the URL, so a link to klal 400
    works whether or not the reviewer is currently looking at Part 2. The address
    bar also tracks navigation (`history.replaceState`, so scrolling does not fill
    the Back button), which makes the current view copyable as-is.

    Word spans now carry `data-word-index`, which is what made this addressable at
    all. **The scroll observer was the hazard**: it calls `setActiveKlal` on
    whatever drifts into view, so a smooth scroll let it overwrite the
    destination mid-animation - measured, routing to klal 66 landed on 61. Routing
    mounts, jumps instantly, and holds the observer off until it has settled. Two
    Playwright regressions cover it.

30. **FIXED 2026-08-26 (reviewer: "klal 179 word 267 - clicking does not highlight
    word in scan page") - a defect introduced by item 24's own merge, the same
    day.** The lexical-defect entries were written with `page: None, bbox: None`.
    Two consequences: `api_page()` could not place them, so they fell through to
    the plain-word pass and rendered on the scan as ordinary prose rather than as
    flagged words; and the click fell back to the klal's START page. Klal 179 w267
    is on page 67 in a klal that starts on 66, so the scan showed 66 with nothing
    to highlight.

    Fixed at both ends: `merge_lexical_defects()` now fills the scan position from
    the same alignment the server uses, and the frontend gained `pageForWord()` -
    `corr.page`, then the server's `word_pages` map, then the klal's start page.
    The manual-correction handler had already worked around this privately; the
    disputed and flag handlers had not. All 56 lexical entries now carry a
    position, and klal 179 w267 serves as a `correction` on page 67.

    Swept for the class: **3 other entries** (klal 22 w48, 30 w120, 198 w403) have
    a `page` that disagrees with the alignment map - but each carries its own bbox
    and is servable on its claimed page, so all three highlight correctly. Their
    page came from a verified vision crop, which outranks the proportional
    heuristic; **deliberately not "fixed"**. A new gated invariant,
    `test_every_flagged_word_can_be_located_on_the_scan`, catches the real defect.

    **The 39 cleared flags were re-checked against this session's root cause**
    (item 28's off-by-one) and the file `cleared_flags_2026-08-26.json` lists all
    of them with a deep link each. All 39 came from the defective 20:36 batch,
    which raised the question directly; testing whether each suggestion fixes an
    unattested word 1-2 positions later returns **0 hits**, so they do look like
    genuine self-suggestions rather than mis-paired corrections. That is evidence,
    not proof - the klal 66 misplacements were 15 words, not 1 - and the clearing
    is reversible either way, since the original notes remain in the append-only
    ledger.

29. **DEEP LINKS + A COPY CONTROL, 2026-08-26 (reviewer requests).** A URL now
    addresses a klal, or a klal and a word:
    `http://127.0.0.1:8420/#klal=66&word=135`. The part is derived from the klal
    id, so a link to klal 400 works whether or not Part 2 is on screen; the
    address bar tracks navigation via `history.replaceState`, so the current view
    is always copyable. Word spans carry `data-word-index`, which is what made
    any of this addressable. **The scroll observer was the hazard** - it calls
    `setActiveKlal` on whatever drifts into view, so a smooth scroll let it
    overwrite the destination mid-animation (routing to klal 66 measurably landed
    on 61); routing now mounts, jumps instantly, and holds the observer off.

    The klal/word header in a correction panel is also a copy button, yielding
    both lines at once:
    `Klal 66 · Word #135 — ע"ס` / `http://127.0.0.1:8420/#klal=66&word=135`.
    It has a non-clipboard fallback, because a copy button that silently does
    nothing is the dead-control shape this file has shipped more than once.
    Three Playwright regressions cover the routing, the address bar and the copy.

30. **FIXED 2026-08-26 (reviewer: "klal 179 word 267 - clicking does not
    highlight word in scan page") - a defect item 24's own merge introduced the
    same day.** The lexical entries were written with `page: None, bbox: None`, so
    `api_page()` could not place them (they rendered as plain prose, not as
    flagged words) and the click fell back to the klal's START page - klal 179
    w267 is on page 67 in a klal starting on 66. Fixed at both ends:
    `merge_lexical_defects()` now fills the scan position from the same alignment
    the server uses, and the frontend gained `pageForWord()` (`corr.page`, then
    `word_pages`, then the klal's start page). All 56 entries now carry a
    position; a new gated invariant catches the class. Swept: 3 other entries
    have a `page` disagreeing with the alignment map, but each carries its own
    bbox and highlights correctly - their page came from a verified vision crop,
    which outranks the heuristic, so they are deliberately left alone.

31. **THE MERGED LEXICAL TIER HAS A PREFIX FALSE-POSITIVE CLASS, and no cheap
    filter separates it (reviewer, klal 179 w267).** `שתרץ` = ש + תרץ ("that he
    answered") is a normal construction; the detector proposed `שרץ` (a creeping
    thing), which is nonsense there. A legitimate prefixed form is unattested as a
    WHOLE in the reference corpus, so an unattested-form detector cannot tell it
    from a corruption.

    **Two suppression rules were tried and both over-suppress.** A plain
    "does it parse as prefix+attested-stem" test excuses 29 of the 56 entries,
    including `כפרק`->`בפרק` (ב/כ, the commonest confusion pair in this print). A
    narrower "does the proposed edit change the STEM rather than the prefix" test
    still suppresses 27, including `מיר`->`מיד` and `וכין`->`ובין`, which look
    real. Both parse; only context decides. **Per Lesson 31 the tuning is handed
    back rather than attempted a third time** - the filter is NOT in the pipeline.
    Raising `REVIEW_MIN_REF` is the blunt lever if the tier proves too noisy.
    klal 179 w267 is recorded as rejected and is the first ground-truth precision
    datapoint on this tier.

32. **LIST PRODUCED 2026-08-26 (reviewer request): every word set with the
    alef-lamed ligature.** `tools/list_ligature_words.py` ->
    `ligature_words.json`. **The ligature codepoint U+FB4F appears ZERO times** in
    part1/2/3.json and zero times in the DocAI stream - checked, not assumed - so
    the sort reaches the corpus as the letters `אל` when read correctly and as one
    of three failure modes otherwise.

    | | Part 1 | Parts 2/3 | total |
    |---|---|---|---|
    | words set with the ligature (contain `אל`) | | | **175 distinct / 2,619 occurrences** |
    | dropped lamed (`אליבא`->`איבא`) | 7 | 314 | 321 |
    | dropped alef (`שמואל`->`שמול`) | 3 | 16 | 19 |
    | both lost (`אל`->`&`) | 3 | 0 | 3 |

    The commonest ligature words are `אלא` (765x), `אלו` (150x), `שמואל` (140x),
    `אליבא` (132x) - which is why this one sort matters more than any other in the
    fount. **13 of the 19 dropped-alef cases are `שמואל` variants**, and 10 of the
    dropped-lamed are `ישרא`->`ישראל`. Part 1's actionable set is only **10
    candidates, 4 of them unflagged**; two of those four are already-resolved
    false positives (`ויגל`, Psalms 16:9; `אוף`, real Aramaic with its own Jastrow
    entry) and are marked as such in the tool so no future run re-proposes them.
    The failure lists are candidates, not confirmed errors - except `both_lost`,
    which is exhaustive, because an ampersand is never Hebrew.

33. **GEMATRIA RULE CONFIRMED AND ENCODED 2026-08-26 (reviewer): a trailing ר in
    a klal marker is a misread ד - with exactly two exceptions, and this corpus
    contains both.** The reviewer's reasoning was "the last digit must be between
    1 and 9". That is right about the UNITS place but not about every numeral:
    Hebrew numerals run high-to-low and a ROUND number simply stops at a higher
    place, so a trailing letter need not be א-ט. Within 1-667 the numbers that
    legitimately end in ר are **200 (`ר`) and 600 (`תר`)** - and klalim 200 and
    600 are exactly the two the corpus has. Every other trailing ר is
    arithmetically impossible (`רמר` = 200+40+200), so the ר must be a ד: this
    fount's ד/ר pair is already a confirmed confusion class.

    Checked corpus-wide: **2 klalim end in ר, both legitimate**. Zero violations
    among klal markers. Encoded as a gated invariant,
    `test_no_klal_marker_ends_in_a_resh_that_should_be_a_dalet`, verified it can
    fail (`רמר`, `קכר`).

    **THE INVARIANT WAS SCOPED TOO NARROWLY AND WOULD HAVE MISSED THE REVIEWER'S
    OWN CASE.** They had just corrected **klal 179 w66 `קנ"ר` -> `קנ"ד`** (154) -
    a numeral in the BODY text, not a klal marker. `קנ"ר` is 100, 50, 200: the 200
    follows a 50, so it is not a numeral at all. Same day they also fixed klal 176
    w691 `חי"ר` -> `חי"ד`.

    **Swept the class properly.** A numeral here carries gershayim immediately
    before its final letter (`קנ"ד`), which is what separates it from `ר'` = רבי -
    a first sweep without that constraint drowned in `דר'`/`לר'`. With it:
    **54 gershayim-forms corpus-wide end in ר where a ד is valid and the ר is
    not** - 14 in Part 1, of which **2 were unflagged and are now flagged**:
    klal 77 w91 `ע"ר` and klal 91 w546 `מ"ר`.

    **The corpus's own usage is the strongest evidence**, better than the
    reference corpus for abbreviations: Part 1 writes `ע"א` 63x, `ע"ב` 61x,
    `ע"ד` 37x against `ע"ר` 5x; `י"ד` 36x against `י"ר` 2x; `מ"ד` 9x against
    `מ"ר` 1x; `כ"ד` 11x against `כ"ר` 2x. Every ר-final form is a rare outlier
    beside a common ד-final twin. That holds whether the form is a numeral or an
    abbreviation, which is why the rule is worth more than its arithmetic alone.

    **Generalising it further does NOT work, measured.** Extending to "any
    gershayim form that is an invalid numeral" returns 205 Part-1 hits, 186 of
    them unflagged and overwhelmingly standard abbreviations - `עכ"ל`
    (עד כאן לשונו, 16x), `י"ל`, `כ"ש`, `ס"ל`, `ל"ת`, `פ"ק`, `ר"ן`. Abbreviations
    do not obey numeral ordering, so the arithmetic test is meaningless for them.
    Second over-broad rule of the day after item 31's prefix filter; per Lesson 31
    it is not being tried a third time. **The narrow trailing-ר rule stands; the
    general one is abandoned.**

34. **REPORTS ARE NOW SHAREABLE, 2026-08-26 (reviewer: "the json is not a good
    way to share the urls - it is not clickable with markdown").** Correct - the
    JSON is what the pipeline reads and diffs, but as a way of HANDING findings to
    a person its links are inert text. `tools/render_report.py` renders any of
    these reports to Markdown (default, clickable almost anywhere a finding gets
    pasted) or HTML (clickable in the browser the dashboard is already open in,
    where the links are same-origin and simply work).

    It reads every report shape in the repo without any of them being rewritten:
    position-per-row (`lexical_defect_report.json`), word-per-row with an
    `occurrences` list (`lexicon_yad_malachi_only.json`), and dict-of-sections
    (`ligature_words.json`, via `--section`). One trap worth recording: **`word`
    means a word INDEX in `cleared_flags_*.json` and the word TEXT in
    `lexicon_yad_malachi_only.json`**, so the key is resolved by TYPE rather than
    by name - guessing by name silently dropped the word index from every link in
    the first run, producing links that opened the right klal at the wrong place.

    The rendered `.md`/`.html` are gitignored: they regenerate in a second, and
    they point at `127.0.0.1:8420`, so they work only on a machine running the
    dashboard. That is right for a review tool and wrong for anything
    outward-facing - do not paste these into a published document.

## Closed — the detail is in `PROJECT-STATUS-HISTORY.md`, by date

Kept as an index so a reference to an old item number still resolves. Nothing here needs action.

| item | what it was | outcome |
|---|---|---|
| 9 / 9a / 9b / 9d / 9e | 2026-08-23 code review, 18 findings across two passes | C1-C4, C15, H5, H6, H8, M11, C16 all fixed; what is still open is item 9c |
| 11 | klal 16's 23 missing words | applied 2026-08-23, user-authorized; span check clean |
| 13 | 2026-08-24 code review, 11 findings on this session's own work | F1-F7 fixed 2026-08-24, F9-F10 fixed 2026-08-25; F8 and F11 accepted open, see item 9c |
| 14 | 14 → 40 stale DocAI page files in the 248-337 range | re-extracted 2026-08-25; zero duplicate page pairs remain anywhere in the book |
| 15 | `sefaria_export/` stale and wrongly attributed | regenerated 2026-08-25 by `export_corpus.py --format sefaria`; Berlin 1851/2, 667 klalim, placeholders empty |
| 17 | klal 88's nav badge read −1 | fixed 2026-08-25; decided was counted per source while the total was counted per word; 3 klalim, 6 phantom decisions |
| 18 | the dashboard offered `6.18M` as a reading, on one click | fixed 2026-08-25; extraction ordered and validated, `Use "X"` no longer saves |
| — | four scan-pane defects on klalim 3 and 4 | fixed 2026-08-25: insert boxes spanning a line break (21 of 40), the klal outline missing on continuation pages, manual words not focusing the scan, manual entries with no bbox |
| — | word-level flags answered by a later decision | fixed 2026-08-25; 23 flags across 7 klalim were still lit on words the reviewer had already ruled on |

---

**Everything else is history.** `PROJECT-STATUS-HISTORY.md` holds the full dated
log, newest first - every finding above traces to an entry there. This file is
meant to be readable in one pass; if it stops being that, move the closed items
out rather than appending.
