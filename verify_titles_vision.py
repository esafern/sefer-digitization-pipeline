# [PRODUCTION] Vision-verify each Part-1 klal's judged `title` field.
#
# Titles aren't an OCR-disagreement problem like verify_corrections_vision.py's
# word-level checks - the print doesn't punctuate where a title ends and
# explanatory text begins, so this is a comprehension judgment, not a text
# match. We crop the klal's printed opening from the scan (first CROP_WORDS
# words, independent of where our judged title happens to end - the crop must
# not leak our own answer) and ask Gemini to independently read the image and
# say where IT would end the heading, blind to our judged title. Only then do
# we compare its answer to ours.
#
# Only klalim marked `trusted` by header_anchored_alignment.py get a crop -
# without a reliable page/position, there is nothing honest to crop.
import json
import os
import sys
import time
import hashlib
import sqlite3
import re
import difflib

import fitz  # PyMuPDF
from google import genai
from google.genai import types

REPO = os.path.dirname(os.path.abspath(__file__))
PDF_PATH = os.path.join(REPO, "berlin_square.pdf")
ALIGNMENT_PATH = os.path.join(REPO, "part1_header_anchored_alignment.json")
PART1_PATH = os.path.join(REPO, "part1.json")
DOCAI_DIR = os.path.join(REPO, "docai_word_boxes")
CACHE_DB = os.path.join(REPO, "adjudication_cache.db")
OUT_PATH = os.path.join(REPO, "title_verification_part1.json")

CROP_WORDS = 30
NO_TEXT_TITLE = "(no text available)"


def clean_word(w):
    return "".join(c for c in w if c.isalnum())


def init_cache():
    conn = sqlite3.connect(CACHE_DB)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS title_cache (crop_hash TEXT PRIMARY KEY, judged_title TEXT, decision_json TEXT)"
    )
    conn.commit()
    conn.close()


def get_cached_decision(crop_bytes):
    crop_hash = hashlib.sha256(crop_bytes).hexdigest()
    conn = sqlite3.connect(CACHE_DB, timeout=10.0)
    row = conn.execute("SELECT decision_json FROM title_cache WHERE crop_hash = ?", (crop_hash,)).fetchone()
    conn.close()
    return row[0] if row else None


def cache_decision(crop_bytes, judged_title, decision_json):
    crop_hash = hashlib.sha256(crop_bytes).hexdigest()
    conn = sqlite3.connect(CACHE_DB, timeout=10.0)
    conn.execute(
        "INSERT OR REPLACE INTO title_cache (crop_hash, judged_title, decision_json) VALUES (?, ?, ?)",
        (crop_hash, judged_title, decision_json),
    )
    conn.commit()
    conn.close()


def union_bbox(tokens):
    return {
        "x1": min(t["x1"] for t in tokens),
        "y1": min(t["y1"] for t in tokens),
        "x2": max(t["x2"] for t in tokens),
        "y2": max(t["y2"] for t in tokens),
    }


ACCEPT_RATIO = 0.7
SEARCH_STAGES = [40, 150, None]  # None = rest of page; small stages since pages are short


def locate_klal_start(page_clean, query_words, search_from=0):
    """Nearest position AT OR AFTER search_from that clears ACCEPT_RATIO -
    NOT the single best-scoring position anywhere on the page. The original
    whole-page brute-force best-match version caused real cross-klal crop
    bleed: several klalim on the same page open with near-identical phrasing
    (e.g. a short run of rules all starting "אין ב\"ד יכול לבטל..."), so a
    global best-match search would happily lock onto a LATER klal's opening
    while cropping an EARLIER one (confirmed: klal 66's vision reading was
    verbatim klal 67's judged title). A per-page cursor that only moves
    forward, mirroring header_anchored_alignment.py's discipline, prevents
    that - each klal can only be found at or after where the previous klal on
    the same page was actually located."""
    qlen = len(query_words)
    if qlen == 0 or search_from >= len(page_clean) - qlen + 1:
        return None, 0.0

    best_any = (None, 0.0)
    for stage_idx, span in enumerate(SEARCH_STAGES):
        end = (len(page_clean) - qlen + 1) if span is None else min(search_from + span, len(page_clean) - qlen + 1)
        for start in range(search_from, max(search_from, end)):
            ratio = difflib.SequenceMatcher(None, query_words, page_clean[start:start + qlen]).ratio()
            if ratio > best_any[1]:
                best_any = (start, ratio)
            if ratio >= ACCEPT_RATIO:
                return start, ratio
        if span is None:
            break
    return best_any  # nothing cleared the bar - return the best guess, caller checks the ratio


