// Yad Malachi review dashboard frontend. Fetches data lazily from
// review_server.py's JSON API instead of having it all inlined - see
// PROJECT-STATUS.md "Review dashboard rearchitecture" for why.

let FLAGS = {};
let KLALIM = [];          // lightweight list from /api/klalim
let klalById = {};
let mountedKlal = {};     // klal_id -> full payload once fetched
let fetchInFlight = {};   // klal_id -> Promise, avoids double-fetch races
let WITNESS_PAGES = [];   // {page, klal_id, total, decided} from /api/witness - continuation-only
// {n: Hebrew numeral} from /api/numerals, for the scan header's Hebrew half.
// DECLARED HERE, with the other init()-populated globals, and NOT beside the
// header code that uses it: as a `let` further down the file than init()'s own
// assignment it was re-initialised to {} on the synchronous pass and the fetched
// table was silently discarded - the header rendered `דף 73` instead of `דף עג`
// with no error, since hebNum() falls back to the digits. Caught by asserting
// the rendered text, not by reading the code (Lesson 19).
let NUMERALS = {};
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

const HEBREW_LETTER_RE = /[\u05D0-\u05EA]/g;
function hebrewLettersOnly(s) {
  return (s || '').match(HEBREW_LETTER_RE)?.join('') || '';
}

// A suggestion is offered to a reviewer as a one-click replacement for a real
// word in a 174-year-old text, so it has to be a WORD, not whatever happened to
// sit after the first arrow in a prose note.
//
// FIXED 2026-08-25, reported by the reviewer as "klal 1 word 229 - proposed
// correction is a serious bug", and it was: the panel offered to replace
// `דנראח` with `6.18M`. The note for that flag says the reference corpus grew
// "2.58M->6.18M words" and, further along, that the stored form is one
// substitution "('ח'->'ה') away from 'דנראה'". The old rule took the first
// `->` in the string and captured the token after it, so it proposed a
// FILE-SIZE FIGURE as Hebrew scripture - and the "Use ..." button saved it on
// one click without a confirmation step.
//
// Swept before fixing: of 261 open word-level flags carrying a suggestion,
// **39 proposed something with no Hebrew letter in it at all** (12 of them the
// literal `6.18M`) and **27 proposed a string containing `?`** (the detectors
// write `word wNNN → ??` when they have no candidate). Klal 1 word 229 is the
// first klal of the work.
function suggestionIsPlausible(suggestion, currentWord) {
  if (!suggestion) return false;
  if (suggestion.indexOf('?') !== -1) return false;      // "→ ??" means the detector had none
  const letters = hebrewLettersOnly(suggestion);
  if (!letters) return false;                            // "6.18M", "ב.", a bare number
  if (!currentWord) return true;
  const wordLetters = hebrewLettersOnly(currentWord);
  // A single letter proposed for a multi-letter word is the ('ח'->'ה')
  // confusion-pair notation being read as a replacement, not a reading.
  if (letters.length === 1 && wordLetters.length > 1) return false;
  // "Proposes what is already there" - but compared RAW, not letters-only.
  // FIXED 2026-08-26 (code review): hebrewLettersOnly() strips the gershayim,
  // so a suggestion that only MOVES one was judged identical to the word and
  // silently dropped. Misplaced gershayim is a real repair class in this print,
  // not detector noise. Swept all open flags before loosening this: exactly two
  // proposals differ from their word in punctuation alone, and both are valid -
  // klal 45 w21 `נלפ"קד` -> `נלפק"ד` and klal 212 w40 `פ"יא` -> `פי"א`. No noise
  // is admitted by the change; the `?`, no-Hebrew-letter and single-letter
  // guards above are what filter the junk, and they are untouched.
  if (suggestion.trim() === currentWord.trim()) return false;
  return true;
}

