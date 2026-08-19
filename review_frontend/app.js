// Yad Malachi review dashboard frontend. Fetches data lazily from
// review_server.py's JSON API instead of having it all inlined - see
// PROJECT-STATUS.md "Review dashboard rearchitecture" for why.

let FLAGS = {};
let KLALIM = [];          // lightweight list from /api/klalim
let klalById = {};
let mountedKlal = {};     // klal_id -> full payload once fetched
let fetchInFlight = {};   // klal_id -> Promise, avoids double-fetch races
let WITNESS_PAGES = [];   // {page, klal_id, total, decided} from /api/witness - continuation-only
                           // pages (no klal marker of their own, e.g. 24/37/40) that pagesWithKlalim()
                           // can't otherwise reach - see PROJECT-STATUS.md session handoff 2026-08-11.

const textScroll = document.getElementById('text-scroll');
const navList = document.getElementById('nav-list');
const legend = document.getElementById('legend');
const tooltip = document.getElementById('tooltip');

// ---------- HTML escaping ----------
// Every interpolation below of corpus text, a recorded decision, a reviewer's
// note or a Gemini rationale into an innerHTML template MUST go through one
// of these. This is not a security posture (the server is local-only and the
// data is the user's own) - it is a FIDELITY one, and it had already broken:
//
// The candidate panel's custom-reading input was written
//   value="${activeText}"
// and this corpus's abbreviation mark - gershayim - is the literal ASCII
// character `"`. part1.json's clean_text contains 6,448 of them. So a
// reviewer who records a custom reading like `ב"ד` (6 such decisions are
// already in review_decisions.jsonl) and later reopens that panel gets
//   value="ב"ד"
// which the browser parses as value="ב" plus a junk attribute: the input
// silently displays `ב`, and saving again records `ב` as their decision. A
// human's exact Hebrew reading, truncated at the most common punctuation
// mark in the book, in the one tool whose entire job is exact fidelity
// (Success Criterion #1). The manual-correction panel already escaped its
// own value= for precisely this reason; the candidate panel never did.
//
// Element-content interpolations are the same class one step milder: part1's
// clean_text carries 3 bare `&` tokens (klal 69/77/167), which the context
// panes render raw. `& ` happens to survive today because it is not a valid
// entity reference - `&amp` or `&lt` in a future correction would not.
function escapeHtml(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
// Attribute values additionally need the quote characters neutralised -
// see the gershayim case above.
function escapeAttr(s) {
  return escapeHtml(s).replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

// Every flagged word/gap reduces to exactly one of three review states,
// shown identically across the nav legend, the text pane, and the scan
// pane: a human decision always wins (even overriding a machine
// "confirmed" verdict), otherwise a `current_text_confirmed` flag means
// the vision pass resolved it without a human, otherwise it's still an
// open dispute nobody has looked at.
const STATE_META = {
  open:    { label: 'Machine-Disputed', color: '#e53e3e' },
  machine: { label: 'Machine-Resolved', color: '#d69e2e' },
  human:   { label: 'Human-Decided',    color: '#38a169' },
};
function wordState(corr) {
  // GUARD added 2026-08-17 (code review): renderKlalBody() branches on
  // opcode === 'ai_flag' before this ever runs, so it's not reachable
  // today - but an ai_flag's current_decision is the AI's OWN klal_flag
  // record, not a human decision, and this function has no other way to
  // tell the difference. If a future code path ever calls wordState() on
  // one directly, it must not silently render an unresolved AI flag as
  // Human-Decided.
  if (corr.opcode === 'ai_flag') return 'open';
  if (corr.current_decision) return 'human';
  if (corr.flag === 'current_text_confirmed') return 'machine';
  return 'open';
}
// The word's final display color/underline follows wordState() above (a
// human decision always wins), but that collapses the machine's own verdict
// once a human has acted - e.g. it can no longer distinguish "a human
// overrode an open dispute" from "a human double-checked an already-
// resolved word." The status LABEL (tooltip / candidate panel) shows both
// axes instead of just the final one.
function statusLabel(corr) {
  const machine = corr.flag === 'current_text_confirmed' ? STATE_META.machine.label : STATE_META.open.label;
  return corr.current_decision ? `${machine} · ${STATE_META.human.label}` : machine;
}

async function init() {
  const [flags, klalim, witness] = await Promise.all([
    fetch('/api/flags').then(r => r.json()),
    fetch('/api/klalim').then(r => r.json()),
    fetch('/api/witness').then(r => r.json()),
  ]);
  FLAGS = flags;
  KLALIM = klalim;
  klalById = Object.fromEntries(klalim.map(k => [k.klal_id, k]));
  WITNESS_PAGES = witness.pages || [];

  buildLegend();
  buildNav();
  buildPlaceholders();
  setupObserver();
  setupFilter();
  setupZoomPan();
  setupPanels();
  setupNavRefreshOnReturn();

  lastActiveKlalId = KLALIM[0].klal_id;
  setActiveKlal(lastActiveKlalId);
}

// FIXED 2026-08-14 (PROJECT-STATUS.md audit item 5): KLALIM/klalById were
// fetched once at init and only ever patched in-memory by THIS tab's own
// saves (see saveCandidateDecision's open_count/decided_count arithmetic
// above) - a decision recorded from another browser tab, or a
// rebuild_all.sh run that reclassified flags corpus-wide (exactly what
// this session's own drift-check/PASS3-allowlist fixes did), left this
// tab's nav badges and legend totals silently wrong until a manual reload,
// with nothing to prompt the reload. The per-klal text/scan panes already
// self-heal on next save (the "stale client cache after a live rebuild"
// fix, 2026-08-09) - only the corpus-wide nav/legend aggregate lacked an
// equivalent. Refetch on visibility-return rather than polling: it's the
// natural moment a user who tabbed away (to run a rebuild, to look at
// something else) comes back, costs nothing while the tab is actually
// idle in the background, and needs no server changes.
function setupNavRefreshOnReturn() {
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') refreshKlalimList();
  });
}

// Dedupes concurrent callers (a visibility-triggered refresh landing at
// the same moment as a save's own refreshKlalimList() call) onto a single
// in-flight fetch, added 2026-08-14 (code review, session audit item 5,
// minor hardening alongside finding 7): without this, two callers each
// fire their own full /api/flags + /api/klalim + /api/witness round trip
// for no benefit - not a correctness bug (whichever resolves last still
// wins with fresh truth, same as before), just wasted requests.
let klalimRefreshInFlight = null;

async function refreshKlalimList() {
  if (klalimRefreshInFlight) return klalimRefreshInFlight;
  klalimRefreshInFlight = (async () => {
    try {
      // Also refetches /api/witness (added 2026-08-14, code review minor
      // finding): init() fetches it but the original visibility-refresh
      // fix didn't, leaving WITNESS_PAGES stale by the same mechanism the
      // fix was closing for everything else.
      const [flags, klalim, witness] = await Promise.all([
        fetch('/api/flags').then(r => r.json()),
        fetch('/api/klalim').then(r => r.json()),
        fetch('/api/witness').then(r => r.json()),
      ]);
      FLAGS = flags;
      KLALIM = klalim;
      klalById = Object.fromEntries(klalim.map(k => [k.klal_id, k]));
      WITNESS_PAGES = witness.pages || [];
      buildLegend();
      buildNav();
      applyFlaggedFilter(); // buildNav() rebuilds nav-items from scratch, unfiltered - reapply
      // FIXED 2026-08-14 (code review, session audit item 5, finding 8):
      // buildNav()'s full innerHTML rebuild also wipes the '.active' class
      // setActiveKlal put on the current nav row - a reviewer scrolled deep
      // into the corpus who tabs away and back lost their highlighted
      // position with no visible indication of where they were.
      // scrollIntoView inside setActiveKlal is a no-op when the row is
      // already visible, so this doesn't cause an unwanted scroll jump on
      // an ordinary refresh.
      if (lastActiveKlalId != null) setActiveKlal(lastActiveKlalId);
    } catch (e) {
      // Added 2026-08-14 (code review minor finding): an unhandled
      // rejection here (e.g. the server restarting mid-request, as this
      // session's own review_server.py restart did) previously surfaced
      // only as a silent console error with no indication of what failed.
      console.error('refreshKlalimList failed (nav/legend may be stale until the next refresh):', e);
    } finally {
      klalimRefreshInFlight = null;
    }
  })();
  return klalimRefreshInFlight;
}

