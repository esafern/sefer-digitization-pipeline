# Competitive landscape — Hebrew digitization, OCR, and correction platforms

Where this pipeline sits among the academic, open-source, and commercial
projects working on Hebrew/Rabbinic text digitization: what they do, what we
should borrow, and what here is genuinely not available elsewhere.

## TL;DR

**The field is barbelled.** At one end, well-funded institutional pipelines
(MiDRASH/EPHE, Friedberg Genizah, NLI) built to push *thousands* of damaged
medieval manuscripts through eScriptorium + Kraken + Passim at scale. At the
other, single-purpose OCR endpoints (Dicta, Transkribus) that hand you text
and stop. **Almost nobody is working the middle**: getting *one* important
printed work to publishable accuracy, cheaply, with a real audit trail.

**Our niche is the disagreement, not the OCR.** We don't compete on
recognition — Document AI does that. The pipeline is built around what happens
*after*: word-level bounding boxes, an explicit diff against the stored text,
image-grounded VLM adjudication of each disputed token, tri-state human review,
and an append-only decision ledger.

**Four things here that no surveyed platform has:**

1. **VLM adjudication of disputed tokens** — crop the disputed bbox out of the
   scan and ask a vision model to *select* between the candidate readings.
   Everyone else either retrains an HTR model (expensive) or leans on
   character-level language-model probability (blind to the ink).
