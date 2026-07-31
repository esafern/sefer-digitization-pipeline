# A case for digitizing Yad Malachi

_A proposal to scan, OCR, and structure one foundational, public-domain work of
Torah that is heavily relied upon but not yet available as clean digital text._

## The work

**Yad Malachi** (יד מלאכי), by **R. Malachi ben Jacob HaKohen of Livorno**
(d. 1772), first printed Livorno 1766–7 (later Berlin 1857). It is a three-part
masterwork of *methodology* — the rules by which the Talmud is learned and halacha
is decided:

1. **Klalei HaTalmud** — an alphabetical index of the rules and technical terms of
   the Talmud, with explanations.
2. **Klalei HaPoskim** — the rules governing the codifiers (Rif, Rambam, Rosh, Tur,
   Shulchan Aruch…).
3. **Klalei HaDinim** — the principles of halachic decision-making and responsa.

It is, in short, the *grammar* of the tradition: not a text read once, but a
reference reached for whenever a question of method arises.

## Why it matters

Its standing is not a matter of opinion — and it is not a historical curiosity.

**Across the centuries.** The author was "quoted **frequently by major halakhic
authorities of the 18th and 19th centuries**," and the Chida praised Yad Malachi
effusively.[^wiki] That reliance is measurable inside the digital library today:
**287 places in Sefaria's existing texts cite יד מלאכי**[^sefaria] — and every one
is a **dead end**, because the work itself is not in the library. A reader who
reaches "Yad Malachi, Klal …" inside a work Sefaria *does* have cannot follow the
reference. The citing works span three centuries:[^sefaria]

| Mentions | Citing work |
|---:|---|
| 118 | Ayin Zokher |
| 17 | Petach Einayim (Chida) |
| 13 | Shem HaGedolim (Chida) |
| 11 | Pardes Yosef |
| 9 | Kaf HaChayim (d. 1939) |
| 8 | Rosh David (Chida) |
| — | + Mishnah Berurah / Biur Halacha, Torah Temimah, Minchat Chinukh, Even Ha'azel, and living responsa (Benei Banim) |

**And in active use today.** Yad Malachi is a living reference, not a shelved
classic:

- It is **continuously republished**: again in the late 20th century, a new Israeli
  edition in 2001, a **Machon Yerushalayim critical edition in 2016** (freshly
  typeset, cross-referencing parallel *Klalim* works), and a third volume in
  2018.[^wiki] A work the contemporary Torah-publishing world keeps re-typesetting
  is a work in active use — and the subject of modern scholarship.[^brown]
- In a large **contemporary English-language halachic reference** (Halachipedia),
  Yad Malachi is cited **243 times** — directly, by its numbered klalim.[^halachipedia]
  That makes it the **single most-cited public-domain work that Sefaria
  lacks**[^mostwanted] — present-day halachic writing reaching for it, hundreds of
  times, right now.
- Modern authorities cite it directly: Kaf HaChaim (d. 1939) and the contemporary
  responsa Benei Banim appear among the 287 above.

## The gap this closes

Yad Malachi is **public domain** — no rights, no license, no permission needed. Yet
there is no **publicly available** clean digital text of it. So every one of those
287 references is unlinkable, and anyone quoting the work must **hand-transcribe the
Hebrew** from a scan. Digitizing it once turns 287 dead references into live links and ends the
re-keying — permanently.

## Why it is an ideal candidate

- **Public domain** — free to reproduce.
- **Cleanly structured** — its native form (numbered *klalim* within three parts)
  maps directly onto a digital schema, so each reference becomes individually
  linkable.
- **Public-domain scans already exist** — no physical scanning needed; see the
  witnesses below.

### The witnesses in hand

Every scan below was inspected page-by-page and identified from its title page. They
resolve to **four distinct print editions across five independent scans** (the two
Przemyśl 1877 files are one printing scanned twice), and each PDF already carries an
embedded OCR text layer:

