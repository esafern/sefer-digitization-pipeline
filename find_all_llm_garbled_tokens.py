import re

def scan_llm_linguistic():
    with open('lexicon.txt', 'r', encoding='utf-8') as f:
        words = [l.strip() for l in f if l.strip()]

    print(f"Loaded {len(words)} lexicon words")

    sofit = set('ךםןףץ')
    non_sofit = set('כמנפצ')

    garbled = []
    typos = []

    # Known valid Rabbinic words / unquoted abbreviations
    valid_unquoted_abbrevs = {
        'אאכ', 'אהנ', 'אומ', 'אחכ', 'איכ', 'איפכ', 'אכ', 'אמינ', 'אנ', 'אעפ', 'אעפכ', 'אפ',
        'באעפ', 'בבהמ', 'בבמ', 'בגמ', 'בהלמ', 'בהמ', 'בפ', 'דפ', 'רפ', 'שכ', 'שמ', 'שנ', 'שפ', 'שצ',
        'תכ', 'תמ', 'תנ', 'תפ', 'תצ', 'תקכ', 'תקמ', 'תקנ', 'תקפ', 'תקצ', 'תרכ', 'תרמ', 'תרנ',
        'כ', 'מ', 'נ', 'פ', 'צ', 'קכ', 'קמ', 'קנ', 'קפ', 'קצ', 'רכ', 'רמ', 'רנ', 'רפ', 'רצ'
    }

    for w in words:
        clean = re.sub(r'[^א-ת]', '', w)
        if not clean: continue

        # Check 1: Long character concatenations (> 11 letters without quotes)
        if len(clean) > 11 and not any(q in w for q in ['"', "'", '״', '׳']):
            garbled.append((w, "concatenation_salad"))
            continue

        # Check 2: Middle sofit letters
        if any(c in sofit for c in clean[:-1]):
            garbled.append((w, "middle_sofit"))
            continue

        # Check 3: Non-sofit at end without quotes if not a recognized abbreviation
        if len(clean) > 1 and clean[-1] in non_sofit and not any(q in w for q in ['"', "'", '״', '׳']):
            # Allow common Rabbinic prefixes + abbrevs (e.g. דאחכ, ולאעפ, כבגמ, etc.)
            stem = clean
            if stem.startswith(('ב', 'ל', 'מ', 'ו', 'ד', 'ש', 'כ')):
                if stem[1:] in valid_unquoted_abbrevs:
                    continue
                if len(stem[1:]) <= 4:  # Short Rabbinic unquoted abbreviation
                    continue
            if clean in valid_unquoted_abbrevs:
                continue

            typos.append((w, "truncated_non_sofit"))

    print(f"\nTotal Garbled OCR Concatenations / Salads found: {len(garbled)}")
    for g, r in garbled:
        print(f"  [GARBLED]: '{g}' ({r})")

    print(f"\nTotal Truncated / Typos found: {len(typos)}")
    for t, r in typos[:30]:
        print(f"  [TYPO]: '{t}' ({r})")
    if len(typos) > 30:
        print(f"  ... and {len(typos) - 30} more")

if __name__ == '__main__':
    scan_llm_linguistic()
