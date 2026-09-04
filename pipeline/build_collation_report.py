#!/usr/bin/env python3
# [PRODUCTION] Where ANOTHER EDITION of this work reads differently - recorded
# as collation, never as a correction.
#
# WHY THIS IS A SEPARATE ARTIFACT FROM THE DISPUTE QUEUE. Every other witness in
# this pipeline (DocAI, Surya, the VLM) reads the SAME INK: the Berlin 1851
# square scan. When they disagree, exactly one of them is misreading, so the
# question is "what does the ink say" and the remedy is a correction. Dicta reads
# the Jerusalem 1975/6 Rashi edition - a DIFFERENT PRINTING. When it disagrees,
# there are three possibilities, not one:
#
#   1. the Berlin corpus misread the ink       -> a correction (dispute queue)
#   2. Dicta misread ITS ink                    -> noise
#   3. the two PRINTINGS genuinely differ       -> collation, and not an error
#      at all
#
# Correcting case 3 would edit the Berlin text to match a different edition -
# directly against success criterion #1 ("no paraphrase, no silent
# normalization"). It is also the defect item 0AQ found running the other way:
# the corpus was carrying `ומתיר` where the ink reads the abbreviation `ומתי׳`,
# and the reviewer ruled for the ink. So a cross-edition reading must never
# reach the correction queue - but it is genuinely interesting, and this file is
# where it goes.
#
# HOW CASE 1 IS SEPARATED FROM CASE 3, mechanically: by asking the engines that
# read the BERLIN ink. If Surya or the VLM ALSO differ from the corpus, the
# Berlin reading itself is in doubt -> that is stage 4a's dispute, not ours. If
# every Berlin-reading engine AGREES with the corpus, then the Berlin ink is
# settled and Dicta is describing the OTHER edition.
#
# WHAT THIS FILE DELIBERATELY DOES NOT REPORT. Measured 2026-09-04 over klalim
# 2-221: 943 positions have Dicta alone differing, and they are NOT mostly
# edition variants - Dicta is 95.6% accurate, so ~4% of ~50,000 aligned
# positions is ~2,000 expected misreads and 943 is consistent with mostly noise.
# Checked directly: of the 68 that differ only by a vav/yod swap, DICTA's reading
# is unattested in 6.18M words of independent Hebrew 24 times against Berlin's 4
# - roughly 6:1 that Dicta is the one erring (`הטור`->`הטיר`, 0x attested;
# `אותו`->`איתו`, 9384x vs 1x). Emitting all 943 as "variants" would be a
# low-precision queue dressed as scholarship.
#
# So only the STRUCTURALLY VERIFIABLE class is reported: the Berlin word ends in
# a geresh and the Jerusalem word continues the same letters. That is not a
# guess about which is right - it is the same word, abbreviated in one printing
# and spelled out in the other, and the shape itself is the evidence. Scored
# against the independent corpus for confirmation, not for selection: 67 of 74
# expansions are attested words (91%).
#
# This is also the layer CASE-YAD-MALACHI.md already wants - abbreviation
# expansion as a read-time overlay rather than something baked into the prose -
# sourced from a real edition instead of guessed.
import json
import os
import sys

INSTALL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(INSTALL_DIR, "pipeline"))
sys.path.insert(0, os.path.join(INSTALL_DIR, "tools"))

import corpus_io as cio  # noqa: E402
import synthesize_multi_witness as smw  # noqa: E402
import typography  # noqa: E402

OUT_PATH = cio.repo_path("collation_report.json")
DICTA_PATH = cio.repo_path("tools", "second_witness_eval",
                           "dicta_jerusalem_part1_baseline.txt")

def _berlin_verdicts(words, klal_id, surya, vlm_a, vlm_b):
    """Each Berlin-ink engine's verdict at each word index.

    The VLM's stability gate is stage 4a's, reused rather than re-invented: if
    pass A and pass B read a position differently, that single witness abstains
    there instead of voting twice (rule 1 of synthesize_multi_witness).
    """
    out = {}
    a_s = cio.align_witness(words, surya[klal_id]) if klal_id in surya else {}
    a_v = cio.align_witness(words, vlm_a[klal_id]) if klal_id in vlm_a else {}
    a_vb = cio.align_witness(words, vlm_b[klal_id]) if klal_id in vlm_b else {}
    for i in set(a_s) | set(a_v):
        verdicts = []
        if i in a_s:
            verdicts.append(("surya", a_s[i][1]))
        if i in a_v and not (i in a_vb and a_v[i][0] != a_vb[i][0]):
            verdicts.append(("vlm", a_v[i][1]))
        if verdicts:
            out[i] = verdicts
    return out


