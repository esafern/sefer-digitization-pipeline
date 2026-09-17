# Setup — Windows

`SETUP.md` is written for macOS. This file is the Windows path, and it is
mostly a much shorter one, because **the review dashboard needs nothing but
Python and the data.** No API key, no cloud credentials, no GPU, no pip
install, not one third-party package.

Written 2026-09-17 for a reviewer's Windows box (item `0HX`). **Part 1 has now been
run on Windows end to end** (2026-09-17): the dashboard serves Sefer HaShorashim
there, scan pane included. Parts 2 and 3 have not — they are the documented Windows
equivalents of what runs on macOS, and the claims about what the code needs
were measured on macOS (the two answers at the end say how). Treat
the first run as the test, and correct this file from it.

---

## Part 1 — A review box (the common case)

You want to open entries, compare our reading against the scan, and record
rulings. That is the whole job, and it runs on a stock Python.

### 1 — Python

Install **Python 3.12 or newer** (the Mac runs 3.14.7):

```powershell
winget install Python.Python.3.14
```

or the installer from <https://www.python.org/downloads/windows/> — tick **"Add
python.exe to PATH"** on the first screen.

**Then close the terminal and open a new one — all of Windows Terminal, not a
new tab.** A shell reads PATH when it starts, and a Windows Terminal tab
inherits the environment the app started with, so a window opened before the
install answers `py` with "not recognized" even though Python is installed.
This was the first thing that happened on the first real install (2026-09-17).
Check it in the new window:

```powershell
py -3 --version
```

`py` is the Windows launcher and is the reliable way to reach a specific
Python; `python` on the PATH may be a Microsoft Store stub.

### 2 — Git

```powershell
winget install Git.Git
```

This also gives you **Git Bash**, which you need only if you ever run the
`.sh` scripts (Part 3).

### 3 — The code

```powershell
mkdir $env:USERPROFILE\work -Force; cd $env:USERPROFILE\work
git clone https://github.com/esafern/sefer-digitization-pipeline.git
cd sefer-digitization-pipeline
git checkout hashorashim-nli-rebuild-and-review
```

**The checkout is not optional.** The repo's default branch is `master`, and
the current work - including every Windows fix in this file - is on
`hashorashim-nli-rebuild-and-review` (as of 2026-09-17). An earlier version of
this step said `cd %USERPROFILE%\work`, which is `cmd.exe` syntax and does
nothing useful in PowerShell.

To pick up later changes: `git pull` in the same directory.

Line endings are pinned by `.gitattributes` (`* text=auto eol=lf`), so the
working tree is LF on Windows too and nothing you save turns a tracked file
into a whole-file diff. Do not set `core.autocrlf` by hand.

### 4 — The book's data

