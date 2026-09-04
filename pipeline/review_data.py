# [PRODUCTION] Reading the review corpus and its derived queues, by part.
#
# EXTRACTED from pipeline/review_server.py 2026-09-01, CLOSING finding C4.
#
# scan_alignment.py took the geometry and freed the two rebuild stages; that
# left two tools still reaching into the HTTP server for its PRIVATE loaders -
# tools/validate_suppression_filters.py wanting _load_witness_queue() and
# tools/patch_witness_word_indices.py wanting _load_klalim(). Neither is
# geometry, so scan_alignment was never their answer, and PROJECT-STATUS item
# 0V recorded them as the honest remainder rather than calling C4 done.
#
# This is that remainder. Everything here answers "what does the corpus look
# like for part N" - the part-token vocabulary, the four per-part JSON readers,
# and the witness queue with its filtering rules. All of it is pure reading:
# no HTTP, no request state, no mutation.
#
# Part-token validation lives here rather than in the server because the two
# functions that consume it (parts_for and load_klalim) are both here, and
# they had already drifted once - parts_for accepted "none" and load_klalim did
# not, so the same query string got Parts 1+2+3 from one and Part 1 from the
# other (finding S4, fixed 2026-08-31). One vocabulary, one place.
#
# BadRequest is raised here and caught in review_server's do_GET, which turns
# it into a 400. That is the one deliberate seam left between the two modules:
# this module knows what a bad part token is, and only the server knows what an
# HTTP status code is.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import corpus_io as cio  # noqa: E402
import review_decisions as rd  # noqa: E402

# NOT copied into module constants. `PART1_MAX_KLAL = cio.PART1_MAX_KLAL` at
# import time froze the value, which defeats the whole point of corpus_io
# resolving the book's shape at call time (Phase 2, 2026-09-04): a server
# pointed at another book would have kept this book's ranges. Both functions
# below ask corpus_io each time instead. This is the same import-time-freeze
# trap item 0AZ documents for paths, one layer out.

# The indirection review_server had, kept deliberately rather than inlined to
# cio.load_repo_json. It is the seam the witness-queue tests patch to feed a
# synthetic queue; inlining it during the 2026-09-01 extraction silently broke
# two of them, which is the whole argument for keeping an extraction a MOVE and
# changing nothing else on the way through.
_load_json = cio.load_repo_json


def get_part_num_for_klal(klal_id):
    """Which declared chunk holds this klal.

    The `<=` ladder this replaces hardcoded 222/444 and, by falling through to
    `return 3`, assumed a book has exactly three chunks and that anything past
    part 2 must be part 3. corpus_io.part_number_for_klal reads the manifest, so
    a one-file book answers 1 for everything and a klal outside every declared
    range is None rather than silently attributed to the last chunk.
    """
    return cio.part_number_for_klal(klal_id)

class BadRequest(ValueError):
    """A query value the CLIENT got wrong - do_GET renders it as a 400.

    A ValueError subclass so existing `except ValueError` call sites keep
    catching it, but its own type so do_GET can tell "the caller sent
    ?part=4" apart from an int() blowing up somewhere inside a handler. The
    second kind is a server bug and must stay a 500; answering it with 400
    would blame the reviewer for our own defect.
    """

# The accepted `part` values, in one place. "0"/"none" are historical spellings
# of "all" that the frontend and older call sites both still emit.
_PART_ALIASES = {"all": "all", "0": "all", "none": "all",
                 "1": "1", "2": "2", "3": "3"}

