# [PRODUCTION] Two cheap, mechanical, no-LLM sweeps over part1.json that no
# prior check ran, both named as "cheap and not yet scripted" in
# PROJECT-STATUS.md's 2026-08-16 semantic-spotcheck-round-2 entry. Per
# CLAUDE.md Lesson 8 ("a cheap, mechanical, no-LLM check can catch what
# expensive LLM-based checks miss entirely") and Lesson 18 (run this class of
# check routinely, not just when something else draws attention).
#
#   1. Next-klal gematria marker: 29 of Part 1's 222 klalim end their
#      clean_text with " : <short-hebrew-token>" - a catchword-like preview
#      of the NEXT klal's number, printed after the closing colon. Compares
#      each found token against klal_id_to_gematria(klal_id + 1) and reports
#      any disagreement. NOT every klal carries this marker (193 don't), and
#      not every disagreement is a corruption - a common short word landing
#      right before the closing colon (e.g. klal 64's "אין") produces the
#      same shape as a genuine single-letter/stray-letter error. Tried
#      distinguishing the two mechanically (lexicon membership of the found
#      token) and dropped it: every one of the 7 real mismatches found here
#      is ALSO an ordinary lexicon word (a short Hebrew string being a valid
#      word is the common case, not a discriminating signal), so the check
#      would have flagged all 7 "low-confidence" and told a reviewer
#      nothing. Telling a genuine stray-letter error apart from an ordinary
#      sentence-final word needs contextual reading, not this script -
#      report all mismatches uniformly and leave that judgment to review.
#   2. Title vs. opening line: no prior check has ever compared a klal's
#      `title` field against the opening phrase of its own `clean_text`
#      (the text between the klal's gematria marker and the first
#      sentence-break punctuation). A legitimately SHORTER title is normal
#      editorial style in this print (e.g. klal 83's title "בשל תורה" for a
#      much longer opening sentence) and is not a finding - tolerated here
#      via a bidirectional-prefix check, not a strict equality gate.
#      What's left after that tolerance is either the title dropping a real
#      word the body keeps (klal 101/102/103/104's "ב"ד"), or the title
#      itself carrying a corruption the body doesn't (klal 69's "אהים" for
#      "אלהים", klal 87's "משנה" for "ממשנה") - both bear on Success
#      Criterion 3 (Sefaria display/citation), not just body-text fidelity.
#
# Both checks are read-only, standalone, and NOT wired into rebuild_all.sh:
# unlike validate_part1_corpus_integrity.py's checks 1-2b, neither has a
# clean zero-false-positive record yet (next-marker's common-word ambiguity;
# title's editorial-shortening cases, tolerated here but not proven
# exhaustive on future corpus edits) - per Lesson 2, a passing gate is not
# the same as a checked result, and these need human/context review before
# either could safely block a rebuild. Same precedent as
# detect_ligature_corruption.py and review_lexicon_gaps.py.
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate_part1_corpus_integrity as integrity

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pipeline"))
import corpus_io as cio  # noqa: E402

PART1_PATH = cio.PART1_PATH


def load_klalim():
    return cio.load_part1_sorted(PART1_PATH)


# --- Check 1: next-klal gematria marker -------------------------------

import re

NEXT_MARKER_RE = re.compile(r":\s*([א-ת]{1,4})$")


def find_next_klal_marker(clean_text):
    """Returns the trailing marker token, or None if this klal doesn't carry
    one. Confirmed against the full corpus: this regex finds exactly 29
    matches, matching PROJECT-STATUS.md's manually-counted figure."""
    m = NEXT_MARKER_RE.search(clean_text.rstrip())
    return m.group(1) if m else None


def check_next_klal_marker(klalim):
    print("\n=== 1. Next-klal gematria marker (trailing ' : <token>') ===")
    by_id = {k["klal_id"]: k for k in klalim}
    carriers = 0
    mismatches = []
    for k in klalim:
        marker = find_next_klal_marker(k["clean_text"])
        if marker is None:
            continue
        carriers += 1
        next_id = k["klal_id"] + 1
        if next_id not in by_id:
            continue  # last klal in Part 1, no "next" to check against
        expected = integrity.klal_id_to_gematria(next_id)
        if marker != expected:
            mismatches.append((k["klal_id"], marker, expected))
    print(f"  {carriers}/{len(klalim)} klalim carry a trailing next-klal marker.")
    if not mismatches:
        print("  0 mismatches against gematria(klal_id + 1).")
    else:
        print(f"  {len(mismatches)} mismatch(es) - some may be an ordinary sentence-final")
        print("  word rather than a real marker; needs contextual reading to tell apart:")
        for kid, found, expected in mismatches:
            print(f"    klal {kid}: found {found!r}, expected {expected!r} for klal {kid + 1}")
    return mismatches


# --- Check 2: title vs. opening line -----------------------------------

# Sentence/clause-break markers this print's opening lines end on, in
# ascending order of how early they're checked. " . "/" ." covers both a
# spaced period and one glued directly to the next word (klal 180's
# "עשה .ודע", no trailing space) - CLAUDE.md's editorial "[.]" convention is
# checked first since it's unambiguous. Bare "'" is deliberately excluded:
# a geresh is the ordinary abbreviation mark for words LIKE "ר'" (rabbi) and
# appears constantly inside a legitimate title, so treating it as a boundary
# produced dozens of false splits when tried.
TITLE_BOUNDARY_TOKENS = ["[.]", "•", " . ", " .", " :", " -", " ,"]


def opening_phrase(clean_text, gematria):
    """The text between the klal's own gematria marker and the first
    sentence-break token - the span a `title` field is expected to echo
    (possibly truncated, see below)."""
    rest = clean_text
    if rest.startswith(gematria + "'"):
        # klal 166's print attaches its own closing geresh directly to the
        # numeral ("קסו'"); see validate_part1_corpus_integrity.py's
        # check_gematria_self_consistency for the same tolerance.
        rest = rest[len(gematria) + 1:]
    elif rest.startswith(gematria):
        rest = rest[len(gematria):]
    rest = rest.lstrip()
    cut = len(rest)
    for token in TITLE_BOUNDARY_TOKENS:
        idx = rest.find(token)
        if idx != -1 and idx < cut:
            cut = idx
    return rest[:cut].strip()


def check_title_vs_opening(klalim):
    print("\n=== 2. Title field vs. own opening line ===")
    mismatches = []
    for k in klalim:
        op = opening_phrase(k["clean_text"], k["gematria"])
        title = k["title"].strip()
        # A title that's a straightforward prefix (in EITHER direction) of
        # the opening phrase is ordinary editorial shortening (klal 83's
        # "בשל תורה" for a much longer sentence) or an internal-punctuation
        # false split (klal 105/134, where a comma inside the sentence cut
        # the extraction short of the full title) - not a finding.
        if op == title or op.startswith(title) or title.startswith(op):
            continue
        mismatches.append((k["klal_id"], title, op))
    if not mismatches:
        print(f"  {len(klalim)}/{len(klalim)} klalim: title matches (or is a clean prefix/superset of) its own opening line.")
    else:
        print(f"  {len(mismatches)} mismatch(es):")
        for kid, title, op in mismatches:
            print(f"    klal {kid}:")
            print(f"      title:   {title!r}")
            print(f"      opening: {op!r}")
    return mismatches


def main():
    klalim = load_klalim()
    check_next_klal_marker(klalim)
    check_title_vs_opening(klalim)


if __name__ == "__main__":
    main()
