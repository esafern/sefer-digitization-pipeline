#!/usr/bin/env python3
"""
[PROTOTYPE] Standalone benchmark script to test a local Hebrew TrOCR model
over our yad-malachi-berlin-sample.pdf and raw DocAI coordinates.

Since TrOCR (Transformer OCR) is a line-level OCR model, running it over a
whole page directly fails. This script solves this elegantly by:
1. Loading the 3-page yad-malachi-berlin-sample.pdf using PyMuPDF.
2. Reading our fresh page_1.json, page_2.json, page_3.json Document AI tokens.
3. Grouping word tokens into horizontal lines using vertical overlap clustering.
4. Rendering high-resolution line crops from the PDF page.
5. Invoking the Hugging Face `cyttic/exp17-trocr-hebrew-synth1m` model to transcribe each line.

Usage:
    python3 tools/test_trocr_benchmark.py --pdf yad-malachi-berlin-sample.pdf --pages 1 2 3
"""
import argparse
import json
import os
import sys
from collections import defaultdict

import fitz  # PyMuPDF

# Ensure we can import from the pipeline library
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pipeline"))
import corpus_io as cio  # noqa: E402


def check_dependencies():
    """Verify that PyTorch and Hugging Face Transformers are installed."""
    try:
        import torch
        from PIL import Image
        from transformers import TrOCRProcessor, VisionEncoderDecoderModel
        return True
    except ImportError:
        print("\n" + "="*70)
        print("Missing Deep Learning Libraries for Local TrOCR Execution!")
        print("="*70)
        print("To run this prototype script locally, please install the following:")
        print("    pip install torch torchvision transformers pillow")
        print("="*70 + "\n")
        return False


def group_words_into_lines(tokens, vertical_overlap_ratio=0.5):
    """
    Cluster word tokens into horizontal text lines using vertical overlap.
    Each token should have x1, y1, x2, y2 normalized coordinates.
    """
    # Sort tokens primarily by y1, secondarily by x1
    sorted_toks = sorted(tokens, key=lambda t: (t["y1"], t["x1"]))
    lines = []

    for tok in sorted_toks:
        # Filter out empty text or page numbers/headers that are very small
        if not tok.get("text") or tok["text"].isdigit():
            continue

        placed = False
        tok_height = tok["y2"] - tok["y1"]

        # Try to place the token in an existing line
        for line in lines:
            # Calculate vertical overlap between token and existing line bounds
            line_y1 = min(t["y1"] for t in line)
            line_y2 = max(t["y2"] for t in line)
            line_height = line_y2 - line_y1

            overlap_y1 = max(tok["y1"], line_y1)
            overlap_y2 = min(tok["y2"], line_y2)
            overlap = max(0.0, overlap_y2 - overlap_y1)

            min_h = min(tok_height, line_height)
            if min_h > 0 and (overlap / min_h) >= vertical_overlap_ratio:
                line.append(tok)
                placed = True
                break

        if not placed:
            # Create a new line
            lines.append([tok])

    # For each line, sort words from right to left (since Hebrew is RTL)
    sorted_lines = []
    for line in lines:
        sorted_line = sorted(line, key=lambda t: t["x1"], reverse=True)
        sorted_lines.append(sorted_line)

    # Sort lines from top to bottom
    sorted_lines.sort(key=lambda line: min(t["y1"] for t in line))
    return sorted_lines


