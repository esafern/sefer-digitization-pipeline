import os
import json
import glob

def rechunk():
    # 1. Read master text
    with open('full_text_cleaned_goal.txt', 'r', encoding='utf-8') as f:
        klal_texts = [line.strip() for line in f if line.strip()]

    print(f"Loaded {len(klal_texts)} Klalim from full_text_cleaned_goal.txt")

    # Map klal_id (1-indexed) to cleaned text
    cleaned_map = {i + 1: text for i, text in enumerate(klal_texts)}

    # 2. Update full_text_cleaned.txt
    with open('full_text_cleaned.txt', 'w', encoding='utf-8') as f:
        for text in klal_texts:
            f.write(text + '\n\n')
    print("Updated full_text_cleaned.txt")

    # 3. Update part1.json, part2.json, part3.json
    for part_name in ['part1.json', 'part2.json', 'part3.json']:
        if os.path.exists(part_name):
            with open(part_name, 'r', encoding='utf-8') as f:
                data = json.load(f)
            updated_count = 0
            for item in data:
                kid = item.get('klal_id')
                if kid in cleaned_map:
                    item['clean_text'] = cleaned_map[kid]
                    updated_count += 1
            with open(part_name, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Updated {part_name} ({updated_count} Klalim updated)")

    # 4. Update aligned_klalim/page_*.json
    aligned_files = sorted(glob.glob('aligned_klalim/page_*.json'))
    for af in aligned_files:
        with open(af, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except Exception:
                continue
        if isinstance(data, list):
            updated = False
            for item in data:
                kid = item.get('klal_id')
                if kid in cleaned_map:
                    item['clean_text'] = cleaned_map[kid]
                    updated = True
            if updated:
                with open(af, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Updated aligned_klalim files across {len(aligned_files)} pages")

    # 5. Re-split klalim_batches
    all_klalim = []
    for part in ['part1.json', 'part2.json', 'part3.json']:
        if os.path.exists(part):
            with open(part, 'r', encoding='utf-8') as f:
                all_klalim.extend(json.load(f))

    import math
    batch_size = 10
    num_batches = math.ceil(len(all_klalim) / batch_size)
    os.makedirs('klalim_batches', exist_ok=True)
    for i in range(num_batches):
        batch = all_klalim[i * batch_size : (i + 1) * batch_size]
        filename = f'klalim_batches/batch_{i+1}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(batch, f, ensure_ascii=False, indent=2)
    print(f"Re-chunked {len(all_klalim)} Klalim into {num_batches} files in klalim_batches/")

    # 6. Update klalim/ and processed_klalim/ if present
    for kdir in ['klalim', 'processed_klalim']:
        if os.path.exists(kdir):
            files = sorted(glob.glob(f'{kdir}/*.json'))
            up_count = 0
            for kf in files:
                with open(kf, 'r', encoding='utf-8') as f:
                    try:
                        kdata = json.load(f)
                    except Exception:
                        continue
                kid = kdata.get('klal_id')
                if kid in cleaned_map:
                    if 'clean_text' in kdata:
                        kdata['clean_text'] = cleaned_map[kid]
                    if 'full_text' in kdata:
                        kdata['full_text'] = cleaned_map[kid]
                    with open(kf, 'w', encoding='utf-8') as f:
                        json.dump(kdata, f, ensure_ascii=False, indent=2)
                    up_count += 1
            print(f"Updated {up_count} files in {kdir}/")

if __name__ == '__main__':
    rechunk()
