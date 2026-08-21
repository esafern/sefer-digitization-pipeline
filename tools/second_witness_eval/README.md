# Second-Witness OCR & HTR Evaluation — Berlin pages 18–20

Testing candidate second-witness engines to determine the best replacement
witness for this pipeline (currently Tesseract, measured near-worthless —
see TL;DR below). Original scope (**Dicta OCR**, **Kraken HTR**, **Gemini
3.6 Flash VLM**); expanded 2026-08-21 with a broader engine/model sweep —
see "2026-08-21: broader candidate sweep" below for what was actually
installed and run, not just researched.

## TL;DR

**Why.** The current second-witness engine, Tesseract, is nearly worthless:
across 419 disagreements it was right **16 times (3.8%)** while DocAI was right
91.2%. It fails because it's a *weaker engine on the same scan* — it disagrees
by being wrong. Dicta is a genuinely different engine, trained on Hebrew, and
**reads Rashi script**, which is where DocAI is weakest.

**The test set is already adjudicated**, so this is a measurement, not an
impression. `yad-malachi-berlin-sample.pdf` (3 pages, 1.0 MB, full resolution,
git-tracked at repo root) = source PDF pages **18, 19, 20** = **klalim 8–22**.

| | |
|---|---:|
| Klalim | 15 (8–22) |
| Ground-truth words | 2,356 |
| Correction candidates | 23 |
| …still open | 11 |
| Human decisions on record | 9 |

**Ground truth** is `groundtruth_klal_8_22.txt` in this directory — the
`clean_text` from `part1.json`, one section per klal, headed by `klal_id`,
gematria marker and title so Dicta's output can be aligned section by section.

**The three questions**, in descending order of what they'd change:

1. Does Dicta **agree with the corpus on the 12 settled candidates**? Agreement
   from a genuinely independent engine is the corroboration Lesson 9 asks for
   and Tesseract never supplied.
2. Does it **break any of the 11 still-open ones**? The immediate practical
   payoff — a third reading on words nobody has ruled on.
3. Does it **find anything neither DocAI nor the corpus has**? Most
   interesting, least likely.

**If it wins on square type**, the real prize is the Rashi-script editions —
**two of which are confirmed in hand locally** (2026-08-19):

| Edition | Local file | Pages |
|---|---|---:|
| Livorno 1766–7 (*editio princeps*) | `~/Downloads/Hebrewbooks_org_32530/32531/32532.pdf` | 348/54/55 |
| Przemyśl 1877 | `~/Downloads/Hebrewbooks_org_14122.pdf` (19.5 MB) | 491 |

Nothing has successfully OCR'd either. HebrewBooks' own "fastocr" for #14122
was tested and **rejected — 44.0% lexicon hit vs. our corpus's 97.8%**, from a
square-model-reading-Rashi letter-confusion signature (ס 9.7× over-produced, א
0.17× under). See `PROJECT-STATUS-HISTORY.md`, 2026-08-19.

A Rashi edition read by a Rashi-capable engine is a second *edition* and a
second *engine* at once — the independent signal Tesseract never was.

## How the page mapping was established

Not inferred. The sample's three embedded page images were MD5-matched against
every image in `berlin_square_corrected.pdf`, giving source page indices 18,
19, 20. Klal attribution for those pages then agreed **exactly** across three
independent artifacts:

- `gematria_trace_part1.json` (marker position)
- `part1_header_anchored_alignment.json` (header-anchored alignment)
- `klal_page_regions.json` (per-klal scan regions)

All three name klalim 8–22, with the same page split (8–12 on p18, 13–16 on
p19, 17–22 on p20).

## Per-klal coverage

| klal | words | candidates | open | human decisions |
|---:|---:|---:|---:|---:|
| 8 | 239 | 1 | 0 | 0 |
| 9 | 23 | 0 | 0 | 0 |
| 10 | 131 | 2 | 1 | 1 |
| 11 | 104 | 1 | 0 | 1 |
| 12 | 333 | 3 | 0 | 2 |
| 13 | 293 | 3 | 1 | 1 |
| 14 | 253 | 0 | 0 | 0 |
| 15 | 27 | 1 | 1 | 2 |
| 16 | 163 | 2 | 1 | 1 |
| 17 | 316 | 2 | 1 | 1 |
| 18 | 78 | 2 | 2 | 0 |
| 19 | 217 | 2 | 2 | 0 |
| 20 | 41 | 2 | 2 | 0 |
| 21 | 70 | 0 | 0 | 0 |
| 22 | 68 | 2 | 1 | 0 |

## 2026-08-21: broader candidate sweep

Beyond Dicta/Kraken/VLM, actually installed and tested (not just
researched) a wider set of engines and models, prompted by this project's
own standing rule that a claim needs real evidence, not an assertion. Full
detail and reasoning in `PROJECT-STATUS.md`'s 2026-08-21 entries and
`PROPOSED_PIPELINE_ARCHITECTURE.md` section 5; summarized here:

**Kraken's "blocked" status was stale, not current.** The prior finding
(`kraken>=5.3` needs `torch>=2.4.0`, blocked on macOS x86_64) describes an
Intel Mac; this machine is arm64 (Apple Silicon), where `kraken 3.0.13` +
`torch 2.13.0` install and run without issue. Ran `tools/test_kraken_
local.py` successfully, then went further: downloaded a real pretrained
Hebrew model (`Ashkenazi_01.mlmodel`, medieval manuscripts,
Zenodo DOI 10.5281/zenodo.5468478 — kraken's own `get` command is broken
against Zenodo's current API, fetched the file directly instead) and ran
real recognition against `images/pdf_pages/page_18.png`. Output:
`'יר מלאכי כללו האלף'` (should be `'יד מלאכי כללי האלף'`) — recognizable
Hebrew with letter-level errors, expected since that model is trained on
handwriting, not this printing's square type. **Kraken itself is not the
blocker; a print-typeface-matched model is what's missing**, and none was
found this session.

**EasyOCR and PaddleOCR ruled out — no Hebrew support at all**, confirmed
by direct inspection (`easyocr.config.all_lang_list` doesn't contain `'he'`;
Paddle's own published language list lacks Hebrew entirely), not assumed
from documentation.

**Surya OCR (`datalab-to/surya`) — the strongest new finding.** A separate
company from Google/Anthropic, installed and runs 100% locally at zero
marginal cost. Full-page OCR on `page_18.png`:
- Running header `'יד מלאכי כללי האלף'` — **exact match** to ground truth
  (Kraken got this wrong).
- Klal 9 body text near-exact vs. this session's own independently-verified
  ground truth (minor noise only: `שכרתבו`/`שכתבו`, `ד"ה`/`דייה`).
- **Correctly recognized klal 10's marker "י" as its own bold span** — the
  exact marker DocAI's own extraction failed to tokenize at all, separately
  root-caused the same session as the cause of a corpus-wide region-overlap
  bug (`PROJECT-STATUS.md`, 316 klalim affected). Surya succeeded exactly
  where DocAI failed, on the same page, same marker.

One page is a spot-check, not a benchmark — **the concrete next step is a
proper multi-page Surya-vs-DocAI comparison**, reusing
`evaluate_ocr_alignment.py`'s existing method, before deciding how to wire
Surya in as a permanent `AbstractWitnessEngine` implementation.

**Claude vision — already used successfully, live, no new integration.**
The acting coding session's own image-reading capability (via its `Read`
tool, not a new API) directly rendered and read a disputed scan crop and
correctly identified a real DocAI letter-misread (klal 16's marker: ט read
as פ) that Gemini-based tooling had missed entirely. Zero setup cost as an
interactive check; not batch-callable by a standalone script unless
routed through the Anthropic API (`ANTHROPIC_API_KEY` — not currently
provisioned in this environment).

**Azure AI Document Intelligence** confirmed (via Microsoft's own docs) to
support Hebrew — the only candidate found so far that could address
circularity at the **primary OCR** level (replacing/complementing DocAI
itself), not just the witness/adjudicator level. Not tested — would need a
new account. **AWS Textract** and **GPT-4V** were not researched in depth
this round — open, not ruled out.

**Recommendation, ranked by (feasibility right now) × (real independence
gained)**: (1) a real multi-page Surya benchmark — already outperformed
DocAI on the one comparison run, zero cost to pursue further; (2) Claude
vision via the Anthropic API as a batch-callable witness/adjudicator
cross-check — already caught a real error the standing pipeline missed,
needs one new API key; (3) Azure AI Document Intelligence as an
alternative primary-OCR source — the only option that fixes circularity at
that level, needs a new account, unverified in practice.

## Status / next step

**Investigation status (2026-08-20):**
The web portal `ocr.dicta.org.il` appears to function primarily as an interactive proofreader ("הגהת מסמכים סרוקים") tied to a Dropbox integration for `.docx`/`.txt` files. Research confirms that Dicta provides powerful Hebrew OCR capabilities across its platform and digital library, but the exact mechanism for direct public web upload of raw image PDFs remains unconfirmed and under active investigation.

If Dicta output is obtained (via API, updated web interface, or direct collaboration), drop the raw text output in this directory and run the automated diff against `groundtruth_klal_8_22.txt`.


## Caveats

- **Unverified:** Dicta's per-file page/size limits, and whether a free account
  carries a quota. Three pages at 1 MB should be inside anything reasonable —
  which is the point of testing with the sample before committing 337 pages.
- The sample PDF was originally produced at **109 MB** for 3 pages (it carried
  the full 337-page original's resource tree). Re-saved with garbage collection
  to 1.0 MB with no re-compression — same PNG dimensions per page. If you
  regenerate it, use `garbage=4, deflate=True, clean=True` or you'll hit upload
  limits for no reason.
