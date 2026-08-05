# [PRODUCTION] Build review.html: a 3-pane human-review tool for Part 1 (klal 1-222).
# Left: scanned page with the specific corrected/flagged words highlighted.
# Middle: continuous, scrolling final text with changed words marked; hover shows
#         the original DocAI OCR reading + vision-verified confidence.
# Right: abridged klal list for navigation.
# All three panes stay in sync as you scroll or click.
#
# Page attribution comes from header_anchored_alignment.py's output
# (part1_header_anchored_alignment.json), NOT aligned_klalim - see CLAUDE.md
# Open Items / Lessons learned: that mapping was discredited (found to be
# wrong via first-principles re-verification against each page's own printed
# section header). Only `trusted` klalim get a page shown; the rest have no
# reliable scan location to point at.
import json
import os

REPO = os.path.dirname(os.path.abspath(__file__))
PART1_MAX_KLAL = 222

FLAG_LABELS = {
    "current_text_may_be_wrong": ("May be wrong", "#e53e3e"),
    "possible_omission": ("Possibly missing", "#805ad5"),
    "current_text_confirmed": ("Confirmed", "#38a169"),
    "unverified_insertion": ("Unverified addition", "#a0aec0"),
    "ambiguous": ("Ambiguous", "#dd6b20"),
    "error": ("Check failed", "#718096"),
    "human_corrected_vision_override": ("Human-corrected (overrides vision)", "#3182ce"),
}


