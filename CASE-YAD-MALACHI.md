# A case for digitizing Yad Malachi

_Scan, OCR, and structure one foundational public-domain work of Torah that is heavily
relied upon but has no public digital text._

> **Bottom line.** *Yad Malachi* is the **#1 public-domain work Sefaria lacks** — cited
> **287 times inside Sefaria's own corpus** (every one a dead link) and **243 times** in
> **Halachipedia**[^halachipedia] (an open compendium of contemporary halachic analysis).
> It is public domain, and **four editions in five scans are already in hand** — three
> of the four editions in clean square type, the kind general OCR reads best. All 667
> numbered *klalim* are OCR'd and structured, and **Part 1** (*Klalei HaGemara*, 222
> klalim) has already reached full-corpus-scale, image-grounded AI adjudication — not a
> pilot anymore (see ["Current state"](#current-state) for the verified numbers).
> Marker-position verification already reaches all three parts. **Current step:**
> independent outside confirmation that Part 1's output is clean, then extending the
> same scan-region and adjudication rigor to Parts 2–3.

## The work

**Yad Malachi** (יד מלאכי), by **R. Malachi ben Jacob HaKohen** of Livorno (1695–1772),
first printed Livorno 1766–7. A three-part masterwork of *methodology* — the *grammar* of
the tradition, reached for whenever a question of method arises:

1. **Klalei HaGemara** — the rules and technical terms of the Talmud, alphabetical.
2. **Klalei HaPoskim** — the rules governing the codifiers (Rif, Rambam, Rosh, Tur, Shulchan Aruch).
3. **Klalei HaDinim** — the principles of halachic decision.

![Title page of the Berlin edition of Yad Malachi, naming the three parts Klalei HaGemara, Klalei HaPoskim, and Klalei HaDinim](images/yad-malachi-berlin-title.png)

_Berlin edition title page — the three parts and the author. Rendered directly from
`berlin_square_corrected.pdf`, page 6._

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

_[Illustration pending: two real dead-end citations — a Halachipedia footnote and the
Chida's Shem HaGedolim (already in Sefaria) both cite Yad Malachi; the linker returns
`linkFailed` because there is no text to point to. Screenshot not currently in the repo.]_

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
Rashi** — what general OCR reads best. Berlin's *Klalei HaGemara* opening, rendered
directly from `berlin_square_corrected.pdf`, page 14:

![The opening page of Klalei HaGemara (Aleph section) in the Berlin edition of Yad Malachi, in clean square Hebrew type](images/yad-malachi-berlin-klal-aleph.png)

_Berlin's *Klalei HaGemara* opening — the cleanest square images to OCR. A Rashi-script
side-by-side comparison is buildable from the Livorno first edition now in hand
(`scans/Hebrewbooks_org_32530.pdf`, title page confirms `נדפס בליוורנו` and printer
ר' משה עטיאס — this table's own HebrewBooks #32530 citation) whenever wanted._

## Process — ensemble OCR with AI adjudication

Accuracy on dense rabbinic Hebrew comes from **consensus across witnesses**, not
proofreading one pass: OCR engines make uncorrelated errors, so where several agree the
reading is near-certain and only disagreements need review.

1. **Gather witnesses.** Five scans / four editions in hand, each an independent witness.
   The two Przemyśl printings share a press (Żupnik/Knoller) — *near*-independent; the
   strongest pairing is Berlin (square) against the Livorno first edition (Rashi).
2. **OCR the images — don't trust the embedded text.** The shipped OCR layers are unusable
   (sample comparison not currently in the repo: Berlin cleanest but still errs, Przemyśl
   badly letter-confused, Livorno unusable). Run **Google Cloud Vision / Document AI** +
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

A first pass over the full work — all three parts, 667 numbered *klalim* — was run via the
**lean single-edition path**: extraction and cross-validation from the Berlin square-type
scan (PDF text layer vs. Document AI), with iterative LLM-driven linguistic/lexicon cleanup
passes. That text is chunked, structured, and sitting in the repo today.

Step 4's **image-grounded, selection-only AI adjudication** is no longer a single untested
pilot — it is the routine, day-to-day correction pipeline for **Part 1** (*Klalei HaGemara*,
klal 1–222), run through a purpose-built local review dashboard (crop + candidate readings +
confidence, alongside the full running text) that a human reviewer works through directly,
not a tool still being designed. Current state, verified against the live corpus files, not
estimated:

- **222 / 222** Part-1 klalim have a trusted page-to-klal alignment (up from a partial
  208/222 earlier in the project) — the scan-to-text mapping every crop depends on.
- **127 flagged word-level candidates remain open** — down sharply from the high-700s as
  corrections get applied — and **91 of those already carry a vision-model verdict against
  the actual scan crop, 90 at ≥0.9 confidence.** The model returns an honest low-confidence
  "uncertain" rather than a fabricated guess when a crop is genuinely too ambiguous to call.
- **A systematic, corpus-wide OCR defect was found, root-caused, and fixed**: this print
  sets the letter pair *aleph-lamed* as a single ligature glyph that the OCR engine has no
  mapping for and reads as a bare *aleph*, silently dropping the *lamed* — confirmed by
  three independent kinds of evidence agreeing (the ink itself under high-DPI magnification,
  a second OCR engine splitting the same glyph the opposite way, and the semantic
  correctness of every reconstructed reading), not by any single confident-looking output.
  **131 corrections across 51 klalim**, applied through the same flag → human-review → apply
  pipeline as every other correction, never a direct edit. Full worked example — the actual
  scan crop, the ascender comparison, the cross-engine and semantic evidence — is in
  [`VERIFIED-AGAINST-THE-INK.html`](VERIFIED-AGAINST-THE-INK.html); it is the clearest
  illustration in the project of what "understanding the actual Rabbinic Hebrew and context"
  means in practice, not a slogan.
- The pipeline has also caught structural defects a text-only pass would miss entirely —
  klal 83's stored text once carried a duplicated opening word with klal 82's own closing
  citation misplaced into the middle of it, traced to Document AI detecting one
  decoratively-set word as two separate tokens and extracting both ahead of a citation line
  that sits physically above them on the page. Confirmed directly against the raw token
  coordinates, not inferred from context, and fixed. Also worked out in full in
  [`VERIFIED-AGAINST-THE-INK.html`](VERIFIED-AGAINST-THE-INK.html).
- Every correction of this kind is recorded through an append-only decision log, kept
  deliberately separate from the corpus-rebuild pipeline so no automated run can ever
  silently overwrite a human judgment call, and the codebase carries a standing regression
  suite (100+ tests) plus multiple independent code-revalidation passes checking the
  pipeline's own decision logic, not just its output.

Marker-position verification — where each klal's own gematria marker sits on the scan,
and whether the text after it matches what's stored — now reaches all three parts, not
just Part 1. What Parts 2–3 (*Klalei HaPoskim*, *Klalei HaDinim* — 445 of 667 klalim)
don't yet have is the layer built on top of that: trusted per-klal scan regions and the
DocAI-vs-stored-text adjudication pass Part 1 already runs. Building and applying that —
and any correction it finds — stays deliberately **out of scope** until Part 1 is
independently confirmed clean by an outside reviewer — not because the method doesn't
generalize, but because Parts 2–3's own scan data has already been observed to fail
differently, and worse, than Part 1's on at least two unrelated defect classes, so a
clean Part 1 is not by itself evidence Parts 2–3 will come out equally clean by the same
process.

## Cost

**The real cost is the *first* text — everything after is a few hundred dollars,**
because the harness is reusable. ~340–460 pages (the square editions bind all three
parts in ~340; the Livorno set is 348 + 54 + 55).

- **One-time harness** (OCR-ensemble + alignment + adjudication): ~40–80 dev hrs — spent
  once, **reused** for every public-domain work after this one.
- **Compute** (multi-engine OCR of the images + AI adjudication): low hundreds of dollars.
- **Expert review** (flagged set, by a Talmid Chacham): ~5–10 hrs (~$150–350), versus
  ~25–45 to proofread every page.

**Net:** this work = harness + a few hundred dollars. Every work after = a few hundred
dollars alone, because the harness is already built. Output can beat any single historic
printing. (The lean single-edition path skips the harness.) _Cost figures are estimates;
page counts from the source catalogs; editions identified from the title pages
transcribed in the footnotes._

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
  **verified candidate normalization** for the reviewer — a worked example (7 flagged; 5
  got verified candidates, e.g. *Rashi on Nedarim 19b*) was produced during scoping but its
  file is not currently in the repo.

**Two paths.** *Lean:* OCR just the Berlin edition, proof, structure — a solid version up
fast (Sefaria is a wiki, refine later). *Full ensemble:* the higher-accuracy upgrade,
reusable for the next work.

## The ask

Digitize Yad Malachi and place it in Sefaria — the top freely-digitizable work it lacks.

1. **Independent outside confirmation that Part 1 is clean.** Image-grounded,
   confidence-scored adjudication has already reached full-corpus scale for Part 1
   (*Klalei HaGemara*, 222/222 klalim aligned) through a working human-review dashboard —
   the next gate is a Talmid Chacham confirming the output independently, not this
   pipeline's own self-assessment, before anything downstream builds on it.
2. **Extend the alignment and correction pipeline to Parts 2–3.** Marker-position
   verification is already built corpus-wide; what's left is the per-klal scan regions
   and the DocAI-vs-stored-text adjudication pass Part 1 already has — deliberately not
   started before (1), since Parts 2–3's own scan data has already shown it can fail
   differently, and worse, than Part 1's.
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

[^halachipedia]: Halachipedia (halachipedia.org) — an open, contemporary,
    English-language halachic wiki/compendium. This project's citation survey of its
    full 640-page corpus found **243** direct citations of Yad Malachi by its numbered
    klalim — confirmed against `CORPUS-COMPARISON.md` (kept in this repo for
    reference, not a live link to the underlying Halachipedia corpus, so it will go
    stale if that corpus changes).

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
    "~⅓ of every citation Sefaria lacks" figure is confirmed against
    `CORPUS-COMPARISON.md` (kept in this repo for reference; see the Halachipedia
    footnote above on staleness): R. Ovadia Yosef's circle (Yalkut Yosef, Chazon
    Ovadyah, Yabia Omer, Yechave Daat, Halacha Brurah, Taharat HaBayit) accounts for
    ~2,300 of 6,771 absent citations there — a third of the entire demand signal,
    one beit midrash. A direct citation count from *within* R. Ovadia's own works
    could not be machine-verified — they are not in a free, searchable digital
    corpus — so beyond that concentration figure, this remains a qualitative
    observation grounded in his documented method and in contemporary co-citation,
    not a counted statistic.

[^mostwanted]: Per this project's citation analysis of the full 640-page Halachipedia
    corpus: among the works Sefaria does **not** have, Yad Malachi (243 citations)
    ranks **#6 overall and #1 of the public-domain tier** — both confirmed against
    `CORPUS-COMPARISON.md` (kept in this repo for reference; see the Halachipedia
    footnote above on staleness). The five works ahead of it overall are all modern,
    in-copyright works (Yalkut Yosef, Chazon Ovadyah, Igrot Moshe, Shemirat Shabbat
    KeHilchata, Yabia Omer) — `CORPUS-COMPARISON.md` confirms this same ranking and
    this same five, at higher counts (945/573/485/409/320) than the original
    citation. Yad Malachi is the top work that can be freely digitized. The specific
    claim that the next public-domain work, Birkei Yosef, trails at 129 isn't in
    `CORPUS-COMPARISON.md` (its own "newly surfaced" list only covers PD works that
    weren't already known from an earlier, smaller sample) and so remains presented
    as originally researched, not independently re-verified here.

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

[^ocrpd]: General principle, not legal advice (as the surrounding paragraph itself
    already says): mechanical OCR of a public-domain
    text is a reproduction of the underlying work, not an original creative
    contribution, so it does not itself generate a new copyright over the resulting
    text — the same reasoning underlying *Bridgeman Art Library v. Corel Corp.*
    (S.D.N.Y. 1999) for photographic reproductions of public-domain works. This does
    not extend to a critical edition's own apparatus, annotations, or original
    scholarly additions, which the "Copyright" note above already treats as
    off-limits to reproduce.

[^linker]: Sefaria's Auto-Linker is a real, documented feature of its
    citation-parsing/auto-linking system. The specific research behind this note's
    claim was not preserved in this repo; verify directly against Sefaria's own
    documentation before relying on the specific mechanics described in the
    surrounding paragraph.
