# Yad Malachi Textual Pipeline: Time & Cost Estimates

## 1. Executive Summary

This document provides realistic engineering estimates for time and direct compute/API costs across two phases:
1. **Phase 2 Development (Steps 3 & 4: Demo Package & NLI Validation Prep)**
2. **Full Production Processing of Multiple Yad Malachi Editions**

---

## 2. Phase 2 Development (Steps 3 & 4: Demo Package & NLI Prep)

### A. Operational Scope
* Full base text extraction from `test_page.pdf` (100% clean computer-typeset text layer).
* Single witness OCR generation (via Tesseract `heb` / Document AI) for `test_page.pdf`.
* Multi-page chunking & difflib sequence alignment harness.
* NLI Demonstration Package & visual review UI dashboard for R. Ezra Shvat.

### B. Time & Cost Breakdown

| Component | Engineering / Execution Time | Direct API / Infrastructure Cost |
| :--- | :---: | :---: |
| **Phase 2A (Base Text + 1 OCR Witness Stream)** | ~4–6 Hours | < $0.10 (Document AI) |
| **Phase 2B (Multi-Page Chunking & Diff Harness)** | ~6–8 Hours | $0.00 (Local Execution) |
| **Phase 2C (NLI Demo Package & Review UI)** | ~6–8 Hours | < $0.05 (Gemini Flash) |
| **TOTAL** | **~16–22 Hours** (~2–3 Days) | **< $1.00 Total** |

---

## 3. Full Production Processing of Multiple Yad Malachi Editions

### A. Corpus Scale & Parameters

| Edition / Printing | Typeface / Script | Pages | OCR Passes per Page |
| :--- | :--- | :---: | :---: |
| **Livorno 1766–7** (*Editio Princeps*) | Rashi Body / Square Lemmas | ~457 | 2 (Jochre / Rashi Engine + Dicta) |
| **Berlin 1857** (NLI Copy) | Clean Square Type | ~337 | 3 (Document AI + Tesseract + Dicta) |
| **Przemyśl 1877** (Scan A & B) | Clean Square Type | ~491 | 3 (Document AI + Tesseract + Dicta) |
| **Przemyśl 1888** | Clean Square Type | ~373 | 3 (Document AI + Tesseract + Dicta) |
| **TOTAL CORPUS** | **4 Editions / 5 Scans** | **~1,660 Pages** | **~4,980 Total OCR Passes** |

### B. Direct Compute & API Costs (Google Cloud Platform)

```
  ┌─────────────────────────┬───────────────────────────────┬────────────────┐
  │ Component               │ Usage / Operations            │ Estimated Cost │
  ├─────────────────────────┼───────────────────────────────┼────────────────┤
  │ Document AI OCR         │ 1,660 pages × $0.0015/page    │ $2.49          │
  │ Gemini 3.6 Flash Vision │ ~5,000 crop adjudications     │ $0.75 – $1.50  │
  │ GCS Storage & Cloud Run │ 1,660 pages batch compute     │ $5.00 – $10.00 │
  ├─────────────────────────┼───────────────────────────────┼────────────────┤
  │ TOTAL CLOUD API COST    │ Full 1,660-Page Multi-Edition │ $10.00 – $15.00│
  └─────────────────────────┴───────────────────────────────┴────────────────┘
```

### C. Pipeline Execution Time (Automated Cloud Batch)
* **Document AI Asynchronous Batch Processing**: ~15–20 minutes.
* **Parallel Cloud Run / ThreadPool Adjudication**: ~20–30 minutes.
* **Total Automated Pipeline Execution Time**: **< 1 Hour** for the entire 1,660-page corpus.

### D. Live Empirical Benchmark Metrics (Page 0 Execution)
* **Total Spatial Tokens**: 761 tokens (`test_page.pdf` Page 0).
* **Base Text**: Clean Document AI spatial Hebrew text.
* **Witness Text**: Full-page Tesseract `heb` OCR stream.
* **Identified Conflicts**: 103 textual divergences (**13.5% conflict rate**).
* **Parallel Adjudication Time**: 174.21s (~2.9 minutes) for all 103 image crops evaluated concurrently (`max_workers=5`).
* **Average Latency Per Conflict**: ~1.69s per crop.

### E. Human Expert Review (Torah Scholar / Talmid Chacham)
* **Scope**: Reviewing only the flagged `UNCERTAIN` conflict set (~100–200 complex paleographic readings across all 457 collation points).
* **Review Time**: **~5–10 Hours** total (versus 25–45 hours to proofread a single edition from scratch).
* **Estimated Review Cost**: **~$150 – $350** total.

---

## 4. Key Takeaways

1. **Phase 2 Development Cost**: Under **$1.00** in direct API costs and **~16–22 hours** of development time to deliver the complete NLI Demonstration Package for R. Ezra Shvat.
2. **Full Production Cost**: Less than **$15.00 total in direct Google Cloud API/compute costs** to run the entire 1,660-page, 4-edition corpus through multi-engine OCR and Gemini visual adjudication.
3. **Labor Efficiency**: Collapses human proofreading from over 100+ hours down to **5–10 hours of targeted expert review**.
