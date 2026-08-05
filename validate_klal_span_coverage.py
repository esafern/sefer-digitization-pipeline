# [PRODUCTION] Standing validation: does each klal's stored `clean_text`
# plausibly account for the real token span between its own marker and the
# next klal's marker on the scan? Every other check in this pipeline
# (build_corrections_dataset.py, the vision pass, the alphabetical/title
# checks) compares docai's reading against stored text WORD-BY-WORD AT
# MATCHING POSITIONS - none of them ever checks whether stored text's total
# LENGTH plausibly accounts for the real span. A klal missing its entire back
# half produces zero per-word mismatches for the words that ARE present, so
# nothing gets flagged as a "correction candidate" - omitting a whole tail
# isn't a disagreement between two readings, it's just short, and length was
# never checked against the source until this script.
#
# Confirmed real, corpus-wide, 2026-08-05 (see PROJECT-STATUS.md "MAJOR:
# cross-page klal truncation"): klal 2's stored text ended mid-sentence
# exactly at a page boundary, missing ~175 real words that were never
# captured anywhere (not even under the wrong klal_id, unlike the separate
# 92-165 off-by-one shift bug). A corpus-wide sweep found 15 of 26 cross-page
# klalim similarly truncated (klal 4 was missing 93% of its real content).
# All 15 were fixed 2026-08-05 by reconstructing clean_text as the real
# marker-to-marker docai token span, stripping running-header/catchword/
# footnote-digit/Google-Books-watermark furniture (see
# scratch/reconstruct_crosspage_v4.py for the furniture-stripping logic and
# the visual/positional verification that validated it - true catchwords sit
# centered on their own line, ~0.57-0.60 indented from the page's right
# margin, regardless of font-size, which turned out to be a more reliable
# signal than font size alone).
#
# Same-page klalim are NOT similarly affected (mean stored/expected ratio
# 1.11 vs 0.70 for cross-page klalim, checked before the fix) - this is
# specifically a page-crossing bug, not a general corpus problem.
#
# Scope: Part 1 only. Requires gematria_trace_part1.json's marker positions
# (built by trace_gematria_sequence.py-style exact-match anchoring) and
# docai_word_boxes/ page tokens. Parts 2-3 have neither yet, so this can't
# run there - that's a known gap, not silently skipped.
import json
import os

REPO = os.path.dirname(os.path.abspath(__file__))
DOCAI_DIR = os.path.join(REPO, "docai_word_boxes")

# same-page ratio distribution centers on 1.11 with real klalim rarely below
# ~0.9; 0.85 leaves margin while still catching klal 175's near-miss
# (0.84, later confirmed a false positive - its "next page" content turned
# out to belong entirely to the following klal, not a real gap) for manual
# review rather than silently treating it as failing.
FLAG_RATIO_THRESHOLD = 0.85


def get_page(cache, page):
    if page not in cache:
        path = os.path.join(DOCAI_DIR, f"page_{page}.json")
        if not os.path.exists(path):
            cache[page] = None
        else:
            cache[page] = json.load(open(path, encoding="utf-8"))
    return cache[page]


def main():
    trace_path = os.path.join(REPO, "gematria_trace_part1.json")
    part1_path = os.path.join(REPO, "part1.json")
    if not (os.path.exists(trace_path) and os.path.exists(part1_path)):
        raise SystemExit("Missing gematria_trace_part1.json or part1.json - nothing to validate.")

    trace = {x["klal_id"]: x for x in json.load(open(trace_path, encoding="utf-8"))}
    part1 = {k["klal_id"]: k for k in json.load(open(part1_path, encoding="utf-8"))}
    ids = sorted(trace)
    cache = {}

    rows = []
    skipped_no_marker = []
    for idx, kid in enumerate(ids):
        x = trace[kid]
        if x.get("marker_position") is None:
            skipped_no_marker.append(kid)
            continue
        if idx + 1 >= len(ids):
            continue
        next_kid = ids[idx + 1]
        nx = trace[next_kid]
        if nx.get("marker_position") is None:
            continue

        page, next_page = x["page"], nx["page"]
        tokens_this = get_page(cache, page)
        if tokens_this is None:
            continue

        if next_page == page:
            span_tokens = nx["marker_position"] - x["marker_position"]
            crosses_page = False
        elif next_page == page + 1:
            tokens_next = get_page(cache, next_page)
            if tokens_next is None:
                continue
            span_tokens = (len(tokens_this) - x["marker_position"]) + nx["marker_position"]
            crosses_page = True
        else:
            continue  # spans more than one page boundary - not handled here

        stored_words = len(part1[kid]["clean_text"].split()) if kid in part1 else 0
        ratio = stored_words / span_tokens if span_tokens else None
        rows.append({
            "klal_id": kid, "page": page, "next_page": next_page,
            "crosses_page": crosses_page, "expected_tokens": span_tokens,
            "stored_words": stored_words, "ratio": ratio,
        })

    same_page = [r for r in rows if not r["crosses_page"]]
    cross_page = [r for r in rows if r["crosses_page"]]
    flagged = [r for r in rows if r["ratio"] is not None and r["ratio"] < FLAG_RATIO_THRESHOLD]

    def mean_ratio(rs):
        vals = [r["ratio"] for r in rs if r["ratio"] is not None]
        return sum(vals) / len(vals) if vals else None

    print(f"Checked {len(rows)} klalim ({len(same_page)} same-page, {len(cross_page)} cross-page); "
          f"{len(skipped_no_marker)} skipped (no exact-match marker position).")
    sp_mean, cp_mean = mean_ratio(same_page), mean_ratio(cross_page)
    print(f"Same-page mean ratio: {sp_mean:.2f}" if sp_mean else "Same-page: n/a")
    print(f"Cross-page mean ratio: {cp_mean:.2f}" if cp_mean else "Cross-page: n/a")
    print()

    if flagged:
        print(f"{len(flagged)} klalim below {FLAG_RATIO_THRESHOLD} ratio (stored word count vs. real token span):")
        for r in sorted(flagged, key=lambda r: r["ratio"]):
            print(f"  klal {r['klal_id']}: page {r['page']}->{r['next_page']}, "
                  f"expected~{r['expected_tokens']} tok, stored {r['stored_words']} words, "
                  f"ratio {r['ratio']:.2f}")
    else:
        print(f"No klalim below {FLAG_RATIO_THRESHOLD} ratio. Clean.")


if __name__ == "__main__":
    main()
