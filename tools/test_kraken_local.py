import os
import sys

os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import kraken
from kraken import binarization, pageseg
from PIL import Image

def main():
    image_path = "images/pdf_pages/page_18.png"
    if not os.path.exists(image_path):
        print(f"Image not found at {image_path}")
        return

    print("1. Opening sample scan page (Page 18)...")
    im = Image.open(image_path)

    print("2. Binarizing page with Kraken nlbin...")
    bw_im = binarization.nlbin(im)

    print("3. Segmenting lines with Kraken pageseg...")
    res = pageseg.segment(bw_im)
    lines = res.get('boxes', [])
    print(f"-> Successfully segmented {len(lines)} line bounding boxes on Page 18!")

if __name__ == "__main__":
    main()
