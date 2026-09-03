# [PRODUCTION] Append-only audit trail for the review dashboard's human
# decisions (candidate overrides + per-klal revisit flags). Every decision
# is a new line appended to review_decisions.jsonl - never rewritten or
# deleted in place, so "current" state is always derivable and full history
# is always recoverable and revisitable.
#
# This exists because the one prior attempt at a human-override mechanism
# was dead code: review.html's tooltip JS read a `human_correction_note`
# field that nothing ever wrote, and the one real manual JSON edit that
# ever set it (klal 1/word 468, 2026-08-05) was silently destroyed the next
# time the pipeline regenerated corrections_part1.json from scratch - see
# PROJECT-STATUS.md. A decision recorded here lives in its own file the
# corpus-build pipeline never touches, so a rebuild can never clobber it.
#
# Record shape (one JSON object per line):
#   id                  short unique id (hex), referenced by an apply_event
#                       row's applied_decision_id
#   ts                  ISO8601 UTC timestamp, set at append time
#   decision_type       "candidate_choice" | "klal_flag" | "apply_event"
#                       | "punctuation_choice" | "witness_choice"
#                       | "manual_correction"
#                       witness_choice: an independent-witness (Tesseract vs
#                       DocAI) disagreement on a reconstructed page, keyed by
#                       docai_token_index rather than a corpus word index,
#                       because the text it concerns is not in part1.json yet.
#                       manual_correction: a reviewer-initiated flag/replace
#                       on ANY word, not just one the machine pipeline
#                       already flagged - added 2026-08-13 per direct user
#                       request ("add feature for reviewer to flag any word
#                       and replace it"). Unlike candidate_choice, there is
#                       no corrections_part1.json entry behind it; the
#                       decision itself is the only record of what was
#                       proposed, at what index, against what original word.
#   klal_id             int
#   word_index          int for candidate_choice/apply_event/
#                       punctuation_choice/manual_correction, null for
#                       klal_flag. For manual_correction this is an index
#                       into clean_text.split(' ') (space-only split,
#                       matching review_frontend/app.js's own convention -
#                       NOT clean_text.split() with no argument, which most
#                       of the corpus-build pipeline uses instead; see
#                       CLAUDE.md/PROJECT-STATUS.md on this project's
#                       standing word-index-scheme risk).
#   chosen_source       "docai_reading"|"final_text"|"vision_transcription"
#                       |"vlm_reading" (added 2026-08-21 - VLM baseline
#                       enrichment, see assemble_corrections_dataset.py)
#                       |"custom"|null for candidate_choice; "accept"|
#                       "reject" for punctuation_choice; always "custom" for
#                       manual_correction (it's always free-typed)
#   chosen_text         the literal chosen string (candidate_choice); "[.]"
#                       or null (punctuation_choice, accept/reject); the
#                       proposed replacement text (manual_correction)
#   candidate_snapshot  full corrections_part1.json entry at decision time
#                       (candidate_choice) or the proposed insertion's
#                       {before_word_index, reasoning} (punctuation_choice)
#                       or {word_index, original_word} (manual_correction -
#                       the word actually seen at that index when flagged,
#                       for drift detection since there's no corrections_
#                       part1.json entry to check against instead), so a
#                       later apply step can detect drift even after that
#                       file gets regenerated
#   needs_revisit       bool (klal_flag only)
#   note                free-text, any decision_type
#   reviewer            who made the decision (default "local")
#   applied_decision_id apply_event rows only: id of the candidate_choice
#                       decision this promoted into part1.json
#
# "Current" for a (klal_id, word_index, decision_type) key = the LAST
# matching line in the file (append order = chronological order - id is a
# random short hex, not a sort key). "History" = every matching line, in
# file order, oldest first.
import json
import os
import threading
import uuid
from datetime import datetime, timezone

# Moved one level deeper (pipeline/ or tools/) 2026-08-16 - REPO now goes up
# two levels, not one, to keep resolving to the actual repo root where
# part1.json/docai_word_boxes/etc. live.
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Overridable via env var so tests/test_review_server.py can point a live
# review_server.py subprocess at a throwaway file instead of the real,
# git-tracked decisions log.
DECISIONS_PATH = os.environ.get("REVIEW_DECISIONS_PATH") or os.path.join(REPO, "review_decisions.jsonl")

