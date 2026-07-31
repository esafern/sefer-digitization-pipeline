# Page 0: Highlighted Text Corrections Report

## Executive Summary
This report highlights all specific textual corrections made by the pipeline for **`test_page.pdf` (Page 0)** after diffing the clean Base text against the Tesseract OCR Witness stream and running Gemini 3.6 Flash visual adjudication.

* **Total Page Tokens**: 7162
* **Total Adjudicated Conflicts**: 42
* **Total Highlights / Corrections Made**: 18

---

## Reconstructed Corrected Text Stream (First 500 Characters)

```text
צפנת דף בי ב' ע"א צפנת קדושין דף ב' ע"א פענח א מתני' וקונה את עצמה בחליצה. גליון: למ"ד חליצה קנין ביר"ש פ"א ופ"ג דיבמות [נ"ל כך] דמ"מ הזיקה של המת פקעה תוס' סוף ד"ה בפרוטה וכו' לפדיון הבן וכו' גליון: אך באמת למה לא נימא דגבי ה וכו' לפדיו / פה"ב ב / כ"ז וסנ בעי שומא עיין לקמן דף ח' דמשמע דא"צ לשום ועיין ערכין דף כ"ז וסנהדרין דף ט"ו ומגילה כ"ד מתני'. וקונה את עצמה בחליצה. בכמה דוכתי בירושלמי מקשה רבי
בעי השוה רבינו2 אך באמת למה לא נימא דגבי פדיון הבן נחלקו אמוראים אי חליצה קנין דהיינו שבחליצה נחשב...
```

---

## Detailed Highlighted Corrections (18 Total)

### Correction #1 (Token #0)
* **Original PDF Word**: `דף`
* **Corrected Text**: `צפנת דף בי`
* **Correction Type**: `WITNESS_REPLACEMENT`
* **Confidence Score**: `0.98`
* **Paleographic Rationale**: The raster crop displays the Hebrew heading 'דף ב''. Option B provides the clean, standard Hebrew transcription of the text and context, whereas Option A contains corrupted character encoding artifacts.

---
### Correction #2 (Token #45)
* **Original PDF Word**: `פה"ב`
* **Corrected Text**: `ה וכו' לפדיו / פה"ב ב / כ"ז וסנ`
* **Correction Type**: `PALEOGRAPHIC_ACRONYM_CORRECTION`
* **Confidence Score**: `0.9`
* **Paleographic Rationale**: The visible crop contains fragments from three lines: 'ה וכו' לפדיו', 'פה"ב ב', and 'כ"ז וסנ'. Candidate Option A contains text from the larger sentence context ('פה"ב בעי שומא עיין לקמן דף ח'') which includes non-visible words and omits the clearly visible third line ('כ"ז וסנ'). Neither option provides a deterministic match for the cropped pixel array.

---
### Correction #3 (Token #72)
* **Original PDF Word**: `מקשה`
* **Corrected Text**: `מקשה רבי
בעי השוה`
* **Correction Type**: `PALEOGRAPHIC_ACRONYM_CORRECTION`
* **Confidence Score**: `0.3`
* **Paleographic Rationale**: The raster crop contains two distinct lines of text ('מקשה רבי' on line 1 and 'בעי השוה' on line 2). Option A contains text from a different part of the context and misses line 2, while Option B is empty. Thus, neither candidate accurately reflects the transcribed image text.

---
### Correction #4 (Token #90)
* **Original PDF Word**: `בעי`
* **Corrected Text**: `מקשה
בעי הש
ומנין ש`
* **Correction Type**: `PALEOGRAPHIC_ACRONYM_CORRECTION`
* **Confidence Score**: `0.95`
* **Paleographic Rationale**: The crop clearly shows three lines of text ('מקשה', 'בעי הש', and 'ומנין ש'). Neither Option A (which includes full text from the surrounding commentary not visible in the crop) nor Option B matches the actual image crop precisely.

