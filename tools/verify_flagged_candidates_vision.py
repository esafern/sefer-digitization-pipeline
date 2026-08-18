# [PRODUCTION] Vision-adjudicates the 168 word-level candidates from the two
# 2026-08-16 batches that flagged klalim via free-text `klal_flag` notes
# (`ai-semantic-spotcheck-round2`, 85 candidates across 32 klalim; `ai-real-
# word-substitution`, 83 candidates across 49 klalim) rather than through
# `build_corrections_dataset.py`'s DocAI-vs-stored-text pipeline. That's
# exactly why they need their own script: neither batch has a bounding box
# the normal machinery already computed (that machinery only runs on DocAI/
# stored DISAGREEMENTS, and both of these detectors exist specifically
# because docai and clean_text AGREE on the same wrong reading at these
# positions - see PROJECT-STATUS.md's "SECOND FINDING" on lexicon-invisible
# corruption), and neither is in the structured `corrections_candidates_
# part1.json` schema the dashboard's candidate panel reads.
#
# Reuses `pipeline/verify_corrections_vision.py`'s crop/adjudicate/cache
# machinery directly (crop_pdf_bounding_box, adjudicate, get_cached_decision/
# cache_decision, init_cache) rather than reimplementing it - those functions
# are already generic over (page, bbox) / (option_a, option_b, context) and
# carry the project's established cache-key discipline (crop_hash + word_a +
# word_b + context_hash + prompt_hash - see CLAUDE.md Lesson 12). This script
# adds only what's specific to THIS batch: parsing candidates out of free-text
# notes, and locating each one's bounding box (neither of which the normal
# pipeline needs, since it starts from a DocAI token that already has one).
#
# Word locator: within the klal's own page region (`klal_page_regions.json`,
# built independently of any correction candidate and covering all 222 Part-1
# klalim), search for a DocAI token whose text exactly matches the word
# CURRENTLY in part1.json at that position - reliable because, as above, docai
# and clean_text already agree at these exact positions. Disambiguates by
# proportional read-order position when the same text recurs in one klal.
#
# READ-ONLY except for the shared adjudication_cache.db (grows the cache
# table other scripts already write to) and a JSON report file. Writes
# nothing to `part1.json` or `review_decisions.jsonl` directly - per CLAUDE.md
# "Human review decisions", a vision opinion informs a reviewer, it doesn't
# become a correction by itself. Run with --dry-run to test candidate
# parsing/locating/cropping with zero API calls; drop --dry-run to actually
# call Gemini (costs real API budget - the whole point of the flag).
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pipeline"))
import corpus_io as cio  # noqa: E402
import verify_corrections_vision as vcv  # noqa: E402

REPO = cio.REPO
PART1_PATH = cio.PART1_PATH
DECISIONS_PATH = os.path.join(REPO, "review_decisions.jsonl")
REGIONS_PATH = os.path.join(REPO, "klal_page_regions.json")
DOCAI_DIR = cio.DOCAI_DIR
REPORT_PATH = os.path.join(REPO, "flagged_candidates_vision_report.json")

TARGET_REVIEWERS = {"ai-semantic-spotcheck-round2", "ai-real-word-substitution"}

# --- 1. Candidate extraction from free-text klal_flag notes -----------------


def _quoted(qname, wname):
    # Tolerates an embedded gershayim/geresh (this corpus's own abbreviation
    # mark, e.g. ר"ס) inside the quoted word: a quote character followed by a
    # Hebrew letter is treated as PART of the word, not the closing
    # delimiter - only a quote NOT followed by a Hebrew letter closes it. The
    # closing delimiter must be the SAME quote character as the opener
    # (backreference) - candidates mix single/double quotes freely, and an
    # earlier draft that accepted either character for the close silently
    # truncated any word ending in a geresh right before its own closing
    # quote (e.g. "הנז'" - dropped the final "'" as if IT were the closer).
    return rf'''(?P<{qname}>["'])(?P<{wname}>(?:[^"']|["'](?=[א-ת]))*)(?P={qname})'''


_RW_PAT = re.compile(r"w(?P<idx>\d+)\s*" + _quoted("q1a", "a") + r"\s*->\s*" + _quoted("q1b", "b"))
_SC_PAT = re.compile(
    r"w(?P<idx>[\d\-]+)(?:\s+and\s+w[\d\-]+)?\s+" + _quoted("q2a", "a")
    + r"\s*->\s*(?:plausibly\s+)?" + _quoted("q2b", "b")
)

