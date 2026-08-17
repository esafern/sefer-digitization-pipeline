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
import bisect
import json
import os
import difflib

import corpus_io as cio

# Moved one level deeper (pipeline/ or tools/) 2026-08-16 - REPO now goes up
# two levels, not one, to keep resolving to the actual repo root where
# part1.json/docai_word_boxes/etc. live.
REPO = cio.REPO
DOCAI_DIR = cio.DOCAI_DIR
ALIGNMENT_PATH = cio.ALIGNMENT_PATH
TRACE_PATH = cio.TRACE_PATH
DEMO_DATASET = cio.DEMO_DATASET_PATH
OUT_PATH = os.path.join(REPO, "klal_page_regions.json")
# max(klal_id) in part1.json. Was the same literal written out independently
# here, in build_corrections_dataset.py and in review_server.py - see the
# longer note at build_corrections_dataset.py's copy for what each one
# silently did wrong if they ever disagreed. DEDUPLICATED 2026-08-17: one
# definition in corpus_io, still asserted equal to the live corpus by
# tests/test_corpus_invariants.py.
PART1_MAX_KLAL = cio.PART1_MAX_KLAL
center_y = cio.center_y

# Byte-identical private copy until 2026-08-17; shared with
# build_corrections_dataset.py and validate_catchword_continuity.py.
clean_word = cio.clean_word


def load_trusted_klal_pages():
    """This module only needs the page grouping; build_corrections_dataset.py
    needs the untrusted list too, and had the identical loop. One
    implementation (corpus_io.trusted_klal_pages) returns both; this caller
    discards the second value explicitly instead of a second copy of the loop
    quietly not collecting it."""
    klal_pages, _untrusted = cio.trusted_klal_pages(ALIGNMENT_PATH, PART1_MAX_KLAL)
    return klal_pages


def load_markers():
    """klal_id -> (page, marker_position) for every klal with a confirmed
    real marker position.

    FIXED 2026-08-17 (bug, code - PROJECT-STATUS.md "klal_page_regions.json
    continuation-bounds bug"): used to accept status=='ok' only, while
    load_end_boundary_positions() below - in this SAME file - already
    accepted 'marker_found_content_mismatch' too, with its own docstring
    citing the established project convention (also used by
    tools/check_klal_token_orphans.py) that both statuses "carry a real,
    usable position," only 'marker_not_found_in_window' does not. That
    inconsistency meant a klal like 167 (status 'marker_found_content_
    mismatch', but its marker_position independently scan-verified - see
    gematria_trace_part1.json's own note) was trusted as an END boundary
    for its neighbor but NOT as a START anchor for itself, so it fell
    through to the coarser heuristic_regions() fallback (no multi-page
    continuation support at all) instead of getting a proper marker-
    anchored, Y-banded region - producing exactly the "undersized region"
    bug reported. Matching load_end_boundary_positions()'s filter here
    fixes klal 167 and, consistently, klal 1/18/86/172 (the same five
    entries load_end_boundary_positions() already trusted)."""
    trace = cio.load_gematria_trace(TRACE_PATH)
    return {
        e["klal_id"]: (e["page"], e["marker_position"])
        for e in trace
        if e.get("status") in ("ok", "marker_found_content_mismatch")
        and e.get("marker_position") is not None
    }


def load_end_boundary_positions():
    """klal_id -> (page, marker_position) for EVERY klal with any usable
    marker position, independent of load_markers()'s stricter 'ok'-only
    filter and of load_trusted_klal_pages()'s unrelated 'trusted' concept -
    used only to find where the NEXT klal's content actually starts, for
    capping a region's end boundary.

    FIXED 2026-08-13 (PROJECT-STATUS.md finding 12): marker_anchored_
    regions() used to look only at all_klal_ids[idx+1] - the next TRUSTED
    klal_id in the page-alignment sense - and require it to have an 'ok'
    marker, so a same-page neighbor whose marker merely has a lesser
    status (e.g. 'marker_found_content_mismatch', which - per this
    project's own established convention, see check_klal_token_orphans.py
    - still carries a real, usable position) was invisible to it. Confirmed
    the exact mechanism on klal 17 (page 20, 'ok', marker 29): klal 18 sits
    on the SAME page at marker 351 but is 'marker_found_content_mismatch',
    so klal 17's box got no end boundary at all and extended to the
    physical bottom of the page (0.866 of page height, 833 tokens, vs a
    0.123 median) - correctly swallowing content that belongs to klal 18.
    Also fixes the compounding case (klal 46/47/48 on page 30): when the
    IMMEDIATE next klal (47) has NO usable position of any kind, the old
    code stopped there instead of continuing the search to klal 48, which
    does have one on the same page."""
    trace = cio.load_gematria_trace(TRACE_PATH)
    return {
        e["klal_id"]: (e["page"], e["marker_position"])
        for e in trace
        if e.get("status") in ("ok", "marker_found_content_mismatch") and e.get("marker_position") is not None
    }


