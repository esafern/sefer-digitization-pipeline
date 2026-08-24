# Master Specification: Multi-Witness Typographic Repair & Consensus Synthesis

> **Status:** Working architecture. Partly built, partly specified — every
> section below is marked **BUILT**, **SPECIFIED**, or **OPEN QUESTION**, and
> nothing is described as done that is not.
> **Target Corpus:** 19th/20th-Century Rabbinic Hebrew/Aramaic Print & Manuscript Editions
> **Scope:** Part 1 only. Parts 2–3 are gated — see §7.
> **Revised 2026-08-23** after the first real synthesis run measured results that
> contradicted this document's central mathematical claim. See §2.

---

## 0. What changed in this revision, and why

The first version of this document described a design that had not been run.
When it was built and run, three things in it turned out to be wrong, and they
are corrected here rather than quietly edited:

1. **The independence proof in §2 is false for this corpus.** It priced two
   engines agreeing on the same wrong token at 3.5 × 10⁻⁷. One Part-1 run
   produced **37 counterexamples**, including unanimous 3-of-3 agreement. §2 is
   rewritten around the measured result.
2. **Two headline accuracy figures were unsourced.** "94.5%" for the VLM and
   "32.4%" for Surya appear nowhere in this repository. The measured numbers,
   with their sources, are in §1.
3. **The roadmap's Phase 4 collided with a binding project rule** (the Parts 2–3
   gate) without mentioning it. §7 states the gate.

This project has a documented history of two fabricated figures reaching its own
status file (`PROJECT-STATUS-HISTORY.md`, 2026-08-21 integrity audit). Every
number below therefore names where it comes from, and anything not measured is
labelled as an estimate.

---

## 1. The Core Problem: Engine-Specific Blind Spots — **BUILT**

Single-engine OCR fails on 19th-century Rabbinic typography through systematic,
engine-specific blind spots:

| Engine | Role | Measured performance | Source |
| :--- | :--- | :--- | :--- |
| **Google Document AI** | Primary extraction | Disagrees with stored text on **1.02%** of Part-1 words (538 of 52,630) | `corrections_verified_part1.json` |
| **Gemini 3.6 Flash (VLM)** | Witness 2 + adjudicator | **93.34%** token accuracy; **87.43%** Pass-A/Pass-B self-consistency | `tools/second_witness_eval/part1_full_baseline_accuracy_report.txt` |
| **Surya OCR (local)** | Witness 3 | **~70%** mean token agreement vs. stored text across 219 covered klalim | measured 2026-08-23, `surya_part1_full_baseline.txt` |

**Read the DocAI figure carefully.** It is a *disagreement rate against a base
text that DocAI itself helped produce*, not an independent error rate. There is
no unbiased error rate for the primary engine in this pipeline, and claiming one
would be circular.

Known blind spots, each observed in this corpus:

* **DocAI** — drops the `ל` from the alef-lamed ligature (`ﭏ`), splits
  abbreviation punctuation, and occasionally drops standalone section markers.
* **Gemini VLM** — strong on semantics and acronyms, but carries **circularity
  risk**: it is also the adjudicator, violating `PROPOSED_PIPELINE_ARCHITECTURE.md`
  Directive #1. Also shows repetition-loop hallucinations on low-contrast lines
  and occasional early stop on long crops.
* **Surya** — runs locally on Apple Silicon with zero API cost and good layout
  recognition, but shows **gershayim-to-yod blindness** (`ז"ל` → `זיל`) and font
  confusion (`פ` ↔ `מ`). It also returns *layout blocks*, which merge
  consecutive short klalim — see §3.1.

---

## 2. Signal vs. Noise in Multi-Witness Ensembles — **REWRITTEN 2026-08-23**

### A. The noise risk of unweighted disagreement — still valid

