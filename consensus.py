import re
import difflib

# --- 1. NORMALIZATION ---
def normalize_hebrew(text):
    """
    Strips all punctuation, vowels (niqqud), and page artifacts.
    Leaves only pure Hebrew consonants (\u05D0-\u05EA) and single spaces.
    """
    clean_text = re.sub(r'[^\u05D0-\u05EA\s]', '', text)
    return re.sub(r'\s+', ' ', clean_text).strip()

# --- 2. TOKEN EXPANSION ---
def expand_to_word(text, start_idx, end_idx):
    """
    Expands character indices outward to the nearest whitespace boundaries
    to extract the full word containing the conflict.
    """
    # Find the start of the word by searching backward for a space
    word_start = text.rfind(' ', 0, start_idx)
    word_start = 0 if word_start == -1 else word_start + 1
    
    # Find the end of the word by searching forward for a space
    word_end = text.find(' ', end_idx)
    word_end = len(text) if word_end == -1 else word_end
    
    return text[word_start:word_end]

# --- 3. CONSENSUS & ALIGNMENT ---
def evaluate_consensus(base_text, witness_text):
    """
    Compares the base OCR against a witness.
    Extracts the full conflicting words when differences are found.
    """
    matcher = difflib.SequenceMatcher(None, base_text, witness_text)
    ratio = matcher.ratio()
    
    if ratio == 1.0:
        return True, "100% Consensus", []
    
    opcodes = matcher.get_opcodes()
    conflicts = [op for op in opcodes if op[0] != 'equal']
    
    extracted_conflicts = []
    for tag, i1, i2, j1, j2 in conflicts:
        base_word = expand_to_word(base_text, i1, i2)
        witness_word = expand_to_word(witness_text, j1, j2)
        
        extracted_conflicts.append({
            "tag": tag,
            "base_indices": (i1, i2),
            "witness_indices": (j1, j2),
            "base_word": base_word,
            "witness_word": witness_word
        })
        
    return False, f"Conflict Detected (Similarity: {ratio:.2%})", extracted_conflicts

if __name__ == "__main__":
    base_ocr_chunk = "כלל א הנה ענין הראשון הוא כך וכך"
    witness_2_chunk = "כלל א הנה ענין הראסון הוא כך וכך"
    
    base_norm = normalize_hebrew(base_ocr_chunk)
    w2_norm = normalize_hebrew(witness_2_chunk)
    
    print("Evaluating Witness 2 (Tesseract):")
    is_match, msg, conflicts = evaluate_consensus(base_norm, w2_norm)
    
    print(f"Status: {msg}\n")
    if not is_match:
        for c in conflicts:
            print(f"Action: {c['tag'].upper()}")
            print(f"Base text token:    '{c['base_word']}'")
            print(f"Witness text token: '{c['witness_word']}'")
            print(f"JSON Payload ready for Gemini: [\"{c['base_word']}\", \"{c['witness_word']}\"]")
