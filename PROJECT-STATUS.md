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
> 4. `0CA` — **a word click's page navigation is undone ~50% of the time.** Not a
>    flaky test, a flaky FEATURE: a reviewer clicking a word on a continuation
>    page is shown the wrong page. Two fixes were tried and reverted; the entry
>    carries the reproduction, what is ruled out and by what measurement, and the
>    live hypothesis (an ordering race between two `showPage()` calls, not a
>    timing window). Start there, not from scratch.
> 5. `16`, `20`, `0N`, `3`, `4` — the standing corpus and witness-queue items.
>
> **Added 2026-09-08 by a code review:** `0DE` (the word-id skip in the FLAG
> reindexer was live and stranding flags — 17 open flags carry an id and nothing
> resolves a flag's position by one; **findings 1-5 fixed**, 6-8 open (LOW, latent),
> and klal 198's two already-diverged flags need a ruling against the ink), `0DD`
> (two ledger tools resolve a bbox to a word with two different distance
> metrics and disagree on 20 of 663 positions), `0DC` (item `0BI`'s
> corpus-root fix was applied to two modules and never swept — 26 more
> freeze their paths at import, four of them `rebuild_all.sh` stages).
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

**THE DELIVERABLE IS PART 1, AND ONLY PART 1.** Reviewer directive 2026-09-07:
*"parts 2 and 3 do not exist, any previous work on those will be discarded and we
will start fresh - the tool has changed dozens of times since then, and I don't
trust any work performed with early iterations. I'm only vouching for part 1 -
and even that is subject to hiring someone to close all disputes."* So the
placeholder counts, the reconstructed klalim and every Parts 2-3 figure in this
file describe work that is to be REDONE, not work in progress. Do not cite them
as corpus state and do not repair them; they are superseded by construction.

**AND PART 1 IS NOT SIGNED OFF EITHER.** It is vouched for only as far as the
open disputes, which need a qualified reviewer to close. Two things must be true
before that person can start, and both are engineering work: **every open dispute
has to be reachable in the dashboard and nowhere else** (item `0CO` - the ranked
queue currently orders 389 of 535, and `0CV` found 136 detector positions
reachable by no route at all), and **every correction already made has to be easy
for them to review and approve** (item `0DA` gives them
`INTERVENTIONS.json` - every change with its as-printed reading, its source and
its evidence).

**The binding constraints.** The Parts 2-3 gate (`START_HERE.md`) still holds:
no `part2.json`/`part3.json` correction may be applied. Recording a decision and
applying it to the corpus remain two separate, deliberate steps.


## Open items

0DF. **[2026-09-08] RE-MEASURED: WHAT IS A DATA ISSUE THE DASHBOARD CANNOT SHOW.
    125 POSITIONS ARE GENUINELY UNSEEN, NOT 580 - AND THE STRUCTURAL REPORT IS
    ALREADY FULLY TRIAGED.**

    Reviewer asked the same question `0CV` asked. Re-measured rather than quoted,
    per this file's own rule, and the answer has moved in both directions.

    ### Method, and the two errors caught inside it

    Every derived report's `(klal_id, word_index)` positions diffed against what
    the dashboard ACTUALLY renders - `GET /api/klal/N` for all 222 klalim, the
    `queue` array, which is api_klal()'s merged view of machine candidates,
    manual rulings, word-level flags and witness rows after claim_word_index().
    866 positions across 160 klalim; `open_count` sums to 684.

    **First cut said 0 rendered and therefore 100% invisible.** It read a
    `corrections` key that does not exist; the array is `queue`. A measurement
    that reports every input as defective is reporting on itself (Lesson 33).
    **Second cut called the witness queue and the title rows invisible** - wrong
    both times: witness rows DO come through `queue` (klal 30/75/88 carry
    witness_count 23/11/10, exactly the 44 counted visible), and title positions
    are indices into the TITLE, a different address space from body word
    indices, so diffing them against body indices compares nothing.

    ### The answer, by population

    | source | positions | not in the dashboard | what that is |
    |---|---:|---:|---|
    | `collation_report.json` | 75 | 74 | **correct by design** - Lesson 38, a cross-edition collation is never a correction queue |
    | `reconstruction_witness_queue.json` | 410 | 366 | **a FILTER**, items 3/4 - Lesson 26 territory |
    | `lexical_defect_report.json` | 213 | 118 | **a deliberate tier decision** (`merge_lexical_defects` takes the sharpest tier only) |
    | `structural_defect_report.json` | 22 | 17 | report-only by design (`0CW`) - **but 15 of the 17 are already `acknowledged`** |
    | `ligature_words.json` | 7 | 3 | unrouted |
    | `title_defect_report.json` | 4 | 4 | different address space; reachable via the Heading panel, but nothing points at them |

    **So the genuinely unseen-and-unreviewed set is 125 positions**: 118 lexical
    + 3 ligature + 4 title. Not 580, and not `0CV`'s 136.

    ### THE STRUCTURAL REPORT IS DONE, which `0CV` could not have known

    15 of its 17 invisible rows carry `acknowledged: true` - the reviewer checked
    them in `0CX`. The 2 that do not are klal 144 w837 (`ה` -> `ח`) and w839
    (`ו` -> `י`), both `enumeration_break`, and both are **exactly the false
    positive `0DE` finding 6 predicts**: the detector assumes any run of >=4
    single letters is an א-ב-ג enumeration STARTING at א, so a run continuing
    from earlier reads as a break. Nothing to review; something to fix.

    ### The 118 lexical are the real population, and they are not weak

    85 `insertion_deletion` + 33 `substitution`; 98 of 118 unambiguous; 101 carry
    a proposal attested >=100x in the independent reference corpus and 21 of
    those >=1,000x. The top of the list, all invisible today:

        http://127.0.0.1:8420/klal/92/word/346    'דהלא'  -> 'דלא'   (12,899x)
        http://127.0.0.1:8420/klal/24/word/166    'ואידן' -> 'ואין'  (12,846x)
        http://127.0.0.1:8420/klal/24/word/230    'ואידן' -> 'ואין'  (12,846x)
        http://127.0.0.1:8420/klal/176/word/555   'ואיין' -> 'ואין'  (12,846x)
        http://127.0.0.1:8420/klal/177/word/550   'מתניי' -> 'מתני'  (5,096x)
        http://127.0.0.1:8420/klal/2/word/188     'בשרש'  -> 'בשר'   (3,530x)
        http://127.0.0.1:8420/klal/11/word/81     'בשרש'  -> 'בשר'   (3,530x)
        http://127.0.0.1:8420/klal/31/word/64     'השיתא' -> 'השתא'  (1,946x)
        http://127.0.0.1:8420/klal/37/word/272    'השיתא' -> 'השתא'  (1,946x)
        http://127.0.0.1:8420/klal/169/word/529   'ואוף'  -> 'ואף'   (1,891x)

    The 3 ligature and 4 title positions, in full:

        http://127.0.0.1:8420/klal/7/word/677     'ויגל' -> 'ויגאל'
        http://127.0.0.1:8420/klal/30/word/1521   'תשל'  -> 'תשאל'
        http://127.0.0.1:8420/klal/150/word/443   'אוף'  -> 'אלוף'
        http://127.0.0.1:8420/klal/9    title w0   (prefix divergence)
        http://127.0.0.1:8420/klal/144  title w4   (detector candidate)
        http://127.0.0.1:8420/klal/186  title w2   (prefix divergence)
        http://127.0.0.1:8420/klal/212  title w0   (detector candidate)

    ### NOT ACTED ON, and the reason is the reason the tier exists

    Widening `merge_lexical_defects()` is a one-line scope change on a DERIVED
    source with no ledger residue, fully reversible. It is not done here because
    the argument against it is measured and still stands: these detectors carry
    real false positives (149 of 262 contradicted by independent witnesses), and
    563 permanent flags on unread material is how the 1,496-flag queue happened.
    **The decision is the reviewer's**, and it is now costed: +118 positions on
    top of 684 open, of which ~101 carry a strongly-attested proposal.

    ### `0CO` re-measured

    `dispute_queue_ranked.json` holds **399 rows against 684 open positions** -
    58%. `0CO` recorded 389 of 535 and the TL;DR 389 of 535; both are stale. The
    item's question is unchanged: widen the ranker to every open position, or
    rename the file and state the remainder in it.

0DE. **[2026-09-08, code review] REVIEW OF `f2daf3b` (`pipeline/`, +559/-30). THE
    ID-SKIP IN BOTH REINDEXERS IS LIVE AND ITS "INERT TODAY" COMMENT IS STALE:
    17 OPEN WORD-LEVEL FLAGS NOW CARRY AN ID AND NO FLAG CONSUMER RESOLVES BY
    ONE.**

    Eight findings. The three marked VERIFIED below were re-checked here against
    the code and the live ledger, not taken from the review's write-up
    (Lesson 19); the rest are reported as found and are NOT independently
    confirmed.

    ### 1. HIGH - `apply_reviewer_decisions.py:334`, the flag reindexer's id skip. VERIFIED. **FIXED 2026-09-08**

    `if rd.word_id_of(rec, backfilled): continue` skips moving any flag that
    names its word by id, on the premise that an id-addressed flag needs no
    reindex. **No flag consumer resolves by id.**
    `review_server._word_level_ai_flags()` builds `by_word[r.get("word_index")]`
    (`review_server.py:308`) and highlights on that raw index;
    `review_counts.flag_still_open` takes `word_index` and is index-keyed
    throughout. Only `resolved_position()` and the senior-review decisions panel
    (`review_server.py:939`) id-resolve, and neither touches flags.

    **The comment says "INERT TODAY - 0 of 1,367 word-level flags carry an id".
    Re-measured 2026-09-08: 1,424 word-level `klal_flag` rows, 17 carry an id,
    and all 17 are OPEN** - klal 54 (w415, 787, 877, 907), klal 167 (w422, 459,
    644, 664, 738, 812, 827, 990, 1037, 1092, 1234), klal 198 (w894, 969).
    Counted through `apply_reviewer_decisions.open_word_flags()` itself, so this
    is the same set the skip will see.

    It compounds: line 370 stamps a `word_id` on every flag the reindexer DOES
    move, so a flag's first reindex is its last. The next word-count change in
    that klal leaves it highlighting the wrong word with nothing left to move
    it - the klal 66 `ע"ס` -> `שהניח` defect this function exists to prevent.

    ### 2. MEDIUM - `apply_reviewer_decisions.py:270`, the same skip on decisions

    Justified by "resolved_position() asks the sidecar first", which is true of
    the applier and the senior-review panel and not of the main text pane:
    `rd.all_current_live("candidate_choice")` is keyed `(klal_id, word_index)`
    and consumed index-wise by `review_counts.merge_decision` and
    `word_states`. `review_queue_part1.json` is rebuilt against fresh indices,
    so an id-carrying pending ruling that was not reindexed stops matching its
    candidate entry: the ruling disappears from the word it was made on and can
    colour a different word decided. Per the comment's own measurement, 9 of 24
    pending rulings. NOT independently verified here.

    ### 3. MEDIUM - `review_counts.py:173`, the one cache with no invalidation. VERIFIED

    `@functools.lru_cache(maxsize=4)` on `_backfilled(path)` is keyed on `path`
    alone and lives for the process. `rd._read_all` is keyed on
    `(st_mtime_ns, st_size)` precisely to honour "a decision recorded in one tab
    is visible to the next request". `review_server` calls `flag_still_open`
    with `path=None` (`review_server.py:446`), so a `word_id_backfill` appended
    while the server is up - `tools/backfill_word_ids.py` in another terminal,
    an apply run - is invisible until restart, and flags stay wrongly open or
    wrongly closed until then.

    Its docstring argues this is fine because the server re-execs under the
    restart rule. **The restart rule covers CODE, not the ledger** - and the
    ledger is the DATA the "reads its source files fresh off disk every request"
    contract is about. This is Lesson 39 (a value cached at load time behind a
    live view) in the counts layer. `(path, mtime_ns, size)` keeps the measured
    win without the staleness. It is also a cross-test hazard: the new test has
    to call `rcount._backfilled.cache_clear()` by hand
    (`tests/test_pipeline_logic.py:6098`), and every test that redirects
    `rd.DECISIONS_PATH` and calls `flag_still_open` without an explicit `path`
    shares the `None` key with every earlier test.

    ### 4. MEDIUM - `apply_reviewer_decisions.py:370`, an ordering the code does not enforce

    The id stamp is correct only under the order the comment names (corpus
    written -> `follow_corpus()` reconciles the sidecar -> this runs).
    `follow_corpus` at `:1123` is wrapped in a bare `except Exception` that
    prints a WARNING and continues, skips klalim not already in the sidecar, and
    returns `reconcile()` `ValueError`s in `problems` that are only printed. In
    all three cases the sidecar is still pre-shift, `id_at(new_wi)` returns the
    id of the word that USED to sit there, and the moved flag is stamped with a
    wrong id - permanently, because finding 1's skip then excludes it from every
    future reindex. Gate the stamp on `touched` / no problem for this klal.
    NOT independently verified here.

    ### 5. MEDIUM - `corpus_io.py:675`, a documented fail-fast lost in a move. VERIFIED. **FIXED 2026-09-08**

    `from bidi.algorithm import get_display` is function-local inside
    `to_visual()`. `tools/preview_dicta_disputes.py:59` still carries the same
    import at module scope with the comment saying why: "burying it inside
    write_md() meant a fresh clone ran the whole corpus-wide alignment and only
    then died with ModuleNotFoundError, having written nothing." The rationale
    did not come along in the 2026-09-07 move. The three generators newly routed
    through `cio.render_hebrew` all default to `--hebrew visual` and call it
    after all the work; `list_drifted_rulings.py:292` calls it INSIDE
    `open(args.out, "w")`, so without python-bidi the existing report is
    truncated to zero bytes and then the run dies. Restore the module-scope
    import.

    ### 6-8. LOW - `build_structural_defect_report.py`, all latent today

    - `:138` `ideal = ALEPH_BET[:len(seq)]` caps at 22 but `ideal[j]` indexes
      `range(len(seq))` - a run of 23+ consecutive single-letter tokens raises
      `IndexError` and aborts stage 4e of `rebuild_all.sh`. The same block also
      assumes any run of >=4 single-letter tokens is an א-ב-ג enumeration
      STARTING at א, so an enumeration continuing from an earlier klal
      (`ד ה ו ז`) reads as four breaks with confident proposals. One qualifying
      run in the corpus today (klal 144 w830, length 10) - but this runs on every
      rebuild against text that changes.
    - `:76` `_key` is `klal_id|detector|stored` with `word_index` deliberately
      excluded for drift-immunity, which also makes it non-unique within a klal:
      two same-detector findings with the same stored text collapse, so
      acknowledging the first silently suppresses the second, unreviewed. 22
      rows / 22 distinct keys today. Needs a stable non-index discriminator.
    - `:156` `cio.load_klal_words(part_path)` is called a second time to build
      `own` when line 92 already holds the identical map. Reuse `klal_words`.

    ### Checked and clean

    Detector tuple arities match their unpacking; `_raised_at`'s `supersedes`
    walk is bounded, cycle-guarded and correctly gated on `klal_flag` (the other
    `supersedes` writers never write that type); `_record_unverified_shifts`'
    row shape matches `main`'s unpacking and only runs off the non-dry-run path;
    the four dead-code removals (`flagged_klalim`, `repair_stream`,
    `get_ligatures`, `POST /api/decisions/candidate`) have no remaining callers
    in `pipeline/`, `tools/`, `tests/`, `rebuild_all.sh` or `review_frontend/`.
    `word_id_of` truthiness vs `is not None` differs between the two reindexers
    and `flag_answered_by_a_later_decision`, but word ids are per-klal and
    1-based, so id 0 cannot occur - latent only.

    ### FIXED 2026-09-08, at the reviewer's instruction: findings 1 and 5

    **Finding 1.** The skip is removed from `reindex_flags_after_shift()` and
    NOT from the decision reindexer beside it - the asymmetry is the fix, and it
    is written into the code as a comment saying what would have to become true
    for the skip to come back (a flag consumer that resolves a POSITION by id).
    The id stamp on a moved flag stays, redescribed as provenance rather than as
    an address: it is what makes a future divergence visible.

    Precision the first write-up of this item got slightly wrong, corrected here
    rather than left standing: **one flag reader does consult the id** -
    `review_counts.flag_answered_by_a_later_decision()` at `:136` matches flag id
    to ruling id, deliberately after the index test. That answers WHETHER a flag
    is answered, never WHERE it sits. The positional path
    (`review_server._word_level_ai_flags()`, the nav/count sets,
    `flag_still_open()`) is index-only, which is what makes the skip wrong.

    `tests/test_pipeline_logic.py::test_an_open_flag_addressed_by_a_stable_id_is_
    not_reindexed` **asserted the defect** and is inverted, renamed
    `..._carrying_a_stable_id_is_STILL_reindexed`. Mutation-checked both ways
    (Lesson 42): re-adding the skip fails it, removing the skip passes it, so the
    test is not blind. Its sibling on the ruling side is untouched and still
    asserts the skip, which is what keeps the pair meaningful (Lesson 25). Suite
    green at 513.

    **NOT repaired, and deliberately: klal 198's two already-diverged flags**
    (w894 carrying id 893, w969 carrying id 968). The fix stops new ones; which
    address is right for these two is a call against the ink, not a guess a
    script should make. They are the only two of the 17 in that state - the other
    15 have index and id naming the same word.

    **Finding 5.** `corpus_io` now resolves python-bidi at import and captures
    the failure instead of raising it, and `check_hebrew_mode(mode)` raises early
    with an actionable message; all three generators call it straight after
    `parse_args()`, and `list_drifted_rulings.py` renders BEFORE it opens its
    output file.

    **Not the bare module-scope import the review recommended, and the reason
    is a measurement:** 87 modules import `corpus_io` and 6 ever render Hebrew,
    so a plain top-level `from bidi.algorithm import get_display` converts a
    missing optional package into a total pipeline outage - every validator,
    detector and the review server - in order to fail fast for six callers. The
    guarded form gives the same fail-fast to those six and leaves the other 81
    working.

    Verified by simulating a machine without python-bidi (import hook): the
    corpus still loads (222 klalim), `--hebrew logical` still works, `--hebrew
    visual` exits immediately with the install instruction, and **an existing
    worklist survives at full size instead of being truncated to 0 bytes** - the
    old shape, reproduced standalone, leaves 0.

    ### The two klal 198 flags, resolved 2026-09-08 - and the causal chain

    Reported above as "needs a call against the ink". The ledger answered it
    instead, and the answer is that the reviewer had already ruled:

    1. **2026-09-07 18:05:38** - `שתישההולאחם` at w570 replaced with
       `שתי הלחם משמע`. One word became three: **+2**.
    2. **18:29:53** - applied. `reindex_flags_after_shift()` worked CORRECTLY,
       moving the flag on `זלזה` w892 -> w894 and the flag on `שכתכתי`
       w967 -> w969, and (new that day) stamping word ids 893 and 968 on the two
       rows it wrote.
    3. **18:45:10** - a `manual_correction` at w573 with `chosen_text=""`, i.e.
       a deletion, applied 18:47:49: **-1**. `זלזה` moved to w893 and `שכתכתי`
       to w968.
    4. **The reindexer did not move the flags this time**, because step 2 had
       just given them ids and the skip passed over them. Flags at 894/969,
       words at 893/968.
    5. **2026-09-08 07:36/07:38** - the reviewer ruled at 893/968, the correct
       current positions.

    **The id stamp cut both ways, which is the useful part of this case.** It is
    what made the skip fire in step 4 (the defect), and it is what let
    `flag_answered_by_a_later_decision()` match ruling to flag across the
    one-word gap in step 5 (the feature): both `still_open=False` before anything
    was touched today, so neither had ever been counted as outstanding. One field,
    opposite consequences, because one path treats the id as an ADDRESS and the
    other only as an IDENTITY.

    **The rulings were recorded and never applied.** Checked before acting: the
    corpus still held `זלזה` and `שכתכתי`, `applied=False` on both. Clearing the
    flags at that point would have removed the last marker on two words that were
    still wrong. Applied instead, this run, with the reviewer's go-ahead - 6
    decisions, 0 insert/delete, so no index moved:

        klal 144 w821  'בכתיכת'  -> 'בכתיבת'
        klal 144 w873  'מהלוקת'  -> 'מחלוקת'
        klal 144 w907  'בישרץ'   -> 'בישראל'
        klal 198 w893  'זלזה'    -> 'ולזה'
        klal 198 w968  'שכתכתי'  -> 'שכתבתי'

    Verified word-by-word against a before/after copy of `part1.json`, not
    against the script's own report (Lesson 19); both klalim unchanged in length
    (1292 and 1095). `./rebuild_all.sh` clean, exit 0, 513 tests.

    **Then the two flag rows were cleared**, superseding the originals with the
    chain above in the note. THE APPLY PATH COULD NOT DO THIS ITSELF and that is
    worth recording: it closes a flag at the applied decision's EXACT index, and
    these sat one to the right, so the same index-vs-id gap that stranded them
    also hid them from the closer. Corpus-wide, open flags carrying a word id go
    17 -> 15; the remaining 15 (klal 54 x4, klal 167 x11) all have index and id
    naming the same word, so none is in this state.

    ### FIXED 2026-09-08, second pass: findings 2, 3 and 4

    All three mutation-checked (Lesson 42): the fix reverted, the test observed
    to fail, the fix restored. Gated suite 513 -> 515.

    **Finding 2 - the decision reindexer's id skip, REMOVED, and by the narrow
    route.** The review's remedy was to teach the queue side to id-resolve. That
    is a change to what the reviewer sees across four endpoints; keeping the
    recorded index correct costs one superseding row per shift and touches no
    rendering, so that is what was done. Both reindexers now maintain the index
    and treat the id as provenance plus the applier's fallback - which is the
    same conclusion finding 1 reached, applied consistently instead of split.

    **Measured before fixing, and it is LATENT: 39 pending rulings, 4 carry an
    id, 0 of the 4 resolve to a different index than the one recorded.** Nothing
    is wrong on screen today. Recorded that way rather than as a live defect.

    The retirement refusal the old skip also carried survives structurally: the
    span check refuses to move a ruling whose word is gone
    (`new_words[new_wi:...] != span`), reporting it as unverified. And Lesson 46
    is satisfied by the line above the removed skip - an applied ruling is
    skipped before the move, so no superseding copy is written over one.

    `test_a_pending_decision_addressed_by_a_stable_id_is_not_reindexed` asserted
    the skip and is inverted, renamed `..._carrying_a_stable_id_is_STILL_
    reindexed`.

    **Finding 3 - `_backfilled()` re-keyed on (mtime_ns, size).** Was
    `lru_cache(maxsize=4)` on `path` alone; the server calls it with `path=None`,
    so one entry served the process. Now the same shape as
    `rd._read_all`/`widentity.load`/`sa.load_regions`, one stat() per call.

    **THE MUTATION DID NOT FAIL, AND THAT WAS THE REAL FINDING.** Restoring the
    lru_cache left the suite green. The test that used to call
    `rcount._backfilled.cache_clear()` by hand never exercised the staleness
    either - its first call answers through the INDEX branch of
    `flag_answered_by_a_later_decision()` and returns before reaching
    `_backfilled()`, so the cache was cold on the second call. So the code was
    right and untested, and the hand-written `cache_clear()` was the only thing
    that looked like coverage. `test_the_backfill_table_re_reads_when_the_ledger_
    grows` now asserts the property directly - read, append an annotation, read
    again - and fails under the mutation. The `cache_clear()` line is deleted,
    and its absence is a second assertion.

    **Finding 4 - the id stamp is gated on `sidecar_in_step`.** A reconciled
    sidecar has exactly one id per word in the klal just written; an
    unreconciled one still holds the pre-shift count and differs by `delta`, so
    length is the whole test. Checked directly rather than plumbed through
    `follow_corpus()`, which returns a COUNT and is called by three corpus
    writers. Out of step: the flag is still MOVED (a stale sidecar is no reason
    to strand it) but carries NO id, and a WARNING names the klal. A missing id
    is recoverable; a wrong one is indistinguishable from a right one forever
    after, and it is what `flag_answered_by_a_later_decision()` matches on.

    Two existing tests stubbed `widentity.load` as `{"stub": True}` - a sidecar
    claiming to exist while carrying no ids, which no real run produces and which
    the new check correctly rejects. Both now stub the real shape.
    `test_a_reindexed_flag_gets_no_id_when_the_sidecar_is_out_of_step` is its
    twin, identical but for a pre-shift id count.

    Findings 6-8 (`build_structural_defect_report.py`, all LOW and latent) are
    NOT fixed and remain as written above.

0DD. **[2026-09-08, code review] TWO LEDGER TOOLS RESOLVE "WHICH WORD IS AT THIS
    BBOX" WITH TWO DIFFERENT METRICS, AND DISAGREE ON 20 OF 663 POSITIONS. One
    of them says in its own docstring that it holds the other's bar.**

    `tools/repoint_stale_decisions.py:76 bbox_signal()` and
    `tools/close_satisfied_rulings.py:69 _bbox_index()` have byte-identical
    bodies - same `word_bboxes_resolved` call, same page filter, same
    `min(here, key=lambda kv: _distance(bbox, kv[1]))`. Their `_distance` is
    not the same function:

    | file | line | metric |
    |---|---|---|
    | `repoint_stale_decisions.py` | 60-67 | Euclidean distance between box **centres** (`_centre` collapses each box to a point) |
    | `close_satisfied_rulings.py` | 63-66 | **L1 over all four corners** (`|x1-x1| + |y1-y1| + |x2-x2| + |y2-y2|`) |

    So the two tools answer the same question - which corpus word a ruling's
    recorded scan position names NOW - and can name different words.

    ### Measured, on the live ledger

    663 rulings (`disputed_choice`, `candidate_choice`, `manual_correction`,
    `witness_choice`) carry a `candidate_snapshot` bbox that resolves against
    `klal_page_regions.json`. **The two metrics pick a different word index on
    20 of them, 3.0%.** Three fall in the tier where the bbox is the SOLE
    deciding signal for `close_satisfied_rulings.py` - its tier-3 REPEATED
    branch, the one that writes an `apply_event`:

        id 4c1f9e85cf6a  klal 8   w1    chosen איידי  (7x)  centre->w29   L1->w0
        id 9ea37a28c374  klal 69  w339  chosen אלהים  (6x)  centre->w321  L1->w339
        id ade4c2678ea6  klal 69  w338  chosen אלהים  (6x)  centre->w321  L1->w339

    klal 69 / `אלהים` is the same klal and the same word Lesson 34 records as
    having been silently deleted once by a mis-scoped mutator. This is a
    position with a history.

    ### NEITHER METRIC IS DEMONSTRABLY THE RIGHT ONE - do not "fix" this by
    ### picking the one that looks better

    Scored against each ruling's own recorded `word_index` (a proxy, and one
    that drifts - it is not ground truth), they are within noise of each other
    over all 663:

    | | centre-Euclidean | corner-L1 |
    |---|---:|---:|
    | lands exactly on the recorded index | 494 (74.5%) | 497 (75.0%) |
    | within 1 word | 564 (85.1%) | 575 (86.7%) |
    | mean `|resolved - recorded|` | 10.6 | 10.4 |

    L1 is better on every line and by almost nothing. **The finding is the
    divergence, not a winner.** Deciding which metric is correct needs the ink
    (render the crop, read which word the box actually covers) on a sample of
    the 20 - Lesson 9's two-signal bar - not a rerun of this table.

    ### Why this is a bug and not a style note

    `close_satisfied_rulings.py`'s module docstring says its tier-3 bar is
    "the ink agreeing with the letters, which is the standing two-signal bar
    (Lesson 9) and **the same one `repoint_stale_decisions.py` holds itself
    to**". It is not the same one. A prose claim about a sibling's behaviour is
    exactly what Lesson 42 says not to ship unmeasured, and this is the pair
    Lesson 46 already caught diverging on a guard - the second divergence in
    the same two files.

    **The remedy is a shared primitive, not a matched pair.** Both files already
    `import scan_alignment as sa` and the function is entirely about scan
    geometry; one `sa.word_index_at_bbox(...)` deletes both copies and makes the
    metric a single decision with one place to record why. Same rule as
    `union_bbox` (finding H3) and `PLACEHOLDER_RE`.

    NOT FIXED. Needs the ink-check above first, because consolidating on the
    wrong metric silently moves 20 rulings.

