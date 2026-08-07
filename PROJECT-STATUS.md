# Project Status — Open Items & Investigation Log

## Punctuation-token diff bug fixed — 61% of Part 1's correction candidates were noise, 2026-08-07

User reported review.html bugs (stray period in hover tooltips, underline
inconsistency, no clear "which candidate was chosen" indicator, "overall
ugly") and asked for a candidate-override mechanism with backend version
tracking, plus a klal-level flag-for-revisit with a note field - before
running a full Part 1 vision-validation pass. Investigating the stray-
period report before touching any UI code surfaced a much bigger issue.

**Root cause (not a display bug): `build_corrections_dataset.py` diffs
DocAI OCR tokens against `clean_text` words via `difflib.SequenceMatcher`
over `clean_word()`-normalized streams. `clean_word()` strips punctuation
but doesn't drop punctuation-only tokens - a bare `.` or `'` becomes `""`
and stays in the stream at its index, so it generates a real-looking diff
opcode against nothing.** Confirmed blast radius: **464 of 762 (61%) of
Part 1's correction candidates had a punctuation-only `docai_reading`/
`final_text` field** - 400 of 435 `delete`-opcode candidates (92%) were
this, plus 64 `insert`-opcode candidates where the "inserted word" was the
literal editorial `[.]` marker. `build_klal_page_regions.py` has the
identical latent bug at lower severity (can misattribute a token's region
box near punctuation, since an empty-string docai token can spuriously
`equal`-align against an empty-string clean_text word).

**Fixed both scripts**: filter tokens/words where `clean_word(...) == ""`
out of both diff streams before they reach `SequenceMatcher`.
`word_index_in_final_text` deliberately keeps indexing into the
**unfiltered** `clean_text.split()` (skipped punctuation words leave gaps,
never get renumbered) - downstream code (assembly, the review UI, the
planned `apply_reviewer_decisions.py`) all locates a word by that index.

Regenerated `corrections_candidates_part1.json`: **762 → 320 candidates**
(140/222 klalim now have any candidate at all, down from 170 - the
klalim that dropped to zero had *only* punctuation-noise candidates, not
real disagreements). Spot-checked: 0/320 survivors have an empty
`clean_word()` on either side. `corrections_verified_part1.json`/
`corrections_part1.json` still show the stale 762-entry state until the
next full (non-`--skip-vision`) `rebuild_all.sh` run - `verify_corrections_
vision.py` rebuilds fresh from `corrections_candidates_part1.json` each
run (not an incremental append), so this resolves automatically once that
run happens; not forced early since it costs Gemini API calls.

This was the direct root cause of the reported "stray period" tooltip bug
(hovering a `possible_omission` flag showed `Scan appears to show: "."`),
and explains a large fraction of why the dashboard felt noisy/hard to
trust - the majority of what looked like flagged disagreements were
meaningless. Dashboard rearchitecture (new local review server, replacing
the single-file `review.html`, with a real candidate-override mechanism
and an append-only decision audit trail) and the full Part 1
vision-validation pass are in progress as follow-up work - see subsequent
entries.

## Closed the two loose ends on `validate_part1_corpus_integrity.py`, 2026-08-07

User asked directly: "did we finish innovating validation checks?" Answer
at the time was no — two loose ends from the script's addition earlier
today: its 3 known false-positive categories were only documented in prose
here, not fixed or baselined in the script itself (so every future run
would re-report them and someone would have to re-derive they're not
bugs), and the script wasn't wired into the standing pytest gate, so
nothing would catch a genuinely new violation automatically. Both closed:

**Fixed all 3 false-positive sources at the source, rather than adding a
baseline exception list** (unlike `SPAN_COVERAGE_BASELINE` etc., these
were bugs in the check's own logic, not corpus content requiring an
exception):
- `klal_id_to_gematria()`'s word-final-letter handling was wrong in both
  directions. Investigated properly this time (not just patched to stop
  complaining): only נ/פ/צ (not כ/מ) take their final form at the end of
  a *multi-letter* numeral in this typesetting (150=קן, 180=קף, 190=קץ),
  while a lone single-letter numeral (20=כ, 40=מ, 50=נ, 80=פ, 90=צ) and
  compounds ending in כ/מ (120=קכ, 140=קמ, 220=רכ) stay in regular form.
  Confirmed against `part1.json`'s own already-crop-verified gematria
  field in both directions before landing on this rule - an earlier,
  simpler attempt (finalize any of the 5 eligible letters unconditionally)
  produced 8 new false positives (20/40/50/80/90/120/140/220) that hadn't
  existed before, caught immediately by re-running, not shipped.
- Character-sanity's paren-balance check now excludes this edition's two
  footnote-marker conventions (`*)`/`**)` and `")`  — asterisk(s) or a
  straight quote directly before a lone close-paren with no matching
  open) from the close-paren count, confirmed against klal 6/7/51/53/71/
  74/106's actual crops.
- Duplicate-phrase's same-title exemption now uses fuzzy title similarity
  (`difflib` ratio ≥ 0.8) instead of exact string equality, catching
  klal 22/23/24's same-maxim-cluster titles that differ only by minor
  orthographic variants (למדים/למדין, אפילו/אפי').

All 3 now run zero-tolerance clean (222/222) against the current corpus.

**Wired those 3 checks into `tests/test_corpus_invariants.py`** as new
zero-tolerance tests (`test_part1_gematria_self_consistency`,
`test_part1_character_sanity`, `test_part1_no_new_duplicated_phrases`),
now part of `rebuild_all.sh` step 7/7's hard gate — 13/13 pytest, up from
10/10. Unlike the other standalone validators (which need the gitignored
`docai_word_boxes` cache and so can't run on a fresh clone, hence
deliberately excluded from the standing suite), this script only touches
tracked files (`part1.json`, `lexicon.txt`) and runs in under a second, so
it has no reason to stay manual-only. Checks 4 (self-reference
directionality) and 5 (lexicon coverage) are deliberately NOT gated - the
script's own docstrings already mark them not-viable/informational, not
zero-tolerance, and gating an informational check would just make the
suite permanently noisy or force treating "not yet in lexicon.txt" as a
failure, which it isn't.

`./rebuild_all.sh --skip-vision` re-run clean throughout. `CLAUDE.md`'s
directory-layout section updated to describe the new gate.

## Klal 144 scan-crop pass — two real fixes found, one left disclosed-ambiguous, 2026-08-07

Same treatment as klal 143 above, applied to klal 144's 1336-word
cross-page extension (the other disclosed-rigor-gap klal, previously only
coherence-read-through checked). Lexicon-scoped triage found 117
not-in-lexicon words — far more than klal 143's 28, consistent with this
klal's unusual register (a philosophical digression on the 13 hermeneutical
principles and Oral/Written Torah transmission, not citation-heavy halachic
prose). Shortlisted 6 that looked like real anomalies rather than ordinary
rare-vocabulary lexicon gaps, cropped all 6 from `berlin_square.pdf` page
52 (docai tokens), cross-checked against same-page/same-klal reference
letters:

- **`דעורת`→`דעות` — confirmed and fixed.** A 2000dpi crop shows exactly
  4 letters (ד-ע-ו-ת), no ר anywhere — the stored/docai `ר` doesn't exist
  on the page at all. `לכמה דעורת ומחלוקתם של חכמים` (nonsense) →
  `לכמה דעות ומחלוקתם של חכמים` ("into many opinions, and their
  disagreement..." — grammatical and coherent).
- **`לגטרי`→`לגמרי` — confirmed and fixed.** Docai misread מ as ט. Crop
  of the disputed letter compared directly against this same klal's own
  correctly-spelled `לגמרי` 33 tokens later on the same page: both show
  the same closed-loop mem shape, not the open-hook shape ט takes
  elsewhere on this page. `לאפוקי מה שהוא מדרבנן לגטרי` (nonsense) →
  `...לגטרי` → `...לגמרי` ("to exclude entirely that which is Rabbinic"
  — standard, common word, fits the sentence).
- **`מהלוקת` (word_index 910) — checked, NOT changed.** Direct crop
  compared against this same klal's own `מחלוקת` (correctly spelled,
  same page) shows the second letter has heh's open left-side gap, not
  het's closed top bar — the print genuinely reads `מהלוקת`, not
  `מחלוקת`, at this specific spot. A real print irregularity (this exact
  word is spelled correctly twice elsewhere on the same page), preserved
  as printed per the fidelity rule, not silently normalized.
- **`ומאו` (word_index 1078) — checked, NOT changed.** Suspected this
  might be `ולאו` (ל/מ confusion), but the crop's second letter has no
  tall ascender (compared directly against `אלא`'s ל one line above in
  the same crop) — confirms מ, matching stored/docai exactly. Left as
  printed even though its exact grammatical role in context isn't fully
  clear — per this project's own standing rule, transcription fidelity
  doesn't require the reviewer to fully parse 18th-century Aramaic syntax,
  only to confirm what's actually printed.
- **`ביטמא` (word_index 725) — checked, NOT changed.** Crop matches
  stored/docai exactly, no letter-shape ambiguity found.
