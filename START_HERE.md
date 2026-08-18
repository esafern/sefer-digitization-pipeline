# Start Here

This is the main onboarding document for this repo. Part 1 is written for a
human contributor; Part 2 is written for an LLM instance (Claude Code,
Gemini CLI, or any other agent) working in this repo — its rules are
binding, not optional reading.

If you only came here from `README.md`, you've got the right file. If
you're an LLM that loaded `CLAUDE.md` automatically, that file is a short
redirect to here — read on.

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
halachic-methodology reference with 667 *klalim* across three parts. See
`CASE-YAD-MALACHI.md` for the rationale (287 dead Sefaria citations
currently point to this work).

Livorno 1766-7 is the work's ORIGINAL printing. The scan this pipeline
actually OCRs, `berlin_square_corrected.pdf`, is a LATER, SECOND printing,
in Berlin, per its own title page (`נדפס ראשונה בליוורנו... ועתה נדפס פעם
שנית` — "first printed in Livorno... now printed a second time," colophon
`ברלין`, editor אפרים הערץ of Silesia). Square Hebrew typeface throughout
(not Rashi script) — matches the filename. Don't conflate the two editions.

**Berlin printing date: Hebrew year תרי"ב = 1851/2 CE**, confirmed
2026-08-18 against the National Library of Israel's catalog record for this
exact edition (NLI system number `990011859020205171`, viewable at
<https://www.nli.org.il/en/books/NNL_ALEPH990011859020205171/NLI> — same
"printed a second time... by Efraim Hertz" edition note, same Berlin/
Zittenfeld imprint, and the same 337-page count as this repo's local PDF —
not git-tracked here, see "Files not in the public repo" in `SETUP.md`).
The
date rests on two independent chronograms inside the book itself (the
publisher's introduction signing-date, and a separate Deuteronomy-verse
chronogram used as the formal creation-date), both encoding 612 — a
primary-source confirmation, not an inference. This supersedes an earlier
"~1857/8" estimate that had been inferred secondhand from a *later*
edition's title page, and separately resolves a discrepancy flagged but
never resolved in `PROJECT-STATUS-HISTORY.md` (a Wikipedia summary had
implied ~1917, evidently a misconverted gematria). See
`PROJECT-STATUS-HISTORY.md`'s 2026-08-18 entries for the full research
trail.

**Provenance.** This pipeline's own working PDFs stay Google Books-sourced
— **do not switch them to an anonymous NLI download.** The original scan
is publicly downloadable at
<https://www.google.com/books/edition/_/OdiHjxI3I0EC> — confirmed
2026-08-18 (via an actual browser render, not a plain HTML fetch, which
first misread it as a different edition entirely) to be this exact
printing: same `דפוס י. זיטטענפעלד` (Zittenfeld) publisher as this scan's
own title page, and Google's own bibliographic panel states its source as
the National Library of Israel itself — so this Google Books copy and the
NLI record below are the same underlying digitization, just re-hosted.
NLI's own site is still the right pointer to give someone else acquiring
this text for the first time (per `CASE-YAD-MALACHI.md`'s "Preparing the
text for Sefaria" section, sourcing from NLI sidesteps Google Books' terms
of use for redistribution), but only if *they* use an NLI account to get
full resolution — an anonymous NLI download is a real quality downgrade,
not an equivalent copy (see below).

**Validated end-to-end 2026-08-18, then deliberately NOT adopted, for a
resolution reason found along the way.** Downloaded the full 337-page book
directly from the NLI record above (`Download` → "the complete document").
Applied the leaf-order fix below to it and confirmed by direct content
inspection (matching folio numbers and catchwords, not just file
existence) that it reproduces the correct reading order — the acquisition
+ fix procedure genuinely works. But image quality is a real, checked
problem, not a formality: NLI's "Maximal (100%)" size is greyed out under
`File format: PDF` (gated behind an NLI account this project doesn't
have) but **is selectable under `File format: JPEG\ZIP`, anonymously** —
comparing the same physical page's embedded/extracted image directly, this
pipeline's local PDF is **3440×5312px PNG** (~18.3 MP, lossless); NLI's
best anonymously-available tier (JPEG\ZIP, Maximal) is **1745×2658px
JPEG** (~4.6 MP, lossy) — about **4x fewer pixels**, plus lossy compression
on top. (The PDF download path's "Medium" — the only anonymous PDF tier —
is worse still: 873×1329px, ~16x fewer pixels; JPEG\ZIP is the better
anonymous path if NLI is ever used for real acquisition.) Even at its best
anonymous tier, NLI is nowhere near this pipeline's existing
OCR/vision-adjudication quality bar. An NLI account might unlock something
higher still (untested) — until confirmed otherwise, treat 1745×2658 as
the ceiling.

**NLI's PDF is also 336 pages, not 337 — a constant 1-page offset, not a
different scan** (separate from the quality issue above, and true at
whatever quality tier you download). This pipeline's local
`berlin_square_corrected.pdf`/`berlin_square_original_transposed.pdf` came
from a Google Books scan whose page 0 is a "Digitized by Google" disclaimer
page that Google inserts and NLI's own digitization doesn't have. Confirmed
by direct comparison: NLI page *i* = the Google-sourced PDF's page *i + 1*
for every page checked, including at the transposed-leaf region. **Every
page-indexed cache in this pipeline** (`docai_word_boxes/`,
`images/pdf_pages/`, `gematria_trace_part1.json`,
`part1_header_anchored_alignment.json`) **is indexed against the
Google-sourced 337-page numbering** — kept only as a documented offset in
case a future, actually-equivalent-quality NLI source is ever adopted; not
acted on now.

