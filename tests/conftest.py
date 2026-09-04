# [PRODUCTION] Session-wide fixtures for the general-purpose (book-
# independent) half of the suite. Item 0AR, step 2 of its own order
# ("the seam -> fixture generator plus a conftest.py -> move the 23 pinned UI
# tests -> split the invariants -> add the guard").
#
# There was no conftest.py in this repo before this file. Its only job is to
# build tests/fixtures/'s tiny synthetic book ONCE per test session and hand
# it out - to pure-Python tests via `fixture_corpus_root` (which points
# corpus_io at it for the duration of one test, then restores the real root),
# and to Playwright tests via `fixture_server` (a review_server.py subprocess
# with BOTH `$SEFER_CORPUS_ROOT` and `$REVIEW_DECISIONS_PATH` pointed at it -
# two separate seams, because review_decisions.py resolves its own path
# independently of corpus_io's root; see build_fixture_corpus.py's note on
# that gap).
#
# WHY SESSION-SCOPED. Building the fixture runs five real pipeline-stage
# subprocesses (~1-2s total) - cheap once, wasteful per-test. Nothing in it
# is test-specific state; individual tests that need a clean ledger record
# their own decisions against a FRESH `review_decisions.jsonl` copy (see
# `fixture_decisions_path` below), never against the shared built corpus,
# so tests cannot see each other's ledger writes.
import json
import os
import shutil
import socket
import subprocess
import sys
import time

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pipeline"))
sys.path.insert(0, os.path.join(REPO, "tests", "fixtures"))

import corpus_io as cio  # noqa: E402
import build_fixture_corpus  # noqa: E402


@pytest.fixture(scope="session")
def fixture_corpus_root(tmp_path_factory):
    """The built fixture corpus directory - session-scoped, built once.

    Tests must not WRITE into this directory (several tests below copy it
    instead, precisely so a mutation in one test cannot leak into another
    that happens to run later in the same session).
    """
    root = tmp_path_factory.mktemp("fixture_sefer")
    build_fixture_corpus.build(str(root))
    return str(root)


@pytest.fixture
def use_fixture_corpus(fixture_corpus_root):
    """Point corpus_io at the fixture for ONE test, then restore the real
    root - for pure-Python tests that call corpus_io/review_decisions
    functions directly (in-process), as opposed to `fixture_server` below
    (a subprocess, which needs the env var form of the same seam).

    Yields the fixture root so a test can also load files from it directly.
    """
    previous = cio.set_corpus_root(fixture_corpus_root)
    try:
        yield fixture_corpus_root
    finally:
        cio.set_corpus_root(previous)


@pytest.fixture
def fixture_decisions_path(fixture_corpus_root, tmp_path):
    """A private COPY of the fixture's review_decisions.jsonl, for a test that
    needs to append its own decisions without affecting `fixture_corpus_root`
    (session-scoped and shared) or any other test."""
    dst = tmp_path / "review_decisions.jsonl"
    shutil.copy(os.path.join(fixture_corpus_root, "review_decisions.jsonl"), dst)
    return str(dst)


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_server(url, timeout=10):
    import urllib.request
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except Exception:
            time.sleep(0.2)
    return False


@pytest.fixture
def fixture_server(fixture_corpus_root, fixture_decisions_path):
    """review_server.py, live, serving the FIXTURE corpus - the
    generalization-focused counterpart to test_review_server.py's own
    `server` fixture (which serves the real corpus and is left as-is; moving
    which tests use which fixture is a per-test decision, not a global one).

    Same subprocess-with-env-vars shape as `server`, plus the one thing that
    fixture needs and this one adds: `SEFER_CORPUS_ROOT`, so every corpus_io
    path the server resolves - in its own process, at its own import time -
    points at the fixture directory rather than the real repo.
    """
    port = _free_port()
    env = dict(os.environ)
    env["SEFER_CORPUS_ROOT"] = fixture_corpus_root
    env["REVIEW_DECISIONS_PATH"] = fixture_decisions_path

    log_path = fixture_decisions_path + ".serverlog"
    log = open(log_path, "w+")
    proc = subprocess.Popen(
        [sys.executable, os.path.join(REPO, "pipeline", "review_server.py"), "--port", str(port)],
        cwd=fixture_corpus_root, env=env, stdout=log, stderr=subprocess.STDOUT,
    )
    base_url = f"http://127.0.0.1:{port}"
    try:
        ok = _wait_for_server(base_url + "/api/flags")
        if not ok:
            log.flush(); log.seek(0)
            out = log.read()
            proc.kill()
            pytest.fail(f"review_server.py never became ready against the fixture corpus:\n{out}")
        yield base_url
    finally:
        proc.kill()
        proc.wait(timeout=5)
        log.close()
        if os.path.exists(log_path):
            os.remove(log_path)


