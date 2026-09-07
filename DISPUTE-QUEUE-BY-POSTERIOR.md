# The open dispute queue, ordered by posterior

402 open dispute(s), scored by `tools/rank_dispute_queue.py`. **Regenerate after any apply** - the queue and the calibration both move.

`posterior` is P(a reviewer adopts the consensus reading), estimated from the stratum this dispute falls in, under a Beta(1,1) posterior so a thin stratum cannot read as a certainty. The interval is 90% credible. **This orders attention; it decides nothing** - every row still needs the ink.

Calibrated on **225 ledger rulings** that recorded a consensus reading; 166 of them adopted it, a base rate of 74%. That base rate is the FALLBACK only - the strata below differ from it by more than 60 points, which is the whole reason this file exists.

## What each stratum is worth

| engines agreeing | n | adopted | posterior | 90% CI |
|---|---:|---:|---:|---|
| `dicta,surya,vlm` | 27 | 27 | 97% | 90%–100% |
| `dicta,surya` | 28 | 24 | 83% | 71%–93% |
| `dicta,vlm` | 36 | 30 | 82% | 70%–91% |
| `surya,vlm` | 104 | 80 | 76% | 69%–83% |
| `dicta,docai,surya,vlm` | 1 | 1 | 67% | 22%–97% ⚠ thin (n<8); ranking falls back to the engine count |
| `docai,surya,vlm` | 9 | 2 | 27% | 9%–51% |
| `docai,vlm` | 7 | 1 | 22% | 5%–47% ⚠ thin (n<8); ranking falls back to the engine count |
| `docai,surya` | 13 | 1 | 13% | 3%–30% |

**Every set containing DocAI scores low and that is mostly SELECTION.** Candidates are generated from DocAI's disagreements with the corpus, so a DocAI-involved consensus is disproportionately re-proposing a word that vision adjudication or a human has already settled. Read it as "this position has probably been looked at already", not as "DocAI is unreliable".

## The queue, by band

| posterior | disputes |
|---|---:|
| >=0.75 | 356 |
| >=0.50 | 12 |
| >=0.25 | 3 |
| <0.25 | 31 |

## The top 40

Highest posterior first - the disputes most likely to be genuine corpus errors, and so the cheapest place for a reviewer to start.

