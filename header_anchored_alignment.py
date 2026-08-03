# [PRODUCTION] First-principles Part-1 page alignment, replacing aligned_klalim's
# discredited page mapping (see CLAUDE.md Open Items: "stop trusting artifacts").
#
# Two independent ground truths only:
#   1. The scan, via DocAI raw OCR tokens in docai_word_boxes/ (a proxy for the
#      printed image - not adjudicated, not corrected, just what's on the page).
#   2. clean_text in part1.json - our current best/adjudicated text per klal.
# A third signal, lexicon.txt (the validated Rabbinic-Hebrew word list), checks
# that clean_text's words are real vocabulary, independent of alignment entirely.
#
# Root-cause finding baked in here: docai_word_boxes/page_1.json..page_12.json
# are byte-identical duplicates of page_13.json..page_24.json (verified by content
# hash - a systematic off-by-12 bug in whatever batch OCR run produced pages 1-61).
# Pages 1-12 are excluded below; they add no unique content (their real counterparts
# are pages 13-24) and, left in, would let the sequence matcher lock onto either
# copy of that span, which is very likely why the previous unanchored alignment
# derived nonsense page attributions.
#
# The previous (non-anchored) whole-corpus SequenceMatcher approach falsely
# reported "confident" klal 1-94 alignment reaching PDF page 60 - but page 60's
# own printed header is "ההא" (Hei, klal 148+), not "הבית" (Bet, where klal 94
# belongs per part1.json's own section field). That is a direct contradiction:
# the previous match was a false positive from repetitive Talmudic phrasing, not
# real alignment. Anchoring every candidate match against the page's own printed
# section header (independent of any derived mapping) catches exactly this.
import json
import os
import re
import glob
import difflib

REPO = os.path.dirname(os.path.abspath(__file__))
DOCAI_DIR = os.path.join(REPO, "docai_word_boxes")
PART1_PATH = os.path.join(REPO, "part1.json")
LEXICON_PATH = os.path.join(REPO, "lexicon.txt")

DUPLICATE_PAGES = set(range(1, 13))  # exact duplicates of pages 13-24, see header comment

# Order matters: this is the sequence Part 1 must progress through.
SECTION_HEADERS = ["האלף", "הבית", "הגימל", "הדלת", "ההא"]


def clean_word(w):
    return "".join(c for c in w if c.isalnum())


def load_pages():
    """Ordered dict of page_num -> list of DocAI tokens, duplicates excluded."""
    pages = {}
    for f in sorted(glob.glob(os.path.join(DOCAI_DIR, "page_*.json"))):
        p = int(re.search(r"page_(\d+)", f).group(1))
        if p in DUPLICATE_PAGES:
            continue
        pages[p] = json.load(open(f, encoding="utf-8"))
    return dict(sorted(pages.items()))


def detect_header(tokens, min_ratio=0.75):
    """Fuzzy-match the page's first ~15 tokens against known section headers.
    Handles OCR misreads (e.g. 'הגימר' for 'הגימל') via ratio instead of exact
    equality. Returns None if nothing on the page matches confidently - that's
    a fact worth surfacing, not something to paper over with a guess."""
    best, best_ratio = None, 0.0
    for t in tokens[:15]:
        tt = t["text"] if isinstance(t, dict) else t
        for h in SECTION_HEADERS:
            r = difflib.SequenceMatcher(None, tt, h).ratio()
            if r > best_ratio:
                best_ratio, best = r, h
    return best if best_ratio >= min_ratio else None


def build_token_stream(pages):
    """Flatten to one global list of (page, token_index, clean_text, raw_text),
    plus page -> detected header."""
    stream = []
    page_header = {}
    for p, toks in pages.items():
        page_header[p] = detect_header(toks)
        for idx, t in enumerate(toks):
            stream.append((p, idx, clean_word(t["text"]), t["text"]))
    return stream, page_header


def expected_section(klal):
    """Derive the expected header word directly from part1.json's own `section`
    field (e.g. 'כללי הבית' -> 'הבית') - independent of any page mapping, since
    this is assigned per klal from the book's own acrostic structure, not from
    aligned_klalim's page grouping."""
    sec = klal.get("section", "")
    for h in SECTION_HEADERS:
        if h in sec:
            return h
    return None


def query_words(klal, n=8):
    """First n real words of clean_text (cleaned), including the leading
    gematria token if present - it's a short, low-uniqueness anchor on its own,
    but combined with the words that follow it's a solid first-principles query
    straight from our best current text."""
    words = [clean_word(w) for w in klal["clean_text"].split()]
    words = [w for w in words if w]
    return words[:n]


ACCEPT_RATIO = 0.7  # tolerates ~2 OCR-vs-clean_text word mismatches out of an 8-word query
SEARCH_STAGES = [500, 1500, 6000, None]  # None = rest of stream; widen only if needed