0DC. **[2026-09-08, code review] THE `0BI` CORPUS-ROOT FIX WAS APPLIED TO TWO
    MODULES AND NEVER SWEPT. 26 MORE FREEZE THEIR PATHS AT IMPORT, 62 CONSTANTS
    IN ALL - INCLUDING FOUR OF THE FIVE `rebuild_all.sh` STAGES AND THE REVIEW
    SERVER.**

    `test_the_corpus_root_seam_reaches_the_scripts_that_write_corpus_data`
    (`tests/test_pipeline_logic.py:7194`) is the right test and its docstring
    states the defect exactly: `$SEFER_CORPUS_ROOT` working is not the same as
    the seam working, because the environment is read before the module loads,
    and a module that copies `cio.PART1_PATH` into a module-level constant
    freezes it where `cio.set_corpus_root()` - what `--corpus` calls, and what a
    second book goes through - can no longer move it. **It checks two modules,
    named as literals: `apply_punctuation_decisions` and
    `patch_witness_word_indices`.** The class was never swept.

    ### The sweep, run the same way the test runs - import, THEN move the root

    Not the grep proxy. `test_the_corpus_root_bypass_count_has_not_grown`
    matches `^REPO = os.path.dirname(...)` in the source and says in its own
    docstring that it cannot see this class; 25 of the 26 below have no such
    line. Each module was imported, `cio.set_corpus_root(tmp)` called after, and
    every module-level string constant asked whether it had moved:

        pipeline/apply_reviewer_decisions.py    PART1_PATH REPO UNVERIFIED_SHIFTS_PATH
        pipeline/assemble_corrections_dataset.py CONSENSUS_PATH IN_PATH LEXICAL_PATH OUT_PATH
                                                 PART1_PATH REPO SURYA_BASELINE_PATH VLM_BASELINE_PATH
        pipeline/audit_applied_decisions.py     PART1_PATH REPO
        pipeline/build_corrections_dataset.py   ALIGNMENT_PATH DEMO_DATASET DOCAI_DIR REPO
        pipeline/build_gematria_trace.py        CACHE_DB
        pipeline/build_klal_page_regions.py     ALIGNMENT_PATH DEMO_DATASET DOCAI_DIR OUT_PATH
                                                 PART2_ALIGNMENT_PATH PART2_TRACE_PATH
                                                 PART3_ALIGNMENT_PATH PART3_TRACE_PATH REPO TRACE_PATH
        pipeline/build_klalim_demo_dataset.py   OUT_PATH REPO
        pipeline/repair_filters/docai_filter.py REFERENCE_FREQ_PATH
        pipeline/review_server.py               FRONTEND_DIR IMAGES_DIR REPO
        pipeline/verify_corrections_vision.py   CACHE_DB CANDIDATES_PATH DEMO_DATASET OUT_PATH PDF_PATH REPO
        tools/build_dicta_baseline.py           DEFAULT_OUT
        tools/build_part1_freq.py               OUT_PATH
        tools/check_klal_token_orphans.py       DOCAI_DIR
        tools/check_next_marker_and_title.py    PART1_PATH
        tools/fetch_sefaria_reference_corpus.py OUT_DIR
        tools/list_unreviewed_auto_corrections.py OUT_PATH
        tools/propose_abbreviation_expansions.py SEFARIA_FREQ_CACHE
        tools/propose_punctuation_part1.py      CACHE_DB OUT_PATH PART1_PATH
        tools/review_lexicon_gaps.py            PART1_PATH
        tools/validate_catchword_continuity.py  DOCAI_DIR
        tools/validate_klal_span_coverage.py    DOCAI_DIR
        tools/validate_lexicon_independent.py   FREQ_CACHE FREQ_META LEXICON_PATH RAW_DIR
        tools/validate_part1_corpus_integrity.py LEXICON_PATH PART1_PATH
        tools/verify_flagged_candidates_vision.py DECISIONS_PATH DOCAI_DIR PART1_PATH
                                                 REGIONS_PATH REPO REPORT_PATH
        tools/verify_reconstruction_witness.py  DOCAI_DIR IMAGES_DIR LEXICON_PATH OUT_PATH
        tools/verify_witness_vision.py          CACHE_DB DOCAI_DIR PDF_PATH QUEUE_PATH REPO

    **Stages 1, 2, 3, 4 and 5 of `rebuild_all.sh` are all in that list**, as is
    `apply_reviewer_decisions.py` - a writer of an authored file - and
    `review_server.py`, whose `IMAGES_DIR` freeze means a server pointed at
    another book would serve THIS book's scan pages beside that book's text.

    `REPO = cio.REPO` is the commonest spelling and it is the trap `corpus_io`'s
    own header warns about in as many words: "a from-import would bind the value
    once and reintroduce the defect, so don't add one." A module-level
    `REPO = cio.REPO` is a from-import wearing attribute-access clothes - it
    fires the PEP 562 hook exactly once. `pipeline/review_data.py:35` already
    writes the same warning for the shape constants and does the right thing.

    ### WHAT THIS DOES AND DOES NOT BREAK TODAY

    Stated plainly so nobody reads it as bigger than it is. **No current run is
    wrong.** `$SEFER_CORPUS_ROOT` is read before import and still works for all
    26; none of the 26 parses `--corpus` itself; and the test suite passes
    (513/513 on `test_corpus_invariants.py` + `test_pipeline_logic.py`,
    2026-09-08 - `START_HERE.md`'s "444" is stale again). What is broken is the
    SEAM: `cio.set_corpus_root()` is the documented way to point this pipeline
    at a second book, item `0AR`/`0AZ` built it for exactly that, and for these
    26 it silently does nothing. A second book's rebuild would write into this
    checkout, which is what `0BI` found the first time.

    ### The fix, and the test that should replace the literal pair

    Mechanical: drop the module-level copy and call `cio.PART1_PATH` /
    `cio.repo_path(...)` at use site. The part worth doing carefully is the
    test - generalize
    `test_the_corpus_root_seam_reaches_the_scripts_that_write_corpus_data` from
    its two hand-listed modules to the ENUMERATED set (walk `pipeline/` and
    `tools/`, find every module-level assignment of a `cio` lazy name or an
    `os.path.join(REPO, ...)`, import it, move the root, assert it followed).
    Two literals cannot ratchet a class; that is the whole reason this sat for
    five days.

    NOT FIXED - 26 modules is a scope decision, and four of them are rebuild
    stages that should not be edited between a review session and a rebuild.

0DA. **[2026-09-07] THE DIPLOMATIC EDITION SHIPS. `--edition diplomatic`
    RECONSTRUCTS THE TEXT AS PRINTED, 370 OF 374 INTERVENTIONS, WITH A
    PROVENANCE MANIFEST BESIDE BOTH EDITIONS.**

    Built for `0CZ` - Sefaria asks for "a baseline text with little intervention,
    so we can refer to a source edition for provenance". The answer is not to
    intervene less; it is to ship BOTH editions and enumerate the difference.

    `tools/export_corpus.py --edition corrected|diplomatic` (default
    `corrected`, so nothing changes for existing callers). Diplomatic walks the
    ledger BACKWARDS from the corrected text rather than reading some other file:
    there is one corpus, and both editions derive from it the same way.

    **370 interventions reverted, 4 not recoverable.** Verified end to end on the
    case that prompted it: the diplomatic text reads `עלוי` where the printer set
    it and the corrected text reads `עליו`, resolved by stable `word_id`.

    `INTERVENTIONS.json` is written beside BOTH editions, carrying every
    difference with `chosen_source`, `reviewer`, `ts`, `decision_id` and how the
    position was resolved. Of the 370: **158 (43%) came from another ENGINE**
    (vlm 126, surya 24, docai 5, dicta 3) - a machine reading the same ink got it
    right, so those correct this project's TRANSCRIPTION rather than the printed
    edition - against 156 `custom`. Only this log can tell a reader which a given
    change was; the text cannot.

    ### Two bugs found by measuring instead of declaring success

    The first version reported **266 of 607 unrecoverable**, a number that came
    within one step of being written down as a property of the ledger. It was iteration order: reverts
    were applied in ASCENDING index order, so each one shifted every later ruling
    in the same klal out from under its own text check. Resolving all positions
    first and reverting RIGHT TO LEFT took it to 370/4.

    The second was hiding behind the first. Two rulings can name one word - a
    `disputed_choice` and a `manual_correction` at the same position - so once
    the first reverts, the second finds its answer already undone. The first cut
    counted that as a refusal, which is how 237 correct positions were reported
    as failures. **Both bugs would have understated the reconstruction and
    invited exactly the wrong conclusion about what the ledger can support.**

    ### Limits, stated in the artifact rather than only here

    Reconstruction is exact for every change made through the decision pipeline.
    **A direct hand edit to `part*.json` leaves no ledger row and is invisible**
    - `START_HERE.md` lists hand edits as a permitted writer, and whether any
    exist has NOT been measured. The manifest says so in its own `limits` field,
    so a recipient reads the caveat with the data rather than from a covering
    note. The 4 unrecoverable positions are listed individually.

0CZ. **[2026-09-07] THE SEFARIA THREAD: WHAT THE LEDGER CAN ACTUALLY SAY ABOUT
    OUR INTERVENTIONS. MEASURED, BECAUSE THE DRAFT REPLY'S CHARACTERISATION IS
    WRONG.**

    Sefaria's stated acquisition standard, communicated to this project 2026-09: **fidelity to the specific edition, no added
    punctuation, no opened abbreviations, "a baseline text with little
    intervention, so we can refer to a source edition for provenance"** - plus
    **demarcation around special formatting (`@01headers`, `@02bold@03`,
    footnotes)**. Sefaria is not currently working on Yad Malachi.

    ### The draft reply says "rampant samach/peh and heh/chet substitutions". It
    ### is not what the corpus shows

    250 applied single-letter substitutions, by pair:

        כ -> ב  53      ד -> ה  20      ח -> ה   9
        ן -> ו  28      ס -> פ  19      ס -> ם   7
        י -> '  22      ר -> ה  15      י -> "   5
        ר -> ד  21      ט -> מ  12      ס -> מ   5

    **`ס->פ` is 19 (8%) and `ח->ה` is 9 (4%)** - together 11%. The dominant class
    is **`כ->ב` at 53**, nearly triple samekh/pe. Naming the two smallest of the
    top six to a professional who may ask for the data is a weak position when
    the real answer - a spread of visually-confusable sorts, led by kaf/bet - is
    better and is measured.

    Note also `י->'` (22) and `י->"` (5): those are not letter confusions at all
    but an abbreviation MARK the OCR read as a yod. Fixing them is transcription
    accuracy, not editing the edition.

    ### THE DISTINCTION THAT ANSWERS HIS QUESTION

    482 applied changes, by where the chosen reading came from:

    | source | n | what it means |
    |---|---:|---|
    | another ENGINE (vlm 144, surya 24, docai 5, dicta 3) | **176 (37%)** | a machine reading the SAME INK got it right and the corpus was wrong - a TRANSCRIPTION fix, not an edit |
    | `custom` (a human typed it) | 259 (53%) | upper bound on editorial intervention - a reviewer may type what an engine also said |
    | other / unrecorded | 47 | |

    So a large share of what the draft calls "correcting printer's errors" is
    correcting OUR OWN transcription, which is squarely inside his standard and
    needs no permission at all. `custom` is an UPPER bound and not a count of
    editorial changes; separating it properly means checking each against the
    engine readings in its snapshot, which has not been done.

    ### The flagship example CHECKS OUT, verified against the ink

    klal 38 w103. Rendered `images/pdf_pages/page_27.png` at 7x: the printer
    genuinely set **עלוי** (ayin-lamed-vav-yod) and DocAI transcribed it
    faithfully. So it is a true printer's error - a vav/yod metathesis - and not
    an OCR misread. The example is sound. It is worth noting it is neither of the
    two classes the draft names.

    ### A DIPLOMATIC EDITION IS RECONSTRUCTIBLE - this is the strong card

    **524 applied rulings changed a reading, and 100% still carry the as-printed
    text in the ledger.** So this project can hand Sefaria the baseline edition
    they ask for AND the corrected one AND a machine-readable list of every
    intervention with its evidence - which is MORE provenance than the standard
    asks for, rather than a request to be excused from it.

    Caveat, unmeasured: this holds for changes recorded through the decision
    pipeline. `START_HERE.md` lists hand edits as a permitted writer of
    `part*.json`, and any of those would not be recoverable. **`export_corpus.py`
    has no diplomatic/as-printed mode today** - the DATA supports it, the
    exporter needs the switch. Do not promise the artifact before building it.

    ### Item `0CY` is now a DELIVERABLE requirement, not just a defect

    His "demarcation around special formatting (@01headers...)" is exactly klal
    144's ten marginal item markers. As things stand they would ship as an
    inline blob of ten letters mid-sentence - the opposite of demarcated.

0DB-TODO. **HIGH PRIORITY — FOOTNOTES ARE FOLDED INTO THE BODY TEXT AND MUST
    BE ISOLATED AND DEMARCATED. 14 markers across 11 klalim in Part 1, scoped.**

    Reviewer, 2026-09-07: "we have folded a few footnotes into the body. i've
    focused on making sure the text is correct and simply added at the place in
    the text where the printer reached the end of the page - but now it seems they
    should be isolated and demarcated."

    **Priority is set by the customer, not by severity.** Sefaria asks
    contractors for "demarcation around special formatting (@01headers,
    @02bold@03, footnotes)" - footnotes are named explicitly (`0CZ`). Today they
    are indistinguishable from the author's running text, which is the one thing
    the acquisition standard asks not to happen.

    ### Scope, measured

    The edition marks a footnote with `*)`, `**)` or `")` - a convention already
    documented and crop-confirmed in
    `tools/validate_part1_corpus_integrity.py:131`, where it exists only to stop
    the paren-balance check from firing on it. **14 markers, 11 klalim:**

        klal   6 w197    klal  30 w726    klal  64 w172    klal  98 w44
        klal   7 w140    klal  30 w843    klal  71 w59     klal 106 w34
        klal   7 w467    klal  51 w58     klal  74 w407
        klal   7 w507    klal  53 w18     klal  59 w142

    **Five open a gloss**: klal 7 w467, 7 w507, 30 w843, 53 w18 and 106 w34 are
    each followed immediately by `הג"ה`, so their opening is machine-findable.
    The others are bare references or run straight on into prose.

    ### The hard part is the END, not the start

    A marker's position is unambiguous; where the note STOPS is not. `הג"ה` gives
    an opening but no closing, and the folded text was inserted at the page seam,
    so a note's last word is wherever the printer's note ended - which is a
    LAYOUT fact, recoverable from the scan and not from the text. Two signals are
    available and neither has been tested:

    - **Type size.** Footnotes are set smaller. First look was inconclusive: on
      pages 27/51/52/64 the tokens under 78% of median height are scattered
      rather than clustered at the page foot, so either the threshold is wrong or
      DocAI's boxes do not preserve the distinction. Worth a direct crop before
      relying on it.
    - **Position.** A note sits below the body block at the page foot. This is the
      stronger signal and is the same geometric argument that works for the
      marginal markers in `0CY-TODO`.

    ### Do not "fix" this by deleting

    The note text is the author's or the editor's and belongs in the deliverable -
    what is wrong is that it is INDISTINGUISHABLE from the body, not that it is
    present. The output is a demarcated note attached to its anchor, and the
    corpus keeps every word it has.

    Not started. Blocked on nothing.

