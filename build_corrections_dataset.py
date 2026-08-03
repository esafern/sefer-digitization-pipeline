# [PRODUCTION] Part 1: align each page's full final text to its DocAI raw-OCR token
# stream in one global diff (far more robust than per-klal window search against
# repeated rabbinic phraseology), then attribute small, high-confidence word-level
# diffs back to their klal for vision-crop verification (see orchestrator.py).
import json
import os
import re
import glob
import difflib

REPO = os.path.dirname(os.path.abspath(__file__))
DOCAI_DIR = os.path.join(REPO, "docai_word_boxes")
ALIGNED_DIR = os.path.join(REPO, "aligned_klalim")
DEMO_DATASET = os.path.join(REPO, "klalim_demo_dataset.json")
PART1_MAX_KLAL = 222


def clean_word(w):
    return "".join(c for c in w if c.isalnum())


def sim(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()


def union_bbox(tokens):
    return {
        "x1": min(t["x1"] for t in tokens),
        "y1": min(t["y1"] for t in tokens),
        "x2": max(t["x2"] for t in tokens),
        "y2": max(t["y2"] for t in tokens),
    }


def main():
    klal_pages = {}
    for f in sorted(glob.glob(os.path.join(ALIGNED_DIR, "page_*.json"))):
        page_id = int(re.search(r"page_(\d+)", f).group(1))
        ids = [k["klal_id"] for k in json.load(open(f)) if 1 <= k["klal_id"] <= PART1_MAX_KLAL]
        if ids:
            # de-dupe while preserving order
            seen = set()
            klal_pages[page_id] = [i for i in ids if not (i in seen or seen.add(i))]

    final_by_id = {k["klal_id"]: k for k in json.load(open(DEMO_DATASET))}

    corrections = []
    skipped_no_docai_page = set()

    for page_id, klal_ids in sorted(klal_pages.items()):
        docai_path = os.path.join(DOCAI_DIR, f"page_{page_id}.json")
        if not os.path.exists(docai_path):
            skipped_no_docai_page.update(klal_ids)
            continue

        docai_tokens = json.load(open(docai_path))
        docai_clean = [clean_word(t["text"]) for t in docai_tokens]

        # Build one concatenated "page final text" word stream, remembering which
        # klal + in-klal word-index each concatenated position came from.
        page_words_raw = []
        page_words_clean = []
        page_word_origin = []  # (klal_id, word_index_in_klal)
        for klal_id in klal_ids:
            k = final_by_id.get(klal_id)
            if not k:
                continue
            words_raw = k["clean_text"].split()
            for idx, w in enumerate(words_raw):
                page_words_raw.append(w)
                page_words_clean.append(clean_word(w))
                page_word_origin.append((klal_id, idx))

        sm = difflib.SequenceMatcher(None, docai_clean, page_words_clean, autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                continue
            # Only trust small, local diffs - large spans are alignment drift, not
            # real per-word corrections.
            if (i2 - i1) > 4 or (j2 - j1) > 4:
                continue

            orig_tokens = docai_tokens[i1:i2]
            orig_word = " ".join(t["text"] for t in orig_tokens) or None
            corrected_word = " ".join(page_words_raw[j1:j2]) or None

            # Every page carries a running header ("יד מלאכי" + section name) that is
            # correctly stripped from clean_text - it's expected to be "missing", not a
            # real omission, so don't flag it as one.
            if orig_word and "מלאכי" in orig_word:
                continue

            if tag == "replace" and orig_word and corrected_word:
                if (i2 - i1) != (j2 - j1):
                    continue  # word-count mismatch on a replace -> likely drift
                if sim(orig_word, corrected_word) < 0.5:
                    continue  # too dissimilar to be a genuine OCR misread

            klal_id, word_idx = page_word_origin[j1] if j1 < len(page_word_origin) else (None, None)
            if klal_id is None:
                continue

            corrections.append({
                "klal_id": klal_id,
                "page": page_id,
                "opcode": tag,
                "word_index_in_final_text": word_idx,
                "original_word": orig_word,
                "corrected_word": corrected_word,
                "bbox": union_bbox(orig_tokens) if orig_tokens else None,
            })

    out = {
        "corrections": corrections,
        "meta": {
            "total_candidates": len(corrections),
            "klalim_covered": len(set(c["klal_id"] for c in corrections)),
            "skipped_no_docai_page_klalim": sorted(skipped_no_docai_page),
        },
    }
    out_path = os.path.join(REPO, "corrections_candidates_part1.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Total candidate corrections: {len(corrections)}")
    print(f"Klalim covered: {out['meta']['klalim_covered']} / {PART1_MAX_KLAL}")
    print(f"Klalim skipped (no DocAI page data): {len(skipped_no_docai_page)}")


if __name__ == "__main__":
    main()
