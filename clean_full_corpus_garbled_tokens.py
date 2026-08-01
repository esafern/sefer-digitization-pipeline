import re

def clean_corpus():
    with open('full_text_cleaned_goal.txt', 'r', encoding='utf-8') as f:
        text = f.read()

    lines = [l.strip() for l in text.split('\n') if l.strip()]

    sofit = set('ךםןףץ')
    cleaned_lines = []

    for l in lines:
        words = l.split()
        if not words: continue

        clean_words = []
        for idx_w, w in enumerate(words):
            # 1. Remove English characters
            w_clean_ascii = re.sub(r'[a-zA-Z]', '', w)
            if not w_clean_ascii: continue

            # 2. Check for garbled middle-sofit or character salad tokens
            clean_w = re.sub(r'[^א-ת]', '', w_clean_ascii)
            
            # If word contains middle sofit letter (except valid prefixed words)
            has_middle_sofit = any(c in sofit for c in clean_w[:-1])
            
            # If word is an unnaturally long character salad (> 12 letters without quotes)
            is_char_salad = len(clean_w) > 12 and not any(q in w for q in ['"', "'", '״', '׳'])

            if has_middle_sofit or is_char_salad:
                # Do not include garbled OCR margin token
                print(f"Stripped OCR noise token: '{w}' in line start: '{words[0]}'")
                continue

            clean_words.append(w_clean_ascii)

        cleaned_lines.append(' '.join(clean_words))

    with open('full_text_cleaned_goal.txt', 'w', encoding='utf-8') as f:
        for cl in cleaned_lines:
            f.write(cl + '\n\n')

    print(f"Cleaned {len(cleaned_lines)} Klalim in full_text_cleaned_goal.txt!")

if __name__ == '__main__':
    clean_corpus()
