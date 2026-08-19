# Pipeline Data Reference

What every JSON/JSONL file in this pipeline actually contains, in the order
data flows through them. Each entry below shows one real record pulled
straight from the live files in this repo, with every field explained and
a note on what stage of the pipeline reads and writes it. This is a
reference for the data shapes, not the process — see `START_HERE.md`'s
"How the pipeline works" and "Directory layout" sections for the scripts that
produce each file, and `PROJECT-STATUS.md` for what's currently open.

Written for **Part 1** (*Klalei HaGemara*), the only part with the full
chain built out as of this writing; Parts 2–3 currently have the corpus
files, the marker-position trace, and the page-region files, but not yet
the corrections pipeline (candidates → verified → final) or an
alignment file — see `PROJECT-STATUS.md` for the live state.

## TL;DR

**Read this first if you're about to load a file by hand — then don't.** Use
`pipeline/corpus_io.py`; every loader here already exists there.

**Three things in this data that will mislead you:**

1. **`corrections_candidates_part1.json`'s field names are inverted from what
   they suggest.** `original_word` is Document AI's *fresh OCR reading*;
   `corrected_word` is the corpus's *currently stored* text — not a proposed
   fix. Downstream stages rename these to the honest `docai_reading` /
   `final_text`. Verified against `build_corrections_dataset.py`'s actual
   `SequenceMatcher` call, not inferred from the names.
2. **The corrections chain is three files, and only the last one is real.**
   `candidates` → `verified` → `corrections_part1.json`. The dashboard shows
   the third. The first two are intermediates and will disagree with the corpus
   if you read them directly.
3. **`review_decisions.jsonl` is append-only and lives outside the rebuild.**
   Nothing in `rebuild_all.sh` reads or writes it. A later row supersedes an
   earlier one for the same `(klal_id, word_index)`; there is no update or
   delete. Reading it means replaying it.

**The one-line map.** `docai_word_boxes/` (raw OCR) and `part*.json` (the
corpus) are the two primary inputs; everything else on this page is derived
from them and regenerable, except `review_decisions.jsonl`, which is neither.

## The flow, in one pass

```
scan (PDF)
  │  Google Document AI OCR
  ▼
docai_word_boxes/page_N.json         ← raw OCR tokens, one file per scan page
  │
  │  (historical: an early, undocumented chunking/extraction pass — see
  │   START_HERE.md's "How the pipeline works" — produced the first version of the
  │   corpus text; everything below this line is the LIVE, current pipeline)
  ▼
part1.json / part2.json / part3.json  ← THE CORPUS. Hand-edited only through
  │                                      the decision pipeline below, never
  │                                      directly.
  │
  ├──────────────► klalim_demo_dataset.json   (the 3 parts, concatenated)
  │
  ├──► build_corrections_dataset.py: diff DocAI's fresh OCR against this
  │     klal's CURRENTLY STORED text
  │       ▼
  │     corrections_candidates_part1.json     (stage 1: raw disagreements)
  │       │
  │       │  verify_corrections_vision.py: crop the scan, ask a vision
  │       │  model to pick between the two readings
  │       ▼
  │     corrections_verified_part1.json       (stage 2: + vision verdict)
  │       │
  │       │  assemble_corrections_dataset.py: classify each verdict into a
  │       │  flag, drop/relabel anything that's drifted since verification
  │       ▼
  │     corrections_part1.json                (stage 3: final — this is
  │                                              what the dashboard shows)
  │
  ├──► build_klal_page_regions.py ──► klal_page_regions.json  (scan bbox
  │                                     per klal, for the crop pane)
  │
  ├──► build_gematria_trace.py ──► gematria_trace_part1/2/3.json (marker
  │                                  position + verification, all 3 parts)
  │
  └──► (older mechanism, still live) part1_header_anchored_alignment.json
        (page-to-klal alignment by section-header matching)

review_server.py serves ALL of the above, fresh off disk on every request,
merged with the human/AI decision layer:

review_decisions.jsonl   ← every reviewer/AI decision, APPEND-ONLY, tracked
  │                          in git, outside the rebuild pipeline entirely
  │
  │  apply_reviewer_decisions.py: promote an accepted decision
  ▼
part1.json   (closes the loop — a decision becomes corpus text)
```

