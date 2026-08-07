// Yad Malachi review dashboard frontend. Fetches data lazily from
// review_server.py's JSON API instead of having it all inlined - see
// PROJECT-STATUS.md "Review dashboard rearchitecture" for why.

let FLAGS = {};
let KLALIM = [];          // lightweight list from /api/klalim
let klalById = {};
let mountedKlal = {};     // klal_id -> full payload once fetched
let fetchInFlight = {};   // klal_id -> Promise, avoids double-fetch races

const textScroll = document.getElementById('text-scroll');
const navList = document.getElementById('nav-list');
const legend = document.getElementById('legend');
const tooltip = document.getElementById('tooltip');

async function init() {
  const [flags, klalim] = await Promise.all([
    fetch('/api/flags').then(r => r.json()),
    fetch('/api/klalim').then(r => r.json()),
  ]);
  FLAGS = flags;
  KLALIM = klalim;
  klalById = Object.fromEntries(klalim.map(k => [k.klal_id, k]));

  buildLegend();
  buildNav();
  buildPlaceholders();
  buildFirstKlalOfPage();
  setupObserver();
  setupFilter();
  setupZoomPan();
  setupPanels();

  lastActiveKlalId = KLALIM[0].klal_id;
  setActiveKlal(lastActiveKlalId);
}

function buildLegend() {
  legend.innerHTML = '';
  Object.entries(FLAGS).forEach(([key, [label, color]]) => {
    const span = document.createElement('span');
    span.innerHTML = `<i style="background:${color}"></i>${label}`;
    legend.appendChild(span);
  });
  const pendingSpan = document.createElement('span');
  pendingSpan.innerHTML = `<i style="background:#d69e2e;border-radius:50%"></i>You've recorded a decision`;
  legend.appendChild(pendingSpan);
}

// ---------- nav pane ----------
function buildNav() {
  navList.innerHTML = '';
  KLALIM.forEach(k => {
    const item = document.createElement('div');
    item.className = 'nav-item' + (k.correction_count ? ' has-flags' : '');
    item.id = 'nav-' + k.klal_id;
    item.dataset.klalId = k.klal_id;
    item.onclick = () => jumpTo(k.klal_id);
    const flagIcon = k.needs_revisit ? '<span class="nflag">&#9873;</span>' : '';
    item.innerHTML = `<span class="nid">${k.klal_id}</span><span class="ntitle" title="${(k.title || '').replace(/"/g, '&quot;')}">${k.title || ''}</span>${flagIcon}<span class="ncount">${k.correction_count}</span>`;
    navList.appendChild(item);
  });
}

function setupFilter() {
  document.getElementById('filter-flagged').addEventListener('change', (e) => {
    const only = e.target.checked;
    document.querySelectorAll('.nav-item').forEach(el => {
      const kid = parseInt(el.dataset.klalId);
      el.style.display = (!only || klalById[kid].needs_revisit) ? '' : 'none';
    });
  });
}

function refreshNavItem(klalId) {
  const k = klalById[klalId];
  const item = document.getElementById('nav-' + klalId);
  if (!k || !item) return;
  const flagIcon = k.needs_revisit ? '<span class="nflag">&#9873;</span>' : '';
  item.innerHTML = `<span class="nid">${k.klal_id}</span><span class="ntitle" title="${(k.title || '').replace(/"/g, '&quot;')}">${k.title || ''}</span>${flagIcon}<span class="ncount">${k.correction_count}</span>`;
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
    head.innerHTML = `<span class="kid">כלל ${k.klal_id}</span><span class="sec">${k.section || ''}</span>`;
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
    if (corr) {
      const span = document.createElement('span');
      const [, color] = FLAGS[corr.flag] || [null, '#a0aec0'];
      const isConfirmed = corr.flag === 'current_text_confirmed';
      span.className = 'flag-word ' + (isConfirmed ? 'confirmed' : 'disputed') + (corr.current_decision ? ' has-decision' : '');
      span.style.borderBottomColor = color;
      span.textContent = w;
      attachWordHandlers(span, k.klal_id, corr);
      body.appendChild(span);
    } else {
      body.appendChild(document.createTextNode(w));
    }
    body.appendChild(document.createTextNode(' '));
  });
}

function makeGapMarker(klalId, corr) {
  const span = document.createElement('span');
  span.className = 'flag-gap';
  const [, color] = FLAGS[corr.flag] || [null, '#a0aec0'];
  span.style.background = color;
  attachWordHandlers(span, klalId, corr, true);
  return span;
}

