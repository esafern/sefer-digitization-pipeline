# [PRODUCTION] Full systematic trace: for every Part-1 klal, locate its
# clean_text opening within its matched page (same forward-cursor discipline
# as verify_titles_vision.py, to avoid the cross-klal crop-bleed bug already
# found and fixed there), then check whether the token AT that position is
# literally the klal's own gematria marker - computed independently from
# klal_id via standard Hebrew numeral conversion, not read from stored data.
#
# This is the check that surfaced the klal 94-114ish region shift: content
# can text-match reasonably well (repetitive Talmudic phrasing) at a position
# whose PRINTED marker says a different number entirely. Marker mismatch is a
# much harder, more specific signal than text-similarity alone.
import json
import os
import difflib

REPO = os.path.dirname(os.path.abspath(__file__))
ALIGNMENT_PATH = os.path.join(REPO, "part1_header_anchored_alignment.json")
PART1_PATH = os.path.join(REPO, "part1.json")
DOCAI_DIR = os.path.join(REPO, "docai_word_boxes")
NO_TEXT_TITLE = "(no text available)"

# Hebrew numeral conversion, traditional form (15->טו, 16->טז to avoid the
# Tetragrammaton-like יה/יו), hundreds/tens/ones concatenated (210 -> רי).
ONES = {1:'א',2:'ב',3:'ג',4:'ד',5:'ה',6:'ו',7:'ז',8:'ח',9:'ט'}
TENS = {10:'י',20:'כ',30:'ל',40:'מ',50:'נ',60:'ס',70:'ע',80:'פ',90:'צ'}
HUNDREDS = {100:'ק',200:'ר',300:'ש',400:'ת'}

def to_gematria(n):
    if n == 15:
        return 'טו'
    if n == 16:
        return 'טז'
    out = ''
    h = (n // 100) * 100
    while h > 400:
        out += HUNDREDS[400]
        h -= 400
    if h:
        out += HUNDREDS[h]
    rem = n % 100
    t = (rem // 10) * 10
    if t:
        out += TENS[t]
    o = rem % 10
    if o:
        out += ONES[o]
    return out


def clean_word(w):
    return "".join(c for c in w if c.isalnum())


ACCEPT_RATIO = 0.6


def locate_marker(page_tokens, page_clean, expected_gem, content_words, cursor_hint):
    """Anchor on an EXACT match of the gematria token itself, not on fuzzy
    content similarity - difflib.SequenceMatcher.ratio() tolerates a 1-token
    shift (it matches subsequences, not exact position), which is fine for
    cropping with margin but fatal here: being off by one token means
    checking the WRONG token as "the marker".

    Searches the WHOLE page, not a forward-only window from a running cursor:
    a strict forward-only cursor cascades badly here - if one klal's search
    fails, the next one inherits a stale cursor and searches too narrow a
    window ahead of where its own marker actually is, which can chain into
    many consecutive false "not found" results. Since the anchor is now an
    exact (and often multi-character, rare) token rather than fuzzy content,
    false-positive collisions elsewhere on the same page are uncommon enough
    that a whole-page search with cursor as a same-page tie-breaker (nearest
    wins) is more robust than strict forward-only windowing."""
    qlen = len(content_words)
    candidates = [i for i in range(len(page_tokens)) if page_tokens[i]["text"] == expected_gem]
    scored = []
    for pos in candidates:
        window = page_clean[pos + 1: pos + 1 + qlen]
        ratio = difflib.SequenceMatcher(None, content_words, window).ratio()
        scored.append((pos, ratio))
    if not scored:
        return None, 0.0
    passing = [s for s in scored if s[1] >= ACCEPT_RATIO]
    pool = passing if passing else scored
    # nearest to cursor_hint wins among the pool (passing matches preferred,
    # else the overall best-effort candidates for diagnostics)
    pool.sort(key=lambda s: (abs(s[0] - cursor_hint), -s[1]))
    return pool[0]


def main():
    alignment = {r["klal_id"]: r for r in json.load(open(ALIGNMENT_PATH, encoding="utf-8"))}
    klalim = {k["klal_id"]: k for k in json.load(open(PART1_PATH, encoding="utf-8"))}

    by_page = {}
    for kid in sorted(klalim):
        k = klalim[kid]
        if k.get("title") == NO_TEXT_TITLE:
            continue
        r = alignment.get(kid)
        if not r or not r.get("matched_page"):
            continue
        by_page.setdefault(r["matched_page"], []).append(kid)

    results = []
    page_cache = {}
    for page in sorted(by_page):
        if page not in page_cache:
            page_cache[page] = json.load(open(os.path.join(DOCAI_DIR, f"page_{page}.json"), encoding="utf-8"))
        page_tokens = page_cache[page]
        page_clean = [clean_word(t["text"]) for t in page_tokens]
        cursor = 0

        for kid in by_page[page]:
            k = klalim[kid]
            expected_gem = to_gematria(kid)
            stored_gem = k.get("gematria", "")
            words = [clean_word(w) for w in k["clean_text"].split()]
            words = [w for w in words if w]
            # drop the leading gematria token from the query itself if present,
            # so we're matching on content, and can separately check the marker
            content_words = words[1:9] if words and words[0] == stored_gem else words[:8]

            pos, ratio = locate_marker(page_tokens, page_clean, expected_gem, content_words, cursor)
            entry = {
                "klal_id": kid, "page": page, "expected_gematria": expected_gem,
                "stored_gematria": stored_gem, "content_match_ratio": round(ratio, 3) if pos is not None else None,
            }
            if pos is None:
                entry["status"] = "marker_not_found_in_window"
                results.append(entry)
                continue
            if ratio < ACCEPT_RATIO:
                entry["status"] = "marker_found_content_mismatch"
                entry["marker_position"] = pos
                results.append(entry)
                continue  # don't advance cursor on a low-confidence hit

            cursor = pos + 1 + len(content_words)
            entry["marker_position"] = pos
            entry["status"] = "ok"
            results.append(entry)

    out_path = os.path.join(REPO, "gematria_trace_part1.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    problems = [r for r in results if r["status"] != "ok"]
    print(f"Checked {len(results)} klalim, {len(problems)} problems")
    for r in problems:
        print(" ", r["klal_id"], "| expected marker:", r["expected_gematria"],
              "| status:", r["status"], "| best content ratio:", r.get("content_match_ratio"))


if __name__ == "__main__":
    main()
