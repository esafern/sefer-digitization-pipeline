# Klal 1 Visual Inspection & Alignment Guide

## Section Information
* **Work**: Sefer Yad Malachi (Livorno 1766 / Berlin 1857 Square Edition)
* **Section**: Klalei HaGemara — Klal 1 (כלל א)
* **Start Page**: Page 14 (`berlin_square.pdf`, 0-indexed Page 13)
* **Word Count**: 692 Base Words | 686 Witness OCR Words

---

## Level 1: Full Original Page Scan (Page 14)

Below is the full original scan of Page 14 containing the opening of **Klal 1**:

<img src="file:///Users/ericsafern/work/yad-malachi/yad-malachi-pipeline/images/klal_001_page_14.png" alt="Full Page 14 Scan" width="100%" />

---

## Level 2: Candidate Text Stream Comparison

### Candidate Stream 1: PDF Embedded Vector Text Layer (Un-reversed R-to-L)
```text
א יד מלאכי כללי האלף אי תניא תניא • מדברי רש"י ז"ל בפ"ב דנדרים י"ט ב' משמע דלאו לדחויי ליה קא מכוין אלא כלומר אי משכחת ברייתא דקאמרא הכי תניא ומיתרצא מילתא בהכי . וכן כתב עוד פ ' אין דורשין י"ט ב' אי תניא בהדי ' דחולקין תני' ונלך אחרי' וחוזר אני בי . וכן נרא' תו מדבריו בפ"ג דיומא ל"א ב' ע"ש ובשלהי פ"ק דזבחים ט"ו ב' יע"ש . אך בפרק המפלת כ"ג ב' פירש אי תניא תניא שמעתי אני מרב מה שאמרתי אבל אתם הואיל ויש משנה בידכם לכן אחריה דנראה דשינה את טעמו ממה שפירש בכל אינך דוכתי שהבאתי • ויש ליישב דדוקא בההיא דנדה פרש"י כן משום דמימרת רב ירמיה בר אבא דעליה אקשינן מהברייתא...
```

### Candidate Stream 2: Tesseract Witness OCR Stream
```text
ייר מלאכי כללי האלף א | אי תמא תניא + מדברי רש"י ז'ל בפ"ב דנדרים ייט ב' משמע רלאו לדחויי ליח קא מכוין אלא כלומר אי משכחת ברייתא דקאמרא הכי תניא ומיתרצא מילתא בהכיי* וכן כרזב עור פ' אין רורשין י"ט ב' אי תניא בהדיי דחולקין תני' ונלך אחריי וחוזר אני בי- וכן נרא' תו מרבריו בפ"ג דיומא ליא ב' עיש וכשלהי פ'ק דזבחים ט"ו ב' יע"ש + אך בפרק המפלת כ"ג ב' פירש אי תניא תניא שמעתי אני מרב מה שאמרתי אבל אתם הואיל ויש משנה בירכם לכו אחריה דנראה דשינה את טעמו ממה שפירש בכל אינך דוכתי שהכאתי - ויש ליישב דרוקא בההיא דנדה פרש'"י כן משום דמימרת רב ירמיה בר אבא דעליה אקשינן מהברייתא משמיה דרב קאמר...
```

---

## Level 3: Targeted Conflict Crop Inspection (6 Key Conflicts)

### Conflict #1

📸 **Cropped Manuscript Image**:
<img src="file:///Users/ericsafern/work/yad-malachi/yad-malachi-pipeline/images/klal_001_crop_01.png" alt="Conflict #1 Crop" width="100%" />

* 🅰️ **Candidate Stream 1 (PDF Layer)**: `א יד`
* 🅱️ **Candidate Stream 2 (Witness OCR)**: `ייר`
* 🤖 **AI Vision Verdict**: **Option UNCERTAIN** (Confidence: 0.0)
* 🔍 **Paleographic Rationale**: The provided image crop consists almost entirely of whitespace with isolated pixel artifacts/noise on the margins, containing no decipherable character strokes. Consequently, it is impossible to deterministically verify either candidate ('א יד' or 'ייר') from the pixel array.
* 📝 **Transcription Found**: ``

