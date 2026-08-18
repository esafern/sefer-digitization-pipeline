# Sefer Digitization Pipeline

A digitization pipeline for historical Hebrew/Rabbinic texts, aimed at
producing Sefaria-ready output: OCR extraction, LLM/vision-based
cross-checking against the actual scan, klal/section-boundary verification,
and a human-review dashboard for resolving flagged disagreements.

The pipeline is built to generalize beyond any one work — see
`CLAUDE.md` for the standing directive on writing it that way — but its
first, and so far only fully-built-out, application is **Yad Malachi**
(R. Malachi ben Jacob HaKohen, Livorno 1766–7), a foundational
halachic-methodology reference with 667 *klalim* across three parts. See
`CASE-YAD-MALACHI.md` for the rationale (287 dead Sefaria citations
currently point to this work).

## Status

- **Part 1** (*Klalei HaGemara*) has the full pipeline built out:
  extraction → correction-candidate generation → vision adjudication →
  human review → applied corrections, plus a standing pytest gate. See
  `PROJECT-STATUS.md` for exactly what's clean, what's open, and what's
  currently being investigated.
- **Parts 2–3** are gated: infrastructure (extraction, marker/scan-linkage
  detection, boundary verification) may be built and run, but no
  correction gets applied to `part2.json`/`part3.json` until Part 1 is
  fully clean *and* independently confirmed by an outside professional —
  see CLAUDE.md's "Parts 2-3 are out of scope..." section for the full
  reasoning and its explicit, dated authorization history.

## Getting started

See `SETUP.md` for environment setup (this repo requires a venv on
PEP 668-managed Python installs) and which files aren't in this public
repo (the source scans, credentials, and several large derived caches)
and how to get them.

## Where things live

- `CLAUDE.md` — durable architecture, pipeline shape, and standing rules.
  Read this first; it explains the single-source-of-truth model for
  corpus text (`part1.json`/`part2.json`/`part3.json`) and the separation
  between recording a human review decision and applying it to the corpus.
- `PROJECT-STATUS.md` — the current, dated state: what's fixed, what's
  broken, what's in progress.
- `PIPELINE-DATA-REFERENCE.md` — what each data file actually contains
  and where it sits in the pipeline.
- `pipeline/` — the live, orchestrated pipeline stages and the review
  server. `tools/` — standalone validators and one-off analysis scripts.
  `tests/` — the pytest suite that gates `rebuild_all.sh`.

## Success criteria

In priority order: (1) absolute fidelity to the author's words, verified
against the scan, never inferred; (2) accurate section/klal chunking; (3)
output that's ready to ingest into Sefaria as-is. See `CLAUDE.md` for the
full statement.
