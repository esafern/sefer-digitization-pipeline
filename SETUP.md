# Setup

## TL;DR

Seven steps, and **two of them are the ones that actually bite**:

```bash
git clone https://github.com/esafern/sefer-digitization-pipeline.git
cd sefer-digitization-pipeline
git config user.email "109570+esafern@users.noreply.github.com"
tar -xf yad-malachi-migration.tar        # ← obtained out-of-band, ~467 MB
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
playwright install chromium              # ← separate from pip; easy to skip
export GEMINI_API_KEY="..."              # put it in ~/.zshrc
python3 tools/verify_local_setup.py && pytest tests/ -q
```

**The tarball is not optional and not in git.** The source PDFs, credentials,
and every large cache directory travel out-of-band. Without it the review
dashboard's scan pane is blank and most of `tools/` can't run.

**`playwright install chromium` is a separate step from `pip install`.**
Skipping it leaves the browser tests failing with "Executable doesn't exist"
and nothing else explaining why.

**`python3 tools/verify_local_setup.py` is the actual proof it worked** — it
opens both PDFs, parses `credentials.json`, and reads `docai_word_boxes/`
through the real loader, rather than just checking that filenames exist.

## New machine, step by step

### 1 — Clone the repo

```bash
git clone https://github.com/esafern/sefer-digitization-pipeline.git
cd sefer-digitization-pipeline
```

Configure git to use GitHub's noreply email (required — GitHub blocks pushes
that expose a private email address):

```bash
git config user.email "109570+esafern@users.noreply.github.com"
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

### 5 — Set GEMINI_API_KEY & Model Rules

The vision-adjudication pipeline authenticates to Gemini via an env var, not
a file. Add to `~/.zshrc` (or `~/.bashrc`) and restart your shell:

```bash
export GEMINI_API_KEY="your-key-here"
```

> [!WARNING]
> **Gemini Model Invariant:** Never call `gemini-2.x` or `gemini-2.5-flash`
> (permanently deprecated / 404 since 2026-08-05). Always use `gemini-3.6-flash`
> (primary) or `gemini-3.5-flash` (fallback), routed through
> `pipeline/vision_adjudication_common.py` (`make_client()` / `adjudicate_with_retry()`).

### 6 — Python & ML Dependency Version Constraints

If installing optional ML/OCR libraries into the venv (e.g., for local model evaluation):
- **PyTorch & NumPy:** `torch 2.2.2` requires `numpy<2` (e.g. `numpy 1.26.4`). Installing `numpy>=2.0` breaks PyTorch C-extensions with `_ARRAY_API not found`.
- **Companion Libraries:** Keep `scipy<1.14` (e.g. `1.13.1`) and `opencv-python-headless<4.10` (e.g. `4.9.0.80`) to prevent NumPy 2.x upgrade conflicts in Python 3.12.

### 7 — Auto-activation with direnv (recommended)

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

### 8 — Verify

```bash
python3 tools/verify_local_setup.py   # checks files, PDFs, credentials, GEMINI_API_KEY
pytest tests/ -q                       # 241 tests as of 2026-08-20; all should pass
```

That 241 splits as 227 gate tests (`test_corpus_invariants.py` 25 +
`test_pipeline_logic.py` 202, both run by `rebuild_all.sh`'s step 6/6) and 14
Playwright browser tests (`test_review_server.py`, outside the gate). The
count grows as tests are added — treat a *higher* number as normal and any
failure as real.

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
