# [PRODUCTION] For every trusted Part-1 klal, compute the bounding region its
# text actually occupies on its scan page - not just the flagged/corrected
# words build_corrections_dataset.py tracks, but a box spanning every matched
# token. review_server.py uses this to highlight "you are here" on the scan
# pane even for klalim with zero flagged corrections (most of them).
#
# Two region-computation strategies, in preference order:
#   1. Marker-anchored, Y-COORDINATE banding: when both this klal's own real
#      marker position AND the next klal's are known (gematria_trace_part1.json,
#      status=='ok'), a klal's region = every token on the page whose Y
#      (line) position falls between the two markers' Y positions. Confirmed
#      2026-08-07 (PROJECT-STATUS.md "review dashboard feedback") this is
#      necessary, not just more-precise-than-needed: klal markers sometimes
#      sit OUT OF READING ORDER in docai's raw token array (a marker glyph in
#      the right-margin gap next to a bold opening word gets array-indexed
#      among the PREVIOUS klal's trailing tokens, despite being visually on
#      its own new line) - the same anomaly already documented for klal 3's
#      own marker (see gematria_trace's note field) turned out to also apply
#      to klal 4's marker, and RAW ARRAY-INDEX slicing (or the old content-
#      diff heuristic, which has no marker anchor at all) has no way to tell
#      the difference. Y-coordinate banding sidesteps this entirely: it
#      doesn't care what order docai's array lists tokens in, only where they
#      visually sit on the page.
#   2. Content-diff heuristic (the original approach, unchanged): for any
#      klal where the marker-anchored approach above doesn't have both
#      endpoints available, reuse the same docai-token <-> clean_text global
#      diff as build_corrections_dataset.py (same page grouping, same
#      klal->page source) - a coarser, non-marker-anchored fallback, "good
#      enough for a region box, not a per-word claim" per the original
#      design.
import json
import os
import difflib

REPO = os.path.dirname(os.path.abspath(__file__))
DOCAI_DIR = os.path.join(REPO, "docai_word_boxes")
ALIGNMENT_PATH = os.path.join(REPO, "part1_header_anchored_alignment.json")
TRACE_PATH = os.path.join(REPO, "gematria_trace_part1.json")
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


def load_markers():
    """klal_id -> (page, marker_position) for every klal with a confirmed
    real marker position - only status=='ok' entries are trustworthy
    (see CLAUDE.md Lesson 3 on gematria_trace's own status field going
    stale)."""
    trace = json.load(open(TRACE_PATH, encoding="utf-8"))
    return {
        e["klal_id"]: (e["page"], e["marker_position"])
        for e in trace
        if e.get("status") == "ok" and e.get("marker_position") is not None
    }


def union_bbox(tokens):
    return {
        "x1": min(t["x1"] for t in tokens),
        "y1": min(t["y1"] for t in tokens),
        "x2": max(t["x2"] for t in tokens),
        "y2": max(t["y2"] for t in tokens),
    }


def marker_anchored_regions(klal_pages, markers, docai_by_page):
    """For every klal whose own marker AND the immediately-following klal's
    marker are both known, band by Y-coordinate between the two - see
    module docstring for why Y-banding, not array-index slicing."""
    regions = {}
    all_klal_ids = sorted({kid for ids in klal_pages.values() for kid in ids})
    for idx, klal_id in enumerate(all_klal_ids):
        if klal_id not in markers:
            continue
        page, marker_idx = markers[klal_id]
        tokens = docai_by_page.get(page)
        if tokens is None or marker_idx >= len(tokens):
            continue
        marker_tok = tokens[marker_idx]

        def center_y(t):
            return (t["y1"] + t["y2"]) / 2

        start_center = center_y(marker_tok)

        # end boundary: the next klal_id's marker, wherever it is.
        next_page, next_marker_idx = None, None
        if idx + 1 < len(all_klal_ids):
            next_id = all_klal_ids[idx + 1]
            if next_id in markers:
                next_page, next_marker_idx = markers[next_id]

        end_center = None
        if next_page == page:
            end_tokens = tokens
            if next_marker_idx is not None and next_marker_idx < len(end_tokens):
                end_center = center_y(end_tokens[next_marker_idx])

        # Compare token CENTERS, not raw y1 - a marker glyph and the bold,
        # visually-taller opening word beside it on the SAME line don't
        # share a y1 (the bold word's box starts higher), so a same-line
        # token can have a smaller y1 than the marker's own y1 despite
        # being on the identical line (confirmed 2026-08-07 debugging klal
        # 3/4's boundary: "אין" y1=0.874 vs its own marker "ד" y1=0.881,
        # 0.007 apart despite being side by side). Centers converge much
        # more tightly for same-line tokens regardless of glyph height.
        tol = 0.004
        band = [t for t in tokens if center_y(t) >= start_center - tol
                and (end_center is None or center_y(t) < end_center - tol)]
        if not band:
            continue

        # This klal genuinely continues onto one or more later pages (e.g.
        # klal 4: starts on the last line of page 15, the next klal doesn't
        # start until page 16 - most of klal 4's text is physically on the
        # far side of a page boundary). A single start-page bbox can't
        # highlight that continuation at all, which is exactly what a
        # reviewer needs when a klal's flagged correction sits on the
        # second page (2026-08-07, PROJECT-STATUS.md "review dashboard
        # feedback"). Add one bbox per additional page the klal's content
        # touches, up to and including the page the NEXT klal's marker
        # lands on (every full intermediate page belongs entirely to this
        # klal; the final one is capped at the next marker).
        continuations = []
        if next_page is not None and next_page > page:
            for cont_page in range(page + 1, next_page + 1):
                cont_tokens = docai_by_page.get(cont_page)
                if not cont_tokens:
                    continue
                if cont_page == next_page and next_marker_idx is not None and next_marker_idx < len(cont_tokens):
                    cont_end_center = center_y(cont_tokens[next_marker_idx])
                    cont_band = [t for t in cont_tokens if center_y(t) < cont_end_center - tol]
                else:
                    cont_band = cont_tokens
                if cont_band:
                    continuations.append({
                        "page": cont_page,
                        "bbox": union_bbox(cont_band),
                        "token_count": len(cont_band),
                    })

        entry = {"page": page, "bbox": union_bbox(band), "token_count": len(band)}
        if continuations:
            entry["continuations"] = continuations
        regions[klal_id] = entry
    return regions