2. **A measured, not assumed, ensemble posterior.** Every multi-engine pipeline
   in this space rests on the premise that independent engines fail
   independently. We measured it on this corpus: **P(consensus correct | two
   distinct engines agree) is ~26–41%**, and 37 measured cases have two or three
   engines making the *identical* error — because a worn printer's sort is
   upstream of every reader. Agreement here decides where to look, never what is
   true. See [§5](#5-where-this-pipeline-is-genuinely-ahead).
3. **Tri-state review with per-word provenance** — open / machine-resolved /
   human-decided, per word, with the decision history queryable.
4. **An append-only decision ledger kept outside the build pipeline** — no
   rebuild can clobber a human judgment, and the whole corpus is reproducible
   from the ledger plus the source.

**What we should take from them.** Dicta's DictaBERT/DictaLM for nikud and
abbreviation expansion if we ever need those. Passim + Freymat's scripts if we
digitize a work with heavy parallels already in Sefaria. Kraken/eScriptorium if
we ever need manuscripts.

**What we still lack.** HTR for handwritten manuscripts (we are printed-only);
multi-reviewer/crowdsourcing; community model sharing. **Standardized archival
export is no longer a gap** — `tools/export_corpus.py` writes ALTO XML v4, PAGE
XML 2019, and TEI P5.

**Best contact if we want a collaborator:** Prof. Avi Shmidman (Bar-Ilan
University / DICTA) — the natural bridge between DICTA's NLP work and academic
DH, and the person most likely to be interested in the VLM adjudication idea.
Verify current contact details before writing; see the [contacts](#contacts)
caveat.

---

## 1. The landscape

Hebrew text digitization was historically split between commercial text
databases (Bar-Ilan Responsa, Otzar HaChochma) and open-source
translation/liturgical projects (Sefaria, OpenSiddur).

A €10M European Research Council initiative — the **MiDRASH Project** — has
since catalyzed a modern, open-source, AI-driven ecosystem, with models and
pipelines shared across the National Library of Israel (NLI), École Pratique
des Hautes Études (EPHE), and Dicta. Most current activity in the field either
belongs to that ecosystem or interoperates with it.

## 2. The projects

### Dicta — Israel Center for Text Analysis

The dominant technical powerhouse for Hebrew NLP.

- **Sites:** [dicta.org.il](https://dicta.org.il/) ·
  [ocr.dicta.org.il](https://ocr.dicta.org.il/) (the web portal appears to be "הגהת מסמכים סרוקים", a Dropbox-synced proofreader requiring .docx/.txt; research confirms Dicta provides Hebrew OCR across its platform, but the exact mechanism for direct public web upload of raw PDFs remains unconfirmed) ·
  [library.dicta.org.il](https://library.dicta.org.il/) (digital library)
- **Code:**
  [github.com/Dicta-Israel-Center-for-Text-Analysis](https://github.com/Dicta-Israel-Center-for-Text-Analysis)
  · [huggingface.co/dicta-il](https://huggingface.co/dicta-il) (models)
- **People:** Prof. Moshe Koppel (founder) · Prof. Avi Shmidman (chief NLP
  researcher, Bar-Ilan University) · Shaltiel Shmidman (lead NLP developer)
- **Stack:** PyTorch, HuggingFace transformers (DictaBERT, DictaLM 3.0 with
  tool-calling), custom nikud models.
- **Strengths:** highly accurate institutional OCR for both square and Rashi script,
  multi-column layout detection, diacritics. Its digital library carries
  diacriticized transcripts of 300+ classic Rabbinic texts.
- **Gap vs. us:** public web-upload / batch API workflow for end-users not yet confirmed,
  no bounding-box data out, no tri-state review UI, no audit log.

### Sefaria / eScriptorium / Passim (the "Freymat" pipeline)

Sefaria's digitization strategy now bridges eScriptorium (OCR/segmentation) and
Passim (text alignment), largely written by the researcher Freymat under
MiDRASH.

- **Code:**
  [from_eScriptorium_to_Passim_and_back](https://github.com/Freymat/from_eScriptorium_to_Passim_and_back)
  · [from_Sefaria_to_Passim](https://github.com/Freymat/from_Sefaria_to_Passim)
  · [Sefaria/Sefaria-Project](https://github.com/Sefaria/Sefaria-Project)
- **People:** Freymat (lead pipeline developer, EPHE/MiDRASH) · Lev Israel
  (CTO, Sefaria) · Dr. Luigi Bambaci (HTR researcher, EPHE)
- **Stack:** Python, eScriptorium REST API, Scala-based Passim on Apache Spark,
  Sefaria REST API, ALTO/PAGE XML.
- **How it works:** manuscript scans → rough OCR in eScriptorium/Kraken →
  Passim aligns that rough text against known ground truth pulled from Sefaria
  → high-confidence alignments (Levenshtein-validated) are written back into
  eScriptorium as training data, eliminating manual transcription for HTR
  training.
- **Gap vs. us:** the clever part is bootstrapping training data from texts
  Sefaria *already has*. That is exactly the case we don't have — Yad Malachi's
  whole problem is that no digital text exists to align against. Also
  line-level, no per-word disagreement detection, no image-grounded
  adjudication.

### Transkribus — READ-COOP

A large European platform specializing in handwritten text recognition and
layout analysis.

- **Sites:** [transkribus.org](https://transkribus.org/) ·
  [app.transkribus.org/models](https://app.transkribus.org/models) (public
  model hub)
- **People:** Dr. Günter Mühlberger (chair, READ-COOP / University of
  Innsbruck)
- **Stack:** PyLaia HTR engine, Java client, proprietary baseline-detection
  networks.
- **Strengths:** specialized public models for historical Hebrew and Yiddish —
  DiJeSt 3.0/2.0 (Hebrew/Judeo-Arabic), IGRA Sfardi (Sephardic semi-cursive),
  The Dybbuk (Yiddish handwriting) — reportedly reaching 1.5–4.5% character
  error rate on clean historical scripts, with native RTL support.
- **Gap vs. us:** line-level correction, no disagreement detection, SaaS with
  paid tiers. RTL support is solid for the model hub's Hebrew models but
  partial/improving elsewhere in the platform.

### Friedberg Genizah Project / MiDRASH

A multi-institution effort to digitize and transcribe the Cairo Genizah.

- **Sites:** [midrash.eu](https://midrash.eu/) ·
  [genizah.dicta.org.il](https://genizah.dicta.org.il/) · datasets on
  [Zenodo](https://zenodo.org/records/14230445)
- **People:** Prof. Daniel Stökl Ben Ezra (PI, HTR lead, EPHE) · Prof. Judith
  Olszowy-Schlanger (lead paleographer, Oxford/EPHE) · Prof. Nachum Dershowitz
  (computer science, Tel Aviv University) · Prof. Avi Shmidman (NLP architect,
  Bar-Ilan/Dicta)
- **Stack:** eScriptorium, Kraken, ALTO XML, JSON datasets.
- **Strengths:** automated recognition of highly mutilated fragments;
  paleographic clustering to determine "joins" between fragments held in
  different libraries; transcriptions published as open data.
- **Gap vs. us:** a different problem entirely — manuscripts at scale, not one
  printed work to publishable accuracy.

### OpenSiddur

Community-driven digitization of Jewish liturgical and ritual texts.

- **Site:** [opensiddur.org](https://opensiddur.org/) · **Code:**
  [github.com/opensiddur/opensiddur](https://github.com/opensiddur/opensiddur)
- **People:** Efraim Feinstein (lead developer) · Aharon Varady (director)
- **Stack:** PHP/WordPress core, Java XML tooling, Tesseract with custom Hebrew
  files.
- **Strengths:** deep TEI XML structuring of liturgy; collaborative
  transcription.
- **Gap vs. us:** relies on volunteer proofreaders correcting raw
  Tesseract/EasyOCR output — manual diffing and crowd-sourced alerts, no
  machine adjudication.

### The rest, briefly

| Project | What it is | Gap vs. this pipeline |
|---|---|---|
| **NLI (Ktiv / JPress)** | The world's largest Hebrew digitization program; line-level crowdsourced newspaper correction | No public correction API, no word-level bbox output, corrections handled internally |
| **Bar-Ilan Responsa** | 100M+ word halakhic corpus, hand-keyed over decades | No modern OCR pipeline at all |
| **Sefaria (the library itself)** | Open digital library with linked texts and community correction | No OCR, no image-level tooling — a text repository |
| **FromThePage** | Crowdsourced transcription SaaS for libraries/archives | No OCR, no native RTL support |
| **PRImA Aletheia** | Desktop Java bbox-level ground-truth editor (PAGE XML) | Not web-based, not Hebrew-specific, no machine correction |

### Candidate OCR & Second-Witness Engines (Evaluated vs. Untried)

To ensure high corpus fidelity, an independent second/third witness engine is needed to corroborate readings. Below is the status of all evaluated and potential witness engines — updated 2026-08-21 with real local test results, not just documentation review (see `PROPOSED_PIPELINE_ARCHITECTURE.md` section 5 and `tools/second_witness_eval/README.md` for full evidence):

| Engine | Type | Strengths | Limitations | Status in this Pipeline |
|---|---|---|---|---|
| **Google Document AI** | Specialized Cloud OCR | Character & word-level geometric bounding boxes, high square-print baseline accuracy | Cloud dependency, closed-source, weaker on dense Rashi script; **confirmed 2026-08-21 to silently fail to tokenize some klal markers at all** (root cause of a corpus-wide region-overlap bug, 316 klalim) | **Current Primary Baseline** (`docai_word_boxes/`) |
| **Multimodal VLMs (Gemini 3.6 Flash)** | Foundation Multimodal AI | Deep Rabbinic semantic understanding, directly reads high-res raster pixels, robust to ligatures and archaic layout | No native word coordinate bboxes; requires prompt engineering; cost per page; **same model family as the Adjudicator — a real, documented circularity gap (Directive #1)** | **Full-page end-to-end witness run 2026-08-21** — 93.34% token accuracy vs. `part1.json` across all 222 Part-1 klalim, 87.43% Pass-A/Pass-B self-consistency; also used for crop adjudication (`verify_corrections_vision.py`) |
| **TrOCR Hebrew (`sivan22/trocr-hebrew`, `cyttic/exp17-trocr-hebrew-synth1m`)** | Line-level Vision Transformer (HuggingFace) | Open weights, runs locally via PyTorch, line-level attention trained on printed Hebrew | **Confirmed blocked, not just unbenchmarked**: the model's own custom tokenizer/vocab was never uploaded to its HuggingFace repo, so decoding with any substitute tokenizer scrambles output (root-caused 2026-08-20) — needs the original tokenizer files or retraining, neither available | Root cause diagnosed; **not fixable without upstream data this project doesn't have** |
| **Kraken (eScriptorium / MiDRASH / NLI models)** | Open HTR/OCR Engine | Industry standard for historical Hebrew manuscripts and early Rabbinic print; open models available | Requires a typeface/period-matched model; the one tested (`Ashkenazi_01`, medieval handwriting) makes letter-level errors on this printing's square type | **Installed and run 2026-08-21 on arm64** — real, readable Hebrew output with letter errors; a print-matched model still needed. The `torch>=2.4` vs. macOS **x86_64** wheel ceiling that blocks it elsewhere is architecture-specific, not a property of Kraken |
| **EasyOCR (JaidedAI)** | Open Deep-Learning OCR | Lightweight Python library | **No Hebrew support at all** — confirmed 2026-08-21 by direct inspection of `easyocr.config.all_lang_list` (`'he'` absent), not by assumption | **Ruled out** — not a candidate for this project |
| **PaddleOCR** | Open Deep-Learning OCR | Wide language coverage, actively maintained | **No Hebrew support** — confirmed 2026-08-21 against Paddle's own published language list | **Ruled out** — not a candidate for this project |
| **PyLaia** | Deep HTR engine (PyTorch) | High accuracy on historical lines with sufficient training data | Requires line segmentation and custom model training | **Not yet tried in this pipeline** |
| **Surya OCR (`datalab-to/surya`)** | Open multilingual OCR/layout (separate company — not Google, not Anthropic) | Runs 100% locally, zero marginal cost, genuine RTL/Hebrew support; the only witness here with no cloud dependency and no per-page cost | Layout-block assignment to klalim is the weak seam, not recognition (4 klalim still carry a neighbour's text); resolution-sensitive | **Promoted from spot-test to a full pipeline witness.** All 63 pages re-rendered at 300 DPI 2026-08-24: mean agreement vs. the corpus **71.7% → 89.9%**, median 91.8%, **190 of 222 klalim improved**, coverage now **222/222**. It had been reading a quarter of the available pixels for the life of the witness stream. Contributes to 297 of the 364 live consensus disputes. |
| **Claude vision (Anthropic, via the coding session's own image-reading capability)** | Foundation Multimodal AI | Genuinely different model family from Google (both DocAI and the Gemini-based witness/adjudicator); zero integration cost as an interactive check | Not batch-callable by a standalone script without a provisioned `ANTHROPIC_API_KEY` (none present in this environment) | **Used successfully, live, 2026-08-21** — directly reading a disputed scan crop correctly identified a real DocAI letter-misread (ט read as פ) that Gemini-based tooling had missed |
| **Azure AI Document Intelligence** | Commercial Cloud OCR (Microsoft) | Confirmed Hebrew support in its Read model; the only candidate here that could replace/complement DocAI itself, not just the witness/adjudicator layer | Needs a new Azure account/API key, not present in this environment; unverified in practice | **Feasibility-checked 2026-08-21, not tested** |
| **AWS Textract** | Commercial Cloud OCR (Amazon) | — | Not researched in depth | **Unresearched as of 2026-08-21** |
| **Dicta OCR Engine** | Proprietary Deep Learning | Best-in-class Rabbinic Hebrew & Rashi recognition | The `ocr.dicta.org.il` URL appears to be a Dropbox-synced proofreader; research confirms Dicta provides Hebrew OCR across its tools, but the exact mechanism for direct public web upload of raw PDFs remains unconfirmed | **Assessed 2026-08-20**: Web upload workflow unconfirmed; under active research |


## 3. Feature comparison

| | Dicta | Sefaria / Freymat | Transkribus | OpenSiddur | FGP / MiDRASH | **This pipeline** |
|---|---|---|---|---|---|---|
| **Primary focus** | General Hebrew NLP; automated Rabbinic libraries | Scale manuscript→library ingestion | General historical HTR | Collaborative liturgy transcription | Ancient manuscripts + paleography | **Surgical, single-work printed Rabbinic digitization** |
| **OCR engine** | Custom Dicta deep-learning models | eScriptorium / Kraken | PyLaia | Tesseract, EasyOCR | eScriptorium / Kraken | Google Document AI (square-print processor) |
| **Disagreement detection** | Deep-learning spellcheck / LM probability | Large-scale text-reuse alignment via Passim | Baseline verification + confidence thresholds | Manual volunteer diffing | Algorithmic "join" alignment across witnesses | **Word-level diff of fresh OCR vs. stored corpus text** (`build_corrections_dataset.py`), plus **multi-witness synthesis** across DocAI, a VLM sampled twice, and Surya (`synthesize_multi_witness.py`) |
| **Known-defect repair before voting** | — | — | — | — | — | **Yes** (`pipeline/repair_filters/`): the printing's alef-lamed ligature is catalogued and restored, arbitrated by an *independent* 6.18M-word corpus — 24% of the review queue was this one artifact |
| **VLM adjudication** | No — text-only LM probability | No — character-level alignment | No — HTR line confidence | No | No | **Yes** (`verify_corrections_vision.py`): crops the disputed bbox, asks Gemini to select between readings |
| **Section/structure tracking** | Simple structural tags | Passim alignment to known chapters | Custom XML baseline anchoring | TEI XML structural mapping | Paleographic layout clustering | **Yes** (`build_gematria_trace.py`): Hebrew-numeral section markers located and verified against physical pages |
| **Human review UI** | Built-in web proofreader | eScriptorium web transcription | Rich Java/web line-correction client | Wiki-style online editors | eScriptorium + NLI transcribe-a-thons | **Yes** (`review_server.py`): local Flask server with live, coordinate-mapped scan crops |
| **Audit / integrity** | Private DB transaction logs | Version control via Sefaria-Data | Server-side revision tracking | Standard git commits | GitLab / eScriptorium versioning | **Yes** (`review_decisions.jsonl`): append-only ledger, deliberately outside the build pipeline, gated by pytest |
| **Archival export** | — | ALTO/PAGE XML | PAGE XML | TEI XML | ALTO XML, Zenodo JSON | **Yes** (`tools/export_corpus.py`): plain, ALTO v4, PAGE 2019, TEI P5 |
| **Openness** | Mixed — public HF models, some private APIs | Fully open on GitHub | Open engine, SaaS with paid tiers | Fully open | Fully open + open Zenodo datasets | Fully open, locally executable, no external server dependency |

## 4. Where to borrow

1. **Nikud and abbreviation expansion — DictaBERT / DictaLM.** If this pipeline
   ever needs to output vocalized text, or to expand abbreviations as a
   read-time layer, Dicta's HuggingFace models are the obvious path rather than
   building it. (`CASE-YAD-MALACHI.md` already treats abbreviation expansion as
   a Dicta layer, not something to bake into the prose.)
2. **Passim for parallel passages.** If a future work has extensive parallels
   already in Sefaria's library, Passim and Freymat's `from_Sefaria_to_Passim`
   can pre-correct against them. Not applicable to Yad Malachi, whose whole
   premise is that no digital text exists.
3. **Kraken / eScriptorium for manuscripts.** If the scope ever moves off
   printed editions, this is the mature path — and a trained Kraken model is
   already the recommended collation witness for the Rashi-script Livorno first
   edition.

## 5. Where this pipeline is genuinely ahead

1. **It measured the assumption the whole field runs on, and found it false.**
   Ensemble OCR is justified by the premise that different engines fail
   independently, so agreement approximates proof. On this corpus that premise
   does not hold: **P(consensus correct | two distinct engines agree) is ~26–41%**,
   and tightening the rule (require the primary engine; require unanimity) buys
   three points of precision for 82% of the recall. The mechanism is not model
   quality but the shared input — **37 measured cases of two or three engines
   producing the *identical* wrong reading**, all traceable to one worn ligature
   sort that every reader sees the same way. A published-style independence
   estimate for the same configuration prices that at 3.5 × 10⁻⁷. The practical
   consequence is architectural: consensus routes attention, the ink decides,
   and a human signs. Any pipeline here that auto-approves on agreement is
   trusting a number nobody in this space appears to have measured.
2. **Multimodal VLM adjudication.** No surveyed platform crops disputed OCR
   zones and queries a vision model to vote on the reading. The alternatives
   are retraining an HTR model on 50+ pages of new ground truth, or trusting a
   character-level language model that never looks at the ink. For a targeted
   print digitization, VLM adjudication is cheaper, immediate, and grounded in
   the image. **The safeguard matters as much as the technique**: the model is
   asked to *select* among candidate readings, never to generate — anything
   unattested comes back as a flagged conjecture, not a silent change.
3. **Structure-aware section anchoring.** Mapping logical Hebrew numerals (klal
   א, ב, ג …) to physical page positions and verifying them is specialized
   work. Large-scale pipelines produce PAGE-XML layout lines; they don't build
   a high-level logical index keyed on Hebrew numeral structure.
4. **Local human-in-the-loop ledgering.** The append-only
   `review_decisions.jsonl`, committed alongside the code and kept out of the
   rebuild path, makes the corpus 100% reproducible (`rebuild_all.sh`) and
   continuously verified (pytest). Nothing else surveyed treats a human
   judgment as a first-class, protected, replayable record.

## 6. Where this pipeline is behind

- **HTR for manuscripts** — printed-only. Kraken/eScriptorium own this.
- **Crowdsourcing / multi-reviewer** — the review server is single-reviewer.
  Every platform built for institutional scale has multi-user workflows.
- **Community model sharing** — Transkribus's model hub and Kraken/Zenodo have
  ecosystems; we have none, because we train nothing.

## Contacts

**Treat every address and handle below as needing verification before use.**
These were gathered from two research passes that disagreed with each other on
affiliation and email for the same person; the affiliations here reflect the
better-supported reading, but the contact details themselves were not
independently confirmed.

- **Prof. Avi Shmidman** — Bar-Ilan University and DICTA. The most natural
  collaborator: the bridge between DICTA's NLP work and academic DH, and the
  person most likely to engage with the VLM-adjudication approach. Dicta could
  also plausibly serve as a third OCR engine in the ensemble. (One research
  pass placed him at Ben-Gurion University with a `@bgu.ac.il` address; the
  Bar-Ilan affiliation is the better-supported one. Confirm the current address
  from Dicta's or Bar-Ilan's own site rather than either figure quoted here.)
- **Freymat** — [github.com/Freymat](https://github.com/Freymat). Author of the
  Sefaria/Passim alignment scripts; the person working closest to the
  OCR↔Sefaria↔HTR seam.
- **Benjamin Kiessling** — [github.com/mittagessen](https://github.com/mittagessen),
  Kraken's author. Relevant if manuscripts or engine comparison ever enter
  scope.
- **Prof. Daniel Stökl Ben Ezra** — EPHE. Co-designed eScriptorium's Hebrew/RTL
  support; the right contact for academic collaboration or publishing the
  pipeline.
- **Sefaria engineering** — [github.com/Sefaria](https://github.com/Sefaria),
  under CTO Lev Israel; general ingest coordination goes to
  **hello@sefaria.org**. They are actively looking for pipelines that help
  ingest public-domain texts they currently lack — which is precisely Yad
  Malachi's position.

## Bottom line

The academic world is building multi-million-euro infrastructure to transcribe
thousands of damaged medieval fragments. This pipeline does something different
and smaller: take one classic printed work — *Klalei HaGemara*, 667 klalim — and
get it to publishable accuracy with a defensible audit trail, run locally by one
person. Document AI supplies the baseline OCR; Surya and a VLM supply witnesses
that fail differently; crop-level adjudication, a catalogued repair filter for
the printing's own defects, the tri-state review model and the protected decision
ledger supply the accuracy and the provenance. That combination is not currently
available anywhere else, and it fits exactly the class of work Sefaria is
missing — with one finding worth handing to the field whether or not anyone
adopts the pipeline: **on real historical print, engine agreement is worth far
less than everyone assumes, and it is cheap to measure.**

---

_Merged 2026-08-19 from two separate research passes — `competition.md` and
`more competition.md`, both removed in the same commit, neither ever tracked in
git — whose contradictions are resolved above. Corrections
made to both sources in the process: the disagreement-detection leg is DocAI
vs. the stored corpus text (DocAI vs. Tesseract is the separate witness pass on
page-crossing klalim, not the main comparison), and standardized ALTO/PAGE/TEI
export is no longer missing._
