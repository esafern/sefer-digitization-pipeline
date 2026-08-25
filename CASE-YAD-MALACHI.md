# The case for digitizing Yad Malachi

_One foundational public-domain work of Torah is missing from every free digital
library, and it is the most-cited one still missing. It is also the cheapest to
fix._

## The case in five lines

1. **Sefaria's own corpus cites *Yad Malachi* 287 times, and every one is a dead
   link.**[^sefaria] The work isn't in the library.
2. **It is the single most-cited public-domain work Sefaria lacks** — 243
   citations in Halachipedia, **26% of every public-domain citation Sefaria is
   missing**, and roughly twice the next title on record.[^halachipedia]
3. **It is public domain, cleanly numbered, and already scanned.** Nothing has to
   be licensed, negotiated or photographed.
4. **The hard part is already built and measured.** A working pipeline takes the
   scan to reviewed text with an audit trail — at a few hundred dollars of
   compute and tens of hours of expert time, against 200–300+ hours of
   transcribing from scratch.
5. **Done once, it stays done.** 287 references light up, hand re-keying ends,
   and the harness is reusable for the next public-domain work.

## Why this work

**Yad Malachi** (יד מלאכי), by **R. Malachi ben Jacob HaKohen** of Livorno
(1695–1772), is the standard reference on the *rules* of halachic reasoning —
the grammar of the tradition, reached for whenever a question of method arises.
Its first part, ***Klalei HaGemara***, runs 667 numbered *klalim* alphabetically
from `כללי האלף` to `כללי התיו`.[^parts]

![Title page of the Berlin edition of Yad Malachi](images/yad-malachi-berlin-title.png)

_Berlin edition title page, rendered from the source scan._

Its standing is measurable, not a matter of taste.[^wiki]

**The Chida relies on it constantly.** Of the 287 citations inside Sefaria, ~156
are his, across four works — the towering Sephardi authority of the era, the
author's own contemporary, treating it as a standing reference. Another ~130 span
the next two centuries: Pardes Yosef, Kaf HaChaim, Mishnah Berurah / Biur
Halacha, Torah Temimah, Minchat Chinukh, living responsa.

| Mentions | Citing work |
|---------:|:------------|
| 118 | Ayin Zokher (Chida) |
| 17 | Petach Einayim (Chida) |
| 13 | Shem HaGedolim (Chida) |
| 11 | Pardes Yosef |
| 9 | Kaf HaChayim (d. 1939) |
| 8 | Rosh David (Chida) |
| — | + Mishnah Berurah / Biur Halacha, Torah Temimah, Minchat Chinukh, Even Ha'azel, Benei Banim |

**It is still in active use.** New editions in 2001, a Machon Yerushalayim
critical edition in 2016, a third volume in 2018;[^wiki] modern scholarship calls
it *"one of the most important halakhic rule books."*[^brown] On one Torah forum
it appears in ~108 posts across ~71 discussions — and **six of those are people
asking someone to post a scan of a klal**, because no clean digital text
exists.[^forum] It is also central to R. Ovadia Yosef's school, whose works are
about a third of every citation Sefaria lacks.[^ovadia]

### The free-to-digitize tier is one work

A survey of Halachipedia's full corpus sorted every work Sefaria *lacks* into a
public-domain tier and a modern in-copyright tier. The public-domain tier is
**21 works / 939 citations** — and Yad Malachi is a quarter of it alone:

| Public-domain work Sefaria lacks | Citations | vs. Yad Malachi |
|:---|---:|---:|
| **Yad Malachi** (d. 1772) | **243** | — |
| Birkei Yosef (Chida, d. 1806) † | 129 | 1.9× fewer |
| Sdei Chemed (d. 1904) | 32 | 7.6× fewer |
| Rokeach · Yafeh Lelev · Maharam Chalava | 18 each | 13.5× fewer |

† Rows 2–4 are the highest per-work figures this project actually recorded, not
certified ranks — the tier's un-itemized middle is known to hold works above
32.[^pdtier] What is not in doubt is the top row.

## Why it is the cheapest one to fix

**Public domain.** No licensing, no rights-holder, no negotiation.

**Already scanned.** Four printings across five scans, each inspected
page-by-page. One of them — Berlin, 1851/2 — is set in clean square type, the
kind general OCR reads best.[^berlin] Nothing needs to be photographed.

| Edition | Script | Scan in hand |
|:---|:---|:---|
| **Livorno 1766–7** (*princeps*)[^livorno] | **Rashi** (body) | HebrewBooks |
| **Berlin 1851/2**[^berlin] | **Square** — cleanest print | Google Books; NLI catalogued |
| **Przemyśl 1877**[^p1877] | **Rashi** (body) | HebrewBooks + Google Books |
| **Przemyśl 1888**[^p1888] | *unverified* | Google Books |

**Cleanly numbered.** Numbered klalim map straight onto a Sefaria schema, and
they are how every one of the 287 sources cites the work — so the inbound links
resolve themselves once the text exists.

**Nobody has to trust the machine.** The pipeline's output is not "OCR text"; it
is a corpus where every changed word traces to a specific disagreement between
independent readers, resolved by a human looking at the actual scan crop, and
recorded in an append-only ledger. That is the difference between a text a
library can accept and a text it cannot.

## Why this pipeline

Three things, in order of how much they matter.

**1. It reads the ink, not just the text.** Every disputed word is re-cropped
from the scan at full resolution and put in front of a human alongside the
competing readings and the machine's reasoning. No correction enters the corpus
because a model was confident — only because a person looked. That is the
difference between 99% and publishable.

**2. It knows what its own machines are worth, because it measured them.** This
project tested the assumption the whole field runs on — that independent OCR
engines fail independently, so their agreement is near-proof — and found it
false on this corpus: **where two distinct engines agree, they are right 26–41%
of the time**, not 99.9%. Agreement routes attention; the ink decides. A pipeline
that doesn't know this number is trusting it blindly.

**3. It is cheap and it is reusable.** Local, one operator, a few hundred dollars
of compute for the full corpus. Everything in it — extraction, alignment,
multi-witness synthesis, crop adjudication, the review dashboard, archival export
in ALTO/PAGE/TEI — is written to work on the next Hebrew work, not just this one.

**Where it stands today.** All 667 klalim of *Klalei HaGemara* are extracted and
structured; the first 222 have been through the full verification pipeline with a
human working the queue; the rest have text and page alignment awaiting their
witness pass. Detail, measurements and costs:
[`HOW-THE-PIPELINE-WORKS.md`](HOW-THE-PIPELINE-WORKS.md). Worked examples with
the actual scan crops: [`VERIFIED-AGAINST-THE-INK.html`](VERIFIED-AGAINST-THE-INK.html).

## The ask

Put *Yad Malachi* into Sefaria — the top freely-digitizable work it lacks.

1. **An outside Talmid Chacham to confirm the reviewed text**, working a queue of
   flagged disagreements with the scan crop already on screen. This pipeline's
   own self-assessment is not the gate; an expert's judgement is.
2. **Coordinate ingest** with Sefaria (**hello@sefaria.org**), attaching each
   printing as its own version.

287 dead references become live links, hand re-keying ends, and the pipeline
stays available for every public-domain work after this one.

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
