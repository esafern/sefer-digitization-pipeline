# The open dispute queue, ordered by posterior

362 open dispute(s), scored by `tools/rank_dispute_queue.py`. **Regenerate after any apply** - the queue and the calibration both move.

`posterior` is P(a reviewer adopts the consensus reading), estimated from the stratum this dispute falls in, under a Beta(1,1) posterior so a thin stratum cannot read as a certainty. The interval is 90% credible. **This orders attention; it decides nothing** - every row still needs the ink.

Calibrated on **266 ledger rulings** that recorded a consensus reading; 196 of them adopted it, a base rate of 74%. That base rate is the FALLBACK only - the strata below differ from it by more than 60 points, which is the whole reason this file exists.

## What each stratum is worth

| engines agreeing | n | adopted | posterior | 90% CI |
|---|---:|---:|---:|---|
| `dicta,surya,vlm` | 43 | 43 | 98% | 93%–100% |
| `dicta,vlm` | 41 | 35 | 84% | 74%–92% |
| `dicta,surya` | 37 | 30 | 79% | 68%–89% |
| `surya,vlm` | 109 | 82 | 75% | 68%–81% |
| `dicta,docai,surya,vlm` | 1 | 1 | 67% | 22%–97% ⚠ thin (n<8); ranking falls back to the engine count |
| `dicta,docai,vlm` | 1 | 1 | 67% | 22%–97% ⚠ thin (n<8); ranking falls back to the engine count |
| `docai,surya,vlm` | 10 | 2 | 25% | 8%–47% |
| `docai,vlm` | 8 | 1 | 20% | 4%–43% |
| `docai,surya` | 16 | 1 | 11% | 2%–25% |

**Every set containing DocAI scores low and that is mostly SELECTION.** Candidates are generated from DocAI's disagreements with the corpus, so a DocAI-involved consensus is disproportionately re-proposing a word that vision adjudication or a human has already settled. Read it as "this position has probably been looked at already", not as "DocAI is unreliable".

## The queue, by band

| posterior | disputes |
|---|---:|
| >=0.75 | 280 |
| >=0.50 | 45 |
| >=0.25 | 2 |
| <0.25 | 35 |

## The top 40

Highest posterior first - the disputes most likely to be genuine corpus errors, and so the cheapest place for a reviewer to start.