0CY-TODO. **NEXT ENGINEERING TASK, agreed with the reviewer 2026-09-07:
    extract marginal item markers as structure.** The signature is measured and
    clean (see `0CY` below): a marker is a SINGLE Hebrew letter, the RIGHTMOST
    token on its line, separated from the next token by a gap of 0.029-0.045
    against a page median of 0.0075 and a 90th percentile of 0.0124 - a 2.3x
    separation with no overlap. `x` alone does NOT work: 13 body tokens on page
    52 also sit above 0.85, one at 0.884. Each marker's `y` identifies the
    paragraph it heads, so marker-to-item attachment falls out of the same
    geometry.

    **This is now a DELIVERABLE requirement, not only a defect**: Sefaria asks
    contractors for "demarcation around special formatting (@01headers,
    @02bold@03, footnotes)" (`0CZ`), and these markers are exactly that. As
    things stand they would ship as an inline blob of ten letters mid-sentence.
    Not started.

0CY. **[2026-09-07] OPEN — klal 144's `א ב ג ד ה ו ז ה ט ו` IS TEN MARGINAL
    ITEM MARKERS FLATTENED INTO THE TEXT. READ OFF THE INK. TWO OF THEM ARE ALSO
    MISREAD.**

    Reviewer: "unusual typography here is unexpected and not handled correctly.
    those are item headers they should have been embedded in the text. can you
    see the ink directly?" Yes - `images/pdf_pages/page_52.png`, which is the
    correctly-indexed render (Lesson 30).

    ### What the ink shows

    The ten letters are **not inline text**. Every one sits at **x 0.87-0.89 -
    the far right margin** - at ten DIFFERENT y positions from 0.26 to 0.77:

        א  y 0.261     ו  y 0.580
        ב  y 0.336     ז  y 0.625
        ג  y 0.367     ח  y 0.687
        ד  y 0.443     ט  y 0.716
        ה  y 0.503     י  y 0.762

    A COLUMN down the margin, one marker per item, heading ten separate list
    items - the `ואלו הן` ("and these are they") immediately after them is the
    list's own introduction. The extraction flattened the column into one
    contiguous inline blob dropped mid-sentence between `הדפוס` and `כיון`.

    **This is an extraction defect, not a text ruling.** No word is misspelled;
    the reading ORDER is wrong, and the markers have lost the items they head.
    Fixing it means teaching the extractor that a column of single glyphs in the
    margin is structure, not running text - and that is a change to how a page is
    read, so it wants its own design and its own before/after measurement.

    **Extent: 1 run corpus-wide** (4+ consecutive single-letter tokens), swept
    over all three part files. That is a FLOOR, not a ceiling - Parts 2-3 are
    largely unextracted, and this is a typographic convention a book uses
    repeatedly wherever it lists things.

    ### Two of the ten are also plain misreads, and the sequence proves it

    Confirmed at 6x against the ink: the 8th marker is **`ח`** (two legs joined
    by a full roof) and DocAI read `ה` (whose left leg is detached); the 10th is
    **`י`** (a short high mark) and DocAI read `ו` (which descends to the
    baseline). Two independent signals agree (Lesson 9): the render, and the
    sequence itself - the 8th and 10th items of a list opening `א ב ג ד ה ו ז`
    can only be `ח` and `י`.

        klal 144 w837   ה -> ח    http://127.0.0.1:8420/klal/144/word/837
        klal 144 w839   ו -> י    http://127.0.0.1:8420/klal/144/word/839

    NOT APPLIED - corpus text goes through the decision pipeline.

    ### The check that would have caught it, now in stage 4e

    `enumeration_break`: a run of 4+ single letters that is not a contiguous
    א-ב-ג sequence. **The sharpest detector in that file**, because every other
    one argues from FREQUENCY, which is evidence, while an enumeration argues
    from SEQUENCE, which is nearly proof. It costs milliseconds and it reports
    exactly the two positions above and nothing else.

    Pinned in both directions - a clean `א ב ג ד ה ו ז ח ט י` must report
    NOTHING, or the detector fires on every list in the book and carries no
    information (Lesson 25). Gate 511 -> 512.

0CX. **[2026-09-07] THE REVIEWER CHECKED ALL 18 STRUCTURAL FINDINGS. ONE WAS
    REAL. THE OTHER 20 ARE NOW ACKNOWLEDGED SO THE REPORT CAN GO QUIET.**

    Reviewer: "those 18 are fine i checked them except 167 w 68 which i fixed.
    ignore them all." **The detector stage was worth building for exactly one
    defect** - klal 167 w68, a duplicated `קי"ל` - and against 20 false
    positives, which is the precision this class was always expected to have.

    ### The problem "ignore them" creates, and the fix

    Without a baseline the stage would announce the same 20 dismissed rows on
    every rebuild forever. **A report its reader learns to skip delivers
    nothing** - Lesson 32 one level on from "a tool that prints is not a tool
    that runs" - and the next real defect would arrive inside that noise, exactly
    the way the one real defect here arrived inside 20.

    `structural_defect_acknowledged.json` records a dismissal; the stage now
    reports **NEW vs previously-acknowledged** and prints `0 NEW` when there is
    nothing unchecked. Acknowledged rows stay IN the report file, so nothing is
    hidden - they just stop being announced.

    ### The key is what makes silencing safe

    `(klal_id, detector, stored)`. **NOT `word_index`**: an index moves whenever
    an earlier edit changes the klal's word count, and an acknowledgement that
    evaporates on an unrelated edit is worse than none - the finding returns
    looking new and the reviewer re-checks work they already did.

    **`stored` IS in the key**, and that is the other half. The dismissal says
    "this text, here, is correct as printed", so it cannot outlive the text.
    Verified by mutation, both directions: injecting a fresh duplicate at klal 5
    reports `1 NEW`; changing the TEXT at acknowledged klal 86 w69 makes that
    row report as NEW again. Pinned by
    `test_acknowledging_a_structural_finding_silences_it_but_not_a_new_one`,
    including that the key is independent of `word_index`.

    ### Also this pass

    The reviewer's 3 rulings unblocked 35 more. 6 closed without a write, **29
    promoted** - klal 154 alone took 20 (`מאיזן`->`מאיזו`, `כרכא`->`כרבא`,
    `דמשכשתא`->`דמשבשתא`, ...), plus klal 167 w68's duplicate `קי"ל` deleted.
    12 open flags closed automatically, 11 reindexed. Applier converged at 0.
    Full vision rebuild: 265 cache hits, **5 live calls**. Gate 511.

