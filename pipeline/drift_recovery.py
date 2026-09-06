# [PRODUCTION] WHERE DID THIS RULING'S WORD GO - the one place that answers it
# when no scan position was ever recorded.
#
# THE GAP THIS FILLS. Applying a correction shifts every later word_index in its
# klal (Lesson 35), and a ruling whose address rotted is invisible and unsafe:
# both display paths drop it, and a fresh ruling at that key lands on the wrong
# word. tools/repoint_stale_decisions.py and tools/close_satisfied_rulings.py
# already recover such a ruling by requiring TWO independent signals to agree -
# the snapshot BBOX resolved through scan_alignment, and the TEXT searched for
# the word the ruling names (Lesson 9).
#
# That bar is right and it is unreachable for a whole class of rulings, because
# THE INK SIGNAL DOES NOT EXIST FOR THEM. Measured on the live ledger
# 2026-09-05: `disputed_choice` carries candidate_snapshot.bbox 353 times out of
# 357 and `candidate_choice` 46 of 51, but `manual_correction` only **37 of
# 369** - and every one of the 131 `ai-dropped-lamed-correction` records, the
# corpus's largest block of unreviewed machine corrections (item 0AT), carries a
# two-key snapshot: `word_index` and `original_word`. Zero bboxes. A script that
# wrote the corpus without ever generating a candidate never had a scan box to
# record. So "re-derive the position from the snapshot bbox" returns None on its
# first line for 108 of 108 of them, and the plan built on it (item 0BO's plan
# item 1) produced nothing.
#
# THE SIGNAL THAT DOES EXIST, and why it is stronger rather than weaker. Within
# one klal the damage is not scattered: an apply run inserts or deletes words at
# particular positions, so every ruling past those positions moves by the SAME
# amount. Measured over the exact 27 positions the flag tool was skipping:
#
#     klal  69   10 stale rulings   exactly one offset fits all of them: -1
#     klal  74    7 stale rulings   exactly one offset fits all of them: -3
#     klal 159    7 stale rulings   exactly one offset fits all of them: +1
#     klal  83    1 stale ruling                                        +1
#     klal 103    1 stale ruling                                        +1
#     klal 163    1 stale ruling                                        +1
#
# Ten rulings agreeing on one number is a tighter constraint than one bounding
# box, and it survives the failure mode `close_satisfied_rulings.py` was built to
# refuse: klal 159's `אליבא` occurs six times, so a per-word text search cannot
# say which one a ruling names - and the uniform offset can, because the other
# nine rulings in that klal have to land correctly under the same shift.
#
# THE BAR. Every recovery needs a position that is UNAMBIGUOUS and a second,
# independent reason to believe it - Lesson 9, with the shift standing in for the
# ink where no ink was recorded.
#
#   1. UNAMBIGUOUS. Exactly one offset in the search window puts the ruling's own
#      word at its own index. Two fits and this refuses; that is the aliasing
#      check, and it is what stops a repeated word being "found" at whichever
#      occurrence happens to be nearest.
#   2. CORROBORATED, by either of two paths, never by (1) alone:
#      (a) the word occurs exactly ONCE in the whole klal, so the match is a
#          statement about a position rather than about an occurrence - the same
#          `unique` tier close_satisfied_rulings.py already trusts; or
#      (b) at least one OTHER unambiguous ruling in the same klal moved by the
#          identical offset. Two rulings written months apart, about different
#          words, agreeing on one number is not a coincidence a wrong shift
#          produces.
#
# WHY NOT "ONE OFFSET FOR THE WHOLE KLAL", which is what this module tried
# first. Because it is false wherever a klal has been edited more than once:
# each insertion or deletion starts a new constant region, so rulings on either
# side of it move by different amounts, and demanding a single klal-wide shift
# refuses every one of them. Measured over the 39 rulings the applier refuses,
# the klal-wide rule recovered 3 and refused 17 with "no single shift relocates
# every ruling in this klal" - and those 17 were not ambiguous, they were merely
# on opposite sides of a shift point. Per-ruling offsets with (2b) as the
# corroboration keeps the same guarantee and does not throw them away.
#
# WHAT THIS DELIBERATELY DOES NOT DO. It does not decide that a ruling is right,
# and it never writes corpus text. It answers one question - which index does
# this ruling now name - so that a flag can be raised there for a human, or a
# worklist row can point at the right word. Everything downstream still needs a
# person and the scan.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import corpus_io as cio  # noqa: E402


def _wid():
    """word_identity, imported lazily for the same cycle reason as _rd."""
    import word_identity
    return word_identity


def _rd():
    """review_decisions, imported lazily.

    It imports this module's sibling `identity`, and importing it at module
    scope here makes a cycle for any caller that reaches drift_recovery through
    review_decisions. Deferred to call time, which costs one dict lookup.
    """
    import review_decisions
    return review_decisions

