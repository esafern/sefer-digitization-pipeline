# Yad Malachi Pipeline: NLI Validation Strategy & Stakeholder Roadmap

## 1. Executive Summary

This document establishes the strategic validation path for the **Yad Malachi Textual Pipeline**, detailing stakeholder relationships, data provenance, and the gateway to publication in digital libraries (Sefaria / Halachipedia).

---

## 2. Key Stakeholders & Strategic Relationships

```
 ┌─────────────────────────────────────────────────────────────────────────┐
 │                        INDEPENDENT BUILD-OUT                            │
 │  Developed independently without prior authorization or buy-in needed   │
 │  from Sefaria.                                                          │
 └────────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
 ┌─────────────────────────────────────────────────────────────────────────┐
 │                   GATEWAY: NATIONAL LIBRARY OF ISRAEL (NLI)             │
 │  Validation Milestone: Presentation to R. Ezra Shvat (NLI domain        │
 │  expert & rare books/manuscripts specialist).                           │
 └────────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
 ┌─────────────────────────────────────────────────────────────────────────┐
 │                     PUBLICATION: SEFARIA INGESTION                      │
 │  Present NLI-validated text to Sefaria to resolve 287 dead-end          │
 │  citations (#1 requested public-domain work).                           │
 └─────────────────────────────────────────────────────────────────────────┘
```

### A. National Library of Israel (NLI) & Provenance
* **Domain Validation Gateway**: The primary milestone prior to external distribution is validation by **R. Ezra Shvat** (senior domain expert and bibliographer at the National Library of Israel).
* **Scan Provenance**: The full multi-page PDF scan of *Yad Malachi* ([`berlin_square.pdf`](file:///Users/ericsafern/work/yad-malachi/yad-malachi-pipeline/berlin_square.pdf), Berlin 1857 square edition) originates directly from the physical holdings of the **NLI** (carrying the historic Hazanovitz collection provenance stamp). Note: [`test_page.pdf`](file:///Users/ericsafern/work/yad-malachi/yad-malachi-pipeline/test_page.pdf) is a separate diagnostic sample page from *Tzofnat Paneach* (Kiddushin 2a) used for initial local engine testing.
* **Alignment**: Transforming NLI's physical collection scans into a clean, linkable, structured digital text creates a direct alignment between NLI holdings and modern digital scholarship.

### B. Sefaria Ingestion Strategy
* **Independent Execution**: The project operates independently of Sefaria.
* **Turn-Key Value Proposition**: Delivering a fully collated, NLI-validated digital text of *Yad Malachi* resolves Sefaria's **#1 public-domain gap** (cited 287 times inside existing Sefaria texts with 0 linkable targets). Sefaria receives a zero-friction, pre-validated asset ready for schema ingestion.

---

## 3. The NLI Demonstration Package Requirements

To prepare for the validation meeting with R. Ezra Shvat, the pipeline build-out will produce an empirical **NLI Demonstration Package**:

1. **Visual Grounding Demonstration**:
   * Side-by-side display of NLI original scan page $\rightarrow$ 300 DPI PyMuPDF raster crop $\rightarrow$ candidate OCR readings $\rightarrow$ Gemini multimodal visual adjudication.
2. **Zero-Hallucination Guardrail Verification**:
   * Concrete proof that the adjudication engine outputs `UNCERTAIN` and paleographic reasoning whenever candidate readings fail to match manuscript raster pixels.
3. **Rabbinic Abbreviation & Acronym Expansion Engine**:
   * **Case Study**: In `test_page.pdf` Page 0 (`גליון: למ"ד חליצה קנין ביר"ש פ"א ופ"ג דיבמות`), **`למ"ד`** represents **למאן דאמר** (*Le-man D'amar*). 
   * **Semantic Prompting**: When provided with explicit Rabbinic domain rules and sentence context, Gemini correctly recognized `למ"ד` as **למאן דאמר** with 0.98 confidence, rejecting literal letter-name misinterpretations ("Lamed").
   * **Requirement**: System prompt and candidate generation include Rabbinic acronym expansion rules (Dicta Maivin / BEREL) to validate true expansions (`למאן דאמר`).
4. **Collation & Variant Apparatus**:
   * Clean collation showcasing genuine historical print variants between *Livorno 1766* (Rashi type), *Berlin 1857* (Square type), and *Przemyśl 1877/1888* (Square type).

---

## 4. Operational Milestones

* [x] **Phase 1**: Local controlled experiment in [`orchestrator.py`](file:///Users/ericsafern/work/yad-malachi/yad-malachi-pipeline/orchestrator.py) with spatial alignment, `ThreadPoolExecutor` multi-threading, and SHA-256 SQLite caching.
* [ ] **Phase 2A**: Expand ingestion across full multi-page sections of `test_page.pdf` and `./document_jsons/`.
* [ ] **Phase 2B**: Build NLI Demonstration Package & review dashboard.
* [ ] **Phase 2C**: NLI Domain Review with R. Ezra Shvat.
* [ ] **Phase 3**: Google Cloud Platform migration (`Yad Malachi Project`) and Sefaria ingestion submission.
