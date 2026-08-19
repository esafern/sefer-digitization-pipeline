# CLAUDE.md / START_HERE.md — historical notes

## TL;DR

**You do not need this file to work on the project.** `START_HERE.md` has the
current, correct state. This is archaeology, kept rather than deleted per this
project's practice of not discarding history just because the incident got
fixed.

**Read it when** you're wondering why a doc claim looks odd, whether a script
you can't find ever existed, or where an archived artifact went.

**What's in it, in one line each:**

- **Pipeline-shape corrections** — the Livorno/Berlin edition mix-up; the
  DocAI-vs-VLM claim that was actually DocAI-vs-stored-text; where
  `part1.json`'s original text came from (traced through git, never fully
  re-traced); `chunker.py` and `orchestrator.py`, both archived as dead.
- **Retired demo/report artifacts** — `review.html`, `SEFARIA-VLM-DEMO.html`
  and the rest, and why each was replaced rather than fixed.
- **Directory-layout history** — the 2026-08-16 flat-root split into
  `pipeline/` + `tools/`, and the `processed_klalim/` directory that was
  documented for months without ever existing.

**The recurring lesson, stated three separate times below because it recurred
three separate times:** *a document's own file-existence and file-location
claims are not automatically true, and need the same verification as any other
claim.* Check the layout against an actual `ls`, never against the previous
version of the document.

---

This file preserves the narrative, self-correction, and reorganization
history that used to live inline in `CLAUDE.md` before it was split into
`START_HERE.md` (current state, for humans and LLM instances) and this file
(archaeology).

Moved here 2026-08-18 when `CLAUDE.md` was split into `START_HERE.md` (a
short `CLAUDE.md` stub remains, redirecting any LLM instance to
`START_HERE.md`). Kept at root, not in `archive/docs/`, because this repo
(unlike the original local working directory) deliberately does not track
`archive/` at all — see `PROJECT-STATUS.md` for that exclusion decision.

## Pipeline shape — correction history

**Printing/edition identification, corrected 2026-08-15.** The original
`CLAUDE.md` marked this detail "CORRECTED 2026-08-15 — verified against the
actual scan and code, not assumed" — flagging that the Livorno-original vs.
Berlin-second-printing distinction (now stated as settled fact in
`START_HERE.md`) had previously been assumed/unverified rather than
confirmed against the scan's own front matter and title page.

**DocAI-vs-VLM comparison claim, corrected before 2026-08-17.** The doc used
to imply the live automated comparison was DocAI vs. VLM. It was corrected
to state the actual comparison: DocAI's raw OCR tokens vs. whatever is
currently stored in `part1.json`. VLM extraction was reclassified as a
secondary, opportunistic manual cross-check, not a systematic leg of the
automated pipeline.

**Where `part1.json`'s original text came from — git archaeology (as of
2026-08-17, not re-traced since).** Traced through git history: the repo's
first commit (`2a5d43e`) contains only extraction/adjudication scripts
(`chunker.py`, `orchestrator.py`, `consensus.py`, `adjudicate_vision.py`,
`extract_hocr.py`, `extract_json.py`, `batch_ocr.py` — all archived now)
plus one sample page's OCR output, no corpus text yet. Those scripts, run
against the Berlin scan, produced `full_text_cleaned_goal.txt`, which went
through many further "OCR fix"/"LLM cross-validation" passes (see early
commit history), and was THEN chunked into `part1.json`/`part2.json`/
`part3.json` for the first time (commit `73c428c`). Only from that point
does the current architecture take over: DocAI's fresh reading gets diffed
against whatever's currently stored, disagreements go to vision-crop
adjudication, then human review, then get applied. The exact internal logic
of that original chunker/orchestrator/consensus-era extraction pass was
never re-traced in detail — it predates the documented architecture and
would need its own investigation if it ever matters (e.g. auditing a
specific very-old piece of text back to its origin).

**`chunker.py`'s status, corrected 2026-08-14.** An earlier version of the
doc described `chunker.py` (the script that pulled raw text per page from
the PDF and handled the reversed-Hebrew-line quirk via `unreverse_line`) as
part of the live path. It was not — it had already been superseded and
archived. This was one of several file-existence claims in the document
found stale around the same time (see "Directory layout" history below).