**The scan itself had two leaves out of order — a defect in the source
binding, not an extraction bug.** Two physical leaves were transposed; true
reading order is printed page 36 → 38 → 37 → 39, found via a
catchword-chain sweep (each page's closing catchword should match the next
page's opening word) and confirmed by rendering both pages directly. On
the Google-sourced 337-page numbering (this repo's local PDFs), that's
0-indexed leaf 37 moving to position 36; on an NLI-sourced 336-page PDF
(one page earlier throughout, see above), the same physical leaves are at
0-indexed 36 moving to position 35. Fixed with `fitz.move_page` (page count
unchanged either way) — `berlin_square_corrected.pdf` (local, not
git-tracked, fixed) is the only PDF that should ever be used as the
pipeline's source; `berlin_square_original_transposed.pdf` (local,
pre-fix) is kept only as a diffable reference, never to be fed to the
pipeline directly. Every
page-indexed cache built before the fix had to move in lockstep:
`docai_word_boxes/page_37.json` ⇄ `page_38.json`, `images/pdf_pages/
page_37.png` ⇄ `page_38.png`, and klalim 76-84's page attribution in
`gematria_trace_part1.json`/`part1_header_anchored_alignment.json` remapped
page 37 → 38. `part1.json`'s own `page` field was deliberately left
untouched (already stale/dead metadata for most of Part 1).

**If you ever need to redo this** — e.g. starting from a completely fresh
scan download rather than this repo's own local `berlin_square_
corrected.pdf` — use `tools/fix_transposed_leaf.py`, a small reusable CLI
built 2026-08-18 and verified two ways: byte-for-byte against the local
Google-sourced PDF, and by direct content inspection against a fresh NLI
download. **Use the indices matching whichever source you actually pulled
from** — they differ by 1 (see above):

```bash
# Google-sourced PDF (this repo's local files use this numbering):
python3 tools/fix_transposed_leaf.py --pdf berlin_square_original_transposed.pdf \
    --from-index 37 --to-index 36 --output berlin_square_corrected.pdf

# NLI-sourced PDF (one page earlier throughout - verified 2026-08-18):
python3 tools/fix_transposed_leaf.py --pdf berlin_square_original_transposed.pdf \
    --from-index 36 --to-index 35 --output berlin_square_corrected.pdf
```

It only fixes the PDF's own physical page order — it does not know about
`docai_word_boxes/`, `images/pdf_pages/`, or the alignment/trace files, so
any of those built from a differently-ordered (or differently-sourced) PDF
still need the manual remap described above. This is a generic
leaf-reordering tool, not Yad-Malachi-specific, in keeping with this
project's generalization goal.

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

Part 1 (*Klalei HaGemara*) has the full pipeline built out. Parts 2-3 are
gated — see Part 2's "Parts 2-3 gate" section below for the binding rule
and its rationale.

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
   `part3.json` (one per Yad Malachi section — THE corpus, hand-edited
   only through the decision pipeline in Part 2, never directly),
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
  `build_klal_page_regions.py`), the live review tool (`review_server.py`,
  `review_decisions.py`, `apply_reviewer_decisions.py`,
  `audit_applied_decisions.py`), and two shared library modules that are
  imported, never run directly, by scripts in both `pipeline/` and
  `tools/`: `vision_adjudication_common.py` (crop/cache/JSON-recovery/
  retry/client machinery for every Gemini-calling script) and
  `corpus_io.py` (repo paths, corpus/derived-artifact loading, DocAI
  page-token loading, alignment/gematria-trace readers, Hebrew-text
  helpers). Both are imported via
  `sys.path.insert(0, os.path.join(REPO, "pipeline"))`.
- **`tools/`** — everything run manually/standalone: all validators
  (`validate_klal_span_coverage.py`, `validate_catchword_continuity.py`,
  `validate_title_alphabetical_order.py`, `check_klal_token_orphans.py`,
  `detect_ligature_corruption.py`, `validate_part1_corpus_integrity.py`,
  `validate_lexicon_independent.py`, `detect_real_word_substitution.py`,
  `check_next_marker_and_title.py`, `verify_flagged_candidates_vision.py`),
  the lexicon/abbreviation-expansion scripts
  (`extract_abbreviation_forms.py`, `propose_abbreviation_expansions.py`,
  `review_lexicon_gaps.py`), the reference-corpus fetcher
  (`fetch_sefaria_reference_corpus.py`), the punctuation pass
  (`propose_punctuation_part1.py`, `apply_punctuation_decisions.py`), the
  witness/reconstruction scripts (`verify_reconstruction_witness.py`,
  `verify_witness_vision.py`), the DocAI page-extraction script
  (`extract_docai_pages.py`, promoted 2026-08-18 from
  `archive/scripts/extend_docai_ocr.py` — needs a GCP service-account key,
  not part of `rebuild_all.sh`), the leaf-order-fix tool
  (`fix_transposed_leaf.py`), and the local-setup verifier
  (`verify_local_setup.py`, see `SETUP.md`).
- **`tests/`** — the pytest suite. `rebuild_all.sh`'s step 6/6 runs
  `test_corpus_invariants.py` (checks the DATA a pipeline run produced) and
  `test_pipeline_logic.py` (checks the pure decision LOGIC on synthetic
  inputs) as a hard gate. `test_review_server.py` (Playwright, live
  server) stays outside the gate, run manually.
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
- `CASE-YAD-MALACHI.md` — the case for why this work needs digitizing.
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
  client machinery for every Gemini-calling script.
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
