# Project Status — current state

## TL;DR

_Current state only. Every claim here is measured, not remembered; the dated
evidence for each is in `PROJECT-STATUS-HISTORY.md`._

> **Picking up where the last session stopped? This file is now the OPEN work
> only.** Eight items are live below; every other item ever written is indexed by
> id at the bottom with its body in `PROJECT-STATUS-HISTORY.md`. A reference from
> code or from another entry still resolves — nothing was deleted or reworded.
>
> **What is open, 2026-09-06:**
> 1. `0BO`'s plan — item 1 (the 26 unreviewed corrections) and item 3 (the
>    drifted rulings) are DONE; **items 2, 4 and 5 are not.** Read it for the
>    ledger measurements, but re-measure before quoting any of them.
> 2. `0BU` — generalization Phase 3 steps 1-3 (the ligature catalogue and the 24
>    corrupt forms). Step 5 is done. **Step 3's guard is the part not to skip:**
>    the invariant must keep its own literal and assert equality against
>    `cio.defects()`, never read its expectation from the file it guards.
> 3. `0BX` — the reindex collision guard. Needs a POLICY decision, not a fix:
>    refuse a re-point onto an occupied key, or record it and move anyway.
> 4. The scroll flake, `test_a_word_click_survives_the_scroll_that_follows_it`.
>    Re-measured 2026-09-06 at **3 failures in 6 runs**, not the "1 in 8" the
>    older entries say; it is now the likeliest cause of a red ungated run.
> 5. `16`, `20`, `0N`, `3`, `4` — the standing corpus and witness-queue items.
>
> **Done 2026-09-06 and archived:** stable word ids (`word_identity.py`) wired
> into every corpus writer and every position-resolving tool, with tombstones and
> restoration links; history addressable by word rather than by slot; the TEI
> export fixed (it crashed on the real corpus at every commit since it was
> written); book identity read from `book.json` on the deliverable path.

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

**What the witnesses are worth, measured.** **Dicta 95.6% word accuracy over
klalim 2–221 (full Part 1 coverage, 2026-09-02 — the strongest witness here)**,
VLM 93.3% token accuracy, Surya 89.9% mean agreement (222/222 coverage),
Tesseract 3.8% on disagreements — the last is why it is being retired (item 3a).
**Dicta is now a voting engine** (2026-09-04) and every dispute it takes part in is marked `cross_edition`, because its vote is a reading of a different PRINTING, not a second look at this ink. **P(consensus correct | two distinct
engines agree) is 26–41%**, so agreement routes attention and the ink decides;
auto-approval on consensus is indefensible at any threshold this data supports.

**The binding constraints.** The Parts 2-3 gate (`START_HERE.md`) still holds:
no `part2.json`/`part3.json` correction may be applied. Recording a decision and
applying it to the corpus remain two separate, deliberate steps.


## Open items

0CA. **[2026-09-06] THE SCROLL FLAKE IS THE DEFECT, NOT THE TEST - AND 11
    DISPUTES NEVER REACH THE DASHBOARD AT ALL.**

    ### The scroll "flake" is a live defect, and the obvious fix makes it worse

    `test_a_word_click_survives_the_scroll_that_follows_it` does not fail on a
    timing artifact. Reproduced: **clicked klal 2 w411, which is on page 15, and
    two seconds later the scan pane was showing page 14 - klal 2's START page.**
    The click had been silently undone, which is exactly the defect the test was
    written to catch. A reviewer clicking a word on a continuation page gets the
    wrong page about half the time.

    MECHANISM. The guard sets `suppressObserverScroll` and clears it on a fixed
    **900ms timer** (`app.js:1988`). The scroll a click starts does not finish on
    a schedule: lazy mounting resizes blocks and the browser's scroll anchoring
    moves `scrollTop` to compensate, so events keep arriving. Whenever they
    outlast 900ms the suppression has lapsed, `updateActiveFromScroll()` resolves
    the klal and `setActiveKlal()` shows its start page. Lesson 40's fix made it
    WORSE, not better: blocks can now SHRINK by up to 2,000px, so a long jump
    overshoots and takes longer to settle - which is why the rate moved from the
    recorded ~1-in-8 to ~50%.

    Lesson 41 exactly: a condition written as a time budget rather than as the
    thing itself.

    **THE OBVIOUS FIX IS WRONG AND WAS REVERTED.** Swapping the timer for
    `releaseObserverWhenScrollSettles()` - the existing settle-detector, which
    the nav-panel jump uses - took the failure from ~50% to **10 runs out of 10**.
    That helper does not merely release suppression: it **re-seats the block for
    `lastActiveKlalId` before releasing**, which is right for a klal jump and
    precisely wrong for a word click, because re-seating to the klal is what
    shows the klal's start page. Reverted; 8 runs afterwards gave 5 passed /
    3 failed, matching the control, so nothing was left damaged. Lesson 31 -
    handed back rather than tuned a second time.

    WHAT THE FIX ACTUALLY NEEDS: the wait-until-`scrollTop`-is-stable loop
    extracted from `releaseObserverWhenScrollSettles()` and used WITHOUT the
    klal re-seat. Two things to verify rather than assume - that the 3s ceiling
    covers the longest jump in this corpus, and that holding suppression longer
    does not strand `lastActiveScanPage` so a later genuine scroll stops updating
    the pane.

    Also swept: four sites suppress the observer. The nav-panel jump
    (`app.js:4222`) correctly pairs `behavior:'smooth'` with the settle-detector;
    `revealWordInText` (~693), `applyHashRoute` (~800) and the word click (1987)
    all use the 900ms timer. Only the word click is demonstrated to fail, but the
    other two are the same proxy-for-condition shape.

    ### 11 disputes that no reviewer can reach

    Measured end to end: all **453** stage-4a consensus disputes do reach
    `corrections_part1.json`, and the API serves **929** items against **928**
    distinct word slots the frontend draws. The loss is small and entirely one
    shape - a `delete` opcode has no word of its own, because it proposes
    inserting BEFORE an index, so it has no anchor to render on.

    **10 append-position proposals**, every one `delete`-opcode at
    `word_index == len(words)` - "DocAI read a word after this klal's last one".
    The API serves them; there is no `[data-word-index=N]` span to attach to, so
    nothing is drawn. Several are substantive: klal 211 `בשם התוספות`, klal 175
    `הלכה 7`, klal 88 `בעיא 4`, klal 84 `4 בעיא`, and 6 more in klalim 106, 114,
    138, 159, 164, 193.

    **AND THE NAV COUNTS THEM.** Klal 211 reports `correction_count` 4 and
    `open_count` 4, one of which is this unreachable, undecided
    `possible_omission`. The reviewer is told there are four things to do and can
    reach three. Klal 88 the same, inside its 11 open.

    **1 collision**: klal 68 w29 holds a `delete`-opcode proposal and a
    `manual_correction` at one index. `claim_word_index` exempts `delete` from
    collision detection on purpose - it has no slot of its own - and app.js's
    `byIndex[c.word_index] = c` then keeps the last, so the insertion proposal is
    invisible. The exemption is right server-side and leaves the frontend with
    two entries and one slot.

    NOT FIXED - both need a UI decision rather than a code change: an insertion
    proposal needs somewhere to be drawn that is not a word (a gap marker between
    words, which `.punct-marker` already demonstrates the shape of), and the nav
    counts must either exclude what cannot be reached or the marker must exist.

