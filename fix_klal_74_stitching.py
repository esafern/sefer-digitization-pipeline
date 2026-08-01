import re

def fix_stitching():
    with open('full_text_cleaned_goal.txt', 'r', encoding='utf-8') as f:
        content = f.read()

    lines = [l.strip() for l in content.split('\n') if l.strip()]
    
    print(f"Initial line count: {len(lines)}")

    # Locate line 147 (Klal 74, starting 'עד אמר ר') and line 149 (starting 'עה רבא אמר')
    # Merge line 149 content into line 147 after removing 'עה ' prefix
    
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('עד אמר ר') and i + 1 < len(lines) and lines[i+1].startswith('עה רבא אמר'):
            # Combine Klal 74 first half and second half
            second_half = lines[i+1][len('עה '):] # strip 'עה ' prefix
            combined_klal_74 = line + ' ' + second_half
            new_lines.append(combined_klal_74)
            i += 2 # Skip the second half line
        elif line.startswith('עו אמר ר \' פלוני משום'):
            # This is printed Klal 75 (עה)
            new_lines.append(line.replace('עו אמר ר', 'עה אמר ר', 1))
            i += 1
        elif line.startswith('עז אינו אלא מן המתמיהין'):
            new_lines.append(line.replace('עז אינו אלא', 'עו אינו אלא', 1))
            i += 1
        elif line.startswith('עח אי אפשר מצינו'):
            new_lines.append(line.replace('עח אי אפשר', 'עז אי אפשר', 1))
            i += 1
        elif line.startswith('עט אכן לא שמיעא לן'):
            new_lines.append(line.replace('עט אכן', 'עח אכן', 1))
            i += 1
        elif line.startswith('פ או לאו דקאמרת'):
            new_lines.append(line.replace('פ או לאו', 'עט או לאו', 1))
            i += 1
        elif line.startswith('פא אלמא קסבר'):
            new_lines.append(line.replace('פא אלמא', 'פ אלמא', 1))
            i += 1
        elif line.startswith('פב בעיא באת"ל'):
            new_lines.append(line.replace('פב בעיא', 'פא בעיא', 1))
            i += 1
        elif line.startswith('פג בשר סופרים'):
            new_lines.append(line.replace('פג בשר', 'פב בשר', 1))
            i += 1
        elif line.startswith('פד בשל בשל') or line.startswith('פד בשל תורה'):
            new_lines.append(line.replace('פד בשל', 'פג בשל', 1))
            i += 1
        elif line.startswith('פה בהדיא קתני'):
            new_lines.append(line.replace('פה בהדיא', 'פד בהדיא', 1))
            i += 1
        else:
            new_lines.append(line)
            i += 1

    print(f"New line count after merging Klal 74 and shifting offset: {len(new_lines)}")

    with open('full_text_cleaned_goal.txt', 'w', encoding='utf-8') as f:
        for l in new_lines:
            f.write(l + '\n\n')

    print("Successfully updated full_text_cleaned_goal.txt!")

if __name__ == '__main__':
    fix_stitching()