0CW. **[2026-09-07] THE THREE ORPHAN DETECTORS ARE IN THE CHAIN, AND ITEM 20 IS
    CLOSED WITH A GUARD RATHER THAN A MEMORY.**

    Both of `0CV`'s actionable findings, done.

    ### Stage 4e: `pipeline/build_structural_defect_report.py`

    Runs `detect_repeated_words`, `detect_ligature_corruption` (compound form
    only) and `detect_split_merge` on every rebuild, writing
    `structural_defect_report.json`. **21 candidates today**: 12 repeated words,
    5 ligature compounds, 2 merges, 2 splits.

    Only the COMPOUND ligature form is taken. The plain dropped-lamed sweep
    already reaches a reviewer through the queue; the compound case is the one
    nothing else looks for, because the ligature swallowed the SPACE, so the
    corrupt token is not a word the lexicon or the vision adjudicator can be
    asked about - `אאמוראי` in klalim 130 and 168 is not a misread letter, it is
    two words with the boundary gone.

    **It writes a report and never a flag**, the same boundary
    `build_lexical_defect_report.py` holds, for the same measured reason: these
    carry real false positives. klal 144's `ז`+`ה` -> `זה` is a list of Hebrew
    NUMERALS being read as a word, and the repeated-word detector cannot
    distinguish a scribal repetition from an OCR one. Folding a tier into the
    review queue the way `merge_lexical_defects()` does is available at any time
    and fully reversible - it is a derived source with no ledger residue - and is
    not done here because nobody has measured a precision tier for these three.
    `test_the_structural_defect_report_is_built_and_stays_a_triage_queue` pins
    both halves: the file must exist, and no row may grow a decision-shaped
    field.

    Each detector's tuple is unpacked at its declared arity rather than with a
    positional guess - they return four different shapes, and guessing is how the
    sibling report ended up scanning its own fields with `isinstance(x, str)`.
    The new file routes every data path through `cio.repo_path()`; the
    corpus-root bypass guard caught the first version and was right to.

    ### Item 20 CLOSED, and replaced by a check

    Zero `Digitized`/`Google` tokens in the corpus, and **no Latin word of 3+
    characters anywhere in `part1/2/3.json`**. All 12 named klalim carry
    normal-length Hebrew, so it is a repair rather than a revert to placeholder.
    The original entry is kept, collapsed, because its MECHANISM is the
    instructive part.

    `test_no_latin_text_survives_anywhere_in_the_corpus` now holds the line, and
    is deliberately wider than the defect: any Latin run of 3+ letters, in
    `clean_text` or `title`, in any of the three files. This book is Hebrew and
    Aramaic - Latin in it is scanner furniture or an OCR artifact, never text -
    and the count is zero, so the bar costs nothing. Verified by mutation: it
    fails when `Digitized by Google` is appended to a klal.

    Gate 508 -> 510.

0CV. **[2026-09-07] SWEEP: WHAT PRINTS BUT DOES NOT DELIVER, WHAT THE DASHBOARD
    CANNOT SHOW, AND WHICH OPEN ITEMS ARE ENGINEERING. ALSO: ITEM 20 IS STALE.**

    Reviewer: "are there open eng. issues? are there data issues unsurfaced in
    the dashboard? ... I am here to fix bugs not adj. disputes."

    ### 1. Findings that only print

    Swept every module for a `print` reporting a FINDING in a file with no write
    path at all. 17 modules hit, but most are validators whose delivery is an
    EXIT CODE, which is a real channel. After discounting those, one genuine case
    remained and is fixed in `0CU` (`unverified_shifts`).

    ### 2. THE DETECTORS: 136 positions no reviewer can see

    All six corpus detectors and all thirteen validators are OUTSIDE
    `rebuild_all.sh`. That is only half a problem, and the halves differ:

    | detector | findings | invisible | routed? |
    |---|---:|---:|---|
    | `detect_insertion_deletion` | 144 | 75 | in-chain via `build_lexical_defect_report.py` |
    | `detect_real_word_substitution` | 109 | 43 | same |
    | `detect_repeated_words` | 12 | 10 | **NO CHAIN, NO ARTIFACT** |
    | `detect_ligature_corruption` | 5 | 4 | **NO CHAIN, NO ARTIFACT** |
    | `detect_split_merge` | 4 | 4 | **NO CHAIN, NO ARTIFACT** |

    **The 118 from the first two are a deliberate scope decision, not a bug.**
    `assemble_corrections_dataset.merge_lexical_defects()` folds only "the
    sharpest tier" into the review queue, on the explicit reasoning that these
    detectors carry heavy false positives (149 of 262 contradicted by independent
    witnesses) and that 563 permanent flags on unread material is how the
    1,496-flag queue happened. The whole set stays in `lexical_defect_report.json`
    (253 entries, 220 positions). Widening the tier is a decision available at
    any time and costs nothing - it is a derived source, not a flag.

    **The 18 from the other three are a real gap.** Nothing runs them, nothing
    stores them, and their output exists only while someone is looking at a
    terminal - which is the exact shape Lesson 32 was written about, still open
    for three detectors after that lesson was recorded. Sample, all invisible:
    klal 130 w11 / 168 w11 `אאמוראי` -> `אלא`+`אמוראי`, klal 150 w167
    `אאיזה`, klal 177 w320 `אאידך` (the alef-lamed ligature fused with the
    FOLLOWING word); five repeated-word pairs; klal 39 w258 `מרבייהו`.

    ### 3. ITEM 20 IS STALE - the damage is gone

    Item 20 records `Digitized by Google` embedded in 12 klalim. **Measured
    today: zero.** Not one watermark token, and **no Latin word of 3+ characters
    anywhere in `part1/2/3.json`.** All 12 klalim carry real Hebrew text of
    normal length (250: 238 words, 616: 991), so this is a repair, not a revert
    to placeholder. The item should be closed; it has been reading as an open
    corpus defect while the corpus has been clean.

    ### 4. The open items that are ENGINEERING, not review work

    - **`0CA`** - a word click's page navigation is undone 40-50% of the time.
      The one open defect a reviewer hits directly. Reproduction, five ruled-out
      hypotheses and the live `_showPageGen` ordering theory are in the entry.
    - **`0CO`** - `DISPUTE-QUEUE-BY-POSTERIOR.md` calls itself "the open dispute
      queue" and orders 389 of 535. Needs a decision: widen the ranker to every
      open red position, or rename the file and state the remainder.
    - **`0BX`** - the reindex collision guard. Policy, not code; and `0CI`
      measured its population shrinking.
    - **`0CE` item 7** - the synthetic-render path still addresses by INDEX, and
      the stable id rescues 0 of the suppressed rulings. Wants a deliberate
      decision about what "still valid" means now that ids exist.
    - **`0BU` Phase 3 steps 1-3** - and `0CH` found step 1's premise wrong: the
      ligature catalogue it is scoped to extract is read by nothing.
    - **`0N`** - `pipeline/second_witness_eval/` is off the rebuild path
      entirely, with two accessors referenced only by tests.

0CU. **[2026-09-07] "WHERE??" — AND THE ANSWER WAS GONE. THE APPLIER'S ONLY
    UNRECOVERABLE FINDING EXISTED NOWHERE BUT STDOUT.**

    An apply run was reported as having left one open flag past an unverifiable
    word-count shift. Asked which one, **nothing could answer.**
    `apply_reviewer_decisions.py:1181` prints `unverified_shifts` and writes them
    to no file, no ledger row, nothing - and that run's output had been piped
    through `grep`, so the klal and word were gone the moment the command
    returned.

    Two failures, and the tool's is the worse one. The first was filtering output
    that had not been read. The tool's is that **this is the only output of an apply run
    that cannot be re-derived afterwards**: every other report describes current
    state and can be recomputed, while this one describes a shift that has
    already happened, against text that has already changed. Lesson 32 in its
    purest form - a finding that only prints has not been delivered.

    ### What could still be established

    The run's word-count changes were klal 36 w14, 71 w62 and 106 w46, so it was
    one of those three. **All word-level flags in all three are now closed** (0
    open of 3 on record), so nothing is currently at risk from it - but that is
    luck, not the process working.

    ### Fixed

    `_record_unverified_shifts()` appends one JSON object per finding to
    `unverified_flag_shifts.jsonl` - klal, the index the flag is still recorded
    at, the index the shift would have moved it to, a timestamp, and why it was
    refused. Flushed per row, per the standing incremental-flush rule.

    **APPEND, not overwrite, and that is the assertion the test makes.** Every
    other per-run report here is safe to overwrite because it is re-derived from
    current state; this one is not, so the next clean run must not erase a
    finding nobody has acted on. `test_an_unverifiable_flag_shift_is_recorded_to_
    a_file_not_only_printed` fails when the mode is changed to `w`.

    Nothing consumes the file automatically: what to do about a flag that may
    name the wrong word is a human judgement, and inventing a re-point here is
    exactly what the applier refuses to do in the first place. Gate 507 -> 508.

0CT. **[2026-09-07] THE WORKLISTS NEEDED THE *OTHER* HALF OF THE BIDI FIX. AND
    THE AUTO-CORRECTION BATCH IS CLOSED: 109 OF 109.**

    Reviewer: "drift doc still reversed heb". Correct, and `0CR` fixed the wrong
    half for their viewer.

    ### Two halves, mutually exclusive, and the repo already had both

    `rtl()` wraps Hebrew in RLI/PDI so a **bidi-aware** renderer sets it
    right-to-left. `to_visual()` reorders the CHARACTERS for a renderer that runs
    **no bidi at all**, where isolates are inert and logical order therefore
    displays backwards. `0CR` shipped only the first, so a viewer doing no bidi
    still showed `רבא` as `אבר`.

    Both halves lived in `tools/preview_dicta_disputes.py`, which is why that
    file's output was the only one that read correctly - and its convention is
    `--hebrew visual` BY DEFAULT with a warning in the file header. `to_visual`,
    `render_hebrew()` and `VISUAL_WARNING` are now in `corpus_io` beside `rtl`,
    and the three worklist generators take the same `--hebrew visual|logical`
    flag with the same default and the same header warning.

    **They are mutually exclusive by nature**, which is why they are one function
    and one flag rather than two independent choices: `python-bidi` predates UBA
    6.3 and raises "RLI not allowed here" on the isolates outright, so visual
    mode strips them first. Discovered by both tools crashing the moment the two
    fixes met.

    **The cost is real and every such file now says so in its own first lines:**
    Hebrew copied OUT of a visual file pastes reversed, including back into this
    pipeline. `--hebrew logical` produces the copy-safe version.

    ### THE AUTO-CORRECTION BATCH IS CLOSED

    **109 of 109 answered, 0 open.** The class that stood at 109 open this
    morning - `ai-dropped-lamed-correction` words applied to the corpus in August
    and never checked by a human - is done.

    ### Also this pass

    13 more rulings closed by `close_satisfied` without a write; 6 promoted:
    klal 36 w14 `[.]` deleted, 70 w32 `סרק`->`פרק`, 71 w5 `היינן`->`היינו`,
    71 w62 `עב` deleted, 73 w87 `עלי`->`על`, 106 w46 `:` deleted. Applier
    converged at 0. Gate 507.

    **One flag needs a human:** a word-count change moved past an open flag that
    could NOT be verified at the shifted index, so it was left where it is and
    may now name the wrong word. The applier reports these by design rather than
    guessing.

0CS. **[2026-09-07] APPLYING AN EDIT WAS RE-OPENING FLAGS THE REVIEWER HAD
    ALREADY ANSWERED. FOUND BECAUSE A WORKLIST COUNT WENT UP.**

    The only symptom: `UNREVIEWED-AUTO-CORRECTIONS-WORKLIST.md` went **1 -> 4**
    across an apply. Nothing else reported anything.

    ### The mechanism, both halves

    Applying a word-count change fires `reindex_flags_after_shift()`, which moves
    an open flag onto the word it names — correct. It does NOT move the ruling
    that ANSWERED that flag, and must not: the decision reindexer deliberately
    skips anything already in the corpus. So after klal 54's two-word split, the
    flag sat at w787 while its answer stayed recorded at w786, and
    `flag_answered_by_a_later_decision` failed **twice over**:

    1. **The index lookup missed** - it asks `source.get((klal_id, word_index))`,
       and the two are no longer at the same index.
    2. **The timestamp test rejected it.** The moved flag is a NEW record with
       today's ts, so the ruling that answered it looked OLDER than the flag -
       and "only a decision newer than the flag answers it" is a deliberate rule
       (a flag raised after a decision is a fresh concern).

    Three klal 54 flags re-opened this way, all three with word ids that match
    exactly across the shift (flag `word_id` 787 == ruling `word_id` 787). This
    is Lesson 35's shape - applying a correction has side effects on review state
    and every one must be carried out in the same step - in the one place that
    entry did not reach.

    ### The fix, both halves

    **`reindex_flags_after_shift` now passes `supersedes=<old flag id>`** on the
    flag it writes. The field already existed and this is exactly what it means:
    the moved flag is the same flag, not a new one. `review_counts._raised_at()`
    follows that chain to the root and asks when the flag was ORIGINALLY raised.

    **`flag_answered_by_a_later_decision` now also matches by stable word id**,
    after the index test and not instead of it: the index test is exact and
    cheap, and most records still carry no id.

    Both are needed - either alone leaves the flag open. Pinned by
    `test_a_reindexed_flag_does_not_reopen_the_ruling_that_answered_it`, which
    fails when the `_raised_at` half is reverted. Gate 506 -> 507.

    **FORWARD-ONLY.** The three klal 54 flags already written carry no
    `supersedes`, so nothing can recover their original raised-time without
    parsing the "[reindexed from wN" note as prose - refused, on the same grounds
    as `0CK`. They are three clicks. Any flag reindexed from now on is correct.

    ### Two traps walked into while fixing it, both already documented here

    `_backfilled()` called `rd.backfilled_word_ids(path)` POSITIONALLY, and the
    applier test harness redirects the ledger by injecting `path=<tmpdir>` as a
    KEYWORD - "multiple values for argument 'path'". `review_decisions.
    superseded_by_an_applied_decision` carries a comment about this exact trap.
    And the first version read the default ledger regardless of what the caller
    passed, which is the ambient-state problem `resolve_word_index`'s `id_state`
    comment already calls out. `path` is threaded through both functions now.

    ### `RED-WITHOUT-A-CANDIDATE.md` DELETED

    It was a one-off written inline to answer "where are the 76", never a tool,
    so nothing regenerated it and it was stale within the hour - the exact
    anti-pattern Lesson 32 names. Its question is answered and recorded in `0CO`;
    re-measured today the numbers are 535 red, 59 with no candidate entry, 58 of
    those carrying an open flag and **1** unexplained (was 76/68/8 - the apply
    passes closed most of them). Re-derive from
    `/api/word-states?bucket=machine_disputed` if it is wanted again, or promote
    it to `tools/` properly.

0CR. **[2026-09-07] THE WORKLISTS RENDERED HEBREW BACKWARDS AROUND AN ARROW.
    A REPORT BUG ONLY — THE CORPUS IS IN CORRECT LOGICAL ORDER, VERIFIED TWO
    WAYS. AND THE FIX ALREADY EXISTED IN ONE FILE.**

    Reviewer: "you are rendering the hebrew backwards. fix and confirm this is
    just an issue in the gen .md - not an issue with the tooling or the data."

    ### The data is CORRECT, checked independently of the reports

    1. **Letter order.** klal 38 w148 stores `אליעזר` as ALEF, LAMED, YOD, AYIN,
       ZAYIN, RESH — logical order. Equal to the logical string, not to its
       reverse.
    2. **Word order, against the scan's own geometry.** DocAI tokens for a line
       have strictly DECREASING x across their stored order, which is right-to-
       left — so stored order IS reading order. This is independent of any
       report and of the corpus itself.
    3. `part1/2/3.json`, `review_decisions.jsonl` and `word_identity.json`
       contain **zero** bidi control characters. Nothing leaked into the data.

    ### The report bug, measured with python-bidi rather than argued

    A `.md` is an LTR-base document. Two Hebrew runs separated only by neutral
    characters resolve into ONE right-to-left run, so they swap and a mirrored
    arrow comes with them:

        logical:  - `אא` -> **`אלא`**
        DISPLAYS: - `אלא`** <- `אא`**

    A "before -> after" row therefore reads as "after <- before" — the repair
    running the wrong way. The CONTEXT lines were never wrong: a Hebrew phrase
    is one run and reversing it IS correct RTL.

    ### The fix existed, in exactly one file

    `tools/preview_dicta_disputes.py` already had `RLI`/`PDI` isolates and an
    `rtl()` helper, with a comment naming the repo's own `direction: rtl;
    unicode-bidi: isolate` as the model. **It was the only copy, so it produced
    the only correctly-rendered reports.** Moved to `corpus_io` as `rtl()` and
    `RLI`/`PDI`; that file now re-exports the shared names, and the two broken
    generators import them. This is the standing rule's exact case — the fix
    already existed in a sibling and never reached the others (Lesson 13), which
    is now three times in one day for me.

    | file | unanchored Hebrew-arrow-Hebrew pairs |
    |---|---:|
    | `CROSS-EDITION-WORKLIST.md` | 403 -> **0** |
    | `UNREVIEWED-AUTO-CORRECTIONS-WORKLIST.md` | 1 -> **0** |
    | `DRIFTED-RULINGS-WORKLIST.md`, `DISPUTE-QUEUE-BY-POSTERIOR.md` | 0 already — they put a Latin word (`chose`, `consensus`) between the two readings, which anchors them |

    Belt and braces on both: a Latin anchor word (`was` / `now`, `corpus` /
    `consensus`) AND the isolates, so the rows read correctly in a renderer that
    implements bidi and in one that does not.

    ### Also this pass

    The reviewer deleted the duplicate `משמע` from `0CQ` — recorded, and it
    needed APPLYING, which is the two-step working as designed. Applied; klal 198
    now reads `ובמנחות פרק שתי הלחם משמע דס"ל`, zero duplicates.

    **Full vision rebuild run with the reviewer's authorisation** (they asked
    about klal 198 w576 still showing confused). 249 cache hits, **14 live
    `gemini-3.6-flash` calls** — the cache did nearly all of it. All 7
    `stale_candidate` flags cleared, w576 included; both failing invariants now
    pass. Gate 506.