VALID_DECISION_TYPES = {
    "disputed_choice",
    "candidate_choice",
    "klal_flag",
    "apply_event",
    "punctuation_choice",
    "witness_choice",
    "manual_correction",
    # A ruling on a klal's TITLE. Its own type, not a manual_correction with a
    # field tag, because all_current() keys on (klal_id, word_index) and a title
    # index is a DIFFERENT ADDRESS from a body index in the same klal - klal 39
    # word 2 names one word in the heading and another in the text. Sharing the
    # namespace would have let one ruling silently displace the other.
    # ADDED 2026-09-03 for item 39: `title` is corpus text under the
    # single-source-of-truth rule, and until now the pipeline had no way to
    # promote a correction to it, so five were HAND-EDITED into part1.json on
    # 2026-08-31 as a recorded exception. This is the path they should have had.
    "title_correction",
}


def _match_decision_types(decision_type):
    if decision_type is None:
        return None
    if decision_type in ("disputed_choice", "candidate_choice"):
        return {"disputed_choice", "candidate_choice"}
    return {decision_type}

# Guards append_decision() against interleaved partial writes under
# ThreadingHTTPServer's concurrent-request model. Python's buffered f.write()
# is not guaranteed to be a single write(2) syscall, so two simultaneous
# appends could interleave bytes mid-line. Low risk in practice (single user,
# browser serializes clicks), but the cost of a lock here is zero.
_APPEND_LOCK = threading.Lock()


def _resolve(path):
    """Resolve a `path=None` argument to the CURRENT value of DECISIONS_PATH.

    FIXED 2026-08-16 (round-2 audit). Every function below used to declare
    `path=DECISIONS_PATH` as a default argument. Python evaluates a default
    argument ONCE, at import time, so the default was permanently bound to
    whatever DECISIONS_PATH held then - and reassigning the module attribute
    afterwards (`rd.DECISIONS_PATH = tmp`, or `monkeypatch.setattr(rd,
    "DECISIONS_PATH", tmp)`) silently had NO effect on any call that didn't
    pass `path=` explicitly. Writes kept landing in the real, git-tracked
    review_decisions.jsonl.

    That idiom is this project's standard way to redirect a script at a
    throwaway file: tests/test_pipeline_logic.py uses monkeypatch.setattr on
    PART1_PATH, RAW_DIR, FREQ_CACHE, FREQ_META, CACHE_DB and
    SEFARIA_FREQ_CACHE, and it works on every one of them because those
    modules read their constant at call time. review_decisions.py was the
    single module where the same idiom failed - and it is the module guarding
    the append-only human-decision log that CLAUDE.md singles out as the one
    file no pipeline run may ever clobber.

    It has already misfired twice, both times as a silent write to the
    tracked log: once during the round-1 audit (a test called a write
    endpoint without stubbing append_decision, appending a junk row - see
    PROJECT-STATUS.md), and once during this round-2 audit while confirming
    this very finding. Both were caught and reverted by a byte-comparison
    afterwards, not by anything in the code refusing the write. Resolving at
    call time makes the safety measure actually work.
    """
    return path if path is not None else DECISIONS_PATH


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


# Reviewer tags that mean a PERSON ruled, as opposed to a script. This lives
# beside append_decision because it is a WRITE-side rule first: see the
# manual_correction guard there.
#
# PUBLIC as of 2026-09-03, and review_server.py's `_ruled_by_human` now delegates
# to it instead of keeping the second copy it carried since 2026-09-02. The old
# comment here said the display side was "a different question with the same
# answer", which is exactly the shape START_HERE's shared-module rule and Lesson
# 13 warn about - a parallel copy that happens to agree. It had already grown a
# third consumer (the ligature invariant, which must not exempt a position on a
# SCRIPT's say-so, item 0AT), and three copies of one predicate is how the
# `ai-dropped-lamed-correction` pass got to look human in the first place.
HUMAN_REVIEWERS = ("local", "user")


def is_human_reviewer(reviewer):
    reviewer = reviewer or ""
    return reviewer in HUMAN_REVIEWERS or reviewer.startswith("local")


def ruled_by_human(rec):
    """Did a PERSON write this ledger record? Takes the record, not the tag."""
    return is_human_reviewer((rec or {}).get("reviewer"))


