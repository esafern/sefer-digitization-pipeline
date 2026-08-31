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

0M. **[2026-08-31] A GERESH READ AS A YOD IN A NUMERAL SLOT — 3 in the corpus,
    all corroborated by two independent engines. DATA ISSUE, not fixed here.**
    Surfaced from the Dicta comparison: on the one specimen line, the corpus
    reads `סעיף אי` where the Dicta Rashi edition, Surya and sofer.ai all read
    `סעיף א'`. DocAI reads `אי` too - which is exactly WHY the corpus has it
    (the corpus was built from DocAI, so a DocAI artifact that nothing
    contradicted became the text).

    **SWEPT the whole of `part1.json`** for the class - a citation word
    (`סעיף`/`דף`/`סימן`/`אות`/`הלכה`/`כלל`/`פרק`/`ס"ק`/`שורה`) followed by a
    short token ending in `י`. 13 raw matches, 10 of them legitimate Hebrew
    (`הלכה כרבי`, `פרק שני`, `כלל לגבי`, `הלכה מפי משנה`). **3 are real:**

    | klal | corpus reads | Surya | Gemini VLM | context |
    |---:|---|---|---|---|
    | 12 | `סעיף אי` | `סעיף א'` | `סעיף א'` | `...חשן משפט סימן רס"ט סעיף אי` |
    | 140 | `אות עי` | `אות ע'` | `אות ע'` | `...הגהות הב"י אות עי שכתב` |
    | 155 | `סעיף זי` | `סעיף ז'` | `סעיף ז'` | `...ב"ח א"ח סי' שי"ח סעיף זי` |

    Two independent engines agree against the corpus on all three, which is the
    Lesson 9 bar for routing to a reviewer - **not** for applying. **NOT
    APPLIED, and `part1.json` NOT touched**: corrections go through the review
    dashboard against the ink, never a hand-edit or a find-replace (START_HERE,
    "Single source of truth"). These three want a reviewer's eyes on the crop.

0J. **[2026-08-31] DICTA MEASURED, BOTH SCRIPTS — it is the WORST engine on
    square type and the FIRST engine ever to read this work's Rashi script.**
    The user supplied two Dicta OCR samples (square Berlin, and a Rashi-script
    edition). Both scored with the new `tools/compare_ocr_engines.py` against
    `part1.json`, artifacts `ocr_engine_comparison_square_13_23.json` and
    `ocr_engine_comparison_rashi_13_22.json`.

    **Square (Berlin), klalim 13-23, every engine on the SAME three pages:**

    | engine | word acc. | CER (letters) | lexicon hit |
    |---|---:|---:|---:|
    | Dicta | **77.6%** | 8.5% | **83.4%** |
    | DocAI (circular - the corpus was built from it) | 99.0% | 0.8% | 99.1% |
    | Surya | 94.7% | 1.9% | 96.8% |
    | Gemini VLM pass A / B | 96.1% / 95.2% | n/a | 98.2% / 98.1% |
    | corpus itself (ceiling) | 100% | 0% | 99.7% |

    Dicta is beaten by everything already wired in. Its failure is systematic,
    not noise: `ב->כ` x159, `ה->ח` x48, `נ->ג` x44, `ל->ר` x13, plus 115
    spurious `ר` insertions. **That is a Rashi-trained model reading square
    type** - the exact mirror of the HebrewBooks fastocr rejection
    (`PROJECT-STATUS-HISTORY.md` 2026-08-19: a square model reading Rashi,
    `ס` 9.7x over, `א` 0.17x under). 83.4% lexicon hit against a 99.7% ceiling
    is the same rejection metric that killed fastocr at 44.0%.

    **Rashi edition, klalim 13-22, scored against the BERLIN corpus:**

    | engine | word acc. | CER (letters) | lexicon hit |
    |---|---:|---:|---:|
    | **Dicta (Rashi ed.)** | **94.8%** | **3.2%** | **98.5%** |
    | Dicta (square ed.) | 77.5% | 9.0% | 83.4% |
    | Surya (square ed.) | 93.9% | 2.1% | 96.3% |
    | DocAI (square ed., circular) | 98.9% | 0.8% | 99.1% |

    94.8% is a FLOOR, not an accuracy: it is a different EDITION, so genuine
    textual variance is charged to Dicta as error. Read the edition-independent
    column instead - **98.5% lexicon hit against a 99.6% ceiling**, versus
    fastocr's 44.0% on the same Rashi-script material. Hand-inspected klal 20
    (its worst, 82.1%): of 7 mismatches, `דבבא מציעא`->`דבמ` is an edition
    abbreviation, `הרף`->`הריף` is an edition variant, and the rest is
    bottom-of-page margin noise. Almost none of its loss is misread letters.

    **Why this matters more than the square result.** Lessons 23/24: a second
    witness must fail DIFFERENTLY, and architectural independence is defeated
    by a defect in the shared ink. Dicta-on-Rashi is a different ENGINE reading
    a different EDITION - different sorts, different compositor, different
    ligatures - which is the only configuration that escapes both. It is the
    independent witness this project has wanted since Tesseract was measured at
    3.8%, and nothing has read either Rashi-script edition before.

    **NOT YET DONE, and this is the whole payoff:** the samples cover 11 klalim.
    The next step is Dicta over the full Rashi-script edition, then wiring it in
    as an `AbstractWitnessEngine`. **Do NOT route Dicta at the square scan** -
    at 77.6% it would inject more disputes than it settles.

0K. **[2026-08-31] THE THREE-PAGE SAMPLE PDF IS PAGES 19-21 / KLALIM 12-24,
    NOT 18-20 / KLALIM 8-22 — Lesson 30, and it invalidates the eval's stated
    ground truth.** `tools/second_witness_eval/README.md` derived the mapping by
    MD5-matching the sample's images into `berlin_square_corrected.pdf`, which
    returns a **`fitz` doc index**, and reported it as a page number. Lesson 30:
    `page N == doc[N-1]` in this repo. Confirmed against CONTENT, two ways:
    sample page 1 aligns **74.2%** with `docai_word_boxes/page_19.json` (846
    tokens, exactly equal) and **1.9%** with `page_18.json`; and anchoring the
    sample's own token stream in `part1.json` lands on klalim 12-24.

    **What it invalidates.** `groundtruth_klal_8_22.txt` is the wrong ground
    truth for this sample - klalim 8-11 are not on these pages at all, and
    klalim 23-24 are on them but missing from the file. The README's "the test
    set is already adjudicated" table (2,356 words, 23 candidates, 11 open, 9
    human decisions) is counted over the wrong klal set, as is its per-klal
    coverage table. The README's own defence - "klal attribution agreed exactly
    across three independent artifacts" - did not detect this, because all three
    were queried with the same wrong page number; they agree with each other and
    not with the image. **`klal_page_regions.json`, `docai_word_boxes/` and
    `images/pdf_pages/` are NOT affected** - they use correct repo numbering,
    and are what proved the error.

    **ONE OF THE SIX WAS A CODE BUG, NOT A COMMENT (Lesson 34 - sweep the
    siblings).** `tools/test_trocr_benchmark.py` did not merely *say* 18/19/20,
    it held `sample_page_map = {1: 18, 2: 19, 3: 20}` and fed it to
    `cio.load_docai_page()`, so every sample page in that benchmark was scored
    against the NEIGHBOURING page's DocAI tokens. Corrected to `{1: 19, 2: 20,
    3: 21}`. Any TrOCR number ever produced by that script is void. **Swept
    every other `fitz` page access in `tools/` and `pipeline/` (13 call sites):
    all the rest are correct** - they route through
    `vision_adjudication_common.crop_pdf_bounding_box()`, which does
    `doc.load_page(page_num_1indexed - 1)`, or through
    `run_surya_part1_full_baseline.py`'s explicit `doc[p - 1]`.
    `test_trocr_benchmark.py` was the only site that had its own copy.

    **SWEPT (Lesson 28) - 6 places carried the claim, all corrected 2026-08-31:**
    `tools/second_witness_eval/README.md` (title, the mapping line, the
    three-artifact section), `groundtruth_klal_8_22.txt`'s header line,
    `evaluate_ocr_alignment.py`'s docstring, `run_vlm_witness_sample.py`'s
    docstring, `test_trocr_benchmark.py`'s page-map comment. **One file was
    checked and is NOT wrong:** `vlm_klal_8_22_ocr.txt` really is klalim 8-22 -
    that script crops per-klal from `klal_page_regions.json`, never by page
    number, so only the page half of its docstring was false.

0L. **[2026-08-31] `vlm_part1_full_baseline*.txt` blocks are PAGE-REGION text,
    not klal text, for 65 of 222 klalim — any character-level metric read off
    those files is meaningless.** Found while scoring Dicta. Klal 15 has **25
    words in the corpus and 245 in the VLM baseline (9.8x)**; klal 9 4.9x, klal
    36 4.8x. The VLM was given a klal's page region and transcribed everything
    in it, so a short klal's block carries its neighbours. **Swept all three
    baseline files:** pass A **65/222** klalim over 1.3x, pass B **46/222**,
    `surya_part1_full_baseline.txt` only **3/222** (klalim 161, 162, 202).
    Word accuracy (matched / reference) is unaffected and every accuracy figure
    quoted in this repo off these files still stands; CER and any
    length-sensitive metric do not. `tools/compare_ocr_engines.py` prints CER
    for them but it should be ignored, not compared.

0G. **[2026-08-31] Two UI tests are DEFINED TWICE in the same file, so the
    first copy of each never runs — and the discarded copy is the stricter one.**
    `tests/test_review_server.py` holds **38 `def test_` statements and pytest
    collects 36**: `test_deep_link_lands_on_the_klal_and_rings_the_word` (lines
    333 and 368) and `test_clicking_a_word_puts_it_in_the_address_bar` (lines 357
    and 386) are each defined twice, and Python rebinds the name, so the earlier
    body is discarded at import. No error, no skip, no warning — the count is the
    only symptom, which is why it survived. Both pairs were written for item 29's
    deep-link feature.
    WHAT THE SHADOWING ACTUALLY COSTS, read side by side rather than assumed:
    the surviving `test_deep_link...` asserts only `assert ringed`, while the
    discarded one asserts `len(ringed) == 1` ("expected exactly one ringed word")
    — so a routing bug that rings several words now passes. The discarded copy
    also exercises the **klal-only** route `/#klal=66` before the klal+word route,
    and the survivor does not, so the bare-klal deep link has **zero coverage**.
    The `test_clicking_a_word...` pair differ only by an added settle wait, which
    costs nothing.
    Swept the class, per the standing rule: all four test files, **this is the
    only file affected** — `test_corpus_invariants.py` (44 defs), 
    `test_pipeline_logic.py` (273) and `test_witness_engine.py` (5) have no
    duplicate names, and their def-count equals their collected count.
    **FIXED 2026-08-31.** The weaker copy of each pair was deleted and its
    surviving twin strengthened, so no coverage was traded away: the deep-link
    test keeps `len(ringed) == 1` and the klal-only route, and the address-bar
    test keeps the settle wait the other copy had. 36 defs, 36 collected.
    **Gated by `test_no_test_file_defines_the_same_test_name_twice`**, which walks
    every `tests/test_*.py` with `ast` and compares module-level `def test_` names
    for duplicates. Verified it can actually fail, per Lesson 25: injecting a
    duplicate into `test_witness_engine.py` fails it by name and line, removing it
    passes. This was Lesson 32's shape one level in — a test that exists, is
    maintained, reads as covering the feature, and does not run.

