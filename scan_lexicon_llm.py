import re

def is_valid_rabbinic_word(word):
    # Strip quotes/apostrophes for clean morphological check
    clean = re.sub(r'[^א-ת]', '', word)
    if not clean:
        return True, "punctuation_only"

    # Single letter or Gematria header
    if len(clean) == 1:
        return True, "single_letter"

    # Known valid sofit rules:
    sofit = set('ךםןףץ')
    non_sofit = set('כמנפצ')

    # Middle sofit check
    if any(c in sofit for c in clean[:-1]):
        return False, "middle_sofit_letter"

    # End non-sofit check without quotes/acronyms
    if len(clean) > 1 and clean[-1] in non_sofit and not any(q in word for q in ['"', "'", '״', '׳']):
        # Allow valid gematria numerals and known abbreviations
        gematria_numerals = {
            'כ', 'מ', 'נ', 'פ', 'צ', 'קכ', 'קמ', 'קנ', 'קפ', 'קצ',
            'רכ', 'רמ', 'רנ', 'רפ', 'רצ', 'שכ', 'שמ', 'שנ', 'שפ', 'שצ',
            'תכ', 'תמ', 'תנ', 'תפ', 'תצ', 'תקכ', 'תקמ', 'תקנ', 'תקפ', 'תקצ',
            'תרכ', 'תרמ', 'תרנ', 'בפ', 'דפ', 'רפ', 'בבבל', 'מממון', 'מממונא'
        }
        if clean not in gematria_numerals:
            return False, "non_sofit_at_end"

    # Unnaturally long words (more than 10 letters without quotes)
    if len(clean) > 11 and not any(q in word for q in ['"', "'", '״', '׳']):
        # Check if it has multiple concatenated Rabbinic words
        return False, "unnatural_length_concatenation"

    # Check for impossible letter clusters in Hebrew/Aramaic
    # e.g., 4 identical letters, or strange character noise
    if re.search(r'(.)\1\1', clean):
        if clean not in ['מממון', 'מממונא', 'בבבל']:
            if not any(q in word for q in ['"', "'", '״', '׳']):
                return False, "triple_consecutive_letters"

    return True, "valid"

def scan_lexicon():
    with open('lexicon.txt', 'r', encoding='utf-8') as f:
        words = [line.strip() for line in f if line.strip()]

    print(f"Total lexicon words to scan: {len(words)}")

    suspicious = []
    for w in words:
        valid, reason = is_valid_rabbinic_word(w)
        if not valid:
            suspicious.append((w, reason))

    print(f"\nTotal suspicious words identified: {len(suspicious)}")

    # Group by reason
    by_reason = {}
    for w, r in suspicious:
        by_reason.setdefault(r, []).append(w)

    for r, w_list in by_reason.items():
        print(f"\n--- Reason: {r} ({len(w_list)} words) ---")
        for w in w_list[:20]:
            print(f"  - {w}")
        if len(w_list) > 20:
            print(f"  ... and {len(w_list) - 20} more")

    # Write report to suspicious_lexicon_report.md
    with open('suspicious_lexicon_report.md', 'w', encoding='utf-8') as f:
        f.write("# Suspicious Lexicon Words Review\n\n")
        f.write(f"Total words scanned: {len(words)}\n")
        f.write(f"Total suspicious words flagged: {len(suspicious)}\n\n")
        for r, w_list in by_reason.items():
            f.write(f"## Category: {r} ({len(w_list)} words)\n\n")
            for w in w_list:
                f.write(f"- `{w}`\n")
            f.write("\n")

    print("\nSaved report to suspicious_lexicon_report.md!")

if __name__ == '__main__':
    scan_lexicon()
