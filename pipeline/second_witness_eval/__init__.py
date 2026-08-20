from .abstract_witness import AbstractWitnessEngine, BoundingBox, OCRToken
from .tesseract_witness import TesseractWitnessEngine
from .vlm_witness import VlmWitnessEngine
from .registry import get_witness_engine, set_default_witness_engine

__all__ = [
    "AbstractWitnessEngine",
    "BoundingBox",
    "OCRToken",
    "TesseractWitnessEngine",
    "VlmWitnessEngine",
    "get_witness_engine",
    "set_default_witness_engine",
]
