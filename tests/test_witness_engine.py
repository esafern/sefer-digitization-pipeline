import pytest
import sys
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pipeline"))

from second_witness_eval import (
    get_witness_engine, set_default_witness_engine,
    VlmWitnessEngine, TesseractWitnessEngine
)

def test_default_witness_engine_is_vlm():
    set_default_witness_engine("vlm")
    engine = get_witness_engine()
    assert isinstance(engine, VlmWitnessEngine)

def test_swappable_tesseract_engine():
    engine = get_witness_engine("tesseract")
    assert isinstance(engine, TesseractWitnessEngine)

def test_invalid_witness_engine_raises():
    with pytest.raises(ValueError):
        get_witness_engine("invalid_engine")

def test_vlm_witness_engine_transcribe_region(monkeypatch, tmp_path):
    engine = VlmWitnessEngine(db_path=str(tmp_path / "test_cache.db"))
    
    # Mock call_gemini_vision_adjudicate
    monkeypatch.setattr(engine, "call_gemini_vision_adjudicate", lambda crop_bytes: "לכו אחריה")
    
    # Mock PyMuPDF crop_pdf_bounding_box
    import second_witness_eval.vlm_witness as vw
    monkeypatch.setattr(vw, "crop_pdf_bounding_box", lambda doc, p, b: b"dummy_crop")
    
    # Mock fitz.open
    class MockDoc:
        def close(self): pass
    monkeypatch.setattr(vw.fitz, "open", lambda path: MockDoc())
    
    from second_witness_eval import BoundingBox
    tokens = engine.transcribe_region("dummy.pdf", 1, BoundingBox(0.1, 0.1, 0.2, 0.2))
    assert len(tokens) == 2
    assert tokens[0].text == "לכו"
    assert tokens[1].text == "אחריה"
    assert tokens[0].confidence == 0.95

def test_vlm_witness_engine_handles_pdf_error(monkeypatch, tmp_path):
    engine = VlmWitnessEngine(db_path=str(tmp_path / "test_cache.db"))
    from second_witness_eval import BoundingBox
    tokens = engine.transcribe_region("non_existent_file.pdf", 1, BoundingBox(0.1, 0.1, 0.2, 0.2))
    assert tokens == []
