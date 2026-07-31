import json

with open('scratch/context_review.json', 'r') as f:
    contexts = json.load(f)

with open('lexicon.txt', 'r') as f:
    lexicon = set(f.read().splitlines())

with open('scratch/flagged_words_pass_1.json', 'r') as f:
    flagged = set(json.load(f))

valid_lexicon = lexicon - flagged

# Common OCR letter confusions in Hebrew
ocr_confusions = [
    ('ר', 'ד'), ('ד', 'ר'),
    ('ה', 'ח'), ('ח', 'ה'),
    ('ס', 'ם'), ('ם', 'ס'),
    ('ב', 'כ'), ('כ', 'ב'),
    ('ט', 'מ'), ('מ', 'ט'),
    ('י', 'ו'), ('ו', 'י'),
    ('ת', 'ח'), ('ח', 'ת'),
    ('פ', 'ס'), ('ס', 'פ'),
    ('ג', 'נ'), ('נ', 'ג')
]

proposals = []

for item in contexts:
    word = item['word']
    context = item['context']
    
    proposed_word = None
    
    # Try simple letter substitutions
    for bad, good in ocr_confusions:
        if bad in word:
            candidate = word.replace(bad, good, 1) # replace one instance
            if candidate in valid_lexicon:
                proposed_word = candidate
                break
            
            # replace all instances
            candidate_all = word.replace(bad, good)
            if candidate_all in valid_lexicon:
                proposed_word = candidate_all
                break

    # Format for markdown
    corrected_context = context.replace(word, f"**{proposed_word}**") if proposed_word else "*(No confident auto-fix found)*"
    highlighted_context = context.replace(word, f"**{word}**")
    
    proposals.append(f"### {word} -> {proposed_word or '???'}\n"
                     f"- **Batch**: {item['batch']} | **Klal**: {item['klal_id']}\n"
                     f"- **Original**: {highlighted_context}\n"
                     f"- **Corrected**: {corrected_context}\n")

with open('proposed_corrections.md', 'w') as f:
    f.write("# Proposed OCR Corrections for Review\n\n")
    f.write('\n'.join(proposals))

print("Created proposed_corrections.md")
