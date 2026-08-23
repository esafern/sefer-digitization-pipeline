#!/usr/bin/env python3
# [STANDALONE] For a klal whose stored word count falls short of its
# marker-to-marker DocAI token span, report WHICH tokens are unaccounted for
# and classify them: page furniture (a running header, a section header, the
# klal's own marker) or real body text.
#
# Built 2026-08-23. validate_klal_span_coverage.py answers "is this klal
# short?" with a ratio; it cannot answer "short of WHAT?", and that second
# question is the one that decides the remedy. A shortfall made of header
# tokens is a measurement artifact and belongs in
# tests/test_corpus_invariants.py's SPAN_COVERAGE_BASELINE. A shortfall made
# of body text is missing corpus content and belongs in
# SPAN_COVERAGE_KNOWN_REAL_GAPS, flagged through the review-decision pipeline.
# Those two live in the same file and had been telling opposite stories about
# klal 84; klal 16 sat in the false-positive set while genuinely missing ~24
# printed words. This script exists so that call is made from evidence rather
# than from which constant someone reached for first.
#
# THIS IS A TRIAGE TOOL, NOT A VERDICT (Lesson 2). A "furniture only" result
# means nothing here looks like body text to a mechanical classifier - it is
# grounds to stop worrying, not proof the klal is complete. A "body text"
# result must still be confirmed by rendering the actual page and reading it
# (Lesson 14), and by checking whether the text is merely stored in the
# NEIGHBOURING klal rather than missing (Lesson 16, the klal 9/10 failure
# mode) - both of which this script reports on but neither of which it
# decides.
import argparse
import difflib
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pipeline"))
sys.path.insert(0, os.path.join(REPO, "tools"))

import corpus_io as cio  # noqa: E402
import validate_klal_span_coverage as vksc  # noqa: E402

# Running-header and section-header words, in the forms DocAI actually
# produces them. `יד מלאכי` (the book's running header) has its ד read as ר or
# ך often enough that an exact-match list alone misses it, which is why the
# normalized forms of the misreads are listed explicitly rather than relying
# on a confusion-pair expansion here - see validate_klal_span_coverage.py's
# own corrected header comment.
FURNITURE_WORDS = {
    cio.hebrew_letters_only(w) for w in (
        "יד", "יר", "יך", "מלאכי",           # running header + its OCR variants
        "כללי",                                # section header, first word
        "האלף", "הבית", "הגימל", "הדלת",      # ... and the letter-section names
        "ההא", "הוו", "הזין", "החית", "הטית",
        "היוד", "הכף", "הלמד", "המם", "הנון",
        "הסמך", "העין", "הפא", "הצדי", "הקוף",
        "הריש", "השין", "התיו",
    )
}


def load_trace_by_id():
    trace = cio.load_gematria_trace()
    if isinstance(trace, dict) and "klalim" in trace:
        return {r["klal_id"]: r for r in trace["klalim"]}
    if isinstance(trace, list):
        return {r["klal_id"]: r for r in trace}
    return trace


def span_tokens_for(trace, kid, next_kid, cache):
    """The raw DocAI tokens between klal kid's marker and next_kid's, using the
    same marker positions and page arithmetic build_spans() measures with, so
    this explains that function's own number rather than a second opinion."""
    x, nx = trace[kid], trace[next_kid]
    page, next_page = x["page"], nx["page"]
    toks_this = vksc.get_page(cache, page)
    if toks_this is None:
        return None
    if next_page == page:
        return toks_this[x["marker_position"]:nx["marker_position"]]
    toks = list(toks_this[x["marker_position"]:])
    for mid in range(page + 1, next_page):
        mid_toks = vksc.get_page(cache, mid)
        if mid_toks is None:
            return None
        toks.extend(mid_toks)
    toks_next = vksc.get_page(cache, next_page)
    if toks_next is None:
        return None
    toks.extend(toks_next[:nx["marker_position"]])
    return toks


def unaccounted_tokens(stored_words, span):
    """Span tokens that do not align to any stored word, in span order."""
    norm = cio.hebrew_letters_only
    stored = [norm(w) for w in stored_words if norm(w)]
    span_words, span_raw = [], []
    for t in span:
        n = norm(t.get("text", ""))
        if n:
            span_words.append(n)
            span_raw.append(t.get("text", ""))
    sm = difflib.SequenceMatcher(None, stored, span_words, autojunk=False)
    out = []
    for tag, _i1, _i2, j1, j2 in sm.get_opcodes():
        if tag in ("insert", "replace"):
            out.extend(zip(span_words[j1:j2], span_raw[j1:j2]))
    matched = sum(b.size for b in sm.get_matching_blocks())
    return out, matched, len(span_words)


def find_elsewhere(needles, exclude_klal, min_run=3):
    """Is a run of unaccounted words simply stored in a DIFFERENT klal? That is
    the klal 9/10 failure mode (Lesson 16) and it changes the remedy entirely -
    a boundary fix, not a reconstruction.

    FIXED 2026-08-23, immediately after this tool's first real use got klal 83
    wrong. The first version probed the FIRST FOUR unaccounted tokens as one
    exact window. Klal 83's unaccounted run starts `['בשו','דף','ס"א','ב']`,
    where `בשו` is an OCR misread of the neighbouring klal's bold opening word -
    so the exact probe failed and the tool reported "not found in any other
    klal -> candidate REAL truncation" for text that is, in fact, stored
    verbatim in klal 82. One bad token at the head of the run must not decide
    the answer (Lesson 6: know a matching strategy's blind spot before trusting
    what it does not flag).

    Now slides a window across the WHOLE run and uses the longest contiguous
    match, so a run whose head is noisy still anchors on its clean middle."""
    norm = cio.hebrew_letters_only
    words = [norm(w) for w, _raw in needles]
    if len(words) < min_run:
        return []
    hits = []
    for part in ("part1.json", "part2.json", "part3.json"):
        for k in cio.load_klalim(cio.repo_path(part)):
            if k["klal_id"] == exclude_klal:
                continue
            ws = [norm(w) for w in k["clean_text"].split()]
            sm = difflib.SequenceMatcher(None, words, ws, autojunk=False)
            block = sm.find_longest_match(0, len(words), 0, len(ws))
            if block.size >= min_run:
                hits.append((part, k["klal_id"], block.b, block.size))
    hits.sort(key=lambda h: -h[3])
    return hits


