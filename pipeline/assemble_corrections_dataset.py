# [PRODUCTION] Combine the vision-verified Part-1 correction candidates into the
# per-klal dataset the review dashboard consumes (review_server.py's /api/klal
# flag overlay - the static review.html this used to name was retired
# 2026-08-07): one entry per flagged word, with a human-readable flag
# classifying what the vision check implies.
import difflib
import json
import os
import sys
import re

import corpus_io as cio
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "repair_filters"))
import docai_filter
# The one definition of "a human already ruled here and it landed", shared rather
# than re-derived - the generator and the assembler must agree on it or a
# suppressed candidate reappears at the next stage, which is exactly what
# happened on klal 84 w0.
import build_corrections_dataset as bcd

# Moved one level deeper (pipeline/ or tools/) 2026-08-16 - REPO now goes up
# two levels, not one, to keep resolving to the actual repo root where
# part1.json/docai_word_boxes/etc. live.
REPO = cio.REPO
IN_PATH = os.path.join(REPO, "corrections_verified_part1.json")
OUT_PATH = os.path.join(REPO, "corrections_part1.json")
PART1_PATH = cio.PART1_PATH
# ADDED 2026-08-21 (PROJECT-STATUS.md, "surface the VLM baseline into the
# dashboard for review" - user-requested, "just enrich"): a THIRD,
# genuinely independent reading for every candidate this stage already
# serves - VlmWitnessEngine's blind, whole-klal transcription, diffed
# against the klal's own current clean_text (the same word-index space
# every candidate here already uses). Optional input: a fresh clone or a
# machine that hasn't run tools/run_part1_vlm_full_baseline.py (a paid API
# script, not part of rebuild_all.sh) simply gets vlm_reading: null
# everywhere rather than a crash - see load_vlm_baseline()'s own docstring.
VLM_BASELINE_PATH = os.path.join(REPO, "tools", "second_witness_eval", "vlm_part1_full_baseline.txt")
SURYA_BASELINE_PATH = os.path.join(REPO, "tools", "second_witness_eval", "surya_part1_full_baseline.txt")
# Written by pipeline/synthesize_multi_witness.py (stage 4a). Absent on a
# fresh clone or before the synthesizer has run - merged if present, skipped
# if not, never a hard dependency.
CONSENSUS_PATH = os.path.join(REPO, "consensus_disputes_part1.json")
LEXICAL_PATH = os.path.join(REPO, "lexical_defect_report.json")

# A lexical-defect entry reaches the REVIEWER only if its proposed reading is
# attested at least this often in the independent reference corpus, and the
# stored form occurs only once here. Both conditions together are what make the
# tier sharp; either alone is mostly noise.
#
# Deliberately conservative, and the number is the knob. Measured 2026-08-26 over
# the 563 unreviewed positions in this class: >=500 gives 59 positions across 42
# klalim (+5% on a 1,070-entry queue), >=200 gives 111, >=40 gives 219, and no
# floor at all gives all 563 - a 53% larger queue of material nobody has read.
# The whole set stays in lexical_defect_report.json either way; this governs what
# is put in front of a human, not what is found.
REVIEW_MIN_REF = 500
REVIEW_MAX_CORPUS_COUNT = 1

# Minimum vision confidence before classify() treats Gemini's A/B selection as
# a machine resolution rather than "ambiguous, a human still has to look".
# Named 2026-08-15: it was the bare literal 0.7 written out three separate
# times inside classify(), and the one place it was MISSING (the 'replace'
# branch, which trusted any confidence at all) is exactly the asymmetry bug
# fixed 2026-08-13, PROJECT-STATUS.md finding 8. Three independent copies of a
# threshold is how one of them gets updated and the others don't.
# Per CLAUDE.md Lesson 2 this is a triage threshold, not a certificate: a
# candidate scoring above it has been prioritised, not proven correct.
MIN_VISION_CONFIDENCE = 0.7