# How far a shift is looked for. Every measured shift in this corpus is within
# a handful of words (-3..+1 over the 27-position sweep above), and a window
# this size already admits ~40 candidate offsets per klal, so widening it buys
# nothing but ambiguity - a wider search makes a UNIQUE fit less likely, not
# more, which is the safe direction to be wrong in.
DEFAULT_WINDOW = 10


def word_identities_of(rec, applied):
    """Every word this ruling's true position could legitimately hold NOW.

    A list, not one word, and the plural is the correction to this module's
    first version. `applied` still decides the shape:

      APPLIED     the corpus was changed to say what the reviewer chose, so
                  `chosen_text` is what sits at the position - one identity. An
                  applied DELETION carries an empty chosen_text and its word is
                  GONE, so it has NO identity and cannot be recovered; hunting
                  for a word that no longer exists is item 0AB's failure, a flag
                  written at a guessed index.
      NOT APPLIED TWO identities, and both are real. Usually nothing was
                  written, so the position still holds
                  review_decisions.original_word (`original_word` for a
                  manual_correction, `final_text` for a candidate/disputed
                  snapshot). But a LATER ruling at the same word may have
                  carried the same change in - which is the entire premise of
                  close_satisfied_rulings.py - and then the position holds the
                  CHOSEN text instead. Klal 210's eight `כקמייתא` rulings are
                  exactly that, and keying on the original alone loses all of
                  them.

    Offering two identities cannot manufacture a recovery: every identity feeds
    the same ambiguity test, so a second one can only ADD candidate offsets, and
    more candidates make a unique fit less likely, not more. It widens what can
    be found and never what can be believed.

    A multi-word span yields no identity: the span moves as a unit but its
    member words are addressed individually, so matching the first word would
    answer at a position the span does not start at.
    """
    def one(text):
        parts = (text or "").strip().split()
        return parts[0] if len(parts) == 1 else None

    if applied:
        return [w for w in [one(rec.get("chosen_text"))] if w]
    out = []
    for w in (one(_rd().original_word(rec)), one(rec.get("chosen_text"))):
        if w and w not in out:
            out.append(w)
    return out


def _occurrences(words, rec, applied):
    """How many places in the klal could hold this ruling, counting every
    identity it may legitimately have. Two identities that both occur means two
    places, which is what bar (2a) has to refuse."""
    names = word_identities_of(rec, applied)
    return sum(1 for w in words if w in names)


def candidate_offsets(words, word_index, identities, window=DEFAULT_WINDOW):
    """Every shift in the window that puts one of `identities` at
    `word_index + shift`.

    Offset 0 is excluded: a ruling still sitting on its own word is not stale,
    and admitting 0 would let "no drift" be reported as a recovery.
    """
    if not identities or word_index is None:
        return []
    if isinstance(identities, str):
        identities = [identities]
    return [d for d in range(-window, window + 1)
            if d != 0 and 0 <= word_index + d < len(words)
            and words[word_index + d] in identities]


