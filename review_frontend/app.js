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

function extractSuggestedWord(reasoning) {
  if (!reasoning) return null;
  if (typeof reasoning === 'object') {
    reasoning = reasoning.reasoning || (reasoning.current_decision && reasoning.current_decision.note) || reasoning.note;
  }
  if (!reasoning || typeof reasoning !== 'string') return null;

  // 1. Arrow pattern: e.g. "בססחים w30 → בפסחים" or "ידן -> ידו"
  const mArrow = reasoning.match(/(?:→|->)\s*['"״׳]?([^\s|'"״׳]+)/);
  if (mArrow) return mArrow[1].trim();

  // 2. Prose patterns
  const m1 = reasoning.match(/away from ['"]([^'"]+)['"]/i);
  if (m1) return m1[1].trim();
  const m2 = reasoning.match(/suggests? ['"]([^'"]+)['"]/i);
  if (m2) return m2[1].trim();
  const m3 = reasoning.match(/['"]([^'"]+)['"]\s*\(\d+x independently attested\)/i);
  if (m3) return m3[1].trim();
  const m4 = reasoning.match(/replaces? (?:with )?['"]([^'"]+)['"]/i);
  if (m4) return m4[1].trim();
  return null;
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
  // Witness items: human decision wins first, then vision-selected A/B ->
  // machine-resolved; NEITHER or absent -> open.
  if (corr.opcode === 'witness') {
    if (corr.current_decision) return 'human';
    return (corr.vision_selected === 'A' || corr.vision_selected === 'B') ? 'machine' : 'open';
  }
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

let currentPart = '1';

function setupPartSelect() {
  const select = document.getElementById('part-select');
  if (!select) return;
  select.onchange = async () => {
    await switchPart(select.value);
  };
}

async function switchPart(partVal) {
  currentPart = partVal;
  const [flags, klalim, witness] = await Promise.all([
    fetch('/api/flags').then(r => r.json()),
    fetch('/api/klalim?part=' + currentPart).then(r => r.json()),
    fetch('/api/witness').then(r => r.json()),
  ]);
  FLAGS = flags;
  KLALIM = klalim;
  klalById = Object.fromEntries(klalim.map(k => [k.klal_id, k]));
  WITNESS_PAGES = witness.pages || [];

  textScroll.innerHTML = '';
  mountedKlal = {};
  fetchInFlight = {};

  buildLegend();
  buildNav();
  buildPlaceholders();
  setupObserver();
  applyFlaggedFilter();

  if (KLALIM.length > 0) {
    lastActiveKlalId = KLALIM[0].klal_id;
    setActiveKlal(lastActiveKlalId);
  }
}

async function init() {
  const [flags, klalim, witness] = await Promise.all([
    fetch('/api/flags').then(r => r.json()),
    fetch('/api/klalim?part=' + currentPart).then(r => r.json()),
    fetch('/api/witness').then(r => r.json()),
  ]);
  FLAGS = flags;
  KLALIM = klalim;
  klalById = Object.fromEntries(klalim.map(k => [k.klal_id, k]));
  WITNESS_PAGES = witness.pages || [];

  setupPartSelect();
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
        fetch('/api/klalim?part=' + (currentPart || '1')).then(r => r.json()),
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
  const aiTotal = KLALIM.reduce((s, k) => s + (k.ai_flag_count || 0), 0);
  const aiRow = document.createElement('div');
  aiRow.className = 'legend-row';
  aiRow.innerHTML = `<i style="border-bottom:3px dashed #805ad5;background:transparent;"></i><span>AI-Flagged</span><b class="legend-count">${aiTotal}</b>`;
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
  const onlyFlagged = document.getElementById('filter-flagged')?.checked;
  const onlyHighValue = document.getElementById('filter-high-value')?.checked;

  document.querySelectorAll('.nav-item').forEach(el => {
    const kid = parseInt(el.dataset.klalId);
    const k = klalById[kid];
    let show = true;
    if (onlyFlagged && !k?.needs_revisit) show = false;
    if (onlyHighValue && (k?.open_count === 0 && k?.machine_disputed_count === 0 && !k?.needs_revisit)) show = false;
    el.style.display = show ? '' : 'none';
  });
}

function setupFilter() {
  document.getElementById('filter-flagged')?.addEventListener('change', applyFlaggedFilter);
  document.getElementById('filter-high-value')?.addEventListener('change', applyFlaggedFilter);
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

// Approximate scroll-driven page-flip points within a multi-page klal's own
// text block. A continuation's token_count is a DocAI-page word count, not
// an exact index into clean_text.split(' ') (punctuation/markers differ
// slightly between the two), so this is a same-neighborhood approximation,
// not an exact boundary - good enough for "the scan flips to the next page
// at roughly the right point while scrolling", which is strictly better
// than never flipping at all (the previous behavior - .continuations was
// served by the API but never read anywhere in this file). Continuations
// are later pages, so each one's tokens are assumed to be the TAIL of the
// klal's word list; walked back-to-front for multiple continuations.
function continuationBoundaries(k) {
  const totalWords = (k.clean_text || '').split(' ').length;
  const conts = k.continuations || [];
  let remaining = totalWords;
  const boundaries = [];
  for (let i = conts.length - 1; i >= 0; i--) {
    remaining = Math.max(0, remaining - (conts[i].token_count || 0));
    boundaries.unshift({ wordIndex: remaining, page: conts[i].page });
  }
  return boundaries; // ascending wordIndex order
}

function renderKlalBody(block, k) {
  const body = block.querySelector('.klal-body');
  body.className = 'klal-body';
  body.innerHTML = '';

  // Most witness items now appear as highlighted words in the text (via the
  // word_index patch). A small number (items whose DocAI token fell in an
  // alignment gap) have no word_index and remain scan-only. Show a banner
  // only for those, so the reviewer knows there are a few items they must
  // find in the scan pane manually. k.witness_count is the TOTAL; the text
  // highlights cover the mapped ones; the difference is scan-only.
  const mappedWitnessCount = k.corrections.filter(c => c.opcode === 'witness').length;
  const unmappedWitness = (k.witness_count || 0) - mappedWitnessCount;
  if (unmappedWitness > 0) {
    const pages = (k.witness_pages || []).join(', ');
    const banner = document.createElement('div');
    banner.className = 'witness-banner';
    banner.innerHTML = `<b>${unmappedWitness}</b> scan-reading disagreement${unmappedWitness === 1 ? '' : 's'} on page${k.witness_pages && k.witness_pages.length > 1 ? 's' : ''} ${pages} could not be mapped to text positions — reviewable in the scan pane only.`;
    body.appendChild(banner);
  }

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
  const contBoundaries = {};
  continuationBoundaries(k).forEach(b => { contBoundaries[b.wordIndex] = b.page; });

  words.forEach((w, i) => {
    if (contBoundaries[i] != null) {
      const marker = document.createElement('span');
      marker.className = 'continuation-marker';
      marker.dataset.page = contBoundaries[i];
      body.appendChild(marker);
    }
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
        // Show the klal's scan page with focused ring on the ai_flag's word.
        // Respect manualPageLock: if the reviewer manually navigated to a
        // continuation page, don't snap back to the start page.
        if (!manualPageLock) {
          const targetPage = corr.page || k.page;
          showPage(targetPage, k.klal_id, corr);
        }
        openManualCorrectionPanel(k.klal_id, i, w, corr);
      };
      body.appendChild(span);
    } else if (corr && corr.opcode === 'witness') {
      // DocAI-vs-Tesseract disagreement on a continuation page. word_index was
      // computed from the page's DocAI token stream via sequence alignment in
      // tools/patch_witness_word_indices.py. Same tri-state coloring as any
      // other flagged word; opens the witness panel (not the candidate panel).
      const span = document.createElement('span');
      span.className = 'flag-word state-' + wordState(corr);
      span.textContent = w;
      span.title = corr.docai_reading
        ? `DocAI: ${corr.docai_reading} | Tesseract: ${corr.tesseract_reading || '—'}`
        : '';
      span.onclick = () => {
        if (!manualPageLock) showPage(corr.page || k.page, k.klal_id, corr);
        openWitnessPanel(corr);
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
      const wState = wordState(corr);
      let chosenText = null;
      if (corr.current_decision && corr.current_decision.chosen_text !== undefined) {
        chosenText = corr.current_decision.chosen_text;
      }
      const pendingDelete = chosenText === '';
      const pendingReplace = !pendingDelete && chosenText && chosenText !== w;

      span.className = 'flag-word state-' + wState
        + (pendingDelete ? ' pending-delete' : '')
        + (pendingReplace ? ' pending-replace' : '');
      span.textContent = w;
      attachWordHandlers(span, k.klal_id, corr);
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
        attachWordHandlers(repl, k.klal_id, corr);
        body.appendChild(repl);
      }
    } else {
      // Plain, not-yet-flagged word - clickable too (2026-08-13, "add
      // feature for reviewer to flag any word and replace it"), not just
      // ones the machine pipeline already flagged. No persistent styling
      // (a hover-only affordance, see .plain-word:hover in app.css) so the
      // vast majority of never-touched text doesn't look visually "flagged".
      const span = document.createElement('span');
      span.className = 'plain-word';
      span.textContent = w;
      span.onclick = () => {
        // FIXED 2026-08-21 (user bug report: klal 2 word 439 didn't jump to
        // page 15). First fix attempt used contBoundaries (built above from
        // continuationBoundaries(), a client-side estimate based on a
        // continuation's token_count) to pick the page - but that's an
        // approximation the code itself already documented as inexact, and
        // a second bug report (word 185 wrongly staying on page 15,
        // highlighting the wrong word) confirmed it: the estimate put the
        // page-14/15 split at word 151, but the real split is elsewhere, so
        // words in the gap navigated to the wrong page. k.word_pages is the
        // real, DocAI-alignment-based word_index -> page map the server now
        // sends (same alignment ai_flag/witness words already trust via
        // their own corr.page) - use it, falling back to k.page only for a
        // word with no alignment match (an OCR gap DocAI never aligned).
        const targetPage = k.word_pages && k.word_pages[i] != null ? k.word_pages[i] : k.page;
        const corrObj = { klal_id: k.klal_id, word_index: i, opcode: 'plain' };
        // FIXED 2026-08-21 (code review): every sibling click handler
        // (ai_flag, witness, attachWordHandlers) guards its showPage() call
        // with `if (!manualPageLock)` so a reviewer's manual scan-pane
        // navigation isn't silently overridden by the next word click; this
        // handler was calling showPage() unconditionally, the one
        // inconsistent case.
        if (!manualPageLock) showPage(targetPage, k.klal_id, corrObj);
        openManualCorrectionPanel(k.klal_id, i, w, null);
      };
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
    tooltip.innerHTML = `<span class="t-flag">${escapeHtml(statusLabel(corr))} (Word #${corr.word_index})</span><span class="t-docai">${docaiTxt}</span>${bodyTxt}${decisionTxt}`;
    tooltip.style.display = 'block';
    positionTooltip(e);
  });
  el.addEventListener('mousemove', positionTooltip);
  el.addEventListener('mouseleave', () => { tooltip.style.display = 'none'; });
  el.addEventListener('click', () => {
    tooltip.style.display = 'none';
    // Each correction carries its own page field — the physical scan page
    // where its bbox lives (may be a continuation page for klals that span
    // multiple pages). Navigate there so the bbox is found.
    if (!manualPageLock) {
      const targetPage = corr.page || (klalById[klalId] && klalById[klalId].page);
      showPage(targetPage, klalId, corr);
    }
    openDisputedPanel(klalId, corr);
  });
}
function positionTooltip(e) {
  const pad = 16;
  let x = e.clientX + pad, y = e.clientY + pad;
  if (x + 360 > window.innerWidth) x = e.clientX - 360;
  tooltip.style.left = x + 'px';
  tooltip.style.top = y + 'px';
}

// ---------- disputed word override panel ----------
const backdrop = document.getElementById('overlay-backdrop');
const disputedPanel = document.getElementById('disputed-panel') || document.getElementById('candidate-panel');
const disputedPanelBody = document.getElementById('disputed-panel-body') || document.getElementById('candidate-panel-body');
const candidatePanel = disputedPanel;
const candidatePanelBody = disputedPanelBody;
const klalFlagPanel = document.getElementById('klal-flag-panel');
const klalFlagPanelBody = document.getElementById('klal-flag-panel-body');
const punctuationPanel = document.getElementById('punctuation-panel');
const punctuationPanelBody = document.getElementById('punctuation-panel-body');
const witnessPanel = document.getElementById('witness-panel');
const witnessPanelBody = document.getElementById('witness-panel-body');
const manualPanel = document.getElementById('manual-panel');
const manualPanelBody = document.getElementById('manual-panel-body');

function setupPanels() {
  const disputedClose = document.getElementById('disputed-panel-close') || document.getElementById('candidate-panel-close');
  if (disputedClose) disputedClose.onclick = dismissPanels;
  document.getElementById('klal-flag-panel-close').onclick = dismissPanels;
  document.getElementById('punctuation-panel-close').onclick = dismissPanels;
  document.getElementById('witness-panel-close').onclick = dismissPanels;
  document.getElementById('manual-panel-close').onclick = dismissPanels;
  backdrop.onclick = dismissPanels;
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') dismissPanels();
  });
}
function closePanels() {
  backdrop.classList.remove('open');
  disputedPanel.classList.remove('open');
  klalFlagPanel.classList.remove('open');
  punctuationPanel.classList.remove('open');
  witnessPanel.classList.remove('open');
  manualPanel.classList.remove('open');
}
// Dismiss panels AND clear scan focus — only for explicit user dismissals
// (Escape, backdrop click), NOT for openPanel()'s internal closePanels() call
// which fires before every panel switch.
function dismissPanels() {
  closePanels();
  clearScanFocus();
}
// ADDED 2026-08-21 (user-requested): a save used to just flash a small
// "Saved ✓" label and leave the panel open indefinitely - the reviewer had
// to manually dismiss it (X button/Escape/backdrop) before moving to the
// next word. Now: show the confirmation clearly (see .save-status.show's
// CSS for the visual treatment), hold it for DECISION_SAVED_CLOSE_DELAY_MS
// so the reviewer actually sees it land, then auto-close - same effect as
// clicking the panel's own X button (dismissPanels, not just closePanels,
// for the same reason those are already wired to the same handler: an
// auto-close should behave identically to a manual one, including
// clearing scan focus). Shared by every save function that already used
// the .save-status pattern (disputed/klal-flag/punctuation/witness) -
// the manual-correction panel deliberately keeps its own different
// confirmation (re-rendering the panel with the fresh post-save state IS
// its confirmation - see openManualCorrectionPanel's own comment on why).
const DECISION_SAVED_CLOSE_DELAY_MS = 2000;
// Incremented on every openPanel() call - same generation-counter pattern
// showPage()'s own _showPageGen already uses for the identical class of
// problem. Without this, a reviewer who saves, then opens a DIFFERENT
// word's panel within DECISION_SAVED_CLOSE_DELAY_MS, would have that new
// panel yanked shut by the FIRST save's now-stale delayed close - a real
// race the auto-close behavior introduces that didn't exist when a save
// never closed anything on its own.
let _panelGen = 0;

function flashSavedThenClose(statusElementId) {
  const status = document.getElementById(statusElementId);
  if (status) status.classList.add('show');
  const gen = _panelGen;
  setTimeout(() => {
    if (status) status.classList.remove('show');
    if (gen === _panelGen) dismissPanels();
  }, DECISION_SAVED_CLOSE_DELAY_MS);
}

function openPanel(panel) {
  closePanels();
  _panelGen++;
  backdrop.classList.add('open');
  panel.classList.add('open');
}

async function openDisputedPanel(klalId, corr) {
  openPanel(disputedPanel);
  disputedPanelBody.innerHTML = '<p>Loading…</p>';

  const k = mountedKlal[klalId] || await fetchKlal(klalId);
  const words = (k.clean_text || '').split(' ');
  const ctxStart = Math.max(0, corr.word_index - 6);
  const ctxEnd = Math.min(words.length, corr.word_index + 7);
  // FIXED 2026-08-14 (same bug class as the witness panel's context
  // highlight, found via user report): a 'replace'/'insert' candidate can
  // carry a multi-word final_text (e.g. word 8 "רב פפא" where docai saw
  // only one word), so bolding words[corr.word_index] alone left the rest
  // of the candidate unstyled. Count how many words final_text actually
  // holds; if none (a 'delete' opcode, or a word_index at the end of the
  // text where there is no word to bold), bold one placeholder word at
  // that index rather than none.
  const spanLen = corr.final_text ? corr.final_text.split(/\s+/).length : 1;
  const ctxWords = words.slice(ctxStart, ctxEnd).map((w, idx) => {
    const absIdx = ctxStart + idx;
    if (absIdx >= corr.word_index && absIdx < corr.word_index + spanLen) {
      return `<b>${escapeHtml(w)}</b>`;
    }
    return escapeHtml(w);
  }).join(' ');

  const decision = corr.current_decision;
  const flagColor = STATE_META[wordState(corr)].color;
  const [flagLabel] = FLAGS[corr.flag] || ['Disputed'];

  const options = [];
  if (corr.opcode === 'insert') {
    // Insert: docai found nothing; corpus has a word
    if (corr.final_text) options.push({ source: 'final_text', label: 'Keep current text', text: corr.final_text });
    options.push({ source: 'remove', label: 'Remove (accept omission)', text: '—' });
  } else if (corr.opcode === 'delete') {
    // Delete: docai found a word; corpus has nothing
    options.push({ source: 'docai_reading', label: 'Accept inserted word', text: corr.docai_reading || '' });
    options.push({ source: 'final_text', label: 'Keep current text (no word)', text: '—' });
  } else {
    // Normal replace
    if (corr.final_text) options.push({ source: 'final_text', label: 'Current text', text: corr.final_text });
    if (corr.docai_reading) options.push({ source: 'docai_reading', label: 'DocAI reading', text: corr.docai_reading });
  }
  if (corr.vision_transcription && !options.some(o => o.text === corr.vision_transcription)) {
    options.push({ source: 'vision_transcription', label: 'Vision reading', text: corr.vision_transcription });
  }
  // VLM baseline reading (added 2026-08-21, stage 4 candidate enrichment):
  // show as an option whenever it differs from everything already listed
  if (corr.vlm_reading && !options.some(o => o.text === corr.vlm_reading)) {
    options.push({ source: 'vlm_reading', label: 'VLM baseline reading', text: corr.vlm_reading });
  }

  // Pre-fill the AI detector's suggested word as an extra selectable option
  // card when present (added 2026-08-14, see openManualCorrectionPanel's
  // note on why: typing Hebrew acronyms by hand is slow and error-prone;
  // this gives the reviewer a 1-click accept option for the AI suggestion
  // without typing). Matches openManualCorrectionPanel's layout: placed
  // right below the current-text option, distinctly styled via .co-meta.
  const suggestedWord = extractSuggestedWord(corr);
  if (suggestedWord && !options.some(o => o.text === suggestedWord)) {
    options.splice(1, 0, {
      source: 'suggested',
      label: 'AI detector suggestion',
      text: suggestedWord,
    });
  }

  let activeSource = decision ? decision.chosen_source : 'final_text';
  let activeText = decision ? (decision.chosen_text || '') : '';
  if (!decision && corr.vision_selected) {
    if (corr.vision_selected === 'A' && options.some(o => o.source === 'docai_reading')) activeSource = 'docai_reading';
    else if (corr.vision_selected === 'B' && options.some(o => o.source === 'final_text')) activeSource = 'final_text';
  }

  // Fall back to custom if the saved source isn't in options
  if (activeSource && !options.some(o => o.source === activeSource) && activeSource !== 'custom' && activeSource !== 'remove') {
    // If the saved decision has custom text, treat as custom
    if (activeText) {
      activeSource = 'custom';
    } else {
      activeSource = 'final_text';
    }
  }

  const html = `
    <div class="panel-section">
      <div><i style="background:${flagColor};width:9px;height:9px;border-radius:2px;display:inline-block;margin-inline-end:6px;"></i>${statusLabel(corr)}</div>
      <div style="font-size:12px;color:var(--ink-faint);margin-top:4px;">${escapeHtml(flagLabel)}${corr.confidence != null ? ' · ' + Math.round(corr.confidence * 100) + '% vision confidence' : ''}</div>
    </div>
    <div class="panel-section">
      <div class="panel-label">Context (Klal ${klalId} · Word #${corr.word_index})</div>
      <div class="panel-word-context">${ctxWords}</div>
      ${corr.reasoning ? `<div style="font-size:12px;color:var(--ink-faint);margin-top:-8px;">${escapeHtml(corr.reasoning)}</div>` : ''}
    </div>
    <div class="panel-section">
      <div class="panel-label">Choose the correct reading</div>
      <div id="disputed-options"></div>
      <div class="disputed-option candidate-option" data-source="custom" id="custom-option">
        <input type="radio" name="disputed" ${activeSource === 'custom' ? 'checked' : ''}>
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
  disputedPanelBody.innerHTML = html;

  const optionsContainer = document.getElementById('disputed-options');
  options.forEach(opt => {
    const div = document.createElement('div');
    div.className = 'disputed-option candidate-option' + (activeSource === opt.source ? ' active' : '');
    div.dataset.source = opt.source;
    div.dataset.text = opt.text;
    div.innerHTML = `<input type="radio" name="disputed" ${activeSource === opt.source ? 'checked' : ''}>
      <div class="co-body"><div class="co-label">${escapeHtml(opt.label)}</div><div class="co-text">${escapeHtml(opt.text)}</div></div>`;
    div.onclick = () => selectDisputedOption(opt.source);
    optionsContainer.appendChild(div);
  });
  document.getElementById('custom-option').onclick = () => selectDisputedOption('custom');
  if (activeSource === 'custom') markActiveOption('custom');

  document.getElementById('save-decision-btn').onclick = () => saveDisputedDecision(klalId, corr);
  document.getElementById('history-toggle').onclick = () => toggleHistory(klalId, corr.word_index);
}

const openCandidatePanel = openDisputedPanel;
window.openCandidatePanel = openCandidatePanel;
window.openDisputedPanel = openDisputedPanel;

function selectDisputedOption(source) {
  markActiveOption(source);
}
const selectCandidateOption = selectDisputedOption;

function markActiveOption(source) {
  document.querySelectorAll('.disputed-option, .candidate-option').forEach(el => {
    const active = el.dataset.source === source;
    el.classList.toggle('active', active);
    const radio = el.querySelector('input[type=radio]');
    if (radio) radio.checked = active;
  });
}

async function saveDisputedDecision(klalId, corr) {
  const activeEl = document.querySelector('.disputed-option.active, .candidate-option.active');
  const source = activeEl ? activeEl.dataset.source : 'final_text';
  let text, chosenSource;
  if (source === 'remove') {
    text = '';
    chosenSource = 'custom';
  } else if (source === 'custom') {
    text = document.getElementById('custom-text-input').value.trim();
    if (!text && corr.opcode !== 'insert' && corr.final_text) { alert('Enter the custom reading first.'); return; }
    chosenSource = 'custom';
  } else if (source === 'suggested') {
    text = activeEl.dataset.text;
    chosenSource = 'custom';
  } else {
    text = corr[source];
    chosenSource = source;
  }
  const note = document.getElementById('decision-note').value.trim();

  const res = await fetch('/api/decisions/disputed', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ klal_id: klalId, word_index: corr.word_index, chosen_source: chosenSource, chosen_text: text, note }),
  });
  if (!res.ok) { alert('Save failed: ' + (await res.text())); return; }

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

  flashSavedThenClose('save-status');
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
    flashSavedThenClose('klal-flag-save-status');
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
  if (currentPage != null) await showPage(currentPage, klalId);

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
  const markedForDeletion = !isAiFlag && existing && existing.current_decision && existing.current_decision.chosen_text === '';
  const currentText = existing && !isAiFlag && !markedForDeletion && existing.current_decision ? existing.current_decision.chosen_text : '';
  const currentNote = existing && existing.current_decision && existing.current_decision.note ? existing.current_decision.note : '';
  const reasoningNote = existing ? (existing.reasoning || (existing.current_decision && existing.current_decision.note)) : null;

  const suggestedWord = extractSuggestedWord(reasoningNote);

  manualPanelBody.innerHTML = `
    <div class="panel-section">
      <div class="panel-label">Klal ${klalId} · Word #${wordIndex}</div>
      <div class="panel-word-context">${ctxWords}</div>
    </div>
    ${suggestedWord ? `
    <div class="panel-section" style="background:#2b6cb022;border:1px solid #3182ce;border-radius:6px;padding:8px 12px;margin-bottom:12px;">
      <div style="font-weight:bold;color:#63b3ed;font-size:13px;">💡 Suggested replacement: <bdi style="font-size:15px;color:#fff;">${escapeHtml(suggestedWord)}</bdi></div>
      <div style="font-size:12px;color:var(--ink-faint);margin-top:2px;">Extracted from lexicon detector analysis</div>
      <button type="button" class="panel-btn" id="use-suggested-word-btn" style="margin-top:8px;padding:4px 12px;font-size:13px;background:#3182ce;color:#fff;border:none;border-radius:4px;cursor:pointer;">Use "${escapeHtml(suggestedWord)}"</button>
    </div>` : ''}
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
             placeholder="Correct reading…" value="${escapeAttr(currentText || (suggestedWord || ''))}">
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
  const useSuggestedBtn = document.getElementById('use-suggested-word-btn');
  if (useSuggestedBtn && suggestedWord) {
    useSuggestedBtn.onclick = () => {
      document.getElementById('manual-correction-text').value = suggestedWord;
      document.getElementById('save-manual-correction-btn').click();
    };
  }

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

    flashSavedThenClose('punct-save-status');
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
  const ctxRaw = await fetch(`/api/witness/context/${w.page}/${w.docai_token_index}`)
    .then(r => r.ok ? r.json() : null).catch(() => null);
  const ctx = (ctxRaw && Array.isArray(ctxRaw.words)) ? ctxRaw : { words: [], target_index: null };
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
      <div class="panel-label">Klal ${w.klal_id} · Token #${w.docai_token_index} · tier ${w.tier} · page ${w.page}</div>
      <div style="font-size:12px;color:var(--ink-faint);">Two OCR engines disagree here and both readings are real Hebrew
      words, so a word-lexicon check can't tell them apart - this needs the ink.</div>
    </div>
    ${decision ? `<div class="panel-section">
      <div class="panel-label">Current decision</div>
      <div style="color:${STATE_META.human.color};font-weight:600;">${STATE_META.human.label}: &ldquo;${escapeHtml(decision.chosen_text !== '' ? decision.chosen_text : '(unreadable)')}&rdquo;</div>
      ${decision.note ? `<div style="font-size:12px;color:var(--ink-faint);margin-top:2px;">${escapeHtml(decision.note)}</div>` : ''}
    </div>` : ''}
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

  // Re-fetch this klal so text-pane spans get corr.current_decision set,
  // and the word turns green (human state) immediately without a full reload.
  delete mountedKlal[w.klal_id];
  delete fetchInFlight[w.klal_id];
  const freshK = await fetchKlal(w.klal_id);
  const block = document.getElementById('klal-block-' + w.klal_id);
  if (block) renderKlalBody(block, freshK);

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

  flashSavedThenClose('witness-save-status');
}

// ---------- scan pane ----------
let currentPage = null;
let scanFocusKlalId = null; // which klal's region/continuation to highlight, independent of which page is shown
let scanFocusCorr = null;   // active focused word candidate object, preserved across zoom and page redraws
let _showPageGen = 0; // generation counter - incremented on every showPage call so stale
                      // async continuations can detect they've been superseded and abort
                      // before appending boxes to a container that already belongs to a newer call.
// When true, setActiveKlal()'s showPage() call is suppressed - prevents scroll-
// driven klal changes from snapping the scan back to a klal's start page after
// the reviewer explicitly navigated to a continuation or adjacent page via the
// prev/next buttons.  Reset when the reviewer clicks a word in the text pane or
// a nav item, both of which express an explicit intent about which page to show.
let manualPageLock = false;
// Focused box that showPage() wants scrolled into view once the new page image
// has loaded and applyZoom has reset the scroll position. Checked inside the
// pageImg 'load' handler (setupZoomPan) which fires after applyZoom runs.
// Set to null when consumed or when a newer showPage supersedes the old focus.
let _pendingScrollToBox = null;
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
    const focusedBox = hlContainer.querySelector('.hl-box.focused');
    if (focusedBox) {
      focusedBox.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' });
    } else {
      scanViewer.scrollLeft = rX * pageImg.offsetWidth - scanViewer.clientWidth / 2;
      scanViewer.scrollTop = rY * pageImg.offsetHeight - scanViewer.clientHeight / 2;
    }
  });
}
function setupZoomPan() {
  document.getElementById('zoom-in').onclick = () => { zoomLevel = Math.min(3, zoomLevel + 0.25); applyZoom(); };
  document.getElementById('zoom-out').onclick = () => { zoomLevel = Math.max(0.3, zoomLevel - 0.25); applyZoom(); };
  scanViewer.addEventListener('wheel', (e) => {
    if (e.ctrlKey || e.metaKey) {
      e.preventDefault();
      const delta = e.deltaY < 0 ? 0.15 : -0.15;
      zoomLevel = Math.max(0.3, Math.min(3, zoomLevel + delta));
      applyZoom();
    }
  }, { passive: false });
  pageImg.addEventListener('load', () => {
    applyZoom(0.5, 0);
    // applyZoom queues a rAF that scrolls to the top of the new page. If a
    // focused word box is pending, queue our scroll AFTER it so we win: both
    // rAFs run in the same frame (registration order), so applyZoom's scroll
    // runs first and ours overwrites it.
    if (_pendingScrollToBox) {
      const box = _pendingScrollToBox;
      _pendingScrollToBox = null;
      requestAnimationFrame(() =>
        box.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' })
      );
    }
  });

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

// Apply focused-word highlight styles directly via JS (setProperty with
// 'important' priority) so they work regardless of browser CSS cache state.
// Thick ring in the box's own state color; interior is set entirely transparent
// so the scan text under the box remains crystal clear for human eyeball review.
function applyFocusStyle(box) {
  const color = box.style.getPropertyValue('--hl-color') || '#3182ce';
  box.style.setProperty('box-shadow', `0 0 0 6px ${color}`, 'important');
  box.style.setProperty('background', 'transparent', 'important');
  box.style.setProperty('z-index', '5');
  box.style.setProperty('opacity', '1', 'important');
}

// Redraw the current scan page without any focused word, restoring all boxes
// to their normal opacity/style. Called when the reviewer clicks away from a
// focused word (plain word click, panel close, etc.).
function clearScanFocus() {
  scanFocusCorr = null;
  if (currentPage != null) showPage(currentPage, scanFocusKlalId, null);
}

async function showPage(page, focusKlalId, focusCorr = undefined) {
  if (focusCorr !== undefined) {
    scanFocusCorr = focusCorr;
  } else {
    focusCorr = scanFocusCorr;
  }
  if (!page) {
    currentPage = null;
    pageIndicator.textContent = 'Part 2 & 3 Review';
    let notice = document.getElementById('scan-notice');
    if (!notice) {
      notice = document.createElement('div');
      notice.id = 'scan-notice';
      notice.style.cssText = 'padding: 40px 24px; text-align: center; color: #a0aec0; font-family: Inter, sans-serif; font-size: 13px; line-height: 1.6; background: #ffffff; border-radius: 8px; margin: 40px auto; max-width: 320px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); direction: rtl;';
      const scanViewer = document.getElementById('scan-viewer');
      if (scanViewer) scanViewer.appendChild(notice);
    }
    notice.style.display = 'block';
    notice.innerHTML = '<b style="color: #2b6cb0; font-size: 15px; display: block; margin-bottom: 8px;">Part 2 &amp; 3 Review</b><span style="color:#4a5568;display:block;margin-bottom:12px;">Scan images are currently available for Part 1 (Klalei HaGemara, Klalim 1–222).</span><span style="color:#2d3748;font-size:12px;">All text, punctuation, and VLM candidates for Part 2 &amp; 3 are fully active in the text pane on the right.</span>';
    const pageContainer = document.getElementById('page-container');
    if (pageContainer) pageContainer.style.display = 'none';
    return;
  }
  const notice = document.getElementById('scan-notice');
  if (notice) notice.style.display = 'none';
  const pageContainer = document.getElementById('page-container');
  // FIXED 2026-08-20 (user report: all scan boxes shifted left, yellow
  // klal-region box running off the left margin). #page-container's CSS
  // rule is `display: table` specifically so it shrink-wraps to #page-img's
  // actual rendered width - #hl-container is `position:absolute; inset:0`
  // inside it, and every .hl-box left/top is a percentage of that box.
  // Setting the inline style to 'block' here permanently overrode the CSS
  // table rule (inline style always wins) on EVERY normal page view, not
  // just this notice-hiding path - `display:block` stretches to the full
  // available width instead of shrink-wrapping, so #hl-container became
  // wider than the actual image (confirmed via Playwright: container
  // width 475px vs image width 443px, a 32px gap) and every percentage-
  // based box position was computed against the wrong denominator.
  // removeProperty (not 'table') so this never has to be kept in sync with
  // the CSS rule's own value by hand.
  if (pageContainer) pageContainer.style.removeProperty('display');
  pageImg.style.display = 'block';
  const gen = ++_showPageGen;
  const pageChanged = page !== currentPage;
  if (pageChanged) {
    currentPage = page;
    pageImg.src = `/images/pdf_pages/page_${page}.png`;
    pageIndicator.textContent = 'Page ' + page;
  }
  scanFocusKlalId = focusKlalId;
  updatePageNavButtons();
  hlContainer.innerHTML = '';

  const focusKlal = mountedKlal[focusKlalId] || (await fetchKlal(focusKlalId).catch(() => null));
  // A newer showPage call superseded this one while we awaited fetchKlal.
  // The newer call already cleared the container and is drawing its own boxes;
  // appending ours would corrupt the display (stale region box from a different
  // klal/page appearing behind the correct word boxes).
  if (gen !== _showPageGen) return;
  // Only draw the klal region box on the klal's START page (not continuations),
  // and only when the reviewer hasn't clicked a specific word to focus - when
  // focusCorr is set, the yellow .focused box is the landmark; drawing the
  // large gold region box on top of it just adds noise.
  let r = null;
  if (!focusCorr && focusKlal && focusKlal.page === page) r = focusKlal.region;
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
  if (gen !== _showPageGen) return; // superseded while awaiting /api/page/
  let focusedBox = null;
  pageItems.forEach(c => {
    if (!c.bbox) return;
    // Is this the specific word the reviewer clicked in the text pane?
    // Branch on focusCorr.opcode (the thing the user clicked) rather than
    // c.kind (the scan-page item) so the lookup key is always driven by the
    // source: witness items key on docai_token_index, everything else on
    // word_index.  Both are integers from the same JSON source, no cast needed.
    const isFocused = focusCorr && c.klal_id === focusKlalId && (
      focusCorr.opcode === 'witness'
        ? c.docai_token_index === focusCorr.docai_token_index
        : c.word_index === focusCorr.word_index
    );

    // Padding around word bounding box to ensure letter tails (final nun, kof, etc.) and ascenders (lamed) are completely clear
    const padX = 0.003;
    const padY = 0.005;
    const bx1 = Math.max(0, c.bbox.x1 - padX);
    const by1 = Math.max(0, c.bbox.y1 - padY);
    const bx2 = Math.min(1, c.bbox.x2 + padX);
    const by2 = Math.min(1, c.bbox.y2 + padY);

    if (c.kind === 'witness') {
      const box = document.createElement('div');
      const state = c.current_decision ? 'human' : 'open';
      box.className = 'hl-box hl-state-' + state + (c.klal_id === focusKlalId ? '' : ' dim') + (isFocused ? ' focused' : '');
      const color = STATE_META[state].color;
      box.style.setProperty('--hl-color', color);
      box.style.background = color + '33';
      box.style.left = (bx1 * 100) + '%';
      box.style.top = (by1 * 100) + '%';
      box.style.width = ((bx2 - bx1) * 100) + '%';
      box.style.height = ((by2 - by1) * 100) + '%';
      box.title = c.current_decision
        ? `${STATE_META.human.label}: "${c.current_decision.chosen_text || ''}"`
        : `${STATE_META.open.label} (tier ${c.tier}) - click to decide`;
      box.addEventListener('click', () => openWitnessPanel(c));
      hlContainer.appendChild(box);
      if (isFocused) { focusedBox = box; applyFocusStyle(box); }
      return;
    }
    if (c.kind === 'plain') {
      if (!isFocused) return;
      const box = document.createElement('div');
      box.className = 'hl-box hl-state-human focused';
      const color = '#3182ce';
      box.style.setProperty('--hl-color', color);
      box.style.background = 'transparent';
      box.style.left = (bx1 * 100) + '%';
      box.style.top = (by1 * 100) + '%';
      box.style.width = ((bx2 - bx1) * 100) + '%';
      box.style.height = ((by2 - by1) * 100) + '%';
      hlContainer.appendChild(box);
      focusedBox = box;
      applyFocusStyle(box);
      return;
    }
    const box = document.createElement('div');
    const state = wordState(c);
    box.className = 'hl-box hl-state-' + state + (c.klal_id === focusKlalId ? '' : ' dim') + (isFocused ? ' focused' : '');
    const color = STATE_META[state].color;
    box.style.setProperty('--hl-color', color);
    box.style.background = color + '33';
    box.style.left = (bx1 * 100) + '%';
    box.style.top = (by1 * 100) + '%';
    box.style.width = ((bx2 - bx1) * 100) + '%';
    box.style.height = ((by2 - by1) * 100) + '%';
    attachWordHandlers(box, c.klal_id, c);
    hlContainer.appendChild(box);
    if (isFocused) { focusedBox = box; applyFocusStyle(box); }
  });

  // Only dim other boxes if we actually found a focused box. If focusCorr was
  // set but nothing matched (e.g. an ai_flag with no bbox in api_page), leave
  // all boxes at normal opacity rather than dimming everything to nothing.
  hlContainer.classList.toggle('has-focus', !!focusedBox);

  if (focusedBox) {
    // applyZoom(0.5, 0) fires on image load and resets scroll to the top of
    // the new page.  We need to scroll the focused box into view AFTER that.
    // Two cases:
    // 1. Page changed: set _pendingScrollToBox; the load handler in
    //    setupZoomPan will consume it and queue a rAF AFTER applyZoom's rAF.
    //    Using a global rather than a { once: true } load listener avoids the
    //    race where a cached image loads before we finish awaiting the page
    //    items and ever get to register our listener.
    // 2. Same page: image already loaded (load won't fire again); use a
    //    double-rAF so we run after any layout passes.
    if (pageChanged && !pageImg.complete) {
      _pendingScrollToBox = focusedBox;
    } else {
      _pendingScrollToBox = null;
      requestAnimationFrame(() =>
        focusedBox.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' })
      );
    }
  } else {
    _pendingScrollToBox = null; // superseded focus, cancel any pending scroll
  }
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
  manualPageLock = true; // suppress scroll-driven setActiveKlal from snapping back
  showPage(targetPage, scanFocusKlalId);
}

// ---------- nav / scroll sync ----------
let suppressObserverScroll = false;
let suppressTimer = null;
let lastActiveKlalId = null;
let lastActiveScanPage = null; // which page updateActiveFromScroll last showed for the active klal

function jumpTo(klalId) {
  const block = document.getElementById('klal-block-' + klalId);
  if (!block) return;
  suppressObserverScroll = true;
  manualPageLock = false; // nav-panel click = explicit klal intent; let setActiveKlal show its page
  lastActiveKlalId = klalId;
  setActiveKlal(klalId);
  // Keep updateActiveFromScroll's continuation-boundary tracking (see
  // there) in sync with this explicit jump, so scrolling afterward within
  // the same klal doesn't immediately re-trigger a redundant showPage call
  // against a stale page from before the jump.
  lastActiveScanPage = klalById[klalId] ? klalById[klalId].page : null;
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
    document.title = `Klal ${klalId} (כלל ${klalId}) · Yad Malachi Review`;
    // manualPageLock: reviewer navigated the scan manually via prev/next -
    // don't snap back to this klal's start page just because the text pane
    // scrolled to it.  The lock is cleared when a word is clicked in the
    // text pane or a nav item is jumped to.
    //
    // Explicit `null` here, not the default `undefined` "keep scanFocusCorr"
    // sentinel - this call fires on every scroll-driven klal change
    // (updateActiveFromScroll) and every nav-panel jump, neither of which is
    // the reviewer clicking a specific word. scanFocusCorr from whichever
    // klal was last focused would otherwise carry into this new klal's page,
    // and isFocused's match is by word_index alone (not scoped to the klal
    // the click actually happened in) - a coincidental same word_index in
    // the new klal then renders a focus ring on the wrong word. FIXED
    // 2026-08-20 (dashboard regression: misplaced/erratic highlight boxes).
    if (!manualPageLock) showPage(k.page, klalId, null);
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
    lastActiveScanPage = klalById[klalId] ? klalById[klalId].page : null;
  }
  // Auto-advance the scan pane to a continuation page as the reader scrolls
  // past its boundary within the SAME klal's own text - the block above
  // only fires on a klal-to-klal transition, so a multi-page klal's own
  // later page was never reached by scrolling, only by the manual scan
  // prev/next buttons. FIXED 2026-08-20 (user report: "scrolling to the
  // bottom of klal 4 does not take you to the next page in the scan").
  if (!manualPageLock) {
    let targetPage = klalById[klalId] ? klalById[klalId].page : null;
    current.querySelectorAll('.continuation-marker').forEach(m => {
      if (m.getBoundingClientRect().top <= line) targetPage = parseInt(m.dataset.page, 10);
    });
    if (targetPage != null && targetPage !== lastActiveScanPage) {
      lastActiveScanPage = targetPage;
      showPage(targetPage, klalId);
    }
  }
}

let scrollScheduled = false;
textScroll.addEventListener('scroll', () => {
  if (suppressObserverScroll || scrollScheduled) return;
  scrollScheduled = true;
  requestAnimationFrame(() => { scrollScheduled = false; updateActiveFromScroll(); });
});

init();
