import json

file_path = '/Users/ericsafern/work/yad-malachi/yad-malachi-pipeline/klalim_batches/batch_14.json'

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

replacements = {
    'אודחיה': 'אורחיה',
    'בחך': 'בחד',
    'בחר': 'בחד',
    'דחר': 'דחד',
    'דחקיכן': 'דחקינן',
    'דטהדרו': 'דמהדרו',
    'דבריעבד': 'דבדיעבד',
    'דיעבך': 'דיעבד',
    'לדתרות': 'להתרות',
    'מרקמתמה': 'מדקמתמה',
    'ערעוד': 'ערעור',
    'ופרויין': 'ופדוייו',
    'חרש': 'חדש',
    'שכתכו': 'שכתבו'
}

for item in data:
    if 'clean_text' in item:
        text = item['clean_text']
        
        # We replace whole words to avoid accidentally replacing substrings in larger words,
        # but since these are very specific, direct replace is mostly safe.
        # Let's do word boundary replacement.
        
        words = text.split(' ')
        new_words = []
        for word in words:
            # strip punctuation for checking
            clean_word = word.strip('.,:;()')
            if clean_word in replacements:
                # Replace the exact substring to preserve attached punctuation
                new_word = word.replace(clean_word, replacements[clean_word])
                new_words.append(new_word)
            else:
                new_words.append(word)
                
        item['clean_text'] = ' '.join(new_words)

with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