`./rebuild_all.sh` runs the five build scripts in the order shown (through
`klal_page_regions.json`) every time `part1.json` changes. The gematria
trace and the alignment file are built separately, not part of that chain.
`review_decisions.jsonl` is never touched by any of it — see `START_HERE.md`'s
"Human review decisions" for why that separation is deliberate.

---

## `docai_word_boxes/page_N.json`

**One file per scanned PDF page** (gitignored — regenerated by re-running
DocAI extraction against the source PDF, not tracked in git). The raw
material everything downstream is built from: every word token Document AI
found on that page, with its bounding box.

```json
{
  "text": "42",
  "x1": 0.8296296000480652,
  "y1": 0.06361426413059235,
  "x2": 0.8641975522041321,
  "y2": 0.07293354719877243
}
```

| Field | Meaning |
|---|---|
| `text` | The literal string Document AI read for this token — a page number, a running header word, a klal's numeral marker, an ordinary word, punctuation. Nothing is filtered out at this stage. |
| `x1`, `y1`, `x2`, `y2` | The token's bounding box, normalized 0–1 as a fraction of the page's width/height — independent of scan resolution or DPI, so any later script can re-crop the exact same spot at whatever DPI it needs. |

A page's file is a flat JSON array of these, in whatever order Document AI
extracted them — **not necessarily reading order**. This has bitten the
pipeline more than once: a klal's bold marker glyph can be array-indexed
*after* the line of text it visually precedes, and Document AI can extract
one decoratively-set word twice as two separate tokens (see
`VERIFIED-AGAINST-THE-INK.html`'s klal 82/83 example). Every script that
needs true reading order re-derives it from `(y-center, then x)`, never
trusts the array order — `corpus_io.center_y()` is the shared helper.

---

## `part1.json` / `part2.json` / `part3.json`

**The corpus. The only hand-edited source of truth for klal text**, one
file per part of the work. Every other file in this pipeline is either
built *from* these or exists to propose a change *to* them — nothing else
is ever edited in parallel. A `part*.json` file is a flat JSON array, one
object per klal:

```json
{
  "klal_id": 1,
  "gematria": "א",
  "section": "כללי האלף",
  "title": "אי תניא תניא",
  "clean_text": "א אי תניא תניא • מדברי רש\"י ז\"ל בפ\"ב דנדרים י\"ט ב' ...",
  "page": 14
}
```

| Field | Meaning |
|---|---|
| `klal_id` | The klal's number in the corpus's own running sequence, 1–667 across all three parts (1–222 in Part 1, 223–444 in Part 2, 445–667 in Part 3). This is the key almost every other file in the pipeline uses to refer back to a specific klal. |
| `gematria` | The klal's number written as a Hebrew numeral (e.g. `א` = 1), matching the bold marginal marker the print itself uses to open each klal. |
| `section` | The alphabetical section this klal falls under within its part (e.g. `כללי האלף`, "the rules of Aleph") — Yad Malachi's own organizing structure, one letter of the alphabet at a time. |
| `title` | A short label for the klal, generally its own opening words — used for navigation, not part of the klal's actual running text. |
| `clean_text` | **The klal's full text**, as one string, opening with its own gematria marker. This is what every word-index in every other file in this pipeline points into — `clean_text.split(" ")` is how a `word_index` becomes an actual word, everywhere in the codebase. |
| `page` | The scan page (1-indexed into the source PDF) this klal's own gematria marker sits on — its starting page; a long klal continues onto further pages, tracked separately in `klal_page_regions.json`'s `continuations`. |

---

## `klalim_demo_dataset.json`

**Purely derived — `part1.json` + `part2.json` + `part3.json`, concatenated,
nothing else.** Same per-klal shape as above, 667 entries. Regenerated by
`build_klalim_demo_dataset.py` any time the parts change; never hand-edited
(a hand-maintained copy of this was the exact "two copies of the truth"
failure mode `START_HERE.md`'s Lesson 13 documents — this file exists precisely
so that mistake can't recur).

---

## `corrections_candidates_part1.json` — stage 1

**Every place Document AI's fresh OCR reading disagrees with what's
currently stored in `part1.json`**, for one klal at a time. This is a raw
diff — nothing here has been checked against the actual scan image yet.

```json
{
  "corrections": [
    {
      "klal_id": 1,
      "page": 14,
      "opcode": "replace",
      "word_index_in_final_text": 85,
      "original_word": "לכן",
      "corrected_word": "לכו",
      "bbox": { "x1": 0.300, "y1": 0.360, "x2": 0.327, "y2": 0.373 }
    }
  ],
  "meta": {
    "total_candidates": 387,
    "klalim_covered": 149,
    "skipped_no_docai_page_klalim": [],
    "unattributable_deletes": [],
    "untrusted_klalim_excluded": []
  }
}
```

| Field | Meaning |
|---|---|
| `klal_id`, `page` | Which klal this disagreement belongs to, and which scan page it sits on. |
| `opcode` | `replace` (DocAI read a different word than what's stored), `insert` (the stored text has a word DocAI's reading doesn't), or `delete` (DocAI saw a word the stored text is missing). |
| `word_index_in_final_text` | The position (0-indexed into `clean_text.split(" ")`) in the klal's **currently stored** text this disagreement is anchored to. |
| `original_word` | **Confusingly named — this is Document AI's own fresh OCR reading**, not the corpus's original text. |
| `corrected_word` | **Also confusingly named — this is what's CURRENTLY STORED** in `part1.json` right now, not a proposed fix. Downstream stages rename these two fields to `docai_reading` and `final_text`, which say what they actually are; this stage still uses the names the diff script happened to give them. |
| `bbox` | The union of the disagreeing tokens' bounding boxes on the scan page — what the vision-adjudication step crops. |
| `meta.total_candidates` / `klalim_covered` | How many disagreements were found, and across how many distinct klalim. |
| `meta.skipped_no_docai_page_klalim` | Klalim this pass couldn't compare at all — no DocAI extraction available for their page. |
| `meta.unattributable_deletes` | A `delete` candidate the script found but couldn't confidently attribute to a specific klal/position (see the script's own comment on why a klal-boundary `delete` is genuinely ambiguous — it could belong to either neighbor). |
| `meta.untrusted_klalim_excluded` | Klalim this pass deliberately skipped because their page-to-klal alignment isn't trusted yet (see `part1_header_anchored_alignment.json` below) — comparing against an unreliable alignment would manufacture false disagreements. |

Written by `pipeline/build_corrections_dataset.py`, the second of
`rebuild_all.sh`'s five build stages (after `build_klalim_demo_dataset.py`).

---

## `corrections_verified_part1.json` — stage 2

**Every candidate from stage 1, with a vision model's verdict added.** For
each one, the pipeline crops the exact bounding box from the scan PDF and
asks a vision model to choose between the two readings — never to invent a
third — naming which one the pixels actually support.

```json
{
  "klal_id": 1,
  "page": 14,
  "opcode": "replace",
  "word_index_in_final_text": 85,
  "original_word": "לכן",
  "corrected_word": "לכו",
  "bbox": { "x1": 0.300, "y1": 0.360, "x2": 0.327, "y2": 0.373 },
  "vision_selected": "B",
  "vision_transcription": "לכו",
  "vision_confidence": 0.98,
  "vision_reasoning": "The context cites Rashi's commentary ('הואיל ויש משנה בידכם לכו אחריה'), where 'לכו' (go / follow) is grammatically and contextually correct. Paleographically, the character following the kaf ('כ') is a vav ('ו') that terminates at the baseline, rather than extending below it as a final nun ('ן') would."
}
```

Same fields as stage 1, plus:

| Field | Meaning |
|---|---|
| `vision_selected` | `"A"` = the model picked Document AI's reading (`original_word`); `"B"` = the model picked the currently-stored text (`corrected_word`); `"UNCERTAIN"` = the crop was too ambiguous to call — an honest non-answer, not a guess; `"ERROR"` on an API failure. |
| `vision_transcription` | What the model itself transcribed from the crop, independent of which of the two labeled options it picked — a second, freer signal alongside the forced choice. |
| `vision_confidence` | The model's own stated confidence, 0–1, in its selection. |
| `vision_reasoning` | The model's full explanation — always paleographic (letter-shape) and/or semantic (does the resulting phrase make sense), always citing the actual crop, never "it looks right." |

In this example: DocAI's fresh OCR read `לכן` (option A), but `part1.json`
already stored `לכו` (option B) — and the model selected B, siding with the
current text and rejecting DocAI's reading as the OCR error. (See
`VERIFIED-AGAINST-THE-INK.html`'s "structured record" section for the same
mechanism on a different word, laid out step by step.)

Written by `pipeline/verify_corrections_vision.py` (stage 3/6 of
`rebuild_all.sh`), the only stage that spends API calls — cached in
`adjudication_cache.db`, keyed on the crop **and** which two readings were
being compared (`START_HERE.md`'s Lesson 12: keying on the crop alone let a
stale verdict from an earlier comparison silently answer a different one).

---

## `corrections_part1.json` — stage 3 (final)

**What the review dashboard actually reads.** Every verified candidate,
classified into a flag and checked for drift, grouped by klal_id. Field
names here are the clear ones — `docai_reading`, `final_text` — because
this is the stage meant to be read by something other than the scripts
that built it.

```json
{
  "1": [
    {
      "word_index": 85,
      "opcode": "replace",
      "docai_reading": "לכן",
      "final_text": "לכו",
      "page": 14,
      "bbox": { "x1": 0.300, "y1": 0.360, "x2": 0.327, "y2": 0.373 },
      "vision_selected": "B",
      "vision_transcription": "לכו",
      "confidence": 0.98,
      "reasoning": "The context cites Rashi's commentary...",
      "flag": "current_text_confirmed"
    }
  ]
}
```

Top level is an object keyed by `klal_id` (as a string), each value the
list of that klal's correction entries. `docai_reading` / `final_text` are
the renamed, clear versions of stage 1's `original_word` / `corrected_word`
— same values, better names. `confidence` / `reasoning` are the renamed
`vision_confidence` / `vision_reasoning`. New field:

| Field | Meaning |
|---|---|
| `flag` | The one field the dashboard's color-coding actually reads. `current_text_confirmed` (replace, vision picked B, high confidence — the stored text is right, shown Machine-Resolved unless a human overrides it); `current_text_may_be_wrong` (replace, vision picked A — an open dispute, Machine-Disputed); `possible_omission` (delete, vision confirms DocAI saw a word the corpus is missing); `unverified_insertion` (insert-type — the stored text has an extra word DocAI's reading doesn't, not vision-checked); `ambiguous` (low confidence, or the model said UNCERTAIN); `stale_candidate` (the word at this position has changed since the candidate was generated — e.g. an earlier fix shifted indices — so this candidate no longer describes anything real; treated as open rather than silently trusted). |

A word's on-screen color always follows a **human decision first** (from
`review_decisions.jsonl`, merged in at serve time — see below), then this
`flag`, then falls back to open. This file itself never records a human
judgment; it's the machine's own best current read.