def crop_word_span(doc, page_num_1indexed, tokens, padding=0.02):
    page = doc.load_page(page_num_1indexed - 1)
    rect_page = page.rect
    width, height = rect_page.width, rect_page.height
    bbox = union_bbox(tokens)

    xmin = max(0.0, bbox["x1"] - padding) * width
    ymin = max(0.0, bbox["y1"] - padding) * height
    xmax = min(1.0, bbox["x2"] + padding) * width
    ymax = min(1.0, bbox["y2"] + padding) * height

    crop_rect = fitz.Rect(xmin, ymin, xmax, ymax)
    pix = page.get_pixmap(clip=crop_rect, dpi=300)
    return pix.tobytes("png")


def sanitize_json(text):
    return re.sub(r'\\(?!["\\/bfnrtu])', '', text)


def extract_fields_lenient(text):
    """Gemini's `reasoning` field routinely quotes Hebrew abbreviations with
    gershayim (e.g. רש"י) unescaped, which breaks json.loads in a way
    sanitize_json's stray-backslash fix doesn't touch. title_reading is
    ordinary words (no embedded quotes in practice) so it parses reliably via
    regex even when the full document doesn't; confidence is a bare number;
    reasoning is best-effort since it's the field actually at fault."""
    title_m = re.search(r'"title_reading"\s*:\s*"(.*?)"\s*,\s*"confidence"', text, re.S)
    conf_m = re.search(r'"confidence"\s*:\s*([0-9.]+)', text)
    reasoning_m = re.search(r'"reasoning"\s*:\s*"(.*)"\s*\}\s*$', text, re.S)
    return {
        "title_reading": title_m.group(1) if title_m else None,
        "confidence": float(conf_m.group(1)) if conf_m else None,
        "reasoning": reasoning_m.group(1) if reasoning_m else "(unparsable reasoning field)",
    }


def adjudicate_title(client, crop_bytes, judged_title):
    cached = get_cached_decision(crop_bytes)
    if cached:
        print("  -> cache hit")
        return cached

    prompt = """
You are analyzing a raster crop from an 18th-century Rabbinic-Hebrew halachic-
methodology digest (Yad Malachi, Klalei HaGemara). Each rule ("klal") opens
with a short heading/title, followed by explanatory text - but the print does
not reliably punctuate where the heading ends and the explanation begins.

The very first item in the crop is a rule-number/item marker (a Hebrew-numeral
letter or short combination, e.g. 'ה' or 'קפו', often set in distinct type) -
EXCLUDE this marker itself from your answer; it is not part of the heading.

Read the crop directly - ignore everything except what is visible in the image.
Identify:
1. The heading/title words only, AFTER the rule-number marker: the shortest
   span of opening words that could stand alone as a heading for this rule.
   This may be as short as one word, or run several words if no shorter span
   makes sense alone.
2. Where you judge the explanatory text begins.

Respond ONLY with JSON using this structure:
{
  "title_reading": "the heading words only, exactly as read from the image",
  "confidence": 0.0 to 1.0,
  "reasoning": "brief explanation of the comprehension judgment"
}
"""

    models_to_try = ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-2.5-flash"]
    max_retries = 3
    last_err = None
    for model_name in models_to_try:
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                        types.Part.from_bytes(data=crop_bytes, mime_type="image/png"),
                        prompt,
                    ],
                    config=types.GenerateContentConfig(response_mime_type="application/json"),
                )
                print(f"  -> live call to {model_name} ok")
                cache_decision(crop_bytes, judged_title, response.text)
                return response.text
            except Exception as e:
                last_err = e
                print(f"  -> {model_name} attempt {attempt} failed: {e}")
                if "503" in str(e) or "429" in str(e):
                    time.sleep((2 ** attempt) * 2)
                else:
                    break
    raise RuntimeError(f"All models failed: {last_err}")


