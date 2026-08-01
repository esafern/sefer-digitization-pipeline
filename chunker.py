import fitz
import re
import json
import os

def unreverse_line(line):
    """
    Un-reverses reversed Hebrew lines from 19th-century scanned PDFs.
    If the string is reversed (starts with punctuation/numbers or reversed letters),
    we flip it back to standard R-to-L reading order.
    """
    cleaned = line.strip()
    if not cleaned:
        return ""
    # Check if Hebrew text is reversed
    hebrew_chars = [c for c in cleaned if '\u0590' <= c <= '\u05FF']
    if len(hebrew_chars) > 0:
        # Flipping string restores standard Hebrew reading order for boustrophedon PDFs
        return cleaned[::-1]
    return cleaned

def extract_klalim_from_berlin(pdf_path="berlin_square.pdf", output_dir="./klalim", max_pages=60):
    os.makedirs(output_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    
    print(f"Scanning '{pdf_path}' ({len(doc)} pages total) for Klalim boundaries...")
    
    klalim = []
    current_klal = None
    
    # Matching Klal headers like 'כלל א', 'כלל ב', 'כג אין למדין', etc.
    klal_pattern = re.compile(r'^\s*([א-ת]{1,3}\s+)?(כלל\s+[א-ת"\']+)\b')
    
    for page_num in range(13, min(max_pages, len(doc))):
        raw_text = doc[page_num].get_text("text")
        raw_lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
        
        # Un-reverse every line for correct Hebrew reading order
        unreversed_lines = [unreverse_line(l) for l in raw_lines]
        
        for line in unreversed_lines:
            # Check for Klal section headers
            match = klal_pattern.search(line)
            if match or line.startswith("כלל ") or " כלל " in line:
                klal_title = line.strip()
                if current_klal and len(current_klal["lines"]) > 5:
                    klalim.append(current_klal)
                
                current_klal = {
                    "klal_id": len(klalim) + 1,
                    "klal_title": klal_title[:60],
                    "section": "Klalei HaGemara - Otiot (Aleph)",
                    "start_page": page_num + 1,
                    "lines": [line]
                }
            elif current_klal:
                current_klal["lines"].append(line)
    
    if current_klal:
        klalim.append(current_klal)
        
    doc.close()
    
    print(f"Successfully extracted {len(klalim)} Klalim across pages 14–{max_pages}.")
    
    # Save individual Klal JSON files
    for k in klalim:
        klal_filename = os.path.join(output_dir, f"klal_{k['klal_id']:03d}.json")
        k["full_text"] = "\n".join(k.pop("lines"))
        with open(klal_filename, "w", encoding="utf-8") as f:
            json.dump(k, f, ensure_ascii=False, indent=2)
        print(f"  • Wrote {klal_filename}: {k['klal_title']} (Page {k['start_page']}, {len(k['full_text'].split())} words)")

    return klalim

if __name__ == "__main__":
    extract_klalim_from_berlin("berlin_square.pdf", output_dir="./klalim", max_pages=60)
