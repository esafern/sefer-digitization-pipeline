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
    page.goto(server + "/", wait_until="networkidle", timeout=15000)
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

    proc = subprocess.Popen(
        [sys.executable, os.path.join(REPO, "pipeline", "review_server.py"), "--port", str(port)],
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
    klal_id, word_index = 1, 85

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
    klal_id, word_index = 1, 85
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
    """Part 1's clean_text contains 3 bare `&` tokens (klal 69 word 338, klal
    77 word 11, klal 167 word 24 - see FOREIGN_CHARACTER_BASELINE in
    tests/test_corpus_invariants.py). The candidate/manual context panes
    interpolate clean_text straight into innerHTML, so they must escape it:
    `& ` survives today only because it is not a valid entity reference, which
    is luck, not a property anyone chose."""
    klal_id, word_index = 69, 338
    _open_dashboard(page, server, klal_id=klal_id)
    page.evaluate(
        "([kid, widx]) => openManualCorrectionPanel(kid, widx, '&', null)",
        [klal_id, word_index],
    )
    page.wait_for_selector("#manual-panel-body .panel-word-context", timeout=5000)

    context_text = page.inner_text("#manual-panel-body .panel-word-context")
    assert "[&]" in context_text, (
        f"the klal-69 ampersand did not render verbatim in the context pane: {context_text!r}"
    )
    assert "&amp;" not in context_text, "double-escaped"
    assert page.test_errors == []


def test_focus_box_transparent_and_zoom_preserves_focus(server, page):
    """Verifies that selecting a word sets a focused highlight box with transparent
    background (for human eyeball review), and that zooming in does not clear the focus."""
    klal_id = 1
    _open_dashboard(page, server, klal_id)

    page.evaluate("""async () => {
        const k = await fetch('/api/klal/1').then(r => r.json());
        const corr = k.corrections.find(c => c.word_index === 85);
        showPage(14, 1, corr);
    }""")
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