def find_best_start(stream, search_from, query, expected_hdr, page_header):
    """Prefer the NEAREST position to search_from that clears ACCEPT_RATIO and
    sits on a page whose printed header matches expected_hdr - not the single
    highest-scoring position anywhere in a wide window. Consecutive klalim are
    printed within a few hundred tokens of each other; a distant "better"
    fuzzy-match on repetitive Talmudic phrasing is exactly the failure mode
    that produced the previous session's false positive at klal 94. Search is
    staged (widen only if nothing qualifies) so any jump larger than
    necessary is visible in the `search_stage` field, not silently accepted.
    Falls back to the best-scoring position regardless of header only if no
    in-section candidate ever clears the bar, and marks it untrusted."""
    qlen = len(query)
    if qlen == 0 or search_from >= len(stream) - qlen:
        return None, 0.0, None, False, None

    # A page's printed header reflects whichever section *starts* that page -
    # the first klal(im) of a new section can legitimately still sit on the
    # last page of the previous section if the transition happens mid-page.
    # Accept the immediately-preceding section's header too, so this real
    # printing convention isn't mistaken for a bad alignment.
    acceptable_headers = {expected_hdr}
    if expected_hdr in SECTION_HEADERS:
        idx = SECTION_HEADERS.index(expected_hdr)
        if idx > 0:
            acceptable_headers.add(SECTION_HEADERS[idx - 1])

    best_any = (None, 0.0)
    for stage_idx, span in enumerate(SEARCH_STAGES):
        end = len(stream) - qlen if span is None else min(search_from + span, len(stream) - qlen)
        for start in range(search_from, max(search_from, end)):
            window = [stream[start + i][2] for i in range(qlen)]
            ratio = difflib.SequenceMatcher(None, query, window).ratio()
            if ratio > best_any[1]:
                best_any = (start, ratio)
            if ratio >= ACCEPT_RATIO:
                pg = stream[start][0]
                if expected_hdr is None or page_header.get(pg) in acceptable_headers:
                    return start, ratio, pg, True, stage_idx
        if span is None:
            break
    # nothing in-section cleared the bar at any stage - report the best guess, untrusted
    start, ratio = best_any
    pg = stream[start][0] if start is not None else None
    return start, ratio, pg, False, None


def load_lexicon():
    return set(w.strip() for w in open(LEXICON_PATH, encoding="utf-8") if w.strip())


def lexicon_hit_rate(clean_text, lexicon):
    words = [clean_word(w) for w in clean_text.split()]
    words = [w for w in words if w]
    if not words:
        return None
    hits = sum(1 for w in words if w in lexicon)
    return hits / len(words)


def main():
    pages = load_pages()
    stream, page_header = build_token_stream(pages)

    print("Deduplicated pages loaded:", sorted(pages.keys())[0], "-", sorted(pages.keys())[-1])
    print("Page -> detected header:")
    for p in sorted(page_header):
        print(f"  page {p}: {page_header[p]}")

    klalim = json.load(open(PART1_PATH, encoding="utf-8"))
    klalim = sorted(klalim, key=lambda k: k["klal_id"])
    lexicon = load_lexicon()

    cursor = 0
    results = []

    for k in klalim:
        expected_hdr = expected_section(k)
        query = query_words(k, n=8)
        lex_rate = lexicon_hit_rate(k["clean_text"], lexicon)

        start, ratio, page, trusted, stage_idx = find_best_start(
            stream, cursor, query, expected_hdr, page_header
        )
        actual_hdr = page_header.get(page) if page is not None else None
        jump_tokens = (start - cursor) if (start is not None) else None

        results.append({
            "klal_id": k["klal_id"],
            "expected_section": expected_hdr,
            "matched_page": page,
            "matched_page_header": actual_hdr,
            "match_ratio": round(ratio, 3),
            "trusted": trusted,
            "search_stage": stage_idx,
            "jump_tokens": jump_tokens,
            "lexicon_hit_rate": round(lex_rate, 3) if lex_rate is not None else None,
        })

        if start is not None and trusted:
            cursor = start + len(query)  # advance past the matched span, trusted only

    out_path = os.path.join(REPO, "part1_header_anchored_alignment.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    trusted_n = sum(1 for r in results if r["trusted"])
    print(f"\n{trusted_n}/{len(results)} klalim trusted (in-section match found)")

    untrusted = [r for r in results if not r["trusted"]]
    print(f"\n{len(untrusted)} untrusted klalim:")
    for r in untrusted:
        print(" ", r["klal_id"], "expected:", r["expected_section"], "| best guess page:", r["matched_page"],
              "(header", r["matched_page_header"], ") ratio", r["match_ratio"])

    large_stage = [r for r in results if r["trusted"] and r["search_stage"] and r["search_stage"] >= 2]
    print(f"\n{len(large_stage)} trusted klalim that needed a widened search (stage >= 2, i.e. jumped >1500 tokens):")
    for r in large_stage:
        print(" ", r["klal_id"], "stage", r["search_stage"], "jump_tokens", r["jump_tokens"])

    low_lex = [r for r in results if r["lexicon_hit_rate"] is not None and r["lexicon_hit_rate"] < 0.5]
    print(f"\n{len(low_lex)} klalim with <50% lexicon hit rate:")
    for r in low_lex:
        print(" ", r["klal_id"], r["lexicon_hit_rate"])


if __name__ == "__main__":
    main()
