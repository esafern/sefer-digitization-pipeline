import re

def fix():
    with open('full_text_cleaned_goal.txt', 'r', encoding='utf-8') as f:
        text = f.read()

    replacements = {
        'גופיייהו': 'גופייהו',
        'הההלכה': 'ההלכה',
        'ובריייתא': 'וברייתא',
        'וקבמסואטכהמ': '',
        'כככרן': 'כרן',
        'כתרווויהן': 'כתרווייהן',
        'עדייין': 'עדיין',
        'עמדיייותתי': '',
        'תהומרשהנ': ''
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    with open('full_text_cleaned_goal.txt', 'w', encoding='utf-8') as f:
        f.write(text)

    print("Fixed final typos and stripped garbled tokens!")

if __name__ == '__main__':
    fix()
