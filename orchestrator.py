# [PRODUCTION]
import os
import sys
import json
import difflib
import traceback
import time
import hashlib
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
import fitz  # PyMuPDF
from google import genai
from google.genai import types

# =====================================================================
# CONFIGURATION & TEST DEFAULTS
# =====================================================================
TEST_PDF = "test_page.pdf"
PAGE_INDEX = 0
CACHE_DB = "adjudication_cache.db"

# =====================================================================
# CACHING LAYER
# =====================================================================

def init_cache():
    conn = sqlite3.connect(CACHE_DB)
    conn.execute("CREATE TABLE IF NOT EXISTS cache (crop_hash TEXT PRIMARY KEY, decision_json TEXT)")
    conn.commit()
    conn.close()

def get_cached_decision(crop_bytes):
    crop_hash = hashlib.sha256(crop_bytes).hexdigest()
    conn = sqlite3.connect(CACHE_DB, timeout=10.0)
    cursor = conn.cursor()
    cursor.execute("SELECT decision_json FROM cache WHERE crop_hash = ?", (crop_hash,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def cache_decision(crop_bytes, decision_json):
    crop_hash = hashlib.sha256(crop_bytes).hexdigest()
    conn = sqlite3.connect(CACHE_DB, timeout=10.0)
    conn.execute("INSERT OR REPLACE INTO cache (crop_hash, decision_json) VALUES (?, ?)", (crop_hash, decision_json))
    conn.commit()
    conn.close()

# =====================================================================
# PIPELINE FUNCTIONS
# =====================================================================

def extract_token_bounding_boxes(doc_ai_json, page_idx=0):
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
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_num)
    rect_page = page.rect
    width, height = rect_page.width, rect_page.height

    xmin = max(0.0, bbox["xmin"] - padding) * width
    ymin = max(0.0, bbox["ymin"] - padding) * height
    xmax = min(1.0, bbox["xmax"] + padding) * width
    ymax = min(1.0, bbox["ymax"] + padding) * height

    crop_rect = fitz.Rect(xmin, ymin, xmax, ymax)
    pix = page.get_pixmap(clip=crop_rect, dpi=300)
    img_bytes = pix.tobytes("png")
    doc.close()
    return img_bytes


def adjudicate_conflict_with_gemini(crop_bytes, option_a, option_b, full_context):
    start_t = time.time()
    cached = get_cached_decision(crop_bytes)
    if cached:
        elapsed_ms = (time.time() - start_t) * 1000
        print(f"  -> Cache HIT (retrieved from SQLite in {elapsed_ms:.2f}ms)")
        return cached

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is missing.")

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are an expert Talmudic and Rabbinic textual verification engine analyzing a Hebrew manuscript raster crop.

Surrounding Talmudic/Rabbinic Sentence Context: "{full_context}"

Evaluate the target raster crop against candidate strings / expansions:
Option A: "{option_a}"
Option B: "{option_b}"

CONSTRAINTS:
1. Perform Rabbinic acronym and semantic analysis using the surrounding sentence context.
2. Recognize standard Rabbinic acronyms and abbreviations (e.g., למ"ד = למאן דאמר, ע"א = עמוד א, פ"א = פרק א).
3. Do NOT mistake Rabbinic acronyms (like למ"ד) for the literal spelled-out Hebrew letter name when sentence context indicates a Talmudic abbreviation/phrase.
4. Output "UNCERTAIN" if neither candidate maps deterministically to the pixel array or if semantic constraints are violated.

Respond ONLY with JSON using this structure:
{{
  "selected_option": "A" or "B" or "UNCERTAIN",
  "transcription_found": "exact text visible in image",
  "confidence": 0.0 to 1.0,
  "reasoning": "contextual Rabbinic paleographic explanation"
}}
"""

    models_to_try = ["gemini-3.6-flash", "gemini-3.5-flash"]
    max_retries = 4

    for model_name in models_to_try:
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                        types.Part.from_bytes(data=crop_bytes, mime_type="image/png"),
                        prompt
                    ],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )
                elapsed_s = time.time() - start_t
                print(f"  -> API MISS - Live call to {model_name} completed in {elapsed_s:.2f}s")
                cache_decision(crop_bytes, response.text)
                return response.text
                
            except Exception as e:
                if "503" in str(e) or "429" in str(e):
                    if attempt < max_retries - 1:
                        sleep_time = (2 ** attempt) * 2
                        time.sleep(sleep_time)
                    else:
                        break
                else:
                    raise e
    raise RuntimeError("All configured Gemini models failed due to rate limits or availability.")


def align_text_to_tokens(base_words, tokens):
    import re
    token_indices = [idx for idx, t in enumerate(tokens) if re.search(r'\w', t["text"])]
    clean_tokens = [re.sub(r'[^\w]', '', tokens[idx]["text"]) for idx in token_indices]
    
    clean_base = [re.sub(r'[^\w]', '', w) for w in base_words]
    clean_base_indices = [idx for idx, cb in enumerate(clean_base) if cb]
    clean_base_words = [clean_base[idx] for idx in clean_base_indices]
    
    matcher = difflib.SequenceMatcher(None, clean_base_words, clean_tokens)
    index_map = {}
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                base_word_idx = clean_base_indices[i1 + k]
                index_map[base_word_idx] = token_indices[j1 + k]
        elif tag in ("replace", "delete"):
            for k in range(i2 - i1):
                base_word_idx = clean_base_indices[i1 + k]
                target_tok_idx = token_indices[j1] if j1 < len(token_indices) else len(tokens) - 1
                index_map[base_word_idx] = target_tok_idx
    return index_map


def _process_single_conflict(conf, full_context):
    decision = adjudicate_conflict_with_gemini(
        conf["crop_bytes"],
        conf["base_segment"],
        conf["witness_segment"],
        full_context
    )
    return conf["id"], conf, decision


def run_pipeline(pdf_path, page_idx, base_text, witness_text, doc_ai_json, max_workers=5):
    import subprocess
    pipeline_start = time.time()
    print("\n--- [STEP 1] Extracting Paragraph-Level Spatial Coordinates ---")
    t0 = time.time()
    
    pages = doc_ai_json.get("pages", [])
    page_layout = pages[page_idx] if page_idx < len(pages) else {}
    doc_text = doc_ai_json.get("text", "")

    doc = fitz.open(pdf_path)
    page = doc.load_page(page_idx)
    rect_page = page.rect
    width, height = rect_page.width, rect_page.height

    conflicts = []
    conflicts_found = 0
    all_base_words = []

    print("\n--- [STEP 2] Paragraph-Level OCR Clipping & Local Diffing ---")
    t1 = time.time()

    paragraphs = page_layout.get("paragraphs", [])
    if not paragraphs:
        paragraphs = page_layout.get("blocks", [])

    for p_idx, p in enumerate(paragraphs):
        vertices = p.get("layout", {}).get("boundingPoly", {}).get("normalizedVertices", [])
        if not vertices:
            continue
        xs = [v.get("x", 0.0) for v in vertices]
        ys = [v.get("y", 0.0) for v in vertices]
        p_bbox = {
            "xmin": min(xs),
            "ymin": min(ys),
            "xmax": max(xs),
            "ymax": max(ys)
        }

        # Extract Base text for this paragraph
        seg = p.get("layout", {}).get("textAnchor", {}).get("textSegments", [])
        p_base_text = ""
        for s in seg:
            p_base_text += doc_text[int(s.get("startIndex", 0)):int(s.get("endIndex", 0))]
        p_base_text = p_base_text.strip()
        if not p_base_text:
            continue

        p_base_words = p_base_text.split()
        all_base_words.extend(p_base_words)

        # Crop exact paragraph bounding box from page at 300 DPI
        pad = 0.01
        crop_rect = fitz.Rect(
            max(0.0, p_bbox["xmin"] - pad) * width,
            max(0.0, p_bbox["ymin"] - pad) * height,
            min(1.0, p_bbox["xmax"] + pad) * width,
            min(1.0, p_bbox["ymax"] + pad) * height
        )
        pix = page.get_pixmap(clip=crop_rect, dpi=300)
        temp_crop_png = f"temp_p_{page_idx}_{p_idx}.png"
        pix.save(temp_crop_png)

        res = subprocess.run(["tesseract", temp_crop_png, "stdout", "-l", "heb"], capture_output=True, text=True)
        p_witness_text = res.stdout.strip()
        if os.path.exists(temp_crop_png):
            os.remove(temp_crop_png)

        p_witness_words = p_witness_text.split()

        def has_medial_final_letter(word):
            import re
            clean_w = re.sub(r'[^\wא-ת]', '', word)
            if len(clean_w) <= 1: return False
            return any(c in "ךםןףץ" for c in clean_w[:-1])

        # Perform local SequenceMatcher diffing ONLY within this paragraph
        matcher = difflib.SequenceMatcher(None, p_base_words, p_witness_words)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            is_conflict = tag in ("replace", "delete", "insert")
            
            # If text matches but violates basic Hebrew orthography, force adjudication
            if not is_conflict and tag == "equal":
                for idx_offset in range(i2 - i1):
                    if has_medial_final_letter(p_base_words[i1 + idx_offset]):
                        is_conflict = True
                        break

            if is_conflict:
                conflicts_found += 1
                b_seg = " ".join(p_base_words[i1:i2])
                w_seg = " ".join(p_witness_words[j1:j2])
                target_crop_bytes = pix.tobytes("png")

                conflicts.append({
                    "id": conflicts_found,
                    "tag": tag,
                    "base_segment": b_seg,
                    "witness_segment": w_seg,
                    "lookup_idx": len(all_base_words) - len(p_base_words) + i1,
                    "token_idx": i1,
                    "bbox": p_bbox,
                    "crop_bytes": target_crop_bytes
                })

    doc.close()
    base_words = all_base_words
    print(f"Paragraph-level diff completed in {time.time() - t1:.3f}s. Found {len(conflicts)} local conflicts.")

    if not conflicts:
        print("No textual divergences found between base and witness texts.")
        return []

    print(f"\n--- [STEP 3] Concurrently Adjudicating {len(conflicts)} Conflicts (max_workers={max_workers}) ---")
    t2 = time.time()
    full_context_str = " ".join(base_words)
    results = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_conf = {
            executor.submit(_process_single_conflict, conf, full_context_str): conf
            for conf in conflicts
        }
        for future in as_completed(future_to_conf):
            conf = future_to_conf[future]
            try:
                conf_id, conf_obj, decision = future.result()
                results[conf_id] = (conf_obj, decision)
            except Exception as exc:
                print(f"  [Conflict #{conf['id']}] Exception: {exc}")

    # Output results in order
    adjudications = []
    for conf_id in sorted(results.keys()):
        conf_obj, decision = results[conf_id]
        print(f"\n[Conflict #{conf_obj['id']}] Tag: '{conf_obj['tag']}'")
        print(f"  Base Reading:    '{conf_obj['base_segment']}'")
        print(f"  Witness Reading: '{conf_obj['witness_segment']}'")
        if conf_obj['token_idx'] is not None:
            print(f"  Mapped Base index {conf_obj['lookup_idx']} -> Token index {conf_obj['token_idx']}")
        else:
            print("  WARNING: Spatial index map failed. Used fallback bbox.")
        print(f"  Target BBox:     {conf_obj['bbox']}")
        print("  Adjudication Result:")
        print(f"  {decision}")
        adjudications.append((conf_obj, decision))

    print(f"\n[Summary] Step 3 Adjudication completed in {time.time() - t2:.2f}s")
    print(f"[Summary] Entire Pipeline Execution completed in {time.time() - pipeline_start:.2f}s")

    # Synthesize clean corrected text
    corrected_text, corrections = synthesize_corrected_text(base_words, adjudications)
    print("\n" + "=" * 60)
    print("RECONSTRUCTED CORRECTED HEBREW TEXT STREAM")
    print("=" * 60)
    print(corrected_text[:500] + "..." if len(corrected_text) > 500 else corrected_text)

    if corrections:
        print("\n" + "=" * 60)
        print(f"HIGHLIGHTED TEXT CORRECTIONS MADE ({len(corrections)} Total Corrections)")
        print("=" * 60)
        for c in corrections[:10]:
            print(f"  • Token #{c['index']}: [Original: '{c['original']}'] -> [Corrected: '{c['corrected']}']")
            print(f"    Type: {c['type']} | Confidence: {c['confidence']}")
            print(f"    Reasoning: {c['reasoning']}\n")

    return adjudications


def synthesize_corrected_text(base_words, adjudications):
    # Constants
    KLALIM_DIR = "/Users/ericsafern/work/yad-malachi/yad-malachi-pipeline/klalim_docai"
    ADJUDICATION_LOG = "/Users/ericsafern/work/yad-malachi/yad-malachi-pipeline/adjudication.log"
    corrected_words = list(base_words)
    corrections = []

    for conf_obj, decision_raw in adjudications:
        try:
            dec = json.loads(decision_raw) if isinstance(decision_raw, str) else decision_raw
            sel = dec.get("selected_option")
            trans = dec.get("transcription_found", "")
            conf = dec.get("confidence", 0.0)
            reason = dec.get("reasoning", "")

            idx = conf_obj.get("lookup_idx")
            if idx is not None and idx < len(corrected_words):
                orig_word = base_words[idx]
                if sel == "B" and conf_obj.get("witness_segment"):
                    new_word = conf_obj["witness_segment"]
                    corrected_words[idx] = new_word
                    corrections.append({
                        "index": idx,
                        "original": orig_word,
                        "corrected": new_word,
                        "confidence": conf,
                        "type": "WITNESS_REPLACEMENT",
                        "reasoning": reason
                    })
                elif sel in ("C", "UNCERTAIN") and trans and trans.strip() != orig_word.strip():
                    new_word = trans.strip()
                    corrected_words[idx] = new_word
                    corrections.append({
                        "index": idx,
                        "original": orig_word,
                        "corrected": new_word,
                        "confidence": conf,
                        "type": "PALEOGRAPHIC_ACRONYM_CORRECTION",
                        "reasoning": reason
                    })
        except Exception:
            pass

    return " ".join(corrected_words), corrections


def run_batch_pipeline(pdf_path, json_dir, start_page=0, end_page=3, max_workers=5):
    import subprocess
    init_cache()
    batch_start = time.time()
    total_conflicts = 0
    total_adjudications = []

    print("=" * 60)
    print(f"ORCHESTRATOR BATCH RUNNER (Pages {start_page} to {end_page})")
    print("=" * 60)

    for page_idx in range(start_page, end_page + 1):
        json_path = os.path.join(json_dir, f"test_page-{page_idx}.json")
        if not os.path.exists(json_path):
            print(f"Skipping page {page_idx}: JSON spatial map missing ({json_path})")
            continue

        print(f"\n>>> PROCESSING PAGE {page_idx} <<<")
        with open(json_path, "r", encoding="utf-8") as f:
            doc_ai_json = json.load(f)

        base_text = doc_ai_json.get("text", "")

        doc = fitz.open(pdf_path)
        page = doc[page_idx]
        pix = page.get_pixmap(dpi=300)
        temp_png = f"temp_page_{page_idx}.png"
        pix.save(temp_png)
        doc.close()

        res = subprocess.run(["tesseract", temp_png, "stdout", "-l", "heb"], capture_output=True, text=True)
        witness_text = res.stdout.strip()
        if os.path.exists(temp_png):
            os.remove(temp_png)

        adjudications = run_pipeline(pdf_path, page_idx, base_text, witness_text, doc_ai_json, max_workers=max_workers)
        total_conflicts += len(adjudications)
        total_adjudications.extend(adjudications)

    elapsed_s = time.time() - batch_start
    print("\n" + "=" * 60)
    print("BATCH PROCESSING COMPLETE")
    print(f"Processed Pages: {start_page} to {end_page}")
    print(f"Total Conflicts Processed: {total_conflicts}")
    print(f"Total Batch Execution Time: {elapsed_s:.2f}s")
    print("=" * 60)
    return total_adjudications


# =====================================================================
# DIAGNOSTIC RUNNER (MAIN ENTRY POINT)
# =====================================================================

if __name__ == "__main__":
    if "--batch" in sys.argv:
        run_batch_pipeline(TEST_PDF, "./document_jsons", start_page=0, end_page=2, max_workers=5)
    else:
        print("=" * 60, flush=True)
        print("ORCHESTRATOR DIAGNOSTIC RUNNER", flush=True)
        print("=" * 60, flush=True)

        json_path = f"./document_jsons/test_page-{PAGE_INDEX}.json"

        print(f"[1/5] Checking target PDF ('{TEST_PDF}')...", end=" ", flush=True)
        if not os.path.exists(TEST_PDF):
            print("FAILED!")
            sys.exit(1)
        print("FOUND.", flush=True)

        print(f"[2/5] Checking spatial JSON ('{json_path}')...", end=" ", flush=True)
        if not os.path.exists(json_path):
            print("FAILED!")
            sys.exit(1)
        print("FOUND.", flush=True)

        init_cache()

        print("[3/5] Loading Document AI JSON...", end=" ", flush=True)
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                real_doc_ai_json = json.load(f)
            print("SUCCESS.", flush=True)
        except Exception as e:
            print("FAILED!")
            sys.exit(1)

        print("[4/5] Extracting Base text & generating Tesseract Witness text...", flush=True)
        base_text = real_doc_ai_json.get("text", "")

        doc = fitz.open(TEST_PDF)
        page = doc[PAGE_INDEX]
        pix = page.get_pixmap(dpi=300)
        temp_png = f"temp_page_{PAGE_INDEX}.png"
        pix.save(temp_png)
        doc.close()

        import subprocess
        res = subprocess.run(["tesseract", temp_png, "stdout", "-l", "heb"], capture_output=True, text=True)
        witness_text = res.stdout.strip()
        if os.path.exists(temp_png):
            os.remove(temp_png)

        print("[5/5] Launching adjudication engine...", flush=True)
        print("-" * 60, flush=True)
        try:
            run_pipeline(TEST_PDF, PAGE_INDEX, base_text, witness_text, real_doc_ai_json)
            print("-" * 60, flush=True)
            print("ORCHESTRATOR COMPLETE.", flush=True)
        except Exception as e:
            traceback.print_exc()
            sys.exit(1)
