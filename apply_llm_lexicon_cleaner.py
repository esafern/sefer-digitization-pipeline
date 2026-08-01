import re

garbled_salads = set([
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
    'התלמודפשזתידיבקמוושתיודתף',
    'ובדבמרשייאתאומוולהדרעתש',
    'ודהקאתונכילובמבתמניע',
    'והככדימוכנכלחעמדדבראימהתם',
    'וזיצליבשהקשו',
    'וללאדויכדתעינאאחרלימנהי',
    'ותלשבהבובאשתויתוכהערתמ',
    'יהיוהדוהדהשמ',
    'כוושבתמוצבאבטבפפזק',
    'כספלזונסיעהכביו',
    'לאאלאאמהרייכא',
    'לדבריובגהולל',
    'לתעניאלבהכדניילהעודנקט',
    'מבדפהאהאכיכש',
    'מבלגאואוכודעלעהד',
    'מקבישלהיאדילקיחהשיאתמבאעירילותא',
    'נמאימרשהובאמעקרדמבואן',
    'נרכאדהנקלטעדש',
    'סהיכייבטסתמא',
    'עלהשתווסבכתזולבותשתיירטצוב',
    'פדאאילולאנואמקרריאן',
    'פליגיכערליעה',
    'שובמרעששיהפיקה',
    'תמשקנלהטטקוונדלחיק'
])

typos_map = {
    'אחרינ ': 'אחרינן ',
    'גמירנ ': 'גמירנן ',
    'דאייתינ ': 'דאייתינן ',
    'דכתיבנ ': 'דכתיבנן ',
    'דמתורצ ': 'דמתורצא ',
    'דרמיזנ ': 'דרמיזנן ',
    'דתריצנ ': 'דתריצנן ',
    'התוספ ': 'התוספות '
}

def clean():
    with open('full_text_cleaned_goal.txt', 'r', encoding='utf-8') as f:
        text = f.read()

    # Apply typos replacements
    for old, new in typos_map.items():
        text = text.replace(old, new)

    lines = [l.strip() for l in text.split('\n') if l.strip()]

    cleaned_lines = []
    removed_count = 0

    for l in lines:
        words = l.split()
        clean_words = []
        for w in words:
            clean_w = re.sub(r'[^א-ת]', '', w)
            if clean_w in garbled_salads or (len(clean_w) > 11 and not any(q in w for q in ['"', "'", '״', '׳'])):
                print(f"Removed garbled salad: '{w}'")
                removed_count += 1
                continue
            clean_words.append(w)
        cleaned_lines.append(' '.join(clean_words))

    with open('full_text_cleaned_goal.txt', 'w', encoding='utf-8') as f:
        for cl in cleaned_lines:
            f.write(cl + '\n\n')

    print(f"Cleaned {removed_count} garbled tokens from full_text_cleaned_goal.txt!")

if __name__ == '__main__':
    clean()
