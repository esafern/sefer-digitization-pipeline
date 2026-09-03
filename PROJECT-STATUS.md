# Project Status — current state

## TL;DR

_Current state only. Every claim here is measured, not remembered; the dated
evidence for each is in `PROJECT-STATUS-HISTORY.md`._

**What the corpus is.** The 667 klalim are ***Klalei HaGemara* in its entirety** —
the work's part one, scan pages 14–247, closing with `סליקו כללי הגמרא` on page
247. `part1/2/3.json` are three FILE CHUNKS of that one part (klalim 1–222,
223–444, 445–667), **not** the work's three parts. *Klalei HaPoskim* (pages
254–291) and *Klalei HaDinim* (292–329) have never been extracted — 76 pages.
Corrected 2026-08-25 against the printed page; the docs had said otherwise since
they were written.

**How much text actually exists.** **596 of 667 klalim carry real text**
(~188,000 words). The other **71 hold a generated placeholder** (`רנ כלל 250`),
all in klalim 223–667 — see open item 16. 44 were reconstructed from the DocAI
token stream and are flagged as unreviewed machine output; **12 of those carry
confirmed page-furniture damage — see open item 20**, which is the one thing in
this file that should be read before quoting the 596.

**Where the review stands** (klalim 1–222, the reviewed third):

| | |
|---|---|
| page-to-klal alignment | 222 / 222 trusted |
| flagged word positions | 1,061 across 185 klalim |
| …made of | 538 pipeline candidates + 364 consensus disputes, 72 shared |
| open / decided / machine-resolved | see the dashboard — re-measure, don't quote from here |
| witnesses read against the ink | DocAI, a VLM sampled twice, Surya at 300 DPI |

**What the witnesses are worth, measured.** **Dicta 95.6% word accuracy over
klalim 2–221 (full Part 1 coverage, 2026-09-02 — the strongest witness here)**,
VLM 93.3% token accuracy, Surya 89.9% mean agreement (222/222 coverage),
Tesseract 3.8% on disagreements — the last is why it is being retired (item 3a).
Dicta is a PREVIEW only: nothing is wired into `rebuild_all.sh`. **P(consensus correct | two distinct
engines agree) is 26–41%**, so agreement routes attention and the ink decides;
auto-approval on consensus is indefensible at any threshold this data supports.

**The binding constraints.** The Parts 2-3 gate (`START_HERE.md`) still holds:
no `part2.json`/`part3.json` correction may be applied. Recording a decision and
applying it to the corpus remain two separate, deliberate steps.


## Open items

### The Dicta pass is COMPLETE — pages 22–114, all of Part 1

_Closed 2026-09-02. The reviewer submitted the five remaining chunks by hand and
dropped the results in `~/Downloads`; they were validated, copied into
`dicta_output/`, and the baseline rebuilt. This section was the file's top open
item since 2026-08-31 and is kept only as the record of what it produced._

**`tools/second_witness_eval/dicta_jerusalem_part1_baseline.txt` now covers scan
pages 22–114** — 467,093 bytes, 10 chunks, header self-flipped from PARTIAL to
COMPLETE. `build_dicta_baseline.py` refuses to write on a gap or overlap, so the
clean write is itself the contiguity proof.

| measured over klalim 2–221 (51,115 reference tokens) | |
|---|---:|
| Dicta word accuracy | **95.6%** |
| lexicon hit rate | 97.1% (corpus ceiling 97.8%) |
| positions Dicta votes at | 50,362 of 52,057 |
| …agreeing with the corpus | 48,842 (97.0%) |

**95.6% across the whole of Part 1, against 95.5% measured on the pages 22–50
third** — the score held when coverage tripled, which is the thing a partial
measurement could not tell us. Dicta is now the strongest witness this project
has by a wide margin: VLM 93.3%, Surya 89.9%, Tesseract 3.8%.

**The preview (`DICTA-NEW-DISPUTES.md`, 419 links) reports 225 new disputes, 186
corroborated, 8 positions a human already ruled against, 0 displacing a different
consensus.** 225 is 3.9x the 58 from the partial baseline — inside the 3–4x this
file predicted. **It is still a PREVIEW: nothing is wired into `rebuild_all.sh`,**
and wiring it in remains a separate decision (item 0N has the three integration
points: `synthesize_multi_witness.ENGINES`, one line in
`assemble_corrections_dataset.py`, and a `dicta_reading` option in `app.js` —
without that last one the field is serialized and never seen, Lesson 29).

`job_id` is null for the five new chunks in `dicta_chunks_remainder/manifest.json`:
they were fetched by hand from the RashiOCR status page rather than through
`tools/fetch_dicta_result.sh`, so no job id was ever seen here. Left null rather
than invented — a value in an audit trail that resolves to nothing is worse than
an absent one.

**The two standing constraints still hold.** Never point Dicta at the square
Berlin scan (77.6% there, worse than everything already wired in), and Dicta is
deterministic (item 0V), so a repeat run buys nothing: it cannot be its own
reliability check, and every dispute still needs the ink or a different engine.

> **Item IDs are allocated per LANE, and are never reassigned once written.**
> Two concurrent sessions share this file, and a newest-first list with
> hand-picked single letters cannot survive that: both writers reach for "the
> next letter" and collide. It happened twice in one day — `0S/0T/0U`, then
> `0V/0W/0X` within hours — and renaming after the fact is not a fix, because
> item IDs are load-bearing: `apply_reviewer_decisions.py` and three test files
> cite them by name in comments (`item 0A`, `0B`, `0C`, `0F`, `0R`, `0U`, `0W`).
>
> - **`0A`–`0Z` — the review/corpus lane** (the main clone, which holds the
>   dashboard and the decision ledger).
> - **`1A`–`1Z` — the refactor lane** (the `-refactor` worktree).
> - A third lane takes `2A`–`2Z`. **Before writing an item, grep the file for
>   your next letter** — the cost of checking is one command; the cost of not
>   checking is an ambiguous cross-reference that a rename cannot safely undo.
>
> Resolved 2026-09-01 by moving the refactor lane's three colliding entries to
> `1G`/`1H`/`1I` — chosen over renaming the review lane's because those are the
> ones code references.

> **The review lane has run out of single letters — `0A`–`0Z` are all
> allocated.** Continuing as `0AA`, `0AB`, … in the same band rather than
> borrowing `2A`–`2Z`, which names a different lane and would misattribute the
> work. Same rule as above: never reassign an ID once written.

0AX. **[2026-09-03] THE 58 ARE APPLIED — and the gate blocked them, correctly,
    because a corpus invariant still held the belief the reviewer had just
    overturned from the ink. The blacklist now defers to a human ruling.**

    All 58 promoted (11 replace, 2 delete, 16 manual, 29 confirmed-no-op); 16
    klalim changed text; `--dry-run` now reports 0 outstanding. Item `0AQ`'s
    eight escalations are in the corpus:

    | klal · word | was | now |
    |---|---|---|
    | 59 · 47 | כוותיה | כוותה |
    | 74 · 203 | דגם | הגם |
    | 77 · 22 / 24 | וטומאות / טומאות | וטמאות / טמאות |
    | 88 · 963 | ומתיר | **ומתי'** |
    | 91 · 191 | העניינים | **העניני'** |
    | 92 · 326, 124 · 26 | אליה | **איה** |

    The two abbreviations are the ones that mattered: the corpus was carrying an
    editorial expansion as if it were the author's text, against success
    criterion #1, and it no longer is. Every one of the 16 text changes was read
    in context against its before/after (Lesson 19) — the three deletions are
    `יד`, `פז`, `יט`, page furniture at a klal's foot, not words.

    **`test_part1_no_dropped_lamed_ligature_corruption` failed the rebuild on
    klal 92 w326 and 124 w26.** It asserts no token in Part 1 is one of 24
    `DROPPED_LAMED_CORRUPT_FORMS`, and `איה` is in that set — put there by the
    2026-08-14/15 ligature fix, and put in the CORPUS that morning by the
    reviewer, from the scan. Lesson 36 exactly: a test pinned to corpus content
    fails when the corpus IMPROVES.

    **Measured before touching it: 7 of the 24 forms are themselves attested
    words in the independent reference corpus** — `אא` 1,145, `איה` 74, `אה` 49,
    `אמא` 22, `האף` 18, `אפא` 11, `והאף` 2. So membership is a suspicion, never a
    verdict, and this is the same blind spot that let `ai-dropped-lamed-
    correction` rewrite 66 attested words (item `0AT`). A blacklist no human can
    overrule would re-assert precisely the belief that pass got wrong.

    **The exemption is narrow and every clause was made to fail on purpose.**
    A position stands down only for a `manual_correction`, written BY A PERSON,
    at that klal AND that word index, whose `chosen_text` is exactly the form
    standing there. `ligature_offenders()` was extracted so it can be run on
    synthetic input, and a new test asserts the guard STILL FIRES in each of the
    four ways it must: nothing recorded, a script's ruling (item `0AT`'s case —
    a script exempts nothing), a human ruling naming a different word, and a
    human ruling at a different index. Lesson 26: an exemption is a suppression,
    and a suppression is validated by what it hides.

    **One duplicate predicate collapsed on the way.** "Did a person rule this?"
    existed twice — `review_decisions._is_human_reviewer` (the append guard) and
    `review_server._ruled_by_human` (the display), the latter's comment calling
    them "a different question with the same answer". The invariant needed a
    third. It is now one public `review_decisions.ruled_by_human`, with both old
    names delegating: START_HERE's shared-module rule and Lesson 13.

    **State after the rebuild:** full `./rebuild_all.sh` green, gate 370 passed.
    `audit_applied_decisions.py` over 553 applied decisions: 56 reflected at a
    shifted index (the known stale-address class, items `0AB`/`0AP` — the ruling
    landed, its recorded index did not move with it) and 1 the audit itself
    classifies as shifted rather than lost (klal 1 w97 punctuation). No applied
    decision is missing from the corpus.

0AY. **[2026-09-03] ITEM 39's TITLE PASS IS BUILT — (i) the detectors read the
    field, (ii) a title ruling has an apply path, (iii) a gated invariant. Only
    (iv), the EXTENT question, is left, and it needs the printed page. The very
    first run found 2 divergences and 3 candidates in a field nothing in this
    repo had ever read.**

    **(i) `--field title`, through one seam.** Six `tools/detect_*.py` sweeps
    call `corpus_io.load_klal_words`, so the field became a parameter THERE
    rather than in six files, and all six gained title coverage at once. They
    also share a new `corpus_io.detector_args()` — one parser where each had
    written its own `sys.argv[1]`, which additionally gives them a `--help` that
    does not run the sweep (item `0Z`'s shape: `patch_witness_word_indices.py`
    had no parsing at all and rewrote the witness queue on `--help`).

    **Two measurement defects had to be fixed before the numbers meant
    anything**, and both were found by reading the first output rather than
    trusting it:

    - **Every title ends with a period glued to its last word** — measured 222
      of 222, with none anywhere else — so that token is a form occurring once
      in the corpus, which is the exact trigger for the rare-form detectors. The
      first run duly proposed `מעצמנו.` → `מעצמו` on klal 144. Stripped, and
      index-preserving so a `word_index` still addresses the same word.
    - **The frequency table must stay the BODY's.** The title field is 1,287
      words; counting rare-ness inside it makes EVERY title word a hapax and the
      gate stops gating. `own_counts` now always comes from `clean_text`
      whatever field is scanned — which leaves body sweeps bit-identical, since
      for them the counting corpus already WAS the scanned one.

    **(ii) `title_correction`, a new decision type.** Not a `manual_correction`
    with a field tag: `all_current()` keys on `(klal_id, word_index)` and a title
    index is a DIFFERENT ADDRESS from a body index in the same klal, so one
    ruling would have silently displaced the other. The apply reuses
    `apply_manual_correction`/`apply_manual_deletion` unchanged — both already
    took a text and returned a text — with its own per-klal-per-run word-count
    slot, because a title shift moves nothing in the body. **This is the path
    the five hand-edits of 2026-08-31 should have had**; that exception to the
    single-source-of-truth rule need not be taken again.

    Five tests, all synthetic: the title is written and the body untouched at the
    same index; drift is refused; a ruling naming the last word WITHOUT its
    period is refused (my own first fixtures were wrong this way, and the drift
    check caught them); a second run is a no-op; and a multi-word title replace
    defers the next ruling in that klal.

    **(iii) `test_every_title_is_a_prefix_of_its_own_body`, gated.** The body
    reprints the heading, so they must agree word for word over the title's
    length — no corpus statistics needed, which is why this class found all six
    of item 39's original defects. **Two klalim diverge and both are baselined
    by ID, with reasons, not by count:**

    - **klal 186** — title `המקיל`, body `המקיל'`. One carries a stray geresh;
      both are complete words, so no frequency test can say which. Needs the ink.
    - **klal 9** — title `איידי`, body `איידי.`, the stop GLUED to the word where
      everywhere else it becomes a separate `[.]`. **Swept the class the moment
      it fired: exactly 2 body words in Part 1 carry a glued terminal period** —
      this one and klal 169 w444 `דוי.`. Deliberately NOT normalised away by
      stripping stops from the body side, which would have made the check pass by
      ceasing to look and left the class unrecorded (Lesson 26).

    A companion test builds a heading with one letter changed and asserts the
    comparison reports it — Lesson 25, since a prefix check that cannot fail is
    not a check.

    **Stage 4c, `pipeline/build_title_report.py`, in `rebuild_all.sh`.** Lesson
    32: a detector that only prints is a detector that does not run. It writes
    `title_defect_report.json` and, like 4b, **never a flag** — the ledger is
    permanent and these candidates carry real false positives.

    **What the first run says.** 222 titles, 1,287 words, 2 prefix divergences
    (above), 3 detector candidates:

    | klal · title word | stored | proposed | body reads | read |
    |---|---|---|---|---|
    | 92 · 6 | נסקי | נפקי | **נסקי, the same** | needs the ink — the idiom is `לא נפקא מינה מידי`, and the body carries the same form, so if it is wrong it is wrong in both |
    | 144 · 4 | מעצמנו | מעצמו | מעצמנו | false positive — "by ourselves" is correct in context |
    | 212 · 0 | הוון | הוו | הוון | false positive — Galilean Aramaic, correct as printed |

    So the detector half found nothing title-specific on its first pass, and the
    PREFIX half found both real questions. Worth recording, because the cheap
    structural check outperformed the expensive statistical one here exactly as
    Lesson 8 predicts.

    **(iv) EXTENT REMAINS UNMEASURED AND UNSWEEPABLE.** A title that has
    swallowed body text still agrees with its body over its own length, so no
    textual check can see it; only the printed type size says where a heading
    stops. The report names this in its own header rather than letting a clean
    run read as "titles are fine". Two are known (klalim 36, 39, both
    reviewer-identified); how many more is unknown and is not being estimated.

    Full suite **467 collected, 466 passed, 1 skipped**.

0AZ. **[2026-09-03] ITEM 0AR IS STARTED: the corpus-root seam is in, and it
    resolves at CALL time. `--corpus DIR` and `$SEFER_CORPUS_ROOT` now point the
    whole data layer at another book. The remaining four steps are unchanged.**

    Item `0AR`'s own framing is the thing that makes this one seam instead of two
    projects: **the test-independence problem and the general-purpose problem are
    the same problem.** A tool that cannot be pointed at another book at runtime
    cannot be pointed at a fixture either.

    **The coupling, re-measured today** — larger than the item's "~35 constants":
    **64 modules compute their own `REPO = dirname(dirname(__file__))`**, and
    `corpus_io`'s eight derived paths are referenced across 74 files (`REPO` 74,
    `PART1_PATH` 20, `repo_path` 20, `DOCAI_DIR` 16).

    **Resolution order, decided at every call:** an explicit `set_corpus_root()`
    (what `--corpus` uses) → `$SEFER_CORPUS_ROOT` → the source-relative default,
    which is exactly what every existing caller already got. Nothing needed to
    change at any call site.

    **CALL TIME IS THE WHOLE POINT, and the module made the mistake itself while
    I was fixing it.** The eight constants were module-level assignments, so a
    root set after import changed nothing and raised nothing — the silent defect
    `review_decisions._resolve()` exists to document, and the one `0AR` names as
    the trap. They are now PEP 562 `__getattr__` lookups, which is safe here for
    a checked reason: **`from corpus_io import X` appears zero times in this
    repo**, and a from-import would bind once and put the defect straight back.
    Then the first import crashed — `def load_part1(path=PART1_PATH)` evaluates
    its default at import too, and a module-level `__getattr__` does not answer a
    bare name inside its own module. Eleven signatures took a `None` sentinel and
    resolve in the body. The crash was the good outcome: the same shape in a
    caller would have been silent.

    **Four tests, and the first one asserts the property rather than the
    plumbing** — not "the setter works" but "the value CHANGES after import",
    which is the only thing that distinguishes this from what was there before.
    The others pin the precedence (an explicit `--corpus` outranks a stale env
    var), prove the LOADERS actually read a two-klal book written into a temp
    directory through the ordinary no-argument API, and cover the flag on the
    shared parser.

    Full `./rebuild_all.sh` green, full suite **470 passed, 1 skipped**.

    **What is NOT done, in `0AR`'s own order:** the fixture-corpus GENERATOR (it
    must be generated, not written — Lesson 13) plus a `conftest.py`, which does
    not exist today; moving the 23 UI tests that pin a klal id; splitting the ~30
    corpus invariants out into a `validate <book>` command, since asserting that
    THIS book's data is well-formed is not a test of a general-purpose tool and
    means a corpus REPAIR can turn the suite red; and the gated guard that no
    test outside the validator module resolves a path under the real corpus root.
    That guard is what stops this decaying, and it is worth noting that today's
    work added tests on both sides of that line — the seam tests are fixture-only,
    the title-prefix invariant deliberately reads the real corpus.

0BA. **[2026-09-03] THE DICTA CONSTRAINT IS AN ACQUISITION LIMIT, NOT A WIRING
    ONE — and item `0N` reads as though they were the same thing. Wiring the
    baseline this repo already holds needs ZERO fetches.**

    Reviewer, on why Dicta is not wired in: *"prob is we don't have an api, just
    an upload page that allows just five files per day."* That is right about the
    service and it does not block the integration, so it is worth separating the
    two before the next reader treats item `0N` as blocked.

    **What the pipeline would consume is a FILE, already on disk.**
    `tools/second_witness_eval/dicta_jerusalem_part1_baseline.txt` — 467,093
    bytes, complete for Part 1 (pages 22–114), written 2026-09-02 — and
    `synthesize_multi_witness.load_baseline()` reads witness baselines from text
    files exactly as it does Surya's and the VLM's. Adding `"dicta"` to
    `ENGINES`, one line in `assemble_corrections_dataset.py`, and a
    `dicta_reading` option in `app.js` (without which the field is serialized and
    never seen — Lesson 29) makes no network call at all. The 5-files-a-day
    ceiling costs nothing here.

    **What the ceiling DOES constrain** is acquiring more Dicta text: a re-run,
    or extending coverage. Part 1's 93 pages took 9 chunks at ~10 pages each, so
    roughly two days of quota — and the same ratio puts klalim 223–667 near 19
    chunks, about four days. Recorded as arithmetic about the constraint, not as
    a proposal: the Parts 2-3 gate is untouched by this entry.

    **Two standing facts still bound any use of it.** Dicta is deterministic
    (item `0V`), so a repeat run is not a reliability check and buys nothing but
    quota; and it must never be pointed at the square Berlin scan (77.6% there,
    worse than everything already wired in). Its 95.6% is on the Jerusalem
    edition, which is also why it is a genuinely independent witness — it is not
    reading the same ink as DocAI, Surya and the VLM, and item `0AQ` flagged that
    as the open question against Lesson 24.

0BB. **[2026-09-03, reviewer proposal] CONTENT-ADDRESSING FOR DRIFT: yes, but
    the address must be `(klal, word, OCCURRENCE)` — the bare word names one
    position for barely half the corpus — and the title cannot share the body's
    namespace, because the body reprints the title. Primitives, snapshot field
    and a stale-address report are in; nothing re-keys the ledger.**

    Reviewer: *"can we address drift by using klal+word as the index? same for
    title - klal+0"*. Measured before answering, and the measurements changed the
    answer twice.

    **1. `(klal, word)` alone is not an address here.** Of Part 1's 52,627 word
    positions, **24,746 (47.0%) hold a word that repeats inside its own klal**,
    and 213 of 222 klalim contain at least one repeat. Klal 54 has 44 `לא`, klal
    74 has 39 `אמר`, klal 75 has 37 `ר'`. So the bare word names a unique
    position for 53% of the corpus and is ambiguous for the rest.

    **2. `(klal, word, occurrence)` is what the proposal wants, and it is worth
    318x.** Averaged over every single-word edit point in Part 1: a numeric
    `word_index` is invalidated by **100%** of the edits before it — that is the
    definition of the thing — while `(word, occurrence)` is invalidated only by
    an edit that adds or removes THE SAME WORD earlier in the same klal, which is
    **0.3%** of later positions.

    | | invalidated by an edit earlier in the klal |
    |---|---:|
    | `word_index` | 16,450,912 / 16,450,912 (100%) |
    | `(word, occurrence)` | 51,723 / 16,450,912 (0.3%) |

    **3. The title CANNOT be `klal+0` in a shared namespace, and the number is
    the argument: 1,286 of Part 1's 1,287 title words also occur in their own
    body — 99.9%.** That is not a coincidence to be worked around, it is the
    field's definition: the body reprints the heading verbatim before continuing,
    so a content address cannot tell the two apart. **The single exception is
    klal 186 `המקיל`, whose body reads `המקיל'` — i.e. the ONE title word that
    does not collide is the one already flagged as a defect.** The separate
    `title_correction` type (item `0AY`) is therefore required, not incidental.

    **What was built — additive, and deliberately not a re-key.**
    `corpus_io.occurrence_of` / `index_of_occurrence`; `word_occurrence` recorded
    in every new `manual_correction` snapshot beside the bbox item `0AP` added;
    and `review_decisions.resolve_word_index(rec, words)` returning `(index,
    how)` where `how` is `index` / `occurrence` / `unique` / None.

    **It REPORTS; it does not relocate.** `review_server._manual_snapshot`'s
    docstring already records that "a unique text match is not evidence of
    position" — measured and rejected when `MAX_EXPLAINABLE_SHIFT` was written —
    and that judgement stands. `occurrence` is a stronger claim than that,
    because the ordinal was recorded AT RULING TIME rather than inferred now, but
    promoting it to an automatic re-point is a separate decision and has not been
    taken. It pairs with the bbox as the second independent signal re-pointing
    requires (Lesson 9).

    **The live exposure is small, and most of what looks stale is not.**
    `audit_applied_decisions.py` now ends with the breakdown:

    | | |
    |---|---:|
    | applied, word gone — **the normal outcome; applying it replaced the word** | 245 |
    | applied, recoverable | 3 |
    | **UNAPPLIED, unresolvable — needs a human** | **17** |
    | **UNAPPLIED, recoverable as a unique word** | **5** |

    So the drift that actually costs something today is ~22 rulings, not the 270
    a naive "does the word still sit at its index" count returns — the same trap
    item `0AB` fell into at 105.

    **Therefore the honest scope of the fix: it is forward-looking.** No ruling
    made before today recorded an ordinal, so the 22 above cannot be recovered by
    it; they need the ink or the bbox. What changes is that the next word-count
    edit does not manufacture a new batch. A full re-key of the 3,100-row
    append-only ledger — with `all_current()` keyed on `(klal_id, word_index)`
    everywhere and `app.js` computing the index from a click — is a much larger
    change and is NOT proposed here.

    Full suite **475 passed, 1 skipped**.

0BC. **[2026-09-03, reviewer] THE EXTENT CLASS IS THE BIG ONE, AND THE HEADING
    HAD NO WRITE PATH AT ALL. `✎ Heading` now rules on a title from the
    dashboard, whole-field at (klal, 0) — the reviewer's own addressing
    proposal. 101 headings are queued for the question. Klalim 89–92 are NOT a
    defect in the way they first looked.**

    Reviewer: *"klal 89 - 92 title is same first word"* → *"no entire title is
    that single first word, all the same. 96 title last word ahddei"*.

    **The repeated first word is the book's own ordering, not a defect.**
    *Klalei HaGemara* is ordered alphabetically by each klal's opening TERM, so
    runs are the norm: **133 of 222 klalim sit in a shared-first-word run**,
    across 35 runs — `הלכה` klalim 166–177 is twelve in a row, and `בעיא` covers
    81, 85–87, 89–95. That much I could answer from the data.

    **What I could not, and what the reviewer supplied, is that the stored
    heading for those klalim is WRONG AT THE OTHER END.** The printed heading is
    the single word `בעיא`; klal 92 stores 24 words, klal 90 stores 16. Klal 96
    is the counter-example that kills any mechanical rule: its heading is three
    words, `בעיו דסמיכי אהדדי`, not one. Item 39 (iv) said length is not the
    signal and only the printed type size decides; this is that, confirmed by a
    reader.

    **I HAD SHIPPED THE APPLY PATH WITH NOTHING ABLE TO CALL IT.** Item `0AY`
    built the `title_correction` type, the apply, the invariant and the report —
    and no endpoint and no control, so the answer to "how can i / you correct?"
    was *neither of us can*. Lesson 29, committed the same day the lesson's own
    file was edited: a capability nothing on screen reaches was not delivered.

    **`POST /api/decisions/title` and a `✎ Heading` button on every klal.** The
    panel leads with the heading AS ONE FIELD, because that is the shape the
    extent fix takes; clicking a word cuts the heading there and fills the box
    (nothing is recorded until Save), clicking it twice corrects that one word
    instead. It is a separate control from the text pane's heading words on
    purpose: those are the BODY's reprint and carry body indices.

    **Whole-field rulings are addressed at `(klal, 0)` — the reviewer's "same for
    title - klal+0", and the reason is arithmetic.** An extent fix removes a RUN
    of words, and every deletion shifts the indices after it, so the apply's
    one-word-count-change-per-klal-per-run limit would turn klal 92's trim into
    **23 apply/rebuild cycles**. As one ruling naming the field it is atomic, and
    its drift check is the ENTIRE stored heading rather than one word — if the
    heading moved at all since the ruling, it describes a heading that no longer
    exists and is skipped. Three tests: it replaces the field, it refuses on
    drift, it never applies twice.

    **The queue: 101 headings**, written into `title_defect_report.json` by stage
    4c. It is klalim in a shared-first-word run whose stored heading is ≥4 words,
    longest first — **explicitly a work queue and not a detector**, since the
    same measurement that motivates it (mean 5.8 words, p90 11, max 24) is the
    one proving length cannot decide. Klal 92 (24w) and klal 90 (16w) lead it.

    **Two live rulings landed from the dashboard while this was being built**,
    and one of them is the answer to item `0AY`'s open question: klal 92 w7
    `נסקי` → `נפקי`, the title-detector candidate whose body carried the same
    form. The other, klal 96 w1 `בעיו` → `בעיי`, is the first record to carry the
    `word_occurrence` field from item `0BB`.

    Full suite green: gate 389, UI 84 passed / 1 skipped.

0BD. **[2026-09-03, reviewer] I PUT THE HEADING PANEL'S CSS IN A FILE NOTHING
    LOADS — a file that did not exist until I created it. Fixed. And the answer
    to "what happens to the words orphaned?": nothing, now gated.**

    Reviewer: *"need a space after the word before the num in the heading
    corrector selector. what happens to the words orphaned?"*

    **The missing space was not a spacing bug.** I appended the panel's rules to
    `review_frontend/style.css`. `index.html` links **`app.css`**, and `style.css`
    did not exist in this repo until my own commit created it with `cat >>` —
    so every rule was inert and the chips rendered as bare buttons with the index
    touching the Hebrew. The file is deleted and the rules are in `app.css`, with
    both cache versions bumped to `v=15`.

    Lesson 29 again, and worth recording as the third instance in two days: the
    apply path shipped with nothing able to call it (item `0BC`), and now its
    styling shipped into a stylesheet nobody serves. **`>>` on a path that does
    not exist creates it silently, which is the whole mechanism** — the same
    shape as writing a JSON field nothing renders. The check that would have
    caught it in one second is `grep stylesheet index.html`.

    The separator is real spacing (`margin-inline-start` + a rule) rather than a
    flex `gap`: the chip row is RTL, so the index sits at the word's left, and at
    the sizes this renders at a gap alone left them touching.

    **NOTHING IS ORPHANED, and the reason is structural rather than careful
    coding.** `title` is not where those words live — it is a SECOND COPY of the
    klal's opening words, and `clean_text` holds them too. Measured: **220 of 222
    Part 1 headings are an exact word-for-word prefix of their own body**, the two
    exceptions being klalim 9 and 186, already baselined, where the body still
    carries the word and differs by a glued stop and a geresh. Klal 92 checked
    end to end: all 24 heading words are a body prefix, so trimming to `בעיא`
    removes 23 words from the `title` field and leaves `clean_text` at 539 words,
    untouched. The trim moves where the heading is DECLARED to end. It deletes no
    text.

    **Gated, because that is a property of the data and could stop being true.**
    `test_trimming_a_heading_cannot_orphan_text` asserts the body CONTAINS the
    heading — deliberately a different question from
    `test_every_title_is_a_prefix_of_its_own_body`, which asks whether the two
    AGREE. The day a heading holds a word its body does not, trimming it would
    genuinely delete that word, and this fails rather than letting it go
    silently.

    Full suite **479 passed, 1 skipped**.

0BE. **[2026-09-03, reviewer] THE HEADING CHIPS WERE BLACK ON BLACK, AND A SAVE
    THAT WORKED LOOKED LIKE A SAVE THAT DID NOTHING — the reviewer recorded klal
    89 twice. Both fixed, both gated.**

    Reviewer: *"individ words are black on black. clicked save heading nothing
    changed"*.

    **BLACK ON BLACK — I wrote a second copy of the theme.** The chips hardcoded
    `background: #262b34` with `color: inherit`, and this app is LIGHT: `--ink`
    is `#1a202c` on `--paper #ffffff`. Dark text on a dark chip. The tell was in
    the same block — `var(--rule, #3a3f4b)`, and **`--rule` is not a token in
    this file at all**, so every one of those fell through to its dark literal.
    Rewritten on `--wash`/`--line`/`--ink`/`--accent`/`--accent-wash`, the same
    tokens `.disputed-option` already uses. Lesson 13 in CSS: a block that
    invents its own palette agrees with the real theme until it doesn't.

    **"NOTHING CHANGED" — the save had worked, and nothing said so.** Two
    `title_correction` rows for klal 89 are in the ledger, identical, 31 minutes
    apart. Recording and applying are separate steps here, so `title` correctly
    still read as stored — but **every other decision in this app shows a
    pending state and this one showed none**, which makes a working save
    indistinguishable from a broken one. That is the failure, not the duplicate.

    Fixed in three places, because the button and the panel are fed by different
    endpoints:

    - `/api/klalim` serves `title_pending` — it had to be THERE, not just on
      `/api/klal`, because the klal header is built from the nav payload. This
      file already carries a comment recording that exact trap, from the time an
      `ai_flag` count was added to `/api/klal` and never rendered because the
      header never sees that response. Loaded once for all 222 klalim, not per
      klal.
    - `/api/klal` serves `title_decision` — what is on record, `applied`, and
      `stale` (a whole-heading ruling drift-checks the ENTIRE stored title, so a
      reviewer needs to see when the heading has moved under it).
    - The button reads `✎ Heading · pending` in the pending colour, the panel
      opens with a "Recorded, not yet applied" note naming the recorded text, and
      a save re-marks the button without refetching the nav.

    **Three gated tests, each one proven to fail before being kept** (Lesson 25 —
    I ran each against a synthetic input that must trip it):

    - **stylesheets, BOTH directions.** Every `<link>` resolves to a real file,
      AND every `.css` in `review_frontend/` is linked. The second direction is
      the one that mattered: item `0BD`'s inert `style.css` would have passed a
      one-way check.
    - **the heading block uses no undefined CSS variable** — `--rule` would have
      failed this on the day it was written.
    - **the heading block hardcodes no colour** except one named exception, the
      pending wash, which has no token.

    Full suite **481 passed, 1 skipped**.

0BF. **[2026-09-03] THE HEADINGS ARE APPLIED — klalim 89 and 90 now read
    `בעיא.` — and applying them exposed a coupling nobody had needed to think
    about: a body correction inside the heading run silently desynchronised
    `title`. Fixed at all three write sites, with two guards each found by a
    test rather than by reasoning.**

    Reviewer: *"the text didn't change, I just see heading pending"*. Correct and
    by design — recording and applying are separate steps — so the apply ran.

    **7 promoted:** klal 89 and 90 headings trimmed to `בעיא.` (from 11 and 16
    words), klal 92 w7 `נסקי`→`נפקי`, klal 96 w1 `בעיו`→`בעיי`, one more manual
    and two confirmed-no-ops. **The orphaning guarantee held exactly as item
    `0BD` predicted**: klal 89's body stayed 56 words, klal 90's 25 — the trims
    removed 26 words from `title` and none from the corpus.

    **THEN THE GATE WENT RED, and it was right.** `title` is a SECOND COPY of a
    klal's opening words, so correcting klal 92 w7 and klal 96 w1 in the body
    left the heading holding the old spelling — the corpus briefly carried two
    spellings of one printed word. Nobody had had to think about this before,
    because until this morning nothing in this pipeline could write `title` at
    all. Lesson 35 exactly: when a step writes to the source of truth, enumerate
    what else describes that truth and update it in the same breath.

    **`sync_heading_word()` carries a body correction into the heading, and it is
    wired at ALL THREE `clean_text` write sites** — the machine `replace`, the
    machine insert/delete, and the manual path — per Lesson 34, which is about
    exactly this: a mutator with three branches, fixed one branch at a time,
    firing again from the next one. The two word-count-changing paths cannot map
    an index safely, so they REPORT rather than guess, and the gated prefix
    invariant is the backstop.

    It is not a new adjudication and needs no ruling of its own: the reviewer
    already decided the word against the ink and the heading is the same printed
    word. A machine deciding a word on its own would be item `0AT`'s defect;
    completing the human's is not.

    **Two guards, and I got both wrong first — each was caught by a test, not by
    thinking about it.**

    - **It propagated body PUNCTUATION into a heading.** The one-time repair
      duly turned klal 9's title into `איידי. אפשר דאמרינן ...`, a period
      mid-heading, because klal 9's body carries a stop glued to `איידי` — one
      of only two such words in Part 1 and a recorded data issue in its own
      right. Reverted by hand, then guarded. Measured: 222 of 222 headings end
      in a period, 0 have one elsewhere.
    - **Then the guard was too strict in the other direction.** Refusing on any
      period meant a correction to the LAST heading word never propagated — and
      that word is exactly where every heading's own terminal period lives, so
      the two never compare equal. The prefix invariant, which strips that
      period before comparing, would then fail on it. Both directions are now
      handled and both are pinned by tests.

    Five tests in all: the sync fires inside the heading run; refuses where the
    two already diverge on purpose (klalim 9 and 186 survive a correction
    elsewhere); refuses body punctuation; handles the terminal period in both
    directions; ignores a correction outside the heading run.

    **State:** `title_defect_report.json`'s extent queue is down to 99 from 101.
    Klalim 91, 92 and 94 carry heading rulings recorded and not yet applied.
    Full suite **486 passed, 1 skipped**.

0AW. **[2026-09-03] WHY `הרל"ם → הרמב"ם` WAS PROPOSED: an abbreviation naming a
    DIFFERENT authority is indistinguishable, to every detector here, from a
    misprint of a commoner one. Reviewer ruled KEEP from the ink. 11 more
    abbreviation-change flags are open; none is this shape.**

    Reviewer: *"i don't know why the suggestion was made... the scan is clear,
    rlm means the rav lechem mishnah."* `הרל"ם` = הרב לחם משנה, R. Abraham de
    Boton's commentary — a real, distinct authority, and the citation reads
    `עיין הרל"ם בפרק א' מהלכות`, which is the idiomatic way to cite a commentary
    ON the Mishneh Torah. The stored text was right.

    **The mechanism.** The note's `INTRA` class is intra-klal consistency: klal
    12 writes `הרמב"ם` at w250, and w192 is a near-neighbour string that occurs
    once. Every arbiter in this repo would make the same call, because an
    abbreviation defeats all three of them at once — it is SHORT (so edit
    distance to a commoner abbreviation is 1-2 letters), it is RARE as a string
    (so a frequency test reads "unattested"), and its expansion is not in the
    text (so nothing can tell that `הרל"ם` and `הרמב"ם` name two different men,
    both of whom are cited on `הלכות`). A consistency heuristic cannot separate
    *one authority written two ways* from *two authorities cited in one klal*.
    This is item 31's prefix false-positive class in a second grammar, and item
    22's point that `lexicon.txt` cannot help here (it learned this corpus's own
    OCR).

    **I was wrong about the four rulings, and the correction matters** because I
    used them as evidence. Klal 12's five manual corrections did NOT come from
    one report: w74 and w192 are `INTRA`, w237 is `FREQ`, w110 is the lexicon-gap
    detector re-run, w160 is the 2026-08-17 retroactive-highlighting backfill.
    Four separate passes landing in one klal is what "sibling rulings" looked
    like from the ledger, and the inference I drew from it — that a keep was
    anomalous among them — had no basis.

    **Swept the class, per the standing rule.** 296 rulings in the ledger carry a
    `X wN → Y | CLASS:` proposal note (FREQ 161, HAPAX-ABSENT 63, INTRA 47, GRAM
    17, FRAGMENT 6, HAPAX-RARE 2); **no script in this repo writes that format**,
    so the pass that produced them was external and its rationale survives only
    in these notes. 31 of the 296 target a gershayim abbreviation, 30 of those
    propose another abbreviation, and 4 of the 30 propose a string IDENTICAL to
    the original — those are the U+05F4-vs-ASCII normalisation of item 57, not
    letter changes.

    **11 abbreviation-change flags are still open**, and every one is a
    letter-confusion repair of a form that is not a word in any reading
    (`ב"ט`→`ב"מ`, `ע"ר`→`ע"ד`, `הנלע"ר`→`הנלע"ד`, `זה"ה`→`וה"ה`, `למ"ר`→`למ"ד`,
    `אע"ס`→`אע"פ`, `עכ"ר`→`עכ"ל`, `והכ"ם`/`בכ"ם`→`מ`, `פ"יא`→`פי"א`,
    `נלפ"קד`→`נלפק"ד` — klalim 37 ×2, 45, 92, 116, 140, 161, 176 ×2, 212, 216).
    **None has the הרל"ם shape**, where the ORIGINAL is itself a valid distinct
    abbreviation. So the exposure this found is one position, already ruled — but
    the blind spot is structural and will fire again on any book citing two
    authorities whose abbreviations are near-neighbours, which is most of
    rabbinic literature. **The cheap mitigation is a stop-list of attested
    work/authority abbreviations that suppresses a proposal to REWRITE one into
    another; it is not built, and per Lesson 31 it should not be bolted onto the
    external pass that is no longer in this repo.**

0AV. **[2026-09-03] STATUS SWEEP: the suite is green at 459, `START_HERE.md`'s
    test counts were stale by five sessions, and 58 recorded rulings are sitting
    unapplied — 8 of them item `0AQ`'s Dicta escalations.**

    Nothing was changed in the corpus. Everything below is measured today, from
    the runner and from the dry run, not quoted from this file.

    **The suite.** `pytest --collect-only -q` reports **459**; the whole suite is
    **458 passed, 1 skipped** (gate 369 passed in 18s; the ungated UI + witness
    pair 89 passed / 1 skipped in 3m28s). Per file, from the collector per
    Lesson 37: invariants 50, logic 319, review_server 85, witness_engine 5.

    **`START_HERE.md` was carrying the 2026-08-31 figures** — 46/274 gated
    (320) and 369 total — which had been overtaken by five sessions of new
    tests. Corrected in place, with the superseded numbers kept in the sentence
    so the drift stays legible. The doc's own rule is that it holds durable
    architecture while this file holds dated truth; a hard-coded count is
    neither, and it will go stale again the next time a lesson earns a test.

    **58 decisions are recorded and not promoted** (`apply_reviewer_decisions.py
    --dry-run`): 11 replace, 2 insert, 16 manual, 29 confirmed-no-op, against
    453 already applied. That backlog includes **all 8 of item `0AQ`'s Dicta
    escalations** (59 w47, 74 w203, 77 w22, 77 w24, 88 w963, 91 w191, 92 w326,
    124 w26), which `0AQ` names as its next action. Applying them is a separate,
    deliberate step and has not been taken.

    **Live queue, from `/api/klalim` rather than from any prose here:** 892
    flagged positions in Part 1 = 105 decided + 210 machine-resolved + 577
    machine-disputed; 504 recorded rulings; 146 klalim with something open; 107
    carrying a revisit pennant; 66 of 67 punctuation candidates open; 222/222
    pages trusted.

    **One ruling worth a second look, not a finding.** The uncommitted ledger
    line — klal 12 w192, recorded 05:08 today — has `chosen_text` equal to
    `original_word` (`הרל"ם`), while its note carries the proposal
    `הרל"ם → הרמב"ם`. Swept the class: **6 no-op `manual_correction`s whose note
    names a concrete different word**, and the four older ones are legitimate
    "keep the stored text" rulings (klal 210 w68 was independently confirmed
    correct in item `1A`). So the shape is normal reviewer behaviour and this is
    most likely a deliberate rejection of the proposal — but the four sibling
    rulings in klal 12 from the same report all recorded the CHANGE, so it is
    worth confirming it was meant as a keep before it is applied as one.

0AU. **[2026-09-03] A GAP STOLE THE SCAN HIGHLIGHT FROM THE WORD SHARING ITS
    INDEX — 40 positions across 35 klalim. FIXED. And the legend's swatches now
    show the mark the text pane actually draws.**

    Reviewer: "clicking on Klal 17 (יז) · Word #308 — בסתם highlights the wrong
    word."

    A `delete`-opcode entry is a GAP: text the scan HAS and the corpus lacks,
    addressed by the index it would be inserted BEFORE. It therefore shares that
    index with the word standing there while its bbox points at different ink —
    klal 17 w308 is `בסתם` at x=0.62, and the omission sharing its index sits at
    **x=0.86**. Two faults compounded:

    - **`api_page` let the gap's key SUPPRESS the word.** Its `served_keys` guard
      treats any entry at (klal, word_index) as covering that word, so the word
      was never emitted at all and the only box on offer was the gap's.
    - **`app.js` matched focus on `word_index` alone**, so even once both are
      served the gap could take the focus.

    The alignment was never wrong — w308's box sits exactly on the DocAI token
    `בסתם`, distance 0.0 — which is worth recording, because "the highlight is on
    the wrong word" reads like an alignment fault and is not one here.

    Fixed on both sides: `served_keys` ignores `delete` entries, and the focus
    test requires gap-ness to match between the clicked thing and the candidate
    entry. The gap stays reachable in its own right — `renderKlalBody` draws a
    marker for it, and clicking THAT passes the gap as the focus.

    `test_no_word_index_is_served_twice_in_either_pane` had to be widened: its
    scan half counted a gap and a word at one index as a duplicate, which is how
    the wrong box passed as the right one. It now excludes `delete` entries from
    that count exactly as its TEXT half already did, and separately asserts that
    no two GAPS share a key — the one case the focus test genuinely cannot
    disambiguate.

    **The legend swatches.** Reviewer: "why are the purple words shown in the
    count with a purple underline but all the others are shown as boxes? in the
    scan page they are all boxes and in the text page they are all lines." The
    legend was inconsistent with ITSELF — three box-ish chips and one underline —
    and matched neither pane. It cannot mirror both, so it mirrors the TEXT pane,
    where the LINE STYLE carries meaning colour alone does not: solid = the
    vision pipeline ruled, dotted = the machine settled it, dashed = an automated
    pass flagged it on textual reasoning with no vision confirmation. Each swatch
    is now drawn with the same border as its `.flag-word.state-*` rule, a test
    asserts the two against each other so they cannot drift, and the row tooltips
    say the scan pane boxes the same colours.

    **And the footer stopped wrapping** (reviewer: "count footer is a bit too
    wide, wraps to anothe line"). It needed 394px in a 347px pane, so it took two
    lines — and it is pinned over the index pane's own bottom corner, where a
    second line eats another row of klalim. The width came from five entries each
    carrying a swatch, a gap and a fixed-width count, so it was trimmed across
    all of those rather than by dropping an entry: 336px in 347 now, one line,
    36px tall against 65. A test asserts the geometry — one row, no wrap — rather
    than any of the particular sizes, since any of them may move again.

    Full suite **459 collected, 458 passed, 1 skipped**.

0AT. **[2026-09-02] 131 CORRECTIONS ENTERED THE CORPUS THAT NO HUMAN EVER
    ADJUDICATED, and the dashboard has been drawing them GREEN as "Human-Decided"
    the whole time. OPEN — the corrections need eyes; the display is fixed.**

    Reviewer, having changed all 8 of item `0AQ`'s positions against the ink:
    *"there is no al-la lig on those last two — the lamed should never have been
    there. I see a prev. pass flagged it to add the lamed based on pattern
    matching — but did a human (me) adjudicate it? it wasn't marked in yellow or
    red."*

    **It did not.** Klal 92 w326 and klal 124 w26 both carry
    `reviewer: 'ai-dropped-lamed-correction'`, written in the same microsecond by
    a script. They are `manual_correction` records — the type this dashboard
    renders GREEN as Human-Decided — so they entered the corpus already looking
    settled and never appeared in any review queue. That is exactly why they were
    never yellow or red.

    | | |
    |---|---:|
    | rulings in the ledger written by a PERSON (`local`/`user`) | 905 |
    | **rulings written by a script** (`ai-*`, `tools/*`) | **1,615** |
    | of the 503 the dashboard counts as recorded, machine-written | 102 |
    | the `ai-dropped-lamed-correction` pass: records / klalim / applied | 131 / 51 / **131** |

    **The pass cannot tell a defect from a real word, and 66 of its 131 replaced
    an attested one.** Judged against the independent 6.18M-word reference corpus
    (NOT `lexicon.txt`, which is built from this corpus and so has already lost
    any word the pass corrected away — Lesson 3): `או` → `אלו` fired on a word
    attested 19,452 times, `א` → `אל` on one attested 17,870 times, `איה` → `אליה`
    on one attested 78 times. **Attestation alone does not prove any single one
    wrong** — `אא` → `אלא` is very likely a genuine ligature repair in context —
    but it does prove the rule was operating on strings with no way to tell the
    two apart, and nobody checked.

    **The reviewer has now confirmed two of them wrong from the ink** (klal 92
    w326, klal 124 w26: the lamed should never have been added). The other 64
    attested-original cases are unaudited and are the queue this creates.

    **Lesson 24 needs re-reading in this light.** It cites the alef-lamed
    ligature as the case where architectural independence fails because every
    engine reads the same defective sort. That is still true where the ligature
    IS present — but this pass ADDED lameds where there was no ligature at all,
    and the engines reading `איה` were reading the ink correctly.

    **FIXED in the display:** every recorded ruling now serves its `reviewer` and
    a `by_human` flag, the recorded list marks machine-written rulings with a cog
    and a `by a script` filter chip, and each row's tooltip names who wrote it.
    A human ruling and a script's are no longer indistinguishable on screen.

    **THE FLAGS THE PASS PROMISED WERE NEVER WRITTEN.** Its note ends *"Flagging
    for human review per user instruction (apply the mechanically-confirmed
    corrections, flag every one)"* — and **114 of the 131 carry no flag at all**.
    (Of the 17 that do, 16 were raised later by the reviewer independently and 1
    by a different AI pass; none came from this one.) Lesson 19 exactly:
    describing a step in writing is not performing it. That is the whole reason
    these were invisible — applied, drawn green, never queued.

    **RESOLVED 2026-09-02/03, in three parts.**

    - **`append_decision` now REFUSES a machine-written `manual_correction`**
      (reviewer: "manual correction was the wrong flag for an automated change
      where the note says it should be reviewed"). That type means A PERSON
      RULED; an automated pass that wants a human to look raises a `klal_flag`,
      which is what a queue is made of. It refuses rather than warns — a warning
      in a batch script's output is a warning nobody reads.
    - **`tools/flag_unreviewed_auto_corrections.py` (new) raised the 87** that
      were unflagged and whose recorded position still holds the corrected word.
      27 more had drifted and were skipped rather than guessed at; 3 were
      withdrawn again because the word has no scan position, and a flag saying
      "check this against the scan" that cannot take you there is a dead end the
      gated invariant forbids. No corpus text was changed and no correction was
      reversed. The open queue went 498 → 579, the pennant count 94 → 108.
    - **A rule divergence surfaced by those flags, and fixed.**
      `review_counts.word_states()` refused to let an open flag override a
      DECIDED word, while `app.js`'s `wordState()` has always tested
      `word_flag && !answered` BEFORE `current_decision`. The guard contradicted
      its own comment — `flag_still_open()` has already removed every answered
      flag, so anything reaching that loop is unanswered — and it had simply
      never fired, because until now no word carried both. Klalim 92 and 124, the
      pair the reviewer had just corrected, were the first two. The screen is the
      ground truth, so the count follows it.

      Two logic tests were pinning the old behaviour, and both were doing it
      through fixtures with NO TIMESTAMPS — so the answered-by-a-later-decision
      comparison was `"" > ""`, always false, and every fixture flag read as
      unanswered. They now carry timestamps and assert the ordering rule itself.

    **STILL NOT FIXED: the 64 corrections whose original was an attested word.**
    They are now in the queue, with the `by a script` filter to walk them.

0AS. **[2026-09-02] A WORD WITH NO OCR ALIGNMENT OPENED THE KLAL'S FIRST PAGE
    INSTEAD OF ITS OWN — 746 words across 55 multi-page klalim. FIXED, and the
    remaining un-placeable ones now SAY so.**

    Reported on the first link from item `0AQ`: "the scan shows the wrong page,
    the klal extends over two and that word is on the following page. and it
    doesnt zoom in." Klal 88 w963: `word_pages["963"]` is **None** — DocAI never
    matched that word — so the lookup fell straight through to the klal's start
    page, 39, while the word is on 40. **Both symptoms were one cause:** wrong
    page, so no box on it, so nothing to zoom to.

    **1,649 of Part 1's 52,630 words have no aligned token at all; 746 of those
    are in a klal that spans pages**, where the start-page fallback is a guess and
    usually the wrong one (klal 88 puts 283 words on page 39 and 840 on page 40).
    Words are in reading order, so the nearest ALIGNED neighbour is a far better
    answer, and that is what `pageForWord()` now walks out to.

    **The first fix changed nothing, and the reason is this file's most-repeated
    defect.** THREE click handlers — editorial mark, manual, plain word — each
    carried their own copy of `word_pages[i] ?? k.page`, and only the shared
    `pageForWord()` was corrected. The deep link dispatches the word's own click
    (item 0AK), so it went through a copy. All three now call the one function,
    and a gated test asserts no fourth copy appears: `word_pages[i]` must not
    occur outside it.

    **Words that cannot be placed AT ALL now say so.** Some have no alignment
    anywhere, so even the right page has no box and nothing to zoom to, and the
    pane simply sat there looking broken — which is how this was reported. The
    warning is deferred 900ms and cancellable, because routing calls `showPage()`
    several times and the earlier ones legitimately find no box yet; announcing
    on the first miss fired it on klal 88 w963, which DOES get a box a moment
    later. Verified on four cases: warn / no-warn / warn / no-warn.

    Two of my own measurement errors along the way, both caught before they
    became "findings": the toast looked broken because I polled at 2200ms and it
    auto-hides at 1800, and then looked broken again because the PREVIOUS case's
    toast was still on screen when the next case started polling.

    Full suite **454 collected, 453 passed, 1 skipped**.

0AQ. **[2026-09-02] THE 8 POSITIONS WHERE DICTA'S CONSENSUS CONTRADICTS A HUMAN
    RULING, itemised. TWO OF THEM LOOK LIKE THE CORPUS CARRYING AN EDITORIAL
    EXPANSION AS IF IT WERE THE AUTHOR'S TEXT. OPEN.**

    The Dicta preview reports these only as a count. Itemised at the reviewer's
    request; nothing has been changed.

    | klal · word | corpus | engines read | agreeing | ruled |
    |---|---|---|---|---|
    | 59 · 47 | כוותיה | כוותה | dicta+surya+vlm | 08-30, `lexical_proposal` |
    | 74 · 203 | דגם | הגם | dicta+surya+vlm | 08-31, confirmed the stored text |
    | 77 · 22 | וטומאות | וטמאות | dicta+surya | 08-31, manual |
    | 77 · 24 | טומאות | טמאות | dicta+surya+vlm | 08-31, manual |
    | **88 · 963** | ומתיר | **ומתי׳** | dicta+surya+vlm | 08-25, manual, *"LOW confidence"* |
    | **91 · 191** | העניינים | **העניני׳** | dicta+surya+vlm | 08-24, manual |
    | 92 · 326 | אליה | איה | dicta+surya+vlm | 08-15, ligature repair |
    | 124 · 26 | אליה | איה | dicta+surya+vlm | 08-15, ligature repair |

    **The two that matter (88 w963, 91 w191): three independent engines read a
    printed ABBREVIATION with a geresh — `ומתי׳`, `העניני׳` — and the human
    expanded it to a full word.** That cuts directly against success criterion #1
    ("no paraphrase, no silent normalization"); klal 88's own note says LOW
    confidence. If the ink shows an abbreviation, the corpus is carrying an
    editorial expansion presented as the author's text. **Klal 77 w22/24 are the
    same shape in spelling** — engines read defective (`טמאות`), corpus has plene
    (`טומאות`), two adjacent words ruled by the same reviewer in the same minute.

    **Klal 74 is settled** (the reviewer explicitly confirmed the stored text)
    and **92/124 are the known alef-lamed ligature** — engines share the misread,
    the human is right. But note a wrinkle worth chasing: **Lesson 24's premise
    is that every engine reads the same ink, and Dicta does not** — it reads the
    Jerusalem 1975/6 edition, not the Berlin scan. Either that printing sets the
    same ligature or Dicta's agreement has another cause; Lesson 24 is
    load-bearing and it is worth knowing which.

    **ALL 8 WERE RULED BY THE REVIEWER, 2026-09-02, AGAINST THE INK — and every
    one went the engines' way.** `reviewer: local` on all eight, and in each case
    the chosen text is the reading the engines gave:

    | | corpus still holds | reviewer chose |
    |---|---|---|
    | 59 · 47 | כוותיה | כוותה |
    | 74 · 203 | דגם | הגם |
    | 77 · 22 | וטומאות | וטמאות |
    | 77 · 24 | טומאות | טמאות |
    | 88 · 963 | ומתיר | **ומתי׳** |
    | 91 · 191 | העניינים | **העניני׳** |
    | 92 · 326 | אליה | **איה** |
    | 124 · 26 | אליה | **איה** |

    So the abbreviation-expansion reading above is confirmed: the ink shows
    `ומתי׳` and `העניני׳`, and the corpus was carrying an editorial expansion.
    And the reviewer's verdict on the last two — *"there is no al-la lig on those
    last two, the lamed should never have been there"* — is what opened item
    `0AT`.

    **NONE OF THE EIGHT IS APPLIED YET.** Recording and promoting are separate
    steps; `apply_reviewer_decisions.py` has not been run for them, so
    `part1.json` still holds the old readings. That is the next action on this
    item. The Dicta preview's escalation count consequently reads **1**, not 8 —
    the survivor is klal 210 w73 (`כבתרייתא` vs `בתרייתא`), which surfaced after
    the `0AP` re-points; the "8" in the Dicta section above is the pre-ruling
    figure and is left as the record of what was found.

    **DocAI cannot arbitrate any of the four contested ones.** All four fall
    inside NON-MATCHING alignment blocks, so the primary OCR of the Berlin scan
    has no placeable reading there. That is not a clean bill of health — it is
    Lesson 15's flag (silence exactly where the sources are too divergent to
    align), and the clustering is itself consistent with the corpus having moved
    away from the ink. These need the scan; the dashboard links are
    `/klal/88/word/963` and `/klal/91/word/191`.

0AR. **[2026-09-02] HOW TO MAKE THE TEST SUITE BOOK-INDEPENDENT — the measured
    plan. NOT STARTED.**

    Reviewer: "I want to test the code not the material because this will be a
    general purpose util." Measured where the coupling actually is:

    | suite | tests | reads the real corpus | pins a klal id |
    |---|---:|---:|---:|
    | `test_pipeline_logic.py` | 316 | 4 | — |
    | `test_witness_engine.py` | 5 | 0 | — |
    | `test_corpus_invariants.py` | 50 | **30** | 0 |
    | `test_review_server.py` | 67 | **62** | **23** |

    **Three tiers wear one name, and that reframing is most of the answer.**
    The engine tests (321) are already book-independent by construction. The ~30
    corpus invariants are **not tests at all for a general-purpose tool** — they
    assert that *this book's data* is well-formed, and belong behind a
    `validate <book>` command; today a corpus REPAIR can turn the suite red,
    which is backwards. Only the ~67 behaviour tests are the real problem.

    **One structural blocker.** `corpus_io.REPO` is `dirname(dirname(__file__))`
    and ~35 constants derive from it, so the corpus location is a function of
    where the source file lives. There is exactly ONE env seam in the whole data
    layer (`REVIEW_DECISIONS_PATH`), added for this same reason. **The
    test-independence problem and the general-purpose problem are the same
    problem**: a tool that cannot be pointed at another book at runtime cannot be
    pointed at a fixture either. Add `SEFER_CORPUS_ROOT` + `--corpus`, honoured
    by `repo_path()`, and both fall out. Resolution must be at CALL time — those
    constants are evaluated at import, and reassigning afterwards silently does
    nothing, the bug `review_decisions._resolve()` exists to document.

    **The fixture corpus must be GENERATED, not written** (Lesson 13): a script
    that emits a tiny `part1.json` + a small PDF via `fitz`, then runs the real
    rebuild stages against it. It needs one of each condition the UI branches on:
    a klal spanning a page break; both machine-resolved flags; a human decision;
    an answered flag standing alone; a word-level `ai_flag`; witness rows with
    and without a `word_index`; a `possible_omission` at `len(words)`; two
    `delete` opcodes at one index; a punctuation candidate; an editorial mark; a
    title with a terminal period; a word whose page ≠ its klal's start page; and
    two identical adjacent words. The last two are exactly the conditions behind
    this week's real bugs (the dead deep-link branch, and the klal 68 deletion).

    **And one gated guard, or it decays**: assert that no test outside the
    validator module resolves a path under the real corpus root.

    Order: the seam (no test changes, independently useful) → fixture generator
    plus a `conftest.py` (there is none today) → move the 23 pinned UI tests →
    split the invariants → add the guard. Honest risk: a fixture is a second
    corpus, and if it drifts from real shapes the tests pass against a book that
    does not exist — mitigated by generating it and keeping a few real-corpus
    smoke tests.

0AP. **[2026-09-02] 40 STALE ADDRESSES RE-POINTED FROM THE INK; the ledger
    learned to say "superseded"; and yesterday's MAX_EXPLAINABLE_SHIFT was WRONG
    about the very case it was written for.**

    Reviewer, on item 0AB: "looking at the first two in klal 1 I see the
    corrected word earlier in the klal — can we recover them all?"

    **No, but 40 of 105.** `tools/repoint_stale_decisions.py` (new) re-points a
    ruling only when TWO independent signals agree: the snapshot BBOX mapped onto
    whichever word occupies that place on the scan now, and the TEXT searched for
    the ruling's chosen or original word. Where only one is available, or the two
    disagree, it refuses. Stale addresses **105 → 77**; the remaining 97 rulings
    are 18 bbox-only, 27 text-only, 3 conflicting, 31 ambiguous, 18 with no
    evidence left, and they sit under the recorded list's `stale address` chip.

    **A unique text match was deliberately not accepted as sufficient**, and that
    is measured, not cautious: the text-only candidates imply shifts of −108 and
    −107, the exact shape of the false relocation that MAX_EXPLAINABLE_SHIFT was
    added to catch.

    **`supersedes` — the ledger's new primitive.** An append-only log cannot
    correct a record, which is its point, but it needs to say "that one is no
    longer the answer". Without it a re-pointed ruling appears BESIDE its own
    stale predecessor, because the original is still the newest record at the old
    key: measured, the stale count moved 105 → 102 without it and 105 → 77 with
    it. Nothing is edited or removed — the original reads back verbatim, and a
    gated test asserts exactly that. Deliberately NOT honoured by `all_current()`:
    a corpus-mutating consumer has its own drift check, and widening the meaning
    of "current" everywhere is a far larger blast radius than the display problem
    it solves. The re-point tool skips already-superseded rulings, so a second run
    finds nothing and writes nothing.

    **I WAS WRONG YESTERDAY, and the better evidence is the ink.**
    `MAX_EXPLAINABLE_SHIFT = 5` (item 0AJ) was derived from shift MAGNITUDE
    alone, and it misjudged the one case it was written for: mapping klal 10's
    snapshot bbox onto the current alignment shows `כתבו` really is at w74 — the
    ink and the letters agree at a shift of −11, so that ruling was HONOURED, not
    lost. Genuine bbox-corroborated shifts reach −31. The magnitude bound is now
    the FALLBACK, used only where no scan position was recorded; where a bbox
    exists it decides. `audit_applied_decisions.py` goes **2 MISMATCH → 1**, and
    the survivor is klal 1 w97, the hand-reverted punctuation case its own
    docstring names as its motivating example.

    **And the forward fix, so the class stops growing.** 55 of the 105 were
    `manual_correction`, which snapshotted `{word_index, original_word}` and
    nothing else — the structural reason half of them were unrecoverable from the
    ink. `api_post_manual_correction` now records the bbox and page too, from the
    geometry `_word_scan_position()` already computes for rendering; a word with
    no aligned DocAI token (1–4% of a klal) records `bbox_unavailable` rather
    than silently nothing.

    Full suite **451 collected, 450 passed, 1 skipped**.


0AO. **[2026-09-02, reviewer-requested] THE COUNT COLUMNS LINE UP, AND THE
    LEGEND EXPLAINS ITSELF.**

    - **Every nav row reserves all three badge slots, red leftmost.** A badge was
      omitted entirely at zero, so the red open count — the only one asking the
      reviewer for anything — sat at a different x on every row and the column
      could not be read down. All three slots are always present, one width,
      tabular figures; an empty one holds its space and draws nothing. Measured
      across 25 rows: one x per colour (red 1238, amber 1264, green 1290).

      The group is `direction: ltr` inside the RTL row, so DOM order IS
      left-to-right there — which is what lets "red written first" mean "red
      leftmost" without reversing anything.

    - **The legend counts line up the same way** (one width, tabular), and each
      now carries a real explanation on hover. The one-line layout hides the
      labels, so without them the bar is five unexplained numbers. The first
      version of these merely echoed the label and its own number back
      ("Machine-Disputed: 498. Machine-Disputed — 498 words…"); they now say what
      the state MEANS and what clicking does. The AI-Flagged tooltip also states
      the thing that most needs stating — that those words are ALSO counted in
      Machine-Disputed, because an open flag makes a word open whatever its own
      entry says — and the recorded row says it is the figure to quote for "how
      much has been reviewed".

    Two tests added, asserting the GEOMETRY (one x per colour across 25 rows,
    red < amber < green) rather than the markup, and that no tooltip is thin
    enough to be a label echo. Full suite **449 collected, 448 passed, 1 skipped**.

0AN. **[2026-09-02] THE INDEX PENNANT AND THE TEXT PANE ANSWERED DIFFERENT
    QUESTIONS WITH THE SAME WORD — 15 of 222 klalim. FIXED, along with four
    reviewer-requested trims.**

    Reported as "117 shows flagged in the middle pane but not in the index
    pane". Klal 117 turned out to be neither: its klal-level flag is clear and
    its one word-level flag at w43 is ANSWERED, so nothing is flagged — the
    button simply read `⚑ flag`, an affordance that scans as a status. It now
    says `⚑ Flag klal` when clear and `⚑ Flagged` when set.

    **The sweep found the real defect, in the mirror direction.** The index
    pennant means "anything in this klal is flagged", klal-level OR word-level;
    `api_klal`'s `needs_revisit` is the klal-level flag ALONE — which is correct,
    because the text pane's button toggles exactly that and would refuse to clear
    what it displayed otherwise. So the two panes disagreed on **15 of 222**
    klalim (17, 23, 71, 75, 81, 91, 138, 140, 151, 158, …), every one of them
    index-says-flagged / text-says-not. The text pane now shows an `⚑ N words`
    marker for the open word-level flags, so it EXPLAINS the pennant instead of
    contradicting it.

    **The first fix was itself a second encoding and did not even render.** I
    added `word_flags_open` to `/api/klal` — a fresh copy of a rule `api_klalim`
    already computes as `ai_flag_count`, and invisible anyway, because the klal
    heading is built from the NAV payload and never saw the field. Removed;
    the marker reads `ai_flag_count`, which is the same rule that builds the
    pennant, computed once. That field's name predates word-level flags being
    raised by anything other than an AI pass; the name is stale, the meaning is
    exactly "open word-level revisit flags".

    **Four trims, all reviewer-requested.**

    - The klal heading drops the section name (constant down the whole pane, and
      the header bar already names the work) and sets both numerals at one size —
      the same fact in two scripts, so sizing one above the other implied a
      hierarchy that is not there.
    - The flag pill sits WITH its heading. `margin-inline-start: auto` had been
      pushing it to the far end of a pane-wide row, ~490px from the heading it
      belongs to.
    - The nav shows only the red open count at rest; the resolved and decided
      badges appear on hover or on the active row. Three coloured pills per row
      made the column read as decoration and buried the one number asking for
      something. Two more klalim now fit on screen.
    - The legend is one 40px line instead of a 124px block of five rows.

    **One suggestion of mine was simply wrong and is withdrawn.** I had proposed
    defaulting the scan to fit-width; measured, it already IS — the page uses 94%
    of the viewer's width (the rest is padding) and its full height fits without
    scrolling. There was nothing to reclaim.

    Six tests added. Two initially SKIPPED against the fixture's empty ledger and
    were rewritten to create their own conditions — a test that skips is not a
    test. Full suite **447 collected, 446 passed, 1 skipped**.

0AM. **[2026-09-02, reviewer-requested] THE PANE HEADERS READ AS ONE CENTRED
    LINE OF PEERS — and the legend stopped letting the klal list show through it.**

    Reviewer: "center the header in each pane. move the titles a bit closer to
    the center and make them the same size and boldness - the hebrew is darker
    and bigger than the other hebrew in the header."

    Measured before changing anything: the Hebrew title was **16px / weight 700 /
    full-strength ink** against a Hebrew reference at **13.5px / 500 / muted**,
    and the two TITLES did not match each other either (9.5px uppercase English
    against an 11px reference). So the bar read as a heading with metadata
    trailing it. All four slots are now peers — one size per SCRIPT (13.5px
    Hebrew, 11.5px Latin, because the two do not have the same optical size at
    the same px), one weight, one colour — and the English title lost its
    uppercase/letter-spacing treatment, which reads as a LABEL and was the
    opposite of the intent.

    The slots also moved into a single group that centres as a unit, rather than
    bookending the bar with the reference stranded between them. The settings
    gear left the flow (`position: absolute`) because a control sitting in the
    row would push the centred text off-centre by half its width, in one pane
    only.

    **A separator bug, found by looking at the render.** The thin rule between
    slots was an `::before` with a logical `margin-inline-end` — and the Hebrew
    slots are `direction: rtl`, so the pseudo-element rendered at ITS start edge,
    the right, stacking two rules together beside the Latin slots and leaving a
    gap where one belonged. The flex ROW is laid out ltr regardless of each
    item's own text direction, so a physical `border-left` is the correct tool.
    (I also misread the first screenshot as showing the two Hebrew slots in the
    wrong ORDER; measuring their offsets showed 753 / 810 / 868 / 931, correct —
    the glyphs inside each box read RTL, which is what fooled the eye. Measured
    rather than "fixed".)

    **The legend was translucent.** `opacity: 0.95` applies to the background as
    well as the text, so the four nav rows sitting behind that fixed box ghosted
    through the counts — klal titles overprinting numbers, in the one place on
    screen that is nothing but numbers. Removed; if it ever wants to feel
    lighter that belongs in the background colour.

    Three tests added, asserting the RELATIONSHIP (every Hebrew slot matching
    every other, every Latin slot matching every other, each group centred to
    within 1px) rather than the particular sizes, which are a design choice that
    may move again. Full suite **444 collected, 443 passed, 1 skipped**.

0AL. **[2026-09-02] THE ZOOM LADDER COULD NOT REACH 100%, and a missing
    /api/corpus rendered as a blank space with nothing in the console. FIXED.**

    - **Zoom.** Reviewer: "zoom -+ goes directly from 95% to 120. 100 seems
      pretty basic." The buttons stepped `current ± 0.25`, and **the clamp is
      what broke it**: from 100%, three zoom-outs give 75 → 50 → **30**
      (clamped at the floor), and the way back up is 55 → 80 → 105. One clamp
      knocks the value off the quarter grid and every later step inherits the
      offset, so 100% — and every other round number — becomes unreachable. The
      ctrl+wheel's 0.15 steps do the same thing faster, which is how 95% happened.
      Replaced with fixed stops (0.3 / 0.5 / 0.75 / 1 / 1.25 / 1.5 / 2 / 2.5 / 3):
      the clamp is now harmless and 100% is always one walk away, including from
      an off-ladder value the wheel or the focus zoom left behind.

      **The related report did NOT reproduce.** "After clicking on a word it went
      back to normal" — measured: a manual 125% goes to 220% for the focus zoom
      and back to 125% on dismiss, repeatably. The focus zoom is deliberate and
      the restore works; if the complaint is that clicking a word changes the
      zoom AT ALL, that is a design question, not a bug, and worth saying so.

    - **Titles.** Reviewer: "remove more titles from the top bar. just show one
      in hebrew and one in eng in the center pane." Both now live in the centre
      pane only; the index and scan bars carry just their own reference. The
      four-slot order had put the work's name at both ends of all three bars —
      six repetitions of one fact, on a screen whose complaint was clutter.

    - **A missing /api/corpus was silent.** Reviewer: "when i sync this repo on
      another machine no titles render — is there code still needing to be
      committed and pushed?" **No: nothing was missing.** `WORK_TITLE`,
      `api_corpus()`, its route and the `data-slot` markup were all on
      origin/master. The cause is a `review_server.py` process **started before
      the endpoint existed** — Python loads the module once, so a synced-but-not-
      restarted server still answers 404.

      That should have been obvious from the console and was not, and that part
      is a defect I shipped: the fetch was
      `fetch('/api/corpus').then(r => r.json()).catch(() => null)` with **no
      `r.ok` check**, so a 404's JSON error body parsed cleanly, `CORPUS` became
      `{error: ...}`, every title rendered as an empty string, and
      `.ph-title:empty` hid it. A deployment problem became a blank space with
      nothing to diagnose — Lesson 26's shape, a filter that HIDES being more
      dangerous than one that rewrites. It now checks `r.ok` and logs the likely
      cause by name. **Restarting the dashboard on that machine is the fix.**

    Three tests added, including one that fulfils a 404 for `/api/corpus` and
    asserts the diagnostic appears AND the dashboard still works without it.
    Full suite **442 collected, 441 passed, 1 skipped**.

0AK. **[2026-09-02] THE SCAN PANE'S OVERLAY CONTROLS SCROLLED AWAY WITH THE
    PAGE — the zoom cluster since yesterday, the page arrows since they were
    added. FIXED. And a word URL now behaves like clicking that word.**

    Reviewer: "what happened to my zoom controls?"

    Both were children of `#scan-viewer`, **the element that scrolls** — and an
    absolutely-positioned child of a scroll container is positioned against the
    scrolled CONTENT, not the visible box. So they slid with the page. Measured
    at 300% zoom: at the top of the scan the zoom cluster sits at y=656, scrolled
    to the middle it is at **y=-388**, at the bottom **y=-777**. Gone.

    **The arrows had carried this since they were added**; moving the zoom
    cluster in beside them yesterday (item 0AF) gave it the same defect, which is
    the only reason it was noticed. Both are now anchored to `#scan-pane`, which
    does not scroll. `--pane-header-h` became a token so the arrows can centre on
    the SCAN rather than on the pane, which now includes a header bar.

    **A URL that names a word behaves like clicking that word.** It used to only
    reveal and highlight, so following a link left the reviewer looking at the
    right word with no way to act on it. `highlightRoutedWord()` now DISPATCHES
    the click on the span rather than reimplementing it: five render branches
    attach five different handlers, and choosing between them here would be a
    sixth copy of that mapping — the exact defect item 0AE records fixing in this
    same function. The clipboard write is the one thing suppressed: a page loaded
    cold from a link has no transient user activation, so the browser rejects it
    and a "Could not copy" toast would appear on every followed link.

    Word-list rows keep their own behaviour (`fromList`) — a row already has the
    list as its context, and opening the word's panel calls `closePanels()`,
    which would shut the list on every row.

    **TWO BUGS OF MY OWN IN THAT CHANGE, both caught by a test that passed alone
    and failed in the suite.** First, `addEventListener('hashchange',
    applyHashRoute)` hands the listener's HashChangeEvent in as the options
    argument, so `event.fromList` was undefined. Second, and the real one:
    wrapping that was not enough, because the row handler set `location.hash` and
    THEN routed — and setting the hash queues a hashchange *task* that re-routes
    with no options. The `routing` guard swallowed it only while the first route
    was still in flight; **on an already-mounted klal every await resolves as a
    microtask, so the route finishes before the task queue is reached** and the
    hashchange ran the full click path. Whether klal 1 happened to be mounted
    decided it, which is precisely why it was invisible in isolation.

    Resolved by splitting `routeToKlal(klalId, wordIndex, opts)` out of
    `applyHashRoute()`, so the list routes DIRECTLY and no hashchange is ever
    queued — `updateHash()` uses `replaceState`, which fires no event.

    Three tests added, one of which asserts the overlay controls do not MOVE, not
    merely that they are visible: a control that wanders is as bad as one that
    vanishes. Full suite **440 collected, 439 passed, 1 skipped**.

0AJ. **[2026-09-02] A NAV JUMP RE-ASSERTED THE LABEL BUT NOT THE GEOMETRY, so
    clicking a klal in the index could select the one above it. 5 of 222 klalim.
    FIXED.**

    Caught by `test_a_nav_jump_lands_on_the_klal_it_was_asked_for` going red on a
    run whose only other change was Dicta data — the corpus was byte-identical, so
    the cause had to be the frontend, and it was: yesterday's new 46px text-pane
    header shortened `#text-scroll` and tipped a marginal case over.

    Klal blocks mount lazily behind ESTIMATED placeholder heights, and the blocks
    a jump scrolls PAST resize as they mount — so the destination drifts below the
    reading line while the smooth scroll is still running.
    `releaseObserverWhenScrollSettles()` then re-asserted the right klal into the
    nav on top of a page whose geometry said otherwise, and the first scroll event
    after the observer was released recomputed the geometric answer and overwrote
    it. Click klal 105, land on 104.

    The fix re-seats the destination block before releasing the observer, instead
    of only re-writing the label. `READING_LINE_OFFSET` is now one constant:
    `updateActiveFromScroll()` asks "which klal am I reading" and this function
    has to give the same answer, and the offset was written out twice.

    **Swept, and the first sweep was wrong.** Sampling 260ms after each click
    reported **125 of 222** klalim landing wrong — and that is the exact artifact
    `jumpTo`'s own comment warns about, a measurement taken mid-animation on a
    ~1.5s smooth scroll. Re-measured after waiting for the scroll to settle: **5
    of 222** (klalim 168, 217, 218, 221, 222), now **2**. The two survivors are
    the last klalim in the corpus, where the nav label is CORRECT and only the
    geometric observer disagrees — no scroll can fix them, because there is
    nothing below them to scroll into, and nothing can scroll further to trigger
    an override. Left alone deliberately.

    Lesson 19's shape, on my own measurement: the first number was 25x the real
    one and would have read as a catastrophe.

0AH. **[2026-09-01] "SO GREEN WORDS ARE APPLIED BUT NOT REBUILT? WHY?" — THEY
    WERE NOT APPLIED. A status label I shipped this morning conflated a
    confirmation with a promotion, and published a wrong number for item 0AB.**

    The reviewer asked the right question about the wrong premise, and the
    premise was mine. `_decision_status()` had one `applied` bucket meaning
    nothing more than `corpus == chosen_text` — which is **trivially true for a
    ruling that keeps the stored reading**, and that is the commonest decision in
    this corpus. Measured on the live corpus:

    | of the 56 words drawn human-decided | |
    |---|---|
    | keep the stored text (nothing to promote) | 46 |
    | change the text, not yet promoted | 9 |
    | changed the text AND promoted | **1** |

    It had been reporting 27 of those as "applied". The one genuine case is klal
    68 w29 — a `chosen_text: ""` deletion of a duplicated `הניזקין`, which **did**
    land (the duplicate is verifiably gone) but reads as un-applied because
    deleting one of two identical adjacent words leaves its twin standing at the
    deleted one's index. Text equality cannot tell that from "never applied", so
    the status now takes `applied_decision_ids()` as outranking the inference —
    a recorded apply_event is a positive statement; equality is a guess a
    duplicate defeats. Whether that claim is still TRUE remains
    `audit_applied_decisions.py`'s job, not the display's.

    **Statuses are now `confirmed` / `applied` / `pending` / `drifted` /
    `unplaced` / `unknown`, and `index_stale` is a separate field** — see 0AB,
    whose headline number this corrects from "105 orphaned" to "105 stale
    addresses, 79 of them on rulings that were honoured anyway".

    And the direct answer to the question as asked: **nothing here is waiting on a
    rebuild.** `part1.json` was last written 14:20 and the last rebuild ran 14:21;
    no apply has run since. The green words are green because they still carry a
    live queue entry, not because a rebuild is overdue.

    Two gated invariants added: a ruling that kept the stored reading must report
    `confirmed`, and `index_stale` must not be a synonym for a lost ruling.

0AI. **[2026-09-01] COULD NOT REPRODUCE: "scan pane is oriented to the middle of
    the page" after dismissing a word. OPEN, needs one detail from the reviewer.**

    Reported for klal 12: selecting a word then clicking away or committing
    leaves the scan mid-page instead of at the klal's region, while navigating
    straight to the klal is correct.

    Tried and NOT reproducing, all with the region box's position measured
    against the viewport rather than eyeballed: window heights 1000/760/560;
    words on the klal's start page (18) and on its continuation (19); dismiss
    delays of 60/150/400/2000 ms; with and without a manual zoom; with and
    without the focus zoom having fired. In every combination the klal-region
    outline ends up in view, at the same scroll offset as a direct nav.

    One hypothesis was measured and **disproved**: `applyZoom()` scrolls the
    focused word into view with `behavior: 'smooth'` and `block: 'center'`, and a
    smooth scroll still animating when the panel is dismissed would land the view
    centred on the word — "the middle" — overriding the instant region scroll.
    That is a real race in the code, but dismissing at 60 ms (well inside the
    animation) does not trigger it. Not fixed on a story: this is the shape
    Lesson 31 warns about, tuning something that has not been measured.

    The one real difference I CAN see: selecting a word on the continuation page
    and dismissing leaves the scan on **page 19** showing klal 12's continuation
    at the top, where a direct nav shows page 18 with the region at the bottom.
    That is defensible behaviour (you were looking at page 19) but it does read
    as "not where the klal is". If that is the report, the fix is a decision about
    which page a dismiss should return to, not a bug hunt.

    **To pin it:** the browser window height, and whether the word selected was on
    page 18 or page 19.

0AG. **[2026-09-01, reviewer-requested] THE INDEX ROW AND THE LEGEND, TIGHTENED —
    and a shared font token that named no Hebrew face.**

    - **The two klal markers were set in different faces**, one pane apart
      (reviewer: "is the heb num in the index pane the same font as the text
      nums? it should be"). `--font-marker` was `'Inter', sans-serif`, and **Inter
      carries no Hebrew**, so every Hebrew marker resolved to whatever the system
      picked — while the index pane's `.nheb` declared no `font-family` at all and
      inherited the body's Frank Ruhl Libre. The same `יב` was a system sans in
      the text pane and a serif in the index, under a token whose own comment
      claimed it was "the section number, in either script". The token now names
      `'Inter', 'David Libre', 'David'`: font matching is per-glyph, so Latin
      digits still take Inter and Hebrew letters take the face `--font-title`
      already uses — the book's own type. An unspecified fallback was never a
      choice, it just looked like one.
    - **The Latin klal id shrank** (18px/34px → 13px/24px, its own
      `--nav-id-size`). It was the widest fixed thing in the index row after the
      badges, at the size of the Hebrew marker beside it, for the half of the
      reference the BOOK does not print.
    - **The part dropdown stopped being a band across the index pane** — "part
      dropdown creates asymmetry any suggestions?" It was full-width while the
      other two panes had nothing at that height. Shrunk to its content and
      folded into the filter row; the option labels drop the klal ranges, which
      are already the first and last rows of the list beneath it. Two rows
      reclaimed for the index across this and the previous pass.
    - **The two Human-Decided counts are two rows**, not one row with a sentence
      hanging off it. Only the first carries a colour swatch — nothing on screen
      is painted for the second, which is the whole reason it exists.
    - **The English title now appears once**, in the index bar. Four slots put it
      at both ends of all three bars, i.e. the work's name six times across one
      window; the Hebrew stays everywhere because the book prints it as a running
      head on every page.

    **ONE THING WAS ASKED FOR AND DELIBERATELY NOT SHIPPED AS WORDED.** The
    request was to label the first row "human-decided (not yet applied)". Measured
    before writing it: of the 54 words drawn as human-decided, **27 are already
    applied** and only **4 are genuinely not yet applied**. Shipping that label
    would have told the reviewer 54 rulings await promotion when the real backlog
    is 4. The row reads "(still shown)" instead, which is what it counts — a
    ruling stops being drawn once its candidate entry is dropped by the rebuild,
    whether or not it was applied. The true not-yet-applied figure is the
    `pending` chip in the recorded list, and making it a third row is a one-line
    change if wanted.

    Full suite **438 collected, 437 passed, 1 skipped**.

0AF. **[2026-09-01, reviewer-requested] ONE HEADER BAR, THREE PANES, LIGHTENED —
    and the old one was overflowing invisibly on two of them.**

    Reviewer: "ui looks ugly and cluttered - needs uniform look and feel. text
    differs between two blue headers ... both headers same size and shape. try
    lighter color since text pane has no matching header. maybe sacrifice a line
    at top to add header that just says something like page text."

    **Four slots, one order, all three panes** — the order taken verbatim from
    the reviewer's own description of the scan pane:

        [Hebrew title]  [Hebrew reference]  [English reference]  [English title]

    | pane | reference |
    |---|---|
    | index | the section being listed (`כללי הגמרא` / Klalei HaGemara) |
    | text | the klal being read (`כלל יב` / Klal 12) — **new**, the pane had no bar at all |
    | scan | the page and klal being shown (`דף יח · כלל יב` / Page 18 · Klal 12) |

    The text pane's bar is the one that was "sacrificed": it was the only pane
    without a header, which is what made the other two read as heavy — and the
    pane a reviewer spends the most time in was the one that never said where
    they were. Its Hebrew numeral comes from `/api/numerals`, the same table the
    scan header uses, not a second gematria implementation.

    **Each pane used to style its own title, which is exactly how the two bars
    came to say different things in a different order.** There is now one slot
    vocabulary (`[data-slot]`, `.ph-*`) and one function filling it, so a pane
    cannot carry a title the others do not. `document.title` was the last
    hardcoded "Yad Malachi" in the frontend and now comes from `/api/corpus` too.

    **The bar was overflowing, invisibly, and `overflow: hidden` was the reason
    nobody could see it.** Measured rather than eyeballed: the index header
    needed 365px in a 347px space at EVERY window width, and the scan header
    overflowed by 58px at 1280. The symptom was a silently eaten slot
    ("Klalei HaGem"), not a broken layout. Fixed by tightening the type scale and
    **moving the zoom cluster out of the scan header onto the scan itself**,
    beside the page arrows already floating there — which is also what makes the
    three bars one object rather than two bars and a toolbar. All three now clear
    their content at 1280/1600/1920, and the new test measures need against
    available rather than trusting the picture.

    **Lighter, and the whole chrome with it.** `--header-bg/fg/muted/line/hover`
    replace the solid `--accent-dark`. The part-select (inline-styled dark navy,
    sitting directly under the newly-lightened index header) and the legend
    (solid `--accent`) moved to the same palette — after the bars were lightened
    those were the only saturated blocks left, and "uniform look and feel" is
    about the chrome, not only the bars.

    **Also:** the two index filters share one line ("max real estate for the
    index"), and the page arrows' GLYPHS swapped back — "arrow behavior is
    correct but swap two icons" — so each points inward along the book's
    right-to-left reading direction. Sides and handlers untouched.

    **Two existing tests were pinned to the old layout.**
    `test_the_scan_header_actually_separates_its_two_scripts` measured
    `hebrew.left - english.right`, which assumes English comes first; the
    reviewer specified the opposite order, so a correct bar scored -173. The
    requirement is unchanged and still pinned — the measurement is now
    order-independent, so re-ordering the bar again cannot fail it for the wrong
    reason. The arrow test's glyph literals were swapped with the glyphs.

    **One thing delivered exactly as specified that is worth a second look:** the
    four-slot order puts the work's name at both ends of every bar, so
    `יד מלאכי` and `YAD MALACHI` now each appear three times across the top of the
    window. That is what was asked for and it is what makes the bars uniform, but
    it is also six repetitions of one fact on a screen whose complaint was
    clutter. Dropping the English title from the text and scan bars would leave
    the shape identical and remove four of the six; not done, because it was not
    what was asked.

    Full suite **435 collected, 434 passed, 1 skipped**.

0AE. **[2026-09-01] EVERY DEEP LINK TO A WORD ON A CONTINUATION PAGE LANDED ON
    THE WRONG PAGE WITH NO HIGHLIGHT — 18,044 words across 55 klalim. FIXED.**

    Reported as one word: "klal 12 w 219 clicking does not show that word
    highlighted." Klal 12 starts on page 18 and word 219 is on page 19; the link
    showed page 18, where that word has no box — so nothing highlighted, and no
    error anywhere.

    **`highlightRoutedWord()` carried a hand-rolled second copy of
    `pageForWord()`, and its `word_pages` branch COULD NOT FIRE.** `klalById` is
    built from `/api/klalim`, whose payload has no `word_pages` key at all — only
    `/api/klal` carries it — so `k.word_pages && …` was always false and every
    deep link fell through to the klal's START page. Lesson 25 in its exact
    shape: a condition that can never be true is not a fallback, it is dead code
    wearing one.

    **Swept before fixing, and it is a class, not a word: 18,044 of Part 1's
    52,630 words sit on a page other than their klal's start page**, across 55
    klalim (klal 30 alone has 1,716). Every deep link to any of them was landing
    on the wrong page — including every row of the word lists added in `0AA`/
    `0AC`, which are deep links, which is how the reviewer met it.

    **The same wrong object was being handed to the real `pageForWord()`** at its
    other call site (`attachWordHandlers`), disabling the same branch there.
    Latent rather than live — it is reached only for a correction served with
    `page: null`, of which Part 1 has 7, none on a continuation page — but it is
    the branch that function was written for (klal 179 w267, 2026-08-26). Both
    call sites now go through `klalForPageLookup()`, which prefers the mounted
    `/api/klal` payload.

    **A SECOND, INDEPENDENT DEFECT, found while reproducing it.** The click set
    the right page and a scroll event a few hundred ms later undid it:
    `updateActiveFromScroll()` resolved a different klal and `setActiveKlal()`
    showed THAT klal's start page. `manualPageLock` guards the scan pane's
    prev/next arrows against exactly this, and a word click deliberately CLEARS
    it (2026-08-26, because the lock was making word clicks dead) — which left
    the click the one deliberate navigation with no protection. It now holds the
    observer off while it settles, the same as `revealWordInText()` and
    `applyHashRoute()` already did; it was simply the third member of that set
    that never joined it.

    **One existing test was pinned to the defect and went red on the repair.**
    `test_the_scan_header_carries_the_reference_in_both_scripts` asserted a
    literal "Page 73" for klal 210 word 133 — but `word_pages["133"]` is 74, and
    the klal splits 61 words on 73 against 69 on 74. 73 was the START page, i.e.
    the wrong answer the bug produced. Lesson 36, verbatim: the test failed
    because the dashboard got BETTER. Its page now comes from the server; its
    Hebrew numerals, which are what it is actually about, follow the resolved
    page rather than a second literal.

0AD. **[2026-09-01, reviewer-requested] DASHBOARD CHROME: one header bar shared
    by both panes, the copy-on-click switch behind a settings icon, the legend
    saying what its two numbers ARE, and the word list getting out of the way.**

    Five small things, from one message.

    - **The index pane's title is now IN a header bar**, not above one. It first
      shipped inside `#nav-filter`, which is white — and its own colours are
      near-white, so it was very nearly invisible. **The Playwright test asserted
      its TEXT and passed the whole time**, which is the limit of checking
      content and never appearance; the new test checks the bar's geometry and
      that the title is not the same colour as the ground it sits on. Both panes
      now share `.pane-header` and measure 48px, aligned at the top of the
      window.
    - **Whitespace between the scan pane's title and its page/klal reference** —
      they were running together. `.pane-ref` is the gap.
    - **The copy-on-click switch moved behind a settings icon.** "Don't put click
      word on link up there on the index pane, hide it away somewhere - settings
      icon?" It is set once and lived with; it does not earn a permanent line
      beside the two filters that get toggled while reading. The tray does not
      close on the click that flips its own switch — that is a control you would
      have to reopen to confirm.
    - **The legend reads "Human-Decided · 51 · visible out of 478 total
      recorded"**, the reviewer's own wording. It said "51 / of 478 recorded",
      which does not say what either number is.
    - **The word list closes on a click in the text or scan pane.** Only that
      panel: the other five are OPENED by a click in those panes, so closing on
      the same click would shut them the instant they opened.

    Full suite **432 collected, 431 passed, 1 skipped** (`pytest --collect-only
    -q`, per Lesson 37).

0AC. **[2026-09-01, reviewer-requested] A SENIOR-REVIEW VIEW OF EVERY RULING,
    the book title on both panes, the scan arrows swapped — and two code-review
    findings fixed, one of which was hiding a real lost correction.**

    **The senior-review view.** "Add a function to show all previously decided
    words — so a sr reviewer can review a human's work." Reviewing a ruling means
    seeing what was decided AND whether it landed, and neither was reachable: a
    ruling stops rendering once it is settled, so the dashboard showed 51 of 478
    and nothing at all about the rest. "of 478 recorded" in the legend is now its
    own control opening its own list — every ruling, with the word now at that
    index, what was chosen, which panel recorded it, when, and a status:
    `applied` / `pending` / `drifted` / `unplaced` / `unknown`, filterable by
    chips. It is the first surface that shows item `0AB` at all; it names
    stranded rulings and does not repair them, which stays a separate decision.

    The click handler tests the recorded button BEFORE the row it sits inside —
    `closest('.legend-clickable')` would otherwise walk past it and open the
    51-word list from a control labelled 478.

    One defect of my own, caught by its test: `rendered` was read from the
    `states` dict, which has no slot for a `delete`-opcode entry (two deletes can
    share an index), so it reported 39 against a legend showing 51 — a third
    number on a screen that already has two. It now comes from `state_rows()`,
    the same source the count uses.

    **Book title on both panes**, from a new `/api/corpus` backed by five
    constants in `corpus_io.py` — not written into `index.html`, because a title
    in the markup is one more place a second work would have to be edited.
    Hebrew first on both surfaces, the same reasoning the nav already applies to
    klal markers: the reviewer is matching against the printed page, and the page
    says `יד מלאכי`. The edition is on hover only.

    **Scan arrows swapped** — previous to the left, next to the right. The glyphs
    moved with the buttons, so each still points away from the centre; swapping
    only the sides would have left "previous" on the left pointing right.

    **Code review finding #1 — `audit_applied_decisions.py` was absorbing a real
    lost correction.** `find_span()` searches the whole klal, so the
    shifted-index reclassification accepted a hit at ANY distance, and the
    drifted list only printed under an env var whose hint string could only be
    read by someone who had already set it. Klal 10's applied `candidate_choice`
    claims `כתבו` at w85; the corpus has `למד` there and `כתבו` at w74, eleven
    words away in a klal whose applies shift by one. It was being reported as
    "reflected at word_index 74 (-11)" — printed nowhere — and that single
    reclassification took the headline from 57 MISMATCH to 1.

    Now bounded by `MAX_EXPLAINABLE_SHIFT = 5`, and the drift list prints by
    default (`AUDIT_HIDE_DRIFT=1` suppresses it). Audit goes 1 → **2 MISMATCH**,
    56 → 55 shifted, and klal 10 is back in front of a human.

    **Two candidate rules were measured and REJECTED before this one.**
    Requiring the relocated span to be UNIQUE in the klal is exactly backwards:
    klal 10's false relocation is the one case whose word occurs exactly once,
    while 36 of the 55 legitimate ones match a word appearing 2–6 times
    (`אלהים` six times in klal 69). And a bound derived from the ledger's own
    word-count deltas is unsound — klalim 159 and 163 show real ±1 shifts while
    every applied decision in them is word-count-neutral, because the pipeline's
    editorial-mark insertions move indices without any decision recording it.
    Measured, not assumed; had either shipped it would have been worse than the
    bug. Observed legitimate shifts span −3..+2, 44 of them exactly ±1.

    **Code review finding #2 — `preview_dicta_disputes.consensus_of()` answered a
    2-2 split by dict-insertion order.** `collect()` always inserts docai, vlm,
    surya, candidate, so an even split always resolved to the docai side;
    `classify()` then found the candidate absent from it and dropped the position
    with no trace. In practice the "contested" section could only ever fire when
    the candidate happened to agree with DocAI. Split into `consensus_groups()`
    (ordered by size, ties on the reading — never on insertion order) plus a
    `prefer=` argument, which is the question the tool asks: what does adding
    THIS engine do to the consensus.

    **Zero effect on today's output** — new/joins/escalations/contested are
    unchanged at 59/63/1/0, because the current Dicta baseline covers only pages
    22–50 and no position there hits a 2-2 split. It is latent, and pages 51–114
    are expected to bring 3–4× the disputes. Verified by construction instead:
    the same split written both ways round now yields the same verdict, which is
    the assertion the old test was missing.

    Findings #3–#8 of that review are untouched and still open. #3 in particular
    is now doing visible damage in a second place: the null `chosen_text` records
    it names are what the recorded list has to report as `unknown`.

    Full suite **426 collected, 425 passed, 1 skipped** (`pytest --collect-only
    -q`, per Lesson 37).

0AB. **[2026-09-01] 105 OF PART 1's 483 RECORDED RULINGS CARRY A STALE ADDRESS —
    but 79 of those were HONOURED anyway. The rulings actually unaccounted for
    number 26. OPEN, and smaller than this entry first claimed.**

    Found while measuring where the legend's "51" comes from (item `0AA`); not
    fixed. **Now visible in the dashboard** — the recorded-rulings list added in
    `0AC` shows a status and a stale-address marker per row, with filters for
    both, so this item finally has a surface.

    **THIS ENTRY'S ORIGINAL NUMBER CONFLATED TWO DIFFERENT THINGS and overstated
    the damage.** It counted a ruling as orphaned whenever the word at its index
    was neither the one ruled on nor the one chosen — which is true both for a
    ruling that was LOST and for one that was HONOURED and then had its index
    shifted out from under it by a later apply in the same klal.
    `audit_applied_decisions.py` separates exactly those two (55 shifted, 2
    genuinely missing); this entry did not. Corrected 2026-09-01 by splitting the
    display's `status` (what happened to the RULING) from `index_stale` (what
    happened to its ADDRESS):

    | | rulings | |
    |---|---|---|
    | applied | 259 | changed the text, and the change is in the corpus |
    | confirmed | 162 | KEPT the stored reading — nothing was ever to be promoted |
    | **pending** | **5** | changes the text, not yet promoted — the real apply backlog |
    | **drifted** | **16** | fate cannot be told from here |
    | **unplaced** | **10** | `word_index` outside the klal entirely |
    | unknown | 31 | nothing usable was snapshotted — see below |
    | **stale address** | **105** | index no longer points at the word it names — 50 of them `applied`, 29 `confirmed` |

    **So: 105 stale addresses, of which 79 belong to rulings that were honoured
    anyway; 26 rulings genuinely unaccounted for; 5 awaiting promotion.** A stale
    address is still a defect — a re-decision at that key lands on the wrong word,
    and both display paths silently drop it — which is what Lesson 35 is about.
    It is just not the same defect as a lost correction, and reporting 105 lost
    corrections was wrong.

    **RECOVERABILITY, measured 2026-09-02** (reviewer: "looking at the first two
    in klal 1 I see the corrected word earlier in the klal — can we recover them
    all?"). No — 43 of 105 can be re-pointed mechanically, and the rest cannot:

    | evidence | rulings | |
    |---|---:|---|
    | snapshot bbox AND text agree | **40** | two independent signals, Lesson 9 satisfied |
    | deletion carrying a bbox | 3 | position known, nothing to text-match |
    | text only, exactly one occurrence | 21 | ONE signal — see the caveat below |
    | bbox present, signals disagree | 7 | needs a human |
    | text only, several occurrences | 20 | ambiguous by construction |
    | no evidence at all | 14 | the word is gone |

    **The 21 single-signal ones are not safe as a class.** Their implied shifts
    include **−108 and −107**, which is the exact shape of the false relocation
    that `MAX_EXPLAINABLE_SHIFT` was added to catch (klal 10's was unique in its
    klal and −11 away, and it was a different occurrence of the same word). A
    unique text match is not evidence of position — that was measured and
    rejected once already.

    **Two things fall out of this.**

    - **55 of the 105 are `manual_correction`, which snapshots no scan position
      at all** — `{word_index, original_word}` and nothing else. That is the
      structural reason half of this class is unrecoverable from the ink, and it
      is a FORWARD fix: `api_post_manual_correction` could snapshot the bbox at
      decision time, since `_word_scan_position()` already computes exactly that
      for rendering. Every future manual ruling would then survive a reindex.
    - **Genuine shifts reach −31** among the 40 two-signal recoveries, well past
      the ±5 `MAX_EXPLAINABLE_SHIFT` set in `audit_applied_decisions.py` on
      2026-09-01. Not a contradiction — that constant governs a narrower
      population (decisions carrying an apply_event, where measured legitimate
      shifts ran −3..+2) — but bbox evidence is a better basis for that bound
      than the empirical range, and it should be re-derived from it.

    Nothing has been re-pointed: the ledger is append-only and protected, and
    re-pointing is a write to it. Awaiting an explicit go-ahead.

    `unknown` is mostly `witness_choice`, which snapshots `docai_reading` vs
    `tesseract_reading` and never records the stored word, plus the records
    carrying a **null `chosen_text`** — the 2026-09-01 review's finding #3, still
    open. Klalim carrying the most stale addresses: 69, 74, 36, 57, 63, 66, 1, 39.

    **This is Lesson 35's failure mode at scale.** Applying a correction shifts
    every later index in that klal, and nothing re-points the decisions past it.
    That lesson was written from an incident of **10** orphaned decisions
    (2026-08-13); the real figure today is 119.

    **Why nothing shows it.** Both display paths drop a drifted decision rather
    than render a wrong word — `api_klal`'s manual loop and `api_klalim`'s count
    both skip on `_word_matches` — which is the RIGHT call for the screen (it is
    what stops someone else's `chosen_text` appearing on an unrelated word) and
    is why no count, badge or legend reflects them. They are neither applied nor
    visible nor audited.

    **Not proposing a repair here, deliberately.** Re-pointing 119 decisions
    means reconstructing an edit history from `apply_event` rows, and per
    Lesson 31 a mutator that has to guess where a word went is exactly what
    should be handed back rather than tuned. What is needed first is a decision
    on what a stranded ruling MEANS: re-point it, retire it, or surface it to
    the reviewer as "you ruled here once and the ground moved". `audit_applied_
    decisions.py` is the natural home for detecting them; today it does not.

    Measured with `review_decisions.all_current()` over `candidate_choice`
    (aliased to `disputed_choice`) and `manual_correction`, against live
    `part1.json`. Re-measure before quoting — the numbers move with every apply.

0AA. **[2026-09-01, reviewer-requested] THE LEGEND'S "HUMAN-DECIDED 51" WAS
    COUNTING THE SCREEN, NOT THE LEDGER — it now shows both. Plus: every legend
    count opens the list of words behind it, and clicking a word copies its
    link.**

    Reviewer: "count for human decisions is 51 — not correct." It was not a
    counting bug — `decided_count` faithfully counts the words rendered GREEN,
    and `test_nav_tristate_matches_what_each_word_actually_renders_as` passes —
    it was a LABELLING one. A decision stops rendering the moment it is settled:
    `assemble_corrections_dataset.py` drops the candidate entry, and an applied
    `manual_correction` fails the display drift check because the word it names
    is no longer there. So 478 rulings on record displayed as 51, and the number
    read as "you have decided 51 words".

    | Part 1 | |
    |---|---|
    | words rendering human-decided | 51 |
    | distinct word positions carrying a ruling | 478 |
    | …of which the corpus already agrees with | 344 (the rest: item `0AB`) |

    **Kept both numbers rather than replacing one.** Swapping in the larger
    figure would have broken the tri-state identity
    (`decided + resolved + disputed == total`) the invariant above asserts. The
    legend row now reads `Human-Decided  51  of 478 recorded`, with the
    distinction in its `title`.

    `recorded_decision_count` (new, on `/api/klalim`) is the union of
    `candidate_choice`/`disputed_choice`, `manual_correction` and
    `witness_choice` positions, keyed to one index space — witness rulings are
    mapped through the witness queue's own `word_index`, exactly as
    `review_counts.word_states()` maps them before colouring the word. **Leaving
    that third leg out was a real defect in the first cut** and klal 30 caught
    it immediately: recorded=3 against decided=9, a context figure SMALLER than
    the count it was giving context to. `punctuation_choice` stays out —
    `before_word_index` addresses the gap between two words, not a word.

    **Two features landed with it, both reviewer-requested.**

    - **Every legend count is now a control.** Clicking one opens the list of
      the words it counts, each row a working deep link, via a new
      `/api/word-states`. The lists are built in the SAME pass as the counts
      (`api_klalim`'s `on_klal_states` callback) — a list that is a different
      length from the number that opened it is this file's oldest defect family
      (nav 1,201 vs 1,061 rendered; klal 88's "-1"; klal 73's missing badge),
      every instance of it two encodings of one rule disagreeing. Holding the
      pointer on a row for 400ms reveals its copy button; a hover would put a
      button under the cursor on all 518 rows and make the list unreadable.
      `review_counts.state_rows()` was extracted for this and `count_row()`
      redefined on top of it, so the enumeration and the count cannot diverge.
    - **Clicking a word copies its URL**, with a toast saying so, and a
      "Copy word link on click" checkbox turns it off (persisted in
      localStorage). Hooked into `focusWordOnScan()` — already the single funnel
      every word click passes through, and already the only place that maintains
      the address bar — so the link copied is the same address the hash is set
      to by construction. `highlightRoutedWord()` passes `viaClick: false`:
      arriving somewhere by following a link must not overwrite the clipboard
      the reviewer used to get there.

    `#legend` was raised from `z-index: 40` to `920`; at 40 it went under the
    panel backdrop its own click opens, so switching legend rows would have
    needed a dismiss step first. `closePanels()` now queries `.side-panel.open`
    instead of naming five panels by hand — a sixth was being added, and a panel
    missing from that list stays open underneath the next one.

    Eight new tests: two gated invariants (list length equals the count it came
    from; recorded is the ledger's union and never below what renders) and six
    Playwright. Full suite **420 collected, 419 passed, 1 skipped** — count from
    `pytest --collect-only -q`, per Lesson 37.

1F. **[2026-09-01] KLAL 209 APPLIED — three spurious words removed, and the
    sentence the 2026-08-14 spot-check called unparseable now parses.**
    34 -> 31 words.

    | | |
    |---|---|
    | was | `…אלא הוא חד מסספיע השם הדין לעונשין שהם מדברי סופרים…` |
    | now | `…אלא הוא הדין לעונשין שהם מדברי סופרים…` |

    `הוא הדין` — "the same law applies" — is a standard rabbinic phrase, and it
    was sitting there all along with `חד מסספיע השם` wedged inside it. The
    spot-check had flagged w16 `מסספיע` as "unreadable as written: not a word in
    any reading", and it was right about the word and short of the real defect,
    which was a three-word intrusion, not one corrupt token.

    **Two independent signals agreed before anything was applied.** The vision
    pass on the `unverified_insertion` candidate at w15 read the crop as marginal
    fragments (`שוה הכ`, `הד`, `סופ`) and reported that the candidate text is NOT
    in the ink; the reviewer then chose to remove the whole span. Semantics and
    the scan pointed the same way (Lesson 9 satisfied).

    **Three overlapping decisions, one intent, and the guards handled it.** The
    reviewer recorded a span removal at w15 AND separate deletions of w16
    `מסספיע` and w17 `השם` — all describing the same three words. Run 1 applied
    the span removal and the per-klal-per-run gate deferred the other two; after
    the rebuild they DRIFTED (w16 now reads `לעונשין`, w17 `שהם`) and were
    correctly skipped, subsumed rather than lost. This is the drift check doing
    exactly its job: three ways of saying one thing collapsed to one edit with no
    double-deletion.

    **A `--skip-vision` shortcut was wrong here and the gate caught it.** The
    first rebuild used `--skip-vision`, and
    `test_no_stale_candidate_survives_a_rebuild` failed with one
    `stale_candidate` at (209, 15) and the instruction to re-run without the
    flag. Removing words changes which candidate sits at a position, so the
    vision stage is what refreshes it. **`--skip-vision` is for iteration that
    does not move word positions**; after any word-count change it leaves the
    reviewer facing a verdict about a different word.

    Post-rebuild: `corrections_part1.json` **624 items across 147 klalim** (was
    625/148). Full suite **405 passed, 1 skipped**.

1E. **[2026-09-01, reviewer-requested] SWEPT THE OPEN-ITEMS LIST ITSELF. Of
    eight checkable claims, three were stale, one was misleading, and one of my
    own was a false alarm. Every error ran the same direction: recorded as open,
    actually closed.**

    | item | claim | verified |
    |---|---|---|
    | 26 | 1 `&` left (per item 37) | **stale** — now 0 |
    | 0G | 2 UI tests never collected | **stale** — 44 declared, 44 collected |
    | 27 | 3 klalim carry seam furniture | **stale** — all 3 repaired (item 1A) |
    | 3 | 419 items, 8 decided, **411 remain** | **misleading** — see below |
    | 16 | 71 of 667 placeholders | accurate — but **0 in Part 1**, so it is gated |
    | 57 | 1 U+05F4 left | accurate — and it is a *ruling to keep*, not a loose end |
    | 0M | 3 geresh-read-as-yod | accurate — klal 12 `סעיף אי`, 140 `אות עי`, 155 `סעיף זי`, all still present |
    | 22/43 | detector not in the rebuild chain | **my false alarm** — see below |

    **Item 3 is the one that matters**, because its number is the one a reader
    would quote. 419 is exact for the FILE; the reviewer is served 44, of which
    24 are open. Corrected in place rather than rewritten, so the drift stays
    legible.

    **My own false alarm, recorded because the method was wrong and the method
    is the point.** I grepped `rebuild_all.sh` for `detect_real_word_substitution`,
    found nothing, and nearly filed "the detector does not run". It runs:
    `build_lexical_defect_report.py:32` imports it, and that IS stage 4b. A grep
    on a shell script answers "is this a stage", not "does this run" — the same
    shape as Lesson 32 and Lesson 37, where the source and the runner disagree.
    Check the import graph, not the driver script.

    **Five duplicate labels, now resolved:** `0S`, `0T`, `0U`, `29`, `30` each
    appeared twice — two sessions appended to this list concurrently on
    2026-09-01 and picked the same next letter. Mine were renamed to `1B`/`1C`/
    `1D` (the other `0U` is cited by name at `tests/test_pipeline_logic.py:5294`,
    so it kept the label); the second 29/30 pair is marked `29b`/`30b` as
    duplicate entries rather than deleted. **A shared newest-first list with
    hand-assigned labels does not survive two concurrent writers** — worth
    knowing before the next parallel session.

    **The systematic finding: nothing was recorded as closed while still broken.**
    That is the safer direction, but it means this list overstates outstanding
    work, and the two numbers most likely to be quoted — 411 witness items, 3
    seam klalim — were the two most wrong.

1A. **[2026-09-01] ITEM 27 IS FULLY CLOSED — all three page-seam klalim are
    clean, and the "remaining" one was repaired on 2026-08-31. Reviewer-prompted
    ("what is wrong with 210? i don't see anything") — nothing is.**

    Checked by CONTENT, not by the indices the item names:
    - **klal 39**: `דבכולהן` — **0 occurrences**.
    - **klal 74**: reads `אמר רבא אמר רב יהודה`, which is exactly what item 27
      says the PAGE reads; the corpus had stored `אמר רבא אמר רבא אמר רב יהודה`.
    - **klal 210**: one `דהלכה`, and the phrase reads
      `אפשר דהלכה כקמייתא ולא כבתרייתא` — "it is possible the halacha is like
      the first and NOT like the latter". `ולא` at w66 is ordinary Hebrew.
      **Every flag on the klal is cleared.**

    **The repair is in the ledger, in detail.** On 2026-08-31 at 11:29-11:30 the
    reviewer recorded three deletions — `דהלכה` (the duplicated catchword), `:`,
    and `לא` (the folio numeral). They took FOUR apply runs to land (15:54,
    15:59, 16:00, 16:00) because of the one-word-count-change-per-klal-per-run
    limit, with the ledger re-indexing the survivors between each run — visible
    in the log as the same decision migrating w66 -> w65 -> w64. That machinery
    (item 0C) worked exactly as designed.

    **THE METHOD ERROR, made three times on this one item, twice by me.**
    Item 37 read klal 39 and klal 210 at the word INDEX item 27 named and
    reported both as "still present"; the indices had moved under the repairs.
    Earlier today I corrected the klal 39 half — and then repeated the mistake on
    klal 210, searching the text for the token `לא`, finding two ordinary
    occurrences, and concluding it "needs the scan" to tell which was furniture.
    It never needed the scan. It needed `review_decisions.jsonl`, which records
    the reviewer deleting that exact word.

    **The rule this earns:** when a status entry names a word position, the
    ledger is the first thing to read, not the last. The corpus tells you what
    the text says NOW; only the ledger tells you whether somebody already
    answered the question. Re-deriving from the text alone will keep producing
    "still open" for things that were closed, because a repair is exactly the
    event that invalidates the index the entry was written against. This is
    Lesson 5 (indices are not stable identifiers) meeting Lesson 19 (verify the
    claim, not the write-up) — and the cheap check is
    `rd._read_all()` filtered to the klal, which is four lines.

0Z. **[2026-09-01] `tools/patch_witness_word_indices.py` HAS NO ARGUMENT
    PARSING AND WRITES ON ANY INVOCATION — I ran it with `--help` and it
    silently rewrote the witness queue.** Reverted; no lasting damage. Recorded
    because the next person will do the same thing.

    The tool ignores `sys.argv` entirely: `main()` reads, re-derives every
    `word_index`, and writes `reconstruction_witness_queue.json` unconditionally
    (`:107`). There is no `argparse`, no `--dry-run`, and it is NOT in
    `rebuild_all.sh` — so it is a hand-run mutator whose safest-looking possible
    invocation is a mutation.

    **What it did:** set klal 88 w310 and w327 to `word_index: null`. Those two
    are not arbitrary — **w327 is the exact row behind the klal 88 "-1
    outstanding" arc**, the witness decision sitting at a position a
    manual_correction already covers. Nulling them removes both from what the
    reviewer is served. Whether the re-derivation is RIGHT is a separate
    question nobody asked and nobody reviewed; the point is that an unreviewed
    answer was written to a tracked file by a command that looked like a
    request for documentation.

    Not fixed here, deliberately — it is a one-line `argparse` guard plus a
    `--dry-run`, but it changes a tool's interface and belongs with a decision
    about whether the re-derivation it performs is currently correct at all.
    Whoever picks it up: check what those two nulls SHOULD be before restoring
    or re-running.

0Y. **[2026-09-01] C4 IS CLOSED. `pipeline/review_data.py` takes the last two
    stragglers, and NOTHING outside `tests/` imports `review_server` any more.**
    `review_server.py` **1,981 → 1,423 today** — 558 lines into three modules
    (`scan_alignment` 391, `review_counts` 310, `review_data` 240).

    Item 0V left C4 two-thirds done and said so rather than claiming the win:
    `tools/validate_suppression_filters.py` wanted `_load_witness_queue()` and
    `tools/patch_witness_word_indices.py` wanted `_load_klalim()`. Neither is
    geometry, so `scan_alignment` was never their answer. `review_data.py` is —
    the part-token vocabulary, the four per-part JSON readers, and the witness
    queue with its filtering rules. All pure reading.

    `BadRequest` is the one deliberate seam left: raised in `review_data`,
    caught in the server's `do_GET`, which turns it into a 400. That module
    knows what a bad part token is; only the server knows what a status code is.

    **The gate now covers `tools/` as well as `pipeline/`**, and was re-probed
    against a `tools/` offender to confirm the widening actually took.

    **A test caught me changing behaviour on the way through, and the lesson is
    the general one.** The extraction inlined `_load_json = cio.load_repo_json`
    at its five call sites — tidier, and wrong: that indirection is the seam
    `test_witness_queue_view_keeps_every_already_decided_item` and
    `test_witness_queue_filter_is_reversible` patch to feed a synthetic queue.
    Both failed. **Keep an extraction a MOVE and change nothing else on the way
    through**; the "while I'm here" tidy is what turns a provable no-op into a
    debugging session. The seam is restored and commented so it does not read as
    an oversight.

    The same two tests also had to be repointed from `rs` to `rdata`: a function
    reads its OWN module's globals, so patching a review_server alias does not
    reach a moved function. That is a real property of every one of today's
    three extractions and is now written down in the tests that depend on it.

    **Verified as a no-op on real data**: `api_klalim` for all 667 klalim,
    `api_klal` for klalim 1/29/88/163/222, and `api_witness_summary` are all
    **byte-identical** before and after, both versions run in place. Suite
    **405 passed, 1 skipped**. Server restarted; `/api/witness` 200,
    `?part=4` still 400.

    **S1's remainder, unchanged by this**: `api_klal` (280 lines) is the
    merged-entry builder — finding #6's other half, and a design question rather
    than a move. `api_page` (121) after it.

1I. **[2026-09-01] `pipeline/review_counts.py` EXTRACTED — S1's second half.
    `review_server.py` 1,981 → 1,585 today; `api_klalim` 249 → 168.** With
    `scan_alignment.py` earlier the same day, the God Object has shed **396
    lines** into two modules that are pure, importable and directly testable.

    **The point was not size, it was finding #6.** The 2026-08-26 review said
    the word-state rule was encoded THREE times — `api_klalim()` for nav counts,
    `api_klal()` for the text pane, `app.js` `wordState()` for colour — and that
    both production defects in that range came from the copies disagreeing (nav
    1,201 vs 1,061 rendered; then klal 88's "-1 outstanding"). It also recorded
    the counter-argument, which still holds: the obvious dedup, having
    `api_klalim` call `api_klal` 222 times, is what starved the Playwright
    suite. So what is now shared is the **rule**, not the request:
    `word_states()` answers "what is every word in this klal?" from data the
    caller already loaded, and `api_klalim` calls it per klal with no extra file
    reads. `app.js` remains a fourth encoding in another language and cannot be
    imported away; it stays held by the tri-state invariant test.

    **Verified as a no-op on real data, not just green.** `api_klalim()` output
    for **all 667 klalim across parts 1/2/3 is byte-identical** before and
    after — dumped from HEAD's `review_server.py` and from the extracted one,
    both run IN PLACE so the data is held constant. Suite **405 passed, 1
    skipped**.

    **Six unit tests the rule never had.** Until now every branch was reachable
    only through a 249-line endpoint, so all of it was covered *only* by the
    corpus-wide tri-state invariant — which says the totals agree but not which
    branch produced them, and cannot exercise a case the live corpus does not
    contain. Each test names the defect it guards: the open flag overriding a
    `current_text_confirmed` candidate (klalim 62, 70), the open flag NOT
    overriding a human decision, a witness vision verdict rendering green
    (klalim 30, 75), witness rows with `word_index: None` or out of range or
    already owned by a manual correction never being counted (klal 88's three
    phantoms), the tri-state summing to the total by construction, and a
    `delete`-opcode entry claiming no word slot.

    **Mutation-tested, not assumed.** Each of the three historical bugs was
    reintroduced into `review_counts.py` in turn — flag override back to
    `setdefault`, witness verdict back to always-DISPUTED, `word_index: None`
    back to counted — and each broke **exactly one** test. Given that three
    separate first-draft tests this week could not fail, that check is now the
    default here rather than a flourish.

    **What is left of S1**: `api_klal` (280 lines) is the largest remaining
    function and builds the merged entry list — the "merged-entry builder" half
    of finding #6's remedy. It shares the precedence rule with `word_states()`
    but expresses it as entry merging rather than classification, so unifying
    them is a real design question, not a move. `api_page` (121) is next after
    that. Neither is urgent now that the rule they share has one home.

1H. **[2026-09-01] `lexicon_yad_malachi_only.json` WAS NON-REPRODUCIBLE — the
    report rewrote itself on every run with no data change behind it.** Found
    while regenerating it to commit a stale copy: the regen produced a diff, and
    regenerating AGAIN produced a different diff.

    **Measured, four runs of the pre-fix generator: four different files.**
    Content identical every time (same 1,140 words, same counts) — only the
    ORDER moved. `near_forms()` collects candidates into a **set** and sorted
    them by `-ref_count` alone, so any two attested forms with an equal count
    came out in set-iteration order, which differs between processes. Observed
    pairs: `שחוזר`/`החוזר` (both attested 97), `ופרה`/`מסרה` (both 53). The
    row-level sort had the same gap. Both are now total (`-count, form, edit`
    and `count, -top_ref, word`), verified stable across repeated runs and
    across three fixed `PYTHONHASHSEED` values.

    **Why this is worth an item and not a silent tidy.** The file is tracked and
    is regenerated by stage 5b of `rebuild_all.sh`, so every rebuild left a
    dirty tracked artifact whose `git diff` carried no information. That trains
    a reader to skip the diff on a file whose whole job is to be read — the same
    cost Lesson 32 names, arrived at from the other direction. It also means any
    earlier commit touching this file recorded churn, not change.

    **Two false starts, both caught, both worth recording as method.**
    (a) My first attempt to prove the diagnosis ran the pre-fix script from the
    scratchpad, where its `REPO` resolves to the scratchpad's parent — so it
    never wrote the repo file and I was hashing an untouched file. It printed no
    `Wrote` line, which is what gave it away. A script that derives `REPO` from
    `__file__` cannot be A/B tested by copying it elsewhere; test it in place.
    (b) The first version of the regression test used **three** tied forms and
    PASSED against the broken sort — with a set that small, iteration order
    coincides with alphabetical often enough to be useless. Rebuilt with ~18
    tied forms and verified to fail on the pre-fix sort before being kept
    (Lesson 25, third time this week).

    Suite **397 passed, 1 skipped**.

1G. **[2026-09-01] `pipeline/scan_alignment.py` EXTRACTED — C4 is closed for the
    rebuild chain, S1 is down 218 lines, and neither the pipeline's output nor
    the test count moved.** `review_server.py` **1,981 → 1,763**;
    `scan_alignment.py` is 391 lines of pure geometry.

    **What moved and why those:** `load_regions`, `resolve_klal_page`,
    `klal_all_pages`, `klals_on_page`, `corpus_stamp`, `docai_page_stamp`,
    `corpus_bbox_cache_key`, `corpus_word_bboxes`, `word_pages_map`,
    `word_bboxes_resolved`, `word_scan_position`, and the two module caches.
    Every one is pure computation over files on disk — no HTTP, no request
    state, no ledger reads — which is what made the move mechanical. Dependency
    analysis before touching anything showed the whole cluster needs only `cio`,
    `os`, `difflib` and its own two caches.

    **The names are PUBLIC now, and that is the actual fix.** C4 was never
    really "a batch stage imports a module"; it was "a batch stage reaches for
    an HTTP server's UNDERSCORE-prefixed internals", which is what made the
    coupling fragile rather than merely present.

    **Both rebuild stages are free of it.** `synthesize_multi_witness.py`
    (stage 4a) and `assemble_corrections_dataset.py` (stage 4) no longer
    reference `review_server` at all. The latter's `import review_server`
    was deliberately hidden *inside a function* with a comment saying the
    laziness existed "so the module does not pull in the HTTP server just to be
    imported" — a workaround for a dependency that should not have existed. It
    is now removed rather than deferred.

    **C4 is NOT fully closed, and the remaining two are not this module's
    problem.** `tools/validate_suppression_filters.py:37` wants
    `_load_witness_queue()` and `tools/patch_witness_word_indices.py:32` wants
    `_load_klalim()` — a queue reader and a corpus reader, neither of them
    geometry. Both are tools rather than build stages, which is why the
    pipeline/ cases were the ones that mattered. Recorded here so the next
    session inherits the true remainder rather than "C4: done".

    **Evidence the move is behaviour-preserving**, not just green:
    - Full suite **392 passed, 1 skipped** — identical to the count immediately
      before the extraction.
    - The rebuild chain re-run end to end produces **byte-identical** output:
      `git status` reports NO change to `corrections_part1.json`,
      `klal_page_regions.json`, `consensus_disputes_part1.json`,
      `lexical_defect_report.json`, `klalim_demo_dataset.json` or
      `ligature_words.json` after regenerating them through the new import.
    - Server restarted and smoke-tested; klal 29 w86 serves `הנה`.

    **Two gates added, both verified to FAIL before being kept** (Lesson 25):
    `test_no_pipeline_stage_imports_the_review_server` (AST-based, probed with a
    throwaway `pipeline/` module that imports the server) and
    `test_scan_alignment_and_review_server_share_one_bbox_cache`. The second
    guards something a green suite would not catch on its own: the extraction
    kept `review_server._corpus_bbox_cache` as an ALIAS so ~40 call sites and a
    dozen tests read unchanged, and for a mutable module-level cache that only
    works while the alias is the *same object*. A rebinding would leave the
    server writing one dict and the geometry reading another — which surfaces as
    stale bounding boxes, not as an error.

1D. **[2026-09-01] TWO DECISIONS APPLIED — ONE REAL EDIT — AND IT CLOSES THE
    ONE POSITION ITEM 0Q SAID NEEDED A HUMAN FIRST.** `apply_reviewer_decisions.py`
    then `./rebuild_all.sh` (full, vision included). Corpus diff: **exactly one
    word**, word count unchanged (klal 29: 400 → 400).

    **klal 29 w86 `חנה` → `הנה` — item 0Q's blocker, resolved by the reviewer
    reversing their own earlier ruling.** Item 0Q flagged this as the one
    position that had to be settled before the other 59 Dicta disputes: the
    corpus read `חנה`, a reviewer had already chosen `חנה` on 2026-08-19, and
    Dicta and the VLM independently read `הנה` — a human holding one reading
    while two independent engines agree on another, which Lesson 9 says must not
    be buried. **On 2026-08-31T19:46 the reviewer ruled again and chose `הנה`.**
    The context now reads `…שלא ראיתיו עד הנה זה כמה שנים…` — `עד הנה`, "until
    now", the ordinary phrase. The ink decided, as item 0Q said it would.

    **klal 2 w316 was a confirm-no-change, and it settles item 57.** The decision
    chose `נ״ד` where the corpus already read `נ״ד` — byte-identical, checked at
    the codepoint level (`U+05E0 U+05F4 U+05D3`), not by eye. So the single
    remaining **U+05F4 GERSHAYIM in Part 1 is a deliberate reviewer ruling, twice
    over** (2026-08-30 and again 2026-08-31), not an oversight item 57 left
    outstanding. Item 57 should be read as *ruled and kept*, not *pending*.

    **Two other open items closed themselves and nobody had noticed.** Measured
    after the rebuild, not remembered:
    - **Item 26 is fully closed: 0 `&` remain corpus-wide** (item 37 recorded
      one survivor at klal 77 w11). It was resolved by the reviewer's own
      already-applied decisions somewhere between that sweep and now.
    - **`ligature_words.json`'s staleness is gone**: it now reports
      `both_lost: 0`, agreeing with the corpus, where item 37 caught it claiming
      3. Stage 5b regenerating it is what fixed that — the remedy item 43 put in
      place is working.

    Post-rebuild figures, all regenerated: `corrections_part1.json` **625 items
    across 148 klalim**; `lexical_defect_report.json` **271 candidates across 90
    klalim** (was 280/93); `klal_page_regions.json` **623 regions across 140
    pages** (610 marker-anchored, 13 heuristic); ligature census **176 distinct
    words / 2,631 occurrences**, 321 dropped-lamed, 18 dropped-alef, 0 both-lost,
    0 literal U+FB4F. Rebuild gate green (344), full suite **392 passed, 1
    skipped**.

1C. **[2026-08-31] S2 IS CLOSED — `corpus_io.words_of()` is now the one
    space-only split, and a test stops a new one being typed.** The finding had
    been open since 2026-08-25 across three reviews, and the reason it stayed
    open is that it kept GROWING: the 2026-08-31 sweep counted 12 sites and
    missed one written that same day (item 37(b) corrected the count to 27
    across 14 files). A finding that spreads faster than it is counted needs a
    gate, not another count.

    **Converted: 27 call sites in 14 files** — `apply_reviewer_decisions.py` (8),
    `review_server.py` (5), `audit_applied_decisions.py` (2),
    `propose_punctuation_part1.py` (2), and one each in `corpus_io.py`,
    `build_klal_page_regions.py`, `build_corrections_dataset.py`,
    `assemble_corrections_dataset.py`, `apply_punctuation_decisions.py`,
    `build_open_items_report.py`, `validate_part1_corpus_integrity.py`,
    `patch_witness_word_indices.py`, `list_ligature_words.py`. Count
    comparisons went to `word_count_of()`.

    **The direction matters, and the 2026-08-25 review had it backwards.** That
    review's remedy R3 says "the answer should be `.split()`". Following it
    would have invalidated the `word_index` of **every decision ever recorded** —
    a `word_index` in this project means an index into `clean_text.split(' ')`,
    because that is what the dashboard's click handler computes and what the
    ledger was written against. `str.split()` collapses whitespace runs and
    renumbers every word after a double space. The convergence went onto the
    scheme the data is already in. **This does not merge the two schemes**:
    machine candidate generation still uses `.split()` legitimately, because it
    diffs token streams instead of addressing stored positions. What ended is
    the *unmarked* use of the space-only split, where the two were told apart
    only by reading each call site and knowing which one it meant.

    **Verified as an identity, not assumed**: `words_of(k)` equals the raw split
    it replaced for **all 667 klalim / 188,744 word positions**, and 0 klalim
    have a double, leading or trailing space today — which is exactly why this
    was latent rather than live, and exactly why it would have gone live
    silently.

    **The gate: `test_no_new_raw_space_split_sites_appear_outside_corpus_io`.**
    AST-based, not grep — these modules discuss `.split(' ')` at length in
    comments and docstrings because the two-scheme distinction has to be
    explained somewhere, and a text search cannot tell an explanation from a
    call. Verified to FAIL on a newly-introduced site before being kept (a
    throwaway probe file), per Lesson 25. Two documented exemptions:
    `corpus_io.py` itself, and
    `second_witness_eval/run_part1_vlm_second_witness.py:61`, which splits a VLM
    ENGINE's output for a membership test and produces no word_index — a
    different question that happens to use the same operator.

    Suite: **377 passed, 1 skipped**. Server restarted and re-smoke-tested.
    Side effect worth noting: running `build_open_items_report.py` to read the
    queue rewrote the tracked `open_items_2026-08-31.json`; it is a derived
    report, so it now reflects current state rather than this morning's.

1B. **[2026-08-31] THE 2026-08-25/26/27 REVIEW BACKLOG IS CLOSED EXCEPT FOR THE
    THREE REFACTORS — nine findings fixed, seven new tests, and the multi-word
    guard turned out to be guarding the wrong thing.** Branch:
    `code-review-fixes-2026-08-31` (kept off `master` because a concurrent
    session is mid-flight on the Dicta work; nothing in that work is touched).
    Suite: **375 passed, 1 skipped, 376 collected** — collected count from
    `pytest --collect-only -q`, per Lesson 37, and it equals the declared count
    in every test file.

    **The one that was not just tidying.** `CODE-REVIEW-2026-08-27.md`'s remedy
    #2 says a multi-word manual replacement should "claim the per-klal-per-run
    slot", and item 37 recorded it as half-applied (present in
    `apply_reviewer_decisions.py`, absent from `export_corpus.py`). Applying it
    to the second file exposed that **the remedy as written does not prevent the
    corruption the finding itself describes.** Claiming the slot stops a second
    *word-count-changing* decision; the decision actually at risk is the
    ordinary *single-word* one that follows a shift. Normally
    `apply_manual_correction`'s drift check catches it — the word at the shifted
    index no longer equals `original_word`. It does **not** catch the case where
    the shifted-into position holds the SAME word: with a repeated word
    (`גימל גימל`), the check passes and the run rewrites the wrong occurrence,
    silently, with the reviewer's note attached to a word they never saw. The
    gate is now on **every** manual branch in both files. Live exposure when
    written: **0** — measured across every unapplied manual decision; one klal
    (74) has more than one and all three of its are word-count-changing, which
    the existing gate already handled.

    **And the premise both files stated was wrong.** Both say "0 multi-word
    manual replacements exist today (re-measured, not remembered)". **Klal 57
    w44 is one** — `לאורויילן` → `לאורויי לן`, recorded 2026-08-30T21:13,
    applied 21:19, and the corpus reads it as two words now. It went through the
    unguarded path. It did no damage (it was the only word-count-changing
    decision in its run, and the next klal-57 decision came a day later and sits
    at a lower index), but the earlier measurement evidently counted only
    unapplied decisions. Lesson 19: the claim was checked against a query, not
    against the log.

    **A test that could not fail, caught before it was committed.** The first
    version of the `export_corpus` regression test passed against the *pre-fix*
    file — the drift check alone produced identical output, so the test
    discriminated nothing (Lesson 25). Rewritten around the repeated-word case
    and verified to fail on `git show HEAD:tools/export_corpus.py` before being
    kept. **Any regression test written for this class must be run against the
    unfixed file first**; the guard and the drift check overlap almost
    everywhere, and the sliver where they don't is the entire finding.

    **Fixed, each verified live or by a test that fails without it:**
    S3's open half (the bbox cache key now stamps the DocAI page too, not only
    `part1/2/3.json` — a page re-extraction no longer serves stale boxes);
    **S4** (`_parts_for`/`_load_klalim` share one validator and raise
    `BadRequest`; `?part=4` is a **400 with a message**, live-checked, where it
    used to be a silent Part 1 — the two had also drifted, `_parts_for`
    accepting `none` and `_load_klalim` not); **S5/#6** (`PART2_MAX_KLAL=444`,
    `PART3_MAX_KLAL=667` and derived `*_MIN` constants in `corpus_io.py`, with
    two invariant tests — one asserting them against the live corpus and
    contiguity, one running `_get_part_num_for_klal` over all 667 klalim);
    **H3/#8** (`union_bbox()` → `corpus_io`, both copies now aliases);
    **H4** (both dead `extract_*_consensus_disputes.py` stubs removed — zero
    executable references, only prose, and `synthesize_multi_witness.py:7-23`
    already carries that history); **#18/#9** (one `clearWordFlag()` in
    `app.js`, both panels call it); **#7** (`FURNITURE_WORDS` imported from
    `corpus_io` directly); and **08-26 #2's unswept sibling**
    (`validate_suppression_filters.load_reference_freq` now delegates to
    `docai_filter.reference_frequencies()` — see item 37(d)).

    **Deliberately NOT done — the three genuine refactors, each wants its own
    session:** **C4** (four modules import `review_server`, five private-helper
    call sites — see item 37(a); an `scan_alignment.py` extraction closes three
    of five, the other two want a decisions/queue loader), **S1** (1,981 lines),
    **S2** (27 `.split(' ')` sites / 14 files, no `words_of()`). H2
    (`_NO_UPPER_BOUND = 10 ** 9`) left alone on purpose: replacing it with
    `PART3_MAX_KLAL` would change what those two alignment rows actually bound,
    which is a data-affecting change wearing a refactor's clothes.

    Review server restarted (rule) and smoke-tested: parts 1/2/3/all return
    222/222/223/667 klalim over the right ranges, `/api/klal/88` and
    `/api/page/73` 200, page latency 11.2 ms.

0Z2. **[2026-09-01] A crash in `compare_ocr_engines.py` on its DEFAULT path,
    introduced by yesterday's fix to the very blindness it was fixing.** Found by
    a peer `/code-review high` that was killed by a session rate limit before it
    could report — its last line was "now let me confirm the
    `compare_ocr_engines` crash end-to-end", which was enough to go looking.

    **The bug.** Finding F9 said the letter-frequency signature iterated the
    REFERENCE's alphabet only, so a letter an engine INVENTS was invisible — in
    the one signal credited with diagnosing fastocr as a hallucinating square
    model. The fix iterates the union and gives an invented letter a ratio of
    infinity. But JSON cannot carry infinity, so `evaluate()` stores it as
    `None` and sets an `invented` flag beside it — and the PRINT path then
    inferred "invented" by comparing the stored ratio back to `float("inf")`,
    which is `False` for `None`, and fell through to `abs(1.0 - None)`:
    **`TypeError`**.

    **It fires on the default.** `--letters` defaults to 6, so any candidate
    containing a Hebrew letter absent from the scored window crashes the tool.
    It never fired on this project's own runs because every Hebrew letter
    appears somewhere in a window of 10+ klalim — but the module's own docstring
    advertises reuse on "the next book", and a narrow window is exactly where an
    absent letter is normal. Reproduced deliberately: klal 9 alone has no
    `ג`/`ח`/`צ`; a candidate inventing `ג` crashes it.

    **Fixed** by sorting and labelling on the `invented` FLAG rather than the
    ratio — the flag is the contract, the ratio is not — with a gated test that
    asserts an invented letter sorts to the top and that the ordering key never
    touches `.ratio` for one. **Gate 362.**

    **The shape worth remembering:** a fix that adds a sentinel value has to
    make every consumer of that value agree on how to recognise it. I stored the
    sentinel one way (a flag plus `None`) and read it another (`== inf`), in the
    same function, on the same day.

0Y2. **[2026-09-01] A peer session's `/code-review high` on the docs commit —
    11 findings, all fair, plus a real seam defect in code I wrote today. One
    claim of my own retracted.**

    **The seam defect, verified myself.** `build_dicta_baseline.py`
    concatenated chunk files with no separator, and Dicta's outputs carry no
    trailing newline — so the last word of chunk N fused to the page marker
    opening chunk N+1 (`תורה=== עמוד 1 ===`), 4 seams, defeating the
    line-anchored `^===\s*עמוד.*$` strip and leaking 4 phantom `עמוד` tokens into
    the witness stream. Fixed (`rstrip("\n") + "\n"`), rebuilt, and a gated test
    now asserts every `===` begins its own line.

    **I MISREPORTED ITS IMPACT AND AM CORRECTING THAT.** I said the bug "had
    injected a false dispute" because the count moved 59 -> 58 after the fix. It
    had not. Running BOTH baselines against the SAME ledger gives identical
    disputes: **the seam fix changes nothing downstream.** The 59 -> 58 was the
    reviewer ruling klal 12 w74 (`ר"ס` -> `ר"פ`, agreeing with dicta+surya) in
    the interval — the same ledger-moves-under-the-measurement effect as klal 29
    w86 in item 0V. The defect is real and worth fixing; its published impact
    was zero. The peer hedged correctly ("could be an alignment artifact"); I
    over-read the hedge as confirmation.

    **Public-doc accuracy, both real:** `HOW-THE-PIPELINE-WORKS.md` was still
    publishing the pre-review 60-new/65-corroborated figures that item 0S
    retracted — and so was item 0P's own table, which is where the doc sourced
    them. Both now read 58/64/1. And `CASE-YAD-MALACHI.md`'s Przemysl correction
    **cited evidence it had just invalidated**: it kept the script claim on
    renders "of pages 30, 250, 400, 480", which are pages of `14122` — the file
    the same footnote reassigns to Jerusalem. The renders prove Jerusalem is
    Rashi-set and say nothing about Przemysl. Re-sourced to the project owner's
    determination of the editions, which also settles Livorno, Przemysl 1877 and
    1888 as Rashi and lets `[^p1888]` drop "unverified".

    **The rest, all fixed:** README presented Dicta as a shipped stage when item
    0Q says preview (`grep -i dicta` finds nothing in `rebuild_all.sh`);
    `START_HERE.md`'s TL;DR still named `VlmWitnessEngine` after item 0N flagged
    that exact line — Lesson 34, sibling unswept, and I swept only the README;
    "five printings, each inspected page-by-page" overstated what this project
    inspected; "the other printings are now readable" generalised from ONE
    measured edition, and the one this doc excludes as a text source; 97.8% and
    97.1% were mixed in a single comparison ("within half a point" holds only
    against 97.1); "barely helped (41% -> 39%)" described a FALL as a small
    help; and `[^dicta]` pointed at comparison tables that are deliberately
    untracked — now points at the tracked baseline instead.

    **Item-ID collisions are now a written rule, not a repeated cleanup.** See
    the note at the head of Open Items: `0x` is the review lane, `1x` the
    refactor lane. The peer's three colliding entries moved to `1G`/`1H`/`1I`
    rather than mine, because code references `item 0W`/`0U`/`0R` by name and a
    rename there breaks a comment that a test relies on for its reasoning.

0X. **[2026-09-01] Outward-facing docs reviewed. One FACTUAL ERROR corrected,
    one legal separation that was missing, and four stale counts.** The public
    set is six files, not the three named: `CASE-YAD-MALACHI.md`,
    `CORPUS-COMPARISON.md`, `COMPETITIVE-LANDSCAPE.md`, plus
    **`HOW-THE-PIPELINE-WORKS.md`** (the case doc's own companion),
    **`VERIFIED-AGAINST-THE-INK.html`** (the evidence showcase) and
    **`README.md`** (the front door, and the stalest of the lot).

    **The factual error.** `CASE-YAD-MALACHI.md`'s `[^p1877]` listed HebrewBooks
    **#14122** as a second scan of Przemysl 1877. It is **Jerusalem 1975/6** —
    the same mistake I made on 2026-09-01 and the reviewer corrected (item 0O),
    made independently by whoever wrote that footnote, and for the same reason:
    #14122's HebrewBooks metadata mis-catalogues it as `פרמישלה תרלז` and its
    approbations genuinely are from Przemysl, so a reader who checks a nearby
    page rather than the title page finds "Przemysl" and stops. The **script**
    verification stands (pages 30/250/400/480 rendered, Rashi-bodied); the
    imprint did not. The two-independent-scans claim is withdrawn rather than
    re-asserted, since I have not re-verified the Google Books one.

    **The separation that was missing, and it matters for a doc whose core claim
    is "public domain, nothing to license".** The edition this pipeline is now
    OCRing is a **1975/6 printing** advertising `עם הוספות` — added matter,
    including Ramchal's `דרכי התלמוד` set before the text. The underlying work is
    PD and mechanical OCR of it carries no new copyright, but modern editorial
    additions are not covered by that. Both docs now state the rule this project
    actually follows: **Berlin 1851/2 is the SOURCE; every other printing is a
    WITNESS.** A witness's readings route a reviewer to a position in the Berlin
    text; none of its words are ingested. Stated as what this project does, not
    as legal advice.

    **The strengthening, which is the reason this was worth doing now.** Until
    this week only ONE of the five printings was machine-readable, so "a second
    edition" was an aspiration - the weakest joint in the "nobody has to trust
    the machine" argument, because every witness was reading the same ink and
    they fail together on a worn sort (37 measured cases). Dicta at 95.5% turns a
    Rashi printing into a real second edition. Both docs now say so, with both
    caveats attached: the 95.5% is scored against a DIFFERENT edition so genuine
    variants count against it and it is a floor, and the same engine reads the
    square Berlin scan at 77.6% and must never be pointed there.

    **Stale counts corrected** (measured, not remembered): README `552 of 667` ->
    **596**, `~179,000 words` -> **~188,500**, `115 placeholders` -> **71**,
    `31 numbered lessons` -> **37**; HOW-THE-PIPELINE-WORKS `595` -> **596**,
    `72 placeholders` -> **71**, `318 tests / 282 gating` -> **409 / 360**.

    **Two things fixed that were wrong in kind, not just out of date.** The
    README's architecture line named `VlmWitnessEngine`, which no stage of
    `rebuild_all.sh` imports (item 0N) — replaced with what the pipeline
    actually does. And its status block quoted `1,061 flagged — 356
    machine-resolved, 997 open, 64 decided`, three numbers that **do not sum to
    the total** and go stale every session; replaced with a pointer to the
    dashboard, which is the discipline `PROJECT-STATUS.md` already applies to
    itself.

    **`CORPUS-COMPARISON.md` needed nothing.** It is a citation-demand survey,
    untouched by anything measured this week, and it already states its own
    limits (the top-250 verification floor, the snapshot caveat, and an explicit
    "cannot establish who ranks #2"). **`VERIFIED-AGAINST-THE-INK.html` NOT
    reviewed** — 2.7 MB of generated showcase, and it predates every measurement
    above; whether its worked examples still match the corpus is unchecked.

0W. **[2026-09-01] Dicta's OCR output is now the ONLY witness baseline not in
    version control, and it is the only one that cannot be regenerated on
    demand.** `b46dcde` untracked `dicta_output/` and the comparison tables. The
    reasoning is good and the problem was mine: `b9aa810` put ~7,100 lines of
    machine output into the tree and pushed a code review over its size budget.
    Working copies stay on disk, and the blobs remain recoverable from history.

    **The asymmetry, though:**

    | baseline | tracked | cost to regenerate |
    |---|---|---|
    | `surya_part1_full_baseline.txt` | **yes** | local, zero marginal cost |
    | `vlm_part1_full_baseline{,_passB}.txt` | **yes** | paid API we control |
    | `dicta_output/…` | **no** | free third-party service, **rate-limited, refusing us today** |

    The one output that is expensive and outside our control is the one not
    kept. For pages 22-50 this is fine - they are in history at `b9aa810`. **The
    real exposure is pages 51-114**: when they arrive they will be untracked
    from the start, so they will never enter history at all, and losing them
    means re-queuing against a service that is already saying "wait".

    **DONE 2026-09-01, on the reviewer's approval.** The per-chunk
    intermediates stay untracked; the single concatenated baseline is now
    tracked as `tools/second_witness_eval/dicta_jerusalem_part1_baseline.txt`,
    beside the Surya and VLM baselines it is the peer of. The diff-size fix
    stays intact — one file, not thirteen.

    **Built by a script, not a `cat`.** `tools/build_dicta_baseline.py` reads
    the chunk manifests and concatenates in PAGE order. That is not ceremony:
    the calibration chunk is `c0001` in its own manifest and covers pages 29-32,
    which falls INSIDE the range another manifest's `c0001` covers, so ordering
    on chunk id or filename interleaves the book. It also **refuses to write on
    a gap or an overlap** — a missing page silently drops text from the middle
    of the baseline and a repeated one duplicates it, and either would surface
    downstream as a mystifying alignment failure rather than an error. Three
    gated tests; 360 passing.

    The file carries an ASCII header naming its page coverage and saying
    **PARTIAL**, so it cannot be quoted as full Part 1 while it stops at page
    50. That is safe only because every consumer tokenizes to Hebrew-bearing
    words, which is asserted by a test rather than assumed. Verified the
    tracked path reproduces the untracked one exactly: identical klal
    segmentation, identical 16,392 tokens, identical 124 dispute URLs.

    **When pages 51-114 land**, drop the outputs in `dicta_output/`, mark them
    done in `dicta_chunks_remainder/manifest.json`, and re-run the builder — it
    will refuse if a chunk is missing rather than quietly producing a
    short baseline.

0V. **[2026-09-01] DICTA IS DETERMINISTIC — same PDFs, second run, BIT-IDENTICAL
    output. It therefore needs no stability gate, and can never be its own
    reliability check.** The reviewer re-submitted pages 22-50 by mistake; the
    accident is a free repeatability measurement this project would not
    otherwise have paid for.

    | | |
    |---|---|
    | all 5 chunk outputs, run 1 vs run 2 | **byte-identical** (md5 each) |
    | concatenated baseline | byte-identical |
    | word accuracy / CER / lexicon hit | 95.5% / 3.8% / 96.7% — unchanged |
    | dispute URLs, positions and order | **identical, all 124** |
    | verdicts | 59 new / 64 corroborated / 1 escalation / 0 contested — unchanged |

    **The one number that moved, and why it is a good sign.** Agreement with the
    corpus went **15,075 -> 15,076**. Not Dicta drifting: `part1.json` moved
    under it. Commit `6d956ae` applied the klal 29 w86 ruling, `חנה` -> `הנה`,
    and Dicta had read `הנה` there all along — so a position where it previously
    DIFFERED now AGREES. The corpus caught up with the witness. That is the same
    position item 0Q flagged as the Lesson 9 case, closing the loop end to end:
    engine proposes, reviewer rules, agreement rises by exactly one.

    **What this changes architecturally.** The VLM needs Pass A/Pass B as a
    STABILITY GATE because it is not deterministic (87.43% self-consistency,
    Lesson 23) — where its two passes disagree, it abstains. **Dicta needs no
    such gate**: a second pass would abstain nowhere, so wiring one would burn
    requests against a free service for zero information.

    **The flip side, and it is the more important half.** A repeat Dicta run
    buys literally nothing — it cannot serve as its own reliability check the
    way the VLM's can. Determinism is repeatability, NOT correctness: Dicta
    reproduces its mistakes exactly as faithfully as its successes. Every one of
    the 59 disputes still needs a second, genuinely different signal or the ink.
    Lesson 23's rule holds with the sign flipped — running this witness twice
    buys no independence *because there is nothing to learn from the second
    run at all*.

    **Scope of the claim.** Same PDFs, same service, same day. It shows the
    endpoint is deterministic for identical input; it says nothing about
    stability across a future model update on Dicta's side. If the remaining
    pages 51-114 are ever re-run months apart, that is the measurement that
    would test it.

0U. **[2026-09-01] THE 75 AUDIT MISMATCHES ARE NOT LOST CORRECTIONS. 72 were
    index drift, 3 are benign, and ZERO corrections are missing from the
    corpus.** `audit_applied_decisions.py` reported **75 of 494** applied
    decisions "no longer reflected in the corpus", which reads as serious
    corpus damage. Investigated; it is not.

    **First, it is not a regression.** Built a throwaway worktree at `49cb6ad`
    and ran the audit there: **75 before** the two 2026-09-01 apply commits,
    **75 after**. Those commits added 2 applied decisions and 0 mismatches.

    **The cause is Lesson 35, pointed at the auditor itself.** Applying a
    correction shifts every later index in that klal - `apply_reviewer_
    decisions.reindex_flags_after_shift()` exists precisely because of it - but
    a DECISION record keeps the `word_index` it was written with. The auditor
    compares at that stale index and calls a hit elsewhere a mismatch. Measured
    offsets: **-11 ×1, -3 ×12, -1 ×28, +1 ×26, +2 ×2**. The corrected text is
    in the corpus in every one of those cases.

    **FIXED: the auditor now classifies instead of lumping.** A failed exact
    check is followed by an EXACT search for the same span elsewhere in the
    klal - drift is reported as "reflected, but at a SHIFTED index", separate
    from a real mismatch. **Deliberately not fuzzy** (Lesson 5): the check at
    the decision's own index still passes or fails on its own, and a near-miss,
    a substring or a word that is genuinely gone all stay MISMATCH. Gated tests
    pin exactly that. **75 -> 3.** This matters beyond tidiness: the script's own
    code carries the note that "a check that routinely fires on correctly-applied
    data is a check people learn to scroll past", and it had become one.

    **All 3 survivors are benign, each read to the bottom:**
    * **klal 1 w97** - `punctuation_choice '[.]'` noted "e2e test accept",
      applied, then deliberately reverted by a later `punctuation_choice`. This
      is the exact precedent named in the auditor's own module docstring as the
      reason it exists. Working as designed.
    * **klal 66 w29** - `manual_correction 'מהדיא'` applied, then
      `disputed_choice 'מההיא'` applied. The corpus has `מההיא`, which is the
      CORRECT reading (`ולמדתי כן מההיא דמשנינן`).
    * **klal 39 w242** - `manual_correction 'ור'` applied (its `chosen_text`
      dropped the geresh the note itself specifies: `זר' w242 → ור'`), then
      `disputed_choice "ור'"` applied. Corpus reads
      `ורב מרבי חייא ור' חייא מרבי`. Correct.

    **RULED BY THE REVIEWER 2026-09-01 — "widen it across the three replacement
    types" — and done.** `is_superseded_by_later_applied()` now resolves
    supersession across `REPLACEMENT_TYPES` = `candidate_choice` /
    `disputed_choice` / `manual_correction`, and `punctuation_choice` keeps
    being checked against its own type alone, because an accepted one INSERTS a
    `[.]` and shifts rather than overwriting — letting it suppress a
    replacement would mask a genuinely reverted correction, which is the one
    case this script exists to catch. **The audit now reports 1 MISMATCH**, and
    it is klal 1 w97, the deliberately reverted e2e-test artifact that MUST
    keep firing. Verified in both directions: klal 66 w29 and klal 39 w242 are
    gone; klal 1 w97 remains.

    `test_supersession_does_not_leak_across_keys` asserted the old scoping on
    purpose, so it was **rewritten rather than deleted**, into three tests that
    state the new rule and its boundaries: a later decision at a DIFFERENT word
    still never suppresses; a later applied REPLACEMENT at the same word now
    does; a later UNAPPLIED decision still does not (the klal 1 w97 case); and
    a `punctuation_choice` never suppresses a replacement. Gate 351.

    **The superseded history, for the record.** The
    last two are the same shape: a `manual_correction` superseded by a later,
    also-applied `disputed_choice` AT THE SAME WORD.
    `is_superseded_by_later_applied()` scopes supersession to the same
    `(klal_id, word_index, decision_type)` key, so it does not see them, and
    `test_supersession_does_not_leak_across_keys` asserts that scoping ON
    PURPOSE. I tried widening it, the test failed, and I reverted rather than
    edit a deliberate assertion in corpus-integrity tooling. **The case for
    widening:** two decisions replacing the same word describe the same word
    whatever type recorded them, and a later applied one legitimately moved the
    corpus past the older claim - which is what supersession means.
    **The case against, and why it cannot be a blanket widening:**
    `punctuation_choice` INSERTS and shifts rather than overwrites, so it must
    never suppress a replacement decision. Any fix should widen across the three
    REPLACEMENT types only (`candidate_choice`/`disputed_choice`/
    `manual_correction`) and update that test's third assertion with the
    reasoning. **Needs the reviewer's ruling.**

0T. **[2026-09-01] The four new tools now have gated tests — and the two
    number-changing defects were both in logic no test could reach.**
    They shipped with zero coverage, and every check I ran on them (a
    falsifiability probe, a 2-2 split reproduction, a manifest merge, the
    fetch-script guards) lived in throwaway scratchpad scripts. Lesson 32:
    nothing would have caused any of it to run again.

    **13 tests added to `tests/test_pipeline_logic.py`** — the gated,
    synthetic-input file — covering `classify`, `consensus_of`, `to_visual`,
    `rtl`, `chunk_ranges`, `confusion_pairs`, `word_alignment`,
    `char_error_rate`, its size ceiling, the letter-ratio union, and
    `trim_to_reference`. Gate is now **342 collected, 342 passed**.

    **A refactor the tests forced, and it is the point.** Both defects lived
    inside `collect()`'s loop over the real corpus, where no synthetic test
    could reach them — so the whole judgement is now `classify(readings,
    stored_norm, label, decided_choice)`, returning one of `new` / `joins` /
    `contested` / `escalation` / `settled` / None. Output is byte-identical
    before and after (59/64/1/0).

    **Verified the tests can actually fail** (Lesson 25 turned on my own
    tests): reimplemented the shipped-in-`b9aa810` classifier and ran the new
    cases against it — a 2-2 split returned `joins` where the test demands
    `contested`; a human-ruled position returned `new` where the test demands
    `escalation`; a human agreeing with the engines returned `new` where the
    test demands `settled`. **All three fail against the old code and pass
    against the new.** A test that cannot fail would have pinned nothing.

0S. **[2026-09-01] `/code-review high` on the session's four new tools — 10
    findings, ALL TEN REAL, and two of them changed published numbers.** The
    review agent had failed on a rate limit the night before, so the tools had
    shipped on my own review only; this is what an independent pass found.

    **Two that moved numbers, both verified before fixing:**
    * **A human-ruled position was counted as a new dispute.**
      `synthesize()` skips a decided position entirely; the preview annotated it
      and counted it anyway. 60 new / 65 corroborated became **59 / 64 / 1**.
    * **A 2-2 engine split was filed as "corroborated."** `without`/`with_it`
      were compared for None-ness but never for the same READING, so a witness
      forming a SECOND consensus on a DIFFERENT reading landed under a heading
      asserting it agreed with the dispute it contradicts. Reproduced
      synthetically; **0 occurrences in the shipped data**, so nothing published
      was wrong — a landmine, not an error.

    **One found only because the fix was tested, not because the review said
    so:** scoping escalations by `(kid, wi) in decided` alone swept in 4
    pre-existing `surya+vlm` escalations Dicta had no vote in — a report about
    the queue, not about what this witness adds. Now requires
    `label in with_it[1]`.

    **And one the data answered on its own:** klal 29 w86 — the Lesson 9 case
    item 0Q flagged, corpus `חנה` against `dicta+vlm` reading `הנה` — **was ruled
    by the reviewer during the session, in the engines' favour**
    (`review_decisions.jsonl` gained it mid-run). It correctly drops out as
    "human agreed with the engines".

    **The other eight, all fixed and each with its check:**
    `.split()` where the repo means `cio.words_of()` (space-only; **0 of 222
    klalim differ today**, so every committed link was right — but this is the
    exact class finding S2 swept 27 sites for, one commit earlier);
    `python-bidi` absent from `requirements.txt` while backing the DEFAULT code
    path, imported after the full corpus alignment so a fresh clone burned the
    run then died (now module-scope + listed); `IndexError` instead of a message
    when a witness anchors nowhere; `fetch_dicta_result.sh` printing `OK` and
    exiting 0 on a failed `mv`, and accepting any non-empty 200 — an HTML error
    page would have been saved as a "successful" OCR result (both now guarded,
    and the Hebrew guard itself false-positived on first write because `\xd7` in
    a BRE is the literal text, fixed with `$'...'`); the chunker rewriting
    `manifest.json` wholesale so a second partial run destroyed run 1's resume
    state — **which this repo had already hit and repaired by hand** (now merges
    by page range and refuses a different source PDF); CER quadratic with no
    ceiling, and not comparable across engines with different in-window
    coverage (now capped, and the offenders carry a ⚠ with an explanation);
    the letter-frequency signature iterating only the REFERENCE's alphabet, so a
    letter the engine INVENTS was invisible — in the one signal credited with
    diagnosing fastocr as a hallucinating square model (now the union);
    `detect_span`'s `min_block=3` able to widen a window on a 3-token
    coincidence (now 8, and it prints its anchors).

    **The lesson worth keeping:** eight of the ten were in code that had passed
    my own review the same evening, and the two that moved numbers were both in
    classification logic that "looked obviously right". A tool that reports
    counts needs its CLASSIFICATION tested, not just its arithmetic.

0R. **[2026-08-31] Hebrew in generated Markdown needs EXPLICIT bidi isolation —
    the repo already knew this for HTML and the knowledge did not travel.**
    Reviewer-reported: `DICTA-NEW-DISPUTES.md` rendered its Hebrew backwards.
    Cause: a Markdown file is an LTR-base document with no stylesheet, so a bare
    Hebrew run reorders against the Latin, digits, URLs and punctuation beside
    it — and in a table row of `| url | 5 | 86 | כ"ר |` there is a lot of that.

    **The repo had already solved this, in CSS.** `review_frontend/app.css` uses
    `direction: rtl; unicode-bidi: isolate` in four places, one with the comment
    "keep the Hebrew from reordering the LTR row"; `tools/render_report.py` sets
    the same on `.heb`. First attempt: `U+2067 RIGHT-TO-LEFT ISOLATE` …
    `U+2069 POP DIRECTIONAL ISOLATE` around every Hebrew run — the character
    form of that CSS rule.

    **THAT DID NOT WORK, and the reason is the useful part.** Reviewer: "still
    has heb rev in md." **Measured, not assumed: `glow` does no bidi at all.**
    Fed `abc כותב xyz`, its output carries the Hebrew byte-for-byte as it read
    it — KAF,VAV,TAV,BET in, KAF,VAV,TAV,BET out. It expects the TERMINAL to run
    the Unicode bidi algorithm, and the terminals in use here do not. So logical
    order displays backwards and **the isolates are inert, because nothing reads
    them.** There is no Markdown-level fix for a renderer that implements none
    of the algorithm; the only remaining lever is the character order itself.

    **FIXED with a `--hebrew visual|logical` mode**, default `visual`, which
    bakes the reordering into the bytes using `python-bidi`'s implementation of
    the real algorithm (already installed here) rather than a hand-rolled
    reverse — naive reversal mishandles gershayim, embedded digits and Latin,
    and this text is full of `דף ג' ב'`. Base direction stays `L`, so URLs and
    ASCII are provably untouched. **The cost is real and is stated in the
    file's own header: Hebrew copied out of a visual-order file pastes
    REVERSED.** `--hebrew logical` regenerates the canonical, copy-safe form for
    any bidi-aware reader (Chrome, GitHub, VS Code).

    **The general rule this settles:** which order is correct depends entirely
    on whether the CONSUMER implements bidi, and that is a property of the
    reader, not of the file. A Hebrew artifact aimed at a terminal and one aimed
    at a browser cannot be the same bytes.

    **A SECOND defect in the same file, same root: MARKDOWN TABLES DESTROY BOTH
    THE LINKS AND THE HEBREW.** Reviewer-reported ("glow is word-wrapping the
    first column - which breaks the link functionality"). Measured with
    `glow -w 80`, which is how these files actually get read:

    ```
     http://127.0.0.1:8420/klal/5/word/8 | 5 | 86 | ⁧כ"ר⁩ | ⁧כ"ד⁩ (dicta+surya+vlm)
     6                                   |   |    |     |
     http://127.0.0.1:8420/klal/5/word/2 | 5 | 27 | ⁧וככ | ⁧ובכתובות⁩
     79                                  |   |  9 | תוב |
    ```

    The URL is wrapped MID-STRING, so it is neither clickable nor copyable, and
    the same narrow cells chop Hebrew words into vertical fragments. **FIXED by
    a layout rule, not a tweak: no URL ever shares a line with anything else,
    and the file has no tables at all.** Verified at 50/60/80/120 columns.
    A bare `--urls-out` list is emitted alongside for piping. Options tested and
    rejected: `[text](url)` (glow does emit OSC-8 hyperlinks, but prints the raw
    URL beside the label, so it is no shorter); shortening to `127.0.0.1:8420/…`
    (still wraps once other columns exist, and relies on the terminal
    auto-linking a schemeless string).

    **SWEPT AND FIXED 2026-09-01 — the same defect was in the SHARED renderer.**
    `tools/render_report.py` carries both paths, and the asymmetry was exact:
    `render_html()` sets `direction:rtl;unicode-bidi:isolate` on `.heb`, and
    `render_markdown()` had nothing. So every Markdown report it has ever
    written displayed its Hebrew backwards in the terminal they are read in -
    `cleared_flags_2026-08-26.md` (39 rows), `open_items_2026-08-31.md` (242
    mixed lines), and anything else rendered through it. **`render_markdown()`
    now takes the same `--hebrew visual|logical` option**, defaulting to visual,
    and **HTML is explicitly excluded** — it has a real bidi engine and
    pre-reordered characters would double-reverse. Two gated tests pin exactly
    that asymmetry. `cleared_flags_2026-08-26.md` regenerated.

    **One file deliberately NOT regenerated:** `open_items_2026-08-31.md`. Its
    source `.json` is being edited by a concurrent session right now, and
    regenerating a derived report from a half-written source is how stale
    artifacts get made. It needs one `python3 tools/render_report.py
    open_items_2026-08-31.json` once that settles.

    **The older lesson still stands.** Every Hebrew-bearing artifact this
    project emits into an LTR container needs this, and every link-bearing one
    needs the no-tables rule. **STILL NOT SWEPT** — `tools/export_corpus.py`'s plain-text
    export, `open_items_*.md`, `cleared_flags_*.md` and any other generated `.md`
    carrying Hebrew have the same exposure and have not been checked. Whoever
    picks this up: the check is whether Hebrew ever shares a line with Latin,
    digits or a URL, not whether the file "looks fine" in one viewer.

0Q. **[2026-08-31] THE 60 NEW DISPUTES ARE NOW A REVIEWABLE ARTIFACT —
    `DICTA-NEW-DISPUTES.md`, one dashboard link per position. Still a PREVIEW;
    nothing written into the pipeline.** Generated by the new
    `tools/preview_dicta_disputes.py`, which reuses `synthesize_multi_witness`'s
    own loaders and vote rules rather than re-deriving them, so a preview cannot
    drift from what stage 4a would actually emit. It reproduces the dry run
    exactly, which is the consistency check.

    **NUMBERS CORRECTED 2026-09-01 by a `/code-review high` pass — the first
    figures were 60 new / 65 corroborated and both were wrong.** The preview
    counted positions a human had already ruled on, which
    `synthesize_multi_witness.synthesize()` never emits as disputes (it breaks
    out of them). **The honest figures are 59 new, 64 corroborated, 1 human-ruled
    escalation, 0 contested.** The gap was small but the entry claimed parity
    with stage 4a, and that claim is what makes the numbers quotable.

    Links use the PATH form `/klal/<id>/word/<index>`, not the `#klal=N&word=M`
    hash form, because `&` gets truncated when a link is pasted into a terminal
    or a chat window — `review_frontend/app.js` already made that choice for its
    copy button and this follows it. **Verified live**: the first three 302 to
    the hash route off the running server, they are not constructed strings
    nobody tried.

    **What they are made of:** 33 `dicta+surya`, 27 `dicta+vlm`, **0
    `dicta+docai`**, across 23 klalim. No position is carried by Dicta alone —
    the two-distinct-engines rule is doing its job, and the absence of a
    docai pairing is expected (DocAI's vote comes from the candidate queue,
    which is already in the reviewer's hands).

    **ONE POSITION NEEDS A HUMAN BEFORE ANY OF THE OTHERS — klal 29 w86.** The
    corpus reads `חנה`, a reviewer **already ruled** and chose `חנה`, and Dicta
    and the VLM independently read `הנה`. Context: `…שלא ראיתיו עד חנה זה כמה
    שנים…`, where `עד הנה` ("until now") is the ordinary reading and `חנה` is
    not. This is exactly the case Lesson 9 says must not be buried: a human
    choosing one thing while two independent engines agree on another. The
    preview marks it and does not hide it. **Not applied** — the ink decides.

0P. **[2026-08-31] DICTA RUN AGAINST THE JERUSALEM EDITION — 29 of 93 Part 1
    pages done (klalim 1–63), 95.5% word accuracy, and the run was HALTED
    DELIBERATELY when the service started refusing uploads.**

    Submitted through <https://rashiocr.dicta.org.il/> in the browser, one file
    at a time, per item 5's standing rule. Chunker: `tools/chunk_pdf_for_ocr.py`.
    Collector: `tools/fetch_dicta_result.sh`. Manifest with job ids and
    per-chunk status: `dicta_chunks/manifest.json`. Output: `dicta_output/`.

    **Measured on what came back — this is the real number, not the sample's.**

    | scope | ref tokens | word acc. | CER | lexicon hit |
    |---|---:|---:|---:|---:|
    | calibration, klalim 13–22 | 1,505 | 94.9% | 2.8% | 99.0% |
    | **klalim 1–63 (pages 22–50)** | **16,304** | **95.5%** | **3.8%** | **96.7%** |
    | _corpus ceiling, same window_ | 16,304 | 100% | 0% | 97.1% |

    **301 DPI was not a handicap.** The calibration chunk matched the
    higher-resolution Google sample point for point (94.9% vs 94.8%, 99.0% vs
    98.5% lexicon), and the full 63-klal run came in HIGHER at 95.5%. Item 0O's
    resolution worry is answered: it was worth checking and it was not a problem.

    **The witness dry run, re-run at 6x the scale — it supersedes item 0N's
    extrapolation.** Klalim 2–62, 16,177 corpus words:

    | | 10-klal dry run (0N) | **61-klal, real data** |
    |---|---:|---:|
    | alignment coverage | 94.5% | **95.4%** |
    | agrees with corpus | 97.4% | **97.7%** |
    | corroborates existing disputes | 8 of 11 (73%) | **65 of 83 (78%)** |
    | NEW disputes created | 4 | **60** |

    **SUPERSEDED — these two rows are the pre-review figures.** The 60/65 counted
    a position a human had already ruled on, which `synthesize()` never emits
    (item 0S). Corrected: **58 new / 64 corroborated / 1 human-ruled escalation**
    (58, not 59, after the reviewer ruled klal 12 w74 on 2026-09-01). Quote those.

    **0N extrapolated ~130 new disputes across Part 1; the honest figure is
    ~218** (60 per 61 klalim x 222). The small sample under-counted by ~60% —
    exactly why Lesson 27 says label an extrapolation as one. Corroboration held
    up and improved. The new disputes have NOT been hand-checked; the 4 from the
    small run were, and all 4 were real corpus errors.

    **WHY THE RUN STOPPED, and it is not a bug to fix by retrying.** After five
    chunks went through quickly, chunk 5 (pages 51–56) failed its Uppy upload
    twice in a row (`העלאה נכשלה`, `קובץ 0 מתוך 1 הועלה`). Five rapid
    submissions is the most plausible cause. The run was halted rather than
    retried a third time — the user's directive is "be CERTAIN to not flood this
    url," and a service refusing uploads is the signal that rule exists for.
    **Resume slowly**, minutes apart, not seconds.

    **CONFIRMED BY THE REVIEWER 2026-08-31, independently of this automation:**
    "i get an error as well when i try to upload to dicta. it is saying to
    wait." So the refusal is the SERVICE rate-limiting, not a browser-automation
    artifact, and halting the run was the correct read rather than a lucky one.

    **RE-CHUNKED for a lower request count, at the reviewer's direction.** The
    remainder is now **5 files, not 11**: pages 51-63, 64-76, 77-89, 90-102,
    103-114 — 13 pages and ~0.5 MB each, in `dicta_chunks_remainder/` with its
    own manifest. Fewer, larger requests is the right trade against a
    per-request limit, and the calibration chunk showed 4 pages processing in
    under 15 seconds, so 13 is not a long job at their end. `dicta_chunks/`
    now keeps only the 4 completed chunks, as the record of pages 22-50.

    **Browser-automation note for whoever resumes:** the email field does not
    reliably accept synthesized keystrokes (~3 of 7 attempts landed). What works
    every time is setting the value through the native `HTMLInputElement` value
    setter plus an `InputEvent`/`keyup`/`change` dispatch, then clicking
    `שליחה`. Always assert the send button is enabled BEFORE clicking it — that
    guard is what stopped a chunk being submitted with an empty address.

0O. **[2026-08-31] THE FULL RASHI EDITION IS IN THE REPO, AND IT IS JERUSALEM
    1975/6 — NOT Przemysl, and NOT the scan the 94.8% was measured on.**
    `yad-malachi-jerusalem-rashi-Hebrewbooks_org_14122.pdf`, 491 pages, 19.5 MB,
    user-supplied. Settled on its own title page after I first mis-called it
    Przemysl off an approbations page (the haskamos ARE from Przemysl; the
    imprint is not - the reviewer corrected this, and the title page is the
    authority. Lesson 17's shape: render the page that actually carries the
    claim, not a nearby one).

    **Title page, verbatim structure:** `נדפס מחדש בעיה"ק ירושלים תובב"א שנת
    תשל"ו` = newly printed, Jerusalem, 5736 = **1975/6**. Its own printing
    history names all four: `נדפס ראשונה בליוורנו בשנת תקכ"ז, ופעם שנית בברלין
    בשנת תרי"ב, ופעם שלישית בפרעמישלא בשנת תרל"ז` — Livorno 5527 (1766/7),
    Berlin **5612**, Przemysl 5637 (1877), then this fourth. **That
    independently corroborates START_HERE's Berlin dating of תרי"ב = 1851/2,
    from a different edition's own title page** — a fourth witness to a date
    that previously rested on two chronograms inside the Berlin book plus the
    NLI catalogue.

    **HebrewBooks' own metadata is wrong about it**, which is where my error and
    the repo's came from: the PDF's keywords read `פרמישלה תרלז` (Przemysl
    1877). `tools/second_witness_eval/README.md` inherits that — it lists
    `~/Downloads/Hebrewbooks_org_14122.pdf` as "Przemysl 1877". Two corrections
    needed there: the imprint, and the path (both `~/Downloads` Rashi files
    named in that README are **gone**; this one now lives in the repo).

    **It is a COMPILATION, not just Yad Malachi.** The title page advertises
    `עם הוספות`, and doc index 18 is Ramchal's `דרכי התלמוד` — added works sit
    in front of the text. Feeding chunks from page 1 would push dozens of pages
    of other authors through a free service for nothing.

    **Located the body locally, at zero cost to Dicta**, by anchoring the PDF's
    embedded HebrewBooks fastocr layer against `part1.json`. fastocr is the
    44%-accurate text this project already rejected for transcription (item 6) —
    it is entirely adequate for ANCHORING, which is a different question:

    | | |
    |---|---|
    | Yad Malachi body begins | doc index 21 (1-based page 22), klal 1 |
    | Part 1 (klalim 1–222) spans | 1-based pages **22–114**, 93 pages |
    | klalim 12–22 (the sample's own range) | doc 28–31 = pages **29–32** |
    | full Part 1 at 6 pages/chunk | **16 chunks** |

    **THE 94.8% DOES NOT TRANSFER TO THIS FILE UNMEASURED.** The Dicta Rashi
    sample is a *Google* digitization (it carries a "Digitized by Google"
    banner); this is HebrewBooks. **0 of the sample's 4 page images appear
    anywhere in this PDF** — they are two different scans of two different
    printings. And the resolution differs: sample **~403x473 DPI**
    (3424x5200 px), this file **301 DPI** (1612x2570 px). 301 DPI is at the
    threshold this repo's own Surya baseline runs at, so this is a reason to
    calibrate, not to reject — but quoting 94.8% for this file would be quoting
    a measurement of a different scan.

    **Calibration chunk built, nothing sent:**
    `dicta_chunks_calibration/yadmalachi-jer-calib_c0001_p0029-p0032.pdf`,
    4 pages, 0.16 MB, klalim ~11–23 — the same klalim as the sample, so its
    result is directly comparable to both the sample and the corpus.

0N. **[2026-08-31] DICTA-AS-WITNESS DRY RUN — measured before building
    anything, and it moved the design. Also: `AbstractWitnessEngine` IS DEAD
    CODE, so the integration everyone has been naming is the wrong door.**

    **The wrong door, first.** `tools/second_witness_eval/README.md` names the
    next step as "wire Surya in as a permanent `AbstractWitnessEngine`
    implementation", and the 2026-08-31 Dicta report repeated that for Dicta.
    Checked: `pipeline/second_witness_eval/` is imported by exactly two things -
    `tests/test_witness_engine.py` (5 tests, outside the gate) and
    `tools/second_witness_eval/run_part1_vlm_second_witness.py` (a standalone
    one-off). **No stage of `rebuild_all.sh` touches it.** The live witness path
    is baseline `.txt` -> `synthesize_multi_witness.py` (stage 4a) ->
    `assemble_corrections_dataset.py` (stage 4) -> server -> `app.js`. And the
    ABC could not carry Dicta anyway: `transcribe_region(pdf_path, page_num,
    bbox)` is crop-based against `berlin_square_corrected.pdf`, while a
    Rashi-edition witness has a different PDF, different pagination and no
    shared bbox. START_HERE's TL;DR also calls `VlmWitnessEngine` the secondary
    witness engine; the VLM's real contribution is its baseline text file.

    **The dry run** (harness in the session scratchpad, wrote nothing): klalim
    13-22, the 10 the Rashi sample fully covers, 1,549 corpus words.

    | | |
    |---|---:|
    | positions where Dicta gets a vote (1:1 alignment) | 1,464 / 1,549 (94.5%) |
    | …agreeing with the corpus | 1,426 (**97.4%** of its votes) |
    | …differing | 38 (2.6%) |
    | existing consensus disputes in scope | 11 |
    | …Dicta **corroborates** | **8 (73%)** |
    | NEW disputes Dicta would create | **4** |

    **All 4 new disputes hand-checked - none is edition noise.** klal 13 w18
    `אכל`->`אבל` (the corpus reads "ate" where "but" belongs), klal 13 w231
    `זוהה`->`זה`, klal 17 w76 `בכוהרי"ק`->`במוהרי"ק`, klal 17 w242
    `רי"ז`->`ר"ז`. The first three are wrong by sense; the fourth needs the ink.

    **The safety result, and it is the reason to proceed.** 24 of Dicta's 38
    disagreements are SOLO (no other engine differs) and **not one became a
    dispute** - the standing two-distinct-engines rule held every one back. Hand
    reading all 24: ~12 are edition/orthographic variants (`סימן`->`סי'`,
    `בספר`->`בס'`, `התו'`->`התוס'`, `דרשה`->`דרשא`, `הר"ף`->`הרי"ף`), ~8 are
    Dicta's own misreads (`הוזכר`->`החכר`, `דרב`->`דקב`), ~4 want the ink
    (`א"ה`->`א"ח`, twice). **Cross-edition variance shows up as SOLO
    disagreement, which the existing rule already discards.** That is the whole
    safety argument, and it is measured, not assumed.

    **The ragged-alignment filter is what makes a cross-edition witness safe -
    validated by what it SUPPRESSES (Lesson 26).** 81 positions dropped in
    scope, read individually: corpus editorial marks the Rashi edition does not
    carry (`.` `:` `•` `[.]`), klal markers, page-margin garbage, and genuine
    abbreviation-style edition differences (`דבבא מציעא`->`דב"מ`, 2 words vs 1).
    Exactly the edition variance, and no letter-level error among them - with
    **one exception worth a reviewer**: klal 19 w54-56, corpus and Surya read
    `בסירא ששה`, the VLM reads `בספרא ששה`, Dicta reads `בסיפא`. A genuine
    three-way split the filter hides because the word counts differ.

    **Extrapolation, labelled as one:** 4 new disputes per 1,549 words scales to
    roughly **130 across Part 1's ~50,195 words**, and 73% corroboration would
    touch ~265 of the 364 existing consensus disputes. From 10 klalim - an
    order of magnitude, not a forecast (Lesson 27).

0M. **[2026-08-31] A GERESH READ AS A YOD IN A NUMERAL SLOT — 3 in the corpus,
    all corroborated by two independent engines. DATA ISSUE, not fixed here.**
    Surfaced from the Dicta comparison: on the one specimen line, the corpus
    reads `סעיף אי` where the Dicta Rashi edition, Surya and sofer.ai all read
    `סעיף א'`. DocAI reads `אי` too - which is exactly WHY the corpus has it
    (the corpus was built from DocAI, so a DocAI artifact that nothing
    contradicted became the text).

    **SWEPT the whole of `part1.json`** for the class - a citation word
    (`סעיף`/`דף`/`סימן`/`אות`/`הלכה`/`כלל`/`פרק`/`ס"ק`/`שורה`) followed by a
    short token ending in `י`. 13 raw matches, 10 of them legitimate Hebrew
    (`הלכה כרבי`, `פרק שני`, `כלל לגבי`, `הלכה מפי משנה`). **3 are real:**

    | klal | corpus reads | Surya | Gemini VLM | context |
    |---:|---|---|---|---|
    | 12 | `סעיף אי` | `סעיף א'` | `סעיף א'` | `...חשן משפט סימן רס"ט סעיף אי` |
    | 140 | `אות עי` | `אות ע'` | `אות ע'` | `...הגהות הב"י אות עי שכתב` |
    | 155 | `סעיף זי` | `סעיף ז'` | `סעיף ז'` | `...ב"ח א"ח סי' שי"ח סעיף זי` |

    Two independent engines agree against the corpus on all three, which is the
    Lesson 9 bar for routing to a reviewer - **not** for applying. **NOT
    APPLIED, and `part1.json` NOT touched**: corrections go through the review
    dashboard against the ink, never a hand-edit or a find-replace (START_HERE,
    "Single source of truth"). These three want a reviewer's eyes on the crop.

0J. **[2026-08-31] DICTA MEASURED, BOTH SCRIPTS — it is the WORST engine on
    square type and the FIRST engine ever to read this work's Rashi script.**
    The user supplied two Dicta OCR samples (square Berlin, and a Rashi-script
    edition). Both scored with the new `tools/compare_ocr_engines.py` against
    `part1.json`, artifacts `ocr_engine_comparison_square_13_23.json` and
    `ocr_engine_comparison_rashi_13_22.json`.

    **Square (Berlin), klalim 13-23, every engine on the SAME three pages:**

    | engine | word acc. | CER (letters) | lexicon hit |
    |---|---:|---:|---:|
    | Dicta | **77.6%** | 8.5% | **83.4%** |
    | DocAI (circular - the corpus was built from it) | 99.0% | 0.8% | 99.1% |
    | Surya | 94.7% | 1.9% | 96.8% |
    | Gemini VLM pass A / B | 96.1% / 95.2% | n/a | 98.2% / 98.1% |
    | corpus itself (ceiling) | 100% | 0% | 99.7% |

    Dicta is beaten by everything already wired in. Its failure is systematic,
    not noise: `ב->כ` x159, `ה->ח` x48, `נ->ג` x44, `ל->ר` x13, plus 115
    spurious `ר` insertions. **That is a Rashi-trained model reading square
    type** - the exact mirror of the HebrewBooks fastocr rejection
    (`PROJECT-STATUS-HISTORY.md` 2026-08-19: a square model reading Rashi,
    `ס` 9.7x over, `א` 0.17x under). 83.4% lexicon hit against a 99.7% ceiling
    is the same rejection metric that killed fastocr at 44.0%.

    **Rashi edition, klalim 13-22, scored against the BERLIN corpus:**

    | engine | word acc. | CER (letters) | lexicon hit |
    |---|---:|---:|---:|
    | **Dicta (Rashi ed.)** | **94.8%** | **3.2%** | **98.5%** |
    | Dicta (square ed.) | 77.5% | 9.0% | 83.4% |
    | Surya (square ed.) | 93.9% | 2.1% | 96.3% |
    | DocAI (square ed., circular) | 98.9% | 0.8% | 99.1% |

    94.8% is a FLOOR, not an accuracy: it is a different EDITION, so genuine
    textual variance is charged to Dicta as error. Read the edition-independent
    column instead - **98.5% lexicon hit against a 99.6% ceiling**, versus
    fastocr's 44.0% on the same Rashi-script material. Hand-inspected klal 20
    (its worst, 82.1%): of 7 mismatches, `דבבא מציעא`->`דבמ` is an edition
    abbreviation, `הרף`->`הריף` is an edition variant, and the rest is
    bottom-of-page margin noise. Almost none of its loss is misread letters.

    **Why this matters more than the square result.** Lessons 23/24: a second
    witness must fail DIFFERENTLY, and architectural independence is defeated
    by a defect in the shared ink. Dicta-on-Rashi is a different ENGINE reading
    a different EDITION - different sorts, different compositor, different
    ligatures - which is the only configuration that escapes both. It is the
    independent witness this project has wanted since Tesseract was measured at
    3.8%, and nothing has read either Rashi-script edition before.

    **NOT YET DONE, and this is the whole payoff:** the samples cover 11 klalim.
    The next step is Dicta over the full Rashi-script edition, then wiring it in
    as an `AbstractWitnessEngine`. **Do NOT route Dicta at the square scan** -
    at 77.6% it would inject more disputes than it settles.

0K. **[2026-08-31] THE THREE-PAGE SAMPLE PDF IS PAGES 19-21 / KLALIM 12-24,
    NOT 18-20 / KLALIM 8-22 — Lesson 30, and it invalidates the eval's stated
    ground truth.** `tools/second_witness_eval/README.md` derived the mapping by
    MD5-matching the sample's images into `berlin_square_corrected.pdf`, which
    returns a **`fitz` doc index**, and reported it as a page number. Lesson 30:
    `page N == doc[N-1]` in this repo. Confirmed against CONTENT, two ways:
    sample page 1 aligns **74.2%** with `docai_word_boxes/page_19.json` (846
    tokens, exactly equal) and **1.9%** with `page_18.json`; and anchoring the
    sample's own token stream in `part1.json` lands on klalim 12-24.

    **What it invalidates.** `groundtruth_klal_8_22.txt` is the wrong ground
    truth for this sample - klalim 8-11 are not on these pages at all, and
    klalim 23-24 are on them but missing from the file. The README's "the test
    set is already adjudicated" table (2,356 words, 23 candidates, 11 open, 9
    human decisions) is counted over the wrong klal set, as is its per-klal
    coverage table. The README's own defence - "klal attribution agreed exactly
    across three independent artifacts" - did not detect this, because all three
    were queried with the same wrong page number; they agree with each other and
    not with the image. **`klal_page_regions.json`, `docai_word_boxes/` and
    `images/pdf_pages/` are NOT affected** - they use correct repo numbering,
    and are what proved the error.

    **ONE OF THE SIX WAS A CODE BUG, NOT A COMMENT (Lesson 34 - sweep the
    siblings).** `tools/test_trocr_benchmark.py` did not merely *say* 18/19/20,
    it held `sample_page_map = {1: 18, 2: 19, 3: 20}` and fed it to
    `cio.load_docai_page()`, so every sample page in that benchmark was scored
    against the NEIGHBOURING page's DocAI tokens. Corrected to `{1: 19, 2: 20,
    3: 21}`. Any TrOCR number ever produced by that script is void. **Swept
    every other `fitz` page access in `tools/` and `pipeline/` (13 call sites):
    all the rest are correct** - they route through
    `vision_adjudication_common.crop_pdf_bounding_box()`, which does
    `doc.load_page(page_num_1indexed - 1)`, or through
    `run_surya_part1_full_baseline.py`'s explicit `doc[p - 1]`.
    `test_trocr_benchmark.py` was the only site that had its own copy.

    **SWEPT (Lesson 28) - 6 places carried the claim, all corrected 2026-08-31:**
    `tools/second_witness_eval/README.md` (title, the mapping line, the
    three-artifact section), `groundtruth_klal_8_22.txt`'s header line,
    `evaluate_ocr_alignment.py`'s docstring, `run_vlm_witness_sample.py`'s
    docstring, `test_trocr_benchmark.py`'s page-map comment. **One file was
    checked and is NOT wrong:** `vlm_klal_8_22_ocr.txt` really is klalim 8-22 -
    that script crops per-klal from `klal_page_regions.json`, never by page
    number, so only the page half of its docstring was false.

0L. **[2026-08-31] `vlm_part1_full_baseline*.txt` blocks are PAGE-REGION text,
    not klal text, for 65 of 222 klalim — any character-level metric read off
    those files is meaningless.** Found while scoring Dicta. Klal 15 has **25
    words in the corpus and 245 in the VLM baseline (9.8x)**; klal 9 4.9x, klal
    36 4.8x. The VLM was given a klal's page region and transcribed everything
    in it, so a short klal's block carries its neighbours. **Swept all three
    baseline files:** pass A **65/222** klalim over 1.3x, pass B **46/222**,
    `surya_part1_full_baseline.txt` only **3/222** (klalim 161, 162, 202).
    Word accuracy (matched / reference) is unaffected and every accuracy figure
    quoted in this repo off these files still stands; CER and any
    length-sensitive metric do not. `tools/compare_ocr_engines.py` prints CER
    for them but it should be ignored, not compared.

0G. **[FIXED — verified 2026-09-01 from the collector, not the source: tests/test_review_server.py declares 44 and pytest collects 44.]** [2026-08-31] Two UI tests are DEFINED TWICE in the same file, so the
    first copy of each never runs — and the discarded copy is the stricter one.**
    `tests/test_review_server.py` holds **38 `def test_` statements and pytest
    collects 36**: `test_deep_link_lands_on_the_klal_and_rings_the_word` (lines
    333 and 368) and `test_clicking_a_word_puts_it_in_the_address_bar` (lines 357
    and 386) are each defined twice, and Python rebinds the name, so the earlier
    body is discarded at import. No error, no skip, no warning — the count is the
    only symptom, which is why it survived. Both pairs were written for item 29's
    deep-link feature.
    WHAT THE SHADOWING ACTUALLY COSTS, read side by side rather than assumed:
    the surviving `test_deep_link...` asserts only `assert ringed`, while the
    discarded one asserts `len(ringed) == 1` ("expected exactly one ringed word")
    — so a routing bug that rings several words now passes. The discarded copy
    also exercises the **klal-only** route `/#klal=66` before the klal+word route,
    and the survivor does not, so the bare-klal deep link has **zero coverage**.
    The `test_clicking_a_word...` pair differ only by an added settle wait, which
    costs nothing.
    Swept the class, per the standing rule: all four test files, **this is the
    only file affected** — `test_corpus_invariants.py` (44 defs), 
    `test_pipeline_logic.py` (273) and `test_witness_engine.py` (5) have no
    duplicate names, and their def-count equals their collected count.
    **FIXED 2026-08-31.** The weaker copy of each pair was deleted and its
    surviving twin strengthened, so no coverage was traded away: the deep-link
    test keeps `len(ringed) == 1` and the klal-only route, and the address-bar
    test keeps the settle wait the other copy had. 36 defs, 36 collected.
    **Gated by `test_no_test_file_defines_the_same_test_name_twice`**, which walks
    every `tests/test_*.py` with `ast` and compares module-level `def test_` names
    for duplicates. Verified it can actually fail, per Lesson 25: injecting a
    duplicate into `test_witness_engine.py` fails it by name and line, removing it
    passes. This was Lesson 32's shape one level in — a test that exists, is
    maintained, reads as covering the feature, and does not run.

0F. **[2026-08-31] The UI test suite is bound to THIS corpus, in its current
    state of repair — the wrong shape for a general-purpose platform.** Measured:
    every test in `tests/test_review_server.py` boots a server against the shipped
    Yad Malachi corpus and **23 pin a corpus coordinate in executable code**
    (`#klal-block-66 .flag-word`, `klal_id, word_index = 1, 85`, a literal `&` at
    klal 69 w338). Zero use synthetic data. So they test the platform PLUS
    this book's defects, and the failure mode is backwards: **the closer the text
    gets to correct, the more tests fail**, because each quietly depended on a
    defect surviving. Seven broke at once on 2026-08-31 when the reviewer's
    decisions were applied — one asserting an `&` that had been correctly repaired
    to `אל`, three sitting on a klal whose candidates were all settled.
    THE ENGINE IS NOT THE PROBLEM: `tests/test_pipeline_logic.py` is 273 tests, 91
    of them purely synthetic and only ~6 touching real data - every fix to the
    apply path, the drift guards, the reindexers and the flag closing is tested on
    a throwaway `אלף בית גימל` corpus and would pass on any book.
    `tests/test_corpus_invariants.py` reads the corpus BY DESIGN, which is right,
    but its three baselines are keyed `(klal_id, word_index)` and every entry
    shifts when a word is inserted or deleted earlier in its klal - item 0C
    reaching into the test suite, where nothing can reindex a literal.
    FIX: a small synthetic corpus fixture carrying one of each condition (a
    disputed word, an ai_flag, a manual correction, a multi-page klal, a
    non-Hebrew character, a duplicated word) for the UI tests to boot against.
    NOT DONE - 2026-08-31 only unpinned the seven that broke, by having them look
    a subject up rather than assume one. That is a patch; the fixture is the fix,
    and it is self-contained work that wants its own scope.
    **CORRECTED 2026-08-31: "all 38 tests" is wrong — the file DEFINES 38 and
    pytest collects and runs only 36.** Two names are defined twice and the first
    body of each is silently discarded; see item 0G. The 38 came from a
    `grep -c "^def test_"`, which counts the source rather than what runs, and
    that distinction is the whole of 0G. The 23 pinned coordinates are unaffected.
    0G is now FIXED and gated, so the count is 36 = 36; the fixture work below is
    unaffected and still open. Note for whoever builds it: a duplicate name in a
    file being rewritten test-by-test is exactly how those two got there, and the
    new guard is what will catch the next one.

0E. **[FIXED 2026-08-31 — see item 46.] A nav jump's smooth scroll outlives the
    observer suppression, so a focus set during it is wiped.** `jumpTo()` starts a
    `scrollIntoView({behavior:'smooth'})` and sets `suppressObserverScroll` for
    **700ms**; measured 2026-08-31, that scroll takes **~1500ms** to settle from a
    long jump (klal 53 -> klal 12 sampled every 300ms: -11337, -3737, -893, -24,
    12). For the remaining ~800ms the scroll observer is live, so
    `updateActiveFromScroll()` fires, calls `setActiveKlal()`, and that calls
    `showPage(page, klal, null)` - the explicit null that clears `scanFocusCorr`.
    Any word focused in that window loses its highlight ring, and the scan pane
    jumps to whichever klal the scroll is passing.
    Caught by instrumenting `showPage`: zooming right after a nav jump produced
    two `showPage(..., null)` calls for klal 4 while the focused word was in klal
    5. NOT a regression - reproduced with 2026-08-31's frontend and server changes
    reverted; it surfaced only because a test's subject moved off klal 1 when its
    corrections were applied.
    NOT YET FIXED. The clean fix is to end the suppression when the scroll
    actually settles rather than after a fixed timeout, which is a behaviour
    change in the scroll/observer path and wants its own before/after. In the
    meantime `tests/test_review_server.py::test_focus_box_transparent_and_zoom_
    preserves_focus` waits for the scroll to settle before focusing, so it tests
    zoom rather than the race.

0D. **[FIXED 2026-08-30, reviewer-reported] Correcting a word cost it its scan
    position, and applying a decision never closed the flag that raised it.**
    Three reports, one measurement behind two of them.
    (a) **63 of 306 open word-level flags (21%) cannot be located on the scan at
    all** — `_word_scan_position()` returns no bbox, so clicking the word
    highlights nothing and there is nothing for the focus-zoom to zoom to. The
    zoom code is intact and correct; it is being handed no box. The cause is that
    the aligner matches CORPUS text against DocAI tokens, so the moment a word is
    repaired it stops matching the token that still holds the OCR error and the
    alignment drops it: `דנראה`, `מאין`, `שבועה`, `אברהם`, `ופומבדיתא` are all in
    the list. **18 of the 63 were created by tonight's own 45 corrections**; 45
    are older. Fixing a word should not blind the reviewer to it.
    (b) `tests/test_corpus_invariants.py::test_every_flagged_word_can_be_located_
    on_the_scan` does NOT cover this: it `continue`s on `opcode in ("delete",
    "ai_flag", "manual")`, and `ai_flag` is precisely what a flagged word is. It
    only fires when an entry lacks a position THOUGH the alignment has one — the
    inverse case. The name promises what it does not check.
    (c) **Applying a decision does not close the flag that raised it.** The
    reviewer cleared klal 66's klal-level flag and the middle pane still read as
    flagged, because `ai_flag_count` counts WORD-level flags and klal 66 has six
    open — four of them (w14, w82, w97, w112) already satisfied by corrections
    applied tonight, including w112's `!`, which no longer exists in the text.
    Nothing in the apply path closes a flag, and the two clearing controls are
    per-flag, so a satisfied flag stays lit until someone clicks it individually.
    **(c) FIXED.** `close_flag_satisfied_by()` closes the flag at apply time — a
    decision applied at that exact word IS a human having ruled there, a
    confirmed-no-op included. It refuses when the flag is NEWER than the apply:
    that means somebody re-opened the position knowing the decision had landed,
    and three real flags depend on it (klal 66 w0, flagged three minutes after its
    own apply was found wrong and reverted; klal 10 w1; klal 17 w308). Backlog
    cleared by `tools/close_flags_already_answered.py`, a one-time backfill that
    reuses the same function rather than restating the rule: **48 dead flags
    closed, 17% of the open queue**, klal 66's four among them.
    **(a) FIXED 2026-08-30 — 63 unlocatable flags down to 10.**
    `_corpus_word_bboxes()` read `SequenceMatcher.get_matching_blocks()`, so ONLY
    words the corpus and DocAI agree on got a box. Backwards, for a queue of words
    flagged BECAUSE the two disagree — and a word lost its box the moment somebody
    repaired it, the corrected form no longer equalling the token that still holds
    the OCR error. It now also pairs an EQUAL-LENGTH `replace` run: n corpus words
    against n tokens between two anchors the alignment already agrees on, so word
    k is token k. That is what a letter substitution, a dropped-lamed ligature and
    a stray `&` all look like. Unequal runs are NOT paired — there the
    correspondence is genuinely unknown and a box on a guessed token points the
    reviewer at the wrong ink.
    Measured against the previous behaviour corpus-wide: **51,043 -> 51,554 boxes,
    511 newly locatable, 0 lost, 0 moved.** The "0 moved" took a second fix:
    paired matches must not choose the PAGE a recurring word lives on (only exact
    ones may), or klal 114 w57-w64 pair against the continuation page holding 5 of
    the klal's 87 tokens and walk off the page they belong to — 8 words that had a
    correct box before.
    **Tried and reverted**: matching non-Hebrew words on their raw text so `&`
    could match `&`. It works and costs too much — putting punctuation tokens back
    into the sequence moved 41 correct boxes and lost 2, ordinary words included.
    The 10 remaining unlocatable words carry no Hebrew letter at all and are
    baselined.
    **(b) FIXED 2026-08-30.** `test_every_flagged_word_can_be_located_on_the_scan`
    exempted `opcode in ("delete", "ai_flag", "manual")` — and `ai_flag` is what a
    flagged word IS — and only fired on the inverse case, an entry lacking a
    position though the alignment has one. Nothing asserted the alignment has one,
    which is why it stayed green through all of the above. Replaced by
    `test_every_open_flag_can_actually_be_found_on_the_scan`, which walks the open
    flags themselves against `_word_scan_position` and baselines the 10.

0C. **[FIXED 2026-08-30] Nothing reindexed the append-only ledger when a klal's
    word count changed — open flags silently walked off their word.**
    `apply_reviewer_decisions.py` limits itself to ONE word-count-changing
    decision per klal per run and prints "run ./rebuild_all.sh, then this script
    again," and that is correct as far as it goes: the rebuild regenerates the
    CANDIDATE files against fresh indices. It does not, and cannot, touch
    `review_decisions.jsonl` — the log is append-only. So every open `klal_flag`
    at an index past the change keeps pointing at the index it was written with,
    which is now a different word. **Fired this run**: deleting the stray `!` at
    klal 66 w112 shortened the klal 215 -> 214, and the flag on `ע"ס` at w135
    came to rest on `שהניח`. Superseded by a new flag at w134 (the old row closed
    with `needs_revisit: false` and an explanation, since nothing may be
    removed). This is the same defect class the reviewer caught on 2026-08-18's
    `ai-semantic-spotcheck-round4` batch — a note attached to the wrong word —
    reached by a different route, so re-verifying that batch did not and could
    not prevent it. **Not yet swept corpus-wide**: only klalim 66 and 219 changed
    word count this run and both were checked by hand, but any earlier
    word-count change may have left the same residue, and no check exists that
    would say so. A validator comparing each open flag's note text against the
    word now at its index would find them.
    **FIXED.** `apply_reviewer_decisions.reindex_flags_after_shift()` moves them
    at apply time, and only on a VERIFIED landing: a flag is shifted only when the
    word it named before is the word at the shifted index, otherwise it is left
    alone and reported — a flag on a guessed word is worse than one a human is
    told to check. The residue was swept, since these notes name their own word
    and the ledger can be checked against the corpus directly: **172 of 258 open
    flags name their own index, and exactly one had drifted** — klal 43 w14, whose
    `ממטונא` sits at w17, confirmed by the note's own quoted context ending
    immediately before it. Moved. Gated by
    `test_no_open_flag_names_a_word_that_is_not_at_its_index`.

0A. **[2026-08-30] A decided dispute could never be applied — 43 rulings
    stranded, now recovered.** `synthesize_multi_witness.active_human_decisions()`
    deliberately DROPS a dispute from the candidate queue the moment a human
    rules on it, so a resolved dispute is not shown again. Correct for the queue,
    fatal downstream: `apply_reviewer_decisions.py` drift-checked each decision's
    `candidate_snapshot` against the live `corrections_part1.json` entry, and an
    ENTRY THAT NO LONGER EXISTS failed that check the same way a changed one
    does. So "entry missing" — the normal state of every unapplied decision —
    read as drift, and the ruling was refused forever. Decide, rebuild, and the
    decision is stranded. **Extent: 43 decisions from 2026-08-22..27, 24 of them
    real edits still sitting uncorrected in `part1.json`** (`&` in klal 167 w24
    among them, plus `שכועה`→`שבועה`, `אברחם`→`אברהם`, `ופומכדיתא`→`ופומבדיתא`).
    FIXED: `snapshot_still_matches_corpus()` falls back to checking the corpus
    itself when the entry is absent — which is the only thing the entry was ever
    proving, and the standard `apply_manual_correction` has always used. An entry
    that is present and DISAGREES still vetoes; a `delete`-opcode decision names
    no span and is never recovered this way. Four gated tests. Applied 2026-08-30:
    80 decisions (27 replace, 2 insert/delete, 15 manual, 36 confirmed-no-op),
    38 words changed across 19 klalim.

0B. **[2026-08-30] `insert`-opcode apply ignored `chosen_text` and deleted a
    word the reviewer never voted to delete — corpus damage, reverted.** Sibling
    of the ★1 finding, same branch, same cause. An `insert` candidate offers one
    span and `apply_insert_removal()` deletes ALL of it, reading `final_text` and
    never `chosen_text`. ★1 fixed the case where the reviewer keeps the whole
    span; nothing covered the reviewer choosing something SHORTER. **It fired on
    klal 66 w0**: stored `סו אין`, reviewer chose the engines' `סו`, and the run
    removed both words — dropping the klal marker AND the `אין` that negates the
    entire klal, turning `אין ב"ד יכול לבטל` (a court CANNOT annul) into `ב"ד
    יכול לבטל` (a court CAN). Caught by reading the applied diff word by word,
    not by any test. `clean_text` restored; the `apply_event` (898c9b4e67d5)
    stands in the append-only log and CANNOT be retracted, so the log now claims
    a change the corpus does not have. **`audit_applied_decisions.py` does not
    catch this** - checked 2026-08-30, it sorts klal 66 w0 into its
    "word-count-changing, not position-verifiable post-hoc" bucket (9 decisions)
    and never compares it to the corpus at all. A reverted insert/delete is
    invisible to the one tool built to find exactly this. The durable record is
    therefore the `klal_flag` appended alongside it, which surfaces on the
    dashboard as an open flag on klal 66; the auditor's blind spot to a reverted
    word-count change is itself worth closing. The script now
    REFUSES this shape rather than guessing. Two gated tests.
    **RULED AND CLOSED 2026-08-30 — verified 2026-08-31, this entry had gone
    stale.** It read "OPEN — needs the user's ruling on klal 66 w0" after the
    ruling had already been given. The reviewer recorded "66 w0 is correct"
    (superseding `disputed_choice` at 2026-08-30T20:37:07, chosen `סו אין`), the
    `klal_flag` was closed in the same second with the reasoning, and a
    confirmed-no-op `apply_event` followed at 21:01:31. The corpus reads
    `סו אין ב"ד יכול` and no flag is open at that word — all three re-checked
    against the ledger and `part1.json`, not inferred from the write-up. The
    evidence had pointed this way: the vision check transcribes `אין ב"ד` at
    0.95, and klal 57 w0 is the identical `נז אין` shape the reviewer chose to
    KEEP. The append-only log still carries the reverted apply_event
    (898c9b4e67d5) claiming a change the corpus does not have; that is by design
    and is documented above.

00. **[CLOSED 2026-08-30 BY THE USER — "close 162/163 surya issue - wasting
    time". Stop raising it in session summaries; the standing reminder inside is
    retired with it.] Surya block mis-assignment: 4 klalim carry a neighbour's
    text.** What was left was a mis-assigned SURYA WITNESS for klalim 162/163,
    not a corpus defect — the stored text of 161/162/163 was re-read on close and
    is clean, each klal opening with its own marker. The cost of leaving it is
    that those two klalim have no working second engine, so cross-checking is
    blind there; the user has weighed that against three failed fix attempts and
    closed it. Retained below as the record of what was measured. NOT to be attempted by an agent without the user saying
    so: three separate attempts to fix it by tuning
    `split_block_across_klalim()` have all regressed the corpus and been
    reverted, the worst costing 29 klalim their coverage and 2.3 points of mean
    agreement. **Any LLM instance reading this file should mention this open
    item to the user in its session summary until it is closed.** (RETIRED
    2026-08-30 — the item is closed; do not carry this directive forward.)
    Details: (swept
    2026-08-24, extent documented per the standing rule). klal 162 (page 59,
    NEW - a regression from the 300-DPI re-render, 0.68 -> 0.09) and its
    knock-on klal 163; klalim 8, 88 and 202 are pre-existing. Root cause for
    162: the block opening `קסב` sits inside klal 161's recorded region, so it
    covers one klal, falls through to centre-assignment, and the whole page
    shifts by one - the marker and the derived region geometry disagree. Two fix
    attempts reverted rather than risk the 190 klalim the re-render improved;
    this wants a scoped change with its own before/after. Context: the same
    re-render cut mis-assignment from 15 klalim to 4.
    **CONFIRMED AGAINST THE INK 2026-08-25 — this item is 2 klalim, not 5.** The
    detector behind it ("the klal's Surya text opens with a neighbour's marker")
    cannot tell a mis-assigned block from a MISREAD marker glyph. Klalim 8, 88
    and 202 agree with their own stored text at 87%, 89% and 93% (genuinely
    mis-assigned klal 162 sits at 9%), and rendering all three markers at 400 DPI
    settles it: the page prints `ח`, `פח בשבת` and `רב היכא`, where Surya read
    `ה`, `פה`, `רא`. **All three are marker misreads; their blocks are correctly
    assigned.** Two are the ח/ה pair behind klal 1's `דנראח` typo. **Only klalim
    162 and 163 are really mis-assigned**, so the remaining work is a marker-read
    fix, NOT another pass at `split_block_across_klalim()` (Lesson 31). Nothing
    to review in klalim 8/88/202 on account of this item.

0. **STANDING RULE, added 2026-08-24 (user directive): never fix one instance —
   sweep the corpus for the class.** Whenever you find and fix an issue, review
   the whole corpus for other instances of the same failure, in the same turn.
   If you fix it, report how many existed and that the count is now zero. If you
   do NOT fix it, sweep anyway and document the other instances together with
   the open issue here — an open item reading "klal 91 has X" when 104 klalim
   have X looks handled and is worse than no entry. Full rule in `START_HERE.md`
   Part 2 ("Never fix one instance"); Lesson 28.

1. **The 312 fabricated "VLM Verified" Parts 2-3 candidates were pulled from
   the dashboard 2026-08-20** — `corrections_part2.json`/`corrections_part3.json`
   emptied to `{}` (user-authorized) after confirming every entry's
   confidence/reasoning was fabricated, not computed — see
   `PROJECT-STATUS-HISTORY.md`'s 2026-08-20 "BUG FOUND" entry. The
   1,496→312 flag filtering pass itself was legitimate and lost no human
   decision, and remains recorded in `review_decisions.jsonl`'s history if
   ever needed again. **Still open: actually run `VlmWitnessEngine` for real
   against those 312 (or whatever set is chosen) before Parts 2-3 candidates
   are shown in the dashboard again.**

1a. **A genuinely independent third OCR/HTR engine is still needed** to fully
    satisfy `PROPOSED_PIPELINE_ARCHITECTURE.md`'s Directive #1 (see TL;DR
    above and that doc's new section 5). Dicta is the leading candidate but
    needs end-to-end raw-scan-upload testing before it can be trusted as a
    witness; Kraken is blocked by `torch>=2.4.0` vs. the macOS x86_64 Python
    3.12 wheel ceiling (2.2.2) without Docker/source build. Until resolved,
    this also gates item 1 above in spirit — running `VlmWitnessEngine`
    "for real" closes the fabrication problem but not the circularity one.

2. **Parts 2–3 corrections are investigated but not applied — correctly, by
   design.** Scan-linkage/verification infrastructure (extraction,
   marker/trace-building, vision-adjudication) is built and has been run over
   the full page range; real data issues have been found and confirmed by
   direct scan-crop verification. Per the standing Parts 2-3 gate (see
   `START_HERE.md`), no actual `part2.json`/`part3.json` edit has been applied
   yet — needs its own explicit go-ahead, same two-step principle as the rest
   of this pipeline.

3. **The witness queue is still open**: 419 items across klal 30/75/88 (160 /
   119 / 140), of which 8 are decided and **411 remain** — the only real
   second opinion (DocAI vs. Tesseract) on those three page-crossing
   reconstructions, covering 2,673 DocAI words at 0.76–0.86 agreement. The
   machine vision pass is done; the human review-in-dashboard pass was
   explicitly deferred by the user as a future step (not forgotten, not a gate
   on anything else). **Tesseract provenance re-confirmed 2026-08-25 from the
   code (`verify_reconstruction_witness.py:79`, `tesseract -l heb`), with a
   recommended replacement measured the same day — see item 3a.**

**CORRECTED 2026-09-01 — the 419 is right about the FILE and wrong about the
   work.** `reconstruction_witness_queue.json` does still hold exactly 419 rows,
   160/119/140 across klalim 30/75/88, so that half of this item has not
   drifted. But the reviewer is never served 419: item 4's remedy was
   implemented, `WITNESS_QUEUE_FILTERED` is on with priority verdicts
   `("B","NEITHER")`, and the dashboard serves **44** — of which **24 are still
   open**. Decisions recorded: **20**, not the 8 this item claims.

   So "411 remain" overstates the outstanding work by roughly 17x, and it is the
   number a reader would most likely quote. The file count and the queue count
   are two different quantities and this item conflates them; item 4 changed
   what the second one means and nothing came back to update the first.

3a. **RECOMMENDED 2026-08-25 (user-requested, measured, not implemented):
    replace the Tesseract leg with Surya, keep the VLM as a gated second
    witness, and keep semantics as triage only.** All three klalim are already
    covered by both at 300 DPI, so this retires a generator rather than building
    one. On the same 4,286 words: Tesseract flags 419, Surya 218, the
    stability-gated VLM 85, and the two agreeing 25 (already live). On the
    queue's own adjudicated positions (anchored subset), Surya catches **7 of 10
    NEITHER cases (70%)** and 4 of 13 where Tesseract beat DocAI, while firing on
    only 15% of the 306 positions that were Tesseract noise — roughly **3× the
    signal-to-noise**. The VLM must not be primary here: it is the adjudicator's
    own model family (Directive #1; the arbiter backs consensus 52% when the VLM
    is in it vs 30% when not). A semantic pass cannot be a witness at all — the
    defect it must catch (a reconstruction stitched from the wrong place) reads
    as fluent Hebrew. **Do not delete the queue**: Surya + gated VLM would have
    missed about half the positions where the arbiter overruled DocAI, so retire
    the generator and keep the findings, filtered per item 4. Two further facts
    from that check: Tesseract read the **1.1–1.2 MP** cached page renders (the
    same starvation that cost Surya 18 points), so its 3.8% is a floor rather
    than a fair number; and **90 of the queue's 419 `word_index` values no longer
    anchor** to their `docai_reading`, so any index-keyed analysis must anchor
    first. Full tables in `PROJECT-STATUS-HISTORY.md`.

4. **The witness queue should be filtered by vision verdict, not worked in
   full — and not pruned by tier.** Analysed 2026-08-19 (full detail and
   tables in `PROJECT-STATUS-HISTORY.md`). Tesseract was right in only **16 of
   419** disagreements (3.8%) vs. DocAI's 91.2%; it fails structurally, being a
   weaker engine on the *same* scan rather than an independent signal. Deleting
   tier D was considered and **rejected**: D holds the most findings in
   absolute terms (13 of 37) and **7 of the 8 human decisions already recorded
   sit in it**. The right cut is `vision_selected in ("B","NEITHER")` — **419 →
   37 items, 91% less work, zero findings lost.** Not implemented: the queue
   file is derived, so filtering belongs in
   `tools/verify_reconstruction_witness.py` or a separate view, never a
   hand-edit. Caveat: all 419 verdicts came back ≥0.9 confidence, so treat the
   37 as a priority queue, not proof the other 382 are clean (Lesson 2).

5. **RESOLVED 2026-08-31 — the Dicta Rashi OCR endpoint is
   <https://rashiocr.dicta.org.il/>.** User-supplied; it is what produced this
   repo's two Dicta samples. Every earlier "mechanism unconfirmed" note was
   searching `ocr.dicta.org.il`, which is a DIFFERENT tool — source inspection of
   its client bundle (`index-B6te2D74.js`) correctly found a proofreading editor
   titled "הגהת מסמכים סרוקים" for `.docx`/`.txt` synced from Dropbox. That
   finding was right about that URL and wrong about Dicta: the raw-scan endpoint
   exists, at a hostname nobody had looked at. A reminder that "we searched and
   did not find it" is a statement about where we looked (Lesson 28's shape,
   applied to research rather than to a bug).

   **STANDING RULE FOR THIS ENDPOINT — it is a free service run by a research
   institute, not an API we pay for.** Submit in small chunks, serially, with a
   real delay between them, and never in parallel. User directive 2026-08-31:
   "be CERTAIN to not flood this url... push them through slowly to be a good
   neighbor." Any script that touches it must rate-limit by construction, resume
   from where it stopped rather than restarting, and write each chunk's result to
   disk as it arrives (the standing incremental-flush rule).

6. **Przemyśl 1888's script is unverified, and HebrewBooks' fastocr is
   rejected.** Assessed 2026-08-19 (detail and tables in
   `PROJECT-STATUS-HISTORY.md`). HebrewBooks #14122's shipped
   "searchable/fastocr" text scores **44.0% lexicon hit vs. our Berlin
   corpus's 97.8%** — unusable, from systematic letter confusion (ס 9.7×
   over-produced, א 0.17× under). That signature revealed a real doc error:
   **Przemyśl 1877's body is Rashi script, not square**, verified by rendering
   pages 30/250/400/480. `CASE-YAD-MALACHI.md` corrected. **Przemyśl 1888 was
   deliberately marked *unverified* rather than corrected by analogy** — it's a
   separate printing and nobody has rendered a body page (Lesson 7). Someone
   should, and it isn't in hand locally.

7. **The public-domain citation tier is only partly itemized.**
   `CORPUS-COMPARISON.md` gives the tier totals (21 works / 939 citations) and
   per-work counts *only* for works its wider sweep newly surfaced. The 15
   already-known public-domain works are counted in the totals but never
   listed individually — and arithmetic shows they average ~40 citations each,
   so the tier's #2–#5 are genuinely unknown. `CASE-YAD-MALACHI.md`'s
   public-domain table states this limit explicitly rather than implying a
   ranking. Closing it means re-running the underlying Halachipedia survey,
   whose raw output is not in this repo. Found 2026-08-19.

8. **CLOSED 2026-08-25 — insert candidates DO have scan boxes, and the ones
   they had were wrong until today.** This item asked whether to build a bbox
   estimate for `opcode: insert` candidates (stored text a fresh DocAI pass
   found no token for, so there is nothing to crop). **It was built 2026-08-21**
   — `estimate_insert_bbox()` in `build_corrections_dataset.py` — and this entry
   was never updated, which is why it still read "awaiting a decision".
   **Today it also got fixed**: it unioned the DocAI tokens either side of the
   gap, which is a tight band only when both sit on the same printed line, and
   at a klal's opening marker the gap IS a line break — so 21 of 40 insert
   candidates carried a box spanning two lines and most of the page width
   (median 0.382 of the page against 0.039 for an ordinary word box; 26 of the
   40 sit at word_index 0). Reported by the reviewer on klalim 3 and 4 as "the
   box is very large, including the bottom of klal 2". After the fix: median
   0.073, max 0.123, zero boxes wider than a quarter page.

9c. **[CORRECTED 2026-08-31 — this entry was STALE and overstated the open
    work. Four of its six sub-items were fixed in code and the entry was never
    updated.]** Verified one at a time against the source, not against the
    write-up (Lesson 19/33):

    | sub-item | claim in this entry | verified state |
    |---|---|---|
    | H6 `typography.py` | "still dead code carrying a third, divergent `CONFUSION_PAIRS`" | **FIXED.** Imported by `synthesize_multi_witness.py:57`, `tools/estimate_consensus_posterior.py`, `tools/survey_shared_engine_errors.py` — not dead. Its third `CONFUSION_PAIRS` is **gone**; its own header documents the removal and points to the two real, deliberately-different sets. |
    | H8 passB | "still violates the incremental-flush rule and no-ops its own cache" | **FIXED / deliberate.** `f.flush()` is at `run_part1_vlm_patch_passB.py:122`. The no-op cache is now a *documented correctness requirement*, not an oversight: Pass A and Pass B must be two INDEPENDENT samples, and a shared crop-keyed cache replays A's answer for B, so every replayed position agrees with itself by construction and sails through the stability gate. Reverted 2026-08-24 with that reasoning in the file. |
    | M9 `is_gershayim_noise()` | "moot for the superseded extractors" | **MOOT, confirmed.** The identifier does not exist anywhere in the repo. The normalisation point still stands if Phase 1 is built. |
    | M11 disputed panel | "still pre-selects the machine verdict" | **FIXED.** Reverted 2026-08-23; `review_frontend/app.js:1412-1427` carries the revert and its reasoning. Undecided words default to the stored text. |
    | C16 Surya coverage | "10 klalim still have no Surya coverage" | **FIXED.** `surya_part1_full_baseline.txt` carries all **222/222** klalim with non-zero text (this file's own TL;DR already said 222/222 — the two disagreed). Thinnest are klal 222 (0.39 of corpus words) and klal 163 (0.42, the known mis-assignment from closed item 00). |
    | C18 `match_block_to_klal` | never-None nearest-region fallback | **STILL OPEN — the only one.** `tools/run_surya_part1_full_baseline.py:79`. Now carries an explicit deferral note: 2 blocks / 4 words affected on pages 14-76, and tightening it changes which text every klal gets, so it wants its own measurement rather than a drive-by. Accepted open, not forgotten. |

    The lesson this entry is itself an instance of: an open item that lists six
    things when five are done reads as five outstanding tasks and costs the next
    reader the time to re-derive all of them. Closed sub-items must be struck
    when they close, not left standing.

10. **`MULTI-WITNESS-REPAIR-AND-SYNTHESIS-PLAN.md` review 2026-08-23 — the
    architecture is sound, four things in it are not.** (a) **Its §2.B independence proof is now empirically refuted, not just
    theoretically doubted: one Part-1 synthesis run produced 16 instances of two
    or three engines making the IDENTICAL error, all of them the alef-lamed
    ligature dropping its `ל`** (`ושמואל`->`ושמוא`, `אליבא`->`איבא`,
    `אליהו`->`איהו`...), including unanimous 3-of-3 agreement — because the defect
    is in the ink, not the models. §2.B puts that at 3.5e-7. Under the document's
    own "2-of-3 -> Auto-Approve, 0 sec" matrix these would have REVERTED correct
    human decisions to the corrupted reading. The proof also does not hold for
    the pair the code actually used:
    VLM Pass A / Pass B are the same model, so the `1/|V|` decoupling term is
    unearned, and the term itself assumes hallucinations distribute uniformly
    over a 50k vocabulary when this document's own §1 argues OCR errors are
    systematic and glyph-driven. (b) Its **"94.5% accuracy" for the VLM is
    unsourced** — this repo's measured, verified figure is 93.34%
    (`part1_full_baseline_accuracy_report.txt`); "Surya error rate 32.4%"
    appears nowhere in the repo at all; and the "~20,300 review flags"
    figure does not reconcile with 39.3% of Part 1's 52,607 words (~20,700)
    or of the VLM's 57,614 (~22,600). Given this project's history with the
    72.03% figure, unsourced numbers in the load-bearing math section need a
    citation or removal. (c) **Phase 4 ("Run the unified 3-witness synthesis
    pipeline across Parts 2 and 3", "Export certified final text") collides
    with the binding Parts 2-3 gate** and does not mention it — synthesis
    infrastructure is authorized under the 2026-08-17 supersede, exporting
    certified Parts 2-3 text is not. (d) Its decision matrix **auto-approves
    corpus text changes with "0 sec" human review** for the 2-of-3 rows,
    which is a policy change to success criterion #1 ("resolved by looking at
    the actual scan, not inferred") and to the two-step record/apply rule —
    it needs an explicit user decision, not an engineering default. Also
    missing: any validation plan for the repair filters themselves (a wrong
    gershayim-recovery rule silently erases the disagreement it should have
    surfaced — Lesson 15), and any statement of where this plugs into
    `rebuild_all.sh`, which is the root cause of C1 above. Phase 1's
    "[x] Establish centralized typography catalog" is checked for a module
    nothing imports.

12. **MEASURED 2026-08-23: P(consensus correct | 2 distinct engines agree)
    is ~26-41%, not the >99.9999% the plan claimed.** Auto-approval on consensus
    is indefensible at any threshold this data supports; consensus is a TRIAGE
    signal, not a decision procedure (`tools/estimate_consensus_posterior.py`).
    Dropping catalogued ligature artifacts barely moves it (41%→39%), so a bigger
    artifact catalogue will not rescue the rule. **Second finding: the
    circularity gap now has an effect size** — where the VLM is one of the
    agreeing engines the Gemini arbiter backs consensus 52% of the time, versus
    30% where it is not. That 22-point spread is what Directive #1's violation
    costs in practice.

16. **71 of 667 klalim still hold a placeholder instead of text** (was 115;
    **44** reconstructed by `tools/reconstruct_placeholder_klalim.py`,
    user-authorised, each flagged as unreviewed machine output — 12 of them
    rewritten 2026-08-26 after the page-furniture damage in item 20). All are in
    klalim 223–667. Re-measured 2026-08-26 from the tool's own refusal report, not
    remembered: **44 have no located gematria marker** and **13 have no next
    marker to bound them** — marker-trace work, not extraction work — while 8 are
    blocked by the corpus invariants (a catchword duplicated at the seam in 7,
    page-header furniture in 1) and 6 by the lexical gates. The reconstructions that DID land are extraction output,
    never read by a human: the gates reject a broadly-wrong span but cannot see a
    scramble buried inside an otherwise good klal.

19. **CLOSED 2026-08-26 — the review was finished in three scoped passes; see
    item 21 for what it found.** The original entry is kept below for the record
    of how it failed. The re-run followed the brief in
    `scratch/NEXT-SESSION-PROMPT.md`: source files only, three separate `high`
    passes rather than one `max` pass over 99 files, run one at a time. All
    three completed. Every parked finding was verified by running something
    before being fixed, and **two did not survive that**: `open_count` is not a
    dead field (a corpus invariant test consumes it), and the claim that 7
    klalim carry a live `needs_revisit` flag over placeholder text is false
    (their latest flag is closed).

19a. **[superseded, kept for the record] CODE REVIEW 2026-08-26 ran out of budget twice; 3 of ~10 angles finished
    and their 21 findings are parked in `CODE-REVIEW-2026-08-26.md`.** One is
    confirmed and fixed: `reconstruct_placeholder_klalim.py` sliced a
    reading-order token list with `marker_position`, a RAW array index, and **6
    of the 51 klalim written 2026-08-25 took a boundary from the wrong token**
    (commit `930ce76`; corpus reverted, tool fixed, reconstruction redone).
    **The rest are unverified angle output and no correctness angle completed**,
    so this range has had a reuse/efficiency/simplification pass and NOT a
    correctness pass. The remaining leads cluster: three more copies of the
    `word_freq.json` loader and of `is_placeholder`, a header regex that does not
    match the invariant it claims to enforce, `api_page()` re-parsing the 1.8 MB
    decision log 25× per request, and `open_count` served with nothing rendering
    it. **Do not re-run this as one max-effort review over 99 files** — see that
    file's header for why it died.

20. **CONFIRMED 2026-08-26 — the page-seam cleaner in
    `reconstruct_placeholder_klalim.py` writes the SCANNER WATERMARK into corpus
    text: `Digitized by Google` is embedded in 12 klalim** (250, 290, 333, 357,
    380, 385, 414, 442, 553, 580, 616, 665), every one of them exactly
    reproducible from the tool, so this is that tool's output and nothing
    else's. Found by a correctness pass over the 2026-08-24/25 range; **all 289
    gated tests pass with the damage in place**, because
    `test_no_page_header_contamination`'s regex only matches the HEBREW running
    header and the watermark is Latin. Swept the whole corpus per the standing
    rule: 12 klalim, all in 223-667, none in reviewed Part 1.

    Mechanism, verified step by step on klal 616 (page 220 -> 221). The Google
    Books footer `Digitized by Google` sits between the catchword at the foot of
    one page and its repetition at the head of the next. `strip_page_furniture()`
    keys on `hebrew_letters_only()`, which maps every Latin token to `""`, so the
    footer is not furniture to it and survives. Three knock-on defects follow
    from the same run:

    - **`drop_seam_duplicate()` is defeated, and separately fires on the wrong
      pair.** It compares only the two tokens either side of the seam index, and
      the watermark now sits between them, so the duplicated catchword survives
      in **3 klalim** (333 `יש ... יש`, 380 `להאמינה ... להאמינה`, 442
      `דהתם ... דהתם`; klal 665 repeats `מחבירו` around a folio). Worse, it
      compares `hebrew_letters_only()` forms, and **two different non-Hebrew
      tokens both normalise to `""` and therefore compare EQUAL** - on klal 616
      that deleted the real folio token `104` as if it were a duplicate.
    - **The folio rule deletes real text.** The token after a header run is
      dropped if it matches `[\d\u05d0-\u05ea"'׳״]{1,5}`, which is *any* Hebrew
      word of 1-5 letters, not a numeral. Traced all 12 firings: 11 removed a
      genuine folio or header word, and **1 removed real text - klal 616 lost
      `אכיל` from `ורב היכי אכיל בשרא`**, because page 221 prints its folio as
      Arabic `104` *before* the header, leaving the first body word where the
      rule expects the numeral. Token geometry settles every case cleanly and is
      the signal the rule should use: every genuine folio sits at relative-y
      <=0.006, the deleted `אכיל` at 0.032.
    - **A running-header word survives in klal 580** (`יר מראכי`), which the
      pytest invariant does not match either - it requires `כללי` to follow.

    **STILL OPEN, and deliberately untouched: 8 more klalim carry the same page
    furniture from an EARLIER extraction, not from this tool** - 279, 368, 415,
    549, 576, 663 (a bare Arabic-digit folio) and 371, 645 (a bare `מלאכי`).
    Confirmed by provenance, not inference: all 12 watermark klalim carry a
    `reconstruct_placeholder_klalim.py` revisit flag and **none of these 8 do**, so
    the reconstruction tool did not write them and re-running it cannot fix them
    (it only fills placeholders, and these hold text). They are `part2.json` /
    `part3.json` edits like any other and need their own go-ahead under the Parts
    2-3 gate. The new Latin-script invariant does NOT cover them - their furniture
    is Hebrew or digits, not Latin - so they are recorded here rather than caught
    by a test. Extent is swept and exact: 8, all in 223-667, none in Part 1.

    **THE TOOL IS FIXED; THE CORPUS IS NOT.** Landed 2026-08-26: a refusal gate on
    any Latin-script token (re-judged against the 12 - **all 12 are now refused**,
    so the fixed tool would never have written them); `drop_seam_duplicate()` no
    longer treats two different non-Hebrew tokens as equal; the folio rule now
    tests token GEOMETRY instead of spelling (**78 -> 45 deletions, 33 real words
    preserved**, every genuine folio still removed - the separation is clean, folios
    at relative-y <=0.006 against `אכיל` at 0.032); and `is_watermark()` moved to
    `corpus_io.py`, since it already existed in `build_corrections_dataset.py` and
    that is exactly why the one tool that writes corpus text from the raw stream
    never had it.

    **THE CORPUS IS FIXED TOO, 2026-08-26, user-authorised.** The user chose
    re-running the fixed tool over reverting to placeholders. Done in the
    documented two steps, the same shape as 930ce76: the 12 were reverted to
    placeholders, then `--apply` rewrote them. **All 12 came back clean** -
    watermark gone, the 6 duplicated catchwords gone, the folios gone, and klal
    616 reads `היכי אכיל בשרא` again. Yield unchanged at 596 klalim with text;
    each of the 12 carries a fresh unreviewed-machine-output revisit flag. Word
    counts moved only by what was removed (250: 242->238, 616: 994->991, 580:
    1027->1021). `rebuild_all.sh --skip-vision` and `sefaria_export/` both
    regenerated; the export now carries 0 Latin-script segments.

    Making the re-run possible needed two further fixes, both found by re-running
    the tool against these 12 rather than by reading it:
    - The watermark had to be STRIPPED, not merely refused - a refusal gate alone
      would have refused all 12 forever. Stripping a literal Latin footer is not a
      retune of the Hebrew furniture heuristic, so `_is_scan_furniture()` removes
      it before the run logic ever sees it.
    - **The folio is set at the page FOOT on some pages, not the head** - pages 86,
      126 and 246 print it at relative-y 0.93, right beside the watermark - so a
      header-band test missed three of them. A bare Arabic-digit token is now
      furniture wherever it sits: this work numbers in Hebrew letters, and the 222
      reviewed klalim of Part 1 contain zero bare Arabic-digit tokens.
    - `FURNITURE_WORDS` listed the OCR variants of the header's FIRST word
      (`יד/יר/יך`) but only the exact `מלאכי` for its second, so page 210's
      `יר מראכי` was a one-word run, fell under the run>=2 threshold, and left a
      running header in klal 580. The four forms the corpus invariant's own
      `מ[לר][אר]כי` admits are now all listed.

    **The invariant landed** (`test_no_scan_watermark_in_clean_text`): no klal text
    may contain a Latin-script token. Verified it can actually fail, per Lesson 25 -
    run against the pre-fix backup it reports all 12 offenders, against the live
    corpus 0. 319 tests pass.

21. **CODE REVIEW COMPLETED 2026-08-26 — three scoped passes, 26 findings
    triaged against the two parked reviews, 24 fixed, 2 refuted.** Method, because
    it is the part worth reusing: `/code-review high` over
    (a) `review_server.py` + `app.js`, (b) the three corpus-writing tools,
    (c) `repair_filters/` + `synthesize_multi_witness.py` — one at a time, source
    only. Every claim was reproduced by running something before being acted on.
    Findings both independent runs raised were the highest-yield; findings only
    one run raised were where the two refutations came from.

    **Fixed — correctness, in rough order of what they could have cost:**
    - `repair_word()` fabricated readings out of abbreviations. `hebrew_letters_only`
      strips gershayim, so `א"ה` (אבן העזר) was arbitrated as `אה` vs `אלה` and
      "repaired" to `א"לה` — not a word, an abbreviation, or anything DocAI read.
      **97 tokens in the live stream** (`א"ה`×73, `א"א`×20, `ש"א`×3, `וא"ה`×1). It
      feeds `docai_repaired`, which the frontend offers as a SELECTABLE reading,
      so one click would have written a fabricated word into the corpus carrying
      an engine's authority. Guarded on internal gershayim only, so the
      trailing-geresh case its own test protects still repairs. 0 reached the
      queue; 893 → 796 repairs stream-wide, all 97 of the difference being these.
    - **A Save with no option selected recorded a null decision — and had already
      done so four times** (klal 90 w4, 88 w1149, 164 w55, 2 w632; three on
      2026-08-24/25). `saveDisputedDecision()` falls back to `source='final_text'`,
      which a `delete` or `ai_flag` entry does not have, so it POSTed
      `chosen_text: null`. Those rows mark the word decided and answer its revisit
      flag while `apply_reviewer_decisions.py` can never promote them, and the log
      is append-only. Guarded in the client AND at the write site —
      `api_post_manual_decision()` has had exactly this check since it was written
      and `api_post_disputed_decision()` never got it. **The four existing rows are
      still there and still count as decisions; superseding them is a reviewer
      action, not a code fix.**
    - **`--apply` wrote the corpus and then crashed before recording a single
      revisit flag**, whenever `sefaria_reference_corpus/word_freq.json` is absent
      — which is a fresh clone, since it is gitignored. Absent cache ⇒ both lexical
      gates skipped silently ⇒ every located span written unchecked ⇒ `TypeError`
      formatting `None` into the flag note, after the write. Now refuses to
      `--apply` at all without the cache, and the notes are built before the write.
    - **12 klalim render a duplicate proposed insertion** (84, 88, 106, 114, 138,
      159, 164, 171, 175, 193, 211, 219 — including 219, the klal the newer block
      was written for): two blocks in `app.js` both rendered
      `gapsBefore[words.length]`, the newer one having superseded the older without
      removing it.
    - **An answered word-level flag rendered decided in the scan pane and nav badge
      and still open in the text pane**, on 5 standalone flags (klal 4 w199/w364,
      163 w427/w573, 167 w24) — `renderKlalBody` hardcoded the class instead of
      calling `wordState()`, so the 2026-08-25 `flag_answered` fix reached one pane
      of three. Klal 163 is the klal that fix was written for.
    - `drop_seam_duplicate()` compared `hebrew_letters_only()` forms, and two
      DIFFERENT non-Hebrew tokens both normalise to `""` and so compared equal —
      on klal 616 it deleted the real folio `104` as a "duplicate" of `Google`.
    - The folio rule deleted real body words: see item 20. Replaced with a
      token-geometry test; **78 → 45 deletions across all spans, 33 real words
      preserved** (`תלת`, `גבי`, `פליגי`, `דאית`, `רבי`, `דרב`, `היא`, `ושוב`,
      `בשם`, `דאפשר`, `היה`, `אכיל`…), every genuine folio still removed.
    - `_reinsert_nonletters()` put the restored ל after a trailing mark
      (`בצלא.` → `בצלא.ל`). Latent, 0 live occurrences.
    - `page_words()` raised `TypeError` on a DocAI page that was never extracted;
      `seam` was counted on the unfiltered token list and sliced a filtered one;
      a furniture run longer than the max was partially stripped, the opposite of
      what its comment says. All latent, all cheap.
    - The insert-bbox estimate clamped both edges at 1.0 independently, collapsing
      the box to zero width at the right page edge. Latent (0 of 40 today).
    - `docai_verdicts()`'s drift guard was **fail-open**: `words_by_klal=None`
      disabled it, and `validate_suppression_filters.py` — the harness whose whole
      job is measuring these filters — called it that way, so it was structurally
      measuring something production no longer does (Lesson 25's shape). Default
      now derives the corpus and guards; opting out is explicit.
    - The synthesizer told an operator "the stored text is correct in each" for a
      bucket that now includes positions where a reviewer's correction is recorded
      but NOT yet applied — i.e. exactly where the corpus is known to be wrong.

    **Fixed — the standing shared-module rule, which is where three of these came
    from:** `is_watermark()`/`WATERMARK_WORDS` and `is_placeholder()`/`PLACEHOLDER_RE`
    both moved to `corpus_io.py` (the watermark filter existed in
    `build_corrections_dataset.py` and nowhere else, which is precisely why the
    reconstruction tool wrote the watermark into 12 klalim; the placeholder rule was
    byte-identical in two files that are two halves of one decision — what gets
    rebuilt and what ships to Sefaria as empty). `reconstruct_placeholder_klalim.py`
    now uses `docai_filter.reference_frequencies()` instead of a third, unnormalised
    private loader (latent: 0 of 185,593 keys carry a non-letter today, fatal the day
    that cache is rebuilt keeping the marks), and `cio.save_part1()` instead of a
    third private `json.dump`. Its `HEADER_CONTAMINATION_RE` now includes the pytest
    invariant's own pattern verbatim — the two were **non-overlapping**, so the tool's
    stated contract ("a reconstruction that would fail the invariants is simply not
    written") was not enforced: `יר מראכי כללי הביח` passed the tool and failed pytest,
    i.e. damage committed first and found afterwards.

    **Fixed — the interactive hot path.** `GET /api/page/73` went **182.5 ms → 9.6 ms**;
    `/api/klal/88` 72.6 → 8.0 ms. Both parked reviews found the cause independently
    (2026-08-25 C1/C2, 2026-08-26 H9/H10/H11): the 1.8 MB decision log was re-parsed
    **25 times per request**. Memoized `_read_all()` on `(st_mtime_ns, st_size)` rather
    than restructuring two 250-line functions — the log is append-only, so any write
    changes both, and a decision recorded in one tab is still visible to the next
    request. Same treatment for the 187 KB `klal_page_regions.json` (6 parses per
    request). Verified before landing that no consumer mutates the shared records
    (0 of 2,153 rows) — and deliberately NOT applied to `_load_corrections()`, whose
    entries the API handlers DO mutate in place.

    **Fixed — three encodings of one rule.** `_word_pages_map()` (proportional),
    `_word_level_ai_flags()` (last-page-wins) and `_word_scan_position()`
    (first-page-wins) each resolved the same multi-page recurring-word collision
    differently; they disagree on **657 and 293 of the 943 colliding words**.
    Collapsed into `_word_bboxes_resolved()`. Nothing a reviewer sees was wrong
    today — 1 of 331 open flags sits on a colliding index and the answers happen to
    agree there, 0 of 203 manual corrections sit on one at all — which is luck about
    where the flags fell, not a property of the code.

    **Fixed — the Sefaria export.** `versionNotes` hardcoded "Klalim 1-222 … 223-667
    have not" even under `--part1-only`, where 223-667 are not in the file; it now
    derives from what is actually exported and **discloses the 44 machine
    reconstructions**, which for a public version file under a real citation address
    is the most load-bearing caveat there is. `--format sefaria --klal-id N` could
    never succeed (the version file addresses klalim by position in a dense 1..N
    array) and failed by blaming the corpus and recommending a flag that was already
    on; it now refuses up front for the real reason.

    **REFUTED — recorded because a wrong finding that looks handled is worse than
    none:**
    - "`open_count` is served with no consumer — Lesson 29's own pattern." It has a
      consumer: `test_nav_tristate_matches_what_each_word_actually_renders_as`
      asserts it never goes negative, which is the canary that caught the klal 88
      "−1" fix-on-fix arc. Kept, with a comment saying so.
    - "7 klalim (280, 430, 431, 432, 438, 539, 643) carry a `needs_revisit` flag
      describing a reconstruction while storing a placeholder." All 7 have a LATER
      flag with `needs_revisit: false` — they were correctly cleared when 930ce76
      withdrew their text. The finding read the flag's note without checking whether
      the flag was still open. The other half of that finding (232 ledger rows across
      51 klal ids) is true and is the append-only design working as intended.

    **Checked and left alone, with the reason:** `repair_word()` treats absence from
    the reference corpus as proof of corruption when `collapsed_freq == 0`, so
    `אוף` (Aramaic "also", 4 occurrences) repairs to `אלוף` ("chief") on the strength
    of 5 references. 13 tokens / 72 occurrences sit in that thin-evidence band and
    most are genuine repairs, so tightening it trades real repairs for this one —
    a threshold decision, not a bug, and Lesson 31 says hand it over rather than
    tune it. `synthesize_multi_witness.attach_scan_positions()` can take a box from
    an `insert` candidate whose bbox is an estimate (0 collisions today).
    `review_server.py` remains a 1,736-line module and
    `synthesize_multi_witness.py` still imports its private helpers — both real,
    both structural refactors that want their own session and their own before/after.

22. **CONFIRMED 2026-08-26 — the detectors that WOULD catch these errors are not
    wired to anything, and `lexicon.txt` cannot fail a word it learned from the
    corpus's own OCR.** Raised by the reviewer after hand-repairing three words in
    klal 84 that no dispute had flagged. Three words, three different causes, all
    verified by running the tools rather than reading them:

    **(a) `בחרא` -> `בחדא` (klal 84 w23) — the detector already finds it, today.**
    `tools/detect_real_word_substitution.py` prints exactly this candidate in its
    current output (`corrupt form 2x in Part 1; correction 331x independently
    attested`). It is `[STANDALONE]`: it prints to stdout, is not in
    `rebuild_all.sh`, and writes no `klal_flag` rows — so nothing routes it to the
    dashboard. **Of its 121 findings, 57 are invisible to a reviewer**, this one
    among them. That is Lesson 29 at the level of a whole tool: computed,
    correct, and shown to nobody. Context confirms the reviewer's reading —
    `תרי זמני או בחדא מסכתא או בתרי מסכתי` ("either in ONE tractate or in TWO")
    — so `בחדא`, not `בתרא`, despite `בתרא` being the commoner word overall
    (620x vs 331x). **Swept: klal 75 w608 carries the IDENTICAL `בחרא` error, is
    also unflagged, and is still uncorrected** (`אמר רב בחרא מלתא גופא`).

    **(b) `כסכתא` -> `מסכתא` (klal 84 w24) — two independent reasons it passed.**
    First, כ/מ is **not in `detect_real_word_substitution.py`'s `CONFUSION_PAIRS`**
    (15 empirically-observed pairs; this is not one). Adding it surfaces **20
    candidates in Part 1**, several obviously real (`אמילת`->`אכילת` 571x,
    `הבכות`->`הבמות` 114x, `עכדו'`->`עמדו` 148x). Second, and more important:
    **`כסכתא` IS IN `lexicon.txt`**, so no lexicon-membership check can ever fail
    it. `lexicon.txt` was built from THIS corpus's own OCR output, so it absorbed
    the error and now vindicates it — already documented for the ligature bug
    ("lexicon.txt cannot catch the ligature corruption - it contains it"), and this
    is the same hole in a second class. **Measured: 4,251 of its 19,015 entries
    (22.4%) have ZERO attestation in the independent reference corpus.**
    `בחרא` is in there too.

    **(c) `לא` -> `אלא` (klal 84 w8) — the ligature pass only ever ran in one
    direction, and this word is out of reach of all of them anyway.**
    `repair_filters/docai_filter.repair_word()` models the `ﭏ` sort dropping its
    **ל** (inserts a ל after an א: `אא`->`אלא`, `ושמוא`->`ושמואל`). It has no rule
    for the sort dropping its **א**, which is what happened here. A mirror sweep
    finds **3 such candidates in Part 1** — `שמול`->`שמואל` (klal 143 w684,
    `רב פפא בר שמול`, genuine, already flagged), klal 30 w1521 `תשל` (uncertain,
    unflagged), and klal 7 w677 `ויגל`, which is a **false positive**: the text is
    Psalms 16:9 `לכן שמח לבי ויגל`, where `ויגל` is correct. So the direction gap
    is real but small in Part 1 — 1 confirmed, 1 open, 1 false.
    **The harder point: no detector in this repo could have caught THIS word.**
    All three (`repair_word`, `detect_real_word_substitution`,
    `detect_insertion_deletion`) gate on the stored form having ZERO independent
    attestation, and `לא` is attested **82,442** times. A real, extremely common
    word standing where a different real word belongs is invisible to every
    frequency arbiter here by construction; only context or the scan finds it.
    This is the honest answer to "I thought we did a pass to find all those":
    the pass was one-directional AND structurally blind to this shape.

    **Not fixed — each needs a decision, none is an agent's call.**
    **ALL THREE FIXED 2026-08-26, user-authorised ("push the ones that are real -
    check them all"). See item 23 for what was pushed, and for a correction to the
    "57 unrouted" figure above, which OVERSTATED the problem.

23. **CLOSED 2026-08-26 - every detector finding triaged against the independent
    witnesses; 15 real ones pushed, and the routing gap turned out to be far
    smaller than item 22 claimed.** Ran `detect_real_word_substitution.py` +
    `detect_insertion_deletion.py`, merged them to **262 distinct (klal, word)
    positions**, and cross-checked EVERY one against Surya, both VLM passes and
    DocAI: **50** where an independent engine reads the PROPOSAL, 149 where one
    reads the STORED form, 29 split, 34 with no reading there.

    **CORRECTION to item 22's "57 of 121 reach nobody".** That counted raw
    findings. Of the 50 that survive witness cross-check, **46 were already
    visible in the dashboard** - the multi-witness consensus pipeline routes them
    already, which is what it is for. Only **4** were genuinely missing. The large
    unrouted remainder is the UNCORROBORATED tail, which the witnesses actively
    contradict (149 of 262). The tools are not "computed and shown to nobody";
    their high-confidence output is largely already routed. Item 22's framing was
    wrong and is corrected here rather than quietly dropped.

    **Pushed as word-level flags (15), each read in context first, none applied to
    the corpus:** klal 10 w1 `איידו`->`איידי` (unanimous 3/3; the next word is
    `דאיידי`); 53 w218 `במשרו`->`במשהו`/`בבשרו` (engines split, needs the scan);
    74 w659 `בסרק`->`בפרק`; 167 w739 `מקטי`->`מקמי`; 117 w43 `כרתב`->`כתב`;
    152 w98 `בסרק`->`בפרק`; 169 w1074 `שרוא`->`שהוא`; 198 w892 `זלזה`->`לזה`;
    3 w262 `מאיין`->`מניין`; 177 w340 `למיפך`->`למיפרך`; 144 w907
    `בישרץ`->**`בישראל`**; 150 w684 `מקטי`->`מקמי`/`מקרי`; 81 w16
    `בתריתא`->`בתרייתא`; 210 w133 `כתרייתא`->`בתרייתא`; **75 w608 `בחרא` - the
    TWIN of the klal 84 w23 the reviewer hand-repaired**, found by the sweep for
    that fix.

    **Rejected after reading them in context - the detectors were wrong:**
    `אאמוראי` (א+אמוראי, a legitimate prefix, 2x in Part 1), `דאיך` (ד+איך, 4x),
    `ואוף` (Aramaic `אוף` = also, 2x), `למהרר` (the stored text is `למה"רר`, a
    title abbreviation), `רבואתא` x2 (a variant of `רבוותא`, 17x attested - the
    proposed `רבותא` means something else), `בבריתא` x2 (a defective spelling of
    `בברייתא`, not a misread letter), plus 10 positions where the "correction" was
    the word minus a legitimate Hebrew prefix or suffix (`דהרוצה` = ד+הרוצה).
    **And one where the proposal was wrong but the word WAS corrupt**: `בישרץ` was
    offered as `בשרץ` ("in a creeping thing") in a passage on the thirteen
    hermeneutical rules; context gives `ורבתה מחלוקת בישראל`, which is what was
    flagged instead. Frequency alone gets these wrong; context decides.

    **Pipeline fixes closing item 22's three causes:**
    - `detect_real_word_substitution.py` gained the **כ/מ** and **ח/ת** pairs, and
      its `MIN_INDEPENDENT_FREQUENCY` floor went **50 -> 40**, because
      `כסכתא`->`מסכתא` missed by exactly five occurrences (`מסכתא` is attested 45x;
      the reference corpus mostly writes `מסכת`). Measured before changing:
      124 -> 138 findings, the 18 gained the same quality as the rest, including
      klal 1's known `דנראח`->`דנראה`. The reviewer's `כסכתא` is now caught.
    - `repair_word()` now models the `ﭏ` sort dropping **either** letter. Two bugs
      surfaced doing it: an early `if "א" not in letters: return None` guard
      excluded the entire new direction (the surviving letter there is the `ל`),
      and `_reinsert_nonletters()` hardcoded the restored letter as `ל`, turning
      `שמול` into `שמולל`. A 2-letter minimum was also needed: without it the bare
      token `ל` "repairs" to `אל` **83 times** - two thirds of the new direction's
      output - purely because `אל` (4,624) happens to be four times commoner than
      standalone `ל` (1,154), which clears MIN_FREQ_RATIO by accident. After the
      guard: dropped-lamed unchanged at **796**, dropped-alef **43**, and only
      **4** reach the review queue, all `שמואל` variants, all genuine.

24. **REVIEWED 2026-08-26 (user-requested): the words that exist in Yad Malachi
    and in none of the 166 reference books.** Written to
    `lexicon_yad_malachi_only.json` - per word, its Part 1 count, every
    occurrence, and the nearest attested forms with edit type.

    `lexicon.txt` holds 19,015 entries; **4,251 (22.4%) are absent from all 166
    books (6.18M words)** - 1,261 present in Part 1, 2,924 only in gated Parts
    2/3, and 66 in no part file at all (stale rows). Narrowing to Part 1, 4+
    letters, no gershayim: **1,162 words**, of which **536 sit one edit from a
    form attested >=40x** and **386 of those are a hapax in Part 1** - the
    top-suspicion tier. The other **626 have no near neighbour** and are most
    likely genuine Yad Malachi vocabulary. (Re-measured after the 79-row purge
    below, and now reproducible: `tools/review_lexicon_only_words.py` writes the
    report, which had been produced by a throwaway script - the
    hand-maintained-derived-file pattern Lesson 13 forbids.)

    **Why this list exists at all:** `lexicon.txt` was built from THIS corpus's
    own OCR output, so it contains the errors and then vindicates them - `כסכתא`
    and `בחרא` are both IN it. Every check run against `lexicon.txt` is only as
    independent as `lexicon.txt`, which is not independent at all. Already
    documented for the ligature bug; **22.4% is the first measurement of how wide
    the hole is.** `tools/validate_lexicon_independent.py` exists to surface
    exactly this, and is read-only, standalone and wired to nothing.

    **PURGED 2026-08-26, user-authorised ("confirm and remove those"): 79 rows,
    each individually justified, 19,015 -> 18,936.** Two sets, deliberately kept
    narrow, and NOT the 4,251:
    - **66 orphan rows** - in `lexicon.txt`, zero attestation in the reference
      corpus, AND appearing in no klal of any part file. They cannot be Yad
      Malachi vocabulary, because the work does not contain them. Visibly junk
      (`דדסומתימאא`, `הבודאבר`, `ורנעשמרת`) plus **learned page furniture**
      (`מראכי`, `כרלי`, `כררי`, `הלמר`) - header words the lexicon absorbed before
      the header contamination was cleaned out of the corpus. Count now 0.
    - **13 confirmed-corrupt forms** - the OCR errors verified in context this
      session: `כסכתא`, `בחרא`, `כרתב`, `שרוא`, `בסרק`, `בישרץ`, `מקטי`,
      `כתרייתא`, `מאיין`, `למיפך`, `בתריתא`, `זלזה`, `איידו`. Precedented by the
      2026-08-15 purge of 24 dropped-lamed forms. (`במשרו` was already absent.)

    **`לא` was deliberately NOT removed**, though the reviewer repaired it at klal
    84 w8. It is attested **82,442** times - a real word that was simply wrong in
    that one position. The rule applied throughout: remove a form only when it has
    zero independent attestation, never merely because one instance of it was
    wrong. `כתרייתא` was checked separately and does qualify - its putative base
    `תרייתא` occurs nowhere at all, so it is a ב/כ misread of `בתרייתא` (120x), not
    a legitimate `כ`+noun.

    **Effect, verified:** all 13 now surface in
    `validate_part1_corpus_integrity.py` check 5 (Part 1 not-in-lexicon: 959
    distinct words), covering **22 Part 1 positions** that the lexicon previously
    whitelisted. Swept per the standing rule: **0 of those 22 are unflagged** - the
    15 pushed above plus existing flags and the reviewer's own decisions cover
    every one. Zero-attestation share moved 22.4% -> 22.0%, which is the honest
    size of the dent: the remaining **4,172** entries are the tier
    `validate_lexicon_independent.py` explicitly warns is "NOT a purge list".

    **SEFARIA'S DICTIONARIES ADDED AS A THIRD LEXICAL SIGNAL, 2026-08-26
    (user-requested).** `tools/lookup_sefaria_dictionaries.py` queries the public
    `/api/words/` endpoint (Jastrow, Klein, BDB - no key). This is a different
    KIND of signal from `word_freq.json`: that counts occurrences in 166 books,
    this asks a lexicographer whether a form is a word at all, so a rare-but-real
    Rabbinic word can be absent from 6.18M words of running text and still have a
    Jastrow entry. Jastrow is the dictionary of Talmudic Aramaic - this text's own
    register. 1,878 forms fetched and cached (one line per lookup, resumable).

    **The method was validated against known ground truth before its output was
    used, and the first version FAILED that check.** Stripping a leading particle
    to find a headword - the obvious mitigation for the endpoint matching
    headwords only - **destroys the signal**: 8 of 13 confirmed-corrupt forms
    "resolve" that way, because stripping a letter that is not a prefix lands on a
    different real word (`כסכתא` -> `סכתא`, a peg; `בחרא` -> `חרא`; `בישרץ` ->
    `ישרץ`). Dropped. On BARE forms the signal is clean in one direction only,
    and that asymmetry is the whole usable content:
    - **0 of 13 confirmed-corrupt forms have a dictionary entry** - so *having*
      an entry is strong evidence a form is real.
    - **7 of 8 confirmed-legitimate forms have no entry either** - so *lacking*
      one means almost nothing, since most words in running text are prefixed or
      inflected.

    Applied to the 549: **54 stored forms are dictionary words** and 4 more have a
    dictionary entry where the proposal does not - **58 confidently cleared**, the
    frequency-based suspicion simply wrong. 384 have a supported proposal and an
    unlisted stored form (consistent with corruption, not proof of it), 107 give
    no signal.

    **It also caught one of this session's own flags.** klal 177 w340 was flagged
    `למיפך` -> `למיפרך`; the dictionary has **`מיפך` (`מֵיפַךְ`, to reverse) and
    nothing for `מיפרך`**, so the stored form is most likely the legitimate
    ל+מיפך. The proposal is retracted in a superseding ledger entry and the flag
    left open. Exactly what a third, differently-failing signal is for (Lesson 9).

    **REVIEWABLE 2026-08-26 (reviewer: "are the 384 words flagged? how can i
    review?" - they were not).** 374 words occupying 626 corpus positions had no
    route to a human at all: only 63 positions were visible, **563 across 143
    klalim were not**. Fixed structurally rather than by flagging them:
    `build_lexical_defect_report.py` now runs as **stage 4b, BEFORE assemble**,
    and `merge_lexical_defects()` folds its sharpest tier into the review queue -
    the same "a witness contributes a source file the pipeline reads, it never
    edits the pipeline's own product" rule finding C1 established for the
    multi-witness synthesizer.

    **Deliberately NOT flags.** These entries are regenerated by every rebuild and
    disappear when the corpus moves under them; nothing is written to the
    append-only ledger. 563 permanent flags on unread material is precisely how
    the 1,496-flag queue happened (item 1). Widening or narrowing the tier now
    costs nothing and leaves no residue.

    **The tier is a documented knob**, `REVIEW_MIN_REF` in
    `assemble_corrections_dataset.py`, currently **500** - the proposal must be
    attested >=500x and the stored form must occur once here. That yields **56
    entries across 36 klalim** on a queue of 883 (+6%). Measured alternatives:
    >=200 gives 111 positions, >=40 gives 219, no floor gives all 563 - a 53%
    larger queue of material nobody has read. Positions a human has already ruled
    on are skipped, so no entry can shadow a decision.

    Two of the repo's own gates caught real defects in this while it was being
    built, which is the system working: the provenance invariant refused entries
    from a source it did not know (they would have been destroyed by the next
    rebuild), and the entry-shape invariant refused a proposal carried in a field
    **nothing renders** - Lesson 29, in code written the same day it was cited
    repeatedly. The proposal is now its own option card in the panel, labelled
    "not an engine reading", and attributed via `lexical_source` exactly as a
    consensus dispute is attributed via `consensus_engines`.

    **Still not done:** the ~500 positions below the tier remain unread, and the
    dictionary cannot settle them - it is silent on prefixed forms by
    construction. Lower `REVIEW_MIN_REF` to surface more; frequency alone
    demonstrably gets some wrong (see `רבואתא`, `בישרץ`).

    **Noticed while here, pre-existing, NOT addressed:**
    `validate_part1_corpus_integrity.py` check 2b reports **7 non-Hebrew
    characters** sitting in Part 1 text - a Greek `Π` (klal 39 w252), three `&`
    (klal 69 w338, 77 w11, 167 w24), two `!` (klal 66 w112, 74 w443) and a `;`
    (klal 176 w694). The new `test_no_scan_watermark_in_clean_text` invariant does
    NOT catch these: it matches `[A-Za-z]`, and none of these are Latin letters.
    They are flagged as DATA issues needing scan verification, and widening the
    invariant would make `rebuild_all.sh` fail on all 7 - a decision, not a
    default.

25. **RETROSPECTIVE 2026-08-26 (user-requested): were today's fixes real, and
    were they repaired structurally or patched once?** Audited against the code,
    not against how the fixes were written up (Lesson 19). Every issue below was
    reproduced before being fixed, so "real" is not in doubt for any of them;
    the interesting column is the second one.

    **Repaired structurally - a future occurrence is now caught by something:**

    | issue | what makes it not-a-one-off |
    |---|---|
    | scan watermark in 12 klalim | new GATED invariant `test_no_scan_watermark_in_clean_text` catches the class from ANY writer, not just this tool; `is_watermark` moved to `corpus_io` |
    | corpus word boxed on a page header (8 klalim) | `header_furniture_indices()` in `corpus_io`, used by the one alignment both the server and the synthesizer share + new gated test |
    | end-of-klal gap marker drawn twice (12 klalim) | new gated test asserting only one renderer exists |
    | Save with nothing selected wrote a null decision | guard at the SERVER write site (not just the client) + new test asserting BOTH POST handlers agree |
    | `repair_word` fabricating readings from abbreviations (97 tokens) | fixed in the shared filter + new test |
    | ligature pass running in one direction only | both directions + new test covering all three sub-bugs it exposed |
    | 1.8 MB decision log parsed 25x per request | memoized at the source (`_read_all`), so every present and future caller benefits |
    | `is_placeholder` / `FURNITURE_WORDS` / `WATERMARK_WORDS` duplicated | all three consolidated into `corpus_io`, the module that exists for exactly this |
    | **detectors that found real errors and told nobody** | **now pipeline stage 5b** - `build_lexical_defect_report.py` regenerates `lexical_defect_report.json` on every rebuild (299 candidates / 96 klalim). They cost 0.1s; the reason given for leaving them out never existed. |

    **Honestly one-off, and here is what would make each structural:**
    - ~~**The lexicon purge (79 rows) is a data edit with no gate behind it.**~~
      **CLOSED in the same pass that identified it.** `lexicon.txt` has no
      generator in this repo and nothing stopped it re-absorbing the OCR errors
      it had just been purged of - the same file was purged by hand in
      2026-08-15 and again 2026-08-26, and neither purge left anything behind to
      hold. `test_lexicon_does_not_whitelist_a_known_corrupt_form` is now in the
      gated suite, listing all 14 confirmed-corrupt forms. Verified it can
      actually fail, per Lesson 25: re-appending `כסכתא` fails the suite,
      removing it passes. Adding to that list is now the documented way to make a
      confirmed reading stick.
    - **The 15 pushed flags and the 12 rewritten klalim are one-off by design** -
      they are review items and corpus content, not mechanisms. Correct as such.
    - **The folio-geometry rule and the `drop_seam_duplicate` empty-string fix
      have no regression test.** Both are inside
      `reconstruct_placeholder_klalim.py`, which no test exercises at all; the
      corpus invariants catch their OUTPUT only if a bad reconstruction is
      actually written. The refusal gate makes that unlikely, not impossible.
    - **The export's `versionNotes` scope fix has no test** either; it would be
      caught only by someone reading a shipped version file.

    **Still standing from today, not fixed:**
    - **4 null-decision rows remain in the ledger** (klal 90 w4, 88 w1149,
      164 w55, 2 w632). The guard stops new ones; it cannot remove these, because
      the log is append-only. They still mark those words decided. Superseding
      them is a reviewer action.
    - **~475 lexicon-only Part 1 words corroborated by frequency alone are
      unread** (item 24).
    - **8 klalim carry pre-existing page furniture** from an earlier extraction,
      under the Parts 2-3 gate (item 20).
    - **7 non-Hebrew characters in Part 1** that the new invariant does not match
      (item 24).

26. **[FULLY CLOSED 2026-09-01 — 0 `&` remain corpus-wide, verified by content; item 37 had recorded one survivor at klal 77 w11.]** RESOLVED AGAINST THE SCAN 2026-08-26: the 7 non-Hebrew characters are not
    one thing, and DELETING them would be wrong for four of them.** The reviewer
    asked whether they could simply be removed. They were rendered from
    `images/pdf_pages` at 4x and read directly (Lesson 14/30 - render and look,
    do not infer). Every one is now flagged at its word index with the reading.

    | klal / word | stored | what the page actually prints | action |
    |---|---|---|---|
    | 69 w338 | `&` | `כגון ﭏ אלהים ה'` — a list of DIVINE NAMES | replace with `אל` |
    | 77 w11 | `&` | `נוטה ﭏ הודאי` | replace with `אל` |
    | 167 w24 | `&` | `פנים ﭏ פנים` — the standard idiom | replace with `אל` |
    | 74 w443 | `!` | `ע"ב ב'.` — a geresh then a period | replace with `.` |
    | 39 w252 | `Π` | the printed FOLIO at the top of page 28 | delete |
    | 66 w112 | `!` | a short mark between `ב"ד` and `חבירו`, unidentified | needs a human eye |
    | 176 w694 | `;` | a semicolon-like mark IS printed there | probably correct as transcribed |

    **The three `&` are the alef-lamed ligature `ﭏ` losing BOTH its letters at
    once** - the same worn sort behind Lesson 24's dropped-lamed bug and behind
    `שמול`->`שמואל`, failing a third way. Its shape genuinely resembles an
    ampersand, which is why DocAI produced one. So this is not a stray-character
    problem: it is the ligature problem again, and deleting the `&` would have
    silently removed the word `אל` from three klalim.

    **Why they were not removed directly:** corpus text is never hand-edited
    (`START_HERE.md`, single-source-of-truth rule). Each is recorded as a
    word-level flag with the scan reading; `apply_reviewer_decisions.py` promotes
    them once the reviewer rules.

27. **[CLOSED 2026-09-01 - all three repaired; see item 1A for the evidence and for the index-vs-ledger error this item's own follow-ups kept making.]** NEW 2026-08-26 - PART 1 CARRIES PAGE-SEAM FURNITURE TOO, not just the
    reconstructions.** Found by sweeping for the class behind klal 39's `Π`
    (standing rule), which turned out to be a folio sitting next to page 27's
    CATCHWORD. Swept all of Part 1 for near-duplicate word pairs at a page
    boundary: **3 klalim**, all confirmed against the DocAI token stream at both
    pages.
    - **klal 39** w251-253: catchword `דבכולהן` + folio `Π` + the real `דבכולהו`.
    - **klal 74** w414-418: page 35's catchword `אמר` plus a duplicated `רבא אמר`
      - the corpus stores `אמר רבא אמר רבא אמר רב יהודה` where the page reads
      `אמר רבא אמר רב יהודה`. Two spurious words.
    - **klal 210** w64-67: `דהלכה : לא דהלכה כקמייתא` - the printed folio **`לא`
      (31)** between two copies of the catchword. **Note this folio is a HEBREW
      NUMERAL**, so the bare-Arabic-digit rule that cleaned the reconstructions
      cannot see it, and neither can the Latin-script invariant.
    All three are flagged. This is the same defect class as item 20's, in the
    REVIEWED third of the corpus, from an extraction that predates this session.
    The existing `validate_catchword_continuity.py` checks that catchwords MATCH
    across a seam; nothing checked whether one ended up inside `clean_text`.

28. **MEASURED 2026-08-26 - the `ai-semantic-spotcheck-round4` flag pass (242
    word-level flags, written 2026-08-18) has a real noise floor, found because
    the reviewer read one.** Report: klal 66 w67, "the suggestion is nonsensical
    and the explanation is gibberish". Both true - it proposed `אמרה` -> `נקראת`
    because of a "doubled final tav", and **`אמרה` contains no tav at all**, while
    `התורה אמרה` is a standard phrase with `אמרה` attested 1,785x. Flag retracted.

    That prompted a measurement of all 238 still-open flags from that pass,
    against the corpus and the independent reference corpus:

    | | |
    |---|---|
    | plausible or arguable | **177** |
    | suggestion is the SAME word - proposes nothing | **42** |
    | note describes a word no longer at that index | **14** |
    | suggestion unrelated AND the stored word is common | **5** |

    - The **42** self-suggestions (`איהו`->`איהו`, `דאם`->`דאם`, `עוד`->`עוד`) are
      pure noise. `suggestionIsPlausible()` already hides the SUGGESTION at display
      time, but the FLAG still lights the word red, so the reviewer is sent to a
      word with nothing to decide.
    - The **5** unrelated ones are the reported class: klal 66 w67
      `אמרה`->`נקראת`, klal 66 w120 `הרי`->`ע"פ` (**zero letters in common**, and
      `הרי` is attested 15,557x), klal 200 w144 `ועל`->`אלו`, plus klal 94 w188 and
      217 w510 which propose the literal `??`.
    - The **14** drifted ones are the good case in disguise: the note names the
      OLD reading and the corpus already holds the corrected one (`אכל` -> `אבל`,
      `ישרץ` -> `ישראל`). **But only 6 of the 14 render as answered**, so **8 flags
      are still lit red on words that were already fixed.**

    **THE "UNRELATED" BUCKET IS NOT NONSENSE - IT IS MIS-INDEXED, and that is
    worse.** The reviewer read the second one (klal 66 w120, `הרי` -> `ע"פ`,
    reason "ס for פ", citing the phrase `אף על פי שהניח`) and said "the note is on
    the following dispute - ayin-peh". Exactly right. **The note's real target is
    w135**, which stores `ע"ס` inside `אף ע"ס שהניח` - the very phrase the reason
    quotes, 15 words from where the flag was filed. Rendered page 34 at 4x and
    read it: **the page prints `אף ע"פ שהניח` with an unmistakable peh.** So the
    2026-08-18 pass FOUND a real ס/פ error, recorded it against the wrong word,
    and it then sat for eight days looking like gibberish. Recovered only because
    a human read the bad flag and recognised what it was about. w120 retracted,
    **w135 flagged and scan-confirmed**.

    **ROOT CAUSE FOUND 2026-08-26, on the reviewer asking whether I had actually
    looked for one. I had not** - I fixed the two instances and stopped at
    "mis-indexed", which is a symptom. The cause is an **OFF-BY-ONE confined to
    the 2026-08-18T20:36 batch**: some corrections were attached to the word
    BEFORE their real target. The reviewer's own words were the diagnosis - "the
    note is on the following dispute" - and I under-read them as a description
    rather than a mechanism.

    **Scope, measured per batch** (does a flag's suggestion plausibly fit its own
    word?): 20:36 = **96%** (133/139), and every later batch = **100%**. So this is
    not a broken pass; it is **6 items in one batch**, four of which landed in
    klal 66, which is why the reviewer hit two of them in a row.

    | flagged | note really belongs to | outcome |
    |---|---|---|
    | klal 92 w439 `דבבעיות` | w440 `או` -> `אלו` | **real error, now flagged** |
    | klal 200 w144 `ועל` | w145 `או` -> `אלו` | **real error, now flagged** |
    | klal 97 w387 `טועה` | w388 `דם` -> `הם` | real, already flagged |
    | klal 174 w17 `ד"ה` | w18 `אלא` | already correct - asks nothing |
    | klal 66 w67 `אמרה` | w82 `נקראתת` -> `נקראת` | re-emitted correctly at 22:11 |
    | klal 66 w120 `הרי` | w135 `ע"ס` -> `ע"פ` | **real, scan-confirmed** |

    All six retracted with a pointer to the true target. **Three real corpus
    errors were recovered from flags that read as gibberish**, and one of them
    (klal 66 w135) is confirmed against the ink.

    **What makes these unrecoverable by any detector here:** `או` is attested
    **37,981x** - a perfectly real word in the wrong place. Every lexical detector
    in this repo gates on the stored form being UNATTESTED, so this whole class is
    invisible to them by construction, exactly like the `לא`->`אלא` the reviewer
    found by eye in klal 84. The 2026-08-18 semantic pass is the only thing that
    has ever found them, which is an argument for re-running it correctly rather
    than retiring it.

    Two automatic recovery searches were tried first and **both were too noisy to
    trust** - matching the suggestion against every other word returns mostly
    punctuation artifacts, and matching the reason's cited phrase mostly finds
    legitimate citations of a CORRECT occurrence elsewhere (`משוס`->`משום` because
    `משום ר'` appears correctly at w80/90/173). What worked was the per-batch
    fit-rate above, which localises the damage instead of trying to repair it.

    **39 CLEARED 2026-08-26, user-authorised - and the count is 39, not 42,
    because I nearly repeated this repo's own bug while counting them.** The
    self-suggestion bucket was built by comparing `hebrew_letters_only()` forms,
    which STRIPS GERSHAYIM - the exact mistake fixed in `suggestionIsPlausible()`
    earlier the same day. Three of the "42" propose a real change that is invisible
    to a letters-only comparison: **klal 45 w21 `נלפ"קד` -> `נלפק"ד`** and **klal
    212 w40 `פ"יא` -> `פי"א`** (misplaced gershayim - the same two the display
    filter had been hiding, and the reason that filter was loosened), plus klal 194
    w420 `דמשסתמו` -> `דמשסתמו?`. Those three are LEFT OPEN. Only the 39 whose
    suggestion is the stored word character for character were cleared, each with
    a note stating that the word itself was not examined and is not asserted
    correct - only that the flag asked nothing.

    That pass now has **202 open flags, down from 238**. The 5 mis-indexed and the
    14 drifted are deliberately untouched: the mis-indexed ones have already
29. **DEEP LINKS ADDED 2026-08-26 (reviewer request): a URL now addresses a klal,
    or a klal and a word.**
    `http://127.0.0.1:8420/#klal=66` and `http://127.0.0.1:8420/#klal=66&word=135`.
    So a finding recorded in this file, in a report, or in a message can carry a
    link that lands on the exact word instead of "klal 66, count to 135". The part
    is derived from the klal id, not carried in the URL, so a link to klal 400
    works whether or not the reviewer is currently looking at Part 2. The address
    bar also tracks navigation (`history.replaceState`, so scrolling does not fill
    the Back button), which makes the current view copyable as-is.

    Word spans now carry `data-word-index`, which is what made this addressable at
    all. **The scroll observer was the hazard**: it calls `setActiveKlal` on
    whatever drifts into view, so a smooth scroll let it overwrite the
    destination mid-animation - measured, routing to klal 66 landed on 61. Routing
    mounts, jumps instantly, and holds the observer off until it has settled. Two
    Playwright regressions cover it.

30. **FIXED 2026-08-26 (reviewer: "klal 179 word 267 - clicking does not highlight
    word in scan page") - a defect introduced by item 24's own merge, the same
    day.** The lexical-defect entries were written with `page: None, bbox: None`.
    Two consequences: `api_page()` could not place them, so they fell through to
    the plain-word pass and rendered on the scan as ordinary prose rather than as
    flagged words; and the click fell back to the klal's START page. Klal 179 w267
    is on page 67 in a klal that starts on 66, so the scan showed 66 with nothing
    to highlight.

    Fixed at both ends: `merge_lexical_defects()` now fills the scan position from
    the same alignment the server uses, and the frontend gained `pageForWord()` -
    `corr.page`, then the server's `word_pages` map, then the klal's start page.
    The manual-correction handler had already worked around this privately; the
    disputed and flag handlers had not. All 56 lexical entries now carry a
    position, and klal 179 w267 serves as a `correction` on page 67.

    Swept for the class: **3 other entries** (klal 22 w48, 30 w120, 198 w403) have
    a `page` that disagrees with the alignment map - but each carries its own bbox
    and is servable on its claimed page, so all three highlight correctly. Their
    page came from a verified vision crop, which outranks the proportional
    heuristic; **deliberately not "fixed"**. A new gated invariant,
    `test_every_flagged_word_can_be_located_on_the_scan`, catches the real defect.

    **The 39 cleared flags were re-checked against this session's root cause**
    (item 28's off-by-one) and the file `cleared_flags_2026-08-26.json` lists all
    of them with a deep link each. All 39 came from the defective 20:36 batch,
    which raised the question directly; testing whether each suggestion fixes an
    unattested word 1-2 positions later returns **0 hits**, so they do look like
    genuine self-suggestions rather than mis-paired corrections. That is evidence,
    not proof - the klal 66 misplacements were 15 words, not 1 - and the clearing
    is reversible either way, since the original notes remain in the append-only
    ledger.

29b. **[DUPLICATE ENTRY — the same feature as item 29 above, written twice on the same day. Kept, not deleted, because the two texts differ in detail.]** DEEP LINKS + A COPY CONTROL, 2026-08-26 (reviewer requests). A URL now
    addresses a klal, or a klal and a word:
    `http://127.0.0.1:8420/#klal=66&word=135`. The part is derived from the klal
    id, so a link to klal 400 works whether or not Part 2 is on screen; the
    address bar tracks navigation via `history.replaceState`, so the current view
    is always copyable. Word spans carry `data-word-index`, which is what made
    any of this addressable. **The scroll observer was the hazard** - it calls
    `setActiveKlal` on whatever drifts into view, so a smooth scroll let it
    overwrite the destination mid-animation (routing to klal 66 measurably landed
    on 61); routing now mounts, jumps instantly, and holds the observer off.

    The klal/word header in a correction panel is also a copy button, yielding
    both lines at once:
    `Klal 66 · Word #135 — ע"ס` / `http://127.0.0.1:8420/#klal=66&word=135`.
    It has a non-clipboard fallback, because a copy button that silently does
    nothing is the dead-control shape this file has shipped more than once.
    Three Playwright regressions cover the routing, the address bar and the copy.

30b. **[DUPLICATE ENTRY — same incident as item 30 above.]** FIXED 2026-08-26 (reviewer: "klal 179 word 267 - clicking does not
    highlight word in scan page") - a defect item 24's own merge introduced the
    same day.** The lexical entries were written with `page: None, bbox: None`, so
    `api_page()` could not place them (they rendered as plain prose, not as
    flagged words) and the click fell back to the klal's START page - klal 179
    w267 is on page 67 in a klal starting on 66. Fixed at both ends:
    `merge_lexical_defects()` now fills the scan position from the same alignment
    the server uses, and the frontend gained `pageForWord()` (`corr.page`, then
    `word_pages`, then the klal's start page). All 56 entries now carry a
    position; a new gated invariant catches the class. Swept: 3 other entries
    have a `page` disagreeing with the alignment map, but each carries its own
    bbox and highlights correctly - their page came from a verified vision crop,
    which outranks the heuristic, so they are deliberately left alone.

31. **THE MERGED LEXICAL TIER HAS A PREFIX FALSE-POSITIVE CLASS, and no cheap
    filter separates it (reviewer, klal 179 w267).** `שתרץ` = ש + תרץ ("that he
    answered") is a normal construction; the detector proposed `שרץ` (a creeping
    thing), which is nonsense there. A legitimate prefixed form is unattested as a
    WHOLE in the reference corpus, so an unattested-form detector cannot tell it
    from a corruption.

    **Two suppression rules were tried and both over-suppress.** A plain
    "does it parse as prefix+attested-stem" test excuses 29 of the 56 entries,
    including `כפרק`->`בפרק` (ב/כ, the commonest confusion pair in this print). A
    narrower "does the proposed edit change the STEM rather than the prefix" test
    still suppresses 27, including `מיר`->`מיד` and `וכין`->`ובין`, which look
    real. Both parse; only context decides. **Per Lesson 31 the tuning is handed
    back rather than attempted a third time** - the filter is NOT in the pipeline.
    Raising `REVIEW_MIN_REF` is the blunt lever if the tier proves too noisy.
    klal 179 w267 is recorded as rejected and is the first ground-truth precision
    datapoint on this tier.

32. **LIST PRODUCED 2026-08-26 (reviewer request): every word set with the
    alef-lamed ligature.** `tools/list_ligature_words.py` ->
    `ligature_words.json`. **The ligature codepoint U+FB4F appears ZERO times** in
    part1/2/3.json and zero times in the DocAI stream - checked, not assumed - so
    the sort reaches the corpus as the letters `אל` when read correctly and as one
    of three failure modes otherwise.

    | | Part 1 | Parts 2/3 | total |
    |---|---|---|---|
    | words set with the ligature (contain `אל`) | | | **175 distinct / 2,619 occurrences** |
    | dropped lamed (`אליבא`->`איבא`) | 7 | 314 | 321 |
    | dropped alef (`שמואל`->`שמול`) | 3 | 16 | 19 |
    | both lost (`אל`->`&`) | 3 | 0 | 3 |

    The commonest ligature words are `אלא` (765x), `אלו` (150x), `שמואל` (140x),
    `אליבא` (132x) - which is why this one sort matters more than any other in the
    fount. **13 of the 19 dropped-alef cases are `שמואל` variants**, and 10 of the
    dropped-lamed are `ישרא`->`ישראל`. Part 1's actionable set is only **10
    candidates, 4 of them unflagged**; two of those four are already-resolved
    false positives (`ויגל`, Psalms 16:9; `אוף`, real Aramaic with its own Jastrow
    entry) and are marked as such in the tool so no future run re-proposes them.
    The failure lists are candidates, not confirmed errors - except `both_lost`,
    which is exhaustive, because an ampersand is never Hebrew.

33. **GEMATRIA RULE CONFIRMED AND ENCODED 2026-08-26 (reviewer): a trailing ר in
    a klal marker is a misread ד - with exactly two exceptions, and this corpus
    contains both.** The reviewer's reasoning was "the last digit must be between
    1 and 9". That is right about the UNITS place but not about every numeral:
    Hebrew numerals run high-to-low and a ROUND number simply stops at a higher
    place, so a trailing letter need not be א-ט. Within 1-667 the numbers that
    legitimately end in ר are **200 (`ר`) and 600 (`תר`)** - and klalim 200 and
    600 are exactly the two the corpus has. Every other trailing ר is
    arithmetically impossible (`רמר` = 200+40+200), so the ר must be a ד: this
    fount's ד/ר pair is already a confirmed confusion class.

    Checked corpus-wide: **2 klalim end in ר, both legitimate**. Zero violations
    among klal markers. Encoded as a gated invariant,
    `test_no_klal_marker_ends_in_a_resh_that_should_be_a_dalet`, verified it can
    fail (`רמר`, `קכר`).

    **THE INVARIANT WAS SCOPED TOO NARROWLY AND WOULD HAVE MISSED THE REVIEWER'S
    OWN CASE.** They had just corrected **klal 179 w66 `קנ"ר` -> `קנ"ד`** (154) -
    a numeral in the BODY text, not a klal marker. `קנ"ר` is 100, 50, 200: the 200
    follows a 50, so it is not a numeral at all. Same day they also fixed klal 176
    w691 `חי"ר` -> `חי"ד`.

    **Swept the class properly.** A numeral here carries gershayim immediately
    before its final letter (`קנ"ד`), which is what separates it from `ר'` = רבי -
    a first sweep without that constraint drowned in `דר'`/`לר'`. With it:
    **54 gershayim-forms corpus-wide end in ר where a ד is valid and the ר is
    not** - 14 in Part 1, of which **2 were unflagged and are now flagged**:
    klal 77 w91 `ע"ר` and klal 91 w546 `מ"ר`.

    **The corpus's own usage is the strongest evidence**, better than the
    reference corpus for abbreviations: Part 1 writes `ע"א` 63x, `ע"ב` 61x,
    `ע"ד` 37x against `ע"ר` 5x; `י"ד` 36x against `י"ר` 2x; `מ"ד` 9x against
    `מ"ר` 1x; `כ"ד` 11x against `כ"ר` 2x. Every ר-final form is a rare outlier
    beside a common ד-final twin. That holds whether the form is a numeral or an
    abbreviation, which is why the rule is worth more than its arithmetic alone.

    **Generalising it further does NOT work, measured.** Extending to "any
    gershayim form that is an invalid numeral" returns 205 Part-1 hits, 186 of
    them unflagged and overwhelmingly standard abbreviations - `עכ"ל`
    (עד כאן לשונו, 16x), `י"ל`, `כ"ש`, `ס"ל`, `ל"ת`, `פ"ק`, `ר"ן`. Abbreviations
    do not obey numeral ordering, so the arithmetic test is meaningless for them.
    Second over-broad rule of the day after item 31's prefix filter; per Lesson 31
    it is not being tried a third time. **The narrow trailing-ר rule stands; the
    general one is abandoned.**

34. **REPORTS ARE NOW SHAREABLE, 2026-08-26 (reviewer: "the json is not a good
    way to share the urls - it is not clickable with markdown").** Correct - the
    JSON is what the pipeline reads and diffs, but as a way of HANDING findings to
    a person its links are inert text. `tools/render_report.py` renders any of
    these reports to Markdown (default, clickable almost anywhere a finding gets
    pasted) or HTML (clickable in the browser the dashboard is already open in,
    where the links are same-origin and simply work).

    It reads every report shape in the repo without any of them being rewritten:
    position-per-row (`lexical_defect_report.json`), word-per-row with an
    `occurrences` list (`lexicon_yad_malachi_only.json`), and dict-of-sections
    (`ligature_words.json`, via `--section`). One trap worth recording: **`word`
    means a word INDEX in `cleared_flags_*.json` and the word TEXT in
    `lexicon_yad_malachi_only.json`**, so the key is resolved by TYPE rather than
    by name - guessing by name silently dropped the word index from every link in
    the first run, producing links that opened the right klal at the wrong place.

    **The URL SHAPE had to change too** (reviewer: "sadly those links you shared
    here in the chat are not clickable"). `/#klal=66&word=135` is what the
    frontend routes on, but it does not survive being pasted: a terminal will not
    hyperlink Markdown link syntax at all, and several that DO linkify a bare URL
    stop at the `&` - which opens the right klal at the WRONG word, worse than a
    link that plainly fails. `review_server.py` now also serves
    **`/klal/66/word/135`** (`ROUTE_SHARE`), a 302 to the hash form, with no `#`
    and no `&` to trip anything. That is what `render_report.py` emits and what
    should be pasted anywhere outside the browser; the hash form remains what the
    app routes on internally and what the panel's copy button yields.

    The rendered `.md`/`.html` are gitignored: they regenerate in a second, and
    they point at `127.0.0.1:8420`, so they work only on a machine running the
    dashboard. Right for a review tool, wrong for anything outward-facing.

    **EVERY WORD NOW CARRIES ITS ADDRESS ON HOVER** (reviewer: "hovering over any
    word should always surface a floating box with the klal + word and an icon to
    copy the link"). Every word in the text pane is addressable, so every word now
    says what its address IS without being clicked - **plain words previously said
    nothing at all**, and flagged ones only spoke through a native `title`
    tooltip, which cannot hold a button.

    It is a HOVERABLE card, not a tooltip, and the distinction is the whole point:
    `#tooltip` sets `pointer-events: none` precisely so it can never swallow a
    click, which makes it the wrong element for something containing a control.
    `#word-card` stays open while the pointer is on it, with a grace period so the
    pointer can cross the gap from the word - asserted in the tests by actually
    moving onto the card before clicking, because a control you cannot reach is
    the failure mode that matters here. It also TAKES OVER the word's native
    `title` (a flagged word's reasoning) and clears the attribute, since two
    floating boxes over one word is worse than none.

    The card's copy button and the panel's yield the same payload, now in the
    paste-safe path form.

    **Presentation, 2026-08-26 (reviewer):** the decision panel's context header
    is larger (11px -> 14px) and no longer styled as a caption - it is the line
    that says WHERE you are and it now carries the copy control. The hover card
    was made lighter and more transparent (`rgba(26,32,44,0.72)`, text at 0.82),
    with a **backdrop blur**, which is what keeps it legible at that alpha: this
    box follows the pointer across text the reviewer is reading, so it should sit
    over the page rather than block it, and without the blur the Hebrew showing
    through is unreadable.

    **The klal's gematria is now part of the reference everywhere** - "Klal 66
    (סו) · Word #135" in the panel header, the hover card and the copied payload.
    `api_klal` had always carried `gematria`; **`/api/klalim` did not**, so
    anything working from `klalById` (the hover card, the nav) had no way to name
    a klal the way the BOOK does. One field added server-side rather than a
    per-call fetch. The reviewer navigates by id and reads the scan by marker;
    the reference should carry both.

    **ONE box, not two, on a disputed word** (reviewer: "we don't need both boxes
    when it is a disputed word, just the big one with the details"). A flagged
    word in the text pane was showing `#tooltip` AND the hover card at once. They
    are merged into the card, because the card is the only one that CAN hold the
    copy control - `#tooltip` is `pointer-events: none` by design so it never
    swallows a click on the scan pane, where it is still used unchanged. The
    detail block was extracted into a shared `wordDetailHtml()` so the two
    surfaces cannot drift, and the card renders it in full: status, the original
    OCR reading, confidence, reasoning and any recorded decision. Nothing was lost
    by suppressing the tooltip in the text pane, which is what made the merge the
    right move rather than just deleting one box.

    **Clicking a word now ZOOMS the scan onto it** (reviewer request). Centring
    already worked; the zoom did not, and at 100% the page is too small to
    adjudicate the thing the queue is full of - a ס/פ, a ד/ר, a dropped ligature
    letter. A click raises the scan to **220%** and centres the focused box.

    Two properties, and the second is the one that would have annoyed daily: it
    zooms IN only, **never out** - a reviewer who has gone to 300% to read a worn
    sort is not yanked back by their next click. It is also a one-shot flag set in
    `focusWordOnScan()` (the single funnel every word click already passes
    through, from the manualPageLock fix), so scrolling or paging afterwards
    leaves the zoom alone.

    Measured: a word away from the page edges centres to **dx 0, dy 0**. A word
    at an edge cannot be centred because the scroll clamps - the test asserts
    "centred on each axis unless that axis is clamped", since asserting a fixed
    tolerance would only have been asserting the viewport width. Note the scan
    pane is RTL, so `scrollLeft` runs 0 -> negative and any clamp check needs
    `abs()`; the first version of the check missed that.

    **Clicking away undoes it** (reviewer). The zoom is the other half of the
    gesture and has to reverse with the highlight, or the reviewer is left at 220%
    on a page they have stopped inspecting. It restores the zoom from BEFORE the
    focus rather than forcing 100%: the normal flow starts at 100% and so returns
    there, which is what was asked, while a reviewer who had gone to 200% by hand
    to study the page keeps it. Touching the zoom controls or the wheel while
    focused hands ownership back - there is then nothing stored to restore.
    Verified both paths: 100% -> 220% -> 100% with the klal outline back, and a
    manual 200% surviving a full focus/dismiss cycle.

35. **[AUDIT 2026-08-27] Heavy code review & Stage 5b / AI flag diagnostic audit.**
    Comprehensive review of the full pipeline + 28 commits (Aug 25-27) documented in
    `CODE-REVIEW-2026-08-27.md` and `LEXICAL-DEFECT-AND-FLAG-AUDIT-2026-08-27.md`.
    
    - **Confirmed Fixes from Prior Reviews**: Memoized JSONL decision loading & region caching
      (182ms -> 9.6ms latency), multi-page bbox collisions, raw token array index alignment in
      `reconstruct_placeholder_klalim.py`, scan watermark & folio geometry cleaner ($y \le 0.02$),
      abbreviation ligature guard in `docai_filter.py`, null decision POST prevention at write site.
    - **Critical Defects & Edge Cases Identified (Ready for Future Triage)**:
      1. `export_corpus.py:_apply_decisions_to_klalim()` drops manual insertions (`original_word is None`)
         which `apply_reviewer_decisions.py:320` handles via `apply_delete_insertion()`.
      2. Multi-word manual replacements (`len(chosen_text.split()) > 1`) change word count without
         setting `word_count_changed_klalim`, allowing subsequent same-run decisions in the same klal
         to apply at shifted word indices.
      3. `corpus_io.py:597` `trusted_klal_pages_with_continuations()` crashes with `AttributeError`
         if `klal_page_regions.json` is absent (`load_json` defaults to `None`).
      4. `review_server.py:453` `_corpus_bbox_cache` module-level dict is never invalidated on corpus edits.
    - **Stage 5b Lexical Defect Report Audit (`lexical_defect_report.json`)**:
      299 candidates across 96 Part-1 klalim (194 unflagged, 97 currently flagged, 8 already decided).
      True-positive examples identified against surrounding context ([klal 179 word 16](http://127.0.0.1:8420/#klal=179&word=16) `יותה`->`יותר`,
      [klal 30 word 250](http://127.0.0.1:8420/#klal=30&word=250)/[1263](http://127.0.0.1:8420/#klal=30&word=1263) `גכי`->`גבי`, [klal 54 word 730](http://127.0.0.1:8420/#klal=54&word=730) `עלירם`->`עליהם`, [klal 7 word 252](http://127.0.0.1:8420/#klal=7&word=252) `הלכרה`->`הלכה`,
      [klal 30 word 1115](http://127.0.0.1:8420/#klal=30&word=1115) `טיניה`->`מיניה`); false positives isolated (names like `זלמן`, terms like `בשרש`).
    - **Active AI Flag Alignment Audit**:
      455 active flags (144 klal-level, 311 word-level). For the 202 Round 4 flags: 187 (92.6%) are
      cleanly aligned at their exact stored word index; 12 are already resolved in stored text;
      only 1 experienced index drift ([klal 43 word 14](http://127.0.0.1:8420/#klal=43&word=14) -> [word 17](http://127.0.0.1:8420/#klal=43&word=17) `ממטונא`->`מממונא`); 1 is retracted ([klal 177 word 340](http://127.0.0.1:8420/#klal=177&word=340) `למיפך`).

36. **THE 2026-08-27 AUDIT'S FOUR "CRITICAL DEFECTS" WERE VERIFIED AND ALL FOUR
    FIXED — three were LATENT, not live, and saying which is the point.** Item 35
    listed them; none had been reproduced. Each was run before being touched.

    | audit finding | verified? | live exposure |
    |---|---|---|
    | `export_corpus` drops manual insertions | **yes** | **0 today** - both existing inserts are already APPLIED, and applied decisions are skipped because part1.json already carries their text |
    | multi-word manual replacement shifts indices | **yes** | **0 today** - no manual decision has multi-word text |
    | `corpus_io` crashes if the regions file is absent | **yes**, `AttributeError` reproduced | 0 - the file is tracked; this is a deleted-file case |
    | `_corpus_bbox_cache` never invalidated | **yes** | **LIVE** - the only one |

    **The cache was the real one.** It was keyed `(klal_id, page)` and never
    cleared, but the alignment it stores is computed FROM the klal's words - so
    applying a decision and rebuilding *while the server ran* left every later
    request drawing boxes from text that no longer existed. That is the exact
    sequence a reviewer performs, and it contradicts this section's own "fresh off
    disk every call" contract. Now keyed on a stamp over part1/2/3.json's
    (mtime, size), the same pattern as the `_read_all` and `_load_regions` memos.

    The export gap is worth stating precisely because "drops manual insertions"
    overstates it: the export re-derives from the CURRENT part1.json and skips
    already-applied decisions, so the gap opens only in the window between
    recording an insert and applying it - which is, admittedly, exactly when an
    export is most likely to be taken. `apply_reviewer_decisions` has three manual
    cases (insert / delete / replace) and the export had two; it now has three,
    proved by an unapplied insert reaching the export in a temp-ledger harness.

    The multi-word guard had to be scoped to the REPLACE path: written broadly it
    consumed the word-count slot that the insert branch's own gate then tripped
    over, and `test_manual_correction_with_no_original_word_inserts_new_text`
    caught it immediately. `corpus_bbox_cache_key()` is now exported so the test
    that pre-seeds that cache builds the key the way the module does.

39. **[2026-08-31] THE `title` FIELD IS UNREVIEWED TERRITORY — it carries its
    own uncorrected OCR, and no detector in this repo has ever looked at it.**
    Found because the reviewer read one: "klal 39 the title ends with harav, the
    amrinan is the beginning of the text." Both halves of that are right, and they
    are two DIFFERENT defects.

    **(a) The extent defect the reviewer reported.** Klal 39's title is
    `אין הלכה כתלמיד במקום הרב אמרינן אף כשהתלמידים הם רבים נגד רכם` — it should
    stop at `הרב`, and `אמרינן ...` is body text that has been pulled into the
    heading. NOT SWEEPABLE MECHANICALLY, and I checked before claiming so: title
    length is not the signal, because this book's headings genuinely are long
    sentences (mean 6.2 words, p90 = 11, and klal 92's legitimate title runs 24).
    Deciding where a heading ends needs the printed page, where it is set in
    larger type. So the extent of (a) is UNKNOWN and is not being guessed at.

    **(b) A sweepable defect found while checking (a), extent exact.** A title
    should be a prefix of its own `clean_text` after the marker. **14 of 222 are
    not.** Eight are benign alignment offsets (the title starts at a different
    word than body[1], e.g. klalim 101-105 whose body opens `ב"ד` where the title
    opens `מתנין`). **Six are real OCR errors sitting in the title where the BODY
    IS ALREADY CORRECT:**

    | klal | title has | body has | class |
    |---|---|---|---|
    | 39 | `רכם` | `רבם` | ב/כ, the commonest confusion in this print |
    | 69 | `אהים` | `אלהים` | **dropped lamed — the alef-lamed ligature again** |
    | 91 | `איכא` | `אליבא` | dropped lamed |
    | 88 | `וכאבל` | `ובאבל` | ב/כ |
    | 87 | `משנה` | `ממשנה` | dropped letter |
    | 36 | `הש"ס'` | `השית'` | — |

    **WHY NOTHING CAUGHT THESE:** every detector, validator and witness in this
    repo reads `clean_text`. `detect_real_word_substitution`, the lexical defect
    report, the consensus pipeline, the corpus invariants, the vision
    adjudicator — all of them. The `title` field has never been read by any of
    them, so it has had no OCR pass at all, and klal 69's is the **same ligature
    sort** that produced items 26 and 32. Lesson 1 in a place nobody had looked:
    a check that was never run over this field has verified nothing about it.

    **THE PIPELINE NEEDS A TITLE PASS — this is the standing requirement, and it
    is not built.** `title` lives in `part1.json`, so it is corpus text under the
    single-source-of-truth rule, but `apply_reviewer_decisions.py` only ever
    writes `clean_text`: **there is no mechanism in this pipeline for promoting a
    title correction, and no detector, witness or invariant reads the field.**
    What a title pass owes, at minimum: (i) the detectors run over `title` as well
    as `clean_text`; (ii) an apply path so a ruling on a title can be recorded and
    promoted like any other, instead of being hand-applied; (iii) a gated
    invariant that a title is a prefix of its own body, with the legitimate
    offsets baselined; (iv) a decision on the EXTENT question, which needs the
    scan because only the printed type size says where a heading stops.

    **5 TITLES HAND-EDITED 2026-08-31, user-authorised** ("for now we will
    hand-edit part1.json. do it carefully and show me the diffs") — a deliberate,
    recorded exception to the single-source-of-truth rule, taken because no apply
    path exists to take instead. Diffs shown and approved before writing:

    | klal | class | was | now |
    |---|---|---|---|
    | 39 | EXTENT | `...במקום הרב אמרינן אף כשהתלמידים הם רבים נגד רכם` | `אין הלכה כתלמיד במקום הרב` |
    | 69 | spelling | `אהים` | `אלהים` |
    | 87 | spelling | `משנה` | `ממשנה` |
    | 88 | spelling | `וכאבל` | `ובאבל` |
    | 91 | spelling | `איכא` | `אליבא` |
    | 36 | EXTENT | `אלא אין דרך הש"ס' סדרי לומר היכא שלא הוזכר שום אמורא ברישא` | `אלא` |

    Klal 39's truncation removes the `רכם` misread along with the absorbed body
    text, so it needed no separate spelling fix. Verified after: the title-order
    validator flags none of the five, and Part 1's first-letter regression count
    is **118 before and 118 after** — the edits introduced no ordering change.
    `./rebuild_all.sh --skip-vision` re-run; 318 gated tests pass.

    **KLAL 36 RESOLVED 2026-08-31 BY THE REVIEWER, and it was an EXTENT case, not
    a spelling one.** I had left it open because title `הש"ס'` and body
    `השית' סדרי` spell the same thing (`ש"ס` abbreviates `שישה סדרים`; `שיתא סדרי`
    is its Aramaic), so I could not tell which the printer set. The reviewer's
    answer dissolved the question: **the heading is just `אלא`** — the term the
    klal is about — and everything after it was absorbed body text, where
    `השית' סדרי` is correct as it stands. Title set to `אלא`; the divergence
    disappeared with the absorbed words. Worth recording as a reasoning error:
    I had classified it by the DIFFERENCE I could see (one word) instead of asking
    whether the whole span belonged, and the two classes need to be tested in the
    other order — extent first, then spelling within what remains.

    **THE EXTENT CLASS REMAINS UNSWEPT.** One klal was corrected because the
    reviewer identified it. How many others have absorbed body text is unknown and
    is not being estimated — per item 0's standing rule this is recorded as
    unmeasured rather than left to read as handled.

    **The alphabetical-order validator is the one thing that does read titles**
    (`tools/validate_title_alphabetical_order.py`) — it checks ORDERING, not
    spelling, and a ב/כ misread mid-title cannot fail it.

56. **[FIXED 2026-08-31] Item 35's defect, one layer below where it was fixed:
    the ASSEMBLER re-served a word an applied decision had settled.** Caught by
    `test_no_candidate_re_raises_a_word_an_applied_decision_already_settled` on
    **klal 84 w0** — the reviewer confirmed the klal marker `פד` against DocAI's
    `פר`, it was applied, and the very next rebuild put the same question back in
    front of them.

    `build_corrections_dataset.py` has dropped settled positions since item 35 and
    did so correctly here — `corrections_candidates_part1.json` carried no entry
    at klal 84 w0. But **`corrections_verified_part1.json` is CUMULATIVE**: it
    keeps every entry the vision stage has ever verified, including ones generated
    before the decision existed, and `assemble_corrections_dataset.py` merged it
    back in. The generator had been taught the rule and the assembler had not.
    Fixed by importing `settled_by_an_applied_decision` rather than restating it —
    the two stages must agree on what "already ruled" means or a suppressed
    candidate simply reappears downstream. The drop is now reported per rebuild
    ("1 verified entry dropped…") instead of happening silently.

    Worth recording about the diagnosis: I first concluded the entry came from the
    consensus or lexical merge, because I checked `corrections_verified_part1.json`
    with `d.get("84")` — and that file is a flat LIST, not a dict keyed by klal.
    The lookup returned nothing and I read that as "not from here". Checking the
    SHAPE before trusting a lookup would have gone straight to it; a query that
    silently returns nothing looks exactly like an absence.

57. **[2026-08-31] `ע״ד` -> `ע"ד` applied; ONE U+05F4 gershayim left in Part 1.**
    The reviewer's own correction of their own keystroke had been recorded at
    16:26 and was still UNAPPLIED — it only became appliable once the final
    rebuild regenerated its candidate, which is why the earlier apply loop
    reported zero pending and this did not surface until asked about directly.
    Applied with two other stragglers (klal 169 w1074 `שרוא` -> `שהוא`, and a
    confirmed-no-op on klal 84 w0 — the one that exposed item 56).
    **The remaining one is klal 2 w316 `נ״ד`** in `אשכחן בפ"ד מיתות נ״ד ב'
    דענשינן` — Sanhedrin 54b, content right, gershayim wrong. It predates today
    (recorded 2026-08-30) and is again the ONLY such character in Part 1, against
    6,405 ASCII quotes. Not corrected: it is corpus text and wants the reviewer's
    ruling like any other.

55. **[2026-08-31] Post-apply state, and two things the apply itself surfaced.**
    The rebuild/apply loop was run to convergence — 48 + 1 + 3 + 3 decisions over
    four rounds, since the script deliberately applies only one word-count-changing
    decision per klal per run. **0 decisions pending at the end.**

    **PART 1 NOW HAS ZERO FOREIGN CHARACTERS** — `validate_part1_corpus_integrity`
    check 2b reports 0, from **7** at the start of the day. The last `&` (klal 77
    w11) is `אל`, and `ligature_words.json` now reports **`both_lost: 0`**, closing
    the last of item 32's three. **Item 27's page-seam furniture is fully removed
    too**: klal 39's catchword `דבכולהן` is gone, and klal 210 reads
    `אפשר דהלכה כקמייתא` — matching the printed page — after its three spurious
    tokens (`דהלכה`, `:`, the folio `לא`) came out one per round.

    **A title diverged from its own body the moment the body was corrected, which
    is item 39's gap arriving on schedule.** Applying klal 77 w7 `לא` -> `אלא` left
    the `title` field still reading `לא`: nothing propagates a body correction into
    the title, because titles have no apply path. Fixed by hand (authorised, same
    as the rest of today's title work) and Part 1 is back to **222/222 clean
    prefixes, 0 divergences**. This is the concrete argument for the title pass:
    every future body correction inside a heading will do this again, silently,
    and only `compare_titles_to_text.py` would notice.

    **A UI test SKIPPED ITSELF because the corpus got better** —
    `tests/test_review_server.py:1079`, with the message "no bare `&` left in
    Part 1 - seed one through the API instead of skipping". That is item 0F /
    Lesson 36 exactly, caught in the act: a test pinned to a defect stops testing
    when the defect is repaired, and a skip is quieter than a failure. The test
    knows what it needs (seed the condition through the API rather than borrow it
    from the shipped corpus); doing that is part of the synthetic-fixture work item
    0F describes, and it is now the second concrete case waiting on it.

54. **[2026-08-31] 48 reviewer decisions applied — and I had to repair an
    index drift I caused myself first. The repair closed a real gap in the
    reindexer.**

    **WHAT WENT WRONG.** Item 48's `[.]` insertions shifted every later index in
    17 klalim. I called `reindex_flags_after_shift()` and **not**
    `reindex_pending_decisions_after_shift()`, which already existed — so open
    flags moved and PENDING DECISIONS did not. Lesson 35 names both in one
    sentence and I acted on half of it. Measured before applying anything: **4
    pending decisions had drifted by exactly +1** (klal 39 w617 and w251, klal 36
    w73, klal 106 w16), each naming a word that sat at index+1.
    A stale decision is worse than a stale flag, as that function's own docstring
    says: a flag points at the wrong word and a human notices, while a decision is
    refused by the drift guard on every future run and is stranded exactly the way
    item 0A stranded 43 rulings.

    **THE GAP THE REPAIR EXPOSED: `reindex_pending_decisions_after_shift()` did
    not cover `disputed_choice`** — only `candidate_choice` and
    `manual_correction`. That is the type that needs it most: a decided dispute is
    dropped from the candidate queue, so it is drift-checked against `part1.json`
    itself, which is precisely the check a shifted index fails. **3 of my 4
    drifted decisions were `disputed_choice`.** Added to the tuple.
    My repair pass was scoped too broadly on the first attempt — it ran over every
    klal whose heading is followed by `[.]`, 92 of them, not the 17 that actually
    shifted. **The verified-move rule refused every one of the extras**: a
    decision moves only when the word it named is provably at the shifted index,
    and in an unshifted klal it is not. 9 moves written, all in klalim 36/39/106,
    all re-verified afterwards against the corpus. The guard did its job on an
    operator error, which is the argument for having written it that way.

    **APPLIED: 48 decisions** (16 replace, 15 manual, 17 confirmed-no-op) — up
    from 44 before the repair, the difference being the 4 recovered. 2 refused and
    40 drift-skipped, both pre-existing and both correctly left alone.
    **The applied diff was read word by word before being accepted**, which is how
    item 0B's corpus damage was caught and is not a step to skip. All six
    deletions verified against the index they name: three commas the reviewer
    ruled on (klalim 31, 36, 146), a doubled geresh (klal 69 w11), and **two of
    item 27's page-seam duplicates finally removed — klal 39's catchword
    `דבכולהן` and klal 210's `דהלכה`**.

    **Two things worth the reviewer's eye, neither a defect:**
    - **klal 74 w966 `בארוכה` -> `בארוכ'`.** Item 51's filter had just protected
      the stored `בארוכה` by rejecting DocAI's `בארוכ` as orthographically
      impossible. Both are right and they do not conflict: a bare `בארוכ` cannot
      exist, the page prints the ABBREVIATION `בארוכ'`, and DocAI dropped the
      geresh. The filter rejected the impossible string; the reviewer supplied the
      real one.
    - **klal 77 w91 came in as `ע״ד` with a U+05F4 gershayim**, not the ASCII `"`
      the corpus uses everywhere else. Part 1 now holds **2** such characters
      (klal 2 w316 and this) against **6,405** ASCII quotes. Not corrected here —
      it is the reviewer's own keystroke and corpus text — but it is the same
      single-instance anomaly flagged on klal 2 w316 in the 2026-08-30 open items.

51. **[FIXED 2026-08-31] An orthographically impossible reading no longer
    reaches a reviewer.** The reviewer's rule, on klal 36 w61: a word-final `כ`
    must be `ך`, so `כתכ` cannot be a Hebrew word and no vision call should have
    been spent on it. `corpus_io.impossible_final_form()` encodes it and
    `assemble_corrections_dataset.classify()` consults it BEFORE any vision
    verdict: such a candidate is `current_text_confirmed`, i.e. machine-resolved,
    not a dispute to put in front of a human.

    **The abbreviation exemption is the load-bearing half**, and it is the same
    one item 33's trailing-`ר` rule needed: an abbreviation does not obey
    final-form orthography, because the letter is an INITIAL, not a word ending.
    `ה"נ` (הכי נמי) is a perfectly good form and is a false positive of the naive
    rule. Measured: 7 candidates carried such a reading, **6 after the exemption**.
    Verified after the rebuild: klal 74 w966 (`בארוכ` vs the correct `בארוכה`),
    klal 36 w61 and klal 182 w0 all now read `current_text_confirmed` — w966 had
    been **OPEN**, asking a reviewer to weigh a string that cannot exist.
    Gated by `test_a_reading_ending_in_a_non_final_letter_form_is_impossible`,
    which is purely synthetic and asserts the exemption as well as the rule.

52. **[2026-08-31, reviewer] The scan pane now scrolls to the klal it is showing,
    and a word click goes to that word's own page.** Reported as "klal 4 doesn't
    move the scan to the correct klal". The region outline was drawn correctly all
    along — the problem is that **klal 4 holds 40 of its 497 tokens (8%) on its
    start page**, in the bottom tenth of it, so a reviewer looking at the top of
    page 15 sees klal 3 and concludes nothing moved. **A class, not one klal: 30
    of 222 klalim start on a page holding under half their text** — klal 92 at 6%,
    klal 30 at 7%, klal 159 at 16%, klal 169 at 17%.
    Fixed with `scrollIntoView({block: 'nearest'})` on the region box, which is
    the reviewer's own rule ("bottom of the page for the first half, top for the
    second") without special-casing either: it scrolls the minimum that brings the
    region into view, landing at the bottom for a start-page sliver and the top for
    a continuation, and is a no-op when the page already fits. Verified in a short
    viewport where the page cannot fit: klal 4 scrolls to 168px with the region in
    view, and clicking word 201 takes the scan to page 16, its own page
    (`pageForWord` already resolved this correctly — confirmed rather than assumed).

53. **[2026-08-31, reviewer: klal 35 w30 "takes me to a completely wrong word"]
    THE FIX IS TO RETRACT THE CANDIDATE — the word is not missing, and the
    aligner is why it looked missing.** `שמות` **is already in klal 35, at word
    45**, in `בספר שמות בארץ בכפות תמרים`. Its stored copy has **no alignment
    box at all**, so DocAI's token for it matched nothing and was reported as an
    omission — at word 30, 15 words before the real one. Both independent
    witnesses read `משמע` at word 30, contradicting the omission outright. The
    scan pane was faithfully drawing the candidate's own bbox; the candidate is
    what is wrong.

    **Two sweeps, because the first metric missed the reported case and saying so
    matters.** A vertical-distance check (is the candidate on a different printed
    line from its neighbours?) found 5 but NOT klal 35 w30, which sits on the
    same line 0.72 of the page width away — the opposite end of an RTL line. A
    reading-order coordinate (line band, then right-to-left within it) catches it:
    **5 omission candidates whose bbox is out of reading order for their word
    index** — klal 17 w308, klal 85 w96, klal 2 w632 (all the NEXT klal's marker,
    a boundary artifact), klal 50 w2, and klal 35 w30.

    **The wider and more useful sweep: 13 of Part 1's 40 omission candidates
    propose a word that ALREADY appears in the same klal.** Eight of those sit at
    the candidate's own scan position (klalim 50, 68, 128, 167×2, 169, 189, 194) —
    unambiguous alignment failures. The rest are further off and need reading:
    klal 35 w30 (15 words away, and the copy is unaligned), klal 175 w173, klal 2
    w632, klal 193 w244, klal 159 w1036.

    **NOT auto-suppressed.** A word can legitimately repeat in a klal, and this
    book restates maxims verbatim as a matter of style — the corpus-integrity
    validator has a whole check devoted to that. So "already present" is a strong
    triage signal, not a proof, and turning it into a filter would be the
    over-suppression this file has recorded twice (items 26 and 31). Recorded with
    its extent for the reviewer to rule on.

50. **[2026-08-31, reviewer] Three nav badges, and editorial marks are
    addressable at last. Plus four findings from the same report, three of which
    need the reviewer's call and are NOT fixed.**

    **FIXED — the third badge.** `machine_resolved_count` was served per klal and
    summed only into the legend total, so klal 73 showed one badge while
    highlighting two words (item 49). The nav row now reads open (red) ->
    machine-resolved (amber) -> human-decided (green), in decreasing order of
    claim on the reviewer's attention, with the amber matching the colour the
    word itself renders in.

    **FIXED — `[.]` was the one token in the text that could not be clicked**
    (reviewer: "36 w14 won't let me click on it - shows ?"). The editorial-mark
    branch of `renderKlalBody` returned early before the span ever got a
    `data-word-index`, so the mark could not be addressed, hovered for its
    reference, deep-linked or clicked - while still CONSUMING a word index, which
    is what made the reference read wrong. It now carries its index and takes the
    same click as a plain word, because a reviewer must be able to remove or
    change a mark this pipeline itself inserted. **This mattered more today than
    yesterday: item 48 inserted 17 more of them.**

    **NOT FIXED, needs a decision — a nav jump shows the klal's START page, and
    for 30 of 222 klalim that page holds a MINORITY of the text.** Reported as
    "klal 4 doesn't move the scan to the correct klal". Measured: klal 4 starts on
    page 15 with **40 of its 497 tokens (8%)** and continues on page 16 with 457;
    the region outline IS drawn, correctly, on the bottom 10% of page 15. So the
    behaviour is right by its own rule and useless in practice. Worst cases:
    klal 92 (36/584 = 6%), klal 30 (133/2021 = 7%), klal 4 (8%), klal 31 (14%),
    klal 159 (16%), klal 169 (17%). Options are to jump to the page holding the
    most of the klal, or to keep the start page (where the marker is) - a
    presentation decision, and after two wrong inferences today I am not making
    it unilaterally.

    **NOT FIXED, a cheap filter worth having — 7 candidates propose a reading
    ending in a NON-FINAL letter form, which Hebrew orthography forbids.** Raised
    by the reviewer on klal 36 w61: "why was ctc considered? cof is impossible
    here, would be cof sofit." Exactly right - a word-final `כ` must be `ך`. The
    class, swept: `כתכ` (36 w61), `בארוכ` (74 w966), `חרא רבפ` (176 w277), `קפכ`
    (182 w0, a klal MARKER), `נחמ` (198 w597, an insertion candidate), `וכפ`
    (217 w548), and `ה"נ` (212 w30).
    **The rule needs the same exception item 33's trailing-`ר` rule needed:
    abbreviations do not obey final-form orthography** - `ה"נ` (הכי נמי) is a
    perfectly good abbreviation and is a FALSE POSITIVE of the naive rule, as is
    anything carrying a geresh or gershayim. Excluding those leaves ~4 genuine
    impossibilities. **The one that matters: klal 74 w966 is still OPEN**
    (`current_text_may_be_wrong`), asking the reviewer to weigh `בארוכ` against
    the correct `בארוכה`. A candidate that cannot be a Hebrew word should never
    reach the queue, and this is a five-line test on `docai_reading`.

    **NOT FIXED, a data issue — klal 35 w30's omission candidate is
    mis-positioned** (reviewer: "takes me to a completely wrong word in the
    scan"). The entry is `opcode: delete` / `possible_omission`, proposing DocAI's
    `שמות` as missing at word 30; its bbox points at a genuine `שמות` on page 26,
    but at the end of an unrelated line (`שיתא סדרי לא סבירא ליה כוותיה · שמות`),
    while corpus word 30 is `משמע` in `לישנא יתירא אמר לך וכו' משמע דההוא אמורא`.
    Rendered the crop at 4x and read it rather than inferring. **Both independent
    witnesses read `משמע` there** (`vlm_reading` and `surya_reading` both
    `משמע`), which contradicts the omission outright - so this looks like a false
    positive whose box happens to land on a real word elsewhere. The scan pane is
    faithfully showing the candidate's own bbox; the candidate is what is wrong.

    **EXPLAINED, not a defect — klal 105 w4 does not zoom** (reviewer: "didn't
    zoom in on the scan panel"). That flag sits on a `,`, a token with no Hebrew
    letter, so the corpus-to-DocAI aligner has nothing to match it on and returns
    no bbox; the focus-zoom has nothing to zoom to. It is one of the 8 entries in
    `UNLOCATABLE_FLAGGED_WORD_BASELINE` for exactly this reason. Matching
    non-Hebrew tokens on their raw text was tried 2026-08-30 and reverted - it
    works and costs too much, moving 41 correct boxes and losing 2. The honest
    position is that punctuation-only flags are not locatable today.

48. **[2026-08-31, reviewer] Five more titles, and the editorial separator `[.]`
    inserted into 17 klalim — with the flag reindexing the insert made necessary.**
    Titles: 97/98/99 -> `ברייתא.` (first word only, the same cluster shape as
    131-133's `דיעבד`), 103/104 -> `ב"ד מתנין לעקור דבר מן התורה.`

    **The bare-separator count went 16 -> 21 because those title edits moved the
    boundary**, which is worth stating: shortening a heading exposes a gap that
    was previously inside it. Recomputed rather than reusing the earlier list.

    **17 got `[.]`, and 4 did NOT.** Klalim 180, 182, 190 and 217 have a period
    already — glued to the following token with no space (`.ודע`,
    `.דאמרי'בפ'`, `.לא`, `.דאמרינן`). That is a TOKENISATION defect, not a
    missing mark, and inserting `[.]` would have doubled the punctuation. Left
    alone and recorded here; the fix there is to split the token, which is a
    different operation and wants its own pass.

    **`[.]` and not `.`, deliberately.** The printed page has no mark at these
    positions — verified by rendering klalim 36 and 106 and reading the lines, not
    inferred. `[.]` is this repo's existing marker for punctuation added by review
    rather than set by the printer (`review_server.py:1603`, checked by
    `audit_applied_decisions.py`), so a bare `.` would assert something about the
    page that is false.

    **EVERY INSERT SHIFTED EVERY LATER INDEX IN ITS KLAL** — Lesson 35 / item 0C,
    the defect that once walked a flag onto the wrong word. The script reused
    `apply_reviewer_decisions.reindex_flags_after_shift()` rather than restating
    the rule, so a flag moved only where the word it named before is the word at
    the shifted index. **26 open flags reindexed, 0 unverified.** Each insertion
    also appended a `punctuation_choice` row to the ledger, so the change is
    traceable in the append-only log rather than appearing as an unexplained diff.

    **The full `./rebuild_all.sh` WITH vision had to run**, not `--skip-vision`:
    the shifts left 3 vision-adjudicated candidates (klal 36 w9/w60, klal 159
    w415) pointing at different words, and `test_no_stale_candidate_flags_are_
    being_served` caught exactly that and said so. 319 gated tests pass after.

49. **[2026-08-31, reviewer: "klal 73 two disputes but the red flag shows only 1"]
    NOT A COUNTING BUG — but it exposes a field that is served per-klal and
    rendered nowhere.** Verified by reading both entries and the rendered DOM.

    Klal 73 has two highlighted words and they are in different states:
    - **w27 `יוחנן`** — DocAI read `יוהנן` (ה for ח); the vision check selected the
      stored text at **0.98** and transcribed `יוחנן`; context is `משום דר' יוחנן
      תנא הוא`, and Rabbi Yochanan is right. Flag `current_text_confirmed`, so it
      renders `state-machine`. **Nothing for a reviewer to decide.**
    - **w87 `עלי`** — Surya and the VLM both read `על`; flag
      `current_text_may_be_wrong`; renders `state-open`. **This one needs a
      ruling.**

    The red badge counts `machine_disputed_count`, which is 1, and that is
    deliberate: item 17 changed it in 2026-08-25 precisely because counting
    total-flagged made a klal look like outstanding work when the machine had
    already settled most of it. So the badge is right, and "two disputes" is also
    right — they are two disputes, one of them resolved.

    **THE REAL GAP: `machine_resolved_count` is served per klal and only ever
    summed into the LEGEND total** (`app.js:680`); no nav row shows its own. So a
    klal with one resolved and one open word shows a single badge and looks like
    it has one highlighted word, when it has two. That is Lesson 29's shape in
    miniature — a field computed, served, and never rendered where it would
    answer the question a reviewer is actually asking. **Not fixed**: adding a
    third badge changes every one of the 222 rows and is a presentation decision
    for the reviewer, not an engineering default.

47. **[2026-08-31, reviewer chose option (a)] The heading/text separator: almost
    nothing was normalisable, and the one case that was is a MISREAD, not a
    missing period.** Asked to make each klal read heading-then-one-period-then
    text, I surveyed what actually sits after the heading run in all 222:

    | separator after the heading | count |
    |---|---|
    | `[.]` | 92 |
    | `.` | 61 |
    | `•` | 46 |
    | no mark at all | 16 |
    | `-` | 4 |
    | `:` | 2 |
    | `,` | 1 |

    The reviewer chose **(a): normalise only the bare and comma cases, leave
    `[.]`, `•` and `:` as the faithful record.** Two reasons that was the right
    call, both established before acting: **`[.]` is a provenance marker, not a
    period** — `review_server.py:1603` writes it when a reviewer ACCEPTS a
    proposed punctuation insertion and `audit_applied_decisions.py` checks for it
    specifically, so flattening 92 of them to `.` would erase the distinction
    between the printer's punctuation and ours and break that auditor — and `•`
    and `:` are marks that are **on the page**.

    **The 16 bare cases are correct as they stand.** Rendered klalim 36 and 106 at
    3x and read the lines: `לו אלא אין דרך השית' סדרי...` and
    `קו בחירתא היא מס' עדיות י"א שאינו...`. **The printer sets no mark there** —
    the bold lead word runs straight into the text. Inserting a period would be
    adding punctuation the original does not have, which is exactly what the `[.]`
    convention exists to record. No edit made.

    **The single comma is a misread middle dot.** Rendered klal 105 at 4x: the
    printer sets a raised `·` after `אמרו` — **the same mark it sets after
    `נינהו` later on the same line, which the corpus already transcribes as `•`**.
    One printed mark, two transcriptions. So this is not "a comma that should be a
    period"; it is `,` -> `•`, and the fix restores agreement with the ink rather
    than imposing a house style on it.

    **Recorded as a word-level flag, not a hand-edit.** Titles were hand-edited
    this session because no apply path exists for that field; `clean_text` HAS
    one, so the single-source-of-truth rule applies at full strength and this goes
    through the dashboard like any other correction. Flag `2e1168f7e5f3` on
    klal 105 w4, carrying the scan reading.

    **CLASS SWEPT, deliberately not flagged: Part 1 carries 26 commas across 23
    klalim** (klal 4 w27, 31 w159, 36 w66, 41 w609/w717, 44 w433, 54 w341,
    70 w94, 83 w41, 91 w579, 94 w22, 100 w31, 105 w4, 118 w14, 126 w44,
    134 w5, 140 w113, 146 w7/w36, 147 w67, 154 w398, 155 w110, 159 w63,
    161 w16, 167 w566/w1067). Any of them may be the same misread; **only klal
    105 w4 has been read against the scan.** The other 25 are recorded here
    rather than flagged, because 25 flags on unread material is how the 1,496-flag
    queue in item 1 happened. Whoever picks this up: the check is a 4x render of
    the line, and the tell is whether the same glyph appears elsewhere on the line
    already transcribed as `•`.

44. **[2026-08-31] I OVER-CORRECTED SEVEN TITLES ON MY OWN INFERENCE AND
    REVERTED THEM. Recorded because the reasoning error is the useful part.**
    The reviewer named klalim 101 (missing `ב"ד`), 105, 132/133 and 134/135.
    Rendering `page_44.png` and `page_49.png` at 2x showed the printed heading of
    each klal set in BOLD — `בית דין` for klal 100, `ב"ד` for 101-105, `דיעבד`
    for 131-133, `דחיה` for 134-135 — and I generalised that into a rule: **the
    title is the bold lead run**. On that rule I truncated klalim 100-105 to
    `בית דין.` / `ב"ד.`, including four the reviewer never mentioned.

    **The rule is wrong.** The reviewer's next message gave klal 105's title as
    `ב"ד שלאחריהם אמרו` — bold word PLUS the following phrase — and klal 106's as
    `בחירתא היא מס' עדיות`, where `בחירתא` alone is what is bold. So the heading
    is not the bold run; the bold is a lead-in and the heading continues past it
    by an amount only a reader can judge. Klal 132 (`דיעבד`) and klal 105
    (`ב"ד שלאחריהם אמרו`) are the same typographic shape with different answers.

    Reverted: klal 100 to its original title (never asked for), and 101-104 given
    the `ב"ד` they were missing rather than a truncation, which is what the
    reviewer actually asked for. 105 and 106 set as dictated.

    **What I should have done, and the rule going forward: STOP INFERRING A
    GENERAL RULE FOR TITLE EXTENT.** I have now guessed it twice — first that
    titles were the whole opening sentence, then that they were the bold run —
    and been wrong both times, in opposite directions. Lesson 31's shape exactly:
    a heuristic retuned twice is asking to be handed back, not tuned a third time.
    Title extent is a per-klal reading against the scan and is the reviewer's
    call; the tooling's job is to SHOW the comparison
    (`tools/compare_titles_to_text.py`), not to decide it. **27 Part 1 titles are
    long-but-clean prefixes and remain unadjudicated** — flagged as suspicion,
    with no rule applied to them.

    Part 1 title state after all of this: **222/222 clean prefixes, 0 divergences,
    0 offsets.**

45. **[2026-08-31, reviewer] The index shows a title without its terminal period;
    the running text keeps it, because there it does a job.** "no period in the
    index pane - it is needed in the text pane to sep the title from the text."
    The period stays on the stored field, where the gated invariant requires it —
    this is a presentation choice, stripped at render by `displayTitle()`, one
    function so every list surface agrees. In a column of 222 headings the period
    is noise; in running text it is the only thing marking where the heading
    stops. Spacing added around the heading run in the text pane
    (`margin-inline-end`, logical properties so it stays correct in the RTL
    column) rather than a wider word-space, so the gap falls once at each boundary
    instead of between every heading word.

46. **[FIXED 2026-08-31 — item 0E, reported by the reviewer as "clicking on 105
    in the index moves the text pane but not the scan".** The symptom was ONE KLAL
    OFF, not a dead pane: the scan did move to page 44, but the scroll observer
    set the active klal to **104** on the way past, so the header read "Klal 104"
    and the scan outlined 104's region while the text pane sat on 105.
    `jumpTo()` released the observer after a fixed **700ms** and a long smooth
    scroll takes **~1500ms** to settle.
    Fixed by `releaseObserverWhenScrollSettles()`, which waits for the scroll to
    actually stop — two consecutive frames at the same offset, with a 3s ceiling
    so a pane that never settles cannot suppress the observer forever — and then
    re-asserts the destination, since the observer was held off for the whole
    animation and never recorded where it landed. **A bigger constant would have
    been the same bug with a longer fuse** (Lesson 31: remove the guess, do not
    retune it).
    Gated by `test_a_nav_jump_lands_on_the_klal_it_was_asked_for`, which asserts
    the active klal AND the scan page because the bug moved one without the other,
    and covers the longest jumps deliberately — at the end of the corpus the
    scroll clamps and cannot put the destination at the top of the pane, so the
    observer's "last block above the reading line" answer is structurally wrong
    there. **Verified it catches the real bug**: with the 700ms behaviour restored
    it fails with "jumped to klal 105 but the index made klal 104 active".
    Two findings about the test harness, worth keeping: `suppressObserverScroll`
    and `currentPage` are script-scoped `let` bindings, NOT window properties, so
    polling `window.currentPage` silently reads `undefined`. Both are now read
    from the DOM (the scan `<img>` src carries the page number), which is the
    honest place to ask what is actually on screen.

42. **[2026-08-31, reviewer] Titles: two more extent fixes, and a punctuation
    rule now gated. Part 1's title field is, for the first time, internally
    consistent.**

    | klal | was | now |
    |---|---|---|
    | 10 | `איידי דקתני במתניתין ואינו עובר עליו נקט נמי בברייתא הכי` | `איידי דאיידי.` |
    | 66 | `אין ביטול ממש אבל להוסיף על תקנתם לאו ביטול מקרי` | `אין ב"ד יכול לבטל דברי ב"ד חבירו אא"כ גדול ממנו בחכמה ובמנין.` |

    Both were the two divergences item 41 could not classify, and both were the
    same shape as klal 36: the stored title was not a misspelling of the heading,
    it was **different text entirely**. Part 1 now has **0 divergences** — every
    one of its 222 titles is a clean prefix of its own body.

    **TERMINAL PUNCTUATION, applied to all 222** (reviewer: "each title should end
    with one period - no more no less. no other punct acceptable"). Not one Part 1
    title ended with a period before this; none contained one at all. All 222
    changes were **pure appends** — the dry run confirmed nothing was removed from
    any title, which is what made this safe to apply in bulk.

    **WHAT "no other punct" WAS NOT ALLOWED TO MEAN.** Read literally it would
    strip `"` and `'`, and those are gershayim and geresh — parts of Hebrew
    ABBREVIATIONS, not sentence punctuation. `ב"ד` is בית דין and `וכו'` is a word;
    removing the marks would have corrupted **121 and 80 occurrences**. The
    reviewer's own klal 66 title, supplied in the same message, contains `ב"ד` and
    `אא"כ`, which settles the reading. Five titles legitimately end `וכו'.`,
    keeping the geresh that belongs to the word and taking the period after it.

    Gated by `test_every_part1_title_ends_with_exactly_one_period`. Verified it can
    fail, per Lesson 25: replacing klal 1's period with a colon fails it by klal id
    and reason. **Scoped to Part 1 deliberately** — Parts 2-3 titles are machine
    truncations (`…`, and some are literally `כלל 447`) rather than transcribed
    headings, so normalising their punctuation would be both gate-violating and
    meaningless. `corpus_io.title_word_span()` is unaffected by the new periods
    because it normalises through `hebrew_letters_only`, verified on five klalim
    after the change.

43. **[2026-08-31, reviewer] The two standalone corpus reports are now stage 5b
    of `rebuild_all.sh`, because they had silently aged out of agreement with the
    corpus.** Raised by the reviewer directly.

    **The mechanism, stated plainly.** `tools/list_ligature_words.py` and
    `tools/review_lexicon_only_words.py` each read the corpus and write a JSON
    report, and **neither was in any chain**. So each report kept whatever numbers
    it had from the last time somebody remembered to run the tool. Nothing was
    wrong with either tool. `ligature_words.json` was stamped 2026-08-30 21:49,
    before that night's corpus edits, and still claimed **`both_lost: 3`** when two
    of those three ampersands had been repaired to `אל` (klal 69 w338, klal 167
    w24) and only klal 77 w11 survived. `lexicon_yad_malachi_only.json` was stale
    the same way.

    **Why it matters more than a wrong number in a file:** a stale count is
    exactly the kind of figure that gets quoted into a status entry or a decision
    as though it were measured today. This file's own TL;DR says every claim in it
    is measured rather than remembered; an unrebuilt report quietly breaks that.

    This is **Lesson 32 in its milder form** — not a detector nobody runs, but a
    report nobody RE-runs — and **Lesson 13** besides: a file fully computable from
    the corpus is a second copy of the truth until something rebuilds it.

    **FIXED by putting them in the chain**, the same remedy stage 4b got: measured
    at **0.28s and 0.24s** on the full corpus, so the reason for leaving them out
    never really existed. Both are pure readers — they write only their own report,
    never a flag, a decision or corpus text — which is what makes this safe to run
    unattended on every rebuild. `review_lexicon_only_words.py` needs the gitignored
    `sefaria_reference_corpus` cache and exits 0 with an explicit "this is not 'no
    findings'" message when it is absent, verified by hiding the cache, so a fresh
    clone is not broken by the new stage.

    **Two alternatives considered and rejected:** a gated staleness test comparing
    report mtimes against `part*.json` would DETECT the problem but then block the
    build until someone re-ran the tools by hand — detection where prevention costs
    half a second; and deleting the committed JSON in favour of print-only output
    would lose the diffable artifact these reports exist to provide.

    Post-rebuild the reports read `both_lost: 1`, dropped-lamed 321, dropped-alef
    18, and 1,144 lexicon-only words — and note that `both_lost` only became
    correct because the tool happened to be run, which is the whole argument.

41. **[2026-08-31, reviewer] A TITLE-vs-TEXT COMPARISON NOW EXISTS FOR EVERY
    KLAL, and the heading is rendered where the book actually puts it — inside the
    text, not above it.**

    **`tools/compare_titles_to_text.py`**, run over all 667. The structural
    property it tests: a title should be a PREFIX of its own `clean_text` after
    the gematria marker, because the printed heading is not separate text — it IS
    the klal's opening, set in larger type.

    | | all 667 | Part 1 |
    |---|---|---|
    | clean prefix of their own body | 581 | 216 |
    | …of which long (>= 11 words), a suspicion only | 24 | 24 |
    | DIVERGES — an OCR error in one of the two | 82 | 2 |
    | offset — title starts at a later body word | 4 | 4 |

    Part 1 is down to **2 divergences** (klalim 10 and 66, where the title matches
    almost none of its body and something structural is wrong) from 14 before this
    session's edits. **The remaining 80 divergences are all in Parts 2-3** and are
    untouched under the gate. Two lessons went into the tool rather than being
    discovered twice: editorial punctuation tokens in the body (`,` `.` `[.]` `•`)
    are SKIPPED, not counted as mismatches — without that, klalim 105 and 134 read
    as OCR divergences when the only difference is a comma the punctuation pass
    inserted; and a title that is a clean but LONG prefix is reported as a
    suspicion with the threshold stated, never as a finding, because this book's
    genuine headings run to 24 words and only the scan says where a heading stops.

    **The heading now renders IN PLACE** (reviewer: "i didn't want the title above
    the text… i want the text itself to have bold for counter and title in the diff
    font — right there in the text"). Yesterday's version put the title on its own
    line above the klal, which renders it twice, since those same words open the
    body. The marker is bold and the heading run is set in `--font-title`, both as
    words in the running text. `corpus_io.title_word_span()` computes how many body
    words the heading occupies and is shared by the server, the audit tool and the
    UI, so the three cannot disagree; it degrades safely, returning 1 for klal 66
    where the title matches only the first word.

    **Applied as a pass over the rendered spans, not inside the word loop** —
    that loop has five branches (plain, ai_flag, disputed, manual, witness) and a
    word is drawn by whichever claimed it, so decorating from inside would be the
    same two lines in five places (Lesson 13/34) and a heading word that happened
    to be disputed would silently miss out. `markTitleRun()` is one rule over the
    final DOM. Neither role class sets `color`, so the state colour a reviewer
    navigates by still shows through on a heading word.

    Sizes raised in both panes and the index number set in `--font-marker`, the
    same face as the text-pane head, so the number reads as the same object in
    both places. Gated by a regression that reads the expected heading length from
    `/api/klal/36` rather than hardcoding it, asserts the title is NOT repeated
    above the text, and compares resolved font families rather than literal names.

40. **[2026-08-31, reviewer] The index pane now carries both scripts on every
    line, and a long title can no longer squeeze the badges off the row.** Each
    row reads `39` · `לט` · title · flag · counts, and the text-pane head now
    reads `כלל 69 · סט` + section + the TITLE, which it never showed at all.

    **Structural typography tokens, added so this generalises past this book.**
    Four `:root` variables — `--font-title`, `--font-marker`, `--title-size`,
    `--marker-size` — plus one `.klal-title` role class used by BOTH panes. They
    name the ROLE a piece of text plays in a sefer's structure, not this printing's
    layout, so a work set differently restyles itself by re-pointing the tokens and
    touches no rules. Before this each pane styled its own text ad hoc, which is
    why the two could differ at all. The title face is deliberately NOT the body
    face: the body is Frank Ruhl Libre, so a title in it reads as more body text;
    `David Libre` is a different Hebrew serif of the same period feel. The
    regression compares RESOLVED font families between panes rather than asserting
    a literal font name, so re-pointing the token for another work keeps it green —
    which is the point of having the token.

    **The scan header's two scripts were separated by ONE SPACE, not the gap the
    rule claimed.** `#klal-indicator` had `margin-inline-start: 1.75rem`, and
    `margin-inline-start` resolves against the ELEMENT's own direction — that span
    is `direction: rtl`, so it became `margin-right: 28px` and put the gap on the
    far side, outside the row. What was left was the literal space in `index.html`:
    a measured **3px**, which is exactly what the reviewer saw. Now an explicit
    `margin-left`, measured at 31px. Gated by a test that asserts the rendered GAP
    between the two boxes — the property was present and read correctly the whole
    time, and only the geometry showed it was landing on the wrong edge. `gematria` has been on
    `/api/klalim` since 2026-08-26 and the nav simply never used it. The row's
    number columns and badges are all `flex-shrink: 0` and only `.ntitle` gives
    way — `.nid` was shrinkable before, which is what let a long title push the
    right-hand end of the row out of view. Gated by a regression that asserts the
    Hebrew column AND checks by GEOMETRY that every badge on the longest-titled
    row still has non-zero width inside the row box; it locates that row by
    looking for the badges rather than pinning a klal id, per item 0F.

    **REFACTOR NOTE, requested by the reviewer and earned the hard way: collapse
    the three duplicated init fetch blocks.** The same
    `Promise.all([/api/flags, /api/klalim, /api/witness])` appears in `init()`,
    `switchPart()` and the post-decision refresh path. Adding a fourth fetch to
    the wrong one of the three cost real time in this session (item 38) and the
    failure was silent, because the globals the OTHER copy sets still looked
    populated. It should become one `loadCorpusState(part)` that all three call.
    Not done here — it touches the app's startup path and wants its own
    before/after, and this session had already changed the frontend four times.
    This is the same shape as `union_bbox()` and the `.split(' ')` sites in
    item 37's structural list; it belongs with them.

38. **[2026-08-31, four reviewer reports on the deep-link flow — all four
    reproduced, fixed and gated.]** Each was measured in a real browser before
    being touched, and two of the four were not what the report said they were,
    which is the part worth keeping.

    **(a) The index pane did not scroll all the way to the klal.** `setActiveKlal`
    scrolled the nav with `block:'nearest'`, which moves the MINIMUM distance that
    makes the row visible. Correct for the continuous scroll-driven reaction it
    was written for; wrong for a jump. Measured on `/klal/210/word/133`: the row
    landed at bottom **1001px against a pane bottom of 1000px** — one pixel PAST
    the fold, so the single row the link exists to reach was the one row the
    reviewer could not see. A deliberate jump now centres; the scroll reaction
    still uses `nearest`, where it is a no-op when the row is already visible.

    **(b) "Moving the cursor over the text makes the highlight disappear" — it was
    not the cursor.** The `.routed-word` ring carried a hard
    `setTimeout(..., 4000)` and simply expired. Measured: the ring survives a
    mouse move at 900ms and is gone at 4s with the pointer untouched. 4 seconds is
    about how long it takes to read the line and start moving the mouse, so the
    two read as cause and effect. The ring now persists until the reviewer
    actually goes somewhere else (a new route, or `clearScanFocus`). **Worth
    noting as a diagnosis pattern: the reported trigger was a coincidence of
    timing, and believing it would have sent the fix into the hover handlers,
    which are not involved at all.**

    **(c) Clicking a highlighted word in the SCAN did not highlight it in the
    text.** The text→scan direction has had a single funnel since 2026-08-25
    (`focusWordOnScan`); the scan→text direction had **nothing** — a scan click
    moved the scan and opened a decision panel, and the middle pane was never
    told. Added `revealWordInText()` as the mirror funnel, shared with the
    deep-link router rather than copied. Two call sites, and the second is the one
    that mattered: **the `kind === 'plain'` box had no click handler at all**, and
    that is precisely the box a deep link draws — so the one word a shared link
    exists to point at was the one word clicking on the scan did nothing for.

    **(d) The scan header now carries the reference in both scripts** (reviewer:
    "Page xx Klal xx, white space, then the same info in Hebrew"). It reads
    `Page 73 · Klal 210` and then `דף עג · כלל רי`. Before, it showed the page in
    one span and a bare `כלל 210` in the other — a Hebrew word beside an Arabic
    numeral, which is not how the book writes it.
    **CAVEAT, recorded because it is genuinely ambiguous and could mislead:**
    `דף עג` is OUR page index written in Hebrew letters. **It is NOT the folio the
    printer set on that leaf** — the printed folio is stripped as page furniture
    (items 20 and 27) and is stored nowhere in this repo, so there is nothing to
    render for it. If that reads as a claim about the book rather than about our
    pagination, the Hebrew page half should be dropped and only `כלל רי` kept.
    The numerals are SERVED from a new `/api/numerals` endpoint over
    `cio.klal_id_to_gematria`, not reimplemented in JS: a JS copy would be
    Lesson 13, and would have had to re-derive the 15/16 exception (`ט"ו`/`ט"ז`,
    not `י"ה`/`י"ו`, which would spell divine names) and the final-letter rule.

    **I made this session's own Lesson 34 mistake while fixing (d), and it is
    recorded rather than quietly corrected.** The three-fetch block at init exists
    in **three** copies (`init`, `switchPart`, and the post-decision refresh) and I
    added the numerals fetch to `switchPart` — the wrong sibling. The header
    rendered `דף 73`, silently, because `hebNum()` falls back to the digits, and my
    own verification passed on `FLAGS`/`KLALIM` being populated, which `init` had
    done. What caught it was the server log showing **`/api/numerals` was never
    requested at all**. The fetch now lives in `init` only, since the table is a
    pure function of the integers and can never return anything new on a part
    switch.

    Four Playwright regressions, one per report, plus the 0G guard. **363 tests
    pass.** The three that can look their subject up off the DOM do so rather than
    pinning a coordinate (item 0F); the header test necessarily pins klal 210 /
    page 73, and asserts the Hebrew half contains `עג`/`רי` AND does **not**
    contain `73`/`210` — without that second half it would have passed against the
    digits-fallback bug it exists to catch.

37. **[SWEEP 2026-08-31] Every finding in every code- and data-review file
    re-verified against the live tree. Two new defects; item 9c was stale; the
    structural backlog is real but smaller than the review files read.** Method:
    each claim was reproduced by running or reading the current source, never
    accepted from the write-up (Lesson 19). Files swept:
    `code-review-2026-08-25.md`, `CODE-REVIEW-2026-08-26.md`,
    `CODE-REVIEW-2026-08-27.md`, `LEXICAL-DEFECT-AND-FLAG-AUDIT-2026-08-27.md`,
    `open_items_2026-08-30.json`, `cleared_flags_2026-08-26.*`, and this file's
    own open items.

    **NEW — see item 0G**: two UI tests shadowed by duplicate definitions, the
    stricter copy of each discarded.

    **NEW — the multi-word manual-replacement guard landed in ONE of the two
    files the audit named.** `CODE-REVIEW-2026-08-27.md`'s remedy #2 says
    explicitly "in both `apply_reviewer_decisions.py` and `tools/export_corpus.py`".
    `manual_correction_changes_word_count()` exists and is called at
    `apply_reviewer_decisions.py:592`; `export_corpus.py`'s manual-replace branch
    (its `else:` at ~line 151) calls `_apply_manual_correction` with **no
    word-count check and no `word_count_changed_klalim.add`**, though that same
    function guards its insert and delete branches. Item 36 recorded the fix
    without noting it was half-applied. This is Lesson 34 exactly — sweep the
    SIBLINGS, and the sibling here was named in the finding itself.
    Live exposure **0 today**: no manual decision has multi-word `chosen_text`
    (re-measured, not remembered). Latent, like its twin was.

    **Verified FIXED and holding** (each re-measured): the four item-36
    "critical" defects; the `_corpus_bbox_cache` invalidation (now keyed on a
    `part1/2/3.json` (mtime,size) stamp — note the stamp does NOT cover
    `docai_word_boxes/` re-extraction, which the original finding also named);
    item 20's watermark (**0 Latin-script tokens corpus-wide**); item 16
    (**71 placeholders / 596 with text**, exact); item 0D(a) (**0 new unlocatable
    open flags**; the baseline shrank 10 -> 7 as words were repaired); item 24
    (`lexicon.txt` **18,936** rows, exact); item 32 (175 intact / 321
    dropped-lamed / 19 dropped-alef / 3 both-lost / **0** U+FB4F, exact).
    All 317 gated tests pass; all 36 collected UI tests pass.

    **Verified STILL OPEN, structural, none of them new** — recorded here because
    they live only in the review files today: `synthesize_multi_witness.py:56`
    still imports `review_server` and calls three private helpers (C4);
    `review_server.py` is now **1,955 lines**, up from the 1,849 that was filed
    as a God Object and the 1,736 before that (S1); 12 `.split(' ')` sites across
    5 files (S2 — the review said "14+ across 7", it is 12/5); `_parts_for()`
    still returns Part 1 for `?part=4` (S4); `223`/`444`/`445` still inline in
    `review_server.py:132-146` and `corpus_io.py` still exports only
    `PART1_MAX_KLAL` (S5/#6); `_NO_UPPER_BOUND = 10 ** 9` (H2); `union_bbox()`
    still byte-identical in two pipeline stages (H3/#8); both superseded
    `extract_*_consensus_disputes.py` stubs still in `tools/` (H4); the
    `clear-word-flag` handler still duplicated in `app.js` (#18/#9).
    **#7 is weaker than filed**: `reconstruct_placeholder_klalim.py` imports
    `FURNITURE_WORDS` from `check_span_shortfall`, but that module is itself
    `FURNITURE_WORDS = cio.FURNITURE_WORDS` — an indirection, not a divergent
    copy, so it cannot drift. Worth tidying, not a Lesson 13 instance.

    **CORRECTED [2026-08-31, re-sweep] — four of the numbers above were wrong,
    and one whole finding was missed. Counted, not remembered.** The sweep's
    method was right and its dispositions hold; its measurements were taken too
    narrowly, which is Lesson 1 in miniature — a sweep scoped to where the
    finding pointed rather than to the whole class.

    (a) **C4 is FOUR modules and FIVE private-helper call sites, not one.**
    `synthesize_multi_witness.py:348` (`rs._word_bboxes_resolved`) and `:370`
    (`rs._load_regions`) are the two the sweep named, but also
    `pipeline/assemble_corrections_dataset.py:263` (`_rs._word_scan_position`),
    `tools/validate_suppression_filters.py:194` (`rs._load_witness_queue`) and
    `tools/patch_witness_word_indices.py:50` (`rs._load_klalim`). So the batch
    pipeline's dependency on the live HTTP server's privates is four times
    wider than the finding that named only `synthesize_multi_witness.py`, and
    an `scan_alignment.py` extraction alone does not close it — two of the five
    want a decisions/queue loader, not geometry.

    (b) **S2 is 27 `.split(' ')` code sites across 14 non-test files**, not
    "12 across 5". Full list from `grep -rn --include='*.py' "split(' ')"
    pipeline tools`, comments excluded: `apply_reviewer_decisions.py` ×8,
    `review_server.py` ×5, `audit_applied_decisions.py` ×2,
    `propose_punctuation_part1.py` ×2, and one each in `corpus_io.py`,
    `build_klal_page_regions.py`, `build_corrections_dataset.py`,
    `assemble_corrections_dataset.py`, `apply_punctuation_decisions.py`,
    `build_open_items_report.py`, `validate_part1_corpus_integrity.py`,
    `patch_witness_word_indices.py`, `list_ligature_words.py`,
    `second_witness_eval/run_part1_vlm_second_witness.py`. **The newest site,
    `tools/build_open_items_report.py:74`, was written on 2026-08-31 — the same
    day as the sweep that counted 12.** The scheme is not just unconsolidated,
    it is still spreading, and there is still no `corpus_io.words_of()`.

    (c) **S1 is 1,981 lines**, not 1,955. Third measurement in the same
    direction: 1,736 → 1,849 → 1,955 → 1,981.

    (d) **NEW — 08-26 finding #2 was half-swept, exactly like the multi-word
    guard above, and for the same reason.** The finding named TWO copies of the
    `word_freq.json` loader: `reconstruct_placeholder_klalim.py:97` and
    "`validate_suppression_filters.py:87` is a second copy". The first now
    delegates to `docai_filter.reference_frequencies()`;
    `tools/validate_suppression_filters.py:87 load_reference_freq()` is still a
    private hand-rolled `json.load` with its own path literal and no
    `lru_cache`. Live divergence **0** — that file's `norm` is
    `cio.hebrew_letters_only`, the same normalisation the canonical loader
    applies, measured not assumed — so it is latent, like its twin was. **Two
    findings in this batch (this and remedy #2) were each fixed in the first
    file they named and not the second, and in both cases the second file was
    named in the finding text itself.** That is Lesson 34 twice in one review
    cycle; the sibling is not merely nearby, it is written down.

    One more, minor: **#4's fix keeps `HEADER_CONTAMINATION_RE` in step with
    `tests/test_corpus_invariants.py:92` by COPYING the pattern string
    (`_PYTEST_INVARIANT_RE`), not importing it, and no test asserts the two
    agree** — unlike #7's `MACHINE_RESOLVED_FLAGS`, which got exactly such a
    guard. Working today; a one-line divergence away from not.

    **Item 27 is two-thirds done, and the remainder is now UNFLAGGED.** klal 74's
    seam is fully repaired (both spurious words deleted, 2026-08-30). klal 39 lost
    its `Π` folio — but the *catchword* `דבכולהן` at w251, which item 27 names as
    part of the same three-word defect, **is still in the corpus and carries no
    open flag**, because the flag that was cleared was the folio's. klal 210's
    Hebrew-numeral folio `לא` at w66 is still present and still flagged.

    **SUPERSEDED [2026-08-31, later same day] — re-measured by CONTENT, and two
    of the three statements above no longer hold.** They were written against
    word INDICES, and the day's own corrections shifted them; re-reading the
    same indices now describes different words. Search by the token, not the
    position (Lesson 5's shape, applied to one's own status entry):
    - **klal 39 is CLEAN.** `דבכולהן` appears **0 times** anywhere in the klal
      (which now runs 663 words and ends `…והוא פלא :`). The catchword was
      removed at some point after the sweep. w251 today reads `היכי`.
    - **klal 210's `לא` cannot be confirmed from the text.** The token appears
      **twice** (w74, w133), not at the w66 the item names, and `לא` is also
      one of the commonest words in the language — so which occurrence, if
      either, is the folio intrusion is **not answerable without the scan**.
      The flag at w66 now reads `needs_revisit: false`. This one needs a look
      at the ink, not another grep.
    - **Item 16 is a Parts 2-3 item, not a Part 1 one:** 71 placeholders
      corpus-wide and **0 in Part 1**, so it sits behind the Parts 2-3 gate and
      is not workable now.

    Live queue at the same moment, from `tools/build_open_items_report.py`:
    **225 open word-level flags, 126 open klal-level, 0 out-of-range, 4 null
    decisions still standing.** The klal-level count is UP from the 88 recorded
    earlier in this item — worth knowing before anyone treats that number as a
    burn-down.

    **Two standalone reports are stale against the corpus they describe.**
    `ligature_words.json` and `lexicon_yad_malachi_only.json` are both stamped
    2026-08-30 21:49, before the 2026-08-31 corpus edits; `ligature_words.json`
    still lists `both_lost: 3` where only **1** `&` survives. Neither tool is in
    `rebuild_all.sh` — Lesson 32's exact shape, in a milder form: not a detector
    nobody runs, but a report that silently ages out of agreement with the text.
    `lexical_defect_report.json` does NOT have this problem; it is stage 4b and
    regenerated (now **280 candidates / 93 klalim / 194 unflagged**, against item
    35's dated 299 / 96 / 194).

    **Item 26 is down to one.** `validate_part1_corpus_integrity.py` check 2b now
    reports a single out-of-repertoire character, klal 77 w11 `&` — from 7.

    **`open_items_2026-08-30.json` WAS HAND-WRITTEN, and it rotted — now
    generated.** It is fully computable from `review_decisions.jsonl` plus the
    corpus, which makes a hand-kept copy Lesson 13 exactly: a "derived" file that
    is really a second copy of the truth, agreeing until the text moves under it.
    It moved. Six of its 24 flagged items were resolved and still listed as open,
    and its lead entry, "NEEDS YOUR RULING on klal 66 w0", had been ruled on the
    day before it was written. **`tools/build_open_items_report.py`** now derives
    the queue from live state; `tools/render_report.py` turns it into clickable
    deep links, so the list cannot age. Current Part 1 queue, measured:
    **233 open word-level flags, 88 open klal-level flags, 0 out-of-range,
    4 null decisions still standing.** The rendered `.md`/`.html` are gitignored,
    the same as every other report view.
    Two details the generator had to get right, both found by running it rather
    than reading it: it splits on a SINGLE space (`.split()`'s whitespace
    collapsing renumbers every word after a double space and points every link one
    word off), and `word_index == len(words)` is the legitimate END-OF-KLAL append
    position for an insert/delete opcode, not an out-of-range index — the two
    surviving null decisions at klal 88 w1149 and klal 164 w55 are both exactly
    that, and a naive bounds check filed them as corrupt.

## Closed — the detail is in `PROJECT-STATUS-HISTORY.md`, by date

Kept as an index so a reference to an old item number still resolves. Nothing here needs action.

| item | what it was | outcome |
|---|---|---|
| 9 / 9a / 9b / 9d / 9e | 2026-08-23 code review, 18 findings across two passes | C1-C4, C15, H5, H6, H8, M11, C16 all fixed; what is still open is item 9c |
| 11 | klal 16's 23 missing words | applied 2026-08-23, user-authorized; span check clean |
| 13 | 2026-08-24 code review, 11 findings on this session's own work | F1-F7 fixed 2026-08-24, F9-F10 fixed 2026-08-25; F8 and F11 accepted open, see item 9c |
| 14 | 14 → 40 stale DocAI page files in the 248-337 range | re-extracted 2026-08-25; zero duplicate page pairs remain anywhere in the book |
| 15 | `sefaria_export/` stale and wrongly attributed | regenerated 2026-08-25 by `export_corpus.py --format sefaria`; Berlin 1851/2, 667 klalim, placeholders empty |
| 17 | klal 88's nav badge read −1 | fixed 2026-08-25; decided was counted per source while the total was counted per word; 3 klalim, 6 phantom decisions |
| 18 | the dashboard offered `6.18M` as a reading, on one click | fixed 2026-08-25; extraction ordered and validated, `Use "X"` no longer saves |
| — | four scan-pane defects on klalim 3 and 4 | fixed 2026-08-25: insert boxes spanning a line break (21 of 40), the klal outline missing on continuation pages, manual words not focusing the scan, manual entries with no bbox |
| — | word-level flags answered by a later decision | fixed 2026-08-25; 23 flags across 7 klalim were still lit on words the reviewer had already ruled on |

---

**Everything else is history.** `PROJECT-STATUS-HISTORY.md` holds the full dated
log, newest first - every finding above traces to an entry there. This file is
meant to be readable in one pass; if it stops being that, move the closed items
out rather than appending.
