# [PRODUCTION] Standing check: for every Part-1 klal boundary with a known
# real marker position (gematria_trace_part1.json), does the klal's OWN
# stored clean_text actually open with the real docai text at that
# position, does any real content anywhere in the span go completely
# uncaptured, and does the same real-span content end up double-assigned to
# two+ klal_ids?
#
# CORRECTION 2026-08-11 (see PROJECT-STATUS.md "klal 5 cross-page
# truncation"): this docstring used to claim Pass 1/2 already covered "every
# token in the span," which was never true - both were windowed to a span's
# OPENING (OPEN_WINDOW=50 / CHUNK_WORDS=15) and neither ever looked at a
# span's middle or end. Verified empirically: ran this script against the
# pre-fix corpus (klal 5's stored text was missing 65 real words at the very
# END of its span) and it reported nothing for klal 5 at all, in either
# pass - confirming this exact blind spot. Pass 3 below is the fix: a
# full-sequence alignment, not a windowed one.
#
# Built 2026-08-06 after the klal 186/187 swap: klal_id 186 in part1.json
# held klal 187's real content verbatim (its stored clean_text opened with
# the real text starting at klal 187's own marker, not klal 186's), while
# klal 186's own real content - a short, distinct span between klal 185's
# real end and klal 187's real marker - was never stored under ANY klal_id
# at all. gematria_trace_part1.json's own marker_position (316) for klal
# 186 already contradicted the stored content (which actually started at
# token 340) via a `content_match_ratio: 0.25` flag - the data needed to
# catch this already existed, it was just never cross-referenced against
# the corpus content. This script automates that cross-reference so a
# similar swap doesn't sit unnoticed again.
#
# validate_klal_span_coverage.py catches TRUNCATION (stored text too short
# for its real span) via an aggregate word-count ratio. It would NOT catch
# a same-length SWAP like 186/187, because the aggregate length can look
# perfectly reasonable when the wrong content of roughly the right size
# gets attached to the wrong klal_id. This script checks POSITION/CONTENT
# instead of just length: does klal N's stored text actually start with
# klal N's real opening tokens?
#
# Scope: Part 1 only (requires docai_word_boxes/ + gematria_trace_part1.json,
# neither of which exists for Parts 2-3 yet - see PROJECT-STATUS.md Open
# Items). Only checks klal pairs where BOTH ends have a known marker
# position ('ok' or 'marker_found_content_mismatch' status in the trace -
# both carry a real, usable position per CLAUDE.md's established
# convention; 'marker_not_found_in_window' does not and is skipped).
import difflib
import json
import os
import re

REPO = os.path.dirname(os.path.abspath(__file__))
DOCAI_DIR = os.path.join(REPO, "docai_word_boxes")
OPEN_WINDOW = 50  # words compared for the "does it open correctly" check
CHUNK_WORDS = 15  # length of a substring chunk used for the double-assignment scan
GAP_MIN_WORDS = 8  # min length of an unmatched real-token run to report as a likely gap (Pass 3)
# word_seq_similarity() cut-off, used in both directions: below it, a klal's
# stored text is reported as NOT opening with its own real marker-position
# text; above it, another klal is reported as the real owner of that text.
# Named 2026-08-15 - it was the bare literal 0.5 in three places, one of which
# was the printed message "word-sequence similarity < 0.5", so changing the
# threshold would have left the script reporting a number it no longer used.
# No derivation on record: it is a triage cut-off, not a calibrated one (the
# only live mismatch, klal 34, scores 0.32 against itself and 0.09 against its
# best other candidate, so nothing currently sits near the boundary).
MISMATCH_SIMILARITY = 0.5