# Candidates the regex parser cannot recover cleanly (each checked by hand
# against its source note - see the note's own klal_id for full context).
# klal 101 (title-field, no body word_index) and klal 212 (a MISSING token,
# not a substitution pair) are deliberately excluded here - neither fits the
# option-A-vs-option-B crop comparison this script runs; both need their own
# one-off look, not this pipeline.
MANUAL_OVERRIDES = [
    (4, 131, "הנזי", "הנז'"),
    (12, 219, "אי", "א'"),
    (25, 779, "הגמי", "הגמ'"),
    (76, 6, "סי'", "פי'"),
    (88, 622, "מהי", "מה'"),
    (88, 963, "ומתי'", "ומתיר"),
    (140, 84, "עי", "ע'"),
    (161, 105, "בס'", "בפ'"),
    (176, 29, "כפ'", "בפ'"),
]

# klal 30 w1206 'וטכל' is explicitly recorded as AMBIGUOUS between two
# candidates with neither dominant - both get vision-checked, not just one.
AMBIGUOUS_OVERRIDES = [
    (30, 1206, "וטכל", "ומכל"),
    (30, 1206, "וטכל", "וטבל"),
]

# The two compound "wX and wY" mentions where the SAME candidate pair is
# named at a second position in the same klal - the regex above only
# captures the first index (by design, so it doesn't also swallow an
# unrelated "wN and wM" appearing later in the reasoning prose, which
# happens in klal 128/176's notes). Both real positions are checked.
SECOND_POSITION_OVERRIDES = [
    (7, 464, "דאס", "דאם"),  # w262 already covered by the regex parse
    (88, 778, "וכאבל", "ובאבל"),  # w2 already covered by the regex parse
]


def _unescape(word):
    # Several notes were composed with a literal backslash before an
    # embedded gershayim/double-quote (e.g. the stored text is literally
    # `ר\"ס`, not `ר"ס`) - an artifact of how the note prose was written,
    # not real corpus content. No real word in this corpus contains a
    # backslash, so stripping it unconditionally is safe.
    return word.replace("\\", "")


def parse_real_word_sub(note, klal_id):
    m = re.search(r"Candidates in this klal:\s*(.+)$", note, re.DOTALL)
    if not m:
        return []
    out = []
    for part in re.split(r";\s*(?=w\d)", m.group(1)):
        part = part.strip()
        if "AMBIGUOUS" in part:
            continue  # handled via AMBIGUOUS_OVERRIDES
        cm = _RW_PAT.search(part)
        if cm:
            out.append((klal_id, int(cm.group("idx")), _unescape(cm.group("a")), _unescape(cm.group("b"))))
    return out


def parse_semantic_spotcheck2(note, klal_id):
    m = re.search(r"Candidates:\s*(.+?)(?:\s*\|\|\s*OVERLAP:|$)", note, re.DOTALL)
    if not m:
        return []
    out = []
    for part in m.group(1).split("|"):
        part = part.strip()
        if not part or not re.match(r"^w[\d\-]", part):
            continue
        cm = _SC_PAT.search(part)
        if cm:
            idx = cm.group("idx").split("-")[0]  # "180-181" -> use the first
            out.append((klal_id, int(idx), _unescape(cm.group("a")), _unescape(cm.group("b"))))
    return out


def load_flagged_candidates(decisions_path=None):
    """Returns a list of dicts: klal_id, word_index, original, candidate,
    reviewer, decision_id - one per (position, hypothesis) pair."""
    decisions_path = decisions_path or DECISIONS_PATH
    out = []
    seen = set()
    for line in open(decisions_path, encoding="utf-8"):
        d = json.loads(line)
        if d.get("decision_type") != "klal_flag" or d.get("reviewer") not in TARGET_REVIEWERS:
            continue
        parser = (parse_real_word_sub if d["reviewer"] == "ai-real-word-substitution"
                  else parse_semantic_spotcheck2)
        for klal_id, word_index, original, candidate in parser(d["note"], d["klal_id"]):
            key = (klal_id, word_index, original, candidate)
            if key in seen:
                continue
            seen.add(key)
            out.append({"klal_id": klal_id, "word_index": word_index, "original": original,
                        "candidate": candidate, "reviewer": d["reviewer"], "decision_id": d["id"]})
    for klal_id, word_index, original, candidate in MANUAL_OVERRIDES + AMBIGUOUS_OVERRIDES + SECOND_POSITION_OVERRIDES:
        key = (klal_id, word_index, original, candidate)
        if key in seen:
            continue
        seen.add(key)
        out.append({"klal_id": klal_id, "word_index": word_index, "original": original,
                    "candidate": candidate, "reviewer": "manual-override", "decision_id": None})
    return out