0F. **[2026-08-31] The UI test suite is bound to THIS corpus, in its current
    state of repair — the wrong shape for a general-purpose platform.** Measured:
    every test in `tests/test_review_server.py` boots a server against the shipped
    Yad Malachi corpus and **23 pin a corpus coordinate in executable code**
    (`#klal-block-66 .flag-word`, `klal_id, word_index = 1, 85`, a literal `&` at
    klal 69 w338). Zero use synthetic data. So they test the platform PLUS
    this book's defects, and the failure mode is backwards: **the closer the text
    gets to correct, the more tests fail**, because each quietly depended on a
    defect surviving. Seven broke at once on 2026-08-31 when the reviewer's
    decisions were applied — one asserting an `&` that had been correctly repaired
    to `אל`, three sitting on a klal whose candidates were all settled.
    THE ENGINE IS NOT THE PROBLEM: `tests/test_pipeline_logic.py` is 273 tests, 91
    of them purely synthetic and only ~6 touching real data - every fix to the
    apply path, the drift guards, the reindexers and the flag closing is tested on
    a throwaway `אלף בית גימל` corpus and would pass on any book.
    `tests/test_corpus_invariants.py` reads the corpus BY DESIGN, which is right,
    but its three baselines are keyed `(klal_id, word_index)` and every entry
    shifts when a word is inserted or deleted earlier in its klal - item 0C
    reaching into the test suite, where nothing can reindex a literal.
    FIX: a small synthetic corpus fixture carrying one of each condition (a
    disputed word, an ai_flag, a manual correction, a multi-page klal, a
    non-Hebrew character, a duplicated word) for the UI tests to boot against.
    NOT DONE - 2026-08-31 only unpinned the seven that broke, by having them look
    a subject up rather than assume one. That is a patch; the fixture is the fix,
    and it is self-contained work that wants its own scope.
    **CORRECTED 2026-08-31: "all 38 tests" is wrong — the file DEFINES 38 and
    pytest collects and runs only 36.** Two names are defined twice and the first
    body of each is silently discarded; see item 0G. The 38 came from a
    `grep -c "^def test_"`, which counts the source rather than what runs, and
    that distinction is the whole of 0G. The 23 pinned coordinates are unaffected.
    0G is now FIXED and gated, so the count is 36 = 36; the fixture work below is
    unaffected and still open. Note for whoever builds it: a duplicate name in a
    file being rewritten test-by-test is exactly how those two got there, and the
    new guard is what will catch the next one.

0E. **[FIXED 2026-08-31 — see item 46.] A nav jump's smooth scroll outlives the
    observer suppression, so a focus set during it is wiped.** `jumpTo()` starts a
    `scrollIntoView({behavior:'smooth'})` and sets `suppressObserverScroll` for
    **700ms**; measured 2026-08-31, that scroll takes **~1500ms** to settle from a
    long jump (klal 53 -> klal 12 sampled every 300ms: -11337, -3737, -893, -24,
    12). For the remaining ~800ms the scroll observer is live, so
    `updateActiveFromScroll()` fires, calls `setActiveKlal()`, and that calls
    `showPage(page, klal, null)` - the explicit null that clears `scanFocusCorr`.
    Any word focused in that window loses its highlight ring, and the scan pane
    jumps to whichever klal the scroll is passing.
    Caught by instrumenting `showPage`: zooming right after a nav jump produced
    two `showPage(..., null)` calls for klal 4 while the focused word was in klal
    5. NOT a regression - reproduced with 2026-08-31's frontend and server changes
    reverted; it surfaced only because a test's subject moved off klal 1 when its
    corrections were applied.
    NOT YET FIXED. The clean fix is to end the suppression when the scroll
    actually settles rather than after a fixed timeout, which is a behaviour
    change in the scroll/observer path and wants its own before/after. In the
    meantime `tests/test_review_server.py::test_focus_box_transparent_and_zoom_
    preserves_focus` waits for the scroll to settle before focusing, so it tests
    zoom rather than the race.

0D. **[FIXED 2026-08-30, reviewer-reported] Correcting a word cost it its scan
    position, and applying a decision never closed the flag that raised it.**
    Three reports, one measurement behind two of them.
    (a) **63 of 306 open word-level flags (21%) cannot be located on the scan at
    all** — `_word_scan_position()` returns no bbox, so clicking the word
    highlights nothing and there is nothing for the focus-zoom to zoom to. The
    zoom code is intact and correct; it is being handed no box. The cause is that
    the aligner matches CORPUS text against DocAI tokens, so the moment a word is
    repaired it stops matching the token that still holds the OCR error and the
    alignment drops it: `דנראה`, `מאין`, `שבועה`, `אברהם`, `ופומבדיתא` are all in
    the list. **18 of the 63 were created by tonight's own 45 corrections**; 45
    are older. Fixing a word should not blind the reviewer to it.
    (b) `tests/test_corpus_invariants.py::test_every_flagged_word_can_be_located_
    on_the_scan` does NOT cover this: it `continue`s on `opcode in ("delete",
    "ai_flag", "manual")`, and `ai_flag` is precisely what a flagged word is. It
    only fires when an entry lacks a position THOUGH the alignment has one — the
    inverse case. The name promises what it does not check.
    (c) **Applying a decision does not close the flag that raised it.** The
    reviewer cleared klal 66's klal-level flag and the middle pane still read as
    flagged, because `ai_flag_count` counts WORD-level flags and klal 66 has six
    open — four of them (w14, w82, w97, w112) already satisfied by corrections
    applied tonight, including w112's `!`, which no longer exists in the text.
    Nothing in the apply path closes a flag, and the two clearing controls are
    per-flag, so a satisfied flag stays lit until someone clicks it individually.
    **(c) FIXED.** `close_flag_satisfied_by()` closes the flag at apply time — a
    decision applied at that exact word IS a human having ruled there, a
    confirmed-no-op included. It refuses when the flag is NEWER than the apply:
    that means somebody re-opened the position knowing the decision had landed,
    and three real flags depend on it (klal 66 w0, flagged three minutes after its
    own apply was found wrong and reverted; klal 10 w1; klal 17 w308). Backlog
    cleared by `tools/close_flags_already_answered.py`, a one-time backfill that
    reuses the same function rather than restating the rule: **48 dead flags
    closed, 17% of the open queue**, klal 66's four among them.
    **(a) FIXED 2026-08-30 — 63 unlocatable flags down to 10.**
    `_corpus_word_bboxes()` read `SequenceMatcher.get_matching_blocks()`, so ONLY
    words the corpus and DocAI agree on got a box. Backwards, for a queue of words
    flagged BECAUSE the two disagree — and a word lost its box the moment somebody
    repaired it, the corrected form no longer equalling the token that still holds
    the OCR error. It now also pairs an EQUAL-LENGTH `replace` run: n corpus words
    against n tokens between two anchors the alignment already agrees on, so word
    k is token k. That is what a letter substitution, a dropped-lamed ligature and
    a stray `&` all look like. Unequal runs are NOT paired — there the
    correspondence is genuinely unknown and a box on a guessed token points the
    reviewer at the wrong ink.
    Measured against the previous behaviour corpus-wide: **51,043 -> 51,554 boxes,
    511 newly locatable, 0 lost, 0 moved.** The "0 moved" took a second fix:
    paired matches must not choose the PAGE a recurring word lives on (only exact
    ones may), or klal 114 w57-w64 pair against the continuation page holding 5 of
    the klal's 87 tokens and walk off the page they belong to — 8 words that had a
    correct box before.
    **Tried and reverted**: matching non-Hebrew words on their raw text so `&`
    could match `&`. It works and costs too much — putting punctuation tokens back
    into the sequence moved 41 correct boxes and lost 2, ordinary words included.
    The 10 remaining unlocatable words carry no Hebrew letter at all and are
    baselined.
    **(b) FIXED 2026-08-30.** `test_every_flagged_word_can_be_located_on_the_scan`
    exempted `opcode in ("delete", "ai_flag", "manual")` — and `ai_flag` is what a
    flagged word IS — and only fired on the inverse case, an entry lacking a
    position though the alignment has one. Nothing asserted the alignment has one,
    which is why it stayed green through all of the above. Replaced by
    `test_every_open_flag_can_actually_be_found_on_the_scan`, which walks the open
    flags themselves against `_word_scan_position` and baselines the 10.

0C. **[FIXED 2026-08-30] Nothing reindexed the append-only ledger when a klal's
    word count changed — open flags silently walked off their word.**
    `apply_reviewer_decisions.py` limits itself to ONE word-count-changing
    decision per klal per run and prints "run ./rebuild_all.sh, then this script
    again," and that is correct as far as it goes: the rebuild regenerates the
    CANDIDATE files against fresh indices. It does not, and cannot, touch
    `review_decisions.jsonl` — the log is append-only. So every open `klal_flag`
    at an index past the change keeps pointing at the index it was written with,
    which is now a different word. **Fired this run**: deleting the stray `!` at
    klal 66 w112 shortened the klal 215 -> 214, and the flag on `ע"ס` at w135
    came to rest on `שהניח`. Superseded by a new flag at w134 (the old row closed
    with `needs_revisit: false` and an explanation, since nothing may be
    removed). This is the same defect class the reviewer caught on 2026-08-18's
    `ai-semantic-spotcheck-round4` batch — a note attached to the wrong word —
    reached by a different route, so re-verifying that batch did not and could
    not prevent it. **Not yet swept corpus-wide**: only klalim 66 and 219 changed
    word count this run and both were checked by hand, but any earlier
    word-count change may have left the same residue, and no check exists that
    would say so. A validator comparing each open flag's note text against the
    word now at its index would find them.
    **FIXED.** `apply_reviewer_decisions.reindex_flags_after_shift()` moves them
    at apply time, and only on a VERIFIED landing: a flag is shifted only when the
    word it named before is the word at the shifted index, otherwise it is left
    alone and reported — a flag on a guessed word is worse than one a human is
    told to check. The residue was swept, since these notes name their own word
    and the ledger can be checked against the corpus directly: **172 of 258 open
    flags name their own index, and exactly one had drifted** — klal 43 w14, whose
    `ממטונא` sits at w17, confirmed by the note's own quoted context ending
    immediately before it. Moved. Gated by
    `test_no_open_flag_names_a_word_that_is_not_at_its_index`.

0A. **[2026-08-30] A decided dispute could never be applied — 43 rulings
    stranded, now recovered.** `synthesize_multi_witness.active_human_decisions()`
    deliberately DROPS a dispute from the candidate queue the moment a human
    rules on it, so a resolved dispute is not shown again. Correct for the queue,
    fatal downstream: `apply_reviewer_decisions.py` drift-checked each decision's
    `candidate_snapshot` against the live `corrections_part1.json` entry, and an
    ENTRY THAT NO LONGER EXISTS failed that check the same way a changed one
    does. So "entry missing" — the normal state of every unapplied decision —
    read as drift, and the ruling was refused forever. Decide, rebuild, and the
    decision is stranded. **Extent: 43 decisions from 2026-08-22..27, 24 of them
    real edits still sitting uncorrected in `part1.json`** (`&` in klal 167 w24
    among them, plus `שכועה`→`שבועה`, `אברחם`→`אברהם`, `ופומכדיתא`→`ופומבדיתא`).
    FIXED: `snapshot_still_matches_corpus()` falls back to checking the corpus
    itself when the entry is absent — which is the only thing the entry was ever
    proving, and the standard `apply_manual_correction` has always used. An entry
    that is present and DISAGREES still vetoes; a `delete`-opcode decision names
    no span and is never recovered this way. Four gated tests. Applied 2026-08-30:
    80 decisions (27 replace, 2 insert/delete, 15 manual, 36 confirmed-no-op),
    38 words changed across 19 klalim.

