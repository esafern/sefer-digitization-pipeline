import json
import os
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

def get_section_for_id(kid):
    for sec_name, s, e in sections:
        if s <= kid <= e:
            return sec_name
    return "כללי הגמרא"

def rebuild():
    with open('full_text_cleaned_goal.txt', 'r', encoding='utf-8') as f:
        klal_texts = [line.strip() for line in f if line.strip()]

    print(f"Loaded {len(klal_texts)} Klalim from full_text_cleaned_goal.txt")

    all_klalim_data = []
    for idx, text in enumerate(klal_texts, 1):
        words = text.split()
        first_word = words[0] if words else to_gematria(idx)
        title = ' '.join(words[1:6]) if len(words) > 1 else text
        sec = get_section_for_id(idx)
        item = {
            'klal_id': idx,
            'gematria': to_gematria(idx),
            'section': sec,
            'title': title,
            'clean_text': text,
            'page': (idx // 15) + 13
        }
        all_klalim_data.append(item)

    # Split into 3 parts (approx 222 klalim each)
    p1 = all_klalim_data[:222]
    p2 = all_klalim_data[222:444]
    p3 = all_klalim_data[444:]

    with open('part1.json', 'w', encoding='utf-8') as f:
        json.dump(p1, f, ensure_ascii=False, indent=2)
    print(f"Saved part1.json ({len(p1)} Klalim)")

    with open('part2.json', 'w', encoding='utf-8') as f:
        json.dump(p2, f, ensure_ascii=False, indent=2)
    print(f"Saved part2.json ({len(p2)} Klalim)")

    with open('part3.json', 'w', encoding='utf-8') as f:
        json.dump(p3, f, ensure_ascii=False, indent=2)
    print(f"Saved part3.json ({len(p3)} Klalim)")

    with open('klalim_demo_dataset.json', 'w', encoding='utf-8') as f:
        json.dump(all_klalim_data, f, ensure_ascii=False, indent=2)
    print(f"Saved klalim_demo_dataset.json ({len(all_klalim_data)} Klalim)")

    # Re-split klalim_batches
    import math
    batch_size = 10
    num_batches = math.ceil(len(all_klalim_data) / batch_size)
    os.makedirs('klalim_batches', exist_ok=True)
    for i in range(num_batches):
        batch = all_klalim_data[i * batch_size : (i + 1) * batch_size]
        filename = f'klalim_batches/batch_{i+1}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(batch, f, ensure_ascii=False, indent=2)
    print(f"Created {num_batches} batch files in klalim_batches/")

    # Update individual klalim/ and processed_klalim/
    for kdir in ['klalim', 'processed_klalim']:
        os.makedirs(kdir, exist_ok=True)
        for item in all_klalim_data:
            kid = item['klal_id']
            file_path = f"{kdir}/klal_{kid:03d}.json"
            kdata = {
                'klal_id': kid,
                'gematria': item['gematria'],
                'section': item['section'],
                'clean_text': item['clean_text'],
                'full_text': item['clean_text']
            }
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(kdata, f, ensure_ascii=False, indent=2)
        print(f"Saved 667 individual files in {kdir}/")

if __name__ == '__main__':
    rebuild()