# Pass 3 known false positives, investigated 2026-08-12 (PROJECT-STATUS.md):
#   klal 4  - the flagged span is klal 3's OWN trailing content (already
#     correctly stored under klal 3), sitting out of Y-reading-order in
#     docai's raw array right after klal 4's marker token - the same
#     array-order-vs-Y-order anomaly already documented in
#     gematria_trace_part1.json's klal-4 entry. Pass 3 computes "real span"
#     by array-order slicing, which has no way to know this.
#   klal 18 - same anomaly class: the flagged span is already correctly
#     stored under klal 17's tail (a citation-collision "יח" mid-sentence,
#     not a real marker skip); klal 18's true marker sits beside its own
#     bold opening word "אמוראים", confirmed by y-coordinate proximity.
#   klal 34 - NOT a missing-content case at all: docai's raw OCR is itself
#     heavily garbled at this klal's opening (already documented - marker
#     misread ל ו/ד, several nearby words independently garbled). The
#     stored text is the already crop-verified CORRECT reading, which
#     naturally diverges from Pass 3's raw-token comparison.
# Real, confirmed genuine gaps found via this same pass (klal 69, 206, 217)
# were fixed directly in part1.json rather than allowlisted here - see
# PROJECT-STATUS.md "Full-span gap scan" fixes, 2026-08-12.
#
# Page furniture that appears in raw docai tokens but never in clean_text:
# the printed folio number + running header ("<num> יד/יר/יך מלאכי כללי X"),
# the Google Books scan watermark, and printer's catchwords/signature digits
# at a page bottom. Stripped before comparison so a page-crossing real span
# isn't penalized for containing text that was NEVER meant to be in
# clean_text in the first place (a real span check, not a furniture check -
# see validate_klal_span_coverage.py's docstring for the same furniture,
# established across many fixes this project).
FURNITURE_WORDS = {"יד", "יר", "יך", "מלאכי", "כללי", "Digitized", "by", "Google"}
SECTION_WORDS = {"האלף", "הבית", "הגימל", "הדלת", "ההא"}


def normalize(text):
    return re.sub(r"[^א-ת]", "", text)


# FIXED 2026-08-14 (PROJECT-STATUS.md audit item 4): this used to be a bare
# {4, 18, 34} klal_id set, which suppresses EVERY Pass-3 hit for those
# klal_ids, not just the one specific span actually investigated above (see
# the investigation notes that used to sit here, now in git history/
# PROJECT-STATUS-HISTORY.md). A genuinely new, different gap appearing
# later in klal 4/18/34 (a future docai/part1.json edit, a trace-data fix)
# would be silently swallowed without ever surfacing, since nothing checked
# it was the SAME gap that was cleared. Re-ran Pass 3 against the current
# corpus (2026-08-14): confirmed each of the 3 klalim still produces
# exactly one hit, matching the spans below - no second, uninvestigated gap
# is being hidden right now. But the mechanism itself couldn't have told us
# that; now it can. Keyed on (klal_id, normalized span text) instead of
# klal_id alone, so only the exact investigated span is suppressed -
# anything else in these klalim surfaces as a normal, real hit.
#   klal 4  - klal 3's own trailing content, out of Y-reading-order in
#     docai's raw array right after klal 4's marker token.
#   klal 18 - klal 17's own tail (a citation-collision "יח" mid-sentence,
#     not a real marker skip).
#   klal 34 - docai's raw OCR is itself heavily garbled at this klal's
#     opening; the stored text is the already crop-verified correct
#     reading, which naturally diverges from Pass 3's raw-token comparison.
PASS3_KNOWN_FALSE_POSITIVES = {
    (4, normalize("ואפ\"ה חשיב ליה שם בזבחים למד מלמד והניח הדבר בתימה וגדולה היא אלי וצ\"ע :")),
    (18, normalize("בסתם ולא שת לבו שהם דחויים מעיקרא :")),
    (34, normalize("אין מישורון גזירה אמות מעצמו אלאס איל קבלה מרבוא האמלדון למכתברר שלא מבסין")),
}


def is_known_pass3_false_positive(klal_id, missing_words):
    """Is this exact gap the one already investigated and cleared for this
    klal? Extracted from main()'s Pass-3 loop 2026-08-14 so the suppression
    rule itself is directly testable (tests/test_pipeline_logic.py) - the
    whole point of the (klal_id, span) key is that a DIFFERENT gap in the
    same klal must still surface, and nothing could check that while the
    rule lived inline in a loop over real scan data."""
    return (klal_id, normalize("".join(missing_words))) in PASS3_KNOWN_FALSE_POSITIVES


def strip_furniture(words):
    return [w for w in words if w not in FURNITURE_WORDS and w not in SECTION_WORDS
            and not re.fullmatch(r"\d+", w)]


