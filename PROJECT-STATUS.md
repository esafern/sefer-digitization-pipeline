# Project Status — Open Items & Investigation Log

**This file holds the current, live state only** — what's fixed, what's
open, what to do next — and is kept short enough to read in full every
session, per CLAUDE.md's "read PROJECT-STATUS.md at the start of every
session, no exceptions." **Split 2026-08-12** from a single 6,175-line/
372KB file that had grown past what a single `Read` call can load; the
full dated investigation history (every entry that used to live below
this point, byte-identical, nothing deleted or rewritten) now lives in
`PROJECT-STATUS-HISTORY.md`. Read that file for the evidence trail behind
any specific finding referenced here, or when grepping for how a past
issue was resolved. **New dated entries with detailed fix/verification
prose go there, not here** — this file should only ever hold a compact
current handoff, re-written (not just appended to) as state changes.

## ►► SESSION HANDOFF — read this first, 2026-08-14

> **Terminology, user directive 2026-08-15, applies to all future
> sessions**: an issue with the DATA is a "data issue," not a "bug." An
> issue with the CODE is a "bug." Added to CLAUDE.md as the durable
> home for this rule (so it survives this file's own "re-written, not
> appended" handoff churn) - noted here too for immediate visibility.

### State on disk right now (verified, not remembered)

- **Branch `master`, HEAD `22aa2c4`.** Working tree is clean. No open
  worktrees (`git worktree list` shows only the main checkout).
- **Review dashboard is running** (`python3 review_server.py`, port 8420,
  PID logged to `/tmp/review_server.log`) on the CURRENT code - restarted
  three times this session (2026-08-14): a `FLAG_LABELS` change, the
  full-pipeline-revalidation merge (`_merge_decision` performance fix),
  and the test-suite-expansion merge (another new `FLAG_LABELS` entry,
  `"unverified"`). No restart needed going forward - part1.json/decision
  edits since then don't require one (`review_server.py` reads fresh off
  disk every request).
- **DONE - dropped-lamed ligature pattern: root cause found, ALL 130
  corrections applied (`c7426d9`, `4b30c69`, plus the group-3 batch
  below).** Root cause: this print sets א+ל as a single ligature glyph
  (U+FB4F) that DocAI reads as a bare א, silently dropping the lamed -
  confirmed by three independent signals on 23 scan-verified instances
  (0 print-faithful, 0 ambiguous). 122 corrections (117 mechanical + 5
  found by a prefix-sweep the original scan missed) applied first across
  50 klalim; a genuinely new test failure surfaced along the way and was
  resolved on its merits, not silenced (klal 217's own deliberate
  re-citation of the same Tosafot passage, now correctly self-matching
  after the fix - added to the duplicate-phrase baseline with evidence).
  Separately, the earlier "~620 ambiguous, needs a scope decision"
  estimate was itself inflated (mostly the unrelated citation numeral
  `א'`) - the real set is 228, individually reviewed 2026-08-15, giving
  **8 more genuine candidates**. **2026-08-15, later the same day: all 8
  applied too**, per user go-ahead, same decision/apply pipeline, each
  flagged with an honest confidence note distinguishing them from the
  122 (contextual-reading judgment, not a deterministic dictionary
  lookup or individual scan check - klal 200's `אליהו` attribution is
  the lowest-confidence of the 8, worth a second look). 8/8 verified
  correct at their recorded positions post-apply; `git diff` shows
  exactly 7 changed part1.json lines (klal 69 took 2 of the 8
  corrections). Third `rebuild_all.sh` run clean, no new test
  surprises this time. **Total: 130 corrections across 51 distinct
  klalim, 0 known remaining candidates from either review pass.** Full
  detail in
  `PROJECT-STATUS-HISTORY.md`'s newest entry. 74/74 pytest + 11/11
  Playwright passing.
