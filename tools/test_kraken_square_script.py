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

    print("Opening Page 18 scan image...")
    im = Image.open(image_path)
    bw_im = binarization.nlbin(im)
    res = pageseg.segment(bw_im)

    boxes = res.get('boxes', [])
    print(f"Kraken segmented {len(boxes)} line boxes.")
    # Show top 5 header boxes (square script section at top of page 18)
    for i, box in enumerate(boxes[:5]):
        print(f" Line {i+1}: {box}")

if __name__ == "__main__":
    main()
