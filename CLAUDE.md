# Yad Malachi Pipeline

Digitization pipeline for **Yad Malachi** (R. Malachi ben Jacob HaKohen, Livorno
1766–7), a foundational halachic-methodology reference with 667 *klalim* across
three parts. Goal: a clean, structured digital text for Sefaria — see
`CASE-YAD-MALACHI.md` for the full rationale (287 dead Sefaria citations point to
this work today). Livorno 1766-7 is the work's ORIGINAL printing - the
actual scan this pipeline OCRs (`berlin_square_corrected.pdf`) is a
later Berlin second edition, see "Pipeline shape" below for the verified
detail; don't conflate the two.

> **Read `PROJECT-STATUS.md` at the start of every session, every time, no
> exceptions.** This file (`CLAUDE.md`) holds durable rules and architecture.
> `PROJECT-STATUS.md` holds the current, specific, dated truth — what's fixed,
> what's still broken, what was investigated and why. Neither substitutes for
> the other. Do not report on, fix, or make claims about corpus quality
> without having read it first.

> **Start the review dashboard (`python3 pipeline/review_server.py`, backgrounded) at
> the start of every session, every time, no exceptions** — check
> `lsof -i :8420` first and skip only if it's already running. It's the live
> human-review tool (see "Pipeline shape" below); the user works in it
> throughout a session and shouldn't have to ask for it each time.

> **Close open items before proposing new ones.** If `PROJECT-STATUS.md`'s
> Open Items section lists unresolved blockers, do not end a turn by offering
> to expand scope ("want me to also check X," "should I dig into Y next") —
> propose a plan to close the existing open items first, or ask which to
> prioritize. Finish what's already known-broken before suggesting where else
> to look.

> **Parts 2-3 are out of scope until Part 1 is clean AND an outside
> professional has independently confirmed the produced text is clean —
> not just this pipeline's own self-assessment.** User directive,
> 2026-08-10, restated explicitly to not be revisited until then: do not
> propose, scope, or start Parts 2-3 work — including "just the easy
> mechanical parts" — before both conditions hold. Rationale, in the
> user's own words: "if part 1 is bad the rest won't magically be
> better." This is not merely caution — see PROJECT-STATUS-HISTORY.md
> 2026-08-10 "methodology audit" for a concrete, already-confirmed reason
> the assumption "fix it once on Part 1, it generalizes" doesn't hold:
> the page-furniture contamination bug hit Part 1 at ~1 instance but hit
> Parts 2-3 at 74/445 klalim (~17%) — same bug class, same detection
> method, a much higher rate nobody has explained. Parts 2-3's own scan
> data can and does fail differently and worse than Part 1's; a clean
> Part 1 pipeline is not evidence Parts 2-3 will come out clean by the
> same process, let alone without its own scan-linkage/vision-
> verification infrastructure ever having been built or run there at
> all.

> **Log every finding to `PROJECT-STATUS.md` yourself, immediately, without
> being asked.** Finding a bug and only mentioning it in chat is not done —
> if the user has to go back through the conversation to recover something
> you found so it isn't lost, that is a dropped ball, and recovering dropped
> balls is not the user's job. The moment you confirm a real issue (a bug, a
> gap, a wrong claim in the file, a script fix, a new script, a job left
> running), write it into `PROJECT-STATUS.md` before moving to the next
> thing — not batched at the end of a long turn, not only when directly
> asked to "update the status file." This applies to your own tooling/script
> fixes too (cache bugs, dead models, UI fixes), not just corpus-content
> findings.

> **Terminology, standing as of 2026-08-15: an issue with the DATA is a
> "data issue," not a "bug." An issue with the CODE is a "bug."** These
> are two different failure classes with two different remedies — a data
> issue (e.g. the dropped-lamed ligature corruption, page-furniture
> contamination, a mis-transcribed word) gets fixed through the
> human-review decision pipeline against the actual scan, never a direct
> hand-edit; a bug (e.g. a cache key missing a component, a test scoped
> to the wrong fixture, a script's docstring overclaiming its own
> coverage) gets fixed by changing code. Calling a data issue a "bug"
> blurs which remedy applies and risks someone reaching for a code fix
> (or a blind find-replace across the corpus) for something that needs
> scan verification instead. Use the precise term in findings, commit
> messages, and `PROJECT-STATUS.md` entries going forward.

## Success criteria (in priority order)

1. **Absolute fidelity to the author's words.** The transcript must match the
   source scans exactly — no paraphrase, no silent normalization, no
   "improving" the text. Every correction must be traceable to a real
   disagreement (routinely DocAI-vs-stored-text; VLM and the untracked
   second physical scan are secondary cross-check signals used manually,
   not systematic legs of the automated pipeline - see "Pipeline shape")
   resolved by looking at the actual scan, not inferred.
2. **Accurate klal chunking.** Each of the 667 klalim must be correctly formed
   and delimited as its own unit, matching Sefaria's structural conventions —
   wrong boundaries (a klal split, merged, or mis-numbered) are as serious a
   defect as a wrong word.
3. **Sefaria-ready output.** The end deliverable must be usable as-is inside
   Sefaria's library in every respect (structure, encoding, section/klal
   numbering, citation-linkability) — not merely "clean text," but ready to
   ingest.

Any pipeline change, correction pass, or shortcut should be weighed against
these three before anything else (speed, script cleanliness, cost).

## Pipeline shape

