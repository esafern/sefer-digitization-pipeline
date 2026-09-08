# [PRODUCTION] What state is each word in, and how many of each are there.
#
# EXTRACTED from pipeline/review_server.py 2026-09-01, the second half of
# finding S1 (the 1,981-line God Object; scan_alignment.py took the geometry
# earlier the same day). This module holds THE word-state rule and the counts
# derived from it.
#
# Why this is one module and not two helpers left in the server: the 2026-08-26
# review's finding #6 named the real problem, which is not size. The word-state
# rule was encoded THREE times - api_klalim() computing nav counts, api_klal()
# merging entries for the text pane, and app.js's wordState() colouring them -
# and the two production defects in that range both came from the copies
# disagreeing. The nav said 1,201 where the pane rendered 1,061; then the fix
# for that made the numerator distinct but left the denominators summing per
# source, and klal 88 showed "-1 outstanding".
#
# That finding also recorded the honest counter-argument, which still holds:
# the obvious dedup - have api_klalim() call api_klal() 222 times - is what
# starved the Playwright suite. So the shared thing is the RULE, not the
# request. word_states() below answers "what is every word in this klal?" from
# data the caller has already loaded once, and api_klalim() calls it per klal
# with no extra file reads.
#
# app.js's wordState() remains a fourth encoding, in another language, and
# cannot be imported away. It is held in step by
# tests/test_corpus_invariants.py::test_nav_tristate_matches_what_each_word_
# actually_renders_as, which transcribes it and asserts the three counts this
# module produces match what the screen shows, klal by klal. That test is the
# safety net for this extraction; if the move changed behaviour, it fires.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import review_decisions as rd  # noqa: E402


# The three states a word can be in, and the ONLY three. They are exhaustive by
# construction in word_states() - every word_index that appears gets exactly one
# - which is what makes decided + machine_resolved + machine_disputed == total
# an identity rather than a coincidence the counts have to be careful about.
DECIDED = "decided"
RESOLVED = "machine_resolved"
DISPUTED = "machine_disputed"


# Flags that mean "the machine settled this; no reading is in dispute". Kept as
# a set rather than an equality test because a SECOND such flag was added
# 2026-08-24 (docai_ligature_artifact) and the equality tests scattered through
# the count/label code were not updated - the same word then rendered green in
# the text pane, "Machine-Disputed" in the nav and legend, and
# "Machine-Disputed" in the panel header. Three verdicts on one screen.
MACHINE_RESOLVED_FLAGS = ("current_text_confirmed", "docai_ligature_artifact")

def word_matches(words, word_index, expected_word):
    """Is `expected_word` still the word sitting at `word_index`?

    The shared drift check behind both manual_correction render paths
    (api_klal's synthetic entries and api_klalim's per-klal count). It was
    written out twice, and BOTH copies bounds-checked only the upper end -
    the same half-a-bounds-check gap already fixed in
    audit_applied_decisions.py's three checkers (2026-08-14, finding 9) and
    in apply_reviewer_decisions.py's five corpus mutators (2026-08-15,
    finding 8); the display path was simply never revisited. Python does not
    raise on a negative index: `words[-1]` is the klal's LAST word, so a
    decision recorded at word_index -1 whose original_word happened to equal
    that last word passed the check and rendered as a live "Human-Decided"
    correction attached to a word it never described, and counted toward
    that klal's decided/total badges.

    Not reachable from today's UI (app.js only ever sends a real index) and
    0 of the 136 recorded manual_correction decisions carry a negative
    index - defence-in-depth on the display path, matching what the
    write-side and corpus-mutating paths already do.
    """
    return 0 <= word_index < len(words) and words[word_index] == expected_word

