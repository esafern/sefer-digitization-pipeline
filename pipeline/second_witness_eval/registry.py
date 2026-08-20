from .abstract_witness import AbstractWitnessEngine
from .tesseract_witness import TesseractWitnessEngine
from .vlm_witness import VlmWitnessEngine

_REGISTRY = {
    "tesseract": TesseractWitnessEngine,
    "vlm": VlmWitnessEngine,
}

_DEFAULT_ENGINE_NAME = "vlm"

def get_witness_engine(engine_name: str = None) -> AbstractWitnessEngine:
    if engine_name is None:
        engine_name = _DEFAULT_ENGINE_NAME
    if engine_name not in _REGISTRY:
        raise ValueError(f"Unknown witness engine: {engine_name}")
    return _REGISTRY[engine_name]()

def set_default_witness_engine(engine_name: str):
    global _DEFAULT_ENGINE_NAME
    if engine_name not in _REGISTRY:
        raise ValueError(f"Unknown witness engine: {engine_name}")
    _DEFAULT_ENGINE_NAME = engine_name
