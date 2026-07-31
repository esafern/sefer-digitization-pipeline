import json
import glob
import re

with open('scratch/flagged_words_pass_1.json', 'r') as f:
    flagged_words = json.load(f)

contexts = []
flagged_set = set(flagged_words)

batch_files = glob.glob('klalim_batches/batch_*.json')

for batch_file in batch_files:
    with open(batch_file, 'r') as f:
        try:
            klalim = json.load(f)
        except:
            continue
        
        for k in klalim:
            text = k.get('clean_text', '')
            words = text.split()
            for i, w in enumerate(words):
                clean_w = re.sub(r'[^א-ת]', '', w)
                if clean_w in flagged_set:
                    start = max(0, i - 10)
                    end = min(len(words), i + 11)
                    context_snippet = ' '.join(words[start:end])
                    contexts.append({
                        'word': clean_w,
                        'klal_id': k.get('klal_id'),
                        'batch': batch_file,
                        'context': context_snippet
                    })

with open('scratch/context_review.json', 'w') as f:
    json.dump(contexts, f, ensure_ascii=False, indent=2)

print(f"Extracted {len(contexts)} contextual sentences.")
