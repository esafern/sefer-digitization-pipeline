#!/usr/bin/env python3
# [PRODUCTION] The `validate <book>` command item 0AR asked for.
#
# `tests/test_corpus_invariants.py` holds ~44 assertions that a given book's
# DATA is well-formed - not properties of the CODE, which is what a test
# suite is for. Until 2026-09-03 those lived undistinguished inside "the test
# suite," so a corpus repair (correctly) turning one red looked like a broken
# build. tests/conftest.py now tags every one of them `@pytest.mark.
# book_content`, derived automatically from which corpus-reading fixture each
# test actually uses - never hand-annotated, so a new test cannot silently
# fall outside the marker's reach the way a hand-maintained list would.
#
# This script is the thin, book-independent front door to that marked set:
# it does not duplicate a single assertion (Lesson 13 - a duplicated
# assertion is a second copy of the truth), it runs the real pytest file with
# `-m book_content`, pointed at whichever corpus `--corpus` names.
#
# Usage:
#   python3 tools/validate_corpus.py                  # validate this repo's own corpus
#   python3 tools/validate_corpus.py --corpus /path/to/other-book
#   python3 tools/validate_corpus.py -k title          # narrow to matching test names
#
# Exit code is pytest's own (0 = every invariant held).
import os
import subprocess
import sys

# THIS INSTALLATION's own directory - this script never reads corpus DATA
# itself (it launches pytest as a subprocess and lets $SEFER_CORPUS_ROOT do
# that), so there is no separate "corpus root" concept here at all, only the
# install location that finds tests/test_corpus_invariants.py. Named
# INSTALL_DIR rather than REPO on purpose: item 0BI's guard test
# (test_the_corpus_root_bypass_count_has_not_grown) flags any file whose
# `REPO` is a fresh `os.path.dirname(os.path.dirname(os.path.abspath(
# __file__)))` - the exact pattern that let $SEFER_CORPUS_ROOT silently do
# nothing for two other scripts this same session - and a `REPO` name here,
# even though genuinely benign, would be indistinguishable from that pattern
# without a human re-reading this file every time the guard's count changed.
INSTALL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    args = sys.argv[1:]
    corpus_root = None
    passthrough = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--corpus":
            if i + 1 >= len(args):
                sys.exit("--corpus needs a directory")
            corpus_root = args[i + 1]
            i += 2
            continue
        if a.startswith("--corpus="):
            corpus_root = a.split("=", 1)[1]
            i += 1
            continue
        passthrough.append(a)
        i += 1

    env = dict(os.environ)
    if corpus_root:
        # Resolved at the FRESH subprocess's own import time, the one case
        # this is safe (item 0AZ) - never set in THIS process, which may
        # already have imported corpus_io against a different root.
        env["SEFER_CORPUS_ROOT"] = os.path.abspath(corpus_root)

    cmd = [sys.executable, "-m", "pytest",
           os.path.join(INSTALL_DIR, "tests", "test_corpus_invariants.py"),
           "-m", "book_content", "-q"] + passthrough
    proc = subprocess.run(cmd, cwd=INSTALL_DIR, env=env)
    sys.exit(proc.returncode)


if __name__ == "__main__":
    main()
