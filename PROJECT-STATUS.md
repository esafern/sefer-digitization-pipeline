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

**How much text actually exists.** **595 of 667 klalim carry real text**
(~188,000 words). The other **72 hold a generated placeholder** (`רנ כלל 250`),
all in klalim 223–667 — see open item 16. 43 were reconstructed from the DocAI
token stream on 2026-08-25 and are flagged as unreviewed machine output.

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

16. **72 of 667 klalim still hold a placeholder instead of text** (was 115;
    43 reconstructed 2026-08-25 by `tools/reconstruct_placeholder_klalim.py`,
    user-authorised, each flagged as unreviewed machine output). All are in
    klalim 223–667. Of those left: **44 have no located gematria marker** and
    **13 have no next marker to bound them** — marker-trace work, not extraction
    work — while 9 are blocked by the corpus invariants (page-header furniture
    carried across a page seam, or a catchword duplicated at the seam) and 6 by
    the lexical gates. The reconstructions that DID land are extraction output,
    never read by a human: the gates reject a broadly-wrong span but cannot see a
    scramble buried inside an otherwise good klal.

19. **CODE REVIEW 2026-08-26 ran out of budget twice; 3 of ~10 angles finished
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
