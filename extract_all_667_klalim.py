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

sections_order = [
    ("כללי האלף", "א"),
    ("כללי הבית", "ב"),
    ("כללי הגימל", "ג"),
    ("כללי הדלת", "ד"),
    ("כללי ההא", "ה"),
    ("כללי הויו", "ו"),
    ("כללי הזין", "ז"),
    ("כללי החית", "ח"),
    ("כללי הטית", "ט"),
    ("כללי היוד", "י"),
    ("כללי הכף", "כ"),
    ("כללי הלמד", "ל"),
    ("כללי המם", "מ"),
    ("כללי הנון", "נ"),
    ("כללי הסמך", "ס"),
    ("כללי העין", "ע"),
    ("כללי הפא", "פ"),
    ("כללי הצדי", "צ"),
    ("כללי הקוף", "ק"),
    ("כללי הריש", "ר"),
    ("כללי השין", "ש"),
    ("כללי התיו", "ת"),
]

def parse_all_sections():
    with open('pdf_extracted_text.txt', 'r', encoding='utf-8') as f:
        text = f.read()

    clean_text = re.sub(r'[\u200e\u200f\u202a-\u202e]', '', text)

    p1_start = clean_text.find('כללי האלף')
    p2_start = clean_text.find('בס"ד כללי שני')
    if p2_start == -1:
        p2_start = clean_text.find('בס"ד כללי הגאונים')

    part1_raw = clean_text[p1_start:p2_start]

    print(f"Part 1 total raw length: {len(part1_raw)} chars")

if __name__ == '__main__':
    parse_all_sections()
