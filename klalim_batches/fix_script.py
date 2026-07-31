import json
import re

def fix_text(text):
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
        'ידייא': 'איידי',
        'בראי': 'בדאי'
    }
    
    # Replace explicit whole words
    for k, v in replacements.items():
        text = re.sub(r'(?<![א-ת])' + k + r'(?![א-ת])', v, text)
        
    # Also catch some substring versions if they are very specific? No, word boundary is safer.
    
    # General sofit letters in the middle of words
    sofit_map = {
        'ך': 'כ',
        'ם': 'מ',
        'ן': 'נ',
        'ף': 'פ',
        'ץ': 'צ'
    }
    
    def replace_sofit(match):
        return sofit_map[match.group(1)] + match.group(2)
        
    # Repeatedly apply in case there are multiple adjacent
    prev_text = None
    while text != prev_text:
        prev_text = text
        text = re.sub(r'([ךםןףץ])([א-ת])', replace_sofit, text)
        
    return text

file_path = '/Users/ericsafern/work/yad-malachi/yad-malachi-pipeline/klalim_batches/batch_12.json'
with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

for item in data:
    if 'clean_text' in item:
        item['clean_text'] = fix_text(item['clean_text'])

with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