function buildLegend() {
  legend.innerHTML = '';
  const totals = { open: 0, machine: 0, human: 0 };
  KLALIM.forEach(k => {
    totals.open += k.machine_disputed_count || 0;
    totals.machine += k.machine_resolved_count || 0;
    totals.human += k.decided_count || 0;
  });
  Object.entries(STATE_META).forEach(([state, { label, color }]) => {
    const row = document.createElement('div');
    row.className = 'legend-row';
    const shape = state === 'machine' ? 'border-radius:2px;border:1.5px dotted ' + color + ';background:transparent;' : 'background:' + color + ';';
    row.innerHTML = `<i style="${shape}"></i><span>${label}</span><b class="legend-count">${totals[state]}</b>`;
    legend.appendChild(row);
  });
  // AI-flagged words render with their own purple dashed underline style
  // (state-ai-flag in app.css) distinct from the three main states above.
  // Add a key so reviewers know what the colour means.
  const aiRow = document.createElement('div');
  aiRow.className = 'legend-row';
  aiRow.innerHTML = `<i style="border-bottom:3px dashed #805ad5;background:transparent;"></i><span>AI-Flagged</span>`;
  legend.appendChild(aiRow);
}

// ---------- nav pane ----------
function navItemInnerHtml(k) {
  const flagIcon = k.needs_revisit ? '<span class="nflag">&#9873;</span>' : '';
  // Two badges, not one undifferentiated count: red = still needs a
  // decision, green = already decided (a reviewer wants to know at a
  // glance how much of a klal's queue is actually done, not just how many
  // words were ever flagged).
  const openBadge = k.open_count ? `<span class="ncount ncount-open">${k.open_count}</span>` : '';
  const decidedBadge = k.decided_count ? `<span class="ncount ncount-decided">${k.decided_count}</span>` : '';
  // No punctuation badge here on purpose: the proposed-punctuation
  // affordances (legend swatch, nav badges, inline blue-dot markers) were
  // removed from the UI 2026-08-11 on user feedback, leaving that feature
  // dormant-but-reversible rather than deleted. /api/klalim still serves
  // punctuation_count/punctuation_open_count for whenever it returns.
  // (That commit left this comment half-rewritten - three unfinished
  // clauses that described a badge which isn't there - until 2026-08-14.)
  return `<span class="nid">${k.klal_id}</span><span class="ntitle" title="${escapeAttr(k.title)}">${escapeHtml(k.title)}</span>${flagIcon}${openBadge}${decidedBadge}`;
}

function buildNav() {
  navList.innerHTML = '';
  KLALIM.forEach(k => {
    const item = document.createElement('div');
    item.className = 'nav-item' + (k.correction_count ? ' has-flags' : '');
    item.id = 'nav-' + k.klal_id;
    item.dataset.klalId = k.klal_id;
    item.onclick = () => jumpTo(k.klal_id);
    item.innerHTML = navItemInnerHtml(k);
    navList.appendChild(item);
  });
}

function applyFlaggedFilter() {
  const only = document.getElementById('filter-flagged').checked;
  document.querySelectorAll('.nav-item').forEach(el => {
    const kid = parseInt(el.dataset.klalId);
    el.style.display = (!only || klalById[kid].needs_revisit) ? '' : 'none';
  });
}

function setupFilter() {
  document.getElementById('filter-flagged').addEventListener('change', applyFlaggedFilter);
}

// ---------- middle pane: placeholders + lazy mount ----------
function buildPlaceholders() {
  textScroll.innerHTML = '';
  KLALIM.forEach(k => {
    const block = document.createElement('div');
    block.className = 'klal-block';
    block.id = 'klal-block-' + k.klal_id;
    block.dataset.klalId = k.klal_id;
    block.dataset.page = k.page || '';
    block.dataset.mounted = 'false';
    // Proportional height estimate (chars-per-line-ish) so mounting real
    // content doesn't cause a large scroll jump for long klalim.
    const estLines = Math.max(1, Math.ceil((k.text_length || 20) / 55));
    block.style.minHeight = (24 + estLines * 34) + 'px';

    const head = document.createElement('div');
    head.className = 'klal-head';
    head.innerHTML = `<span class="kid">כלל ${k.klal_id}</span><span class="sec">${escapeHtml(k.section)}</span>`;
    const flagBtn = document.createElement('button');
    flagBtn.className = 'klal-flag-btn' + (k.needs_revisit ? ' active' : '');
    flagBtn.textContent = k.needs_revisit ? '⚑ flagged' : '⚑ flag';
    flagBtn.onclick = (e) => { e.stopPropagation(); openKlalFlagPanel(k.klal_id); };
    head.appendChild(flagBtn);
    block.appendChild(head);

    const body = document.createElement('div');
    body.className = 'klal-body loading';
    body.textContent = '…';
    block.appendChild(body);

    textScroll.appendChild(block);
  });
}

let observer;
function setupObserver() {
  observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const kid = parseInt(entry.target.dataset.klalId);
        mountKlal(kid);
      }
    });
  }, { root: null, rootMargin: '800px 0px', threshold: 0 });
  document.querySelectorAll('.klal-block').forEach(el => observer.observe(el));
}

function fetchKlal(klalId) {
  if (mountedKlal[klalId]) return Promise.resolve(mountedKlal[klalId]);
  if (fetchInFlight[klalId]) return fetchInFlight[klalId];
  fetchInFlight[klalId] = fetch('/api/klal/' + klalId)
    .then(r => r.json())
    .then(data => { mountedKlal[klalId] = data; return data; });
  return fetchInFlight[klalId];
}

async function mountKlal(klalId) {
  const block = document.getElementById('klal-block-' + klalId);
  if (!block || block.dataset.mounted === 'true') return;
  block.dataset.mounted = 'true'; // set immediately, avoid re-entrant double mount
  const data = await fetchKlal(klalId);
  renderKlalBody(block, data);
  observer.unobserve(block);
}

function renderKlalBody(block, k) {
  const body = block.querySelector('.klal-body');
  body.className = 'klal-body';
  body.innerHTML = '';

  const words = (k.clean_text || '').split(' ');
  const byIndex = {};
  k.corrections.forEach(c => { if (c.opcode !== 'delete') byIndex[c.word_index] = c; });
  const gapsBefore = {};
  k.corrections.forEach(c => {
    if (c.opcode === 'delete') {
      gapsBefore[c.word_index] = gapsBefore[c.word_index] || [];
      gapsBefore[c.word_index].push(c);
    }
  });

  words.forEach((w, i) => {
    if (gapsBefore[i]) gapsBefore[i].forEach(c => body.appendChild(makeGapMarker(k.klal_id, c)));
    if (w === '[.]') {
      const mark = document.createElement('span');
      mark.className = 'editorial-mark';
      mark.textContent = '[.]';
      mark.title = 'Editorial insertion: not in the original print. Marks a title/explanation boundary the printer left unpunctuated.';
      body.appendChild(mark);
      body.appendChild(document.createTextNode(' '));
      return;
    }
    const corr = byIndex[i];
    if (corr && corr.opcode === 'ai_flag') {
      // FIXED 2026-08-17 (user bug report on klal 1: an AI pass's note
      // named a specific disputed word in prose, but nothing highlighted
      // it - the reviewer had to find it by reading the note and searching
      // the text by eye). Routed through the same manual-correction panel
      // "plain word" clicks already use - it already displays an existing
      // `note` field (klal_flag's own note, the AI pass's reasoning) and
      // lets the reviewer propose a fix or dismiss it, no new panel needed.
      const span = document.createElement('span');
      span.className = 'flag-word state-ai-flag';
      span.textContent = w;
      span.title = corr.reasoning || '';
      span.onclick = () => {
        // Show the klal's scan page (the ai_flag has no per-word bbox, but
        // seeing the page is better than seeing nothing - mirrors what
        // attachWordHandlers does for correction candidates via corr.page).
        if (k.page) showPage(k.page, k.klal_id);
        openManualCorrectionPanel(k.klal_id, i, w, corr);
      };
      body.appendChild(span);
    } else if (corr && corr.opcode === 'manual') {
      // Reviewer-flagged word (2026-08-13, no machine candidate behind it -
      // see openManualCorrectionPanel) - always Human-Decided (there's no
      // machine-disputed phase for these to have come from), routed through
      // the dedicated manual panel rather than openCandidatePanel, which is
      // built around vision-generated options this kind of entry doesn't have.
      const span = document.createElement('span');
      // chosen_text=='' means marked for deletion (2026-08-13) - the word
      // is still physically present in clean_text (recording a decision
      // and applying it to the corpus are always separate steps, same as
      // every other decision type here), so still shown, struck through
      // to signal "pending removal" rather than "pending replacement".
      const chosenText = corr.current_decision.chosen_text;
      const pendingDelete = chosenText === '';
      // FIXED 2026-08-17 (user bug report: a recorded manual correction
      // turned the word green but kept showing the OLD, disputed text with
      // no sign of what it would become once applied - confusing, read as
      // "wrong text" rather than "not yet applied"). A pending REPLACEMENT
      // (chosen_text set, and actually different from what part1.json
      // still has - editing a word to itself is a real, if odd, case that
      // needs no "pending" treatment at all) gets the same struck-through
      // treatment as pending-delete, plus the actual chosen text shown
      // right after it, so the reviewer sees the outcome without reopening
      // the panel.
      const pendingReplace = !pendingDelete && chosenText && chosenText !== w;
      span.className = 'flag-word state-human' + (pendingDelete ? ' pending-delete' : '')
        + (pendingReplace ? ' pending-replace' : '');
      span.textContent = w;
      span.onclick = () => openManualCorrectionPanel(k.klal_id, i, w, corr);
      body.appendChild(span);
      if (pendingReplace) {
        const arrow = document.createElement('span');
        arrow.className = 'pending-replace-arrow';
        arrow.textContent = ' → ';
        body.appendChild(arrow);
        const repl = document.createElement('span');
        repl.className = 'pending-replace-text';
        repl.textContent = chosenText;
        repl.title = 'Pending: recorded but not yet applied to part1.json';
        repl.onclick = () => openManualCorrectionPanel(k.klal_id, i, w, corr);
        body.appendChild(repl);
      }
    } else if (corr) {
      const span = document.createElement('span');
      span.className = 'flag-word state-' + wordState(corr);
      span.textContent = w;
      attachWordHandlers(span, k.klal_id, corr);
      body.appendChild(span);
    } else {
      // Plain, not-yet-flagged word - clickable too (2026-08-13, "add
      // feature for reviewer to flag any word and replace it"), not just
      // ones the machine pipeline already flagged. No persistent styling
      // (a hover-only affordance, see .plain-word:hover in app.css) so the
      // vast majority of never-touched text doesn't look visually "flagged".
      const span = document.createElement('span');
      span.className = 'plain-word';
      span.textContent = w;
      span.onclick = () => openManualCorrectionPanel(k.klal_id, i, w, null);
      body.appendChild(span);
    }
    body.appendChild(document.createTextNode(' '));
  });
  // A delete-opcode candidate can be filed at word_index == words.length
  // (missing text trails the klal's very last word, e.g. a boundary case
  // at a klal seam) - the forEach above only ever visits i < words.length,
  // so that gap was silently never rendered. Render it after the loop,
  // in the same "before word i" position it would have taken at i ==
  // words.length, i.e. at the end of the body.
  if (gapsBefore[words.length]) gapsBefore[words.length].forEach(c => body.appendChild(makeGapMarker(k.klal_id, c)));
}

