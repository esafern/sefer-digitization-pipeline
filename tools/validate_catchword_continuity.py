# [PRODUCTION] Catchword-continuity sanity check, suggested 2026-08-07 while
# investigating a confusing review-dashboard correction on klal 4 (see
# PROJECT-STATUS.md "review dashboard feedback"): this print's binding
# convention sometimes repeats the last real word of a page as a small
# preview at the very bottom, to give the reader a head start turning the
# page - a traditional printer's "catchword." The idea here: that's a
# free, cheap structural invariant to check corpus-wide - the last real
# (non-furniture) token on page N should equal the first real token of
# page N+1 (skipping page N+1's own running header, and skipping a klal's
# gematria marker if the boundary happens to land exactly on a new klal -
# an exact check against gematria_trace_part1.json's real marker positions,
# not a word-shape guess; see load_marker_positions()).
#
# This is explicitly NOT a zero-tolerance check. Not every page boundary
# has a catchword (mid-paragraph boundaries usually don't - only a
# genuine last-word-of-page repeat would match), and OCR on a catchword
# (small, sometimes faint, at the very edge of the scan) is often worse
# than on body text. Treat "no match" as uninformative, not a defect -
# the useful signal is a match (confirms the ending token really is a
# printer's catchword, not stray noise) and is being kept as a triage
# tool for exactly the kind of confusion that prompted this: telling a
# genuine catchword apart from an isolated scan artifact near a page's
# bottom edge (e.g. the klal-4 "1" investigation - confirmed NOT a
# catchword, since it didn't match page 16's real opening word at all,
# and directly cropping the mark showed it was an isolated ink speck in
# blank space, not a repeated word).
import json
import os
import re

# Moved one level deeper (pipeline/ or tools/) 2026-08-16 - REPO now goes up
# two levels, not one, to keep resolving to the actual repo root where
# part1.json/docai_word_boxes/etc. live.
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCAI_DIR = os.path.join(REPO, "docai_word_boxes")
# CORRECTED 2026-08-14: this used to say "pages 1-12 are byte-identical
# duplicates of 13-24, see CLAUDE.md" - both halves false. Checked all 12
# pairs: every one differs, and CLAUDE.md says nothing of the sort. Pages
# 1-12 are the scan's FRONT MATTER (Google's digitization notice, library
# stamps/shelfmarks, the publisher's preface and the author's own
# introduction) - no running header, no klal markers, no catchwords to
# check. The value 13 was right; only its stated reason was invented.
FIRST_REAL_PAGE = 13
# Last scan page to consider. DERIVED 2026-08-15 from docai_word_boxes/ rather
# than hard-coded: it was a bare `LAST_PAGE = 82` with no comment and no stated
# derivation, sitting one line under a constant whose invented justification
# this project already had to correct (see FIRST_REAL_PAGE above). 82 happens
# to be right today - docai_word_boxes/ holds exactly page_1..page_82 - but the
# failure mode of a stale literal here is silent, not loud: a scan that gained
# pages would simply never have its later boundaries checked, and the script
# would still print a confident "Checked N page boundaries" (CLAUDE.md
# Lesson 1 - quietly narrowed coverage reported as if complete). The literal
# stays only as the fallback for a fresh clone with no docai cache, where the
# loop just skips every missing page anyway.
FALLBACK_LAST_PAGE = 82


def _discover_last_page():
    if not os.path.isdir(DOCAI_DIR):
        return FALLBACK_LAST_PAGE
    pages = [int(m.group(1)) for m in
             (re.fullmatch(r"page_(\d+)\.json", f) for f in os.listdir(DOCAI_DIR)) if m]
    return max(pages) if pages else FALLBACK_LAST_PAGE


LAST_PAGE = _discover_last_page()

# FIXED 2026-08-14: "כלל" (a common standalone Hebrew word - "rule",
# "principle") used to be in this set too, alongside "כללי" (the actual
# header token, "rules of..."). That meant any genuine catchword or page-
# opening word that happened to just be the bare word "כלל" would be
# silently treated as furniture and skipped, in both last_real_tokens()
# and first_real_tokens() - the exact false-negative shape this file's own
# docstring says is fine ("no match" is uninformative here), but it's
# still a real accuracy gap, not a disclosed limitation. Confirmed 0 of
# 70 Part-1 pages are currently affected either way (no page boundary's
# real last/first token is the bare word "כלל"), so removing it is a
# true no-op today and only matters for future data.
HEADER_WORDS = {"יד", "מלאכי", "יר", "יך", "כללי", "כללי-"}
FURNITURE_RE = re.compile(r"^(Digitized|by|Google)$", re.IGNORECASE)
# Matching HEADER_WORDS through clean_word() (which strips punctuation) makes
# the abbreviation י"ד collapse onto the header's bare יד - and י"ד is a very
# common citation in this book (Yoreh De'ah, or a siman number), not page
# furniture. Same false-furniture shape as the bare כלל entry removed
# 2026-08-14, but unlike that one this is NOT inert: 43 tokens across the scan
# (39 י"ד, 2 י"ר, 2 י"ך) are currently eaten, and one of them changes a
# reported page boundary - page 45 really ends `...סימן י"ד : בתר` but was
# reported as `א סימן בתר`, silently dropping the siman number and pulling in
# an unrelated earlier token. A running-header word is always a bare word;
# a gershayim/geresh inside the token means it is an abbreviation instead.
ABBREV_MARKS = "\"'׳״"
GEMATRIA_LETTERS = set("אבגדהוזחטיכלמנסעפצקרשתךםןףץ")