---

### Conflict #2

📸 **Cropped Manuscript Image**:
<img src="file:///Users/ericsafern/work/yad-malachi/yad-malachi-pipeline/images/klal_001_crop_02.png" alt="Conflict #2 Crop" width="100%" />

* 🅰️ **Candidate Stream 1 (PDF Layer)**: `אי תניא תניא •`
* 🅱️ **Candidate Stream 2 (Witness OCR)**: `א | אי תמא תניא +`
* 🤖 **AI Vision Verdict**: **Option UNCERTAIN** (Confidence: 0.0)
* 🔍 **Paleographic Rationale**: The provided image crop is almost entirely blank, containing only faint stray specks on the far right edge without recognizable Hebrew characters. It is impossible to deterministically map either candidate string to the pixel array.
* 📝 **Transcription Found**: ``

---

### Conflict #3

📸 **Cropped Manuscript Image**:
<img src="file:///Users/ericsafern/work/yad-malachi/yad-malachi-pipeline/images/klal_001_crop_03.png" alt="Conflict #3 Crop" width="100%" />

* 🅰️ **Candidate Stream 1 (PDF Layer)**: `ז"ל`
* 🅱️ **Candidate Stream 2 (Witness OCR)**: `ז'ל`
* 🤖 **AI Vision Verdict**: **Option UNCERTAIN** (Confidence: 0.0)
* 🔍 **Paleographic Rationale**: The provided image crop is almost entirely blank and contains only isolated specks/artifacts without legible text corresponding to either candidate 'ז"ל' or 'ז'ל'.
* 📝 **Transcription Found**: ``

---

### Conflict #4

📸 **Cropped Manuscript Image**:
<img src="file:///Users/ericsafern/work/yad-malachi/yad-malachi-pipeline/images/klal_001_crop_04.png" alt="Conflict #4 Crop" width="100%" />

* 🅰️ **Candidate Stream 1 (PDF Layer)**: `י"ט`
* 🅱️ **Candidate Stream 2 (Witness OCR)**: `ייט`
* 🤖 **AI Vision Verdict**: **Option UNCERTAIN** (Confidence: 0.0)
* 🔍 **Paleographic Rationale**: The provided raster crop is essentially blank, containing only minor background noise/specks and no legible Hebrew letters or gershayim. Consequently, neither candidate string ('י"ט' or 'ייט') can be visually verified in the image.
* 📝 **Transcription Found**: ``

---

### Conflict #5

📸 **Cropped Manuscript Image**:
<img src="file:///Users/ericsafern/work/yad-malachi/yad-malachi-pipeline/images/klal_001_crop_05.png" alt="Conflict #5 Crop" width="100%" />

* 🅰️ **Candidate Stream 1 (PDF Layer)**: `דלאו`
* 🅱️ **Candidate Stream 2 (Witness OCR)**: `רלאו`
* 🤖 **AI Vision Verdict**: **Option UNCERTAIN** (Confidence: 0.0)
* 🔍 **Paleographic Rationale**: The provided image crop contains only blank white space with a few tiny background noise specks; there are no legible Hebrew letters or characters visible to map to either candidate option.
* 📝 **Transcription Found**: `none`

---

### Conflict #6

📸 **Cropped Manuscript Image**:
<img src="file:///Users/ericsafern/work/yad-malachi/yad-malachi-pipeline/images/klal_001_crop_06.png" alt="Conflict #6 Crop" width="100%" />

* 🅰️ **Candidate Stream 1 (PDF Layer)**: `ליה`
* 🅱️ **Candidate Stream 2 (Witness OCR)**: `ליח`
* 🤖 **AI Vision Verdict**: **Option UNCERTAIN** (Confidence: 0.0)
* 🔍 **Paleographic Rationale**: The provided image crop contains only isolated noise specks and lacks legible Hebrew characters. Even though 'ליה' is the semantically correct word in the context ('לדחויי ליה קא מכוין'), the visual data is insufficient to deterministically verify either candidate.
* 📝 **Transcription Found**: ``

---

