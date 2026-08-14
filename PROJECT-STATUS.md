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
   - **STILL OPEN, not investigated this session**: witness decisions
     keyed `(klal_id, docai_token_index)` with no page component (risk 2,
     safe only because `PAGE_TO_KLAL` is currently 1:1);
     `propose_punctuation_part1.py`'s cache key doesn't cover the prompt
     text or model (risk 3, dormant pipeline, no live effect).
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

**No other known open items beyond the above.** Full detail, evidence,
and the complete dated history behind every claim above is in
`PROJECT-STATUS-HISTORY.md`.