# --- Splitting "the test suite" from "does this book's data validate" -------
#
# Item 0AR's own framing: `test_corpus_invariants.py`'s corpus-reading tests
# ARE NOT TESTS for a general-purpose tool - they assert that THIS book's
# data is well-formed, and a corpus repair (correctly) turns them red. They
# belong behind a `validate <book>` command, not in a suite that is supposed
# to certify the CODE.
#
# The split is done by MARKER, not by moving 40+ test bodies into a new file:
# moving them would either duplicate every corpus-reading fixture (a second
# copy that drifts, Lesson 13) or force this file's whole fixture set to
# migrate with them for no reason - the assertions and the fixtures they read
# belong together, in the file that has always held them. What changes is
# which SUITE a test counts toward, and that is exactly what a marker means.
#
# The marker is applied AUTOMATICALLY, from the real fixture dependency graph,
# not hand-typed onto ~40 individual functions - hand-annotation is the thing
# that drifts silently the day someone adds a 41st test and forgets the
# decorator. `CORPUS_CONTENT_FIXTURES` is exhaustive as of 2026-09-03 (every
# session-scoped fixture in test_corpus_invariants.py that opens a real file
# under the corpus root); a new such fixture there needs a matching entry
# here, and there is no way to forget silently - a test using an un-listed
# corpus-reading fixture stays wrongly unmarked, which is a reason to keep
# this list next to conftest.py's own guard test, not to trust it blindly.
CORPUS_CONTENT_FIXTURES = {
    "part_klalim", "all_klalim", "part1_by_id", "corrections",
    "regions", "alignment", "all_alignment", "decision_records",
}

# ...AND the tests that read the real corpus WITHOUT going through any of those
# fixtures, which the closure rule above cannot see.
#
# FOUND 2026-09-03 by an ultra review, and it is the exact hole the fixture rule
# was always going to have: the marker is derived from a test's fixture
# dependencies, so a test that opens a corpus file by path, or calls
# review_server's loaders directly, is invisible to it. Both of these do:
#   - test_lexicon_does_not_whitelist_a_known_corrupt_form reads lexicon.txt
#   - test_no_corpus_word_is_aligned_to_page_furniture calls review_server's
#     _load_klalim/_load_regions against the live corpus
# Both therefore sat in the general/portable bucket, where a legitimate lexicon
# purge or realignment turns them red - the precise false alarm the book_content
# split exists to prevent - while tools/validate_corpus.py, which runs only
# `-m book_content`, never exercised them at all.
#
# A NAME LIST IS A HAND-MAINTAINED THING and this repo has learned twice what
# those cost (Lesson 13), so it does not stand alone:
# test_every_corpus_reading_invariant_is_marked in test_pipeline_logic.py greps
# the test source for corpus-reading calls and fails if one is neither
# fixture-covered nor listed here. Adding a test that reads the corpus without
# updating this set is a test failure, not a silent miss.
CORPUS_CONTENT_TESTS = {
    "test_lexicon_does_not_whitelist_a_known_corrupt_form",
    "test_no_corpus_word_is_aligned_to_page_furniture",
}


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "book_content: asserts THIS book's data is well-formed, not a property "
        "of the code - see tools/validate_corpus.py, the `validate <book>` "
        "command item 0AR asked for. Excluded from the general-purpose gate.",
    )


def pytest_collection_modifyitems(config, items):
    for item in items:
        by_fixture = CORPUS_CONTENT_FIXTURES & set(getattr(item, "fixturenames", ()))
        by_name = item.name in CORPUS_CONTENT_TESTS
        if by_fixture or by_name:
            item.add_marker(pytest.mark.book_content)


# --- The guard: item 0AR's "or it decays" clause ----------------------------
#
# ADDED with this file rather than deferred to a later step, because a guard
# added AFTER tests already reference the real corpus by path has nothing to
# check against; adding it now, while only a handful of files do, is what
# keeps the number from growing unnoticed. See test_pipeline_logic.py's
# test_the_corpus_root_bypass_count_has_not_grown for the assertion
# itself - kept there rather than here so it participates in the SAME suite
# 0AR measured (test_pipeline_logic.py, not this file, which no CI stage
# collects on its own).
