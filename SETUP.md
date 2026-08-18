# Setup

## New machine, step by step

### 1 — Clone the repo

```bash
git clone https://github.com/esafern/sefer-digitization-pipeline.git
cd sefer-digitization-pipeline
```

### 2 — Restore gitignored data files

The repo doesn't carry credentials, the source PDFs, or the large cache
directories. They travel as a single tarball (`yad-malachi-migration.tar`,
~467 MB) which must be obtained out-of-band (copy it from the previous
machine or from wherever it was stashed).

Place the tarball in the repo root and extract:

```bash
tar -xf yad-malachi-migration.tar
```

This restores `credentials.json`, the two source PDFs, `docai_word_boxes/`,
and the other cache dirs listed in "Files not in the public repo" below. The
tarball entries are relative paths, so extracting from the repo root puts
everything in the right place.

### 3 — Python environment

`python3` on a Homebrew Mac is PEP 668 externally-managed — plain `pip3
install` fails. Use a venv:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

`requirements.txt` covers pipeline/tools runtime deps (pymupdf, google-genai,
google-cloud-documentai); `requirements-dev.txt` covers testing (pytest,
playwright). Both are needed for local development.

### 4 — Install Playwright's browser

Playwright ships the browser binaries separately from the Python package —
`pip install` alone leaves the test suite broken with "Executable doesn't
exist" errors on every browser test:

```bash
playwright install chromium
```

### 5 — Set GEMINI_API_KEY

The vision-adjudication pipeline authenticates to Gemini via an env var, not
a file. Add to `~/.zshrc` (or `~/.bashrc`) and restart your shell:

```bash
export GEMINI_API_KEY="your-key-here"
```

### 6 — Auto-activation with direnv (recommended)

Manually re-activating the venv each session is easy to forget. This repo
ships a tracked `.envrc` (`source venv/bin/activate`) that
[direnv](https://direnv.net/) picks up automatically on `cd`:

```bash
brew install direnv
# add to ~/.zshrc: eval "$(direnv hook zsh)"  — then restart your shell
direnv allow .          # one-time trust of this repo's .envrc
```

After that, `cd` into the repo activates the venv automatically; `cd` out
deactivates it.

### 7 — Verify

```bash
python3 tools/verify_local_setup.py   # checks files, PDFs, credentials, GEMINI_API_KEY
pytest tests/ -q                       # 199 tests; all should pass
```

---

## Files not in the public repo

`credentials.json`, `berlin_square_corrected.pdf`,
`berlin_square_original_transposed.pdf`, and the following cache directories
are gitignored and must be migrated separately (step 2 above handles all of
them if the tarball is complete):

- `docai_word_boxes/` — DocAI per-page word-box JSON
- `document_jsons_berlin/` — raw Document AI output
- `sefaria_reference_corpus/` — reference text for lexicon work
- `klalim_docai/` — klal-level DocAI extractions
- `llm_klal_starts/` — LLM boundary-detection cache
- `sefaria_export/` — Sefaria ingest output
- `vlm_extractions/` — vision-model extraction cache
- `images/pdf_pages/` — rendered scan pages for the review dashboard

`images/pdf_pages/` is easy to miss: the dashboard's left-pane scan image
depends on it but nothing else does, so its absence only surfaces when you
open a klal in the dashboard (caught 2026-08-18 on a fresh migration).

After migrating, verify everything actually landed:

```bash
python3 tools/verify_local_setup.py
```

Checks presence AND minimal validity (both PDFs opened and page-counted;
`credentials.json` parsed and shape-checked; `docai_word_boxes/` read through
`corpus_io.load_docai_page`). Exits non-zero if anything *required* is
missing; recommended-but-missing items print as warnings.