Written by `pipeline/assemble_corrections_dataset.py` (stage 4/6 of
`rebuild_all.sh`).

---

## `klal_page_regions.json`

**Where each klal actually sits on the scan** — independent of whether it
has any flagged correction — what the review dashboard's scan pane
highlights.

```json
{
  "2": {
    "page": 14,
    "bbox": { "x1": 0.1238, "y1": 0.7362, "x2": 0.8830, "y2": 0.9822 },
    "token_count": 213,
    "continuations": [
      {
        "page": 15,
        "bbox": { "x1": 0.1214, "y1": 0.0551, "x2": 0.8780, "y2": 0.5100 },
        "token_count": 486
      }
    ]
  }
}
```

| Field | Meaning |
|---|---|
| `page` | The scan page this klal's own text region starts on (its marker's page). |
| `bbox` | The bounding box of this klal's text on that starting page — `x1/y1` top-left, `x2/y2` bottom-right, normalized 0–1. |
| `token_count` | How many DocAI tokens fall inside that box — a rough size/density check, not otherwise used downstream. |
| `continuations` | Present only when the klal's text runs onto further pages (klal 2 here starts near the bottom of page 14 and mostly continues on page 15) — one entry per additional page, same `page`/`bbox`/`token_count` shape, so the scan pane can keep the highlight following the klal across a page-flip. |