def load_vlm_baseline(path=VLM_BASELINE_PATH):
    """{klal_id: [word, ...]} from tools/run_part1_vlm_full_baseline.py's
    output - a blind, whole-klal transcription per klal, genuinely
    independent of the DocAI-vs-stored-text comparison every candidate here
    already comes from (see PROJECT-STATUS.md, 2026-08-21, "the VLM A/B
    passes... surface the better readings into the dashboard"). Same header
    format both baseline passes (A and B) write: "=== KLAL N (...) ===".
    Returns {} - not an error - if the file doesn't exist, so a fresh clone
    or a machine that hasn't run the (paid-API, not rebuild_all.sh-gated)
    baseline script yet still assembles correctly, just without VLM
    enrichment."""
    if not os.path.exists(path):
        return {}
    by_klal = {}
    current_klal = None
    lines = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^===\s*KLAL\s+(\d+)", line)
            if m:
                if current_klal is not None:
                    by_klal[current_klal] = " ".join(lines).split()
                    lines = []
                current_klal = int(m.group(1))
            elif current_klal is not None:
                lines.append(line.strip())
        if current_klal is not None:
            by_klal[current_klal] = " ".join(lines).split()
    return by_klal


def build_vlm_alignment(klal_words, vlm_words):
    """clean_text word_index -> the witness's own word at that position.

    FIXED 2026-08-23 (code review, finding C15). This used to walk
    SequenceMatcher.get_matching_blocks() alone - and a matching block is BY
    DEFINITION a run where the two sequences are equal, so every value it
    returned was just the corpus's own word handed back. Measured before the
    fix: 49,138 aligned VLM words and 34,892 aligned Surya words, ZERO
    divergent in either. The `vlm_reading`/`surya_reading` fields this feeds
    were therefore structurally incapable of ever showing the disagreement
    they were added to surface, and review_frontend/app.js's "only offer it if
    it says something new" dedupe then dropped every one of them, so the
    option never rendered at all.

    Now delegates to corpus_io.align_witness, which additionally reports an
    unambiguous 1:1 substitution as a real differing reading while still
    refusing to pair words positionally inside a ragged replace block
    (Lesson 5). Kept as a named wrapper because three call sites and the
    existing unit tests refer to it, and because "the alignment used by the
    corrections assembler" is worth a name of its own."""
    return {wi: reading for wi, (reading, _verdict)
            in cio.align_witness(klal_words, vlm_words).items()}


def _ligature_artifact_flag(c, repaired="__derive__"):
    """"docai_ligature_artifact" when repairing DocAI's reading makes it EXACTLY
    the stored text, else None.

    This is the safest criterion available and deliberately not a judgement
    call: the candidate exists only because DocAI's raw output differed from the
    corpus, and if restoring one known-dropped `ל` makes the two identical then
    the disagreement was the ligature and nothing else. There is no reading to
    choose between, so there is nothing for a reviewer to adjudicate.

    Measured 2026-08-24: 118 of 498 Part-1 candidates (24%) are this - a quarter
    of the review queue that never should have been in it. Flagged rather than
    DELETED, per Lesson 26: a filter that removes items from a reviewer's view
    must leave them findable and say why it acted."""
    # `repaired` is passed in by the one production caller, which has already
    # derived it for the entry's own "docai_repaired" field - deriving it twice
    # per candidate was ~498 redundant repairs per rebuild (code review
    # 2026-08-26, H16). Defaulted rather than made required so the tests, which
    # call this with a bare candidate dict, keep working.
    if repaired == "__derive__":
        repaired = docai_filter.repair_word(c.get("original_word"))
    if not repaired:
        return None
    stored = c.get("corrected_word")
    if stored and cio.hebrew_letters_only(repaired) == cio.hebrew_letters_only(stored):
        return "docai_ligature_artifact"
    return None


