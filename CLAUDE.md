# Yad Malachi Pipeline

Digitization pipeline for **Yad Malachi** (R. Malachi ben Jacob HaKohen, Livorno
1766–7), a foundational halachic-methodology reference with 667 *klalim* across
three parts. Goal: a clean, structured digital text for Sefaria — see
`CASE-YAD-MALACHI.md` for the full rationale (287 dead Sefaria citations point to
this work today).

> **Read `PROJECT-STATUS.md` at the start of every session, every time, no
> exceptions.** This file (`CLAUDE.md`) holds durable rules and architecture.
> `PROJECT-STATUS.md` holds the current, specific, dated truth — what's fixed,
> what's still broken, what was investigated and why. Neither substitutes for
> the other. Do not report on, fix, or make claims about corpus quality
> without having read it first.

> **Close open items before proposing new ones.** If `PROJECT-STATUS.md`'s
> Open Items section lists unresolved blockers, do not end a turn by offering
> to expand scope ("want me to also check X," "should I dig into Y next") —
> propose a plan to close the existing open items first, or ask which to
> prioritize. Finish what's already known-broken before suggesting where else
> to look.

> **Log every finding to `PROJECT-STATUS.md` yourself, immediately, without
> being asked.** Finding a bug and only mentioning it in chat is not done —
> if the user has to go back through the conversation to recover something
> you found so it isn't lost, that is a dropped ball, and recovering dropped
> balls is not the user's job. The moment you confirm a real issue (a bug, a
> gap, a wrong claim in the file, a script fix, a new script, a job left
> running), write it into `PROJECT-STATUS.md` before moving to the next
> thing — not batched at the end of a long turn, not only when directly
> asked to "update the status file." This applies to your own tooling/script
> fixes too (cache bugs, dead models, UI fixes), not just corpus-content
> findings.

## Pipeline shape

## Success criteria (in priority order)

1. **Absolute fidelity to the author's words.** The transcript must match the
   source scans exactly — no paraphrase, no silent normalization, no
   "improving" the text. Every correction must be traceable to a real OCR/VLM
   disagreement resolved by looking at the actual scan, not inferred.
2. **Accurate klal chunking.** Each of the 667 klalim must be correctly formed
   and delimited as its own unit, matching Sefaria's structural conventions —
   wrong boundaries (a klal split, merged, or mis-numbered) are as serious a
   defect as a wrong word.
3. **Sefaria-ready output.** The end deliverable must be usable as-is inside
   Sefaria's library in every respect (structure, encoding, section/klal
   numbering, citation-linkability) — not merely "clean text," but ready to
   ingest.

Any pipeline change, correction pass, or shortcut should be weighed against
these three before anything else (speed, script cleanliness, cost).

## Pipeline shape

Source scans (`berlin_square.pdf`, Sefaria VLM output, DocAI OCR) get extracted,
cross-validated between OCR engines, and adjudicated word-by-word before landing
in the canonical text files. Concretely:

1. **Extraction** — `chunker.py` pulls raw text per page from the PDF (handles
   the reversed-Hebrew-line quirk of these 19th-century scans via
   `unreverse_line`). DocAI/VLM extraction happens through the (gitignored)
   `docai_word_boxes/`, `document_jsons_berlin/`, `vlm_extractions/` caches.
2. **Adjudication** — `orchestrator.py` is the live, `[PRODUCTION]`-tagged
   cross-validator: crops each token's bounding box from the PDF, sends it to
   Gemini (`google.genai`) for a vision-based OCR/VLM disagreement call, and
   caches every decision in `adjudication_cache.db` (sqlite, keyed by crop
   hash) so repeat runs don't re-spend API calls. Requires a Gemini API key in
   the environment (not committed — check `credentials.json`, gitignored).
3. **Assembly & lexicon** — outputs converge into `full_text_cleaned.txt` /
   `full_text_cleaned_goal.txt`, `part1.json` / `part2.json` / `part3.json`
   (one per Yad Malachi section), `processed_klalim/` (per-klal JSON, 813
   tracked files), and `lexicon.txt` (~19k unique validated Rabbinic Hebrew
   words used as a spell-check dictionary during cleanup passes).
4. **Demos/reports** — `SEFARIA-VLM-DEMO.html`, `SEFARIA-BERLIN-DEMO.html`, and
   the `*-VISUAL-REPORT.html` / `*-OVERVIEW.html` files at root are rendered
   inspection demos, not pipeline code — open them in a browser to visually
   verify a correction, per the `.gemini/rules/robust_ocr_processing.md` rule
   file's UI-verification requirement.

## Single source of truth for corpus text — read before editing any text file