**CORRECTED 2026-08-15 — verified against the actual scan and code, not
assumed.** The work's ORIGINAL printing is Livorno, 1766-7 (confirmed:
the front-matter approbation on the scan is explicitly dated ליוורנו
[Livorno]/התקכ"ז, i.e. Hebrew year 5527 = 1766-7 CE), but the source
PDF this pipeline actually OCRs — `berlin_square_corrected.pdf` — is a
LATER, SECOND printing, in Berlin, per its own title page (`נדפס ראשונה
בליוורנו... ועתה נדפס פעם שנית` — "first printed in Livorno... now
printed a second time," colophon `ברלין`, editor אפרים הערץ of Silesia,
"with several additions and corrections"). Square Hebrew typeface
throughout (not Rashi script) - matches the filename. Exact Berlin
printing date not yet established (out of scope to chase further right
now). Two PDFs are tracked in git specifically for this ONE scan (both
negated out of the otherwise-blanket `*.pdf` gitignore rule):
`berlin_square_corrected.pdf` (the live, working copy, page order fixed)
and `berlin_square_original_transposed.pdf` (the untouched original,
kept only so the page-order fix has a diffable reference - not a
second, independent scan of a different physical copy). A genuinely
SECOND physical scan (a different copy of the printed book) does exist
— `ספר_יד_מלאכי (1).pdf` — but it is untracked, not part of the routine
pipeline, and was used exactly once (2026-08-05, klal 1's second
disputed word) as a manual independent cross-check the user supplied;
see PROJECT-STATUS-HISTORY.md's "Klal 1's second flagged word" entry.

The LIVE, AUTOMATED comparison in today's pipeline
(`build_corrections_dataset.py`) is **DocAI's raw OCR tokens vs.
whatever is CURRENTLY STORED in `part1.json`** (via `klalim_demo_
dataset.json`) — not DocAI vs VLM as this section used to imply. VLM
extraction (`vlm_extractions/`, only ~12 sparse page files, not a
full-corpus pass) is a secondary, opportunistic cross-check signal used
manually during specific investigations (e.g. the 2026-08-14/15
dropped-lamed ligature investigation), not a systematic leg of the
automated candidate-generation pipeline - and its own klal-numbering
does NOT reliably align with the corpus's final numbering (confirmed:
VLM's stored "klal 2" and part1.json's current klal 2 are unrelated
text, almost certainly a klal-chunking/numbering mismatch on VLM's
side, not a content disagreement worth comparing word-by-word).

Where did the CURRENTLY STORED text in `part1.json` originally come
from, if it's not one of the two things being compared today? Traced
through git history: the repo's first commit (`2a5d43e`) contains only
extraction/adjudication scripts (`chunker.py`, `orchestrator.py`,
`consensus.py`, `adjudicate_vision.py`, `extract_hocr.py`,
`extract_json.py`, `batch_ocr.py` - all archived now) plus one sample
page's OCR output, no corpus text yet. Those scripts, run against the
Berlin scan, produced `full_text_cleaned_goal.txt`, which went through
many further "OCR fix"/"LLM cross-validation" passes (see early commit
history), and was THEN chunked into `part1.json`/`part2.json`/
`part3.json` for the first time (commit `73c428c`). Only from that
point does the architecture described below take over: DocAI's fresh
reading gets diffed against whatever's currently stored, disagreements
go to vision-crop adjudication, then human review, then get applied.
The exact internal logic of that original chunker/orchestrator/
consensus-era extraction pass has not been re-traced in detail - it
predates this file's documented architecture and would need its own
investigation if it ever matters (e.g. auditing a specific very-old
piece of text back to its origin).

1. **Extraction** — DocAI/VLM extraction through the (gitignored)
   `docai_word_boxes/`, `document_jsons_berlin/`, `vlm_extractions/` caches is
   the live path. `chunker.py` — the earlier script that pulled raw text
   per page from the PDF and handled the reversed-Hebrew-line quirk of
   this print's scans via `unreverse_line` — has been superseded by
   this and is archived at `archive/scripts/chunker.py` (CORRECTED
   2026-08-14: this section used to describe it as part of the live
   path; it is not — see "Directory layout" below for other file-existence
   claims in this document that had gone stale the same way).
2. **Adjudication** — `verify_corrections_vision.py` is the live vision
   adjudicator (run by `rebuild_all.sh`). NOTE: `orchestrator.py` was ARCHIVED
   2026-08-11 after an audit confirmed it was dead (not in `rebuild_all.sh`,
   imported only by already-archived code, entry points pointing at
   `test_page.pdf`) and carried 4 real bugs including the crop-hash-only cache
   this file used to claim was fixed project-wide. Formerly described as
   cross-validator: crops each token's bounding box from the PDF, sends it to
   Gemini (`google.genai`) for a vision-based OCR/VLM disagreement call, and
   caches every decision in `adjudication_cache.db` (sqlite, keyed by crop
   hash) so repeat runs don't re-spend API calls. Requires a Gemini API key in
   the environment (not committed — check `credentials.json`, gitignored).
3. **Assembly & lexicon** — outputs converge into `full_text_cleaned.txt` /
   `full_text_cleaned_goal.txt`, `part1.json` / `part2.json` / `part3.json`
   (one per Yad Malachi section), `aligned_klalim/` / `klalim_batches/`
   (per-klal JSON at earlier pipeline stages — CORRECTED 2026-08-16, this
   line used to name a `processed_klalim/` directory that does not exist
   anywhere in the repo and was never caught; see "Directory layout"
   below for what actually is tracked), and `lexicon.txt` (~19k unique
   validated Rabbinic Hebrew words used as a spell-check dictionary
   during cleanup passes).