def recover_klal(words, records, applied, window=DEFAULT_WINDOW):
    """Recover one klal's stale rulings. Returns (recovered, refused).

    `applied` is the set of ruling ids already promoted into the corpus (or a
    bool, when every record in the call shares one state) - see
    expected_word_of, whose answer inverts on it.

    `records` is every ruling recorded against this klal that the caller has
    already decided is stale (see stale_against). `recovered` is
    {record id: (new_word_index, offset, why)}; `refused` is
    {record id: reason}, so a caller can report the whole set rather than only
    its successes - the difference between a worklist and a silent filter
    (Lesson 26).
    """
    def _applied(r):
        return applied if isinstance(applied, bool) else r["id"] in applied

    by_id = {r["id"]: r for r in records}
    fits_by_id, refused = {}, {}

    # A RECORDED STABLE ID BEATS EVERYTHING BELOW, so it is consulted first and
    # the shift arithmetic never runs for a ruling that has one. This module
    # exists because most rulings have no scan position; the id, where present,
    # is a better answer than either - it is exact rather than inferred, and it
    # is the only address that survives the word's own text changing. The shift
    # search stays for the 594 rulings recorded before ids existed, and for any
    # klal whose sidecar is absent.
    id_state = _wid().load()
    settled_by_id = {}
    if id_state:
        for r in records:
            wid_val = ((r.get("candidate_snapshot") or {}).get("word_id"))
            if wid_val is None:
                continue
            found, status = _wid().locate(id_state, r["klal_id"], wid_val)
            if status == "live":
                settled_by_id[r["id"]] = (found, 0,
                                          f"stable word id {wid_val}, which names "
                                          f"the word itself rather than its text")
            elif status == "retired":
                dead = _wid().retirement_of(id_state, r["klal_id"], wid_val) or {}
                refused[r["id"]] = (
                    f"the word this ruling names (stable id {wid_val}, "
                    f"{dead.get('word')!r}) was {dead.get('reason', 'removed')} "
                    f"from the corpus - it has no position to recover")

    for r in records:
        if r["id"] in settled_by_id or r["id"] in refused:
            continue
        names = word_identities_of(r, _applied(r))
        if not names:
            refused[r["id"]] = ("names no single word - an applied deletion, a "
                                "multi-word span, or no recorded original")
            continue
        fits = candidate_offsets(words, r["word_index"], names, window)
        if not fits:
            refused[r["id"]] = (f"{' / '.join(repr(n) for n in names)} is nowhere "
                                f"within {window} words of w{r['word_index']}")
        else:
            fits_by_id[r["id"]] = fits

    # ANCHORS - the shifts this klal can be SHOWN to have undergone, established
    # only from rulings that need no disambiguating themselves.
    #
    # A ruling with one candidate offset and a word that is unique in the klal
    # pins that offset outright. Two rulings that each have one candidate offset
    # and agree on it pin it as well: they were written at different times about
    # different words, so a wrong shift does not produce that agreement.
    #
    # This is what lets an AMBIGUOUS ruling be settled. Klal 74 is the case that
    # forced it: `אליעזר` appears at w535 and w540, so the ruling at w538 has two
    # in-window fits and cannot choose between them alone - but four other
    # rulings in the same klal each have a single fit at -3, which says the
    # region shifted by three, and only one of the two candidates is at -3. The
    # earlier klal-wide rule reached the same answer by demanding every ruling
    # share one offset; that is a special case of this, and it fails the moment a
    # klal has two shift regions (the 17 refusals measured on the drifted set).
    solo = {rid: f[0] for rid, f in fits_by_id.items() if len(f) == 1}
    votes = {}
    for rid, off in solo.items():
        votes.setdefault(off, []).append(rid)
    anchors = set()
    for off, ids in votes.items():
        if len(ids) >= 2:
            anchors.add(off)
        elif _occurrences(words, by_id[ids[0]], _applied(by_id[ids[0]])) == 1:
            anchors.add(off)

    recovered = dict(settled_by_id)
    for rid, fits in fits_by_id.items():
        rec = by_id[rid]
        names = word_identities_of(rec, _applied(rec))
        expected = " / ".join(names)
        hits = [d for d in fits if d in anchors]
        if len(hits) == 1:
            off = hits[0]
            peers = len(votes.get(off, [])) - (1 if rid in solo else 0)
            why = (f"shift of {off:+d}, attested by {peers} other unambiguous "
                   f"ruling(s) in this klal" if peers else
                   f"shift of {off:+d}; {expected} occurs exactly once in this klal")
            recovered[rid] = (rec["word_index"] + off, off, why)
        elif len(hits) > 1:
            refused[rid] = (f"this klal shifted by more than one amount ({sorted(hits)}) "
                            f"and {expected} fits at more than one of them")
        elif len(fits) > 1:
            refused[rid] = (f"ambiguous - {len(fits)} shifts fit equally well "
                            f"({fits}) and none is attested by another ruling here")
        else:
            # A single in-window fit, on a word that repeats, with nothing else in
            # the klal moving by that amount. Refused on purpose: the window is
            # the only reason it looked unique, which is the aliasing case.
            refused[rid] = (f"shift of {fits[0]:+d} is the only fit within {window} "
                            f"words, but {expected} repeats in this klal and no "
                            f"other ruling here moved by that amount")
    return recovered, refused


def stale_against(words, rec, applied):
    """Does this ruling's recorded index still hold the word it names?

    The shared "is it stale" test, so a caller never writes its own half of it.
    A ruling naming no single word (a deletion) is reported NOT stale here -
    this method cannot speak to it either way, and calling it stale would put it
    into a recovery that must refuse it anyway.
    """
    names = word_identities_of(rec, applied)
    wi = rec.get("word_index")
    if not names or wi is None:
        return False
    return not (0 <= wi < len(words) and words[wi] in names)


def group_by_klal(records):
    """{klal_id: [records]}, preserving order - the shape both callers need."""
    out = {}
    for r in records:
        out.setdefault(r["klal_id"], []).append(r)
    return out


def load_corpus_words(part_klalim=None):
    """{klal_id: [words]} for the corpus, split the way an index addresses it."""
    klalim = part_klalim if part_klalim is not None else cio.load_part1()
    return {k["klal_id"]: cio.words_of(k) for k in klalim}