def clean_word(w):
    return "".join(c for c in w if c.isalnum())


def is_header_word(w):
    return clean_word(w) in HEADER_WORDS and not any(c in ABBREV_MARKS for c in w)


SECTION_WORDS = {"האלף", "הבית", "הגימל", "הדלת", "ההא"}


def load_marker_positions():
    """page -> set of token indices that are a REAL klal's own marker
    position, per gematria_trace_part1.json. Replaces an earlier shape-based
    guess ('a short token made entirely of Hebrew letters') that silently
    ate real opening words - bug found and fixed 2026-08-11 (PROJECT-STATUS.md
    'klal 5 cross-page truncation'): `looks_like_gematria_marker` matched any
    1-4 letter all-Hebrew word, which is most short Hebrew words, not just
    markers, and the guard meant to limit it to one leading token (`not out`)
    kept re-firing across MULTIPLE leading words as long as none had been
    accepted yet. On page 17 it ate both `אי` and `נמי` - real opening words -
    before finally accepting `ועיקר`, so page 16's genuine catchword (`אי`,
    confirmed via klal 5's fix) never got compared against page 17's real
    opening at all, and this boundary was misclassified as 'no match'.
    Cross-referencing the independently-verified marker position is exact:
    only skip a token when some klal is actually known to start right there."""
    path = os.path.join(REPO, "gematria_trace_part1.json")
    if not os.path.exists(path):
        return {}
    trace = json.load(open(path, encoding="utf-8"))
    out = {}
    for e in trace:
        page, pos = e.get("page"), e.get("marker_position")
        if page is not None and pos is not None:
            out.setdefault(page, set()).add(pos)
    return out


def is_furniture(tok_text):
    w = tok_text.strip()
    if not w:
        return True
    if FURNITURE_RE.match(w):
        return True
    if is_header_word(w):
        return True
    if w.isdigit():
        return True
    if not any(c in GEMATRIA_LETTERS for c in w) and not clean_word(w):
        return True  # pure punctuation
    return False


def last_real_tokens(tokens, n=3):
    out = []
    for t in reversed(tokens):
        if is_furniture(t["text"]):
            continue
        out.append(t["text"])
        if len(out) >= n:
            break
    return list(reversed(out))


def first_real_tokens(tokens, n=4, skip_header_words=6, marker_positions=None):
    """Skip the page's own running header (a handful of tokens at the very
    top - 'יד/יר/יך מלאכי כללי <section>' or similar), then a klal marker
    ONLY if this exact token index is a real, independently-verified marker
    position for this page (see load_marker_positions()), then return the
    next n real tokens."""
    marker_positions = marker_positions or set()
    out = []
    skipped_header = 0
    for idx, t in enumerate(tokens):
        w = t["text"].strip()
        if not w:
            continue
        if skipped_header < skip_header_words and (
            is_furniture(w) or is_header_word(w) or clean_word(w) in SECTION_WORDS
        ):
            skipped_header += 1
            continue
        if not out and idx in marker_positions:
            continue  # a real klal genuinely starts here - not body text
        out.append(w)
        if len(out) >= n:
            break
    return out


def load_page(page_num):
    path = os.path.join(DOCAI_DIR, f"page_{page_num}.json")
    if not os.path.exists(path):
        return None
    return json.load(open(path, encoding="utf-8"))


def main():
    marker_positions = load_marker_positions()
    matches, no_matches, skipped = [], [], []
    for page_num in range(FIRST_REAL_PAGE, LAST_PAGE):
        this_page = load_page(page_num)
        next_page = load_page(page_num + 1)
        if not this_page or not next_page:
            skipped.append(page_num)
            continue

        ending = last_real_tokens(this_page, n=3)
        opening = first_real_tokens(next_page, n=4, marker_positions=marker_positions.get(page_num + 1))
        if not ending or not opening:
            skipped.append(page_num)
            continue

        last_word = clean_word(ending[-1])
        opening_words = [clean_word(w) for w in opening]
        if last_word and last_word in opening_words:
            matches.append((page_num, ending, opening))
        else:
            no_matches.append((page_num, ending, opening))

    print(f"Checked {len(matches) + len(no_matches)} page boundaries ({len(skipped)} skipped - missing page data).\n")
    print(f"=== {len(matches)} boundaries where the page's last real word reappears as the next "
          f"page's opening (genuine catchword, or coincidental repetition) ===")
    for page_num, ending, opening in matches:
        print(f"  page {page_num}->{page_num+1}: ...{' '.join(ending)}  |  {' '.join(opening)}...")

    print(f"\n=== {len(no_matches)} boundaries with NO match (most page breaks - mid-paragraph, "
          f"no catchword used, or the catchword itself misread) - informational only, not a defect ===")
    print("  (not printed in full - triage sample only, first 15)")
    for page_num, ending, opening in no_matches[:15]:
        print(f"  page {page_num}->{page_num+1}: ...{' '.join(ending)}  |  {' '.join(opening)}...")


if __name__ == "__main__":
    main()
