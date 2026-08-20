import os
import subprocess
import tempfile
import fitz
from typing import List
import sys

from .abstract_witness import AbstractWitnessEngine, BoundingBox, OCRToken

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "pipeline"))
import corpus_io as cio

class TesseractWitnessEngine(AbstractWitnessEngine):
    def transcribe_region(self, pdf_path: str, page_num: int, bbox: BoundingBox) -> List[OCRToken]:
        doc = fitz.open(pdf_path)
        page = doc.load_page(page_num - 1)
        rect_page = page.rect
        width, height = rect_page.width, rect_page.height

        padding = 0.02
        xmin = max(0.0, bbox.x1 - padding) * width
        ymin = max(0.0, bbox.y1 - padding) * height
        xmax = min(1.0, bbox.x2 + padding) * width
        ymax = min(1.0, bbox.y2 + padding) * height

        crop_rect = fitz.Rect(xmin, ymin, xmax, ymax)
        pix = page.get_pixmap(clip=crop_rect, dpi=300)
        
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(pix.tobytes("png"))
            tmp_path = f.name
        
        out = subprocess.run(["tesseract", tmp_path, "stdout", "-l", "heb"], capture_output=True, text=True)
        os.remove(tmp_path)
        
        if out.returncode != 0:
            raise SystemExit(f"tesseract failed: {out.stderr[:300]}")
            
        tokens = []
        for word in out.stdout.split():
            if cio.hebrew_letters_only(word):
                tokens.append(OCRToken(text=word, bbox=None, confidence=0.8))
                
        return tokens
