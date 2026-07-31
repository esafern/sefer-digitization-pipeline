import json
import glob
import re

fixes = {
    "אטת": "אמת",
    "משוס": "משום",
    "וכין": "ובין",
    "מיירו": "מיירי",
    "שחפך": "שהפך",
    "יומיח": "יומיה",
    "דמגילח": "דמגילה",
    "בחליכות": "בהליכות",
    "חמתחיל": "המתחיל",
    "בססחים": "בפסחים",
    "מלמר": "מלמד",
    "הטאת": "חטאת",
    "הלבה": "הלכה",
    "הפוסקיס": "הפוסקים",
    "קאטרינן": "קאמרינן",
    "רוזכר": "הוזכר",
    "רמכריע": "המכריע",
    "בירושלטי": "בירושלמי",
    "בכורורת": "בכורות",
    "אהרדי": "אהדדי",
    "איבא": "איכא",
    "בקירושין": "בקידושין",
    "דאיסליגו": "דאיפליגו",
    "דהולין": "דחולין",
    "טרורים": "טהורים",
    "יכום": "יבום",
    "וכתכו": "וכתבו",
    "כתכו": "כתבו",
    "שיעוד": "שיעור",
    "שיהבאתי": "שהבאתי",
    "שכרתבו": "שכתבו"
}

batch_files = glob.glob('klalim_batches/batch_*.json')
total_fixes = 0

for batch_file in batch_files:
    changed = False
    with open(batch_file, 'r') as f:
        try:
            klalim = json.load(f)
        except:
            continue
            
    for k in klalim:
        if 'clean_text' in k:
            text = k['clean_text']
            for wrong, right in fixes.items():
                # use regex with word boundaries to avoid replacing substrings
                # in Hebrew, word boundaries can be tricky, so we use (?<![א-ת])wrong(?![א-ת])
                pattern = f"(?<![א-ת]){wrong}(?![א-ת])"
                new_text, count = re.subn(pattern, right, text)
                if count > 0:
                    text = new_text
                    changed = True
                    total_fixes += count
            k['clean_text'] = text
            
    if changed:
        with open(batch_file, 'w') as f:
            json.dump(klalim, f, ensure_ascii=False, indent=2)

print(f"Applied {total_fixes} high-confidence fixes across the JSON batches.")
