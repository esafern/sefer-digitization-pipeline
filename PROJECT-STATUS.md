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

**1. URGENT, before anyone runs `apply_reviewer_decisions.py` for real:
it will currently DELETE text a reviewer voted to KEEP.** `apply_insert_
removal` (line 183) is called with the snapshot's `final_text` and never
consults `decision["chosen_text"]` - the `replace` path has a no-op guard
for "chosen equals current text," the `insert` path has none. **Two such
decisions are already pending right now**: klal 4 word 0 (`chosen_text:
'ד'`) and klal 57 word 0 (`chosen_text: 'נז אין'`) - `--dry-run` reports
both as ordinary inserts; running for real would strip klal 4's opening
marker and klal 57's gematria marker + first word. `review_frontend/
app.js:343` is what offers "keep current text" as a choice for
insert-opcode candidates in the first place, so this is reachable through
normal dashboard use, not an edge case. **Do not run `apply_reviewer_
decisions.py` without `--dry-run` until this is fixed.** Full evidence in
`PROJECT-STATUS-HISTORY.md`, finding ★1.

**2. 10 of 29 delete-opcode candidates (9 of them `possible_omission`,
the highest-value class) never render in the review dashboard's text
pane** - they're filed at `word_index == len(words)` and the renderer's
loop never reaches that index. A reviewer working the text pane normally
will never see klal 84/106/114/138/164/171/175/193/211/219's delete
candidates at all; they're only reachable via the scan pane. Full
evidence in `PROJECT-STATUS-HISTORY.md`, finding ★2.

**3. The other 10 confirmed bugs from the same audit (numbered 3-12 in
`PROJECT-STATUS-HISTORY.md`) are lower-severity - witness-tier
mis-triage, a structural blind spot for DocAI omissions, stale nav
badges after a witness save, delete-opcode vision prompts asking the
model to choose against the literal string "None," and others - read
that entry in full before picking the next piece of work; don't
triage from this summary alone.**

**4. Klal 30/75/88's four tier-A witness adjudications were carried
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

**5. General standing caution, not a specific open bug**: docstring/
comment overclaims have now turned up multiple times this session across
different validator scripts (see `PROJECT-STATUS-HISTORY.md` for the
specific instances) - a script's claimed coverage is not evidence of its
actual coverage. Worth a sanity pass on any OTHER validator's docstring
before trusting it at face value.

**No other known open items beyond the above.** Full detail, evidence,
and the complete dated history behind every claim above is in
`PROJECT-STATUS-HISTORY.md`.