def flag_answered_by_a_later_decision(klal_id, word_index, flag_rec,
                                       candidate_decisions=None,
                                       manual_decisions=None, path=None):
    """True when a human recorded a decision at this exact word AFTER the flag
    was raised.

    ADDED 2026-08-25, reviewer report on klal 163: "i cleared the flag but it
    still shows in the middle and right." They had cleared the KLAL-level flag,
    but three word-level flags stayed open on words they had already decided
    that same afternoon - so the klal stayed lit, the words stayed marked, and
    the panel still announced an open revisit flag. A flag says "come back and
    look at this word"; a decision recorded at that word afterwards IS the
    reviewer having looked. Requiring a second, separate click to say so is the
    friction, not the safeguard.

    ORDER IS THE WHOLE POINT: only a decision NEWER than the flag answers it. A
    flag raised after a decision is a fresh concern about an already-decided
    word (a later detector pass finding something the reviewer did not address)
    and must stay open.

    Swept 2026-08-25: 331 open word-level flags across 110 klalim, of which 23
    across 7 klalim are answered this way - klal 88 (12), klal 163 (3), klal 91
    (3), 29 (2), and one each in 2, 4, 8. The other 308 are genuinely
    unanswered and are untouched by this.

    Nothing is written to the ledger. The flag record stands exactly as
    recorded; this only decides whether it is still asking for something.
    """
    if candidate_decisions is None:
        candidate_decisions = rd.all_current("candidate_choice")
    if manual_decisions is None:
        manual_decisions = rd.all_current("manual_correction")
    flag_ts = _raised_at(flag_rec, path)
    for source in (candidate_decisions, manual_decisions):
        decision = source.get((klal_id, word_index))
        if decision and (decision.get("ts") or "") > flag_ts:
            return True

    # THEN BY STABLE WORD ID, because an index match is not the same question.
    #
    # FOUND 2026-09-07 (item 0CS), by a worklist count going UP after an apply.
    # Applying a word-count change fires reindex_flags_after_shift(), which moves
    # the FLAG onto the word it names - correctly. It does NOT move the ruling
    # that ANSWERED that flag, and must not: reindex_pending_decisions_after_
    # shift() deliberately skips anything already in the corpus ("already in the
    # corpus, not pending"). So the flag lands at w787 while the ruling that
    # answered it stays recorded at w786, the index test above misses, and a
    # flag the reviewer had already dealt with RE-OPENS.
    #
    # Measured on klal 54 the day this was written: three flags reindexed +1 by
    # one two-word split, all three re-opening, all three with ids that match
    # exactly (flag word_id 787 == ruling word_id 787). The id is the address
    # that survives the shift - which is the whole reason it exists - so ask it.
    #
    # Deliberately AFTER the index test and not instead of it: the index test is
    # exact and cheap, most flags and rulings still carry no id at all, and a
    # ruling recorded at the same index is the same word by definition.
    flag_id = rd.word_id_of(flag_rec, _backfilled(path))
    if flag_id is not None:
        for source in (candidate_decisions, manual_decisions):
            for (kid, _wi), decision in source.items():
                if kid != klal_id or (decision.get("ts") or "") <= flag_ts:
                    continue
                if rd.word_id_of(decision, _backfilled(path)) == flag_id:
                    return True
    return False


def _raised_at(flag_rec, path=None):
    """When this flag was ORIGINALLY raised, following `supersedes` to the root.

    A reindexed flag is the same concern at a new address, not a new one, but it
    is a new RECORD with today's timestamp. Using that timestamp makes an
    already-answered flag re-open the moment an unrelated edit shifts its klal,
    because the answer then looks older than the flag (item 0CS, measured on klal
    54: three flags, +1 shift, all three re-opened). Walk back to the first
    record in the chain and ask when THAT was written.

    Bounded, and deliberately: a corrupt or self-referential chain must not spin
    a request forever, so it gives up and uses the record it has.
    """
    rec, seen = flag_rec, set()
    for _ in range(32):
        prev_id = rec.get("supersedes")
        if not prev_id or prev_id in seen:
            break
        seen.add(prev_id)
        prev = rd.find_by_id(prev_id, path=path)
        if not prev or prev.get("decision_type") != "klal_flag":
            break
        rec = prev
    return rec.get("ts") or ""


# (resolved path -> ((mtime_ns, size), table)). Mirrors review_decisions._READ_
# CACHE deliberately - see _backfilled().
_BACKFILL_CACHE = {}