def title_agreement(judged_title, vision_title):
    a = [clean_word(w) for w in judged_title.split() if clean_word(w)]
    b = [clean_word(w) for w in (vision_title or "").split() if clean_word(w)]
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def main():
    init_cache()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("GEMINI_API_KEY not set")
    client = genai.Client(api_key=api_key)

    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    out_path = sys.argv[2] if len(sys.argv) > 2 else OUT_PATH

    alignment = {r["klal_id"]: r for r in json.load(open(ALIGNMENT_PATH, encoding="utf-8"))}
    klalim = {k["klal_id"]: k for k in json.load(open(PART1_PATH, encoding="utf-8"))}

    page_cache = {}
    doc = fitz.open(PDF_PATH)

    # Group by page, klal_id order within each page - a running cursor per
    # page is what makes the forward-only search in locate_klal_start correct.
    by_page = {}
    for kid in sorted(klalim):
        r = alignment.get(kid)
        k = klalim[kid]
        if not r or not r["trusted"]:
            continue
        if k.get("title") == NO_TEXT_TITLE:
            continue
        by_page.setdefault(r["matched_page"], []).append(kid)

    targets = [kid for page in sorted(by_page) for kid in by_page[page]]
    if limit:
        targets = targets[:limit]
        # rebuild by_page restricted to the limited targets, same page order
        target_set = set(targets)
        by_page = {p: [k for k in ks if k in target_set] for p, ks in by_page.items()}
        by_page = {p: ks for p, ks in by_page.items() if ks}

    results = []
    for page in sorted(by_page):
        if page not in page_cache:
            page_cache[page] = json.load(open(os.path.join(DOCAI_DIR, f"page_{page}.json"), encoding="utf-8"))
        page_tokens = page_cache[page]
        page_clean = [clean_word(t["text"]) for t in page_tokens]
        cursor = 0

        for kid in by_page[page]:
            k = klalim[kid]
            query_words = [clean_word(w) for w in k["clean_text"].split()][:8]
            query_words = [w for w in query_words if w]
            start, ratio = locate_klal_start(page_clean, query_words, cursor)
            if start is None or ratio < ACCEPT_RATIO:
                results.append({"klal_id": kid, "judged_title": k["title"], "error": "could_not_locate_on_page",
                                 "locate_ratio": round(ratio, 3) if start is not None else None})
                continue
            cursor = start + len(query_words)  # forward-only, next klal on this page starts no earlier

            span_tokens = page_tokens[start: start + CROP_WORDS]
            crop_bytes = crop_word_span(doc, page, span_tokens)

            print(f"Klal {kid} page {page}: judged title = {k['title']!r}")
            try:
                decision_text = adjudicate_title(client, crop_bytes, k["title"])
                try:
                    decision = json.loads(decision_text)
                except json.JSONDecodeError:
                    try:
                        decision = json.loads(sanitize_json(decision_text))
                    except json.JSONDecodeError:
                        decision = extract_fields_lenient(decision_text)
            except Exception as e:
                print(f"  !! failed: {e}")
                decision = {"title_reading": None, "confidence": None, "reasoning": str(e)}

            agreement = title_agreement(k["title"], decision.get("title_reading"))
            results.append({
                "klal_id": kid,
                "page": page,
                "judged_title": k["title"],
                "vision_title_reading": decision.get("title_reading"),
                "vision_confidence": decision.get("confidence"),
                "vision_reasoning": decision.get("reasoning"),
                "agreement_ratio": round(agreement, 3),
            })

    doc.close()
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    scored = [r for r in results if "agreement_ratio" in r]
    low_agreement = [r for r in scored if r["agreement_ratio"] < 0.7]
    print(f"\nWrote {len(results)} results to {out_path}")
    print(f"{len(scored)} scored, {len(low_agreement)} with agreement < 0.7:")
    for r in low_agreement:
        print(" ", r["klal_id"], repr(r["judged_title"]), "vs vision:", repr(r["vision_title_reading"]), r["agreement_ratio"])


if __name__ == "__main__":
    main()
