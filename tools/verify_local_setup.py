#!/usr/bin/env python3
"""Verify every piece of local setup that git does NOT carry is actually
present and minimally valid - the files/dirs SETUP.md's "Files not in the
public repo" section says must be migrated separately, plus the venv and
GEMINI_API_KEY that SETUP.md also calls out as needed but not committed.

Read-only, standalone (not part of rebuild_all.sh - this checks the
environment, not the corpus). Exit code 0 iff every REQUIRED item passes;
missing RECOMMENDED items print as warnings but do not fail the run, same
distinction SETUP.md draws between the two.

Each check does more than "does the path exist": the two PDFs are opened
and their page count checked, credentials.json is parsed as JSON and
shape-checked, docai_word_boxes/ is read through corpus_io.load_docai_page
(not a hand-rolled json.load, per this project's shared-library rule) to
confirm at least one page is genuinely parseable, not just present.

Usage:
    python3 tools/verify_local_setup.py
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pipeline"))
import corpus_io as cio  # noqa: E402

EXPECTED_PDF_PAGES = 337


def check_file(path, required, min_bytes=1):
    full = os.path.join(REPO, path)
    if not os.path.isfile(full):
        return False, "missing"
    size = os.path.getsize(full)
    if size < min_bytes:
        return False, f"present but only {size} bytes - looks truncated/empty"
    return True, f"{size:,} bytes"


def check_dir(path, required, min_files=1):
    full = os.path.join(REPO, path)
    if not os.path.isdir(full):
        return False, "missing"
    n = sum(
        len([f for f in files if not f.startswith(".")])
        for _, _, files in os.walk(full)
    )
    if n < min_files:
        return False, f"present but empty (0 files, including subdirectories)"
    return True, f"{n} files (recursive)"


def check_credentials():
    ok, detail = check_file("credentials.json", required=True)
    if not ok:
        return ok, detail
    try:
        with open(os.path.join(REPO, "credentials.json")) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        return False, f"present but not valid JSON ({e})"
    if data.get("type") != "service_account" or "private_key" not in data:
        return False, "present, valid JSON, but missing expected service-account fields"
    return True, f"valid service-account JSON ({detail})"


def check_pdf(path):
    ok, detail = check_file(path, required=True, min_bytes=10_000_000)
    if not ok:
        return ok, detail
    try:
        import fitz  # pymupdf
        doc = fitz.open(os.path.join(REPO, path))
        pages = doc.page_count
    except Exception as e:
        return False, f"present ({detail}) but pymupdf could not open it: {e}"
    if pages != EXPECTED_PDF_PAGES:
        return False, f"opens fine but has {pages} pages, expected {EXPECTED_PDF_PAGES}"
    return True, f"{detail}, {pages} pages (opened and verified with pymupdf)"


def check_docai_word_boxes():
    ok, detail = check_dir("docai_word_boxes", required=True, min_files=1)
    if not ok:
        return ok, detail
    page1 = cio.load_docai_page(1)
    if page1 is None:
        return False, f"{detail}, but page_1.json is missing or unreadable"
    if not isinstance(page1, list) or len(page1) == 0:
        return False, f"{detail}, but page_1.json did not parse to a non-empty token list"
    return True, f"{detail}, page_1.json parses via corpus_io.load_docai_page ({len(page1)} tokens)"


def check_venv_packages():
    missing = []
    for module_name, pip_name in [
        ("fitz", "pymupdf"),
        ("google.genai", "google-genai"),
        ("google.cloud.documentai", "google-cloud-documentai"),
    ]:
        try:
            __import__(module_name)
        except ImportError:
            missing.append(pip_name)
    if missing:
        return False, f"missing: {', '.join(missing)} - run `pip install -r requirements.txt`"
    return True, "pymupdf, google-genai, google-cloud-documentai all importable"


def check_gemini_key():
    val = os.environ.get("GEMINI_API_KEY", "")
    if not val:
        return False, "GEMINI_API_KEY not set in this shell's environment"
    return True, f"set ({len(val)} chars) - presence only, NOT verified against the API"


REQUIRED = [
    ("credentials.json", check_credentials),
    ("berlin_square_corrected.pdf", lambda: check_pdf("berlin_square_corrected.pdf")),
    ("berlin_square_original_transposed.pdf", lambda: check_pdf("berlin_square_original_transposed.pdf")),
    ("venv packages (pymupdf/google-genai/google-cloud-documentai)", check_venv_packages),
]

RECOMMENDED = [
    ("docai_word_boxes/", check_docai_word_boxes),
    ("document_jsons_berlin/", lambda: check_dir("document_jsons_berlin", required=False)),
    ("sefaria_reference_corpus/", lambda: check_dir("sefaria_reference_corpus", required=False)),
    ("klalim_docai/", lambda: check_dir("klalim_docai", required=False)),
    ("llm_klal_starts/", lambda: check_dir("llm_klal_starts", required=False)),
    ("sefaria_export/", lambda: check_dir("sefaria_export", required=False)),
    ("vlm_extractions/", lambda: check_dir("vlm_extractions", required=False)),
    ("GEMINI_API_KEY", check_gemini_key),
]


def run(label, checks):
    all_ok = True
    print(f"\n{label}:")
    for name, fn in checks:
        ok, detail = fn()
        all_ok = all_ok and ok
        mark = "OK  " if ok else "FAIL"
        print(f"  [{mark}] {name}: {detail}")
    return all_ok


def main():
    required_ok = run("Required (needed for the core pipeline to run at all)", REQUIRED)
    recommended_ok = run("Recommended (needed for specific tools - witness review, punctuation, lexicon cross-check, etc.)", RECOMMENDED)

    print()
    if required_ok and recommended_ok:
        print("Everything present and verified.")
    elif required_ok:
        print("All REQUIRED items pass. Some RECOMMENDED items are missing - fine unless you need the specific tool that uses them.")
    else:
        print("One or more REQUIRED items failed - the core pipeline will not run cleanly. See SETUP.md.")

    sys.exit(0 if required_ok else 1)


if __name__ == "__main__":
    main()
