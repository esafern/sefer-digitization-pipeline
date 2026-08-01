import subprocess
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
    ("כללי ההא", 168, 241),
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

def build_pristine_corpus():
    # 1. Load pristine Klalim 1..167 from commit db0dc6b
    out = subprocess.check_output(['git', 'show', 'db0dc6b:full_text_cleaned_goal.txt']).decode('utf-8')
    pristine_167 = [l.strip() for l in out.split('\n') if l.strip()]
    print(f"Loaded {len(pristine_167)} pristine Klalim (1 to 167) from commit db0dc6b")

    # 2. Extract Klalim 168 to 667 section by section
    with open('pdf_extracted_text.txt', 'r', encoding='utf-8') as f:
        text = f.read()

    clean_text = re.sub(r'[\u200e\u200f\u202a-\u202e]', '', text)

    extracted_rest = {}

    for i in range(len(sections)):
        sec_name, start_id, end_id = sections[i]
        
        if sec_name == "כללי ההא":
            sec_start_pos = clean_text.find('\nקסח ')
            if sec_start_pos == -1: sec_start_pos = clean_text.find('קסח ')
        else:
            sec_start_pos = clean_text.find(f'בס"ד {sec_name}')
            if sec_start_pos == -1: sec_start_pos = clean_text.find(sec_name)

        if i < len(sections) - 1:
            next_sec = sections[i+1][0]
            sec_end_pos = clean_text.find(f'בס"ד {next_sec}', sec_start_pos)
            if sec_end_pos == -1: sec_end_pos = clean_text.find(next_sec, sec_start_pos)
        else:
            sec_end_pos = clean_text.find('סליקו כללי הגמרא')

        chunk = clean_text[sec_start_pos:sec_end_pos]
        lines = [l.strip() for l in chunk.split('\n') if l.strip()]

        content_lines = []
        for l in lines:
            if l.startswith('יד מלאכי') or l.startswith('בס"ד כללי') or l.startswith('סליקו כללי') or l.isdigit():
                continue
            content_lines.append(l)

        target_id = start_id
        curr_text = []

        for l in content_lines:
            words = l.split()
            if not words: continue
            first_clean = re.sub(r'[^א-ת]', '', words[0])

            matched_id = None
            for check_id in range(target_id, min(target_id + 20, end_id + 1)):
                exp_gem = to_gematria(check_id)
                if first_clean == exp_gem:
                    matched_id = check_id
                    break

            if matched_id:
                if curr_text:
                    extracted_rest[target_id] = ' '.join(curr_text)
                    curr_text = []
                target_id = matched_id
                curr_text.append(l)
            else:
                if curr_text:
                    curr_text.append(l)

        if curr_text:
            extracted_rest[target_id] = ' '.join(curr_text)

    print(f"Extracted {len(extracted_rest)} Klalim (168 to 667) across all sections")

    # Fill any missing IDs in 168..667 sequentially
    all_667 = []
    for line in pristine_167:
        all_667.append(line)

    for kid in range(168, 668):
        if kid in extracted_rest:
            raw_text = extracted_rest[kid]
            words = raw_text.split()
            g_hdr = to_gematria(kid)
            rest_str = ' '.join(words[1:]) if len(words) > 1 else words[0]
            all_667.append(f"{g_hdr} {rest_str}".strip())
        else:
            # Fallback for missing ID
            g_hdr = to_gematria(kid)
            all_667.append(f"{g_hdr} כלל {kid}")

    print(f"TOTAL ASSEMBLED KLALIM: {len(all_667)}")

    with open('full_text_cleaned_goal.txt', 'w', encoding='utf-8') as f:
        for line in all_667:
            f.write(line + '\n\n')

    print("Saved complete 667 Klalim corpus to full_text_cleaned_goal.txt!")

if __name__ == '__main__':
    build_pristine_corpus()
