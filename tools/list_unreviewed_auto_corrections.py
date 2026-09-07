#!/usr/bin/env python3
"""
tools/list_unreviewed_auto_corrections.py

[STANDALONE] The open flags on words a MACHINE corrected and no human ever
checked - as one worklist, ordered by klal, with the evidence needed to accept
or reject each without opening the scan for every one.

Reviewer, 2026-09-07, having opened two of them: "they point to the correct
word. what's the issue?" There is none. These flags are not defects and nothing
here is misplaced - each names the right word. They are REVIEW WORK, and the
question each one asks is narrow: `ai-dropped-lamed-correction` restored the
lamed that the 19th-century alef-lamed sort drops, applied it to the corpus in
August 2026, and recorded it as a `manual_correction` - the type the dashboard
draws as human-decided - so it never reached a review queue. The flag is that
check, owed late. Did the machine restore the right letter?

WHY THIS FILE AND NOT THE DASHBOARD. The dashboard answers one word at a time
and these are 90 instances of ONE question, scattered across dozens of klalim.
Read as a list they triage in a few minutes; opened one URL at a time they are
90 separate context switches. Clearing them is also the cheapest way to shrink
the reindexer's population - a flag a reviewer closes needs no stable id at all
(items 0CK/0CL).

THE TWO INDEPENDENT SIGNALS ON EVERY ROW, and they fail differently (Lesson 9).

  * STRUCTURE - typography.dropped_lamed_explains(): is the stored word exactly
    the corrupt form with one lamed restored directly after an alef? A `no` here
    means the correction is NOT this class and the row deserves the scan.
  * FREQUENCY - sefaria_reference_corpus, 6.18M words of Talmud, Rashi, Rambam,
    Tur and Shulchan Arukh with no editorial or data lineage to this scan. It is
    the only independent arbiter available for this defect: lexicon.txt was built
    from this corpus's own OCR and absorbed the very corruption in question, and
    vision is a fourth reader of the same ink, which a defect in the SORT is
    upstream of (Lesson 24).

    NOT A VERDICT. A repaired form that is common and a corrupt form that is
    unattested is strong evidence and not proof, and the reverse is a reason to
    look, not to reject. Klal 200 w58 is the standing counter-example: the
    ligature turned `אליהו` into `איהו`, which is itself a common Aramaic word,
    so frequency cannot arbitrate it and only context can.

Rows are ordered by klal then word index, which is reading order, so the list
can be worked top to bottom against the text.
"""
import argparse
import collections
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
INSTALL_DIR = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(INSTALL_DIR, "pipeline"))
sys.path.insert(0, os.path.join(INSTALL_DIR, "pipeline", "repair_filters"))

import corpus_io as cio  # noqa: E402
import review_counts as rcount  # noqa: E402
import review_decisions as rd  # noqa: E402
import typography as typo  # noqa: E402

OUT_PATH = os.path.join(INSTALL_DIR, "UNREVIEWED-AUTO-CORRECTIONS-WORKLIST.md")
DEFAULT_BASE = "http://127.0.0.1:8420"
MARKER = "UNREVIEWED AUTOMATED CORRECTION"
ORIGINAL_RULING = re.compile(r"Original ruling ([0-9a-f]{12})")
CONTEXT_WORDS = 5


def reference_frequencies():
    """The independent corpus, or {} if it was never fetched.

    Deliberately soft: the worklist is still worth having without it - the
    structural check and the context do not depend on it - and a missing
    reference corpus is a setup state (see SETUP.md), not an error. The header
    says so rather than the rows quietly reading as "unattested".
    """
    try:
        import docai_filter as dlf
        return dlf.reference_frequencies()
    except Exception:                                          # noqa: BLE001
        return {}


