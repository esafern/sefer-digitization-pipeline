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

## ►► SESSION HANDOFF — read this first, 2026-08-16 (continued into 2026-08-17)

### DONE 2026-08-17 — Parts 2-3 infra item 3: the previously-throttled vision-adjudication pass completed clean over the full extended page range (76-249)

Re-ran `pipeline/build_gematria_trace.py --vision` (via `venv/bin/python3` -
the system python lacks PyMuPDF/`fitz`, which the vision tier needs to crop
the PDF; the mechanical-only runs earlier this session didn't hit this since
`--vision` wasn't passed) over `part2.json`/`part3.json`, pages 76-249 (was
76-235 before this session's extraction extension - klal 664-667 now
reachable). 62 vision adjudications requested (cache-backed, per Lesson 12's
cache-key discipline - only 3 transient `503 UNAVAILABLE` retries this run,
all succeeded, no manual resume needed this time). `part1/2/3.json` all
confirmed untouched (this pass only writes the two trace files + its own
cache db) - correct, matches the pipeline's read-only-on-corpus design.

Final: `gematria_trace_part2.json` 222 klalim (148 ok / 45 mismatch / 29
not-found, was 144/36/42 mechanical-only); `gematria_trace_part3.json` 223
klalim (167 ok / 31 mismatch / 25 not-found, was 161/22/40 mechanical-only
at the old 76-235 range). Vision resolved some not-found/mismatch into ok
and reclassified others; not yet spot-checked individually against the raw
scan beyond what the tool's own cached reasoning shows - same caveat as the
Part 1 vision tier had at merge time.

### DONE 2026-08-17 — Parts 2-3 infra item 4: investigated the 14 high-value garbled-text leads (DocAI reads clean in all 14; stored text diverges more severely than a single-word typo in most); NEW finding: a cheap word-count outlier sweep surfaces at least 9 klalim shaped like klal 663's merge bug, including 2 of the 14 leads

Investigation only, no corpus writes — per explicit user scope decision, this
does NOT apply anything to `part2.json`/`part3.json`; CLAUDE.md's Parts 2-3
gate still requires its own separate go-ahead before any actual correction
there.