def _backfilled(path=None):
    """The pre-id rulings' word ids, re-read whenever the ledger changes.

    rd.backfilled_word_ids() is a full pass over the append-only log, and
    flag_answered_by_a_later_decision runs per flag per request - 290 open flags
    would otherwise re-parse a 4,400-line log 290 times.

    KEYED ON (mtime_ns, size), NOT ON PATH ALONE - corrected 2026-09-08, item
    0DE finding 3. This was an `lru_cache(maxsize=4)` on `path`, so one entry
    served the life of the process. review_server.py calls flag_still_open()
    with path=None, which meant EVERY request in a server's lifetime shared one
    snapshot: a `word_id_backfill` appended while the dashboard was up - by
    tools/backfill_word_ids.py in another terminal, or by an apply run - stayed
    invisible until restart, and flags stayed wrongly open or wrongly closed
    until then.

    Its previous docstring argued that was fine because the server re-execs
    under START_HERE.md's restart rule. THAT RULE IS ABOUT CODE. The ledger is
    DATA, and the server's standing contract is that it reads its source files
    fresh off disk on every request - which is exactly what rd._read_all()
    keys on (st_mtime_ns, st_size) to honour, in the module right next door.
    Caching the VALUE behind a live view is Lesson 39, one layer in from the two
    panes that lesson was written about.

    The log is append-only, so any write grows it and the stamp always moves.
    Same performance as before on a quiet ledger - one stat() per call - and it
    also removes a cross-test hazard: with an lru_cache, every test that
    redirected rd.DECISIONS_PATH and called flag_still_open() without an
    explicit `path` shared the `None` key with every earlier test.
    """
    # KEYWORD, not positional - the trap review_decisions.superseded_by_an_
    # applied_decision has its own comment about. The applier test harness
    # redirects the ledger by wrapping these readers and injecting
    # `path=<tmpdir>`, so a positional `path` arrives alongside that keyword and
    # raises "multiple values for argument 'path'". Walked into it 2026-09-07
    # despite the comment existing.
    resolved = rd._resolve(path)
    try:
        st = os.stat(resolved)
    except OSError:
        # No ledger yet: nothing to memoize, and nothing to serve stale either.
        return rd.backfilled_word_ids(path=path)
    stamp = (st.st_mtime_ns, st.st_size)
    cached = _BACKFILL_CACHE.get(resolved)
    if cached is not None and cached[0] == stamp:
        return cached[1]
    table = rd.backfilled_word_ids(path=path)
    _BACKFILL_CACHE[resolved] = (stamp, table)
    return table

def claim_word_index(corrections, word_index, overlay_key=None, overlay=None):
    """Return the entry already serving `word_index`, after optionally
    overlaying extra data onto it - or None if the index is free.

    THE RULE THIS ENFORCES, and why it is a helper rather than three copies:
    review_frontend/app.js builds its word map as
    `corrections.forEach(c => byIndex[c.word_index] = c)` - LAST WRITE WINS. So
    two entries at one word_index means the reviewer silently sees only the
    second, losing whatever the first carried: its bbox (no scan highlight at
    all), its readings, its vision verdict and confidence.

    api_klal() builds `corrections` from FOUR sources - machine candidates,
    manual_correction decisions, word-level klal_flags, and witness
    disagreements - and every source after the first must therefore check
    whether the index is already taken. Found 2026-08-24 by live review of klal
    91 (manual over machine), then by sweeping every klal, which turned up four
    more `replace+witness` collisions and one `ai_flag+witness`. Each source had
    grown its own partial guard (the flag and witness paths both checked
    `manual_word_indices` but not machine candidates), which is exactly the
    shape that leaves one combination uncovered.
    """
    existing = next((c for c in corrections
                     if c.get("word_index") == word_index and c.get("opcode") != "delete"),
                    None)
    if existing is not None and overlay_key is not None:
        existing[overlay_key] = overlay
    return existing

def merge_decision(entry, klal_id, decided):
    """Overlay the current human decision (if any) on top of a raw
    review_queue_part1.json entry - never mutates the source data, this is
    a display-time merge only.

    `decided` is one all_current("candidate_choice") map, built once by the
    caller. This used to call rd.current_for() per entry, and every such
    call re-reads and re-parses the WHOLE review_decisions.jsonl - so a
    klal with 11 candidates cost 11 full parses of the append-only log on
    every single /api/klal request, growing with the log forever. Same
    semantics either way (current_for and all_current both resolve a key to
    the last matching line in file order), just resolved once."""
    entry = dict(entry)
    entry["current_decision"] = decided.get((klal_id, entry["word_index"]))
    return entry


