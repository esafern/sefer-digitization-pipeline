# [PRODUCTION] Extract Document AI OCR tokens for specific PDF pages into
# docai_word_boxes/page_N.json, in the same {text, x1, y1, x2, y2} normalized
# token format the rest of the pipeline already reads via
# corpus_io.load_docai_page() - so downstream alignment code needs no
# changes. Skips any page whose output file already exists, so it's safe to
# re-run over a range to fill in gaps incrementally.
#
# Promoted 2026-08-18 from archive/scripts/extend_docai_ocr.py (PROJECT-
# STATUS-HISTORY.md 2026-08-18/17): that script had been reused as a one-off
# for every actual Parts 2-3 DocAI extraction this project has done, despite
# being archived - meaning the live extraction path had no home in
# pipeline/ or tools/ at all. Promoted here rather than left archived, with
# three real fixes along the way, not just a file move:
#   - The archived script's PDF_PATH was hardcoded to `berlin_square.pdf`,
#     the pre-page-order-fix filename that predates the 2026-08-11 leaf
#     correction. Every real run since has had to manually override this;
#     the correct current file, `berlin_square_corrected.pdf`, is now the
#     default (still overridable via --pdf, e.g. for a different work).
#   - REPO/output-dir resolution now goes through corpus_io.py
#     (`cio.DOCAI_DIR`, `cio.repo_path`) instead of a private copy, per this
#     project's shared-library rule.
#   - PROJECT_ID/LOCATION/PROCESSOR_ID were hardcoded constants with no
#     override; now CLI flags (env-var fallback), since a different
#     digitization work would need its own DocAI processor - the
#     reusable-pipeline goal this pipeline is held to.
#
# Requires a GCP service-account key. If GOOGLE_APPLICATION_CREDENTIALS
# isn't already set, defaults to this repo's own credentials.json (see
# SETUP.md) if that file exists.
import argparse
import json
import os
import sys

import fitz
from google.cloud import documentai

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pipeline"))
import corpus_io as cio  # noqa: E402

DEFAULT_PDF = cio.repo_path("berlin_square_corrected.pdf")
DEFAULT_PROJECT_ID = os.environ.get("DOCAI_PROJECT_ID", "gen-lang-client-0289907848")
DEFAULT_LOCATION = os.environ.get("DOCAI_LOCATION", "us")
DEFAULT_PROCESSOR_ID = os.environ.get("DOCAI_PROCESSOR_ID", "4d3d4f204562f1d6")


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


def main(pdf_page_numbers_1indexed, pdf_path, out_dir, project_id, location, processor_id):
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        default_creds = cio.repo_path("credentials.json")
        if os.path.exists(default_creds):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = default_creds
        else:
            raise SystemExit(
                "GOOGLE_APPLICATION_CREDENTIALS not set and no credentials.json "
                "found at the repo root - see SETUP.md"
            )

    client = documentai.DocumentProcessorServiceClient()
    name = client.processor_path(project_id, location, processor_id)

    doc = fitz.open(pdf_path)
    for page_num in pdf_page_numbers_1indexed:
        page_idx = page_num - 1
        if page_idx >= len(doc):
            print(f"page {page_num}: beyond end of PDF ({len(doc)} pages), skipping")
            continue
        out_path = os.path.join(out_dir, f"page_{page_num}.json")
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pages", nargs="+", type=int, help="1-indexed PDF page numbers to extract")
    parser.add_argument("--pdf", default=DEFAULT_PDF, help=f"source PDF (default: {DEFAULT_PDF})")
    parser.add_argument("--out-dir", default=cio.DOCAI_DIR, help=f"output directory (default: {cio.DOCAI_DIR})")
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--location", default=DEFAULT_LOCATION)
    parser.add_argument("--processor-id", default=DEFAULT_PROCESSOR_ID)
    args = parser.parse_args()
    main(args.pages, args.pdf, args.out_dir, args.project_id, args.location, args.processor_id)