def load_berlin_engines():
    """The three Berlin-ink baselines. Kept OUT of collate() on purpose: the
    decision logic below is what needs testing, and a test that had to
    materialize the real 220-klal baselines to exercise it would only ever run
    against whatever today's corpus happens to contain (Lesson 36)."""
    return (smw.load_baseline(smw.SURYA_PATH), smw.load_baseline(smw.VLM_A_PATH),
            smw.load_baseline(smw.VLM_B_PATH))


def load_reference_freq():
    freq = cio.load_json(
        cio.repo_path("sefaria_reference_corpus", "word_freq.json"), {}) or {}
    if isinstance(freq, dict) and "freq" in freq:
        freq = freq["freq"]
    return freq


def collate(part1, witness_by_klal, edition_label, berlin_engines, freq):
    """Positions where the other edition spells out what this one abbreviates."""
    surya, vlm_a, vlm_b = berlin_engines
    rows = []
    for klal in part1:
        kid = klal["klal_id"]
        if kid not in witness_by_klal:
            continue
        words = cio.words_of(klal)
        berlin = _berlin_verdicts(words, kid, surya, vlm_a, vlm_b)
        for i, (other_word, verdict) in cio.align_witness(
                words, witness_by_klal[kid]).items():
            if verdict != "differs":
                continue
            # The Berlin ink must be SETTLED for this to be about the edition
            # rather than about a misread - see this module's header.
            here = berlin.get(i)
            if not here or not all(v == "agrees" for _, v in here):
                continue
            stored = words[i]
            # The shape test lives in typography.abbreviation_expansion,
            # SHARED with stage 4a - which uses the same predicate to warn a
            # reviewer when a consensus would expand an abbreviation. Two
            # copies of this rule would drift apart (Lesson 13).
            base = typography.abbreviation_expansion(stored, other_word)
            if base is None:
                continue
            rows.append({
                "klal_id": kid,
                "word_index": i,
                "this_edition": stored,
                "other_edition": other_word,
                "expansion_of": base,
                "other_edition_label": edition_label,
                "berlin_engines_agreeing": [n for n, _ in here],
                # Corroboration, NOT the selection rule: the shape already
                # established these are the same word. This says whether the
                # expanded form is one the language actually uses.
                #
                # `null`, not 0, when there is no reference corpus to ask. The
                # sefaria_reference_corpus cache is gitignored, so on a fresh
                # clone every count would otherwise be 0 and the report would
                # read "0% attested" - a confident claim of UNattestedness
                # sourced from an empty lookup table (Lesson 25: a check that
                # cannot distinguish absent from negative has checked nothing).
                "expansion_attested": (
                    freq.get(cio.hebrew_letters_only(other_word), 0)
                    if freq else None),
                # Said out loud on every row, because this file sits next to
                # files that ARE correction queues.
                "kind": "edition_variant",
                "actionable": False,
            })
    rows.sort(key=lambda r: (r["klal_id"], r["word_index"]))
    return rows


MD_PATH = cio.repo_path("EDITION-VARIANTS.md")


