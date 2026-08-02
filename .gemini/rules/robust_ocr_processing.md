---
description: Ensure OCR alignment pipelines use programmatic auto-healing (e.g. restoring skipped words from LLM anchors) rather than hardcoding fixes for displaced text.
---
# Robust OCR Processing

When processing or aligning OCR data (like Document AI) against LLM anchors, NEVER hardcode fixes for specific text displacements or hallucinations. Instead, write programmatic auto-healing logic (e.g., cross-referencing the fuzzy match against the LLM anchor and automatically restoring dropped leading words) so the pipeline remains generic and self-correcting.

**Structural Invariant Mapping:**
Never assume sequential completeness if items might be dropped. Always map extracted anchors back to their true invariant identifiers in the text (e.g., parsing Gematria prefixes or explicit section markers) to detect skipped or missing items mathematically, before assigning sequential IDs.
