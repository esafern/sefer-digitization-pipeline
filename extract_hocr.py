import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io

def extract_hocr_from_page(pdf_path, page_num, output_path):
    print(f"Opening {pdf_path}...")
    doc = fitz.open(pdf_path)
    
    # Load the specific page (0-indexed)
    page = doc.load_page(page_num)
    
    # Render page to a high-res pixmap (300 DPI)
    zoom = 300 / 72
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    
    # Convert PyMuPDF pixmap to Pillow Image
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    
    print("Running Tesseract OCR (Hebrew)...")
    # Run Tesseract specifying Hebrew and asking for hOCR output
    hocr_data = pytesseract.image_to_pdf_or_hocr(img, lang='heb', extension='hocr')
    
    # Save the hOCR data
    with open(output_path, 'wb') as f:
        f.write(hocr_data)
        
    print(f"hOCR spatial data saved to {output_path}")

if __name__ == "__main__":
    # Test on page 14 (index 13) of the Berlin scan
    extract_hocr_from_page("./berlin_square.pdf", 13, "berlin_page_14.hocr")