0BZ. **[2026-09-06] THE ID REACHES EVERY POSITION-RESOLVING TOOL; TWO DEAD
    FUNCTIONS OF MY OWN REMOVED; THIS FILE SPLIT SO THE PRIME DOCS LOAD IN ONE
    READ.**

    ### Callers

    Three tools resolved a position without consulting a stable id.
    `repoint_stale_decisions.py` now asks it FIRST and re-points on it alone -
    everything else there infers a position and demands two signals agree because
    inference can be wrong, and an id is not inference. A `retired` id is refused
    rather than re-pointed: the word was deliberately removed, so moving the
    ruling anywhere would attach a human's decision to a word they never saw.
    `close_satisfied_rulings.py` gained a `word_id` tier that skips the aliasing
    question its other tiers exist to answer (`אליבא` x11 in klal 91).
    `audit_applied_decisions.py` turned out to be id-aware ALREADY through
    `rd.resolve_word_index` - the earlier "0 id-aware refs" reading was a false
    negative from grepping for the wrong tokens - but it had never been taught
    the two statuses that call adds, so it was bucketing a `word_id` address as a
    STALE one and had no wording for `retired`. Both fixed.

    All three are PROSPECTIVE: 0 of the 594 rulings on record when ids began
    carry one, so none fires on today's ledger. Each is driven by a synthetic
    ruling in the suite, because untested they would be exactly the built-and-
    never-exercised shape this week keeps finding.

    ### Half-finished sweep

    Swept every function in `pipeline/` and `tools/` for ones nothing calls. The
    first pass reported 57 and was WRONG - its regex excluded dotted calls, so
    `cio.align_witness(` did not count. Corrected, it reports 16, of which 14 are
    aliased (`_load_alignment = rdata.load_alignment`) or dispatched from a
    registry or an argparse `type=`. **The only genuinely dead code was two
    functions I added this session** - `word_identity.seed()` and
    `drift_recovery.load_corpus_words()` - both unused since written. Removed.

    ### The document split

    `PROJECT-STATUS.md` had reached **7,646 lines**, past what a single `Read`
    loads, which makes START_HERE's "read PROJECT-STATUS.md first, every session"
    impossible to honour literally - the same failure that forced the 2026-08-12
    split, recurring.

    It now holds **the open items only: 930 lines**. Every one of the 137 items
    is still listed by id in an index table at the bottom, with its body moved
    verbatim to `PROJECT-STATUS-HISTORY.md`. **Nothing was deleted or reworded**,
    and ids did not change, so a reference from code (`apply_reviewer_decisions.py`
    and three test files cite `0A`, `0B`, `0C`, `0F`, `0R`, `0U`, `0W` by name) or
    from another entry still resolves. Verified mechanically before committing:
    137 of 137 ids findable in the status file, 0 bodies missing from the
    history, 0 duplicated, TL;DR and the item-ID lane rule both preserved.

    Prime docs now: `START_HERE.md` 1,210, `PROJECT-STATUS.md` 930, `CLAUDE.md`
    27, `README.md` 59 - each loadable in one pull.

## Open items

0BO. **[2026-09-05] SESSION LOG AND THE NEXT SESSION'S PLAN. Read this first;
    it is the handoff.**

    **A PROCESS BREACH TO NOTE, because the next session should not repeat it.**
    Almost everything below was written only into commit messages during the
    2026-09-04/05 session, not into this file, which is the standing requirement
    ("log every finding immediately, without being asked"). Only the Dicta
    wiring, `HOW-THE-PIPELINE-WORKS.md`, and Lessons 38-45 were logged as they
    happened. This entry is the batched catch-up the rule exists to prevent.

    ### Where the corpus stands (re-measure; do not quote these)

    | | |
    |---|---:|
    | rulings naming a text | 690 |
    | applied | 625 |
    | unapplied | 65 — the applier is CONVERGED at 0 applicable |
    | drifted, needs a human | **39** |
    | open disputes (`current_text_may_be_wrong`) | 454, of which **362 cross-edition** |
    | open klal flags | 385 (~82% machine-raised) |
    | unreviewed machine corrections IN the corpus | **74**, of which **32 carry no flag** |

    ### What was built (all committed and pushed, `3897d65`..`a5942bc`)

    **Dicta votes** (`3897d65`). Stage 4a 283 -> 506 disputes; 405 involve
    Dicta, 223 with only ONE Berlin engine dissenting. Every such record carries
    `cross_edition`, `same_edition_agreeing` and `abbreviation_shape`, rendered
    three ways in the dashboard, and `chosen_source: "dicta_reading"` is
    greppable in the ledger. Stage 4d (`build_collation_report.py`) reports 74
    genuine cross-edition differences as COLLATION that is never a correction.

    **`abbreviation_shape` found a real defect class**: 18 positions where the
    corpus read the abbreviation geresh as a YOD (`מה׳` stored as `מהי`). The
    reviewer has closed most; 5 remain.

    **Two applier defects, both live for weeks.** (i)
    `settled_by_an_applied_decision` tested `if chosen:` on `chosen_text`, and an
    applied DELETION carries an empty one — so **every applied deletion fell
    through and its verified entry returned on the next rebuild**. 35 decisions
    were in that state. (ii) `all_current()` does not honour `supersedes`, so a
    re-pointed ruling stayed live at its OLD key while its replacement was
    applied — the applier retried **8 of them every run**, counted as work a
    human owed. Both fixed; `superseded_by_an_applied_decision()` is the new
    predicate.

    **New tools.** `close_satisfied_rulings.py` (closed 36 rulings the corpus
    already held, in three tiers, refusing 3 where a repeated word had no ink
    corroboration — klal 66 w17's bbox resolves to w34, so closing it on text
    alone would have been wrong). `list_drifted_rulings.py` ->
    `DRIFTED-RULINGS-WORKLIST.md`. `analyze_decision_ledger.py`.
    `list_cross_edition_disputes.py` -> `CROSS-EDITION-WORKLIST.md`.

    **Item 0BI moved.** The four scripts that write corpus-shaped output
    (`apply_punctuation_decisions`, `reconstruct_placeholder_klalim`,
    `patch_witness_word_indices`, `export_corpus`) now split INSTALL_DIR from
    `repo_path()`, verified against a temp `$SEFER_CORPUS_ROOT`. **The guard's
    detector used `os.listdir` and could not see subdirectories** — it read 51
    while the real figure was higher. Now recursive and exact in BOTH directions
    (fixing a script fails until its name is struck off). `KNOWN_BYPASS_COUNT`
    51 -> **47**.

    ### What the ledger says (from `tools/analyze_decision_ledger.py`)

    * **The vision arbiter's confidence carries no signal.** 0.972 mean when
      right, 0.962 when wrong, 169 of 171 ratings in one narrow band. Any
      threshold on it (`MIN_VISION_CONFIDENCE`) selects nothing. When it
      PROPOSES A CHANGE it is right 6 times in 50.
    * Head-to-head (the unbiased comparison): **VLM beats Surya 42-9**, Dicta
      beats Surya 9-4 and VLM 5-4. DocAI's apparent 12% is selection, not
      accuracy — candidates are generated FROM its disagreements.
    * **Raw DocAI 0% vs ligature-repaired 97%** on the same 36 positions.
    * Consensus ladder on human-ruled positions: 1 engine 3%, 2 engines 57%,
      3 engines 73%. NOT the same quantity as `estimate_consensus_posterior.py`'s
      26-41%, which uses the vision arbiter on UNDECIDED positions precisely
      because this sample is selected.
    * Error signatures differ by engine, which is why consensus works at all:
      DocAI ד/ר 25x, Surya ו/ז 10x, VLM diffuse.

    ### NEXT SESSION — do these, in this order

    **1. Make the 32 unfindable corrections findable.** They are applied to the
    corpus, no person has reviewed them, and they carry NO flag, so nothing in
    the dashboard shows them. `tools/flag_unreviewed_auto_corrections.py`
    reports exactly why: **27 skipped because the position has DRIFTED** — it
    will not write a flag at an index that no longer names its word (item 0AB's
    failure). The fix is machinery that now exists: re-derive the position from
    the snapshot bbox with two-signal corroboration, as
    `repoint_stale_decisions.py` and `close_satisfied_rulings.py` do. EXTEND
    THAT TOOL; do not write a fourth worklist. Highest priority because the
    corpus currently holds text nobody verified and there is no queue entry
    pointing at it.

    **2. Generalization Phase 3 — extract print-run defect knowledge.** Reviewer
    approved the shape on 2026-09-05 and asked to see the inventory first; it is
    below, and it was shown. No second book is in view, and the reviewer
    confirmed Phase 3 can proceed without one.

    *The mechanism already exists* — `book.json` + `corpus_io.book_identity()` +
    `_WORK_DEFAULTS` is Phase 2's, resolved at call time through the seam.
    `book.json` does not exist on disk; the defaults carry Yad Malachi. Phase 3
    adds a `defects` block in the same shape as Phase 2's `parts` array, read
    through `corpus_io`, with today's values as defaults so behaviour is
    identical for this book.

    | what | where it is now | why it is this book's |
    |---|---|---|
    | ligature catalogue (`alef_lamed` ﭏ, `chet_zayin`) | `pipeline/typography.py`, hardcoded | sorts THIS compositor used |
    | `dropped_lamed_explains()` | `typography.py` | the detector for one specific sort |
    | the 24 corrupt forms | **TWO copies** — `tests/test_corpus_invariants.py:697` and `tools/validate_lexicon_independent.py:77` | the words this ligature produced in this text |

    Three cautions recorded with the reviewer:
    - The 24 forms are **already duplicated**, and the second copy's own comment
      says "same 24 forms as" the first. Extraction collapses a live Lesson 13,
      which is an argument for doing it.
    - They are **not purely a property of the press**: 7 of the 24 are attested
      Hebrew words, which is why the ligature guard needed a per-position
      human-ruling exemption (item 0AX). Extract them labelled as
      MEASURED-FROM-THIS-CORPUS, not as a declared fact about the printing.
    - `ABBREV_MARKS` is probably universal Hebrew — leave it. "Berlin" appears in
      15 Python files but is mostly explanatory PROSE; extract only what is
      behaviour (paths, labels, the edition string) and leave the commentary
      alone, or 15 files get worse.

    **3. The 39 drifted rulings** are human work, not engineering.
    `DRIFTED-RULINGS-WORKLIST.md` has them bucketed by which signals exist.
    Regenerate it after any apply.

    **4. Known-flaky, pre-existing, NOT from this session's work.**
    `test_a_word_click_survives_the_scroll_that_follows_it` fails roughly 1 run
    in 8 — measured with `app.js` reverted to HEAD, so it is not the scroll
    changes. Worth fixing; nobody has.

    **5. Still open and untouched:** Phases 4 (UI vocabulary — "klal",
    "gematria", "section" are hardcoded across `app.js` and the server) and 5
    (onboard a second book, the only phase that can validate 1-4). The 47
    remaining seam bypasses. The nav label drifting at the very end of the
    corpus is FIXED (`endClampKlalId`), but its root cause — the container
    clamping so a jump cannot reach the reading line — is inherent.