// ---------- proposed punctuation markers ----------
function makePunctuationMarker(klalId, p) {
  const span = document.createElement('span');
  const decision = p.current_decision; // {accepted, note} | null
  const state = !decision ? 'pending' : (decision.accepted ? 'accepted' : 'rejected');
  span.className = 'punct-marker punct-' + state;
  span.textContent = '·'; // middle dot
  span.title = state === 'pending'
    ? 'Proposed punctuation - click to review'
    : (state === 'accepted' ? 'Accepted - will become "[.]"' : 'Rejected - click to reconsider');
  span.onclick = () => openPunctuationPanel(klalId, p);
  return span;
}

function makeGapMarker(klalId, corr) {
  const span = document.createElement('span');
  span.className = 'flag-gap';
  span.style.background = STATE_META[wordState(corr)].color;
  attachWordHandlers(span, klalId, corr, true);
  return span;
}

// ---------- quick hover tooltip ----------
function attachWordHandlers(el, klalId, corr, isGap) {
  const [label] = FLAGS[corr.flag] || ['Flagged'];
  el.addEventListener('mouseenter', (e) => {
    const confTxt = (corr.confidence != null) ? (Math.round(corr.confidence * 100) + '% confidence') : 'not scan-verified';
    const hebrewBit = `<bdi>${escapeHtml(corr.docai_reading || (isGap ? '' : '(none)'))}</bdi>`;
    const docaiTxt = isGap
      ? `Scan appears to show: "${hebrewBit}" — not present in current text`
      : `Original OCR reading: "${hebrewBit}"`;
    const bodyTxt = `<span class="t-conf">${escapeHtml(label)} — ${confTxt}${corr.reasoning ? ' — ' + escapeHtml(corr.reasoning) : ''}</span>`;
    const decisionTxt = corr.current_decision
      ? `<span class="t-hint">Your decision: "${escapeHtml(corr.current_decision.chosen_text)}"${corr.current_decision.note ? ' — ' + escapeHtml(corr.current_decision.note) : ''}</span>`
      : `<span class="t-hint">Click for details / to record a decision</span>`;
    tooltip.innerHTML = `<span class="t-flag">${escapeHtml(statusLabel(corr))}</span><span class="t-docai">${docaiTxt}</span>${bodyTxt}${decisionTxt}`;
    tooltip.style.display = 'block';
    positionTooltip(e);
  });
  el.addEventListener('mousemove', positionTooltip);
  el.addEventListener('mouseleave', () => { tooltip.style.display = 'none'; });
  el.addEventListener('click', () => {
    tooltip.style.display = 'none';
    if (corr.page) showPage(corr.page, klalId);
    openCandidatePanel(klalId, corr);
  });
}
function positionTooltip(e) {
  const pad = 16;
  let x = e.clientX + pad, y = e.clientY + pad;
  if (x + 360 > window.innerWidth) x = e.clientX - 360;
  tooltip.style.left = x + 'px';
  tooltip.style.top = y + 'px';
}

// ---------- candidate override panel ----------
const backdrop = document.getElementById('overlay-backdrop');
const candidatePanel = document.getElementById('candidate-panel');
const candidatePanelBody = document.getElementById('candidate-panel-body');
const klalFlagPanel = document.getElementById('klal-flag-panel');
const klalFlagPanelBody = document.getElementById('klal-flag-panel-body');
const punctuationPanel = document.getElementById('punctuation-panel');
const punctuationPanelBody = document.getElementById('punctuation-panel-body');
const witnessPanel = document.getElementById('witness-panel');
const witnessPanelBody = document.getElementById('witness-panel-body');
const manualPanel = document.getElementById('manual-panel');
const manualPanelBody = document.getElementById('manual-panel-body');

function setupPanels() {
  document.getElementById('candidate-panel-close').onclick = closePanels;
  document.getElementById('klal-flag-panel-close').onclick = closePanels;
  document.getElementById('punctuation-panel-close').onclick = closePanels;
  document.getElementById('witness-panel-close').onclick = closePanels;
  document.getElementById('manual-panel-close').onclick = closePanels;
  backdrop.onclick = closePanels;
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closePanels();
  });
}
function closePanels() {
  backdrop.classList.remove('open');
  candidatePanel.classList.remove('open');
  klalFlagPanel.classList.remove('open');
  punctuationPanel.classList.remove('open');
  witnessPanel.classList.remove('open');
  manualPanel.classList.remove('open');
}
function openPanel(panel) {
  closePanels();
  backdrop.classList.add('open');
  panel.classList.add('open');
}