Written by `pipeline/build_klal_page_regions.py` (stage 5/6 of
`rebuild_all.sh`) — the last stage before the pytest gate. Anchors each
region on the klal's marker position from `gematria_trace_part1.json`
where available ("marker-anchored"), falling back to a cruder heuristic
where the trace couldn't place a marker.

---

## `gematria_trace_part1.json` / `_part2.json` / `_part3.json`

**For every klal: where its own marginal numeral marker actually sits on
the scan, and whether the text right after it matches what's stored.**
This is the file `klal_page_regions.json` (and several standalone
validators) build on — the closest thing this pipeline has to ground truth
for "does this klal genuinely start here."

```json
{
  "klal_id": 1,
  "page": 14,
  "expected_gematria": "א",
  "stored_gematria": "א",
  "content_match_ratio": 0.375,
  "status": "marker_found_content_mismatch",
  "marker_position": 0
}
```

| Field | Meaning |
|---|---|
| `klal_id`, `page` | Which klal, and which scan page its marker was found on. |
| `expected_gematria` | The Hebrew-numeral marker this klal_id *should* carry, computed from `klal_id` itself (e.g. klal 115 should read `קטו`, not the naively-converted `קיה` — the conversion has a documented ט"ו/ט"ז exception). |
| `stored_gematria` | The `gematria` field `part1.json` actually has stored for this klal — compared against `expected_gematria` as an independent internal-consistency check. |
| `marker_position` | The index into that page's raw `docai_word_boxes` token array where the marker token was found (`null` if never located). |
| `content_match_ratio` | How well the text immediately following the marker (in true reading order, not array order) matches this klal's own stored opening — 0.0 (no relation) to 1.0 (exact). |
| `status` | `ok` (marker found, content agrees); `marker_found_content_mismatch` (marker located, but the following text doesn't match what's stored — exactly what this entry shows, and exactly the shape a Pattern-A/Pattern-B corruption produces, see `PROJECT-STATUS.md`); `marker_not_found_in_window` (no plausible marker found at all near where the cursor expected one). |