### The Dicta pass is COMPLETE — pages 22–114, all of Part 1

_Closed 2026-09-02. The reviewer submitted the five remaining chunks by hand and
dropped the results in `~/Downloads`; they were validated, copied into
`dicta_output/`, and the baseline rebuilt. This section was the file's top open
item since 2026-08-31 and is kept only as the record of what it produced._

**`tools/second_witness_eval/dicta_jerusalem_part1_baseline.txt` now covers scan
pages 22–114** — 467,093 bytes, 10 chunks, header self-flipped from PARTIAL to
COMPLETE. `build_dicta_baseline.py` refuses to write on a gap or overlap, so the
clean write is itself the contiguity proof.

| measured over klalim 2–221 (51,115 reference tokens) | |
|---|---:|
| Dicta word accuracy | **95.6%** |
| lexicon hit rate | 97.1% (corpus ceiling 97.8%) |
| positions Dicta votes at | 50,362 of 52,057 |
| …agreeing with the corpus | 48,842 (97.0%) |

**95.6% across the whole of Part 1, against 95.5% measured on the pages 22–50
third** — the score held when coverage tripled, which is the thing a partial
measurement could not tell us. Dicta is now the strongest witness this project
has by a wide margin: VLM 93.3%, Surya 89.9%, Tesseract 3.8%.

