# [PRODUCTION] Extend DocAI OCR coverage beyond page 61 (the previous limit) by
# running the same synchronous DocAI processor per-page and saving output in the
# same {text, x1, y1, x2, y2} token format as the existing docai_word_boxes/*.json
# files, so downstream alignment code needs no changes.
import os
import sys
import json

import fitz
from google.cloud import documentai

REPO = os.path.dirname(os.path.abspath(__file__))
PDF_PATH = os.path.join(REPO, "berlin_square.pdf")
OUT_DIR = os.path.join(REPO, "docai_word_boxes")

PROJECT_ID = "gen-lang-client-0289907848"
LOCATION = "us"
PROCESSOR_ID = "4d3d4f204562f1d6"


def extract_single_page_pdf(doc, page_idx):
    single = fitz.open()
    single.insert_pdf(doc, from_page=page_idx, to_page=page_idx)
    return single.tobytes()


def process_page(client, name, page_bytes):
    raw_document = documentai.RawDocument(content=page_bytes, mime_type="application/pdf")
    request = documentai.ProcessRequest(name=name, raw_document=raw_document)
    result = client.process_document(request=request)
    return result.document


def document_to_tokens(document):
    tokens = []
    doc_text = document.text
    if not document.pages:
        return tokens
    page = document.pages[0]
    for token in page.tokens:
        seg = token.layout.text_anchor.text_segments
        text = "".join(doc_text[int(s.start_index):int(s.end_index)] for s in seg)
        verts = token.layout.bounding_poly.normalized_vertices
        if not verts:
            continue
        xs = [v.x for v in verts]
        ys = [v.y for v in verts]
        tokens.append({
            "text": text.strip(),
            "x1": min(xs), "y1": min(ys),
            "x2": max(xs), "y2": max(ys),
        })
    return tokens


def main(pdf_page_numbers_1indexed):
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        raise SystemExit("GOOGLE_APPLICATION_CREDENTIALS not set")

    client = documentai.DocumentProcessorServiceClient()
    name = client.processor_path(PROJECT_ID, LOCATION, PROCESSOR_ID)

    doc = fitz.open(PDF_PATH)
    for page_num in pdf_page_numbers_1indexed:
        page_idx = page_num - 1
        if page_idx >= len(doc):
            print(f"page {page_num}: beyond end of PDF ({len(doc)} pages), skipping")
            continue
        out_path = os.path.join(OUT_DIR, f"page_{page_num}.json")
        if os.path.exists(out_path):
            print(f"page {page_num}: already exists, skipping")
            continue

        page_bytes = extract_single_page_pdf(doc, page_idx)
        document = process_page(client, name, page_bytes)
        tokens = document_to_tokens(document)

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(tokens, f, ensure_ascii=False, indent=2)
        print(f"page {page_num}: {len(tokens)} tokens -> {out_path}")

    doc.close()


if __name__ == "__main__":
    pages = [int(x) for x in sys.argv[1:]]
    if not pages:
        raise SystemExit("usage: extend_docai_ocr.py <page_num> [page_num ...]")
    main(pages)
