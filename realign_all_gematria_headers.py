import re

def to_gematria(n):
    units = ["", "א", "ב", "ג", "ד", "ה", "ו", "ז", "ח", "ט"]
    tens = ["", "י", "כ", "ל", "מ", "נ", "ס", "ע", "פ", "צ"]
    hundreds = ["", "ק", "ר", "ש", "ת"]
    
    if n == 15:
        return "טו"
    if n == 16:
        return "טז"
        
    res = ""
    if n >= 100:
        h = n // 100
        res += hundreds[h]
        n %= 100
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

def realign():
    with open('full_text_cleaned_goal.txt', 'r', encoding='utf-8') as f:
        content = f.read()
        
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    print(f"Loaded {len(lines)} Klalim lines.")
    
    realigned_lines = []
    for i, l in enumerate(lines, 1):
        words = l.split()
        expected_gematria = to_gematria(i)
        # Keep everything after words[0]
        rest_of_line = ' '.join(words[1:])
        realigned_line = f"{expected_gematria} {rest_of_line}"
        realigned_lines.append(realigned_line)
        
    with open('full_text_cleaned_goal.txt', 'w', encoding='utf-8') as f:
        for l in realigned_lines:
            f.write(l + '\n\n')
            
    print(f"Successfully realigned all {len(realigned_lines)} Klalim headers!")

if __name__ == '__main__':
    realign()
