import time
import os
import sys
import json
import difflib
import traceback
import fitz  # PyMuPDF
from google import genai
from google.genai import types

# =====================================================================
# CONFIGURATION & TEST DEFAULTS
# =====================================================================
TEST_PDF = "test_page.pdf"
PAGE_INDEX = 0

# Sample text streams with an intentional variant to trigger conflict adjudication
BASE_TEXT = "יד מלאכי כלל א רוצה לומר"
WITNESS_TEXT = "יד מלאכי כלל א רוצה ללמוד"


# =====================================================================
# PIPELINE FUNCTIONS
# =====================================================================

def extract_token_bounding_boxes(doc_ai_json, page_idx=0):
    """
    Extracts word tokens and their normalized bounding boxes (0.0 - 1.0)
    from Document AI JSON schema.
    """
    pages = doc_ai_json.get("pages", [])
    if not pages or page_idx >= len(pages):
        return []

    page = pages[page_idx]
    doc_text = doc_ai_json.get("text", "")
    extracted_tokens = []

    for token in page.get("tokens", []):
        layout = token.get("layout", {})
        text_anchor = layout.get("textAnchor", {})
        segments = text_anchor.get("textSegments", [])

        # Reconstruct token text from segment offsets
        token_text = ""
        for seg in segments:
            start = int(seg.get("startIndex", 0))
            end = int(seg.get("endIndex", 0))
            token_text += doc_text[start:end]

        vertices = layout.get("boundingPoly", {}).get("normalizedVertices", [])
        if vertices:
            xs = [v.get("x", 0.0) for v in vertices]
            ys = [v.get("y", 0.0) for v in vertices]
            bbox = {
                "xmin": min(xs),
                "ymin": min(ys),
                "xmax": max(xs),
                "ymax": max(ys)
            }
            extracted_tokens.append({
                "text": token_text.strip(),
                "bbox": bbox
            })

    return extracted_tokens


def crop_pdf_bounding_box(pdf_path, page_num, bbox, padding=0.02):
    """
    Crops a specific bounding box region out of a PDF page using PyMuPDF (fitz)
    and returns the cropped PNG image bytes.
    """
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_num)
    rect_page = page.rect
    width, height = rect_page.width, rect_page.height

    # Convert normalized (0.0-1.0) coordinates to absolute points
    xmin = max(0.0, bbox["xmin"] - padding) * width
    ymin = max(0.0, bbox["ymin"] - padding) * height
    xmax = min(1.0, bbox["xmax"] + padding) * width
    ymax = min(1.0, bbox["ymax"] + padding) * height

    crop_rect = fitz.Rect(xmin, ymin, xmax, ymax)
    pix = page.get_pixmap(clip=crop_rect, dpi=300)
    img_bytes = pix.tobytes("png")
    doc.close()
    return img_bytes


def adjudicate_conflict_with_gemini(crop_bytes, option_a, option_b):
    """
    Sends the cropped PNG bytes to Gemini 2.5/3.5 Flash to visually resolve 
    the variant reading between Option A and Option B.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is missing.")

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are an expert Hebrew paleographer and textual critic analyzing a printed or handwritten Hebrew source.

Examine the attached image crop very carefully.
Determine which of the following two candidate readings matches the printed text in the image:

Option A: "{option_a}"
Option B: "{option_b}"

Respond ONLY with JSON using this structure:
{{
  "selected_option": "A" or "B" or "UNCERTAIN",
  "transcription_found": "exact text visible in image",
  "confidence": 0.0 to 1.0,
  "reasoning": "brief visual explanation"
}}
"""