def write_md(path, rows, payload, prev, hebrew="visual"):
    """A readable rendering of the same rows.

    Written because the JSON alone would be Lesson 32: a report whose whole
    value is that a PERSON reads it, in a format no person reads. Same
    visual-order convention as DICTA-NEW-DISPUTES.md, for the same reason (the
    terminal renderers in use here run no bidi algorithm).

    Deliberately NOT linked into the review dashboard. Every other report in
    this repo that a reviewer opens is a queue of things to decide; putting
    these 74 beside them would invite exactly the ruling this file exists to
    prevent.
    """
    iso = (hebrew == "logical")
    L = ["# Where the Jerusalem edition spells out what Berlin abbreviates", ""]
    if hebrew == "visual":
        L += ["> **Hebrew below is in VISUAL order**, reordered so it reads "
              "correctly in a terminal renderer that does no bidi (`glow`). "
              "**Do not copy Hebrew out of this file** - it will paste reversed.",
              ""]
    L += ["**This is collation, not a correction queue. Nothing here is a "
          "defect and nothing here may be applied.** The corpus transcribes "
          f"{payload['this_edition']}; these rows describe a DIFFERENT printing "
          f"({payload['other_edition']}). Where Berlin prints an abbreviation, "
          "the Berlin abbreviation is what the corpus must keep - that is what "
          "the reviewer ruled in item 0AQ.",
          "",
          "Only positions where **every Berlin-reading engine agrees with the "
          "corpus** are listed, so the Berlin ink is not in question at any of "
          "them. The far larger set of cross-edition differences is deliberately "
          "excluded as mostly Dicta's own misreads - see the header of "
          "`pipeline/build_collation_report.py` for the measurement.",
          ""]
    scored = [r for r in rows if r["expansion_attested"] is not None]
    att = sum(1 for r in scored if r["expansion_attested"])
    L += ["| | |", "|---|---:|",
          f"| expansions found | {len(rows)} |",
          f"| klalim they fall in | {len(set(r['klal_id'] for r in rows))} |"]
    if scored:
        L.append(f"| …whose expanded form is attested in independent Hebrew | "
                 f"{att} of {len(scored)} ({att / len(scored):.0%}) |")
    else:
        L.append("| attestation | not scored (no reference corpus) |")
    # One bullet per row rather than a table: in visual mode the bidi
    # reordering is applied to the WHOLE LINE, so a table row's `|` separators
    # and its numbers get carried across the Hebrew and the columns come out
    # transposed. DICTA-NEW-DISPUTES.md uses bullets for the same reason.
    L += [""]
    last = None
    for r in rows:
        if r["klal_id"] != last:
            last = r["klal_id"]
            L += ["", f"### klal {last}", ""]
        n = r["expansion_attested"]
        n = ("attestation not scored" if n is None else
             (f"attested {n:,} time{'' if n == 1 else 's'}" if n
              else "**attested 0 times**"))
        L.append(f"- word {r['word_index']}: Berlin "
                 f"{prev.rtl(r['this_edition'], iso)} - Jerusalem "
                 f"{prev.rtl(r['other_edition'], iso)} ({n})")
    L += ["",
          "An expansion attested **0** times is most likely Dicta misreading "
          "Berlin's own geresh as a letter (`\u05e1\u05d9\u05f3` read as "
          "`\u05e1\u05d9\u05d9`), not a real difference between the "
          "printings. Those rows are kept rather than dropped because the "
          "attestation count is corroboration here, not the selection rule.",
          ""]
    if hebrew == "visual":
        L = prev.to_visual(L)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
        f.flush()
    return path


def main():
    sys.path.insert(0, os.path.join(INSTALL_DIR, "tools"))
    import preview_dicta_disputes as prev

    part1 = cio.load_part1_sorted()
    if not os.path.exists(DICTA_PATH):
        print(f"  {DICTA_PATH} absent - no second edition to collate against.")
        print("  This is not 'no variants found'; nothing was compared.")
        return
    witness = prev.witness_by_klal(DICTA_PATH, part1)
    freq = load_reference_freq()
    rows = collate(part1, witness, "Jerusalem 1975/6 (Rashi script), via Dicta",
                   load_berlin_engines(), freq)

    attested = sum(1 for r in rows if r["expansion_attested"])
    payload = {
        "this_edition": cio.WORK_EDITION,
        "other_edition": "Jerusalem 1975/6 (Rashi script), via Dicta RashiOCR",
        "kind": "collation - NOT a correction queue",
        "note": ("Where the other printing spells out a word this one abbreviates. "
                 "These are NOT errors and must never be applied to the corpus: "
                 "the Berlin text is what this project transcribes, and every row "
                 "here is a position where the Berlin ink is settled (both "
                 "Berlin-reading engines agree with the corpus). See "
                 "pipeline/build_collation_report.py for why the wider set of "
                 "cross-edition differences is deliberately not reported."),
        "rows": rows,
    }
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
        f.flush()
    print(f"Wrote {OUT_PATH}: {len(rows)} abbreviation(s) the other edition spells out")
    if rows and freq:
        print(f"  {attested} of {len(rows)} expansions are attested in the independent "
              f"corpus ({attested / len(rows):.0%})")
    elif rows:
        print("  sefaria_reference_corpus absent - expansions NOT scored "
              "(this is 'not checked', not 'not attested')")
    if rows:
        write_md(MD_PATH, rows, payload, prev)
        print(f"Wrote {MD_PATH}")
    print("  COLLATION, not corrections - nothing here is applicable to the corpus.")


if __name__ == "__main__":
    main()