// ---------- quick hover tooltip ----------
function attachWordHandlers(el, klalId, corr, isGap) {
  const [label] = FLAGS[corr.flag] || ['Flagged'];
  el.addEventListener('mouseenter', (e) => {
    const confTxt = (corr.confidence != null) ? (Math.round(corr.confidence * 100) + '% confidence') : 'not scan-verified';
    const hebrewBit = `<bdi>${corr.docai_reading || (isGap ? '' : '(none)')}</bdi>`;
    const docaiTxt = isGap
      ? `Scan appears to show: "${hebrewBit}" — not present in current text`
      : `Original OCR reading: "${hebrewBit}"`;
    const bodyTxt = `<span class="t-conf">${confTxt}${corr.reasoning ? ' — ' + corr.reasoning : ''}</span>`;
    const decisionTxt = corr.current_decision
      ? `<span class="t-hint">Your decision: "${corr.current_decision.chosen_text}"${corr.current_decision.note ? ' — ' + corr.current_decision.note : ''}</span>`
      : `<span class="t-hint">Click for details / to record a decision</span>`;
    tooltip.innerHTML = `<span class="t-flag">${label}</span><span class="t-docai">${docaiTxt}</span>${bodyTxt}${decisionTxt}`;
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

function setupPanels() {
  document.getElementById('candidate-panel-close').onclick = closePanels;
  document.getElementById('klal-flag-panel-close').onclick = closePanels;
  backdrop.onclick = closePanels;
}
function closePanels() {
  backdrop.classList.remove('open');
  candidatePanel.classList.remove('open');
  klalFlagPanel.classList.remove('open');
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
  const ctxWords = words.slice(ctxStart, ctxEnd).map((w, idx) =>
    (ctxStart + idx === corr.word_index) ? `<b>${w}</b>` : w
  ).join(' ');

  const [flagLabel, flagColor] = FLAGS[corr.flag] || ['Flagged', '#a0aec0'];

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
    options.push({ source: 'remove', label: 'Remove this text (accept the omission)', text: '(nothing - remove "' + corr.final_text + '")' });
  }

  const decision = corr.current_decision;
  const activeSource = decision ? decision.chosen_source : 'final_text';
  const activeText = decision ? decision.chosen_text : corr.final_text;

  let html = `
    <div class="panel-section">
      <div class="panel-label">Flag</div>
      <div><i style="background:${flagColor};width:9px;height:9px;border-radius:2px;display:inline-block;margin-inline-end:6px;"></i>${flagLabel}${corr.confidence != null ? ' · ' + Math.round(corr.confidence * 100) + '% vision confidence' : ''}</div>
    </div>
    <div class="panel-section">
      <div class="panel-label">Context (klal ${klalId})</div>
      <div class="panel-word-context">${ctxWords}</div>
      ${corr.reasoning ? `<div style="font-size:12px;color:var(--ink-faint);margin-top:-8px;">${corr.reasoning}</div>` : ''}
    </div>
    <div class="panel-section">
      <div class="panel-label">Choose the correct reading</div>
      <div id="candidate-options"></div>
      <div class="candidate-option" data-source="custom" id="custom-option">
        <input type="radio" name="candidate" ${activeSource === 'custom' ? 'checked' : ''}>
        <div class="co-body">
          <div class="co-label">Custom</div>
          <input type="text" class="custom-text" id="custom-text-input" placeholder="Type the correct reading…" value="${activeSource === 'custom' ? (activeText || '') : ''}">
        </div>
      </div>
    </div>
    <div class="panel-section">
      <div class="panel-label">Note (optional)</div>
      <textarea id="decision-note" rows="3" placeholder="Why? e.g. &quot;crop-confirmed against page 26&quot;">${decision && decision.note ? decision.note : ''}</textarea>
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
      <div class="co-body"><div class="co-label">${opt.label}</div><div class="co-text">${opt.text}</div></div>`;
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
    // Empty is only meaningful (and allowed) for 'insert' opcode candidates
    // (unverified_insertion - stored text has a word docai never saw) -
    // there it means "remove this, accept the omission." For every other
    // opcode an empty custom answer isn't a real decision, just an
    // unfilled field.
    if (!text && corr.opcode !== 'insert') { alert('Enter the custom reading first.'); return; }
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
  const record = await res.json();

  // Reflect immediately without a full reload: patch the in-memory
  // correction entry and re-render this klal's word span.
  const k = mountedKlal[klalId];
  const entry = k.corrections.find(c => c.word_index === corr.word_index);
  if (entry) entry.current_decision = record;
  const block = document.getElementById('klal-block-' + klalId);
  if (block) renderKlalBody(block, k);

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
          <div class="h-text">${h.chosen_text || ''}</div>
          ${h.note ? `<div class="h-note">${h.note}</div>` : ''}
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

  klalFlagPanelBody.innerHTML = `
    <div class="panel-section">
      <div class="panel-label">Klal ${klalId}</div>
      <div class="checkbox-row">
        <input type="checkbox" id="needs-revisit-checkbox" ${state.needs_revisit ? 'checked' : ''}>
        <label for="needs-revisit-checkbox">Needs revisit</label>
      </div>
    </div>
    <div class="panel-section">
      <div class="panel-label">Note</div>
      <textarea id="klal-flag-note" rows="4" placeholder="What needs a second look, and why?">${state.note || ''}</textarea>
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
    klalById[klalId].needs_revisit = needsRevisit;
    refreshNavItem(klalId);
    const block = document.getElementById('klal-block-' + klalId);
    const btn = block && block.querySelector('.klal-flag-btn');
    if (btn) { btn.classList.toggle('active', needsRevisit); btn.textContent = needsRevisit ? '⚑ flagged' : '⚑ flag'; }
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
            ${h.note ? `<div class="h-note">${h.note}</div>` : ''}
          </div>`).join('')
      : '<p style="color:var(--ink-faint);font-size:12px;">No history yet.</p>';
    list.style.display = 'block';
    toggle.textContent = 'Hide history';
  };
}

