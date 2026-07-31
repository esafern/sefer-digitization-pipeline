import json
import re

file_path = '/Users/ericsafern/work/yad-malachi/yad-malachi-pipeline/klalim_batches/batch_4.json'

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

replacements = {
    'רחיה': 'דחיה',
    'דיעבר': 'דיעבד',
    'דבד': 'דבר',
    'הריוט': 'הדיוט',
    'רוא': 'דוא',
    'תודה': 'תורה',
    'עור': 'עוד',
    'חסרא': 'חסדא',
    'נלער': 'נלע"ד',
    'כמד': 'כמר',
    'אייךו': 'איירי',
    'ידייא': 'איידי'
}

sofit_map = {
    'ך': 'כ',
    'ם': 'מ',
    'ן': 'נ',
    'ף': 'פ',
    'ץ': 'צ'
}

def fix_sofit(text):
    for sofit, regular in sofit_map.items():
        text = re.sub(sofit + r'(?=[א-ת])', regular, text)
    return text

for item in data:
    if 'clean_text' in item:
        text = item['clean_text']
        # Apply specific replacements
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Also let's do a generic word boundary replace just in case? No, the user said "e.g.", 
        # let's just do a blind replace of these substrings, and generic sofit replacement.
        text = fix_sofit(text)
        item['clean_text'] = text

with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Done")