| Edition | Press | Script | Scan in hand | Pages (scan) |
|---|---|---|---|---|
| **Livorno 1766–7** — *editio princeps*[^livorno] | (Livorno) | **Rashi** (body); square lemmas | HebrewBooks #32530 / #32532 / #32531 (3 part-files) | 348 / 54 / 55 |
| **Berlin ~1857/8**[^berlin] | Ephraim Herz | **Square** | Google Books | 337 |
| **Przemyśl 1877**[^p1877] | M. A. Knoller | **Square** | HebrewBooks #14122 | 491 |
| **Przemyśl 1877** (2nd scan)[^p1877] | " | **Square** | Google Books | 489 |
| **Przemyśl 1888**[^p1888] | Żupnik, Knoller & Hamerschmidt | **Square** | Google Books | 373 |

The three later editions each bind all three parts in one volume, and **all three
are set in clean square Hebrew type, not Rashi** — which is exactly what
general-purpose OCR reads best (see process). The same passage — the opening of
*Klalei HaAleph*, on Rashi to Nedarim 19b — in the Berlin (square) and Livorno
(Rashi) editions:

![Yad Malachi, opening of Klalei HaAleph: Berlin square type vs. Livorno Rashi type, the same passage side by side](images/yad-malachi-rashi-vs-square.png)

## Process — ensemble OCR with AI adjudication

High accuracy on dense rabbinic Hebrew comes not from proofreading one OCR pass but
from **consensus across many witnesses**. OCR engines make *uncorrelated* errors, so
where several agree the reading is near-certain, and disagreements are automatically
localized to specific words — turning "proofread everything" into "adjudicate the
few conflicts."

1. **Gather every public-domain witness.** Five scans of four editions are already in
   hand — the Livorno 1766–7 first edition (Rashi) and three square-set reprints
   (Berlin ~1857/8, Przemyśl 1877 in two scans, Przemyśl 1888); add any further early
   printings from Otzar if convenient. Each edition is an independent witness to the
   same PD text. (Modern critical editions are *not* scanned into the corpus — see the
   copyright note.) Two caveats on independence: the two Przemyśl printings share a
   press lineage (Żupnik/Knoller), so treat them as *near*-independent; the strongest
   independent pairing is **Berlin** (square) against the **Livorno** first edition
   (Rashi). The two scans of Przemyśl 1877 are the same *type* but differ in scan
   noise, so they still help the vote.
