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
#                       | "punctuation_choice"
#   klal_id             int
#   word_index          int for candidate_choice/apply_event/
#                       punctuation_choice, null for klal_flag
#   chosen_source       "docai_reading"|"final_text"|"vision_transcription"
#                       |"custom"|null for candidate_choice; "accept"|
#                       "reject" for punctuation_choice
#   chosen_text         the literal chosen string (candidate_choice); "[.]"
#                       or null (punctuation_choice, accept/reject)
#   candidate_snapshot  full corrections_part1.json entry at decision time
#                       (candidate_choice) or the proposed insertion's
#                       {before_word_index, reasoning} (punctuation_choice),
#                       so a later apply step can detect drift even after
#                       that file gets regenerated
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
import uuid
from datetime import datetime, timezone

REPO = os.path.dirname(os.path.abspath(__file__))
# Overridable via env var so tests/test_review_server.py can point a live
# review_server.py subprocess at a throwaway file instead of the real,
# git-tracked decisions log.
DECISIONS_PATH = os.environ.get("REVIEW_DECISIONS_PATH") or os.path.join(REPO, "review_decisions.jsonl")

VALID_DECISION_TYPES = {"candidate_choice", "klal_flag", "apply_event", "punctuation_choice"}


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def append_decision(decision_type, klal_id, word_index=None, chosen_source=None,
                     chosen_text=None, candidate_snapshot=None, needs_revisit=None,
                     note=None, reviewer="local", applied_decision_id=None,
                     path=DECISIONS_PATH):
    if decision_type not in VALID_DECISION_TYPES:
        raise ValueError(f"invalid decision_type: {decision_type!r}")
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
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def _read_all(path=DECISIONS_PATH):
    if not os.path.exists(path):
        return []
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def history_for(klal_id, word_index=None, decision_type=None, path=DECISIONS_PATH):
    """All decisions matching the key, oldest first. Pass word_index to
    narrow to a specific word; omit it (with decision_type="klal_flag") for
    a klal-level query - klal_flag/apply_event rows structurally always
    carry the word_index they're about (or None for klal_flag), so
    decision_type alone is enough to disambiguate without needing a
    separate "match None explicitly" sentinel."""
    records = _read_all(path)
    out = []
    for r in records:
        if r["klal_id"] != klal_id:
            continue
        if word_index is not None and r.get("word_index") != word_index:
            continue
        if decision_type is not None and r["decision_type"] != decision_type:
            continue
        out.append(r)
    return out


def current_for(klal_id, word_index=None, decision_type=None, path=DECISIONS_PATH):
    """The latest decision matching the key, or None."""
    h = history_for(klal_id, word_index, decision_type, path)
    return h[-1] if h else None


def all_current(decision_type, path=DECISIONS_PATH):
    """Latest decision per (klal_id, word_index) for a given decision_type -
    e.g. every currently-active candidate override, or every klal's current
    flag state. Returns {(klal_id, word_index): record}."""
    records = _read_all(path)
    current = {}
    for r in records:
        if r["decision_type"] != decision_type:
            continue
        key = (r["klal_id"], r.get("word_index"))
        current[key] = r  # later (later-appended) records win for the same key
    return current


def flagged_klalim(path=DECISIONS_PATH):
    """klal_ids whose current klal_flag decision has needs_revisit=True."""
    current = all_current("klal_flag", path)
    return sorted(kid for (kid, _), r in current.items() if r.get("needs_revisit"))


def applied_decision_ids(path=DECISIONS_PATH):
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


def find_by_id(decision_id, path=DECISIONS_PATH):
    for r in _read_all(path):
        if r["id"] == decision_id:
            return r
    return None
