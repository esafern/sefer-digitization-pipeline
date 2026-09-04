# [PRODUCTION] WHO made a decision - the one place that answers it.
#
# THE PROBLEM THIS REPLACES. Every record in review_decisions.jsonl carries a
# single free-text `reviewer` string, and that one string has been doing three
# different jobs at once:
#
#   WHO       a person ("local", "user", "local-backfill-2026-08-17")
#   WHAT KIND human or machine
#   WHICH     which automated pass ("ai-dropped-lamed-correction",
#             "tools/reconstruct_placeholder_klalim.py")
#
# Measured on the live log 2026-09-04: 3,203 records, **35 distinct reviewer
# strings** for what is really about six agents and one person. The conflation
# is not cosmetic - it is the direct cause of item 0AT, where a script's
# `manual_correction` was indistinguishable from a human ruling and 131 machine
# corrections rendered in the dashboard as adjudicated. `is_human_reviewer()`
# has to guess from a `"local"` PREFIX because there is nothing else to read.
#
# WHAT THIS DOES NOT TOUCH: `chosen_source`. Which ENGINE's reading won
# (docai_reading / vlm_reading / surya_reading / vision_transcription) is
# already recorded, separately and correctly. "Who recorded the decision" and
# "whose reading was chosen" are different questions; merging them would lose
# information the ledger already has.
#
# THE ACTOR SHAPE, as stored on a record:
#
#   {"kind": "human"|"tool",
#    "id": "r-eric" | "gemini-vision-adjudicator",
#    "display": "Eric Safern" | "Gemini Vision Adjudicator",
#    "email": "eric@example.com",        # humans only, snapshot - see below
#    "via": "review-dashboard" | "verify_corrections_vision.py",
#    "verified": false}
#
# `id` IS AN INTERNAL ID, NOT AN EMAIL (user's call, 2026-09-04). The ledger is
# permanent and an email is not: people change addresses, and a decision from
# 2026 must still resolve to the same person afterwards. The stable internal id
# is the join key; `reviewers.json` maps it to a current email and display name.
#
# ...AND the email/display are ALSO snapshotted onto the record. That is not a
# contradiction of the line above, it is what an append-only audit log is for:
# the id answers "who is this, now and forever", the snapshot answers "what did
# we believe when this was written" - recoverable even if the roster file is
# lost or edited. The snapshot is explicitly NOT authoritative for present-day
# lookups; resolve the id against the roster for that.
#
# `verified` IS THE HONEST BIT. Until real authentication exists, an identity
# here is ASSERTED by whoever ran the process (an env var or a config file),
# not proven. Writing an email into a permanent audit trail while implying it
# was authenticated would be exactly the kind of overclaim this project logs
# findings about. When Google OIDC lands, the provider's verified subject sets
# `verified: true` and adds an `auth` block; nothing else here changes.
#
# THE SEAM. Two functions are the whole interface:
#   resolve_actor()  - who is acting NOW (env/config today, a session later)
#   actor_of(record) - who acted THEN (structured if present, legacy if not)
# Swapping in OIDC replaces the body of resolve_actor and nothing else, the
# same way corpus_root() localised "where is the corpus".
import json
import os

# THIS INSTALLATION, not the corpus root: a reviewer roster is a property of the
# deployment and its people, not of the book being reviewed - the same team may
# review several books. Deliberately named INSTALL_DIR rather than REPO, both
# because that is what it means and because `REPO = os.path.dirname(...)` is the
# seam-bypass pattern item 0BI's guard watches for.
INSTALL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ROSTER_PATH = os.environ.get("SEFER_REVIEWERS") or os.path.join(INSTALL_DIR, "reviewers.json")

# The env var naming the person at the keyboard, by internal id.
ACTIVE_REVIEWER_ENV = "SEFER_REVIEWER"

HUMAN = "human"
TOOL = "tool"

# Known automated agents. A REGISTRY rather than free text, because free text is
# how 35 distinct strings accumulated for six agents - each one plausible when it
# was written, never counted until someone did. An id absent from here is not
# rejected (a new pass must be able to run), but it is marked `unregistered` so
# the sprawl is visible instead of silent.
TOOL_ACTORS = {
    "docai": "Google Document AI (primary OCR)",
    "gemini-vision-adjudicator": "Gemini vision adjudication of a disputed crop",
    "dicta": "Dicta RashiOCR",
    "surya": "Surya OCR (local)",
    "vlm": "VLM full-page witness",
    "tesseract": "Tesseract (retired witness)",
    "lexical-detector": "The lexical//substitution detectors",
    "pipeline-script": "An unattributed pipeline or tools/ script",
}