_is_human_reviewer = is_human_reviewer  # pre-2026-09-03 internal name


def append_decision(decision_type, klal_id, word_index=None, chosen_source=None,
                     chosen_text=None, candidate_snapshot=None, needs_revisit=None,
                     note=None, reviewer="local", applied_decision_id=None,
                     supersedes=None, path=None):
    """`supersedes` is the id of an earlier ruling this one REPLACES.

    ADDED 2026-09-02 for tools/repoint_stale_decisions.py. An append-only log has
    no way to correct a record - which is its point - but it does need a way to
    say "that one is no longer the answer", or a re-pointed ruling appears
    alongside its own stale predecessor and the reviewer sees both. Nothing is
    edited or removed; the superseded record stands exactly as written, and this
    is a forward reference to it.

    Deliberately NOT honoured by all_current(): a consumer that applies decisions
    to the corpus has its own drift check and will skip a stale one on the text,
    and widening the meaning of "current" across every consumer is a change with
    a much larger blast radius than the display problem this solves.
    """
    path = _resolve(path)  # see _resolve(): NOT a default arg, deliberately
    if decision_type not in VALID_DECISION_TYPES:
        raise ValueError(f"invalid decision_type: {decision_type!r}")
    # A SCRIPT MAY NOT RECORD A HUMAN RULING. `manual_correction` is the type the
    # dashboard renders GREEN as Human-Decided and drops out of every queue, so
    # writing one from an automated pass says "a person settled this" about
    # something no person has seen.
    #
    # ADDED 2026-09-02, reviewer: "manual correction was the wrong flag for an
    # automated change where the note says it should be reviewed." The
    # `ai-dropped-lamed-correction` pass wrote 131 of them, its own note said "A
    # human should still check this specific instance against the scan" and
    # "flag every one" - and 114 of the 131 were never flagged. Applied to the
    # corpus, drawn as settled, invisible to review. Two of them are now
    # confirmed wrong against the ink.
    #
    # An automated pass that wants a human to look raises a `klal_flag`, which is
    # what a queue is made of. This refuses rather than warns: a warning in a
    # batch script's output is a warning nobody reads.
    if decision_type == "manual_correction" and not _is_human_reviewer(reviewer):
        raise ValueError(
            f"reviewer {reviewer!r} may not write a manual_correction: that type means "
            "A PERSON RULED, and the dashboard renders it as settled. An automated "
            "pass records a klal_flag (needs_revisit=True) so a human still sees it.")
    record = {
        "id": uuid.uuid4().hex[:12],
        "ts": _now_iso(),
        "decision_type": decision_type,
        "klal_id": klal_id,
        "word_index": word_index,
        "chosen_source": chosen_source,
        "chosen_text": chosen_text,
        "candidate_snapshot": candidate_snapshot,
        "needs_revisit": needs_revisit,
        "note": note,
        "reviewer": reviewer,
        "applied_decision_id": applied_decision_id,
        "supersedes": supersedes,
    }
    with _APPEND_LOCK:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


# (path -> ((mtime_ns, size), records)) for the last file read. See _read_all().
_READ_CACHE = {}


def _read_all(path=None):
    """Every decision row, oldest first, re-read from disk whenever the file
    has changed.

    MEMOIZED 2026-08-26 (code review: 2026-08-25 C1/C2, 2026-08-26 H9/H10/H11 -
    both runs found this independently). A single request calls this many times
    over - `GET /api/page/73` measured **25 full parses of the 1.8 MB log,
    182.5 ms**, because api_page() calls _word_level_ai_flags() per klal and
    that function alone re-reads candidate_choice and manual_correction. With
    this cache the same request is **14.0 ms**; /api/klal/88 goes 9 parses ->
    11.6 ms, /api/klalim 7 parses -> 20.4 ms.

    This does NOT weaken review_server.py's "fresh off disk every call,
    deliberately no cache" contract, and the distinction matters. The key is
    (st_mtime_ns, st_size), so any write invalidates it - and this file is
    APPEND-ONLY by design (see the module header), so a write always grows it
    and the size alone would be enough. A decision recorded in one tab is
    visible to the next request from another, which is the property that
    contract exists to protect.

    Returning the cached list means callers share record objects across threads
    (ThreadingHTTPServer). Verified before landing this: replaying
    api_page/api_klal/api_klalim over shared records mutated 0 of 2,153 rows -
    every consumer reads. A caller that needs to mutate a row must copy it.
    """
    path = _resolve(path)
    try:
        st = os.stat(path)
    except OSError:
        return []
    stamp = (st.st_mtime_ns, st.st_size)
    cached = _READ_CACHE.get(path)
    if cached is not None and cached[0] == stamp:
        return cached[1]
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    _READ_CACHE[path] = (stamp, records)
    return records


