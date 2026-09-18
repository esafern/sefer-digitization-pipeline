# Project Status — current state

## TL;DR

_Current state only. Every claim here is measured, not remembered; the dated
evidence for each is in `PROJECT-STATUS-HISTORY.md`._

> **Picking up after 2026-09-15? Read item `0GQ` first** - the handoff for
> Sefer HaShorashim: its state (the ledger is empty, so the corpus can still be
> wiped; the witness apply path is built and off) and the open work in order.
>
> **Then read `0GV`-`0GZ`, from the evening of 2026-09-15, before the Sefaria
> meeting of 2026-09-16.**
> * A demo copy of the corpus root runs on :8422: `~/work/hashorashim-demo`,
>   an APFS clone with no `.git` and its own ledger, holding 4 applied witness
>   rulings in entry 1. The real root on :8421 still has no rulings.
> * Demo rulings are applied with `apply_reviewer_decisions.py
>   --apply-witness-choices`, then `build_klalim_demo_dataset.py`. NEVER the
>   full rebuild, which re-derives the rows the green boxes hang on (`0GW`).
> * Scheduled for after the meeting: the verse-check fix (`0GZ`).
> * Still open from that evening:
>   - the fused-footnote vision pass, sample first (`0GZ`);
>   - witness rulings in `audit_applied_decisions.py` (`0GL`, `0GW`);
>   - footnote and heading demarcation in the export, which waits on Sefaria
>     naming its footnote tag (`0GV`).
>
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
> 4. ~~`0CA`~~ — **FIXED 2026-09-08, see `0DG`.** A nav jump left a
>    requestAnimationFrame loop running that re-seated its own klal 17ms after a
>    word click. 0 failures in 28 runs against a 5-in-10 baseline. The same work
>    found and fixed a second, pre-existing full-suite failure caused by shared
>    ledger state between tests.
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

0GR. **[2026-09-15, reviewer: "the headers in heb and eng - font can be a bit
    bigger, and more white space between words - there is space to grow a
    bit"] DONE.** The three pane-header bars, both books.
    * Hebrew slots 13.5 -> 16px, Latin slots 11.5 -> 13.5px, `word-spacing:
      0.2em` inside a slot, and the gap between slots 12 -> 16px
      (`.ph-mid`, `review_frontend/app.css`).
    * **Found on the way: a second copy of the Hebrew size (Lesson 13, THE
      SECOND COPY OF THE TRUTH).** `#klal-indicator` carried its own
      `font-size: 13.5px`, and an id rule outranks the slot rule, so the scan
      pane's Hebrew stayed small while the other two bars grew.
      `test_the_pane_headers_are_centred_and_their_slots_are_peers` caught it
      before it shipped. The line is removed. A sweep of `app.css` and
      `app.js` found no other rule or script setting a header slot's size.
    * `test_the_scan_header_actually_separates_its_two_scripts` now asks for
      at least 14px, derived from the new 16px gap as its old 10 was from 12.
    * Measured live, after a restart of both dashboards: nothing clips at 1700
      or 1280px on either book. **At a 1000px window, HaShorashim's text bar
      shortens `Shoresh #1` with an ellipsis** (it needs 443px and has 388).
      That is the designed yield (the English reference gives way first),
      but it did not happen before this change. 1280px is the narrowest
      width the layout test targets. Full browser suite: 113 passed,
      1 skipped.
    * **The "Master text" box (reviewer: "master text selection box needs
      whitespace separation").** `#text-view` was pinned out of the flow at
      `left: 8px`, and the centred group ignored it. Measured on :8421 it was
      14px clear at a 1700px window and overlapped the Hebrew title by 41px at
      1440 and 75px at 1280. **That overlap is older than today:** at 1280 it
      was about 30px before the type grew. No test could see it, because the
      shipped corpus declares no comparison texts and the box stays hidden
      (Lesson 25, A SIGNAL THAT CANNOT DISAGREE).
    * Now `#text-header` is a `1fr auto 1fr` grid with a 24px column gap. The
      group centres on the pane while the box's column has room, and moves
      right instead of under the box when it has not. Measured live: 24px
      clear at 1700, 1440, 1280 and 1100.
      `test_the_text_view_box_never_runs_into_the_centred_header` shows the
      box by hand and fails under the old rule (header text 1px from the box
      at 1280). Full browser suite: 114 passed, 1 skipped.
    * ~~OPEN~~ **FIXED 2026-09-15 (reviewer: "yes eng title give way").** At
      1440px and below on HaShorashim the text bar was 75px short, and the
      English reference, which yielded first, shrank to nothing at 1280: an
      empty slot between two dividers. **The English book title now gives
      way, and the reference does not shrink while a title shares its bar**
      (`.ph-ref.ph-en:has(~ .ph-title.ph-en:not(:empty)) { flex-shrink: 0 }`).
      Read off the pixels on :8421, `/entry/32`:
      - at 1440, `Sefer Ha...` with `Shoresh #32` whole;
      - at 1280, the title is down to `S` and the reference is whole;
      - at 1100, the title is gone and the reference is whole at the edge.
      `test_the_english_title_gives_way_before_the_reference` puts
      HaShorashim's strings into the slots by hand, because Yad Malachi's
      names fit and would pass whatever the rule said.
      - ~~OPEN~~ **MOOT THE SAME DAY: the reference left this bar (`0GT`).**
        What remains is guarded by
        `test_the_text_bar_fits_a_long_title_beside_the_which_text_box`
        (HaShorashim's titles beside the box at 1280, no slot losing letters).
        Narrower widths were not re-measured. The entry as written: Below
        about 1090px on HaShorashim, with the which-text box shown, the
        reference runs past the bar's edge and is clipped with no ellipsis:
        2px at 1080, 36px at 1000 (`#32` gone). Before today the box covered
        the Hebrew title at those widths instead. 1280px is the narrowest
        width the layout test targets. A fix would hide the English title
        outright below some bar width (a container query), so the reference
        could shrink with an ellipsis again. That threshold is per book, and
        it is the reviewer's call.
      - **Three probes in a row reported this bar wrong, and the pixels
        caught each one (Lessons 43, THE PROBE THAT CANNOT SEE, and 45,
        PIXELS, NOT THE DOM).**
        1. The first rule was `flex-shrink: 1000` against 1. Its test compared
           integer `clientWidth` and `scrollWidth` with 1px of slack, and
           passed. The screen read `Shoresh #...`: the reference was about
           0.08px short, and an ellipsis fires on any overflow. This file said
           "`Shoresh #32` is whole (102 of 102px)" until the screenshot was
           read.
        2. After the fix, a probe on the `.ph-mid` box said everything fit at
           1000px. The slots that cannot shrink spill out of that box, so it
           never saw them.
        3. A text-Range sweep then said 78px past the edge at 1280, where the
           screenshot shows all of it. A Range covers text that the slot's own
           `overflow: hidden` clips.
        The numbers above come from a fourth probe (the reference's text
        Range against the bar's edge). It was accepted only because it agrees
        with the screenshots at 1280, 1100 and 1000.
      - The test now measures fractional overflow from the text itself. On
        the old rule it fails its real assertion (the reference 0.05px
        short). Its precondition was blind once too (Lesson 42): it first
        asked whether the title shrank, which is the thing under test.

0IH. **[2026-09-18, reviewer: "add them. other lessons or rules not captured?"] SEVEN STANDING RULES
    MOVED FROM CLAUDE'S MEMORY INTO START_HERE; THREE STALE FACTS CORRECTED; THE HEBREW CHECK MADE
    TRUSTWORTHY.** See `DOCS-HISTORY.md` for the list. Nothing in START_HERE had said any of them,
    so a Gemini session or a fresh clone was bound by none.
    * `tools/check_mixed_direction.py`, three false positives or misses found by running it on
      START_HERE itself and fixed, each with a test: a QUOTED span with punctuation inside (a
      title-page quotation with an ellipsis, an initial in a printer's name) is one piece; a
      double quote counts only at a word boundary, because inside a word it is gershayim and
      pairing one abbreviation's mark with the next would silently mask the text between; and the
      check reads by PARAGRAPH, since Markdown wraps a quotation across lines. START_HERE and the
      four live drafts check clean; the sent citation email still shows its 15 true positives.
      `PROJECT-STATUS.md` shows 222 - lists of backticked words in notes read in a terminal, which
      does no bidi reordering, so not a target.
    * **Candidate lessons, proposed and NOT added** (numbering is the reviewer's to grant): see the
      reply of the same day.

0IG. **[2026-09-18, from the reviewer's Windows screenshot] THE "WHOLE-FILE DIFF" AFTER THE WINDOWS
    APPLY WAS NOT LINE ENDINGS: SEFER HASHORASHIM'S part1.json WAS WRITTEN IN A FORMAT NO OTHER CORPUS
    WRITER USES.**
    * The screenshot's `git diff --stat` before the discard: `part1.json | 11864`, 5,936 insertions
      and 5,934 deletions - every line changed, line count unchanged. Measured here: the committed
      file matches `json.dumps(indent=1, ensure_ascii=False)` exactly; `cio.save_part1` writes
      `indent=2`. So the first apply re-indented all 5,934 lines. `0IB`/`0HX` had me reading it as
      CRLF; `git ls-files --eol` showing `i/lf w/lf` for part1.json was the clue I did not follow.
    * **The outlier writer:** `tools/build_root_corpus.py:738`,
      `json.dump(records, fh, ensure_ascii=False, indent=1)` - the book builder, which is not in
      START_HERE's authored-file table and so never went through `save_part1`, whose own docstring
      calls it "the ONE serialization ... a writer that disagreed would rewrite the whole file as a
      diff on every apply". Lesson 13, THE SECOND COPY OF THE TRUTH. Now `cio.save_part1(records,
      path=args.out)`. Swept: the other corpus writers (the applier, the punctuation applier, the
      placeholder reconstructor) already use it; the other hits for `part1.json` only read it.
      Guard `test_every_tool_that_writes_a_corpus_file_uses_its_one_serializer` fails on the old
      builder, checked.
    * **Not done, the reviewer's call:** the committed HaShorashim `part1.json` is still `indent=1`,
      so the first real apply there will still show a whole-file diff. A one-time re-serialization
      through `save_part1` is content-identical (verifiable by comparing the parsed JSON) and makes
      every later apply a one-line diff. It records no decision.
    * The Windows box is back in step: `git restore .` then `git pull` fast-forwarded
      `0ac0d57..54a5372`, bringing the empty ledger and the `0IE` rebuild.

0IF. **[2026-09-18, reviewer: "hold on - we are not recording any decisions for sho. yet - we need
    to keep opts open. separately: reverse hebrew mixed with english leads to confused sentences
    ... record this so it doesn't keep happening"] THE TWO TEST RULINGS REVERTED; A CHECK FOR
    HEBREW THAT RENDERS BACKWARDS.**
    * **Sefer HaShorashim takes no rulings yet.** The two witness rulings recorded on the Windows
      box on 2026-09-17 had been committed and pushed to the private corpus repo (`0ac0d57`, 2
      lines, nothing else). Reverted in `54a5372`: the ledger is 0 bytes again and the rows stay
      recoverable from history. My own advice was the problem - I had told the reviewer to commit
      and push both the rulings and the apply, against `0GQ`'s standing state (ledger empty, corpus
      wipeable). The uncommitted apply on the Windows box is to be discarded there
      (`git restore .`, then `git pull`). Standing rule recorded in Claude's memory: no HaShorashim
      rulings recorded or applied until the reviewer says so; rebuilding derived files is fine.
    * **Hebrew inside English prose rendered backwards.** Two Hebrew pieces separated only by
      punctuation - `Under shoresh אבל, (שופטים ז, ככ). ככ is not a number` - are one
      right-to-left run to the Unicode bidi algorithm, so an email client draws the shoresh, the
      citation and the numeral in reverse order. The fix is in the writing: English between the
      pieces (`Under shoresh אבל the note reads (שופטים ז, ככ), and the verse number ככ is ...`).
    * **`tools/check_mixed_direction.py`** finds every such place and exits 1 if any exist; a
      parenthesised citation counts as one piece (its inner comma is not a boundary), and a Hebrew
      phrase separated by spaces only is one piece. Test
      `test_two_pieces_of_hebrew_are_never_divided_by_punctuation_alone` holds a flagged and a
      clean version of the same sentence, so it can fail both ways. Found 14 places in the two live
      drafts to the Sefaria editor, all rewritten; the four live drafts now check clean. The
      already-sent citation email has 15 (e.g. `Under אלה, (בראשית מא, כז) where`). Recorded in
      Claude's memory with the instruction to run the check on every draft containing Hebrew.

0IE. **[2026-09-18, reviewer: "fix those 2 bugs then regen and add his reading with credit"] BOTH
    PARSER BUGS FIXED; THE REGENERATION FOUND TWO FLAGS THE EYE PASS HAD WRONGLY PASSED - THE SENT
    EMAIL'S "146 HOLD UP" IS 144.**
    * **Fixed in `tools/adjudicate_against_verse.py`**, one test each written first and seen to fail:
      - a verse field listing several verses is split, not summed (`VERSE_LIST`, `cited_verses()`);
        a colon or bracket ends the verse field (commentary or a second reference) - only after the
        first comma, since before it a colon is a Talmud folio side (`שבת קיח:`, 133 notes);
        `(ברא, מט, כד)`, a comma after the book, reads as chapter and verse;
      - `(שם שם, כט)` inherits the chapter; a stray mark before the parenthesis no longer hides a
        note; and an UNREADABLE note now clears the running reference on both failure paths, so
        `שם` after it resolves to nothing instead of an older book (Lesson 34 - the second path,
        the no-comma branch, had the same defect and was found by reading the sibling).
      - `tools/validate_quotations.py` corroborates a quotation against EVERY verse the citation
        names (range or list), where it had used the first verse only and the span solely to
        suppress a false "misplaced". Tests `test_a_citation_naming_several_verses_is_not_summed_into_one`,
        `test_ibid_follows_the_note_before_it_or_resolves_to_nothing`. Gate 593 passed.
    * **Regenerated, before -> after:** confirmed 13,508 -> 13,530; not corroborated 6,079 -> 6,062;
      unparsed 770 -> 778 (+8: ibid after an unreadable note, deliberately); nonexistent verse
      93 -> 80; points elsewhere 150 -> 148. CSV 146 -> 144 rows, every one still
      `checked_by_eye = yes`.
    * **THE TWO ROWS THAT LEFT WERE FALSE FLAGS, AND THE 2026-09-14 EYE PASS HAD PASSED BOTH.**
      `(דברים ב, ט, יג)` under `והב` is Deuteronomy 2:9 and 2:13; the quotation is 2:13, so the note
      is right - the parser summed it to 2:22 and the row read `misprint`, proposed 2:13, "the
      quotation is the proposed verse and not the cited one", `checked_by_eye = yes`. Same for
      `(במדבר טז,ז, כא)` under `בדל`: 16:7 and 16:21, quotation 16:21, parsed as 16:28. The eye
      pass compared the quotation with the PARSED reference in `cited_ref`, not with the note as
      printed - Lesson 50, SAY WHICH ONE YOU CHECKED, on the same file that lesson was written
      about. Consequences: 144 hold up, not 146; 90 misprints, not 92; 72 single-letter, not 73.
      The letter pairs are unchanged (ה/ח 31, ב/כ 16, כ/נ 4, ב/ג 4, ו/ז 3). **The sent email
      carries 146 and 92**, and the reply draft corrects them.
    * **Sefaria editor's reading recorded**, in `citation_review.json`: the `צפת` row is now kind
      `placed by Sefaria` (not `misprint` - 7:19 may be Bacher's deliberate pointer to the wording),
      proposed I Kings 7:16, with a `credit` field and the reasoning; the file carries an
      `annotations` entry recording the change.
    * **The 80 still out of range, re-sorted:** 57 well-formed numerals past the chapter's end, 10
      `שם` references that are genuinely out of range (e.g. `(שם מה, לג)` under `הדד` - Jeremiah
      48:33, where `הידד` stands; מה for מח), 7 chapters that do not exist, 6 malformed numerals
      (`ככ` x4). Two of the ten, both under `ספא`, are ibid pointing past the note before it
      (Genesis 43:24/25 behind a Judges note), which no parser reading "the note before" can get.
      None of the 80 read against the text yet.
    * **RE-RUN THE SAME DAY (reviewer: "rebuild demo is over"), rehearsed first on an APFS clone
      of the corpus root, then run on the real one - byte-identical to the rehearsal.** What the
      rehearsal changed before anything real was touched:
      - **The ibid clearing moved from `parse_citation` into `entry_refs`.** The inline-citation
        tool calls `parse_citation` on every parenthetical in running text, prose included, where
        `שם` after a prose bracket still means the last citation; clearing there would have left
        real citations in their corrected text as words. With the clearing in the footnote caller
        only, `gold100_text.json` / `gold100_footnotes.json` come out BYTE-IDENTICAL (old parser
        reproduces the committed files; new parser changes 0 of 100 entries, 1,177 citations
        either way) - so they were not regenerated.
      - **Clearing was re-decided by count, not by example.** It made one right answer
        unresolvable: `(שם לז, יא)` under `בר` is Job 37:11 behind a Mishnah note, and the old
        inheritance got it. Counted over all 13 `שם` notes after an unreadable one: inheriting
        matched the quotation 1 time, was wrong or pointed at no verse 8, and had nothing to inherit
        2 (e.g. `(מ' פאה ד, ט)` then `(שם ו, א)` is Mishnah Peah 6:1, not Leviticus 6:1). Clearing
        kept; the cost is that one row, stated in the test's docstring.
      - **The prefix strip widened**: anything before `(` - `וֹ (ש"ב א, ו)` had a pointed letter
        glued on, which hid the note and sent the `(שם, שם)` after it to I Samuel 30:16.
      - **The same first-verse-only bug in the SIBLING (Lesson 34):** `adjudicate_against_verse.py`'s
        own lookup read a range or list against its first verse. `(תהלים מ, ח—י)` under `אז` had
        4 rows "uncorroborated, 0 matched" that now match 16 words; 9 verdicts moved in all.
      - A first "reproduce with the old parser" run returned 0 rows and would have passed as a
        comparison: the copied tool looked for the Tanakh next to itself, found none, and checked
        nothing (Lesson 25). Caught because the row count was 0; re-run with the corpus linked, the
        old tool reproduces the committed `verse_verdicts.json` byte-for-byte.
    * **Result, all attributable to this fix:** citation buckets 13,532 / 6,066 / 772 / 80 (sum
      20,450); CSV unchanged at 144 rows; `verse_verdicts.json` -1 row (the Job case), +5 (lists,
      the colon comment, the comma after the book, the glued prefix), 14 changed; the witness
      queue keeps all 2,057 rows with the same keys, 20 of them changed in `verse` only, and the
      two ruled words on entry 1 (w37, w74) byte-identical - `witness_disputes.json` was
      deliberately NOT rebuilt, which is what keeps the `0GW` hazard away. The live dashboard on
      :8421 serves the new verdicts without a restart.

0ID. **[2026-09-18, the Sefaria editor's reply to the citation email, relayed by the reviewer: what
    are the other third of the citations, is the remaining manual work 12 cases, and the unplaced
    `צפת` note] THE FOUR BUCKETS ARE EXCLUSIVE AND SUM TO 20,450; THE 93 OUT-OF-RANGE REFERENCES HOLD
    ~70 UNREAD ERRORS AND EXPOSE TWO PARSER BUGS.**
    * **Every citation falls in exactly one of four buckets** (`quotation_suspects.json` counts,
      summed to confirm they are exclusive): 13,508 (66.1%) quotation corroborated by the cited
      verse; 6,079 (29.7%) did not corroborate; 770 (3.8%) did not parse; 93 (0.5%) cited verse not
      in the reference corpus. `suspect words` (299), `quotation ends in the cited verse` (425) and
      `citation points elsewhere` (150) are overlays on those, not further buckets. The 158 rows read
      by hand came out of the did-not-corroborate bucket; 8 of them are now dropped automatically by
      `ends_in_cited` (`0FM`), hence 150 today.
    * **The 770 are mostly not Tanakh references at all**, by their openings: Mishnah (`מ'` 105,
      `משנה` 38), Talmud tractates (`שבת` 40, `בבא` 27, `חולין` 23, `ברכות` 21 and more), `בבלי` 25,
      Ibn Janah's Kitab al-Luma (`למע` 82), cross-references (`עיין` 17, `דף` 20), Tosefta, Sifra -
      and 77 `שם` notes the parser could not resolve. Out of scope for a verse check, not failures.
    * **The 93, sorted by cause** (read from `entry_refs`, not re-derived): 57 well-formed numerals
      past the chapter's end (`(תהלים כג, ח)`, Psalm 23 has 6 verses); 7 chapters that do not exist
      (`(עמוס י, י)`, `(רות כ, יז)`); 6 numerals that are not numerals, 4 of them `ככ` - `כב` with the
      ב/כ confusion (`(שופטים ז, ככ)` under `אבל`, `אבן`, `אבר`, `אז`); **16 `שם` references and 7
      verse lists that are OUR PARSER's misreadings.** So ~70 probable errors in their apparatus -
      NONE read against the verse text yet; some of the 57 may be chapter-numbering differences
      (Joel 3 / 4) rather than misprints.
    * **BUG, `tools/adjudicate_against_verse.py` `entry_refs()` - FIXED, `0IE`:** a note listing several
      verses is summed into one number - `(מ"א ח, לח, לט, מ)` -> I Kings 8:117,
      `(ירמיה מח, כט, ל)` -> Jeremiah 48:59; and a `שם` note is misresolved - `(שם שם, כט)` -> Isaiah
      300:29, `(שם יב, כג: קנה במקום כסה)` -> Proverbs 12:411. 23 instances visible here because they
      land out of range; the same defects on a note that happens to land IN range would put a
      quotation against the wrong verse and count it as not corroborated, and that number is
      unmeasured. Sweep before fixing: every note with more than one comma, and every `שם`.
    * **`צפת`, the row `citation_corrections.csv` marks "unclear":** Ibn Janah quotes II Chronicles
      3:15 (`וְהַצֶּפֶת אֲשֶׁר־עַל־רֹאשׁוֹ`) and glosses it `והכותרת אשר על ראשו כאשר הוא מבואר
      בנוסחא האחרת`, note `(מ"א ז, יט)`. The editor places it at I Kings 7:16, by way of Radak's
      parallel entry. The verses bear him out on content - 7:16 gives each capital five cubits, as
      Chronicles gives the `צפת`, where 7:19 says four - while 7:19 is the verse whose WORDING the
      gloss echoes (`וכתרת אשר על ראש העמודים`). The tool's own proposal for this row, I Kings 5:19,
      matched nothing but `כאשר` and is wrong. **Pending:** record the editor's reading in
      `citation_review.json`, credited to him, and regenerate the CSV. **DONE, `0IE`.**
    * Reply drafted: `draft_email_citation_numbers.txt` in the corpus root, revised under `0IE` with
      the regenerated figures. Not sent.

0IC. **[2026-09-18, reviewer, on the Windows box: "why are these wit. choices?" and, of the
    applier's closing advice, "do that"] THE APPLIER TOLD EVERY BOOK TO RUN YAD MALACHI'S REBUILD -
    THE ONE COMMAND SEFER HASHORASHIM MUST NOT RUN.**
    * `apply_reviewer_decisions.py:1619` ended every successful run with
      `2. Run ./rebuild_all.sh to regenerate derived files and fresh word indices.`, with no idea
      which corpus root it had just written to. On the Sefer HaShorashim root that chain re-derives
      the rows this book's rulings are drawn against (`0GQ`, `0GW`) - the advice pointed straight
      at the documented mistake. It now asks `cio.corpus_root_is_this_repo()` (new, public: the
      private `_DEFAULT_ROOT` comparison had no name) and prints
      `build_klalim_demo_dataset.py` plus the corpus root and an explicit "do NOT run
      rebuild_all.sh here" for any other book. Test
      `test_the_applier_names_the_rebuild_that_belongs_to_the_book` reads both branches; its first
      version asserted the other branch never mentions `rebuild_all.sh` at all and failed on the
      warning line, which is the half worth keeping.
    * **Why every HaShorashim ruling is a `witness_choice`, and it is structural:** that corpus has
      **0** rows in `review_queue_part1.json` and **2,057** in `reconstruction_witness_queue.json`.
      It has no machine-candidate queue at all - its disputes are our reading against Sefaria's, so
      the dashboard records `/api/decisions/witness`. Consequence for the reviewer: a plain apply
      reports "witness rulings recorded and NOT applied" and changes nothing;
      `--apply-witness-choices` is required for this book, every time.
    * **The Windows round trip, verified here after the rulings were pushed:** 2 rows, LF line
      endings (`0HX`'s fix, written on Windows), no Hebrew geresh/gershayim in `chosen_text`
      (`0HR`), and both recorded under actor `eric` - so `0HZ`'s per-tab reviewer name works on
      Windows. Dry run with the flag: klal 1 word 37 witness-replace, word 74 witness-confirmed.

0IB. **[2026-09-17, reviewer: "push everything ... server loads with yad malachi in two panes but
    the scan page is empty. what is a clean way to push that over? what's the cleanest way to get
    hashorashim on the win box? does the private repo have everything? if rebuild is required, is
    that proc entirely local?"] BOTH REPOS PUSHED; THE WINDOWS BOX NEEDS THE TWO IGNORED FOLDERS
    AND NO REBUILD.**
    * **A NEW RULE FOR THIS FILE, and it cost a pointless scrub to learn: never annotate an
      example value with a claim about whose it is.** A placeholder username in a test identifies
      nobody. An entry here that says which real person an example value was taken from IS the
      identification, and it turns an ordinary token into one - in the same public file the
      role-not-name rule exists to protect. The value is not the leak; the annotation is. Reviewer,
      the same day: the earlier version of this item was the botch, not the test data.
    * The pre-push scan over every unpushed commit ran as the rule requires. What it matched is the
      book's own text quoting the Amora (`כשמואל`, `ולשמואל`, `ושמואל`, and a lexical-repair test
      on `שמואל`/`שמול`) and generic first names used as example reviewers in the `0HZ` tests.
      Nothing was redacted and no history was rewritten.
    * **Private repo (`esafern/hashorashim`, visibility PRIVATE):** `citation_corrections.csv`'s
      regenerated headwords committed and pushed to `nli-fulltone-rebuild`. Its default branch is
      `master`, so a clone needs `--branch nli-fulltone-rebuild`.
    * **Does it have everything? Measured, not assumed:** a fresh clone from GitHub (45 MB), served
      by a venv with no packages. Every route answered 200 except the page image (404). But
      without `docai_word_boxes/` the answers are silently thinner: `/api/page/58` 8.5 KB against
      51 KB, `/api/klal/1` 6.5 KB against 7.3 KB (Lesson 26). With `images/pdf_pages/` and
      `docai_word_boxes/` added, everything is whole. No rebuild is needed: the derived files are
      tracked.
    * **Yad Malachi's empty scan pane is the same two folders**, gitignored in this repo. Bundles
      made in `~/work/transfer/` (outside both repos), each extracting in its book's root:
      `yad-malachi-scan-data.zip` 155 MB (337 page PNGs, 337 word-box pages),
      `hashorashim-scan-data.zip` 433 MB (94 + 94); both pass `unzip -t`.
    * **Found making the bundle: `docai_word_boxes/docai_word_boxes` is a symlink** into the
      pre-migration clone (`~/work/yad-malachi/yad-malachi-pipeline/docai_word_boxes`, dated
      2026-08-17). Zip followed it and the first bundle was 1.27 GB and 8,676 files. Inert for the
      dashboard, which reads `page_N.json` only; excluded from the bundle, left in place.
    * **Is a rebuild local?** Every `rebuild_all.sh` stage's import closure was read: the only
      network or cloud library is `google` (and `fitz`) in `verify_corrections_vision.py`, which
      `--skip-vision` leaves out. Everything else is local.
    * **CONFIRMED THE SAME DAY: the dashboard runs on Windows, serving Sefer HaShorashim from the
      private repo plus the two folders** (reviewer: "works fine, so windows is now a first-class
      host for dashboard for hashorashim"). REVIEWING is proven there. Recording and applying
      rulings on Windows have not been exercised by anyone yet, and `atomic_write`'s retry around
      `os.replace` under a reader (`0HZ`) is still untested on that platform.
    * **"Two panes":** the index pane is hidden below 1200 CSS pixels (`app.css` media query),
      which also hides the settings button and the new reviewer pill. Windows display scaling
      shrinks the CSS width.
    * `SETUP-WINDOWS.md` updated with all of it, plus a fix: step 3 said `cd %USERPROFILE%\work`,
      which is `cmd.exe` syntax, under a PowerShell heading. The reviewer's own edit to that file
      (localhost works too) is in the same commit.
    * **The spelling thread is its own draft** (`draft_email_spelling.txt`). Its letter-name example
      first named the shoresh `גף`; the page-147 heading `הגימל והפא והנון` is the shoresh `גפן`,
      corrected before handing over. A claim that the page prints `הרש` and `התו` was dropped:
      those two were never read off the ink. The paragraph still has to come OUT of the second
      email, which the reviewer had open in an editor, so it was not touched.

0IA. **[2026-09-17, reviewer, reporting the call with the Sefaria editor] TWO TOPICS FROM THE CALL,
    EACH NOW A DRAFT; ONE OF THEM DESCRIBES A FEATURE THAT DOES NOT EXIST YET.** Neither sent.
    * **Sefer HaShorashim's spelling differences are editorial, by their contractor** (paraphrased
      from the reviewer's account): plene/defective, vowel points and other spelling choices were
      decisions made when the text was prepared, and need to be talked through. This is the
      question `0HI` was built for. A paragraph citing three of its measured classes - points on
      34.2% of their words where the printing has almost none (`0GY`); a geresh inside letter names
      that pages 58 and 147 do not print; 266 of 300 plene/defective differences inside vocalized
      quotations - went into the second email, with an offer of the full list.
    * **Which OCR produced their Sefer HaShorashim text is unknown.** The reviewer does not know; the
      second email now asks, because every comparison against "their OCR" is measured against it.
    * **Their larger problem: uneven quality across texts, and corrections arriving by email in a
      steady stream** that has to be processed and put before a human. The reviewer said this
      project could help, without details. `draft_email_corrections_stream.txt` sets out the shape:
      a correction as a disputed word beside the scan, a human ruling, a separate apply step;
      structured submissions (a form or a fixed format) turn into entries mechanically, freeform
      email needs a model to parse and a human to see the original beside the parse; and only
      texts with a scan of their edition aligned can be checked against the page - a per-book
      effort, so it proposes starting with one text, and asks for volume, the texts that draw most,
      and a few anonymized examples.
    * **NOTHING INGESTS AN OUTSIDE CORRECTION TODAY.** The closest existing path is the witness /
      comparison-text mechanism (another text's reading at a position, `build_witness_disputes`),
      which is the natural seam. The draft says "could" and "would" throughout for that reason.
      Not scoped, and a scope decision for the reviewer.

0HZ. **[2026-09-17, reviewer: "expose the current username onscreen, and in the db settings allow
    the user to change it there. can we configure so if one server is serving multiple sessions,
    each can have a different user? it should return to the default set by the env value at each
    new session. do the write to temp and rename for the apply step. is there a good way to let
    the user know the entry is stale b/c another session has unapplied changes?"] ALL FOUR DONE.**
    * **A name per session, not per process.** The tab keeps the chosen name in `sessionStorage`:
      it survives that tab's reloads, ends with the tab, and a new tab starts at the default. The
      server holds no per-user state - `postDecision()` (app.js) sends `X-Sefer-Reviewer`,
      percent-encoded, on every ruling; `do_POST` validates it
      (`identity.normalize_reviewer_id`: letters of any script, digits, space and `._@-`, 64 max;
      anything else is a 400 and nothing is written) and parks it on a thread-local for `_actor()`.
      No header means `$SEFER_REVIEWER` exactly as before. Still asserted, `verified: false`.
      Chrome copies sessionStorage into a DUPLICATED tab, so a duplicate starts with its
      original's name.
    * **On screen:** an icon-and-name pill in the index pane's filter row, and a "Recording rulings
      as" field with the roster as suggestions and a "Use default" button in the settings tray.
      `GET /api/reviewer` serves the default and the roster WITHOUT emails.
    * **Three layout defects found only in screenshots, fixed (Lesson 45):** the hidden server
      notice drew as an empty yellow bar (`display: flex` outranks `[hidden]`); "Recording as
      <name>" ellipsized to "Recording a..." at 1280px, then, with the label set to shrink first,
      clipped mid-letter ("Recorc shmuel") - hence the icon; and a long Hebrew name lost its
      START until the name span got `dir="auto"`.
    * **The eight save paths now share `postDecision()`.** Each built its own fetch; the header
      had to reach all eight (Lesson 34), and the helper also records the ids of this tab's own
      rulings.
    * **Stale entries.** `GET /api/changes?since=N` returns the rows appended after row N - a
      stable cursor because the ledger is append-only - plus `corpus_stamp` for
      `klalim_demo_dataset.json`. The tab polls every 15 s while visible and on becoming visible.
      A row whose id this tab did not get back from its own save, on a mounted entry, puts a
      notice on that entry naming who ruled, with "Refresh entry"; any refetch that STARTED after
      the notice clears it, including the tab's own next save there. A moved `corpus_stamp` (an
      apply and rebuild) or a replaced log is a page-level "Reload page" notice. While one of the
      tab's own saves is in flight the poll does not classify rows or advance its cursor, so its
      own ruling is never reported as another session's. **That race guard has no test.**
    * **Atomic corpus writes.** `cio.atomic_write` (temp in the same directory, flush, fsync,
      `os.replace`; the temp removed and the original untouched if the block raises).
      `save_part1` - the one serializer every corpus writer uses - `word_identity.save`, whose
      hand-written version it replaces, and `build_klalim_demo_dataset.py`, the file the text pane
      is served from. On Windows `os.replace` onto a file a reader holds open raises
      PermissionError; it is retried 20 times at 50 ms. **Untested on Windows.**
    * **Tests.** Logic: `test_a_corpus_write_is_never_visible_half_done` (a reader mid-write sees
      the old file - an in-place writer was run and reads `''`), `..._name_its_reviewer_...`,
      `test_changes_reports_every_row_appended_since_a_tabs_cursor`; the line-endings guard now
      follows the writers into `atomic_write`. Browser, on the fixture:
      `test_each_tab_records_rulings_under_its_own_name`,
      `test_another_sessions_ruling_marks_the_open_entry_stale`,
      `test_the_hidden_server_notice_takes_no_room`. Four mutations, each caught: the header
      dropped, sessionStorage swapped for localStorage, the own-id filter removed, the `[hidden]`
      rule removed. Gate 590 passed; browser and fixture suites 137 passed, 1 skipped. All three
      dashboards restarted.
    * **FOUND ON THE WAY, NOT CAUSED BY THIS: `test_a_nav_jump_lands_on_the_klal_it_was_asked_for`
      is flaky again.** It failed once in the full run; alone it failed 3 in 10 with this change,
      and 3 in 10 at HEAD `c5cc7c4` in a clean worktree. Item `0DG` recorded 0 in 28 on 2026-09-08,
      so something since then brought `0CA`'s symptom back. Not investigated.
    * **Still open from `0HY`:** a cross-process lock on the ledger append (two server processes,
      or an instance count above one, share no lock), and real authentication.

0HY. **[2026-09-17, reviewer, relaying the Sefaria editor's question about running the dashboard
    in the cloud: "how can he set [the username] on the fly? if multiple people try to use the
    dashboard at the same time, is there a real risk of corruption?"] READ FROM THE CODE, NOT
    CHANGED. IDENTITY IS ONE PER PROCESS; THE LEDGER IS SAFE WITHIN ONE PROCESS AND UNGUARDED
    ACROSS PROCESSES; SIMULTANEOUS RULINGS COLLIDE SILENTLY; APPLYING DURING REVIEW IS THE REAL
    HAZARD.**
    * **Identity cannot be set on the fly.** `pipeline/identity.py:157`:
      `reviewer_id = reviewer_id or os.environ.get(ACTIVE_REVIEWER_ENV)` - `$SEFER_REVIEWER`, read
      per request from the PROCESS environment, which a running server cannot change. Nothing in a
      request (header, cookie, form field) carries a name. So changing reviewer means restarting
      the server, and every person using one server is recorded as the same id. Unset, it records
      `local` / "Unidentified local reviewer". The seam for real auth exists and is documented in
      the module header (`verified` flips when an authenticated subject is available); nothing
      feeds it yet.
    * **File corruption, one server process: guarded.** `review_decisions.py:149-156`, a
      `threading.Lock()` around every append, one JSON record per line; readers re-read on
      `(mtime_ns, size)`. The server writes nothing but the ledger (no `save_part1`, no
      `word_identity.save`, no `json.dump` in the server or the modules its handlers call).
    * **Across processes: no guard.** The lock is in-process. Two servers on one corpus root, a
      cloud service scaled to more than one instance, or a tool appending while the server does,
      share no lock. Small `O_APPEND` writes on a local Linux disk are very unlikely to interleave;
      on a network or FUSE mount (e.g. a bucket mounted into a container) that assumption does not
      hold. Not measured.
    * **Collisions are silent, not corrupt.** `all_current()`: "later (later-appended) records win
      for the same key". Two reviewers ruling on one word both land in the ledger, the later wins,
      no warning is raised, and neither sees the other's ruling until they reload (the panel data
      is fetched when the entry mounts).
    * **Applying during review is the real hazard.** `apply_reviewer_decisions.py` rewrites
      `part1.json` IN PLACE (`corpus_io.save_part1`, `open(path, "w")`, not temp-and-rename as
      `word_identity.save` does) and shifts word indices. A dashboard request mid-write can read a
      truncated file (an error, transient); a ruling recorded against pre-apply positions is caught
      by the applier's drift check rather than misapplied, but it becomes cleanup work.
    * **Cloud-specific, not code:** a container's local filesystem is typically ephemeral, so a
      ledger kept there is lost on restart; and with no authentication, anyone who reaches the URL
      can read the corpus - for Sefer HaShorashim, Sefaria's unreleased data - and write rulings.
    * **Open, and not started (a scope decision for the reviewer):** a per-request identity from an
      authenticating proxy's verified header into `resolve_actor`; a cross-process file lock on the
      append; temp-and-rename in `save_part1`.
      **ANNOTATED same day, see `0HZ`:** temp-and-rename DONE; a per-SESSION identity DONE, but
      asserted by the tab, not taken from an authenticating proxy; the cross-process lock NOT done.

0HX. **[2026-09-17, reviewer: "i need new instructions for installing tool on windows box. is any
    ai involved or needed for making decisions and applying them? ... is ai required for ingesting
    a new sefer?"] `SETUP-WINDOWS.md` WRITTEN, AND FOUR WINDOWS-ONLY DEFECTS FIXED ON THE WAY.
    THE REVIEW HALF IS STANDARD-LIBRARY PYTHON; A NEW BOOK STILL NEEDS AN OCR MODEL.**
    * **The two answers, measured rather than recalled.** The import closure of
      `review_server.py`, `apply_reviewer_decisions.py`, `audit_applied_decisions.py`,
      `build_klalim_demo_dataset.py` and `tools/export_corpus.py` is 12 files and imports ONE
      non-stdlib package, `python-bidi`, whose import is caught in a `try` and used only to render
      Hebrew for a terminal. Proved by running it: a `venv --without-pip` with no `bidi`, `fitz`,
      `numpy`, `PIL` or `google` served `/`, `/api/corpus`, `/api/klal/1`, `/api/klal/1/versions`,
      `/api/page/58` and a 3.6 MB scan PNG, all 200. Ingest is the other way round - OCR is a paid
      cloud model per book, the witnesses are models, and only the vision adjudicator is removable
      (`--skip-vision`), at the cost of triage, not text.
    * **Nothing here has been run on Windows. The doc says so in its own header.**
    * **Defect 1, the authored files would have been rewritten as CRLF.** Python's text mode writes
      `os.linesep`, and all three authored files are TRACKED, so the first corpus write on a
      Windows box turns `part1.json`, `word_identity.json` and `review_decisions.jsonl` into
      whole-file diffs against the Mac. `save_part1`, `word_identity.save` and
      `review_decisions.append_decision` now pass `newline="\n"`; `.gitattributes`
      (`* text=auto eol=lf`) covers every derived artifact and script as well. `git ls-files --eol`
      shows index and working tree already LF, so the attribute renormalises nothing.
      `test_every_writer_of_an_authored_file_pins_its_line_endings` reads the call sites with `ast`
      - a written-then-read-back test cannot fail on a Mac (Lesson 25) - and it fails when the
      keyword is removed, checked both ways.
    * **Defect 2, three scripts opened a text file with no `encoding=`** and would have read Hebrew
      through a legacy Windows code page: `validate_suppression_filters.py:205`,
      `verify_local_setup.py:60` (the script a new machine runs to prove itself) and
      `verify_witness_green_vision.py:197`, the last of them a WRITE.
      `test_no_script_opens_a_text_file_without_saying_utf8` sweeps all of `pipeline/` and `tools/`
      and holds the count at zero.
    * **Defect 3, `rebuild_all.sh` could not find a Windows venv.** Every stage called
      `./venv/bin/python`, which on Windows is `venv\Scripts\python.exe`, so a Git Bash run died on
      step 1. It now resolves `$PY` from either layout and exits with a message if neither exists.
    * Gate after all of it: 587 passed. Both dashboards and the demo copy restarted, since
      `corpus_io.py`, `review_decisions.py` and `word_identity.py` are modules the server imports.
    * **First real install, same day: Python installed, `py` "not found" in PowerShell.** Cause:
      the terminal predated the install and had the old PATH; a new window fixed it (reviewer
      confirmed). Step 1 now says to close and reopen the terminal, not open a tab.
    * **Open:** steps 2 onward are still unrun on Windows; the reviewer install continues to be the
      test of this file. Also unaddressed there: `tools/` scripts that shell out (`tesseract`), and
      anything expecting a POSIX path separator in a CLI argument.

0HW. **[2026-09-17, reviewer: "let's start with an email just about the citations... when you
    reference a specific citation, you must reference the shoresh where it is found. not my urls
    since he does not yet have the tool"] THE CITATION CSV NOW WRITES THE HEADWORD THE WAY THE BOOK
    PRINTS IT, AND TWO FIGURES IN THE OLD DRAFT WERE STALE.**
    The call with the Sefaria editor happened and went well. He has no dashboard, so a finding's
    only address is its shoresh - which makes the headword column of
    `citation_corrections.csv` the deliverable's index, and it was written in the FOLDED form
    (`אמ`, `אפ`, `אונ`).
    * `corpus_io.root_display()` finalizes a folded root's last letter, the inverse of the display
      half of `root_key()`. Checked against all 100 reviewed entries: every one of them ends its
      root in a final form where one exists, and none ends in a plain one. It is a display
      function and says so - never a lookup key. `validate_quotations.py` applies it to the CSV's
      headword column only; the `--review` join still runs on the folded root.
    * Regenerated with the command in the tool's own docstring and diffed against the committed
      file: 146 rows, same order, **40 rows differ and all of them in column 1**
      (`אמ`→`אם`, `דרכ`→`דרך`, `טפפ`→`טפף`).
    * Test `test_a_root_shown_outside_this_pipeline_ends_in_a_final_letter`; an inert
      `root_display` fails it (Lesson 42). Gate: 585 passed.
    * **Two figures in the unsent draft were stale, re-measured against the 146-row CSV:** 21 rows
      sit inside the reviewed hundred, not 18 (5 under `אם`, 3 each `אלה`/`אמן`, 2 each
      `און`/`אף`, 1 each `אח`, `אחה`, `אך`, `אוץ`, `אכף`, `אלם`), and the matching had to fold
      finals to see them at all - a raw headword match finds 2 of the 21. Item `0FM`'s own "22...
      along with 28 suspect words" predates the eye pass that took the file from 158 rows to 146.
    * **The suspect-word sentence was dropped from the email rather than restated.** 299 words are
      flagged as sitting inside an otherwise-matching quotation, 26 of them in the hundred, and
      reading those 26 shows most are Ibn Janah's own prose inside the window (`וכמהו`, `כאמרו`,
      `כמו`) - the tool's docstring says it reports suspects, not errors. A few look like real
      truncations (`רל` under `אן` at `(במדבר יב, יג)`, `עמ` under `אסר`), but they have not been
      read by eye, so they are not a claim to put in a letter. **Open: the 299 need an eye pass
      before any of them is offered to Sefaria.**
    * The draft is `draft_email_citations.txt` in the corpus root - citations only, every specific
      citation addressed by shoresh, no dashboard links. **SENT 2026-09-17 by the reviewer, with
      their own edits.** One of them corrected an attribution: the draft said "I read all 158
      against the verse text by hand", and that reading was done by Claude, not the reviewer
      (reviewer: "I did not manually review the pesukim cited - you did that work"). Recorded as a
      standing rule in Claude's memory: in a draft written as the reviewer, "I" never claims work
      Claude or the pipeline did. **The sent wording settles the form: "The AI read all 158 against
      the verse text by hand"** - name the tool plainly rather than reaching for the passive. The
      sent text is kept in the corpus root as `sent_email_citations_2026-09-17.txt` (the portion
      the reviewer pasted back), and the three unsent drafts were aligned to its two conventions:
      that attribution, and one short paragraph per cited example, opening "Under shoresh X".
    * **The other half of the old draft is now `draft_email_text_findings.txt`** (the 95.1% measure,
      the 89 of 90, the three places the page reads against his correction, the nun/gimel caveat,
      the one verse question), with the same shoresh addressing and every first-person claim
      checked against who did the work. The verse question was re-read against the reference
      corpus: Isaiah 44:19 has `בְמוֹ־אֵ֗שׁ`. Not sent.
      **REVISED same day (reviewer's edits requested):** the 78 is now explained as what it is -
      of the 89 corrections that fall on a disagreement, 78 have our reading equal to the
      correction and 11 have neither reading right (the `0GH` table: 78 / 1 shared / 11 third
      reading); the three page-against-correction words each carry their shoresh and a phrase from
      his own corrected text (`אכף` w19 `נֶפֶשׁ עָמֵל גרמה לו`, `איד` w7 after Proverbs 1:26,
      `אם` w318 `בזולת פועל חולף ווזה`), both verses checked against the reference corpus; the
      shared-error paragraph opens from the call; every example is labelled "the shoresh X".
      **Declined as unmeasured:** that working through the disagreements would also have found
      "quite a few more he missed". Nothing measures errors his review left standing: the page has
      been read only at the 12 places ours differs from his CORRECTION (3 back ours - wrong
      corrections, not misses), and the 4 unchanged nun/gimel differences have not been read
      against the ink.
      **An opening added the same day** (the reviewer's own draft, cleaned up): the project needs a
      name; the dashboard runs on Windows; no AI in reviewing, ruling or applying (`0HX`); several
      users on one server with per-tab names and the stale-entry notice (`0HZ`), no authentication,
      one server per copy of the data (`0HY`); the OCR engine is swappable and five engines have
      already been run (DocAI, Cloud Vision, Surya, Tesseract, a VLM, via `tools/ocr_pages_*.py`
      and the witness runs); the vision adjudicator is optional (`--skip-vision`).
      **Found while checking "runs entirely locally": the dashboard is not fully offline.**
      `review_frontend/app.css:1` is `@import url('https://fonts.googleapis.com/css2?family=Frank+Ruhl+Libre...&family=David+Libre...&family=Inter...')`.
      Not AI and not data - a font request - but a sandbox with no internet access renders in
      system fonts, and every page view tells Google the dashboard was opened. The email says so in
      one parenthesis. **Open:** bundling the three fonts (all SIL Open Font License) into
      `review_frontend/` would make the claim unqualified; not done.

0HV. **[2026-09-16, reviewer: "review the data and code for hashorashim. surface any issues likely
    to come up during the demo"] PRE-DEMO REVIEW. NO SHOW-STOPPERS IN THE SOFTWARE; THREE ERRORS
    IN MY OWN DEMO MATERIAL, CORRECTED; FOUR THINGS HE MAY SEE ON SCREEN.**
    * **Swept, all 317 entries on the demo copy (:8422):** every `/api/klal` and `/versions`
      responds, none over 2s; every heading run found; every entry has Sefaria's text; all 5
      homographs split; 2,057 queue rows, none misplaced except two gap rows at the END of their
      entries (111/15 `בספר התוספת.`, 171/27 `עבידת בית אלהא.` - valid, `word_index == len(words)`)
      and entry 1 w37, whose row still names the pre-ruling `אַבְּן` (the panel shows it as "Our OCR",
      which is right).
    * **Walked in a browser, every demo link:** 26 dashboard addresses loaded with 0 page errors and
      0 console errors, the scan image present on each, the dispute panel opening on all but
      55/209 (row at 211, noted in the links file). The text-view selector switched all six views
      on entries 1, 59 and 73 with no errors. On the three pages whose image offset was checked by
      text only (70, 84, 85), the scan boxes sit on the right words.
    * **Errors in the demo material, found by reading the panels, corrected:**
      1. **The nun/gimel answer described the wrong seven words.** None of the 7 remaining nun/gimel
         differences is one of his corrections - the panel shows every one "(UNCHANGED)". Measured
         instead: **his review made 7 nun/gimel corrections in the hundred, and our independent
         read already holds 6** (`אגודה` 12/72, `גדרים` 59/244, `גופו` 63/45, `גופם` 63/47, `וגזרה`
         79/688, `בגבהי` 79/748); the 7th, the Arabic `ג'זאיר` (55/209), we misread too. The draft,
         the script and the links file now say that, and list the 7 unchanged differences separately.
      2. **Three of the four "verse questions" were spelling-only** (`ואונו`, `בין`, `ובנותיך`), and
         the panel he would see says the verse "cannot settle how the page spells the word" (`0GE`,
         Lesson 38). Dropped; `במו`/`כמו` (99/48, a letter difference the verse supports) kept.
      3. **Beat 4's example showed the verse-check gap on screen.** Entry 9 `בעליוי` prints Isaiah 1:3
         containing `בעליו` and says "could not be matched to the cited verse" - `0GZ`'s open bug,
         scheduled after the demo. Replaced with 25/4 `ויאהלז` (footnote marker, Genesis 13:12,
         "The verse has their reading, not ours").
    * **On screen, not errors, but he may ask** (added to the script as "Careful"):
      - the index footer reads **2,047 open** - all 317 entries; the script's 697 is the reviewed 100;
      - **entry 1, the first screen, shows a stray `ל`** in `צמח ל הדשא` (w12): the small raised mark
        `0GN` noted where Sefaria has `[י]צמח`, read as a letter. **No row flags it** - a data issue,
        unsurfaced, and a sibling of the footnote-marker class;
      - panels show internal tier codes raw (`TIER C_FOOTNOTE_MARKER`, `THEIR_CORRECTION_ONLY`,
        `A_NUN_GIMEL`);
      - the demo copy's entry 8 carries 4 recorded, unapplied rulings.
    * **Checked and NOT an issue for the demo:** `witnessReliabilityNote()` prints "measured correct
      in 99.2% of words" (`app.js:3921`), the hand-typed figure `0HU` showed is not an accuracy - but
      it renders only on the machine-candidate panel with a witness overlay, and HaShorashim's
      `review_queue_part1.json` is `{}`, so it never appears. Still a false sentence in the code.
    * All three dashboards restarted on the current code; `review_server.py`'s newer mtime was a
      byte-identical restore from a mutation test.

0HU. **[2026-09-16, reviewer: "script out (big picture) the demo - show where we add value and
    make his life easier"] DEMO SCRIPT PUBLISHED; EVERY SCREEN CHECKED ON :8422. AND A
    MISLEADING FIELD NAME IN THE EXPORT.**
    * **The script:** <https://claude.ai/artifact/XYo4R5BxhqWboBZUtVFMpm> - eight beats, ~25
      minutes, each with the screen to open, the line to say, the measured number and what it
      saves Sefaria's reviewers: the hundred as yardstick (95.1% words, nun/gimel 88 -> 6); 5% of
      words holding 89 of 90 corrections; the scan one click away and the text views; the tier
      naming the kind of difference (entry 9 w22); rulings recorded, applied and listed; the
      citation check (146); three ink questions on reviewed text; next steps, handing off to the
      seven questions.
    * **Checked before publishing, on the demo copy:** entry 1's four rulings (w37 `אַבְּ`); 57/11
      `הוא`, 68/23 `גמרה`, 79/389 `וזה`; 9/22 `בעליוי` served as tier `C_footnote_marker` with
      Isaiah 1:3; entry 73's homograph split (109 words of theirs); entry 59's four views.
    * **Two claims caught and softened before publishing:** the text views do NOT line their
      texts up with ours line for line (`0HH`: punctuation tokens and inline numerals), so the
      script says to toggle for the reading, not the layout; and the 18-in-reviewed-entries
      citation figure is from 2026-09-14, not re-run.
    * **FOUND: `INTERVENTIONS.json` calls the pre-correction OCR reading `as_printed`.** The demo
      export lists entry 1 w37 as `as_printed: אַבְּן` - but the page does not print that nun; it
      is a footnote mark the OCR fused into the word, and removing it is the correction. For an
      OCR-artifact correction the field states something false about the page. The script says to
      describe the list rather than open the JSON. Not changed: renaming a field in an export
      Sefaria consumes is their format question as much as ours (`tools/export_corpus.py`).
    * **CORRECTED THE SAME EVENING, on the reviewer's questions.**
      - **The "99.2%" was never a measurement of accuracy, and no committed tool produces it.**
        It reaches the witness queue as a hand-typed CLI argument
        (`build_witness_review_queue.py --witness-accuracy`). Re-measured on one basis today -
        `build_witness_disputes.text_words` tokens, 12,732 reviewed words, their corrected text
        as reference: **their raw OCR 98.7%, our text 95.4%.** But their corrected text was made
        BY EDITING their raw OCR, so their figure mostly says how little the review changed
        (about 1 word in 80), and any error it left is inside the reference. The two figures
        are not comparable; the sentence is removed from the draft to the Sefaria editor. Same
        shape as `0HM`: a reference built from one source scores that source.
      - **"His reviewers read every word" was an assumption.** Nothing on record says how the
        Sefaria editor reviews, whether against the scan, or alone. The script's thesis and two
        beats now state only what is measured (89 of 90 of his review's corrections sit in the
        5% of disagreement), and beat 2 carries a question to ASK him instead. The draft's "a
        full read" wording is gone for the same reason.
      - **The page itself was broken on screen:** `.check li` was a grid, so every inline child
        of a checklist line (a bold, a link, a code span) became its own grid cell, and the text
        stacked on top of itself. Rendered and looked at before republishing this time - the
        step the page-design guidance asks for and the first publish skipped (Lesson 45, PIXELS,
        NOT THE DOM).
      - **The nun/gimel point was about us, not him.** "88 -> 6" is this project's history. What
        the Sefaria editor actually raised (`0FJ`) was that nun/gimel interchanges were frequent
        in Arabic words and some of HIS corrections might be wrong. Re-measured to answer that:
        over the hundred, our independent read agrees with his nun/gimel readings everywhere
        except **7** places (`text_words` basis; the scoring tool's own basis counts 6) - 3 plain
        misreadings of ours (`ינח` 26/93, `והתרנום` 55/262, `מננד` 79/1118) and 4 open: `נאוה`
        (ours `גאוה`, 46/104), `ההנעה` (`ההגעה`, 70/299), `בבנא` (`בבגא`, 92/26), `ישגה`
        (`ישנה`, 79/407). The draft paragraph and script beat 1 now say that; neither asserts
        which way the four go - that is an ink question, not yet read.


0HT. **[2026-09-16, reviewer: review the draft to the Sefaria editor, "update facts, remove the
    defensive and negative language"] REVISED, AS A NEW DRAFT BESIDE THE OLD ONE IN THE
    PRIVATE CORPUS ROOT. SIX CLAIMS WERE STALE; ALL RE-MEASURED TODAY.** Not sent.
    * **Why they were stale.** The 2026-09-14 draft carried the BITONAL-era figures
      (`0FH`, `0FJ`, `0FL`), though `0GH` had re-measured on the NLI build the same day.
      Re-run today on the corpus as it stands, `measure_against_reviewed.py` and
      `measure_correction_overlap.py` over the 100 reviewed entries (13,735 words):
      | claim | draft | today |
      |---|---|---|
      | our read vs their corrected text | 84.0% words, 95.6% chars | **95.1% words, 98.8% chars** |
      | their edits | 118: 107 corrections, 11 citations | **114: 90 letter corrections, 15 citations, 7 division, 2 bracketed** |
      | corrections our text already holds | 82 of 107 | **78 of 90** |
      | our shared error | `במינוי` | **`גרמה` (root `אכף`) - and the page prints the shared reading `גמרה`** |
      | disagreement surface | 1,054 positions, 7.7%, 87% of errors | **697 positions, 5%, 89 of 90 corrections** |
      | nun/gimel | "gimel read as nun ~9x more often" | **88 -> 6 errors, from the scan change** |
    * **Kept and re-verified:** all citation figures against `citation_corrections.csv` -
      146 rows (92 misprint, 73 of them single-letter; ה/ח 31, ב/כ 16, כ/נ 4, ב/ג 4, ו/ז 3;
      36 edition numbering: Jeremiah 31 x17, I Samuel 24 x8, Exodus 20 x7, I Chronicles 12
      x4; 16 off-by-one; 1 wrong proposal; 1 unclear), every row checked by eye; `ההגעה` is
      still in root `אל`. **Kept NOT re-run:** 20,450 citations, 66% confirmed, 158 flagged,
      18 inside the hundred with 27 suspect words, and the four verse questions (`0FM`,
      about their data, which no corpus change touches); the majority-vote finding (`0FN`)
      is kept as a principle with its old-engine numbers removed.
    * **Added:** the two other places `0GH` read on the ink where the page matches our
      reading against their correction (`הוא` under `איד`, `וזה` under `אם`), a Sefaria link
      on every biblical reference, the greeting for the days between Rosh Hashanah and Yom
      Kippur, and a line about tomorrow's call.
    * **Removed:** "not in my favour", "I am not going to dress that up", "the honest
      answer ... is no", "Not that my read is good - it isn't", "I should warn you ... it
      fails", "the bias is mine", "I owe you an accurate account", "If I had told you ... I
      would have been wrong", "this is not a distraction" - each replaced by the fact it was
      guarding, stated plainly.

0HS. **[2026-09-16, reviewer: "show me all these can't leave loose ends. i want to
    apply those 40 times 2 decisions I made ... if I decided on a change we need to
    apply it"] EVERY RULING NOW ACCOUNTED FOR: THE APPLIER, THE PUNCTUATION APPLIER
    AND THE WITNESS PATH REPORT NOTHING PENDING, AND THE AUDIT REPORTS 0
    MISMATCHES (IT WAS 2).**
    * **The 80 ink readings (`0HN`, `0HP`).** Each mapped to its corpus word and
      compared with the text as it stood: 65 already agreed, 3 were can't-tell,
      **12 still differed and are now applied** - `וכר`->`ובר` (23/304),
      `ברק`->`בדק` (26/15), `רס"יז`->`רמ"ז` (30/307), `סע"כ`->`מע"ב` (30/317),
      `התכוננות`->`התבוננות` (30/802), `חזה`->`וזה` (31/69), `היה`->`הוה` (66/176),
      `והלכתי`->`והלכת'` (153/111), `הל"ם`->`הל"מ` (159/721), `שהגיהן`->`שהגיהו`
      (163/348), `וכפלוגתא`->`ובפלוגתא` (167/511), `רעדיות`->`דעדיות` (167/1208).
      Recorded as the reviewer's rulings relayed from this session, each note
      naming its sheet and item; the corpus's own marks kept where the letter
      count agrees.
    * **Klal 211's terminal colon.** The reviewer ruled `בשם התוספות :` and an hour
      later `בשם התוספות`; the later one was applied. **Page 74 prints the colon** -
      read on the ink and present in Document AI's own tokens (`בשם`, `התוספות`,
      `:`) - so the first ruling was carried: klal 211 now ends `בשם התוספות :`.
    * **The 15 the applier had been holding (14 "drifted", 1 refused) were ALL
      copies of rulings already applied** - the same decision recorded at an index
      a later edit then moved, with only one copy landing. **Applying any of the 8
      deletions among them would have deleted a correct word** (`היכי` 39/251, `רב`
      74/417, `נקט`/`לה` 74/442-443, `לעונשין`/`שהם` 209/16-17, the tail of klal
      36, `כ"ה` 22/48), so the guards were right. Closed with `apply_event`s that
      each name the applied twin, after a code check - same text at the same word,
      or the identical ruling within 4 words with its word gone, or one word of an
      applied span deletion: 2 by `tools/close_satisfied_rulings.py`, 13 by
      `scratch/ink_check_0HN/settle_twins.py` (gitignored; every row's note says
      what was verified).
    * **Loose ends the question did not name, found on the way and closed:**
      - **17 accepted punctuation rulings** were already in the text - the `[.]`
        after each heading, inserted with the heading separators - verified by the
        words either side; **3 rejects at klal 1** reverted a 2026-08-10 "e2e test
        accept", and the corpus has no `[.]` there.
      - **32 witness rulings on Yad Malachi** (August's DocAI/Tesseract
        reconstruction queue): every one already reflected - confirmations, and
        changes carried in by later manual rulings at the same words; 1 was
        "unreadable". Closed after the audit's own checker agreed.
      - **Klal 35 w54**: two rulings the re-point tool copied on 2026-09-06 from
        rulings at w44 that had ALREADY been applied (`בספר` removed from `בספר
        שמות`). Lesson 46 exactly. Applying them would delete the `בספר` of `בספר
        ראשון לציון`. The applier already treats them as settled
        (`restates_an_applied_ruling`); nothing to do, and they must never apply.
    * **The audit, taught four shapes it could not see, each tested and
      mutation-checked** (`audit_applied_decisions.py`):
      1. an explicit `supersedes` link from a later APPLIED ruling - a re-point is a
         new row at a new index, and klal 1 w95 `לכו` had been a MISMATCH since
         2026-09-06 though its re-point at w85 holds (this also moved 42 rows from
         "shifted" to "superseded", 88 -> 46);
      2. a witness row older than word positions resolves through its scan box,
         and is UNVERIFIABLE rather than a mismatch when that cannot find it;
      3. a CONFIRMATION of an OCR reading is honoured when the corpus has the same
         letters plus a mark the token could not carry (`וכו`/`וכו'`); changes
         still compare exactly;
      4. rulings are compared in the ASCII mark convention (`0HR`).
    * **A test pinned to the defect, moved to synthetic data** (Lesson 36):
      `test_a_ruling_the_text_pane_cannot_place_is_still_announced` asserted klal
      74's three real stranded rulings were announced, and failed the moment they
      were verified as applied copies and closed. Same behaviour, own corpus; fails
      if the banner is emptied.
    * **Final state, measured:** `apply_reviewer_decisions.py --dry-run` - 0 to
      apply, 0 refused, 0 drifted, 0 witness pending; `apply_punctuation_decisions.py
      --dry-run` - 0; audit - **1,121 checked, 709 confirmed, 0 MISMATCH**;
      `./rebuild_all.sh --skip-vision` with authored files byte-identical; the
      dashboard serves the corrected text in all 10 changed klalim; gate 584 passed.

0HR. **[2026-09-16, reviewer: "change to ascii everywhere"] DONE FOR PART 1,
    AND FOR EVERY RULING FROM NOW ON. PART 3'S ONE WORD LEFT, BY THE GATE.**
    * **Swept first.** Non-ASCII quote-like characters (gershayim, geresh,
      curly quotes, modifier/prime marks) in `clean_text` and `title` of every
      corpus: **Part 1: 5 `״` + 5 `׳`, in 10 words. Part 2: none. Part 3: one
      `׳`** (klal 575 w118 `ס׳`). **Sefer HaShorashim: none.** No title carried
      one.
    * **The 10 Part 1 words, through the decision pipeline** - one
      `manual_correction` each, letters unchanged, recorded as the reviewer's
      ruling relayed from this session (`actor` `r-eric`, `via`
      `claude-code-session`, the instruction quoted in the note), dry run, apply,
      audit, `./rebuild_all.sh --skip-vision`: `נ״ד` (2/316), `הנז׳` (4/131),
      `מה׳` (88/622), `דב״מ` (128/949), `בפ״ק` (150/293), `בס״פ` (150/533), `מ״ו`
      (154/506), `בפ׳` (159/879), `כ׳` (187/213), `להתוס׳` (216/137) - each now
      ASCII. Diffed: 10 words changed, every one only in its mark. **0 Hebrew
      marks left in `part1.json`; the dashboard serves the ASCII form at 10 of
      10 and 0 Hebrew marks across klalim 1-222.** Authored files byte-identical
      across the rebuild; gate 581 passed; all three dashboards restarted
      (`corpus_io.py` and `review_decisions.py` changed).
    * **From now on, at the write.** `cio.ascii_marks()` is applied to
      `chosen_text` inside `review_decisions.append_decision` - the one place the
      six dashboard routes and every tool pass through - so a Hebrew keyboard
      cannot put `״`/`׳` into the corpus by any route. `original_word` in the
      snapshot is NOT touched: it is the drift anchor and must match the corpus
      as it stands. Test
      `test_a_ruling_is_recorded_with_ascii_abbreviation_marks`, which fails with
      the normalisation removed. The existing ledger is append-only and was not
      rewritten; old rows keep what was typed.
    * **Part 3's `ס׳` was NOT changed.** Applying any `part2.json`/`part3.json`
      edit needs its own explicit go-ahead under the Parts 2-3 gate, and that
      text is slated to be discarded and redone. Say the word and it is one
      ruling.
    * **An audit false alarm this exposed, fixed.** Normalising `להתוס׳` at
      216/137 made `audit_applied_decisions.py` report a new MISMATCH (2 -> 3) on
      an OLDER applied ruling that wrote the two-word span `ראיתי להתוס׳` at
      216/136: supersession was looked up only at a ruling's own start index. The
      corpus was right. `overtaken_inside_span()` now treats such a ruling as
      superseded ONLY when every differing word in its span carries a later,
      APPLIED replacement ruling at exactly that word whose text the corpus now
      holds. Test `test_the_audit_sees_a_later_ruling_inside_an_earlier_multi_word_span`
      fails under three mutations (an unapplied later ruling counting, the later
      text not checked against the corpus, one explained word being enough).
      Audit back to the 2 known mismatches.

0HQ. **[2026-09-16, reviewer: "apply my decisions to the corpus"] 26 RULINGS
    APPLIED, 25 WORDS CHANGED IN PART 1, VERIFIED ON THE DASHBOARD. AND A MARK
    CONVENTION QUESTION FOR THE REVIEWER.**
    * **What was applied.** The reviewer's own dashboard rulings of 15:07-15:26
      UTC today - 18 disputed choices (one a confirmation) and 8 manual
      corrections - covering all 7 of `0HN`'s unsurfaced errors, most of its 10
      queued ones, and nearby words. `apply_reviewer_decisions.py`, dry run
      first: it would apply exactly those 26 and nothing older.
    * **The corpus diff, word by word:** 25 words, no word-count change, no
      heading touched: `לכו`->`לבו` (94/374), `שארירת`->`שארית` (97/353),
      `רב"ט`->`דב״מ` (128/949), `ומ"ס`->`ומ"מ` (133/30), `ותקשי`->`דתקשי`
      (147/288), `כסר`->`כמר` (147/423), `בס"ק`->`בפ״ק` (150/293), `שמיען`->`שמיע`
      (150/344), `בס"ס`->`בס״פ` (150/533), `מקטי`->`מקמי` (150/684), `שרוא`->`שהוא`
      (150/797), `בתלמור`->`בתלמוד` (150/802), `לא`->`אלא` (151/7),
      `ואיכא`->`ואליבא` (151/69), `דרא`->`דהא` (152/47), `שכרתבו`->`שכתבו`
      (152/58), `בסרק`->`בפרק` (152/98), `וכי`->`הכי` (152/115), `ט"ו`->`מ״ו`
      (154/506), `היכאת`->`היכא` (159/29), `איכא`->`אליבא` (159/57), `בר"ס`->`בר"פ`
      (159/117), `ראשה`->`האשה` (159/163), `לא`->`אלא` (159/808), `בס'`->`בפ׳`
      (159/879). 8 open flags closed by the applies; word ids reconciled in 10
      klalim.
    * **Checked, not assumed:**
      - `audit_applied_decisions.py`: 1,031 checked (was 1,005), 648 confirmed
        (was 622) - +26 each, exactly these. MISMATCH unchanged at the 2 known.
      - `./rebuild_all.sh --skip-vision` (the Gemini re-verification step
        skipped), gate 579 passed. `part1-3.json`, `word_identity.json` and
        `review_decisions.jsonl` byte-identical before and after the rebuild.
      - The dashboard serves the corrected word at **25 of 25**, with 0 open
        machine rows left on them (Lesson 33: done when the screen shows it).
    * **Left as they were, by the applier's own guards** (older rulings, not
      today's): 14 drifted (36/108, 39/251, 74/417, 74/442, 74/443, 159/10,
      161/289, 174/116, 200/145, 206/2, 209/16, 209/17, 211/73, 216/123) and 1
      refused for a word-count mismatch (22/48). 20 `punctuation_choice` rulings
      are pending too; they go through `tools/apply_punctuation_decisions.py`,
      which was not asked for and not run.
    * **THE MARK CONVENTION - A QUESTION, NOT A FIX.** Five of the manual
      corrections were typed with the Hebrew gershayim/geresh characters (`״`
      U+05F4, `׳` U+05F3) where the corpus writes ASCII `"` and `'`: across all
      three files, **22,946 `"` and 10,386 `'` against 1 `״` and 5 `׳`** before
      today. They were applied exactly as ruled: `manual_correction` means a
      person ruled (`review_decisions.append_decision` refuses it from anything
      else), so rewriting the reviewer's text is not a tool's call.
      **Swept:** 10 words in Part 1 now carry a Unicode mark -
      <http://127.0.0.1:8420/entry/2/word/316> `נ״ד`,
      <http://127.0.0.1:8420/entry/4/word/131> `הנז׳`,
      <http://127.0.0.1:8420/entry/88/word/622> `מה׳`,
      <http://127.0.0.1:8420/entry/128/word/949> `דב״מ`,
      <http://127.0.0.1:8420/entry/150/word/293> `בפ״ק`,
      <http://127.0.0.1:8420/entry/150/word/533> `בס״פ`,
      <http://127.0.0.1:8420/entry/154/word/506> `מ״ו`,
      <http://127.0.0.1:8420/entry/159/word/879> `בפ׳`,
      <http://127.0.0.1:8420/entry/187/word/213> `כ׳`,
      <http://127.0.0.1:8420/entry/216/word/137> `להתוס׳` - and one in part3.json
      (klal 575 w118 `ס׳`, gated, untouched). Letter-level tools strip marks, so
      alignment and the detectors are unaffected; the deliverable text is what
      carries two spellings of one printed mark. The Unicode characters are the
      typographically correct ones, so the choice is real: re-rule these 10 to
      ASCII, or adopt Unicode as the convention (33,000 existing marks to
      convert, through the pipeline). Either way the dashboard's input will keep
      producing whichever the reviewer's keyboard types until one is chosen.
      **DECIDED THE SAME DAY: ASCII. Done for Part 1 and enforced at the write -
      see `0HR`.**

0HP. **[2026-09-16, reviewer: "ok" to a second blinded sheet] SHEET 2 PUBLISHED:
    THE 189 UNSURFACED FULL-TONE CANDIDATES, STRATIFIED. SCORING WAITS ON THE
    REVIEWER.**
    * **Design, fixed before any answer.** From `0HO`'s 189: **all 13** whose
      corpus reading is not a lexicon word (a census, not a sample) plus a
      **random 27 of the other 176** (seed `20260917`). Page order; strata not
      shown. Each item: the word cropped from both scans, the corpus reading and
      the full-tone reading as A and B in a per-item random order. Key held back
      in `scratch/ink_check_0HN/sheet2/key.json` (gitignored); builder beside it.
      Every row was asserted against the candidate file before cropping (corpus
      reading = bitonal token text, full-tone reading = full-tone token text).
    * **The sheet:** <https://claude.ai/artifact/6VPXzpZFdpb8N9yX3uuGSD>, answers
      saved to its own store as sheet 1 did.
    * **What it will measure.** Two numbers, never pooled: (1) the 13 as plain
      counts - how many are real errors; (2) on the 27, the share where the ink
      agrees with FULL TONE among A/B picks, with a 95% interval, as the estimate
      for the 176 - reported inconclusive if the interval straddles an even split.
      Neither and can't-tell reported, not dropped.
    * **SCORED 2026-09-16. THE SELECTION EFFECT `0HO` PREDICTED IS REAL, AND
      LARGE: ON THE UNFLAGGED REMAINDER THE CORPUS IS USUALLY RIGHT.**

      | | full tone right | corpus right | neither | can't tell |
      |---|---|---|---|---|
      | census, 13 (corpus reading not a word) | 4 | 6 | 2 | 1 |
      | random 27 of the other 176 | 4 | 19 | 2 | 2 |

      **On the 27: full tone 4 of 23 settled = 17.4%, 95% Wilson 7.0-37.1%** -
      the whole interval is below an even split, so by the stated rule this is
      conclusive, and the OPPOSITE of sheet 1's 85.7% at all disagreements. Review
      and the existing detectors had already caught most of what full tone would
      fix; what they left behind is mostly full tone misreading a good word
      (`באבל`->`באכל`, `עד`->`ער`, `לקדמון`->`לקרמון`, `ושמרת`->`זשמרת`). Even
      the "corpus reading is not a word" census is only 4 of 13 for full tone -
      the lexicon lacks forms such as `אהדורי` and `דמפומייהו`, which is Lesson 49
      on the other side of the ledger.
    * **11 real corpus errors found, none in the queue, none applied:**
      - full tone reads the ink:
        <http://127.0.0.1:8420/entry/23/word/304> `וכר` -> `ובר`,
        <http://127.0.0.1:8420/entry/26/word/15> `ברק` -> `בדק`,
        <http://127.0.0.1:8420/entry/30/word/802> `התכוננות` -> `התבוננות`,
        <http://127.0.0.1:8420/entry/31/word/69> `חזה` -> `וזה`,
        <http://127.0.0.1:8420/entry/66/word/176> `היה` -> `הוה`,
        <http://127.0.0.1:8420/entry/163/word/348> `שהגיהן` -> `שהגיהו`,
        <http://127.0.0.1:8420/entry/167/word/511> `וכפלוגתא` -> `ובפלוגתא`,
        <http://127.0.0.1:8420/entry/167/word/1208> `רעדיות` -> `דעדיות`;
      - neither reading, the page prints the reviewer's:
        <http://127.0.0.1:8420/entry/30/word/307> `רס"יז` -> `רמ״ז`,
        <http://127.0.0.1:8420/entry/30/word/317> `סע"כ` -> `מע״ב`,
        <http://127.0.0.1:8420/entry/153/word/111> `והלכתי` -> `והלכת׳`.
      Entry 30 holds three of them. Can't tell: 30/1009, 118/41, 150/260.
      <http://127.0.0.1:8420/entry/194/word/189> `הל'` against printed `הל׳` is an
      apostrophe for a geresh, a representation question rather than a misread.
    * **Totals for the day, unsurfaced corpus errors confirmed on the ink: 18** -
      sheet 1's 7 and these 11.
    * **Do not queue the remaining 149 untested rows.** At a 7-37% yield they
      would put roughly 110-140 correct words in front of a reviewer to find
      perhaps 25-35 errors, which is how the 1,496-flag queue happened (Lesson
      49). They stay in `fulltone_candidates_part1.json` as a record.
    * **What this says about full tone for Part 1.** It is the better image to
      ADJUDICATE with (sheet 1), and its whole-Part-1 pass has now been mined:
      review had already absorbed most of its value. The case for it is
      strongest on text that has NOT been reviewed - which is Parts 2-3, still
      gated.

0HO. **[2026-09-16, reviewer: "then do the full docai"] ALL OF PART 1 READ BY
    DocAI FROM BOTH SCANS. 367 PLACES THE CORPUS HOLDS THE BITONAL READING AND
    FULL TONE READS OTHERWISE; 189 SURFACED NOWHERE. AND `0HN`'S 86% DOES NOT
    TRANSFER TO THEM.**
    * **The run.** Pages 14-76 (klalim 1-222), DocAI `eu` `bc652834c231f24e`, on
      the bitonal scan and on the full-tone NLI scan; 40-59 reused from `0HM`,
      the other 43 pages per scan new, no failures. Page mapping re-verified
      before spending at 14, 25 and 76 (nine points in all, end to end).
      Layers gitignored: `docai_bitonal_layer/`, `docai_fulltone_layer/`.
    * **The sweep** (`scratch/ink_check_0HN/part1_sweep.py`): the two layers
      aligned to each other and the bitonal layer to `part1.json` (99.2% of its
      tokens aligned). **889** one-word-for-one-word disagreements:
      - **412** - the corpus already holds the full-tone reading;
      - **367** - the corpus still holds the BITONAL reading;
      - 74 - the corpus holds a third reading; 36 - not on a corpus word
        (running heads, apparatus).
      **All 367 are in `fulltone_candidates_part1.json`** with dashboard URL,
      page, both readings and the full-tone box. Every one was checked against
      the word the dashboard serves at that address: 0 mismatches.
    * **Surfaced or not, from the LIVE dashboard** - not the queue file, which
      my first count read and got wrong: it showed 0 queued where the
      dashboard serves 163 (Lesson 33, state not printout; caught before
      reporting):

      | state | rows |
      |---|---|
      | **surfaced nowhere** | **189**, across 84 klalim |
      | already queued | 163 (143 `current_text_may_be_wrong`, 9 `ai_flag`, 7 `manual_correction`, 4 `current_text_confirmed`) |
      | a human already ruled - and kept the bitonal reading | 15 |

      The 15 are a useful check on full tone: `בל'`/`בלי`, `להו`/`להן`,
      `אבל`/`אכל`, `נזכר`/`נוכר` - several full-tone readings there are plainly
      wrong, which is the ~14% `0HN` measured.
    * **DO NOT APPLY `0HN`'S 85.7% TO THE 189** (Lesson 27, THE SAMPLE THAT
      SELECTED ITSELF). That sample was drawn from ALL disagreements. The 189
      are what is LEFT after human review and every detector has had its pass,
      and those passes catch the obvious case - a bitonal reading that is not a
      word. So the remainder is enriched for the opposite. Measured with
      `lexicon.txt`, a triage signal and not a verdict (Lesson 49):

      | | corpus reading only is a word | full-tone reading only is a word | both | neither |
      |---|---|---|---|---|
      | 189 surfaced nowhere | **81** | **6** | 95 | 7 |
      | 163 already queued | 14 | 34 | 108 | 7 |

      A random 8 of the 189 looks the same way: `דהוי`/`דחוי`, `הרי`/`חרי`,
      `אהדורי`/`אהרורי` read as the corpus being right; `ארבא`/`ארכא` and
      `בחד`/`בחר` are open. **The yield on the 189 is unknown and very likely
      well under 86%.** It needs its own blinded ink read before it is a
      worklist. The highest-yield slice is the 13 where the corpus reading is
      not a word (6 full-tone-word-only, 7 neither).
    * Nothing applied, nothing added to the queue. Cost: 86 new pages, cents.

0HN. **[2026-09-16, reviewer: "yes" to a 40-word ink sample] THE BLINDED
    READING SHEET IS PUBLISHED. SCORING WAITS ON THE REVIEWER'S 40 PICKS.**
    `0HM` left DocAI's scan question unsettled because both available
    references are biased, in opposite directions. The unbiased reference is
    the ink, read by a person, at places where the two readings differ.
    * **Population: 292** one-word-for-one-word places, over pages 40-59, where
      DocAI (`eu` `bc652834c231f24e`) reads the bitonal Google scan and the
      full-tone NLI scan differently - aligned on the two layers' own tokens,
      so every item carries a box in each image (`0HM` counted 290 from plain
      text; the token route finds 292). **Sample: 40**, `random.sample` with
      seed `20260916`, shown in page order.
    * **Blinded.** Each item shows the word cropped from BOTH scans, boxed, and
      two readings labelled A and B **in a per-item random order**. The page
      never carries which reading came from which scan; that key is held back
      in `scratch/ink_check_0HN/ink_key.json` (gitignored). **Do not open it
      before the sheet is read.** Differing letters are highlighted, which
      directs attention without revealing the source.
    * **Crops checked before publishing**, on three items: the box sits on the
      same word in both images, and context was widened after the first look
      because a short word at a line's end left too little of its neighbours
      (Lesson 14).
    * **The sheet:** <https://claude.ai/artifact/MZhyUVSikmgKVuEQM5oC3d>. Answers
      save per item to the artifact's own store (`answers/<item id>`), so they
      are read back without being transcribed; if a view cannot save, the page
      shows a one-line summary to paste instead. Choices: A, B, Neither (with an
      optional "what the page prints"), Can't tell.
    * **What it will measure**, stated before the answers exist so the reading
      cannot be fitted to them: of the items the reviewer settles as A or B,
      the share where the FULL-TONE reading matches the ink, with a 95%
      interval. Neither and Can't-tell are reported, not dropped. At n=40 an
      even split and a 70/30 split are distinguishable; 55/45 is not, and will
      be reported as inconclusive rather than as a lean.
    * **Reproducible without the scratchpad:** `build_ink_sample.py` beside the
      key regenerates the same 40 from the two gitignored layers and the seed.
    * **SCORED 2026-09-16, after the reviewer read all 40. FULL TONE, AND IT IS
      NOT CLOSE.** Answers read back from the sheet's store, then unblinded
      against the key, by the rule written above before any answer existed:

      | the ink agreed with | items |
      |---|---|
      | DocAI on FULL TONE | **30** |
      | DocAI on BITONAL | 5 |
      | neither | 5 |
      | can't tell | 0 |

      **Full tone 30 of 35 settled = 85.7%, 95% Wilson interval 70.6-93.7%.**
      The lower bound is far from an even split, so by the pre-stated rule this
      is conclusive: where DocAI reads the two scans differently, the full-tone
      reading is the right one about six times in seven. This also confirms
      `0HM`'s diagnosis - DocAI-bitonal won the whole-text score only because the
      reference is its own unreviewed output.
      - **All 5 "neither" are ONE error, and neither scan fixes it**: the
        alef-lamed ligature losing its `ל` - the page prints `ישראל`, `אליבא`
        (twice), `ולשמואל`, `אלא`. Lesson 24, SHARED INK, SHARED ERROR, exactly:
        the defect is in the sort, upstream of the scan.
      - The 5 bitonal wins: `ובירושלמי`, `כיס`, `הוי`, `ממיפך`, `בב"י`.
      - **Extrapolation, labelled as one:** at these rates, of the 292
        disagreements on these 20 pages full tone is right at ~219 and bitonal
        at ~37 - a net ~180 words, about 1.2 points of the 14,866. Not measured.
    * **AND THE SAMPLE FOUND LIVE DATA ISSUES IN THE REVIEWED THIRD.** Each of the
      40 positions was mapped onto `part1.json` (40 of 40 mapped; every served
      word matched the bitonal reading string-for-string, e.g. `שארירת`, `כסר`,
      `שרוא`, which does not happen by accident) and compared with the reviewer's
      ink reading. **The corpus disagrees with the ink at 17 of 40.**
      - **10 are already open** in the queue as `current_text_may_be_wrong`,
        awaiting a ruling:
        <http://127.0.0.1:8420/entry/94/word/374> `לכו` (ink `לבו`),
        <http://127.0.0.1:8420/entry/97/word/353> `שארירת` (`שארית`),
        <http://127.0.0.1:8420/entry/133/word/30> `ומ"ס` (`ומ"מ`),
        <http://127.0.0.1:8420/entry/147/word/288> `ותקשי` (`דתקשי`),
        <http://127.0.0.1:8420/entry/147/word/423> `כסר` (`כמר`),
        <http://127.0.0.1:8420/entry/150/word/344> `שמיען` (`שמיע`),
        <http://127.0.0.1:8420/entry/150/word/797> `שרוא` (`שהוא`),
        <http://127.0.0.1:8420/entry/152/word/115> `וכי` (`הכי`),
        <http://127.0.0.1:8420/entry/159/word/117> `בר"ס` (`בר"פ`),
        <http://127.0.0.1:8420/entry/159/word/721> `הל"ם` (`הל"מ`).
      - **7 are surfaced NOWHERE** - no queue row, no flag:
        <http://127.0.0.1:8420/entry/128/word/949> `רב"ט` (ink `דב"מ`),
        <http://127.0.0.1:8420/entry/150/word/293> `בס"ק` (`בפ"ק`),
        <http://127.0.0.1:8420/entry/150/word/533> `בס"ס` (`בס"פ`),
        <http://127.0.0.1:8420/entry/154/word/506> `ט"ו` (`מ"ו`),
        <http://127.0.0.1:8420/entry/159/word/57> `איכא` (`אליבא`),
        <http://127.0.0.1:8420/entry/159/word/808> `לא` (`אלא`),
        <http://127.0.0.1:8420/entry/159/word/879> `בס'` (`בפ`).
        Four are abbreviations (`ס`/`פ`, `ט`/`מ`, `ר`/`ד` inside a gershayim
        form) and two are the alef-lamed ligature. **Not swept to the class yet**:
        the 7-in-40 rate is a sample from DISAGREEMENT positions only, so it
        cannot be scaled to the corpus; the sweep is the full 292 compared against
        `part1.json`, and beyond these pages, a full-tone DocAI pass.
      - These are the reviewer's readings off the crops; nothing was applied.

0HM. **[2026-09-16, reviewer: "yes" to running the controlled comparison] FULL
    TONE WINS ON YAD MALACHI TOO - BY A TENTH OF WHAT IT WON ON HaSHORASHIM.
    +0.33 POINTS OF WORDS, NOT +3.0.**
    `0FW`'s protocol, on this book: one engine, one set of pages, only the
    pixels differ. Cloud Vision (no processor to provision, can be pointed at
    either scan), pages **40-59**, scored against `part1.json` klalim **90-162**,
    **14,866 reference words**. 40 API calls, about six cents.

    | source | words | CER | lexicon hit |
    |---|---|---|---|
    | Cloud Vision, BITONAL (Google, rendered 400 dpi, 2304x3552) | 0.9680 | 0.01556 | 0.9612 |
    | Cloud Vision, FULL TONE (NLI text crop, 1400x2325) | **0.9713** | **0.01462** | **0.9633** |

    **+0.33 points of words** - 49 more of 14,866 - and 6% relatively less
    character error. Compare HaShorashim, same protocol: **+3.0** with Cloud
    Vision (`0FW`) and +2.9 with DocAI (`0FZ`).
    * **Where the gain is, and where it is not.** Stroke-shape confusions, the
      class thresholding destroys, improve: `ד->ר` 52 -> 38 (-27%), `ב->כ`
      27 -> 17 (-37%), `ו->ן` 65 -> 56 (-14%). Dropped and unrelated letters do
      not: `ל->∅` 49 -> 53, `ס->פ` 15 -> 25. **The `ד->ו` 24 -> 0 and `ר->ד`
      0 -> 22 rows are NOT real zeroes** - each engine's list is its own top 8,
      so absence there means "outside its top 8", not "never happened".
    * **Why the gain is so much smaller here, most likely.** On this book the
      bitonal copy is far better than HaShorashim's: 2304x3552 rendered against
      the full-tone crop's 1400x2325, about 1.6x the linear resolution. Yad
      Malachi's thresholded scan is simply a good one, so there is less for tone
      to recover.
    * **The bias runs AGAINST full tone, so +0.33 is a floor, not a point
      estimate.** `part1.json` was built from the bitonal scan and reviewed
      against it, so the ground truth agrees with that source by construction.
      HaShorashim's measurement used Sefaria's independently reviewed text and
      had no such tilt. This is the one asymmetry that would make the true gain
      larger than measured, and there is no way to remove it without an
      independent transcription of these pages.
    * **This is not yet the run that decides anything.** `0FZ` established that
      the combination that matters is **DocAI** on the full-tone images - DocAI
      is the corpus engine and beats Cloud Vision by several points on running
      text. `tools/ocr_pages_docai.py` is written and waiting.
      **BLOCKED ON A VALUE NOBODY WROTE DOWN**: `DOCAI_PROCESSOR`. The service
      account holds `roles/documentai.apiUser`, which grants processing but not
      `processors.list` (`0FY`), so the id cannot be recovered by asking the API
      - and it appears in no file in this repo, either corpus root, `.envrc`, or
      the shell history. The processor that produced HaShorashim's
      `nli_docai_layer` exists; only its id is missing. That is Lesson 32's
      shape applied to configuration: a paid, reproducible run whose settings
      live in one person's shell has to be re-derived to repeat.
    * **Artifacts.** `ocr_scan_source_comparison_yad.json` (tracked). The two
      page layers are gitignored: `cv_bitonal_layer/`, `cv_fulltone_layer/`,
      20 pages each, written page by page as they arrived.
    * **The page mapping was verified before spending** (Lesson 30): Google page
      N = NLI image N-1, checked by reading the running head, folio and opening
      words at Google 36, 37, 38, 40, 59 and 100 - six points, including both
      ends of the sample window and both sides of the transposed leaf.
    * **ADDED THE SAME EVENING: THE DocAI RUN, AND IT DOES NOT HAVE ONE ANSWER.**
      **The processor id** was not the number first supplied -
      `112964197445881461354` is the `doc-ai-worker` service account's
      `client_id` in `credentials.json`, a 21-digit number the console shows
      prominently. The real ids were listed through the reviewer's own gcloud
      login (the service account cannot list):
      **`eu` `bc652834c231f24e` `shorashim-ocr`** and **`us` `4d3d4f204562f1d6`
      `hebrew-ocr`**, both `OCR_PROCESSOR`, both enabled. The `us` one is almost
      certainly the original corpus processor. Recorded HERE so the next run
      does not re-derive them. Run on `eu` for both scans, per the region choice.
      Also: `gcloud documentai` does not exist in this installation - the command
      I suggested for listing processors was wrong; the REST endpoint is the
      route.

      | source, pages 40-59, klalim 90-162 | words | CER | lexicon |
      |---|---|---|---|
      | Cloud Vision, bitonal | 0.9680 | 0.01556 | 0.9612 |
      | Cloud Vision, full tone | 0.9713 | 0.01462 | 0.9633 |
      | DocAI, bitonal | **0.9810** | **0.01199** | 0.9627 |
      | DocAI, full tone | 0.9783 | 0.01214 | **0.9649** |

      **On the whole text, DocAI reads the BITONAL scan better, by 0.27.** And
      that number cannot be taken at face value, because `part1.json` IS
      DocAI-on-bitonal wherever no human intervened: every error it made that
      review did not catch now scores as correct.

      **So the same four runs were scored only at the 79 words a human
      corrected** in klalim 90-162 (text-changing, one word for one word,
      verified still in place) - the places where the ink was checked:

      | engine / scan | reads the ruling | repeats the corrected error | other |
      |---|---|---|---|
      | Cloud Vision, bitonal | 24 (30%) | 32 (41%) | 23 |
      | Cloud Vision, full tone | **33 (42%)** | **26 (33%)** | 20 |
      | DocAI, bitonal | 17 (22%) | 53 (67%) | 9 |
      | DocAI, full tone | **31 (39%)** | **36 (46%)** | 12 |

      **With DocAI, full tone reads the human's correction 31 times to
      bitonal's 17, and repeats the error 36 times to 53.**

      **THAT SUBSET IS BIASED TOO, THE OTHER WAY** (Lesson 27, THE SAMPLE THAT
      SELECTED ITSELF): these rulings exist because DocAI-on-bitonal got these
      words wrong, so it is disadvantaged on them by construction. The two DocAI
      measurements therefore point in opposite directions and **each is biased
      in exactly the direction it points** - neither settles DocAI.
      **Cloud Vision is the fair witness**, because it had no hand in building
      the corpus or choosing the rulings, and on BOTH measures it prefers full
      tone: +0.33 on the whole text, 33 vs 24 at the corrected words.

      **What would settle DocAI:** a reference that neither scan produced. The
      cheapest one is already enumerated - DocAI reads the two scans identically
      on 98.0% of tokens and **disagrees at 312 places, 290 of them one word for
      one word**, over these 20 pages. Reading a sample of those 290 off the ink
      is the unbiased answer, and it is also exactly the worklist `0EK` proposed
      full tone for: the adjudication image, not the primary.

0HL. **[2026-09-16, reviewer: "dropped the better scan into yad mal"] THE
    FULL-TONE YAD MALACHI IS HERE AND MEASURED. AND THE LEAF-FIX RECIPE
    `START_HERE.md` GIVES FOR AN NLI SOURCE IS WRONG - RUNNING IT WOULD BREAK
    THIS DOWNLOAD.**
    * **What arrived**, `~/work/yad-malachi/yad-malachi-pipeline/scans/dedupmrg1254702642_IE85912636/`
      (note the location: that is the OLD pre-migration clone, not the live
      tree this pipeline runs from):
      - **336 JPEGs, 332 greyscale and 4 RGB** (images 1, 284, 335, 336 - boards
        and a colour target). Median **4.6 MP**, range 4.4-5.4, ~1755x2655.
      - That is the `JPEG\ZIP + Maximal (100%)` tier `0HJ` predicted at
        1745x2658 / 4.6 MP, and **four times** the 1.16 MP copy already in
        `nli_verification/`. The EXIF dpi tag reads 72, which is a JPEG default
        and not a measurement; ~2655 px over a ~9-inch leaf is ~295 dpi,
        consistent with the 300 dpi NLI confirmed this week.
      - **Genuine continuous tone**: 256 grey levels in use on a body page.
        Midtones are 7.2% of pixels against HaShorashim's 45.7% (`0EC`) - a
        cleaner, higher-contrast scan, not a thresholded one. Whether that is
        enough to help is `0FW`'s experiment, not a claim to make here.
    * **The page mapping, verified against CONTENT at four points** (Lesson 30),
      not against plausibility: **Google page N = NLI image N-1.** Checked at
      Google 36, 37, 38 and 100 by reading the running head, the folio and the
      opening words off the crop - e.g. Google 100 opens `ע"ח ב' ד"ה והתנן
      ובסוכה` and so does NLI image 99. A whole-page pixel correlation was tried
      first and is USELESS here (0.14-0.44, offsets inconsistent): one source is
      1-bit and the other greyscale, with different margins.
    * **THE FINDING: the transposed leaf is the GOOGLE copy's defect alone, and
      `START_HERE.md` told you to "fix" the NLI copy too.** The correct sequence,
      read off the ink, is folio `יב` opening `אמר רבא`, folio `יב` opening
      `פתחון פה`, folio `יג` opening `דמדקאמר` - a recto/verso pair sharing a
      folio number, then the next leaf.
      - **The new JPEG\ZIP set reads exactly that**, at images 35, 36, 37.
      - **So does the August NLI PDF**, at 0-indexed 34, 35, 36 - read directly,
        not inferred. Two independent NLI acquisitions agreeing (Lesson 9).
      - `nli_verification/berlin_square_corrected.pdf` differs from the raw
        download at **exactly two pages, 0-indexed 35 and 36, which are
        swapped** (rendered-page hashes over 33-40: identical everywhere else).
        That swap is the documented NLI command, and it turns the correct order
        into the wrong one. **The file whose name says `corrected` is the
        mis-ordered one.** Kept, because it is the evidence.
      - The wrong command came from the 1-page count difference between the two
        sources rather than from the leaves, while the doc described it as
        "verified ... by direct content inspection against a fresh NLI
        download". `START_HERE.md` is corrected and `DOCS-HISTORY.md` records
        the removal.
    * **Not wired into anything, deliberately.** `0EK`'s conclusion still
      governs: use a tonal scan as the ADJUDICATION source - the image the
      vision adjudicator crops from - while OCR continues on the existing scan,
      because every page-indexed cache in this repo is keyed to the Google
      337-page numbering and switching primary means rebuilding all of them.
      With the mapping above that is a one-line lookup, not a migration.
    * **The experiment this unblocks** is `0FW`'s, run on Yad Malachi: one
      engine, one set of pages, only the pixels differ. On HaShorashim it gave
      +3.0 points of word accuracy, +2.0 of characters and nun/gimel errors
      39 -> 8. Nothing has been run here yet.

0HK. **[2026-09-16, reviewer: "fix the root split now"] EACH HOMOGRAPH ENTRY IS
    SERVED ITS OWN HALF OF THE SHARED TEXT. THE BOOK'S PHANTOM "WORDS ONLY THEY
    HAVE" GOES 1,136 -> 108.**
    This was the other half of the 2026-09-13 code review's finding 3. That
    review fixed `build_witness_disputes.group_disputes` - the entries JOINED,
    aligned once against their one text, each difference mapped back - and gave
    `api_klal_versions` a NOTE instead of a fix, so the endpoint kept serving the
    whole shared text to both halves.
    * **`cio.split_shared_comparison(entry_texts, witness_text)`** aligns our
      entries joined, the same way the dispute builder does, and cuts their text
      at each seam. **It refuses rather than guesses**: unmapped, a first cut at
      0, or two cuts on one word all return None and the caller keeps today's
      behaviour.
      - Aligning each half SEPARATELY is what it must not do, measured: our 178
        mapped to their 0-11 and our 179 to their 0-40, the same words twice.
      - Its key deliberately differs from `build_witness_disputes.text_words`,
        which drops words under two letters. A seam wants every anchor, and with
        the two-letter rule `["אלף 12 בית", "ו גימל"]` against `"אלף בית ו
        גימל"` puts their `ו` in the FIRST slice when it opens the second entry.
        On the five real roots both rules give the same answer, so it is a
        difference of principle today.
    * **`api_klal_versions`** serves the slice and a new `theirs_split`;
      `theirs_covers` still names the sibling, because the reviewer has to know
      the seam was drawn by us. The frontend note now says which they have - a
      slice, or the whole text because the seam could not be found.
    * **Live on :8421, all five roots and a control:**

      | entries | ours | their slices |
      |---|---|---|
      | 72 / 73 | 902 / 138 | 744 / 109 |
      | 122 / 123 | 10 / 19 | 7 / 13 |
      | 178 / 179 | 17 / 35 | 14 / 26 |
      | 185 / 186 | 25 / 20 | 21 / 15 |
      | 313 / 314 | 197 / 34 | 164 / 24 |

      Entry 32, a unique root, is untouched: `theirs_split` false, 187 words as
      before. **The book-wide "a word only they have" falls from 1,136 to 108**,
      and the largest remaining entry holds 16 rather than 811.
    * **FOUR OF FIVE MUTATIONS SURVIVED THE FIRST CUT OF THE TESTS** (Lesson 42),
      and resolving them changed the code twice:
      - Three refusal cases were all caught by the SAME early return
        (`nxt is None`), so the ordering guard and the first-cut guard were
        untested. Both are reachable and now have a case each - and the ordering
        guard needs THREE entries to fire at all, because with two there is one
        cut and nothing for it to be out of order with. What it catches is not a
        DECREASE, which difflib's rising blocks make impossible, but two cuts on
        one word when a middle entry matches nothing.
      - A `cuts[-1] >= len(wit)` guard **could never fire** - every cut is an
        index into `wit`, so the last slice always holds a word. Written, then
        removed (Lesson 25).
      - Dropping our letterless tokens is **inert**, because their side already
        drops them and a letterless key can match nothing. Kept for symmetry and
        SAID to be inert, rather than commented as though it did something.
    * Suites: gate 579 passed; browser 120 passed, 1 skipped. All three
      dashboards restarted (`corpus_io.py`, `review_server.py` and `app.js` all
      changed); no test server survived the browser run.

0HJ. **[2026-09-16] THE NLI CONTACT'S ANSWER ON SCAN SOURCES: 300 DPI IS THE
    CEILING, MASTER INCLUDED. `0FO`'s OPEN REQUEST IS CLOSED, AS UNAVAILABLE -
    AND THE RULING FREEZE IT WAS BLOCKING CAN LIFT.**
    * **The answer, paraphrased** (the repo names correspondents by role):
      printed books are scanned at 300 DPI; the MASTER file is at that same
      quality; the access copy is compressed and loses some detail but is also
      300 DPI.
    * **What it closes.** `0FO` ended "the NLI contact confirms the online copy is
      300 dpi and is asking what the printed-books masters are held at", and
      framed the whole request as the thing that would make pre-processing worth
      doing: "a master that is full-tone AND high-resolution is the only input on
      which the usual pipeline has anything to work with". **That input does not
      exist.** The three sources this project holds are now known to be the whole
      field:

      | scan | pixels | depth | dpi |
      |---|---|---|---|
      | Google Books | 3528x5278 | 1 bpc, bitonal | ~600 |
      | HebrewBooks | 2266x3444 | 1 bpc, bitonal | ~385 |
      | NLI full-tone | ~1843x2890 | RGB | **300, and that is NLI's ceiling** |

      Nothing combines full tone with more than 300 dpi, and nothing will.
    * **We already hold the 300 dpi full tone, at native resolution, for the
      whole slice.** Measured: `page_image_sources.json` records all **94** pages
      58-151 as `nli_fulltone` (69 `PASS`, 25 `TEXT_ONLY` on the offset check),
      and the dashboard images are CROPS of the Rosetta JPEGs, not downsamples -
      page 58 is 1344x1917 cut from an 1843x2890 original whose EXIF declares
      300x300 dpi. The `nominal_dpi: 150.0` in that file describes the base
      HebrewBooks PDF the substitution replaced, not what we read.
    * **The one thing still on the table is compression, and it is small.** Our
      copies are JPEG at **0.81 bits per pixel**, quantization table
      `[6, 4, 4, 6, 10, 16, 20, 24]` - the standard IJG luminance table at
      roughly quality 81. The master would be the same pixel count without that.
      Whether it buys a reading is not measurable without it, and the best
      evidence available says no: `0FQ`'s paired experiment DOUBLED the
      resolution on 66 nun/gimel positions and moved the adjudicator by **net
      -1** (3 wrong->right, 4 right->wrong), at 18% correct on a two-way choice
      either way. Removing JPEG artifacts is a far smaller change than 2x
      resolution.
    * **The consequence for the corpus, and it is the reviewer's call.**
      `0GV` set "no rulings until the NLI contact answers on scan sources" and
      `0GZ` repeated it ("no ruling goes into the real corpus until the scan
      source is settled"). The answer is in and it is a ceiling, so the source we
      are reading is the best full-tone source that exists for this book. The
      freeze has nothing left to wait for. The real ledger is still 0 bytes and
      `--apply-witness-choices` is still off; turning it on remains a separate,
      explicit decision (`0GQ` item 4), and `0HE` findings 2 and 3 are still open
      on that path.
    * **`book.json`'s `versionSource` needs no change.** It already names the NLI
      record (`0GV`), which is the source we are in fact reading.
    * **Cheap parallel ask, if the reviewer wants it:** the uncompressed master
      for the 94 pages of the slice only, not the 656-page book. It costs nothing
      to request and nothing to wait for, since it changes no decision above.
    * **ADDED THE SAME DAY. The reviewer drafted a reply - "it's not a question
      of dpi, I'm looking for a full tone scan instead of a bi-tone scan" - and
      the instinct is right but the book is wrong.** Measured now, from the two
      PDFs in this repo, rather than from `0EK`'s note:
      ```
      berlin_square_corrected.pdf              3456 x 5312   colorspace 1, bpc 1   PNG   (Google Books)
      nli_verification/berlin_square_corrected.pdf   873 x 1329   colorspace 1, bpc 8   JPEG  (NLI)
      ```
      - **Sefer HaShorashim already HAS NLI's full tone**: the Rosetta images are
        24-bit RGB at 300 dpi and all 94 pages of the slice are read from them.
        Asking NLI for a full-tone scan of that book would be asking for what
        they have already supplied.
      - **Yad Malachi is the book with no tone at all.** Its only scan is 1 bit
        per pixel, and NLI's own derivative of it **is 8-bit greyscale** - so the
        continuous-tone source exists and was rejected on 2026-08-18 purely on
        pixel count, which is the decision `0EK` already recorded as made "on an
        axis that omitted" bit depth.
      - **The trade is now fully quantified, because the DPI answer supplies the
        missing half.** 300 dpi on this page is roughly 1800x2900 (~5.2 MP, 8
        bpc) against our 3456x5312 (18.3 MP, 1 bpc): about 3.5x fewer pixels for
        8 bits of tone instead of 1. That is the SAME trade already made on
        HaShorashim, where `0FW` measured it controlled - same engine, same 35
        pages, only the pixels differ - at **+3.0 points of word accuracy, +2.0
        of characters, and nun/gimel errors 39 -> 8, a 79% cut**.
      - So the reply to send asks for the **Yad Malachi** (NLI
        `990011859020205171`) full-tone master at 300 dpi, says explicitly that
        lower resolution than what we hold is acceptable because the tone is
        worth more than the pixels, and carries `0EK`'s other two asks that are
        still unanswered: the redistribution terms, since Sefaria is the
        destination, and the spec before the files.
    * **CORRECTED, same day, on the reviewer's question "so we have it
      already?" - YES, AND THAT CHANGES THE PLAN: the NLI contact is NOT on the
      critical path for Yad Malachi.**
      - `nli_verification/berlin_square_corrected.pdf` **is** an NLI full-tone
        copy of Yad Malachi, already in this repo - but it is the **lowest**
        tier, `PDF + Medium`, 873x1329 = **1.16 MP**, against Google's 18.3 MP.
      - **Looked at, not assumed.** The same printed page rendered from both to
        the same physical size: the 1-bit Google crop resolves the strokes
        cleanly and the 8-bit NLI crop is visibly soft, letters greyed and
        smeared together. Tone at 1.16 MP does not recover what 18.3 MP bitonal
        resolves. **The copy we hold is not a usable substitute and no
        experiment should be run on it.**
      - **The tier that matters was never downloaded for this book.**
        `JPEG\ZIP + Maximal (100%)` is 1745x2658 = **4.6 MP** and is available
        ANONYMOUSLY - four times the pixels of what we hold. That is the exact
        route that produced HaShorashim's full-tone corpus: the reviewer
        downloaded 656 JPEGs, 405 MB, at *complete document + JPEG\ZIP +
        Maximal*, no account and no correspondence.
      - **And it is within a whisker of the master.** 300 dpi on this page is
        ~5.2 MP; the free anonymous tier is 4.6 MP. The only thing the contact
        can add is the absence of JPEG compression.
      - **So the decisive move costs one download and no waiting**: pull Yad
        Malachi at `JPEG\ZIP + Maximal`, then run `0FW`'s controlled comparison -
        one engine, one set of pages, only the pixels differ. The email is worth
        sending for the redistribution terms and the uncompressed master, but
        nothing needs to wait for it.

0HI. **[2026-09-16, reviewer: "I need a list of the ways our scan differs from
    sef... need a complete list so i can discuss if the diffs are intentional
    b/c of policy"] EVERY CLASS, COUNTED, ON TWO BASES. TWO OF THE REVIEWER'S
    OWN TWO EXAMPLES COME OUT DIFFERENTLY THAN EXPECTED.**
    **Method, and the one thing that decides how to read the numbers.** Every
    token-level difference between `master` and Sefaria, classified by a
    normalization ladder (NFKD -> points -> geresh -> brackets -> all
    punctuation -> letters) so each difference is attributed to the layer at
    which it disappears. Run twice: against their **corrected** text (98
    entries - the policy-bearing basis, because their raw OCR carries their own
    errors, `0FD`) and against their **raw OCR** (all 317 - scale, but it mixes
    policy with their mistakes). Our punctuation-only tokens and bare numerals
    are set aside before aligning, or each one turns into a fake word division
    (`0HH`). Maqaf-joined tokens of theirs are split, as our text writes them.

    | class | vs corrected (98) | vs raw OCR (317) | whose choice |
    |---|---:|---:|---|
    | niqqud / cantillation | 3,976 | 10,691 | **theirs** |
    | maqaf-joined tokens | 1,136 | 3,284 | **theirs** |
    | our punctuation as its own token | 937 | 2,790 | ours (DocAI), `0HH` |
    | our footnote numerals inline | 952 | 2,776 | ours, by design |
    | their sentence punctuation glued | 563 | 1,680 | tokenization, `0HH` |
    | geresh inside a letter name | 384 | 1,096 | **theirs - VERIFIED ON THE INK** |
    | plene / defective | 300 | 913 | **not a policy - see below** |
    | letters differ, other | 166 | 797 | real disagreements |
    | brackets | 119 | 395 | mixed, `0GN` / `0HH` |
    | word division | 79 | 472 | mixed |
    | divine name | 35 | 87 | **theirs** |
    | inline source citations | 21 | 3 | **theirs**, corrected layer only |
    | nun / gimel | 8 | 55 | OCR, both sides |
    | a word only we have | 52 | 288 | to check |
    | a word only they have | 54 | 1,136 | see the segmentation note |
    | unicode presentation forms | 0 | 1 | theirs, `0GY` |

    * **Niqqud, sized.** Our 41,873 words carry points on **20**; their 37,293
      carry them on **12,759 (34.2%)**. `0GY` already settled where those come
      from - the Masoretic text, carried in with their verse identification,
      not this printing - and read the ink to prove it. Confirmed policy.
    * **The geresh in letter names is THEIRS, and this is new.** They write
      `האל'ף`, `הבי'ת`, `הגימ'ל`; we write `האלף`, `הבית`, `הגימל`.
      **Read directly off the scan, two headings on two different pages**
      (Lesson 9): page 58 prints `האלף והבית.` and page 147 prints `הגימל והפא
      והנון.` - letterspaced for emphasis, **no geresh in either**. So the mark
      is their editorial addition and our OCR is not dropping anything. Ordinary
      abbreviations agree, which is what makes the class specific rather than
      general: `ר"ל` 110 ours / 107 theirs, `ע"מ` 58 / 61. The whole gap is
      letter names - ours 417 tokens with an internal mark against their 1,768.
      Their convention also SPELLS THE NAME OUT: our `והרש` is their `והרי'ש`,
      our `התו` their `התי'ו`, our `הוו` their `הוי'ו`.
    * **Plene / defective: there is NO normalization policy. The reviewer's
      guess does not survive the measurement, and neither does the example.**
      - `ואיפשר` occurs 12 times in our text. **Sefaria writes `ואיפשר` in 9 of
        them**, `ואפשר` in 2 (entries 32 and 79) and `ואיפשׁר` in 1. The
        reviewer was looking at one of the two exceptions, which is exactly why
        it is in the queue as `C_spelling_vav_yod`.
      - Of the 300 plene differences against their corrected text, **266 (89%)
        are inside a word THEY VOCALIZED** - i.e. inside an imported Masoretic
        quotation, which is `0GY`'s finding again and the same mechanism that
        makes the printed plene `עודנו` come back as `עֹדֶנּוּ`. 22 more are the
        letter-name convention above.
      - **That leaves 12 genuine running-text differences in 98 entries**, and
        several are not spelling at all: `והוא`/`והיא`, `הפסקו`/`הפסוק`,
        `נותנת`/`ניתנת`, `אחית`/`אחות`, `נוספת`/`נוספות`, their `ווזה` for our
        `וזה`. The direction does lean our way (233 plene to their 67), which is
        what an imported Masoretic text would produce on its own.
    * **Divine name.** We write `י"י` 93 times; they write `ה'` 114 times and
      `י"י` 6. A representation choice on their side, not a reading of the ink.
    * **Structural, and it is showing the wrong text in the dashboard today.**
      **We split 5 roots into two entries each where Sefaria has one**:
      `אלה` (72/73), `ארש` (122/123), `בכה` (178/179), `בלה` (185/186), `גרש`
      (313/314). Every one of our 312 distinct roots exists in their 1,974, so
      nothing is unmatched - but both of our halves pair to the SAME Sefaria
      entry, so one of the two comparison panes shows text that does not belong
      to it. **This is 927 of the 1,136 "a word only they have"**: entry 73
      alone accounts for 811 and entry 72 for 116. Entry 73 is ours 138 words
      against the 853 it is being shown.
      - <http://127.0.0.1:8421/entry/73/word/0> ours `האלף והלמד וההא הנראת`,
        shown Sefaria's `האל'ף והלמ'ד והה'א הרפה` - the text of our entry 72.
      - The others to check the same way: <http://127.0.0.1:8421/entry/123/word/0>,
        <http://127.0.0.1:8421/entry/179/word/0>,
        <http://127.0.0.1:8421/entry/186/word/0>,
        <http://127.0.0.1:8421/entry/314/word/0>.
    * **What is actually in dispute, once policy is set aside**: 166 letters-differ
      rows, 12 spelling differences, 8 nun/gimel, 79 word divisions and ~106
      words one side has and the other lacks, over the 98 entries they have
      corrected. Everything else in the table above is a difference in how the
      same text is written down.
    * Nothing was changed. The classifier is a session script, not a tool in the
      repo - if this list is going to be re-run after a rebuild it should become
      one, and that is not built.

0HH. **[2026-09-16, reviewer on <http://127.0.0.1:8421/entry/32/word/194>: "we
    chunk the word and the following bracket into two tokens - sef has one.
    similarly for the period after each sentence... throws off alignment when
    switching. also - why do we surface this word as a dispute but not the
    opening bracket word `[ כמו` vs `[כמו`"] ALL THREE CONFIRMED, MEASURED, AND
    THE THIRD HAS A CAUSE NOBODY HAD LOOKED AT. NOTHING CHANGED.**
    * **1. The separate tokens are DOCUMENT AI's, not this build's.** Page 65's
      token stream reads
      `['אולי', '21', 'שם', 'מקום', '[', 'בבבל', ']', '.', 'כי', 'אויל', ...]` -
      64 standalone bracket/period/quote tokens on that page alone, each with
      its own bbox. `build_root_corpus.py:639` joins the stream with
      `" ".join(...)`, faithfully, so `clean_text` inherits the tokenization.
      Entry 32 w191-195 is `[ כמו אשת הן ]`.
      **Extent, the whole slice: 2,791 punctuation-only word positions, 6.67% of
      our 41,873, and they are in all 317 entries.** `.` 1,385, `"` 330, `]`
      278, `[` 276, `'` 209, `,` 149, `()` 94, the rest singletons. Yad Malachi
      has the same shape at a third the rate (4,563 of 188,740, 2.42%), mostly
      the geresh and the `•` separator.
    * **2. The toggle cannot line up anywhere, and the arithmetic says why.**
      Our 41,873 words against Sefaria's 35,628 - a gap of **6,245, of which
      5,566 (89%) is these 2,791 punctuation tokens plus our 2,775 bare footnote
      numerals**. 679 is everything else. Entry 32: 214 words against their 187.
      **Not one of the 317 entries has the same word count as theirs**, so
      `0GX`'s line-for-line match (verified against our OCR, which shares our
      tokenization) can never hold against THEIR two texts.
      The renderer adds to it: `renderAltBody` appends a text node after every
      word span -
      ```js
      // review_frontend/app.js:5296
          span.textContent = plain ? withoutPoints(words[i]) : words[i];
          body.appendChild(span);
          body.appendChild(document.createTextNode(' '));
      ```
      - so our standalone period draws as ` . ` where theirs draws `המה.`: a
      space before every sentence end that their text does not have, 1,385 times.
    * **3. The queue cannot see a bracket AT ALL. It is not `bracket_only()` -
      it is one level earlier, in the tokenizer, and `bracket_only` never runs.**
      ```python
      # tools/build_witness_disputes.py, text_words()
          for raw in cio.HEBREW_PUNCT.sub(" ", cio.strip_points(normed)).split():
              w = cio.hebrew_letters_only(raw)
              if len(w) >= 2:
                  out.append((w, raw, pos))
      ```
      Run on the reviewer's own phrase:
      ```
      ours   -> [('ואשת',…,0), ('אולת',…,1), ('כמו','כמו',3), ('אשת',…,4), ('הן','הן',5), ('או',…,7)]
      theirs -> [('ואשת',…,0), ('אולת',…,1), ('כמו','[כמו',2), ('אשת',…,3), ('חן','חן]',4), ('או',…,5)]
      ```
      Our `[` at position 2 and `]` at position 6 are not in the list at all,
      and `כמו` / `[כמו` are EQUAL, so `SequenceMatcher` reports no difference
      and no row is ever built for `bracket_only` to judge. `הן` / `חן` differ in
      a letter, so that one becomes a row - and it carries the RAW tokens, which
      is why the reviewer is shown `חן]` with a bracket the panel gives them no
      way to act on.
      **What the comparison never sees: 5,910 of our 41,873 word positions,
      14.1%** - 2,791 punctuation-only, 2,775 bare numerals (correctly, they are
      footnote marks), 147 one-letter Hebrew words, 197 other.
      **And of the 33,856 pairs it aligns as EQUAL, 3,099 have different raw
      tokens** - 2,704 other punctuation, **395 a bracket**.
    * **The 395, split, because only one half is work.** For **355** our text HAS
      the bracket, as its own token beside the word: nothing to rule on, it is
      the same difference as 1 and 2. For the rest our text has no bracket
      anywhere near - **18 positions at a generous +/-3-word window** (40 at
      +/-1, 19 at +/-2; the wider windows are absorbing a footnote numeral
      sitting between the word and the bracket). These are the ones that could be
      `0GN`'s class - a printed bracket our OCR dropped - or their editor's own
      insertion, which only the ink decides. **None of the 18 is surfaced
      anywhere**, and 276/118-119 are one bracketed span, so it is ~17 spans:
      - <http://127.0.0.1:8421/entry/55/word/212> `אי` against their `[אי]`
      - <http://127.0.0.1:8421/entry/65/word/363> `תקוה` against their `תקוה].`
      - <http://127.0.0.1:8421/entry/79/word/920> `כנפיו` against their `[כנפיו]`
      - <http://127.0.0.1:8421/entry/79/word/1033> `ודור` against their `[ודור]`
      - <http://127.0.0.1:8421/entry/82/word/19> `בשוא` against their `[בשוא]`
      - <http://127.0.0.1:8421/entry/90/word/40> `למשקלת` against their `למשקלת]`
      - <http://127.0.0.1:8421/entry/132/word/893> `ענוים` against their `[ענוים]`
      - <http://127.0.0.1:8421/entry/132/word/944> `ואשר` against their `[ואשר]`
      - <http://127.0.0.1:8421/entry/132/word/1109> `סבבונו` against their `[סבבונו]`
      - <http://127.0.0.1:8421/entry/133/word/692> `המלך` against their `[המלך]`
      - <http://127.0.0.1:8421/entry/133/word/870> `יצחק` against their `יצחק].`
      - <http://127.0.0.1:8421/entry/183/word/254> `וצורם` against their `[וצורם]`
      - <http://127.0.0.1:8421/entry/196/word/244> `כי` against their `[כי`
      - <http://127.0.0.1:8421/entry/216/word/337> `ברכיו` against their `[ברכיו]`
      - <http://127.0.0.1:8421/entry/276/word/118> `והנה` against their `[והנה`
      - <http://127.0.0.1:8421/entry/276/word/119> `הוא` against their `הוא]`
      - <http://127.0.0.1:8421/entry/288/word/23> `תריב` against their `[תריב]`
      - <http://127.0.0.1:8421/entry/313/word/140> `ונשקעה` against their `[ונשקעה]`
      This is Lesson 26 (THE FILTER THAT HIDES) at the tokenizer: `0GN` measured
      55 editorial rows and 8 bracket-only ones and read every one on the ink,
      but that count was of rows the builder EMITTED. The rows it never built
      were not counted until now.
    * **Nothing is fixed, because the first two are one decision and it is the
      reviewer's**, and this is the cheapest moment it will ever be: the real
      ledger is 0 bytes, so re-tokenizing renumbers nothing that exists. Three
      ways, and they are not exclusive:
      1. **Leave `clean_text` as the DocAI token stream.** Every token keeps its
         own bbox, which is what the scan highlighting hangs on, and `word_index`
         stays as recorded. The toggle stays misaligned.
      2. **Glue punctuation to its neighbour at build time.** Fixes all three at
         once and is free TODAY on the real corpus. It renumbers the demo copy's
         8 rulings, and it would have to merge two bboxes into one or drop one.
         Yad Malachi's 1,005 applied rulings mean this cannot be a shared default
         without a per-book switch.
      3. **Join them for DISPLAY only**, the shape the reviewer already accepted
         for niqqud (`0GY` option 2): nothing stored, served or exported changes,
         `word_index` is untouched, and the toggle lines up. It does not help 3 -
         the queue still cannot see a bracket.
      The 18 above are separate from all of that and can be surfaced without
      touching the tokenization.

0HG. **[2026-09-16, reviewer: "fix 4 then 1"] `0HE` FINDINGS 4 AND 1 FIXED, PLUS
    THE SIBLING NEITHER OF THEM WAS IN. THE AUDIT WENT FROM 998 TO 1,005 AND
    FROM 0 TO 4 ON THE DEMO.**
    * **Finding 4 - the flag-closing crash, and the address space under it.**
      `applied` now carries the decision that produced each entry, so nothing
      guesses it from two maps it may not be in:
      ```python
      # pipeline/apply_reviewer_decisions.py, was
              decisions.get((klal_id, word_index))
              or manual_decisions.get((klal_id, word_index))
      # now
          for klal_id, word_index, kind, decision in applied:
      ```
      All 11 `applied.append` sites carry it; `decision` was already in scope at
      every one.
      - **A heading ruling now closes NOTHING, deliberately.** Passing the right
        decision alone would have turned the crash into a silently WRONG close:
        a title ruling's index is a `title.split(' ')` position, `open_word_flags`
        is keyed on the body, and `cio.title_word_run` puts the heading at body
        word 1 wherever a gematria numeral opens the entry and at 0 where none
        does. And the ruling rewrites `title` while leaving `clean_text` alone,
        so the flagged body word still reads exactly what the flag was raised
        about - closing it would erase a live request. `heading_flag_still_open()`
        locates it and the run NAMES it instead, under "word flag(s) LEFT OPEN".
      - **It locates the run from the heading as it stood BEFORE the run**
        (`titles_before`). The first cut used the klal's current `title`, which
        the ruling has already rewritten, so the heading no longer matched the
        body and the run could not be found at all - caught by the test, not by
        reading.
      - Witness kinds need no mapping: the witness block appends the ruling's
        SNAPSHOT `word_index`, which is a body position (`0GW`).
    * **Finding 1 - the audit, and a THIRD type nobody had noticed.** `CHECKERS`
      was missing `title_correction` as well as `witness_choice`. The arithmetic
      said so and nobody had done it: 1,005 applied rulings on the live ledger,
      **998** reported as checked.
      - `check_witness_choice` reads a ruling exactly as `witness_choice_edit()`
        writes one - the SNAPSHOT's `word_index`, the snapshot's `master_reading`
        else `docai_reading` - and calls `unreadable`, `remove`, a gap insertion
        and a length-changing replace unverifiable by position, as the other
        checkers do for the same shapes. A confirmation IS verifiable.
      - `check_title_correction` reads `cio.title_words_of`, never `clean_text`,
        and a `whole` ruling against the entire stored heading.
      - `RELOCATABLE_TYPES` keeps the find_span/bbox relocation machinery off
        heading rulings: the heading is a PREFIX of the body, so searching the
        body for its words would find them and file a real mismatch as a benign
        shift.
      - **The skip is no longer silent.** An unregistered type is counted and
        named - `N NOT CHECKED - no checker is registered for their decision
        type` - because the bare `continue` never reached `total` either, which
        is why two omissions in a row were invisible.
      - `report_stale_addresses()` gets its own witness pass. It cannot go
        through the existing loop: the ruling's key is an OCR token, and its
        snapshot has no `original_word`, so `resolve_word_index` would read a
        token number as a word position. And every UNAPPLIED bucket is now
        LISTED, `unresolvable` included - its own note said that one "needs a
        human" and the report then named no row (Lesson 32).
    * **The sibling, swept and fixed** (Lesson 34).
      `tools/close_flags_already_answered.py` matches apply_events against open
      word flags by raw integer, so a `title_correction` apply_event would close
      a BODY flag carrying the same number. It resolves its decision by
      `applied_decision_id` and so never had the None crash - only the address
      bug. `applied_positions()` now drops the heading types
      (`ard.HEADING_DECISION_TYPES`). **Measured on the live ledger: 783 ->
      776 positions, the 7 excluded are exactly klalim 89/90/91/92/94/96/168 at
      word 0, and NONE carries an open flag today** - so the tool's dry run
      reports the same 96 flags before and after. A latent bug closed with no
      effect on current data.
    * **Measured after, all three corpora:**
      - Yad Malachi: `Checked 1005` (was 998), 622 confirmed (was 615) - the 7
        heading rulings, every one still reflected. MISMATCH unchanged at 2
        (klal 1 w95 and the klal 1 w97 precedent the script was written for).
      - `~/work/hashorashim-demo`: `Checked 4` (was 0), 4 confirmed, and the one
        applied ruling that actually changed text is reported in the
        stale-address pass as `applied unresolvable`, which is the correct
        outcome - applying it is what replaced the word it names.
      - `~/work/hashorashim`: 0 applied and it says so; the ledger is still 0
        bytes.
    * **Seven tests, each seen failing first, each mutation-checked.** Two
      mutations on the applier (heading rulings falling through to the closer;
      locating the run from the corrected title), one on the reported index, one
      restoring the two-map guess, and four on the audit (dropping the two new
      checkers, reading the ruling key instead of the snapshot, dropping the
      witness pass, restoring the bare `continue`). Gate suite: 574 passed.
    * **NOT fixed, still handed back:** `0HE` findings 2 and 3, which only bite
      on the `--apply-witness-choices` path that is off.

0HF. **[2026-09-16, reviewer: "surface the items to review"] `0GQ`'s REVIEW
    WORKLIST, EVERY ROW WITH ITS DASHBOARD ADDRESS, EACH ONE CHECKED AGAINST
    THE LIVE SERVER. 53 POSITIONS. ONE OF THE THREE GROUPS IS NOT SERVED AS A
    DISPUTE.**
    Each position below was fetched from :8421 and its word read out of the
    served `clean_text`, not taken from the queue file (Lesson 50, SAY WHICH ONE
    YOU CHECKED). No write of any kind was made; the real ledger is still 0
    bytes.
    * **Group 1 - the 4 rows where OUR reading is wrong** (`0GN`, read off the
      ink). All four are served as witness disputes.
      - <http://127.0.0.1:8421/entry/32/word/194> `הן` -> theirs `חן]`, p65, tier `C_both_attested` (witness row)
      - <http://127.0.0.1:8421/entry/83/word/91> `כה` -> theirs `כח].`, p87, tier `C_both_attested` (witness row)
      - <http://127.0.0.1:8421/entry/211/word/186> `ען` -> theirs `עז].`, p123, tier `A_ours_not_a_word` (witness row)
      - <http://127.0.0.1:8421/entry/212/word/1355> `כו` -> theirs `בו]`, p126, tier `C_both_attested` (witness row)
    * **Group 2 - the `B_bracketed_letters` tier, 15 rows.** All 15 are served
      as witness disputes. The verdict beside each is `0GN`'s reading of the
      crop, not a fresh one:
      - <http://127.0.0.1:8421/entry/1/word/11> `צמח` -> theirs `[י]צמח`, p58 - not on the page (witness row)
      - <http://127.0.0.1:8421/entry/15/word/72> `יש` -> theirs `[ויש`, p61 - printed, our OCR dropped it (witness row)
      - <http://127.0.0.1:8421/entry/36/word/172> `ארבעה` -> theirs `[ל]ארבעה`, p67 - printed, our OCR dropped it (witness row)
      - <http://127.0.0.1:8421/entry/36/word/341> `האמת` -> theirs `האמת[י]`, p67 - printed, our OCR dropped it (witness row)
      - <http://127.0.0.1:8421/entry/38/word/288> `מנד` -> theirs `מנדי]`, p68 - unreadable from the crop (witness row)
      - <http://127.0.0.1:8421/entry/59/word/285> `משחתא` -> theirs `[ומשחתא`, p74 - not on the page (witness row)
      - <http://127.0.0.1:8421/entry/93/word/199> `ענינים` -> theirs `[ה]ענינים`, p89 - printed, our OCR dropped it (witness row)
      - <http://127.0.0.1:8421/entry/132/word/348> `תוספת` -> theirs `ו[ב]תוספת`, p98 - printed, our OCR dropped it (witness row)
      - <http://127.0.0.1:8421/entry/141/word/451> `מצוא` -> theirs `[ל]מצוא`, p105 - printed, our OCR dropped it (witness row)
      - <http://127.0.0.1:8421/entry/193/word/461> `פארותיו` -> theirs `פארתו [פארתיו]`, p118 - not on the page (witness row)
      - <http://127.0.0.1:8421/entry/200/word/27> `על` -> theirs `על[ת]`, p120 - printed, our OCR dropped it (witness row)
      - <http://127.0.0.1:8421/entry/212/word/455> `האדם` -> theirs `[ל]האדם`, p124 - printed, our OCR dropped it (witness row)
      - <http://127.0.0.1:8421/entry/257/word/66> `איננו` -> theirs `[ו]איננו`, p137 - printed, our OCR dropped it (witness row)
      - <http://127.0.0.1:8421/entry/271/word/232> `רקח` -> theirs `[ה]רקח`, p140 - not on the page (witness row)
      - <http://127.0.0.1:8421/entry/302/word/58> `יגרם` -> theirs `יגורם]`, p148 - not on the page (witness row)
    * **Group 3 - the 34 footnote marks whose image and page numbering
      disagree** (`0GO`, `footnote_marks.json` rows with `decision == "review"`).
      **NONE of the 34 carries a witness row** - every one is an ordinary word in
      the text, so clicking it opens the MANUAL panel, not the witness panel, and
      there is no "theirs" to choose. Say so before handing these to anyone. The
      stored word at each is the bare mark itself (`"`, `'` or `*`); the number
      beside it is what the vision pass read from the image.
      - p58: <http://127.0.0.1:8421/entry/4/word/113> `"` after `ועוגב`, read as 17 (gap 15-18)
      - p67: <http://127.0.0.1:8421/entry/36/word/255> `"` after `אור`, read as 10 (gap 8-11)
      - p68: <http://127.0.0.1:8421/entry/38/word/355> `"` after `אביריו`, read as 5 (gap 9-10), <http://127.0.0.1:8421/entry/38/word/387> `'` after `אחיו`, read as 7 (gap 9-10)
      - p70: <http://127.0.0.1:8421/entry/45/word/28> `*` after `אחדים`, read as 4 (gap 2-3)
      - p71: <http://127.0.0.1:8421/entry/49/word/28> `"` after `מאחריו`, read as 17 (gap 14-17)
      - p72: <http://127.0.0.1:8421/entry/55/word/93> `'` after `הלילה`, read as 31 (gap 29-32)
      - p73: <http://127.0.0.1:8421/entry/55/word/164> `"` after `בתבור`, read as 3 (gap 1-5), <http://127.0.0.1:8421/entry/55/word/180> `'` after `המלך`, read as 4 (gap 1-5), <http://127.0.0.1:8421/entry/55/word/185> `"` after `הזה`, read as 5 (gap 1-5), <http://127.0.0.1:8421/entry/58/word/85> `"` after `בצהרים`, read as 32 (gap 30-33)
      - p87: <http://127.0.0.1:8421/entry/82/word/218> `*` after `וממלכתך`, read as 5 (gap 3-5)
      - p89: <http://127.0.0.1:8421/entry/93/word/150> `"` after `ואנקה`, read as 17 (gap 15-18)
      - p91: <http://127.0.0.1:8421/entry/97/word/374> `"` after `י"י`, read as 7 (gap 4-6)
      - p92: <http://127.0.0.1:8421/entry/99/word/114> `'` after `משפט`, read as 1 (gap 2-3)
      - p97: <http://127.0.0.1:8421/entry/127/word/53> `'` after `יסודו`, read as 9 (gap 7-11), <http://127.0.0.1:8421/entry/127/word/60> `"` after `יסודותיה`, read as 10 (gap 7-11)
      - p98: <http://127.0.0.1:8421/entry/132/word/35> `'` after `ה`, read as 9 (gap 4-9)
      - p99: <http://127.0.0.1:8421/entry/132/word/835> `'` after `וגו`, read as 29 (gap 26-29)
      - p100: <http://127.0.0.1:8421/entry/133/word/107> `'` after `אתהם`, read as 21 (gap 30-32)
      - p103: <http://127.0.0.1:8421/entry/135/word/107> `"` after `ילבש`, read as 2 (gap 0-0)
      - p105: <http://127.0.0.1:8421/entry/140/word/187> `"` after `בגדותיך`, read as 1 (gap 0-10), <http://127.0.0.1:8421/entry/141/word/7> `"` after `הבדים`, read as 6 (gap 0-10), <http://127.0.0.1:8421/entry/141/word/21> `"` after `מתניהם`, read as 7 (gap 0-10), <http://127.0.0.1:8421/entry/141/word/32> `"` after `ערוה`, read as 8 (gap 0-10), <http://127.0.0.1:8421/entry/141/word/37> `"` after `הבדים`, read as 9 (gap 0-10)
      - p117: <http://127.0.0.1:8421/entry/193/word/9> `"` after `לך`, read as 6 (gap 4-6)
      - p124: <http://127.0.0.1:8421/entry/212/word/152> `"` after `האלהים`, read as 2 (gap 19-21)
      - p126: <http://127.0.0.1:8421/entry/212/word/1242> `"` after `בחרבותם`, read as 4 (gap 9-10)
      - p127: <http://127.0.0.1:8421/entry/215/word/227> `'` after `במרום`, read as 31 (gap 29-33)
      - p131: <http://127.0.0.1:8421/entry/229/word/13> `"` after `הגג`, read as 2 (gap 0-1), <http://127.0.0.1:8421/entry/230/word/7> `"` after `גאה`, read as 4 (gap 0-1)
      - p140: <http://127.0.0.1:8421/entry/271/word/175> `"` after `וגיאותיך`, read as 15 (gap 13-15)
      - p151: <http://127.0.0.1:8421/entry/317/word/102> `"` after `וגלמודה`, read as 6 (gap 6-8)
    * **What the two crowded pages actually show**, read off the page's full
      mark list rather than the review rows alone:
      - **p73** has anchors at 1 and 5 and three marks between them, read as 3,
        4 and 5. Three marks for four missing numbers, so the fill rule
        (`0GO`: fill only when stray tokens equal missing numbers) declines -
        and the arithmetic says **one footnote on that page has no token at
        all**, which is `0GQ`'s "one missed footnote shifting the rest",
        confirmed. Its idx33 row is the same shape: one mark, gap 30-33.
      - **p105 is NOT a shift.** Its nine marks read, in page order, 1, 2, 3,
        **1**, 6, 7, 8, 9, circle. The first three were accepted; the fourth
        came back as `1` a second time where the sequence wants 4, and 5 has no
        token. So it is one misread numeral plus one missing one, and the 6-9
        that follow are correct and were held back only because the duplicate
        broke the run.

0HE. **[2026-09-16, reviewer: "investigate 0gl / w"] `0GL`'s OPEN PREREQUISITE
    IS FOUR SITES, NOT ONE. THE AUDIT PRINTS AN ALL-CLEAR OVER A BOOK WHOSE
    EVERY RULING IT SKIPS, AND ONE PATH CRASHES ON A WITNESS OR TITLE RULING.
    NOTHING CHANGED; ALL FOUR ARE HANDED BACK.**
    Swept every hard-coded decision-type list in `pipeline/` and `tools/`
    (Lesson 34, SWEEP THE SIBLINGS). Six tools already name `witness_choice`
    (`analyze_decision_ledger`, `close_satisfied_rulings`,
    `build_open_items_report`, `verify_witness_green_vision`, `export_corpus`
    since `0GW`, and `repoint_stale_decisions`, which EXCLUDES it in a comment
    that says why). These four do not.
    * ~~**1.**~~ **FIXED 2026-09-16, see `0HG`.** `audit_applied_decisions.py`
      checked no witness ruling, in BOTH of its passes, and nothing in its
      output said so.
      ```python
      # pipeline/audit_applied_decisions.py:349
              checker = CHECKERS.get(decision_type)
              if checker is None:
                  continue  # not one of the 3 checkable decision types
      ```
      A skipped ruling is never added to `total`, so the count it prints cannot
      reveal the omission. The stale-address pass carries its own second copy of
      the list:
      ```python
      # pipeline/audit_applied_decisions.py:456
          for dtype in ("candidate_choice", "disputed_choice", "manual_correction", "title_correction"):
      ```
      **Measured**, `SEFER_CORPUS_ROOT=~/work/hashorashim-demo`, a corpus whose
      ledger holds 4 APPLIED witness rulings in entry 1 including one real text
      change (`0GW`: w37 `אַבְּן` -> `אַבְּ`):
      ```
      Checked 0 applied decisions across candidate_choice/disputed_choice/manual_correction/punctuation_choice:
        0 confirmed still reflected in part1.json
        ...
        0 MISMATCH - applied decision no longer reflected in the corpus

        no ruling carries a stale address.
      ```
      So the one read-only check that exists to catch a correction that stopped
      being true gives a clean bill to a book where 100% of the rulings are
      invisible to it. Lesson 33's false all-clear. It is also the SAME defect
      the file's own comment at `:154` records for `disputed_choice` after the
      2026-08-23 rename - "CHECKERS.get() returning None hits a bare `continue`
      below, so every decision recorded after the rename was silently skipped" -
      hit a second time by a type added later.
    * **2. `reindex_pending_decisions_after_shift` does not move a pending
      witness ruling, though the witness apply path feeds it shifts.**
      ```python
      # pipeline/apply_reviewer_decisions.py:298
          for d_type in ("candidate_choice", "manual_correction", "disputed_choice"):
      ```
      The witness block records `word_count_shifts[klal_id]` on a `remove` or a
      gap `insert` (`:1305`), and `:1456` hands those shifts to this function.
      Every later pending witness ruling in that entry therefore keeps a snapshot
      `word_index` that is now one too high. **It fails SAFE, not silently**:
      `witness_choice_edit` refuses a drifted ruling rather than misapplying it -
      ```python
      # pipeline/apply_reviewer_decisions.py:781
          if words[wi:wi + len(seen)] != seen:
              return None, "drift - the entry no longer reads what the ruling saw there"
      ```
      - so the cost is recorded review work turning into `SKIP ... drift` rows,
      not a corrupted corpus. Lesson 35 (APPLYING HAS SIDE EFFECTS). For Yad
      Malachi this never fires; for HaShorashim every ruling is a witness ruling.
    * **3. A witness ruling never goes through `resolved_position()`**, the
      "THE ONE PLACE THE APPLIER ASKS WHERE" resolver (`:790`) that lets a
      stable word id find a ruling's word after an index moves. The two
      `resolved_position()` callers are `:928` and `:1153`; the witness block
      reads `snap["word_index"]` raw (`:1285`, `:777`). So the sidecar built
      exactly to survive shifts does not help the one book that needs it.
    * ~~**4.**~~ **FIXED 2026-09-16, see `0HG`.** A CRASH, latent, in the
      flag-closing step - and not witness-only.
      ```python
      # pipeline/apply_reviewer_decisions.py:1441
          for klal_id, word_index, kind in applied:
              if close_flag_satisfied_by(klal_id, word_index,
                                         decisions.get((klal_id, word_index))
                                         or manual_decisions.get((klal_id, word_index)), kind):
      ```
      `decisions` is `all_current("candidate_choice")` (`:857`) and
      `manual_decisions` is `all_current("manual_correction")` (`:858`), so a
      `witness-*` apply (`:1314`) and a `title-whole`/title apply (`:1375`,
      `:1401`) both resolve to `None` there. `close_flag_satisfied_by` returns
      early when no flag is open at that word, which is why it has never fired -
      but with one open it does `decision["id"]`:
      ```
      TypeError: 'NoneType' object is not subscriptable
      ```
      (probed directly against `close_flag_satisfied_by(1, 37, None,
      "witness-replace")` with one open flag stubbed at w37; with no open flag
      the same call returns `False`.) The step runs deliberately AFTER the corpus
      is written (`:1437`), so the crash would leave `part1.json` edited and word
      ids reconciled while the flag re-point, the pending-decision re-point and
      the summary never happen.
      **Reachability, measured on the real Yad Malachi ledger:** 7 applied
      `title_correction` rulings (klalim 89, 90, 91, 92, 94, 96, 168), every one
      at word 0, and none has an open word-flag at index 0 - so the coincidence
      has not occurred. It becomes live the day a reviewer flags a word and then
      rules on that same word through the heading or witness panel.
      A second, smaller thing in the same call: a title ruling's `word_index` is
      a `title.split(' ')` position while `open_word_flags` is keyed on body
      positions. They coincide only while the heading run starts at body word 0,
      which is why the wrong-flag reading has not shown up either.
    * **Not changed, on purpose.** Turning `--apply-witness-choices` on needs
      the reviewer's go-ahead and ends the option to wipe (`0GQ` item 4), and 2
      and 3 only matter on that path. 1 and 4 are independent of it: the audit is
      read-only and the crash is reachable through the heading panel today.
    * **State of the demo ledger while measuring**, recorded because `0GW`
      records four: `~/work/hashorashim-demo` now holds **8** witness rulings.
      The 4 in entry 1 are applied (16:56-16:57 UTC 2026-09-15); 4 more in entry
      8 were recorded at 18:51-18:52 UTC and are NOT applied, one of them a real
      text change (`נאמרל` -> `נאמר`, from the Tesseract reading). The real root
      on :8421 is still 0 bytes.

0HD. **[2026-09-16, reviewer: "he's a UI guy, he will play around with different
    ui on macOS than our simple html dashboard", then "write the api doc"]
    `REVIEW-API.md`: THE REVIEW SERVER'S HTTP API, FOR A CLIENT OTHER THAN THE
    HTML DASHBOARD. DONE.**
    * **What it covers.**
      - The 13 GET and 6 POST API routes, plus the scan images and share
        links. Each has a response recorded from the fixture corpus
        (`tests/fixtures/build_fixture_corpus.py`) on a throwaway server.
      - How to develop against that sandbox.
      - The rules a client has to keep: single-space word numbering, bboxes
        as fractions from the top-left, and witness rulings keyed by token
        index.
      - Linked from README.md's documentation map and from SETUP.md's
        collaborator section.
    * **Measured while writing it, with every write on the fixture only.** The
      repo's `review_decisions.jsonl` was untouched throughout, and
      `git status` stayed clean.
      - `REVIEW_DECISIONS_PATH` redirects the ledger. Two rulings went to the
        override file and none to the corpus root's own.
      - A manual ruling posted without `original_word` is not drawn on its
        word. It comes back in `stranded_rulings` instead, so the doc tells a
        client always to send it.
      - `OPTIONS` answers 501, and no response carries CORS headers, so a web
        page on another origin cannot use the API. Not changed, because a
        native client does not need them.
      - `/api/decisions/witness` accepts a `null` `chosen_text`, which the
        disputed, manual and title routes refuse. Recorded, not changed.
    * **A claim of mine, corrected.** I told the reviewer the server requires a
      note on every ruling. It does not: `note` is optional on all six routes.
    * **Guard.** `test_review_api_doc_names_every_route_and_only_real_ones`
      compares the doc's `/api/` routes with the server's own routes, in both
      directions. It was mutation-checked both ways:
      - dropping the witness-context route from the doc fails it, naming
        `/api/witness/context/<n>/<n>`;
      - naming the removed `/api/decisions/candidate` alias fails it too.
      The response samples are not checked.

0HC. **[2026-09-15, reviewer: "his python complained about numpy"] requirements.txt
    NEVER LISTED PILLOW OR NUMPY; A FRESH INSTALL COULD NOT EVEN COLLECT THE GATE
    SUITE. FIXED.**
    * **Measured, by a real fresh install.** A Python 3.14 venv in the session
      scratchpad, built from `requirements.txt` and `requirements-dev.txt`
      only, stopped at `ImportError while importing test module
      tests/test_pipeline_logic.py ... No module named 'PIL'`: the gate suite
      imports tools that import PIL at module level.
      - An import sweep of `pipeline/`, `tools/` and `tests/` found Pillow
        used by 13 tools and numpy by 4 (`render_pdf_pages.py`,
        `build_root_corpus.py`, `experiment_scan_source.py`,
        `ocr_pages_vlm.py`), neither listed.
      - The owner's venv had both from OCR experiments, so nothing here broke
        (Lesson 26's shape: a gap only visible from outside).
    * **Fixed** with `Pillow>=10.4` and `numpy>=2.0` as FLOORS, not pins: an
      exact old Pillow can mean compiling it from source on a new Python. The
      owner's venv runs Pillow 10.4.0 and numpy 2.5.2. A fresh install
      resolves Pillow 12.3.0 and numpy 2.5.3 from ready-built packages, then
      collects 706 tests, and all five numpy/Pillow tools import.
    * **Left unlisted by design** (experiment and benchmark scripts, SETUP.md
      step 6): `cv2`, `kraken`, `surya`, `torch`, `transformers`. The sweep's
      `docai_filter`, `evaluate_ocr_alignment` and `repair_filters` are the
      project's own modules in subfolders, not missing packages.
    * **The one gate failure in that run was NOT the packages.**
      `test_ligature_artifact_flag_only_fires_on_an_exact_match_to_stored_text`
      failed in the fresh venv AND the owner's, because
      `docai_filter.reference_frequencies()` read an empty table: the whole
      `sefaria_reference_corpus/` had been MOVED out of the repo, to
      `~/Downloads/sefaria_reference_corpus`, between 23:44:55 and 23:47:29
      (the repo root's own timestamp), just after `0HB`'s restore was
      committed. It was not moved by any command of this session. The fresh
      venv was built at 23:48:38, so every run after that lacked the folder.
      The reviewer had moved it there by accident and moved it back; it is
      identical to the 23:20 snapshot. The re-run in the fresh venv: 566 passed in 19.48s.

0HB. **[2026-09-15, 23:29] I REBUILT `sefaria_reference_corpus/word_freq.json`
    BY ACCIDENT - THE REBUILD `0EU` SAYS IS THE REVIEWER'S CALL. RESTORED
    EXACTLY THE SAME NIGHT, FROM THE MAC'S LOCAL TIME MACHINE SNAPSHOT.**
    * **RESTORED, and exact.** The local APFS snapshot
      `com.apple.TimeMachine.2026-09-15-232045.local` was taken nine minutes
      before the run, and macOS mounted it read-only while the reviewer
      browsed Time Machine. It held `word_freq.json` dated 2026-08-17 23:59:06:
      3,484,257 bytes, sha `da96e80dc4`, 166 books, 6,180,337 words, extractor
      2, byte-identical to the 2026-08-18 migration tarball. Both files were
      copied back from it with dates preserved, and are identical to the
      snapshot. The rebuilt 205-book pair survives only in the session
      scratchpad.
    * **What that settles.** The table had not changed since 2026-08-17, and
      the 166 rabbinic book files are byte-identical to the tarball's. So the
      85 per-book differences below come from the COUNTING having changed
      since, with `EXTRACTOR_VERSION` still 2.
      - It is not the maqaf split of `0FC`: Arakhin contains no maqaf.
      - That same commit began treating geresh and gershayim as punctuation,
        which is the next suspect, untested.
      - **OPEN (Lesson 12, THE KEY MUST HOLD THE QUESTION):** the next
        legitimate rebuild will change every count without anything saying
        so. Bump the version when the counting changes, and re-measure the
        recorded figures when that rebuild is chosen.
    * **The trap is still armed on this machine.** The folder holds 205 books
      and a 166-book table, so any run of `validate_lexicon_independent.py`
      rebuilds the table again, until `0EU` is decided.
    * The reviewer's first restore landed in the OLD checkout
      (`~/work/yad-malachi/yad-malachi-pipeline/sefaria_reference_corpus/`,
      `word_freq copy.json` and `word_freq.meta copy.json`). Those files are
      theirs to remove.
    * **Not reconciled:** `0ES`/`0ET` report "Rebuilt: 199,890 types" on
      2026-09-10, the same count this run produced. The snapshot shows the
      Aug-17 table was on disk tonight regardless, so whatever that rebuild
      was, it was not left in place.
    * **What happened.** While checking SETUP.md's reference-corpus steps
      (reviewer: "steps to rebuild images/pdf and ref corpus"), I ran
      `venv/bin/python tools/validate_lexicon_independent.py --help` to read
      its usage. It has no argument parser, so it RAN. Its first line was
      `Rebuilding word_freq.json: it was built by a different extractor
      version or from a different set of books.` It rebuilt the attestation
      table from every book on disk: 205, the 39 Tanakh books `0EN` added
      for HaShorashim included.
    * **Scope, measured.** Exactly two files changed, `word_freq.json` and
      `word_freq.meta.json`. Nothing else in the repo changed in that window,
      and the script writes nothing else. The folder is gitignored, so git
      cannot restore it. Time Machine's destination (a NAS) would not mount,
      and the audio worktree has no copy.
    * **Before and after:** the rebuild holds 205 books, 6,497,426 words,
      199,890 forms. The 2026-08-18 migration tarball holds 166 books,
      6,180,337 words, 185,593 forms, extractor version 2 - the 166 `0EU`
      describes as the table in use.
    * **The rebuilt version is saved** in the session scratchpad
      (`rebuilt_205/`), so a restore can be undone.
    * **NOT a proven-exact restore, yet.** Rebuilt from the same 166 files at
      the same extractor version, 85 of those books now count differently
      (Arakhin 24,929 -> 24,960; the 166 sum to 6,187,331, not 6,180,337).
      So either the book files changed after 2026-08-18, or the counting
      changed without `EXTRACTOR_VERSION` moving. The second would mean the
      cache's validity key misses a real change (Lesson 12, THE KEY MUST
      HOLD THE QUESTION).
    * **Also found:** `render_pdf_pages.py --verify` reported pages 14 and 15
      as failed ("boxes not on their words", ink contrast 1.28 and 1.24 < 1.6)
      on renders pixel-identical to the working images (max difference 0).
      The verifier is wrong, not the render. SETUP.md's step 2 also had
      `--register all` and `--verify`, both corrected in the working tree.

0HA. **[2026-09-15, reviewer: "i have a collab who wants to create a branch on
    his local mac. he cloned the repo but needs to rebuild stuff that isn't in
    the repo and use brew to install apps"] SETUP.md GAINS A COLLABORATOR PATH;
    THE SETUP CHECKER REQUIRED A KEY ONLY ONE SCRIPT READS.**
    * **BUG, fixed:** `tools/verify_local_setup.py` listed `credentials.json`
      as REQUIRED, but only `tools/extract_docai_pages.py` reads it (Document
      AI OCR, a paid job run once per book). A collaborator who reviews,
      tests or rebuilds was told a correct setup had FAILED. It is
      RECOMMENDED now. Checked with the file made to look absent: a warning,
      exit 0. It is also a Google Cloud service-account key, and the owner's
      migration tarball (2026-08-18, 490 MB) carries it, so a collaborator's
      copy of the data should be built without it.
    * **SETUP.md, for a collaborator:**
      - Homebrew step 0 (`python@3.14`, optional `direnv` and `gh`; tesseract
        only for the retired witness);
      - their OWN GitHub noreply email, where step 1 had the owner's;
      - what can be rebuilt rather than sent: the page images
        (`render_pdf_pages.py --all --verify`), the reference corpus
        (`fetch_sefaria_reference_corpus.py --register all`), every derived
        file (`rebuild_all.sh --skip-vision`), and the PDF, downloaded from
        Google Books and fixed with `fix_transposed_leaf.py` rather than
        redistributed;
      - `docai_word_boxes/` (42 MB) as the one directory that must be sent;
      - a collaborator section: branch from the current branch (on
        2026-09-15 `master` was 24 commits behind
        `hashorashim-nli-rebuild-and-review`), write access or a fork, the
        public-repo rules, and the private second book (`SEFER_CORPUS_ROOT`,
        the owner's decision);
      - the stale "241 tests" count removed.

0GZ. **[2026-09-15, reviewer, on <http://127.0.0.1:8421/entry/9/word/22>
    `בעליוי`: "the word is in the torah quote but the note says otherwise. we
    are wrong, we picked up the footnote. any way we can catch this class of
    errors?"] A DATA ISSUE, A CLASS, AND A VERSE-CHECK BUG. NOTHING CHANGED YET.**
    * **The instance (data).** On page 60 the print reads
      `מפטמין. אבוס בעליו⁷ אם ילין`, and DocAI read the raised 7 as a final
      yod. The page's own numbering shows it: entry 9 has footnote 6 at w17
      and 8 at w27, and no 7. The queue already serves the row, tier
      `C_footnote_marker`, class `footnote_numeral`, theirs `בעליו`. Its fix
      is a ruling, and no ruling goes into the real corpus until the scan
      source is settled.
    * **The class.** 163 witness rows sit in tier `C_footnote_marker` (96
      `one_letter`, 63 `footnote_numeral`, 4 other). The letters DocAI fused
      on: `י` 48, `ל` 20, `ס` 12, `ג` 12, `ן` 8, `ד` 8, `ם` 7, `ו` 7, `"י` 6.
      `0GO` measured 960 page numerals with no token of their own, and this
      is where many of them went.
    * **BUG: the verse note cannot rule on a short quotation that contains
      the dispute.** `tools/adjudicate_against_verse.py`, `quotation_run()`:
      the disputed position is exempt from the miss budget and is also NOT
      COUNTED as matched. So a two-word quotation, one word of it disputed,
      can match at most 1 word and never reach `--min-matched 2`:
      ```python
              if i == skip:
                  start = i
                  i -= 1
                  continue
      ```
      Entry 9 w22: quotation `מפטמין אבוס בעליו`, matched 1, `uncorroborated`.
      - Measured: 224 of the 300 `uncorroborated` rows have exactly 1
        matched word. Counting the disputed word when one reading is in the
        verse would rule 185 THEIRS, 6 OURS, 2 both and 31 neither; 21 THEIRS
        and 3 neither are in `C_footnote_marker`. Checked against the known
        case: entry 9 w22 comes out THEIRS.
      - It is not a one-line fix. Some of the 185 are spelling variants
        (entry 8 w74 `העפרת`/`העופרת`, entry 9 w9 `וברבורים`/`וברברים`) that
        must keep the `spelling_only` caveat, because the verse does not
        decide this edition's spelling (`0GE`). And `spelling_only` MISFIRES
        on fused numerals: entry 9 w22 is tagged a vav/yod spelling difference
        when the extra yod is footnote 7.
    * **A hypothesis of mine, disproved by the code.** I guessed "not in the
      quotation" came from the disputed word sitting at the anchor. It
      cannot: the anchor is the first mark strictly AFTER the word
      (`at(p) > pos`, line 428). `not_in_quotation` means the run stopped
      short of the word.
    * **A detector that does NOT work, so it is not to be built.** "In a gap
      in the page's footnote numbering, a word ending in a digit-lookalike
      letter whose remainder is in the lexicon" found 19 single candidates
      in 227 single gaps. It MISSED entry 9 w22, because `אבוס` (`אבו` + `ס`)
      also qualifies in that span. Most of its 17 "new" catches are ordinary
      words (`כמו`, `אני`, `אבל`, `בחורים`, `בענין`), and it confirmed 1 of
      the 163 tier rows. A lexicon says a remainder is a word, not that this
      page printed a numeral there (Lesson 49).
    * **What would catch the class, for the reviewer to choose:**
      1. Fix the verse check: count the disputed word when one reading is in
         the verse and at least one other quoted word matched, and stop
         `spelling_only` firing when ours = theirs + trailing letters. It
         takes effect only through a rebuild of `verse_verdicts.json` and the
         witness queue, which also re-derives the rows the demo's green boxes
         hang on. So: after the demo. **Reviewer 2026-09-15: "fix the verse
         check after the demo" - decided, scheduled for after the Sefaria
         meeting of 2026-09-16.**
      2. Fusions that Sefaria's text does not reveal: take the page-numbering
         gap as the locator and read each candidate word's last character
         from the image, the `0GO` method (38 of 39 right on numeral-or-not).
         It is a paid run, so a 40-item sample and an explicit go come first.

0GY. **[2026-09-15, reviewer: "the master should include all the nikkud from the
    sefaria version. if that is difficult or problematic perhaps we should start
    fresh for the demo with the sefaria as the base for the master text"] NOT
    DONE, PUT BACK TO THE REVIEWER: THE PRINT DOES NOT CARRY SEFARIA'S NIQQUD.**
    * **Two independent signals agree (Lesson 9):**
      - **Counts over the slice:** Sefaria's OCR points 62,531 of 187,028
        words (33.4%), with 4 cantillation marks; their corrected text points
        4,142 of 13,232 (31.3%). Our OCR baseline points **20 of 41,873**. DocAI
        does read niqqud where it is printed (`אַבְּ`, `בַּלוּקָה`, `אַבְלַקת`:
        Arabic transliterations), so a print that pointed a third of its
        words would not come back with 20.
      - **The ink, entry 1, page 58** (crops from the dashboard's page
        image):
        * the quotations are UNPOINTED, `לראות באבי הנחל¹` and
          `שנאמר עודנו באבו לא יקטף²`, where Sefaria has `לִרְאוֹת בְּאִבֵּי
          הַנָּחַל` and `עֹדֶנּוּ בְּאִבּוֹ`;
        * the Arabic word IS pointed, `אַבְּ ... אַבְּ³`;
        * the print spells `עודנו` plene, as we read it, not `עדנו`.
    * **So Sefaria's niqqud is theirs, not the printer's**, most likely
      carried in from the Masoretic text with their verse identification
      (their own export note says the quotations were checked against Tanakh
      by refLink). Lesson 38 and `0GE` record the trap: the Masoretic text is
      another book.
    * **Why neither option was taken.** Importing it would put ~62,000
      pointed words into the text that are not in this edition. That is
      against the Sefaria editor's own standard (fidelity to the specific
      edition, little intervention, a baseline a source edition can be cited
      for) and against success criterion #1. Rebuilding master from Sefaria's
      text for the demo does the same, and more: their Masoretic spellings
      (`עדנו` for the printed `עודנו`) and their inline citations would become
      the text. It would also invert what the demo shows, our independent
      read of the ink catching their errors, and it is a rebuild of the
      corpus, the scan alignment and the witness queue the night before the
      meeting.
    * **Offered instead:** leave master as the print, and address the reason
      for the request (the toggle comparison) in the DISPLAY. For example, an
      option to draw their texts without points while comparing letters. Or,
      if Sefaria wants a vocalized version, a separate layer whose
      interventions are listed with their source, never mixed into master.
    * **Option 2 DONE (reviewer: "do option 2 tonight").** The text-view
      selector offers "Sefaria OCR, no vowel points" and "Sefaria corrected,
      no vowel points".
      - Display only: `withoutPoints()` in `app.js` (`HEBREW_POINTS`, the
        only copy) sets their words without niqqud or cantillation. It keeps
        maqaf, paseq, sof pasuq and nun hafukha. Nothing served, stored or
        exported changes.
      - **Its first cut left points on screen, and my probe said it had not.**
        Their OCR writes pointed letters as ONE precomposed character in 44,214
        words: Alphabetic Presentation Forms, most often `וּ` U+FB35 (10,095),
        `שׁ` U+FB2A (9,750), `וֹ` U+FB4B (8,537) and `בּ` U+FB31 (6,878). A
        point regex cannot see them. The view showed `לראוֹת בּאבּי`, while
        the check, using the same regex, reported 0 pointed words (Lesson 43).
        It is fixed by NFKD before stripping, which also takes the ligature ﭏ
        to `אל`. Their corrected text uses no presentation forms.
      - **The counts above, corrected.** Measured after NFKD, their OCR points
        **63,453** of 187,028 words (33.9%), not the 62,531 first written here
        by the raw regex. Their corrected text: 4,141. The conclusion is the
        same.
      - Live on :8422, entries 1, 59 and 130: 0 pointed words and 0
        presentation forms in the new view, the heading still bold, and no
        page errors. A screenshot shows `לראות באבי הנחל`. At 1280px the
        wider selector (203px) keeps its 24px gap, and no title is cut.
      - The browser test now carries a pointed word AND a presentation-form
        word. It fails with stripping disabled, and with NFKD removed. Full
        browser suite: 120 passed, 1 skipped.
    * **A report that was the wrong dashboard.** "The master text now has my
      corrections in red" was :8421, the real root, where nothing is applied
      and entry 1's four words are open disputes. :8422 had them green
      (`rgb(56, 161, 105)`). Settled by colours read on both ports and by the
      :8421 request log (a scroll through `/api/klal/23-30/versions` that no
      probe made); the reviewer confirmed it. No code change.

0GX. **[2026-09-15, reviewer: "hard to compare the texts b/c only the master text
    has the title in bold. try to line the diff texts up as much as possible so
    the eye can spot the differences when we toggle between"] DONE.
    THE OTHER THREE TEXTS ARE NOW SET THE WAY MASTER IS.**
    * **What differed.**
      - Master is drawn word by word, with the heading bold and the footnote
        numerals raised.
      - The other three were one plain block, under a one-line banner that
        pushed every line down, at line height 1.9 against master's 2, with
        `pre-wrap` whitespace, full-size numerals and full-size citations.
      - Screenshots of entry 1 showed the first line already in a different
        place.
    * **Server** (`api_klal_versions`): each text now carries a `layout`.
      - Its heading run comes from `cio.title_word_run` and its numerals from
        `cio.footnote_ref_positions`, the two helpers master uses, with words
        from `cio.words_of`.
      - Stray marks read as numerals (`_footnote_marks_for`) are served for
        OUR two texts only, because they are addressed by our word positions.
      - Whitespace is collapsed in THEIR texts only. Collapsing ours would
        renumber the `word_index` space every ruling uses.
    * **Frontend** (`renderAltBody`):
      - One `.alt-word` span per word, with master's 1px padding, drawn with
        master's own `markTitleRun` / `markFootnoteRefs`. Both now take the
        index attribute, and alt words carry `data-alt-index`, so no word
        lookup on the page can mistake them for master's.
      - Master's line height, and no banner in the flow: the read-only notice
        is the selector's tooltip. A homograph note stays in the flow.
      - Their citations are one small raised unit each, where the page prints
        the note's numeral.
      - Master's page-break markers appear in our OCR while it has master's
        word count.
    * **Measured live on :8422:**
      - Entry 1: master and our OCR have 83 words each, heading words 0-2
        styled in both, 4 raised numerals in both, and line tops within 1px.
        They visibly diverge at exactly the applied ruling, w37 `אַבְּ`
        against `אַבְּן`, whose extra letter wraps `ולא` to the next line.
      - Entry 59 matches over all 25 lines.
      - Their two texts show their heading `האל'ף והבי'ת` bold in the same
        place. No banners, no page errors.
    * **Tests:**
      - `test_the_versions_endpoint_places_each_texts_heading_and_numerals`
        (server) fails when our texts are collapsed and when theirs are not.
      - `test_every_text_view_is_set_like_master_so_a_toggle_moves_only_the_differences`
        (browser, versions fed through the network layer, since the shipped
        corpus has no comparison texts) checks that a text identical to
        master starts at the same height, has the same heading, breaks at the
        same words and sets every line within 1px, that a citation is raised,
        and that switching back leaves nothing behind. It fails with the
        banner restored, with the heading unstyled, and with the citation at
        full size.
      - **Its first cut was blind to line height (Lesson 42):** a 1.9 mutation
        passed, because the same words still wrap in the same places. It now
        compares every line's top, and the mutation fails.
      - Logic suite 504 passed; browser suite 120 passed, 1 skipped.
    * **What still differs by design, not by setting:**
      - Master alone draws witness gap carets and pending-replacement text,
        and, where they apply, the unmapped-witness and stranded-ruling
        banners. Each of these moves master's lines.
      - Their texts carry vowel points and gershayim, so their lines run
        longer.
      - `title_word_run` counts an empty word beside the heading as part of it;
        noticed while testing and not changed.
    * **The repo's raw-split guard caught me.** The first cut split with
      `.split(" ")` in `review_server.py`, where the rule is `cio.words_of`.
      `test_no_new_raw_space_split_sites_appear_outside_corpus_io` failed on
      it, and it is fixed.

0GW. **[2026-09-15, reviewer: "I made a few changes in the demo dashboard. how
    do we push them so the text is updated to reflect the change but the green
    boxes are still there?"] APPLIED ON THE DEMO COPY. AND A BUG: THE EXPORT
    CANNOT SEE A WITNESS RULING.**
    * **What was applied.** 4 `witness_choice` rulings in entry 1 of
      `~/work/hashorashim-demo`:
      - word 20 `עודנו`, word 74 `פרי` and word 81 `הרמונים` are confirmed:
        each ruling equals the stored text;
      - word 37 `אַבְּן` -> `אַבְּ` is the one text change. It removes a
        footnote mark that DocAI had fused onto the word as a final nun; their
        text has `אב`.
      The real root is untouched, and its ledger is still 0 bytes.
    * **The method, proven on a throwaway clone first:**
      ```
      SEFER_CORPUS_ROOT=~/work/hashorashim-demo python3 pipeline/apply_reviewer_decisions.py --apply-witness-choices
      SEFER_CORPUS_ROOT=~/work/hashorashim-demo python3 pipeline/build_klalim_demo_dataset.py
      ```
      - The SECOND step is not optional. `review_data.load_klalim()` serves
        entry text from `klalim_demo_dataset.json`, so after the apply alone
        `part1.json` held `אַבְּ` while `/api/klal/1` and the page still
        showed `אַבְּן`.
      - NOT the full rebuild. It also rebuilds the witness queue, and the
        green boxes hang on its rows.
      - After both steps, on :8422: word 37 reads `אַבְּ`, all 4 words are
        still `state-human` in the text, 4 `hl-state-human` boxes are on the
        scan, and there are no page errors.
    * **A field trap, recorded because it cost a false alarm.** A
      `witness_choice` row's TOP-LEVEL `word_index` holds the DocAI token
      index (24, 40), because witness rulings are keyed by token. The word's
      position in `clean_text` is `candidate_snapshot.word_index` (20, 37).
      Reading the top-level field made the applier look as if it were
      targeting the wrong words; it was not. This is Lesson 48's shape (one
      name, two meanings), in the append-only file where it cannot be
      renamed.
    * ~~BUG, OPEN~~ **BUG, FIXED THE SAME NIGHT (reviewer: "fix it tonight"):
      `INTERVENTIONS.json` and the diplomatic edition ignored witness
      rulings.**
      ```python
      # tools/export_corpus.py:291
          for dtype in ("candidate_choice", "disputed_choice", "manual_correction"):
              for (kid, wi), dec in rd.all_current(dtype).items():
      ```
      After the apply, the demo copy's export lists **0 interventions**, and
      its diplomatic ("as printed") edition reads `אַבְּ` at word 37, the
      CORRECTED reading. Nothing reverted it, and nothing lists it. For
      Sefer HaShorashim every ruling is a witness ruling, so the "every
      intervention auditable and separable" answer to Sefaria's standard
      (`0DA`) does not hold for this book today. This is `0GL`'s open item
      ("witness rulings in `audit_applied_decisions.py`") found in a second
      place: a sibling not swept (Lesson 34).
      - A fix would read a witness ruling's as-printed word from its snapshot
        (`docai_reading`, at `candidate_snapshot.word_index`) and its
        correction from `chosen_text`.
      - **The fix.** `_revert_to_as_printed()` now reads `witness_choice`
        exactly as `apply_reviewer_decisions.witness_choice_edit()` writes
        one:
        * the replaced words are the snapshot's `master_reading` (else
          `docai_reading`), at the SNAPSHOT's `word_index`, never the key's
          token number;
        * `remove` is put back;
        * a gap insertion is taken out;
        * `unreadable` and confirmed rulings are skipped.
      - A second defect found while fixing it: the "already as-printed" test
        matched `[]` for an insertion, so a witness insertion whose words had
        gone missing would have been skipped silently. It now needs a
        non-empty reading, and such a row is REFUSED and listed.
      - The manifest's `source_note` gains a sentence explaining witness
        sources, only when a witness row is present.
      - `test_the_diplomatic_edition_reverts_witness_rulings_by_their_snapshot_position`
        has one entry per kind (replace, remove, insert, confirmed,
        unapplied, lost insertion), each keyed by a token number that differs
        from its position. It fails under all three mutations: the type left
        out, addressed by the key, the guard removed. Logic suite: 503
        passed.
      - Yad Malachi's sefaria, plain, diplomatic and TEI exports, manifest
        included, are byte-identical to `HEAD`'s, so no ruling of that book
        reaches the narrowed guard.
      - **The demo copy now exports 1 intervention**: entry 1 w37, as printed
        `אַבְּן`, corrected to `אַבְּ`, `witness_choice`, `custom`, 0 not
        recoverable. The diplomatic edition reads `אַבְּן` there and the
        corrected edition `אַבְּ`. `~/work/hashorashim-demo/export/` is
        regenerated.
      - **Siblings NOT changed, recorded so they are not mistaken for
        covered:**
        * `audit_applied_decisions.py` still checks no witness ruling. That is
          `0GL`'s open prerequisite for turning `--apply-witness-choices` on
          in the real corpus.
        * The corrected edition applies PENDING candidate and manual rulings
          in memory, but not pending witness rulings. That matches the
          applier's default (witness rulings are off unless asked for), so an
          export does not promote what the applier would not.
        * ALTO/PAGE/TEI read only `candidate_choice` and `manual_correction`
          for their layout annotations (`export_corpus.py`, the
          `all_corrections` / `all_manual` pair), so a witness ruling
          carries no annotation there.

0GV. **[2026-09-15, reviewer: "what needs to be done to be ready to show to
    Sefaria?" A Meet screen-share with the Sefaria editor is on 2026-09-16.
    No rulings until the NLI contact answers on scan sources.] DEMO READINESS,
    MEASURED. THE DASHBOARD IS READY; THE EXPORT IS NOT.**
    * **Dashboard, :8421.** Checked on entries 1, 17, 32, 59, 130, 203, 245
      and 317: no page or console errors, the witness panel opens, and all
      four text views switch (master, our OCR, their OCR, their corrected).
      Past the 100 entries they reviewed, "their corrected" shows "Sefaria
      has not sent a corrected version of this shoresh", which is correct.
    * **Sefaria export, first run ever on this book**, to the scratchpad; the
      corpus root was left untouched. It runs and writes `index.json`
      (Reference/Dictionary, one section) and `version_hebrew.json` (317
      entries), with 0 interventions because the ledger is empty. Three BUGS:
      - The version notes are Yad Malachi's. `tools/export_corpus.py:996`
        writes "OCR of the Berlin 1851/2 printing (Google Books scan)", and
        `:999` "... klalim carry extracted text". HaShorashim's `book.json`
        carries `edition` and `scan_source`, and the export does not read
        them.
      - The plain export labels every entry `כלל` (`:419`, `:427`), where
        `book.json`'s `ui.unit_he` is `שורש`.
      - No demarcation. The 2,772 footnote numerals are bare numbers in the
        text, and no format writes `@01` headings. That is the standard the
        Sefaria editor named ("demarcation around special formatting").
    * **A demo sandbox is possible and not built.** Rulings and word ids are
      written only under the corpus root, or to `$REVIEW_DECISIONS_PATH`. An
      APFS clone of the 1.6 GB root on its own port would take live rulings
      while the real ledger stays empty.
    * The part selector still offers Parts 2, 3 and "All parts" on this
      one-part book (`0GQ` item 7), and it is on screen at every load.
    **DONE THE SAME DAY (reviewer: "go" on items 1-3):**
    * **The export speaks for the book it holds.** Two optional `book.json`
      fields are read by `corpus_io`: `version_provenance()` and
      `reviewed_through()`. A declared book that omits them gets its own
      edition label and no review claim. With no `book.json`, Yad Malachi
      keeps its old sentences. `sectionNames` and the plain-text label come
      from the book's unit.
      - HaShorashim's `book.json` now declares its provenance, in the real
        root and in the demo copy. That change is uncommitted in the corpus
        root's private repo.
      - HaShorashim's export now reads "OCR of the Berlin 1896 printing
        (National Library of Israel full-tone photographs) ... none of the
        317 shorashim has yet been through word-level review", with
        `["Shoresh", "Segment"]` and `[שורש אב]`.
      - Yad Malachi's sefaria, plain, plain `--by-klal` and TEI exports are
        byte-identical to `HEAD`'s export script, run side by side.
      - `test_a_declared_book_exports_its_own_provenance_unit_and_review_claim`
        fails under four mutations: YM provenance inherited, review claimed by
        default, `Klal` hardcoded, `כלל` hardcoded. The existing export test
        now pins Yad Malachi's two sentences word for word.
    * **The part selector hides on a one-part book** (`CORPUS.parts`, which
      `/api/corpus` already served).
      `test_the_part_selector_shows_only_for_a_book_of_several_parts` checks
      the fixture (one part) and Yad Malachi (three), and fails under "never
      hidden" and under "always hidden".
    * **Demo sandbox: `~/work/hashorashim-demo` on :8422.** An APFS clone of
      the corpus root without `.git`. Its process has no
      `REVIEW_DECISIONS_PATH`, and its ledger and word ids resolve inside the
      clone. **Proven by a real write:**
      - a klal flag recorded through the page on :8422 put a 481-byte row in
        the clone's ledger;
      - the real ledger stayed at 0 bytes, and the real root's `git status`
        showed only the intended `book.json` change;
      - the clone's ledger was then reset from the real, empty one. :8422
        shows entry 1 unflagged, and `diff -rq -x .git` finds the clone
        identical to the real root.
    * Suites after all of it: logic 502 passed; browser 119 passed, 1 skipped.
    * **Item 4 (demarcation) NOT built, on purpose.** The only convention on
      record is `@01headers` and `@02bold@03`. Nothing in the repo says which
      tag Sefaria uses for a footnote reference, and inventing one in a file
      meant for the customer is the wrong risk. It is a question for the
      meeting. Heading runs and the 2,772 `footnote_refs` positions are
      already recorded, so the answer turns into a small change.
    * ~~Open~~ **DONE (reviewer: "change versionSource"):** `versionSource`
      named the Google Books copy (`m58-AQAAMAAJ`) while the text was read
      from NLI photographs. `book.json` now declares the NLI record,
      <https://www.nli.org.il/en/books/NNL_ALEPH990010892830205171/NLI>, in
      the real root and the demo copy. The record is identified in `0EC` with
      Rosetta PID `IE36945577`, the folder the full-tone photographs came
      from. Revisit it if the NLI contact's answer on scan sources changes
      the source.
    * **A probe of mine was wrong again, caught before any claim.** A "files
      changed in the clone" check used `find -newer part1.json`, and plain
      `cp -R` stamps each copy with the time it was copied. So it listed every
      file copied after `part1.json`, including the draft email, which no
      server writes. It was replaced by the content diff above.

0GU. **[2026-09-15, reviewer: "clicking on a non-dispute word gives me a popup
    but does not highlight the word in the scan pane"] A BUG, FIXED; one class
    left OPEN by design.**
    * **The bug.** `scan_alignment.klals_on_page()` took an entry's START page
      from the alignment file's own pair, and only when that file said
      trusted:
      ```python
          for kid, r in alignment.items():
              if r.get("trusted") and r.get("matched_page") == page_num:
                  klals.add(kid)
      ```
      The function above it, `resolve_klal_page()`, stopped trusting that pair
      on 2026-08-21 and prefers the page in `klal_page_regions.json`.
      `/api/klal`, `word_pages` and the scan header all use it. This sibling
      never got the fix (Lesson 13, THE SECOND COPY OF THE TRUTH). So an
      entry marked `trusted: false` was missing from its own start page in
      `/api/page`, which then served no plain-word boxes for it. A click on an
      undisputed word opened the panel, showed the "no OCR alignment" toast,
      and drew nothing on the scan.
    * **The fix.** `klals_on_page()` asks `resolve_klal_page()` for each start
      page, so there is one definition. Continuations are unchanged.
      `test_klals_on_page_takes_each_start_page_from_resolve_klal_page`
      covers three cases: untrusted, a trusted alignment that disagrees with
      the region, and no region at all. It fails under the old loop.
    * **Measured through the live API, before and after, both books:**
      - HaShorashim: 32,688 of 41,873 words boxed (78.1%) before, 36,093
        (86.2%) after. That is exactly +3,405, the aligned Hebrew words of
        the 42 untrusted entries.
      - Entries with no box at all went from 4 (entries 2, 100, 194 and 315)
        to 0. Untrusted entries now sit at 85.6%, trusted at 86.3%.
      - Aligned words still unboxed: 0 in either book.
      - Yad Malachi: 98.0% before and after, since its two page sources agree
        on all 222 klalim.
    * **Clicked in the browser on :8421**, across entries 2, 32, 59, 100, 150,
      211, 290, 194 and 315: 58 of 58 sampled Hebrew plain words now draw
      their box; before, entries 2, 100 and 211 failed on every word
      sampled. No page errors. Gated logic suite 501 passed; browser suite
      118 passed, 1 skipped.
    * **OPEN, a decision for the reviewer: words with no Hebrew letters are
      never boxed.** On HaShorashim that is 2,984 punctuation tokens (`.`,
      `,`, `"`, `[`) and 2,763 footnote numerals. Yad Malachi has 949. They
      normalize to "" and are dropped from the alignment on purpose
      (`corpus_word_bboxes`, 2026-08-30). Matching them by raw text was tried
      and reverted, because it moved 41 correct boxes on Yad Malachi. Clicking
      one opens the panel with the "no OCR alignment" toast. HaShorashim
      separates its punctuation into words, so this class is about 14% of
      the book, not 2%. A placement that does not touch the SequenceMatcher
      is possible: box a non-letter word only when both neighbours are boxed
      and exactly one non-letter token lies between them. It is not built.
      Also unboxed: 35 Hebrew words on HaShorashim and 128 on Yad Malachi
      that DocAI never aligned.
    * **Sibling, left as is:** `corpus_io.trusted_klal_pages()`, which feeds
      the rebuild's candidate stage, also reads `trusted` / `matched_page`.
      There, dropping an untrusted entry is deliberate (Lesson 15, SILENCE
      WHERE IT CANNOT ALIGN: no candidates rather than candidates from the
      wrong page), and it reports the dropped ids. It changes nothing on
      HaShorashim today, whose corpus IS the DocAI reading. Whether it should
      take the region's page is a rebuild-stage change, for the reviewer.
    * **My own probe was wrong once on the way (Lesson 43, THE PROBE THAT
      CANNOT SEE).** A sweep filtered with
      `(x.get("word_index") or -1) >= 0`, and `0 or -1` is `-1`, so word 0 of
      every entry read as unboxed. That invented a "leftover" of about 300
      aligned-but-unboxed words per book. It was caught before it reached
      this file. Every number above comes from the corrected sweep.

0GT. **[2026-09-15, reviewer: "remove the shoresh from the middle pane header -
    just the book title. also add light yellow box around selected shoresh in
    text pane - same as scan pane"] DONE.** Both books; `review_frontend/`.
    * **The text bar shows the book title only.** `#text-ref-he` and
      `#text-ref-en` are gone from `index.html`, and so is their only writer,
      `updateTextHeader()`. The CSS rule that held the reference at full width
      (`0GR`) matched nothing afterwards and is removed. The scan bar still
      names the entry and page.
    * **The entry being read is boxed in the text.** `.klal-block.current-entry`
      shares one rule with the scan's `.hl-current-klal`: the gold 3px ring,
      the pale fill and the 4px radius. `markActiveKlal()` sets it on each
      move and takes it off the previous block, so a scroll, a jump and a word
      click all move it. Every block gets the padding, with a matching negative
      margin, so no text reflows when the box moves. The box shows whether or
      not a word is selected. On the scan it hides while a word is focused;
      the text pane has its own word marker, so it was not copied there.
    * **Tests:**
      - `test_the_text_pane_header_carries_only_the_book_title` replaces the
        2026-09-01 test that pinned the reference, with both directives
        written into it.
      - `test_the_entry_being_read_is_boxed_in_the_text_as_on_the_scan`
        checks the computed look against a probe `.hl-current-klal`, that
        exactly one block wears the box, and that it moves.
      - The word-click test now asserts the box, not the removed reference.
      - The one-bar test asserts that the text bar carries titles and no
        reference.
      - `test_the_english_title_gives_way_before_the_reference` became
        `test_the_text_bar_fits_a_long_title_beside_the_which_text_box`.
      - Mutations, each failing its own assertion: the box never taken off
        the old entry (entries 1 and 2 both boxed); the box never put on; the
        text box outside the shared rule; the title too big to fit (loses
        135px).
    * Live, both dashboards restarted: :8421 entry 32 and :8420 entry 12 at
      1440, and :8421 at 1280. The bar shows only the title, one block is
      boxed, the screenshots match the scan's look, and there are no page
      errors. Full browser suite: 118 passed, 1 skipped.

0GS. **[2026-09-15, reviewer: "clicking away keeps the focus on the dispute prev
    seen in the popup - correctly. after that escape should return to the
    default mode where all disputes are highlighted and no word is selected.
    this should return to 100% zoom. same for selecting a diff. entry"] DONE,
    uncommitted.** `review_frontend/app.js`.
    * **Escape now has two steps.**
      - With a panel open, it is the dismissal, unchanged: identical to
        clicking away, so the word stays focused and the zoom stays put
        (`0DI`, `0DK`).
      - With nothing open, `returnToDefaultView()` clears the selection. No
        focused box and no dimming on the scan. No routed or cursor marker in
        the text. The remembered word is dropped and keyboard focus leaves
        the word. The zoom goes to 100%, and the address names the entry
        without a word.
      - The reset stays on the page being shown, not the entry's start page,
        and it never scrolls the text pane. That was `0DS`'s reason for
        guarding Escape. An Escape with nothing to reset does nothing, not
        even a redraw.
    * **Choosing a different entry resets the same way** (`jumpTo()`, and a
      `routeToKlal()` address naming only an entry). Choosing the entry you
      are already in is not moving on: it keeps its zoom, as it keeps its
      panel. Scrolling across an entry boundary is not choosing one, and
      does not reset.
    * **This brings back the 2026-08-26 "zoom back out to 100", on a
      different gesture.** `0DK` removed it from clicking away because it
      blinked there, and clicking away still changes nothing on the scan.
      `test_clicking_away_changes_nothing_in_the_scan_pane` is untouched and
      passes.
    * **Found by a mutation run: an older address-bar bug.** Choosing entry 12
      from the index after a word in entry 66 left `#entry=66&word=200` in
      the address bar: nothing on the jump path wrote the hash. A link copied
      from there led back to the word just left. Swept: `updateHash` has
      three callers (word click, routed link, and now the reset), and
      scrolling never writes it. `jumpTo()` now does, when the entry changes.
    * **Tests:**
      - `test_escape_after_clicking_away_returns_to_the_default_view` covers
        the two steps, no scroll of the text pane, and a third Escape that
        must not rebuild the highlight layer.
      - `test_choosing_another_entry_returns_to_the_default_view` covers the
        same entry keeping 220% and another entry going to 100% with no
        focus, no marker and `#entry=12`.
      - Each fails under its mutation, on its own assertion. The mutations:
        the Escape reset removed; the reset run with nothing to reset; the
        jumpTo reset removed; the reset on the same entry too; the address
        update removed.
    * **Live on :8421 (HaShorashim)**, `/entry/32/word/194`: arriving gives
      220%, one focused box and the panel open. The first Escape closes the
      panel and keeps everything. The second gives 100%, no focus, no
      marker, `#entry=32` and the same text scroll. From the same word,
      choosing entry 40 in the index gives 100%, no focus and `#entry=40`.
      No page errors. Full browser suite: 117 passed, 1 skipped. That run
      came before the last header-rule change in `0GR`; the 12 header and
      navigation tests pass after it.

0GQ. **[2026-09-15] HANDOFF - SEFER HaSHORASHIM, WHERE IT STANDS AND WHAT IS
    OPEN.** Read this first after a clear; the items below it (`0GB`-`0GP`)
    hold the evidence.
    **State, checked 2026-09-15.**
    * The corpus is PDF pages 58-151 (the א-ב-ג slice), read by DocAI from the
      NLI full-tone photographs: 317 entries.
    * `review_decisions.jsonl` is **0 bytes**, so the corpus is still a pure
      rebuild of the OCR and can be wiped (reviewer: "retain the option to
      wipe the corpus").
    * The witness apply path is built and OFF: `--apply-witness-choices`,
      including gap insertion (`0GL`, `0GP`).
    * Dashboards: :8421 serves HaShorashim, :8420 Yad Malachi.
    * The witness queue has 2,057 rows. 61 are served by word position; 53
      of those are gaps where only Sefaria has words.
    * 15 pipeline commits are unpushed. Scanned: no correspondent is named
      in any of them. Pushing is the reviewer's decision; never
      `git push --all`, never the `backup/pre-anonymize-2026-09-13` branch.
    **Open, in the order I would take it.**
    1. **Reviewing on :8421.**
       - Start with the 4 rows where our reading is wrong (`0GN`: 32/194,
         83/91, 211/186, 212/1355), then the `B_bracketed_letters` tier (15
         rows).
       - The 34 footnote marks whose image and page numbering disagree
         (`0GO`): `footnote_marks.json` rows with `decision == "review"`.
         Pages with several, such as p73 and p105, are probably one missed
         footnote shifting the rest.
    2. **Ink checks nobody has made.**
       - The long runs `--max-span 4` drops (`0GP`): 130/35 (we have 1 word,
         they have 16), 203/60, 245/82 (a leaked variant note), 317/180 (the
         next chapter's heading), and 84/22, 4/62, 136/10.
       - Three words both OCRs read alike inside a quotation: 20/150, 98/69
         and 135/17.
       - The three `צרי` heading concerns: 83, 175 and 203.
       - Two footnote marks I could not read: entry 38 `מנד`, and one in
         entry 193.
    3. **The citation deliverable (`0FM`).** `citation_corrections.csv` has
       146 rows, every one checked by eye. The draft to the Sefaria editor
       carries these numbers and is NOT sent. Still open: 1 row unclear
       (#147), and 16 off-by-one rows that could be a misprint or numbering.
    4. **Before `--apply-witness-choices` is ever turned on** (`0GL`):
       - a tool that re-points recorded rulings after a rebuild renumbers
         entries (each ruling carries its row to do it with);
       - witness rulings in `audit_applied_decisions.py`;
       - the reviewer's go-ahead, since turning it on ends the option to wipe.
    5. **Footnotes (`0GO`).**
       - How the notes appear in the final text is for the reviewer and
         Sefaria to decide.
       - 960 numerals have no token of their own (DocAI fused them into a
         word); they are the `C_footnote_marker` tier.
       - 10 marks are unread.
       - `experiment_footnote_marks.py` writes its JSON only at the END.
         Every paid answer is cached as it arrives, but the session-start
         rule wants item-by-item output: fix that before the next paid run.
    6. **Printed brackets our OCR dropped** (`0GN`, the bracket-only rows): a
       representation question, not yet decided.
    7. **UI.** The part selector offers Parts 2 and 3 on a one-part book.
    8. **Yad Malachi and the older items.** `0CO` and `0CV` need
       re-measuring. The TL;DR's `0BO`, `0BU`, `0BX` and `0DC`-`0DE` were not
       touched this session.
    **Lessons from this session.**
    * A new Lesson 50: say exactly which object you checked. Six rows of one
      file were reported as the first six of another.
    * Lesson 33 gained the false all-clear: a `| tail` chain hid three
      refusals, and a rebuild left the dashboard on the old entry list.
    * The public-repo naming rule is now in START_HERE's session-start list,
      file names included.
    * Three mutation checks this session survived at first. Each was a hole
      in a TEST, not the code, and each was closed (Lesson 42 doing its job).
    **How to rebuild.** The corpus-root `README.md` has the full chain:
    renumbering (alignment compared by root, word ids reseeded with an empty
    ledger), the dashboard's entry list, the witness queue, the citation
    check and the footnote-mark run.

0GP. **[2026-09-14, reviewer: "any unsurfaced disputes or corrections"] YES:
    61 ONE-SIDED DISPUTES AND 7 LONG RUNS REACH NO SCREEN. SHARED ERRORS ARE
    RARE.** Measured on the 317-entry build.
    * **61 of the 2,064 disputes are never served.** None is bracket-only;
      all are `one_side_empty`. The queue builder places a row on one of our
      tokens, and 55 have none; 6 more sit on a word that repeats on its page.
      They break down:
      - 48 words Sefaria has and we lack, 50 of the 61 being a single word.
        They include 5 bracketed insertions and 2 divine names; e.g.
        <http://127.0.0.1:8421/entry/59/word/131> `כבשים`,
        <http://127.0.0.1:8421/entry/79/word/920> `כנפו`.
      - 5 MOVED words: the same words at another place in each text, so the
        texts disagree on word order. Entry 17 `הזאת`, 46 `כמו דוה`, 55
        `אוי`, 132 `מפניהם`, 292 `יהודה`, e.g.
        <http://127.0.0.1:8421/entry/17/word/49>.
      - 3 words we have and they lack: 41 w31 `בכלל`, 65 w106
        `וכמהו אך יקם`, 277 w430 `אדמים`.
    * **7 runs longer than `--max-span 4` are dropped.** 4 matter:
      - <http://127.0.0.1:8421/entry/130/word/35>: we have 1 word, they have 16;
      - <http://127.0.0.1:8421/entry/203/word/60>: 16 words only they have,
        `מה בצע בדמי...`;
      - <http://127.0.0.1:8421/entry/245/word/82>: `בע יש הערה על המלה
        הערבית`, a variant note leaked from the apparatus (the p134 line);
      - <http://127.0.0.1:8421/entry/317/word/180>: the next chapter's
        heading, `המאמר הרביעי...`, which only they have.
      The other 3: 84 w22 (ours garbled), and 4 w62 and 136 w10 (6 words
      each that only we have).
    * **Sefaria corrections where our text shares their original error:
      1** (`measure_correction_overlap.py`: of their 90 reading edits in 99
      reviewed roots, ours HAD 78, SHARED 1, THIRD 11). It is served, as the
      one `their_correction_only` row.
    * **Suspect words inside verified quotations, with both texts reading
      the same word:** 20 of the 52 suspects that fall in our slice. The
      other 247 of the 299 are outside it. Read against the verse, about 17
      are not errors: Ibn Janah's own words inside the quotation (`באמרו`,
      `וכמהו`, `כמו`, `ר"ל`), one ketiv/qere (`מברחיו`), one plene spelling
      (`ירושלים`). Three are worth the ink:
      <http://127.0.0.1:8421/entry/20/word/150> `בכמו`,
      <http://127.0.0.1:8421/entry/98/word/69> `עמ` (the verse has `ועמק`),
      <http://127.0.0.1:8421/entry/135/word/17> `ואגרטלי`.
    **THE 61 ARE SERVED NOW (reviewer: "yes", 2026-09-14).**
    * `build_witness_review_queue.py` no longer drops a dispute that has no
      token of ours. It serves it by word position, keyed by a synthetic
      NEGATIVE `docai_token_index` that no real token can take, with
      `anchored: false`, and with `gap: true` where our side is empty.
      `gap_box()` draws its scan box between the neighbouring words; in
      right-to-left print the word before the gap is the one on the right.
    * The server appends a gap as its own entry and never merges it onto
      the word after it: `claim_word_index` skips gaps as it skips `delete`
      entries. On the scan, a gap's box neither hides nor replaces that
      word's own box.
    * The text pane draws a caret before the word, and it opens the witness
      panel. The panel reads "before word N" and offers "Keep our text -
      nothing belongs here" or "Add their words here"; it fetches no raw
      context, since a gap has no token. The applier refuses a gap ruling
      explicitly: accepting their words means an insertion, which is not
      built.
    * Rebuilt: 61 served by word position (53 gaps, 8 of our words with no
      token), and the queue goes from 1,996 to 2,057 rows, with 0 duplicate
      keys and every row boxed. Live :8421: 317 entries load and the witness
      total is 2,057. Entry 59 shows carets before words 23 and 131; the one
      before 131 sits between `כ'` and `בני שנה` where Sefaria has
      `כבשים`, and its panel offers both options.
    * 51 of the 53 gaps showed at first. The other 2 are words missing after
      an entry's LAST word, and the server's range check dropped them. Both
      the server and the text pane's end-of-entry block are fixed. Live
      after a PID restart: all 53 gaps and all 8 unpinned words of ours are
      served; entries 111 and 171 draw their gap after the last word;
      entry 17 w49 shows as an open dispute; no page errors.
    * **"ADD THEIR WORDS" BUILT AND OFF, 2026-09-15 (reviewer: "build add
      their words").** `witness_choice_edit` turns a gap ruling into an
      INSERTION before `word_index`; keeping our text is a no-op. A gap has
      no word of its own to check, so the drift guard is its neighbours: the
      queue row now records `gap_context` (the master words before and
      after), and the applier refuses when either has changed or when none
      was recorded. It runs only under `--apply-witness-choices`, the same
      switch as every witness ruling (`0GL`), so the corpus can still be
      wiped. Word ids follow through the applier's generic
      `widentity.follow_corpus()` after the save, and a shifted flag through
      `word_count_shifts`, which the witness path already sets. Rebuilt: all
      53 gap rows carry `gap_context`, and all 53 agree with the corpus.
      Tests: `test_a_gap_ruling_inserts_their_words_only_while_its_neighbours_stand`,
      which fails under each of three mutations (no neighbour check, missing
      context allowed, the next word overwritten); and
      `test_an_inserted_witness_reading_reaches_the_corpus_only_when_asked_for`.
      The browser test now also chooses "Add their words" and sees them
      pending after the caret.
    * `claim_word_index` skipping a gap is tested on its own
      (`test_a_gap_is_never_claimed_as_the_word_it_stands_before`), because
      the fixture has no witness row on a gap's word and could not notice the
      guard missing; with the guard removed the test fails. Full suite: 693
      passed, 1 skipped.
    * Tests: `test_a_gap_is_boxed_where_the_missing_words_would_stand`,
      `test_a_gap_ruling_is_recorded_but_never_applied_as_a_replacement`,
      `test_a_gap_where_only_the_witness_has_words_is_shown_and_can_be_ruled`.
      The last runs on a new fixture row: klal 4, a gap before word 3.

0GO. **[2026-09-14, reviewer: "we can afford some whitespace after the shoresh
    in the index pane so the titles are all left justified. what are we doing
    with the footnotes? right now I see bare numbers in the text"]**
    * **Index pane.** A book referred to by root sets its titles flush left, so
      the column lines up however wide the root is. `body.by-root` is set from
      `/api/corpus`, and `.by-root .nav-item .ntitle` is aligned left. Yad
      Malachi is unchanged.
    * **What happens to the footnotes, as of today.**
      - The reference numerals stay in `clean_text` as words. Nothing is
        deleted (`0EX`).
      - The build records their positions as `footnote_refs`: 2,772 across 307
        entries in the current build. Until today nothing served that field,
        so the text pane showed them as full-size numbers.
      - The notes themselves are mostly citations of the verse a quotation
        comes from. They are cut out with the apparatus and kept nowhere in
        our corpus. `0EX` measured that our OCR of the small apparatus type
        cannot be paired with the references: 0 of 94 pages pair. The agreed
        split is "their citations, our running text"; Sefaria's 20,450 notes
        (`witness_footnotes.json`) are used only for the verse checks.
      - A numeral that DocAI fused into the preceding word as letters leaves
        no number to find. Those rows are the `C_footnote_marker` tier.
    * **Now:** the text pane draws the numerals small and raised, as the page
      prints them, with a tooltip saying what they are. `/api/klal` serves
      `footnote_refs`, recomputed from the current words so a ruling cannot
      leave the positions stale, and only for a book whose build records them.
      The pattern has one copy, `corpus_io.FOOTNOTE_REF`, which the build now
      uses too.
    * **Open, for the reviewer and Sefaria:** how the notes appear in the
      final text. Sefaria's citations could be shown on hover by pairing each
      entry's numerals with their notes in order; that pairing has not been
      measured.
    * **Index, corrected the same day** (reviewer: "I meant right justified").
      Flush-left titles were the wrong reading and are reverted. A title
      starts where its row's markers end. A root with periods (`א.ב.ד`) is
      wider than `.nheb`'s 30px minimum, and a three-digit number is wider
      than `.nid`'s 24px, so each title started wherever its own markers
      ended. `sizeMarkerColumn()` now measures the widest number and root in
      the list and sets both columns to them, as `--nid-w` and `--nheb-w`. It
      runs again once the marker font has loaded, and applies to both books.
      Test:
      `test_every_index_title_starts_in_the_same_place_however_wide_its_markers`.
    * **Reviewer: "footnotes are integers monotonically increasing so we
      should auto-identify the ones that scanned as gershayim."** Measured on
      the build's line stream, pages 58-151:
      - Numbering restarts at 1 on each page and climbs. Our OCR damages it
        three ways. A raised numeral is read as a mark: p61 reads `6 ·" 8`
        where the page has 7. A digit is misread: `8 20 10`, and `32 88 34`.
        Or the numeral is dropped, or fused into its word.
      - Prototype: the longest rising run of numerals per page gives the
        anchors (2,408). A gap is filled only when the count of stray tokens
        in it equals the count of missing numbers. This identified 187 marks
        and 84 misread numerals. 654 gap tokens stayed unresolved, 381 of them
        marks, and 960 missing numbers have no token at all. Of 577
        standalone marks, 187 were identified.
      - **On the ink, 16 identified marks sampled across the book: 10 right.**
        Two had the right spot but the wrong number, because an anchor
        numeral was itself misread (p73: 5 assigned 4; p89: 17 assigned 16).
        Two were real abbreviation marks (`אח׳` p98, `ה׳` p128). Two were a
        second printed sign, a small raised circle that is not a numbered
        note (p105, p118); it is the mark behind Sefaria's `[ה]רקח`. **Not
        good enough to label automatically.** A refinement was measured: skip a
        mark after a word of one or two letters, and fill a gap only between
        anchors confirmed by a neighbour one away.
      - **Refined, on a fresh ink sample of 20 from other pages: 15 right.**
        It identifies 52 marks instead of 187 and skips 5 abbreviation marks.
        Three misses are numbers off by one (p72: 31 assigned 30; p87: 5
        assigned 4; p100: 21 or 31). Two are abbreviation marks after
        three-letter words (`ונו׳` p99, `אומ׳` p100). Across both samples the
        POSITION is nearly always a raised note; the NUMBER is what fails,
        because an anchor numeral was itself misread. OCR text alone does not
        carry enough to number these. Reading each raised mark from the image
        would be a second signal, and that is put to the reviewer. Nothing
        identified is written to the corpus.
    * **Reviewer: "do 1 - size it on a sample first"** (read each raised
      mark from the image). `tools/experiment_footnote_marks.py` samples 40
      stray marks, seed 17: 20 the sequence numbers and 20 it cannot place.
      Each is cropped from the full-tone page with a red box and put to
      `gemini-3.6-flash` through the shared, cached adjudication helper.
      Results are in `footnote_marks_sample.json` in the corpus root, with the
      truth read by eye from the crops BEFORE the answers were opened.
      - Truth: 36 real numerals, 2 abbreviation marks (`וגו׳`), 1 small
        raised circle, 1 stroke I could not call. **17 of the 20 marks the
        sequence cannot place are real numerals.**
      - Model, numeral or not: 37/39 right. It caught both abbreviation marks
        and the circle, and missed two `36`s, calling them "other".
      - Model, exact number: 23/36. 11 of the misses are ONE DIGIT of a
        two-digit numeral (7 for 17). The red box covered only the OCR's mark,
        often one digit, and the prompt asked what is inside the box. This is
        a flaw of the experiment's design, not of the model.
      - Sequence alone: 16/19. Accepting only where the model and the
        sequence agree: 11 accepted, all 11 right.
      - Each side corrects the other. The model fixed the sequence's
        off-by-ones (8→9, 5→6), and the sequence fixed the model's one-digit
        reads. Next: ask for the whole raised number, box widened, and rerun
        the same 40.
      - **Rerun with the whole-number prompt and a wider box, the same 40
        marks, scored against the same truth** (`footnote_marks_sample_v2.json`):
        * numeral or not: 38/39;
        * exact number: 33/36. The misses: one `36` called "other", 31 read
          as 21, and 4 read as 1.
        * Where the model and the sequence agree: 14 of 19 accepted, **all 14
          right**.
        * Where they disagree (5): the model was right three times (9, 6,
          17) and the sequence twice (31, 4). So a disagreement goes to a
          person; neither side wins by rule.
        * Marks the sequence cannot place: the model numbered 16 of 20, **all
          16 right**. The other 4 are the two `וגו׳`, the circle and the
          missed `36`.
        * The uncertain stroke (row 20) the model calls a geresh.
      - **Sizing a full run:** 577 stray marks, one call each (about 14 times
        this sample). A rule that fits these numbers:
        * accept where model and sequence agree;
        * accept the model's number where the sequence has none;
        * send disagreements to review;
        * record the model's geresh and circle as NOT footnotes.
        On this sample that accepts 30 of 40 with 0 wrong, and sends 5 to
        review. Caveats: 40 is a small sample; the truth is one reader's view
        of 313 dpi crops; two of 36 numerals were missed. Put to the reviewer
        before any full run.
    * **FULL RUN, 2026-09-14 (reviewer: "yes run all 577").** All 577 stray
      marks were read: one live call each, then every rerun from the cache.
      `footnote_marks.json` is in the corpus root. The rule was refined twice
      on what the run showed, both times scored against the 52 marks read by
      eye (the 40-mark sample plus 12 more):
      - **Placement.** The first pass placed 0 of 577 at an entry word. It
        went through the server's word boxes, and a punctuation-only word has
        none: entry 15 word 6, the `"` on p61, has no box. Now each mark is
        placed by aligning the build's token stream with the corpus words:
        577 of 577 placed, and every stored word equals its mark.
      - **"Out of order" was mostly "already there".** Requiring a
        model-alone number to fit between the page's numerals either side
        sent 107 to review. On 12 of them read by eye the model was right 12
        times, and 8 were the same printed numeral read twice: once as a
        number token, once as a stray mark. A page numbers each footnote
        once, so a mark whose number is already on the page is a DUPLICATE,
        and nothing is drawn. When the digit beside a mark is PART of its
        number (`5` beside a mark read as 50), it is a SPLIT: the mark shows
        the whole number, and that digit is folded into it on display.
      - **Two ordering flaws, caught by the eye check.** First, a
        disagreement with the sequence must go to review before the duplicate
        test: at p100 the sequence said 31 and the model misread 21, and 21
        was on the page. Second, two marks on one page given the same number
        are one numeral when adjacent: entry 93 words 67 and 69 are `"`
        either side of a `4`, and both were read as 14 (`one_number_each`).
      - **Final: 285 accepted, 22 split, 111 duplicate, 34 review, 115 not a
        footnote (101 geresh, 14 circle), 10 unread.** 307 marks are drawn,
        with no page number given twice and no digit folded in twice. **All 52
        eye-checked marks are right under the final rule.** That is 52 marks,
        read by one reader from 313 dpi crops.
      - The dashboard serves an entry's accepted and split rows, only while
        the stored word is still the mark; a split is served only while its
        digit is still a numeral. It draws the number raised, dotted, in
        place of the mark. The text is unchanged.
      - Tests cover the rule, one number per page, the server rule and the
        drawing. Mutations tried: the rule (disagreement accepted, geresh as a
        numeral, no model-alone branch) and the server (no still-the-mark
        check, not accepted-only). Each fails.
    * **Checked live after a PID restart of :8421.** Entry 15 serves
      `footnote_refs` [16, 28, 53, 57, 93], the page draws 36 raised numerals
      with no page errors, and the index titles line up flush left. The bare
      `"` in entry 15 (`אגם מים " מקום`) is footnote 7, read as a gershayim:
      exactly the case the reviewer raised.

0GN. **[2026-09-14, reviewer: "yes" to checking whether Sefaria's bracketed
    insertions are printed] 34 OF THE 55 "EDITORIAL" ROWS ARE ORDINARY LETTER
    DISPUTES, HIDDEN BECAUSE THEIR TOKEN CARRIES A BRACKET.**
    `build_witness_disputes.py` marks a row editorial with
    `EDITORIAL = re.compile(r"[\[\]]")`, which matches any bracket character
    in their reading, and the queue never serves those rows. Classified
    mechanically on the 317-entry build (2,064 disputes, 55 editorial):
    * **B, 34 rows: letters differ once the brackets are removed.** These are
      real disputes. Examples: `ירגע` vs `ירנע].` (nun/gimel, entry 170),
      `ען` vs `עז].` (211), `הן` vs `חן]` (32), `ממון` vs `[מטון]` (129),
      `המחבר` vs `הסתבר]` (212).
    * **A, 13 rows: their bracketed text, which we lack.** Examples: `צמח` vs
      `[י]צמח` (1), an inserted `[או]` (12), `ארבעה` vs `[ל]ארבעה` (36).
    * **A', 8 rows: only the brackets differ.**
    The book does print brackets: our OCR reads 276 `[`, while their text has
    1,218.
    **ON THE INK, ALL 55 ROWS.** Each word was cropped with its neighbours
    from the word's own page and read by eye. The mechanical classes above do
    not survive; the ink sorts the rows like this:
    * **10 rows: a bracketed letter is PRINTED and our OCR dropped it.** Rows
      3, 5, 6, 7, 16, 21, 27, 32, 37, 46, e.g. `[ו]יש`, `[ל]ארבעה`,
      `האמת[י]`, `[כ]מפגיע`, `[ל]מצוא`, `על[ת]`.
    * **4 rows: our letters are wrong and theirs match the ink.** `הן` for
      `חן]`, `כה` for `כח`, `ען` for `עז]`, `כו` for `בו]`.
    * **2 rows: our text has a stray letter where a small printed mark sits.**
      `הבשםל`, `הסדורג`.
    * **19 rows: their OCR's letters are wrong and ours match the ink.** The
      bracket is printed in each case, e.g. `ירגע` (their `ירנע].`),
      `ממון`, `כשמטה`, `ידעם`, `המחבר`, `בוגדה`.
    * **9 rows: only the brackets or the word division differ**, e.g.
      `פלו[ני`, `ופירש[נו]`, `[סי]מן`, `ב [ א ]` against `ב[א]`.
    * **9 rows: their editor's own additions, with nothing printed.** `[או]`,
      `[מאני]`, `[לו]`, `[פארתיו]`, `[ארבע אותיות]`; `[במלבן]`, which is the
      qere where the page prints the ketiv `במלכן`; and `[י]צמח` and
      `[ה]רקח`, where the page has only a small raised mark.
    * **2 rows I could not read from the crop:** `מנד`/`מנדי]` in entry 38,
      and one in entry 193.
    So the filter hides 45 rows that are not editorial: 16 of them are places
    where our text is wrong or missing printed letters, and 19 would confirm
    our reading. These readings are mine, from crops of the 313 dpi images,
    and each row goes to the reviewer on the dashboard once it is served.
    **FIX, 2026-09-14.** `build_witness_disputes.bracket_only()` replaces the
    any-bracket pattern. A row stays out only when both sides have the same
    letters once brackets are removed. The queue builder and the verse tool
    skip on `bracket_only`. Test:
    `test_only_a_difference_in_brackets_alone_is_kept_out_of_the_queue`, which
    fails under each of three mutations: no bracket precondition, the old
    any-bracket rule, and never bracket-only. After the rebuild: 8 rows are
    bracket-only, and the queue has 1,954 -> 1,996 rows.
    **One labelling defect, found in the rebuilt queue.** A printed bracketed
    vav or yod that we dropped (`[ו]יש`, `האמת[י]`, `[ו]איננו`) differs from
    ours by one vav or yod, so the queue files it as `C_spelling_vav_yod`.
    That calls it a spelling variant, when the question is whether the letter
    is printed.
    **FIXED 2026-09-14: a new tier, `B_bracketed_letters`.** A row gets it
    when their reading has a bracket and every letter of ours plus more;
    that includes their misplaced `[ויש` for the printed `[ו]יש`. It is
    tested before the nun/gimel, lexicon and vav/yod tiers. Test: new
    assertions in `test_a_witness_tier_says_what_the_disagreement_is_not_a_fallback`,
    including a vav/yod row without a bracket and one where ours is longer.
    Mutations: dropping the check, the bracket condition or the subsequence
    condition each fails the test. A "theirs is longer" condition survived
    mutation because it is implied (equal letters are `C_markup` first), so
    it was removed rather than tested. The panel explains the tier.
    In the rebuilt queue it holds 15 rows. Against the ink table above:
    * 9 have the letters printed, dropped by our OCR (entries 15, 36 twice,
      93, 132, 141, 200, 212, 257);
    * 5 do not have them on the page (1, 59, 193, 271, 302);
    * 1 was unreadable (38).
    Queue: 1,996 rows. `C_spelling_vav_yod` 687.
    A side finding: a dispute row's `page` is the page where its ENTRY starts,
    not its word's page. Cropping by it found no box for 25 of the 55 rows.
    The queue sets its own page and bbox, so the dashboard is unaffected.

0GM. **[2026-09-14, reviewer: "yes" to "entry 16 has never been compared"]
    ENTRY 16 (`אג`) IS NOT AN ENTRY. IT IS A FALSE HEADING, AND `0GF` HAD THE
    CAUSE BACKWARDS.** `0GF` said Sefaria's data "has no `אג` key and runs it
    into the previous entry". Their data is right and our split is wrong. On
    the ink (PDF p61) the words are running text:
    `...ואחד מהם אגם בקבוץ / האלף והגימל. אבל זה הוא שדעתי נוטה אליו...`, which
    says "אגם, with qibbutz under the aleph and the gimel". It is a vowel
    description inside `אגמ` that wraps to the start of a line. That line is
    flush, while every real heading is indented; the next line,
    `האלף והגימל והנון.`, is. `build_root_corpus.segment()` splits at any line
    that parses as a heading, so this one became an entry.
    Four signals agree:
    * the sense of the sentence;
    * the layout: the line's indent is 0.0007 of the page width, against a
      median of 0.082 for the 318 headings and 0.002 for body lines;
    * the root order: `אג` follows `אגמ`, but a section heading opens its group;
    * their text, which keeps these words inside `אגמ`.
    **The order check.** `detect_root_entries.order_violations()` flags 17 of
    317 adjacent pairs on this corpus. 16 of them are the book's own
    arrangement, measured:
    * each chapter opens with `X הכפולה` (`בב`, `גג`);
    * the doubled root heads its two-letter group (`אלל` before `אלה`, `ברר`
      before `ברא`).
    With a key that encodes that arrangement, there is 1 violation in 318
    headings, and it is this one. Lesson 0 was served in session: I had put the
    fix to the reviewer as "split their entry 15 at `אג`", from one signal
    (Lesson 9).
    **FIXED 2026-09-14.**
    * `detect_root_entries.root_order_key()` encodes the book's order.
      `order_violations()` uses it, so the detector's `--check-order` stops
      reporting the book's own arrangement.
    * `build_root_corpus.segment()` refuses a parsed heading only when BOTH
      signals hold: its root sorts before the current entry's, and its first
      Hebrew word stands less than `HEADING_INDENT_MIN` = 0.02 in from the
      column edge. The column edge is the 90th percentile of the page's line
      ends. Either signal alone keeps the heading. The indent skips a leading
      numeral, because p109's `88 הבית והזין הכפולה` sets its numeral out in the
      margin.
    * The refused line stays in `אגמ`'s text, and the build prints it.
    * The cross-check no longer counts the Google layer's reading of the same
      prose as a heading DocAI missed. Before this change it put
      `suspect_merge` on all 7 entries starting on p61; now there are 0.
    * Dry run: 317 entries, 1 heading refused, 0 missed.
    * Tests: `test_the_book_order_puts_chapter_section_and_doubled_roots_first`
      and `test_a_flush_line_that_breaks_the_root_order_is_text_not_a_heading`.
      Each fails under all four mutations: without the order signal, without
      the indent signal, counting a numeral as the indent, and without the
      doubled-root rank. The first version of the second test survived two of
      them, and it was widened until it did not.
    **Roots now display with periods** (reviewer, same message: "shorashim
    should have periods"). A book referred to by root shows `א.ג.ם` for `אגמ`
    in the index row, the text-pane header and every "Shoresh ..." label, with
    the last letter in final form. This is display only: `app.js` has
    `rootDisplay()`, and the stored root still keys the comparison texts. Test:
    `test_a_root_is_shown_letter_period_letter_ending_in_its_final_form`.
    **REBUILT 2026-09-14. The corpus now has 317 entries.**
    * Compared by root, one text changed and one root is gone. `אגמ` went from
      140 to 155 words and now ends `...ואת האגמים שרפו באש.`; `אג` no longer
      exists. Every other entry's text is identical, renumbered one lower
      from 16 up.
    * Alignment by root: 0 page moves, 0 trust changes.
    * Word ids reseeded. The ledger is still 0 bytes, so no ruling held an id.
    * OCR baseline replaced: 317 entries, 41,873 words.
    * Disputes (2,064) and queue rows (1,954) are unchanged in count.
      `אגמ`'s extra 15 words were a run longer than `--max-span 4`: dropped
      before, matched now.
    * Against the 100 reviewed entries (13,735 words): words 0.9509 -> 0.9514,
      chars 0.9873 -> 0.9878, coverage 0.9881 -> 0.9891; nun/gimel stays at 6.
    * Live :8421: 317 entries, every one loads, 0 duplicate queue keys.
      1,954 witness rows, 0 on another page than their word, and the same 4
      words unaligned as before. All 94 witness pages load. The three `צרי`
      heading concerns are now 83, 175 and 203.
    **Two gaps in the rebuild itself, found while running it.**
    * The corpus README's chain never regenerated `klalim_demo_dataset.json`,
      which is the dashboard's entry list. After the whole chain, and a
      restart, :8421 still served 318 entries and the old 16.
      `pipeline/build_klalim_demo_dataset.py` is now in the chain, right after
      `build_root_corpus`.
    * A renumbering trips three guards in turn:
      - `build_header_alignment.py` refuses on 83 "page moves" that are all
        the same entries one id lower;
      - `seed_word_identity.py --apply` will not reseed without `--reseed`;
      - `snapshot_ocr_baseline.py --replace` then refuses too.
      My first run piped every step through `tail` under `set -e`, which hid
      all three refusals. The witness steps then ran on the new text with the
      old ids. I re-ran it step by step, checking each exit code. As `0GG`
      did, the alignment was written to scratch and compared BY ROOT before it
      was installed. The corpus README now says so.

0GL. **[2026-09-14, reviewer: "where do I look?" - for the two-readings spots]
    THE FIVE SPOTS ARE REACHABLE, BUT THE POPUP CANNOT RECORD THE FIX THREE OF
    THEM NEED: "REMOVE THIS WORD". THAT IS ALL 116 `one_side_empty` ROWS.** Not
    fixed; put to the reviewer.

    Where DocAI returned two different readings of one printed word, both are
    in the text, and each has a witness row on or next to it:
    <http://127.0.0.1:8421/entry/62/word/24> `אי אין` (their `איןפירושו`),
    <http://127.0.0.1:8421/entry/100/word/330> `באפין באפיו`,
    <http://127.0.0.1:8421/entry/139/word/117> `תי חבורותי` (their `חבורתי.`),
    <http://127.0.0.1:8421/entry/212/word/90> `ובשרש בשרש`,
    <http://127.0.0.1:8421/entry/248/word/75> `ות בגדרות`.
    At 100, 212 and 248 the row is `one_side_empty` - their text has nothing
    where we have the extra word - so the popup offers only our word,
    "Unreadable" and Custom, and Custom refuses an empty reading:

        review_frontend/app.js:3965 (witness panel save)
        if (!text) { alert('Enter the custom reading first.'); return; }

    The manual panel has a Remove option, but a word carrying a witness row
    opens the witness panel instead. Extent: all 116 `one_side_empty` rows are
    this shape (their side empty; none the other way - a word only they have
    has no token of ours to anchor to, `0GF`'s unanchorable 55); 38 are in
    reviewed entries, every one `unchanged` by their corrector. And a witness
    ruling, once recorded, still reaches the corpus by no code path (`0EA`).
    Proposed: a "Remove this word" option on a witness row whose other side is
    empty, recorded as a deletion; the `witness_choice` apply path is the
    auto-adopt work already queued.

    **BOTH DONE 2026-09-14 (reviewer: "do 1. do 2. but don't turn it on - we
    need to retain the option to wipe the corpus").**
    1. The witness popup offers "Remove this word - <witness> has nothing here"
       on a row whose witness side is empty and ours is not, recorded as
       `chosen_source: remove`, `chosen_text: ""`; the word shows struck
       through, and "Current decision" reads "(remove this word)". Checked live
       on entry 100 w330 (offered) and 139 w117 (not offered - they have a
       reading) WITHOUT saving: HaShorashim's ledger is still 0 bytes, so the
       corpus is still a rebuild of the OCR. Test
       `test_a_witness_row_with_nothing_on_their_side_offers_to_remove_our_word`
       on a new fixture row (klal 4 w1, their side empty), failing when the
       option is disabled.
    2. **The apply path is BUILT AND OFF.** `apply_reviewer_decisions.py
       --apply-witness-choices` promotes witness rulings through
       `witness_choice_edit()`: the position is the ruling's snapshot
       `word_index`, and the snapshot's `master_reading` must still be there
       (drift otherwise); `remove` deletes, `unreadable` applies nothing, the
       rest replace, and a word-count change takes the same one-per-klal-per-run
       gate as every other path. WITHOUT the flag a run applies none of them
       and prints how many are waiting. It has not been run on either corpus.
       The applier writes part1.json only when a counter moved, and a
       witness-only run must count - that line was missing from the first
       version and is what the gating test caught under mutation. Tests
       `test_a_witness_ruling_says_exactly_what_it_does_to_the_words`,
       `test_witness_rulings_reach_the_corpus_only_when_asked_for_by_name`.
    **Before turning it on**, one caveat the reviewer should hold: a witness
    ruling is keyed by entry and OCR token, and a corpus rebuild renumbers
    entries (`0GG` shifted every id from 85 up), so rulings recorded now and
    then followed by a wipe would need re-pointing - each carries its row
    (page, bbox, readings) to do it with. `audit_applied_decisions.py` does not
    yet check witness rulings either.

0GK. **[2026-09-14, reviewer on <http://127.0.0.1:8421/entry/1/word/81>: "the
    text is clearly maleh - with the vav. so our reading matches the text.
    explain your note about the pasuk - i see the pasuk is written chaser but
    the discussion repeats the word maleh"] THE VAV/YOD TIER NOTE TALKS ABOUT
    QUOTATIONS ON EVERY ROW - 258 OF 684 ARE NOT KNOWN TO BE IN ONE. Not fixed;
    put to the reviewer.**

    Entry 1: w64-67 is the quotation of <https://www.sefaria.org/Song_of_Songs.6.11>,
    `הפרחה הגפן הנצו הרמנים` (chaser, as the verse), footnote 4; w78-81 is Ibn
    Janah repeating the phrase in his own argument, and there the page prints
    `הרמונים` maleh (the reviewer, from the ink). Ours reads `הרמונים`; Sefaria's
    OCR and corrected text both read `הרמנים.` - the Bible's spelling carried into
    the author's repetition, `unchanged` by their corrector. So at w81 OUR reading
    is the page's and theirs is not. The row has no verse record at all: their
    last footnote is at the quotation, so nothing follows the word.

    The popup nonetheless says, from `witnessTierNote()`:

        C_spelling_vav_yod: 'The same word spelled with or without a vav/yod. Their verse quotations come from a pointed Tanakh, so inside a quotation their spelling may be the Bible’s rather than this page’s.'

    - true of a word inside a quotation, and beside the point here. Measured on
    the 684 `C_spelling_vav_yod` rows: 426 have the word inside a matched
    quotation (THEIRS 330, neither 83, OURS 9, both 4); 258 do not, or it is not
    known - `not_in_quotation` 90, `uncorroborated` 130, no citation after the
    word 38. Proposed: the note says which of the three the row is, and for a
    word outside a quotation says the Bible's spelling is no reason for theirs.

    **FIXED 2026-09-14 (reviewer: "yes do both").** `vavYodNote()` in app.js
    reads the row's verse verdict: inside a matched quotation it keeps the
    Tanakh-spelling caution; `not_in_quotation`, `uncorroborated` and no
    citation each say so, and that the page decides. Checked in a browser on
    w81 (no citation follows), entry 1 w20 (inside a quotation) and entry 21
    w61 (not in the quotation).

    **AND THE DOUBLED-TOKEN FIX `0GG` RECORDED, FIXED THE SAME TURN.**
    `build_root_corpus.drop_doubled_tokens()` keeps one token where DocAI
    returned the same text twice over the same ink (overlap >= 0.8 of the
    smaller box; the 18 real doubles overlap 0.87-1.0, p87's second-row words
    0.72-0.74 and survive; two different words are never touched). 25 tokens
    dropped: the 18 doubled words and six doubled numerals and marks (`23 23`,
    `18 18`, `26 26`, `27 27`, `37 37`, `" "`), each checked adjacent to its twin
    in the old text. 20 entries changed and nothing else; consecutive doubled
    words 43 -> 25. Rebuilt downstream (ledger empty): alignment 0 page or trust
    changes, word ids reseeded and verified, baseline 41,873 words, disputes
    2,078 -> 2,064, queue 1,954 anchored (0 duplicate keys, 0 wrong-page rows,
    318/318 entries 200), heading concerns still 3. Against the reviewed
    entries: words 0.9507 -> 0.9509, precision 0.9864 -> 0.9868, coverage
    unchanged. The five different-text pairs (two readings of one stretch of
    ink) are still both in the text. Test:
    `test_a_word_docai_returned_twice_over_the_same_ink_is_kept_once`, failing
    with the bar lowered to 0.7.

0GJ. **[2026-09-14, reviewer: "you have the titles as the first word - but should
    be the first three - the shoresh. and test - any time those three words are
    not the name of three letters, we have a concern"] THE WHOLE ROOT IS THE
    HEADING NOW, AND A HEADING WORD THAT IS NOT A LETTER'S NAME IS A CONCERN ON
    SCREEN. THREE ENTRIES CARRY ONE; THE INK SPLITS THEM TWO TO ONE.**

    **Why the page styled one word.** `corpus_io.title_word_span()` skipped
    `words[0]` as "the gematria marker". Yad Malachi has one; Sefer HaShorashim's
    entries open with the heading itself, so the span matched nothing on all 318
    and the page styled word 0 alone - as a marker - and the rest of the root as
    body text:

        pipeline/corpus_io.py (before)
        for raw in words[1:]:                     # words[0] is the gematria marker

    **Fixed:** `title_word_run()` returns where the heading starts - after a
    marker, tried first, or at word 0 - and the heading's own punctuation is
    skipped as the body's always was (a `[` before it, entry 103; a period inside
    it, `הגימל . והרש והבית .`, entry 304), without swallowing an opening bracket
    that begins the text after it (entries 134, 225, 230). The server serves
    `title_word_start`; `markTitleRun()` styles a marker only when there is one.
    Measured: Yad Malachi's 667 klalim across all three part files give exactly
    the committed spans; HaShorashim's 318 all find the whole heading at word 0
    (0 before).

    **The concern.** `detect_root_entries.heading_concerns()` - beside the
    vocabulary it checks - requires every heading word to be a letter name in
    the edition's spelling, the doubling word, or a homograph qualifier; a
    spelling the matcher tolerates that is not a letter's name (`OCR_VARIANTS`:
    `צרי` for `צדי`, `נימל` for `גימל`) is a concern, and so is a root the names
    do not spell. `tools/check_letter_headings.py` writes
    `heading_concerns.json`; the server attaches a row only while the entry's
    title is still the one checked, and the `✎ Heading` control shows
    "⚠ concern" with the reasons in its tooltip. The 7 headings carrying a
    qualifier (`עוד`, `הרפה`, `הנראית`...) are not concerns.

    **Three concerns, and what the page prints** (NLI photograph and the Google
    copy at 500 dpi, which agree):
    * <http://127.0.0.1:8421/entry/84> `האלף והמם והצרי .` - the page PRINTS
      `והצרי`, with a resh (p87). Our heading is the page; Sefaria writes `צד'י`.
    * <http://127.0.0.1:8421/entry/176> `הבית והיוד והצרי .` - also printed
      `והצרי` (p112).
    * <http://127.0.0.1:8421/entry/204> `הבית והצרי והעין .` - the page prints
      `והצדי` (p120, like every other heading there): DocAI read the dalet as a
      resh. **A data issue in our stored heading**, for the reviewer through
      `✎ Heading`.
    So `צרי` is not only an OCR confusion, as `LETTER_NAMES`' comment said -
    corrected there. The concern text says the ink decides and does not say
    which way.

    Tests: `test_the_heading_is_found_after_a_marker_or_at_word_0`,
    `test_a_heading_word_that_is_not_a_letter_name_is_a_concern`.

    **FOUND WHILE VERIFYING - EVERY HASHORASHIM LINK ABOVE ENTRY 222 BLANKED THE
    PAGE.** A fresh browser on `/entry/304` built 0 blocks: `routeToKlal()` asked
    `partForKlal()`, which was Yad Malachi's chunking written into the page -

        review_frontend/app.js (before)
        function partForKlal(klalId) {
          if (klalId <= 222) return '1';
          if (klalId <= 444) return '2';
          return '3';
        }

    - so it switched to "part 2", which Sefer HaShorashim (one part, 1-318) does
    not have, and the pane emptied. Links below 223 worked, which is why every
    check until now passed; links given in this file and in chat to entries 248,
    254, 270, 280 and 304 did not. The server had replaced the same ladder with
    `corpus_io.part_number_for_klal()` long ago; the page kept its copy (Lesson
    13). Fixed: `/api/corpus` serves `parts` from book.json and `partForKlal()`
    reads them, the ladder remaining only for a server too old to send them.
    Still latent, not fixed: the part selector offers Parts 2 and 3 on a
    one-part book, and picking one shows an empty list (UI tests select Parts 2
    and 3 on the one-part fixture on purpose, so trimming it is its own change).

0GI. **[2026-09-14, reviewer, on <http://127.0.0.1:8421/entry/58/word/11>]
    TWO POPUP DEFECTS: A TOKEN NUMBER NOBODY CAN USE, AND A VERSE SHOWN FOR A
    WORD THAT IS IN NO QUOTATION - 492 ROWS, WITH A FALSE EXPLANATION.** Plus a
    third, reported the same turn on <http://127.0.0.1:8421/entry/69/word/23>:
    "i don't see sef. correction".

    **ALL THREE FIXED 2026-09-14 (reviewer: "do that").**
    * The label reads `word N` (the URL's number); rows with no word position
      keep `OCR token #N`, labelled.
    * `adjudicate_against_verse.verdict_for()` (extracted from `main()`) writes
      `not_in_quotation` for a matched quotation the word lies outside - 492 -
      and keeps `uncorroborated` for the 295 that matched under 2 words. The
      popup shows no verse for `not_in_quotation`, one line saying no cited
      verse covers the word.
    * **Entry 69 w23 had no row at all.** Rows came only from disputes, and both
      OCRs read `גמרה` there, so their correction `גרמה` had nothing to hang on -
      `0GF` had counted it among the unsurfaced. `build_witness_review_queue.py
      --witness-text` now adds a `their_correction_only` row for every reading
      correction at a word both OCRs read alike (the SHARED rows of `0GH`'s
      tool): 1 today, served, 0 colliding with a dispute's token. And
      `corrected_status()` called that case `same_letters` - markup - which
      `test_an_unchanged_word_in_the_corrected_text_is_not_agreement` ASSERTED,
      on these very letters: a test pinned to the defect (Lesson 36). It is
      `changed_from_both` now, and the line is inverted with a comment saying so.
    Verified live on :8421: both popups rendered in a browser - 58 w11 reads
    "word 11", no Genesis 2:6, "No cited verse covers this word"; 69 w23 shows
    both OCRs' `גמרה` and "Sefaria corrected text (changed - both OCRs read
    otherwise): `גרמה`". Queue 1,968 rows, 0 duplicate keys, 0 wrong-page rows,
    318/318 entries 200. Tests `test_a_word_outside_the_quotation_is_not_judged_
    by_its_verse` and `test_a_correction_at_a_word_both_ocrs_read_alike_becomes_
    a_row`, each failing under a mutation that undoes its fix.

    The original report, as written before the fix:

    **1. "Token #167" names the right word in an index space nobody sees.** The
    box is on `הוא` (raw OCR token 210 on p73). `page_token_index` 167 counts
    only letter-bearing tokens - the space `api_witness_context` slices
    (`review_server.py:1820`, `dtoks`) - and is neither the raw token (210) nor
    the word's place in the entry (11, the number in the URL):

        review_frontend/app.js:3832
        <div class="panel-label">${entryRefName(w.klal_id)} · Token #${w.page_token_index ?? w.docai_token_index} · tier ${w.tier} · page ${w.page}</div>

    Proposed: show `word N` when the row has a `word_index` (every HaShorashim
    row), the token index only as a labelled fallback (Yad Malachi rows with
    `word_index: null`, `0EA`).

    **2. The verse belongs to the NEXT quotation.** The word is Ibn Janah's own
    gloss right after <https://www.sefaria.org/Proverbs.1.26>'s quotation (`...
    באידכם אשחק ¹⁹ הוא הצער`); that marker is at the word, so the tool took the
    next one, <https://www.sefaria.org/Genesis.2.6>, whose quotation `ואד יעלה מן
    הארץ` matched 4 words (corroboration 0.8) and stops well after the word. The
    tool's verdict merges two different situations:

        tools/adjudicate_against_verse.py:448
        if matched < args.min_matched or not (start <= pos < anchor):
            verdict = "uncorroborated"

    and the popup explains all of them with the first one's sentence:

        review_frontend/app.js:4984
        uncorroborated: 'The quotation could not be matched to the cited verse, so the verse cannot rule here.',

    Measured on the 787 `uncorroborated` rows: **295** matched fewer than 2
    words (the sentence is true); **492** matched 2+ and the disputed word is
    simply outside the quotation - the sentence is false, and the verse shown is
    not evidence about the word at all. So the 1,616 rows "with a cited verse"
    (`0GE`, `0GG`) are really 1,124 where a verse is at least near, and 829
    where a verse bears on the word (THEIRS 586, neither 212, OURS 21, both 10).

    Proposed: the tool writes `not_in_quotation` for the second case, and the
    popup shows NO verse for it - at most one line saying the word is in Ibn
    Janah's own words - keeping "could not be matched" for the 295.

0GH. **[2026-09-14, reviewer: "how many corrections did Sefaria make, how many
    where our OCR differs from theirs, all the ones where we argue with their
    correction, the value we add, and how much the better scan helped"]
    MEASURED ON THEIR 100 REVIEWED ENTRIES: THEY MADE 90 LETTER CORRECTIONS;
    OUR DISAGREEMENT WITH THEIR OCR SITS ON 89 OF THEM, AND OUR TEXT ALREADY
    HOLDS 78. THREE OF THEIR CORRECTIONS DEPART FROM THE PRINTED PAGE.**

    `tools/measure_correction_overlap.py` (new): their raw OCR (T), their
    reviewed text (C), ours (O); every T->C difference classified, and located
    in O through the words where O and T agree. Letters only (points deleted,
    punctuation separating - the review queue's normalisation); a
    punctuation-only change is not counted. The `אלה a`/`אלה b` halves are
    joined, so 99 roots = the 100 entries. Test:
    `test_the_correction_overlap_tells_had_shared_and_third_apart`.

    **Their edits: 114** - 90 letter corrections, 15 citations added inline, 7
    word-division changes, 2 bracketed insertions. (`0FK` counted 107
    corrections on a different tokenization; this is the count on the queue's.)

    Three corpora, the SCAN the only difference between the last two -
    `bitonal` is the Google scan's tokens through today's pipeline, built in a
    scratch corpus root:

                                       pre-NLI   bitonal    NLI
                                      (1caef3f)   today    today
        words vs their corrected        0.8939   0.9170   0.9507
        chars                           0.9561   0.9774   0.9871
        precision                       0.9225   0.9703   0.9864
        nun/gimel errors                    88       88        6
        of their 90 corrections, ours:
          already reads the correction      72       72       78
          reads their original error         1        1        1
          reads a third thing               16       17       11
        ours differs from their OCR,
          reviewed entries (positions)    1139     1123      703
          whole slice (<=4-word, queue)   3180     3198     2078
        ours differs from their corrected 1069     1053      628

    **The value, stated as what it is.** A reviewer who looked only at the 703
    places our OCR disagrees with theirs - 5% of the 13,735 words - would reach
    89 of the 90 corrections their reviewer found by reading everything, and
    for 78 of them our reading IS the fix. 13% of those 703 are their errors;
    the rest are ours or spelling/markup. The better scan kept that recall and
    cut the places to look from 1,123 to 703 (-37%), and our pre-filled fixes
    from 72 to 78. It does NOT make our text the better base: ours still differs
    from their corrected text at 628 positions, their raw OCR at 114 edits
    (`0EZ`'s conclusion stands). Extrapolation, labelled as one: the 214
    unreviewed roots of the slice carry 1,432 such positions; at the reviewed
    rate, ~180 would be their errors. The reviewed entries are all in א.

    **All 12 places our text disagrees with their correction, read off the NLI
    scan** (300 dpi crops of the native 150; the letters at issue are clear):
    * **The page backs OUR reading against their correction - 3 (data issues in
      THEIR text, for the Sefaria editor):**
      <http://127.0.0.1:8421/entry/58/word/11> prints `הוא`, their correction
      `והוא` adds a vav (their raw OCR there is `וצא` - 2 of 3 letters wrong -
      and their footnote anchor for <https://www.sefaria.org/Proverbs.1.26>
      sits on that very token, where the page has its superscript 19; it looks
      as if the corrector fixed `צא` and kept the OCR's leading vav - inferred,
      not shown); <http://127.0.0.1:8421/entry/69/word/23> prints `גמרה`
      (both OCRs agree), their `גרמה` reorders the printed letters - an
      emendation, against their own fidelity standard;
      <http://127.0.0.1:8421/entry/80/word/389> prints `וזה`, their `ווזה` has an
      extra vav.
    * **Our footnote marker glued to the right word - 5**, their correction
      right: entry 39 w120, 42 w36, 83 w267, 88 w58, 90 w53.
    * **Our misreads - 4**, their correction right: 39 w250 `אד'`, 39 w305
      `מנד'`, 56 w209 `ג'זאיר`, 88 w51 `כל'` (the geresh read as a yod by both
      OCRs).
    `0FB`'s 19-of-34 "ink backs OUR reading" came from the vision adjudicator on
    the old corpus and a different sample; this is a direct read of every row.

    **Paused for this:** the doubled-token fix `0GG` records. Its sweep of Yad
    Malachi's DocAI pages found 60 same-text and 241 different-text overlapping
    token pairs; whether any reached that book's reviewed corpus is NOT measured.

0GG. **[2026-09-14, reviewer: "go" on the heading problems] THE FOUR LOST
    HEADINGS ARE BACK - `אמר`, `בוצ`, `במ`, `גרב`. TWO WERE LINE MERGES AND TWO
    WERE THE HEADING PATTERN, AND EVERY CAUSE WAS READ OFF THE INK FIRST.**

    Swept first: 4 of Sefaria's roots had no entry of ours; the text layer knew
    2 of them (p87, p116) and neither of the other two.

    * **p116, `במ` - skew.** The photograph is tilted ~0.75 deg (page slope
      -0.013); the heading line's tops climb 0.7807 -> 0.7931 and
      `page_lines()`' chain (consecutive tops within `LINE_TOL`) walked into the
      next line, interleaving `הבית והמם .` with `הבמות לא סרו`.
    * **p87, `אמר` - DocAI's boxes, not skew** (slope 0.000). The printed second
      line (`ונשלם בספר התוספת...`) has no row of its own: DocAI returned it with
      every box starting inside line 1 and half again as tall (tops 0.6485 vs
      0.6425, heights 0.0345 vs 0.0230), plus a copy of line 1's last word
      (`הרפיון`, same x). This settles what `0FZ` left undetermined. My first
      account to the reviewer - "a second reading of line 1" - was wrong, said
      before I had looked for line 2 anywhere on the page.
    * **p148, `גרב` - the pattern.** The page prints `הגימל. והרש והבית.`, a
      period after the first letter name, in the NLI photograph and the Google
      copy alike; p585 prints `השין. והרש והפא.` the same way. The matcher
      demanded the second name straight after the first.
    * **p108, `בוץ` - the pattern.** The page prints `הבית והואו והצירי.` -
      `צירי` for tsadi, the same four letters in the Google copy at 450 dpi, and
      the only heading-shaped `צירי` in either text layer. `0FI` had filed
      `הצירי` as a vowel-name QUALIFIER from this very line; after the list's
      vav the qualifier could never match, so בוץ merged into בוס.

    **Fixed.** `tools/detect_root_entries.py`: `צירי` is a letter name, `הצירי`
    is no longer a qualifier, and an optional period may follow the first name.
    Swept old against new over both text layers (651 pages) and the DocAI
    stream: +`בוצ` p108, +`גרב` p148, +`שרפ` p585 (Google layer only, outside
    the corpus); no other line changes. `tools/build_root_corpus.py`:
    `_split_merged_rows()` cuts a chained line whose words clash horizontally -
    two different words on one stretch of a printed line - at its largest
    centre gap on the page's deskewed level, only when >=3 clashing words sit on
    EACH side, recursively.

    **The first version regressed and was replaced before it reached the corpus**
    (one retune, per Lesson 31 - a third would have been handed back). Grouping
    EVERY line on the deskewed level fixed p116 and split six lines that had been
    right: p68 a raised `31`, p78 a page number, p88 `שהיא שרש`, p95 `והם`, p115
    `י"י באפו`, and p103 the heading word `הבית` - which loses the root באש -
    under a slope of only -0.001: the chain's hard threshold turns any shift into
    a split. Its row split also fired on single pairs of alternate readings (p74
    `אי`/`אין`, p92 `באפיו`/`באפין`, p103 `חבורותי`/`תי`). The final version
    leaves every line without a row of clashes exactly as it was. Line diff over
    94 pages: 7 change - p87 and p116's headings, and p70, p95, p112, p128 and
    p144, whose interleaved APPARATUS lines now read in order.

    **Rebuilt** (HaShorashim ledger empty, checked before writing): root
    entries 1,927 -> 1,930; corpus 314 -> 318 - exactly the four gained,
    <http://127.0.0.1:8421/entry/85> `אמר` (p87, 129 words),
    <http://127.0.0.1:8421/entry/159> `בוץ` (p108, 55),
    <http://127.0.0.1:8421/entry/193> `במ` (p116, 57),
    <http://127.0.0.1:8421/entry/304> `גרב` (p148, 8), and their four neighbours
    shortened at exactly the absorbed heading (`אמצ` 249 -> 120, `בוס` 122 ->
    67, `בלת` 264 -> 207, `גרר` 223 -> 215); the other 310 byte-identical.
    `suspect_merge` 3 -> 0. Against the reviewed entries (99 in every source,
    13,619 words): words 0.9491 -> **0.9514**, chars 0.9852 -> **0.9877**,
    precision 0.9786 -> **0.9869**, coverage 0.9887 unchanged; 100 of 100
    reviewed entries now match. Alignment by root: 0 page moves, 0 trust
    changes, the four new entries trusted (271/314 -> 275/318). Word ids
    reseeded - `--verify` first showed the old sidecar naming the wrong words
    from entry 85 on, as a renumbering must - and the OCR baseline replaced.
    Disputes 2,062 -> 2,078 (the new roots 9/3/2/2; Sefaria compared on 317
    entries); queue 1,967 anchored, 1,616 with a cited verse. Live :8421: 318
    entries, all 200, 0 duplicate queue keys, the four new headings render;
    0 of the 1,963 rows whose word aligns sit on another page (4 words do not
    align). Gate 542 passed; UI + fixture + witness-engine 126 passed, 1
    skipped. Tests, each seen to fail on the old code first:
    `test_a_skewed_page_does_not_chain_two_printed_lines_into_one`,
    `test_a_row_boxed_up_into_the_line_above_is_split_off_not_interleaved`,
    `test_a_heading_may_print_a_period_after_its_first_letter_name`.

    **FOUND ON THE WAY, NOT FIXED - DocAI emits one word twice at one spot.**
    19 same-text token pairs with boxes overlapping >=0.87 on pages 58-151
    (outside p87's row case), and 18 of them put a doubled word into the corpus
    text - matched by word and page to the pairs; the ink is not checked one by
    one: <http://127.0.0.1:8421/entry/40/word/6> `אזוב`,
    <http://127.0.0.1:8421/entry/45/word/24> `האח` (three in a row where the
    Psalms phrase, e.g. <https://www.sefaria.org/Psalms.35.21>, has two),
    <http://127.0.0.1:8421/entry/47/word/407> `יפריא`,
    <http://127.0.0.1:8421/entry/50/word/225> `אבד`,
    <http://127.0.0.1:8421/entry/59/word/57> `זה`,
    <http://127.0.0.1:8421/entry/100/word/265> `וישתחו`,
    <http://127.0.0.1:8421/entry/115/word/121> `נפתחו`,
    <http://127.0.0.1:8421/entry/133/word/217> `ושתי`,
    <http://127.0.0.1:8421/entry/133/word/1182> `אשורים`,
    <http://127.0.0.1:8421/entry/134/word/430> `את`,
    <http://127.0.0.1:8421/entry/139/word/6> `היאר`,
    <http://127.0.0.1:8421/entry/141/word/132> `הנדה`,
    <http://127.0.0.1:8421/entry/206/word/55> `אם` and w57 `במבצרים`,
    <http://127.0.0.1:8421/entry/248/word/163> `החצר`,
    <http://127.0.0.1:8421/entry/254/word/10> `גובי`,
    <http://127.0.0.1:8421/entry/270/word/52> `כחשים`,
    <http://127.0.0.1:8421/entry/280/word/17> `במשנה`. The corpus holds 43
    consecutive doubled words in all; the other 25 are not claimed either way
    (many are real biblical doublings - `איש איש`, `מאד מאד`, `גבוהה גבוהה`).
    16 of the 18 already sit within one word of a Sefaria queue row; entry 59
    w57 and entry 206 w57 do not.
    Five more pairs overlap with DIFFERENT text - two readings of one stretch
    of ink (p74 `אי`/`אין`, p92, p103, p123 `בשרש`/`ובשרש`, p135) - and both
    readings are in the text. The fix is in `build_root_corpus.py`, not the
    ledger: one token per stretch of ink. Not done here, so this change
    measures one thing.

0GF. **[2026-09-14, reviewer: "are there still unsurfaced corrections or
    disputes?"] YES - INVENTORIED BY CLASS. THE BIGGEST IS ~1,370 WORDS OF
    APPARATUS-LIKE TEXT IN THE BODY THAT NO DISPUTE EVER SHOWS.** HaShorashim,
    measured on the 2026-09-14 build (2,054 disputes, 1,945 served).

    * **Served and drawn: all of it.** 0 queue rows share a word; the server
      holds no witness row the text pane cannot draw.
    * **109 disputes not served.** 54 are Sefaria's bracketed `[...]` insertions,
      skipped as editorial by design (`[י]צמח`, `[או]`) - a filter that hides
      (Lesson 26); whether the brackets are PRINTED is unchecked. 55 cannot be
      anchored - mostly one-sided insert/delete, including moved words (klal 18:
      `הזאת` at w37 on one side, w49 on the other).
    * **52 differences longer than 4 words are DROPPED** by
      `build_witness_disputes.py --max-span 4` as "an alignment failure" - and
      they are the most serious rows (Lesson 26). 41 are runs only OUR text has,
      **1,368 words, 35 of them carrying apparatus vocabulary** (`מוסיף`, `חסר`,
      `בע`, `עיין`...) - Bacher's footnote apparatus left in the body text, e.g.
      <http://127.0.0.1:8421/entry/4/word/135> (a 72-word run beginning
      `לא יצמח נער מוסיף`). Mostly INHERITED: the pre-rebuild corpus had 42
      such runs, 1,207 words (885 apparatus-like); today's has 1,112
      apparatus-like - about 160 words worse. 3 are runs only THEY have: entry
      15 w140 is really our entry 16 (`אג`) - their data has no `אג` key and
      runs it into the previous entry, so entry 16 is never compared at all;
      <http://127.0.0.1:8421/entry/201/word/77> (13 words from `מה בצע בדמי`)
      and <http://127.0.0.1:8421/entry/314/word/180> (the section heading
      `המאמר הרביעי...`) are unchecked. 8 are long replacements, some of them
      their writing out an abbreviated quotation.
    * **3 Sefaria corrections where our OCR equals theirs**, so no dispute exists
      and nothing shows them:
      <http://127.0.0.1:8421/entry/56/word/209> (`נזאיר ולרזנים` -> `ג'זאיר.
      ולרוזנים או`), <http://127.0.0.1:8421/entry/69/word/23> (`גמרה` ->
      `גרמה`), <http://127.0.0.1:8421/entry/87/word/53> (`כלי` -> `כל'`);
      plus 9 citations they added. (A first count said 25; it included the
      dropped long spans above - corrected.)
    * **The two lost headings** (`0GC`): `suspect_merge` on entries 84, 189, 190
      is still rendered nowhere. **Headings recovered 2026-09-14 (`0GG`)**; no
      entry carries the flag now, and it is still rendered nowhere.
    * **THE APPARATUS LEAK - FIXED 2026-09-14 (reviewer: "yes").** Cause, from
      the line dump: on the full-tone crops the variant apparatus is set at
      0.80-1.08 of body size, and `classify()`'s bottom-up small-type scan
      stopped at the first larger line - on p99 its LAST line (0.77) abandoned
      the whole citation list. `build_root_corpus.py` now cuts by LAYOUT: a
      printed rule (`find_rule_y`: one concentrated, isolated long run of ink -
      49 pages), else a gap >= 1.35 pitches whose next line STARTS as apparatus
      starts (`gap_cut_index`: note letter read as `ל`/`לא`/`לב`..., or a
      numeral - 43 pages); type size is consulted by neither. The first rule
      detector saw nothing (its threshold was text-dark; the hairline is grey);
      the second fired on Hebrew baselines and was fixed by concentration and
      isolation; not loosened further (Lesson 31), though it misses rules the eye
      sees on p69/p95/p104 - the gap signal covers them. Measured against the
      100 reviewed entries, words 0.9287 -> **0.9491**, chars 0.9663 ->
      **0.9852**, precision 0.9353 -> **0.9786**, coverage **0.9887 unchanged**
      (nothing reviewed was removed). Ours-only runs >4 words: 41 runs / 1,368
      words -> **7 / 223**, apparatus-like 1,112 -> 12. Body 43,821 -> 41,897
      words. Left: one variant-note line on p134 (no gap above it; entry 243
      w82), and runs that are HEADING problems, not apparatus - the two known
      merges (84, 190) and what look like absorbed headings in 157
      (`הבית והואו והצירי`) and 300 (`הגימל והרש והבית`) - all four fixed
      2026-09-14, `0GG`. Rebuilt downstream:
      alignment (0 moves by root), word ids reseeded (no rulings exist), OCR
      baseline replaced, disputes 2,062, queue 1,952 - 0 duplicate keys,
      314/314 entries 200, 0 wrong-page rows, 0 context mismatches. Test:
      `test_the_apparatus_is_cut_by_layout_not_type_size`; gate 539 passed.
    * **Yad Malachi, not re-measured today:** `0CO` (164 red words outside the
      ranked queue, 2026-09-07) and `0CV` (136 detector positions no route
      reaches) are still open as recorded.
    * **RE-CHECKED 2026-09-14, after `0GG` renumbered every entry from 85 up.**
      The links above for entries 85 and later point at the wrong entry now.
      The 13-word run `מה בצע בדמי` is at
      <http://127.0.0.1:8421/entry/204/word/21> (it was 201 w77). The
      section-heading run `המאמר הרביעי` no longer occurs verbatim in any
      entry, and whether it was cut or only re-tokenized is unchecked. The p134
      variant line is in one of entries 238-246 (pages 133-134); its current id
      is not pinned. Entry 16 (`אג`) still has **0 witness rows**
      (<http://127.0.0.1:8421/entry/16>), so it is still never compared.

0GE. **[2026-09-14, reviewer: "this is a direct quote from the Torah - are we
    not checking that?"] THE VERSE CHECK EXISTS, RUNS, AND REACHES NO SCREEN - AND
    SHOWN AS A VERDICT IT WOULD IMPOSE THE BIBLE'S SPELLING ON THIS EDITION.**

    The case: <http://127.0.0.1:8421/entry/21/word/127>, stored `בארם לעולם`,
    quoting [Genesis 6:3](https://www.sefaria.org/Genesis.6.3) (footnote 20,
    `(בראשית ו, ג)`). The PAGE prints `באדם לעולם` - and the dalet cannot be
    read by eye: at this scan's resolution it is shape-identical to a resh (a 5x
    crop first looked like `בארם`). It was settled by a CONTROL: the certain
    dalet of `האדמה` (`הנלקח מן האדמה`) on the line above has the same glyph,
    and the word is the entry's own root, `אדם`. DocAI read that one glyph shape
    as dalet in `האדמה` and as resh here. (This line was first written as
    "crop read at 5x" before the 5x crop had been looked at - corrected.) The verse
    reads `בָֽאָדָם֙ לְעֹלָ֔ם` - letters `באדם לעלם`. So: our OCR `בארם לעולם`
    misreads the dalet; Sefaria's `באדם לעלם` (OCR and corrected alike) carries
    the Bible's defective `לעלם` where this printing has the plene `לעולם`. NO
    candidate is what the page prints, and the verse is right about the dalet
    and not about the vav.

    `tools/adjudicate_against_verse.py` (`0FF`) reaches this row and rules
    THEIRS - both of their words are in the verse. Rerun 2026-09-14 on today's
    1,905 disputes: 1,477 reach a cited verse; THEIRS 547, OURS 18, both 11,
    neither 195, uncorroborated 706. It writes a file nothing in `pipeline/` or
    `review_frontend/` reads (Lesson 32 PRINTING IS NOT RUNNING).

    **Of the 547 THEIRS verdicts, 379 differ only by a vav/yod** - where the
    Masoretic text is evidence about the Bible's spelling, not this compositor's
    (Lesson 38 ANOTHER BOOK IS NOT A SECOND OPINION; Sefaria's own standard is
    fidelity to the edition). 133 are real letter differences, where the verse
    IS strong evidence; 20 mix both; 15 are unequal spans.

    **Spans bundle independent differences.** 125 queue rows are multi-word
    spans of equal length on both sides; 51 of them mix a letter difference with
    a vav/yod one (w127 among them), so no offered reading can be right and the
    reviewer must type a custom one.

    **BUILT 2026-09-14 (reviewer: "go").** (i) `disputes_for()` splits an
    equal-length replace into one row per differing word; maqaf pieces sharing a
    corpus position stay one row, so no two rows claim one token. Disputes
    1,905 -> 2,054; anchored 1,945; klal 21 is now w127 `בארם`/`באדם` (tier
    C_both_attested) and w128 `לעולם`/`לעלם` (C_spelling_vav_yod). (ii) The verse
    tool writes the pointed `verse_text`; `build_witness_review_queue.py
    --verse-verdicts` attaches a `verse` record to each row - ref, Sefaria link,
    the note as printed, the verse, the verdict and `spelling_only`; the server
    passes it; the panel shows "Cited verse" as EVIDENCE, never a selectable
    reading, and for a spelling-only difference says the verse cannot settle
    this edition's spelling. Of 1,597 rows with a cited verse: THEIRS 159 +
    417 spelling-only, OURS 12 + 9 spelling-only, both 6 + 4, neither 117 + 91,
    uncorroborated 480 + 302. Verified: 0 duplicate keys, 314/314 entries 200,
    0 wrong-page rows, 0 context mismatches. Test:
    `test_a_multi_word_difference_becomes_one_row_per_word`.

0GD. **[2026-09-13] CODE REVIEW (high) OF `3006efe..HEAD` PLUS THE UNCOMMITTED
    TREE: 7 FINDINGS, ALL VERIFIED, NONE TOUCHES THE LEDGER OR `part1.json`.**
    Counts below are measured, not the reviewer-agent's estimates.

    **ALL SEVEN FIXED 2026-09-13/14 (reviewer: "go ahead fix"):**
    * 1: `classify()` tests a drift FIRST and `summarize()` re-judges every stored
      record: p48 is now FAIL and the tool exits 1 (272 PASS / 323 TEXT_ONLY /
      16 INCONCLUSIVE / 1 FAIL). Test: `..._reads_as_its_neighbour_is_a_failure_...`.
    * 2: rows are anchored to the WORD ALIGNMENT's own token
      (`scan_alignment.word_bboxes_resolved`, the server's own resolver), with a
      letters fallback that must be unique across ALL the entry's pages. Rows on
      a page other than their word's: 31 -> **0**. And it fixed most of `0GC`'s
      unreachable disputes: **anchored 826 of 1,847 -> 1,798 of 1,905** (1,794
      by the alignment); "word repeats on page" 329 -> 6; "no usable token"
      643 -> 49.
    * 3: `root_groups()`/`group_disputes()` align a homograph pair JOINTLY
      against the witness's one text and map each difference back to its entry
      - Sefaria keys by root and runs both headings together (`ארש`'s text holds
      `האל'ף והרי'ש והשי'ן` twice). 308 -> 313 entries compared; disputes 1,847
      -> 1,905. The queue's corrected-text step uses the same pairing; the
      versions endpoint returns `theirs_covers` and the read-only view says
      "their entry for this root also covers shoresh #N". `בכה`/`בלה` are real
      second entries (root_entries.json has both), not duplicates.
      Test: `test_a_homograph_pair_is_compared_against_the_one_text_...`.
    * 4: the five save/refresh redraws go through `redrawKlalBody()`, which
      honours the text view. No test (the fixture has no comparison texts).
    * 5: fixed with the reviewer's `punctuation_only` report (below).
    * 6: the PDF builder compares the recorded `nli_file`, not only the index.
    * 7: the ink search is centred on the offset under test (±`INK_WINDOW`), and
      the check renders the base PDF `page_image_sources.json` records, never
      the assembled full-tone PDF.

    **A REGRESSION THE FIX FOR 2 CAUSED, AND ITS FIX.** With rows on their words'
    own pages, (132, 138) existed on both p99 and p100; review_data's guard - which
    documents exactly this risk: "(klal_id, docai_token_index) alone - NOT page" -
    raised, and **every HaShorashim entry returned HTTP 500** until fixed. The
    guard did its job. `docai_token_index` is now ENTRY-relative (offset of the
    entry's earlier pages + index on the page), so the ledger key stays unique
    without adding a page to it; the page-relative index travels as
    `page_token_index` for the context endpoint, `verify_witness_vision` and
    `verify_witness_green_vision`. Yad Malachi's queue (another producer, one
    page per klal) is untouched. Verified: 0 duplicate keys, 314/314 entries 200,
    0 wrong-page rows, and the popup's context bracket lands on the row's own
    word for all 1,798 rows. Gate 537 passed.

    **UI suite: 107 passed, 1 skipped on an undisturbed run.** An earlier run
    showed 16 failed - self-inflicted, Lesson 44 DO NOT MUTATE A TREE YOU ARE
    EDITING: while it ran I restarted the dashboards twice with
    `pkill -f 'pipeline/review_server.py'`, which also matches the fixture
    servers the suite spawns, and edited served files under it. Restart the
    dashboards by the PID on :8420/:8421 (`lsof -ti tcp:8420`), never by pattern,
    while any test run is live.

    1. MEDIUM `tools/verify_nli_page_offset.py` - an offset drift is reported
       INCONCLUSIVE, not FAIL: a shifted page scores the right page below
       `MIN_TEXT_SCORE`, which is tested FIRST, and `summarize()` exits 0 unless
       FAIL. It already happened: **p48 is INCONCLUSIVE while p49's text scores
       0.594 against its image** - a real off-by-one, outside 58-151. The PDF
       builder refuses INCONCLUSIVE pages, so no wrong image was embedded.
    2. MEDIUM `tools/build_witness_review_queue.py` - each dispute is anchored on
       `d["page"]`, the entry's START page (`build_witness_disputes.py`), so a
       word on a continuation page is searched on the wrong page. **31 of 823
       served rows sit on a page other than their word's**, e.g.
       <http://127.0.0.1:8421/entry/23/word/93> (`אדירים`, anchored p62, word on
       p63) - a unique same-letter token on the start page takes the box. The
       rest land in "no usable token" (part of the 1,021 unreachable, `0GC`).
    3. MEDIUM `tools/build_witness_disputes.py` - `by_root` keeps the LAST entry
       per root; **5 roots have two entries** (`אלה`, `ארש`, `בכה`, `בלה`, `גרש`),
       so 5 entries are never compared and get no rows. The mirror in
       `corrected_positions()` compares both of a pair against one corrected text.
       Note `בכה`/`בלה` are the two headings `0GC` recorded as "gained".
    4. LOW `review_frontend/app.js` `saveWitnessDecision` - redraws with
       `renderKlalBody` regardless of the text-view toggle, so a save while on a
       non-master view flips that entry to Master under an unchanged selector.
    5. LOW `app.js` `witnessTierNote` - omits `same_letters`, so a `C_markup`
       note's counts do not sum to its total.
    6. LOW `tools/build_nli_page_pdf.py` - checks the NLI INDEX against the
       offset check but never the recorded `nli_file`, so a different glob or
       folder embeds a different photo while the check passes.
    **Reviewer report, same day (<http://127.0.0.1:8421/entry/18/word/8>,
    stored `רוה`):** (a) the popup said Sefaria's corrected reading was
    "(unchanged)" while showing `רוח` against their OCR `רוח,` - the corrector
    moved the comma, and `corrected_status()` compared letters only. A
    `punctuation_only` status now covers "same letters, different visible
    string" (12 of 245 reviewed rows). (b) The popup named the shoresh but not
    its number; the label is now "Shoresh אגפ (#18)". (c) Finding 5 below is
    fixed with (a): the tier note counts every status. (d) "Header says entry 17,
    index points to 17" did NOT reproduce: 10 attempts - 1100x800 to 1920x1080,
    cold load and hash change, long jumps from entries 120/200/300, header
    sampled at 0.3/0.7/1.5/3/6 s - all showed 18 in header, index and scan pane.
    **RESOLVED by the reviewer's next report:** "when i click on a word in a diff
    klal - the popup and scan jump there, but the index stays where it was and
    the scan header doesn't change." Every attempt above ARRIVED by link; the
    defect needs a CLICK. `focusWordOnScan()` (the funnel every word click goes
    through) moved the scan to the word's page and never told the index or the
    two headers, which read `_headerKlalId` - set only by `setActiveKlal()`, i.e.
    by the reading-line observer. Clicking a word in the klal below the reading
    line left all three naming the klal above. Pre-existing, both books.
    FIXED: `setActiveKlal()` split into `markActiveKlal()` (labels only) plus the
    start-page `showPage()`; `focusWordOnScan()` calls `markActiveKlal()` and
    records `lastActiveKlalId`, so the next scroll re-syncs to the reading line
    as the scan page already did. Not `setActiveKlal()`, whose start-page
    `showPage()` would undo the word's page (the `0CA` shape).
    `test_clicking_a_word_in_another_klal_makes_that_klal_the_active_one` failed
    on the defect first ('1' == '2'), passes now; it asserts the click scrolled
    nothing, so the observer cannot pass it by accident (Lesson 43). Siblings:
    the scan-box click and every list/deep link route through `focusWordOnScan`
    or `applyHashRoute`/`setActiveKlal`, and their tests pass.

    7. LOW `tools/verify_nli_page_offset.py` - the "ink" signal is not
       independent: `find_nli_page` searches offsets -45..-33 only, and now that
       `scan_pdf` names the full-tone PDF, a rerun compares the NLI crop with
       itself on 58-151.

0GC. **[2026-09-13, reviewer: "rebuild after confirming the offset"] THE NLI
    REBUILD HAS A BLOCKER 0FZ NEVER EXERCISED: NLI TOKENS ARE IN A DIFFERENT
    COORDINATE SPACE FROM EVERY IMAGE THE DASHBOARD AND THE VISION CROPS USE.**

    **The offset check is built:** `tools/verify_nli_page_offset.py`, two signals
    per page - Tesseract `heb` on the NLI image against the Google Books layer of
    pages p-3..p+3 (the neighbours are the negative control), and
    `find_nli_page`'s ink-profile search. Prototype on 58/75/92/400/640: right
    page 0.72-0.85, every neighbour 0.04-0.21, so -40 already holds at 400 and
    640. Trial: p59 is `TEXT_ONLY` - the ink search picked index 26, not 19 -
    which is `0FU`'s warning reproduced, and why ink is the second signal. Full
    sweep writing to `~/work/hashorashim/nli_page_offset_check.jsonl`.

    **The corpus pages are confirmed, on ONE signal.** Pages 58-151: 94 of 94
    have the right page best on text, smallest margin over any neighbour 0.311.
    The ink search agrees on 69 and picks a different image on 25, so this is
    the text signal alone - the fixed offset holding contiguously is what makes
    it acceptable, not a second independent agreement.

    **Option (a) chosen by the reviewer and in progress** (pages 58-151 only; the
    other 557 pages stay Google-sourced):
    * `experiment_scan_source.nli_text_crop()` is now the one crop; the three
      hand copies in `ocr_pages_docai/cloud_vision/vlm.py` call it. Pixel-identical
      to the old inline code on 35/35 pages, and equal to the image DocAI records
      having received (p58: DocAI `dimension` 1344x1917, crop 1344x1917; aspect
      error 0.00000 on all 35).
    * `tools/build_nli_page_pdf.py` (new) embeds that crop as the page, refusing
      any page not verified at the offset; writes `page_image_sources.json`.
    * `render_pdf_pages.py --verify` falls back, on a page with no text layer, to
      a box-on-ink contrast check. Calibrated on p58 with the crossed pairings as
      the negative control: same-source 5.34 / 6.90, crossed 1.10 / 0.86; bar 2.5.
    * DocAI on NLI pages 93-151 running (59 pages; 58-92 existed). Pre-rebuild
      tokens and page images kept as `docai_word_boxes_gb_bitonal/` and
      `images/pdf_pages_gb_bitonal/`, both gitignored.
    * `test_pipeline_logic.py` 470 passed after the refactor.

    **Rebuilt 2026-09-13.** Offset sweep over all 651 pages: 0 FAIL; -40 holds
    from p50 to p646. The INCONCLUSIVE pages (40-49, 601, 610, 647-651) are pages
    whose Google layer holds no Hebrew - every candidate scores 0 - not drift.
    DocAI read NLI pp93-151 with 0 failures. `book.json` `scan_pdf` ->
    `Sefer_hashorashim_nli_fulltone.pdf` (111 MB; 94 NLI pages, 557 Google);
    `scan_source` says which. `build_root_corpus.py` -> 314 entries; renders
    94/94 pass the box-on-ink check.

    Against the 100 reviewed entries (99 scorable, 13,619 words), the REAL build
    reproduces `0FZ`'s slice figures exactly:

        before   words 0.8956  chars 0.9576  nun/gimel 87
        after    words 0.9287  chars 0.9663  nun/gimel  6

    Witness queue 1,362 -> 826 anchored rows (disputes 2,793 -> 1,847); tier
    `A_nun_gimel` 203 -> 24, `A_ours_not_a_word` 463 -> 200. Word ids reseeded
    (43,821 words; the ledger is empty, so nothing pointed at the old ids).

    Keyed by ROOT (not klal id), 312 roots are common: 0 page changes in the
    corpus, 0 in the alignment; titles 210 identical, 46 spacing/punctuation, 56
    letters - the sampled letter changes are all OCR fixes (`הנימל`->`הגימל`,
    `הגון`->`הנון`, `היור`->`היוד`, `המס`->`המם`).

    **DATA ISSUE, two headings lost and two gained**, all four confirmed as real
    headings by `root_entries.json`:
    * LOST: `אמר` (p87, the line merge `0FZ` recorded) and `במ` (p116) - their
      text now sits inside the preceding entry. **RECOVERED 2026-09-14
      (`0GG`)**, with `בוצ` and `גרב`; the entry numbers in the URLs below are
      pre-`0GG` and have since shifted.
    * GAINED: `בכה` (p112) and `בלה` (p115), which the bitonal build had merged.

    **The alignment guard tests a proxy (Lesson 41).** `build_header_alignment.py`
    refused to write because 24 klalim "would change page" - klal 85 through 188,
    exactly the ids between the lost `אמר` and the gained `בכה`. Keyed by root
    there are 0 moves. The guard compares by `klal_id`, which aliases "this entry
    moved page" and "entries were renumbered". Not fixed.

    **My own defect, caught before it was used:** the first alignment comparison
    reported "0 moves" because it read `page` from rows whose field is
    `matched_page` - `None` vs `None` - Lesson 21, FLAT COORDINATE KEYS. The
    first title/page comparisons also zipped entries by POSITION across the
    renumbering; both redone keyed by root, which is where the figures above
    come from.

    **Verified end to end through the live :8421 server:** 314 klalim, 826 open;
    the seven witness boxes `/api/page/58` serves were drawn on the image the
    server serves (1344x1917, the crop) and every one sits on its word.

    **The two lost headings, where their text sits now** (data issue):
    * `אמר` - <http://127.0.0.1:8421/klal/84/word/126>, stored `והריש`, inside
      `אמצ`: "...בספר והמם ההמם **והריש** והורים , . אמר..." (heading line
      interleaved with the line below it).
    * `במ` - <http://127.0.0.1:8421/klal/190/word/209>, stored `הבית`, inside
      `בלת`: "...הבמות לא **הבית** סרו 24 והמם . על ויקרא..." (same shape).
    The cross-check against `root_entries.json` covers every heading on 58-151
    and finds exactly these two, so it is the sweep for this class.
    **`suspect_merge` (klalim 84, 189, 190) is read by nothing** in `pipeline/`
    or `review_frontend/` - the only field pointing at these is shown to no one
    (Lesson 29 THE FIELD NOBODY RENDERS). Not fixed. (2026-09-14: no entry
    carries it after `0GG` - but it is still rendered nowhere, so the next merge
    would be exactly as silent.)

    **A regression my rebuild caused, and fixed.** The rebuilt queue served
    `witness_accuracy: None`, and the panel's fallback (`app.js:3693`) then told
    the reviewer the 99.2% Sefaria witness "was measured correct in 16 of 419
    such cases (3.8%), so it is shown for context, not as a competing reading".
    The committed queue files carried 0.992 per row, but `git log -S` shows the
    builder NEVER wrote it per row - it wrote only the top-level
    `witness_word_accuracy`, which nothing that renders reads. So the value came
    from a step outside the builder, and any rebuild would lose it.
    `build_witness_review_queue.py` now writes it per row; served value 0.992 on
    every row sampled. No test covers the builder, `verify_nli_page_offset.py`
    or `build_nli_page_pdf.py`.

    **2026-09-13, reviewer requests, built.** (i) "don't call them klalim": a
    `ui` block in book.json (`cio.ui_vocabulary()`, defaults Klal) - HaShorashim
    now reads "שורש אב" / "Shorash #1" in the headers, block heads, panels and
    page title; Yad Malachi is unchanged. (ii) "once corrections are applied, why
    would that change what is seen under docai ocr reading?": it would have -
    `docai_reading` WAS the master word. `tools/snapshot_ocr_baseline.py` (new)
    froze `ocr_baseline_part1.json` (314 entries, 43,821 words, each with its
    word id; refuses once any apply_event exists) and the queue reads our OCR
    from it through the stable id. (iii) Sefaria's corrected reading is on every
    row in an entry they reviewed (97 entries). (iv) A text-pane toggle: Master /
    Our OCR / Sefaria OCR / Sefaria corrected, via `/api/klal/<id>/versions`;
    the three non-master views are read-only, and their inserted citations are
    marked, not merged (reviewer's choice: separate markup).

    **The tier note was false, and the tier behind it was a fallback.**
    `tier_for()` returned `C_both_attested` for every row whose OUR word was in
    the lexicon, whatever theirs was (`טתאוה` is not in it). Split by what the
    disagreement is, measured against the corrected text on reviewed entries:

        tier                  rows reviewed theirs ours neither
        A_nun_gimel             24     5      3     2     0
        A_ours_not_a_word      186    53     47     4     2
        B_ours_unattested       55    11      4     7     0
        C_both_attested        175    48     40     7     1
        C_footnote_numeral      25     6      6     0     0
        C_markup                 2     0      -     -     -
        C_spelling_vav_yod     285   103    101     1     1
        C_theirs_unattested     43     8      1     7     0
        one_side_empty          31    11     11     0     0

    **CAUTION on `C_spelling_vav_yod`'s 101/103:** their verse quotations are a
    pointed Tanakh's text, and the corrector left most of them alone, so their
    OCR and their corrected text agree there by construction - it is not
    evidence about this page (e.g. klal 1 w20 `עודנו`/`עדנו`, Job 8:12). And
    the old notes' "51 of 51" / "198 of 198" are gone: on the full-tone build
    nun/gimel is 3/5 and ours-not-a-word 47/53.

    **CORRECTION, same day - "unchanged" is not agreement (reviewer: "I suspect
    those are words they did *not* correct").** The table above counted a row as
    "theirs" whenever Sefaria's corrected text equals their OCR there. But a word
    their corrector never touched reads the same in both layers whether or not
    anyone checked it - it cannot disagree (Lesson 25). Split by what the
    corrector actually DID, on the 245 reviewed rows:

        left their OCR unchanged        213   no evidence either way
        changed it TO OUR reading        28
        changed it to something else      4

    **Where they changed a disputed word, it was to our reading 28 times in 32.**
    Every "theirs" figure above - and the auto-adopt argument built on them - was
    counting untouched words. The queue now carries `corrected_status` per row,
    the popup labels the corrected reading "(unchanged)" / "(changed - to our
    reading)", and the tier note counts only changes.

    **UI vocabulary, re-checked in pixels:** a rendered-DOM sweep of :8421 (text
    nodes, title/placeholder/aria attributes, document.title; index, headers,
    hover card, witness/flag/heading panels, settings) finds 0 strings with
    klal/כלל; the same sweep on :8420 finds 876, so it can see them. The unit is
    now spelled "Shoresh" (it was "Shorash", which is wrong). Still "klal": the
    share URL (`/klal/<n>/word/<m>`, `#klal=`) and every internal identifier
    (`klal_id` in the ledger, the API, the code) - a neutral name is a decision
    put to the reviewer, not made here.

    **DATA ISSUE CLASS: FOOTNOTE MARKERS READ INTO OUR WORDS** (reviewer found
    one: <http://127.0.0.1:8421/entry/1/word/37>, stored `אַבְּן` - the page
    prints `אַבִּ` with a superscript 3, and DocAI read the 3 as a final nun).
    Swept: 135 of the 1,847 disputes have the shape "ours = theirs + 1-2 trailing
    characters" (tails י 52, ל 25, ס 10, ן 9, ג 9, ו 7, ד 6, ם 5). 73 are in the
    dashboard queue; **62 are not reachable in the dashboard at all** (see the
    next paragraph). All 73 queue rows were cropped from the full-tone page
    images and read BY EYE: about 59 show a superscript marker right after the
    word - a numeral (3, 4, 5, 7, 9, 15, 16, 17, 19, 31) or a small raised mark
    that is not a digit and that DocAI mostly reads as `ל`/`ס`; about 11 are
    genuine readings with no marker (`החרבן`, `בחסרונו`, `הנערה`, `גויי`,
    `שמספיק`, `כולהו`, `בכורתי`, `בעבועי`, `בערבי`, `אפ[ילו]`) and one is a
    geresh read as yod (`נאי`); ~3 unclear. The old `footnote_numeral` rule saw
    only a trailing yod/vav/quote and ALSO misfired on `כולהו`, which the page
    prints. Code: a `C_footnote_marker` tier now covers the whole shape, with a
    note that says it is a triage label checked by eye, not a verdict; the
    footnote-numbering-gap signal was tried and is NOT used - its first form
    counted 11,804 "missing" numerals, and restricted to small gaps it flags 23
    of the 73 and misses most of the markers. The data fix is the reviewer's:
    each row needs a ruling, and the marker itself belongs in the text as
    demarcated footnote structure (`0CY`/`0DB` class), not deleted.

    **A false line of mine, fixed:** the popup said "Master text now reads
    `אבן`" on w37 when nothing had been applied - `master_reading` came from the
    disputes file, which stores spans with points deleted, and our OCR keeps
    them (`אַבְּן`). It now comes from part1.json's own words; 0 rows differ.

    **1,021 OF 1,847 SEFARIA DISPUTES ARE NOT IN THE DASHBOARD.** The queue can
    anchor a dispute only to a page token that matches our word exactly once:
    329 fail because the word repeats on its page, 643 because no letter-bearing
    token matches (a footnote marker glued into the word is one cause). They are
    in `witness_disputes.json` and reachable by no route - Lesson 26, THE FILTER
    THAT HIDES. Not fixed; the anchor could use the word index plus the
    alignment, which every row already carries.

    **Share links are book-neutral:** `/entry/<n>/word/<m>` and `#entry=`, with
    `/klal/` and `#klal=` resolving permanently (START_HERE's reporting rule
    updated). Internal identifiers stay `klal_id`/`klalId` - 7,635 occurrences in
    code and tests, `klal_id` stored in 4,846 ledger rows and every API payload;
    a rename is put to the reviewer as its own decision.

    **Auto-adopt (reviewer chose "our OCR, auto-adopt evidence") is NOT done.**
    No tier above is clean enough to adopt on one signal: ours-not-a-word would
    import ~6 wrong words per 57. The next step is a second, independent signal -
    the vision adjudicator on the FULL-TONE crops (`0FS`: 90% vs 18% on
    nun/gimel) - measured on these reviewed rows before any rule is proposed.
    Also: no code can apply a `witness_choice`; adoption needs that path.

    **Still to do:** the corpus root's README "How to rebuild" does not yet list
    the NLI steps or `--witness-accuracy`; `candidates_part1.json`,
    `candidates_verified_part1.json`, `lexical_vision_report.json` and the gold
    dispute files there predate the rebuild (none is read by the server). Nothing
    is committed in either repo.

    **The blocker.** Same word, same page, two token sets:

        docai_word_boxes/page_58.json  'המאמר'  y1 0.2180   (Google PDF page)
        nli_docai_layer/page_58.json   'המאמר'  y1 0.0193   (NLI photo, cropped)

    `tools/ocr_pages_docai.py:141-145` crops each NLI image to its ink box before
    sending it, so the returned boxes are normalised to that crop. But the scan
    pane serves `images/pdf_pages/` rendered from `book.json`'s `scan_pdf`
    (`review_server.py:72`), and the vision crops open the PDF
    (`verify_corrections_vision.py:306`, `verify_flagged_candidates_vision.py:569`).
    A corpus rebuilt from NLI tokens would put every word box and every vision
    crop in the wrong place. `0FZ` measured text only, so it could not see this.
    Options, the reviewer's call: (a) make the NLI crop the book's page image -
    render `images/pdf_pages/` and the vision crops from it, which also gives the
    reviewer and the adjudicator the full-tone scan `0FS` measured at 90% vs 18%
    on nun/gimel; (b) register NLI coordinates onto the PDF page per page.

    **Scope.** The corpus spans PDF pages 58-150 (314 entries, א-ב-ג). `0FZ`'s
    "651 pages" is the whole dictionary, which the corpus does not cover yet.

    **Tier A (`0FX`) should wait for the rebuild:** 203 of its 666 rows are
    nun/gimel, the class full tone cuts 85 -> 6, and no code can apply a
    `witness_choice` to the corpus (`0EA`, still true - the applier promotes
    `candidate_choice`, `manual_correction`, `title_correction`).

    **Correction to the TL;DR and to my own status report today:** `0BX` does not
    need a policy decision. It was decided 2026-09-08 ("refuse and report", see
    `0DM`) and implemented in `a03c313`.

0GB. **[2026-09-13] STATUS SWEEP: THE TL;DR IS A WEEK STALE, AND THE AUDIO
    WORKTREE HOLDS TWO UNCOMMITTED LEDGER ROWS.**

    * **The TL;DR's "What is open, 2026-09-06" block and its "Eight items are
      live" claim are stale.** The Open items section now holds item bodies from
      `0BZ` through `0GA` plus `0BO` — dozens, not eight — and the whole of the
      HaShorashim work (`0EC`-`0GA`) is absent from the TL;DR. Not rewritten here;
      the TL;DR needs a deliberate pass, not a patch.
    * **Live counts, Yad Malachi :8420, measured 2026-09-13 from `/api/klalim`:**
      222 klalim, all `page_trusted`; `open_count` 619, `decided_count` 185,
      `machine_resolved_count` 176, `machine_disputed_count` 443; 88 klalim
      `needs_revisit`; punctuation 66 open / 1 decided; `title_pending` 0. Ledger
      4,846 lines. Tests: 658 collected.
    * **HaShorashim :8421:** 314 entries, 1,362 open, 0 decided, ledger empty — so
      `0FZ`'s "queue is disposable" condition still holds.
    * **`0GA`'s two stale servers (ports 64210, 65163) are no longer running.**
    * **`../sefer-digitization-pipeline-audio`** (`feature/audio-transcript-review`,
      9 commits ahead of `master`, last commit 2026-08-29) has uncommitted edits:
      two appended `review_decisions.jsonl` rows, both `decision_type:
      audio_transcript_edit` with `klal_id: 0` (not corpus rulings), and a
      21,588-line diff to `transcript/rav_kook_lecture.json`. If that branch is
      ever merged, those rows enter Yad Malachi's ledger under a klal id that does
      not exist. Needs the reviewer's call: commit, discard, or give the audio
      feature its own ledger (as `0GA` did for HaShorashim).

      **Checked 2026-09-13: the rows cannot corrupt corpus data.** The branch
      adds `audio_transcript_edit` to `VALID_DECISION_TYPES`, so the gated
      type invariant would pass after a merge. Of the ten tools that read every
      ledger row unfiltered, nine filter by `decision_type` or by klal
      membership before using a row, and `backfill_word_ids.py:131-133` refuses a
      ruling whose klal is not in `part1.json`. HaShorashim cannot see them at
      all - its ledger is `~/work/hashorashim/review_decisions.jsonl`. The real
      costs of a merge are elsewhere: the branch forked at `b7f2025`
      (2026-08-27), so its +413-line `review_server.py` and +771-line `app.js`
      conflict with two weeks of master; the append-only ledger conflicts at
      its tail, where a careless resolution drops rows; and it commits an 18 MB
      lecture recording (`audio/a-detailed-overview-of-rav-kook-...mp3`) and its
      transcript into a PUBLIC repo. Not pushed anywhere as of today.

0FB. **[2026-09-10] OUR TEXT vs SEFARIA'S *MANUALLY CORRECTED* TEXT, PUT TO THE
    INK: 56/44 ON 34 REAL READING DIFFERENCES. TOO CLOSE AND TOO SMALL TO CLAIM
    ANYTHING.**

    Item `0EZ` measured our text against their corrected entries and could not
    assume gold was right - their pass may normalise orthography rather than
    correct it (`עדנו` for our `עודנו`). So the disagreements were cropped and
    put to the vision adjudicator, using the same `--source witness` route with
    their corrected text as the witness. 42 disputes, all adjudicated.

        real reading difference                    37   A 19 / B 15 / UNCERTAIN 3
        heading markup (their span splits the ה)    3   A  3
        word division / &nbsp; only                 2   A  2

        ON THE 34 DECIDABLE READING DIFFERENCES
           ink backs OUR reading         19   56%
           ink backs THEIR correction    15   44%

    ### The number moved twice and the classification is why

    The interim read on 30 unclassified rows said **66.7% for us**. Five of those
    "wins" were not readings at all - `הבית` against their `בי'ת`, which is their
    HTML splitting the `ה` into a span, and two `&nbsp;` word-division artifacts.
    Removing what was never a reading disagreement takes it to **56%**. That is
    the third figure today that changed materially once someone looked at what
    was inside it (`0EZ`'s 76% -> 88.5% -> 98.4%, `0ET`'s 36% -> 25.7%).

    **Do not report 56% as a result either.** n=34, one adjudicator, and this
    project's own record (`0EA`, `0EB`) is that vision is a signal and not a
    verdict. The defensible statement is that at the point where the two texts
    disagree on a reading, the scan supports each side about equally - which is
    itself informative, because one side is raw OCR and the other is a human's
    deliberate correction.

    ### Why that is worth telling the Sefaria editor, carefully

    If it holds at larger n, **some of his manual corrections are not
    improvements** - 19 of 34 places where he changed the text away from what the
    page appears to show. At 657 entries reviewed and 1,368 to go, that is worth
    knowing before more hours go in. It is also exactly the claim that needs the
    most evidence before it is made, which is the argument for asking for 100
    corrected entries rather than 10 (draft sent for the reviewer's approval).

    Examples where the ink backs us: `ונוש` against their `וגוש`, `ויעשה` against
    `ויעשו`. Where it backs them: `ועגינה` -> `וענינה`, `מתלעותיופי` ->
    `מתלעתיו`.

0FA. **[2026-09-10] QUESTION 2 ANSWERED: THE MERGE IS RELIABLE. 98.8% OF
    SEFARIA'S 20,450 FOOTNOTE ANCHORS TRANSFER ONTO OUR TOKENS WITHIN ONE WORD.**

    The Sefaria editor's second question - is there a reliable way to merge the two datasets,
    taking the citations from theirs and the text from ours. Measured rather than
    estimated.

    Their apparatus is not prose: `word/footnotes.xml` holds 20,450 footnote
    bodies and `document.xml` holds 20,450 `footnoteReference` markers, so every
    note is ANCHORED to a token position in their text (item `0EY`). The merge is
    therefore a word-level alignment problem, and
    `tools/build_witness_disputes.py` already computes exactly that alignment to
    find disagreements - the anchors can ride on it.

    Extracted all 20,450 anchor positions and placed them onto our token stream
    for א-ב-ג (3,159 anchors, 306 shared entries):

        nearest aligned token, exact              2,046   64.8%
        within +/- 1 word                         3,122   98.8%
        within +/- 2 words                        3,151   99.7%
        within +/- 3 words                        3,157   99.9%
        unplaceable                                   2    0.1%

    **A footnote's position tolerates a word; a citation attaches after a phrase,
    not between two letters.** So the operative number is 98.8%, and the two
    unplaceable anchors are in `בכה` and `בלג`.

    ### Why exact matching fails, which is the elegant part

    Of the 1,113 anchors whose immediately-preceding token does not align:

        genuinely different reading                       841   75.6%
        ours = theirs + a numeral read as letters         264   23.7%
        no nearby anchor                                    8    0.7%

    with examples `הנחל`->`הנחלי`, `שריד`->`שרידי`, `ועוגב`->`ועוגבי`. **Nearly a
    quarter of the exact-match failures are the footnote numeral itself** - the
    anchor attaches to precisely the token our OCR corrupted, because the thing
    that corrupted it IS the footnote marker. The neighbour aligns, which is why a
    one-word window recovers almost all of them.

    ### What this means practically

    The two datasets can be merged without a human adjudicating placement. What a
    human is still needed for is the 24% of running-text tokens where the two
    disagree, which is a different question and the one item `0EZ` is measuring.

    **Not built.** The measurement is a script, not a tool; turning it into a
    merge would mean writing the anchors into our corpus as structure. That
    should wait for a decision about whose text is the base - and on the evidence
    of `0EZ` (their raw reads 99.1% against our 98.4%), that decision is not
    obviously ours.

0EZ. **[2026-09-10, Sefaria] GROUND TRUTH AT LAST - AND OUR RAW READ IS WORSE
    THAN THEIRS. 98.4% AGAINST 99.1% ON CHARACTERS.**

    The Sefaria editor's position: the dictionary is fully parsed, the
    verses were carefully identified, **the running-text OCR is weak**,
    and rather than abort or ship as-is he is correcting it by hand - 657 of
    2,025 entries done. His two questions decide the project:

    1. Can the model produce a high-fidelity read that saves most of the
       human review?
    2. Is there a reliable way to merge the two datasets, keeping the
       citations from theirs and the running text from ours?

    He sent 10 manually corrected entries (verified against the source PDF) and
    10 raw ones. **The corrected sample is the first ground truth this project
    has ever had for this book.**

    ### Question 1, measured. It does not currently favour us.

    Five of the ten corrected entries fall inside the א-ב-ג slice. Character
    accuracy against gold, word division ignored, 7,878 gold characters:

        OURS (raw DocAI, no correction pass)   98.4%
        THEIR RAW (described as weak)          99.1%

    **Their existing data is better than our extraction**, and the honest reading
    of that description is that he is holding it to a high bar, not that it is bad. Their
    manual pass moves 99.1% -> 100%, i.e. it is worth about 0.9% of characters.

    ### TWO NUMBERS I ALMOST REPORTED THAT WERE WRONG

    First pass gave **ours 76.0%, theirs 79.1%** on tokens. Both meaningless:
    their corrected `html` renders resolved citations as inline text
    (`<a class="refLink">שה"ש ו יא</a>`), so our text was being penalised for
    lacking citations that live in the apparatus we correctly exclude. Stripping
    refLinks: ours 88.5%, theirs 92.8%.

    Still wrong. Those token figures are dominated by WORD DIVISION - their HTML
    splits the heading as `ה` + `אל'ף`, ours has `האלף`; `שמתרגם` against
    `שמ תרגם`. On characters, which word division cannot touch, the same texts
    are 98.4% and 99.1%. **A 10-point token gap was a 0.7-point character gap.**
    Two corrections in one measurement, both caught by diffing a single entry by
    hand rather than trusting the aggregate (Lesson 33 STATE, NOT PRINTOUT).

    ### What is NOT yet established, and it matters for the answer

    **Whether gold is right where we differ.** Their corrected text may normalise
    orthography - gold `עדנו` against our `עודנו`, gold `הרמנים` against our
    `הרמונים` - and this project's own rule is that the ink decides, not the
    transcription. A pass is running now that puts our reading and theirs to the
    vision adjudicator on the crop. If a material share of the 1.6% turns out to
    be their normalisation rather than our error, the gap narrows.

    **Sample size: 5 entries, 7,878 characters, 3 of them aleph.** This is an
    indication, not a rate. He has 657 corrected entries; getting even 100 of
    them would settle question 1 properly, and asking for them is cheap.

    ### The honest framing for question 1

    Our raw extraction is not better than what he already has. The pipeline's
    claim was never the extraction - it is the adjudication layer, which has not
    been run on this book beyond 120 sample disputes. So the answerable version
    of his question is: **does the review pipeline close a 1.6% character gap
    cheaper than a human reading 2,025 entries?** That is measurable and is not
    yet measured.

0GA. **[2026-09-13] HANDOFF - STATE OF SEFER HaShorashim AT THE END OF THE
    LONG SESSION. READ THIS FIRST.**

    **Dashboards.** Yad Malachi on :8420, Sefer HaShorashim on :8421
    (`SEFER_CORPUS_ROOT=~/work/hashorashim python3 pipeline/review_server.py
    --port 8421`). Two stale Yad Malachi servers from 2026-09-06 were seen on
    ephemeral ports (64210, 65163) running old code; not started by this work.

    **Fixed 2026-09-11/13, all found by looking at the running dashboard:**
    * Each book now has its OWN decision ledger (`review_decisions.py` used the
      code folder; HaShorashim was reading and would have written Yad Malachi's
      4,846-line ledger). Nothing leaked. HaShorashim's ledger is
      `~/work/hashorashim/review_decisions.jsonl` and is empty.
    * Witness context bracket indexed raw tokens; now letter-bearing tokens.
    * Witness `word_index` was an index into a filtered list; now a position
      in `clean_text.split(' ')`. Before: 1,357 of 1,362 rows put the text-pane
      highlight on the wrong word. After: 1,362 right. Regression test
      `test_a_witness_dispute_word_index_is_a_position_in_clean_text_split`.
    * Per-tier panel text instead of one sentence that contradicted tier A.

    **Files that lived only in `/tmp` and were LOST** when it was cleared:
    `ibnj_entries.json`, `ibnj_gold100.json`, `ibnj_anchored.json`,
    `ng_located.json`, `correction_ledger.json`. The two that matter are now
    persisted in the corpus root and the tools' usage lines point at them:
    * `witness_entries.json` / `witness_entries_flat.json` - Sefaria's
      unreviewed text per entry, recovered from `witness_footnotes.json`
      (which stores each entry's tokens verbatim).
    * `gold100_text.json` - the 100 reviewed entries, citation-free, rebuilt by
      `tools/anchors_from_inline_citations.py --text-out`.
    Recovered disputes differ trivially from the lost-file build (2,795 vs
    2,793 rows; 310 vs 306 shared entries), because the corpus has since gained
    the 0FI headings.

    **Document AI.** Processor `bc652834c231f24e`, Document OCR, region `eu`,
    project `gen-lang-client-0289907848`; service account `doc-ai-worker` holds
    `roles/documentai.apiUser` (processes; cannot `get`/`list` - expected). The
    corpus was built by an older processor `4d3d4f204562f1d6` in `us`, fed whole
    PDF pages. Run: `DOCAI_PROJECT=... DOCAI_LOCATION=eu DOCAI_PROCESSOR=...
    python3 tools/ocr_pages_docai.py --check`.

    **Repositories (2026-09-13).** This pipeline repo is PUBLIC
    (`esafern/sefer-digitization-pipeline`) and was pushed after rewriting the
    35 unpushed commits so that correspondents appear by ROLE only - "the
    Sefaria editor", "the NLI contact" - with their emails paraphrased, not
    quoted. **Keep it that way in every status item, commit message and
    docstring.** The pre-rewrite history survives LOCALLY ONLY, in branch
    `backup/pre-anonymize-2026-09-13` and in
    `~/sefer-pipeline-pre-anonymize-2026-09-13.bundle`: never `git push --all`,
    never push that branch. The corpus root now has a PRIVATE remote,
    `esafern/hashorashim`; it holds Sefaria's unreleased dataset and must never
    be made public.

    **The decision in front of the reviewer** (`0FZ`): rebuild the book from
    NLI's full-tone images through that processor. On the 35-page slice it wins
    on every measure (words 0.9287 vs 0.9002, nun/gimel 6 vs 85). Blockers
    left: spend (651 pages) and verifying the NLI<->PDF page offset (-40,
    checked on 58-92 only; NLI has 656 images to 651 pages) across the book,
    which costs nothing and should come first. The dashboard queue is
    disposable until the first ruling - so do not rule on HaShorashim rows
    until that decision is made.

0FZ. **[2026-09-11] DOCUMENT AI ON THE FULL-TONE SCAN BEATS EVERYTHING WE HAVE,
    ON EVERY MEASURE. AND 0FW'S "ENGINE MATTERS MORE THAN SCAN" WAS AN ARTIFACT.**

    Processor `bc652834c231f24e` (Document OCR, `eu`) was run over pages 58-92 on
    BOTH scans, and both outputs were put through the corpus's own pipeline
    (`build_root_corpus.py`, which removes running heads and apparatus by page
    geometry) in isolated scratch corpus roots. Scored with
    `tools/measure_against_reviewed.py` on the 99 reviewed entries present in
    every source, 13,619 words:

    | source | words | chars | coverage | precision | nun/gimel |
    |---|---|---|---|---|---|
    | corpus (original `us` processor, bitonal) | 0.8956 | 0.9576 | 0.9840 | 0.9256 | 87 |
    | new processor, bitonal | 0.9002 | 0.9610 | 0.9843 | 0.9340 | 85 |
    | **new processor, FULL TONE** | **0.9287** | **0.9663** | **0.9887** | **0.9353** | **6** |

    Holding processor AND pipeline fixed, full tone gains **+2.9 points of
    words** and cuts nun/gimel errors **85 -> 6 (-93%)**. Against the corpus as it
    stands: +3.3 words, 87 -> 6. The character gain is small (+0.5) because a
    nun/gimel error is one letter inside a word - it barely moves a character
    score and costs a whole word, so words is the metric that sees this class.

    **The control that makes this trustworthy.** Rebuilding the corpus from the
    ORIGINAL tokens in a scratch root over the same pages reproduced the real
    corpus to four decimal places on all 100 entries (0.8939 / 0.9561 / 88), and
    the real `book.json` was untouched. So the scratch-root builds are the same
    pipeline, not an approximation of it.

    **Why 0FW was wrong.** It compared the processed corpus (0.95) against RAW OCR
    text with a crude cleanup (~0.87) and called the 7-8 point gap "engine".
    Split into coverage and precision, every source reproduced 95-98% of the
    reviewed text; the gap was EXTRA text - apparatus whose citation numerals
    are Hebrew letters (`שם ה יא`), which a trailing-Arabic-digits rule cannot
    see. The new processor on the same bitonal scan, through the same pipeline,
    matches the original (0.9595 vs 0.9561 chars). The engine was never the
    difference; the pipeline was. Raw against raw, the scan effect is the larger.

    **Two things that bias AGAINST full tone, so the advantage is conservative:**
    * One heading (`אמר`, p87) was not recognised on the full-tone build, so its
      text merged into the preceding reviewed entry `אמץ`, inflating it. `אמר`
      itself drops out of the comparison (99 entries, not 100).
      The cause is a LINE MERGE, not a detector gap: on full-tone p87 the heading
      and the line below it came out as one line with their words interleaved
      (`ונשלם האלף בספר והמם ההמם והריש והורים , . אמר ...`). It is NOT skew -
      measured, p87's line angle is 0.000 deg. Skew does exist on the
      photographed full-tone pages (median |angle| 0.074 deg, worst p70 at
      0.83 deg, against 0.006 / 0.014 deg on the flat bitonal scan), but the one
      merge traced here is on a page with none, and merging is rare overall:
      1,156 body lines on full tone against 1,161 on bitonal over 35 pages, 22
      pages identical. **Deskew is therefore NOT indicated by this evidence** -
      recorded so it is not chased on the strength of one merged heading. The
      exact cause of the p87 merge is undetermined.
      **ANNOTATED 2026-09-14 (`0GG`): now determined** - DocAI boxed the
      printed second line up into the first (tops 0.6485 vs 0.6425, heights
      0.0345 vs 0.0230); not skew, as measured here. But p116's merge, outside
      these 35 pages, IS skew (slope -0.013). Grouping every line on a deskewed
      level was then tried and split six lines that had been right, so this
      paragraph's conclusion holds for OCR and for grouping alike; the fix is
      local to lines that are demonstrably two rows.
    * 70 apparatus lines were dropped under the label "watermark" - the NLI
      apparatus sits where the Google watermark sits on the other scan, and that
      rule is positional. They are apparatus and should go, so no body text was
      lost (full tone has the HIGHEST coverage), but the label is wrong and the
      rule is scan-specific.

    **Two defects of mine along the way.** The comparison script merged
    homographs (`אלה a` + `אלה b` under one key, 991 spurious words in one
    entry); `measure_against_reviewed.py` pairs occurrences in order. And the
    first DocAI pass saved `document.text` only, discarding the layout the
    pipeline needs, so the slice had to be processed twice: about 145 pages in
    all, roughly half of it that redo. The tool now saves text, tokens and the
    full Document on every run.

    **What this recommends, and what it does not do.** Rebuilding the book from
    NLI's full-tone images through this processor is the evidenced next step.
    It is NOT done, for three reasons that are the reviewer's to weigh:
    * spend - 651 pages, against 35 measured here;
    * the NLI<->PDF page mapping (offset -40) is content-verified over 58-92
      only, NLI has 656 images to the PDF's 651, and a drifting offset silently
      pairs text with the wrong page (`0FU` caught exactly that);
    * ~~a corpus rebuild changes the text under the dashboard's 1,362-row
      queue.~~ **LIFTED 2026-09-11 by the reviewer:** "going forward we can throw
      away the rows in the queue. no one has looked at them yet." The HaShorashim
      witness queue is DISPOSABLE - regenerate it after any rebuild, preserve
      nothing from it. This holds only while no ruling exists on this book; the
      first recorded decision ends it, and after that a rebuild needs the
      drift/repoint machinery like Yad Malachi does.

0FY. **[2026-09-11] DOCUMENT AI SETUP: THE API IS ALREADY ENABLED AND THE
    SERVICE ACCOUNT ALREADY EXISTS. WHAT IS MISSING IS A PROCESSOR AND ONE ROLE.
    REGION IS `eu`.**

    Probed rather than assumed. Listing processors as the existing service
    account fails with **`IAM_PERMISSION_DENIED`, not `SERVICE_DISABLED`** - so
    `documentai.googleapis.com` is enabled on `gen-lang-client-0289907848`. The
    credentials in `$GOOGLE_APPLICATION_CREDENTIALS` are a service account
    already named `doc-ai-worker@gen-lang-client-0289907848.iam.gserviceaccount.com`,
    and `gcloud` 578.0.0 is installed but authenticated AS that service account,
    which is why it cannot create anything.

    **The region is `eu`** (reviewer's choice, 2026-09-11): the work is done in
    Israel and the correspondents are Sefaria and the NLI.
    `tools/ocr_pages_docai.py` defaults to it. The endpoint is derived from the
    location, and a processor created in `eu` returns a bare PERMISSION error
    from the `us` endpoint rather than "not found" - which is also why the probe
    above could not rule out an existing processor: it asked `us`.

    Remaining steps, all needing the reviewer's own credentials:

        gcloud auth login
        gcloud config set project gen-lang-client-0289907848
        curl -X POST \
          -H "Authorization: Bearer $(gcloud auth print-access-token)" \
          -H "Content-Type: application/json" \
          -d '{"type": "OCR_PROCESSOR", "displayName": "shorashim-ocr"}' \
          "https://eu-documentai.googleapis.com/v1/projects/gen-lang-client-0289907848/locations/eu/processors"
        gcloud projects add-iam-policy-binding gen-lang-client-0289907848 \
            --member="serviceAccount:doc-ai-worker@gen-lang-client-0289907848.iam.gserviceaccount.com" \
            --role="roles/documentai.apiUser"

    **CORRECTED 2026-09-11: there is no `gcloud documentai` command group.** The
    first version of these steps said `gcloud documentai processors create`;
    checked against gcloud 584.0.0 it is `Invalid choice: 'documentai'` in GA,
    and the alpha component is not installed. Processor creation goes through
    the REST API (above) or the console. The IAM step is an ordinary GA command
    and was right. The `print-access-token` must be taken AFTER logging in as a
    human account - taken as the service account, the create is denied.

    The processor's returned `name` uses the project NUMBER, not the id
    (`projects/<NUMBER>/locations/eu/processors/<ID>`). gcloud's configured
    project was `1045375753125`; if that is the number shown, it is the same
    project and that open question is closed.

    `roles/documentai.apiUser` grants processing but NOT `processors.list`, which
    is fine: the tool addresses the processor by id. Then
    `DOCAI_PROJECT` / `DOCAI_LOCATION=eu` / `DOCAI_PROCESSOR`, and
    `python3 tools/ocr_pages_docai.py --check` proves the config before a run
    spends anything.

    Scope the spend by running the 35-page slice first, not the 651-page book:
    the slice is what decides whether a rebuild is worth it, and it is the
    cheapest item on the list. Pricing not quoted here - I could not retrieve a
    current figure I would stand behind, so read
    <https://cloud.google.com/document-ai/pricing> rather than a number from me.

    `OCR_PROCESSOR` (standard Document OCR) is the type to start with, because it
    is what produced the 0.9499-character baseline in `0FW` that this run is
    trying to beat. Enterprise Document OCR is a separate, dearer type and
    changing two things at once would repeat `0FU`'s mistake.

0FX. **[2026-09-11] THE WITNESS QUEUE DOES NOT NEED FILTERING. IT IS 98.6%
    REAL CORPUS ERRORS. IT NEEDS ORDERING, AND NOW HAS IT.**

    Before shipping a ranking, it was labelled: of the 1,362 queue rows, 435 fall
    inside the 100 manually reviewed entries, where the truth is known. At 429 of
    those 435 - **98.6%** - our corpus is wrong.

    That is not a surprise once stated: the witness reads 99.2% of words
    correctly and we read 95%, so a position where the two disagree is
    overwhelmingly a position where we are wrong. It does mean the instinct from
    `0DV` ("563 permanent flags on unread material") does not apply here. That
    queue was full of noise; this one is not.

    | rule | rows | ours wrong | precision |
    |---|---|---|---|
    | all rows | 435 | 429 | **98.6%** |
    | our word not in the lexicon | 219 | 218 | 99.5% |
    | ours not a word AND theirs is | 198 | 198 | **100.0%** |
    | nun/gimel single letter | 51 | 51 | **100.0%** |

    So tiers are for taking the unambiguous ones first, not for hiding anything -
    every row is still served. `tools/build_witness_review_queue.py` now labels
    each row, and the whole 1,362 break down as:

    | tier | rows |
    |---|---|
    | `A_nun_gimel` | 203 |
    | `A_ours_not_a_word` | 463 |
    | `B_ours_unattested` | 70 |
    | `C_both_attested` | 583 |
    | `one_side_empty` | 43 |

    666 rows are tier A, and tier A measured 100% ours-wrong on the labelled
    sample. **That is the case for applying tier A mechanically rather than
    asking a human to click 666 times** - but applying corpus changes runs
    through the decisions/apply pipeline and is a reviewer's call, so it is
    stated here and not done.

    Verified live on :8421 across klalim 1-59: 193 witness rows served, tiers
    present, `witness_name` and `witness_accuracy` reaching the client. 656
    passed, 1 skipped.

    A note on my own verification: the first check of this reported ZERO rows and
    I nearly recorded a regression. The API returns them under `queue`; my script
    read `corrections`. The server was correct the whole time.

0FW. **[2026-09-11] CONTROLLED AT LAST: SAME ENGINE, TWO SCANS. FULL TONE WINS
    ON BOTH AXES - AND THE ENGINE MATTERS MORE THAN THE SCAN FOR RUNNING TEXT.**

    `0FU` could not separate scan from engine because both changed at once. Cloud
    Vision needs no processor to be provisioned and can be pointed at either
    scan, so it supplies the missing control: same engine, same 35 pages, same
    segmentation, same ground truth, only the pixels differ.

    | source | word | chars | nun/gimel errors |
    |---|---|---|---|
    | Cloud Vision on BITONAL | 0.7908 | 0.8588 | 39 |
    | Cloud Vision on FULL TONE | **0.8208** | **0.8788** | **8** |
    | DocAI on BITONAL (what the corpus is) | 0.8879 | 0.9499 | 72 |

    11,705 words of ground truth over 81 entries present in all three.

    **The scan result, now controlled**: holding the engine fixed, full tone
    gains +3.0 points of words and +2.0 of characters, and cuts nun/gimel errors
    by 79% (39 -> 8). So the full-tone scan is better on running text too, not
    only on the one class it was chosen to test. That is the clean version of
    `0FS` and it survives.

    **The engine result, which is larger and cuts the other way**: DocAI on the
    WORSE scan still beats Cloud Vision on the BETTER one by 7 points of
    characters. For this material the engine is worth more than the pixels.

    > **CONFOUNDED - see `0FZ` (2026-09-11).** The 7 points compared the
    > PROCESSED corpus (`build_root_corpus.py`: running heads and apparatus
    > removed by page geometry) against RAW Cloud Vision text with only a crude
    > first-line/trailing-digits cleanup. Split into coverage and precision, all
    > five sources reproduce 95-98% of the reviewed text; the gap is EXTRA text
    > in the raw layers (precision 0.67-0.77 against the corpus's 0.87). A fresh
    > DocAI processor on the same bitonal scan scores 0.8704 raw - one point over
    > Cloud Vision, not seven. Raw against raw, the scan effect (~2 points) is
    > larger than the engine effect (~1). Do not cite the 7-point figure.

    So neither of the two things we can run today is the right combination. The
    experiment that matters is the one we cannot run: **DocAI on the full-tone
    images**, which should carry DocAI's running-text quality and the full-tone
    scan's nun/gimel fix at once. It is blocked on nothing technical - the
    service-account credentials work and `google-cloud-documentai` is installed -
    only on a Document AI processor being provisioned in the project, which is a
    console and billing decision and therefore the reviewer's.

    Expected value if it lands, extrapolating from the two controlled deltas:
    DocAI's 0.9499 characters plus roughly the scan's nun/gimel reduction, i.e.
    the corpus's largest error class mostly gone without giving up read quality.
    That is worth a rebuild of the slice to verify before any rebuild of the book.

0FV. **[2026-09-11] SEFER HaShorashim IS UP IN THE DASHBOARD ON :8421, WITH
    1,362 REAL ROWS. YAD MALACHI IS UNCHANGED ON :8420.**

    Both blockers from `0FT` are fixed, each in the smallest way that keeps the
    other book's behaviour provably identical.

    **The cut is now per-witness.** `review_data.load_witness_queue` returns the
    queue whole when the file carries NO vision verdicts, and otherwise behaves
    exactly as before. Yad Malachi's file HAS verdicts, so its filter path is
    untouched by construction - measured before and after, it serves the same 44
    rows. HaShorashim went from 0 to 1,362.

    **The witness has a name.** `review_frontend/app.js` gained `witnessLabel()`
    and `witnessReliabilityNote()`, both defaulting to the historical Tesseract
    text when a row carries no `witness_name`, and the five hardcoded sites now
    read through them. `review_server.py` passes `witness_name` and
    `witness_accuracy` through on both the overlay and the standalone entry.
    Verified live: Yad Malachi's witness rows carry `witness_name=None` and still
    render "Tesseract"; HaShorashim's carry "Sefaria (Ibn Janah digitization)"
    and 0.992, so the panel now states that witness's own measured accuracy
    instead of Tesseract's 3.8%.

    `review_queue_part1.json` was created EMPTY (`{}`) for this book, which the
    server requires to exist. Empty is the honest value: the machine-candidate
    diff is DocAI against a corpus built from DocAI (item `0ER`).

    Live check, both servers running at once:

    | | :8420 Yad Malachi | :8421 HaShorashim |
    |---|---|---|
    | HTTP | 200 | 200 |
    | klalim listed | 222 | 314 |
    | witness rows served | 44 (unchanged) | 1,362 |

    54 of the first 59 HaShorashim klalim carry witness rows. Klal 1's first is
    `הנחלי` (ours) against `הנחל` (Sefaria) on p58 - the position the verse check
    already settled for Sefaria at <https://www.sefaria.org/Song_of_Songs.6.11>.

    Full suite green (656 passed, 1 skipped) before the restart.

    **What the reviewer should know before working this queue.** It is NOT
    ranked. 1,362 rows is far too many to work through, and item `0DV`'s "563
    permanent flags on unread material" is the warning. The ranking signal that
    exists and is measured is in `0FL`: our-reading-disagrees plus his-word-not-
    in-lexicon cuts 1,054 flags to 195 while still catching half his corrections,
    and adding "and ours IS a word" gets 57.5% precision on 40 rows. Wiring that
    as a tier is the obvious next step and is not done.

0FU. **[2026-09-11] RE-READ THE SLICE FROM THE FULL-TONE SCAN: NUN/GIMEL DROPS
    83 -> 16, BUT THE VLM LOSES MORE ON RUNNING TEXT THAN THE SCAN GAINS.**

    `tools/ocr_pages_vlm.py` transcribed all 35 pages of the reviewed slice from
    NLI's full-tone images, un-thresholded, and the result was segmented into 91
    entries and scored against the same 100 reviewed entries used throughout.

    | source | word | chars | nun/gimel errors |
    |---|---|---|---|
    | DocAI on the bitonal scan | 0.8953 | **0.9573** | **83** |
    | Gemini VLM on the full-tone scan | 0.7870 | 0.8486 | **16** |

    **Two changes were made at once and they must be attributed separately.**

    The nun/gimel collapse - 83 errors down to 16, an 81% reduction - belongs to
    the SCAN, and that attribution is clean because `0FS` ran the controlled
    version: same engine, same prompt, same words, only the pixels changed, 18%
    -> 90%.

    The overall loss belongs to the ENGINE, and it is not truncation. On the 62
    entries the VLM transcribed completely (9,207 words) it scores 0.9127 against
    DocAI's 0.9704, so it is worse at running text across the board, not just
    dropping tails. This is the "stochastic generation risk" the reviewer's own
    engine matrix names for generative extraction, measured: a VLM asked to read
    a whole page paraphrases and drifts in a way a dedicated OCR engine does not.

    **So the next step is not more VLM.** It is a real OCR engine on the
    full-tone images - DocAI or Cloud Vision on the NLI JPEGs rather than on the
    bitonal PDF. That would take the scan's nun/gimel gain without paying the
    VLM's running-text penalty, and it is the experiment that decides whether the
    corpus should be rebuilt from NLI. `google-cloud-documentai` is already a
    declared dependency (`tools/verify_local_setup.py`), but no submission path
    for loose page images exists in this repo yet.

    **A page-alignment near-miss worth recording.** NLI's images do not
    correspond to PDF pages by any fixed rule the file numbering exposes, so the
    tool matches pages by ink-profile correlation and refuses below a threshold.
    Lowering that threshold to recover 7 skipped pages produced two transcripts
    OF THE WRONG PAGE - p59 and p66 both matched the same NLI file, which is what
    exposed it. Facing pages of solid text correlate well with each other, so a
    respectable correlation is not evidence of the right page. The fix was a
    CONTENT check: the running head prints the root range (`אבח-אגד`) on rectos
    and the page number on versos, and comparing those against the Google Books
    layer caught p59, p80 and p84. All 35 pages now verify. The tool gained an
    explicit `--offset`, which once established over several pages is stronger
    than any per-page correlation.

    Incidentally: the Google Books text layer REVERSES the digits of the printed
    page number (`21` for 12, `92` for 29) - an RTL bug in that layer, not in the
    print. The NLI transcription reads them correctly.

0FT. **[2026-09-10] DASHBOARD AUDIT FOR HaShorashim: THE STALE-ARTIFACT HALF IS
    NOW FIXED; THE QUEUE HALF NEEDS A PER-WITNESS LABEL AND A PER-WITNESS CUT.**

    `review_server.py` resolves everything through `corpus_io`, and `cio.REPO`
    correctly follows `$SEFER_CORPUS_ROOT`, so a second book needs no code change
    to be SERVED - only `--port 8421`, leaving Yad Malachi's :8420 untouched.

    ### Fixed in this pass

    The corpus rebuild (`0FI`, 307 -> 314 entries) had silently orphaned every
    derived artifact. All four were still at 307 while `part1.json` was at 314,
    so klal ids had shifted underneath them:

    | artifact | was | now |
    |---|---|---|
    | `klal_page_regions.json` | 307 | 314 |
    | `klalim_demo_dataset.json` | 307 | 314 |
    | `part1_header_anchored_alignment.json` | 307 | 314 |
    | `word_identity.json` | 307 | 314 |

    `word_identity.json` was the dangerous one: re-seeding reported **280 of 314
    klalim where "every id after the first divergence names the wrong word"**. It
    was regenerated from scratch rather than patched, which is safe here only
    because no reviewer decision exists for this book yet - the ids carried no
    human investment. Had they, this would have been a recovery job.
    `build_header_alignment.py`'s guard refused to overwrite (223 klalim would
    change page) and was right to: the fresh build was inspected first and holds
    the same trust rate, 86.9% against 87.3%.

    ### Still needed, and none of it is data

    `review_queue_part1.json` is absent and its producer is vacuous for this book
    (`0ER`). The server's OTHER route - `reconstruction_witness_queue.json`,
    served as `opcode: "witness"` - now has a producer,
    `tools/build_witness_review_queue.py`, which anchors 1,362 of 2,793 disputes
    to a unique DocAI token (422 are words that repeat on their page and cannot
    be anchored safely; 942 have no matching token). The file is written. **The
    dashboard would still serve zero rows from it**, for two reasons that are
    both calibrations belonging to the OTHER witness:

    1. **`review_data.load_witness_queue` filters by vision verdict.** It keeps
       only rows where the vision pass sided against the corpus - a cut chosen
       when the witness was Tesseract at 3.8% accuracy. This witness is at 99.2%
       (`0FK`), and `0FQ` measured the vision pass at 18% on this book's dominant
       error class. Serving through that filter hides the real corrections behind
       a signal we have measured as broken.
    2. **`review_frontend/app.js` hardcodes the witness's name in four places**
       and displays "Tesseract was measured correct in only 3.8%". Putting
       Sefaria's transcription behind that label and that warning would actively
       push a reviewer to dismiss corrections that are right nine times in ten.

    So the remaining work is: carry `witness_name` and the witness's measured
    accuracy through to the UI (the queue file already records both), and make
    the priority cut per-witness instead of global. Both touch shared code and
    therefore oblige restarting the live :8420 dashboard, which is the reviewer's
    call and is why they are not done here.

0FS. **[2026-09-10] CONFIRMED, AND LARGER THAN EXPECTED: THE FULL-TONE SCAN
    TAKES NUN/GIMEL FROM 18% TO 90%. AND BINARIZING IT OURSELVES THROWS AWAY A
    THIRD OF THAT.**

    `tools/experiment_scan_source.py`, same protocol as `0FQ` - same 66
    positions, same prompt, same model, same fixed-seed A/B assignment. Only the
    pixels change.

    | source | correct | rate |
    |---|---|---|
    | Google Books, 1 bpc, 300 dpi | 12/66 | 18.2% |
    | Google Books, 1 bpc, 600 dpi | 10/65 | 15.4% |
    | **NLI, full tone, ~313 dpi, as scanned** | **47/52** | **90.4%** |
    | NLI, binarized by us with Otsu | 31/51 | 60.8% |

    The hypothesis in `0FR` is confirmed and the effect is not marginal. A scan
    with **half the linear resolution and a fifth of the pixels** takes this
    error class from worse-than-chance to 90%. The information was never missing
    from the printing; it was destroyed by somebody else's thresholding before
    the file reached us.

    **DO NOT BINARIZE.** Paired over 50 cases, our own Otsu pass BREAKS 15 that
    the raw tone gets right and fixes 1 - net -14. Binarization is not a
    preparation step for a modern vision model, it is a lossy decision that
    happens to be baked into most of the scans in circulation. The usual advice
    to "binarize and deskew before OCR" is advice for Tesseract-era engines and
    is actively wrong here.

    **THE SELECTION EFFECT, STATED PLAINLY.** These 66 positions were chosen
    because our DocAI pass - reading the bitonal scan - got them wrong. So the
    bitonal arms are being scored on their own known failures and 18% is not
    their general accuracy. What the experiment establishes is the actionable
    claim: **on the positions where the bitonal scan misleads our OCR, the
    full-tone scan recovers 90% of them**, and the NLI arm was not part of that
    selection. A general accuracy comparison needs an unbiased page sample and
    has not been run.

    Five full-tone failures remain (`ודגן`, `לאגם`, `אגפיו`, `ישגא`, `הדאגה`),
    all at 0.95-1.0 confidence. Confidence remains uninformative on this class in
    every arm - it is 0.95 whether right or wrong - so it must not be used as a
    filter anywhere.

    **What this changes.** The pipeline reads the Google Books scan because it
    has the most pixels; on the evidence it should read NLI's full-tone images
    and never threshold them. That is a re-OCR of the book from a different
    source, which is a substantial job and is NOT yet done - `part1.json` and
    every measurement in `0FH`-`0FN` still come from the bitonal scan.

0FQ. **[2026-09-10] RESOLUTION IS NOT THE CONSTRAINT ON THE VISION
    ADJUDICATOR. THE ADJUDICATOR IS 82-85% WRONG ON NUN/GIMEL AT 0.95
    CONFIDENCE, AND THE CONFIDENCE CARRIES NO SIGNAL AT ALL.**

    Paired experiment, `tools/experiment_crop_resolution.py`: 66 positions where
    our OCR read nun and Sefaria's reviewed text reads gimel, each put to
    gemini-3.6-flash twice - at 300 dpi (the current default) and at 600 (the
    scan's native) - with the same randomized A/B assignment both times, so the
    crop is the only variable.

    | | correct |
    |---|---|
    | 300 dpi | 12/66 (18.2%) |
    | 600 dpi | 10/65 (15.4%) |

    Paired: 3 wrong->right, 4 right->wrong, **net -1**. Doubling the resolution
    changes nothing.

    **The number that matters is not the difference, it is the level.** A
    two-alternative forced choice should score 50% by guessing. At 18% the model
    is not guessing - it systematically chooses the nun. Mean confidence 0.95,
    and mean confidence WHEN WRONG also 0.95, with fluent shape-based reasoning
    every time ("a flat horizontal base extending to the left, characteristic of
    a nun rather than a gimel"). There is no threshold that filters these out.

    The ground truth is not in doubt: the correct readings are `גבורים`, `גשר`,
    `תרגם`, `ואביגיל` - Abigail - against our `נבורים`, `נשר`, `תרנם`,
    `ואביניל`, which are not words.

    **This invalidates vision adjudication as a check on this error class**, and
    the class is a third of all our single-letter errors. It also explains p138
    (`ונוש`/`וגוש`, ruled OURS at 0.95, wrong): that was not an unlucky call, it
    was the modal behaviour.

0FR. **[2026-09-10] THE BITONAL SCAN FUSED THE GIMEL'S LEG. THE FULL-TONE SCAN
    KEEPS IT - AT HALF THE RESOLUTION. WE MAY BE OCR-ING THE WRONG SCAN.**

    Cropped the SAME gimel (in `לגדלתם`, p60, verified aligned) from both scans:

    * **Google Books, 1 bpc, ~600 dpi**: the gimel's descending left leg is
      present but WELDED to the adjacent stroke. The 1-bit threshold fused
      neighbouring ink, and the fused form is exactly a heavy nun.
    * **NLI, RGB, ~313 dpi**: the leg is a separate stroke with white space
      around it, and the gimel/dalet pair is plainly distinct.

    So the information the model needs is not missing from the PRINTING, and it
    is not missing because of resolution. It was destroyed by binarization,
    before we ever saw the file - which is precisely the step `0FO` records as
    already done, destructively, on both of our high-resolution copies.

    This reverses the working assumption. The pipeline runs on the Google Books
    scan because it has the most pixels; on this error class the lower-resolution
    full-tone scan appears to carry MORE usable information. It also sharpens the
    ask to NLI: a full-tone master at higher resolution would beat everything we
    hold, and full tone matters more than dpi.

    **STATED AS A HYPOTHESIS, NOT A RESULT.** It rests on one letter examined
    closely plus a mechanism that explains it. The test that would settle it is
    to OCR a sample of NLI pages - with and without adaptive binarization - and
    score the nun/gimel class against the 100 reviewed entries, the same ground
    truth used above. Not yet run.

0FO. **[2026-09-10] SCAN INVENTORY: THE HIGH-RESOLUTION COPIES ARE BITONAL AND
    THE FULL-TONE COPY IS THE LOW-RESOLUTION ONE. PRE-PROCESSING IS ONLY LIVE ON
    THE WORST SCAN.**

    Measured, not assumed, on the same printed page:

    | scan | pixels | bit depth | implied dpi |
    |---|---|---|---|
    | Google Books | 3528x5278 (18.6 MP) | **1 bpc, bitonal** | ~600 |
    | HebrewBooks | 2266x3444 (7.8 MP) | **1 bpc, bitonal** | ~385 |
    | NLI online | ~1842x2891 (5.3 MP) | **RGB, 24 bpp** | ~313 |

    This settles what pre-processing can and cannot do here. Binarization is the
    step most often recommended before OCR, and on the two high-resolution copies
    it has ALREADY BEEN DONE, destructively, at the source: a 1-bit image has no
    tone left to threshold better. Deskew and denoise remain available on all
    three. Adaptive binarization, contrast work and upscaling are available only
    on NLI - which is the lowest-resolution copy we hold.

    So pre-processing and the request to NLI are not alternatives. The request is
    what would make pre-processing worth doing: a master that is full-tone AND
    high-resolution is the only input on which the usual pipeline has anything to
    work with. The NLI contact confirms the online copy is 300 dpi and is asking what
    the printed-books masters are held at.

0FP. **[2026-09-10] WE CROP AT 300 DPI FROM A 600 DPI SCAN BEFORE ASKING THE
    MODEL TO JUDGE A FINE STROKE.**

    `pipeline/vision_adjudication_common.crop_pdf_bounding_box` takes `dpi=300`
    as its default and every caller uses it. The Google Books scan renders its
    native 3528 px at exactly 600 dpi, so every vision adjudication this project
    has run - including the one that got p138 `ונוש`/`וגוש` wrong at 0.95
    confidence - has been looking at a half-resolution crop, a quarter of the
    available pixels, of exactly the kind of distinction (a gimel's leg) that
    lives in fine strokes.

    Raising it is free and needs no new scan. It is NOT yet demonstrated to help:
    rendered side by side at 300 and 600, the gimel in `לגדלתם` (p60) is legible
    in both, so resolution may not be the binding constraint on the adjudicator.
    That makes it a cheap experiment with a real ground truth to score against -
    77 positions in the reviewed 100 where we read nun and the reviewed text
    reads gimel - not a fix to apply blind.

    **What could NOT be determined**: the raster DocAI itself worked from. I
    tried to infer it from coordinate quantization in the stored word boxes; the
    best integer-grid fit is 1637 px against a stored 3528 px, but the residual
    is 0.165 px where a real grid would be near zero and random would be 0.25.
    That is not evidence, and no claim is made from it. Answering it needs the
    submission path, not the stored output.

0FN. **[2026-09-10] MAJORITY VOTING ACROSS OUR ENGINES MAKES THE TEXT WORSE BY
    452 WORDS. INDEPENDENCE IS THE ASSET, NOT ENGINE COUNT.**

    Measured on the 100 reviewed entries (13,735 words of ground truth), three
    witnesses: Sefaria's OCR, our DocAI, and the Google Books text layer.

    | engine | word error rate |
    |---|---|
    | Sefaria's OCR | 1.35% |
    | ours (DocAI) | 8.59% |
    | Google Books layer | 10.48% |

    The error-set overlaps are the finding:

    | pair | Jaccard | share |
    |---|---|---|
    | DocAI & Google Books layer | **0.429** | 66.6% of our errors are also the layer's |
    | Sefaria & DocAI | 0.071 | 48.4% |
    | Sefaria & Google layer | 0.045 | 37.6% |

    Two Google engines on the same scan are ONE witness with a 0.43 Jaccard, not
    two. Lesson 24 (SAME INK, SAME FAILURE) now has a number attached to it.

    A 2-of-3 majority vote therefore **fixes 78 of Sefaria's errors and breaks
    530 that Sefaria had right - net -452 words**. All 530 breaks are positions
    where our two correlated engines agree on the SAME wrong reading and outvote
    the accurate witness. Naive adjudication across correlated engines is not
    neutral, it is harmful.

    **The rule this sets for adding any future engine**: evaluate it by the
    Jaccard of its error set against the engines already present, not by its
    standalone accuracy. A 10% engine that fails independently is worth more here
    than a 5% engine that fails the way we already do.

    Where the value actually is, on the same data: our disagreement with
    Sefaria's OCR is 1,054 positions (7.7% of the text) and contains 87.3% of the
    107 corrections a human made, with the right reading present in our column in
    82 of them. A detector, not a corrector-by-vote.

0FK. **[2026-09-10] THE .docx IS SEFARIA'S UNREVIEWED LAYER EXACTLY - 1.0000
    CHARACTER AGREEMENT - SO THE 100 REVIEWED ENTRIES GIVE A COMPLETE CORRECTION
    LEDGER.**

    Checked on the 10 unreviewed sample entries, citations stripped from both:
    character agreement is 1.0000 on every one. `0FD`'s figure of 0.899 was my
    own normalization noise, not a difference in the data. So .docx vs corrected
    on the 100 reviewed entries is precisely the list of corrections a human made.

    **Two tokenization artifacts had to come out first, and both were mine.**
    Stripping `<span>` to a SPACE split `האלף והבית` into four tokens: measured
    against the .docx, tags-to-space gives 0.9418 word agreement and tags-to-
    nothing 0.9988. And `&nbsp;` (13 of them) is not whitespace to `str.split()`,
    so `הרקמה&nbsp;הרבה` survived as one glued token. Both were invisible at
    character level, because joining words for a character comparison discards
    spaces anyway - which is exactly why the earlier character figures looked
    fine while the word figures did not.

    The ledger, after both fixes: **118 edits, of which 107 are OCR corrections
    and 11 are citations he added.** 107 corrections in 13,573 words is a word
    error rate of 0.79% in his raw extraction.

0FL. **[2026-09-10] OF HIS 107 CORRECTIONS WE INDEPENDENTLY HAD 82 RIGHT, AND WE
    SHARED HIS ERROR EXACTLY ONCE.**

    | | | |
    |---|---|---|
    | we already had his correction | 82 | 76.6% |
    | we had a third reading | 22 | 20.6% |
    | we shared his error exactly | 3 | 2.8% |

    Two of those three are not OCR errors at all - a citation typo he introduced
    (`שמית` for `שמות`) and an editorial note he added. **One genuine shared
    error**: `במינוי` for `במינו`.

    What an automated pass could have done with his raw text plus ours:

    | rule | flags | catches | precision |
    |---|---|---|---|
    | our reading disagrees with his | 1,054 (7.7% of text) | 87.3% | 9.8% |
    | + his word not in the lexicon | 195 (1.4%) | 49.2% | 29.7% |
    | + his word not a word AND ours is | 92 (0.7%) | 28.0% | 35.9% |
    | + single token, ours a word, his not | 40 (0.3%) | 19.5% | 57.5% |

    **82 of the 107 we could have FIXED outright**, not merely flagged, because
    our reading already IS his correction. The value here is not our extraction
    quality - it is worse than his - it is that the two engines fail
    differently, which is Lesson 24 pointed at someone else's corpus.

0FM. **[2026-09-10] THE VERSE CHECK CANNOT FIND SEFARIA'S OCR ERRORS - THEIR
    QUOTATIONS WERE ALREADY MACHINE-VERIFIED. IT FINDS THEIR CITATION ERRORS
    INSTEAD.**

    Of his 118 edits, **exactly ONE falls inside a verified biblical quotation**.
    The rest are in Ibn Janah's own prose, which has no source. The reason is in
    his own export note: the raw layer already has "automated citation
    resolution/linking applied (refLinks verified against Tanakh text)". The
    quotations were cleaned against Tanakh before any human saw them.

    This corrects the framing in `0FF`. The verse check is powerful against OUR
    text - it settles 673 of our 2,793 disputes - and near-useless for finding
    OCR errors in theirs. Do not tell Sefaria it will clean their running text.

    **What it does find in their data is misplaced references**, and those were
    never machine-checked, because resolving a citation as written cannot notice
    that the numeral itself was misread. `tools/validate_quotations.py` grows the
    quotation backwards from each marker, and where it fails to corroborate,
    searches the cited book for the verse the quotation actually reproduces:

    * 20,450 citations, 66.1% of quotations verified against the cited verse
    * **158 citations whose quotation reproduces a different verse of the same book**
    * 52 of those are off by one verse and are flagged separately as a possible
      edition-numbering difference (17 in Jeremiah alone, a chapter with known
      variant numbering) - NOT presented as errors
    * of the remaining 106, **72 (68%) are explained by a single Hebrew-letter
      substitution in the numeral**, and the substitutions are the same OCR
      confusion classes as the body text: `ה`/`ח` 31, `ב`/`כ` 16, `ו`/`ז`,
      `כ`/`נ`, `ט`/`מ`

    Examples: `(ישעיה נט, יד)` for Isaiah 29:14 (`נט`/`כט`), `(בראשית מא, כז)`
    for Genesis 41:57 (`כז`/`נז`), `(אסתר ח, יב)` for Esther 5:12 (`ח`/`ה`).

    **22 of these are inside the 100 entries a human already reviewed**, along
    with 28 suspect words in verified quotations - so this finds things that
    survived manual review. Delivered as `citation_corrections.csv` (headword,
    note as printed, cited ref, proposed ref, matching words, the single-letter
    confusion, the quotation, and a Sefaria URL).

    **Four positions where the verse backs OUR reading over his CORRECTED text**,
    each verified against the verse data directly rather than from memory:
    `ואונו`/`ואנו` <https://www.sefaria.org/Job.40.16>, `בין`/`בן`
    <https://www.sefaria.org/Hosea.13.15>, `ובנותיך`/`ובנתיך`
    <https://www.sefaria.org/Isaiah.60.4>, `במו`/`כמו`
    <https://www.sefaria.org/Isaiah.44.19>.

    Three defects of mine had to be fixed before any of this was deliverable, all
    found by disbelieving a result rather than by a test: anchors emitted in WORD
    units by one producer and TOKEN units by the other (which made the verse check
    appear to catch zero); the search window straddling the previous quotation;
    and verse RANGES (`ח—י`, 11 of them) collapsed to a single gematria. Together
    they turned 448 false candidates into 158.
    **ANNOTATED 2026-09-14 (reviewer: "did we / can we do this?" about the
    Sefaria editor's shelved request).** A spot-check of the first six
    `misplaced_citations` rows in `quotation_suspects.json` found five real
    errors (Job 5:6, Genesis 35:18, Proverbs 29:20, Jeremiah 36:22,
    Genesis 9:5) and ONE row where the window still straddles the previous
    quotation. For `איל` the note `(שם נז, ה)` is right for `הנחמים באלים`
    (Isaiah 57:5), but the window ran back into `ותחפרו מהגנות אשר בחרתם`
    (Isaiah 1:29) and proposed 1:29. So the straddle fix above is not
    complete, and `citation_corrections.csv` (158 rows) needs an eye pass
    before it is relied on. Whether the draft to the Sefaria editor that
    attaches the file was sent is not recorded here. (Reviewer, the same day:
    it was not.) The first version of this annotation named that draft by its
    FILE NAME, and the corpus-root drafts are named after their recipients, so
    the editor's name was in this public file. The commit was amended before
    any push. Refer to the drafts by recipient role, never by file name.
    **CORRECTION, same day (reviewer: "cit corr - you checked the first 6
    rows?").** In chat I called those six "the first six rows" of
    `citation_corrections.csv`. They are not. They are the first six of the
    same 158 citations in `quotation_suspects.json`, in a different order. All
    six are in the CSV, the Isaiah 57:5 false alarm included. The CSV's own
    first six rows, checked against Sefaria's verse text in
    `sefaria_reference_corpus/raw`:
    * **4 are real misprinted numerals:** `(ויקרא יח, ב)` for Leviticus 18:20
      (ב/כ); `(ויקרא כ, ה)` for Leviticus 2:5 (כ/ב); `(אסתר ח, יב)` for
      Esther 5:12 (ח/ה); `(משלי לא, כ)` for Proverbs 31:2 (כ/ב).
    * **2 are a numbering difference, not an error:** `(שם לא, לא)` and
      `(שם לא, לב)` quote what Sefaria numbers Jeremiah 31:32 and 31:33.
      Both are one lower in the same chapter, so the edition numbers
      Jeremiah 31 one verse off Sefaria. The printed note is right by its own
      numbering; the proposed ref is still the one a Sefaria link needs.
    * **A labelling defect across the file.** 45 rows are off by exactly one
      verse, and 37 of them carry a `single_letter_confusion` label such as
      `א->ב` or `ב->ג`. Adjacent numerals are not a visual OCR confusion. The
      label is filled in whenever the two numerals differ by one letter, and
      it presents a numbering difference as a misprint. Not fixed.
    **FIXED 2026-09-14 (reviewer: "not sent. do 1").** Every one of the 158
    rows was read against Sefaria's verse text. Verdicts:
    * 92 misprints;
    * 36 edition numbering (Jeremiah 31 ×17, I Samuel 24 ×8, Exodus 20 ×7,
      I Chronicles 12 ×4);
    * 16 off by one in a single case, where the data cannot tell a misprint
      from a numbering difference;
    * 12 not an error. Nine are windows that reached an earlier quotation.
      The other three: #97, where the note is for `וישגם` (Genesis 44:6);
      #140, for `פי ה'` (Exodus 17:1); #152, where Ibn Janah says "about
      Babylon", which is Jeremiah 50:44;
    * 1 wrong proposal: `(משלי טו, ג)` is Proverbs 16:3, not 3:7;
    * 1 unclear.
    They are recorded in `citation_review.json` in the corpus root.
    `validate_quotations.py` now:
    * drops a candidate whose last two quoted words belong to the cited
      verse and not to the verse the run matched (`ends_in_cited`);
    * labels a one-verse offset "edition numbering" when its chapter has it
      repeatedly (`citation_kind`), and clears the letter label for those;
    * applies the verdicts with `--review`, adding `kind`,
      `checked_by_eye` and `why`.
    **Its first version dropped a real row.** The last two words of the
    Jeremiah 31:31 note, `נאם ה'`, are a formula that stands in 31:31 and
    31:32 alike, so the words must single out the cited verse. Before any
    change, the regenerated file was compared with the committed one: the
    same 158 rows in the same order. The new CSV has 146 rows: 92 misprint,
    36 edition numbering, 16 off by one, 1 wrong proposal (corrected to
    Proverbs 16:3), 1 unclear. Every row reads `checked_by_eye = yes`.
    Exactly the 12 "not an error" rows are gone: 8 by the rule, 4 by
    verdict. Test: `test_a_citation_is_right_when_the_words_before_it_end_in_its_verse`.

0FH. **[2026-09-10] THE 100 REVIEWED ENTRIES ARRIVED. OUR READ IS 95.6% OF
    CHARACTERS AGAINST THEM, AND THE SHORTFALL IS MOSTLY STRUCTURAL.**

    The Sefaria editor sent `ibn_janah_corrected_100.json` - the first 100 manually reviewed
    entries in dictionary order, all in א, reviewed 2026-08-22/23. All 100 fall
    inside the א-ב-ג slice. Ground truth went from 1,946 words to 14,295.

    | | words | characters |
    |---|---|---|
    | our OCR vs his corrected, all 100 | 0.8402 | **0.9562** |
    | the 85 structurally sound entries | - | **0.9685** |

    Median entry is 0.980; the mean is dragged by a tail of entries with a
    STRUCTURAL fault, not a reading fault. That distinction is the finding. The
    worst offenders were an entry boundary we missed (so two entries merged), the
    footnote apparatus leaking into the body, and running-head debris - none of
    them letters misread.

    `0FE`'s five-entry figures (0.8977 / 0.9643) were optimistic on both axes.
    Five entries is five entries.

    Caveats he stated and they are real: stray citations or verse words may still
    need correction, he re-cut Mishnah citations to Sefaria ref syntax, and he
    removed internal cross-references from the inline citations (they work better
    as footnotes). So the corrected layer is a strong baseline, not a gold
    standard, and `0FD`'s rule still holds - nothing is scored against a witness
    as though it were error-free.

0FI. **[2026-09-10] TWO HEADING FORMS THE DETECTOR COULD NOT SEE. A MISSED
    HEADING DOES NOT LOSE TEXT, IT MERGES IT.**

    Chasing the worst entry in the `0FH` comparison - our `אלל` at 987 words
    against his 62 - found the detector blind to two real heading forms:

    * **A QUALIFIER after the letter names.** The edition distinguishes two
      entries that spell the same root with a following word: `האלף והלמד וההא
      הרפה` and `... הנראת` are the two `אלה` entries (his data splits them as
      `אלה a` / `אלה b`). The pattern required the terminator directly after the
      last letter name, so both were invisible. Discovered from the data by
      clustering every line whose letter-name run is complete but unterminated:
      `עוד` 35, `הנראית`/`הנראה`/`הנראת` 8, `הרפה`/`הרפא` 3, `הצירי` 1 - 46
      book-wide, 7 in the slice. `הכפול` (3) is NOT a qualifier: it is the
      masculine of `הכפולה` and doubles the letter, and skipping it would
      mis-key the entry.
      **CORRECTED 2026-09-14 (`0GG`): `הצירי` was never a qualifier.** Its one
      occurrence is p108 `הבית והואו והצירי.`, where `צירי` is the third LETTER
      NAME of `בוץ` - the list's vav in front, the same four letters in the NLI
      photograph and the Google copy. The qualifier pattern could not match it
      and בוץ merged into בוס. It is a letter name now.
    * **A geresh INSIDE a letter name.** p65 prints `האלף והואו והיו"ד`, and
      Sefaria's own transcription writes `אל'ף`, `בי'ת` throughout. One line in
      this scan; it is what merged our `אוח` with `אוי`.

    Effect on the corpus: 307 -> 314 entries, nothing lost, `אלל` from 5,245
    chars to 335, and all 100 of the witness's entries now align (was 97).
    Character agreement 0.9497 -> 0.9562, structurally sound entries 81 -> 85.

    A near-miss worth recording: the first rebuild appeared to LOSE 7 entries and
    I began attributing it to the qualifier change. It was my own invocation -
    `--cross-check` omitted, so the text-layer recovery never ran. Check the
    command before blaming the diff.

0FJ. **[2026-09-10] NUN/GIMEL IS THE DOMINANT ERROR CLASS AND THE BIAS IS OURS.
    WHERE ANY SOURCE CAN CHECK IT, HIS CORRECTION WINS.**

    The Sefaria editor flagged this himself: nun/gimel interchanges were frequent in
    Arabic words, and some of his corrections may be wrong. Measured across single-letter
    substitutions:

    | | vs his corrected | vs his uncorrected |
    |---|---|---|
    | nun/gimel share of all substitutions | 33.6% (73/217) | 42.9% (378/882) |
    | ours-nun / his-gimel | 66 | 339 |
    | ours-gimel / his-nun | 7 | 39 |

    The asymmetry is the point: our engine reads gimel as nun about nine times
    more often than the reverse. This is our systematic defect in this typeface,
    not a symmetric confusion.

    His worry does not survive contact with the evidence, as far as any external
    source can reach:

    * **The verse decides 11 of them. All 11 go to him, none to us.** (60 of 61
      against his uncorrected text.)
    * Of the 48 the verse cannot reach, **his reading is a real Hebrew word in
      40** - `תרגום`, `וגאון`, `ודגן`, `וגם` - while ours are nonwords
      (`תרנום`, `ונאון`, `ודנן`, `ונם`).
    * Of the remaining 8, six have his stem in the lexicon and ours absent.

    **Exactly one position is genuinely open**: p78 `אל`, ours `ההגעה` against
    his `ההנעה`. Both are real grammatical terms with both stems in the lexicon,
    the word is not in a quotation, and no source available to either of us
    settles it.

    The honest limit: 75% of nun/gimel disputes are uncorroborated by the verse,
    and those are precisely the Arabic-in-Hebrew-letters cases he is worried
    about - the check is blind exactly where his concern lives. What can be said
    is that no miscorrection was found, and that the lexicon reaches most of what
    the verse cannot.

0FC. **[2026-09-10] A MAQAF WAS BEING DELETED INSTEAD OF SPLITTING. IT PUT
    18,627 IMPOSSIBLE WORDS INTO THE LEXICON AND 580 PHANTOM ROWS INTO THE
    HUMAN QUEUE.**

    Three tools each wrote `re.compile(r"[֑-ׇ]")` and deleted the whole block.
    That block mixes two different things: marks that sit ON a letter (vowels,
    cantillation), which carry no boundary, and punctuation that sits BETWEEN
    words, which does. U+05BE MAQAF is the second kind - it is what joins
    `אֶת־כָּל־הָעַמִּים` in a pointed text - so deleting it yields the single
    token `אתכלהעמים`.

    Measured over Sefaria's 39 books of Tanakh, not estimated:

    | rule | tokens | word types |
    |---|---|---|
    | deleting (shipped) | 267,787 | 56,157 |
    | separating (fixed) | 310,095 | 40,138 |

    So 42,308 tokens - 13.6% - were being welded to a neighbour. Consequences,
    both silent:

    * **`lexicon.txt` for this book was 8.6% fiction.** 18,627 of its 217,841
      types were glued forms that can never match anything, and 1,169 real
      Tanakh word types were absent from it altogether - `ומן`, `נבט`,
      `מגרשיה`, `טבחים`. This is the lexicon used as a validity signal by
      `compare_ocr_engines.py`, by the lexical detectors and by
      `extract_pdf_text_layer.py --order detect`, in a book that is a
      **dictionary of the Bible**. Rebuilt: 199,890 types.
    * **580 of 3,373 witness disputes - 17.2% - were not disputes.** The witness
      is pointed and writes the phrase with maqaf; our corpus is unpointed and
      writes it with spaces. A typography difference was queued for a human as a
      disagreement about letters. Queue is now 2,793.

    Yad Malachi is NOT affected: its `lexicon.txt` is derived from its own
    unpointed OCR and contains no maqaf (checked, not assumed).

    Fixed at the seam rather than in three places - `corpus_io.HEBREW_POINTS`,
    `HEBREW_PUNCT`, `strip_points()`, `hebrew_words()` - because the same rule
    was independently written three times and all three were wrong the same way
    (Lesson 34 SWEEP THE SIBLINGS). Regression test:
    `test_a_maqaf_separates_words_instead_of_vanishing`. Full suite green.

0FD. **[2026-09-10] THE `.docx` SET IS SEFARIA'S *UNCORRECTED* TEXT. A CLAIM
    THAT IT WAS THE CORRECTED LAYER WAS VERIFIED BY A TEST THAT COULD NOT FAIL.**

    Asked directly whether the comparison used the corrected layer, this project
    answered yes and offered as evidence that `פרי` (corrected) was present in
    the witness while `נורי` (raw) was not. The test was substring membership
    over a whole entry, and `פרי` occurs elsewhere in that entry - in
    `בפרי הנחל` - so it passed without touching the disputed position at all.

    At the disputed position the three layers read:

    | layer | reading |
    |---|---|
    | Sefaria, manually corrected | `שהוא פרי` |
    | the `.docx` set | `שהוא נורי` |

    `נורי` is the OCR error; the corrected layer fixed it. Aggregate agreement
    with the corrected text, citations removed, over the 20 sample entries:
    `.docx` 0.899 against RAW, 0.798 against CORRECTED. The `.docx` is the
    pre-review source.

    **What this does and does not invalidate.** `gold_disputes.json` - the 156
    rows behind the review panels - is built from `corrected_sample` and IS the
    corrected layer, so the panels were right. `witness_disputes.json` (2,793)
    is built from the `.docx` and compares our OCR against THEIR UNCORRECTED
    OCR. That is still a useful independent witness (Lesson 24: different ink,
    different engine) but it is **not ground truth**, and nothing may be scored
    against it as if it were.

0FE. **[2026-09-10] MEASURED AGAINST THE CORRECTED TEXT ON ONE BASIS: OURS
    96.4% OF CHARACTERS, THEIRS 99.6%.**

    Earlier figures (98.4% / 99.1%) were taken on inconsistent bases - the maqaf
    defect was in one side, and inline citations were counted against the text
    that keeps them as footnotes. Recomputed with citations and editorial
    brackets removed from both sides, weighted by entry length, over the 5
    corrected entries inside the א-ב-ג slice - 1,946 words of ground truth:

    | | words | characters |
    |---|---|---|
    | our OCR vs corrected | 0.8977 | 0.9643 |
    | their `.docx` vs corrected | 0.9639 | 0.9960 |

    The gap is wider than previously stated and runs against us. Five entries is
    still five entries; this is why the ask to the Sefaria editor is 100 reviewed entries.
    **Do not quote these to him as a rate.**

0FF. **[2026-09-10] DISPUTES CAN BE SETTLED AGAINST THE VERSE THE APPARATUS
    CITES. 610 OF 2,793 SETTLED WITH NO HUMAN AND NO VISION CALL.**

    `tools/extract_witness_footnotes.py` recovers all 20,450 footnote TEXTS (the
    earlier pass kept only their positions); `tools/anchors_from_inline_citations.py`
    does the same for the corrected export, whose citations are already inline;
    `tools/adjudicate_against_verse.py` settles a disputed word by looking up the
    verse its quotation comes from.

    It overturned a vision verdict held at 0.95. On p138 our text reads `ונוש`
    and the corrected text reads `וגוש`; the adjudicator ruled OURS, reading the
    glyph as a nun. The entry's footnote 1 cites <https://www.sefaria.org/Job.7.5>,
    which reads `רִמָּה (וגיש) [וְג֣וּשׁ] עָפָר` - **gimel in both ketiv and qere**
    - and the entry's own headword is `גוש`. The verse settled in one lookup what
    the crop could not.

    ### Three things had to be right before any verdict meant anything

    **The span cannot be "everything since the last footnote."** Between two
    markers sits Ibn Janah's own argument, which has no source; a 19-word stretch
    containing a 4-word quotation scores 0.17 however right the citation is. That
    first attempt left 77% uncorroborated. The run is now grown BACKWARDS from
    the marker while the words keep appearing in the verse, with the disputed
    position itself exempt - if our reading is the wrong one it will not be in
    the verse, and it must not be allowed to truncate the quotation that proves
    it wrong.

    **The citation must be checked before it is trusted.** This apparatus
    contains transposed references: `ויתאבכו גאות עשן` is
    <https://www.sefaria.org/Isaiah.9.17>, its note reads `(ישעיה יז, ט)` = 17:9.
    Isaiah 17:9 is a real verse, so a naive lookup returns a real text with
    nothing to do with the quotation and BOTH readings come back absent - a
    silent wrong answer. Transposition is tested explicitly and named.

    **The anchors and the readings must come from the SAME text.** The .docx
    anchors index Sefaria's uncorrected stream; the gold disputes carry their
    corrected readings. Locating a corrected reading in an uncorrected stream
    picked wrong quotations and produced 30 spurious "ours" wins. The corrected
    export carries its citations inline at the marker's position, so it anchors
    itself - hence the second tool.

    ### Results

    Gold (122 disputes against the 5 corrected entries in the slice): 82 reach a
    cited verse, **13 decided, every one of them for the corrected text and none
    for us** - which is what a hand-corrected witness should look like. 67
    uncorroborated, of which 40 match zero words: the disputed word sits in Ibn
    Janah's own prose and has no source to check. That is a real limit, not a
    failure.

    Full queue (2,793 disputes against their uncorrected text): 1,952 reach a
    cited verse, **662 for them, 11 for us, 9 both, 131 neither, 1,139
    uncorroborated**. So 673 positions - 24.1% of the whole queue - are settled
    at zero marginal cost, and the 662/11 split is consistent with the character
    measurement in `0FE`.

    Citation parsing is at 96.2% of 20,450 (was 85.5%). Bacher abbreviates book
    names by TRUNCATION with a geresh - `ישע'`, `ברא'`, `שופ'` - which an
    exact-match table misses, so a truncation now resolves as a UNIQUE prefix of
    a real book name and resolves to nothing when ambiguous (`מ` prefixes
    מלכים, מיכה and מלאכי alike). `(שם, שם)` - a second note on the same verse,
    98 of them - now inherits the whole previous reference rather than being read
    as a gematria.

    The 11 are worth their own look: they are positions where THEIR text is
    wrong and ours is right, verified against the verse. Examples -
    `וצפיר`/`משיר` at <https://www.sefaria.org/Daniel.8.8>, `במו`/`כמו` at
    <https://www.sefaria.org/Isaiah.44.19>, `באנק`/`נאנק` at
    <https://www.sefaria.org/Ezekiel.26.15>, `דגן`/`מן` at
    <https://www.sefaria.org/Hosea.7.14>. Written to
    `verse_adjudication_witness.json`.

    The 131 `neither` are apparatus QC candidates: both readings absent from the
    cited verse means the citation is wrong, the quotation is abbreviated, or the
    printing follows a variant. Worth showing the Sefaria editor.

0FG. **[2026-09-10] AN INVISIBLE JOINER WAS TEARING WORDS IN HALF.**

    Found while auditing a verdict that looked wrong: `ירושלים` vs `ירושלם` came
    back as `neither`, though <https://www.sefaria.org/Isaiah.22.21> plainly has
    the word. Sefaria writes Jerusalem as `יְרוּשָׁלַ֖͏ִם` with U+034F COMBINING
    GRAPHEME JOINER between the two vowel signs. U+034F is not a Hebrew letter,
    so a "split on non-Hebrew" rule cut the word into `ירושל` and `ם`, and the
    lookup reported the word absent from the verse it is in.

    Counted across the reference corpus: 652 U+034F, 769 U+200E, 2 U+200D. Now
    deleted in `corpus_io.INVISIBLE` before anything splits. Moved 25 rows out
    of `both` and into a decision. Same regression test as `0FC`.

    Same family as the maqaf defect and found the same way - by disbelieving a
    verdict and checking it against the source rather than accepting the
    aggregate.

0EY. **[2026-09-10] SEFARIA'S FILES CARRY THE ENTIRE APPARATUS AS 20,450
    ANCHORED WORD FOOTNOTES. WE DETECT 66% OF IT AND SHOULD NOT TRY FOR MORE.**

    The `.docx` files are not plain text with citations typed inline. Each one
    carries `word/footnotes.xml` - 2 MB in chapter 01 alone - and every footnote
    is ANCHORED to a position in the running text:

        footnote bodies              20,450
        in-text anchor markers       20,450
        look like `(book ch, v)`     20,092   98%

    The rest are Bacher's own editorial cross-references, e.g.
    `(עיין מה שכתבתי בספרי על חיי ר' יונה דף 201)` and `(למע 852 רקמה 551)`,
    pointing into Sefer HaRikmah. So this is the complete apparatus of the Bacher
    edition, transcribed, normalised to `(שה"ש ו, יא)` form, and positioned.

    **This is far more than "attention to citations" and I had underrated it.**
    Items `0EM` and `0EE` described the dataset's value from its bracketed root
    headwords and its nikkud; the apparatus is the larger part and it is
    structured, not prose.

    ### What our own detection is worth against it

    Item `0EX` recorded 2,085 inline reference numerals for א-ב-ג. Against their
    anchors on the same 306 entries:

        our inline reference numerals    2,085
        their anchored footnotes         3,159
        recall                              66%
        entries where we find fewer        226
        equal                               59
        more                                21

    So roughly **1,074 references in א-ב-ג alone are invisible to us** - the ones
    DocAI fused into the preceding word as Hebrew letters (`החכסייג`) or dropped
    outright. The 246 `footnote_numeral` disputes in item `0ES` are the visible
    tip of that, not the whole of it.

    ### The consequence, and it is now overdetermined

    Item `0EX` measured that the apparatus BLOCK cannot be paired to the body by
    number (0 of 94 pages). This measures the other end: even the body-side
    markers are only 66% recoverable. **Two independent measurements now say the
    same thing** - the citation apparatus is not reconstructible from this OCR at
    usable quality, and Sefaria's version of it is the one to use.

    That makes the division of labour concrete in both directions: their
    apparatus and their citations, our running text (where their own transcription
    scores 92.0% to our 90.3%, item `0EO`, i.e. we are comparable and both need
    the ink). The remaining engineering question is how to MERGE them, which is
    not a question this pipeline has ever had to answer before.

    **Open, and it is the right next conversation with the Sefaria editor:** their footnote
    anchors are positions in THEIR text, and our text is a different token
    stream. Transferring the apparatus onto our corpus means aligning the two at
    word level - which is exactly what `tools/build_witness_disputes.py` already
    does to find disagreements, so the alignment exists and the anchors could ride
    on it. Not built.

0EX. **[2026-09-10] 2,085 INLINE FOOTNOTE REFERENCES RECORDED. AND A MEASURED
    REASON NOT TO REBUILD SEFARIA'S CITATION WORK: 0 OF 94 PAGES PAIR.**

    ### The easy half: standalone reference numerals

    `build_root_corpus.py` now records the word positions of Bacher's inline
    reference numerals as a `footnote_refs` field. **2,085 of them across 273 of
    307 entries, and `clean_text` is unchanged** - recorded as structure, not
    removed, because Sefaria named footnote demarcation as a requirement and this
    project's fidelity rule forbids silently deleting from the text. What
    representation they finally take is the reviewer's decision.

    The rule is safe for a reason specific to the book: **19th-century Hebrew
    numbers with letters** (`יח יז`), so a standalone Arabic numeral cannot be
    part of the text. Every context confirms it -

        ולא אבה י"י אלהיך 11 כבר נזכר
        בשאול ואבדו לא תשבענה 10

    a biblical quotation, the reference, then the commentary. Values run 1..~50
    per page, matching the printed apparatus, with a few OCR outliers (624).

    ### The hard half stays with Sefaria, and now there is a number for why

    The apparatus lines this pipeline drops CONTAIN the citations those
    references point to, so pairing reference N with citation N would reconstruct
    the whole apparatus independently. It does not work:

        pages with body references                                    94
        body reference numerals                                    2,086
        apparatus numerals legible                                 2,457   (118%)
        pages where EVERY body ref has a matching apparatus numeral     0   (0%)

    The apparatus numerals are printed small and DocAI mangles them - on p121 the
    run reads `1 ... : ... 8 ... י ... •` where the print has 1,2,3,4,6,7 - while
    chapter and verse numbers INSIDE citations come out as digits and inflate the
    count to 118% of the body's. So the two sides cannot be aligned by number,
    and aligning by position would compound both error rates.

    **This is the measured form of item `0EE`'s reasoning.** Sefaria's dataset has
    the citations done carefully by a human; rebuilding them from this OCR would
    produce a worse apparatus and cost the time item `0EE` said to save. The
    division of labour is now a finding rather than a courtesy: their citations,
    our running text.

    **Still not solved: the fused half.** A numeral DocAI absorbed into the
    preceding word as Hebrew letters (`החכם` + superscript 29 + `ג` ->
    `החכסייג`) leaves no numeric token to detect. Those are the 246 witness
    disputes in item `0ES`, 55% of which vision confirms as real errors, and they
    need the ink one at a time.

0EW. **[2026-09-10] WHOLE-BOOK HEADING DETECTION MEASURED AGAINST AN
    INDEPENDENT SOURCE: 94.2% RECALL, AND THE MISSES ARE SCATTERED.**

    `tools/detect_root_entries.py` over all 651 pages of the recovered text layer,
    against Sefaria's 22 files:

        ours (PDF text layer)   1,871 distinct roots
        theirs                  1,974
        in both                 1,860   = 94.2% of theirs
        only theirs               114
        only ours                  11

    **The misses are spread, not clustered** - צ 12, ר 12, י 11, ש 10, מ 9, נ 8
    and a long tail. That matters: the earlier `רש` bug (item `0EJ`) took out an
    entire 30-page מאמר and showed up as one letter at zero, which the
    alphabetical-order check could not see. A flat distribution across 20 letters
    is the signature of individual headings garbled by OCR, not of a rule that is
    wrong.

    The 11 we have and they do not are the more interesting direction and have
    not been looked at - each is either a real entry their transcription missed or
    a false positive of ours, and both are worth knowing.

    **The obvious next step, not done:** the recovery mechanism built in `0EO`
    already takes a boundary from one source when the other garbles it. Pointing
    it at Sefaria's root list instead of the text layer would recover most of the
    114 the same way, since their list is independent of both our OCR sources.
    That would put whole-book heading recall close to 100% before any human looks
    at it - but it makes the corpus structurally dependent on their data, which is
    a decision about the collaboration rather than a technical one, and it should
    be made with the reviewer awake.

0EV. **[2026-09-10] THE REMAINING GAP FOR THE DEMO: THE DASHBOARD CANNOT SHOW
    THE ONLY QUEUE WORTH SHOWING. NOT STARTED, DELIBERATELY.**

    The Sefaria editor asked to try the review dashboard. Everything the
    dashboard needs for HaShorashim now exists - corpus, regions, alignment, page
    images, word ids, lexicon - with one exception, and it is the important one.

    `review_server.py` builds its flag overlay from `review_queue_part1.json`,
    which comes from `assemble_corrections_dataset.py`, which comes from the
    DocAI-vs-corpus diff. **For this book that diff is vacuous** (item `0ER`):
    346 candidates, zero reading differences. So the dashboard would open, render
    the scan, highlight nothing worth ruling on, and look like a clean book.

    The queue with real content is `witness_disputes.json` - 3,373 rows, ~23% of
    which the vision adjudicator confirms as genuine corpus errors - and the
    server has no route to it.

    **Why I did not build it tonight.** It means changing `review_server.py` or
    its data layer, and this repo's standing rule is to restart the dashboard on
    any change to the server OR anything it imports. The reviewer's Yad Malachi
    dashboard is running on :8420 and is the live review tool; a second book
    cannot bind that port and a half-finished server change made unattended could
    take the deliverable book's review offline. That is not a risk worth taking
    without someone awake.

    ### The shape it should take

    Not a new pane. `review_queue_part1.json` is a rebuild-owned derived file, so
    the cheapest correct route is a SECOND queue source that the assembler merges,
    with each entry carrying which witness raised it - the dashboard already
    distinguishes `cross_edition` and `same_edition_agreeing` for Dicta (Lesson
    38), and a human-supervised witness deserves at least that much labelling. A
    reviewer should be able to see "Sefaria's transcription reads X here" as a
    different kind of claim from "Surya reads X here".

    Two things to settle before writing it: whether a witness dispute enters the
    same queue as a candidate correction or a parallel one, and whether the
    vision verdict is shown as a pre-filter (only surfacing the ~23% the ink
    supports) or as an annotation on all of them. Lesson 49 argues for the first;
    item `0DV`'s "563 permanent flags on unread material" argues loudly for not
    surfacing 3,373 rows to a human at all.

0EU. **[2026-09-10] FETCHING TANAKH INVALIDATED THE SHARED REFERENCE CACHE FOR
    YAD MALACHI'S DETECTORS. NOT REBUILT - THAT IS THE REVIEWER'S CALL.**

    `sefaria_reference_corpus/` is SHARED between books: it sits beside the code,
    not in a corpus root, and `word_freq.json` is the attestation table several
    Yad Malachi detectors reason against. Item `0EN` added 39 Tanakh books to it
    for HaShorashim, so:

        books cached in word_freq.json   166
        books on disk now                205
        on disk but not in the cache      39

    `tools/detect_split_merge.py` noticed by itself and refused to run -
    "built by a different extractor version or from a different set of books ...
    Skipping truncated-word completion rather than scoring against a corpus of
    unknown shape". That is the right behaviour and it is why this is a flagged
    item rather than a silent corruption.

    **Rebuilding it is NOT a neutral refresh and I have not done it.** The table
    decides what counts as attested Hebrew, so adding the Bible makes forms
    attested that were not, and every lexical measurement Yad Malachi has on
    record - including item `0DU`'s "166 of 166 came back as the stored text" and
    the 6.18M-word figures cited in Lesson 38 - was computed against the 166-book
    table. Rebuilding changes the basis of those numbers without changing the
    text they describe.

    Two defensible options, and the choice is a judgement about the deliverable
    book rather than a technical one:

    1. **Rebuild to 205 books.** Yad Malachi quotes Tanakh constantly too, so the
       larger table is arguably the better instrument - but every recorded
       lexical figure becomes non-comparable and should be re-measured.
    2. **Keep the reference corpus per-register**, as
       `fetch_sefaria_reference_corpus.py --register` now allows, with a separate
       frequency table per book. More faithful to each book's language, and it
       leaves Yad Malachi's recorded measurements standing.

    I would take (2) - a register is a property of the book, which is the same
    reasoning that moved book identity into `book.json` - but it is not my call
    to make on the deliverable, and until it is made `detect_split_merge.py` is
    inert for BOTH books.

0ET. **[2026-09-10] A HUMAN-SUPERVISED WITNESS YIELDS 36% REAL CORPUS ERRORS
    WHERE THE LEXICAL DETECTORS YIELDED 0%. THAT IS THE ARGUMENT FOR THE
    COLLABORATION, MEASURED.**

    36 disputes from Sefaria's dataset (first 12 of each class) cropped and put
    to the vision adjudicator via `verify_flagged_candidates_vision.py --source
    witness`, a new source added to the existing tool rather than a parallel
    caller:

        A = corpus (ours) correct      23   63.9%
        B = witness correct, WE ARE WRONG   13   36.1%
        median confidence               0.98

    By dispute class, which is where it gets useful:

        footnote_numeral    8 B / 4 A     67% real corpus errors
        one_letter          3 B / 9 A     25%
        other               2 B / 10 A    17%

    ### Set that against item `0DU`

    On 2026-09-09 the lexical detectors' candidates were cropped and put to the
    same adjudicator: **166 of 166 came back as the STORED text.** Zero yield,
    median confidence 0.98, including every candidate whose proposal was attested
    over a thousand times in an independent corpus. Lesson 49 was written from
    that result.

    A frequency argument is evidence about the language. **A human-supervised
    transcription is evidence about this page**, and it is worth 36% against 0%.
    That is the concrete, measured case for working from Sefaria's dataset rather
    than around it, and it is worth showing the Sefaria editor: his files are not a
    convenience, they are the only witness this project has ever had that finds
    real errors at a usable rate.

    ### The adjudicator's own reasoning names the defect class

    Unprompted, on the first row:

    > "The visible text is 'הנחל' followed by a superscript footnote index number
    > '1', which raw OCR misidentified as a letter 'י' ('הנחלי')."

    That is item `0ES`'s footnote-numeral class confirmed from the ink rather
    than from a pattern in the diff, and it is 67% real - by far the highest-yield
    bucket. 246 such rows exist in א-ב-ג alone.

    ### What this rate is NOT

    ### THE RATE, MEASURED THREE WAYS, AND THE FIRST TWO WERE BOTH WRONG

        first 12 per class, klal order      36.1%
        randomised, 43 of 120 (interim)     23.3%
        randomised, all 120 complete        33.3%
        POPULATION-WEIGHTED                 25.7%   <- the one to quote

    The first was a self-selected sample (Lesson 27), concentrated in the opening
    entries of aleph. The second was an interim read on a third of the run. The
    third is complete and randomised - **and still wrong as a population figure**,
    because it is STRATIFIED: 40 rows from each of three classes, when the classes
    are not equally common and the yields differ sharply.

        class              population   share    sample share   yield
        one_letter              1,116   45.3%        33.3%      22.5%
        other                   1,101   44.7%        33.3%      22.5%
        footnote_numeral          246   10.0%        33.3%      55.0%

    Equal sampling over-weighted `footnote_numeral` by 3.3x its true share, and
    it is the highest-yield class by a factor of 2.4. Weighting each class by its
    real frequency gives **25.7%**, and that projects to roughly **634 real errors
    in the 2,463-row adjudicable queue** for א-ב-ג alone.

    A stratified sample is the right way to measure the CLASSES - 40 rows each is
    what makes the per-class figures usable at all - and the wrong number to
    report as a whole. Both halves of that are the finding.

    **The comparison that matters is unchanged and is not sensitive to any of
    this**: 25.7% against the lexical detectors' 0% in item `0DU`. Every version
    of this measurement, from 23% to 36%, says the same thing about the
    difference between a human-supervised witness and a frequency argument.

    Nothing was applied. The verdicts sit in
    `~/work/hashorashim/lexical_vision_report.json`; promoting any of them into
    the corpus is a separate, deliberate step, and for this book it should wait
    for a reviewer who reads Hebrew.

0ES. **[2026-09-10] A REVIEW QUEUE THAT CAN ACTUALLY DISAGREE: 3,373 DISPUTES
    FROM SEFARIA'S DIGITIZATION, AND A 246-CASE DEFECT CLASS IN OUR OWN TEXT.**

    `tools/build_witness_disputes.py` (new) answers item `0ER`: the built-in
    generator cannot check a corpus built from the same engine, so the queue
    comes from an INDEPENDENT witness. Sefaria's dataset is the strongest one
    available - it is the only witness in this project with a human in its
    history rather than an OCR engine.

        306 shared entries, 37,538 corpus words
        3,373 disputes                    (70 are the witness's own editorial brackets)

        one_letter          1,116   33.8%
        other               1,101   33.3%
        join_split            708   21.4%   same letters, different word division
        footnote_numeral      246    7.4%
        one_side_empty        132    4.0%

    ### The footnote numerals are OUR defect and the witness found them

    246 rows where our reading is the witness's plus a trailing `י`, `יי` or
    `"י`. This edition prints reference numerals as superscripts INSIDE the line
    (`בצקו 16`), and DocAI reads them as yods glued to the preceding word:

        הנחלי  | הנחל          שרידי  | שריד
        ועוגבי | ועוגב         אבויין | אבוי

    Item `0EJ` deferred separating the footnote APPARATUS pending the Sefaria editor's files.
    This is the same problem's other half, inside the running line, and it was
    invisible to every measure taken so far - the words are plausible Hebrew, the
    lexicon accepts most of them, and no OCR witness disagrees because they all
    read the same superscript. **It took a human-supervised transcription to see
    it.** That is the concrete argument for the collaboration, and it is a
    tractable defect class rather than a scatter.

    ### What the tool deliberately does not do

    It proposes nothing and applies nothing; every row says only that two
    readings differ. Agreement is not recorded, because two sources agreeing
    tells you they agree (Lesson 25). `join_split` rows are classified and
    excluded from the reviewer-facing list - a different word division is not a
    disputed reading - and editorial insertions in the witness's brackets are
    flagged as the witness's EDITOR speaking rather than as OCR.

    **Next, not done:** route these through the vision adjudicator before any
    reach a human. Lesson 49 FREQUENCY IS NOT THIS PAGE applies with full force -
    a witness disagreeing is evidence that the position is worth looking at, not
    evidence about which reading is right, and item `0DU` measured 166 of 166
    lexically-derived hypotheses coming back as the stored text once cropped.

0ER. **[2026-09-10] THE CANDIDATE GENERATOR CANNOT DISAGREE WITH ITSELF. FOR
    THIS BOOK IT IS LESSON 25, AND THE REVIEW QUEUE HAS TO COME FROM SOMEWHERE
    ELSE.**

    `build_corrections_dataset.py` diffs **DocAI's fresh OCR against whatever the
    corpus currently stores**. For Yad Malachi that is a real comparison: the
    corpus came from an earlier extraction and has had 1,100+ human rulings
    applied, so the two genuinely differ.

    **For Sefer HaShorashim the corpus IS DocAI's output** - `build_root_corpus.py`
    builds it from the same token stream. Measured on all 346 candidates it
    produces:

        docai None (deletion)      227
        stored None (insertion)    119
        real reading difference      0

    Not one substitution, because there cannot be one. Every candidate is a
    tokenisation or line-joining artifact of the furniture filtering, not a
    disagreement about what the ink says. This is Lesson 25 A SIGNAL THAT CANNOT
    DISAGREE exactly - the check ran, produced 346 rows, and carries no
    information about the text. A reviewer worked through this queue would be
    ruling on 346 questions with no right answer in them.

    ### What the queue must be built from instead

    Three genuinely independent signals exist for this book and none is wired in:

    * **The Sefaria editor's dataset** (item `0EM`) - an independent, human-supervised
      digitization. 76.4% token agreement over 306 shared entries, so roughly
      8,700 token-level disagreements in א-ב-ג alone. This is the richest source
      and the only one with a human in its history.
    * **Cloud Vision** (item `0EH`) - measurably NOT DocAI's twin: its dominant
      error is `ו->ן` x16, which DocAI does not make, against a Books-layer
      profile that is DocAI's error-for-error.
    * **The Google Books text layer** - DocAI's twin, so a reliability gate only,
      never a vote (item `0ED`).

    **Do not fix this by loosening the existing generator.** It is doing its job
    correctly; its job is simply vacuous when the corpus and the engine are the
    same artifact. The fix is a second queue source, and it should carry which
    witness raised each dispute so a reviewer can weigh a human-supervised
    disagreement differently from an OCR one.

    Corollary worth stating for any future book: **a corpus built from engine X
    can never be checked by engine X.** The first witness a newly-ingested book
    needs is not a better version of its own extractor.

0EQ. **[2026-09-10] THE PIPELINE RUNS ON THE SECOND BOOK. 493 CANDIDATES, AND
    THREE THINGS THAT ONLY BREAK FOR A BOOK THAT ISN'T YAD MALACHI.**

    End-to-end against `~/work/hashorashim`, stage by stage:

        build_klalim_demo_dataset   307 klalim                        OK
        seed_word_identity          307 seeded, 42,646 words          OK
        build_corrections_dataset   493 candidates, 244/307 covered   OK
        build_klal_page_regions     no gematria trace                 N/A
        verify_corrections_vision   running, live Gemini calls        OK
        assemble_corrections        needs stage 3                     pending

    **39 klalim excluded as untrusted by the alignment** built in `0EP` - the
    mechanism working exactly as designed, refusing to compare OCR against a page
    whose printed root range does not bracket the entry.

    ### A MISSING INPUT REPORTED ITSELF AS A TypeError

    Two stages failed with `TypeError: 'NoneType' object is not iterable` and no
    mention of any file: `build_klal_page_regions.py` on a missing gematria trace
    and `assemble_corrections_dataset.py` on a missing stage-3 output. Both
    loaders return None for an absent file and both callers iterate it. **That is
    the first thing anyone ingesting a new book hits**, and it names nothing.
    Lesson 21's own advice - prefer a loader that raises on an unexpected shape
    over one that shrugs - applied to absence rather than shape. Both now exit
    naming the file and what produces it.

    ### Regions without a gematria marker

    `build_klal_page_regions.py` derives a klal's scan box from its marker
    position, and this book has no markers at all. But the segmentation already
    knows every line of every entry and each line carries DocAI's boxes, so the
    region is just their union per page - strictly better than deriving it from a
    single marker. `tools/build_root_corpus.py --regions` now writes
    `klal_page_regions.json` in the existing format, continuations included:
    **307 regions, 73 spanning a page break.**

    Verified against the ink rather than the count: klal 198 (root בצר, page 121)
    was drawn onto its own page image and the box lands exactly on that entry -
    from `הבית והצדי והריש. ויבצרו את כרמיהם` to the end of its text, excluding
    the catchword and the whole footnote apparatus below it.

    ### The manifest went stale the moment the corpus changed

    Rebuilding to 307 entries left `book.json` declaring `last_klal: 299`, so
    `get_part_num_for_klal(300)` returned None - which reads downstream as "that
    klal does not exist" rather than as a stale manifest. `build_root_corpus.py`
    now updates the declaration when it writes the corpus, because a number
    computable from the data should not be maintained by hand (Lesson 13).

    **Watch item, not yet run down:** the vision stage is adjudicating entry
    HEADINGS as candidate corrections - `Klal 8 page 60: 'האלף והבית והסמך' vs
    None`. A heading is corpus text here (it is the entry's `title`), so this may
    be correct, but a candidate whose stored side is None deserves a look before
    any of it reaches a reviewer.

0EP. **[2026-09-10] THE ALIGNMENT HAS A PRODUCER AT LAST. AND IT TRIED TO ROLL
    BACK THE TRANSPOSED-LEAF FIX ON YAD MALACHI.**

    `tools/build_header_alignment.py` (new) closes the second half of item
    `0EI`'s gap: `part1_header_anchored_alignment.json` had **no producer at
    all**. That is not cosmetic - `build_corrections_dataset.py` SKIPS any klal
    whose alignment is untrusted rather than compare against an unreliable page,
    so a book without this file generates no correction candidates and looks
    exactly like a clean one (Lesson 26 THE FILTER THAT HIDES).

    ### HaShorashim: 268 of 307 trusted, on a stronger anchor than Yad Malachi's

    The recto running head prints the range of roots on the spread
    (`אבח - אגד`), so the test is CONTAINMENT rather than string similarity: does
    this entry's root sort between the two bounds? That brackets the entry
    instead of naming its chapter.

    Three things were measured rather than assumed, and I got two of them wrong
    first:

    * **Which pages a range governs.** Ranges on {P} alone contain 43.3% of
      entries, {P, P-1} 43.6%, **{P, P+1} 85.3%** - a range printed on a recto
      governs that page and the verso before it. I coded `P-1` first and shipped
      a 43.6% trusted rate that looked like a data problem and was a sign error.
    * **The bounds arrive reversed.** The head is RTL and DocAI sometimes emits
      the two sides in reading order: p79 comes out `('אלל', 'אלה')`, whose end
      sorts before its start, which is impossible in print. Sorting the pair is
      safe because ascending order is a fact about the book, not a guess about
      the OCR. 85.3% -> **87.3%**.
    * **The residue is mostly garbled heads, not misplaced entries.** Of 39
      untrusted: 4 sit on chapter-opening pages that print no range at all, and
      the rest have a bound the OCR truncated (`('נה', 'בעט')` for בנה) or a root
      genuinely past the range. None of them is repaired here - untrusted means
      "do not compare against this page", which is the conservative direction.

    ### AND IT WOULD HAVE REGRESSED YAD MALACHI. CAUGHT BY --dry-run.

    The `section-header` strategy reproduces Yad Malachi's trust levels exactly -
    222 of 222, matching the migrated file - and that agreement is worthless,
    because the two files disagree about WHERE 11 klalim are:

        klalim 76-84   corpus page 37   migrated alignment page 38

    That is precisely the transposed-leaf remap. START_HERE records it: the
    alignment and the gematria trace were moved 37 -> 38, and **`part1.json`'s
    own `page` field was deliberately left untouched** because it is "already
    stale/dead metadata for most of Part 1". This tool takes `matched_page` from
    that field, so writing it would have rolled the fix back while printing
    "trusted 222 (100.0%)".

    A count that matches is not a file that matches (Lesson 33 STATE, NOT
    PRINTOUT). The tool now **refuses to write** when its pages disagree with an
    existing alignment, names the first klal that would move, and exits non-zero.
    Yad Malachi's file is untouched.

    **Open:** the `page` field is authoritative for a corpus this pipeline
    segmented - HaShorashim's page is where the heading line was actually found -
    and not for Yad Malachi. Reproducing the original forward search, which
    derived the page rather than trusting the record, is the proper fix and is
    NOT done. Until it is, Yad Malachi's alignment remains a migrated cache with
    no regenerator, and `0EI` is closed for one book of the two.

0EO. **[2026-09-10] ALL 7 MERGED ENTRIES REPAIRED. AND I ALMOST TOLD SEFARIA
    THEIR DATA HAD A HOLE IN IT THAT WAS ENTIRELY MY PARSER.**

    ### The near-miss, first, because it is the important part

    Their aleph chapter appeared to be missing its whole shin section - `אש`,
    `אשה`, `אשר`, `אשש` and the rest, ~10 roots - and I had the finding written
    up as a gap in their dataset to report back. It is not a gap.

    **They encode shin as `U+FB2A HEBREW LETTER SHIN WITH SHIN DOT`**, the
    precomposed Alphabetic-Presentation-Forms character, not `ש` plus a combining
    point. `U+FB2A` sits outside `[א-ת]` (U+05D0-U+05EA), so my headword pattern
    rejected every root containing a shin, silently, in a book where shin-final
    roots are common. `unicodedata.normalize("NFKC", ...)` decomposes it and the
    roots reappear.

        their entries   1,698  ->  1,974      (+276, all shin-bearing)
        starred         1,220  ->  1,345

    Two lessons already in the file, both mine: this was silence, not an error
    (Lesson 26 THE FILTER THAT HIDES), and I was one step from surfacing a
    "finding" about a collaborator's work that was a defect in my own reader.
    **Check your own instrument before reporting a gap in someone else's data.**

    ### And it inverted the headline comparison, which was already in a draft email

    Because their shin entries were missing, the running-text comparison was
    scoring a mutilated subset of their data. Corrected, with NFKC applied to
    both sides and - separately - the root-identifier normalisation (folding
    final letters) NO LONGER applied to running text, where it turns `אלהים`
    into `אלהימ` and costs 16 points to both sides equally:

                            first reported     corrected
        ours                    90.1%            90.3%
        theirs                  85.2%            92.0%
        token agreement         57.2%            76.4%

    **Their text is slightly BETTER than ours, not 5 points worse.** The draft to
    the Sefaria editor said the opposite and cited his own pessimism back at him as
    corroboration. Fixed before sending. The corrected figure is also the more
    useful one: two independent readings agreeing on 76% leaves a 24%
    disagreement surface, which is a review queue, not a verdict.

    ### Boundary recovery: 7 of 7, and one false positive caught by reading it

    DocAI substitutes letters INSIDE the letter name - `נון`->`גון`,
    `טית`->`מית`, `יוד`->`יור`, `למד`->`למו` - so the garbled heading is not in
    the closed vocabulary and is invisible to the matcher. Rather than add each
    garble as a variant (whack-a-mole that erodes the anchor), the boundary is
    taken from the PDF text layer, which read the same heading correctly and
    knows its page. Fuzzy selection among one page's lines is what Lesson 5
    explicitly permits; it is not a position claim.

    Three guards were each added because the version without them was wrong:

    1. **Length-matched scoring.** Comparing a 17-char heading against 40 chars
       of line diluted the ratio with body text and buried four correct
       top-ranked matches at 0.54-0.72 under a 0.75 bar. The ranking had been
       right all along; only the number was unfair.
    2. **Global assignment, not per-entry greedy.** `בהל` and `בהט` sit on p107
       with headings differing in one letter, so scoring them independently made
       them compete for each other's line and a margin test rejected both.
    3. **A line that already parses as a heading is not available.** Without it,
       `גד` was handed `הגימל והדלת הכפולה . יגדו על נפש צדיק` at 0.846 - that is
       `גדד`, a different root DocAI read correctly - which would have split
       `גדד`'s entry at the wrong place under the wrong name. **That fired, and
       was caught by reading the recovery log rather than the count.**

    Result: 307 entries, 0 flagged, 0 empty, and 306 of their 312 א-ב-ג roots
    matched - 98% boundary agreement between two independent digitizations. The
    residue is 6 roots only they have (אוי אלה בוצ בלה גבה גרב) and 1 only I have
    (אג): a short, checkable list where one side is wrong.
    **ANNOTATED 2026-09-14:** `בוצ` and `גרב` were OURS being wrong - two heading
    forms the matcher could not read (`0GG`); both are entries now.

    A fourth defect, same class as `0EL`'s: the forced-boundary path split title
    from body at the first period, and p133's garbled heading
    (`הנימל , והדלת כזרע גר`) has its only period at the line's end - one more
    empty entry. It now uses the layer heading's own length, rounded to a word
    boundary.

0EN. **[2026-09-10] EVERY LEXICON NUMBER THIS PROJECT PRODUCED FOR HASHORASHIM
    WAS 23-26 POINTS TOO LOW. THE REFERENCE CORPUS HAS NO BIBLE IN IT.**

    `sefaria_reference_corpus/` held 166 books - Talmud, Rambam, Tur, Shulchan
    Arukh, Rashi on the Talmud - and **zero of the 39 biblical books**. Checked,
    not assumed. Sefer HaShorashim is a dictionary OF THE BIBLE and quotes it on
    nearly every line, so the instrument was measuring the wrong language.

        engine / scan        old lexicon    new lexicon    change
        CloudVision  gb          67.5%         93.3%       +25.8
        CloudVision  nli         67.5%         93.6%       +26.1
        DocAI        gb          66.7%         92.2%       +25.5
        DocAI        nli         67.5%         93.5%       +26.1
        DocAI        hb          65.7%         90.9%       +25.2
        Tesseract    gb          64.6%         89.0%       +24.4
        Tesseract    nli         60.0%         83.5%       +23.5
        Dicta(Rashi) gb          62.5%         85.4%       +22.9

    Because the error was uniform across engines the COMPARISON survived - the
    ordering is unchanged - but **no absolute figure from items `0EC`, `0EG` or
    `0EH` means anything**, and anything gated on a lexicon threshold would have
    been wrong outright. That is Lesson 2 A SCORE IS NOT A CHECK arriving through
    the instrument rather than the threshold.

    ### What changed in the conclusions

    * **Cloud Vision now edges DocAI on both scans** (93.3/93.6 vs 92.2/93.5).
    * **NLI is the best input for both Google cloud engines** despite having a
      third of Google Books' pixels - 93.6 and 93.5 against 93.3 and 92.2. That
      strengthens item `0EK`'s case for asking NLI for masters: the tonal scan
      already wins at 5.8 MP.
    * Tesseract and Dicta still clearly prefer the high-resolution bitonal scan
      (89.0 vs 83.5, 85.4 vs 84.0). The split is cloud-vs-local, as `0EH` said.
    * **Ours vs the Sefaria editor's dataset moves from a 1.8-point gap to 4.9**: 90.1%
      against 85.2% over 275 shared roots, which is consistent with his own
      report that the running-text OCR fared poorly. Token agreement between the
      two is unchanged at 57.2% - a 43% disagreement surface that only the ink
      can settle.

    ### Two tools, and a latent bug in a third

    `tools/build_book_lexicon.py` (new) builds `lexicon.txt` for the CURRENT
    corpus root, reusing `validate_lexicon_independent`'s extractor rather than
    reimplementing it. Register `all` (Tanakh + rabbinic/medieval, 205 books,
    6.45M tokens, 217,841 types) is the default for this book: Tanakh alone would
    cover the quotations and mark Ibn Tibbon's own prose as errors.
    `tools/fetch_sefaria_reference_corpus.py` gained `--register`, since a
    register is a property of the BOOK, not of the script.

    **And fetching Tanakh exposed a bug that would break a fresh clone.**
    `books.json` now serves URLs ALREADY percent-encoded (`.../I%20Samuel/...`)
    where it once served literal spaces; `download()` quoted each path segment
    again, producing `%2520` and a 404. Every one of the 7 failures had a space
    in its title. **This is invisible on this machine** because all 166 rabbinic
    files were fetched before the change and `main()` skips what is on disk - so
    the corpus that half this project's validity signals rest on could not be
    rebuilt from scratch, and nothing said so. Fixed with `quote(unquote(x))`,
    idempotent for both forms; 39/39 Tanakh titles now fetch.

    **Not yet done: Yad Malachi's own lexicon is unaffected and unexamined.**
    Its register genuinely is rabbinic, so its 97-99% figures are measured with
    the right instrument. But `lexicon.txt` there is derived from the corpus
    itself and PROJECT-STATUS already records that it "cannot catch the ligature
    corruption - it contains it". Building an independent one for Yad Malachi
    with this tool is now a one-line run and has not been done.

0EM. **[2026-09-10] THE SEFARIA EDITOR'S DATASET ARRIVED. 1,698 ROOT ENTRIES WITH EXPLICIT
    MARKERS - AND IT INDEPENDENTLY CONFIRMS ALL 7 OF MY `suspect_merge` FLAGS.**

    `~/work/hashorashim/IbnJanachShorashim/` - 22 `.docx` (one per מאמר, numbered
    01-22, matching the book's 22 letter chapters exactly) plus `20a.pdf` and
    `22a.pdf`. 8.5 MB.

    ### What it is

        root entries          1,698   marked explicitly as `[אב]`, not inferred
        of those, starred     1,220   trailing `*` - meaning UNKNOWN, ask the Sefaria editor
        running text          246,348 chars (nikkud stripped)
        vocalisation          24% of Hebrew letters carry nikkud or te'amim
        per chapter           an index table of that chapter's roots (28x5 in ch.1)

    The vocalisation is the citation work he described: biblical quotations are
    pointed (`לִרְאוֹת בְּאִבֵּי הַנָּחַל`) while Ibn Janah's own prose is not, so the
    quotations are machine-separable from the commentary **by nikkud density
    alone** - no judgement, no layout heuristic. That is a better handle on the
    citation apparatus than anything this pipeline could have derived, and it is
    the reason `0EE` said to ask for it before duplicating the work.

    Their entry markers are also structurally better than mine: `[אב]` is
    explicit and not OCR-derived, where my `tools/detect_root_entries.py` infers
    the root from spelled-out letter names in an OCR stream and can lose one when
    the OCR garbles it (item `0EJ`).

    Two format details cost me a wrong first count of 424: entries can carry a
    trailing `*`, and shin is written with its dot INSIDE the brackets
    (`[אישׁ]`), so a naive `\[([א-ת]+)\]$` misses 1,274 of 1,698. Also **they
    write roots with FINAL letter forms** (`אבך`, `אבן`) where this pipeline uses
    non-final (`אבכ`, `אבנ`); comparing without normalising makes 78 of 275
    genuine matches look like disagreements.

    ### 7 OF 7. THE CROSS-CHECK FLAGS WERE REAL.

    Item `0EJ` flagged 8 headings the PDF text layer found and DocAI missed, and
    warned they were a MERGE defect rather than an absence - the next root's text
    running on into the previous entry with no boundary. Their dataset, built
    independently of both of my OCR sources, lists every one of the 7 that fall
    in א-ב-ג as a real entry:

        אינ אמצ בהט בהל גד גדפ גמצ

    That is third-party confirmation that the flags were not false alarms, and it
    means 7 entries in `part1.json` are currently merged and need splitting.

    ### The running text: a 43% adjudication surface, and NO verdict yet

        275 shared roots        mine 33,645 tokens   theirs 32,420 tokens
        lexicon hit             mine 62.0%           theirs 60.2%
        token-sequence agreement between the two:    57.2%

    **Do not read the 1.8-point gap as "ours is better".** The lexicon is Yad
    Malachi's rabbinic vocabulary and this is biblical lexicography, so it is the
    wrong instrument for both sides equally (Lesson 49's shape - a frequency
    argument is evidence about the language, not about this page). Their text
    also carries editorial insertions in brackets (`ומקום [י]צמח`) that count as
    divergences without being errors.

    What IS established is the size of the disagreement: the two readings differ
    on ~43% of tokens across 275 entries. That is a large, real adjudication
    surface and it is exactly what this pipeline exists to resolve - which is the
    concrete form of the division of labour `0EE` proposed. Settling who is right
    needs the ink, not either lexicon.

    **Open:** what does the trailing `*` mark on 1,220 of 1,698 entries? Ask
    before assuming; it is on 72% of entries, so guessing wrong would be costly.

0EL. **[2026-09-09] THE PAGE RENDERER EXISTS AT LAST - AND BUILDING IT FOUND
    THREE DEFECTS IN WORK I HAD JUST SHIPPED.**

    `tools/render_pdf_pages.py` (new) closes half of item `0EI`'s gap:
    `images/pdf_pages/` had **no generator at all** since the project began
    (START_HERE: "has no live rendering script at all... must be migrated as a
    pre-built cache"), which is survivable for one book and blocking for a
    second. 94 HaShorashim pages rendered and verified.

    **It reproduces Yad Malachi's migrated cache byte-for-byte** - pages 99, 100
    and 101 at pixel correlation r=1.0000 - so the gap is closed for both books,
    not just the new one. That was NOT true of the first version, and the
    difference is the finding: the migrated cache renders at a constant zoom of
    **2.0833 = exactly 150 DPI**, while I had written a fixed 864px WIDTH. Those
    agree only where the mediabox happens to match; Yad Malachi's varies page to
    page (856/860/864 px at 150 DPI), so page 100 matched exactly and 99 and 101
    silently rescaled. Measured, not assumed - and it is Lesson 30's shape again,
    since a rescaled page is still legible Hebrew.

    ### The verifier had to be fixed twice before it could be believed

    1. It compared the PDF text layer against DocAI tokens WITHOUT accounting for
       reading order, so a visual-order layer failed on every page: **94 of 94
       "wrong page" against a correct render.** It now scores both orders and
       keeps the better, because the question is page IDENTITY and reading order
       is irrelevant to it.
    2. It then reported `0.0%` for Yad Malachi, whose layer holds no Hebrew at
       all (item `0ED`'s Quartz-stripped skeleton). That is **cannot verify**,
       not failure, and reporting it as failure would flag every correct page of
       the deliverable book. It now returns None and says so.

    Both were caught only because the check fired on data I knew was right.

    ### AND THE CORPUS I SHIPPED AN HOUR AGO HAD PAGE FURNITURE IN IT

    Item `0EJ` claimed the page separates cleanly by line height. That is true of
    the FOOTNOTE APPARATUS and false of the RUNNING HEADS. This book sets two
    kinds: the verso `73 ספר השרשים` in small type, which the height rule caught,
    and the recto root-range `בצק - בקר 73` **in full-size type**, measured at
    0.90-1.08x the page median - indistinguishable from body by height.

        running-head lines wrongly kept as body:   32
        entries contaminated:                      30 of 299   (10%)

    That is Yad Malachi's item 20 page-furniture class, reproduced on day one of
    a new book, by me, in the same session that wrote the tool. Running heads are
    now matched by CONTENT at the top of the page rather than by size: 95 head
    lines dropped, contamination re-measured at **0 of 299**.

    ### And a second defect in the same build: comma-terminated headings

    `segment()` split title from body at `text.find(".")`, but headings terminate
    with a period OR a comma. A comma-terminated heading therefore swallowed its
    entire entry into the title, leaving the text empty - `האלף והנימל , אבל זה
    הוא...` kept everything. **8 entries were empty and 14 were under 20
    characters.** `detect_root_entries.match_heading()` now returns the match
    SPAN and the split uses the heading's own terminator.

        before   14 entries < 20 chars, 8 of them empty, 196,213 chars total
        after     5 entries < 20 chars, none empty,      199,145 chars total

    The surviving 5 were checked individually and are genuine one-line entries
    (`בהק הוא פרח בעור .`, `גרן ויקב .`), not defects.

    ### State

    299 entries, 199,145 characters, no furniture, no empty entries. 543 tests
    pass. Still open from `0EI`: `part1_header_anchored_alignment.json`, which
    has no producer. The running heads are the natural anchor for it and the
    recto ones carry ROOT RANGES (`ברא - ברה`), which bracket the entries on the
    page - a stronger signal than Yad Malachi's single section letter, and now
    reliably extracted as a side effect of the furniture fix.

0EK. **[2026-09-09] EVERY SCAN THIS PROJECT HAS EVER USED IS 1-BIT. INCLUDING
    YAD MALACHI'S. THE NLI REJECTION WAS DECIDED ON AN AXIS THAT OMITTED IT.**

    Reviewer is in contact with someone at the NLI and asked whether to request
    their highest-resolution scans of both books. Measured first.

        berlin_square_corrected.pdf   3448 x 5312   18.3 MP   1 bpc PNG
        HaShorashim Google Books      3522 x 5278   18.6 MP   1 bpc PNG
        HaShorashim HebrewBooks       2163 x 3351    7.3 MP   1 bpc PNG
        HaShorashim NLI (anonymous)   2004 x 2892    5.8 MP   24-bit RGB

    **Yad Malachi's scan is bitonal too.** START_HERE's resolution figure for it
    is correct - 3440x5312, confirmed over 30 sampled body pages - but the file
    is 1 bit per pixel and nothing in this repo says so. Its NLI comparison table
    ranks the two sources on pixel count and lossy-vs-lossless and **never on bit
    depth**, so the 2026-08-18 decision to reject NLI was made without the axis
    on which NLI actually wins.

    (My own first measurement of this said 2213x2750 / 9.1 MP. That was wrong: I
    averaged the page image together with the 1034x204 "Digitized by Google"
    watermark strip, which is also >500px wide. Taking the LARGEST image per page
    gives 18.3 MP. Recorded because the wrong number would have argued for
    exactly the same conclusion by a false route.)

    ### Why this matters more than resolution

    Thresholding is irreversible and it happens upstream of every engine. So no
    measurement this project has ever made could distinguish a WORN sort from a
    faint one - the evidence was destroyed at capture, before DocAI, Surya, the
    VLM or Dicta ever saw it.

    That is Lesson 24 SHARED INK, SHARED ERROR's actual mechanism, and item `24`
    records the measured dead end: enumerating and excluding the known artifact
    barely improved the ensemble (41% -> 39%), so "a bigger artifact catalogue is
    not the repair". **Continuous tone is a different lever, and it is the only
    one not yet tried.** 37 identical wrong readings across three engines came
    from one alef-lamed sort; a grey image is what tells a vision adjudicator
    whether the ל is absent or merely light.

    Corroborating, measured today on HaShorashim: the two bitonal copies fail in
    OPPOSITE directions - Google merges adjacent letters, HebrewBooks breaks
    strokes within them - and the continuous-tone copy is what adjudicates
    between them. But at 5.8 MP that arbiter is resolution-limited. A master file
    would be the first source that is both high-resolution AND continuous tone.

    ### What to ask for, and the one that decides it

    NLI system numbers: Yad Malachi `990011859020205171`, HaShorashim
    `990010892830205171`. Ask for the **preservation masters**, not the web
    derivatives, and ask for the SPEC BEFORE the files - DPI, bit depth, colour
    space. If the masters are also bitonal there is nothing to gain and the
    logistics stop there. Also ask the redistribution terms: START_HERE already
    notes NLI sourcing sidesteps Google Books' terms of use, and Sefaria is the
    destination.

    ### It does NOT have to become the primary, and that is the cheap path

    Every page-indexed cache is keyed to one PDF's numbering - `docai_word_boxes/`,
    `images/pdf_pages/`, the alignments, and Yad Malachi's own `page` fields.
    Switching primary means rebuilding all of them, and the NLI copies do not
    even share page ORDER (HaShorashim's roman introduction is bound at the back;
    NLI's Yad Malachi PDF is 336 pages against Google's 337).

    So use it as the **adjudication source only** - the image the vision
    adjudicator crops from - while OCR continues on the existing scan. That
    captures the entire benefit, which is a tonal image at the moment of human or
    model judgement, and costs no cache migration. Mapping between them is by
    PRINTED PAGE NUMBER, never image index (item `0EC`).

0EJ. **[2026-09-09] THE א-ב-ג CORPUS EXISTS: 299 ENTRIES, 196,213 CHARACTERS,
    LOADING THROUGH THE SEAM. AND THE TWO OCRs DISAGREE ABOUT 8 HEADINGS, WHICH
    IS A MERGE DEFECT, NOT A MISSING ONE.**

    `tools/build_root_corpus.py` (new). DocAI token stream -> lines -> classified
    -> split at headings -> `part1.json`. Built over PDF pages 58-151.

        lines kept      3,119 body
        lines dropped   62 running head, 633 apparatus, 108 watermark
        entries         299
        characters      196,213
        median entry    358 chars

    ### The footnote apparatus separates GEOMETRICALLY, so deferring it cost nothing

    Sefaria named footnotes explicitly and item `0EE` defers the editorial work
    pending the Sefaria editor's dataset - but FINDING the apparatus needs no judgement, only
    the bounding boxes DocAI already returns. Measured on PDF page 121:

        line 0      y 0.072  h 0.0127   `72 ספר השרשים`        running head
        lines 1-32  y 0.105  h 0.0176-0.0213                    BODY
        line 33     y 0.790  h 0.0123   `לב וישטפני .`          catchword
        lines 34-39 y 0.813  h 0.0102-0.0127                    APPARATUS
        line 40     y 0.959  h 0.0237   `Google by Digitized`   watermark

    Body type ~0.019, apparatus type ~0.011 - a 1.7x gap. **Token height alone
    does not work and was tried first:** a short word like `מה` has a smaller box
    for want of ascenders whatever its type size, so 29-31% of tokens read as
    "small" scattered through the body. The signal is only clean once tokens are
    clustered into LINES. The threshold is the PER-PAGE median, not a constant,
    because page images vary 10-20% in size.

    ### The heading anchor was too strict, and the DocAI stream proved it

    First build found 287 headings against the text layer's 308. Diagnosed rather
    than patched: the headings ARE present and ARE line-initial, but the line
    opens with a footnote numeral or a bracket that the two OCRs place
    differently -

        p59    17 האלף והבית והכף . ויתאבכו גאות עשן
        p109   88 הבית והזין הכפולה , בחזו להם ישראל
        p146   [ הנימל והעין וההא , יגעה שור

    `^\s*ה` rejected all of them. Widened to "the first HEBREW letter on the line
    must open the heading", which keeps the anchor's strength - terminator still
    required, letter-name vocabulary still closed - and recovered 12. Full-book
    count moved 1,873 -> 1,876.

    ### THE REMAINING 8 ARE A MERGE DEFECT AND ARE FLAGGED IN THE CORPUS

        only in the text layer:  אינ איש אמצ בהט בהל גד גדפ גמצ
        only in DocAI:           none

    Seven of them DocAI simply does not contain (`והיוד והנון`, `והמם והצרי`,
    `וההא והטית`... all absent from its token stream), so DocAI misread those
    heading lines - the reverse of the general pattern. `בכה` is the other
    direction: the text layer detected it TWICE on p112, a false positive of its
    own.

    **A missed heading does not produce a missing entry - it produces a silently
    MERGED one**, where the next root's text runs on with no boundary. That is
    worse than an absence and nothing else in this pipeline would surface it, so
    `--cross-check` writes `suspect_merge` onto the affected records: **20 entries
    flagged** (the flag is per-PAGE, so it is a deliberate superset of the 8 -
    safe, not precise). These are the first real disputes this book has, and they
    are structural rather than lexical, which is a good thing to have in front of
    a reviewer at a demo.

    ### State

    `~/work/hashorashim/` is now a git repo (scans, caches, dicta samples and the
    email draft gitignored; `book.json`, `README.md`, `part1.json`,
    `root_entries.json` and the engine comparison tracked). `book.json` declares
    `parts` 1-299 and `scan_pdf`. Verified through the seam:
    `SEFER_CORPUS_ROOT=~/work/hashorashim` loads 299 klalim, resolves the right
    scan, and reports `PART1_MAX_KLAL 299`.

    **Still needed before the dashboard can open it:** `images/pdf_pages/` (no
    renderer exists) and `part1_header_anchored_alignment.json` (no producer
    exists) - both from item `0EI`.

0EI. **[2026-09-09] THE SEAM DID NOT CARRY THE SCAN. AND THE BYPASS GUARD
    CAUGHT MY OWN THREE NEW TOOLS.**

    Reviewer: "is there also code work needed on the seam to injest a new text?"
    Audited rather than estimated. Yes, and it was the one artifact that matters
    most on the vision path.

    ### The scan filename was a literal in six live files

    `pipeline/verify_corrections_vision.py:83-84`, `rebuild_all.sh` stage 3, the
    stage that crops every disputed word out of the scan:

        REPO = cio.REPO
        PDF_PATH = os.path.join(REPO, "berlin_square_corrected.pdf")

    `cio.REPO` IS the seam, so the DIRECTORY followed the corpus root and the
    FILENAME did not. A second book therefore got a path pointing at its own root
    with the first book's filename on the end - a missing file rather than a
    crop of the wrong book, which is luck, not design. Same literal in
    `build_gematria_trace.py` (there at least behind an overridable `--pdf`),
    `verify_witness_vision.py`, `verify_witness_green_vision.py`,
    `run_surya_part1_full_baseline.py`, `verify_local_setup.py`.

    Compounding it, `PDF_PATH` was a module-level assignment, so it froze at
    import - item `0DC`'s class ("26 more freeze their paths at import, four of
    them rebuild stages"), and precisely the defect corpus_io's PEP 562
    `__getattr__` exists to prevent, reintroduced one level up.

    **Fixed:** `scan_pdf` is now a `book.json` identity field with
    `cio.SCAN_PDF_PATH` resolving it at call time, and the adjudicator reads it
    through a function (`pdf_path()`), never a module constant. Under the strict
    rule from `0EC`, a corpus root with a book.json must now DECLARE its scan or
    raise - a second book cannot silently inherit this one's. The other five
    files still carry the literal and are not yet swept.

    ### THE BYPASS GUARD CAUGHT ME

    `test_the_corpus_root_bypass_count_has_not_grown` failed on my own three new
    tools - `extract_pdf_text_layer.py`, `gate_docai_against_layer.py`,
    `detect_root_entries.py` - all three of which had copy-pasted
    `REPO = os.path.dirname(HERE)`, which is exactly what that guard's docstring
    predicts ("the single easiest thing to paste from a sibling file"). The
    correct response was to route them through corpus_io, not to bump
    `KNOWN_BYPASS_COUNT`; done, and 543 tests pass. Worth recording that the
    guard works and that it caught the person who had just been writing about
    seams.

    ### What ELSE a second book needs that no code can produce

    Checked by grepping for WRITERS, not readers:

    * **`part1_header_anchored_alignment.json` has no producer at all.** Nothing
      in `pipeline/` or `tools/` writes it; it is a migrated cache. It is what
      maps a klal to its scan page, and `build_corrections_dataset.py` skips any
      klal whose alignment is untrusted - so without it a second book generates
      no candidates. For HaShorashim the mechanism is actually EASIER: odd pages
      carry root-range running heads (`אבה - אגד`) which bracket the entries on
      the page, a stronger anchor than Yad Malachi's single section letter.
    * **`images/pdf_pages/page_N.png` has no renderer** - START_HERE already says
      so. Small job, genuinely absent.

    ### א ב ג slice, scoped and extracted

    Reviewer chose the first three מאמרים for the demo. **308 entries** (א 132,
    ב 90, ג 86), PDF pages 58-151, printed 10-103. DocAI extracted over all 94
    pages into `~/work/hashorashim/docai_word_boxes/`; `page_121.json` opens
    `72 / ספר / השרשים`, confirming the +48 offset against the token stream
    rather than against the rendered header alone.

    Footnote work is deliberately DEFERRED pending the Sefaria editor's dataset (item `0EE`).

0EH. **[2026-09-09] CLOUD VISION IS *NOT* DOCAI'S TWIN - THE BOOKS LAYER IS.
    97.4% ON YAD MALACHI, AND ITS DOMINANT ERROR IS ITS OWN. DRIVE HEADLESS
    CONVERSION IS BLOCKED.**

    Reviewer directive: try Cloud Vision and the Drive headless conversion on
    both books. `google-cloud-vision` installed;
    `document_text_detection` with `language_hints=["he"]`.

    ### Yad Malachi, klalim 13-23, scored against the corpus

        Cloud Vision (DOC_TEXT)   4180 tok   97.4%   lex 97.8%
        Google Books layer        4159 tok   97.2%   lex 97.6%
        DocAI (primary)           2489 tok   98.6%   lex 99.1%
        Dicta (square)            2491 tok   78.1%   lex 83.4%
        corpus (ceiling)          2253 tok  100.0%   lex 99.7%

    (Vision and the Books layer are flagged non-comparable on CER: both were
    extracted over whole pages against an 11-klal window, so the overhang counts
    as insertions. Word accuracy divides by the reference and is unaffected.)

    ### THE SUBSTITUTION PROFILES SPLIT THE THREE GOOGLE ENGINES IN TWO

        Cloud Vision   ו->ן x16,  ∅->י x5,  ב->כ x4,  ה->ח x3,  ∅->יי x3,  ד->ו x3
        Books layer    ה->ח x6,   ∅->י x4,  ∅->יי x4, כ->ב x3,  ם->ס x2,   ן->ו x2
        DocAI          ה->ח x6,   ∅->יי x4, ∅->י x4,  ב->כ x3,  מ->ט x2,   ת->ר x2

    **This refines item `0ED`, which assumed the Google engines were one family.**
    The Books layer IS DocAI's twin - same error, same count, on the top four.
    Cloud Vision is not: its dominant failure is **ו->ן, sixteen times**, more
    than double any error it shares with DocAI, and the Books layer shows the
    OPPOSITE substitution (ן->ו x2). The letter-frequency signature agrees -
    Cloud Vision over-produces nun at 1.11x where the Books layer over-produces
    shin at 1.10x.

    So Cloud Vision carries genuinely independent signal on its dominant error
    class while sharing the secondary ones. It is a better witness candidate than
    the Books layer, and **ו->ן at word-final position is a systematic,
    lexicon-checkable error class** - cheap to post-correct, which would raise it
    further. Neither is yet wired to anything.

    ### HaShorashim, printed pages 71-76, reference-free

        engine                 GB      NLI     agrees w/ DocAI (GB / NLI)
        Cloud Vision         67.5%   67.5%        90.4%  /  94.0%
        DocAI                66.7%   67.5%          -    /    -
        Tesseract            64.6%   60.0%        86.7%  /  72.6%
        Dicta (Rashi model)  62.5%   61.3%        82.3%  /  72.2%

    **Corrects `0EG`'s "DocAI is the only engine indifferent to the
    continuous-tone scan":** Cloud Vision is equally indifferent (67.5% on both).
    The split is not DocAI-vs-rest, it is **cloud-vs-local** - both Google cloud
    engines read the 5.8 MP colour scan as well as the 19 MP bitonal one, while
    Tesseract and Dicta both drop sharply on it. The argument for Google Books as
    primary now rests on the two engines that are NOT scan-indifferent.

    ### Drive headless conversion: blocked, and the fallback is not worth it

        HttpError 403: "Google Drive API has not been used in project
        1045375753125 before or it is disabled."

    Enabling it is a console action only the reviewer can take. Even then a
    service account typically has no Drive storage quota outside a Workspace
    domain, so a second failure is likely - worth one retry, not a plan.

    The claude.ai Drive connector WOULD work (`create_file` accepts
    `base64Content` and converts image uploads to a Google Doc by default), but
    the image has to pass through the conversation as base64: **~170k tokens for
    a single page**, and it lands scans in the reviewer's personal Drive. Not a
    viable comparison harness. Expected value is low regardless - the Drive
    converter is very likely the same Google OCR family the Books layer already
    represents, and that one is already measured as DocAI's twin.

0EG. **[2026-09-09] THE HEBREWBOOKS TITLE PAGE SETTLES PROVENANCE AND
    CORRECTS MY PUBLISHER CALL. AND DICTA'S *RASHI* READER DOES FAR BETTER ON
    SQUARE TYPE THAN I PREDICTED.**

    ### Provenance, read off the ink

    The HebrewBooks copy carries an oval ownership stamp on its first page:
    `ספרית אגודת חסידי חב"ד / אהל [יוסף] יצחק / ליובאוויטש / ארה"ב` - the
    Chabad-Lubavitch library. Reviewer had said "Chabad"; it is now verified from
    the image rather than taken on report. So the three exemplars are Ohio State
    (Google Books, bookplate at 0-idx 1), Chabad-Lubavitch (HebrewBooks), and
    NLI's own copy (accession stamp `26 AUG 1927`).

    ### I WAS WRONG TO DISMISS GOOGLE'S "A. BERLINER"

    Item `0EC` recorded `publisher: "Itzkowski, for Mekize Nirdamim"` and said
    Google Books "lists A. Berliner, who was one of the Mekize Nirdamim heads,
    not the press" - i.e. that Google had it wrong. The German title page, which
    the HebrewBooks copy reproduces and which I had not read, says:

        BERLIN 1896.
        Herausgegeben im Selbstverlage des Vereins M'KIZE NIRDAMIM.
        (Dr. A. Berliner.)
        In Commission bei J. Kauffmann, Frankfurt a. M.

    So the volume is the society's OWN imprint with Berliner named as the
    responsible editor, Kauffmann the commission agent, and Itzkowski only the
    printer (from the Hebrew title page). Google's attribution is defensible and
    mine was the narrower reading. `book.json` now says
    `"Mekize Nirdamim (Selbstverlag), printed by Itzkowski, Berlin"`, which is
    what ships in the TEI sourceDesc.

    ### Dicta, measured instead of predicted

    Item `0EC` said Dicta "does not earn its place here on the evidence this
    project already has" - reasoning from Yad Malachi, where Dicta's SQUARE model
    scored 77.6% against DocAI's 99.0%. **The reviewer pushed back ("it can't
    hurt to try"), and was right to.** Dicta square access is not available to
    this project (support has been asked); the RASHI reader was run instead, on
    the same six pages (printed 71-76) already carrying DocAI and Tesseract
    baselines:

                              tokens   types   lex hit   agrees with DocAI
        DocAI          GB       2966    1493     66.7%          -
        DocAI          NLI      2972    1466     67.5%          -
        Dicta(Rashi)   GB       2983    1587     62.5%        82.3%
        Dicta(Rashi)   NLI      3078    1709     61.3%        72.2%

    A model for the WRONG SCRIPT lands 4.2 points behind DocAI on this book,
    where the right-script model landed 15.7 points behind on Yad Malachi. Its
    output is fluent and it reads the structural headings correctly, including
    the `רש` spelling that broke my own detector: `הבית והעין והרש.` = בער,
    followed by `כי בערה בם אש י"י`. **The square model is now worth chasing
    rather than written off**, and the ask to Dicta support is the right move.

    Two caveats. Lexicon hit rate is a weak proxy and cannot say who is RIGHT
    where they differ - 82.3% agreement with DocAI leaves ~18% needing
    adjudication. And the rates are not comparable across books: 62.5% here
    against 83.4% on Yad Malachi reflects different vocabulary, not a worse read.

    ### A pattern across three engines now

    **DocAI is the only engine tested that reads the continuous-tone NLI scan as
    well as the 19 MP bitonal one.** Tesseract strongly prefers Google Books
    (11.1% vs 24.5% idiosyncratic-reading rate) and so does Dicta (82.3% vs 72.2%
    agreement, 62.5% vs 61.3% lexicon hit). Two independent engines both prefer
    the high-resolution bitonal input; only DocAI is indifferent. That is an
    argument for Google Books as primary that does not depend on DocAI's own
    preference, and it strengthens `0EC`'s conclusion by a route `0EC` did not
    have.

0EF. **[2026-09-09] ENTRY SEGMENTATION FOR HASHORASHIM: 1,873 ROOT ENTRIES,
    VALIDATED BY THE BOOK'S OWN ALPHABET TO 2 UNEXPLAINED PAIRS IN 1,872. AND A
    HAND-WRITTEN LETTER LIST THAT SILENTLY LOST A WHOLE מאמר.**

    `tools/detect_root_entries.py` (new). This book has no gematria marker, so
    `build_gematria_trace.py` has no analogue; what it has instead is every entry
    headed by its root SPELLED OUT AS LETTER NAMES and closed by a period or
    comma - `הבית והצדי והקוף.` = ב-צ-ק. Run over the recovered Google Books
    layer (`tools/extract_pdf_text_layer.py`, 1,094,298 Hebrew chars over 636
    pages, no API cost).

        entry headings          1,873
        root lengths            2 letters 125, 3 letters 1,748
        initials covered        21 of 22

    ### THE FIRST VERSION FOUND 840 AND THE GUARD DID NOT NOTICE

    I wrote the 22 letter names from knowledge of the alphabet. The edition
    prints resh as **`רש`**, not `ריש`, so **the entire ר מאמר - 30 pages, PDF
    509-538 - came back empty**, and the same list missed `חת`, `טת`, `ואו` and
    the geminate formula `כפולה` ("the doubled one", 152 occurrences, repeating
    the preceding letter: `הרש וההא הכפולה` = ר-ה-ה). 1,033 entries missing, 55%
    of the true total.

    **The alphabetical-order check reported 1 violation in 839 and was clean.**
    It could not see this: a whole missing section produces no local inversion,
    because ק -> ש is still forward. Lesson 26 THE FILTER THAT HIDES, in the
    guard rather than in the data - the failure was silence, and I was reading a
    99.9% pass as coverage when it was only monotonicity. What caught it was a
    coverage check the tool did not have: **entries per initial letter, where
    ר:0 and ו:0 are impossible on their face.** That check is in it now and runs
    by default.

    The vocabulary is no longer hand-written. It was rediscovered by clustering
    every line-initial heading-SHAPED line in the layer and reading off the words
    that actually occupy the slots - 1,987 such lines, head-words ranked, so a
    spelling the edition uses cannot be missed by my not knowing it.

    ### The order check, once geminate collation is accounted for

        adjacent pairs                          1,872
        order violations                          119   6.4%
          explained by geminate / 2-letter collation 117   98% of violations
          UNEXPLAINED                                 2   0.11% of all pairs

    The edition does not collate geminate roots where naive alphabetical order
    puts them (`בב` precedes `באר`, `ארר` precedes `ארב`), so 117 of the 119 are
    my sorting model being wrong, not the detector. **The 2 that remain are real
    and need a human against the ink:**

        p237  יגר -> יגע    היוד והנימל והעין.
        p591  תחש -> תחר    התו והחת והרש.

    ### ו:0 is CORRECT, and was checked rather than assumed

    Hebrew roots essentially do not begin with vav, so a missing ו מאמר is
    expected - but "expected" is not measured. Confirmed structurally: **2 pages
    separate the last ה entry (p173) from the first ז entry (p176)**, so the book
    has no ו section to miss.

    Artifact: `~/work/hashorashim/root_entries.json`. **Not yet a corpus** - these
    are headings with page and line, not segmented entry TEXT, and they are
    derived from Google OCR, so every heading is as good as that OCR. Building
    `part*.json` from them, and declaring the 22 מאמרים in `book.json`'s `parts`,
    is the next step.

0EE. **[2026-09-09, reviewer] THIS IS NOT A SECOND BOOK WE CHOSE. SEFARIA IS
    ALREADY WORKING ON IT, THEY HAVE A DATASET WE DO NOT HAVE, AND THERE IS A
    MEETING NEXT WEEK.**

    From the Sefaria editor, forwarded by the reviewer 2026-09-09, in summary:
    he agreed to both requests; his current project is Sefer HaShorashim of Ibn
    Janah; **Sefaria received a digitized dataset with careful attention to
    citations but weak OCR of the running text**; and he wants to try the model,
    test its fidelity, and compare its review dashboard with traditional OCR
    software, meeting the following week.

    ### What this changes

    START_HERE's Part 1 says Sefaria is the customer and their requirements
    outrank this project's preferences. Items `0EC`/`0ED` were written as though
    HaShorashim were a second book this project picked up. It is not. It is **the
    customer's live project**, and the ask is explicitly to test this pipeline's
    FIDELITY and its REVIEW DASHBOARD against it.

    * **Their dataset is the thing to get, and we do not have it.** Careful
      citations, poor running-text OCR is the exact complement of what this
      pipeline produces. Bacher's `מראה מקומות` apparatus is the hard part of
      this book structurally - it is `0DB-TODO`'s footnote class arriving much
      larger (item `0EC`) - and someone has already done it carefully. Asking for
      it is the highest-value action available and costs one email.
    * **The deliverable is a demonstration, not just a text.** "Testing its
      fidelity" and "experimenting with its review dashboard" means the dashboard
      has to LOAD this book. That needs real `part*.json` content, which needs
      entry segmentation on the letter-name formula (`הבית והצדי והריש` = בצר,
      item `0EC`). That is now the critical path, not the scan question.
    * **He named the same NLI scan** (`/he/` locale of the record already
      downloaded), so source selection is aligned - and we have a measurement he
      probably does not: NLI's Maximal is **5.8 MP against Google Books' 19 MP**
      (item `0EC`), and DocAI nonetheless reads them equally well. Worth telling
      him rather than letting him assume the library scan is the best input.
    * **"Comparing it with traditional OCR software"** is the comparison item
      `0EC` already ran on three scans and two engines. That artifact
      (`ocr_engine_comparison_three_scans.json`) was built for us and is directly
      the thing he says he wants to do.

    ### The Yad Malachi gate is a live demo asset, not just housekeeping

    Item `0ED` recovered a free full-corpus OCR layer nobody had read and turned
    it into a reliability gate. On a call about "testing fidelity", that is a
    concrete demonstration of the method: a witness recovered, measured at 97.2%,
    and then DECLINED as a vote because its errors are DocAI's. The declining is
    the part worth showing.

    **Open, in priority order:** (1) ask the Sefaria editor for the digitized dataset and its
    provenance/licence; (2) entry segmentation so the dashboard can load the
    book; (3) tell him the scan measurements before he commits to NLI as primary.

0ED. **[2026-09-09, reviewer question] "WAS THERE A SECOND GOOGLE OCR WE USED
    FOR YAD MALACHI?" NO - AND THE ONE THAT EXISTED WAS STRIPPED OUT BY A PDF
    RE-SAVE. IT SCORES 97.2%, AND IT IS DOCAI'S TWIN.**

    ### It was never used, and it could not have been

    Nothing in this repo has ever read a PDF text layer: `get_text(` appears
    **zero times** across `pipeline/`, `tools/` and `tests/`. The only "text
    layer" mentions in the status files are item `0EC`'s, written today about
    Sefer HaShorashim.

    Nor could it be, from the files the pipeline uses. Measured across all 337
    pages:

        berlin_square_corrected.pdf              pages WITH HEBREW   0   chars        0
        berlin_square_original_transposed.pdf    pages WITH HEBREW   0   chars        0
        ~/Downloads/ספר_יד_מלאכי Berlin.pdf       pages WITH HEBREW 332   chars  1,005,824

    Both repo PDFs report 334 of 337 pages as having "text", which is what a
    naive check sees - and every one of those pages holds **only whitespace**
    plus the English "Digitized by Google" disclaimer. Their producer string is
    `macOS Version 26.6 Quartz`; the original download's is `Google Books PDF
    Converter`. **A re-save through Quartz kept the layer's whitespace skeleton
    and threw away every Hebrew character** - about a million of them, covering
    essentially the whole book - and nothing noticed, because nothing reads it.
    The original is still on disk and the loss is fully recoverable.

    ### What it is worth: 97.2%, second only to DocAI

    Extracted from the original download for 0-idx pages 17-21 (whole-line
    reversal - the layer is in VISUAL order, same as HaShorashim's) and scored
    with `tools/compare_ocr_engines.py --klalim 13-23`, which works here because
    Yad Malachi HAS a reference corpus:

        Google Books text layer   4159 tok   97.2%   lex 97.6%
        DocAI (primary)           2489 tok   98.6%   lex 99.1%
        Dicta (square)            2491 tok   78.1%   lex 83.4%
        corpus (ceiling)          2253 tok  100.0%   lex 99.7%

    Its CER is flagged and NOT comparable - I extracted five whole pages against
    an 11-klal window, so 85% of its tokens are overhang the CER counts as
    insertions. Word accuracy divides by the reference and is unaffected.

    ### AND IT IS NOT AN INDEPENDENT WITNESS. Read the substitutions.

        Google Books layer:  ה->ח x6,  ∅->י x4,  ∅->יי x4,  כ->ב x3,  ם->ס x2
        DocAI (primary):     ה->ח x6,  ∅->יי x4, ∅->י x4,   ב->כ x3,  מ->ט x2

    Same error, same count, on the top four. Two Google OCR systems reading the
    same ink fail the same way - Lesson 24 SHARED INK, SHARED ERROR compounded by
    Lesson 23 AN ENGINE, NOT A SAMPLE. **Do not count it as a vote.** Its correct
    use is Lesson 23's own prescription for a repeat run: a RELIABILITY GATE on
    DocAI - where the two Google readings diverge, DocAI is less certain and the
    position deserves a look; where they agree, that agreement carries almost no
    information beyond DocAI's own confidence.

    That is a genuinely useful thing to have for free on a book whose open work
    is closing disputes, and it is cheap: no API, no key, no cost, full corpus.
    But it must be wired in as a gate, not as a third engine in a consensus vote,
    or it will manufacture false 2-of-3 agreement on exactly the glyphs DocAI
    already gets wrong.

    ### Transfers to HaShorashim

    Its Google Books PDF carries 636 Hebrew pages / 1,094,298 characters
    (item `0EC`). Same relationship must be assumed there: that layer is DocAI's
    sibling, not a second opinion, until measured otherwise - and it cannot be
    measured there yet, because that book has no reference corpus.

    ### DONE, same turn - and the remap I prescribed turned out to be WRONG

    `tools/extract_pdf_text_layer.py` (new, generic, both books) recovers a
    scanned PDF's embedded layer one file per page. `--report` counts HEBREW
    characters rather than non-blank text, because that is exactly the check that
    would have caught this years earlier: the stripped PDFs report 334 of 337
    pages as "having text" and hold only whitespace. It exits non-zero on them.

    **Reading order is DETECTED, not assumed** - `--order detect` scores both
    readings against the lexicon and says which it chose. On this file: as-is
    18.6% vs reversed 93.3%, so VISUAL. HaShorashim's HebrewBooks PDF is the
    opposite convention, so guessing would silently mirror one of them.

    **The transposed-leaf remap is NOT needed and my instruction to apply it was
    wrong.** `~/Downloads/ספר_יד_מלאכי Berlin.pdf` is already in the CORRECTED
    page order: its 0-idx pages 36 and 37 are pixel-identical (r=1.000) to
    `berlin_square_corrected.pdf`'s 36 and 37, and to
    `berlin_square_original_transposed.pdf`'s 37 and 36. Independently confirmed
    by content: extracted page N overlaps `docai_word_boxes/page_N.json` at
    96-98% across pages 20/36/37/38/39/100/200, and **the check discriminates** -
    neighbouring cache pages score 20-36%, so it can fail and does not (Lesson
    25). How a pre-fix-dated download is already in post-fix order is unexplained
    and worth a look before anyone rebuilds a page-indexed cache from it.

    Result: `google_books_layer/` - 337 files, 2.6 MB, gitignored, aligned to the
    pipeline's own page numbering.

    ### The gate: 4,747 divergent spans over 190,915 tokens

    `tools/gate_docai_against_layer.py` aligns the two Google readings per page
    and reports only where they SPLIT. It deliberately reports no agreement
    score, because agreement between two Google systems on one sheet of ink
    carries no information. Over Part 1's pages 14-247, 234 pages compared:

        divergent spans   4,747   2.49% of DocAI tokens
        worst pages       148 (4.40%), 238 (4.33%), 195 (4.23%), 170 (4.02%)

    Triaged by the cheap lexicon test:

        spacing only          554   11.7%   tokenisation, not a reading difference
        LAYER valid, DocAI not 1434   30.2%
        DocAI valid, layer not  646   13.6%
        both valid             1953   41.1%   needs the ink
        neither valid           160    3.4%

    The layer beats DocAI better than 2:1 on that test, and the examples are the
    classic sorts: `בססחים`->`בפסחים`, `אטינא`->`אמינא`, `לדערת`->`לדעת`,
    `מלמר`->`מלמד`, `מוער`->`מועד` - ס/פ, ט/מ and ר/ד confusions where DocAI
    produced a non-word and the layer produced the right one.

    **TWO THINGS THAT ARE NOT ESTABLISHED, and both matter more than the 1,434.**

    First, **this is a lexicon argument, which is Lesson 49 FREQUENCY IS NOT THIS
    PAGE** - measured TODAY in item `0DU`, where 166 of 166 lexically-derived
    hypotheses came back as the STORED text once cropped and put to the vision
    adjudicator. This detector is somewhat better founded than those, because a
    second reading of the same pixels is proposing the alternative rather than a
    frequency table - but it is still the same engine family and it still has to
    go through vision before any of it reaches a reviewer.

    Second, **these are DocAI-vs-layer, NOT corpus-vs-layer.** The corpus is not
    DocAI's raw output; it has had a review pass. An unknown fraction of the
    1,434 are positions the corpus already holds correctly. Nobody may quote
    1,434 as a count of corpus errors. The actionable set is the subset where the
    CORPUS still carries DocAI's reading, and computing it is the next step.

    Artifact: `docai_layer_gate.json`. Nothing is applied and no caller consumes
    it, by design.

0EC. **[2026-09-09, reviewer directive] A SECOND BOOK: SEFER HASHORASHIM OF
    IBN JANAH. AND THE IDENTITY SEAM SILENTLY LENDS IT YAD MALACHI'S EDITION,
    ITS PUBLISHER AND ITS 667-KLAL SHAPE.**

    Reviewer, 2026-09-09: "we have a new book to injest - Sefer HaShorashim of
    Ibn Janah", corpus root `~/work/hashorashim`, decisions taken the same turn:
    the Hebrew (Ibn Tibbon's translation, ed. Bacher) first with the Arabic
    original (ed. Neubauer, Oxford 1875) later as a cross-edition witness; a
    sibling corpus root driving ONE shared codebase, not a second clone.

    ### The scan, measured

    `~/work/hashorashim/Sefer_ha_shorashim_berlin_1896.pdf`, 17.5 MB, **651
    pages**, a Google Books digitization of the Ohio State University copy.

        page images      3494x5270 .. 3638x5388 PNG   (18.4 - 19.2 MP)
        Yad Malachi      3440x5312                    (18.3 MP)
        text layer       645 / 651 pages (Google's own OCR)
        0-idx page 0     the "Digitized by Google" disclaimer, same as YM
        every page       a 1034x204 "Digitized by Google" footer strip

    So it clears the resolution bar this project set when it rejected NLI at
    1745x2658, and it is the same SHAPE of artifact as the Yad Malachi PDF -
    including the page-0 disclaimer that gives that file its +1 offset against
    NLI numbering.

    Edition confirmed **from the book's own title page, rendered and read**, not
    from a catalogue: `ברלין. תרנ"ו.` (5656 = 1895/6 CE), printer `בדפוס של צבי
    הירש ב"ר יצחק איטצקאווסקי`, editor `בנימין זאב באכער` (Wilhelm Bacher,
    Rabbinical Seminary of Budapest), from the Vatican and Escorial manuscripts
    (`על פי שני כתבי יד אשר ברומי ובעסקוריאל`). The book names itself `החלק השני
    ממחברת הדקדוק` - the second part of Kitab al-Tanqih, Sefer HaRikmah being the
    first. Page 5 carries the Mekize Nirdamim series page (`הוקמה מחדש בשנת
    תרמ"ה`), so Mekize Nirdamim is the SOCIETY and Itzkowski the PRINTER; do not
    collapse the two into one `publisher` field without saying which it holds.

    **Sefaria does not have this book.** Their `Sefer HaShorashim` is RADAK's
    (`authors: [{'en': 'Radak'}]`, Naples 1490, `categories: ['Reference',
    'Dictionary']`), and its own `enDesc` says it "draws heavily on earlier works
    of Rabbi Judah ben David Hayyuj and Rabbi Jonah ibn Janah". The source Radak
    drew on is absent from the library. Same shape as the Yad Malachi case.

    ### The text layer is stored in VISUAL order, and mirrored Hebrew reads as Hebrew

    Google's embedded OCR extracts each line reversed - characters AND word
    order. Raw `PyMuPDF` `get_text()` on 0-idx 120:

        RAW  : ורמאןינע ןכו ןוהה ץובקמ ותוא ודמחו והובהאש המ רמא ולאכ םעצב י"יל יתמרחהו
        s[::-1]: והחרמתי לי"י בצעם כאלו אמר מה שאהבוהו וחמדו אותו מקבוץ ההון וכן עניןאמרו

    Whole-line reversal is correct; per-WORD reversal is not, and produces
    fluent-looking Hebrew in the wrong order. This is a free same-ink witness
    (like DocAI and Surya, NOT a cross-edition one - Lesson 38 does not apply to
    it, Lesson 24 SHARED INK, SHARED ERROR does), but only after reversal.

    **The page numbers are NOT reversed and I nearly recorded a wrong offset.**
    They extract as separate runs: raw `72` on 0-idx 120 is printed page 72, and
    reversing it to 27 gave three mutually contradictory page offsets that I was
    one step from writing down as fact. The rendered page says 72. Printed page N
    = 0-indexed PDF page N + 48, consistent across 0-idx 60/120/300; front matter
    0-47. Lesson 30 THE WRONG PAGE LOOKS RIGHT, caught by rendering.

    ### The structural unit is not a klal, and the marker is better than a gematria

    Read off the rendered page rather than guessed: entries are headed by the
    root SPELLED OUT AS LETTER NAMES - `הבית והצדי והריש` is the root בצר,
    `הבית והצרי והקוף` is בצק (and the `הצרי`/`הצדי` split in those two is a
    ר/ד misread of the same word, this pipeline's bread and butter). The chapters
    are `מאמרים`, one per letter: 0-idx 300 reads `המאמר השלשה עשר מספר השרשים`.

    Consequences, none of them speculative:

    * `book.json`'s `parts` array takes any number of entries, so 22 letter
      chapters declare cleanly where 3 file chunks do now.
    * `build_gematria_trace.py` has NO analogue here and needs a replacement
      keyed on the letter-name formula - a closed 22-word vocabulary, so it is
      cheaper to detect than a gematria marker AND self-checking, because the
      names spell the root and the roots run alphabetically.
    * `tools/validate_title_alphabetical_order.py` stops being a weak check and
      becomes a real structural invariant.
    * `tools/validate_catchword_continuity.py` applies unchanged - 0-idx 120
      carries the catchword `ב וישמפני.`
    * Bacher's footnote apparatus is dense, numbered, and structurally separate
      from the body. That is `0DB-TODO`'s problem class arriving much larger, and
      it is one of the three things Sefaria named explicitly (`@01headers`,
      `@02bold@03`, footnotes).
    * `pipeline/typography.py`'s alef-lamed predicates are calibrated to Berlin
      1851/2 Zittenfeld type. This is Berlin 1895/6 Itzkowski type - a different
      printing house and different sorts - so those predicates are per-book
      knowledge hardcoded in code with no seam, which is item `0BU` step 1
      arriving as a live problem rather than a cleanup.

    ### THE BUG, and it is on the deliverable path

    `pipeline/corpus_io.py:539`:

        return {key: stored.get(key) or default for key, default in _WORK_DEFAULTS.items()}

    `pipeline/corpus_io.py:255-256`:

        declared = (load_json(repo_path("book.json"), None) or {}).get("parts")
        if not declared:
            return [dict(p) for p in _PARTS_DEFAULT]

    The merge is PER KEY and the guard is FALSINESS, so a `book.json` that
    declares a different book inherits Yad Malachi's value for every key it
    omits, and for every key it sets to `""` or `[]`. Measured with the payload
    `tests/test_pipeline_logic.py:7760` already uses (`Sefer Bedikah`, which
    omits `edition`):

        edition  = 'Berlin, 1851/2 - the second printing, not the Livorno 1766-7 original'
        parts()  = ['part1.json', 'part2.json', 'part3.json']   PART1_MAX_KLAL = 222

    So a second book gets a Berlin 1851/2 edition statement and a 667-klal
    three-chunk shape it does not have. `edition` reaches the dashboard through
    `review_server.py:842`; `parts()` reaches `PART*_MAX_KLAL` and ~40 call
    sites.

    **The test written to prevent exactly this cannot fail on it.**
    `test_the_export_names_the_book_from_book_identity_not_from_a_literal`
    exists because "a second corpus exported through this pipeline would have
    carried Yad Malachi's title into its TEI header and its Sefaria index - a
    wrong edition attribution in a public library". Its payload sets nine keys
    and asserts on those nine. It omits `edition` and asserts nothing about it,
    so the one key that still comes back wrong is the one key outside the
    assertion. Lesson 25 A SIGNAL THAT CANNOT DISAGREE, in the guard rather than
    in the pipeline.

    **Extent, swept rather than assumed:** two sites, both in `corpus_io.py`,
    both on the identity seam. The other `or`-fallbacks the sweep turned up
    (`corpus_root()`'s env var, `_resolve_part_path`'s path default, dict
    lookups over genuinely-optional buckets in `list_drifted_rulings.py` and
    `rank_dispute_queue.py`) are a different pattern and are correct as written.

    **Fix shape, not yet applied:** distinguish ABSENT from BLANK. No
    `book.json` at all keeps the defaults, so this repo's own corpus does not
    move. A `book.json` that EXISTS is the book's declaration: a key it sets is
    used as declared (`"section": ""` means this book has no section, not
    "Klalei HaGemara"), and a key it omits raises naming the key rather than
    borrowing another book's. Per Lesson 21, prefer the loader that raises over
    the one that shrugs.

    ### UPDATE, same turn: a SECOND COPY of the same setting, and a third to come

    Reviewer supplied the HebrewBooks scan too (`req=36864`): **same edition,
    different exemplar** - Google Books digitized the Ohio State copy,
    HebrewBooks the Chabad copy. And: **"a much higher res scan exists from NLI.
    I have not yet received that scan."**

                            Google Books (OSU)        HebrewBooks (Chabad)
        pages               651                       639
        page image          3494x5270..3638x5388      2088x3344..2266x3468
        megapixels          18.4 - 19.2               6.9 - 8.3  (median 7.25)
        bit depth           full-tone PNG             1 bpc BITONAL DeviceGray
        text layer          645/651, VISUAL order     639/639, LOGICAL order
        printed page N      0-idx N + 48              0-idx N + 39

    **The two text layers use opposite conventions.** Google's needs whole-line
    reversal; HebrewBooks' raw `ספר השרשים` extracts correctly as written. Two
    PDFs of one book disagreeing about this is a trap for anything reading both -
    detect per file, never assume.

    **CORRECTION, and it is my own unmeasured claim.** The table above first
    read "full-tone PNG" for Google Books against "1 bpc BITONAL" for
    HebrewBooks, and I built an argument on it - that HebrewBooks was already
    thresholded and so had lost the grey a vision adjudicator uses to tell a
    broken sort from a full one. **I never measured the Google file's bit
    depth.** I had printed `bpc` for HebrewBooks and not for Google, then
    asserted the difference. Measured since, across 17 sampled body pages in
    each: `(1, 'DeviceGray', 'png')` for BOTH. Lesson 1, THE UNRUN CHECK.

    So neither file preserves ink tone, and every claim in this entry about
    bleed or ink weight - mine or anyone's - is a claim about two THRESHOLDING
    PIPELINES, not about two sheets of paper. That is the strongest argument yet
    for waiting on the NLI scan: if it is greyscale or colour it is the only
    source here that can answer an ink question at all.

    ### The ink comparison, measured independently

    Reviewer read the pages up close and reported the Google copy as having ink
    bleed and the HebrewBooks copy as lighter with more whitespace inside the
    letters. **That observation was written into this entry as a quoted premise
    and elaborated into an argument about closed counters before anyone had
    measured it, which is not evidence and should not have been recorded as
    though it were.** Measured now, on printed page 72 in both (GB 0-idx 120, HB
    0-idx 111 - same setting, same words), with the Google image downsampled to
    the HebrewBooks glyph height so the comparison is not merely a resolution
    difference:

        RESOLUTION-NORMALISED, both at 28px glyph height
                                  Google (downsampled)   HebrewBooks
          ink coverage                  17.16 %             15.20 %
          stroke width                  0.258 x H           0.298 x H
          enclosed counters/glyph       0.118               0.021
          connected components          1267                1564

    **CORRECTION, from a reviewer screenshot: I read a two-sided metric in one
    direction.** I wrote that Google was "the cleaner and more discriminable of
    the two". It is not cleaner - it fails DIFFERENTLY, and my own component
    count said so. Shown on the same words in both copies (`שם אבי ר` /
    `הוא בעצמו`, GB p.13, HB p.5):

        Google      merges ADJACENT LETTERS - in הוא the ה and ו are squeezed
                    into one blob. Over-inking closes the space BETWEEN letters.
        HebrewBooks breaks strokes WITHIN a letter - in שם the final mem has a
                    gap in its right leg, a closed box rendered open.

    The numbers carry both halves. Google has more ink and **fewer** connected
    components (1267 vs 1564) because its letters run together; HebrewBooks has
    less ink, more components and a fifth as many surviving counters because its
    strokes come apart. A low component count is MERGING and a high one is
    FRAGMENTATION; I reported only the HebrewBooks side and turned a symmetric
    measurement into a ranking.

    **Opposite failure modes are the good outcome**, and better than one copy
    winning: they are real independence at the glyph level. Where Google fuses
    ה+ו, HebrewBooks probably does not; where HebrewBooks splits a ם, Google
    probably does not. That is the escape from Lesson 24 that no additional OCR
    ENGINE can provide, because every engine reads one image and inherits its
    defects. The operational rule: never settle a disputed glyph by whichever
    file looks like better ink - ask which failure mode the glyph is a case of,
    and consult the copy that does not have that one.

    Not a verdict, and the limits are load bearing: one region of one page;
    enclosed counters are rare in Hebrew square script, so 0.118 vs 0.021 is
    ~150 holes against ~33 and is threshold-sensitive; and the downsample
    applies MY binarization to an image HebrewBooks' scanner had already
    binarized its own way. The usable conclusion is narrower and firmer: the two
    files differ in ways dominated by capture and thresholding, so a disputed
    glyph must not be settled by whichever file "looks like better ink".

    **The second copy is still worth having**, for the reason that has nothing
    to do with ink tone: it is the one witness class that can break Lesson 24,
    SHARED INK, SHARED ERROR. Every engine this project runs reads the same ink,
    which is why 37 identical wrong readings survived to 2-of-3 and 3-of-3
    consensus on Yad Malachi. Two copies of the SAME SETTING are different
    impressions from the same type, so a sort that failed on one sheet can print
    cleanly on the other. Lesson 38 does not apply - the type is identical, so
    "the two printings genuinely differ" cannot explain a disagreement.

    ### DICTA IS NOT A STRONG WITNESS FOR THIS BOOK, and this repo already knew

    The reviewer expected Dicta to do poorly on square script. Checked rather
    than accepted, and it is measured in this repo already - `ocr_engine_comparison_square_13_23.json`
    and `ocr_engine_comparison_rashi_13_22.json`:

        Dicta (square, Berlin)      acc 77.6%   cer 8.49%
        Dicta (RASHI ed.)           acc 94.8%   cer 3.25%
        DocAI (primary, square)     acc 99.0%   cer 0.77%
        Surya (square)              acc 94.7%   cer 1.87%
        Gemini VLM pass A (square)  acc 96.1%

    **This file's own TL;DR is misleading about that and should be read with
    care.** "Dicta 95.6% word accuracy over klalim 2-221 - the strongest witness
    here" is Dicta reading the Jerusalem RASHI printing. On square type the same
    engine scores 77.6%. Nothing in the TL;DR says which script the 95.6% was
    measured on, so the natural reading of it is wrong for any square-script
    book. Sefer HaShorashim is square throughout: DocAI carries it, Surya and the
    VLM corroborate, Dicta does not earn its seat on the evidence already in the
    repo.

    ### SEQUENCING CONSTRAINT, because a third scan is coming

    **Do not build any page-indexed cache for this book until the NLI scan
    arrives** - `docai_word_boxes/`, `images/pdf_pages/`, alignments, marker
    traces. Each is keyed to one PDF's page numbering, none re-derives the
    mapping on its own, and START_HERE's transposed-leaf section records what
    re-pointing them by hand costs. Structural work (chapter and entry
    boundaries, the letter-name formula) is content, not pixels, and can proceed
    now. This is also why the DocAI extraction has NOT been started.

    ### THE NLI RECORD WORKS. Reviewer could not see or download it; I could.

    <https://www.nli.org.il/en/books/NNL_ALEPH990010892830205171/NLI>, driven in
    a real browser 2026-09-09 because a plain fetch cannot see this site (curl
    returns a **Cloudflare challenge**, 6,846 bytes, no record content - the same
    trap START_HERE records for the Yad Malachi Google Books check).

    * The record and the page-turner **load and render**. First hit showed
      Cloudflare's "Just a moment..." interstitial and cleared on its own after a
      wait; that is the likeliest thing the reviewer hit.
    * **657 images** - a THIRD distinct count, against Google Books' 651 and
      HebrewBooks' 639. Image 1 is the physical binding, so NLI is shooting cover
      and boards that the other two omit. This is NOT the simple one-page
      disclaimer offset START_HERE documents for Yad Malachi's NLI copy; do not
      assume any fixed offset between the three without checking content.
    * The **Downloading** dialog offers complete document / current page only,
      PDF or JPEG\ZIP, and Maximal (100%) / Medium (50%) / Small (25%).
      **Maximal is greyed out under PDF and ENABLED under JPEG\ZIP** - checked by
      selecting it, not assumed - anonymously, with no account. Identical to the
      behaviour START_HERE records for Yad Malachi.

    **WHAT IS STILL UNMEASURED, and it is the whole question: NLI's actual
    "Maximal" pixel dimensions.** The browser extension kept dropping the tab out
    of its group before the IIIF/delivery URLs could be read, and curl is
    Cloudflare-blocked, so the reviewer's "a much higher res scan exists from
    NLI" is UNTESTED here. It should not be repeated as fact until it is, and the
    only precedent in this repo points the other way: for Yad Malachi, NLI's best
    anonymous tier was 1745x2658 (4.6 MP) against Google Books' 3440x5312
    (18.3 MP), four times fewer pixels, and that is why NLI was rejected there.
    Google Books here is 18.4-19.2 MP, so NLI has a high bar to clear.

    **The cheap decisive test, not run because downloading needs the reviewer's
    go-ahead:** in that same dialog choose *current page only* + *JPEG\ZIP* +
    *Maximal (100%)*. That is one image, a few hundred KB, and it settles the
    resolution question for the whole book. Nothing was downloaded and the
    terms-of-use box was not ticked.

    ### THE NLI SCAN ARRIVED. IT IS THE LOWEST RESOLUTION OF THE THREE AND THE
    ONLY ONE THAT SHOWS THE INK.

    Downloaded by the reviewer at *complete document + JPEG\ZIP + Maximal
    (100%)* - the highest tier NLI offers anonymously. Rosetta PID `IE36945577`,
    656 JPEGs, 405 MB.

                        Google Books (OSU)   HebrewBooks (Chabad)   NLI (own copy)
        images                 651                  639                 656
        megapixels        18.4 - 19.2            6.9 - 8.3        5.2 - 6.6 (med 5.8)
        bit depth        1 bpc bitonal        1 bpc bitonal       24-bit RGB, TONE
        printed page N    0-idx N + 48         0-idx N + 39        image N + 10

    **The "much higher res scan exists from NLI" expectation is not borne out** -
    NLI is about a third of Google Books' pixels and slightly fewer than even
    HebrewBooks. This is the Yad Malachi precedent repeating exactly: NLI's best
    anonymous tier there was 4.6 MP against Google's 18.3 MP, and that is why it
    was rejected. Flagged as untested in the previous entry; now tested, and it
    went the way the precedent predicted rather than the way it was expected to.

    **But it is genuine continuous tone, and that changes its role rather than
    disqualifying it.** Verified rather than inferred from the RGB mode: 219 of
    256 grey levels carry pixels, **45.7% of pixels are midtones** (40-215), mean
    channel spread 20-32. Both other copies are 1-bit - they discarded the tone
    at capture, irreversibly. So the previous entry's line "neither file shows
    you the ink" is now answered: NLI does.

    ### The three copies are one page pushed three ways

    Same words, printed page 72, cropped from all three
    (`השלמת מלכותך ואין אחרי התכלית`):

        Google Books   DILATED - very black, strokes bulked, adjacent letters running together
        NLI            THE REFERENCE - soft and grey, every letterform complete and separated
        HebrewBooks    ERODED - thin, ragged, strokes breaking

    This confirms the merge/break characterisation above from a third direction,
    and it settles the operational question: **when Google says two letters are
    merged and HebrewBooks says a stroke is broken, NLI is what decides which is
    the artifact.** Lower resolution shows up in NLI as softness, never as loss
    of letter identity.

    ### THREE EXEMPLARS, THREE BINDING ORDERS. Map by PRINTED PAGE, never by image index.

    Ohio State (Google), Chabad (HebrewBooks), and NLI's own copy (accession
    stamp `26 AUG 1927`, pencil shelfmark 492.439.27) - three distinct physical
    books, which strengthens the Lesson 24 escape further.

    **Bacher's roman-numbered editor's introduction is bound at the FRONT in the
    Google copy and at the BACK in the NLI copy** - NLI image #640 is page XXXII
    and #650 is page XLII, after the body ends near #600 (page 590). Ordinary for
    a Mekize Nirdamim volume issued in fascicles and bound to the owner's taste,
    and it is why the front-matter offsets differ so wildly (48 vs 10). Verified
    at printed pages 2, 3, 72 and 590 in NLI against 12, 72 and 252 in Google.

    This is START_HERE's transposed-leaf problem at VOLUME scale. Every
    page-indexed cache must record which scan it was built from, and nothing may
    map between copies by image index.

    **Still open: which scan is primary for OCR.** Google Books has 3x the pixels
    but has been thresholded toward ink; NLI has the true letterforms at a third
    the resolution. DocAI scored 99.0% on Yad Malachi's comparable bitonal square
    scan, so the bitonal path is not disqualified - but this is now a measurable
    question and `tools/compare_ocr_engines.py` is the tool for it. Do not pick on
    the pixel count. `book.json`'s `scan_source` still names the Google copy and
    must be revisited once the primary is chosen, because it ships in the TEI
    sourceDesc.

    ### THE ENGINE COMPARISON ACROSS ALL THREE SCANS. TWO ENGINES DISAGREE ABOUT
    NLI, AND THAT DISAGREEMENT IS THE RESULT.

    Reviewer directive, 2026-09-09: "run the engine comparison across all three
    scans." `tools/compare_ocr_engines.py` could not be used as-is - its primary
    signal is word accuracy against `part*.json` and **this book has no corpus
    yet**, so there is nothing to score against. Built reference-free instead, on
    the SAME six printed body pages (71-76) pulled from each scan by its own
    verified offset. Artifact:
    `~/work/hashorashim/ocr_engine_comparison_three_scans.json`.

    Metrics, none of which need a reference: **unique-type rate** (types this
    scan produced that neither other scan did - idiosyncratic readings, lower is
    better), **lexicon hit rate** (against `lexicon.txt`, comparative only - it
    is Yad Malachi rabbinic vocabulary and this book is biblical lexicography),
    and **cross-scan agreement** of one engine reading all three.

    ### DocAI - the production engine, 99.0% on Yad Malachi square type

                 tokens   types   uniq rate   lex hit
        GB         2966    2041       2.5%      66.7%
        HB         2982    2076       8.2%      65.7%
        NLI        2972    2018       2.7%      67.5%   <- highest lexicon hit

        cross-scan agreement:  GB vs NLI 94.7%   GB vs HB 90.8%   HB vs NLI 90.0%

    **NLI reads as well as Google Books despite having a third of the pixels**,
    and slightly better on lexicon hit. GB and NLI agree with each other at
    94.7%, the highest pairwise figure in the experiment; HB is the outlier on
    every pairing and has 3x the idiosyncratic-reading rate of either.

    ### Tesseract 5.5.3 - and it says the opposite about NLI

                 uniq rate   lex hit
        GB           11.1%     64.6%
        HB           20.4%     60.3%
        NLI          24.5%     60.0%

    Two confounds were tested and BOTH are dead:

    * **Resolution.** GB downsampled to NLI's height stays good (12.7% / 64.1%);
      NLI upsampled to GB's height stays bad (24.6% / 61.1%). Not a pixel-count
      effect.
    * **Internal binarisation.** Tesseract thresholds colour input itself, so NLI
      was pre-binarised two ways. Both made it WORSE: Otsu 54.1% / 48.6%,
      Sauvola 28.4% / 57.1%, against 24.5% / 60.0% native.

    So Tesseract genuinely reads the continuous-tone scan poorly, and DocAI
    genuinely does not. **Had this been run with one engine it would have
    produced a confident and wrong conclusion** - Tesseract alone says NLI is a
    markedly inferior scan; DocAI says it is the equal of Google Books. Lesson 9
    (TWO SIGNALS OR NONE) and Lesson 23 (AN ENGINE, NOT A SAMPLE) earning their
    place on the first real question this book asked.

    **A cross-engine agreement figure per scan was computed (GB 86.7%, HB 74.2%,
    NLI 72.6%) and should NOT be read as scan quality.** It is confounded by
    exactly the above: Tesseract is poor on NLI, so DocAI-vs-Tesseract on NLI
    measures Tesseract. Recorded in the artifact with that caveat attached.

    ### What this settles, and what it does not

    * **Primary for OCR: Google Books.** It wins or ties on every metric under
      both engines, and its 3x resolution is a real advantage for the crop-based
      vision adjudicator, which shows a bbox crop to a VLM.
    * **NLI is not a fallback, it is a full second witness AND the tone arbiter.**
      The prediction that 5.8 MP would cost it accuracy is refuted for DocAI.
    * **HebrewBooks is the weakest OCR input of the three** - 8.2% unique-type
      rate against 2.5/2.7, lowest agreement with both others. Its value is as a
      third exemplar for the merge/break arbitration, not as an OCR source.
    * **NOT settled: absolute accuracy.** Every number here is comparative. No
      word-accuracy figure exists or can exist for this book until there is a
      reference text, and the lexicon hit rates are depressed for all three
      because the lexicon is the wrong book's. Do not quote 66.7% as an accuracy.

    Cost: 18 DocAI pages. Nothing was written into `docai_word_boxes/` - that is
    Yad Malachi's page-indexed cache and writing this book's pages into it would
    have been a real contamination bug; the dumps live in the session scratchpad
    and the summary in the corpus root.

    ### Landed this turn

    * `~/work/hashorashim/` is a corpus root: `book.json` (every field declared;
      `parts: []` and `version_source: ""` are deliberate empty DECLARATIONS,
      valid under the new rule) and a `README.md` carrying the measurements
      above. No corpus files yet.
    * `version_source` is
      <https://www.google.com/books/edition/_/m58-AQAAMAAJ>, supplied by the
      reviewer. **I had rejected that id as the Harvard copy and was wrong to.**
      That came from a small-model summary of the Google about page naming an
      identifier `HARVARD32044019925452`; the PDF ITSELF carries an Ohio State
      University book-depository plate at 0-idx 1, which is primary evidence
      about this file and outranks a secondhand read of a web page. I let the
      summary override the artifact. The Harvard string is still unexplained -
      Google about pages list related copies - so if provenance ever matters for
      redistribution, check it in a browser rather than by text fetch, exactly as
      START_HERE records for the Yad Malachi edition.
    * The `corpus_io.py` fix above is applied, with per-FIELD strictness rather
      than all-or-nothing: `cio.WORK_TITLE` needs `title` declared and nothing
      else, while `book_identity()` requires the whole dict its consumers use.
      543 tests pass; the review server was restarted (corpus_io is one of the
      six modules it imports) and `/api/corpus` still answers Yad Malachi.

0EB. **[2026-09-09, reviewer] THE TESSERACT WITNESS LAYER: 419 ADJUDICATIONS,
    2 TIMES THE REVIEWER PICKED TESSERACT, 0 CORPUS CHANGES. THE REVIEWER
    CALLED IT AND THE LEDGER AGREES.**

    Reviewer, 2026-09-09: "the tesserect layer was mostly noise very few
    disputes resulted in a change but it wasted reviewer time." Measured against
    `reconstruction_witness_queue.json` and the ledger rather than recalled:

    ### What it cost

        419  items built, all on the 3 reconstructed pages (24, 37, 40)
        419  Gemini vision adjudications to triage them
         44  survived WITNESS_PRIORITY_VERDICTS = ("B", "NEITHER") and were served
         32  a human actually ruled on

    ### What it returned

    Vision over the whole built queue:

        382  A - DocAI, which is what the corpus was already built from   91.2%
         16  B - Tesseract, the witness                                    3.8%
         21  NEITHER                                                       5.0%

    The 32 human rulings, by what the reviewer picked:

         18  docai_reading      - kept what the corpus already had. No change.
         11  custom             - typed something themselves
          2  tesseract_reading  - THE WITNESS WON
          1  unreadable

    **BOTH Tesseract wins are unmapped.** klal 30 docai token 379 (`ידו`) and
    klal 88 token 552 (`וכוותייהו`) have `word_index: null` in the queue, so
    they sit on no word, have no dashboard URL, and cannot be applied by
    anything. In the entire history of this layer the Tesseract reading was
    chosen twice and reached the corpus zero times.

    Nor did anything else. No script promotes a `witness_choice` (item `0EA`),
    so the 11 custom rulings did not land either - 6 of them the corpus already
    held, which is to say they were confirmations, and the other 5 are still
    outstanding as of today.

    ### The one thing the layer actually found

    One real defect, and it took today's `verify_witness_green_vision.py` pass to
    surface it - it was never green, so `0EA`'s green-filtered first pass missed
    it:

        http://127.0.0.1:8420/klal/88/word/518    corpus בס'    ruling בפ'

    The context is `על ברייתא דמתנייא ___ אלו מגלחין`, and `אלו מגלחין` is a
    PEREK of Moed Katan, so the word is `בפ'` (בפרק), not `בס'` (בספר). Both
    forms are common in this book - `בפ'` 103x, `בס'` 62x - so frequency does not
    decide it; the referent does. The ink agrees at 0.98.

    Note where that finding came from: a `custom` reading the reviewer TYPED, not
    from Tesseract. The witness engine's own contribution to the corpus over 419
    items is nil.

    **FIXED the same day.** The reviewer ruled it in the dashboard at 16:29 as a
    `disputed_choice` (`chosen_source: surya_reading`), and it applied: klal 88
    w518 `בס'` -> `בפ'`, word count unchanged at 1149, now reading
    `על ברייתא דמתנייא בפ' אלו מגלחין`. So the layer's lifetime yield is one
    corrected word, and it needed a route the layer itself does not have.

    ### Verdict, and it is a scope decision, not a code change

    Do not rebuild or extend this layer. Its queue is already restricted to 3
    reconstructed pages, and even there the second engine agreed with the first
    91% of the time and beat it 3.8% - a rate the vision pass alone matches at a
    fraction of the reviewer attention. Lesson 24 SHARED INK, SHARED ERROR
    predicted exactly this: a second OCR engine on the same scan is not a second
    opinion, it is the same page read twice.

    What is worth keeping is the FINDING above and the 5 outstanding customs -
    those came from a human reading the crop, which is the part that worked.

0EA. **[2026-09-09] 27 GREEN WORDS ARE GREEN ON A `witness_choice`, AND NO
    SCRIPT IN THIS REPO CAN PUT A `witness_choice` INTO THE CORPUS.**

    **ANNOTATED 2026-09-14 (`0GL`):** a path exists now -
    `apply_reviewer_decisions.py --apply-witness-choices` - built and OFF by the
    reviewer's instruction, so a plain apply run still promotes none. Nothing
    has been applied through it on either book.

    Found while confirming `0DY`'s eight were gone. Of the 184 words that render
    green in Part 1:

        128  manual_correction
         27  witness_choice          <- these
         23  disputed_choice
          4  no live ruling carrying text
          2  candidate_choice

    `apply_reviewer_decisions.py` promotes exactly three types -
    `all_current("candidate_choice")`, `all_current("manual_correction")`,
    `all_current("title_correction")` - and `audit_applied_decisions.py` checks
    four. `witness_choice` is in neither list, and a grep across `pipeline/` and
    `tools/` finds no writer for it. So a witness ruling colours a word as
    settled and there is no code path by which the corpus can ever hold it.

    That is `0DY`'s defect exactly - green means A HUMAN RULED HERE, not THE
    CORPUS HOLDS IT - at a door `0DY`'s re-ruling mitigation does not reach,
    because re-ruling in the witness panel produces another `witness_choice`.

    ### CORRECTION TO THIS ITEM, SAME DAY

    As first written, this item said a check of these words against `part1.json`
    was "an artifact of indexing the corpus with a token index, not findings",
    citing `review_server.py:1546`. THAT IS WRONG, and the mistake was reading a
    docstring instead of the data (Lesson 33 STATE, NOT PRINTOUT).

    The LEDGER stores the docai_token_index - verified, klal 30's witness rows
    are at 4, 12, 22, 29, 36... which is exactly the queue's
    `docai_token_index` list. But `/api/word-states`, which is what the check
    read, serves them ALREADY MAPPED through
    `reconstruction_witness_queue.json`'s own `word_index` (klal 30 token 4 ->
    word 120), exactly as the comment two lines above 1546 says it does. So the
    comparison was against the right index all along.

    ### ADJUDICATED AGAINST THE INK, and now it is a real answer

    `tools/verify_witness_green_vision.py` (new). It asks a different question
    from `verify_witness_vision.py`: that one triages the queue by choosing
    between two OCR ENGINES before a human rules; this one runs after the human
    has ruled and asks THE CORPUS READS X HERE - IS THAT WHAT IS PRINTED? One
    question rather than two options, because on 21 of 28 the corpus and the
    ruling agree and a two-option prompt would be asking the model to choose
    between a string and itself - `verify_corrections_vision.py` finding 7's
    shape, which always resolves to UNCERTAIN.

    28 adjudicated (3 more are unmappable, below):

        17  the ink shows what the corpus holds        - settled
         8  vision returned NEITHER and transcribed a NON-WORD
         2  vision picked the ruling, on a geresh vs apostrophe only
         1  genuinely open

    THE 8 ARE VISION FAILURES, NOT CORPUS FINDINGS, and saying so is the point
    of running this before surfacing anything. Every one transcribed something
    that occurs ZERO times in 9,926 distinct corpus words - `אכ"ר` for `אב"ד`,
    `דהייט` for `דהיינו`, `כשם` for `בשם`, `חה` for `וזה`, `למתי` for `לכותי`,
    `שורה` for `שוה`. Those are the model reading letterforms literally through
    the same ב/כ, נו/ט, ו/ח confusions the OCR makes. Attestation is the filter:
    a NEITHER whose transcription is not a word anywhere in the corpus is
    evidence about the model, not about the page.

    The 2 geresh rows are the prompt's own constraint 4 being ignored - it says
    to treat `׳` and `'` as the same mark - so they are cosmetic, not findings.

    ### WHAT IS ACTUALLY OPEN

    Two positions for a human, and three rulings that sit on no word at all:

        http://127.0.0.1:8420/klal/30/word/166    corpus חז"ל,      ruling וז״ל,       ink ח"ל
        http://127.0.0.1:8420/klal/75/word/1174   corpus ביואין זה, ruling ברואין זה,  ink בוזאין זה

    klal 30 w166 is a choice between two standard abbreviations - `חז"ל`
    (חכמינו זכרונם לברכה) and `וז״ל` (וזה לשונו) - and the ink's `ח"ל` supports
    the corpus's first letter, not the ruling's. klal 75 w1174 is the one place
    all three readings are unattested: `ביואין` occurs once in the corpus (here,
    so it is its own only witness), `ברואין` and `בוזאין` never. `רואין` occurs
    twice, which makes the ruling's ב-prefix plausible - it needs the crop.

    UNMAPPED - a live witness ruling whose queue row carries `word_index: null`,
    so it colours nothing and can be reached from nowhere:

        klal 30, docai token 379, page 24: chose `ידו`
        klal 88, docai token 552, page 40: chose `וכוותייהו`
        klal 88, docai token 861, page 40: chose `` (empty)

    ### STILL OPEN, and unchanged by the above

    No script promotes a `witness_choice` into `part1.json`. The 17 confirmed
    rows are right by luck of the reconstruction, not because anything applied
    them, and the two open positions cannot be fixed by re-ruling in the witness
    panel - that produces another `witness_choice`. Whether a witness ruling is
    even MEANT to change the base text (it offers `docai_reading` against
    `tesseract_reading`, and `_decision_original_word` records that it snapshots
    neither) is a reviewer question. It belongs with the deferred tri-state work
    in `0DY`.

0DZ. **[2026-09-09, reviewer] "USING THAT URL DOES *NOT* ZOOM IN THE SCAN PANEL
    ON THE SELECTED WORD" - IT DID ZOOM. IT ZOOMED SOMEWHERE THE WORD IS NOT.
    FIXED.**

    Reported on the eight `0DY` links, and true of every share URL that names a
    word far enough down its page to need a scroll.

    ### What the reviewer saw, measured

    Headed Chromium, 1600x1000, following each of the eight links cold:

        klal  word   zoom     focused box, relative to a 954px-tall viewer
        23    599    220%     578px below its centre - off screen
        69    188    220%     686px below - off screen
        159   10     220%     741px below - off screen
        161   289    220%     187px below - off screen
        174   116    220%     677px below - off screen
        200   145    220%     862px below - off screen
        216   123    220%     932px below - off screen
        206   2      220%     on screen

    Seven of eight. Only klal 206 w2 looked right, and only because it is the
    second word on the page: it needs no scroll, so nothing could go wrong.

    Note `zoom: 220%` in all eight rows. THE ZOOM WAS NEVER THE PROBLEM - the
    pane magnified to reading level every time, at the top-left of a page whose
    word is 700px further down. A check on `#zoom-level` sees a healthy system
    (Lesson 41: THE GUARD THAT TESTS A PROXY).

    ### Cause

    Centring on a word is a smooth scroll, ~400ms. The routed click also OPENS
    THE WORD'S DECISION PANEL, which narrows `#scan-viewer`, which fires the
    ResizeObserver inside those 400ms - and `refitScanToPane()` did this:

        applyZoom(null, null, { centreFocused: false });

    Its comment says why: "A resize is not a request to go to the focused word,
    it is a request to keep the view still" (item `0DJ`). But `applyZoom` reads
    the anchors off the CURRENT scroll - mid-animation, still at the top of the
    page - and then sets `scrollLeft`/`scrollTop` directly, which in Chrome
    CANCELS a running smooth scroll. So the refit pinned the pane to where the
    animation happened to be and killed the animation that was leaving.

    Lesson 41 again, on the fixing side: the guard asked "is this a resize?"
    when the condition that matters is "is the reviewer mid-arrival at a word?"

    ### Fix

    `review_frontend/app.js`, a deadline set wherever a centring scroll is
    issued and read by the one call site that repeats:

        let _focusScrollUntil = 0;
        const FOCUS_SCROLL_MS = 1000;               // > the ~400ms smooth scroll
        function markFocusScrollInFlight() { _focusScrollUntil = performance.now() + FOCUS_SCROLL_MS; }
        function focusScrollInFlight() { return performance.now() < _focusScrollUntil; }

        // in refitScanToPane(), before the 0DJ line:
        if (focusScrollInFlight() && hlContainer.querySelector('.hl-box.focused')) {
          applyZoom(null, null, { behavior: 'auto' });
          return;
        }

    `behavior: 'auto'` deliberately: the smooth scroll still in flight is aimed
    at an offset computed against the OLD image width, so it must be REPLACED,
    not allowed to finish. An instant scroll does both.

    After: 0 of 8 off screen, headed, at 1600x1000 and 1280x800.

    ### Why this survived until a reviewer hit it

    THE SUITE COULD NOT SEE IT. Headless Chromium has no real smooth-scroll
    animation, so there is nothing for the refit to interrupt: 0 of 8 links fail
    headless, 7 of 8 fail headed. Every frontend test in this project runs
    headless.

    So `test_a_share_url_lands_the_word_on_screen_in_the_scan` launches its own
    HEADED browser, off the module's playwright instance (a second
    `sync_playwright()` in the same thread raises "Sync API inside the asyncio
    loop"), and skips if no display is available. It asserts the box is on
    screen, not that the readout says 220%.

    A second test, `test_a_resize_long_after_arriving_still_does_not_chase_the_word`,
    pins the BOUNDARY - a resize outside the window must still hold the view
    still, which is 0DJ. That gap was real: 0DJ's own test records three
    attempts to drive it through a real `set_viewport_size()` that all passed
    under a mutation restoring the chase, so it tests `applyZoom`'s contract and
    leaves `refitScanToPane`'s call site - the line this item edits - uncovered.
    Measured: replacing the new gate with `true` left all 105 existing tests
    green. The real resize IS observable here because 0DZ's re-centre is an
    INSTANT scroll, landing in one frame rather than animating past any wait.

    Mutation-checked both ways: gate forced on, the boundary test fails; gate
    forced off, the share-URL test fails. 652 passed, 1 skipped.

0DY. **[2026-09-09, reviewer] "WHY DOES klal 159 w10 SHOW GREEN?" BECAUSE GREEN
    MEANS *A HUMAN RULED HERE*, NOT *THE CORPUS HOLDS IT* - AND FOR 8 WORDS
    THOSE HAVE COME APART. SIX OF THEM PERMANENTLY.**

    ### The mechanism

    The entry at klal 159 w10 is an `ai_flag`, and `app.js:222` colours it:

        if (corr.opcode === 'ai_flag') return corr.flag_answered ? 'human' : 'open';

    `flag_answered` is true because `_flag_answered_by_a_later_decision()` found a
    `disputed_choice` at that word dated 2026-09-07, later than the flag itself
    (2026-08-31). That is correct and is the klal 163 fix working: a flag a human
    has since ruled on must stop showing as open work.

    **But the ruling is unapplied and permanently undappliable.** Its
    `candidate_snapshot` is `null` (item `0DX`, cause B), so nothing can
    drift-check it and nothing can re-point it. The corpus still reads `איכא`
    where the reviewer chose `אליבא`, and the screen says done.

    Note what green does NOT come from here: `current_decision` on an `ai_flag`
    entry is the FLAG'S OWN `klal_flag` row (`chosen_text: null`), not the human
    ruling - `wordState()` carries a comment saying exactly that. A first attempt
    to measure this compared `current_decision.chosen_text` and found 8 mismatches
    that did not include klal 159 w10 itself. The right comparison is against the
    ruling that ANSWERED the flag, which is a different row.

    ### Extent, measured against what the reviewer actually sees

    **198 words render green. 8 of them are green on an unapplied ruling whose
    text the corpus does not hold:**

        http://127.0.0.1:8420/klal/23/word/599    chose 'בעי'         corpus 'ביעי'
        http://127.0.0.1:8420/klal/69/word/188    chose 'אל ואלהים'   corpus 'ואלהים דליתא'
        http://127.0.0.1:8420/klal/159/word/10    chose 'אליבא'       corpus 'איכא'
        http://127.0.0.1:8420/klal/161/word/289   chose 'נתנאל'       corpus 'נתנן'
        http://127.0.0.1:8420/klal/174/word/116   chose 'אלא'         corpus 'לא'
        http://127.0.0.1:8420/klal/200/word/145   chose 'אלו'         corpus 'או'
        http://127.0.0.1:8420/klal/206/word/2     chose 'אלו'         corpus 'או'
        http://127.0.0.1:8420/klal/216/word/123   chose 'אלא'         corpus 'לא'

    **Six of the eight are the null-snapshot ligature rulings of `0DX` cause B** -
    so they are not merely unapplied, they are unappliable by any code path, and
    they will show green until someone re-rules them. The other two are worth a
    look on their own: klal 23 w599, and klal 69 w188, which is the same klal and
    the same `ואלהים` that Lesson 34 records as having been silently deleted once
    by a mis-scoped mutator.

    The other 190 green words are honest: their ruling is applied, or its text is
    what the corpus holds.

    ### NOT FIXED, and this one is deliberate

    The obvious repair is a fourth word state - "ruled, but not in the corpus" -
    or making `flag_answered` require an APPLIED ruling. Both change the
    tri-state, which `review_counts.word_states()` and `app.js`'s `wordState()`
    encode twice and `test_nav_tristate_matches_what_each_word_actually_renders_as`
    pins across both.

    An hour before this was found, three attempts at a smaller change to the same
    function (`api_klal`'s stranded panel, item `0DX`) each regressed a different
    invariant, and were reverted under Lesson 31. Attempting a tri-state change on
    the same afternoon, in the same function, without first establishing how the
    four merged sources interact, is the same mistake with a bigger blast radius.
    The measurement above is what the fix should be built on, and the fix wants
    its own session.

    **The cheap mitigation, if the eight matter before then:** they are all in
    `0DX`'s list and all reachable in the dashboard queue except klal 211 w73.
    Re-ruling one clears both the drift and the false green in a single click.

    ### UPDATE 2026-09-09, later the same day: THE EIGHT ARE GONE

    The reviewer took the cheap mitigation and re-ruled klal 159 w10 and 161
    w289 in the dashboard. Those re-rulings carry a `candidate_snapshot`, unlike
    the 2026-09-07 pair, so they are appliable - and applying them also closed
    the four ligature siblings. Verified word by word against a before-copy of
    `part1.json`:

        klal  23 w599    ביעי  ->   בעי     ruling: בעי
        klal  69 w188  ואלהים  ->  ואלהים   ruling: ואלהים  (already correct - see below)
        klal 159 w10     איכא  ->  אליבא    ruling: אליבא
        klal 161 w289    נתנן  ->  נתנאל    ruling: נתנאל
        klal 174 w116      לא  ->    אלא    ruling: אלא
        klal 200 w145      או  ->    אלו    ruling: אלו
        klal 206 w2        או  ->    אלו    ruling: אלו
        klal 216 w123      לא  ->    אלא    ruling: אלא

    Eight for eight. Re-measured against the live `/api/word-states`: **184
    words render green, and 0 of them sit on a promotable ruling whose text the
    corpus does not hold** (was 8).

    **klal 69 w188 was never actually wrong**, and that is a correction to the
    list as first surfaced. Its newest live ruling is a 2026-09-07
    `disputed_choice` for `ואלהים`, which the corpus already held; the
    `אל ואלהים` this item first reported is a 2026-08-30 row that ruling
    supersedes. The measurement took the ruling that ANSWERED the flag rather
    than the NEWEST live ruling at the word, and for this one word those are
    different rows.

    **The applier reports the six as skipped-for-drift on every run, and will
    forever.** The ledger is append-only, so the superseded 2026-09-07
    null-snapshot rows are still in it and still fail the drift gate - they
    appear in the same run's "7 open flags closed" list and its "14 skipped"
    list, which reads like a contradiction and is not. Nothing to fix in the
    corpus; a reader of that output needs to know it.

    The tri-state repair is still deferred, and still wants its own session -
    see `0EA`, which is the same defect at a door the fix above does not reach.

0DX. **[2026-09-09] A DECLINED INSERTION NOW SETTLES BEFORE THE DRIFT GATE - TWO
    RULINGS UNSTUCK SINCE 2026-08-11. THE STRANDED-PANEL WIDENING WAS ATTEMPTED
    THREE TIMES, REGRESSED EVERY TIME, AND IS REVERTED AND HANDED BACK.**

    ### Fixed: a ruling that needs no write could never reach the branch for it

    `chosen_text: ""` on a `delete` opcode means "do not insert here". It writes
    NOTHING, so there is no position to verify and nothing drift can invalidate.
    But the drift gate ran first:

        if not snapshot_matches(snapshot, live_entry, ignore_index=by_id):
            if live_entry is not None or not snapshot_still_matches_corpus(
                    snapshot, klal, at=word_index):
                skipped_drift.append((klal_id, word_index))
                continue
        ...
        rejected_insertion = (opcode == "delete"
                              and not (decision["chosen_text"] or "").strip())

    and `snapshot_still_matches_corpus()` refuses a delete-opcode snapshot in its
    own docstring - "names no such span - there is nothing in the corpus to check
    it against". So the rejection branch was unreachable for exactly the rulings
    it was written for. **klal 4 w35 and klal 106 w46, both stuck since
    2026-08-11**; klal 106 w46 doubly, that klal having exactly 46 words so w46
    is the append position and out of range for any corpus check that could pass.

    Declined insertions are now settled ABOVE the gate. An ACCEPTED insertion
    still faces it in full, because that one writes. Drift worklist 16 -> 14, and
    the later branch's `rejected_insertion` is removed as dead code with the
    reason recorded rather than silently dropped - its note wording was carried
    forward so the two spellings of one outcome do not diverge.

    ### NOT fixed: the stranded panel still shows only `manual_correction`

    `api_klal`'s stranded loop iterates `all_current_live("manual_correction")`
    alone, so a `disputed_choice` or `candidate_choice` that lost its queue entry
    is reachable by NO route: not the text pane, not the queue, not the panel -
    only the drift worklist, which cannot clear anything. Measured: **3 rulings**
    (klal 4 w35, 106 w46, 211 w73 - all `delete`-opcode). Two of the three are
    now settled by the fix above, so the live extent is **1**: klal 211 w73.

    **Three attempts, three regressions, so it is reverted under Lesson 31.**

      1. Widened the loop's input to both ruling types. That loop has TWO jobs -
         collect stranded rulings AND build `manual_word_indices`, which marks a
         word human-decided - so it widened both, and 6 words began rendering as
         `manual` with no box on the scan.
      2. Narrowed `manual_word_indices.add()` to `manual_correction`. Did not
         help; klal 17 w242 still gained a queue entry it never had, and I could
         not explain why from reading.
      3. Left the original loop untouched and added a separate pass. That worked
         for the three target klalim and left klal 17 alone - and broke four
         other tests, including `test_word_level_ai_flag_yields_to_a_manual_
         correction_on_the_same_word`.

    Each attempt was built on a mechanism I had not established, which is what
    Lesson 31 is about: "further attempts are guesses wearing fixes' clothes, and
    the correct move is to document the issue with its measured extent and hand
    it to the user". The measured extent is above. `api_klal` merges four sources
    through `claim_word_index()` under a last-write-wins map, and anything added
    to that merge has to be reasoned about against all four - which is the work
    this needs and did not get.

    ### Corrections to two counts I reported before measuring properly

    I told the reviewer "25 pending" and "10 reachable by no route". Both came
    from `rd.all_current`, which returns superseded rows; `rd.all_current_live`
    exists for exactly this and says so ("A DISPLAY must not show a superseded
    ruling"). The real numbers: **16 pending** (now 14), and **3** with no route
    (now 1). Seven of the "10" were superseded rows that are not pending at all,
    and five of the rest DO reach the reviewer through the panel. Lesson 33
    (STATE, NOT PRINTOUT) for the second time in two days - the wrong accessor
    reporting on itself.

    ### Why the other pending rulings are stuck, since it was asked

    Of the 9 the reindexer cannot move, two causes:

      * **3 name no word** (`opcode: delete`) - an insertion is addressed by the
        index it goes BEFORE, so its snapshot carries `final_text: null` by
        construction. This is `0DT`, and it turns out to bite in two places: the
        reindexer AND the drift gate.
      * **6 have `candidate_snapshot: null`** - no snapshot at all. klal 159 w10,
        161 w289, 174 w116, 200 w145, 206 w2, 216 w123, every one a dropped-alef
        ligature repair recorded from the worklist on 2026-09-04. With no
        snapshot there is nothing to drift-check and nothing to verify a move
        against, so they are permanently drifted by construction. No code fix
        reaches these: they need re-ruling in the dashboard, where they ARE
        reachable through the queue.

0DW. **[2026-09-09] TECH-DEBT SWEEP OF THE WHOLE PROJECT, AND THE 49 LESSONS
    REWORKED: EVERY LESSON NOW HAS A NAME, AN ORDER BY MEASURED BITE, AND A
    FAMILY MAP. PLUS LESSON 0.**

    Reviewer: "find tech debt across the whole project... review all 49 lessons.
    surely some are duplicate. order by frequency of bite. reword as needed.
    reference across lessons." Then: "give each lesson a short descriptive name.
    useless to say lesson 5 bit me again." Then: Lesson 0.

    ### The debt sweep - most axes came back CLEAN, which is the finding

    52,947 lines across 109 files. Run: orphan functions, functions referenced
    only by tests, modules nothing imports and nothing runs, one-off scripts
    named in no doc/test/chain, record fields written and never read, duplicated
    function bodies, TODO/FIXME markers, unreferenced root data files.

    | axis | result |
    |---|---|
    | orphaned functions | **0** |
    | referenced only by `tests/` | **0** |
    | TODO / FIXME / XXX / HACK | **0** |
    | duplicated function bodies across files | 2, both already filed (`0DD`, `0N`) |
    | record fields written and never read | 1: `ci_low`/`ci_high` per dispute in `dispute_queue_ranked.json` |
    | modules nothing imports and nothing runs | 1: `pipeline/second_witness_eval/__init__.py` |
    | scripts in no doc, no test, no chain | 3: `test_kraken_local.py`, `test_kraken_square_script.py`, `test_trocr_benchmark.py` |
    | root data files nothing reads | 6 |

    **The three dead engine scripts are the only real code debt.** kraken and
    trocr were evaluated and not adopted; neither is in `requirements.txt`
    (though both are installed in this venv, which is its own small lie). The
    repo's own rule is that git is the archive - "a one-time script is not lost
    when it is deleted" - so these are exactly what that rule is for. NOT
    deleted here: three docs still discuss the engines, and removing the scripts
    without checking what those docs promise is how a reference goes stale.

    ### THE DOCUMENTED TEST COUNTS WERE WRONG FOR THE FOURTH TIME

    `START_HERE.md` said 56/388/444 gated and "562 in total". Measured
    2026-09-09: **62/464/526 gated, 650 total.** The three previous values were
    also wrong when quoted. All four sat in a paragraph whose own last sentence
    read "Re-measure before citing; do not quote this line."

    **The numbers are removed rather than corrected.** A number nobody can keep
    true does not belong in prose; the paragraph now names the command
    (`pytest tests/ --collect-only -q`) and points at Lesson 37, which is the
    only count that means anything. Correcting them a fifth time would have been
    the same defect with a fresh date on it.

    ### The lessons: no duplicates, but nine FAMILIES

    Reviewed all 49 for duplication. **There is none.** What reads as repetition
    is one failure shape at different LEVELS, and the level is the useful part -
    e.g. BUILT AND DELIVERS NOTHING runs 1 (never run) -> 32 (runs, writes
    nowhere) -> 29 (written, never displayed) -> 47 (complete, tested, no
    caller), in ascending order of how finished the thing looks. Nine such
    families are now mapped at the top of the section.

    Three entries were NOT rules at all and are rewritten as rules: 20, 21 and
    22 were implementation notes in a different register (22 still carried LaTeX
    from wherever it was imported from, and described an architecture item `0N`
    says nothing on the rebuild path uses - it is now kept explicitly as a
    standing example of Lesson 47).

    ### Named, and ordered by MEASURED bite

    Every lesson has a short name, because "Lesson 5 bit me again" carries
    nothing and *FUZZY IS NOT A POSITION* carries the whole finding.

    **The numbers stay as stable ids and nothing was renumbered: 723 citations
    of "Lesson N" exist** (334 in code, 389 in the status files). Renumbering to
    put the sharpest first would have broken every one - which is Lesson 48
    (RENAME BY TOKEN, NOT REGEX) applied to this document: the names are the
    derived, renameable half, the numbers are the append-only log. So the
    ordering is an INDEX, not a reordering.

    Ranked by citations per day since introduction, not raw count - a raw count
    ranks by age. Top five: **34 SWEEP THE SIBLINGS** (4.1/day), **13 THE SECOND
    COPY OF THE TRUTH** (3.6), **25 A SIGNAL THAT CANNOT DISAGREE** (3.1), **46
    ANNOTATE, DO NOT SUPERSEDE** (3.0), **9 TWO SIGNALS OR NONE** (2.6). The
    index says in its own header that a low rate is not permission to skip one:
    45 PIXELS, NOT THE DOM has never been cited and was used twice on the day it
    was measured.

    ### Lesson 0

    Reviewer's own words: "Don't Forget My Lessons. If you are bitten by one of
    these - acknowledge it in detail with code - then write ten times I Will Not
    (do x)."

    Being bitten by a rule already written down is a different failure from
    finding a new one, and it now gets a different response: name the lesson,
    paste the code that did it, state what the lesson said that you did anyway -
    then ten literal lines of `I will not <the specific thing>`.

    Its justification is measured on this session and counted rather than
    remembered: **42 THE MUTATION THAT DID NOT FAIL bit five times across three
    tests** (one test went blind in three successive shapes), **13** once (the
    same `--acknowledge` block written three times, two already diverged), **19**
    once (asserting klal 144's findings were false positives, contradicted by an
    item in the same file), **33** once (a measurement that read my model of a
    report instead of its fields). All four were read at the start of that
    session and several were cited by me inside it.

    ### LESSON 0 SERVED, ON THIS SESSION, WITH THE CODE

    Recorded here because the ten lines go in the reply where the reviewer sees
    them, but the EVIDENCE has to survive the conversation - and because Lesson
    0's stated purpose is a line that can be grepped for to see which rules keep
    failing to bind. The reviewer had to ask twice for this: the first
    acknowledgement was prose, and Lesson 0 says *with the code*.

    **13 THE SECOND COPY OF THE TRUTH.** The same `--acknowledge` block written
    three times in one afternoon, two already diverged by the time anyone looked.
    `build_title_report.py:204` and `list_ligature_words.py:141` both did:

        n = ack.record(cands, ACK_PATH, args.note, text_field="title_word",
                       only=lambda r: (r["klal_id"], r["word_index"]) in want)
        missed = want - {(r["klal_id"], r["word_index"]) for r in cands}
        if missed:
            raise SystemExit(...)

    - record, THEN validate. `build_structural_defect_report.py:231` validated
    first. So `--acknowledge 144:4 --acknowledge 999:0` wrote the first and
    raised on the second in two tools of three, leaving a partial write nobody is
    told about. Fixed as `triage_ack.record_selected()` (item `0DQ`).
    *I will not write the same logic a second time instead of extracting it.*

    **19 WRITTEN IS NOT APPLIED.** `0DF` as committed at `c69234e` said klal 144
    w837/w839 "are **exactly the false positive `0DE` finding 6 predicts**". The
    header of `build_structural_defect_report.py:114`, in a file read that same
    session, already said the opposite:

        # `א ב ג ד ה ו ז` can only be `ח`. Confirmed against the scan on the case
        # that prompted it - page 52's right margin carries ten markers, and DocAI
        # read the 8th `ח` as `ה` and the 10th `י` as `ו`, both plain misreads of

    Finding 6 is about runs that do NOT start at `א`; klal 144's run starts at
    `א`, so it never applied. Told to the reviewer twice before the file was
    opened. *I will not assert a connection I have not opened the file to check.*

    **33 STATE, NOT PRINTOUT.** The function that produced `0DF`'s counts:

        def positions(rows, kid_key="klal_id", wi_key="word_index"):
            out=set()
            for r in rows:
                k,w=r.get(kid_key), r.get(wi_key)
                if k is not None and w is not None and k<=222: out.add((k,w))
            return out

    It reads two fields. The rows it read carry a third that settles them -
    `"resolved_false_positive": "ויגל is correct - Psalms 16:9, not ויגאל"` - and
    stage 5b prints `of the candidates, 2 are already-resolved false positives`
    on every rebuild, so the number was on screen during the run that produced
    the wrong one. *I will not measure a record without reading every field that
    settles it.*

    **42 THE MUTATION THAT DID NOT FAIL**, five times across three tests, the
    worst of them three successive shapes of one test. Shape two pinned the klal
    to stop it flaking:

        page.eval_on_selector('#klal-block-66 [data-word-index="200"]', "el => el.click()")
        ...
        assert abs(after - before) < 0.15

    - and klal 66 w200's focus box is never far from either end of the page (gap
    measured at 0.111), so "hold the view" and "chase the word" return the same
    number and the assertion passes either way. *I will not ship a test I have
    not watched fail.*

    ### The pattern, which is the part worth keeping

    **Three of the four were trusting my own output** - my test, my claim, my
    measurement. Other people's artifacts get checked here by default; mine got
    checked only when something forced it. That is the workflow gap Lesson 0
    exists to surface, and it is a better finding than any of the four
    individually.


0DV. **[2026-09-09, reviewer directive] THE LEXICAL DETECTORS ARE DOCUMENTED AS
    WEAK AND GATED ON VISION, AND THEIR 126 ADJUDICATED POSITIONS ARE CLEARED.
    UNSURFACED LEXICAL FINDINGS: 126 -> 0.**

    Reviewer: "wire it and document that the tool is nearly useless and must be
    adj. by vision b4 surfacing to a human."

    ### Wired

    `lexical_defect_report.json` was the last triage report with no
    acknowledgement store (`0DN` left it, deliberately, pending the tier
    decision `0DU` has now made). It uses the same `pipeline/triage_ack.py` as
    the structural, title and ligature reports, with its own store
    `lexical_defect_acknowledged.json`, keyed on content and never an index.

    `--acknowledge-from-vision REPORT` is the intended route and the reason this
    was worth wiring: it reads a `lexical_vision_report.json` and acknowledges
    every position the ink read as the STORED text. Two guards, both of which
    matter more than the convenience:

      * a row carrying an `error` was never adjudicated, so it is NOT
        acknowledged - recording a check nobody made is the one thing an
        acknowledgement store must never do;
      * a position where ANY hypothesis went the other way is excluded and
        printed, so a single `B` cannot be buried under its own position's other
        proposals.

    **140 rows acknowledged, covering the 126 positions of `0DU`.** Verified
    across a full rebuild: 238 candidates, 140 acknowledged, 98 not - and the 98
    are exactly the ones the review queue already surfaces, so **unsurfaced
    lexical positions are 126 -> 0**. That was the whole of the remaining
    unsurfaced set.

    ### Documented, in the four places someone would actually look

    Not one note in a status file. The verdict now sits where a reader arrives:

      * **`tools/detect_insertion_deletion.py` and
        `tools/detect_real_word_substitution.py`** - a banner at the top of each,
        before the code, saying the output must be vision-adjudicated before it
        is surfaced, with both measurements.
      * **`pipeline/build_lexical_defect_report.py`** - the same, plus the two
        commands that adjudicate and record.
      * **`pipeline/assemble_corrections_dataset.py`, on `REVIEW_MIN_REF`
        itself** - the constant somebody would reach for to widen the tier, now
        carrying the measurement that says not to.
      * **`START_HERE.md` Lesson 49** - because it is a rule, not history.

    ### Lesson 49, and it generalises past this book

    "A frequency argument is evidence about the LANGUAGE, not about THIS PAGE."
    No threshold fixes it, because it is not a tuning problem: this book is a
    19th-century printing of a halachic reference and is full of forms that are
    rare in a modern reference corpus and correct on the sheet - so the rarity
    that makes a candidate look sharp is the same property that makes the book
    what it is. For a pipeline meant to generalise to other historical texts,
    that is the part worth carrying.

    ### Corrected on the way

    `START_HERE.md`'s TL;DR said "Part 2's 37 numbered lessons"; there are 49. A
    first attempt at fixing it wrote **63** - a regex counting every `^N. **` in
    the file, which swept up the TL;DR's own numbered lists. Caught by reading
    the number back instead of trusting the edit, which is the same discipline
    this item is about.

0DU. **[2026-09-09] VISION PASS OVER THE UNSURFACED LEXICAL FINDINGS. THE INK
    AGREES WITH THE CORPUS ON ALL 126 POSITIONS - 166 OF 166 HYPOTHESES. THE TIER
    THRESHOLD IS DOING ITS JOB AND SHOULD NOT BE WIDENED.**

    Reviewer, on the highest-ranked finding of the whole set: "klal 92 w346 -
    the ink shows the heh. so not a helpful thing. do a vision pass against them
    all."

    ### Result

    **166 of 166 hypotheses selected the STORED text.** 126 positions, every
    proposal for each one (not just the top-ranked - an `ambiguous` row is
    precisely where frequency cannot choose, so asking the ink about only the
    commonest guess would inherit the bias the ink is being asked to settle,
    Lesson 10). Confidence 0.95-1.00, median 0.98, none below 0.9. 0 errors.

    **Including all 28 whose proposal is attested >=1,000x in the reference
    corpus** - the tier that looks most convincing on paper. `דהלא` -> `דלא` at
    12,899x is a false positive, and so is every one of its neighbours.

    ### THE SIGNAL WAS CHECKED FOR ITS ABILITY TO DISAGREE (Lesson 25)

    166/166 in one direction is exactly the shape of a measurement that cannot
    fail. Two checks before believing it:

    1. **A positive control.** Fed the adjudicator positions where the ink is
       KNOWN to disagree - corrections the reviewer already applied and verified
       - with the wrong pre-correction text as option A. Of the six tried, five
       no longer locate (the applied correction changed the token the locator
       matches on), and **the one that did chose B**, transcribing `גבי` against
       a stored `גכי`. The instrument can say B.
    2. **The transcription field.** 165 of 166 `transcription_found` values equal
       the stored word exactly; the one exception, klal 74 w671, read `שרבא שה`
       - more than the word, a crop carrying its neighbour - and still matched on
       the word itself.

    A second, independent signal agrees: the reviewer read klal 92 w346 off the
    scan themselves and reached the same answer before this ran (Lesson 9).

    ### What it settles

    `merge_lexical_defects()`'s tier - `REVIEW_MIN_REF = 500`, `corpus_count <=
    1`, unambiguous - has been an open question all session: widening it is one
    line and would surface these. **The answer is no.** On this evidence the unsurfaced
    tier is entirely false positives, and widening would put 126 positions of
    them in front of a reviewer - 563 permanent flags on unread material is how
    the 1,496-flag queue happened (item 1).

    The number to hold onto: **both lexical detectors argue from FREQUENCY**,
    which is evidence about the LANGUAGE and not about this page. A rarer word
    one edit from a commoner one is a hypothesis, and on this corpus, below the
    current threshold, it is a hypothesis that is wrong every time it was
    checked.

    ### The tool, and one thing fixed before it ran

    A SOURCE on `tools/verify_flagged_candidates_vision.py`, not a new script:
    `--source lexical`. Everything from the word locator through the
    crop/cache/retry chain was already generic over `{klal_id, word_index,
    original, candidate}`; only where candidates came from was hardcoded to the
    2026-08-16 flag batches. Located 166/166, none needing manual handling.

    **It buffered every result for a single write at the end** - so a 429 or a
    503 partway through a paid run lost everything already paid for, which
    START_HERE.md's incremental-flush rule exists to prevent and which this
    production script had never honoured. Fixed BEFORE the run, not after losing
    one: each result is appended to `lexical_vision_report.jsonl` and flushed as
    it completes. Its report path is now source-specific too - a lexical run was
    about to overwrite `flagged_candidates_vision_report.json`, a different
    investigation's findings.

    ### Not done

    `lexical_defect_report.json` still has no acknowledgement store (`0DN`), so
    these 126 cannot be marked checked and will be re-reported by every rebuild.
    Now that they have a vision verdict, wiring it is worth doing - the store
    exists and takes three lines - but what "acknowledged" should mean for a row
    that a widened tier might later promote is still the reviewer's call.

0DT. **[2026-09-09] WHY klal 211 w73 DRIFTED: AN INSERTION RULING NAMES NO WORD,
    SO THE REINDEXER CAN NEVER MOVE IT. THAT IS 9 OF THE 16 ROWS IN THE DRIFT
    WORKLIST.**

    ### The mechanism, and it is structural rather than an accident

    `reindex_pending_decisions_after_shift()` verifies a move the only way it
    safely can - the word the ruling named must be the word at the shifted index:

        snapshot = decision.get("candidate_snapshot") or {}
        named = snapshot.get("final_text") or snapshot.get("original_word")
        if not named:
            continue                       # nothing to verify a move against

    **An insertion proposal has no such word by construction.** A `delete`-opcode
    candidate is text the SCAN has and the corpus lacks, addressed by the index it
    would be inserted BEFORE, so its snapshot carries `final_text: null` and no
    `original_word`. It can never satisfy that test, so it is never moved, and the
    first word-count change earlier in its klal strands it permanently.

    klal 211, exactly: at 20:17:24 the reviewer ruled an insertion at w67; at
    20:17:50 another at w73. The 21:10 apply run landed w67 - **+4 words** - and
    everything past it moved. w73's ruling stayed at w73, where the corpus now
    reads `יבין`, and the applier's drift guard correctly refused it.

    ### Extent: 9 of 25 pending rulings, and they are 9 of the 16 drifted

        klal   4 w35    delete   ''
        klal 106 w46    delete   ''
        klal 159 w10    -        'אליבא'
        klal 161 w289   -        'נתנאל'
        klal 174 w116   -        'אלא'
        klal 200 w145   -        'אלו'
        klal 206 w2     -        'אלו'
        klal 211 w73    delete   'בשם התוספות :'
        klal 216 w123   -        'אלא'

    **56% of the drift worklist is this one gap**, not anything a human did or
    got wrong. A reviewer working that list is being asked to re-adjudicate
    positions a script could have re-pointed.

    ### The reviewer had already fixed klal 211 themselves, which is the tell

    At **21:23:12**, thirteen minutes after the apply that shifted the klal, they
    ruled the same insertion again at **w77** - the new append position - with
    `בשם התוספות` (the earlier one read `בשם התוספות :`, from a vision
    transcription that saw a colon). Applied 2026-09-09 at their instruction
    ("yes at the end"); klal 211 is 77 -> 79 words and now ends `... תע"א בשם
    התוספות`.

    So the pipeline's answer to a stranded insertion is currently "the reviewer
    notices and re-does it by hand." That works and should not have to.

    **The stale w73 ruling is still in the drift list** and will stay there: its
    `chosen_text` differs from w77's by the colon, so
    `restates_an_applied_ruling()` - which settles a row only while `chosen_text`
    is IDENTICAL - cannot retire it. NOT retired here, because choosing between
    two of the reviewer's own rulings is not a script's call.

    ### The fix that is available, NOT taken

    These snapshots carry a `bbox` and the ledger carries `word_id`, and
    `resolved_position()` already resolves a ruling by both. The reindexer uses
    neither - it only knows the text test. Teaching it to fall back to the bbox
    for a ruling that names no word would move all nine, and it is the same
    two-signal bar `close_satisfied_rulings.py` already holds itself to.

    Not built here: it changes what gets re-pointed automatically, which is a
    scope decision, and item `0DD` is still open on exactly which bbox metric to
    trust - two tools currently disagree on 20 of 663 positions. Building this on
    top of an unsettled metric would be the wrong order.

0DS. **[2026-09-09] HEAVY REVIEW OF TWO DAYS' WORK. FOUR REAL DEFECTS, THREE OF
    THEM IN CODE WRITTEN THE SAME DAY - INCLUDING A CORRECTION TO `0BX`'s OWN
    COLLISION GUARD.**

    Fresh-eyes review of `743f8a6..HEAD` at max effort, plus a self-pass. The
    review dropped two findings mid-flight because the self-pass had already
    fixed them (`0DQ`'s partial write, the `id(row)` keying), which is the split
    working as intended.

    ### 1. HIGH - the diplomatic edition restored 9 words that were never there

    `tools/export_corpus.py`'s deletion-revert branch, `elif not span:`, inserted
    unconditionally. The `replace` branch beside it carries an already-as-printed
    check whose comment explains the exact hazard - "two rulings can name one
    word... once the first has reverted it, the second finds its own answer
    already undone" - and the deletion branch never got it. An insert is not
    idempotent, so both fired.

    Measured: 44 applied rulings reach that branch, **7 positions are named
    twice**, and klal 209's is a three-word phrase - **9 spurious words**. klal 13
    ended `... תיובתיה • יד יד`. The manifest reported 0 refusals for any of it,
    so nothing on the artifact said so, in the edition whose entire purpose is
    fidelity to the printed page.

    **Keyed on the POSITION, not the text**, and the difference was measured:
    testing "is the word already there" reads correctly for a klal marker and
    WRONG for punctuation, where a comma at the resolved index is no evidence
    that it is THIS ruling's comma. The text test drops 14 words; position-keying
    drops the 9 that are actually duplicated. The first fix written here was the
    text test, and it was replaced before commit.

    ### 2/3. MEDIUM - `0BX`'s guard could not see the rulings it most needed to

    Written yesterday, wrong yesterday. `occupied` was seeded from `wi <=
    position`, on the stated premise that "everything after it moves by the same
    delta". **The premise is false**: the loop declines to move three sets of
    rulings that sit PAST position - already applied, no text to verify against,
    refused by the text check - and none was in the set. A mover could land on an
    APPLIED ruling and win the `(klal_id, word_index)` key, which
    `rd.all_current()` resolves last-row-wins: the applied one goes invisible to
    the applier, the display maps and the counts. The exact loss the guard exists
    to prevent, left reachable by the guard itself.

    Now: every occupied slot is seeded, and a slot is freed only when its
    occupant ACTUALLY moves (`occupied.discard(wi)` on a committed move). That
    makes iteration order matter - descending for `delta > 0`, ascending for
    `delta < 0` - the same ordering problem `0DA` hit reverting the diplomatic
    edition. Same correction on the flag side, where `skip` (flags closed earlier
    in the run) is now held occupied too.

    ### 4. MEDIUM - a nav jump scrolled back to the klal it was leaving

    `jumpTo()` closes an open panel before moving to another klal, and it closed
    it with `dismissPanels()` - which since `0DH` also SNAPS the cursor to
    `_lastVisitedWord`, a word in the klal being left. The snap's instant
    `scrollIntoView` overrode the jump's in-flight smooth scroll and re-armed
    `suppressTimer` at 900ms inside a settle loop allowed 3000ms: the drift
    `releaseObserverWhenScrollSettles()` exists to prevent, reintroduced by a
    helper with no idea who was calling it. `dismissPanels({snap: false})` for a
    navigation, and the cursor is dropped on the way out.

    Same finding's tail: the Escape handler had no "is a panel open" test, which
    the click handler beside it has. Harmless while dismissing only closed
    things; since the snap, a stray Escape scrolled the pane. Guarded.

    ### 7. LOW - a migration note that the store contradicted in one line

    `list_ligature_words.py` said "Both entries were migrated"; one was. The
    other (`אוף`) was deliberately not, because the reviewer had reversed that
    judgement - correct decision, wrong sentence. Corrected, with a note saying
    why it is worth correcting: a migration note is exactly the prose a later
    reader trusts instead of checking.

    ### THE TEST FOR FINDING 3's SIBLING WENT BLIND THREE TIMES

    `test_resizing_the_pane_does_not_chase_the_focused_word` passed under
    mutation in three successive shapes: parked at an end the zoom had already
    centred; pinned to a klal whose box is never far from either end (gap 0.111
    of the page); and driven through `set_viewport_size`, where the pane really
    does resize (clientWidth 547 -> 475) and `refitScanToPane` really does fire
    (twice, measured) but the resulting smooth `scrollIntoView` is not observable
    inside any wait worth defending.

    It now asserts `applyZoom`'s CONTRACT in the real page - `centreFocused:
    false` holds the view, the default still centres - and says in its own
    docstring that this is narrower than the resize path it stands for. Three
    attempts at one measurement is the point to stop and test the rule (Lesson
    31); shipping the third green one would have been a test that cannot fail
    (Lesson 25).

    ### Still open from the review

    - **5 (LOW)** `_raised_at()` calls `rd.find_by_id()` per `supersedes` hop and
      that is an unindexed linear scan, running per flag per request. Not a
      re-parse (the list is cached) but the walk is new and grows with the ledger.
      NOT fixed - measured instead: `/api/klalim` A/B'd against the old
      process-lifetime cache came out 27.2 / 25.4 / 25.7ms min across three server
      starts, inside run-to-run variance. The documented 20.4ms baseline is from
      2026-08-26 and the ledger has grown ~1,000 rows since.
    - **6 (LOW)** `list_unreviewed_auto_corrections.evidence()` returning
      `(None, None, None)` is triaged as "neither form in the reference corpus",
      a frequency claim it never made; the honest label is "no ruling recorded".
      Latent - the worklist has 0 open rows.

    Gate 526, UI 104 passed / 1 skipped, rebuild clean.

0DP. **[2026-09-08, reviewer] CLEARING ONE STRUCTURAL FINDING CLEARED ALL OF
    THEM. `--acknowledge KLAL:WORD` ADDED, AND klal 187 w120 IS CLEARED.**

    The reviewer said klal 187 w120 is fine and asked how to clear it. The only
    option `build_structural_defect_report.py` had was **`--acknowledge-all`**,
    which records every current finding - so clearing the one they had checked
    would silently have dismissed every other open one with it. Today that was
    harmless (it was the only open row); it would not have been on any other day,
    and the reviewer would have had no way to know.

    `--acknowledge KLAL:WORD` now matches the two flags added with `0DN`, and all
    three go through `triage_ack.record(..., only=...)` - one mechanism, one
    predicate, no third copy. It refuses a klal:word that is not in the report
    rather than writing an entry that matches nothing.

    **Cleared: klal 187 w120** `רבוואתה` -> `רבו ואתה`. `רבוואתה` is the Aramaic
    plural, not `רבו` + `ואתה`. The merge detector argues from the independent
    frequency of the two halves (1168x / 364x) and cannot see that the whole is a
    word.

    **THE FINDING WAS CREATED BY THE REVIEWER'S OWN CORRECTION**, applied hours
    earlier the same day: `רבואתה` -> `רבוואתה` (klal 187 w120, in the batch of
    31). The detector then fired on the corrected text. That is the detector
    working, not failing - and it is the argument for why stage 4e writes a
    report and never a flag: a correction can manufacture a candidate, and a
    queue that auto-flagged them would hand the reviewer their own work back.

    ### The state of stage 4e, since it was asked

    Runs on **every rebuild**, stage 4e of `rebuild_all.sh`, writing
    `structural_defect_report.json`. Three detectors, four row types:

        repeated_word       10
        ligature_compound    5
        merge                3
        split                0   (none currently)

    **18 findings, 18 acknowledged, 0 open.** Every structural candidate in the
    corpus has now been checked and dismissed by the reviewer. All three merge
    findings are false positives of the same shape - a real word whose halves are
    independently common: `מרבייהו` (305x/483x), `לעירובין` (491x/1512x),
    `רבוואתה` (1168x/364x).

    That 3-for-3 rate is worth recording against any future proposal to route
    merge findings into the review queue: on this corpus the detector's precision
    for `merge` is currently **0 of 3**.

    Gate 523. Rebuild clean.

0DO. **[2026-09-08] THE APPLIER'S FINDINGS FILE HAD NEVER HELD A REAL FINDING.
    86 OF 86 ROWS WERE TEST POLLUTION, AND THE FIX FOR IT WAS ONE LINE MISSING
    FROM A FIXTURE.**

    `unverified_flag_shifts.jsonl` exists because of item `0CU`: the reviewer
    asked "where??" about an unverified shift and the answer was gone, so the
    applier started writing its refusals to a tracked, append-only file instead
    of only printing them.

    **Found while applying 31 decisions: every row in it is synthetic.**
    `tests/test_pipeline_logic.py`'s `apply_harness` redirects every ledger
    READER - the fixture's own comment is a list of them, each added after it
    bit - and never redirected this WRITER. So any test whose run produced a
    refusal appended to the production file.

        86 rows total
        86 with klal_id == 1     <- the fixture's synthetic klal
         0 from any real klal

    Dated from 2026-09-07T19:27, which is the day `0CU` created the file. **It
    has never contained a finding**, and a real one would have arrived into 86
    rows of noise - the exact defeat of the purpose the file was built for.

    Fixed: `apply_harness` now patches `UNVERIFIED_SHIFTS_PATH` to `tmp_path`,
    and the file is truncated (all 86 rows were synthetic; git holds the history
    if anyone wants it). Verified after: a full gated run and a full
    `rebuild_all.sh` both leave it at 0 rows.

    ### The test for it was blind first, and the second cut says why in the code

    `test_the_applier_never_writes_its_findings_file_during_a_test` compares the
    production file's size across a run. First cut used a flag at w4: with a
    uniform deletion every surviving word still matches at its shifted index, so
    w4 MOVED cleanly, **no refusal was produced at all**, and the test passed
    whether the redirect was there or not. Second cut uses a flag PAST THE END of
    the klal, which the bounds check refuses outright, and asserts that a refusal
    actually happened.

    The assertions are ordered production-file-first on purpose: with the
    precondition first, removing the redirect failed on a `FileNotFoundError`
    from the tmp file rather than on the assertion that explains what broke. A
    mutation should say what it broke.

    ### Also this run

    **31 decisions applied**, verified word by word against a before-copy: klal
    144 w837/w839 (`ה`->`ח`, `ו`->`י`, the reviewer's own corrections to the
    marginal markers), klal 30 w1521 `תשל`->`תשקצו`, klal 150 w443 `אוף`->`אף`,
    klal 92 w416 `אפים`->`אלפים`, plus 26 more from the reviewer's session. Two
    were word-count changes (klal 28 w47, klal 29 w99 deletions), which exercised
    `0DM`'s new reindex collision guard in production - it refused nothing, and
    the two shifts it did make were both verified.

    **`TITLE_NOT_PREFIX_OF_BODY_BASELINE` is down to `{9}`.** klal 186's body w3
    read `המקיל'` against the title's `המקיל`; the reviewer ruled the stray
    geresh off and applying it made the two agree. The gate failed the rebuild
    demanding the id be struck from the baseline BY NAME rather than passing
    quietly on a shrunken set - which is the whole reason that baseline is a set
    of ids and not a count.

    Gate 522 -> 523.

0DN. **[2026-09-08, reviewer] "WHERE ARE THESE STORED ANYWAY?" IN FOUR PLACES,
    ONE OF THEM HARDCODED IN A SCRIPT AND KEYED ON A DRIFTING INDEX. NOW ONE
    MECHANISM.**

    The reviewer asked to clear two findings in two different reports and then
    asked where such things are kept. The answer was worse than the question
    implied:

    | report | where a "checked, it is fine" lived | keyed on |
    |---|---|---|
    | `structural_defect_report.json` | `structural_defect_acknowledged.json` | content - correct |
    | `ligature_words.json` | **`KNOWN_FALSE_POSITIVES`, a dict in `tools/list_ligature_words.py:52`** | **`(klal_id, word_index)`** |
    | `title_defect_report.json` | **nothing** | - |
    | `lexical_defect_report.json` | **nothing** | - |

    **The hardcoded dict is the finding.** Clearing a ligature false positive
    meant editing a script, so the reviewer could not do it and it did not look
    like data to anyone reading the report. And its key DRIFTS: an insertion
    anywhere earlier in the klal moves every later index, so the resolution
    silently lands on a different word - the exact failure
    `build_structural_defect_report._key`'s own comment explains it is avoiding,
    in a sibling file, in the opposite direction. Two files, one question, and
    the one that got it wrong was the one nobody had reason to open.

    The two reports with NO mechanism are the other half: a title or lexical
    finding a human had checked came back on every rebuild forever, which is how
    the reviewer arrived at the question.

    ### `pipeline/triage_ack.py`

    One module: `key` / `keys_for` / `load` / `annotate` / `record`. Content key
    `klal | detector | text | occurrence`, never an index. `text_field` is a
    parameter because the reports genuinely disagree on the field name
    (`stored`, `title_word`, `word`) and that name is part of each report's
    published schema - a rename would break readers for cosmetics.

    Each report keeps its OWN store file, so nothing already recorded moves:
    structural still reads `structural_defect_acknowledged.json` and its **20
    acknowledgements survive untouched** (verified by rebuilding: 22 rows, 20
    acknowledged, before and after).

    `--acknowledge KLAL:WORD --note "..."` on `build_title_report.py` and
    `tools/list_ligature_words.py`. It refuses a klal:word that is not in the
    report rather than writing an entry that matches nothing.

    ### Cleared this session, at the reviewer's instruction

    **klal 144 title w4** `מעצמנו` -> `מעצמו`: a false positive. `מעצמנו` is
    first-person plural and agrees with `לנו` in the same title; `מעצמו` is third
    person singular. The detector is frequency-only (`ref_count` 365, and 7 vs 2
    in this corpus) and cannot see agreement. Note recorded with the entry.

    **klal 7 w677** `ויגל`: migrated, not newly cleared - it had been resolved
    since 2026-08-26 (Psalms 16:9, <https://www.sefaria.org/Psalms.16.9>) and the reviewer's "clear it" was already
    true. Reported to them as already-marked rather than acted on twice.

    **klal 150 w443 `אוף` was NOT migrated, deliberately.** Its old marker said
    "אוף is real Aramaic ('also'), not a collapsed אלוף" - and on 2026-09-08 the
    reviewer ruled the opposite, `אוף` -> `אף`, noting a printer's error against
    the M.Y. critical edition. Carrying the old resolution forward would have
    re-asserted a judgement the reviewer has since reversed. The ledger ruling
    stands; the marker is gone.

    ### Not done

    `lexical_defect_report.json` still has no store. It is the largest triage
    surface (213 rows, 118 unsurfaced) and wiring it is the same three lines, but
    its rows are the ones a widened `merge_lexical_defects()` would push into the
    review queue - so what "acknowledged" should mean there depends on a decision
    the reviewer has not made yet (`0DF`). Flagged rather than guessed.

    Gate 520 -> 522.

0DM. **[2026-09-08] `0BX`'s COLLISION GUARD AND `0DE` FINDINGS 6, 7, 8 - ALL
    FIXED, EACH MUTATION-CHECKED. AND A CORRECTION TO `0DF`.**

    ### `0BX` - the reindex collision guard. POLICY: REFUSE AND REPORT

    The item flagged this as needing a policy decision, "refuse" vs "record and
    move anyway". **Refuse**, because it is the choice both reindexers already
    make one line earlier for a move they cannot verify against the text, and
    because "record and move anyway" needs somewhere to put the displaced ruling
    and a reader that looks there. Refusing needs neither and cannot lose
    anything.

    Both reindexers now seed an `occupied` set and refuse a move onto it:

        occupied = {wi for (kid, wi) in current
                    if kid == klal_id and wi is not None and wi <= position}
        ...
        if new_wi in occupied:
            unverified.append((wi, new_wi, "collision")); continue
        occupied.add(new_wi)

    **Only slots at or before `position` are seeded, and that is the whole
    reachability argument.** Everything after `position` moves by the same delta,
    so movers keep their relative order and cannot collide with each other; the
    real case is `delta < 0` landing on a record that is not moving. Targets are
    added as they are written, so two movers cannot be sent to one slot either.

    **The flag side was swept too (Lesson 34), and it had never been measured.**
    Identical shape: `review_server._word_level_ai_flags()` builds
    `by_word[widx]` and the last row per index wins, so two flags on one index
    means one renders nowhere.

    `unverified` rows are now `(old, new, reason)` and
    `unverified_flag_shifts.jsonl` carries `reason` plus a per-reason note, because
    "the word moved somewhere I could not verify" and "the target slot is taken"
    need different actions and the file was making the reviewer infer which from
    two indices.

    ### A finding from writing the flag test, worth more than the test

    The flag collision **could not be reproduced through `apply_harness.run()`**.
    A shift originates at an applied decision's `word_index`, and `main()` runs
    `close_flag_satisfied_by()` for every applied position BEFORE the reindex - so
    the flag sitting in the target slot is normally CLOSED first, and a closed
    flag's slot is genuinely free. The collision needs that closure not to happen,
    which is reachable (`close_flag_satisfied_by` has conditions) but not
    constructible in one line. The test drives `reindex_flags_after_shift()`
    directly and says so, rather than dressing a unit test as an end-to-end one.

    ### `0DE` finding 6 - the enumeration detector, both halves

    `ideal = ALEPH_BET[:len(seq)]` now anchors on the run's OWN first letter and
    is bounds-checked:

        start = ALEPH_BET.find(run[0][1])
        if start == -1 or start + len(seq) > len(ALEPH_BET):
            run = []
            continue
        ideal = ALEPH_BET[start:start + len(seq)]

    That fixes the `IndexError` on a 23+ run (which would abort stage 4e) and the
    assumption that every run starts at `א`. A list continuing from an earlier
    column - `ד ה ו ז` - now produces nothing, while `ד ה ז ח` is still caught,
    which is the assertion that stops the fix from buying silence (Lesson 26).

    The tradeoff is stated in the code rather than hidden: if the FIRST letter is
    itself a misread the anchor is wrong. That is strictly better than the old
    behaviour, which was that same failure for every run not starting at `א`.

    ### `0DE` finding 7 - the acknowledgement key, with a migration that costs nothing

    `_key` gains an occurrence ordinal in `word_index` order, so two findings
    alike in one klal no longer collapse. It survives a uniform shift because
    every index in a klal moves together and the ORDER does not.

    **Occurrence 0 keeps the legacy key**, deliberately: all 22 rows in the live
    report are first occurrences, so none of the 20 existing acknowledgements is
    invalidated. Verified by rebuilding: 22 rows -> 22, 20 acknowledged -> 20, no
    row added or removed, no acknowledgement flipped. A migration that quietly
    re-opened finished work would have been worse than the bug.

    ### `0DE` finding 8

    `cio.load_klal_words(part_path)` at `:156` reuses `klal_words` from `:92`.

    ### CORRECTION TO `0DF`, and it was told to the reviewer twice first

    `0DF` called klal 144 w837/w839 "exactly the false positive `0DE` finding 6
    predicts". **They are TRUE positives.** Item `0CY` in this same file already
    had them confirmed at 6x against the ink, with URLs, and this module's own
    header names them: DocAI read the 8th `ח` as `ה` and the 10th `י` as `ו`.
    klal 144's run starts at `א`, so finding 6's assumption never applied to it.

    Lesson 19's shape applied to a write-up: a plausible connection between two
    things in the same paragraph, asserted without opening the file that refutes
    it in one line - and repeated to the reviewer before being checked. Finding 6
    was a real latent defect; it was never the explanation for these two.

    Gate 515 -> 520. Rebuild clean, exit 0; the only diff in
    `structural_defect_report.json` is the evidence WORDING - same 22 findings,
    same 20 acknowledgements, same proposals.

0DL. **[2026-09-08, reviewer] "CLICKING ON ANY WORD THEN CLICKING AWAY LEAVES A
    GOLD BOX AROUND THE WORD." THE CURSOR WAS WEARING THE DEEP-LINK RING. IT HAS
    ITS OWN, QUIET MARKER NOW.**

    `0DH`'s `snapToLastVisitedWord()` reused `revealWordInText()` for the scroll
    AND for its marker - deliberately, to avoid a second copy of the same four
    lines. The scroll was the right thing to share. The marker was not.

    `.routed-word` is the DEEP-LINK ring: `outline: 3px solid #d69e2e`, a gold
    background wash, and a two-cycle pulse. It is built to shout at someone who
    has just arrived from a pasted URL and does not know where to look. Left on
    the word after every dismissal it reads as a word STATE instead - and gold is
    `--pending` everywhere else on this screen, so it reads as a state the word
    does not have.

    It also never went away. Before `0DI`, dismissing ran `clearScanFocus()` ->
    `clearRoutedWord()`, which removed it. `0DI` stopped calling that, so the
    only remaining caller is `revealWordInText()` clearing everything EXCEPT the
    word it is about to mark. Dismissing went from removing the ring to adding
    one that nothing removes.

    ### The fix

    `.cursor-word`: one 2px `--ink-faint` outline, no fill, no animation. A
    cursor should be findable and otherwise silent, and must not compete with a
    word's real state colour.

    `revealWordInText(klalId, wordIndex, { marker })` takes which one to apply -
    `routed-word` by default so every existing caller is unchanged, `cursor-word`
    from the snap. `clearRoutedWord()` clears both (`WORD_MARKERS`), so the two
    can never be on screen at once.

    And a fresh word click removes the cursor: it marks where you LEFT OFF, so it
    has no business being visible while you are actively on a word. Dismissing
    puts it back, on that word.

    ### Test

    `test_dismissing_a_word_panel_snaps_the_cursor_back_to_that_word` now asserts
    both halves - the word carries `cursor-word` and does NOT carry
    `routed-word`. Mutation-checked: pointing the snap back at `routed-word`
    fails it. UI suite 103 passed / 1 skipped.

    ### Fourth report on one gesture, and the pattern is now clear

    `0DH` (snap) -> `0DI` (flicker) -> `0DJ` (stutter) -> `0DK` (blink) -> `0DL`
    (this). Every one is a consequence of `0DH` reusing existing machinery
    without asking what else that machinery carried: `revealWordInText` carried a
    marker meant for a different situation, and `clearScanFocus` carried four
    behaviours of which only one was wanted. Reuse is right in this repo and the
    shared-module rule says so - but reusing a function means inheriting
    everything it does, and the thing to check before reusing is what ELSE it
    does and who else was relying on that.

0DK. **[2026-09-08, reviewer] "BLINKS WHEN I CLICK AWAY, NO ISSUE WHEN I CLICK ON
    A SPECIFIC WORD" - STILL, AFTER `0DI` AND `0DJ`. IT WAS THE ZOOM RESTORE,
    WHICH BOTH FIXES HAD DELIBERATELY PRESERVED. A DISMISSAL NOW CHANGES NOTHING
    IN THE SCAN PANE.**

    ### THE REAL FINDING IS WHY TWO FIXES MISSED IT

    Every probe written for `0DI` and `0DJ` drove a word whose click did NOT
    zoom - the sampled zoom read "100%" before and after in all of them, which
    means `_zoomBeforeFocus` was null and `restoreZoomAfterFocus()` returned on
    its first line. **Three rounds of instrumentation measured a dismissal path
    that was doing almost nothing**, and reported it as quiet.

    `FOCUS_ZOOM = 2.2`. A real word click zooms to 220%; dismissal put it back to
    100%, resizing the page image **1133px -> 515px in a single frame**. That is
    the blink, it was there before this session, and it survived both fixes
    because both were built to preserve the 2026-08-26 directive that asked for
    it.

    The reviewer had already chosen otherwise, in as many words - "keep the
    word's yellow focus box AND CURRENT ZOOM" - and `0DI` kept the focus but not
    the zoom, on the reasoning that dropping the restore would strand the pane at
    220%. That reasoning was wrong on the facts (clicking any word re-zooms; the
    buttons work) and it is what cost two more rounds. **When a reviewer picks an
    option, the deviation is the thing to justify, not the compliance.**

    Lesson 31 names the number: this is the third attempt at one gesture. The
    first two were inference; this one started from a probe that finally
    reproduced the reviewer's conditions.

    ### Measured, same probe both ways

    | | image width after dismiss | zoom | state changes |
    |---|---|---|---|
    | before | 515px (was 1133) | 220% -> 100% | 1 |
    | after | **1133px, unchanged** | **220%, unchanged** | **0** |

    ### What changed

    `settleScanAfterDismiss()` now only disarms `_zoomOnFocus`. The dismissal
    touches nothing else on the scan.

    `restoreZoomAfterFocus()` REMOVED - the dismissal was its only caller.
    `_zoomBeforeFocus` REMOVED with it: once nothing restores, it was written by
    `zoomToFocus()`, cleared in three places, and read for its value by nothing -
    Lesson 29's shape exactly, and it would have read as a live feature to the
    next person. Both removals leave a note saying what stood there, because
    their ABSENCE is now the behaviour.

    ### The 2026-08-26 directive is fully superseded, on purpose

    "Clicking away returns the highlight to the entire klal correctly and should
    also zoom back out to 100." `0DI` reversed the outline half; this reverses
    the zoom half. `test_clicking_away_restores_the_zoom_and_the_klal_outline` is
    now `test_clicking_away_changes_nothing_in_the_scan_pane` and asserts the
    inverse of what it originally did. All three dated directives are written
    into its docstring rather than one silently replacing another - the reviewer
    asked for the zoom-out before they had seen it next to a focus that survives.

    Mutation-checked: restoring the zoom fails it with "the zoom moved on
    dismissal (220% -> 100%) - that resize is the blink". UI suite 103 passed /
    1 skipped.

    ### The lesson, and it is about the instrument

    `0DJ` already recorded that an unwritten LIFETIME assumption caused the
    cascade. This adds the sharper one: **a probe that does not reproduce the
    reviewer's conditions reports quiet and is believed.** Three separate
    instrumented runs said "no oscillation, no width change" while the actual
    gesture resized the image by 618px, because the sampled word never zoomed.
    Before trusting an instrument that finds nothing, check that it can see the
    thing it is looking for - Lesson 25 pointed at one's own measurements.

0DJ. **[2026-09-08, reviewer] "THE PANE STUTTERS - IT KIND OF ZOOMS IN AND OUT A
    BIT A FEW TIMES PER SECOND." SELF-INFLICTED BY `0DI`, AND THE MECHANISM IS
    THAT `applyZoom()` THREW AWAY THE ANCHORS ITS CALLER PASSED.**

    ### Could not reproduce it, and the questions found it instead

    Three probes failed to reproduce: no image-width oscillation after a
    dismissal, none at any zoom stop from 100% to 300%, with and without both
    scrollbars. Headless Chromium uses OVERLAY scrollbars, which do not consume
    `clientWidth` - and consuming `clientWidth` is the entire mechanism, so the
    environment could not exhibit it.

    Two questions did what the probes could not. **"Only after dismissing a
    word"** and **"clicking another word stops it"** together name the cause
    exactly: the focus box, whose lifetime `0DI` had just changed.

    ### The mechanism

    `applyZoom(anchorRatioX, anchorRatioY)` computed anchors, then in its rAF did:

        const focusedBox = hlContainer.querySelector('.hl-box.focused');
        if (focusedBox) focusedBox.scrollIntoView({behavior:'smooth', ...});
        else            /* use the anchors */

    **The anchors were silently discarded whenever a focus box existed.** That
    was harmless for as long as a focus box was short-lived - it existed while a
    word's panel was open and was destroyed on dismissal. `0DI` made the focus
    SURVIVE a dismissal, on purpose, to stop a different flicker. The box became
    permanent, and every later `applyZoom()` began animating a smooth scroll to
    it whether or not its caller wanted one.

    `refitScanToPane()` is the caller that repeats. It runs from a
    ResizeObserver, and its own comment says "null anchors: keep whatever the
    reviewer is currently looking at centred" - a sentence the code had not been
    honouring. Re-fitting the image toggles a scrollbar, which changes
    `clientWidth`, which fires the observer again; the `_lastFitWidth` guard damps
    that only if each pass CONVERGES, and a smooth scrollIntoView on every pass is
    a moving target instead. Hence a few oscillations per second, and hence
    "clicking another word stops it" - a new focus re-anchors the loop.

    ### The fix

    Centring on the focused word is **opt-in**: `applyZoom(rX, rY, {centreFocused
    = true, behavior = 'smooth'})`. Both defaults preserve the old behaviour, so
    `zoomToFocus()` and the image-load handler are untouched. Two callers change:

    - `refitScanToPane()` passes `centreFocused: false` - a resize is a request to
      keep the view STILL, not to travel to the focused word, and it is the call
      that repeats.
    - `restoreZoomAfterFocus()` passes `behavior: 'auto'` - a settle lands in one
      frame instead of animating for ~300ms where a refit can fire mid-scroll.

    ### THE TEST WAS BLIND FIRST, AND THE MUTATION IS WHAT SAID SO

    `test_resizing_the_pane_does_not_chase_the_focused_word` passed against BOTH
    the fix and the mutation on its first cut. The reason is worth keeping: at
    100% the page fits its pane vertically, so "park the view away from the word"
    moved nothing, and before/after were identical no matter what the code did.
    Second cut zooms in until the pane genuinely overflows and asserts the
    precondition (`overflow > 200px`), then parks at whichever END is farther
    from where the zoom left the view - the first attempt parked at the bottom,
    which the zoom had already centred on, and moved 11px.

    Now fails under both mutations with the same message - "the resize moved the
    view from 0.310 to 0.665 of the page". Lesson 42, twice in one item: a
    mutation that does not fail is a finding about the test.

    UI suite 103 passed / 1 skipped.

    ### What this cost, and the pattern across 0DH/0DI/0DJ

    Three reviewer reports in a row on one gesture, each fixing the last one's
    side effect: the cursor snap (`0DH`), the flicker it made visible (`0DI`),
    and the stutter `0DI` caused (`0DJ`). The through-line is a LIFETIME
    assumption nobody had written down - "a focus box is short-lived" - which two
    separate pieces of code depended on without saying so. Changing the lifetime
    was correct; what was missing was asking who else read that state.

0DI. **[2026-09-08, reviewer] "WHEN I CLICK AWAY THE SCAN PANE FLICKERS." IT WAS
    THE PANE BEING SENT TO TWO PLACES ON ONE FRAME. FIXED BY NOT CLEARING THE
    SCAN FOCUS - WHICH REVERSES HALF OF A 2026-08-26 DIRECTIVE, SAID PLAINLY.**

    ### Not caused by the day's work, and that was checked first

    The report landed right after `0DG`/`0DH` touched this exact gesture, so the
    first question was whether it was a regression. Instrumented the dismissal on
    the current code and on `HEAD~1` (before both changes): **identical** - two
    distinct scan-pane states inside 36ms, either way. Pre-existing.

    ### What it actually was

    `dismissPanels()` called `clearScanFocus()`, which did two things in the same
    tick, each with its own scroll target:

        showPage(currentPage, scanFocusKlalId, null)
            -> empties hlContainer, drops the word's yellow box, draws the
               whole-klal gold outline, and rAFs box.scrollIntoView({block:
               'nearest'}) to bring THAT into view
        restoreZoomAfterFocus()
            -> applyZoom(0.5, 0), whose own comment reads
               "no focused box left to centre on: show the page top"

    One aims at the klal region, the other at the top of the page, on the same
    frame - with the highlight layer emptied and rebuilt in between. Measured
    through the dismissal, sampling every 8ms:

    | | distinct scan-pane states |
    |---|---|
    | before | **2** (focused box -> gold outline -> boxes rebuilt, t=21 then t=36) |
    | after | **1** (nothing changes; the word stays focused) |

    ### THE PIXEL PROBE WAS BLIND, AND IS RECORDED AS SUCH

    A screenshot-per-40ms capture of the scan pane reported **0 visual changes**
    - because each screenshot costs about 40ms and the whole transient is over in
    36. It "passed" against the defect it was written for, which is Lesson 43
    exactly. The DOM sampler at 8ms is what saw it. A slow probe is not evidence
    of absence.

    ### The fix, and the directive it reverses

    `dismissPanels()` no longer clears the scan focus. `clearScanFocus()` is
    narrowed to `settleScanAfterDismiss()`, which keeps only what a dismissal
    still owes: disarm `_zoomOnFocus` (set by every word click, normally consumed
    by the showPage we no longer call) and restore the zoom.

    **`test_clicking_away_restores_the_zoom_and_the_klal_outline` was pinning the
    OLD behaviour, from an explicit 2026-08-26 request by the same reviewer:**
    "clicking away returns the highlight to the entire klal correctly and should
    also zoom back out to 100". Its two halves are now split:

    - **The zoom half stands, unchanged.** Both zoom assertions still pass
      untouched, including "a manual zoom survives a focus/dismiss cycle".
    - **The outline half is reversed.** Returning the highlight to the whole klal
      IS the rebuild, so it cannot be kept and the flicker removed.

    The test is renamed `..._and_keeps_the_word_focused`, carries both dated
    directives in its docstring rather than letting one quietly replace the
    other, and now asserts the opposite of what it did: the focus box survives
    and `.hl-current-klal` does NOT come back.

    **The zoom still lands correctly because the focus stays.** `applyZoom()`
    centres `.hl-box.focused` whenever one exists and only falls back to its
    anchor ratios when none does - so leaving the word focused turns
    `restoreZoomAfterFocus()`'s "show the page top" into "keep the word centred"
    with no code change to either. One operation, one target.

    Consistent with `0DH` by construction: the text pane snaps the cursor back to
    the last visited word and the scan pane stays on that same word, instead of
    the two disagreeing.

    UI suite 102 passed / 1 skipped.

0DG. **[2026-09-08] `0CA` IS FIXED. IT WAS A CANCELLATION BUG, NOT A TIMING ONE:
    A NAV JUMP LEAVES AN rAF LOOP RUNNING THAT RE-SEATS ITS OWN KLAL 17ms AFTER
    THE REVIEWER CLICKS A WORD. 0/28 FAILURES AGAINST A 5-IN-10 BASELINE.**

    `0CA` handed over a reproduction, a 14ms measurement and an instruction: this
    is an ORDERING bug, start from `_showPageGen`, do not adjust any timing. All
    three were right, and the guard it pointed at turned out to be innocent.

    ### Reproducing it needed the viewport, which is why it hid

    A hand-driven probe against the live server passed 8/8, then 8/8 again with
    the test's nav-click navigation, then 8/8 with the test's own empty-ledger
    server. The variable that mattered was `browser.new_page(viewport={"width":
    1600, "height": 1000})`. Geometry decides which klal the reading line
    resolves to, so a default-viewport probe is a different experiment. Baseline
    re-measured at the real viewport: **5 failed of 10**.

    ### The mechanism, from the instrumented run

        t=1462 enter page=15 gen=4 focusWord=411   at focusWordOnScan (app.js:2018)
        t=1462 >>> WRITE src page=15 gen=4
        t=1479 enter page=14 gen=5 focusWord=None  at setActiveKlal (app.js:4440)
                                                   at tick (app.js:4379)
        t=1479 >>> WRITE src page=14 gen=5

    `jumpTo()` starts `releaseObserverWhenScrollSettles()`, a requestAnimation
    Frame loop that waits for the smooth scroll to stop and then re-asserts the
    jump's destination - `setActiveKlal(lastActiveKlalId)`, which calls
    `showPage(k.page)`, the klal's START page. **Nothing could cancel that loop.**
    A word click sets `suppressObserverScroll` and calls
    `clearTimeout(suppressTimer)`, but a rAF loop is not a timeout, so the jump's
    pending re-seat fires anyway - 17ms after the click's own `showPage` - and
    then clears the suppression the click had just set.

    **`_showPageGen` cannot catch this and is not at fault.** That guard protects
    the box drawing after `showPage`'s awaits; `pageImg.src` is written
    SYNCHRONOUSLY at the top, before any await, so the last caller to ENTER
    showPage wins the image no matter which generation it holds.

    This also explains `0CA`'s strangest datum - that reusing
    `releaseObserverWhenScrollSettles()` as a fix made it fail 10 times in 10.
    That was not a near miss. It was calling the defect.

    ### The fix

    A generation on the settle loop (`_settleGen`) plus
    `cancelPendingScrollSettle()`, called by `focusWordOnScan()`. A superseded
    tick returns without re-seating and without touching
    `suppressObserverScroll` - whoever superseded it owns both. No constant was
    added, changed or removed.

    Lesson 40: a scaffold's teardown is a separate step from putting it up, and
    it is the one that gets forgotten.

    ### Measured, because a single green run means nothing here

    | | result |
    |---|---|
    | baseline, real viewport | **5 failed / 10** |
    | after the fix, batch 1 | 0 failed / 12 |
    | after the fix, batch 2 | 0 failed / 16 |
    | mutation (drop the cancel call) | **2 failed / 10** - the flake returns |

    The mutation is weaker than the baseline because it removes only ONE of the
    fix's two halves: the `myGen` check stays, so a second jump still cancels the
    first. Stated rather than rounded up.

    ### AND A SECOND, PRE-EXISTING FAILURE - found by running the whole suite

    `test_navigating_to_another_klal_closes_the_open_word_panel` also failed, and
    a CONTROL run on the pre-fix `app.js` failed both, so it was not caused by
    this work. It passed 6/6 in isolation and failed only in the full suite.

    **The cause is shared state, and it is a class, not a case.**
    `_find_disputed_klal()` reads `review_queue_part1.json` off disk and so
    returns klal 7 for the whole run, while this module's server writes to ONE
    shared ledger. `test_candidate_override_flow_persists_and_does_not_touch_
    part1json` records an override on klal 7's word; from that moment the word
    stops rendering as `.flag-word.state-open`, and every later test clicking
    that selector waits 5s for an element that will never come back.
    pytest-randomly shuffles, so whether the recorder runs before or after the
    clickers changes per run - which is what made it read as flakiness.

    That is Lesson 36's shape with the shared LEDGER in the corpus's role. Fixed
    with `_find_open_disputed_klal(server)`, which asks the live server what is
    open NOW; all five call sites moved to it. **Full UI suite: 102 passed / 1
    skipped, three consecutive shuffled runs**, from 100 passed / 2 failed.

0DH. **[2026-09-08, reviewer request] DISMISSING A WORD PANEL NOW SNAPS THE
    CURSOR BACK TO THE WORD YOU WERE ON.**

    Reviewer: "when i have a word pop-up and i click away, cursor should snap to
    last-visited word in the middle pane."

    `dismissPanels()` ran `clearScanFocus()`, which runs `clearRoutedWord()` - so
    closing a panel removed the ring and left nothing marking where the reviewer
    had been, in a pane where a klal runs to 1,300 words and the panel's own
    navigation may have scrolled elsewhere.

    `_lastVisitedWord` is recorded in the two FUNNELS rather than at each click
    site: `focusWordOnScan()` (every text-pane word click routes through it) and
    `revealWordInText()` (the scan->text direction). A third copy at the call
    sites is what those funnels exist to prevent.

    `snapToLastVisitedWord()` reuses `revealWordInText()` for the scroll and the
    ring rather than writing a second copy of either, then adds `tabindex="-1"`
    and `focus({preventScroll: true})` so the word is the KEYBOARD cursor too -
    tab order is unchanged, and preventScroll because revealWordInText has
    already scrolled with the observer suppression that scroll requires. Called
    from `dismissPanels()` AFTER `clearScanFocus()`, or the ring would be removed
    a line later.

    `test_dismissing_a_word_panel_snaps_the_cursor_back_to_that_word` asserts all
    three halves - ringed, in view, and holding focus - and scrolls 4,000px away
    first so "in view" cannot pass by accident. Mutation-checked both ways:
    removing the snap call fails it, and keeping the snap but dropping the
    `focus()` fails it on the cursor assertion alone.

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
    | `ligature_words.json` | 7 | 3 (**really 1** - see below) | unrouted |
    | `title_defect_report.json` | 4 | 4 | different address space; reachable via the Heading panel, but nothing points at them |

    **So the genuinely unseen-and-unreviewed set is 123 positions**: 118 lexical
    + 1 ligature + 4 title. Not 580, and not `0CV`'s 136.

    **CORRECTED 2026-09-08, second error in this item's arithmetic.** It first
    said 125, counting 3 ligature positions. **Two of the three were already
    marked resolved in the file I was reading**, and I did not look at the field:

        klal 7   w677  ויגל -> ויגאל   resolved_false_positive:
                                       "ויגל is correct - Psalms 16:9, not ויגאל"
        klal 150 w443  אוף  -> אלוף    resolved_false_positive:
                                       "אוף is real Aramaic ('also'), not a collapsed אלוף"

    `positions()` in the measuring script keyed on `(klal_id, word_index)` and
    never read `resolved_false_positive`, so a finding somebody had already
    settled counted as one nobody had seen. The rebuild's own stage-5b output
    prints "of the candidates, N are already-resolved false positives, marked as
    such" - the information was on screen during the run that produced the wrong
    number. Same shape as this item's other correction: a measurement believed
    because it was mine.

    ### THE STRUCTURAL REPORT IS DONE, which `0CV` could not have known

    15 of its 17 invisible rows carry `acknowledged: true` - the reviewer checked
    them in `0CX`. The 2 that do not are klal 144 w837 (`ה` -> `ח`) and w839
    (`ו` -> `י`), both `enumeration_break`.

    **CORRECTED 2026-09-08: this entry first called those two "exactly the false
    positive `0DE` finding 6 predicts". THAT WAS WRONG, and it was repeated to
    the reviewer twice before being checked.** They are TRUE positives, and this
    file already said so - `build_structural_defect_report.py`'s own header
    records them as confirmed against the scan: "page 52's right margin carries
    ten markers, and DocAI read the 8th `ח` as `ה` and the 10th `י` as `ו`, both
    plain misreads of letters the sequence already determined." klal 144's run
    DOES start at א (`אבגדהוזהטו`), so finding 6's start-at-א assumption never
    applied to it. They are unacknowledged because they are real open findings.

    The error is Lesson 19's shape applied to a write-up: a plausible connection
    between two things in the same paragraph, asserted without opening the file
    that would have refuted it in one line. Finding 6 is still a real latent
    defect; it is simply not the explanation for these two.

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
