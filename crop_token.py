import fitz  # PyMuPDF
from bs4 import BeautifulSoup
import re

def crop_word_from_hocr(pdf_path, page_num, hocr_path, output_image_path, target_word_index=20, padding_px=15):
    print("Parsing hOCR data...")
    with open(hocr_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'lxml')
        
    # Find all tokens identified by Tesseract
    words = soup.find_all('span', class_='ocrx_word')
    
    if not words or len(words) <= target_word_index:
        print("Error: Target word index out of bounds.")
        return
        
    target_node = words[target_word_index]
    ocr_text = target_node.text.strip()
    title_attr = target_node.get('title', '')
    
    # Extract the bounding box coordinates (format: bbox x0 y0 x1 y1)
    match = re.search(r'bbox (\d+) (\d+) (\d+) (\d+)', title_attr)
    if not match:
        print("Error: No bounding box found for this token.")
        return
        
    x0, y0, x1, y1 = map(int, match.groups())
    print(f"Target token: '{ocr_text}' | Scaled coords: [{x0}, {y0}, {x1}, {y1}]")
    
    # Open the PDF to perform the crop
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_num)
    
    # Reverse the 300 DPI scaling applied in step 1 (300 / 72 = 4.1666)
    zoom = 300 / 72
    
    # Translate scaled coordinates back to PDF points, applying padding
    padding_pts = padding_px / zoom
    crop_rect = fitz.Rect(
        (x0 / zoom) - padding_pts,
        (y0 / zoom) - padding_pts,
        (x1 / zoom) + padding_pts,
        (y1 / zoom) + padding_pts
    )
    
    # Render ONLY that specific rectangle at high resolution
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, clip=crop_rect, alpha=False)
    
    pix.save(output_image_path)
    print(f"Success. Cropped context window saved to {output_image_path}")

if __name__ == "__main__":
    # We will target word #20 on the page, just to ensure we are into the main body text
    crop_word_from_hocr(
        pdf_path="berlin_square.pdf", 
        page_num=13, 
        hocr_path="berlin_page_14.hocr", 
        output_image_path="test_crop.png", 
        target_word_index=20, 
        padding_px=20
    )