def history_for(klal_id, word_index=None, decision_type=None, path=None):
    """All decisions matching the key, oldest first. Pass word_index to
    narrow to a specific word.

    CORRECTED 2026-08-17: this docstring used to claim klal_flag rows
    "structurally always" carry word_index=None - true when written, no
    longer true. klal_flag can now ALSO name one specific word (an AI pass
    flagging a single candidate, e.g. detect_real_word_substitution.py -
    see review_server.py's _word_level_ai_flags() and
    _general_klal_flag_current()/_general_klal_flag_history(), which are
    the general-panel-only query this function's old docstring was
    describing). Omitting word_index here does NOT filter by word_index at
    all - it returns every decision for the klal regardless, general or
    word-level alike; a caller that wants ONLY the general (word_index is
    None) klal_flag rows must filter for that explicitly, which is exactly
    what the two review_server.py helpers above do rather than relying on
    this function's word_index=None default to mean that."""
    records = _read_all(path)
    allowed_types = _match_decision_types(decision_type)
    out = []
    for r in records:
        if r["klal_id"] != klal_id:
            continue
        if word_index is not None and r.get("word_index") != word_index:
            continue
        if allowed_types is not None and r["decision_type"] not in allowed_types:
            continue
        out.append(r)
    return out


def current_for(klal_id, word_index=None, decision_type=None, path=None):
    """The latest decision matching the key, or None."""
    h = history_for(klal_id, word_index, decision_type, path)
    return h[-1] if h else None


def all_current(decision_type, path=None):
    """Latest decision per (klal_id, word_index) for a given decision_type -
    e.g. every currently-active disputed/candidate override, or every klal's current
    flag state. Returns {(klal_id, word_index): record}."""
    records = _read_all(path)
    allowed_types = _match_decision_types(decision_type)
    current = {}
    for r in records:
        if allowed_types is not None and r["decision_type"] not in allowed_types:
            continue
        key = (r["klal_id"], r.get("word_index"))
        current[key] = r  # later (later-appended) records win for the same key
    return current


def flagged_klalim(path=None):
    """klal_ids whose current klal_flag decision has needs_revisit=True."""
    current = all_current("klal_flag", path)
    return sorted(kid for (kid, _), r in current.items() if r.get("needs_revisit"))


def applied_decision_ids(path=None):
    """ids of decisions already promoted into the corpus, i.e. every
    `applied_decision_id` referenced by an apply_event row.

    Both apply scripts write an apply_event for each decision they promote,
    but until 2026-08-11 neither of them ever READ those rows back - so a
    second run re-applied everything. For `replace`/`insert` opcodes that was
    masked, because those paths re-verify the live text still matches the
    snapshot and bail when it doesn't; the `delete` path (which inserts a word
    rather than replacing one) had no such check and duplicated its insertion
    on every run, and the punctuation apply script duplicated all of its
    insertions. See PROJECT-STATUS.md "Deep methodology audit". This is the
    general fix: an applied decision is identified by id, not inferred from
    whether the text happens to still look un-applied."""
    return {
        r["applied_decision_id"]
        for r in _read_all(path)
        if r["decision_type"] == "apply_event" and r.get("applied_decision_id")
    }


def superseded_ids(path=None):
    """Every ruling id that a LATER record declares it replaces.

    ADDED 2026-09-02 with `supersedes` - the read side of it. A separate function
    rather than a filter inside all_current() on purpose: see append_decision's
    note. This is what a DISPLAY needs to stop showing a ruling beside the
    corrected copy of itself; what a corpus-mutating consumer needs is its own
    drift check, which it already has.
    """
    return {r["supersedes"] for r in _read_all(path) if r.get("supersedes")}


def find_by_id(decision_id, path=None):
    for r in _read_all(path):
        if r["id"] == decision_id:
            return r
    return None