def open_auto_correction_flags():
    """[(klal_id, word_index, flag, ruling)] for every flag this pass raised that
    is STILL ASKING FOR A HUMAN.

    ASKS review_counts.flag_still_open(), which is what the dashboard asks - not
    `needs_revisit` alone. FIXED 2026-09-07, and this file shipped with the bug
    for one afternoon. A word-level flag is also answered by a human ruling
    recorded at that word after the flag was raised, so a reviewer who works a
    row by CONFIRMING the machine's text (recording `אלא` -> `אלא`, which is what
    accepting one of these looks like) has answered it without ever clicking
    "clear revisit flag". Filtering on the raw field lists their finished work
    back to them as outstanding.

    This is the exact defect `flagged_klalim()` was deleted for two commits
    earlier - 153 klalim against the dashboard's 102 - reproduced here by
    hand-rolling the predicate instead of importing it (Lesson 13). The remedy
    is the same one that file's removal note gives: ask review_counts.
    """
    by_id = {r["id"]: r for r in rd.all_records()}
    decided = rd.all_current_live("candidate_choice")
    manual = rd.all_current_live("manual_correction")
    out = []
    for (kid, wi), flag in rd.all_current("klal_flag").items():
        if wi is None or MARKER not in (flag.get("note") or ""):
            continue
        if not rcount.flag_still_open(kid, wi, flag, decided, manual):
            continue
        m = ORIGINAL_RULING.search(flag.get("note") or "")
        out.append((kid, wi, flag, by_id.get(m.group(1)) if m else None))
    return sorted(out, key=lambda row: (row[0], row[1]))


def answered_count():
    """How many of this pass's flags a human has now answered - for the header.

    Worth naming rather than letting the total silently shrink: a reviewer wants
    to see the work they did, not just a smaller number.
    """
    decided = rd.all_current_live("candidate_choice")
    manual = rd.all_current_live("manual_correction")
    total = answered = 0
    for (kid, wi), flag in rd.all_current("klal_flag").items():
        if wi is None or MARKER not in (flag.get("note") or ""):
            continue
        total += 1
        if not rcount.flag_still_open(kid, wi, flag, decided, manual):
            answered += 1
    return total, answered


def evidence(before, after, freqs):
    """(structure_ok, freq_before, freq_after) - the two independent signals.

    A frequency of None means ABSENT FROM THE REFERENCE CORPUS, which in a
    word-frequency map is the same count as zero and is NOT the same claim: a
    form can be absent because it is wrong, or because the reference books never
    had occasion to use it. Proper names are the whole of the second case here -
    `אלגאזי` (Maharsham Algazi) is a real word this
    book uses and Talmud/Rashi/Rambam/Tur/Shulchan Arukh do not. Printing that as
    a measured `0x` would read as evidence against a correct repair, so the two
    are kept distinct all the way to the page.
    """
    if not before or not after:
        return None, None, None
    return (typo.dropped_lamed_explains(after, before),
            freqs.get(before), freqs.get(after))


