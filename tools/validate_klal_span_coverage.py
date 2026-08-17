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
# archive/scripts/reconstruct_crosspage_v4.py - moved out of the gitignored
# scratch/ 2026-08-11, per CLAUDE.md's warning that scratch/ held
# non-reproducible one-offs - for the furniture-stripping logic and
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
import sys

# Moved one level deeper (pipeline/ or tools/) 2026-08-16 - REPO now goes up
# two levels, not one, to keep resolving to the actual repo root where
# part1.json/docai_word_boxes/etc. live.
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pipeline"))
import corpus_io as cio  # noqa: E402

DOCAI_DIR = cio.DOCAI_DIR

# same-page ratio distribution centers on 1.11 with real klalim rarely below
# ~0.9; 0.85 leaves margin while still catching klal 175's near-miss
# (0.84, later confirmed a false positive - its "next page" content turned
# out to belong entirely to the following klal, not a real gap) for manual
# review rather than silently treating it as failing.
FLAG_RATIO_THRESHOLD = 0.85


def get_page(cache, page):
    """Signature deliberately unchanged (a plain dict passed in by the
    caller): tests/test_corpus_invariants.py calls build_spans(trace, part1,
    {}) directly, so the cache stays the caller's object rather than becoming
    a corpus_io.DocaiPageCache instance. Only the load itself is shared -
    four scripts had this same get-or-load body, disagreeing on the
    missing-page answer. None here, as before."""
    if page not in cache:
        cache[page] = cio.load_docai_page(page, DOCAI_DIR)
    return cache[page]


def build_spans(trace, part1, cache):
    """Measure every klal span that CAN be measured, and record every one that
    can't with its reason. Returns (rows, unmeasured).

    This function is the single implementation of the span math - imported and
    called by tests/test_corpus_invariants.py rather than reimplemented there.
    That duplication is exactly how the blind spot below survived a
    zero-tolerance pytest gate (audit 2026-08-10/11, PROJECT-STATUS.md): the
    test had its own copy of the same `continue` statements, so the gate was
    structurally incapable of catching what the script structurally skipped.

    Three cases used to `continue` silently, dropping 20 of 222 klalim from
    BOTH the "checked" and "skipped" counts the script printed (185 + 14 = 199,
    not 222, and nothing said so):

    1. The next klal has no marker. Fixed by pairing with the next klal that
       DOES have one and comparing against the summed stored words of every
       klal the span covers - a span that spans klalim N..M must be compared
       against N..M's combined text, not N's alone, or the ratio is
       meaninglessly low by construction.
    2. The span crosses more than one page boundary. Fixed by summing the
       intermediate pages' token counts. This case alone hid klal 30
       (ratio 0.06), klal 83-84 (0.09) and klal 88 (0.24) - the largest
       real shortfalls in Part 1, and the same cross-page-truncation failure
       mode this validator was built for.
    3. Page token data missing / no following marker at all. Still not
       measurable, but now REPORTED rather than dropped.
    """
    ids = sorted(trace)
    marker_ids = [k for k in ids if trace[k].get("marker_position") is not None]
    rows, unmeasured = [], []

    for pos, kid in enumerate(marker_ids):
        x = trace[kid]
        if pos + 1 >= len(marker_ids):
            unmeasured.append((kid, "last klal with a known marker - no following marker to bound its span"))
            continue
        next_kid = marker_ids[pos + 1]
        nx = trace[next_kid]
        page, next_page = x["page"], nx["page"]

        tokens_this = get_page(cache, page)
        if tokens_this is None:
            unmeasured.append((kid, f"page {page} token data missing"))
            continue

        if next_page == page:
            span_tokens = nx["marker_position"] - x["marker_position"]
        elif next_page > page:
            tokens_next = get_page(cache, next_page)
            if tokens_next is None:
                unmeasured.append((kid, f"page {next_page} token data missing"))
                continue
            span_tokens = (len(tokens_this) - x["marker_position"]) + nx["marker_position"]
            missing_mid = []
            for mid in range(page + 1, next_page):
                mid_tokens = get_page(cache, mid)
                if mid_tokens is None:
                    missing_mid.append(mid)
                else:
                    span_tokens += len(mid_tokens)
            if missing_mid:
                unmeasured.append((kid, f"intermediate page(s) {missing_mid} token data missing"))
                continue
        else:
            unmeasured.append((kid, f"next klal {next_kid} maps to an EARLIER page "
                                    f"({next_page} < {page}) - alignment inconsistency, not a span"))
            continue

        if not span_tokens:
            unmeasured.append((kid, f"zero-length span to klal {next_kid} (identical marker positions)"))
            continue

        covered = [k for k in range(kid, next_kid) if k in part1]
        stored_words = sum(len(part1[k]["clean_text"].split()) for k in covered)
        rows.append({
            "klal_id": kid,
            "covered_klal_ids": covered,
            "next_klal_id": next_kid,
            "page": page,
            "next_page": next_page,
            "crosses_page": next_page != page,
            "expected_tokens": span_tokens,
            "stored_words": stored_words,
            "ratio": stored_words / span_tokens,
        })
    return rows, unmeasured


