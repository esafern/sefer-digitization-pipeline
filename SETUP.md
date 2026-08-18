# Setup

## Python environment

This machine's `python3` (Homebrew) is PEP 668 externally-managed — plain
`pip3 install` at the system level fails with `error: externally-managed-
environment`. Use a venv (also keeps this project's pinned versions isolated
from anything else on the machine):

```bash
python3 -m venv venv
source venv/bin/activate        # now `pip` (not just `pip3`) resolves, inside the venv
pip install -r requirements.txt -r requirements-dev.txt
```

`requirements.txt` covers the pipeline/tools runtime deps (pymupdf,
google-genai, google-cloud-documentai); `requirements-dev.txt` covers testing
(pytest, playwright). Both are needed for local development.

Verify with:

```bash
pytest tests/ -q
```

Re-activate the venv (`source venv/bin/activate`) in each new shell session
before running any pipeline script.

## Files not in the public repo

See `PROJECT-STATUS.md` / ask for the migration walkthrough — `credentials.json`,
the two source PDFs, and several gitignored cache directories
(`docai_word_boxes/`, `document_jsons_berlin/`, `sefaria_reference_corpus/`,
`klalim_docai/`, `llm_klal_starts/`, `sefaria_export/`, `vlm_extractions/`)
must be migrated separately (not via git). `GEMINI_API_KEY` is an environment
variable, not a file — re-export it in your shell profile.