- **98%** [klal 12 · w271](http://127.0.0.1:8420/klal/12/word/271) — corpus `לייה` → consensus `ל"ה` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **98%** [klal 23 · w653](http://127.0.0.1:8420/klal/23/word/653) — corpus `ואיהן` → consensus `ואיהו` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **98%** [klal 23 · w710](http://127.0.0.1:8420/klal/23/word/710) — corpus `ע"ר` → consensus `ע"ד` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **98%** [klal 25 · w20](http://127.0.0.1:8420/klal/25/word/20) — corpus `אשנח` → consensus `אשגח` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **98%** [klal 25 · w400](http://127.0.0.1:8420/klal/25/word/400) — corpus `להן` → consensus `להו` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **98%** [klal 30 · w1263](http://127.0.0.1:8420/klal/30/word/1263) — corpus `גכי` → consensus `גבי` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **98%** [klal 30 · w1650](http://127.0.0.1:8420/klal/30/word/1650) — corpus `הכ"ס` → consensus `הכ"מ` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **98%** [klal 33 · w124](http://127.0.0.1:8420/klal/33/word/124) — corpus `לדם` → consensus `להם` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **98%** [klal 37 · w96](http://127.0.0.1:8420/klal/37/word/96) — corpus `ב"ט` → consensus `ב"מ` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **98%** [klal 39 · w272](http://127.0.0.1:8420/klal/39/word/272) — corpus `הנה` → consensus `הוה` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **98%** [klal 41 · w105](http://127.0.0.1:8420/klal/41/word/105) — corpus `יהין` → consensus `יהיו` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **98%** [klal 41 · w110](http://127.0.0.1:8420/klal/41/word/110) — corpus `רוא` → consensus `הוא` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **98%** [klal 41 · w123](http://127.0.0.1:8420/klal/41/word/123) — corpus `שהכ"ס` → consensus `שהכ"מ` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **98%** [klal 41 · w217](http://127.0.0.1:8420/klal/41/word/217) — corpus `הגדות` → consensus `הגהות` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **98%** [klal 41 · w256](http://127.0.0.1:8420/klal/41/word/256) — corpus `כתכו` → consensus `כתבו` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **98%** [klal 41 · w282](http://127.0.0.1:8420/klal/41/word/282) — corpus `לדם` → consensus `להם` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **98%** [klal 41 · w289](http://127.0.0.1:8420/klal/41/word/289) — corpus `ולא` → consensus `דלא` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **98%** [klal 41 · w398](http://127.0.0.1:8420/klal/41/word/398) — corpus `במילתיהן` → consensus `במילתיהו` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **98%** [klal 41 · w660](http://127.0.0.1:8420/klal/41/word/660) — corpus `רשלשה` → consensus `דשלשה` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **98%** [klal 41 · w750](http://127.0.0.1:8420/klal/41/word/750) — corpus `זרה` → consensus `זה` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **98%** [klal 41 · w753](http://127.0.0.1:8420/klal/41/word/753) — corpus `דוי` → consensus `הוי` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **98%** [klal 42 · w18](http://127.0.0.1:8420/klal/42/word/18) — corpus `כתשובותיו` → consensus `בתשובותיו` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **98%** [klal 42 · w29](http://127.0.0.1:8420/klal/42/word/29) — corpus `דקטא` → consensus `דקמא` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **98%** [klal 43 · w102](http://127.0.0.1:8420/klal/43/word/102) — corpus `וכשמחתינן` → consensus `דכשמחתינן` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **98%** [klal 44 · w102](http://127.0.0.1:8420/klal/44/word/102) — corpus `ל"ר` → consensus `ל"ד` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **98%** [klal 44 · w162](http://127.0.0.1:8420/klal/44/word/162) — corpus `דרפקר` → consensus `דהפקר` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **98%** [klal 44 · w362](http://127.0.0.1:8420/klal/44/word/362) — corpus `לירחית` → consensus `לידחות` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **98%** [klal 44 · w407](http://127.0.0.1:8420/klal/44/word/407) — corpus `הגחל` → consensus `הגדול` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **98%** [klal 48 · w7](http://127.0.0.1:8420/klal/48/word/7) — corpus `בדליכאי` → consensus `בדליכא` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **98%** [klal 51 · w145](http://127.0.0.1:8420/klal/51/word/145) — corpus `להן` → consensus `להו` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **98%** [klal 54 · w415](http://127.0.0.1:8420/klal/54/word/415) — corpus `כין` → consensus `בין` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **98%** [klal 54 · w822](http://127.0.0.1:8420/klal/54/word/822) — corpus `שרקשה` → consensus `שהקשה` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **98%** [klal 54 · w972](http://127.0.0.1:8420/klal/54/word/972) — corpus `שביתת` → consensus `שבת` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **98%** [klal 74 · w879](http://127.0.0.1:8420/klal/74/word/879) — corpus `ל"ר` → consensus `ל"ד` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **98%** [klal 75 · w5](http://127.0.0.1:8420/klal/75/word/5) — corpus `ר"ס` → consensus `ר"פ` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **98%** [klal 75 · w156](http://127.0.0.1:8420/klal/75/word/156) — corpus `משים` → consensus `משום` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **98%** [klal 75 · w203](http://127.0.0.1:8420/klal/75/word/203) — corpus `ר"ס` → consensus `ר"מ` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **98%** [klal 75 · w222](http://127.0.0.1:8420/klal/75/word/222) — corpus `בס'` → consensus `בפ'` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **98%** [klal 75 · w853](http://127.0.0.1:8420/klal/75/word/853) — corpus `משכו` → consensus `משמו` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)
- **98%** [klal 75 · w1058](http://127.0.0.1:8420/klal/75/word/1058) — corpus `נהמן` → consensus `נחמן` (dicta, surya, vlm); cross-edition (**2** Berlin engine(s) dissent)

## Limits

1. The calibration is positions a human RULED ON. If the easy disputes were worked first, the untouched queue is harder than this sample says (Lesson 27).
2. A stratum marked thin has fewer than 8 observations and falls back to the engine COUNT, or to the whole sample, rather than being trusted on its own.
3. This is not `tools/estimate_consensus_posterior.py`'s number and does not replace it. That one arbitrates UNDECIDED positions with vision to ask whether consensus may ever auto-approve (it may not, ~31%). This one asks a different question - what should a human open first - and answers it from what humans actually did.
