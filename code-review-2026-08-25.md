# Heavy Code Review: Sefer Digitization Pipeline
**Date**: 2026-08-25 • **Scope**: Full pipeline + 7 days of changes (70 commits, 2026-08-18 → 2026-08-25)

> **TRIAGED AND CLOSED 2026-08-26**, jointly with `CODE-REVIEW-2026-08-26.md` rather than separately. C1/C2 were also found independently by that run and are fixed (182.5 ms -> 9.6 ms on `/api/page/73`). C3 is real as a class but named the wrong function: `_word_level_ai_flags`' last-page-wins produces 0 wrong answers today, while `_word_scan_position`'s first-page-wins - added in the reviewed range and not flagged here - is the one that diverges; all three resolutions are now collapsed into one. S2/S5 confirmed latent and measured (0 klalim diverge; part boundaries 222/444/667 correct today, still unasserted). S1/C4 accepted and deferred: they are structural refactors that want their own session. See `PROJECT-STATUS.md` item 21.


---

## Executive Summary

The codebase is **remarkably well-documented and defensively coded** for a single-developer project — most one-off fixes are already logged, lessons are codified, and the same bug classes keep getting structurally prevented rather than just patched. The orientation documents are honest, detailed, and unusually candid about failure modes.

That said, the velocity of the last 7 days (70 commits, 25 of which touched [review_server.py](file:///Users/ericsafern/work/sefer-digitization-pipeline/pipeline/review_server.py)) has concentrated complexity in ways that create **real structural risk**. Below are findings organized by severity.

---

## 🔴 Critical Findings (Errors / Latent Bugs)

### C1: `review_decisions._read_all()` re-parses the entire JSONL on every call — O(N²) per request

Every `api_klal()` and `api_klalim()` request calls `rd.all_current()` **multiple times** — for `candidate_choice`, `manual_correction`, `klal_flag`, `witness_choice`, `punctuation_choice`. Each `all_current()` call invokes [`_read_all()`](file:///Users/ericsafern/work/sefer-digitization-pipeline/pipeline/review_decisions.py#L176-L186), which re-reads and re-parses `review_decisions.jsonl` from disk and deserializes every JSON line.

In [`api_klalim()`](file:///Users/ericsafern/work/sefer-digitization-pipeline/pipeline/review_server.py#L685-L906) alone:
```
all_klal_flags     → _read_all()  #1
decided            → _read_all()  #2
_manual_for_flags  → _read_all()  #3
manual_decided     → _read_all()  #4  (re-reads same manual_correction data as #3!)
witness_decided    → _read_all()  #5
punct_decided      → _read_all()  #6
```

That's **6 full file reads + JSON parses** of the same growing append-only log per single `/api/klalim` request. The log currently has ~1,800+ lines and grows with every reviewer decision. As the corpus review progresses, every navigation click gets slower.

> **Fix**: Read `_read_all()` once per request and pass the records list through, or add a request-scoped memo. The file is small today but grows monotonically, and nothing ever truncates it by design.

### C2: `api_klalim()` calls `rd.all_current("manual_correction")` twice

Line 698 computes `_manual_for_flags` = `rd.all_current("manual_correction")`, and line 730 computes `manual_decided` = `rd.all_current("manual_correction")` — the **exact same query**, with the exact same result. Both read the entire log independently. This is a copy-paste artifact from the two features being added in different commits.

> **Fix**: Assign once, use twice. `_manual_for_flags` and `manual_decided` should be the same variable.

### C3: `_word_level_ai_flags()` doesn't deduplicate against multi-page bbox collisions

In [`_word_level_ai_flags()`](file:///Users/ericsafern/work/sefer-digitization-pipeline/pipeline/review_server.py#L569-L630), the bbox-lookup loop at lines 588-592 overwrites `bboxes[wi]` for any word that matches on more than one page — **last-page-wins**, the exact collision class that `_word_pages_map()` (line 466-512) was explicitly fixed to handle with a proportional-position heuristic. The fix in `_word_pages_map` was added on 2026-08-21 but `_word_level_ai_flags`' own loop was never updated to match.

```python
# Lines 589-592: last-page-wins, no proportional resolution
for page in pages:
    page_bboxes = _corpus_word_bboxes(klal_id, words, page)
    for wi, bbox in page_bboxes.items():
        bboxes[wi] = (bbox, page)  # ← silently overwrites first-page match
```

> **Fix**: Use the same proportional-position resolution as `_word_pages_map()`, or extract the shared logic into a common helper.

### C4: `synthesize_multi_witness.py` imports `review_server` at module scope

[`synthesize_multi_witness.py`](file:///Users/ericsafern/work/sefer-digitization-pipeline/pipeline/synthesize_multi_witness.py#L56) does `import review_server as rs` and then calls `rs._word_pages_map()` and `rs._corpus_word_bboxes()`. These are private (underscore-prefixed) functions in a 1,700-line HTTP server module. This creates a **hard dependency from a batch pipeline stage on the live web server** — any change to review_server's private helpers can break the rebuild chain.

> **Fix**: Extract `_word_pages_map()`, `_corpus_word_bboxes()`, and `_corpus_bbox_cache` into `corpus_io.py` (or a new `pipeline/scan_alignment.py`), where both `review_server.py` and `synthesize_multi_witness.py` can import them as public API.

---

## 🟡 Significant Findings (Shortfalls / Structural Risks)

### S1: `review_server.py` is a 1,736-line God Object

This file is a monolithic server that combines:
- HTTP routing and static file serving (1,574–1,736)
- Data loading and caching (121–211)
- Complex multi-source count aggregation (`api_klalim`, 685–906: **222 lines**)
- Complex multi-source entry merging (`api_klal`, 909–1,174: **266 lines**)
- Scan-geometry coordinate mapping (422–512)
- Per-word flag lifecycle logic (515–630)
- 6 different POST endpoint handlers (1,340–1,532)

It changed 25 times in 7 days. That churn rate in a file this size, with this much interleaved state logic, is the primary source of the fix-on-fix patterns visible in the git history (e.g., the "negative open_count" on 2026-08-25 caused by a fix on 2026-08-24 that only made the numerator distinct but not the denominators).

> **Refactor opportunity**: Extract into at least 3 modules:
> 1. `pipeline/scan_alignment.py` — `_corpus_word_bboxes`, `_word_pages_map`, `_word_scan_position`, `_klal_all_pages`
> 2. `pipeline/review_counts.py` — the count/state aggregation logic from `api_klalim` and the merge logic from `api_klal`
> 3. `pipeline/review_server.py` — HTTP routing, static serving, POST handlers (thin glue)

### S2: The `.split()` vs `.split(' ')` indexing scheme split is a time bomb

The codebase deliberately maintains **two different word-indexing schemes**:
- Machine candidates: `clean_text.split()` (whitespace-collapsing)
- Manual corrections / frontend: `clean_text.split(' ')` (space-preserving)

These produce different indices whenever the text contains double spaces, leading/trailing spaces, or non-space whitespace. Today they agree because `test_corpus_invariants` enforces no double spaces, and `apply_reviewer_decisions.py` normalizes at runtime. But:

**14 call sites** use `.split(" ")`:
| File | Lines |
|------|-------|
| [audit_applied_decisions.py](file:///Users/ericsafern/work/sefer-digitization-pipeline/pipeline/audit_applied_decisions.py#L103) | 103, 136 |
| [review_server.py](file:///Users/ericsafern/work/sefer-digitization-pipeline/pipeline/review_server.py#L737) | 737, 775, 944, 1293, 1325 |
| [apply_punctuation_decisions.py](file:///Users/ericsafern/work/sefer-digitization-pipeline/tools/apply_punctuation_decisions.py#L150) | 150 |
| [patch_witness_word_indices.py](file:///Users/ericsafern/work/sefer-digitization-pipeline/tools/patch_witness_word_indices.py#L54) | 54 |
| [propose_punctuation_part1.py](file:///Users/ericsafern/work/sefer-digitization-pipeline/tools/propose_punctuation_part1.py#L218) | 218, 281 |
| [validate_part1_corpus_integrity.py](file:///Users/ericsafern/work/sefer-digitization-pipeline/tools/validate_part1_corpus_integrity.py#L195) | 195 |
| [build_klal_page_regions.py](file:///Users/ericsafern/work/sefer-digitization-pipeline/pipeline/build_klal_page_regions.py#L243) | 243 |

The day someone introduces a text with an unusual whitespace pattern (or a regex-based cleanup inserts one), indices silently misalign between the display and the mutation paths.

> **Fix**: Normalize in `corpus_io.py` — add a `words_of(klal)` method that is THE single source of word lists, used everywhere. The test that gates double-spaces is necessary but insufficient (it guards the data, not the code that could introduce new data with different whitespace).

### S3: `_corpus_bbox_cache` is a module-level dict with no invalidation or size limit

[`_corpus_bbox_cache`](file:///Users/ericsafern/work/sefer-digitization-pipeline/pipeline/review_server.py#L422) at line 422 caches `(klal_id, page)` → bbox mappings **forever** (no TTL, no LRU, no size limit). The server re-reads JSON files fresh on every request by design ("deliberately no cache" per line 121), but this cache contradicts that design: if `docai_word_boxes/page_N.json` were re-extracted or if the corpus text changed (shifting alignments), the cache would serve stale bbox data until the server process is restarted.

> **Fix**: Either remove the cache (it's a premature optimization for a single-user tool) or add a `corpus_io.load_docai_page`-level cache with file-mtime invalidation.

### S4: `_parts_for()` silently treats any unrecognized input as Part 1

[`_parts_for()`](file:///Users/ericsafern/work/sefer-digitization-pipeline/pipeline/review_server.py#L153-L170) at line 170 returns `(1,)` for any `part_str` that doesn't match `"all"`, `"0"`, `"none"`, `"2"`, or `"3"` — including typos like `"11"`, `"4"`, or `"part1"`. A query like `?part=part1` silently returns Part 1 data, but `?part=all_parts` also silently returns Part 1 data. This is the kind of silent fallthrough that masks bugs in callers.

> **Fix**: Return `(1,)` only for `"1"`, and raise or return an error for unrecognized values.

### S5: Hard-coded Part 2/3 boundaries in `_get_part_num_for_klal()` and `_load_klalim()`

[`_get_part_num_for_klal()`](file:///Users/ericsafern/work/sefer-digitization-pipeline/pipeline/review_server.py#L129-L135) uses magic number `444` (line 132) and the filter in [`_load_klalim()`](file:///Users/ericsafern/work/sefer-digitization-pipeline/pipeline/review_server.py#L138-L150) uses magic numbers `223` and `444` and `445` (lines 144-146). These partition the klal range into Parts 1/2/3, but:

- `PART1_MAX_KLAL = 222` is canonically defined in `corpus_io.py` and asserted against the live corpus
- The boundaries for Parts 2 and 3 have **no corresponding constants** and **no test asserting them against the data**
- If part2.json or part3.json ever gains or loses a klal, these literals silently misclassify klalim

> **Fix**: Define `PART2_MAX_KLAL = 444` in `corpus_io.py` alongside `PART1_MAX_KLAL`, asserted by the invariant tests.

### S6: No CSRF or rate-limit protection on write endpoints

The review server's POST endpoints ([`/api/decisions/manual`](file:///Users/ericsafern/work/sefer-digitization-pipeline/pipeline/review_server.py#L1671), [`/api/decisions/candidate`](file:///Users/ericsafern/work/sefer-digitization-pipeline/pipeline/review_server.py#L1663), etc.) accept any JSON body with no authentication, CSRF token, or rate limiting. A script or even a browser extension on the same machine could append arbitrary decisions to the append-only log. This is documented as acceptable for a single-user local tool, but the log is git-tracked and **cannot be compacted by design** — bad rows live forever.

> **Mitigate**: At minimum, add a simple nonce or session token to prevent accidental double-submissions (the "suggestions on one click" fix at commit `1e76f99` suggests this has already happened).

---

## 🟢 Moderate Findings (Hard-coded Values / One-off Patterns)

### H1: Magic numbers in pipeline stage scripts

| Constant | File | Line | Value | Risk |
|----------|------|------|-------|------|
| `MAX_DIFF_SPAN_WORDS` | [build_corrections_dataset.py](file:///Users/ericsafern/work/sefer-digitization-pipeline/pipeline/build_corrections_dataset.py#L50) | 50 | `4` | Named, documented ✓ |
| `MIN_REPLACE_SIMILARITY` | [build_corrections_dataset.py](file:///Users/ericsafern/work/sefer-digitization-pipeline/pipeline/build_corrections_dataset.py#L60) | 60 | `0.5` | Named, documented ✓ |
| `MIN_VISION_CONFIDENCE` | [assemble_corrections_dataset.py](file:///Users/ericsafern/work/sefer-digitization-pipeline/pipeline/assemble_corrections_dataset.py#L48) | 48 | `0.7` | Named, documented ✓ |
| `CONTEXT_WINDOW_WORDS` | [verify_corrections_vision.py](file:///Users/ericsafern/work/sefer-digitization-pipeline/pipeline/verify_corrections_vision.py#L100) | 100 | `35` | Named ✓, cache-invalidating if changed |
| `CROP_PADDING` | [verify_corrections_vision.py](file:///Users/ericsafern/work/sefer-digitization-pipeline/pipeline/verify_corrections_vision.py#L109) | 109 | `0.02` | Named ✓, cache-invalidating |
| `WITNESS_CONTEXT_WINDOW` | [review_server.py](file:///Users/ericsafern/work/sefer-digitization-pipeline/pipeline/review_server.py#L1420) | 1420 | `12` | Named ✓ |
| `OVERLAP_TRIM_GAP` | [build_klal_page_regions.py](file:///Users/ericsafern/work/sefer-digitization-pipeline/pipeline/build_klal_page_regions.py#L301) | 301 | `0.002` | Named ✓ |
| `tol` | [build_klal_page_regions.py](file:///Users/ericsafern/work/sefer-digitization-pipeline/pipeline/build_klal_page_regions.py#L187) | 187 | `0.004` | **Unnamed inline** — Y-band tolerance |
| `MIN_ESTIMATED_BOX_WIDTH` | [build_corrections_dataset.py](file:///Users/ericsafern/work/sefer-digitization-pipeline/pipeline/build_corrections_dataset.py#L138) | 138 | `0.03` | Named ✓ |
| `223`, `444`, `445` | [review_server.py](file:///Users/ericsafern/work/sefer-digitization-pipeline/pipeline/review_server.py#L132-L146) | 132-146 | Part boundaries | **Unnamed, no test** |

> **Credit**: Almost every magic number has been named and documented, often with the commit that did it recorded in a comment. The exceptions are the Part 2/3 boundaries and the Y-band tolerance `tol = 0.004`.

### H2: `_NO_UPPER_BOUND = 10 ** 9` in `build_klal_page_regions.py`

[Line 381](file:///Users/ericsafern/work/sefer-digitization-pipeline/pipeline/build_klal_page_regions.py#L381): `_NO_UPPER_BOUND = 10 ** 9` is used as a "no real upper bound" sentinel for Parts 2/3's max_klal parameter. While functionally correct, this is fragile — a better approach is to compute `max(klal_id)` from the actual data for each part, or use `float('inf')`.

### H3: `union_bbox()` is defined independently in two files

Both [build_corrections_dataset.py](file:///Users/ericsafern/work/sefer-digitization-pipeline/pipeline/build_corrections_dataset.py#L126-L132) (line 126) and [build_klal_page_regions.py](file:///Users/ericsafern/work/sefer-digitization-pipeline/pipeline/build_klal_page_regions.py#L136-L142) (line 136) contain byte-identical `union_bbox()` implementations. This is exactly the pattern `corpus_io.py` was created to consolidate.

> **Fix**: Move `union_bbox()` to `corpus_io.py`.

### H4: Superseded stubs should be removed

[`tools/extract_surya_consensus_disputes.py`](file:///Users/ericsafern/work/sefer-digitization-pipeline/tools/extract_surya_consensus_disputes.py) and [`tools/extract_vlm_consensus_disputes.py`](file:///Users/ericsafern/work/sefer-digitization-pipeline/tools/extract_vlm_consensus_disputes.py) are 38-line stubs that exist only to print a deprecation message. They add confusion during code review (they appear in git stats as recently changed files) without serving any runtime purpose.

### H5: `_flag_answered_by_a_later_decision()` uses string timestamp comparison

[`_flag_answered_by_a_later_decision()`](file:///Users/ericsafern/work/sefer-digitization-pipeline/pipeline/review_server.py#L515-L552) at line 550 compares timestamps as raw strings:
```python
if decision and (decision.get("ts") or "") > flag_ts:
```
This works only because the timestamps are ISO 8601 UTC format (`YYYY-MM-DDTHH:MM:SS...`), which sorts lexicographically correctly. But it's brittle — a timezone-aware timestamp, a local time, or a slightly different ISO format (e.g., with a `+03:00` offset) would break the comparison silently. Given that `_now_iso()` uses `datetime.now(timezone.utc).isoformat()`, this is safe *today*, but it's an implicit contract that should be explicit.

---

## 📊 Churn Analysis: Fix-on-Fix Patterns

The git history reveals clear **cascading fix** patterns, where a fix in one commit creates a new bug discovered in the next:

| Date | Commit | Fix | New bug introduced |
|------|--------|-----|-------------------|
| Aug 24 | `07ce185` | Fix 5 shadowing collisions in api_klal | Made only NUMERATOR distinct, left denominators summing independently |
| Aug 25 | `1553556` | Fix negative open_count from above | — (finally stable) |
| Aug 24 | `1e76f99` | Stop saving suggestions on one click | — |
| Aug 25 | `6b8bf9c` | Auto-close manual-correction panel | Didn't reach stale-cached browser tabs |
| Aug 25 | `c9dd076` | Auto-derive cache-buster from file | — (fixed stale tabs too) |
| Aug 24 | `1e76f99` | Stop proposing "6.18M" as reading | — |

The most dangerous instance: the count-logic fix that introduced a negative `open_count` (klal 88 went from showing inflated counts to showing `-1`). This was a **3-commit arc**: the original multi-source count logic (working but overcounting) → the dedup fix (broke denominators) → the tri-state fix (correct). Each step was individually reasonable; the cascade happened because `api_klalim`'s count logic is too complex to reason about locally.

> **This is the strongest argument for S1's refactoring**: the count/state logic needs to be in a module with its own dedicated tests, not interspersed with HTTP routing and bbox lookups.

---

## 🏗 Refactoring Opportunities (Organized by Impact)

### R1: Extract scan-alignment geometry from `review_server.py` (High Impact)

**What**: Move `_corpus_word_bboxes()`, `_corpus_bbox_cache`, `_word_pages_map()`, `_word_scan_position()`, `_klal_all_pages()`, and the coordinate-resolution heuristics into a dedicated `pipeline/scan_alignment.py` module.

**Why**: These functions are already called by `synthesize_multi_witness.py` via private-name imports. They are pure computation (no HTTP state), self-contained, and independently testable. They are also the most algorithmically complex code in the server — the multi-page recurring-word collision fix alone is 50 lines of careful proportional-position arithmetic.

**Bug class prevented**: The C3 finding (stale bbox collision in `_word_level_ai_flags`) exists because the same logic was separately hand-coded in two places within the same file. Extracting it makes the single implementation the one that gets fixed.

### R2: Single-pass decision loading per request (High Impact)

**What**: Add a `DecisionSnapshot` class or a simple function that reads `review_decisions.jsonl` once and returns all six `all_current()` maps as a named tuple. Pass this through `api_klalim()` and `api_klal()` instead of calling `rd.all_current()` 6+ times per request.

**Why**: Eliminates finding C1 (O(N²) file reads) and C2 (duplicate reads), and makes the cost of growing the decisions log O(1) per request instead of O(N × calls).

### R3: Unify word-splitting into `corpus_io.words_of()` (Medium Impact)

**What**: Add `corpus_io.words_of(klal_or_text)` that returns the canonical word list. Decide once whether the canonical split is `.split()` or `.split(' ')`. The answer should be `.split()` with the normalization `apply_reviewer_decisions.py` already does at line 213.

**Why**: Eliminates finding S2's time-bomb. Today 14 call sites use `.split(' ')` and ~25 use `.split()`. They agree because no text has double spaces, but that's enforced by a test, not by the code.

### R4: Define Part 2/3 boundaries as constants (Low Impact, High Safety)

**What**: Add `PART2_MAX_KLAL = 444` and `PART3_MAX_KLAL = 667` (or derive them from the live data) in `corpus_io.py`. Add a `test_part23_max_klal_constants_agree` test.

**Why**: Eliminates finding S5. Three literal magic numbers (`223`, `444`, `445`) scattered across `review_server.py` with no tests and no constants.

### R5: Consolidate `union_bbox()` into `corpus_io.py` (Low Impact)

**What**: Move the identical `union_bbox()` implementations from `build_corrections_dataset.py` and `build_klal_page_regions.py` into `corpus_io.py`.

**Why**: Two byte-identical copies of a 6-line function in a project that already created `corpus_io.py` specifically to eliminate this pattern.

---

## ✅ What's Working Well

1. **Lesson codification**: 31 numbered lessons, each traced to a specific incident, with standing rules enforced in code (not just docs). This is unusually disciplined.

2. **Append-only audit trail**: The `review_decisions.jsonl` design is exactly right — no data is ever lost, every decision is traceable, and the separation of "record" from "apply" prevents silent corpus corruption.

3. **Cache key discipline**: After three real bugs (crop-only keys, missing context hash, missing prompt hash), the composite cache key `(crop_hash, word_a, word_b, context_hash, prompt_hash)` is thorough and correctly documented.

4. **Drift detection**: Every mutation path (`apply_replace`, `apply_manual_correction`, `apply_delete_insertion`) verifies the live text still matches the decision-time snapshot before writing. Defence-in-depth at the corpus-write boundary.

5. **Test gate in the rebuild chain**: `rebuild_all.sh` runs the invariant + logic tests as a hard gate. The tests are substantial (1,629 + 4,223 lines) and test real failure modes, not happy paths.

6. **Incremental flush discipline**: After the VLM baseline data-loss near-miss, every batch script now flushes to disk item-by-item. `verify_corrections_vision.py` rewrites its entire output after every candidate — expensive but crash-safe.

7. **Self-documenting comments**: Nearly every fix comment includes the date, the finding ID, the user report that triggered it, and the measured impact. This makes the codebase's history legible without reading git logs.

---

## Recommended Priority Order

| # | Finding | Severity | Effort | Impact |
|---|---------|----------|--------|--------|
| 1 | R2: Single-pass decision loading | 🔴 C1+C2 | ~1 hour | Eliminates O(N²) per request |
| 2 | R1: Extract scan-alignment | 🔴 C4 + 🟡 S1 | ~3 hours | Breaks the God Object, fixes C3 |
| 3 | R4: Part 2/3 constants | 🟡 S5 | ~30 min | Prevents silent misclassification |
| 4 | R3: Unify word-splitting | 🟡 S2 | ~2 hours | Closes the indexing scheme split |
| 5 | R5: Consolidate `union_bbox` | 🟢 H3 | ~15 min | Removes a documented anti-pattern |
| 6 | S4: Validate `_parts_for()` | 🟡 S4 | ~15 min | Stops silent fallthrough |
| 7 | C3: Fix ai_flag bbox collision | 🔴 C3 | ~30 min | Fixes last-page-wins regression |