def normalize_part(part_num):
    """Canonical part token ("all"/"1"/"2"/"3") for a raw query value or int.

    RAISES ValueError on anything else. FIXED 2026-08-31 (finding S4, filed in
    the 2026-08-25 review and restated as the 2026-08-27 review's #5): both
    parts_for() and load_klalim() ended in a bare `else` that returned Part 1,
    so `?part=4`, `?part=part1`, `?part=all_parts` and a plain typo all served
    Part 1 data under a 200 - indistinguishable, to the caller, from asking for
    Part 1. A silent fallthrough in a dispatcher is how a client-side typo turns
    into a wrong answer nobody can see; the reviewer would be reading Part 1
    believing it was Part 3.

    Both functions now share this one validator rather than each carrying its
    own ladder - they had already drifted, in a small way that mattered:
    parts_for accepted "none" and load_klalim did not, so `?part=none` asked
    two functions the same question and got Parts 1+2+3 from one and Part 1
    from the other. Lesson 13, at the scale of two `if` chains.

    do_GET turns the ValueError into a 400, so a bad query says so.
    """
    part_str = str(part_num).lower() if part_num is not None else "all"
    if part_str not in _PART_ALIASES:
        raise BadRequest(
            f"unknown part {part_str!r} - expected one of "
            f"{sorted(_PART_ALIASES)}")
    return _PART_ALIASES[part_str]

def load_klalim(part_num=1):
    demo = _load_json("klalim_demo_dataset.json", [])
    part_str = normalize_part(part_num)
    if part_str == "all":
        klalim = demo
    else:
        # One rule for every chunk, from the manifest - not a three-branch ladder
        # with a different shape per part (part 2 bounded both ends, part 3 open
        # ended, part 1 by upper bound alone). Those three spellings were three
        # chances to disagree, and the open-ended part-3 branch silently claimed
        # any klal past 445 no matter how many chunks the book declares.
        wanted = int(part_str)
        declared = cio.parts()
        if wanted > len(declared):
            klalim = []
        else:
            bounds = declared[wanted - 1]
            klalim = [k for k in demo
                      if bounds["first_klal"] <= k["klal_id"] <= bounds["last_klal"]]
    klalim.sort(key=lambda k: k["klal_id"])
    return {k["klal_id"]: k for k in klalim}, klalim

def parts_for(part_num):
    # Same string-normalization convention as load_klalim above (part_num
    # arrives as either an int, from a Python call site that already knows
    # the part, or a raw query-string value like "2"/"3"/"all"). FIXED
    # 2026-08-20 (code review): load_alignment/load_corrections used to
    # accept part_num and silently ignore it, always merging all three
    # parts - correct but wasteful (3x the JSON parses this request
    # actually needs). load_punctuation_candidates separately compared
    # this same value with `== 1` (an int), which is never true for the
    # string values "2"/"3"/"all" the query path passes, and built a
    # nonexistent "punctuation_candidates_partall.json" filename - Parts
    # 2/3/All silently showed punctuation_count=0 for every klal.
    part_str = normalize_part(part_num)
    if part_str == "all":
        return (1, 2, 3)
    return (int(part_str),)

def load_alignment(part_num=None):
    fnames = {1: "part1_header_anchored_alignment.json",
              2: "part2_header_anchored_alignment.json",
              3: "part3_header_anchored_alignment.json"}
    align = []
    for p in parts_for(part_num):
        align += _load_json(fnames[p], [])
    return {r["klal_id"]: r for r in align}

def load_corrections(part_num=None):
    fnames = {1: "corrections_part1.json", 2: "corrections_part2.json", 3: "corrections_part3.json"}
    combined = {}
    for p in parts_for(part_num):
        c = _load_json(fnames[p], {})
        if isinstance(c, dict):
            combined.update(c)
    return combined

def load_punctuation_candidates(part_num=1):
    # Only Part 1 has punctuation candidates generated as of 2026-08-20 -
    # parts 2/3 correctly return {} (no file) rather than erroring, so this
    # stays forward-compatible if punctuation_candidates_part{2,3}.json are
    # ever built.
    fnames = {1: "punctuation_candidates_part1.json",
              2: "punctuation_candidates_part2.json",
              3: "punctuation_candidates_part3.json"}
    combined = {}
    for p in parts_for(part_num):
        c = _load_json(fnames[p], {})
        if isinstance(c, dict):
            combined.update(c)
    return combined

# The vision verdicts that keep a witness item in the reviewer's queue. "A"
# means the vision pass sided with DocAI against Tesseract, which on this
# corpus is the overwhelmingly common and overwhelmingly correct outcome
# (DocAI 91.2% vs Tesseract 3.8% across the 419 items).
WITNESS_PRIORITY_VERDICTS = ("B", "NEITHER")

