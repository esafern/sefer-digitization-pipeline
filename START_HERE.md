# Start Here

This is the main onboarding document for this repo. Part 1 is written for a
human contributor; Part 2 is written for an LLM instance (Claude Code,
Gemini CLI, or any other agent) working in this repo — its rules are
binding, not optional reading.

If you only came here from `README.md`, you've got the right file. If
you're an LLM that loaded `CLAUDE.md` automatically, that file is a short
redirect to here — read on.

## TL;DR

**The pipeline.** Document AI primary text extraction → secondary witness evaluation (VLM `VlmWitnessEngine`) → diff & crop disagreements → VLM Vision Adjudicator (`call_gemini_vision_adjudicate`) → human review in a local dashboard → persistent decision ledger (`review_decisions.jsonl`). Five build stages, orchestrated by `./rebuild_all.sh`, gated by pytest.

**The corpus.** `part1.json` / `part2.json` / `part3.json` are the **only** hand-edited source of truth, and they are never hand-edited directly — every change goes through the decision pipeline. Everything else that shows klal text is derived and must be regenerated.

**The four things that will bite you if you skip them:**

1. **Read `PROJECT-STATUS.md` before making any claim about corpus quality.**
   This file holds durable rules; that one holds the current dated truth.
2. **The Parts 2-3 gate is binding.** Building Parts 2–3 infrastructure is
   authorized; *applying* any `part2.json`/`part3.json` correction is not,
   until Part 1 is independently confirmed clean by an outside professional.
3. **Log every finding to `PROJECT-STATUS.md` yourself, immediately.** A bug
   mentioned only in chat is a dropped ball, and recovering it is not the
   user's job.
4. **Never fix one instance — sweep the corpus for the class.** Every bug in
   this project's history that was reported as one case turned out to be many
   (one unclearable flag was 325 across 104 klalim). See Part 2's "Never fix
   one instance" section; it is binding whether or not you fix the thing.

**Vocabulary that matters here.** A problem in the DATA is a "data issue" —
fixed through human review against the scan. A problem in the CODE is a
"bug" — fixed by changing code. They have different remedies; don't blur them.

**Before you hand-roll anything**, check `pipeline/corpus_io.py` (paths,
loaders, Hebrew helpers) and `pipeline/vision_adjudication_common.py`
(crop/cache/retry/client). A hand-maintained parallel copy has produced the
same bug class here more than once.

**Then read Part 2's 37 numbered lessons.** They are rules, not history. The
short version of most of them: a check that wasn't run has verified nothing, a
passing score is not a checked result, and no single confident signal is
enough.

---

# Part 1 — For humans

## What this is

A digitization pipeline for historical Hebrew/Rabbinic texts: OCR
extraction, LLM/vision-based cross-checking against the actual scan,
section-boundary verification, and a human-review dashboard for resolving
flagged disagreements — aimed at producing output ready to ingest into
Sefaria.

The pipeline is built to generalize beyond any one work — everything here
(DocAI extraction, marker/scan-linkage detection, boundary verification,
the diff-and-review machinery, the review dashboard) should be written so
it applies to other historical Hebrew texts, not hardcoded to one work's
specific shape where that can reasonably be avoided. Prefer parameterized,
documented, reusable scripts (the `pipeline/`+`tools/` shared-library
pattern below) over quick one-off scripts.

Its first, and so far only fully-built-out, application is **Yad Malachi**
(R. Malachi ben Jacob HaKohen, Livorno 1766–7), a foundational
halachic-methodology reference in three parts. **The digitized corpus is its
part one, *Klalei HaGemara*, complete: 667 *klalim*, scan pages 14-247.** The
other two parts (*Klalei HaPoskim*, pages 254-~295; *Klalei HaDinim*, pages
~296-331) are scanned but have never been extracted — corrected 2026-08-25, see
`PROJECT-STATUS.md`'s TL;DR. See `CASE-YAD-MALACHI.md` for the rationale (287
dead Sefaria citations currently point to this work).

### The scan: which edition, which file, and why not NLI