**WIRED IN 2026-09-04, at the reviewer's instruction.** All three integration
points item `0N` named are done: `synthesize_multi_witness.ENGINES`,
`assemble_corrections_dataset.py`, and a `dicta_reading` option in `app.js`
(without that last one the field would be serialized and never seen — Lesson 29,
and this file's history has two prior instances of exactly that).

**Stage 4a went from 283 to 506 consensus disputes.** 405 of the 506 have Dicta
among the agreeing engines; **223 of those have only ONE engine that read this
scan** dissenting from the corpus, which is the number a reviewer needs and
cannot get from the engine names alone.

**How a cross-edition dispute is RECOGNISED**, since its vote does not mean what
a same-edition vote means. Three fields on every record, rendered in three
places:

| field | says |
|---|---|
| `cross_edition` | a different printing is one of the agreeing voices |
| `same_edition_agreeing` | how many engines that read THIS scan differ from the corpus (1 = the ink has a single dissenter) |
| `abbreviation_shape` | this disagreement is about an abbreviation mark, in one of two directions that mean opposite things |

In the dashboard: the reading is offered as a choice labelled *"Dicta reading — a
DIFFERENT edition (Jerusalem 1975/6)"*; the panel shows an amber warning banner
naming the edition and, where `same_edition_agreeing == 1`, saying the ink has
one dissenter; and the word carries a superscript **J** in the text pane so the
reviewer can spot these without opening each one. In the ledger, a decision that
took Dicta's word records `chosen_source: "dicta_reading"` — the only source in
the schema that is not a reading of this book's own scan, greppable on purpose.

**`abbreviation_shape` found something, and it runs both ways.** Measured on the
real corpus:

* **`consensus_abbreviates` — 18 positions** where the consensus would RESTORE
  an abbreviation mark the corpus spelled out. This is item `0AQ`'s own defect
  found systematically: the corpus reads the abbreviation geresh as a **yod**,
  so `מה׳` is stored as `מהי` (7 instances), `הל׳` as `הלי`, `התוס׳` as `התוסי`.
  Real correction candidates. The class was already 13 without Dicta; Dicta adds
  5 and corroborates the rest — which is the clearest thing it has earned.
* **`consensus_expands` — 4 positions** where the consensus would SPELL OUT an
  abbreviation the corpus stores. All 4 are cross-edition with
  `same_edition_agreeing == 1`, exactly the profile that says "the other
  printing writes it out." Item `0AQ` ruled the Berlin abbreviation is what the
  corpus keeps, so these are flagged with that ruling quoted in the note, not
  proposed as fixes.

**The preview (`DICTA-NEW-DISPUTES.md`) reports 223 new disputes, 182
corroborated, 1 position a human already ruled against, 0 displacing a different
consensus** (regenerated 2026-09-04; it read 225/186/8 before the 0AQ rulings
were applied). 223 is 3.8x the 58 from the partial baseline — inside the 3–4x
this file predicted, and it is the number that actually landed. **It is still a PREVIEW: nothing is wired into `rebuild_all.sh`,**
and wiring it in remains a separate decision (item 0N has the three integration
points: `synthesize_multi_witness.ENGINES`, one line in
`assemble_corrections_dataset.py`, and a `dicta_reading` option in `app.js` —
without that last one the field is serialized and never seen, Lesson 29).

**What its SOLO differences are worth, measured 2026-09-04 — and the answer
corrected a guess this file used to carry.** Dicta reads a different PRINTING
(Jerusalem 1975/6), so a position where Dicta alone differs could be a real
difference between the editions. There are 943 of them, and `preview_dicta_
disputes.py` used to say in its own output that such a position "is usually a
textual variant rather than a misread." **That was wrong.** Of the 68 that
differ only by a vav/yod swap, DICTA's reading is unattested in 6.18M words of
independent Hebrew 24 times against the corpus's 4 — roughly 6:1 that the
witness, not the edition, is the source (`הטור`→`הטיר`, 0x attested;
`אותו`→`איתו`, 9,384x against 1x). At 95.6% accuracy over ~50,000 aligned
positions Dicta is expected to misread ~2,000 words, so 943 solo-differs is
consistent with mostly noise. The sentence has been corrected in the script.

**The subset that IS a real cross-edition difference is now collated, and is
never a correction.** `pipeline/build_collation_report.py` (stage 4d) reports
only the structurally verifiable class: the Berlin word ends in a geresh and the
Jerusalem word continues the same letters, so it is the same word abbreviated in
one printing and spelled out in the other — the shape itself is the evidence,
not a judgement about which is right. **74 rows across 48 klalim; 67 of the 74
expanded forms are attested in the independent corpus (91%)**, scored as
corroboration and not as the selection rule. Output: `collation_report.json` and
the readable `EDITION-VARIANTS.md`.

This artifact is deliberately **not** wired to the dashboard and nothing
downstream reads it. Applying a row would edit the Berlin text to match
Jerusalem — the exact thing the reviewer ruled against in item `0AQ`, where the
corpus had to keep `ומתי׳` over the editorial expansion `ומתיר`. Every row
carries `"actionable": false` and no field the applier keys on. Six tests in
`test_pipeline_logic.py` hold the boundary, two of them proving the gate can
fail: a position where a Berlin engine ALSO differs is refused (that is stage
4a's dispute, not collation), as is a position no Berlin engine read at all.

`job_id` is null for the five new chunks in `dicta_chunks_remainder/manifest.json`:
they were fetched by hand from the RashiOCR status page rather than through
`tools/fetch_dicta_result.sh`, so no job id was ever seen here. Left null rather
than invented — a value in an audit trail that resolves to nothing is worse than
an absent one.

**The two standing constraints still hold.** Never point Dicta at the square
Berlin scan (77.6% there, worse than everything already wired in), and Dicta is
deterministic (item 0V), so a repeat run buys nothing: it cannot be its own
reliability check, and every dispute still needs the ink or a different engine.

> **Item IDs are allocated per LANE, and are never reassigned once written.**
> Two concurrent sessions share this file, and a newest-first list with
> hand-picked single letters cannot survive that: both writers reach for "the
> next letter" and collide. It happened twice in one day — `0S/0T/0U`, then
> `0V/0W/0X` within hours — and renaming after the fact is not a fix, because
> item IDs are load-bearing: `apply_reviewer_decisions.py` and three test files
> cite them by name in comments (`item 0A`, `0B`, `0C`, `0F`, `0R`, `0U`, `0W`).
>
> - **`0A`–`0Z` — the review/corpus lane** (the main clone, which holds the
>   dashboard and the decision ledger).
> - **`1A`–`1Z` — the refactor lane** (the `-refactor` worktree).
> - A third lane takes `2A`–`2Z`. **Before writing an item, grep the file for
>   your next letter** — the cost of checking is one command; the cost of not
>   checking is an ambiguous cross-reference that a rename cannot safely undo.
>
> Resolved 2026-09-01 by moving the refactor lane's three colliding entries to
> `1G`/`1H`/`1I` — chosen over renaming the review lane's because those are the
> ones code references.

> **The review lane has run out of single letters — `0A`–`0Z` are all
> allocated.** Continuing as `0AA`, `0AB`, … in the same band rather than
> borrowing `2A`–`2Z`, which names a different lane and would misattribute the
> work. Same rule as above: never reassign an ID once written.

0BU. **[2026-09-06] PHASE 3, THE SLICE ON THE DELIVERABLE PATH - AND THE TEI
    EXPORT WAS CRASHING ON THE REAL CORPUS THE WHOLE TIME.**

    Item `0BR`'s Phase 3 guide said to do step 5 first: `export_corpus.py`
    hardcodes the book in the output that actually ships. Doing it turned up a
    live defect in the same file that nothing had ever run into.

    ### THE TEI EXPORT CRASHED. Every commit since the file was written.

    `python3 tools/export_corpus.py --format tei --output-dir X` dies with
    `AttributeError: 'NoneType' object has no attribute 'get'`. Verified against
    `137988f` in a clean worktree, so it is not from this week's work - it has
    never worked on the full corpus.

    Cause: `dec.get("candidate_snapshot", {})`. A dict default applies only when
    the key is ABSENT, and **2,678 of 3,504 ledger records carry the key with an
    explicit null** - 3 of them `disputed_choice`, which is the map this path
    reads, and one is enough.

    **Why nothing caught it** is the more useful half.
    `test_export_tei_generates_valid_tei_p5_xml` builds two synthetic klalim with
    no decisions at all, so the branch never executed; and nobody had run the
    export on the corpus. Lesson 1 exactly - a tool not run on what it applies to
    has verified nothing - against one of the three archival formats
    `START_HERE.md` names as the institutional-ingestion deliverable (success
    criterion 3). Swept the idiom: 9 sites across three files, all converted.

    **A second defect underneath it.** With no snapshot, `orig` fell back to `""`
    and TEI emitted `<orig></orig>` - an archival record ASSERTING that the
    reading before a pending correction was nothing. The decision is unapplied by
    construction on that path, so the word standing at the index IS the original.
    13 lines of the full export change: 12 empty originals filled in, and one
    `<choice>` collapsing to a plain `<w>` because the reviewer's pick matched
    the word already there, so there is no variant to show. Zero `<orig/>`
    remain.

    ### The identity extraction

    `book_identity()` gains the publication fields (`edition_label`, `publisher`,
    `scan_source`, `version_source`, `categories`), deliberately as SHORT
    composable strings rather than finished sentences - storing "Berlin 1851/2
    printing (Zittenfeld); scan via Google Books / NLI." whole would make a
    second book restate the sentence's grammar as well as its facts.
    `cio.scope_label()` derives "Part 1"/"complete"/"Parts 1-2" from the declared
    chunking, replacing a literal `Part 1` that the TEI title printed even under
    `--all-parts`, naming a 667-klal export after its first third.

    **The Yad Malachi export is byte-identical**: both Sefaria files match a
    pre-change export exactly, and the TEI differs only in the 13 lines above.
    **And the seam demonstrably works**: with a `book.json` naming a different
    book, the TEI title, the sourceDesc, the Sefaria index title, its categories,
    its node key, the versionTitle and the versionSource all follow. Both
    properties are pinned by tests; the byte-identity one asserts the composed
    strings so a later edit to `_WORK_DEFAULTS` cannot move the deliverable
    silently.

    The `SEFARIA_*` constants became plain accessor FUNCTIONS, not a module
    `__getattr__`: nothing outside the file reads them (checked), and a
    `__getattr__` hook is not consulted for a bare global lookup inside the
    module's own functions - the trap two `tools/` scripts fell into earlier the
    same day.

    ### A precedence bug I introduced, and the tests caught

    Sweeping `.get("candidate_snapshot", {})` -> `.get("candidate_snapshot") or
    {}` with a blind `str.replace` turned six CHAINED sites into
    `x.get("candidate_snapshot") or {}.get("original_word")`, which parses as
    `x.get(...) or ({}.get(...))` and returns **the whole snapshot dict instead
    of the field**. Five tests failed immediately - the manual-correction apply
    paths - and the fix is parentheses. Worth recording because the sweep was the
    right instinct and the mechanism was not: a chained expression is not a
    string, and a regex that knows about the chain (or an AST edit) is what that
    change needed.

    Gate 464 passed. plain/alto/page/tei/sefaria all export. No corpus text
    changed.

    ### Phase 3, still to do

    Steps 1-3 of `0BR`'s guide - extracting the ligature catalogue and the 24
    corrupt forms - are NOT done. Step 3's guard is the part not to skip: the
    invariant must keep its own literal and assert equality against
    `cio.defects()`, never read its expectation from the file it guards.

0BX. **[2026-09-06] ARCHITECTURAL SWEEP FOR THE FAILURE CLASSES THIS WEEK KEPT
    PRODUCING. Four classes checked clean, one real finding, two stranded
    features.**

    Asked to review the architecture for "similar missed functionality - edge
    cases", meaning the shapes just found: built-but-not-connected, connected-
    but-never-run, and keyed-on-the-wrong-thing. Everything below is measured.

    ### THE REAL FINDING: the ledger's current-state map is keyed on a SLOT, and
    the reindexer moves rulings between slots with no collision check

    `all_current()` keys on `(klal_id, word_index)` and takes the last row per
    key. `reindex_pending_decisions_after_shift()` appends a re-pointed copy at
    `wi + delta` **without checking whether that key is already occupied**, so a
    shift can move one ruling on top of another and the older one becomes
    invisible to every consumer of `all_current` - the applier, the dashboard's
    display maps, and the tri-state counts - with nothing recording that it was
    displaced.

    Measured on the live ledger: **94 `(klal, word_index)` keys carry rulings
    about MORE THAN ONE WORD, hiding 115 rulings.** The split is the part that
    matters, and it is better than the raw number suggests:

    | | |
    |---|---:|
    | applied - already in the corpus, harmless | 105 |
    | superseded - deliberately replaced | 2 |
    | **unapplied and not superseded - invisible** | **8** |

    **None of the 8 is a cleanly lost decision**, checked one by one: klal 2 w30
    is two exact duplicates of a ruling that WAS applied (`בססחים`->`בפסחים`);
    klal 35 w44 is the two span-wide deletions a later ruling explicitly retires
    by note, one of which carries `supersedes` and the other does not; klal 210
    w65/w66/w131 are reindexing collisions where a re-point moved a ruling onto a
    slot another already held. So nothing is currently lost - but the mechanism
    is silent, and the only reason it has not lost something is that the
    collisions happened to land on duplicates and retirements.

    The fix is small and belongs with the reindexer: refuse (or record) a
    re-point onto an occupied key, the same way `close_satisfied_rulings.py`
    refuses a position the ink does not corroborate. NOT DONE - flagged for a
    decision, because "refuse" and "record and move anyway" are different
    policies and the second needs somewhere to put the displaced ruling.

    ### Two features whose work is stranded, both deliberately

    **47 punctuation proposals have no way to be reviewed.**
    `punctuation_candidates_part1.json` holds 67 across 3 klalim, 20 carry a
    `punctuation_choice` decision, and the affordance that opens them was removed
    from the UI on 2026-08-11 - documented in `app.js` as "dormant, not dead,
    kept reversible". The server still computes and serves
    `punctuation_count` / `_decided_count` / `_open_count` on every klal row and
    the frontend references none of them. So the removal is intentional and the
    counts are consistent with it; what is worth knowing is the number sitting
    behind the dormant door.

    **`flag_note` is served and never rendered** (`review_server.py:1220`). It
    carries the reason a word was flagged. Currently null on every correction in
    the first 60 klalim, so nothing is being lost today - it is a latent Lesson 29
    rather than a live one, and it will start hiding information the first time a
    detector writes a note through that path.

    ### Four classes checked and CLEAN, which is most of the value here

    1. **The null-default class beyond `candidate_snapshot`.** The remaining
       `.get(key, {})` sites (`build_part1_freq`, `propose_abbreviation_
       expansions`) read dicts those files build themselves, where the key cannot
       be present-and-null. `chosen_text` is null 2,682 times in the ledger and
       reaches `export_corpus`'s TEI writer, but `ET` serializes `text=None` as
       an empty element rather than raising, and **0 unapplied rulings currently
       carry a null `chosen_text`**.
    2. **Empty `<reg/>` in the TEI export - 8 of them, and NOT a bug.** All eight
       come from rulings with `chosen_text: ""`, which is a real DELETION, and
       `<choice><orig>מקומו</orig><reg/></choice>` is a correct encoding of "this
       word is deleted". Investigated as a suspected sibling of the `<orig/>`
       defect fixed in `dcc7841` and it is not one.
    3. **Ungated writers of tracked, non-regenerated files: none left.** The
       sweep's two hits were false positives (both read `corrections_part1.json`
       through `repo_path`, neither writes it). `patch_witness_word_indices.py`
       was the one real member and is gated now.
    4. **API fields served but never rendered: 8 of 11 candidates are false
       positives.** `current_text_may_be_wrong`, `unverified_insertion` and
       `stale_candidate` are KEYS of `FLAG_LABELS`, which the frontend fetches
       wholesale into `FLAGS` and reads as `FLAGS[corr.flag]`;
       `applied_decision_id`, `candidate_snapshot` and `lexical_source` are
       ledger fields riding along in history rows, not display fields. The three
       genuine ones are `flag_note` and the punctuation counts, above.

    ### Method note

    The field sweep walked API responses collecting dict keys and hit a trap
    worth recording: several endpoints key their payloads BY WORD INDEX, so the
    walk collected 900+ numeric "field names" and buried the 11 real ones. A
    sweep over a structure that mixes data-keyed and schema-keyed dicts has to
    filter for identifier-shaped keys or it reports its own input back.

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

0N. **[2026-08-31] DICTA-AS-WITNESS DRY RUN — measured before building
    anything, and it moved the design. Also: `AbstractWitnessEngine` IS DEAD
    CODE, so the integration everyone has been naming is the wrong door.**

    **The wrong door, first.** `tools/second_witness_eval/README.md` names the
    next step as "wire Surya in as a permanent `AbstractWitnessEngine`
    implementation", and the 2026-08-31 Dicta report repeated that for Dicta.
    Checked: `pipeline/second_witness_eval/` is imported by exactly two things -
    `tests/test_witness_engine.py` (5 tests, outside the gate) and
    `tools/second_witness_eval/run_part1_vlm_second_witness.py` (a standalone
    one-off). **No stage of `rebuild_all.sh` touches it.** The live witness path
    is baseline `.txt` -> `synthesize_multi_witness.py` (stage 4a) ->
    `assemble_corrections_dataset.py` (stage 4) -> server -> `app.js`. And the
    ABC could not carry Dicta anyway: `transcribe_region(pdf_path, page_num,
    bbox)` is crop-based against `berlin_square_corrected.pdf`, while a
    Rashi-edition witness has a different PDF, different pagination and no
    shared bbox. START_HERE's TL;DR also calls `VlmWitnessEngine` the secondary
    witness engine; the VLM's real contribution is its baseline text file.

    **The dry run** (harness in the session scratchpad, wrote nothing): klalim
    13-22, the 10 the Rashi sample fully covers, 1,549 corpus words.

    | | |
    |---|---:|
    | positions where Dicta gets a vote (1:1 alignment) | 1,464 / 1,549 (94.5%) |
    | …agreeing with the corpus | 1,426 (**97.4%** of its votes) |
    | …differing | 38 (2.6%) |
    | existing consensus disputes in scope | 11 |
    | …Dicta **corroborates** | **8 (73%)** |
    | NEW disputes Dicta would create | **4** |

    **All 4 new disputes hand-checked - none is edition noise.** klal 13 w18
    `אכל`->`אבל` (the corpus reads "ate" where "but" belongs), klal 13 w231
    `זוהה`->`זה`, klal 17 w76 `בכוהרי"ק`->`במוהרי"ק`, klal 17 w242
    `רי"ז`->`ר"ז`. The first three are wrong by sense; the fourth needs the ink.

    **The safety result, and it is the reason to proceed.** 24 of Dicta's 38
    disagreements are SOLO (no other engine differs) and **not one became a
    dispute** - the standing two-distinct-engines rule held every one back. Hand
    reading all 24: ~12 are edition/orthographic variants (`סימן`->`סי'`,
    `בספר`->`בס'`, `התו'`->`התוס'`, `דרשה`->`דרשא`, `הר"ף`->`הרי"ף`), ~8 are
    Dicta's own misreads (`הוזכר`->`החכר`, `דרב`->`דקב`), ~4 want the ink
    (`א"ה`->`א"ח`, twice). **Cross-edition variance shows up as SOLO
    disagreement, which the existing rule already discards.** That is the whole
    safety argument, and it is measured, not assumed.

    **The ragged-alignment filter is what makes a cross-edition witness safe -
    validated by what it SUPPRESSES (Lesson 26).** 81 positions dropped in
    scope, read individually: corpus editorial marks the Rashi edition does not
    carry (`.` `:` `•` `[.]`), klal markers, page-margin garbage, and genuine
    abbreviation-style edition differences (`דבבא מציעא`->`דב"מ`, 2 words vs 1).
    Exactly the edition variance, and no letter-level error among them - with
    **one exception worth a reviewer**: klal 19 w54-56, corpus and Surya read
    `בסירא ששה`, the VLM reads `בספרא ששה`, Dicta reads `בסיפא`. A genuine
    three-way split the filter hides because the word counts differ.

    **Extrapolation, labelled as one:** 4 new disputes per 1,549 words scales to
    roughly **130 across Part 1's ~50,195 words**, and 73% corroboration would
    touch ~265 of the 364 existing consensus disputes. From 10 klalim - an
    order of magnitude, not a forecast (Lesson 27).

3. **The witness queue is still open**: 419 items across klal 30/75/88 (160 /
   119 / 140), of which 8 are decided and **411 remain** — the only real
   second opinion (DocAI vs. Tesseract) on those three page-crossing
   reconstructions, covering 2,673 DocAI words at 0.76–0.86 agreement. The
   machine vision pass is done; the human review-in-dashboard pass was
   explicitly deferred by the user as a future step (not forgotten, not a gate
   on anything else). **Tesseract provenance re-confirmed 2026-08-25 from the
   code (`verify_reconstruction_witness.py:79`, `tesseract -l heb`), with a
   recommended replacement measured the same day — see item 3a.**

**CORRECTED 2026-09-01 — the 419 is right about the FILE and wrong about the
   work.** `reconstruction_witness_queue.json` does still hold exactly 419 rows,
   160/119/140 across klalim 30/75/88, so that half of this item has not
   drifted. But the reviewer is never served 419: item 4's remedy was
   implemented, `WITNESS_QUEUE_FILTERED` is on with priority verdicts
   `("B","NEITHER")`, and the dashboard serves **44** — of which **24 are still
   open**. Decisions recorded: **20**, not the 8 this item claims.

   So "411 remain" overstates the outstanding work by roughly 17x, and it is the
   number a reader would most likely quote. The file count and the queue count
   are two different quantities and this item conflates them; item 4 changed
   what the second one means and nothing came back to update the first.

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

> **Item IDs are allocated per LANE, and are never reassigned once written.**
> Two concurrent sessions share this file, and a newest-first list with
> hand-picked single letters cannot survive that: both writers reach for "the
> next letter" and collide. It happened twice in one day — `0S/0T/0U`, then
> `0V/0W/0X` within hours — and renaming after the fact is not a fix, because
> item IDs are load-bearing: `apply_reviewer_decisions.py` and three test files
> cite them by name in comments (`item 0A`, `0B`, `0C`, `0F`, `0R`, `0U`, `0W`).
>
> - **`0A`–`0Z` — the review/corpus lane** (the main clone, which holds the
>   dashboard and the decision ledger).
> - **`1A`–`1Z` — the refactor lane** (the `-refactor` worktree).
> - A third lane takes `2A`–`2Z`. **Before writing an item, grep the file for
>   your next letter** — the cost of checking is one command; the cost of not
>   checking is an ambiguous cross-reference that a rename cannot safely undo.
>
> Resolved 2026-09-01 by moving the refactor lane's three colliding entries to
> `1G`/`1H`/`1I` — chosen over renaming the review lane's because those are the
> ones code references.

> **The review lane has run out of single letters — `0A`–`0Z` are all
> allocated.** Continuing as `0AA`, `0AB`, … in the same band rather than
> borrowing `2A`–`2Z`, which names a different lane and would misattribute the
> work. Same rule as above: never reassign an ID once written.

## Archived — full text in `PROJECT-STATUS-HISTORY.md`

_Every item ever written is listed here by id, so a reference from code or
from another entry still resolves. The BODY moved; nothing was deleted or
reworded. Split 2026-09-06 for the same reason as the 2026-08-12 one: this
file had reached 7,646 lines, past what a single read can load, which makes
"read PROJECT-STATUS.md first" impossible to honour literally._

| item | date | what it was |
|---|---|---|
| `0BY` | 2026-09-06 | [2026-09-06] THE ID API IS NARROWED TO ONE ACCESSOR, AND A RESTORED WORD NOW POINTS BACK AT THE ONE IT REPLACES. |
| `0BW` | 2026-09-06 | [2026-09-06] HISTORY IS KEPT - BUT `history_for` RETURNS A SLOT'S HISTORY, NOT A WORD'S. Now it says which. |
| `0BV` | 2026-09-06 | [2026-09-06] THE WORD ID NOW ACTUALLY RESOLVES SOMETHING, ALL THREE WRITERS KEEP IT IN STEP, AND A DELETED ID IS A TOMBSTONE RATHER THAN A SIL |
| `0BT` | 2026-09-06 | [2026-09-06] SELF-INFLICTED: `git checkout -- .` DESTROYED NINE FILES OF UNCOMMITTED WORK. FIVE WERE REBUILT FROM THE TRANSCRIPT, NOT FROM A BACKU |
| `0BS` | 2026-09-06 | [2026-09-06] A STABLE WORD ID, AND THE DISPUTE QUEUE ORDERED BY A CALIBRATED POSTERIOR. |
| `0BR` | 2026-09-06 | [2026-09-06] THE MANUAL WRITE PATH ALREADY RECORDS THE SCAN POSITION - WHAT WAS MISSING WAS THE GUARD. AND THE RESTART RULE NOW COVERS WHAT THE |
| `0BQ` | 2026-09-06 | [2026-09-06] ITEM 0BO's PLAN ITEMS 1 AND 3, DONE - AND THE ADDRESSING PROBLEM HAS A CHEAP SOLVENT THE BBOX WAS HIDING. |
| `0BP` | 2026-09-05 | [2026-09-05] CODE REVIEW OF THE WEEK'S CHANGES (`4ec7dc8`..`137988f`), AND A BLOCKING CORRECTION TO ITEM `0BO`'s PLAN ITEM 1. |
| `0BN` | 2026-09-04 | [2026-09-04] PHASE 2: THE BOOK'S SHAPE IS DECLARED, NOT HARDCODED. `book.json` now says how the corpus is chunked; 222/444/667 and the three-f |
| `0BM` | 2026-09-04 | [2026-09-04, reviewer-requested] EVERY DECISION NOW CARRIES A STRUCTURED ACTOR: who ruled, by stable internal id, and which tool recorded it. The |
| `0BK` | 2026-09-03 | [2026-09-03] RE-CONFIRMED DIRECTLY AGAINST THE INK: the closing page reads `סליקו כללי התיו וסליקו כללי הגמרא`, and the final klal is `תרסז` ( |
| `0BJ` | 2026-09-03 | [2026-09-03] ITEM 0AR IS DONE, in its own order: fixture generator → conftest.py → moved 4 pinned UI tests → split the invariants behind a `bo |
| `0BI` | 2026-09-03 | [2026-09-03] 51 SCRIPTS BYPASS THE CORPUS-ROOT SEAM ITEM `0AZ` BUILT — including one that ALREADY SILENTLY OVERWROTE LIVE, TRACKED DATA the first |
| `0BH` | 2026-09-03 | [2026-09-03] FOUR MORE HEADINGS APPLIED (91, 92, 94, 96) — and klal 92 demonstrated the drift check working exactly as `0BC` designed it, not a |
| `0BG` | 2026-09-03 | [2026-09-03, reviewer] THE HEADING PANEL READ ITS OWN STATE FROM A STALE CACHE — the reviewer corrected klal 96's heading, reopened the panel, and |
| `0BF` | 2026-09-03 | [2026-09-03] THE HEADINGS ARE APPLIED — klalim 89 and 90 now read `בעיא.` — and applying them exposed a coupling nobody had needed to think ab |
| `0BE` | 2026-09-03 | [2026-09-03, reviewer] THE HEADING CHIPS WERE BLACK ON BLACK, AND A SAVE THAT WORKED LOOKED LIKE A SAVE THAT DID NOTHING — the reviewer recorded k |
| `0BD` | 2026-09-03 | [2026-09-03, reviewer] I PUT THE HEADING PANEL'S CSS IN A FILE NOTHING LOADS — a file that did not exist until I created it. Fixed. And the answer |
| `0BC` | 2026-09-03 | [2026-09-03, reviewer] THE EXTENT CLASS IS THE BIG ONE, AND THE HEADING HAD NO WRITE PATH AT ALL. `✎ Heading` now rules on a title from the da |
| `0BB` | 2026-09-03 | [2026-09-03, reviewer proposal] CONTENT-ADDRESSING FOR DRIFT: yes, but the address must be `(klal, word, OCCURRENCE)` — the bare word names one |
| `0BA` | 2026-09-03 | [2026-09-03] THE DICTA CONSTRAINT IS AN ACQUISITION LIMIT, NOT A WIRING ONE — and item `0N` reads as though they were the same thing. Wiring the |
| `0AZ` | 2026-09-03 | [2026-09-03] ITEM 0AR IS STARTED: the corpus-root seam is in, and it resolves at CALL time. `--corpus DIR` and `$SEFER_CORPUS_ROOT` now point the |
| `0AY` | 2026-09-03 | [2026-09-03] ITEM 39's TITLE PASS IS BUILT — (i) the detectors read the field, (ii) a title ruling has an apply path, (iii) a gated invariant. Onl |
| `0AX` | 2026-09-03 | [2026-09-03] THE 58 ARE APPLIED — and the gate blocked them, correctly, because a corpus invariant still held the belief the reviewer had just |
| `0AW` | 2026-09-03 | [2026-09-03] WHY `הרל"ם → הרמב"ם` WAS PROPOSED: an abbreviation naming a DIFFERENT authority is indistinguishable, to every detector here, from a |
| `0AV` | 2026-09-03 | [2026-09-03] STATUS SWEEP: the suite is green at 459, `START_HERE.md`'s test counts were stale by five sessions, and 58 recorded rulings are sitti |
| `0AU` | 2026-09-03 | [2026-09-03] A GAP STOLE THE SCAN HIGHLIGHT FROM THE WORD SHARING ITS INDEX — 40 positions across 35 klalim. FIXED. And the legend's swatches now |
| `0AT` | 2026-09-02 | [2026-09-02] 131 CORRECTIONS ENTERED THE CORPUS THAT NO HUMAN EVER ADJUDICATED, and the dashboard has been drawing them GREEN as "Human-Decided" |
| `0AS` | 2026-09-02 | [2026-09-02] A WORD WITH NO OCR ALIGNMENT OPENED THE KLAL'S FIRST PAGE INSTEAD OF ITS OWN — 746 words across 55 multi-page klalim. FIXED, and the |
| `0AR` | 2026-09-02 | [2026-09-02] HOW TO MAKE THE TEST SUITE BOOK-INDEPENDENT — the measured plan. NOT STARTED. |
| `0AQ` | 2026-09-02 | [2026-09-02] THE 8 POSITIONS WHERE DICTA'S CONSENSUS CONTRADICTS A HUMAN RULING, itemised. TWO OF THEM LOOK LIKE THE CORPUS CARRYING AN EDITORIAL |
| `0AP` | 2026-09-02 | [2026-09-02] 40 STALE ADDRESSES RE-POINTED FROM THE INK; the ledger learned to say "superseded"; and yesterday's MAX_EXPLAINABLE_SHIFT was WRONG |
| `0AO` | 2026-09-02 | [2026-09-02, reviewer-requested] THE COUNT COLUMNS LINE UP, AND THE LEGEND EXPLAINS ITSELF. |
| `0AN` | 2026-09-02 | [2026-09-02] THE INDEX PENNANT AND THE TEXT PANE ANSWERED DIFFERENT QUESTIONS WITH THE SAME WORD — 15 of 222 klalim. FIXED, along with four re |
| `0AM` | 2026-09-02 | [2026-09-02, reviewer-requested] THE PANE HEADERS READ AS ONE CENTRED LINE OF PEERS — and the legend stopped letting the klal list show through it |
| `0AL` | 2026-09-02 | [2026-09-02] THE ZOOM LADDER COULD NOT REACH 100%, and a missing /api/corpus rendered as a blank space with nothing in the console. FIXED. |
| `0AK` | 2026-09-02 | [2026-09-02] THE SCAN PANE'S OVERLAY CONTROLS SCROLLED AWAY WITH THE PAGE — the zoom cluster since yesterday, the page arrows since they were |
| `0AJ` | 2026-09-02 | [2026-09-02] A NAV JUMP RE-ASSERTED THE LABEL BUT NOT THE GEOMETRY, so clicking a klal in the index could select the one above it. 5 of 222 klalim |
| `27` | 2026-09-01 | [CLOSED 2026-09-01 - all three repaired; see item 1A for the evidence and for the index-vs-ledger error this item's own follow-ups kept making.] |
| `1I` | 2026-09-01 | [2026-09-01] `pipeline/review_counts.py` EXTRACTED — S1's second half. `review_server.py` 1,981 → 1,585 today; `api_klalim` 249 → 168. |
| `1H` | 2026-09-01 | [2026-09-01] `lexicon_yad_malachi_only.json` WAS NON-REPRODUCIBLE — the report rewrote itself on every run with no data change behind it. |
| `1G` | 2026-09-01 | [2026-09-01] `pipeline/scan_alignment.py` EXTRACTED — C4 is closed for the rebuild chain, S1 is down 218 lines, and neither the pipeline's output |
| `1F` | 2026-09-01 | [2026-09-01] KLAL 209 APPLIED — three spurious words removed, and the sentence the 2026-08-14 spot-check called unparseable now parses. |
| `1E` | 2026-09-01 | [2026-09-01, reviewer-requested] SWEPT THE OPEN-ITEMS LIST ITSELF. Of eight checkable claims, three were stale, one was misleading, and one of my |
| `1D` | 2026-09-01 | [2026-09-01] TWO DECISIONS APPLIED — ONE REAL EDIT — AND IT CLOSES THE ONE POSITION ITEM 0Q SAID NEEDED A HUMAN FIRST. |
| `1A` | 2026-09-01 | [2026-09-01] ITEM 27 IS FULLY CLOSED — all three page-seam klalim are clean, and the "remaining" one was repaired on 2026-08-31. Reviewer-prompted |
| `0Z2` | 2026-09-01 | [2026-09-01] A crash in `compare_ocr_engines.py` on its DEFAULT path, introduced by yesterday's fix to the very blindness it was fixing. |
| `0Z` | 2026-09-01 | [2026-09-01] `tools/patch_witness_word_indices.py` HAS NO ARGUMENT PARSING AND WRITES ON ANY INVOCATION — I ran it with `--help` and it silent |
| `0Y2` | 2026-09-01 | [2026-09-01] A peer session's `/code-review high` on the docs commit — 11 findings, all fair, plus a real seam defect in code I wrote today. One |
| `0Y` | 2026-09-01 | [2026-09-01] C4 IS CLOSED. `pipeline/review_data.py` takes the last two stragglers, and NOTHING outside `tests/` imports `review_server` any more. |
| `0X` | 2026-09-01 | [2026-09-01] Outward-facing docs reviewed. One FACTUAL ERROR corrected, one legal separation that was missing, and four stale counts. |
| `0W` | 2026-09-01 | [2026-09-01] Dicta's OCR output is now the ONLY witness baseline not in version control, and it is the only one that cannot be regenerated on |
| `0V` | 2026-09-01 | [2026-09-01] DICTA IS DETERMINISTIC — same PDFs, second run, BIT-IDENTICAL output. It therefore needs no stability gate, and can never be its own |
| `0U` | 2026-09-01 | [2026-09-01] THE 75 AUDIT MISMATCHES ARE NOT LOST CORRECTIONS. 72 were index drift, 3 are benign, and ZERO corrections are missing from the co |
| `0T` | 2026-09-01 | [2026-09-01] The four new tools now have gated tests — and the two number-changing defects were both in logic no test could reach. |
| `0S` | 2026-09-01 | [2026-09-01] `/code-review high` on the session's four new tools — 10 findings, ALL TEN REAL, and two of them changed published numbers. |
| `0AI` | 2026-09-01 | [2026-09-01] COULD NOT REPRODUCE: "scan pane is oriented to the middle of the page" after dismissing a word. OPEN, needs one detail from the revie |
| `0AH` | 2026-09-01 | [2026-09-01] "SO GREEN WORDS ARE APPLIED BUT NOT REBUILT? WHY?" — THEY WERE NOT APPLIED. A status label I shipped this morning conflated a con |
| `0AG` | 2026-09-01 | [2026-09-01, reviewer-requested] THE INDEX ROW AND THE LEGEND, TIGHTENED — and a shared font token that named no Hebrew face. |
| `0AF` | 2026-09-01 | [2026-09-01, reviewer-requested] ONE HEADER BAR, THREE PANES, LIGHTENED — and the old one was overflowing invisibly on two of them. |
| `0AE` | 2026-09-01 | [2026-09-01] EVERY DEEP LINK TO A WORD ON A CONTINUATION PAGE LANDED ON THE WRONG PAGE WITH NO HIGHLIGHT — 18,044 words across 55 klalim. FIXED. |
| `0AD` | 2026-09-01 | [2026-09-01, reviewer-requested] DASHBOARD CHROME: one header bar shared by both panes, the copy-on-click switch behind a settings icon, the legen |
| `0AC` | 2026-09-01 | [2026-09-01, reviewer-requested] A SENIOR-REVIEW VIEW OF EVERY RULING, the book title on both panes, the scan arrows swapped — and two code-review |
| `0AB` | 2026-09-01 | [2026-09-01] 105 OF PART 1's 483 RECORDED RULINGS CARRY A STALE ADDRESS — but 79 of those were HONOURED anyway. The rulings actually unaccounted f |
| `0AA` | 2026-09-01 | [2026-09-01, reviewer-requested] THE LEGEND'S "HUMAN-DECIDED 51" WAS COUNTING THE SCREEN, NOT THE LEDGER — it now shows both. Plus: every legend |
| `57` | 2026-08-31 | [2026-08-31] `ע״ד` -> `ע"ד` applied; ONE U+05F4 gershayim left in Part 1. |
| `56` | 2026-08-31 | [FIXED 2026-08-31] Item 35's defect, one layer below where it was fixed: the ASSEMBLER re-served a word an applied decision had settled. |
| `55` | 2026-08-31 | [2026-08-31] Post-apply state, and two things the apply itself surfaced. |
| `54` | 2026-08-31 | [2026-08-31] 48 reviewer decisions applied — and I had to repair an index drift I caused myself first. The repair closed a real gap in the rei |
| `53` | 2026-08-31 | [2026-08-31, reviewer: klal 35 w30 "takes me to a completely wrong word"] THE FIX IS TO RETRACT THE CANDIDATE — the word is not missing, and the |
| `52` | 2026-08-31 | [2026-08-31, reviewer] The scan pane now scrolls to the klal it is showing, and a word click goes to that word's own page. |
| `51` | 2026-08-31 | [FIXED 2026-08-31] An orthographically impossible reading no longer reaches a reviewer. |
| `50` | 2026-08-31 | [2026-08-31, reviewer] Three nav badges, and editorial marks are addressable at last. Plus four findings from the same report, three of which |
| `49` | 2026-08-31 | [2026-08-31, reviewer: "klal 73 two disputes but the red flag shows only 1"] NOT A COUNTING BUG — but it exposes a field that is served per-klal a |
| `48` | 2026-08-31 | [2026-08-31, reviewer] Five more titles, and the editorial separator `[.]` inserted into 17 klalim — with the flag reindexing the insert made nece |
| `47` | 2026-08-31 | [2026-08-31, reviewer chose option (a)] The heading/text separator: almost nothing was normalisable, and the one case that was is a MISREAD, not a |
| `46` | 2026-08-31 | [FIXED 2026-08-31 — item 0E, reported by the reviewer as "clicking on 105 in the index moves the text pane but not the scan". |
| `45` | 2026-08-31 | [2026-08-31, reviewer] The index shows a title without its terminal period; the running text keeps it, because there it does a job. |
| `44` | 2026-08-31 | [2026-08-31] I OVER-CORRECTED SEVEN TITLES ON MY OWN INFERENCE AND REVERTED THEM. Recorded because the reasoning error is the useful part. |
| `43` | 2026-08-31 | [2026-08-31, reviewer] The two standalone corpus reports are now stage 5b of `rebuild_all.sh`, because they had silently aged out of agreement wit |
| `42` | 2026-08-31 | [2026-08-31, reviewer] Titles: two more extent fixes, and a punctuation rule now gated. Part 1's title field is, for the first time, internally |
| `41` | 2026-08-31 | [2026-08-31, reviewer] A TITLE-vs-TEXT COMPARISON NOW EXISTS FOR EVERY KLAL, and the heading is rendered where the book actually puts it — inside |
| `40` | 2026-08-31 | [2026-08-31, reviewer] The index pane now carries both scripts on every line, and a long title can no longer squeeze the badges off the row. |
| `39` | 2026-08-31 | [2026-08-31] THE `title` FIELD IS UNREVIEWED TERRITORY — it carries its own uncorrected OCR, and no detector in this repo has ever looked at it. |
| `38` | 2026-08-31 | [2026-08-31, four reviewer reports on the deep-link flow — all four reproduced, fixed and gated.] |
| `37` | 2026-08-31 | [SWEEP 2026-08-31] Every finding in every code- and data-review file re-verified against the live tree. Two new defects; item 9c was stale; the |
| `1C` | 2026-08-31 | [2026-08-31] S2 IS CLOSED — `corpus_io.words_of()` is now the one space-only split, and a test stops a new one being typed. |
| `1B` | 2026-08-31 | [2026-08-31] THE 2026-08-25/26/27 REVIEW BACKLOG IS CLOSED EXCEPT FOR THE THREE REFACTORS — nine findings fixed, seven new tests, and the multi-wo |
| `0R` | 2026-08-31 | [2026-08-31] Hebrew in generated Markdown needs EXPLICIT bidi isolation — the repo already knew this for HTML and the knowledge did not travel. |
| `0Q` | 2026-08-31 | [2026-08-31] THE 60 NEW DISPUTES ARE NOW A REVIEWABLE ARTIFACT — `DICTA-NEW-DISPUTES.md`, one dashboard link per position. Still a PREVIEW; no |
| `0P` | 2026-08-31 | [2026-08-31] DICTA RUN AGAINST THE JERUSALEM EDITION — 29 of 93 Part 1 pages done (klalim 1–63), 95.5% word accuracy, and the run was HALTED D |
| `0O` | 2026-08-31 | [2026-08-31] THE FULL RASHI EDITION IS IN THE REPO, AND IT IS JERUSALEM 1975/6 — NOT Przemysl, and NOT the scan the 94.8% was measured on. |
| `0M` | 2026-08-31 | [2026-08-31] A GERESH READ AS A YOD IN A NUMERAL SLOT — 3 in the corpus, all corroborated by two independent engines. DATA ISSUE, not fixed here. |
| `0L` | 2026-08-31 | [2026-08-31] `vlm_part1_full_baseline*.txt` blocks are PAGE-REGION text, not klal text, for 65 of 222 klalim — any character-level metric read off |
| `0K` | 2026-08-31 | [2026-08-31] THE THREE-PAGE SAMPLE PDF IS PAGES 19-21 / KLALIM 12-24, NOT 18-20 / KLALIM 8-22 — Lesson 30, and it invalidates the eval's stated |
| `0J` | 2026-08-31 | [2026-08-31] DICTA MEASURED, BOTH SCRIPTS — it is the WORST engine on square type and the FIRST engine ever to read this work's Rashi script. |
| `0G` | 2026-08-31 | [FIXED — verified 2026-09-01 from the collector, not the source: tests/test_review_server.py declares 44 and pytest collects 44.] |
| `0F` | 2026-08-31 | [2026-08-31] The UI test suite is bound to THIS corpus, in its current state of repair — the wrong shape for a general-purpose platform. |
| `0E` | 2026-08-31 | [FIXED 2026-08-31 — see item 46.] A nav jump's smooth scroll outlives the observer suppression, so a focus set during it is wiped. |
| `0D` | 2026-08-30 | [FIXED 2026-08-30, reviewer-reported] Correcting a word cost it its scan position, and applying a decision never closed the flag that raised it. |
| `0C` | 2026-08-30 | [FIXED 2026-08-30] Nothing reindexed the append-only ledger when a klal's word count changed — open flags silently walked off their word. |
| `0B` | 2026-08-30 | [2026-08-30] `insert`-opcode apply ignored `chosen_text` and deleted a word the reviewer never voted to delete — corpus damage, reverted. |
| `0A` | 2026-08-30 | [2026-08-30] A decided dispute could never be applied — 43 rulings stranded, now recovered. |
| `00` | 2026-08-30 | [CLOSED 2026-08-30 BY THE USER — "close 162/163 surya issue - wasting time". Stop raising it in session summaries; the standing reminder inside is |
| `8` | — | CLOSED 2026-08-25 — insert candidates DO have scan boxes, and the ones they had were wrong until today. |
| `7` | — | The public-domain citation tier is only partly itemized. |
| `6` | — | Przemyśl 1888's script is unverified, and HebrewBooks' fastocr is rejected. |
| `5` | — | RESOLVED 2026-08-31 — the Dicta Rashi OCR endpoint is <https://rashiocr.dicta.org.il/>. |
| `36` | — | THE 2026-08-27 AUDIT'S FOUR "CRITICAL DEFECTS" WERE VERIFIED AND ALL FOUR FIXED — three were LATENT, not live, and saying which is the point. |
| `35` | — | [AUDIT 2026-08-27] Heavy code review & Stage 5b / AI flag diagnostic audit. |
| `34` | — | REPORTS ARE NOW SHAREABLE, 2026-08-26 (reviewer: "the json is not a good way to share the urls - it is not clickable with markdown"). |
| `33` | — | GEMATRIA RULE CONFIRMED AND ENCODED 2026-08-26 (reviewer): a trailing ר in a klal marker is a misread ד - with exactly two exceptions, and this co |
| `32` | — | LIST PRODUCED 2026-08-26 (reviewer request): every word set with the alef-lamed ligature. |
| `31` | — | THE MERGED LEXICAL TIER HAS A PREFIX FALSE-POSITIVE CLASS, and no cheap filter separates it (reviewer, klal 179 w267). |
| `30` | — | FIXED 2026-08-26 (reviewer: "klal 179 word 267 - clicking does not highlight word in scan page") - a defect introduced by item 24's own merge, the |
| `29` | — | DEEP LINKS ADDED 2026-08-26 (reviewer request): a URL now addresses a klal, or a klal and a word. |
| `28` | — | MEASURED 2026-08-26 - the `ai-semantic-spotcheck-round4` flag pass (242 word-level flags, written 2026-08-18) has a real noise floor, found becaus |
| `26` | — | [FULLY CLOSED 2026-09-01 — 0 `&` remain corpus-wide, verified by content; item 37 had recorded one survivor at klal 77 w11.] |
| `25` | — | RETROSPECTIVE 2026-08-26 (user-requested): were today's fixes real, and were they repaired structurally or patched once? |
| `24` | — | REVIEWED 2026-08-26 (user-requested): the words that exist in Yad Malachi and in none of the 166 reference books. |
| `23` | — | CLOSED 2026-08-26 - every detector finding triaged against the independent witnesses; 15 real ones pushed, and the routing gap turned out to be fa |
| `22` | — | CONFIRMED 2026-08-26 — the detectors that WOULD catch these errors are not wired to anything, and `lexicon.txt` cannot fail a word it learned from |
| `21` | — | CODE REVIEW COMPLETED 2026-08-26 — three scoped passes, 26 findings triaged against the two parked reviews, 24 fixed, 2 refuted. |
| `2` | — | Parts 2–3 corrections are investigated but not applied — correctly, by design. |
| `19` | — | CLOSED 2026-08-26 — the review was finished in three scoped passes; see item 21 for what it found. |
| `12` | — | MEASURED 2026-08-23: P(consensus correct / 2 distinct engines agree) is ~26-41%, not the >99.9999% the plan claimed. |
| `10` | — | `MULTI-WITNESS-REPAIR-AND-SYNTHESIS-PLAN.md` review 2026-08-23 — the architecture is sound, four things in it are not. |
| `1` | — | The 312 fabricated "VLM Verified" Parts 2-3 candidates were pulled from the dashboard 2026-08-20 |
| `0` | — | STANDING RULE, added 2026-08-24 (user directive): never fix one instance — sweep the corpus for the class. |
