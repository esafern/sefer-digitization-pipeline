# A case for digitizing Yad Malachi

_Scan, OCR, and structure one foundational public-domain work of Torah that is heavily
relied upon but has no public digital text._

## TL;DR

**The work.** *Yad Malachi* (Livorno 1766–7) is the standard reference on the *rules* of
halachic reasoning. Its first part, ***Klalei HaGemara***, is 667 numbered *klalim*
running alphabetically from `כללי האלף` to `כללי התיו`.

**The demand is measured, not asserted.** Sefaria's own corpus cites it **287 times**, and
every one is a dead link. Halachipedia cites it **243 times** — **26% of every
public-domain citation Sefaria lacks, in one work**, and roughly **twice** the next
public-domain title on record ([the table below](#the-free-to-digitize-tier-is-one-work)).

**It is the easiest big win available.** Public domain, cleanly numbered (klalim map
straight onto a Sefaria schema), and **already scanned** — four editions in five scans in
hand, one of them in clean square type, the kind general OCR reads best.

**The text is built.** All **667 klalim of Klalei HaGemara** — ~179,000 words, scan pages
14–247 — are extracted, chunked, and structured. Klalim **1–222** additionally carry the
full verification pipeline: 222/222 trusted page-to-klal alignment, four independent
witnesses read against the ink, and **1,061 flagged word positions** in a live review
dashboard. Klalim 223–667 have text and page alignment but no witness set yet.

**What isn't done, stated plainly.** The book's other two parts — *Klalei HaPoskim*
(pages 254–~295) and *Klalei HaDinim* (~296–331) — are scanned but **not extracted at
all**. And no correction anywhere in the corpus is promoted without a human ruling: the
machine flags, a person decides.

**What's needed.** (1) An outside Talmid Chacham independently confirming the reviewed
text is clean — this pipeline's own self-assessment is not the gate. (2) Working the open
queue. (3) Coordinating ingest with Sefaria.

**The payoff.** 287 dead references light up automatically, hand-re-keying from scans
ends, and the harness is reusable for every subsequent public-domain work.

## The work

**Yad Malachi** (יד מלאכי), by **R. Malachi ben Jacob HaKohen** of Livorno (1695–1772),
first printed Livorno 1766–7. A three-part masterwork of *methodology* — the *grammar* of
the tradition, reached for whenever a question of method arises:

1. **Klalei HaGemara** — the rules and technical terms of the Talmud, alphabetical.
   **667 klalim**, and the part this project has digitized end to end.
2. **Klalei HaPoskim** — the rules governing the codifiers: Rif, Rambam, Semag, Rosh,
   Rashba/Ritva, Tur, Shulchan Aruch. Its own numbering, restarting at 1.
3. **Klalei HaDinim** — the principles of halachic decision, alphabetical again, its own
   numbering.

Parts 2 and 3 are **not digitized** — see [Current state](#current-state). Their klal
counts are quoted variously in secondary sources (one common figure pairs 299 and 146 with
a "222" for Klalei HaGemara, which the printed book contradicts outright — the Berlin
edition closes Klalei HaGemara at klal **667** with the colophon `סליקו כללי התיו וסליקו
כללי הגמרא` on page 247). Nothing here relies on those counts.[^parts]

![Title page of the Berlin edition of Yad Malachi, naming the three parts Klalei HaGemara, Klalei HaPoskim, and Klalei HaDinim](images/yad-malachi-berlin-title.png)

_Berlin edition title page — the three parts and the author. Rendered directly from
`berlin_square_corrected.pdf`, page 6._

## Why it matters

Its standing is independent and measurable, not a matter of opinion.[^wiki]

**287 dead ends inside Sefaria.** The corpus cites יד מלאכי in **287 places**[^sefaria] —
each unfollowable, because the work isn't in the library. Who cites it, and what it shows:

| Mentions | Citing Work                                                                                   |
|---------:|:----------------------------------------------------------------------------------------------|
|      118 | Ayin Zokher (Chida)                                                                           |
|       17 | Petach Einayim (Chida)                                                                        |
|       13 | Shem HaGedolim (Chida)                                                                        |
|        8 | Rosh David (Chida)                                                                            |
|       11 | Pardes Yosef                                                                                  |
|        9 | Kaf HaChayim (d. 1939)                                                                        |
|        — | + Mishnah Berurah / Biur Halacha, Torah Temimah, Minchat Chinukh, Even Ha'azel, Benei Banim   |

- **The Chida relies on it constantly** — ~156 of the 287, across four of his works. The
  towering Sephardi authority of the era, the author's own contemporary, treats it as a
  standing reference.
- **And it doesn't stop with him** — ~130 more span the next two centuries (Pardes Yosef,
  Kaf HaChaim d. 1939, Mishnah Berurah / Biur Halacha, Torah Temimah, Minchat Chinukh,
  living responsa).

**Still in active use:**

- **Republished and studied** — new editions in 2001, a Machon Yerushalayim critical
  edition (2016), a third volume (2018)[^wiki]; and modern scholarship calls it *"one of
  the most important halakhic rule books."*[^brown]
- **243 citations in Halachipedia**[^halachipedia] — the **single most-cited public-domain
  work Sefaria lacks**[^mostwanted] (see the table below).
- **Live debate, and the pain point in the wild** — on one Torah forum, Yad Malachi appears
  in **~108 posts across ~71 discussions** (50 by a specific *klal*), and **6 are requests
  for a *scan* of a klal**, because no clean digital text exists.[^forum]
- **Central to R. Ovadia Yosef's school** — whose works are ~⅓ of every citation Sefaria
  lacks, and whose method is built on the *klalei ha-hora'ah* that Yad Malachi codifies.[^ovadia]

### The free-to-digitize tier is one work

A survey of Halachipedia's full 640-page corpus[^halachipedia] sorted every work Sefaria
*lacks* into a public-domain tier (digitize freely, no licensing) and a modern
in-copyright tier. The public-domain tier is **21 works / 939 citations** — and Yad
Malachi is a quarter of it by itself:

| Public-domain work Sefaria lacks               | Halachipedia citations | vs. Yad Malachi |
|:-----------------------------------------------|-----------------------:|----------------:|
| **Yad Malachi** (Malachi HaKohen, d. 1772)     |                **243** |               — |
| Birkei Yosef (Chida, d. 1806) †                |                    129 |      1.9× fewer |
| Sdei Chemed (C. C. Medini, d. 1904)            |                     32 |      7.6× fewer |
| Rokeach · Yafeh Lelev · Maharam Chalava (tied) |                18 each |     13.5× fewer |

† The Birkei Yosef figure comes from this project's original citation research and was
**not** re-derived in the later full-corpus sweep, which itemized per-work counts only for
works it newly surfaced. So rows 2–4 are the highest per-work figures this repo actually
records — not certified ranks 2, 3 and 4, and the tier's un-itemized middle is known to
hold works above 32.[^pdtier]

What is not in doubt is the top row: **243 of the tier's 939 citations — 26% of every
public-domain citation Sefaria lacks — sit on one work.** Nothing else in the tier is
close, at either figure on record for the runner-up.

## The gap this closes

Yad Malachi is **public domain**, yet has **no free, structured, linkable** text. What
exists is paywalled or unstructured — Otzar HaChochma (searchable page-images,
subscription) and the proprietary Machon Yerushalayim edition. So all 287 references stay
dead, and anyone quoting the work must **hand-transcribe from a scan**. Digitizing it once
ends that permanently.

## An ideal candidate

Public domain, cleanly structured (numbered *klalim* map straight onto a digital schema),
and **already scanned** — no physical scanning needed.

### The witnesses in hand

Four print editions across five scans (the two Przemyśl 1877 files are one printing scanned
twice), each inspected page-by-page. These are **page images**; some ship an embedded OCR
layer, but it is **not good enough to use** (see *Method*) — the work is to OCR the images.

| Edition                                   | Press                          | Script                                 | Scan in Hand                             | Pages         |
|:------------------------------------------|:-------------------------------|:---------------------------------------|:-----------------------------------------|:--------------|
| **Livorno 1766–7** (*princeps*)[^livorno] | Moshe Attias (Livorno)         | **Rashi** (body); square lemmas        | HebrewBooks #32530 / #32532 / #32531     | 348 / 54 / 55 |
| **Berlin 1851/2**[^berlin]                | Ephraim Herz / Y. Zittenfeld   | **Square** (cleanest print)            | Google Books (in hand); NLI (catalogued) | 337           |
| **Przemyśl 1877**[^p1877]                 | M. A. Knoller / Żupnik         | **Rashi** (body); square headers/lemmas| HebrewBooks #14122                       | 491           |
| **Przemyśl 1877** (2nd scan)[^p1877]      | "                              | **Rashi** (same printing)              | Google Books                             | 489           |
| **Przemyśl 1888**[^p1888]                 | Żupnik, Knoller & Hamerschmidt | *unverified*[^p1888]                   | Google Books                             | 373           |

**Only Berlin is set in clean square type** — the Przemyśl 1877 printing's body is Rashi
(corrected 2026-08-19, see [^p1877]), which is why Berlin is the OCR base and why a
Rashi-capable engine is needed for everything else. Berlin's *Klalei HaGemara* opening,
rendered directly from `berlin_square_corrected.pdf`, page 14:

![The opening page of Klalei HaGemara (Aleph section) in the Berlin edition of Yad Malachi, in clean square Hebrew type](images/yad-malachi-berlin-klal-aleph.png)

_Berlin's *Klalei HaGemara* opening — the cleanest square images to OCR._

## Method — many witnesses, one human decision

Accuracy on dense rabbinic Hebrew does not come from proofreading a single OCR pass. It
comes from putting several *independent* readers in front of the same ink, surfacing every
place they disagree, and resolving each disagreement **against the scan** — not against a
model's confidence score.

1. **Extract.** Google Cloud Document AI produces full-page words with high-precision
   bounding boxes over the Berlin square-type images. Every downstream crop depends on
   those coordinates.
2. **Add witnesses that fail differently.** A multimodal VLM (**Gemini 3.6 Flash**) reads
   whole pages; **Surya**, a locally-run open OCR engine, reads them again at 300 DPI.
   Each is measured against the corpus, not assumed: VLM **93.3%** token accuracy over all
   222 reviewed klalim, Surya **89.9%** mean agreement, Tesseract **3.8%** — which is why
   Tesseract is retained only as a historical witness and not as a leg of the pipeline.
3. **Diff, don't trust.** Each witness's reading is aligned against the stored text word by
   word. Agreement is the null result; every disagreement becomes a candidate with a real
   bounding box.
4. **Adjudicate against the ink — selection-only.** Each disputed token's box is cropped
   from the scan and put to a vision model **with the candidate readings**, which must
   *select* one and say why. It is never asked to generate a reading; anything unattested
   comes back as a flagged conjecture, not a silent change.
5. **Repair known printer's defects before counting agreement.** This printing sets
   *aleph-lamed* as one ligature sort (`ﭏ`) that OCR has no mapping for and reads as a bare
   *aleph* — silently dropping the *lamed*. A dedicated filter restores it, arbitrated by
   an independent 6.18-million-word reference corpus, never by this project's own lexicon.
6. **A human rules on every change.** Decisions are recorded in an append-only ledger and
   promoted into the corpus by a separate, deliberate step. No batch run can overwrite a
   human judgment.
7. **Structure and ingest** — parts → klalim → one segment per klal, plus a confidence map.

### What we measured that the field assumes

The standard argument for ensemble OCR is that independent engines make uncorrelated
errors, so agreement is near-proof. **We tested that on this corpus and it is false**, and
the finding is worth more than the pipeline that produced it:

- **P(the consensus reading is correct | two distinct engines agree) is ~26–41%** —
  measured, not modelled. A published-style estimate for the same configuration put the
  odds of correlated error at 3.5 × 10⁻⁷. Consensus is a **triage signal**, not a decision
  procedure, and auto-approval on consensus is indefensible at any threshold this data
  supports.
- **Architectural independence is defeated by a defect in the shared input.** Three
  different engines read the same worn sort and make the same wrong call: 37 measured cases
  of two or three engines agreeing on an identical error, including unanimous 3-of-3, all
  from that one alef-lamed ligature. Every engine is reading the same ink.
- **Tightening the rule doesn't rescue it.** Requiring the primary engine, or unanimity,
  buys three points of precision for 82% of the recall — measured, then rejected.
- So the pipeline uses agreement to decide **where to look first**, and the ink to decide
  **what is true**. That is the opposite of what a confidence threshold does.

**Copyright.** Reproduce base text only from public-domain printings; you may *consult* a
modern critical edition for a hard reading, but not reproduce its apparatus. (General
principle, not legal advice.)

## Current state

_Every figure below is read from the live corpus and dashboard, not from a past report._

### What exists

| | |
|:---|:---|
| **Klalei HaGemara, complete** | 667 klalim, ~179,000 words, scan pages 14–247, extracted, chunked and structured |
| **Klalim 1–222** (`part1.json`) | full verification pipeline: alignment, four witnesses, vision adjudication, live review dashboard |
| **Klalim 223–667** | text and page-level alignment built; **no witness set yet** |
| **Klalei HaPoskim / HaDinim** | scanned (pages 254–331), **never extracted** |

### Klalim 1–222, in detail

- **222 / 222 klalim have a trusted page-to-klal alignment** — the scan-to-text mapping
  every crop depends on.
- **1,061 flagged word positions across 185 klalim.** 356 are machine-resolved (a known
  printer's-defect artifact, not a real disagreement); **997 remain open** for a human,
  and 64 carry a recorded decision. The vision model returns an honest low-confidence
  "uncertain" rather than a fabricated guess when a crop is genuinely ambiguous.
- Those items come from two independent sources — **538 word-level candidates** from the
  DocAI-vs-corpus diff, and **364 multi-witness consensus disputes** where two or three
  engines agree on a reading the corpus doesn't have. 72 positions are flagged by both.
- **The corpus-wide ligature defect was found, root-caused, and repaired.** Confirmed by
  three independent kinds of evidence agreeing: the ink itself under high-DPI
  magnification, cross-engine character distributions, and semantic correctness of every
  reconstructed reading. **131 corrections across 51 klalim** were applied through
  flag → human review → apply, never a direct edit. The filter that automates the
  recognition was **validated before it was trusted**: on a reviewer's complete
  22-decision review of one klal it took the primary engine from **0/18 correct to 17/18**,
  and on 106 candidates the reviewer had already resolved it agreed **106/106**. It now
  identifies 118 of the 538 candidates (**24% of the queue**) as pure artifact.
  Worked example: [`VERIFIED-AGAINST-THE-INK.html`](VERIFIED-AGAINST-THE-INK.html).
- **A 174-year-old printer's error in the very first klal, flagged and left standing.**
  In **Klal 1, word 229** the Berlin typesetter set `דנראח` — with a final *chet* — where
  the sentence requires `דנראה` (`"...דנראה מתוך דבריו..."`, *"it appears from his
  words"*). The printed word occurs **nowhere else in this work and nowhere in a
  6.18-million-word rabbinic reference corpus**; the correct form occurs 3× in these 222
  klalim, 12× across all 667, and 43× in the reference corpus. The pipeline flagged it in
  seconds — **and the corpus still reads `דנראח` today**, because emending a printed source
  is a human's call, not a detector's. That is the discipline, not a gap in it.
- The pipeline also catches structural defects a text-only pass would miss entirely —
  token reordering and heading contamination traced directly to coordinate bounding boxes.
- **1,774 decisions in an append-only ledger** (`review_decisions.jsonl`), kept outside the
  automated rebuild so no batch run can overwrite a human judgment. **303 regression
  tests** guard the pipeline — 282 gating every rebuild, 5 on the witness engine, 16
  browser tests over the review dashboard.

### What is deliberately not done

- **No `part2.json`/`part3.json` correction has been applied.** Klalim 223–667 are gated
  behind independent confirmation that the reviewed third is clean — a standing decision,
  on the reasoning that a clean first third is not evidence the rest comes out clean by the
  same process.
- **Klalei HaPoskim and Klalei HaDinim have not been started.** Roughly 78 scanned pages.
  Extraction there is a fresh run, not a rerun.

## Cost & effort

The upfront investment is in the **reusable digitization and review harness**; subsequent
public-domain texts inherit it.

- **Harness & pipeline engineering** (DocAI ingestion, alignment, multi-witness synthesis,
  VLM adjudication, review UI, export tooling): ~80–120 dev hours, done.
- **Compute & API** (Document AI OCR + Gemini vision adjudication): low hundreds of dollars
  for the full corpus. Surya is local and free.
- **Expert Talmid Chacham review**: the live queue is **997 open items across klalim
  1–222**, at roughly 1–3 minutes each with the crop, the candidates and the model's
  reasoning already on screen — call it **~30–50 focused hours** for that third, and a
  comparable pass per remaining third once its witness set is built. That is an estimate
  from the queue's current size, not a measured throughput; the honest comparison is
  against the 200–300+ hours transcribing or proofreading raw scans from scratch.

## Preparing the text for Sefaria

The last mile keeps two things separate — **the text** and **the links**:

- **Text.** OCR the **Berlin edition images** (cleanest square; source from NLI, which also
  sidesteps Google's terms — **check resolution before committing to it**, see [^berlin]:
  NLI's anonymous download tier tested at ~4× fewer pixels than the scan used here).
  Licensing is clean — a PD edition, and mechanical OCR of PD text carries no new
  copyright.[^ocrpd] **Keep the prose faithful:** don't expand abbreviations (that's a
  read-time Dicta layer); *do* proof against the image, strip cruft (running headers, page
  numbers, stamps), and **segment into the schema** (*Yad Malachi, Klalei HaGemara,
  Klal N*). The schema this project already emits declares exactly one node —
  `Klalei HaGemara` — which is what the corpus actually is.
- **Links.** Don't hand-insert them — Sefaria's **Auto-Linker** builds them from parseable
  citations (title spelled out + numeric ref).[^linker] So the useful "normalization" is on
  the *citation references*, not the prose. Design the schema's addressing to **match how
  the 287 sources cite it**, or the inbound links won't auto-resolve.
- **Link-readiness QA.** Before ingest, run the text through the linker as a *test* (don't
  apply links): it flags each unresolved citation and pairs it with a verified candidate
  normalization for the reviewer.

## The ask

Digitize Yad Malachi and place it in Sefaria — the top freely-digitizable work it lacks.

1. **Independent outside confirmation.** Image-grounded, confidence-scored adjudication has
   reached full-corpus scale for klalim 1–222 (222/222 aligned) through a working
   human-review dashboard. The next gate is a Talmid Chacham confirming that output
   independently, before anything downstream is promoted.
2. **Work the queue, then extend it.** 997 open items are waiting on a reviewer today;
   klalim 223–667 need their witness set built next; Klalei HaPoskim and HaDinim need
   extraction from page 254 on.
3. **Coordinate ingest** with Sefaria (**hello@sefaria.org**), attaching each printing as
   its own version.

287 dead references become live links, hand re-keying ends, and the open-source pipeline
remains available for every subsequent rabbinic digitization project.

## Notes

[^parts]: The corpus's own three files (`part1.json`, `part2.json`, `part3.json`) are
    **chunks of Klalei HaGemara** — klalim 1–222, 223–444, 445–667 — not the work's three
    parts; the repo's "Parts 2-3" vocabulary refers to those files. Established
    2026-08-25 from the printed book: the alphabetical section headers run continuously
    across all three files, page 247 closes with `סליקו כללי הגמרא`, page 254 is a fresh
    part title page (`חלק שני · כללי שני התלמודים`) whose first klal is numbered `א`, and
    the project's own Sefaria export schema had always declared a single
    `Klalei HaGemara` node. Evidence trail in `PROJECT-STATUS-HISTORY.md`.

[^wiki]: English Wikipedia, "Malachi ben Jacob ha-Kohen" — three-part structure;
    author's death in 1772; his standing among later authorities and the Chida's
    praise; and the republication history (2001; Machon Yerushalayim critical
    edition 2016; third volume 2018). Its per-part klal counts are not used here; see
    [^parts].

[^sefaria]: Sefaria search API (`search-wrapper`, `type: text`), querying the corpus
    for citations of יד מלאכי: **287** in-corpus references, and the per-work
    breakdown in the table (Ayin Zokher 118, Petach Einayim 17, Shem HaGedolim 13,
    Pardes Yosef 11, Kaf HaChayim 9, Rosh David 8, and the further works listed).

[^halachipedia]: Halachipedia (halachipedia.org) — an open, contemporary,
    English-language halachic wiki/compendium. This project's citation survey of its
    full 640-page corpus found **243** direct citations of Yad Malachi by its numbered
    klalim — confirmed against `CORPUS-COMPARISON.md`.

[^brown]: Benjamin Brown (Hebrew University of Jerusalem), *"'Some say this, some say
    that': Pragmatics and discourse markers in Yad Malachi's interpretation rules,"*
    **JLL 3 (2014): 1–19**, DOI 10.14762/jll.2014.001. An independent, non-halachic
    (linguistics) study that calls Yad Malachi "one of the most important halakhic rule
    books" and "one of the classic books of rules … known for its clear and organized
    writing style." Bibliography: R. Malachi HaCohen Montefoscoli (1695–1772) of Livorno,
    *Yad Malachi*, 3 vols., Livorno: Moshe Attias Press, 1766–1767.

[^forum]: tora-forum.co.il, thread *"האומנם הכלל הוא שב'יש ויש' שבשולחן ערוך ההלכה כיש
    בתרא?"* ("is the rule really that a *yesh … ve-yesh* in the Shulchan Aruch follows
    the latter opinion?"). The opening post anchors on Yad Malachi — attaching its
    Klalei HaPoskim page. Forum-wide figures: exact-phrase search of tora-forum.co.il
    for *"יד מלאכי"* yielded 108 posts / 71 threads (50 citing a specific klal; 6
    requesting a scan), evidence of ongoing demand.

[^ovadia]: R. Ovadia Yosef's methodology systematically applies *klalei ha-hora'ah*
    (the rules of pesak governing Rif/Rambam/Rosh and Mechaber), Yad Malachi's exact
    domain. R. Ovadia Yosef's circle (Yalkut Yosef, Chazon Ovadyah, Yabia Omer,
    Yechave Daat, Halacha Brurah, Taharat HaBayit) accounts for ~2,300 of 6,771
    absent citations in Halachipedia — a third of the entire demand signal.

[^mostwanted]: Per this project's citation analysis of the full 640-page Halachipedia
    corpus: among the works Sefaria lacks, Yad Malachi (243 citations) ranks **#6
    overall and #1 of the public-domain tier**. The five works ahead of it overall are
    all modern in-copyright works (Yalkut Yosef, Chazon Ovadyah, Igrot Moshe,
    Shemirat Shabbat KeHilchata, Yabia Omer).

[^pdtier]: Tier totals (21 public-domain works / 939 citations) and per-work counts
    for Sdei Chemed, Rokeach, Yafeh Lelev, and Maharam Chalava are from `CORPUS-COMPARISON.md`.
    15 un-itemized public-domain works share 593 citations, averaging ~40 each.

[^livorno]: **Livorno 1766–7, first edition** (HebrewBooks #32530 / #32532 / #32531).
    Title page: *ספר יד מלאכי*, by *מלאכי בכמ"ר יעקב הכהן*; the three parts (Klalei
    HaGemara / HaPoskim / HaDinim). The *editio princeps*: body set in **Rashi
    script** with square keyword-lemmas. Digitized as three part-files (348 / 54 / 55 pp).
    Held locally, outside this repo.

[^berlin]: **Berlin, Hebrew year תרי"ב = 1851/2 CE.** In hand as a Google
    Books full-view scan (3440×5312px per page), publicly downloadable
    at <https://www.google.com/books/edition/_/OdiHjxI3I0EC>. Publisher:
    `דפוס י. זיטטענפעלד` (Y. Zittenfeld press, matching NLI catalog record
    `990011859020205171`). Date confirmed 2026-08-18 directly from NLI's
    cataloging and two internal chronograms (*תרי"ב*, 612 = 1851/2), superseding an
    earlier secondhand "~1857" estimate. Clean square type.

[^p1877]: **Przemyśl 1877** — present in two independent scans: HebrewBooks #14122
    and Google Books. Colophon: *פרעמישלא בשנת התרל"ז לב"ע* (5637 = 1877),
    publisher M. A. Knoller, printed by Żupnik & Knoller. **Rashi script in the body,
    with square running headers and square bold klal-lemmas** (corrected 2026-08-19;
    verified by direct render of pages 30, 250, 400, 480).

[^p1888]: **Przemyśl 1888** (Google Books full-view scan). Colophon: *JAD MALACHI,
    PRZEMYŚL, Drukiem Żupnika, Knollera i Hamerszmida, 1888* (*התרמ"ח*, 5648).
    Script unverified; treat as unconfirmed.

[^ocrpd]: General principle, not legal advice: mechanical OCR of a public-domain
    text is a reproduction of the underlying work and does not generate a new copyright
    (*Bridgeman Art Library v. Corel Corp.*). This does not extend to modern critical
    apparatuses or annotations.

[^linker]: Sefaria's Auto-Linker parses structured citations (title + section) to
    automatically generate cross-corpus links.
