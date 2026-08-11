# [PRODUCTION] Part 1: align each page's full final text to its DocAI raw-OCR token
# stream in one global diff (far more robust than per-klal window search against
# repeated rabbinic phraseology), then attribute small, high-confidence word-level
# diffs back to their klal for vision-crop verification (see orchestrator.py).
#
# Klal -> page attribution comes from header_anchored_alignment.py's output
# (part1_header_anchored_alignment.json), NOT aligned_klalim - that mapping was
# discredited (see CLAUDE.md Open Items: "stop trusting artifacts"; it was built
# from a flawed process and produced false-positive alignments that don't survive
# cross-checking against each page's own printed section header). Only klalim
# marked `trusted` there get a page attribution here; untrusted/placeholder
# klalim have no reliable crop to verify against and are skipped, not guessed at.
import json
import os
import difflib

REPO = os.path.dirname(os.path.abspath(__file__))
DOCAI_DIR = os.path.join(REPO, "docai_word_boxes")
ALIGNMENT_PATH = os.path.join(REPO, "part1_header_anchored_alignment.json")
DEMO_DATASET = os.path.join(REPO, "klalim_demo_dataset.json")
PART1_MAX_KLAL = 222


def clean_word(w):
    return "".join(c for c in w if c.isalnum())


# The Google Books scan watermark ("Digitized by Google") sits at the bottom of
# many pages and is correctly absent from clean_text, exactly like the running
# header filtered below - it is page furniture, never corpus content. Same set
# used by check_klal_token_orphans.py / validate_klal_span_coverage.py's
# furniture stripping. Until 2026-08-11 these tokens produced no candidates only
# by accident: sitting at the very end of a page's word stream, they tripped the
# `j1 >= len(page_word_origin)` bail-out and were dropped unattributed. Once
# delete-opcode attribution was fixed they surfaced as 10 spurious
# "possible omission" candidates, so they now get filtered explicitly, at the
# same point punctuation-only tokens are - by design, not by side effect.
WATERMARK_WORDS = {"digitized", "by", "google"}


def is_watermark(tok_text):
    return clean_word(tok_text).lower() in WATERMARK_WORDS