2. **Start from the OCR you already have, then add engines.** Every one of these PDFs
   — both the Google Books and the HebrewBooks files — **already carries an embedded
   OCR text layer** (verified: ~3,000 characters of extractable text per page). So
   the ensemble does not start from zero: Google's OCR (on the Google Books scans) and
   HebrewBooks' OCR are two *free, already-computed* witnesses on the square editions.
   Extract those first, then add fresh passes to raise accuracy and de-correlate
   errors. **Worked example:** [`data/ocr-samples/`](ocr-samples/) shows the same three
   passages (the Aleph/Bet/Gimel section openings) as raw embedded OCR from all five
   scans — a concrete look at how much they agree, and where they don't. It is a sharp
   reminder that square type is *necessary but not sufficient*: the Berlin scan OCRs
   cleanly, yet the (also square) Przemyśl Google scans come out badly letter-confused,
   and the Rashi Livorno is unusable as-is — which is exactly why the steps below add
   better engines rather than trusting the embedded layers:
   - **Square editions (Berlin, Przemyśl) — the base text.** Run **Google Cloud
     Vision / Document AI** and **Tesseract `heb`** (both strong on square Hebrew,
     both weak on Rashi — which is why the square editions carry the load). These plus
     the two embedded layers give **~4 passes per square edition**.
   - **Livorno first edition (Rashi) — collation witness.** General engines fail on
     Rashi, so read it with a Rashi-capable tool: **Jochre 3** (open-source, trained
     for rabbinic/Rashi type) or a **Kraken/eScriptorium** model trained on this
     typeface. It contributes variant readings, not the base.
   - **Rabbinic-Hebrew post-correction on every pass.** Run outputs through
     **Dicta**[^dicta] — a free Israeli non-profit built specifically for rabbinic
     Hebrew: its OCR/**Maivin** tools expand abbreviations, restore
     punctuation, and its rabbinic language model (**BEREL**) fixes context-obvious
     OCR errors (e.g. a wrong letter inside a known talmudic phrase). Dicta is
     web-based, so it runs on macOS in a browser; I found **no dedicated Mac desktop
     app built on Dicta** — the closest "built-for-this" option is Dicta's own tools,
     with **ABBYY FineReader** (desktop Mac/Windows, good general square OCR, no
     rabbinic specialization) and **Transkribus** (trainable HTR platform) as
     alternatives. Uncorrelated errors across these engines *and* editions make
     agreement a strong signal.
3. **Align and vote — per scan.** Align the engine outputs (word/character sequence
   alignment, anchored on the numbered *klalim*) and take a per-token consensus.
   Agreed tokens — the large majority — are accepted automatically; only conflicts
   are flagged.
4. **AI adjudication — image-grounded, selection-only.** For each flagged token,
   give a multimodal model (Claude / GPT with vision) the candidate readings **plus
   the cropped scan image** of that word, and have it *select* the correct reading —
   never invent text. It must name the witness it relied on; anything not attested
   by a scan is a flagged conjecture for a human, not a silent change. This is the
   critical guardrail against the model "helpfully" emending the text to what it
   expects.
5. **Collate the editions.** With each printing reduced to a best-text, collate them
   against each other. Genuine differences between printings (a typo or correction in
   one) are recorded as variants — yielding a text potentially *more accurate than
   any single historic printing*, with an apparatus. (This is a corrected reading of
   the PD printings against each other — not a critical edition; the modern Machon
   Yerushalayim edition is the scholarly critical text, and this does not aim to
   supersede it.)
6. **Expert review — only the flagged set.** A **domain expert — a Torah scholar
   (Talmid Chacham) fluent in this genre**, not merely a Hebrew reader — resolves the
   remaining conflicts against the scan (and may **consult** the modern critical
   editions as a reference for hard readings — see note) and spot-checks the
   auto-accepted text. The genre matters: dense abbreviations, talmudic shorthand, and
   the *klalim*-cross-references are ambiguous to a non-specialist, so the reviewer's
   fluency is what makes the flagged readings resolvable. Because they only ever touch
   disagreements, this is a fraction of full proofreading.
7. **Structure and ingest** into the three parts and their klalim; output text +
   per-token confidence map + variant apparatus.

**Copyright note.** The *base text you reproduce* comes only from fully
public-domain printings. You may **consult** modern critical editions (2001; Machon
Yerushalayim 2016) to decide a hard reading — using a work to inform judgment is not
infringement — but you may not reproduce their annotations, cross-references, or
apparatus, or OCR them into the corpus; source the actual reading from a PD printing.
(General principle, not legal advice; have counsel bless the workflow before
publication.)

## Cost

The ensemble front-loads a little engineering and collapses the human cost — which
is the expensive part of any digitization.

The work is **~457 pages** (the verified Livorno set: 348 + 54 + 55), OCR'd across
a couple of witnesses.

- **One-time harness** (OCR-ensemble + alignment + adjudication): developer time,
  ~40–80 hrs, and **reusable** for every other public-domain work — so it amortizes
  far beyond this one text.
- **Compute** (multi-engine OCR + AI adjudication over ~460 pages across the
  editions — and two OCR passes per square edition already exist free as embedded
  text layers): modest — low hundreds of dollars in OCR/API credits at most.
- **Expert review** — only the flagged conflict set, and by a Torah scholar (Talmid
  Chacham), not a general proofreader. If the ensemble auto-accepts ~90% of tokens,
  the reviewer handles the rest in perhaps **~5–10 hours (~$150–350)**, versus ~25–45
  hours to proofread all 457 pages single-pass.

Net: after the reusable harness exists, the **marginal cost per work is a few hundred
dollars**, and the output is *more* accurate than a single proofread pass —
potentially better than any of the historic printings. For that, a foundational work
of Torah
— cited 287 times inside the very library that currently lacks it, and 243 times in
contemporary halachic writing — goes permanently online.

_Cost figures are estimates; page counts are from the source catalogs and from the
scan page-counts. Every scan was inspected page-by-page; edition identifications are
from the title pages transcribed in the footnotes below._

## Notes

[^wiki]: English Wikipedia, "Malachi ben Jacob ha-Kohen" — three-part structure;
    author's death in 1772; his standing among later authorities and the Chida's
    praise; and the republication history (2001; Machon Yerushalayim critical
    edition 2016; third volume 2018).

[^sefaria]: Sefaria search API (`search-wrapper`, `type: text`), querying the corpus
    for citations of יד מלאכי: **287** in-corpus references, and the per-work
    breakdown in the table (Ayin Zokher 118, Petach Einayim 17, Shem HaGedolim 13,
    Pardes Yosef 11, Kaf HaChayim 9, Rosh David 8, and the further works listed).

[^halachipedia]: This project's citation survey of Halachipedia (a large contemporary
    English-language halachic reference): **243** direct citations of Yad Malachi by
    its numbered klalim, in the full 640-page corpus (`data/CORPUS-COMPARISON.md`).

[^brown]: Benjamin Brown, *"Some Say This, Some Say That": … Interpretation Rules in
    Yad Malachi* — modern academic scholarship on the work.

[^mostwanted]: Per this project's citation analysis of the full 640-page Halachipedia
    corpus (`data/SEFARIA-MOST-WANTED.md`, `data/CORPUS-COMPARISON.md`): among the
    works Sefaria does **not** have, Yad Malachi (243 citations) ranks **#6 overall
    and #1 of the public-domain tier** — the next public-domain work, Birkei Yosef,
    trails at 129. The five works ahead of it overall are all modern, in-copyright
    works (Yalkut Yosef, Chazon Ovadyah, Igrot Moshe, Shemirat Shabbat KeHilchata,
    Yabia Omer) that cannot be freely digitized; Yad Malachi is the top work that can.

[^livorno]: **Livorno 1766–7, first edition** (HebrewBooks #32530 / #32532 / #32531).
    Title page: *ספר יד מלאכי*, by *מלאכי בכמ"ר יעקב הכהן*; the three parts (Klalei
    HaGemara / HaPoskim / HaDinim). The *editio princeps*: body set in **Rashi
    script** with square keyword-lemmas; the roughest of the scans (ink bleed, skew).
    Digitized as three part-files (348 / 54 / 55 pp).

[^berlin]: **Berlin ~1857/8** (Google Books full-view scan). Title page: *ספר יד
    מלאכי חלק ראשון*, publisher *אפרים הערץ* (Ephraim Herz), *מדינת שלעזיען*, place
    *ברלין* (Berlin); notes it was "printed first in Livorno … and now a second time."
    The Przemyśl 1877 title page dates this Berlin printing to *התרי"ח* (5618 =
    1857/8). **Square** type, the cleanest scan. (The NLI copy carries the
    Hazanovitz-collection bookplate — a provenance stamp, not part of the edition.)

[^p1877]: **Przemyśl 1877** — present in two independent scans: HebrewBooks #14122 and
    a separate Google Books full-view scan. Title page: *ספר יד מלאכי חלק ראשון* …
    *מלאכי בכמ"ר יעקב הכהן*; colophon *פרעמישלא בשנת התרל"ז לב"ע* (5637 = 1877),
    publisher *משה אהרן קנעניל* (M. A. Knoller), printed by *ר' חיים אהרן זאפניק ען
    קנאללער* (Zupnik & Knoller); it names the prior Livorno (first) and Berlin
    (*התרי"ח*) printings. **Square** type. The two Przemyśl printings share this press
    lineage, so treat them as *near*-independent.

[^p1888]: **Przemyśl 1888** (Google Books full-view scan). Latin colophon: *JAD
    MALACHI, PRZEMYŚL, Drukiem Żupnika, Knollera i Hamerszmida, 1888*; Hebrew
    *פרעמישלא בשנת התרמ"ח לב"ע* (5648 = 1888). **Square** type.

[^dicta]: Dicta — analytical tools for Hebrew texts (dicta.org.il), a free Israeli
    non-profit; its Maivin tool vocalizes and punctuates rabbinic text, expands
    abbreviations, and identifies sources, and its BEREL model is a rabbinic-Hebrew
    language model. See also English Wikipedia, "Dicta (organization)."
