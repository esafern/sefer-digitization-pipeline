# How the pipeline works — method, state and costs

Companion to [`CASE-YAD-MALACHI.md`](CASE-YAD-MALACHI.md), which makes the case
for digitizing the work. This file holds the operational detail that case doesn't
need: how the method works, what has been measured, what is built and what isn't,
and what it costs.

For the day-to-day engineering state, see `PROJECT-STATUS.md`. For the evidence
trail behind any figure here, see `PROJECT-STATUS-HISTORY.md`.

## The method — many witnesses, one human decision

Accuracy on dense rabbinic Hebrew does not come from proofreading a single OCR
pass. It comes from putting several *independent* readers in front of the same
ink, surfacing every place they disagree, and resolving each disagreement
**against the scan** — not against a model's confidence score.

1. **Extract.** Google Cloud Document AI produces full-page words with
   high-precision bounding boxes over the Berlin square-type images. Every
   downstream crop depends on those coordinates.
2. **Add witnesses that fail differently.** A multimodal VLM (Gemini 3.6 Flash)
   reads whole pages; Surya, a locally-run open OCR engine, reads them again at
   300 DPI. Each is measured against the corpus, not assumed: **VLM 93.3% token
   accuracy** over all 222 reviewed klalim, **Surya 89.9%** mean agreement,
   **Tesseract 3.8%** — which is why Tesseract is retained as a historical
   witness and not as a leg of the pipeline.
3. **Diff, don't trust.** Each witness's reading is aligned against the stored
   text word by word. Agreement is the null result; every disagreement becomes a
   candidate with a real bounding box.
4. **Adjudicate against the ink — selection-only.** Each disputed token's box is
   cropped from the scan and put to a vision model **with the candidate
   readings**, which must *select* one and say why. It is never asked to generate
   a reading; anything unattested comes back as a flagged conjecture, not a
   silent change.
5. **Repair known printer's defects before counting agreement.** This printing
   sets *aleph-lamed* as one ligature sort (`ﭏ`) that OCR has no mapping for and
   reads as a bare *aleph*, silently dropping the *lamed*. A dedicated filter
   restores it, arbitrated by an independent 6.18-million-word reference corpus,
   never by this project's own lexicon.
6. **A human rules on every change.** Decisions are recorded in an append-only
   ledger and promoted into the corpus by a separate, deliberate step. No batch
   run can overwrite a human judgment.
7. **Structure and ingest** — klalim → one segment per klal, plus a confidence
   map. `tools/export_corpus.py --format sefaria` writes the ingest pair.

## What we measured that the field assumes

The standard argument for ensemble OCR is that independent engines make
uncorrelated errors, so agreement is near-proof. **We tested that on this corpus
and it is false**, and the finding is worth more than the pipeline that produced
it:

- **P(the consensus reading is correct | two distinct engines agree) is ~26–41%** —
  measured, not modelled. A published-style estimate for the same configuration
  put the odds of correlated error at 3.5 × 10⁻⁷. Consensus is a **triage
  signal**, not a decision procedure, and auto-approval on consensus is
  indefensible at any threshold this data supports.
- **Architectural independence is defeated by a defect in the shared input.**
  Three different engines read the same worn sort and make the same wrong call:
  37 measured cases of two or three engines agreeing on an identical error,
  including unanimous 3-of-3, all from that one alef-lamed ligature. Every engine
  is reading the same ink.
- **Tightening the rule doesn't rescue it.** Requiring the primary engine, or
  unanimity, buys three points of precision for 82% of the recall — measured,
  then rejected.

So the pipeline uses agreement to decide **where to look first**, and the ink to
decide **what is true**. That is the opposite of what a confidence threshold does.

## What the printing itself does

Two findings that any digitization of this edition will meet:

- **The compositor substitutes sorts.** Four words on page 40 alone are set with
  a *kaf* where the sentence requires a *bet* — `וכלבד` for `ובלבד`, and three
  more — with a correct bet two letters away in the same word for comparison, at
  900 DPI. The same thing happens with *chet* and *heh*, in both directions: 7
  words printed with ח where ה belongs, 5 the reverse.
- **An OCR engine reading those words is not wrong.** Any pipeline that scores
  its engines against a corrected text books them as recognition failures and
  learns the wrong lesson. Deciding what belongs in a digital edition — the ink
  as set, or the word as meant — is an editorial judgement for a person.

Worked examples, with the crops: [`VERIFIED-AGAINST-THE-INK.html`](VERIFIED-AGAINST-THE-INK.html).

## Current state

_Re-measured from the live corpus, 2026-08-25._

| | |
|:---|:---|
| **Klalei HaGemara** | 595 of 667 klalim carry real text (~188,000 words), scan pages 14–247 |
| 72 klalim | still hold a generated placeholder, all in klalim 223–667 |
| **Klalim 1–222** | full verification pipeline: 222/222 trusted page alignment, four witnesses, vision adjudication, live review dashboard |
| Klalim 223–667 | text and page-level alignment; no witness set has been run there |
| **Klalei HaPoskim** (pages 254–291) · **Klalei HaDinim** (292–329) | scanned, never extracted |

**The reviewed third in detail.** 1,061 flagged word positions across 185
klalim — 538 pipeline candidates plus 364 multi-witness consensus disputes, 72 of
them at the same position. A third are machine-resolved (118 of those are the
catalogued ligature artifact); the rest wait for a human.

**Guardrails.** Every correction is recorded in an append-only ledger
(`review_decisions.jsonl`) kept outside the automated rebuild, so no batch run
can overwrite a human judgment. 318 regression tests, 282 of them gating every
pipeline rebuild.

**Deliberately not done.** No `part2.json`/`part3.json` correction is applied
without its own go-ahead: a clean first third is not evidence the rest comes out
clean by the same process.

## Cost and effort

The upfront investment is in the **reusable harness**; subsequent public-domain
texts inherit it.

- **Harness and pipeline engineering** (DocAI ingestion, alignment, multi-witness
  synthesis, VLM adjudication, review UI, export tooling): ~80–120 dev hours,
  done.
- **Compute and API** (Document AI OCR + Gemini vision adjudication): low
  hundreds of dollars for the full corpus. Surya is local and free.
- **Expert Talmid Chacham review**: the live queue is ~970 open items across
  klalim 1–222, at roughly 1–3 minutes each with the crop, the candidates and the
  model's reasoning already on screen — call it **~30–50 focused hours** for that
  third, and a comparable pass per remaining third once its witness set is built.
  That is an estimate from the queue's size, not a measured throughput. The
  honest comparison is against the 200–300+ hours of transcribing or proofreading
  raw scans from scratch.

## Preparing the text for Sefaria

The last mile keeps two things separate — **the text** and **the links**:

- **Text.** OCR the Berlin edition images (cleanest square type). Licensing is
  clean: a public-domain edition, and mechanical OCR of PD text carries no new
  copyright. **Keep the prose faithful** — don't expand abbreviations (that's a
  read-time layer); do proof against the image, strip running headers and page
  numbers, and segment into the schema (*Yad Malachi, Klalei HaGemara, Klal N*).
  The schema this project emits declares exactly one node, `Klalei HaGemara`,
  which is what the corpus actually is.
- **Links.** Don't hand-insert them — Sefaria's Auto-Linker builds them from
  parseable citations. Design the schema's addressing to match how the 287
  sources cite it, or the inbound links won't auto-resolve.
- **Link-readiness QA.** Before ingest, run the text through the linker as a
  *test*: it flags each unresolved citation and pairs it with a candidate
  normalization for the reviewer.
