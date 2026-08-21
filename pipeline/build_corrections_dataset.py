# [PRODUCTION] Part 1: align each page's full final text to its DocAI raw-OCR token
# stream in one global diff (far more robust than per-klal window search against
# repeated rabbinic phraseology), then attribute small, high-confidence word-level
# diffs back to their klal for vision-crop verification (see
# verify_corrections_vision.py, the next rebuild_all.sh stage - the older
# orchestrator.py this used to point at was archived 2026-08-11 as dead).
#
# Klal -> page attribution comes from part1_header_anchored_alignment.json
# (produced by archive/scripts/header_anchored_alignment.py, a one-time run),
# NOT aligned_klalim - that mapping was discredited (CLAUDE.md Lesson 3, "never
# trust a derived/aggregate artifact as ground truth"; it was built from a flawed
# process and produced false-positive alignments that don't survive
# cross-checking against each page's own printed section header). Only klalim
# marked `trusted` there get a page attribution here; untrusted/placeholder
# klalim have no reliable crop to verify against and are skipped, not guessed at.
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
DEMO_DATASET = cio.DEMO_DATASET_PATH
# Highest klal_id belonging to Part 1 - i.e. max(klal_id) in part1.json, which
# is data, not a chosen number. DOCUMENTED 2026-08-15: this same literal used
# to be written out independently here, in build_klal_page_regions.py and in
# review_server.py, with no comment in any of the three and nothing tying it
# back to the corpus. If Part 1 ever gains or loses a klal (a split/merge -
# Success Criterion #2's own failure mode) and only one copy had been updated,
# each script would have failed silently and differently: this one drops the
# klal from candidate generation AND from the "Klalim covered: N / 222"
# denominator it prints, build_klal_page_regions gives it no scan region,
# review_server stops serving it to the dashboard entirely.
# DEDUPLICATED 2026-08-17: all three now read corpus_io.PART1_MAX_KLAL, so
# there is nothing left for the three copies to disagree about. The half of
# tests/test_corpus_invariants.py::test_part1_max_klal_constants_agree_with_
# the_corpus that still matters - the constant equals max(klal_id) in the live
# part1.json - is unchanged and still gates the rebuild.
PART1_MAX_KLAL = cio.PART1_MAX_KLAL
# Longest diff span, in words, still treated as a real per-word correction
# rather than alignment drift. Named 2026-08-14: it was a bare literal `4`
# repeated on both sides of the opcode test, and review_frontend/app.js's
# multi-word-highlight code already cited it by an invented name ("MAX_SPAN=4")
# that did not exist anywhere.
MAX_DIFF_SPAN_WORDS = 4
# Minimum character-level SequenceMatcher ratio between the DocAI reading and
# the stored text before a same-word-count 'replace' opcode is believed to be
# one word misread as another rather than two unrelated words the global diff
# happened to line up. Named 2026-08-15 (it was a bare literal 0.5 with only
# "too dissimilar to be a genuine OCR misread" next to it). The value is a
# triage cut-off with no derivation on record - it has never been calibrated
# against a labelled set, and per CLAUDE.md Lesson 15 the candidates it drops
# are silent, not reported, so lowering it would surface more candidates
# rather than fewer. Do not treat "no candidate here" as "checked and clean".
MIN_REPLACE_SIMILARITY = 0.5


# Shared with build_klal_page_regions.py and validate_catchword_continuity.py,
# which each carried a byte-identical private copy until 2026-08-17 - see
# corpus_io's module docstring. The furniture sets below are deliberately NOT
# shared, for the reason the comment on WATERMARK_WORDS gives.
clean_word = cio.clean_word


