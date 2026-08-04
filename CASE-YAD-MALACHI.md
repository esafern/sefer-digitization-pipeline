# A case for digitizing Yad Malachi

_Scan, OCR, and structure one foundational public-domain work of Torah that is heavily
relied upon but has no public digital text._

> **Bottom line.** *Yad Malachi* is the **#1 public-domain work Sefaria lacks** — cited
> **287 times inside Sefaria's own corpus** (every one a dead link) and **243 times** in
> contemporary halacha. It is public domain, and **four editions in five scans are
> already in hand** (three in clean square type). A first pass over the full work — all
> 667 numbered *klalim* — is already OCR'd and structured via the lean single-edition
> (Berlin) path. **Current step:** bringing image-grounded, confidence-scored AI
> adjudication — proven on a pilot page — up to full-corpus scale, starting with Part 1
> (*Klalei HaGemara*), the only range with scan-to-text alignment built so far.

## The work

**Yad Malachi** (יד מלאכי), by **R. Malachi ben Jacob HaKohen** of Livorno (1695–1772),
first printed Livorno 1766–7. A three-part masterwork of *methodology* — the *grammar* of
the tradition, reached for whenever a question of method arises:

1. **Klalei HaGemara** — the rules and technical terms of the Talmud, alphabetical.
2. **Klalei HaPoskim** — the rules governing the codifiers (Rif, Rambam, Rosh, Tur, Shulchan Aruch).
3. **Klalei HaDinim** — the principles of halachic decision.

![Title page of the Berlin edition of Yad Malachi, naming the three parts Klalei HaGemara, Klalei HaPoskim, and Klalei HaDinim](images/yad-malachi-berlin-title.png)

_Berlin edition title page — the three parts and the author._

## Why it matters

Its standing is independent and measurable, not a matter of opinion.[^wiki]

**287 dead ends inside Sefaria.** The corpus cites יד מלאכי in **287 places**[^sefaria] —
each unfollowable, because the work isn't in the library. Who cites it, and what it shows:

| Mentions | Citing work |
|---:|---|
| 118 | Ayin Zokher (Chida) |
| 17 | Petach Einayim (Chida) |
| 13 | Shem HaGedolim (Chida) |
| 8 | Rosh David (Chida) |
| 11 | Pardes Yosef |
| 9 | Kaf HaChayim (d. 1939) |
| — | + Mishnah Berurah / Biur Halacha, Torah Temimah, Minchat Chinukh, Even Ha'azel, Benei Banim |

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
  work Sefaria lacks.**[^mostwanted]
- **Live debate, and the pain point in the wild** — on one Torah forum, Yad Malachi appears
  in **~108 posts across ~71 discussions** (50 by a specific *klal*), and **6 are requests
  for a *scan* of a klal**, because no clean digital text exists.[^forum]
- **Central to R. Ovadia Yosef's school** — whose works are ~⅓ of every citation Sefaria
  lacks, and whose method is built on the *klalei ha-hora'ah* that Yad Malachi codifies.[^ovadia]

## The gap this closes

Yad Malachi is **public domain**, yet has **no free, structured, linkable** text. What
exists is paywalled or unstructured — Otzar HaChochma (searchable page-images,
subscription) and the proprietary Machon Yerushalayim edition. So all 287 references stay
dead, and anyone quoting the work must **hand-transcribe from a scan**. Digitizing it once
ends that permanently.

![Two real dead-end citations of Yad Malachi — a Halachipedia footnote and a Shem HaGedolim entry inside Sefaria — each failing to resolve because the work is not in the library](images/yad-malachi-broken-citation.png)

_Two real dead ends: a Halachipedia footnote and the Chida's Shem HaGedolim (already in
Sefaria) both cite Yad Malachi; the linker returns `linkFailed` — there is no text to
point to._

## An ideal candidate

Public domain, cleanly structured (numbered *klalim* map straight onto a digital schema),
and **already scanned** — no physical scanning needed.

### The witnesses in hand

Four print editions across five scans (the two Przemyśl 1877 files are one printing scanned
twice), each inspected page-by-page. These are **page images**; some ship an embedded OCR
layer, but it is **not good enough to use** (see *Process*) — the work is to OCR the images.

| Edition | Press | Script | Scan in hand | Pages |
|---|---|---|---|---|
| **Livorno 1766–7** — *editio princeps*[^livorno] | (Livorno) | **Rashi** (body); square lemmas | HebrewBooks #32530 / #32532 / #32531 | 348 / 54 / 55 |
| **Berlin ~1857/8**[^berlin] | Ephraim Herz | **Square** | Google Books | 337 |
| **Przemyśl 1877**[^p1877] | M. A. Knoller | **Square** | HebrewBooks #14122 | 491 |
| **Przemyśl 1877** (2nd scan)[^p1877] | " | **Square** | Google Books | 489 |
| **Przemyśl 1888**[^p1888] | Żupnik, Knoller & Hamerschmidt | **Square** | Google Books | 373 |