def merge_consensus_disputes(by_klal, path=CONSENSUS_PATH):
    """Fold pipeline/synthesize_multi_witness.py's output into this stage's
    own, so a rebuild REGENERATES multi-witness disputes instead of deleting
    them.

    ADDED 2026-08-23 (code review, finding C1). The two scripts this replaces
    (tools/extract_{vlm,surya}_consensus_disputes.py) delivered the same kind
    of finding by opening corrections_part1.json - this stage's OUTPUT - and
    appending to it. 1,108 items lived there, and every one of them, plus any
    human review time spent on them, was destroyed by the next ./rebuild_all.sh
    run. A witness contributes a source file the pipeline reads; it never
    edits the pipeline's own product.

    Two cases, deliberately kept distinct:
      * A position that ALREADY has a candidate (DocAI disagreed there, so
        this stage built one from the verified set) is ENRICHED - it gains
        the corroborating engines, not a duplicate row.
      * A position with no candidate (DocAI agreed with the corpus, but two
        other engines agree it is wrong) becomes a NEW entry. This is the
        genuinely new signal multi-witness synthesis adds: a disagreement the
        DocAI-vs-stored diff cannot see by construction.

    Missing file is not an error - the synthesizer may not have run yet on a
    fresh clone, same contract as load_vlm_baseline()."""
    consensus = cio.load_json(path, default={}) or {}
    n_new = n_enriched = 0

    for kid_str, items in consensus.items():
        existing = {e["word_index"]: e for e in by_klal.get(kid_str, [])}
        for d in items:
            engines = d.get("agreeing_engines", [])
            witnesses = d.get("witnesses", {})
            note = (f"Multi-witness consensus: {' + '.join(engines)} agree on "
                    f"'{d['consensus_reading']}' against stored '{d['final_text']}'.")
            artifact = d.get("ligature_artifact")
            if artifact:
                # The engines agree because they share ONE printing defect, not
                # because they independently corroborate each other. Carried
                # through so the dashboard can say so rather than showing a
                # reviewer "3 engines agree" for a known ink artifact.
                note += (f" NOTE: explainable as the catalogued '{artifact}' printer "
                         f"ligature artifact - a shared ink defect, so this agreement "
                         f"is NOT independent corroboration and the stored text is "
                         f"most likely correct.")
            prior = existing.get(d["word_index"])
            if prior is not None:
                prior["consensus_engines"] = engines
                prior["consensus_reading"] = d["consensus_reading"]
                prior["ligature_artifact"] = artifact
                n_enriched += 1
                continue
            by_klal.setdefault(kid_str, []).append({
                "word_index": d["word_index"],
                "opcode": "replace",
                # C2: these are what each engine ACTUALLY read, or None where
                # it was not consulted / had no usable reading. Never the
                # corpus's own word standing in for an engine that never ran.
                "docai_reading": witnesses.get("docai"),
                "final_text": d["final_text"],
                "page": d.get("page"),
                "bbox": d.get("bbox"),
                "vision_selected": None,
                "vision_transcription": None,
                "confidence": None,
                "reasoning": note,
                "vlm_reading": witnesses.get("vlm"),
                "surya_reading": witnesses.get("surya"),
                "consensus_engines": engines,
                "consensus_reading": d["consensus_reading"],
                "ligature_artifact": artifact,
                "flag": "current_text_may_be_wrong",
            })
            n_new += 1

    for items in by_klal.values():
        items.sort(key=lambda e: e["word_index"])
    return n_new, n_enriched


