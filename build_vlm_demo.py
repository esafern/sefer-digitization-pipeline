import os
import json

def build_demo():
    aligned_dir = "/Users/ericsafern/work/yad-malachi/yad-malachi-pipeline/aligned_klalim"
    out_html = "/Users/ericsafern/work/yad-malachi/yad-malachi-pipeline/SEFARIA-VLM-DEMO.html"
    
    # Load all aligned klalim
    all_klalim = []
    for filename in sorted(os.listdir(aligned_dir)):
        if not filename.endswith(".json"): continue
        with open(os.path.join(aligned_dir, filename), "r") as f:
            all_klalim.extend(json.load(f))
            
    # Sort by page and klal_id
    all_klalim.sort(key=lambda x: (x["page"], x["klal_id"]))
    
    # Group by page
    pages_map = {}
    for k in all_klalim:
        p = k["page"]
        if p not in pages_map:
            pages_map[p] = []
        pages_map[p].append(k)
        
    html = """
    <!DOCTYPE html>
    <html lang="he" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>Yad Malachi - VLM Architecture Demo</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Frank+Ruhl+Libre:wght@400;700&display=swap');
            
            body {
                font-family: 'Frank Ruhl Libre', serif;
                margin: 0;
                padding: 0;
                background-color: #f0f2f5;
                color: #2c3e50;
                display: flex;
                height: 100vh;
                overflow: hidden;
            }
            
            #sidebar {
                width: 400px;
                background: white;
                box-shadow: -2px 0 10px rgba(0,0,0,0.1);
                display: flex;
                flex-direction: column;
                z-index: 10;
            }
            
            .header {
                padding: 20px;
                background: #1a365d;
                color: white;
                text-align: center;
            }
            
            .header h1 {
                margin: 0;
                font-size: 24px;
            }
            
            .header p {
                margin: 5px 0 0 0;
                font-size: 14px;
                opacity: 0.8;
            }
            
            #klalim-list {
                flex: 1;
                overflow-y: auto;
                padding: 10px;
            }
            
            .klal-card {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 10px;
                cursor: pointer;
                transition: all 0.2s ease;
                box-shadow: 0 2px 4px rgba(0,0,0,0.02);
            }
            
            .klal-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 6px rgba(0,0,0,0.05);
                border-color: #3182ce;
            }
            
            .klal-card.active {
                background: #ebf8ff;
                border-color: #3182ce;
            }
            
            .klal-id {
                font-weight: bold;
                color: #2b6cb0;
                margin-bottom: 8px;
                font-size: 18px;
                display: flex;
                justify-content: space-between;
            }
            
            .klal-section {
                font-size: 12px;
                background: #bee3f8;
                padding: 2px 8px;
                border-radius: 12px;
                color: #2c5282;
            }
            
            .klal-text {
                font-size: 15px;
                line-height: 1.5;
                color: #4a5568;
                display: -webkit-box;
                -webkit-line-clamp: 3;
                -webkit-box-orient: vertical;
                overflow: hidden;
            }
            
            #viewer {
                flex: 1;
                background: #e2e8f0;
                position: relative;
                overflow: hidden;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            
            .page-container {
                position: relative;
                height: 95%;
                box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                background: white;
            }
            
            .page-image {
                height: 100%;
                width: auto;
                display: block;
            }
            
            .highlight-box {
                position: absolute;
                background-color: rgba(255, 235, 59, 0.3);
                border: 2px solid rgba(255, 193, 7, 0.8);
                border-radius: 4px;
                pointer-events: none;
                transition: all 0.3s ease;
                opacity: 0;
                transform: scale(0.98);
            }
            
            .highlight-box.active {
                opacity: 1;
                transform: scale(1);
                box-shadow: 0 0 15px rgba(255, 193, 7, 0.5);
                z-index: 20;
            }
            
            .page-overlay {
                position: absolute;
                top: 0; left: 0; right: 0; bottom: 0;
                pointer-events: none;
                background: rgba(0,0,0,0.4);
                transition: opacity 0.3s;
                opacity: 0;
                z-index: 5;
            }
            
            .page-overlay.active {
                opacity: 1;
            }
            
            .nav-btn {
                position: absolute;
                top: 50%;
                transform: translateY(-50%);
                background: rgba(255,255,255,0.9);
                border: none;
                border-radius: 50%;
                width: 50px;
                height: 50px;
                font-size: 24px;
                cursor: pointer;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                z-index: 30;
                display: flex;
                justify-content: center;
                align-items: center;
                color: #2d3748;
                transition: all 0.2s;
            }
            
            .nav-btn:hover {
                background: white;
                transform: translateY(-50%) scale(1.1);
            }
            
            .nav-prev { right: 20px; }
            .nav-next { left: 20px; }
            
            .page-indicator {
                position: absolute;
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%);
                background: rgba(0,0,0,0.7);
                color: white;
                padding: 8px 16px;
                border-radius: 20px;
                font-family: sans-serif;
                font-size: 14px;
                z-index: 30;
            }
        </style>
    </head>
    <body>
        <div id="sidebar">
            <div class="header">
                <h1>יד מלאכי - VLM Extraction</h1>
                <p>Clean Semantic Text + Precise Geometric Bounds</p>
            </div>
            <div id="klalim-list">
    """
    
    # Generate sidebar items
    for k in all_klalim:
        html += f"""
                <div class="klal-card" onclick="showKlal('{k['page']}', '{k['klal_id']}')" id="card-{k['page']}-{k['klal_id']}">
                    <div class="klal-id">
                        <span>כלל {k['klal_id']}</span>
                        <span class="klal-section">{k['section']}</span>
                    </div>
                    <div class="klal-text">{k['clean_text']}</div>
                </div>
        """
        
    html += """
            </div>
        </div>
        <div id="viewer">
            <button class="nav-btn nav-prev" onclick="prevPage()">&#10095;</button>
            <button class="nav-btn nav-next" onclick="nextPage()">&#10094;</button>
            <div class="page-indicator" id="page-indicator">Page 14</div>
            
            <div class="page-container" id="page-container">
                <img src="" class="page-image" id="page-img">
                <div class="page-overlay" id="page-overlay"></div>
                <div id="highlights-container"></div>
            </div>
        </div>

        <script>
            const klalimData = 
    """
    html += json.dumps(pages_map, ensure_ascii=False)
    html += """;
            
            const pages = Object.keys(klalimData).map(Number).sort((a,b) => a-b);
            let currentPageIdx = 0;
            let activeKlalId = null;
            
            function loadPage(pageIdx) {
                if(pageIdx < 0 || pageIdx >= pages.length) return;
                currentPageIdx = pageIdx;
                const pageNum = pages[currentPageIdx];
                
                document.getElementById('page-img').src = `images/pdf_pages/page_${pageNum}.png`;
                document.getElementById('page-indicator').innerText = `Page ${pageNum}`;
                
                const container = document.getElementById('highlights-container');
                container.innerHTML = '';
                
                const klalimOnPage = klalimData[pageNum] || [];
                klalimOnPage.forEach(k => {
                    const box = document.createElement('div');
                    box.className = 'highlight-box';
                    box.id = `hl-${k.page}-${k.klal_id}`;
                    
                    // We need to add padding since we only mapped the start/end words
                    // The width/height needs some buffer to cover the whole text block
                    // Since it's a normalized bounding box (0-100%), we just use the CSS percentages
                    const bbox = k.bbox || { top: 10, left: 10, width: 80, height: 10 };
                    box.style.top = (bbox.top - 1) + '%';
                    box.style.left = (bbox.left - 1) + '%';
                    box.style.width = (bbox.width + 2) + '%';
                    box.style.height = (bbox.height + 2) + '%';
                    
                    container.appendChild(box);
                });
                
                // Clear active states
                document.querySelectorAll('.klal-card').forEach(el => el.classList.remove('active'));
                document.getElementById('page-overlay').classList.remove('active');
            }
            
            function showKlal(pageNum, klalId) {
                pageNum = parseInt(pageNum);
                const pageIdx = pages.indexOf(pageNum);
                if(pageIdx !== currentPageIdx) {
                    loadPage(pageIdx);
                }
                
                // Set active card
                document.querySelectorAll('.klal-card').forEach(el => el.classList.remove('active'));
                document.getElementById(`card-${pageNum}-${klalId}`).classList.add('active');
                
                // Set active highlight
                document.querySelectorAll('.highlight-box').forEach(el => el.classList.remove('active'));
                const hl = document.getElementById(`hl-${pageNum}-${klalId}`);
                if(hl) {
                    hl.classList.add('active');
                    document.getElementById('page-overlay').classList.add('active');
                    
                    // Scroll sidebar
                    const card = document.getElementById(`card-${pageNum}-${klalId}`);
                    card.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
            
            function nextPage() { loadPage(currentPageIdx + 1); }
            function prevPage() { loadPage(currentPageIdx - 1); }
            
            // Initialize
            loadPage(0);
        </script>
    </body>
    </html>
    """
    
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html)
        
    print(f"Generated {out_html}")

if __name__ == "__main__":
    build_demo()