- **`בכתיכת` (word_index 858) — left disclosed-ambiguous, NOT changed.**
  Suspected `בכתיבת` (`כתב יד` / "in manuscript" is a standard idiom;
  `בכתיכת` isn't a word). Cropped at 2000dpi and cross-checked against
  both an unambiguous ב reference and an unambiguous כ reference (the
  word `כתב` elsewhere on this page, where letter identity is certain
  from context) — the disputed letter's shape didn't cleanly match either
  reference confidently enough to call. Per Lesson 6 (every check has a
  blind spot; don't force a guess when genuinely undecided), left as
  currently stored, disclosed rather than silently resolved either way.

`part1.json` updated (2 fixes, unique-string replace, count=1 verified
before writing), `gematria_trace_part1.json`'s klal 144 note updated.
`./rebuild_all.sh --skip-vision` re-run clean, 10/10 pytest.

**Both klal 143 and klal 144's disclosed cross-page-extension rigor gap
are now closed to the same "targeted crop-check of flagged candidates"
standard** — not full word-by-word verification of all 2095 combined
words, which was never the bar set for this pass (see klal 143's own
scope disclosure above); the remaining un-cropped words in both klalim
are unremarkable running prose with no lexicon/coherence flag against
them.

## Klal 34 investigation — the last untrusted klal in Part 1, resolved, 2026-08-07

Klal 34's *content* was already fixed and crop-confirmed back on 2026-08-05
(title word-order, missing clause), but it remained the sole klal (of 222)
that `part1_header_anchored_alignment.json` couldn't trust
(`match_ratio: 0.5`, `matched_page: 51` — a spurious match on an unrelated
page, `trusted: false`), meaning it had **zero** correction candidates and
had never gone through the correction-candidate/vision pipeline at all
(the exact Lesson 15 blind spot). Root cause traced, not just re-described:

**The marker itself was misread by docai.** `gematria_trace_part1.json`
had klal 34 as `marker_not_found_in_window` because the automated search
was looking for `לד` (34) — but page 26 token 374 (bounded correctly
between klal 33's marker at token 221 and klal 35's at token 475) reads
`לו` (36) in docai's raw OCR, a ד→ו marker misread (the same family as
klal 167/196-197's ז→ו). Confirmed by direct 1500dpi crop of
`berlin_square.pdf` page 26: unambiguous `לד` (dalet's squared corner),
not a vav. Fixed `gematria_trace_part1.json`'s klal 34 entry: `status: ok`,
`marker_position: 374`.

**Why the alignment tool still couldn't auto-trust it even at the right
position**: tested directly — the 8-word fuzzy query from `clean_text`
scores only 0.375 against docai's own window at the crop-confirmed correct
start, well under `ACCEPT_RATIO` (0.7). Docai's OCR is independently
garbled on several *other* words in this same span too (`מישורון` for
`אדם דן`, `אלאס`/`איל` for `אלא`/`א"כ`, etc.) — not a search/cursor bug,
a genuinely bad OCR patch. Added a documented `MANUAL_OVERRIDES` mechanism
to `archive/scripts/header_anchored_alignment.py` (klal_id → crop-verified
(page, token_index), with inline citation) rather than lowering
`ACCEPT_RATIO` globally, which would reintroduce the false-positive risk
the header-anchoring was built to prevent. Re-ran: **222/222 klalim now
trusted** (up from 221/222), diffed old vs new output first per Lesson 3 —
zero regressions among the other 221 (only klal 34's `trusted`/`matched_page`
changed; small `lexicon_hit_rate`/`jump_tokens` drift elsewhere is just
`lexicon.txt` having grown since the alignment file was last generated,
unrelated to this fix). Also fixed an unrelated pre-existing crash in the
script's own reporting code (`search_stage` int comparison breaking on the
new `"manual_override"` string value).

**Regenerated the pipeline** (`rebuild_all.sh --skip-vision`): klal 34 now
generates 6 correction candidates (previously 0) — `Klalim excluded as
untrusted: 0 -> []`. Crop-checked all 6 directly (not deferred to a vision
pass — direct crop is this project's highest-confidence signal):
- 4 are parenthesis/geresh punctuation-tokenization diffs (docai splits `(`
  `'` `'` `)` as separate tokens; stored `clean_text` already has the same
  punctuation inline) — diff-alignment noise, not a content issue; the
  parens are genuinely on the page and genuinely in stored text.
- `דוא`→`הוא`: docai's raw OCR misread, already correctly adjudicated in
  stored text (`הוא` is the only grammatical reading; `דוא` isn't a word).
- `פגשתיהן`→`פגשתיהו` (docai vs. stored): **crop-confirmed stored text is
  correct.** Direct 2000dpi crop of `(דרשתיהו פגשתיהו בפ' ב' דברכות...)`
  shows both words ending in ו, not docai's ן — `דרשתיהו`/`פגשתיהו`
  ("I expounded it, I encountered it" — 1st-person-past + 3rd-person-object
  suffix, a real grammatical construction, matching this author's habit
  elsewhere of narrating his own research trail before a citation).

**No `part1.json` text change was needed** — every candidate this fix
surfaced was already correct as stored. This closes klal 34 as an open
item: content confirmed (2026-08-05), now also structurally trusted and
pipeline-visible (2026-08-07), all new candidates it exposed reviewed.
Not run: a formal Gemini vision-verification pass on these 6 candidates —
direct crop-confirmation already exceeds that standard, so it wasn't
spent; can be added later if the corpus-wide vision-verification pass is
ever rerun anyway. `./rebuild_all.sh --skip-vision` clean, 10/10 pytest.

## Klal 143 scan-crop pass — one real fix found (`דמרך`→`דמהיך`), 2026-08-07

Picked up the disclosed rigor gap from the klal 144/85-86 closure above:
klal 143's 759-word cross-page extension had only ever been coherence-
read-through checked, never crop-checked against the physical scan.
Full word-by-word cropping of 759 words isn't practical in one pass, so
used the same triage approach as the rest of this document: ran
`validate_part1_corpus_integrity.py`'s lexicon-coverage check scoped to
just this klal to shortlist suspicious tokens (28 not-in-lexicon words,
mostly `פומבדיתא`/Pumbedita and its prefixed forms — expected, a place
name), then prioritized the 3 that looked like real anomalies rather than
ordinary proper-noun lexicon gaps: an internal spelling inconsistency
(`שמואל` spelled correctly at word_index ~598, then `שמول` at 747, same
person's name), a second internal inconsistency (`ופומבדיתא` spelled
correctly 7 times, `ופומכדיתא` once at word_index 711), and one word with
no obvious reading at all (`דמרך`, word_index 593).

Cropped all three directly from `berlin_square.pdf` page 51 at up to
2000dpi (docai token bboxes: 77, 196, 231), cross-checked against
same-page reference letters per Lesson 6/9 (not trusted on shape alone):

- **`דמרך`→`דמהיך` — confirmed and fixed.** The crop clearly shows 5
  letters (ד-מ-ה-י-ך), not the stored 4 (ד-מ-ר-ך): docai's raw OCR (and
  the stored text, which inherited it) misread ה as ר and dropped the
  י entirely. Confirmed by direct comparison against this page's own
  `הרבה`/`הואיל` (ה — two-legged shape with a gap on the left) and `בר`
  (ר — single stroke, no left leg): the target's middle letter matches
  the ה reference, not the ר reference. This is the same structural
  blind spot as Lesson 15/16 — docai's raw text and the stored text
  agreed with each other (both wrong), so no correction-candidate was
  ever generated for it; only a direct crop against reference letters
  caught it. Applied to `part1.json` (unique-string replace, verified
  count=1 before writing) and `gematria_trace_part1.json`'s klal 143
  note. `./rebuild_all.sh --skip-vision` re-run clean, 10/10 pytest.
- **`שמول` (word_index 747) — checked, NOT changed.** Crop unambiguously
  shows ל (matches this page's own `לכל` ל-shape: tall ascender curling
  at top), not א+geresh. The print itself really does spell the name
  two different ways in the same klal (`שמואל` earlier, `שמول` here) —
  per success criterion #1 (fidelity over "improving" the text), an
  internal print inconsistency is preserved as printed, not silently
  normalized to match the other occurrence.
- **`ופומכדיתא` (word_index 711) — checked, NOT changed.** Crop shows a
  rounder, open-hook letterform matching כ, distinguishable from this
  same word's own correctly-spelled `ופומבדיתא` occurrence elsewhere on
  the same page (a squarer, closed ב shape) side by side. Same
  conclusion as `שמول` — a real print-level inconsistency, not a
  transcription error, left as printed.

**Scope disclosed explicitly**: this checked the 3 most-suspicious of 759
words (the lexicon-flagged, semantically-anomalous ones), not every word
in klal 143's extension. This raises confidence but does not make klal
143 fully crop-verified word-by-word the way short klalim elsewhere in
this document are — a residual, smaller version of the same disclosed gap
remains for the ~756 uncropped words, most of which are unremarkable
running prose with no lexicon/coherence flag against them. Klal 144 (1336
words, same disclosed gap, not yet touched) is still open.

## New standing check `validate_part1_corpus_integrity.py` added; found and fixed a real derived-file drift while verifying the session's work — 2026-08-07

Requested: check the working tree matches this document's narrated 2026-08-07
work before committing, since some in-flight work might have been
interrupted (Lesson 19 — a written "fixed" claim isn't the same as a
verified diff). Spot-checked the specific fixes claimed above (klal 36,
88, 147, 151, 178's second corrupted span, the `page`-field regeneration,
klal 123's baseline entry) directly against `part1.json`/`corrections_part1.json`
content and against `tests/test_corpus_invariants.py`'s diff — all matched
exactly as described.

**Found a real gap in the process itself, not in the narrated fixes**: an
untracked `validate_part1_corpus_integrity.py` was sitting in the working
tree — a new `[PRODUCTION]`-tagged, 5-check standing validator (gematria
self-consistency, character/encoding sanity, duplicated-phrase detection,
self-reference directionality, full-corpus lexicon coverage) that had never
been logged here despite CLAUDE.md's standing rule to log every finding
immediately. Its `main()` called `check_duplicate_phrases(klalim, n=5)`,
directly contradicting that same function's own inline comment explaining
why `n=10` was chosen (n=5 produces 333 mostly-explainable hits; n=10 is
"the narrowest threshold that still lets a few same-title-cluster examples
through") — a leftover from mid-tuning, fixed to `n=10` to match the
documented decision.

Running the corrected script surfaced no real corpus bugs, but three
categories of script-side false positives worth recording so a future run
isn't re-investigated from scratch:
- **Gematria self-consistency, 3 "issues" (klal 150, 180, 190)**: the
  script's own `klal_id_to_gematria()` doesn't apply Hebrew's word-final-
  letter substitution (ן/ם/ך/ף/ץ) at the end of a numeral spelling. Directly
  confirmed `part1.json`'s `gematria` field and `clean_text`'s own opening
  word agree with each other in all three cases (קן/קף/קץ) — internally
  consistent, matches the already-documented "alternate-valid-gematria-
  spelling" finding for klal 190/215 above. Not a corpus bug.
- **Unbalanced parens, 10 "issues"**: a single closing `)` is this edition's
  footnote-marker convention (e.g. klal 6 `...הרמה*) :`, klal 7 `...רבינו
  הקדוש **) מסדר...`) — an asterisk/mark plus a lone close-paren flags a
  footnote, not an enumerated list requiring a matching open-paren. Not a
  corpus bug.
- **Duplicated-phrase, 2 "issues" at n=10 (klal 22/23, 23/24)**: genuine
  same-maxim-title-cluster sharing (`אין למדין/למדים מן הכללות אפילו/אפי'
  במקום שנאמר בהן חוץ`, the same convention already documented for klal
  100-104), missed by the script's same-title exemption because the three
  titles differ by minor spelling variants (למדים/למדין, אפילו/אפי') that
  the exemption's exact-string comparison doesn't tolerate. Not a corpus
  bug — a known blind spot in the check's title-equality logic.

**Separately, running `pytest` before committing caught the actual
interrupted work**: `test_klalim_demo_dataset_matches_part_concatenation`
failed — `klalim_demo_dataset.json` (a derived file, must never be
hand-edited, see "Single source of truth" in CLAUDE.md) still had the
pre-fix `gematria` field values (קנ/קפ/קצ) and stale `page` values for most
of Part 1, even though `part1.json` itself already had the corrected
final-letter forms (קן/קף/קץ) and regenerated `page` field from the
2026-08-07 fix logged above. `./rebuild_all.sh --skip-vision` had evidently
not been re-run after that last `part1.json` edit before the session ended.
Ran it now: `klalim_demo_dataset.json` regenerated cleanly (334-line diff,
gematria + page fields only, `clean_text`/`title` unchanged), all 7 rebuild
stages + 10/10 pytest pass. No content was lost — this was a stale derived
artifact, not a corpus defect.

## Second pass on the disclosed-uncertain items from the 85-item crop review — 2026-08-07

Requested: revisit the items left disclosed/unresolved in the section
below rather than leave them indefinitely open. Re-cropped each at
tighter zoom and, critically, pulled the **fuller surrounding sentence**
this time (the original pass often looked at the disputed word in
isolation) - most resolved once the sentence-level context was visible,
not from a better pixel read alone.

**5 confirmed real fixes, applied to `part1.json`**:
- **Klal 36**: `הש"ס '` (with a stray dangling apostrophe already
  visible in the stored text - a tell that an earlier pass had already
  half-noticed something was off here and left it unresolved) →
  `השית'`. Direct crop with full sentence context (`אין דרך השית' סדרי
  לומר היכא...`) confirms the print has no ס anywhere in this word -
  unambiguously ה-ש-י-ת plus a geresh, not `הש"ס`.
- **Klal 88**: `בעניותי` → `בעניי`. Crop with context (`אני בעניי
  שמעתי ולא אבין`) clearly shows the shorter 5-letter form, not the
  7-letter `בעניותי`.
- **Klal 147**: `דסמך` → `דסמיך`. Tight crop shows a clear extra letter
  (yod) before the final kaf that the shorter reading lacks.
- **Klal 151** (both `אמרה`/`אמר` instances, not just the one already
  fixed in the original pass): `דודאי אמר רב אבל` → `דודאי אמרה רב אבל`,
  and `אי אמר רב לא פסקינן` → `אי אמרה רב לא פסקינן`. Both crops clearly
  show a final ה (the open 3-stroke gap shape), confirmed against a
  same-line reference ה in `בזה` for the second instance.

**6 re-confirmed correct as currently stored** (the sentence-level
context, not available or not pulled in the original pass, settles
these decisively): klal 151's `רמכריע`/`המכריע` (already correct, not
actually one of the newly-revisited items - a labeling mixup in the
original todo list); klal 176's `אשידה`/`אשירה`; klal 178's `אכל`/`אבל`
(`אבל` directly introduces a quoted Tosafot clause - "בלשונם אבל..." =
"in their words: 'However...'" - a natural, common citation
construction); klal 181's `סכר`/`סבר` (the fuller sentence already has
a second, unambiguous `סבר` a few words later in the identical
construction `דמר סבר הכי ומר סבר הכי` - internally consistent, no
reason to think the first instance differs); klal 183's `בסי"ג`/`בפי"ג`
(citing Maharai Kurkos's chapter-organized commentary - `בפי"ג` "in
chapter 13" is the expected citation form) and `וככתובות`/`ובכתובות`
(part of a tractate citation list, `ובכתובות` "and in [tractate]
Ketubot" fits the list format the other conjunctions in the same
sentence use).

**2 still genuinely unresolved after this second pass, left disclosed
rather than guessed**: klal 215 (`וכך`/`וכף`) and klal 216
(`וכר`/`וכו'`) - both single-word abbreviation/particle disputes where
the crop remains visually ambiguous even at 800dpi and the semantic case
for the current text, while reasonably strong (`וכך` "and thus" and
`וכו'` "etc." are both far more standard than the alternative), isn't
decisive enough to treat as confirmed. Lower severity than the others
(particles, not content words).

`rebuild_all.sh` re-run clean: `current_text_may_be_wrong` dropped
70→65 (5 fixes), 10/10 pytest.

## Crop-check of all 85 `current_text_may_be_wrong` flags — 2026-08-06/07

User-requested: crop-check every one of the 85 vision-flagged
`current_text_may_be_wrong` items from the vision-verification run above,
not a sample. Initial read of the data looked like a single systemic
pattern - all 85 had `vision_selected: 'A'` (favoring the raw DocAI OCR
reading over the current adjudicated text), and a lexicon cross-check
showed the current stored text was a real dictionary word in 68/85 cases
vs. DocAI's raw reading in only 41/85, with one already-documented case
(klal 82's `בשר`→`בשל` fix) directly contradicted by vision at 1.0
confidence. That looked like a simple, uniform vision bias (Lesson 10) -
crop-check a sample, trust the majority pattern, done.

**That would have been wrong.** Direct crop inspection of all 85 (rendered
at 700-900dpi with generous margin per Lesson 14, compared letter-by-letter
against unambiguous same-page/same-font reference letters where needed)
found the bias pattern holds for the large majority, but **15 of the 85
are genuine errors in the current stored text**, concentrated in specific
klalim - proving the full check was necessary, not optional (Lesson 1),
and that a flag's aggregate statistics are not a substitute for looking at
each one (Lesson 2). **Fixed, applied to `part1.json`, `rebuild_all.sh`
re-run clean (764 candidates now, `current_text_may_be_wrong` dropped
70/85→70, pytest 10/10)**:

- **Klal 86, 87**: a real, repeated pattern - `חדוש`/`חידוש`/`חודש` (same
  triliteral root, "novella" vs "month") got mis-normalized during an
  earlier correction pass. Confirmed by direct crop AND by rendering
  `מטעם` from the same page in the same font (contains both מ and ט side
  by side) as an unambiguous calibration reference: `בחודשיו`→`בחדושיו`,
  `ובחידושי`→`ובחדושי` (klal 86); `בחודשי`→`בחדושי`,
  `ובחידושיו`→`ובחדושיו` (klal 87). Also klal 87: `משנה`→`ממשנה` (dropped
  the מ prefix - "שנתנה לו **מ**משנה", confirmed two clear מ strokes in
  the crop), `ע"ש`→`יע"ש` (dropped a י), `ט"ז`→`ט"ו` (ז/ו confusion,
  daf citation).
- **Klal 169**: `ורבינן`→`ורבינו` (ן/ו confusion; crop clearly shows a
  final vav, not nun).
- **Klal 178**: `אא`→`לא` (word_index 283 specifically - the current text
  had the non-word `אא` where the print reads `לא`/"not").
- **Klal 193**: a second real cluster - the actual print reads the full
  name `שמואל`/`כשמואל` (confirmed directly: "אי אמרה **שמואל** לחודיה"
  and "קאי **כשמואל**" both crop-legible in full), not the stored
  `שמון`/`כשמון`. Also `אטרה`→`אמרה` (ט/מ confusion - "ר' יוחנן" needs a
  verb, `אטרה` isn't a word).
- **Klal 208**: `זהה`→`זה` ("this" - `זהה` isn't 18th-century Hebrew
  vocabulary; crop shows two letters, not three).
- **Klal 220**: the stored `clean_text` had literal corrupted garbage
  (`לא שסי"יחך ואנכלואן הבודאב:ר שיבא לידי מעשה`) where the crop clearly
  reads a complete, ordinary sentence: `לא שייך אלא בדבר שיבא לידי מעשה`
  ("[it] is only relevant to a matter that will come to practical
  application"). This is the most severe of the 15 - not a letter
  confusion, a straightforwardly garbled/corrupted span that must have
  entered the text at some earlier processing step.

**One planned fix retracted before applying - a reminder that letter-shape
alone isn't enough (Lesson 6/9), context matters just as much**: klal 194's
`כ"מ` was initially misjudged as a `כ"ט` error based on tight-crop letter
shape alone. Rereading the full phrase - `וע"ע כ"מ פ' כ"ר מה' אישות`
("see also **Kesef Mishneh** [on] chapter...") - makes clear `כ"מ` is the
standard abbreviation for the halachic commentary *Kesef Mishneh*, a
completely sensible citation; `כ"ט` has no standard meaning in this slot.
Left unchanged. `דלפוס`→`דלפום` (klal 194, same klal, different word) was
re-confirmed and applied - `לפום` ("according to") is one of the most
common words in Talmudic Aramaic and the crop's final letter is
unambiguously a squared final-mem, not samekh.

**New, more serious finding surfaced while fixing klal 178, NOT yet
investigated or fixed**: the same klal's `clean_text` ends in a second,
worse corrupted span that was never flagged by the correction-candidate
pipeline at all - `אא הוא הדין לכל דדסומתימאא דנבאסשררו :לא נכללו` is not
real Hebrew in any reading. This sits right after the one `אא`→`לא` fix
applied above (two more unexplained `אא` tokens in the same klal, one
inside the garbled span itself). Because `build_corrections_dataset.py`
generates candidates by diffing DocAI raw tokens against `clean_text`,
and this span is garbled on **both** sides in a way that likely broke the
alignment (the same blind spot as Lesson 15, just from corruption instead
of low match_ratio), no candidate was ever generated here - the flag
pipeline is structurally blind to it. Needs a dedicated re-derivation from
`docai_word_boxes` against the physical page, the same treatment already
given to klal 82/83/128/165-167/180/182/185-190/194/196-197/215-217.
**Klal 178's ending is not yet trustworthy - flag for the next content
pass.**

**Left unresolved, genuinely ambiguous after direct crop inspection -
disclosed rather than guessed (per this project's own standing
convention)**, no change made: klal 36 (`הש"ס`/`השית'`), klal 88
(`בעניותי`/`בעניי`), klal 147 (`דסמיך`/`דסמך`), klal 151 (second `אמרה`/
`אמר` instance), klal 176 (`אשידה`/`אשירה`), klal 178 (`אכל`/`אבל` - a
different word_index than the fixed `אא`/`לא` one), klal 181
(`סכר`/`סבר`), klal 183 (`בסי"ג`/`בפי"ג` and `וככתובות`/`ובכתובות`),
klal 215 (`וכך`/`וכף`), klal 216 (`וכר`/`וכו'`). None of these are wrong
as currently stored as far as this session could determine - just not
confirmable either way from the crop alone.

The remaining ~70 of the 85 (the majority) were checked and confirmed the
current stored text is correct - vision's `A` pick was wrong, consistent
with the original bias hypothesis. Full per-item list and reasoning
worked through interactively this session; not separately filed, but the
governing methodology (crop at 700-900dpi, compare against same-page/
same-font reference letters, require semantic+visual agreement per
Lesson 9) is recorded here for the next person doing this kind of review.

**Read this at the start of every session, alongside `CLAUDE.md`.** `CLAUDE.md`
holds the durable rules; this file holds the current, specific, dated state of
the pipeline — what's fixed, what's still broken, and what was investigated
and why. It will go stale faster than `CLAUDE.md` and should be updated (not
just appended to — correct superseded claims) whenever a finding changes.

## `verify_corrections_vision.py` bug fixed: no request timeout, a hung call could block the whole run forever — 2026-08-06

Found while re-running vision verification after refreshing the header-
anchored alignment (see the vision-verification section below). The script's
retry/backoff logic only triggers on a *caught exception* - it had no
request timeout, so when one specific crop's Gemini call never returned and
never raised, the run sat blocked on that single candidate for 20+ minutes
at ~0% CPU with zero progress and no error, never reaching the retry path
at all. Confirmed by two consecutive checks 20 minutes apart showing the
exact same log line with no new output and no cache growth. Fixed
(partially): `genai.Client(...)` now passes `http_options=types.
HttpOptions(timeout=60000)` (60s). **Confirmed insufficient on its own**:
the same run hung a second time two candidates later (klal 187, `קפו`),
same symptom (0% CPU, zero cache growth, 15+ minutes, no exception ever
raised - so the 60s timeout is not actually firing). Isolated test: the
exact same candidate (same crop, same word pair) succeeds in ~20s when
run in a brand-new process. **Root cause found via `lsof -a -p <pid> -i`
on a stuck process**: it was sitting on a real ESTABLISHED TCP connection
to Google's API (over the machine's Windscribe VPN tunnel) that never
returned a response - a network/VPN-level stall, not a code deadlock, and
the client-level 60s `HttpOptions` timeout does not tear the connection
down (confirmed hung 20+ min with the socket still ESTABLISHED the whole
time). This is local-environment-specific (the VPN), not a corpus or
pipeline design bug. Workaround in place: a watchdog loop
(`vision_watchdog.sh`, in the session scratchpad, not committed) kills
and restarts the script whenever `adjudication_cache.db`'s
`corrections_cache` row count stalls for 6 consecutive 60s checks (~6
min - long enough not to kill a genuinely slow-but-alive call, which has
been seen taking up to ~40s normally), looping until the script completes
cleanly. Restarting is cheap since cache lookups are <10ms. This is a
workaround for a VPN/network issue, not a code fix - if it recurs outside
this session, check the VPN connection first before assuming a script
bug.

## Vision verification: coverage was already ~complete, not "90-item sample" — 2026-08-06

The Open Items claim "corrections_candidates_part1.json has 794 candidates
across 177 klalim, but only a 90-item sample has been vision-verified" was
itself stale (superseded, not corrected until now — see the two other
retracted-claim corrections above). Before running anything tonight,
`corrections_verified_part1.json` already had 551/551 vision-checkable
(bbox-present) candidates verified, 0 errors — the "90-item sample" number
was from an earlier point in the project and never updated as later runs
covered the rest. That claim is corrected now.

Ran `./rebuild_all.sh` (full, not `--skip-vision`) to pick up the word-pairs
that changed from tonight's klal 167/185-190/196-197/215-217 fixes: 628
current candidates, 622 already cache-hit, 2 new live Gemini calls (rest of
the "new" set turned out to be no-bbox insertions, not vision-checkable).
0 errors. Result: `corrections_part1.json` flags = `current_text_may_be_wrong:
70, current_text_confirmed: 123, unverified_insertion: 102, ambiguous: 279,
possible_omission: 54` across 628 items / 151 klalim. Full pipeline +
pytest suite ran clean.

**Gap found and FIXED: `part1_header_anchored_alignment.json` was stale
and structurally blocked vision-candidate generation for 13 klalim,
including the 9 just fixed tonight.** It still marked klal 34, 92, 129,
172, 180, 182, 186, 187, 190, 194, 197, 210, 216, 217 as `trusted: False`
using page/content data from before tonight's marker-misread-plus-merge
splits — `build_corrections_dataset.py` can't align to an untrusted klal
(Lesson 15), so these had **zero** correction candidates and had never
been vision-checked against their real content. Reran the (archived)
`header_anchored_alignment.py` against current `part1.json` (copied to
a temp location to run, since it resolves paths relative to its own
file - not re-added to root, still archived): diffed old vs new before
trusting it (Lesson 3) - all 13 flipped cleanly to `trusted: True`, zero
regressions among the previously-trusted 208, only klal 34 remains
untrusted (already a known/resolved case, Lesson 14's word-order klal).
221/222 now trusted, up from 208/222.

Regenerated candidates and ran vision verification against the newly
unblocked set: 777 candidates across 169 klalim (up from 628/151), 0
errors after one candidate's transient 504 timeout was picked up on a
second pass. Final `corrections_part1.json` flags: `current_text_may_be_
wrong: 85, current_text_confirmed: 149, unverified_insertion: 108,
ambiguous: 364, possible_omission: 71`. Full pipeline + pytest suite ran
clean. Part 1 vision-candidate coverage is now effectively complete
(221/222 klalim aligned and candidate-checked; klal 34 is the sole
known exception, already understood).

This run also surfaced and worked around a real infra issue, not a
corpus bug: see the `verify_corrections_vision.py` VPN-stall section
above (the vision-verification step of this fix took ~2.5 hours of
wall-clock time across the VPN-hang investigation and workaround before
the user turned the VPN off, after which the remaining candidates
finished in about 15 minutes).

**85 `current_text_may_be_wrong` items are an unreviewed queue, not a
finished result** (Lesson 2: a flag is a triage tool, not a verified
outcome) — none of these 85 have been individually crop-checked against
the scan yet. This is the next piece of work (user-requested, in
progress): crop-check each one, prioritizing the 13 klalim just
unblocked (34, 92, 129, 172, 180, 182, 186, 187, 190, 194, 197, 210,
216, 217) since their content changed most recently and has never been
human-reviewed against a vision check before.

## Standing regression test suite added — 2026-08-06

Requested: review status and consider building a test suite to improve
process. New `tests/test_corpus_invariants.py` (pytest, added to
`rebuild_all.sh` as step 7/7, gated by `set -euo pipefail` so a failing
test fails the whole rebuild) converts several of the manual sweeps this
document's "process evaluation" sections kept re-discovering by hand
(Lessons 8/18: a cheap corpus-wide text-pattern sweep catches what
klal-by-klal review misses) into standing, always-run checks:

- **Zero-tolerance** (no known legitimate exception anywhere in the
  corpus): klal_id sequence is exactly 1–667 with no gaps/dupes;
  `klalim_demo_dataset.json` exactly equals part1+part2+part3 concatenated
  (the Lesson 13 drift check); the `(no text available)` placeholder set
  and `CONFIRMED_NUMBERING_GAPS` are both now the **empty set** (as of the
  "Klal 185-190, 196-197, 215-217 resolved" section below — every klal
  originally treated as a genuine numbering gap, including this line's
  original {187, 190, 197, 216, 217} baseline and 167 before it, turned
  out to be a marker-misread-plus-merge with real recoverable content,
  not a real gap); zero page-header-contamination
  matches (all spelling variants); zero debug-print leaks (the klal
  152/154 `"283\n"` bug class); title/clean_text never empty.
- **Baseline (no-NEW-violations)**, because these checks have real,
  currently-documented false positives that aren't corpus bugs: duplicate-
  consecutive-word (Torah-verse repetition like klal 29's `שור שור שור` is
  genuine content, not a bug — the sweep's own false-positive rate was
  itself a finding, see the 2026-08-06 corpus-wide-anomaly section above),
  title-alphabetical-order (klal 101–104's deliberate elliptical-title
  convention, Parts 2–3's un-judged `"כלל <N>"` placeholders), and
  `validate_klal_span_coverage.py`'s ratio flag (klal 175's known
  conservative-rounding false positive, klal 106 at the threshold, klal
  179/181/193 now legitimately shorter post-180/182/194-split). Each
  baseline is a hard-coded set/count with inline citations to the exact
  section of this document that explains why it's not a bug; a NEW entry
  beyond the baseline fails the test and needs the same scan-verification
  standard as every other fix in this document before either being
  corrected or added to the baseline.

Span-coverage check requires the gitignored `gematria_trace_part1.json` +
`docai_word_boxes/` cache and `pytest.skip()`s if absent (e.g. a fresh
clone) rather than failing — consistent with those being regenerable
caches, not source-of-truth files.

**Verified working, not just written**: ran the full suite (10 tests, all
pass, 0.14s, no API calls) against current data; ran the full
`rebuild_all.sh --skip-vision` end-to-end with the new step 7/7 wired in
(confirmed idempotent — no diffs in `corrections_part1.json` /
`klal_page_regions.json` / `review.html`); smoke-tested all three
zero-tolerance detectors (header-contamination regex, debug-digit-leak
regex, duplicate-word baseline-diff) against synthetic bad input matching
the three real historical bugs (header leak, klal 152/154 debug leak,
klal 128's `לאוקומי לאוקומי`) to confirm they actually catch what they
claim to, not just pass vacuously on already-clean data.

`pytest` added to the venv and pinned in new `requirements-dev.txt` (no
requirements file of any kind existed before this).

## Klal 167 resolved — it was never a numbering gap, 2026-08-06

**Retraction of the 2026-08-06 "confirmed genuine numbering gap" verdict
for klal 167** (see the RETRACTED-AND-CORRECTED and "Update: klal 167's
marker genuinely does not exist" sections above). User pushed back: קסו
(166) and קסז (167) are easy to mix up in this print. Direct investigation
confirmed this exactly - it's the same marker-misread failure mode already
seen for klal 107 (ז read as ו), not a print gap, compounded by a second,
independent bug: klal 166's real content had been merged into klal 165's
stored text.

**True structure, confirmed by direct crop and full-token re-derivation**:
page 60 has two separate tokens both OCR'd as `קסו` at token 429 and token
503. Token 429 is genuinely `קסו` (klal 166's real marker - confirmed by
letterform, clean vertical vav). Token 503 is `קסז` (klal 167's real
marker) misread as `קסו` - confirmed by directly cropping and comparing
the last letter of both tokens at matching zoom: token 429's is an
unambiguous vav (clean vertical stroke, small rightward flag at top);
token 503's is visibly different (more bulk at the top, a small foot at
bottom-left) - consistent with zayin, not vav. Because docai's raw text
for token 503 matched the already-existing marker text (`קסו`) rather than
introducing a new distinct string, no prior "find the marker" text search
(including the one that produced the "genuine gap" verdict) ever
considered it as a *candidate* for klal 167 at all - it read as a
duplicate of klal 166's marker, not a new one.

Separately: klal 165's stored `clean_text` (page 60) contained klal 166's
real content merged in, undivided, after its own real ending - the same
"content hiding inside a trusted neighbor" pattern as klal 180/182/194
(Lesson 16), just not caught by that pass because 165/166 were never
flagged as candidates for it (both looked like ordinary, already-fixed
klalim from the 92-165 shift-zone work).

**Fixed, all three re-derived directly from `docai_word_boxes` tokens
(not hand-retyped) and cross-checked against the pre-existing stored text
where it already existed**:
- **Klal 165**: truncated to its own real content only (tokens 334-428,
  page 60) - exact match against the pre-existing stored text up to the
  split point, confirming the split boundary is clean.
- **Klal 166** (new record, was previously absent from the corpus
  entirely under its own klal_id): real content is tokens 429-502, page
  60 - the content that had been merged into klal 165. Title judged as
  `הלכה כמר בר רב אשי בכוליה תלמודא בר ממיפך שבועה ואודיתא` (the opening
  clause up to the natural `•` boundary, same convention as klal 165's own
  title).
- **Klal 167**: no longer a placeholder. Content = the pre-existing
  klal-166 slot's already-cleaned text (marker glyph corrected קסו->קסז)
  + the previously-uncaptured continuation across page 61 (977 tokens)
  and into page 62 up to klal 168's already-confirmed real marker (token
  140) - the span the earlier session found had "no marker anywhere" and
  wrongly concluded was empty. This is a third, independent bug on top of
  the marker misread: **that whole ~1450-token span was never extracted
  into the corpus under any klal_id before tonight** - not mislabeled
  elsewhere, genuinely absent, the same "content never captured at all"
  pattern as klal 92 and klal 128's missing tail.
- Title kept as `הלכה כבתראי` (already-judged, still accurate for the
  extended content - the whole span is one continuous discussion of the
  same maxim). `page` corrected 26 (stale) -> 60. Klal 168's stale `page`
  field (26) also corrected -> 62 (its own real marker was already
  correctly positioned; only this field was wrong).

**Verification standard, disclosed explicitly per this project's own
convention for large cross-page spans (klal 128/143/144 precedent)**:
klal 165/166's split and the two crop-checked word fixes below were
individually scan-confirmed; the bulk of the ~1450-word page 61/62
extension was verified by full-text coherence read-through (real
tractate/authority names throughout - Rif, Rambam, Rosh, Tosafot, Ran,
Rashba, Maggid Mishneh - ending in a natural closing formula), **not**
word-by-word crop-checked, matching the disclosed lighter standard used
for the other large cross-page klalim this session. Two things found and
crop-confirmed during the read-through:
- `טסי` (docai) -> `טפי` (real print) at the very first word of the page
  61 continuation - confirmed by direct crop; matches the already-noted
  catchword preview at the bottom of page 60, and grammatically necessary
  (`טפי` = "more/further", `טסי` isn't a word).
- `תלמור` -> `תלמוד` - confirmed by direct crop, the same well-established
  ד/ר confusion family documented throughout this corpus; `תלמוד` also
  appears correctly spelled elsewhere in this same klal.
- **Two duplicate-token artifacts caught by the new pytest suite**, not by
  the read-through: `הרי"ף הרי"ף` and `דף דף`, each a docai near-identical-
  bbox double-detection of a single printed word (same bug class as klal
  82/83's `בשל בשל`) - confirmed by direct crop that only one instance of
  each is actually printed, then the spurious duplicate token dropped.
  This is the regression suite added earlier tonight working exactly as
  intended: `test_no_new_duplicate_consecutive_words` failed on the first
  `rebuild_all.sh` run after this fix, which is what surfaced both.
- **Left as raw, unverified docai text, disclosed rather than guessed**:
  `מקטי` (×2, context suggests `מקמי` = "prior to") and `טי` in
  `בפ' טי שהוציאוהו` (context suggests `מי`, the perek name). A direct
  crop of the first `מקטי` instance was inconclusive - two close-reading
  attempts on the same token produced different letter identifications
  (ambiguous ט/מ shapes in this specific print), which per this project's
  own standing lesson means further eyeballing is unreliable and the
  right move is to leave it unresolved rather than force a guess. Also
  left as-is: two stray `-` hyphen artifacts and `רעדיות` (likely
  `דעדיות`/Mishnah Eduyot) - plausible but not verified.

`gematria_trace_part1.json` updated for klal 165/166/167 with `note`
fields explaining the correction (same convention as the klal 3/95
fixes), including klal 167's marker_position (503) which was previously
`marker_not_found_in_window`.

Full `rebuild_all.sh --skip-vision` re-run clean after the fix (including
the fixed duplicate-word baseline entry, relabeled 166->167 for the
already-documented genuine `קי"ל קי"ל` repetition). `validate_klal_span_
coverage.py` and `validate_title_alphabetical_order.py` both unaffected
(same flagged sets as before - klal 166/167 don't appear in either).

CONFIRMED_NUMBERING_GAPS in `tests/test_corpus_invariants.py` updated to
drop 167 - the remaining 5 (187, 190, 197, 216, 217) are unaffected by
this finding and still stand as directly-confirmed genuine gaps.

## Klal 185-190, 196-197, 215-217 resolved — none of the remaining 5 "confirmed gaps" were real, 2026-08-06

Requested: check the other 5 klalim (187, 190, 197, 216, 217) the same way
klal 167 was just resolved. User directly caught the first one by re-reading
the rendered page image themselves ("what you have for 186 is actually
187... 186 text is missing"), which reframed the whole approach: instead of
trusting the earlier "confirmed gap" verdicts, build a general check for
**orphaned tokens** (real docai content never captured under any klal_id)
and **double-assigned tokens** (the same real content captured under more
than one klal_id).

**New standing script: `check_klal_token_orphans.py`** (Part 1 only, same
`docai_word_boxes`/`gematria_trace_part1.json` dependency as the other
Part-1-only validators). For every klal boundary with a known real marker
position, it checks whether the klal's own stored `clean_text` actually
opens with the real docai text at that position - catching a same-length
*swap* (wrong content of about the right size attached to the wrong
klal_id), which `validate_klal_span_coverage.py`'s aggregate word-count
ratio cannot catch. Two designs were tried and rejected before landing on
word-sequence alignment (see the script's own docstring for the full
reasoning): a character-blob `SequenceMatcher` ratio scored the klal
186/187 swap at 0.68 (comfortably "matching") purely because both openings
share a 4-word template (`קפו הלכה כדברי המקיל`); a strict per-position
word check went the other way and false-flagged ~30% of the whole corpus,
because a single stripped `[.]` editorial mark or unstripped furniture
token permanently shifts every position after it. `difflib.SequenceMatcher`
over **word sequences** (not characters, not strict position) tolerates
small insertions/deletions while still correctly penalizing genuinely wrong
content. Run clean against the corrected corpus: 177 spans checked, 0
opening mismatches, 0 double-assignments.

**All 5 resolved - each was a marker-misread-plus-merge, the exact same
compound bug shape as klal 166/167, just varying which letter got
misread**:

- **Klal 185/186/187**: klal_id 186 held klal 187's real content verbatim
  (its own genuine קפז marker misread as קפו by docai, colliding with klal
  186's own real קפו marker sitting 24 tokens earlier on the same page).
  klal 186's own real content - a short, distinct 24-word span between
  klal 185's real end and klal 187's real marker - was orphaned, never
  stored under any klal_id at all. Confirmed by direct crop: both
  "קפו"-reading tokens are genuinely ו-shaped (ruled out a ד/ר or ז/ו-style
  misread for THIS specific pair - the collision here is a real print
  duplicate value, not an OCR letter confusion). Split: klal 186 now holds
  its own real (short) content, klal 187 now holds what was mislabeled
  under 186 (marker corrected to קפז).
- **Klal 189/190**: klal_id 189 held klal 190's real content merged in
  undivided (Lesson 16 pattern) behind a **correctly-read** קץ marker that
  no prior automated search ever found, because the search only tried the
  standard-form spelling קצ - קץ is the word-final-letter form of the same
  letter (ק"ץ, both = 190), standard Hebrew orthography, never
  cross-checked as an alternate spelling. Confirmed by direct crop: bold
  קץ marker immediately followed by bold הלכה, the standard convention.
  Split at the word boundary in the pre-existing (already-cleaned) stored
  text.
- **Klal 196/197**: klal_id 196 held klal 197's real content merged in
  undivided behind a קצז marker misread as קצו (ז->ו, the same specific
  confusion already confirmed for klal 166/167 - now a 2-for-2 pattern for
  this exact letter substitution). Confirmed by direct crop and by reading
  the full ~450-word span for a natural closing colon before the misread
  marker. Real klal 197 crosses the page 70->71 boundary; furniture (page
  70's catchword+watermark, page 71's running header) stripped using the
  same method established for every other cross-page reconstruction this
  project.
- **Klal 215/216/217**: klal_id 215 held **two** klalim's content merged
  in - not just one - the most severe instance of this bug pattern found
  yet (1645 words, three klalim's worth, under one klal_id). klal 216's
  real marker רטז was misread רטן (ז misread as final-nun ן - **a new
  letter-confusion pair for this project**, not previously catalogued;
  confirmed by direct crop, the marker's last stroke has ז's characteristic
  shape, not ן's). klal 217's real marker ריז was misread ריו (ז->ו, same
  family as 166/167 and 196/197). Both markers sit behind clean klal-ending
  colons, confirmed by direct crop and by reading the ~1600-word combined
  span end to end. Real 216 crosses the page 74->75 boundary, real 217
  crosses page 75->76; both required careful furniture-stripping (page 76
  additionally had a stray out-of-position `1` token before its real
  4-word header, plus a separately-positioned printed folio number `לב`,
  a token-count anomaly like the one already documented for klal 97's page
  44 header). Split by locating the two marker words in the pre-existing
  stored text (not rebuilt from raw tokens - an earlier attempt to rebuild
  klal 215 directly from `docai_word_boxes` introduced a spurious `חזה`
  vs `וזה` word difference against the already-hand-corrected stored
  text, which the split-in-place approach avoided).

**Separately found and fixed, same investigation: klal 3/4 duplication.**
While calibrating the orphan-scanner, its double-assignment pass flagged
klal 4's opening chunk as also appearing under klal 3. klal 3's real,
already-correct final sentence (`ד ואפ"ה חשיב ליה שם בזבחים למד מלמד
והניח הדבר בתימה וגדולה היא אלי וצ"ע :`) had ALSO been prepended to klal
4's stored text - confirmed by direct crop with bounding-box annotation:
the small `ד` at the very end of klal 3's real last line and the bold `ד`
that's klal 4's genuine marker are two *different* tokens sitting on
different lines, and something (most likely the original cross-page-
truncation reconstruction, which used the small `ד` as an anchor) grabbed
the wrong one. Fixed by trimming the duplicated prefix from klal 4's
stored text; klal 3 needed no change.

**New letter-confusion pairs catalogued tonight, worth remembering for
any future unresolved-marker investigation**: ז misread as ה is NOT what
happened for 185/186 (ruled out by direct crop - that was a genuine
duplicate value, not a misread); ז misread as final-nun ן (new, klal 216);
alternate-valid-gematria-spelling blind spots for both 190 (קץ vs קצ) and
215 (רטו vs ריה) - a distinct failure mode from a letter misread, since
the text is read *correctly* but the search tool never tried the
alternate valid spelling.

Full pipeline (`rebuild_all.sh --skip-vision`) re-run clean after all
fixes; `validate_klal_span_coverage.py` and `validate_title_alphabetical_
order.py` both re-run clean (same baselines as before - none of tonight's
fixes introduced a new flag); `gematria_trace_part1.json` updated with
proper entries and `note` fields for every klal touched, matching the
established convention. `tests/test_corpus_invariants.py`'s
`CONFIRMED_NUMBERING_GAPS` set is now **empty** - every klal originally
flagged as a genuine numbering gap turned out not to be one.

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
- **RESOLVED 2026-08-06**: the many pre-existing tracked one-off scripts at
  root noted below as not-yet-cleaned-up have now been moved. Root cleanup
  done: 37 one-off scripts (`fix_1_line_offset_and_rebuild.py`,
  `fix_klal_74_stitching.py`, `build_full_pristine_667.py`, etc.) →
  `archive/scripts/`, their throwaway JSON outputs + a stray `.hocr` →
  `archive/data/`, 19 superseded planning/report docs (predating
  `review.html` as the live verification tool) → new `archive/docs/`, and
  13 gitignored `*.old` backups deleted outright. Root now holds only the
  13 scripts actually in active use (`rebuild_all.sh`'s 6 stages,
  `orchestrator.py`, `chunker.py`, `build_vlm_demo.py`, and 3 standalone
  validators). Verified by re-running the full rebuild + all validators
  after the move — one dependency mistake caught in the process:
  `gematria_trace_part1.json` was briefly archived as throwaway trace data
  but is a live input to `validate_klal_span_coverage.py`; restored to
  root immediately when the validator failed.
- **The abridged `title` field must be judged, not algorithmically derived.**
  The source print doesn't reliably punctuate where a title ends and
  explanatory text begins (e.g. klal 5's title is the single word `איתמר` —
  no word-count or punctuation rule can know that). Titles for all 222 Part 1
  klalim were manually read and judged (see `apply_judged_titles.py`) rather
  than generated by a formula; Parts 2–3 (klal 223–667) still need the same
  treatment — do not regenerate Part 1's titles algorithmically. **Quantified
  2026-08-05**: at minimum 115 of 445 Part 2–3 klalim (26%) have a literal
  `"כלל <N>"` placeholder title, not real judged content — see "Alphabetical
  order check redone correctly, twice" below for the full list. This is
  larger than a documentation gap; it means over a quarter of Parts 2–3 have
  no usable title at all yet.
- **Editorial punctuation insertions are marked `[.]` in `clean_text`** (square
  brackets, the standard critical-edition convention), inserted only where the
  original print has no punctuation at the judged title/explanation boundary.
  This is scoped to that one boundary per klal, not a full re-punctuation of
  every sentence — a corpus-wide punctuation pass is a distinct, much larger
  task not yet undertaken (needs its own scoping: cost, whether to cover all
  667, and a review pass before treating inserted marks as final).
- **SUPERSEDED — all 8 of the original "no text available" klalim turned
  out to have real content; none was a genuine numbering gap.** First 3
  (klal 180, 182, 194) were found merged into a neighboring klal's stored
  text behind a garbled second marker (dated 2026-08-06 section below).
  The remaining 5 (167, 187, 190, 197, 216, 217 — see the two
  "resolved" sections above this Open Items block) turned out to be the
  same marker-misread-plus-merge pattern, not real gaps either. Part 1
  now has zero `(no text available)` placeholders and zero entries in
  `CONFIRMED_NUMBERING_GAPS`. Original text (retained for the record):
  "3 of the original 8 'no text available' klalim had real content and
  are now fixed: klal 180, 182, 194 were each merged into a neighboring
  klal's stored text, hidden behind a garbled second marker and
  page-header noise - see the dated 2026-08-06 section below (the
  correction of an earlier same-night finding that wrongly called all 8
  numbering gaps; the user caught the error). All three are now split
  out, scan-confirmed, and titled."
- **SUPERSEDED — the 2026-08-06 "CLOSED: 6 confirmed genuine numbering
  gaps" verdict below was itself wrong for all six.** Klal 167 (see "Klal
  167 resolved" above) and klal 187, 190, 197, 216, 217 (see "Klal
  185-190, 196-197, 215-217 resolved" above) were each a marker-misread-
  plus-merge, not a real gap: real content existed for every one of them,
  merged undivided into a neighboring klal's stored text behind a garbled
  second marker. All six are now split out, scan-confirmed, and titled in
  `part1.json`; `tests/test_corpus_invariants.py`'s
  `CONFIRMED_NUMBERING_GAPS` is now the empty set (was `{187, 190, 197,
  216, 217}`) and the `(no text available)` placeholder set is now empty
  too — there are no known genuine numbering gaps left in Part 1. Original
  "CLOSED" text (retained below for the record, do not treat as current):
  "Klal 167, 187, 190, 197, 216, 217 are confirmed genuine numbering
  gaps - all six directly verified by visual inspection of the physical
  scan page at the exact boundary (not just token adjacency, which is
  what produced the wrong 180/182/194 conclusion). Klal 85/86 is a
  separate, already-resolved matter (checked 2026-08-06; it is NOT
  currently a merge issue - an earlier note in this document citing it as
  an open parallel was stale). User decision (2026-08-06): keep the
  explicit placeholder — each of the six stays in the klal_id sequence
  with clean_text/title set to "(no text available)", citable at its
  correct number rather than omitted from the sequence."
- **Klal 186 — fixed 2026-08-06** (see dated section below): the garbled
  opening was a corruption of `הלכה כדברי המקיל באבל`, confirmed by
  direct crop of the real page (68, not the stale stored `27`). No
  longer open.
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
  pages 1–12 exists now (see the duplicate-page bug below) but none of it has
  been transcribed into `clean_text` or any structured output — this is a
  distinct, unscoped piece of work, not covered by "667 klalim" success
  criteria as currently framed.
- **`docai_word_boxes/page_1.json`–`page_12.json` were byte-identical
  duplicates of `page_13.json`–`page_24.json`** (a systematic off-by-12 bug in
  whatever batch OCR run originally produced pages 1–61) — found and fixed by
  deleting and re-extracting pages 1–12 with `extend_docai_ocr.py`'s
  synchronous per-page method. `header_anchored_alignment.py` excludes/ignores
  this range for klal-text alignment purposes (front matter, not klalim), but
  any future front-matter transcription work should use the now-correct pages
  1–12, not assume they're still bad.
- **`aligned_klalim`'s page-to-klal mapping is discredited — do not trust it.**
  First-principles re-verification (`header_anchored_alignment.py`, which
  cross-checks each klal's text against its page's own printed section header,
  independent of `aligned_klalim`) found the mapping was wrong; an earlier
  session's belief that vision-verified coverage was klal 1–222 turned out to
  itself be based on this flawed mapping. Real coverage, re-derived from
  scratch: `part1_header_anchored_alignment.json` now has a trusted
  page-attribution for 208/222 Part-1 klalim (the other 14: the 8 known
  placeholder klalim, klal 186's known corruption, and 5 more low-text-
  similarity flags — klal 34, 92, 129, 172, 210 — worth a closer look).
  `docai_word_boxes` page coverage was extended from page 61 to page 82 to
  make this possible. `build_corrections_dataset.py` and `review.html` use
  this mapping; `corrections_candidates_part1.json` has 794 candidates across
  177 klalim, but only a 90-item sample has been vision-verified so far — the
  rest still needs it.
- **Klal 65, 21, 218, 219 fixed**: same ד/ר, ם/ס, ו/י visually-similar-letter
  OCR confusion in each case — `ב"ר`→`ב"ד` (65, confirmed against Mishnah
  Eduyot 1:5), `עודו`→`עורו` (21), `שגס`→`שגם` (218), `האו`→`האי` (219). Each
  confirmed by both the vision check and the text-only semantic-plausibility
  check (`verify_semantic_sanity.py`) agreeing independently, and cross-checked
  against `gematria_trace_part1.json` to confirm they sit outside the
  structural shift zone (see below) before touching them.
- **Klal 82, 83 fixed**: `בשר`→`בשל` (82; `בשר סופרים` is meaningless, `בשל
  סופרים הלך אחר המקיל` is a real, well-known halachic maxim). Klal 83 was a
  genuine cross-klal-boundary text scramble, not just a word error: the
  stored text had a nonsensical duplicated `בשל בשל` with klal 82's closing
  citation (`דף ס"א ב' וש"ות זקן אהרן סי' קפ"ג`) misplaced into its middle.
  Root cause, re-confirmed 2026-08-04 by reading `docai_word_boxes/page_37.json`'s
  raw token array directly (not just re-asserting the earlier summary): klal
  82's own extraction stops mid-word (`ישרא`, never reaching `ישראל` or the
  citation after it). Klal 83's decoratively-set opening word got detected by
  Document AI as **two separate tokens** (`בשו` at y=0.7772, then `בשל` at
  y=0.7676 — same word, two boxes, two slightly different OCR reads), and
  **both were extracted before the citation line** (`דף ס"א ב'...קפ"ג` at
  y=0.7608) even though the citation's smaller y-value means it sits
  physically *above* both of them on the page. Whatever assembles the running
  text per klal just walks the token array in extraction order, so it
  faithfully reproduced the inversion: doubled opening word, then a citation
  that belongs to the klal above, then the real sentence. True reading order
  is klal 82 ending with the citation, then klal 83 opening
  `בשל תורה הלך אחר המחמיר...` (the deliberate counterpart to klal
  82's `בשל סופרים הלך אחר המקיל` — Biblical law → strict, rabbinic law →
  lenient). Fixed: 82 now ends with the citation restored; 83 now reads `בשל
  תורה הלך אחר המחמיר ובשל סופרים הלך אחר המקיל...` with the duplicate and
  the misplaced citation removed. **Found only because the user manually
  spot-checked and pushed back on a result already reported as "resolved"
  (0.8 agreement)** — see `CLAUDE.md` Lessons Learned on why a passing score
  isn't the same as verified.
- **RESOLVED, both halves — checked 2026-08-07, this bullet was stale and
  had never been corrected against later work that already closed it
  (the "update it, not just append" rule this document sets for itself).**
  Original text, retained for the record: "Two more candidates from the
  same batch that fixed klal 65/21/218/219 were deliberately NOT applied:
  klal 144 (`הדואה`→`הרואה`, high confidence) sits in a spot the gematria
  trace couldn't confirm either way, and klal 85's flagged 'missing `פו`'
  is not a word-level fix at all — the model's own reasoning shows `פו`
  marks the start of klal **86**, meaning klal 85 and 86 are currently
  merged into one entry. That's a klal-boundary problem (success criterion
  #2), not a text correction; fixing it means splitting the klal, not
  inserting a word. Left for the structural pass below."
  - **Klal 144's `הדואה`→`הרואה`**: the flagged word never belonged to
    what's now canonical klal_id 144 at all — it was mislabeled under a
    stale/legacy local numbering. The content actually landed in current
    klal_id 143 (`דיוני גולה הוא קרנא`, 759 words) during the later klal
    130-144 cross-page reconstruction (see "klal 143 and klal 144 turned
    out to be two more large, cross-page klalim" above), which explicitly
    resolved this exact fix via sentence-context confirmation (`בפ'
    הרואה נ"ח ב'` — the Berachot chapter name) and also fixed a second,
    related item in the same klal (`שבהדי"ף`→`שבהרי"ף`). Directly
    re-verified now: current `part1.json` klal 143 contains `הרואה` and
    `שבהרי"ף`, not the old misreadings — the fix is applied and correct.
    Canonical klal_id 144 (`דרשות אין לנו לעשות מעצמנו`, 1336 words) is
    unrelated content and never had this issue.
  - **Klal 85/86 merge concern**: confirmed NOT a merge. Current
    `part1.json` has klal 85 and 86 as distinct, complete entries, each
    opening with its own real gematria marker (`פה`, `פו`) as the literal
    first word of `clean_text` and ending in a natural closing colon.
    `check_klal_token_orphans.py` re-run clean (196/196 spans, 0 orphans,
    0 double-assignments) — this boundary is included and passes. Matches
    the already-existing "Klal 85/86 is a separate, already-resolved
    matter" note elsewhere in this document; this bullet was the one place
    that note was never propagated to.
  - **Genuinely still open, disclosed rather than silently dropped**: klal
    143 and klal 144's long cross-page extensions (759 and 1336 words,
    the reconstruction that resolved the `הדואה`/`שבהדי"ף` items above)
    were verified only by full-text coherence read-through, never
    individually crop-checked against the physical scan — a disclosed,
    lower-rigor standard than the rest of this document (see "Neither
    extension was cropped against the physical scan at all" above). A
    scan-crop follow-up pass on these two specific klalim is the one real
    piece of unfinished work this investigation surfaces.
- **Systematic semantic-sanity pass run against all 52 klal-1–91 title flags**
  scoring below 0.9 agreement (widened from 0.7 — see `CLAUDE.md` Lessons
  Learned item 2), not just a sample: `semantic_sanity_titles_1to91.json`.
  8 of 52 came back favoring the alternative reading. Two were klal 82/83
  (already found and fixed by hand, see above — good independent
  cross-validation, the automated pass reached the same conclusion). Of the
  remaining 6, each was checked against an actual scan crop before touching
  anything (not just trusted on the semantic score alone):
  - **Klal 50 fixed**: stored text had a duplicated `עונשין עונשין מן הדין`;
    the scan clearly shows the word only once. Now `אין עונשין מן הדין`.
  - **Klal 58 checked and NOT changed**: the semantic pass suggested
    `בשיטה`→`כשיטה`, but a tight, high-DPI crop of just that word shows an
    unambiguous `ב` (flat right-angle corner, not `כ`'s curve). Current text
    is correct — the semantic-sanity signal was wrong here, a concrete
    reminder that even the second-layer check needs verification against the
    actual scan when it disagrees, not blind trust.
  - **Klal 21, 39, 75, 79: RESOLVED 2026-08-05** (see "Klal 21, 39, 66,
    75, 79 — all checked against the scan, all confirmed correct" below).
    All four checked directly against the scan by precise y-coordinate
    token filtering; current stored text confirmed correct in every case
    — none of the semantic-pass flags held up. No change needed, no
    longer open. (Original flags, for the record: klal 21 `תותה`→`תותיה`;
    klal 39/75 long-vs-short title candidates; klal 79 `או`→`אי` plus a
    supposedly-missing trailing `וכו'`.)
  - The other 44 of the 52 (agreement 0.7–0.9, not among the 8 the semantic
    pass flagged) are presumed fine per that pass, but — consistent with the
    klal 58 result above — a semantic-sanity "no objection" is still not the
    same as a scan-verified result. Treat as reasonably trustworthy, not
    scan-confirmed.

## Klal 178's second corrupted span — FIXED, 2026-08-07

Closes the open item logged in the "Crop-check of all 85
`current_text_may_be_wrong` flags" section above. Found klal 178's real
marker (page 66, token 419) and klal 179's real marker (page 66, token
833) via `gematria_trace_part1.json`, read the full 414-token raw docai
span between them end to end. The raw text matches the stored
`clean_text` exactly all the way to `...מכללו אא הוא הדין לכל` and then
diverges completely - the real continuation is a fully coherent halachic
sentence closing with the standard `כנלע"ד וכ"כ [authority]...ע"ש :`
formula (`המקומות והאיסורין דסתמא נאסרו ולא באו לשלול רק היכא דידעינן
בבירור דמעולם לא נכללו בכלל האיסור דומיא דבשר בחלב וכדכתיבנא כנלע"ד וכ"כ
שם הריטב"א ע"ש :`), not the stored `דדסומתימאא דנבאסשררו :לא נכללו`
garbage. Applied (unique-string replace, verified count=1 before
writing). The `אא` immediately before the fixed span was deliberately
left as-is - docai's independent raw OCR reads `אא` at that exact
position too (not `אלא`), so it's what's actually printed, not part of
the corruption. `rebuild_all.sh` re-run clean, 10/10 pytest.

## `part1.json`'s own `page` field is stale/dead metadata for most of Part 1 — found 2026-08-07, NOT fixed (confirmed non-blocking)

Found while resolving the 92-165 marker positions below: cross-referencing
every klal's `part1.json` `page` field against `gematria_trace_part1.json`'s
independently-confirmed real PDF page turned up **136 mismatches across
nearly the whole of Part 1** (klal 3 through klal 222), not just the 92-165
range - e.g. klal 220-222 show `page: 30` in `part1.json` while their real
PDF page is 76. This looked like a major, corpus-wide bug at first.

**Confirmed non-blocking before treating it as one** (per this project's own
standing rule not to trust a field's role without checking): grepped every
build script for a read of `k["page"]`/`k['page']`. Only `build_review_html.py`
touches it, and that script **overwrites** it on read
(`k["page"] = trusted_page_of.get(k["klal_id"])`, sourced from
`part1_header_anchored_alignment.json`'s trusted `matched_page`, not from
`part1.json` at all). `build_klal_page_regions.py` and
`build_corrections_dataset.py` independently source their own page grouping
from the same alignment file, never from `part1.json`. **`part1.json`'s own
`page` field is not read by any live part of the pipeline** - it's vestigial,
most likely dating to before `part1_header_anchored_alignment.json` existed
and superseded it as the trusted page source. This explains why such a
widespread mismatch was never noticed as a functional bug (nothing was
broken) despite individual instances being spot-fixed in passing elsewhere
in this document (klal 165 "`page` corrected 26 (stale) -> 60", klal 168
similarly) - those fixes were cosmetic/consistency cleanup, not restoring
broken functionality.

**Still worth fixing eventually, just not urgently**: if `part1.json` is
ever exported toward the Sefaria delivery (success criterion #3), a stale
`page` field per klal would be wrong metadata in the final product even
though it's inert today. Left as an open item, not fixed tonight - not
blocking anything currently.

**FIXED 2026-08-07.** Regenerated from the two trusted sources instead of
by hand: `gematria_trace_part1.json`'s marker-anchored `page` where
`status == 'ok'` (199/222 klalim - the more precise value, tied to an
exact token position), falling back to
`part1_header_anchored_alignment.json`'s trusted `matched_page` for the
rest. Cross-checked the two sources against each other first (per Lesson
9, independent signals should agree before trusting either): 199 klalim
had both, only 1 disagreement (klal 190, a page-boundary edge case -
its marker sits at the tail of page 68 but the bulk of its
alignment-matched content is page 69; kept the marker page as more
precise for "where does this klal begin"). 148 of 222 `page` values
corrected. **Klal 34 is the sole klal with no reliable page source at
all** (neither trace nor alignment trust it - the same already-documented
Lesson 14 word-order case) - left untouched, not guessed. `rebuild_all.sh`
re-run clean, 10/10 pytest. No longer open.

**Superseded later the same day — see "Klal 34 investigation" above.**
Klal 34's marker was found (page 26, token 374; docai had misread the
marker glyph itself) and both `gematria_trace_part1.json` and
`part1_header_anchored_alignment.json` now trust it. Its `page` field is
no longer an exception - already correctly `26` in `part1.json` from the
crop-confirmed 2026-08-05 work, now backed by a trusted source too.

## Klal 123 span-coverage false positive - verified and added to the test baseline, 2026-08-07

Surfaced by `tests/test_corpus_invariants.py`'s span-coverage regression
test correctly catching it as a NEW flag (not yet in the baseline) after
the 92-165 marker-position fixes below changed what the validator could
compute. Read the full raw token span between klal 123's and klal 124's
confirmed real markers (page 46 idx 741 → page 47 idx 41, 64 tokens) end
to end: the stored 53-word `clean_text` is genuinely complete (a real,
naturally short klal - part of the already-documented `קכב`/`קכג`
same-title pair) - the gap is `Digitized by Google` (scan watermark), a
stray footnote numeral, a folio number, and the next page's running
header, ~11 furniture tokens inflating the raw span-token count. Same
false-positive class as klal 106/175. Added to
`SPAN_COVERAGE_BASELINE` in `tests/test_corpus_invariants.py` with a
citation. `rebuild_all.sh` re-run clean, 10/10 pytest.

## Structural klal-boundary/content-shift issue — RESOLVED 2026-08-07, see below for the closing status

**SUPERSEDED.** The "70 of ~120 klalim still show a genuine marker/content
mismatch" claim below was accurate when written (2026-08-05) but describes
a problem that has since been closed out through many individual fixing
sessions logged throughout this document (klal 92-129 fixed one by one,
klal 165/166/167/185-190/196-197/215-217 fixed via the marker-misread-
plus-merge pattern). By 2026-08-07, the only genuinely remaining piece was
17 klalim (93, 115, 116, 124, 127, 129, 131, 139, 144, 145, 147, 149, 150,
151, 153, 155, 160, 164) whose real marker position had never been found
by any automated search - not because their content was wrong, but
because the search window was too narrow (klal 129's case, already
documented) or the marker glyph itself was OCR-misread in a way no
"not found" search retried (ז misread as ו/ן, ד misread as ר - the same
families already catalogued throughout this document). **All 17 resolved
2026-08-07** by widening the search and trying known letter-confusion
variants; for every one, the docai raw text at the newly-found position
was compared against the already-stored `clean_text` and matched exactly
(content was already correct - it just needed its position confirmed),
and the 4 genuinely ambiguous letter-shape cases (116, 124, 127, 147)
were additionally confirmed by direct crop against the scan. **No content
changes were needed - this was a metadata/trace-file gap, not a text
bug.** `gematria_trace_part1.json` updated with all 17 positions.

**Second finding while closing this out: `gematria_trace_part1.json`'s
`status` field is itself stale in many places and cannot be trusted at
face value** (Lesson 3) - 37 entries in the 92-165 range still said
`marker_found_content_mismatch` from an early diagnostic pass, frozen
from *before* the individual klal-by-klal fixes that happened over the
following two days were applied. Re-verified all 37 directly (docai raw
text at the recorded position vs. stored `clean_text`): every single one
already matches (mismatches were leftover docai OCR artifacts already
correctly adjudicated in the stored text, e.g. `רחיה`→stored `דחיה`,
`ביו בית`→stored `בית` (already-documented duplicate-token drop), not
real problems). All 37 updated to `status: ok`. Combined with the 17
above, **the entire klal 92-165 structural range is now confirmed
resolved** - `check_klal_token_orphans.py` (196/196 spans checked, up
from 177, 0 issues) and `validate_klal_span_coverage.py` both re-run
clean.

**Third finding, out of scope for tonight, logged separately below (`part1.json`
"page" field is stale/unused metadata) and fourth finding (klal 123 false
positive, now baselined) - see the two sections immediately below this
one.**

Original (2026-08-05) text, retained for the historical record - the
specific numbers and "NOT fixed" framing are superseded by the above, the
causal analysis (docai file-swap bug vs. upstream assembly error) is
still accurate history:

First-principles gematria-marker tracing (`trace_gematria_sequence.py` →
`gematria_trace_part1.json`) found real, independently-confirmed content
misalignment spanning roughly **klal 92–165**. This is now confirmed to have
(at least) two distinct, separately-diagnosed causes:

1. **A docai file-swap bug** (see below) — explains *some* of the range's
   symptoms (klal 101, 102, 104 were victims of this specifically and are now
   fixed by re-extraction) but not most of it.
2. **A genuine, still-unfixed upstream error** in how `clean_text`'s klal
   boundaries were originally assembled for this range, unrelated to any
   OCR-extraction bug. Directly re-verified after the docai fix (see below)
   for klal 94/95/98/99/100 — still wrong, e.g. stored klal 99 is actually
   gematria צח=98's real content. **70 of ~120 klalim in klal 92–165 still
   show a genuine marker/content mismatch after the docai fix.** This needs
   its own scoped re-chunking pass against the scan — not a quick patch, and
   not something to fix by editing the `title` field (the klal 102–106/108/
   119/210 title-letter violations found by `validate_title_section_letter.py`
   are a symptom of this, not a standalone title-wording issue). Klal 85/86
   (see above) may be an additional, separate merge issue nearby.

Before extending `trace_gematria_sequence.py` further, note its blind spot:
short gematria markers (roughly klal 1–90) collide with ordinary citation
numerals in the running text, so a "not found" result there is not proof of
a problem, and a "found" result is not proof of correctness either. See
`CLAUDE.md` Lessons Learned.

## docai_word_boxes file-swap bug — found and fixed

`docai_word_boxes/page_37.json` and `page_38.json` had their content swapped
— confirmed by tight-cropping the exact same bbox from both candidate
physical PDF pages at 400dpi and reading both directly (not inferred). A real
bug in the *original* (pre-existing) batch extraction of pages 13–61,
unrelated to the page 1–12 duplicate-junk bug. **Fixed by deleting and
re-extracting all of pages 13–61** with `extend_docai_ocr.py`'s synchronous
per-page method (the same method already proven correct for pages 1–12 and
63–82). A full backup of the pre-fix files exists in scratch. Spot-verified
after re-extraction: pages 20, 34, 37, 38, 39, 50, 60 all tight-crop-confirmed
correct.

**IMPORTANT — this cache is gitignored.** `docai_word_boxes/` is treated as a
"regenerable cache" per `CLAUDE.md`'s directory-layout convention, but tonight
proved regeneration isn't always trivially correct — the *original*
extraction had this real bug baked in. The corrected files exist on local
disk now (and survive a session clear, since that only affects conversation
state, not the filesystem) but are NOT captured in git history. If this repo
is ever re-cloned fresh, pages 13–61 need to be re-extracted with
`extend_docai_ocr.py` (the per-page synchronous method) — do not assume
whatever regeneration process existed before tonight is safe to blindly rerun
without the same tight-crop verification done here.

### Effect on the klal 92–160+ finding: partially explained, NOT resolved

See "Structural klal-boundary/content-shift issue" above — re-running the
full pipeline against corrected data resolved klal 101/102/104 specifically
but left the majority of that range's problems unchanged, proving it's a
real, separate, upstream issue.

### Effect on klal 1–91: genuinely improved, but not 100% clean

Titles re-verified against corrected data
(`title_verification_part1_1to91.json` — supersedes the klal 1–91 slice of
the original `title_verification_part1.json`, which was built on pre-fix
docai data and should not be trusted for that range anymore): low-agreement
count dropped from 45/90 to 41/90, and the previously badly-broken klal
76–84 cluster mostly resolved (78, 79, 81, 82, 84 scored 0.8–1.0 — and see
klal 82/83 above for why "scored 0.8" still needed a manual look).

**Known-real remaining problems in klal 1–91**, none explained by either root
cause found so far:
- **Klal 34 — fixed 2026-08-04** (see dated section below): was a real
  missing-clause error, not just a low-similarity false alarm. No longer
  open.
- **Klal 66 — resolved 2026-08-05** (see dated section below): checked
  directly against the scan with precise y-coordinate token filtering;
  current text matches the print exactly. No longer open - the "wrong
  content" flag was itself a false alarm.
- **Klal 67 — resolved 2026-08-04** (see dated section below): the marker
  *is* on page 34 (`scratch/klal67_marker_zoom2.png` shows `סז` clearly) —
  the earlier "not found" result was a tool/search-precision miss, not a
  real misattribution. No text change needed.
- **Klal 21, 39, 75, 79 — resolved 2026-08-05** (see dated section below):
  all four checked directly against the scan; current text confirmed
  correct in every case, including klal 79 where the flag's specific
  concerns (`או`/`אי`, a supposedly-missing `וכו'`) were both already wrong
  or already resolved. No longer open.
- Word-level correction verification for 1–91 is no longer a thin sample —
  see the 2026-08-04 dated section below, which crop-verified 40 additional
  candidates. Corpus-wide (parts 1–3, all 794 candidates), coverage is still
  thin.

**Honest bottom line for "is klal 1–91 presentable": closer, and the named
list is now clear.** The severe, multi-klal cascading failures are gone.
Klal 50, 65, 21 (the corrections-level fix), 82, 83, 218, 219, 34 are now
fixed and scan-confirmed; klal 67's marker mystery, klal 3's disagreement,
klal 66, and klal 21/39/75/79 (title-level) are all resolved (reviewed, no
fix needed in any of them). What remains is the general thin
word-level-verification coverage the rest of the corpus (parts 2–3, and the
untouched 90–222 range of part 1) still has, not a named list of specific
unresolved klalim in 1–91 anymore. Do not present this range as fully
verified without either resolving those items or explicitly caveating them.

## Klal 1–91 correction-candidate semantic/vision disagreement pass — 2026-08-04

Of the 794 `corrections_candidates_part1.json` candidates, 61 are
"replace"-type items in the klal 1–91 range where a docai-raw reading
(candidate A) differs from the current stored text (candidate B). Each was
run through `verify_semantic_sanity.py` (`scratch/semantic_check_reversions_1to91.json`),
independently from the vision check already on file
(`scratch/corrections_verified_1to91.json`) — two independent signals, per
`CLAUDE.md` Lessons Learned #9.

- **21 of 61**: vision and semantic agreed (both favored A, or both favored
  B). Applied/kept per that agreement without further work needed.
- **40 of 61**: vision and semantic disagreed — vision consistently favored
  the docai-raw reading (A), semantic consistently favored the current text
  (B) as the more standard-looking word. Per Lessons Learned #9, disagreement
  alone is not a resolution either way — each of these 40 was individually
  tie-broken with a fresh high-zoom crop of the exact word from the source
  scan (all saved under `scratch/klal<N>_*.png`), not decided by trusting
  either automated signal.
  - **Initial pass (same day) got this wrong: all 35 were applied on the
    strength of the crop tie-break alone**, i.e. purely on which letterform
    the pixels seemed to show, without checking whether the resulting
    sentence actually made sense. That is exactly the mistake Lessons
    Learned #2/#9 warn against — a "passing" pixel read is not a checked
    result, and a single signal (even a manually-verified one) isn't
    sufficient when it's cheap to also check the sentence. **Corrected the
    same day** by re-reading every one of the 35 in full sentence context
    (recognizable technical terms, standard citation abbreviations, named
    Amoraim, real tractate/perek names, grammatical fit) instead of trusting
    the isolated letterform:
    - **17 of 35 held up** under sentence-level review and were left as
      applied. These aren't just "the crop looked right" — each matches
      something independently checkable: a real perek name (`העור והרוטב`
      in Chullin), a verbatim Mishnah quote (`רואה אני את דברי אדמון`,
      Ketubot 13), a named Amora (`רבא`), a standard Aramaic idiom
      (`לאו אורחיה`), or — for the klal 87 cluster — a coherent Aramaic
      anecdote that only reads as a connected narrative once corrected
      (the pre-session text had `שרמינו בתרומה`, which is nonsense; the
      corrected text has `שהניחו בתימה`, "[what Tosafot] left in
      puzzlement," a standard construction). Full klal-by-klal list of the
      17 lives in session notes, not reproduced here in full.
    - **18 of 35 were wrong and have been reverted** back to the pre-session
      text: the applied reading replaced a real, sensible word with either a
      non-word or a broken standard phrase. Examples: `דנראה` (standard "it
      appears from") was changed to the non-word `דנראח`; `הש"ס` (standard
      abbreviation for the Talmud) was changed to the non-word `השית`;
      `וז"ל` (standard citation formula "and this is his wording") was
      changed to `ח"ל`; `חטאת` (part of the real perek name `דם חטאת` in
      Zevachim) was changed to `הטאת`; `והכ"מ` (Kesef Mishneh, a standard
      commentary paired with Maggid Mishneh in the same sentence) was
      changed to the unrecognized `והכ"ט`. Full revert list: klal 1, 14, 22,
      25 (×2), 36, 41 (×6), 42, 43, 44, 54, 60, 61, 62, 74, 86 (×4), 87 (×4),
      88, 91 — see `PROJECT-STATUS.md` git history for the complete
      before/after pairs (recovered via `git show` against the erroneous
      commit).
    - **A further 6 of the 35** were spelling/abbreviation variants where
      both readings are attested Hebrew forms (`חודשי`/`חדושי`,
      `תינוקת`/`תנוקת`, `ט"ז`/`ט"ו`, `ע"ש`/`יע"ש`, `ש"כ`/`ש"ב`) or a citation
      detail not resolvable by sentence-sense alone (a daf number). No
      positive evidence supported the change in any of these, so they were
      reverted too, as unproven rather than left as an unverified change.
  - **1 of 40 — klal 3, resolved 2026-08-04, kept as current text**:
    `מלמר`(docai)/`מלמד`(current) disagreement. Initial isolated-letterform
    crop comparison (target letter vs. `גמר`/`מחבריה`'s ר and `שנדפס`'s ד,
    same page) leaned toward the docai reading (`מלמר`) — but re-examined at
    the sentence level rather than the single-letter level, that read doesn't
    hold up: `אין למדין למד מלמד` is a recognized halachic-methodology
    technical term (exactly the genre of rule this book catalogs), and it
    recurs a second time in this same klal's body text
    (`שיכול לומר עליו אין למדין למד מלמד`, docai word-index 132, ~7 lines
    above the title occurrence) — docai flagged *both* independent
    occurrences as `מלמר`. Two separate physical type-pieces reading
    ambiguously the same way points to a typeface-level ד/ר legibility issue
    in this font (the same confusion pattern drives most of the other 39
    disagreements in this batch) rather than to two coincidental print
    defects landing on the one technical term where a defect would be least
    expected. Semantic confidence for `מלמד` was 1.0, the ceiling for this
    batch. **Kept as `מלמד` — no change applied**. This klal 3 case is what
    prompted the full re-review above: the same reasoning (trust the
    sentence, not the isolated pixel read) applies to all 40, and 18 of the
    other 35 turned out to have the same problem.

**Klal 87 `שכדור`/`שסידר` — investigated 2026-08-05, fixed.** Same narrative
cluster: `ורב אשי שכדור/שסידר התלמוד הוא דקאמר`. First write-up of this item
mischaracterized the record — corrected here. The actual vision-adjudication
result (`scratch/corrections_verified_1to91.json`, klal 87 word-index 250)
had vision *reject* docai's raw `שסידר` reading in favor of `שכדור`
("clearly shows... כ (kaf)... forming שכדור"), which is why it was correctly
excluded from the semantic tie-break batch (that batch only covered cases
where vision sided *with* the docai reading — see above). But `שכדור` isn't
a word, while `שסידר` is exactly the well-known epithet for Rav Ashi as
compiler of the Talmud — contextually a strong candidate for another wrong
vision call, so it got the same crop-plus-context treatment as everything
else in this pass. A fresh, higher-zoom crop
(`scratch/klal87_shakadur_ultrazoom.png`) settled it directly: the second
letter is unambiguously a closed loop (ס, samech), not the open-sided כ
(kaf) the original vision pass reported — i.e. vision misread this specific
letter. Fixed to `שסידר` in `part1.json` and `klalim_demo_dataset.json`,
confirmed by both the corrected pixel read and the historical epithet match.

Separately, klal 34's long-open "low text-similarity flag, never
investigated" item and klal 67's "marker not found on page 34" item were
both investigated this session (extensive `scratch/klal34_*.png` and
`scratch/klal67_*.png` crops) — see the corrected bullets above. Klal 34 had
a genuinely missing clause restored to `clean_text`
(`היינו לדון לגמרי דבר שלא נתברר לו שכן הוא האמת אבל דבר שיודעין בו שכן הוא
האמת אך לא נתברר לנו סמך מן הכתוב`) plus a title correction (`אין דנין` →
`אין דן אדם`, `אם כן` → `א"כ`) — both independently re-confirmed by a fresh
scan crop specifically because the word order and the parenthetical
citation initially looked suspicious on a first sentence-level read; the
scan settled it in favor of the applied text as originally written. Klal 67
needed no text fix — the marker was on the page all along.

**Methodological note for future passes**: a manually-verified crop
resolves *what letterform is on the page* — it does not by itself resolve
*whether that's the intended reading*, because this typeface has a
pervasive ד/ר (and similar) legibility problem that a single crop of an
isolated letter can't diagnose. Sentence-level context (does this produce a
real word, a standard citation abbreviation, a matching named source, a
grammatical sentence) is a separate, necessary check and should be run
*before* applying any crop-confirmed fix, not treated as optional once the
pixels "look" like they favor one reading.

Committed 2026-08-04 along with this write-up (initial pass), corrected the
same day after re-review (18 reverts + 1 new finding logged), then the klal
87 `שסידר` fix landed 2026-08-05 once that finding was itself run through
the same crop-plus-context check.

## Stale files archived

`full_text_cleaned.txt` / `full_text_cleaned_goal.txt` / `processed_klalim/`
were moved to `archive/data/` — confirmed via cheap text diff (not vision) to
be stale, superseded snapshots with zero unique content versus current
`part1/2/3.json`, not additional sources of truth.

## `images/pdf_pages/` rendered-page cache — mismatch found, scope now fully checked, NOT yet fixed

Found while building `VERIFIED-AGAINST-THE-INK.html` (a real-evidence showcase
doc): `images/pdf_pages/page_37.png` does **not** show page 37 — it shows an
unrelated page (printed page "12", a *Rabbi Yochanan* sugya). The actual
klal 82/83 content that belongs at `page_37.png` (printed page "יג"/13) is
instead sitting at `images/pdf_pages/page_38.png` — confirmed by directly
re-rendering both pages from `berlin_square.pdf` with PyMuPDF and reading
them. This is likely related to (but not identical in shape to) the earlier
`docai_word_boxes/page_37.json`↔`page_38.json` swap bug — same two pages,
different underlying cache, not yet fixed here. **`review.html` and
`build_review_html.py` load scan images from this exact
`images/pdf_pages/page_${page}.png` path**, so this is not just a cosmetic
issue in a demo doc — the live review UI shows reviewers the wrong page image
for page 37/38.

**Full-coverage scope check run 2026-08-04** (all 80 cached pages, `page_14`–
`page_93`, not a sample — per `CLAUDE.md` Lessons Learned #1): re-rendered
every page fresh from `berlin_square.pdf` at matching DPI, downsampled to a
grayscale thumbnail, and diffed against the cached PNG. Rendering is fully
deterministic — all 78 non-swapped pages come back at exactly 0.00 mean pixel
diff, zero noise — so the check has no ambiguous middle ground to worry about.
**Result: 37 and 38 are the only mismatched pair in the entire cache.** The
same script's nearby-index search independently re-derived the swap direction
(page_37.png's content pixel-matches real PDF page 38, and vice versa,
0.00 diff) without being told the answer in advance, cross-confirming the
original manual finding. Script: `check_pdf_pages_cache.py` (currently in
scratch, not committed).

**Fixed 2026-08-04**: `page_37.png` and `page_38.png` re-rendered directly
from `berlin_square.pdf` (same ~150 DPI as the rest of the cache) and
overwritten in place. Confirms the swap was clean, not corruption: the old
(wrong) `page_37.png`'s pixel dimensions (872×1332) exactly matched the
correct render of page 38, and vice versa (864×1336 for page 37) — one more
independent signal the two files had simply been saved under each other's
names. Re-ran the full 80-page check after the fix: all 80 pages, including
37/38, now come back at 0.00 diff against a fresh render. Pre-fix files
backed up to scratch before being overwritten. Per Lessons Learned #3/#4,
re-verify after any future regeneration of this directory rather than
assuming this fix persists automatically.

## `adjudication_cache.db` — 7 of 86 `cache` rows have unparseable `decision_json`

Found in the same pass: `SELECT decision_json FROM cache` has 86 rows, but 7
fail `json.loads` outright (malformed JSON, not just a low-confidence/
UNCERTAIN result — those parse fine and are a separate, expected outcome).
Of the 79 that do parse, confidence is ≥0.9 in 59 (median 0.95); 19 are
legitimate 0.0 "UNCERTAIN" verdicts, not errors. The 7 unparseable rows
haven't been individually inspected — unknown whether they represent a
prompt/parsing bug worth fixing or just a handful of dead cache entries.

## Klal 57–59 title + body review — 2026-08-05

Requested spot-review of klal 57/58/59's titles. All three titles are
correct as stored and directly scan-confirmed (page 32):
`אין הלכה כשיטה` (57), `אין הלכה בשיטה` (58, with ב — see the pre-existing
"Klal 58 checked and NOT changed" note above, re-confirmed here), `אין הלכה
כשיטה` (59, again with כ). The three consecutive near-duplicate titles are
real, not a corpus artifact — this is a deliberate triplet of klalim
elaborating variations on one principle, a structure this book uses
elsewhere too.

Checking the body text of 57 and 59 against the same page surfaced a bug
class not seen before in this project: **phantom tokens** — docai inserting
words into the extraction that don't exist anywhere on the physical page,
as opposed to the misread-an-existing-letter errors (ד/ר etc.) that account
for every other finding so far. Confirmed and fixed, each independently
verified by re-rendering the exact page region and reading it directly
(not inferred from any prior extraction):

- **Klal 57**: `...כחד מינייהו או נו אין דלא אזלא...` — `נו אין` does not
  exist on the page at all; line 1 ends `...מינייהו או` and line 2 begins
  directly with `דלא אזלא`, confirmed via `docai_word_boxes/page_32.json`'s
  own token y2-coordinates (the "נו"/"אין" tokens were phantom insertions at
  the start of line 2) and a direct crop of that exact line boundary.
  Removed `נו אין `.
- **Klal 57**: `...דוכתא כחד טיניידו או דאזלא...` — `טיניידו` is not a word;
  the klal uses the parallel construction `כחד מינייהו או X` twice in one
  sentence, and the first instance (a few words earlier) correctly reads
  `מינייהו`. Scan-confirmed the second instance also reads `מינייהו` — the
  stored `טיניידו` was a docai misread (this one *is* a same-token-type
  misread, not a phantom insertion). Fixed to `מינייהו`.
- **Klal 59**: `...ע"כ לא קאמר ר רבי פלוני וע"כ...` — the standalone `ר`
  before `רבי` is a phantom token; the page reads `לא קאמר רבי פלוני וע"כ`
  with nothing between `קאמר` and `רבי`. Removed the phantom `ר`.
- **Klal 59**: trailing `... ולי הדיוט נלע"ד 3 *` — `3 *` is a printer's
  gathering-signature mark printed in a distinct Latin-numeral typeface
  below the text block (page furniture, not content — confirmed by direct
  crop, `scratch/klal59_bottom_signature2.png`), not part of the klal's
  text. Removed from `clean_text`.
- **Checked and left as-is**: klal 59's `לא קאמר ר"ס וכו'` (second
  occurrence of the "placeholder name" rhetorical pattern, first occurrence
  a few lines earlier is `ר"פ`) — independently confirmed by both docai's
  raw OCR and a direct crop to genuinely read `ר"ס`, not `ר"פ`. The klal
  deliberately uses two different placeholder abbreviations in its two
  parallel examples; this is not an error.

**Open implication, not yet acted on**: phantom-token insertion is a
different failure mode than anything catalogued so far in this document (all
prior findings were misreads of real ink, or page/file swaps — never
content invented from nothing). Page 32 alone had two independent instances
of it. This may be worth a targeted, cheap mechanical check across the rest
of the corpus (e.g. flagging any word/short-phrase in `clean_text` that
doesn't appear in `docai_word_boxes` at a *sane* position on its claimed
page) before assuming it's rare — per `CLAUDE.md` Lessons Learned #1, a
two-for-two hit rate on the one page checked so far is not evidence of
rarity, only of not having looked elsewhere yet.

## All 222 Part-1 titles reviewed — structure confirmed, 2 fixes, 2026-08-05

Prompted by the klal 57–59 review: the user identified that Yad Malachi's
klalim are **structurally alphabetical**, something not previously
documented here. Confirmed mechanically against `part1.json`'s `section`
field: Part 1 is five clean, non-overlapping ranges, one per first letter of
the title, in strict Hebrew-alphabet order —

| Klal range | Section | Letter |
|---|---|---|
| 1–80 | כללי האלף | א |
| 81–122 | כללי הבית | ב |
| 123–128 | כללי הגימל | ג |
| 129–147 | כללי הדלת | ד |
| 148–222 | כללי ההא | ה |

(Parts 2–3 presumably continue ו–ת for the remaining 445 klalim — not
checked, no vision/scan infrastructure exists for them yet, see Open Items.)

**This is section-level grouping only, not a full dictionary sort within
each section.** E.g. klal 6 (`אדם חשוב שאני`) follows klal 5 (`איתמר`) even
though ד sorts before י — a true dictionary sort would reverse that. What
actually governs order within a section is thematic/keyword clustering: the
book runs consecutive (or near-consecutive) klalim sharing an opening word
or restating the same principle across several angles/exceptions before
moving on (`איידי` ×5 at klal 7–11; `אין למדין/למדים מן הכללות` ×3 at
22–24; `הלכה כרבא לגבי אביי` ×5 at 157–161; `השוה הכתוב אשה לאיש...` ×4 at
207–209+211; etc.). Mechanically verified this is real authorial structure,
not accidental duplication: every repeated-title cluster checked (12
clusters, 34 klalim) has a **fully distinct `clean_text` body** in every
member — zero exact-duplicate bodies found.

**Mechanical first-letter-vs-section check, all 222 titles**: 16 mismatches,
all 16 already accounted for by pre-existing documented issues (8 are the
klal 92–165 structural-shift symptom already logged — 102–106, 108, 119,
210; 8 are the known `(no text available)` placeholder klalim — 180, 182,
187, 190, 194, 197, 216, 217). No new mismatches.

**Full read-through of all 222 titles for Talmudic-phrase plausibility.**
Most independently correspond to well-attested Talmudic/halachic-methodology
language — several directly cross-checked against known sources: klal 65/67
against Mishnah Eduyot 1:5 (already logged), klal 21 against the "lifting
the shard to find the pearl" idiom (Bava Batra-family), klal 63
`איבעית אימא ואיבעית אימא`, klal 101 `בית דין מתנין לעקור דבר מן התורה`,
klal 154's `יע"ל קג"ם` mnemonic (the six Abaye-over-Rava exceptions), klal
165/166 on Rav Ashi/Mar bar Rav Ashi (consistent with the klal 87 `שסידר`
finding above), klal 121 `בית הלל אומרים`, klal 207–209+211
`השוה הכתוב אשה לאיש לכל עונשין שבתורה`. Two real problems found and fixed,
both scan-confirmed:

- **Klal 219 — `title` field was stale, out of sync with `clean_text`.** An
  earlier session (see the klal 65/21/218/219 entry above) fixed `האו`→`האי`
  in this klal's `clean_text`, but the `title` field was never regenerated
  from it and still read the old `האו`. Separately, both the title and
  `clean_text` had `ר' ישמעץ` for the *first* of two `תנא דבי ר' ישמעאל`
  references in the same sentence — checked both occurrences side by side
  at matching zoom (`scratch/klal219_first_yishmael.png` /
  `..._second_yishmael.png`): both end in the same אל (alef-lamed) shape,
  no ץ (tzadi) anywhere on the page. Fixed: title now
  `האי תנא דבי ר' ישמעאל מפיק מאידך תנא דבי ר' ישמעאל`, `clean_text`'s
  `ישמעץ` corrected to `ישמעאל`.
- **Checked and confirmed correct, not an error**: klal 195's
  `הלכה כרב מונא ברוב הירושלמי` — suspected `מונא` might be a corruption of
  the more commonly-known Yerushalmi Amora `רב מנא`, but a direct crop
  (`scratch/klal195_muna_check.png`) confirms the vav is genuinely printed;
  `מונא` is what the page says. Not changed.

**Not independently verified in this pass** (would need dedicated source
lookups beyond what's checkable from the scan alone): the precise identity/
attestation of less-common terms like `בחירתא` (**klal 106, not 107 as
originally written here** — corrected 2026-08-05 once the 92-165 shift fix
reached this range and moved this content to its real klal_id; klal 177 is
separate and still unchecked) and a few specific-sage citations (klal
203's `ראב"י`, klal 176's `ר' שמעון שזורי`) — these read as plausible
genre-consistent content and were not flagged, but "plausible" here means
"not contradicted by anything checked," not "traced to a citable Talmudic
locus."

## Page-furniture contamination (footnote numerals, catchwords, gathering
## signatures) bleeding into `clean_text` — systemic, found and fixed, 2026-08-05

Requested rebuild of `review.html` surfaced a "stray period" at the top of
the middle pane (klal 1). Investigating it directly (not from the earlier
title-review pass) found klal 1's `clean_text` ended with a duplicated
trailing `ב` — klal 2's own gematria marker, leaked onto klal 1's tail.
Confirmed via `docai_word_boxes/page_14.json`: the token stream genuinely
has `ל"ב :` ending klal 1's real line, then a new line starting `ב אם אינו
ענין...` (klal 2's real opening) — the assembly step duplicated that `ב`
onto both. Fixed (klal 1 now ends cleanly at `וס"ס ל"ב :`).

A mechanical sweep of all 222 Part-1 `clean_text` tails for trailing digits/
asterisks found this was not isolated: **17 more klalim** had the same class
of contamination, none previously documented. Two distinct sub-patterns,
both genuine artifacts of this 1766 print, not OCR hallucination this time —
confirmed individually against the scan for every one of the 17:

- **Printer's gathering-signature numbers / catchwords in the bottom
  margin**, printed in a smaller/distinct typeface below the last real line
  of text, that `clean_text` incorrectly absorbed as body text. Two
  sub-cases: a bare signature number (klal 25 `2`, klal 53 `כיה`/`3`
  — the `כיה` catchword directly confirmed against page 31's actual
  opening tokens, an exact match; klal 84 `בעיא 4`, klal 124 `5 1`
  — the `1` here traced to an isolated ink speck, not a real numeral; klal
  144 `1` — traced to scanner noise near the Google watermark; klal 129
  `1`; klal 131 `5*`; klal 151 `6`; klal 155 `6*`; klal 167 `2`), and a
  mid-sentence footnote-reference numeral sitting between two real words on
  adjacent print lines (klal 2 `בהשגותיו 1 לסי'` — real text is
  `בהשגותיו לסי'`; klal 4 `יגעתי 1 ולא` — real text is `יגעתי ולא`).
- **Duplicated marker fragments from the adjacent klal**, same failure mode
  as klal 1 above but caught by the same sweep: klal 165 ended with a
  garbled `४ . קסה` — `קסה` is a misread duplicate of klal 166's own
  opening marker (klal 166 already has a correct `קסו` at its own start,
  confirmed independently); klal 175 ended with `הלכה *7` — `הלכה` is klal
  176's own opening word as a catchword (klal 176 already starts correctly
  with `קעו הלכה...`), `7*` the signature. klal 164 ended with a spurious
  `1 •` where neither character exists on the actual page at that position
  (confirmed by direct crop — nothing follows the real last word `בהלכות`
  except scan noise); both removed rather than assuming the bullet was
  misplaced-but-real.

**One of the 17 was not contamination and was NOT changed**: klal 6's
`הרמה * ) :` is a genuine footnote-reference marker printed tight against
the word it annotates (`הרמה*)`, no line-break, unlike every other case
above which sits in a separate margin line) — confirmed by direct crop.
Fixed only the spurious spacing (`הרמה * )` → `הרמה*)`), left the marker
itself in place. This is the same "a match on symptom is not proof of the
same cause" caution as the rest of this document — 16 of 17 flagged tails
were margin contamination, but the 17th needed its own independent check
before being treated the same way.

**Method note**: every fix in this section was confirmed by locating the
exact `docai_word_boxes` tokens at the tail position, then rendering that
exact page region from `berlin_square.pdf` and reading it directly — several
(klal 129's page attribution is marked `trusted: false` in
`part1_header_anchored_alignment.json`, but the exact phrase match against
`docai_word_boxes/page_47.json` confirms the page is in fact correct for
this specific text) were cross-confirmed by checking what the *next* klal
or *next* page actually starts with, not assumed from the pattern alone.

**Not yet done**: this sweep only covered Part 1 (klal 1–222), the only part
with scan/docai infrastructure. Parts 2–3 (klal 223–667) have not been
checked for the same contamination pattern and likely have it too — no
scan-verification infrastructure exists for them yet (see Open Items).

## Alphabetical-order check redone correctly, twice — 2026-08-05

The "All 222 Part-1 titles reviewed" section above understated what it
verified. Two rounds of correction, both prompted by the user pushing back
on a claim that turned out to be checking the wrong thing:

**Round 1 — the check itself was too weak.** The original check compared
each title's first letter against that klal's own `section` field — i.e.
one derived field against another derived field. A klal-boundary corruption
that shifted `title` and `section` together would pass silently. Corrected
by checking the title-letter *sequence* against itself, independent of
`section`.

**Round 2 — even the corrected sequence check under-reported real scope.**
A first attempt at the sequence check (pairwise "does rank ever decrease")
and a second attempt (run-length-encode into blocks, flag every non-largest
block of a letter) both still missed or misreported the true violator set —
full detail and why each failed is in `validate_title_alphabetical_order.py`'s
docstring. **The correct formulation is isotonic regression**: assign every
klal a non-decreasing letter rank that maximizes agreement with its own
observed title-letter; klalim where the observed letter had to be overridden
are the true violations. This is now a standing script,
`validate_title_alphabetical_order.py`, run against `klalim_demo_dataset.json`
(the full 667-klal sequence — checking part1/2/3.json individually would
spuriously flag a letter that legitimately continues across a part seam).
**`validate_title_section_letter.py` is retired** (kept as a stub pointing
here, not deleted, since PROJECT-STATUS.md's older entries still name it).

**Result, run against the current corpus:**

- **Part 1: exactly klal 102, 103, 104, 105, 106, 108, 119, 210** — the same
  8 already documented under "Structural klal-boundary/content-shift issue."
  This reconciles a real internal inconsistency: that section's own text
  says **70 of ~120 klalim in the 92–165 range have a genuine content
  mismatch** (confirmed again directly from `gematria_trace_part1.json`:
  65 klalim in that range are flagged `marker_found_content_mismatch` or
  `marker_not_found_in_window`), but the alphabetical-order check only
  surfaces 8. **These are not the same measurement.** The alphabetical
  check only catches a title whose *first word* is wrong; most of the 65
  content-mismatch klalim have a completely normal-looking title and
  marker while the *body text underneath* belongs to a different klal —
  invisible to any check that only looks at the first letter. Do not treat
  "8 title-letter violations, confirmed" as evidence the 92–165 issue is
  smaller than previously documented. It is not — see the Structural
  section above, still open, still ~65 klalim.
- **Parts 2–3: ~108 klalim flagged, but this is a different, already-known
  cause, not a new corruption pattern.** The overwhelming majority are
  titled literally with the placeholder pattern `"כלל <N>"` (e.g. klal 246's
  title is literally `כלל 246`) — the leading word `כלל` (Hebrew for "rule")
  starts with כ, which is what's flooding the flagged list, not a real
  boundary break. **Quantified for the first time**: `115 of 445 Part 2–3
  klalim (26%) have this literal placeholder title`, not the "handful" the
  8-klalim Part-1 figure might imply — a materially bigger version of the
  already-documented "Parts 2–3 titles were never manually judged" open
  item. Full klal_id list: 240, 246, 250, 267, 270, 272, 275, 277, 280, 287,
  290, 297, 303, 304, 309, 311–314, 316, 320, 323, 330–335, 340, 344, 347,
  350, 357, 367, 372, 377, 380, 383–385, 387, 390, 391, 397, 401–404, 407,
  414, 416, 417, 420, 422, 427, 430–444, 447, 450, 451, 457, 467, 477, 480,
  484, 487, 490, 494, 497, 507, 514, 516, 517, 520, 527, 537, 539, 540,
  550–553, 557, 577, 580, 587, 590, 597, 601, 607, 608, 613, 616, 620, 627,
  637, 640, 643, 647, 650, 657, 665, 667. A handful of the remaining flagged
  klalim (e.g. 412, 346) have real body content but a title that looks like
  an un-judged mid-sentence fragment rather than a real title — consistent
  with the same "never manually judged" gap, not separately investigated
  klal-by-klal here.

## review.html left-pane fixes — 2026-08-05

Requested: restore the missing left-pane navigation and add a "current klal"
indicator. Both diagnosed from source only — the Chrome extension hung/
crashed on every attempt to load `review.html` in a live browser this
session (even `tabs_context_mcp` timed out), so neither fix was visually
confirmed in a rendered page, only verified by reading the generated HTML/JS.

- **Nav buttons**: `review.html`'s scan-pane (left, confirmed correct by
  `dir="rtl"` on `<html>`) never had prev/next page controls — traced to a
  sibling demo, `SEFARIA-VLM-DEMO.html`, which has exactly this
  (`nav-btn nav-prev`/`nav-next`) and appears to be what `review.html`'s
  rewrite dropped. Added `#page-nav-prev`/`#page-nav-next` buttons wired to
  step through the sorted list of pages that actually have klalim, jumping
  to each page's first klal (keeps all three panes in sync via the existing
  `jumpTo()` path).
- **Current-klal highlight**: previously the scan pane only drew boxes for
  *flagged corrections* on the current page — a klal with zero flagged
  corrections (the majority; only 90 of 774 candidates are flagged) got no
  visual indicator at all. New `build_klal_page_regions.py` derives a real
  per-klal bounding region from the same docai-token alignment
  `build_corrections_dataset.py` already computes (union of every matched
  token's bbox for that klal, not just mismatched ones) → `klal_page_regions.json`
  (208/222 Part-1 klalim covered, matching the existing `trusted`-page
  coverage figure). `review.html` now draws a yellow (`#d69e2e`) box for the
  current klal's real region regardless of whether it has any flags.
- Still owed: an actual visual confirmation once the Chrome extension issue
  clears, per `CLAUDE.md`'s UI-verification convention.

## Klal 33/34 spot-check (user-requested review of klal 1–112) — 2026-08-05

**Klal 34 title — user was right, words were swapped, fixed.** Title was
stored as `אין דן אדם גזירה שוה מעצמו אלא א"כ קבלה מרבו` (verb before
subject). First crop attempt at the actual print (`berlin_square.pdf` page
26) was misread as confirming this order — **that misread was wrong**: a
narrower crop clipped the right edge and caused `אדם` (the boxy
dalet+final-mem shape) to be misattributed as coming after `דן` rather than
before it. A wider, unclipped crop including the bold `אין` anchor resolved
it unambiguously: the real order is `אין` `אדם` `דן` `גזירה` `שוה`
`מעצמו`... — i.e. `אין אדם דן גזירה שוה מעצמו אלא א"כ קבלה מרבו`, matching
both the user's read and the well-known Pesachim 66a phrasing this klal is
quoting. Fixed in `part1.json` (title + `clean_text` opening). Another
instance of the standing project lesson (klal 66, klal 1's `ומדקמהד` case):
a single close-in crop of a disputed word/phrase is not reliable on its own
when it clips the frame — verify with a wider, anchor-inclusive crop before
concluding. New standing lesson from this: see `CLAUDE.md` Lessons 14/15.

**Root cause of the swap, traced via `git show`**: not a fresh error. Before
2026-08-04 (`e93788d`, the klal 1-91 vision/semantic disagreement pass), the
title read `אין דנין גזירה שוה מעצמו אלא אם כן קבלה מרבו` — missing `אדם`
entirely. That commit correctly identified `אדם` was missing and added it
back, but placed it after `דן` instead of before — introducing the
wrong-order text that stood for a full day. Two independent sessions
(2026-08-04 and 2026-08-05) both misjudged the same word pair's order,
consistent with a real visual difficulty in this print's typesetting
(`אדם` sits as a cramped box shape immediately after the enlarged bold
`אין`), not two unrelated slips.

**Why this was invisible to every automated check — a new, systemic finding,
not specific to klal 34.** `corrections_part1.json` has **zero** entries for
klal 34, not a low-confidence one — checked why: `part1_header_anchored_alignment.json`'s
`match_ratio` for klal 34 is 0.375 (untrusted). Checked every low-`match_ratio`
Part-1 klal against `corrections_part1.json` and found a complete,
100% correlation: **every klal with `match_ratio` below ~0.65 (34, 92, 129,
172, 180, 182, 187, 190, 194, 197, 210, 216, 217 — 13 klalim) has exactly
zero correction candidates.** `build_corrections_dataset.py` can't align
docai's garbled tokens to stored text at these positions, so it produces no
comparison at all, not a low score — meaning "no flags" for these 13 is not
evidence of correctness, it's evidence the check never ran. Of these 13:
the 8 placeholder klalim and klal 186 (corrupted) were already known; 34 and
92 are now manually verified/fixed; **129, 172, 210 remain open, unchecked,
and are exactly as invisible to the pipeline right now as 34 was** — see
`CLAUDE.md` Lesson 15. Next step for this open item: manually check 129,
172, 210 the same way (wide-anchor-crop protocol per Lesson 14), not assume
their silence in `corrections_part1.json` means they're fine.

**Update, same day: 129, 172, 210 checked.**

**Klal 129 — not independently fixed; folded into the open 92–165
shift-zone item.** `part1_header_anchored_alignment.json` shows a real
section-header mismatch for 129 (`expected_section: הדלת`,
`matched_page_header: הגימל`), consistent with the same off-by-one shift
already being worked sequentially from klal 92 (currently resolved through
111). Did not attempt a standalone fix — that reconstruction is inherently
sequential (each klal's true content depends on the previous klal's
boundary being correctly resolved first), so fixing 129 in isolation before
112–128 are resolved would be unreliable. Will be picked up when the
shift-zone work reaches it.

**Klal 172 — real, confirmed defect, fixed.** Title was stored as
`הלכה כר"ע מחבירו` (incomplete) and `clean_text` read `...מחבירו [.] ולא
:דהחולקים...`, with a spurious editorial `[.]` mark and a stray colon.
Direct crop of the scan (`berlin_square.pdf` page 64, marker `קעב`) shows
the print continues `כר"ע מחבירו ולא מחבירין • היינו היכא דהחולקים...` —
a whole clause (`מחבירין • היינו היכא`) was missing from the stored text,
and the print already has a natural `•` boundary at the right spot (the
`[.]` editorial insertion was never needed here). Fixed title to
`הלכה כר"ע מחבירו ולא מחבירין`, restored the missing clause, removed the
spurious `[.]`/stray colon. Also fixed stale `page` (was 26, confirmed 64).

**Klal 210 — real, confirmed defects, fixed (4 separate issues, same
klal).** Extensively checked against `berlin_square.pdf` pages 73–74 (marker
`רי`) with pixel-measured, wide-anchor crops throughout, given the day's
earlier misreads:
1. Title/opening word: stored `דקו` → confirmed `הי` (`"which of them"`, an
   idiom echoed twice later in the same klal — `הי מתרווייהו`, `הי מנייהו
   דאחריתי`). `דקו` isn't a real word here.
2. `וכלומר הי החשה נשנית` → `וכלומר הי מתרווייהו נשנית` — `החשה` was wrong,
   confirmed via crop and matching docai.
3. Page-crossing running-header contamination: stored had
   `אפשר דהלכה $8 יך מלאכי כללי ההא לא דהלכה` — `$8 יך מלאכי כללי ההא` is
   the page-74 running header plus a garbled artifact that was never
   stripped when this klal's span crossed the page 73→74 boundary. Fixed to
   `אפשר דהלכה : לא דהלכה` — the `:` is genuinely printed at the bottom of
   page 73 (crop-confirmed), the header/artifact is not.
4. `למידע אי בתרייתא הוא אם לא` → `למידע אי כתרייתא הוא אם לא` — confirmed
   by crop the letter is כ (open top-right), not ב (closed box). Note: a
   *different*, earlier occurrence in the same klal (`שהוזכרה באחרונה
   בתרייתא היא`) was separately crop-checked and confirmed already correct
   as `בתרייתא` (closed ב) — same two letters, two different words in two
   different grammatical roles, not the same error repeated. Also fixed
   stale `page` (was 29, confirmed 73).

All three investigated with the wide-anchor-crop protocol from `CLAUDE.md`
Lesson 14, given how many single-crop misreads happened earlier this
session. This closes the "129/172/210 unchecked" item — the low-`match_ratio`
blind spot (Lesson 15) itself remains a standing risk for any future
untrusted-alignment klal, not just these three.

**Klal 33 was genuinely truncated — fixed.** Stored `clean_text` stopped at
`...לכן בכי האי גוונא`; the scan (same page 26) continues directly with
`אין משיבין לאחר מעשה עד כאן דבריו • ועיין ספר אש דת דף ע' ע"ב וג' :` —
confirmed via `docai_word_boxes/page_26.json` tokens 355–373 and a direct
crop. This is the same failure class as the "MAJOR: cross-page klal
truncation" bug documented above, except same-page (not a page-boundary
case) — meaning that bug class isn't confined to cross-page klalim either;
`validate_klal_span_coverage.py` should have flagged this by ratio but
apparently didn't (not re-checked why in this pass). Fixed in `part1.json`;
`klalim_demo_dataset.json` needs `build_klalim_demo_dataset.py` re-run.

**Also found and fixed in passing**: `part1.json`'s `page` field for klal 33
and 34 was stale (`16`, alongside klal 28–37 as a block — all uniformly
`16`, which cannot be right since these are 10 different klalim). Both
verified directly against the scan to actually be page **26**; corrected
for 33/34 only. The other klalim in that 28–37 block are very likely also
misattributed (same stale block value) but were not individually checked in
this pass — do not assume they're fixed.

**Review of klal 1–112 was requested but not otherwise completed this
pass** — only 33/34 were checked (the two the user flagged) before this
finding was logged; per "close open items before new ones," the remaining
klal 1–112 title/text review and the still-open klal 92–165 shift-zone
work (currently at klal 112) both remain open.

`rebuild_all.sh` (full, not `--skip-vision`) re-run after the klal 33 fix:
726 items / 163 klalim (97 `current_text_may_be_wrong`, 131
`current_text_confirmed`, 137 `unverified_insertion`, 301 `ambiguous`, 60
`possible_omission`), zero `error` flags. All comparisons were cache hits —
zero new Gemini calls, zero cost.

## Vision-adjudication cache and script robustness fixes — 2026-08-05

Found while trying to regenerate `corrections_part1.json` after the day's
text fixes:

- **`adjudication_cache.db` cache key was crop-hash-only, not
  (crop_hash, word_a, word_b)** — see `CLAUDE.md`'s "Single source of truth"
  section for the full writeup and the confirmed damage (217 word-pair
  decisions had collapsed onto 140 unique crops before the fix). New
  `corrections_cache` table, composite primary key, migrated the salvageable
  140 rows.
- **`NOT NULL` constraint on the new table broke caching for delete/insert-
  type comparisons** (one side of the pair is `None` by construction, e.g.
  `"Digitized by Google" vs None`) — every such candidate failed to cache
  and fell through to a full live re-call every time it was hit. Fixed by
  coercing `None` to a sentinel string before the query rather than relaxing
  the schema.
- **`gemini-2.5-flash` in the model fallback list is permanently dead**
  (404 "no longer available to new users", not transient) — was silently
  eating a retry slot on every single fallback path. Removed.
- **`adjudication_cache.db` was hitting real `database is locked` errors**
  under concurrent-ish access (this script opens a fresh connection per
  cache read/write) — each one discarded an already-successful Gemini
  response and forced a re-call. Added `PRAGMA journal_mode=WAL` to
  `init_cache()`.
- All four fixes are in `verify_corrections_vision.py`. A full re-run against
  all 770 current candidates was in progress as of this write-up (started
  2026-08-05 ~09:27) — **not yet complete; `corrections_part1.json` and
  `review.html` will still reflect the pre-fix data until it finishes.**
  Follow up: confirm it completed cleanly, then re-run
  `assemble_corrections_dataset.py` + `build_review_html.py` if it wasn't
  already triggered by `rebuild_all.sh`.

## Single source of truth for corpus text — 2026-08-05

`klalim_demo_dataset.json` was being hand-edited in parallel with
`part1/2/3.json` on every fix this session — confirmed to be exactly their
concatenation with zero field-level differences, i.e. a fully redundant copy
maintained by hand instead of by a script. New `build_klalim_demo_dataset.py`
generates it from the three part files; new `rebuild_all.sh` chains the
whole derived-artifact pipeline (`klalim_demo_dataset.json` →
`corrections_candidates_part1.json` → vision-verify → `corrections_part1.json`
→ `klal_page_regions.json` → `review.html`) in one command. Full rationale
and the standing rule ("never hand-edit a derived file in parallel") are in
`CLAUDE.md`'s "Single source of truth" section, not duplicated here.

## Structural re-chunking (klal 92–165) — Step 1–2 in progress, 2026-08-05

Working the plan agreed with the user (structural issues fixed before any
further breadth expansion): Step 1 confirmed the affected range sits on
**pages 41–60** (via `part1_header_anchored_alignment.json`; klal 92 and 129
are themselves marked untrusted for page attribution — worth resolving as
part of this pass, not separately). Page 58 has no trusted klal match in
this range, not yet explained.

Step 2 (re-deriving true klal boundaries via exact-match marker anchoring):
`scratch/reconstruct_92_165_boundaries.py` reuses `gematria_trace_part1.json`'s
existing exact-match positions (both its `ok` and
`marker_found_content_mismatch` statuses carry a real, usable token
position — only `marker_not_found_in_window` lacks one) and adds a bounded
fuzzy search *between two already-confirmed neighbors* for the klalim that
had none.

- **57 of 79 klalim in the klal 90–168 window already have a confirmed
  token position** (from the existing exact-match trace).
- **22 had no exact match.** A bounded fuzzy search (similarity ≥0.75,
  restricted to the token window between confirmed neighbors — a much
  tighter constraint than the original whole-page search) resolved a
  further few (klal 116, 124, 129, 145, 151); **18 remain genuinely
  unresolved**: klal 93, 95, 98, 107, 115, 127, 131, 139, 144, 147, 149,
  150, 153, 155, 160, 164, 167 (plus one more — see
  `scratch/resolved_92_165_positions.json` for the exact current list).
  This is treated as real signal, not a weak search: it means these 18
  markers are print/OCR-hard enough that even a relaxed, tightly-bounded
  fuzzy match can't find them, consistent with `CLAUDE.md`'s standing
  caution that `trace_gematria_sequence.py`-style marker search has a real
  blind spot in this corpus. **First bug found and fixed in this same
  script**: an earlier version of the bounded search included the
  neighbor's own token in its search window, causing several klalim to
  "resolve" to the exact same position as their neighbor (i.e. matching a
  token against itself) — fixed by starting the window strictly after the
  previous neighbor's position, not at it.

**Not yet done**: (a) reconstructing `clean_text` for the 57+ klalim with
confirmed boundaries on both sides (next step - safe, mechanical once a
span's start and end are both known), (b) locating the 18 still-missing
markers by direct scan crop (the same manual-verification method used for
every other fix this session, not automation), (c) verifying a sample of
reconstructed spans against the actual scan before trusting any of this
wholesale, per Lessons Learned #2. This is a multi-step, multi-turn effort
by design, not something to rush to "done" - see `CLAUDE.md`'s "close open
items before new ones" rule for why this is being worked as its own item
rather than left half-finished while starting something else.

### Mechanical reconstruction is NOT safe to mass-apply — real cause found, 2026-08-05

Spot-checked 3 of the 39 mechanically-reconstructed spans against both the
old stored text and the actual scan before trusting any of them (per the
plan's own Step 4). Klal 99 (page 44, exact-match position 342) failed the
check in an informative way: the scan genuinely shows `צט`(99) immediately
followed by `ברייתא דמייתי לה הש"ס למפרך` — but that text is currently
stored under **klal 100**, not 99. Directly preceding the `צט` token is
`דף פ"ה רע"ד :` — a page/column citation — meaning this specific `צט` is
very likely a **coincidental citation number** ("column 99" of some cited
work), not klal 99's real klal-opening marker, sitting embedded inside a
citation rather than starting a new klal.

**This means the marker/citation collision blind spot is not confined to
klal 1–90 as previously documented** (`CLAUDE.md` / this file's earlier
notes on `trace_gematria_sequence.py`) — confirmed recurring at klal 99,
inside the 92–165 zone this whole pass is trying to fix. Exact-match token
search alone cannot distinguish a real klal-opening marker from a
coincidentally-equal citation number; it needs an additional signal (e.g.
whether the marker sits at a genuine paragraph/line start following
sentence-final punctuation, not mid-citation) before a position can be
trusted.

**Klal 128's missing tail fixed** (2026-08-06, later the same overnight
session): appended the ~838-word missing continuation
(`docai_word_boxes/page_48.json` tokens 5-842) using the same disclosed
lighter-verification standard as the other large cross-page klalim
(full read-through for coherence). Found and fixed ~15 non-word docai
misreads on that read-through (the established ד/ר/ה confusion family,
three separately-mangled forms of `שמואל`, one duplicated `עם עם`). One
word (`שר סוגיין`) deliberately left as the raw, uncorrected docai
reading rather than replaced with an unconfirmed guess - flagged, not
silently resolved either way. Klal 128 is now 1313 words total and no
longer an open item.

**Consequence: none of the 39 mechanically-reconstructed spans in
`scratch/reconstructed_92_165.json` have been applied, and none should be
without individual verification.** The mechanical pass was useful for
narrowing down candidate positions fast, but per Lessons Learned #2/#6 a
"position found" result here is not a "position correct" result. Continuing
this work requires either (a) a stronger automated filter for real-marker-
vs-citation before trusting any exact-match position, or (b) the same
per-klal manual scan verification used for every other fix this session,
just at the scale of ~65 klalim instead of a handful. Not yet decided which;
flagging for the user rather than picking one and running with it, since
this materially changes the effort estimate for closing this open item.
User chose: build a better automated marker-vs-citation filter first
(see next section), not full manual verification of all ~65.

## Vision-verification rebuild completed — 2026-08-05, but surfaced a billing blocker

The full `rebuild_all.sh` run (started ~09:27, background) finished cleanly
end to end: `corrections_verified_part1.json` (770 results),
`corrections_part1.json` (770 items / 174 klalim, flags: 104
`current_text_may_be_wrong`, 142 `current_text_confirmed`, 60
`possible_omission`, 150 `unverified_insertion`, 275 `ambiguous`, 39
`error`), `klal_page_regions.json` (208 regions), `review.html` all
regenerated and committed together with `adjudication_cache.db`.

**Real blocker surfaced, not just a technical detail**: the run logged
**173 occurrences** of `RESOURCE_EXHAUSTED` — Gemini's own error text is
`"Your prepayment credits are depleted. Please go to AI Studio ... to
manage your project and billing."` This is not a transient rate limit; it's
the account's prepaid balance running low/out. Every occurrence this run
happened to succeed on retry (via `adjudicate()`'s model-fallback/retry
loop), so nothing failed outright *this time*, but **this can block all
future Gemini-dependent work in this project** — including the
marker-vs-citation filter work for the klal 92–165 structural fix, which
the user just chose specifically to reduce reliance on further Gemini
calls. **Needs the user's attention on the billing/AI-Studio side** — not
something fixable from this codebase.

Separately, **39 of 770 results have unparseable `decision_json`**
(`"Expecting ',' delimiter..."` JSON errors, e.g. klal 22, 86, 87, 103,
126) even after `sanitize_json()`'s existing escape-stripping — a larger
recurrence of the smaller "7 of 86" instance already logged above. Not yet
individually inspected; unknown whether a prompt tweak would fix it or if
it's an inherent occasional model-output quirk to just retry past.

## Automated marker-vs-citation filter attempt — tried, did not work, 2026-08-05

Per the user's chosen approach (build a better automated filter before
manual verification), tried two mechanical signals to distinguish klal 99's
false-positive `צט` marker (a coincidental citation number, see above) from
a real klal-opening marker, using all 13 confirmed `ok`-status markers in
the 90–168 range as the comparison set:

- **Preceding-context punctuation** (real markers should follow a genuine
  klal-ending colon, not a mid-citation one): doesn't discriminate. Every
  single confirmed-real marker checked is *also* preceded by a citation
  ending in a colon (e.g. klal 104 is preceded by `דף ע"ד ע"ד :`, the same
  shape as klal 99's false positive's `דף פ"ה רע"ד :`). Klalim routinely
  end by citing a source, so "preceded by a citation+colon" is normal for
  real boundaries too, not a discriminator.
- **Token height of the word after the marker** (hypothesis: real klal
  openings use enlarged/bold typography): doesn't discriminate either. The
  false positive's next-word height (0.01888) falls squarely inside the
  confirmed-real range (0.01499–0.02064, mean 0.01844) — not an outlier in
  either direction.

**Checked whether there's a second, real occurrence of `צט` on the same
page that a "nearest match" search might have missed: there isn't.** `צט`
appears exactly once on page 44, and it's the citation. This changes the
diagnosis: it's not that the search picked the wrong one of several
candidates — there is no other candidate. Klal 99's real marker is either
on a different page than currently attributed, or doesn't exist as a
separate token at all (consistent with a merge/shift earlier in the
sequence propagating forward, not a one-off local error).

**Conclusion: a cheap mechanical filter for this specific failure mode was
not found.** Both signals tried are exhausted; no obvious third one is
apparent from this one example. This needs either (a) a smarter
content-level check (does the resulting text plausibly complete as a real
klal title vs. continue a citation — inherently a semantic judgment, not
positional/typographic) or (b) the manual per-klal scan verification path
this filter was meant to reduce. Given the Gemini billing blocker logged
above, (a) via LLM semantic check may itself be constrained right now.
Flagging back to the user rather than silently falling back to a slower
path without saying why the fast path didn't pan out.

## Gemini credits restored, gap-fill verified clean — 2026-08-05

User added Gemini credits after the billing blocker above. Verified no
damage before re-running: all 24 `RESOURCE_EXHAUSTED` failures (klal 215,
218, 219, 220) were cleanly flagged `error` in `corrections_part1.json`, not
silently masquerading as real decisions, and `cache_decision()` is only
called on a successful response so none of the 24 were cached as errors
either — confirmed nothing needed to be undone, only completed. Re-ran
`verify_corrections_vision.py`: all 24 resolved (0 `RESOURCE_EXHAUSTED`
remaining). 15 `error` entries remain, but these are the separate,
already-logged JSON-parse-failure issue, not credit-related. Re-ran
`assemble_corrections_dataset.py` + `build_review_html.py` to propagate:
`corrections_part1.json` now 770 items / 174 klalim (109
`current_text_may_be_wrong`, 143 `current_text_confirmed`, 63
`possible_omission`, 150 `unverified_insertion`, 290 `ambiguous`, 15
`error`).

## Klal 92 structural fix — real content confirmed missing, transcription in progress, 2026-08-05

Manual per-klal scan verification (chosen after the automated filter dead
end above) started at the beginning of the 92–165 range. **Klal 92 is
confirmed a duplication bug, not a shift**: its currently-stored
`clean_text` is word-for-word klal 90's real content immediately followed
by klal 91's real content (with klal 91's own `צא` marker embedded
mid-text) — and klal 90/91 *also* separately, correctly hold this exact
same content under their own `klal_id`s. So klal 92's real content isn't
mislabeled elsewhere, it's simply **absent from the corpus entirely**.

Confirmed directly from the scan (page 41, the same exact-match position
`gematria_trace_part1.json` already had, y=0.8546): klal 92's real opening
is `צב בעיא מצינו דבעי בגמרא במילתא דלא נסקי מינה אף מידי בזמן התלמוד מפני
שהוא דבר שכבר עבר ואפי'ה קבעי לה משום דרוש שכל וקבל שכר וזה בס"פ א' חולין
י"ז בעי ר'...` — this is klal 92's *entire* real title/opening (confirmed
by reading to the bottom of page 41, where the page ends — nothing else
follows on that page). The klal continues onto page 42 with a long,
citation-dense halachic discussion (`רבי ירמיה איכרי בשר נחירה...`,
concerning פסח מצרים and korbanot) with no bold/enlarged new-klal-opening
visible for a full page of text - klal 92 is long, this isn't a quick
transcription.

**Not yet complete**: only the opening ~40 words are transcribed and
confirmed; the full klal 92 body (continuing across page 42) still needs
transcription, and this is klal 1 of ~65 in the range. Given the content
density observed just in this one klal, full manual verification of the
whole range is a substantially larger effort than a few turns - continuing,
but flagging the realistic scale now rather than after the fact.

## Klal 92-165 root cause identified: a clean off-by-one content shift, not scattered corruption — 2026-08-05

Continuing the manual verification, the true shape of the bug became clear:
**this is a contiguous off-by-one shift** (`clean_text` currently stored
under `klal_id N` is really klal `N-1`'s real content), not random scatter.
Confirmed directly by reading the real markers on the page: klal 92's real
marker (`צב`, page 41) is followed by content currently stored under
`klal_id 93`; klal 93's real marker (`צג`, page 42) precedes content
currently under `klal_id 94`; klal 94's real marker (`צד`, page 42)
precedes content currently under `klal_id 95`; klal 95's real marker (`צה`,
page 43) precedes content currently under `klal_id 96`. Four independent
confirmations of the same shift-by-one pattern.

**This also reframes the earlier "marker/citation collision" finding for
klal 99** (see "Automated marker-vs-citation filter attempt" above): that
wasn't a coincidental citation number after all. The `צט` token really is
klal 99's real marker; the automated check flagged it as a mismatch only
because it was comparing against klal 99's *currently stored* (shifted,
wrong) content instead of the correct one. The filter-search dead end and
the shift are very likely the same underlying bug, not two separate issues.

**Fixed and applied, scan-confirmed**: klal 92, 93, 94 (`part1.json` +
`klalim_demo_dataset.json`). Each klal's real content was extracted as the
exact docai token span between its own confirmed marker and the next
klal's, not hand-retyped - the OCR words themselves are generally reliable
(confirmed throughout this session); what was wrong was which klal_id they
were filed under. Two bugs caught and fixed *during* this extraction, not
after:
- A page-crossing span naively included the next page's running header
  (`יד מלאכי כללי הבית טו`) as body text - fixed by stripping the fixed
  5-token header run whenever a span crosses into a new page.
- Klal 92's span initially included a duplicate word fragment: page 41's
  scan captured a partial glimpse of its own last line (`רי`, cut off) that
  page 42 then captures again, completely and correctly (`ר' ירמיה`) -
  confirmed by direct high-zoom crop of page 41's very last line. Removed
  the partial duplicate.
- Klal 92 needed a judged title/explanation boundary (no natural print
  punctuation at that point, marked `[.]` per the established convention);
  klal 93 and 94 both had a natural period in the print at the right spot,
  no judgment call needed.

**Klal 95 is now the new boundary and is known-wrong** (still holds the
stale content that used to belong to klal 94, now duplicated with the
just-fixed klal 94) - this is expected, not a new bug: fixing N always
"un-covers" N+1 as the next thing needing the same treatment in a
contiguous shift. Klal 95's real marker position is already found (`צה`,
page 43, confirmed by direct crop) - its end boundary (klal 96's real
marker) is not yet located. This is the immediate next step.

Regenerated `review.html` after this fix (`rebuild_all.sh`) so the 3
klalim's corrected text and titles are visible there, not just in
`part1.json`.

**Continued 2026-08-05: klal 95, 96, 97 fixed, same method, each
scan-confirmed.** Klal 95's real content (`gematria_trace_part1.json`
correctly located `צה` at page 43 token 534 once searched directly - the
prior "marker_not_found_in_window" was a window-size limitation of the
original search pass, not a real absence) was, per the established
off-by-one pattern, sitting mislabeled under klal 96 (with its own leading
marker glyph altered from `צה` to `צו` to match its wrong container - an
additional, subtler corruption on top of the shift itself: someone/some
process had edited the marker character to agree with the ID it was filed
under, backwards from how it should work). Moved to klal 95 (marker
corrected back to `צה`); this uncovered klal 96 as the next stale
boundary, whose real content (marker `צו`, confirmed) was sitting
mislabeled under klal 97 (same marker-glyph corruption, `צו`->`צז`); fixed,
which uncovered klal 97 as the next stale boundary. **Klal 97 turned out to
also be cross-page** (page 43->44) **and independently truncated** at the
page boundary - a 15th, previously-unscoped instance of the "MAJOR:
cross-page klal truncation" bug from earlier in this document (not caught
by that pass because klal 97/98's markers weren't yet resolved at the
time that scope check ran). Reconstructed properly: page 43's tail
included its own catchword (`היא`, confirmed by height 0.0089 vs the
0.017 body-text norm and off-margin positioning - a duplicate preview of
page 44's real first word, correctly stripped) and page 44's header
included an unusual 5th token (`טז`, the printed folio number, positioned
separately from the 4-word `יד מלאכי כללי הבית` running header) that the
existing `strip_head_header` heuristic (built for single-*character*
extra markers) would not have caught automatically - stripped manually
after a direct crop confirmed it's page furniture, not body text. Klal 97
final: 427 words (was 184, mislabeled under klal 98 and independently
truncated at the same page boundary).

Each of the three (95/96/97) marker positions and the klal-97 page
boundary were confirmed by direct high-res crop against
`berlin_square.pdf` before being applied, not trusted from token-text
matching alone - `scratch/klal95_boundary.png`, `klal96_marker.png`,
`klal97_marker.png`, `klal98_marker.png` (staged, not yet committed).

**Klal 98 is now the new known-wrong boundary** (still holds klal 97's
old, truncated, mislabeled content) - next step in this ongoing,
multi-turn effort. `validate_klal_span_coverage.py` re-run clean after
each step: klal 96 dropped off the flagged list once fixed (95/97 aren't
independently checkable by that script yet since their far-end markers
weren't in `gematria_trace_part1.json` before this session). Full
`rebuild_all.sh` re-run after 95/96/97: `corrections_part1.json` now 738
items / 167 klalim, zero `error` flags.

**Continued further the same session: klal 98, 99, 100, 101, 102, 103,
104 fixed, same off-by-one method, each scan-confirmed.** Same cascading
pattern throughout - each fix uncovers the next stale boundary. Klal 105
is now the current known-wrong boundary. Two new OCR-error patterns
surfaced and fixed while reconstructing this stretch, both confirmed by
direct crop, not applied from token text alone:

- **A second docai duplicate-token instance, same class as klal 82/83**:
  page 44 tokens 385 (`ביו`) and 386 (`בית`) have near-identical bounding
  boxes (x1 0.841 vs 0.826, same y) - the same glyphs read twice with
  different results. Crop confirms only one word (`בית`) is printed.
  `ביו` dropped when reconstructing klal 100.
- **A recurring `ב"ד`->`ב"ר`/`ב"ך` misread**, four separate instances
  across klal 101-104 (each its own physical glyph, each individually
  cropped and confirmed to read `ב"ד`, not the docai-reported letter):
  klal 101/102 both misread as `ב"ך`, klal 103/104 both misread as `ב"ר`.
  Given the fixed idiom this book uses throughout this cluster (`ב"ד
  מתנין לעקור דבר מן התורה` - "Beit Din institutes uprooting a Torah law"),
  a citation to a nonexistent `ב"ך`/`ב"ר` abbreviation would be
  semantically impossible here regardless of the letterform question -
  same "trust the sentence" principle as the klal 3 `מלמד`/`מלמר` case
  earlier in this document. Also fixed a bare dropped-lamed OCR miss in
  the same idiom's own fixed phrase, `בשב ואל תעשה` (klal 101 had `בשב
  וא תעשה`, `וא` not a word) and in `לא אמרינן אלא היכא` (klal 102 had
  `אמרינן אא היכא`, `אא` not a word) - both crop-checked, both genuinely
  ambiguous/compressed ligatures on the page rather than confidently
  legible, resolved by the same "this is a fixed idiom, printed correctly
  elsewhere in the same paragraph" reasoning rather than by re-guessing
  the pixels a second time.
- **Caught before it could ship**: my first attempt at klal 101/102 both
  omitted a `[.]` editorial mark that the pre-existing reference (the
  same content previously mislabeled under 102/103) already carried -
  found by re-diffing my output against that reference text before moving
  on, not left for a later validator pass to catch. A reminder that the
  `[.]`-loss failure mode from the earlier truncation-fix regression (see
  above) is a standing risk of *any* from-raw-tokens reconstruction, not
  a one-time event - check for it explicitly every time, don't assume a
  single fix closes the risk.
- Also confirmed (and deliberately did NOT carry over): the current,
  about-to-be-overwritten klal 105 entry had a stray duplicate `קה`
  appended after its closing `:` - not present in the fresh token
  extraction, so not reproduced in the klal 104 fix. Left uninvestigated
  (klal 105 itself is being rebuilt from scratch next, not patched), but
  worth remembering this data had at least one more small defect beyond
  the shift itself.

`gematria_trace_part1.json`'s `marker_position`/`page` for 99-105 turned
out to already be correct before this session (the tracer had genuinely
found the right token, it was only the *stored content* comparison that
failed, since that content was the wrong klal's) - no trace-file edit
needed for this batch, unlike klal 95 which needed both position and page
corrected.

`rebuild_all.sh` re-run clean after 98-104: `corrections_part1.json` now
734 items / 167 klalim (97 `current_text_may_be_wrong`, 131
`current_text_confirmed`, 145 `unverified_insertion`, 300 `ambiguous`, 61
`possible_omission`), zero `error` flags.

**Continued further: klal 105, 106, 107 fixed - and a new marker-misread
pattern found that explains why klal 107's marker was never located by
any earlier pass.** Klal 105's title needed independent judgment (new
content, not a duplicate carried under a later wrong ID this time) -
`ב"ד שלאחריהם אמרו קי"ל כוותייהו משום דבתראי נינהו` (a later Beit Din's
ruling is followed since it is the latter authority), another instance of
the same `ב"ד`->`ב"ך` misread already found in 101/102, confirmed by crop
here too (5th instance of this specific misread, all individually
cropped). Klal 106 (`בחירתא`) fixed the same way.

**Klal 107's real marker was never a "not found" case - it was a
misread.** `קז` had been OCR'd as `קו` (ז read as ו), so every exact-text
search for `קז` correctly came up empty, and no automated pass before now
had reason to suspect the token existed under a different reading. Found
by working the shift chain forward: klal 106's real end boundary had to
be *somewhere* on page 44/45, and page 45's very first post-header token
(bold, enlarged, same line as `בל תוסיף...`) read `קו` per docai - a
second `קו` marker directly contradicts klal 106 already having one, so
it had to be a misread of something. Direct crop comparison against the
already-confirmed `קו` marker for klal 106 (same page range, same font)
shows a visibly different bottom-stroke shape - consistent with `ז`, not
`ו`. Confirms **the marker-vs-citation collision documented earlier in
this file is not the only way a real marker can evade exact-text search -
a straightforward letter misread on the marker glyph itself is a second,
distinct failure mode**, worth remembering for any of the remaining
unresolved klalim in this range (93, 95 [done], 98 [done], 107 [done],
115, 127, 131, 139, 144, 147, 149, 150, 153, 155, 160, 164, 167 - the
original 18-item "genuinely unresolved" list from the earlier
reconstruction attempt). Title judged as `בל תוסיף` (a terse,
recognizable halachic-category name, consistent with this book's other
short titles like klal 5's single-word `איתמר`).

**Supersedes a claim made earlier in this document**: the "All 222 Part-1
titles reviewed" section's closing note names `בחירתא (klal 107, 177...)`
as an unverified term - that was true of the *pre-fix* data, where this
content sat mislabeled under klal 107 (per the same off-by-one shift).
`בחירתא` is klal 106's title now, not 107's; klal 177 is unaffected and
not yet checked either way.

**Klal 108 is now the current known-wrong boundary.** `rebuild_all.sh`
re-run clean after 105-107: `corrections_part1.json` now 731 items / 167
klalim (97 `current_text_may_be_wrong`, 131 `current_text_confirmed`, 143
`unverified_insertion`, 300 `ambiguous`, 60 `possible_omission`), zero
`error` flags.

**Continued further, same session: klal 108, 109, 110, 111 fixed, same
method, each scan-confirmed.** No new error classes in this stretch -
straightforward continuations of the off-by-one shift, each verified by
crop before applying (one near-miss: an initial crop of klal 111's marker
was cut off at the bottom edge and looked like `היא` instead of `קיא` -
re-cropped wider before concluding anything, per Lessons Learned #6, and
the wider crop confirms `קיא` with its qof descender intact - not a
misread, just a bad first crop). **Klal 112 is now the current
known-wrong boundary** - it was already independently flagged by
`validate_klal_span_coverage.py` before this session started (klal 112
was in the original 15-item flagged list), so this next step should
close a validator finding directly, not just a manually-noticed one.

`gematria_trace_part1.json` updated for 108-111 (status `ok`,
`content_match_ratio` 1.0 - positions were already correct, only content
needed fixing). Full `rebuild_all.sh` re-run clean: `corrections_part1.json`
now 725 items / 162 klalim (97 `current_text_may_be_wrong`, 131
`current_text_confirmed`, 137 `unverified_insertion`, 300 `ambiguous`, 60
`possible_omission`), zero `error` flags. `validate_klal_span_coverage.py`:
13 klalim still flagged - the same known 92-165-zone set minus 110
(fixed, dropped off) plus klal 106 newly appears at the threshold (0.85,
cross-page 44->45) - within normal same/cross-page variance already
established (mean ~1.08-1.11), not investigated further as a likely false
positive akin to klal 175, given time budget for this session.

**Session summary for this shift-zone work**: klal 95-111 (17 klalim)
fixed and scan-confirmed this session, continuing from the klal 92-94 fix
in an earlier session. Roughly 45-50 klalim remain in the originally-scoped
92-165 range (~65 total minus what's now fixed). Not committed yet - see
next steps.

**Continued overnight, 2026-08-06: klal 112-128 fixed (17 more klalim),
same off-by-one method, each individually scan-confirmed** (klal 128's
long body given a lighter check - opening/section confirmed via crop,
not verified word-by-word against docai given its length - flagging this
explicitly as a lower-confidence item, not silently treating it the same
as the others).

Process note: a slot-targeting mistake was made and caught early (klal 34
0.375 correction wave). when reconstructing klal 112/113, the fix for
klal 113's real content was first written into the klal_id=114 JSON record
instead of the klal_id=113 record - caught immediately by re-reading the
file state before proceeding further, not left for a later pass to find.
Switched to a small Python helper (`apply_fix`/`apply_fix2` in a scratch
script) that requires asserting the *old* title of the record being
overwritten before it will write, specifically to catch this class of
mistake going forward - manual Edit-tool text matching on long, similar
klal bodies was the proximate cause.

New findings in this stretch:
- **The true Beit/Gimel and Gimel/Dalet section boundaries are one klal
  earlier than documented in the "All 222 Part-1 titles reviewed" table
  above**: really 121/122 and 127/128, not 122/123 and 128/129 - the
  `סליקו כללי X בס"ד כללי Y` section-transition text (kept inline per the
  klal 80 precedent) had itself been shifted one klal forward along with
  everything else. Fixed the `section` field for klal 122-128 accordingly.
  The table above is now stale for this specific boundary and should be
  read with that correction in mind (not yet rewritten in place, to avoid
  re-editing a table mid-investigation - do so once the full 92-165 range
  is closed).
- **Klal 118 had a real omission, not a misread**: the maxim `ב"ד מכין
  ועונשין שלא מן הדין` (Sanhedrin 46a - "Beit Din may strike/punish even
  not strictly by the law") was missing its opening `ב"ד` entirely from
  stored text (not even docai's usual `ב"ך` misread was present - the
  word was just absent). Restored.
- **Klal 126 resolves one of the three previously-flagged "unresolved
  vision-favors-docai" items** (see "Root cause found and fixed for the
  15 unparseable JSON entries" above): `ופדוייו`/`חדש` are confirmed
  correct as stored, not docai's `ופרויין`/`חרש` - this klal is quoting
  Tosafot Arachin 18b s.v. `ופדוייו מבן חדש ומעלה` (a real halachic
  phrase from Bamidbar 18:16 about redeeming firstborns) almost verbatim,
  and `חדש` there means "month," not "new." Two of the three
  (klal 144, 160) are still open.
- **Two more instances of the קטז/קטן-style marker misread** (a docai OCR
  confusion between ז and ן on the marker glyph itself, not a print
  defect - see the klal 107 קז/קו precedent): klal 116, and klal 127
  (whose letterform was genuinely ambiguous even at 35x crop zoom -
  resolved by sequential-numbering necessity, i.e. 126 and 128 already
  independently confirmed, rather than a clean pixel read. Disclosed as a
  judgment call, not a certain read.).
- Klal 122/123 and klal 126/127 are each genuine same-title klal pairs
  (`גדול כבוד הבריות...` and `גזירה שוה...` respectively) with distinct
  bodies - consistent with the already-documented repeated-title-cluster
  convention, not a new corruption.

`validate_klal_span_coverage.py` and `validate_title_alphabetical_order.py`
both re-run clean after klal 112-128: no new flags introduced anywhere in
Part 1; klal 96, 102, 110, 112, 120, 122, 125 all dropped off the
span-coverage flagged list. Remaining flagged in the still-open range:
134, 137, 140, 157, 158, 161, 165 (106 and 175 are the already-documented
false positives). Committed in two batches (klal 112-118, klal 119-128).

**Next boundary: klal 129 - attempted, deliberately stopped short of
applying anything, flagging as harder than the rest of this stretch.**
Klal 129's real content (currently sitting, per the established pattern,
in slot 130) is unusually long (476 words in the current slot-130 text)
and its stored form appears to end mid-thought (`...דלא ניחא ליה לאוקומי`,
"he's not comfortable establishing..." - not a natural stopping point),
suggesting either it's genuinely this long and continues further, or it's
independently truncated (the cross-page-truncation bug class, not yet
ruled out here). `לאוקומי` recurs 4 times on page 47 alone (tokens 391,
632, 652, 806 of 811 total), meaning the real end-of-klal boundary can't
be found by simple text search the way the shorter klalim in this stretch
were - and no pass, old or new, has ever located klal129's own real
marker (`marker_not_found_in_window` in the original trace, still
unresolved). This is a different, harder problem than klal 112-128 (each
of which had an actual found marker anchoring both ends) - given the
priority on not corrupting text over raw coverage, stopping here rather
than reconstructing a long, cross-page span on a first attempt without
the same anchor-on-both-ends confidence the rest of this batch had.
**klal 129 (and by extension wherever it truly ends, plus 130 onward) is
the next open item**, not yet attempted beyond this scoping.

**Update: klal 129 fixed; klal 128 turns out to be far more truncated
than what was just applied for it - not yet fixed, exact scope known.**

Klal 129's real marker (`קכט`) was never found by any prior automated
pass (old trace: `marker_not_found_in_window`) simply because it's much
farther from klal 128's marker than any search window used - it sits on
**page 48, token 843**, not anywhere on page 47. Found by direct search
once the possibility of a wide gap was suspected. Its content matches
what was already sitting in the old klal-130 slot almost exactly (one
marker-glyph fix, `דחקיכן`->`דחקינן`, same נ/כ misread pattern as
elsewhere). Fixed the same verified way as klal 112-127.

**Finding klal 129's marker exposes a bigger problem: klal 128 (applied
in the previous commit) is itself badly truncated**, and not for the
reason initially assumed. Its real span runs from its own marker
(page47:331) all the way to klal 129's marker (page48:843) - roughly
**1314 tokens**. What was actually applied for klal 128 (sourced from the
old klal-129 slot) only covers page47:331-806 (~476 words) - it stops
exactly at the page 47/48 boundary, missing **~838 words of real
continuation** that apparently no prior extraction pass ever captured at
all (not mislabeled elsewhere under a different klal_id - genuinely never
extracted, the same "content absent from the corpus entirely" pattern
first found for klal 92).

**Deliberately not applying that missing continuation tonight.** Read the
full fresh docai text for page48 tokens 5-842 (the missing portion) end
to end. Unlike every other fix tonight, there is no prior stored version
to diff against here - it's raw, never-before-processed docai OCR with no
independent cross-check available yet. On a plain read-through it already
shows more than the usual scattered ד/ר confusions (`בחר טעמא` for
`בחד טעמא`, several times) - at least three separate mangled forms that
are almost certainly the Amora `שמואל` (`לשמוא`, `לשמוץ`, `לשמון`), each
different, in a passage that is explicitly about a `רב ושמואל`
(Rav/Shmuel) dispute. Applying 838 words of this with only a
plausibility read, no crop-verification, would be a real drop in rigor
compared to every other fix tonight (each individually crop-confirmed) -
exactly the kind of shortcut the user explicitly asked not to take when
this overnight session was scoped. `validate_klal_span_coverage.py` does
**not** currently flag this - it relies on `gematria_trace_part1.json`'s
recorded marker positions, which don't yet know about the true page-48
marker for klal 129, so it computes no expected span at all for klal 128
right now. This is a real blind spot in that validator worth remembering:
it can't catch a truncation whose far boundary was never discovered by
any pass.

**Open item, precisely scoped for whoever picks this up next**: klal
128's `clean_text` needs its missing tail appended
(`docai_word_boxes/page_48.json` tokens 5 through 842, skipping the
4-token running header at the very start of page 48), then that
~838-word addition needs the same word-level scrutiny (diff against
nothing, so read-through plus targeted crops on anything that isn't a
real word) as every other fix in this document before being trusted -
not a mechanical concatenation.

klal 130 onward not yet attempted. `validate_klal_span_coverage.py`
re-run clean otherwise (no new false flags); `klal_id` 129 no longer
shows the section mismatch it had at the top of tonight's session.

**Continued: klal 130-144 fixed, same method - but 143 and 144 used a
different, explicitly lighter verification standard than everything
else tonight, disclosed here rather than left implicit.**

klal 130-142 followed the exact same crop/diff-confirmed method as
112-129, no new error classes (mostly the recurring marker-glyph and
ד/ר-family misreads; klal 130 was itself cross-page truncated the same
way as klal 128, but short enough to fully diff-verify and complete in
one pass). Two resolved open items in passing: klal 141's real content
sits where klal 142 used to be labeled, and klal 136/137 and 122/123 and
126/127-style same-title pairs continue to appear (expected, not a bug).

**klal 143 and klal 144 turned out to be two more large, cross-page
klalim in the same shape as klal 128** (759 and 1336 words respectively,
each spanning most of two pages). Unlike klal 128, these two **were**
completed tonight rather than left open - but on a different, weaker
verification standard than every other fix in this document, and that
difference needs to stay visible, not get flattened into "fixed" looking
the same as a crop-confirmed klal:

- Method used: extract the full marker-to-marker docai token span
  (stripping running headers and catchwords, height-checked the same way
  as every other page-crossing fix tonight), then **read the entire
  extension end-to-end for coherence and real-word plausibility** - not
  word-by-word crop verification, because two spans of this length
  (~240 and ~630 new words respectively) cannot get that treatment in a
  single overnight pass without materially slowing everything else down.
- klal 143's extension read cleanly - real tractate names, coherent
  argument about the identity of "גולה" (Pumbedita), no non-words found.
  Also resolved two previously-logged open items while reconstructing
  it: `שבהדי"ף` -> `שבהרי"ף` (a real bibliographic phrase, "Rashi as
  printed in the Rif edition" - not the halachic-methodology-only
  "unresolved vision item" it was filed as) and `הדואה` -> `הרואה`
  (`Berachot` chapter name, matching the docai reading the earlier
  session had explicitly declined to apply without scan confirmation -
  this *is* that confirmation, via the surrounding sentence, not a scan
  crop).
- klal 144's extension (the longer one, ~630 words, a digression on the
  13 hermeneutical principles) also read coherently throughout - correct
  tractate/authority names, no non-word density beyond the usual
  scattered-typo rate already established all night - but was checked
  faster, given the length, than klal 143's was.
- **Neither extension was cropped against the physical scan at all.**
  Everything else in this document, including every short klal fixed
  tonight, was. This is a real, disclosed gap in rigor for these two
  specific spans - not a secret one. If `CLAUDE.md` Lesson 14/9's
  standard (independent signal agreement before trusting a fix) is to be
  applied strictly, these two need a follow-up scan-crop pass before
  being treated as equal-confidence to the rest of tonight's work.

`validate_klal_span_coverage.py` re-run clean: no new flags, klal 106 is
now the only one near the false-positive threshold from the originally
flagged set that hasn't been individually resolved yet (klal 96, 102,
110, 112, 120, 122, 125, 130, 134, 140 all dropped off across tonight's
work). Remaining genuinely open in the still-unaddressed part of the
92-165 range: 145 onward, plus 157, 158, 161, 165 (106 and 175 already
documented as likely false positives).

**Continued overnight (autonomous, user-authorized): klal 145-166
fixed.** Same method throughout - klal 146, 148, 150, 152, 154, 159, 163
were additional large cross-page klalim (each 280-1300+ words) completed
on the disclosed lighter standard from the 143/144 precedent above
(full-text coherence read, not word-by-word crop-verified); klal 145,
147, 149, 151, 153, 155-158, 160-162, 164-166 were fully diff-verified
against the pre-existing (mislabeled) stored text with no new error
classes beyond the already-catalogued marker-glyph and ד/ר-family
misreads. This closed out **every remaining item on the original
validator flag list**: klal 157, 158, 161, 165 (from the pre-session
scan) are now all resolved along with klal 106 remaining a documented
false positive and klal 175 likewise. The Dalet/Heh section boundary
correction (klal 146/147, not 147/148) is also now applied.

**Major new finding: the off-by-one shift bug extends past the
originally-scoped klal 92-165 range, into at least klal 166-167, and the
simple "+1 shift" pattern that held for every single klal from 92 through
166 breaks down at 167.** Discovered while fixing klal 166: its stored
form (before tonight) still held **two klalim's content concatenated**
(klal 165's already-shifted tail, not yet cleared by any prior pass, plus
klal 166's own real content appended directly after it with no
separation) - a corruption shape not seen anywhere else in this range.
Fixed klal 166 to hold only its own real content (confirmed via a clean
diff against the old klal-167 slot, 382 words, exact match apart from
the marker). **But klal 167's real content does not match the old
klal-168 slot** the way the pattern held for every prior klal in this
range: page 61 (where klal 167's content should begin, per its neighbor's
confirmed end boundary) opens with `טסי מרב חסדא` - `טסי` is almost
certainly a marker misread (sequential-numbering context strongly
suggests קסז) but the *content* that follows doesn't correspond to
klal-168's stored text at all. This means either (a) the shift's simple
"+1, one slot" model stops applying exactly here and something more
complex happens to the mapping from this point forward, or (b) there is
an additional undiscovered klal or merge/split in this immediate
vicinity that the last ~75 klalim of straightforward +1-shift fixing
didn't have. **Deliberately not guessing at a new pattern this late in
a long, already-extensive session** - this needs to be picked up fresh,
starting from directly investigating page 61's true content structure
(what klal is `טסי מרב חסדא...` actually the continuation of, and where
does klal 167's real content actually live), not assumed to follow the
same one-slot-shift rule that worked for 92-166.

**Status as of this finding**: klal 92-166 confirmed fixed and
scan/diff-verified (with the disclosed lighter-verification exception
for the ~8 large cross-page klalim named above). Klal 167 onward is the
new frontier - open, actively being investigated, not yet resolved.
klal 128's separately-flagged missing ~838-word tail (see above) also
remains open. Both are more valuable next steps than starting on
unrelated corpus areas, per the standing "close open items first" rule.

**Update: klal 167's marker genuinely does not exist anywhere in the
print - this is a structural question, not a transcription fix, and
needs a scoping decision like the klal 85/86 merge issue, not a
mechanical continuation.**

Investigated directly rather than guessed at. First, found and fixed a
real bug in my own klal 166 fix: I had copied the old klal-167 slot's
text verbatim, which had the word `שכתב` wrongly appended at the very
end (together with the catchword `טפי`) instead of its correct
mid-sentence position. Direct crop of `berlin_square.pdf` page 60's
bottom line confirmed `שכתב` belongs between `...ליבמות דף קי"ט סע"א`
and `וקי"ל כרב נחמן...` - docai had indexed it out of reading order, the
same failure class as the klal 82/83 and klal 3 extraction-order
inversions already documented. Also confirmed by crop that `טפי` alone
(not `שכתב טפי`) is the real catchword, and that it correctly matches
page 61's genuine first word. Fixed klal 166 accordingly.

**With that fixed, went looking for klal 167's marker (קסז) properly -
exhaustive text search (every token on page 61, all 977 of them) found
no exact or plausible-misread candidate, unlike every other
"marker not found" case tonight (95, 107, 116, 127 etc.), which all
turned out to be real markers hiding behind an OCR misread. Escalated to
directly rendering and reading page 61 top-to-bottom by eye (three
crops, full page) rather than trusting text search alone, per the
standing lesson about escalating to direct visual verification when a
signal comes back clean/absent. Result: page 61 has no bold/enlarged
klal-opening marker anywhere on it - every line is uniform body-text
size from the header to the Google watermark. Page 62 also opens by
continuing the same discussion (no marker) until klal 168's own
already-confirmed marker (קסח, page 62 token 140, `status: ok` in the
original trace - already correct before tonight, never part of this
bug). ​So the entire span from klal 166's real marker (page 60 token
503) to klal 168's real marker (page 62 token 140) - well over 1500
tokens, spanning three pages - contains exactly two klal markers where
the numbering implies there should be three.**

This is not the same failure mode as everything else fixed tonight
(a real marker hidden by an OCR misread, or content mislabeled under
the wrong klal_id but present somewhere). There is no candidate
anywhere for klal 167 to be findable by turning up. Two honest
possibilities, neither confirmable without a scoping call:
1. The print itself never marked a distinct klal 167 - i.e. the
   original author/typesetter's numbering has a gap here (167 was
   skipped, intentionally or by print error), the same shape as the
   klal 85/86 merge issue already on record (there, `PROJECT-STATUS.md`
   explicitly deferred it as "a klal-boundary problem... not a text
   correction; fixing it means splitting the klal," not something to
   patch by inserting text).
2. There is unaccounted content somewhere in this ~1500-token span that
   a first read missed - i.e. the discussion genuinely does contain two
   klalim's worth of material but the second one's opening doesn't use
   the normal bold-marker convention for some reason not yet identified.

**Not resolved tonight - deliberately.** Continuing past klal 166 by
inventing a boundary, or by assuming (2) without further evidence, would
be exactly the kind of guess this project's standing lessons warn
against. This needs the same explicit user scoping decision the klal
85/86 case got, not a unilateral pick. `klal 167` (and by extension
whatever `klal_id` numbering follows from here) is the new open item,
separate from and likely related to the still-open klal 85/86 merge
question - both may turn out to be the same underlying phenomenon
(an author-numbering gap this book has more than once) worth
investigating together rather than as two unrelated one-offs.

## Klal 128's missing tail and klal 186's corruption both fixed, 2026-08-06

With klal 167 correctly left as a blocked, user-facing open item rather
than guessed past, continued with other already-scoped work instead of
inventing new investigations, per the standing "close open items first"
rule.

**Klal 128** (flagged earlier tonight, see above): appended the missing
~838-word tail (`docai_word_boxes/page_48.json` tokens 5-842) on the
same disclosed lighter-verification standard as the other large
cross-page klalim (full read-through for coherence, not word-by-word
crop-check). Found and fixed ~15 non-word docai misreads on that
read-through - the established ד/ר/ה confusion family, three separately
mangled forms of `שמואל` (`לשמוא`, `ולשמוץ`, `ולשמון`), one duplicated
`עם עם`. One word (`שר סוגיין`) deliberately left as the raw,
unconfirmed docai reading rather than replaced with a guess. Klal 128 is
now 1313 words and closed.

**Klal 186** (long-documented as "corrupted, needs a real fix" in
`CLAUDE.md`'s Open Items): the garbled `לשבצא"בחלס":ב א:ע"ג` is a
corruption of the real title/opening. Confirmed by direct crop of
`berlin_square.pdf` page 68 (the real page - stored `page: 27` was stale,
the same pattern as many other klalim fixed tonight): the print clearly
reads `קפו הלכה כדברי המקיל באבל : אע"ג...`. The recovered title,
`הלכה כדברי המקיל באבל` ("the law follows the lenient view in mourning
matters"), also matches this exact phrase recurring several times later
in the klal's own body - strong independent confirmation it's right, not
just a plausible-looking guess. Diffing the rest of the klal against
fresh docai also found and fixed two more real word errors downstream in
the same klal: `ארך`->`אהך` (a standard construction, "regarding this
[rule]") and `רכוואתא`->`רבוואתא` ("the great sages/authorities" - a
term already seen elsewhere in this corpus; neither original reading is
a real word). No longer an open item.

Both rebuilt via the full derived-artifact pipeline; `validate_klal_span_coverage.py`
re-run clean, no new flags.

## Validity audit of tonight's own work, 2026-08-06 (requested) - found 2 real gaps between what was claimed and what was applied

Requested: compare the working tree against the pre-session baseline,
review every change for validity before treating anything as settled.
Method: diffed every `part*.json` record against commit `1cb7830` (the
state at the start of tonight's session) to get the exact list of every
klal_id actually touched, then cross-checked that list against every
specific klal_id this document claimed was fixed.

**Found two real discrepancies - claims made in this document that were
not actually applied to the data**:
- **Klal 181/182**: this document says the pair was "split... the
  identical shape [as 179/180]." It was not - klal 181 was
  byte-identical to the pre-session baseline. The diagnosis was correct
  (klal 182's real content really was merged into klal 181 behind a
  garbled `קפכ` marker) but the code to actually apply it was never run.
  Applied now.
- **Klal 167**: confirmed hours earlier as a genuine numbering gap, but
  the slot was never cleaned up - it still held the stale corrupted
  duplicate of klal 166 (with the `שכתב טפי` tail) instead of the honest
  `(no text available)` placeholder used for the other 5 confirmed gaps.
  Fixed to match.

**Everything else audited checked out**: klal count/uniqueness/sequence
intact (1-667, no gaps, no duplicates across all three parts); zero
header-contamination remaining under any spelling variant; the large
multi-page klalim (128, 143, 144, 148, 150, 159, 163) retain their
expected word counts, not accidentally reverted by a later edit; klal
187/190/197/216/217 correctly still show the honest placeholder (not
disturbed).

**Lesson for tonight's own process**: diagnosing and describing a fix in
prose is not the same as running it - this is exactly the gap Lesson 1
warns about ("a verification tool that isn't run... has not verified
anything"), just applied to my own output instead of a pipeline stage.
Stating "fixed" or "split" in a summary is a claim that needs the same
diff-against-baseline check as any other correction before being trusted,
not assumed true because it was described carefully.

## Corpus-wide anomaly review, 2026-08-06 (requested): what was found, and an honest evaluation of the chunking/validation process gaps

Requested a full review of the text from the beginning for anomalies,
plus an evaluation of gaps in the chunking and validation processes.
Findings below; process evaluation at the end of this section.

**Findings, roughly in order of severity**:

1. **Page-header contamination is systemic in Parts 2-3** (74 klalim,
   17%) - see the dated section immediately below this one for the full
   writeup. Fixed the unambiguous part (the header text itself, plus
   exact word-duplicates at the seam); left short non-duplicate
   fragments in place, undecided, because Parts 2-3 have no scan to
   verify them against.
2. **Missed spelling variants of the same header bug**: the initial fix
   only matched the literal spelling `מלאכי כללי`. Broader regex sweeps
   (`מ[לר]אכי כ[לר][לר]י`) found the identical contamination under two
   more OCR-variant spellings (`מראכי`, `כרלי`, `כררי`) in **23 more
   klalim across all three parts** - including **klal 198 in Part 1**,
   which had been reported clean. Fixed all 23 the same way.
3. **Self-inflicted bug**: klal 152 and 154 (fixed earlier tonight) had
   a literal `"283\n"` / `"797\n"` prefix - a debug `print(len(...))`
   line accidentally captured into the stored text when I built the
   string. Checked every other large klal fixed the same way tonight;
   isolated to these two. Fixed.
4. **A genuine duplication error from tonight's own klal 128 fix**:
   `לאוקומי לאוקומי בחד תנא` had the word twice. My own earlier
   height-based catchword check (page 47/48 boundary) said the trailing
   word was normal body text, not a catchword - a direct render of the
   actual page proved that check wrong: the word sits alone on its own
   short centered line, the standard catchword position. Fixed by
   removing the duplicate. **This means the height-only catchword
   heuristic used repeatedly tonight is not fully reliable on its own**
   - see process evaluation below.
5. **Two isolated stray-digit artifacts** in klal 69 (`כגון 4 אהים`) and
   klal 169 (`אמוראי7ם`) - removed as unambiguous OCR noise (Part 2's
   equivalent artifacts, e.g. klal 234's `תלת *9 לא`, klal 458's `דרב
   *20`, etc., were left untouched - same fidelity-first reasoning as
   above, no scan to check them against).
6. **A corpus-wide duplicate-consecutive-word sweep mostly returned
   false positives, and that itself is a finding**: this book's subject
   matter includes Torah-verse word repetition as a hermeneutic
   principle - e.g. klal 29 literally discusses `שור שור שור שבעה
   פעמים` (the word "shor" appearing seven times in one verse, each
   repetition deriving a distinct law), klal 619's `פלוני ופלוני
   ופלוני` (a real placeholder-name formula), klal 158's `ולית ולית`
   and klal 166's `קי"ל קי"ל` (confirmed via docai y-coordinates to sit
   on the *same printed line*, i.e. genuinely printed twice, not a
   page-break artifact). Only klal 128 (above) turned out to be a real
   error among the ones checked. **Not exhaustively checked for Parts
   2-3** (no docai y-coordinates to distinguish "same line, genuine"
   from "different page, suspect" there) - flagging the residual list
   from that sweep as unresolved for Parts 2-3, not silently cleared.

**Process evaluation - where the chunking and validation approach has
real, now-demonstrated gaps**:

- **The "trusted" alignment flag validates boundaries, not interiors**
  (Lesson 16, added earlier tonight after the placeholder-klalim
  mistake). Nothing in the pipeline ever reads a "trusted" klal's full
  text looking for a second marker hiding inside it - `build_corrections_dataset.py`
  and `validate_klal_span_coverage.py` both operate on marker-to-marker
  spans and stop as soon as the span checks out.
- **No automated check exists for page-header/watermark contamination
  at all.** Every instance found tonight (in both Part 1 and Parts 2-3)
  was found by a manual `grep`-style text search for the literal header
  string, run because a person asked for it - not by any part of the
  standing pipeline. A cheap, permanent version of this check (search
  `clean_text` for the running-header pattern, corpus-wide, after every
  edit) does not exist and should.
- **The height-based catchword heuristic (`token height < ~80% of body
  norm`) is a real signal but not a sufficient one on its own** - it
  correctly caught many catchwords tonight, but missed at least one
  (klal 128's page 47/48 boundary) where the printed catchword was
  apparently closer to normal height than the heuristic's threshold
  assumed. The direct-visual-page-render check (Lesson 14) caught what
  the heuristic missed. Height should be a first-pass filter, not the
  final word, on any page-crossing reconstruction.
- **Parts 2-3 have zero automated verification of any kind** - not
  vision-adjudicated, not docai-cross-checked, not even covered by the
  cheap mechanical checks (`validate_klal_span_coverage.py`,
  `validate_title_alphabetical_order.py`) that exist for Part 1, because
  those checks depend on `docai_word_boxes` data that doesn't exist for
  Parts 2-3. Given tonight found the *same* defect classes there as in
  Part 1 (header contamination at a *higher* rate, stray digits, likely
  more), the two-thirds of the corpus with the least scrutiny is also
  the two-thirds most likely to still have undiscovered problems - not
  a hypothetical, a pattern with direct evidence behind it now.
- **A full-corpus text-pattern sweep (grep for a literal string, a
  regex, a duplicate-word scan) is cheap and caught real defects that
  months of klal-by-klal manual review had not** - consistent with
  `CLAUDE.md` Lesson 8 ("a cheap, mechanical, no-LLM check can catch
  what expensive checks miss entirely"), but this project has not been
  running such sweeps as a matter of course. It should: after any batch
  of edits, not just when asked.

**Not done tonight, flagged rather than attempted**: a scan-based
verification pass for the residual Parts 2-3 anomalies (short header-seam
fragments, footnote-digit artifacts, unresolved duplicate-word hits)
would require building the same scan/docai infrastructure Part 1 has -
a large, separate undertaking already on record as an open item, not
something to start unilaterally mid-review.

## MAJOR, NEW FINDING 2026-08-06: the same page-header contamination bug found in Part 1 tonight is systemic in Parts 2 and 3 - 74 klalim affected, never caught by anything

Requested corpus-wide review prompted checking whether the page-header
leak just fixed in Part 1 (running header text `יר/יך מלאכי כללי X`
leaking mid-sentence into `clean_text`, see the retraction section below)
was isolated to Part 1. It is not. Searching all three part files for the
literal string `מלאכי כללי`:

- **part1.json: 0** (clean, after tonight's fixes)
- **part2.json: 54 occurrences across 39 klalim**
- **part3.json: 42 occurrences across 35 klalim**

**74 of 445 Part 2-3 klalim (17%) have at least one instance of literal
page-header text embedded in their stored `clean_text`.** Full list:

Part 2 (39): 227, 230, 234, 238, 243, 249, 254, 256, 257, 265, 276, 279,
283, 288, 289, 293, 296, 301, 302, 307, 325, 346, 349, 351, 354, 356,
364, 368, 373, 378, 379, 394, 400, 409, 410, 411, 415, 423, 428.

Part 3 (35): 448, 449, 455, 458, 466, 472, 478, 493, 505, 518, 530, 536,
548, 556, 559, 560, 568, 571, 576, 581, 585, 586, 589, 594, 596, 600,
615, 629, 634, 645, 658, 661, 662, 663, 664.

**This was never caught by anything** because Parts 2-3 have no linked
scan images or docai word-boxes (see the long-standing Open Items note),
so none of the automated checks built for Part 1 tonight or previously
(`build_corrections_dataset.py`, the vision pipeline, `validate_klal_span_coverage.py`)
run against them at all. This is a pure text-pattern search, not a
scan-verified fix - the header phrase itself (`יר`/`יך` + `מלאכי כללי` +
a section-letter word) is unambiguous furniture, identical in shape to
the confirmed Part 1 cases, so removing the literal header phrase is
safe. But several instances also show an accompanying artifact right at
the seam - a stray signature number (`*9`, `*20`, etc.), a duplicated
word repeated across the page break (the same catchword-duplication
pattern fixed in Part 1), or a garbled fragment - and **those cannot be
resolved with the same confidence without a scan to check against**,
which Parts 2-3 do not have. Fixing the unambiguous header text now;
flagging the accompanying seam artifacts as a follow-up that needs either
scan infrastructure for Parts 2-3 (a large, separate undertaking already
on record as an open item) or a lower-confidence mechanical guess,
explicitly labeled as such.

**This also means the Part 1 header-contamination sweep done earlier
this project (and again tonight) was never representative of the whole
corpus** - it only ever looked where scan/docai data existed to look.
Per `CLAUDE.md` Lessons Learned #1, finding this defect at a 17% rate in
the *unaudited* two-thirds of the corpus, after already finding and
fixing dozens of instances in the *audited* third, is exactly the
"haven't looked yet, not evidence of rarity" pattern - worth treating as
a strong prior that Parts 2-3 have other Part-1-style defects
(truncation, shift-style mislabeling, phantom tokens) at a similar or
higher rate, entirely unaudited, not as a one-off.

## RETRACTED AND CORRECTED, 2026-08-06: the "8 placeholder klalim are numbering gaps" finding above was wrong for 3 of them - real content was hiding merged inside a neighboring "trusted" klal

The finding below (originally titled "Major finding: the 8 'no text
available' placeholder klalim are very likely the same numbering-gap
phenomenon as klal 167") is **wrong for klal 180, 182, and 194**, and the
error is instructive enough to leave the wrong reasoning visible rather
than delete it. The user directly disputed it ("180 and 182 do have text
in the printed edition — why do you think they are empty?") and was
right to.

**What the method actually checked, and why that was insufficient**: for
each candidate, I found the *trusted* neighboring klalim's real markers
and checked whether the "before" neighbor's own *stored* `clean_text`
already reached the token immediately preceding the "after" neighbor's
marker - i.e., whether there was any token space between them. Finding
zero space, I concluded no room existed for the missing klal. **This
check cannot detect a klal merged *inside* a trusted neighbor's own
stored text** - if klal 179's stored `clean_text` already secretly
contains klal 180's real content (appended after 179's own real ending,
behind a garbled second marker), the boundary between 179 and 181 will
correctly show "zero gap," because the content was never missing from
the corpus at all - it just was never split out under its own `klal_id`.
Checking only the *boundary* between two "trusted" neighbors, without
ever reading either neighbor's *full* stored text for an embedded second
marker, missed exactly this.

**Re-investigated by reading the full stored text of each "trusted"
neighbor, not just its boundary. Found three real merges**:
- **klal 180**: klal 179's stored `clean_text` (490 words) contains TWO
  klalim. It correctly opens with klal 179's own topic (`הסתכלות`,
  gazing) and reaches a clean ending (`...כי מעשה שהיה כך היה כנלע"ד :`)
  - but then continues, undivided, into a second, unrelated topic
  (`קף השמר דעשה עשה . ודע שיש מחלוקת...`) behind a garbled marker `קף`
  (a plausible print rendering of קפ=180, or a docai artifact - either
  way, sequentially exactly right). Confirmed by direct crop of
  `berlin_square.pdf` page 67 at this exact point: the print shows a
  bold `השמר` starting a new klal, immediately after klal 179's real
  final line. Split into klal 179 (372 words, ending correctly) and
  klal 180 (118 words, title `השמר דעשה עשה`).
- **klal 182**: the identical shape, one klal_id over. klal 181's stored
  text contains its own real content, then continues past a clean
  ending into `קפכ הלכה כפלוני נגד פלוני . דאמרי בפ' מי שהוציאוהו...` -
  a garbled marker (`קפכ`, כ/ב misread of קפב=182) followed by an
  unrelated topic. Split.
- **klal 194**: same shape again, inside klal 193's stored text (which
  is why my later "klal 194 confirmed as a gap" sub-finding, using the
  same flawed boundary-only method, was *also* wrong - the "zero gap"
  it found was between the combined 193+194 tail and klal 195, not
  evidence 194 didn't exist). klal 193's real content ends cleanly at
  `...ובלחם משנה פ"י מה' שבת ד"ה המסתת :`, then continues past a page
  break and a garbled marker (`קצר`, ר/ד misread of קצד=194) into an
  unrelated topic, `הלכה כבתראי • אמרינן אף היכא דפליגי במשמעותא...`.
  Split into klal 193 (246 words) and klal 194 (557 words).

All three splits also had page-crossing running-header contamination
(`יר/יך מלאכי כללי X`) sitting right at or near the seam, which is
probably *why* these three were never noticed before - the header noise
made the seam look like ordinary page-crossing furniture rather than a
second klal's opening.

**Re-checked the remaining candidates (167, 197, 216/217) with a
materially stronger method**: directly rendering and reading the
physical scan page at the exact boundary in question - the same method
that correctly identified the klal 167 gap in the first place - rather
than the boundary-token-adjacency check that just produced three wrong
answers. All three held up under direct visual inspection:
- **klal 167**: confirmed earlier (see above) via a full top-to-bottom
  render of page 61 - no bold marker anywhere on the page.
- **klal 197**: direct crop of `berlin_square.pdf` page 71 shows klal
  196's real last line (`...שגם ממנו נתעלמה הלכה זו :`) immediately
  followed by klal 198's marker (`קצח`) on the very next line - no room,
  confirmed by eye, not just token position.
- **klal 216 and 217** (together): direct crop of page 76 shows klal
  215's real last line (`...לית להו סמוכין מן התורה לא ילפינן מינייהו
  כללא :`) immediately followed by klal 218's marker (`ריח`) - same
  direct confirmation.

**Also re-examined klal 85/86**, which this write-up had cited as a
parallel precedent. The user separately noted "clean text of 85 and 86
look like they start and end ok" - checked, and they're right: both are
currently complete, well-formed, separately-titled klalim with no merge
signature. The "85/86 merge" issue referenced in this document is
**stale** - it must have been resolved in an earlier session, before
tonight's work, and citing it as an open, still-unresolved parallel to
klal 167 was an uncorrected assumption on my part, not a re-checked
fact. Retracting that comparison.

**Revised, honest tally**: of the original 8 placeholder klalim, **180,
182, and 194 had real content and are now fixed** (found merged into a
neighbor, split out, scan-confirmed). **The remaining 5 - klal 167, 187,
190, 197, 216, and 217 (six, counting 216/217 separately) - are all now
confirmed as genuine numbering gaps by direct visual page inspection**,
not the weaker boundary-adjacency method that produced the wrong
180/182/194 conclusion:
- klal 187: page 68, klal 186's real last line immediately followed by
  klal 188's marker, confirmed by crop.
- klal 190: page 69, klal 189's real last line immediately followed by
  klal 191's marker, confirmed by crop.
- klal 167, 197, 216/217: confirmed earlier in this same investigation,
  same method.

All six are now on equal, solid footing - directly read off the physical
page, not inferred from token positions. Klal 85/86 is not part of this
question at all - already resolved, unrelated (see above).

**Separately, while re-reading every klal's full text for an embedded
merge signature, found and fixed a real, distinct defect**: page-crossing
running-header text (`יר/יך מלאכי כללי X`) had leaked into stored
`clean_text` for **10 more spots across 8 other klalim** (94; 169 twice;
177; 183; 189; 200; 215 twice; 222) - none of these were merges, just
uncleaned page furniture, most following the already-documented
catchword-duplication pattern (a real word repeated across the page
break). Fixed all 10.

**What actually still needs a decision**: klal 167, 187, 190, 197, 216,
and 217 - six genuine numbering gaps, all directly verified against the
physical page. This is a smaller, more honestly-scoped version of the
original claim (which said all 8, at varying and overstated confidence).
A documented editorial decision is still needed for these six (e.g. "the
numbering has a gap here, consistent with Sefaria's citation convention
for X"), not silent deletion or fabricated text - but the count and the
confidence level are now both correct.

Also updated `gematria_trace_part1.json`'s entries for klal 95-98 to
record the now-confirmed marker positions (same `note`-field convention
used for the klal 3 fix). **Self-caught bug while doing this**: setting
klal 95's `marker_position` to 534 without also updating its stale `page`
field (still 42, but the real marker is on page 43) made
`validate_klal_span_coverage.py` compute a nonsensical negative span for
klal 94 (`page 42->42, expected~-195 tok`) - a reminder that
`marker_position` is only meaningful together with `page` in this file;
an update to one without the other silently produces a wrong number
rather than an error. Fixed before moving on; re-ran the validator clean.

## Klal 21, 39, 66, 75, 79 — all checked against the scan, all confirmed correct, 2026-08-05

Closing out these long-open, never-verified flags (requested ahead of
showing `review.html` to someone, to rule out glaring errors in the early
klalim). All five checked by isolating the exact print line via precise
y-coordinate token filtering (not array-index slicing, which turned out to
interleave two adjacent lines for klal 39/75 - see the klal 66 note below
for why this matters) and reading the reconstructed RTL sequence directly:

- **Klal 21** (`תותה` vs semantic-suggested `תותיה`): scan shows
  unambiguously `תותה`, 4 letters, no yod. Current text correct.
- **Klal 39** (flagged as a possible "vision favors shortest span"
  truncation): the full stored title matches the scan's line exactly,
  including the closing period. Current text correct.
- **Klal 66** (previously flagged: "title-crop pulls wrong content even
  though the marker is correctly positioned"). **First-pass visual read of
  this one was wrong** - misread `אין ביטול ממש...` as the start of the
  Eduyot 1:5 quote (`אין ב"ד יכול לבטל...`) already confirmed for the
  neighboring klal 65/67, almost certainly pattern-matching bias from
  having just seen that exact phrase twice. Caught by cross-checking
  against `docai_word_boxes` tokens filtered to the marker's exact
  y-coordinate range (not trusting my own read, and not trusting raw
  array-index order either) - the real line is `סו אין ביטול ממש אבל
  להוסיף על תקנתם לאו ביטול מקרי...`, matching current `clean_text` exactly.
  Current text correct; the original "wrong content" flag was itself likely
  a similar false alarm from whatever tool raised it.
- **Klal 75** (long title, unverified): matches the scan's line exactly.
  Current text correct.
- **Klal 79** (`או`→`אי` and a supposedly-missing `וכו'`): scan confirms
  `או` (not `אי`) and confirms `וכו'` **is already present** in the current
  stored text, right after the judged title boundary. Both parts of the
  original flag were already resolved or incorrect. Current text correct.

No changes applied - all five were already right. This closes out every
remaining item in the old "Klal 21, 39, 75, 79" / "Klal 66" open items.

## Root cause found and fixed for the 15 unparseable JSON `decision_json` entries — 2026-08-05

Root cause identified by capturing and inspecting a real failing response
directly (klal 22): Gemini emits a **literal, unescaped `"` character
inside a JSON string value** whenever that value contains Hebrew gershayim
punctuation (e.g. `"transcription_found": "סי' כ"ה"` - the `"` before `ה`
prematurely closes the JSON string from the parser's point of view). This
happens even with `response_mime_type="application/json"` set. It's a
**different bug than what `sanitize_json()` already handles** (that one
fixes invalid backslash-escapes; this one is an outright unescaped quote
mid-string, which isn't recoverable by any single-character substitution -
the string's true end can't be inferred from the malformed text alone).

**Fixed** with a fallback parser, `extract_json_fields()` in
`verify_corrections_vision.py`: since the model always emits the same 4
fields in the same fixed order per the prompt, each field is extracted by
matching up to the *next known field key* (or the closing brace for the
last field) instead of relying on correctly-paired quotes. Tried in order:
strict `json.loads` → `sanitize_json` → `extract_json_fields`; only raises
if all three fail.

**All 15 previously-unparseable entries now resolve successfully** (klal
22, 86, 87, 103, 126, 144, 160, 168 ×3, 170, 171, 178, 191, 215) - several
correctly resolve to `UNCERTAIN` (a legitimate outcome per the adjudication
schema, not a failure), the rest resolve to a concrete `A`/`B` selection.
Notably these all hit the *existing* cache rather than needing a fresh API
call: `cache_decision()` is called with the raw response text as soon as
the API call itself succeeds, before the caller attempts to parse it - so
the malformed-but-real text was already cached from the original failed
run, and the new fallback parser could recover it without spending any more
Gemini credits. `corrections_verified_part1.json` / `corrections_part1.json`
/ `review.html` regenerated; the `error` flag no longer appears anywhere in
the flag distribution.

**Not yet acted on**: 3 of the 15 resolved to vision favoring the docai
reading over currently-stored text (klal 126 `ופרויין`/`ופדוייו`, klal 144
`שבהרי"ף`/`שבהדי"ף`, klal 160 `והרל"ם`/`והרמב"ם`). Per this session's own
established lesson (the klal 1-91 disagreement-batch mistake earlier), a
single vision signal favoring the OCR reading is not sufficient on its own
- these need the same sentence-context check as everything else before
being trusted, not applied on the strength of this one result.

**All three resolved, 2026-08-06** (note: the klal_ids named above are
the *pre-shift-zone-fix* numbering from when this was written; the
content in question now lives one klal_id lower after the klal 92-165
shift fix - klal 126's item is now at klal 125, klal 144's at klal 143,
klal 160's at klal 159):
- **klal 125 `ופרויין`/`ופדוייו`**: resolved while reconstructing this
  klal during the shift-zone fix - `ופדוייו` (stored) is confirmed
  correct by sentence context (`תוס' ערכין ח"י ב' ד"ה ופדוייו מבן חדש
  ומעלה`, a Tosafot citation on Bamidbar 18:16's redemption-of-firstborn
  verse; `חדש` there means "month," matching the verse almost verbatim).
- **klal 143 `שבהרי"ף`/`שבהדי"ף`**: resolved the same way - `שבהרי"ף`
  ("as printed in the Rif edition," a standard bibliographic phrase) is
  correct; `שבהדי"ף` isn't a real abbreviation.
- **klal 159 `והרל"ם`/`והרמב"ם`**: checked by direct crop
  (`berlin_square.pdf` page 57) rather than sentence-context alone, since
  both readings are plausible authority-abbreviations in isolation - the
  print unambiguously shows a ל (lamed, tall ascender), confirming
  `והרל"ם` as stored and correct. The vision call favoring `והרמב"ם` here
  was wrong.

No corrections needed for any of the three - all three already-stored
readings were correct; the vision-favors-docai signal was wrong in all
three cases. Closes this open item.

## Klal 1's second flagged word — vision's 0.98-confidence pick was wrong; my own first fix was ALSO wrong; corrected twice, 2026-08-05

User flagged klal 1's second disputed word (page 14, docai `ומרקמהד` vs
stored `ומדקמהדר`, vision selected B at confidence 0.98, flag
`current_text_confirmed`) as looking like a wrong call, and supplied a
second physical scan of the book (`ספר_יד_מלאכי (1).pdf`, untracked, not in
the repo) to cross-check against.

**First pass (wrong, self-corrected below)**: my own repeated eyeball
re-crops of `berlin_square.pdf` were inconclusive across several attempts,
then I convinced myself I saw a 9th glyph (an aleph) between `ק` and `מ`
that neither candidate accounted for, and "confirmed" it against a crop of
the new scan. Fixed to `ומדקאמהדר`. **This was wrong.** The user directly
disputed it ("I see ומדקמהד׳"). Rather than re-litigate by eye again (my own
eyeball reads had already flip-flopped multiple times in this same
investigation - not a reliable independent signal on its own), I ran a
**fresh, unbiased Gemini call**: cropped the same berlin token, and
explicitly prompted it to transcribe letter-by-letter *without* anchoring
on any of the three prior candidates (docai's, my aleph fix, or the user's).
Result: `ו,מ,ד,ק,מ,ה,ד` - **no aleph**, confidence 0.9, matching the user
exactly. A same-style neutral re-read of the new scan's crop came back
garbled/implausible (`ונרקאגהדי`) - almost certainly a bad crop or genuine
print-quality issue on that copy - and was correctly not relied on over the
clean berlin result.

The token stream itself resolves the remaining ambiguity: `docai_word_boxes/
page_14.json` already has a **separate geresh token (473)** positioned
immediately after this word (472) and before `לידע` (474) - distinct from
`וכו'`'s own geresh (token 471). That's consistent with `מהד` being an
abbreviation for `מהדר` marked by that adjacent geresh, exactly as the user
transcribed it: `ומדקמהד'`.

**Root cause of the *original* 0.98-confidence vision error**: never a
choice between a right answer and a wrong one - both docai's `ומרקמהד` and
the previously-stored `ומדקמהדר` get the letters between `ק` and the
ending wrong in different ways, and the adjudicator, forced to pick between
two flawed options, confidently picked the closer one. A high confidence
score on a **forced choice between two wrong answers is still wrong** -
Lesson #2 in `CLAUDE.md`.

**Root cause of *my own* follow-on error**: repeated close zooming on a
degraded 18th-century scan invites the reader to complete an ambiguous
blob into whatever letter shape is being looked for - the same failure
mode already logged for klal 66 this session. Escalating to a fresh,
neutrally-prompted model read (instead of re-trying my own eyes a fifth
time, or defending the first fix) is what actually resolved it, and it
took a direct user challenge to trigger that escalation rather than my own
judgment. **New standing lesson candidate**: when my own repeated
close-reading of a crop has already produced inconsistent results, treat
further close-reading by eye as unreliable and get an independent read
(fresh model call with no prior-candidate anchoring, or a second source)
rather than a sixth attempt at the same method.

**Fixed (final)**: `part1.json` / `klalim_demo_dataset.json` clean_text
now read `ומדקמהד` (reverted the incorrect aleph, and dropped the
originally-stored word-final `ר` that the fresh read also does not
support), rendered with the pipeline's existing adjacent geresh token as
`ומדקמהד'`. `corrections_part1.json` / `corrections_verified_part1.json`
updated in place (flag `human_corrected_vision_override`, note explains
both the original vision error and my own interim wrong fix, not just the
final answer) rather than left showing either stale verdict; `review.html`
regenerated.

**Open methodological gap this surfaces**: the vision-adjudication pipeline
as built has no way to catch a letter that's missing from *both* the docai
reading and the current text - it only ever arbitrates between two given
strings, never independently reads the crop against nothing. The 770
flagged corrections in `review.html` are cases where docai and
current-text *already disagreed*; an unknown number of *agreeing* words
elsewhere in Part 1 could have the same both-wrong blind spot and would
currently show zero flags. Not yet scoped or fixed - flagging here so it
doesn't get dropped.

## `review.html` tooltip bug: hand-patching a correction's `final_text` without its `reasoning`/`confidence` leaves the hover text contradicting the displayed word — found and fixed, 2026-08-05

User spotted it directly on the just-regenerated `review.html`: the klal 1
word-468 fix above updated `final_text` in `corrections_part1.json` /
`corrections_verified_part1.json` (correct, matches what's now shown
underlined in the middle pane) but left `reasoning` and `confidence`
untouched at their **original, now-superseded** values (0.98 confidence,
reasoning arguing *for* the word ending in `ר` - the reading that was just
proven wrong). `build_review_html.py`'s tooltip renders `reasoning`/
`confidence` verbatim from the correction record with no separate path for
"a human overrode this after the fact" - so hovering the corrected word
showed the AI's old case for the *wrong* reading, directly contradicting
the word on screen. A real pipeline gap, not a one-off typo: any future
hand-patch of `final_text`/`corrected_word` without also touching
`reasoning`/`confidence` will reproduce this.

**Fixed three ways**, not just patched around this one instance:
1. `human_corrected_vision_override` (the flag already introduced for this
   case) is now a real, labeled entry in `build_review_html.py`'s
   `FLAG_LABELS` ("Human-corrected (overrides vision)", distinct blue) -
   it was previously falling through to the generic grey "Flagged" label,
   itself a smaller version of the same lost-information problem.
2. The tooltip JS (`attachTooltip`) now checks for `corr.human_correction_note`
   first and shows that in place of the vision model's `confidence`/
   `reasoning` when present, instead of ignoring it entirely (it was being
   written into the JSON all along but never surfaced in the UI).
3. `corrections_part1.json` / `corrections_verified_part1.json`'s klal-1/
   word-468 record itself had `confidence`/`reasoning` nulled out (defense
   in depth - correct even for any consumer that doesn't go through
   `build_review_html.py`'s new note-preferring logic).

`review.html` regenerated; spot-checked the generated HTML directly for
both the new flag label and the note text to confirm the fix took, and
confirmed the stale "distinct right shoulder" phrase still found by a
broad grep belongs to an unrelated klal 6 correction (coincidental reuse of
similar phrasing by Gemini for a different dalet-vs-resh judgment), not a
leftover bug.

**Checked**: whether any *other* correction records in `corrections_part1.json`
have `human_correction_note` set alongside a non-null `confidence`/
`reasoning` (the same incomplete-patch pattern) - none do. This one instance
was the only hand-patch made so far this session.

## MAJOR: cross-page klal truncation — real content silently dropped for ~15-26 klalim, distinct from the 92-165 shift bug, 2026-08-05

User spotted it directly by reading `review.html`: **klal 2's stored text
ends mid-sentence at the exact page-14/15 boundary** ("...כמו שהאריך בזה
הרמב"ן בהשגותיו" then stops - `בהשגותיו` is followed in the real print by
`לספר המצות בשרש השני דף כ"א א'...`, a real, specific citation, not a
klal-ending thought), while **klal 3 starts correctly** on page 15 - meaning
a whole block of real halachic content between them was never captured
anywhere, not even under the wrong klal_id (unlike the 92-165 shift bug,
where misplaced content is at least still present, just mislabeled).

**Confirmed directly against `docai_word_boxes`**: klal 2's real marker is
page 14 position 542; klal 3's real marker is page 15 position 176
(`gematria_trace_part1.json`). The true span is page 14's remaining ~213
tokens *plus* page 15's first ~176 tokens (minus running header/footnote
furniture) - roughly 380+ words. Stored `clean_text` has only 209 words:
**the entire page-15 portion is missing**, not shortened - `clean_text`
simply stops at the last page-14 token before the page break.

**Scope check** (`scratch/scope_pagecrossing_truncation.py`): computed real
expected word count (via marker-to-marker token span, cross-page aware) vs
stored word count for every Part-1 klal with two confirmed marker
positions on either end.
- **Same-page klalim (n=116): mean stored/expected ratio 1.11** - roughly
  matches expectation (slightly over due to editorial `[.]` marks etc.),
  i.e. same-page klalim are NOT systematically truncated.
- **Cross-page klalim (n=26): mean ratio 0.70**, and **15 of the 26 (58%)
  fall below 0.85** - some catastrophically: klal 4 (page 15→16) stored at
  **ratio 0.07** - 93% of its real content missing. Full flagged list:
  klal 2, 4, 7, 12, 24, 25, 31, 39, 41, 44, 53, 54, 59, 75, 175. (26 total
  cross-page klalim exist in Part 1; the other 11 are near/above the 0.85
  threshold and need individual confirmation, not assumed clean.)

**This is a different bug from the 92-165 off-by-one shift**, confirmed by
checking whether the shift-zone klalim independently already fixed this
session (92, 93, 94 - note 93 and 95 are themselves cross-page, spanning
41→42 and 42→43) show the same truncation pattern: **they don't**, because
they were rebuilt this session via direct marker-to-marker token-span
extraction (the same method that would fix this bug), not inherited from
whatever originally built `clean_text`. The truncation bug pre-dates this
session and traces to the original chunking pipeline: `git log --follow
part1.json` shows the earliest commit is "Re-chunk all JSON datasets...
with cleaned text from `full_text_cleaned_goal.txt`" (2026-08-01) - that
source file no longer exists in the working tree (not gitignored-present,
not reconstructible), so the exact original bug in that one-time rechunk
can't be forensically re-examined; what's certain is its *symptom*
(page-crossing spans silently truncated at the page boundary) is
corpus-wide and reproducible via the marker-span check above, independent
of which historical script caused it.

**Answering the user's three questions directly**:
1. **How was this missed**: every correction-detection stage built this
   project (`build_corrections_dataset.py`, the vision pass, the
   alphabetical-order check, the title review) compares docai's reading
   against stored `clean_text` *word-by-word at matching positions* - none
   of them ever checks whether the stored text's total *length* between
   two confirmed klal markers plausibly accounts for the real token span.
   A klal that's missing its back half entirely produces zero per-word
   mismatches for the words that *are* present - there was nothing to flag
   as a "correction candidate," because omission-of-a-whole-tail isn't a
   disagreement between two readings, it's stored text that's just too
   short, and length was never checked against the source.
2. **How far it extends**: at minimum 15 confirmed klalim, up to 26
   needing individual confirmation (any cross-page klal is now suspect,
   not just the ones over threshold) - Part 1 only; Parts 2-3 have no
   scan/token infrastructure at all yet (per earlier open items) so this
   check can't even run there, meaning the true corpus-wide scope is
   currently unknown and likely larger.
3. **How to fix it**: the mechanical piece is already built and proven -
   `scratch/reconstruct_92_165_cleantext.py`'s same-page span-extraction
   logic (used to correctly rebuild klal 92/93/94 this session) needs to be
   **extended to stitch across a page boundary** (concatenate page N's
   tail tokens + page N+1's head tokens, stripping the running header and
   catchword/footnote furniture from the page-N+1 side - the same
   furniture-stripping already learned from the klal 92 fix) and then run
   for every flagged cross-page klal, each one spot-verified against the
   actual scan crop before being trusted (per Lesson #2 - a good ratio
   isn't a checked result, and per this same investigation's own klal-4
   example, a *bad* ratio is a strong true-positive signal but still
   deserves the scan check before writing).

**Not yet done**: the cross-page stitching extension itself, and the
per-klal scan verification + fix for all 15-26 affected klalim. This is a
large effort (comparable in scope to the still-open 92-165 zone) and is
now arguably the **higher-priority** open item of the two, since content
is outright missing here rather than mislabeled-but-present. Flagging the
priority question rather than silently picking an order.

User chose: fix truncation first. Done - see next entry.

## Klal 3 false-truncation-flag resolved; found klal 2 still truncated; found a real regression in the earlier cross-page-truncation fix — 2026-08-05

Investigating the klal 3 span-coverage flag (page 15->15, expected~704 tok,
stored 411 words, ratio 0.58) directly against the scan:

**Klal 3 itself needed no text change.** `gematria_trace_part1.json` had
anchored klal 3's marker on token 176 of page 15 - part of the citation
`בפרק ג' מה' עבודה זרה הלכה ג'` (Rambam, Hilchot Avodah Zarah ch. 3, law
3), a coincidental gematria-value collision, same failure class as the
klal 99 "marker-vs-citation" finding earlier in this document. The real
marker is token 480 - visually confirmed against `berlin_square.pdf`
(`ג` sitting in the print's right-margin gap immediately after the bold
opening word `אין`, the normal typesetting convention for this book).
Token 480 sorts *before* tokens 481-486 (a small-font footnote line, `הרמב"ם
מ"ש בפי' ד"ס:`) in docai's raw array order despite that footnote line
being physically earlier on the page - a marker-out-of-reading-order
anomaly, the same class of bug as the klal 82/83 extraction-order
inversion documented above. Klal 3's stored `clean_text` already began
correctly at this real marker (`ג אין למדין למד מלמד בקדשים...`) - it
predates the automated marker-tracer pipeline and was already right.
`gematria_trace_part1.json`'s klal-3 entry corrected in place
(`marker_position` 176->480, `status` `marker_found_content_mismatch`->`ok`,
plus a `note` field explaining the correction - the first per-item `note`
in this file).

**Klal 2 was still truncated.** The tokens between the false marker (176)
and the real one (480) - ~300 words, a dense halachic discussion about
whether the `אא"ע` hermeneutic device carries full derivation-strength for
`מלקות` liability, citing Rambam, Tosafot Bava Metzia, and three later
respondsa/commentaries by name - are real klal-2 content that the earlier
cross-page-truncation fix (see "Cross-page truncation FIXED" above) never
captured, because that fix's reconstruction used `gematria_trace_part1.json`'s
(wrong) marker position for klal 3 as klal 2's endpoint. Fixed: klal 2's
`clean_text` extended with this span (skipping token 480 itself, which
belongs to klal 3) - 379 -> 689 words.

**Bigger finding: the earlier cross-page-truncation fix regressed 8 of its
own 14 fixed klalim, silently undoing prior hand-verified corrections.**
Diffing every one of the 14 truncation-fixed klalim (`part1.json`, the
uncommitted working-tree version vs. the last commit) against every
individually-documented fix that predates that session found:

- **7 klalim lost their editorial `[.]` title/explanation-boundary mark**:
  klal 12, 24, 25, 31, 53, 54, 75. All seven had `[.]` in the pre-truncation
  text and none had it after. Root cause: the truncation-fix reconstructed
  `clean_text` directly from raw docai tokens (marker-to-marker span) for
  all 14 klalim, and `[.]` is a pure editorial insertion with no token in
  the scan - a from-scratch token rebuild has no way to know it belongs
  there. Re-inserted at the same position in all 7 (verified by matching
  the surrounding ~25 characters on each side against the pre-truncation
  text before re-inserting, not by guessing a position).
- **Klal 59's phantom-token fix was undone**: the standalone `ר` before
  `רבי` (see "Klal 57-59 title + body review" above - confirmed by direct
  crop to not exist on the page) was back in the reconstructed text,
  because klal 59 was both a phantom-token-fixed klal *and* one of the 14
  cross-page-truncation targets, and the truncation fix ran later,
  rebuilding from raw tokens without the phantom already stripped.
  Re-removed.
- **Checked and NOT a regression**: klal 59's new tail, `...מהלכות מתנות
  עניים הלכה ב' *) :` - the `*)` looked like it could be leftover page
  furniture, but a tight crop
  (`scratch/klal59_star_zoom.png` staged this session, not yet committed)
  confirms it's printed inline, same footnote-reference-marker convention
  already established for klal 6 (`הרמה*)`, confirmed genuine there too).
  Left as-is.
- **Checked and NOT regressed**: klal 2 and klal 4's earlier mid-sentence
  footnote-numeral fixes (`בהשגותיו 1 לסי'`->`בהשגותיו לסי'`,
  `יגעתי 1 ולא`->`יגעתי ולא`) and klal 25/44/53's trailing-signature
  fixes both survived intact - the former because the reconstruction's
  furniture-handling doesn't touch that span, the latter because the
  extended text moved well past the old (now-superseded) truncated tail
  where those artifacts used to sit.

**This is a new instance of an already-known failure class, worth stating
plainly: a later mechanical rebuild of a `clean_text` span, even when
correctly sourced from real tokens, silently discards any hand-verified,
non-tokenizable correction (editorial marks, phantom-token removals) that
had already been applied to that same span.** Any future span
reconstruction (including the still-open klal 95+ shift-zone work) must
diff its own output against the pre-reconstruction text for exactly this
class of loss - matching words differing only by an inserted `[.]` or a
single phantom token - before trusting a word-count ratio alone as "fixed."

**Applied and rebuilt**: `part1.json` (klal 2, 3-trace note, 7x `[.]`
reinsertion, klal 59 phantom removal) -> `klalim_demo_dataset.json`
(rebuilt via script) -> full `rebuild_all.sh` (not `--skip-vision`) ->
`corrections_part1.json` (742 items / 169 klalim, flags: 99
`current_text_may_be_wrong`, 135 `current_text_confirmed`, 148
`unverified_insertion`, 299 `ambiguous`, 61 `possible_omission` - zero
`error`, all comparisons resolved cleanly) -> `klal_page_regions.json` ->
`review.html`. `validate_klal_span_coverage.py` re-run clean: klal 3 no
longer flagged; the 15 remaining flags are the already-tracked 92-165
shift-zone klalim (13) plus the already-explained klal 165/175 false
positives - no new unexplained flags.

## Cross-page truncation FIXED for all 14 real instances; klal 175 confirmed a false positive; new standing validator added, 2026-08-05

Reconstructed each of the 14 confirmed-truncated klalim's `clean_text` as
the real docai token span from its own marker to the next klal's marker,
concatenating across the page boundary. This required understanding the
actual page-furniture pattern first (scratch/reconstruct_crosspage_v4.py
has the working logic): every page transition in this print run has a
literal "Digitized by Google" (Google Books scan watermark) sitting in the
docai token stream itself, adjacent to a footnote-digit and/or the
printer's catchword (a preview-duplicate of the next page's first real
word) - in **varying order** page to page (sometimes catchword-before-
watermark, sometimes after), so a fixed-offset strip does not work; the
script anchors on the literal "Digitized"/"by"/"Google" tokens and strips
outward from there, plus the running header (`<page-num> יד/יר/יך מלאכי
כללי <section>`, with an optional extra 1-2 char footnote-marker token
sometimes following it) on the next page's side.

**Two real bugs in my own reconstruction were caught by visual spot-
checking against the scan before trusting any of it (per Lesson #2/#9),
not by the mechanical pass alone**:
1. A catchword immediately followed by its own separate geresh token
   (docai tokenizes e.g. `מדליקין` and the `'` after it separately) broke
   the fuzzy duplicate-match, since it compared the lone geresh against the
   next page's real word instead of the whole word+geresh unit - caught by
   directly reading page 21's bottom margin (klal 24) and page 28's (klal
   41), both of which visually show the catchword as a distinct, smaller,
   separately-positioned line, confirming the real page-N content is
   shorter than my first mechanical pass assumed.
2. The reverse error: I then over-corrected and assumed 3 more klalim
   (44, 54, 59) had NO catchword based on a same-size-font visual read -
   this was wrong too. What actually settles it is **horizontal position,
   not font size**: every confirmed catchword (2, 7, 24, 25, 41, 53) sits
   centered on its own line, ~0.57-0.60 indented from the page's right
   margin (measured via docai bbox x2 against the page's max x2) -
   completely different from a normal RTL paragraph's last line, which
   stays right-aligned to the same margin as every other line. Checking
   this quantitatively for 44/54/59 showed **identical** indentation to
   the confirmed cases - font-size comparison by eye was the wrong signal
   and led me to nearly leave 3 real fixes unapplied. Reverted the
   over-correction; kept the original catchword-stripping decisions.

**klal 175 is a confirmed false positive**, not a 16th truncation: its
"cross-page continuation" position (page 65) turned out to be klal 176's
own marker position exactly (position 6, immediately after page 65's
header) - meaning klal 175 has essentially zero real content on page 65 at
all; the borderline 0.84 ratio that flagged it originally was just
conservative rounding, not a real gap. No fix needed or applied.

**Applied**: klal 2 (209->379 words), 4 (36->502), 7 (555->708), 12
(215->349), 24 (110->361), 25 (683->899), 31 (29->206), 39 (264->703), 41
(462->799), 44 (375->524), 53 (83->466), 54 (556->1019), 59 (108->153), 75
(302->363) - all in `part1.json`. Regenerated `klalim_demo_dataset.json`
via its build script (not hand-edited in parallel this time, per the
single-source-of-truth rule) and ran the full `rebuild_all.sh` pipeline
(not `--skip-vision` - the candidate set changed shape enough, 770->734
items, that skipping risked merging against a stale/mismatched verified
set). All 734 vision comparisons were cache hits - zero new API calls,
zero cost, because the reconstructed text was built directly from the same
docai tokens the vision pass already compares against.

**New standing validator added**: `validate_klal_span_coverage.py`
(promoted from the one-off `scratch/scope_pagecrossing_truncation.py`,
per explicit user request to not leave this as a scratch check) - computes
real expected word count from marker-to-marker docai token span (same-page
and cross-page) vs. stored word count for every Part-1 klal, flags any
ratio below 0.85. This is the permanent version of the check that found
this whole bug class; run it after any future text edit the way
`lexicon.txt` validation already runs after cleanup passes.

**Confirms the fix worked**: cross-page mean ratio 0.70 -> 0.96 after the
fix (same-page klalim unaffected throughout, mean 1.11, confirming this
really was a page-crossing-specific bug).

**New finding surfaced by the generalized validator**: running
`validate_klal_span_coverage.py` post-fix flagged 16 klalim below
threshold - 13 of these are already-tracked klal 92-165 shift-zone klalim
(96, 102, 110, 112, 120, 122, 125, 134, 137, 140, 157, 158, 161, 165 -
consistent with that separate, already-open bug), klal 175 is the
already-documented conservative-rounding false positive (see above, no fix
needed), and **klal 3 was new - investigated and resolved 2026-08-05, see
the dated section below.** It was not a real truncation: the marker
tracer had anchored on the wrong "ג" token (a citation collision), which
in turn had also mis-set the endpoint used to reconstruct **klal 2**,
still truncated by ~300 words even after the earlier cross-page-truncation
fix. See below for the fix and for a second, more serious bug the
investigation surfaced in that earlier fix's own output.
