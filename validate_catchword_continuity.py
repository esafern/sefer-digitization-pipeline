# [PRODUCTION] Catchword-continuity sanity check, suggested 2026-08-07 while
# investigating a confusing review-dashboard correction on klal 4 (see
# PROJECT-STATUS.md "review dashboard feedback"): this print's binding
# convention sometimes repeats the last real word of a page as a small
# preview at the very bottom, to give the reader a head start turning the
# page - a traditional printer's "catchword." The idea here: that's a
# free, cheap structural invariant to check corpus-wide - the last real
# (non-furniture) token on page N should equal the first real token of
# page N+1 (skipping page N+1's own running header, and skipping a klal's
# gematria marker if the boundary happens to land exactly on a new klal).
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

REPO = os.path.dirname(os.path.abspath(__file__))
DOCAI_DIR = os.path.join(REPO, "docai_word_boxes")
FIRST_REAL_PAGE = 13  # pages 1-12 are byte-identical duplicates of 13-24, see CLAUDE.md
LAST_PAGE = 82

HEADER_WORDS = {"יד", "מלאכי", "יר", "יך", "כללי", "כללי-", "כלל"}
FURNITURE_RE = re.compile(r"^(Digitized|by|Google)$", re.IGNORECASE)
GEMATRIA_LETTERS = set("אבגדהוזחטיכלמנסעפצקרשתךםןףץ")


def clean_word(w):
    return "".join(c for c in w if c.isalnum())


def looks_like_gematria_marker(tok_text):
    """A klal marker is a short token made entirely of Hebrew letters used
    as numerals - not a rigorous check (a short real word would also
    match), just enough to skip an actual marker sitting right at a page's
    first real token, per the user's own framing: 'ignoring any klal
    gematria header.'"""
    w = clean_word(tok_text)
    return 1 <= len(w) <= 4 and all(c in GEMATRIA_LETTERS for c in w)


def is_furniture(tok_text):
    w = tok_text.strip()
    if not w:
        return True
    if FURNITURE_RE.match(w):
        return True
    if clean_word(w) in HEADER_WORDS:
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


def first_real_tokens(tokens, n=4, skip_header_words=6):
    """Skip the page's own running header (a handful of tokens at the very
    top - 'יד/יר/יך מלאכי כללי <section>' or similar), then optionally one
    klal gematria marker, then return the next n real tokens."""
    out = []
    skipped_header = 0
    for t in tokens:
        w = t["text"].strip()
        if not w:
            continue
        if skipped_header < skip_header_words and (is_furniture(w) or clean_word(w) in HEADER_WORDS):
            skipped_header += 1
            continue
        if not out and looks_like_gematria_marker(w):
            continue  # the "ignoring any klal gematria header" case
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
    matches, no_matches, skipped = [], [], []
    for page_num in range(FIRST_REAL_PAGE, LAST_PAGE):
        this_page = load_page(page_num)
        next_page = load_page(page_num + 1)
        if not this_page or not next_page:
            skipped.append(page_num)
            continue

        ending = last_real_tokens(this_page, n=3)
        opening = first_real_tokens(next_page, n=4)
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