def word_seq_similarity(real_words, stored_words):
    """difflib.SequenceMatcher over WORD sequences (not a character blob,
    not strict positional equality). Word-sequence alignment tolerates the
    small insertions/deletions that are expected and harmless (an editorial
    `[.]` mark present in stored text but not in raw tokens, a stray
    OCR/editorial word here and there) while still correctly penalizing
    genuinely wrong content, because a wrong klal's text won't align for
    more than its first few (shared-refrain) words before the two sequences
    diverge for good. A character-blob ratio was tried first and rejected
    2026-08-06: it scored klal 186-vs-187's swapped content at 0.68 (comfortably
    "matching") purely because both openings share the 4-word template
    'קפו הלכה כדברי המקיל', which dominates a short comparison window
    regardless of what follows. A strict per-position word check was tried
    second and also rejected: it false-flagged ~30% of the whole corpus,
    because ANY single inserted/dropped word (a stripped `[.]`, an
    unstripped furniture token) permanently shifts every position after it,
    even in an otherwise-correct match. Sequence alignment (LCS-based, via
    difflib) doesn't have either problem.
    """
    rw = [normalize(w) for w in real_words[:OPEN_WINDOW] if normalize(w)]
    sw = [normalize(w) for w in stored_words[:OPEN_WINDOW] if normalize(w)]
    if not rw or not sw:
        return 0.0
    return difflib.SequenceMatcher(None, rw, sw).ratio()


def load_json(path):
    return json.load(open(path, encoding="utf-8"))


def get_page(cache, page):
    if page not in cache:
        path = os.path.join(DOCAI_DIR, f"page_{page}.json")
        cache[page] = load_json(path) if os.path.exists(path) else None
    return cache[page]


def real_span_tokens(cache, x, nx):
    """Real docai token span from klal x's marker to klal nx's marker,
    across any number of intervening pages, with page furniture stripped so
    it's comparable to clean_text.

    FIXED 2026-08-12 (PROJECT-STATUS.md finding 5, second audit round): this
    used to hard-stop at `next_page == page + 1` and return None for any
    wider gap, with the caller silently `continue`-ing past the None with no
    accounting - so this check simply never ran on klal 30->31, 75->76,
    88->89, 159->160, 167->168, 169->170, 197->199, all real 2-page gaps
    (one full intervening page with no klal marker of its own). Those
    include exactly the three multi-page reconstructions (klal 30/75/88)
    with the least other independent verification in the corpus - the
    highest-value place for this check to actually run. Generalized to walk
    every intervening page rather than special-casing one extra page, so a
    3+ page gap (none currently exist, but nothing here assumes otherwise)
    is handled the same way instead of hitting the same wall again."""
    page, next_page = x["page"], nx["page"]
    tokens_this = get_page(cache, page)
    if tokens_this is None:
        return None
    if next_page < page:
        return None  # not expected to occur; guard rather than misbehave
    if next_page == page:
        words = [t["text"] for t in tokens_this[x["marker_position"]:nx["marker_position"]]]
    else:
        words = [t["text"] for t in tokens_this[x["marker_position"]:]]
        for mid_page in range(page + 1, next_page):
            tokens_mid = get_page(cache, mid_page)
            if tokens_mid is None:
                return None
            words += [t["text"] for t in tokens_mid]
        tokens_next = get_page(cache, next_page)
        if tokens_next is None:
            return None
        words += [t["text"] for t in tokens_next[:nx["marker_position"]]]
    return strip_furniture(words)


def best_match_owner(real_words, part1, self_kid):
    """Which klal_id (if any) does this klal's real opening text actually
    appear to belong to, using the same word-sequence check against every
    other klal's stored opening?

    FIXED 2026-08-14: `self_kid` was accepted and never used, so the scan
    included the klal we already know mismatches - making the answer able to
    come back as the klal itself, which says nothing. Live on the only
    current mismatch: klal 34 reported "not found at the start of any klal's
    stored clean_text (best guess klal_id 34)", i.e. it named the very klal
    under investigation as the best candidate owner of its own missing text.
    Excluding self is what the docstring always described and is the only
    reading that answers the question being asked (is this text sitting
    under a DIFFERENT klal_id?)."""
    best_kid, best_sim = None, 0.0
    for other_kid, k in part1.items():
        if other_kid == self_kid:
            continue
        sim = word_seq_similarity(real_words, k["clean_text"].split())
        if sim > best_sim:
            best_kid, best_sim = other_kid, sim
    return best_kid, best_sim


