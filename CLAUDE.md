# Yad Malachi Pipeline

Digitization pipeline for **Yad Malachi** (R. Malachi ben Jacob HaKohen, Livorno
1766–7), a foundational halachic-methodology reference with 667 *klalim* across
three parts. Goal: a clean, structured digital text for Sefaria — see
`CASE-YAD-MALACHI.md` for the full rationale (287 dead Sefaria citations point to
this work today).

## Pipeline shape

## Success criteria (in priority order)

1. **Absolute fidelity to the author's words.** The transcript must match the
   source scans exactly — no paraphrase, no silent normalization, no
   "improving" the text. Every correction must be traceable to a real OCR/VLM
   disagreement resolved by looking at the actual scan, not inferred.
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

Source scans (`berlin_square.pdf`, Sefaria VLM output, DocAI OCR) get extracted,
cross-validated between OCR engines, and adjudicated word-by-word before landing
in the canonical text files. Concretely:

1. **Extraction** — `chunker.py` pulls raw text per page from the PDF (handles
   the reversed-Hebrew-line quirk of these 19th-century scans via
   `unreverse_line`). DocAI/VLM extraction happens through the (gitignored)
   `docai_word_boxes/`, `document_jsons_berlin/`, `vlm_extractions/` caches.
2. **Adjudication** — `orchestrator.py` is the live, `[PRODUCTION]`-tagged
   cross-validator: crops each token's bounding box from the PDF, sends it to
   Gemini (`google.genai`) for a vision-based OCR/VLM disagreement call, and
   caches every decision in `adjudication_cache.db` (sqlite, keyed by crop
   hash) so repeat runs don't re-spend API calls. Requires a Gemini API key in
   the environment (not committed — check `credentials.json`, gitignored).
3. **Assembly & lexicon** — outputs converge into `full_text_cleaned.txt` /
   `full_text_cleaned_goal.txt`, `part1.json` / `part2.json` / `part3.json`
   (one per Yad Malachi section), `processed_klalim/` (per-klal JSON, 813
   tracked files), and `lexicon.txt` (~19k unique validated Rabbinic Hebrew
   words used as a spell-check dictionary during cleanup passes).
4. **Demos/reports** — `SEFARIA-VLM-DEMO.html`, `SEFARIA-BERLIN-DEMO.html`, and
   the `*-VISUAL-REPORT.html` / `*-OVERVIEW.html` files at root are rendered
   inspection demos, not pipeline code — open them in a browser to visually
   verify a correction, per the `.gemini/rules/robust_ocr_processing.md` rule
   file's UI-verification requirement.

## Directory layout

- `orchestrator.py`, `chunker.py` — the only two files marked as live pipeline
  code; everything else at root is either an established data artifact (see
  above) or a historical one-off script.
- `archive/scripts/`, `archive/data/` — one-time, already-applied patch/find/
  debug scripts (hardcoded to specific klal numbers or line indices) and their
  throwaway text/JSON dumps, moved out of the root in Aug 2026 for
  discoverability. Safe to reference for *how* a past fix was done, not meant
  to be rerun as-is.
- `aligned_klalim/`, `klalim_batches/`, `processed_klalim/` — tracked,
  versioned pipeline output at various stages.
- `docai_word_boxes/`, `document_jsons_berlin/`, `klalim_docai/`,
  `llm_klal_starts/`, `sefaria_export/`, `vlm_extractions/`, `scratch/` —
  gitignored regenerable caches/intermediates. Don't assume these exist on a
  fresh clone; they're rebuilt by re-running the extraction scripts against
  the source scans.
- `.gemini/rules/` — Gemini CLI's equivalent of this file; this project has
  been worked on from both Claude Code and Gemini CLI, so check both when
  looking for standing directives.

## Open items

- **Rigorous (vision-confidence-scored) review currently covers Part 1 only**
  (klal 1–222, the range with scan+bbox data). Parts 2 and 3 have no linked
  scan images or word bounding boxes yet, so no vision-adjudicated confidence
  scores exist for them — corrections there are unverified against the source
  scan until that data is built out.
- The review UI (`review.html`, renamed from `SEFARIA-BERLIN-DEMO.html`) is a
  work in progress: 3-pane layout (scan-highlight left / full text middle /
  abridged klal nav right), with per-word corrections + confidence surfaced
  for human review.
- The many pre-existing tracked one-off scripts at root
  (`fix_1_line_offset_and_rebuild.py`, `fix_klal_74_stitching.py`,
  `build_full_pristine_667.py`, etc.) follow the same disposable-patch pattern
  as what got moved into `archive/` — they predate that cleanup and weren't
  touched, since reorganizing already-tracked history is a bigger call than
  tidying untracked files.

## Conventions observed

- Corrections are driven by direct LLM adjudication with **rendered UI
  verification** (open the HTML demo, visually confirm), not blind text diffs
  — see `.gemini/rules/rabbinic_ocr_adjudication.md` / `robust_ocr_processing.md`.
- Every cleanup pass targets **zero flagged items** in `lexicon.txt` validation
  before being considered done (see commit history: "100% clean validation
  pass" is the recurring bar).