Flagging every word where **any** witness disagrees with the base text produces
noise dominated by the weakest engine. With Surya's ~30% disagreement rate, a
union rule over three witnesses flags on the order of **a third of the corpus** —
tens of thousands of items, most of them Surya's predictable acronym artifacts.
This is why the pipeline uses a consensus rule rather than a union rule, and that
reasoning is unchanged.

### B. The decoupling argument — **FALSE AS ORIGINALLY STATED**

The original text argued that because the engines have orthogonal architectures,
the probability of two producing the *same* wrong token is bounded by
ε₁ × ε₂ × 1/|V| ≈ 3.5 × 10⁻⁷, so a 2-of-N agreement is correct with probability
> 99.9999%.

**This does not hold, and the failure is not marginal.** The first full synthesis
run over Part 1 found **37 positions where two or three engines agreed on the
same wrong reading**, including unanimous DocAI + Surya + VLM agreement. Every
one is the same artifact: the alef-lamed ligature losing its `ל` —
`ושמואל`→`ושמוא`, `אליבא`→`איבא`, `אליהו`→`איהו`, `אלגאזי`→`אגאזי`, `ואל`→`וא`.

**Why the argument fails.** The `1/|V|` term assumes a wrong reading is drawn
roughly uniformly from a 50,000-word vocabulary. It is not. Every engine is
reading *the same ink*, and where the ink itself carries a defect — a single
worn or ambiguous printer's sort — all three fail toward the *same visually
plausible* neighbour. Architectural independence is irrelevant to a defect that
is upstream of every architecture. The remaining independence is real but far
weaker than a 1/|V| factor implies.

**A second, narrower error:** the pipeline as first built counted VLM Pass A and
Pass B as two witnesses. They are one model sampled twice (87.43% measured
self-consistency), so their agreement carries no independence at all. Corrected —
see §3.4.

### C. What replaces it

Two rules, both now enforced in code:

1. **A witness is an engine, not a sample.** Consensus requires two *distinct*
   engines. Pass A/Pass B agreement is a stability gate on the single VLM
   witness: where the two passes disagree, the VLM abstains rather than votes.
2. **A consensus every engine can reach through one shared ink defect is not
   corroboration.** Agreements matching a catalogued typographic artifact are
   tagged as such and must not be treated as evidence against the stored text.

### D. The posterior, measured — **~26–41%, not >99.9999%**

Quantified 2026-08-23 (`tools/estimate_consensus_posterior.py`), using stage 3's
crop-level vision adjudication as arbiter on the 176 *undecided* consensus
positions:

| subset | n | posterior |
| :--- | ---: | ---: |
| all undecided consensus | 56 | 41% |
| + catalogued artifacts dropped | 51 | 39% |
| **VLM-free (arbiter independent of both witnesses)** | 27 | **30%** |
| + confidence gate + artifacts dropped | 23 | **26%** |
| unanimous 3-of-3 | 4 | 50% |

**Two-of-three agreement is worth roughly a coin flip at best, and about one in
four when the arbiter is genuinely independent.** Dropping catalogued ligature
artifacts barely moves it (41% → 39%), so the known sort is not what makes
consensus weak — consensus is simply weak.

**The VLM-free gap is itself a measurement of the circularity gap.** Where the
VLM is one of the agreeing engines, the Gemini arbiter backs the consensus 52%
of the time; where it is not, 30%. That 22-point spread is what Directive #1's
violation is worth in practice.

**What the human-decision sample says, and why it is NOT the posterior.** Forty
consensus positions carry a human decision, and in 39 the reviewer kept the
stored text. That sample is adversarially selected — a reviewer looked at those
words and confirmed the corpus, so consensus loses by construction. It supports
exactly one conclusion, already enforced in code: **consensus must not reopen
human-confirmed positions.**

*Limits:* vision is a fourth opinion, not ground truth; only DocAI-involved
positions carry a verdict, and those are the *strongest* consensus cases, which
makes this more damning for the surya+vlm majority rather than less; n is small.
Re-run the tool as review decisions accumulate.

