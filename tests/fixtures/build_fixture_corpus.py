#!/usr/bin/env python3
# [PRODUCTION] Turns fixture_book.py's data into a real, on-disk corpus
# directory - by RUNNING the real pipeline stages against it, not by writing
# their output by hand. Item 0AR: "the fixture corpus must be GENERATED, not
# written" (Lesson 13) - a hand-typed corrections_part1.json would be a second
# copy of something the real code derives, and would drift from what the real
# code actually does the day either one changes without the other.
#
# WHAT IS RUN FOR REAL (subprocesses, each with SEFER_CORPUS_ROOT pointed at
# the fixture directory - the seam item 0AZ built, used exactly as intended:
# resolved fresh at each subprocess's own import time, never reassigned mid-
# process):
#   build_klalim_demo_dataset.py, build_corrections_dataset.py,
#   assemble_corrections_dataset.py, build_klal_page_regions.py,
#   synthesize_multi_witness.py (best-effort - degrades to a no-op with no
#   witness baselines present, same as a fresh clone).
#
# WHAT IS INJECTED INSTEAD, and why each one specifically is not run for real:
#   - verify_corrections_vision.py is SKIPPED (costs a real Gemini call) -
#     `corrections_verified_part1.json` is built directly from the real
#     candidates, each annotated with a canned vision verdict in the exact
#     schema that stage produces. This is the same skip rebuild_all.sh's own
#     --skip-vision flag makes; the fixture just makes the substitution
#     explicit rather than optional.
#   - The two MACHINE-RESOLVED flags (`current_text_confirmed`,
#     `docai_ligature_artifact`) are injected into the assembled
#     corrections_part1.json. Assigning them for real requires this book's
#     OWN defect-classification heuristics (ligature-artifact detection is
#     Yad Malachi's Berlin-print-specific knowledge - see the generalization
#     plan's Phase 3) - reproducing that heuristic here would make the fixture
#     depend on the very thing Phase 3 is meant to extract. The review UI's
#     handling of the FLAG VALUE is what this fixture tests, not how a real
#     pipeline would arrive at it.
#   - The `possible_omission` at `len(words)` and the second `delete` opcode
#     at klal 3 word 1 are injected for the same reason as the flags: forcing
#     difflib's page-wide diff to land an extra token at an EXACT boundary
#     position, or two independent omissions at one shared index, is coercing
#     a heuristic rather than exercising it - Lesson 34's own citation of this
#     exact shape (two decisions colliding at one index) is a historical
#     accident, not a derivable one.
#   - Klal 1's CONTINUATION (page 1 -> 2) correction and its region's
#     `continuations` entry are both injected, discovered the hard way: a
#     first attempt let fixture_book.py's page-2 DocAI reading genuinely
#     differ at the continuation word, and the real pipeline never attributed
#     it to klal 1 at all (it came back as an "insert" - the whole 3-word span
#     "uncorroborated" - plus an "unattributable_delete" for page 2's actual
#     reading). The reason: klal_page_regions.json's continuation detection
#     (`marker_anchored_regions()`) works by Y-COORDINATE banding against a
#     page's real printed layout, and a bootstrap-pass re-ordering (running
#     the region builder once before the correction stage, to solve the
#     genuine cold-start gap noted below) does not fix that - a two-line
#     synthetic page simply has no realistic geometry for that heuristic to
#     find a continuation in. This is real, documented print-specific
#     complexity (the same class Phase 3 of the generalization plan targets),
#     not a shortfall in this generator.
#   - `reconstruction_witness_queue.json` and
#     `punctuation_candidates_part1.json` are written directly - both are
#     themselves the output of other paid-API-or-Tesseract passes that this
#     fixture has no reason to invoke.
#   - `review_decisions.jsonl` IS generated for real, through
#     `review_decisions.append_decision()` - an append-only ledger's natural
#     generation method is appending to it, so calling the real function is
#     the non-shortcut path here, not an exception to it.
#
# Run standalone for inspection: `python3 tests/fixtures/build_fixture_corpus.py /tmp/tryit`
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "pipeline"))
sys.path.insert(0, os.path.join(REPO, "tools"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import corpus_io as cio  # noqa: E402
import review_decisions as rd  # noqa: E402
import fixture_book as book  # noqa: E402

PIPELINE_DIR = os.path.join(REPO, "pipeline")


def _run_stage(script_name, root):
    """One pipeline stage, as a subprocess with SEFER_CORPUS_ROOT set BEFORE
    the interpreter starts - not after, and not via set_corpus_root() in this
    process. That distinction is item 0AZ's whole point: a fresh subprocess
    resolves corpus_io's lazy paths against the environment it is BORN with,
    which is the one case reassigning the root is actually safe."""
    env = dict(os.environ)
    env["SEFER_CORPUS_ROOT"] = root
    proc = subprocess.run(
        [sys.executable, os.path.join(PIPELINE_DIR, script_name)],
        cwd=root, env=env, capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"fixture generation: {script_name} failed (exit {proc.returncode})\n"
            f"--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}"
        )
    return proc.stdout


def _write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


def _write_docai_pages(root):
    """docai_word_boxes/page_N.json - fabricated directly. A real book's DocAI
    cache is externally-sourced input this pipeline reads, never something
    rebuild_all.sh itself produces (extraction needs a live GCP account), so
    writing it by hand here is the same relationship a real book has to it,
    not a shortcut around a derivable file."""
    docai_dir = os.path.join(root, "docai_word_boxes")
    os.makedirs(docai_dir, exist_ok=True)
    for page_num, words in ((1, book.PAGE1_DOCAI_WORDS), (2, book.PAGE2_DOCAI_WORDS)):
        tokens = []
        n = len(words)
        for i, w in enumerate(words):
            # Right-to-left layout: x DECREASES as reading-order index
            # increases, purely so a rendered screenshot looks plausible.
            # Nothing that reads this file cares about visual placement.
            x1 = 0.85 - (i / max(n, 1)) * 0.7
            y1 = 0.1 + (i // 6) * 0.08
            tokens.append({
                "text": w, "x1": round(x1, 4), "y1": round(y1, 4),
                "x2": round(x1 + 0.06, 4), "y2": round(y1 + 0.03, 4),
            })
        _write_json(os.path.join(docai_dir, f"page_{page_num}.json"), tokens)


def _write_alignment_and_trace(root):
    """part1_header_anchored_alignment.json + gematria_trace_part1.json.

    Hand-written rather than run through build_gematria_trace.py's own
    marker-search heuristic: that heuristic is exactly the kind of print-run-
    specific pattern matching (catchwords, running headers, OCR noise
    tolerance) the generalization plan's Phase 3 is about, and this fixture's
    four klalim have no real page furniture to search through. What matters
    for the tests this fixture serves is that the SHAPE is right and that
    downstream readers (trusted_klal_pages, build_klal_page_regions.py - run
    for REAL below) get a valid, minimal input.
    """
    alignment = [
        {"klal_id": k["klal_id"], "expected_section": book.SECTION,
         "matched_page": k["page"], "matched_page_header": book.SECTION,
         "match_ratio": 1.0, "trusted": True, "search_stage": 0,
         "jump_tokens": 0, "lexicon_hit_rate": 1.0}
        for k in book.KLALIM
    ]
    _write_json(os.path.join(root, "part1_header_anchored_alignment.json"), alignment)

    # marker_position = the klal's own opening word's index in that PAGE's
    # docai token list (0-based) - real build_klal_page_regions.py reads this
    # to anchor each klal's region.
    trace = [
        {"klal_id": 1, "page": 1, "marker_position": 0, "status": "ok"},
        {"klal_id": 2, "page": 2, "marker_position": 3, "status": "ok"},
        {"klal_id": 3, "page": 2, "marker_position": 9, "status": "ok"},
        {"klal_id": 4, "page": 2, "marker_position": 14, "status": "ok"},
    ]
    _write_json(os.path.join(root, "gematria_trace_part1.json"), trace)

    # build_klal_page_regions.py's main() unconditionally loads all THREE
    # parts' alignment/trace files (no part2/3.json content of ours needs
    # them - this fixture has no Part 2/3 - but the loader has no graceful
    # skip for an absent file: load_gematria_trace's default is None, and the
    # caller does `for e in trace` with no None-guard). Empty, valid files,
    # not a workaround: an empty part is exactly what a one-part book (this
    # fixture, or plausibly a first real book with no sequel volumes) IS.
    for part_num in (2, 3):
        _write_json(os.path.join(root, f"part{part_num}_header_anchored_alignment.json"), [])
        _write_json(os.path.join(root, f"gematria_trace_part{part_num}.json"), [])


def _write_pdf_and_page_images(root):
    """A tiny real PDF (via fitz) with the two pages' words actually drawn on
    it, plus the pre-rendered PNGs review_server serves from
    images/pdf_pages/. START_HERE.md is explicit that `images/pdf_pages/` has
    no live rendering script in the real pipeline either - it is a pre-built
    cache everywhere, including here."""
    import fitz  # PyMuPDF

    pdf_path = os.path.join(root, "fixture_scan.pdf")
    doc = fitz.open()
    for page_words in (book.PAGE1_DOCAI_WORDS, book.PAGE2_DOCAI_WORDS):
        page = doc.new_page(width=400, height=600)
        y = 40
        # Drawn left-to-right in blocks of a few words per line - legibility
        # of the PDF itself is not load-bearing for any test; only that a
        # page exists to render.
        for i in range(0, len(page_words), 6):
            page.insert_text((20, y), " ".join(page_words[i:i + 6]),
                             fontsize=14, fontname="helv")
            y += 24
    doc.save(pdf_path)

    images_dir = os.path.join(root, "images", "pdf_pages")
    os.makedirs(images_dir, exist_ok=True)
    for i, page in enumerate(doc, start=1):
        pix = page.get_pixmap(dpi=100)
        pix.save(os.path.join(images_dir, f"page_{i}.png"))
    doc.close()


def _fabricate_verified_from_candidates(root):
    """corrections_verified_part1.json - the ONE stage in this generator that
    stands in for a real, paid API call (verify_corrections_vision.py). Every
    candidate is carried through unchanged (`**c`) and given a canned,
    deterministic vision verdict under the exact field names that stage
    writes (`vision_selected`/`vision_transcription`/`vision_confidence`/
    `vision_reasoning` - assemble_corrections_dataset.py renames the last two
    to `confidence`/`reasoning` itself), as a FLAT LIST - the candidates file
    wraps its list in `{"corrections": [...], "meta": {...}}`, the verified
    file does not.
    """
    candidates = cio.load_json(os.path.join(root, "corrections_candidates_part1.json"), {})
    verified = []
    for c in candidates.get("corrections", []):
        verified.append({
            **c,
            "vision_selected": "A",  # "the docai/final_text reading is correct"
            "vision_transcription": c.get("corrected_word") or c.get("original_word") or "",
            "vision_confidence": 0.99,
            "vision_reasoning": "fixture: canned verdict, no vision call made",
        })
    _write_json(os.path.join(root, "corrections_verified_part1.json"), verified)


def _inject_special_corrections(root):
    """The conditions that need book-specific heuristics or a genuine
    historical coincidence to arise naturally - see this module's header for
    why each is injected rather than earned through the real diff/classifier.
    Applied AFTER assemble_corrections_dataset.py has run for real, so the
    one entry the real pipeline DID produce (klal 2's manual-decision replace)
    is exactly what it produced.
    """
    path = os.path.join(root, "corrections_part1.json")
    corrections = cio.load_json(path, {})

    # Klal 1: the continuation-page correction, REPLACING whatever the real
    # diff produced. Before the region builder's `continuations` entry exists
    # (injected two steps from now, after build_klal_page_regions.py's real
    # run), klal 1 is attributed to page 1 alone, so its whole page-2 span
    # comes back as an "insert" (uncorroborated) - see this module's header.
    # Leaving that stale entry alongside the clean injected one below would
    # show a reviewer two conflicting proposals for the same three words.
    # word_index 6 = "דלת", the second continuation word (index: 0 marker,
    # 1-4 page 1, 5-7 continuation).
    corrections["1"] = []
    corrections["1"].append({
        "word_index": 6, "opcode": "replace", "docai_reading": "דלד",
        "docai_repaired": None, "final_text": "דלת", "page": 2,
        "bbox": {"x1": 0.5111, "y1": 0.1, "x2": 0.5711, "y2": 0.13},
        "vision_selected": "A", "vision_transcription": "דלת", "confidence": 0.95,
        "reasoning": "fixture: injected continuation-page replace",
        # An ordinary open dispute, same flag the real pipeline gave klal 2's
        # own replace candidate - not None, which review_server.FLAG_LABELS
        # has no entry for (test_every_served_flag_has_a_dashboard_label
        # correctly rejects it: an unnamed flag renders as an uncoloured,
        # unlabelled "Flagged" word).
        "flag": "current_text_may_be_wrong",
    })

    # Klal 2: both MACHINE-RESOLVED flags. word_index 4/5 ("טית"/"יוד") are
    # not otherwise in dispute - these two entries exist purely to give the
    # review-counts logic a RESOLVED-state row to count, one of each flag
    # value review_counts.MACHINE_RESOLVED_FLAGS recognises.
    #
    # `docai_reading` DIFFERS from `final_text` on both, matching a real
    # `current_text_confirmed` row (checked against the real corpus while
    # building this: "current_text_confirmed" does NOT mean docai agrees with
    # the stored text - it means vision confirmed the STORED text is right
    # DESPITE docai/consensus disagreeing. A first version of this fixture had
    # docai_reading == final_text on both, which
    # test_no_corrections_item_attributes_the_stored_text_to_an_engine
    # correctly rejects: "an engine that was not consulted must read null,
    # never the corpus's own word" - docai WAS consulted here, and read
    # something else, which is the whole reason vision had to arbitrate.
    corrections.setdefault("2", []).extend([
        {"word_index": 4, "opcode": "replace", "docai_reading": "טיס",
         "docai_repaired": None, "final_text": "טית", "page": 2,
         "bbox": {"x1": 0.3, "y1": 0.18, "x2": 0.36, "y2": 0.21},
         "vision_selected": "B", "vision_transcription": "טית", "confidence": 0.99,
         "reasoning": "fixture: injected machine-resolved row",
         "flag": "current_text_confirmed"},
        {"word_index": 5, "opcode": "replace", "docai_reading": "יד",
         "docai_repaired": None, "final_text": "יוד", "page": 2,
         "bbox": {"x1": 0.24, "y1": 0.18, "x2": 0.3, "y2": 0.21},
         "vision_selected": "B", "vision_transcription": "יוד", "confidence": 0.99,
         "reasoning": "fixture: injected machine-resolved row",
         "flag": "docai_ligature_artifact"},
    ])

    # Klal 3: a `possible_omission` at len(words) (index 5 - one past "נון"
    # at index 4) - DocAI is imagined to have seen one more word, "סמך", that
    # the corpus never recorded.
    corrections.setdefault("3", []).append({
        "word_index": 5, "opcode": "delete", "docai_reading": "סמך",
        "docai_repaired": None, "final_text": None, "page": 2,
        "bbox": {"x1": 0.1, "y1": 0.34, "x2": 0.16, "y2": 0.37},
        "vision_selected": "A", "vision_transcription": "סמך", "confidence": 0.9,
        "reasoning": "fixture: injected end-of-klal omission",
        "flag": "possible_omission",
    })

    # Klal 3: TWO CANDIDATES colliding at ONE index (word_index 1, "כף") -
    # the sibling-collision shape Lesson 34 names directly (klal 66 w0, then
    # klal 69 w188: two decisions the SAME position can carry, discovered as
    # two separate bugs because two separate code branches handled it).
    #
    # ONE delete, one REPLACE - not two deletes. A first version of this
    # fixture used two `delete` opcodes, and
    # test_no_word_index_is_served_twice_in_either_pane correctly rejected it:
    # a gated invariant (item 0AU, added the SAME session as this generator)
    # now forbids two GAPS ever sharing a key, because the focus test that
    # disambiguates a click "genuinely cannot tell two gaps apart" (its own
    # words). That is real, current, and worth keeping intact - Lesson 34's
    # historical sibling collisions were never actually two `delete`s at one
    # index; they were a DECISION answering the wrong branch of one word's
    # dispute, which klal 3 word 3's answered-flag scenario above already
    # demonstrates (a klal_flag and a manual_correction, two ledger records,
    # one key). This pair demonstrates the CORRECTIONS-level version of the
    # same shape without tripping the invariant that specifically targets
    # two indistinguishable gaps.
    corrections.setdefault("3", []).extend([
        {"word_index": 1, "opcode": "delete", "docai_reading": "למ",
         "docai_repaired": None, "final_text": None, "page": 2,
         "bbox": {"x1": 0.5, "y1": 0.26, "x2": 0.56, "y2": 0.29},
         "vision_selected": "B", "vision_transcription": "למ", "confidence": 0.7,
         "reasoning": "fixture: injected candidate #1 at a shared index",
         "flag": "ambiguous"},
        {"word_index": 1, "opcode": "replace", "docai_reading": "מד",
         "docai_repaired": None, "final_text": "כף", "page": 2,
         "bbox": {"x1": 0.5, "y1": 0.26, "x2": 0.56, "y2": 0.29},
         "vision_selected": "NEITHER", "vision_transcription": "מד", "confidence": 0.6,
         "reasoning": "fixture: injected candidate #2 at the SAME shared index",
         "flag": "ambiguous"},
    ])

    _write_json(path, corrections)


def _inject_continuation_region(root):
    """klal_page_regions.json[1]["continuations"] - the other half of the
    injected continuation correction above, and the one that actually
    matters to the review UI: `trusted_klal_pages_with_continuations` (used
    by both build_corrections_dataset.py and review_server.py's own page-to-
    klal mapping) reads this field to know page 2 is PARTLY klal 1's. Without
    it, api_page(2) and pageForWord() would have no way to place klal 1's
    continuation words on the page they are actually on - which is precisely
    the bug item 0AS fixed for the real corpus, so this fixture would
    otherwise test the review UI's OWN regression without ever exercising it.
    """
    path = os.path.join(root, "klal_page_regions.json")
    regions = cio.load_json(path, {})
    regions["1"]["continuations"] = [{
        "page": 2,
        "bbox": {"x1": 0.36, "y1": 0.1, "x2": 0.85, "y2": 0.13},
        "token_count": 3,
    }]
    _write_json(path, regions)


def _write_witness_queue(root):
    """reconstruction_witness_queue.json - klal 4, one row WITH word_index,
    one row WITHOUT. Both carry `vision_selected` in
    WITNESS_PRIORITY_VERDICTS ("B"/"NEITHER") so review_server's own filter
    (WITNESS_QUEUE_FILTERED) actually serves them - a queue entry the filter
    drops would silently test nothing."""
    #
    # `docai_token_index` is PAGE-RELATIVE - an index into that page's own token
    # list, exactly as verify_reconstruction_witness.py produces it - not an
    # offset within the klal. Page 2's tokens are klal 1's 3 continuation words
    # (0-2), then klal 2's 6 (3-8), then klal 3's 5 (9-13), then klal 4's 4
    # (14-17), so klal 4's "עין"/"פא" are 16/17. The first version of this
    # fixture wrote 2/3 - klal-relative offsets, which resolve to "הא"/"ב" on the
    # real page - so any test reading api_witness_context here would have
    # inspected the wrong word while appearing to pass, hiding the very
    # page-vs-klal indexing bug class this fixture exists to catch. Found by the
    # 2026-09-03 ultra review.
    #
    # meta.stats is keyed by the SCAN PAGE, likewise matching the real generator.
    queue = {
        "meta": {"stats": {"2": {"klal_id": 4, "docai_words": 4,
                                  "tesseract_words": 4, "agreement": 0.5,
                                  "flagged": 2}}},
        "queue": [
            {"klal_id": 4, "page": 2, "docai_reading": "עין",
             "tesseract_reading": "עיו", "opcode": "replace", "tier": "D",
             "bbox": {"x1": 0.15, "y1": 0.42, "x2": 0.21, "y2": 0.45},
             "docai_token_index": 16, "vision_selected": "B",
             "vision_transcription": "עין", "vision_confidence": 0.9,
             "vision_reasoning": "fixture", "word_index": 2},
            {"klal_id": 4, "page": 2, "docai_reading": "פא",
             "tesseract_reading": "פה", "opcode": "replace", "tier": "D",
             "bbox": {"x1": 0.1, "y1": 0.42, "x2": 0.16, "y2": 0.45},
             "docai_token_index": 17, "vision_selected": "NEITHER",
             "vision_transcription": "פ", "vision_confidence": 0.6,
             "vision_reasoning": "fixture: no word_index - never aligned to a corpus word"},
        ],
    }
    _write_json(os.path.join(root, "reconstruction_witness_queue.json"), queue)


def _write_punctuation_candidates(root):
    # `before_word_index` is the index the mark is inserted BEFORE, i.e. the
    # index of `word_after` - verified against the real corpus (klal 1's entry at
    # 87 has words[87] == its own word_after). Klal 2's words are
    # [ב,וו,זין,חית,...], so a break between "זין" (2) and "חית" (3) is 3, not 2.
    # The first version wrote 2 and the smoke test asserted that same wrong value
    # back, so nothing caught it. Found by the 2026-09-03 ultra review.
    _write_json(os.path.join(root, "punctuation_candidates_part1.json"), {
        "2": [{"before_word_index": 3, "word_before": "זין", "word_after": "חית",
               "reasoning": "fixture: a proposed sentence break"}],
    })


def _write_review_decisions(root):
    """The ledger - generated by calling the REAL append_decision(), pointed
    at this fixture's own file via `path=` (the pre-existing
    REVIEW_DECISIONS_PATH seam, unrelated to corpus_io's root but serving the
    identical purpose for this one file)."""
    path = os.path.join(root, "review_decisions.jsonl")

    # A human decision (klal 2 word 3, "חית" -> "חתי" is what the real
    # diff pipeline ALSO proposed above - the same word, ruled by a person).
    rd.append_decision(
        "manual_correction", klal_id=2, word_index=3, chosen_source="custom",
        chosen_text="חית", candidate_snapshot={"word_index": 3, "original_word": "חית"},
        note="fixture: a human ruling", reviewer="local", path=path,
    )

    # An OPEN word-level ai_flag (klal 3 word 2, "למד") - no later decision
    # at this key, so it must still read as open.
    rd.append_decision(
        "klal_flag", klal_id=3, word_index=2, needs_revisit=True,
        note="fixture: an open word-level flag", reviewer="local", path=path,
    )

    # An ANSWERED flag standing alone (klal 3 word 3, "מם") - the flag, then
    # a later decision at the same key. Real, sequential timestamps matter
    # here (item 0AT: two logic tests were pinned on fixtures with NO
    # timestamps, and the ordering rule silently never fired) - both calls
    # stamp `now()` themselves, in order.
    rd.append_decision(
        "klal_flag", klal_id=3, word_index=3, needs_revisit=True,
        note="fixture: a flag that gets answered", reviewer="local", path=path,
    )
    rd.append_decision(
        "manual_correction", klal_id=3, word_index=3, chosen_source="custom",
        chosen_text="מם", candidate_snapshot={"word_index": 3, "original_word": "מם"},
        note="fixture: the answer to the flag above", reviewer="local", path=path,
    )


def build(root):
    """Build the fixture corpus into `root` (created if absent). Returns root."""
    os.makedirs(root, exist_ok=True)

    # book.json - the manifest (Phase 2). This fixture is a ONE-CHUNK book with
    # four klalim, which is the point: it exercises the declared-shape path
    # rather than inheriting Yad Malachi's three files and 667-klal range. Its
    # identity fields are here too, so /api/corpus names THIS book - until
    # 2026-09-04 the WORK_* constants were hardcoded and the fixture's own name
    # was dead code nothing could read (ultra review).
    _write_json(os.path.join(root, "book.json"), {
        "title": book.WORK_TITLE,
        "title_he": book.WORK_TITLE_HE,
        "section": book.SECTION,
        "section_he": book.SECTION_HE,
        "edition": "Synthetic fixture - no scan, no edition",
        "parts": [{"file": "part1.json", "first_klal": 1,
                   "last_klal": max(k["klal_id"] for k in book.KLALIM)}],
    })
    _write_json(os.path.join(root, "part1.json"), book.KLALIM)
    # part2/3 still written, EMPTY, because build_klal_page_regions.py loads all
    # three parts' alignment/trace files unconditionally (see below). They are
    # not declared in the manifest, so nothing treats them as chunks of this
    # book - the difference between "a file exists" and "the book has 3 parts".
    _write_json(os.path.join(root, "part2.json"), [])
    _write_json(os.path.join(root, "part3.json"), [])
    # build_corrections_dataset.py reads review_decisions.jsonl directly (to
    # drop candidates a decision already settled) via a hardcoded
    # `os.path.join(REPO, "review_decisions.jsonl")` - not through
    # review_decisions.DECISIONS_PATH's own $REVIEW_DECISIONS_PATH seam. Worth
    # a real finding (logged separately): the two seams can disagree if a
    # caller ever points them at different places. For this fixture it only
    # means the file must exist, empty, before that stage runs - the actual
    # decisions are appended for real at the end of this function.
    open(os.path.join(root, "review_decisions.jsonl"), "w", encoding="utf-8").close()

    _write_docai_pages(root)
    _write_alignment_and_trace(root)
    _write_pdf_and_page_images(root)

    _run_stage("build_klalim_demo_dataset.py", root)
    # BOOTSTRAP PASS. build_corrections_dataset.py resolves each klal's page
    # attribution through trusted_klal_pages_WITH_CONTINUATIONS, which reads
    # continuation info out of klal_page_regions.json - a file that does not
    # exist yet on a brand-new corpus. rebuild_all.sh never notices this on
    # the REAL corpus because that file is a tracked, already-built artifact
    # from every previous run; a fixture generated from nothing has no
    # previous run to inherit it from. This is a genuine cold-start gap in
    # the real pipeline's own stage order (2 depends on 5's PRIOR output),
    # not a fixture-only workaround - logged as a finding, not silently
    # routed around. Running the region builder once before the correction
    # stage, purely from alignment+trace+docai geometry (it reads no
    # correction data), reproduces what a SECOND real rebuild run would see;
    # it is run again below in the real stage order for the same reason
    # rebuild_all.sh always re-runs every stage rather than trusting staleness.
    _run_stage("build_klal_page_regions.py", root)
    _run_stage("build_corrections_dataset.py", root)
    _fabricate_verified_from_candidates(root)
    _run_stage("assemble_corrections_dataset.py", root)
    _inject_special_corrections(root)
    _run_stage("build_klal_page_regions.py", root)
    _inject_continuation_region(root)
    _run_stage("synthesize_multi_witness.py", root)  # best-effort; no baselines present

    _write_witness_queue(root)
    _write_punctuation_candidates(root)
    _write_review_decisions(root)

    return root


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "/tmp/fixture_sefer"
    build(target)
    print(f"Fixture corpus built at {target}")