async function openCandidatePanel(klalId, corr) {
  openPanel(candidatePanel);
  candidatePanelBody.innerHTML = '<p>Loading…</p>';

  const k = mountedKlal[klalId] || await fetchKlal(klalId);
  const words = (k.clean_text || '').split(' ');
  const ctxStart = Math.max(0, corr.word_index - 6);
  const ctxEnd = Math.min(words.length, corr.word_index + 7);
  // FIXED 2026-08-14 (same bug class as the witness panel's context
  // highlight, found via user report): a 'replace'/'insert' candidate can
  // span multiple words (build_corrections_dataset.py allows up to
  // MAX_DIFF_SPAN_WORDS, currently 4 - the constant was unnamed and this
  // comment cited a name that didn't exist until 2026-08-14), but this
  // used to bold only the single word AT
  // corr.word_index - the rest of a multi-word disagreement (e.g.
  // final_text "בספר שמות", 2 words) rendered as plain, unhighlighted
  // text. Bold the whole span, using final_text's own word count
  // ('delete'/'manual' are always effectively 1 - word_index there is an
  // insertion anchor point, not a real current-text span).
  const corrSpanLen = (corr.opcode === 'replace' || corr.opcode === 'insert') && corr.final_text
    ? corr.final_text.split(' ').length : 1;
  const corrSpanEnd = Math.min(words.length, corr.word_index + corrSpanLen);
  const ctxWords = [
    escapeHtml(words.slice(ctxStart, corr.word_index).join(' ')),
    `<b>${escapeHtml(words.slice(corr.word_index, corrSpanEnd).join(' '))}</b>`,
    escapeHtml(words.slice(corrSpanEnd, ctxEnd).join(' ')),
  ].filter(Boolean).join(' ');

  const [flagLabel] = FLAGS[corr.flag] || ['Flagged'];
  const flagColor = STATE_META[wordState(corr)].color;

  const options = [];
  if (corr.docai_reading) options.push({ source: 'docai_reading', label: 'DocAI OCR reading', text: corr.docai_reading });
  if (corr.final_text) options.push({ source: 'final_text', label: 'Current stored text', text: corr.final_text });
  if (corr.vision_transcription && corr.vision_transcription !== corr.docai_reading && corr.vision_transcription !== corr.final_text) {
    options.push({ source: 'vision_transcription', label: 'Vision-model reading', text: corr.vision_transcription });
  }
  // 'insert' opcode = stored text has a word/phrase DocAI never saw at all
  // (docai_reading is null by construction) - offer an explicit removal
  // choice rather than relying on the non-obvious "pick custom, leave it
  // blank" convention.
  if (corr.opcode === 'insert') {
    options.push({ source: 'remove', label: 'Remove this text (accept the omission)', text: '(nothing - remove "' + (corr.final_text || '') + '")' });
  } else if (!corr.final_text) {
    // The mirror case: nothing is currently stored here (a gap - DocAI/vision
    // saw a candidate word the corpus never captured) and the correct human
    // call can be "no, nothing belongs here" - e.g. klal 4 word_index 35: the
    // scan token is a footnote-reference digit, not real klal text. Without
    // this, there was no way to record "confirmed omission" at all: the
    // panel offered no blank option, and the custom field rejected an empty
    // answer for any opcode other than 'insert'.
    options.push({ source: 'remove', label: 'Confirm nothing belongs here', text: '(nothing - no insertion needed)' });
  }

  const decision = corr.current_decision;
  const activeSource = decision ? decision.chosen_source : 'final_text';
  const activeText = decision ? decision.chosen_text : corr.final_text;

  let html = `
    <div class="panel-section">
      <div class="panel-label">Status</div>
      <div><i style="background:${flagColor};width:9px;height:9px;border-radius:2px;display:inline-block;margin-inline-end:6px;"></i>${statusLabel(corr)}</div>
      <div style="font-size:12px;color:var(--ink-faint);margin-top:4px;">${escapeHtml(flagLabel)}${corr.confidence != null ? ' · ' + Math.round(corr.confidence * 100) + '% vision confidence' : ''}</div>
    </div>
    <div class="panel-section">
      <div class="panel-label">Context (klal ${klalId})</div>
      <div class="panel-word-context">${ctxWords}</div>
      ${corr.reasoning ? `<div style="font-size:12px;color:var(--ink-faint);margin-top:-8px;">${escapeHtml(corr.reasoning)}</div>` : ''}
    </div>
    <div class="panel-section">
      <div class="panel-label">Choose the correct reading</div>
      <div id="candidate-options"></div>
      <div class="candidate-option" data-source="custom" id="custom-option">
        <input type="radio" name="candidate" ${activeSource === 'custom' ? 'checked' : ''}>
        <div class="co-body">
          <div class="co-label">Custom</div>
          <input type="text" class="custom-text" id="custom-text-input" placeholder="Type the correct reading…" value="${escapeAttr(activeSource === 'custom' ? activeText : '')}">
        </div>
      </div>
    </div>
    <div class="panel-section">
      <div class="panel-label">Note (optional)</div>
      <textarea id="decision-note" rows="3" placeholder="Why? e.g. &quot;crop-confirmed against page 26&quot;">${escapeHtml(decision && decision.note)}</textarea>
    </div>
    <div class="panel-section">
      <button class="panel-btn" id="save-decision-btn">Save decision</button>
      <span class="save-status" id="save-status">Saved ✓</span>
    </div>
    <div class="panel-section">
      <span class="history-toggle" id="history-toggle">Show decision history</span>
      <div class="history-list" id="history-list" style="display:none;"></div>
    </div>
  `;
  candidatePanelBody.innerHTML = html;

  const optionsContainer = document.getElementById('candidate-options');
  options.forEach(opt => {
    const div = document.createElement('div');
    div.className = 'candidate-option' + (activeSource === opt.source ? ' active' : '');
    div.dataset.source = opt.source;
    div.innerHTML = `<input type="radio" name="candidate" ${activeSource === opt.source ? 'checked' : ''}>
      <div class="co-body"><div class="co-label">${escapeHtml(opt.label)}</div><div class="co-text">${escapeHtml(opt.text)}</div></div>`;
    div.onclick = () => selectCandidateOption(opt.source);
    optionsContainer.appendChild(div);
  });
  document.getElementById('custom-option').onclick = () => selectCandidateOption('custom');
  if (activeSource === 'custom') markActiveOption('custom');

  document.getElementById('save-decision-btn').onclick = () => saveCandidateDecision(klalId, corr);
  document.getElementById('history-toggle').onclick = () => toggleHistory(klalId, corr.word_index);
}

function selectCandidateOption(source) {
  markActiveOption(source);
}
function markActiveOption(source) {
  document.querySelectorAll('.candidate-option').forEach(el => {
    const active = el.dataset.source === source;
    el.classList.toggle('active', active);
    const radio = el.querySelector('input[type=radio]');
    if (radio) radio.checked = active;
  });
}

async function saveCandidateDecision(klalId, corr) {
  const activeEl = document.querySelector('.candidate-option.active');
  const source = activeEl ? activeEl.dataset.source : 'final_text';
  let text, chosenSource;
  if (source === 'remove') {
    // 'remove' is a UI-only convenience for insert-opcode candidates; the
    // decision schema itself only knows docai_reading/final_text/
    // vision_transcription/custom, so this is recorded as an explicit
    // empty custom answer.
    text = '';
    chosenSource = 'custom';
  } else if (source === 'custom') {
    text = document.getElementById('custom-text-input').value.trim();
    // Empty is only meaningful (and allowed) when "nothing" is itself a real
    // answer: an 'insert' opcode candidate (stored text has a word docai
    // never saw - blank means "remove it, accept the omission") or a gap
    // with no current final_text (docai/vision saw a candidate word the
    // corpus never captured - blank means "confirm no insertion needed").
    // Otherwise (a normal two-reading dispute, real text on both sides) an
    // empty custom answer isn't a real decision, just an unfilled field.
    if (!text && corr.opcode !== 'insert' && corr.final_text) { alert('Enter the custom reading first.'); return; }
    chosenSource = 'custom';
  } else {
    text = corr[source];
    chosenSource = source;
  }
  const note = document.getElementById('decision-note').value.trim();

  const res = await fetch('/api/decisions/candidate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ klal_id: klalId, word_index: corr.word_index, chosen_source: chosenSource, chosen_text: text, note }),
  });
  if (!res.ok) { alert('Save failed: ' + (await res.text())); return; }

  // Re-fetch this klal fresh from the server instead of patching the
  // cached copy in place - a save is also the moment to pick up any
  // flag/text drift that happened server-side since this klal was first
  // mounted (e.g. a corpus rebuild that ran while this tab stayed open,
  // which otherwise leaves the text pane showing stale flag colors
  // indefinitely - see PROJECT-STATUS.md "stale client cache after a
  // live rebuild", 2026-08-09).
  delete mountedKlal[klalId];
  delete fetchInFlight[klalId];
  const k = await fetchKlal(klalId);
  const block = document.getElementById('klal-block-' + klalId);
  if (block) renderKlalBody(block, k);

  // Also refresh the scan pane's highlighted boxes the same way, if it's
  // currently on screen - otherwise a save only fixes the text pane and
  // the scan pane keeps showing whatever it last fetched.
  if (currentPage != null) await showPage(currentPage, klalId);

  // Keep the nav-pane's open/decided badge counts and the legend's
  // corpus-wide tri-state totals live too, instead of waiting for a
  // reload. FIXED 2026-08-14 (code review, session audit item 5): this
  // used to patch klalById[klalId]'s counts in place with +1/-1
  // arithmetic. That races against setupNavRefreshOnReturn's own
  // visibility-triggered refreshKlalimList(): if that refetch resolves
  // in the window after this save's POST lands server-side but before
  // this arithmetic ran, the arithmetic then applied its delta ON TOP OF
  // already-current counts, double-counting the change. Calling
  // refreshKlalimList() here instead - the same function the visibility
  // refresh uses - means there is only ONE way klalById's counts are
  // ever written: a full re-fetch of server truth. Two fresh re-fetches
  // can still race with each other, but whichever resolves last simply
  // overwrites with its own correct snapshot - nothing ever compounds a
  // delta onto a value it doesn't know is already stale.
  await refreshKlalimList();

  const status = document.getElementById('save-status');
  status.classList.add('show');
  setTimeout(() => status.classList.remove('show'), 2000);
}

async function toggleHistory(klalId, wordIndex) {
  const list = document.getElementById('history-list');
  const toggle = document.getElementById('history-toggle');
  if (list.style.display === 'block') { list.style.display = 'none'; toggle.textContent = 'Show decision history'; return; }
  const history = await fetch(`/api/decisions/${klalId}/${wordIndex}`).then(r => r.json());
  list.innerHTML = history.length
    ? history.slice().reverse().map(h => `
        <div class="history-item">
          <div class="h-ts">${new Date(h.ts).toLocaleString()}</div>
          <div class="h-text">${escapeHtml(h.chosen_text)}</div>
          ${h.note ? `<div class="h-note">${escapeHtml(h.note)}</div>` : ''}
        </div>`).join('')
    : '<p style="color:var(--ink-faint);font-size:12px;">No decisions recorded yet.</p>';
  list.style.display = 'block';
  toggle.textContent = 'Hide decision history';
}

