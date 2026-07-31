import json
import re
import sys

def fix_sofit(text):
    # Sofit to regular
    sofit_map = {'ך': 'כ', 'ם': 'מ', 'ן': 'נ', 'ף': 'פ', 'ץ': 'צ'}
    def replace_sofit(match):
        return sofit_map[match.group(1)]
    
    # Match sofit letter followed by any word character (Hebrew letters included)
    # Actually, a sofit letter shouldn't be inside a word. 
    # Let's find any sofit letter that is immediately followed by a Hebrew letter
    # or immediately preceded by a Hebrew letter IF it's not the end of the word.
    # To be safe, just replace any sofit letter that has a Hebrew letter right after it.
    text = re.sub(r'([ךםןףץ])(?=[א-ת])', replace_sofit, text)
    return text

def fix_dr(text):
    # Hardcoded replacements based on prompt and common sense
    replacements = {
        'רחיה': 'דחיה',
        'דיעבר': 'דיעבד',
        'דבד': 'דבר',
        'הריוט': 'הדיוט',
        'רוא': 'הוא', # prompt says דוא? wait, 'רוא' -> 'דוא' or 'הוא'? Let's do 'דוא' and 'הוא' based on context. Wait, "שדוא" -> "שהוא".
        'שדוא': 'שהוא',
        'תודה': 'תורה',
        'עור': 'עוד',
        'חסרא': 'חסדא',
        'נלער': 'נלע"ד',
        'כמד': 'כמר',
        'אייךו': 'איירי', # kaph instead of resh
        'ידייא': 'איידי', 
        'הדואה': 'הרואה',
        'דדחי': 'דדחי',
        'טיניידו': 'מינייהו',
        'אכל': 'אבל'
    }
    # Wait, the prompt literally says:
    # "e.g. 'רחיה' -> 'דחיה', 'דיעבר' -> 'דיעבד', 'דבד' -> 'דבר', 'הריוט' -> 'הדיוט', 'רוא' -> 'דוא', 'תודה' -> 'תורה', 'עור' -> 'עוד', 'חסרא' -> 'חסדא', 'נלער' -> 'נלע"ד', 'כמד' -> 'כמר'."
    # Let's also do a word-by-word pass.
    # But wait, there might be other Dalet/Resh confusions not in the examples.
    return text

# Let's use an LLM API to fix the text? We don't have an LLM API in the script.
# We will just write a script that does the sofit replacement, and we will manually inspect the text.
