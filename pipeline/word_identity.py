# [PRODUCTION] A STABLE ID FOR EVERY WORD - an address that survives both the
# index moving and the word's own text changing.
#
# WHY THE TWO ADDRESSES THIS REPO ALREADY HAS ARE NOT ENOUGH, measured on the
# live ledger 2026-09-06 over the 594 current word-level rulings:
#
#     resolves by word_index ...........  42
#     resolves by (word, occurrence) ....   1
#     resolves because the word is unique   8
#     DOES NOT RESOLVE .................. 543   (517 applied, 26 unapplied)
#
# `word_index` is invalidated by any earlier edit - that is items 0AB, 0AP and
# Lesson 35, and it is why `occurrence_of` was added as "the stable half of a
# word's address". But look at WHICH rulings fail: 517 of the 543 are APPLIED,
# and they fail BY CONSTRUCTION. The occurrence anchor names `original_word` -
# the word the ruling was ruling ON - and applying the ruling is precisely what
# replaces that word. klal 4 w0 anchors on `ד` and the corpus now holds `ד`;
# klal 57 w0 anchors on `נז` and now holds `נז אין`. The anchor is a name for
# text that the successful operation destroyed.
#
# So no address DERIVED FROM THE TEXT can survive a correction, however clever
# the derivation. A stable id has to be assigned to the POSITION and carried
# across edits by whoever makes them. That is what this module is.
#
# WHERE IT LIVES, AND WHY NOT IN part*.json. `word_identity.json` is a SIDECAR
# keyed by klal, parallel to `cio.words_of(klal)`. The corpus files are the
# hand-edited source of truth under START_HERE's single-source rule, and
# threading a per-word array through them would put structural bookkeeping into
# the one file a human edits and the Parts 2-3 gate protects. The cost of the
# sidecar is honest and stated: it is a SECOND COPY OF THE CORPUS'S STRUCTURE,
# which is Lesson 13's shape exactly, and a second copy that can drift silently
# is worse than no copy at all. That is why `verify()` exists, why a gated
# invariant calls it, and why every mismatch is loud rather than repaired in
# passing.
#
# IDS ARE PER-KLAL AND NEVER REUSED. `next` is a high-water mark that only ever
# rises, so a deleted word's id is retired rather than recycled onto whatever
# slides into its place - the failure that would make an id worse than an index,
# because it would resolve confidently to the wrong word.
#
# WHAT PRESERVES AN ID, and this is the whole contract:
#
#   a word whose TEXT is corrected in place ....... keeps its id
#   a word that other edits shift left or right ... keeps its id
#   a word that is deleted ........................ its id retires, forever
#   a word that is inserted ....................... gets a fresh id
#
# Reconciliation is DIFF-DRIVEN (`reconcile`), not instrumented per opcode. The
# applier has three mutation branches plus manual and title paths, and Lesson 34
# is the record of what happens when a rule is implemented per branch: it gets
# fixed in the one that fired and the siblings keep the bug. Diffing old words
# against new words handles every branch through one code path, including ones
# added later.
import difflib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import corpus_io as cio  # noqa: E402

FILENAME = "word_identity.json"


def path():
    """Resolved at call time, through the corpus-root seam like everything else."""
    return cio.repo_path(FILENAME)


def load(state_path=None):
    """The sidecar, or an empty map when it does not exist yet.

    Absent is a legitimate state - a fresh clone, or a corpus this has never
    been seeded for - and must not stop anything from running. Callers that
    need it to be present say so themselves.
    """
    raw = cio.load_json(state_path or path(), None) or {}
    return {int(k): v for k, v in raw.items()}