// ---------- klal-level flag panel ----------
async function openKlalFlagPanel(klalId) {
  openPanel(klalFlagPanel);
  klalFlagPanelBody.innerHTML = '<p>Loading…</p>';
  const state = await fetch(`/api/klal/${klalId}/flag`).then(r => r.json());
  // The button/nav badge can be flagged for a reason THIS checkbox doesn't
  // control - an open word-level ai_flag also lights it (see the save
  // handler's stillFlagged fix below) but this panel only ever edits the
  // klal's general note. Surface that explicitly rather than leaving a
  // silent "button says flagged, checkbox unchecked" mismatch (2026-08-17
  // code review).
  const flaggedByWordLevel = !state.needs_revisit
    && klalById[klalId] && klalById[klalId].needs_revisit;

  klalFlagPanelBody.innerHTML = `
    <div class="panel-section">
      <div class="panel-label">Klal ${klalId}</div>
      <div class="checkbox-row">
        <input type="checkbox" id="needs-revisit-checkbox" ${state.needs_revisit ? 'checked' : ''}>
        <label for="needs-revisit-checkbox">Needs revisit</label>
      </div>
      ${flaggedByWordLevel ? `<div style="font-size:12px;color:var(--ink-faint);margin-top:6px;">
        This klal shows as flagged because of an open AI-flagged word in the text, not this note -
        that's tracked separately and won't change if you save here unchecked.</div>` : ''}
    </div>
    <div class="panel-section">
      <div class="panel-label">Note</div>
      <textarea id="klal-flag-note" rows="4" placeholder="What needs a second look, and why?">${escapeHtml(state.note)}</textarea>
    </div>
    <div class="panel-section">
      <button class="panel-btn" id="save-klal-flag-btn">Save</button>
      <span class="save-status" id="klal-flag-save-status">Saved ✓</span>
    </div>
    <div class="panel-section">
      <span class="history-toggle" id="klal-flag-history-toggle">Show history</span>
      <div class="history-list" id="klal-flag-history-list" style="display:none;"></div>
    </div>
  `;

  document.getElementById('save-klal-flag-btn').onclick = async () => {
    const needsRevisit = document.getElementById('needs-revisit-checkbox').checked;
    const note = document.getElementById('klal-flag-note').value.trim();
    const res = await fetch('/api/decisions/klal_flag', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ klal_id: klalId, needs_revisit: needsRevisit, note }),
    });
    if (!res.ok) { alert('Save failed: ' + (await res.text())); return; }
    // FIXED 2026-08-14 (code review, session audit item 5): direct
    // assignment here raced against setupNavRefreshOnReturn's
    // refreshKlalimList() the same way the count arithmetic elsewhere
    // did - a refetch in flight before this POST landed could resolve
    // afterward and overwrite this assignment with the stale value.
    // refreshKlalimList() re-fetches server truth (which already
    // reflects this save, since it POSTed first) instead.
    await refreshKlalimList();
    // FIXED 2026-08-17 (code review): this used to set the button from the
    // local `needsRevisit` checkbox value directly - correct only for the
    // GENERAL note this panel edits, not for the klal's overall flagged
    // state. rd.flagged_klalim() (which drives the nav badge and this
    // button's state everywhere else, via klalById[].needs_revisit) also
    // lights up on an open WORD-LEVEL ai_flag - so saving this panel with
    // the checkbox left unchecked, on a klal that still had an open
    // word-level flag, silently un-flagged the button while the word
    // itself stayed highlighted. refreshKlalimList() just fetched server
    // truth reflecting both; read the button state from there instead.
    const block = document.getElementById('klal-block-' + klalId);
    const btn = block && block.querySelector('.klal-flag-btn');
    const stillFlagged = klalById[klalId] ? klalById[klalId].needs_revisit : needsRevisit;
    if (btn) { btn.classList.toggle('active', stillFlagged); btn.textContent = stillFlagged ? '⚑ flagged' : '⚑ flag'; }
    const status = document.getElementById('klal-flag-save-status');
    status.classList.add('show');
    setTimeout(() => status.classList.remove('show'), 2000);
  };

  document.getElementById('klal-flag-history-toggle').onclick = async () => {
    const list = document.getElementById('klal-flag-history-list');
    const toggle = document.getElementById('klal-flag-history-toggle');
    if (list.style.display === 'block') { list.style.display = 'none'; toggle.textContent = 'Show history'; return; }
    list.innerHTML = state.history.length
      ? state.history.slice().reverse().map(h => `
          <div class="history-item">
            <div class="h-ts">${new Date(h.ts).toLocaleString()} — ${h.needs_revisit ? 'flagged' : 'unflagged'}</div>
            ${h.note ? `<div class="h-note">${escapeHtml(h.note)}</div>` : ''}
          </div>`).join('')
      : '<p style="color:var(--ink-faint);font-size:12px;">No history yet.</p>';
    list.style.display = 'block';
    toggle.textContent = 'Hide history';
  };
}

// ---------- manual word correction (2026-08-13: "add feature for reviewer
// to flag any word and replace it" - not just words the machine pipeline
// already flagged). Reuses the same append-only decisions log and the same
// two-step decide-then-apply-reviewer-decisions.py separation as every
// other decision type; see apply_manual_correction() there for how it
// reaches part1.json. ----------
async function saveManualDecision(klalId, wordIndex, word, chosenText, note) {
  const res = await fetch('/api/decisions/manual', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ klal_id: klalId, word_index: wordIndex, original_word: word, chosen_text: chosenText, note }),
  });
  if (!res.ok) { alert('Save failed: ' + (await res.text())); return null; }

  delete mountedKlal[klalId];
  delete fetchInFlight[klalId];
  const freshK = await fetchKlal(klalId);
  const block = document.getElementById('klal-block-' + klalId);
  if (block) renderKlalBody(block, freshK);
  if (currentPage != null) await showPage(currentPage, scanFocusKlalId);

  // FIXED 2026-08-14 (code review, session audit item 5): this used to
  // patch klalById[klalId]'s correction_count/decided_count in place,
  // guarded by a wasAlreadyDecided flag the caller passed in - the same
  // race as saveCandidateDecision above (a concurrent visibility-
  // triggered refreshKlalimList() could resolve between this POST and
  // the arithmetic, causing a double-count). Delegating to
  // refreshKlalimList() removes the need for the guard entirely: editing
  // an already-decided word or deciding a fresh one both just re-fetch
  // the server's own count, which is correct either way - the
  // wasAlreadyDecided parameter is gone accordingly, see call sites.
  await refreshKlalimList();
  // Return the fresh synthetic 'manual' entry so the caller can re-render
  // the panel itself against the just-saved state (not just the text
  // pane) - without this, a successful delete left the "Click again to
  // confirm delete" button text sitting there as if nothing had happened,
  // and a second click would silently record a redundant decision.
  return freshK.corrections.find(c => c.word_index === wordIndex && c.opcode === 'manual') || null;
}