def sim(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()


def union_bbox(tokens):
    return {
        "x1": min(t["x1"] for t in tokens),
        "y1": min(t["y1"] for t in tokens),
        "x2": max(t["x2"] for t in tokens),
        "y2": max(t["y2"] for t in tokens),
    }


def load_trusted_klal_pages():
    """Group klal_ids by matched_page, trusted entries only, klal_id order
    preserved within each page (matches print order)."""
    alignment = json.load(open(ALIGNMENT_PATH, encoding="utf-8"))
    klal_pages = {}
    untrusted_ids = []
    for r in sorted(alignment, key=lambda r: r["klal_id"]):
        if not (1 <= r["klal_id"] <= PART1_MAX_KLAL):
            continue
        if not r["trusted"]:
            untrusted_ids.append(r["klal_id"])
            continue
        klal_pages.setdefault(r["matched_page"], []).append(r["klal_id"])
    return klal_pages, untrusted_ids


def main():
    klal_pages, untrusted_ids = load_trusted_klal_pages()

    final_by_id = {k["klal_id"]: k for k in json.load(open(DEMO_DATASET))}

    corrections = []
    skipped_no_docai_page = set()
    unattributable_deletes = []

    for page_id, klal_ids in sorted(klal_pages.items()):
        docai_path = os.path.join(DOCAI_DIR, f"page_{page_id}.json")
        if not os.path.exists(docai_path):
            skipped_no_docai_page.update(klal_ids)
            continue

        # clean_word() strips punctuation but doesn't drop punctuation-only
        # tokens (they become "" and stay in the stream) - filter those out
        # entirely before the diff, otherwise a bare "." or "'" generates a
        # spurious opcode that looks like a real word-level disagreement.
        # Confirmed 2026-08-07: this was the root cause of 464/762 (61%) of
        # Part 1's correction candidates having a punctuation-only
        # docai_reading/final_text field (PROJECT-STATUS.md "Punctuation-
        # token diff bug fixed").
        docai_tokens = [t for t in json.load(open(docai_path))
                        if clean_word(t["text"]) and not is_watermark(t["text"])]
        docai_clean = [clean_word(t["text"]) for t in docai_tokens]

        # Build one concatenated "page final text" word stream, remembering which
        # klal + in-klal word-index each concatenated position came from.
        # word_index_in_klal deliberately stays the word's position in the
        # UNFILTERED words_raw/clean_text.split() - downstream code (assembly,
        # the review UI, apply_reviewer_decisions.py) all locates a word by
        # that index, so skipped punctuation words must leave gaps, not get
        # renumbered.
        page_words_raw = []
        page_words_clean = []
        page_word_origin = []  # (klal_id, word_index_in_klal)
        for klal_id in klal_ids:
            k = final_by_id.get(klal_id)
            if not k:
                continue
            words_raw = k["clean_text"].split()
            for idx, w in enumerate(words_raw):
                cw = clean_word(w)
                if not cw:
                    continue
                page_words_raw.append(w)
                page_words_clean.append(cw)
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

            # Attribution. For `replace`/`insert` the diff span j1:j2 is real
            # stored text, so page_word_origin[j1] is the right owner.
            #
            # For `delete` (docai saw words the stored text doesn't have)
            # j1 == j2, so page_word_origin[j1] is the word AFTER the gap. At a
            # klal boundary that word belongs to the NEXT klal, while the missing
            # text physically trails the END of the previous one - a klal's own
            # gematria marker opens it, so anything before that marker is still
            # the previous klal's. Filing it under the next klal at word_index 0
            # meant an accepted decision would insert the missing words BEFORE
            # that klal's marker, corrupting two klalim at once. Confirmed
            # 2026-08-11 on 4 of 30 live delete candidates (PROJECT-STATUS.md
            # "Deep methodology audit"): e.g. `ס"ח ונכון הוא` was filed under
            # klal 220 word 0 although klal 219 ends mid-citation (`...סימן`
            # with no number) exactly where it is missing.
            if tag == "delete":
                if j1 == 0:
                    # Missing text precedes the first klal on this page, so it
                    # trails a klal on the PREVIOUS page, which isn't in this
                    # page's word stream. Not attributable here - skip rather
                    # than guess (it would otherwise be filed under this page's
                    # first klal at word_index 0, the same bug).
                    unattributable_deletes.append((page_id, orig_word))
                    continue
                prev_klal_id = page_word_origin[j1 - 1][0]
                at_boundary = (j1 >= len(page_word_origin)
                               or page_word_origin[j1][0] != prev_klal_id)
                if at_boundary:
                    # Trails the end of prev_klal_id: append position.
                    klal_id = prev_klal_id
                    word_idx = len(final_by_id[klal_id]["clean_text"].split())
                else:
                    klal_id, word_idx = page_word_origin[j1]
            else:
                if j1 >= len(page_word_origin):
                    continue
                klal_id, word_idx = page_word_origin[j1]

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
            "unattributable_deletes": [{"page": p, "docai_reading": w} for p, w in unattributable_deletes],
            "untrusted_klalim_excluded": sorted(untrusted_ids),
        },
    }
    out_path = os.path.join(REPO, "corrections_candidates_part1.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Total candidate corrections: {len(corrections)}")
    print(f"Klalim covered: {out['meta']['klalim_covered']} / {PART1_MAX_KLAL}")
    print(f"Klalim skipped (no DocAI page data): {len(skipped_no_docai_page)}")
    print(f"Delete candidates not attributable to a klal on their own page "
          f"(missing text precedes the page's first klal): {len(unattributable_deletes)}")
    print(f"Klalim excluded as untrusted by header-anchored alignment: {len(untrusted_ids)} -> {untrusted_ids}")


if __name__ == "__main__":
    main()
