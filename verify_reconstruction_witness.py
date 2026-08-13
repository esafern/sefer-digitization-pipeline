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
# Triage tiers (lexicon.txt = ~19k validated Rabbinic Hebrew words). A
# multi-word segment counts as "in lexicon" only if EVERY word in it is
# (checked word-by-word, not as one concatenated blob - see tier()):
#   A  docai NOT in lexicon, tesseract IS   -> docai probably misread or
#      (opcode=='insert', docai_reading is None) DOCAI OMITTED REAL
#      CONTENT ENTIRELY that tesseract caught. Work first either way.
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


FURNITURE_NORM = {norm(f) for f in FURNITURE}


def is_furniture(w):
    # FIXED 2026-08-13 (PROJECT-STATUS.md finding 3/4): this used to norm()
    # the whole (possibly multi-word) segment as one string, so a genuine
    # multi-word furniture phrase like "יך מלאכי" (folio mark + book word,
    # both individually in FURNITURE) normed to the concatenated "יךמלאכי" -
    # which matches nothing in FURNITURE_NORM, so it silently escaped the
    # filter and sat in the queue as if it were a real disputed word.
    # Confirmed: 2 of 3 page-40 furniture items escaped this way. Check
    # every word in the segment individually instead.
    words = w.split()
    if not words:
        return False
    return all(norm(wd) in FURNITURE_NORM or wd.strip().isdigit() for wd in words)


def tier(d_word, t_word, lex):
    # FIXED 2026-08-13 (PROJECT-STATUS.md finding 3): this used to norm()
    # the whole (possibly multi-word) segment as one string before the
    # lexicon lookup, so a real 2-word segment like "בתוס ד\"ה" normed to
    # the concatenated "בתוסדה" - never a real lexicon word regardless of
    # whether the individual words are - while its counterpart could
    # coincidentally concatenate into something that IS a lexicon word
    # (confirmed: "בחופ ה" -> "בחופה", a real word, driving a tier-A
    # verdict that was actually one of this session's four "tier-A"
    # adjudications and the corpus edit built on it). A segment is only
    # genuinely "in the lexicon" if EVERY word in it is a real word on its
    # own - checking word-by-word instead of on the concatenated blob.
    # Recomputed against the live queue: 62 B->D, 2 B->C, 2 B->A, 1 A->D.
    d_words = [norm(w) for w in d_word.split() if norm(w)]
    t_words = [norm(w) for w in t_word.split() if norm(w)]
    d_in = bool(d_words) and all(w in lex for w in d_words)
    t_in = bool(t_words) and all(w in lex for w in t_words)
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
        skipped_oversize = skipped_furniture = 0
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                continue
            if (i2 - i1) > MAX_SPAN or (j2 - j1) > MAX_SPAN:
                skipped_oversize += 1
                continue  # large spans are alignment drift, not a word-level call
            d_seg = " ".join(t["text"] for t in dtoks[i1:i2])
            t_seg = " ".join(twords[j1:j2])
            if is_furniture(d_seg) or is_furniture(t_seg):
                skipped_furniture += 1
                continue
            # FIXED 2026-08-13 (PROJECT-STATUS.md finding 4): this used to
            # `continue` whenever d_seg was empty (tag=='insert', i1==i2) -
            # i.e. DocAI has NOTHING at this position but Tesseract found
            # real text there. That is exactly the failure mode this
            # witness pass exists to catch (DocAI silently omitting real
            # content) and it structurally could not report a single
            # instance of it - confirmed the live queue was 416 replace +
            # 1 delete + 0 insert. An insert-opcode item has no DocAI
            # tokens of its own to bound a crop with, so anchor on the
            # nearest real DocAI token instead of dropping the item.
            if not d_seg and not t_seg:
                continue  # nothing on either side - not a real disagreement
            box = dtoks[i1:i2]
            if not box:
                if i1 < len(dtoks):
                    box = [dtoks[i1]]
                elif i1 > 0:
                    box = [dtoks[i1 - 1]]
            queue.append({
                "klal_id": klal_id,
                "page": page,
                "docai_reading": d_seg or None,
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
        # Accounting, not silent dropping (this project's own standing
        # pattern - see the round-1 and round-2 fixes to
        # validate_klal_span_coverage.py / check_klal_token_orphans.py):
        # every non-'equal' opcode now lands in "flagged" or one of these
        # two skip counters, never neither.
        stats[page] = {"klal_id": klal_id, "docai_words": len(dwords),
                       "tesseract_words": len(twords),
                       "agreement": round(agree / len(dwords), 3), "flagged": n,
                       "skipped_oversize_span": skipped_oversize,
                       "skipped_furniture": skipped_furniture}

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