Built by `pipeline/build_gematria_trace.py`, written generically enough to
trace any of the three parts (or all three as one continuous sequence,
sharing a monotonic search cursor) — not part of `rebuild_all.sh`, run
manually, and never auto-applied to corpus text; a trace result is a lead
for a human to check against the scan, not a correction by itself.

---

## `part1_header_anchored_alignment.json`

**An older, separate mechanism for the same underlying question the
gematria trace answers** — which scan page each klal genuinely belongs
to — by matching each klal's expected alphabetical section header against
the page headers Document AI actually read, walking forward through the
pages.

```json
{
  "klal_id": 1,
  "expected_section": "האלף",
  "matched_page": 14,
  "matched_page_header": "האלף",
  "match_ratio": 0.75,
  "trusted": true,
  "search_stage": 0,
  "jump_tokens": 401,
  "lexicon_hit_rate": 0.998
}
```

| Field | Meaning |
|---|---|
| `expected_section` | The alphabetical section (from `part1.json`'s own `section` field) this klal should fall under. |
| `matched_page`, `matched_page_header` | The scan page the search landed on, and what its running header actually read. |
| `match_ratio` | How closely the found header matches the expected section name. |
| `trusted` | Whether this match clears the bar to be relied on downstream — `build_corrections_dataset.py` skips comparing any klal whose alignment isn't trusted (see that file's `meta.untrusted_klalim_excluded` above), rather than manufacture false disagreements against an unreliable page. |
| `search_stage` | Which tier of the search strategy found this match (an earlier, stricter tier is more trustworthy than a later, looser fallback). |
| `jump_tokens` | How far forward the search had to scan from its last confirmed position to find this match — a large jump is itself a signal worth a second look. |
| `lexicon_hit_rate` | What fraction of the words on the matched page are recognized Hebrew vocabulary — a page that's mostly gibberish (a bad OCR page, or the wrong page entirely) scores low here independent of whether the header string happened to match. |

Predates `gematria_trace_*.json` and answers a related but not identical
question (page-level section alignment vs. exact klal-marker position);
both are still live and consulted independently — see `START_HERE.md`'s Lesson
15 for a concrete case (13 Part-1 klalim) where a low `match_ratio` here
correctly predicted that `build_corrections_dataset.py` would find nothing
to compare, before the gematria trace existed to explain why.

---

## `punctuation_candidates_part1.json`

**A separate, secondary candidate pipeline**, parallel to the main
corrections chain: proposed sentence/clause-break insertion points,
drafted by an LLM reading each klal's continuous, unpunctuated running
text.

```json
{
  "1": [
    {
      "before_word_index": 87,
      "reasoning": "Marks the end of Rashi's quoted text and the beginning of the author's inference ('דנראה דשינה').",
      "word_before": "אחריה",
      "word_after": "דנראה"
    }
  ]
}
```

