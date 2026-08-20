from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class BoundingBox:
    x1: float
    y1: float
    x2: float
    y2: float

@dataclass
class OCRToken:
    text: str
    bbox: Optional[BoundingBox]
    confidence: float

class AbstractWitnessEngine(ABC):
    @abstractmethod
    def transcribe_region(self, pdf_path: str, page_num: int, bbox: BoundingBox) -> List[OCRToken]:
        """Transcribes region crop into tokens."""
        pass
