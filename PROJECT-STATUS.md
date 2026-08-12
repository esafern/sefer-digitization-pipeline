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
issue was resolved. New dated entries go there, not here — this file
should only ever hold the current handoff.

## ►► SESSION HANDOFF — read this first, 2026-08-12 (state as of the second source-audit round, same day as the original handoff below)

### State on disk right now (verified, not remembered)

- **Branch `master`, HEAD `be25d12`, working tree has one uncommitted
  change**: this split itself (`PROJECT-STATUS.md` rewritten,
  `PROJECT-STATUS-HISTORY.md` added) - commit it as part of finishing this
  task. Six commits before that on top of `86c83ef` culminated in `be25d12`
  (two of the four carried-forward tier-A adjudications applied to
  `part1.json`, the other two recorded as `klal_flag` decisions - see
  "carried forward" note under NEXT STEPS below).
- **Review dashboard is running** (`python3 review_server.py` - check
  `lsof -i :8420` first per CLAUDE.md). The user has been actively
  reviewing in it during this session; expect more decisions in
  `review_decisions.jsonl` by the time this is read.
- **Every previously-tracked corpus-content gap is closed** (klal 5, 29,
  30/75/88, 37, 69, 206, 217 - see `PROJECT-STATUS-HISTORY.md` "All open
  corpus-content bugs closed" and "Multi-page reconstruction APPLIED" for
  full traces). `rebuild_all.sh`'s pytest gate (`tests/test_corpus_
  invariants.py`) is 14/14 passing. Separately, `tests/test_review_
  server.py` holds 5 more tests (browser/Playwright-based, NOT part of
  the automated gate, run manually) - `tests/` as a whole is 19 tests,
  which is where a "19 tests" figure comes from if you see one; the
  zero-tolerance rebuild gate itself is still exactly the 14 in
  `test_corpus_invariants.py`.
- A dedicated Opus audit (second round of this exercise - see NEXT STEPS)
  found **12 confirmed bugs, none fixed yet**, two of them live
  corpus-damage risks. Full findings, with evidence, are in
  `PROJECT-STATUS-HISTORY.md` under "Second source-audit round — 12
  confirmed bugs, NONE FIXED YET, 2026-08-12". Read that entry before
  touching the review/apply workflow.

### NEXT STEPS, in order

**1. ★1 FIXED 2026-08-12.** `apply_reviewer_decisions.py`'s no-op guard
(previously `replace`-only: skip applying when `decision["chosen_text"]
== snapshot["final_text"]`) now also covers `insert`-opcode decisions,
which share the same "chosen text equals what's already stored" no-op
semantics - `insert`'s `final_text` is the extra span
`apply_insert_removal` would otherwise unconditionally delete. Re-ran
`--dry-run` against the live decisions log: the two previously-dangerous
pending decisions (klal 4 word 0, klal 57 word 0 - both "keep current
text") now report `confirmed-no-op` instead of `insert`; all 12 currently
pending `candidate_choice` decisions resolve as no-ops (0 replace, 0
insert/delete) - i.e. running the script for real right now would change
nothing in `part1.json`, only log confirmations. Not yet run for real
(that's a separate deliberate step, per CLAUDE.md's "recording a decision
and applying it to the corpus are always two distinct steps") - safe to
when wanted. Related, NOT fixed: `delete`-opcode's mirror case ("confirm
nothing belongs here", `chosen_text=''`) still gets misreported as
"skipped - drift" by `apply_delete_insertion`'s `not chosen_text` guard,
rather than recorded as its own no-op - cosmetic (over-cautious label,
not data loss) but worth a follow-up.

**2. ★2 FIXED 2026-08-12.** `review_frontend/app.js`'s `renderKlalBody`
only rendered a delete-opcode gap marker for `i < words.length` (the
`forEach` loop's range); added one extra check after the loop for
`gapsBefore[words.length]`, rendering it at the end of the body - the
same position it would have taken at `i == words.length`. Verified two
ways: (a) in the browser via the live dashboard, klal 219's previously
invisible candidate (`ס"ח ונכון הוא`, 98% vision confidence,
`possible_omission`) now renders as a clickable red marker at the end of
the text and opens the normal decision panel; (b) programmatically
against the live API for all 10 affected klalim
(84/106/114/138/164/171/175/193/211/219) - each has exactly one delete
candidate at `word_index == word_count`, all now covered by the same
check. `tests/test_review_server.py` (5/5) still passes.

**3. Finding 5 FIXED 2026-08-12.** `check_klal_token_orphans.py`'s
`real_span_tokens` hard-stopped at a 1-page gap and returned `None` for
anything wider, and the caller `continue`d past that `None` with no
accounting - so this check silently never ran on 7 klal-boundary pairs,
including klal 30->31, 75->76, 88->89 (all real 2-page gaps: one full
intervening page consumed entirely by a multi-page reconstruction, no
klal marker of its own). Those three are exactly the klalim the session
handoff already flags as having "almost no independent verification."
Generalized `real_span_tokens` to walk any number of intervening pages
instead of special-casing one; added explicit skip accounting with an
assertion that checked+skipped always equals the total pair count (same
fix shape as round 1's `validate_klal_span_coverage.py` finding).
Result: **"Checked 204" (was 197), 0 skipped, and Pass 3's full-span gap
scan now runs on klal 30/75/88 for the first time and reports no gaps** -
not fully independent of DocAI (the reconstruction's own source), but a
genuine assembly-correctness check (wrong token order/dropped/duplicated
content would still be caught) that had simply never executed before.

**4. The remaining 9 confirmed bugs from the same audit (numbered 3, 4,
6-12 in `PROJECT-STATUS-HISTORY.md`) are lower-severity - witness-tier
mis-triage, a structural blind spot for DocAI omissions, stale nav
badges after a witness save, delete-opcode vision prompts asking the
model to choose against the literal string "None," and others - read
that entry in full before picking the next piece of work; don't
triage from this summary alone.**

**5. Klal 30/75/88's four tier-A witness adjudications were carried
forward and closed 2026-08-12**: `וכוותיידו`→`וכוותייהו` (klal 88) and
`בתוס ' ד"ה`→`כתוס ' ד"ה` (klal 30) are **APPLIED** to `part1.json`,
rebuild clean. `ידן`/`ידו` (klal 30 - scan actually shows `ידך`) and
`רתם`/`התם` (klal 88 - source-text anomaly, DocAI is faithful, do NOT
correct) are **NOT** text edits - both recorded as `klal_flag` decisions
in `review_decisions.jsonl` (ids `5220cb956175`, `f15d365a9168`) pending
a human call. The broader witness queue (tier C: 94 items, tier B: 102,
tier D: 217) is still open and still the only real second opinion on the
~3,800 words reconstructed for klal 30/75/88, but per finding 3 above,
its own tier triage is now known to be wrong for 16.1% of items - read
that finding before trusting a tier label at face value.

**6. General standing caution, not a specific open bug**: docstring/
comment overclaims have now turned up multiple times this session across
different validator scripts (see `PROJECT-STATUS-HISTORY.md` for the
specific instances) - a script's claimed coverage is not evidence of its
actual coverage. Worth a sanity pass on any OTHER validator's docstring
before trusting it at face value.

**No other known open items beyond the above.** Full detail, evidence,
and the complete dated history behind every claim above is in
`PROJECT-STATUS-HISTORY.md`.
