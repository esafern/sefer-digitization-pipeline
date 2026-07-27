import re

def chunk_hebrew_text(raw_text, anchor_regex):
    """
    Splits a continuous string of Hebrew text into isolated chunks based on a regex anchor.
    Uses a lookahead assertion to ensure the structural anchor remains in the resulting chunk.
    """
    # Split the text. The lookahead (?=) ensures we slice immediately before the match.
    chunks = re.split(anchor_regex, raw_text)
    
    # Clean up whitespace and filter out any empty chunks caused by leading text
    processed_chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
    
    return processed_chunks

if __name__ == "__main__":
    # A simulated raw OCR output containing a preface and two distinct sections
    sample_ocr = (
        "הקדמה לכל הספר ברוך השם וכו. \n"
        "כלל א הנה ענין הראשון הוא כך וכך \n"
        "שלא לעשות טעויות. \n"
        "כלל ב וזה הענין השני שצריך לדעת \n"
        "כדי להבין את הכלל הראשון."
    )
    
    # The Regex Pattern:
    # (?=     -> Positive lookahead (split right before this matches)
    # \bכלל\b -> The exact word 'כלל' with word boundaries
    # \s+     -> One or more spaces
    # [א-ת]   -> A single Hebrew letter (Aleph through Tav)
    regex_pattern = r'(?=\bכלל\b\s+[א-ת])'
    
    print("Slicing raw OCR text into bounded contexts...\n")
    chunks = chunk_hebrew_text(sample_ocr, regex_pattern)
    
    print(f"Total chunks extracted: {len(chunks)}\n")
    for i, chunk in enumerate(chunks, 1):
        print(f"--- Chunk {i} ---")
        print(chunk)
        print("-" * 15 + "\n")