async function openManualCorrectionPanel(klalId, wordIndex, word, existing) {
  openPanel(manualPanel);
  manualPanelBody.innerHTML = '<p>Loading…</p>';

  const k = mountedKlal[klalId] || await fetchKlal(klalId);
  const words = (k.clean_text || '').split(' ');
  const ctxStart = Math.max(0, wordIndex - 8);
  const ctxEnd = Math.min(words.length, wordIndex + 9);
  const ctxWords = words.slice(ctxStart, ctxEnd).map((w, idx) =>
    (ctxStart + idx === wordIndex) ? `<b>[${escapeHtml(w)}]</b>` : escapeHtml(w)
  ).join(' ');

  // FIXED 2026-08-17 (code review, follow-up to bug #1's ai_flag routing):
  // an ai_flag's current_decision is a klal_flag record, which carries no
  // chosen_text (chosen_source/chosen_text are candidate_choice/manual_
  // correction fields, always null on klal_flag) - treating it like a real
  // manual correction pre-filled the text input with `null` and labeled an
  // un-actioned AI flag "Correction on record" as if a reviewer had already
  // proposed something. An ai_flag is a machine-raised concern awaiting a
  // reviewer's first look, not a correction on record.
  const isAiFlag = existing && existing.opcode === 'ai_flag';
  const markedForDeletion = !isAiFlag && existing && existing.current_decision.chosen_text === '';
  const currentText = existing && !isAiFlag && !markedForDeletion ? existing.current_decision.chosen_text : '';
  const currentNote = existing && existing.current_decision.note ? existing.current_decision.note : '';

  manualPanelBody.innerHTML = `
    <div class="panel-section">
      <div class="panel-label">Klal ${klalId}, word ${wordIndex}</div>
      <div class="panel-word-context">${ctxWords}</div>
    </div>
    ${isAiFlag ? `
    <div class="panel-section">
      <div class="panel-label">AI-flagged word</div>
      <div style="font-size:12px;color:var(--ink-faint);">Raised by an automated pass, not yet reviewed
      by a human. Propose a correction below, or leave it and record your own note.</div>
    </div>` : ''}
    ${markedForDeletion ? `
    <div class="panel-section">
      <div class="panel-label">Marked for deletion</div>
      <div style="font-size:12px;color:var(--ink-faint);">Not yet removed from the corpus - recording
      a decision and applying it to part1.json are always separate steps. Save a replacement below to
      change your mind, or use Delete again to reconfirm.</div>
    </div>` : ''}
    <div class="panel-section">
      <div class="panel-label">${existing && !isAiFlag ? 'Correction on record' : 'Propose a correction'}</div>
      <input type="text" class="custom-text" id="manual-correction-text"
             placeholder="Correct reading…" value="${escapeAttr(currentText)}">
    </div>
    <div class="panel-section">
      <div class="panel-label">Note (optional)</div>
      <textarea id="manual-correction-note" rows="3" placeholder="Why? e.g. &quot;scan confirms X, not Y&quot;">${escapeHtml(currentNote)}</textarea>
    </div>
    <div class="panel-section">
      <button class="panel-btn" id="save-manual-correction-btn">Save correction</button>
      ${isAiFlag ? `<button class="panel-btn secondary" id="accept-current-text-btn">Accept current text</button>` : ''}
      <button class="panel-btn secondary" id="delete-manual-word-btn">Delete this word</button>
    </div>
    ${existing ? `
    <div class="panel-section">
      <span class="history-toggle" id="manual-correction-history-toggle">Show decision history</span>
      <div class="history-list" id="manual-correction-history-list" style="display:none;"></div>
    </div>` : ''}
  `;

  // No separate "Saved" flash here (unlike every other panel in this
  // app) - both actions below re-open this same panel against the fresh
  // post-save state on success, and that refreshed content (the new
  // "Correction on record" text, or "Marked for deletion") IS the
  // confirmation; a flash immediately clobbered by that re-render would
  // never actually be seen.
  document.getElementById('save-manual-correction-btn').onclick = async () => {
    const text = document.getElementById('manual-correction-text').value.trim();
    if (!text) { alert('Enter the corrected reading first (or use Delete this word instead).'); return; }
    const note = document.getElementById('manual-correction-note').value.trim();
    const freshCorr = await saveManualDecision(klalId, wordIndex, word, text, note);
    if (freshCorr) openManualCorrectionPanel(klalId, wordIndex, word, freshCorr);
  };

  // "Accept current text" — dismisses an AI flag without a text change.
  // Records a manual_correction with chosen_text == the current word (a
  // deliberate no-op: the reviewer looked at it, the text is correct as-is).
  // apply_reviewer_decisions.py handles this correctly: replace word with
  // itself, net change to part1.json is zero, apply_event is recorded.
  if (isAiFlag) {
    document.getElementById('accept-current-text-btn').onclick = async () => {
      const note = document.getElementById('manual-correction-note').value.trim();
      const freshCorr = await saveManualDecision(klalId, wordIndex, word, word,
        note || 'AI flag reviewed — current text confirmed');
      if (freshCorr) openManualCorrectionPanel(klalId, wordIndex, word, freshCorr);
    };
  }

  // Arm-then-confirm in the panel itself rather than a native confirm()
  // dialog - consistent with the rest of this app (no other action here
  // uses a browser-native dialog) and avoids the well-known problem of
  // native dialogs blocking further automated/scripted interaction with
  // the page entirely once triggered.
  let deleteArmed = false;
  const deleteBtn = document.getElementById('delete-manual-word-btn');
  deleteBtn.onclick = async () => {
    if (!deleteArmed) {
      deleteArmed = true;
      deleteBtn.textContent = 'Click again to confirm delete';
      deleteBtn.classList.add('armed');
      setTimeout(() => {
        if (!deleteArmed) return;  // already resolved (clicked through or panel reused)
        deleteArmed = false;
        deleteBtn.textContent = 'Delete this word';
        deleteBtn.classList.remove('armed');
      }, 4000);
      return;
    }
    deleteArmed = false;
    const note = document.getElementById('manual-correction-note').value.trim();
    const freshCorr = await saveManualDecision(klalId, wordIndex, word, '', note);
    if (freshCorr) openManualCorrectionPanel(klalId, wordIndex, word, freshCorr);
  };

  if (existing) {
    document.getElementById('manual-correction-history-toggle').onclick = async () => {
      const list = document.getElementById('manual-correction-history-list');
      const toggle = document.getElementById('manual-correction-history-toggle');
      if (list.style.display === 'block') { list.style.display = 'none'; toggle.textContent = 'Show decision history'; return; }
      const history = await fetch(`/api/decisions/${klalId}/${wordIndex}`).then(r => r.json());
      list.innerHTML = history.length
        ? history.slice().reverse().map(h => `
            <div class="history-item">
              <div class="h-ts">${new Date(h.ts).toLocaleString()}</div>
              <div class="h-text">${escapeHtml(h.chosen_text)}</div>
              ${h.note ? `<div class="h-note">${escapeHtml(h.note)}</div>` : ''}
            </div>`).join('')
        : '<p style="color:var(--ink-faint);font-size:12px;">No decisions recorded yet.</p>';
      list.style.display = 'block';
      toggle.textContent = 'Hide decision history';
    };
  }
}

// ---------- proposed-punctuation review panel ----------
async function openPunctuationPanel(klalId, p) {
  openPanel(punctuationPanel);
  punctuationPanelBody.innerHTML = '<p>Loading…</p>';

  const k = mountedKlal[klalId] || await fetchKlal(klalId);
  const words = (k.clean_text || '').split(' ');
  const idx = p.before_word_index;
  const ctxStart = Math.max(0, idx - 10);
  const ctxEnd = Math.min(words.length, idx + 10);
  const ctxWords = words.slice(ctxStart, ctxEnd).map((w, i) =>
    (ctxStart + i === idx) ? `<b>[.]</b> ${escapeHtml(w)}` : escapeHtml(w)
  ).join(' ');

  const decision = p.current_decision;
  const activeChoice = decision ? (decision.accepted ? 'accept' : 'reject') : null;

  punctuationPanelBody.innerHTML = `
    <div class="panel-section">
      <div class="panel-label">Proposed break (klal ${klalId})</div>
      <div class="panel-word-context">${ctxWords}</div>
      ${p.reasoning ? `<div style="font-size:12px;color:var(--ink-faint);margin-top:-8px;">${escapeHtml(p.reasoning)}</div>` : ''}
    </div>
    <div class="panel-section">
      <div class="panel-label">Decision</div>
      <div class="candidate-option${activeChoice === 'accept' ? ' active' : ''}" data-choice="accept" id="punct-accept-option">
        <input type="radio" name="punct-choice" ${activeChoice === 'accept' ? 'checked' : ''}>
        <div class="co-body"><div class="co-label">Accept</div><div class="co-text">Insert "[.]" here</div></div>
      </div>
      <div class="candidate-option${activeChoice === 'reject' ? ' active' : ''}" data-choice="reject" id="punct-reject-option">
        <input type="radio" name="punct-choice" ${activeChoice === 'reject' ? 'checked' : ''}>
        <div class="co-body"><div class="co-label">Reject</div><div class="co-text">Leave the text as-is here</div></div>
      </div>
    </div>
    <div class="panel-section">
      <div class="panel-label">Note (optional)</div>
      <textarea id="punct-decision-note" rows="3" placeholder="Why? e.g. &quot;not a real clause break&quot;">${escapeHtml(decision && decision.note)}</textarea>
    </div>
    <div class="panel-section">
      <button class="panel-btn" id="save-punct-decision-btn">Save decision</button>
      <span class="save-status" id="punct-save-status">Saved ✓</span>
    </div>
  `;

  const markChoice = (choice) => {
    document.getElementById('punct-accept-option').classList.toggle('active', choice === 'accept');
    document.getElementById('punct-reject-option').classList.toggle('active', choice === 'reject');
    document.getElementById('punct-accept-option').querySelector('input').checked = choice === 'accept';
    document.getElementById('punct-reject-option').querySelector('input').checked = choice === 'reject';
  };
  document.getElementById('punct-accept-option').onclick = () => markChoice('accept');
  document.getElementById('punct-reject-option').onclick = () => markChoice('reject');

  document.getElementById('save-punct-decision-btn').onclick = async () => {
    const activeEl = document.querySelector('#punct-accept-option.active, #punct-reject-option.active');
    if (!activeEl) { alert('Choose Accept or Reject first.'); return; }
    const accepted = activeEl.dataset.choice === 'accept';
    const note = document.getElementById('punct-decision-note').value.trim();

    const res = await fetch('/api/decisions/punctuation', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ klal_id: klalId, before_word_index: idx, accepted, note }),
    });
    if (!res.ok) { alert('Save failed: ' + (await res.text())); return; }

    delete mountedKlal[klalId];
    delete fetchInFlight[klalId];
    const freshK = await fetchKlal(klalId);
    const block = document.getElementById('klal-block-' + klalId);
    if (block) renderKlalBody(block, freshK);

    // FIXED 2026-08-14 (code review, session audit item 5): same race as
    // saveCandidateDecision's badge arithmetic above - refreshKlalimList()
    // replaces the in-place +1/-1 patch.
    await refreshKlalimList();

    const status = document.getElementById('punct-save-status');
    status.classList.add('show');
    setTimeout(() => status.classList.remove('show'), 2000);
  };
}

