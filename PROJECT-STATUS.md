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
