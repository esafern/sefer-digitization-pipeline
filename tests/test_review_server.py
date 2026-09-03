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
import re
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

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
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except Exception:
            time.sleep(0.2)
    return False


def _get_json(server, path):
    with urllib.request.urlopen(server + path) as resp:
        return json.loads(resp.read())


def _post_json(server, path, body):
    """Returns (status, payload). A 4xx/5xx is returned like any other
    response rather than raised - several tests assert on the rejection."""
    req = urllib.request.Request(
        server + path, data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def _open_dashboard(page, server, klal_id=None):
    """Load the dashboard and, optionally, navigate to a specific klal.
    Navigating explicitly (rather than trusting that a klal happens to be
    inside the initial viewport) matters: klal blocks mount lazily, so a
    bare `.first` selector only ever searches what loaded on screen."""
    # `networkidle` is the wrong gate here and it made two tests flaky
    # (2026-08-25): index.html pulls a Google Fonts stylesheet, so "no network
    # activity for 500ms" depends on a THIRD-PARTY host answering, not on the
    # dashboard being ready. Wait for the app's own readiness signal instead -
    # the nav list is built from /api/klalim, so its first item existing means
    # the page has loaded, fetched and rendered.
    page.goto(server + "/", wait_until="domcontentloaded", timeout=15000)
    page.wait_for_selector(".nav-item", timeout=15000)
    page.wait_for_timeout(500)
    if klal_id is not None:
        page.click(f"#nav-{klal_id}")
        page.wait_for_timeout(500)


@pytest.fixture(scope="module")
def server():
    port = _free_port()
    decisions_path = tempfile.mktemp(suffix=".jsonl", prefix="test_review_decisions_")
    with open(decisions_path, "w", encoding="utf-8") as f:
        pass
    env = dict(os.environ)
    env["REVIEW_DECISIONS_PATH"] = decisions_path

    # FIXED 2026-08-25. This used stdout=PIPE with nobody reading it. The server
    # logs one line per request, so once ~64KB of log filled the OS pipe buffer
    # the server BLOCKED on write and stopped answering - and the symptom was a
    # page load timing out against a server that answers in 0.01s when you probe
    # it by hand. It only appeared once this module grew past ~24 browser tests,
    # which is why it read as flakiness: the last two tests in the file were the
    # ones that happened to arrive after the buffer filled. Log to a file the
    # fixture can still dump on failure.
    log = open(decisions_path + ".serverlog", "w+")
    proc = subprocess.Popen(
        [sys.executable, os.path.join(REPO, "pipeline", "review_server.py"), "--port", str(port)],
        cwd=REPO, env=env,
        stdout=log, stderr=subprocess.STDOUT,
    )
    base_url = f"http://127.0.0.1:{port}"
    try:
        ok = _wait_for_server(base_url + "/api/flags")
        if not ok:
            log.flush(); log.seek(0)
            out = log.read()
            proc.kill()
            pytest.fail(f"review_server.py never became ready:\n{out}")
        yield base_url
    finally:
        proc.kill()
        proc.wait(timeout=5)
        log.close()
        for path in (decisions_path, decisions_path + ".serverlog"):
            if os.path.exists(path):
                os.remove(path)


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


def test_the_title_history_endpoint_reports_every_heading_ruling(server):
    """The panel's state comes from HERE, not from the /api/klal cache.

    ADDED 2026-09-03 (item 0BG). openTitlePanel used to read `title_decision`
    out of `mountedKlal` - the /api/klal payload from whenever the klal was
    first scrolled into view, which lives for the whole page session. A tab open
    across a server restart therefore held a payload from before that field
    existed, and the panel explained nothing: the reviewer corrected klal 96's
    heading, reopened, and found it did not "explain my change like the others".

    Decision state is the one thing on that screen that changes while the page
    is open, so it must be fetched, not cached.
    """
    payload = _get_json(server, "/api/klal/1/title-history")
    assert payload["klal_id"] == 1
    assert isinstance(payload["history"], list)
    assert "title" in payload
    # `current` is the newest ruling or None - never absent, so the frontend
    # never has to distinguish "no key" from "no ruling".
    assert "current" in payload

    for row in payload["history"]:
        for field in ("id", "ts", "chosen_text", "applied", "whole", "by_human"):
            assert field in row, f"{field} missing from a heading-history row: {row}"
        assert isinstance(row["applied"], bool), (
            "`applied` is what tells a reviewer whether the heading they are "
            "looking at already reflects the ruling - it must never be absent"
        )


def test_a_recorded_heading_ruling_is_reported_as_not_yet_applied(server):
    """Record one and read it straight back: it must come back UNAPPLIED.

    That distinction is the whole complaint this endpoint answers - recording
    and applying are separate steps here, so a panel that cannot tell them apart
    makes a save that worked look like one that did nothing.
    """
    before = _get_json(server, "/api/klal/2/title-history")
    stored_title = before["title"]

    status, rec = _post_json(server, "/api/decisions/title", {
        "klal_id": 2, "word_index": 0, "whole": True,
        "chosen_text": stored_title,  # a no-op ruling: records without proposing a change
        "note": "test_a_recorded_heading_ruling_is_reported_as_not_yet_applied",
    })
    assert status == 201, rec

    after = _get_json(server, "/api/klal/2/title-history")
    assert len(after["history"]) == len(before["history"]) + 1
    current = after["current"]
    assert current["id"] == rec["id"]
    assert current["applied"] is False, "a freshly recorded ruling has not been applied"
    assert current["whole"] is True
    assert current["was"] == stored_title, (
        "a whole-heading ruling records the ENTIRE stored heading as its drift check"
    )
    assert after["title"] == stored_title, "recording must not change part1.json"


def test_nav_populates_and_no_console_errors(server, page):
    _open_dashboard(page, server)
    nav_items = page.locator(".nav-item")
    assert nav_items.count() == 222
    assert page.test_errors == []


def test_klal_lazy_mounts_with_real_content(server, page):
    _open_dashboard(page, server)
    page.wait_for_timeout(300)
    block = page.locator("#klal-block-1")
    assert block.get_attribute("data-mounted") == "true"
    assert "טרם" not in block.inner_text()  # placeholder text ("…") is gone
    assert len(block.inner_text()) > 20


def _find_klal_with_a_flag_word():
    """A klal that currently HAS a rendered flagged word.

    Hardcoding one is brittle for the reason _find_disputed_klal() already gives,
    and 2026-08-31 proved it: five tests pinned to klal 66 and klal 53 broke at
    once when the reviewer's decisions were applied and
    build_corrections_dataset's new settled-position filter dropped 279 candidates
    those klalim no longer needed. The corpus getting BETTER must not fail the
    suite - a test that depends on a specific defect surviving is testing the
    defect, not the behaviour."""
    with open(os.path.join(REPO, "corrections_part1.json"), encoding="utf-8") as f:
        data = json.load(f)
    for kid in sorted(data.keys(), key=int):
        # A `delete` entry marks a GAP where the corpus has no word at all, so it
        # renders as an omission marker and never as a .flag-word - having an
        # entry is not the same as having a clickable word.
        if any(c.get("opcode") != "delete" for c in data[kid]):
            return int(kid)
    return None


def _find_candidate_position():
    """(klal_id, word_index) of a live, renderable candidate.

    Same lesson as _find_klal_with_a_flag_word(): three tests pinned themselves to
    klal 1 word 85, and klal 1 has no candidates at all once its corrections are
    applied and the settled-position filter drops them. The panel they open needs
    a real entry behind it; which one is not the point of any of them."""
    with open(os.path.join(REPO, "corrections_part1.json"), encoding="utf-8") as f:
        data = json.load(f)
    for kid in sorted(data.keys(), key=int):
        for c in data[kid]:
            if c.get("opcode") != "delete":
                return int(kid), c["word_index"]
    return None, None


def _find_word_containing(char):
    """(klal_id, word_index) of a corpus word containing `char`, or None."""
    with open(PART1_PATH, encoding="utf-8") as f:
        for klal in json.load(f):
            for i, w in enumerate(klal["clean_text"].split(" ")):
                if char in w:
                    return klal["klal_id"], i
    return None


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

    _open_dashboard(page, server, klal_id)

    disputed = page.locator(f"#klal-block-{klal_id} .flag-word.state-open").first
    disputed.click()
    page.wait_for_selector("#disputed-panel.open, #candidate-panel.open", timeout=5000)

    options = page.locator(".disputed-option, .candidate-option")
    assert options.count() >= 1

    # switch to whichever option isn't already active, save a note
    options.first.click()
    page.fill("#decision-note", "e2e test note")
    page.click("#save-decision-btn")
    page.wait_for_selector("#save-status.show", timeout=5000)

    # a recorded decision always wins the tri-state, so the word span
    # should now show the human-resolved (green) state regardless of what
    # it was before
    page.click("#disputed-panel-close, #candidate-panel-close")
    assert page.locator(".flag-word.state-human").count() >= 1

    # reload from scratch and confirm the decision persisted server-side,
    # not just in the page's in-memory state.
    _open_dashboard(page, server, klal_id)
    assert page.locator(f"#klal-block-{klal_id} .flag-word.state-human").count() >= 1

    after_hash = _file_sha256(PART1_PATH)
    assert before_hash == after_hash, "a recorded decision must never touch part1.json directly"


def test_klal_flag_panel_saves_and_shows_in_nav(server, page):
    _open_dashboard(page, server)
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


def test_manual_correction_panel_auto_closes_after_a_save(server, page):
    """REGRESSION 2026-08-25 (reviewer: "after save correction the right pane
    should auto-close").

    The manual-correction panel was the one panel in the app that stayed open
    after a save - it re-opened itself against the fresh post-save state, on the
    reasoning that the refreshed content was the confirmation. It is also the
    panel a reviewer uses most, so it was the one leaving a pane to dismiss by
    hand after every correction. It must now behave like the other four: flash
    the confirmation, hold it, close.

    Asserts the whole sequence, not just the flash - a test that only waited for
    `.save-status.show` would have passed against the old behaviour too."""
    _open_dashboard(page, server, 1)

    page.locator("#klal-block-1 .plain-word").first.click()
    page.wait_for_selector("#manual-panel.open", timeout=5000)

    page.fill("#manual-correction-text", "בדיקה")
    page.fill("#manual-correction-note", "e2e auto-close test")
    page.click("#save-manual-correction-btn")

    # the confirmation is shown...
    page.wait_for_selector("#manual-save-status.show", timeout=5000)
    assert page.locator("#manual-panel.open").count() == 1, (
        "the panel must stay open long enough for the reviewer to see the confirmation")

    # ...and then the panel closes itself, with no click from the reviewer.
    page.wait_for_function(
        "() => !document.querySelector('#manual-panel').classList.contains('open')",
        timeout=6000)
    assert page.locator("#backdrop.open").count() == 0, (
        "auto-close must dismiss the backdrop too, exactly as the X button does")

    # RE-DECIDING an already-decided word must close too (reviewer, klal 167
    # w22: "still doesn't autoclose when i save decision" - reported against a
    # word that already carried a manual_correction, which is a different render
    # path from the plain word above: it comes back as an `opcode: manual` entry
    # with a decision attached, so the panel opens pre-filled).
    page.locator("#klal-block-1 .flag-word.state-human").first.click()
    page.wait_for_selector("#manual-panel.open", timeout=5000)
    assert page.input_value("#manual-correction-text") == "בדיקה", (
        "re-opening a decided word should pre-fill the recorded reading")
    page.fill("#manual-correction-text", "בדיקה2")
    page.click("#save-manual-correction-btn")
    page.wait_for_selector("#manual-save-status.show", timeout=5000)
    page.wait_for_function(
        "() => !document.querySelector('#manual-panel').classList.contains('open')",
        timeout=6000)


def test_deep_link_lands_on_the_klal_and_rings_the_word(server, page):
    """ADDED 2026-08-26 with the deep-link feature (reviewer request): a URL can
    address a klal, or a klal and a word, so a finding written down anywhere can
    carry a link that lands on it.

    The first working version was defeated by the app's own scroll observer -
    jumpTo() scrolls SMOOTHLY, the observer calls setActiveKlal() on whatever
    drifts past during the animation, and routing to klal 66 landed on klal 61
    with no word ringed. That is what this test pins: not that the hash parses,
    but that the reviewer actually ends up on the right word."""
    page.goto(server + "/#klal=66", wait_until="domcontentloaded", timeout=15000)
    page.wait_for_selector(".nav-item", timeout=15000)
    page.wait_for_timeout(1500)
    assert page.eval_on_selector(".nav-item.active", "el => el.dataset.klalId") == "66"

    page.goto(server + "/#klal=66&word=135", wait_until="domcontentloaded", timeout=15000)
    page.wait_for_selector(".nav-item", timeout=15000)
    page.wait_for_timeout(2500)
    assert page.eval_on_selector(".nav-item.active", "el => el.dataset.klalId") == "66"
    ringed = page.eval_on_selector_all(".routed-word", "els => els.map(e => e.textContent)")
    assert len(ringed) == 1, f"expected exactly one ringed word, got {ringed}"
    assert page.test_errors == []


def test_clicking_a_word_puts_it_in_the_address_bar(server, page):
    """The address bar has to be copyable as-is, or the deep links are write-only.
    replaceState, not pushState: a reviewer moving through a klal must not have to
    press Back forty times to leave."""
    _open_dashboard(page, server, klal_id=92)
    page.wait_for_timeout(800)      # let the mount settle before clicking into it
    page.eval_on_selector('#klal-block-92 [data-word-index="440"]', "el => el.click()")
    page.wait_for_timeout(800)
    assert page.evaluate("location.hash") == "#klal=92&word=440"
    assert page.test_errors == []


def test_correction_panel_header_copies_the_reference_and_link(server, page):
    """ADDED 2026-08-26 (reviewer request). The klal/word header in a correction
    panel is also a copy control: it yields the readable reference AND the deep
    link, so a finding can be pasted into a note without anyone retyping an
    index. Asserted end to end rather than by reading the markup - a copy button
    that silently does nothing is the dead-control shape this file has shipped
    more than once."""
    page.context.grant_permissions(["clipboard-read", "clipboard-write"])
    page.goto(server + "/#klal=66&word=135", wait_until="domcontentloaded", timeout=15000)
    page.wait_for_selector(".nav-item", timeout=15000)
    page.wait_for_timeout(2200)
    page.eval_on_selector('#klal-block-66 [data-word-index="135"]', "el => el.click()")
    page.wait_for_timeout(900)
    # scoped to the PANEL: the hover card also renders a .copy-ref
    btn = page.query_selector(".side-panel.open .copy-ref")
    assert btn, "the panel header carries no copy control"
    btn.click()
    page.wait_for_timeout(600)
    copied = page.evaluate("navigator.clipboard.readText()")
    assert "Klal 66" in copied and "Word #135" in copied, copied
    # the PASTE-SAFE path form, not the hash form: `&` is routinely truncated
    # when a URL is pasted into a terminal or a chat window
    assert "/klal/66/word/135" in copied, copied
    assert page.test_errors == []


def test_shareable_path_link_redirects_to_the_deep_link(server, page):
    """ADDED 2026-08-26 (reviewer: "sadly those links you shared here in the chat
    are not clickable"). `/#klal=66&word=135` is what the frontend routes on, but
    it does not survive being pasted: terminals do not hyperlink Markdown link
    syntax, and several that linkify a bare URL truncate at the `&` - opening the
    right klal at the wrong word, which is worse than failing outright.
    `/klal/66/word/135` contains no `#` and no `&`."""
    page.goto(server + "/klal/66/word/135", wait_until="domcontentloaded", timeout=15000)
    page.wait_for_selector(".nav-item", timeout=15000)
    page.wait_for_timeout(2500)
    assert page.url.endswith("/#klal=66&word=135"), page.url
    assert page.eval_on_selector(".nav-item.active", "el => el.dataset.klalId") == "66"
    assert page.eval_on_selector_all(".routed-word", "els => els.length") >= 1
    assert page.test_errors == []


def test_hovering_any_word_offers_its_reference_and_a_copy_control(server, page):
    """ADDED 2026-08-26 (reviewer: "hovering over any word should always surface a
    floating box with the klal + word and an icon to copy the link").

    Every word is addressable, so every word should say what its address is
    without being clicked - and PLAIN words previously said nothing at all. The
    card has to be HOVERABLE, not a tooltip: `#tooltip` sets pointer-events:none
    so it can never swallow a click, which makes it the wrong element for
    something holding a button. Asserted by actually moving onto the card and
    clicking, because a control you cannot reach is the failure mode here."""
    page.context.grant_permissions(["clipboard-read", "clipboard-write"])
    page.goto(server + "/klal/66", wait_until="domcontentloaded", timeout=15000)
    page.wait_for_selector(".nav-item", timeout=15000)
    page.wait_for_timeout(2000)

    page.hover('#klal-block-66 .plain-word[data-word-index="10"]')
    page.wait_for_timeout(400)
    assert page.is_visible("#word-card")
    # "Klal 66 (סו) · Word #10" - the id to navigate by AND the marker the book
    # prints, which is what the reviewer is looking at on the scan.
    ref = page.inner_text("#word-card .wc-ref")
    assert "Klal 66" in ref and "Word #10" in ref, ref
    assert "סו" in ref, f"the klal's gematria is missing from the reference: {ref}"

    # move onto the card: it must survive leaving the word, or the button is
    # unreachable no matter how it is styled
    page.hover("#word-card .copy-ref")
    page.wait_for_timeout(400)
    assert page.is_visible("#word-card"), "the card closed before the pointer reached it"

    page.click("#word-card .copy-ref")
    page.wait_for_timeout(500)
    copied = page.evaluate("navigator.clipboard.readText()")
    assert "Klal 66" in copied and "Word #10" in copied and "סו" in copied, copied
    assert "/klal/66/word/10" in copied, copied   # the paste-safe path form
    assert page.test_errors == []


def test_a_flagged_word_shows_exactly_one_floating_box_with_the_detail(server, page):
    """REGRESSION 2026-08-26 (reviewer: "we don't need both boxes when it is a
    disputed word, just the big one with the details").

    A flagged word in the text pane was showing TWO at once: `#tooltip` from
    attachWordHandlers and `#word-card` from the hover delegation. They are now
    one box - the card, because it is the only one that can hold the copy control
    (`#tooltip` is pointer-events:none by design so it can never swallow a click
    on the scan pane, where it is still used). The card renders the SAME detail
    via the shared wordDetailHtml(), so suppressing the tooltip here loses
    nothing. The card also takes over any native `title`, which would otherwise
    be a third box."""
    # Looked up, not hardcoded: klal 66 carried the flagged word this was written
    # against until 2026-08-31, when the reviewer settled every one of them.
    kid = _find_klal_with_a_flag_word()
    assert kid is not None, "no klal currently carries a flagged word to test with"
    page.goto(server + f"/klal/{kid}", wait_until="domcontentloaded", timeout=15000)
    page.wait_for_selector(".nav-item", timeout=15000)
    page.wait_for_timeout(2000)
    fw = page.query_selector(f"#klal-block-{kid} .flag-word[data-word-index]")
    assert fw, f"klal {kid} has no flagged word to test with"
    fw.hover()
    page.wait_for_timeout(500)
    assert page.is_visible("#word-card")
    assert not page.is_visible("#tooltip"), "the old tooltip still appears beside the card"
    assert fw.get_attribute("title") in (None, ""), "native title still present beside the card"
    # the one box must carry the detail the suppressed tooltip used to show
    text = page.inner_text("#word-card")
    assert "Word #" in text and "Klal" in text, text
    assert "reading" in text.lower() or "scan appears" in text.lower(), text
    assert page.query_selector("#word-card .copy-ref"), "the merged box lost its copy control"
    assert page.test_errors == []


def test_clicking_a_word_zooms_and_centres_the_scan_on_it(server, page):
    """ADDED 2026-08-26 (reviewer: "when i click on a word, zoom in and center on
    that word in the scan panel"). Adjudicating a ס/פ or a ד/ר means reading one
    glyph, and at 100% the page is too small to do that.

    Two properties, and the second is the one that would annoy: the click zooms
    IN to a reading level, and it never zooms OUT - a reviewer who has gone to
    300% to read a worn sort must not be yanked back by their next click."""
    page.goto(server + "/klal/66", wait_until="domcontentloaded", timeout=15000)
    page.wait_for_selector(".nav-item", timeout=15000)
    page.wait_for_timeout(2200)
    assert page.inner_text("#zoom-level") == "100%"

    page.eval_on_selector('#klal-block-66 [data-word-index="200"]', "el => el.click()")
    page.wait_for_timeout(2500)
    assert page.inner_text("#zoom-level") == "220%", page.inner_text("#zoom-level")

    # Centred on each axis, UNLESS the scroll is clamped at a page edge - a word
    # in the last line cannot be pulled to the middle of the viewport, and
    # asserting otherwise would only be asserting the viewport size. The property
    # is "as centred as the axis allows".
    off = page.evaluate("""() => {
      const v = document.getElementById('scan-viewer');
      const b = document.querySelector('.hl-box.focused');
      if (!b) return null;
      const vr = v.getBoundingClientRect(), br = b.getBoundingClientRect();
      // RTL makes scrollLeft run 0 -> negative, hence the abs()
      const maxX = v.scrollWidth - v.clientWidth, maxY = v.scrollHeight - v.clientHeight;
      return {
        dx: (br.left + br.width/2) - (vr.left + vr.width/2),
        dy: (br.top + br.height/2) - (vr.top + vr.height/2),
        clampedX: Math.abs(v.scrollLeft) < 2 || Math.abs(Math.abs(v.scrollLeft) - maxX) < 2,
        clampedY: v.scrollTop < 2 || Math.abs(v.scrollTop - maxY) < 2,
      };
    }""")
    assert off is not None, "no focused box on the scan"
    assert off["clampedX"] or abs(off["dx"]) < 12, off
    assert off["clampedY"] or abs(off["dy"]) < 12, off

    # a manual zoom beyond the target survives the next click
    for _ in range(3):
        page.click("#zoom-in")
    page.wait_for_timeout(600)
    zoomed = page.inner_text("#zoom-level")
    page.eval_on_selector('#klal-block-66 [data-word-index="10"]', "el => el.click()")
    page.wait_for_timeout(2000)
    assert page.inner_text("#zoom-level") == zoomed, (
        f"the click zoomed back out from {zoomed} to {page.inner_text('#zoom-level')}")
    assert page.test_errors == []


def test_clicking_away_restores_the_zoom_and_the_klal_outline(server, page):
    """ADDED 2026-08-26 (reviewer: "clicking away returns the highlight to the
    entire klal correctly and should also zoom back out to 100").

    The zoom is the other half of the click-to-focus gesture and has to undo with
    it, or the reviewer is left at 220% looking at a page they have stopped
    inspecting. It restores what was there BEFORE the focus rather than a hard
    100%: a reviewer who had zoomed to 200% by hand to study the page keeps it
    when they dismiss a word - the normal flow starts at 100% and so returns
    there, which is the requested behaviour without stepping on a manual zoom."""
    page.goto(server + "/klal/66", wait_until="domcontentloaded", timeout=15000)
    page.wait_for_selector(".nav-item", timeout=15000)
    page.wait_for_timeout(2200)
    assert page.inner_text("#zoom-level") == "100%"

    page.eval_on_selector('#klal-block-66 [data-word-index="200"]', "el => el.click()")
    page.wait_for_timeout(2200)
    assert page.inner_text("#zoom-level") == "220%"

    page.keyboard.press("Escape")
    page.wait_for_timeout(1800)
    assert page.inner_text("#zoom-level") == "100%", page.inner_text("#zoom-level")
    assert page.eval_on_selector_all(".hl-current-klal", "e => e.length") > 0, (
        "the whole-klal outline did not come back")

    # a zoom the reviewer set themselves survives a focus/dismiss cycle
    for _ in range(4):
        page.click("#zoom-in")
    page.wait_for_timeout(600)
    manual = page.inner_text("#zoom-level")
    page.eval_on_selector('#klal-block-66 [data-word-index="100"]', "el => el.click()")
    page.wait_for_timeout(1800)
    page.keyboard.press("Escape")
    page.wait_for_timeout(1800)
    assert page.inner_text("#zoom-level") == manual, (
        f"a manual zoom of {manual} was reset to {page.inner_text('#zoom-level')}")
    assert page.test_errors == []


def test_index_stamps_asset_versions_from_the_files_themselves(server):
    """ADDED 2026-08-25. index.html shipped a hand-maintained `?v=6` that was last
    bumped in 1e59522 and never again, through every app.js change since. The
    reviewer reported a fix as not working on a tab that had been open since
    before it landed - running the old file. The stamp is now derived from the
    file's own mtime and size, so it changes whenever the asset does and nobody
    has to remember."""
    import re as _re
    import urllib.request
    with urllib.request.urlopen(server + "/") as resp:
        html = resp.read().decode("utf-8")
    stamps = dict(_re.findall(r"/(app\.(?:js|css))\?v=([^\"']+)", html))
    assert set(stamps) == {"app.js", "app.css"}, f"expected both assets stamped, got {stamps}"
    for name, stamp in stamps.items():
        assert stamp != "6", f"{name} still carries the stale hand-maintained version"
        st = os.stat(os.path.join(REPO, "review_frontend", name))
        assert stamp == f"{int(st.st_mtime)}-{st.st_size}", (
            f"{name}'s stamp must follow the file: got {stamp}")


def test_a_suggested_replacement_is_a_word_not_a_number_from_the_note(server, page):
    """REGRESSION 2026-08-25, reviewer: "klal 1 word 229 - proposed correction is
    a serious bug."

    It was. The panel offered to replace `דנראח` with **`6.18M`**. That flag's
    note mentions the reference corpus growing "2.58M->6.18M words" long before
    it says the stored form is one substitution "('ח'->'ה') away from 'דנראה'",
    and the old extractor took the FIRST arrow in the string. The "Use ..."
    button then saved on a single click with nothing in between, so one click
    recorded a file-size figure as the reading of the first klal of the work.

    Swept at the time: of 261 open word-level flags carrying a suggestion, 39
    proposed a string with no Hebrew letter in it (12 of them literally
    `6.18M`) and 27 proposed something containing `?`.

    Seeds the real note through the API so the assertion runs against the exact
    text that produced the bug. The note is what is under test, not the position.

    MOVED off word 229 on 2026-08-30, when the `דנראח`->`דנראה` decision this
    note describes was finally applied to the corpus. That made part1.json
    disagree with DocAI's raw reading at 229 for the first time, so the next
    rebuild generated a `replace` candidate there - and a real candidate
    outranks a synthesized ai_flag by design (_claim_word_index: "the richer
    entry wins"), so the word stopped rendering as .state-ai-flag and this test
    hung on its selector. Every applied correction creates a candidate at its
    own position that way, so the fix is to seed at a word that carries no
    candidate rather than to loosen the selector - clicking by data-word-index
    would open the candidate panel instead and assert nothing about the
    suggestion extractor, which is the whole point here."""
    real_note = (
        "Lexicon-gap detector re-run 2026-08-17/18 against the EXPANDED independent "
        "reference corpus (added Mishneh Torah + Tur + Rashi on Talmud to the existing "
        "Shulchan Arukh + Talmud Bavli set, 2.58M->6.18M words) - this candidate's "
        "confusable neighbor didn't clear the attestation floor in the smaller corpus. "
        "Stored form 'דנראח' has ZERO attestation in the expanded corpus and is one "
        "letter-substitution ('ח'->'ה') away from 'דנראה' (43x independently attested)."
    )
    body = json.dumps({"klal_id": 1, "word_index": 224, "needs_revisit": True,
                       "note": real_note}).encode("utf-8")
    req = urllib.request.Request(server + "/api/decisions/klal_flag", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        assert resp.status in (200, 201)

    _open_dashboard(page, server, 1)
    page.locator("#klal-block-1 .flag-word.state-ai-flag").first.click()
    page.wait_for_selector("#manual-panel.open", timeout=5000)

    panel = page.locator("#manual-panel").inner_text()
    assert "6.18M" not in panel, "the panel is offering a corpus-size figure as a reading"
    assert "??" not in panel, "the panel is offering the detectors' no-candidate marker"
    # the correct reading IS derivable from this note, so it must be the one offered
    assert "דנראה" in panel, f"expected the attested reading to be suggested; panel was:\n{panel}"
    assert page.input_value("#manual-correction-text") in ("", "דנראה"), (
        "the text box must be empty or pre-filled with the plausible suggestion")


def test_the_use_suggestion_button_fills_the_box_without_saving(server, page):
    """The other half of the same report. `Use "X"` used to click Save itself, so
    a reviewer accepted a proposed reading without ever seeing it in the box.
    Success criterion #1 - resolved by looking, not inferred - makes that the
    wrong default no matter how good the suggestion is."""
    real_note = "שחפך w110 → שהפך | INTRA: כ for ה in a common verb"
    body = json.dumps({"klal_id": 1, "word_index": 100, "needs_revisit": True,
                       "note": real_note}).encode("utf-8")
    req = urllib.request.Request(server + "/api/decisions/klal_flag", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        assert resp.status in (200, 201)

    _open_dashboard(page, server, 1)
    page.locator("#klal-block-1 .flag-word.state-ai-flag").first.click()
    page.wait_for_selector("#manual-panel.open", timeout=5000)
    if page.locator("#use-suggested-word-btn").count() == 0:
        pytest.skip("no suggestion offered for the seeded flag")
    page.click("#use-suggested-word-btn")
    page.wait_for_timeout(400)
    assert page.locator("#manual-panel.open").count() == 1, (
        "filling the suggestion must NOT save and close - the reviewer has not agreed yet")
    assert page.locator("#manual-save-status.show").count() == 0, (
        "no decision may be recorded until the reviewer presses Save")


def test_a_multi_page_klal_is_outlined_on_its_continuation_pages_too(server, page):
    """REGRESSION 2026-08-25 (reviewer, klal 4: "the highlight of the whole klal
    only covers the first part on the first page, not the rest on the
    following").

    showPage() drew `region` and only when `focusKlal.page === page`, so a klal
    starting at the bottom of page 15 and running down page 16 outlined the
    sliver on 15 and nothing at all on 16 - where most of its text is. The
    per-page boxes were already served in `continuations[]` and never read."""
    klal_id = 4
    klal = _get_json(server, f"/api/klal/{klal_id}")
    conts = klal.get("continuations") or []
    if not conts:
        pytest.skip(f"klal {klal_id} is no longer multi-page")
    cont_page = conts[0]["page"]
    assert cont_page != klal["page"], "continuation must be on a different page"

    _open_dashboard(page, server, klal_id)
    page.wait_for_selector(f"#klal-block-{klal_id}", timeout=8000)
    # Let the mount's own scroll-driven showPage() settle first, or it lands
    # after ours and repaints the start page's box over the answer.
    page.wait_for_timeout(1200)
    page.evaluate(f"showPage({cont_page}, {klal_id})")

    # Assert the GEOMETRY, not just that a box exists: it has to be the
    # continuation's OWN bbox. Counting boxes alone passes against the pre-fix
    # code the moment anything draws one - the same trap the old nav-count
    # invariant fell into. Polled rather than sampled, since showPage is async.
    expected_top = round(conts[0]["bbox"]["y1"] * 100, 3)
    page.wait_for_function(
        """(want) => {
            const el = document.querySelector('#hl-container .hl-current-klal');
            if (!el) return false;
            return Math.abs(parseFloat(el.style.top) - want) < 0.01;
        }""",
        arg=expected_top, timeout=8000)
    assert page.locator("#hl-container .hl-current-klal").count() == 1


def test_clicking_a_manually_corrected_word_focuses_it_on_the_scan(server, page):
    """REGRESSION 2026-08-25 (reviewer, klal 4: "clicking on word 95 does not
    highlight that word"). Every other flagged-word branch in renderKlalBody
    calls showPage() before opening its panel; the `manual` branch opened the
    panel and left the scan pane alone. The box was always served - api_page()'s
    plain-word pass covers every aligned word - nothing asked for it."""
    _open_dashboard(page, server, 1)
    page.locator("#klal-block-1 .plain-word").first.click()
    page.wait_for_selector("#manual-panel.open", timeout=5000)
    page.fill("#manual-correction-text", "בדיקה")
    page.click("#save-manual-correction-btn")
    page.wait_for_function(
        "() => !document.querySelector('#manual-panel').classList.contains('open')",
        timeout=8000)

    # now click the word again - it is a `manual` entry this time
    page.locator("#klal-block-1 .flag-word.state-human").first.click()
    page.wait_for_selector("#manual-panel.open", timeout=5000)
    page.wait_for_timeout(600)
    assert page.locator("#hl-container .hl-box.focused").count() >= 1, (
        "clicking a manually-corrected word must focus its box on the scan pane")


def test_an_accepted_omission_shows_the_text_it_will_insert(server, page):
    """REGRESSION 2026-08-25 (reviewer, klal 219: "i decided to add the proposed
    text - but that text is not seen in the middle pane").

    A `possible_omission` candidate is words the scan has and the corpus lacks;
    accepting one is a decision to ADD them. It rendered as a bare coloured
    sliver, with the accepted text reachable only by hovering - so while reading
    the klal there was no way to see what had been agreed to. A pending
    REPLACEMENT has shown its incoming text inline since 2026-08-17."""
    klal_id, gap = None, None
    for kid in (219, 4, 30, 88, 91):
        for c in _get_json(server, f"/api/klal/{kid}")["corrections"]:
            if c.get("opcode") == "delete":
                klal_id, gap = kid, c
                break
        if gap:
            break
    if not gap:
        pytest.skip("no omission candidate served to test against")

    body = json.dumps({"klal_id": klal_id, "word_index": gap["word_index"],
                       "chosen_source": "docai_reading",
                       "chosen_text": "טקסט חדש"}).encode("utf-8")
    req = urllib.request.Request(server + "/api/decisions/disputed", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        assert resp.status in (200, 201)

    _open_dashboard(page, server, klal_id)
    page.wait_for_selector(f"#klal-block-{klal_id}", timeout=8000)
    text = page.locator(f"#klal-block-{klal_id}").inner_text()
    assert "טקסט חדש" in text, (
        "an accepted omission must show the text it will insert, not only a coloured gap")


def test_clicking_blank_text_closes_the_panel_but_clicking_a_word_does_not(server, page):
    """ADDED 2026-08-25 (user request: "clicking away (in a blank part of the
    middle pane) should cancel that and close the right pane").

    The backdrop deliberately does not cover the text pane, so a reviewer can
    click straight from one word to the next without dismissing first - which
    left a click on the prose itself with no way to say "never mind".

    Asserts BOTH halves: blank space closes, and a word does not. Testing only
    the close would pass against a handler that dismissed on every click in the
    pane, which would make word-to-word review impossible."""
    _open_dashboard(page, server, 1)
    page.locator("#klal-block-1 .plain-word").first.click()
    page.wait_for_selector("#manual-panel.open", timeout=5000)

    # a click on another word must NOT close it - it retargets
    page.locator("#klal-block-1 .plain-word").nth(3).click()
    page.wait_for_timeout(300)
    assert page.locator(".side-panel.open").count() == 1, (
        "clicking another word must move the panel, not close it")

    # A click on blank space inside the text pane cancels. Pick a point the
    # open panel does not cover and PROVE it first - the panel is positioned
    # over the right-hand side of the pane, so an obvious-looking corner lands
    # on the panel itself and the test would be asserting nothing.
    box = page.locator("#text-scroll").bounding_box()
    x, y = box["x"] + 6, box["y"] + 6
    hit = page.evaluate(
        "(pt) => { const el = document.elementFromPoint(pt[0], pt[1]); return el && el.id; }",
        [x, y])
    assert hit == "text-scroll", f"expected blank text-pane at ({x},{y}), hit {hit!r}"
    page.mouse.click(x, y)
    page.wait_for_function(
        "() => document.querySelectorAll('.side-panel.open').length === 0", timeout=5000)


def test_decisions_api_reflects_saved_state(server):
    data = _get_json(server, "/api/klal/1/flag")
    # written by test_klal_flag_panel_saves_and_shows_in_nav, which runs
    # earlier in this module (pytest runs test functions in file order by
    # default within a module-scoped server fixture)
    assert data["needs_revisit"] is True
    assert data["note"] == "e2e klal flag note"


# --- API-level behaviour (no browser needed) --------------------------------

def test_a_manual_correction_whose_word_has_moved_is_not_rendered(server):
    """Drift check added 2026-08-14. Unlike candidate/punctuation decisions -
    which can only surface where a live candidate entry exists at that index -
    every recorded manual_correction used to render unconditionally. After an
    edit that shifts word positions, an old decision's word_index lands on an
    unrelated word, and the dashboard would show THAT word as Human-Decided
    with someone else's chosen text attached (PROJECT-STATUS.md's 2026-08-13
    reindexing incident, in miniature).
    """
    klal = _get_json(server, "/api/klal/1")
    real_word = klal["clean_text"].split(" ")[4]

    status, _ = _post_json(server, "/api/decisions/manual", {
        "klal_id": 1, "word_index": 4, "original_word": "לא-המילה-הזאת",
        "chosen_text": "תחליף", "note": "drifted decision",
    })
    assert status == 201, "the server records the decision either way - rendering is what's gated"
    entries = [c for c in _get_json(server, "/api/klal/1")["corrections"] if c["opcode"] == "manual"]
    assert not [c for c in entries if c["word_index"] == 4], (
        "a manual correction whose snapshotted original_word no longer matches the live text at "
        "that index must not be rendered"
    )

    _post_json(server, "/api/decisions/manual", {
        "klal_id": 1, "word_index": 4, "original_word": real_word,
        "chosen_text": "תחליף", "note": "current decision",
    })
    entries = [c for c in _get_json(server, "/api/klal/1")["corrections"] if c["opcode"] == "manual"]
    assert [c for c in entries if c["word_index"] == 4], (
        "a manual correction that still matches the live word must be rendered"
    )


def test_manual_correction_requires_an_explicit_chosen_text(server):
    """chosen_text == "" means DELETE this word; a MISSING chosen_text is a
    client bug and must be rejected rather than silently recorded as one or
    the other."""
    status, payload = _post_json(server, "/api/decisions/manual", {
        "klal_id": 1, "word_index": 0, "original_word": "x",
    })
    assert status == 400 and "chosen_text" in payload["error"]


def test_every_flag_the_api_serves_has_a_label(server):
    """The same property tests/test_pipeline_logic.py checks against
    review_server.FLAG_LABELS directly, asserted here end-to-end: through the
    real /api/flags the frontend consumes, against the real
    /api/klal payloads it renders."""
    labels = _get_json(server, "/api/flags")
    served = set()
    for klal_id in (1, 4, 30, 88, 168, 222):
        served |= {c["flag"] for c in _get_json(server, f"/api/klal/{klal_id}")["corrections"]}
    # 'manual_correction' is deliberately not in FLAG_LABELS: manual entries
    # have their own render path in app.js (renderKlalBody's opcode === 'manual'
    # branch) and never look a flag up.
    unlabelled = sorted(f for f in served if f not in labels and f != "manual_correction")
    assert not unlabelled, f"flag(s) served by /api/klal with no /api/flags label: {unlabelled}"


# --- nav refresh: dedup, error handling, highlight restore ------------------
# Added 2026-08-14. The refresh path itself was written the same day (audit
# item 5 + its code-review follow-ups) and verified only by ad-hoc browser
# automation in that session - nothing repeatable covered it.

def test_concurrent_nav_refreshes_share_one_round_of_requests(server, page):
    _open_dashboard(page, server)
    counts = page.evaluate("""async () => {
      const seen = [];
      const realFetch = window.fetch;
      window.fetch = (...args) => { seen.push(String(args[0])); return realFetch(...args); };
      try {
        await Promise.all([refreshKlalimList(), refreshKlalimList(), refreshKlalimList()]);
      } finally {
        window.fetch = realFetch;
      }
      return ['/api/flags', '/api/klalim', '/api/witness']
        .map(u => seen.filter(s => s.includes(u)).length);
    }""")
    assert counts == [1, 1, 1], (
        f"three concurrent refreshes fired {counts} requests for /api/flags, /api/klalim, "
        "/api/witness - they must dedupe onto one in-flight fetch"
    )
    assert page.test_errors == []


def test_a_failed_nav_refresh_is_caught_and_leaves_the_next_one_working(server, page):
    _open_dashboard(page, server)
    recovered = page.evaluate("""async () => {
      const realFetch = window.fetch;
      window.fetch = () => Promise.reject(new Error('simulated server restart'));
      try {
        await refreshKlalimList();
      } finally {
        window.fetch = realFetch;
      }
      // The in-flight guard must have been cleared in `finally`, or every
      // later refresh returns the same rejected promise forever.
      await refreshKlalimList();
      return KLALIM.length;
    }""")
    assert recovered == 222
    assert page.test_errors == [], (
        "a failed refresh must be caught and logged, not surface as an unhandled rejection"
    )


def test_nav_highlight_and_flagged_filter_survive_a_nav_rebuild(server, page):
    """refreshKlalimList() rebuilds the nav via innerHTML, which wipes both
    the '.active' highlight and the flagged-only filter's applied display
    state. Both are restored explicitly (setActiveKlal + applyFlaggedFilter);
    without that, a reviewer scrolled deep into the corpus loses their place
    the moment any save or tab-return triggers a refresh.
    """
    # Flag the klal this test navigates to, so it stays visible under the
    # filter and the test doesn't depend on what an earlier test happened to
    # flag first.
    _post_json(server, "/api/decisions/klal_flag",
               {"klal_id": 150, "needs_revisit": True, "note": "nav rebuild test"})
    _open_dashboard(page, server, klal_id=150)
    # jumpTo() smooth-scrolls, and the scroll observer keeps updating the
    # active row until it settles - read whichever row is active once it has,
    # rather than assuming it is still the one that was clicked.
    page.wait_for_timeout(1500)
    active_before = page.evaluate("document.querySelector('.nav-item.active')?.id")
    assert active_before is not None

    page.check("#filter-flagged")
    page.wait_for_timeout(200)
    flagged_before = page.locator(".nav-item:visible").count()
    assert flagged_before >= 1

    page.evaluate("refreshKlalimList()")
    page.wait_for_timeout(500)

    assert page.evaluate("document.querySelector('.nav-item.active')?.id") == active_before, (
        "the active nav row must survive a rebuild"
    )
    assert page.locator(".nav-item:visible").count() == flagged_before, (
        "the flagged-only filter must still be applied after a rebuild"
    )


# --- HTML escaping in review_frontend/app.js (round-2 audit, 2026-08-16) ----

GERSHAYIM_READING = 'ב"ד'  # beit din - the gershayim IS a literal ASCII "
# Deliberately entity-forming. A bare `&` or `<tag>` round-trips through an
# unescaped interpolation by accident (`& ` is not a valid entity reference;
# `<` is inert inside a textarea's RCDATA), so neither discriminates. `&amp;`
# and a literal `<b>` in an innerHTML context do.
ADVERSARIAL_NOTE = 'R &amp; J <b>see p. 4</b> &lt;end&gt;'


def test_a_recorded_custom_reading_containing_gershayim_survives_a_panel_reopen(
        server, page):
    """The candidate panel used to render its custom-reading input as
    `value="${activeText}"`, unescaped.

    This corpus's abbreviation mark is the literal ASCII `"` (part1.json's
    clean_text holds 6,448 of them), so a recorded custom reading like `ב"ד`
    produced `value="ב"ד"` - which a browser parses as value="ב" plus a junk
    attribute. The reviewer reopened their own decision and saw `ב`, and
    saving again would have recorded `ב`: a human's exact Hebrew reading
    silently truncated at the most common punctuation mark in the book, in the
    tool whose whole purpose is exact fidelity (Success Criterion #1).

    Six candidate_choice decisions whose chosen_text contains a gershayim are
    already in review_decisions.jsonl, so this is the ordinary case, not an
    exotic one. The manual-correction panel had escaped its own value= for
    exactly this reason since it was written; the candidate panel never did.
    """
    klal_id, word_index = _find_candidate_position()
    assert klal_id is not None, "no live candidate to record a decision against"

    status, _ = _post_json(server, "/api/decisions/candidate", {
        "klal_id": klal_id, "word_index": word_index,
        "chosen_source": "custom", "chosen_text": GERSHAYIM_READING,
        "note": ADVERSARIAL_NOTE,
    })
    assert status == 201

    _open_dashboard(page, server, klal_id=klal_id)
    page.evaluate(
        """async ([kid, widx]) => {
            const k = await fetch('/api/klal/' + kid).then(r => r.json());
            openCandidatePanel(kid, k.corrections.find(c => c.word_index === widx));
        }""",
        [klal_id, word_index],
    )
    page.wait_for_selector("#custom-text-input", timeout=5000)

    assert page.input_value("#custom-text-input") == GERSHAYIM_READING, (
        "the recorded custom reading came back truncated - the gershayim closed the "
        "value attribute early (escapeAttr regression in openCandidatePanel)"
    )
    # A note carrying HTML-special characters must round-trip verbatim too.
    # ADVERSARIAL_NOTE is chosen to actually DISCRIMINATE: a textarea's
    # contents are RCDATA, so a bare `&` or a `<tag>` survives unescaped
    # interpolation by luck and proves nothing. `&amp;` does not - the parser
    # decodes it to `&` on the way in, so an unescaped write loses a
    # character the reviewer typed. Found by mutation testing: a first draft
    # of this assertion used 'R & J <see p. 4>' and stayed GREEN when
    # escapeHtml was reduced to a pass-through.
    assert page.input_value("#decision-note") == ADVERSARIAL_NOTE
    assert page.test_errors == []


def test_a_note_with_html_special_characters_renders_verbatim_in_the_history_panel(
        server, page):
    """The decision-history list interpolates chosen_text and note straight
    into innerHTML - a real HTML parsing context, unlike a textarea's RCDATA.
    An unescaped note containing markup is not merely mangled, it is
    INTERPRETED: `<b>` becomes bold formatting and the tag text disappears
    from what the reviewer reads back."""
    klal_id, word_index = _find_candidate_position()
    assert klal_id is not None, "no live candidate to record a decision against"
    status, _ = _post_json(server, "/api/decisions/candidate", {
        "klal_id": klal_id, "word_index": word_index,
        "chosen_source": "custom", "chosen_text": GERSHAYIM_READING,
        "note": ADVERSARIAL_NOTE,
    })
    assert status == 201

    _open_dashboard(page, server, klal_id=klal_id)
    page.evaluate(
        """async ([kid, widx]) => {
            const k = await fetch('/api/klal/' + kid).then(r => r.json());
            openCandidatePanel(kid, k.corrections.find(c => c.word_index === widx));
        }""",
        [klal_id, word_index],
    )
    page.wait_for_selector("#history-toggle", timeout=5000)
    page.click("#history-toggle")
    page.wait_for_selector("#history-list .h-note", timeout=5000)

    notes = page.locator("#history-list .h-note")
    rendered = [notes.nth(i).inner_text() for i in range(notes.count())]
    assert ADVERSARIAL_NOTE in rendered, (
        f"the note was altered on its way through innerHTML: {rendered!r}"
    )
    assert page.locator("#history-list .h-note b").count() == 0, (
        "the note's literal <b> was parsed as markup instead of shown as text"
    )
    assert page.test_errors == []


def test_corpus_text_with_html_special_characters_renders_verbatim(server, page):
    """Part 1's clean_text still contains a bare `&` token. The candidate/manual
    context panes interpolate clean_text straight into innerHTML, so they must
    escape it: `& ` survives today only because it is not a valid entity
    reference, which is luck, not a property anyone chose.

    The POSITION is looked up, not hardcoded. This was pinned to klal 69 w338
    until 2026-08-31, when that `&` was correctly repaired to `אל` - the test then
    failed because the corpus had improved, which is the wrong thing for a test to
    notice. Two of the three are now gone; when the last one (klal 77 w11) is
    repaired this should seed a word with an `&` through the API rather than be
    deleted, since the escaping behaviour still needs a guard."""
    found = _find_word_containing("&")
    if found is None:
        pytest.skip("no bare `&` left in Part 1 - seed one through the API instead of skipping")
    klal_id, word_index = found
    _open_dashboard(page, server, klal_id=klal_id)
    page.evaluate(
        "([kid, widx]) => openManualCorrectionPanel(kid, widx, '&', null)",
        [klal_id, word_index],
    )
    page.wait_for_selector("#manual-panel-body .panel-word-context", timeout=5000)

    context_text = page.inner_text("#manual-panel-body .panel-word-context")
    assert "[&]" in context_text, (
        f"the klal-{klal_id} ampersand did not render verbatim in the context pane: {context_text!r}"
    )
    assert "&amp;" not in context_text, "double-escaped"
    assert page.test_errors == []


def test_focus_box_transparent_and_zoom_preserves_focus(server, page):
    """Verifies that selecting a word sets a focused highlight box with transparent
    background (for human eyeball review), and that zooming in does not clear the focus."""
    klal_id, word_index = _find_candidate_position()
    assert klal_id is not None, "no live candidate to focus on"
    _open_dashboard(page, server, klal_id)
    # Let the nav jump's SMOOTH scroll finish before focusing a word. It runs
    # ~1.5s from a long jump, and suppressObserverScroll only masks the scroll
    # observer for 700ms - so a scroll still in flight fires
    # updateActiveFromScroll, which calls setActiveKlal -> showPage(page, klal,
    # null) and wipes scanFocusCorr. Instrumented 2026-08-31: zooming here
    # produced two showPage(..., null) calls for a DIFFERENT klal than the
    # focused word's. Not what this test is about - see PROJECT-STATUS 0E for the
    # window itself.
    _settle(page, "Math.round(document.getElementById('text-scroll').scrollTop)")

    page.evaluate("""async ([kid, widx]) => {
        const k = await fetch('/api/klal/' + kid).then(r => r.json());
        const corr = k.corrections.find(c => c.word_index === widx);
        showPage(corr.page || k.page, kid, corr);
    }""", [klal_id, word_index])
    page.wait_for_selector(".hl-box.focused", timeout=5000)

    # 1. Verify interior transparency
    bg = page.evaluate("getComputedStyle(document.querySelector('.hl-box.focused')).backgroundColor")
    assert bg in ("rgba(0, 0, 0, 0)", "transparent"), f"Focused box must be transparent, got: {bg}"

    # 2. Zoom in and verify focus remains intact
    page.click("#zoom-in")
    page.wait_for_timeout(300)
    assert page.locator(".hl-box.focused").count() == 1, "Zooming in must preserve word focus"
    assert page.test_errors == []


def test_part_selector_switches_corpus_parts(server, page):
    """Verifies that selecting Part 2 and Part 3 in #part-select updates the nav list
    and fetches klalim from the selected part."""
    _open_dashboard(page, server)

    # 1. Switch to Part 2
    page.select_option("#part-select", "2")
    page.wait_for_timeout(500)
    page.wait_for_selector("#nav-223", timeout=5000)
    assert page.locator("#nav-223").count() == 1, "Part 2 must load Klal 223"

    # 2. Switch to Part 3
    page.select_option("#part-select", "3")
    page.wait_for_timeout(500)
    page.wait_for_selector("#nav-445", timeout=5000)
    assert page.locator("#nav-445").count() == 1, "Part 3 must load Klal 445"

    # 3. Switch back to Part 1
    page.select_option("#part-select", "1")
    page.wait_for_timeout(500)
    page.wait_for_selector("#nav-1", timeout=5000)
    assert page.locator("#nav-1").count() == 1, "Part 1 must reload Klal 1"
    assert page.test_errors == []



def test_a_backticked_replacement_in_a_note_is_offered(server, page):
    """REGRESSION 2026-08-30, reviewer: "69 w338 ... did not surface the
    recommended word from the note".

    validate_part1_corpus_integrity.py writes its proposals with BACKTICKS -
    ``'&' w338 -> REPLACE with `אל` `` - so extractSuggestedWord's anchored
    pattern captured the literal word "REPLACE", which carries no Hebrew letter
    and was correctly dropped by suggestionIsPlausible. Nothing else matched,
    and the panel offered no reading at all for a flag that names one plainly.
    Three of the four affected flags are the `&` -> `אל` ligature repairs.

    Uses the real note verbatim, and asserts the panel offers `אל` and not the
    verb."""
    real_note = (
        "'&' w338 -> REPLACE with `אל` - it is the alef-lamed ligature ﭏ | "
        "NON-HEBREW CHARACTER in Part 1 text, one of 7 reported by "
        "validate_part1_corpus_integrity.py check 2b and never resolved."
    )
    # w222, not 224: the `server` fixture's ledger is module-scoped and shared,
    # and test_a_suggested_replacement_is_a_word_not_a_number_from_the_note seeds
    # its own flag at 224. Two flags at one index means the later-appended note
    # wins in _word_level_ai_flags, so the pair passed alone and failed together.
    # Click by data-word-index too - `.state-ai-flag.first` is whichever flag the
    # DOM happens to order first once more than one klal-1 flag exists.
    body = json.dumps({"klal_id": 1, "word_index": 222, "needs_revisit": True,
                       "note": real_note}).encode("utf-8")
    req = urllib.request.Request(server + "/api/decisions/klal_flag", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        assert resp.status in (200, 201)

    _open_dashboard(page, server, 1)
    page.locator('#klal-block-1 [data-word-index="222"]').first.click()
    page.wait_for_selector("#manual-panel.open", timeout=5000)

    panel = page.locator("#manual-panel").inner_text()
    # The offered reading, not merely the letters appearing somewhere on screen -
    # the klal text itself is in this panel, so a bare `in panel` would pass on
    # any note. Assert the "Use ..." control, which is what a click applies.
    assert 'Use "אל"' in panel, f"the note names `אל` plainly; panel was:\n{panel}"


def test_a_backticked_context_word_is_not_mistaken_for_a_proposal(server, page):
    """The other half of the same fix. Most backticks in these notes hold
    CONTEXT, not a proposal - klal 74 w416's `אמר` is the catchword the note
    wants DELETED, not a replacement for it. A bare "first backticked token"
    rule would offer `אמר` as the new reading of `אמר`, so the backtick is only
    honoured behind the verb `replace ... with`."""
    real_note = (
        "'אמר' w416 -> PAGE-SEAM FURNITURE: page 35's catchword `אמר` and a "
        "duplicated `רבא אמר` are both present; the catchword should be deleted."
    )
    body = json.dumps({"klal_id": 1, "word_index": 226, "needs_revisit": True,
                       "note": real_note}).encode("utf-8")
    req = urllib.request.Request(server + "/api/decisions/klal_flag", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        assert resp.status in (200, 201)

    _open_dashboard(page, server, 1)
    page.locator('#klal-block-1 [data-word-index="226"]').first.click()
    page.wait_for_selector("#manual-panel.open", timeout=5000)

    panel = page.locator("#manual-panel").inner_text()
    assert "Use `אמר`" not in panel and "Use אמר" not in panel, (
        f"a context word was offered as a replacement; panel was:\n{panel}")


def _settle(page, expr, timeout_ms=9000):
    """Block until a moving element stops moving, then return where it stopped.

    `expr` is JS returning the number to watch (a left edge, a block's top).

    Two consecutive equal readings are NOT enough, and getting that wrong cost
    two rounds here: a CSS transition and a smooth scroll both have a beat before
    anything moves, so the first two samples match the START position and the
    wait returns instantly - reading the panel off-screen right, or the klal
    block 34,000px away, and failing for a reason that has nothing to do with the
    bug. Require the value to have CHANGED at least once, then to hold still
    across three polls."""
    import time
    deadline = time.time() + timeout_ms / 1000
    first = last = page.evaluate(expr)
    moved, stable = False, 0
    while time.time() < deadline:
        page.wait_for_timeout(120)
        now = page.evaluate(expr)
        if now != last:
            moved, stable = True, 0
        else:
            stable += 1
        last = now
        if moved and stable >= 3:
            return now
        if not moved and stable >= 12:      # it was already where it belongs
            return now
    raise AssertionError(f"never settled: started {first}, last read {last}")


def test_the_klal_list_is_clickable_while_a_decision_panel_is_open(server, page):
    """REGRESSION 2026-08-31, reviewer: "clicking on klal 12 in the correction
    pane does not jump the text pane to that klal".

    It was never about klal 12. `.side-panel` was `position: fixed; right: 0;
    width: 420px` and the layout is RTL, so the rightmost column - the 380px nav
    pane listing every klal - sat entirely underneath it: 380px of overlap, 100%
    of the pane. While any decision panel was open, a click meant for a klal
    landed on the panel and nothing happened. From a cold page load it worked,
    which is why it read as klal-specific.

    Asserts the geometry AND the behaviour: zero overlap is what makes the click
    reach the list, and the click is what the reviewer actually does."""
    kid = _find_klal_with_a_flag_word()
    assert kid is not None, "no klal currently carries a candidate to open a panel with"
    _open_dashboard(page, server, kid)
    page.locator(f"#klal-block-{kid} .flag-word").first.click()
    page.wait_for_selector(".side-panel.open", timeout=5000)
    # .open only adds the class; the panel is still sliding for another 180ms
    # (transition: transform .18s). Measured mid-flight it reads as off-screen
    # right, which looks like a pass for the wrong reason - wait for the geometry
    # to STOP changing rather than for it to reach any particular value, so the
    # settled position is what gets asserted.
    _settle(page, "Math.round(document.querySelector('.side-panel.open').getBoundingClientRect().left)")

    overlap = page.evaluate("""() => {
        const nav = document.getElementById('nav-pane').getBoundingClientRect();
        const panel = document.querySelector('.side-panel.open').getBoundingClientRect();
        return Math.max(0, Math.min(nav.right, panel.right) - Math.max(nav.left, panel.left));
    }""")
    assert overlap == 0, (
        f"the open panel covers {overlap:.0f}px of the nav pane, so a click meant for a klal "
        f"lands on the panel and the list is unusable while any panel is open")

    page.click("#nav-12", timeout=5000)
    assert page.evaluate("document.querySelector('.nav-item.active')?.id") == "nav-12"
    # The jump is a SMOOTH scroll and takes ~1.5s to settle from a long distance;
    # sampled early it reads as thousands of pixels off, which would fail for the
    # wrong reason. Wait for the position to stop changing, then assert where it
    # landed - the same shape as _settle_panel above.
    top = _settle(page, "Math.round(document.getElementById('klal-block-12').getBoundingClientRect().top)")
    assert abs(top) < 120, f"the text pane did not jump to klal 12 (block settled at top {top}px)"


def test_a_closed_panel_does_not_park_on_top_of_the_klal_list(server, page):
    """The other half of docking the panel beside the nav pane rather than over
    it: `transform: translateX(100%)` hid a panel anchored at `right: 0`, but a
    panel anchored at `right: var(--nav-w)` needs to travel its own width PLUS
    that offset, or closing it leaves it parked over the list it was moved off."""
    kid = _find_klal_with_a_flag_word()
    assert kid is not None, "no klal currently carries a candidate to open a panel with"
    _open_dashboard(page, server, kid)
    page.locator(f"#klal-block-{kid} .flag-word").first.click()
    page.wait_for_selector(".side-panel.open", timeout=5000)
    page.keyboard.press("Escape")
    _settle(page, "Math.round(document.getElementById('disputed-panel').getBoundingClientRect().left)")

    overlap = page.evaluate("""() => {
        const nav = document.getElementById('nav-pane').getBoundingClientRect();
        const panel = document.getElementById('disputed-panel').getBoundingClientRect();
        return Math.max(0, Math.min(nav.right, panel.right) - Math.max(nav.left, panel.left));
    }""")
    assert overlap == 0, f"a closed panel still overlaps the nav pane by {overlap}px"

# ---------------------------------------------------------------------------
# 2026-08-31 reviewer reports. All four look the subject up rather than pinning
# a corpus coordinate where they can (item 0F): the klal is chosen for having a
# multi-page-safe flagged word, and the word index is read off the DOM.
# ---------------------------------------------------------------------------

def test_a_deep_link_scrolls_the_index_pane_fully_onto_the_klal(server, page):
    """REGRESSION 2026-08-31, reviewer: "the index pane does not scroll all the
    way to the actual klal".

    setActiveKlal scrolled the nav with block:'nearest', which moves the MINIMUM
    distance that makes the row visible. Right for the continuous scroll reaction,
    wrong for a jump: measured on /klal/210/word/133 the row landed at bottom
    1001px against a pane bottom of 1000px - one pixel past the fold, so the
    destination the link exists to reach was the one row you could not see.
    Asserts full visibility, not a scrollTop, because a pixel target would only
    be asserting the viewport height."""
    page.goto(server + "/klal/210/word/133", wait_until="domcontentloaded", timeout=15000)
    page.wait_for_selector(".nav-item", timeout=15000)
    page.wait_for_timeout(2500)
    visible = page.evaluate("""() => {
      const nav = document.getElementById('nav-210');
      if (!nav) return null;
      let p = nav.parentElement;
      while (p && p !== document.body) {
        const st = getComputedStyle(p);
        if (/(auto|scroll)/.test(st.overflowY) && p.scrollHeight > p.clientHeight) break;
        p = p.parentElement;
      }
      if (!p || p === document.body) return null;
      const n = nav.getBoundingClientRect(), s = p.getBoundingClientRect();
      return n.top >= s.top && n.bottom <= s.bottom;
    }""")
    assert visible is True, "the deep link's klal is not fully visible in the index pane"
    assert page.test_errors == []


def test_the_routed_word_ring_outlives_the_reader(server, page):
    """REGRESSION 2026-08-31, reviewer: "if i move my cursor over the text the
    highlight disappears".

    It was not the cursor. The ring carried a hard setTimeout(..., 4000) and
    simply expired - which lands about when a reviewer has finished reading the
    line and started moving the mouse, so the two read as cause and effect. This
    moves the pointer AND waits past the old expiry, because asserting only one
    of the two would still pass against the bug."""
    page.goto(server + "/klal/210/word/133", wait_until="domcontentloaded", timeout=15000)
    page.wait_for_selector(".routed-word", timeout=15000)
    page.mouse.move(700, 400)
    page.wait_for_timeout(400)
    page.mouse.move(650, 470)
    page.wait_for_timeout(5000)          # past the 4000ms the ring used to die at
    ringed = page.eval_on_selector_all(".routed-word",
                                       "els => els.map(e => e.dataset.wordIndex)")
    assert ringed == ["133"], f"expected the ring to still be on w133, got {ringed}"
    assert page.test_errors == []


def test_clicking_a_scan_box_reveals_that_word_in_the_text(server, page):
    """REGRESSION 2026-08-31, reviewer: "clicking on the highlighted word in the
    scan does not highlight the same word in the text".

    text->scan had a single funnel (focusWordOnScan); scan->text had nothing, so
    a scan click moved the scan and opened a panel and the middle pane was never
    told. Reads the box's own klal/word off the DOM rather than pinning one."""
    page.goto(server + "/klal/210/word/133", wait_until="domcontentloaded", timeout=15000)
    page.wait_for_selector("#hl-container .hl-box", timeout=15000)
    page.wait_for_timeout(1500)
    page.evaluate("document.querySelectorAll('.routed-word').forEach(e => e.classList.remove('routed-word'))")
    target = page.evaluate("""() => {
      const boxes = [...document.querySelectorAll('#hl-container .hl-box')];
      const b = boxes.find(x => x.className.includes('focused')) || boxes[0];
      if (!b) return null;
      b.click();
      return true;
    }""")
    assert target, "no highlighted box on the scan page to click"
    page.wait_for_selector(".routed-word", timeout=8000)
    got = page.eval_on_selector_all(".routed-word", "els => els.length")
    assert got == 1, f"expected exactly one word ringed in the text pane, got {got}"
    assert page.test_errors == []


def test_the_scan_header_carries_the_reference_in_both_scripts(server, page):
    """ADDED 2026-08-31 (reviewer): the scan header should read the page and klal,
    then whitespace, then the same reference in Hebrew.

    The Hebrew numerals come from /api/numerals rather than a JS gematria table,
    so this also pins that the fetch actually reached the running code - the first
    attempt added it to switchPart() instead of init(), and the header quietly
    rendered `דף 73` because hebNum() falls back to the digits (Lesson 34).

    UPDATED 2026-09-01. This asserted a LITERAL "Page 73", and klal 210 word 133
    is on page 74 - `word_pages["133"]` says so, and the klal splits 61 words on
    73 against 69 on 74. 73 was the klal's START page, which is what the deep
    link wrongly showed until highlightRoutedWord()'s dead word_pages branch was
    fixed. So this test was pinning the defect and went red on the repair, which
    is Lesson 36 in its exact shape. The page now comes from the server, the way
    the two new deep-link tests take theirs; the numerals, which are what this
    test is actually about, keep their literals because 210 -> רי is arithmetic
    and does not move with the corpus.
    """
    klal = _get_json(server, "/api/klal/210")
    want_page = (klal.get("word_pages") or {}).get("133") or klal.get("page")
    page.goto(server + "/klal/210/word/133", wait_until="domcontentloaded", timeout=15000)
    page.wait_for_selector(".nav-item", timeout=15000)
    page.wait_for_timeout(2500)
    en = page.eval_on_selector("#page-indicator", "el => el.textContent")
    he = page.eval_on_selector("#klal-indicator", "el => el.textContent")
    assert f"Page {want_page}" in en and "Klal 210" in en, f"{en!r}, expected page {want_page}"
    # Both numerals, the ones the BOOK would use rather than the digits. The PAGE
    # numeral comes from /api/numerals keyed on the page the server actually
    # resolved, so it follows the fix above instead of re-pinning a literal; רי
    # (210) stays literal because the klal id does not move.
    want_he_page = _get_json(server, "/api/numerals")[str(want_page)]
    assert want_he_page in he, f"Hebrew half did not render the page numeral: {he!r}"
    assert "רי" in he, f"Hebrew half did not render the klal numeral: {he!r}"
    assert str(want_page) not in he and "210" not in he, f"Hebrew half still shows digits: {he!r}"
    assert page.test_errors == []

def test_the_index_row_carries_both_scripts_and_never_squeezes_out_its_badges(server, page):
    """ADDED 2026-08-31 (reviewer): the index pane should show the English number
    AND the Hebrew on every line, and a long title must be ellipsised rather than
    pushing the dispute counts and the flag off the row.

    Asserts the SECOND half by geometry, not by eye: it finds a row that actually
    has both badges and checks each badge still has non-zero width and sits inside
    the row's own box. A row is chosen by looking for the badges rather than by
    pinning a klal id, so settling that klal's queue cannot break this (item 0F)."""
    _open_dashboard(page, server, klal_id=1)
    page.wait_for_selector(".nav-item .nheb", timeout=15000)
    got = page.evaluate("""() => {
      const heb = [...document.querySelectorAll('.nav-item')].slice(0, 5)
        .map(r => r.querySelector('.nheb') && r.querySelector('.nheb').textContent);
      // The row with the LONGEST title that carries any fixed furniture at all -
      // that is the row where a squeeze would show first. Not pinned to a klal,
      // and not requiring BOTH badges: the test server's ledger is a temp copy
      // and may carry no decided ones.
      const cands = [...document.querySelectorAll('.nav-item')]
        .filter(r => r.querySelector('.ncount, .nflag'));
      const row = cands.sort((a, b) =>
        (b.querySelector('.ntitle')?.textContent || '').length -
        (a.querySelector('.ntitle')?.textContent || '').length)[0];
      if (!row) return {heb, badges: null};
      const rr = row.getBoundingClientRect();
      const badges = [...row.querySelectorAll('.ncount, .nflag')].map(b => {
        const br = b.getBoundingClientRect();
        return {w: br.width, inside: br.right <= rr.right + 0.5 && br.left >= rr.left - 0.5};
      });
      const t = row.querySelector('.ntitle');
      return {heb, badges, titleClipped: t ? t.scrollWidth >= t.clientWidth : null};
    }""")
    assert got["heb"][:5] == ["א", "ב", "ג", "ד", "ה"], got["heb"]
    assert got["badges"], "no index row carries a badge or flag to check"
    for b in got["badges"]:
        assert b["w"] > 0 and b["inside"], f"a badge is squeezed out of the row: {got['badges']}"
    assert page.test_errors == []

def test_the_heading_is_styled_in_place_in_the_text_not_repeated_above_it(server, page):
    """ADDED 2026-08-31 (reviewer): "i didn't want the title above the text. i want
    the text itself to have bold for counter and title in the diff font - right
    there in the text."

    The book does not print a title above a klal - the klal OPENS with its
    heading, set in larger type - so the heading is styled as a PREFIX OF THE BODY
    and must not also appear as a separate line. Asserts all four properties that
    makes: the heading run exists in the body, the marker is bold, the heading is
    in a different face from the body around it, and the index row uses that SAME
    face so the two panes agree.

    Compares RESOLVED font families rather than literal names, so re-pointing
    --font-title for a work with a different layout keeps this green - which is
    the point of having the token. Uses klal 36, whose heading is a single word,
    and reads the expected length from the API rather than hardcoding it."""
    _open_dashboard(page, server, klal_id=36)
    page.wait_for_selector("#klal-block-36 .klal-title-word", timeout=15000)
    expected = page.evaluate("() => fetch('/api/klal/36').then(r => r.json()).then(d => d.title_word_count)")
    got = page.evaluate("""() => {
      const fam = el => el ? getComputedStyle(el).fontFamily.split(',')[0].replace(/["']/g, '').trim() : null;
      const blk = document.getElementById('klal-block-36');
      const marker = blk.querySelector('.klal-marker-word');
      const title = blk.querySelector('.klal-title-word');
      const plain = [...blk.querySelectorAll('[data-word-index]')]
        .find(e => parseInt(e.dataset.wordIndex, 10) > 6);
      return {
        titleRun: blk.querySelectorAll('.klal-title-word').length,
        markerWeight: parseInt(getComputedStyle(marker).fontWeight, 10),
        titleFont: fam(title), bodyFont: fam(plain), navFont: fam(document.querySelector('.nav-item .klal-title')),
        headRepeatsTitle: !!blk.querySelector('.klal-head .klal-title'),
      };
    }""")
    assert not got["headRepeatsTitle"], "the title is still repeated above the text"
    assert got["titleRun"] == expected, f"heading run is {got['titleRun']}, API says {expected}"
    assert got["markerWeight"] >= 700, got
    assert got["titleFont"] != got["bodyFont"], f"heading is set in the body face: {got}"
    assert got["titleFont"] == got["navFont"], f"index and text disagree on the title face: {got}"
    assert page.test_errors == []


def test_the_scan_header_actually_separates_its_two_scripts(server, page):
    """REGRESSION 2026-08-31, reviewer: "i said to add whitespace to sep. eng from
    heb above the scan page. you left one space!!"

    The rule said `margin-inline-start`, which resolves against the ELEMENT's own
    direction - and that span is `direction: rtl`, so it became margin-right and
    put the gap on the far side. What survived was the single literal space in
    index.html: a measured 3px. Asserts the rendered GAP, because the property
    was present and correct-looking the whole time and only the geometry showed
    it was landing on the wrong edge.

    UPDATED 2026-09-01. This measured `hebrew.left - english.right`, which
    assumes the English half comes FIRST - and the reviewer then specified the
    opposite order for every pane ("heb title w.s. heb klal page w.s eng klal
    page w.s. eng title"), so a correct layout scored -173. The requirement is
    unchanged and still worth pinning: the two scripts must not run together.
    Only the measurement is now order-independent, so re-ordering the bar again
    cannot fail it for the wrong reason."""
    _open_dashboard(page, server, klal_id=69)
    page.wait_for_timeout(1200)
    gap = page.evaluate("""() => {
      const a = document.getElementById('page-indicator').getBoundingClientRect();
      const b = document.getElementById('klal-indicator').getBoundingClientRect();
      // The clear space between them, whichever sits on the left.
      return Math.max(a.left, b.left) - Math.min(a.right, b.right);
    }""")
    assert gap >= 6, f"english and hebrew halves are only {gap:.0f}px apart"
    assert page.test_errors == []

def test_a_nav_jump_lands_on_the_klal_it_was_asked_for(server, page):
    """REGRESSION 2026-08-31, reviewer: "clicking on 105 in the index moves the
    text pane but not the scan" - item 0E, which had been recorded as open.

    The symptom was ONE KLAL OFF rather than a dead pane: the scan did go to
    page 44, but the observer set the active klal to 104 on the way past, so the
    header read "Klal 104" and the scan outlined 104's region while the text pane
    sat on 105. jumpTo() released the scroll observer after a fixed 700ms and a
    long smooth scroll takes ~1500ms to settle.

    Covers the LONGEST jumps deliberately - the last klalim are where the scroll
    clamps at the bottom and cannot put the destination at the top of the pane, so
    the observer's "last block above the reading line" answer is structurally
    wrong there. Asserts the active klal AND the scan page, because the bug moved
    one without the other."""
    _open_dashboard(page, server, klal_id=1)
    for target in (105, 219, 2):
        page.eval_on_selector(f"#nav-{target}", "el => el.click()")
        # Wait for the SCROLL to settle, observed from the DOM. `suppressObserver
        # Scroll` is a script-scoped `let`, so it is not a window property and
        # cannot be polled from here - checking it was the first attempt and it
        # timed out on a binding that does not exist.
        page.wait_for_function(
            """() => {
              const el = document.getElementById('text-scroll');
              const now = Math.round(el.scrollTop);
              const settled = window.__lastTop === now ? (window.__stable = (window.__stable || 0) + 1)
                                                       : (window.__stable = 0);
              window.__lastTop = now;
              return settled >= 3;
            }""", timeout=10000)
        page.wait_for_timeout(500)   # let the post-settle re-assert run
        page.evaluate("() => { window.__stable = 0; window.__lastTop = null; }")
        # Both read from the DOM. `currentPage` is a script-scoped `let` like
        # suppressObserverScroll above, so `window.currentPage` is undefined - the
        # rendered scan is the honest place to ask which page is actually shown.
        got = page.evaluate("""() => {
            const m = (document.getElementById('page-img').getAttribute('src') || '')
                        .match(/page_(\\d+)\\.png/);
            return {
              active: document.querySelector('.nav-item.active')?.dataset?.klalId,
              page: m ? parseInt(m[1], 10) : null,
            };
        }""")
        want_page = page.evaluate(
            f"() => fetch('/api/klal/{target}').then(r => r.json()).then(d => d.page)")
        assert got["active"] == str(target), (
            f"jumped to klal {target} but the index made klal {got['active']} active")
        assert got["page"] == want_page, (
            f"jumped to klal {target}: scan shows page {got['page']}, expected {want_page}")
    assert page.test_errors == []



# --- the legend as a control, and copy-on-click (2026-09-01) ----------------
# Both features were asked for in one message ("clicking on a word should push
# the url for that word into the clipboard... clicking on a flag count at the
# bottom of the index panel should pop up a list of those flags as clickable
# links, hovering for a while should pop up a copy to clipboard icon"), and both
# are pure UI: nothing below asserts a COUNT, only that the number shown and the
# thing behind it agree. Lesson 36 - this module boots against the shipped
# corpus, and 23 of its tests once pinned a coordinate in executable code, so
# seven broke at once when the text was REPAIRED.


def _legend_rows(page):
    """[(bucket, label, count)] for every clickable legend row."""
    return page.evaluate("""() => [...document.querySelectorAll('#legend .legend-clickable')]
        .map(r => ({
          bucket: r.dataset.bucket,
          label: r.dataset.label,
          count: parseInt(r.querySelector('.legend-count').textContent, 10),
        }))""")


def test_a_legend_count_opens_the_list_of_exactly_the_words_it_counts(server, page):
    """The property the whole arrangement exists for.

    /api/word-states is built in the same pass as /api/klalim's counts precisely
    so a list can never be a different length from the number that opened it.
    Every regression this file already carries in that family - nav 1,201 vs
    1,061 rendered, klal 88's "-1", klal 73's missing badge - was two encodings
    of one rule disagreeing, and a list is a third surface for the same rule.
    """
    _open_dashboard(page, server)
    rows = _legend_rows(page)
    assert rows, "the legend rendered no clickable rows at all"
    # The four state rows are always there. The `recorded` row appears only once
    # a ruling exists, so it is optional HERE - this test ran clean in isolation
    # and failed in the full suite, where earlier tests have recorded decisions
    # and the fifth row shows up. An equality on this set is a test that depends
    # on which other tests ran first.
    buckets = {r["bucket"] for r in rows}
    assert {"machine_disputed", "machine_resolved", "decided", "ai_flag"} <= buckets, buckets
    assert buckets <= {"machine_disputed", "machine_resolved", "decided", "ai_flag", "recorded"}, buckets

    for row in rows:
        page.keyboard.press("Escape")
        page.eval_on_selector(
            f"#legend .legend-clickable[data-bucket='{row['bucket']}']", "el => el.click()")
        page.wait_for_selector("#flag-list-panel.open", timeout=5000)
        page.wait_for_function(
            "() => !document.querySelector('#flag-list-panel-body p')?.textContent.includes('Loading')",
            timeout=10000)
        listed = page.locator("#flag-list-panel .flag-list-item").count()
        assert listed == row["count"], (
            f"legend row '{row['label']}' says {row['count']} but its list holds {listed}")
        if row["count"] == 0:
            assert page.locator("#flag-list-panel .flag-list-empty").count() == 1, (
                "a zero count must SAY there are none - an empty panel body reads as a broken list")
    assert page.test_errors == []


def test_a_row_in_the_word_list_navigates_to_its_word(server, page):
    """A list of links whose links do nothing is Lesson 29's dead field with a
    cursor on it. Asserts the text pane actually lands on the word - the ring
    class revealWordInText() puts there - not merely that the hash changed."""
    _open_dashboard(page, server)
    page.eval_on_selector("#legend .legend-clickable[data-bucket='machine_disputed']", "el => el.click()")
    page.wait_for_selector("#flag-list-panel .flag-list-item", timeout=10000)
    target = page.evaluate("""() => {
        const a = document.querySelector('#flag-list-panel .flag-list-item');
        return { klal: a.dataset.klal, word: a.dataset.word };
    }""")
    page.eval_on_selector("#flag-list-panel .flag-list-item", "el => el.click()")
    page.wait_for_timeout(1200)
    assert page.evaluate("() => location.hash") == f"#klal={target['klal']}&word={target['word']}"
    ringed = page.locator(
        f"#klal-block-{target['klal']} [data-word-index='{target['word']}'].routed-word")
    assert ringed.count() >= 1, (
        f"clicked the list row for klal {target['klal']} word {target['word']} and the text pane "
        "never ringed it")
    assert page.locator("#flag-list-panel.open").count() == 1, (
        "the panel must stay open - the point of the list is working down it")
    assert page.test_errors == []


def test_holding_the_pointer_on_a_list_row_reveals_its_copy_button(server, page):
    """"hovering for a while should pop up a copy to clipboard icon" - the
    reviewer asked for a DWELL, and the difference matters: 518 rows each showing
    a button the instant the pointer crosses them is a list you cannot scroll
    through and read."""
    _open_dashboard(page, server)
    page.eval_on_selector("#legend .legend-clickable[data-bucket='machine_disputed']", "el => el.click()")
    page.wait_for_selector("#flag-list-panel .flag-list-item", timeout=10000)
    row = page.locator("#flag-list-panel .flag-list-item").first
    assert not row.locator(".flag-list-copy").is_visible(), (
        "the copy button must start hidden, or the dwell buys nothing")
    row.hover()
    page.wait_for_timeout(150)          # inside FLAG_LIST_DWELL_MS (400ms)
    assert not row.locator(".flag-list-copy").is_visible(), (
        "the copy button appeared before the dwell elapsed - a pointer merely "
        "crossing the row must not reveal it")
    page.wait_for_timeout(600)          # past it
    assert row.locator(".flag-list-copy").is_visible()
    assert page.test_errors == []


def _grant_clipboard(page, server):
    page.context.grant_permissions(["clipboard-read", "clipboard-write"], origin=server)


def test_clicking_a_word_copies_its_link_and_says_so(server, page):
    """"clicking on a word should push the url for that word into the clipboard,
    with a popup message saying so."

    Asserts the CLIPBOARD, not just the toast: a confirmation that fires whether
    or not anything was copied is exactly the dead control copyText()'s own note
    records this file shipping twice.
    """
    _grant_clipboard(page, server)
    _open_dashboard(page, server, klal_id=1)
    page.evaluate("() => navigator.clipboard.writeText('nothing copied yet')")
    word = page.locator("#klal-block-1 [data-word-index]").nth(3)
    index = word.get_attribute("data-word-index")
    text = word.inner_text().strip()
    word.click()
    page.wait_for_selector("#toast", state="visible", timeout=5000)
    toast = page.locator("#toast").inner_text()
    assert "Link copied" in toast and f"#{index}" in toast, toast

    copied = page.evaluate("() => navigator.clipboard.readText()")
    assert copied.endswith(f"/klal/1/word/{index}"), (
        f"the clipboard does not hold this word's link: {copied!r}")
    # The SAME payload the hover card's own copy button produces - two copy
    # affordances yielding different text for one word would be worse than one.
    assert f"Word #{index}" in copied and text in copied, copied
    assert page.test_errors == []


def test_the_copy_on_click_toggle_turns_it_off_and_survives_a_reload(server, page):
    """"should be a flag to disable this behavior" - and a preference that
    forgets itself on reload is not a preference, in a dashboard whose own
    standing rule is to restart the server on every frontend change."""
    _grant_clipboard(page, server)
    _open_dashboard(page, server, klal_id=1)

    def open_settings():
        # MOVED into the settings tray 2026-09-01 (reviewer: "don't put click
        # word on link up there on the index pane, hide it away somewhere -
        # settings icon?"), so the switch has to be revealed before it is used.
        if page.locator("#settings-popover").is_hidden():
            page.click("#settings-btn")
            page.wait_for_timeout(200)

    def click_word():
        # Every word click also opens a decision panel, and that panel then sits
        # over the text - so a second click has to dismiss it first or Playwright
        # (correctly) reports the panel intercepting the pointer.
        page.keyboard.press("Escape")
        page.wait_for_timeout(150)
        page.locator("#klal-block-1 [data-word-index]").nth(5).click()
        page.wait_for_timeout(600)

    open_settings()
    page.uncheck("#filter-copy-link")
    page.evaluate("() => navigator.clipboard.writeText('untouched')")
    click_word()
    assert page.evaluate("() => navigator.clipboard.readText()") == "untouched", (
        "the toggle is off and the click still wrote to the clipboard")

    _open_dashboard(page, server, klal_id=1)
    open_settings()
    assert page.locator("#filter-copy-link").is_checked() is False, (
        "the off-switch reset itself on reload")
    click_word()
    assert page.evaluate("() => navigator.clipboard.readText()") == "untouched"

    page.keyboard.press("Escape")
    open_settings()
    page.check("#filter-copy-link")
    click_word()
    assert page.evaluate("() => navigator.clipboard.readText()") != "untouched", (
        "turning it back on did not restore the copy")
    assert page.test_errors == []


def _find_disputed_word():
    """(klal_id, word_index) of a live machine-disputed word.

    _find_disputed_klal() answers only the klal half, and these tests need the
    exact word. Derived from corrections_part1.json for the same reason that one
    gives: which klal and word carry an open dispute shrinks as corrections get
    applied, so a hardcoded pair is a test that fails when the corpus IMPROVES
    (Lesson 36).
    """
    with open(os.path.join(REPO, "corrections_part1.json"), encoding="utf-8") as f:
        data = json.load(f)
    for kid in sorted(data.keys(), key=int):
        for c in data[kid]:
            if c.get("flag") == "current_text_may_be_wrong" and c.get("opcode") != "delete":
                return int(kid), c["word_index"]
    raise AssertionError("no open dispute in the corpus - these tests have no subject")


def test_a_word_url_behaves_like_clicking_that_word(server, page):
    """"opening a url that specif. a word should behave like clik on a wrd"
    (reviewer, 2026-09-02). It used to only reveal and highlight, so following a
    link left you looking at the right word with no way to act on it - you had to
    click the word you had just been taken to.

    Asserts the URL and the CLICK produce the same state rather than pinning what
    that state is: five render branches attach five different handlers, and which
    panel a given word opens is not this test's business.
    """
    _grant_clipboard(page, server)
    _open_dashboard(page, server)
    klal_id, word_index = _find_disputed_word()
    page.evaluate(f"() => {{ location.hash = '#klal={klal_id}&word={word_index}'; }}")
    page.wait_for_timeout(2500)
    via_url = page.evaluate("""() => ({
        panels: [...document.querySelectorAll('.side-panel.open')].map(p => p.id),
        focused: document.querySelectorAll('#hl-container .hl-box.focused').length,
        page: (document.getElementById('page-img').getAttribute('src') || '').match(/page_(\\d+)/)[1],
    })""")
    assert via_url["panels"], "following a word URL opened no panel at all"

    page.keyboard.press("Escape")
    page.wait_for_timeout(400)
    page.eval_on_selector(f"#klal-block-{klal_id} [data-word-index='{word_index}']", "el => el.click()")
    page.wait_for_timeout(1500)
    via_click = page.evaluate("""() => ({
        panels: [...document.querySelectorAll('.side-panel.open')].map(p => p.id),
        focused: document.querySelectorAll('#hl-container .hl-box.focused').length,
        page: (document.getElementById('page-img').getAttribute('src') || '').match(/page_(\\d+)/)[1],
    })""")
    assert via_url == via_click, f"URL gave {via_url}, click gave {via_click}"
    assert page.test_errors == []


def test_following_a_word_url_still_leaves_the_clipboard_alone(server, page):
    """The ONE thing a routed click must not do. A real click copies the word's
    URL; doing that on arrival would be pointless - the reviewer HAS the URL,
    they just opened it - and a page loaded cold from a link has no transient
    user activation, so the browser would reject the write and put a "Could not
    copy" toast on screen every time anyone followed a link."""
    _grant_clipboard(page, server)
    _open_dashboard(page, server)
    page.evaluate("() => navigator.clipboard.writeText('the link I followed')")
    klal_id, word_index = _find_disputed_word()
    page.evaluate(f"() => {{ location.hash = '#klal={klal_id}&word={word_index}'; }}")
    page.wait_for_timeout(2500)
    assert page.evaluate("() => navigator.clipboard.readText()") == "the link I followed"
    # ...and it still ROUTED, or this passes for the wrong reason.
    assert page.locator(f"#klal-block-{klal_id} [data-word-index='{word_index}']").count() == 1
    assert page.locator(".side-panel.open").count() >= 1
    assert page.test_errors == []


def test_the_scan_overlay_controls_stay_put_when_the_scan_is_scrolled(server, page):
    """REGRESSION 2026-09-02, reviewer: "what happened to my zoom controls?"

    They were children of #scan-viewer - the element that SCROLLS - and an
    absolutely-positioned child of a scroll container is positioned against the
    scrolled CONTENT, so they slid away with the page. Measured at 300% zoom
    scrolled past the top, the zoom cluster and both page arrows sat at negative
    y: entirely gone. The arrows had carried this since they were added; moving
    the zoom cluster in beside them gave it the same defect, which is how it was
    noticed. Both are now anchored to #scan-pane, which does not scroll.
    """
    _open_dashboard(page, server, klal_id=2)
    for _ in range(8):
        page.click("#zoom-in")
        page.wait_for_timeout(120)
    page.wait_for_timeout(400)
    seen = []
    for frac in (0.0, 0.5, 1.0):
        page.evaluate(f"() => {{ const v = document.getElementById('scan-viewer');"
                      f" v.scrollTop = v.scrollHeight * {frac}; }}")
        page.wait_for_timeout(300)
        seen.append(page.evaluate("""() => {
            const v = document.getElementById('scan-viewer').getBoundingClientRect();
            const at = id => {
              const r = document.getElementById(id).getBoundingClientRect();
              return { y: Math.round(r.top),
                       visible: r.bottom > v.top + 2 && r.top < v.bottom - 2 };
            };
            return { zoom: at('zoom-controls'), prev: at('page-nav-prev'), next: at('page-nav-next') };
        }"""))
    for i, s in enumerate(seen):
        for name in ("zoom", "prev", "next"):
            assert s[name]["visible"], f"at scroll position {i}, #{name} is off-screen: {s}"
    # ...and they must not MOVE either - a control that wanders is as bad as one
    # that vanishes.
    for name in ("zoom", "prev", "next"):
        ys = {s[name]["y"] for s in seen}
        assert len(ys) == 1, f"#{name} moved with the scroll: y values {sorted(ys)}"
    assert page.test_errors == []


def test_the_legend_names_recorded_rulings_beside_the_rendered_count(server, page):
    """The reviewer's actual report: "count for human decisions is 51 - not
    correct." decided_count counts words rendered GREEN, and a ruling stops
    rendering once it is settled - the rebuild drops the candidate entry, and an
    applied manual_correction fails the display drift check because the word it
    names is no longer there. 463 rulings on record showed as 51.

    Recorded is built WITHOUT that drift check, so a decision whose snapshotted
    word has moved still counts. This posts exactly such a decision and asserts
    it reaches the recorded figure and NOT the rendered one - the difference
    between the two numbers is the whole feature.
    """
    before = _get_json(server, "/api/klalim?part=1")
    row_before = next(r for r in before if r["klal_id"] == 12)

    status, _ = _post_json(server, "/api/decisions/manual", {
        "klal_id": 12, "word_index": 3, "original_word": "לא-המילה-שכאן",
        "chosen_text": "תחליף", "note": "drifted on purpose - recorded, not rendered",
    })
    assert status == 201
    row_after = next(r for r in _get_json(server, "/api/klalim?part=1") if r["klal_id"] == 12)
    assert row_after["recorded_decision_count"] == row_before["recorded_decision_count"] + 1, (
        "a ruling whose word has drifted is still a ruling - it must reach the recorded count")
    assert row_after["decided_count"] == row_before["decided_count"], (
        "it must NOT reach the rendered count - nothing on screen is green because of it")

    _open_dashboard(page, server)
    shown = int(page.locator(
        "#legend .legend-clickable[data-bucket='decided'] .legend-count").inner_text())
    recorded = int(page.locator(
        "#legend .legend-clickable[data-bucket='recorded'] .legend-count").inner_text())
    assert recorded > shown, (
        f"the legend shows {shown} still drawn and {recorded} recorded; the second number exists "
        "because the first one alone read as 'you have decided 51 words'")
    assert page.test_errors == []


def test_the_recorded_total_opens_every_ruling_with_its_status(server, page):
    """"add a function to show all previously decided words - so a sr reviewer
    can review a human's work" (2026-09-01).

    Reviewing someone's work means seeing what they decided AND whether it
    landed, and neither was reachable: a ruling stops rendering once it is
    settled, so the dashboard showed 51 of 478 and nothing about the rest. The
    recorded total is its own control opening its own list, with a status per
    row - NOT a second reading of the count beside it, which is why the click
    handler has to test it before the row it sits inside.
    """
    status, _ = _post_json(server, "/api/decisions/manual", {
        "klal_id": 8, "word_index": 2, "original_word": "לא-המילה-שכאן",
        "chosen_text": "תחליף", "note": "recorded, and it never landed",
    })
    assert status == 201
    _open_dashboard(page, server)

    page.eval_on_selector("#legend .legend-clickable[data-bucket='recorded']", "el => el.click()")
    page.wait_for_selector("#flag-list-panel .flag-list-item", timeout=10000)
    rows = page.locator("#flag-list-panel .flag-list-item").count()
    served = len(_get_json(server, "/api/word-states?part=1")["recorded"])
    assert rows == served, f"the recorded list holds {rows}, the API serves {served}"

    # It must NOT have opened the Human-Decided list - that is the defect the
    # nested control invites, and the two lists differ in length.
    rendered = int(page.locator(
        "#legend .legend-clickable[data-bucket='decided'] .legend-count").inner_text())
    assert rows != rendered or served == rendered, (
        "clicking 'of N recorded' opened the rendered-count list instead")

    # The ruling just posted names a word that is not there, so it must be
    # listed AND marked - it is exactly the case a senior reviewer is hunting.
    drifted = page.locator("#flag-list-panel .recorded-item.rec-drifted")
    assert drifted.count() >= 1, "a ruling that never landed is not marked as such"
    assert page.test_errors == []


def test_a_recorded_status_chip_filters_the_list(server, page):
    """478 rows in one undifferentiated column is not a review tool. The chips
    are the split a senior reviewer actually wants - 'which of these never
    landed' - so each must narrow the list to its own count."""
    _open_dashboard(page, server)
    page.eval_on_selector("#legend .legend-clickable[data-bucket='recorded']", "el => el.click()")
    page.wait_for_selector("#flag-list-panel .flag-list-item", timeout=10000)
    total = page.locator("#flag-list-panel .flag-list-item").count()

    chips = page.evaluate("""() => [...document.querySelectorAll('#flag-list-panel .rec-chip')]
        .map(c => ({ status: c.dataset.status, n: parseInt(c.querySelector('b').textContent, 10) }))""")
    assert len(chips) >= 2, f"expected an 'all' chip and at least one status: {chips}"
    assert chips[0]["status"] == "all" and chips[0]["n"] == total

    for chip in chips[1:]:
        page.eval_on_selector(
            f"#flag-list-panel .rec-chip[data-status='{chip['status']}']", "el => el.click()")
        page.wait_for_timeout(250)
        shown = page.locator("#flag-list-panel .flag-list-item").count()
        assert shown == chip["n"], (
            f"chip '{chip['status']}' claims {chip['n']} and the list shows {shown}")
    assert page.test_errors == []


PANE_HEADERS = ("nav-header", "text-header", "scan-header")


def test_every_pane_header_carries_the_book_title_from_the_server(server, page):
    """"on index pane header should show book title also scan pane", and then
    "maybe sacrifice a line at top to add header" for the third pane.

    Asserts against /api/corpus rather than a literal: this pipeline is meant to
    generalize past one work, and a test pinning "Yad Malachi" would make the
    second book's arrival look like a regression.
    """
    corpus = _get_json(server, "/api/corpus")
    assert corpus["title_he"] and corpus["title"], corpus
    _open_dashboard(page, server)
    # EXACTLY ONE of each, and both in the CENTRE pane. Reviewer, 2026-09-02:
    # "remove more titles from the top bar. just show one in hebrew and one in
    # eng in the center pane." The four-slot order had put the work's name at
    # both ends of all three bars - six repetitions of one fact across the top of
    # one window, on a screen whose complaint was clutter. The outer panes now
    # carry only their own reference.
    he = page.locator("[data-slot='title-he']")
    en = page.locator("[data-slot='title-en']")
    assert he.count() == 1, f"{he.count()} Hebrew titles on screen, expected 1"
    assert en.count() == 1, f"{en.count()} English titles on screen, expected 1"
    assert he.inner_text().strip() == corpus["title_he"]
    # text_content(), not inner_text(): the slot is styled `text-transform:
    # uppercase`, and inner_text() returns what is PAINTED.
    assert en.text_content().strip() == corpus["title"]
    # The edition is the thing START_HERE.md warns about conflating; it belongs
    # on hover, not on screen.
    assert corpus["edition"] in he.get_attribute("title")
    for slot in ("title-he", "title-en"):
        assert page.evaluate(
            "(sel) => document.getElementById('text-header')"
            ".contains(document.querySelector(sel))", f"[data-slot='{slot}']"
        ), f"{slot} is not in the centre pane"
    assert page.test_errors == []


def test_the_scan_page_arrows_sit_on_the_sides_the_reviewer_asked_for(server, page):
    """"on scan page - arrows should switch places" (2026-09-01). Previous moved
    to the LEFT and next to the RIGHT, and the glyphs moved with them so each
    still points away from the centre - swapping only the sides would have left
    'previous' on the left pointing right. Asserts geometry, not CSS text, since
    the property that matters is where they land on screen."""
    _open_dashboard(page, server, klal_id=2)
    box = page.evaluate("""() => {
        const p = document.getElementById('page-nav-prev').getBoundingClientRect();
        const n = document.getElementById('page-nav-next').getBoundingClientRect();
        return {
          prev: p.left, next: n.left,
          prevGlyph: document.getElementById('page-nav-prev').textContent.trim(),
          nextGlyph: document.getElementById('page-nav-next').textContent.trim(),
        };
    }""")
    assert box["prev"] < box["next"], (
        f"previous must sit left of next: prev at {box['prev']}, next at {box['next']}")
    # GLYPHS SWAPPED BACK 2026-09-01: "arrow behavior is correct but swap two
    # icons". The sides and the handlers are unchanged; the two characters trade
    # places so each arrow points INWARD, along the book's right-to-left reading
    # direction rather than the buttons' left-to-right one.
    assert box["prevGlyph"] == "›", box["prevGlyph"]
    assert box["nextGlyph"] == "‹", box["nextGlyph"]
    assert page.test_errors == []


def test_a_deep_link_lands_on_the_page_the_word_is_actually_on(server, page):
    """REGRESSION 2026-09-01, reviewer: "klal 12 w 219 clicking does not show
    that word highlighted" - reached from a list row, which is a deep link.

    highlightRoutedWord() carried a hand-rolled copy of pageForWord() whose
    word_pages branch COULD NOT FIRE: `klalById` is built from /api/klalim,
    whose payload has no `word_pages` key at all, so the test was always false
    and every deep link fell through to the klal's START page. Klal 12 word 219
    lives on page 19; the link showed page 18, where that word has no box - so
    nothing highlighted, and no error anywhere. Lesson 25.

    Swept: 18,044 words across 55 klalim sit on a page other than their klal's
    start page, so this was every one of them. Asserts against the server's own
    word_pages rather than a literal page number, and picks its cases from the
    live data - a klal that stops spanning pages must not fail this test.
    """
    spanning = []
    for row in _get_json(server, "/api/klalim?part=1"):
        if len(spanning) >= 3:
            break
        klal = _get_json(server, f"/api/klal/{row['klal_id']}")
        start, pages = klal.get("page"), klal.get("word_pages") or {}
        off = sorted((int(i) for i, p in pages.items() if p is not None and p != start))
        if off:
            spanning.append((row["klal_id"], off[len(off) // 2], pages[str(off[len(off) // 2])]))
    assert spanning, "no klal in Part 1 spans more than one page - this test has no subject"

    _open_dashboard(page, server)
    for klal_id, word_index, want_page in spanning:
        page.evaluate("() => { location.hash = '#'; }")
        page.evaluate(f"() => {{ location.hash = '#klal={klal_id}&word={word_index}'; }}")
        page.wait_for_timeout(2000)
        src = page.locator("#page-img").get_attribute("src")
        assert f"page_{want_page}.png" in src, (
            f"deep link to klal {klal_id} word {word_index} should show page {want_page}, got {src}")
        assert page.locator("#hl-container .hl-box.focused").count() == 1, (
            f"klal {klal_id} word {word_index}: right page, no highlight on the word")
    assert page.test_errors == []


def test_a_word_click_survives_the_scroll_that_follows_it(server, page):
    """Found while reproducing the klal 12 w219 report, and a distinct defect
    from the deep-link one above.

    The click set the right page, then a scroll event a few hundred ms later had
    updateActiveFromScroll() resolve a different klal and setActiveKlal() show
    THAT klal's start page - undoing the navigation, silently. manualPageLock
    guards the scan pane's prev/next arrows against exactly this and a word click
    deliberately clears it, which left the click the one deliberate navigation
    with no protection. Clicking with Playwright scrolls the element into view
    first, which is what makes this reproducible here.
    """
    klal_id, word_index, want_page = None, None, None
    for row in _get_json(server, "/api/klalim?part=1"):
        klal = _get_json(server, f"/api/klal/{row['klal_id']}")
        start, pages = klal.get("page"), klal.get("word_pages") or {}
        off = sorted((int(i) for i, p in pages.items() if p is not None and p != start))
        if off:
            klal_id, word_index = row["klal_id"], off[len(off) // 2]
            want_page = pages[str(word_index)]
            break
    assert klal_id is not None, "no klal spans a page break - nothing to assert"

    _open_dashboard(page, server, klal_id=klal_id)
    page.keyboard.press("Escape")
    page.locator(f"#klal-block-{klal_id} [data-word-index='{word_index}']").first.click()
    page.wait_for_timeout(2000)     # past the settle window the fix installs
    src = page.locator("#page-img").get_attribute("src")
    assert f"page_{want_page}.png" in src, (
        f"clicked klal {klal_id} word {word_index} (page {want_page}); the scan drifted to {src}")
    assert page.locator("#hl-container .hl-box.focused").count() == 1
    assert page.test_errors == []


def test_the_three_pane_headers_are_one_bar_in_the_same_order(server, page):
    """"text differs between two blue headers ... both headers same size and
    shape", with the scan pane's own order given as the template:

        [Hebrew title]  [Hebrew reference]  [English reference]  [English title]

    They sit side by side across the top of one window, so a difference in
    height, position or slot order reads as a mistake. The title also has to be
    READABLE, which is what its first version was not - it shipped near-white on
    the white filter block and the test that asserted only its TEXT passed the
    whole time."""
    _open_dashboard(page, server)
    geom = page.evaluate(r"""(ids) => ids.map(id => {
        const h = document.getElementById(id);
        const r = h.getBoundingClientRect();
        const cs = getComputedStyle(h);
        return {
          id,
          h: Math.round(r.height), top: Math.round(r.top),
          bg: cs.backgroundColor,
          slots: [...h.querySelectorAll('.ph-title, .ph-ref')]
                   .map(e => e.className.replace(/\s+/g, ' ').trim()),
          fg: getComputedStyle(h.querySelector('.ph-ref.ph-he')).color,
        };
    })""", list(PANE_HEADERS))

    heights = {g["h"] for g in geom}
    assert len(heights) == 1, f"the three bars are different heights: {geom}"
    assert {g["top"] for g in geom} == {0}, f"the bars do not start at the top: {geom}"
    assert len({g["bg"] for g in geom}) == 1, f"the bars are different colours: {geom}"
    # The two REFERENCE slots, Hebrew then English, are what every bar shares.
    # The titles are the centre pane's alone - see
    # test_every_pane_header_carries_the_book_title_from_the_server.
    want = ["ph-ref ph-he", "ph-ref ph-en"]
    for g in geom:
        refs = [c for c in g["slots"] if c.startswith("ph-ref")]
        assert refs == want, f"{g['id']} reference slots are {refs}, expected {want}"
        titles = [c for c in g["slots"] if c.startswith("ph-title")]
        if g["id"] == "text-header":
            assert titles == ["ph-title ph-he", "ph-title ph-en"], g["slots"]
        else:
            assert titles == [], f"{g['id']} still carries a title: {g['slots']}"
        assert g["fg"] != g["bg"], f"{g['id']}: its text is the colour of its own bar"

    # Nothing may overflow its bar. `overflow: hidden` on the header means an
    # over-wide bar shows no symptom at all - it silently eats a slot - so this
    # measures need against available rather than trusting the picture. Checked
    # at the narrowest width the layout targets as well as the default.
    for width in (1280, 1600):
        page.set_viewport_size({"width": width, "height": 1000})
        page.wait_for_timeout(300)
        over = page.evaluate("""(ids) => ids.map(id => {
            const h = document.getElementById(id);
            const kids = [...h.children];
            const need = kids.reduce((s, k) => s + k.scrollWidth, 0) + 12 * (kids.length - 1);
            return { id, over: Math.round(need - (h.clientWidth - 32)) };
        }).filter(r => r.over > 0)""", list(PANE_HEADERS))
        assert not over, f"at {width}px these headers overflow (px): {over}"
    assert page.test_errors == []


def test_the_copy_on_click_switch_is_behind_the_settings_icon(server, page):
    """"don't put click word on link up there on the index pane, hide it away
    somewhere - settings icon?" A preference set once does not belong beside the
    two filters that get toggled while reading."""
    _open_dashboard(page, server)
    assert page.locator("#nav-filter #filter-copy-link").count() == 0, (
        "the switch is still sitting in the filter block")
    assert page.locator("#settings-popover").is_hidden(), "the tray must start closed"
    page.click("#settings-btn")
    page.wait_for_timeout(250)
    assert page.locator("#filter-copy-link").is_visible()
    # A tray that closes on the click that flips the switch is a control you have
    # to reopen to confirm.
    page.click("#filter-copy-link")
    page.wait_for_timeout(200)
    assert page.locator("#settings-popover").is_visible(), "the tray closed on its own switch"
    page.click("#nav-list")
    page.wait_for_timeout(250)
    assert page.locator("#settings-popover").is_hidden(), "an outside click must put it away"
    assert page.test_errors == []


def test_the_word_list_closes_when_the_reviewer_goes_back_to_reading(server, page):
    """"pop up from index human-decided should disappear when clicked inside text
    pane or scan pane." Only THIS panel closes that way - the other five are
    OPENED by a click in those panes, so closing on the same click would shut
    them the instant they opened."""
    _open_dashboard(page, server, klal_id=2)
    for pane in ("#scan-pane", "#text-scroll"):
        page.eval_on_selector(
            "#legend .legend-clickable[data-bucket='machine_disputed']", "el => el.click()")
        page.wait_for_selector("#flag-list-panel .flag-list-item", timeout=10000)
        page.eval_on_selector(pane, "el => el.click()")
        page.wait_for_timeout(350)
        assert page.locator("#flag-list-panel.open").count() == 0, (
            f"a click in {pane} left the word list open")
        assert page.locator("#overlay-backdrop.open").count() == 0, (
            f"a click in {pane} closed the list but left the backdrop over the page")
    # A word click still opens ITS panel - closing the list must not have eaten it.
    page.locator("#klal-block-2 [data-word-index]").nth(4).click()
    page.wait_for_timeout(600)
    assert page.locator(".side-panel.open").count() == 1, (
        "clicking a word no longer opens its decision panel")
    assert page.test_errors == []


def test_the_legend_gives_each_human_decided_count_its_own_row(server, page):
    """Reviewer, 2026-09-01: "for counts at bottom one row human-decided (...)
    and the following row human-decided (total recorded)".

    Two counts hanging off one row read as one number with a footnote; they are
    two different measures. The first is what is still DRAWN in the text - a
    ruling stops being drawn once it is settled - and the second is what is on
    record. Only the first carries a colour swatch, because only the first
    describes something painted on screen.

    Records its own ruling first: the fixture's ledger starts EMPTY, so with no
    decisions there is no second row at all - and a test that passes because the
    thing it checks is absent has checked nothing (Lesson 25).
    """
    status, _ = _post_json(server, "/api/decisions/manual", {
        "klal_id": 20, "word_index": 1, "original_word": "לא-המילה-שכאן",
        "chosen_text": "תחליף", "note": "so the legend has something to count",
    })
    assert status == 201
    _open_dashboard(page, server)
    rows = page.evaluate("""() => [...document.querySelectorAll('#legend .legend-row')].map(r => ({
        bucket: r.dataset.bucket,
        label: (r.querySelector('.legend-label') || {}).textContent || '',
        count: parseInt((r.querySelector('.legend-count') || {}).textContent, 10),
        swatch: !!r.querySelector('i'),
    }))""")
    by_bucket = {r["bucket"]: r for r in rows if r["bucket"]}
    assert "decided" in by_bucket and "recorded" in by_bucket, rows

    drawn, recorded = by_bucket["decided"], by_bucket["recorded"]
    # Adjacent rows, in that order - "the FOLLOWING row".
    order = [r["bucket"] for r in rows]
    assert order.index("recorded") == order.index("decided") + 1, order
    assert "total recorded" in recorded["label"], recorded
    assert recorded["count"] >= drawn["count"], (drawn, recorded)
    # The swatch is the colour key. Nothing on screen is painted for the recorded
    # row - that is the whole reason it exists - so it must not claim a colour.
    assert drawn["swatch"] and not recorded["swatch"], (drawn, recorded)
    assert page.test_errors == []


def test_the_index_filters_share_one_line(server, page):
    """"put two flags above index pane on same line to max real estate for the
    index." Every row the filter block costs is a klal the list cannot show."""
    _open_dashboard(page, server)
    same_line = page.evaluate("""() => {
        const a = document.getElementById('filter-flagged').getBoundingClientRect();
        const b = document.getElementById('filter-high-value').getBoundingClientRect();
        return { same: Math.abs(a.top - b.top) < 2, aTop: Math.round(a.top), bTop: Math.round(b.top) };
    }""")
    assert same_line["same"], f"the two filters are on different lines: {same_line}"
    assert page.test_errors == []


def test_the_scan_controls_are_not_inside_the_header(server, page):
    """The scan bar could not fit four text slots AND a control cluster - it
    overflowed by 58px at a 1280px window, invisibly, because the header clips.
    The zoom controls moved onto the scan itself, beside the page arrows that
    were already there, which is also what makes the three bars the same object
    rather than two bars and one toolbar."""
    _open_dashboard(page, server, klal_id=2)
    assert page.evaluate(
        "() => !document.getElementById('scan-header').contains(document.getElementById('zoom-controls'))"
    ), "the zoom cluster is still inside the scan header"
    # Moved, not lost: it must still be on screen and still zoom.
    assert page.locator("#zoom-controls").is_visible()
    page.click("#zoom-in")
    page.wait_for_timeout(300)
    assert page.inner_text("#zoom-level") != "100%", "the zoom controls stopped working after the move"
    assert page.test_errors == []


def test_the_text_pane_header_names_the_klal_being_read(server, page):
    """"maybe sacrifice a line at top to add header that just says something like
    page text." The middle pane was the only one of the three without a bar, and
    the pane a reviewer spends the most time in was the one that never said where
    they were. Its reference is the klal, in both scripts, exactly as the scan
    pane names the page it is showing - and it has to FOLLOW the reviewer, not
    just render once."""
    _open_dashboard(page, server, klal_id=2)
    page.wait_for_timeout(600)
    assert page.inner_text("#text-ref-en").strip() == "Klal 2"
    assert "כלל" in page.inner_text("#text-ref-he")
    page.click("#nav-8")
    page.wait_for_timeout(900)
    assert page.inner_text("#text-ref-en").strip() == "Klal 8", (
        "the text pane's header did not follow the reviewer to another klal")
    # The Hebrew numeral comes from /api/numerals, the same table the scan header
    # uses - not a second gematria implementation (Lesson 13).
    assert _get_json(server, "/api/numerals")["8"] in page.inner_text("#text-ref-he")
    assert page.test_errors == []


def test_the_two_klal_markers_are_set_in_the_same_face(server, page):
    """Reviewer, 2026-09-01: "is the heb num in the index pane the same font as
    the text nums? it should be" - it was not.

    `--font-marker` was `'Inter', sans-serif`, and Inter carries no Hebrew, so
    every Hebrew marker resolved to whatever the system happened to pick; the
    index pane's `.nheb` meanwhile declared no font-family at all and inherited
    the body's Frank Ruhl Libre. The same numeral was a sans in one pane and a
    serif in the other, one pane apart, and the token's own comment claimed it
    was "the section number, in either script".

    Asserts the computed stack rather than a literal face name: the point is that
    the two agree and that the fallback is a CHOICE, not that it is any
    particular font - re-pointing --font-marker for another work must not fail
    this.
    """
    _open_dashboard(page, server, klal_id=12)
    page.wait_for_timeout(600)
    faces = page.evaluate("""() => {
        const f = sel => { const e = document.querySelector(sel);
                           return e ? getComputedStyle(e).fontFamily : null; };
        return { navHeb: f('#nav-12 .nheb'), navId: f('#nav-12 .nid'),
                 textMarker: f('#klal-block-12 .klal-marker-word'),
                 textHead: f('#klal-block-12 .klal-head .kid') };
    }""")
    assert all(faces.values()), faces
    assert len(set(faces.values())) == 1, (
        f"the klal markers are set in different faces across the panes: {faces}")
    # ...and the stack must actually name a Hebrew face, or "the same font" is
    # only true by accident of whatever the system resolves today.
    assert "David" in faces["navHeb"], (
        f"--font-marker names no Hebrew face, so its Hebrew fallback is unspecified: {faces['navHeb']}")
    assert page.test_errors == []


def test_the_latin_klal_id_does_not_outweigh_the_hebrew_one_in_the_index(server, page):
    """"english numbers are too large wasting space." The Latin id shared
    --nav-marker-size at 18px with a 34px min-width, in a 380px column of 222
    rows - the widest fixed thing in the row after the badges, for the half of
    the reference the BOOK does not print. The Hebrew marker keeps the larger
    size: that is the one a reviewer matches against the scan."""
    _open_dashboard(page, server)
    sizes = page.evaluate("""() => {
        const px = sel => parseFloat(getComputedStyle(document.querySelector(sel)).fontSize);
        const w  = sel => document.querySelector(sel).getBoundingClientRect().width;
        return { idSize: px('#nav-12 .nid'), hebSize: px('#nav-12 .nheb'),
                 idWidth: w('#nav-12 .nid') };
    }""")
    assert sizes["idSize"] < sizes["hebSize"], (
        f"the Latin id is not smaller than the Hebrew marker it sits beside: {sizes}")
    assert sizes["idWidth"] <= 30, f"the Latin id column is {sizes['idWidth']:.0f}px wide"
    assert page.test_errors == []


def test_the_part_selector_shares_the_filter_row(server, page):
    """"part dropdown creates asymmetry any suggestions?" It was a full-width
    block spanning the index pane while the other two panes had nothing at that
    height. Folded into the filter row it stops being a band across the pane and
    gives the list back a row - the standing "max real estate" ask."""
    _open_dashboard(page, server)
    geom = page.evaluate("""() => {
        const s = document.getElementById('part-select').getBoundingClientRect();
        const f = document.getElementById('filter-flagged').getBoundingClientRect();
        const pane = document.getElementById('nav-filter').getBoundingClientRect();
        return { sameRow: Math.abs((s.top + s.height/2) - (f.top + f.height/2)) < 6,
                 selW: Math.round(s.width), paneW: Math.round(pane.width) };
    }""")
    assert geom["sameRow"], f"the part selector is not on the filter row: {geom}"
    assert geom["selW"] < geom["paneW"] * 0.5, (
        f"the part selector still spans the pane: {geom['selW']}px of {geom['paneW']}px")
    # Still switches parts - moving a control must not break it.
    page.select_option("#part-select", "2")
    page.wait_for_timeout(1200)
    assert page.locator(".nav-item").count() > 0
    assert page.locator(".nav-item").first.get_attribute("data-klal-id") == "223"
    assert page.test_errors == []


def test_the_zoom_ladder_always_contains_one_hundred_percent(server, page):
    """REGRESSION 2026-09-02, reviewer: "zoom -+ goes directly from 95% to 120.
    100 seems pretty basic."

    The buttons stepped by `current +- 0.25` and the CLAMP is what broke it: from
    100%, three zoom-outs give 75 -> 50 -> 30 (clamped), and the way back is
    55 -> 80 -> 105. One clamp knocks the value off the quarter grid and every
    later step inherits the offset, so 100% - and every other round number -
    becomes unreachable. The ctrl+wheel's 0.15 steps do it faster.

    Asserts reachability from BOTH ends and from an off-ladder value the focus
    zoom leaves behind, which is the case a fixed grid alone would not cover.
    """
    _open_dashboard(page, server, klal_id=2)
    read = lambda: page.inner_text("#zoom-level")

    for _ in range(6):                       # down to the floor and stay there
        page.click("#zoom-out")
        page.wait_for_timeout(120)
    floor = read()
    seen = []
    for _ in range(6):
        page.click("#zoom-in")
        page.wait_for_timeout(120)
        seen.append(read())
    assert "100%" in seen, f"climbing from {floor} never passes 100%: {seen}"

    # ...and from an OFF-LADDER value, which is the case the reviewer actually
    # hit. ctrl+wheel zooms continuously in 0.15 steps, so it lands between
    # stops; the buttons must then walk back ONTO the ladder rather than carrying
    # the offset forward forever, which is what "95% -> 120%" was.
    _open_dashboard(page, server, klal_id=2)
    page.hover("#scan-viewer")
    page.keyboard.down("Control")
    page.mouse.wheel(0, -120)
    page.keyboard.up("Control")
    page.wait_for_timeout(400)
    off = read()
    assert off != "100%", "the wheel did not move the zoom off 100% - this half tests nothing"
    walked = []
    for _ in range(3):
        page.click("#zoom-out")
        page.wait_for_timeout(150)
        walked.append(read())
    assert "100%" in walked, f"from an off-ladder {off}, stepping down never hits 100%: {walked}"
    assert page.test_errors == []


def test_a_missing_corpus_endpoint_says_so_instead_of_rendering_nothing(server, page):
    """REGRESSION 2026-09-02, reviewer: "when i sync this repo on another machine
    no titles render ... is there code still needing to be committed and pushed?"

    Nothing was missing from the repo. A review_server.py process started BEFORE
    /api/corpus existed answers 404 with a JSON body; `r.json()` parses it
    happily, CORPUS becomes {error: ...}, every title renders as an empty string,
    and `.ph-title:empty` hides it. A deployment problem became a blank space
    with nothing in the console - Lesson 26, a filter that HIDES being worse than
    one that rewrites. The fetch now checks `r.ok` and names the likely cause.
    """
    errors = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.route("**/api/corpus", lambda route: route.fulfill(
        status=404, content_type="application/json", body='{"error": "unknown endpoint"}'))
    _open_dashboard(page, server)
    page.wait_for_timeout(800)
    named = [e for e in errors if "/api/corpus failed" in e]
    assert named, f"a missing /api/corpus produced no diagnostic at all: {errors}"
    assert "restart the server" in named[0], named[0]
    # ...and the dashboard must still WORK without it - the title is chrome.
    assert page.locator(".nav-item").count() > 0, "a missing title endpoint broke the whole page"


def test_the_pane_headers_are_centred_and_their_slots_are_peers(server, page):
    """Reviewer, 2026-09-02: "center the header in each pane. move the titles a
    bit closer to the center and make them the same size and boldness - the
    hebrew is darker and bigger than the other hebrew in the header."

    The Hebrew title was 16px/700 in full-strength ink beside a 13.5px/500 muted
    Hebrew reference, so it read as a heading with metadata trailing it rather
    than as one line. Asserts the RELATIONSHIP - every Hebrew slot matching every
    other, every Latin slot matching every other - not the particular sizes,
    which are a design choice that may move again.
    """
    _open_dashboard(page, server, klal_id=12)
    page.wait_for_timeout(600)
    data = page.evaluate("""() => {
        const out = { centring: [], he: [], en: [] };
        for (const id of ['nav-header', 'text-header', 'scan-header']) {
            const h = document.getElementById(id);
            const hr = h.getBoundingClientRect();
            const g = h.querySelector('.ph-mid').getBoundingClientRect();
            out.centring.push({ id, off: Math.round((g.left + g.right) / 2 - (hr.left + hr.right) / 2) });
            for (const e of h.querySelectorAll('.ph-title, .ph-ref')) {
                const cs = getComputedStyle(e);
                const key = e.classList.contains('ph-he') ? 'he' : 'en';
                out[key].push(cs.fontSize + '/' + cs.fontWeight + '/' + cs.color);
            }
        }
        return out;
    }""")
    for row in data["centring"]:
        assert abs(row["off"]) <= 1, f"{row['id']} content is {row['off']}px off centre"
    assert len(set(data["he"])) == 1, f"the Hebrew slots do not match each other: {set(data['he'])}"
    assert len(set(data["en"])) == 1, f"the Latin slots do not match each other: {set(data['en'])}"
    assert page.test_errors == []


def test_the_legend_does_not_let_the_klal_list_show_through_it(server, page):
    """The legend is a FIXED box over the index pane's own bottom corner, and it
    carried `opacity: 0.95` - which applies to the background too, so the four
    nav rows behind it ghosted through the counts. Klal titles overprinting
    numbers, in the one place on screen that is nothing but numbers."""
    _open_dashboard(page, server)
    opacity = page.evaluate("() => getComputedStyle(document.getElementById('legend')).opacity")
    assert opacity == "1", f"#legend is translucent ({opacity}); the nav rows behind it show through"
    bg = page.evaluate("() => getComputedStyle(document.getElementById('legend')).backgroundColor")
    assert "rgba" not in bg or bg.endswith(", 1)"), f"#legend's background is translucent: {bg}"
    assert page.test_errors == []


def test_the_klal_heading_keeps_its_flag_control_beside_it(server, page):
    """Reviewer, 2026-09-02: put the flag pill with its heading, and drop the
    section name.

    `.klal-flag-btn` carried `margin-inline-start: auto` in a pane-wide flex row,
    which pushed it ~490px away from the heading it belongs to - a control
    floating against nothing. The section name is gone because it never changed
    down the whole pane and the header bar already names the work.
    """
    _open_dashboard(page, server, klal_id=12)
    page.wait_for_timeout(800)
    geom = page.evaluate("""() => {
        const h = document.querySelector('#klal-block-12 .klal-head');
        const kid = h.querySelector('.kid').getBoundingClientRect();
        const btn = h.querySelector('.klal-flag-btn').getBoundingClientRect();
        const gap = Math.round(Math.max(kid.left, btn.left) - Math.min(kid.right, btn.right));
        const sizes = [...h.querySelectorAll('.kid-n')]
            .map(e => getComputedStyle(e).fontSize);
        return { gap, sizes, hasSection: !!h.querySelector('.sec') };
    }""")
    assert not geom["hasSection"], "the section name is still in the klal heading"
    assert geom["gap"] <= 40, f"the flag control sits {geom['gap']}px from its heading"
    # "make both numbers the same size" - they are the same fact in two scripts.
    assert len(set(geom["sizes"])) == 1, f"the two klal numerals differ in size: {geom['sizes']}"
    assert page.test_errors == []


def test_only_the_open_count_shows_on_a_nav_row_until_it_is_hovered(server, page):
    """Reviewer, 2026-09-02: "show the red open count and the rest on hover."
    Three coloured pills on every row made the column read as decoration, and the
    one number actually asking for something was the hardest to pick out."""
    # Targets the MACHINE-RESOLVED badge, which comes from the corpus and so
    # exists whatever the ledger holds. Keying on the decided badge made this
    # skip against the fixture's empty ledger, and a test that skips is not a
    # test.
    klal_id = next((r["klal_id"] for r in _get_json(server, "/api/klalim?part=1")
                    if r["machine_resolved_count"] and r["machine_disputed_count"]), None)
    assert klal_id is not None, "no klal carries both an open and a resolved count"
    _open_dashboard(page, server, klal_id=klal_id)
    page.wait_for_timeout(400)
    vis = """(id) => {
        const r = document.getElementById('nav-' + id);
        const v = sel => { const e = r.querySelector(sel);
                           return e ? getComputedStyle(e).visibility : null; };
        return { open: v('.ncount-open'), machine: v('.ncount-machine') };
    }"""
    # setActiveKlal marks the row `.active`, which reveals the extra counts by
    # design - measure a row the reviewer is NOT on.
    other = next(r["klal_id"] for r in _get_json(server, "/api/klalim?part=1")
                 if r["klal_id"] != klal_id and r["machine_resolved_count"] and r["machine_disputed_count"])
    at_rest = page.evaluate(vis, other)
    assert at_rest["machine"] == "hidden", f"the resolved badge is showing at rest: {at_rest}"
    assert at_rest["open"] == "visible", f"the open count must stay visible: {at_rest}"
    page.hover(f"#nav-{other}")
    page.wait_for_timeout(250)
    assert page.evaluate(vis, other)["machine"] == "visible", (
        "hovering the row did not reveal the other counts")
    assert page.test_errors == []


def test_the_text_pane_accounts_for_the_index_pennant(server, page):
    """REGRESSION 2026-09-02, reviewer: "117 shows flagged in the middle pane but
    not in the index pane."

    The index pennant means "anything in this klal is flagged", klal-level OR
    word-level; the text pane's button toggles the KLAL-level flag alone, and
    would refuse to clear what it displayed if it showed anything more. So the
    two panes answered different questions with the same word, and 15 of 222
    klalim showed a pennant in the index against an unflagged button in the text.
    The pane now names the open word-level flags as their own marker.
    """
    # Create the condition rather than hunt for it: the fixture's ledger is
    # empty, so nothing is flagged at all and this would otherwise skip.
    target = 30
    status, _ = _post_json(server, "/api/decisions/klal_flag", {
        "klal_id": target, "word_index": 5, "needs_revisit": True,
        "note": "a word-level flag, with no klal-level flag beside it",
    })
    assert status == 201
    nav = next(r for r in _get_json(server, "/api/klalim?part=1") if r["klal_id"] == target)
    klal = _get_json(server, f"/api/klal/{target}")
    assert nav["needs_revisit"], "a word-level flag must raise the index pennant"
    assert not klal["needs_revisit"], "...without claiming the KLAL itself is flagged"
    assert nav["ai_flag_count"] >= 1, "the open word-level flag is not being counted"

    _open_dashboard(page, server, klal_id=target)
    page.wait_for_timeout(800)
    assert page.locator(f"#nav-{target} .nflag").count() == 1, "the index pennant vanished"
    marker = page.locator(f"#klal-block-{target} .klal-wordflags")
    assert marker.count() == 1, (
        f"klal {target} shows a pennant in the index and nothing in the text pane")
    assert "word" in marker.inner_text()
    assert page.test_errors == []


def test_every_nav_row_reserves_all_three_badge_slots_with_red_leftmost(server, page):
    """Reviewer, 2026-09-02: "red pill first on the left so they all line up.
    green orange always in their slot even if nothing before it."

    A badge was omitted entirely at zero, so the red count - the only one asking
    the reviewer for something - sat at a different x on every row and the column
    could not be read down. Asserts the geometry across many rows, not the markup:
    the property is that the columns LINE UP.
    """
    _open_dashboard(page, server)
    rows = page.evaluate("""() => [...document.querySelectorAll('.nav-item')].slice(0, 25).map(r => {
        const at = sel => {
          const e = r.querySelector(sel);
          return e ? Math.round(e.getBoundingClientRect().left) : null;
        };
        return { klal: r.dataset.klalId, open: at('.ncount-open'),
                 machine: at('.ncount-machine'), decided: at('.ncount-decided') };
    })""")
    assert len(rows) >= 10, "not enough nav rows to judge alignment"
    for name in ("open", "machine", "decided"):
        missing = [r["klal"] for r in rows if r[name] is None]
        assert not missing, f"klal(im) {missing} have no {name} slot reserved at all"
        xs = {r[name] for r in rows}
        assert len(xs) == 1, f"the {name} badge sits at {len(xs)} different x positions: {sorted(xs)}"
    for r in rows:
        assert r["open"] < r["machine"] < r["decided"], (
            f"klal {r['klal']}: badges are not red, amber, green left to right: {r}")
    assert page.test_errors == []


def test_every_legend_count_explains_itself_on_hover(server, page):
    """Reviewer, 2026-09-02: "hovering over the counts on the bottom surface
    explanation." The one-line legend hides its labels, so without these the bar
    is five unexplained numbers. Each must say what the state MEANS - not repeat
    its own name, which is what the first version did."""
    status, _ = _post_json(server, "/api/decisions/manual", {
        "klal_id": 20, "word_index": 1, "original_word": "לא-המילה-שכאן",
        "chosen_text": "תחליף", "note": "so the recorded row exists",
    })
    assert status == 201
    _open_dashboard(page, server)
    rows = page.evaluate("""() => [...document.querySelectorAll('#legend .legend-row')].map(r => ({
        bucket: r.dataset.bucket,
        title: r.title,
        count: (r.querySelector('.legend-count') || {}).textContent,
    }))""")
    assert len(rows) >= 5, f"expected every state plus the recorded total: {rows}"
    for r in rows:
        assert r["title"], f"legend row {r['bucket']} has no hover explanation"
        # A real explanation, not the label echoed back with a number.
        assert len(r["title"]) > 80, f"{r['bucket']}'s tooltip is too thin to explain anything: {r['title']}"
        assert r["count"] in r["title"], (
            f"{r['bucket']}'s tooltip does not mention its own count {r['count']}")
        assert r["title"].count("—") <= 1 or r["title"].count(r["bucket"]) <= 1, (
            f"{r['bucket']}'s tooltip repeats its own name: {r['title'][:120]}")
    assert page.test_errors == []


def _find_unaligned_word_in_a_multi_page_klal(server):
    """(klal_id, word_index) of a word with NO DocAI alignment, in a klal that
    spans pages - the case where falling back to the klal's start page is a
    guess, and usually the wrong one."""
    for row in _get_json(server, "/api/klalim?part=1"):
        klal = _get_json(server, f"/api/klal/{row['klal_id']}")
        pages = klal.get("word_pages") or {}
        distinct = {p for p in pages.values() if p is not None}
        if len(distinct) < 2:
            continue
        n = len(klal["clean_text"].split(" "))
        missing = [i for i in range(n) if pages.get(str(i)) is None]
        if missing:
            return row["klal_id"], missing[len(missing) // 2], klal["page"]
    return None, None, None


def test_a_word_with_no_alignment_still_opens_the_page_it_falls_on(server, page):
    """REGRESSION 2026-09-02, reviewer on klal 88 w963: "the scan shows the wrong
    page, the klal extends over two and that word is on the following page. and
    it doesnt zoom in."

    1,649 of Part 1's words have no aligned DocAI token, so `word_pages` has no
    entry for them - and the fallback went straight to the klal's START page.
    For the 746 of those that sit in a MULTI-PAGE klal that is usually wrong, and
    both symptoms followed from it: wrong page, so no box on it, so nothing to
    zoom to. Words are in reading order, so the nearest ALIGNED neighbour is a far
    better answer than the klal's first page.

    Three click handlers each carried their own copy of this lookup and only
    `pageForWord()` was fixed first, which is why the first attempt changed
    nothing; all of them go through the one function now.
    """
    klal_id, word_index, start_page = _find_unaligned_word_in_a_multi_page_klal(server)
    assert klal_id is not None, "no unaligned word in a multi-page klal - nothing to test"
    klal = _get_json(server, f"/api/klal/{klal_id}")
    pages = klal["word_pages"]
    neighbours = [pages[str(i)] for i in range(word_index - 40, word_index + 41)
                  if pages.get(str(i)) is not None]
    assert neighbours, "the word has no aligned neighbour within 40 words either way"

    _open_dashboard(page, server)
    page.evaluate(f"() => {{ location.hash = '#klal={klal_id}&word={word_index}'; }}")
    page.wait_for_timeout(2500)
    shown = int(page.evaluate(
        r"() => (document.getElementById('page-img').getAttribute('src') || '')"
        r".match(/page_(\d+)/)[1]"))
    assert shown in neighbours, (
        f"klal {klal_id} w{word_index} has no alignment; the scan opened page {shown}, "
        f"which is not where its neighbours are ({sorted(set(neighbours))})")
    assert page.test_errors == []


def test_only_one_page_lookup_exists(server, page):
    """The bug above survived its first fix because three click handlers each
    carried their own copy of `word_pages[i] ?? k.page`, and only the shared
    helper was corrected. This is the cheap assertion that keeps them merged -
    the same defect class this file has now recorded four times."""
    app_js = os.path.join(REPO, "review_frontend", "app.js")
    with open(app_js, encoding="utf-8") as f:
        source = f.read()
    body = re.sub(r"//.*", "", source)
    copies = body.count("word_pages[i]")
    assert copies == 0, (
        f"{copies} hand-rolled per-word page lookup(s) outside pageForWord(); "
        "route them through it instead")


def test_a_word_that_cannot_be_placed_on_the_scan_says_so(server, page):
    """Some words have no alignment ANYWHERE, so even the right page has no box
    to draw and nothing to zoom to. The pane just sat there looking broken -
    which is how it was reported. The warning is deferred and cancellable:
    routing calls showPage() several times and the earlier ones legitimately find
    no box yet, so announcing on the first miss fired it on words that DO get one
    a moment later."""
    klal_id, word_index, _ = _find_unaligned_word_in_a_multi_page_klal(server)
    assert klal_id is not None
    _open_dashboard(page, server)

    def route_and_watch(kid, wi):
        page.wait_for_function(
            "() => document.getElementById('toast').style.display !== 'block'", timeout=6000)
        page.evaluate("() => { location.hash = '#'; }")
        page.evaluate(f"() => {{ location.hash = '#klal={kid}&word={wi}'; }}")
        for _ in range(28):
            page.wait_for_timeout(120)
            text = page.evaluate(
                "() => document.getElementById('toast').style.display === 'block'"
                " ? document.getElementById('toast').textContent : null")
            if text and "no OCR alignment" in text:
                return True
        return False

    warned = route_and_watch(klal_id, word_index)
    boxes = page.locator("#hl-container .hl-box.focused").count()
    # Exactly one of the two must be true: either the word IS on the scan, or the
    # reviewer is told it is not. Silence with no box is the reported bug.
    assert warned or boxes == 1, (
        f"klal {klal_id} w{word_index}: no focus box and no explanation")

    # ...and a word that IS locatable must NOT be warned about.
    kid, wi = _find_disputed_word()
    warned_ok = route_and_watch(kid, wi)
    if page.locator("#hl-container .hl-box.focused").count() == 1:
        assert not warned_ok, "warned about a word that was found on the scan"
    assert page.test_errors == []


def test_a_recorded_ruling_says_who_made_it(server, page):
    """REGRESSION 2026-09-02, reviewer on the alef-lamed pair: "did a human (me)
    adjudicate it? it wasn't marked in yellow or red."

    It did not. Automated passes write `manual_correction` records, which this
    dashboard has always drawn GREEN as Human-Decided - so a machine ruling
    entered the corpus already looking settled and never appeared in anyone's
    queue. Measured: 1,615 of the ledger's 2,520 rulings were machine-written.
    Every recorded row now carries its `reviewer`, and a chip filters to the ones
    no person adjudicated.
    """
    status, _ = _post_json(server, "/api/decisions/manual", {
        "klal_id": 22, "word_index": 3, "original_word": "לא-המילה-שכאן",
        "chosen_text": "תחליף", "note": "a ruling a person made",
    })
    assert status == 201
    rows = _get_json(server, "/api/word-states?part=1")["recorded"]
    assert rows, "no recorded rulings to judge"
    for r in rows:
        assert "by_human" in r and isinstance(r["by_human"], bool), r
        assert "reviewer" in r, r
    # The endpoint writes `reviewer: local`, which is what a person clicking is.
    mine = [r for r in rows if r["klal_id"] == 22 and r["word_index"] == 3]
    assert mine and mine[0]["by_human"], mine

    _open_dashboard(page, server)
    page.eval_on_selector("#legend .legend-clickable[data-bucket='recorded']", "el => el.click()")
    page.wait_for_selector("#flag-list-panel .flag-list-item", timeout=10000)
    served_machine = sum(1 for r in rows if not r["by_human"])
    chip = page.locator("#flag-list-panel .rec-chip[data-status='machine']")
    if served_machine:
        assert chip.count() == 1, "no chip for the rulings nobody adjudicated"
        assert int(chip.locator("b").inner_text()) == served_machine
        chip.click()
        page.wait_for_timeout(300)
        assert page.locator("#flag-list-panel .flag-list-item").count() == served_machine
        assert page.locator("#flag-list-panel .recorded-item.rec-machine").count() == served_machine
    else:
        assert chip.count() == 0, "a chip for a category with nothing in it"
    assert page.test_errors == []


def test_a_gap_does_not_steal_the_focus_from_the_word_at_its_index(server, page):
    """REGRESSION 2026-09-03, reviewer: "clicking on Klal 17 (יז) · Word #308 —
    בסתם highlights the wrong word."

    A `delete`-opcode entry is a GAP - text the scan has and the corpus lacks -
    addressed by the index it would be inserted BEFORE. It therefore SHARES that
    index with the word standing there while its bbox points somewhere else
    entirely: klal 17 w308 is `בסתם` at x=0.62 and the omission sharing its index
    sits at x=0.86. Two faults compounded - api_page let the gap's key suppress
    the word so it was never served at all, and app.js matched focus on
    word_index alone so the gap took it. 40 gap entries across 35 klalim share an
    index with a real word.
    """
    corr = json.load(open(os.path.join(REPO, "corrections_part1.json"), encoding="utf-8"))
    target = None
    for kid, items in sorted(corr.items(), key=lambda kv: int(kv[0])):
        for c in items:
            if c.get("opcode") == "delete" and c.get("bbox") and c.get("page") is not None:
                target = (int(kid), c["word_index"], c["page"], c["bbox"])
                break
        if target:
            break
    assert target, "no gap entry with a scan position - nothing to test"
    klal_id, word_index, gap_page, gap_bbox = target

    items = _get_json(server, f"/api/page/{gap_page}")
    here = [c for c in items if c.get("klal_id") == klal_id and c.get("word_index") == word_index]
    kinds = {c.get("kind") for c in here}
    assert "plain" in kinds or any(c.get("opcode") != "delete" for c in here), (
        f"klal {klal_id} w{word_index}: the gap suppressed the word - only {kinds} served")

    _open_dashboard(page, server)
    page.evaluate(f"() => {{ location.hash = '#klal={klal_id}&word={word_index}'; }}")
    page.wait_for_timeout(2500)
    focused = page.evaluate("""() => {
        const f = document.querySelectorAll('#hl-container .hl-box.focused');
        return [...f].map(b => parseFloat(b.style.left));
    }""")
    assert len(focused) == 1, f"expected exactly one focused box, got {len(focused)}"
    # ...and it must NOT be the gap's box.
    gap_left = gap_bbox["x1"] * 100
    assert abs(focused[0] - gap_left) > 1.0, (
        f"the focused box sits on the gap at {gap_left:.1f}%, not on the word")
    assert page.test_errors == []


def test_each_legend_swatch_matches_the_line_the_text_pane_draws(server, page):
    """Reviewer, 2026-09-03: "why are the purple words shown in the count with a
    purple underline but all the others are shown as boxes?"

    The legend was inconsistent with ITSELF - three box-ish chips and one
    underline - and matched neither pane. It cannot mirror both (the scan draws
    boxes, the text draws rules), so it mirrors the TEXT pane, where the line
    STYLE carries meaning colour alone does not: solid = the vision pipeline
    ruled, dotted = the machine settled it, dashed = an automated pass flagged it
    on textual reasoning with no vision confirmation.

    Asserts the swatches against app.css's own `.flag-word.state-*` rules, so the
    two cannot drift apart.
    """
    with open(os.path.join(REPO, "review_frontend", "app.css"), encoding="utf-8") as f:
        css = f.read()
    wanted = {}
    for state, bucket in (("open", "machine_disputed"), ("machine", "machine_resolved"),
                          ("human", "decided"), ("ai-flag", "ai_flag")):
        m = re.search(r"\.flag-word\.state-" + re.escape(state)
                      + r"\s*\{[^}]*border-bottom:\s*(\d+)px\s+(solid|dashed|dotted)", css)
        assert m, f"no border-bottom rule for .flag-word.state-{state}"
        wanted[bucket] = (m.group(1) + "px", m.group(2))

    _open_dashboard(page, server)
    got = page.evaluate("""() => {
        const out = {};
        for (const r of document.querySelectorAll('#legend .legend-row')) {
            const i = r.querySelector('i');
            if (!i || !r.dataset.bucket) continue;
            const cs = getComputedStyle(i);
            out[r.dataset.bucket] = [cs.borderBottomWidth, cs.borderBottomStyle];
        }
        return out;
    }""")
    for bucket, expect in wanted.items():
        assert bucket in got, f"no legend swatch for {bucket}"
        assert tuple(got[bucket]) == expect, (
            f"{bucket}: legend draws {got[bucket]}, the text pane draws {list(expect)}")
    # ...and every swatch is the SAME KIND of mark - that was the complaint.
    assert all(v[1] in ("solid", "dashed", "dotted") for v in got.values()), got
    assert page.test_errors == []


def test_the_count_footer_fits_on_one_line(server, page):
    """Reviewer, 2026-09-03: "count footer is a bit too wide, wraps to anothe
    line." It needed 394px in a 347px pane.

    The legend is pinned over the index pane's own bottom corner, so a second
    line eats another row of klalim and pushes the box up over the list. Asserts
    the GEOMETRY - one row of items, no wrap - rather than any particular size,
    since the trim was spread across padding, gaps, swatch width and the count
    column and any of those may move again.
    """
    _open_dashboard(page, server)
    geom = page.evaluate("""() => {
        const legend = document.getElementById('legend');
        const cs = getComputedStyle(legend);
        const rows = [...legend.querySelectorAll('.legend-row')];
        const need = rows.reduce((s, r) => s + r.getBoundingClientRect().width, 0)
                     + parseFloat(cs.columnGap) * (rows.length - 1);
        return {
            lines: new Set(rows.map(r => Math.round(r.getBoundingClientRect().top))).size,
            rows: rows.length,
            needs: Math.round(need),
            avail: Math.round(legend.clientWidth
                              - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight)),
        };
    }""")
    assert geom["rows"] >= 4, f"the legend lost entries: {geom}"
    assert geom["lines"] == 1, (
        f"the count footer wraps onto {geom['lines']} lines "
        f"(needs {geom['needs']}px, has {geom['avail']}px)")
    assert geom["needs"] <= geom["avail"], geom
    assert page.test_errors == []
