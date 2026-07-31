# Yad Malachi Textual Pipeline: High-Level Strategic Alignment & Goal Audit

## 1. Executive Summary

This document evaluates the high-level strategic alignment of the **Yad Malachi Textual Pipeline** to confirm that technical implementation and architectural evolutions remain 100% aligned with the core project mission established in [`CASE-YAD-MALACHI.md`](file:///Users/ericsafern/work/yad-malachi/yad-malachi-pipeline/CASE-YAD-MALACHI.md).

---

## 2. Strategic Goal Audit: Vision vs. Execution

```
 ┌─────────────────────────────────────────────────────────────────────────┐
 │                            ORIGINAL VISION                              │
 │ Digitizing Yad Malachi into a clean, linkable, public-domain text to    │
 │ resolve 287 un-linked Sefaria references & 243 Halachipedia citations.  │
 └────────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
 ┌─────────────────────────────────────────────────────────────────────────┐
 │                            GOAL AUDIT STATUS                            │
 │  ✔ Target Work: Yad Malachi (R. Malachi ben Jacob HaKohen of Livorno)  │
 │  ✔ Target Output: Linkable digital edition across 3 parts & klalim      │
 │  ✔ Accuracy Guardrails: Zero text hallucination / strict verification  │
 │  ✔ Labor Reduction: Auto-accept consensus, flag only true conflicts    │
 └────────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
 ┌─────────────────────────────────────────────────────────────────────────┐
 │                       ARCHITECTURAL EVOLUTION                           │
 │ Upgraded from text-only OCR voting to Image-Grounded Visual Adjudication│
 │ using 300 DPI PyMuPDF raster crops + Gemini Multimodal Vision.          │
 └─────────────────────────────────────────────────────────────────────────┘
```

### Goal Alignment Matrix

| Project Dimension | Vision (`CASE-YAD-MALACHI.md`) | Current Execution State | Alignment Status |
| :--- | :--- | :--- | :---: |
| **Core Target** | Digitizing *Yad Malachi* (Livorno 1766, Berlin 1857, Przemyśl 1877/1888). | Pipeline built specifically for *Yad Malachi* spatial JSONs and PDF pages. | **100% ALIGNED** |
| **Public-Domain Focus** | Restrict base text ingestion to PD printings. | Ingests PD scans (`test_page.pdf`) & Document AI spatial outputs. | **100% ALIGNED** |
| **Validation Milestone** | Domain validation by NLI expert R. Ezra Shvat. | Target milestone: NLI Demonstration Package (see [`NLI-VALIDATION-STRATEGY.md`](file:///Users/ericsafern/work/yad-malachi/yad-malachi-pipeline/NLI-VALIDATION-STRATEGY.md)). | **100% ALIGNED** |
| **Collation Strategy** | Text-based voting across OCR passes. | **Upgraded**: Image-grounded visual adjudication against 300 DPI PDF rasters. | **STRONGER THAN ORIGINAL** |
| **Hallucination Prevention** | Guardrail prompt: select attested candidates or flag uncertainty. | Enforced in Gemini prompt; model outputs `UNCERTAIN` + paleographic reasoning. | **100% ALIGNED** |
| **Cost & Labor Optimization** | Collapse human proofreading to ~5–10 hours of expert review. | SQLite SHA-256 caching + ThreadPoolExecutor concurrency minimizes API & human cost. | **100% ALIGNED** |

---

## 3. Detailed Architectural Evolution Analysis

### Why the Technical Evolution Strengthens the Mission
The original proposal suggested relying on text-based consensus voting across 5 OCR engine outputs. During implementation, we evolved the architecture to **Image-Grounded Visual Adjudication**:

1. **Visual Truth vs. Textual Guesswork**: Text-based voting engines can agree on a shared OCR misreading. By feeding the high-DPI manuscript image crop directly to Gemini (`gemini-3.6-flash`), the system verifies what is physically printed on the page rather than voting on text strings.
2. **Handling Rabbinic Acronyms & Abbreviations**: Rabbinic texts use abbreviations extensively (e.g., `למ"ד` = `למאן דאמר` / `לומד`). Pure text diffing flags these as errors. Our spatial alignment and visual adjudication engine correctly identifies `למ"ד` on the manuscript, transcribes the gershayim marks, and explains the relation to candidate readings.
3. **Resilience & Zero Duplication**: The addition of local SQLite caching (`adjudication_cache.db`) ensures that identical manuscript crops are never re-sent to the network, locking in determinism and cost efficiency.

---

## 4. Phase Roadmap & Next Milestones

```
 ┌────────────────────────────────────────────────────────────────────────┐
 │ PHASE 1: Controlled Core Experiment (COMPLETED & VERIFIED)             │
 │ • Verified spatial token alignment & difflib normalization            │
 │ • Validated ThreadPoolExecutor multi-threaded adjudication             │
 │ • Integrated SHA-256 SQLite caching (adjudication_cache.db)           │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ PHASE 2: Full Extraction & OCR Stream Ingestion (CURRENT STEP)         │
 │ • Extract full base text streams from target PDFs                     │
 │ • Run witness scans through OCR tools to generate comparison streams   │
 │ • Execute orchestrator across full 457-page corpus                    │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ PHASE 3: Cloud Deployment ('Yad Malachi Project')                      │
 │ • Migrate from local test repo to Google Cloud Platform               │
 │ • Deploy Cloud Run worker / task queues for full-scale ingestion      │
 └────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Conclusion

**We have not drifted from our goals.** The mission to produce a high-accuracy, linkable, public-domain digital edition of *Yad Malachi* remains completely intact. The technical changes made in code have significantly increased the precision, determinism, and speed of the pipeline.
