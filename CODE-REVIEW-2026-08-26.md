# Code review, 2026-08-26 — findings inbox (partial run)

`/code-review max a16f9a0^..HEAD` over the 2026-08-24/25 work: **28 commits, 99
files, +28,288 / −13,750**. The run was launched twice and **exhausted the
session budget both times**; of ~10 angle agents, **three completed** and
returned findings. There was **no verification pass** — the skill's verify stage
never ran — so everything below except the first item is **unverified angle
output**, recorded verbatim in substance so a later session need not re-derive
it. Treat each as a lead with an argument attached, not as a confirmed defect.

The three angles that finished: **F (reuse)**, **G (simplification)**,
**H (efficiency)**. Angles A/B/D/E/J and the line-by-line scan never ran, so
**correctness coverage of this range is incomplete** — the one confirmed
corpus-damaging bug below came from the *reuse* angle, not a correctness angle,
which is a reason to finish the job rather than call it done.

---

## FIXED — the one that mattered

**1. `reconstruct_placeholder_klalim.py` sliced a reading-order list with a raw
array index.** `marker_position` is an index into the RAW token array —
`build_gematria_trace.py:47` says so outright — but `page_words()` returned
tokens re-sorted by `bgt.reading_order()`. Verified: the two orders disagree on
**23 of 391 trace rows**, and **6 of the 51 klalim written 2026-08-25 (287, 414,
443, 444, 487, 490) took a boundary from the wrong token**. Corpus reverted, tool
fixed, reconstruction redone — 15 of 44 reconstructions changed. Commit
`930ce76`. `tools/check_span_shortfall.py::span_tokens_for` already did this
correctly and should have been imported.

---

## Open — reuse (Angle F)

**2. Third copy of the `word_freq.json` loader** (`reconstruct_placeholder_klalim.py:97`).
The canonical `docai_filter.reference_frequencies()` is lru-cached and normalises
keys with `hebrew_letters_only`; this copy does neither, yet its consumer looks up
normalised forms. Latent today (0 of 185,593 keys carry a non-letter), fatal the
day the cache is regenerated keeping geresh/gershayim: attestation collapses,
every reconstruction fails the lexical gate, and the reported reason blames the
text rather than the arbiter. `validate_suppression_filters.py:87` is a second
copy.

**3. `is_placeholder` duplicated** between `reconstruct_placeholder_klalim.py:80`
and `export_corpus.py:625`, added in the same range, byte-identical, only the
export copy tested. They are two halves of one decision — which klalim get
rebuilt, which ship to Sefaria as empty — so divergence either loses a real klal
from the deliverable or ships a stub as text.

**4. `HEADER_CONTAMINATION_RE` re-implemented** (`reconstruct_placeholder_klalim.py:213`)
under the same name as `tests/test_corpus_invariants.py:92`, with a
**non-overlapping** rule. The invariant tolerates OCR misreads of both header
words (`מ[לר][אר]כי כ[לר][לר]י`); the tool requires literal `מלאכי`. So the
tool's stated contract — "a reconstruction that would fail the invariants is
simply not written" — is not actually enforced: `יר מראכי כללי הביח` passes the
tool and fails pytest afterwards, i.e. corpus damage committed then discovered.

**5. `--apply` writes the corpus with its own `json.dump`** instead of
`cio.save_part1(path=...)`, which exists precisely because two copies of that
body had already diverged once. Third copy; flags currently match.

**6. `api_klalim()` re-derives `api_klal()`'s merge precedence** by hand
(`review_server.py:830`) to compute counts, making a third encoding of the
word-state rule (server counts, `app.js` `wordState()`, and the test's
transcription). Two production defects in this very range came from that split.
The angle notes the honest counter-argument: calling `api_klal` 222 times per
request is what starved the Playwright suite, so the fix is a shared
`word_state()` + merged-entry builder, not naive reuse.

**7. `MACHINE_RESOLVED_FLAGS` hand-copied into `app.js:141`** although the server
already ships flag metadata to that client via `/api/flags`. Kept in step by a
test that regex-scrapes JS source, which breaks on reformatting.

**8. `_same_line()` is a fourth definition of "same printed line"**
(`build_corrections_dataset.py:141`), where `corpus_io.center_y` documents itself
as *the* signal for that question. Genuinely different classifier, and
`estimate_insert_bbox` branches on it — a disagreement puts the reviewer's box on
the wrong ink, the exact defect that change was written to fix.

## Open — efficiency (Angle H)

**9. `api_page()` calls `_word_level_ai_flags()` per klal**, each re-parsing the
1.8 MB decisions log 1–3×. Measured: **GET /api/page/73 does 25 full parses,
159.5 ms, ~130 ms of it redundant** — up from 3 parses pre-diff. `api_klalim()`
already fixed this exact pattern and its comment warns against it.

**10. `_word_level_ai_flags()` re-reads `candidate_choice`/`manual_correction`**
that every caller already has in scope (`review_server.py:594`). 2 of 9 parses on
GET /api/klal/88.

**11. `api_klalim()` reads `manual_correction` twice**, 32 lines apart
(`:698` and `:730`).

**12. Two set comprehensions scan the whole flag map inside the per-klal loop**
(`review_server.py:783`): 222 × 1092 × 2 iterations, **9.1 ms vs 0.2 ms** if
bucketed once — an idiom the same function already uses twice.

**13. `_word_scan_position()` doesn't pass `regions`** to `_klal_all_pages()`,
forcing a 187 KB re-read per call; 6 reads per `/api/page/73`. The parameter
exists and is simply unused.

**14. `_claim_word_index()` does a linear scan** per overlay lookup
(`review_server.py:654`); klal 88 ≈ 2,580 comparisons. `app.js` builds the
by-index map this needs.

**15. `run_surya_part1_full_baseline.py:290` opens the 114 MB PDF inside the
per-page loop** — 63 opens for a full re-render — while the `--fill-gaps` block
added in the same commit opens it once, correctly.

**16. `repair_word()` called twice per candidate** in
`assemble_corrections_dataset.py` (`:319` and again inside
`_ligature_artifact_flag`), ~498 redundant derivations per rebuild.

## Open — simplification (Angle G)

**17. `open_count` is computed and served but no longer rendered** — both
frontend consumers were removed in this range, leaving only tests asserting it.
Lesson 29's exact pattern, reintroduced.

**18. The "Clear revisit flag" handler is copy-pasted** into both panels
(`app.js:1117` and `:1520`), ~20 lines each. This is how the original unclearable
flag bug happened.

**19. `saveManualDecision()` now returns three kinds of value** (false / null /
entry) but every caller tests only `!== false`; the documented contract and the
final `find()` are dead, and the obvious tidy-up silently breaks the delete path.

**20. `repair_stream()` has no production caller** — only a test — while the
package docstring claims the DocAI stream is repaired before consensus. Related
dead branch: `_reinsert_nonletters`'s `if letters == expanded` cannot fire.

**21. `_stamp_asset_versions` may be redundant** with the
`Cache-Control: no-cache, must-revalidate` the same handler already sends. The
angle argues the stamp does not address the incident that motivated it (a stale
tab needs a reload either way). Worth a decision: keep and justify, or remove
with the test.

---

## Not covered

Angles A (line-by-line), B (removed behaviour), D (language pitfalls),
E (wrapper correctness) and J (conventions) never completed. **No correctness
angle finished.** The range still needs a correctness pass — see the next
session's brief.
