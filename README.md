# Sefer Digitization Pipeline

A high-fidelity digitization pipeline for historical Rabbinic Hebrew/Aramaic texts, engineered for Sefaria-ready output.

## TL;DR

**Architecture & Workflow.** Primary text extraction (Google Document AI) → witness baselines that fail differently (a VLM read twice, Surya at 300 DPI) → multi-witness consensus synthesis → image-grounded vision adjudication of every disputed token → interactive human review dashboard → persistent decision ledger. A second-*edition* Rashi-script witness (Dicta) has been measured and previewed but is **not yet wired into the rebuild chain**. Every decision is recorded in an append-only, git-tracked ledger (`review_decisions.jsonl`) that automated rebuilds never overwrite.

**Key Differentiation.** Most Hebrew OCR tooling stops at raw OCR or character-level alignment. This pipeline is built around **multi-witness vision adjudication**: exact token-level bounding boxes, image-grounded VLM evaluation of every disputed token, and a tri-state (open / machine-resolved / human-decided) review model with per-word provenance. See `COMPETITIVE-LANDSCAPE.md`.

**Corpus Application.** **Yad Malachi** (R. Malachi ben Jacob HaKohen, Livorno 1766–7). The digitized corpus is the work's part one, ***Klalei HaGemara*** — **596 of its 667 *klalim*, ~188,500 words**, scan pages 14–247 — split across three files for handling (`part1/2/3.json` = klalim 1–222, 223–444, 445–667). **71 klalim** in 223–667 are unfilled placeholders. The book's other two parts, *Klalei HaPoskim* (pages 254–291) and *Klalei HaDinim* (292–329), are **not extracted**.

**Where to start reading.** `START_HERE.md` for project context and binding operational rules. Then `PROJECT-STATUS.md` for current operational state.

## Status

- **Klalim 1–222** (`part1.json`): 222/222 trusted page-to-klal alignment; witnesses read against the ink (Document AI, a VLM sampled twice, Surya at 300 DPI). A second-edition Rashi witness has been measured over klalim 1–63 and its findings previewed for a reviewer; it is not a pipeline stage yet. The flag queue moves every session — **re-measure it from the dashboard rather than quoting a number here**, which is the same discipline `PROJECT-STATUS.md` applies to itself.
- **Klalim 223–667** (`part2.json`, `part3.json`): text and page-level alignment built; **71 are unfilled placeholders**, and **no witness set has been run there yet and no correction has been applied** — a standing gate, not an oversight.
- **Klalei HaPoskim / Klalei HaDinim**: scanned, never extracted.

`PROJECT-STATUS.md` has live operational details, and is the only file to trust for corpus-quality claims.

## Getting started

See `SETUP.md`.

## Documentation map

| File | What it's for |
|---|---|
| `START_HERE.md` | **The main onboarding doc.** Part 1: project context, success criteria, architecture, directory layout, commands (for humans). Part 2: binding operational rules for LLM agents — session checklist, the Parts 2-3 gate, the corpus single-source-of-truth rule, 45 numbered lessons. |
| `PROJECT-STATUS.md` | Current, dated state: what's open, what's in progress. Kept short enough to read in full every session. |
| `PROJECT-STATUS-HISTORY.md` | The closed-out dated log — the evidence trail behind any finding referenced in the status file. |
| `SETUP.md` | Environment setup, and which files aren't in this repo and how to get them. |
| `PIPELINE-DATA-REFERENCE.md` | What each data file actually contains, field by field, in flow order. |
| `CASE-YAD-MALACHI.md` | **The case for the project** — why this work, why it is the cheapest one to fix, why this pipeline, and the ask. Short by design. |
| `HOW-THE-PIPELINE-WORKS.md` | The companion to that case: method, what the witnesses measured, current state, costs, and the Sefaria last mile. |
| `CORPUS-COMPARISON.md` | The citation survey behind the case doc's demand figures. |
| `COMPETITIVE-LANDSCAPE.md` | How this pipeline compares to Dicta, eScriptorium, Transkribus, the MiDRASH/Sefaria pipelines, and others — what to borrow, what's genuinely unique here. |
| `VERIFIED-AGAINST-THE-INK.html` | Outward-facing evidence showcase: real scan crops, real corrections, worked end-to-end. |
| `CLAUDE.md` | A redirect stub, not content. Exists only because some tools auto-load that exact filename; it points to `START_HERE.md`. |
| `DOCS-HISTORY.md` | How the docs and directory layout themselves evolved. Archaeology, not required reading. |

Code lives in `pipeline/` (the live, orchestrated stages and the review
server), `tools/` (standalone validators, exporters, one-off analysis), and
`tests/` (the pytest suite gating `rebuild_all.sh`).

## Success criteria

In priority order:

1. **Absolute fidelity to the author's words** — verified against the scan,
   never inferred, never silently normalized.
2. **Accurate klal chunking** — a wrong boundary is as serious a defect as a
   wrong word.
3. **Sefaria-ready output** — usable as-is on ingest, not merely "clean text."

`START_HERE.md` has the full statement. Any change, correction pass, or
shortcut gets weighed against these three before speed or cleanliness.
