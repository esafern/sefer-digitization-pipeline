# Second-Witness OCR & HTR Evaluation — Berlin pages 18–20

Testing candidate second-witness engines (**Dicta OCR**, **Kraken HTR**, **Gemini 3.6 Flash VLM**) to determine the best replacement witness for this pipeline.

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