def main():
    trace_path = cio.TRACE_PATH
    part1_path = cio.PART1_PATH
    if not (os.path.exists(trace_path) and os.path.exists(part1_path)):
        raise SystemExit("Missing gematria_trace_part1.json or part1.json - nothing to validate.")

    trace = {x["klal_id"]: x for x in cio.load_gematria_trace(trace_path)}
    part1 = cio.load_part1_by_id(part1_path)
    cache = {}

    rows, unmeasured = build_spans(trace, part1, cache)

    same_page = [r for r in rows if not r["crosses_page"]]
    cross_page = [r for r in rows if r["crosses_page"]]
    flagged = [r for r in rows if r["ratio"] < FLAG_RATIO_THRESHOLD]

    no_marker = sorted(k for k in trace if trace[k].get("marker_position") is None)
    not_in_trace = sorted(k for k in part1 if k not in trace)

    def mean_ratio(rs):
        vals = [r["ratio"] for r in rs]
        return sum(vals) / len(vals) if vals else None

    # Full accounting - every Part-1 klal lands in exactly one bucket below, and
    # the totals are asserted to add up. Before 2026-08-11 this printed
    # "Checked 185... 14 skipped" against 222 real klalim and said nothing about
    # the other 23 (PROJECT-STATUS.md, deep methodology audit).
    measured_ids = {k for r in rows for k in r["covered_klal_ids"]}
    print(f"Part 1: {len(part1)} klalim, {len(trace)} with a trace entry.")
    print(f"  {len(rows)} measurable spans ({len(same_page)} same-page, {len(cross_page)} cross-page), "
          f"covering {len(measured_ids)} klalim.")
    print(f"  {len(unmeasured)} span(s) NOT measurable (reported below, never silently dropped).")
    print(f"  {len(no_marker)} klal(im) with no exact-match marker position: {no_marker}")
    if not_in_trace:
        print(f"  {len(not_in_trace)} klal(im) absent from gematria_trace_part1.json entirely: {not_in_trace}")

    accounted = len(rows) + len(unmeasured)
    marker_count = len(trace) - len(no_marker)
    if accounted != marker_count:
        print(f"  !! ACCOUNTING ERROR: {accounted} spans accounted for, {marker_count} klalim have markers.")

    sp_mean, cp_mean = mean_ratio(same_page), mean_ratio(cross_page)
    print(f"\nSame-page mean ratio:  {sp_mean:.2f}" if sp_mean else "\nSame-page: n/a")
    print(f"Cross-page mean ratio: {cp_mean:.2f}" if cp_mean else "Cross-page: n/a")

    if unmeasured:
        print(f"\n{len(unmeasured)} span(s) that could not be measured:")
        for kid, reason in unmeasured:
            print(f"  klal {kid}: {reason}")

    print()
    if flagged:
        print(f"{len(flagged)} span(s) below {FLAG_RATIO_THRESHOLD} ratio (stored word count vs. real token span):")
        for r in sorted(flagged, key=lambda r: r["ratio"]):
            covered = r["covered_klal_ids"]
            label = f"klal {r['klal_id']}" if len(covered) <= 1 else \
                    f"klal {covered[0]}-{covered[-1]} ({len(covered)} klalim, combined)"
            print(f"  {label}: page {r['page']}->{r['next_page']}, "
                  f"expected~{r['expected_tokens']} tok, stored {r['stored_words']} words, "
                  f"ratio {r['ratio']:.2f}")
    else:
        print(f"No spans below {FLAG_RATIO_THRESHOLD} ratio. Clean.")


if __name__ == "__main__":
    main()
