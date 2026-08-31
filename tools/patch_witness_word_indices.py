#!/usr/bin/env python3
"""One-time (idempotent) patch: add word_index to reconstruction_witness_queue.json.

witness items carry docai_token_index (an index into the page's DocAI token
list) but not a corpus word_index.  Reviewers need the corpus position so the
dashboard can highlight the word in the text pane alongside the scan boxes.

The mapping is computed via difflib.SequenceMatcher between the normalized
DocAI token stream and the normalized corpus word list for each klal.  Coverage
is high (873/880 tokens mapped for klal 30's page 24 in testing).  Items whose
token falls in an unmapped gap (rare - typically tokens that are pure furniture
or appear in a large-span skip) get word_index=null.

Multi-token DocAI segments (opcode 'replace' where the reading spans several
tokens, e.g. 'חטאת הוו' for token_index 29) map to the FIRST corpus word of
the span - enough to locate and highlight the word.

Safe to re-run: the script reads the existing queue, recomputes, and overwrites.
Any previously-computed word_index values are replaced with the freshly computed
ones (the computation is deterministic given the same corpus + DocAI pages).
"""
import difflib
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pipeline"))
sys.path.insert(0, os.path.join(REPO, "tools"))

import corpus_io as cio  # noqa: E402
import review_server as rs  # noqa: E402

OUT_PATH = os.path.join(REPO, "reconstruction_witness_queue.json")
DOCAI_DIR = cio.DOCAI_DIR
norm = cio.hebrew_letters_only
FURNITURE = {"יד", "יר", "יך", "מלאכי", "כללי", "האלף", "הבית",
             "הגימל", "הדלת", "ההא", "Digitized", "by", "Google"}


def docai_tokens_for_page(page):
    toks = cio.load_docai_page(page, DOCAI_DIR)
    if toks is None:
        raise FileNotFoundError(cio.docai_page_path(page, DOCAI_DIR))
    return [t for t in toks if norm(t["text"])]


def build_mapping(klal_id, page):
    """Return dict: docai_token_index -> corpus_word_index for this page."""
    klalim_by_id, _ = rs._load_klalim()
    k = klalim_by_id.get(klal_id)
    if not k:
        return {}
    corpus_words = cio.words_of(k)
    corpus_norm = [norm(w) for w in corpus_words]

    dtoks = docai_tokens_for_page(page)
    dwords = [norm(t["text"]) for t in dtoks]

    sm = difflib.SequenceMatcher(None, corpus_norm, dwords, autojunk=False)
    mapping = {}
    for corpus_start, dtok_start, size in sm.get_matching_blocks():
        for offset in range(size):
            mapping[dtok_start + offset] = corpus_start + offset
    return mapping


def main():
    with open(OUT_PATH, encoding="utf-8") as f:
        data = json.load(f)

    queue = data.get("queue", data) if isinstance(data, dict) else data
    if isinstance(data, dict):
        is_wrapped = True
    else:
        is_wrapped = False
        queue = data

    # Collect unique (klal_id, page) pairs
    pairs = {(w["klal_id"], w["page"]) for w in queue if w.get("page")}
    print(f"Computing word_index mappings for {len(pairs)} (klal, page) pairs:")

    mappings = {}
    for klal_id, page in sorted(pairs):
        mapping = build_mapping(klal_id, page)
        mappings[(klal_id, page)] = mapping
        covered = len(mapping)
        total_toks = len(docai_tokens_for_page(page))
        print(f"  klal={klal_id} page={page}: {covered}/{total_toks} tokens mapped")

    updated = 0
    for w in queue:
        page = w.get("page")
        klal_id = w.get("klal_id")
        ti = w.get("docai_token_index")
        if page is None or ti is None:
            w["word_index"] = None
            continue
        wi = mappings.get((klal_id, page), {}).get(ti)
        w["word_index"] = wi
        if wi is not None:
            updated += 1

    print(f"\nword_index set on {updated}/{len(queue)} items "
          f"({len(queue) - updated} unmapped → null)")

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        if is_wrapped:
            json.dump(data, f, ensure_ascii=False, indent=2)
        else:
            json.dump(queue, f, ensure_ascii=False, indent=2)
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
