import re

def fix():
    with open('full_text_cleaned_goal.txt', 'r', encoding='utf-8') as f:
        text = f.read()

    replacements = {
        'גופיייהו': 'גופייהו',
        'דאייתינ ': 'דאייתינן ',
        'דהלכ ': 'דהלכה ',
        'הלכ ': 'הלכה ',
        'ומזכ ': 'ומזכיר ',
        'יייז': 'י"ז',
        'שתמצ ': 'שתמצא '
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    with open('full_text_cleaned_goal.txt', 'w', encoding='utf-8') as f:
        f.write(text)

    print("Fixed 7 remaining typos in full_text_cleaned_goal.txt!")

if __name__ == '__main__':
    fix()
