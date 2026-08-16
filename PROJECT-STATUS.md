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

## ►► SESSION HANDOFF — read this first, 2026-08-16

### DONE 2026-08-16 — revalidation/refactor audit ROUND 2 of the live pipeline, merged (rebased onto master, 4 commits `532391d`..`ffc5b88`, merge commit `a75e028`)

The branch was cut before this session's own follow-on work (the app.js
escaping fix `7153e1d` and the lexicon-gap triage `16a75de`) had landed, so
merging required a `git rebase` onto current master first, not a plain
merge. That produced one real conflict in `review_frontend/app.js` - both
this round and the earlier `7153e1d` had independently added HTML-escaping
around the same functions. Resolved by taking round 2's version wholesale:
diffed both against their shared base and confirmed round 2's is a strict
superset (it also escapes the nav-item title attribute and corpus-text
context words that `7153e1d` had skipped - the latter now independently
justified by round 2's own foreign-character finding below, which proves
Part 1 does contain a few non-Hebrew characters).

Independently re-verified before merging, not just the agent's report
trusted: mutation-tested the DECISIONS_PATH fix by hand (reintroduced the
exact historical bug pattern, confirmed the new test goes red, restored
green) - and in doing so reproduced the bug's own real-world failure mode
on myself, appending a junk `klal_flag` row (klal_id 424242) to this
worktree's tracked `review_decisions.jsonl`; caught by the sha256 check
below and reverted with `git checkout --`, never merged. Independently
read the actual corpus text at all 7 foreign-character positions and at
the 6 gershayim-bearing `chosen_text` decisions the app.js fix's
justification cited - both held up exactly as described (see the entries
below). Re-ran the full suite post-rebase (105/105 pytest, 14/14
Playwright) and `./rebuild_all.sh` (0 live API calls - confirmed safe
beforehand by checking stage 1-2 output was already byte-identical to
master). sha256 of all 10 corpus/derived/decision files confirmed
byte-identical to master post-merge. Dashboard restarted post-merge
(`review_decisions.py` changed - Python doesn't hot-reload). Both this
round's worktree and round 1's (`../yad-malachi-pipeline-revalidation-
worktree`) removed after merging; branches left in git history.

**This is a SECOND, separate pass over the same scope as the round-1 audit
immediately below — not a duplicate of it.** Its brief was to find what round
1 missed: go deeper, start from what round 1 said it did NOT cover, and don't
re-derive anything already fixed. 3 findings, all fixed, each
mutation-verified. Not yet merged — user re-verifies independently first, as
with every prior round.

All three are **bugs (code)**. Separately, the third one surfaced a **data
issue** (7 stray characters in Part 1) which is reported and baselined, NOT
corrected — see finding 2. No `part*.json` and no `review_decisions.jsonl`
content was changed: all 10 corpus/derived/decision/lexicon files are
sha256-identical to the pre-audit baseline after a full `./rebuild_all.sh`
WITH vision (**0 live API calls**, every candidate a cache hit — verified by
confirming `corrections_candidates_part1.json`, the vision stage's only
input, was byte-identical BEFORE letting that stage run). 105/105 pytest (was
102 — 3 new, all mutation-verified) + 14/14 Playwright (was 11 — 3 new). All
5 scan-dependent standalone validators' stdout byte-identical.

**1. `review_decisions.py` — reassigning `DECISIONS_PATH` was a silent no-op, so writes kept landing in the tracked log.**
All seven functions declared `path=DECISIONS_PATH` as a **default argument**.
Python evaluates a default once, at import time, so `rd.DECISIONS_PATH = tmp`
— and `monkeypatch.setattr(rd, "DECISIONS_PATH", tmp)` — had **no effect** on
any call that omitted `path=`. The write still went to the real, git-tracked
`review_decisions.jsonl`.
  - That idiom is this suite's standard redirection mechanism, and it works
    everywhere else: `PART1_PATH`, `RAW_DIR`, `FREQ_CACHE`, `FREQ_META`,
    `CACHE_DB`, `SEFARIA_FREQ_CACHE` all rely on it, because those modules
    read their constant at call time. `review_decisions.py` was the **single
    module where it silently failed** — and it is the module guarding the
    append-only human-decision log CLAUDE.md singles out as the one file no
    pipeline run may ever clobber.
  - **It has now misfired twice, both as silent writes to the tracked log**:
    once during round 1 (a test called a write endpoint without stubbing
    `rd.append_decision`, appending a junk row) and once during THIS round
    while confirming the finding. Both were caught by a byte-comparison
    afterwards, never by the code refusing. Round 1 recorded the incident and
    fixed its symptom (stubbing that one test); the trap itself survived.
  - Fixed with call-time resolution (`_resolve()`). Every existing caller
    either passes an explicit path or relies on the env var (read before
    import), so behaviour is unchanged for all of them.
  - Test: `test_reassigning_DECISIONS_PATH_redirects_calls_that_pass_no_
    explicit_path` — deliberately **the only test in the file that omits
    `path=`**, which is exactly why the trap went unexercised through three
    prior audit rounds. Mutation-verified red/green, with the mutated run
    pointed at a scratch sink via `REVIEW_DECISIONS_PATH` so reproducing the
    bug could not touch the tracked log.

**2. `validate_part1_corpus_integrity.py` — the character-sanity gate cannot see a stray Greek `Π`, and Part 1 contains one.**
`check_character_sanity()` is a zero-tolerance gate in `rebuild_all.sh`, and
its own docstring says it "catches leftover OCR/scan artifacts (a stray `"P"`
from page furniture, an unstripped `"Google"` fragment, a truncated
bracket)". Its stray-letter test is `LATIN_RE = [A-Za-z]` — so it catches a
Latin `P` and misses **its Greek homoglyph `Π` (U+03A0), the exact example it
names**. CLAUDE.md Lesson 6 in one line.
  - A full character inventory of `part1.json` (milliseconds — Lessons 8 and
    18) found **7 foreign-character tokens across 6 klalim** that three prior
    audit rounds of vision, semantic and lexicon checking never surfaced,
    because no check had ever asked the general question, only three narrow
    ones: klal 39 w252 `Π`; klal 66 w97 and klal 74 w443 `!`; klal 69 w338,
    klal 77 w11, klal 167 w24 `&`; klal 176 w694 `;`.
  - Added `check_foreign_characters()` — anything outside the Hebrew block,
    the space, and `PART1_ALLOWED_NON_HEBREW`, a repertoire **derived** from
    the corpus's own inventory and checked entry by entry against a real use,
    not chosen. Gated in `tests/test_corpus_invariants.py`.
  - **The 7 existing instances are a DATA issue and were NOT corrected** —
    baselined in `FOREIGN_CHARACTER_BASELINE`, keyed by
    `(klal_id, word_index, char)` per the `PASS3_KNOWN_FALSE_POSITIVES`
    precedent so only those exact positions are suppressed. **NOT YET DONE:
    scan-verify all 7 and resolve them through the review pipeline.**
  - **Recorded with them, deliberately not acted on**: all three `&` sit
    exactly where `אל` reads naturally — klal 69 `כגון אל אלהים ה'` (the
    biblical `אֵל אֱלֹהִים יְהוָה`), klal 77 `נוטה אל הודאי`, klal 167
    `פנים אל פנים`. That is the same two-letter sequence as the confirmed
    alef-lamed ligature (U+FB4F) bug this project has already corrected 131
    instances of, raising the question of whether `&` is a **third**
    substitution DocAI makes for that one glyph (alongside the bare `א` and
    the bare `לא` the VLM produced). One frequency/semantic signal only —
    Lesson 9 and Success Criterion #1 both say that is not enough to change a
    character. Note `detect_ligature_corruption.py` structurally cannot find
    this shape: it only considers tokens that already contain an `א`.
  - Two tests, deliberately: the corpus gate, PLUS a hermetic can-it-fire
    test on synthetic input — without the latter the gate stays green if the
    check is neutered, since `found - baseline` is empty either way (Lesson
    2). Same reasoning that put the three older gated checks under
    can-it-fire tests. 3 mutations, 3 red, restored green.