def merge_lexical_defects(by_klal, path=LEXICAL_PATH,
                          min_ref=REVIEW_MIN_REF, max_count=REVIEW_MAX_CORPUS_COUNT):
    """Fold the sharpest tier of pipeline/build_lexical_defect_report.py into the
    review queue, so those words are actually REVIEWABLE instead of only listed.

    ADDED 2026-08-26 (reviewer: "are the 384 words flagged? how can i review?").
    They were not: 563 positions across 143 klalim had no way to reach a human.
    The two lexical detectors had been run, their findings written to a report,
    and the report shown to nobody - the same gap that let the reviewer hand-repair
    a word in klal 84 that a detector had already found.

    A DERIVED SOURCE, NOT A FLAG. These entries are regenerated by every rebuild
    and vanish when the corpus changes under them, exactly like the multi-witness
    disputes above - nothing is written to the append-only ledger, so widening or
    narrowing the tier costs nothing and leaves no residue. That distinction is
    the whole reason this is here rather than in review_decisions.jsonl: this
    material is UNREAD, and 563 permanent flags on unread material is how the
    1,496-flag queue happened (PROJECT-STATUS item 1).

    A position that already carries a candidate is left alone - the richer entry
    wins, and a second row at the same word_index would shadow it under app.js's
    last-write-wins map."""
    report = cio.load_json(path, default=[]) or []
    import review_decisions as rd
    # The same scan-alignment machinery synthesize_multi_witness reuses (its own
    # note explains why hand-rolling it produced 260 wrong bboxes).
    #
    # This used to be `import review_server as _rs`, deliberately INSIDE the
    # function, with the comment "so the module does not pull in the HTTP server
    # just to be imported" - a lazy import working around a dependency that
    # should never have existed. scan_alignment.py (2026-09-01, finding C4) is
    # that dependency removed rather than deferred, so the import can be
    # ordinary. Kept local only to keep this diff to the coupling itself.
    import scan_alignment as _sa
    _scan_position = _sa.word_scan_position
    klalim_by_id = {k["klal_id"]: k for k in cio.load_part1_sorted()}
    decided = {k for k in rd.all_current("manual_correction")}
    decided |= {k for k in rd.all_current("candidate_choice")}
    decided |= {k for k in rd.all_current("disputed_choice")}
    n = 0
    for d in report:
        if d.get("ambiguous"):
            continue                      # more than one answer clears the bar: report only
        if d.get("rank", 0) < min_ref or d.get("corpus_count", 99) > max_count:
            continue
        kid_str = str(d["klal_id"])
        existing = {e["word_index"] for e in by_klal.get(kid_str, [])}
        if d["word_index"] in existing:
            continue
        if (d["klal_id"], d["word_index"]) in decided:
            # A human has already ruled here. Adding an entry would collide with
            # their decision in app.js's last-write-wins map and hide it - the
            # same reason synthesize_multi_witness drops a dispute once decided.
            continue
        prop = (d.get("proposals") or [{}])[0]
        # Give the entry its real scan position. Without it api_page() cannot
        # place the entry on a page, so it falls through to the plain-word pass
        # and the word renders on the scan as ordinary prose rather than as the
        # flagged word it is - and a click navigates to the klal's START page,
        # which is wrong for any word past a page break (reviewer: klal 179 w267,
        # on page 67 of a klal that starts on 66). Same helper the server uses to
        # answer that question everywhere else.
        page, bbox = None, None
        words = cio.words_of(klalim_by_id.get(d["klal_id"], {}))
        if words:
            bbox, page = _scan_position(d["klal_id"], words, d["word_index"])
        note = (f"Lexical defect: stored '{d['stored']}' has NO attestation in the "
                f"independent reference corpus and occurs {d['corpus_count']}x here, while "
                f"'{prop.get('form')}' is attested {prop.get('ref_count')}x and is one "
                f"{prop.get('edit')} away. Found by tools/detect_"
                f"{'real_word_substitution' if d['detector'] == 'substitution' else 'insertion_deletion'}.py. "
                f"FREQUENCY EVIDENCE ONLY - not scan-verified and not corroborated by "
                f"another engine; read the context before acting.")
        by_klal.setdefault(kid_str, []).append({
            "word_index": d["word_index"],
            "opcode": "replace",
            "docai_reading": None,
            "final_text": d["stored"],
            "page": page,
            "bbox": bbox,
            "vision_selected": None,
            "vision_transcription": None,
            "confidence": None,
            "reasoning": note,
            "vlm_reading": None,
            "surya_reading": None,
            # A RENDERABLE, ATTRIBUTED proposal. Not `vision_transcription` or any
            # engine field: no engine read this. It comes from a frequency table
            # and a dictionary, and saying otherwise would be the "corpus's own
            # word standing in for an engine that never ran" mistake the consensus
            # merge above warns about. app.js offers it as its own option card and
            # labels it as such; test_correction_entries_have_the_field_shape_
            # their_opcode_implies accepts it as an alternative BECAUSE of
            # lexical_source, which is its attribution - the same role
            # consensus_engines plays for a consensus dispute.
            "lexical_proposal": prop.get("form"),
            "lexical_source": ("detect_real_word_substitution.py"
                               if d["detector"] == "substitution"
                               else "detect_insertion_deletion.py"),
            "flag": "current_text_may_be_wrong",
        })
        n += 1
    for items in by_klal.values():
        items.sort(key=lambda e: e["word_index"])
    return n


def live_word_span(words, word_index, expected_text):
    """Same span logic as apply_reviewer_decisions.py's apply_replace(): a
    multi-word corrected_word occupies word_index..word_index+n in the
    whitespace-split clean_text. Returns the live span, or None if
    word_index is out of range."""
    span_len = len(expected_text.split()) if expected_text else 1
    if word_index < 0 or word_index + span_len > len(words):
        return None
    return words[word_index:word_index + span_len]


def check_drift(c, klal_words):
    """A candidate was generated against a snapshot of part1.json at build
    time. If part1.json has since changed at this position (another fix,
    a punctuation pass, a reindexing bug - see PROJECT-STATUS.md's
    reindexing incident) the candidate's word_index/corrected_word can go
    stale while corrections_verified_part1.json still serves the old
    values as if current. Only 'replace' and 'insert' have a non-null
    corrected_word to check against live text; 'delete' proposes a word
    that by definition isn't in final_text, so there's nothing at
    word_index to compare it to - only bounds-check it."""
    op = c["opcode"]
    idx = c["word_index_in_final_text"]
    if klal_words is None:
        return True  # klal_id not in current part1.json at all
    if op in ("replace", "insert"):
        expected = c["corrected_word"]
        live = live_word_span(klal_words, idx, expected)
        if live is None:
            return True
        return " ".join(live) != (expected or "")
    if op == "delete":
        return idx < 0 or idx > len(klal_words)
    return False