---

## 3. Engine Repair Filters

### 3.1 Surya block re-segmentation — **BUILT**

Surya returns *layout* blocks and routinely groups consecutive short klalim into
a single `<p>`. The assembler originally assigned each block to a klal by the
block's vertical centre, so a merged block went entirely to one klal and the
other received nothing — and an empty body was then read downstream as "this
witness agrees with every word" rather than "this witness has no reading".
**10 of Part 1's 222 klalim were empty for this reason.**

`split_block_across_klalim()` in `tools/run_surya_part1_full_baseline.py` cuts a
merged block at each covered klal's gematria marker, using
`build_gematria_trace.near_miss_variants` so a misread numeral still anchors.
Three guards, each added after a measured failure:

* Genuine-overlap epsilon — a block starting exactly on the previous klal's
  bottom edge must not "cover" it.
* A missing marker does not advance the search cursor (otherwise one absent
  numeral swallows every klal after it).
* A positional guard — a cut must land roughly where that klal's region sits in
  the block, or a numeral-shaped word in ordinary prose becomes a false cut.

**Coverage: 212/222 → 219/222.**

### 3.2 DocAI ligature repair — **BUILT 2026-08-24**

`pipeline/typography.py` catalogues the alef-lamed and chet-zayin sorts and
provides `dropped_lamed_explains()`, which recognises a reading that is the
stored word minus one `ל` after an `א`. This is used to *tag* consensus
agreements, not to rewrite text.

**BUILT: `pipeline/repair_filters/docai_filter.py`.** Measured 2026-08-24 against a reviewer's complete decision set
for klal 91: DocAI agrees with the human on **0 of 18** words raw, and **17 of 18
(94%)** once the dropped `ל` is restored. Surya goes 10% → 90%. The primary
engine is reading the ink correctly and nothing downstream expands the ligature,
so its correct readings are being discarded as errors. Expanding `אא` → `אלא`
etc. is what turns that around.

**Validated before being trusted, per §3.5, against two independent human
samples:** the reviewer's complete 22-decision review of klal 91 (DocAI 0/18 raw
→ **17/18, 94%** repaired, **zero words made worse**), and every candidate the
reviewer had already resolved by hand that the filter now classifies as a pure
artifact — **106 of 106 agreement**, the reviewer having kept the stored text in
every one.

**Arbiter:** `sefaria_reference_corpus` only. `lexicon.txt` is unusable here — it
was built from this corpus's own OCR and "absorbed and then validated the
alef-lamed ligature corruption" — and the vision adjudicator is unusable for the
same reason a fourth reader of the same pixels always is (§2B).

**Impact:** 137 of 498 Part-1 candidates carry a repairable DocAI reading, and
**118 (24%) repair to EXACTLY the stored text** — the disagreement was the
ligature and nothing else, so there is no reading to choose between. Those are
flagged `docai_ligature_artifact` and drop out of the reviewer's open queue.

**The raw `docai_reading` is never overwritten.** The repair is offered
alongside it as `docai_repaired`; success criterion #1 forbids silent
normalisation, and the reviewer must be able to see what the engine actually
produced. Items are flagged, never deleted (Lesson 26).

**Known limitation:** a prefixed collapsed form (`ש"איבא`) is left alone, because
the expanded form is not attested standalone in the reference corpus. Measured as
a miss, not a wrong repair. Note `tools/detect_ligature_corruption.py` already
handles the reverse direction — a corrupt form stored *in the corpus* — and its
header explains why an ingest-level fix is impossible: DocAI collapses the
ligature before this repo ever sees the text.

### 3.3 Gershayim recovery (Surya) — **SPECIFIED**

Detect internal `י`/`יי` and test whether substituting `"` yields a recognised
Rabbinic acronym (`זיל`→`ז"ל`, `דיה`→`ד"ה`, `הניל`→`הנ"ל`).

### 3.4 VLM stability gating — **BUILT**

