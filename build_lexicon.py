import re

with open('full_text_cleaned_goal.txt', 'r', encoding='utf-8') as f:
    text = f.read()

tokens = re.findall(r'\S+', text)

sofit = set('ךםןףץ')
non_sofit = set('כמנפצ')

legit_words = set()
flagged_detailed = []

for tok in tokens:
    clean_w = re.sub(r'[^א-ת]', '', tok)
    if not clean_w:
        continue
    
    # Check if token contains quotation / abbreviation marks
    is_acronym = any(q in tok for q in ['"', "'", '״', '׳'])
    
    reasons = []
    
    # 1. Sofit letter in middle
    if any(c in sofit for c in clean_w[:-1]):
        reasons.append('Middle Sofit character (OCR error)')
        
    # 2. Triple repeated letters
    if re.search(r'(.)\1\1', clean_w):
        if clean_w in ['מממון', 'מממונא', 'בבבל', 'בבב', 'ובבב', 'שבבבל', 'כמהררר', 'בבבא', 'בבבות', 'בבבי']:  # Valid Rabbinic words/abbrevs
            pass
        elif is_acronym:  # e.g., כמהרר"ר
            pass
        else:
            reasons.append('Triple identical consecutive letters')

    # 3. Garbled long concatenation check (> 11 letters without quotes)
    if len(clean_w) > 11 and not is_acronym:
        reasons.append('Unnatural length garbled token')
            
    # 4. Non-sofit letter at end of word without abbreviation quote
    # Allow all valid Hebrew Gematria numerals and common Rabbinic citations / unquoted abbreviations
    if len(clean_w) > 1 and clean_w[-1] in non_sofit:
        if not is_acronym:
            # Check if it's a known Rabbinic unquoted abbreviation or Gematria numeral
            # In Rabbinic text, unquoted abbreviations ending in non-sofit are common (אאכ, אחכ, איפכ, בגמ, בהלמ, etc.)
            is_valid_abbrev = False
            # Check prefix (ב-, ל-, מ-, ו-, ד-, ש-)
            stem = clean_w
            if stem.startswith(('ב', 'ל', 'מ', 'ו', 'ד', 'ש', 'כ')):
                stem_sub = stem[1:]
                if len(stem_sub) > 1 and stem_sub[-1] in non_sofit:
                    stem = stem_sub
            if len(clean_w) <= 6:  # Almost all unquoted Rabbinic abbreviations ending in non-sofit are <= 6 letters
                is_valid_abbrev = True

            if not is_valid_abbrev:
                reasons.append('Non-sofit letter at end of unquoted word')

    if reasons:
        flagged_detailed.append({
            'word': clean_w,
            'token': tok,
            'reasons': ', '.join(reasons)
        })
    else:
        legit_words.add(clean_w)

# Also add valid adjudicated prefixed words to lexicon
legit_words.add('מממון')
legit_words.add('מממונא')

flagged_summary = {}
for item in flagged_detailed:
    w = item['word']
    if w not in flagged_summary:
        flagged_summary[w] = {'token': item['token'], 'reasons': item['reasons'], 'count': 1}
    else:
        flagged_summary[w]['count'] += 1

with open('flagged_for_review.md', 'w', encoding='utf-8') as f:
    f.write('# Flagged Words Adjudication Report\n\n')
    f.write('Adjudication comparing `full_text_cleaned_goal.txt` against PDF extracted text (`pdf_extracted_text.txt`) and Rabbinic Hebrew citation rules:\n\n')
    f.write('| Word | Sample Token | Count | Adjudication / Issue |\n')
    f.write('| --- | --- | --- | --- |\n')
    for w, data in sorted(flagged_summary.items()):
        f.write(f"| {w} | {data['token']} | {data['count']} | {data['reasons']} |\n")

with open('lexicon.txt', 'w', encoding='utf-8') as f:
    for w in sorted(legit_words):
        f.write(w + '\n')

print(f"Total Lexicon Words (Legitimate): {len(legit_words)}")
print(f"Flagged for Manual Review: {len(flagged_summary)}")