def main():
    demo = json.load(open(os.path.join(REPO, "klalim_demo_dataset.json")))
    klalim = [k for k in demo if k["klal_id"] <= PART1_MAX_KLAL]
    klalim.sort(key=lambda k: k["klal_id"])

    alignment = {r["klal_id"]: r for r in json.load(open(os.path.join(REPO, "part1_header_anchored_alignment.json")))}
    trusted_page_of = {kid: r["matched_page"] for kid, r in alignment.items() if r["trusted"]}

    corrections = json.load(open(os.path.join(REPO, "corrections_part1.json")))

    regions_path = os.path.join(REPO, "klal_page_regions.json")
    regions = json.load(open(regions_path, encoding="utf-8")) if os.path.exists(regions_path) else {}

    for k in klalim:
        k["page"] = trusted_page_of.get(k["klal_id"])
        k["page_trusted"] = k["klal_id"] in trusted_page_of
        k["corrections"] = corrections.get(str(k["klal_id"]), [])
        k["region"] = regions.get(str(k["klal_id"]), {}).get("bbox")

    pages_with_corrections = sorted(set(
        c["page"] for entries in corrections.values() for c in entries if c.get("page")
    ))

    data_json = json.dumps(klalim, ensure_ascii=False)
    flags_json = json.dumps(FLAG_LABELS, ensure_ascii=False)

    html = HTML_TEMPLATE.replace("__KLALIM_DATA__", data_json).replace("__FLAG_LABELS__", flags_json)

    out_path = os.path.join(REPO, "review.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    total_corr = sum(len(k["corrections"]) for k in klalim)
    print(f"Wrote {out_path}: {len(klalim)} klalim, {total_corr} flagged corrections, "
          f"{len(pages_with_corrections)} pages with at least one flag")


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<title>Yad Malachi — Correction Review</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Frank+Ruhl+Libre:wght@400;700&display=swap');

  * { box-sizing: border-box; }
  body {
    font-family: 'Frank Ruhl Libre', serif;
    margin: 0; padding: 0;
    background: #f0f2f5;
    color: #2c3e50;
    display: flex;
    height: 100vh;
    overflow: hidden;
  }

  /* ---------- LEFT: scan ---------- */
  #scan-pane {
    width: 34%;
    background: #e2e8f0;
    display: flex;
    flex-direction: column;
    border-left: 1px solid #cbd5e0;
  }
  #scan-header {
    padding: 10px 16px;
    background: #1a365d;
    color: white;
    font-size: 13px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    direction: ltr;
  }
  #zoom-controls { display: flex; align-items: center; gap: 6px; }
  #zoom-controls button {
    width: 22px; height: 22px;
    border: none; border-radius: 4px;
    background: rgba(255,255,255,0.15);
    color: white;
    font-size: 15px;
    line-height: 1;
    cursor: pointer;
  }
  #zoom-controls button:hover { background: rgba(255,255,255,0.3); }
  #zoom-level { font-size: 11px; min-width: 34px; text-align: center; opacity: .85; }
  #scan-viewer {
    flex: 1;
    position: relative;
    overflow: auto;
    /* NOT display:flex + justify-content:center - that centers via the flex
       algorithm, which only creates scrollable space on one side of the
       overflow. Once the page is zoomed past the viewport, half the image
       becomes permanently unreachable by scroll. margin:auto on the child
       gives the same centered-when-small look but full scroll range in
       every direction once it's larger than the viewport. */
    padding: 16px 0;
    cursor: grab;
  }
  #scan-viewer.panning { cursor: grabbing; }
  #page-container {
    position: relative;
    display: table;
    margin: 0 auto;
    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    background: white;
  }
  #page-img { display: block; width: 480px; height: auto; -webkit-user-drag: none; user-select: none; }
  #hl-container { position: absolute; inset: 0; overflow: hidden; }
  .hl-box {
    position: absolute;
    border-radius: 3px;
    border: 2px solid;
    cursor: help;
    transition: opacity .15s ease;
  }
  .hl-box.dim { opacity: 0.35; }
  .hl-current-klal {
    position: absolute;
    border-radius: 4px;
    border: 3px solid #d69e2e;
    background: rgba(236, 201, 75, 0.18);
    pointer-events: none;
    transition: top .15s ease, left .15s ease, width .15s ease, height .15s ease, opacity .15s ease;
  }
  .page-nav-btn {
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    z-index: 5;
    width: 34px; height: 34px;
    border-radius: 50%;
    border: none;
    background: rgba(26, 54, 93, 0.85);
    color: white;
    font-size: 16px;
    cursor: pointer;
    display: flex; align-items: center; justify-content: center;
  }
  .page-nav-btn:hover { background: #1a365d; }
  .page-nav-btn:disabled { opacity: 0.3; cursor: default; }
  .page-nav-btn:disabled:hover { background: rgba(26, 54, 93, 0.85); }
  #page-nav-prev { right: 10px; }
  #page-nav-next { left: 10px; }

  /* ---------- MIDDLE: running text ---------- */
  #text-pane {
    flex: 1;
    display: flex;
    flex-direction: column;
    background: white;
    min-width: 0;
  }
  #text-header {
    padding: 10px 20px;
    background: #2b6cb0;
    color: white;
    font-size: 13px;
  }
  #text-scroll {
    flex: 1;
    overflow-y: auto;
    padding: 24px 32px;
    line-height: 1.9;
    font-size: 17px;
  }
  .klal-block { margin-bottom: 28px; scroll-margin-top: 12px; }
  .klal-block .klal-head {
    font-weight: bold;
    color: #2b6cb0;
    font-size: 14px;
    margin-bottom: 6px;
    display: flex;
    gap: 10px;
    align-items: baseline;
  }
  .klal-block .klal-head .sec { font-weight: normal; color: #718096; font-size: 12px; }
  .klal-body { color: #2d3748; }

  .flag-word {
    border-bottom: 3px solid;
    cursor: help;
    border-radius: 2px;
    padding: 0 1px;
  }
  .flag-gap {
    display: inline-block;
    width: 8px;
    height: 14px;
    margin: 0 2px;
    border-radius: 2px;
    cursor: help;
    vertical-align: middle;
  }
  .editorial-mark {
    color: #3182ce;
    font-weight: bold;
    cursor: help;
    opacity: 0.85;
  }

  /* ---------- RIGHT: abridged nav ---------- */
  #nav-pane {
    width: 420px;
    flex-shrink: 0;
    background: white;
    border-right: 1px solid #e2e8f0;
    display: flex;
    flex-direction: column;
  }
  #nav-header {
    padding: 16px;
    background: #1a365d;
    color: white;
  }
  #nav-header h1 { margin: 0; font-size: 17px; }
  #nav-header p { margin: 4px 0 0; font-size: 11px; opacity: .8; }
  #nav-list { flex: 1; overflow-y: auto; padding: 6px; }
  .nav-item {
    padding: 8px 10px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 13px;
    display: flex;
    justify-content: space-between;
    gap: 6px;
    align-items: center;
  }
  .nav-item:hover { background: #ebf8ff; }
  .nav-item.active { background: #bee3f8; }
  .nav-item .nid { color: #2b6cb0; font-weight: bold; min-width: 34px; }
  .nav-item .ntitle { flex: 1; min-width: 0; color: #4a5568; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .nav-item .ncount {
    background: #e53e3e; color: white; border-radius: 10px;
    font-size: 10px; padding: 1px 6px; display: none;
  }
  .nav-item.has-flags .ncount { display: inline-block; }

  /* ---------- tooltip ---------- */
  #tooltip {
    position: fixed;
    max-width: 360px;
    background: #1a202c;
    color: #f7fafc;
    padding: 10px 14px;
    border-radius: 8px;
    font-size: 13px;
    line-height: 1.5;
    box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    z-index: 999;
    display: none;
    pointer-events: none;
    direction: ltr;
    text-align: left;
    unicode-bidi: isolate;
  }
  #tooltip .t-flag { font-weight: bold; margin-bottom: 4px; display: block; }
  #tooltip .t-docai { display: block; margin-bottom: 6px; }
  #tooltip .t-conf { color: #a0aec0; font-size: 11px; display: block; }

  #legend {
    padding: 8px 16px;
    font-size: 11px;
    color: #4a5568;
    background: #f7fafc;
    border-top: 1px solid #e2e8f0;
    display: flex;
    gap: 14px;
    flex-wrap: wrap;
  }
  #legend span { display: inline-flex; align-items: center; gap: 5px; }
  #legend i { width: 10px; height: 10px; border-radius: 2px; display: inline-block; }
</style>
</head>
<body>

  <div id="nav-pane">
    <div id="nav-header">
      <h1>Yad Malachi</h1>
      <p>Klalei HaGemara — Part 1 — Correction review</p>
    </div>
    <div id="nav-list"></div>
    <div id="legend"></div>
  </div>

  <div id="text-pane">
    <div id="text-header">Full text — changed words are underlined; hover for the original OCR reading and confidence.</div>
    <div id="text-scroll"></div>
  </div>

  <div id="scan-pane">
    <div id="scan-header">
      <span><span id="page-indicator">Page —</span> <span id="klal-indicator"></span></span>
      <span id="zoom-controls">
        <button id="zoom-out" title="Zoom out">−</button>
        <span id="zoom-level">100%</span>
        <button id="zoom-in" title="Zoom in">+</button>
      </span>
    </div>
    <div id="scan-viewer">
      <button id="page-nav-prev" class="page-nav-btn" title="Previous page">&#8250;</button>
      <button id="page-nav-next" class="page-nav-btn" title="Next page">&#8249;</button>
      <div id="page-container">
        <img id="page-img" src="">
        <div id="hl-container"></div>
      </div>
    </div>
  </div>

  <div id="tooltip"></div>

<script>
const KLALIM = __KLALIM_DATA__;
const FLAGS = __FLAG_LABELS__;

const byId = {};
KLALIM.forEach(k => byId[k.klal_id] = k);

// ---------- build right nav ----------
const navList = document.getElementById('nav-list');
KLALIM.forEach(k => {
  const item = document.createElement('div');
  item.className = 'nav-item' + (k.corrections.length ? ' has-flags' : '');
  item.id = 'nav-' + k.klal_id;
  item.onclick = () => jumpTo(k.klal_id);
  item.innerHTML = `<span class="nid">${k.klal_id}</span><span class="ntitle" title="${(k.title || '').replace(/"/g, '&quot;')}">${k.title || ''}</span><span class="ncount">${k.corrections.length}</span>`;
  navList.appendChild(item);
});

// ---------- legend ----------
const legend = document.getElementById('legend');
Object.entries(FLAGS).forEach(([key, [label, color]]) => {
  const span = document.createElement('span');
  span.innerHTML = `<i style="background:${color}"></i>${label}`;
  legend.appendChild(span);
});

// ---------- build middle running text ----------
const textScroll = document.getElementById('text-scroll');
KLALIM.forEach(k => {
  const block = document.createElement('div');
  block.className = 'klal-block';
  block.id = 'klal-block-' + k.klal_id;
  block.dataset.klalId = k.klal_id;
  block.dataset.page = k.page || '';

  const head = document.createElement('div');
  head.className = 'klal-head';
  head.innerHTML = `<span>כלל ${k.klal_id}</span><span class="sec">${k.section || ''}</span>`;
  block.appendChild(head);

  const body = document.createElement('div');
  body.className = 'klal-body';

  const words = (k.clean_text || '').split(' ');
  const byIndex = {};
  k.corrections.forEach(c => {
    if (c.opcode !== 'delete') byIndex[c.word_index] = c;
  });
  // 'delete' corrections mark a gap BEFORE this word index (nothing to underline).
  const gapsBefore = {};
  k.corrections.forEach(c => {
    if (c.opcode === 'delete') {
      gapsBefore[c.word_index] = gapsBefore[c.word_index] || [];
      gapsBefore[c.word_index].push(c);
    }
  });

  words.forEach((w, i) => {
    if (gapsBefore[i]) {
      gapsBefore[i].forEach(c => body.appendChild(makeGapMarker(c)));
    }
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
      span.className = 'flag-word';
      const [, color] = FLAGS[corr.flag] || [null, '#a0aec0'];
      span.style.borderBottomColor = color;
      span.textContent = w;
      attachTooltip(span, corr);
      body.appendChild(span);
    } else {
      body.appendChild(document.createTextNode(w));
    }
    body.appendChild(document.createTextNode(' '));
  });

  block.appendChild(body);
  textScroll.appendChild(block);
});

