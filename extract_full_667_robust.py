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

def parse_all():
    with open('pdf_extracted_text.txt', 'r', encoding='utf-8') as f:
        text = f.read()

    clean_text = re.sub(r'[\u200e\u200f\u202a-\u202e]', '', text)

    p1_start = clean_text.find('כללי האלף')
    p2_start = clean_text.find('סליקו כללי הגמרא')
    if p2_start == -1:
        p2_start = clean_text.find('בס"ד כללי שני')

    part1_raw = clean_text[p1_start:p2_start + len('סליקו כללי הגמרא')]
    lines = [l.strip() for l in part1_raw.split('\n') if l.strip()]

    content_lines = []
    for l in lines:
        if l.startswith('יד מלאכי') or l.startswith('בס"ד כללי') or l.startswith('סליקו כללי') or l.isdigit():
            continue
        content_lines.append(l)

    klalim = []
    target_id = 1
    curr_text = []

    for idx, l in enumerate(content_lines):
        words = l.split()
        if not words:
            continue
        first_clean = re.sub(r'[^א-ת]', '', words[0])

        matched_id = None
        for check_id in range(target_id, min(target_id + 15, 668)):
            exp_gem = to_gematria(check_id)
            if first_clean == exp_gem:
                matched_id = check_id
                break

        if matched_id:
            if curr_text:
                klalim.append({'id': target_id, 'gematria': to_gematria(target_id), 'text': ' '.join(curr_text)})
                curr_text = []
            if matched_id > target_id + 1:
                print(f"Skipped from {target_id} ({to_gematria(target_id)}) to {matched_id} ({to_gematria(matched_id)}) at line: '{l[:40]}'")
            target_id = matched_id
            curr_text.append(l)
        else:
            if curr_text:
                curr_text.append(l)

    if curr_text:
        klalim.append({'id': target_id, 'gematria': to_gematria(target_id), 'text': ' '.join(curr_text)})

    print(f"Total Klalim extracted: {len(klalim)}")
    print(f"Final Klal ID extracted: {klalim[-1]['id']} ({klalim[-1]['gematria']})")
    print(f"Final Klal snippet: {klalim[-1]['text'][:80]}")

if __name__ == '__main__':
    parse_all()