---
### Correction #5 (Token #125)
* **Original PDF Word**: `דמשמע`
* **Corrected Text**: `ומנין שבפ
דמשמע דא
דבקידושין`
* **Correction Type**: `PALEOGRAPHIC_ACRONYM_CORRECTION`
* **Confidence Score**: `0.0`
* **Paleographic Rationale**: The raster crop contains three partial lines of Hebrew text ('ומנין שבפ', 'דמשמע דא', 'דבקידושין'). Neither Candidate A nor Candidate B accurately represents the text visible in the crop image.

---
### Correction #6 (Token #178)
* **Original PDF Word**: `זה`
* **Corrected Text**: `יוסף 3
זה לפ
לפדיון`
* **Correction Type**: `PALEOGRAPHIC_ACRONYM_CORRECTION`
* **Confidence Score**: `0.95`
* **Paleographic Rationale**: The raster crop visually contains three partial lines of Hebrew text: 'יוסף 3', 'זה לפ', and 'לפדיון'. Candidate Option A contains a much longer string ('זה לפדיון בני לא אמר כלום עגל זה בחמש סלעים') that extends far beyond the text captured in this image crop, while Option B is empty. Since neither candidate option deterministically matches the exact text visible in the crop, UNCERTAIN is selected per the system constraints.

---
### Correction #7 (Token #199)
* **Original PDF Word**: `לפדיון`
* **Corrected Text**: `זה לפדיון
לפדיון בני
האי פדיון`
* **Correction Type**: `PALEOGRAPHIC_ACRONYM_CORRECTION`
* **Confidence Score**: `0.0`
* **Paleographic Rationale**: Neither candidate option correctly transcribes the visual text in the raster crop, which clearly shows the three line fragments: 'זה לפדיון', 'לפדיון בני', and 'האי פדיון'. Option B contains an oversized block of distant text not aligned to the crop, so UNCERTAIN is returned as per instructions.

---
### Correction #8 (Token #209)
* **Original PDF Word**: `בין`
* **Corrected Text**: `שמעון
בין מג
חולצת`
* **Correction Type**: `PALEOGRAPHIC_ACRONYM_CORRECTION`
* **Confidence Score**: `0.95`
* **Paleographic Rationale**: The crop visibly contains three lines of text: 'שמעון', 'בין מג', and 'חולצת'. Option A misses the first line ('שמעון') entirely and includes text beyond the crop boundaries. Option B is empty. Thus, neither candidate deterministically represents the visible raster text, requiring UNCERTAIN.

---
### Correction #9 (Token #227)
* **Original PDF Word**: `חולצת`
* **Corrected Text**: `בין מגרש
חולצת וא
וחליצה),`
* **Correction Type**: `PALEOGRAPHIC_ACRONYM_CORRECTION`
* **Confidence Score**: `0.9`
* **Paleographic Rationale**: The raster crop contains the fragment 'בין מגרש / חולצת וא... / וחליצה),'. Neither candidate string Option A nor Option B accurately matches the visual text in the image crop, so UNCERTAIN is selected.

