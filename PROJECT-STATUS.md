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

### State on disk right now (verified, not remembered)

- **Branch `master`, HEAD `b472db4`.** Working tree is clean except
  `witness_vision_cache.db`, which a detached background process (see
  "In progress" below) is actively writing to - leave it alone, it'll be
  committed once that process finishes.
- **Review dashboard is running** (`python3 review_server.py`, port 8420)
  and does NOT need a restart - nothing in this session's work touched
  server code past what was already live.
- **Every previously-tracked corpus-content gap is closed** (klal 5, 29,
  30/75/88, 37, 69, 206, 217; the second source-audit round's 12 confirmed
  bugs; the reindexing incident's 3 root causes - all fixed, verified
  against real data, and committed). `rebuild_all.sh`'s pytest gate
  (`tests/test_corpus_invariants.py`) is 14/14 passing;
  `tests/test_review_server.py` (5 more, Playwright, not part of the
  automated gate) is 5/5. Full evidence for all of the above is in
  `PROJECT-STATUS-HISTORY.md`.
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

### IN PROGRESS - not yet done, check on this first next session

**`verify_witness_vision.py`'s full 419-item vision-adjudication pass
over the witness queue is running detached** (`nohup`+`disown`, survives
independent of any session) - started fresh against the bbox-corrected
queue. Check progress with `sqlite3 witness_vision_cache.db "SELECT
COUNT(*) FROM witness_cache;"` (target 419) or `ps aux | grep
verify_witness_vision`. It writes `vision_selected`/`vision_
transcription`/`vision_confidence`/`vision_reasoning` into
`reconstruction_witness_queue.json` in ONE write at the very end of its
loop, not incrementally - so the queue file will show nothing until it's
fully done. Once it finishes: review the results, commit `reconstruction_
witness_queue.json` and `witness_vision_cache.db`, and report what it
found. This is a TRIAGE layer only (per its own design) - it does not
record `witness_choice` decisions itself, so it doesn't close item #2
below on its own.

### NEXT STEPS, in order

**1. Hardening worth doing, not yet done**: `assemble_corrections_
dataset.py` has no cross-check that a verified candidate's `corrected_
word` still matches the CURRENT `part1.json` content before serving it -
the reindexing incident above only surfaced because a human noticed and
reported it. Same drift-detection shape as `apply_reviewer_decisions.py`'s
`snapshot_matches()` would catch this class of bug automatically.

**2. One witness adjudication still needs a genuine human call before
any text edit**, resolvable directly through the manual-correction
feature (klal 30 word ~48 in the dashboard):
   - Klal 30 - `ידן`/`ידו` (DocAI/Tesseract) vs what the scan actually
     shows, `ידך` - *both* engines are wrong here. User has independently
     stated the correct reading is `ידו`, possibly as part of a longer
     phrase `את ידו הנפלאה` - whether to insert `את` too is still open.
     (klal_flag id `5220cb956175`)
   - Klal 88 - `רתם`/`התם` - the print genuinely shows `ר`; source-text/
     broken-type anomaly, not an OCR error - editorial awareness only,
     do NOT silently correct. (id `f15d365a9168`)

**3. The broader witness queue (tier B/C/D, ~411 items across klal
30/75/88) is still fully open for human review** and is the only real
second opinion on the ~3,800 words reconstructed for those three klalim.
The in-progress vision pass (see above) will add a machine second
opinion once it finishes, but doesn't substitute for working through it
in the dashboard (page-step to 24/37/40, click a box) - highest-value
follow-up QA, though not a gate on anything.

**4. Unverified risks flagged by the second audit round, not confirmed
bugs** (full reasoning in `PROJECT-STATUS-HISTORY.md`'s audit entry): an
`apply_event` is never invalidated when its underlying decision is later
reverted outside the normal flow; witness decisions are keyed `(klal_id,
docai_token_index)` with no page component (safe only because
`PAGE_TO_KLAL` is currently 1:1); `propose_punctuation_part1.py`'s cache
key doesn't cover the prompt text or model; `PASS3_KNOWN_FALSE_POSITIVES`
suppresses ALL Pass-3 hits for klal 4/18/34, not just the investigated
spans; `review_frontend/app.js` fetches `/api/klalim` once at init and
never refetches, so nav badges/legend go stale after a rebuild elsewhere
until a manual reload; `strip_head_header`'s folio-numeral heuristic ate
klal 89's real marker `פט` once (caught by an existing guard, but the
rule can't reliably tell a folio numeral from a klal marker).

**5. General standing caution**: docstring/comment overclaims turned up
repeatedly across both audit rounds this session, in different validator
scripts - a script's claimed coverage is not evidence of its actual
coverage.

**No other known open items beyond the above.** Full detail, evidence,
and the complete dated history behind every claim above is in
`PROJECT-STATUS-HISTORY.md`.
