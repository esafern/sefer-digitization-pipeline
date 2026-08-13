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

## ►► SESSION HANDOFF — read this first, 2026-08-13

### State on disk right now (verified, not remembered)

- **Branch `master`, HEAD `9a0a3e9`, working tree has one uncommitted
  change**: this handoff rewrite itself (`PROJECT-STATUS.md` condensed,
  the detailed fix trail moved to `PROJECT-STATUS-HISTORY.md`'s "Second
  source-audit round — all 12 confirmed bugs fixed" entry) - commit it as
  part of finishing this task.
- **Every confirmed bug from the second source-audit round is fixed,
  verified against real data (not just read as plausible), and
  committed** — all 12, including the two ★-marked live corpus-damage
  risks. One commit per fix on `master`: `99c20d9` (★1) `c664044` (★2)
  `87faa24` (finding 5) `96f5505` (finding 11) `03765a2` (finding 7)
  `69da3be` (finding 9) `fa20715` (finding 6) `33fb95f` (finding 8)
  `0e7aa84` (finding 12) `16cffc0` (finding 10) `9a0a3e9` (findings 3+4).
  Full fix-by-fix evidence is in `PROJECT-STATUS-HISTORY.md`.
- **Review dashboard is running** (`python3 review_server.py` - check
  `lsof -i :8420` first per CLAUDE.md; **was restarted 2026-08-13** to
  pick up the feature below - server code isn't hot-reloaded like the
  data files are, remember to restart after backend changes).
- **New feature, 2026-08-13**: reviewers can now flag/replace ANY word in
  a klal's text, not just ones the machine pipeline already flagged
  (direct user request). Click any plain word -> "Flag / correct word"
  panel -> type the correction -> Save. New `manual_correction` decision
  type in `review_decisions.jsonl` (own snapshot: `{word_index,
  original_word}`, no `corrections_part1.json` entry involved); new
  `POST /api/decisions/manual` endpoint; `apply_reviewer_decisions.py`
  gained a same-shape apply pass (`apply_manual_correction`, same-position
  replace only, no word-count change, drift-checked against the live
  corpus text directly). Verified end-to-end in the browser: panel opens
  with correct context, save updates the nav badge/legend live AND
  matches a fresh `/api/klalim` fetch exactly, reopening shows the
  decision pre-filled with working history. All 19 tests still pass.
- **Extended, 2026-08-13, same day**: the panel above can now DELETE a
  word too, not just replace it (direct follow-up request). `chosen_text
  == ""` (explicitly empty, not missing) means delete;
  `apply_manual_deletion` in `apply_reviewer_decisions.py` removes the
  word entirely, sharing the insert/delete opcodes' one-word-count-change-
  per-klal-per-run guard since deletion shifts every later index in that
  klal (an ordinary replace doesn't need this - same position in, same
  position out). Confirm-to-delete is an in-panel arm/click-again pattern,
  not a native `confirm()` dialog (those block further page interaction
  once triggered and are inconsistent with the rest of this app). A word
  marked for deletion still renders (recording a decision and applying it
  are always separate steps here) with a strikethrough
  (`.pending-delete`). Found and fixed one real bug while verifying this:
  the panel didn't refresh its own state after a successful save, so a
  completed delete left a stale "click again to confirm" button behind -
  fixed by having both Save and Delete re-open the panel against the
  fresh post-save state, which doubles as the save confirmation (no
  separate flash needed). Verified end-to-end incl. the per-klal-per-run
  guard against real data (`apply_reviewer_decisions.py --dry-run`
  correctly applied one manual-delete per klal and skipped a second one in
  the same klal with the expected message). All 19 tests still pass.
  **2026-08-14, user request**: the 4 test decisions this verification
  work left on klal 3 (word 3 `למד`->`למד-TEST` id `7cb1a6ac7bc1`; word 7/
  10/22 deletes, ids `0022073fb6de`/`5b34465c4b41`/`3a0e19aa9bfc`) were
  directly removed from `review_decisions.jsonl` - a deliberate,
  explicit exception to this file's normal append-only/never-delete rule
  (see CLAUDE.md), made only because these were self-identified test
  garbage with zero real editorial content, never applied to `part1.json`,
  and the user explicitly asked for them to go. Left two other klal-3
  entries alone (`ee438748e37f`/`b57f13bc2a7d`, word 3, chosen_text=`למד`,
  no note) - those are the user's own real action re-confirming the
  correct word after seeing the test garbage, not something I created.
  Verified: 0 strikethrough words remain in klal 3, its 4 remaining
  Human-Decided words are all legitimate. 19/19 tests still pass.
- **Every previously-tracked corpus-content gap is closed** (klal 5, 29,
  30/75/88, 37, 69, 206, 217 - see `PROJECT-STATUS-HISTORY.md` "All open
  corpus-content bugs closed" and "Multi-page reconstruction APPLIED").
  `rebuild_all.sh`'s pytest gate (`tests/test_corpus_invariants.py`) is
  14/14 passing; `tests/test_review_server.py` (5 more, browser/
  Playwright-based, NOT part of the automated gate) is 5/5.

- **RESOLVED 2026-08-14 - reindexing incident from the geresh-spacing
  fix above.** `./rebuild_all.sh --skip-vision` after that corpus-wide
  fix left the dashboard showing corrections/notes pointing at the wrong
  word (user-reported: "corrected text points to the wrong word... note
  is correct but does not match the highlighted text... green box not
  seen for the first correction"). **Root cause 1**: `--skip-vision`
  skips `verify_corrections_vision.py`, so `corrections_verified_
  part1.json` kept its PRE-fix `word_index_in_final_text`/`corrected_word`
  while `corrections_candidates_part1.json` (which DID regenerate) already
  had the correct POST-fix values - confirmed on klal 1: candidates file
  said word 437/`ומדקמהד'`, the stale verified file still said word
  468/`ומדקמהד`. Fixed by running the FULL rebuild (live vision
  re-verification, not `--skip-vision`) - see the geresh-spacing commit.
  **Lesson: `--skip-vision` is only safe for a fix that doesn't change any
  klal's WORD COUNT** - it silently keeps old candidate positions/content
  for anything that does, and nothing currently detects or warns about
  this.
  **Root cause 2, found while verifying the fix**: the full rebuild
  correctly realigned MACHINE candidates, but every EXISTING HUMAN
  DECISION recorded before the reindex was keyed by its OLD word_index -
  10 real decisions (7 `candidate_choice`, 1 `manual_correction`, 1
  `punctuation_choice`, plus one of my own re-filings that itself had an
  off-by-one) were silently orphaned, no longer attached to the candidate
  they were actually about. Recovered all 10 by re-filing each at its
  correct new position (verified byte-for-byte, not guessed): `bbox`
  (pixel-based, never changes) for the 7 `candidate_choice` decisions;
  unique word-content search for the 1 `manual_correction`; the
  candidate's own stored `word_before`/`word_after` anchor for the
  punctuation one. `punctuation_candidates_part1.json` itself (67 of 74
  entries) needed the same relocation - 7 were anchored to a `word_before`
  of a bare `"'"`, i.e. the exact floating-apostrophe artifact just fixed,
  and were dropped rather than guessed at (can be regenerated fresh by
  `propose_punctuation_part1.py` if wanted; its own cache already
  invalidates on this clean_text change).
  **Root cause 3, a real independent bug found via the same verification**:
  unlike `candidate_choice`/`punctuation_choice` (which only ever look up
  a decision for a position that already has a live candidate, so a stale
  decision at an abandoned position just never surfaces), `api_klal()`'s
  `manual_correction` handling rendered EVERY recorded decision
  unconditionally, with no check that the word still matched. Fixed in
  `review_server.py` (both `api_klal()` and `api_klalim()`'s count) to
  skip a decision whose `original_word` no longer matches the live text -
  this bug existed independent of this specific incident and would
  recur on any future edit that shifts a manual-corrected word's position.
  **Verified end-to-end after all fixes**: every live `candidate_choice`/
  `manual_correction`/`punctuation_choice` decision cross-checked against
  current `part1.json`/`corrections_part1.json`/`punctuation_candidates_
  part1.json` content (0 mismatches), confirmed visually in the browser -
  klal 1's scan-pane box renders green (`hl-state-human`) again, text pane
  correctly underlines the decided word. 19/19 tests pass.

### NEXT STEPS, in order

**1. Hardening worth doing, not yet done**: `assemble_corrections_
dataset.py` has no cross-check that a verified candidate's `corrected_
word` still matches the CURRENT `part1.json` content at its `word_index_
in_final_text` before serving it - the reindexing incident above only
surfaced because a human happened to notice and report it, not because
anything detected the staleness. Same drift-detection shape as
`apply_reviewer_decisions.py`'s `snapshot_matches()` would catch this
class of bug automatically on any future edit that changes word
positions, instead of relying on remembering to always run the full
(non-`--skip-vision`) rebuild.

**2. Two witness adjudications still need a genuine human call before
any text edit** (carried forward from the prior session, both recorded
as `klal_flag` decisions in `review_decisions.jsonl`, not text edits) -
**now resolvable directly through the new manual-correction feature
above**, no script/hand-edit needed:
   - Klal 30 - `ידן`/`ידו` (DocAI/Tesseract) vs what the scan actually
     shows, `ידך` - *both* engines are wrong here. User has independently
     stated the correct reading is `ידו` (matching Tesseract), possibly as
     part of a longer phrase `את ידו הנפלאה` - neither DocAI nor Tesseract
     captured an `את` at this position, and whether to insert it too is
     still an open question for the user to resolve, ideally via the new
     panel directly on klal 30 word ~48 in the dashboard. (klal_flag id
     `5220cb956175`)
   - Klal 88 - `רתם`/`התם` - the print genuinely shows `ר`; this is a
     source-text/broken-type anomaly, not an OCR error - editorial
     awareness only, do NOT silently correct. (id `f15d365a9168`)
   - Also klal 30, docai_token_index 22: a witness decision was recorded
     accidentally while browser-testing a UI fix (clicked to test a
     counter, not a real read of the crop) - flagged via `klal_flag` id
     `f39158d3ba5a`, still needs an actual look.

**3. The broader witness queue (tier B/C/D, ~411 items across klal
30/75/88) is still fully open** and is the only real second opinion on
the ~3,800 words reconstructed for those three klalim. Its tier labels
are now trustworthy (finding 3's per-word lexicon fix) and it now
includes DocAI-omission cases it structurally couldn't show before
(finding 4) - working through it (page-step to 24/37/40 in the
dashboard, click a box) remains the highest-value follow-up QA, though
it is not a gate on anything.

**4. Unverified risks flagged by the second audit round, not confirmed
bugs, worth someone's attention** (full reasoning in
`PROJECT-STATUS-HISTORY.md`'s audit entry): an `apply_event` is never
invalidated when its underlying decision is later reverted outside the
normal flow; witness decisions are keyed `(klal_id, docai_token_index)`
with no page component (safe only because `PAGE_TO_KLAL` is currently
1:1); `propose_punctuation_part1.py`'s cache key doesn't cover the
prompt text or model, so editing the prompt would silently reuse old
proposals (dormant pipeline, no live effect); `PASS3_KNOWN_FALSE_
POSITIVES` suppresses ALL Pass-3 hits for klal 4/18/34, not just the
investigated spans; `review_frontend/app.js` fetches `/api/klalim` once
at init and never refetches, so nav badges/legend/klal-page map go stale
after a rebuild elsewhere until a manual reload; `strip_head_header`'s
folio-numeral heuristic ate klal 89's real marker `פט` once (caught by
an existing guard that run, but the rule can't reliably tell a folio
numeral from a klal marker).

**5. General standing caution, not a specific open bug**: docstring/
comment overclaims turned up repeatedly across both audit rounds this
session, in different validator scripts - a script's claimed coverage is
not evidence of its actual coverage. Worth a sanity pass on any OTHER
validator's docstring before trusting it at face value.

**No other known open items beyond the above.** Full detail, evidence,
and the complete dated history behind every claim above is in
`PROJECT-STATUS-HISTORY.md`.
