#!/usr/bin/env python3
"""
pipeline/typography.py

Catalog of 19th-century Hebrew typography, printer ligatures, combined glyph sorts,
and character-confusion patterns specific to the 1852 Berlin printing of Sefer Yad Malachi.

Serves as the single source of truth for typographic anomaly detection and OCR witness mapping.
"""

from typing import Dict, List, Tuple

# Known combined printer glyphs and ligatures used by the Berlin 1852 typesetter
PRINTER_LIGATURES_AND_GLYPHS = [
    {
        "id": "alef_lamed",
        "name": "Alef-Lamed Ligature (ﭏ)",
        "unicode": "U+FB4F",
        "composed_letters": ("א", "ל"),
        "target_string": "אל",
        "ocr_behavior": {
            "docai": "Collapses ligature to bare 'א', silently dropping 'ל'.",
            "tesseract": "Frequently misreads as 'א', 'ד', or splits into garbage tokens.",
            "vlm": "Correctly transcribes 'אל' from visual context in most cases."
        },
        "description": "Standard 19th-century Hebrew printing sort combining Alef and Lamed into a single block.",
        "examples": [
            "אלא -> transcribed by DocAI as אא",
            "אלו -> transcribed by DocAI as או",
            "אליבא -> transcribed by DocAI as איבא"
        ],
        "detector_script": "tools/detect_ligature_corruption.py"
    },
    {
        "id": "chet_zayin",
        "name": "Chet-Zayin Combined Glyph / Ligature (ח+ז)",
        "unicode": None,
        "composed_letters": ("ח", "ז"),
        "target_string": "חז",
        "ocr_behavior": {
            "docai": "Occasionally reads correctly as 'חז' but with compressed bounding box.",
            "tesseract": "Misreads as 'הל' (e.g. 'חז\"ל' -> 'הלל').",
            "vlm": "Unconditioned VLM sometimes misjudges as bare 'ח\"ל' (assuming 'ז' was omitted due to tight kern/fused left leg)."
        },
        "description": "Typesetter sort where the left leg of Chet is kerned/fused with the head of Zayin, commonly seen in the abbreviation חז\"ל.",
        "examples": [
            "Klal 30, Token 49 (Word 166, Page 24): 'חז\"ל' printed with fused Chet-Zayin sort."
        ],
        "detector_script": None
    }
]

# Character confusion pairs observed in 19th-century square rabbinic typography
# Used by gematria marker tracking, reconstruction matching, and OCR sanity checks
CONFUSION_PAIRS: Tuple[Tuple[str, str], ...] = (
    ("ט", "פ"),  # Added 2026-08-23: Klal 16 'טז' misread as 'פז'
    ("ד", "ר"),  # Common square-font ascender/corner confusion
    ("ו", "ז"),  # Narrow stem vs headed stem
    ("ב", "כ"),  # Square bottom base vs rounded corner
    ("ח", "ת"),  # Left foot vs open gap
    ("ה", "ח"),  # Left leg gap vs closed bridge
    ("ם", "ס"),  # Square final mem vs rounded samekh
    ("י", "ו"),  # Short yod vs long vav
    ("נ", "ג"),  # Nun vs Gimel base
)


def get_ligatures() -> List[Dict]:
    return PRINTER_LIGATURES_AND_GLYPHS


def get_confusion_pairs() -> Tuple[Tuple[str, str], ...]:
    return CONFUSION_PAIRS
