# [PRODUCTION] For every trusted Part-1 klal, compute the bounding region its
# text actually occupies on its scan page - not just the flagged/corrected
# words build_corrections_dataset.py tracks, but a box spanning every matched
# token. review.html uses this to highlight "you are here" on the scan pane
# even for klalim with zero flagged corrections (most of them).
#
# Reuses the exact same docai-token <-> clean_text global diff as
# build_corrections_dataset.py (same page grouping, same klal->page source),
# so the two stay consistent by construction - this is not a separate
# alignment guess, it's the same one with a different output.
import json
import os
import difflib

REPO = os.path.dirname(os.path.abspath(__file__))
DOCAI_DIR = os.path.join(REPO, "docai_word_boxes")
ALIGNMENT_PATH = os.path.join(REPO, "part1_header_anchored_alignment.json")
DEMO_DATASET = os.path.join(REPO, "klalim_demo_dataset.json")
OUT_PATH = os.path.join(REPO, "klal_page_regions.json")
PART1_MAX_KLAL = 222


def clean_word(w):
    return "".join(c for c in w if c.isalnum())


def load_trusted_klal_pages():
    alignment = json.load(open(ALIGNMENT_PATH, encoding="utf-8"))
    klal_pages = {}
    for r in sorted(alignment, key=lambda r: r["klal_id"]):
        if not (1 <= r["klal_id"] <= PART1_MAX_KLAL):
            continue
        if not r["trusted"]:
            continue
        klal_pages.setdefault(r["matched_page"], []).append(r["klal_id"])
    return klal_pages


def main():
    klal_pages = load_trusted_klal_pages()
    final_by_id = {k["klal_id"]: k for k in json.load(open(DEMO_DATASET, encoding="utf-8"))}

    regions = {}
    for page_id, klal_ids in sorted(klal_pages.items()):
        docai_path = os.path.join(DOCAI_DIR, f"page_{page_id}.json")
        if not os.path.exists(docai_path):
            continue
        docai_tokens = json.load(open(docai_path, encoding="utf-8"))
        docai_clean = [clean_word(t["text"]) for t in docai_tokens]

        page_words_clean = []
        page_word_origin = []
        for klal_id in klal_ids:
            k = final_by_id.get(klal_id)
            if not k:
                continue
            for idx, w in enumerate(k["clean_text"].split()):
                page_words_clean.append(clean_word(w))
                page_word_origin.append(klal_id)

        sm = difflib.SequenceMatcher(None, docai_clean, page_words_clean, autojunk=False)
        klal_tokens = {}
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag not in ("equal", "replace"):
                continue
            for j in range(j1, j2):
                if j >= len(page_word_origin):
                    continue
                klal_id = page_word_origin[j]
                # map j (page_words position) back to a docai token index for a bbox;
                # for 'equal' i and j advance together, for 'replace' spans may differ
                # in length - just use whatever docai tokens this opcode covers, split
                # proportionally, good enough for a region box (not a per-word claim).
                i = i1 + min(j - j1, (i2 - i1) - 1) if (i2 - i1) > 0 else None
                if i is None or i >= len(docai_tokens):
                    continue
                klal_tokens.setdefault(klal_id, []).append(docai_tokens[i])

        for klal_id, tokens in klal_tokens.items():
            if not tokens:
                continue
            regions[klal_id] = {
                "page": page_id,
                "bbox": {
                    "x1": min(t["x1"] for t in tokens),
                    "y1": min(t["y1"] for t in tokens),
                    "x2": max(t["x2"] for t in tokens),
                    "y2": max(t["y2"] for t in tokens),
                },
                "token_count": len(tokens),
            }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(regions, f, ensure_ascii=False, indent=2)
    print(f"Wrote {OUT_PATH}: {len(regions)} klal regions across {len(klal_pages)} pages")


if __name__ == "__main__":
    main()
