import os
import sys
from typing import List
import fitz

from .abstract_witness import AbstractWitnessEngine, BoundingBox, OCRToken

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "pipeline"))

from vision_adjudication_common import (
    make_client, adjudicate_with_retry, init_cache_table, 
    get_cached_decision, put_cached_decision, crop_pdf_bounding_box
)

class VlmWitnessEngine(AbstractWitnessEngine):
    def __init__(self, db_path=None, table_name="vlm_witness_cache"):
        if db_path is None:
            db_path = os.path.join(REPO, "adjudication_cache.db")
        self.db_path = db_path
        self.table_name = table_name
        self.prompt_hash = "vlm_literal_ocr_v1"
        
        # Flushes schemas implicitly upon initialization
        init_cache_table(self.db_path, self.table_name, self.prompt_hash, has_model_column=True)
        
        api_key = os.environ.get("GEMINI_API_KEY", "dummy_key")
        self.client = make_client(api_key)

    def call_gemini_vision_adjudicate(self, crop_bytes: bytes) -> str:
        prompt = (
            "You are a literal OCR reader for 19th-century Hebrew typography. "
            "Transcribe the Hebrew text visible in this image crop verbatim line-by-line. "
            "Do not assume or infer text outside this image. Output only the raw Hebrew characters."
        )
        
        def cache_get():
            return get_cached_decision(
                self.db_path, self.table_name, self.prompt_hash, crop_bytes, "", "", ""
            )
            
        def cache_put(text, model):
            put_cached_decision(
                self.db_path, self.table_name, self.prompt_hash, 
                crop_bytes, "", "", "", text, model=model
            )

        # Uses central models with exponential backoff on 503/429
        return adjudicate_with_retry(
            client=self.client,
            crop_bytes=crop_bytes,
            prompt=prompt,
            cache_get=cache_get,
            cache_put=cache_put,
            models_to_try=("gemini-3.6-flash", "gemini-3.5-flash"),
            response_mime_type="text/plain"
        )

    def transcribe_region(self, pdf_path: str, page_num: int, bbox: BoundingBox) -> List[OCRToken]:
        try:
            doc = fitz.open(pdf_path)
            crop_bytes = crop_pdf_bounding_box(doc, page_num, {
                "x1": bbox.x1, "y1": bbox.y1, "x2": bbox.x2, "y2": bbox.y2
            })
            doc.close()
        except Exception as err:
            sys.stderr.write(f"[VlmWitnessEngine] Error cropping PDF {pdf_path} p.{page_num}: {err}\n")
            return []

        try:
            text = self.call_gemini_vision_adjudicate(crop_bytes)
        except Exception as err:
            sys.stderr.write(f"[VlmWitnessEngine] VLM API call failed: {err}\n")
            return []
        
        tokens = []
        if text:
            for word in text.split():
                tokens.append(OCRToken(text=word, bbox=None, confidence=0.95))
            
        return tokens