**Two editions, don't conflate them.** Livorno 1766-7 is the work's ORIGINAL
printing. The scan this pipeline actually OCRs, `berlin_square_corrected.pdf`,
is a LATER, SECOND printing, in Berlin, per its own title page (`נדפס ראשונה
בליוורנו... ועתה נדפס פעם שנית` — "first printed in Livorno... now printed a
second time," colophon `ברלין`, editor אפרים הערץ of Silesia). Square Hebrew
typeface throughout (not Rashi script) — matches the filename.

**Berlin printing date: Hebrew year תרי"ב = 1851/2 CE**, confirmed 2026-08-18
against the National Library of Israel's catalog record for this exact edition
(NLI system number `990011859020205171`,
<https://www.nli.org.il/en/books/NNL_ALEPH990011859020205171/NLI> — same
"printed a second time... by Efraim Hertz" edition note, same Berlin/
Zittenfeld imprint, same 337-page count as this repo's local PDF). The date
rests on two independent chronograms inside the book itself (the publisher's
introduction signing-date, and a separate Deuteronomy-verse chronogram used as
the formal creation-date), both encoding 612 — a primary-source confirmation,
not an inference. This supersedes an earlier "~1857/8" estimate inferred
secondhand from a *later* edition's title page, and separately resolves a
discrepancy flagged but never resolved in `PROJECT-STATUS-HISTORY.md` (a
Wikipedia summary implied ~1917, evidently a misconverted gematria). Full
research trail: `PROJECT-STATUS-HISTORY.md`, 2026-08-18.

**Provenance: this pipeline's PDFs stay Google Books-sourced — do not switch
them to an anonymous NLI download.** The original scan is publicly
downloadable at <https://www.google.com/books/edition/_/OdiHjxI3I0EC> —
confirmed 2026-08-18 (via an actual browser render; a plain HTML fetch first
misread it as a different edition entirely) to be this exact printing: same
`דפוס י. זיטטענפעלד` (Zittenfeld) publisher as this scan's own title page, and
Google's own bibliographic panel names its source as the National Library of
Israel. So the Google Books copy and the NLI record are the same underlying
digitization, re-hosted.

**Why NLI was validated and then deliberately not adopted.** The full 337-page
book was downloaded from the NLI record, the leaf-order fix below applied to
it, and correct reading order confirmed by direct content inspection (matching
folio numbers and catchwords, not just file existence) — the acquisition + fix
procedure genuinely works. It was rejected on image quality, checked directly
on the same physical page:

| Source | Resolution | Notes |
|---|---|---|
| This repo's local PDF (Google Books) | **3440×5312** (~18.3 MP) | PNG, lossless |
| NLI, `JPEG\ZIP` + Maximal (best anonymous tier) | 1745×2658 (~4.6 MP) | ~4x fewer pixels, lossy |
| NLI, PDF + Medium (only anonymous PDF tier) | 873×1329 | ~16x fewer pixels |

NLI's "Maximal (100%)" is greyed out under `File format: PDF` (gated behind an
NLI account this project doesn't have) but **is** selectable under `File
format: JPEG\ZIP`, anonymously. Even at its best anonymous tier, NLI is
nowhere near this pipeline's OCR/vision-adjudication quality bar. An NLI
account might unlock something higher (untested) — until confirmed otherwise,
treat 1745×2658 as the ceiling. NLI's site is still the right pointer to give
someone else acquiring this text for the first time (per
`HOW-THE-PIPELINE-WORKS.md`'s "Preparing the text for Sefaria" section, sourcing
from NLI sidesteps Google Books' terms of use for redistribution) — but only
if *they* use an NLI account to get full resolution.

**NLI's PDF is 336 pages, not 337 — a constant 1-page offset, not a different
scan.** This pipeline's local PDFs came from a Google Books scan whose page 0
is a "Digitized by Google" disclaimer page that NLI's own digitization doesn't
have. Confirmed by direct comparison: NLI page *i* = the Google-sourced PDF's
page *i + 1* for every page checked, including at the transposed-leaf region.
**Every page-indexed cache in this pipeline** (`docai_word_boxes/`,
`images/pdf_pages/`, `gematria_trace_part1.json`,
`part1_header_anchored_alignment.json`) **is indexed against the
Google-sourced 337-page numbering** — the offset is documented only in case a
future, actually-equivalent-quality NLI source is ever adopted; not acted on
now.

### The transposed leaves — a defect in the source binding, not an extraction bug

Two physical leaves were bound out of order; true reading order is printed
page 36 → 38 → 37 → 39. Found via a catchword-chain sweep (each page's closing
catchword should match the next page's opening word) and confirmed by
rendering both pages directly.

On the Google-sourced 337-page numbering (this repo's local PDFs) that's
0-indexed leaf 37 moving to position 36; on an NLI-sourced 336-page PDF, the
same physical leaves are at 0-indexed 36 moving to position 35. Fixed with
`fitz.move_page` (page count unchanged either way).
**`berlin_square_corrected.pdf` is the only PDF that should ever be used as
the pipeline's source**; `berlin_square_original_transposed.pdf` (pre-fix) is
kept only as a diffable reference, never fed to the pipeline. Every
page-indexed cache built before the fix moved in lockstep:
`docai_word_boxes/page_37.json` ⇄ `page_38.json`,
`images/pdf_pages/page_37.png` ⇄ `page_38.png`, and klalim 76-84's page
attribution in
`gematria_trace_part1.json`/`part1_header_anchored_alignment.json` remapped
page 37 → 38. `part1.json`'s own `page` field was deliberately left untouched
(already stale/dead metadata for most of Part 1).

**If you ever need to redo this** — e.g. starting from a completely fresh scan
download — use `tools/fix_transposed_leaf.py`, a small reusable CLI built
2026-08-18 and verified two ways: byte-for-byte against the local
Google-sourced PDF, and by direct content inspection against a fresh NLI
download. **Use the indices matching whichever source you actually pulled
from** — they differ by 1:

```bash
# Google-sourced PDF (this repo's local files use this numbering):
python3 tools/fix_transposed_leaf.py --pdf berlin_square_original_transposed.pdf \
    --from-index 37 --to-index 36 --output berlin_square_corrected.pdf

# NLI-sourced PDF (one page earlier throughout - verified 2026-08-18):
python3 tools/fix_transposed_leaf.py --pdf berlin_square_original_transposed.pdf \
    --from-index 36 --to-index 35 --output berlin_square_corrected.pdf
```

It only fixes the PDF's own physical page order — it does not know about
`docai_word_boxes/`, `images/pdf_pages/`, or the alignment/trace files, so any
of those built from a differently-ordered (or differently-sourced) PDF still
need the manual remap described above. This is a generic leaf-reordering tool,
not Yad-Malachi-specific, in keeping with this project's generalization goal.


## Success criteria (in priority order)

1. **Absolute fidelity to the author's words.** The transcript must match
   the source scans exactly — no paraphrase, no silent normalization, no
   "improving" the text. Every correction must be traceable to a real
   disagreement (routinely DocAI-vs-stored-text; VLM and the untracked
   second physical scan are secondary cross-check signals used manually,
   not systematic legs of the automated pipeline) resolved by looking at
   the actual scan, not inferred.
2. **Accurate klal chunking.** Each of the 667 klalim must be correctly
   formed and delimited as its own unit, matching Sefaria's structural
   conventions — wrong boundaries (a klal split, merged, or mis-numbered)
   are as serious a defect as a wrong word.
3. **Sefaria-ready output.** The end deliverable must be usable as-is
   inside Sefaria's library in every respect (structure, encoding,
   section/klal numbering, citation-linkability) — not merely "clean
   text," but ready to ingest.

Any pipeline change, correction pass, or shortcut should be weighed against
these three before anything else (speed, script cleanliness, cost).

## Current status

See `PROJECT-STATUS.md` — the detailed, dated log of open items, confirmed
bugs, fixes applied, and in-progress investigations. `PROJECT-STATUS-HISTORY.md`
holds the older, closed-out history. This file (`START_HERE.md`) holds
durable rules and architecture; `PROJECT-STATUS.md` holds the current,
specific, dated truth. Neither substitutes for the other.

`part1.json` (klalim 1-222) has the full pipeline built out. `part2.json` /
`part3.json` (klalim 223-444 / 445-667 — the rest of the same *Klalei
HaGemara*, on pages 77-247) are gated — see Part 2's "Parts 2-3 gate" section
below for the binding rule and its rationale. **"Parts 2-3" throughout this
repo means those two FILES, not the work's second and third parts**; the
labelling predates the 2026-08-25 correction above and the gate itself is
unaffected by it.

## How the pipeline works

1. **Extraction** — Google Document AI OCR produces
   `docai_word_boxes/page_N.json` (raw OCR tokens, one file per scan page,
   gitignored). VLM extraction (`vlm_extractions/`, sparse — not a
   full-corpus pass) is a secondary, opportunistic cross-check signal used
   manually during specific investigations, not a systematic pipeline leg.
2. **Correction-candidate generation** — `pipeline/build_corrections_dataset.py`
   diffs DocAI's fresh OCR tokens against whatever is CURRENTLY STORED in
   `part1.json` (via `klalim_demo_dataset.json`), producing
   `corrections_candidates_part1.json`.
3. **Vision adjudication** — `pipeline/verify_corrections_vision.py` crops
   each disputed token's bounding box from the PDF, sends it to Gemini
   (`google.genai`) for a vision-based OCR disagreement call, and caches
   every decision in `adjudication_cache.db` (keyed on the full
   comparison — crop hash + both readings — not just the crop; see Part
   2's cache-keying rule). Requires a Gemini API key in the environment
   (not committed — check `credentials.json`, gitignored).
4. **Assembly** — outputs converge into `part1.json` / `part2.json` /
   `part3.json` (three file chunks of ONE section — klalim 1-222, 223-444,
   445-667 of *Klalei HaGemara*, the work's part one; NOT one file per Yad
   Malachi part, see the scan section above — THE corpus, hand-edited only
   through the decision pipeline in Part 2, never directly),
   `aligned_klalim/` / `klalim_batches/` (per-klal JSON at earlier
   pipeline stages), and `lexicon.txt` (~19k unique validated Rabbinic
   Hebrew words used as a spell-check dictionary).
5. **Review** — `pipeline/review_server.py` + `review_frontend/` (run with
   `python3 pipeline/review_server.py`, open `http://127.0.0.1:8420/`) is
   the live human-review dashboard: visually verify a correction against
   the actual scan crop, and record a candidate-override or klal-flag
   decision. See Part 2's "Human review decisions" section for how
   recording a decision differs from applying it to the corpus.

For exactly what each data file contains, see `PIPELINE-DATA-REFERENCE.md`.

## Directory layout

- **`pipeline/`** — the scripts that make up the actual running system:
  the 5 `rebuild_all.sh`-orchestrated correction-data stages
  (`build_klalim_demo_dataset.py`, `build_corrections_dataset.py`,
  `verify_corrections_vision.py`, `assemble_corrections_dataset.py`,
  `build_klal_page_regions.py`), the marker/scan-linkage trace builder run
  separately from that chain and covering all three parts
  (`build_gematria_trace.py`), the live review tool (`review_server.py`,
  `review_decisions.py`, `apply_reviewer_decisions.py`,
  `audit_applied_decisions.py`), and two shared library modules that are
  imported, never run directly, by scripts in both `pipeline/` and
  `tools/`: `vision_adjudication_common.py` (crop/cache/JSON-recovery/
  retry/client machinery for every Gemini-calling script) and
  `corpus_io.py` (repo paths, corpus/derived-artifact loading, DocAI
  page-token loading, alignment/gematria-trace readers, Hebrew-text
  helpers). Both are imported via
  `sys.path.insert(0, os.path.join(REPO, "pipeline"))`.
- **`tools/`** — everything run manually/standalone. None of it is part of
  `rebuild_all.sh`. Grouped by what it's for:
  - **Validators** (assert an invariant, exit non-zero on violation):
    `validate_klal_span_coverage.py`, `validate_catchword_continuity.py`,
    `validate_title_alphabetical_order.py`,
    `validate_part1_corpus_integrity.py`, `validate_lexicon_independent.py`,
    `check_klal_token_orphans.py`, `check_next_marker_and_title.py`.
  - **Corpus-wide defect sweeps** (cheap, mechanical, no LLM — Lesson 8/18:
    run these routinely after any batch of edits):
    `detect_ligature_corruption.py`, `detect_real_word_substitution.py`,
    `detect_cross_klal_errors.py`, `detect_insertion_deletion.py`,
    `detect_repeated_words.py`, `detect_split_merge.py`.
  - **Lexicon / abbreviation work**: `extract_abbreviation_forms.py`,
    `propose_abbreviation_expansions.py`, `review_lexicon_gaps.py`,
    `build_part1_freq.py`, and the reference-corpus fetcher
    `fetch_sefaria_reference_corpus.py`.
  - **Punctuation pass**: `propose_punctuation_part1.py`,
    `apply_punctuation_decisions.py`.
  - **Witness / reconstruction** (the DocAI-vs-Tesseract second opinion on
    page-crossing klalim): `verify_reconstruction_witness.py`,
    `verify_witness_vision.py`, `verify_flagged_candidates_vision.py`,
    `patch_witness_word_indices.py`.
  - **Export**: `export_corpus.py` — writes the reviewed corpus as plain
    text, ALTO XML v4, PAGE XML 2019, or TEI P5, applying all current human
    decisions in memory exactly as `apply_reviewer_decisions.py` would,
    without touching `part1.json`. The archival-standards output that makes
    the corpus ingestible by institutional tooling.
  - **Source acquisition and setup**: `extract_docai_pages.py` (DocAI
    extraction — needs a GCP service-account key; promoted 2026-08-18 from
    `archive/scripts/extend_docai_ocr.py`), `fix_transposed_leaf.py` (the
    leaf-order fix, see the scan section above), `verify_local_setup.py`
    (proves a fresh migration actually landed — see `SETUP.md`).
- **`tests/`** — the pytest suite. Counts re-measured 2026-08-31 by collecting
  each file, not by grepping `def test_` — see Lesson 37 for why those two
  numbers are not the same thing. `rebuild_all.sh`'s step 6/6 runs
  `test_corpus_invariants.py` (46 tests — checks the DATA a pipeline run
  produced) and `test_pipeline_logic.py` (274 tests — checks the pure decision
  LOGIC on synthetic inputs) as a hard gate, 320 together.
  `test_review_server.py` (44 Playwright tests, live server) and
  `test_witness_engine.py` (5 tests) stay outside the gate, run manually.
  369 in total. One of the gated invariants,
  `test_no_test_file_defines_the_same_test_name_twice`, exists to keep the
  declared and collected counts equal — see Lesson 37.
- Data files, caches, `rebuild_all.sh`, `review_frontend/`, and every
  `.md`/`.html` doc live at root.
- **This repo has no `archive/` directory.** The original local
  development copy keeps one (`archive/scripts/`, `archive/data/`,
  `archive/docs/` — one-time, already-applied patch/find/debug scripts and
  superseded planning/report docs), but it's deliberately excluded from
  this public repo — not pushed, not tracked here. `DOCS-HISTORY.md` at
  root is the one piece of that archival material kept public: this
  document's own reorganization/correction history.
- `docai_word_boxes/`, `document_jsons_berlin/`, `klalim_docai/`,
  `llm_klal_starts/`, `sefaria_export/`, `vlm_extractions/`,
  `images/pdf_pages/`, `scratch/`, `sefaria_reference_corpus/` — gitignored
  caches/intermediates, not present on a fresh clone. "Regenerable" is
  aspirational for some of these, not a guarantee — `images/pdf_pages/`
  (the review dashboard's scan-page images) has no live rendering script at
  all (confirmed 2026-08-18, after its absence broke the dashboard's scan
  pane on a fresh migration); it must be migrated as a pre-built cache, the
  same as the others with no generator. See `SETUP.md` for how to get them,
  and `tools/verify_local_setup.py` to confirm they actually landed.
- `.gemini/rules/` — Gemini CLI's equivalent of Part 2 below; this project
  has been worked on from both Claude Code and Gemini CLI, so check both
  when looking for standing directives.

## Commands

All of these assume the venv is active (automatic if you're using direnv —
see `SETUP.md`; otherwise `source venv/bin/activate` first).

**Start the review dashboard** (the live human-review tool — see "How the
pipeline works" above). **Runs in the foreground and blocks the shell it's
started in** — background it unless you want a terminal permanently tied up:

```bash
python3 pipeline/review_server.py &     # backgrounded - shell stays free
```

Open <http://127.0.0.1:8420/>. To stop it later: `lsof -i :8420` to find the
PID, then `kill <PID>` (also the first thing to check if it fails to bind —
something may already be listening on that port). Running it plain in the
foreground (no `&`) is fine too if you're giving it its own terminal tab on
purpose.

**Run the test suite**:

```bash
pytest tests/ -q
```

**Rebuild the correction-data pipeline** (all 5 stages — see "Single source
of truth for corpus text" in Part 2) after any edit to a `part*.json` file:

```bash
./rebuild_all.sh              # full run, including live Gemini vision calls
./rebuild_all.sh --skip-vision  # skip the Gemini re-verification step, for fast iteration
```

**Record a review decision, then promote it into the corpus** — two
separate, deliberate steps (see "Human review decisions" in Part 2):
recording happens by clicking in the dashboard itself; promoting is:

```bash
python3 pipeline/apply_reviewer_decisions.py
python3 pipeline/audit_applied_decisions.py   # read-only check: did every applied decision actually land?
```

**Standalone validators and one-off tools** (`tools/`, none part of
`rebuild_all.sh`, run manually) — see "Directory layout" above for what
each one checks; a few of the most generally useful:

```bash
python3 tools/validate_part1_corpus_integrity.py   # needs only tracked files, runs on a fresh clone
python3 tools/check_klal_token_orphans.py          # needs docai_word_boxes/ (gitignored, migrated separately)
python3 tools/detect_ligature_corruption.py        # needs only part*.json
python3 tools/verify_local_setup.py                # after migrating to a new machine: proves everything not in git actually landed
```

## Where to find things

- `SETUP.md` — environment setup, and which files aren't in the public
  repo and how to get them.
- `PROJECT-STATUS.md` — current, dated state.
- `PROJECT-STATUS-HISTORY.md` — older, closed-out history.
- `PIPELINE-DATA-REFERENCE.md` — what each data file contains, field by
  field.
- `CASE-YAD-MALACHI.md` — the case for the project (short; the argument only).
- `HOW-THE-PIPELINE-WORKS.md` — its companion: method, measurements, state, costs.
- `CORPUS-COMPARISON.md` — the citation survey behind that case's demand
  figures.
- `COMPETITIVE-LANDSCAPE.md` — the other Hebrew digitization platforms, what
  to borrow from them, and what is genuinely unique here.
- `VERIFIED-AGAINST-THE-INK.html` — the outward-facing evidence showcase.
- `DOCS-HISTORY.md` — this document's own history.

---

# Part 2 — For LLM instances

These are binding operational rules, not suggestions. If you're working in
this repo as an LLM agent, follow them exactly.

## Session start, every time, no exceptions

- **Read `PROJECT-STATUS.md` first.** Part 1 above holds durable rules and
  architecture; `PROJECT-STATUS.md` holds the current, specific, dated
  truth — what's fixed, what's still broken, what was investigated and
  why. Do not report on, fix, or make claims about corpus quality without
  having read it first.
- **Start the review dashboard** (`python3 pipeline/review_server.py`,
  backgrounded) — check `lsof -i :8420` first and skip only if it's
  already running. It's the live human-review tool; the user works in it
  throughout a session and shouldn't have to ask for it each time.
- **Auto-restart review server on any frontend or server change.** Whenever modifying
  `pipeline/review_server.py` or any file in `review_frontend/`, immediately restart the background
  server process (`kill <PID>` + restart `python3 pipeline/review_server.py`) without asking.
- **Mandatory incremental disk flushing on all scripts.** All batch-processing, VLM, OCR, and API scripts
  MUST flush their output to disk item-by-item (`open(..., "a")`, `f.flush()`, `conn.commit()`). Never buffer
  results in memory to write at the end — cloud API failures, 429 quota exhaustion, and 503 errors will cause data loss.
- **Close open items before proposing new ones.** If `PROJECT-STATUS.md`'s
  Open Items section lists unresolved blockers, do not end a turn by
  offering to expand scope ("want me to also check X," "should I dig into
  Y next") — propose a plan to close the existing open items first, or ask
  which to prioritize.

## Parts 2-3 gate

**Parts 2-3 are out of scope until Part 1 is clean AND an outside
professional has independently confirmed the produced text is clean — not
just this pipeline's own self-assessment.** User directive, 2026-08-10,
restated explicitly to not be revisited until then: do not propose, scope,
or start Parts 2-3 work — including "just the easy mechanical parts" —
before both conditions hold. Rationale, in the user's own words: "if part 1
is bad the rest won't magically be better." This is not merely caution —
see `PROJECT-STATUS-HISTORY.md` 2026-08-10 "methodology audit" for a
concrete, already-confirmed reason the assumption "fix it once on Part 1,
it generalizes" doesn't hold: the page-furniture contamination bug hit Part
1 at ~1 instance but hit Parts 2-3 at 74/445 klalim (~17%) — same bug
class, same detection method, a much higher rate nobody has explained.
Parts 2-3's own scan data can and does fail differently and worse than Part
1's; a clean Part 1 pipeline is not evidence Parts 2-3 will come out clean
by the same process, let alone without its own scan-linkage/vision-
verification infrastructure ever having been built or run there at all.

**PARTIALLY SUPERSEDED 2026-08-17, by the same user, explicitly and
knowingly** ("this is my directive so I can decide"): the "do not propose,
scope, or start" language above is lifted specifically for building the
Parts 2-3 scan-linkage/verification INFRASTRUCTURE itself (DocAI extraction
over their page range, marker/trace-building, klal-boundary verification) —
not for finalizing or applying Parts 2-3 corrections. The rationale above
was restated in full to the user before this decision, not skipped past;
the user's own read: the code is meaningfully better than it was two weeks
ago and they want to see, concretely, whether it holds up on Parts 2-3
rather than defer that question further. Actually promoting any Parts 2-3
`part*.json` edit still needs its own explicit go-ahead, the same as every
correction this pipeline has ever applied — building the infrastructure and
deciding to trust/apply what it finds are still two separate, deliberate
steps (same principle as "Human review decisions" below). The original
rationale (page-furniture 17% disparity, no infrastructure ever run there)
is not wrong and is not deleted — it's the reason a dedicated klal-boundary
verification pass is a required part of this work, not an optional
nice-to-have, see `PROJECT-STATUS.md` for the live plan.

## Never fix one instance — sweep the corpus for the class

**Whenever you find and fix an issue, you MUST review the entire corpus for
other instances of the same failure class, in the same turn.** A bug you found
by looking at one klal is almost never confined to that klal; it is confined to
where you happened to look. Finding it is evidence about your sampling, not
about its extent.

**If you fix it on the spot, sweep anyway** — the fix is not done until you have
measured how many instances existed and confirmed the count is now zero. Report
the number, not just the fix.

**If you do NOT fix it, sweep anyway**, and document the other instances
*together with* the open issue in `PROJECT-STATUS.md`, so the next person
inherits the true scope rather than the one example. An open issue recorded as
"klal 91 has X" when 104 klalim have X is a worse record than no entry at all,
because it looks handled.

This is not a counsel of thoroughness — it is a correction for a specific,
repeated failure in this project's history. Every one of these was found as a
single instance and turned out to be a class:

| found as | actual extent |
|---|---|
| klal 9/10 region-box overlap | 316 of 667 klalim |
| klal 91's two disputes not highlighted | 5 more collisions, and the scan pane repeating the same defect independently |
| klal 91's unclearable revisit flag | **325 open flags across 104 klalim, every one unclearable** |
| klal 663's wrong scan page | `klal_page_regions.json` never built for Parts 2-3 at all |
| one `marker_not_found_in_window` | 100% correlation with 13 region overlaps |

The sweep is usually cheap — a loop over `api_klal()` for all 222 klalim runs in
seconds — and it is the difference between fixing a symptom and closing a defect.
Where a sweep is genuinely expensive, say so explicitly and get a scope decision
(Lesson 1); never quietly fix the one instance and move on.

## Log every finding immediately

**Log every finding to `PROJECT-STATUS.md` yourself, immediately, without
being asked.** Finding a bug and only mentioning it in chat is not done —
if the user has to go back through the conversation to recover something
you found so it isn't lost, that is a dropped ball, and recovering dropped
balls is not the user's job. The moment you confirm a real issue (a bug, a
gap, a wrong claim in a doc, a script fix, a new script, a job left
running), write it into `PROJECT-STATUS.md` before moving to the next
thing — not batched at the end of a long turn, not only when directly
asked to "update the status file." This applies to your own tooling/script
fixes too (cache bugs, dead models, UI fixes), not just corpus-content
findings.

## Terminology

**An issue with the DATA is a "data issue," not a "bug." An issue with the
CODE is a "bug."** These are two different failure classes with two
different remedies — a data issue (e.g. a dropped ligature corruption,
page-furniture contamination, a mis-transcribed word) gets fixed through
the human-review decision pipeline against the actual scan, never a direct
hand-edit; a bug (e.g. a cache key missing a component, a test scoped to
the wrong fixture, a script's docstring overclaiming its own coverage)
gets fixed by changing code. Calling a data issue a "bug" blurs which
remedy applies and risks someone reaching for a code fix (or a blind
find-replace across the corpus) for something that needs scan verification
instead. Use the precise term in findings, commit messages, and
`PROJECT-STATUS.md` entries.

## Single source of truth for corpus text — read before editing any text file

**`part1.json` / `part2.json` / `part3.json` are the only hand-edited
source of truth for klal text.** Every other JSON/HTML artifact that shows
or uses klal text is *derived* from them and must be regenerated, never
hand-edited in parallel:

- `klalim_demo_dataset.json` = `part1.json` + `part2.json` + `part3.json`
  concatenated, nothing else. Regenerate with `build_klalim_demo_dataset.py`.
- `corrections_candidates_part1.json` → `corrections_verified_part1.json`
  → `corrections_part1.json` → `review_server.py`'s flag overlay is a
  pipeline, each stage derived from the one before it and from
  `klalim_demo_dataset.json`.
- `klal_page_regions.json` (per-klal scan bounding box) also derives from
  the same docai-token alignment.

**After any edit to a `part*.json` file, run `./rebuild_all.sh`** — this
regenerates every derived file listed above. `review_server.py` reads its
source files fresh off disk on every request (no embedded/cached data, no
restart needed), but it still needs those files to actually be current —
running the rebuild is what keeps them that way. Don't hand-run individual
stages and try to remember which ones are now stale.

`./rebuild_all.sh --skip-vision` skips only the Gemini re-verification
step, for fast iteration when you don't need fresh flag classifications
yet.

## Human review decisions — a separate, protected layer from the rebuild pipeline

`review_server.py` lets a reviewer override which candidate reading is
correct for a flagged word, or flag an entire klal for revisiting with a
note. Every such decision is appended (never overwritten or deleted) to
`review_decisions.jsonl` via `review_decisions.py` — this file is
**deliberately tracked in git and outside the corpus-build pipeline**, so
no `rebuild_all.sh` run can ever clobber a human decision. A decision
recorded in the UI does **not** touch `part1.json` by itself —
`apply_reviewer_decisions.py` is the separate, manually-run script that
promotes accepted decisions into the corpus text, with its own drift
detection and one-insert/delete-per-klal-per-run safety limit. Recording a
decision and applying it to the corpus are always two distinct, deliberate
steps.

`audit_applied_decisions.py` is a read-only, standalone check on that
boundary from the other direction: for every decision the log claims was
applied, does `part1.json` still actually reflect it? Not part of
`rebuild_all.sh`, run manually.

### The vision-adjudication cache must be keyed on the full comparison, not just the crop

`adjudication_cache.db` caches Gemini's decision for "does this crop show
reading A or reading B" so repeat runs don't re-spend API calls. **The
cache key must include which two readings were being compared (crop_hash +
word_a + word_b), not the crop image alone.** A crop-hash-only cache is a
real bug, not a hardening opportunity: the same bbox gets re-cropped across
sessions to answer different comparisons as `clean_text` changes (a fix,
then later a revert), and a crop-only cache silently returns a stale
decision for the *current* comparison. `verify_corrections_vision.py`'s
`corrections_cache` table does this correctly; if you add another
vision-caching script, key it the same way.

## Shared library modules — check these before hand-rolling a loader, a cache, or a client

Two modules in `pipeline/` are libraries, not entry points — imported by
scripts in **both** `pipeline/` and `tools/`:

- **`vision_adjudication_common.py`** — crop/cache/JSON-recovery/retry/
  client machinery for every Gemini-calling script. (Always uses
  `gemini-3.6-flash` / `gemini-3.5-flash`; never call `gemini-2.x`, which is
  permanently unavailable / 404).
- **`corpus_io.py`** — repo paths, corpus and derived-artifact loading
  (`load_klalim`/`load_part1*`/`save_part1`/`load_json`), DocAI
  page-token loading (`load_docai_page`, `DocaiPageCache`), the alignment
  and gematria-trace readers, `clean_word`/`hebrew_letters_only`, and
  `PART1_MAX_KLAL`.

**The standing rule: before writing a new `json.load(open(...))` for a
corpus/derived file, a new `docai_word_boxes/page_N.json` read, a new
Gemini client, a new sqlite decision cache, or a new copy of
`PART1_MAX_KLAL` or a Hebrew-letter set — use the shared module.** If what
you need genuinely differs, add a parameter with a comment saying what real
difference it encodes, rather than a private copy.

Why this is a rule and not a preference: the identical bug class has been
found in a hand-maintained copy multiple separate times in this project —
a missing cache-key component, a missing request timeout — and in every
case the fix already existed in a sibling file, which never got it. A
hand-maintained parallel copy is a second copy of the truth that happens to
usually agree — see Lesson 13 below.

## Conventions observed

- Corrections are driven by direct LLM adjudication with **rendered UI
  verification** (open the review dashboard, visually confirm), not blind
  text diffs — see `.gemini/rules/rabbinic_ocr_adjudication.md` /
  `robust_ocr_processing.md`.
- Every cleanup pass targets **zero flagged items** in `lexicon.txt`
  validation before being considered done.

## Lessons learned — binding, not optional reading

These are rules, not history. For the specific incidents that produced
them, see `PROJECT-STATUS.md` / `PROJECT-STATUS-HISTORY.md`. Do not delete
a lesson because its incident got fixed — the rule still applies to the
next incident.

1. **A verification tool that exists but isn't run on everything it
   applies to has not verified anything.** Running it on a sample, or only
   on items a different/narrower check already flagged, is not the same as
   running it. If full coverage is too expensive, say so explicitly and
   get a scope decision — never quietly narrow coverage and report the
   narrower result as if it were complete.
2. **A passing score is not the same as a checked result.** A numeric
   agreement/confidence threshold is a triage tool for where to look
   first, not a certificate of correctness. A high score can still hide a
   single wrong word. Look at what a "passing" result actually contains
   before moving on, especially anywhere close to the threshold.
3. **Never trust a derived/aggregate artifact as ground truth, no matter
   how long it's been treated as authoritative.** Re-derive from primary
   sources (the scan image, raw OCR, a validated lexicon) rather than
   trusting anything built by an earlier, unaudited pipeline stage —
   including this project's own prior outputs.
4. **Raw/source-adjacent data is not automatically correct just because
   it's closer to the scan than derived data.** OCR extraction itself can
   have real bugs (mislabeled files, swapped pages, wrong content). Verify
   with the most direct method available — e.g. rendering the exact source
   region a claim is based on and reading it directly — not just by
   checking that matching content exists somewhere.
5. **Fuzzy/subsequence text matching is not precise enough for
   exact-position claims.** It tolerates small shifts and will report a
   high similarity score for content that's merely nearby, not exactly
   there. Fine for coarse attribution or cropping with margin; wrong for
   "is this the exact right token/position." For exact-position questions,
   anchor on an exact match first and use fuzzy similarity only to
   disambiguate among exact candidates.
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
   data before assuming it's resolved — don't assume one explanation
   covers every instance that looked the same.
8. **A cheap, mechanical, no-LLM check can catch what expensive LLM-based
   checks miss entirely, and vice versa — run every independent check you
   have, don't rely on the most sophisticated one alone.**
   Structural/consistency rules (format, sequence, grouping invariants)
   are nearly free and catch a different class of error than semantic or
   visual review.
9. **Independent verification signals must agree before a fix is
   trusted.** Pixel-reading (vision) and linguistic-plausibility (semantic)
   checks fail in different ways — a misread crop can look pixel-plausible
   but be meaningless, and vice versa. Require at least two independent
   signals to agree, not just one confident-sounding one.
10. **Prompts bias results in specific, predictable directions — watch for
    the bias itself, not just its symptoms.** E.g. asking for "the
    shortest valid answer" systematically produces truncation, which then
    shows up as many false "disagreements." Fix the instruction, don't
    just tune a threshold around its side effect.
11. **A locally clean fix can still be a symptom of a larger unresolved
    problem.** If a broader/structural check flagged something upstream,
    don't stop investigating just because the first specific instance you
    looked at resolved cleanly.
12. **A cache key must cover everything that changes the correct answer,
    not just the expensive part.** Keying a decision cache on the crop
    image alone (not also the two readings being compared) meant a stale
    decision from an earlier comparison got silently reused for a
    different, current comparison on the same crop. If a cache can be
    asked two different questions about the same cached object, the cache
    key must include which question was asked.
13. **A hand-maintained "derived" file is not actually derived — it's a
    second copy of the truth that happens to usually agree.** Any file
    whose content is fully computable from another file (e.g. a
    concatenation, a join, a filter) should be built by a script and
    regenerated, never edited in parallel by hand "to save time." Parallel
    hand-edits agree until the day someone forgets one of the two places —
    the failure is silent, not loud, so you won't notice until something
    downstream looks stale.
14. **Judging word ORDER in a cropped RTL image is a distinct failure mode
    from misreading a letter, and needs its own safeguard.** A tight crop
    around a disputed word pair can clip the anchor word that establishes
    which side is "first," and reading right-to-left off a clipped image
    silently inverts the answer. Any crop meant to establish order (not
    just letter identity) must keep an unambiguous anchor (a bold opening
    word, a klal marker) fully inside the frame with visible margin —
    never crop so tight that a word touches the edge. When your reading
    and another source directly disagree, don't re-run the same method
    closer — cross-check with a differently-sourced signal (raw token
    x-coordinates, a fresh independently-prompted model read) per lesson
    9.
15. **A comparison pipeline that requires aligning two OCR sources
    produces silence, not a low score, exactly where the source OCR is too
    garbled to align — and silence is not evidence of correctness there.**
    Treat a low/untrusted alignment `match_ratio` as its own
    mandatory-manual-review flag, independent of whatever the
    corrections/vision pipeline shows for that klal. This is a different
    blind spot than lesson 1 (coverage gap) — the tool nominally ran, but
    structurally cannot produce output on the cases that need checking
    most.
16. **Checking only the boundary between two "trusted" neighbors cannot
    detect content merged inside one of them.** A "trusted" flag on a klal
    says its *boundaries* were validated, not that its *interior* was
    searched for a second klal hiding inside it. Before concluding a
    klal_id has no content anywhere, read the full stored text of both
    neighbors for an embedded second marker and topic shift — do not infer
    absence from edge-adjacency alone. The direct-visual-page-render check
    (Lesson 14) is the reliable method here too.
17. **A token-height threshold for detecting catchwords is a useful
    first-pass filter, not a sufficient check on its own.** A direct
    render of the actual page can contradict a height measurement. On any
    page-crossing reconstruction, treat a borderline or unexpected height
    reading as a reason to render and look, not as settled by the number
    alone.
18. **A cheap, corpus-wide text-pattern sweep (grep a literal string, a
    regex, a duplicate-word scan) can find in minutes what extensive
    klal-by-klal manual review missed for an entire project's history.**
    Run this class of check routinely (after any batch of edits, not just
    when asked) — per Lesson 8, it catches a different class of error than
    vision/semantic review and costs almost nothing to run.
19. **Diagnosing a fix and describing it in writing is not the same as
    applying it — verify every "fixed"/"split"/"applied" claim against a
    diff of the actual data, not against how carefully it was written
    up.** This is Lesson 1 ("a check that isn't run has not verified
    anything") applied to one's own output: a prose claim of "fixed" is
    itself unverified until checked against a real before/after diff.
20. **Multi-volume/multi-part works must map page alignment across the full physical scan range.**
    When serving page-level bounding boxes and UI rendering for secondary parts (Parts 2 & 3),
    loader functions (`_load_alignment`, `_load_corrections`) must read combined datasets across all parts
    (`part1`, `part2`, `part3`) rather than defaulting to Part 1.
21. **Flattened Bounding Box Schema Discipline.**
    `_corpus_word_bboxes()` and `load_docai_page()` expect flat coordinate keys (`"x1"`, `"y1"`, `"x2"`, `"y2"`)
    on token objects. Nested `bbox: {x1: ...}` dictionary structures fail silently with `None` lookups,
    returning 0 bounding boxes to the UI. Always enforce flat coordinate keys in token serialization.
22. **Pluggable VLM Witness Engine Architecture.**
    Secondary witness evaluation must inherit from `AbstractWitnessEngine` ABC with image-grounded VLM adjudication
    ($\ge 0.90$ confidence) and disk caching in `adjudication_cache.db` to eliminate Tesseract OCR noise while
    preserving engine swappability.
23. **A witness is an ENGINE, not a SAMPLE. Running one model twice buys no
    independence.** Two passes of the same model agreeing is a *stability*
    measurement of that one witness, not corroboration by two. Treating VLM
    Pass A == Pass B as two-of-three consensus produced 1,051 disputes
    (2026-08-23); when a genuinely different engine was consulted on the same
    positions, **290 of them had that engine agreeing with the stored corpus
    text against the VLM**. Before counting a witness, ask what would have to go
    wrong for it to fail *differently* from the witness beside it. If the answer
    is "nothing — it's the same model", it is one witness. Use a repeat run as a
    reliability gate on that single witness instead: where the two passes
    disagree, it abstains.
24. **Architectural independence is defeated by a defect in the shared input.**
    Different OCR architectures fail differently on *ambiguous* glyphs, and
    identically on a *defective* one — every engine is reading the same ink, so
    a worn or ligatured printer's sort is upstream of all of them. Measured
    2026-08-23: 37 cases of two or three engines producing the identical wrong
    reading, including unanimous 3-of-3, all from one sort (the alef-lamed
    ligature `ﭏ` losing its `ל`). A published estimate priced that at
    3.5 × 10⁻⁷. Never reason about ensemble agreement with a `1/|V|`
    vocabulary term: hallucinations are not drawn uniformly from a vocabulary,
    they are drawn from what the glyph plausibly looks like. Corollary, also
    measured: enumerating and excluding the known defect barely improved the
    ensemble (41% → 39%), so a bigger artifact catalogue is not the repair.
25. **A signal that CANNOT disagree carries no information — verify a check can
    fail before trusting that it passed.** `build_vlm_alignment()` mapped only
    `SequenceMatcher.get_matching_blocks()`, where the two sequences are equal
    *by definition*, so the `vlm_reading`/`surya_reading` fields it fed could
    only ever echo the corpus's own word back: 49,138 and 34,892 aligned words,
    **zero divergent in either**. The feature shipped, was celebrated in
    `PROJECT-STATUS.md`, and was structurally incapable of doing its job. For
    any new comparison, agreement metric, or validator, construct one input that
    MUST make it report a difference. If you cannot, it is not measuring
    anything.
26. **A filter that HIDES is at least as dangerous as one that rewrites, and is
    harder to catch — validate it by what it suppresses, not by what it
    emits.** A wrong rewrite produces visible wrong text; a wrong suppression
    produces *silence*, and silence where a check cannot operate is not evidence
    of correctness (Lesson 15). This matters in proportion: measured 2026-08-24,
    the live filters suppress **12,444** items (VLM stability abstentions 1,577;
    ragged-alignment drops 10,455; witness-queue filtering 375; artifact tagging
    37) against **216** disputes that actually reach a reviewer — the filters
    decide roughly 98% of what a human never sees. Any filter standing between
    the corpus and a reviewer needs a measured false-negative rate against a
    hand-checked sample before it is trusted, and "it only tags, it doesn't
    rewrite" is not an exemption.
27. **An adversarially-selected sample cannot estimate a rate.** 40 consensus
    positions carried a human decision and in 39 the reviewer kept the stored
    text — which looks like "consensus is 2.5% accurate" and is not: a reviewer
    had already examined those exact words and confirmed the corpus, so a
    proposal to change them loses by construction. The usable estimate had to
    come from *undecided* positions. Before turning a labelled subset into a
    rate, ask why those particular items got labelled; if the labelling process
    selected on the outcome, the rate measures the selection, not the thing.
28. **A bug found in one place is a statement about where you looked, not about
    where it is — sweep the corpus before calling it fixed.** Every instance of
    this class in this project's history was reported as a single case and
    turned out to be many: a klal 9/10 box overlap that was 316 klalim; two
    unhighlighted disputes in klal 91 that were five collisions across two
    independent panes; one unclearable revisit flag that was **325 flags across
    104 klalim**. The sweep is nearly always cheap (a loop over all 222 klalim
    runs in seconds) and it changes what you are allowed to claim: without it
    you have fixed an instance, not closed a defect. This binds whether or not
    you fix the thing — an issue left open must still be documented with its
    real extent, because an open item that says "klal 91" when the answer is
    "104 klalim" reads as handled and is worse than silence. See Part 2's
    "Never fix one instance" section for the operational rule.
29. **A field nothing reads is not a feature — a serialized JSON key looks
    exactly like a delivered one.** Twice in one session (2026-08-24) a signal
    was computed, written into the API response, and never shown to a human, so
    it looked finished at every layer except the only one that matters.
    `vlm_reading` was built from an alignment structurally incapable of
    reporting disagreement and then dropped by the frontend's dedupe;
    `docai_repaired` - the reading measured **94% correct where the raw DocAI
    reading is 0%** - was served and never rendered, so the reviewer could not
    select the answer the pipeline had already worked out. `witness_overlay` was
    described in a commit message as "overlaid, not dropped": true of the JSON,
    false of the screen. For every new field ask two questions before calling it
    done — **who displays this, and what does a reviewer do differently because
    of it?** If neither has an answer, nothing was delivered. Sibling of Lesson
    25: that one is about a signal that cannot disagree, this one about a signal
    nobody sees.
30. **A wrong render looks exactly like a right one — verify indexing against
    CONTENT, never against plausibility.** `fitz.open(pdf)[N]` is page N+1 in
    this repo (`page N == doc[N-1]`, confirmed by pixel correlation:
    `page_30.png` vs `doc[29]` = 0.995, vs `doc[30]` = 0.038). Every ad-hoc crop
    made through that path on 2026-08-24 read the neighbouring page, and nothing
    in the images said so — they were legible 19th-century Hebrew, just the
    wrong legible Hebrew. It produced a retracted "resolution is not the lever"
    finding and nearly produced a filed pipeline bug ("these three klalim have
    wrong regions") that was false. What caught it was not looking harder at the
    image but asking **where the cropped text actually lives in the corpus** —
    a uniform +1 offset across three independent cases is a bug in the reader,
    not the data. Prefer `images/pdf_pages/page_N.png`, which is correctly
    indexed; when you must render, prove the mapping on a known page first.
31. **When your own fix regresses on measurement, revert AND STOP — a heuristic
    you have retuned twice is asking to be handed back, not tuned a third
    time.** `split_block_across_klalim()` was adjusted three times in one day to
    fix 4 mis-assigned klalim. Attempt two fixed nothing and cost 0.05pt;
    attempt three cost **29 klalim their coverage and 2.3 points of mean
    agreement**, collapsing twelve klalim (0.94 → 0.10 among them). All were
    reverted, and the only reason none reached the corpus is that a before/after
    measurement ran every time. The rule is not "measure" — that is Lesson 19 —
    it is that **repeated retuning of one heuristic is itself the signal**: the
    problem is under-specified, further attempts are guesses wearing fixes'
    clothes, and the correct move is to document the issue with its measured
    extent and hand it to the user. Never let a fix for N instances put the
    other 200 at risk.

32. **A tool that prints is not a tool that runs. Put a cheap check in the
    chain, or accept that its findings do not exist.** `detect_real_word_
    substitution.py` was finding `בחרא`->`בחדא` in klal 84 correctly, in its
    normal output, for as long as it had existed - and on 2026-08-26 the reviewer
    found that word by eye, because the script was `[STANDALONE]`, printed to
    stdout, was in no chain and wrote no file. It costs **0.1 seconds** on the
    full corpus. This is Lesson 29 ("a field nothing reads is not a feature")
    raised one level: a whole detector can be correct, maintained, and
    tested, and still deliver nothing. When you find yourself writing
    `[STANDALONE]` on something cheap and repeatable, ask what will cause it to
    run again, and if the answer is "somebody remembers", put it in
    `rebuild_all.sh` and have it write an artifact. Corollary, learned the same
    day: routing its output is a SEPARATE decision from running it - these
    detectors carry real false positives (the independent witnesses contradict
    149 of 262 findings), so the stage writes a triage report and never a flag.

33. **Check a tool's STATE, not its printout.** After purging 79 rows from
    `lexicon.txt`, the effect was checked by grepping the corpus-integrity
    validator's output for the purged forms - 1 of 13 appeared, which read as
    "the purge did not work". It had worked perfectly; the validator truncates
    its report to the top entries by frequency. Computing the set membership
    directly showed all 13. A grep against a summary is a check on the summary.
    This is Lesson 19's shape ("verify against the data, not against the
    write-up") applied to tooling output, and it costs a false alarm every time.

34. **Sweep the SIBLINGS of a bug, not just its class of input.** One defect -
    a decision naming a different span than the one it answers - was fixed three
    separate times in three branches of the same function: the confirmed-no-op
    (finding ★1), then the `insert` opcode (klal 66 w0, which deleted the `אין`
    that negates a klal), then `replace` (klal 69 w188, which deleted `ואלהים`).
    Each fix was correct and each was scoped to the branch that had just fired,
    so the next branch fired next. Lesson 28 says a bug found in one place is a
    statement about where you looked; the sibling branches of the SAME FUNCTION
    are the cheapest place to look, and both misses cost a real deleted word
    caught only by reading an applied diff word by word. When a mutator has three
    paths and one is wrong, read the other two before writing the test.

35. **Applying a correction has side effects on the review state, and every one
    of them must be carried out in the same step.** Promoting a decision into the
    corpus is not the end of the operation. It closes the flag that raised it; it
    shifts every later index in that klal, so both the open flags AND the pending
    decisions past that point must be re-pointed; and it makes the corpus disagree
    with the OCR tokens at that word, which regenerates a candidate there unless
    the generator is told the position is settled. NONE of that was carried out,
    so every correction quietly degraded the queue it came from: 48 dead flags
    still lit, one flag walked onto the wrong word, decisions stranded at stale
    indices, and 279 candidates - 46% of the queue - asking the reviewer to rule
    again on words they had already settled, 39 of them proposing to UNDO an
    applied fix. When a step writes to the source of truth, enumerate what else
    describes that truth and update it in the same breath, or the description
    rots against the thing it describes.

36. **A test pinned to real corpus content is testing the defect, not the
    behaviour - and it fails when the corpus IMPROVES.** All 38 UI tests boot
    against the shipped corpus and 23 pin a coordinate in executable code, so
    repairing the text broke seven of them at once: one asserted a literal `&`
    that had just been correctly repaired to `אל`, three sat on a klal whose
    candidates had all been settled. For a general-purpose platform that failure
    mode is inverted - the closer a text gets to correct, the more tests fail.
    The engine layer is already right (`test_pipeline_logic.py` is 274 tests as of
    2026-08-31, 273 when this lesson was written; 91
    purely synthetic, verified on a throwaway `אלף בית גימל` corpus and portable
    to any book); it is the UI layer that needs a synthetic fixture corpus
    carrying one of each condition. Corollary for the invariants that DO read the
    real corpus by design: a baseline keyed `(klal_id, word_index)` shifts on
    every insertion, and nothing can reindex a literal in a test file.

37. **A test that is DEFINED is not a test that RUNS — count what the runner
    collects, never what the file declares.** `tests/test_review_server.py`
    declares 38 `def test_` statements and pytest collects **36**: two names are
    defined twice, and Python rebinds a name on the second `def`, so the first
    body is discarded at import with no error, no skip and no warning. The only
    symptom is the difference between two numbers nobody was comparing — and the
    discarded copy was in both cases the STRICTER one, asserting
    `len(ringed) == 1` where the survivor asserts merely `assert ringed`, and
    covering a route (`/#klal=66`, klal without word) the survivor never visits.
    So the feature read as tested, the suite was green, and the coverage was not
    there. This is Lesson 32 ("a tool that prints is not a tool that runs") one
    level in, and Lesson 33's shape as well: `grep -c "^def test_"` is a check on
    the SOURCE, and the thing that decides what runs is the collector. Whenever
    you cite a test count — in a status entry, a review, a commit message — get
    it from `pytest --collect-only -q`, and if the two numbers disagree, the
    disagreement IS the finding. A `def test_` count equal to the collected count
    is one cheap assertion; nothing in this repo's gate makes it yet.