0CQ. **[2026-09-07] SECOND APPLY PASS — AND THE GATE CAUGHT A RULING THAT PUT
    A DUPLICATE WORD IN THE CORPUS. THE REVIEWER'S RULING, NOT A BUG.**

    27 more rulings (15 `manual_correction`, 8 `witness_choice`, 4
    `disputed_choice`). `close_satisfied` closed 12 without a write; the applier
    promoted **7**, verified by diff:

        klal  25 w364  דברין -> דבריו       klal  30 w853  אב"ר -> אב"ד
        klal  37 w344  גכ    -> גב          klal  37 w352  ורוק -> ודוק
        klal  38 w103  עלוי  -> עליו        klal 198 w809  שרוא -> שהוא
        klal 198 w570  שתישההולאחם -> שתי הלחם משמע   (1 word -> 3)

    ### THE GATE CAUGHT A REAL DATA ISSUE, which is what it is for

    `test_no_new_duplicate_consecutive_words` failed on **(198, `משמע`)**. klal
    198 now reads:

        ... ובמנחות פרק שתי הלחם משמע משמע דס"ל שהוא רק לאו ...

    The garbled OCR word `שתישההולאחם` was ruled to be `שתי הלחם משמע` — but
    `משמע` ALREADY followed it. Before: `פרק שתישההולאחם משמע דס"ל`. After: two
    `משמע` in a row. The repair looks right as far as `שתי הלחם` (the Menachot
    chapter name); the third word duplicates what was already there.

    **This is a data issue, not a bug** — the pipeline did exactly what it was
    told. It is the same failure mode as klal 128's `לאוקומי לאוקומי`
    (2026-08-06), and it is caught by a cheap mechanical sweep that costs
    milliseconds, which is Lesson 18 paying for itself: no vision pass and no
    semantic review would have found this, because both words are correct
    Hebrew and correct in context individually.

    NEEDS A HUMAN: delete one `משמע` (now at klal 198 w572/w573) against the
    scan. Not fixed here - corpus text goes through the decision pipeline.

    ### The other failure is benign and self-describing

    `test_no_stale_candidate_flags_are_being_served`: 7 candidates in klal 198
    flagged `stale_candidate`, because the +2 word-count change shifted every
    later index and `--skip-vision` does not re-derive them. The test's own
    message names the remedy - a full `./rebuild_all.sh` WITH vision. Not run
    here: it spends live Gemini calls and that is the reviewer's budget.

    ### The id work paid off on its first live run

    klal 198 w570 changed the word count, which fired
    `reindex_flags_after_shift` for the first time since `0CL`. Both moved flags
    came out carrying the id of the word they landed on - klal 198 w894
    `word_id` 893, w969 `word_id` 968 - while the two closures at the old
    indices correctly carry none. Those two flags will never need reindexing
    again.

    ### Trajectory, measured, because the reviewer asked whether this is closing

    | | |
    |---|---:|
    | rulings on record | 971 |
    | recorded 2026-09-07 alone | 145 |
    | red (`machine_disputed`) remaining | 539 |
    | purple (`ai_flag`) remaining | 169 |
    | open word positions | 714 across 136 klalim |

    Red and purple OVERLAP by ~68 (item `0CO`), so the union is roughly 640
    positions, not 708. At today's rate that is several more sessions of review,
    not a session. **The special cases ARE closing** - the auto-correction batch
    went 109 -> 1, the applier converges to 0 after every pass, both clearing
    tools are at their floor - but the DISPUTE queue is the bulk of the work and
    it is barely dented: 971 rulings have retired roughly 183 red words, because
    most rulings confirm rather than change.

0CP. **[2026-09-07] APPLIED THE REVIEW PASS: 93 CLOSED WITHOUT A WRITE, 17
    PROMOTED INTO THE CORPUS. THE GATE WENT RED ON A STATUS THAT HAD NEVER
    EXISTED BEFORE.**

    `0CG`'s order, run on the reviewer's own pass. `close_satisfied_rulings.py
    --apply` closed **93** (92 by stable word id) without touching `part1.json`,
    which took the applier from **82 to 17** - the confirmations were rulings the
    corpus already held. The 17 that remained are the genuine changes.

    **The corpus diff, verified word by word against the intent: 17 changes
    across 10 klalim, nothing collateral.** 16 replaces and one delete:

        klal  63 w40   סד -> (deleted, a folio marker in י"ד רסי' כ"א סד)
        klal  69 w173/181, 75 w745, 165 w17, 208 w11, 216 w37   לא -> אלא
        klal  74 w110  נופי -> גופי      klal 74 w309  בס"ד -> בפ"ד
        klal  74 w319  דגם  -> הגם       klal 74 w332/366  ארת -> את
        klal  75 w942  משוס -> משום      klal 91 w136  שואים -> שואלים
        klal  91 w406  והא  -> דהא       klal 200 w54  אפאנדרי -> אלפאנדרי
        klal 214 w150  ישמע -> ישמעאל

    Applier converged at 0 after the rebuild. 3 open flags closed automatically
    by `close_flag_satisfied_by`. Drifted rulings 13 -> 15.

    ### THE GATE FAILED, and the test was wrong rather than the code

    `test_the_word_list_behind_a_legend_count_is_exactly_what_that_count_counts`
    asserts every recorded row carries a status from an enumerated set, and klal
    63 w40 came back **`retired`**, which was not in it.

    `retired` is not new and not an error: `review_server.py:960` has set it
    since the id work landed, for a ruling whose word a later ruling DELETED -
    "an answer rather than a failure to find one" - and it is the same status
    `rd.resolve_word_index` documents and `repoint_stale_decisions.py` refuses a
    re-point on. **It had simply never been PRODUCED.** Reaching it needs an
    applied deletion at a word carrying a stable word id, and the first one in
    this project's history was klal 63 w40, today. The set was written from the
    statuses that existed when the test was written, which is the failure mode an
    enumeration has: it is correct until the system produces one more.

    Fixed by completing the set, not by loosening the assertion. Gate 506.

0CO. **[2026-09-07] OPEN: THE RANKED DISPUTE QUEUE COVERS 394 OF THE 558 RED
    WORDS ON SCREEN. WORKING IT TO ZERO WOULD LEAVE 164 RED, WITH NO WORKLIST
    POINTING AT THEM.**

    Found answering the reviewer's "what's left". `DISPUTE-QUEUE-BY-POSTERIOR.md`
    calls itself "the open dispute queue" and is the tool built to order exactly
    that question. Measured against `/api/word-states?bucket=machine_disputed`,
    which is what the text pane actually draws red:

    | | |
    |---|---:|
    | red (`machine_disputed`) positions on screen | **558** |
    | rows in the ranked queue | 436 |
    | in both | 394 |
    | **red but NOT in the ranked queue** | **164** |
    | ranked but not currently red | 42 |

    **The 164, by what backs them:** 76 have **no entry in
    `review_queue_part1.json` at all**, scattered across 45 klalim (not the
    witness-queue klalim 30/75/88, so not item `3`); the other 88 have queue
    entries whose flag is not a consensus dispute — `current_text_may_be_wrong`
    49, `possible_omission` 17, `unverified_insertion` 16, `ambiguous` 5.
    `rank_dispute_queue.py` scores by consensus stratum (which engines agree), so
    a candidate with no consensus behind it has nothing to score and drops out
    silently.

    **The 42 going the other way** are rows the ranked queue lists that the text
    pane draws GOLD, not red: 33 `current_text_confirmed`, 6
    `docai_ligature_artifact` — both members of
    `review_counts.MACHINE_RESOLVED_FLAGS`.

    So the file's own header count is not the number of open red words, in either
    direction. This is the shape `0CH` deleted `flagged_klalim` for and `0CN`
    caught in a tool written hours earlier: two answers to one question, and the
    reviewer has no way to see which one they are looking at. It is worse here
    because the ranked queue is the DOCUMENT a reviewer works from — a worklist
    that silently covers 71% of its own subject.

    NOT FIXED, and the fix is a decision rather than a patch. Either
    `rank_dispute_queue.py` widens to every open red position and says
    "unscoreable" for the ones with no stratum (honest, and the file stops
    claiming completeness it does not have), or it keeps its scope and is
    RENAMED to what it actually is — the scoreable consensus disputes — with the
    remaining count stated beside it. **What must not stand is a file called "the
    open dispute queue" that is missing 164 of them.**

    ### RESOLVED same day: what the 76 are

    **68 carry an open word-level `klal_flag`.** `review_counts.word_states()`
    marks an open flag as `DISPUTED`, so these render RED in the text pane and
    are ALSO counted as purple `ai_flag`. **The two legend buckets are not
    disjoint**, which is the thing to know before reading red + purple as a
    total, and it is not stated anywhere the reviewer can see.

    **The other 8 are in klalim 30 and 75 only** - two of the three
    witness-queue klalim (30/75/88, open item `3`, 419 rows). The witness queue
    addresses words by `docai_token_index`, NOT by corpus `word_index`, so it
    cannot be matched against corpus positions by number and its items cannot
    appear in `review_queue_part1.json` by construction. Listed in
    `RED-WITHOUT-A-CANDIDATE.md` with context.

    So nothing here is unaccounted for. What remains is the presentation defect:
    a legend whose two largest buckets overlap by 68 words without saying so, and
    a "dispute queue" that orders 394 of 558. Both are still open.

0CN. **[2026-09-07] THE REVIEWER WORKED THE WORKLIST — 94 OF 109 ANSWERED. THE
    TOOL SHIPPED THAT MORNING HAD THE EXACT BUG `flagged_klalim` WAS DELETED
    FOR, AND THE NEW STALENESS CHECK HAS A RACE.**

    84 rulings recorded in the dashboard: 56 `manual_correction`, 28
    `disputed_choice`, append-only verified against the pre-session ledger.
    Mostly CONFIRMATIONS (`אלא` -> `אלא`) — which is what
    accepting one of these looks like — with real changes among them
    (`לא` -> `אלא` off `vlm_reading`).

    ### A bug shipped that morning, caught on the first re-run

    `list_unreviewed_auto_corrections.py` selected open flags with
    `flag.get("needs_revisit")` — **the naive filter, hand-rolled, two commits
    after `0CH` deleted `flagged_klalim()` for being exactly that.** A word-level
    flag is ALSO answered by a human ruling recorded at that word, so a reviewer
    who confirms the machine's text has answered the flag without ever clicking
    "clear revisit flag". Regenerating would have listed 90 of their finished
    rows back to them as outstanding.

    Fixed by importing the predicate instead of re-deriving it
    (`review_counts.flag_still_open`, which is what the dashboard asks). **90 ->
    14 open, 95 answered.** The lesson is not "check needs_revisit properly", it
    is Lesson 13's: a second answer was written to a question that already had one,
    in a file whose whole purpose was to agree with the dashboard. Deleting the
    old copy did not stop me making a new one.

    ### The staleness check has a race, and it fired the first time it mattered

    `START_HERE.md`'s snapshot-and-diff reported `review_decisions.jsonl`
    **CHANGED** across a rebuild — which is precisely the bug that invariant
    exists to catch, and was not one. Two rows had been appended by the reviewer,
    in the dashboard, during the ~40 seconds the rebuild took. The diff cannot
    distinguish "a rebuild stage wrote this" from "a human wrote this during the
    rebuild"; only the rows can, and they were `reviewer: local`, timestamped
    inside the window. Caveat now in `START_HERE.md`: **read the added rows before
    filing a rebuild stage as a ledger writer**, and take the snapshot when the
    dashboard is idle. Lesson 44 with the roles swapped — there a background job
    mutated a tree someone was editing, here a foreground job measured one.

    ### Where the pipeline stands after the pass

    | | |
    |---|---:|
    | applier would promote | **82** (12 replace, 58 manual, 12 confirmed-no-op) |
    | `close_satisfied` would close without touching the corpus | **74** (73 by stable word id) |
    | `repoint` re-pointable / stale | 0 / 12 |
    | auto-correction flags still open | **14 of 109** |
    | drifted rulings | 11 -> **13** |

    The applier's 82 and close_satisfied's 74 **overlap heavily** — a confirmation
    is a ruling the corpus already holds, so the applier would write it and
    `close_satisfied` would settle it without a write. `0CG` established the
    order: close first, then apply what genuinely changes. NOT RUN — promoting is
    the reviewer's deliberate step.

    Rebuild ran: `review_queue_part1.json` 703 -> 691 (12 decided disputes drop
    out), ranked queue 453 -> 436, consensus disputes 107 -> 105, `part*.json`
    and the sidecar untouched.

0CM. **[2026-09-07] THE 90 UNREVIEWED AUTO-CORRECTIONS AS ONE WORKLIST, WITH
    THE TWO INDEPENDENT SIGNALS ON EVERY ROW. 82 TRIAGE CLEAN, 8 WANT A LOOK.**

    `tools/list_unreviewed_auto_corrections.py` ->
    `UNREVIEWED-AUTO-CORRECTIONS-WORKLIST.md`, built at the reviewer's request
    after they opened two of these flags and asked what the issue was. Ordered by
    klal then word index, which is reading order, so it works top to bottom.

    **What they are.** `ai-dropped-lamed-correction` restored the lamed the
    19th-century `ﭏ` sort drops when it wears (`אלא` prints as
    `אא`), applied it to the corpus in Aug 2026, and recorded it as a
    `manual_correction` - the type the dashboard draws as human-decided - so it
    never reached a review queue. **Verified while building this: all 90 sit on
    the word their own correction produced.** None has drifted, nothing is
    misplaced. The only question is whether the machine restored the right
    letter.

    **Two signals per row, chosen because they fail differently (Lesson 9).**
    STRUCTURE, `typography.dropped_lamed_explains()`: is the stored word exactly
    the corrupt form with one lamed restored after an alef? FREQUENCY,
    `sefaria_reference_corpus`: 6.18M words with no lineage to this scan - the
    only independent arbiter available here, because `lexicon.txt` was built from
    this corpus's own OCR and absorbed this very corruption, and vision is a
    fourth reader of ink a defect in the SORT is upstream of (Lesson 24).

    | triage | count |
    |---|---:|
    | clean - corrupt form unattested | 50 |
    | clean - repair far commoner | 32 |
    | LOOK - both forms attested | 5 |
    | neither form in the reference corpus | 3 |

    The 8 that are not "clean" are the interesting ones and they are named: klal
    69 w112, 138 w47, 144 w619, 158 w176, **200 w58** (the standing
    counter-example - `איהו` is itself a common Aramaic word,
    so frequency cannot arbitrate it), and the three `אלגאזי`
    rows, a proper name the reference books had no occasion to use.

    **A label bug found and fixed while building it.** The first version printed
    an absent form as a measured `0x` and called it "no reference data". Absent
    and counted-zero are the same NUMBER and not the same STATEMENT: printing
    `אלגאזי` as `0x` reads as evidence against a correct
    repair, when the truth is that Talmud/Rashi/Rambam/Tur/Shulchan Arukh simply
    never name this rabbi. Rows now say "not in it", and the triage label
    distinguishes "neither form in the reference corpus" from "repair
    unattested" and from "reference corpus unavailable" - three different
    situations the first cut collapsed into one.

    **The triage is a place to start, never a verdict** (Lesson 2). Clearing
    these is also the cheapest route to the addressing problem `0CK`/`0CL`
    describe: a flag a reviewer closes needs no stable id at all.