# The Google Books scan watermark ("Digitized by Google") sits at the bottom of
# many pages and is correctly absent from clean_text, exactly like the running
# header filtered below - it is page furniture, never corpus content.
#
# CORRECTED 2026-08-15: this comment used to claim this was the "same set used
# by check_klal_token_orphans.py / validate_klal_span_coverage.py's furniture
# stripping". Both halves were false, and the second is the more misleading -
# validate_klal_span_coverage.py does no furniture stripping AT ALL (it counts
# raw tokens; its docstring only describes the archived reconstruct script's
# stripping), which is precisely why known-complete klalim like 106/123/175
# sit in that validator's flagged baseline: ~8-11 furniture tokens inflate
# their expected span. The sets are also genuinely different, not shared:
# this one is 3 lowercase watermark words matched through clean_word().lower();
# check_klal_token_orphans.FURNITURE_WORDS additionally carries the running
# header (יד/יר/יך/מלאכי/כללי) and matches the raw token exactly, case- and
# punctuation-sensitively; validate_catchword_continuity uses a third form
# again (HEADER_WORDS + a case-insensitive FURNITURE_RE + is_header_word's
# gershayim guard). Three near-duplicate definitions of "page furniture" is a
# real drift risk, deliberately NOT unified 2026-08-15: their matching rules
# differ, so a single shared set would silently change what each script
# strips. Documented here rather than papered over - see PROJECT-STATUS.md.
#
# Until 2026-08-11 these tokens produced no candidates only
# by accident: sitting at the very end of a page's word stream, they tripped the
# `j1 >= len(page_word_origin)` bail-out and were dropped unattributed. Once
# delete-opcode attribution was fixed they surfaced as 10 spurious
# "possible omission" candidates, so they now get filtered explicitly, at the
# same point punctuation-only tokens are - by design, not by side effect.
WATERMARK_WORDS = {"digitized", "by", "google"}


def is_watermark(tok_text):
    return clean_word(tok_text).lower() in WATERMARK_WORDS


# Every page carries a running header ("יד מלאכי" + section name) that is
# correctly stripped from clean_text - it's expected to be "missing" from a
# diff span, not a real omission, so a span containing it must not be flagged
# as one. FIXED 2026-08-16 (round-2 follow-up): this used to be a substring
# test (`"מלאכי" in orig_word`) on the whole joined diff-span text. A real
# word that merely CONTAINS those four letters as a substring (a prefix
# glued on the front, or an adjacent token fused into the same span) would
# have been silently treated as header furniture and dropped - never
# surfacing as a candidate, with no flag or log to notice by. Matches
# check_klal_token_orphans.FURNITURE_WORDS's convention instead: exact token
# equality, not substring containment. Extracted to its own function
# (previously inline in main()) so it's unit-testable without the full
# DocAI/page-word pipeline.
def is_running_header(orig_tokens):
    return any(t["text"] == "מלאכי" for t in orig_tokens)