0B. **[2026-08-30] `insert`-opcode apply ignored `chosen_text` and deleted a
    word the reviewer never voted to delete — corpus damage, reverted.** Sibling
    of the ★1 finding, same branch, same cause. An `insert` candidate offers one
    span and `apply_insert_removal()` deletes ALL of it, reading `final_text` and
    never `chosen_text`. ★1 fixed the case where the reviewer keeps the whole
    span; nothing covered the reviewer choosing something SHORTER. **It fired on
    klal 66 w0**: stored `סו אין`, reviewer chose the engines' `סו`, and the run
    removed both words — dropping the klal marker AND the `אין` that negates the
    entire klal, turning `אין ב"ד יכול לבטל` (a court CANNOT annul) into `ב"ד
    יכול לבטל` (a court CAN). Caught by reading the applied diff word by word,
    not by any test. `clean_text` restored; the `apply_event` (898c9b4e67d5)
    stands in the append-only log and CANNOT be retracted, so the log now claims
    a change the corpus does not have. **`audit_applied_decisions.py` does not
    catch this** - checked 2026-08-30, it sorts klal 66 w0 into its
    "word-count-changing, not position-verifiable post-hoc" bucket (9 decisions)
    and never compares it to the corpus at all. A reverted insert/delete is
    invisible to the one tool built to find exactly this. The durable record is
    therefore the `klal_flag` appended alongside it, which surfaces on the
    dashboard as an open flag on klal 66; the auditor's blind spot to a reverted
    word-count change is itself worth closing. The script now
    REFUSES this shape rather than guessing. Two gated tests.
    **RULED AND CLOSED 2026-08-30 — verified 2026-08-31, this entry had gone
    stale.** It read "OPEN — needs the user's ruling on klal 66 w0" after the
    ruling had already been given. The reviewer recorded "66 w0 is correct"
    (superseding `disputed_choice` at 2026-08-30T20:37:07, chosen `סו אין`), the
    `klal_flag` was closed in the same second with the reasoning, and a
    confirmed-no-op `apply_event` followed at 21:01:31. The corpus reads
    `סו אין ב"ד יכול` and no flag is open at that word — all three re-checked
    against the ledger and `part1.json`, not inferred from the write-up. The
    evidence had pointed this way: the vision check transcribes `אין ב"ד` at
    0.95, and klal 57 w0 is the identical `נז אין` shape the reviewer chose to
    KEEP. The append-only log still carries the reverted apply_event
    (898c9b4e67d5) claiming a change the corpus does not have; that is by design
    and is documented above.