**`part1.json` / `part2.json` / `part3.json` are the only hand-edited source
of truth for klal text.** Every other JSON/HTML artifact that shows or uses
klal text is *derived* from them and must be regenerated, never hand-edited
in parallel:

- `klalim_demo_dataset.json` = `part1.json` + `part2.json` + `part3.json`
  concatenated, nothing else. Regenerate with `build_klalim_demo_dataset.py`.
  (Before 2026-08-05 this was hand-maintained in parallel with the part
  files on every fix — exactly the kind of two-copies-of-the-truth setup
  that silently drifts. Don't reintroduce that.)
- `corrections_candidates_part1.json` → `corrections_verified_part1.json` →
  `corrections_part1.json` → `review.html`'s flag overlay is a pipeline, each
  stage derived from the one before it and from `klalim_demo_dataset.json`.
- `klal_page_regions.json` (per-klal scan bounding box, independent of
  whether the klal has any flagged correction) also derives from the same
  docai-token alignment.

**After any edit to a `part*.json` file, run `./rebuild_all.sh`** — this
regenerates every derived file listed above, ending in a fresh
`review.html`. Don't hand-run individual stages and try to remember which
ones are now stale; that's exactly how `review.html` went out of sync for an
entire session's worth of corrections in August 2026 (see PROJECT-STATUS.md).
The vision-verification stage (the only one that costs API calls) is safe to
re-run every time — see the next section.

`./rebuild_all.sh --skip-vision` skips only the Gemini re-verification step,
for fast iteration when you don't need fresh flag classifications yet.

### The vision-adjudication cache must be keyed on the full comparison, not just the crop

`adjudication_cache.db` caches Gemini's decision for "does this crop show
reading A or reading B" so repeat runs don't re-spend API calls. **The cache
key must include which two readings were being compared (crop_hash + word_a
+ word_b), not the crop image alone.** A crop-hash-only cache is a real bug,
not a hardening opportunity: the same bbox gets re-cropped across sessions to
answer different comparisons as `clean_text` changes (a fix, then later a
revert), and a crop-only cache silently returns a stale decision for the
*current* comparison — confirmed 2026-08-05, see PROJECT-STATUS.md: this
collapsed 217 real word-pair decisions onto 140 unique crops, meaning 77 had
already been silently overwritten by an unrelated comparison before anyone
noticed. `verify_corrections_vision.py`'s `corrections_cache` table does this
correctly; if you add another vision-caching script, key it the same way.

## Directory layout

- `orchestrator.py`, `chunker.py` — the two OCR/VLM-extraction pipeline
  scripts. `build_klalim_demo_dataset.py`, `build_corrections_dataset.py`,
  `verify_corrections_vision.py`, `assemble_corrections_dataset.py`,
  `build_klal_page_regions.py`, `build_review_html.py`, and `rebuild_all.sh`
  are the review-artifact pipeline (see "Single source of truth" above) —
  everything else at root is either an established data artifact or a
  historical one-off script.
- `archive/scripts/`, `archive/data/` — one-time, already-applied patch/find/
  debug scripts (hardcoded to specific klal numbers or line indices) and their
  throwaway text/JSON dumps, moved out of the root in Aug 2026 for
  discoverability. Safe to reference for *how* a past fix was done, not meant
  to be rerun as-is.
- `aligned_klalim/`, `klalim_batches/`, `processed_klalim/` — tracked,
  versioned pipeline output at various stages.
- `docai_word_boxes/`, `document_jsons_berlin/`, `klalim_docai/`,
  `llm_klal_starts/`, `sefaria_export/`, `vlm_extractions/`, `scratch/` —
  gitignored regenerable caches/intermediates. Don't assume these exist on a
  fresh clone; they're rebuilt by re-running the extraction scripts against
  the source scans.
- `.gemini/rules/` — Gemini CLI's equivalent of this file; this project has
  been worked on from both Claude Code and Gemini CLI, so check both when
  looking for standing directives.

## Open items

See `PROJECT-STATUS.md` — the detailed, dated log of open items, confirmed
bugs, fixes applied, and in-progress investigations lives there now, not
here, so it can be updated freely without this file's durable rules drifting
along with it. Read it before touching corpus quality, and update it (not
just append — correct superseded claims) whenever a finding changes.

## Conventions observed

- Corrections are driven by direct LLM adjudication with **rendered UI
  verification** (open the HTML demo, visually confirm), not blind text diffs
  — see `.gemini/rules/rabbinic_ocr_adjudication.md` / `robust_ocr_processing.md`.
- Every cleanup pass targets **zero flagged items** in `lexicon.txt` validation
  before being considered done (see commit history: "100% clean validation
  pass" is the recurring bar).

## Lessons learned — binding, not optional reading

These are rules, not history. For the specific incidents that produced them,
see `PROJECT-STATUS.md`. Do not delete a lesson because its incident got
fixed — the rule still applies to the next incident.

1. **A verification tool that exists but isn't run on everything it applies
   to has not verified anything.** Running it on a sample, or only on items
   a different/narrower check already flagged, is not the same as running it.
   If full coverage is too expensive, say so explicitly and get a scope
   decision — never quietly narrow coverage and report the narrower result as
   if it were complete.
2. **A passing score is not the same as a checked result.** A numeric
   agreement/confidence threshold is a triage tool for where to look first,
   not a certificate of correctness. A high score can still hide a single
   wrong word. Look at what a "passing" result actually contains before
   moving on, especially anywhere close to the threshold.
3. **Never trust a derived/aggregate artifact as ground truth, no matter how
   long it's been treated as authoritative.** Re-derive from primary sources
   (the scan image, raw OCR, a validated lexicon) rather than trusting
   anything built by an earlier, unaudited pipeline stage — including this
   project's own prior outputs.
4. **Raw/source-adjacent data is not automatically correct just because it's
   closer to the scan than derived data.** OCR extraction itself can have
   real bugs (mislabeled files, swapped pages, wrong content). Verify with
   the most direct method available — e.g. rendering the exact source region
   a claim is based on and reading it directly — not just by checking that
   matching content exists somewhere.
5. **Fuzzy/subsequence text matching is not precise enough for exact-position
   claims.** It tolerates small shifts and will report a high similarity
   score for content that's merely nearby, not exactly there. Fine for
   coarse attribution or cropping with margin; wrong for "is this the exact
   right token/position." For exact-position questions, anchor on an exact
   match first and use fuzzy similarity only to disambiguate among exact
   candidates.
6. **Every matching/anchoring strategy has its own blind spot — know it
   before trusting silence as proof of correctness.** Exact-match anchors
   can collide with short/common values that recur for unrelated reasons.
   Fuzzy matches can lock onto coincidentally-similar content elsewhere.
   Cursor/position-based search can cascade failures if one bad match
   corrupts the position everything after it searches from. Understand the
   specific failure mode of a check before trusting what it doesn't flag.
7. **Fixing one root cause does not mean the symptoms it produced are now
   explained.** Multiple independent bugs can produce similar-looking
   symptoms. After a fix, re-verify the original finding against corrected
   data before assuming it's resolved — don't assume one explanation covers
   every instance that looked the same.
8. **A cheap, mechanical, no-LLM check can catch what expensive LLM-based
   checks miss entirely, and vice versa — run every independent check you
   have, don't rely on the most sophisticated one alone.** Structural/
   consistency rules (format, sequence, grouping invariants) are nearly free
   and catch a different class of error than semantic or visual review.
9. **Independent verification signals must agree before a fix is trusted.**
   Pixel-reading (vision) and linguistic-plausibility (semantic) checks fail
   in different ways — a misread crop can look pixel-plausible but be
   meaningless, and vice versa. Require at least two independent signals to
   agree, not just one confident-sounding one.
10. **Prompts bias results in specific, predictable directions — watch for
    the bias itself, not just its symptoms.** E.g. asking for "the shortest
    valid answer" systematically produces truncation, which then shows up as
    many false "disagreements." Fix the instruction, don't just tune a
    threshold around its side effect.
11. **A locally clean fix can still be a symptom of a larger unresolved
    problem.** If a broader/structural check flagged something upstream,
    don't stop investigating just because the first specific instance you
    looked at resolved cleanly.
12. **A cache key must cover everything that changes the correct answer, not
    just the expensive part.** Keying a decision cache on the crop image
    alone (not also the two readings being compared) meant a stale decision
    from an earlier comparison got silently reused for a different, current
    comparison on the same crop — see "Single source of truth" above. If a
    cache can be asked two different questions about the same cached object,
    the cache key must include which question was asked.
13. **A hand-maintained "derived" file is not actually derived — it's a
    second copy of the truth that happens to usually agree.** Any file whose
    content is fully computable from another file (e.g. a concatenation, a
    join, a filter) should be built by a script and regenerated, never edited
    in parallel by hand "to save time." Parallel hand-edits agree until the
    day someone forgets one of the two places — the failure is silent, not
    loud, so you won't notice until something downstream looks stale.
14. **Judging word ORDER in a cropped RTL image is a distinct failure mode
    from misreading a letter, and needs its own safeguard.** A tight crop
    around a disputed word pair can clip the anchor word that establishes
    which side is "first," and reading right-to-left off a clipped image
    silently inverts the answer — confirmed 2026-08-05, klal 34's title
    (`אין דן אדם...` vs. the correct `אין אדם דן...`): a narrow crop was
    read as confirming the wrong order, and re-cropping the *same way* after
    being directly contradicted reproduced the same risk. Any crop meant to
    establish order (not just letter identity) must keep an unambiguous
    anchor (a bold opening word, a klal marker) fully inside the frame with
    visible margin — never crop so tight that a word touches the edge. When
    your reading and another source directly disagree, don't re-run the same
    method closer — cross-check with a differently-sourced signal (raw token
    x-coordinates, a fresh independently-prompted model read) per lesson 9,
    the same way the klal-1 `ומדקמהד` case was ultimately resolved.
15. **A comparison pipeline that requires aligning two OCR sources produces
    silence, not a low score, exactly where the source OCR is too garbled to
    align — and silence is not evidence of correctness there.** Confirmed
    2026-08-05: every Part-1 klal with a low/untrusted alignment
    `match_ratio` in `part1_header_anchored_alignment.json` (34, 92, 129,
    172, 180, 182, 187, 190, 194, 197, 210, 216, 217) has **zero** entries in
    `corrections_part1.json` — not a low-confidence flag, no candidate was
    ever generated, because `build_corrections_dataset.py` can't align
    unrecognizable docai tokens to stored text in the first place. This is a
    different blind spot than lesson 1 (coverage gap) — the tool nominally
    ran, but structurally cannot produce output on the cases that need
    checking most. Treat a low/untrusted alignment `match_ratio` as its own
    mandatory-manual-review flag, independent of whatever the
    corrections/vision pipeline shows for that klal.
16. **Checking only the boundary between two "trusted" neighbors cannot
    detect content merged inside one of them.** Confirmed 2026-08-06: a
    check of whether klal N's "trusted" stored text already reached the
    token immediately before klal N+2's marker found "zero gap" for
    klal 180, 182, and 194 and concluded no room existed for them — wrong
    in all three cases. Each was really sitting, whole, inside its
    "trusted" neighbor's own `clean_text`, appended after that neighbor's
    real ending, behind a garbled second marker the boundary check never
    looked for because it never read the neighbor's *full* text, only its
    edges. A "trusted" flag on a klal says its *boundaries* were
    validated, not that its *interior* was searched for a second klal
    hiding inside it. Before concluding a klal_id has no content anywhere,
    read the full stored text of both neighbors for an embedded second
    marker and topic shift — do not infer absence from edge-adjacency
    alone. The direct-visual-page-render check (Lesson 14) is the
    reliable method here too: rendering the physical boundary and reading
    it caught the three wrong conclusions and confirmed the six real
    gaps at equal confidence, where token-position inference gave a
    50/50 record.
17. **A token-height threshold for detecting catchwords is a useful
    first-pass filter, not a sufficient check on its own.** Confirmed
    2026-08-06: the height-based catchword check (used repeatedly the
    night of the klal 92-165 shift-zone work) correctly flagged most
    catchwords, but wrongly cleared one as normal body text (klal 128's
    page 47/48 boundary), producing a real duplicated word in the stored
    text (`לאוקומי לאוקומי`) that stood until a corpus-wide
    duplicate-word sweep caught it. A direct render of the actual page
    showed the word sitting alone on its own short centered line - the
    standard catchword position - contradicting the height measurement.
    On any page-crossing reconstruction, treat a borderline or
    unexpected height reading as a reason to render and look, not as
    settled by the number alone.
18. **A cheap, corpus-wide text-pattern sweep (grep a literal string, a
    regex, a duplicate-word scan) can find in minutes what extensive
    klal-by-klal manual review missed for an entire project's history.**
    Confirmed 2026-08-06: a plain string search for the page-running-header
    text found contamination in 74 Part 2-3 klalim (17%) and one missed
    Part 1 instance, none of which any prior manual pass or automated
    check had caught, because no such sweep had ever been run as a
    matter of course - only individual klalim got checked, one at a
    time, when something else drew attention to them. Run this class of
    check routinely (after any batch of edits, not just when asked) -
    per Lesson 8, it catches a different class of error than
    vision/semantic review and costs almost nothing to run.
19. **Diagnosing a fix and describing it in writing is not the same as
    applying it — verify every "fixed"/"split"/"applied" claim against a
    diff of the actual data, not against how carefully it was written
    up.** Confirmed 2026-08-06: this document stated klal 181/182 had
    been "split, the identical shape as 179/180" — the diagnosis was
    correct but the code to apply it was never run, and the file sat
    byte-identical to its pre-fix state for the rest of the session
    despite being narrated as done. Found only because a later request
    to diff the whole session against its starting commit surfaced it.
    This is Lesson 1 ("a check that isn't run has not verified
    anything") applied to one's own output: a prose claim of "fixed" is
    itself unverified until checked against a real before/after diff.