- **DONE 2026-08-15 - dropped-lamed items 1 & 2: detection script +
  regression test, and a targeted `lexicon.txt` purge.** Per user
  request ("do 1 and 2" from the open-items list above).
  **Item 1**: a true ingest-level fix ("map the ligature codepoint")
  turned out to be impossible - `docai_word_boxes/` contains zero U+FB4F
  characters anywhere, so DocAI's own recognition already collapses the
  ligature to a bare א before this repo ever sees the text; there is
  nothing to map. Built instead: `detect_ligature_corruption.py` (new,
  standalone, read-only), a generalized, re-runnable version of the
  investigation's methodology (exact + full Hebrew-prefix sweep,
  frequency-based candidate scoring, gershayim exclusion, a separate
  "ambiguous with a common standalone word" bucket for the group-3-style
  short forms that need context review rather than blind trust) -
  usable on any `part*.json` file, though running it against Parts 2-3
  is explicitly NOT the same as scoping Parts 2-3 correction work (see
  finding below). Also added `test_part1_no_dropped_lamed_ligature_
  corruption` to `tests/test_corpus_invariants.py`'s zero-tolerance gate
  - a permanent regression guard against the 22 known-corrupt forms
  reappearing in Part 1. **Caught a real scoping bug in its own first
  draft**: the test initially used the `all_klalim` fixture (all 3
  parts) and immediately failed with hundreds of hits in Parts 2-3's own
  text - correctly rescoped to `part_klalim["part1.json"]` before
  merging; verified both that it now passes on the real corpus and that
  it still fires on a deliberate mutation (injected `אא` into klal 1,
  confirmed red, restored byte-identical).
  **The new detection script immediately found one real, previously-
  missed instance**: klal 92 word 444, `לאופי`→`לאלופי` - missed by the
  original mechanical sweep (its base-form list didn't include `אופי`)
  and by the 23-instance scan-verification pass (different curated
  list). High confidence, not scan-verified: the identical phrase
  `לאלופי דורות משעה` appears CORRECTLY three more times in the same
  klal. Applied via the same decision/apply pipeline. **Corrected total:
  131 corrections across 51 klalim.**
  **Item 2**: no independent external Hebrew/Rabbinic dictionary is
  integrated into this pipeline, so a full re-derivation wasn't
  possible - did a targeted purge instead. Read `archive/scripts/
  build_lexicon.py` (the original, one-time build script) first: it only
  ran shape-based heuristics (repeated letters, sofit placement, length)
  against the corpus's OWN text, with zero semantic/dictionary grounding
  - confirming exactly why it "validated" `אא` and friends as legitimate
  words. Removed the 24 confirmed-corrupt base forms from `lexicon.txt`
  (19039 -> 19015 words), after checking each had ZERO remaining
  legitimate use anywhere in Part 1's ~52,600 words post-fix (a complete-
  accounting argument, not guesswork) - including extra care on the 3
  forms with a plausible unrelated meaning in general Hebrew/Aramaic
  (`אמא` "mother"/"there", `בצלא` "in the shadow of", `אפא` possibly
  "father") by individually re-reading all 4 of `אמא`'s Part-1 contexts
  before including it (all 4 were unambiguously `אלמא`, the standard
  Talmudic "hence/it follows," e.g. `אלמא קסבר`/`אלמא ס"ל` - standard
  formulaic Talmudic phrasing, not "mother"). File re-verified sorted,
  deduplicated, no empty lines after the edit.
  **Finding, NOT scoping Parts 2-3 work**: checking whether the 24 forms
  were safe to remove (would removal affect a legitimate Parts 2-3 use?)
  required checking their occurrence counts in `part2.json`/`part3.json`
  too - this is a pure lookup, not editorial work, but it surfaced a
  significant fact worth logging per CLAUDE.md's "log immediately" rule:
  **Parts 2-3 have hundreds of unfixed instances of this exact bug**
  (e.g. `אא` alone: 74 in Part 2, 35 in Part 3, vs Part 1's 40 real
  corruptions before today's fix; `איבא`: 70 in Part 2). This is the
  SAME shape as the already-documented page-furniture-contamination
  precedent (rare in Part 1, disproportionately common in Parts 2-3,
  cause unexplained) - independent evidence for the standing directive's
  own reasoning ("if part 1 is bad the rest won't magically be better"
  cuts both ways: a clean Part 1 is not evidence Parts 2-3 will be
  clean, and this is now a second confirmed case of exactly that).
  **Not started, not scoped, not proposed** per the standing gate -
  logged here only because CLAUDE.md requires logging confirmed findings
  immediately, not because it's next.
  Full `./rebuild_all.sh` clean, 75/75 pytest + 11/11 Playwright (86
  total) passing.
- **DONE - test-suite expansion/refactor, merged 2026-08-14 (`b30eae5`).**
  Another Opus 5 subagent, same isolated-worktree pattern, built out
  regression coverage for main-pipeline decision logic that had none
  (test count 20 -> 85: 21 corpus invariants + new `tests/
  test_pipeline_logic.py`'s 53 hermetic unit tests, both gated in
  `rebuild_all.sh`; 11 Playwright tests, up from 5). Found and fixed a
  real gap while writing tests: `classify()`'s `"unverified"` fallback
  flag had no `FLAG_LABELS` entry - same class as `stale_candidate`
  found by code review a few hours earlier, this time caught by a test
  instead. Independently re-verified before merging: full suite re-run
  in the main repo (74 pytest + 11 Playwright, all passing); the
  `check_klal_token_orphans.py` refactor confirmed byte-identical output
  (redone in-place after an initial `/tmp`-path-resolution false alarm -
  same mistake and same fix as the previous merge); mutation testing
  spot-checked directly (broke `check_drift`'s klal-missing branch,
  confirmed exactly the relevant new test went red, restored byte-
  identical); full `./rebuild_all.sh` clean post-merge, zero data drift.
- **CLAUDE.md corrected 2026-08-14**: it had drifted from reality the
  same way script docstrings have in the past (Lesson 19's pattern, now
  confirmed in the durable-rules file itself, not just a script) -
  `chunker.py` was described as live but is archived; `build_vlm_demo.py`
  was listed as an "active root script" in one paragraph while a
  different paragraph in the SAME file already said it was archived (an
  internal contradiction); `validate_title_section_letter.py` was listed
  as active but is archived too; `validate_catchword_continuity.py` is
  live but was missing from the list entirely. All verified against an
  actual `ls`/`archive/` check before correcting, not assumed. Also
  restructured "Directory layout" (was one long run-on bullet) into
  role-grouped sub-bullets, fixed a duplicated heading and a repeated
  sentence, and added `audit_applied_decisions.py` (new today) which
  wasn't documented there yet. Full diff in commit `c460eea`.
- **DONE - full-pipeline revalidation/refactor, merged 2026-08-14
  (`85624f7`).** Per explicit user request, an Opus 5 subagent ran in an
  isolated git worktree (never touched the live dashboard or this branch
  while running) doing a full revalidation-and-refactor pass over the
  MAIN pipeline, deliberately excluding witness/punctuation. **16
  findings, all fixed** - full detail in item 9 below and
  `PROJECT-STATUS-HISTORY.md`'s newest entry. Before merging, every
  finding was INDEPENDENTLY re-verified (not just trusted from the
  agent's report): the prompt-template extraction confirmed byte-
  identical to the pre-change f-string by direct comparison against git
  history; the cache migration confirmed lossless (419 rows before/after)
  and idempotent; all corpus/derived data files confirmed byte-identical
  across the whole change set; the `review_server.py` refactor confirmed
  to produce byte-identical API responses via a live side-by-side diff
  against the unmodified server on 7 endpoints; the catchword-validator
  fix confirmed to change exactly the one claimed output line (a first
  comparison attempt gave a misleading large diff - traced to a `REPO`-
  path resolution artifact in the verification script's own methodology,
  not a real discrepancy, and redone correctly before trusting it). Full
  `./rebuild_all.sh` (with vision) run clean post-merge: all cache hits,
  0 live API calls, 15/15 pytest, 5/5 Playwright, zero data drift.
  Worktree and its branch deleted after merging.
- **NEW, IMPORTANT, NOT YET RESOLVED - possible systematic dropped-ל
  pattern found 2026-08-14 by a semantic-plausibility spot-check** (an
  Opus 5 subagent read a random ~20% sample of Part 1 by word count -
  10,858 of 52,609 words, 59 of 222 klalim, seed 20260814 - for sentences
  that read as scan-corruption-shaped gibberish in context, calibrated
  hard against flagging normal terse/citation-heavy Talmudic style).
  Headline finding, independently confirmed by direct corpus word-count
  (not just trusted from the agent's report): `אא` appears **45** times
  in `part1.json` against `אלא` appearing 237 times - and multiple other
  words show the same shape (`איבא` 12 vs `אליבא` 21, `שמוא` 7 vs
  `שמואל` 45, `אעזר` 9 vs `אלעזר` 10, `אהים` 7 vs `אלהים` 3, etc.) - ~86
  mechanically-countable instances across ~29+ klalim, all missing
  specifically the letter ל (the one Hebrew letter with a tall ascender -
  a plausible but UNCONFIRMED mechanism hypothesis, not a finding). 33
  `klal_flag` decisions recorded in `review_decisions.jsonl`
  (`reviewer: "ai-semantic-spotcheck"`, `needs_revisit: true`) - confirmed
  landed correctly (grep count matches, sample entry read back clean,
  live on the running dashboard via `/api/klal/92`). No `part1.json` edit
  was made - correctly, per Lesson 9 (semantic signal alone is not
  sufficient) and Success Criterion #1 (never correct without checking
  the actual scan).
  **ROOT CAUSE FOUND AND CONFIRMED AGAINST THE INK, 2026-08-14 (second
  pass, 23 scan-verified instances). It is a genuine EXTRACTION BUG, not
  a print anomaly: this Livorno print sets the letter pair `אל` as the
  single ALEF-LAMED LIGATURE glyph `ﭏ` (U+FB4F), and DocAI reads that one
  glyph as a bare `א`, silently dropping the lamed component.** Every
  affected word form is exactly a word where a `ל` immediately follows an
  `א` - `אלא`→`אא`, `אליבא`→`איבא`, `אלעזר`→`אעזר`, `שמואל`→`שמוא`,
  `אלהים`→`אהים`, `ישראל`→`ישרא`, `אלפא`→`אפא`, `אלעאי`→`אעאי` - which is
  the mechanism's fingerprint, not a coincidence.
  Evidence, three independent signals agreeing (Lesson 9):
  (a) **Pixels.** 600-1800 DPI crops of 23 instances across 22 klalim and
  21 different pages (31-76): in every one, the disputed `א` carries a
  tall hooked lamed ascender, while plain alefs on the SAME LINE
  (`ביתא`, `ורבא`, `תנא`, `בתירא`, `הביא`, `יצא`) have no ascender at
  all. Negative control passed: klal 44's `א"א` (a real abbreviation,
  `אשת איש`) shows two plain alefs with a gershayim and NO ascender on
  either - so this is a real discrimination, not "ascenders seen
  everywhere."
  (b) **Cross-engine.** On page 40 (klal 88) the VLM extraction reads the
  same glyph as a bare `לא` - keeping the lamed, dropping the alef -
  where DocAI read `אא`. Two engines splitting one composite glyph in
  complementary directions is the signature of an unmapped ligature. The
  same VLM page also reads `ר' אלעזר` in full where the print uses
  separate sorts, so the ligature is used INCONSISTENTLY by the
  compositor (normal for hand-set type), which is why the corrupt and
  correct spellings coexist in the corpus.
  (c) **Semantics.** Every reconstructed reading is the contextually
  correct word (`אינו אלא לא תעשה`, `קודם אלפא ביתא`, `בארץ ישראל`).
  **This OVERTURNS the earlier same-day read of klal 199 word_index 38**,
  which this file previously recorded as "two adjacent alefs with NO
  lamed - transcription faithful to the ink." Re-cropped at 1800 DPI with
  the following word `לא` (which carries a standalone lamed) inside the
  same frame as an anchor control: the token's first glyph has an
  ascender identical in shape to that standalone lamed, and the alef of
  the preceding `אינו` has none. The ink reads `אלא`. The earlier read
  counted two glyphs and missed that the first glyph carries two letters.
  It is therefore **NOT** the klal 88 `רתם`/`התם` class, and the
  editorial-awareness-only disposition proposed on the basis of that one
  instance does not apply.
  **Result: 23 of 23 scan-verified instances are extraction bugs; 0
  print-faithful; 0 ambiguous.** No corpus edit made - 23 `klal_flag`
  decisions recorded in `review_decisions.jsonl`
  (`reviewer: "ai-scan-crop-verification"`, verified live on the
  dashboard via `/api/klal/199/flag`), each naming the word, word_index,
  docai page/token, and the confirmed read, flagged as needing a
  `manual_correction` decision from a human.
  **SCOPE, revised (the earlier "~86" was both under- and over-counted).**
  5 of the 45 `אא` tokens are the genuine abbreviation `א"א` and are NOT
  part of the pattern. Against that, the pattern is wider than the 8
  word-forms originally listed: a mechanical sweep for "inserting `ל`
  immediately after an `א` yields an attested corpus word" found 117
  occurrences of 22 confirmed-corrupt forms across 48 Part-1 klalim
  (adds `איביה` 5, `איעזר` 4, `אמא` 4, `ישמעא` 4, `איבייהו` 3, `אגאזי` 3,
  `ושמוא` 3, `דשמוא` 2, `בצלא` 2, `איה` 2, `האה` 2, `אה`, `האף`, `וכאה`);
  a follow-up systematic PREFIX sweep (the exact-match scan above only
  checked bare forms, missing a `ל`/`ו`/`ב` prefix stuck to the front)
  found **5 more genuine instances** of the identical mechanism:
  `בשאה`→`בשאלה` (klal 103, a halachic term - vow annulment via
  she'ela), `ואהים`→`ואלהים` (×2, klal 69), `והאף`→`והאלף` (klal 138),
  `לאפא`→`לאלפא` (klal 75, same "אלפא ביתא" phrase already confirmed
  elsewhere) - and correctly REJECTED one coincidental false match from
  that same sweep (`מאה`, klal 92, is just the ordinary word "hundred,"
  at home in a list of "thousand, hundred, one," not a corrupted form).
  **Total 122 occurrences across 50 klalim.**
  **APPLIED 2026-08-15.** Per direct user instruction ("1 and 2 apply...
  of course flag for human review"), all 122 were recorded as
  `manual_correction` decisions (`reviewer: "ai-dropped-lamed-
  correction"`, each note distinguishing whether that specific instance
  was individually scan-verified (23 of them) or applied on the strength
  of the confirmed mechanism plus its own fingerprint match (the other
  99) - a human should still spot-check the unscan-verified ones) and
  promoted into `part1.json` via `apply_reviewer_decisions.py`. Verified
  before committing: all 122/122 read back correctly at their recorded
  positions (0 mismatches); `git diff --stat part1.json` shows exactly
  50 changed lines, matching the 50 distinct klalim touched; two full
  `./rebuild_all.sh` runs (with vision) completed clean. One real test
  failure surfaced and was resolved, not silenced: fixing klal 217's
  word 571 (`אליבא`, itself one of the 23 scan-verified instances) made
  it byte-identical to the klal's OTHER, already-correct occurrence of
  the same 10-word Tosafot quotation - `tests/test_corpus_invariants.py`
  correctly flagged this as a new intra-klal duplicate phrase; confirmed
  genuine (the author explicitly re-cites the same Tosafot a second
  time, `גם הלום ראיתי מה שכתב הרב הנזכר שם בשם התוספות`) and added to
  `INTRA_KLAL_DUPLICATE_PHRASE_BASELINE` with the evidence inline, same
  as the 3 already-baselined genuine repeats (klal 65/189/198). Final
  state: 74/74 pytest + 11/11 Playwright passing.
  **The ~620-instance "ambiguous, needs scope decision" estimate was
  ALSO wrong** - it counted every gershayim-stripped match, so ~386 of
  the reported 395 `א` instances were actually `א'` (the citation
  numeral "1"), unrelated to this pattern entirely. The real ambiguous
  set is **228** (`או` 117, `אי` 89, `איהו` 11, `א` 9, `וא` 2), and per
  user instruction ("group 3 review yourself and report") all 228 were
  read in context 2026-08-15 (the small groups individually, the two
  large groups via structural filtering + random-sample validation - see
  full method and results in `PROJECT-STATUS-HISTORY.md`). Result: `אי`
  (89) is essentially clean (standard Talmudic "if," no genuine
  candidates found). **8 genuine candidates identified, NOT YET APPLIED
  - awaiting a decision**: klal 158/168 (`או`→`אלו`, "these" not "or");
  klal 69 (×2)/198 (`א`→`אל`, divine-name context and a biblical
  quotation, `אל תאמר בלבבך`); klal 169/176 (`וא`→`ואל`, the same
  phrase - `כי אל דעות ה'`, 1 Sam. 2:3 - appearing independently
  corrupted the same way in two different klalim); klal 200 (`איהו`→
  `אליהו`, a book title, lower confidence on the exact attribution than
  the others). None of these 8 are individually scan-verified.
  **SECONDARY FINDING**: every corrupt form (of the 122, before
  correction) was present in `lexicon.txt`, so lexicon validation
  structurally could not have caught this class of error - CLAUDE.md's
  "zero flagged items in lexicon validation" bar was being met the whole
  time. A lexicon re-derivation from an independent source (not this
  corpus's own output) would close this gap; not done.
  **NOT YET DONE**: no fix to the extraction stage itself. The durable
  repair is to make the DocAI-ingest path map the ligature codepoint (and
  the glyph DocAI substitutes for it) to `אל`; nothing in the pipeline
  does this today, and `docai_word_boxes/` contains zero `ﭏ` characters,
  so the loss happens inside DocAI, before this repo sees the text.
  Parts 2-3 are almost certainly affected the same way but are out of
  scope per the standing directive.

### `lexicon.txt` cannot catch the ligature corruption - it contains it

Found 2026-08-14 while scoping the above. `אא`, `אעזר`, `שמוא`, `אהים`,
`איבא`, `ישרא`, `אפא`, `אעאי`, `ישמעא`, `אמא`, `אגאזי`, `ושמוא`,
`דשמוא`, `איעזר`, `איביה`, `בצלא` are ALL present in `lexicon.txt` as
"validated Rabbinic Hebrew words." The lexicon was built from this
corpus's own output, so it absorbed the corruption and now certifies it.
This is exactly CLAUDE.md Lesson 3 ("never trust a derived/aggregate
artifact as ground truth") with a concrete cost: CLAUDE.md's "Conventions
observed" bar - "every cleanup pass targets zero flagged items in
`lexicon.txt` validation" - was being met while 117+ corrupted words sat
in Part 1, because the dictionary the check validates against was
downstream of the bug. Any lexicon-based validation result predating this
finding should be read as no evidence either way on this class of error.
A lexicon re-derivation from an independent source is the fix; not done.
- **Every previously-tracked corpus-content gap is closed** (klal 5, 29,
  30/75/88, 37, 69, 206, 217; the second source-audit round's 12 confirmed
  bugs; the reindexing incident's 3 root causes - all fixed, verified
  against real data, and committed). `rebuild_all.sh`'s pytest gate is
  now two files - `tests/test_corpus_invariants.py` (21) +
  `tests/test_pipeline_logic.py` (53, new 2026-08-14) - 74/74 passing;
  `tests/test_review_server.py` (11 more, Playwright, deliberately not
  part of the automated gate) is 11/11. Full evidence for all of the
  above is in `PROJECT-STATUS-HISTORY.md`.
- **This session's work (2026-08-13/14), all committed, full detail in
  `PROJECT-STATUS-HISTORY.md`'s two newest entries**:
  1. New reviewer feature: flag/replace/delete ANY word in a klal's text,
     not just machine-flagged ones (`manual_correction` decision type,
     `POST /api/decisions/manual`, arm/confirm delete pattern in the UI).
  2. Corpus-wide fix: 2,548 instances of a stray space before an
     abbreviation geresh (printer's mark), across 201 klalim.
  3. Reindexing incident from #2's `--skip-vision` rebuild (stale
     candidate positions, 10 orphaned human decisions, one independent
     `api_klal()` drift-check bug) - fully diagnosed and recovered, 0
     mismatches left.
  4. Multi-word disagreement highlighting bug (witness + candidate
     panels bracketed only the first word of a multi-word span) - fixed,
     user-confirmed working.
  5. Witness bbox line-wrap bug: a multi-word span crossing a line-wrap
     got a bbox unioned across both lines (up to 75.6% of page width),
     which geometrically overlapped and stole clicks from smaller boxes
     underneath. Fixed by anchoring the bbox to only the anchor token's
     own line. 11 of 419 witness items affected, all corrected.
  6. klal 3's 4 self-identified test-garbage decisions removed from
     `review_decisions.jsonl` (deliberate, explicit user-requested
     exception to the normal append-only rule).
  7. klal 30/docai_token_index 22 flag closed - user directly confirmed
     `וכו` is correct.
  8. Validator review: read all 5 active validator scripts against their
     own docstrings, found and fixed 2 real bugs (`validate_catchword_
     continuity.py`'s `HEADER_WORDS` wrongly included the bare word
     `כלל`; `validate_title_alphabetical_order.py` silently skipped
     titles with a non-Hebrew first character instead of reporting them
     - klal 353, Part 2, is the one current instance).
  9. **Full-pipeline revalidation & refactor pass** (user directive:
     "revalidate and refactor entire process - not just recently changed
     scripts", witness/punctuation deliberately excluded). Read every
     `rebuild_all.sh` stage, all 5 validators, the pytest gate, the
     decision/apply layer and `review_server.py` + `review_frontend/`'s
     candidate plumbing against their own claims and against real data.
     **16 findings, all fixed and individually verified** - full detail in
     `PROJECT-STATUS-HISTORY.md`'s newest entry. The one that matters most:
     `verify_corrections_vision.py`'s cache key did not cover the PROMPT
     TEMPLATE, so the 2026-08-12 prompt fix only landed by luck (an
     unrelated schema change had dropped every row two days earlier) and
     the same edit today would have been a silent no-op. Closed with a
     `prompt_hash` key component and a lossless back-filling migration -
     419 cached answers kept, 0 API calls spent. Also: a JSON-unescape gap
     in this file's lenient response parser (same class as the witness
     script's, which PROJECT-STATUS.md had flagged here as un-audited);
     a corpus-wide whitespace invariant now gating the two coexisting
     word-index schemes; `check_klal_token_orphans.py`'s
     `best_match_owner` ignoring its `self_kid` argument; a
     `HEADER_WORDS` false-furniture hit eating the citation `י"ד` on 43
     tokens; and several docstrings/comments claiming coverage, constants
     or file locations that do not exist. Every change verified by a full
     `./rebuild_all.sh` (with vision) producing byte-identical derived
     JSON, 15/15 corpus tests, 5/5 Playwright browser tests.

### DONE, AWAITING MERGE - test-coverage expansion + test-suite refactor (worktree `agent-a8a04e346269f3067`, 5 commits), 2026-08-14

**Merge note**: `review_server.py` changed (one new `FLAG_LABELS` entry), so
the live dashboard needs a restart after merging - Python constants there do
not hot-reload the way the data files do. No corpus, derived-data, cache or
decision-log file was touched: `git diff` against the worktree base shows
only `CLAUDE.md`, `PROJECT-STATUS.md`, `check_klal_token_orphans.py`,
`rebuild_all.sh`, `review_server.py` and the three test files. A full
`./rebuild_all.sh --skip-vision` was run with the new two-file gate: 74/74
pass and all five derived JSON files are sha256-identical to before.

Separate, complementary follow-up to the revalidation pass above (which
fixed 16 bugs but added only ONE test): systematically build regression
coverage for main-pipeline logic that had none, and clean up the two
existing test files. Same scope rules - witness/punctuation excluded.

- **`apply_reviewer_decisions.main()`'s per-run safety model covered end to
  end** (5 tests, against throwaway copies of part1.json/corrections/the
  decisions log - nothing tracked is touched): a "keep the current text"
  vote on an INSERT candidate deletes nothing (finding ★1, where it
  silently deleted exactly what the reviewer voted to keep) and is still
  recorded as a reviewed no-op; at most one word-count-changing decision
  lands per klal per run; a decision with an `apply_event` on record is
  never applied twice (the `יגעתי 1 1 1 ולא` bug); a drifted candidate is
  skipped AND not recorded as applied; plus a positive control (a clean
  replace really does land), without which a mutation making `main()`
  refuse everything would pass all four refusal tests.
- **NEW `tests/test_pipeline_logic.py` (53 tests), wired into
  `rebuild_all.sh`'s step 6/6 gate alongside the corpus suite.** Pure
  unit tests, hermetic (no network, no API key, no scan cache, no writes
  to any tracked file - temp dirs only, via `review_decisions.py`'s own
  `path=` parameter). It covers logic that is INERT on today's real data
  and therefore invisible to any corpus-level check: `assemble_
  corrections_dataset.py`'s `check_drift`/`live_word_span` (0 candidates
  currently drift) and `classify`'s confidence gating; every
  `apply_reviewer_decisions.py` mutator, including the re-apply guard that
  produced `יגעתי 1 1 1 ולא` in 2026-08-11; `review_decisions.py`'s
  append-only/latest-per-key contract; `audit_applied_decisions.py`'s 3
  checkers and `is_superseded_by_later_applied` (the klal 1 word 97
  precedent, as a permanent test rather than a one-off check);
  `verify_corrections_vision.py`'s `extract_json_fields`/
  `unescape_json_fragment` and the FULL cache key - every component
  (crop, word_a, word_b, context, prompt_hash) asserted to actually
  discriminate, plus the migration's losslessness/idempotence;
  `build_klal_page_regions.py`'s heuristic fallback path (internal
  consistency only - it has no ground truth to assert against, see below).
- **6 new zero-tolerance tests in `tests/test_corpus_invariants.py`**
  (15 -> 21), all on the review layer's derived files, all confirmed
  clean against the current corpus: no `stale_candidate` flag is being
  served; every served flag has a `FLAG_LABELS` entry; every candidate's
  `word_index` points inside its own klal (delete's append position
  allowed); each opcode's field shape (`replace`/`insert`/`delete` null
  patterns + normalised bbox); every trusted klal has exactly one
  well-formed scan region agreeing with its aligned page, continuations
  strictly increasing; `review_decisions.jsonl` is intact (parseable,
  unique ids, valid decision_types, apply_event refs resolve, int
  klal_ids, word_index null iff klal_flag, chronological order).
- **REAL FINDING, fixed: `classify()`'s `"unverified"` fallback flag had
  no `FLAG_LABELS` entry** - the identical gap as `"stale_candidate"`
  (found in code review a few hours earlier), found this time by the new
  test rather than by a human reading the code. Unreachable today
  (`build_corrections_dataset.py` only emits difflib's three opcodes),
  but the fallback exists for the unexpected case, which is exactly when
  rendering it as an anonymous "Flagged" would be worst. Added
  `"unverified": ["Unclassified (unexpected opcode)", "#718096"]`.
  **Needs a `review_server.py` restart to take effect once merged** -
  server-side Python constants don't hot-reload the way data files do.
- **Standalone-validator coverage added (second batch, same file):**
  `check_klal_token_orphans.py`'s Pass-3 allowlist (the exact investigated
  span still suppressed; a DIFFERENT span in klal 4/18/34 NOT suppressed;
  the allowlist structurally proven to be span-keyed, not klal_id-keyed;
  every stored span proven already-normalised, since an unnormalised one
  could never match and the suppression would be silently dead) and
  `best_match_owner`'s self-exclusion; `validate_part1_corpus_integrity.py`'s
  three GATED checks proven able to FIRE (a wrong gematria field, a wrong
  opening word, Latin/digit/bracket damage, a real duplicated phrase) as
  well as to stay quiet on their documented exemptions (klal 166's geresh,
  the two footnote-marker conventions, the same-title cluster) - per Lesson
  2, a gate that cannot fail is indistinguishable from one that passes, and
  all three of these had false-positive sources removed from them in the
  past, any of which could have been over-corrected into blindness;
  `validate_title_alphabetical_order.py`'s unrankable-first-character
  reporting and its contiguity detection; `validate_catchword_continuity.py`'s
  `is_header_word` (the `י"ד`-eaten-as-furniture fix from earlier today).
- **One small enabling refactor**: `check_klal_token_orphans.py`'s Pass-3
  suppression rule extracted from an inline expression in `main()`'s loop
  into `is_known_pass3_false_positive(klal_id, missing_words)`. Behaviour
  verified unchanged by diffing the full script output before/after against
  a `git stash`ed baseline (byte-identical, including the "3 known false
  positive(s) suppressed" line).
- **`tests/test_review_server.py`: 5 -> 11 tests, plus a refactor.** New
  API-level tests (no browser): a `manual_correction` whose snapshotted
  `original_word` no longer matches the live text at that index is NOT
  rendered by `/api/klal` (the drift check added earlier today - the only
  decision type that used to render unconditionally), a missing
  `chosen_text` is rejected 400 while `""` legitimately means delete, and
  every flag `/api/klal` actually serves has an `/api/flags` label
  end-to-end. New Playwright tests for `refreshKlalimList()` (written
  earlier today, verified then only by ad-hoc browser automation): three
  concurrent refreshes fire exactly one round of `/api/flags`+`/api/klalim`
  +`/api/witness`; a failed refresh is caught, logged, and leaves the
  in-flight guard cleared so the next one works; the active nav row AND the
  flagged-only filter both survive `buildNav()`'s full innerHTML rebuild.
  Refactor: `_get_json`/`_post_json`/`_open_dashboard` helpers replace the
  goto+wait+click+urllib boilerplate repeated across the existing tests
  (assertions unchanged), and the new nav test flags its own klal via the
  API instead of depending on an earlier test having flagged one.
- **Every new test verified to actually FAIL when its invariant is
  violated**, not just to pass: 23 source mutations (drift check
  neutered, confidence gate removed, label deleted, re-apply guard
  removed, negative-index bounds check removed, supersession logic
  loosened, JSON-unescape removed, prompt_hash dropped from the cache
  lookup, `already_done` ignored, append mode changed to write, the
  Pass-3 allowlist reverted to klal_id-only, `best_match_owner`'s
  self-exclusion removed, the gematria field comparison disabled, the
  footnote-marker lookbehind removed, the same-title exemption widened to
  everything, intra-klal duplicate detection disabled, the
  unrankable-title report silenced, the header-word abbreviation guard
  removed, the confirmed-no-op branch narrowed back to replace-only,
  the one-word-count-change-per-run guard removed, the already-applied
  guard removed, the snapshot drift check removed, main()'s decision loop
  emptied) and 15 data mutations (stale flag, unknown flag, out-of-range
  index, broken opcode shape, inverted bbox, missing/malformed/mis-paged/
  zero-token region, duplicate id, bad decision_type, dangling
  apply_event, string klal_id, out-of-order records, truncated line) and
  7 review-layer mutations (refresh dedup guard removed, its try/catch
  removed, the post-rebuild `setActiveKlal` restore removed, the
  `applyFlaggedFilter` re-apply removed, `api_klal`'s manual-correction
  drift check disabled, the missing-`chosen_text` rejection removed, a
  served flag's label deleted, twice - once for an unreachable flag and
  once for a served one). 46 mutations run, 45 red. The one that came
  back GREEN is recorded rather than quietly re-rolled: deleting the
  brand-new `"unverified"` label does not fail the end-to-end API test,
  correctly - no klal currently serves that flag, which is exactly why
  the unit-level "every flag classify() CAN emit is labelled" test
  exists alongside it (re-run against `"current_text_confirmed"`, a flag
  that IS served, it goes red). Every mutated tracked file was restored
  and sha256-verified byte-identical afterwards.
- **Deliberately NOT covered - stated so nobody reads 85 green tests as
  "the pipeline is tested"**: (a) `build_corrections_dataset.py`'s
  difflib alignment and `build_klal_page_regions.py`'s marker-anchored
  Y-banding - the two places where a wrong answer is a wrong CROP shown
  to a reviewer, and neither has any ground truth a synthetic fixture
  could assert against without inventing one (that's what
  `validate_klal_span_coverage.py` + direct crop inspection are for);
  (b) the heuristic regions' real-data geometry beyond structural
  soundness - "does this box actually contain this klal's ink" is a
  vision question, and an overlap check would false-positive on
  legitimately overlapping same-page line boxes; (c) anything that would
  spend an API call (`adjudicate`'s retry/fallback chain is exercised
  only through its cache); (d) witness/punctuation code, out of scope by
  standing directive; (e) `review_frontend/app.js`'s rendering beyond the
  paths the 11 browser tests touch. Coverage here is deep on the
  decision/apply/flag layer and on parsing/caching, and shallow-to-absent
  on alignment geometry.

### `verify_witness_vision.py`'s 419-item pass finished 2026-08-14

All 419 witness-queue items (klal 30/75/88) now carry `vision_selected`/
`vision_transcription`/`vision_confidence`/`vision_reasoning` in
`reconstruction_witness_queue.json`: 382 sided with DocAI ("A"), 16 with
Tesseract ("B"), 21 "NEITHER" (model transcribed a third reading), 0
errors. Confidence was 0.90-1.00 across the board (mean 0.979) - per
Lesson 2, treat that uniformly-high band as a triage prior, not a
certificate; it hasn't been checked against a held-out sample of known-
wrong cases.

**Bug found and fixed in the same pass**: 5/419 items (klal 30 tok 84,
284, 750, 835; klal 75 tok 555) came back from Gemini as `ERROR` because
`sanitize_json`'s repair regex only fixes bad backslash escapes, not a
literal unescaped `"` *inside* a JSON string value - which happens
routinely here because Hebrew gershayim/geresh punctuation inside a
transcribed abbreviation (e.g. `ז"ל`, `הרא"ש`, `כ"ו`) IS a literal `"`
character, and the model didn't escape it despite `response_mime_type=
"application/json"`. Fixed by adding `parse_decision_lenient()` to
`verify_witness_vision.py` (field-by-field regex extraction, used as a
third fallback after `json.loads` and `sanitize_json` both fail) and
wired into the parse chain. All 5 raw responses were already sitting in
`witness_vision_cache.db` (cache_put runs before parsing) as valid,
high-confidence "A" decisions - recovered by re-parsing the cached text
with the fixed parser, at zero additional API cost. Verified: all 419
items now have a non-null `vision_selected` and `vision_confidence`,
file re-validated as parseable JSON. Any future re-run of this script (or
`verify_corrections_vision.py`'s similarly-shaped parser, not yet
audited for the same gap) should hit this fallback automatically if the
same failure recurs.

**Not yet done**: commit `reconstruction_witness_queue.json`,
`witness_vision_cache.db`, and `verify_witness_vision.py` together. This
is still a TRIAGE layer only (per its own design) - it does not record
`witness_choice` decisions itself, so it doesn't close item #2 below on
its own; a human still needs to work through the dashboard.

### NEXT STEPS, in order

**1. DONE 2026-08-14 - drift check added to `assemble_corrections_
dataset.py`.** It now loads `part1.json` fresh on every run and cross-
checks each verified candidate's `corrected_word`/`word_index_in_
final_text` against the LIVE clean_text at that klal_id before serving
it - same shape as `apply_reviewer_decisions.py`'s `snapshot_matches()`.
`replace`/`insert` candidates are checked by exact span match (handles
multi-word spans, same span logic as `apply_replace()`); `delete`
candidates (whose `corrected_word` is null by definition) get a bounds
check only. A drifted candidate is force-flagged `"stale_candidate"`
instead of whatever `classify()` would otherwise compute - `review_
frontend/app.js` treats any flag other than `"current_text_confirmed"`
as its default "open" state, so this required no frontend change. Ran
against current live data: 0 drift detected (expected - the reindexing
incident was already fully recovered), output byte-identical to the
pre-change run, confirming the new check is a pure addition, not a
behavior change on clean data. Unit-verified the detector itself fires
correctly on synthetic replace/insert/delete drift and out-of-bounds
cases before trusting the 0-drift result on real data (Lesson 2 - a
"nothing found" result needs the check itself proven to fire, not just
taken on faith).

**2. DONE 2026-08-14 - klal 30/88 witness items closed.**
   - Klal 30, `part1.json` word_index 501 (space-split scheme): `ידן` →
     `ידו`, applied via the manual-correction feature (`manual_correction`
     id `177240ab78c5`, applied via `apply_reviewer_decisions.py`, verified
     in `git diff part1.json`: `...ושם הראנו ידו הנפלאה ובקיאותו...`).
     **LOWER CONFIDENCE than a normal vision-confirmed correction** - no
     engine or crop directly confirmed `ידו`: DocAI read `ידן`, Tesseract
     read `ידו`, and a direct 900 DPI crop read closer to `ידך` than
     either. This rests on user editorial judgment of what reads naturally
     in context, not a pixel-level confirmation. Did NOT insert `את` before
     `ידו` (`את ידו הנפלאה` vs the applied `ידו הנפלאה`) - that phrasing
     question is still open and deliberately untouched. klal_flag
     `5220cb956175` closed via `fb26188404a5`.
   - Klal 88 - `רתם`/`התם`: no text change. The 900 DPI crop unambiguously
     shows `ר` (high confidence, unlike klal 30) - current text is
     faithful to the print; a source-text/broken-type anomaly, not an OCR
     error, so per fidelity criterion #1 it stays uncorrected. Closed as
     editorial-awareness-only. klal_flag `f15d365a9168` closed via
     `9ee397027685`.
   - Applying klal 30's decision surfaced 3 OTHER already-recorded-but-
     never-applied decisions left over from the 2026-08-13 reindexing
     recovery (`apply_reviewer_decisions.py` applies everything pending in
     one pass, no per-decision selection) - klal 1 word 437 (`ומדקמהד'`→
     `ומדקמהדר`), klal 1 word 85 (`לכן`→`לכו`), klal 3 word 3 (no-op,
     chosen text already matched). User confirmed applying all of it
     together. `./rebuild_all.sh` re-run after, 14/14 tests pass, 0 drift
     flagged by the new drift check (item 1) on the freshly-applied text.

**3. The broader witness queue (tier B/C/D, ~411 items across klal
30/75/88) is still fully open for human review** and is the only real
second opinion on the ~3,800 words reconstructed for those three klalim.
The vision pass (now finished, see above) gives a machine second opinion
per item, but per its own design doesn't substitute for working through
it in the dashboard (page-step to 24/37/40, click a box) - highest-value
follow-up QA, though not a gate on anything. **User explicitly deferred
this 2026-08-14** ("leave that as a future step") after being offered a
narrower option (surfacing just the 37 items where vision disagreed with
DocAI or found neither reading correct) - not started, no scope decided
yet beyond "later."

**4. Unverified risks flagged by the second audit round - 4 of 6
investigated and closed 2026-08-14, 2 still open:**

   - **DONE - apply_event staleness (risk 1).** Built `audit_applied_decisions.py`
     (new, standalone, read-only): for every decision the log claims was
     applied (has an `apply_event`), verifies the live `part1.json` still
     actually reflects it. The concrete precedent this closes: klal 1 word
     97's punctuation decision was accepted, applied, then hand-reverted
     outside the normal apply-script flow (2026-08-10, documented in
     `review_decisions.jsonl` ids `784b22672ac0`/`4759be432a2c`/
     `4e6b53d98d36`) - the `apply_event` for the original accept is still
     on record and nothing ever re-checked whether it's still true.
     `applied_decision_ids()`'s own docstring says this design choice is
     deliberate ("identified by id, not inferred from whether the text
     happens to still look un-applied"), which is sound ONLY as long as
     nothing bypasses the apply scripts - this audit is the missing check
     on that assumption. Ran against the current corpus: 17 applied
     decisions checked, 15 confirmed still correctly reflected, 2
     word-count-changing ones reported as not position-verifiable post-hoc
     (stated as a real limitation in the script's own docstring, not
     silently treated as passing), 0 mismatches. Unit-verified the checker
     itself catches synthetic reverted-replace/manual/punctuation cases
     before trusting the 0-mismatch result on real data.
   - **DONE - PASS3_KNOWN_FALSE_POSITIVES over-suppression (risk 4).**
     `check_klal_token_orphans.py`'s allowlist was a bare `{4, 18, 34}`
     klal_id set, suppressing EVERY Pass-3 gap hit for those klalim, not
     just the one specific span investigated 2026-08-12. Re-ran Pass 3
     against the current corpus: confirmed each of the 3 klalim still
     produces exactly the one investigated hit (no second, uninvestigated
     gap was hiding there right now) - but the mechanism couldn't have
     told us that before this fix. Changed the allowlist to
     `{(klal_id, normalized_span_text)}` so only the exact investigated
     span is suppressed; any different gap in these klalim now surfaces
     normally. Verified: same script output before/after (no regression),
     and a synthetic different-span check confirms it's no longer
     suppressed.
   - **DONE - stale nav/legend after external changes (risk 5).**
     `review_frontend/app.js` fetched `/api/klalim`/`/api/flags` once at
     init and never refetched, so a decision from another tab or a
     `rebuild_all.sh` run elsewhere (exactly what this session's own
     drift-check/PASS3 fixes did) left nav badges and legend totals wrong
     until a manual reload. Added `setupNavRefreshOnReturn()`: refetches
     both endpoints and rebuilds nav+legend on `visibilitychange` ->
     `'visible'` (the natural moment a user returns to an already-open
     tab), not on a poll. Also extracted `applyFlaggedFilter()` so the
     "flagged only" filter state survives a nav rebuild instead of
     silently resetting. Verified live in a real browser tab (not just
     read the code): instrumented `fetch` and confirmed exactly one
     `/api/flags` + `/api/klalim` refetch fires per simulated
     visibility-return, `KLALIM` becomes a fresh object, nav/legend
     re-render, no console errors.
   - **DONE - strip_head_header folio-numeral/marker ambiguity (risk 6).**
     The heuristic has no LOCAL way to tell a folio numeral from a real
     klal marker (both are 1-2 Hebrew letters in the same position) - it
     already ate klal 89's real marker `פט` once, caught only because ONE
     of its three call sites happened to have a separate downstream guard
     (`hstart >= nx["marker_position"]`); the other two had none. Added
     `build_marker_index()` (ground truth from `gematria_trace_part1.json`)
     and a `protected` param to `strip_head_header` so it refuses to
     consume a token position known to be a real marker, applied at the
     content-inclusion call sites (`page_body` for middle-page splicing,
     the tail-part-building calls). **Deliberately NOT applied** to the two
     `first_real_word` calls used for catchword-matching
     (`end_first_any`/`nxt_word`) - tried first, and it broke a real,
     verified case: page 40's actual printed catchword is `בעיא` (klal
     89's SECOND token), because this print's catchword convention
     reproduces the next page's first WORD OF RUNNING TEXT, skipping past
     a bare klal-number marker like `פט` rather than catching the marker
     itself. Protecting the marker in that lookup made it return `פט`
     instead, which no longer matched the real catchword and left it
     un-stripped (901 -> 902 words, a regression caught by re-running the
     script's own dry-run output and diffing against a `git stash`
     baseline before trusting the fix, not assumed correct from reading
     the code). Final version's dry-run output is byte-identical to the
     pre-fix baseline for klal 30/75/88 (all 3 already reconstructed, so a
     true no-op today), with the protection mechanism itself separately
     unit-verified to actually block consuming a known marker position.
   - **STILL OPEN, not investigated**: witness decisions keyed
     `(klal_id, docai_token_index)` with no page component (risk 2, safe
     only because `PAGE_TO_KLAL` is currently 1:1);
     `propose_punctuation_part1.py`'s cache key doesn't cover the prompt
     text or model (risk 3, dormant pipeline, no live effect). **Risk 3's
     sibling in the LIVE pipeline was found and closed 2026-08-14** -
     `verify_corrections_vision.py` had the identical gap and it was not
     dormant; see item 9 above. Risk 3 itself is unchanged, but it should
     no longer be read as "the only place this pattern exists."
   - **CODE-REVIEWED 2026-08-14 (Opus 5, high thoroughness, via
     subagent).** Reviewed everything committed this session so far
     (5 commits) - found 10 concrete issues, several of them real bugs
     in the fixes above written the same session, including one that had
     already corrupted committed data (3 witness-queue entries with
     literal backslash artifacts from `parse_decision_lenient`'s missing
     JSON-unescape step). All 10 fixed and independently re-verified
     (unit tests, live browser tests, dry-run diffs against baselines) -
     full detail in `PROJECT-STATUS-HISTORY.md`'s newest entry. Notably:
     `audit_applied_decisions.py` (item 1 above) originally skipped its
     own motivating precedent case (klal 1 word 97) due to a latest-
     per-key iteration bug - fixed, and it now correctly flags that case
     as a live MISMATCH (already understood/expected, a documented
     2026-08-10 test-revert, not a new corpus problem - no action
     needed). The marker-protection fix (item 4 above) had a real latent
     gap on 4 of 9 affected pages, on the unprotected side - fixed with
     a third `skip_marker` behavior; still a no-op for the currently-
     processed klal 30/75/88 (byte-identical dry-run output), but no
     longer silently wrong if this script is ever pointed at a klal
     spanning those pages. The visibility-refresh fix (item 5 pattern)
     had introduced its own race in the badge-count arithmetic - fixed
     by having every save path re-derive counts from a fresh
     `refreshKlalimList()` call instead of patching in place, which
     closes the race by construction rather than by careful ordering.

**5. General standing caution**: docstring/comment overclaims turned up
repeatedly across both audit rounds this session, in different validator
scripts - a script's claimed coverage is not evidence of its actual
coverage.

**6. DONE 2026-08-15 - the 8 group-3 candidates applied.** Per user
go-ahead, all 8 recorded and promoted the same way as the 122: klal 158
`או`→`אלו`; klal 168 `או`→`אלו`; klal 69 `א`→`אל` (×2); klal 198
`א`→`אל`; klal 169 `וא`→`ואל`; klal 176 `וא`→`ואל`; klal 200 `איהו`→
`אליהו` (lowest confidence of the 8 - attribution context is slightly
off, worth a second look regardless of being applied). None
individually scan-verified, unlike the 122. 8/8 verified correct
post-apply, third `rebuild_all.sh` run clean (74/74 pytest, 11/11
Playwright, no new test surprises). Full context/reasoning for each in
`PROJECT-STATUS-HISTORY.md`'s dropped-lamed entry.

**DONE 2026-08-15** (see the dropped-lamed entry near the top of this
file's handoff for full detail): a true DocAI-ingest-level fix turned
out to be impossible (the ligature information is already lost inside
DocAI's own recognition, before this repo sees the text) - built
`detect_ligature_corruption.py` (a re-runnable detection script) and a
permanent zero-tolerance regression test instead, and found + applied
one more real instance (klal 92) the two prior passes had missed.
`lexicon.txt` was purged of the 24 confirmed-corrupt forms (not a full
re-derivation - no independent external source is available). klal
200's `אליהו` attribution is still worth a second look even though it's
applied - not urgent, nobody's acting on it wrongly by leaving it.

**Still open, smaller**: nothing else identified. Parts 2-3 are
confirmed (2026-08-15, incidentally, while scoping the lexicon purge -
see the dropped-lamed entry) to have hundreds of unfixed instances of
this same bug - logged per CLAUDE.md's rule, explicitly NOT scoped or
proposed as work, per the standing Parts-2-3 gate.

**No other known open items beyond the above.** Full detail, evidence,
and the complete dated history behind every claim above is in
`PROJECT-STATUS-HISTORY.md`.