def sim(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()


def union_bbox(tokens):
    return {
        "x1": min(t["x1"] for t in tokens),
        "y1": min(t["y1"] for t in tokens),
        "x2": max(t["x2"] for t in tokens),
        "y2": max(t["y2"] for t in tokens),
    }


def estimate_insert_bbox(docai_tokens, i1):
    """Bbox estimate for an 'insert'-opcode candidate: stored text with NO
    matching DocAI token at all (i1 == i2 in the diff span - see the
    'insert' branch in main() below), so there's no token to crop directly,
    unlike replace/delete. Added 2026-08-21 (PROJECT-STATUS.md open item 8,
    user-requested, "baked into the tool, not a one-off"): union the DocAI
    tokens immediately BEFORE and AFTER the gap in DocAI's own reading-order
    stream - a band spanning "roughly where the missing word should sit",
    the same "generous crop, visible margin" precedent as CLAUDE.md
    Lesson 14, not a precise single-word guess. Callers must treat this
    differently from a real per-word bbox (see corrections' own
    `bbox_estimated` field) - it can span two real words' worth of page
    width if the neighbors aren't adjacent on the same line.

    Returns None only if there are zero DocAI tokens on the whole page
    (i1 == 0 and docai_tokens is empty) - not expected in practice, since a
    page that produced any correction candidate at all has tokens by
    construction, but handled rather than assumed."""
    neighbors = []
    if i1 > 0:
        neighbors.append(docai_tokens[i1 - 1])
    if i1 < len(docai_tokens):
        neighbors.append(docai_tokens[i1])
    if not neighbors:
        return None
    return union_bbox(neighbors)


def load_trusted_klal_pages():
    """Group klal_ids by matched_page, trusted entries only, klal_id order
    preserved within each page (matches print order). Includes continuation
    pages so that klals spanning multiple pages get correction candidates
    generated for ALL their pages, not just the start page.

    Body moved to corpus_io 2026-08-17; switched from trusted_klal_pages to
    trusted_klal_pages_with_continuations 2026-08-19 to fix the 56 multi-page
    klalim whose continuation-page words never generated candidates. Kept as
    a thin wrapper so this module's own ALIGNMENT_PATH/PART1_MAX_KLAL remain
    what the function reads (and stay monkeypatchable).
    """
    return cio.trusted_klal_pages_with_continuations(ALIGNMENT_PATH, PART1_MAX_KLAL)


def main():
    klal_pages, untrusted_ids = load_trusted_klal_pages()

    final_by_id = {k["klal_id"]: k for k in cio.load_demo_dataset(DEMO_DATASET)}

    corrections = []
    skipped_no_docai_page = set()
    unattributable_deletes = []

    for page_id, klal_ids in sorted(klal_pages.items()):
        raw_tokens = cio.load_docai_page(page_id, DOCAI_DIR)
        if raw_tokens is None:
            skipped_no_docai_page.update(klal_ids)
            continue

        # clean_word() strips punctuation but doesn't drop punctuation-only
        # tokens (they become "" and stay in the stream) - filter those out
        # entirely before the diff, otherwise a bare "." or "'" generates a
        # spurious opcode that looks like a real word-level disagreement.
        # Confirmed 2026-08-07: this was the root cause of 464/762 (61%) of
        # Part 1's correction candidates having a punctuation-only
        # docai_reading/final_text field (PROJECT-STATUS.md "Punctuation-
        # token diff bug fixed"). The filtering stays here, at the call site,
        # rather than moving into corpus_io.load_docai_page - that loader is
        # deliberately unfiltered because marker positions index into the raw
        # array (see its docstring).
        docai_tokens = [t for t in raw_tokens
                        if clean_word(t["text"]) and not is_watermark(t["text"])]
        docai_clean = [clean_word(t["text"]) for t in docai_tokens]

        # Build one concatenated "page final text" word stream, remembering which
        # klal + in-klal word-index each concatenated position came from.
        # word_index_in_klal deliberately stays the word's position in the
        # UNFILTERED words_raw/clean_text.split() - downstream code (assembly,
        # the review UI, apply_reviewer_decisions.py) all locates a word by
        # that index, so skipped punctuation words must leave gaps, not get
        # renumbered.
        page_words_raw = []
        page_words_clean = []
        page_word_origin = []  # (klal_id, word_index_in_klal)
        for klal_id in klal_ids:
            k = final_by_id.get(klal_id)
            if not k:
                continue
            words_raw = k["clean_text"].split()
            for idx, w in enumerate(words_raw):
                cw = clean_word(w)
                if not cw:
                    continue
                page_words_raw.append(w)
                page_words_clean.append(cw)
                page_word_origin.append((klal_id, idx))

        sm = difflib.SequenceMatcher(None, docai_clean, page_words_clean, autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                continue
            # Only trust small, local diffs - large spans are alignment drift, not
            # real per-word corrections.
            if (i2 - i1) > MAX_DIFF_SPAN_WORDS or (j2 - j1) > MAX_DIFF_SPAN_WORDS:
                continue

            orig_tokens = docai_tokens[i1:i2]
            orig_word = " ".join(t["text"] for t in orig_tokens) or None
            corrected_word = " ".join(page_words_raw[j1:j2]) or None

            # See is_running_header()'s docstring above for why this is an exact-token
            # test, not the substring test it used to be. Verified empirically that
            # this diff-span-level header IS always its own standalone DocAI token on
            # real data - byte-identical corrections_candidates_part1.json before and
            # after this change - so the fix is a no-op today, defence-in-depth against
            # the next scan/print where it might not be.
            if orig_tokens and is_running_header(orig_tokens):
                continue

            if tag == "replace" and orig_word and corrected_word:
                if (i2 - i1) != (j2 - j1):
                    continue  # word-count mismatch on a replace -> likely drift
                if sim(orig_word, corrected_word) < MIN_REPLACE_SIMILARITY:
                    continue  # too dissimilar to be a genuine OCR misread

            # Attribution. For `replace`/`insert` the diff span j1:j2 is real
            # stored text, so page_word_origin[j1] is the right owner.
            #
            # For `delete` (docai saw words the stored text doesn't have)
            # j1 == j2, so page_word_origin[j1] is the word AFTER the gap. At a
            # klal boundary that word belongs to the NEXT klal, while the missing
            # text physically trails the END of the previous one - a klal's own
            # gematria marker opens it, so anything before that marker is still
            # the previous klal's. Filing it under the next klal at word_index 0
            # meant an accepted decision would insert the missing words BEFORE
            # that klal's marker, corrupting two klalim at once. Confirmed
            # 2026-08-11 on 4 of 30 live delete candidates (PROJECT-STATUS.md
            # "Deep methodology audit"): e.g. `ס"ח ונכון הוא` was filed under
            # klal 220 word 0 although klal 219 ends mid-citation (`...סימן`
            # with no number) exactly where it is missing.
            if tag == "delete":
                if j1 == 0:
                    # Missing text precedes the first klal on this page, so it
                    # trails a klal on the PREVIOUS page, which isn't in this
                    # page's word stream. Not attributable here - skip rather
                    # than guess (it would otherwise be filed under this page's
                    # first klal at word_index 0, the same bug).
                    unattributable_deletes.append((page_id, orig_word))
                    continue
                prev_klal_id = page_word_origin[j1 - 1][0]
                at_boundary = (j1 >= len(page_word_origin)
                               or page_word_origin[j1][0] != prev_klal_id)
                if at_boundary:
                    # Trails the end of prev_klal_id: append position.
                    klal_id = prev_klal_id
                    word_idx = len(final_by_id[klal_id]["clean_text"].split())
                else:
                    klal_id, word_idx = page_word_origin[j1]
            else:
                if j1 >= len(page_word_origin):
                    continue
                klal_id, word_idx = page_word_origin[j1]

            # 'insert'-opcode candidates have no matching DocAI token
            # (orig_tokens is empty - see the attribution comment above),
            # so union_bbox(orig_tokens) is never usable for them; estimate
            # a band instead. FIXED 2026-08-21 (PROJECT-STATUS.md open item
            # 8): these used to always get bbox=None, which meant
            # verify_corrections_vision.py skipped vision-cropping them
            # entirely and review_server.py's api_page() never served them
            # to the dashboard - a real word never got a scan-pane highlight
            # or a chance at vision adjudication.
            if tag == "insert":
                bbox = estimate_insert_bbox(docai_tokens, i1)
                bbox_estimated = bbox is not None
            else:
                bbox = union_bbox(orig_tokens) if orig_tokens else None
                bbox_estimated = False

            corrections.append({
                "klal_id": klal_id,
                "page": page_id,
                "opcode": tag,
                "word_index_in_final_text": word_idx,
                "original_word": orig_word,
                "corrected_word": corrected_word,
                "bbox": bbox,
                "bbox_estimated": bbox_estimated,
            })

    out = {
        "corrections": corrections,
        "meta": {
            "total_candidates": len(corrections),
            "klalim_covered": len(set(c["klal_id"] for c in corrections)),
            "skipped_no_docai_page_klalim": sorted(skipped_no_docai_page),
            "unattributable_deletes": [{"page": p, "docai_reading": w} for p, w in unattributable_deletes],
            "untrusted_klalim_excluded": sorted(untrusted_ids),
        },
    }
    out_path = os.path.join(REPO, "corrections_candidates_part1.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Total candidate corrections: {len(corrections)}")
    print(f"Klalim covered: {out['meta']['klalim_covered']} / {PART1_MAX_KLAL}")
    print(f"Klalim skipped (no DocAI page data): {len(skipped_no_docai_page)}")
    print(f"Delete candidates not attributable to a klal on their own page "
          f"(missing text precedes the page's first klal): {len(unattributable_deletes)}")
    print(f"Klalim excluded as untrusted by header-anchored alignment: {len(untrusted_ids)} -> {untrusted_ids}")


if __name__ == "__main__":
    main()