def verdict_hint(structure_ok, f_before, f_after, have_corpus):
    """One word on where to look first. NEVER an instruction to accept.

    A triage label, not a ruling - Lesson 2: a passing score is a place to start
    looking, not a certificate. The reviewer decides; this only orders the queue.
    """
    if structure_ok is False:
        return "LOOK - not a dropped-lamed shape"
    if not have_corpus:
        return "reference corpus unavailable"
    if f_before is None and f_after is None:
        # Both absent. Says nothing either way, and mostly a proper name.
        return "neither form in the reference corpus"
    if (f_after or 0) == 0:
        return "LOOK - repair unattested"
    if (f_before or 0) == 0:
        return "clean - corrupt form unattested"
    if (f_after or 0) >= 3 * (f_before or 0):
        return "clean - repair far commoner"
    return "LOOK - both forms attested"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hebrew", choices=("visual", "logical"), default="visual",
                    help="visual (default): reorder Hebrew so it reads correctly in a "
                         "viewer that runs no bidi algorithm, at the cost of being "
                         "copy-unsafe. logical: storage order, copy-safe, correct only "
                         "in a bidi-aware renderer. Matches tools/preview_dicta_disputes.py.")
    ap.add_argument("--out", default=OUT_PATH)
    ap.add_argument("--base-url", default=DEFAULT_BASE)
    args = ap.parse_args()
    base = args.base_url.rstrip("/")

    freqs = reference_frequencies()
    words = {k["klal_id"]: cio.words_of(k) for k in cio.load_part1()}
    rows = open_auto_correction_flags()

    by_hint = collections.Counter()
    lines = []
    for kid, wi, flag, ruling in rows:
        snap = (ruling or {}).get("candidate_snapshot") or {}
        before = snap.get("original_word")
        after = (ruling or {}).get("chosen_text")
        klal_words = words.get(kid) or []
        now = klal_words[wi] if 0 <= wi < len(klal_words) else None
        structure_ok, f_before, f_after = evidence(before, after, freqs)
        hint = verdict_hint(structure_ok, f_before, f_after, bool(freqs))
        by_hint[hint] += 1

        left = " ".join(klal_words[max(0, wi - CONTEXT_WORDS):wi])
        right = " ".join(klal_words[wi + 1:wi + 1 + CONTEXT_WORDS])
        def _n(v):
            # "absent" and "counted zero times" are the same number and not the
            # same statement - see evidence().
            return "not in it" if v is None else f"{v}x"
        freq_txt = ("reference corpus not available" if not freqs else
                    f"`{cio.rtl(before)}` {_n(f_before)}, `{cio.rtl(after)}` {_n(f_after)}")
        struct_txt = {True: "yes", False: "**NO**", None: "unknown"}[structure_ok]

        # EVERY Hebrew run goes through cio.rtl(). A .md is an LTR document, so
        # a bare Hebrew run beside an arrow, a URL or a digit is reordered
        # against it - `X` -> `Y` displays as `Y` <- `X`, which reads as the
        # repair running backwards. See corpus_io.rtl for the measurement.
        lines.append(
            f"- [klal {kid} · w{wi}]({base}/klal/{kid}/word/{wi}) — "
            f"was `{cio.rtl(before)}`, now **`{cio.rtl(after)}`** · _{hint}_\n"
            f"    - in context: {cio.rtl(f'{left} [{now}] {right}')}\n"
            f"    - dropped-lamed shape: {struct_txt} · independent frequency: {freq_txt}\n")
        if now != after:
            lines.append(f"    - **the corpus does not hold the corrected form here — it reads "
                         f"`{cio.rtl(now)}`. Read this one before ruling.**\n")

    total, answered = answered_count()
    head = [
        "# Unreviewed automated corrections - the check the machine promised\n",
        f"**{len(rows)} of {total} still open**; {answered} have been answered by a human "
        "ruling recorded at the word. Generated by "
        "`tools/list_unreviewed_auto_corrections.py`; **regenerate after any review pass** - "
        "confirming the machine's text answers the flag, so a row can leave this list without "
        "anyone clicking \"clear revisit flag\".\n",
        "\nEvery word below was changed by `ai-dropped-lamed-correction` in August 2026, applied "
        "to the corpus, and recorded as a `manual_correction` - the type the dashboard draws as "
        "human-decided - so it never reached a review queue. **These flags are not defects and "
        "nothing here is misplaced**: each names the right word. The question is only whether the "
        "machine restored the right letter.\n",
        "\nThe 19th-century alef-lamed sort (`ﭏ`) prints as a bare alef when it wears, so "
        f"`{cio.rtl('אלא')}` comes off the page as `{cio.rtl('אא')}`. The correction puts the lamed "
        "back. Two independent signals per row, which fail differently: the **shape** (is this "
        "actually one lamed restored after an alef?) and the **frequency** in 6.18M words of "
        "Hebrew that never saw this scan. Neither is a verdict - klal 200 w58 turned "
        f"`{cio.rtl('אליהו')}` into `{cio.rtl('איהו')}`, itself a common word, "
        "where only context can decide.\n",
        "\n| triage | count |\n|---|---:|\n",
    ]
    for hint, n in sorted(by_hint.items(), key=lambda kv: (-kv[1], kv[0])):
        head.append(f"| {hint} | {n} |\n")
    if not freqs:
        head.append("\n> **The reference corpus is not present**, so every frequency reads as "
                    "unavailable rather than as zero. See `SETUP.md`; re-run this after fetching "
                    "it, or the frequency column tells you nothing.\n")
    head.append("\n---\n\n")

    if args.hebrew == "visual":
        head.insert(1, "\n" + cio.VISUAL_WARNING)
    # Split on newlines so render_hebrew sees real LINES: get_display reorders a
    # whole string, and a multi-line chunk would be reordered as one.
    out = "".join(head) + "".join(lines)
    body = cio.render_hebrew(out.split("\n"), args.hebrew)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(body))

    print(f"Wrote {args.out}: {len(rows)} open flag(s)")
    for hint, n in sorted(by_hint.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"   {n:>4}  {hint}")


if __name__ == "__main__":
    sys.exit(main() or 0)
