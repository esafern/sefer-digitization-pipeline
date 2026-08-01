import json
import os

def update_aligned():
    with open('klalim_demo_dataset.json', 'r', encoding='utf-8') as f:
        klalim_data = json.load(f)

    os.makedirs('aligned_klalim', exist_ok=True)

    # Group by page
    pages = {}
    for item in klalim_data:
        p = item.get('page', 14)
        # Ensure bbox is present
        if 'bbox' not in item or not item['bbox']:
            # Assign a clean default bbox normalized percentage overlay
            idx_on_page = len(pages.get(p, []))
            top_pct = 12.0 + (idx_on_page * 6.0) % 75.0
            item['bbox'] = {
                'top': top_pct,
                'left': 10.0,
                'width': 80.0,
                'height': 6.0
            }
        pages.setdefault(p, []).append(item)

    for p, items in pages.items():
        page_file = f"aligned_klalim/page_{p:02d}.json"
        with open(page_file, 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=2)

    print(f"Updated aligned_klalim/ across {len(pages)} page files with valid bboxes!")

if __name__ == '__main__':
    update_aligned()