function extractSuggestedWord(reasoning, currentWord) {
  if (!reasoning) return null;
  if (typeof reasoning === 'object') {
    currentWord = currentWord || reasoning.final_text;
    reasoning = reasoning.reasoning || (reasoning.current_decision && reasoning.current_decision.note) || reasoning.note;
  }
  if (!reasoning || typeof reasoning !== 'string') return null;

  const candidates = [];
  // 1. The detectors' own canonical form, anchored on the flagged word and its
  // index: "בפיק w427 → בפ\"ק". This is the only arrow that is a proposal;
  // every other arrow in these notes is prose.
  const mAnchored = reasoning.match(/(?:^|\|)\s*\S+\s+w\d+\s*(?:→|->)\s*['"״׳]?([^\s|]+)/);
  if (mAnchored) candidates.push(mAnchored[1]);
  // 2. Prose patterns, which name the attested word explicitly.
  // The quote class includes a BACKTICK. validate_part1_corpus_integrity.py
  // writes its proposals as ``'&' w338 -> REPLACE with `אל` `` - so pattern 1
  // captured the literal word "REPLACE", which has no Hebrew letter and was
  // dropped, and the panel offered nothing at all (reviewer, 2026-08-30: "did
  // not surface the recommended word from the note"). Four open flags were
  // silently suggestion-less that way, three of them the `&` -> `אל` ligature
  // repairs.
  //
  // Deliberately NOT "take the first backticked token": swept all 25 open flags
  // whose anchored capture is non-Hebrew, and in most of them the backticks hold
  // CONTEXT, not a proposal - klal 39 w252's `יד מלאכי כללי האלף` is the folio
  // header it wants deleted, klal 74 w416's `אמר` is the catchword, klal 176
  // w694's is "PROBABLY CORRECT AS TRANSCRIBED - do not delete". A bare-backtick
  // rule would put a wrong word in the box more often than a right one. Anchoring
  // on the verb `replace ... with` is what makes the proposal a proposal.
  const prose = [
    /away from ['"`]([^'"`]+)['"`]/i,
    /suggests? ['"`]([^'"`]+)['"`]/i,
    /['"`]([^'"`]+)['"`]\s*\(\d+x independently attested\)/i,
    /replaces? (?:with )?['"`]([^'"`]+)['"`]/i,
  ];
  for (const re of prose) {
    const m = reasoning.match(re);
    if (m) candidates.push(m[1]);
  }
  // 3. Any remaining arrow, last and least - kept so an older note shape still
  // yields something, but it now has to survive the same plausibility check.
  const mArrow = reasoning.match(/(?:→|->)\s*['"״׳]?([^\s|'"״׳]+)/);
  if (mArrow) candidates.push(mArrow[1]);

  for (const c of candidates) {
    const trimmed = (c || '').trim().replace(/^['"״׳]|['"״׳]$/g, '');
    if (suggestionIsPlausible(trimmed, currentWord)) return trimmed;
  }
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
// Flags meaning "the machine settled this". Must stay in sync with
// review_server.MACHINE_RESOLVED_FLAGS - a flag in one list and not the other
// renders the same word with two different verdicts on one screen.
const MACHINE_RESOLVED_FLAGS = ['current_text_confirmed', 'docai_ligature_artifact'];

function wordState(corr) {
  // GUARD added 2026-08-17 (code review): renderKlalBody() branches on
  // opcode === 'ai_flag' before this ever runs, so it's not reachable
  // today - but an ai_flag's current_decision is the AI's OWN klal_flag
  // record, not a human decision, and this function has no other way to
  // tell the difference. If a future code path ever calls wordState() on
  // one directly, it must not silently render an unresolved AI flag as
  // Human-Decided.
  // An ai_flag's current_decision is the AI's OWN klal_flag record, never a
  // human decision - hence the early return. But a flag the server marks
  // `flag_answered` HAS a human decision at that word, recorded after the flag
  // was raised; it renders here at all only because its richer entry is gone
  // (a consensus dispute the synthesizer drops once decided). Showing it as an
  // open dispute puts a red word on a position the reviewer already ruled on -
  // which is the klal 163 report in a second costume.
  if (corr.opcode === 'ai_flag') return corr.flag_answered ? 'human' : 'open';
  // An UNANSWERED word-level flag makes the word open, whatever else the entry
  // also is. api_klal() merges a flag onto a richer entry at the same index as
  // `word_flag` rather than appending a second one, and only the ai_flag branch
  // above ever looked at it - so a flag sitting on a machine candidate rendered
  // by the candidate's own verdict. Seven words carried an open flag and showed
  // AMBER, "the machine settled this", which is the one colour that tells a
  // reviewer to move on. Reported 2026-08-30 on klalim 62 and 70: "two flagged
  // words in the center but the correction pane showed 1 red flag".
  // `answered` is computed server-side (_flag_answered_by_a_later_decision) and
  // carried on the overlay; a flag a later decision already answered stays out
  // of this and renders as decided, which is the klal 163 case.
  if (corr.word_flag && !corr.word_flag.answered) return 'open';
  if (corr.current_decision) return 'human';
  if (MACHINE_RESOLVED_FLAGS.includes(corr.flag)) return 'machine';
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
  const machine = MACHINE_RESOLVED_FLAGS.includes(corr.flag) ? STATE_META.machine.label : STATE_META.open.label;
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


// ---------- copyable word reference ----------
//
// ADDED 2026-08-26 (reviewer request): the klal/word header in a correction
// panel doubles as a copy control, handing over both the human-readable
// reference and the deep link in one go:
//
//     Klal 66 · Word #135 — ע"ס
//     http://127.0.0.1:8420/#klal=66&word=135
//
// so a finding can be pasted into a note, a status entry or a message without
// anyone retyping an index.
// The title as a LIST label: no terminal period. One place, so every surface
// that shows a title in a list agrees.
function displayTitle(title) {
  return (title || '').replace(/\.\s*$/, '');
}

function klalRefName(klalId) {
  // "Klal 66 (סו)" - the id a reviewer navigates by, plus the marker the BOOK
  // prints, which is what they are actually looking at on the scan. ADDED
  // 2026-08-26 at the reviewer's request.
  const g = (klalById[klalId] || {}).gematria;
  return `Klal ${klalId}` + (g ? ` (${g})` : '');
}

function wordRefLabel(klalId, wordIndex, word, prefix) {
  const label = `${prefix || ''}${klalRefName(klalId)} &middot; Word #${wordIndex}`;
  return `<div class="panel-label panel-label-copy">${label}` +
         `<button class="copy-ref" type="button" title="Copy reference and link"` +
         ` data-klal="${klalId}" data-word="${wordIndex}"` +
         ` data-text="${escapeAttr(word == null ? '' : String(word))}"` +
         `>&#128203;</button></div>`;
}

function wordRefPayload(klalId, wordIndex, word) {
  // The PATH form, not the hash form: it survives being pasted into a terminal
  // or a chat window, where `&` is routinely truncated. The server 302s it.
  const url = `${location.origin}/klal/${klalId}/word/${wordIndex}`;
  const head = `${klalRefName(klalId)} · Word #${wordIndex}` + (word ? ` — ${word}` : '');
  return `${head}\n${url}`;
}

async function copyText(text) {
  // navigator.clipboard needs a secure context. http://127.0.0.1 counts as one,
  // but not every browser/profile agrees, and a copy button that silently does
  // nothing is exactly the dead control this file has shipped twice already -
  // so there is a fallback rather than a bare await.
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch (e) { /* fall through */ }
  try {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.setAttribute('readonly', '');
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    const ok = document.execCommand('copy');
    document.body.removeChild(ta);
    return ok;
  } catch (e) {
    return false;
  }
}

document.addEventListener('click', async (e) => {
  const btn = e.target.closest && e.target.closest('.copy-ref');
  if (!btn) return;
  e.stopPropagation();               // must not bubble into dismissPanels()
  const payload = wordRefPayload(btn.dataset.klal, btn.dataset.word, btn.dataset.text);
  const ok = await copyText(payload);
  btn.classList.add(ok ? 'copied' : 'copy-failed');
  const before = btn.innerHTML;
  btn.innerHTML = ok ? '&#10003;' : '&#10007;';
  setTimeout(() => { btn.innerHTML = before; btn.classList.remove('copied', 'copy-failed'); }, 1400);
});


// ---------- transient status toast ----------
//
// ADDED 2026-09-01, for the copy-on-click confirmation below. A copy that
// succeeds silently is indistinguishable from one that failed - the dead-control
// failure copyText()'s own note above records this file shipping twice - and the
// feedback that already exists (a checkmark swapped into the .copy-ref button
// that was clicked) has no button to live in when the trigger is the WORD ITSELF.
// role="status" so a screen reader announces it without stealing focus from the
// text the reviewer is reading.
const toastEl = document.createElement('div');
toastEl.id = 'toast';
toastEl.setAttribute('role', 'status');
toastEl.style.display = 'none';
document.body.appendChild(toastEl);
let toastTimer = null;

function showToast(message, ok) {
  toastEl.textContent = message;
  toastEl.classList.toggle('toast-fail', ok === false);
  toastEl.style.display = 'block';
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { toastEl.style.display = 'none'; }, 1800);
}


// ---------- copy a word's link on click ----------
//
// ADDED 2026-09-01 (reviewer: "clicking on a word should push the url for that
// word into the clipboard, with a popup message saying so ... should be a flag
// to disable this behavior").
//
// Hooked into focusWordOnScan() rather than into the six click handlers: that
// function is already the single funnel every word click passes through, and
// already the one place that maintains the address bar, so the link copied is
// the same address the hash is set to BY CONSTRUCTION instead of by a second
// formatter that can drift from it. The payload is wordRefPayload()'s path form
// - byte-identical to what the hover card's clipboard button has produced since
// 2026-08-26. Two copy affordances yielding different text for the same word
// would be worse than having only one.
//
// The OFF-SWITCH is a checkbox in the nav filter, persisted in localStorage so
// it survives the reload every review_server.py restart forces. Opt-OUT
// (default on) because that is what was asked for. Every localStorage access is
// wrapped: a profile with site data blocked THROWS on read, and an exception
// here would take the click handler - and so the panel - down with it.
const COPY_ON_CLICK_KEY = 'ym.copyWordLinkOnClick';
let copyOnClick = true;
// True only while highlightRoutedWord() is synthesizing a click from a URL.
// See its own note: the deep-link path wants everything a click does EXCEPT the
// clipboard write.
let _routedClick = false;

function setupSettingsTray() {
  const btn = document.getElementById('settings-btn');
  const tray = document.getElementById('settings-popover');
  if (!btn || !tray) return;
  const setOpen = (open) => {
    tray.hidden = !open;
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
  };
  btn.onclick = (e) => {
    e.stopPropagation();
    setOpen(tray.hidden);
  };
  // Clicking anywhere else puts it away. Not on the tray itself - the reviewer
  // is in there to flip a switch, and a tray that closes on the click that flips
  // it is a control you have to reopen to confirm.
  document.addEventListener('click', (e) => {
    if (tray.hidden) return;
    if (e.target.closest('#settings-popover') || e.target.closest('#settings-btn')) return;
    setOpen(false);
  });
}

function setupCopyOnClickToggle() {
  try {
    copyOnClick = localStorage.getItem(COPY_ON_CLICK_KEY) !== '0';
  } catch (e) {
    copyOnClick = true;
  }
  const box = document.getElementById('filter-copy-link');
  if (!box) return;
  box.checked = copyOnClick;
  box.onchange = () => {
    copyOnClick = box.checked;
    try { localStorage.setItem(COPY_ON_CLICK_KEY, copyOnClick ? '1' : '0'); } catch (e) { /* not fatal */ }
    showToast(copyOnClick ? 'Copying each word\u2019s link on click'
                          : 'Copy-on-click off');
  };
}

// The word as it is actually rendered. focusWordOnScan() gets a correction, not
// a span, and a correction does not reliably carry the surface word (a plain
// word's is synthesized on the spot, and a candidate's `final_text` can be a
// multi-word replacement). The klal is always mounted by the time a word in it
// can be clicked, so read it off the DOM - the same source the hover card's own
// copy button uses (span.textContent), which is what keeps the two payloads
// identical.
function wordTextAt(klalId, wordIndex) {
  const block = document.getElementById('klal-block-' + klalId);
  const span = block && block.querySelector(`[data-word-index="${wordIndex}"]`);
  return span ? (span.textContent || '').trim() : '';
}

async function copyWordLink(klalId, wordIndex) {
  if (!copyOnClick || _routedClick || klalId == null || wordIndex == null) return;
  const ok = await copyText(wordRefPayload(klalId, wordIndex, wordTextAt(klalId, wordIndex)));
  showToast(ok ? `Link copied \u2014 ${klalRefName(klalId)} \u00b7 Word #${wordIndex}`
               : 'Could not copy the link to the clipboard', ok);
}


// ---------- hover card on every word ----------
//
// ADDED 2026-08-26 (reviewer: "hovering over any word should always surface a
// floating box with the klal + word and an icon to copy the link"). Every word
// in the text pane is addressable, so every word should say what its address IS
// without having to be clicked - previously only flagged words said anything,
// and only through a native `title` tooltip that cannot hold a button.
//
// It is a HOVERABLE card, not a tooltip: `#tooltip` sets `pointer-events: none`
// precisely so it never swallows a click, which makes it the wrong element for
// something containing a control. The card therefore keeps itself open while the
// pointer is over it, with a short grace period so the pointer can cross the gap
// from the word.
//
// The word's own `title` (a flagged word's reasoning) is MOVED into the card and
// the attribute cleared, so the browser's native tooltip does not also appear -
// two floating boxes over one word is worse than none.
const wordCard = document.createElement('div');
wordCard.id = 'word-card';
wordCard.style.display = 'none';
document.body.appendChild(wordCard);

let wordCardHideTimer = null;
let wordCardFor = null;

function hideWordCard(immediate) {
  clearTimeout(wordCardHideTimer);
  const go = () => { wordCard.style.display = 'none'; wordCardFor = null; };
  if (immediate) go(); else wordCardHideTimer = setTimeout(go, 260);
}

function showWordCard(span, klalId) {
  const wi = span.dataset.wordIndex;
  if (wi == null) return;
  clearTimeout(wordCardHideTimer);
  if (wordCardFor === span) return;                 // already showing for this word
  wordCardFor = span;
  // Take over the native tooltip so only one box appears.
  if (span.getAttribute('title')) {
    span.dataset.detail = span.getAttribute('title');
    span.removeAttribute('title');
  }
  // A flagged word gets the FULL detail here rather than in a second floating
  // box - see attachWordHandlers' note on skipTooltip. A plain word falls back
  // to whatever native title it carried, which is usually nothing.
  const corr = span._corr;
  const detail = corr
    ? wordDetailHtml(corr, span._isGap)
    : (span.dataset.detail ? `<span class="t-conf">${escapeHtml(span.dataset.detail)}</span>` : '');
  const status = corr ? `<span class="wc-status">${escapeHtml(statusLabel(corr))}</span>` : '';
  wordCard.innerHTML =
    `<div class="wc-head">` +
      `<span class="wc-ref">${klalRefName(klalId)} &middot; Word #${wi}</span>` +
      status +
      `<button class="copy-ref" type="button" title="Copy reference and link"` +
      ` data-klal="${klalId}" data-word="${wi}"` +
      ` data-text="${escapeAttr(span.textContent || '')}">&#128203;</button>` +
    `</div>` +
    (detail ? `<div class="wc-detail">${detail}</div>` : '');
  wordCard.classList.toggle('wc-rich', !!corr);
  wordCard.style.display = 'block';
  const r = span.getBoundingClientRect();
  const w = wordCard.offsetWidth, h = wordCard.offsetHeight;
  let left = r.left + r.width / 2 - w / 2;
  left = Math.max(8, Math.min(left, window.innerWidth - w - 8));
  let top = r.top - h - 8;
  if (top < 8) top = r.bottom + 8;                  // flip below when it would clip
  wordCard.style.left = left + 'px';
  wordCard.style.top = top + 'px';
}

textScroll.addEventListener('mouseover', (e) => {
  const span = e.target.closest && e.target.closest('[data-word-index]');
  if (!span || !textScroll.contains(span)) return;
  const block = span.closest('[data-klal-id]');
  if (!block) return;
  showWordCard(span, block.dataset.klalId);
});
textScroll.addEventListener('mouseout', (e) => {
  const span = e.target.closest && e.target.closest('[data-word-index]');
  if (!span) return;
  if (e.relatedTarget && wordCard.contains(e.relatedTarget)) return;   // moved onto the card
  hideWordCard(false);
});
wordCard.addEventListener('mouseenter', () => clearTimeout(wordCardHideTimer));
wordCard.addEventListener('mouseleave', () => hideWordCard(false));
// A click anywhere that is not the copy button dismisses it, so the card never
// sits over the text the reviewer is trying to read.
document.addEventListener('click', (e) => {
  if (e.target.closest && e.target.closest('.copy-ref')) return;
  hideWordCard(true);
});

// ---------- deep links ----------
//
// ADDED 2026-08-26 (reviewer request). A klal, or a klal and a word, can be
// addressed directly:
//     http://127.0.0.1:8420/#klal=66
//     http://127.0.0.1:8420/#klal=66&word=135
// so a finding recorded anywhere - a status entry, a report, a message - can
// carry a link that lands on the exact word instead of "klal 66, count to 135".
//
// The part is derived from the klal id rather than being part of the URL: a
// link to klal 400 must work whether or not the reviewer happens to be looking
// at Part 2 (the nav only holds one part at a time). Same boundaries as
// review_server._get_part_num_for_klal.
//
// The hash is also kept up to date as the reviewer navigates, via
// history.replaceState so scrolling does not fill the back button with
// hundreds of entries - the address bar is then always copyable as-is.
function partForKlal(klalId) {
  if (klalId <= 222) return '1';
  if (klalId <= 444) return '2';
  return '3';
}

function parseHashRoute() {
  const h = (location.hash || '').replace(/^#/, '');
  if (!h) return null;
  const p = new URLSearchParams(h);
  const klal = parseInt(p.get('klal'), 10);
  if (!Number.isInteger(klal)) return null;
  const word = parseInt(p.get('word'), 10);
  return { klal, word: Number.isInteger(word) ? word : null };
}

function updateHash(klalId, wordIndex) {
  if (!klalId) return;
  const h = wordIndex == null ? `#klal=${klalId}` : `#klal=${klalId}&word=${wordIndex}`;
  if (location.hash !== h) history.replaceState(null, '', h);
}

// Clear the ring wherever it is. Exported as a function rather than inlined
// because three call sites need it and a missed one leaves two rings up.
function clearRoutedWord(except) {
  document.querySelectorAll('.routed-word').forEach(el => {
    if (el !== except) el.classList.remove('routed-word');
  });
}

// Scroll the text pane to a word and ring it. FIX 2026-08-31, reviewer:
// "clicking on the highlighted word in the scan does not highlight the same
// word in the text". The text->scan direction had a single funnel
// (focusWordOnScan) and the scan->text direction had NOTHING - a scan box's
// click opened the decision panel and moved the scan, and the middle pane was
// never told. This is that missing funnel, and the deep-link router now shares
// it rather than keeping a second copy of the same four lines.
async function revealWordInText(klalId, wordIndex) {
  await mountKlal(klalId);
  const block = document.getElementById('klal-block-' + klalId);
  if (!block) return null;
  const span = block.querySelector(`[data-word-index="${wordIndex}"]`);
  if (!span) return null;                  // out of range, or the klal has no text
  // Hold the scroll observer off: this scroll would otherwise drift the active
  // klal (and its scan page) off the word we are pointing at - the same hazard
  // the deep-link router documents above.
  suppressObserverScroll = true;
  clearTimeout(suppressTimer);
  span.scrollIntoView({ behavior: 'auto', block: 'center' });
  suppressTimer = setTimeout(() => { suppressObserverScroll = false; }, 900);
  // A ring, not a state class: the word's real state (open, decided,
  // machine-resolved) must keep owning its colour.
  // FIXED 2026-08-31 (reviewer: "if i move my cursor over the text the highlight
  // disappears"). It was not the cursor - the ring carried a hard
  // setTimeout(..., 4000) and simply expired, which happens to land about when
  // a reviewer has finished reading the line and started moving the mouse, so
  // the two read as cause and effect. Measured: the ring survives a mouse move
  // at 900ms and is gone by 4s with the pointer untouched. It now persists until
  // the reviewer actually goes somewhere else.
  clearRoutedWord(span);
  span.classList.add('routed-word');
  return span;
}

async function highlightRoutedWord(klalId, wordIndex, opts) {
  const span = await revealWordInText(klalId, wordIndex);
  if (!span) return;
  if (opts && opts.fromList) {
    // Reveal and focus only - see the word list's own click handler for why a
    // row must not open the word's panel.
    const page = pageForWord(klalForPageLookup(klalId), wordIndex, null);
    if (page != null) {
      focusWordOnScan(page, klalId, { klal_id: klalId, word_index: wordIndex, opcode: 'plain' },
                      { viaClick: false });
    }
    return;
  }
  // FIXED 2026-09-01 (reviewer: "klal 12 w 219 clicking does not show that word
  // highlighted" - reached from a list row, which is a deep link).
  //
  // These four lines were a hand-rolled second copy of pageForWord(), and its
  // word_pages branch COULD NOT FIRE: `klalById` is built from /api/klalim,
  // whose payload has no `word_pages` key at all (only /api/klal carries it), so
  // the test was always false and every deep link fell through to the klal's
  // START page. Klal 12 word 219 lives on page 19 and the link showed page 18,
  // where the word has no box - so nothing highlighted, with no error.
  //
  // Lesson 25 exactly: a condition that cannot be true is not a fallback, it is
  // dead code wearing one. Swept: 18,044 words across 55 klalim sit on a page
  // other than their klal's start page, and every deep link to one of them was
  // landing on the wrong page.
  //
  // pageForWord() now, against the MOUNTED klal - revealWordInText() has just
  // awaited mountKlal(), so mountedKlal[klalId] is the /api/klal payload that
  // does carry word_pages.
  // A URL THAT NAMES A WORD BEHAVES LIKE CLICKING THAT WORD (reviewer,
  // 2026-09-02). It used to only reveal and highlight, so following a link left
  // the reviewer looking at the right word with no way to act on it - they had
  // to click the word they had just been taken to.
  //
  // The click is DISPATCHED on the span rather than reimplemented, deliberately.
  // Five different render branches attach five different handlers (disputed,
  // manual, ai_flag, witness, plain), and picking the right one here would be a
  // sixth copy of that mapping - which is the exact defect the comment above
  // records fixing in this very function. Dispatching cannot pick wrong.
  //
  // `_routedClick` suppresses only the clipboard write. A real click copies the
  // word's URL; doing that here would be pointless (the reviewer HAS the URL -
  // they just opened it) and would usually fail anyway, because a page loaded
  // cold from a link has no transient user activation and the browser rejects
  // the clipboard write - which would put a "Could not copy" toast on screen
  // every time someone followed a link.
  _routedClick = true;
  try {
    span.click();
  } finally {
    _routedClick = false;
  }
}

let routing = false;

// Route to a klal, optionally to a word inside it. THE one implementation;
// applyHashRoute() is the thin wrapper that reads an address off the URL.
//
// SPLIT 2026-09-02, to take the word list off the hash entirely. The row handler
// used to set `location.hash` and then call applyHashRoute({fromList: true}),
// and setting the hash queues a hashchange TASK that calls applyHashRoute again
// with no options. The `routing` guard was supposed to swallow that second call,
// and usually did - but only while the first was still in flight. When the klal
// is ALREADY MOUNTED every await inside resolves as a microtask, the whole route
// finishes before the macrotask queue is reached, `routing` is false again, and
// the hashchange runs the full click path: the row opened the word's panel,
// which closes the list the row lives in.
//
// That is why the test passed alone and failed in the suite - whether klal 1 was
// already mounted decided it. Routing directly means no hashchange is ever
// queued: updateHash() uses replaceState, which fires no event.
async function routeToKlal(klalId, wordIndex, opts) {
  if (routing) return;
  const route = { klal: klalId, word: wordIndex };
  routing = true;
  try {
    const want = partForKlal(route.klal);
    if (want !== currentPart) {
      const sel = document.getElementById('part-select');
      if (sel) sel.value = want;
      await switchPart(want);
    }
    if (!klalById[route.klal]) return;     // not in this corpus
    // The scroll observer calls setActiveKlal on whatever drifts into view, so a
    // SMOOTH scroll lets it overwrite the destination before the animation ends
    // - measured: routing to klal 66 landed on 61. Mount first, jump instantly,
    // and hold the observer off until everything has settled.
    suppressObserverScroll = true;
    clearTimeout(suppressTimer);
    manualPageLock = false;
    await mountKlal(route.klal);
    const block = document.getElementById('klal-block-' + route.klal);
    if (block) block.scrollIntoView({ behavior: 'auto', block: 'start' });
    lastActiveKlalId = route.klal;
    lastActiveScanPage = klalById[route.klal] ? klalById[route.klal].page : null;
    setActiveKlal(route.klal, 'center');
    if (route.word != null) {
      await highlightRoutedWord(route.klal, route.word, opts);
    }
    updateHash(route.klal, route.word);    // last word wins, not the observer
    suppressTimer = setTimeout(() => { suppressObserverScroll = false; }, 900);
  } finally {
    routing = false;
  }
}

async function applyHashRoute() {
  const route = parseHashRoute();
  if (!route) return;
  return routeToKlal(route.klal, route.word);
}

// ---------- the book this dashboard has loaded ----------
//
// ADDED 2026-09-01 (reviewer: "on index pane header should show book title also
// scan pane"). Fetched from /api/corpus rather than written into index.html:
// this pipeline is built to generalize past one work, and a title in the markup
// is one more place a second book would have to be edited.
//
// Both surfaces get the HEBREW title first. That is the same reasoning the nav
// already applies to klal markers - the reviewer is matching what they see
// against the printed page, and the page says `יד מלאכי`, not "Yad Malachi".
let CORPUS = null;

// Fill the title slots in EVERY pane header at once.
//
// REWRITTEN 2026-09-01 (reviewer: "text differs between two blue headers ...
// both headers same size and shape"). Each pane used to build its own title
// markup, which is precisely how the two bars came to say different things in a
// different order. There is now one slot vocabulary - `[data-slot]` - and one
// function that fills it, so a pane cannot have a title the others do not.
function renderBookTitle() {
  if (!CORPUS) return;
  const heb = CORPUS.title_he || '';
  const eng = CORPUS.title || '';
  // The edition, on hover only. It matters - START_HERE.md spends a section on
  // not confusing this Berlin reprint with the Livorno original - but it is not
  // what a reviewer needs on screen at all times, and three copies of it across
  // three bars is the clutter this pass is removing.
  const tip = [eng, CORPUS.section, CORPUS.edition].filter(Boolean).join(' \u2014 ');
  document.querySelectorAll('[data-slot="title-he"]').forEach(el => {
    el.textContent = heb; el.title = tip;
  });
  document.querySelectorAll('[data-slot="title-en"]').forEach(el => {
    el.textContent = eng; el.title = tip;
  });
  // The index pane's reference is the SECTION it is listing, which is the
  // standing answer to "what am I looking at" for that pane - the other two
  // panes' references move as you read, and this one does not.
  const navHe = document.getElementById('nav-ref-he');
  const navEn = document.getElementById('nav-ref-en');
  if (navHe) navHe.textContent = CORPUS.section_he || '';
  if (navEn) navEn.textContent = CORPUS.section || '';
}

// The text pane's reference: the klal being read, in both scripts, exactly as
// the scan pane names the page it is showing. ADDED 2026-09-01 with that pane's
// first header - it was the only one of the three without a bar, and the pane a
// reviewer spends the most time in was the one that never said where they were.
function updateTextHeader() {
  const he = document.getElementById('text-ref-he');
  const en = document.getElementById('text-ref-en');
  if (!he || !en) return;
  const kid = _headerKlalId;
  if (kid == null) { he.textContent = ''; en.textContent = ''; return; }
  he.textContent = 'כלל ' + hebNum(kid);
  en.textContent = 'Klal ' + kid;
}

async function init() {
  const [flags, klalim, witness, numerals, corpus] = await Promise.all([
    fetch('/api/flags').then(r => r.json()),
    fetch('/api/klalim?part=' + currentPart).then(r => r.json()),
    fetch('/api/witness').then(r => r.json()),
    // Fetched HERE and nowhere else, deliberately. The same three-fetch block
    // appears in init(), switchPart() and the post-decision refresh - and the
    // numeral table is a pure function of the integers, identical in every part
    // and constant for the life of the process, so re-fetching it on a part
    // switch would be two more copies of a request that can never return
    // anything new. (Adding it to switchPart FIRST is exactly the sibling-branch
    // mistake Lesson 34 describes: the header stayed in digits and the globals
    // init() sets still looked right, so the wrong edit read as a working one.)
    fetch('/api/numerals').then(r => r.json()),
    // Fetched here and nowhere else, for the same reason as the numeral table
    // directly above: the work's title is constant for the life of the process
    // and identical in every part, so re-fetching it on a part switch could
    // never return anything new.
    // `r.ok` is checked, and the failure is REPORTED. FIXED 2026-09-02 (reviewer:
    // "when i sync this repo on another machine no titles render ... is there
    // code still needing to be committed and pushed?" - no, there was not).
    // A server process started BEFORE /api/corpus existed answers 404 with a
    // JSON body, `r.json()` parses it happily, CORPUS becomes {error: ...}, and
    // every title renders as an empty string that `.ph-title:empty` then hides.
    // A deployment problem became a blank space with nothing in the console -
    // Lesson 26: a filter that HIDES is more dangerous than one that rewrites.
    fetch('/api/corpus').then(r => {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    }).catch(e => {
      console.error(
        `/api/corpus failed (${e.message}) - the pane headers will have no title. ` +
        'The usual cause is a review_server.py process that was started BEFORE ' +
        'this endpoint existed: restart the server after pulling.');
      return null;
    }),
  ]);
  FLAGS = flags;
  NUMERALS = numerals || {};
  CORPUS = corpus;
  renderBookTitle();
  KLALIM = klalim;
  klalById = Object.fromEntries(klalim.map(k => [k.klal_id, k]));
  WITNESS_PAGES = witness.pages || [];

  setupPartSelect();
  buildLegend();
  buildNav();
  buildPlaceholders();
  setupObserver();
  setupFilter();
  setupSettingsTray();
  setupCopyOnClickToggle();
  setupZoomPan();
  setupPanels();
  setupNavRefreshOnReturn();

  lastActiveKlalId = KLALIM[0].klal_id;
  setActiveKlal(lastActiveKlalId);

  // A link that was opened cold beats the default "first klal" landing.
  await applyHashRoute();
  window.addEventListener('hashchange', applyHashRoute);
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

// Which /api/word-states list stands behind each legend row. The names are the
// server's own state constants (review_counts.DECIDED/RESOLVED/DISPUTED), not a
// second vocabulary - a legend row whose bucket name does not exist on the
// server opens an empty list and says nothing about why.
const LEGEND_BUCKET = {
  open: 'machine_disputed',
  machine: 'machine_resolved',
  human: 'decided',
  ai: 'ai_flag',
};

function buildLegend() {
  legend.innerHTML = '';
  const totals = { open: 0, machine: 0, human: 0 };
  // RECORDED decisions, which is NOT what the three tri-state totals count.
  // See review_server.api_klalim's own note: decided_count is the number of
  // words rendered GREEN right now, and a decision stops rendering the moment
  // it is settled - the candidate entry is dropped by the rebuild, and an
  // applied manual correction fails the drift check because the word it names
  // is no longer there. Part 1 reads 51 green against 463 rulings recorded.
  // Both are true and they answer different questions, so the row shows both
  // rather than one replacing the other: swapping in the larger number would
  // break the tri-state identity (decided + resolved + disputed == total) that
  // test_nav_tristate_matches_what_each_word_actually_renders_as asserts, and
  // leaving only the smaller one is what made 51 read as "you have decided 51
  // words".
  let recorded = 0;
  KLALIM.forEach(k => {
    totals.open += k.machine_disputed_count || 0;
    totals.machine += k.machine_resolved_count || 0;
    totals.human += k.decided_count || 0;
    recorded += k.recorded_decision_count || 0;
  });
  // The Human-Decided row says WHICH human-decided count it is. The bare label
  // read as "you have decided 54 words", which is not what it counts - see
  // review_server.api_klalim's note on recorded_decision_count.
  const LEGEND_SUFFIX = { human: ' (still shown)' };
  const LEGEND_EXPLAIN = {
    open: 'Machine-Disputed \u2014 {n} words. An OCR engine or the multi-witness '
        + 'consensus reads something other than what the corpus stores, and nobody '
        + 'has ruled on it yet. This is the outstanding review queue.',
    machine: 'Machine-Resolved \u2014 {n} words. The pipeline settled these itself: '
           + 'either the scan was crop-checked and confirmed the stored reading, or '
           + 'the disagreement is a known printer-ligature artifact. No reviewer '
           + 'action is needed.',
    human: 'Human-Decided (still shown) \u2014 {n} words are DRAWN this colour right '
         + 'now. A ruling stops being drawn once it is settled, because the rebuild '
         + 'drops its candidate entry, so this is not the number of rulings on '
         + 'record - the next count along is.',
  };
  Object.entries(STATE_META).forEach(([state, { label, color }]) => {
    const shown = label + (LEGEND_SUFFIX[state] || '');
    const row = document.createElement('div');
    row.className = 'legend-row legend-clickable';
    row.dataset.bucket = LEGEND_BUCKET[state];
    row.dataset.label = shown;
    // The one-line legend hides the labels, so these ARE the vocabulary now -
    // without them the bar is five unexplained numbers (reviewer 2026-09-02:
    // "hovering over the counts on the bottom surface explanation"). Each says
    // what the state MEANS and what clicking does, not just its own name again.
    row.title = LEGEND_EXPLAIN[state].replace('{n}', totals[state])
              + `\n\nClick to list all ${totals[state]}.`;
    const shape = state === 'machine' ? 'border-radius:2px;border:1.5px dotted ' + color + ';background:transparent;' : 'background:' + color + ';';
    row.innerHTML = `<i style="${shape}"></i><span class="legend-label">${shown}</span><b class="legend-count">${totals[state]}</b>`;
    legend.appendChild(row);

    // ...and its own row directly beneath it, not a sentence hanging off it
    // (reviewer 2026-09-01: "one row human-decided (...) and the following row
    // human-decided (total recorded)"). No swatch: nothing on screen is painted
    // this colour, which is exactly the point of the row.
    if (state === 'human' && recorded) {
      const sub = document.createElement('div');
      sub.className = 'legend-row legend-row-sub legend-clickable';
      sub.dataset.bucket = 'recorded';
      sub.dataset.label = 'Every recorded ruling';
      sub.title = `Human-Decided (total recorded) \u2014 ${recorded} distinct word `
                + 'positions in this part carry a ruling on record, whether or not it is '
                + 'still drawn in the text. This is the number to quote for "how much has '
                + 'been reviewed".\n\nClick to review all of them: what each one chose, '
                + 'and whether the corpus reflects it.';
      sub.innerHTML = `<span class="legend-label">${label} (total recorded)</span>` +
                      `<b class="legend-count">${recorded}</b>`;
      legend.appendChild(sub);
    }
  });
  // AI-flagged words render with their own purple dashed underline style
  // (state-ai-flag in app.css) distinct from the three main states above.
  // Add a key so reviewers know what the colour means.
  const aiTotal = KLALIM.reduce((s, k) => s + (k.ai_flag_count || 0), 0);
  const aiRow = document.createElement('div');
  aiRow.className = 'legend-row legend-clickable';
  aiRow.dataset.bucket = LEGEND_BUCKET.ai;
  aiRow.dataset.label = 'AI-Flagged';
  aiRow.title = `AI-Flagged \u2014 ${aiTotal} words carry an open word-level revisit `
              + 'flag, raised by an automated pass rather than by a disagreement between '
              + 'engines. These are also counted in Machine-Disputed: the flag makes the '
              + `word open whatever its own entry says.\n\nClick to list all ${aiTotal}.`;
  aiRow.innerHTML = `<i style="border-bottom:3px dashed #805ad5;background:transparent;"></i><span class="legend-label">AI-Flagged</span><b class="legend-count">${aiTotal}</b>`;
  legend.appendChild(aiRow);
}

// ---------- nav pane ----------
function navItemInnerHtml(k) {
  const flagIcon = k.needs_revisit ? '<span class="nflag">&#9873;</span>' : '';
  // Two badges, not one undifferentiated count: red = still needs a
  // decision, green = already decided (a reviewer wants to know at a
  // glance how much of a klal's queue is actually done, not just how many
  // words were ever flagged).
  // FIXED 2026-08-25 (reviewer, klal 88: "i see 9 or more disputes but the
  // count in the right pane is 2"). This badge used `open_count`, which is
  // total - decided, so it counted MACHINE-RESOLVED words - which render GREEN,
  // needing nothing from a reviewer - as outstanding work. The legend two
  // functions up has always summed `machine_disputed_count` instead, so the
  // same word was "open" in the badge and "resolved" in the legend, and neither
  // matched the colours on screen. Klal 88 measured 26 highlighted words = 17
  // decided + 5 machine-resolved + 4 disputed: badge said 9, four were red.
  // The badge now counts what is actually red, which is what a reviewer is
  // looking for when they scan the nav for remaining work.
  // ALL THREE SLOTS, ALWAYS, and red first (reviewer 2026-09-02: "red pill first
  // on the left so they all line up. green orange always in their slot even if
  // nothing before it"). A badge was omitted entirely at zero, so the red count -
  // the only one asking for something - sat at a different x on every row and
  // the column could not be read down. An empty slot keeps its width and draws
  // nothing.
  //
  // The group is `direction: ltr` (see .ncounts), so DOM order IS left-to-right
  // order here even though the row around it is RTL. Red first therefore means
  // red leftmost, on every row, whatever the other two hold.
  const badge = (cls, n) =>
    `<span class="ncount ${cls}${n ? '' : ' ncount-empty'}">${n || ''}</span>`;
  const badges = '<span class="ncounts">'
    + badge('ncount-open', k.machine_disputed_count)
    + badge('ncount-machine', k.machine_resolved_count)
    + badge('ncount-decided', k.decided_count)
    + '</span>';
  const heb = k.gematria ? `<span class="nheb">${escapeHtml(k.gematria)}</span>` : '';
  // The terminal period is NOT shown here (reviewer 2026-08-31: "no period in
  // the index pane - it is needed in the text pane to sep the title from the
  // text"). It stays on the stored field, where the gated invariant requires it;
  // this is a presentation choice, so the strip happens at render time and the
  // data is untouched. In a list of 222 headings the period is noise; in the
  // running text it is the only thing marking where the heading stops.
  const shown = displayTitle(k.title);
  return `<span class="nid">${k.klal_id}</span>${heb}<span class="ntitle klal-title" title="${escapeAttr(k.title)}">${escapeHtml(shown)}</span>${flagIcon}${badges}`;
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
    if (onlyHighValue && (k?.machine_disputed_count === 0 && !k?.needs_revisit)) show = false;
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
    // NO title here, deliberately (reviewer 2026-08-31: "i didn't want the title
    // above the text"). The heading is not a separate string in the book - it IS
    // the klal's opening words, set in larger type - so showing it above the text
    // renders it twice. It is styled IN PLACE instead, see markTitleRun() below.
    // The section name is GONE from here (reviewer 2026-09-02: "drop the sec
    // name"). It never changes down the whole pane, and the header bar above
    // already names the work; a constant repeated 222 times is furniture, not
    // information. The two numerals are one size now ("make both numbers the
    // same size") - they are the same fact in two scripts, and sizing one above
    // the other implied a hierarchy that is not there.
    const kmark = k.gematria
      ? `כלל <span class="kid-n">${k.klal_id}</span> · <span class="kid-n">${escapeHtml(k.gematria)}</span>`
      : `כלל <span class="kid-n">${k.klal_id}</span>`;
    head.innerHTML = `<span class="kid">${kmark}</span>`;
    const flagBtn = document.createElement('button');
    flagBtn.className = 'klal-flag-btn' + (k.needs_revisit ? ' active' : '');
    // "flag" read as a STATUS rather than a control - which is what the reviewer
    // hit on klal 117, whose klal-level flag is clear and whose one word flag is
    // answered: nothing is flagged, and the button still said "flag". The verb
    // is explicit now, and only the active state says "Flagged".
    flagBtn.textContent = k.needs_revisit ? '⚑ Flagged' : '⚑ Flag klal';
    flagBtn.title = k.needs_revisit
      ? 'This klal is flagged for revisit - click to review or clear'
      : 'Flag this klal for revisit';
    flagBtn.onclick = (e) => { e.stopPropagation(); openKlalFlagPanel(k.klal_id); };
    head.appendChild(flagBtn);
    // ...and the word-level flags the INDEX pennant is counting, which the klal
    // button deliberately does not (it toggles the klal-level flag alone). Both
    // panes now tell the same story instead of answering different questions
    // with the same word - 15 of 222 klalim showed a pennant in the index and an
    // unflagged button here (reviewer: "117 shows flagged in the middle pane but
    // not in the index pane").
    //
    // `ai_flag_count` IS the open-word-level-flag count: api_klalim computes it
    // with the very rule that builds the pennant, and it is the name that field
    // has carried since word-level flags were only ever raised by an AI pass. A
    // second field on /api/klal would have been a second encoding of one rule,
    // which is this file's most-repeated defect - and the first attempt was
    // exactly that, and did not even render, because THIS head is built from the
    // nav payload and never saw it.
    const openWordFlags = k.ai_flag_count || 0;
    if (openWordFlags) {
      const wf = document.createElement('span');
      wf.className = 'klal-wordflags';
      wf.textContent = `⚑ ${openWordFlags} word${openWordFlags === 1 ? '' : 's'}`;
      wf.title = `${openWordFlags} word-level revisit flag(s) still open in this klal. `
               + 'This is what the index pennant is showing; clear them from each word\u2019s own panel.';
      head.appendChild(wf);
    }
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

// Style the klal's MARKER and its printed HEADING in place, inside the running
// text (reviewer 2026-08-31: "i want the text itself to have bold for counter
// and title in the diff font - right there in the text").
//
// Applied as a PASS OVER THE RENDERED SPANS rather than inside the word loop on
// purpose: that loop has five separate branches (plain word, ai_flag, disputed,
// manual, witness) and a word is styled by whichever one claimed it. Decorating
// from inside would mean the same two lines in five places - the shape this repo
// keeps finding as Lesson 13/34 - and a title word that happens to be disputed
// would silently miss out. Here it is one rule over the final DOM, so it cannot
// matter which branch drew the word.
//
// The span comes from the server (corpus_io.title_word_span), not from comparing
// strings here: the comparison has to skip editorial punctuation and normalise
// Hebrew, and a second copy of that in JS would drift.
function markTitleRun(body, k) {
  const spans = body.querySelectorAll('[data-word-index]');
  if (!spans.length) return;
  const n = k.title_word_count || 0;
  spans.forEach(el => {
    const i = parseInt(el.dataset.wordIndex, 10);
    if (i === 0) el.classList.add('klal-marker-word');
    else if (n && i <= n) el.classList.add('klal-title-word');
  });
  // The LAST heading word carries the gap that separates the heading from the
  // text, and the marker carries the gap before it (reviewer: "one more space
  // between count title and text in reading pane"). Tagged here rather than
  // matched with :last-of-type, which would pick the last span in the body
  // whether or not it belongs to the heading.
  if (n) {
    const last = body.querySelector(`[data-word-index="${n}"]`);
    if (last) last.classList.add('klal-title-end');
  }
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
    if (gapsBefore[i]) gapsBefore[i].forEach(c => {
      body.appendChild(makeGapMarker(k.klal_id, c));
      const accepted = c.current_decision && c.current_decision.chosen_text;
      if (accepted) {
        body.appendChild(makePendingInsertText(accepted));
        body.appendChild(document.createTextNode(' '));
      }
    });
    if (w === '[.]') {
      const mark = document.createElement('span');
      mark.className = 'editorial-mark';
      mark.textContent = '[.]';
      mark.title = 'Editorial insertion: not in the original print. Marks a title/explanation boundary the printer left unpunctuated.';
      // FIXED 2026-08-31 (reviewer: "36 w14 won't let me click on it - shows ?").
      // This branch returned early before the word ever got a data-word-index, so
      // an editorial mark was the one token in the text that could not be
      // addressed, hovered for its reference, deep-linked, or clicked - while
      // still consuming a word index, which is what made the reference look
      // wrong. It matters more now than it did: 17 more of these were inserted
      // today, one per klal that had no heading separator.
      // It gets the same click as a plain word - a reviewer must be able to
      // remove or change a mark this pipeline itself inserted.
      mark.dataset.wordIndex = i;
      mark.onclick = () => {
        const targetPage = pageForWord(k, i, null);
        focusWordOnScan(targetPage, k.klal_id, { klal_id: k.klal_id, word_index: i, opcode: 'plain' });
        openManualCorrectionPanel(k.klal_id, i, w, null);
      };
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
      // FIXED 2026-08-26 (code review). This hardcoded 'state-ai-flag', so the
      // `flag_answered` handling added to wordState() on 2026-08-25 never
      // reached the text pane - the scan pane (which does go through
      // wordState()) drew the word green and the nav badge counted it decided,
      // while the text pane kept the purple dashed open-flag treatment on the
      // same word. Live on 5 standalone answered flags: klal 4 w199/w364,
      // klal 163 w427/w573, klal 167 w24 - and klal 163 is the klal that fix
      // was written for.
      const aiState = wordState(corr);
      span.className = 'flag-word state-' + (aiState === 'human' ? 'human' : 'ai-flag');
      span.dataset.wordIndex = i;
      span.textContent = w;
      span.title = corr.reasoning || '';
      span.onclick = () => {
        // Show the klal's scan page with focused ring on the ai_flag's word.
        // Respect manualPageLock: if the reviewer manually navigated to a
        // continuation page, don't snap back to the start page.
        focusWordOnScan(pageForWord(k, i, corr), k.klal_id, corr);
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
      span.dataset.wordIndex = i;
      span.textContent = w;
      span.title = corr.docai_reading
        ? `DocAI: ${corr.docai_reading} | Tesseract: ${corr.tesseract_reading || '—'}`
        : '';
      span.onclick = () => {
        focusWordOnScan(pageForWord(k, i, corr), k.klal_id, corr);
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
      span.dataset.wordIndex = i;
      span.textContent = w;
      // FIXED 2026-08-25 (reviewer, klal 4: "clicking on word 95 does not
      // highlight that word"). Every sibling branch here - ai_flag, witness,
      // candidate, plain - calls showPage() before opening its panel; this one
      // opened the panel and left the scan pane wherever it was. The word's box
      // is served (api_page's plain-word pass has always covered it, and manual
      // entries now carry their own page/bbox too); nothing was asking for it.
      const focusManual = () => {
        focusWordOnScan(pageForWord(k, i, corr),
          k.klal_id, corr);
        openManualCorrectionPanel(k.klal_id, i, w, corr);
      };
      span.onclick = focusManual;
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
        repl.onclick = focusManual;
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
      span.dataset.wordIndex = i;
      span.textContent = w;
      attachWordHandlers(span, k.klal_id, corr, false, true);
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
        attachWordHandlers(repl, k.klal_id, corr, false, true);
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
      span.dataset.wordIndex = i;
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
        // pageForWord(), not a fourth copy of it - see its own note. This
        // branch carried the `k.page` fallback that sent klal 88 w963 to the
        // klal's first page instead of the one the word is on.
        const targetPage = pageForWord(k, i, null);
        const corrObj = { klal_id: k.klal_id, word_index: i, opcode: 'plain' };
        // All five word-click handlers now go through focusWordOnScan(), which
        // navigates unconditionally. (2026-08-21 had made them consistent the
        // OTHER way, all guarding on manualPageLock; 2026-08-26 reversed that
        // after the lock turned out to make word clicks dead - see
        // focusWordOnScan's own note. Consistency was right, the choice of
        // which way was not.)
        focusWordOnScan(targetPage, k.klal_id, corrObj);
        openManualCorrectionPanel(k.klal_id, i, w, null);
      };
      body.appendChild(span);
    }
    body.appendChild(document.createTextNode(' '));
  });

  markTitleRun(body, k);

  // FIXED 2026-08-25 (reviewer, klal 219). A `possible_omission` whose
  // word_index equals the klal's word count is text the scan has AFTER the last
  // stored word - and the loop above walks the stored words, so a gap at that
  // index had no word to render before and never appeared at all. Not an edge
  // case: 12 of the 40 omission candidates sit there, klal 219's among them, and
  // three of them are a whole missing phrase ('בשם התוספות', 'דוכתי דבגמרא',
  // 'ס"ח ונכון הוא'). The reviewer could decide one only by finding it in the
  // scan pane. Rendered at the end of the klal, in reading order, where the
  // missing text belongs.
  Object.keys(gapsBefore)
    .map(Number)
    .filter(idx => idx >= words.length)
    .sort((a, b) => a - b)
    .forEach(idx => gapsBefore[idx].forEach(c => {
      body.appendChild(makeGapMarker(k.klal_id, c));
      const accepted = c.current_decision && c.current_decision.chosen_text;
      if (accepted) {
        body.appendChild(makePendingInsertText(accepted));
        body.appendChild(document.createTextNode(' '));
      }
    }));
  // (The block above supersedes an earlier one-liner that rendered
  // gapsBefore[words.length] a second time here. REMOVED 2026-08-26 (code
  // review): its filter is `idx >= words.length`, so a candidate at exactly
  // words.length was drawn TWICE - once with its accepted insert text, once
  // bare - in the 12 klalim that have one (84, 88, 106, 114, 138, 159, 164,
  // 171, 175, 193, 211, 219, including klal 219, the klal the newer block was
  // written for). The reviewer saw a duplicate proposed insertion at the end
  // of the klal.)
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
  attachWordHandlers(span, klalId, corr, true, true);
  return span;
}

// FIXED 2026-08-25 (reviewer, klal 219: "i decided to add the proposed text -
// but that text is not seen in the middle pane"). A `possible_omission` is
// words the scan has and the corpus lacks; accepting one is a decision to ADD
// them. It rendered as a bare coloured sliver whose only trace of the accepted
// text was a hover tooltip - so the reviewer had no way to see, while reading,
// what they had agreed to insert. A pending REPLACEMENT has shown its incoming
// text inline since 2026-08-17; an insertion is the same promise and gets the
// same treatment. Recording still does not touch part1.json - the text renders
// as pending until apply_reviewer_decisions.py runs.
function makePendingInsertText(chosenText) {
  const el = document.createElement('span');
  el.className = 'pending-replace-text';
  el.textContent = chosenText;
  el.title = 'Pending insertion: recorded but not yet applied to part1.json';
  return el;
}

// ---------- quick hover tooltip ----------
// The detail block for a flagged word, shared by both hover surfaces: the scan
// pane's #tooltip and the text pane's #word-card. Extracted 2026-08-26 so the
// two cannot drift - they say the same thing about the same word.
function wordDetailHtml(corr, isGap) {
  const [label] = FLAGS[corr.flag] || ['Flagged'];
  const confTxt = (corr.confidence != null) ? (Math.round(corr.confidence * 100) + '% confidence') : 'not scan-verified';
  const hebrewBit = `<bdi>${escapeHtml(corr.docai_reading || (isGap ? '' : '(none)'))}</bdi>`;
  const docaiTxt = isGap
    ? `Scan appears to show: "${hebrewBit}" — not present in current text`
    : `Original OCR reading: "${hebrewBit}"`;
  const bodyTxt = `<span class="t-conf">${escapeHtml(label)} — ${confTxt}${corr.reasoning ? ' — ' + escapeHtml(corr.reasoning) : ''}</span>`;
  const decisionTxt = corr.current_decision
    ? `<span class="t-hint">Your decision: "${escapeHtml(corr.current_decision.chosen_text)}"${corr.current_decision.note ? ' — ' + escapeHtml(corr.current_decision.note) : ''}</span>`
    : `<span class="t-hint">Click for details / to record a decision</span>`;
  return `<span class="t-docai">${docaiTxt}</span>${bodyTxt}${decisionTxt}`;
}

// `skipTooltip` is set by the TEXT-pane call sites. A flagged word there was
// showing TWO floating boxes at once - this #tooltip and the hover card - which
// the reviewer rightly called redundant ("we don't need both boxes when it is a
// disputed word"). The card wins in the text pane because it can hold the copy
// control (#tooltip is pointer-events:none by design, so it can never swallow a
// click on the scan pane, which is also why it cannot host a button). The card
// renders wordDetailHtml() itself, so nothing is lost by suppressing this one.
function attachWordHandlers(el, klalId, corr, isGap, skipTooltip) {
  if (!skipTooltip) {
    el.addEventListener('mouseenter', (e) => {
      tooltip.innerHTML =
        `<span class="t-flag">${escapeHtml(statusLabel(corr))} (Word #${corr.word_index})</span>` +
        wordDetailHtml(corr, isGap);
      tooltip.style.display = 'block';
      positionTooltip(e);
    });
    el.addEventListener('mousemove', positionTooltip);
    el.addEventListener('mouseleave', () => { tooltip.style.display = 'none'; });
  }
  // The card needs the correction to render the same detail; stash it rather
  // than re-deriving it from mountedKlal on every mouseover.
  el._corr = corr;
  el._isGap = !!isGap;
  el.addEventListener('click', () => {
    tooltip.style.display = 'none';
    // Each correction carries its own page field — the physical scan page
    // where its bbox lives (may be a continuation page for klals that span
    // multiple pages). Navigate there so the bbox is found.
    focusWordOnScan(pageForWord(klalForPageLookup(klalId), corr.word_index, corr), klalId, corr);
    // ADDED 2026-08-31: if the click came from the SCAN pane, take the text pane
    // to the same word. attachWordHandlers is shared by both panes, so this is
    // gated on where the element lives - a text-pane click is already at its
    // word and must not be scrolled out from under the reviewer's cursor.
    if (!textScroll.contains(el)) revealWordInText(klalId, corr.word_index);
    openDisputedPanel(klalId, corr);
  });
}
// The scan page a word actually lives on. `corr.page` when the entry carries
// one, then the server's DocAI-alignment map, and only then the klal's START
// page - which is right only for a klal that fits on one page.
//
// ADDED 2026-08-26 (reviewer: "klal 179 word 267 - clicking does not highlight
// word in scan page"). That word sits on page 67; klal 179 starts on page 66;
// its entry had no `page`, so `corr.page || k.page` sent the scan to 66 and the
// highlight had nothing to match. The manual-correction handler had already
// worked around this by consulting word_pages; the disputed and flag handlers
// had not. One helper, used by all of them.
// The klal object that actually KNOWS which page each word is on.
//
// ADDED 2026-09-01 with the deep-link fix above. `klalById` comes from
// /api/klalim - the nav payload, which carries `page` but not `word_pages` - so
// handing it to pageForWord() silently disables that function's whole middle
// branch, which is the branch it was written for. Every caller wanting a
// per-WORD page must ask the mounted /api/klal payload; the nav object is the
// fallback for a klal that is not mounted yet, where the start page is the only
// answer available.
function klalForPageLookup(klalId) {
  return mountedKlal[klalId] || klalById[klalId];
}

function pageForWord(k, wordIndex, corr) {
  if (corr && corr.page != null) return corr.page;
  const pages = k && k.word_pages;
  if (pages && wordIndex != null) {
    if (pages[wordIndex] != null) return pages[wordIndex];
    // NO ALIGNED TOKEN for this word - 1,649 of Part 1's 52,630 words, because
    // DocAI never matched them. Falling straight through to the klal's START
    // page is a guess, and in a klal that spans pages it is usually the WRONG
    // guess: 746 of those words live in a multi-page klal, and klal 88 w963 -
    // reported 2026-09-02 - is on page 40 of a klal that starts on 39 and runs
    // to 41. The scan opened on 39, the word had no box there, and nothing
    // highlighted or zoomed.
    //
    // Words are in reading order, so the nearest word that IS aligned is a far
    // better answer than the klal's first page. Walk outward, preferring the
    // preceding neighbour: text flows forward, so the word before this one is
    // on this one's page unless a page break falls between them.
    for (let d = 1; d <= 500; d++) {
      if (pages[wordIndex - d] != null) return pages[wordIndex - d];
      if (pages[wordIndex + d] != null) return pages[wordIndex + d];
    }
  }
  return k ? k.page : null;
}

// Clicking a WORD is explicit intent to look at that word, so it always moves
// the scan pane - and clears manualPageLock on the way, exactly as jumpTo() does
// for a nav-panel click.
//
// FIXED 2026-08-26 (reviewer: "the review panel is currently in a bad state -
// clicking on words does not refresh the left pane with just that word
// highlighted"). manualPageLock is set by the scan pane's own prev/next arrows,
// and until now it was cleared ONLY by clicking a klal in the nav list. So the
// moment a reviewer paged the scan by hand - the natural thing to do while
// reading - every subsequent word click silently stopped refreshing the scan,
// with nothing on screen saying why and no obvious way out. The lock exists to
// stop SCROLLING from snapping the page back (its two remaining call sites,
// setActiveKlal and the scroll auto-advance, still honour it); it was never
// meant to defeat a deliberate click.
function focusWordOnScan(targetPage, klalId, corr, opts) {
  manualPageLock = false;
  _zoomOnFocus = true;
  // Every word click routes through here, so this is the one place that has to
  // know the address bar exists. replaceState, not pushState: a reviewer moving
  // through a klal should not have to press Back forty times to leave.
  if (corr && corr.word_index != null) {
    updateHash(klalId, corr.word_index);
    // ...and the one place that copies that address, for the same reason - see
    // copyWordLink(). `viaClick: false` is passed by the ONLY non-click caller,
    // highlightRoutedWord(): arriving somewhere by following a link must not
    // overwrite the clipboard the reviewer used to get there, and a deep link
    // opened cold would otherwise fire a toast at a reviewer who clicked
    // nothing.
    if (!opts || opts.viaClick !== false) copyWordLink(klalId, corr.word_index);
  }
  // FIXED 2026-09-01, found while reproducing the klal 12 w219 report: the click
  // set page 19 correctly and then a scroll event fired a few hundred ms later,
  // updateActiveFromScroll() resolved a different klal, and setActiveKlal()
  // showed THAT klal's start page - undoing the navigation the click had just
  // made, with nothing on screen saying why.
  //
  // manualPageLock guards the scan pane's own prev/next arrows against exactly
  // this, and a word click deliberately CLEARS it (2026-08-26, because the lock
  // was making word clicks dead) - which left the click itself the one
  // deliberate navigation with no protection at all. revealWordInText() and
  // applyHashRoute() both already hold the observer off while they settle; this
  // is the third member of that set and simply never joined it.
  //
  // lastActiveScanPage is moved with it so the observer's own page branch does
  // not treat the new page as a change and re-show the old one.
  suppressObserverScroll = true;
  clearTimeout(suppressTimer);
  lastActiveScanPage = targetPage;
  suppressTimer = setTimeout(() => { suppressObserverScroll = false; }, 900);
  showPage(targetPage, klalId, corr);
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
const flagListPanel = document.getElementById('flag-list-panel');
const flagListPanelBody = document.getElementById('flag-list-panel-body');

function setupPanels() {
  const disputedClose = document.getElementById('disputed-panel-close') || document.getElementById('candidate-panel-close');
  if (disputedClose) disputedClose.onclick = dismissPanels;
  document.getElementById('klal-flag-panel-close').onclick = dismissPanels;
  document.getElementById('punctuation-panel-close').onclick = dismissPanels;
  document.getElementById('witness-panel-close').onclick = dismissPanels;
  document.getElementById('manual-panel-close').onclick = dismissPanels;
  document.getElementById('flag-list-panel-close').onclick = dismissPanels;
  backdrop.onclick = dismissPanels;
  // ADDED 2026-08-25 (user request: "clicking away (in a blank part of the
  // middle pane) should cancel that and close the right pane"). The backdrop
  // does not cover the text pane - by design, so a reviewer can keep reading
  // and click straight from one word to the next without a dismiss step - so a
  // click on the prose itself had no way to say "never mind". Anything that is
  // a word, a gap marker, a klal header control or a pending-replacement is
  // still a real target and opens/keeps its panel; a click that lands on none
  // of them is blank space and cancels.
  const INTERACTIVE_IN_TEXT = [
    '.flag-word', '.plain-word', '.flag-gap', '.editorial-mark',
    '.pending-replace-text', '.klal-flag-btn', '.continuation-marker',
    // '.punct-marker' added 2026-08-26 (code review). Dormant, not dead:
    // makePunctuationMarker() is not called from renderKlalBody today (the
    // punctuation affordances were removed from the UI 2026-08-11, kept
    // reversible). The moment they return, openPunctuationPanel() opens the
    // panel synchronously before its first await, the same click bubbles here,
    // matches nothing, finds '.side-panel.open' and dismisses it - the panel
    // would shut the instant it opened.
    '.punct-marker',
    'button', 'a', 'input', 'textarea', 'select',
  ].join(',');
  textScroll.addEventListener('click', (e) => {
    if (e.target.closest(INTERACTIVE_IN_TEXT)) return;
    if (!document.querySelector('.side-panel.open')) return;  // nothing to close
    dismissPanels();
  });
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') dismissPanels();
  });
}
function closePanels() {
  // Was five hand-listed panels until 2026-09-01, when a sixth was added: a
  // panel missing from this list stays open UNDER the next one, and nothing on
  // screen says which of the two is answering your click. Querying the class
  // that already defines "is a side panel" cannot be forgotten.
  backdrop.classList.remove('open');
  document.querySelectorAll('.side-panel.open').forEach(p => p.classList.remove('open'));
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
// the .save-status pattern. As of 2026-08-25 that is ALL FIVE panels -
// the manual-correction panel kept its own re-render-as-confirmation
// behaviour until a reviewer pointed out it was the one panel they still
// had to close by hand after every correction.
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

// ONE definition of "clear the word-level revisit flag", used by both panels.
// DEDUPLICATED 2026-08-31 (finding #18 of the 2026-08-26 review, restated as
// the 2026-08-27 review's #9). The disputed panel and the manual-correction
// panel each carried a ~20-line verbatim copy of this handler, differing only
// in where they got the word index. Copy-pasting this exact control is how the
// original unclearable-flag bug reached 325 flags across 104 klalim: a fix
// applied to one copy leaves the other answering the same click differently.
async function clearWordFlag(klalId, wordIndex) {
  const res = await fetch('/api/decisions/klal_flag', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ klal_id: klalId, word_index: wordIndex,
                           needs_revisit: false,
                           note: 'Word-level revisit flag cleared from the dashboard.' }),
  });
  if (!res.ok) { alert('Could not clear the flag: ' + (await res.text())); return false; }
  // Same refresh path every other save handler uses (there is no
  // refreshKlal(); the pattern is drop the cache, refetch, re-render).
  delete mountedKlal[klalId];
  delete fetchInFlight[klalId];
  const fresh = await fetchKlal(klalId);
  const block = document.getElementById('klal-block-' + klalId);
  if (block) renderKlalBody(block, fresh);
  refreshKlalimList();
  dismissPanels();
  return true;
}

// ---------- the word list behind a legend count ----------
//
// ADDED 2026-09-01 (reviewer: "clicking on a flag count at the bottom of the
// index panel should pop up a list of those flags as clickable links, hovering
// for a while should pop up a copy to clipboard icon").
//
// The legend has shown four totals since it was built and there was no way to
// get from a total to the words inside it: a reviewer wanting to work through
// the open disputes had to open klalim one at a time looking for red. This is
// Lesson 29's question asked of the legend itself - who acts on this number,
// and how? - and until now the answer was "nobody can".
//
// The lists come from /api/word-states, which is computed in the SAME pass as
// the counts (api_klalim's on_klal_states callback), so a list can never be a
// different length from the number that opened it.
//
// COPY ICON ON DWELL, not on hover: a list of 518 rows with a control on every
// one is a wall of buttons, and the same icon appearing under the pointer the
// instant it crosses a row makes the list unreadable while scrolling. The row
// has to be held.
const FLAG_LIST_DWELL_MS = 400;
let flagListDwellTimer = null;
// The rows currently in the panel, kept so the recorded view's status filter can
// re-render without another round trip.
let flagListRows = [];
let flagListBucket = null;
let flagListStatus = 'all';

// What each status means, in the words a senior reviewer needs. Order is the
// order the chips appear in, which is decreasing claim on their attention:
// something that never landed matters more than something that did.
const RECORDED_STATUS_META = {
  pending:   ['pending',   'The ruling CHANGES the text and the corpus does not have the change yet. This, and only this, is the promote-to-corpus backlog: run apply_reviewer_decisions.py.'],
  drifted:   ['drifted',   'The word at this position is neither the one ruled on nor the one chosen, and no apply_event claims the ruling was promoted - so what became of it cannot be told from here.'],
  unplaced:  ['unplaced',  'The recorded word_index is outside this klal entirely.'],
  unknown:   ['unknown',   'No original word was snapshotted - witness rulings record docai vs tesseract and never the stored word - so there is nothing to compare against.'],
  applied:   ['applied',   'The ruling changed the text and the change is in the corpus.'],
  confirmed: ['confirmed', 'The ruling KEPT the stored reading. There was never anything to promote - this is the commonest decision in the corpus, and counting it as "applied" is what made 27 of 54 drawn-green words look promoted when only 1 was.'],
};
// Not a status - a second, independent fact about the same row. See
// review_server._decision_index_is_stale(): `status` is what happened to the
// RULING, this is what happened to its ADDRESS, and a ruling can be honoured and
// still have an index that no longer points at the word it described.
const RECORDED_STALE_LABEL = ['stale address',
  'The ruling\u2019s recorded word_index no longer points at the word it names, because a later apply in the same klal shifted everything after it and nothing re-pointed the decision. Open item 0AB. Most of these were still HONOURED - it is the address that rotted, not the ruling.'];

async function openFlagListPanel(bucket, label) {
  openPanel(flagListPanel);
  document.getElementById('flag-list-panel-title').textContent = label;
  flagListPanelBody.innerHTML = '<p>Loading…</p>';
  flagListBucket = bucket;
  flagListStatus = 'all';
  let data;
  try {
    const res = await fetch('/api/word-states?part=' + (currentPart || '1'));
    if (!res.ok) throw new Error(await res.text());
    data = await res.json();
  } catch (e) {
    // Not an alert(): the panel is already open and is the natural place to say
    // so. A silent empty list would read as "there are none", which is the one
    // wrong thing this panel can say.
    flagListPanelBody.innerHTML =
      `<p class="flag-list-empty">Could not load the word list: ${escapeHtml(String(e.message || e))}</p>`;
    return;
  }
  flagListRows = data[bucket] || [];
  renderFlagList(label);
}

function flagListItemHtml(r, recorded) {
  const href = `#klal=${r.klal_id}&word=${r.word_index}`;
  const name = `Klal ${r.klal_id}` + (r.gematria ? ` (${r.gematria})` : '');
  // A null word is a possible_omission sitting at len(words) - text the scan
  // has and the corpus does not - so there is nothing to print, and saying
  // "(not in text)" is the whole content of that row.
  const word = r.word == null
    ? '<span class="flag-list-nul">(not in text)</span>'
    : `<bdi class="flag-list-word">${escapeHtml(r.word)}</bdi>`;
  let middle = word;
  let cls = 'flag-list-item';
  let title = '';
  if (recorded) {
    cls += ' recorded-item rec-' + (r.status || 'unknown') + (r.index_stale ? ' rec-stale' : '');
    // Only show the arrow when the ruling actually CHANGED something. A reviewer
    // confirming the stored text (chosen_source "final_text") is the commonest
    // decision in this corpus by far, and rendering "word -> same word" 300
    // times would bury the rulings that did change the text.
    const changed = r.chosen_text != null && r.chosen_text !== r.word;
    const chosen = r.chosen_text === '' ? '<span class="rec-deleted">(deleted)</span>'
                                        : `<bdi class="rec-chosen">${escapeHtml(String(r.chosen_text))}</bdi>`;
    middle = `<span class="rec-status">${escapeHtml((RECORDED_STATUS_META[r.status] || [r.status])[0])}</span>` +
             (r.index_stale ? `<span class="rec-stale-mark" title="${escapeAttr(RECORDED_STALE_LABEL[1])}">&#9888;</span>` : '') +
             word + (changed ? `<span class="rec-arrow">&rarr;</span>${chosen}` : '');
    const when = (r.ts || '').slice(0, 10);
    title = `${r.decision_type || 'decision'}${when ? ' on ' + when : ''}` +
            (r.original_word != null ? ` \u2014 ruled on "${r.original_word}"` : '') +
            (r.note ? ` \u2014 ${r.note}` : '') +
            `\n${(RECORDED_STATUS_META[r.status] || ['', ''])[1]}`;
  }
  return `<a class="${cls}" href="${href}" title="${escapeAttr(title)}"` +
           ` data-klal="${r.klal_id}" data-word="${r.word_index}">` +
           `<span class="flag-list-ref">${escapeHtml(name)} &middot; #${r.word_index}</span>` +
           middle +
           `<button class="copy-ref flag-list-copy" type="button" tabindex="-1"` +
           ` title="Copy reference and link" data-klal="${r.klal_id}" data-word="${r.word_index}"` +
           ` data-text="${escapeAttr(r.word == null ? '' : String(r.word))}">&#128203;</button>` +
         `</a>`;
}

function renderFlagList(label) {
  const recorded = flagListBucket === 'recorded';
  if (!flagListRows.length) {
    flagListPanelBody.innerHTML = '<p class="flag-list-empty">No words in this state in the current part.</p>';
    return;
  }
  const matches = (r) => flagListStatus === 'all'
    || (flagListStatus === 'stale' ? r.index_stale : r.status === flagListStatus);
  const shown = flagListRows.filter(matches);

  let head = `<p class="flag-list-summary">${flagListRows.length} word(s) &mdash; ${escapeHtml(label)}. ` +
             `Click one to go to it; hold the pointer on a row for its copy button.</p>`;
  if (recorded) {
    // The status breakdown, as filters. A senior reviewer reviewing someone's
    // work does not want 478 rows in one undifferentiated column - they want
    // "which of these never landed", which is exactly the split this offers.
    const counts = { stale: 0 };
    flagListRows.forEach(r => {
      counts[r.status] = (counts[r.status] || 0) + 1;
      if (r.index_stale) counts.stale += 1;
    });
    // RECORDED_STATUS_META's key order is the order these appear in, and it runs
    // from "needs a human" to "settled" - the chips a senior reviewer reaches for
    // first should not be at the end of the row. `stale` rides along at the end
    // because it cuts ACROSS the statuses rather than being one of them.
    const order = ['all'].concat(Object.keys(RECORDED_STATUS_META).filter(st => counts[st]))
                         .concat(counts.stale ? ['stale'] : []);
    const chips = order.map(st => {
        const n = st === 'all' ? flagListRows.length : counts[st];
        const meta = st === 'stale' ? RECORDED_STALE_LABEL : RECORDED_STATUS_META[st];
        return `<button type="button" class="rec-chip rec-${st}` +
               (flagListStatus === st ? ' rec-chip-on' : '') + `" data-status="${st}"` +
               ` title="${escapeAttr(meta ? meta[1] : 'Every ruling on record for this part.')}">` +
               `${st === 'all' ? 'all' : escapeHtml(meta[0])} <b>${n}</b></button>`;
      }).join('');
    head = `<p class="flag-list-summary">Every ruling recorded for this part &mdash; what was decided, ` +
           `and whether the corpus reflects it. A ruling stops being highlighted in the text once it is ` +
           `settled, which is why this list is far longer than the Human-Decided count.</p>` +
           `<div class="rec-chips">${chips}</div>`;
  }
  flagListPanelBody.innerHTML = head +
    (shown.length
      ? `<div class="flag-list">${shown.map(r => flagListItemHtml(r, recorded)).join('')}</div>`
      : '<p class="flag-list-empty">Nothing in that state.</p>');
}

// Delegated, so the handlers survive every re-render of the list body.
flagListPanelBody.addEventListener('click', (e) => {
  if (e.target.closest('.copy-ref')) return;      // the global .copy-ref handler owns this
  const chip = e.target.closest('.rec-chip');
  if (chip) {
    flagListStatus = chip.dataset.status;
    renderFlagList(document.getElementById('flag-list-panel-title').textContent);
    return;
  }
  const a = e.target.closest('.flag-list-item');
  if (!a) return;
  e.preventDefault();
  // Route DIRECTLY - never via location.hash. Setting the hash queues a
  // hashchange that re-routes with no options, which on an already-mounted klal
  // wins the race and opens the word's panel; that calls closePanels() and shuts
  // this list on every row. routeToKlal()'s own note has the mechanism.
  // `fromList` is what keeps the row from opening that panel: a URL that names a
  // word behaves like clicking it, but a row already has the list as its
  // context, and the point of the list is working down it.
  routeToKlal(Number(a.dataset.klal), Number(a.dataset.word), { fromList: true });
});
flagListPanelBody.addEventListener('mouseover', (e) => {
  const a = e.target.closest && e.target.closest('.flag-list-item');
  if (!a || !flagListPanelBody.contains(a)) return;
  clearTimeout(flagListDwellTimer);
  flagListDwellTimer = setTimeout(() => {
    flagListPanelBody.querySelectorAll('.flag-list-item.dwell')
      .forEach(el => el.classList.remove('dwell'));
    a.classList.add('dwell');
  }, FLAG_LIST_DWELL_MS);
});
flagListPanelBody.addEventListener('mouseout', (e) => {
  const a = e.target.closest && e.target.closest('.flag-list-item');
  if (!a) return;
  // Moving onto the row's own copy button must not cancel the dwell that
  // revealed it - that is the one move the reviewer is about to make.
  if (e.relatedTarget && a.contains(e.relatedTarget)) return;
  clearTimeout(flagListDwellTimer);
  a.classList.remove('dwell');
});

// Put the list away when the reviewer goes back to the text or the scan
// (reviewer 2026-09-01: "pop up from index human-decided should disappear when
// clicked inside text pane or scan pane").
//
// Only THIS panel, and without clearScanFocus(): the other five are opened BY a
// click in those panes, so closing on the same click would shut them the instant
// they opened - the exact failure the '.punct-marker' entry in setupPanels'
// INTERACTIVE_IN_TEXT list is a standing note about. The list is the one panel
// opened from the index, so leaving the index is what dismisses it.
//
// Capture phase, so it runs before the word's own handler opens its panel and
// the ordering is close-then-open rather than the reverse.
function closeFlagListPanel() {
  if (!flagListPanel.classList.contains('open')) return;
  flagListPanel.classList.remove('open');
  if (!document.querySelector('.side-panel.open')) backdrop.classList.remove('open');
}
['text-pane', 'scan-pane'].forEach(id => {
  const pane = document.getElementById(id);
  if (pane) pane.addEventListener('click', closeFlagListPanel, true);
});

// The legend is rebuilt from scratch by buildLegend() on every refresh, so this
// is delegated to the container rather than bound per row.
legend.addEventListener('click', (e) => {
  if (!e.target.closest) return;
  // Every legend entry is now a sibling ROW, including the recorded total, so
  // one lookup serves all of them. It used to be a button nested inside the
  // Human-Decided row, which needed testing first or `closest` walked past it to
  // the row and opened the 54-word list from a control labelled 481.
  const row = e.target.closest('.legend-clickable');
  if (!row || !legend.contains(row)) return;
  openFlagListPanel(row.dataset.bucket, row.dataset.label);
});

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
    // 'no_word', not 'final_text'. FIXED 2026-08-26 (reviewer: klal 66 word 17,
    // "can't save decision current text (no word)"). A `delete` candidate has NO
    // final_text by definition - the corpus has nothing at that position - so
    // this option resolved `corr['final_text']` to undefined and POSTed
    // chosen_text: null. The null-decision guard added earlier the same day then
    // refused it, which turned a legitimate reviewer choice ("this proposed
    // insertion is wrong, the corpus is right as it stands") into an unsaveable
    // one for all 40 omission candidates across 35 klalim.
    //
    // The four pre-existing null rows (klal 90 w4, 88 w1149, 164 w55, 2 w632)
    // were recorded through THIS option and were correct decisions, not accidents
    // - the readings they reject are junk (`בעיא 4`, `४`, `ג`). Yesterday's note
    // calling them "a Save with nothing chosen" was wrong; see PROJECT-STATUS.
    // An explicit empty string says "no text here" and is exactly what
    // apply_delete_insertion() already treats as a no-op.
    options.push({ source: 'no_word', label: 'Keep current text (no word)', text: '—' });
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
  // Surya OCR baseline reading (added 2026-08-23, independent local witness):
  if (corr.surya_reading && !options.some(o => o.text === corr.surya_reading)) {
    options.push({ source: 'surya_reading', label: 'Surya OCR reading', text: corr.surya_reading });
  }
  // A lexical-defect proposal (pipeline stage 4b). NOT an engine reading - it
  // comes from the independent reference corpus's frequency table plus the
  // detectors' one-edit search - so it is labelled for what it is rather than
  // shown beside the OCR engines as if a witness had read it. ADDED 2026-08-26
  // (reviewer: "are the 384 words flagged? how can i review?"): without an
  // option card these entries would render a panel with nothing to choose, which
  // is the dead-control shape this file already hit twice today.
  if (corr.lexical_proposal && !options.some(o => o.text === corr.lexical_proposal)) {
    options.push({ source: 'lexical_proposal', label: 'Lexical proposal (not an engine reading)',
                   text: corr.lexical_proposal });
  }
  // DocAI's reading with the alef-lamed ligature's dropped lamed restored
  // (pipeline/repair_filters/docai_filter.py). ADDED 2026-08-24 in a review of
  // this session's own code: the field was being computed and served and NEVER
  // SHOWN, which made the single most valuable reading invisible - measured
  // against a reviewer's complete klal 91 review, the repaired DocAI reading is
  // right 94% of the time where the raw one is right 0%. Placed directly after
  // the raw DocAI option so the two read as a pair.
  if (corr.docai_repaired && !options.some(o => o.text === corr.docai_repaired)) {
    const at = options.findIndex(o => o.source === 'docai_reading');
    options.splice(at < 0 ? options.length : at + 1, 0, {
      source: 'docai_repaired',
      label: 'DocAI reading, ligature repaired',
      text: corr.docai_repaired,
    });
  }

  // Pre-fill the AI detector's suggested word as an extra selectable option
  // card when present (added 2026-08-14, see openManualCorrectionPanel's
  // note on why: typing Hebrew acronyms by hand is slow and error-prone;
  // this gives the reviewer a 1-click accept option for the AI suggestion
  // without typing). Matches openManualCorrectionPanel's layout: placed
  // right below the current-text option, distinctly styled via .co-meta.
  const suggestedWord = extractSuggestedWord(corr, corr.final_text);
  if (suggestedWord && !options.some(o => o.text === suggestedWord)) {
    options.splice(1, 0, {
      source: 'suggested',
      label: 'AI detector suggestion',
      text: suggestedWord,
    });
  }

  // REVERTED 2026-08-23 (code review, finding M11). A block here used to
  // pre-select the MACHINE's own answer on an undecided word -
  // vision_selected 'A' checked the DocAI option, 'B' the current text - so the
  // radio a reviewer found already filled in was the vision model's verdict,
  // and a single Save click promoted it into review_decisions.jsonl as a HUMAN
  // decision, indistinguishable from one where someone actually looked at the
  // scan. This project's first success criterion is that every correction is
  // "resolved by looking at the actual scan, not inferred", and the whole
  // record/apply split exists to keep machine output and human judgement
  // separate; a pre-checked machine answer quietly makes agreeing with the
  // machine the path of least resistance. The machine's verdict is still shown
  // - statusLabel() and the confidence percentage in the panel header both
  // report it, and wordState() colours the word by it - it just no longer
  // arrives pre-selected. Undecided words default to the conservative
  // current stored text, as they did before.
  let activeSource = decision ? decision.chosen_source : 'final_text';
  let activeText = decision ? (decision.chosen_text || '') : '';

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
      ${corr.consensus_engines && corr.consensus_engines.length ? `<div style="font-size:12px;color:var(--ink-faint);margin-top:4px;">
        ${escapeHtml(corr.consensus_engines.join(' + '))} agree on <b>${escapeHtml(corr.consensus_reading || '')}</b>${corr.ligature_artifact ? ' — but this is a known <b>' + escapeHtml(corr.ligature_artifact) + '</b> ink artifact, so the agreement is a shared misread, not corroboration' : ''}</div>` : ''}
    </div>
    <div class="panel-section">
      ${wordRefLabel(klalId, corr.word_index, words[corr.word_index], 'Context &middot; ')}
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
    ${corr.witness_overlay ? `
    <div class="panel-section">
      <div class="panel-label">Second-witness disagreement (DocAI vs Tesseract)</div>
      <div style="font-size:12px;color:var(--ink-faint);">
        DocAI: ${escapeHtml(corr.witness_overlay.docai_reading || '—')} ·
        Tesseract: ${escapeHtml(corr.witness_overlay.tesseract_reading || '—')}
        ${corr.witness_overlay.tier ? ' · tier ' + escapeHtml(corr.witness_overlay.tier) : ''}
        ${corr.witness_overlay.current_decision ? ' · already decided' : ''}
      </div>
      <div style="font-size:11px;color:var(--ink-faint);margin-top:4px;">
        This word also carries a witness-queue disagreement. Tesseract was measured
        correct in 16 of 419 such cases (3.8%), so it is shown for context, not as a
        competing reading.</div>
    </div>` : ''}
    ${(corr.word_flag || corr.flag === 'ai_flag') ? `
    <div class="panel-section">
      <div class="panel-label">Revisit flag</div>
      <div style="font-size:12px;color:var(--ink-faint);margin-bottom:6px;">
        ${(corr.word_flag && corr.word_flag.answered)
          ? `Answered — you recorded a decision on this word after the flag was raised${corr.word_flag.reviewer ? ' by ' + escapeHtml(corr.word_flag.reviewer) : ''}, so it no longer counts as outstanding. Clearing it just closes the record.`
          : `This word carries an open revisit flag${corr.word_flag && corr.word_flag.reviewer ? ' from ' + escapeHtml(corr.word_flag.reviewer) : ''}.`}</div>
      <button class="panel-btn" id="clear-word-flag-btn">Clear revisit flag</button>
    </div>` : ''}
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

  // ADDED 2026-08-24 (user report: "i can't clear the revisit flag"). A
  // WORD-level revisit flag is keyed on (klal_id, word_index) and is cleared
  // only by a later record at that same key - which the klal-flag panel cannot
  // write, since it only ever posts klal-level flags. That panel already
  // admitted the gap in its own copy ("that's tracked separately and won't
  // change if you save here unchecked") without offering a way to close it.
  // The control belongs here, on the word itself.
  const clearBtn = document.getElementById('clear-word-flag-btn');
  if (clearBtn) {
    clearBtn.onclick = () => clearWordFlag(klalId, corr.word_index);
  }
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
  if (source === 'no_word') {
    // An omission candidate the reviewer rejects: nothing is inserted. Recorded
    // as an explicit empty string rather than null so it is a decision, not a
    // missing field - and so it survives the null guard below.
    text = '';
    chosenSource = 'final_text';
  } else if (source === 'remove') {
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
  // FIXED 2026-08-26 (code review). With no option selected, `source` falls
  // back to 'final_text' - and a `delete` (omission) candidate or a synthesized
  // `ai_flag` entry has no final_text at all, so this POSTed
  // chosen_source:'final_text', chosen_text:null. That is not a null decision in
  // theory: it has already happened FOUR times in review_decisions.jsonl (klal
  // 90 w4, 88 w1149, 164 w55, 2 w632 - all opcode 'delete', three of them on
  // 2026-08-24/25). The append-only log keeps them forever; they mark the word
  // decided and answer its revisit flag, while apply_reviewer_decisions.py can
  // never promote them (no text to write). An empty string is a real choice
  // ('remove', and an `insert`'s empty custom box); null never is.
  if (text == null) {
    alert('Choose a reading first - this candidate has no default to accept.');
    return;
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
    // ADDED 2026-08-25 (reviewer on klal 163: "i cleared the flag but it still
    // shows"). Unchecking here clears only the klal's general note; the pennant
    // also lights for open AI-flagged WORDS, which this panel does not touch.
    // The panel says so when you RE-OPEN it - which is one click too late, and
    // is why that clear got clicked twice. Say it in the confirmation itself.
    const status = document.getElementById('klal-flag-save-status');
    const wordFlags = klalById[klalId] ? (klalById[klalId].ai_flag_count || 0) : 0;
    if (status) {
      status.textContent = (!needsRevisit && stillFlagged && wordFlags)
        ? `Saved ✓ — still flagged by ${wordFlags} AI-flagged word${wordFlags === 1 ? '' : 's'} in the text`
        : 'Saved ✓';
    }
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
  // Returns FALSE on failure specifically, so a caller can tell a failed save
  // from a successful one that produced no synthetic entry to return (a delete
  // can legitimately leave nothing at this word_index). Before the panel
  // auto-closed, both cases were `null` and both simply skipped the re-render,
  // so the distinction did not matter; now one must flash-and-close and the
  // other must not.
  if (!res.ok) { alert('Save failed: ' + (await res.text())); return false; }

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

  const suggestedWord = extractSuggestedWord(reasoningNote, word);

  manualPanelBody.innerHTML = `
    <div class="panel-section">
      ${wordRefLabel(klalId, wordIndex, word, '')}
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
      ${isAiFlag || (existing && existing.word_flag) ? `<button class="panel-btn secondary" id="clear-word-flag-btn-manual">Clear revisit flag</button>` : ''}
      <span class="save-status" id="manual-save-status">Saved ✓</span>
    </div>
    ${existing ? `
    <div class="panel-section">
      <span class="history-toggle" id="manual-correction-history-toggle">Show decision history</span>
      <div class="history-list" id="manual-correction-history-list" style="display:none;"></div>
    </div>` : ''}
  `;

  // CHANGED 2026-08-25 (user-requested: "after save correction the right pane
  // should auto-close"). This panel used to be the one exception in the app: on
  // save it RE-OPENED itself against the fresh post-save state, on the reasoning
  // that the refreshed content ("Correction on record" / "Marked for deletion")
  // was itself the confirmation. In practice that left the reviewer to dismiss a
  // panel by hand after every single correction - the exact complaint that
  // produced flashSavedThenClose() for the other four panels on 2026-08-21, and
  // the manual panel is the one a reviewer uses most. It now behaves like the
  // rest: flash the confirmation, hold it, close. The re-render is no longer
  // needed as confirmation because the word itself turns green in the text pane
  // (renderKlalBody has already run inside saveManualDecision by then).
  const useSuggestedBtn = document.getElementById('use-suggested-word-btn');
  if (useSuggestedBtn && suggestedWord) {
    useSuggestedBtn.onclick = () => {
      // FILL ONLY - no auto-save. This used to click Save itself, so a single
      // click recorded a decision the reviewer never read. That is what turned
      // a bad suggestion (klal 1 w229's `6.18M`) from an annoyance into a
      // corpus-integrity risk. The suggestion now lands in the box and the
      // reviewer presses Save, which is one extra click and the whole
      // safeguard: success criterion #1 says a correction is resolved by
      // looking, not by accepting a proposal sight unseen.
      const box = document.getElementById('manual-correction-text');
      box.value = suggestedWord;
      box.focus();
    };
  }

  document.getElementById('save-manual-correction-btn').onclick = async () => {
    const text = document.getElementById('manual-correction-text').value.trim();
    if (!text) { alert('Enter the corrected reading first (or use Delete this word instead).'); return; }
    const note = document.getElementById('manual-correction-note').value.trim();
    const saved = await saveManualDecision(klalId, wordIndex, word, text, note);
    if (saved !== false) flashSavedThenClose('manual-save-status');
  };

  // "Accept current text" — dismisses an AI flag without a text change.
  // Records a manual_correction with chosen_text == the current word (a
  // deliberate no-op: the reviewer looked at it, the text is correct as-is).
  // apply_reviewer_decisions.py handles this correctly: replace word with
  // itself, net change to part1.json is zero, apply_event is recorded.
  if (isAiFlag) {
    document.getElementById('accept-current-text-btn').onclick = async () => {
      const note = document.getElementById('manual-correction-note').value.trim();
      const saved = await saveManualDecision(klalId, wordIndex, word, word,
        note || 'AI flag reviewed — current text confirmed');
      if (saved !== false) flashSavedThenClose('manual-save-status');
    };
  }

  // Arm-then-confirm in the panel itself rather than a native confirm()
  // dialog - consistent with the rest of this app (no other action here
  // uses a browser-native dialog) and avoids the well-known problem of
  // native dialogs blocking further automated/scripted interaction with
  // the page entirely once triggered.
  let deleteArmed = false;
  // ADDED 2026-08-24, second pass. The first fix for "i can't clear the revisit
  // flag" put the control ONLY in the disputed panel - but renderKlalBody routes
  // opcode 'ai_flag' and opcode 'manual' words to THIS panel, so the control was
  // unreachable for exactly the flags that render as their own entry. Measured:
  // 128 of 325 open word-level flags were clearable, 197 were not. The earlier
  // corpus sweep asserted the wrong property - that the served entry carries a
  // `word_flag` field, not that a panel offering the button actually renders.
  const clearFlagManual = document.getElementById('clear-word-flag-btn-manual');
  if (clearFlagManual) {
    clearFlagManual.onclick = () => clearWordFlag(klalId, wordIndex);
  }

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
    const saved = await saveManualDecision(klalId, wordIndex, word, '', note);
    if (saved !== false) flashSavedThenClose('manual-save-status');
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
// Pending "this word is not on the scan" warning - see the end of showPage().
let _noScanPositionTimer = null;
const pageImg = document.getElementById('page-img');
const hlContainer = document.getElementById('hl-container');
const pageIndicator = document.getElementById('page-indicator');
const klalIndicator = document.getElementById('klal-indicator');
let _headerKlalId = null;

// The scan header reads "Page 73 · Klal 210" and then the SAME reference in
// Hebrew, "דף עג · כלל רי" (reviewer request, 2026-08-31). Before this it showed
// the page in one span and a bare "כלל 210" in the other - the klal number in
// Arabic digits beside a Hebrew word, which is not how the book writes it, and
// no page reference in Hebrew at all.
//
// CAVEAT, stated because it is genuinely ambiguous: `דף עג` is OUR page index
// written in Hebrew letters. It is NOT the folio the printer set on that leaf -
// the printed folio is stripped as page furniture (item 20/27) and is stored
// nowhere in this repo, so there is nothing to display for it.
function hebNum(n) {
  return NUMERALS[n] || NUMERALS[String(n)] || String(n);
}

function updateScanHeader() {
  const page = currentPage;
  const kid = _headerKlalId;
  if (page == null) {
    pageIndicator.textContent = 'Part 2 & 3 Review';
    klalIndicator.textContent = '';
    return;
  }
  const en = 'Page ' + page + (kid != null ? ' · Klal ' + kid : '');
  const he = 'דף ' + hebNum(page) + (kid != null ? ' · כלל ' + hebNum(kid) : '');
  pageIndicator.textContent = en;
  klalIndicator.textContent = he;
}
const scanViewer = document.getElementById('scan-viewer');

let zoomLevel = 1;
// Clicking a word zooms the scan in on it (2026-08-26, reviewer request). Set by
// focusWordOnScan - the single funnel every word click already goes through -
// and consumed by whichever of showPage's two centring paths runs.
//
// It raises the zoom, never lowers it: a reviewer who has deliberately zoomed to
// 300% to read a worn glyph should not be yanked back to 220% by their next
// click. And it is a one-shot flag, so scrolling or paging afterwards leaves the
// zoom alone - only an explicit click re-triggers it.
const FOCUS_ZOOM = 2.2;
let _zoomOnFocus = false;
// The zoom in effect before a click zoomed in on a word, so clicking away can
// put it back (2026-08-26, reviewer: "clicking away ... should also zoom back
// out to 100"). null means the current zoom was NOT set by a focus, so there is
// nothing to undo and clearing focus leaves it alone - a reviewer who zoomed to
// 300% by hand to study a page keeps it when they dismiss a word.
let _zoomBeforeFocus = null;

function zoomToFocus(box) {
  if (zoomLevel < FOCUS_ZOOM) {
    if (_zoomBeforeFocus === null) _zoomBeforeFocus = zoomLevel;
    zoomLevel = FOCUS_ZOOM;
    applyZoom();          // applyZoom centres .hl-box.focused itself
  } else {
    box.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' });
  }
}

function restoreZoomAfterFocus() {
  if (_zoomBeforeFocus === null) return;
  zoomLevel = _zoomBeforeFocus;
  _zoomBeforeFocus = null;
  applyZoom(0.5, 0);      // no focused box left to centre on: show the page top
}
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
// FIXED STOPS, not `current +- 0.25` (reviewer 2026-09-02: "zoom -+ goes
// directly from 95% to 120. 100 seems pretty basic").
//
// The old buttons stepped by a quarter from wherever they happened to be, and
// the clamp is what broke it: from 100%, three zoom-outs give 75 -> 50 -> 30
// (clamped), and from 30 the way back is 55 -> 80 -> 105. One clamp knocks the
// value off the quarter grid and EVERY later step inherits the offset, so 100%
// becomes unreachable - as does any round number. The ctrl+wheel's 0.15 steps do
// the same thing faster.
//
// Stops make the clamp harmless and 100% always one click away, from anywhere,
// including from a value the wheel or the focus zoom left behind.
const ZOOM_STOPS = [0.3, 0.5, 0.75, 1, 1.25, 1.5, 2, 2.5, 3];

function zoomStep(direction) {
  const eps = 1e-6;   // 0.75 + 0.25 is not exactly 1 in binary floating point
  const next = direction > 0
    ? ZOOM_STOPS.find(z => z > zoomLevel + eps)
    : ZOOM_STOPS.slice().reverse().find(z => z < zoomLevel - eps);
  if (next === undefined) return;          // already at an end of the ladder
  // Touching the zoom by hand hands ownership back to the reviewer: whatever the
  // focus had stored is no longer theirs to restore.
  _zoomBeforeFocus = null;
  zoomLevel = next;
  applyZoom();
}

function setupZoomPan() {
  document.getElementById('zoom-in').onclick = () => zoomStep(+1);
  document.getElementById('zoom-out').onclick = () => zoomStep(-1);
  scanViewer.addEventListener('wheel', (e) => {
    if (e.ctrlKey || e.metaKey) {
      e.preventDefault();
      const delta = e.deltaY < 0 ? 0.15 : -0.15;
      _zoomBeforeFocus = null;   // same as the buttons: manual zoom wins
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
      const zoomThis = _zoomOnFocus;
      _zoomOnFocus = false;
      requestAnimationFrame(() => {
        if (zoomThis) zoomToFocus(box);
        else box.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' });
      });
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
  clearRoutedWord();          // the ring is half of the same gesture
  scanFocusCorr = null;
  _zoomOnFocus = false;   // a pending focus-zoom must not fire into a cleared view
  if (currentPage != null) showPage(currentPage, scanFocusKlalId, null);
  restoreZoomAfterFocus();
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
    updateScanHeader();
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
  // Draw the klal outline on whichever of its pages is being shown - only when
  // the reviewer hasn't clicked a specific word to focus, since then the yellow
  // .focused box is the landmark and a large gold box on top of it is noise.
  //
  // FIXED 2026-08-25 (reviewer, klal 4: "the highlight of the whole klal only
  // covers the first part on the first page, not the rest on the following").
  // This drew `region` and only on `focusKlal.page`, so a klal spanning pages
  // 15-16 outlined the sliver on 15 and nothing at all on 16 - where most of its
  // text actually is. The per-page boxes were already served in
  // `continuations[]` and simply never read: a field computed, serialized, and
  // never displayed (Lesson 29).
  let r = null;
  if (!focusCorr && focusKlal) {
    if (focusKlal.page === page) {
      r = focusKlal.region;
    } else {
      const cont = (focusKlal.continuations || []).find(c => c.page === page);
      if (cont) r = cont.bbox;
    }
  }
  if (r) {
    const box = document.createElement('div');
    box.className = 'hl-current-klal';
    box.style.left = (r.x1 * 100) + '%';
    box.style.top = (r.y1 * 100) + '%';
    box.style.width = ((r.x2 - r.x1) * 100) + '%';
    box.style.height = ((r.y2 - r.y1) * 100) + '%';
    hlContainer.appendChild(box);
    // ADDED 2026-08-31 (reviewer, klal 4: "doesn't move the scan to the correct
    // klal"). The outline was drawn correctly and could sit off-screen: klal 4
    // holds 40 of its 497 tokens on its start page, in the bottom 10% of it, so
    // a reviewer looking at the top of page 15 sees klal 3 and concludes the scan
    // never moved. 30 of 222 klalim start on a page holding under half their
    // text - klal 92 is 6%, klal 30 is 7% - so this is a class, not one klal.
    //
    // The reviewer's own rule: bottom of the page for a klal that ends it, top
    // for one that begins the next. `block: 'nearest'` expresses exactly that
    // without special-casing either - it scrolls the minimum that brings the
    // region into view, which lands at the bottom for a start-page sliver and the
    // top for a continuation. It is also a no-op when the whole page already fits,
    // which is the common case at 100%.
    requestAnimationFrame(() => box.scrollIntoView({ block: 'nearest', behavior: 'auto' }));
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
      // ADDED 2026-08-31: this is the box a DEEP LINK draws, and it carried no
      // click handler at all - so the one word a shared link exists to point at
      // was the one word clicking on the scan did nothing for. It has no
      // correction to open a panel for, so it only reveals the word in the text.
      box.style.cursor = 'pointer';
      box.addEventListener('click', () => revealWordInText(c.klal_id, c.word_index));
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
    clearTimeout(_noScanPositionTimer);   // a later render found it after all
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
      const zoomThis = _zoomOnFocus;
      _zoomOnFocus = false;
      requestAnimationFrame(() => {
        if (zoomThis) zoomToFocus(focusedBox);
        else focusedBox.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' });
      });
    }
  } else {
    _pendingScrollToBox = null; // superseded focus, cancel any pending scroll
    _zoomOnFocus = false;       // ...and disarm the zoom, or the NEXT render steals it
    // SAY SO when a word the reviewer asked for cannot be put on the scan.
    // 1,649 of Part 1's words have no aligned DocAI token at all, so there is
    // no box to draw and nothing to zoom to - and the pane simply sat there
    // looking like a bug, which is how it was reported ("it doesnt zoom in").
    // Only for an explicit word request: showPage() is also called with
    // focusCorr null on every scroll, and a toast on those would be constant.
    // DEFERRED AND CANCELLABLE. Routing to a word calls showPage() several times
    // - clearScanFocus, setActiveKlal, then focusWordOnScan - and the earlier
    // ones legitimately find no box because they are still on the previous page.
    // Announcing on the first miss fired this warning on words that DO get a
    // box a moment later (klal 88 w963 did, measured). Wait, and let a
    // successful render call it off.
    if (focusCorr && focusCorr.word_index != null) {
      clearTimeout(_noScanPositionTimer);
      _noScanPositionTimer = setTimeout(() => {
        showToast('That word has no OCR alignment, so it cannot be located on the '
                  + 'scan \u2014 showing the page it falls on.');
      }, 900);
    }
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
  // NOT awaited, deliberately - tried on 2026-08-31 and reverted. The theory was
  // that scrolling against an unmounted block's ESTIMATED height would land off
  // once the real content resized it; measured on a 188-klal jump it changed
  // nothing (settled 23px vs 45px, both correct), because the smooth scroll takes
  // ~1.5s and the mount lands long before it finishes. The symptom that suggested
  // it was a test sampling the position mid-scroll.
  mountKlal(klalId);
  block.scrollIntoView({ behavior: 'smooth', block: 'start' });
  releaseObserverWhenScrollSettles();
}

// FIXED 2026-08-31 (reviewer: "clicking on 105 in the index moves the text pane
// but not the scan" - item 0E, which had been recorded as open).
//
// The symptom was one klal off, not a dead pane: the scan DID go to page 44, but
// the observer set the active klal to 104 on the way past, so the header read
// "Klal 104" and the scan outlined 104's region while the text pane sat on 105.
//
// jumpTo() scrolls SMOOTHLY and used to release the observer after a FIXED 700ms,
// but a long jump takes ~1500ms to settle - measured klal 53 -> 12 at
// -11337, -3737, -893, -24, 12 px sampled every 300ms. For the remaining ~800ms
// the observer was live and overwrote the destination.
//
// A bigger constant would be the same bug with a longer fuse (Lesson 31: do not
// retune a heuristic, remove the guess). This waits for the scroll to ACTUALLY
// stop: two consecutive frames at the same offset, with a hard ceiling so a
// pane that never settles cannot suppress the observer forever.
// Where "which klal am I reading" is decided: the last block whose top is at or
// above this line. ONE definition, because updateActiveFromScroll() asks the
// question and releaseObserverWhenScrollSettles() has to give the same answer -
// they had the offset written out separately, and a jump that lands just past a
// line the jump code cannot see is a jump that undoes itself.
const READING_LINE_OFFSET = 48;

function readingLine() {
  return textScroll.getBoundingClientRect().top + READING_LINE_OFFSET;
}

function releaseObserverWhenScrollSettles(maxMs = 3000) {
  clearTimeout(suppressTimer);
  const started = performance.now();
  let last = null, stable = 0;
  const tick = () => {
    const now = Math.round(textScroll.scrollTop);
    stable = (now === last) ? stable + 1 : 0;
    last = now;
    if (stable >= 2 || performance.now() - started > maxMs) {
      // The observer was held off for the whole animation, so it never recorded
      // where we landed. Re-assert the destination rather than leaving whatever
      // the last scroll-driven update happened to set.
      //
      // FIXED 2026-09-02: re-asserting the LABEL was not enough. Klal blocks
      // mount lazily behind estimated placeholder heights, and the ones the jump
      // scrolls PAST resize as they mount - so the destination drifts below the
      // reading line while the animation is still running. setActiveKlal() then
      // wrote the right klal into the nav on top of a page whose geometry said
      // otherwise, and the first scroll event after the observer was released
      // recomputed the geometric answer and overwrote it: click klal 105, land on
      // 104. Re-seat the block BEFORE releasing, so the two agree.
      //
      // Order matters: the re-seat is an instant scroll, and doing it while the
      // observer is still suppressed keeps it from firing the very handler this
      // is defending against.
      if (lastActiveKlalId != null) {
        const block = document.getElementById('klal-block-' + lastActiveKlalId);
        // `> line` only: a block sitting ABOVE the line is already the answer,
        // and re-seating it would fight the reviewer at the end of the corpus,
        // where the container bottoms out and the last klalim CANNOT be scrolled
        // to the top. Those keep the re-asserted label (measured 2026-09-02:
        // klalim 221 and 222 land 218px and 546px past the line and no scroll
        // can fix it - there is nothing below them to scroll into).
        if (block && block.getBoundingClientRect().top > readingLine()) {
          block.scrollIntoView({ behavior: 'auto', block: 'start' });
        }
        setActiveKlal(lastActiveKlalId);
      }
      suppressObserverScroll = false;
      return;
    }
    requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

function setActiveKlal(klalId, navBlock) {
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
    // `navBlock` is 'center' for a DELIBERATE jump (a deep link, a nav click)
    // and undefined for the continuous scroll-driven reaction below.
    // FIXED 2026-08-31 (reviewer: "the index pane does not scroll all the way to
    // the actual klal"). 'nearest' scrolls the MINIMUM distance that makes the
    // row visible, which is right for the scroll reaction and wrong for a jump:
    // measured on /klal/210/word/133, the row landed at bottom 1001px against a
    // pane bottom of 1000px - one pixel PAST the fold, so the destination the
    // reviewer asked for was the one row they could not see. Centring a jump
    // also gives the surrounding klalim as context, which is the point of the
    // index pane.
    navEl.scrollIntoView({ block: navBlock || 'nearest', behavior: 'auto' });
  }
  const k = klalById[klalId];
  if (k) {
    _headerKlalId = klalId;
    updateScanHeader();
    updateTextHeader();
    // The work's name comes from /api/corpus like every other surface that
    // shows it (2026-09-01) - this was the last hardcoded "Yad Malachi" left in
    // the frontend, and a second book would have renamed every tab but this one.
    document.title = `Klal ${klalId} (כלל ${hebNum(klalId)}) · ${(CORPUS && CORPUS.title) || 'Review'}`;
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
  const line = readingLine();   // see READING_LINE_OFFSET - one definition
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
