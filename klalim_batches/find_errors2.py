import json
import re

with open('batch_14.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

sofit_mid = set()
words_all = []

for item in data:
    text = item.get('clean_text', '')
    for word in text.split():
        words_all.append(word)
        if re.search(r'[םןץףך][א-ת]', word):
            sofit_mid.add(word)

print("Mid sofits:", sofit_mid)

replacements = {
    'רחיה': 'דחיה', 'דיעבר': 'דיעבד', 'דבד': 'דבר', 'הריוט': 'הדיוט',
    'רוא': 'דוא', 'תודה': 'תורה', 'עור': 'עוד', 'חסרא': 'חסדא',
    'נלער': 'נלע"ד', 'כמד': 'כמר', 'אייךו': 'איירי', 'ידייא': 'איידי'
}

for w in words_all:
    for k in replacements.keys():
        if k in w:
            print(f"Found explicit example: {w}")