def main():
    trace = {x["klal_id"]: x for x in load_json(os.path.join(REPO, "gematria_trace_part1.json"))
              if x.get("marker_position") is not None}
    part1 = {k["klal_id"]: k for k in load_json(os.path.join(REPO, "part1.json"))}
    ids = sorted(trace)
    cache = {}

    # --- Pass 1: opening-content check per klal ---
    # Deliberately pairs with the NEXT AVAILABLE trace entry, not literally
    # kid+1 - klalim with no known marker position get skipped over, which
    # means the computed "real span" for the klal just before a gap silently
    # extends across it. (CORRECTED 2026-08-14: this used to name "the 5
    # still-open 'no text available' placeholders: 187, 190, 197, 216, 217".
    # Both halves are stale - there are no "(no text available)" placeholders
    # left at all, tests/test_corpus_invariants.py's CONFIRMED_NUMBERING_GAPS
    # is now empty, and the klalim actually lacking a marker_position are a
    # different, larger set of 14: 10, 16, 22, 37, 47, 50, 57, 63, 67, 84,
    # 87, 129, 190, 198. Deliberately not re-listing them inline - the list
    # is data that moves; read it off gematria_trace_part1.json.) That's fine
    # for THIS check (it still
    # correctly captures kid's own real opening tokens, which is all the
    # word-position comparison needs) but means it does NOT by itself locate
    # what's inside the gap - see the per-mismatch owner lookup below for that.
    mismatches = []
    spans = {}  # kid -> real_tokens (for pass 2)
    adjacent_spans = {}  # kid -> real_tokens, ONLY where next_kid == kid+1 (for pass 3 - see below)
    # FIXED 2026-08-12 (PROJECT-STATUS.md finding 5): both `continue`s below
    # used to drop a pair with no record of having done so - the printed
    # "Checked N" count silently didn't sum to len(ids)-1, the same shape as
    # validate_klal_span_coverage.py's silent-drop bug (round 1 of this
    # audit). Now every pair lands in exactly one bucket - spans (checked)
    # or skipped (with a reason) - and main() asserts they sum correctly.
    skipped = []  # (kid, next_kid, reason)
    for idx, kid in enumerate(ids):
        if idx + 1 >= len(ids):
            continue
        next_kid = ids[idx + 1]
        real_tokens = real_span_tokens(cache, trace[kid], trace[next_kid])
        if kid not in part1:
            skipped.append((kid, next_kid, "klal_id not in part1.json"))
            continue
        if real_tokens is None:
            skipped.append((kid, next_kid, "docai page data unavailable for this span"))
            continue
        if next_kid == kid + 1:
            adjacent_spans[kid] = real_tokens
        spans[kid] = real_tokens
        sim = word_seq_similarity(real_tokens, part1[kid]["clean_text"].split())
        if sim < MISMATCH_SIMILARITY:
            mismatches.append((kid, next_kid, sim))

    total_pairs = max(len(ids) - 1, 0)
    assert len(spans) + len(skipped) == total_pairs, (
        f"!! ACCOUNTING ERROR: {len(spans)} checked + {len(skipped)} skipped "
        f"!= {total_pairs} total pairs - a pair fell through uncounted.")
    print(f"Checked {len(spans)} klal spans with known real positions on both ends.")
    if skipped:
        print(f"Skipped {len(skipped)} pair(s) (not silently dropped - see reason):")
        for kid, next_kid, reason in skipped:
            print(f"  klal {kid} -> {next_kid}: {reason}")
    print(f"\n{len(mismatches)} klal(im) whose stored clean_text does NOT open with its own real "
          f"marker-position text (word-sequence similarity < {MISMATCH_SIMILARITY}):")
    for kid, next_kid, sim in mismatches:
        real_open_preview = " ".join(spans[kid][:OPEN_WINDOW])
        print(f"  klal {kid} (real span ends at klal {next_kid}'s marker): "
              f"similarity {sim:.2f}")
        print(f"    real opening tokens : {real_open_preview}")
        print(f"    stored clean_text   : {' '.join(part1[kid]['clean_text'].split()[:OPEN_WINDOW])}")

        owner, owner_sim = best_match_owner(spans[kid], part1, kid)
        if owner_sim > MISMATCH_SIMILARITY:
            print(f"    -> its real opening text is currently stored under klal_id {owner} (similarity {owner_sim:.2f})")
        else:
            print(f"    -> its real opening text was NOT found at the start of any klal's "
                  f"stored clean_text (best guess klal_id {owner}, only {owner_sim:.2f} similarity - "
                  f"likely orphaned, not just misassigned)")

    # --- Pass 2: double-assignment scan - does the same real-span content chunk
    # appear (near-verbatim) inside more than one klal's stored clean_text?
    # KNOWN BLIND SPOT (2026-08-10, second audit round, not yet fixed): the
    # exact-normalized-substring match this relies on measured 43 of 197
    # spans (21.8%) matching NOTHING at all, including their own correct
    # owner - structurally blind exactly where docai is garbled (the same
    # shape as Lesson 15). "None found" below means "no double-assignment
    # detected in the spans this technique could match," not "verified
    # clean" - do not read a clean run here as full coverage. ---
    print(f"\n--- Double-assignment scan (same real content appearing under 2+ klal_ids) ---")
    all_text_norm = {kid: normalize(k["clean_text"]) for kid, k in part1.items()}
    double_hits = []
    for kid, real_tokens in spans.items():
        words = real_tokens
        if len(words) < CHUNK_WORDS:
            continue
        chunk = normalize("".join(words[:CHUNK_WORDS]))
        owners = [other_kid for other_kid, txt in all_text_norm.items() if chunk and chunk in txt]
        if len(owners) > 1:
            double_hits.append((kid, owners))
    if double_hits:
        for kid, owners in double_hits:
            print(f"  klal {kid}'s real opening chunk appears under klal_id(s): {owners}")
    else:
        print("  None found.")

    # --- Pass 3: full-span gap scan - does ANY contiguous run of real span
    # tokens (not just the opening) have no counterpart anywhere in the
    # klal's stored clean_text? Full-sequence alignment (autojunk=False -
    # see PROJECT-STATUS.md standing caution on this exact SequenceMatcher
    # default causing false "no match" results elsewhere), not windowed to
    # the opening like Pass 1/2 - this is what actually catches a truncated
    # TAIL like klal 5's, which both passes above are structurally blind to.
    #
    # Deliberately uses adjacent_spans, NOT spans: `spans[kid]`'s real range
    # extends to the NEXT AVAILABLE trace entry (see Pass 1's own comment
    # above), which silently aggregates a skipped markerless klal's content
    # into kid's own span whenever one sits in between. Comparing that
    # aggregate against kid's OWN clean_text alone then reports the
    # in-between klal's entire rightful content as a "gap" - a real false
    # positive, confirmed empirically 2026-08-11: before this filter, this
    # pass reported 20+ klalim with gaps of 30-600 words, and every single
    # large one lined up exactly with a skipped markerless klal (9, 15, 21,
    # 36, 46, 49, 56, 62, 66, 83, 86, 128, 179, 181, 189, 193, 197). Only
    # kid/next_kid pairs that are truly adjacent (no skip) give an
    # unambiguous single-klal span to check. ---
    print(f"\n--- Full-span gap scan (real content missing anywhere in the span, not just the opening) ---")
    gap_hits, known_fp_hits = [], []
    for kid, real_tokens in adjacent_spans.items():
        stored_words = part1[kid]["clean_text"].split()
        rw = [normalize(w) for w in real_tokens]
        sw = [normalize(w) for w in stored_words]
        sm = difflib.SequenceMatcher(None, rw, sw, autojunk=False)
        for tag, i1, i2, _j1, _j2 in sm.get_opcodes():
            if tag in ("delete", "replace") and (i2 - i1) >= GAP_MIN_WORDS:
                missing = real_tokens[i1:i2]
                (known_fp_hits if is_known_pass3_false_positive(kid, missing) else gap_hits).append(
                    (kid, missing))
    if gap_hits:
        for kid, missing in gap_hits:
            preview = " ".join(missing[:GAP_MIN_WORDS * 3])
            print(f"  klal {kid}: {len(missing)} real word(s) with no counterpart in stored text: {preview}...")
    else:
        print("  None found.")
    if known_fp_hits:
        print(f"  ({len(known_fp_hits)} known false positive(s) suppressed - "
              f"klal {sorted({k for k, _ in known_fp_hits})}, see PASS3_KNOWN_FALSE_POSITIVES)")


if __name__ == "__main__":
    main()