def save(state, state_path=None):
    """Write the sidecar atomically.

    ATOMIC because a torn write here is worse than no file: half an id array is
    silently misaligned rather than obviously absent, and `verify()` would then
    report every klal after the tear. Written to a temp file in the same
    directory and renamed, which is atomic within a filesystem - the same
    reasoning the flushing rule in START_HERE encodes for batch scripts, applied
    to a single-shot write.
    """
    target = state_path or path()
    tmp = target + ".tmp"
    # ONE LINE PER KLAL, and that is about the DIFF, not about bytes. Pretty
    # printing put each of Part 1's 52,629 ids on its own line - a 53,741-line
    # tracked file in which inserting one word rewrites every line after it, so
    # every apply would land an unreadable diff on a file whose whole purpose is
    # to be auditable. Per-klal lines mean an edit shows as one changed line
    # naming the klal it changed.
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("{\n")
        rows = sorted(state.items())
        for i, (kid, entry) in enumerate(rows):
            f.write(f'  "{kid}": ' + json.dumps(entry, ensure_ascii=False,
                                                separators=(",", ":")))
            f.write(",\n" if i < len(rows) - 1 else "\n")
        f.write("}\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, target)


def seed_klal(words, start=1):
    """Fresh ids for one klal's words: 1..n, with the high-water mark after."""
    return {"ids": list(range(start, start + len(words))),
            "next": start + len(words)}


def seed(klalim):
    """A whole corpus's worth, from scratch. Ids are only meaningful WITHIN a
    klal, so each starts at 1 - there is no global namespace to collide in and
    a per-klal counter keeps the numbers small and readable in a ledger."""
    return {k["klal_id"]: seed_klal(cio.words_of(k)) for k in klalim}


def ids_for(state, klal_id):
    return (state.get(klal_id) or {}).get("ids") or []


def id_at(state, klal_id, index):
    """The stable id of the word currently at `index`, or None."""
    ids = ids_for(state, klal_id)
    return ids[index] if 0 <= index < len(ids) else None


def index_of(state, klal_id, word_id):
    """Where the word with this id sits NOW, or None if it is gone.

    None is a real answer and the important one: a retired id means the word was
    deleted, which a caller must be able to tell apart from "it moved". Nothing
    here searches for a replacement.
    """
    ids = ids_for(state, klal_id)
    try:
        return ids.index(word_id)
    except ValueError:
        return None


def reconcile(state, klal_id, old_words, new_words):
    """Carry ids across one klal's edit. Returns (kept, retired, minted).

    DIFF-DRIVEN on purpose - see the module header. The mapping each opcode gets:

      equal ................. ids carry over unchanged.
      replace, same length .. ids carry over. This is the case the whole module
                              exists for: correcting a word's TEXT must not
                              change which word it is, or every applied ruling
                              loses its address the moment it succeeds.
      replace, different .... treated as a delete plus an insert. The
                              correspondence between n old words and m new ones
                              is genuinely unknown when n != m, and inventing
                              one would hand out an id that says "this is the
                              same word" about a word nobody established was the
                              same. Refusing is the whole value of the id.
      insert ................ fresh ids from the high-water mark.
      delete ................ ids retire, and are never reused.
    """
    entry = state.get(klal_id) or seed_klal(old_words)
    old_ids, nxt = list(entry["ids"]), entry["next"]
    if len(old_ids) != len(old_words):
        raise ValueError(
            f"klal {klal_id}: the sidecar holds {len(old_ids)} ids for "
            f"{len(old_words)} words - it is out of step with the corpus and "
            f"reconciling would silently misalign every id after the gap. "
            f"Re-seed this klal deliberately (tools/seed_word_identity.py) "
            f"and accept that its id continuity is lost."
        )

    out, retired, minted = [], [], []
    sm = difflib.SequenceMatcher(None, old_words, new_words, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal" or (tag == "replace" and (i2 - i1) == (j2 - j1)):
            out.extend(old_ids[i1:i2])
        else:
            retired.extend(old_ids[i1:i2])
            for _ in range(j2 - j1):
                out.append(nxt)
                minted.append(nxt)
                nxt += 1
    state[klal_id] = {"ids": out, "next": nxt}
    kept = len(out) - len(minted)
    return kept, retired, minted


def verify(klalim, state):
    """Every way the sidecar can disagree with the corpus, as a list of strings.

    Empty means consistent. This is the function the gated invariant calls, and
    it is deliberately exhaustive rather than early-returning: a report naming
    one klal when six are wrong is the shape Lesson 28 warns about.
    """
    problems = []
    for k in klalim:
        kid = k["klal_id"]
        words = cio.words_of(k)
        entry = state.get(kid)
        if entry is None:
            problems.append(f"klal {kid}: no ids at all ({len(words)} words)")
            continue
        ids = entry.get("ids") or []
        if len(ids) != len(words):
            problems.append(
                f"klal {kid}: {len(ids)} ids for {len(words)} words - every id "
                f"after the first divergence names the wrong word")
        if len(set(ids)) != len(ids):
            dupes = sorted({i for i in ids if ids.count(i) > 1})
            problems.append(
                f"klal {kid}: duplicate ids {dupes[:5]} - an id that names two "
                f"positions is not an identity")
        if ids and entry.get("next", 0) <= max(ids):
            problems.append(
                f"klal {kid}: high-water mark {entry.get('next')} is not above "
                f"its largest id {max(ids)} - the next insert would REUSE a "
                f"live id and resolve confidently to the wrong word")
    return problems


def snapshot_fields(state, klal_id, word_index):
    """The identity fields a ruling records about the word it names.

    Returned as a dict to merge into candidate_snapshot, so a caller that has no
    sidecar yet simply merges nothing rather than writing nulls that later read
    as "this was recorded and was empty".
    """
    wid = id_at(state, klal_id, word_index)
    return {"word_id": wid} if wid is not None else {}


def resolve(state, rec, klal_id=None):
    """Where the word this ruling named sits NOW, by id alone. -> index or None.

    Independent of the ruling's text, which is what makes it work where
    review_decisions.resolve_word_index cannot: it never asks what the word was.
    """
    snap = (rec or {}).get("candidate_snapshot") or {}
    wid = snap.get("word_id")
    if wid is None:
        return None
    return index_of(state, klal_id if klal_id is not None else rec["klal_id"], wid)