def flag_still_open(klal_id, word_index, rec, decided, manual_decisions, path=None):
    """Is this klal_flag record still asking for a human?

    A klal-level flag (word_index None) is open until someone clears it. A
    WORD-level flag is ALSO answered by a human decision recorded at that word
    after the flag was raised - see flag_answered_by_a_later_decision().

    Without the second half, clearing the klal-level flag could never turn the
    nav's pennant off while any word-level flag remained, which is what the
    reviewer hit on klal 163: cleared twice, still lit, no explanation.

    Was a closure inside api_klalim() until 2026-09-01; it is a rule about a
    record, not about a request, and word_states() needs the same answer.
    """
    if not rec.get("needs_revisit"):
        return False
    if word_index is None:
        return True
    return not flag_answered_by_a_later_decision(klal_id, word_index, rec,
                                                 decided, manual_decisions, path=path)


def machine_state(klal_id, entry, decided):
    """The state of one MACHINE candidate entry.

    A human decision always wins (this is app.js wordState()'s first test),
    otherwise a machine-resolved flag, otherwise nobody has looked at it yet.
    """
    if (klal_id, entry["word_index"]) in decided:
        return DECIDED
    return RESOLVED if entry.get("flag") in MACHINE_RESOLVED_FLAGS else DISPUTED


def word_states(klal_id, n_words, entries, witness_entries, *,
                manual_indices, open_flag_indices, answered_flag_indices,
                decided, witness_decided):
    """{word_index: state} for every word this klal actually RENDERS.

    api_klal() merges colliding entries via claim_word_index() - manual over
    candidate, flag over candidate, witness over candidate - so exactly ONE
    entry per word_index survives to be drawn. These states must describe that
    surviving entry, which is why this classifies in api_klal()'s own source
    order rather than adding up sources independently.

    FIXED 2026-08-24 (code review): the totals used to add every source
    independently, counting items the text pane never renders - nav 1,201 vs
    1,061 rendered across 88 klalim.
    FIXED 2026-08-25 (reviewer: "klal 88 shows -1 even though a few are
    outstanding"): that fix made only the NUMERATOR distinct and left the
    denominators summing their sources, so a word claimed by two of them - a
    witness decision at a position a manual_correction already covers, klal 88
    w327 - was counted once in the total and twice in decided, and open_count
    went NEGATIVE. Swept: 3 klalim (30, 88, 91) carried 6 such phantom
    decisions; only 88 had enough to cross zero. Two of klal 88's three came
    from witness rows whose word_index is None: never rendered, still counted.

    Keyword-only from `manual_indices` on, deliberately: this takes five
    same-shaped collections and a positional call site would be unreadable and
    silently mis-orderable.
    """
    state = {}

    for e in entries:                                    # 1. machine candidates
        if e.get("opcode") == "delete":
            continue                                     # no word_index slot of its own
        state[e["word_index"]] = machine_state(klal_id, e, decided)

    for wi in manual_indices:                            # 2. born decided
        state[wi] = DECIDED

    # 3. An OPEN flag makes the word disputed, overriding the machine's own
    # verdict for the entry it overlays. This was setdefault(), so a flag
    # landing on a `current_text_confirmed` candidate left the word counted AND
    # coloured machine-resolved - amber, "nothing to do here" - while the flag
    # underneath was still asking for a human. Seven words corpus-wide; the
    # reviewer hit two (klalim 62, 70: "two flagged words in the center but the
    # correction pane showed 1 red flag").
    #
    # A DECIDED word IS overridden too, and the `!= DECIDED` guard that used to
    # sit here was wrong on its own reasoning. flag_still_open() has ALREADY
    # removed every flag a later decision answered, so a flag reaching this loop
    # is one the decision did not answer - a fresh concern about an
    # already-decided word, which is precisely the case that must stay open.
    # app.js's wordState() has always tested `word_flag && !answered` BEFORE
    # `current_decision`, so the guard also made the nav disagree with the
    # screen; it simply never fired, because until 2026-09-02 no word carried
    # both an unanswered flag and a decision. Raising the review flags that
    # `ai-dropped-lamed-correction` promised and never wrote (item 0AT) created
    # the first two - klalim 92 and 124, the pair the reviewer had just
    # corrected against the ink - and the tri-state invariant caught it.
    for wi in open_flag_indices:
        state[wi] = DISPUTED

    # 3b. An ANSWERED flag still renders - it has to, or nothing on screen can
    # clear it - and it renders as human-decided, since a decision at that word
    # is what answered it. It usually overlays a richer entry and adds nothing;
    # it only stands alone when that entry is gone, which happens routinely:
    # synthesize_multi_witness.py drops a consensus dispute once a human has
    # decided the position, so the next rebuild removes the host. Measured on
    # the 2026-08-25 rebuild: 14 entries removed, 7 answered flags across
    # klalim 2/4/88/163/167 left standing alone. Counted DECIDED to match what
    # renders.
    for wi in answered_flag_indices:
        state.setdefault(wi, DECIDED)

    for w in witness_entries:                            # 4. witness disagreements
        wi = w.get("word_index")
        if wi is None or not (0 <= wi < n_words) or wi in manual_indices:
            continue                                     # not rendered - see api_klal()
        if wi in state:
            continue                                     # overlaid onto a richer entry
        # A witness item the vision pass called (A or B) renders GREEN - app.js's
        # wordState() treats a vision verdict on a witness exactly as it treats
        # `current_text_confirmed` on a candidate. This used to call every
        # undecided witness DISPUTED, which put klalim 30 and 75 on screen with
        # more green words than the nav badge admitted (6 and 2). Same
        # divergence class as `docai_ligature_artifact` in 2026-08-24's finding
        # F2: the screen is the ground truth, so the count follows it.
        if (klal_id, w["docai_token_index"]) in witness_decided:
            state[wi] = DECIDED
        elif w.get("vision_selected") in ("A", "B"):
            state[wi] = RESOLVED
        else:
            state[wi] = DISPUTED

    return state