max_retries = 4
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=[
                    types.Part.from_bytes(data=crop_bytes, mime_type="image/png"),
                    prompt
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            return response.text
            
        except Exception as e:
            # Catch capacity bounces (503) and rate limits (429)
            if "503" in str(e) or "429" in str(e):
                if attempt < max_retries - 1:
                    sleep_time = (2 ** attempt) * 2  # Sleeps: 2s, 4s, 8s...
                    print(f"  -> API busy (503). Backing off for {sleep_time}s (Attempt {attempt + 1}/{max_retries})...")
                    time.sleep(sleep_time)
                else:
                    print("  -> Max retries hit. API is completely saturated.")
                    raise e
            else:
                # If it's a 404 or some other fatal error, crash immediately
                raise e



def run_pipeline(pdf_path, page_idx, base_text, witness_text, doc_ai_json):
    """
    Main orchestration routine: diffs texts, locates spatial coordinates,
    crops regions, and invokes Gemini multimodal adjudication.
    """
    print("\n--- [STEP 1] Extracting Spatial Coordinates ---")
    tokens = extract_token_bounding_boxes(doc_ai_json, page_idx)
    print(f"Loaded {len(tokens)} spatial tokens from Document AI.")

    print("\n--- [STEP 2] Diffing Text Streams ---")
    matcher = difflib.SequenceMatcher(None, base_text.split(), witness_text.split())
    opcodes = matcher.get_opcodes()

    conflicts_found = 0

    for tag, i1, i2, j1, j2 in opcodes:
        if tag in ("replace", "delete", "insert"):
            conflicts_found += 1
            base_segment = " ".join(base_text.split()[i1:i2])
            witness_segment = " ".join(witness_text.split()[j1:j2])

            print(f"\n[Conflict #{conflicts_found}] Tag: '{tag}'")
            print(f"  Base Reading:    '{base_segment}'")
            print(f"  Witness Reading: '{witness_segment}'")

            # Fallback bbox to center of page if token alignment is loose
            target_bbox = {"xmin": 0.2, "ymin": 0.2, "xmax": 0.8, "ymax": 0.8}

            # Attempt spatial match against extracted Document AI tokens
            for tok in tokens:
                if any(w in tok["text"] for w in base_segment.split() if len(w) > 1):
                    target_bbox = tok["bbox"]
                    break

            print(f"  Target BBox:     {target_bbox}")

            # Crop image
            print("  Cropping PDF region...")
            crop_bytes = crop_pdf_bounding_box(pdf_path, page_idx, target_bbox)

            # Send to Gemini
            print("  Submitting crop to Gemini for visual adjudication...")
            decision = adjudicate_conflict_with_gemini(crop_bytes, base_segment, witness_segment)
            print("  Adjudication Result:")
            print(f"  {decision}")

    if conflicts_found == 0:
        print("No textual divergences found between base and witness texts.")


# =====================================================================
# DIAGNOSTIC RUNNER (MAIN ENTRY POINT)
# =====================================================================

if __name__ == "__main__":
    print("=" * 60, flush=True)
    print("ORCHESTRATOR DIAGNOSTIC RUNNER", flush=True)
    print("=" * 60, flush=True)

    json_path = "./document_jsons/test_page-0.json"

    # 1. Verify Target PDF
    print(f"[1/5] Checking target PDF ('{TEST_PDF}')...", end=" ", flush=True)
    if not os.path.exists(TEST_PDF):
        print("FAILED!")
        print(f"  -> ABSOLUTE PATH SEARCHED: {os.path.abspath(TEST_PDF)}")
        print("  -> ERROR: PDF file missing in execution directory.")
        sys.exit(1)
    print("FOUND.", flush=True)

    # 2. Verify Spatial JSON
    print(f"[2/5] Checking spatial JSON ('{json_path}')...", end=" ", flush=True)
    if not os.path.exists(json_path):
        print("FAILED!")
        print(f"  -> ABSOLUTE PATH SEARCHED: {os.path.abspath(json_path)}")
        print("  -> ERROR: JSON spatial map file missing.")
        sys.exit(1)
    print("FOUND.", flush=True)

    # 3. Inspect JSON Payload
    print("[3/5] Loading Document AI JSON...", end=" ", flush=True)
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            real_doc_ai_json = json.load(f)
        pages_count = len(real_doc_ai_json.get("pages", []))
        tokens_count = len(real_doc_ai_json.get("pages", [{}])[0].get("tokens", [])) if pages_count > 0 else 0
        print(f"SUCCESS. (Parsed {pages_count} page(s), {tokens_count} tokens)", flush=True)
    except Exception as e:
        print("FAILED!")
        print(f"  -> Exception while loading JSON: {e}")
        traceback.print_exc()
        sys.exit(1)

    # 4. Inspect Text Streams
    print("[4/5] Checking text streams for conflicts...", flush=True)
    print(f"  -> Base Text Length:    {len(BASE_TEXT)} chars")
    print(f"  -> Witness Text Length: {len(WITNESS_TEXT)} chars")

    if BASE_TEXT == WITNESS_TEXT:
        print("  -> WARNING: Base text and Witness text are 100% IDENTICAL.")
        print("  -> Pipeline exiting because no OCR conflicts exist to resolve.")
        sys.exit(0)

    # 5. Execute Pipeline
    print("[5/5] Launching adjudication engine...", flush=True)
    print("-" * 60, flush=True)
    try:
        run_pipeline(TEST_PDF, PAGE_INDEX, BASE_TEXT, WITNESS_TEXT, real_doc_ai_json)
        print("-" * 60, flush=True)
        print("ORCHESTRATOR COMPLETE.", flush=True)
    except Exception as e:
        print("\n" + "!" * 60, flush=True)
        print("CRITICAL EXCEPTION DURING PIPELINE EXECUTION:", flush=True)
        print("!" * 60, flush=True)
        traceback.print_exc()
        sys.exit(1)
