---
description: Enforce direct LLM linguistic adjudication, visual PDF image verification, and strict prohibition of Python heuristic checkers for Rabbinic Hebrew/Aramaic text.
---
# Rabbinic Text OCR Adjudication & Visual Verification Rules

## 1. Direct LLM Linguistic Review (No Python Heuristics)
- **Do NOT** use Python scripts, regex patterns, or hardcoded spell-check heuristics to identify typos or suspicious words in Rabbinic Hebrew/Aramaic text.
- Evaluate word and sentence validity directly using LLM linguistic knowledge of Rabbinic idioms, Aramaic verb forms, and Rabbinic acronyms.
- Use Python **only** for deterministic extraction and index generation (e.g., `build_lexicon.py`).

## 2. Visual Image Ground-Truth Comparison
- For any flagged item, textual ambiguity, or suspected corruption, inspect the high-resolution scanned page image directly (`view_file` on `.png` images in `images/` or `images/pdf_pages/`).
- Compare the scanned printed image line-by-line with the master text file.

## 3. Audit for Structural Transcription Artifacts
- Check for **chunking/stitching duplications** (where content from one section header accidentally copies into the next).
- Check for **running header bleed** (where top-margin running headers like book/chapter titles get merged into body sentences).

## 4. Mandatory Methodological Reporting
- Always state explicitly in outputs:
  - Exact file paths used (e.g., `full_text_cleaned_goal.txt`, `lexicon.txt`, `page_21.png`).
  - Tools and method applied.
  - Step-by-step adjudication work.