def classify(c):
    op = c["opcode"]
    sel = c.get("vision_selected")
    conf = c.get("vision_confidence")

    # ORTHOGRAPHY FIRST, before any vision verdict is consulted. ADDED 2026-08-31
    # (reviewer, klal 36 w61: "cof is impossible here, would be cof sofit"). A
    # proposed reading ending in a plain form of a letter that Hebrew writes
    # differently at a word end cannot be what the page says, whatever a model
    # scored it - so the stored text stands and this is a machine resolution, not
    # a dispute to put in front of a human. `impossible_final_form` exempts
    # abbreviations, which do not obey the rule (see its docstring).
    # Measured when added: 7 candidates carried such a reading, 6 after the
    # abbreviation exemption, and klal 74 w966 was still OPEN - asking a reviewer
    # to weigh `בארוכ` against the correct `בארוכה`.
    if op in ("replace", "delete") and cio.impossible_final_form(c.get("original_word")):
        return "current_text_confirmed" if op == "replace" else "ambiguous"

    if op == "replace":
        # FIXED 2026-08-13 (PROJECT-STATUS.md finding 8): 'delete' below
        # gates on MIN_VISION_CONFIDENCE before trusting a selection; this
        # branch used to trust A/B at any confidence, including a
        # low-confidence guess - asymmetric for no principled reason.
        # Currently inert (all 214 live replace candidates score >= 0.7),
        # but a future low-confidence replace would otherwise sail through
        # as if it were a confident machine resolution.
        if sel == "A":
            return "current_text_may_be_wrong" if conf and conf >= MIN_VISION_CONFIDENCE else "ambiguous"
        if sel == "B":
            return "current_text_confirmed" if conf and conf >= MIN_VISION_CONFIDENCE else "ambiguous"
        if sel == "UNCERTAIN":
            return "ambiguous"
        return "error"
    if op == "delete":
        if sel == "A" and conf and conf >= MIN_VISION_CONFIDENCE:
            return "possible_omission"
        if sel == "ERROR":
            return "error"
        return "ambiguous"
    if op == "insert":
        return "unverified_insertion"
    return "unverified"