# Legacy `reviewer` strings that mean A PERSON. Everything else in the log is a
# script. Kept as an explicit tuple rather than a prefix test so the mapping is
# auditable; `local-*` variants are folded in by the prefix rule below because
# five of them exist and all are the same one human.
LEGACY_HUMAN = ("local", "user")


def _roster():
    """{internal_id: {"email": ..., "display": ...}} - empty if absent.

    Absent is the normal case today and must stay usable: this project runs
    single-user and local, and a missing roster should degrade to an
    unidentified human, never block a ruling from being recorded.
    """
    try:
        with open(ROSTER_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {}
    return data.get("reviewers", data) if isinstance(data, dict) else {}


def human_actor(reviewer_id, via="review-dashboard", verified=False):
    """Build a human actor from an internal id, resolved against the roster."""
    entry = _roster().get(reviewer_id) or {}
    actor = {
        "kind": HUMAN,
        "id": reviewer_id,
        "display": entry.get("display") or reviewer_id,
        "via": via,
        # ASSERTED until an auth provider says otherwise - see the header.
        "verified": bool(verified),
    }
    if entry.get("email"):
        actor["email"] = entry["email"]
    if reviewer_id not in _roster():
        actor["unregistered"] = True
    return actor


def tool_actor(tool_id, via=None):
    """Build a tool actor. `via` defaults to the tool id itself."""
    actor = {
        "kind": TOOL,
        "id": tool_id,
        "display": TOOL_ACTORS.get(tool_id, tool_id),
        "via": via or tool_id,
        "verified": False,
    }
    if tool_id not in TOOL_ACTORS:
        actor["unregistered"] = True
    return actor


def resolve_actor(reviewer_id=None, via="review-dashboard"):
    """WHO IS ACTING NOW.

    Today: the internal id passed in, else $SEFER_REVIEWER, else an
    unidentified local human - which is exactly what every one of the 1,372
    `"local"` records already means, so the default preserves today's behaviour
    rather than inventing an identity nobody asserted.

    Later: an authenticated session. This function is the only thing that has to
    change; `verified` becomes True and an `auth` block joins the actor.
    """
    reviewer_id = reviewer_id or os.environ.get(ACTIVE_REVIEWER_ENV)
    if not reviewer_id:
        return {"kind": HUMAN, "id": "local", "display": "Unidentified local reviewer",
                "via": via, "verified": False}
    return human_actor(reviewer_id, via=via)


def actor_of(record):
    """WHO ACTED THEN - structured if the record has it, mapped if it does not.

    Every one of the 3,203 records written before 2026-09-04 has only the legacy
    string, and the log is append-only, so nothing is migrated: this maps them on
    read, deterministically, forever. A caller never needs to know which era a
    record came from.
    """
    actor = (record or {}).get("actor")
    if isinstance(actor, dict) and actor.get("kind"):
        return actor
    return actor_from_legacy_reviewer((record or {}).get("reviewer"))


def actor_from_legacy_reviewer(reviewer):
    """The pre-2026-09-04 `reviewer` string, as an actor.

    A human here is deliberately id `"local"` with no email: the old records do
    not say WHICH person, and inventing one would be fabricating provenance in an
    audit trail. `legacy: True` marks that the identity was inferred from a
    string rather than recorded.
    """
    reviewer = reviewer or ""
    is_human = reviewer in LEGACY_HUMAN or reviewer.startswith("local")
    if is_human:
        return {"kind": HUMAN, "id": "local", "display": reviewer or "local",
                "via": reviewer or "unknown", "verified": False, "legacy": True}
    return {"kind": TOOL, "id": reviewer or "unknown",
            "display": TOOL_ACTORS.get(reviewer, reviewer or "unknown"),
            "via": reviewer or "unknown", "verified": False, "legacy": True}


def is_human(actor):
    return (actor or {}).get("kind") == HUMAN


def reviewer_string(actor):
    """The legacy `reviewer` field to write alongside a structured actor.

    Every existing reader - review_counts, the apply script, three tools, the
    dashboard's own filters - reads `reviewer`, and they all keep working
    because a record carries BOTH. A human writes "local" (or "local:<id>" once
    identified), a tool writes its own id, so
    review_decisions.is_human_reviewer's prefix rule stays true by construction
    rather than by coincidence.
    """
    if is_human(actor):
        rid = actor.get("id") or "local"
        return "local" if rid == "local" else f"local:{rid}"
    return actor.get("id") or "unknown"
