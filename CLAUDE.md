# Yad Malachi Pipeline

Digitization pipeline for **Yad Malachi** (R. Malachi ben Jacob HaKohen, Livorno
1766–7), a foundational halachic-methodology reference with 667 *klalim* across
three parts. Goal: a clean, structured digital text for Sefaria — see
`CASE-YAD-MALACHI.md` for the full rationale (287 dead Sefaria citations point to
this work today).

> **Read `PROJECT-STATUS.md` at the start of every session, every time, no
> exceptions.** This file (`CLAUDE.md`) holds durable rules and architecture.
> `PROJECT-STATUS.md` holds the current, specific, dated truth — what's fixed,
> what's still broken, what was investigated and why. Neither substitutes for
> the other. Do not report on, fix, or make claims about corpus quality
> without having read it first.

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