// ---------- witness disagreement panel (independent Tesseract-vs-DocAI
// readings for the reconstructed continuation pages - see
// reconstruction_witness_queue.json / PROJECT-STATUS.md session handoff
// 2026-08-11). Indexed by docai_token_index, a different space from
// corrections' word_index - the two never collide since the server keys
// decisions by decision_type ("witness_choice" vs "candidate_choice"). ----------
async function openWitnessPanel(w) {
  openPanel(witnessPanel);
  witnessPanelBody.innerHTML = '<p>Loading…</p>';

  const decision = w.current_decision;
  const activeSource = decision ? decision.chosen_source : null;

  const options = [
    { source: 'docai_reading', label: 'DocAI OCR reading', text: w.docai_reading },
    { source: 'tesseract_reading', label: 'Tesseract OCR reading', text: w.tesseract_reading },
    { source: 'unreadable', label: 'Unreadable / neither is right', text: '(mark as unreadable)' },
  ].filter(opt => opt.text);

  // Raw DocAI text surrounding this item, not just the isolated crop image -
  // per user feedback 2026-08-12: an image crop with no surrounding text is
  // hard to place in context. Deliberately labeled as raw/unverified OCR,
  // not the not-yet-applied reconstruction draft - see review_server.py
  // api_witness_context()'s docstring for why.
  const ctx = await fetch(`/api/witness/context/${w.page}/${w.docai_token_index}`).then(r => r.json());
  // FIXED 2026-08-14 (user report: clicked a witness box on the scan pane,
  // saw "...וזו היא [שיטת] התוס ג"כ..." - only the FIRST word of a
  // multi-word disagreement was bracketed, even though docai_reading was
  // the full two-word span "שיטת התוס"). This used to bracket exactly one
  // word at ctx.target_index regardless of how many words the actual
  // disagreement spans (opcode/MAX_SPAN in verify_reconstruction_
  // witness.py allow up to 4) - bracket the whole span instead, using the
  // word count already available in docai_reading.
  let ctxHtml;
  if (ctx.words.length) {
    const spanLen = w.docai_reading ? w.docai_reading.split(' ').length : 1;
    const ti = ctx.target_index;
    const tEnd = Math.min(ctx.words.length, ti + spanLen);
    const before = escapeHtml(ctx.words.slice(0, ti).join(' '));
    const target = escapeHtml(ctx.words.slice(ti, tEnd).join(' '));
    const after = escapeHtml(ctx.words.slice(tEnd).join(' '));
    ctxHtml = [before, `<b>[${target}]</b>`, after].filter(Boolean).join(' ');
  } else {
    ctxHtml = '<span style="color:var(--ink-faint);">no context available</span>';
  }

  witnessPanelBody.innerHTML = `
    <div class="panel-section">
      <div class="panel-label">Klal ${w.klal_id} · tier ${w.tier} · page ${w.page}</div>
      <div style="font-size:12px;color:var(--ink-faint);">Two OCR engines disagree here and both readings are real Hebrew
      words, so a word-lexicon check can't tell them apart - this needs the ink.</div>
    </div>
    <div class="panel-section">
      <div class="panel-label">Raw OCR context (page ${w.page}, unverified - furniture/misreads possible)</div>
      <div class="panel-word-context">${ctxHtml}</div>
    </div>
    <div class="panel-section">
      <div class="panel-label">Choose the correct reading</div>
      <div id="witness-options"></div>
      <div class="candidate-option" data-source="custom" id="witness-custom-option">
        <input type="radio" name="witness-candidate" ${activeSource === 'custom' ? 'checked' : ''}>
        <div class="co-body">
          <div class="co-label">Custom</div>
          <input type="text" class="custom-text" id="witness-custom-text" placeholder="Type the correct reading…" value="${escapeAttr(activeSource === 'custom' ? decision.chosen_text : '')}">
        </div>
      </div>
    </div>
    <div class="panel-section">
      <div class="panel-label">Note (optional)</div>
      <textarea id="witness-decision-note" rows="3" placeholder="Why? e.g. &quot;crop-confirmed against page 26&quot;">${escapeHtml(decision && decision.note)}</textarea>
    </div>
    <div class="panel-section">
      <button class="panel-btn" id="save-witness-decision-btn">Save decision</button>
      <span class="save-status" id="witness-save-status">Saved ✓</span>
    </div>
  `;

  const optionsContainer = document.getElementById('witness-options');
  options.forEach(opt => {
    const div = document.createElement('div');
    div.className = 'candidate-option' + (activeSource === opt.source ? ' active' : '');
    div.dataset.source = opt.source;
    div.innerHTML = `<input type="radio" name="witness-candidate" ${activeSource === opt.source ? 'checked' : ''}>
      <div class="co-body"><div class="co-label">${escapeHtml(opt.label)}</div><div class="co-text">${escapeHtml(opt.text)}</div></div>`;
    div.onclick = () => markActiveWitnessOption(opt.source);
    optionsContainer.appendChild(div);
  });
  document.getElementById('witness-custom-option').onclick = () => markActiveWitnessOption('custom');
  if (activeSource) markActiveWitnessOption(activeSource);

  document.getElementById('save-witness-decision-btn').onclick = () => saveWitnessDecision(w);
}

function markActiveWitnessOption(source) {
  document.querySelectorAll('#witness-panel-body .candidate-option').forEach(el => {
    const active = el.dataset.source === source;
    el.classList.toggle('active', active);
    const radio = el.querySelector('input[type=radio]');
    if (radio) radio.checked = active;
  });
}

async function saveWitnessDecision(w) {
  const activeEl = document.querySelector('#witness-panel-body .candidate-option.active');
  if (!activeEl) { alert('Choose a reading first.'); return; }
  const source = activeEl.dataset.source;
  let text;
  if (source === 'custom') {
    text = document.getElementById('witness-custom-text').value.trim();
    if (!text) { alert('Enter the custom reading first.'); return; }
  } else if (source === 'unreadable') {
    text = '';
  } else {
    text = w[source];
  }
  const note = document.getElementById('witness-decision-note').value.trim();

  const res = await fetch('/api/decisions/witness', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      klal_id: w.klal_id, docai_token_index: w.docai_token_index,
      chosen_source: source, chosen_text: text, note,
    }),
  });
  if (!res.ok) { alert('Save failed: ' + (await res.text())); return; }

  // Refresh the witness page summary (decided counts) and redraw this
  // page's boxes so the saved item's box state updates immediately.
  WITNESS_PAGES = (await fetch('/api/witness').then(r => r.json())).pages || [];
  if (currentPage != null) await showPage(currentPage, scanFocusKlalId);

  // Keep the nav-pane badge and legend live too, same as
  // saveCandidateDecision does - witness items fold into the same
  // server-side tri-state counters (api_klalim), but this save path never
  // updated the client's cached copy of them, so the nav badge and legend
  // stayed stale until a full reload (2026-08-12, PROJECT-STATUS.md
  // finding 6). FIXED 2026-08-14 (code review, session audit item 5):
  // that fix itself used the same in-place +1/-1 arithmetic pattern that
  // races against setupNavRefreshOnReturn's refreshKlalimList() elsewhere
  // in this file - replaced with the same refreshKlalimList() call.
  await refreshKlalimList();

  const status = document.getElementById('witness-save-status');
  status.classList.add('show');
  setTimeout(() => status.classList.remove('show'), 2000);
}

// ---------- scan pane ----------
let currentPage = null;
let scanFocusKlalId = null; // which klal's region/continuation to highlight, independent of which page is shown
const pageImg = document.getElementById('page-img');
const hlContainer = document.getElementById('hl-container');
const pageIndicator = document.getElementById('page-indicator');
const klalIndicator = document.getElementById('klal-indicator');
const scanViewer = document.getElementById('scan-viewer');