def report(kid, trace, part1, cache, context):
    ids = sorted(k for k in trace if trace[k].get("marker_position") is not None)
    if kid not in ids:
        print(f"klal {kid}: no marker position - span not measurable")
        return
    pos = ids.index(kid)
    if pos + 1 >= len(ids):
        print(f"klal {kid}: last klal with a marker - no following marker")
        return
    next_kid = ids[pos + 1]
    span = span_tokens_for(trace, kid, next_kid, cache)
    if span is None:
        print(f"klal {kid}: page token data missing")
        return

    stored_words = part1[kid]["clean_text"].split()
    unacc, matched, span_len = unaccounted_tokens(stored_words, span)
    furniture = [(n, r) for n, r in unacc if n in FURNITURE_WORDS]
    body = [(n, r) for n, r in unacc if n not in FURNITURE_WORDS]
    # The klal's own marker and the NEXT klal's are legitimately in the span
    # but never in stored text; do not report them as missing body.
    markers = {cio.hebrew_letters_only(cio.klal_id_to_gematria(k)) for k in (kid, next_kid)}
    body = [(n, r) for n, r in body if n not in markers]

    x, nx = trace[kid], trace[next_kid]
    print(f"\n=== klal {kid} -> {next_kid}  (page {x['page']}"
          f"{'' if nx['page'] == x['page'] else ' -> %d' % nx['page']}"
          f", {'same-page' if nx['page'] == x['page'] else 'CROSS-PAGE'})")
    print(f"    stored {len(stored_words)} words, span {span_len} tokens, matched {matched}")
    print(f"    unaccounted: {len(unacc)}  ({len(furniture)} furniture, {len(body)} other)")
    if furniture:
        print(f"    furniture: {[r for _n, r in furniture]}")
    if not body:
        print("    VERDICT: no body text unaccounted for -> consistent with a "
              "measurement artifact (triage only, not proof of completeness)")
        return
    print(f"    OTHER TOKENS: {[r for _n, r in body]}")
    hits = find_elsewhere(body, kid)
    if hits:
        top = hits[0]
        frac = top[3] / len(body)
        # A run that is MOSTLY found elsewhere is the neighbour's text sitting
        # in this span. A short generic run matching inside a long unaccounted
        # run is usually just a stock Aramaic formula (e.g. `אף על גב דלא`,
        # which recurs across dozens of klalim) and must NOT be read as
        # "found, therefore not missing" - Lesson 6, know the blind spot.
        if frac < 0.5:
            print(f"    ** PARTIAL match only: {top[3]} of {len(body)} words "
                  f"({frac:.0%}) appear in {top[0]} klal {top[1]}. Too small a "
                  f"fraction to explain the run - most likely a stock formula "
                  f"matching coincidentally. Treat as candidate REAL truncation "
                  f"and render the page (Lesson 14).")
            if context:
                print(f"    stored text ENDS: ...{' '.join(stored_words[-8:])}")
            return
        print(f"    ** {top[3]} of these {len(body)} words are STORED IN "
              f"{top[0]} klal {top[1]} (at word {top[2]}) -> NOT missing content. "
              f"Either a boundary error (klal 9/10 mode) or a marker-extraction-"
              f"order artifact (klal 65/66 mode, where the bold marker token is "
              f"emitted before the line it visually follows, so the neighbour's "
              f"tail lands inside this klal's span).")
        if len(hits) > 1:
            print(f"       other matches: {hits[1:4]}")
    else:
        print("    ** not found in any other klal -> candidate REAL truncation. "
              "Render the page and read it before concluding (Lesson 14).")
    if context:
        print(f"    stored text ENDS: ...{' '.join(stored_words[-8:])}")
        nxt = part1.get(next_kid)
        if nxt:
            print(f"    klal {next_kid} STARTS: {' '.join(nxt['clean_text'].split()[:8])}...")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("klal_ids", nargs="*", type=int,
                    help="klal ids to check (default: every klal the span "
                         "validator currently flags below its threshold)")
    ap.add_argument("--no-context", action="store_true",
                    help="omit the stored-text boundary preview")
    args = ap.parse_args()

    trace = load_trace_by_id()
    part1 = cio.load_part1_by_id()
    cache = {}

    ids = args.klal_ids
    if not ids:
        rows, _ = vksc.build_spans(trace, part1, cache)
        ids = [r["klal_id"] for r in rows if r["ratio"] < vksc.FLAG_RATIO_THRESHOLD]
        print(f"No klal ids given - checking the {len(ids)} span(s) currently "
              f"below {vksc.FLAG_RATIO_THRESHOLD}: {ids}")

    for kid in ids:
        report(kid, trace, part1, cache, context=not args.no_context)


if __name__ == "__main__":
    main()