4. **Demos/reports** — `pipeline/review_server.py` + `review_frontend/` (a
   live local server, run with `python3 pipeline/review_server.py` then open
   `http://127.0.0.1:8420/`) is the live, current human-review tool — use it
   to visually verify a correction, per the
   `.gemini/rules/robust_ocr_processing.md` rule file's UI-verification
   requirement, and to record a candidate-override or klal-flag decision
   (see "Human review decisions" below). It replaced the old
   `build_review_html.py` → `review.html` (a single ~963KB generated file
   with all of Part 1 inlined into one `<script>` tag) 2026-08-07 - that
   approach was retired for both a real data-pipeline bug it was surfacing
   (see PROJECT-STATUS.md "Punctuation-token diff bug fixed") and its own
   performance/architecture problems; `build_review_html.py` is now archived
   at `archive/scripts/build_review_html.py`, not part of the live pipeline.
   `VERIFIED-AGAINST-THE-INK.html` (an evidence showcase tied to
   `CASE-YAD-MALACHI.md`, which links it) is now the ONLY live demo/report
   artifact at root. It is a curated evidence document — 13 embedded scan
   crops with commentary, ~443 Hebrew characters total — NOT a rendering of
   the corpus, so it does not go stale when klal text changes. It has no
   generator script; it is hand-made and cannot be regenerated.
   `SEFARIA-VLM-DEMO.html` and its generator `build_vlm_demo.py` were
   ARCHIVED 2026-08-11 (`archive/docs/`, `archive/scripts/`): the demo was
   built from the discredited `aligned_klalim/`, showed text differing from
   `part1.json` in 145 of 222 Part-1 klalim, and rendered 14 fabricated
   placeholder bounding boxes across all 667 klalim under a "Precise
   Geometric Bounds" heading. Nothing linked it. It needs no replacement:
   `review_server.py` supersedes it internally (real per-klal boxes from
   `klal_page_regions.json`, live data, plus candidates and decisions), and
   `VERIFIED-AGAINST-THE-INK.html` already fills the outward-facing role.

   As of 2026-08-06, one-off `*-VISUAL-REPORT.html` / `*-OVERVIEW.html` /
   similar report docs from earlier in the project (dated through early
   August, superseded once `review.html` became the live verification tool,
   itself since superseded by `review_server.py`) were moved to
   `archive/docs/` — see "Directory layout" below. Don't assume a
   `*-REPORT.html` or `*-OVERVIEW.html` name at root is current; check
   whether a script in the active pipeline still generates it.

## Single source of truth for corpus text — read before editing any text file

**`part1.json` / `part2.json` / `part3.json` are the only hand-edited source
of truth for klal text.** Every other JSON/HTML artifact that shows or uses
klal text is *derived* from them and must be regenerated, never hand-edited
in parallel:

- `klalim_demo_dataset.json` = `part1.json` + `part2.json` + `part3.json`
  concatenated, nothing else. Regenerate with `build_klalim_demo_dataset.py`.
  (Before 2026-08-05 this was hand-maintained in parallel with the part
  files on every fix — exactly the kind of two-copies-of-the-truth setup
  that silently drifts. Don't reintroduce that.)
- `corrections_candidates_part1.json` → `corrections_verified_part1.json` →
  `corrections_part1.json` → `review_server.py`'s flag overlay is a
  pipeline, each stage derived from the one before it and from
  `klalim_demo_dataset.json`.
- `klal_page_regions.json` (per-klal scan bounding box, independent of
  whether the klal has any flagged correction) also derives from the same
  docai-token alignment.

**After any edit to a `part*.json` file, run `./rebuild_all.sh`** — this
regenerates every derived file listed above. `review_server.py` reads its
source files fresh off disk on every request (no embedded/cached data, no
restart needed), but it still needs those files to actually be current —
running the rebuild is what keeps them that way. Don't hand-run individual
stages and try to remember which ones are now stale; that's exactly how the
old `review.html` went out of sync for an entire session's worth of
corrections in August 2026 (see PROJECT-STATUS.md). The vision-verification
stage (the only one that costs API calls) is safe to re-run every time —
see the next section.

`./rebuild_all.sh --skip-vision` skips only the Gemini re-verification step,
for fast iteration when you don't need fresh flag classifications yet.

## Human review decisions — a separate, protected layer from the rebuild pipeline

`review_server.py` lets a reviewer override which candidate reading is
correct for a flagged word, or flag an entire klal for revisiting with a
note. Every such decision is appended (never overwritten or deleted) to
`review_decisions.jsonl` via `review_decisions.py` - this file is
**deliberately tracked in git and outside the corpus-build pipeline**, so
no `rebuild_all.sh` run can ever clobber a human decision (see
PROJECT-STATUS.md for why this matters: the one prior attempt at a human-
override mechanism was dead code that a pipeline rebuild silently
destroyed). A decision recorded in the UI does **not** touch `part1.json`
by itself — `apply_reviewer_decisions.py` is the separate, manually-run
script that promotes accepted decisions into the corpus text, with its own
drift detection and one-insert/delete-per-klal-per-run safety limit (see
its module docstring). Recording a decision and applying it to the corpus
are always two distinct, deliberate steps.

`audit_applied_decisions.py` (added 2026-08-14) is a read-only,
standalone check on that boundary from the other direction: for every
decision the log claims was applied (has an `apply_event`), does
`part1.json` still actually reflect it? `apply_reviewer_decisions.py`'s
own "don't re-apply" guard trusts the log permanently once a decision is
marked applied — sound only as long as nothing mutates `part1.json`
outside the normal apply-script flow. This script is the missing
re-check on that assumption; it changes nothing, only reports. Not part
of `rebuild_all.sh`, run manually.

### The vision-adjudication cache must be keyed on the full comparison, not just the crop

`adjudication_cache.db` caches Gemini's decision for "does this crop show
reading A or reading B" so repeat runs don't re-spend API calls. **The cache
key must include which two readings were being compared (crop_hash + word_a
+ word_b), not the crop image alone.** A crop-hash-only cache is a real bug,
not a hardening opportunity: the same bbox gets re-cropped across sessions to
answer different comparisons as `clean_text` changes (a fix, then later a
revert), and a crop-only cache silently returns a stale decision for the
*current* comparison — confirmed 2026-08-05, see PROJECT-STATUS.md: this
collapsed 217 real word-pair decisions onto 140 unique crops, meaning 77 had
already been silently overwritten by an unrelated comparison before anyone
noticed. `verify_corrections_vision.py`'s `corrections_cache` table does this
correctly; if you add another vision-caching script, key it the same way.

## Shared library modules — check these before hand-rolling a loader, a cache, or a client

Two modules in `pipeline/` are libraries, not entry points. Neither is ever
run directly; both are imported by scripts in **both** `pipeline/` and
`tools/`, via `sys.path.insert(0, os.path.join(REPO, "pipeline"))`.

- **`vision_adjudication_common.py`** (2026-08-17) — crop/cache/JSON-recovery/
  retry/client machinery for every Gemini-calling script.
- **`corpus_io.py`** (2026-08-17) — repo paths, corpus and derived-artifact
  loading (`load_klalim`/`load_part1*`/`save_part1`/`load_json`), DocAI
  page-token loading (`load_docai_page`, `DocaiPageCache`), the alignment and
  gematria-trace readers, `clean_word`/`hebrew_letters_only`, and
  `PART1_MAX_KLAL`.

**The standing rule: before writing a new `json.load(open(...))` for a
corpus/derived file, a new `docai_word_boxes/page_N.json` read, a new Gemini
client, a new sqlite decision cache, or a new copy of `PART1_MAX_KLAL` or a
Hebrew-letter set — use the shared module. If what you need genuinely differs,
add a parameter with a comment saying what real difference it encodes (the way
`has_model_column` and `load_docai_page(default=)` do), rather than a private
copy.**

Why this is a rule and not a preference: the identical bug class has now been
found in a hand-maintained copy **five separate times** in this project — the
missing-`prompt_hash` cache key three times (2026-08-14, 2026-08-16,
2026-08-16 again) and the missing Gemini request-timeout twice (2026-08-17,
in `verify_flagged_candidates_vision.py` and then in
`propose_punctuation_part1.py`, the latter outside the vision code
entirely). In every case the fix existed already, in a sibling file, and the
sibling never got it. That is Lesson 13's failure mode ("a hand-maintained
parallel copy is a second copy of the truth that happens to usually agree")
applied to code rather than data.

Each module's own docstring records, per item, the concrete incident that
justified extracting it — and, equally important, what was examined and
deliberately **not** extracted (the three page-furniture word sets, which
match by different rules over different contents; the punctuation cache's
genuinely different schema; each script's own prompt template and argparse).
Keep that convention: a coincidental resemblance between two scripts serving
different concerns is not duplication, and forcing a shared abstraction onto
one can silently change behavior — a data-affecting change wearing a
refactor's clothes.

## Directory layout

**REORGANIZED 2026-08-16** — root used to be flat: 24 live `.py` files
sitting directly next to `part1.json`, `rebuild_all.sh`, and everything
else, with this section as prose the only map of which script did what.
Per user request ("root should be clean... consider a code dir or even
three"), split into two subdirectories by role:

- **`pipeline/`** (11 files as of 2026-08-17, was 9 at the 2026-08-16
  reorg) — the scripts that make up the actual running system: the 5
  `rebuild_all.sh`-orchestrated correction-data stages, plus the live
  review tool (`review_server.py` and its 3 decision-layer scripts), plus
  the **two shared library modules** added 2026-08-17 (see "Shared library
  modules" below): `vision_adjudication_common.py` and `corpus_io.py`.
  These two are not entry points and are never run directly — they are
  imported by scripts in BOTH `pipeline/` and `tools/`, which is why they
  live here rather than in a third directory: `tools/apply_punctuation_
  decisions.py` already established the `sys.path.insert(0, os.path.join(
  REPO, "pipeline"))` cross-directory import at the reorg, and reusing it
  was cheaper than inventing a second convention.
- **`tools/`** (18 files as of 2026-08-17, was 15 at the 2026-08-16 reorg -
  `detect_real_word_substitution.py`, `check_next_marker_and_title.py`, and
  `verify_flagged_candidates_vision.py` added since; see PROJECT-STATUS.md
  for each) — everything run manually/standalone: all validators, the
  lexicon/abbreviation-expansion scripts, the punctuation pass, and the
  witness/reconstruction scripts.
- **`tests/`** — unchanged, still holds the pytest suite.
- Data files, caches, `rebuild_all.sh`, `review_frontend/`, and every `.md`/
  `.html` doc stayed at root — only Python scripts moved.
  `flagged_candidates_vision_report.json` (added 2026-08-16) is one such
  data file - the full-detail JSON output of `tools/verify_flagged_
  candidates_vision.py`'s Gemini vision-adjudication pass, kept at root
  alongside `corrections_candidates_part1.json` and similar (see
  PROJECT-STATUS.md for what it holds); not part of the `rebuild_all.sh`
  chain, a one-off report artifact, not regenerated automatically.

Every script's own `REPO` constant (`os.path.dirname(os.path.abspath(
__file__))`) was updated to go up one additional directory level so every
`os.path.join(REPO, ...)` path still resolves to the true repo root
(verified, not assumed: re-ran `rebuild_all.sh` post-move with byte-
identical output on all 5 derived files, 108/108 pytest, 14/14 Playwright).
`review_frontend/` did NOT move — `pipeline/review_server.py` serves it via
`os.path.join(REPO, "review_frontend")`, which still resolves correctly
under the same fix. The one cross-directory import this split created —
`tools/apply_punctuation_decisions.py` needs `pipeline/review_decisions.py`
— is handled with an explicit `sys.path.insert()`, documented inline at
that import; every other script's imports stay within its own new
directory. `tests/*.py` updated to add both `pipeline/` and `tools/` to
`sys.path`/its dynamic-import calls rather than rewriting every individual
`import X as Y` line.

Before this reorg, a full-repo audit confirmed the one genuinely
disconnected script (`reconstruct_multipage_klalim.py` — see the
Witness/reconstruction bullet below) and archived it; everything else
below was already live, just partly undocumented here until this pass
(see each bullet's own added-date).

**Prior correction, 2026-08-14** (kept for the lesson, not just the
history): this section used to be one long run-on bullet, and had drifted
from reality in three places nobody had caught — a stale "active root
script" claim for an already-archived file, an archived file listed as
active, and a live file missing from the list entirely. Restructured into
sub-bullets and re-verified against an actual `ls` at root, not against
the previous version of this file — the lesson (applied again in this
2026-08-16 pass): this document's own file-existence and file-location
claims are not automatically true and need the same checking as any other
claim.

- `pipeline/`, by role:
  - **Correction-data pipeline** (see "Single source of truth" above) —
    `build_klalim_demo_dataset.py`, `build_corrections_dataset.py`,
    `verify_corrections_vision.py`, `assemble_corrections_dataset.py`,
    `build_klal_page_regions.py`, run in that order by `rebuild_all.sh`
    (which calls each as `pipeline/<name>.py`). `orchestrator.py` and
    `chunker.py`, the two earlier OCR/VLM-extraction scripts this pipeline
    superseded, are both archived (`archive/scripts/`) — see "Pipeline
    shape" above for why.
  - **Live review tool** — `review_server.py`, `review_decisions.py`,
    `apply_reviewer_decisions.py` (added 2026-08-07, see "Human review
    decisions" above), and `audit_applied_decisions.py` (added 2026-08-14,
    see the same section) — not part of `rebuild_all.sh`, run separately
    with `python3 pipeline/review_server.py`. Serves `review_frontend/`
    (unmoved, at root) via its own `REPO`-relative path.
  - **Shared library modules, imported not run** (both added 2026-08-17,
    see "Shared library modules" below) — `vision_adjudication_common.py`
    and `corpus_io.py`.
- `tools/`, by role:
  - **Punctuation pass, Part 1 only** — `propose_punctuation_part1.py`
    and `apply_punctuation_decisions.py` (added 2026-08-10, see
    PROJECT-STATUS.md) are a parallel candidate→review→apply pipeline
    for corpus-wide punctuation: the propose script drafts `[.]`-marked
    sentence/clause-break insertions per klal via Gemini into
    `punctuation_candidates_part1.json` (its own sqlite cache,
    `punctuation_cache.db`, keyed on klal_id + clean_text + a prompt hash
    added 2026-08-16 so a later corpus edit OR a prompt-wording edit both
    invalidate stale proposals — the identical fix `verify_corrections_
    vision.py`'s cache already had); `review_server.py` surfaces every
    proposal as a clickable blue `·` marker in the text pane for
    accept/reject via the same `review_decisions.jsonl` audit trail
    (`punctuation_choice` decision type); `apply_punctuation_decisions.py`
    promotes accepted decisions into `part1.json`, mirroring
    `apply_reviewer_decisions.py`'s drift-detection/never-silently-mutate
    pattern (and importing it directly from `pipeline/` — the one
    cross-directory import in the reorg, see above). Like the
    correction-candidate scripts, not part of `rebuild_all.sh` — run
    manually. Secondary to the main correction pipeline (user directive
    2026-08-14).
  - **pytest gate** — `rebuild_all.sh`'s step 6/6 runs
    `tests/test_corpus_invariants.py` AND `tests/test_pipeline_logic.py`
    (added 2026-08-14) as a hard gate; see "Standing regression test
    suite" in PROJECT-STATUS.md for what they check and why
    (`requirements-dev.txt` pins the pytest version). The two are
    deliberately split by what they test, not by speed: the first checks
    the DATA a pipeline run produced (the corpus + the derived files the
    dashboard serves), the second the pure decision LOGIC that produces
    it, on synthetic inputs. The split exists because several correctness
    paths — candidate drift detection, the apply-script's re-apply guard,
    the vision cache key — are inert on today's real data and therefore
    invisible to any amount of corpus checking, while each of them was
    added after a real incident. `tests/test_review_server.py` (Playwright,
    live server) stays outside the gate and is run manually.
  - **Standalone validators, run manually** — `validate_klal_span_
    coverage.py`, `validate_catchword_continuity.py`, `validate_title_
    alphabetical_order.py`, and `check_klal_token_orphans.py` (added
    2026-08-06 — checks every Part-1 klal boundary for orphaned tokens
    never captured under any klal_id, or the same tokens captured under
    two; see PROJECT-STATUS.md "Klal 185-190, 196-197, 215-217 resolved")
    - not part of `rebuild_all.sh`, each needs the gitignored
    `docai_word_boxes`/scan-derived caches, so none of them can run on a
    fresh clone.
  - **`detect_ligature_corruption.py`** (added 2026-08-15 — re-runnable
    detector for the alef-lamed ligature extraction bug, see
    PROJECT-STATUS.md) needs only `part*.json`, so it CAN run on a fresh
    clone unlike the scan-dependent validators above — but is still not
    wired into `rebuild_all.sh` (its output needs human/context review
    before any correction, not zero-tolerance gating).
  - **`fetch_sefaria_reference_corpus.py`** / **`validate_lexicon_
    independent.py`** (added 2026-08-16 — downloads Shulchan Arukh +
    Talmud Bavli from Sefaria's public export as a genuinely independent
    Rabbinic Hebrew/Aramaic reference corpus, since `lexicon.txt` is
    derived from this project's own OCR and so cannot independently
    validate itself; see PROJECT-STATUS.md). Output cached in the
    gitignored `sefaria_reference_corpus/` — not `sefaria_export/`,
    which is this project's own OUTPUT for Sefaria (a different,
    pre-existing, differently-purposed gitignored directory; don't
    conflate the two). Needs network access on first run only (cached
    after); not wired into `rebuild_all.sh` for the same reason as
    `detect_ligature_corruption.py` above.
  - **`validate_part1_corpus_integrity.py`** (added 2026-08-07 — 6
    independent no-LLM sweeps over `part1.json` alone: gematria
    self-consistency, character/encoding sanity, a general foreign-
    character repertoire check added 2026-08-16 (see PROJECT-STATUS.md —
    the narrower Latin/Arabic/bracket check above missed a Greek `Π`
    homoglyph of its own named example), duplicated-phrase detection,
    self-reference directionality, full-corpus lexicon coverage) is also
    runnable standalone for its full output, but unlike the scan-dependent
    validators above, its checks 1-2b (zero known false positives as of
    2026-08-07/16, after fixing bugs in the script itself — see
    PROJECT-STATUS.md) are wired into `tests/test_corpus_invariants.py`
    as additional zero-tolerance gates in `rebuild_all.sh`'s step 6/6,
    since it needs only tracked files (no gitignored cache) and runs in
    under a second. Its checks 4 (self-reference directionality) and 5
    (lexicon coverage) are deliberately NOT gated — the script's own
    docstrings mark them not-viable/informational, not zero-tolerance.
  - **Abbreviation-expansion candidate pipeline** (added 2026-08-16, see
    PROJECT-STATUS.md — undocumented here until the 2026-08-16 correction,
    the same drift class the 2026-08-14 note above already warns about)
    — `extract_abbreviation_forms.py` (prints the canonical list of every
    gershayim/geresh-marked abbreviation form in Part 1, with per-klal
    attribution) and `propose_abbreviation_expansions.py` (categorizes
    each into `expand`/`stays`/`name`/`scholarly`/`numeral`/`artifact`/
    `unresolved`/`truncated` and drafts a candidate expansion for the
    `expand` category, cross-checking `sefaria_reference_corpus/
    word_freq.json` for single-clear-winner truncated-word completions).
    Both read-only, standalone, re-runnable; neither writes `part1.json`
    or `review_decisions.jsonl` — no review/apply stage exists yet, this
    is candidate generation only. Not wired into `rebuild_all.sh`.
  - **`review_lexicon_gaps.py`** (added 2026-08-16 — triages
    `validate_part1_corpus_integrity.py` check 5's raw "951 not-in-lexicon
    words" list against independent-corpus attestation, prefix-stripped
    morphology, and the known dropped-lamed shape, down to a short list of
    genuine candidates; see PROJECT-STATUS.md) is read-only and
    re-runnable like the validators above, but its output is recorded
    directly as `klal_flag` decisions (`reviewer: "ai-lexicon-full-
    review"`) rather than printed for separate action — the same
    propose→dashboard-flag pattern as the vision/lexicon cross-check
    work, not a new mechanism. Not wired into `rebuild_all.sh`.
  - **Witness/reconstruction code** (excluded from this project's own
    code-revalidation audits by standing scope decision, but genuinely
    live, not archived): `verify_reconstruction_witness.py` and
    `verify_witness_vision.py` produce and vision-triage `reconstruction_
    witness_queue.json`/`witness_vision_cache.db`, which `pipeline/
    review_server.py`'s witness API endpoints actively serve to the
    dashboard's Witness panel for the still-open ~411-item human review
    queue (klal 30/75/88) — see "NEXT STEPS" in PROJECT-STATUS.md.
    `reconstruct_multipage_klalim.py`, the script that originally
    reconstructed those three klalim's text into `part1.json`, did its
    one job (already applied, `--apply` run under explicit authorization
    2026-08-12) and was ARCHIVED 2026-08-16 (`archive/scripts/`) as part
    of the same pass that created `pipeline/`/`tools/` — it was already
    documented in `tests/test_corpus_invariants.py`'s own comments as
    "not part of `rebuild_all.sh` ... a deliberate one-off."
- Root also has a `tests/` directory (the pytest suite above) and
  `requirements-dev.txt` — every `.py` file that isn't in `pipeline/`,
  `tools/`, or `tests/` has been moved to `archive/scripts/`.
- `archive/scripts/`, `archive/data/`, `archive/docs/` — one-time,
  already-applied patch/find/debug scripts (hardcoded to specific klal
  numbers or line indices), their throwaway text/JSON dumps, and superseded
  planning/report docs (dated Jul–early Aug 2026, before `review.html` became
  the live verification artifact), moved out of the root for discoverability
  (`scripts`/`data` in Aug 2026, `docs` added 2026-08-06). Safe to reference
  for *how* a past fix was done or what was investigated, not meant to be
  rerun/treated as current.
- `aligned_klalim/`, `klalim_batches/` — tracked, versioned pipeline
  output at various early stages. **CORRECTED 2026-08-16**: this bullet
  used to also name a third directory, `processed_klalim/`, that does not
  exist anywhere in the repo — a claim nobody had caught. Root hygiene
  the same day found a real, separate `klalim/` (668 per-klal JSON files,
  bare/no-suffix name, likely what `processed_klalim/` actually meant to
  say) that was tracked but referenced by nothing live (no script, test,
  or doc pointed at it) — archived to `archive/data/klalim/`.
- `docai_word_boxes/`, `document_jsons_berlin/`, `klalim_docai/`,
  `llm_klal_starts/`, `sefaria_export/`, `vlm_extractions/`, `scratch/` (see
  the WARNING below) —
  gitignored regenerable caches/intermediates. Don't assume these exist on a
  fresh clone; they're rebuilt by re-running the extraction scripts against
  the source scans.
  **WARNING about `scratch/`:** it is gitignored but was NOT purely
  regenerable. Until 2026-08-11 it held 19 one-off scripts encoding
  non-reproducible logic, four of which PROJECT-STATUS.md cites as the method
  or evidence for corpus changes already applied. Those have been moved to the
  tracked `archive/scripts/`. What remains in `scratch/` (PNG crops, JSON
  dumps, a cache backup) genuinely is disposable — but never assume that of a
  `.py` file found there again; move it to `archive/scripts/` instead.
- `.gemini/rules/` — Gemini CLI's equivalent of this file; this project has
  been worked on from both Claude Code and Gemini CLI, so check both when
  looking for standing directives.

## Open items

See `PROJECT-STATUS.md` — the detailed, dated log of open items, confirmed
bugs, fixes applied, and in-progress investigations lives there now, not
here, so it can be updated freely without this file's durable rules drifting
along with it. Read it before touching corpus quality, and update it (not
just append — correct superseded claims) whenever a finding changes.

## Conventions observed

- Corrections are driven by direct LLM adjudication with **rendered UI
  verification** (open the HTML demo, visually confirm), not blind text diffs
  — see `.gemini/rules/rabbinic_ocr_adjudication.md` / `robust_ocr_processing.md`.
- Every cleanup pass targets **zero flagged items** in `lexicon.txt` validation
  before being considered done (see commit history: "100% clean validation
  pass" is the recurring bar).

## Lessons learned — binding, not optional reading

These are rules, not history. For the specific incidents that produced them,
see `PROJECT-STATUS.md`. Do not delete a lesson because its incident got
fixed — the rule still applies to the next incident.

1. **A verification tool that exists but isn't run on everything it applies
   to has not verified anything.** Running it on a sample, or only on items
   a different/narrower check already flagged, is not the same as running it.
   If full coverage is too expensive, say so explicitly and get a scope
   decision — never quietly narrow coverage and report the narrower result as
   if it were complete.
2. **A passing score is not the same as a checked result.** A numeric
   agreement/confidence threshold is a triage tool for where to look first,
   not a certificate of correctness. A high score can still hide a single
   wrong word. Look at what a "passing" result actually contains before
   moving on, especially anywhere close to the threshold.
3. **Never trust a derived/aggregate artifact as ground truth, no matter how
   long it's been treated as authoritative.** Re-derive from primary sources
   (the scan image, raw OCR, a validated lexicon) rather than trusting
   anything built by an earlier, unaudited pipeline stage — including this
   project's own prior outputs.
4. **Raw/source-adjacent data is not automatically correct just because it's
   closer to the scan than derived data.** OCR extraction itself can have
   real bugs (mislabeled files, swapped pages, wrong content). Verify with
   the most direct method available — e.g. rendering the exact source region
   a claim is based on and reading it directly — not just by checking that
   matching content exists somewhere.
5. **Fuzzy/subsequence text matching is not precise enough for exact-position
   claims.** It tolerates small shifts and will report a high similarity
   score for content that's merely nearby, not exactly there. Fine for
   coarse attribution or cropping with margin; wrong for "is this the exact
   right token/position." For exact-position questions, anchor on an exact
   match first and use fuzzy similarity only to disambiguate among exact
   candidates.
6. **Every matching/anchoring strategy has its own blind spot — know it
   before trusting silence as proof of correctness.** Exact-match anchors
   can collide with short/common values that recur for unrelated reasons.
   Fuzzy matches can lock onto coincidentally-similar content elsewhere.
   Cursor/position-based search can cascade failures if one bad match
   corrupts the position everything after it searches from. Understand the
   specific failure mode of a check before trusting what it doesn't flag.
7. **Fixing one root cause does not mean the symptoms it produced are now
   explained.** Multiple independent bugs can produce similar-looking
   symptoms. After a fix, re-verify the original finding against corrected
   data before assuming it's resolved — don't assume one explanation covers
   every instance that looked the same.
8. **A cheap, mechanical, no-LLM check can catch what expensive LLM-based
   checks miss entirely, and vice versa — run every independent check you
   have, don't rely on the most sophisticated one alone.** Structural/
   consistency rules (format, sequence, grouping invariants) are nearly free
   and catch a different class of error than semantic or visual review.
9. **Independent verification signals must agree before a fix is trusted.**
   Pixel-reading (vision) and linguistic-plausibility (semantic) checks fail
   in different ways — a misread crop can look pixel-plausible but be
   meaningless, and vice versa. Require at least two independent signals to
   agree, not just one confident-sounding one.
10. **Prompts bias results in specific, predictable directions — watch for
    the bias itself, not just its symptoms.** E.g. asking for "the shortest
    valid answer" systematically produces truncation, which then shows up as
    many false "disagreements." Fix the instruction, don't just tune a
    threshold around its side effect.
11. **A locally clean fix can still be a symptom of a larger unresolved
    problem.** If a broader/structural check flagged something upstream,
    don't stop investigating just because the first specific instance you
    looked at resolved cleanly.
12. **A cache key must cover everything that changes the correct answer, not
    just the expensive part.** Keying a decision cache on the crop image
    alone (not also the two readings being compared) meant a stale decision
    from an earlier comparison got silently reused for a different, current
    comparison on the same crop — see "Single source of truth" above. If a
    cache can be asked two different questions about the same cached object,
    the cache key must include which question was asked.
13. **A hand-maintained "derived" file is not actually derived — it's a
    second copy of the truth that happens to usually agree.** Any file whose
    content is fully computable from another file (e.g. a concatenation, a
    join, a filter) should be built by a script and regenerated, never edited
    in parallel by hand "to save time." Parallel hand-edits agree until the
    day someone forgets one of the two places — the failure is silent, not
    loud, so you won't notice until something downstream looks stale.
14. **Judging word ORDER in a cropped RTL image is a distinct failure mode
    from misreading a letter, and needs its own safeguard.** A tight crop
    around a disputed word pair can clip the anchor word that establishes
    which side is "first," and reading right-to-left off a clipped image
    silently inverts the answer — confirmed 2026-08-05, klal 34's title
    (`אין דן אדם...` vs. the correct `אין אדם דן...`): a narrow crop was
    read as confirming the wrong order, and re-cropping the *same way* after
    being directly contradicted reproduced the same risk. Any crop meant to
    establish order (not just letter identity) must keep an unambiguous
    anchor (a bold opening word, a klal marker) fully inside the frame with
    visible margin — never crop so tight that a word touches the edge. When
    your reading and another source directly disagree, don't re-run the same
    method closer — cross-check with a differently-sourced signal (raw token
    x-coordinates, a fresh independently-prompted model read) per lesson 9,
    the same way the klal-1 `ומדקמהד` case was ultimately resolved.
15. **A comparison pipeline that requires aligning two OCR sources produces
    silence, not a low score, exactly where the source OCR is too garbled to
    align — and silence is not evidence of correctness there.** Confirmed
    2026-08-05: every Part-1 klal with a low/untrusted alignment
    `match_ratio` in `part1_header_anchored_alignment.json` (34, 92, 129,
    172, 180, 182, 187, 190, 194, 197, 210, 216, 217) has **zero** entries in
    `corrections_part1.json` — not a low-confidence flag, no candidate was
    ever generated, because `build_corrections_dataset.py` can't align
    unrecognizable docai tokens to stored text in the first place. This is a
    different blind spot than lesson 1 (coverage gap) — the tool nominally
    ran, but structurally cannot produce output on the cases that need
    checking most. Treat a low/untrusted alignment `match_ratio` as its own
    mandatory-manual-review flag, independent of whatever the
    corrections/vision pipeline shows for that klal.
16. **Checking only the boundary between two "trusted" neighbors cannot
    detect content merged inside one of them.** Confirmed 2026-08-06: a
    check of whether klal N's "trusted" stored text already reached the
    token immediately before klal N+2's marker found "zero gap" for
    klal 180, 182, and 194 and concluded no room existed for them — wrong
    in all three cases. Each was really sitting, whole, inside its
    "trusted" neighbor's own `clean_text`, appended after that neighbor's
    real ending, behind a garbled second marker the boundary check never
    looked for because it never read the neighbor's *full* text, only its
    edges. A "trusted" flag on a klal says its *boundaries* were
    validated, not that its *interior* was searched for a second klal
    hiding inside it. Before concluding a klal_id has no content anywhere,
    read the full stored text of both neighbors for an embedded second
    marker and topic shift — do not infer absence from edge-adjacency
    alone. The direct-visual-page-render check (Lesson 14) is the
    reliable method here too: rendering the physical boundary and reading
    it caught the three wrong conclusions and confirmed the six real
    gaps at equal confidence, where token-position inference gave a
    50/50 record.
17. **A token-height threshold for detecting catchwords is a useful
    first-pass filter, not a sufficient check on its own.** Confirmed
    2026-08-06: the height-based catchword check (used repeatedly the
    night of the klal 92-165 shift-zone work) correctly flagged most
    catchwords, but wrongly cleared one as normal body text (klal 128's
    page 47/48 boundary), producing a real duplicated word in the stored
    text (`לאוקומי לאוקומי`) that stood until a corpus-wide
    duplicate-word sweep caught it. A direct render of the actual page
    showed the word sitting alone on its own short centered line - the
    standard catchword position - contradicting the height measurement.
    On any page-crossing reconstruction, treat a borderline or
    unexpected height reading as a reason to render and look, not as
    settled by the number alone.
18. **A cheap, corpus-wide text-pattern sweep (grep a literal string, a
    regex, a duplicate-word scan) can find in minutes what extensive
    klal-by-klal manual review missed for an entire project's history.**
    Confirmed 2026-08-06: a plain string search for the page-running-header
    text found contamination in 74 Part 2-3 klalim (17%) and one missed
    Part 1 instance, none of which any prior manual pass or automated
    check had caught, because no such sweep had ever been run as a
    matter of course - only individual klalim got checked, one at a
    time, when something else drew attention to them. Run this class of
    check routinely (after any batch of edits, not just when asked) -
    per Lesson 8, it catches a different class of error than
    vision/semantic review and costs almost nothing to run.
19. **Diagnosing a fix and describing it in writing is not the same as
    applying it — verify every "fixed"/"split"/"applied" claim against a
    diff of the actual data, not against how carefully it was written
    up.** Confirmed 2026-08-06: this document stated klal 181/182 had
    been "split, the identical shape as 179/180" — the diagnosis was
    correct but the code to apply it was never run, and the file sat
    byte-identical to its pre-fix state for the rest of the session
    despite being narrated as done. Found only because a later request
    to diff the whole session against its starting commit surfaced it.
    This is Lesson 1 ("a check that isn't run has not verified
    anything") applied to one's own output: a prose claim of "fixed" is
    itself unverified until checked against a real before/after diff.
