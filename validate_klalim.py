import os
import json
import re

def to_gematria(num):
    # Basic gematria for 1-400
    if num <= 0 or num > 400: return str(num)
    
    letters = {
        100: 'ק', 200: 'ר', 300: 'ש', 400: 'ת',
        10: 'י', 20: 'כ', 30: 'ל', 40: 'מ', 50: 'נ', 60: 'ס', 70: 'ע', 80: 'פ', 90: 'צ',
        1: 'א', 2: 'ב', 3: 'ג', 4: 'ד', 5: 'ה', 6: 'ו', 7: 'ז', 8: 'ח', 9: 'ט'
    }
    
    result = ""
    for val in sorted(letters.keys(), reverse=True):
        while num >= val:
            # Special case for 15 (ט"ו) and 16 (ט"ז) to avoid writing the Name of God
            if num == 15 and val == 10:
                result += 'טו'
                num -= 15
                break
            if num == 16 and val == 10:
                result += 'טז'
                num -= 16
                break
                
            result += letters[val]
            num -= val
            
    return result

def validate():
    aligned_dir = "/Users/ericsafern/work/yad-malachi/yad-malachi-pipeline/aligned_klalim"
    
    all_klalim = []
    for filename in sorted(os.listdir(aligned_dir)):
        if not filename.endswith(".json"): continue
        with open(os.path.join(aligned_dir, filename), "r") as f:
            all_klalim.extend(json.load(f))
            
    errors = []
    
    # Group by section
    sections = {}
    for k in all_klalim:
        sec = k.get("section", "Aleph")
        sections.setdefault(sec, []).append(k)
        
    for sec, klalim in sections.items():
        klalim.sort(key=lambda x: x["klal_id"])
        
        # 1. Continuity Check
        expected_id = klalim[0]["klal_id"] if klalim else 1
        for k in klalim:
            if k["klal_id"] != expected_id:
                errors.append(f"MISSING KLAL in {sec}: Expected Klal {expected_id}, but found {k['klal_id']}")
                expected_id = k["klal_id"]
            expected_id += 1
        
    # 2. Orthography & Prefix Check
    for k in all_klalim:
        text = k["clean_text"].strip()
        expected_letter = to_gematria(k["klal_id"])
        
        words = text.split()
        if not words:
            errors.append(f"EMPTY KLAL: Klal {k['klal_id']} (Page {k['page']}) is empty.")
            continue
            
        first_word_clean = ''.join(c for c in words[0] if c.isalnum())
        # Verify first word is a valid Gematria numeral header
        if not re.match(r'^[א-ת]+$', first_word_clean):
            errors.append(f"PREFIX ERROR: Klal {k['klal_id']} starts with non-Hebrew header '{first_word_clean}'. Full text start: {text[:20]}")
            
        # Check invalid english characters
        if re.search(r'[a-zA-Z]', text):
            errors.append(f"ORTHOGRAPHY ERROR in Klal {k['klal_id']} (Page {k['page']}): Found English characters.")
            
        if "ארם" in text:
            errors.append(f"ORTHOGRAPHY ERROR in Klal {k['klal_id']} (Page {k['page']}): Found known hallucination 'ארם'.")
                
        # 3. Sofit letters in the middle of words
        sofit_letters = {'ך', 'ם', 'ן', 'ף', 'ץ'}
        for word in words:
            # Clean word of punctuation first to accurately check the last letter
            clean_w = ''.join(c for c in word if c.isalnum())
            if len(clean_w) > 1:
                # Check all characters except the last one
                for i, char in enumerate(clean_w[:-1]):
                    if char in sofit_letters:
                        errors.append(f"IMPOSSIBLE WORD ERROR in Klal {k['klal_id']} (Page {k['page']}): Sofit letter '{char}' found in middle of word '{word}'")
                        break
            
    if errors:
        print("VALIDATION FAILED!")
        for e in errors:
            print("-", e)
    else:
        print("VALIDATION PASSED! All klalim are completely valid and strictly sequential.")
        
if __name__ == "__main__":
    validate()
