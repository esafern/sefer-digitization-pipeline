import re

def to_gematria(n):
    units = ["", "א", "ב", "ג", "ד", "ה", "ו", "ז", "ח", "ט"]
    tens = ["", "י", "כ", "ל", "מ", "נ", "ס", "ע", "פ", "צ"]
    hundreds = ["", "ק", "ר", "ש", "ת", "תק", "תר"]
    
    if n == 15:
        return "טו"
    if n == 16:
        return "טז"
        
    res = ""
    if n >= 600:
        res += "תר"
        n -= 600
    elif n >= 500:
        res += "תק"
        n -= 500
    elif n >= 400:
        res += "ת"
        n -= 400
    elif n >= 300:
        res += "ש"
        n -= 300
    elif n >= 200:
        res += "ר"
        n -= 200
    elif n >= 100:
        res += "ק"
        n -= 100
        
    if n >= 10:
        if n == 15:
            return res + "טו"
        if n == 16:
            return res + "טז"
        t = n // 10
        res += tens[t]
        n %= 10
    if n > 0:
        res += units[n]
    return res

def parse_full_corpus():
    with open('pdf_extracted_text.txt', 'r', encoding='utf-8') as f:
        text = f.read()

    clean_text = re.sub(r'[\u200e\u200f\u202a-\u202e]', '', text)

    p1_start = clean_text.find('כללי האלף')
    p2_start = clean_text.find('סליקו כללי הגמרא')
    if p2_start == -1:
        p2_start = clean_text.find('בס"ד כללי שני')

    part1_raw = clean_text[p1_start:p2_start + len('סליקו כללי הגמרא')]
    lines = [l.strip() for l in part1_raw.split('\n') if l.strip()]

    # Filter out page headers, section dividers, etc.
    content_lines = []
    for l in lines:
        if l.startswith('יד מלאכי') or l.startswith('בס"ד כללי') or l.startswith('סליקו כללי') or l.isdigit():
            continue
        content_lines.append(l)

    # Now parse by matching sequential Gematria headers 1..667
    klalim = []
    target_id = 1
    curr_text = []

    for l in content_lines:
        words = l.split()
        if not words:
            continue
        first_clean = words[0].replace('"', '').replace("'", '').replace('.', '')

        expected_str = to_gematria(target_id)
        next_expected_str = to_gematria(target_id + 1)

        if first_clean == expected_str or first_clean == next_expected_str:
            if curr_text:
                klalim.append({'id': target_id - 1, 'text': ' '.join(curr_text)})
                curr_text = []
            if first_clean == next_expected_str:
                target_id += 1
            target_id += 1
            curr_text.append(l)
        else:
            if curr_text:
                curr_text.append(l)

    if curr_text:
        klalim.append({'id': target_id - 1, 'text': ' '.join(curr_text)})

    print(f"Total Klalim extracted using sequential Gematria matching 1..667: {len(klalim)}")
    for k in klalim[:10]:
        print(f"Klal {k['id']:03d}: {k['text'][:60]}")
    print("...")
    for k in klalim[-10:]:
        print(f"Klal {k['id']:03d}: {k['text'][:60]}")

if __name__ == '__main__':
    parse_full_corpus()