function makeGapMarker(corr) {
  const span = document.createElement('span');
  span.className = 'flag-gap';
  const [, color] = FLAGS[corr.flag] || [null, '#a0aec0'];
  span.style.background = color;
  attachTooltip(span, corr, true);
  return span;
}

// ---------- tooltip ----------
const tooltip = document.getElementById('tooltip');
function attachTooltip(el, corr, isGap) {
  const [label] = FLAGS[corr.flag] || ['Flagged'];
  el.addEventListener('mouseenter', (e) => {
    const confTxt = (corr.confidence != null) ? (Math.round(corr.confidence * 100) + '% confidence') : 'not scan-verified';
    const hebrewBit = `<bdi>${corr.docai_reading || (isGap ? '' : '(none)')}</bdi>`;
    const docaiTxt = isGap
      ? `Scan appears to show: "${hebrewBit}" — not present in current text`
      : `Original OCR reading: "${hebrewBit}"`;
    // A human_correction_note means a person overrode the vision model's own
    // decision after the fact - show that explanation instead of the vision
    // model's (now-superseded) confidence/reasoning, which would otherwise
    // contradict the word actually displayed in the text pane.
    const bodyTxt = corr.human_correction_note
      ? `<span class="t-conf">${corr.human_correction_note}</span>`
      : `<span class="t-conf">${confTxt}${corr.reasoning ? ' — ' + corr.reasoning : ''}</span>`;
    tooltip.innerHTML = `<span class="t-flag">${label}</span><span class="t-docai">${docaiTxt}</span>${bodyTxt}`;
    tooltip.style.display = 'block';
    positionTooltip(e);
  });
  el.addEventListener('mousemove', positionTooltip);
  el.addEventListener('mouseleave', () => { tooltip.style.display = 'none'; });
  el.addEventListener('click', () => highlightOnScan(corr));
}
function positionTooltip(e) {
  const pad = 16;
  let x = e.clientX + pad, y = e.clientY + pad;
  if (x + 380 > window.innerWidth) x = e.clientX - 380;
  tooltip.style.left = x + 'px';
  tooltip.style.top = y + 'px';
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
  // Preserve whatever point in the image was centered in the viewport
  // before the zoom change - otherwise every +/- click recenters on the
  // image's middle and the user loses whatever region they'd panned to.
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
document.getElementById('zoom-in').onclick = () => { zoomLevel = Math.min(3, zoomLevel + 0.25); applyZoom(); };
document.getElementById('zoom-out').onclick = () => { zoomLevel = Math.max(0.3, zoomLevel - 0.25); applyZoom(); };
pageImg.addEventListener('load', () => applyZoom(0.5, 0));
applyZoom(0.5, 0);

// ---------- click-and-drag panning ----------
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

function showPage(page, focusKlalId) {
  if (page !== currentPage) {
    currentPage = page;
    pageImg.src = `images/pdf_pages/page_${page}.png`;
    pageIndicator.textContent = 'Page ' + page;
  }
  updatePageNavButtons();
  hlContainer.innerHTML = '';

  // "You are here": the current klal's own text region, independent of
  // whether it has any flagged corrections (most klalim don't).
  const focusKlal = byId[focusKlalId];
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

  KLALIM.filter(k => k.page === page).forEach(k => {
    k.corrections.forEach(c => {
      if (!c.bbox) return;
      const box = document.createElement('div');
      box.className = 'hl-box' + (k.klal_id === focusKlalId ? '' : ' dim');
      const [, color] = FLAGS[c.flag] || [null, '#a0aec0'];
      box.style.borderColor = color;
      box.style.background = color + '33';
      box.style.left = (c.bbox.x1 * 100) + '%';
      box.style.top = (c.bbox.y1 * 100) + '%';
      box.style.width = ((c.bbox.x2 - c.bbox.x1) * 100) + '%';
      box.style.height = ((c.bbox.y2 - c.bbox.y1) * 100) + '%';
      attachTooltip(box, c);
      hlContainer.appendChild(box);
    });
  });
}

function highlightOnScan(corr) {
  if (!corr.page) return;
  showPage(corr.page, corr.klal_id);
}

// ---------- page-to-page nav (left pane) ----------
const pagesWithKlalim = Array.from(new Set(KLALIM.filter(k => k.page).map(k => k.page))).sort((a, b) => a - b);
const firstKlalOfPage = {};
KLALIM.forEach(k => {
  if (k.page && !(k.page in firstKlalOfPage)) firstKlalOfPage[k.page] = k.klal_id;
});
const prevBtn = document.getElementById('page-nav-prev');
const nextBtn = document.getElementById('page-nav-next');

function updatePageNavButtons() {
  const idx = pagesWithKlalim.indexOf(currentPage);
  prevBtn.disabled = idx <= 0;
  nextBtn.disabled = idx === -1 || idx >= pagesWithKlalim.length - 1;
}
function goToPageOffset(offset) {
  const idx = pagesWithKlalim.indexOf(currentPage);
  if (idx === -1) return;
  const targetPage = pagesWithKlalim[idx + offset];
  if (targetPage == null) return;
  const targetKlal = firstKlalOfPage[targetPage];
  if (targetKlal != null) jumpTo(targetKlal);
}
prevBtn.onclick = () => goToPageOffset(-1);
nextBtn.onclick = () => goToPageOffset(1);

// ---------- nav / sync ----------
let suppressObserver = false;
let suppressTimer = null;

function jumpTo(klalId) {
  const block = document.getElementById('klal-block-' + klalId);
  if (!block) return;
  // Pin the clicked klal immediately - the IntersectionObserver fires
  // repeatedly during the smooth-scroll animation and can otherwise settle
  // on the next block instead of the one that was actually clicked.
  suppressObserver = true;
  lastActiveKlalId = klalId;
  setActiveKlal(klalId);
  block.scrollIntoView({ behavior: 'smooth', block: 'start' });
  clearTimeout(suppressTimer);
  suppressTimer = setTimeout(() => { suppressObserver = false; }, 700);
}

function setActiveKlal(klalId) {
  document.querySelectorAll('.nav-item.active').forEach(el => el.classList.remove('active'));
  const navEl = document.getElementById('nav-' + klalId);
  if (navEl) navEl.classList.add('active');
  const k = byId[klalId];
  if (k) {
    klalIndicator.textContent = 'כלל ' + klalId;
    if (k.page) showPage(k.page, klalId);
  }
}

// Scroll-spy: the active klal is whichever block's top edge has most recently
// scrolled past a line near the top of the middle pane. Far more predictable
// than IntersectionObserver's "largest visible ratio wins" when blocks vary
// a lot in height (some klalim are one line, some are hundreds of words).
const allBlocks = Array.from(document.querySelectorAll('.klal-block'));
let lastActiveKlalId = null;

function updateActiveFromScroll() {
  const containerTop = textScroll.getBoundingClientRect().top;
  const line = containerTop + 48;
  let current = allBlocks[0];
  for (const block of allBlocks) {
    if (block.getBoundingClientRect().top <= line) {
      current = block;
    } else {
      break;
    }
  }
  const klalId = parseInt(current.dataset.klalId);
  if (klalId !== lastActiveKlalId) {
    lastActiveKlalId = klalId;
    setActiveKlal(klalId);
  }
}

let scrollScheduled = false;
textScroll.addEventListener('scroll', () => {
  if (suppressObserver || scrollScheduled) return;
  scrollScheduled = true;
  requestAnimationFrame(() => {
    scrollScheduled = false;
    updateActiveFromScroll();
  });
});

// init
lastActiveKlalId = KLALIM[0].klal_id;
setActiveKlal(lastActiveKlalId);
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