Pass A/Pass B disagreement makes the VLM abstain at that position. Measured:
**1,577 abstentions** across Part 1 — exactly the positions the pre-correction
pipeline counted as "dual-VLM consensus".

### 3.5 Filter validation — **HARNESS BUILT 2026-08-24; 2 of 4 filters measured**

Every filter in this section transforms a witness *before* it votes. A wrong
filter therefore does not produce a visible disagreement — it **erases** one, and
silence where a check cannot operate is not evidence of correctness (Lesson 15).

**Correction to an earlier framing in this document's own history:** this was
once deprioritised as "only matters once a filter rewrites text, and none does".
That was wrong twice over. The filters are *why the reviewer's queue is usable* —
they exist to keep engine artifacts from becoming disputes — which is exactly
why they decide what a human is permitted to see. And a wrong SUPPRESSION is
harder to catch than a wrong rewrite, not softer: it produces silence, and
silence where a check cannot operate is not evidence (Lesson 15, Lesson 26).

**Scale, measured 2026-08-24.** The live filters suppress **~12,400** items
against **216** disputes reaching a reviewer — they decide roughly 98% of the
review surface:

| filter | suppresses | validated? |
| :--- | ---: | :--- |
| VLM Pass-A/B stability gate | 1,577 | **measured**: 61 false negatives (another engine independently agreed) |
| `align_witness` ragged-block drop | 10,455 | unmeasured — unfalsifiable by construction |
| Witness-queue vision filter | 375 | partial — the 16/419 Tesseract measurement |
| Ligature-artifact tagging | 37 | **measured**: 34/37 corroborated |

`tools/validate_suppression_filters.py` reports these. Two findings from
building it are worth more than the numbers:

* **Picking the arbiter is the hard part, and two obvious choices were circular.**
  Validating the ligature tag against *vision* is Lesson 24 applied to one's own
  method — vision is a fourth reader of the same pixels, so it cannot arbitrate a
  pixel-level defect (it "disagreed" with 14 of 37 tags, because it read the
  corrupted glyph too). Validating against `lexicon.txt` fails differently: that
  file was built from this corpus's own OCR and, per
  `tools/validate_lexicon_independent.py`, "absorbed and then validated the
  alef-lamed ligature corruption". Only `sefaria_reference_corpus` — 6.18M words
  that never saw this scan — is independent for this question.
* **The tag has a real blind spot.** Its one contradicted case is klal 200 w58,
  `אליהו` → `איהו`: the ligature produced a corrupt form that is itself a common
  word (Aramaic "he"), so frequency cannot arbitrate and only context can. This
  is the real-word-substitution class `tools/detect_real_word_substitution.py`
  exists for, reached from the other direction.

No filter may be promoted from tagging to rewriting until it has a measured
rate against an independent signal, recorded in `PROJECT-STATUS.md`. §3.1 alone
needed three iterations, and one intermediate version silently cost three
klalim 30–360 words each.

---

## 4. Consensus Decision Matrix — **BUILT, WITH ONE OPEN POLICY QUESTION**

| Condition | Pipeline resolution | Status |
| :--- | :--- | :--- |
| All witnesses agree with the stored text | No candidate produced | **BUILT** — the common case; costs nothing |
| DocAI disagrees with stored text | Vision-adjudicated candidate → human review | **BUILT** — the existing corrections pipeline |
| Two *distinct* engines agree against the stored text | Consensus dispute → human review, with per-engine attribution | **BUILT** — 176 disputes in Part 1 |
| Two engines agree, but a catalogued ligature artifact explains it | Surfaced **tagged as an artifact**; stored text presumed correct | **BUILT** |
| Three-way split / lexicon gap | Human review queue | **BUILT** |

### The open policy question: auto-approval

The original version of this matrix auto-approved 2-of-3 consensus with **"0 sec"**
human review. That is not implemented, and it should not be implemented without
an explicit decision, for two reasons:

1. **It contradicts success criterion #1** — every correction must be "resolved
   by looking at the actual scan, not inferred" — and the record/apply split that
   keeps machine output separate from human judgement.
2. **It would have caused measurable damage.** Of the 40 positions where the
   consensus contradicts a recorded human decision, **32 are the ligature
   artifact**. Auto-approval would have reverted correct human decisions to the
   corrupted reading.

**Recommendation, now with a measured number behind it:** keep every consensus
dispute human-reviewed. §2D puts P(consensus correct) at **~26–41%** — auto-
approval would introduce errors at roughly the rate it fixes them. Even the
unanimous 3-of-3 subset measures 50% (n=4), so the "safe first step" floated in
the earlier revision is not safe either. Consensus is a triage signal, not a
decision procedure, and should be treated as one until a genuinely independent
arbiter exists (§8 item 4).

---

## 5. How this plugs into the existing pipeline — **BUILT**

The original document did not say where any of this ran, which is why the first
implementation wrote its results directly into `corrections_part1.json` — a
**derived** file that `./rebuild_all.sh` regenerates from scratch. 1,108 items
and any review time spent on them were one rebuild away from deletion.

The rule that prevents a repeat: **a witness contributes a source file the
pipeline reads; it never edits the pipeline's own output.**

```
rebuild_all.sh
  1/6  build_klalim_demo_dataset.py
  2/6  build_corrections_dataset.py     DocAI vs stored text -> candidates
  3/6  verify_corrections_vision.py     vision adjudication (the only paid stage)
  4a/6 synthesize_multi_witness.py      <- witnesses in, consensus_disputes_part1.json out
  4/6  assemble_corrections_dataset.py  <- merges 4a's output; writes corrections_part1.json
  5/6  build_klal_page_regions.py
  6/6  pytest (hard gate)
```

Witness baselines (`vlm_part1_full_baseline*.txt`, `surya_part1_full_baseline.txt`)
are inputs produced by separate, manually-run scripts — Surya is local and free,
the VLM passes are paid. Stage 4a is pure local computation and therefore lives
inside the gated chain.

Two corpus invariants enforce this: every item in `corrections_part1.json` must
trace to stage 3 or stage 4a, and no item may report an engine reading identical
to the stored text.

---

## 6. Current state — Part 1

| Metric | Value |
| :--- | :--- |
| Corrections dataset | 658 items (538 vision-adjudicated + 176 consensus, deduplicated) |
| Consensus disputes | 176 across 85 klalim |
| Agreements explained by a ligature artifact | 37 |
| VLM abstentions (Pass A/B instability) | 1,577 |
| Surya coverage | 219 / 222 klalim |
| Klalim with no Surya reading | 3 (49, 129, 201) — counted as an **absent witness**, never as agreement |

---

## 7. Parts 2–3 — **GATED, NOT SCHEDULED**

**There is currently no witness set for Parts 2–3 at all.** `corrections_part2.json`
and `corrections_part3.json` are both empty `{}` (emptied 2026-08-20 when 312
fabricated "VLM Verified" candidates were pulled). The 419-item
`reconstruction_witness_queue.json` is DocAI-vs-Tesseract and covers klalim 30,
75 and 88 — **all Part 1**. So Parts 2–3 work does not mean "run the existing
pipeline there"; it means building a witness set from zero.

*Open provenance question, flagged rather than assumed:* the ~2,088 Parts 2–3
flags purged on 2026-08-20 carry reviewer tags naming the lexicon-gap detector
(1,745) and the dropped-lamed detector (320), not Tesseract — but
`PROJECT-STATUS.md`'s own TL;DR describes them as "Tesseract/lexicon-gap"
auto-flags, and this repo excludes the `archive/` directory where a Tesseract
pass could have lived. If any Parts 2–3 signal was in fact Tesseract-derived,
that is a reason to rebuild rather than reuse it: this project measured Tesseract
correct in only 16 of 419 disagreements (3.8%) against DocAI's 91.2%, and
concluded it "fails structurally, being a weaker engine on the *same* scan rather
than an independent signal."