**`orchestrator.py`, archived 2026-08-11.** Archived after an audit
confirmed it was dead (not in `rebuild_all.sh`, imported only by
already-archived code, entry points pointing at `test_page.pdf`) and
carried 4 real bugs — including a crop-hash-only vision-adjudication cache
that an earlier version of `CLAUDE.md` had wrongly claimed was fixed
project-wide. (The correct, project-wide-fixed version of that cache
pattern is `verify_corrections_vision.py`'s `corrections_cache` table —
see `START_HERE.md`'s vision-adjudication cache-keying rule.)

**`processed_klalim/` claim, corrected 2026-08-16.** An earlier version of
the doc's "Assembly & lexicon" bullet named a `processed_klalim/` directory
that did not exist anywhere in the repo — a claim nobody had caught until a
2026-08-16 root-hygiene pass. See "Directory layout — reorganization
history" below for what that pass actually found (`klalim/`, archived).

## Demos/reports — retired artifacts

`pipeline/review_server.py` is the current live review tool, and
`VERIFIED-AGAINST-THE-INK.html` is the only live demo/report artifact at
root. Both superseded a sequence of earlier, now-archived artifacts:

- **`build_review_html.py` → `review.html`** (a single ~963KB generated
  file with all of Part 1 inlined into one `<script>` tag) was the review
  tool until 2026-08-07. Retired for both a real data-pipeline bug it was
  surfacing (see `PROJECT-STATUS.md` "Punctuation-token diff bug fixed")
  and its own performance/architecture problems. `build_review_html.py` is
  archived at `archive/scripts/build_review_html.py`.
- **`SEFARIA-VLM-DEMO.html`** and its generator `build_vlm_demo.py` were
  archived 2026-08-11 (`archive/docs/`, `archive/scripts/`): the demo was
  built from the discredited `aligned_klalim/`, showed text differing from
  `part1.json` in 145 of 222 Part-1 klalim, and rendered 14 fabricated
  placeholder bounding boxes across all 667 klalim under a "Precise
  Geometric Bounds" heading. Nothing linked it, and it needed no
  replacement — `review_server.py` supersedes it internally (real per-klal
  boxes from `klal_page_regions.json`, live data), and
  `VERIFIED-AGAINST-THE-INK.html` already fills the outward-facing
  evidence-showcase role.
- As of 2026-08-06, one-off `*-VISUAL-REPORT.html` / `*-OVERVIEW.html` /
  similar report docs from earlier in the project (dated through early
  August, superseded once `review.html` became the live verification tool)
  were moved to `archive/docs/`.

## Directory layout — reorganization history

**Root reorganized 2026-08-16.** Root used to be flat: 24 live `.py` files
sitting directly next to `part1.json`, `rebuild_all.sh`, and everything
else, with `CLAUDE.md`'s "Directory layout" section as prose the only map
of which script did what. Per user request ("root should be clean...
consider a code dir or even three"), split into `pipeline/` (the running
system) and `tools/` (standalone/manual scripts), with `tests/` unchanged.

Every script's own `REPO` constant
(`os.path.dirname(os.path.abspath(__file__))`) was updated to go up one
additional directory level so every `os.path.join(REPO, ...)` path still
resolved to the true repo root — verified, not assumed, by re-running
`rebuild_all.sh` post-move with byte-identical output on all 5 derived
files, 108/108 pytest, 14/14 Playwright. `review_frontend/` did not move.
The one cross-directory import the split created —
`tools/apply_punctuation_decisions.py` needing `pipeline/review_decisions.py`
— was handled with an explicit `sys.path.insert()`.

Before this reorg, a full-repo audit confirmed one genuinely disconnected
script (`reconstruct_multipage_klalim.py`) and archived it; everything else
was already live, just partly undocumented in `CLAUDE.md` until that pass.

**Prior correction, 2026-08-14** (kept for the lesson, not just the
history): the "Directory layout" section used to be one long run-on bullet,
and had drifted from reality in three places nobody had caught — a stale
"active root script" claim for an already-archived file, an archived file
listed as active, and a live file missing from the list entirely.
Restructured into sub-bullets and re-verified against an actual `ls` at
root, not against the previous version of the document — the lesson
(applied again at the 2026-08-16 reorg): a document's own file-existence
and file-location claims are not automatically true and need the same
checking as any other claim.

**`processed_klalim/` → real `klalim/`, corrected 2026-08-16.** The
"Directory layout" section's `aligned_klalim/`/`klalim_batches/` bullet
used to also name a third directory, `processed_klalim/`, that does not
exist anywhere in the repo — a claim nobody had caught. The same day's root
hygiene pass found a real, separate `klalim/` (668 per-klal JSON files,
bare/no-suffix name, likely what `processed_klalim/` actually meant to
say) that was tracked but referenced by nothing live (no script, test, or
doc pointed at it) — archived to `archive/data/klalim/`.