def state_rows(klal_id, states, entries, decided):
    """Every item count_row() counts, as (word_index, state) pairs.

    `delete`-opcode entries have no word_index slot of their own (two of them
    can sit at the same index), so they are carried alongside the per-word
    states rather than inside them - the one place a count is not one-per-word.
    They still HAVE a word_index; what they lack is exclusive use of it, which
    is why they cannot live in the `states` dict.

    EXTRACTED 2026-09-01 so /api/word-states can enumerate the same items the
    legend counts. The legend now shows a count and offers a list behind it, and
    those two must be the same set or the list is a fifth encoding of the rule
    this module exists to hold once (see the header). count_row() is defined on
    this function for exactly that reason - not as a convenience.

    Sorted by word_index so the list a reviewer opens reads in text order.
    """
    rows = sorted(states.items())
    rows += [(e["word_index"], machine_state(klal_id, e, decided))
             for e in entries if e.get("opcode") == "delete"]
    return rows


def count_row(klal_id, states, entries, decided):
    """The four tri-state counts, from word_states()' output.

    The tri-state sums to the total BY CONSTRUCTION here, not by coincidence,
    which is the property test_nav_tristate_matches_what_each_word_actually_
    renders_as asserts.
    """
    all_states = [st for _wi, st in state_rows(klal_id, states, entries, decided)]
    total = len(all_states)
    decided_count = all_states.count(DECIDED)
    return {
        "correction_count": total,
        "decided_count": decided_count,
        # Served but no longer rendered: the nav badge switched to
        # machine_disputed_count on 2026-08-25 (see app.js's own note). NOT
        # Lesson 29's dead field, and deliberately kept - it is the arithmetic
        # canary for this logic, asserted by test_nav_tristate_matches_what_
        # each_word_actually_renders_as, which is what caught the klal 88 "-1"
        # fix-on-fix arc. If you remove it, remove that test's subject too, not
        # just the key.
        "open_count": total - decided_count,
        "machine_disputed_count": all_states.count(DISPUTED),
        "machine_resolved_count": all_states.count(RESOLVED),
    }
