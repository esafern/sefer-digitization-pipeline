# Yad Malachi Textual Pipeline: Low-Level Current State & Architecture

## 1. Executive Summary

This document provides a low-level technical overview of the current execution state of the **Yad Malachi Textual Pipeline** repository as of July 2026. The pipeline handles Document AI spatial token parsing, text-to-token sequence alignment, high-DPI PDF raster cropping, SHA-256 SQLite caching, and multi-threaded Gemini multimodal AI visual adjudication.

---

## 2. Low-Level Component Architecture

### A. Token Parsing & Bounding Box Extraction (`extract_token_bounding_boxes`)
* **Input**: Document AI spatial JSON schema (`pages[].tokens[]`).
* **Logic**: Iterates over tokens, extracts text substring via `textAnchor.textSegments[].startIndex/endIndex`, and derives normalized bounding boxes:
  $$\text{xmin} = \min(x_v), \quad \text{xmax} = \max(x_v), \quad \text{ymin} = \min(y_v), \quad \text{ymax} = \max(y_v)$$
* **Output**: Array of dicts: `[{"text": "...", "bbox": {"xmin": ..., "ymin": ..., "xmax": ..., "ymax": ...}}]`.

### B. Sequence Matching & Word Normalization (`align_text_to_tokens`)
* **Problem Solved**: Prevents spatial alignment drift caused by punctuation or acronym expansions (e.g., base text `"לומד"` vs manuscript token `"למ\"ד"`).
* **Algorithm**:
  1. Filter tokens to those containing word characters (`re.search(r'\w', t["text"])`).
  2. Strip non-word characters from base words and token strings (`re.sub(r'[^\w]', '', ...)`).
  3. Execute `difflib.SequenceMatcher(None, clean_base_words, clean_tokens)`.
  4. Map base word index `clean_base_indices[i1 + k]` to exact manuscript token index `token_indices[j1 + k]`.

### C. Raster Region Cropping (`crop_pdf_bounding_box`)
* **Engine**: PyMuPDF (`fitz`).
* **DPI**: 300 DPI high-resolution rendering.
* **Padding**: Relative padding of `0.02` (2% of page width/height) with boundary clamping `[0.0, 1.0]`.
* **Output**: PNG image byte array (`img_bytes`).

### D. SQLite Caching Layer (`init_cache`, `get_cached_decision`, `cache_decision`)
* **Database**: `adjudication_cache.db`.
* **Table Schema**: `cache (crop_hash TEXT PRIMARY KEY, decision_json TEXT)`.
* **Hash Function**: `hashlib.sha256(crop_bytes).hexdigest()`.
* **Concurrency Safety**: Thread-safe per-call connections with `timeout=10.0`.
* **Latency**: Bypasses network API call for cache hits in `< 1ms`.

### E. Multimodal AI Adjudication & Resilience (`adjudicate_conflict_with_gemini`)
* **SDK**: `google.genai` Client.
* **Model Fallback Chain**: Primary: `gemini-3.6-flash`, Secondary: `gemini-3.5-flash`.
* **Resilience**: Exponential backoff (`(2 ** attempt) * 2` seconds) handling HTTP `503 UNAVAILABLE` / `429 RATE_LIMIT`.
* **Guardrail Prompt**: Restricts response to structured JSON schema (`selected_option`, `transcription_found`, `confidence`, `reasoning`).

### F. Multi-Threaded Execution (`run_pipeline`)
* **Executor**: `concurrent.futures.ThreadPoolExecutor(max_workers=5)`.
* **Process**: Dispatches conflict crops asynchronously and collects ordered results via `as_completed`.

---

## 3. Verified Diagnostic Benchmark & Rabbinic Acronym Finding

* **Target PDF**: `test_page.pdf` (Page 0, diagnostic test sample page from *Tzofnat Paneach* on Kiddushin 2a; computer-typeset vector PDF providing a zero-OCR-noise spatial baseline)
* **Target JSON**: `./document_jsons/test_page-0.json` (761 tokens)
* **Target Conflict**: `Base[1]` (`"לומד"`) vs `Witness[1]` (`"לומר"`)
* **Mapped Token**: Token #21 (`"למ\"ד"`), BBox `{'xmin': 0.70077336, 'ymin': 0.20807062, 'xmax': 0.74122548, 'ymax': 0.22404371}`

### Two-Phase Text Ingestion Strategy
1. **Phase 2A (`test_page.pdf`)**: Uses the clean vector text layer as the Base stream, requiring only **one newly OCR'd witness text stream** to diff against for testing.
2. **Phase 2B (`berlin_square.pdf`)**: For the 1857 Berlin scan (where embedded OCR is far less reliable due to 19th-century print artifacts), the pipeline will generate **multiple independent OCR passes** (Document AI, Tesseract, Dicta) for consensus voting and visual adjudication.
* **Gemini Response (With Rabbinic Context Instruction & True Expansion)**:
  ```json
  {
    "selected_option": "C",
    "transcription_found": ": למ\"ד",
    "confidence": 0.98,
    "reasoning": "In Rabbinic commentary context (such as 'למ\"ד חליצה קנין'), the standard acronym למ\"ד expands to 'למאן דאמר' (according to the one who says). The image clearly shows the acronym למ\"ד with gershayim."
  }
  ```
* **Critical Rabbinic & System Insights**:
  1. **Semantic Context Matters**: Without Rabbinic domain instructions, the model mistook the acronym `למ"ד` for the literal letter name "Lamed".
  2. **Surrounding Sentence Validation**: When provided with the full sentence context (`גליון: למ"ד חליצה קנין ביר"ש פ"א ופ"ג דיבמות`), Gemini correctly parsed `למ"ד` as **למאן דאמר** (*Le-man D'amar*) with 0.98 confidence.
  3. **Prompt Specification**: The prompt now explicitly instructs the model to perform Rabbinic semantic/acronym analysis and prevents literal letter-name misinterpretations.

---

## 4. File Manifest

* [`orchestrator.py`](file:///Users/ericsafern/work/yad-malachi/yad-malachi-pipeline/orchestrator.py): Main execution engine.
* [`CASE-YAD-MALACHI.md`](file:///Users/ericsafern/work/yad-malachi/yad-malachi-pipeline/CASE-YAD-MALACHI.md): Master proposal and rationale.
* [`LOW-LEVEL-CURRENT-STATE.md`](file:///Users/ericsafern/work/yad-malachi/yad-malachi-pipeline/LOW-LEVEL-CURRENT-STATE.md): Technical current state reference (this document).
* `test_page.pdf`: Diagnostic test sample page from *Tzofnat Paneach* (Kiddushin 2a).
* `berlin_square.pdf`: Full multi-page PDF scan of *Yad Malachi* (Berlin 1857 square edition, from NLI holdings).
* `adjudication_cache.db`: SQLite cache database.
* `./document_jsons/`: Document AI spatial JSON outputs (`test_page-0.json` .. `test_page-41.json`).
