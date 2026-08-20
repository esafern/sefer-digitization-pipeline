# A case for digitizing Yad Malachi

_Scan, OCR, and structure one foundational public-domain work of Torah that is heavily
relied upon but has no public digital text._

## TL;DR

**The work.** *Yad Malachi* (Livorno 1766–7) is the standard reference on the *rules* of
halachic reasoning — 667 numbered *klalim* across three parts.

**The demand is measured, not asserted.** Sefaria's own corpus cites it **287 times**, and
every one is a dead link. Halachipedia cites it **243 times** — **26% of every
public-domain citation Sefaria lacks, in one work**, and roughly **twice** the next
public-domain title on record ([the table below](#the-free-to-digitize-tier-is-one-work)).

**It is the easiest big win available.** Public domain, cleanly numbered (klalim map
straight onto a Sefaria schema), and **already scanned** — four editions in five scans in
hand — though only Berlin is in clean square type, the kind general OCR reads best.

**The work is largely done.** All 667 klalim are OCR'd and structured. **Part 1** (*Klalei
HaGemara*, 222 klalim) has 222/222 trusted page-to-klal alignment and image-grounded,
selection-only AI adjudication running as its routine correction pipeline — not a pilot.
Parts 2–3 have marker verification and the scan-linkage/adjudication infrastructure built
and run over their full page range, with 916 klalim carrying an open review flag — and,
by standing decision, not one correction applied to them yet.

**What's needed.** (1) An outside Talmid Chacham independently confirming Part 1's output is clean —
this pipeline's own self-assessment is not the gate. (2) Working through Parts 2–3's open
flags and applying what they confirm. (3) Coordinating ingest with Sefaria.

**The payoff.** 287 dead references light up automatically, hand-re-keying from scans
ends, and the harness is reusable for subsequent public-domain works.

## The work

**Yad Malachi** (יד מלאכי), by **R. Malachi ben Jacob HaKohen** of Livorno (1695–1772),
first printed Livorno 1766–7. A three-part masterwork of *methodology* — the *grammar* of
the tradition, reached for whenever a question of method arises:

1. **Klalei HaGemara** — the rules and technical terms of the Talmud, alphabetical (222 klalim).
2. **Klalei HaPoskim** — the rules governing the codifiers: Rif, Rambam, Rosh, Tur, Shulchan Aruch (299 klalim).
3. **Klalei HaDinim** — the principles of halachic decision (146 klalim).

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
  the most important halakhic rule books"* / *"one of the classic books of rules."*[^brown]
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
layer, but it is **not good enough to use** (see *Process*) — the work is to OCR the images.

| Edition                                   | Press                          | Script                                 | Scan in Hand                             | Pages         |
|:------------------------------------------|:-------------------------------|:---------------------------------------|:-----------------------------------------|:--------------|
| **Livorno 1766–7** (*princeps*)[^livorno] | Moshe Attias (Livorno)         | **Rashi** (body); square lemmas        | HebrewBooks #32530 / #32532 / #32531     | 348 / 54 / 55 |
| **Berlin 1851/2**[^berlin]                | Ephraim Herz / Y. Zittenfeld   | **Square** (cleanest print)            | Google Books (in hand); NLI (catalogued) | 337           |
| **Przemyśl 1877**[^p1877]                 | M. A. Knoller / Żupnik         | **Rashi** (body); square headers/lemmas| HebrewBooks #14122                       | 491           |
| **Przemyśl 1877** (2nd scan)[^p1877]      | "                              | **Rashi** (same printing)              | Google Books                             | 489           |
| **Przemyśl 1888**[^p1888]                 | Żupnik, Knoller & Hamerschmidt | *unverified*[^p1888]                   | Google Books                             | 373           |

The later editions bind all three parts. **Only Berlin is set in clean square type** —
the Przemyśl 1877 printing's body is Rashi (corrected 2026-08-19, see [^p1877]), which
is why Berlin remains the OCR base and why a Rashi-capable engine is needed for
everything else. Berlin's *Klalei HaGemara* opening, rendered
directly from `berlin_square_corrected.pdf`, page 14:

![The opening page of Klalei HaGemara (Aleph section) in the Berlin edition of Yad Malachi, in clean square Hebrew type](images/yad-malachi-berlin-klal-aleph.png)

_Berlin's *Klalei HaGemara* opening — the cleanest square images to OCR. A Rashi-script
side-by-side comparison is buildable from the Livorno first edition in hand
(`scans/Hebrewbooks_org_32530.pdf`, title page confirms `נדפס בליוורנו` and printer
ר' משה עטיאס — HebrewBooks #32530) whenever wanted._

## Process — ensemble OCR with AI adjudication

Accuracy on dense rabbinic Hebrew comes from **consensus across witnesses**, not
proofreading one pass: OCR engines make uncorrelated errors, so where several agree the
reading is near-certain and only disagreements need review.

1. **Gather witnesses.** Five scans / four editions in hand, each an independent witness.
   The two Przemyśl printings share a press (Żupnik/Knoller) — *near*-independent; the
   strongest pairing is Berlin (square) against the Livorno first edition (Rashi).
2. **OCR the images — don't trust embedded text.** The shipped OCR layers are unusable
   (Berlin cleanest but still errs, Przemyśl badly letter-confused, Livorno unusable).
   The core pipeline uses **Google Cloud Document AI** to extract full-page words and
   high-precision bounding boxes over Berlin's square images. Earlier tests using Tesseract
   `heb` showed low discriminative power on historical rabbinic type (only 3.8% accuracy on
   disagreements, 16/419); the pipeline now relies on high-resolution multimodal vision
   models (**Gemini 3.6 Flash**) and rabbinic lexicon validation to resolve disputes against
   the ink crops. Collation against Rashi-set editions (Livorno, Przemyśl) leverages **Dicta**[^dicta]
   and trained HTR/VLM models.
3. **Align and vote.** Per-token consensus anchored on the numbered *klalim*; agreed tokens
   auto-accepted, conflicts flagged.
4. **AI adjudication — image-grounded, selection-only.** For each flagged token, give a
   vision model the candidate readings **plus the cropped scan** and have it *select* —
   never invent — naming the witness it used. Anything unattested is a flagged conjecture,
   not a silent change. This is the guardrail against "helpful" emendation.
5. **Collate the editions** into a variant apparatus — potentially more accurate than any
   single historic printing. (Not a critical edition; it does not aim to supersede the
   Machon Yerushalayim text.)
6. **Expert review — flagged set only.** A Torah scholar (Talmid Chacham) fluent in the
   genre resolves the conflicts against the scan and spot-checks the rest — reviewing
   the flagged disputes rather than reading the entire corpus cold.
7. **Structure and ingest** into the three parts → klalim; output text + confidence map +
   apparatus.

**Copyright.** Reproduce base text only from public-domain printings; you may *consult* a
modern critical edition for a hard reading, but not reproduce its apparatus. (General
principle, not legal advice.)

## Current state

A first pass over the full work — all three parts, 667 numbered *klalim* — was run via the
**lean single-edition path**: extraction and cross-validation from the Berlin square-type
scan (PDF text layer vs. Document AI), with iterative LLM-driven linguistic/lexicon cleanup
passes. That text is chunked, structured, and sitting in the repo today.

Step 4's **image-grounded, selection-only AI adjudication** is the routine, day-to-day
correction pipeline for **Part 1** (*Klalei HaGemara*, klal 1–222), run through a
purpose-built local review dashboard (crop + candidate readings + confidence, alongside
the full running text) that a human reviewer works through directly. Current state,
verified against live corpus files:

- **222 / 222** Part-1 klalim have a trusted page-to-klal alignment — the scan-to-text
  mapping every crop depends on.
- **539 word-level correction candidates across 149 klalim**, of which **387 remain open**
  (machine-disputed, awaiting human ruling) — down as corrections get applied. The vision
  model returns an honest low-confidence "uncertain" rather than a fabricated guess when
  a crop is genuinely too ambiguous to call.
- **A systematic, corpus-wide OCR defect was found, root-caused, and fixed**: this print
  sets the letter pair *aleph-lamed* as a single ligature glyph that the OCR engine has no
  mapping for and reads as a bare *aleph*, silently dropping the *lamed* — confirmed by
  three independent kinds of evidence agreeing (the ink itself under high-DPI magnification,
  cross-engine character distributions, and semantic correctness of every reconstructed
  reading). **131 corrections across 51 klalim**, applied through the same flag → human-review →
  apply pipeline, never a direct edit. Full worked example is in
  [`VERIFIED-AGAINST-THE-INK.html`](VERIFIED-AGAINST-THE-INK.html).
- **A 170-year-old printer's error in the very first klal was caught by 21st-century AI**: In **Klal 1 (word 229)**, the 1857 Berlin edition typesetter printed **`דנראח`** (with a final Chet `'ח'`). Our automated Rabbinic AI lexicon gap detector flagged this word for review:
  1. *The printer's word (`דנראח`)* **a) makes no sense textually** in context (`"...דנראה מתוך דבריו..."` — *"it appears from his words"*), and **b) is nowhere else to be found** — zero occurrences in this text, and zero occurrences across our 6.18-million-word Rabbinic reference lexicon (Shulchan Arukh, Talmud Bavli, Mishneh Torah, Tur, Rashi).
  2. *The correct replacement word (`דנראה`)* is **found 3 times in Part 1** (and 12 times across the full 667-klal Yad Malachi text), and **countless times across the Rabbinic lexicon** (43x independently attested in core reference texts). An error that stood undetected in print for over 160 years was identified and resolved in seconds.
- The pipeline has also caught structural defects a text-only pass would miss entirely —
  such as token reordering and heading contamination in klal 83, traced directly to
  coordinate bounding boxes and fixed.
- Every correction is recorded through an append-only decision log (`review_decisions.jsonl`),
  kept separate from the automated rebuild pipeline so no batch run can overwrite a human
  judgment call. The codebase carries a standing regression suite (**241 tests** — 227
  gating every pipeline rebuild, 14 browser tests over the review dashboard) plus independent
  code-revalidation passes checking pipeline logic.

**Parts 2–3** (*Klalei HaPoskim*, *Klalei HaDinim* — 445 of 667 klalim): Marker-position
verification, scan-linkage, and vision-adjudication infrastructure reach all three parts across
the full 667 klalim, surfacing **916 open review flags** queued for reviewer adjudication.

## Cost & Effort

The upfront investment is in the **reusable digitization and review harness**; subsequent
public-domain texts benefit from this infrastructure.

- **Harness & pipeline engineering** (DocAI ingestion, alignment, VLM adjudication, review UI, export tools): ~80–120 dev hours.
- **Compute & API costs** (Document AI OCR + Gemini 3.6 Flash vision adjudication): low hundreds of dollars (~$150–$300 for the full corpus).
- **Expert Talmid Chacham review**: **~40–80 focused hours (~$2,000–$4,000)** to systematically review the ~1,300 flagged candidate readings, verify ambiguous Rabbinic ligature crops against the ink, check obscure Talmudic/Rishonim citations, and certify corpus fidelity across all 667 klalim. (Far more efficient than the 200–300+ hours required to transcribe or proofread raw scans from scratch.)

## Preparing the text for Sefaria

The last mile keeps two things separate — **the text** and **the links**:

- **Text.** OCR the **Berlin edition images** (cleanest square; source from NLI, which also
  sidesteps Google's terms — **check resolution before committing to it**, see [^berlin]:
  NLI's anonymous download tier tested at ~4x fewer pixels than the high-res scan used in
  this pipeline). Licensing is clean — a PD edition, and mechanical OCR of PD text carries
  no new copyright.[^ocrpd] **Keep the prose faithful:** don't expand abbreviations (that's
  a read-time Dicta layer); *do* proof against the image, strip cruft (running headers,
  page numbers, stamps), restore two-column reading order, and **segment into the schema**
  (parts → klalim → one segment per klal, e.g. *Yad Malachi, Klalei HaGemara, Aleph 1*).
- **Links.** Don't hand-insert them — Sefaria's **Auto-Linker** builds them from parseable
  citations (title spelled out + numeric ref).[^linker] So the useful "normalization" is on
  the *citation references*, not the prose. Design the schema's addressing to **match how
  the 287 sources cite it**, or the inbound links won't auto-resolve — and those **287
  references light up automatically** once the work exists.
- **Link-readiness QA.** Before ingest, run the text through the linker as a *test* (don't
  apply links): it flags each unresolved citation, pairing each with a verified candidate
  normalization for the reviewer.

## The ask

Digitize Yad Malachi and place it in Sefaria — the top freely-digitizable work it lacks.

1. **Independent outside confirmation that Part 1 is clean.** Image-grounded,
   confidence-scored adjudication has reached full-corpus scale for Part 1 (222/222 klalim
   aligned) through a working human-review dashboard. The next gate is a Talmid Chacham
   confirming the output independently before downstream promotion.
2. **Review and finalize Parts 2–3.** Marker verification and scan-linkage infrastructure
   are complete; 916 klalim carry review flags. Proceed with expert review and apply
   verified corrections.
3. **Coordinate ingest** with Sefaria (**hello@sefaria.org**), attaching each printing as
   its own version.

287 dead references become live links, hand re-keying ends, and the open-source pipeline
remains available for every subsequent rabbinic digitization project.

## Notes

[^wiki]: English Wikipedia, "Malachi ben Jacob ha-Kohen" — three-part structure;
    author's death in 1772; his standing among later authorities and the Chida's
    praise; and the republication history (2001; Machon Yerushalayim critical
    edition 2016; third volume 2018).

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

[^berlin]: **Berlin, Hebrew year תרי"ב = 1851/2 CE.** In hand as a Google
    Books full-view scan (3440×5312px per page), publicly downloadable
    at <https://www.google.com/books/edition/_/OdiHjxI3I0EC>. Publisher:
    `דפוס י. זיטטענפעלד` (Y. Zittenfeld press, matching NLI catalog record
    `990011859020205171`). Date confirmed 2026-08-18 directly from NLI's
    cataloging and internal chronograms (*תרי"ב*, 612 = 1851/2). Clean square type.

[^p1877]: **Przemyśl 1877** — present in two independent scans: HebrewBooks #14122
    and Google Books. Colophon: *פרעמישלא בשנת התרל"ז לב"ע* (5637 = 1877),
    publisher M. A. Knoller, printed by Żupnik & Knoller. **Rashi script in the body,
    with square running headers and square bold klal-lemmas** (corrected 2026-08-19;
    verified by direct render of pages 30, 250, 400, 480).

[^p1888]: **Przemyśl 1888** (Google Books full-view scan). Colophon: *JAD MALACHI,
    PRZEMYŚL, Drukiem Żupnika, Knollera i Hamerszmida, 1888* (*התרמ"ח*, 5648).
    Script unverified; treat as unconfirmed.

[^dicta]: Dicta — analytical tools for Hebrew texts (dicta.org.il), an Israeli
    non-profit; its tools include rabbinic text analysis, abbreviation expansion,
    and source identification.

[^ocrpd]: General principle, not legal advice: mechanical OCR of a public-domain
    text is a reproduction of the underlying work and does not generate a new copyright
    (*Bridgeman Art Library v. Corel Corp.*). This does not extend to modern critical
    apparatuses or annotations.

[^linker]: Sefaria's Auto-Linker parses structured citations (title + section) to
    automatically generate cross-corpus links.