def heuristic_regions(klal_pages, docai_by_page, final_by_id, already_done):
    regions = {}
    for page_id, klal_ids in sorted(klal_pages.items()):
        raw_tokens = docai_by_page.get(page_id)
        if raw_tokens is None:
            continue
        # Punctuation-only tokens must be dropped for this diff (2026-08-07,
        # PROJECT-STATUS.md "Punctuation-token diff bug fixed") - marker_
        # anchored_regions() needs the raw unfiltered array for index
        # validity, but this heuristic path never uses marker indices, so
        # filtering here is safe and necessary.
        docai_tokens = [t for t in raw_tokens if clean_word(t["text"])]
        docai_clean = [clean_word(t["text"]) for t in docai_tokens]

        page_words_clean = []
        page_word_origin = []
        for klal_id in klal_ids:
            k = final_by_id.get(klal_id)
            if not k:
                continue
            for idx, w in enumerate(k["clean_text"].split()):
                cw = clean_word(w)
                if not cw:
                    continue
                page_words_clean.append(cw)
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
                if klal_id in already_done:
                    continue
                i = i1 + min(j - j1, (i2 - i1) - 1) if (i2 - i1) > 0 else None
                if i is None or i >= len(docai_tokens):
                    continue
                klal_tokens.setdefault(klal_id, []).append(docai_tokens[i])

        for klal_id, tokens in klal_tokens.items():
            if not tokens:
                continue
            regions[klal_id] = {"page": page_id, "bbox": union_bbox(tokens), "token_count": len(tokens)}
    return regions


def main():
    klal_pages = load_trusted_klal_pages()
    markers = load_markers()
    final_by_id = {k["klal_id"]: k for k in json.load(open(DEMO_DATASET, encoding="utf-8"))}

    # Every page in the covered range, not just pages that have a klal marker
    # on them. A page that is ENTIRELY one klal's continuation (no marker of its
    # own) would otherwise never be loaded, so it could never appear in that
    # klal's `continuations` list and the reviewer could not see it on the scan
    # pane at all. Found 2026-08-11 on klal 75, whose text runs page 36 -> 37
    # with the whole of page 37 inside it: the continuation silently listed only
    # page 38. The same hole applies to pages 24 and 40 (klal 30 and klal 88's
    # middle pages) - i.e. precisely the pages needed to verify the outstanding
    # cross-page reconstruction work. Loading the full range is cheap (~82 small
    # JSON files) and removes the whole class.
    anchor_pages = set(klal_pages) | {p for p, _ in markers.values()}
    pages_needed = set(range(min(anchor_pages), max(anchor_pages) + 1)) if anchor_pages else set()
    docai_by_page = {}
    for page_id in pages_needed:
        docai_path = os.path.join(DOCAI_DIR, f"page_{page_id}.json")
        if not os.path.exists(docai_path):
            continue
        # Drop punctuation-only tokens - clean_word() reduces them to "" but
        # doesn't remove them, which can spuriously misattribute a bbox near
        # punctuation (2026-08-07, PROJECT-STATUS.md "Punctuation-token diff
        # bug fixed"). Marker indices in gematria_trace were computed against
        # the ORIGINAL (unfiltered) docai_word_boxes array, so this filtering
        # must happen consistently for both strategies below - recomputing
        # it once here, shared.
        raw = json.load(open(docai_path, encoding="utf-8"))
        docai_by_page[page_id] = raw  # unfiltered - marker_position indexes into this

    regions = marker_anchored_regions(klal_pages, markers, docai_by_page)
    regions.update(heuristic_regions(klal_pages, docai_by_page, final_by_id, already_done=set(regions)))

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(regions, f, ensure_ascii=False, indent=2)
    n_anchored = sum(1 for kid in regions if kid in markers)
    print(f"Wrote {OUT_PATH}: {len(regions)} klal regions across {len(klal_pages)} pages "
          f"({n_anchored} marker-anchored, {len(regions) - n_anchored} heuristic fallback)")


if __name__ == "__main__":
    main()