The three later editions bind all three parts and are set in **clean square type, not
Rashi** — what general OCR reads best. The same passage (opening of *Klalei HaAleph*),
Berlin square vs. Livorno Rashi:

![Yad Malachi, opening of Klalei HaAleph: Berlin square type vs. Livorno Rashi type, the same passage side by side](images/yad-malachi-rashi-vs-square.png)

![The opening page of Klalei HaGemara (Aleph section) in the Berlin edition of Yad Malachi, in clean square Hebrew type](images/yad-malachi-berlin-klal-aleph.png)

_Berlin's *Klalei HaGemara* opening — the cleanest square images to OCR._

## Process — ensemble OCR with AI adjudication

Accuracy on dense rabbinic Hebrew comes from **consensus across witnesses**, not
proofreading one pass: OCR engines make uncorrelated errors, so where several agree the
reading is near-certain and only disagreements need review.

1. **Gather witnesses.** Five scans / four editions in hand, each an independent witness.
   The two Przemyśl printings share a press (Żupnik/Knoller) — *near*-independent; the
   strongest pairing is Berlin (square) against the Livorno first edition (Rashi).
2. **OCR the images — don't trust the embedded text.** The shipped OCR layers are unusable
   ([`data/ocr-samples/`](ocr-samples/): Berlin cleanest but still errs, Przemyśl badly
   letter-confused, Livorno unusable). Run **Google Cloud Vision / Document AI** +
   **Tesseract `heb`** over the square editions' images (many passes to vote on); read the
   Rashi Livorno with **Jochre 3** or a trained **Kraken/eScriptorium** model as a
   collation witness; post-correct with **Dicta**[^dicta] (abbreviation expansion, the
   BEREL rabbinic model). ABBYY FineReader / Transkribus are alternatives.
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
   genre resolves the conflicts against the scan and spot-checks the rest — a fraction of
   full proofreading, since they touch only disagreements.
7. **Structure and ingest** into the three parts → klalim; output text + confidence map +
   apparatus.

**Copyright.** Reproduce base text only from public-domain printings; you may *consult* a
modern critical edition for a hard reading, but not reproduce its apparatus. (General
principle, not legal advice.)

## Current state

A first pass over the full work — all three parts, 667 numbered *klalim* — has already
been run via the **lean single-edition path**: extraction and cross-validation from the
Berlin square-type scan (PDF text layer vs. Document AI), with iterative LLM-driven
linguistic/lexicon cleanup passes. That text is chunked, structured, and sitting in the
repo today.

What's *not* yet done is step 4's **image-grounded, selection-only AI adjudication** at
corpus scale — but it is no longer a single untested pilot. Of Part 1's 794 flagged
word-level candidates, 90 have been vision-adjudicated against the actual scan crop, and the
underlying cache holds 86 live decisions, confidence at or above 0.9 in roughly three
quarters of them — the model returns an honest low-confidence "uncertain" rather than a
fabricated guess when a crop is genuinely too ambiguous to call. The method has also caught
a defect a text-only pass would have missed entirely: klal 83's stored text carried a
duplicated opening word with klal 82's own closing citation misplaced into the middle of
it — traced to Document AI detecting one decoratively-set word as two separate tokens and
extracting both ahead of a citation line that sits physically above them on the page,
confirmed directly against the raw token coordinates, not inferred from context. Worked
examples — scan crops, bounding boxes,
and the underlying JSON — are in [`VERIFIED-AGAINST-THE-INK.html`](VERIFIED-AGAINST-THE-INK.html).
Most corrections currently in the text came from **text-only LLM linguistic review** —
plausible given context, but not yet verified against the actual scan pixels, which is a
gap against this project's own fidelity bar (every correction should be traceable to a
real disagreement resolved by looking at the scan, not inferred). Scan-to-text alignment
(the word bounding boxes the crop-and-verify step needs) exists today only for **Part 1**
(*Klalei HaGemara*, klal 1–222); Parts 2–3 need the same alignment built before they can
reach equivalent rigor. A human-review interface (crop + candidate readings + confidence,
alongside the full running text) is in development to make that final adjudication pass
tractable for a reviewer.

## Cost

~340–460 pages (the square editions bind all three parts in ~340; the Livorno set is 348 +
54 + 55).

- **One-time harness** (OCR-ensemble + alignment + adjudication): ~40–80 dev hrs,
  **reusable** for every other PD work — the real cost of the *first* text.
- **Compute** (multi-engine OCR of the images + AI adjudication): low hundreds of dollars.
- **Expert review** (flagged set, by a Talmid Chacham): ~5–10 hrs (~$150–350), versus
  ~25–45 to proofread every page.

**Net:** the first work = harness + a few hundred dollars; each work after = a few hundred
dollars, because the harness is reused. Output can beat any single historic printing. (The
lean single-edition path skips the harness.) _Cost figures are estimates; page counts from
the source catalogs; editions identified from the title pages transcribed in the footnotes._

## Preparing the text for Sefaria

The last mile keeps two things separate — **the text** and **the links**:

- **Text.** OCR the **Berlin edition images** (cleanest square; source from NLI, which also
  sidesteps Google's terms). Licensing is clean — a PD edition, and mechanical OCR of PD
  text carries no new copyright.[^ocrpd] **Keep the prose faithful:** don't expand
  abbreviations (that's a read-time Dicta layer); *do* proof against the image, strip cruft
  (running headers, page numbers, stamps), restore two-column reading order, and **segment
  into the schema** (parts → klalim → one segment per klal, e.g. *Yad Malachi, Klalei
  HaGemara, Aleph 1*).
- **Links.** Don't hand-insert them — Sefaria's **Auto-Linker** builds them from parseable
  citations (title spelled out + numeric ref).[^linker] So the useful "normalization" is on
  the *citation references*, not the prose. Design the schema's addressing to **match how
  the 287 sources cite it**, or the inbound links won't auto-resolve — and those **287
  references light up automatically** once the work exists.
- **Link-readiness QA.** Before ingest, run the text through the linker as a *test* (don't
  apply links): it flags each unresolved citation, and this project pairs each with a
  **verified candidate normalization** for the reviewer — worked example in
  [`data/link-readiness-demo.md`](link-readiness-demo.md) (7 flagged; 5 got verified
  candidates, e.g. *Rashi on Nedarim 19b*).

**Two paths.** *Lean:* OCR just the Berlin edition, proof, structure — a solid version up
fast (Sefaria is a wiki, refine later). *Full ensemble:* the higher-accuracy upgrade,
reusable for the next work.

## The ask

Digitize Yad Malachi and place it in Sefaria — the top freely-digitizable work it lacks.

1. **Bring the proven pilot to full-corpus scale.** Extend image-grounded, confidence-scored
   adjudication from the one-page proof of concept across Part 1 (*Klalei HaGemara*), where
   scan-to-text alignment already exists, using the human-review interface now in
   development.
2. **Extend scan alignment to Parts 2–3** so the same rigor is possible there, then repeat
   the adjudication pass.
3. **Coordinate ingest** with Sefaria (**hello@sefaria.org**), attaching each printing as
   its own version.

287 dead references become live links, the re-keying ends, and the reusable harness lowers
the cost of every public-domain work after this one.

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

[^brown]: Benjamin Brown (Hebrew University of Jerusalem), *"'Some say this, some say
    that': Pragmatics and discourse markers in Yad Malachi's interpretation rules,"*
    **JLL 3 (2014): 1–19**, DOI 10.14762/jll.2014.001. An independent, non-halachic
    (linguistics) study that calls Yad Malachi "one of the most important halakhic rule
    books" and "one of the classic books of rules … known for its clear and organized
    writing style," and takes it as the representative text for analyzing how halacha
    decides between opinions. It also fixes the bibliography: R. Malachi HaCohen
    Montefoscoli (1695–1772) of Livorno, *Yad Malachi*, 3 vols., Livorno: Moshe Attias
    Press, 1766–1767.

[^forum]: tora-forum.co.il, thread *"האומנם הכלל הוא שב'יש ויש' שבשולחן ערוך ההלכה כיש
    בתרא?"* ("is the rule really that a *yesh … ve-yesh* in the Shulchan Aruch follows
    the latter opinion?"). The opening post anchors on Yad Malachi — attaching its
    Klalei HaPoskim page — and brings Edut BiYehosef (R. Yosef Samun), R. Shmuel ibn
    Elbaz, and R. Avraham Pinto; a reply cites the Mishnah Berurah (Hilchot Shabbat and
    Eruvin). A contemporary lay/lamdanut forum, cited here as evidence of live usage,
    not as a halakhic authority; read by reference per the site's robots policy. The
    forum-wide figures are from an exact-phrase search of tora-forum.co.il for *"יד
    מלאכי"* (108 posts / 71 threads; 50 citing a specific klal; 6 requesting a scan) —
    counts only; no forum text is reproduced here, per the site's `ai-train=no` signal.
    Phrase-search figures may include the occasional non-sefer occurrence of the words
    *יד מלאכי*; sampled results were all genuine citations of the work.

[^ovadia]: R. Ovadia Yosef's methodology is documented as systematically applying the
    *klalei ha-hora'ah* — the rules of pesak governing the Rif/Rambam/Rosh and the
    Mechaber (e.g. webyeshiva.org, "Rabbi Ovadia Yosef's Halakhic Methodology";
    Nishmat; R. Chaim Jachter, Kol Torah) — which is Yad Malachi's exact domain. The
    demand figures are this project's Halachipedia analysis (`CORPUS-COMPARISON.md`);
    the same-footnote co-citations (Yad Malachi with Taharat HaBayit and Yabia Omer)
    are from the Halachipedia corpus (`pipeline/hp_cache`). **Caveat:** a direct
    citation count from *within* R. Ovadia's own works could not be machine-verified —
    they are not in a free, searchable digital corpus — so this is a qualitative
    observation grounded in his documented method and in contemporary co-citation, not
    a counted statistic.

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
