import json
import re

def fix_text(text):
    # Specific Dalet/Resh confusions to fix based on prompt examples and common OCR errors
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
        'רמסייע': 'דמסייע', # seen in line 6
        'כתכו': 'כתבו',     # seen in line 42
        'השארי': 'השאר',   # etc.
    }
    
    for k, v in replacements.items():
        text = text.replace(k, v)
        
    # Fix Sofit letters appearing in the middle of words
    sofit_map = {
        'ך': 'כ',
        'ם': 'מ',
        'ן': 'נ',
        'ף': 'פ',
        'ץ': 'צ'
    }
    
    for sofit, regular in sofit_map.items():
        text = re.sub(sofit + r'(?=[א-ת])', regular, text)
        
    return text

def main():
    file_path = '/Users/ericsafern/work/yad-malachi/yad-malachi-pipeline/klalim_batches/batch_7.json'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    for entry in data:
        if 'clean_text' in entry:
            entry['clean_text'] = fix_text(entry['clean_text'])
            
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()