0CL. **[2026-09-07] THE MACHINE FLAG WRITERS NOW ATTACH THE ID AT WRITE TIME —
    THE TAP AND THE LOOP. AND THE 284 OPEN FLAGS SPLIT INTO FOUR GROUPS, ONE OF
    WHICH IS A DEAD END NOBODY HAD LOOKED AT.**

    `0CK` step 1, done. Two sites, and they are the complete set — every other
    `klal_flag` writer either already has the id (`review_server.py:1761`, since
    `3f623f9`), writes a klal-LEVEL flag that correctly gets none
    (`reconstruct_placeholder_klalim.py`), or writes a CLOSURE, which is not
    reindexed (`apply_reviewer_decisions.py:199` and `:324`).

    **The tap:** `flag_unreviewed_auto_corrections.py` now merges
    `word_identity.snapshot_fields()` into the flag it writes — the same seam
    `review_server._with_word_id` uses, not a private copy. It already had the
    position in hand; it was writing the ruling id into the note as ENGLISH and
    the word id nowhere.

    **The loop:** when `reindex_flags_after_shift` DOES move a flag, the flag it
    writes at the new index now carries the id of the word it landed on, so **that
    move is the last one it needs** — the skip added in `0CK` passes over it
    forever after. This is safe only because of the ordering, which is now named
    in the code: `save_part1()` -> `widentity.follow_corpus()` -> the reindexers,
    so `id_at(new_wi)` describes the post-shift corpus. Read before
    `follow_corpus`, the same call returns the id of whatever USED to sit there.

    Three tests, each mutation-checked. Gate 505 -> 506.

    ### The 284 open Part 1 flags, grouped by what a migration could do

    | group | flags | live URL of one |
    |---|---:|---|
    | **A** template `Original ruling <id>`, ruling HAS a word id — **inheritable** | **85** | `/klal/38/word/148` (`אליעזר`) |
    | **B** same template, ruling has NO word id — gains nothing | 5 | `/klal/169/word/22` (`ושמואל`) |
    | **C** different template `decision <id>` — **DEAD END** | 40 | `/klal/24/word/247` (`הכמים`) |
    | **D** no ruling id in the note at all | 154 | `/klal/14/word/158` (`דמגילח`) |

    **Group C is the finding.** It reads like a second template worth a second
    pass, and it is not: **all 40 name a `klal_flag` whose own `word_index` is
    None** — a klal-LEVEL flag, which names no word by construction, so there is
    no word id to inherit and never will be. `local-backfill-2026-08-17` linked
    each word-level flag to the klal-level finding it came from, which is the
    right provenance and the wrong direction for this. Checked on all 40, not on
    the sample: 40 of 40 are `('klal_flag', 'klal-level/none')`.

    So the migration's real ceiling is **85 of 284**, and groups B, C and D — 199
    flags — stay on `reindex_flags_after_shift` permanently unless a reviewer
    re-writes them. That is the honest number to weigh against the risk, which
    `0CK` states: after this session's skip, a wrong id makes a flag sit
    permanently on a wrong word with nothing left to move it.

    ### CORRECTION, same day, and the framing above is what needed it

    The reviewer opened the first two group-A URLs and asked what the issue was:
    "they point to the correct word. what's the issue?" **There is none, and the
    grouping above should not be read as defect triage.** Every one of these 284
    flags names the right word today. Nothing here is misplaced, and the four
    groups sort them by whether a hypothetical FUTURE migration could give them a
    stable id — which only ever matters for a flag still open when a later
    correction changes its klal's word count.

    **All 90 of groups A+B are one class**: `ai-dropped-lamed-correction`
    restored the lamed the `ﭏ` sort drops (`איעזר`->`אליעזר`, `אא`->`אלא`),
    applied it to the corpus in Aug 2026, and recorded it as a
    `manual_correction` — the type the dashboard draws as human-decided — so no
    human ever checked it. The flag is that check, owed. The reviewer's read on
    the first two ("I would accept the text in both cases") is the correct
    outcome for that class, and **a flag a reviewer clears needs no id at all**:
    reviewing them dissolves the addressing question rather than solving it.

    The open flags are REVIEW WORK, not addressing work, and the id migration is
    a hedge against them staying open, not a repair. Full breakdown of the 284:

        134  ai-semantic-spotcheck-round4
         90  unreviewed auto-correction by ai-dropped-lamed-correction  <- groups A+B
         40  local-backfill-2026-08-17                                  <- group C
         20  seven other writers

0CK. **[2026-09-07] THE REINDEXERS NOW SKIP A RULING ADDRESSED BY ID. STEP 2 IS
    BLOCKED, MEASURED THREE WAYS — AND THE LINKAGE THAT WOULD UNBLOCK IT EXISTS,
    IN PROSE, IN 130 FLAG NOTES.**

    ### Step 1, done: the id skip, on BOTH reindexers

    `reindex_pending_decisions_after_shift` and `reindex_flags_after_shift` now
    skip a record for which `rd.word_id_of()` returns an id. The reindexer exists
    to keep an INDEX-shaped address pointing at its word; a ruling addressed by
    id does not have that problem, and moving it appends a superseding copy that
    changes only a number `resolved_position()` no longer reads. **This is how
    the reindexer retires — one ruling at a time as ids reach them** — rather
    than by being switched off while rulings that still need it exist.

    A RETIRED id is skipped too, deliberately: the word was removed, so no index
    describes it, and moving the ruling onto whatever now sits at `wi + delta`
    would attach a human's decision to a word they never saw. Same refusal
    `repoint_stale_decisions.py` already makes.

    Both reindexers got it, not just the one that fires today (Lesson 34). The
    flag version is INERT — 0 of 1,367 flags carry an id — and goes live for
    flags written from now on, which do carry one since `3f623f9`.

    **Two paired tests, and both mutations fail.** `..._is_not_reindexed` for
    each reindexer, deliberately identical to the existing "is moved too" tests
    except for the `word_id` in the snapshot. Mutated to skip unconditionally,
    the two OLD tests fail; mutated to never skip, the two NEW ones fail. A skip
    that could not distinguish would pass its own test alone (Lesson 25). Gate
    503 -> 505.

    ### Step 2 is BLOCKED. Adding `klal_flag` to `RULING_TYPES` backfills ZERO

    Run as an experiment before being believed: `RULING_TYPES` extended,
    dry run, reverted. 1,111 more records enter and **every one is refused** —
    592 "klal is not in part1.json" (Parts 2-3 are not seeded), 584 "no exact,
    corroborated address". Not a tuning problem. **A `klal_flag` names a POSITION,
    not a WORD**: `candidate_snapshot` is null, there is no `chosen_text` and no
    `original_word`, so `word_identities_of()` returns nothing and every
    text-matching branch of `resolve_word_index` falls through. The backfill's
    whole safety property is corroborating an address against the word it names,
    and a flag offers nothing to corroborate against. This is the honest reason
    `klal_flag` was left out of `RULING_TYPES`, and it is a better reason than
    the omission looked.

    Three routes, all measuring 0 against today's ledger:

    | route | ceiling |
    |---|---:|
    | extend `RULING_TYPES` | **0** — measured, above |
    | inherit from the ruling a flag names via `applied_decision_id` | **0** — no open Part 1 flag sets that field |
    | parse the note prose | refused as a method |

    ### THE FINDING: the linkage exists, in the wrong place

    **130 of the 284 open Part 1 flags name a 12-hex ruling id inside their note
    text**, and all 130 resolve to real ledger rows — `flag_unreviewed_auto_
    corrections.py` writes "Original ruling 689c22c0d7db, recorded at w113 and
    re-derived to this position" as PROSE. **85 of those rulings carry a stable
    word id**, which the flag could inherit on a genuinely corroborated basis:
    the flag was written ABOUT that ruling's word.

    So the ceiling is not really 0 — it is **85 of 284**, gated behind a field
    that the writers fill in with English instead of data. Two consequences, and
    neither is a tidy-up:

    1. **Fix the writers** — DONE, see `0CL`. **And not the way this entry first
       said.** It proposed setting `applied_decision_id`, which already means
       something else on a flag: all 129 rows that carry it are `needs_revisit:
       false` closures written by `close_flag_satisfied_by`, where it means "the
       ruling that ANSWERED this flag", not "the ruling this flag is ABOUT". One
       field, two opposed senses, in an append-only log — Lesson 48's exact trap.
       The right fix needs no linkage field at all: attach the word id at write
       time, the way the dashboard already does.
    2. **The existing flags need a decision.** Recovering them means reading an
       id out of prose, once, in a labelled migration — the class of move this
       repo distrusts. Reviewer's call. Grouped, with live URLs, in `0CL`.

0CJ. **[2026-09-07] RAN THE BACKFILL. THE DECISION-REINDEXER'S POPULATION IS
    NOW 38% ID-ADDRESSED, THE FLAG ONE IS STILL 0% — AND THE REINDEXER DOES NOT
    YET LOOK AT IDS, WHICH IS THE STEP THAT ACTUALLY RETIRES IT.**

    `0CI` step 1, applied. `tools/backfill_word_ids.py --apply` wrote **18
    annotations**; ledger 4,164 -> 4,182, first 4,164 rows byte-identical, all 18
    `word_id_backfill` with no `chosen_text` and no opcode, each naming the ruling
    it annotates — annotations, not superseding copies (Lesson 46).

    | | before | after |
    |---|---:|---:|
    | pending rulings carrying a stable id | 0 / 24 | **9 / 24** |
    | open word-level flags carrying one | 0 / 290 | 0 / 290 |
    | backfill annotations on record | 601 | 619 |

    The 9 sit at 6 positions — klal 35 w54 carries three ruling types at one
    index, 69 w187 two — plus 39 w13, 63 w40, 69 w337, 210 w130. Predicted 7 from
    the gainers list; the measured 9 is higher because `all_current` keys per
    type and several positions carry more than one.

    ### The regression that fired last time did NOT fire this time

    The 601-row backfill broke the decision-history panel for 299 words
    (`0CC`): `history_for_word_id` matched the ANNOTATION and missed the RULING.
    Checked all 6 newly-annotated positions through `/api/decisions/<k>/<w>`:
    every one returns its rulings, tagged `word_id_source: backfill`, and no
    `word_id_backfill` row appears in any panel. The `ANNOTATION_TYPES` class
    exclusion holds under new annotations, which is what it was written for.

    ### The rebuild moved NOTHING, and that is the rule's other half

    Ran the snapshot-and-diff check `START_HERE.md` now prescribes. All 15 files
    identical — three authored, ten derived. So an `apply_event` moves the queue
    (`0CG`: 707 -> 703) and a `word_id_backfill` annotation does not. Both halves
    of "a write to an authored file" are now measured rather than assumed, and
    they differ.

    ### WHAT THIS DOES NOT DO, and it is the next step

    `reindex_pending_decisions_after_shift` **does not check for a word id**
    (`apply_reviewer_decisions.py:236-241`: it filters on applied-ness and on the
    snapshot naming a text, nothing else). So all 9 id-carrying rulings would
    still get an index-shaped superseding copy on the next word-count shift. The
    id helps them at APPLY time, through `resolved_position()`; it does not yet
    keep them out of the reindexer.

    **Making the reindexer skip a ruling that carries a stable id is what
    actually retires it, incrementally, ruling by ruling** — and it shrinks
    `0BX`'s collision surface directly, since a ruling that is never moved cannot
    collide. Small and testable. NOT DONE: it changes the applier's write
    behaviour, so it wants its own deliberate step and a synthetic test for the
    skip, in the shape `0BZ`'s prospective id tests already use.

0CI. **[2026-09-07] "IS REINDEXING STILL NECESSARY NOW THAT IDS EXIST?" YES —
    AND THE MEASUREMENT IS THE FINDING. THE ID LAYER COVERS 0% OF WHAT EITHER
    REINDEXER ACTUALLY MOVES.**

    Reviewer, asked before agreeing to build `0BX`'s collision guard: "why do we
    need to worry about reindex - will it still be necessary?" The premise is
    sound — `resolved_position()`'s own docstring says the reindexer is what ids
    "paper over", and a ruling that carries an id "does not need any of that".
    Measured against the live ledger, the id layer is not there yet.

    | population the reindexer moves | count | carry a stable id |
    |---|---:|---:|
    | pending rulings (`candidate_choice`/`manual_correction`/`disputed_choice`) | 24 | **0** |
    | open word-level `klal_flag`s | 290 | **0** |
    | all word-level `klal_flag` rows ever | 1,367 | **0** |

    ### Why, and it is not a bug — it is where the backfill aimed

    **600 of the 601 backfill annotations went to APPLIED rulings**: 306
    `disputed_choice`, 267 `manual_correction`, 27 `candidate_choice`, and
    exactly **1** pending. Applied rulings are the ones that never need moving.
    The pending set — the reindexer's entire population — got one row.

    And the forward path has barely run: **3 rulings have ever been recorded
    natively with a snapshot `word_id`** (2 `manual_correction`, 1
    `disputed_choice`) since ids began on 2026-09-06. `0CB`'s "drift is prevented
    now, not just recoverable" is true of the code path and not yet true of the
    data: almost nothing has flowed through it.

    ### Two different answers for the two reindexers

    **`reindex_pending_decisions_after_shift` (24 rulings) is retirable, mostly,
    and cheaply.** `tools/backfill_word_ids.py` re-run today reports **18 rulings
    that can be given an id on an exact, corroborated address** — 7 of them
    pending (klal 35 w54 x2, 39 w13, 63 w40, 69 w187, 69 w337, 210 w130). It has
    not been re-run since 2026-09-06 and the ledger has moved twice since. That
    is free coverage sitting on the floor. The other 17 pending cannot be
    addressed at all — 11 are the drifted set no automatic route will touch.

    **`reindex_flags_after_shift` (290 open, 1,367 total) is NOT retirable, and
    cannot become so as the tools stand.** `backfill_word_ids.RULING_TYPES` is
    `("candidate_choice", "disputed_choice", "manual_correction")` — `klal_flag`
    is not in it, so **no flag has any route to an id except being re-written by
    a reviewer**. `0CC` added ids to the `klal_flag` write path on 2026-09-06 at
    `3f623f9`; no flag has been written since, so coverage is still 0 of 1,367.

    ### What this does to `0BX`

    `0BX`'s collision risk lives in the DECISION reindexer, whose population is
    24 and shrinking, and 7 of those can stop being index-addressed this week.
    So the guard is worth less than it looked, and the larger win is closing the
    coverage hole instead:

    1. **Re-run `backfill_word_ids.py --apply`** — 18 gain ids, 7 pending. Free,
       the tool exists, and it is an annotation writer (Lesson 46-safe).
    2. **Extend `RULING_TYPES` to `klal_flag`** — the only thing that could
       retire `reindex_flags_after_shift` for most of 1,367 rows. Needs care:
       a flag's `word_index` is a body-word index like a ruling's, unlike
       `witness_choice` (a docai token index) and `title_correction` (an index
       into `title.split(' ')`), which are correctly excluded from ids and must
       stay excluded.
    3. Only then decide `0BX`'s refuse-vs-record policy, against whatever
       population is actually left.

    NOT DONE — this is the measurement, and step 2 changes what a tool writes to
    an append-only log, which is a decision, not a tidy-up.

