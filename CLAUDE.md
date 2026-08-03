# Yad Malachi Pipeline

Digitization pipeline for **Yad Malachi** (R. Malachi ben Jacob HaKohen, Livorno
1766–7), a foundational halachic-methodology reference with 667 *klalim* across
three parts. Goal: a clean, structured digital text for Sefaria — see
`CASE-YAD-MALACHI.md` for the full rationale (287 dead Sefaria citations point to
this work today).

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

## Directory layout

- `orchestrator.py`, `chunker.py` — the only two files marked as live pipeline
  code; everything else at root is either an established data artifact (see
  above) or a historical one-off script.
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

- **Rigorous (vision-confidence-scored) review currently covers Part 1 only**
  — see the `aligned_klalim`/header-anchored-alignment item below for what
  "Part 1 coverage" actually means now (klal 1–222 attempted, 208 trusted).
  Parts 2 and 3 have no linked scan images or word bounding boxes yet, so no
  vision-adjudicated confidence scores exist for them at all — corrections
  there are unverified against the source scan until that data is built out.
- The review UI (`review.html`, renamed from `SEFARIA-BERLIN-DEMO.html`) is a
  work in progress: 3-pane layout (scan-highlight left / full text middle /
  abridged klal nav right), with per-word corrections + confidence surfaced
  for human review.
- The many pre-existing tracked one-off scripts at root
  (`fix_1_line_offset_and_rebuild.py`, `fix_klal_74_stitching.py`,
  `build_full_pristine_667.py`, etc.) follow the same disposable-patch pattern
  as what got moved into `archive/` — they predate that cleanup and weren't
  touched, since reorganizing already-tracked history is a bigger call than
  tidying untracked files.
- **The abridged `title` field must be judged, not algorithmically derived.**
  The source print doesn't reliably punctuate where a title ends and
  explanatory text begins (e.g. klal 5's title is the single word `איתמר` —
  no word-count or punctuation rule can know that). Titles for all 222 Part 1
  klalim were manually read and judged (see `apply_judged_titles.py`) rather
  than generated by a formula; Parts 2–3 (klal 223–667) still need the same
  treatment — do not regenerate Part 1's titles algorithmically.
- **Editorial punctuation insertions are marked `[.]` in `clean_text`** (square
  brackets, the standard critical-edition convention), inserted only where the
  original print has no punctuation at the judged title/explanation boundary.
  This is scoped to that one boundary per klal, not a full re-punctuation of
  every sentence — a corpus-wide punctuation pass is a distinct, much larger
  task not yet undertaken (needs its own scoping: cost, whether to cover all
  667, and a review pass before treating inserted marks as final).
- **8 Part-1 klalim have no real text at all**, just a placeholder
  (`"קפ כלל 180"` etc.): klal **180, 182, 187, 190, 194, 197, 216, 217**.
  These need their actual content extracted/OCR'd from the scan — currently
  titled `(no text available)` as an honest placeholder, not fabricated.
- **Klal 186's `clean_text` is corrupted** (`לשבצא"בחלס":ב א:ע"ג` — not real
  words, likely an OCR garble) beyond the "1 word title" workaround applied
  here (`title` = `הלכה`, the only safely-identifiable word). Needs a real
  fix against the scan, not just a title-side patch.
- Fixed in passing: klal 92's `clean_text` had a duplicated OCR fragment
  (`"המק המקובל"` → `"המקובל"`), corrected across all base files.
- **The book's front matter (title page, haskama, hakdama) is real, substantial
  content and still needs to be transcribed and included in the eventual
  Sefaria delivery** — it is NOT part of the 667 klalim and isn't covered by
  any pipeline stage yet. `berlin_square.pdf` pages 1–13 (before klal 1 begins
  on page 14) contain: p.3 a National Library of Israel catalog page (names
  author/title), p.4 a handwritten ownership/provenance inscription, p.6 the
  printed title page (`ספר יד מלאכי חלק ראשון`, publisher/place/date), p.7 a
  haskama (rabbinic approbation) by ישכר אבולעפיא, and p.8–9+ the הקדמה
  (introduction) signed by אליהו בכ"ר משה הכהן. Pages 1, 2, 5 are genuinely
  blank/non-text (scan boilerplate, binding material). Real DocAI OCR for
  pages 1–12 was extracted for the first time in this session (previously
  `docai_word_boxes/page_1.json`–`page_12.json` were a duplicate-data bug, see
  below) but none of it has been transcribed into `clean_text` or any
  structured output — this is a distinct, unscoped piece of work, not covered
  by "667 klalim" success criteria as currently framed.
