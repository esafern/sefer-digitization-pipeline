import re

def clean_noise():
    with open('full_text_cleaned_goal.txt', 'r', encoding='utf-8') as f:
        text = f.read()

    lines = [l.strip() for l in text.split('\n') if l.strip()]

    cleaned_lines = []
    for l in lines:
        words = l.split()
        clean_words = []
        for w in words:
            # Strip garbled OCR strings (length > 10 without spaces or invalid sofit placement)
            clean_w = re.sub(r'[^א-ת]', '', w)
            if len(clean_w) > 12 and not any(mark in w for mark in ['"', "'", '״', '׳']):
                print(f"Removing garbled OCR token: {w}")
                continue
            if any(c in 'ךםןףץ' for c in clean_w[:-1]):
                # Check if it's a known garbled OCR token
                if len(clean_w) > 6 or re.search(r'[ךםןףץ][א-ת]', w):
                    print(f"Removing middle-sofit garbled token: {w}")
                    continue
            clean_words.append(w)
        cleaned_lines.append(' '.join(clean_words))

    with open('full_text_cleaned_goal.txt', 'w', encoding='utf-8') as f:
        for cl in cleaned_lines:
            f.write(cl + '\n\n')

    print("Cleaned OCR noise strings from full_text_cleaned_goal.txt!")

if __name__ == '__main__':
    clean_noise()
