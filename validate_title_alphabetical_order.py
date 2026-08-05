# [PRODUCTION] Standing validation: Yad Malachi's klalim are structurally
# alphabetical - every klal's `title` groups by its first letter, and each
# letter's klalim form ONE contiguous run across the book (see
# PROJECT-STATUS.md, "All 222 Part-1 titles reviewed"). Run this any time
# `title` or klal ordering changes, the same way lexicon.txt validation runs
# after a text cleanup pass (see CLAUDE.md Conventions: "zero flagged items"
# is the bar).
#
# Supersedes validate_title_section_letter.py (2026-08-04), which only
# checked a title's first letter against its own `section` field - a weaker
# test than it looks, for two reasons found 2026-08-05:
#   1. It's comparing two DERIVED fields against each other. A klal-boundary
#      corruption that shifted `title` and `section` together passes it
#      silently - it can only catch a title that disagrees with its OWN
#      section label, not a title+section pair that are consistently wrong
#      in the same way.
#   2. Its SECTION_LETTER map only covered Part 1's 5 known section names;
#      anything not in that map (all of Parts 2-3) was silently skipped
#      entirely, despite the script iterating over part2.json/part3.json.
#
# This version checks something the `section` field can't corrupt: given the
# actual observed sequence of title-first-letters across klal_id order, does
# every letter's set of occurrences form a single contiguous block? A letter
# that appears, disappears, and reappears later is the real signature of a
# broken klal boundary - independent of whatever any `section` field claims.
# (A plain pairwise "does the letter ever decrease" check is NOT equivalent
# and was also tried and rejected 2026-08-05: it misses a corrupted run that
# jumps to a materially LATER letter and back, e.g. a single Dalet-titled
# klal stranded in the middle of a Hey run looks like a normal forward jump
# to a pairwise check, because ד->ה is shaped identically to a real section
# boundary. Contiguity catches it either way.)
import json
import os
from collections import defaultdict

REPO = os.path.dirname(os.path.abspath(__file__))
NO_TEXT_TITLE = "(no text available)"
ALPHABET = "אבגדהוזחטיכלמנסעפצקרשת"
RANK = {c: i for i, c in enumerate(ALPHABET)}


def load_klalim(path):
    data = json.load(open(path, encoding="utf-8"))
    return data["klalim"] if isinstance(data, dict) and "klalim" in data else data


def find_violations(klalim):
    """klalim must already be in the order the book presents them (klal_id order).

    Formalization: this is isotonic regression. Assign every klal a letter
    rank such that assigned ranks are non-decreasing across the whole
    sequence, choosing the assignment that maximizes how many klalim keep
    their own observed rank. A klal whose observed rank had to be overridden
    to preserve non-decreasing order is a violation. Solved with an O(n *
    |alphabet|) DP: dp[i][r] = best achievable match-count for the first i
    klalim with klal i assigned rank r, using a running prefix-max over
    dp[i-1][r'] for r' <= r so each step is O(|alphabet|) instead of
    O(|alphabet|^2).

    Two simpler formulations were tried first and rejected (2026-08-05):
    - min/max occurrence RANGE per letter: a single outlier far from a
      letter's real cluster inflates that letter's span and falsely
      implicates every correctly-labeled klal inside the inflated range.
    - run-length-encode into blocks, then maximum-weight strictly-increasing
      subsequence of BLOCKS: still wrong, because a letter can only
      contribute one block to a strictly-increasing chain - if a corruption
      splits one real section into several same-letter fragments (as klal
      102-106/108/119 does to the Bet section), only the single biggest
      fragment gets credited as "home" and every other genuinely-correct
      fragment gets flagged as an anomaly right along with the real ones.
      Isotonic regression doesn't have this problem: it operates on
      individual klalim, not pre-merged blocks, so the same letter can
      "reclaim" the sequence as many times as the data supports without
      being penalized for fragmentation.
    """
    seq = []
    for k in klalim:
        title = (k.get("title") or "").strip()
        if not title or title == NO_TEXT_TITLE:
            continue
        c = title[0]
        if c not in RANK:
            continue  # not a Hebrew letter (shouldn't happen for a real title)
        seq.append((k["klal_id"], c))

    n = len(seq)
    if n == 0:
        return {}
    L = len(ALPHABET)

    # dp[r] = best match-count achievable for the prefix processed so far,
    # with the last-assigned rank being exactly r. prefix_max[r] tracks
    # max(dp[0..r]) so each new position updates in O(L) total, not O(L^2).
    dp = [0] * L
    backtrack = []  # backtrack[i][r] = best predecessor rank (<=r) for dp at step i
    for kid, c in seq:
        obs = RANK[c]
        new_dp = [0] * L
        step_choice = [0] * L
        best_so_far = -1
        best_r_so_far = 0
        for r in range(L):
            if dp[r] > best_so_far:
                best_so_far = dp[r]
                best_r_so_far = r
            step_choice[r] = best_r_so_far
            new_dp[r] = best_so_far + (1 if r == obs else 0)
        dp = new_dp
        backtrack.append(step_choice)

    end_rank = max(range(L), key=lambda r: dp[r])
    assigned = [None] * n
    r = end_rank
    for i in range(n - 1, -1, -1):
        assigned[i] = r
        r = backtrack[i][r]

    by_klal = defaultdict(list)
    for (kid, c), r in zip(seq, assigned):
        if RANK[c] != r:
            by_klal[kid].append({
                "klal_id": kid,
                "actual_letter": c,
                "expected_letter": ALPHABET[r],
            })
    return by_klal


def main():
    # Only klalim_demo_dataset.json (the full 667-klal sequence) is checked -
    # the alphabet doesn't reset at a part boundary, so checking part1/2/3.json
    # individually would spuriously flag a letter that legitimately continues
    # across a part seam. Regenerate it first if part*.json changed
    # (build_klalim_demo_dataset.py / rebuild_all.sh) rather than trusting a
    # stale copy here.
    path = os.path.join(REPO, "klalim_demo_dataset.json")
    klalim = load_klalim(path)
    klalim = sorted(klalim, key=lambda k: k["klal_id"])
    by_klal = find_violations(klalim)

    if by_klal:
        print(f"{len(by_klal)} klal(im) flagged:")
        for kid in sorted(by_klal):
            r = by_klal[kid][0]
            print(f"  klal {kid}: title starts {r['actual_letter']!r}, "
                  f"expected {r['expected_letter']!r} to keep the sequence non-decreasing")
    else:
        print("Clean - 0 flagged items.")


if __name__ == "__main__":
    main()
