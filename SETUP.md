# Setup

## TL;DR

A handful of steps, and **two of them are the ones that actually bite**:

```bash
brew install python@3.14 direnv          # step 0 - Homebrew prerequisites
git clone https://github.com/esafern/sefer-digitization-pipeline.git
cd sefer-digitization-pipeline
git config user.email "<YOUR GitHub noreply address>"   # yours, not the owner's - step 1
tar -xf <the data tarball>               # ← obtained out-of-band - step 2
python3.14 -m venv venv && source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
playwright install chromium              # ← separate from pip; easy to skip
export GEMINI_API_KEY="..."              # your own key; put it in ~/.zshrc
python3 tools/verify_local_setup.py && pytest tests/ -q
```

**Setting up as a collaborator rather than on the owner's own machine?** Read
"Working on this repo as a collaborator" below before you branch: the
default branch is not the current one, and some data is not yours to be sent.

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

### 0 — Homebrew prerequisites

```bash
brew install python@3.14     # the version the working venv runs (3.14.7 as of 2026-09-15)
brew install direnv          # optional, recommended - step 7
brew install gh              # optional - pull requests from the terminal
```

`git` comes with the Xcode command-line tools (`xcode-select --install`) if it
is not already there. Nothing in the live pipeline needs `tesseract`: three
scripts still shell out to it for the retired Tesseract witness, so install it
(`brew install tesseract tesseract-lang`) only if you are running those. Surya
and the other ML engines are pip packages, not Homebrew ones - see step 6.

### 1 — Clone the repo

```bash
git clone https://github.com/esafern/sefer-digitization-pipeline.git
cd sefer-digitization-pipeline
```

Configure git with **your own** GitHub noreply address (required - GitHub
blocks pushes that expose a private email address). It is on
<https://github.com/settings/emails>, shaped `ID+login@users.noreply.github.com`:

```bash
git config user.email "<ID>+<your-login>@users.noreply.github.com"
```

The owner's machines use `109570+esafern@users.noreply.github.com`. Do not copy
that onto yours, or your commits are attributed to the owner.

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

**The owner's tarball carries `credentials.json`, a Google Cloud
service-account key. A collaborator's copy should not.** Only
`tools/extract_docai_pages.py` reads it, to run Document AI OCR over scan pages
(a paid job, done once per book), and nothing a collaborator reviews, tests or
rebuilds needs it. `verify_local_setup.py` lists it as recommended, not
required, for that reason.

**Some of it can be rebuilt instead of copied:**

```bash
# The source PDF: download the Berlin scan yourself from Google Books
# (START_HERE.md, "The scan") and apply the leaf-order fix, rather than being
# sent a copy - the Google Books terms govern redistribution. Save the download
# as berlin_square_original_transposed.pdf: the checker expects both files, and
# the original stays as the diffable reference.
python3 tools/fix_transposed_leaf.py --pdf berlin_square_original_transposed.pdf \
    --from-index 37 --to-index 36 --output berlin_square_corrected.pdf

python3 tools/render_pdf_pages.py --all              # images/pdf_pages/ - 150 dpi, pixel-identical to the owner's
python3 tools/fetch_sefaria_reference_corpus.py      # sefaria_reference_corpus/raw/ - the RABBINIC register (network)
./rebuild_all.sh --skip-vision                       # every derived data file, no Gemini calls
```

Three traps in those lines, each found the hard way on 2026-09-15 (item `0HB`):
* **Leave `--verify` off `render_pdf_pages.py` for now.** It reported pages 14
  and 15 as failed ("boxes not on their words") on renders pixel-identical to
  the owner's working images. The check is wrong, not the render.
* **Fetch the DEFAULT register only.** `--register tanakh` and `--register all`
  add the Bible books Sefer HaShorashim uses, and the folder is shared. The
  next run of `tools/validate_lexicon_independent.py` then REBUILDS
  `sefaria_reference_corpus/word_freq.json` from every book on disk. That is
  the attestation table Yad Malachi's detectors score against, and changing
  its book set changes the basis of every recorded lexical number (`0EU`).
* **`validate_lexicon_independent.py` has no `--help`.** Any run of it,
  including one meant only to read its usage, rebuilds that table when it
  looks stale.

For lexical numbers comparable with the ones on record, ask the owner for the
`sefaria_reference_corpus/` in the 2026-08-18 migration tarball rather than
fetching it: exactly the 166 rabbinic books and the `word_freq.json` built from
them (6,180,337 words). Two reasons. Sefaria's texts change, so a fresh fetch
is not the corpus those numbers were measured on. And the counting has changed
since the table was built (`0HB`), so even the same 166 files now count to
6,187,331. The owner's live folder is NOT the one to copy: it also holds the 39
Bible books, which would trigger the rebuild described above.

`docai_word_boxes/` cannot be rebuilt without Document AI and the key above. It
is the one directory a collaborator must be sent.

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
python3 tools/verify_local_setup.py   # checks files, PDFs, the venv; key and credentials are warnings
pytest tests/ -q                       # all should pass
```

No test count is written here, on purpose: every one this file and
START_HERE.md ever carried went stale. Get it from the runner,
`pytest tests/ --collect-only -q | tail -1`. `test_corpus_invariants.py` and
`test_pipeline_logic.py` are the gate `rebuild_all.sh` runs; the Playwright
browser tests (`test_review_server.py`) sit outside it. Any failure is real.

---

## Working on this repo as a collaborator

**Branch from the current branch, not from `master`.** The clone checks out
`master`, which lags the working branch - on 2026-09-15 it was 24 commits
behind `hashorashim-nli-rebuild-and-review`. Ask the owner which branch is
current, then:

```bash
git fetch origin
git switch -c <your-branch> origin/<current-branch>
```

**Pushing needs write access.** The repo is `esafern/sefer-digitization-pipeline`:
either the owner adds you as a collaborator on GitHub, or you fork it and open
pull requests from the fork.

**This repository is PUBLIC.** START_HERE.md's rules bind every contributor,
and three matter on day one:
* private correspondents are named by ROLE, never by name - in commits, code,
  comments and file names alike;
* never commit `credentials.json` or any key (`.gitignore` covers the known
  ones);
* read START_HERE.md, then PROJECT-STATUS.md, before changing anything. If you
  work with Claude Code, `CLAUDE.md` routes it there.

**Building a different interface?** `REVIEW-API.md` documents the review
server's HTTP API. It also shows how to run the server on a sandbox corpus, so
that test clicks never reach the owner's `review_decisions.jsonl`.

**The second book, Sefer HaShorashim, is not in this repo.** Its corpus lives
in a separate PRIVATE repository holding data Sefaria has not released, and
the pipeline reaches it through `SEFER_CORPUS_ROOT`. Access is the owner's
decision, and its large files are not in that repo either. Without it,
everything here runs on Yad Malachi.

---

## Files not in the public repo

`credentials.json` (Document AI extraction only - see step 2),
`berlin_square_corrected.pdf`, `berlin_square_original_transposed.pdf`, and
the following cache directories are gitignored and must be migrated separately
(step 2 above handles all of them if the tarball is complete):

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