- **`docai_word_boxes/page_1.json`–`page_12.json` were byte-identical
  duplicates of `page_13.json`–`page_24.json`** (a systematic off-by-12 bug in
  whatever batch OCR run originally produced pages 1–61) — discovered and
  fixed this session by deleting and re-extracting pages 1–12 with
  `extend_docai_ocr.py`'s synchronous per-page method. `header_anchored_alignment.py`
  excludes/ignores this range for klal-text alignment purposes (front matter,
  not klalim), but any future front-matter transcription work should use the
  now-correct pages 1–12, not assume they're still bad.
- **`aligned_klalim`'s page-to-klal mapping is discredited — do not trust it.**
  First-principles re-verification (`header_anchored_alignment.py`, which
  cross-checks each klal's text against its page's own printed section header,
  independent of `aligned_klalim`) found the mapping was wrong; the previous
  session's belief that vision-verified coverage was klal 1–222 turned out to
  itself be based on this flawed mapping. Real coverage, re-derived from
  scratch: `part1_header_anchored_alignment.json` now has a trusted
  page-attribution for 208/222 Part-1 klalim (the other 14: the 8 known
  placeholder klalim, klal 186's known corruption, and 5 more low-text-
  similarity flags — klal 34, 92, 129, 172, 210 — worth a closer look).
  `docai_word_boxes` page coverage was extended from page 61 to page 82 to
  make this possible. `build_corrections_dataset.py` and `review.html` were
  updated to use this new mapping; `corrections_candidates_part1.json` was
  regenerated (791 candidates across 177 klalim, up from 20) but only a
  90-item sample has been vision-verified so far — the rest still needs it.
- **Klal 65 fixed**: `clean_text`/`title` had `ב"ר` where the scan and the
  well-known Talmudic source (Mishnah Eduyot 1:5, `אין בית דין יכול לבטל דברי
  בית דין חבירו`) both confirm `ב"ד` — a ד/ר OCR confusion (the single most
  common OCR error pattern in this corpus). Confirmed independently by both
  vision (image crop) and a text-only semantic-plausibility check
  (`verify_semantic_sanity.py` / `run_semantic_sanity_pass.py`) before fixing.
  That semantic-sanity pass is a new, general second layer over any
  vision-flagged disagreement — pixel-reading and linguistic-plausibility are
  independent signals that catch different failure modes, and both should
  agree before a fix is trusted.
- `full_text_cleaned.txt` / `full_text_cleaned_goal.txt` / `processed_klalim/`
  were archived to `archive/data/` this session — confirmed (cheap text diff,
  not vision) to be stale, superseded snapshots with zero unique content
  versus current `part1/2/3.json`, not additional sources of truth.
