#!/usr/bin/env python3
# [PRODUCTION] Independent-witness verification for reconstructed page content.
#
# Why this exists: the reconstructed text for klal 30/75/88 comes FROM the DocAI
# token stream, so `build_corrections_dataset.py` (DocAI vs stored text) cannot
# say anything about it - measured 2026-08-11 at 1 candidate for ~3,800 words,
# circular by construction (PROJECT-STATUS.md). Verifying it needs a genuinely
# independent reading of the same pixels, not a smarter diff of the same source.
#
# Tesseract (`-l heb`) is that second reading: a different engine, already
# installed, and measured at 76.1% exact word agreement with DocAI on page 24 -
# i.e. it disagrees often enough to be informative and agrees often enough to
# align. This is the same base-vs-witness design orchestrator.py was built
# around, scoped to the specific pages that need it.
#
# Output is a REVIEW QUEUE, never a correction. Nothing here writes part1.json.
# Each row carries DocAI's bbox so a flagged word can be cropped and read
# directly (the project's standing UI/scan-verification requirement), plus a
# lexicon-based triage tier so the queue can be worked highest-suspicion first
# rather than top-to-bottom.
#
# Triage tiers (lexicon.txt = ~19k validated Rabbinic Hebrew words):
#   A  docai NOT in lexicon, tesseract IS   -> docai probably misread. Work first.
#   B  neither in lexicon                   -> both suspect, likely hard glyphs.
#   C  both in lexicon but different        -> genuine ambiguity, needs the scan.
#   D  docai IS in lexicon, tesseract NOT   -> tesseract probably wrong. Lowest.
#
# Usage: python3 verify_reconstruction_witness.py [--page 24 37 40]
import argparse
import difflib
import json
import os
import re
import subprocess

REPO = os.path.dirname(os.path.abspath(__file__))
DOCAI_DIR = os.path.join(REPO, "docai_word_boxes")
IMAGES_DIR = os.path.join(REPO, "images", "pdf_pages")
LEXICON_PATH = os.path.join(REPO, "lexicon.txt")
OUT_PATH = os.path.join(REPO, "reconstruction_witness_queue.json")

HEB = "אבגדהוזחטיכלמנסעפצקרשתךםןףץ"
FURNITURE = {"יד", "יר", "יך", "מלאכי", "כללי", "האלף", "הבית",
             "הגימל", "הדלת", "ההא", "Digitized", "by", "Google"}
# page -> the klal whose text that page carries (all three are continuation-only
# pages, i.e. no klal marker of their own - which is exactly why the normal
# corrections pipeline never sees them)
PAGE_TO_KLAL = {24: 30, 37: 75, 40: 88}
MAX_SPAN = 4


def norm(s):
    return "".join(c for c in s if c in HEB)


def load_lexicon():
    return set(w.strip() for w in open(LEXICON_PATH, encoding="utf-8") if w.strip())


def tesseract_words(page):
    img = os.path.join(IMAGES_DIR, f"page_{page}.png")
    if not os.path.exists(img):
        raise SystemExit(f"missing page image: {img}")
    out = subprocess.run(["tesseract", img, "stdout", "-l", "heb"],
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit(f"tesseract failed on page {page}: {out.stderr[:300]}")
    return [w for w in out.stdout.split() if norm(w)]


def docai_tokens(page):
    toks = json.load(open(os.path.join(DOCAI_DIR, f"page_{page}.json"), encoding="utf-8"))
    return [t for t in toks if norm(t["text"])]


def is_furniture(w):
    return norm(w) in {norm(f) for f in FURNITURE} or w.strip().isdigit()


def tier(d_word, t_word, lex):
    d_in, t_in = norm(d_word) in lex, norm(t_word) in lex
    if not d_in and t_in:
        return "A"
    if not d_in and not t_in:
        return "B"
    if d_in and t_in:
        return "C"
    return "D"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", type=int, nargs="*", default=sorted(PAGE_TO_KLAL))
    args = ap.parse_args()
    lex = load_lexicon()
    queue, stats = [], {}

    for page in args.page:
        klal_id = PAGE_TO_KLAL.get(page)
        dtoks = docai_tokens(page)
        dwords = [norm(t["text"]) for t in dtoks]
        twords = [norm(w) for w in tesseract_words(page)]
        sm = difflib.SequenceMatcher(None, dwords, twords, autojunk=False)
        agree = sum(b.size for b in sm.get_matching_blocks())
        n = 0
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                continue
            if (i2 - i1) > MAX_SPAN or (j2 - j1) > MAX_SPAN:
                continue  # large spans are alignment drift, not a word-level call
            d_seg = " ".join(t["text"] for t in dtoks[i1:i2])
            t_seg = " ".join(twords[j1:j2])
            if not d_seg or is_furniture(d_seg):
                continue
            box = dtoks[i1:i2]
            queue.append({
                "klal_id": klal_id,
                "page": page,
                "docai_reading": d_seg,
                "tesseract_reading": t_seg or None,
                "opcode": tag,
                "tier": tier(d_seg, t_seg, lex),
                "bbox": {
                    "x1": min(t["x1"] for t in box), "y1": min(t["y1"] for t in box),
                    "x2": max(t["x2"] for t in box), "y2": max(t["y2"] for t in box),
                } if box else None,
                "docai_token_index": i1,
            })
            n += 1
        stats[page] = {"klal_id": klal_id, "docai_words": len(dwords),
                       "tesseract_words": len(twords),
                       "agreement": round(agree / len(dwords), 3), "flagged": n}

    by_tier = {}
    for q in queue:
        by_tier[q["tier"]] = by_tier.get(q["tier"], 0) + 1
    json.dump({"meta": {"stats": stats, "by_tier": by_tier, "total": len(queue)},
               "queue": queue},
              open(OUT_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print("Independent-witness pass (DocAI vs Tesseract, same page image)\n")
    for p, s in stats.items():
        print(f"  page {p} (klal {s['klal_id']}): docai {s['docai_words']} words, "
              f"tesseract {s['tesseract_words']}, agreement {s['agreement']:.1%}, "
              f"{s['flagged']} flagged")
    print(f"\n  total queue: {len(queue)}")
    for t in "ABCD":
        if by_tier.get(t):
            print(f"    tier {t}: {by_tier[t]}")
    print(f"\nWrote {OUT_PATH} (review queue only - nothing was written to part1.json)")


if __name__ == "__main__":
    main()