let zoomLevel = 1;
function applyZoom(anchorRatioX, anchorRatioY) {
  const rX = anchorRatioX != null ? anchorRatioX
    : (scanViewer.scrollLeft + scanViewer.clientWidth / 2) / (pageImg.offsetWidth || 1);
  const rY = anchorRatioY != null ? anchorRatioY
    : (scanViewer.scrollTop + scanViewer.clientHeight / 2) / (pageImg.offsetHeight || 1);
  const fitWidth = scanViewer.clientWidth - 32;
  pageImg.style.width = Math.round(fitWidth * zoomLevel) + 'px';
  document.getElementById('zoom-level').textContent = Math.round(zoomLevel * 100) + '%';
  requestAnimationFrame(() => {
    scanViewer.scrollLeft = rX * pageImg.offsetWidth - scanViewer.clientWidth / 2;
    scanViewer.scrollTop = rY * pageImg.offsetHeight - scanViewer.clientHeight / 2;
  });
}
function setupZoomPan() {
  document.getElementById('zoom-in').onclick = () => { zoomLevel = Math.min(3, zoomLevel + 0.25); applyZoom(); };
  document.getElementById('zoom-out').onclick = () => { zoomLevel = Math.max(0.3, zoomLevel - 0.25); applyZoom(); };
  pageImg.addEventListener('load', () => applyZoom(0.5, 0));

  let panning = false, panStartX = 0, panStartY = 0, panScrollLeft = 0, panScrollTop = 0;
  scanViewer.addEventListener('mousedown', (e) => {
    panning = true;
    scanViewer.classList.add('panning');
    panStartX = e.clientX; panStartY = e.clientY;
    panScrollLeft = scanViewer.scrollLeft; panScrollTop = scanViewer.scrollTop;
    e.preventDefault();
  });
  window.addEventListener('mousemove', (e) => {
    if (!panning) return;
    scanViewer.scrollLeft = panScrollLeft - (e.clientX - panStartX);
    scanViewer.scrollTop = panScrollTop - (e.clientY - panStartY);
  });
  window.addEventListener('mouseup', () => { panning = false; scanViewer.classList.remove('panning'); });

  document.getElementById('page-nav-prev').onclick = () => goToPageOffset(-1);
  document.getElementById('page-nav-next').onclick = () => goToPageOffset(1);
}

async function showPage(page, focusKlalId) {
  if (page !== currentPage) {
    currentPage = page;
    pageImg.src = `/images/pdf_pages/page_${page}.png`;
    pageIndicator.textContent = 'Page ' + page;
  }
  scanFocusKlalId = focusKlalId;
  updatePageNavButtons();
  hlContainer.innerHTML = '';

  const focusKlal = mountedKlal[focusKlalId] || (await fetchKlal(focusKlalId).catch(() => null));
  // A klal's highlight region can be on its own starting page (`region`)
  // or, if it continues past a page boundary, on a later page it also
  // touches (`continuations`) - e.g. klal 4 starts on the last line of
  // page 15 but most of it is on page 16. Use whichever matches the page
  // actually being shown, so manually flipping pages (see
  // goToPageOffset) still highlights the right region instead of showing
  // nothing once you've moved off the klal's start page.
  let r = null;
  if (focusKlal) {
    if (focusKlal.page === page) r = focusKlal.region;
    else r = (focusKlal.continuations || []).find(c => c.page === page)?.bbox;
  }
  if (r) {
    const box = document.createElement('div');
    box.className = 'hl-current-klal';
    box.style.left = (r.x1 * 100) + '%';
    box.style.top = (r.y1 * 100) + '%';
    box.style.width = ((r.x2 - r.x1) * 100) + '%';
    box.style.height = ((r.y2 - r.y1) * 100) + '%';
    hlContainer.appendChild(box);
  }

  const pageItems = await fetch('/api/page/' + page).then(r => r.json());
  pageItems.forEach(c => {
    if (!c.bbox) return;
    if (c.kind === 'witness') {
      // Same tri-state treatment as every other flagged word (2026-08-12,
      // user request: "put the witness flags in as machine-disputed same
      // as the others") - no separate purple category. A witness item has
      // no machine-resolved state (nothing auto-resolves it): it's either
      // an open dispute or a human decision.
      const box = document.createElement('div');
      const state = c.current_decision ? 'human' : 'open';
      box.className = 'hl-box hl-state-' + state + (c.klal_id === focusKlalId ? '' : ' dim');
      const color = STATE_META[state].color;
      box.style.setProperty('--hl-color', color);
      box.style.background = color + '33';
      box.style.left = (c.bbox.x1 * 100) + '%';
      box.style.top = (c.bbox.y1 * 100) + '%';
      box.style.width = ((c.bbox.x2 - c.bbox.x1) * 100) + '%';
      box.style.height = ((c.bbox.y2 - c.bbox.y1) * 100) + '%';
      box.title = c.current_decision
        ? `${STATE_META.human.label}: "${c.current_decision.chosen_text || ''}"`
        : `${STATE_META.open.label} (tier ${c.tier}) - click to decide`;
      box.addEventListener('click', () => openWitnessPanel(c));
      hlContainer.appendChild(box);
      return;
    }
    const box = document.createElement('div');
    const state = wordState(c);
    box.className = 'hl-box hl-state-' + state + (c.klal_id === focusKlalId ? '' : ' dim');
    const color = STATE_META[state].color;
    box.style.setProperty('--hl-color', color);
    box.style.background = color + '33';
    box.style.left = (c.bbox.x1 * 100) + '%';
    box.style.top = (c.bbox.y1 * 100) + '%';
    box.style.width = ((c.bbox.x2 - c.bbox.x1) * 100) + '%';
    box.style.height = ((c.bbox.y2 - c.bbox.y1) * 100) + '%';
    attachWordHandlers(box, c.klal_id, c);
    hlContainer.appendChild(box);
  });
}

// Witness-queue pages (24/37/40) are continuation-only - no klal marker of
// their own - so they're absent from every klal's own `page` field and the
// stepper would otherwise skip straight over them, leaving the witness
// queue unreachable. Merged in here so both nav buttons and goToPageOffset
// treat them as normal stops.
const pagesWithKlalim = () => Array.from(new Set([
  ...KLALIM.filter(k => k.page).map(k => k.page),
  ...WITNESS_PAGES.map(w => w.page),
])).sort((a, b) => a - b);

function updatePageNavButtons() {
  const pages = pagesWithKlalim();
  const idx = pages.indexOf(currentPage);
  document.getElementById('page-nav-prev').disabled = idx <= 0;
  document.getElementById('page-nav-next').disabled = idx === -1 || idx >= pages.length - 1;
}
function goToPageOffset(offset) {
  // Deliberately does NOT jump the middle text pane to a different klal -
  // this only flips which scan image is shown, so a reviewer can manually
  // browse to the next/previous physical page for context (e.g. to see
  // the rest of a klal that continues past a page boundary) while staying
  // put in the text they're reading. showPage() itself still tries to
  // highlight scanFocusKlalId's region on whatever page this lands on,
  // via its `continuations` list if the klal touches this page too.
  const pages = pagesWithKlalim();
  const idx = pages.indexOf(currentPage);
  if (idx === -1) return;
  const targetPage = pages[idx + offset];
  if (targetPage == null) return;
  showPage(targetPage, scanFocusKlalId);
}

// ---------- nav / scroll sync ----------
let suppressObserverScroll = false;
let suppressTimer = null;
let lastActiveKlalId = null;

function jumpTo(klalId) {
  const block = document.getElementById('klal-block-' + klalId);
  if (!block) return;
  suppressObserverScroll = true;
  lastActiveKlalId = klalId;
  setActiveKlal(klalId);
  mountKlal(klalId);
  block.scrollIntoView({ behavior: 'smooth', block: 'start' });
  clearTimeout(suppressTimer);
  suppressTimer = setTimeout(() => { suppressObserverScroll = false; }, 700);
}

function setActiveKlal(klalId) {
  document.querySelectorAll('.nav-item.active').forEach(el => el.classList.remove('active'));
  const navEl = document.getElementById('nav-' + klalId);
  if (navEl) {
    navEl.classList.add('active');
    // Scrolling the middle text pane only toggled this class before - the
    // nav pane's own scroll position never followed, so the highlighted
    // row silently scrolled out of view as you read through the corpus.
    // 'nearest' is a no-op when the row is already visible (e.g. right
    // after a click in jumpTo()), so this only moves the nav pane when it
    // actually needs to. behavior:'auto' (not 'smooth') deliberately -
    // this fires continuously as a background reaction to text-pane
    // scrolling, and confirmed via testing that 'smooth' can silently
    // never complete (rAF-driven smooth-scroll gets throttled when the
    // tab isn't in the foreground), leaving the nav pane stuck instead of
    // just less animated.
    navEl.scrollIntoView({ block: 'nearest', behavior: 'auto' });
  }
  const k = klalById[klalId];
  if (k) {
    klalIndicator.textContent = 'כלל ' + klalId;
    if (k.page) showPage(k.page, klalId);
  }
}

function updateActiveFromScroll() {
  const allBlocks = Array.from(document.querySelectorAll('.klal-block'));
  const containerTop = textScroll.getBoundingClientRect().top;
  const line = containerTop + 48;
  let current = allBlocks[0];
  for (const block of allBlocks) {
    if (block.getBoundingClientRect().top <= line) current = block;
    else break;
  }
  const klalId = parseInt(current.dataset.klalId);
  if (klalId !== lastActiveKlalId) {
    lastActiveKlalId = klalId;
    setActiveKlal(klalId);
  }
}

let scrollScheduled = false;
textScroll.addEventListener('scroll', () => {
  if (suppressObserverScroll || scrollScheduled) return;
  scrollScheduled = true;
  requestAnimationFrame(() => { scrollScheduled = false; updateActiveFromScroll(); });
});

init();