**3. `review_frontend/app.js` — a recorded custom reading was truncated at the gershayim.**
The candidate panel rendered its custom-reading input as
`value="${activeText}"`, unescaped. This corpus's abbreviation mark **is the
literal ASCII `"`** (`part1.json`'s clean_text holds 6,448 of them), so a
recorded reading like `ב"ד` produced `value="ב"ד"` — which a browser parses as
`value="ב"` plus a junk attribute. **The reviewer reopened their own decision
and saw `ב`; saving again would have recorded `ב`.** A human's exact Hebrew
reading, silently truncated at the most common punctuation mark in the book,
in the tool whose entire job is exact fidelity (Success Criterion #1).
  - Not exotic: **6 `candidate_choice` decisions whose `chosen_text` contains
    a gershayim are already in `review_decisions.jsonl`** (klal 103/104/105,
    `ב"ד`). The manual-correction panel had escaped its own `value=` since it
    was written — the candidate panel never did, so the inconsistency sat
    visible in the file the whole time.
  - This is the finding round 1 reported and declined to fix (it found only
    the milder `tooltip.innerHTML` form, and its rule was no fix without a
    test). Added `escapeHtml()`/`escapeAttr()` and applied them at all **23**
    in-scope interpolation sites: nav title (attribute AND content), klal
    section, tooltip, both context panes (which interpolate `clean_text` —
    and klal 69/77/167 carry the bare `&` tokens from finding 2), candidate
    options, all four note textareas, both decision-history lists.
  - **Left unfixed, out of scope**: the witness panel carries the identical
    `value=` bug at its own custom-reading input (`app.js` ~line 1047).
    Reported, not changed, per the standing witness exclusion.
  - 3 new Playwright tests. **Mutation testing caught a defect in this
    audit's own test data and it is recorded rather than quietly re-rolled**:
    the first draft asserted on a note reading `'R & J <see p. 4>'` and
    stayed **GREEN** when `escapeHtml` was reduced to a pass-through — a bare
    `&` is not a valid entity reference and `<` is inert inside a textarea's
    RCDATA, so neither discriminates. Retargeted at `&amp;` and a literal
    `<b>` in an `innerHTML` context, which do. Lesson 2 applied to the
    auditor's own fixture. Final: 3 mutations, 3 red, restored green.

**Checked and found clean / hypotheses disproved (recorded so round 3 doesn't
re-derive them):** `build_klalim_demo_dataset.py`, `assemble_corrections_
dataset.py`, `build_klal_page_regions.py` (incl. round 1's key-order fix),
`rebuild_all.sh`, `review_server.py`, `validate_title_alphabetical_order.py`'s
isotonic DP, `detect_ligature_corruption.py` and
`fetch_sefaria_reference_corpus.py` — no new findings. One hypothesis was
tested and **disproved**: that `validate_lexicon_independent.py`'s report 2
was inflated by a normalisation mismatch (lexicon words carrying gershayim
can never match a frequency table built with a Hebrew-only filter). Measured:
`lexicon.txt` contains **zero** non-Hebrew characters, so the two sides
normalise identically and the 5,945-word figure stands as reported.

### DONE 2026-08-16 — full revalidation/refactor audit of the live pipeline, merged (7 commits `f8183e1`..`800564a`, merge commit on `master`)

Independently re-verified before merge, not just the agent's report trusted:
sha256 of all 9 corpus/derived/decision files confirmed byte-identical
between the worktree and pre-merge master; 102/102 pytest re-run directly
(not just read from the report); the diffs in `apply_reviewer_decisions.py`,
`review_server.py`, and `propose_abbreviation_expansions.py` spot-checked
against the specific claims below. Merged to master; `review_server.py`
changed, so the live dashboard was restarted post-merge (Python constants
there don't hot-reload) and reconfirmed serving on port 8420. Worktree
(`../yad-malachi-pipeline-revalidation-worktree`) and its branch left in
place, not yet deleted - safe to remove, kept only in case a re-check of the
merge is wanted.

All findings are **bugs (code)**, not data issues. No `part*.json` and no
`review_decisions.jsonl` content was changed (all four byte-identical to
master); full `./rebuild_all.sh` WITH vision = 316 cache hits / **0 live API
calls**, all 5 derived JSON files byte-identical; 102/102 pytest (was 77 — 25
new tests, every one mutation-verified red-then-green); all 5 scan-dependent
standalone validators' stdout byte-identical.

**1. `propose_abbreviation_expansions.py` (written 2026-08-16, no prior review) — 6 silent miscategorisation bugs.**
It writes nothing, which is exactly why it had to be right before a review/
apply stage is built on it.
  - A prefixed form's proposal was the ROOT's expansion verbatim, dropping
    the stripped prefix — `דר' -> רבי`, `התוס' -> תוספות`, `ובס' -> בספר`:
    **113 forms / 642 occurrences**, printed identically to a hand-verified
    dictionary hit. Substituting one would DELETE a real Hebrew letter
    (Success Criterion 1).
  - Prefix decomposition preferred the LONGEST PREFIX, not the longest
    surviving root. `ומוהר"ש`/`ומהר"י` were re-analysed as `ומ-`+`וה-`+`ר"ש`
    (SCHOLARLY) instead of `ו-` + a NAME root; `ולמ"ד` lost the ל that is
    part of the abbreviation.
  - No guard against a prefix stacking on a copy of itself (`דדחי'` →
    `ד-ד-`+`חי'` → "דדחידושי").
  - `looks_like_bare_numeral()` had **no upper length bound** despite its own
    docstring, and `resolve()` falls back to it — so **187 forms / 249
    occurrences** of plain Hebrew prose (`ובקדושין'`, `דתלמידי'`, `התוספו'`)
    were filed under a heading that says they are citation numbers needing no
    attention. Lesson 15's shape.
  - The frequency-based truncated-word completion was reported as `expand`.
    It appends exactly ONE letter, so a multi-letter truncation has no
    correct candidate and a merely-common word wins by default —
    **confirmed wrong on real data**: `בפי' -> בפיו` where all 10 Part-1
    occurrences are `בפירוש` ("בפי' רש"י על החומש"), `בחי' -> בחיי` where all
    4 are `בחידושי`. Now its own weaker-evidence category.
  - `looks_like_bare_numeral()` tested only the ASCII apostrophe while
    QUOTE_CHARS includes U+05F3; inert today, but a normalisation pass would
    have switched off both geresh-shaped paths with no error.
  - Dictionary corrections, each verified against its own Part-1 contexts:
    `משא"כ` was resolving to "אם כן" via a `מש-` prefix (it is **מה שאין כן**,
    5x); `מ"ל` was "מנא לן" (klal 54's `מ"ל חומרא רבא` is **מה לי**) while
    `מנ"ל`, the form that IS מנא לן, resolved to "מנראה לי"; **`ר"ל` moved to
    `scholarly`** — both referents are live in Part 1 (**ריש לקיש** in klal
    16/39/74/75, **רצה לומר** in klal 30) against a single unconditional
    expansion for 47 occurrences; `מה'`(122x)/`גמ'`/`בפי'`/`חי'` rescued from
    NUMERAL as expansions, and `פ'`/`ס'`/`פי'`/`הל'` rescued as genuinely
    two-way `scholarly` entries.

**2. `validate_lexicon_independent.py` — the independent reference corpus was silently missing a quarter of the Shulchan Arukh.**
`flatten_strings()` handled str and list but fell through on **dict**, and
Shulchan Arukh, Even HaEzer's `text` is a dict (`""`, `Seder HaGet`,
`Seder Halitzah`). It contributed **exactly zero words** while being
downloaded, counted as present, and named in the docstring: **106,474 words,
4.3%** of the corpus (2,473,227 → 2,579,701 measured). This is the ONE check
whose reference data has no lineage to this project's own OCR — the signal
every other check is measured against. Impact measured, not estimated:
**111 lexicon.txt words were wrongly reported as having "zero independent
attestation"** (6056 → 5945), e.g. `ביבמות`, `בכתובות`, `בקונטריס`, `גש`.
Also added: per-book counts with a loud WARNING for any zero-word book;
`word_freq.meta.json` provenance (extractor version + source file list) so a
cache built by the old rule can never be silently reused, with
`propose_abbreviation_expansions.py` declining a table it cannot vouch for.
`fetch_sefaria_reference_corpus.py` separately ignored curl's exit status and
left a failed download on disk, which the next run then counted as present —
the failure was reported once and invisible after that.

**NOTE:** `sefaria_reference_corpus/word_freq.json` in the MAIN checkout was
rebuilt (correctly, with Even HaEzer) during this audit — the worktree
symlinks that gitignored directory, and a validator-baseline run wrote
through it. Regenerable cache only; nothing tracked was touched.

**3. `detect_ligature_corruption.py`** — `load_klal_words()` used
`split(" ")` while every index-bearing script uses `split()`; a single double
space would shift every reported word_index, in the direction that edits the
corpus at a position nobody chose. Inert today (0 klalim in any part file
where the two disagree) and gated by
`test_clean_text_whitespace_is_single_spaces_only`. Its METHOD docstring also
claimed pass 1 "covers... all single/double-letter Hebrew prefixes", backed
by two constants (`PREFIX1`, `ALL_PREFIXES`) **nothing in the file ever
read**. There is no prefix logic. Docstring corrected and the real gap
recorded with a measurement rather than a guess: a prefix-stripping variant
yields 74 forms / 2,646 occurrences on Part 1, headed by `לא->לאל` (699),
`הוא->הואל` (381) — it drowns the signal, so the gap needs a different
discriminator, not a bolt-on. Second limit now stated: the frequency table is
built from the part file being scanned, i.e. the corpus validating itself.

**4. `review_server.py`** — both manual_correction render paths
(`api_klal`, `api_klalim`) bounds-checked only the upper end, the same
half-a-bounds-check gap fixed in `audit_applied_decisions.py` (2026-08-14)
and `apply_reviewer_decisions.py` (2026-08-15); the display path was never
revisited and had two copies of the expression. Extracted to one
`_word_matches()` with both bounds, and a negative `word_index` is now
refused at the write endpoint too (the log is append-only, so a bad row can
only be superseded, never removed).

**5. `apply_reviewer_decisions.apply_replace()`** had no empty-`final_text`
guard: `span` was `[]` and `n` fell back to 1, so for an out-of-range
word_index the drift check compared `words[wi:wi+1]` — `[]` in Python, not an
IndexError — against the empty span, PASSED, and the slice assignment
APPENDED to the end of the klal. `apply_insert_removal()` has had the
equivalent guard since it was written. Not reachable today; defence-in-depth
on the one path that writes `part1.json`.

**6. New corpus-invariant gate:
`test_no_rendered_manual_correction_hides_a_machine_candidate`.**
`app.js`'s word map is last-write-wins and `api_klal()` appends manual
entries after the machine candidates, so a manual entry at the same
word_index silently replaces the machine candidate — the reviewer sees a
green Human-Decided word and never learns the vision pass disputed it.
`review_server.py` asserts in a comment that this can't happen. It is not a
property of the data: **78 (klal_id, word_index) positions already collide**;
all are invisible only because the drift check drops them (1 manual decision
renders at all, 0 collisions). Mutation-verified to fire.

**Found, NOT fixed (reported rather than changed):**
- `review_frontend/app.js` interpolates `corr.reasoning`, `chosen_text` and
  `note` into `tooltip.innerHTML` unescaped. Local-only and display-only, but
  a note or a Gemini rationale containing `<`/`&` is silently mangled in a
  tool whose job is exact Hebrew fidelity. Not changed here: the frontend's
  only coverage is the Playwright suite, which is outside the gate, and this
  audit's rule was to ship no fix without a test that would have caught it.
- `build_corrections_dataset.py`'s running-header filter is a bare substring
  test (`"מלאכי" in orig_word`), not a word-boundary one — the weaker form of
  the bug fixed in `validate_catchword_continuity.is_header_word` 2026-08-14.
  Currently inert (0 Part-1 stored tokens contain `מלאכי`), and tightening it
  changes what the pipeline strips with no ground truth to check against —
  the same reasoning that left the three page-furniture definitions unified.
- Two defects in **this audit's own work**, both caught by the verification
  step and fixed in `e9968e6`, recorded because they are the interesting
  ones: a new test called a write endpoint without stubbing
  `rd.append_decision`, so mutation-testing the guard it covers appended one
  junk row to `review_decisions.jsonl` (reverted, never committed, file
  byte-identical); and a "behaviour-preserving" merge-order change in
  `build_klal_page_regions.py` reordered all 222 entries of a tracked derived
  file, caught only by the byte-identical check (Lesson 19 applied to the
  auditor).

> **This session's work (2026-08-16), in order - full detail lower in this
> file, dated entries under each heading**: (1) merged and independently
> re-verified the hard-wired-value audit (`154cb8d`); (2) closed 3 items
> from the prior handoff's open-items list - klal 200's `אליהו` attribution
> confirmed already scan-verified (a stale "worth a second look" claim,
> corrected), the witness `(klal_id, docai_token_index)` collision risk
> investigated and guarded (not fully closed - see "risk 2" below), and an
> independent lexicon cross-check built (Shulchan Arukh + Talmud Bavli via
> Sefaria's public export) which surfaced a real new corruption shape (5
> instances, 4 klalim, flagged not corrected); (3) built then REBUILT an
> abbreviation-expansion candidate list after the user caught the first
> version's core assumption error (it would have proposed expanding `רש"י`
> into a full name) - see "abbreviation-expansion candidate list built,
> then REBUILT" below for the real, evidence-based pattern; (4) this
> close-out sweep itself found and fixed 2 stale status claims (a merged
> worktree still marked "AWAITING MERGE," a 2-day-stale HEAD hash) and
> flagged one dangling branch for a future session's judgment call, not
> resolved. **No corpus text was changed this session** - every finding
> above is either a code fix, a documentation correction, or a flagged
> candidate awaiting human/scan review, never a direct `part1.json` edit.

> **Terminology, user directive 2026-08-15, applies to all future
> sessions**: an issue with the DATA is a "data issue," not a "bug." An
> issue with the CODE is a "bug." Added to CLAUDE.md as the durable
> home for this rule (so it survives this file's own "re-written, not
> appended" handoff churn) - noted here too for immediate visibility.

> **CLAUDE.md's "Pipeline shape" section was itself factually wrong in
> three ways, corrected 2026-08-15 after the user directly pushed back
> on an incorrect explanation and asked for it to be verified against
> the actual scan/code**: (1) the source PDF (`berlin_square_
> corrected.pdf`) is a Berlin SECOND printing, not the Livorno original -
> confirmed by reading the actual title page (`נדפס ראשונה בליוורנו...
> ועתה נדפס פעם שנית`, colophon `ברלין`); (2) the live automated
> comparison (`build_corrections_dataset.py`) is DocAI-vs-CURRENTLY-
> STORED-part1.json-text, not DocAI-vs-VLM as the doc implied - VLM
> extraction is sparse (~12 pages) and used only as a manual, opportunistic
> cross-check, and its own klal-numbering doesn't align with the corpus's
> (confirmed: VLM's "klal 2" and part1.json's current klal 2 are unrelated
> text); (3) a genuinely second physical scan does exist
> (`ספר_יד_מלאכי (1).pdf`, untracked) but was used exactly once,
> 2026-08-05, not routinely. Full corrected explanation now in CLAUDE.md's
> "Pipeline shape" section - read that, not this bullet, for the durable
> version. This is exactly Lesson 19's failure shape (a confident prose
> explanation that was never checked against the primary source) applied
> to documentation the assistant itself wrote, not a script's docstring -
> the same discipline this file demands of corpus claims applies to
> architecture claims too.

### DONE 2026-08-15 - hard-wired-value audit of the MAIN pipeline (merged from worktree `agent-acfcf39ded375a897`)

Per user request: audit the main pipeline's 20 in-scope files for hardcoded
values, magic numbers and special-cased logic that make the code fragile in
ways that aren't clearly intentional. Witness/punctuation excluded, as
standing. All findings below are **bugs (code), not data issues** - no
`part*.json` file was touched, and the full rebuild confirms all five derived
JSON files byte-identical.

**Fixed (each verified: 77/77 pytest incl. 2 new tests, 11/11 Playwright,
full `./rebuild_all.sh` WITH vision = 316 cache hits / 0 live API calls / 0
data drift, and all 7 standalone validators' stdout byte-identical to a
pre-change baseline):**

1. **`PART1_MAX_KLAL = 222` was written out independently in three live files**
   (`build_corrections_dataset.py`, `build_klal_page_regions.py`,
   `review_server.py`) with no comment in any of them and nothing tying it to
   the corpus. It is data - `max(klal_id)` in `part1.json` - not a chosen
   number, and every failure mode of a drifted copy is silent: the klal simply
   stops getting correction candidates, stops getting a scan region, or stops
   being served to the dashboard. Documented the derivation at all three sites
   and added a zero-tolerance gate,
   `test_part1_max_klal_constants_agree_with_the_corpus`, asserting all three
   equal `part1.json`'s own max klal_id AND that Part 1 is a contiguous 1..N
   block (without which `klal_id <= PART1_MAX_KLAL` is filtering on the wrong
   property). Deliberately NOT derived at runtime in `review_server.py` - that
   would add a 512KB read to every HTTP request. Mutation-verified (set one
   copy to 221 -> red, restored -> green).
2. **`assemble_corrections_dataset.py`'s vision-confidence gate `0.7` was a
   bare literal written three times inside `classify()`.** The place it was
   once MISSING is the already-fixed 2026-08-13 finding 8 (the `replace`
   branch trusting any confidence at all) - i.e. this exact triplication has
   already produced one real bug. Named `MIN_VISION_CONFIDENCE`.
3. **`build_corrections_dataset.py`'s `sim(...) < 0.5` replace-similarity
   cut-off** was unnamed with no derivation. Named `MIN_REPLACE_SIMILARITY`
   and documented as an uncalibrated triage cut-off whose rejects are silent
   (Lesson 15: "no candidate here" is not "checked and clean").
4. **`check_klal_token_orphans.py`'s 0.5 similarity threshold appeared three
   times, one of which was inside the printed message** `"word-sequence
   similarity < 0.5"` - so changing the threshold would have left the script
   reporting a number it no longer used. Named `MISMATCH_SIMILARITY` and
   interpolated into the message.
5. **`verify_corrections_vision.py`: unnamed `35`/`36`/`400` context-window
   numbers and `padding=0.02`/`dpi=300` crop geometry.** The 35-vs-36
   asymmetry (an exclusive slice end) reads like an off-by-one inviting a
   "fix"; all five feed `context_hash`/`crop_hash`, so any change silently
   costs a full re-run against the paid API. Named `CONTEXT_WINDOW_WORDS`,
   `FALLBACK_CONTEXT_CHARS`, `CROP_PADDING`, `CROP_DPI`, values unchanged
   (proven by the 0-API-call rebuild).
6. **`validate_catchword_continuity.py`'s `LAST_PAGE = 82` had no comment and
   no derivation** - one line under the constant whose invented justification
   this project already had to correct (`FIRST_REAL_PAGE`, 2026-08-14). A scan
   that gained pages would silently never have its later boundaries checked
   while the script still printed a confident "Checked N page boundaries"
   (Lesson 1). Now derived from `docai_word_boxes/` (max `page_N.json` = 82
   today, output byte-identical), with the literal kept only as the
   no-cache fallback.
7. **`validate_part1_corpus_integrity.py`: bare `ref_val > 667` and
   `m.start() - 25`** inline in check 4. Named `TOTAL_KLALIM` (cross-
   referenced to the 1..667 corpus invariant) and
   `SELF_REF_DIRECTION_WINDOW_CHARS`. Low impact - check 4 is documented
   NOT VIABLE and is not gated - but free to fix.
8. **`apply_reviewer_decisions.py`'s five corpus mutators bounds-checked only
   the UPPER end of `word_index`.** Exactly the half-a-bounds-check gap fixed
   in `audit_applied_decisions.py`'s three checkers 2026-08-14 (finding 9) and
   guarded in `check_drift` - but never in the code that actually WRITES
   `part1.json`. Python doesn't raise on a negative index: `words[-1]` is the
   last word and `words[-1:-1] = span` inserts before it, so
   `apply_manual_correction`/`apply_manual_deletion`/`apply_delete_insertion`
   would have edited, deleted or inserted at the klal's LAST word for a
   decision recorded at index -1. Added `word_index < 0` to all five, plus
   `test_every_mutator_refuses_a_negative_word_index`. **Not reachable from
   today's producers** (both are structurally non-negative) - defence-in-depth,
   not a fix for observed corruption. The test's first draft passed for the
   wrong reason (a -1 against a 1-word span is refused by the span check
   anyway); caught by mutation testing and rewritten with indices that
   genuinely discriminate, then re-verified one guard at a time (4 mutations,
   4 red, restored green).
9. **A comment in `build_corrections_dataset.py` claimed `WATERMARK_WORDS` was
   the "same set used by check_klal_token_orphans.py /
   validate_klal_span_coverage.py's furniture stripping". Both halves are
   false** - the same class as the `MAX_SPAN=4` citation of a nonexistent
   constant fixed 2026-08-14. `validate_klal_span_coverage.py` does no
   furniture stripping AT ALL (which is precisely why known-complete klalim
   106/123/175 sit in its flagged baseline - furniture inflates their expected
   span), and the three definitions that do exist differ materially:
   lowercased+punctuation-stripped here, raw case-sensitive exact match in
   `check_klal_token_orphans.FURNITURE_WORDS`, a third form again in
   `validate_catchword_continuity` (`HEADER_WORDS` + case-insensitive
   `FURNITURE_RE` + the gershayim guard). Comment corrected to state what is
   actually true.

**Found, deliberately NOT changed (reported rather than guessed at):**

- **Three near-duplicate definitions of "page furniture" across
  `build_corrections_dataset.py`, `check_klal_token_orphans.py` and
  `validate_catchword_continuity.py`** (finding 9 above), plus `SECTION_WORDS`
  defined identically in two of them. A real drift risk, but their MATCHING
  RULES differ, so a single shared set would silently change what each script
  strips - a behaviour change with no ground truth to check it against.
  Documented in place instead. Whoever unifies these must re-verify each
  script's output, not just the set membership.
- `build_klal_page_regions.py`'s `tol = 0.004` Y-banding tolerance: a magic
  number, but a local variable with a real derivation comment (the klal 3/4
  0.007-apart example) and no cross-file copy. Changing it moves every region
  box with no ground truth to check against.
- `verify_corrections_vision.py`'s `max_retries = 3` / `(2 ** attempt) * 2`
  backoff / `timeout=60000`: ordinary transport-layer tuning, each already
  carrying its own incident comment.
- `review_frontend/app.js`'s UI numbers (panel context windows ±6/±8/±10,
  tooltip offsets, 2000ms flashes, zoom steps, the 55-chars-per-line
  placeholder estimate): display-only, a wrong value is visible immediately
  rather than silent.

**Explicitly NOT flagged as findings** (they are the correct, hard-won
design this project already documents): `PASS3_KNOWN_FALSE_POSITIVES`
(span-keyed, per-entry evidence), `INTRA_KLAL_DUPLICATE_PHRASE_BASELINE`,
`DROPPED_LAMED_CORRUPT_FORMS`, `DUPLICATE_WORD_BASELINE`,
`SPAN_COVERAGE_BASELINE`, `AMBIGUOUS_WITH_LAMED_INSERTED`,
`FLAG_LABELS`, `FIRST_REAL_PAGE = 13` (justification corrected 2026-08-14),
`FLAG_RATIO_THRESHOLD = 0.85` and `TITLE_SIMILARITY_THRESHOLD = 0.8` (both
already named with their derivation), `n=10` in the duplicate-phrase checks
(empirically derived, reasoning recorded), and `list(range(1, 668))` in the
klal-sequence test (the invariant itself, not an incidental constant).

**No data issues found.** Nothing in `part1.json`/`part2.json`/`part3.json`
was read as suspect during this pass, and no corpus file was touched.

Independently re-verified 2026-08-16 before merge (not just the agent's own
report trusted): read the full diff against master, ran `77/77 pytest` in the
worktree with the real (gitignored) `docai_word_boxes`/`document_jsons_berlin`/
`vlm_extractions` caches symlinked in (a first run without them produced a
false-looking regression - 0 candidates, 0 regions - purely because those
caches don't exist in a fresh worktree per CLAUDE.md, not a real defect), ran
`./rebuild_all.sh` with vision live (confirmed 0 API calls, all cache hits),
and diffed all 7 derived files (`klalim_demo_dataset.json`,
`corrections_verified_part1.json`, `corrections_part1.json`,
`klal_page_regions.json`, `part1.json`, `part2.json`, `part3.json`) against
master's current versions by sha256 - all byte-identical. Merged to master,
worktree removed.

### State on disk right now (verified, not remembered)

- **CORRECTED 2026-08-16** - the HEAD hash and dashboard-restart history
  below were from 2026-08-14 and had gone stale (Lesson 19's own pattern,
  caught during this session's close-out sweep rather than left for the
  next session to discover). Current, re-verified facts as of the end of
  this session:
- **Branch `master`, HEAD `a749719`.** Working tree clean, 77/77 pytest
  (`tests/test_corpus_invariants.py` + `tests/test_pipeline_logic.py`)
  passing. `git worktree list` shows only the main checkout - no leftover
  worktrees from this session's merges.
- **One pre-existing, unrelated dangling branch found during this sweep,
  NOT investigated further or touched**: `pipeline-audit-fixes-and-page-
  order-repair`, tip `5a86ef6` (2026-08-11, "fix 8 correctness bugs,
  repair transposed PDF leaves 37/38"), not an ancestor of `master`. Its
  diff against its own merge-base is large (~10.7k lines across 32 files)
  but every file it touches (`propose_punctuation_part1.py`,
  `reconstruct_multipage_klalim.py`, `verify_reconstruction_witness.py`,
  etc.) already exists and is live on `master` today via separate later
  commits, so this is very likely early/superseded work, not orphaned
  unmerged fixes - but this was NOT confirmed line-by-line, only inferred
  from file presence. Flagging for a future session to either confirm
  superseded and delete, or investigate further - not deleted here since
  that wasn't asked for and the superseded-vs-orphaned question isn't
  fully closed.
- **Review dashboard is running** (`python3 review_server.py`, PID 54339,
  port 8420) on the CURRENT code - restarted once this session (2026-08-16,
  for the witness-collision-guard fix in `_load_witness_queue()`). No
  restart needed going forward for anything committed after that restart.
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

### DONE 2026-08-16 - full triage of check 5's 951 not-in-lexicon words (`review_lexicon_gaps.py`, new) - 109 candidates flagged across 43 klalim, a previously-unnamed corruption class

`validate_part1_corpus_integrity.py`'s check 5 has reported "951 distinct
not-in-lexicon words / 1104 occurrences / 846 hapax" for months as an
uninvestigated informational number. It has now been triaged in full. **No
corpus file was touched** - `part1.json`/`part2.json`/`part3.json` are
byte-identical (sha256 verified before and after), 102/102 pytest, check 5's own
output unchanged. The work is a new read-only script plus 43 appended
`klal_flag` rows.

- **`review_lexicon_gaps.py`** (new, standalone, read-only, re-runnable -
  verified deterministic across two runs, stdout and `--json` both
  byte-identical). Attaches five independent signals to each of the 951 forms
  and buckets each into exactly one bucket, so the counts sum to 951 with
  nothing dropped: surface punctuation (check 5 strips gershayim, so `א"א`
  reaches lexicon.txt as `אא`); independent attestation in
  `sefaria_reference_corpus/` (provenance confirmed current before use -
  extractor v2, 41 books, Even HaEzer's 106,474 words present, 2,579,701 total);
  prefix-stripped resolution (imports `propose_abbreviation_expansions.
  prefix_decompositions()` rather than reimplementing it); the known
  dropped-lamed shape; and a single-edit-neighbour check added mid-task once the
  unresolved list turned out to be full of one-letter misreads. `--contexts`
  prints every occurrence in its own klal's words, which is the actual reading
  step.
- **Bucket ordering was itself a finding.** The three "benign explanation"
  buckets originally outranked the corruption-shape signal and buried real
  candidates behind an explanation that happened to also apply: `וכלבד` (for
  `ובלבד`) decomposes as ו+כ+לבד, so a spurious prefix hit explained a misread
  ב; `וחרמב"ם` (for `והרמב"ם`) carries a gershayim, so the abbreviation rule
  explained a misread ה. Corrected - an explanation for why a form is missing
  from lexicon.txt is not evidence the form is right. 16 forms moved buckets.
- **Triage result** (951 forms / 1104 occurrences): `ocr_shape_to_read` 59/61,
  `abbreviation_artifact` 105/127, `known_corrupt_form` **0/0**,
  `independently_attested` 127/168, `prefix_resolved` 329/379,
  `weakly_attested` 164/195, `unresolved` 167/174. **377 forms were read in
  context, every occurrence** (the first bucket, the last bucket, and the
  zero-attestation half of `prefix_resolved`); the other 574 are accounted for
  by attestation, ordinary prefix morphology, or gershayim-stripping, and their
  form lists were eyeballed as a check on that.
- **The dropped-lamed fix has left no residue check 5 can see**: 0 genuine
  survivors of the 24 purged corrupt forms. The 2 apparent hits (`אא`, `אה`) are
  every-occurrence-gershayim `א"א`/`א"ה` - the same false-positive class the
  original investigation had to back out twice, reported explicitly rather than
  silently bucketed.
- **NEW FINDING - a single-letter OCR-confusion class, distinct from the
  dropped-lamed ligature bug.** 109 candidates across 43 klalim, concentrated in
  a small set of letter pairs: **ב/כ** (`וכתב`→`וכתכ`, `בכתיבת`→`בכתיכת`,
  `אברהם`→`אכרהם`, `יבום`→`יכום`), **ד/ר** (`בתלמוד`→`בתלמור`,
  `דשלשה`→`רשלשה`), **ה/ר** (`בהדיא`→`ברדיא`, `עליהם`→`עלירם`,
  `שהקשה`→`שרקשה`), **ה/ד** (`דבריהם`→`דברידם`, `דאיהו`→`דאידו`,
  `אליהו`→`אלידו`), **ה/ח** (`מחלוקת`→`מהלוקת`, `חטאת`→`הטאת`), **ט/מ**
  (`מיניה`→`טיניה`, `הקומץ`→`הקוטץ`), **ס/פ** (`לפרש`→`לסרש`,
  `בפסחים`→`בססחים`), **ג/נ** (`דמגילה`→`דמנילה`, `אשגח`→`אשנח`). Several carry
  internal corroboration that owes nothing to a dictionary: klal 143 spells
  ופומבדיתא correctly at w546 and `ופומכדיתא` at w651; klal 186's `לסרש` sits
  four words from a correct לפרש in the same clause; klal 92 has `למכבר קראי`
  once against `למסבר קראי` four times in the same klal; klal 30's corrected
  `לאקושינהו` occurs independently elsewhere in Part 1. The ד/ה direction is
  **already scan-confirmed** in this project - `וכוותיידו`/`וכוותייהו`, klal 88,
  in the witness-method entry in PROJECT-STATUS-HISTORY.md.
- **Flagged, NOT corrected.** 43 `klal_flag` decisions (`reviewer:
  "ai-lexicon-full-review"`, `needs_revisit: true`), one per klal, each note
  listing every candidate word with its `word_index`, the hypothesised reading,
  and the specific reason. Every one of the 109 word indices was validated
  against `part1.json` before writing. Verified after: `review_decisions.jsonl`
  grew 399 -> 442 lines, the first 399 byte-identical to `HEAD`'s version, all 43
  new rows well-formed `klal_flag`; live dashboard confirmed serving them
  (`/api/klal/1/flag`, `/30`, `/159`, `/217`). This is textual evidence only -
  **nothing here was checked against the scan**, and klal 88's already-scan-
  verified `רתם`/`התם` (print-faithful broken type, correctly excluded from this
  list after checking the history) is the standing proof that some of these will
  turn out to be faithful to the ink.
- **SECOND FINDING, and the more important one: this whole class is largely
  INVISIBLE to check 5, because `lexicon.txt` contains the corrupt forms.** The
  contexts read above surfaced 13 further corruptions of the identical shape
  whose corrupt form is itself a real Hebrew word, so check 5 never reported
  them: `ישרץ`→`ישראל` (klal 88 w1061; and the prefixed `בישרץ`→`בישראל`, klal
  144 w907), `שמה`→`שמח` (klal 7, quoting Ps.
  16:9), `אכל`→`אבל` (klal 30), `ליבא`→`אליבא` (klal 159), `לדם`→`להם` (klal
  196, quoting Ex. 23:32), `ארת`→`את` (klal 97), `שרוא`→`שהוא` (klal 150),
  `לדו`→`להו` (klal 37), `דיא`→`היא` (klal 154), `כין`→`בין` (klal 54),
  `גכ`→`גב` (klal 37), `טרור`→`טהור` (klal 4), `שכתכו`→`שכתבו` (klal 163). All
  13 verified present in `lexicon.txt`, and each re-verified at a real word
  index in `part1.json` (that re-check caught one wrong klal-144 claim in this
  entry's own first draft - the token there is the prefixed `בישרץ`, not
  `ישרץ` - Lesson 19 applied to this write-up). This is the same structural failure
  already recorded for the ligature bug ("`lexicon.txt` cannot catch the
  ligature corruption - it contains it"), now confirmed for a second, unrelated
  corruption class. **These 13 are NOT in the 43 flags** - they were found while
  reading context for other words, not by any systematic method, so their true
  corpus-wide count is unknown and is certainly higher. **NOT DONE**: a
  systematic sweep for this class. It needs a different detector (an
  independent-attestation ratio test over every Part-1 token, not a lexicon
  membership test), the same shape as the gap
  `detect_ligature_corruption.py`'s docstring records for prefixed forms.
- **Side effect worth knowing about**: 21 of the 43 klalim already had a
  `klal_flag` row, and the dashboard shows the LAST row per klal as current, so
  those earlier notes (e.g. klal 130's and 150's `ai-lexicon-crosscheck`
  candidates from earlier the same day) are no longer the displayed one. Nothing
  is lost - the log is append-only and `history_for()` returns all of them - but
  a reviewer working from the dashboard alone will not see them. Klal 30 is the
  one case where the previous current row was `needs_revisit: false` (a human
  had cleared it) and is now re-raised, on the strength of 12 new candidates.

### DONE 2026-08-16 - independent lexicon cross-check built (closes the "no independent source available" gap above)

Per user request ("do #3"). `lexicon.txt` was built from this project's own
OCR output (see below), so nothing it validates against is truly
independent. Built a genuinely independent Rabbinic Hebrew/Aramaic reference
corpus and a read-only cross-check against it - not a lexicon rebuild, a new
signal.

- **`fetch_sefaria_reference_corpus.py`** (new, standalone): downloads
  Shulchan Arukh (all 4 chelekim) + Talmud Bavli (37 tractates), Hebrew,
  from Sefaria's public GCS export bucket (`Sefaria-Export` on GitHub -
  no API key, one merged JSON per book). Same halachic-code/Talmudic-
  citation register as Yad Malachi. Output: `sefaria_reference_corpus/raw/`
  (41 files, ~45MB), gitignored like this project's other scan-derived
  caches. Idempotent - skips files already present.
- **`validate_lexicon_independent.py`** (new, standalone, read-only):
  builds a word-frequency table from the 41 files (2,473,227 words,
  113,955 unique forms - a real independent sample, not a toy) and
  produces two reports, neither of which writes anything:
  1. **Sanity-checks the 2026-08-15 lexicon purge.** 17/24 of the
     dropped-lamed corrupt forms have ZERO independent attestation
     (supports the purge). **7/24 DO have nonzero independent
     attestation** as real words somewhere in this 2.47M-word corpus -
     `אא` (28x, vs `אלא` at 19,144x - 684x more common), `אה` (8x vs
     `אלה` 182x), `איה` (48x vs `אליה` 53x), `אמא` (15x vs `אלמא` 586x),
     `אפא` (2x vs `אלפא` 33x), `האף` (11x vs `האלף` 13x), `והאף` (1x vs
     `והאלף` 1x). This does NOT overturn the purge - the overwhelming
     frequency skew toward the corrected form still holds, and Part 1's
     own instances of `אמא`/`אפא` were separately, individually
     re-read in context on 2026-08-15 before the purge (see above) - but
     it is new evidence that wasn't available when the "0 ambiguous"
     framing was written, logged here per Lesson 2.
  2. **6,056/19,015 lexicon.txt words (31.8%) have zero independent
     attestation.** Explicitly NOT a purge list - the script's own
     docstring says so and the report is capped/labelled as
     for-individual-reading. Confirmed by spot-check: most of the sample
     are legitimate (medieval/early-modern rabbinic names Yad Malachi
     cites that predate or postdate the Talmud/Shulchan Aruch corpus,
     e.g. `אבודרהם`/Abudarham, `אבולעפיא`/Abulafia - real historical
     figures with no reason to appear in the reference corpus).
- **REAL NEW FINDING while spot-checking report 2**: the independent
  check surfaced a corruption SHAPE the two prior dropped-lamed passes
  structurally could not catch. `detect_ligature_corruption.py`'s method
  only checks "does inserting ל after an א within THIS token produce a
  real word" - it cannot catch a corrupted `אלא`->`אא` that ALSO lost its
  following space and fused with the next word into one token. Checked
  every lexicon.txt word starting with `אא` (len>2) for actual presence
  in `part1.json` (16 found); 11 are the genuine abbreviation `אא"כ`/
  `אא"ע` (gershayim-marked acronyms, correctly excluded by gershayim
  guards elsewhere but this ad-hoc check didn't have one, caught by
  reading the list rather than trusting the count). **5 real candidates,
  4 distinct klalim, none scan-verified**: klal 130 word 11 and klal 168
  word 11, both `אאמוראי` (candidate split `אלא`+`אמוראי`, "but/rather
  the amoraim..."); klal 150 word 167 `אאיזה` (`אלא`+`איזה`, "but
  which"); klal 168 word 162 `אאביי` (`אלא`+`אביי`, "but Abaye [said]");
  klal 177 word 318 `אאידך` (`אלא`+`אידך`, "but the other"). All five
  candidate splits are ordinary, natural Talmudic phrasing, and all have
  zero independent attestation as single words while both halves of each
  split are common independently. **Not corrected** - per Success
  Criterion #1, a different corruption shape than the already-confirmed
  131 instances needs its own verification (Lesson 9: two independent
  signals should agree, and this is only one so far - a frequency
  argument, not a scan read). Recorded as 4 `klal_flag` decisions
  (`reviewer: "ai-lexicon-crosscheck"`, `needs_revisit: true`, ids
  `815a2579b395`/`92a97742f8b3`/`0a15fcf0df69`/`4826eb63b40e`) - confirmed
  live on the dashboard (`/api/klal/130/flag` etc.) before logging this.
  **NOT YET DONE**: scan-verify these 5 instances; consider whether
  `detect_ligature_corruption.py` should gain a second pass for this
  compound-token shape (would need a word-frequency-based split search,
  not just single-token insertion - a real design question, not done
  here).
- Verified: `fetch_sefaria_reference_corpus.py` re-run confirms 41/41
  idempotent (no re-download); `validate_lexicon_independent.py` re-run
  produces byte-identical report output; live dashboard confirmed
  serving all 4 new flags correctly; nothing in `part1.json`/
  `lexicon.txt`/any derived pipeline file was touched by this work - it
  is purely additive (two new scripts + one gitignored cache dir + 4
  decision-log entries).
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

### DONE - test-coverage expansion + test-suite refactor (worktree `agent-a8a04e346269f3067`, 5 commits), 2026-08-14, merged as `b30eae5`

**CORRECTED 2026-08-16**: this heading said "AWAITING MERGE" - stale, found
while doing session-close housekeeping. It merged the same day
(`b30eae5 Merge test-suite expansion + refactor (85 tests, worktree
agent-a8a04e346269f3067)`) and is also already summarized as done in the
"DONE - test-suite expansion/refactor, merged 2026-08-14" bullet near the
top of this file - this section is that merge's own detailed working notes,
left in place for the evidence trail, not a second pending item.

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

**DONE**: `reconstruction_witness_queue.json`, `witness_vision_cache.db`,
and `verify_witness_vision.py` committed together (`145337d`) - this line
previously said "not yet done" and was stale; corrected 2026-08-16 after
`git status`/`git log -- <files>` showed the working tree already clean
and the commit already on master. This is still a TRIAGE layer only (per
its own design) - it does not record `witness_choice` decisions itself,
so it doesn't close item #2 below on its own; a human still needs to work
through the dashboard.

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
   - **DONE 2026-08-16 - risk 2 investigated and guarded (not fully
     closed).** Confirmed the exact mechanism: every witness match/lookup
     site in `review_server.py` (`api_klal`'s decided-count,
     `api_witness_summary`, `api_witness_context`,
     `api_post_witness_decision`'s snapshot lookup) keys on `(klal_id,
     docai_token_index)` alone, and `docai_token_index` is PAGE-RELATIVE
     (an index into that page's own filtered token list, per
     `verify_reconstruction_witness.py`) - so the key is only unique
     today because `PAGE_TO_KLAL = {24: 30, 37: 75, 40: 88}` happens to
     map each page to a DIFFERENT klal_id. Nothing enforced that. Checked
     current data: no collision exists (`_load_witness_queue()` now
     asserts this on every load). Fix applied: `_load_witness_queue()` in
     `review_server.py` raises immediately if the same
     `(klal_id, docai_token_index)` pair is ever seen on two different
     pages, turning a hypothetical silent misattribution (a human's
     witness decision on one page's word landing on a different page's
     word) into a loud failure at load time. **Not the full fix** - the
     matching logic itself still doesn't use `page`; that would need
     changes at every match site plus the frontend's request payload, and
     nothing currently motivates it (no klal is planned to get a second
     witness-processed page). Verified: `_load_witness_queue()` loads
     clean (419 items, 0 collisions), 77/77 pytest, live server restarted
     and `/api/witness` + the dashboard both confirmed working
     post-change, no data file touched.
   - **STILL OPEN, not investigated**: `propose_punctuation_part1.py`'s
     cache key doesn't cover the prompt text or model (risk 3, dormant
     pipeline, no live effect). **Risk 3's sibling in the LIVE pipeline
     was found and closed 2026-08-14** - `verify_corrections_vision.py`
     had the identical gap and it was not dormant; see item 9 above. Risk
     3 itself is unchanged, but it should no longer be read as "the only
     place this pattern exists."
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
**RESOLVED 2026-08-15/16, found in `review_decisions.jsonl`**: a
separate `candidate_choice` decision (`b58eb7b2b475`, `reviewer:
"local"`, i.e. a human working the normal flagged-correction dashboard,
not the AI passes above) independently scan-verified this exact word
via Gemini vision at 0.98 confidence - "a prominent ascender for the
letter Lamed... between the Aleph and Yod" - and directly resolved the
attribution doubt: the surrounding text reads `כמוהר"ר אליהו`, i.e. the
scan itself names the referent "Eliyahu," which settles the "is this
really Eliyahu Rabbah/Zuta" concern the AI note raised. No longer just
"applied on judgment" - now individually scan-verified like the other
23. Nothing left open here.

**DONE 2026-08-15** (see the dropped-lamed entry near the top of this
file's handoff for full detail): a true DocAI-ingest-level fix turned
out to be impossible (the ligature information is already lost inside
DocAI's own recognition, before this repo sees the text) - built
`detect_ligature_corruption.py` (a re-runnable detection script) and a
permanent zero-tolerance regression test instead, and found + applied
one more real instance (klal 92) the two prior passes had missed.
`lexicon.txt` was purged of the 24 confirmed-corrupt forms (not a full
re-derivation at the time - an independent external source is now
available, see the 2026-08-16 entry above). klal 200's `אליהו`
attribution - flagged above as the lowest-confidence of the 8 group-3
corrections - is now scan-verified and resolved, see the item 6 update
above; no longer an open item.

**Still open, smaller**: nothing else identified. Parts 2-3 are
confirmed (2026-08-15, incidentally, while scoping the lexicon purge -
see the dropped-lamed entry) to have hundreds of unfixed instances of
this same bug - logged per CLAUDE.md's rule, explicitly NOT scoped or
proposed as work, per the standing Parts-2-3 gate.

### DONE 2026-08-16 - abbreviation-expansion candidate list built, then REBUILT after checking real editorial practice

User added two reference JPGs (Machon Yerushalayim's critical edition of
klal 1-2 - gitignored, `*.jpg` added to `.gitignore`, purely for reference,
never a scan/correction source per Success Criterion #1) and noted that
edition expands abbreviations and adds punctuation.

**First version was wrong in its core assumption**, caught by the user
before it went anywhere: it treated every gershayim/geresh-marked token as
an expansion candidate, which would have proposed turning `רש"י` into
"Rabbi Shlomo Yitzchaki" inline - not something any real critical edition
does. User's exact instruction: "we would not want to expand r"shi into Rav
Shlomo... Look at those two pages - see which words they expanded." Cropped
both JPGs at 3x and compared specific phrases word-for-word against
`part1.json`'s actual klal-1 text (not assumed from the abbreviation's
category in isolation). Real, evidence-based pattern found:

- **NEVER expanded, confirmed by repeated direct comparison**: person/work-
  name acronyms (`רש"י`, `הרא"ש`, `הר"ן`, `הרשב"א`, `רי"ף` all stayed
  abbreviated every time they appeared across both pages), formulaic
  markers (`ז"ל`, `ד"ה`, `וכו'`, `ע"כ`, `ודו"ק`, `ולענ"ד`, `הנ"ל`, `מ"מ`),
  and citation-format tokens (folio+side `י"ט ב'`/`ל"א ב'`, chapter+number
  `בפ"ב`/`בפ"ג`).
- **Genuinely expanded, confirmed by direct before/after pairs**: single-
  word GERESH-TRUNCATED forms restored to their full ending - our `בהדי'`
  → their `בהדיא`; our `תני'` → their `תניא`; our `נרא'` → their `נראה`;
  our `אחרי'` → their `אחריה`. Bare `פ'` (used as an ordinary noun, not
  part of a number-citation) → `פרק`. `ע"ש` → `עיין שם` specifically
  (confirmed twice) even though `ע"כ`/`וכו'`/`מ"מ` in the SAME paragraphs
  stayed abbreviated - this is a per-abbreviation editorial choice, not a
  rule that generalizes from one form to its siblings.
- **A third, higher-risk case the first version didn't separate out at
  all**: ambiguous multi-referent acronyms get resolved to ONE specific
  full name by the editors, not just spelled out - our `אליבא דר"י` became
  their `אליבא דרבי יהודה`, i.e. someone read the actual sugya and decided
  which of several possible sages (Yehuda? Yosi? Rabbeinu Yitzchak?) was
  meant. That is scholarship, not a lexical lookup, and is a DIFFERENT and
  greater risk than an ordinary ambiguous phrase-abbreviation (where
  listing 2-3 options and letting a human pick is safe) - picking one
  automatically here would be actively wrong more often than not.

**`propose_abbreviation_expansions.py` rebuilt around 5 explicit
categories** (`expand` / `stays` / `name` / `scholarly` / plus the existing
`numeral`/`artifact`/`unresolved`), each root entry tagged so a reader can
see WHY a form isn't a candidate, not just that it's absent:

- **`name`** (111 forms, 960 occurrences) - person/work acronyms, never
  proposed.
- **`scholarly`** (54 forms, 268 occurrences) - ambiguous-referent
  acronyms (`ר"י`, `ר"ש`, `ר"א`, `ר"ח`, `ר"פ`, `ר"ת`, `ד"מ`, `כ"מ`, `כ"א`,
  `ר"ה`, `ב"ה`), never proposed, multiple options listed for a human who
  reads the actual passage.
- **`stays`** (96 forms, 1888 occurrences) - confirmed or strongly
  analogous convention (citation-format chapter/folio numbers, Shulchan
  Arukh section names treated as proper-noun-like labels).
- **`expand`** (239 forms, 2397 occurrences, 24.9%) - the actual candidate
  list, including a new mechanism (see below).
- `numeral` 246/1720 (17.9%), `artifact` 2/50 (0.5%), `unresolved`
  829/2330 (24.2%) - unchanged in kind from the first version.

**New mechanism added during the rebuild, reusing today's earlier
infrastructure**: `resolve_truncated_word()` handles single-geresh
word-ending truncations (a DIFFERENT shape from multi-letter acronyms) by
trying each common Hebrew word-final letter against the stem and checking
the independent Sefaria corpus (`sefaria_reference_corpus/word_freq.json`,
built earlier today - see the lexicon cross-check entry above) for a
single, clearly-dominant completion - the exact one-clear-winner method
`detect_ligature_corruption.py` already uses for the dropped-lamed bug,
applied here to a missing word-ending instead of a missing letter. Found
58 forms this way (`בפי'`→`בפיו`, `משו'`→`משום`, `תני'`→`תניא`, `נרא'`→
`נראה`, etc.) - spot-checked against the confirmed page-comparison pairs
above, all consistent.

**Two real bugs found and fixed while building this, both by testing
directly rather than trusting the aggregate coverage number**:
1. Prefix-stripping originally tried only ONE level, so stacked prefixes
   (e.g. `להרא"ש` = ל + ה + `רא"ש`) failed to resolve even though the bare
   root was in the dictionary - fixed to try 2 stacked levels.
2. The truncated-word mechanism's first cut (minimum stem length 2)
   mis-resolved `דר'` (64 occurrences) and `ור'` (44 occurrences) against
   unrelated independent-corpus words (`דרך`, `ורן`) - both were actually
   `ר'` ("Rabbi," a hyper-common standalone title this text prefixes
   freely) misread as a truncated single word. Fixed two ways: added `ר'`
   → `רבי` as its own root entry (safe - it doesn't commit to WHICH rabbi,
   since the actual name already follows as a separate word, unlike the
   `ר"י`-class fused acronyms above), and raised the minimum stem length
   to 3 (every length-2-stem hit tested was wrong; every length-3+ hit was
   right).
3. (Carried from the first pass) A print-specific orthography detail found
   by checking rather than assuming: guessed `כנה"ג` (gershayim before the
   last letter) for Knesset HaGedolah; the corpus's actual form is `כנ"הג`
   (gershayim one position earlier) in all 7 occurrences.

**Still not a correction pipeline** - both scripts are read-only, nothing
writes `part1.json`, no decision was recorded, no review/apply stage was
built (not requested). Verified: `tests/test_corpus_invariants.py` +
`tests/test_pipeline_logic.py` still 77/77 after the rebuild; both
scripts' `--json` output accounts for all 1577 forms with none dropped.

**No other known open items beyond the above.** Full detail, evidence,
and the complete dated history behind every claim above is in
`PROJECT-STATUS-HISTORY.md`.