0CH. **[2026-09-07] CLEARED `0CE`'s LOOSE ENDS 4-8. THE DEAD ACCESSOR OVER THE
    LIGATURE CATALOGUE WAS THE SMALL HALF - THE CATALOGUE ITSELF HAS NO READER,
    WHICH CHANGES WHAT PHASE 3 STEP 1 IS.**

    Swept the CLASS before touching the instances, on Lesson 47's axes rather
    than by orphan-hunting. Two axes, both cheap, and the scripts are in the
    scratch dir because the axes are the durable part:

    | axis | found |
    |---|---|
    | argparse flags declared, `args.<dest>` never read | **exactly 2**, both known — no third instance across 103 files |
    | module-level functions referenced only from `tests/` | `flagged_klalim`, `repair_stream`, **and 2 new**: `get_witness_engine` / `set_default_witness_engine` |
    | functions referenced nowhere at all | `typography.get_ligatures`, `build_part1_freq.load_or_build` |

    The two new ones are in `pipeline/second_witness_eval/registry.py` — inside
    the subsystem item `0N` already establishes is off the rebuild path
    entirely. Left alone deliberately: deleting them is part of the decision `0N`
    holds open, not a tidy-up.

    ### THE FINDING: `PRINTER_LIGATURES_AND_GLYPHS` is read by nothing

    `get_ligatures()` was flagged as a dead one-line accessor. It is — but the
    list underneath it has no reader either, in `pipeline/`, `tools/` or
    `tests/`. The five modules that import `typography` all want the PREDICATES
    (`dropped_lamed_explains` and friends), which hardcode the alef-lamed rule in
    code instead of reading it from the catalogue.

    **This changes item `0BU` Phase 3 step 1**, scoped as "extract the ligature
    catalogue (`alef_lamed` ﭏ, `chet_zayin`) from `pipeline/typography.py` into
    `book.json`". Extracting that list moves DEAD DATA into a config file and
    changes no behaviour, because no behaviour depends on it. What is genuinely
    this-book-specific AND load-bearing is the predicates and the 24 corrupt
    forms (still duplicated across `tests/test_corpus_invariants.py` and
    `tools/validate_lexicon_independent.py`). Decide which of the two Phase 3
    means before doing it — the list looks like the seam and is not one. The
    catalogue is kept and re-labelled in place as documentation rather than
    configuration, with that consequence written where the next reader will hit
    it.

    ### `flagged_klalim` was wrong by 50%, measured before deleting

    It filtered on `needs_revisit` alone; the dashboard uses
    `rcount.flag_still_open`, which also accounts for the decisions that ANSWERED
    a flag. Against the live ledger: **153 klalim against the server's 102**, a
    strict over-report (0 klalim in the live answer only) — and its extras
    include klalim above 222, which are not Part 1 at all. Removed.

    `app.js` carried the same wrong belief in a comment that named
    `rd.flagged_klalim()` as what "drives the nav badge and this button's state
    everywhere else". It never did; `api_klalim` builds its own `flagged` set at
    `review_server.py:448`. Corrected — a wrong comment about which function is
    authoritative is how the next reader picks the wrong one.

    ### `repair_stream` — the §3.5 obligation is discharged, just not there

    Removed. The audit trail it existed to return ("a filter that changes what a
    reviewer sees must be able to say exactly what it changed") is produced
    per-RECORD instead: every pipeline candidate carries `docai_reading` and
    `docai_repaired` side by side — measured **282 of 282** such records in
    `review_queue_part1.json`, 35 where the repair changed the reading — so the
    reviewer sees before and after at the position they are ruling on. A
    per-stream trail would still have needed routing somewhere to mean anything
    (Lesson 29). The principle is kept and re-sited, not dropped.

    ### The rest

    `--part` deleted from both tools rather than threaded: they write rulings
    keyed to Part 1 indices, and Parts 2-3 corrections may not be applied at all
    while the gate holds, so a `--part 2` run has nowhere to land.
    `load_or_build` deleted with the "As a library" usage block that documented
    it. `POST /api/decisions/candidate` removed — `app.js` posts every ruling to
    `/api/decisions/disputed`, and the two UI tests that used the alias used it
    for its name; repointed, and the dead route verified 404 against the
    restarted server.

    **Gate 505 -> 503**, the two removals being the tests whose subjects are
    gone; the third was rewritten onto `all_current()`. UI suite: 100 passed,
    1 skipped, 1 failed — the failure is `0CA`, the known 40-50% flake, and it
    reproduced on klal 2 w411 (wanted page 15, got 14).

0CG. **[2026-09-07] RAN THE CLEARING SEQUENCE. 14 RULINGS CLOSED, THE APPLIER
    CONVERGED FROM 4 TO 1, AND THE REBUILD DROPPED EXACTLY THE 4 QUEUE ENTRIES
    IT WAS PREDICTED TO.**

    The sequence `0CF` argued for, run in order, with the ledger snapshotted
    first so every step was diffable.

    ### `close_satisfied_rulings.py --apply` — 14 closed

        klal   1 w85   -> לכו        [unique]        klal  98 w24   -> ע"ד     [unique]
        klal  23 w190  -> משום       [word_id]       klal  98 w61   -> ב"מ     [unique]
        klal  69 w38   -> ואלהיכם    [unique]        klal 146 w43   -> ובאדם   [unique]
        klal  69 w338  -> אלהים      [confirmation]  klal 163 w239  -> למד     [unique]
        klal  88 w149  -> אלעזר      [word_id]       klal 163 w430  -> שכתבו   [unique]
        klal  88 w383  -> אלא        [word_id]       klal 210 w65   -> כקמייתא [confirmation]
        klal  97 w106  -> טהורים     [unique]        klal 210 w138  -> נכתבו   [unique]

    Append-only verified rather than assumed: the first 4,150 rows are
    byte-identical to the pre-run snapshot and the 14 new rows are all
    `apply_event`, actor `pipeline-script via close_satisfied_rulings`.
    `part1.json` untouched. The 4 refusals stand (klal 39 w13, 69 w187, 69 w337,
    210 w130 — a repeated word with no corroborating ink).

    ### The coupling `0CF` predicted, measured

    | | before | after |
    |---|---:|---:|
    | `close_satisfied` closable | 14 | **0 — converged** |
    | applier would promote | 4 | **1** (klal 63 w40) |
    | applier already-promoted | 665 | 668 |
    | applier drift refusals | 11 | 11 — unchanged |
    | `repoint` already-in-corpus | 579 | 593 |
    | `repoint` re-pointable / stale | 0 / 11 | 0 / 11 — unchanged |

    Three of the 14 (klal 23 w190, 88 w149, 88 w383) were the applier's own
    queue: it would have written text the corpus already held. The other 11 were
    never in the applier's set at all — its total stayed 680 across the run —
    which is worth knowing, because the two tools work on different sets and only
    their overlap looks like double work.

    ### The rebuild was REQUIRED, and by a rule the docs do not currently state

    4 queue entries sat at just-closed positions (`current_text_confirmed` at
    klal 23 w190, 97 w106, 98 w24, 98 w61), so the derived queue was stale against
    the ledger with **no `part*.json` edit having happened**. The standing rule is
    "after any edit to a `part*.json` file, run `./rebuild_all.sh`", which does
    not cover this: `settled_by_an_applied_decision` reads the LEDGER, so
    appending an `apply_event` changes the queue's inputs by itself.

    `./rebuild_all.sh --skip-vision`, diffed against a snapshot of all 15 files:

        part1/2/3.json, word_identity.json, review_decisions.jsonl   byte-identical
        candidates_part1.json      286 -> 282   dropped klal 97, 98
        review_queue_part1.json    707 -> 703   dropped (23,190) (97,106) (98,24) (98,61)
        everything else derived                 unchanged

    Removed set == predicted set exactly, nothing added. Gate 505 passed inside
    the rebuild. Dashboard totals moved 930/850 open -> 926/847 across 144 klalim.

    ### What is left, and it is human work

    `DRIFTED-RULINGS-WORKLIST.md` regenerated: **11 rulings**, 2 ink-only /
    4 text-only / 5 neither. Plus klal 63 w40, which the applier will promote on
    a deliberate run. No machine route remains open on any of them.

0CF. **[2026-09-07] COLD-SESSION RE-MEASUREMENT OF `0CE`'s HANDOFF. THREE OF
    ITS NUMBERS DO NOT REPRODUCE, AND ONE OF THEM IS A CLAIM, NOT STALENESS.**

    Nothing in the tree changed between `743f8a6` and this measurement (`git
    status` clean, no apply run), so these are not drift — they are what the
    tools say when run.

    | `0CE` says | measured today | |
    |---|---|---|
    | 7 stranded rulings, "the applier's whole drift list" | the drift list is **11** | the 7 are its `manual_correction` rows; the other 4 are 1 `candidate_choice` (klal 4 w35) and 3 `disputed_choice` (106 w46, 174 w116, 206 w2) |
    | 1 ruling the applier would promote (klal 63 w40) | **4** | klal 23 w190 confirmed-no-op, 63 w40 manual-delete, 88 w149 and 88 w383 manual. Only one word-count-changing decision applies per klal per run, so 63 w40 still needs its own rebuild-then-rerun cycle |
    | `close_satisfied_rulings.py` has 11 more to close | **14** (3 by `word_id`, 2 by confirmation, 9 unique), 4 refused for want of ink corroboration | |

    `repoint_stale_decisions.py` reproduces exactly: **0 re-pointable, 11 stale
    and left alone, 579 already-in-corpus untouched** (`0CE` said 581 — the
    difference is the two rows `close_satisfied` has since settled, not a
    disagreement).

    **`DRIFTED-RULINGS-WORKLIST.md` was 17 hours stale** — generated 14:23 on
    2026-09-06, before the 43 rows the 00:13 commit recorded, so it listed 26
    rulings including 11 in a "SETTLED, no judgement needed" section that the
    clearing tools have since taken. Regenerated: 11 rulings, bucketed 2 ink-only
    / 4 text-only / 5 neither. The file carries its own "regenerate after any
    apply" instruction and the ledger moved without an apply, which is the case
    that instruction does not cover.

    **Gate re-measured, `pytest --collect-only`:** `test_corpus_invariants.py`
    60 + `test_pipeline_logic.py` 445 = **505 gated, all passing**;
    `test_review_server.py` 102, `test_fixture_corpus.py` 14,
    `test_witness_engine.py` 5 — **626 total**. `START_HERE.md` still says
    56/388/444 and 562, which is the staleness that file warns about in its own
    text (Lesson 37).

    **`0CE` item 3's "both change what the other sees" is wrong of DRY RUNS, and
    right only of `--apply`.** `close_satisfied_rulings.py` returns before its
    `append_decision` loop (`:177`) and writes nothing whatever on a dry run;
    `repoint_stale_decisions.py` writes `stale_decision_repoint_report.json`
    (`:245`, before the `--apply` guard at `:251`), and the only reference to that
    file anywhere in the repo is its own `--out` default, so no tool reads it.
    Two dry runs in a row, in either order, return identical answers. The real
    coupling is one-directional and goes through the ledger: `close_satisfied
    --apply` appends `apply_event` rows, `repoint` skips `rd.applied_decision_ids()`
    at `:196` (the Lesson 46 guard), so closing a ruling shrinks repoint's input
    set. Re-measure after an `--apply`, not after a dry run.

    Loose ends 4–8 of `0CE` all reproduce as written: `--part` is declared and
    `args.part` is never read in either `close_satisfied_rulings.py:142` or
    `repoint_stale_decisions.py:164`; `flagged_klalim`, `repair_stream`,
    `typography.get_ligatures`, `build_part1_freq.load_or_build` and
    `POST /api/decisions/candidate` are each referenced only from `tests/`.

0CE. **[2026-09-07] LOOSE ENDS AS OF THE SESSION CLOSE — what a cold session
    should pick up, in order.**

    **1. Seven stranded rulings, and they need a human against the scan.** klal
    36 w108, 39 w251, 74 w417/442/443, 209 w16/w17. No stable id, no bbox
    corroboration, no text match; the words they name are gone from the corpus
    (klal 39 w251 named `דבכולהן`, that position now reads `היכי`). They are the
    applier's whole drift list, they now show as a red banner on their klal, and
    **no tool should re-point them** — every automatic route has already declined.

    **2. One ruling the applier would promote, not yet applied.** klal 63 w40,
    a manual delete of `סד`, which reads as a folio marker in `י"ד רסי' כ"א סד`.
    `apply_reviewer_decisions.py --dry-run` shows it; promoting is a deliberate
    step and has been left to the reviewer.

    **3. Two clearing runs still available.** `close_satisfied_rulings.py` has
    11 more it can close and `repoint_stale_decisions.py` now reports 0
    re-pointable with 581 left alone as already-in-corpus. Re-run the dry runs
    first — both change what the other sees.

    **4. `--part N` is a lie on two tools.** `close_satisfied_rulings.py:140` and
    `repoint_stale_decisions.py:161` declare it and then hardcode
    `load_part1*()`, so `--part 2` silently operates on Part 1. Either thread it
    or delete the flag; a flag that accepts a value and ignores it is worse than
    no flag.

    **5. `flagged_klalim()` is a wrong answer with no caller.** It filters on
    `needs_revisit` alone while the dashboard uses `rcount.flag_still_open`,
    which accounts for decisions that answered the flag. Two answers to one
    question and the unused one is the wrong one (Lesson 13). Delete it.

    **6. `docai_filter.repair_stream()` unused**, so the audit trail it exists to
    return — "a filter that changes what a reviewer sees must be able to say
    exactly what it changed" (§3.5) — is never produced. Production calls
    `repair_word` per word and discards what changed. Either wire it or drop the
    §3.5 claim.

    **7. The synthetic-render path still addresses by INDEX.** `review_server.py`
    renders a `manual_correction` only when `_word_matches(words, word_index,
    original_word)` at the RECORDED index. The stable id rescues 0 of the 239
    suppressed today, and that is not an id failure — applying a ruling replaces
    the word it named, so `original_word` is gone at the correct address too.
    Worth a deliberate decision about what "still valid" should mean here now
    that ids exist; do not assume the id fixes it.

    **8. Dead accessors and a dead route.** `typography.get_ligatures()`,
    `build_part1_freq.load_or_build()`, and the `POST /api/decisions/candidate`
    alias nothing calls.

    **Still open from before today:** `0CA` the scroll defect (word click undone
    ~50%, page override lands at 14ms, `_showPageGen` hypothesis, two attempted
    fixes both reverted); `0BX` the reindex collision guard (klal 210 has three
    rulings resolving to one word — the id made them all name it correctly, which
    is why the guard is still wanted); Phase 3 steps 1–3; standing corpus items
    16, 20, 0N, 3, 4.

0CD. **[2026-09-07] RENAME PASS, THE REBUILD, AND THE MARKERS. ALSO: A
    RECOMMENDED TOOL MANUFACTURED 13 FALSE DRIFT ROWS.**

    ### The one that went wrong

    `tools/repoint_stale_decisions.py --apply` was recommended to the reviewer
    without first checking it for the guard its own sibling has. It re-points ALREADY-APPLIED
    rulings, and a re-pointed copy of an applied ruling is an unapplied row
    carrying a `chosen_text` the corpus already holds. **24 copies written, 23 of
    them superseding applied rulings, 13 straight into the applier's drift
    bucket** - which grew 22 -> 24 while the 11 genuine refusals sat unchanged.
    Fixed at the cause (the tool now skips `applied_decision_ids()`, reporting
    581 left alone) and at the effect (`restates_an_applied_ruling()` settles the
    23 already written). Applier drift 24 -> 11, already-applied 650 -> 667. See
    Lesson 46.

    ### A regression shipped the day before, found today

    The 601-row backfill broke the decision-history panel for **299 words**.
    `history_for_word_id` selected on `candidate_snapshot.word_id`; annotations
    carry one and the rulings they annotate do not, so it matched the ANNOTATION
    and missed the RULING - wrong row returned and right row omitted, from one
    line. Every one of the 299 was a word a human had ruled on, and the panel
    showed bookkeeping in its place. Annotations are now excluded as a CLASS
    (`ANNOTATION_TYPES`), and each row reports `word_id_source: recorded|backfill`.

    ### The rename pass

    Three things were called "corrections": the machine's proposals, a human's
    ruling, and the corrected text. Full mapping and the reasoning are in
    `START_HERE.md`'s new "The three authored files" section and Lesson 48.

        corrections_candidates_part1.json -> candidates_part1.json
        corrections_verified_part1.json   -> candidates_verified_part1.json
        corrections_part{1,2,3}.json      -> review_queue_part{1,2,3}.json
        original_word   (candidate files) -> docai_reading
        corrected_word  (candidate files) -> stored_text
        load_corrections()                -> load_review_queue()
        api_klal()'s "corrections" key    -> "queue"

    **The ledger was deliberately not touched** - filename, `decision_type`
    values, snapshot fields - and a new invariant pins that line. Archives
    (`PROJECT-STATUS-HISTORY.md`, dated audits) keep the old names on purpose:
    rewriting a filename inside a dated entry makes it claim something that was
    not true then.

    ### The rebuild, dry-run first

    `./rebuild_all.sh --skip-vision` into an isolated `$SEFER_CORPUS_ROOT` before
    touching the real tree. It predicted the outcome exactly: two files, one
    record - `candidates_part1.json` 287 -> 286, `review_queue_part1.json` 708 ->
    707, removing klal 66 w17 (`delete`, `'סו אין'`). Everything else identical,
    `part*.json` and the ledger and the sidecar included. The real run matched.

    **Three false alarms in the dry run, all missing inputs rather than
    predictions** - consensus disputes collapsing to 2 bytes (no witness
    baselines), the ranked queue to 4 bytes, and all 75 collation rows differing
    (no `sefaria_reference_corpus/word_freq.json`, so `expansion_attested` went
    null, which that code returns deliberately rather than a false zero). Worth
    keeping as method: an isolated-root dry run needs `tools/` and the reference
    corpora symlinked in, or it lies in the alarming direction.

    ### Markers for the work that was invisible

    `api_klal` suppresses a `manual_correction` whose recorded index no longer
    holds its word - correct, and a bare `continue`, so the klal page said nothing
    at all. These rulings have no queue entry either, by construction. Now a
    klal-level banner names what was ruled, what was chosen, and what sits at that
    index now. NOT drawn on a word: the position is precisely what is untrusted.

    239 of 283 manual corrections are suppressed; 220 are applied and right to be
    silent. **7 remain across Part 1** - klal 36 w108, 39 w251, 74 w417/442/443,
    209 w16/w17 - and they are exactly the applier's drift list. My first version
    said 19, because it excluded only `applied_decision_ids` and listed 12 settled
    copies as stuck work while the corpus visibly held their text.

    ### Also landed

    `$SEFER_REVIEWER` wired into all seven write handlers (Lesson 47); stable ids
    swept into `klal_flag` and `punctuation_choice` writes, and deliberately NOT
    into `witness_choice`/`title_correction`, which address different spaces;
    `word_id_of()` extracted so the two clearing tools stopped being blind to the
    601 backfills (`repoint` 0 -> 53 re-pointable, `close_satisfied` 0 -> 18).

    Gate 625. 17 commits, pushed.

0CC. **[2026-09-07] A SWEEP FOR HALF-FINISHED FEATURES. FOUND A REGRESSION
    SHIPPED HOURS EARLIER, AN ENV VAR THAT DID NOTHING, AND THE ID MISSING FROM
    FOUR OF SEVEN WRITE PATHS.**

    Reviewer: "you implemented the id? will this completely stop the drifting?"
    then, after `0CB`, "I asked you earlier for unimplemented features. look for
    more." The earlier sweep had reported none. It was wrong, and the reason it
    was wrong is worth more than the findings: it looked for functions NOTHING
    calls. Every gap below is a function something calls - a test, or one caller
    of three. **An orphan sweep cannot see a feature that is fully built, fully
    tested, and wired to nothing.**

    ### 1. The history panel, broken by the previous day's backfill

    `history_for_word_id` selects rows on `candidate_snapshot.word_id`. The 601
    annotations each carry one; the rulings they annotate carry none, by design.
    So it matched the ANNOTATION and missed the ruling - **wrong row returned and
    right row omitted, from one line**. Measured on the live ledger: **299 words**
    whose panel returned basis `word_id` and a single `word_id_backfill` row,
    which `api_decision_history` duly served in place of the rulings the index
    path had been showing. Every one was a word a human had ruled on.

    Fixed with the order `resolve_word_index` already used, and annotations
    excluded as a CLASS (`ANNOTATION_TYPES`) rather than by name, since any future
    type that records something ABOUT a ruling will carry an id the same way. Each
    row now says `word_id_source: recorded|backfill` - which also gives the
    annotations' `basis` evidence its first reader.

    ### 2. `$SEFER_REVIEWER` was decorative

    `reviewers.json` has said "set $SEFER_REVIEWER to the id of whoever is
    reviewing" since 2026-09-04. `identity.resolve_actor()`, the only thing that
    reads it, had **no production caller**. All seven write handlers passed
    neither `actor` nor `reviewer`, so `append_decision`'s default stamped the
    literal `"local"` on every one of the 902 rulings recorded since. Setting the
    variable did nothing, silently, while the docs said it worked.

    The whole layer was built and unreachable: roster, the id/email split that
    keeps a permanent id in an append-only log while emails change, the write-time
    snapshot, the `unregistered` marking. One call site was missing. Unset still
    writes plain `local`, so nothing about an existing setup changes and no
    identity is invented for a reviewer who asserted none. Announced at startup,
    because an asserted identity that is wrong is only discoverable afterwards in
    a log that cannot be edited.

    ### 3. The id was in three write paths of seven

    | path | id? | why |
    |---|---|---|
    | `disputed_choice`, `manual_correction`, `candidate_choice` | yes | already |
    | `klal_flag` (word-level) | **added** | 1,367 rows; `reindex_flags_after_shift` exists BECAUSE these rot |
    | `punctuation_choice` | **added** | 21 rows; `apply_punctuation_decisions` changes word counts |
    | `witness_choice` | no, correctly | `word_index` is a `docai_token_index` |
    | `title_correction` | no, correctly | index into `title.split(' ')` |

    All 26 records written since ids began were flags, none carrying an id - **new
    drift being created after the fix that was supposed to have ended it**. `0CB`'s
    "drift is prevented going forward" was true for rulings and false for flags.
    The two exclusions are pinned by a test, because "attach it everywhere" is the
    natural next edit and would name a real word and the wrong one.

    ### 4. The clearing tools could not see the backfill

    `repoint_stale_decisions.py` and `close_satisfied_rulings.py` both read
    `candidate_snapshot.word_id` directly - so the two tools whose whole job is
    unsticking rulings were blind to all 601 addresses that had just been
    recovered for them. `review_decisions.word_id_of()` is now the one place that
    knows an id lives in two shapes, and all three readers use it.

        repoint_stale_decisions   0 -> 53 re-pointable (all by stable id)
        close_satisfied_rulings   0 -> 18 already satisfied by the corpus

    Neither applied - promoting is a separate deliberate step.

    ### Smaller, not acted on

    - `tools/close_satisfied_rulings.py` and `tools/repoint_stale_decisions.py`
      each declare `--part N` and then hardcode `load_part1*()`. **`--part 2`
      silently operates on Part 1.**
    - `review_decisions.flagged_klalim()` - a naive `needs_revisit` filter with no
      caller, while the dashboard uses `rcount.flag_still_open`, which accounts for
      decisions that answered the flag. Two answers to one question, and the
      unused one is the wrong one (Lesson 13).
    - `docai_filter.repair_stream()` unused, so the audit trail it exists to
      return - "a filter that changes what a reviewer sees must be able to say
      exactly what it changed" (§3.5) - is never produced. Production calls
      `repair_word` per word and discards what changed.
    - Dead one-line accessors: `typography.get_ligatures()`,
      `build_part1_freq.load_or_build()`. Alias route `POST
      /api/decisions/candidate` that nothing calls.

    ### What to sweep with next time

    Orphan-hunting is the weakest of these. What actually found things: functions
    referenced ONLY by tests; env vars documented but read nowhere; declared CLI
    flags never read; ledger fields written but never consumed; and comparing each
    writer of a record type against its siblings. Scripts for all five are
    disposable, but the axes are not.

0CB. **[2026-09-06] THE APPLIER NOW ADDRESSES WORDS BY ID, AND 601 EXISTING
    RULINGS WERE GIVEN ONE. DRIFT IS PREVENTED NOW, NOT JUST RECOVERABLE.**

    Reviewer: "i thought we modified the way indexing works to avoid drift going
    forward". It had not been. **What existed was a RECOVERY layer, not an
    ADDRESSING one**, and the earlier entries oversold it. `all_current()` keyed
    on `(klal_id, word_index)`; all three apply loops took the position off that
    KEY; and the applier's only use of `word_identity` was to reconcile ids AFTER
    it wrote. It never read an id to decide WHERE to write. So the old sequence
    was intact: apply a word-count change, every later index shifts, rulings
    drift, the reindexer moves them, collisions become possible.

    ### One seam, not twenty-six edits

    `word_index` is a single local rebound through each apply loop, so the
    position is now resolved ONCE per loop by `resolved_position()` and every one
    of the 26 downstream uses - the live-entry lookup, the text mutation, the
    apply_event, the reporting - follows automatically.

    It is deliberately STRICTER than `review_decisions.resolve_word_index`: it
    takes only `word_id` (the sidecar knows where the word is) and `index` (the
    recorded index still holds its word). It refuses `retired` outright, and it
    does NOT act on `unique` or `occurrence` - that function's own docstring
    calls those a hint for a human re-point and never an authority, and this is
    the corpus mutator.

    **Inert until ids exist, which is what made it landable mid-flight.** With no
    ruling carrying an id the dry run was byte-identical: 0 applied, 26 skipped,
    gate green. A mutation disabling the id branch fails the two new tests.

    Two drift checks had to move with it, and this was the subtle part: both
    compared against the RECORDED index, which is exactly what an id-resolved
    ruling has moved away from. `snapshot_still_matches_corpus` takes the
    resolved position, and `snapshot_matches` drops `word_index` from its key
    tuple when the id resolved it - narrower than it sounds, since the
    identity-bearing fields are still compared. What is dropped is the address,
    not the evidence.

    The title loop is deliberately NOT converted: title indices are a different
    address space (`title.split(' ')`), and the sidecar indexes body words.

    **One ordering bug in the first version, found by writing the test for it.**
    The body loop fetched its `review_queue_part1.json` entry BEFORE resolving the
    position - so for exactly the rulings the id rescues, it drift-checked against
    the entry belonging to whatever word now sits at the stale index and refused a
    correct ruling as drift. The lookup moved below the resolution. The comment
    claiming "everything below reads this local" had been false when written,
    which is the tell (Lesson 29's shape: a claim nobody checked).

    `resolve_word_index`'s backfill lookup is INJECTABLE for the same reason
    `id_state` is, and was not at first: it reached for the default ledger while
    its caller worked on another, so a test that wrote a backfill to its own log
    watched the function answer from production. Batch callers now read it once
    per run rather than once per ruling.

    ### The backfill: 601 of 667

    `tools/backfill_word_ids.py`. Time-sensitive, which is the argument for
    running it now rather than later: most pre-id rulings still resolve today,
    and each apply makes a few more unresolvable. Backfilling freezes an identity
    while it is still derivable.

    | resolves as | before | after |
    |---|---:|---:|
    | `word_id` | 0 | **601** |
    | index / occurrence / unique | 52 | 3 |
    | unresolvable | 543 | **63** |

    **It writes an ANNOTATION, not a superseding copy, and the difference was
    MEASURED.** 582 of the 601 are already APPLIED. A superseding copy takes a new
    decision id, so it falls out of `applied_decision_ids()` and those 582 stop
    reading as settled. Built that ledger and ran the applier against it: it
    reports **226 to apply** - 47 manual re-writes, 179 no-op re-confirmations -
    where today it reports 4, and the drift worklist goes **22 -> 380**. A
    `word_id_backfill` row carries no `chosen_text` and no opcode, so no apply
    path can pick it up, and a corpus invariant now holds that shape for all 601.

    Evidence per annotation, and three sources only - the resolvers that already
    exist, never a private copy: the ruling's own address still resolving; for an
    APPLIED ruling, the text it CHOSE still sitting at its recorded index (which
    is why `drift_recovery.word_identities_of(applied=True)` exists); or
    `drift_recovery.recover_klal`'s shift, which must be unambiguous AND
    corroborated. **66 refused** - reported, never guessed at. Every row records
    `word_id_source: "backfill"` and its basis, so an inferred id can always be
    told from one recorded at ruling time.

    ### What it unblocked, NOT APPLIED

    The applier's refusals drop 26 -> 22, and it would now apply 4: klal 63 w40
    (a real deletion of `סד`, which reads as a folio marker in
    `י"ד רסי' כ"א סד`) and three identical no-op confirmations at klal 210 w65.
    **Left for the reviewer** - promoting a ruling into the corpus is a separate
    deliberate step and always has been.

    Worth noting from that list: three rulings now resolve to ONE word (klal 210
    w66/w67/w68 -> w65). The id does not stop several rulings naming the same
    word; it makes them all name it CORRECTLY, which is the right outcome and
    also why `0BX`'s collision guard is still worth having.

    Gate 484. No corpus text changed.

0CA. **[2026-09-06] A WORD CLICK'S PAGE NAVIGATION IS UNDONE ~50% OF THE TIME.
    OPEN, WITH THE MECHANISM NARROWED BUT NOT FOUND. (This entry's first version
    also claimed 11 unreachable disputes - a false alarm, retracted below.)**

    ### The symptom

    Clicking a word that sits on a klal's CONTINUATION page shows that page, and
    then the scan pane silently reverts to the klal's START page. A reviewer
    checking a word against the ink is shown the wrong ink, about half the time,
    with nothing on screen saying why.

    `test_a_word_click_survives_the_scroll_that_follows_it` catches it. **It is
    not a flaky test - it is a flaky FEATURE**, and it has been recorded as a
    known flake ("roughly 1 run in 8") since 2026-09-05, which undersells it.

    ### How to reproduce, in one command

        ./venv/bin/python -m pytest tests/test_review_server.py -q \
            -k word_click_survives_the_scroll

    Run it 8-12 times. Measured 2026-09-06 across four separate batches:
    5/8, 3/6, 5/12 and 2/8 failures - call it **40-50%**. A single green run means
    nothing here; anything under ~10 runs cannot tell a fix from luck. Measured as
    a control in a clean worktree at `5fc3077`, so it is not caused by any of that
    day's work.

    ### What the evidence says

    A `MutationObserver` on `#page-img` during a failing run:

        t=1541  src=page_15.png     <- the click's correct navigation
        t=1555  src=page_14.png     <- undone, FOURTEEN MILLISECONDS LATER

    That single number rules out the entire timing story this entry used to
    carry. The override is effectively immediate, so **nothing about how long the
    observer is suppressed can be the mechanism.**

    ### Ruled out, each by a measurement rather than an argument

    | hypothesis | verdict |
    |---|---|
    | CPU load / a slow machine | NO - 3/3 passed under four busy cores |
    | the shared module-scoped server, state from earlier tests | NO - fails in isolation too |
    | the 900ms suppression window lapsing mid-scroll | **NO - the override lands at 14ms** |
    | reuse `releaseObserverWhenScrollSettles()` | MADE IT WORSE, 10 failures in 10: it re-seats the block for `lastActiveKlalId` before releasing, which is right for a klal jump and is exactly "show the klal's page" |
    | hold suppression until `scrollTop` stops (`whenScrollSettles`) | NO EFFECT - 7 passed / 5 failed, same as baseline |

    Both attempted fixes are REVERTED. `app.js` is unchanged from `5fc3077` on
    this path; do not go looking for a half-applied fix.

    ### The live hypothesis, and where to look

    14ms says two `showPage()` calls are in flight and the wrong one resolves
    last: one for the KLAL (page 14) from the navigation, one for the WORD
    (page 15) from the click. `showPage` is async and already carries a
    `_showPageGen` generation guard for precisely this - grep for "superseded
    while awaiting" - so the question is **which path writes `#page-img.src`
    without consulting that guard**, or which one bumps the generation and then
    writes anyway.

    Start by logging `_showPageGen` at entry and at the write in `showPage`,
    along with the caller, and run the reproduction until it fails. This is an
    ORDERING bug; do not adjust any timing.

    ### Why it is handed over rather than attempted again

    Two fixes built on a mechanism that turned out to be wrong. Lesson 31: a
    heuristic retuned twice is asking to be handed back, and the third attempt
    should start from the 14ms and the generation guard, not from another guess
    about scrolling.

    ### RETRACTED: the 11 "unreachable" disputes are all reachable

    **This entry originally reported 11 disputes no reviewer could get to. That
    was wrong, and both halves of it were wrong.** Corrected the same day, before
    anything was built on it.

    What is still true and was worth measuring: all **453** stage-4a consensus
    disputes reach `review_queue_part1.json`, and the API serves **929** items.
    Nothing is lost between synthesis and the server.

    What was wrong is the rendering claim, and the error was method, not
    arithmetic. **The frontend's merge rule was reimplemented in Python instead of
    reading it** - `byIndex[c.word_index] = c` over every entry, plus the
    assumption that an index with no word span cannot be drawn. `renderKlalBody`
    does neither of those things:

    * it EXCLUDES `delete` opcodes from `byIndex` (`app.js:1520`), so an
      insertion proposal never competes with a word entry for a slot. The klal 68
      w29 "collision" does not exist - both render, one as a word and one as a
      gap marker.
    * it has a dedicated block AFTER the word loop (`app.js:1778`) that draws
      every `gapsBefore[idx]` with `idx >= words.length`. It was added 2026-08-25
      for exactly this reviewer report (klal 219) and its own comment names the
      same klalim it "found": 84, 88, 106, 114, 138, 159, 164, 175, 193, 211.

    Verified in a browser rather than by reading, since reading is what produced
    the error: `test_an_append_position_insertion_proposal_is_reachable` opens
    each of the ten klalim and asserts a `.flag-gap` marker exists for every
    append-position proposal. It passes. The test is KEPT - the property was
    never pinned, which is why a wrong claim about it survived long enough to be
    written down.

    The nav counts are therefore right too: klal 211's four corrections are four
    reachable corrections.

    THE LESSON, which is the only thing here worth carrying forward: this is
    Lesson 33's shape one level over. That lesson says check a tool's STATE, not
    its printout; this was checking a MODEL of the renderer rather than the
    renderer. A reimplementation of someone else's rule agrees with it right up
    until the case you were investigating, which is the case it was written for.


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
    functions added that session** - `word_identity.seed()` and
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

    ### A precedence bug introduced here, and caught by the tests

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
       sweep's two hits were false positives (both read `review_queue_part1.json`
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

20. **CLOSED 2026-09-07 — THE DAMAGE IS GONE. Re-measured before closing:
    **zero** occurrences of `Digitized`/`Google` in `part1/2/3.json`, and **no
    Latin word of 3 or more characters anywhere in the corpus at all**. All 12
    named klalim carry normal-length Hebrew (250: 238 words, 290: 316, 616: 991,
    665: 440), so this is a repair rather than a revert to placeholder. The item
    had been reading as an open corpus defect while the corpus was clean; found
    while sweeping for unsurfaced data issues (item `0CV`). The original entry
    is preserved below because the MECHANISM it documents is still the
    instructive part - `strip_page_furniture()` keys on `hebrew_letters_only()`,
    which maps every Latin token to `""`, so a Latin watermark is invisible to
    the cleaner that is supposed to remove it, and the gated test missed it
    because its regex only matches the HEBREW running header.**

    <details><summary>Original entry, 2026-08-26</summary>

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


    </details>

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