// ---------- scan pane ----------
let currentPage = null;
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
  updatePageNavButtons();
  hlContainer.innerHTML = '';

  const focusKlal = mountedKlal[focusKlalId];
  if (focusKlal && focusKlal.region) {
    const r = focusKlal.region;
    const box = document.createElement('div');
    box.className = 'hl-current-klal';
    box.style.left = (r.x1 * 100) + '%';
    box.style.top = (r.y1 * 100) + '%';
    box.style.width = ((r.x2 - r.x1) * 100) + '%';
    box.style.height = ((r.y2 - r.y1) * 100) + '%';
    hlContainer.appendChild(box);
  }

  const pageCorrections = await fetch('/api/page/' + page).then(r => r.json());
  pageCorrections.forEach(c => {
    if (!c.bbox) return;
    const box = document.createElement('div');
    box.className = 'hl-box' + (c.klal_id === focusKlalId ? '' : ' dim');
    const [, color] = FLAGS[c.flag] || [null, '#a0aec0'];
    box.style.borderColor = color;
    box.style.background = color + '33';
    box.style.left = (c.bbox.x1 * 100) + '%';
    box.style.top = (c.bbox.y1 * 100) + '%';
    box.style.width = ((c.bbox.x2 - c.bbox.x1) * 100) + '%';
    box.style.height = ((c.bbox.y2 - c.bbox.y1) * 100) + '%';
    attachWordHandlers(box, c.klal_id, c);
    hlContainer.appendChild(box);
  });
}

const pagesWithKlalim = () => Array.from(new Set(KLALIM.filter(k => k.page).map(k => k.page))).sort((a, b) => a - b);
const firstKlalOfPage = {};
function buildFirstKlalOfPage() {
  KLALIM.forEach(k => { if (k.page && !(k.page in firstKlalOfPage)) firstKlalOfPage[k.page] = k.klal_id; });
}

function updatePageNavButtons() {
  const pages = pagesWithKlalim();
  const idx = pages.indexOf(currentPage);
  document.getElementById('page-nav-prev').disabled = idx <= 0;
  document.getElementById('page-nav-next').disabled = idx === -1 || idx >= pages.length - 1;
}
function goToPageOffset(offset) {
  const pages = pagesWithKlalim();
  const idx = pages.indexOf(currentPage);
  if (idx === -1) return;
  const targetPage = pages[idx + offset];
  if (targetPage == null) return;
  const targetKlal = firstKlalOfPage[targetPage];
  if (targetKlal != null) jumpTo(targetKlal);
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
  if (navEl) navEl.classList.add('active');
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
