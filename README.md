# Sefer Digitization Pipeline

A high-fidelity digitization pipeline for historical Rabbinic Hebrew/Aramaic texts, engineered for Sefaria-ready output.

## TL;DR

**Architecture & Workflow.** Primary Text Extraction (Google Document AI) → Secondary Witness Evaluation (VLM `VlmWitnessEngine`) → Multi-Witness Image-Grounded Adjudication (VLM Vision Adjudicator) → Interactive Human Review Dashboard → Persistent Decision Ledger. Every decision is recorded in an append-only, git-tracked ledger (`review_decisions.jsonl`) that automated rebuilds never overwrite.

**Key Differentiation.** Most Hebrew OCR tooling stops at raw OCR or character-level alignment. This pipeline is built around **multi-witness vision adjudication**: exact token-level bounding boxes, image-grounded VLM evaluation of every disputed token, and a tri-state (open / machine-resolved / human-decided) review model with per-word provenance. See `COMPETITIVE-LANDSCAPE.md`.

**Corpus Application.** **Yad Malachi** (R. Malachi ben Jacob HaKohen, Livorno 1766–7) — 667 *klalim* across three parts. 
- **Part 1** (*Klalei HaGemara*, 222 klalim): Fully aligned and reviewed against page scans.
- **Parts 2–3** (*Klalei HaPoskim*, *Klalei HaDinim*, 445 klalim): Fully mapped with VLM witness candidates queued for reviewer adjudication.

**Where to start reading.** `START_HERE.md` for project context and binding operational rules. Then `PROJECT-STATUS.md` for current operational state.

## Status

- **Part 1** (*Klalei HaGemara*, 222 klalim): 222/222 klalim trusted and aligned; multi-witness VLM candidates adjudicated and reviewed.
- **Parts 2–3** (*Klalei HaPoskim*, *Klalei HaDinim*, 445 klalim): 445/445 klalim mapped with VLM secondary witness candidates generated and queued for human review.

`PROJECT-STATUS.md` has live operational details.

## Getting started

See `SETUP.md`.

## Documentation map

| File | What it's for |
|---|---|
| `START_HERE.md` | **The main onboarding doc.** Part 1: project context, success criteria, architecture, directory layout, commands (for humans). Part 2: binding operational rules for LLM agents — session checklist, the Parts 2-3 gate, the corpus single-source-of-truth rule, 19 numbered lessons. |
| `PROJECT-STATUS.md` | Current, dated state: what's open, what's in progress. Kept short enough to read in full every session. |
| `PROJECT-STATUS-HISTORY.md` | The closed-out dated log — the evidence trail behind any finding referenced in the status file. |
| `SETUP.md` | Environment setup, and which files aren't in this repo and how to get them. |
| `PIPELINE-DATA-REFERENCE.md` | What each data file actually contains, field by field, in flow order. |
| `CASE-YAD-MALACHI.md` | The case for why this work needs digitizing — citation demand, editions in hand, method, cost, and the ask. |
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