def main():
    verified = cio.load_json(IN_PATH)
    part1 = cio.load_part1(PART1_PATH)
    words_by_klal = {k["klal_id"]: k["clean_text"].split() for k in part1}
    vlm_by_klal = load_vlm_baseline(VLM_BASELINE_PATH)
    surya_by_klal = load_vlm_baseline(SURYA_BASELINE_PATH)
    # Built lazily, once per klal actually needed (not all 222) - the
    # alignment itself is cheap, but no reason to pay for klalim with zero
    # candidates.
    vlm_alignment_cache = {}
    surya_alignment_cache = {}

    def vlm_reading_for(klal_id, word_index):
        if klal_id not in vlm_by_klal:
            return None
        if klal_id not in vlm_alignment_cache:
            vlm_alignment_cache[klal_id] = build_vlm_alignment(
                words_by_klal.get(klal_id, []), vlm_by_klal[klal_id])
        return vlm_alignment_cache[klal_id].get(word_index)

    def surya_reading_for(klal_id, word_index):
        if klal_id not in surya_by_klal:
            return None
        if klal_id not in surya_alignment_cache:
            surya_alignment_cache[klal_id] = build_vlm_alignment(
                words_by_klal.get(klal_id, []), surya_by_klal[klal_id])
        return surya_alignment_cache[klal_id].get(word_index)

    by_klal = {}
    n_drifted = 0
    # A position a human has already ruled on and had APPLIED must not come back
    # as a candidate. build_corrections_dataset.py drops those when it GENERATES,
    # but corrections_verified_part1.json is cumulative - it keeps every entry the
    # vision stage ever verified - so an entry generated before the decision was
    # applied survives in it and gets re-assembled here.
    #
    # FIXED 2026-08-31, caught by test_no_candidate_re_raises_a_word_an_applied_
    # decision_already_settled on klal 84 w0: the reviewer confirmed the klal
    # marker `פד` against DocAI's `פר`, it was applied, and the next rebuild put
    # the same question back in front of them. That is item 35's defect one layer
    # below where it was fixed - the generator was taught, the assembler was not.
    n_settled_dropped = 0
    settled = bcd.settled_by_an_applied_decision({k["klal_id"]: k for k in part1})
    for c in verified:
        if (c["klal_id"], c.get("word_index_in_final_text")) in settled:
            n_settled_dropped += 1
            continue
        drifted = check_drift(c, words_by_klal.get(c["klal_id"]))
        # Derived once and used twice - for the entry's own "docai_repaired" and
        # by _ligature_artifact_flag() below, which used to re-derive it from the
        # same input (~498 redundant repairs per rebuild; code review 2026-08-26).
        _repaired = docai_filter.repair_word(c["original_word"])
        entry = {
            "word_index": c["word_index_in_final_text"],
            "opcode": c["opcode"],
            "docai_reading": c["original_word"],
            # ADDED 2026-08-24 (plan §3.2, built after being specified since the
            # first draft). The RAW DocAI reading above is never overwritten -
            # success criterion #1 forbids silent normalisation, and the reviewer
            # must be able to see what the engine actually produced. This is the
            # same reading with the alef-lamed ligature's dropped `ל` restored,
            # offered alongside it. Measured against a reviewer's complete
            # 22-decision review of klal 91: DocAI 0/18 raw, 17/18 (94%) repaired,
            # zero words made worse.
            "docai_repaired": _repaired,
            "final_text": c["corrected_word"],
            "page": c["page"],
            "bbox": c["bbox"],
            "vision_selected": c.get("vision_selected"),
            "vision_transcription": c.get("vision_transcription"),
            "confidence": c.get("vision_confidence"),
            "reasoning": c.get("vision_reasoning"),
            "vlm_reading": vlm_reading_for(c["klal_id"], c["word_index_in_final_text"]),
            "surya_reading": surya_reading_for(c["klal_id"], c["word_index_in_final_text"]),
            # A drifted candidate's flag is forced to "stale_candidate"
            # rather than whatever classify() would say - a confident
            # "current_text_confirmed" is actively misleading once the
            # candidate no longer points at the text it was verified
            # against (see PROJECT-STATUS.md's reindexing incident, the
            # exact failure this closes). review_frontend/app.js treats
            # any flag other than "current_text_confirmed" as its default
            # "open" state, so this is safe to introduce without a
            # frontend change.
            "flag": ("stale_candidate" if drifted
                     else _ligature_artifact_flag(c, _repaired) or classify(c)),
        }
        if drifted:
            n_drifted += 1
        by_klal.setdefault(str(c["klal_id"]), []).append(entry)

    # F10 (code review 2026-08-24): the ligature filter depends on
    # sefaria_reference_corpus/word_freq.json, which is GITIGNORED. Without it
    # repair_word() returns None for everything, so this stage silently produces
    # a materially different reviewer queue - 118 items flagged
    # current_text_may_be_wrong instead of docai_ligature_artifact, and no
    # repaired-reading option anywhere - with no indication that anything was
    # skipped. A clone would look correct and quietly hand its reviewer a
    # quarter more work. Say so loudly instead.
    if not docai_filter.reference_frequencies():
        print("WARNING: sefaria_reference_corpus/word_freq.json is absent - the DocAI "
              "alef-lamed ligature repair is DISABLED for this run.")
        print("         ~118 Part-1 candidates that are pure ligature artifacts will be "
              "served as open disputes, and no repaired reading will be offered.")
        print("         See SETUP.md for how to obtain the reference corpus.")

    n_new, n_enriched = merge_consensus_disputes(by_klal)
    n_lex = merge_lexical_defects(by_klal)

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(by_klal, f, ensure_ascii=False, indent=2)

    flags = {}
    for entries in by_klal.values():
        for e in entries:
            flags[e["flag"]] = flags.get(e["flag"], 0) + 1
    if n_settled_dropped:
        print(f"  {n_settled_dropped} verified entry(ies) dropped: a human decision was already "
              f"APPLIED at that word, so re-serving it would ask them to rule on their own fix")
    print(f"Wrote {OUT_PATH}: {sum(len(v) for v in by_klal.values())} items across {len(by_klal)} klalim")
    print(f"  multi-witness consensus: {n_new} new dispute(s), {n_enriched} existing candidate(s) enriched")
    print(f"  lexical defects (unattested word, one edit from a common one): {n_lex} new entry(ies)")
    print("By flag:", flags)
    if n_drifted:
        print(f"WARNING: {n_drifted} candidate(s) drifted from live part1.json content - "
              f"flagged 'stale_candidate', not served as their computed classification.")


if __name__ == "__main__":
    main()