**Running this pipeline over Parts 2–3, or exporting certified Parts 2–3 text, is
not authorized by this document.** `START_HERE.md`'s Parts 2–3 gate is binding:
building infrastructure is permitted (2026-08-17 supersede); *applying* any
`part2.json`/`part3.json` correction requires its own explicit go-ahead **and**
independent confirmation by an outside professional that Part 1 is clean.

The original roadmap listed "run the synthesis pipeline across Parts 2 and 3" and
"export certified final text" as ordinary next steps. That was wrong and is
removed. The rationale is not caution for its own sake: the page-furniture
contamination bug hit Part 1 at ~1 instance and Parts 2–3 at 74/445 klalim
(~17%), and Parts 2–3's own alignment data is known to be wrong for 391 of 445
klalim.

---

## 8. Open items

1. **Quantify the posterior — DONE 2026-08-23, and it settles the auto-approval
   question: ~26–41%** (§2D). Auto-approval on 2-of-3 consensus is indefensible
   at any threshold this data supports. Consensus remains valuable as a TRIAGE
   signal — it surfaces words worth a human look — but it is not a decision
   procedure. Re-run `tools/estimate_consensus_posterior.py` as decisions
   accumulate.
2. **Enumerate the printer's defective sorts — DONE 2026-08-23, result below.**
   `tools/survey_shared_engine_errors.py` classified all 216 multi-witness
   agreements by their corpus→consensus transformation, separating ink defects
   (context-locked, raised unanimity) from engine confusions (scattered, ~zero
   unanimity). **Exactly one context-locked ink defect exists at detectable
   frequency: the alef-lamed ligature (37 instances, 100% locked after `א`).**
   16 of the 18 classified transformations have zero unanimous agreements. The
   catalogue is not missing a second ink-level defect at that frequency.
   *Open residue:* 4 unanimous agreements are unexplained by a catalogued sort,
   3 of them `כ→ב` (including `איכא`→`איבא` twice in klal 91). Rendered: the ink
   reads as `ב` in both, identically — consistent with either a damaged `כ` sort
   or a genuine corpus error. Needs a scholar, not more pixels. **Standing
   limit:** this method is blind to a defect baked into the corpus itself, since
   no disagreement would remain to detect.
3. **Filter validation harness — BUILT 2026-08-24** (§3.5). 2 of 4 filters now
   have a measured rate against an independent signal; the `align_witness`
   ragged-block drop (10,455 slots) and the witness-queue filter (375) remain
   justified by argument rather than measurement, and closing the former needs a
   hand-checked sample rather than another derived signal.
4. **A genuinely independent third engine.** Gemini is both witness 2 and
   adjudicator — `PROPOSED_PIPELINE_ARCHITECTURE.md` Directive #1 is still
   violated. Dicta is the leading candidate; Kraken is blocked on a macOS
   torch-wheel constraint.
5. **3 klalim with no Surya reading** (§6) — **two levers tried, both ruled out
   2026-08-23.** A plain re-run is futile: Surya is deterministic and the
   re-OCR of pages 30/48/73 came back byte-identical. Higher input resolution is
   not the lever either: at 300 DPI (4.7 MP vs the cached 1.1 MP) klal 49's `מט`
   and klal 129's `קכט` are *still* unread, though the block segmentation changes
   substantially. Klal 201's own marker IS read, but its block holds no second
   anchor (klal 202's `רב` is absent from Surya's output too), so the 201/202
   boundary cannot be located without inventing one — which §3.1's guards exist
   to prevent. **These three are structurally uncovered by Surya as configured,
   not pending a re-run.** Closing them needs a different engine or a different
   Surya configuration, and the current handling — report by name, count as an
   absent witness — is correct in the meantime.
