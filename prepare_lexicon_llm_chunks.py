import os

def chunk_lexicon():
    with open('lexicon.txt', 'r', encoding='utf-8') as f:
        words = [l.strip() for l in f if l.strip()]

    print(f"Total lexicon words: {len(words)}")

    out_dir = 'scratch/llm_lexicon_chunks'
    os.makedirs(out_dir, exist_ok=True)

    chunk_size = 2000
    for i in range(0, len(words), chunk_size):
        chunk_words = words[i:i+chunk_size]
        file_path = f"{out_dir}/chunk_{i//chunk_size + 1}.txt"
        with open(file_path, 'w', encoding='utf-8') as out_f:
            out_f.write('\n'.join(chunk_words))
        print(f"Wrote {len(chunk_words)} words to {file_path}")

if __name__ == '__main__':
    chunk_lexicon()