| Field | Meaning |
|---|---|
| `before_word_index` | Where a break is proposed — immediately before this word index in the klal's `clean_text`. |
| `reasoning` | Why: what shifts at this point (end of a quotation, start of the author's own inference, a new citation, etc). |
| `word_before`, `word_after` | The two words the proposed break falls between — enough context to judge the proposal without reopening the full klal text. |

Keyed by `klal_id` like `corrections_part1.json`. Reviewed the same way as
a correction — the dashboard shows each as a clickable marker in the text
pane — but accepted/rejected through `punctuation_choice` decisions (below)
rather than `candidate_choice`, and promoted into the corpus by a separate
script, `tools/apply_punctuation_decisions.py`. Not part of
`rebuild_all.sh`; secondary to the main correction pipeline by standing
priority.

---

## `review_decisions.jsonl`

**The human-and-AI decision log — append-only, one JSON object per line,
tracked in git, and deliberately outside the rebuild pipeline entirely**
(see `START_HERE.md`'s "Human review decisions"). Nothing in this file is ever
edited or removed once written; a changed mind is a *new* line, not an
edit to the old one. Six decision types share the same envelope:

```json
{
  "id": "30eb75cf11db",
  "ts": "2026-08-08T22:16:43.808886+00:00",
  "decision_type": "candidate_choice",
  "klal_id": 3,
  "word_index": 175,
  "chosen_source": "final_text",
  "chosen_text": "מלמד",
  "candidate_snapshot": { "...": "the full corrections_part1.json entry this decision was made against" },
  "needs_revisit": null,
  "note": "...",
  "reviewer": "local",
  "applied_decision_id": null
}
```

**Envelope fields, present on every line:**

| Field | Meaning |
|---|---|
| `id` | A short random id for this decision — how `apply_event` rows and `applied_decision_id` refer back to it. |
| `ts` | When this decision was recorded, ISO 8601. |
| `decision_type` | Which of the six kinds this line is — see below, each uses the shared fields differently. |
| `klal_id`, `word_index` | Which word this decision is about. `word_index` is `null` for a klal-wide note rather than a specific word. |
| `reviewer` | Who/what recorded it — a human reviewer's tag, or an AI pass's own name (e.g. `ai-vision-verify-flagged-candidates`) when the "decision" is itself a flagged finding awaiting human review, not a human's own judgment. |
| `note` | Free-text reasoning — for a human decision, why; for an AI-pass finding recorded as a `klal_flag`, its full analysis. |
| `applied_decision_id` | Set only on an `apply_event` row (see below) — which decision it promoted. |

**The six `decision_type` values**, and what the shared `chosen_source` /
`chosen_text` / `candidate_snapshot` / `needs_revisit` fields mean for each:

- **`candidate_choice`** — a reviewer's ruling on a machine-flagged
  correction from `corrections_part1.json`. `chosen_source` is `"docai_reading"`, `"final_text"`, or `"custom"` (the reviewer typed something neither option offered); `chosen_text` is the resulting word; `candidate_snapshot` is the full correction entry this was decided against, kept so a later corpus edit can be checked for drift (see `apply_reviewer_decisions.py`'s own drift guard).
- **`manual_correction`** — a reviewer flagging and fixing a word the
  machine pipeline never flagged at all (no `corrections_part1.json` entry
  behind it). `candidate_snapshot` here is just `{"word_index": ..., "original_word": ...}` — there was no machine candidate to snapshot. `chosen_text: ""` means marked for deletion, not replacement.
- **`klal_flag`** — a klal (or, if `word_index` is set, one specific word
  within it) flagged as needing a closer look, with `needs_revisit`
  true/false. This is also how an AI pass (a semantic spot-check, a
  lexicon-gap sweep, a vision cross-check) records a finding for a human
  to triage — `reviewer` names the pass, `note` carries its full reasoning.
  `review_server.py` synthesizes any *open*, word-indexed `klal_flag` into
  a highlightable entry in the text pane at serve time (opcode `ai_flag`)
  — this is presentation logic, not a seventh file format.
- **`punctuation_choice`** — accept/reject on a
  `punctuation_candidates_part1.json` proposal; `chosen_source` is
  `"accept"` or `"reject"`.
- **`witness_choice`** — a reviewer's ruling on a DocAI-vs-Tesseract
  disagreement from the witness/reconstruction queue (a secondary
  cross-check signal, used on a specific, still-open ~411-item review
  queue for klal 30/75/88 — see `PROJECT-STATUS.md`).
- **`apply_event`** — a record that a specific decision (named in
  `applied_decision_id`) was promoted into `part1.json`. Written by
  `apply_reviewer_decisions.py`, never by the dashboard directly. This is
  what lets `apply_reviewer_decisions.py` know not to re-apply a decision
  it already promoted, and what `audit_applied_decisions.py` checks
  against the actual corpus to catch that assumption going stale.

Recording a decision and applying it to `part1.json` are always two
separate, deliberate steps — a `candidate_choice`/`manual_correction`/
`punctuation_choice` decision sits recorded and inert until
`apply_reviewer_decisions.py` (or `tools/apply_punctuation_decisions.py`)
is run by hand.

---

## `reconstruction_witness_queue.json`

**The second-opinion queue.** Everywhere else in this pipeline the comparison
is DocAI vs. the stored corpus text. This file holds the one place a genuinely
*different* OCR engine is used as a witness: Tesseract, run over the three
page-crossing klalim whose text had to be reconstructed across a leaf boundary
(klal 30, 75, 88). `review_server.py` loads it and folds undecided items into
the same machine-disputed count as ordinary corrections.

```json
{
  "klal_id": 30,
  "page": 24,
  "docai_reading": "דמנחות",
  "tesseract_reading": "י ו דמנחורז",
  "opcode": "replace",
  "tier": "D",
  "bbox": { "x1": 0.825, "y1": 0.088, "x2": 0.892, "y2": 0.105 },
  "docai_token_index": 4,
  "vision_selected": "A",
  "vision_transcription": "דמנחות ד'",
  "vision_confidence": 0.98,
  "vision_reasoning": "The first line clearly reads ...",
  "word_index": 120
}
```

| Field | Meaning |
|---|---|
| `klal_id`, `page` | Which klal this disagreement sits in, and the scan page it was cropped from. |
| `docai_reading` / `tesseract_reading` | The two engines' readings — reading A and reading B respectively in the vision prompt. |
| `opcode` | `replace` / `insert` / `delete`, same vocabulary as the corrections chain. |
| `tier` | Severity bucket assigned at queue-build time (`A`–`D`; A is the most serious). Current distribution: D 279, C 96, B 36, A 8. |
| `bbox` | Normalized 0–1 box, same convention as `docai_word_boxes/page_N.json`. |
| `docai_token_index` | The **key** a `witness_choice` decision is recorded against — *not* `word_index`. |
| `word_index` | Position in the klal's `clean_text`, for highlighting in the text pane. |
| `vision_*` | The machine pass's verdict, transcription, confidence and reasoning — already run over the whole queue. |

The file's `meta` block carries per-klal stats (`docai_words`,
`tesseract_words`, `agreement`, `flagged`, and counts of items skipped as
oversize spans or page furniture) plus the `by_tier` histogram and total.
Live figures: **419 items** across klal 30 (160), 75 (119) and 88 (140),
covering 2,673 DocAI words at 0.76–0.86 engine agreement. 8 have a human
`witness_choice`; **411 are open** — see `PROJECT-STATUS.md` open item 3.

## `lexicon.txt`

One validated Rabbinic Hebrew word per line, **19,015 lines** currently. Used
as the spell-check dictionary for the lexicon-gap sweeps and as the
`lexicon_hit_rate` signal in `part1_header_anchored_alignment.json`. Built and
audited by `tools/validate_lexicon_independent.py` and
`tools/review_lexicon_gaps.py`. Per the conventions in `START_HERE.md`, a
cleanup pass isn't done until lexicon validation flags zero items.

## The sqlite decision caches

Four `.db` files at root, all gitignored-or-migrated rather than rebuilt, all
serving the same purpose: don't re-spend an API call on a question already
answered.

| File | Caches |
|---|---|
| `adjudication_cache.db` | `verify_corrections_vision.py`'s per-token vision verdicts (`corrections_cache` table) |
| `witness_vision_cache.db` | the vision pass over `reconstruction_witness_queue.json` |
| `punctuation_cache.db` | `tools/propose_punctuation_part1.py`'s proposals |
| `gematria_trace_vision_cache.db` | vision checks during marker-position tracing |

**The cache-key rule applies to all of them** (`START_HERE.md` Lesson 12): the
key must include *which two readings were being compared* — `crop_hash +
word_a + word_b` — not the crop image alone. The same bbox gets re-cropped
across sessions to answer *different* questions as the stored text changes, and
a crop-only key silently returns a stale verdict for the current question.
`verify_corrections_vision.py`'s `corrections_cache` is the reference
implementation; key any new vision cache the same way.