The code carries no book. A book is a **corpus root**: its own directory, its
own private git repo, holding `part1.json`, `review_decisions.jsonl`,
`word_identity.json`, the derived JSON beside them, and an `images\pdf_pages\`
directory of rendered scan pages.

Git carries the text, the rulings and every derived file. It does **not**
carry two folders, and the dashboard needs both:

| folder | what it is | without it |
|---|---|---|
| `images\pdf_pages\` | one PNG per scan page | the scan pane is empty |
| `docai_word_boxes\` | where each word sits on the page | the scan shows no boxes on words - **silently**: every request still succeeds |

Measured 2026-09-17 on a fresh clone of the Sefer HaShorashim repo, served by a
Python with no packages: every route answered, and without `docai_word_boxes`
a page's payload fell from 51 KB to 8.5 KB - the word boxes simply absent.

They travel as one zip per book, made on the owner's Mac. Put the zip in the
book's root folder and extract it there, so it creates `images\pdf_pages\`
and `docai_word_boxes\` beside `part1.json` (Explorer's *Extract All*, or
`tar -xf <zip>` in PowerShell):

| book | root folder | zip | size |
|---|---|---|---|
| Yad Malachi | the code repo itself | `yad-malachi-scan-data.zip` | 155 MB |
| Sefer HaShorashim | its own clone, below | `hashorashim-scan-data.zip` | 433 MB |

Sefer HaShorashim's corpus root is a **private** repo, and its default branch
is not the current one either:

```powershell
cd $env:USERPROFILE\work
git clone --branch nli-fulltone-rebuild https://github.com/esafern/hashorashim.git
```

**No rebuild is needed** to review either book: the derived files are
committed. After rulings are applied, `build_klalim_demo_dataset.py` is the one
step that refreshes what the dashboard shows (Part 2). Never run
`rebuild_all.sh` on the Sefer HaShorashim root.

For Yad Malachi the corpus root **is** the code repo; for any other book it is
a separate directory and you point the server at it.

### 5 — Run it

PowerShell, from the repo:

```powershell
$env:SEFER_CORPUS_ROOT = "C:\Users\<you>\work\hashorashim"
py -3 pipeline\review_server.py --port 8420
```

or `cmd.exe`:

```cmd
set SEFER_CORPUS_ROOT=C:\Users\<you>\work\hashorashim
py -3 pipeline\review_server.py --port 8420
```

Leave that window open — the server runs in the foreground and logs each
request. Open <http://127.0.0.1:8420/> or <http://localhost:8420/>.

For Yad Malachi, leave `SEFER_CORPUS_ROOT` unset.

Stop it with **Ctrl-C** in its window. If a port is stuck:

```powershell
netstat -ano | findstr :8420
taskkill /PID <the last column> /F
```

Windows Firewall should not prompt: the server binds `127.0.0.1`, which never
leaves the machine. If it does prompt, **Cancel** is the right answer — nothing
outside the box needs to reach it.

### 6 — Check it worked

In the browser: the entry list fills, an entry's text appears beside a scan
image, and clicking a coloured word opens its panel.

**Two panes instead of three means the window is narrower than 1200 pixels.**
The index pane is hidden below that width, by design, and with it the settings
button and the reviewer name. Widen or maximize the window. Windows display
scaling counts here: at 150%, a 1920-pixel screen is 1280 pixels to the
browser. If the text is there and
the scan pane is empty, `images\pdf_pages\` did not come with the corpus root.

A ruling you record is appended to `review_decisions.jsonl` in the corpus root.
That file is the record of your work — it is committed to the corpus repo, and
it is the one thing on the box that cannot be regenerated.

---

## Part 2 — Promoting rulings into the text

Recording a ruling and applying it are two deliberate steps, both stdlib-only:

```powershell
py -3 pipeline\apply_reviewer_decisions.py --dry-run
py -3 pipeline\apply_reviewer_decisions.py
py -3 pipeline\build_klalim_demo_dataset.py
py -3 pipeline\audit_applied_decisions.py
```

(`$env:SEFER_CORPUS_ROOT` set as in step 5 for any book other than Yad Malachi.)

Always the dry run first. The audit is read-only and answers the opposite
question: for every decision the log says was applied, does the corpus still
show it?

**No model, no network, no key is involved in any of this** — see the answers
at the bottom.

---

## Part 3 — A full pipeline box (only if you are ingesting or rebuilding)

Everything above is the reviewer's half. Rebuilding derived data, cropping the
PDF, running OCR or the vision adjudicator needs the packages and the keys:

```powershell
py -3 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
playwright install chromium          # browser tests only
$env:GEMINI_API_KEY = "..."          # your own key
py -3 -m pytest tests\test_pipeline_logic.py tests\test_corpus_invariants.py -q
```

The venv's interpreter is `venv\Scripts\python.exe`, not `venv/bin/python`.

**A rebuild is local except for one step.** Every stage of `rebuild_all.sh`
runs on this machine; the only one that calls out is
`verify_corrections_vision.py`, the Gemini vision adjudicator, and
`--skip-vision` leaves it out. Checked 2026-09-17 by reading each stage's
imports: nothing else imports a network or cloud library.

**`rebuild_all.sh` is a bash script.** Run it from **Git Bash** or WSL; it now
finds either venv layout (`venv/bin/python`, else `venv/Scripts/python.exe`)
and says so if it finds neither. Under WSL, remember it is a different
filesystem and a different venv — build one inside WSL rather than reusing the
Windows one.

Hebrew in the console: use **Windows Terminal**, not the old `conhost` console.
If Hebrew comes out as question marks, `chcp 65001` sets the code page to
UTF-8. This affects only what you can read in the terminal; every file this
repo writes is UTF-8 explicitly, whatever the console is doing.

---

## Is any AI involved in reviewing, deciding, and applying?

**No.** Measured, not assumed:

* The import closure of the dashboard and the two apply/audit tools —
  `review_server.py` and the modules it reaches, `apply_reviewer_decisions.py`, `audit_applied_decisions.py`,
  `build_klalim_demo_dataset.py`, `tools/export_corpus.py` — is 12 files and
  imports **one** package outside the standard library: `python-bidi`, and that
  import is caught in a `try` and used only when a tool renders a Hebrew report
  for a terminal.
* Proved by running it: a `venv --without-pip` with no `bidi`, `fitz`, `numpy`,
  `PIL` or `google` package served `/`, `/api/corpus`, `/api/klal/1`,
  `/api/klal/1/versions`, `/api/page/58` and a 3.6 MB scan PNG, all `200`.
* No network call of any kind: nothing in that closure imports `requests`,
  `urllib.request`, or a cloud SDK.

**What AI did do is upstream of you.** The words on screen are an OCR engine's
reading; the disagreements the dashboard shows you were found by diffing
engines against each other; the "machine's proposal" on a panel is a cached
verdict from a vision model that ran months ago. None of it runs, or is
consulted, when you rule — you are reading a stored opinion and then reading
the ink.

## Is AI required to ingest a new sefer?

**Yes, for the reading. Optionally, for the triage.**

* **OCR is the AI that cannot be removed.** A scan has to become text, and here
  that is Google Document AI (`tools/extract_docai_pages.py`, a paid cloud job,
  a service-account key, once per book). Any substitute is another model.
* **The second and third witnesses are models too.** The pipeline's core claim
  is that one engine's reading is not evidence — a disagreement between engines
  that fail differently is what tells a human where to look. Those witnesses
  have been a VLM read twice, Surya at 300 DPI, and for Sefer HaShorashim
  Sefaria's own OCR.
* **The vision adjudicator is a model, and it is the removable one.** It crops
  each disputed word from the page and asks a Gemini vision call which reading
  the ink supports, caching every answer. `rebuild_all.sh --skip-vision` runs
  the chain without it. What you lose is triage, not text: the disagreements
  are still found and still queued, just unranked and unclassified, so a human
  reads more of them.

So: **a new book needs AI to be read, and a human to be trusted.** The
reviewing half of this system — the part this Windows box is for — is ordinary
deterministic software, and that is deliberate: a ruling has to be a person's.
