# Yad Malachi Pipeline: Conflict Analysis, Reconciliation & Human Review

## 1. Executive Summary

This document provides a concrete breakdown of how the pipeline distinguishes **Auto-Approved Consensus Chunks** from **Conflicting Chunks**, how AI visual adjudication reconciles minor OCR errors, and how complex layout disruptions are routed to the **Torah Scholar Approval Portal** for human verification.

---

## 2. Auto-Approved Consensus Chunks (~90% of Page Text)

When multiple OCR passes agree 100% on a word or sentence chunk, the pipeline **auto-accepts** the text immediately. No AI vision calls are made, guaranteeing zero API spend and zero latency for clean text.

### Real Examples (Page 0 Execution)
* **Consensus Chunk 1**:  
  `וקונה את עצמה בחליצה. גליון: למ"ד חליצה קנין ביר"ש פ"א ופ"ג דיבמות`  
  *Status*: 100% Identical across engines $\rightarrow$ **Auto-Accepted (0 API Calls)**.

* **Consensus Chunk 2**:  
  `סוף ד"ה בפרוטה וכו' לפדיון הבן וכו' גליון: אך באמת למה לא נימא דגבי`  
  *Status*: 100% Identical across engines $\rightarrow$ **Auto-Accepted (0 API Calls)**.

---

## 3. Conflicting Chunks & How They Are Reconciled

When OCR engines disagree, the pipeline crops the 300 DPI raster image and submits it to the AI vision engine (Gemini 3.6 Flash).

```
 ┌─────────────────────────────────────────────────────────────────────────┐
 │                            CONFLICT TAXONOMY                            │
 ├─────────────────────────────────────────────────────────────────────────┤
 │ 1. Minor OCR Character Confusion  ──► Reconciled by AI Vision (Auto)    │
 │ 2. Rabbinic Acronym Expansion     ──► Reconciled by AI Vision (Auto)    │
 │ 3. Page Layout / Footnote Split  ──► Routed to Torah Scholar Portal    │
 └─────────────────────────────────────────────────────────────────────────┘
```

### Type 1: Minor OCR Character Confusion (Reconciled Automatically)
* **Base OCR**: `"דף ב'"` (Correct gershayim `'`)
* **Witness OCR (Tesseract)**: `'דף בי'` (Misread gershayim `'` as letter `י`)
* **AI Visual Inspection**: Inspects the 300 DPI crop, verifies the gershayim mark on the printed page, selects `"דף ב'"`, and assigns **98% confidence**.
* **Outcome**: **Auto-Accepted into final text**.

### Type 2: OCR Letter Swap & Noise (Reconciled Automatically)
* **Base OCR**: `"תוס'"` (*Tosafot*)
* **Witness OCR (Tesseract)**: `".4 תופ'"` (Misread `ס` as `פ` and inserted noise `.4`)
* **AI Visual Inspection**: Inspects the manuscript crop, identifies the standard Rabbinic heading `"תוס'"`, rejects the misreading `".4 תופ'"`, and assigns **95% confidence**.
* **Outcome**: **Auto-Accepted into final text**.

---

## 4. Complex Conflicts Requiring Human Review

Certain conflicts cannot and should not be auto-accepted by AI alone. These are automatically flagged for **Human Torah Scholar Review**:

### Type 3: Page Layout, Column Wrapping & Marginal Footnote Disruption
* **Base OCR**: `מקשה רבינו2 אך באמת למה לא נימא דגבי פדיון הבן` (Main commentary line)
* **Witness OCR**: `[Empty / Wrapped into lower footnote column]`
* **Why They Differed**: Tesseract wrapped the marginal commentary line into a lower footnote block, breaking word alignment between text streams.
* **AI Visual Finding**: Gemini inspects the crop and detects that text boundaries wrap across column borders. It assigns **confidence < 95%** or returns **`UNCERTAIN`**.

### The Torah Scholar Approval Workflow

```
 ┌────────────────────────────────────────────────────────────────────────┐
 │                      TORAH SCHOLAR APPROVAL PORTAL                     │
 ├────────────────────────────────────────────────────────────────────────┤
 │ [ FULL ORIGINAL PAGE SCAN DISPLAYED WITH TARGET REGION HIGHLIGHTED ]   │
 │                                                                        │
 │ Target Region: Line 19, Margin / Footnote Boundary                     │
 │ Base OCR:      מקשה רבינו2 אך באמת למה לא נימא דגבי פדיון הבן         │
 │ Witness OCR:   [Text wrapped into lower footnote block]                │
 │ AI Status:     UNCERTAIN (Confidence: 82% - Column Wrap Detected)      │
 │                                                                        │
 │ 📋 PROMPT: "Please consult the printed critical edition on your desk   │
 │            (e.g., Machon Yerushalayim 2016) to verify text placement." │
 │                                                                        │
 │ [ APPROVE BASE TEXT ]   [ APPROVE WITNESS TEXT ]   [ EDIT MANUALLY ]   │
 └────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Summary Table

| Category | Difference Cause | System Resolution | Human Action Needed? |
| :--- | :--- | :--- | :---: |
| **Consensus Chunk** | Engines agree 100%. | Auto-Accepted (0 API spend). | **No** |
| **Character Confusion** | Faded gershayim / letter swap. | Reconciled by AI Vision ($\ge 95\%$ confidence). | **No** |
| **Acronym Expansion** | Acronym (`למ"ד`) vs Full Phrase. | Reconciled by AI Vision ($\ge 98\%$ confidence). | **No** |
| **Layout / Footnote Split** | Column wrapping / margin split. | Flagged as `UNCERTAIN` ($< 95\%$ confidence). | **Yes (1-Click Portal)** |