- **97%** [klal 12 · w271](http://127.0.0.1:8420/klal/12/word/271) — corpus `לייה` → consensus `ל"ה` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **97%** [klal 12 · w298](http://127.0.0.1:8420/klal/12/word/298) — corpus `מהרי"י` → consensus `מהר"י` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **97%** [klal 13 · w175](http://127.0.0.1:8420/klal/13/word/175) — corpus `לייג` → consensus `ל"ג` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **97%** [klal 17 · w51](http://127.0.0.1:8420/klal/17/word/51) — corpus `דב"ט` → consensus `דב"מ` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **97%** [klal 17 · w79](http://127.0.0.1:8420/klal/17/word/79) — corpus `וצייד` → consensus `וצ"ד` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **97%** [klal 18 · w58](http://127.0.0.1:8420/klal/18/word/58) — corpus `דאיתמרן` → consensus `דאיתמרו` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **97%** [klal 19 · w26](http://127.0.0.1:8420/klal/19/word/26) — corpus `לייב` → consensus `ל"ב` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **97%** [klal 19 · w34](http://127.0.0.1:8420/klal/19/word/34) — corpus `הר"יש` → consensus `הר"ש` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **97%** [klal 19 · w38](http://127.0.0.1:8420/klal/19/word/38) — corpus `בט"ש` → consensus `במ"ש` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **97%** [klal 23 · w653](http://127.0.0.1:8420/klal/23/word/653) — corpus `ואיהן` → consensus `ואיהו` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **97%** [klal 23 · w710](http://127.0.0.1:8420/klal/23/word/710) — corpus `ע"ר` → consensus `ע"ד` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **97%** [klal 25 · w20](http://127.0.0.1:8420/klal/25/word/20) — corpus `אשנח` → consensus `אשגח` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **97%** [klal 25 · w400](http://127.0.0.1:8420/klal/25/word/400) — corpus `להן` → consensus `להו` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **97%** [klal 25 · w521](http://127.0.0.1:8420/klal/25/word/521) — corpus `וכ"ש` → consensus `דכ"ש` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **97%** [klal 29 · w222](http://127.0.0.1:8420/klal/29/word/222) — corpus `ואחר` → consensus `ואחד` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **97%** [klal 30 · w250](http://127.0.0.1:8420/klal/30/word/250) — corpus `גכי` → consensus `גבי` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **97%** [klal 30 · w1165](http://127.0.0.1:8420/klal/30/word/1165) — corpus `כזה` → consensus `בזה` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **97%** [klal 30 · w1208](http://127.0.0.1:8420/klal/30/word/1208) — corpus `עכדו'` → consensus `עבדו'` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **97%** [klal 30 · w1263](http://127.0.0.1:8420/klal/30/word/1263) — corpus `גכי` → consensus `גבי` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **97%** [klal 30 · w1376](http://127.0.0.1:8420/klal/30/word/1376) — corpus `ראמו` → consensus `דאמו` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **97%** [klal 30 · w1650](http://127.0.0.1:8420/klal/30/word/1650) — corpus `הכ"ס` → consensus `הכ"מ` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **97%** [klal 33 · w124](http://127.0.0.1:8420/klal/33/word/124) — corpus `לדם` → consensus `להם` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **97%** [klal 37 · w96](http://127.0.0.1:8420/klal/37/word/96) — corpus `ב"ט` → consensus `ב"מ` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **97%** [klal 38 · w208](http://127.0.0.1:8420/klal/38/word/208) — corpus `גכי` → consensus `גבי` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **97%** [klal 39 · w272](http://127.0.0.1:8420/klal/39/word/272) — corpus `הנה` → consensus `הוה` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **97%** [klal 41 · w105](http://127.0.0.1:8420/klal/41/word/105) — corpus `יהין` → consensus `יהיו` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **97%** [klal 41 · w110](http://127.0.0.1:8420/klal/41/word/110) — corpus `רוא` → consensus `הוא` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **97%** [klal 41 · w123](http://127.0.0.1:8420/klal/41/word/123) — corpus `שהכ"ס` → consensus `שהכ"מ` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **97%** [klal 41 · w217](http://127.0.0.1:8420/klal/41/word/217) — corpus `הגדות` → consensus `הגהות` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **97%** [klal 41 · w256](http://127.0.0.1:8420/klal/41/word/256) — corpus `כתכו` → consensus `כתבו` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **97%** [klal 41 · w282](http://127.0.0.1:8420/klal/41/word/282) — corpus `לדם` → consensus `להם` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **97%** [klal 41 · w289](http://127.0.0.1:8420/klal/41/word/289) — corpus `ולא` → consensus `דלא` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **97%** [klal 41 · w398](http://127.0.0.1:8420/klal/41/word/398) — corpus `במילתיהן` → consensus `במילתיהו` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **97%** [klal 41 · w660](http://127.0.0.1:8420/klal/41/word/660) — corpus `רשלשה` → consensus `דשלשה` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **97%** [klal 41 · w750](http://127.0.0.1:8420/klal/41/word/750) — corpus `זרה` → consensus `זה` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **97%** [klal 41 · w753](http://127.0.0.1:8420/klal/41/word/753) — corpus `דוי` → consensus `הוי` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **97%** [klal 42 · w18](http://127.0.0.1:8420/klal/42/word/18) — corpus `כתשובותיו` → consensus `בתשובותיו` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **97%** [klal 42 · w29](http://127.0.0.1:8420/klal/42/word/29) — corpus `דקטא` → consensus `דקמא` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **97%** [klal 43 · w102](http://127.0.0.1:8420/klal/43/word/102) — corpus `וכשמחתינן` → consensus `דכשמחתינן` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **97%** [klal 44 · w102](http://127.0.0.1:8420/klal/44/word/102) — corpus `ל"ר` → consensus `ל"ד` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)

## Limits

1. The calibration is positions a human RULED ON. If the easy disputes were worked first, the untouched queue is harder than this sample says (Lesson 27).
2. A stratum marked thin has fewer than 8 observations and falls back to the engine COUNT, or to the whole sample, rather than being trusted on its own.
3. This is not `tools/estimate_consensus_posterior.py`'s number and does not replace it. That one arbitrates UNDECIDED positions with vision to ask whether consensus may ever auto-approve (it may not, ~31%). This one asks a different question - what should a human open first - and answers it from what humans actually did.