def union_bbox(tokens):
    return {
        "x1": min(t["x1"] for t in tokens),
        "y1": min(t["y1"] for t in tokens),
        "x2": max(t["x2"] for t in tokens),
        "y2": max(t["y2"] for t in tokens),
    }


def marker_anchored_regions(klal_pages, markers, end_boundary_positions, docai_by_page):
    """For every klal whose own marker AND the next available marker are
    both known, band by Y-coordinate between the two - see module
    docstring for why Y-banding, not array-index slicing."""
    regions = {}
    all_klal_ids = sorted({kid for ids in klal_pages.values() for kid in ids})
    end_boundary_ids = sorted(end_boundary_positions)
    for idx, klal_id in enumerate(all_klal_ids):
        if klal_id not in markers:
            continue
        page, marker_idx = markers[klal_id]
        tokens = docai_by_page.get(page)
        if tokens is None or marker_idx >= len(tokens):
            continue
        marker_tok = tokens[marker_idx]
        start_center = center_y(marker_tok)

        # End boundary: the NEXT klal_id with any usable marker position
        # (see load_end_boundary_positions - not just the immediately
        # next id in all_klal_ids, and not restricted to 'ok' status),
        # wherever it is. bisect finds the first candidate id strictly
        # greater than this klal - end_boundary_ids is small (<=222) so a
        # linear-cost bisect per klal is negligible.
        next_page, next_marker_idx = None, None
        pos = bisect.bisect_right(end_boundary_ids, klal_id)
        if pos < len(end_boundary_ids):
            next_page, next_marker_idx = end_boundary_positions[end_boundary_ids[pos]]

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
    end_boundary_positions = load_end_boundary_positions()
    final_by_id = {k["klal_id"]: k for k in cio.load_demo_dataset(DEMO_DATASET)}

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
        # Deliberately UNFILTERED. Punctuation-only tokens must be dropped
        # before a content diff (2026-08-07, PROJECT-STATUS.md
        # "Punctuation-token diff bug fixed") but must NOT be dropped here:
        # gematria_trace's marker_position indexes into the original
        # docai_word_boxes array, so filtering at load time would shift every
        # marker index off by the number of punctuation tokens before it.
        # heuristic_regions() therefore filters locally instead (it never uses
        # marker indices); marker_anchored_regions() needs the array as-is.
        # An earlier version of this comment claimed the filtering happened
        # here, "shared" by both strategies - it never did, and the line
        # directly below it said the opposite. corpus_io.load_docai_page
        # carries the same unfiltered guarantee in its own docstring.
        tokens = cio.load_docai_page(page_id, DOCAI_DIR)
        if tokens is None:
            continue
        docai_by_page[page_id] = tokens

    anchored = marker_anchored_regions(klal_pages, markers, end_boundary_positions, docai_by_page)
    heuristic = heuristic_regions(klal_pages, docai_by_page, final_by_id, already_done=set(anchored))
    # Anchored wins on a collision: strategy 1 is the preferred one per this
    # module's docstring, and the merge should say so directly rather than
    # depend on heuristic_regions() having honoured `already_done` - two
    # things that have to agree instead of one. It was written
    # {**anchored, **heuristic}, i.e. the coarse content-diff fallback
    # silently overriding the marker-anchored box if that second mechanism
    # ever lapsed.
    #
    # Written as setdefault rather than {**heuristic, **anchored} so the
    # KEY ORDER is unchanged too (anchored first, then heuristic) - dicts
    # serialise in insertion order, and the other spelling reorders all 222
    # entries in a tracked file for no functional reason. 0 klal_ids are in
    # both maps today, so this is behaviour-preserving in every respect;
    # verified by a full rebuild producing a byte-identical
    # klal_page_regions.json. tests/test_pipeline_logic.py still checks
    # `already_done` itself.
    regions = dict(anchored)
    for klal_id, region in heuristic.items():
        regions.setdefault(klal_id, region)

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(regions, f, ensure_ascii=False, indent=2)
    # Counted from which strategy actually produced each region, not from
    # `kid in markers` - having a marker is not the same as the marker-anchored
    # path succeeding (it bails on a missing page, an out-of-range marker index,
    # or an empty Y-band, and such a klal then falls through to the heuristic
    # while still being "in markers"). No such klal exists today, which is
    # exactly why the wrong count read as right.
    print(f"Wrote {OUT_PATH}: {len(regions)} klal regions across {len(klal_pages)} pages "
          f"({len(anchored)} marker-anchored, {len(heuristic)} heuristic fallback)")


if __name__ == "__main__":
    main()
