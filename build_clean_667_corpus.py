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

sections = [
    ("כללי האלף", 1, 80),
    ("כללי הבית", 81, 122),
    ("כללי הגימל", 123, 128),
    ("כללי הדלת", 129, 147),
    ("כללי ההא", 148, 241),
    ("כללי הויו", 242, 263),
    ("כללי הזין", 264, 274),
    ("כללי החית", 275, 290),
    ("כללי הטית", 291, 294),
    ("כללי היוד", 295, 300),
    ("כללי הכף", 301, 345),
    ("כללי הלמד", 346, 405),
    ("כללי המם", 406, 487),
    ("כללי הנון", 488, 494),
    ("כללי הסמך", 495, 513),
    ("כללי העין", 514, 519),
    ("כללי הפא", 520, 528),
    ("כללי הצדי", 529, 530),
    ("כללי הקוף", 531, 553),
    ("כללי הריש", 554, 615),
    ("כללי השין", 616, 628),
    ("כללי התיו", 629, 667)
]

def assemble_all_667_perfect():
    with open('pdf_extracted_text.txt', 'r', encoding='utf-8') as f:
        text = f.read()

    clean_text = re.sub(r'[\u200e\u200f\u202a-\u202e]', '', text)

    p1_start = clean_text.find('כללי האלף')
    p2_start = clean_text.find('סליקו כללי הגמרא')
    if p2_start == -1:
        p2_start = clean_text.find('בס"ד כללי שני')

    part1_raw = clean_text[p1_start:p2_start + len('סליקו כללי הגמרא')]

    all_klalim = []

    for i in range(len(sections)):
        sec_name, start_id, end_id = sections[i]
        expected_count = end_id - start_id + 1

        if i == 0:
            sec_start_pos = 0
        else:
            sec_start_pos = part1_raw.find(f'בס"ד {sec_name}')
            if sec_start_pos == -1:
                sec_start_pos = part1_raw.find(sec_name)

        if i < len(sections) - 1:
            next_sec_name = sections[i+1][0]
            sec_end_pos = part1_raw.find(f'בס"ד {next_sec_name}', sec_start_pos)
            if sec_end_pos == -1:
                sec_end_pos = part1_raw.find(next_sec_name, sec_start_pos)
        else:
            sec_end_pos = len(part1_raw)

        sec_chunk = part1_raw[sec_start_pos:sec_end_pos]
        lines = [l.strip() for l in sec_chunk.split('\n') if l.strip()]

        filtered_lines = []
        for l in lines:
            if l.startswith('יד מלאכי') or l.startswith('בס"ד כללי') or l.startswith('סליקו כללי') or l.isdigit():
                continue
            filtered_lines.append(l)

        # Build blocks inside section
        sec_blocks = []
        curr = []
        for l in filtered_lines:
            words = l.split()
            if not words:
                continue
            first_clean = re.sub(r'[^א-ת]', '', words[0])

            # A new Klal block starts if first word is Gematria numeral header or bold heading
            if len(words) >= 2 and len(first_clean) <= 5 and re.match(r'^[א-ת]{1,4}$', first_clean) and first_clean not in ['דהא', 'ואם', 'עכ', 'עש', 'בשם', 'אלא', 'ומזה', 'ודוק', 'וככ', 'ועיין']:
                # Check if it looks like a new entry header
                if curr:
                    sec_blocks.append(' '.join(curr))
                    curr = []
                curr.append(l)
            else:
                if curr:
                    curr.append(l)
                else:
                    curr.append(l)
        if curr:
            sec_blocks.append(' '.join(curr))

        print(f"Section {sec_name:<15}: target range {start_id}..{end_id} ({expected_count} expected), parsed {len(sec_blocks)} blocks")

        for idx_b, b in enumerate(sec_blocks):
            klal_num = start_id + idx_b
            if klal_num <= end_id:
                words = b.split()
                g_hdr = to_gematria(klal_num)
                rest = ' '.join(words[1:]) if len(words) > 1 else words[0]
                # Standardize line format to: <Gematria_ID> <Text>
                all_klalim.append({'id': klal_num, 'gematria': g_hdr, 'text': f"{g_hdr} {rest}"})

    print(f"\nTotal assembled Klalim: {len(all_klalim)} / 667")

    with open('full_text_cleaned_goal.txt', 'w', encoding='utf-8') as f:
        for item in all_klalim:
            f.write(item['text'] + '\n\n')

    print("Saved all Klalim cleanly to full_text_cleaned_goal.txt!")

if __name__ == '__main__':
    assemble_all_667_perfect()
