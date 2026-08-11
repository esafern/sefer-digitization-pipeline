# [PRODUCTION] End-to-end test for review_server.py + review_frontend/,
# using a real headless browser (Playwright) against a real server
# subprocess. Deliberately kept OUT of tests/test_corpus_invariants.py's
# rebuild_all.sh gate - unlike that fast, no-API, no-network corpus-data
# suite, this needs a live server process and a real browser, so it's run
# on demand: `./venv/bin/python -m pytest tests/test_review_server.py -v`.
#
# Playwright was installed specifically because the Chrome-extension-based
# browser automation available in this environment could never
# successfully load review.html/review_server.py's page (page too heavy,
# extension timed out repeatedly) - see PROJECT-STATUS.md "Review
# dashboard rearchitecture". This is the actual, working verification
# method for this dashboard, not a nice-to-have.
import hashlib
import json
import os
import socket
import subprocess
import sys
import tempfile
import time

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PART1_PATH = os.path.join(REPO, "part1.json")

playwright_sync_api = pytest.importorskip("playwright.sync_api")
sync_playwright = playwright_sync_api.sync_playwright


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _file_sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


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


@pytest.fixture(scope="module")
def server():
    port = _free_port()
    decisions_path = tempfile.mktemp(suffix=".jsonl", prefix="test_review_decisions_")
    env = dict(os.environ)
    env["REVIEW_DECISIONS_PATH"] = decisions_path

    proc = subprocess.Popen(
        [sys.executable, os.path.join(REPO, "review_server.py"), "--port", str(port)],
        cwd=REPO, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    base_url = f"http://127.0.0.1:{port}"
    try:
        ok = _wait_for_server(base_url + "/api/flags")
        if not ok:
            out = proc.stdout.read().decode("utf-8", "replace") if proc.stdout else ""
            proc.kill()
            pytest.fail(f"review_server.py never became ready:\n{out}")
        yield base_url
    finally:
        proc.kill()
        proc.wait(timeout=5)
        if os.path.exists(decisions_path):
            os.remove(decisions_path)


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


@pytest.fixture
def page(browser):
    pg = browser.new_page(viewport={"width": 1600, "height": 1000})
    errors = []
    pg.on("pageerror", lambda exc: errors.append(str(exc)))
    pg.test_errors = errors  # attach for assertions
    yield pg
    pg.close()


def test_nav_populates_and_no_console_errors(server, page):
    page.goto(server + "/", wait_until="networkidle", timeout=15000)
    page.wait_for_timeout(500)
    nav_items = page.locator(".nav-item")
    assert nav_items.count() == 222
    assert page.test_errors == []


def test_klal_lazy_mounts_with_real_content(server, page):
    page.goto(server + "/", wait_until="networkidle", timeout=15000)
    page.wait_for_timeout(800)
    block = page.locator("#klal-block-1")
    assert block.get_attribute("data-mounted") == "true"
    assert "טרם" not in block.inner_text()  # placeholder text ("…") is gone
    assert len(block.inner_text()) > 20


def _find_disputed_klal():
    # Which klal actually has a `current_text_may_be_wrong` candidate isn't
    # fixed - it shrinks over time as corrections get crop-checked and
    # applied (see PROJECT-STATUS.md), so a hardcoded klal_id or a bare
    # ".flag-word.state-open".first (which only searches whatever happens
    # to be lazy-mounted within the initial viewport) is brittle. Look the
    # current one up directly instead.
    with open(os.path.join(REPO, "corrections_part1.json"), encoding="utf-8") as f:
        data = json.load(f)
    for kid in sorted(data.keys(), key=int):
        if any(c.get("flag") == "current_text_may_be_wrong" for c in data[kid]):
            return int(kid)
    return None


def test_candidate_override_flow_persists_and_does_not_touch_part1json(server, page):
    before_hash = _file_sha256(PART1_PATH)
    klal_id = _find_disputed_klal()
    assert klal_id is not None, "no current_text_may_be_wrong candidate exists to test against"

    page.goto(server + "/", wait_until="networkidle", timeout=15000)
    page.wait_for_timeout(500)
    page.click(f"#nav-{klal_id}")
    page.wait_for_timeout(500)

    disputed = page.locator(f"#klal-block-{klal_id} .flag-word.state-open").first
    disputed.click()
    page.wait_for_selector("#candidate-panel.open", timeout=5000)

    options = page.locator(".candidate-option")
    assert options.count() >= 1

    # switch to whichever option isn't already active, save a note
    options.first.click()
    page.fill("#decision-note", "e2e test note")
    page.click("#save-decision-btn")
    page.wait_for_selector("#save-status.show", timeout=5000)

    # a recorded decision always wins the tri-state, so the word span
    # should now show the human-resolved (green) state regardless of what
    # it was before
    page.click("#candidate-panel-close")
    assert page.locator(".flag-word.state-human").count() >= 1

    # reload from scratch and confirm the decision persisted server-side,
    # not just in the page's in-memory state - navigate back to the same
    # klal explicitly rather than assuming it's within whatever lazily
    # mounts in the initial viewport after a fresh load.
    page.goto(server + "/", wait_until="networkidle", timeout=15000)
    page.wait_for_timeout(500)
    page.click(f"#nav-{klal_id}")
    page.wait_for_timeout(500)
    assert page.locator(f"#klal-block-{klal_id} .flag-word.state-human").count() >= 1

    after_hash = _file_sha256(PART1_PATH)
    assert before_hash == after_hash, "a recorded decision must never touch part1.json directly"


def test_klal_flag_panel_saves_and_shows_in_nav(server, page):
    page.goto(server + "/", wait_until="networkidle", timeout=15000)
    page.wait_for_timeout(500)

    page.locator(".klal-flag-btn").first.click()
    page.wait_for_selector("#klal-flag-panel.open", timeout=5000)
    page.check("#needs-revisit-checkbox")
    page.fill("#klal-flag-note", "e2e klal flag note")
    page.click("#save-klal-flag-btn")
    page.wait_for_selector("#klal-flag-save-status.show", timeout=5000)
    page.click("#klal-flag-panel-close")

    page.check("#filter-flagged")
    page.wait_for_timeout(300)
    visible_items = page.locator(".nav-item:visible")
    assert visible_items.count() == 1
    assert "1" == visible_items.first.locator(".nid").inner_text()


def test_decisions_api_reflects_saved_state(server):
    import urllib.request
    with urllib.request.urlopen(server + "/api/klal/1/flag") as resp:
        data = json.loads(resp.read())
    # written by test_klal_flag_panel_saves_and_shows_in_nav, which runs
    # earlier in this module (pytest runs test functions in file order by
    # default within a module-scoped server fixture)
    assert data["needs_revisit"] is True
    assert data["note"] == "e2e klal flag note"
