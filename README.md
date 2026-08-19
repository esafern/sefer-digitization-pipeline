# Sefer Digitization Pipeline

A digitization pipeline for historical Hebrew/Rabbinic texts, aimed at
producing Sefaria-ready output.

## TL;DR

**What it does.** OCR extraction (Google Document AI) → diff the fresh OCR
against the stored corpus text → crop each disagreement out of the scan and
have a vision model adjudicate it → human review in a local dashboard →
apply. Every decision is recorded in an append-only, git-tracked ledger that
no automated rebuild can touch.

**What makes it different.** Most Hebrew digitization tooling stops at OCR or
at line-level correction. This pipeline is built around the *disagreement*:
word-level bounding boxes, image-grounded VLM adjudication of each disputed
token, and a tri-state (open / machine-resolved / human-decided) review model
with per-word provenance. See `COMPETITIVE-LANDSCAPE.md`.

**What it's been run on.** **Yad Malachi** (R. Malachi ben Jacob HaKohen,
Livorno 1766–7) — 667 *klalim* in three parts, the #1 public-domain work
Sefaria lacks (287 dead citations point at it today). Part 1 is fully built
out; Parts 2–3 have the infrastructure built and run, with corrections found
but deliberately not applied yet. Yad Malachi is the first application, not
the design target: the pipeline is written to generalize to other historical
Hebrew texts, and that is a standing directive, not an aspiration — see
`START_HERE.md`.

**Where to start reading.** `START_HERE.md` — Part 1 for humans, Part 2 for
LLM agents (binding rules). Then `PROJECT-STATUS.md` for what's actually open
right now.

**Not in this repo.** The source scans, credentials, and several large derived
caches are gitignored — `SETUP.md` explains how to get them, and
`tools/verify_local_setup.py` proves they landed.

## Status

- **Part 1** (*Klalei HaGemara*, 222 klalim) has the full pipeline: extraction
  → correction-candidate generation → vision adjudication → human review →
  applied corrections, gated by a 222-test pytest suite on every rebuild.
  222/222 klalim have a trusted page-to-klal alignment; 125 word-level
  candidates remain open.
- **Parts 2–3** (445 klalim) have marker verification and the
  scan-linkage/adjudication infrastructure built and run over their full page
  range. 916 klalim carry an open review flag. **No `part2.json`/`part3.json`
  correction has been applied** — that step needs its own explicit go-ahead,
  per the Parts 2-3 gate in `START_HERE.md`.

`PROJECT-STATUS.md` has the live detail.

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