**Method**: for each of the 14 leads (klal 281, 282, 299, 300, 374, 389, 408,
412, 482, 510, 543, 549, 613, 634 — from the `build_gematria_trace.py` pass
logged above, all at content agreement ≤0.333), pulled the raw
`docai_word_boxes` tokens in true reading order (Y-center, then RTL x —
never array order, per this session's confirmed marker-ordering artifact)
starting immediately after the confirmed marker, and compared against the
stored `clean_text` opening.

**All 14 DocAI continuations read as clean, grammatical Rabbinic Hebrew** —
no garbling on the scan/OCR side, confirming the marker positions
themselves are trustworthy anchors (consistent with the original finding).
**The stored text's divergence is not uniformly a single corrupted word.**
For 6 (300, 374, 389, 510, 543, 549) the opening word(s) match DocAI closely
and the garble sits a few words in — the shape the original finding assumed.
But for at least 6 more (281, 282, 299, 408, 412, 482, 613) the stored
opening diverges from DocAI within the first clause into an entirely
different sentence, not a plausible single-token misread — e.g. klal 299
stored `מדאורייתא ע"ש ועיין מ"ש עליו...` vs DocAI `ידע אמורא רישא דברייתא
ולא ידע סיפא...`, klal 613 stored `כר' יוחנן לגבייהו כ"מ פ"ד...` vs DocAI
`רב פ"ה מה' ע"ז : תריד רבא ורבא בר עולא...`. This shape (whole differing
sentences, not a garbled token) is closer to what CLAUDE.md's Parts 2-3 gate
already warned Part 1's fixes might not generalize to.

**NEW, from a cheap mechanical check run on the side of this investigation**
(per Lesson 8 — corpus-wide structural sweeps catch what per-klal review
misses): sorted every Parts 2-3 klal by stored word count. Median is 75
words, mean 284.9 (skewed by outliers). Top 10: klal 663 (9,545 — already
flagged, "almost certainly several klalim merged"), 410 (8,041), 301
(3,146), 256 (3,111), 664 (2,656), 409 (2,594), 556 (2,550), 283 (2,505), 307
(2,142), **549 (2,121 — one of the 14 leads above)**. klal 634 (also one of
the 14) is not top-10 but at 750 words is ~10x the median. This is a NEW
finding, not previously logged: at least 9 klalim beyond 663 are large
enough to be plausible merge-of-several-klalim candidates by the same
mechanism, not yet individually checked. 549 and 634 being both on this list
AND on the garbled-opening list is suggestive (a merge could produce both
symptoms — wrong/garbled text right after the marker if the marker actually
belongs to different content than what got stored under it) but not
confirmed; needs the same scan-crop check as the 3 that were already
resolved this way (klal 30/75/88, see `reconstruct_multipage_klalim.py`
history).

**NEXT STEP, not yet done**: scan-crop verification per klal (the project's
standing method for resolving this class of disagreement, not further token
comparison) — starting with the 6 whole-different-sentence cases and the 2
length-outlier overlaps, before any of this becomes a write to `part2/
3.json`. Full length list for the other 7 top-10 outliers (410, 301, 256,
664, 409, 556, 283) not yet cross-checked against their own DocAI markers -
worth doing before concluding klal 663 is the only merge case in the corpus.

### DONE 2026-08-17 — klal 4 word 36 corrected (טרור→טהור), a data issue: user-recorded manual_correction applied via `apply_reviewer_decisions.py`

User recorded the correction directly via the review dashboard (word 36:
טרור→טהור), confirming an already-vision-verified candidate (decision
5d65c7612a3c, `ai-vision-verify-flagged-candidates`, 2026-08-16, conf 0.98
"CANDIDATE CORRECTION SUPPORTED" - the visible ה construction distinguishes
it from the stored ר). Applied via `apply_reviewer_decisions.py` (1 applied,
189 already-promoted skipped as no-ops, 10 pre-existing drifted decisions
correctly left untouched pending separate human review - unrelated to this
fix). `./rebuild_all.sh` clean after, 174/174.

Note-quality aside, not a corpus issue: this decision's note initially read
as a copy-paste of the unrelated backfill-script template (mismatched
`decision_type`/reviewer), which could have been mistaken for leftover test
data - corrected in place (uncommitted at the time, so no append-only-history
concern) to accurately describe it as the user's own dashboard action.

### DONE 2026-08-17 — Parts 2-3 infra item 2: `docai_word_boxes/` extended to full gapless coverage (pages 1-249, was 1-235 estimate); 5 verified `gematria_trace_part1.json` corrections applied (klal 129, 190, 180, 182, 194); `klal_page_regions.json` rebuilt (206→211 marker-anchored)

Per the user's "go ahead with 1 2 3 4" directive under the 2026-08-17
infrastructure-only Parts 2-3 authorization (CLAUDE.md's gate note) - this is
item 2 of that list ("apply 5 verified corrections to
`gematria_trace_part1.json`"), plus the extraction-coverage groundwork item 2
depended on.

**Physical extent of the whole 667-klal work, confirmed by direct rendering,
not estimate**: scouted the PDF directly and found page 247 is the literal
end - klal 666/667 followed by the traditional closing benediction "סליקו
כללי התיו וסליקו כללי הגמרא... בעורת האל הגדול הגבור והנורא" and a printer's
colophon. Page 250 is confirmed separate back matter (an index, "מפתחות על
כללי הגמרא"), not part of the klalim proper. `docai_word_boxes/` extended in
two passes this session (82→235 as a rough estimate, then 235→249 once the
true end was located) for full gapless coverage 1-249, 0 extraction failures
either pass.

**5 `gematria_trace_part1.json` corrections, each independently re-verified
against raw `docai_word_boxes` tokens before applying** (per Lesson 19 - a
trace-builder agent's claim is not applied on its say-so alone): klal 129
(page 47→48, marker_position=843), klal 190 (page 68→69, marker_position
added=378) - both already verified earlier this session; klal 180, 182, 194
newly verified this pass and added as brand-new entries (previously entirely
absent from the trace file) - klal 180 page 67 token 319 exact "קף" match;
klal 182 page 67 token 576 "קפכ" for expected "קפב" (ב/כ misread, status
`marker_found_content_mismatch`); klal 194 page 70 token 5 "קצר" for expected
"קצד" (ד/ר misread, status `marker_found_content_mismatch`). Total trace
entries 219→222. Cross-checked against `part1_header_anchored_alignment.json`
after applying - all 5 already agree independently (matched_page 48/69/67/
67/70, all `trusted: true`), consistent rather than contradictory.

`klal_page_regions.json` rebuilt off the corrected trace: 206→211
marker-anchored (211-206=5, exactly the 5 klalim just fixed), 16→11 heuristic
fallback. Full `pytest tests/ -q`: 188 passed. `./rebuild_all.sh` (with
vision, not skip-vision): completed clean, "174 passed", "== done ==".

Item 3 (resume throttled Parts 2-3 vision-adjudication pass) and item 4 (the
14 high-value garbled-text leads in Parts 2-3 - klal 281, 282, 299, 300, 374,
389, 408, 412, 482, 510, 543, 549, 613, 634) still open. Item 4 needs its own
separate explicit go-ahead before writing any actual correction to `part2/
3.json`, per CLAUDE.md's gate note - "go ahead with 1 2 3 4" authorized this
infrastructure work, not yet confirmed to extend to applying Parts 2-3
corpus corrections.

### DONE 2026-08-17 — retroactive backfill: 65 pre-existing AI-pass findings pushed into word-level highlighting (the "not started here" question from bug #1's entry, now resolved); a mandatory drift check caught 49 more that would have highlighted the wrong or now-nonexistent word

Per direct user request, following on from the two review-harness bugs
above. Scope: every currently-open (`needs_revisit: true`) general-level
(`word_index: null`) `klal_flag` - 109 total across 10 reviewer categories -
checked for a parseable single-word candidate to backfill with a real
`word_index`, using `pipeline/review_server.py`'s new `_word_level_ai_flags()`
mechanism (bug #1 above).

**Parser, built and tested before trusting it on real data**: the two
biggest categories (`ai-vision-verify-flagged-candidates`, 58 flags/122
individual candidate lines; `ai-semantic-spotcheck*`+`ai-lexicon-full-review`,
33 flags) both use a consistent `w<N> '<word>' -> ...` shape - parsed 122/122
vision-verify candidate lines successfully (0 unparseable), further filtered
to skip verdicts of `ORIGINAL TEXT CONFIRMED` (68 - already resolved by that
pass's own vision check, correctly must NOT be re-highlighted as open) and 2
non-standard-verdict lines (klal 198's w1055/w861 - already fixed via
`manual_correction` earlier this session, note is simply stale), keeping only
`CANDIDATE CORRECTION SUPPORTED`/`UNCERTAIN` (52).

**Mandatory drift check, not optional - caught 49 real problems**: every
parsed (word_index, word) pair was checked against the word ACTUALLY at that
position in current `part1.json` before backfilling; only an exact match
proceeded. 49 of 114 candidates failed this check - some from this session's
OWN edits shifting indices (klal 65/66's boundary fix moved everything past
its insertion point; klal 65 w71/w75 no longer even exist, truncated by that
fix), most from independent EARLIER fixes making the old note simply stale
(e.g. klal 4/25 w403/714 `איהן`->`איהו` already corrected, klal 149 w130
`דשמוא`->`דשמואל` already corrected). Backfilling any of these 49 blind would
have highlighted either the WRONG word or a position that no longer exists -
this is exactly the failure mode CLAUDE.md Lesson 19 warns about (a
"fixed"/"applied" claim needs checking against a real diff, not assumed from
how carefully the note was written), applied to a backfill instead of a fix.
Full list of all 49 skips kept in this session's scratch space (not
committed, regenerable from the same parser against current data).

**65 backfilled** (`reviewer: "local-backfill-2026-08-17"`, each a new
`klal_flag` with `word_index` set, `needs_revisit: true`, note pointing back
to the original finding's decision id for full context rather than
duplicating the reasoning). Spot-checked live via `/api/klal/88` - both
backfilled entries (w622, w1111) render correctly through the same
`ai_flag`-opcode mechanism bug #1 built and already browser-verified; not
re-verified in the browser again since it's the identical, already-proven
code path consuming new data, not new code.

**NOT backfilled, deliberately, with reasons** (18 flags across 4
categories): `ai-scan-crop-verification` (6 klalim) and `ai-followup-
unflagged-findings` (4) describe boundary/marker-level findings, not a
single disputed word_index within the klal's own body text - forcing one
would misrepresent the finding. `ai-title-vs-opening-check` (3) compares the
whole `title` field against the whole opening phrase, not one word.
`local-harness-coverage-audit`/`local-manual-crop-verify` (5, this session's
own earlier work) already have precise, individually-known positions but
weren't run through this same generic backfill pass - low priority since I
already know exactly what they are; can be added directly if it matters
later.

188/188 pytest, `rebuild_all.sh` clean.

### DONE 2026-08-17 — review harness BUG #2 fixed: a recorded-but-not-yet-applied manual correction showed the OLD disputed word styled green (Human-Decided), with no indication of what it would actually become

**User bug report, klal 2** (found immediately after bug #1 above was fixed
and while re-testing): "the flag was on, an issue is mentioned in the notes
but the word was not highlighted" - expected, not a regression, see bug #1's
"NOT retroactively backfilled" scope note; klal 2's flags all predate the
fix. "I then manually corrected it, and the word is now marked in green, but
it has the wrong text." Root-caused directly against the real record
(`2009bc46c399`, klal 2 word 109, `אטינא`->`אמינא`): the decision was
recorded correctly, but `part1.json` still had `אטינא` (recording and
applying are always separate steps, per this project's standing
architecture) - the frontend's manual-correction render path showed that
OLD text with only a color change, no indication of the CHOSEN replacement,
which reads as "wrong" rather than "pending."

**Fix, `review_frontend/app.js`/`app.css`**: a pending replacement (chosen
text set and different from the still-current word - editing a word to
itself needs no such treatment) now renders struck-through, followed by an
arrow and the chosen text in green bold, mirroring the existing
`pending-delete` treatment rather than inventing a new pattern. The
machine-candidate pathway (vision A/B choices) already surfaced this via
its hover tooltip ("Your decision: ...") - this gap was specific to the
manual-correction pathway, which had no indication at all, not even on
hover.

**Verified live**, same standard as bug #1: restarted the server, confirmed
against klal 2's actual real (not synthetic-test) pending correction -
screenshot shows `אטינא` struck through, `→`, `אמינא` in green bold, exactly
as designed. 188/188 pytest (frontend-only change, no Python logic touched).

**The apply mechanism itself** (user's direct follow-up question): `pipeline/
apply_reviewer_decisions.py`, run manually - reads every decision without an
`apply_event` yet, re-verifies the live text still matches what the decision
was recorded against (drift check - refuses if the corpus changed underneath
it since), and only then writes the corpus edit plus an `apply_event` marking
it done. Never automatic, never part of `rebuild_all.sh` - recording a
decision and promoting it into the corpus are always two distinct, deliberate
steps (CLAUDE.md "Human review decisions"), by design, not an oversight - the
FEEDBACK gap fixed here was that the pending state looked like a mistake
instead of an intentional waypoint.

### DONE 2026-08-17 — review harness BUG fixed: a klal_flag naming a specific word (AI-pass free text) was never highlighted in the text pane, forcing the reviewer to find it by reading prose and searching by eye; also applied klal 1 w446's real fix (ומידו->ומיהו) that surfaced the bug

**User bug report, klal 1**: "I saw klal 1 was flagged for review. When I looked at the notes it said there was a question about מידו vs ומיהו - but the questionable word was not highlighted, I needed to find it myself." A second, related report - after fixing it via the dashboard, the corpus text didn't visibly change - turned out to be expected behavior (recording a decision and applying it to part1.json are always separate steps, per this project's standing architecture), not a bug; the actual gap was upstream of that.

**Root cause, both parts a genuine code BUG, not a data issue**: `detect_real_word_substitution.py`-class AI passes record a candidate word by name in a klal_flag's free-text `note`, but never set the decision's `word_index` field - even though `append_decision()` has always accepted it on any decision type. `review_decisions.py`'s own `history_for()` docstring had baked in the wrong assumption ("klal_flag rows structurally always carry... None"), and `tests/test_corpus_invariants.py` had a zero-tolerance gate actively ENFORCING it (`(word_index is None) != (decision_type == 'klal_flag')`) - so the highlighting mechanism (which only reads the structured `corrections` array built from `corrections_part1.json`) had no way to know klal 1's disputed word was word_index 446; the note was prose the frontend never parsed.

**klal 1 w446 itself - the real fix that surfaced this**: applied `ומידו`->`ומיהו` (manual_correction, user's own choice, independently re-verified before applying - see the separate entry below, three converging signals: direct 9000 DPI crop, 201x-vs-1x frequency, and semantic parse of the sentence). This *directly contradicted* an earlier 0.95-confidence vision-adjudication result that had closed the same candidate as "no correction needed" - a real disagreement between two automated signals that got silently resolved in favor of vision (Lesson 9 violation), never flagged as uncertain. Recorded a reconciling decision (`b4033dc18363`) documenting why the vision read was wrong.

**Fix, in `pipeline/review_server.py`**: split klal_flag handling into two structurally-separate concerns rather than patching the symptom -
- `_general_klal_flag_current()`/`_general_klal_flag_history()` (word_index IS None) - the reviewer-facing "needs a second look" panel, unchanged behavior, now explicit about what it excludes.
- `_word_level_ai_flags()` (word_index IS NOT None) - synthesizes a `corrections`-shaped entry for each still-open word-level flag, same pattern `api_klal()` already used for manual_correction entries (2026-08-13) to get highlighted without a real `corrections_part1.json` row behind them. A manual_correction on the same word_index wins (redundant AI flag suppressed) - a human has already acted on it.
- `tests/test_corpus_invariants.py`'s integrity gate relaxed to match: every OTHER decision type must still always carry a real word_index (unchanged, still enforced); only klal_flag may now legitimately be either.
- `review_frontend/app.js`/`app.css`: new `ai_flag` opcode branch, routed through the EXISTING manual-correction panel (already displays a `note` field and lets the reviewer propose a fix or dismiss - no new panel needed), new distinct visual style (dashed purple underline, `.state-ai-flag`) so it reads as "AI-flagged, not vision-verified" rather than being confused with the vision-backed states.

**Verified, not assumed**: 4 new unit tests (general-panel isolation, synthesis, closed/out-of-bounds skipping, manual_correction precedence) - `tests/test_pipeline_logic.py`. Live end-to-end check against the running dashboard (restarted to pick up the code change, not just data): recorded a real test klal_flag with `word_index=1` on klal 3, confirmed via direct API calls that `/api/klal/3` includes the synthesized highlight at exactly word 1 and `/api/klal/3/flag` (general panel) does NOT leak it, then via the actual browser - screenshot confirms the correct word highlighted with the new dashed-purple style at the right position (distinct from a pre-existing green Human-Decided underline on a different word in the same klal), and a direct DOM-level click confirms the manual-correction panel opens with the AI's note pre-populated in the note field. Test flag reverted after. 188/188 pytest (was 184), `rebuild_all.sh` clean.

**Scope, explicitly NOT done**: this fixes the mechanism GOING FORWARD - any future or re-run AI pass that sets `word_index` on a single-candidate klal_flag will now render correctly. It does NOT retroactively backfill already-recorded flags: `detect_real_word_substitution.py` itself is a read-only detector (found 49 klalim / 83 candidates per its original run) that has never itself called `append_decision` - the actual recording was a separate, apparently one-off/session-specific action not preserved as a live re-runnable script, so simply "fixing the detector" doesn't retroactively help past batches. A real, still-open question: is a backfill pass (parsing existing free-text notes to recover word_index for the ~49+ affected klalim across this and similarly-shaped passes like `ai-lexicon-full-review`) worth doing, and if so scoped as its own deliberate task - not started here, no scope decision made.

### DONE 2026-08-17 — `pipeline/build_gematria_trace.py` BUILT (the missing marker/trace generator, generic per the reusable-pipeline directive); Parts 2-3 traces produced for the first time; 7 findings logged below, NONE fixed

Closes the "NOT YET DONE: the marker/trace-building script itself" item in
the entry below. Nothing in this repo regenerated `gematria_trace_part1.json`
- the file is tracked, hand-corrected and load-bearing
(`build_klal_page_regions.py` anchors every region on it,
`check_klal_token_orphans.py` reads it, and its page attribution reaches
`build_corrections_dataset.py`) but its generator was lost/archived. This is
that generator, written parameterized (corpus file(s), DocAI directory, page
range, marker x-band, thresholds - repeated `--part SRC:DEST` pairs trace as
ONE continuous sequence sharing a cursor) rather than as a Parts-2-3 one-off.

**How a marker is accepted** - three tiers, each with its own evidence bar,
plus an optional vision tier. Reading order is re-derived from bbox-center Y
and RTL x on every page and DocAI's array order is never used for anything
(the marker-out-of-reading-order artifact is confirmed three times in this
corpus). The search is monotonic and unbounded forward, with ONE bound that
is load-bearing: a candidate may be accepted on POSITION ALONE only within
~2 pages of the cursor. The first version had no such bound and it destroyed
the run - klal 10's absent marker matched an unrelated margin `י` 37 pages
later at content ratio 0.0, the cursor jumped there, and 201 of 222 klalim
then reported not-found (Lesson 6, exactly). Tier 2 ("content-anchored":
anchor on the stored opening, take the short marker-band token before it,
consult the numeral not at all) is what finds a marker DocAI misread in a way
nobody catalogued, without widening tier 1 into the unbounded fuzzy numeral
search Lesson 5 warns against.

**Part 1 validation** (the point of running it there first). 219 ok / 0
mismatch / 3 not-found mechanically, 220/0/2 with `--vision`, against the
tracked file's 202/5/12 over 219 entries. **207 of 222 klalim reproduce the
tracked file's page AND marker_position exactly**; every one of the 20
disagreements was investigated individually against the raw token context,
and all 20 favour the new output. Note the tracked file's own statuses are
heavily hand-corrected (20 of its `ok` entries carry content_match_ratio 0.0,
flipped by the 2026-08-07 "status was stale" pass), so an exact status match
was never the target.

**Parts 2-3 traces built for the first time** - `gematria_trace_part2.json`
(144 ok / 36 mismatch / 42 not-found) and `gematria_trace_part3.json` (161 /
22 / 40), pages 76-235, ~2.5s mechanical. Part 2 starts on page 77 (klal 223
at token 53), the Part 2/3 boundary is mid-page 164 (klal 444 at token 253,
klal 445 at token 312), and marker pages are strictly monotonic across all
363 placed markers - an independent structural check that the cursor never
desynchronized.

**FINDINGS - all logged, none fixed, each needs its own routing:**

1. **`gematria_trace_part1.json` has two stale page attributions, both
   independently corroborated.** klal 129 is recorded as page 47; its marker
   is an exact `קכט` on page **48** token 843 (content 0.875). klal 190 is
   recorded as page 68 with `marker_position: null` and a note saying the
   position was never re-derived; it is on page **69** token 378 (exact `קץ`,
   content 1.000). Corroboration from a completely separate source:
   `part1_header_anchored_alignment.json` already says 48 and 69 for these
   two. Same class as klal 198's page 70->71 fix earlier today, and the same
   consequence - `build_corrections_dataset.py` reads the alignment file, so
   the disagreement between the two files is live.
2. **Three klalim are absent from `gematria_trace_part1.json` entirely** -
   180, 182, 194, the three split out of their neighbours in the 2026-08-06
   work. All three now locate cleanly: 180 at page 67 token 319 (exact `קף`,
   0.875), 182 at page 67 token 576 (content-anchored; DocAI read the marker
   `קפכ` for `קפב`, 0.750), 194 at page 70 token 5 (`קצר` for `קצד`, 1.000).
   The alignment file's pages (67/67/70) agree with all three.
3. **Two stale gematria fields in the trace file.** Its `expected_gematria`
   for klal 115/116 is `קיה`/`קיו`, from the pre-fix conversion that lacked
   the ט"ו/ט"ז exception (correct: `קטו`/`קטז`), and its `stored_gematria`
   for klal 150 is `קנ` where `part1.json` now stores `קן`. Derived-file
   drift, not a corpus problem - a regenerated trace does not inherit it.
4. **klal 57's marker is genuinely unresolved and the surrounding text looks
   wrong.** A marker-band token at page 32 index 694 sits between klal 56
   (592) and klal 58 (746) where klal 57's must be, but DocAI reads it `נו`
   (=56, and klal 56's own marker at 592 also reads `נו`), and a vision crop
   independently read `נו` too at 0.95 confidence - so the script left it
   unplaced rather than force it. Separately, the tokens after 694 run
   `אין דלא אזלא סוגיא...` while klal 57's stored text has
   `אין הלכה כשיטה . לא אמרינן אלא היכא דלא איפסיקא הלכתא בהדיא כחד מינייהו
   או דלא אזלא סוגיא...` - i.e. the marker+`אין` pair sits in the MIDDLE of
   the stored text's own sequence. Needs a scan crop, not more inference.
5. **klal 10 has no marker token on its page at all.** Its opening
   (`איידי דקתני במתניתין...`) anchors at reading rank 431 on page 18 with
   preceding tokens at x1 0.51-0.65 - mid-line, no margin glyph. Either
   DocAI dropped the marker or klal 10's boundary is not at a marker.
6. **Parts 2-3: 14 klalim have a real (non-placeholder) stored text that
   disagrees with the scan at their own confirmed marker** - klal 281, 282,
   299, 300, 374, 389, 408, 412, 482, 510, 543, 549, 613, 634, all at content
   agreement <= 0.333. Their stored text is visibly garbled at the opening
   (`תליאא`, `פעלוקלוהל`, `המכק"דהגש`, `הרהשי"אי מבירליתשא`,
   `דרעשת"ין לדרשג"ייל`, `הבאגממורא ובסתבראת להקסדכמרותן`, `אדהודמדייא`).
   These are the highest-value Parts 2-3 leads this pass produced: the marker
   position is trustworthy, the text is not. A further 11 klalim with real
   stored text could not be placed at all (452, 453, 454, 544, 545, 548, 569,
   571, 575, 664, 666), and 6 placed `ok` sit at a borderline 0.50-0.67
   (411, 415, 419, 542, 556, 596).
7. **DocAI extraction stops at page 235, but the work does not.** klal 663 is
   the last klal placed (page 234); 664-667 are unplaced because their pages
   were never extracted. Confirmed by direct render, not inferred: page 236
   and page 242 both still carry the `יד מלאכי / כללי התיו` running header
   and solid body text, while page 250 is back matter (the
   `מפתחות על כללי הגמרא` index). So the body runs to somewhere in 243-249
   and **extraction needs extending by ~8-14 pages before Part 3's trace can
   be finished.** Relatedly, klal 663's stored `clean_text` is 9,545 words -
   by far the largest in the corpus and almost certainly several klalim
   merged.

**Context for the counts, not a new finding**: 115 of the 445 Parts 2-3
klalim (70 in Part 2, 45 in Part 3, 0 in Part 1) store `clean_text` as
literally `"<numeral> כלל <klal_id>"` - placeholders, already quantified with
the identical 115 figure and id list in PROJECT-STATUS-HISTORY.md. They
account for 71 of the 82 not-found and 44 of the 58 mismatch entries.
`has_comparable_opening()` treats them as "nothing to compare" rather than "the
content disagrees" (a different finding) and locates them on numeral + margin
+ sequence alone, capped at `marker_found_content_mismatch` - never `ok`,
since `ok` asserts exactly the thing that cannot be checked for them.

**Vision tier**: implemented on `vision_adjudication_common` (cache keyed
crop+expected+observed+context+prompt_hash, per Lesson 12), used only for
borderline (0.15-0.50), ambiguous, or placeholder-with-misread-numeral cases
- never for an unambiguous mechanical match, which a test enforces. It
independently re-confirmed klal 34's hand-corrected marker (`לד` at 0.98) and
correctly REFUSED klal 57's. A full Parts 2-3 vision pass is in progress and
is being throttled upstream (repeated `503 UNAVAILABLE - high demand` on
gemini-3.6-flash); the cache makes it resumable, so re-running `--vision`
picks up where it stopped and re-spends nothing.

**NOT DONE, deliberately**: `gematria_trace_part1.json` was NOT overwritten.
Regenerating it would change 20 entries, add 3, and move two page
attributions that `build_klal_page_regions.py` and
`part1_header_anchored_alignment.json` both consume - a data change to a
tracked, hand-corrected, live-pipeline file that needs its own explicit
go-ahead, the same as any correction. `rebuild_all.sh` is unaffected (the new
script is not wired into it). `part1/2/3.json` sha256 verified unchanged
before and after.

### DONE 2026-08-17 — full DocAI extraction over the estimated Parts 2-3 page range (93-235, 143 pages); klal_id_to_gematria()/gematria_to_value() moved into corpus_io.py

143 pages extracted (`docai_word_boxes/page_93.json` through `page_235.json`),
0 failures, ~300s total, same processor/calling pattern as the 10-page test
slice and Part 1's own extraction. `docai_word_boxes/` now has continuous
coverage page 1-235 with zero gaps (verified by listing, not assumed).
Real cost still not independently verified (see the entry below on why -
service-account billing-API permission ceiling) - this is real spend the
user authorized on an estimate, not a confirmed-cheap number.

Moved `klal_id_to_gematria()`/`gematria_to_value()` (previously only in
`tools/validate_part1_corpus_integrity.py`) into `pipeline/corpus_io.py`
so the new marker-detection script (below) reuses the same tested
conversion instead of a second copy - directly exercising the reusable-
pipeline goal rather than deferring it. `validate_part1_corpus_integrity.py`
keeps aliased module attributes so every existing call site (including
`tools/check_next_marker_and_title.py`'s `integrity.klal_id_to_gematria`
reference) keeps working unchanged. Spot-checked the moved function
against known values including Part 2/3's own boundaries (223->`רכג`,
445->`תמה`, 667->`תרסז`). 166/166 pytest, `rebuild_all.sh` clean.

### OPEN 2026-08-17 — Parts 2-3 scan-linkage/verification infrastructure: user explicitly authorized starting it (partial override of the standing gate, see CLAUDE.md); reusable-pipeline goal newly documented; extraction stage confirmed to need no new code; marker/trace-building stage NOT yet built - in progress

Per direct user request. Full context/reasoning is in CLAUDE.md's updated
Parts-2-3-gate callout - not duplicated here in full, but the key facts:

**New durable goal, previously undocumented anywhere** (added to CLAUDE.md
as its own top-of-file callout): this pipeline's ultimate purpose is to be
REUSABLE for other historical Hebrew texts, not a Yad-Malachi-only tool.
This is a real constraint on how new code gets written from this point on
(prefer parameterized/documented/reusable scripts, extend the `corpus_io.py`
shared-library pattern rather than one-off scripts), not just an aspiration.

**Scope of what's authorized now vs still gated**: building the scan-
linkage/verification INFRASTRUCTURE for Parts 2-3 (extraction, marker/
trace-building, boundary verification) is authorized, starting now.
Applying any actual Parts 2-3 correction still needs its own separate
explicit go-ahead - same two-step principle as the rest of this pipeline
(review vs apply are always distinct deliberate steps).

**Fact-finding done before any code was written, not assumed**:
- `part2.json`/`part3.json`'s stored `page` field is WRONG - confirmed by
  directly rendering PDF page 30 (part2's own klal 223's claimed page):
  it shows PART 1 content (klal ~45-53, "כללי האלף" header), not Part 2 at
  all. **No scan-linkage of any kind currently exists for Parts 2-3**, not
  even basic page attribution - this matches and sharpens what the
  now-partially-superseded gate already said ("without its own scan-
  linkage/vision-verification infrastructure ever having been built or run
  there at all").
- Scouted the real PDF directly (low-DPI renders at pages 77/85/140/200) to
  find where Parts 2-3 actually live: **page 77 already shows klal 224-227**
  - Part 2 starts essentially immediately after Part 1 ends (page 76), no
    gap, no separate title/front matter page. Page 200 shows klal ~559
    (deep in Part 3). The alphabetical section headers (`כללי האלף` ->
    `כללי ההא` -> ... -> `כללי הריש`) run CONTINUOUSLY across all three
    parts, confirming Parts 1/2/3 are editorial/project-management
    divisions of ONE continuous printed sequence, not separate physical
    sections with their own front matter. **Working estimate**: the full
    667-klal work spans roughly pages 14-225 of the 337-page PDF (~3.6
    klalim/page, matching Part 1's own density); pages beyond ~225 are
    presumed back matter, not yet confirmed.
- **Decided against wholesale "regenerate Parts 2-3 from scratch"**: Parts
  1/2/3 all came from the SAME original chunker-era extraction run (one
  shared process, chunked into all three part files at once - see
  CLAUDE.md "Pipeline shape"). Part 1 isn't cleaner because its original
  extraction was better; it's cleaner because it alone has since been run
  through hundreds of rounds of the DocAI-diff-and-review pipeline. The
  right move is to give Parts 2-3 that SAME treatment (diff current stored
  text against fresh DocAI, correct via the normal review pipeline),
  preserving whatever's already correct, not discard it. **Real caveat,
  not waved away**: the one CONFIRMED fact (page-furniture contamination at
  17% of Parts 2-3's klalim vs ~1 instance in Part 1) is evidence
  Parts 2-3's klal BOUNDARIES specifically may need more than word-level
  diffing catches - word-diffing cannot detect a klal split, merged, or
  mis-numbered (exactly the bug class fixed in Part 1 today: klal 65/66,
  klal 17/18, klal 197/198 - see entries below). A dedicated boundary/
  chunking verification pass is therefore a REQUIRED part of this work, not
  optional, separate from ordinary word-level correction candidates.
- **Terminology check on today's own 3 fixes, since it's directly relevant
  to what this new work will produce**: klal 65/66 and klal 17/18 were pure
  DATA cleanup (direct `part1.json` edits, no code touched). klal 197/198
  was BOTH - a real CODE bug (`pipeline/build_klal_page_regions.py`'s
  `load_markers()`, inconsistent with its own sibling function in the same
  file) and two DATA fixes (`gematria_trace_part1.json`,
  `part1_header_anchored_alignment.json`). The lesson for Parts 2-3: pure
  word-level diff-and-review only ever produces data cleanup: boundary/
  linkage work can surface CODE bugs in the new trace-building script
  itself, not just data issues in what it reads.

**Extraction stage - confirmed to need NO new code.** Ran a real 10-page
test slice (pages 83-92, the first pages past what was already cached)
using the exact calling pattern from the already-archived
`archive/scripts/extend_docai_ocr.py`, unmodified except for pointing at
`berlin_square_corrected.pdf` instead of that archived script's pre-page-
-order-fix `berlin_square.pdf`. Succeeded cleanly: 10/10 pages, 2.65s/page
average, 800-980 tokens/page, consistent with Part 1's own pages, no
errors. Given the new reusable-pipeline goal, this script should be
rehabilitated into a clean, parameterized `pipeline/`-tier script (using
`corpus_io.py`, no hardcoded processor IDs where avoidable) rather than
left archived/one-off - not done yet, small cleanup not new logic.

**Cost check, not fully resolved**: could not get a live, verified
Document-AI billing figure - the `doc-ai-worker` service account lacks
Cloud Billing API access (`gcloud billing accounts list` ->
PERMISSION_DENIED, same permission ceiling as the earlier Cloud Vision API
situation this session). Reported the published-rate order of magnitude
(likely low-single-digit dollars for the full ~150-page Parts 2-3 range) as
an ESTIMATE ONLY, explicitly caveated as not live-verified, not stated as
fact. If precision matters, needs the user's own console access.

**NOT YET DONE**: the marker/trace-building script itself (the one
genuinely new piece of code this work needs - no live or archived script
currently builds a `gematria_trace`-equivalent for any part) - currently
being scoped via a collaboratively-developed prompt, to be handed to a
high-effort background agent, then independently re-verified before merging
(same standard as every agent-produced code change this session). Full
extraction over the ~150-page Parts 2-3 range also not yet run (only the
10-page test slice); pinpointing the exact Part 2/3 boundary (~klal 445)
and Part 3's end page also not yet done precisely (currently a working
estimate from low-DPI scouting only).

### DONE 2026-08-17 — the klal_page_regions.json fix's real payoff: 6 previously-UNVERIFIABLE candidates (klal 167) now exact-token locatable; scan-verified: 1 genuine DATA issue fixed, 3 disconfirmed print-faithful, 2 left genuinely uncertain

Direct follow-through, not just a claim the earlier fix "should help": re-ran
`locate_word()` from `tools/verify_flagged_candidates_vision.py` against all
16 previously band-estimate-located candidates in `flagged_candidates_
vision_report.json`, using the freshly-fixed `klal_page_regions.json`. 6 of
16 - all of them klal 167's, exactly the klal that fix targeted - now
resolve to an exact single token instead of a multi-line band (one of
which, per that locator's own docstring, used to come back as an entire
page-paragraph). The other 10 (klal 4/37/38/123/176/189/204) are unrelated
to today's fix and remain band-estimate.

Scan-verified all 6 at 1400-7200 DPI, generous margin, context checked
against `part1.json` before reading each crop:

- **klal 167 w877 `דרוא`->`דהוא` - CONFIRMED, a genuine DATA issue, FIXED.**
  Context "...דרב נחמן בר יצחק דהוא בתרא פריך לשמואל..." - the crop
  unambiguously shows ה (a clear gap-under-bar, not a plain resh hook), a
  real ר/ה OCR confusion. Recorded as `manual_correction` `6d946f77ec8f`,
  applied.
- **3 DISCONFIRMED (print-faithful, closed, no change)**: w1050 `התימא`
  (candidate `דתימא` - crop clearly shows ה not ד), w1362 `כדנא` (candidate
  `כהנא` - crop shows ד, a closed corner not a gap-shape ה; also the only
  reading that makes grammatical sense, "מילתא כדנא" = "such a matter"),
  w665 `וסליג` (candidate `ופליג` - crop shows a fully closed ס loop, not
  an open-hooked פ). Each closed with its own `klal_flag`
  (`455d8a37716d`/`c578bbf72ef0`/`32bf869d65fe`), scoped to that word_index
  only.
- **2 left OPEN, genuinely uncertain even at 7200 DPI**: w739 and w898
  (both `מקטי` -> candidate `מקמי`). Calibrated directly against clean
  reference letters on the same page (ט from `שיטת`, מ from `תלמיד`)
  before concluding - still could not call the disputed letter confidently
  either way; not forcing a verdict either direction just because it's the
  last one standing. Linguistic signal only, not independent visual
  confirmation (Lesson 9): `מקמי` ("prior to") is a common, well-attested
  Aramaic word; `מקטי` doesn't parse as any standard word - real, but not a
  substitute for a pixel read. Recorded as open `klal_flag`s
  (`a088141d0c51`/`1fa0416a871b`) for a differently-sourced signal later
  (e.g. a fresh vision call, per Lesson 9), not decided on inconclusive
  pixels.

**Verified**: `rebuild_all.sh` clean, 152/152 pytest. `git diff part1.json`
shows exactly the one `דרוא`->`דהוא` change, nothing else touched.

**Batch score, worth naming plainly**: 1 real fix, 3 false leads, 2 genuine
unknowns, out of 6 candidates that were completely unreachable before
today. Not "the fix found 6 new errors" - most of what was previously
unverifiable turns out to be print-faithful once actually checked, which
is itself the expected, calibrated outcome (matches this project's
running pattern: a locate/verify tool existing is not the same as its
candidates being correct - CLAUDE.md Lesson 1/2).

### DONE 2026-08-17 — 3 open items closed: klal 17's marker-contamination DATA issue fixed; the `klal_page_regions.json` continuation-bounds BUG (klal 197/198/167) fixed at both the code and data layer; `detect_ligature_corruption.py` gained the compound-token second pass it was missing

Per direct user request ("do all 3") against the 3 items offered the prior
turn. All corpus-text changes went through the normal manual_correction
pipeline, not a hand-edit; the code/trace fixes were independently
verified against the raw scan/token data before applying, not assumed.

**1. klal 17 w308 `יח` — DATA issue, FIXED.** Closes round 3's marker-
contamination flag (`88d7ab4958f8`). Direct 1200 DPI crop of
`berlin_square_corrected.pdf` page 20 confirms the SAME raw-DocAI-token-
ordering artifact found earlier today for the klal 65/66 boundary: array
position 351 sits between "לעיל" (350) and "בסתם" (352) in the raw
`docai_word_boxes/page_20.json` stream, but its true page position (far-
right margin, bold, own line) is several lines BELOW both - it is klal
18's own marker (klal 18's stored text already correctly opens `["יח",
"אמוראים", ...]`), bled into klal 17's body by the same extraction bug,
not genuine klal 17 content. Klal 17 itself ends cleanly one line above
with a closing colon, exactly matching the crop. Recorded as
`manual_correction` `71a9a7f46daf` (`chosen_text: ""`, i.e. delete - per
`apply_reviewer_decisions.py`'s documented convention), applied, klal 17's
flag closed (`5c314d5ea45a`). Klal 18 untouched, unaffected.

**Cross-reference, worth naming**: `pipeline/build_klal_page_regions.py`'s
own docstring already documented this EXACT artifact class before today
("klal markers sometimes sit OUT OF READING ORDER in docai's raw token
array... the same anomaly already documented for klal 3's own marker...
turned out to also apply to klal 4's marker") and its 2026-08-13 fix
comment independently re-derives the identical klal 17/18 case by marker
position, confirming klal 18's marker sits at token 351 on page 20 with
status `marker_found_content_mismatch` - cross-validating today's crop-
based finding from a completely different code path. Three confirmed
instances now (klal 3/4, klal 65/66, klal 17/18) of the same raw-
extraction-ordering bug independently corrupting BOTH region computation
AND text extraction, fixed piecemeal in each place it was found so far -
worth being alert to a fourth.

**2. `klal_page_regions.json`'s continuation-bounds bug — BOTH a bug and a
data issue, both fixed.** Root cause, traced precisely rather than patched
around: `build_klal_page_regions.py`'s `load_markers()` (used for a klal's
OWN start anchor) required `status=='ok'` only, while
`load_end_boundary_positions()` - in the SAME file - already accepted
`marker_found_content_mismatch` too, citing the established project
convention (also used by `tools/check_klal_token_orphans.py`) that both
statuses carry a real, usable position. That inconsistency meant klal 167
(status `marker_found_content_mismatch`, but its `marker_position` already
individually scan-verified per the trace's own note) was trusted as an END
boundary for its neighbor but not as a START anchor for itself, so it fell
through to the coarse `heuristic_regions()` fallback - no multi-page
continuation support at all - producing the reported "undersized region."
**CODE FIX**: `load_markers()` now accepts both statuses, matching its
sibling function; this also correctly upgrades klal 1/18/86/172 (the same
5 entries `load_end_boundary_positions()` already trusted) from heuristic
to marker-anchored, not just klal 167.

Separately, klal 198 had NO marker position in `gematria_trace_part1.json`
at all (`status: 'marker_not_found_in_window'`) - the code fix alone
couldn't help this one. Searched `docai_word_boxes/page_71.json` directly:
the marker exists, CORRECTLY read as `קצח` (not misread, unlike its
neighbors), at token 242 - one page later than the trace's `page: 70`
attribution, which is presumably why the original search window missed
it. Confirmed by context: token 241 is a klal-closing colon, token 242 is
`קצח` at the right-margin marker x-position, immediately followed by a
coherent new opening. **DATA FIX**: `gematria_trace_part1.json`'s klal 198
entry corrected (`page: 71`, `marker_position: 242`, `status: 'ok'`, noted
inline). This also fixes klal 197's own bug (its continuation was over-
claiming all of page 71 because klal 198, the true next marker, was
invisible to the end-boundary lookup, so it fell through to klal 199
instead) as a direct consequence - no separate fix needed for 197.

Regenerating `klal_page_regions.json` surfaced one more discrepancy - a
zero-tolerance test caught it, not missed it: `part1_header_anchored_
alignment.json` (a separate, older alignment source feeding
`build_corrections_dataset.py` via `trusted_klal_pages()`) still claimed
klal 198's page was 70. **DATA FIX**: corrected `matched_page` to 71 in
that file too (its other provenance fields - `match_ratio`, `jump_tokens`
etc - describe the ORIGINAL heuristic search that produced the now-
corrected wrong answer, and are left as-is; no note-field convention
exists in this file to attach an explanation the way `gematria_trace`'s
does).

**Consequence, expected and welcome**: `build_corrections_dataset.py` had
been scanning the WRONG page for klal 198 candidates this entire time (its
earlier klal 198 corrections this session had to be found by manually
searching `docai_word_boxes/page_72.json` directly - see the earlier
manual_correction entries - which is also consistent evidence: klal 198's
content really does span pages 71-72, matching this fix exactly). Now
fixed: `rebuild_all.sh` generated 13 new correction candidates for the
correctly-attributed page (372 -> 385 total), one of which hit a transient
504 DEADLINE_EXCEEDED on the Gemini call (klal 198 `איבא`->`אליבא`, itself
another dropped-lamed instance) - resolved cleanly on a second
`verify_corrections_vision.py` run, 0 errors remaining.

**Verified**: `klal_page_regions.json` regenerated (206 marker-anchored,
was 200; 16 heuristic, was 22) - visually confirmed klal 197 now caps at
klal 198's true y-position instead of spanning all of page 71, klal 198
gets its own proper region (page 71 + continuation onto 72), klal 167 gets
its documented pages 61-62 continuations. Full `rebuild_all.sh`: clean,
152/152 pytest, including the zero-tolerance scan-region-vs-alignment
cross-check that caught the `part1_header_anchored_alignment.json` gap
above.

**3. `detect_ligature_corruption.py`'s compound-token second pass -
BUILT.** The 2026-08-16 lexicon-crosscheck finding (5 instances, 4
klalim: klal 130/168 w11 `אאמוראי`, klal 150 w167 `אאיזה`, klal 168 w162
`אאביי`, klal 177 w318 `אאידך`) identified a corruption shape pass 1's
single-token `_resolve()` cannot see: "אלא" losing its ל AND its
following space in the same stroke, fusing with the next word. New
`find_compound_candidates()` worked out the exact split point
empirically from the 4 known instances (not assumed): the residue left
by "אלא" losing its lamed is a single leading א, not two - the SECOND
leading א belongs to the fused-in following word, which independently
happens to also start with א in every confirmed case (the space is
dropped exactly where it's least visually detectable, between two
already-identical adjacent letters). Same frequency discriminator as
pass 1: the candidate split's second half must be independently attested
MORE often than the whole unsplit token. Re-running against `part1.json`
finds EXACTLY the 5 known instances, no more, no fewer - a clean fit, not
overfit to the training examples (verified by first testing the naive
"drop 2 characters" version, which found ZERO candidates - caught the
off-by-one before trusting the result, not after). These 5 are already
visible in `review_decisions.jsonl` (`815a2579b395`/`92a97742f8b3`/
`0a15fcf0df69`/`4826eb63b40e`, `ai-lexicon-crosscheck`, `needs_revisit:
true`) - no new flags needed. **Still not scan-verified** - this pass
finds candidates, exactly like pass 1; it does not confirm or apply
anything.

### DONE 2026-08-17 — review-harness coverage audit: user asked "are we ready for Part 2" — answer is no (standing gate unmet), but the question surfaced a real gap: 5 of 7 baselined foreign-character DATA issues were never individually pushed into `review_decisions.jsonl`, invisible on the dashboard despite being "NOT YET DONE: scan-verify" in this file since 2026-08-16. Fixed. Also closed 2 stale-open flags for already-resolved findings.

Per direct user request: "it is critical all open data issues are pushed
into the review harness so they are visible" (human verification itself
explicitly deferred - this was a coverage audit, not a scan-verification
pass). Checked every "NOT YET DONE"/"STILL OPEN" item currently in this
file against `review_decisions.jsonl` rather than assuming a documented
finding is automatically a visible one:

- **klal 17's `יח` marker-contamination candidate (round 3)** - already
  flagged (`88d7ab4958f8`, `needs_revisit: true`). No action needed.
- **The ~411-item witness queue (klal 30/75/88)** - has its own dedicated
  harness mechanism (`review_server.py`'s Witness panel, not `klal_flag`),
  already live. No action needed.
- **`FOREIGN_CHARACTER_BASELINE`'s 7 instances** (`tests/test_
  corpus_invariants.py`, added 2026-08-16) - checked each of the 7 `(klal_id,
  word_index, char)` tuples against `review_decisions.jsonl` for a flag that
  actually covers THAT finding (not just any flag on that klal). Only 2 of 7
  did: klal 39 (w252 `Π`) and klal 66 (w97 `!`, both via the 2026-08-14
  semantic-spotcheck pass, which happened to independently notice the same
  characters). **klal 69 (w338 `&`), klal 74 (w443 `!`), klal 77 (w11 `&` -
  this klal had ZERO klal_flag rows of any kind), klal 167 (w24 `&`), and
  klal 176 (w694 `;`, only mentioned in passing inside an unrelated flag's
  note as "already-reported... not re-reported here") had NO flag actually
  representing this finding.** Pushed 5 new `klal_flag` decisions
  (`reviewer: "local-harness-coverage-audit"`, `needs_revisit: true`,
  ids `36a651302e06`/`780a12ec1343`/`03d27685b8a5`/`6bcd4e5ee6dd`/
  `2a738f66ac41`), each citing the exact character/word_index and
  `FOREIGN_CHARACTER_BASELINE`. Confirmed live via `/api/klalim` -
  `needs_revisit: true` now shows for all 5.
- **klal 66's existing flag (`a6b9c1760675`) is now stale in one detail**
  (not a coverage gap, a labeling one): its note says "word 97 '!'" -
  correct when written 2026-08-14, but the klal 65/66 boundary fix
  (2026-08-17, this file's own entry above) inserted 15 words before that
  position, so the character now sits at word 112 (matching
  `FOREIGN_CHARACTER_BASELINE`'s current entry). `review_decisions.jsonl`
  is append-only, not corrected in place - noted here rather than edited.
  Anyone scan-verifying should locate the `!` by its quoted context
  ("`דברי ב"ד ! חבירו`"), not the stale index.
- **Opposite problem, found while checking klal 206/140**: those two
  klalim's round-2 semantic-spotcheck flags were STILL showing
  `needs_revisit: true` on the dashboard for a specific candidate
  (klal 206 w2, klal 140 w97 - the alef-lamed-ligature hypothesis) that
  had ALREADY been scan-verified and closed print-faithful (this file's
  "DONE 2026-08-16 - item 1 from NEXT STEPS" entry) - that resolution
  explicitly said "No review_decisions.jsonl action needed," which was
  true for applying a correction but left the dashboard showing a resolved
  question as still open. Closed with 2 new `klal_flag` decisions
  (`needs_revisit: false`, ids `033524f85941`/`f4511b968001`), each scoped
  to ONLY that one candidate - both klalim's OTHER round-2 candidates
  (klal 140 w91/w159/w84, klal 206 w161) remain open and untouched.

**No `part1.json` change, no human scan-verification performed** (per the
user's explicit deferral) - this was purely a review_decisions.jsonl
completeness/accuracy pass. 25/25 pytest re-check on the review-decisions
integrity test, dashboard confirmed live via direct API calls, not assumed.

**Answer to the actual question asked**: not ready for Part 2. CLAUDE.md's
standing gate (Part 1 clean AND outside-professional-confirmed, user
directive 2026-08-10, explicitly not to be revisited until then) is
unmet on both conditions - Part 1 still has the witness queue, the klal 17
candidate, the 5 now-visible foreign-character issues just pushed above,
and the ordinary round 1-3 semantic-spotcheck queue outstanding, and no
outside professional review has happened. Per "close open items before
proposing new ones," that queue - not Part 2 - is the next work.

### DONE 2026-08-17 — revalidation round 4 ("pipeline improvements") FAILED mid-task on the monthly Claude spend limit; researched, finished, verified, and merged (`800cd01`), worktree cleaned up

### DONE 2026-08-17 — round-5 modularization: `pipeline/corpus_io.py` extracted, all 25 pipeline/+tools/ scripts migrated, 3 more code bugs found doing it. Independently re-verified and merged to master, worktree cleaned up.

Per direct user request following the `vision_adjudication_common.py` merge
(`800cd01`): that consolidation happened because the SAME bug class had been
found and fixed independently three times across three files before anyone
consolidated. The user's read — "three independent recurrences is a
duplication-of-logic problem, not a coincidence" — scoped this round to
survey the wider `pipeline/` + `tools/` directories, not just the vision
trio. Two commits on branch `worktree-agent-a0b300028d41bab51`, based on
`800cd01`: `c196bd0` (module + 9 `pipeline/` callers), `81f70fd` (16
`tools/` callers + 3 bug fixes).

**New shared module `pipeline/corpus_io.py`**, same documented style as
`vision_adjudication_common.py` (per-item WHY citing the specific prior
incident, functions parameterized rather than reading module globals,
explicit tests). What it holds, with the evidence for each:

- **The DocAI page-token loader** — NINE call sites had written the same
  path-join + exists-check + `json.load` by hand, four of them wrapped in a
  hand-rolled page cache with identical get-or-load bodies. The copies had
  ALREADY diverged on what a missing page returns: some `None`, one `[]`,
  and `verify_reconstruction_witness.py` had no exists-check at all (it
  raised). Every one of those behaviours is preserved exactly — now as an
  explicit `default=` argument per call site instead of an accident of which
  copy you happened to read.
- **`clean_word()`** (alnum filter) — byte-identical in three files, and the
  normalization the whole docai-vs-stored-text diff rests on.
- **`hebrew_letters_only()`** — the SAME function written FOUR ways: a
  27-character literal (`verify_witness_vision.py`,
  `verify_reconstruction_witness.py`, `review_server.py`), a regex
  `[^א-ת]` (`check_klal_token_orphans.normalize`), and a filter over
  `validate_part1_corpus_integrity.HEBREW_LETTERS`. Verified equivalent, not
  assumed (same 27 code points, U+05D0–U+05EA). `review_server.py`'s copy
  carried a comment reading "Must match verify_reconstruction_witness.py's
  HEB/norm() exactly" — because `reconstruction_witness_queue.json`'s stored
  `docai_token_index` values are only meaningful if all three agree. That
  requirement is now structural instead of a note asking the next editor to
  remember it.
- **`PART1_MAX_KLAL`** — was three private literals (plus a FOURTH bare `222`
  found in `propose_punctuation_part1.py`, see bug 2 below, which the
  2026-08-15 hard-wired-value audit missed entirely).
- **`load_klalim()`'s `{"klalim": [...]}`-vs-bare-list tolerance** — present
  in only 2 of 12 readers of those same files, so whether a wrapped file
  loaded depended on which script you came in through. Plus
  `load_part1`/`_sorted`/`_by_id` and **`save_part1()`**, the last
  byte-identical in `apply_reviewer_decisions.py` and
  `apply_punctuation_decisions.py` — the only two scripts in the repo allowed
  to WRITE the hand-edited source of truth, i.e. the least acceptable place
  for two independent copies of how it gets serialized.
- **`trusted_klal_pages()`** — the same alignment filter loop twice, differing
  only in whether the untrusted list was collected (Lesson 15's "silence, not
  a low score"). One function returning both.

**THREE CODE BUGS found in the survey, each an independent instance of the
drift class this round exists to close** — a fix applied to one copy and
never to its siblings:

1. **`tools/propose_punctuation_part1.py` built its Gemini client with a bare
   `genai.Client(api_key=...)`, missing the explicit request timeout.** This
   is the FOURTH instance of that identical missing fix (after the 2026-08-06
   hung-call incident, fixed in `verify_corrections_vision.py` and
   `verify_witness_vision.py`, then found missing in
   `verify_flagged_candidates_vision.py` in round 4) and the FIRST outside the
   vision trio — direct evidence the drift was never confined to the three
   files `vision_adjudication_common.py` was extracted from. Now routed
   through that module's `make_client()`.
2. **The same file's `MODELS_TO_TRY` still listed `gemini-2.5-flash`**, which
   has permanently 404'd since 2026-08-05 ("no longer available to new users")
   and was dropped from the vision scripts' chain then, because a dead model
   silently eats a retry slot on every fallback path instead of ever helping.
   Its independently-written copy never got that fix.
3. **`tools/validate_part1_corpus_integrity.py`'s check 3 produced a
   NON-DETERMINISTIC report.** It iterated a SET of word tuples, so Python's
   per-process string-hash randomization reordered the printed lines on every
   run. Found by trying to prove this refactor behavior-preserving, and
   confirmed empirically rather than inferred: five runs of identical code
   against the identical corpus produced five different orderings of the same
   lines (klal 65/66/67's same-title-cluster block). **This directly defeats
   this project's standing verification method** — diffing two runs (Lesson
   19) — because a real change and pure noise look identical. Fixed with
   `sorted()`; the reported line multiset is provably unchanged.

**Deliberately NOT extracted, each recorded with its reason in the module
docstring** (the survey's judgement calls, not oversights): the three
page-furniture word sets (`WATERMARK_WORDS` / `FURNITURE_WORDS` /
`HEADER_WORDS`+`FURNITURE_RE` — they LOOK like one concept but match by
different rules over different contents, and `build_corrections_dataset.py`'s
own 2026-08-15 comment already records this as examined-and-left-alone;
unifying them would change what each script strips, i.e. a data-affecting
change wearing a refactor's clothes); `propose_punctuation_part1.py`'s sqlite
cache (a genuinely different single-opaque-key schema, correctly keyed for
Lesson 12 in its own way); each script's own PROMPT_TEMPLATE and argparse
setup (nine different CLIs resembling each other only because argparse has
one shape); `validate_title_alphabetical_order.ALPHABET` (22 base letters, an
ORDERING alphabet where a final form is not a distinct sort position — a
different purpose, not a fourth copy of the 27-letter set); and the
`REPO = os.path.dirname(os.path.dirname(...))` line in all 27 scripts, which
is **structurally irreducible** — a `tools/` script must compute the repo
root BEFORE it can put `pipeline/` on `sys.path` to import the shared module
at all. What was removed is everything DERIVED from it.

**Verification, done not assumed:**
- `./rebuild_all.sh` output **byte-identical on all 5 derived files** against
  a baseline captured before any edit (`klalim_demo_dataset.json`,
  `corrections_candidates_part1.json`, `corrections_verified_part1.json`,
  `corrections_part1.json`, `klal_page_regions.json`), **0 live Gemini
  calls**.
- Captured stdout+stderr of **all 14 runnable standalone tools** before and
  after (via `git stash`, same machine, same data) — byte-identical
  everywhere except the two deliberate fixes (the model list, and check 3's
  ordering whose line multiset is provably unchanged).
- **152/152 pytest** (was 140), **14/14 Playwright** (`test_review_server.py`,
  run manually as usual — it exercises `review_server.py`, whose `_load_json`
  and `_witness_norm` both moved).
- **12 new hermetic tests**, 7 of them mutation-verified red/green
  (`save_part1`'s on-disk format, `trusted_klal_pages`' untrusted list,
  `DocaiPageCache` actually caching, the Hebrew-letter set equivalence, the
  timeout fix, the dead-model list, and the sort — the last run 12x per
  mutation since that bug is per-process probabilistic; 11/12 red).
- `part1.json`/`part2.json`/`part3.json`/`review_decisions.jsonl`/
  `lexicon.txt` **sha256-unchanged**. No corpus data touched — this is a
  code-organization refactor only.

**`tests/test_corpus_invariants.py::test_part1_max_klal_constants_agree_with_
the_corpus` was updated, not weakened**: the "three literals agree with each
other" half is now structural, and the half that a shared constant cannot fix
by itself — the constant agrees with the LIVE corpus — is unchanged and still
gates the rebuild. Each module is still read through its own attribute, so a
module re-introducing a private literal is still caught.

**New standing rule added to CLAUDE.md** ("Shared library modules — check
these before hand-rolling a loader, a cache, or a client"), with the count
that motivates it: the identical bug class has now been found in a
hand-maintained copy **five separate times** in this project.

**Independently re-verified before merging, same standard as round 3/round 4**
(not just the agent's own self-report): read `corpus_io.py` and both
`part1.json`-writer diffs (`apply_reviewer_decisions.py`,
`apply_punctuation_decisions.py`) directly - `save_part1()` is the same
`ensure_ascii=False, indent=2` `json.dump` as before, `PART1_PATH`/`REPO`
stay script-level attributes (monkeypatchable in tests, unchanged). Ran the
full test suite fresh in the worktree independently: **166/166** (152
gated + 14 Playwright). Captured master's 4 checkable derived files as a
baseline, ran the worktree's own `rebuild_all.sh --skip-vision`, diffed:
**byte-identical on all 4**. sha256-confirmed `part1/2/3.json`,
`review_decisions.jsonl`, `lexicon.txt` unchanged between the worktree and
master. Independently re-read and confirmed all 3 claimed bug fixes
against the actual diff (the propose_punctuation timeout + dead-model
fixes, and the `sorted()` ordering fix). Merged to master as a merge
commit (`PROJECT-STATUS.md` was the only real conflict - both entries kept,
this one's status updated from NOT YET MERGED); worktree and branch removed.

Background agent (`a06c15e0c6c77fa80`) spun off to look for pipeline-code
improvements terminated early on the monthly spend limit, mid-fix. True
resume wasn't available (`ListAgents` showed nothing reachable - the
process, not just paused, was gone). Researched the worktree directly
instead: confirmed via `git diff` against the worktree's actual base
commit (not against a `master` that had since moved on) that it touched
only code/tests - `pipeline/verify_corrections_vision.py`,
`tools/verify_witness_vision.py`, `tools/verify_flagged_candidates_
vision.py`, `tests/test_pipeline_logic.py`, plus a new
`pipeline/vision_adjudication_common.py` - and the two changed data
files (`adjudication_cache.db`, `flagged_candidates_vision_report.json`)
were pure regenerable side effects of the agent running its own scripts
while testing, not corpus content. **This is a bug situation start to
finish, no data issue anywhere in it** - CLAUDE.md's terminology
distinction applies cleanly here since nothing touched `part1.json`.

**What it did**: extracted the crop/cache/JSON-recovery/retry machinery
duplicated across all three vision-adjudication scripts into
`vision_adjudication_common.py`, motivated by concrete prior drift (the
missing-`prompt_hash` cache-key bug, CLAUDE.md Lesson 12, had already
been independently fixed twice in different scripts before round 3
found it a third time). Fixed two real, confirmed **bugs** in
`verify_flagged_candidates_vision.py` while doing it: a missing
request-timeout on client construction (the 2026-08-06 hung-call
incident class, already fixed in its two siblings), and no per-candidate
error handling in the batch loop - one candidate's total failure used to
crash the whole run and discard every already-paid-for Gemini result,
since output is only written after the loop completes.

**What was left open, root-caused**: ran the worktree's full test suite
(154 tests) - 153 passed, exactly 1 failed:
`test_parse_decision_text_prefers_strict_json_first`. Read the
implementation: `parse_decision_text()`'s docstring promised a 3-tier
JSON-recovery chain (strict `json.loads`, then a sanitized retry, then
lenient field extraction) but the function body only ever called the
lenient extractor - a genuine **bug**, code not data, and almost
certainly the "divergence"/"mutation" the agent's last message
referenced (it had written the correct docstring and test but hadn't
yet finished the implementation to match). This is the same
docstring-overclaims-implementation shape already flagged as a standing
risk elsewhere in this file ("docstring/comment overclaims turned up
repeatedly across both audit rounds").

**Fixed directly** (small, precisely scoped once root-caused): implemented
the two missing tiers (`json.loads`, then `json.loads(sanitize_json(...))`)
before falling through to `extract_json_fields`. Verified: 154/154 pytest
in the worktree, then copied the 5 files into the main checkout (safe -
confirmed `master` hadn't diverged on any of them since the worktree's
base commit), 154/154 pytest again, `rebuild_all.sh` clean (140/140 of
its own two-suite subset, all 5 derived files unchanged - confirms the
refactor is behavior-preserving on every corpus-facing output). Committed
`800cd01`. Worktree and its branch removed (`git worktree remove`,
`git branch -d`) - fully merged, nothing left dangling.

**Pattern worth naming**: this is the THIRD time in this project the same
class of bug - one script's hand-maintained copy of shared logic missing
a fix its siblings already got - has been found independently (missing
`prompt_hash`: twice before this round; missing timeout: found again in a
third script this round; now `parse_decision_text`'s incomplete chain).
See the code-consolidation refactor entry below, spawned specifically to
address this pattern at its root rather than continuing to catch each
recurrence one at a time.

### RESEARCH 2026-08-17 — Document AI tested on both the base (Berlin, square) scan and the Livorno (Rashi) scan for direct comparison; two background jobs launched (full-Part-1 heb_rashi OCR on both scans, and a round-3 semantic-plausibility spot-check)

Per direct user request. Identified the exact klal being used for cross-tool
comparison this session by direct text search rather than by re-deriving its
number from a misread gematria marker (an earlier attempt in this same
session misidentified it - corrected here, not repeated): **klal 183**
(`הלכה כדברי המכריע`).

- **Berlin (base) scan**: didn't need a fresh API call - klal 183 already
  has a cached DocAI reading in `docai_word_boxes/page_67.json` from the
  live pipeline. Extracted it directly: `קפג הלכה כדברי המכריע - אפשר דלא
  אמרי' כן...` - **zero errors**, exactly matches the correct text. Cleanly
  better than both `heb_rashi` (one confirmed error, `כדבני` for `כדברי`)
  and Google Cloud Vision (visibly worse, multiple ה/ס confusions) tested
  earlier on the same passage - though note the comparison isn't perfectly
  apples-to-apples on scan quality, since those two were tested against a
  DIFFERENT physical scan (Przemyśl) of the same text, not this one.
- **Livorno (Rashi) scan**: a genuinely NEW test - DocAI has never
  processed this scan before. Called it fresh (`google-cloud-documentai`,
  same processor already used for Berlin, reusing the calling pattern from
  archived `extend_docai_ocr.py`) on the same Livorno page already tested
  with standard `heb` and `heb_rashi` earlier this session. **Result: DocAI
  got the page header right (`יר מלאכי כללי ההא`, one letter off from `יד`)
  but the body text is heavily garbled** - comparable in severity to
  `heb_rashi`'s attempt on the same page, NOT the dramatic advantage DocAI
  showed on the square scan above. First-pass visual comparison only, NOT
  word-by-word verified (flagging this explicitly, per the correction
  entry below about not overclaiming OCR quality from an unverified
  glance). **Real, calibrated takeaway**: DocAI's apparent edge in this
  project is specific to square/print type, not a general quality
  advantage - it does not show a clear win over the purpose-built
  `heb_rashi` model on genuine Rashi script.

**Two background jobs launched, not yet complete as of this entry:**
1. Full-Part-1 `heb_rashi` OCR pass on BOTH scans - Berlin (pages 14-76,
   62 pages, the actual pages Part 1 occupies per `klal_page_regions.json`)
   and the entire Livorno scan (348 pages, all of Part 1 in that edition).
   300 DPI, ~1.4 sec/page measured directly, ~10 minutes total, $0 cost
   (fully local Tesseract). Output: `/tmp/heb_rashi_full_run/berlin_part1_
   heb_rashi.txt` and `livorno_part1_heb_rashi.txt` (scratch space, not
   committed - regenerable from `/tmp/heb_rashi_full_run/run_ocr.sh`).
   Purpose: enable a full-corpus diff against `part1.json`, not just
   sampled pages. **DONE/REVIEWED 2026-08-17, see the CORRECTION entry
   below (`heb_rashi` on Berlin) - the run completed but is NOT usable as
   a full-corpus witness on either scan; no diff against `part1.json` was
   built, it would have been diffing against near-garbage.**
2. Semantic-plausibility spot-check ROUND 3 - a background agent given the
   full round-1/round-2 methodology and told to draw a fresh ~20% sample
   (`seed 20260817`) excluding both prior rounds' known klalim (33 + 55 =
   88 distinct), same textual-only, no-scan-check discipline. Not
   complete as of this entry - its own findings will log to this file
   directly per its instructions when it finishes.

### DONE 2026-08-17 — semantic-plausibility spot-check ROUND 3, a fresh 20% sample of Part 1 — 8 of 40 klalim flagged, one possible NEW boundary/truncation instance, several already-known findings independently re-derived and NOT re-flagged

Third independent full-sentence reading pass over Part 1, per the round-2
methodology exactly, on a fresh non-overlapping sample. **No corpus file was
touched** — `part1.json`/`part2.json`/`part3.json`/`lexicon.txt` are
sha256-identical before and after; `review_decisions.jsonl` grew 687 → 695
lines with the first 687 byte-identical (confirmed via `git diff`, additions
only, no changed/removed lines); 131/131 pytest before and after. The work is
8 appended `klal_flag` rows, nothing else.

**Sample definition.** Verified round 1's 33 and round 2's 55 recorded klal
sets have **zero overlap** with each other (union = 88 distinct). **Pool**:
all 222 Part-1 klal_ids minus that union = **134 klalim**. **Method**:
`random.seed(20260817)`, `order = random.sample(pool, len(pool))` (full
permutation), then klalim from the front of that permutation while cumulative
word count < 10,500. **Sample**: **40 klalim / 10,539 words / 20.03% of Part
1's 52,609** — 3, 17, 19, 21, 22, 23, 27, 30, 31, 34, 52, 58, 65, 69, 90, 103,
105, 112, 113, 121, 124, 130, 134, 143, 144, 150, 153, 163, 164, 168, 181,
185, 186, 188, 191, 207, 210, 211, 218, 221. Every one was read in full, not
skimmed. A FOURTH pass can exclude round 1+2+3's combined 128 klalim exactly
by re-running the same two lines.

**Result: 8 of the 40 klalim flagged** (`reviewer:
"ai-semantic-spotcheck-round3"`, `needs_revisit: true`, one row per klal).
Flagged: 17, 30, 65, 143, 144, 150, 163, 168. **32 klalim were read and
deliberately NOT flagged**: 3, 19, 21, 22, 23, 27, 31, 34, 52, 58, 69, 90,
103, 105, 112, 113, 121, 124, 130, 134, 153, 164, 181, 185, 186, 188, 191,
207, 210, 211, 218, 221.

- **A possible NEW boundary/truncation instance, klal 65** (same shape as
  round 2's klal 189 flag): the klal's own title phrase repeats VERBATIM
  mid-body (w60-70, identical to w2-12), then the text breaks off unfinished
  right where it starts qualifying a new point (`...נלע"ד דהיינו דוקא` —
  "in my opinion this applies only when...") with no closing colon, jumping
  straight to the next klal's (66) marker at w75 (which itself correctly
  matches gematria(66), so `check_next_marker_and_title.py`'s trailing-marker
  check doesn't catch this — neither does its title check, since the title
  DOES match the klal's own opening line). **NOT YET DONE: scan-verify.**
- **klal 17 w308 `יח`**: a bare `יח` breaks the sentence mid-body
  (`...הנזכר לעיל יח בסתם...`). Corpus-wide `יח` occurs exactly one other
  time in Part 1 — as klal 18's own opening/marker word — making this look
  like marker/page-furniture bleed-through into klal 17's body, a different
  failure shape than the already-scripted trailing-marker check (which only
  looks at a klal's own end, not a marker-shaped token appearing mid-body).
- **Internally-corroborated single-letter/word candidates** (the same
  standard as rounds 1-2 — a correct form of the same word spelled correctly
  elsewhere in the SAME klal or corpus-wide): klal 143 w684 `שמול`→`שמואל`
  (correct `רב פפא בר שמואל` earlier in the same klal, w558); klal 150 w244
  `בשיטרת`→`בשיטת` (correct `בשיטה`/`בשיטת` twice elsewhere in the same
  klal); klal 168 w455-456 `המחילי רבא`→`המחילה רבה` (the fixed idiom
  spelled correctly in klal 69 w192 and klal 163 w609); klal 163 w238
  `למר`→`למד` (ד/ר confusion, restores normal subject+verb grammar).
- **klal 144** (the author's long methodological essay on the 13 middot,
  quoting a manuscript at length) produced the most candidates in one klal:
  w598 a bare `.` token standing where every other `חזון נחום` citation in
  Part 1 has a work-type word (cf. klal 154's near-identical `חזון נחום על
  ספר קדשים`) — plausibly a dropped `ספר`/`סדר`; w924 a stray `י` splitting
  the ordinary phrase `סדר הגון` into three tokens; w949 `למרן` — a common
  real word elsewhere in Part 1 (9x, always the citation idiom `מצאתי למרן
  ב...`) but contextually out of place in a sentence about Moshe Rabbeinu at
  Sinai — plausibly `ומסרן` ("and transmitted them"), the same
  real-word-substitution shape `detect_real_word_substitution.py` already
  tracks; w914 and w1078 `הין`→ plausibly `היו`, LOWER CONFIDENCE since the
  same form recurs a third time in klal 219 (not in this sample) — a
  genuinely repeated form across two klalim could be this print's own
  orthographic convention rather than corruption, flagged for review only.
- **klal 30 w1017 `ראשה`**: sits right after a closing paren+colon ending a
  bracketed Berlin-editor marginal gloss (the `הג"ה מאת... בק"ק בערלין`
  note) and doesn't connect grammatically to what follows — flagged as a
  possible textual seam around the inserted gloss (Success Criterion 2),
  distinct from a word-substitution candidate.

**Due-diligence DROPS — candidates seriously considered, then ruled out
before writing any flag, per Lesson 2/the round-2 calibration standard, not
reported as findings:** klal 23 `ואיהן` (looked like `איהו` misspelled, but
`איהן` recurs 3x elsewhere in Part 1 in the fixed idiom `איהן גופיה` —
genuine spelling, not corruption); klal 69 `דא` (looked incomplete for `דאל`,
but `דא` is a normal standalone Aramaic "this," attested 7x elsewhere in Part
1); klal 124 `אליה מקום כבודו` (looked broken, but the IDENTICAL phrase
appears in klal 92 w328 — a genuine fixed idiom, not corruption); klal 69
w338 `&` (real foreign-character anomaly, but this is ALREADY the
fully-documented `FOREIGN_CHARACTER_BASELINE` finding from the 2026-08-16
character-sanity work — not new, not re-flagged).

**OVERLAP with prior work, called out per klal in each flag's own note** (not
just here): klal 30 — this session also independently spotted w952 `וו"ל`
(same word as klal 30's, correct form `וז"ל`), but that exact word_index is
ALREADY flagged by `ai-lexicon-full-review`; not re-flagged, noted only.
klal 144 — independently also spotted w873 `מהלוקת` and w1040 `ומאו`, both
ALREADY flagged (`ai-lexicon-full-review`/`ai-real-word-substitution`), and
w873 has ALREADY been vision-verified (`ai-vision-verify-flagged-
candidates`) as print-faithful — a useful caution against over-trusting this
klal's other still-unverified candidates. klal 69 and klal 186 (both in this
sample) already carry flags from `ai-title-vs-opening-check`/other passes
for DIFFERENT words than anything found this round; read in full, nothing
new found, not re-flagged, no new row written.

**Calibration note, consistent with rounds 1-2**: dense folio/acronym runs
and terse elliptical argumentation remained the text's normal register
throughout and were not flagged on their own. The 4 due-diligence drops
above are the clearest evidence yet that checking a candidate against the
REST of the corpus (not just intuition about whether a word "looks odd")
is load-bearing — all 4 had a plausible corrupt-looking surface reading that
turned out to be this author's/print's genuine, repeated usage once checked.

**klal 65's apparent truncation: scan-verified and FIXED**, see the
"klal 65/66 boundary fix" entry immediately below. klal 17's `יח`
mid-body marker-contamination candidate is **still NOT YET DONE**; the
rest remain ordinary word-level candidates in the existing queue, same
priority tier as round 1/2's unverified items.

### DONE 2026-08-17 — klal 65/66 boundary fix: klal 66's own title-phrase (15 words) was misattributed to klal 65's tail, with a duplicated marker token; moved to where it belongs. One more word-level fix (מדדיא→מהדיא) found opportunistically during scan verification. Both applied, rebuild clean.

Closes round 3's "possible NEW boundary/truncation instance, klal 65" flag
above, per explicit user direction ("do klal 65 trunc fix"). Diagnosis
does NOT match round 3's own hypothesis (content lost/truncated) — the
true bug is a **misplaced boundary**, no content was ever lost.

**Diagnosis, scan-verified against `berlin_square_corrected.pdf` page 34**
(600 DPI full-context crop across all of klal 65's ending and klal 66's
first two lines, plus 4800-7200 DPI solo-word crops): klal 65's stored
`clean_text` correctly ends `...ועיין מגן אברהם סס"י תר"ץ :` (word 59,
the real closing colon) but then wrongly continued for another 16 words —
klal 66's own title restated as an opening clause (`ב"ד יכול לבטל דברי
ב"ד חבירו אא"כ גדול ממנו בחכמה ובמנין • נלע"ד דהיינו דוקא`) plus a
duplicated copy of klal 66's marker `סו`. klal 66's stored text started
`סו אין ביטול ממש אבל...`, skipping straight from its marker+`אין` to
`ביטול ממש` and missing that same 15-word clause entirely.

**Root cause, confirmed via `docai_word_boxes/page_34.json`'s raw token
stream** (only ONE `סו` token exists on the page, at position 81): the
raw DocAI extraction put that token AFTER the full line of body text
(`ב"ד יכול...דוקא`) it visually introduces, rather than before it — the
rendered page shows `סו` plainly at the START of its own line (`סו אין
ב"ד יכול לבטל...`), not interposed mid-sentence after `דוקא` as the raw
token position implies. This same extraction-ordering artifact is almost
certainly what fooled the original chunker into duplicating the marker
and mis-splitting the boundary in the first place. `gematria_trace_
part1.json`'s `marker_position` for klal 66 inherits the same artifact,
which is why `test_no_new_span_coverage_flags` flagged klal 65 as
"too short" after the fix — a false positive (baselined with full
explanation, `tests/test_corpus_invariants.py`'s `SPAN_COVERAGE_BASELINE`).

**Fix applied directly to `part1.json`** (no existing tool supports a
cross-klal structural move — `apply_reviewer_decisions.py`'s
`manual_correction`/`candidate_choice` types are same-position-only
within one klal — so this followed the established precedent for
boundary fixes, e.g. klal 180/182/194: a careful, directly-verified
one-off edit to the hand-edited source of truth, not a silent
find-replace): klal 65 truncated to its correct 60 words; the recovered
15-word clause inserted into klal 66 between its existing `סו`/`אין` and
`ביטול`, discarding the duplicate trailing `סו` (klal 66 already has its
own correct one at word 0).

**Side effect, expected and confirmed correct, not a new bug**: klal 66's
opening now legitimately duplicates a 10-word phrase with BOTH its
neighbors — klal 65 (whose title it quotes verbatim before qualifying it,
`...דוקא ביטול ממש אבל...` — "this applies only when [it is] an actual
annulment, but...") and klal 67 (which shares klal 65's exact title,
already an established same-title-cluster). All three klalim are one
continuous halachic discussion of a single rule. Before the fix this
same quotation sat wrongly duplicated INSIDE klal 65 alone, which is why
it was already in `INTRA_KLAL_DUPLICATE_PHRASE_BASELINE` — the fix
correctly turns it into a cross-klal duplicate instead, so that klal
entry was removed (now stale) and a new
`DUPLICATE_PHRASE_ADJACENT_PAIR_BASELINE = {(65, 66), (66, 67)}` added to
`test_part1_no_new_duplicated_phrases` (which previously had no baseline
mechanism at all — added one, same pattern as the other two).
`FOREIGN_CHARACTER_BASELINE`'s existing klal 66 entry also needed its
`word_index` updated (97→112) since the 15-word insertion shifted every
later position — same character, same text, confirmed via re-check.

**Second finding, opportunistic**: while scan-verifying the boundary,
directly adjacent text (klal 66, now word 29) showed `ולמדתי כן מדדיא
דמשנינן` — `מדדיא` is not an attested word. 4800/7200 DPI crops of the
same token show a clear gap under the top horizontal stroke on both
disputed letters, the defining shape of `ה` (he), not `ד`'s (dalet) flush
corner. `מהדיא` (mem-he-dalet-yod-alef) is a standard, attested Talmudic
Aramaic idiom ("explicitly/plainly stated," e.g. `איתמר מהדיא`) and fits
the sentence exactly: "and I learned this explicitly, that we
distinguish... in Sotah." Visual and linguistic evidence agree (Lesson
9). Recorded as `manual_correction` (`20b975b2c154`) and applied via
`apply_reviewer_decisions.py`.

**Verification**: `git diff part1.json` shows exactly the two changes
described (klal 65 truncated, klal 66 restructured + the one-word fix).
`./rebuild_all.sh` clean, 131/131 pytest. No other klal touched.

### CORRECTION 2026-08-17 — `heb_rashi`'s full-Part-1 Berlin run reviewed: near-total garbage, NOT the "works fine on square print too" bonus finding from 2026-08-16. That finding does not generalize to the actual Berlin scan this pipeline uses.

Per user request ("review heb_rashi on part 1"). Read the completed full-run
output (`/tmp/heb_rashi_full_run/berlin_part1_heb_rashi.txt`,
`livorno_part1_heb_rashi.txt`) and immediately noticed the Berlin output
looked like near-total letter salad, not the "roughly comparable to
standard `heb`" quality the 2026-08-16 "bonus finding" reported. Verified
directly rather than trusting the visual impression (Lesson 2):

- **Confirmed the rendered source image itself is fine**, ruling out a
  rendering/pipeline bug before blaming the OCR model: `berlin/page_014.png`
  (300 DPI, from `run_ocr.sh`) is pristine, right-side-up, correctly-ordered,
  clearly legible square print - matches klal 1's known opening text exactly
  by eye.
- **Re-ran Tesseract directly on that exact image, both models, output to
  files (not piped)**: `heb_rashi` produced `י - ם ת ש כ י` / `ל כלני וגלף` -
  meaningless. Standard `heb` on the SAME image produced `אי תניא תניא +
  מדברי רש"י ז'ל בפ"ב דנדרים ייט ב' משמע רלאו לדחויי ליח קא מכוין` - highly
  legible, closely matching part1.json's actual klal 1 text.
- **Confirmed systematic, not a one-page fluke**: repeated the same
  `heb_rashi` vs `heb` comparison on pages 20, 40, 60 (spread across Part
  1). `heb_rashi` produced unreadable output on every one; `heb` produced
  legible, largely-correct Hebrew on every one.
- **Livorno (genuine Rashi script) checked too, for completeness**: sampled
  pages 50/150/250. Neither model produces usable output on the body text
  at full-corpus scale - both garbage - though `heb_rashi` gets the running
  header line right more often. This re-confirms (does not overturn) the
  earlier single-page finding that Rashi script remains genuinely hard for
  both tools; no new claim here.

**What this corrects**: the 2026-08-16 "bonus finding" entry ("`heb_rashi`
ALSO produced good output on the SQUARE test page... suggests `heb_rashi`
might be usable as a single model across both this project's script types")
was tested against `Hebrewbooks_org_14122.pdf` - a DIFFERENT square scan,
not `berlin_square_corrected.pdf`, the scan this pipeline actually OCRs.
That entry already explicitly hedged this ("worth confirming on more
samples before relying on it") - this is that confirmation, and it comes
back negative. **`heb_rashi` is not a viable OCR choice for the Berlin
scan specifically**, despite performing reasonably on at least two OTHER
square-typeface scans of this same work (Przemyśl, `Hebrewbooks_org_14122`)
tested earlier this session and last. The same standing lesson already in
CLAUDE.md (Parts 2-3 not inheriting Part 1's pipeline quality) applies at
a smaller scale here too: OCR-tool performance on one scan of a work does
not transfer to a different physical scan/copy of the "same" typeface,
even nominally identical square Hebrew print - each scan needs its own
direct verification, not an assumption from a different copy.

**Conclusion for the original purpose (enable a full-corpus diff against
`part1.json`)**: not built, and correctly so - diffing `part1.json` against
near-garbage OCR would produce a wall of noise, not real signal. No further
action planned on `heb_rashi` for Berlin. DocAI remains this pipeline's
correction-candidate source for Berlin (already confirmed clean on klal 183
in the entry above) and is unaffected by this finding.

### CORRECTION 2026-08-17 — the "near-perfect" heb_rashi claim on the square Przemyśl scan overclaimed; word-level errors verified; Google Cloud Vision tested and found WORSE

Per direct user correction, applying CLAUDE.md Lesson 19 to this session's own
just-written output: the entry below ("RESEARCH... try the second square scan
with various ocr tools") called `heb_rashi`'s output on `scans/ספר_יד_מלאכי.pdf`
page 100 (Przemyśl 1877) "near-perfect" without doing a real word-by-word
check against the actual scan - exactly the failure Lesson 19 warns about.

**Verified directly at 1200-2400 DPI, not assumed**: the FIRST word `הלכה`
(halacha) - which the write-up's own comparison line incorrectly implied was
wrong - is in fact CORRECT; the error was in that comparison's own assumed-
ground-truth text, not in `heb_rashi`'s reading. The SECOND word IS a
genuine `heb_rashi` error: the scan reads `כדברי` (standard construction,
"according to the words of") but `heb_rashi` produced `כדבני` (ר misread as
נ). Corrected assessment: `heb_rashi` on this page is good but NOT
error-free - real letter-level mistakes remain, just fewer/subtler than
standard `heb`'s. The right general lesson: don't grade OCR output against
your own unverified assumption of the source text - check the actual scan,
same discipline this project demands everywhere else, now including casual
tool-comparison narration.

**Google Cloud Vision - installed and tested this session (`google-cloud-
vision` pip package; required the user to enable the Vision API in the GCP
console - the existing `doc-ai-worker` service account is scoped narrowly to
Document AI and has no IAM permission to self-enable new APIs, confirmed by
trying `gcloud services enable vision.googleapis.com` directly, which was
denied at the permission level, not just "not yet enabled").** Tested BOTH
`text_detection` (general/scene-text mode) and `document_text_detection`
(the dense-document-specific mode, the theoretically-correct choice for this
material) on the identical page/line already checked above - **both
endpoints returned byte-identical output**, and it is **visibly worse than
`heb_rashi`** on the same line: `סלכס כלכרי סכליע לפסל לכל למרי' כן...`
(ה misread as ס repeatedly, among other errors) vs. `heb_rashi`'s `ספנ הלכה
כדבני הוכריע אפשר דלא מרי׳ כן...` (first real word correct, one confirmed
letter error). Not yet checked word-by-word to the same rigor as `heb_rashi`
above (this finding is itself only a first-pass visual comparison, not a
verified count) - but the gap looks real enough to record as a genuine
result, not just noise, while flagging that it hasn't had the full
verification treatment either.

### SCOPED, NOT STARTED, 2026-08-16 — Rashi/Livorno second-witness project

Per direct user request ("scope 3") following the OCR-tool research above.
Not implemented - a plan only, for a future scope decision.

**Framing, load-bearing**: Livorno and Berlin are DIFFERENT PRINTINGS
(Berlin's own title page says "with several additions and corrections" -
see CLAUDE.md "Pipeline shape"). A Livorno/Berlin disagreement is NOT
automatically "the current pipeline's OCR is wrong" the way a DocAI/
Tesseract disagreement on the SAME scan is - it could be a genuine edition
difference. This makes the project a second EDITORIAL witness needing full
adjudication discipline, not a cheap OCR cross-check - more valuable
(Livorno is the original printing, arguably closer to authorial intent)
but a bigger lift than it first looks.

**Five phases**: (1) full-corpus `heb_rashi` Tesseract extraction of all 348
Livorno pages - the engine is confirmed working (see the empirical test
above), untested at full-corpus scale; (2) klal-boundary alignment, mapping
Livorno's own markers to `klal_id`s - THE big unknown, since nothing
establishes today whether Livorno's layout/pagination/klal count/ordering
even matches Berlin's; (3) comparison logic (Livorno-OCR vs. stored text) -
mostly reusable from `build_corrections_dataset.py`'s existing diff shape;
(4) adjudication - reuse `verify_corrections_vision.py`'s crop/adjudicate/
cache machinery, but the PROMPT needs real redesign to reason about
"different editions," not just "which engine misread the same ink"; (5)
decision integration - a third witness column in the dashboard needs actual
UI work, not just backend plumbing.

**Recommended next step, if this gets picked up**: timebox a small manual
investigation of phase 2 first (locate 5-10 klal markers by hand in the
Livorno scan) before scoping the rest in detail, since alignment risk could
change the whole project's size. Rough total effort if alignment isn't
unusually painful: comparable to or larger than the original correction
pipeline, given the new prompt/UI work phases 4-5 need.

### DONE 2026-08-16 — item 2 closed: klal 198's 2 candidates scan-verified and applied; klal 212's "missing halacha number" checked and closed, print-faithful

Per direct user request ("2. close the two small loose ends"). Both had been
sitting open since earlier in the session.

**klal 198 w1055 and w861** couldn't be vision-verified automatically because
`klal_page_regions.json`'s entry for klal 198 is broken - a near-zero-area
bbox on page 70 claiming 1087 tokens, nested INSIDE klal 197's own claimed
region rather than describing klal 198's real location. Root-caused, not just
worked around: klal 198's actual gematria marker (`קצח`) was found by direct
search on **page 71**, sitting in the middle of the region klal 197's own
`continuations` list currently claims in full - so klal 197's page-71 (and
likely page-72) continuation bounds are the real bug, over-claiming territory
that belongs to klal 198. Not fixed in `klal_page_regions.json` itself this
pass (that's a `build_klal_page_regions.py` continuation-detection fix,
bigger than unblocking these 2 words) - worked around by searching
`docai_word_boxes` directly for each target word and disambiguating by
matching context against `part1.json`'s own surrounding words, then cropping
at 2400 DPI. Both confirmed: w1055 `עוכר`->`עובר` (context `ואמנם אמרו שהוא
___ בכך וכך עשה` matches exactly), w861 `יצהק`->`יצחק` (context `רבינא ורב
נחמן בר ___ ס"ל` matches exactly, standard Amora name). Applied via
`manual_correction` + `apply_reviewer_decisions.py` (2 words, klal 198 only).

**klal 212 w51** - the round-2 semantic-spotcheck's "halacha NUMBER is
missing" hypothesis (`...הלכה וגם...` with no number, guessed as a dropped
token) - checked directly against a 2400 DPI crop of the exact gap between
the two words: **ordinary word-spacing, nothing squeezed in, no sign of a
dropped token.** The print itself reads `הלכה וגם` with no number - print-
faithful as transcribed. Closed via `klal_flag` (`needs_revisit: false`), no
`part1.json` change. Whether the AUTHOR omitted the number is a content
question outside this pipeline's fidelity scope.

Full rebuild after applying klal 198's 2 words: 131/131 pytest, only
`part1.json`/`klalim_demo_dataset.json`/`review_decisions.jsonl` changed (no
new vision candidates generated near these manual-path edits, so
`corrections_*`/`klal_page_regions.json` correctly unchanged this time).

**Still open**: `klal_page_regions.json`'s continuation-bounds bug for klal
197/198 (and the separate, already-logged klal 167 undersized-region gap) -
both real, both would need a `build_klal_page_regions.py` fix, neither
attempted this pass.

### DONE 2026-08-16 — 28 independently-reverified corrections applied to part1.json; 5 closed as print-faithful; rebuild clean

Follow-up to the 1200 DPI re-verification entry below. Recorded the 28 CONFIRMED
items as `manual_correction` decisions (`reviewer: "local-1200dpi-reverify"`,
each note citing the specific 1200 DPI crop finding, not just the original
lower-resolution vision verdict) and the 5 DISCONFIRMED items as closing
`klal_flag` notes (`needs_revisit: false`, same "checked, print-faithful"
precedent as klal 88's `רתם`/`התם`) - `review_decisions.jsonl` grew 621 -> 654
(append-only, verified).

Ran `pipeline/apply_reviewer_decisions.py` (dry-run first, then for real):
applied exactly the 28 manual corrections (0 replace/insert-delete, matching
expectation), correctly left 152 already-applied historical decisions alone
and 10 unrelated drifted ones alone (neither touched by this session).
**28 word-level corrections across 18 distinct klalim** (klal 4, 7, 11, 12,
13, 25, 48, 49, 62, 67, 70, 96, 97, 98, 126, 128, 163, 186 - several klalim
had multiple corrections, e.g. klal 25 had 4, klal 128 had 3).

Ran `./rebuild_all.sh` (full, WITH vision) after: **0 live Gemini calls, every
candidate a cache hit**, all 5 derived files regenerated
(`klalim_demo_dataset.json`, `corrections_candidates_part1.json`,
`corrections_verified_part1.json`, `corrections_part1.json`,
`klal_page_regions.json`), 131/131 pytest. Dashboard (already running, no
restart needed - reads fresh from disk) spot-confirmed live via
`/api/klal/4` showing the corrected `איהו` in place. Git status confirms only
the expected 9 files changed (7 derived/cache + `part1.json` + `review_decisions.jsonl`),
nothing else touched.

**Still open from this batch**: the 24 UNCERTAIN items and 8 UNVERIFIABLE
(band-estimate) items remain exactly as the vision pass left them - flagged,
not applied, not closed. The 24 uncertain ones still have real linguistic
support for their candidates (per the detector's own zero-independent-
attestation method) even without independent visual confirmation - worth
a second pass with a different technique (e.g. a differently-prompted/
higher-resolution automated vision call, or direct human reading in the
dashboard) rather than left indefinitely. The 8 band-estimate ones need
`klal_page_regions.json`'s continuation-detection gap (klal 167/198) fixed
before they're even locatable, let alone verifiable.

### DONE 2026-08-16 — independent 1200 DPI re-verification of all 65 vision-"B" candidates: 28 confirmed, 5 confirmed WRONG, 24 genuinely uncertain, 8 unverifiable

Per direct user request to start on item 1 (work the 65 candidate-supported vision
results). Before applying anything, cross-checked one against this session's own
earlier klal 140 finding and found a direct contradiction (the low-res vision pass
said B at 1.0 confidence; a careful 2400 DPI read earlier the same session said the
opposite) - so did NOT trust the batch blindly. Per user direction, re-cropped all
65 at 1200 DPI with generous margin (proportional padding, minimum floor) and a red
box drawn around the exact target token, and read each one directly rather than
trusting the automated verdict.

**Result: the 300 DPI automated vision pass has a real, non-trivial error rate on
subtle letter-shape distinctions - not a one-off.** Of the 57 exact-token-located
items:
- **28 independently CONFIRMED** - crop unambiguously matches the candidate.
- **5 independently DISCONFIRMED** (crop actually supports the CURRENT text, not
  the candidate) - klal 140 w97 (`והשוא`/`והשואל`, found first, see below), klal 71
  w55 (`דעים`/`רעים` - crop shows ד not ר), klal 75 w1058 (`נהמן`/`נחמן` - crop
  shows ה not ח; "רב נחמן" is an extremely common Amora name, so this is a
  genuinely surprising result worth a second look, not dismissed as unlikely just
  because it's unexpected), klal 217 w313 (`מיר`/`מיד` - crop shows ר not ד), klal
  161 w105 (`בס'`/`בפ'` - crop shows ס not פ).
- **24 genuinely UNCERTAIN even at 1200 DPI** - mostly ד/ר, כ/ב, ה/ח confusions,
  or a bare geresh vs. yod (a single small mark, inherently hard to discriminate
  at any resolution). Many of these have strong INDEPENDENT linguistic support
  for the candidate (they came from `detect_real_word_substitution.py`
  specifically because the candidate is a well-attested real word and the
  original isn't attested at all - e.g. `ובלבד`/`יבום`/`דהוה` are extremely
  common Talmudic forms vs. their unattested originals) - the visual uncertainty
  doesn't cancel that prior, but isn't independent confirmation of it either.
- **8 UNVERIFIABLE with current crop tooling** - the band-estimate-located items
  (including all 4 from klal 167's known-broken region data). One highlight crop
  came back as an entire page-paragraph, confirming these can't be pinned to a
  single word without first fixing the underlying locator/region-data gap.

Full per-item categorization and reasoning kept in this session's scratch space
(`/tmp/reverify_crops/categorization.json` - not committed, regenerable from
`flagged_candidates_vision_report.json` plus this methodology if needed again).

**Not yet acted on** - the 28 confirmed still need to go through the actual
decision/apply pipeline (next step), and the 5 disconfirmed need to be recorded
too (as "checked, print-faithful as-is," matching the klal 88/140 precedent) so
they don't get silently re-flagged as open in the future.

### RESEARCH 2026-08-16, continued — `scans/` now holds the Livorno original (Rashi, confirmed); expanded OCR-tool research; a Rashi-trained Tesseract model tested EMPIRICALLY and works

Follow-up to the OCR-witness research above, per user request to expand
beyond the original five tools, note the newly-consolidated `scans/`
directory, and actually test whether any tool produces usable candidate
text - not just survey literature.

**`scans/` directory identified (5 files, none tracked/gitignored status
not yet decided - see Open Items).** Rendered and read a real page from
each rather than trusting filenames:
- **`Hebrewbooks_org_32530.pdf` (348 pages) = the LIVORNO ORIGINAL,
  CONFIRMED, in Rashi script.** Title page directly reads `נדפס בליוורנו`
  (printed in Livorno), press of ר' משה עטיאס - this is exactly
  `CASE-YAD-MALACHI.md`'s own table row citing "HebrewBooks #32530," now an
  actual file instead of just a citation. **CORRECTS a stale claim** in
  that same doc (fixed this session) that said "this repo doesn't hold a
  Livorno scan." **User's hypothesis ("I believe all the old scans are
  rashi script") is PARTLY right, corrected here**: of the 4 historical-
  edition PDFs now in `scans/`, only this ONE (the Livorno original) is
  Rashi - the other three are square type, matching what `CASE-YAD-
  MALACHI.md`'s table already said (visually confirmed, not assumed):
  - `Hebrewbooks_org_14122.pdf` (491p) = Przemyśl 1877, square (exact
    HebrewBooks #14122 match to the table).
  - `ספר_יד_מלאכי.pdf` (489p) = Przemyśl 1877, 2nd scan, square.
  - `ספר_יד_מלאכי (1).pdf` (373p) = Przemyśl 1888, square.
- **`יד מלאכי.PDF` (2 pages) and the two `.jpg` files are NOT historical
  scans** - a modern typeset critical edition (footer credits "הוצאת
  מישור" via "אוצר החכמה", page 553) and what look like product-listing
  photos of a physical 3-volume modern set (`sofrimdeals.com` watermark
  visible). Useful only as an independent MODERN reference for semantic
  cross-checking, not as an OCR witness for what the historical prints say.

**Expanded tool research (beyond Tesseract/Jochre 3/Kraken/Dicta/ABBYY):**
- **EasyOCR and PaddleOCR: RULED OUT.** Confirmed no Hebrew model in either
  framework's standard offering - not a viable option at all, not just a
  weak one.
- **Transkribus / DiJeSt 3.0 - a serious new lead, NOT YET TESTED (needs an
  account).** A public, actively-maintained model from Haifa University's
  "Digitizing Jewish Studies" project, explicitly covering "printed (or
  typed) text in Hebrew Script" (Hebrew/Yiddish/Judeo-Arabic/Ladino,
  15th-21st c.), reporting 1.79% CER - but that figure is on the model's
  OWN validation set (Lesson 2: a reported score is a triage signal, not a
  certificate), and its training-data breakdown (Hasidic Stories, a Yiddish
  theatre lexicon, Yiddish newspapers) reads Yiddish-heavy - genuine rabbinic
  Hebrew coverage, let alone Rashi-script specifically, isn't confirmed from
  available documentation. Free tier exists (50 credits/month), API access
  requires an Organisation-tier plan. Not testable without an account this
  session - flagged for the user to try directly if interested, not signed
  up for autonomously.
- **Surya OCR**: 90+ languages, local/no-cloud, but no confirmed Hebrew
  script support found in available docs - unresolved, not ruled in or out.
- **TrOCR + Kraken**: used together on Dead Sea Scrolls Hebrew fragments per
  one source - but that's ancient HANDWRITTEN Hebrew, a very different
  problem from 18th/19th-century PRINTED Rabbinic Hebrew; not a direct
  precedent for this project's material.

**EMPIRICAL TEST, not just research - the concrete answer to "does any
scan+tool combo actually work":**
Downloaded the community `heb_rashi` Tesseract model (gitlab.com/pninim.org/
tessdata_heb_rashi, LSTM-trained specifically for Hebrew Rashi script) and
ran real OCR against real 300 DPI crops of a mid-book content page from both
`Hebrewbooks_org_32530.pdf` (Rashi) and `Hebrewbooks_org_14122.pdf` (square),
comparing against standard Tesseract `heb`:
- **Standard `heb` on the SQUARE page**: moderately usable - individual
  words mostly legible Hebrew with plausible-looking (if error-prone)
  content, matching this project's own DocAI/Tesseract experience on the
  Berlin square print.
- **Standard `heb` on the RASHI page**: effectively USELESS - output is
  largely incoherent, riddled with stray Arabic digits substituted for
  Hebrew letters, not a usable starting point for correction. Directly
  confirms the "Rashi is harder" hypothesis empirically, not just by
  reputation.
- **`heb_rashi` (the Rashi-trained model) on the SAME Rashi page**:
  **dramatically better** - genuinely coherent Rabbinic Hebrew emerges,
  real legal terminology recognizable (e.g. correctly producing phrases
  close to `וכ"כ מרן בכ"מ פ"ו מהל' ברכות`), still with real errors (gershayim
  rendering, some letter confusions) needing correction, but a real,
  usable CANDIDATE text - not a research claim, an actual output compared
  directly against the actual page. **This is a genuine, actionable
  finding: a Rashi-tuned Tesseract model is an effective witness for the
  Livorno scan specifically**, unlike generic Tesseract or (per the
  earlier research) Jochre 3.
- **Bonus finding**: `heb_rashi` ALSO produced good output on the SQUARE
  test page - comparable quality to the standard `heb` model on the same
  page. Not confirmed why (broader training diversity than its name
  suggests, or Rashi-script training generalizing reasonably to square
  letterforms) - but suggests `heb_rashi` might be usable as a single
  model across both this project's script types rather than needing to
  switch, worth confirming on more samples before relying on it.
  **CORRECTED 2026-08-17** (see that date's CORRECTION entry near the top
  of this file's handoff): confirmed on more samples exactly as flagged
  here as needed - and it came back negative. Tested directly against
  `berlin_square_corrected.pdf` (this pipeline's actual live scan, not
  `Hebrewbooks_org_14122.pdf` tested here) across 4 widely-spread pages:
  `heb_rashi` produces near-total garbage on every one, while standard
  `heb` on the SAME images stays legible and largely correct. Does not
  generalize across different scans of nominally the same typeface -
  each scan needs its own direct check.

**Other editions/scans online**: Hebrew Wikipedia's edition list matches
what's already cataloged (Livorno original; Przemyśl 1877/1888; several
MODERN critical editions - Mishor 2001, Machon Yerushalayim 2016 - not
additional historical witnesses) - no additional historical printing found
beyond what `CASE-YAD-MALACHI.md`'s table and `scans/` already cover.
**One discrepancy flagged, not resolved**: Wikipedia's summary implies a
Berlin printing year of 5677 (~1917), sharply different from `CASE-YAD-
MALACHI.md`'s own "~1857/8" estimate (itself already flagged there as
unconfirmed) - the fetch/summarization pass that surfaced this may have
mis-converted a Hebrew-year gematria (a known failure mode, not verified
against the primary source), so this is reported as a discrepancy worth a
closer direct look, not a correction to make yet.

**Nothing applied to the pipeline** - this is still research plus one
concrete empirical test, not a scoped implementation. If a Rashi-script
extraction pass is ever wanted, `heb_rashi` Tesseract is now a confirmed,
free, working starting point - worth being a `pipeline/`-tier tool if that
work is scoped, not a research-only conclusion anymore.

### RESEARCH 2026-08-16 — multi-engine OCR witness options revisited (Tesseract/Jochre 3/Kraken/Dicta/ABBYY); one correction to CASE-YAD-MALACHI.md's original proposal, one promising unexplored lead

Per direct user request ("do a deep research into these options to see if
any will serve as a useful witness against our DocAI scan") - these five
engines were named in `CASE-YAD-MALACHI.md`'s "Process — ensemble OCR with
AI adjudication" section (the aspirational "full ensemble" upgrade path,
never built - the actual pipeline took the "lean single-edition" path:
DocAI + iterative LLM cleanup on Berlin square only). External web research
(not just recalled training knowledge), findings below stated with their
source confidence:

- **Tesseract**: already integrated, narrowly - `tools/verify_witness_
  vision.py` already compares DocAI vs. Tesseract crops for the klal 30/75/
  88 witness-reconstruction queue (`pytesseract` in `requirements-dev.txt`).
  Free, local, zero marginal cost. Real caveat found in general Hebrew-OCR
  literature (not confirmed against THIS project's own scan directly):
  Tesseract's accuracy drops substantially on 19th-century-style rabbinic
  print vs. clean modern Hebrew, and its confusable-letter classes
  (ו/ז, ב/כ, כ/ס and similar) overlap heavily with the confusion pairs
  `detect_real_word_substitution.py` already tracks for DocAI's own errors -
  meaning Tesseract-DocAI agreement is weaker evidence of correctness than
  the ensemble theory assumes if both engines share the same blind spots,
  since CASE-YAD-MALACHI.md's own rationale for ensembling ("OCR engines
  make uncorrelated errors") only holds where the errors ARE actually
  uncorrelated.
- **Jochre 3 - CORRECTION to CASE-YAD-MALACHI.md's proposal.** Jochre
  (Assaf Urieli, since 2009) is built and trained specifically for
  **Yiddish** OCR - the current Jochre 3 paper (arXiv:2501.08442) describes
  YOLOv8 layout models and a CNN glyph recognizer trained on a Yiddish
  corpus, including a Yiddish-specific typeface (Vaybertaytsh) variant. No
  evidence found of a Hebrew/Rabbinic-tuned Jochre model. Sharing the Hebrew
  alphabet doesn't make it a good fit for square/Rashi Rabbinic Hebrew - the
  original CASE doc's Jochre recommendation appears to be a mismatch, not
  verified against Jochre's actual training target. Not recommended.
- **Kraken/eScriptorium**: general-purpose, actively used in digital-
  humanities work on historical non-Latin scripts, with real Hebrew-script
  precedent (the BiblIA dataset, medieval Hebrew/Aramaic MANUSCRIPTS across
  6 script traditions) - but that precedent is handwritten, not printed
  square/Rashi type from an 18th/19th-century press, and no ready pretrained
  model for this project's actual typeface was found. Kraken is fundamentally
  a TRAINABLE engine - using it well here would mean preparing labeled
  training data (line images + transcriptions) and training a custom model,
  roughly the scale of effort `CASE-YAD-MALACHI.md` already estimated for
  the full ensemble harness (40-80 dev hrs). Highest technical ceiling of
  the five, but a real project, not a quick add.
- **Dicta - the most promising unexplored lead, and a second correction to
  CASE-YAD-MALACHI.md.** The CASE doc describes Dicta only as a POST-
  correction NLP layer (abbreviation expansion, the BEREL model) - but
  Dicta has a real, purpose-built OCR product, **Dicta Maivin**
  (illuminate.dicta.org.il), specifically adapted to rabbinic typefaces.
  Professor Moshe Koppel (Dicta's founder) is quoted demonstrating it
  directly on a 19th-century Rashi-script print (Avkat Rokhel, 1865) -
  exactly this project's kind of source material, arguably a better match
  than square type since Rashi is the harder script. Free (Dicta's tools
  are stated as free/open for public use). **Not yet actionable**: no
  documented public API or bulk/programmatic access was found - it appears
  to be a web upload tool, which doesn't fit this pipeline's automated
  crop-and-compare workflow at 340-460-page scale without either manual
  per-page work or direct outreach to Dicta asking about API/bulk access.
  **Worth a direct inquiry** given how precisely it targets this exact
  problem, free of charge, from an established Hebrew-NLP research org.
- **ABBYY FineReader**: broad, mature, general multi-language OCR with
  Hebrew support, but no rabbinic-specific tuning, and a real cost barrier
  for the tier that actually offers API/scriptable access (FineReader
  Server, roughly $10k-30k/yr for small-to-mid concurrent-processing
  deployments per current vendor-pricing pages) - the cheap consumer tier
  ($16/mo) is desktop-only, no API. Marketing claims of strong Hebrew
  accuracy found during this search were vague/unsourced (SEO-style content
  sites, not a rigorous benchmark) and are flagged as such, not repeated as
  fact. Cost disproportionate to a project this size given free alternatives
  exist; not recommended as a near-term option.

**Recommendation, in priority order**: (1) short-term, near-zero-cost -
consider whether Tesseract's existing DocAI-comparison role should extend
beyond the witness-reconstruction queue to a broader secondary signal, with
the caveat above about correlated error modes tempering how much weight to
give agreement between the two; (2) medium-term, potentially high-value -
directly ask Dicta about API/bulk access to Maivin, since it's the only
option here actually built and demonstrated for rabbinic-print OCR
specifically; (3) longer-term, highest ceiling but a real project -
Kraken/eScriptorium with a custom-trained model, if the corpus ever
warrants that scale of investment; (4) not recommended - Jochre 3 (wrong
language target) and ABBYY (cost, no rabbinic-specific advantage).
**Nothing acted on** - this is research to inform a future decision, not a
scoped or started implementation.

### DONE 2026-08-16 — round-3 refactor/correctness audit found a 4th real bug in `verify_flagged_candidates_vision.py`'s locator, fixed while the live vision run was mid-flight

Per direct user request ("another high-powered review... eye toward
refactoring") while the credit-restored vision run below was executing in
the background. Launched as a worktree-isolated agent per the standing
round-1/round-2/hard-wired-value-audit pattern - full findings on its own
branch `worktree-agent-ac6c84c65115b67e6` (not yet merged): **one bug fixed
there** (`tools/verify_witness_vision.py`'s `witness_cache` table was
missing `prompt_hash` from its key - the same Lesson-12 gap already fixed
twice elsewhere in this project, now a third confirmed sibling; mutation-
tested, 419 existing cached rows migrated losslessly, 117/117 pytest in that
worktree), **one refactor opportunity reported not executed** (`verify_
corrections_vision.py`/`verify_witness_vision.py` duplicate near-identical
crop/adjudicate/cache machinery - the missing-`prompt_hash` bug is direct
proof the duplication already causes drift; deliberately not touched this
round since it would edit the file the live vision job was actively using),
and **one bug found in code the audit's worktree couldn't reach** (`tools/
verify_flagged_candidates_vision.py` is uncommitted in the main checkout, not
in git history yet, so the isolated worktree could only read and report it).

**That reported bug was real and is now fixed directly in the main checkout**:
`locate_word()`'s disambiguation logic tracked only the LAST page's token
list (`match_bbox_region`/`match_page` overwritten on every page with a
match), so whenever the same word text matched on BOTH a klal's primary page
and its continuation page, every match from the earlier page was
unconditionally penalized (`1e9`, "not in this list") regardless of which
occurrence was actually closer to `word_index` - the function silently
always returned whichever page was iterated last. Confirmed on real data:
**4 of the 160 located candidates were affected** - klal 30 w1263/w250
`גכי` and klal 41 w256/w473 `כתכו`, each matching on two pages. Fixed by
ranking every match on one GLOBAL scale (each page's local rank offset by
the running token count of pages before it - the same technique `locate_
word_band_fallback()` already used for its own estimate). Verified against
real data post-fix: klal 30 w250 now correctly resolves to page 24 (primary,
was wrongly page 25) and klal 41 w256 to page 28 (primary, was wrongly page
29) - 2 of the 4 demonstrably changed answer, not just a defensive no-op.
New hermetic test, mutation-verified (reintroduced the exact bug, confirmed
red, restored, confirmed green). 127/127 pytest.

**Consequence for the live vision run below**: that run's `located` list was
computed ONCE at process start, before this fix existed, so its in-memory
copy still has the OLD (wrong-page) bboxes baked in for these 4 candidates -
editing the source file mid-run does not retroactively fix an already-
running process. Deliberately NOT killed/restarted (would waste the API
budget/time already spent on the other 156, all unaffected and correct).
**Action needed after the current run finishes**: re-run `python3 tools/
verify_flagged_candidates_vision.py` once more. Because the adjudication
cache is keyed on `crop_hash` (among other things) and these 4 candidates
now produce a genuinely different crop, the other 156 will be instant cache
hits and only these 4 will trigger fresh (now-correct) API calls - no need
to hand-pick which ones to re-run.

### DONE 2026-08-16 — item 2 from NEXT STEPS: all 160 locatable candidates vision-adjudicated (93 original-confirmed, 65 candidate-supported, 2 uncertain), 72 klal_flag decisions recorded

Per direct user request ("do 1 2 and 3"), then explicit direction ("build full
pipeline, run all 168") after a scope check-in. This is the biggest of the
three items - unlike items 1/3, neither the 85 `ai-semantic-spotcheck-round2`
nor the 83 `ai-real-word-substitution` candidates (168 total across 81
`klal_flag` rows) has a pre-computed bounding box or structured JSON entry -
both live only in free-text note prose, and neither went through
`build_corrections_dataset.py`'s DocAI-vs-stored-text pipeline (by design:
both detectors exist BECAUSE docai and clean_text already agree on the same
wrong reading at these positions, so the normal diff pipeline never surfaces
them as a disagreement in the first place).

**New standalone script, three parts:**
1. **Note parser** - regex-extracts `(klal_id, word_index, original, candidate)`
   tuples from both note formats (semicolon-separated for real-word-sub,
   pipe-separated with an `|| OVERLAP:` suffix to strip for spotcheck2).
   Tolerates an embedded gershayim inside a quoted word by requiring the
   CLOSING delimiter to match the OPENING one (backreference) and treating an
   internal quote-followed-by-Hebrew-letter as part of the word, not a
   closer - an earlier draft used a bare `["']` for both ends and silently
   truncated words like `הנז'` wherever wrapped in double quotes, since this
   corpus's own abbreviation mark IS the ASCII `"`. Also strips a literal
   backslash-before-quote artifact found in ~19 notes (`ר\"ס` in the stored
   text, not `ר"ס` - confirmed by reading the raw JSONL, an artifact of how
   the note prose was written, not real corpus content). 9 further candidates
   the regex genuinely can't parse (multi-word originals, an "X followed
   directly by Y" missing-token shape) are hand-transcribed as
   `MANUAL_OVERRIDES`, each checked against its source note. klal 101's title
   finding and klal 212's "halacha NUMBER is missing" finding are deliberately
   EXCLUDED - neither is an option-A-vs-option-B substitution this script's
   comparison shape fits; klal 101 already has its own flag, klal 212 needs
   its own one-off look. klal 30's genuinely AMBIGUOUS entry contributes BOTH
   hypotheses, not one.
2. **Word locator** - given `(klal_id, word_index)`, searches `klal_page_
   regions.json` + `docai_word_boxes/` for a token whose text exactly matches
   the word currently in `part1.json` (reliable per the point above: docai
   and clean_text already agree here). Two real bugs found and fixed during
   construction, not just described:
   - **Only searched the klal's PRIMARY page, not its `continuations`.** 54 of
     Part 1's 222 klalim span a page break, recorded in `klal_page_regions.
     json`'s own `continuations` list - a field the dashboard's per-klal crop
     already reads but this script's first draft didn't. Fixed; confirmed on
     real data (klal 12 w237, previously unlocatable, now finds it on the
     continuation page).
   - **DocAI tokenizes a trailing geresh as its own token**, so a word like
     `סי'` never has one token matching its full text. Falls back to matching
     the word with its trailing mark stripped.
   Went from 71/162 located (exact match, page bug present) to 144/162 after
   both fixes. The remaining 18 fall back to a coarser **band-estimate**: a
   several-line-tall crop centered on a purely proportional (word_index /
   total_words) position, wide enough to tolerate the estimate being off by a
   few words (CLAUDE.md Lesson 14's "generous crop, visible margin," applied
   to an estimated rather than exact position). **Found a THIRD real bug via
   this fallback, not by inspection**: klal 167's `klal_page_regions.json`
   entry claims 990 tokens on one page for a 1369-word klal with NO
   `continuations` listed - a genuine gap in that file, not this script's
   fault. A naive proportional estimate for a late word_index in klal 167
   landed in the page-FOOTER "Digitized by Google" strip (confirmed by
   generating and reading the actual crop, not assumed). Added a sanity check
   - a band containing zero Hebrew-letter tokens is refused, not returned -
   which correctly excludes klal 198's 2 candidates (same underlying region-
   data gap, a near-zero-area bbox for 1087 claimed tokens) while still
   locating klal 167's other 6 (their estimated positions happen to fall
   inside the klal's genuine, if undersized, region). **klal_page_regions.
   json's continuation-detection has a real, unfixed gap for at least these
   two klalim - not chased down further here, logged for a future session.**
   **Final: 160/162 located (144 exact-token, 16 band-estimate), 2 need a
   manual crop (klal 198).**
3. **Vision adjudication** - reuses `pipeline/verify_corrections_vision.py`'s
   `crop_pdf_bounding_box`/`adjudicate`/`init_cache`/cache functions DIRECTLY
   (they're already generic over page/bbox and option-A/option-B/context, not
   tied to the structured candidate schema) rather than reimplementing them -
   so results land in the same `adjudication_cache.db` cache, keyed the same
   correct way (crop_hash + word_a + word_b + context_hash + prompt_hash, per
   CLAUDE.md Lesson 12). Writes a JSON report file only - no `part1.json` or
   `review_decisions.jsonl` write, per the standing "a vision opinion informs
   a reviewer, it doesn't become a correction by itself" rule.

11 new hermetic tests in `tests/test_pipeline_logic.py` (note parsing for
both formats, the backslash-artifact fix, the embedded-gershayim delimiter
fix, the continuation-page fix, the footer-rejection fix, and - added after
the round-3 audit below found a 4th bug - the cross-page disambiguation
fix), all load-bearing ones mutation-verified red/green. 127/127 pytest.

**RUN 2026-08-16, later the same day, after the user topped up Gemini API
credits.** First run: all 160 located candidates adjudicated cleanly, 0
errors, `flagged_candidates_vision_report.json` written. Corpus/decision
files confirmed byte-identical before and after (only `adjudication_cache.
db` grew). While this run was executing, the round-3 refactor audit
(separate entry above) found a 4th real bug in the locator - re-ran the
script a second time after fixing it: 156/160 were instant cache hits (their
crop didn't change), exactly 2 triggered fresh API calls (klal 30 w250, klal
41 w256 - the 2 of the 4 affected candidates whose page assignment actually
flipped), confirming the fix and the caching discipline both worked exactly
as designed. Corpus/decision files re-confirmed byte-identical after the
second run too.

**Results: 93 selected A (current text confirmed print-faithful, no
correction needed - the klal 88 `רתם`/`התם` pattern, now at bulk scale),
65 selected B (vision favors the proposed candidate correction over what's
currently stored), 2 UNCERTAIN, 2 not vision-verified (klal 198 - the
region-data gap noted above).** Spot-checked reasoning text on both A- and
B-selected results before trusting the aggregate counts (Lesson 2): the
model grounds its answers in specific letter-shape/paleographic observations
in both directions (e.g. "a standard vav terminating at the baseline, unlike
a final nun which would extend below it" for a B-selection; "a rounded
bottom-right corner without the sharp rightward projection of a bet" for an
A-selection) - not just picking a side. **Known limitation, not yet fixed**:
this script reuses `verify_corrections_vision.py`'s `PROMPT_TEMPLATE`
verbatim, which labels the two options "DocAI raw OCR reading" / "current
adjudicated text" - both labels are semantically WRONG for this batch
(option A here is actually the currently-stored word, option B the proposed
candidate, neither is a DocAI reading). The spot-check above found no sign
this misled the model's actual visual analysis, but the prompt should be
adapted to accurate labels before this class of script is reused again -
flagged, not fixed, since fixing it now would invalidate today's cache and
require re-running all 160 against a different prompt_hash.

**72 new `klal_flag` decisions** (`reviewer: "ai-vision-verify-flagged-
candidates"`, `needs_revisit: true`, one per klal, each note listing every
candidate's verdict + confidence + a trimmed reasoning excerpt + the above
prompt-labeling caveat). Verified: `review_decisions.jsonl` grew 549 -> 621
(append-only, spot-confirmed live via `/api/klal/7/flag`), `part1/2/3.json`
sha256 unchanged, 127/127 pytest. **NOT applied to part1.json** - per the
standing "a vision opinion informs a reviewer, it doesn't become a
correction by itself" rule, the 65 B-selected candidates are now the
highest-value next targets for a human working the dashboard, not
auto-corrected. klal 198's 2 candidates and the klal 167/198
`klal_page_regions.json` gap remain open, needing a manual look.

### DONE 2026-08-16 — item 1 from NEXT STEPS: klal 206 w2 and klal 140 w97 scan-verified — BOTH print-faithful, NOT the ligature bug

Per direct user request. The round-2 semantic-spotcheck entry below flagged
these as "TWO POSSIBLE NEW INSTANCES" of the alef-lamed ligature dropped-
lamed bug and left "0 known remaining candidates" an open question pending
scan verification. Direct high-DPI crops (1200-2400 DPI, `berlin_square_
corrected.pdf`, PyMuPDF) resolve both, cleanly, in the OPPOSITE direction
from the hypothesis:

- **klal 206 w2, page 73**: the headline `הרי או באזהרה` - the disputed
  word is unambiguously TWO letters (א-ו), no lamed ascender anywhere, at
  1200 DPI and again at a 2400 DPI tight zoom. Directly compared against
  the correctly-spelled `אלו` three lines below on the SAME page/scan
  (same phrase, `הרי אלו באזהרה`, in the body) which shows an unmistakable
  tall lamed stroke - confirming the crop-reading method itself is
  discriminating real letter shapes, not a rendering artifact. The print
  itself reads `או`, differing from its own body's six correct instances
  of `אלו` - an authorial/typesetting inconsistency in the original, not
  an OCR/ligature misread.
- **klal 140 w97, page 50**: `כשחשב המתיר והשוא שמותר להתיר לכתחלה` - the
  disputed word is unambiguously FIVE letters (ו-ה-ש-ו-א) at a 2400 DPI
  tight crop, with clear whitespace before the next word `שמותר` and no
  trailing lamed. `והשוא` is not a standalone word (`והשואל`, "and the one
  who asks," is what the sentence grammatically wants), so this reads as a
  genuine print defect/dropped-type error in the original book, not an
  extraction bug - but the ink itself has only 5 letters, matching what
  `part1.json` already stores exactly.

**Both cases: current `part1.json` text is ALREADY print-faithful. No
correction applied, no `part1.json` change.** Same precedent as klal 88's
`רתם`/`התם` (CLAUDE.md Lesson 1 in reverse: running the verification this
time changed the answer FROM "probable corruption" TO "confirmed
faithful," which is exactly why the check had to be run rather than left
as a described-but-unverified hypothesis). The dropped-lamed ligature
pattern's "0 known remaining candidates" claim (2026-08-15 entry) stands -
these two were a false lead, now closed with evidence rather than left
open. No `review_decisions.jsonl` action needed (nothing to accept/apply);
crops kept only in this session's scratch space, not committed (regenerable
from the coordinates and DPI documented above).

### DONE 2026-08-16 — item 3 from NEXT STEPS: `tools/check_next_marker_and_title.py` built (both checks), 7 new klal_flag decisions

Per direct user request ("do 1 2 and 3" against the open-items list). New
standalone, read-only, re-runnable script implementing the two cheap
mechanical checks this file already named as "not yet scripted":

1. **Next-klal gematria marker.** 29/222 Part-1 klalim end `clean_text` with
   a trailing " : <token>" - a catchword-like preview of the next klal's
   number. Reproduces exactly the 29-carrier / 7-mismatch figures this file
   already recorded by hand (klal 15/21/36/46/49/62/64) - all 7 were
   already flagged in a prior pass (49/62 via `ai-semantic-spotcheck-
   round2`, the other 5 via `ai-followup-unflagged-findings`), so this
   check found nothing NEW to flag, only confirmed the existing flags via
   an independently-reproduced, re-runnable method instead of one-off prose.
   Tried a lexicon-membership "low-confidence" signal to separate genuine
   stray-letter errors from ordinary sentence-final words (klal 21/64's
   documented ambiguity) and dropped it: every one of the 7 mismatches is
   ALSO an ordinary lexicon word, so the signal discriminated nothing -
   recorded as a dead end so a future session doesn't retry it.
2. **Title field vs. own opening line.** Extracts the phrase between a
   klal's gematria marker and its first sentence-break punctuation,
   compares to `title`, tolerating a title that's a clean prefix in EITHER
   direction (ordinary editorial shortening, e.g. klal 83's "בשל תורה" for
   a much longer sentence; or an internal-punctuation false split, e.g.
   klal 105/134). After that tolerance, **8 real mismatches**, of which
   klal 101 was already flagged (round-2 semantic spotcheck) and **7 are
   NEW findings, now flagged** (`reviewer: "ai-title-vs-opening-check"`):
   - **klal 102, 103, 104**: same "ב"ד"-dropped-from-title shape as the
     already-known klal 101 - the issue is a repeated pattern across this
     run of 4 consecutive klalim, not a one-off.
   - **klal 69**: title has `אהים`, body has `אלהים` - the title itself
     is missing a `ל`, a corruption the body doesn't share. Not previously
     reported anywhere in this file.
   - **klal 87**: title has `משנה`, body has `ממשנה` - title missing the
     `מ` prefix. Not previously reported.
   - **klal 36**: title has `הש"ס'`, body has `השית'` - a real word-form
     divergence between the two fields, distinct from (but on the same
     klal as) that klal's already-flagged next-marker mismatch above.
   - **klal 186**: title lacks a geresh present in the body after
     `המקיל` - lowest-significance of the 7, likely a stray-punctuation
     artifact rather than a content corruption, flagged anyway per "log
     every finding."

Both checks are read-only, standalone, deliberately **NOT wired into
`rebuild_all.sh`**: neither has a clean zero-false-positive record (next-
marker's ordinary-word ambiguity; title's editorial-shortening cases,
tolerated but not proven exhaustive against future edits) - same
precedent as `detect_ligature_corruption.py`/`review_lexicon_gaps.py`.
4 new hermetic tests in `tests/test_pipeline_logic.py`, each mutation-
verified (broke the marker regex's end-anchor, broke the prefix-tolerance
check - both confirmed red, restored green). 118/118 pytest.

Verified: `review_decisions.jsonl` grew 542 -> 549 (append-only, all 7
well-formed, spot-confirmed live via `/api/klal/36/flag` showing both this
klal's next-marker AND title-vs-opening flags in `history`), `part1/2/3.json`
sha256 unchanged. TEXTUAL EVIDENCE ONLY - nothing here was checked against
the scan.

### DONE 2026-08-16 — item 5 from NEXT STEPS closed: dangling branch confirmed superseded (already deleted, not by this session)

Per direct user request ("delete after validating not needed"). The branch
this file flagged as "found, NOT investigated further" (`pipeline-audit-
fixes-and-page-order-repair`, tip `5a86ef6`) turned out to already be gone -
the ref no longer exists in `refs/heads` (deleted by an earlier, unlogged
action; the commit survives only via reflog, not merged into `master`).
Did the line-by-line confirmation this file said was missing, on the
highest-risk files: `part1.json`'s one real content diff (klal 144's stray
extra `כ`) is already fixed identically in current `master`; `rebuild_all.sh`
and `verify_corrections_vision.py`'s diffs are pure path-reorg/superseded-
logic (the branch's raw inline prompt vs. master's `PROMPT_TEMPLATE`/
`PROMPT_HASH`); `review_frontend/app.js`'s 83-line diff is entirely the
pre-`escapeHtml` version of code master already carries escaped. No
branch-only content found anywhere master lacks. Nothing to delete - the
ref is already gone - and no further action needed.

### DONE 2026-08-16 — revalidation/refactor audit ROUND 3, merged from worktree `worktree-agent-ac6c84c65115b67e6`

Per direct user request for a third round of the standing revalidation/
refactor audit, this time explicitly scoped to include witness code (no
longer excluded) and with an explicit eye toward refactoring, not just
correctness. One commit (`13aee25` after rebase, `9103ea9` in the original
worktree), one bug found and fixed, mutation-verified; two further findings
reported at the time, not fixed in this worktree (see below for why -
**finding 2's locator bug was subsequently fixed directly in the main
checkout, see the entry above**). Independently re-verified before merging,
not just the agent's report trusted: re-read the actual `tools/verify_
witness_vision.py` diff, rebased onto current master (one real conflict in
this file's own "SESSION HANDOFF" section, both sides' content kept - see
the merge commit `0cc52d5`), ran the full test suite post-rebase (130/130
passing in the worktree, 1 skipped for the gitignored scan cache not being
present there), and tested the migration against a COPY of the real tracked
`witness_vision_cache.db` (422 rows, not the 419 the worktree's own
docstring estimated - migrated losslessly either way, backup table
preserved, schema correct) before merging. **After merging**, ran the
migration for real on the actual tracked `witness_vision_cache.db` too
(commit `4b9a261`) - the merge itself only brings in the CODE fix, the
tracked cache file doesn't migrate itself until something calls
`init_cache()`, and leaving that implicit would have meant the file sat on
the old, buggy schema until someone happened to next run `verify_witness_
vision.py`. Verified: 422/422 rows carried over, `decision_json` byte-
identical to pre-migration, 131/131 pytest in the main checkout
post-merge (has the gitignored scan cache, so the one worktree-skip runs
here). Worktree and its temp helper branches removed after merging.

**1. FIXED (bug, code) - `tools/verify_witness_vision.py`'s `witness_cache`
table was missing `prompt_hash` from its cache key.** PRIMARY KEY was
`(crop_hash, word_a, word_b, context_hash)` - the exact gap CLAUDE.md
Lesson 12 already documents being found and fixed TWICE in this project,
in `pipeline/verify_corrections_vision.py` (2026-08-14) and
`tools/propose_punctuation_part1.py` (2026-08-16). This is a THIRD sibling
script with the identical crop/adjudicate/cache shape, missed both times.
A future edit to the prompt wording (already documented as a real,
not-hypothetical event in the sibling's own history) would have silently
kept serving pre-edit cached answers under the new prompt forever.
  - Fixed the same way as both siblings: hoisted the inline prompt
    f-string into a named `PROMPT_TEMPLATE`/`PROMPT_HASH`, added
    `prompt_hash` to the cache schema/key, and added a lossless
    `_migrate_add_prompt_hash()` that back-fills existing rows under
    today's hash rather than dropping them (this cache holds 419 real,
    already-paid-for Gemini answers per the module's own docstring).
  - 4 new hermetic tests in `tests/test_pipeline_logic.py`
    (`test_witness_vision_cache_key_covers_*`,
    `test_witness_vision_cache_stores_a_null_side_*`,
    `test_witness_vision_cache_migration_is_lossless_and_idempotent`),
    directly mirroring the existing `verify_corrections_vision.py` tests.
    Mutation-verified: reintroduced the exact original bug (dropped
    `prompt_hash` from `get_cached()`'s WHERE clause), confirmed
    `test_witness_vision_cache_key_covers_the_prompt_template` went red,
    restored, confirmed green. 117/117 pytest (was 113), 1 skipped - up
    from 113 because this worktree had no local venv and one had to be
    built fresh (`requirements-dev.txt` plus `google-genai`, `pymupdf`,
    `Levenshtein`, `RapidFuzz`, `beautifulsoup4`, `lxml`, `pytesseract` -
    matching the main checkout's installed set - to make the
    `requires_witness_vision_deps`-gated tests actually run rather than
    skip). Not part of `rebuild_all.sh`'s chain, so no rebuild was needed
    or run for this fix. **No live Gemini calls were made** - this session
    deliberately made zero API calls throughout, per the explicit
    instruction not to compete with a live budget-sensitive job running in
    the main checkout concurrently.
  - **NOT fixed for the same reason it hasn't been generalized before**:
    `verify_corrections_vision.py`'s and `verify_witness_vision.py`'s
    `sanitize_json`/`unescape_json_fragment`/cache-init/migrate/get/put/
    crop/retry-loop machinery are now independently duplicated in
    (at least) these two files, nearly line-for-line - `verify_witness_
    vision.py`'s own module docstring even says the analogous
    `tools/verify_flagged_candidates_vision.py` (see finding 2 below)
    "reuses `pipeline/verify_corrections_vision.py`'s crop/adjudicate/
    cache machinery directly," but `verify_witness_vision.py` itself does
    NOT reuse it - it carries its own full copy. This bug is direct,
    demonstrated proof of Lesson 13 ("a hand-maintained parallel copy
    drifts"): one copy got the prompt-hash fix twice on other files, this
    third copy didn't. **Reported, not executed**: extracting a shared
    module (`vision_adjudication_common.py`-shaped: crop_pdf_bounding_box,
    sanitize_json, unescape_json_fragment, a cache-table factory keyed the
    same way, the retry/backoff loop) would remove this duplication at its
    root, but touches `pipeline/verify_corrections_vision.py` - the exact
    file the concurrently-running main-checkout Gemini job most plausibly
    depends on - and a structural refactor of a live paid-API script
    shouldn't be attempted blind, in the same session as an explicit
    instruction not to touch that job's path. Recommend as dedicated
    follow-up work with the live job stopped first, not folded into this
    round.

**2. REVIEWED, NOT FIXED (two files exist ONLY in the main checkout's
uncommitted working tree - not in git history at all, on any branch).**
`tools/check_next_marker_and_title.py` and `tools/verify_flagged_
candidates_vision.py` were named as first-priority audit targets (written
this session, never reviewed), but `git log --all` for both paths returns
nothing in this worktree, and worktrees only see committed history - per
CLAUDE.md's own "Directory layout" discipline this means neither file is
part of the tracked codebase yet, only sitting on disk in the main
checkout. Read both directly from the main-checkout path (read-only, no
edits possible from an uncommitted, untracked file in a different
worktree):
  - `check_next_marker_and_title.py` - reviewed in full, no bugs found.
    Both checks (next-klal gematria marker, title-vs-opening-line) match
    their own docstrings' claims; `TITLE_BOUNDARY_TOKENS` scanning takes
    the earliest-occurring boundary correctly regardless of list order;
    imports `klal_id_to_gematria`/`GEMATRIA_VALUES` from
    `validate_part1_corpus_integrity.py` rather than re-deriving them (no
    duplication).
  - `verify_flagged_candidates_vision.py` - **one likely real bug found in
    `locate_word()`'s cross-page disambiguation - AT THE TIME OF THIS
    WORKTREE'S REPORT, not fixable here (file wasn't in git history yet).
    Since fixed directly in the main checkout - see the entry above this
    one for the applied fix, confirmation it DOES fire on real data (4 of
    160 candidates), and re-verification.** When a candidate word's exact
    text matches DocAI tokens on BOTH a klal's main page AND one of its
    continuation pages (`region.get("continuations", [])`), the function's
    `match_bbox_region`/`match_page` variables were overwritten on every
    loop iteration that found a match, ending up set to whichever page was
    iterated LAST (main page first, then continuations, in list order) -
    not necessarily the page the correct match is actually on. In the
    ambiguous-disambiguation branch, `match_bbox_region.index(t)` was then
    computed only against that last page's token list, so any candidate
    token from an EARLIER page failed `t in match_bbox_region` and was
    penalized with a hardcoded `1e9` sentinel distance - meaning a
    same-text match on an earlier page could never legitimately win the
    proportional-position disambiguation once a later continuation page
    also had a same-text match, regardless of which one was actually
    correct. `locate_word()`'s own docstring said it "Disambiguates by
    proportional read-order position when the same text recurs in one
    klal" with no carve-out for the cross-page case - a real gap against
    its own stated contract, and a 4th bug in the exact shape this task
    brief anticipated (the author's own docstring already recorded 3 found
    during construction, all about page-continuation/proportional-position
    logic).

**Scope note**: `review_frontend/app.js` (spot-checked all `innerHTML`/
`value=` interpolation sites for escaping - all corpus-derived content is
escaped, `buildLegend()`'s two unescaped interpolations are static
`STATE_META` labels, not corpus data, so that's correctly unescaped, not a
gap), `tools/verify_reconstruction_witness.py`, `tools/review_lexicon_
gaps.py`, `tools/extract_abbreviation_forms.py`, and
`tools/detect_real_word_substitution.py` were each read in full - no
further bugs found, matching prior rounds' "checked and found clean"
convention (round 2's list, further up this file). `tools/verify_
reconstruction_witness.py` and `pipeline/review_server.py`'s witness
endpoints in particular already carry extensive fix history from earlier
2026-08-16 work (the `(klal_id, docai_token_index)` collision guard, the
furniture/tier word-by-word fixes, the line-wrap bbox fix) and showed no
further gaps on this pass.

### DONE 2026-08-16 — systematic detector built for the "real-word substitution" corruption class; 49 klalim flagged (83 candidates)

Per direct user request ("is there a good solution for #3?" / "go") - a real gap
this file already recorded as **NOT DONE**: the 13 "lexicon-invisible" corruption
candidates found earlier today (corrupt form is itself a real word, so no
lexicon-membership check can catch it) were all found by accident, not by any
repeatable method.

**`tools/detect_real_word_substitution.py`** (new, standalone, read-only).
Generalizes the exact "one clear winner" method `detect_ligature_corruption.py`
and `propose_abbreviation_expansions.resolve_truncated_word()` already use, to
single-letter SUBSTITUTION errors restricted to 8 empirically-observed
confusion pairs (ב/כ, ד/ר, ה/ר, ה/ד, ה/ח, ט/מ, ס/פ, ג/נ). For a word rare in
Part 1's own text, tries every confusable substitution and accepts a candidate
only if (a) the ORIGINAL word has ZERO independent-corpus attestation and (b)
the substituted form is well-attested there.

**Scope, stated honestly**: catches SUBSTITUTION errors only. Of the 13 known
incidental instances, ~10 are this shape; 3 (ישרץ->ישראל, ליבא->אליבא,
ארת->את) are insertion/deletion errors - a different shape, not attempted.
Cannot solve a confusion pair where BOTH readings are common independently
(klal 107's כל->בל is the concrete counterexample - כל is far more common than
בל, so a frequency test goes nowhere useful); that needs contextual/semantic
reading, not a sharper threshold.

**Real bug found and fixed while building it, not just described**: the first
working version used a dominance-RATIO test (candidate beats original by 5x)
rather than requiring zero attestation, and produced **348** "high-confidence"
hits on real data - mostly ordinary rare-but-real words losing a frequency
contest to an extremely common neighbour (אמה "cubit" -> אמר just because אמר
is near-ubiquitous). Requiring zero independent attestation for the original
cut that to **83** (82 high-confidence + 1 ambiguous), verified by spot-
checking 7 of them directly against `part1.json` context (all 7 plausible) and
finding exactly one further false positive: klal 88 w423 `רתם`, already scan-
verified print-faithful - added as a named, evidenced exclusion
(`KNOWN_FALSE_POSITIVES`), same precedent as `check_klal_token_orphans.py`'s
`PASS3_KNOWN_FALSE_POSITIVES`.

**Second bug found and fixed in the same build**: the ambiguous-candidate
bucket originally kept only the top-frequency option, discarding the others -
caught by reading klal 30 word 1206 `וטכל` in actual context (`דמל וטכל לשם
עכדו'`): the script's top pick was `ומכל` (103x), but the linguistically
correct reading is `וטבל` ("and immersed" - standard conversion/circumcision
terminology, 66x), a DIFFERENT substitution the frequency contest merely
ranked second. Fixed to return every qualifying option, not just the winner -
a reviewer choosing from a truncated list would never have seen the right
answer.

6 new hermetic tests (`tests/test_pipeline_logic.py`), each mutation-verified
(reintroduced the dominance-ratio bug, the truncated-ambiguous-list bug, and a
removed KNOWN_FALSE_POSITIVES exclusion - all 3 confirmed red, restored
green). 114/114 pytest.

**49 klalim flagged** (`reviewer: "ai-real-word-substitution"`, `needs_revisit:
true`), covering all 83 candidates (grouped one decision per klal, listing
every candidate word in that klal, matching `review_lexicon_gaps.py`'s
convention). Textual/frequency evidence only, nothing scan-verified, no
`part1.json` edit. Verified: `review_decisions.jsonl` grew 493 -> 542
(append-only, all 49 well-formed, spot-confirmed live via
`/api/klal/4/flag`), `part1/2/3.json` sha256 unchanged.

**Still open, correctly not closed by this**: the 3 non-substitution-shaped
lexicon-invisible instances, and the fundamental "both readings common"
blind spot (klal 107's כל/בל) - neither is solvable by this method, only by
context-aware reading (the semantic-plausibility passes, run at partial
coverage so far).

### DONE 2026-08-16 — 19 previously reported-but-not-flagged findings, now flagged

Per direct user request ("are the other findings flagged for human review? / yes and
any other findings not flagged") - a check across today's session for anything written
up in this file as a finding but never recorded as a `klal_flag` decision. Found two
such groups, both already documented above/below in this file, neither previously
flagged:

- **5 of the round-2 semantic sample's 7 next-klal gematria-marker mismatches** (klal
  15, 21, 36, 46, 64 - 49 and 62 were already flagged, being inside that round's actual
  sample). These 5 were found by a corpus-wide MECHANICAL check, not individually read -
  flagged with that caveat explicit in each note, and with klal 21/64 additionally
  marked lower-confidence per this file's own assessment ("probably an ordinary
  sentence-final word after a colon, not a marker").
- **All 13 of the "lexicon-invisible" corruption candidates** found incidentally while
  reading context during today's lexicon-gap triage (`review_lexicon_gaps.py`),
  explicitly excluded from that pass's 43 systematic flags. Every one of these 13
  klalim already carried an earlier flag for a DIFFERENT word from the systematic
  pass - since the dashboard shows only the latest decision per klal, the incidental
  finding was invisible to a reviewer working from the dashboard alone until this. Word
  index for each looked up fresh against `part1.json` (not assumed from the prose) -
  `klal 159` needed both of its two matching occurrences named, since the original
  note didn't specify which one.

19 new `klal_flag` decisions (`reviewer: "ai-followup-unflagged-findings"`,
`needs_revisit: true`), all textual evidence only, none scan-verified, no `part1.json`
edit. Verified: `review_decisions.jsonl` grew 474 -> 493 (append-only, all 19 well-formed,
spot-confirmed live via `/api/klal/15/flag` and others), `part1.json`/`part2.json`/
`part3.json` sha256 unchanged, 108/108 pytest.

### DONE 2026-08-16 — CASE-YAD-MALACHI.md/VERIFIED-AGAINST-THE-INK.html refresh, root reorg, and file hygiene, all closed out

Full detail in the commits themselves (`9d4ea1d` reorg, `a324b72` klalim/ archive,
`de0750a` doc refresh, `525671c` image regeneration) - compact summary here per this
file's own "compact current handoff" rule:

- **Root reorganized** into `pipeline/` (9 files, the live rebuild_all.sh chain + review
  tool) and `tools/` (15 files, everything manual/standalone) per user-selected layout;
  every `REPO` path, cross-script import, test import, and `rebuild_all.sh` invocation
  fixed and verified (108/108 pytest, 14/14 Playwright, full clean rebuild, 0 API calls).
- **Two case/evidence docs refreshed against current reality**: `VERIFIED-AGAINST-
  THE-INK.html` gained a new centerpiece section on the alef-lamed ligature bug (a real
  1200 DPI crop generated fresh from `berlin_square_corrected.pdf`, klal 88 page 40) and
  had every stale number corrected (222/222 klalim trusted, was 208/222; 316/356
  candidates vision-adjudicated, was 90/794; the klal 92-165 defect marked resolved).
  `CASE-YAD-MALACHI.md`'s "Current state"/"Bottom line"/"The ask" rewritten to match, 4
  dead image refs and 4 dead `data/*.md` refs fixed, 2 pre-existing dangling footnotes
  (`[^linker]`, `[^ocrpd]`) found and fixed while auditing.
- **Root cause of the broken images found, not just the symptom**: `images/*.png` sat
  under this repo's blanket `.gitignore` PNG rule with no exception, so any image placed
  there was never trackable - broken on every clone but the one that made it. Regenerated
  2 of the 4 original images directly from `berlin_square_corrected.pdf` (title page,
  Klalei HaAleph opening - both content-verified against existing footnotes/alignment
  data before use) and added specific `.gitignore` exceptions, matching the precedent
  already set for the two source PDFs. The other 2 (a citation-screenshot, a Rashi-scan
  comparison) need assets this repo doesn't hold - left pending, not faked.
- **Data/file hygiene**: archived a stale, unreferenced `klalim/` directory (668 files,
  older format) to `archive/data/klalim/`; corrected `CLAUDE.md`'s own claim of a
  nonexistent `processed_klalim/` directory found in the process. **2026-08-16, later**:
  4 gitignored/untracked stray root files with no live reference (`test_page.pdf` -
  confirmed leftover from the archived `orchestrator.py`'s hardcoded test fixture;
  `document_jsons/test_page-*.json` - DocAI output derived from that same fixture;
  `test_crop.png` - unexplained; `KiddushinRogochovDraft.pdf` - unexplained, possibly
  unrelated to this project) moved to `archive/old/` per direct user instruction. Since
  all four were already gitignored, this is a local filesystem move only - no commit,
  nothing for git to track either way.

### DONE 2026-08-16 — semantic-plausibility spot-check ROUND 2, a fresh 20% sample of Part 1 — 32 klalim flagged, 2 possible NEW dropped-lamed-ligature instances, 1 new mechanical check

A second, independent full-sentence reading pass over Part 1, deliberately
sampling klalim the 2026-08-14 `ai-semantic-spotcheck` pass did NOT flag. **No
corpus file was touched** — `part1.json`/`part2.json`/`part3.json`/`lexicon.txt`
are sha256-identical to `HEAD` before and after; `review_decisions.jsonl` grew
442 → 474 lines with the first 442 byte-identical to `HEAD`; 108/108 pytest
before and after. The work is 32 appended `klal_flag` rows, nothing else.

**Sample definition — recorded precisely this time, closing the exact gap this
round had to work around.** The 2026-08-14 pass recorded only "59 of 222
klalim, seed 20260814" in prose, with no committed script or seed-reproducible
artifact, so only the 33 klalim that produced a flag were recoverable (via
`reviewer: "ai-semantic-spotcheck"`); the other ~26 are unrecoverable and may
have re-entered this round's pool by chance. That is an acknowledged overlap
risk, not a clean complement.
- **Pool**: all 222 Part-1 klal_ids minus the 33 recoverable already-sampled
  ones (1, 8, 29, 37, 39, 41, 44, 48, 54, 60, 61, 64, 66, 68, 92, 94, 97, 106,
  115, 116, 136, 149, 154, 159, 169, 174, 197, 199, 200, 209, 214, 216, 217)
  = **189 klalim / 39,452 words**.
- **Method**: `random.seed(20260816)`, `order = random.sample(pool, len(pool))`
  (a full permutation of the sorted pool), then take klalim from the front of
  that permutation while the cumulative word count is < 10,500.
- **Sample**: **55 klalim / 10,510 words / 19.98% of Part 1's 52,609** —
  4, 7, 10, 11, 12, 14, 18, 20, 25, 32, 38, 43, 45, 49, 55, 62, 67, 70, 71, 76,
  78, 86, 87, 88, 89, 96, 98, 101, 107, 108, 110, 111, 114, 118, 123, 126, 128,
  140, 141, 142, 146, 156, 160, 161, 166, 173, 176, 184, 189, 195, 202, 204,
  206, 212, 222. Every one was read in full, not skimmed.
- A THIRD pass can exclude these 55 exactly by re-running the same two lines.

**Result: 32 of the 55 klalim flagged, 85 word-level candidates**
(`reviewer: "ai-semantic-spotcheck-round2"`, `needs_revisit: true`, one row per
klal, each note naming every word with its `word_index`, quoted context, and the
specific reason). Every one of the 85 `(klal_id, word_index, token)` triples was
validated against `part1.json` before any row was written. **TEXTUAL EVIDENCE
ONLY — nothing here was checked against the scan**, and klal 88's already-scan-
verified `רתם`/`התם` (print-faithful broken type) is the standing proof that
some of these will be faithful to the ink. Flagged klalim: 4, 7, 10, 11, 12, 14,
18, 25, 38, 45, 49, 62, 67, 70, 71, 76, 88, 96, 98, 101, 107, 110, 126, 128,
140, 146, 161, 176, 189, 204, 206, 212. **23 klalim were read and deliberately
NOT flagged** (20, 32, 43, 55, 78, 86, 87, 89, 108, 111, 114, 118, 123, 141,
142, 156, 160, 166, 173, 184, 195, 202, 222) — see the calibration note below.

- **TWO POSSIBLE NEW INSTANCES OF THE ALEF-LAMED LIGATURE (U+FB4F) DROPPED-LAMED
  EXTRACTION BUG, in a pattern this file records as complete with "0 known
  remaining candidates."** Both are a missing `ל` immediately following an `א`,
  the confirmed mechanism's exact fingerprint:
  - **klal 206 w2 `או` → `אלו`**, in the klal's head-line AND in its `title`
    FIELD (`הרי או באזהרה`). The klal's own body writes `הרי אלו באזהרה`
    correctly **six times**. `detect_ligature_corruption.py` would place `או` in
    its ambiguous-with-a-common-standalone-word bucket rather than report it —
    this is precisely the residue only context reading can surface.
  - **klal 140 w97 `והשוא` → `והשואל`** (`כשחשב המתיר והשואל שמותר להתיר
    לכתחלה`). Note that script builds its frequency table from the part file
    being scanned, so a base form rare in Part 1 can be missed.
  - **NOT YET DONE**: scan-verify both. If confirmed, "0 known remaining
    candidates" is wrong and the ambiguous bucket needs a second, context-aware
    pass rather than a frequency test (Lesson 7: fixing one root cause does not
    explain every symptom that looked the same).
- **NEW MECHANICAL CHECK, cheap, not yet scripted (Lessons 8/18): the
  next-klal gematria marker printed after a klal's closing colon.** 29 Part-1
  klalim carry one; **7 of the 29 disagree with `gematria(klal_id + 1)`** —
  klal 15 `פז`/`טז`, 21 `כך`/`כב`, 36 `לו`/`לז`, 46 `מו`/`מז`, **49 `ג`/`נ`**,
  **62 `סוג`/`סג`**, 64 `אין`/`סה`. (21 and 64 are probably ordinary sentence-
  final words after a colon, not markers; 15/36/46/49/62 each show a single-
  letter or stray-letter error of exactly the classes already recorded.) Only
  49 and 62 fall inside this round's sample and are flagged; **the other five
  are reported here and NOT flagged — nobody has read those klalim in this
  pass.** This bears on Success Criterion 2 (chunking), and it costs
  milliseconds to run corpus-wide. Separately, the LEADING marker disagrees
  in 3 klalim (150 `קן`, 180 `קף`, 190 `קץ` — final forms where the plain form
  is expected); that reads as a print convention, not corruption, and is
  recorded as informational only.
- **TITLE-FIELD data issues, distinct from body text** (they are what Sefaria
  would display and what a citation resolves to — Success Criterion 3):
  **klal 101**'s `title` is `מתנין לעקור דבר מן התורה בשב ואל תעשה` but the
  klal's own opening line reads `ב"ד מתנין לעקור...` — the title has lost its
  subject. **klal 88**'s `title` carries `וכאבל` (for `ובאבל`) and **klal
  206**'s carries `או` (for `אלו`), the same corruptions as their body text.
  No prior check has ever compared a klal's `title` field against its own
  opening line; that is another cheap sweep nobody has run.
- **The dominant class is the single-letter OCR-confusion class named by today's
  lexicon-gap triage, but the majority of these instances are INVISIBLE to that
  triage because the corrupt form is itself a real Hebrew word in
  `lexicon.txt`** — the structural failure that entry already flagged as its
  "SECOND FINDING, and the more important one." Examples from this round, all
  with internal corroboration owing nothing to a dictionary: klal 107 w26 `כל`
  → `בל` (the klal's own head-term is `בל תוסיף`); klal 12 w212 `עור` → `עוד`;
  klal 128 w820 `המפקיר` → `המפקיד` (the same perek is written correctly twice
  in the same klal); klal 140 w159 `הפרת` → `הפת` (written correctly 23 words
  earlier); klal 176 w480 `מייתכא` → `מייתבא`; klal 88 w510 `אכל` → `אבל` and
  w327 `חזה` → `וזה`; klal 38 w27 `מרבץ` → `מרבנן`; klal 110 w76 `לטרוי` →
  `למהוי` (BK 30a, quoted verbatim otherwise); klal 62 w71 `דודאה` → `הודאה`
  (BB 40a's three-item list, second item corrupt). **This round did not run a
  systematic detector for the class** — it read 55 klalim. The systematic sweep
  that entry records as NOT DONE (an independent-attestation ratio test over
  every Part-1 token, not a lexicon-membership test) is still not done, and this
  round is independent evidence that its true corpus-wide count is materially
  higher than 109.
- **A recurring `ו`→final-`ן` shape, not previously named**: klal 4 w403 and
  klal 25 w714 `איהן` → `איהו`, klal 71 w5 `היינן` → `היינו`, klal 126 w54
  `רבן` → `רבו`, klal 62 w70 `כתובן` → `כתובו`, klal 25 w364 `דברין` → `דבריו`.
  Six instances in a 20% sample, all in ordinary words, all producing a
  lexicon-resident token.
- **Abbreviation-internal letter confusions are systematically under-detected**
  because a two-or-three-letter gershayim form is rarely in `lexicon.txt` at
  all and rarely has a "one edit away" neighbour: `ב"ט`→`ב"מ` (klal 25 w136,
  klal 98 w60), `כ"ט`/`כ"ס`→`כ"מ` (klal 25 w727, klal 128 w126, klal 204 w15),
  `ח"ט`→`ח"מ` (klal 96 w23), `מר"ת`→`מד"ת` (klal 67 w43), `אע"ס`→`אע"פ` (klal
  161 w83), `ר"ס`→`ר"פ` (klal 12 w74), `ש"ס`→`ש"מ` (klal 128 w353),
  `בי"ר`→`בי"ד` (klal 189 w277), `ע"ר`→`ע"ד` (klal 98 w23), `הרל"ם`→`הרמב"ם`
  (klal 12 w192), `למ"ר`→`למ"ד` (klal 140 w91).
- **Two further artifact classes, counted corpus-wide (informational, no flags
  outside the sample):** 45 lone-geresh tokens (a bare `'` standing as its own
  word, e.g. `בפ' '`) across 29 Part-1 klalim; 43 punctuation-glued tokens
  (`.לא`, `:לוקי`, `,נתיבות`) across 34 klalim, concentrated almost entirely in
  klal 168-222. Also a small gershayim-as-double-yod class (`דייה` for `ד"ה`
  ×3, `לייה`/`לייג`/`לייב`, `יייז`) and a misplaced-gershayim class (klal 45
  w21 `נלפ"קד` against `נלפק"ד` ×2 / `לפק"ד` ×8 elsewhere).
- **klal 189 may be TRUNCATED, not merely corrupt**: it ends
  `...וכל :לוקי דינים אלו בחדושי הריטב"א` with a colon glued to a broken word,
  no closing `:` and no next-klal marker, unlike its neighbours. Flagged as a
  possible boundary problem (Success Criterion 2), not only a word-level one.

**Calibration** — 23 of the 55 klalim read produced no flag, and several
initially-odd readings were deliberately passed rather than flagged: klal 89
w18 `אכל` is genuine Aramaic `א + כל` ("on each of them"), not the `אבל`
corruption it superficially resembles; klal 88 w425 `רתם` is the already-scan-
verified print-faithful instance and is excluded; klal 43 w99 `הרי`, klal 20
`מדסיפא`, klal 111's `לר"ס`, klal 89 `בעינים`, klal 146 `ערך ספק` and klal 160
`בשעת הרוח` all read oddly but each has a plausible non-corrupt reading and
none was flagged; terse elliptical argumentation and dense folio/acronym runs
were treated as the text's normal register throughout, never as evidence of
corruption. klal 189 w406 `דרתם` WAS flagged but with an explicit caveat that
the prior is print-faithful, on klal 88's precedent.

**Overlap with today's other work, called out per klal** (each note carries its
own OVERLAP line): klal 4, 7, 12, 14, 25, 43, 88, 128 were already flagged by
`ai-lexicon-full-review` — every candidate reported here is at a DIFFERENT word
index than that pass's; klal 43 produced nothing new and is not re-flagged.
klal 4 w36 `טרור` and klal 88 w1061 `ישרץ` are already in this file's 13-item
lexicon-invisible list and are not re-reported. klal 176 carries one of the 7
baselined foreign characters (w694 `;`) — a different, already-reported item.
Note the dashboard shows the LAST row per klal as current, so for those 8
klalim the `ai-lexicon-full-review` note is no longer the displayed one; nothing
is lost (the log is append-only and `history_for()` returns all rows), but a
reviewer working from the dashboard alone will not see both.

**NOT YET DONE, in priority order**: (1) scan-verify the two possible ligature
instances (klal 206 w2, klal 140 w97) — they bear on whether a pattern this file
calls closed actually is; (2) scan-verify the 85 candidates through the normal
review pipeline; (3) script the next-klal-marker check and the title-vs-opening-
line check and decide whether either belongs in `rebuild_all.sh`; (4) the
systematic independent-attestation sweep for the lexicon-invisible confusion
class, still not done.

### DONE 2026-08-16 — the 3 remaining found-not-fixed items from today's two revalidation rounds, closed (`4171531`)

Per direct user request ("complete 2" against the open-items list). All
three were already diagnosed by round 1 or round 2 above; this closes them.
Deliberately touches witness (item 2) and punctuation (item 3) code, which
the two revalidation rounds excluded by standing scope - user-directed
exception, naming these three specifically, not a re-opening of that
exclusion generally.

1. **`build_corrections_dataset.py`'s running-header filter** was a
   substring test (`"מלאכי" in orig_word`) on the whole joined diff-span
   text - a real word merely CONTAINING those four letters as a substring
   (a prefix glued on the front, or an adjacent token fused into the same
   span) would have been silently treated as header furniture and dropped,
   never surfacing as a candidate. Extracted to `is_running_header()`, now
   exact-DocAI-token equality, matching `check_klal_token_orphans.
   FURNITURE_WORDS`'s existing convention. Verified byte-identical
   `corrections_candidates_part1.json` before/after - a real no-op on
   today's data, defence-in-depth against the next scan/print.
2. **`review_frontend/app.js`'s witness panel** had the identical
   unescaped-`value=` bug already fixed in the candidate panel this session
   (round 2's finding 3: a gershayim in a custom reading truncates the
   displayed value on re-open) - round 2 deliberately left it, citing the
   witness scope exclusion. Applied the same `escapeHtml`/`escapeAttr`
   treatment to the witness panel's context highlight, custom-text value,
   note textarea, and option label/text.
3. **`propose_punctuation_part1.py`'s cache key** was `sha256(klal_id|
   clean_text)` only, not covering the prompt template - the identical gap
   already fixed in `verify_corrections_vision.py` 2026-08-14 (see that
   file's `PROMPT_HASH` for the precedent and the incident it prevents).
   Extracted `PROMPT_TEMPLATE`/`PROMPT_HASH` the same way, folded
   `prompt_hash` into the key via a new `cache_key_for()`, and added a
   lossless migration (`migrate_add_prompt_hash`) that back-fills any
   pre-fix cached row whose klal text still matches today's corpus. Checked
   against the real `punctuation_cache.db` (a scratch copy, not the tracked
   file): **0 of its 3 existing rows migrate**, because klal 1/2/3's text
   has itself changed since the 2026-08-14 pilot that cached them - already
   orphaned by ordinary corpus-content drift, unrelated to and unaffected
   by this fix. The migration is verified correct against synthetic data
   instead (a hermetic test with a real matching row, confirming it DOES
   carry over when the text hasn't drifted).

All three: hermetic unit tests added (`tests/test_pipeline_logic.py`), each
mutation-verified (reintroduced the original bug, confirmed the new test
goes red, restored, confirmed green). Full `./rebuild_all.sh` run clean:
stage 1-2 output confirmed byte-identical before letting the vision stage
run (a real check, not assumed safe), all cache hits, 0 live API calls,
108/108 pytest, 14/14 Playwright, all 9 corpus/derived/decision files
byte-identical. `review_frontend/app.js` is read fresh from disk per
request (`_serve_static`, no restart needed - confirmed by reading the
server code, not assumed).

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

**Found, NOT fixed at the time (reported rather than changed) — BOTH SINCE FIXED,
2026-08-16, see the "3 remaining found-not-fixed items" entry earlier in this
handoff (`4171531`): this list was left stale for several commits after the
fix landed, exactly the Lesson-19 failure shape this file keeps warning about,
now caught and corrected here too:**
- ~~`review_frontend/app.js` interpolates `corr.reasoning`, `chosen_text` and
  `note` into `tooltip.innerHTML` unescaped.~~ **FIXED** — `escapeHtml`/
  `escapeAttr` applied at every site in the candidate/klal-flag/manual panels
  (`7153e1d`) and the witness panel (`4171531`).
- ~~`build_corrections_dataset.py`'s running-header filter is a bare substring
  test.~~ **FIXED** — extracted to `is_running_header()`, now exact-token
  equality matching `check_klal_token_orphans.FURNITURE_WORDS`'s convention
  (`4171531`).
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
- **CLOSED 2026-08-16, later** - `pipeline-audit-fixes-and-page-order-
  repair` (tip `5a86ef6`, "fix 8 correctness bugs, repair transposed PDF
  leaves 37/38"), previously flagged above as "not investigated further,"
  is gone: the branch ref itself no longer exists in `refs/heads` (deleted
  by an earlier, unlogged action - the commit survives only via reflog,
  not merged into `master`, `git branch --contains 5a86ef6` empty). Per
  direct user request, did the line-by-line confirmation this entry
  previously said was missing, on the highest-risk files first:
  `part1.json`'s one real content diff (klal 144, a stray extra `כ` in
  `כתב כ הכ"ס`) is already fixed identically in current `master`;
  `rebuild_all.sh`'s diff is pure path-reorg/comment updates; `verify_
  corrections_vision.py`'s 48-line diff and `review_frontend/app.js`'s
  83-line diff both show every branch-only line as an OLDER, less-evolved
  version of logic `master` already carries further (the branch's raw
  inline prompt vs. master's named `PROMPT_TEMPLATE`/`PROMPT_HASH`; the
  branch's unescaped `innerHTML` vs. master's `escapeHtml`/`escapeAttr`).
  No branch-only content found anywhere that master lacks. Confirmed
  superseded, not orphaned. Nothing to delete - the ref is already gone -
  and no further action needed.
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
   - **FIXED 2026-08-16** (was "STILL OPEN, not investigated" here since
     2026-08-14): `propose_punctuation_part1.py`'s cache key didn't cover the
     prompt text or model (risk 3). Fixed the same way as its LIVE-pipeline
     sibling below (`verify_corrections_vision.py`, closed 2026-08-14) -
     `PROMPT_TEMPLATE`/`PROMPT_HASH` extracted, folded into the key, lossless
     migration added. See the "3 remaining found-not-fixed items" entry
     earlier in this handoff (`4171531`) for full detail.
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
