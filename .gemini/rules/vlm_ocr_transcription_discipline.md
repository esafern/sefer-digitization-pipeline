---
description: Enforce literal unconditioned prompts for VLM OCR, region-level cropping, vocabulary parity verification for neural OCR, and coordinate decoupling.
---
# VLM OCR Transcription & Second-Witness Discipline

## 1. Unconditioned Visual Prompts (Preventing Generative Hallucinations)
- When using Multimodal Vision-Language Models (e.g. Gemini 3.6 Flash) for OCR transcription, **never include book titles, author background, or thematic summaries in the prompt**.
- Contextual cues invite the model's generative language prior to override visual perception and recite memorized or related text from elsewhere in the work.
- Use strictly literal, character-level transcription prompts:
  > *"You are a literal OCR reader for 19th-century Hebrew typography. Transcribe the Hebrew text visible in this image crop verbatim line-by-line. Do not assume or infer text outside this image. Output only the raw Hebrew characters."*

## 2. Region-Level Bounded Cropping vs. Full Pages
- Do not pass unconstrained full pages to VLMs for raw transcription; full-page prompts frequently suffer from heading omission, paragraph jumping, and column reordering.
- Always crop to individual section or *klal* bounding boxes (using `klal_page_regions.json`), allowing the vision model to transcribe focused, high-DPI text blocks.

## 3. Vocabulary Parity Verification for Neural Seq2Seq OCR
- Before evaluating any Hugging Face neural OCR checkpoint (e.g. TrOCR):
  1. Verify that native tokenizer files (`tokenizer.json`, `vocab.txt`, or `sentencepiece.bpe.model`) exist in the model repository.
  2. Mathematically verify that `model.config.decoder.vocab_size == tokenizer.vocab_size`.
  3. Never pair a neural checkpoint with an arbitrary third-party tokenizer with mismatched vocabulary dimensions (e.g. pairing a 128k embedding table with a 32k tokenizer), as token IDs will decode into random modern corpus hallucinations or hit premature `[EOS]` stop tokens.

## 4. Coordinate Plane Decoupling for Candidate Witnesses
- Candidate second-witness engines (Kraken, Dicta, VLMs, TrOCR) do **not** need to generate bounding-box coordinates.
- Document AI's bounding boxes are already 100% verified across the corpus; candidate engines only need to output raw Hebrew text, which is sequence-aligned back to the DocAI coordinate plane by `tools/verify_reconstruction_witness.py`.