# --- 2. Word locator: (klal_id, word_index, original text) -> (page, bbox) --


def load_regions():
    return cio.load_json(REGIONS_PATH)


def load_page_tokens(page):
    """[] (not None) for a missing page - locate_word() iterates the result
    directly. That divergence from the other eight copies of this loader is
    now an explicit argument rather than a difference you had to notice."""
    return cio.load_docai_page(page, DOCAI_DIR, default=[])


def locate_word(klal_id, word_index, original_text, regions, total_words_in_klal, token_cache):
    """Returns (page, bbox, ambiguous_count) or None if not found. bbox is
    the union of the matched token(s) if `original_text` is itself a
    multi-word span (none of this batch's candidates are, but kept general).

    Searches every page the klal's region covers, not just the first: 54 of
    Part 1's 222 klalim span a page break, recorded in `klal_page_regions.
    json` as a `continuations` list - a klal_page_regions.json bug the
    dashboard's own per-klal crop already knows to handle. Missing it here
    silently failed to locate every candidate whose word_index happened to
    fall on the continuation page (confirmed: klal 12 w237 - fixed by this,
    not a text-matching problem at all).

    FIXED (round-3 audit, 2026-08-16): when the same text matched on BOTH the
    primary page and a continuation page, an earlier draft tracked only the
    LAST page's token list for disambiguation - so every match from an
    earlier page compared against a rank list it didn't belong to, always
    lost (an unconditional 1e9 penalty), and the function silently always
    returned whichever page happened to be iterated last, regardless of
    which occurrence was actually closer to word_index. Confirmed on real
    data: klal 30 w1263/w250 'גכי' and klal 41 w256/w473 'כתכו' both match on
    two pages. Fixed by ranking every match on a single GLOBAL scale (each
    page's local reading-order rank offset by the running token count of the
    pages before it), the same running-offset technique
    locate_word_band_fallback() already uses for its own estimate."""
    region = regions.get(str(klal_id))
    if region is None:
        return None
    page_regions = [(region["page"], region["bbox"])]
    for cont in region.get("continuations", []):
        page_regions.append((cont["page"], cont["bbox"]))

    # (page, token, global_rank) for every match, across all pages.
    matches = []
    running_offset = 0
    for page, bbox in page_regions:
        if page not in token_cache:
            token_cache[page] = load_page_tokens(page)
        tokens = token_cache[page]
        pad = 0.006
        in_region = [t for t in tokens
                     if bbox["x1"] - pad <= t["x1"] and t["x2"] <= bbox["x2"] + pad
                     and bbox["y1"] - pad <= t["y1"] and t["y2"] <= bbox["y2"] + pad]
        in_region.sort(key=lambda t: (round(t["y1"], 3), -t["x1"]))
        found = [t for t in in_region if t["text"] == original_text]
        if not found and original_text.endswith(("'", '"')):
            # DocAI tokenizes a trailing geresh/gershayim as its OWN token
            # (confirmed: klal 76's "סי'" is two DocAI tokens, "סי" then "'"),
            # so a word ending in one never has a single token matching its
            # full text. Match the word minus its trailing mark instead.
            found = [t for t in in_region if t["text"] == original_text.rstrip("'\"")]
        for t in found:
            matches.append((page, t, running_offset + in_region.index(t)))
        running_offset += len(in_region)

    if not matches:
        return None
    if len(matches) == 1:
        page, token, _ = matches[0]
        return page, token, 1
    # Multiple identical-text tokens, possibly spanning a page break:
    # disambiguate by reading-order position (top-to-bottom, right-to-left
    # per line, continuation pages counted after the primary page) closest
    # to this word's proportional position among the klal's own words.
    expected_rank = (word_index / total_words_in_klal) * running_offset if total_words_in_klal else 0
    best_page, best_token, _ = min(matches, key=lambda m: abs(m[2] - expected_rank))
    return best_page, best_token, len(matches)