WITNESS_QUEUE_FILTERED = True

def load_witness_queue():
    """Independent-witness (Tesseract vs DocAI) disagreements for the
    reconstructed continuation pages - see verify_reconstruction_witness.py.

    These are anchored on the SCAN (page + bbox), not on a corpus word index,
    which is deliberate: it means they can be reviewed by reading the ink even
    though the reconstructed text is NOT in part1.json yet. Reviewing and
    committing text to the corpus stay separate steps, the same way recording a
    candidate decision is separate from apply_reviewer_decisions.py.

    Every read/write site below (api_klal's decided-count, api_witness_summary,
    api_witness_context, api_post_witness_decision's snapshot lookup) matches
    items by (klal_id, docai_token_index) alone - NOT page, even though
    docai_token_index is page-relative (an index into that page's own filtered
    token list, per verify_reconstruction_witness.py). That is only safe
    because PAGE_TO_KLAL there currently maps each of its 3 pages to a
    DIFFERENT klal_id (24->30, 37->75, 40->88) - investigated 2026-08-16 as
    the standing "risk 2" open item. If a klal_id ever needed a second
    witness-processed page (e.g. klal 30 spanning two reconstructed pages),
    that page's items would silently collide with the first page's under the
    same (klal_id, token_index) key - `next(...)` lookups would return
    whichever item happens to come first, and a decision recorded against one
    page's word could get attributed to a different page's word entirely, with
    no error. Asserting it here, not fixing the matching logic itself: no
    current data triggers it (checked below), and a real fix (adding page to
    every match site + the decision key + the frontend's request payload) is a
    bigger, currently-unmotivated change - this turns a hypothetical future
    silent misattribution into an immediate loud failure instead."""
    q = _load_json("reconstruction_witness_queue.json", {})
    items = q.get("queue", []) if isinstance(q, dict) else []
    seen = {}
    for w in items:
        key = (w["klal_id"], w["docai_token_index"])
        if key in seen and seen[key] != w.get("page"):
            raise RuntimeError(
                f"witness queue: (klal_id, docai_token_index) {key} appears on "
                f"both page {seen[key]} and page {w.get('page')} - the "
                f"page-less matching used throughout this file can no longer "
                f"tell these apart. See this function's docstring."
            )
        seen[key] = w.get("page")

    # ADDED 2026-08-23, implementing the triage decided (and left unbuilt) on
    # 2026-08-19: work this queue by VISION VERDICT, not in full.
    #
    # Tesseract was right in only 16 of 419 disagreements (3.8%) against
    # DocAI's 91.2% - it fails structurally, being a weaker engine on the SAME
    # scan rather than an independent signal. Cutting to the items where the
    # vision pass did NOT side with DocAI leaves 37 of 419 and loses zero of
    # the recorded findings.
    #
    # Filtering here rather than in the queue FILE is deliberate: the file is
    # the complete evidence trail and stays complete (it is also derived, so a
    # hand-edit would be the Lesson 13 defect this repo keeps re-finding). This
    # is a view; flip WITNESS_QUEUE_FILTERED to False to serve everything again.
    #
    # The union with already-decided items is not defensive padding - it is
    # load-bearing. Measured before shipping: 7 of the 10 recorded decisions
    # sit OUTSIDE the priority cut, so a naive filter would have erased every
    # one of them from the dashboard. This is the same trap that got tier-D
    # deletion rejected on 2026-08-19.
    #
    # CAVEAT, per Lesson 2: all 419 verdicts came back at >= 0.9 confidence, so
    # the 37 are a PRIORITY QUEUE, not proof the other 382 are clean.
    if not WITNESS_QUEUE_FILTERED:
        return items
    decided = {k for k in rd.all_current("witness_choice")}
    return [w for w in items
            if w.get("vision_selected") in WITNESS_PRIORITY_VERDICTS
            or (w["klal_id"], w["docai_token_index"]) in decided]