00. **[CLOSED 2026-08-30 BY THE USER — "close 162/163 surya issue - wasting
    time". Stop raising it in session summaries; the standing reminder inside is
    retired with it.] Surya block mis-assignment: 4 klalim carry a neighbour's
    text.** What was left was a mis-assigned SURYA WITNESS for klalim 162/163,
    not a corpus defect — the stored text of 161/162/163 was re-read on close and
    is clean, each klal opening with its own marker. The cost of leaving it is
    that those two klalim have no working second engine, so cross-checking is
    blind there; the user has weighed that against three failed fix attempts and
    closed it. Retained below as the record of what was measured. NOT to be attempted by an agent without the user saying
    so: three separate attempts to fix it by tuning
    `split_block_across_klalim()` have all regressed the corpus and been
    reverted, the worst costing 29 klalim their coverage and 2.3 points of mean
    agreement. **Any LLM instance reading this file should mention this open
    item to the user in its session summary until it is closed.** (RETIRED
    2026-08-30 — the item is closed; do not carry this directive forward.)
    Details: (swept
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

9c. **[CORRECTED 2026-08-31 — this entry was STALE and overstated the open
    work. Four of its six sub-items were fixed in code and the entry was never
    updated.]** Verified one at a time against the source, not against the
    write-up (Lesson 19/33):

    | sub-item | claim in this entry | verified state |
    |---|---|---|
    | H6 `typography.py` | "still dead code carrying a third, divergent `CONFUSION_PAIRS`" | **FIXED.** Imported by `synthesize_multi_witness.py:57`, `tools/estimate_consensus_posterior.py`, `tools/survey_shared_engine_errors.py` — not dead. Its third `CONFUSION_PAIRS` is **gone**; its own header documents the removal and points to the two real, deliberately-different sets. |
    | H8 passB | "still violates the incremental-flush rule and no-ops its own cache" | **FIXED / deliberate.** `f.flush()` is at `run_part1_vlm_patch_passB.py:122`. The no-op cache is now a *documented correctness requirement*, not an oversight: Pass A and Pass B must be two INDEPENDENT samples, and a shared crop-keyed cache replays A's answer for B, so every replayed position agrees with itself by construction and sails through the stability gate. Reverted 2026-08-24 with that reasoning in the file. |
    | M9 `is_gershayim_noise()` | "moot for the superseded extractors" | **MOOT, confirmed.** The identifier does not exist anywhere in the repo. The normalisation point still stands if Phase 1 is built. |
    | M11 disputed panel | "still pre-selects the machine verdict" | **FIXED.** Reverted 2026-08-23; `review_frontend/app.js:1412-1427` carries the revert and its reasoning. Undecided words default to the stored text. |
    | C16 Surya coverage | "10 klalim still have no Surya coverage" | **FIXED.** `surya_part1_full_baseline.txt` carries all **222/222** klalim with non-zero text (this file's own TL;DR already said 222/222 — the two disagreed). Thinnest are klal 222 (0.39 of corpus words) and klal 163 (0.42, the known mis-assignment from closed item 00). |
    | C18 `match_block_to_klal` | never-None nearest-region fallback | **STILL OPEN — the only one.** `tools/run_surya_part1_full_baseline.py:79`. Now carries an explicit deferral note: 2 blocks / 4 words affected on pages 14-76, and tightening it changes which text every klal gets, so it wants its own measurement rather than a drive-by. Accepted open, not forgotten. |

    The lesson this entry is itself an instance of: an open item that lists six
    things when five are done reads as five outstanding tasks and costs the next
    reader the time to re-derive all of them. Closed sub-items must be struck
    when they close, not left standing.

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

    **The URL SHAPE had to change too** (reviewer: "sadly those links you shared
    here in the chat are not clickable"). `/#klal=66&word=135` is what the
    frontend routes on, but it does not survive being pasted: a terminal will not
    hyperlink Markdown link syntax at all, and several that DO linkify a bare URL
    stop at the `&` - which opens the right klal at the WRONG word, worse than a
    link that plainly fails. `review_server.py` now also serves
    **`/klal/66/word/135`** (`ROUTE_SHARE`), a 302 to the hash form, with no `#`
    and no `&` to trip anything. That is what `render_report.py` emits and what
    should be pasted anywhere outside the browser; the hash form remains what the
    app routes on internally and what the panel's copy button yields.

    The rendered `.md`/`.html` are gitignored: they regenerate in a second, and
    they point at `127.0.0.1:8420`, so they work only on a machine running the
    dashboard. Right for a review tool, wrong for anything outward-facing.

    **EVERY WORD NOW CARRIES ITS ADDRESS ON HOVER** (reviewer: "hovering over any
    word should always surface a floating box with the klal + word and an icon to
    copy the link"). Every word in the text pane is addressable, so every word now
    says what its address IS without being clicked - **plain words previously said
    nothing at all**, and flagged ones only spoke through a native `title`
    tooltip, which cannot hold a button.

    It is a HOVERABLE card, not a tooltip, and the distinction is the whole point:
    `#tooltip` sets `pointer-events: none` precisely so it can never swallow a
    click, which makes it the wrong element for something containing a control.
    `#word-card` stays open while the pointer is on it, with a grace period so the
    pointer can cross the gap from the word - asserted in the tests by actually
    moving onto the card before clicking, because a control you cannot reach is
    the failure mode that matters here. It also TAKES OVER the word's native
    `title` (a flagged word's reasoning) and clears the attribute, since two
    floating boxes over one word is worse than none.

    The card's copy button and the panel's yield the same payload, now in the
    paste-safe path form.

    **Presentation, 2026-08-26 (reviewer):** the decision panel's context header
    is larger (11px -> 14px) and no longer styled as a caption - it is the line
    that says WHERE you are and it now carries the copy control. The hover card
    was made lighter and more transparent (`rgba(26,32,44,0.72)`, text at 0.82),
    with a **backdrop blur**, which is what keeps it legible at that alpha: this
    box follows the pointer across text the reviewer is reading, so it should sit
    over the page rather than block it, and without the blur the Hebrew showing
    through is unreadable.

    **The klal's gematria is now part of the reference everywhere** - "Klal 66
    (סו) · Word #135" in the panel header, the hover card and the copied payload.
    `api_klal` had always carried `gematria`; **`/api/klalim` did not**, so
    anything working from `klalById` (the hover card, the nav) had no way to name
    a klal the way the BOOK does. One field added server-side rather than a
    per-call fetch. The reviewer navigates by id and reads the scan by marker;
    the reference should carry both.

    **ONE box, not two, on a disputed word** (reviewer: "we don't need both boxes
    when it is a disputed word, just the big one with the details"). A flagged
    word in the text pane was showing `#tooltip` AND the hover card at once. They
    are merged into the card, because the card is the only one that CAN hold the
    copy control - `#tooltip` is `pointer-events: none` by design so it never
    swallows a click on the scan pane, where it is still used unchanged. The
    detail block was extracted into a shared `wordDetailHtml()` so the two
    surfaces cannot drift, and the card renders it in full: status, the original
    OCR reading, confidence, reasoning and any recorded decision. Nothing was lost
    by suppressing the tooltip in the text pane, which is what made the merge the
    right move rather than just deleting one box.

    **Clicking a word now ZOOMS the scan onto it** (reviewer request). Centring
    already worked; the zoom did not, and at 100% the page is too small to
    adjudicate the thing the queue is full of - a ס/פ, a ד/ר, a dropped ligature
    letter. A click raises the scan to **220%** and centres the focused box.

    Two properties, and the second is the one that would have annoyed daily: it
    zooms IN only, **never out** - a reviewer who has gone to 300% to read a worn
    sort is not yanked back by their next click. It is also a one-shot flag set in
    `focusWordOnScan()` (the single funnel every word click already passes
    through, from the manualPageLock fix), so scrolling or paging afterwards
    leaves the zoom alone.

    Measured: a word away from the page edges centres to **dx 0, dy 0**. A word
    at an edge cannot be centred because the scroll clamps - the test asserts
    "centred on each axis unless that axis is clamped", since asserting a fixed
    tolerance would only have been asserting the viewport width. Note the scan
    pane is RTL, so `scrollLeft` runs 0 -> negative and any clamp check needs
    `abs()`; the first version of the check missed that.

    **Clicking away undoes it** (reviewer). The zoom is the other half of the
    gesture and has to reverse with the highlight, or the reviewer is left at 220%
    on a page they have stopped inspecting. It restores the zoom from BEFORE the
    focus rather than forcing 100%: the normal flow starts at 100% and so returns
    there, which is what was asked, while a reviewer who had gone to 200% by hand
    to study the page keeps it. Touching the zoom controls or the wheel while
    focused hands ownership back - there is then nothing stored to restore.
    Verified both paths: 100% -> 220% -> 100% with the klal outline back, and a
    manual 200% surviving a full focus/dismiss cycle.

35. **[AUDIT 2026-08-27] Heavy code review & Stage 5b / AI flag diagnostic audit.**
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
      True-positive examples identified against surrounding context ([klal 179 word 16](http://127.0.0.1:8420/#klal=179&word=16) `יותה`->`יותר`,
      [klal 30 word 250](http://127.0.0.1:8420/#klal=30&word=250)/[1263](http://127.0.0.1:8420/#klal=30&word=1263) `גכי`->`גבי`, [klal 54 word 730](http://127.0.0.1:8420/#klal=54&word=730) `עלירם`->`עליהם`, [klal 7 word 252](http://127.0.0.1:8420/#klal=7&word=252) `הלכרה`->`הלכה`,
      [klal 30 word 1115](http://127.0.0.1:8420/#klal=30&word=1115) `טיניה`->`מיניה`); false positives isolated (names like `זלמן`, terms like `בשרש`).
    - **Active AI Flag Alignment Audit**:
      455 active flags (144 klal-level, 311 word-level). For the 202 Round 4 flags: 187 (92.6%) are
      cleanly aligned at their exact stored word index; 12 are already resolved in stored text;
      only 1 experienced index drift ([klal 43 word 14](http://127.0.0.1:8420/#klal=43&word=14) -> [word 17](http://127.0.0.1:8420/#klal=43&word=17) `ממטונא`->`מממונא`); 1 is retracted ([klal 177 word 340](http://127.0.0.1:8420/#klal=177&word=340) `למיפך`).

36. **THE 2026-08-27 AUDIT'S FOUR "CRITICAL DEFECTS" WERE VERIFIED AND ALL FOUR
    FIXED — three were LATENT, not live, and saying which is the point.** Item 35
    listed them; none had been reproduced. Each was run before being touched.

    | audit finding | verified? | live exposure |
    |---|---|---|
    | `export_corpus` drops manual insertions | **yes** | **0 today** - both existing inserts are already APPLIED, and applied decisions are skipped because part1.json already carries their text |
    | multi-word manual replacement shifts indices | **yes** | **0 today** - no manual decision has multi-word text |
    | `corpus_io` crashes if the regions file is absent | **yes**, `AttributeError` reproduced | 0 - the file is tracked; this is a deleted-file case |
    | `_corpus_bbox_cache` never invalidated | **yes** | **LIVE** - the only one |

    **The cache was the real one.** It was keyed `(klal_id, page)` and never
    cleared, but the alignment it stores is computed FROM the klal's words - so
    applying a decision and rebuilding *while the server ran* left every later
    request drawing boxes from text that no longer existed. That is the exact
    sequence a reviewer performs, and it contradicts this section's own "fresh off
    disk every call" contract. Now keyed on a stamp over part1/2/3.json's
    (mtime, size), the same pattern as the `_read_all` and `_load_regions` memos.

    The export gap is worth stating precisely because "drops manual insertions"
    overstates it: the export re-derives from the CURRENT part1.json and skips
    already-applied decisions, so the gap opens only in the window between
    recording an insert and applying it - which is, admittedly, exactly when an
    export is most likely to be taken. `apply_reviewer_decisions` has three manual
    cases (insert / delete / replace) and the export had two; it now has three,
    proved by an unapplied insert reaching the export in a temp-ledger harness.

    The multi-word guard had to be scoped to the REPLACE path: written broadly it
    consumed the word-count slot that the insert branch's own gate then tripped
    over, and `test_manual_correction_with_no_original_word_inserts_new_text`
    caught it immediately. `corpus_bbox_cache_key()` is now exported so the test
    that pre-seeds that cache builds the key the way the module does.

39. **[2026-08-31] THE `title` FIELD IS UNREVIEWED TERRITORY — it carries its
    own uncorrected OCR, and no detector in this repo has ever looked at it.**
    Found because the reviewer read one: "klal 39 the title ends with harav, the
    amrinan is the beginning of the text." Both halves of that are right, and they
    are two DIFFERENT defects.

    **(a) The extent defect the reviewer reported.** Klal 39's title is
    `אין הלכה כתלמיד במקום הרב אמרינן אף כשהתלמידים הם רבים נגד רכם` — it should
    stop at `הרב`, and `אמרינן ...` is body text that has been pulled into the
    heading. NOT SWEEPABLE MECHANICALLY, and I checked before claiming so: title
    length is not the signal, because this book's headings genuinely are long
    sentences (mean 6.2 words, p90 = 11, and klal 92's legitimate title runs 24).
    Deciding where a heading ends needs the printed page, where it is set in
    larger type. So the extent of (a) is UNKNOWN and is not being guessed at.

    **(b) A sweepable defect found while checking (a), extent exact.** A title
    should be a prefix of its own `clean_text` after the marker. **14 of 222 are
    not.** Eight are benign alignment offsets (the title starts at a different
    word than body[1], e.g. klalim 101-105 whose body opens `ב"ד` where the title
    opens `מתנין`). **Six are real OCR errors sitting in the title where the BODY
    IS ALREADY CORRECT:**

    | klal | title has | body has | class |
    |---|---|---|---|
    | 39 | `רכם` | `רבם` | ב/כ, the commonest confusion in this print |
    | 69 | `אהים` | `אלהים` | **dropped lamed — the alef-lamed ligature again** |
    | 91 | `איכא` | `אליבא` | dropped lamed |
    | 88 | `וכאבל` | `ובאבל` | ב/כ |
    | 87 | `משנה` | `ממשנה` | dropped letter |
    | 36 | `הש"ס'` | `השית'` | — |

    **WHY NOTHING CAUGHT THESE:** every detector, validator and witness in this
    repo reads `clean_text`. `detect_real_word_substitution`, the lexical defect
    report, the consensus pipeline, the corpus invariants, the vision
    adjudicator — all of them. The `title` field has never been read by any of
    them, so it has had no OCR pass at all, and klal 69's is the **same ligature
    sort** that produced items 26 and 32. Lesson 1 in a place nobody had looked:
    a check that was never run over this field has verified nothing about it.

    **THE PIPELINE NEEDS A TITLE PASS — this is the standing requirement, and it
    is not built.** `title` lives in `part1.json`, so it is corpus text under the
    single-source-of-truth rule, but `apply_reviewer_decisions.py` only ever
    writes `clean_text`: **there is no mechanism in this pipeline for promoting a
    title correction, and no detector, witness or invariant reads the field.**
    What a title pass owes, at minimum: (i) the detectors run over `title` as well
    as `clean_text`; (ii) an apply path so a ruling on a title can be recorded and
    promoted like any other, instead of being hand-applied; (iii) a gated
    invariant that a title is a prefix of its own body, with the legitimate
    offsets baselined; (iv) a decision on the EXTENT question, which needs the
    scan because only the printed type size says where a heading stops.

    **5 TITLES HAND-EDITED 2026-08-31, user-authorised** ("for now we will
    hand-edit part1.json. do it carefully and show me the diffs") — a deliberate,
    recorded exception to the single-source-of-truth rule, taken because no apply
    path exists to take instead. Diffs shown and approved before writing:

    | klal | class | was | now |
    |---|---|---|---|
    | 39 | EXTENT | `...במקום הרב אמרינן אף כשהתלמידים הם רבים נגד רכם` | `אין הלכה כתלמיד במקום הרב` |
    | 69 | spelling | `אהים` | `אלהים` |
    | 87 | spelling | `משנה` | `ממשנה` |
    | 88 | spelling | `וכאבל` | `ובאבל` |
    | 91 | spelling | `איכא` | `אליבא` |
    | 36 | EXTENT | `אלא אין דרך הש"ס' סדרי לומר היכא שלא הוזכר שום אמורא ברישא` | `אלא` |

    Klal 39's truncation removes the `רכם` misread along with the absorbed body
    text, so it needed no separate spelling fix. Verified after: the title-order
    validator flags none of the five, and Part 1's first-letter regression count
    is **118 before and 118 after** — the edits introduced no ordering change.
    `./rebuild_all.sh --skip-vision` re-run; 318 gated tests pass.

    **KLAL 36 RESOLVED 2026-08-31 BY THE REVIEWER, and it was an EXTENT case, not
    a spelling one.** I had left it open because title `הש"ס'` and body
    `השית' סדרי` spell the same thing (`ש"ס` abbreviates `שישה סדרים`; `שיתא סדרי`
    is its Aramaic), so I could not tell which the printer set. The reviewer's
    answer dissolved the question: **the heading is just `אלא`** — the term the
    klal is about — and everything after it was absorbed body text, where
    `השית' סדרי` is correct as it stands. Title set to `אלא`; the divergence
    disappeared with the absorbed words. Worth recording as a reasoning error:
    I had classified it by the DIFFERENCE I could see (one word) instead of asking
    whether the whole span belonged, and the two classes need to be tested in the
    other order — extent first, then spelling within what remains.

    **THE EXTENT CLASS REMAINS UNSWEPT.** One klal was corrected because the
    reviewer identified it. How many others have absorbed body text is unknown and
    is not being estimated — per item 0's standing rule this is recorded as
    unmeasured rather than left to read as handled.

    **The alphabetical-order validator is the one thing that does read titles**
    (`tools/validate_title_alphabetical_order.py`) — it checks ORDERING, not
    spelling, and a ב/כ misread mid-title cannot fail it.

55. **[2026-08-31] Post-apply state, and two things the apply itself surfaced.**
    The rebuild/apply loop was run to convergence — 48 + 1 + 3 + 3 decisions over
    four rounds, since the script deliberately applies only one word-count-changing
    decision per klal per run. **0 decisions pending at the end.**

    **PART 1 NOW HAS ZERO FOREIGN CHARACTERS** — `validate_part1_corpus_integrity`
    check 2b reports 0, from **7** at the start of the day. The last `&` (klal 77
    w11) is `אל`, and `ligature_words.json` now reports **`both_lost: 0`**, closing
    the last of item 32's three. **Item 27's page-seam furniture is fully removed
    too**: klal 39's catchword `דבכולהן` is gone, and klal 210 reads
    `אפשר דהלכה כקמייתא` — matching the printed page — after its three spurious
    tokens (`דהלכה`, `:`, the folio `לא`) came out one per round.

    **A title diverged from its own body the moment the body was corrected, which
    is item 39's gap arriving on schedule.** Applying klal 77 w7 `לא` -> `אלא` left
    the `title` field still reading `לא`: nothing propagates a body correction into
    the title, because titles have no apply path. Fixed by hand (authorised, same
    as the rest of today's title work) and Part 1 is back to **222/222 clean
    prefixes, 0 divergences**. This is the concrete argument for the title pass:
    every future body correction inside a heading will do this again, silently,
    and only `compare_titles_to_text.py` would notice.

    **A UI test SKIPPED ITSELF because the corpus got better** —
    `tests/test_review_server.py:1079`, with the message "no bare `&` left in
    Part 1 - seed one through the API instead of skipping". That is item 0F /
    Lesson 36 exactly, caught in the act: a test pinned to a defect stops testing
    when the defect is repaired, and a skip is quieter than a failure. The test
    knows what it needs (seed the condition through the API rather than borrow it
    from the shipped corpus); doing that is part of the synthetic-fixture work item
    0F describes, and it is now the second concrete case waiting on it.

54. **[2026-08-31] 48 reviewer decisions applied — and I had to repair an
    index drift I caused myself first. The repair closed a real gap in the
    reindexer.**

    **WHAT WENT WRONG.** Item 48's `[.]` insertions shifted every later index in
    17 klalim. I called `reindex_flags_after_shift()` and **not**
    `reindex_pending_decisions_after_shift()`, which already existed — so open
    flags moved and PENDING DECISIONS did not. Lesson 35 names both in one
    sentence and I acted on half of it. Measured before applying anything: **4
    pending decisions had drifted by exactly +1** (klal 39 w617 and w251, klal 36
    w73, klal 106 w16), each naming a word that sat at index+1.
    A stale decision is worse than a stale flag, as that function's own docstring
    says: a flag points at the wrong word and a human notices, while a decision is
    refused by the drift guard on every future run and is stranded exactly the way
    item 0A stranded 43 rulings.

    **THE GAP THE REPAIR EXPOSED: `reindex_pending_decisions_after_shift()` did
    not cover `disputed_choice`** — only `candidate_choice` and
    `manual_correction`. That is the type that needs it most: a decided dispute is
    dropped from the candidate queue, so it is drift-checked against `part1.json`
    itself, which is precisely the check a shifted index fails. **3 of my 4
    drifted decisions were `disputed_choice`.** Added to the tuple.
    My repair pass was scoped too broadly on the first attempt — it ran over every
    klal whose heading is followed by `[.]`, 92 of them, not the 17 that actually
    shifted. **The verified-move rule refused every one of the extras**: a
    decision moves only when the word it named is provably at the shifted index,
    and in an unshifted klal it is not. 9 moves written, all in klalim 36/39/106,
    all re-verified afterwards against the corpus. The guard did its job on an
    operator error, which is the argument for having written it that way.

    **APPLIED: 48 decisions** (16 replace, 15 manual, 17 confirmed-no-op) — up
    from 44 before the repair, the difference being the 4 recovered. 2 refused and
    40 drift-skipped, both pre-existing and both correctly left alone.
    **The applied diff was read word by word before being accepted**, which is how
    item 0B's corpus damage was caught and is not a step to skip. All six
    deletions verified against the index they name: three commas the reviewer
    ruled on (klalim 31, 36, 146), a doubled geresh (klal 69 w11), and **two of
    item 27's page-seam duplicates finally removed — klal 39's catchword
    `דבכולהן` and klal 210's `דהלכה`**.

    **Two things worth the reviewer's eye, neither a defect:**
    - **klal 74 w966 `בארוכה` -> `בארוכ'`.** Item 51's filter had just protected
      the stored `בארוכה` by rejecting DocAI's `בארוכ` as orthographically
      impossible. Both are right and they do not conflict: a bare `בארוכ` cannot
      exist, the page prints the ABBREVIATION `בארוכ'`, and DocAI dropped the
      geresh. The filter rejected the impossible string; the reviewer supplied the
      real one.
    - **klal 77 w91 came in as `ע״ד` with a U+05F4 gershayim**, not the ASCII `"`
      the corpus uses everywhere else. Part 1 now holds **2** such characters
      (klal 2 w316 and this) against **6,405** ASCII quotes. Not corrected here —
      it is the reviewer's own keystroke and corpus text — but it is the same
      single-instance anomaly flagged on klal 2 w316 in the 2026-08-30 open items.

51. **[FIXED 2026-08-31] An orthographically impossible reading no longer
    reaches a reviewer.** The reviewer's rule, on klal 36 w61: a word-final `כ`
    must be `ך`, so `כתכ` cannot be a Hebrew word and no vision call should have
    been spent on it. `corpus_io.impossible_final_form()` encodes it and
    `assemble_corrections_dataset.classify()` consults it BEFORE any vision
    verdict: such a candidate is `current_text_confirmed`, i.e. machine-resolved,
    not a dispute to put in front of a human.

    **The abbreviation exemption is the load-bearing half**, and it is the same
    one item 33's trailing-`ר` rule needed: an abbreviation does not obey
    final-form orthography, because the letter is an INITIAL, not a word ending.
    `ה"נ` (הכי נמי) is a perfectly good form and is a false positive of the naive
    rule. Measured: 7 candidates carried such a reading, **6 after the exemption**.
    Verified after the rebuild: klal 74 w966 (`בארוכ` vs the correct `בארוכה`),
    klal 36 w61 and klal 182 w0 all now read `current_text_confirmed` — w966 had
    been **OPEN**, asking a reviewer to weigh a string that cannot exist.
    Gated by `test_a_reading_ending_in_a_non_final_letter_form_is_impossible`,
    which is purely synthetic and asserts the exemption as well as the rule.

52. **[2026-08-31, reviewer] The scan pane now scrolls to the klal it is showing,
    and a word click goes to that word's own page.** Reported as "klal 4 doesn't
    move the scan to the correct klal". The region outline was drawn correctly all
    along — the problem is that **klal 4 holds 40 of its 497 tokens (8%) on its
    start page**, in the bottom tenth of it, so a reviewer looking at the top of
    page 15 sees klal 3 and concludes nothing moved. **A class, not one klal: 30
    of 222 klalim start on a page holding under half their text** — klal 92 at 6%,
    klal 30 at 7%, klal 159 at 16%, klal 169 at 17%.
    Fixed with `scrollIntoView({block: 'nearest'})` on the region box, which is
    the reviewer's own rule ("bottom of the page for the first half, top for the
    second") without special-casing either: it scrolls the minimum that brings the
    region into view, landing at the bottom for a start-page sliver and the top for
    a continuation, and is a no-op when the page already fits. Verified in a short
    viewport where the page cannot fit: klal 4 scrolls to 168px with the region in
    view, and clicking word 201 takes the scan to page 16, its own page
    (`pageForWord` already resolved this correctly — confirmed rather than assumed).

53. **[2026-08-31, reviewer: klal 35 w30 "takes me to a completely wrong word"]
    THE FIX IS TO RETRACT THE CANDIDATE — the word is not missing, and the
    aligner is why it looked missing.** `שמות` **is already in klal 35, at word
    45**, in `בספר שמות בארץ בכפות תמרים`. Its stored copy has **no alignment
    box at all**, so DocAI's token for it matched nothing and was reported as an
    omission — at word 30, 15 words before the real one. Both independent
    witnesses read `משמע` at word 30, contradicting the omission outright. The
    scan pane was faithfully drawing the candidate's own bbox; the candidate is
    what is wrong.

    **Two sweeps, because the first metric missed the reported case and saying so
    matters.** A vertical-distance check (is the candidate on a different printed
    line from its neighbours?) found 5 but NOT klal 35 w30, which sits on the
    same line 0.72 of the page width away — the opposite end of an RTL line. A
    reading-order coordinate (line band, then right-to-left within it) catches it:
    **5 omission candidates whose bbox is out of reading order for their word
    index** — klal 17 w308, klal 85 w96, klal 2 w632 (all the NEXT klal's marker,
    a boundary artifact), klal 50 w2, and klal 35 w30.

    **The wider and more useful sweep: 13 of Part 1's 40 omission candidates
    propose a word that ALREADY appears in the same klal.** Eight of those sit at
    the candidate's own scan position (klalim 50, 68, 128, 167×2, 169, 189, 194) —
    unambiguous alignment failures. The rest are further off and need reading:
    klal 35 w30 (15 words away, and the copy is unaligned), klal 175 w173, klal 2
    w632, klal 193 w244, klal 159 w1036.

    **NOT auto-suppressed.** A word can legitimately repeat in a klal, and this
    book restates maxims verbatim as a matter of style — the corpus-integrity
    validator has a whole check devoted to that. So "already present" is a strong
    triage signal, not a proof, and turning it into a filter would be the
    over-suppression this file has recorded twice (items 26 and 31). Recorded with
    its extent for the reviewer to rule on.

50. **[2026-08-31, reviewer] Three nav badges, and editorial marks are
    addressable at last. Plus four findings from the same report, three of which
    need the reviewer's call and are NOT fixed.**

    **FIXED — the third badge.** `machine_resolved_count` was served per klal and
    summed only into the legend total, so klal 73 showed one badge while
    highlighting two words (item 49). The nav row now reads open (red) ->
    machine-resolved (amber) -> human-decided (green), in decreasing order of
    claim on the reviewer's attention, with the amber matching the colour the
    word itself renders in.

    **FIXED — `[.]` was the one token in the text that could not be clicked**
    (reviewer: "36 w14 won't let me click on it - shows ?"). The editorial-mark
    branch of `renderKlalBody` returned early before the span ever got a
    `data-word-index`, so the mark could not be addressed, hovered for its
    reference, deep-linked or clicked - while still CONSUMING a word index, which
    is what made the reference read wrong. It now carries its index and takes the
    same click as a plain word, because a reviewer must be able to remove or
    change a mark this pipeline itself inserted. **This mattered more today than
    yesterday: item 48 inserted 17 more of them.**

    **NOT FIXED, needs a decision — a nav jump shows the klal's START page, and
    for 30 of 222 klalim that page holds a MINORITY of the text.** Reported as
    "klal 4 doesn't move the scan to the correct klal". Measured: klal 4 starts on
    page 15 with **40 of its 497 tokens (8%)** and continues on page 16 with 457;
    the region outline IS drawn, correctly, on the bottom 10% of page 15. So the
    behaviour is right by its own rule and useless in practice. Worst cases:
    klal 92 (36/584 = 6%), klal 30 (133/2021 = 7%), klal 4 (8%), klal 31 (14%),
    klal 159 (16%), klal 169 (17%). Options are to jump to the page holding the
    most of the klal, or to keep the start page (where the marker is) - a
    presentation decision, and after two wrong inferences today I am not making
    it unilaterally.

    **NOT FIXED, a cheap filter worth having — 7 candidates propose a reading
    ending in a NON-FINAL letter form, which Hebrew orthography forbids.** Raised
    by the reviewer on klal 36 w61: "why was ctc considered? cof is impossible
    here, would be cof sofit." Exactly right - a word-final `כ` must be `ך`. The
    class, swept: `כתכ` (36 w61), `בארוכ` (74 w966), `חרא רבפ` (176 w277), `קפכ`
    (182 w0, a klal MARKER), `נחמ` (198 w597, an insertion candidate), `וכפ`
    (217 w548), and `ה"נ` (212 w30).
    **The rule needs the same exception item 33's trailing-`ר` rule needed:
    abbreviations do not obey final-form orthography** - `ה"נ` (הכי נמי) is a
    perfectly good abbreviation and is a FALSE POSITIVE of the naive rule, as is
    anything carrying a geresh or gershayim. Excluding those leaves ~4 genuine
    impossibilities. **The one that matters: klal 74 w966 is still OPEN**
    (`current_text_may_be_wrong`), asking the reviewer to weigh `בארוכ` against
    the correct `בארוכה`. A candidate that cannot be a Hebrew word should never
    reach the queue, and this is a five-line test on `docai_reading`.

    **NOT FIXED, a data issue — klal 35 w30's omission candidate is
    mis-positioned** (reviewer: "takes me to a completely wrong word in the
    scan"). The entry is `opcode: delete` / `possible_omission`, proposing DocAI's
    `שמות` as missing at word 30; its bbox points at a genuine `שמות` on page 26,
    but at the end of an unrelated line (`שיתא סדרי לא סבירא ליה כוותיה · שמות`),
    while corpus word 30 is `משמע` in `לישנא יתירא אמר לך וכו' משמע דההוא אמורא`.
    Rendered the crop at 4x and read it rather than inferring. **Both independent
    witnesses read `משמע` there** (`vlm_reading` and `surya_reading` both
    `משמע`), which contradicts the omission outright - so this looks like a false
    positive whose box happens to land on a real word elsewhere. The scan pane is
    faithfully showing the candidate's own bbox; the candidate is what is wrong.

    **EXPLAINED, not a defect — klal 105 w4 does not zoom** (reviewer: "didn't
    zoom in on the scan panel"). That flag sits on a `,`, a token with no Hebrew
    letter, so the corpus-to-DocAI aligner has nothing to match it on and returns
    no bbox; the focus-zoom has nothing to zoom to. It is one of the 8 entries in
    `UNLOCATABLE_FLAGGED_WORD_BASELINE` for exactly this reason. Matching
    non-Hebrew tokens on their raw text was tried 2026-08-30 and reverted - it
    works and costs too much, moving 41 correct boxes and losing 2. The honest
    position is that punctuation-only flags are not locatable today.

48. **[2026-08-31, reviewer] Five more titles, and the editorial separator `[.]`
    inserted into 17 klalim — with the flag reindexing the insert made necessary.**
    Titles: 97/98/99 -> `ברייתא.` (first word only, the same cluster shape as
    131-133's `דיעבד`), 103/104 -> `ב"ד מתנין לעקור דבר מן התורה.`

    **The bare-separator count went 16 -> 21 because those title edits moved the
    boundary**, which is worth stating: shortening a heading exposes a gap that
    was previously inside it. Recomputed rather than reusing the earlier list.

    **17 got `[.]`, and 4 did NOT.** Klalim 180, 182, 190 and 217 have a period
    already — glued to the following token with no space (`.ודע`,
    `.דאמרי'בפ'`, `.לא`, `.דאמרינן`). That is a TOKENISATION defect, not a
    missing mark, and inserting `[.]` would have doubled the punctuation. Left
    alone and recorded here; the fix there is to split the token, which is a
    different operation and wants its own pass.

    **`[.]` and not `.`, deliberately.** The printed page has no mark at these
    positions — verified by rendering klalim 36 and 106 and reading the lines, not
    inferred. `[.]` is this repo's existing marker for punctuation added by review
    rather than set by the printer (`review_server.py:1603`, checked by
    `audit_applied_decisions.py`), so a bare `.` would assert something about the
    page that is false.

    **EVERY INSERT SHIFTED EVERY LATER INDEX IN ITS KLAL** — Lesson 35 / item 0C,
    the defect that once walked a flag onto the wrong word. The script reused
    `apply_reviewer_decisions.reindex_flags_after_shift()` rather than restating
    the rule, so a flag moved only where the word it named before is the word at
    the shifted index. **26 open flags reindexed, 0 unverified.** Each insertion
    also appended a `punctuation_choice` row to the ledger, so the change is
    traceable in the append-only log rather than appearing as an unexplained diff.

    **The full `./rebuild_all.sh` WITH vision had to run**, not `--skip-vision`:
    the shifts left 3 vision-adjudicated candidates (klal 36 w9/w60, klal 159
    w415) pointing at different words, and `test_no_stale_candidate_flags_are_
    being_served` caught exactly that and said so. 319 gated tests pass after.

49. **[2026-08-31, reviewer: "klal 73 two disputes but the red flag shows only 1"]
    NOT A COUNTING BUG — but it exposes a field that is served per-klal and
    rendered nowhere.** Verified by reading both entries and the rendered DOM.

    Klal 73 has two highlighted words and they are in different states:
    - **w27 `יוחנן`** — DocAI read `יוהנן` (ה for ח); the vision check selected the
      stored text at **0.98** and transcribed `יוחנן`; context is `משום דר' יוחנן
      תנא הוא`, and Rabbi Yochanan is right. Flag `current_text_confirmed`, so it
      renders `state-machine`. **Nothing for a reviewer to decide.**
    - **w87 `עלי`** — Surya and the VLM both read `על`; flag
      `current_text_may_be_wrong`; renders `state-open`. **This one needs a
      ruling.**

    The red badge counts `machine_disputed_count`, which is 1, and that is
    deliberate: item 17 changed it in 2026-08-25 precisely because counting
    total-flagged made a klal look like outstanding work when the machine had
    already settled most of it. So the badge is right, and "two disputes" is also
    right — they are two disputes, one of them resolved.

    **THE REAL GAP: `machine_resolved_count` is served per klal and only ever
    summed into the LEGEND total** (`app.js:680`); no nav row shows its own. So a
    klal with one resolved and one open word shows a single badge and looks like
    it has one highlighted word, when it has two. That is Lesson 29's shape in
    miniature — a field computed, served, and never rendered where it would
    answer the question a reviewer is actually asking. **Not fixed**: adding a
    third badge changes every one of the 222 rows and is a presentation decision
    for the reviewer, not an engineering default.

47. **[2026-08-31, reviewer chose option (a)] The heading/text separator: almost
    nothing was normalisable, and the one case that was is a MISREAD, not a
    missing period.** Asked to make each klal read heading-then-one-period-then
    text, I surveyed what actually sits after the heading run in all 222:

    | separator after the heading | count |
    |---|---|
    | `[.]` | 92 |
    | `.` | 61 |
    | `•` | 46 |
    | no mark at all | 16 |
    | `-` | 4 |
    | `:` | 2 |
    | `,` | 1 |

    The reviewer chose **(a): normalise only the bare and comma cases, leave
    `[.]`, `•` and `:` as the faithful record.** Two reasons that was the right
    call, both established before acting: **`[.]` is a provenance marker, not a
    period** — `review_server.py:1603` writes it when a reviewer ACCEPTS a
    proposed punctuation insertion and `audit_applied_decisions.py` checks for it
    specifically, so flattening 92 of them to `.` would erase the distinction
    between the printer's punctuation and ours and break that auditor — and `•`
    and `:` are marks that are **on the page**.

    **The 16 bare cases are correct as they stand.** Rendered klalim 36 and 106 at
    3x and read the lines: `לו אלא אין דרך השית' סדרי...` and
    `קו בחירתא היא מס' עדיות י"א שאינו...`. **The printer sets no mark there** —
    the bold lead word runs straight into the text. Inserting a period would be
    adding punctuation the original does not have, which is exactly what the `[.]`
    convention exists to record. No edit made.

    **The single comma is a misread middle dot.** Rendered klal 105 at 4x: the
    printer sets a raised `·` after `אמרו` — **the same mark it sets after
    `נינהו` later on the same line, which the corpus already transcribes as `•`**.
    One printed mark, two transcriptions. So this is not "a comma that should be a
    period"; it is `,` -> `•`, and the fix restores agreement with the ink rather
    than imposing a house style on it.

    **Recorded as a word-level flag, not a hand-edit.** Titles were hand-edited
    this session because no apply path exists for that field; `clean_text` HAS
    one, so the single-source-of-truth rule applies at full strength and this goes
    through the dashboard like any other correction. Flag `2e1168f7e5f3` on
    klal 105 w4, carrying the scan reading.

    **CLASS SWEPT, deliberately not flagged: Part 1 carries 26 commas across 23
    klalim** (klal 4 w27, 31 w159, 36 w66, 41 w609/w717, 44 w433, 54 w341,
    70 w94, 83 w41, 91 w579, 94 w22, 100 w31, 105 w4, 118 w14, 126 w44,
    134 w5, 140 w113, 146 w7/w36, 147 w67, 154 w398, 155 w110, 159 w63,
    161 w16, 167 w566/w1067). Any of them may be the same misread; **only klal
    105 w4 has been read against the scan.** The other 25 are recorded here
    rather than flagged, because 25 flags on unread material is how the 1,496-flag
    queue in item 1 happened. Whoever picks this up: the check is a 4x render of
    the line, and the tell is whether the same glyph appears elsewhere on the line
    already transcribed as `•`.

44. **[2026-08-31] I OVER-CORRECTED SEVEN TITLES ON MY OWN INFERENCE AND
    REVERTED THEM. Recorded because the reasoning error is the useful part.**
    The reviewer named klalim 101 (missing `ב"ד`), 105, 132/133 and 134/135.
    Rendering `page_44.png` and `page_49.png` at 2x showed the printed heading of
    each klal set in BOLD — `בית דין` for klal 100, `ב"ד` for 101-105, `דיעבד`
    for 131-133, `דחיה` for 134-135 — and I generalised that into a rule: **the
    title is the bold lead run**. On that rule I truncated klalim 100-105 to
    `בית דין.` / `ב"ד.`, including four the reviewer never mentioned.

    **The rule is wrong.** The reviewer's next message gave klal 105's title as
    `ב"ד שלאחריהם אמרו` — bold word PLUS the following phrase — and klal 106's as
    `בחירתא היא מס' עדיות`, where `בחירתא` alone is what is bold. So the heading
    is not the bold run; the bold is a lead-in and the heading continues past it
    by an amount only a reader can judge. Klal 132 (`דיעבד`) and klal 105
    (`ב"ד שלאחריהם אמרו`) are the same typographic shape with different answers.

    Reverted: klal 100 to its original title (never asked for), and 101-104 given
    the `ב"ד` they were missing rather than a truncation, which is what the
    reviewer actually asked for. 105 and 106 set as dictated.

    **What I should have done, and the rule going forward: STOP INFERRING A
    GENERAL RULE FOR TITLE EXTENT.** I have now guessed it twice — first that
    titles were the whole opening sentence, then that they were the bold run —
    and been wrong both times, in opposite directions. Lesson 31's shape exactly:
    a heuristic retuned twice is asking to be handed back, not tuned a third time.
    Title extent is a per-klal reading against the scan and is the reviewer's
    call; the tooling's job is to SHOW the comparison
    (`tools/compare_titles_to_text.py`), not to decide it. **27 Part 1 titles are
    long-but-clean prefixes and remain unadjudicated** — flagged as suspicion,
    with no rule applied to them.

    Part 1 title state after all of this: **222/222 clean prefixes, 0 divergences,
    0 offsets.**

45. **[2026-08-31, reviewer] The index shows a title without its terminal period;
    the running text keeps it, because there it does a job.** "no period in the
    index pane - it is needed in the text pane to sep the title from the text."
    The period stays on the stored field, where the gated invariant requires it —
    this is a presentation choice, stripped at render by `displayTitle()`, one
    function so every list surface agrees. In a column of 222 headings the period
    is noise; in running text it is the only thing marking where the heading
    stops. Spacing added around the heading run in the text pane
    (`margin-inline-end`, logical properties so it stays correct in the RTL
    column) rather than a wider word-space, so the gap falls once at each boundary
    instead of between every heading word.

46. **[FIXED 2026-08-31 — item 0E, reported by the reviewer as "clicking on 105
    in the index moves the text pane but not the scan".** The symptom was ONE KLAL
    OFF, not a dead pane: the scan did move to page 44, but the scroll observer
    set the active klal to **104** on the way past, so the header read "Klal 104"
    and the scan outlined 104's region while the text pane sat on 105.
    `jumpTo()` released the observer after a fixed **700ms** and a long smooth
    scroll takes **~1500ms** to settle.
    Fixed by `releaseObserverWhenScrollSettles()`, which waits for the scroll to
    actually stop — two consecutive frames at the same offset, with a 3s ceiling
    so a pane that never settles cannot suppress the observer forever — and then
    re-asserts the destination, since the observer was held off for the whole
    animation and never recorded where it landed. **A bigger constant would have
    been the same bug with a longer fuse** (Lesson 31: remove the guess, do not
    retune it).
    Gated by `test_a_nav_jump_lands_on_the_klal_it_was_asked_for`, which asserts
    the active klal AND the scan page because the bug moved one without the other,
    and covers the longest jumps deliberately — at the end of the corpus the
    scroll clamps and cannot put the destination at the top of the pane, so the
    observer's "last block above the reading line" answer is structurally wrong
    there. **Verified it catches the real bug**: with the 700ms behaviour restored
    it fails with "jumped to klal 105 but the index made klal 104 active".
    Two findings about the test harness, worth keeping: `suppressObserverScroll`
    and `currentPage` are script-scoped `let` bindings, NOT window properties, so
    polling `window.currentPage` silently reads `undefined`. Both are now read
    from the DOM (the scan `<img>` src carries the page number), which is the
    honest place to ask what is actually on screen.

42. **[2026-08-31, reviewer] Titles: two more extent fixes, and a punctuation
    rule now gated. Part 1's title field is, for the first time, internally
    consistent.**

    | klal | was | now |
    |---|---|---|
    | 10 | `איידי דקתני במתניתין ואינו עובר עליו נקט נמי בברייתא הכי` | `איידי דאיידי.` |
    | 66 | `אין ביטול ממש אבל להוסיף על תקנתם לאו ביטול מקרי` | `אין ב"ד יכול לבטל דברי ב"ד חבירו אא"כ גדול ממנו בחכמה ובמנין.` |

    Both were the two divergences item 41 could not classify, and both were the
    same shape as klal 36: the stored title was not a misspelling of the heading,
    it was **different text entirely**. Part 1 now has **0 divergences** — every
    one of its 222 titles is a clean prefix of its own body.

    **TERMINAL PUNCTUATION, applied to all 222** (reviewer: "each title should end
    with one period - no more no less. no other punct acceptable"). Not one Part 1
    title ended with a period before this; none contained one at all. All 222
    changes were **pure appends** — the dry run confirmed nothing was removed from
    any title, which is what made this safe to apply in bulk.

    **WHAT "no other punct" WAS NOT ALLOWED TO MEAN.** Read literally it would
    strip `"` and `'`, and those are gershayim and geresh — parts of Hebrew
    ABBREVIATIONS, not sentence punctuation. `ב"ד` is בית דין and `וכו'` is a word;
    removing the marks would have corrupted **121 and 80 occurrences**. The
    reviewer's own klal 66 title, supplied in the same message, contains `ב"ד` and
    `אא"כ`, which settles the reading. Five titles legitimately end `וכו'.`,
    keeping the geresh that belongs to the word and taking the period after it.

    Gated by `test_every_part1_title_ends_with_exactly_one_period`. Verified it can
    fail, per Lesson 25: replacing klal 1's period with a colon fails it by klal id
    and reason. **Scoped to Part 1 deliberately** — Parts 2-3 titles are machine
    truncations (`…`, and some are literally `כלל 447`) rather than transcribed
    headings, so normalising their punctuation would be both gate-violating and
    meaningless. `corpus_io.title_word_span()` is unaffected by the new periods
    because it normalises through `hebrew_letters_only`, verified on five klalim
    after the change.

43. **[2026-08-31, reviewer] The two standalone corpus reports are now stage 5b
    of `rebuild_all.sh`, because they had silently aged out of agreement with the
    corpus.** Raised by the reviewer directly.

    **The mechanism, stated plainly.** `tools/list_ligature_words.py` and
    `tools/review_lexicon_only_words.py` each read the corpus and write a JSON
    report, and **neither was in any chain**. So each report kept whatever numbers
    it had from the last time somebody remembered to run the tool. Nothing was
    wrong with either tool. `ligature_words.json` was stamped 2026-08-30 21:49,
    before that night's corpus edits, and still claimed **`both_lost: 3`** when two
    of those three ampersands had been repaired to `אל` (klal 69 w338, klal 167
    w24) and only klal 77 w11 survived. `lexicon_yad_malachi_only.json` was stale
    the same way.

    **Why it matters more than a wrong number in a file:** a stale count is
    exactly the kind of figure that gets quoted into a status entry or a decision
    as though it were measured today. This file's own TL;DR says every claim in it
    is measured rather than remembered; an unrebuilt report quietly breaks that.

    This is **Lesson 32 in its milder form** — not a detector nobody runs, but a
    report nobody RE-runs — and **Lesson 13** besides: a file fully computable from
    the corpus is a second copy of the truth until something rebuilds it.

    **FIXED by putting them in the chain**, the same remedy stage 4b got: measured
    at **0.28s and 0.24s** on the full corpus, so the reason for leaving them out
    never really existed. Both are pure readers — they write only their own report,
    never a flag, a decision or corpus text — which is what makes this safe to run
    unattended on every rebuild. `review_lexicon_only_words.py` needs the gitignored
    `sefaria_reference_corpus` cache and exits 0 with an explicit "this is not 'no
    findings'" message when it is absent, verified by hiding the cache, so a fresh
    clone is not broken by the new stage.

    **Two alternatives considered and rejected:** a gated staleness test comparing
    report mtimes against `part*.json` would DETECT the problem but then block the
    build until someone re-ran the tools by hand — detection where prevention costs
    half a second; and deleting the committed JSON in favour of print-only output
    would lose the diffable artifact these reports exist to provide.

    Post-rebuild the reports read `both_lost: 1`, dropped-lamed 321, dropped-alef
    18, and 1,144 lexicon-only words — and note that `both_lost` only became
    correct because the tool happened to be run, which is the whole argument.

41. **[2026-08-31, reviewer] A TITLE-vs-TEXT COMPARISON NOW EXISTS FOR EVERY
    KLAL, and the heading is rendered where the book actually puts it — inside the
    text, not above it.**

    **`tools/compare_titles_to_text.py`**, run over all 667. The structural
    property it tests: a title should be a PREFIX of its own `clean_text` after
    the gematria marker, because the printed heading is not separate text — it IS
    the klal's opening, set in larger type.

    | | all 667 | Part 1 |
    |---|---|---|
    | clean prefix of their own body | 581 | 216 |
    | …of which long (>= 11 words), a suspicion only | 24 | 24 |
    | DIVERGES — an OCR error in one of the two | 82 | 2 |
    | offset — title starts at a later body word | 4 | 4 |

    Part 1 is down to **2 divergences** (klalim 10 and 66, where the title matches
    almost none of its body and something structural is wrong) from 14 before this
    session's edits. **The remaining 80 divergences are all in Parts 2-3** and are
    untouched under the gate. Two lessons went into the tool rather than being
    discovered twice: editorial punctuation tokens in the body (`,` `.` `[.]` `•`)
    are SKIPPED, not counted as mismatches — without that, klalim 105 and 134 read
    as OCR divergences when the only difference is a comma the punctuation pass
    inserted; and a title that is a clean but LONG prefix is reported as a
    suspicion with the threshold stated, never as a finding, because this book's
    genuine headings run to 24 words and only the scan says where a heading stops.

    **The heading now renders IN PLACE** (reviewer: "i didn't want the title above
    the text… i want the text itself to have bold for counter and title in the diff
    font — right there in the text"). Yesterday's version put the title on its own
    line above the klal, which renders it twice, since those same words open the
    body. The marker is bold and the heading run is set in `--font-title`, both as
    words in the running text. `corpus_io.title_word_span()` computes how many body
    words the heading occupies and is shared by the server, the audit tool and the
    UI, so the three cannot disagree; it degrades safely, returning 1 for klal 66
    where the title matches only the first word.

    **Applied as a pass over the rendered spans, not inside the word loop** —
    that loop has five branches (plain, ai_flag, disputed, manual, witness) and a
    word is drawn by whichever claimed it, so decorating from inside would be the
    same two lines in five places (Lesson 13/34) and a heading word that happened
    to be disputed would silently miss out. `markTitleRun()` is one rule over the
    final DOM. Neither role class sets `color`, so the state colour a reviewer
    navigates by still shows through on a heading word.

    Sizes raised in both panes and the index number set in `--font-marker`, the
    same face as the text-pane head, so the number reads as the same object in
    both places. Gated by a regression that reads the expected heading length from
    `/api/klal/36` rather than hardcoding it, asserts the title is NOT repeated
    above the text, and compares resolved font families rather than literal names.

40. **[2026-08-31, reviewer] The index pane now carries both scripts on every
    line, and a long title can no longer squeeze the badges off the row.** Each
    row reads `39` · `לט` · title · flag · counts, and the text-pane head now
    reads `כלל 69 · סט` + section + the TITLE, which it never showed at all.

    **Structural typography tokens, added so this generalises past this book.**
    Four `:root` variables — `--font-title`, `--font-marker`, `--title-size`,
    `--marker-size` — plus one `.klal-title` role class used by BOTH panes. They
    name the ROLE a piece of text plays in a sefer's structure, not this printing's
    layout, so a work set differently restyles itself by re-pointing the tokens and
    touches no rules. Before this each pane styled its own text ad hoc, which is
    why the two could differ at all. The title face is deliberately NOT the body
    face: the body is Frank Ruhl Libre, so a title in it reads as more body text;
    `David Libre` is a different Hebrew serif of the same period feel. The
    regression compares RESOLVED font families between panes rather than asserting
    a literal font name, so re-pointing the token for another work keeps it green —
    which is the point of having the token.

    **The scan header's two scripts were separated by ONE SPACE, not the gap the
    rule claimed.** `#klal-indicator` had `margin-inline-start: 1.75rem`, and
    `margin-inline-start` resolves against the ELEMENT's own direction — that span
    is `direction: rtl`, so it became `margin-right: 28px` and put the gap on the
    far side, outside the row. What was left was the literal space in `index.html`:
    a measured **3px**, which is exactly what the reviewer saw. Now an explicit
    `margin-left`, measured at 31px. Gated by a test that asserts the rendered GAP
    between the two boxes — the property was present and read correctly the whole
    time, and only the geometry showed it was landing on the wrong edge. `gematria` has been on
    `/api/klalim` since 2026-08-26 and the nav simply never used it. The row's
    number columns and badges are all `flex-shrink: 0` and only `.ntitle` gives
    way — `.nid` was shrinkable before, which is what let a long title push the
    right-hand end of the row out of view. Gated by a regression that asserts the
    Hebrew column AND checks by GEOMETRY that every badge on the longest-titled
    row still has non-zero width inside the row box; it locates that row by
    looking for the badges rather than pinning a klal id, per item 0F.

    **REFACTOR NOTE, requested by the reviewer and earned the hard way: collapse
    the three duplicated init fetch blocks.** The same
    `Promise.all([/api/flags, /api/klalim, /api/witness])` appears in `init()`,
    `switchPart()` and the post-decision refresh path. Adding a fourth fetch to
    the wrong one of the three cost real time in this session (item 38) and the
    failure was silent, because the globals the OTHER copy sets still looked
    populated. It should become one `loadCorpusState(part)` that all three call.
    Not done here — it touches the app's startup path and wants its own
    before/after, and this session had already changed the frontend four times.
    This is the same shape as `union_bbox()` and the `.split(' ')` sites in
    item 37's structural list; it belongs with them.

38. **[2026-08-31, four reviewer reports on the deep-link flow — all four
    reproduced, fixed and gated.]** Each was measured in a real browser before
    being touched, and two of the four were not what the report said they were,
    which is the part worth keeping.

    **(a) The index pane did not scroll all the way to the klal.** `setActiveKlal`
    scrolled the nav with `block:'nearest'`, which moves the MINIMUM distance that
    makes the row visible. Correct for the continuous scroll-driven reaction it
    was written for; wrong for a jump. Measured on `/klal/210/word/133`: the row
    landed at bottom **1001px against a pane bottom of 1000px** — one pixel PAST
    the fold, so the single row the link exists to reach was the one row the
    reviewer could not see. A deliberate jump now centres; the scroll reaction
    still uses `nearest`, where it is a no-op when the row is already visible.

    **(b) "Moving the cursor over the text makes the highlight disappear" — it was
    not the cursor.** The `.routed-word` ring carried a hard
    `setTimeout(..., 4000)` and simply expired. Measured: the ring survives a
    mouse move at 900ms and is gone at 4s with the pointer untouched. 4 seconds is
    about how long it takes to read the line and start moving the mouse, so the
    two read as cause and effect. The ring now persists until the reviewer
    actually goes somewhere else (a new route, or `clearScanFocus`). **Worth
    noting as a diagnosis pattern: the reported trigger was a coincidence of
    timing, and believing it would have sent the fix into the hover handlers,
    which are not involved at all.**

    **(c) Clicking a highlighted word in the SCAN did not highlight it in the
    text.** The text→scan direction has had a single funnel since 2026-08-25
    (`focusWordOnScan`); the scan→text direction had **nothing** — a scan click
    moved the scan and opened a decision panel, and the middle pane was never
    told. Added `revealWordInText()` as the mirror funnel, shared with the
    deep-link router rather than copied. Two call sites, and the second is the one
    that mattered: **the `kind === 'plain'` box had no click handler at all**, and
    that is precisely the box a deep link draws — so the one word a shared link
    exists to point at was the one word clicking on the scan did nothing for.

    **(d) The scan header now carries the reference in both scripts** (reviewer:
    "Page xx Klal xx, white space, then the same info in Hebrew"). It reads
    `Page 73 · Klal 210` and then `דף עג · כלל רי`. Before, it showed the page in
    one span and a bare `כלל 210` in the other — a Hebrew word beside an Arabic
    numeral, which is not how the book writes it.
    **CAVEAT, recorded because it is genuinely ambiguous and could mislead:**
    `דף עג` is OUR page index written in Hebrew letters. **It is NOT the folio the
    printer set on that leaf** — the printed folio is stripped as page furniture
    (items 20 and 27) and is stored nowhere in this repo, so there is nothing to
    render for it. If that reads as a claim about the book rather than about our
    pagination, the Hebrew page half should be dropped and only `כלל רי` kept.
    The numerals are SERVED from a new `/api/numerals` endpoint over
    `cio.klal_id_to_gematria`, not reimplemented in JS: a JS copy would be
    Lesson 13, and would have had to re-derive the 15/16 exception (`ט"ו`/`ט"ז`,
    not `י"ה`/`י"ו`, which would spell divine names) and the final-letter rule.

    **I made this session's own Lesson 34 mistake while fixing (d), and it is
    recorded rather than quietly corrected.** The three-fetch block at init exists
    in **three** copies (`init`, `switchPart`, and the post-decision refresh) and I
    added the numerals fetch to `switchPart` — the wrong sibling. The header
    rendered `דף 73`, silently, because `hebNum()` falls back to the digits, and my
    own verification passed on `FLAGS`/`KLALIM` being populated, which `init` had
    done. What caught it was the server log showing **`/api/numerals` was never
    requested at all**. The fetch now lives in `init` only, since the table is a
    pure function of the integers and can never return anything new on a part
    switch.

    Four Playwright regressions, one per report, plus the 0G guard. **363 tests
    pass.** The three that can look their subject up off the DOM do so rather than
    pinning a coordinate (item 0F); the header test necessarily pins klal 210 /
    page 73, and asserts the Hebrew half contains `עג`/`רי` AND does **not**
    contain `73`/`210` — without that second half it would have passed against the
    digits-fallback bug it exists to catch.

37. **[SWEEP 2026-08-31] Every finding in every code- and data-review file
    re-verified against the live tree. Two new defects; item 9c was stale; the
    structural backlog is real but smaller than the review files read.** Method:
    each claim was reproduced by running or reading the current source, never
    accepted from the write-up (Lesson 19). Files swept:
    `code-review-2026-08-25.md`, `CODE-REVIEW-2026-08-26.md`,
    `CODE-REVIEW-2026-08-27.md`, `LEXICAL-DEFECT-AND-FLAG-AUDIT-2026-08-27.md`,
    `open_items_2026-08-30.json`, `cleared_flags_2026-08-26.*`, and this file's
    own open items.

    **NEW — see item 0G**: two UI tests shadowed by duplicate definitions, the
    stricter copy of each discarded.

    **NEW — the multi-word manual-replacement guard landed in ONE of the two
    files the audit named.** `CODE-REVIEW-2026-08-27.md`'s remedy #2 says
    explicitly "in both `apply_reviewer_decisions.py` and `tools/export_corpus.py`".
    `manual_correction_changes_word_count()` exists and is called at
    `apply_reviewer_decisions.py:592`; `export_corpus.py`'s manual-replace branch
    (its `else:` at ~line 151) calls `_apply_manual_correction` with **no
    word-count check and no `word_count_changed_klalim.add`**, though that same
    function guards its insert and delete branches. Item 36 recorded the fix
    without noting it was half-applied. This is Lesson 34 exactly — sweep the
    SIBLINGS, and the sibling here was named in the finding itself.
    Live exposure **0 today**: no manual decision has multi-word `chosen_text`
    (re-measured, not remembered). Latent, like its twin was.

    **Verified FIXED and holding** (each re-measured): the four item-36
    "critical" defects; the `_corpus_bbox_cache` invalidation (now keyed on a
    `part1/2/3.json` (mtime,size) stamp — note the stamp does NOT cover
    `docai_word_boxes/` re-extraction, which the original finding also named);
    item 20's watermark (**0 Latin-script tokens corpus-wide**); item 16
    (**71 placeholders / 596 with text**, exact); item 0D(a) (**0 new unlocatable
    open flags**; the baseline shrank 10 -> 7 as words were repaired); item 24
    (`lexicon.txt` **18,936** rows, exact); item 32 (175 intact / 321
    dropped-lamed / 19 dropped-alef / 3 both-lost / **0** U+FB4F, exact).
    All 317 gated tests pass; all 36 collected UI tests pass.

    **Verified STILL OPEN, structural, none of them new** — recorded here because
    they live only in the review files today: `synthesize_multi_witness.py:56`
    still imports `review_server` and calls three private helpers (C4);
    `review_server.py` is now **1,955 lines**, up from the 1,849 that was filed
    as a God Object and the 1,736 before that (S1); 12 `.split(' ')` sites across
    5 files (S2 — the review said "14+ across 7", it is 12/5); `_parts_for()`
    still returns Part 1 for `?part=4` (S4); `223`/`444`/`445` still inline in
    `review_server.py:132-146` and `corpus_io.py` still exports only
    `PART1_MAX_KLAL` (S5/#6); `_NO_UPPER_BOUND = 10 ** 9` (H2); `union_bbox()`
    still byte-identical in two pipeline stages (H3/#8); both superseded
    `extract_*_consensus_disputes.py` stubs still in `tools/` (H4); the
    `clear-word-flag` handler still duplicated in `app.js` (#18/#9).
    **#7 is weaker than filed**: `reconstruct_placeholder_klalim.py` imports
    `FURNITURE_WORDS` from `check_span_shortfall`, but that module is itself
    `FURNITURE_WORDS = cio.FURNITURE_WORDS` — an indirection, not a divergent
    copy, so it cannot drift. Worth tidying, not a Lesson 13 instance.

    **Item 27 is two-thirds done, and the remainder is now UNFLAGGED.** klal 74's
    seam is fully repaired (both spurious words deleted, 2026-08-30). klal 39 lost
    its `Π` folio — but the *catchword* `דבכולהן` at w251, which item 27 names as
    part of the same three-word defect, **is still in the corpus and carries no
    open flag**, because the flag that was cleared was the folio's. klal 210's
    Hebrew-numeral folio `לא` at w66 is still present and still flagged.

    **Two standalone reports are stale against the corpus they describe.**
    `ligature_words.json` and `lexicon_yad_malachi_only.json` are both stamped
    2026-08-30 21:49, before the 2026-08-31 corpus edits; `ligature_words.json`
    still lists `both_lost: 3` where only **1** `&` survives. Neither tool is in
    `rebuild_all.sh` — Lesson 32's exact shape, in a milder form: not a detector
    nobody runs, but a report that silently ages out of agreement with the text.
    `lexical_defect_report.json` does NOT have this problem; it is stage 4b and
    regenerated (now **280 candidates / 93 klalim / 194 unflagged**, against item
    35's dated 299 / 96 / 194).

    **Item 26 is down to one.** `validate_part1_corpus_integrity.py` check 2b now
    reports a single out-of-repertoire character, klal 77 w11 `&` — from 7.

    **`open_items_2026-08-30.json` WAS HAND-WRITTEN, and it rotted — now
    generated.** It is fully computable from `review_decisions.jsonl` plus the
    corpus, which makes a hand-kept copy Lesson 13 exactly: a "derived" file that
    is really a second copy of the truth, agreeing until the text moves under it.
    It moved. Six of its 24 flagged items were resolved and still listed as open,
    and its lead entry, "NEEDS YOUR RULING on klal 66 w0", had been ruled on the
    day before it was written. **`tools/build_open_items_report.py`** now derives
    the queue from live state; `tools/render_report.py` turns it into clickable
    deep links, so the list cannot age. Current Part 1 queue, measured:
    **233 open word-level flags, 88 open klal-level flags, 0 out-of-range,
    4 null decisions still standing.** The rendered `.md`/`.html` are gitignored,
    the same as every other report view.
    Two details the generator had to get right, both found by running it rather
    than reading it: it splits on a SINGLE space (`.split()`'s whitespace
    collapsing renumbers every word after a double space and points every link one
    word off), and `word_index == len(words)` is the legitimate END-OF-KLAL append
    position for an insert/delete opcode, not an out-of-range index — the two
    surviving null decisions at klal 88 w1149 and klal 164 w55 are both exactly
    that, and a naive bounds check filed them as corrupt.

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