def locate_word_band_fallback(klal_id, word_index, regions, total_words_in_klal, token_cache):
    """For the minority of candidates locate_word() can't pin to an exact
    token (a multi-word original span like klal 4's 'כרבי שב"ג'; a klal
    whose klal_page_regions.json entry is itself short of tokens - klal 167
    claims 990 on one page for a 1369-word klal with no `continuations`
    listed, a real gap in that file worth its own look some day, not chased
    down here). Falls back to a coarser, wider crop: estimate the token's
    reading-order rank purely by word_index's proportion of the klal's total
    word count, then return a several-line BAND around that estimate rather
    than a single token - wide enough to tolerate the estimate being off by
    a few words, matching this project's own "generous crop, visible margin"
    precedent (CLAUDE.md Lesson 14) rather than a tight, precise guess."""
    region = regions.get(str(klal_id))
    if region is None:
        return None
    page_regions = [(region["page"], region["bbox"], region.get("token_count", 0))]
    for cont in region.get("continuations", []):
        page_regions.append((cont["page"], cont["bbox"], cont.get("token_count", 0)))

    total_tokens = sum(tc for _, _, tc in page_regions) or total_words_in_klal
    target_rank = (word_index / total_words_in_klal) * total_tokens if total_words_in_klal else 0

    running = 0
    for page, bbox, tc in page_regions:
        if target_rank <= running + tc or (page, bbox, tc) == page_regions[-1]:
            local_rank = target_rank - running
            if page not in token_cache:
                token_cache[page] = load_page_tokens(page)
            tokens = token_cache[page]
            pad = 0.006
            in_region = [t for t in tokens
                         if bbox["x1"] - pad <= t["x1"] and t["x2"] <= bbox["x2"] + pad
                         and bbox["y1"] - pad <= t["y1"] and t["y2"] <= bbox["y2"] + pad]
            if not in_region:
                return None
            # A band with zero Hebrew-letter tokens means the region itself
            # is wrong for this klal (confirmed: klal 167 claims 990 tokens
            # on one page for a 1369-word klal with no `continuations`
            # listed - a real gap in klal_page_regions.json - and the
            # estimated band for a late word_index lands past its real
            # content, in the page-footer "Digitized by Google" strip).
            # Report unlocated rather than hand back a crop of a footer.
            if not any(re.search(r"[א-ת]", t["text"]) for t in in_region):
                return None
            in_region.sort(key=lambda t: (round(t["y1"], 3), -t["x1"]))
            idx = max(0, min(len(in_region) - 1, round(local_rank)))
            center = in_region[idx]
            # Band: full region width, +/- 3 lines of estimated height around center.
            heights = [t["y2"] - t["y1"] for t in in_region]
            line_h = sorted(heights)[len(heights) // 2] if heights else 0.02
            band = {
                "x1": bbox["x1"], "x2": bbox["x2"],
                "y1": max(bbox["y1"], center["y1"] - 3 * line_h),
                "y2": min(bbox["y2"], center["y2"] + 3 * line_h),
            }
            return page, band, "band-estimate"
        running += tc
    return None


def context_for(klal_id, word_index, klalim_by_id, window=vcv.CONTEXT_WINDOW_WORDS):
    words = klalim_by_id[klal_id]["clean_text"].split()
    start = max(0, word_index - window)
    end = min(len(words), word_index + window + 1)
    return " ".join(words[start:end])


def build_client(api_key):
    """FIXED (round-4 audit, 2026-08-17): this used to be an inline
    `genai.Client(api_key=api_key)` call in main(), missing the explicit
    request-timeout fix (`http_options=types.HttpOptions(timeout=60000)`)
    that vcv (verify_corrections_vision.py) and verify_witness_vision.py
    both carry after a 2026-08-06 incident where a hung call blocked a run
    for 20+ minutes at zero CPU with no retry ever triggering - a second,
    independent instance of the exact drift class CLAUDE.md Lesson 13 /
    round 3's shared-module finding already documents once (the
    missing-prompt_hash cache-key bug). Pulled into its own function so the
    fix is directly testable rather than only reachable via a live API call
    from main()."""
    return vcv.vac.make_client(api_key)


def adjudicate_one(client, doc, klalim_by_id, c):
    """Crop, adjudicate, and parse a single located candidate, returning the
    result dict main() appends to `results`. Isolated per-candidate error
    handling: FIXED (round-4 audit) - this used to be inline in main()'s
    loop with no try/except at all, so a single candidate's total failure
    (a persistent 429 exhausting every retry, a malformed response even the
    lenient parser can't recover) crashed the whole batch and lost every
    already-adjudicated result accumulated so far, since `results` is only
    written to disk after the loop completes. Now caught here and recorded
    as an error entry, matching vcv.main()'s own established shape, so one
    bad candidate can't cost the rest of an already-paid-for run.

    Also FIXED: this used to call vcv.extract_json_fields() directly,
    skipping the strict-json.loads-first attempt every other caller of this
    parse chain gets (vcv.main()'s own loop, via vcv.parse_decision_text()).
    extract_json_fields's regex-based recovery doesn't handle a \\uXXXX
    escape (see its own docstring) - strict json.loads does - so a
    well-formed response using one would have been silently corrupted
    rather than parsed correctly. vcv.parse_decision_text() is used here
    instead, closing that gap.
    """
    try:
        crop_bytes = vcv.crop_pdf_bounding_box(doc, c["page"], c["bbox"], padding=0.03)
        context = context_for(c["klal_id"], c["word_index"], klalim_by_id)
        raw = vcv.adjudicate(client, crop_bytes, c["original"], c["candidate"], context)
        fields = vcv.parse_decision_text(raw)
        return {**c, "vision_raw": raw, "vision_fields": fields}
    except Exception as e:
        print(f"  !! failed: {e}")
        return {**c, "vision_raw": None, "vision_fields": None, "error": str(e)}


# --- 3. Driver ----------------------------------------------------------


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                     help="locate + crop only, no Gemini calls, no cache writes")
    ap.add_argument("--limit", type=int, default=None, help="process only the first N candidates")
    args = ap.parse_args()

    klalim = cio.load_part1(PART1_PATH)
    klalim_by_id = {k["klal_id"]: k for k in klalim}
    word_counts = {kid: len(k["clean_text"].split()) for kid, k in klalim_by_id.items()}
    regions = load_regions()

    candidates = load_flagged_candidates()
    print(f"Parsed {len(candidates)} candidate (position, hypothesis) pairs "
          f"from {len(TARGET_REVIEWERS)} reviewer batches.")
    if args.limit:
        candidates = candidates[:args.limit]

    token_cache = {}
    located, unlocated, ambiguous, band_estimated = [], [], [], []
    for c in candidates:
        total_words = word_counts.get(c["klal_id"], 0)
        result = locate_word(c["klal_id"], c["word_index"], c["original"], regions,
                              total_words, token_cache)
        if result is not None:
            page, token, match_count = result
            c["page"] = page
            c["bbox"] = {k: token[k] for k in ("x1", "y1", "x2", "y2")}
            c["locate_method"] = "exact-token"
            if match_count > 1:
                ambiguous.append(c)
            located.append(c)
            continue
        # Fall back to a coarser band estimate rather than dropping the
        # candidate entirely - see locate_word_band_fallback's docstring.
        band_result = locate_word_band_fallback(c["klal_id"], c["word_index"], regions,
                                                  total_words, token_cache)
        if band_result is None:
            unlocated.append(c)
            continue
        page, band, _ = band_result
        c["page"] = page
        c["bbox"] = band
        c["locate_method"] = "band-estimate"
        band_estimated.append(c)
        located.append(c)

    print(f"Located: {len(located)}/{len(candidates)} "
          f"({len(ambiguous)} disambiguated among multiple same-text matches, "
          f"{len(band_estimated)} via coarser band-estimate fallback)")
    if unlocated:
        print(f"NOT LOCATED AT ALL ({len(unlocated)}) - needs manual crop:")
        for c in unlocated:
            print(f"    klal {c['klal_id']} w{c['word_index']} {c['original']!r}")

    if args.dry_run:
        import fitz
        doc = fitz.open(vcv.PDF_PATH)
        crop_dir = os.path.join(REPO, "scratch", "flagged_candidate_crops_dryrun")
        os.makedirs(crop_dir, exist_ok=True)
        for i, c in enumerate(located[:5]):
            crop_bytes = vcv.crop_pdf_bounding_box(doc, c["page"], c["bbox"], padding=0.03)
            out_path = os.path.join(crop_dir, f"{c['klal_id']}_w{c['word_index']}.png")
            with open(out_path, "wb") as f:
                f.write(crop_bytes)
            print(f"  sample crop {i+1}/5 -> {out_path}")
        print(f"\nDRY RUN: {len(located)} candidates ready to adjudicate, "
              f"{len(unlocated)} need manual handling. No API calls made.")
        return

    import fitz
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("GEMINI_API_KEY not set")
    client = build_client(api_key)
    vcv.init_cache()
    doc = fitz.open(vcv.PDF_PATH)

    results = []
    for i, c in enumerate(located):
        print(f"[{i+1}/{len(located)}] klal {c['klal_id']} w{c['word_index']} "
              f"{c['original']!r} vs {c['candidate']!r}")
        results.append(adjudicate_one(client, doc, klalim_by_id, c))

    for c in unlocated:
        results.append({**c, "vision_raw": None, "vision_fields": None, "error": "not located"})

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nWrote {len(results)} results to {REPORT_PATH}")


if __name__ == "__main__":
    main()
