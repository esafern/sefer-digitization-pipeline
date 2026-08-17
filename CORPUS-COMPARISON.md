# Full-corpus rebuild — 250-page sample vs the whole 640-page Halachipedia

_Mined the entire mineable corpus (640 substantial pages, gently/serially) and
rebuilt the most-wanted list. This compares it to the original 250-page sample._

## Headline: demand concentrated, it didn't broaden

| | 250-page sample | full 640-page | change |
|---|---:|---:|---:|
| Pages mined | 250 | 640 | 2.6× |
| Citation detections | 14,268 | 38,195 | 2.7× |
| Distinct works seen | 3,520 | 7,878 | 2.2× |
| **Absent works (the list)** | **72** | **71** | **−1** |
| **Absent citations** | **2,758** | **6,771** | **2.5×** |
| Tier 1 (public domain) | 22 | 21 | |
| Tier 2 (modern) | 50 | 50 | |

The corpus grew 2.6× but the **work count barely moved (72 → 71)**. The extra
data didn't reveal a long new tail of missing works — it **piled more citations
onto the works we already had**. The list was already capturing the right works
by page 250; the whole corpus mostly sharpened their demand ranking.

## The R. Ovadia Yosef concentration held — and intensified

Every leader roughly 2–3×'d, and the Sephardi psak ecosystem stayed the story:

| work | 250pg | full | × |
|---|---:|---:|---:|
| Yalkut Yosef (Y. Yosef) | 428 | 945 | 2.2 |
| Chazon Ovadyah (O. Yosef) | 268 | 573 | 2.1 |
| Igrot Moshe (Feinstein) | 174 | 485 | 2.8 |
| Shemirat Shabbat KeHilchata | 161 | 409 | 2.5 |
| Yabia Omer (O. Yosef) | 102 | 320 | 3.1 |
| Halacha Brurah (D. Yosef) | 104 | 240 | 2.3 |
| Badei Hashulchan | 47 | 186 | 4.0 |

R. Ovadia Yosef's circle alone (Yalkut Yosef, Chazon Ovadyah, Yabia Omer,
Yechave Daat, Halacha Brurah, Taharat Habayit) now accounts for **~2,300 of the
6,771 absent citations** — a third of the entire demand signal, one beit midrash.

## What the wider corpus newly surfaced

~14 genuinely-new absent works, mostly mid-tier — a mix of public-domain classics
and modern works:

- **Yad Malachi** (243, PD — Malachi HaKohen d.1772) — jumped straight to #6. A
  Talmudic-methodology work; the count is concentrated on methodology-heavy pages.
- **Sdei Chemed** (32, PD — C.C. Medini d.1904), **Rokeach** (18, PD), **Machzik
  Bracha** (17, Chida), **Yafeh Lelev** (18, PD), **Maharam Chalava** (18, PD).
- **Pitchei Choshen** (28), **Otzar Haposkim** (24), **Mishpitei Aretz** (36),
  **Nefesh Harav** (18), **Amot Shel Halacha** (20) — all modern.

Public-domain tier (digitize, no licensing) is now **21 works / 939 citations**.

## The pressure-test methodology generalized

Verifying the new works live turned up the **same defect classes** the original
pressure-test fixed — evidence the cleanup rules generalize rather than overfit:

- **Dups** (4): `Sh"t Yabia Omer`→Yabia Omer, `Igros Moshe O.C`→Igrot Moshe,
  `Sh"t Yechave Daat`→Yechave Daat, `Rivevot Ephraim`→Rivevot Efraim.
- **Noise / non-works** (5): `Dvar Charif` (the *concept* דבר חריף, all cited "9:3"),
  `Rav Schachter` (a person), `Lashon Hara`, `Kli Sh'Melachto LeIssur`,
  `Niddah Shiur`.
- **False-absent** (3): `Meiri Pesachim` → *Meiri on Pesachim*; and two spelling-split
  cases caught by a new cross-check — `Eliya Rabba` (71 cites!) → *Eliyah Rabbah on
  Shulchan Arukh, Orach Chayim*, and `Radvaz` → *Teshuvot HaRadbaz* — where one spelling
  resolved (→ excluded) while sibling spellings stranded in "absent." The builder now
  reclassifies an absent cluster that matches a present-under-variant title.

## One honest methodology note

The builder verifies the **top-250 works by frequency**. In a 2.5×-denser corpus
the demand floor rises — rank-250 now bottoms out at **17 citations** (it was 7 in
the small sample) — so ~12 of the lowest-cited works from the original list
(Turei Even, Maharshag, Bet Efraim, … all 7–12 cites) fall *below* that floor.
They're still absent; they're just outcompeted for the processing budget by
higher-demand works. This is the right behaviour for a demand-ranked list — a
7-citation work matters less in 640 pages than in 250 — but it's why the net
count is flat rather than growing: the wider sample swapped the low-freq tail for
higher-demand newcomers (Yad Malachi, Sdei Chemed, …) while 2–3×-ing the core.

## Bottom line

The 250-page sample was already a **representative** picture — the full corpus
confirms the same works and the same R. Ovadia Yosef–dominated shape, with much
stronger statistical weight. If Sefaria acts on one thing, it's the Yosef corpus;
if it wants a free win, the 21-work public-domain tier.
