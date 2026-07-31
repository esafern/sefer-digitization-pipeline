import json

with open('batch_14.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

dalet_resh_words = set()
for item in data:
    text = item.get('clean_text', '')
    for word in text.split():
        if 'ר' in word or 'ד' in word or 'ך' in word or 'ן' in word or 'ף' in word or 'ץ' in word or 'ם' in word:
            dalet_resh_words.add(word.strip('.,:"\'()'))

for w in sorted(dalet_resh_words):
    print(w)

