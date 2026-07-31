import json
import re

with open('batch_14.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

sofit_letters = "םןץףך"
mid_sofit_pattern = re.compile(r'[' + sofit_letters + r'][א-ת]+|[א-ת]+[' + sofit_letters + r'][א-ת]+')

dalet_resh_candidates = []
mid_sofits = []

for item in data:
    text = item.get('clean_text', '')
    words = text.split()
    for word in words:
        if mid_sofit_pattern.search(word):
            mid_sofits.append(word)
        if 'ר' in word or 'ד' in word:
            dalet_resh_candidates.append(word)

print("Mid sofits:")
print(set(mid_sofits))

