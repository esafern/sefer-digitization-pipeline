import json
import re

with open('klalim_batches/batch_6.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Replacements requested
dr_replacements = {
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
    'ידייא': 'איידי',
    # Adding words found in text just in case:
    'הדואה': 'הרואה',
    'שדוא': 'שהוא'
}

def fix_sofit(text):
    # Fix sofit letters that are followed by another Hebrew letter
    sofit_map = {'ך': 'כ', 'ם': 'מ', 'ן': 'נ', 'ף': 'פ', 'ץ': 'צ'}
    def replace_sofit(match):
        return sofit_map[match.group(1)]
    return re.sub(r'([ךםןףץ])(?=[א-ת])', replace_sofit, text)

for item in data:
    text = item.get('clean_text', '')
    
    # 1. Apply specific word replacements
    for bad, good in dr_replacements.items():
        # Replace whole words only, except for נלער which might not be standalone
        text = re.sub(rf'\b{bad}\b', good, text)
        
    # Extra check for נלער
    text = text.replace('נלער', 'נלע"ד')
    text = text.replace('אייךו', 'איירי')
    text = text.replace('ידייא', 'איידי')
    
    # 2. Fix sofit letters in the middle of words
    text = fix_sofit(text)
    
    # 3. Look for other obvious D/R confusions
    # (e.g. דוהומת -> דוחה ומות? No, in line 42: "דוהומת" - maybe "דוחה את")
    text = text.replace('דוהומת', 'דוחה את')
    
    item['clean_text'] = text

with open('klalim_batches/batch_6.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Done fixing.")