def get_line_bounding_box(line, padding=0.005):
    """Calculate the combined normalized bounding box for a group of words."""
    x1 = min(t["x1"] for t in line)
    y1 = min(t["y1"] for t in line)
    x2 = max(t["x2"] for t in line)
    y2 = max(t["y2"] for t in line)

    # Apply slight padding to avoid clipping the tops/bottoms of letters
    return {
        "x1": max(0.0, x1 - padding),
        "y1": max(0.0, y1 - padding),
        "x2": min(1.0, x2 + padding),
        "y2": min(1.0, y2 + padding),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pdf", default="yad-malachi-berlin-sample.pdf", help="Sample PDF file")
    parser.add_argument("--pages", nargs="+", type=int, default=[1, 2, 3], help="1-indexed pages of the sample PDF")
    parser.add_argument("--model", default="cyttic/exp17-trocr-hebrew-synth1m", help="Hugging Face TrOCR model path")
    parser.add_argument("--dpi", type=int, default=300, help="DPI for rendering crops")
    args = parser.parse_args()

    # Check local file existence
    if not os.path.exists(args.pdf):
        sys.exit(f"Error: Sample PDF file not found at: {args.pdf}\nRun page extraction first.")

    for p in args.pages:
        json_path = f"page_{p}.json"
        if not os.path.exists(json_path):
            sys.exit(f"Error: Required fresh raw DocAI JSON file not found: {json_path}\nRun extract_docai_pages.py first.")

    # Check dependencies before loading HF transformers
    has_ml_libs = check_dependencies()

    print(f"Loading PDF: {args.pdf}...")
    doc = fitz.open(args.pdf)

    # Load TrOCR model if libraries are present
    processor, model, device = None, None, None
    if has_ml_libs:
        import torch
        from transformers import TrOCRProcessor, VisionEncoderDecoderModel

        print(f"Loading local TrOCR model '{args.model}' from Hugging Face...")
        print("(Note: This will download several hundred MBs on the first execution)")
        
        # Load processor and model
        # Using microsoft/trocr-base-printed for image processing and dicta-il/dictabert for Hebrew tokenization
        from transformers import AutoTokenizer, ViTImageProcessor
        image_processor = ViTImageProcessor.from_pretrained("microsoft/trocr-base-printed")
        tokenizer = AutoTokenizer.from_pretrained("dicta-il/dictabert")
        processor = TrOCRProcessor(image_processor=image_processor, tokenizer=tokenizer)
        model = VisionEncoderDecoderModel.from_pretrained(args.model)
        
        # Use GPU/MPS if available for fast inference
        if torch.cuda.is_available():
            device = "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"
            
        model.to(device)
        print(f"Model loaded successfully on device: {device}\n")

    # Process each page
    for p in args.pages:
        # 1-indexed page number in the sample matches 0-indexed page index of sample PDF
        pdf_page_idx = p - 1
        if pdf_page_idx >= len(doc):
            print(f"Skipping page {p} (out of bounds)")
            continue

        page = doc[pdf_page_idx]
        width, height = page.rect.width, page.rect.height
        print(f"\n" + "="*50)
        print(f"PROCESSING PAGE {p} (PDF index {pdf_page_idx}) - resolution: {width}x{height} pt")
        print("="*50)

        # Load DocAI raw coordinates
        with open(f"page_{p}.json", "r", encoding="utf-8") as f:
            tokens = json.load(f)

        print(f"Loaded {len(tokens)} word tokens. Grouping into horizontal lines...")
        lines = group_words_into_lines(tokens)
        print(f"Clustered words into {len(lines)} distinct lines.\n")

        for idx, line in enumerate(lines[:15]):  # Show first 15 lines as prototype test
            # Calculate bounding box for the line
            box = get_line_bounding_box(line)
            
            # Formulate the expected baseline text from DocAI tokens
            docai_baseline = " ".join(t["text"] for t in line)

            # Define crop rectangle in PDF points
            rect = fitz.Rect(
                box["x1"] * width,
                box["y1"] * height,
                box["x2"] * width,
                box["y2"] * height
            )

            # Render high-resolution line crop (dpi scale)
            zoom = args.dpi / 72.0
            matrix = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=matrix, clip=rect)

            print(f"Line {idx+1:02d}: Bounding box {rect}")
            print(f"  [DocAI Raw Baseline]: {docai_baseline}")

            if has_ml_libs:
                from PIL import Image
                import torch

                # Convert PyMuPDF pixmap to PIL Image
                img_data = pix.tobytes("png")
                from io import BytesIO
                img = Image.open(BytesIO(img_data)).convert("RGB")

                # Process image through TrOCR
                pixel_values = processor(images=img, return_tensors="pt").pixel_values.to(device)
                
                # Generate token IDs
                with torch.no_grad():
                    generated_ids = model.generate(pixel_values)
                
                # Decode to string
                trocr_transcription = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
                print(f"  [Local TrOCR Output]: {trocr_transcription}")
            else:
                print(f"  [Local TrOCR Output]: (Install torch/transformers to generate local transcription!)")
            print("-" * 50)

    doc.close()


if __name__ == "__main__":
    main()
