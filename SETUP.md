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
before running any pipeline script — or set up auto-activation once (below)
and skip this step forever after.

### Auto-activation with direnv (optional, recommended)

Manually re-activating the venv every session is easy to forget. This repo
ships a tracked `.envrc` (`source venv/bin/activate`) that
[direnv](https://direnv.net/) uses to activate/deactivate the venv
automatically on `cd` in/out of the repo:

```bash
brew install direnv
# add to ~/.zshrc (or ~/.bashrc): eval "$(direnv hook zsh)"  — then restart your shell
cd /path/to/sefer-digitization-pipeline
direnv allow .          # one-time trust of this repo's .envrc
```

After that, `cd` into the repo activates the venv automatically (you'll see
`direnv: loading .envrc` / `direnv: export ...`), and `cd`-ing out
deactivates it. No `source venv/bin/activate` needed again.

## Files not in the public repo

See `PROJECT-STATUS.md` / ask for the migration walkthrough — `credentials.json`,
the two source PDFs, and several gitignored cache directories
(`docai_word_boxes/`, `document_jsons_berlin/`, `sefaria_reference_corpus/`,
`klalim_docai/`, `llm_klal_starts/`, `sefaria_export/`, `vlm_extractions/`)
must be migrated separately (not via git). `GEMINI_API_KEY` is an environment
variable, not a file — re-export it in your shell profile.