---
### Correction #10 (Token #317)
* **Original PDF Word**: `רבי`
* **Corrected Text**: `שם, "ר
רבי זעי
מילהו`
* **Correction Type**: `PALEOGRAPHIC_ACRONYM_CORRECTION`
* **Confidence Score**: `0.0`
* **Paleographic Rationale**: The image crop contains fragments across three vertical lines (שם, "ר / רבי זעי / מילהו). Neither Candidate A (a full line of context) nor Candidate B matches the exact visible text in the cropped image array.

---
### Correction #11 (Token #336)
* **Original PDF Word**: `מיליהון`
* **Corrected Text**: `רבי זעירא א
מיליהון ד
קומי ר' יו`
* **Correction Type**: `PALEOGRAPHIC_ACRONYM_CORRECTION`
* **Confidence Score**: `0.0`
* **Paleographic Rationale**: The raster crop contains three partial lines ('רבי זעירא א', 'מיליהון ד', 'קומי ר' יו'). Neither Option A nor Option B accurately transcribes the visible pixel text in this crop.

---
### Correction #12 (Token #354)
* **Original PDF Word**: `קומי`
* **Corrected Text**: `מיליהון
קומי ר'
סבור ח`
* **Correction Type**: `PALEOGRAPHIC_ACRONYM_CORRECTION`
* **Confidence Score**: `0.95`
* **Paleographic Rationale**: The visible text in the cropped raster image contains three lines reading 'מיליהון', 'קומי ר'', and 'סבור ח'. Neither Option A nor Option B accurately transcribes this exact visual crop (Option A includes text not present in the crop and omits lines 1 and 3, while Option B is empty).

---
### Correction #13 (Token #366)
* **Original PDF Word**: `סבור`
* **Corrected Text**: `קומי ר'
סבור ח
הוא "קו`
* **Correction Type**: `PALEOGRAPHIC_ACRONYM_CORRECTION`
* **Confidence Score**: `0.9`
* **Paleographic Rationale**: The raster crop contains three partial lines: 'קומי ר'', 'סבור ח', and 'הוא "קו'. Neither Option A (which includes full words/phrases not fully visible in the crop and omits surrounding lines) nor Option B (empty string) accurately transcribes the exact visual contents of the image.

---
### Correction #14 (Token #382)
* **Original PDF Word**: `הוא`
* **Corrected Text**: `סבור ח
הוא "ק
חליצה`
* **Correction Type**: `PALEOGRAPHIC_ACRONYM_CORRECTION`
* **Confidence Score**: `0.3`
* **Paleographic Rationale**: The raster crop contains vertical line fragments ('סבור ח', 'הוא "ק', 'חליצה') rather than the full candidate string in Option A ('הוא "קונה את עצמה" משמע דחליצה קנין, אך למ"ד'). Neither option matches the exact pixel array deterministically.

---
### Correction #15 (Token #401)
* **Original PDF Word**: `חליצה`
* **Corrected Text**: `הוא "קונ
חליצה פט
דמכל מקו`
* **Correction Type**: `PALEOGRAPHIC_ACRONYM_CORRECTION`
* **Confidence Score**: `0.9`
* **Paleographic Rationale**: The raster crop contains three lines showing line fragments: 'הוא "קונ' (from 'הוא "קונה...'), 'חליצה פט' (from 'חליצה פטור...'), and 'דמכל מקו' (from 'דמכל מקום...'). Neither Option A nor Option B correctly transcribes these visible text lines.

---
### Correction #16 (Token #436)
* **Original PDF Word**: `היתה`
* **Corrected Text**: `דמכל מ
היתה עלי
ומצד זה`
* **Correction Type**: `PALEOGRAPHIC_ACRONYM_CORRECTION`
* **Confidence Score**: `0.95`
* **Paleographic Rationale**: The raster crop contains three partial lines ('דמכל מ', 'היתה עלי', 'ומצד זה'). Candidate Option A only covers a full context sentence corresponding partially to the second line, missing lines 1 and 3 and containing text truncated in the crop. Therefore, neither option deterministically matches the exact visible raster text, requiring UNCERTAIN.

---
### Correction #17 (Token #469)
* **Original PDF Word**: `תוס'`
* **Corrected Text**: `ומצד ז
תוס' ס
דשוה כ`
* **Correction Type**: `PALEOGRAPHIC_ACRONYM_CORRECTION`
* **Confidence Score**: `0.95`
* **Paleographic Rationale**: The raster crop contains truncated vertical line fragments ('ומצד ז', 'תוס' ס', 'דשוה כ'). Neither candidate Option A nor Option B accurately transcribes or maps deterministically to the visible text fragment in the crop.

---
### Correction #18 (Token #609)
* **Original PDF Word**: `3.`
* **Corrected Text**: `3. נח`
* **Correction Type**: `PALEOGRAPHIC_ACRONYM_CORRECTION`
* **Confidence Score**: `0.0`
* **Paleographic Rationale**: The crop contains Hebrew text including '3. נח' and 'הפירושים', which does not match candidate Option A ("") or Option B ("="). Therefore, neither option is correct.

---