- **Klal 21, 218, 219 fixed** (same ד/ר, ם/ס, ו/י OCR-confusion pattern as
  klal 65): `עודו`→`עורו` (21), `שגס`→`שגם` (218), `האו`→`האי` (219). Each
  confirmed via the semantic-sanity pass AND checked against
  `gematria_trace_part1.json` to confirm they sit outside the klal 92–160+
  shift zone before touching them — see next item. Two more candidates from
  the same batch were deliberately NOT applied: klal 144 (`הדואה`→`הרואה`,
  high confidence) sits in a spot the gematria trace couldn't confirm either
  way, and klal 85's flagged "missing `פו`" is not a word-level fix at all —
  the model's own reasoning shows `פו` marks the start of klal **86**,
  meaning klal 85 and 86 are currently merged into one entry. That's a
  klal-boundary problem (success criterion #2), not a text correction; fixing
  it means splitting the klal, not inserting a word. Left for the structural
  pass below.
- **Structural klal-boundary/content-shift issue, confirmed but NOT fixed**:
  first-principles gematria-marker tracing (`trace_gematria_sequence.py` →
  `gematria_trace_part1.json`) found real, independently-confirmed content
  misalignment spanning roughly **klal 92–160+** (manually verified via raw
  OCR tokens for 94/95, 98/99, 102–106 specifically — our stored klal 99 is
  actually gematria צח=98's content, etc.). The klal 102–106/108/119/210
  title-letter violations found by `validate_title_section_letter.py` are a
  symptom of this, not a standalone title-wording issue — do NOT fix them by
  just editing the `title` field; the underlying `clean_text`/klal boundaries
  need re-deriving against the scan first. Klal 85/86 (see above) may be an
  additional, separate merge issue nearby. This needs its own scoped
  investigation, not a quick patch — see the trace tool's own limitations
  under Lessons Learned before extending it (short gematria markers collide
  with ordinary citation numerals; a "not found" result there is not proof of
  a problem, and a "found" result there is not proof of correctness either).

## Conventions observed

- Corrections are driven by direct LLM adjudication with **rendered UI
  verification** (open the HTML demo, visually confirm), not blind text diffs
  — see `.gemini/rules/rabbinic_ocr_adjudication.md` / `robust_ocr_processing.md`.
- Every cleanup pass targets **zero flagged items** in `lexicon.txt` validation
  before being considered done (see commit history: "100% clean validation
  pass" is the recurring bar).

## Lessons learned (methodology, not just facts — apply these going forward)

- **Never trust a derived/aggregate artifact as ground truth, no matter how
  established it looks.** `aligned_klalim` had been treated as authoritative
  for the project's whole history; it was wrong. `full_text_cleaned.txt` and
  `processed_klalim/` looked like additional sources of truth; they were
  stale snapshots nobody had re-derived in weeks. When in doubt, re-derive
  from the two/three real sources only: the scan image, raw DocAI OCR, and
  `lexicon.txt` — never from something itself built by an earlier, unaudited
  pipeline stage.
- **`difflib.SequenceMatcher.ratio()` is not precise enough for exact-position
  checks.** It matches subsequences, not exact position, so it tolerates a
  ±1-token shift and will still report a high ratio. Fine for cropping (with
  a margin) or coarse page attribution; wrong for "is this exact token X."
  For exact-position questions (e.g. "is the printed marker right here"),
  anchor on an exact token match first, and use fuzzy content similarity only
  to confirm/disambiguate among exact-match candidates — not the other way
  around.
- **Exact-token anchoring has its own blind spot: short gematria markers
  collide with ordinary citation numerals.** Single/double-letter values
  (roughly klal 1–90) are also constantly used as ordinary chapter/halacha/
  folio citation numbers throughout the running text (`בפרק ג'`, `הלכה ג`,
  `דף ג'`), so exact-match search for a bare `ג` finds many false positives.
  Longer, more distinctive multi-letter markers (90+) don't have this
  problem. Any future gematria-anchored check needs a different strategy for
  low values (e.g. requiring specific preceding punctuation, or falling back
  to the neighbor-content-window method) rather than trusting exact match
  alone.
- **A "cursor only advances forward" search is fragile if the window is a
  narrow, fixed span ahead of the cursor.** If one item's search fails, the
  cursor doesn't move, and the next item inherits an increasingly stale
  cursor with a fixed-size window — a few consecutive failures can cascade
  into everything downstream falsely failing too. Prefer either a generous/
  staged widening window, or (once anchoring on something exact and rare
  enough that false positives are unlikely) searching the whole page and
  using the cursor only as a tie-breaker among candidates, not a hard bound.
- **LLM prompts that ask for "the shortest span that could stand alone" bias
  the model toward truncating** — about half of `verify_titles_vision.py`'s
  first-run "disagreements" were this artifact, not real errors, and it
  actively caused a wrong correction to be nearly made (klal 104/105, where
  the "shortest" reading strips exactly the clause that distinguishes a klal
  from its immediate neighbors in a themed run of related sub-rules). Ask for
  a heading that stays distinguishable from neighboring entries, not the
  shortest self-contained one.
- **Vision (pixel-reading) and text-only semantic-plausibility checks catch
  different failure modes — run both and require agreement before trusting a
  fix.** A crop can be misread as something that "looks pixel-plausible" but
  makes no linguistic sense, or a genuinely correct reading can look
  suspicious out of context. Klal 65's `ב"ר`→`ב"ד` fix (a ד/ר OCR confusion,
  the single most common error pattern in this corpus) was only trusted once
  both signals agreed independently.
- **A cheap, mechanical, no-LLM structural rule can catch what both vision
  and semantic checks miss.** Titles are grouped by section, and every
  section is itself a first-letter grouping (א for כללי האלף, ב for כללי
  הבית, etc.) — a title that doesn't start with its section's letter is a
  hard, free red flag. This caught real errors (klal 102–106, 119, in
  addition to 108 and 210 already flagged other ways) that neither the vision
  nor the semantic pass had surfaced. See `validate_title_section_letter.py`
  — run this any time titles change, same bar as lexicon validation: zero
  flagged items.
- **When several consecutive klalim share near-identical opening phrasing
  (a common print pattern — closely related sub-rules distinguished only by
  a trailing clause), per-klal verification MUST use a running position
  cursor across the page, or it will bleed across klal boundaries** — confirmed
  concretely: klal 66's vision-read "title" was verbatim klal 67's real
  title, because the crop locator had no memory of where the previous klal
  on the same page was found and locked onto the wrong occurrence of very
  similar text.
- **A locally "confirmed" fix can still be a symptom of something bigger.**
  The klal 102–105 "missing `ב"ד` prefix" pattern looked like a self-contained
  title-wording question; pulling the actual scan crop revealed it's a
  symptom of a much larger, still only partially-mapped content/numbering
  misalignment spanning roughly klal 92–160+ (see `gematria_trace_part1.json`,
  produced by `trace_gematria_sequence.py`) — not yet fixed, needs its own
  scoped pass. Don't stop investigating at the first artifact that resolves
  cleanly if a structural check (like the letter rule above) suggests
  something upstream is still off.
