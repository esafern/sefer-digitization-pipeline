import re

garbled_words = [
    'אבחשדמעמצתיאנודלבחגומברעאעמללזככוונתותועמשתחולכפכותב',
    'אימתכיללואבמגהביוכור',
    'אמורבנזהינריחסאבלמאדובוכיובמווקתינלהכמבד',
    'אמרלותאאלאאמרבידבדרמסשתאמינועבתדלושיליבחיודתיהאחארבילם',
    'בוחללאבבאווכדלכשתילבונלארכקנלהעיכדא',
    'בתכלרליחהגבמי',
    'דאבהלקשליפיא',
    'דדפהלמכיתאשהוציאוהו',
    'דמאהמרעברודאתלעיזהרכבבדיהריוכראמדשגומם',
    'דמוהריהבגלמרואדמכולהלרשצאאשהאזרכידרברחיקירהתומס',
    'דקשעמכוראלמסיישקמלושדיט',
    'הלנאימאומקיר',
    'התלמודפשזתידיבקמוושתיודתף',
    'ובדבמרשייאתאומוולהדרעתש',
    'ודהקאתונכילובמבתמניע',
    'והככדימוכנכלחעמדדבראימהתם',
    'וזיצליבשהקשו',
    'וללאדויכדתעינאאחרלימנהי',
    'כוושבתמוצבאבטבפפזק',
    'כספלזונסיעהכביו'
]

def clean_garbled():
    with open('full_text_cleaned_goal.txt', 'r', encoding='utf-8') as f:
        text = f.read()

    lines = [l.strip() for l in text.split('\n') if l.strip()]

    cleaned_lines = []
    removed_count = 0

    for l in lines:
        words = l.split()
        clean_words = []
        for w in words:
            clean_w = re.sub(r'[^א-ת]', '', w)
            # Remove garbled words (> 12 letters without quotes)
            if len(clean_w) > 11 and not any(q in w for q in ['"', "'", '״', '׳']):
                print(f"Removing garbled token: '{w}'")
                removed_count += 1
                continue
            clean_words.append(w)
        cleaned_lines.append(' '.join(clean_words))

    with open('full_text_cleaned_goal.txt', 'w', encoding='utf-8') as f:
        for cl in cleaned_lines:
            f.write(cl + '\n\n')

    print(f"Removed {removed_count} garbled tokens from full_text_cleaned_goal.txt!")

if __name__ == '__main__':
    clean_garbled()
