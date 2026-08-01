import re

def fix_dups():
    with open('full_text_cleaned_goal.txt', 'r', encoding='utf-8') as f:
        content = f.read()

    lines = [l.strip() for l in content.split('\n') if l.strip()]

    print(f"Current lines count: {len(lines)}")

    # Remove the 5 bogus single-word lines:
    # 'קיג בורכא'
    # 'קיד בדותא'
    # 'קטו במחלוקת'
    # 'קטז בתר'
    # 'קיז בו'

    new_lines = []
    for l in lines:
        if l in ['קיג בורכא', 'קיד בדותא', 'קטו במחלוקת', 'קטז בתר', 'קיז בו']:
            print(f"Removing bogus line: '{l}'")
            continue
        new_lines.append(l)

    # Now update headers for items after 112:
    # 'קיב בורכא' -> 'קיב בורכא היא' (if needed)
    # 'קיח בורכא היא' -> 'קיב בורכא היא'
    # 'קיט בדותא היא' -> 'קיג בדותא היא'
    # 'קכ\' במחלוקת' -> 'קיד במחלוקת'
    # 'קכא בתר דבעיא' -> 'קטו בתר דבעיא'
    # 'קכב בו ביום' -> 'קטז בו ביום'
    # 'קכג בני נח' -> 'קיז בני נח'
    # 'קכד מכין ועונשין' -> 'קיח מכין ועונשין'
    # 'קכה בהא זכינהו' -> 'קיט בהא זכינהו'
    # 'קכו בית הלל' -> 'קכ בית הלל'
    # 'קכז בפרוע' -> 'קכא בפרוע'

    final_lines = []
    for l in new_lines:
        if l.startswith('קיח בורכא היא'):
            final_lines.append(l.replace('קיח בורכא', 'קיב בורכא', 1))
        elif l.startswith('קיט בדותא היא'):
            final_lines.append(l.replace('קיט בדותא', 'קיג בדותא', 1))
        elif l.startswith("קכ' במחלוקת هي") or l.startswith("קכ' במחלוקת"):
            final_lines.append(re.sub(r"^קכ[']? במחלוקת", "קיד במחלוקת", l))
        elif l.startswith('קכא בתר דבעיא'):
            final_lines.append(l.replace('קכא בתר', 'קטו בתר', 1))
        elif l.startswith('קכב בו ביום'):
            final_lines.append(l.replace('קכב בו', 'קטז בו', 1))
        elif l.startswith('קכג בני נח'):
            final_lines.append(l.replace('קכג בני', 'קיז בני', 1))
        elif l.startswith('קכד מכין'):
            final_lines.append(l.replace('קכד מכין', 'קיח מכין', 1))
        elif l.startswith('קכה בהא זכינהו'):
            final_lines.append(l.replace('קכה בהא', 'קיט בהא', 1))
        elif l.startswith('קכו בית הלל'):
            final_lines.append(l.replace('קכו בית', 'קכ בית', 1))
        elif l.startswith('קכז בפרוע'):
            final_lines.append(l.replace('קכז בפרוע', 'קכא בפרוע', 1))
        else:
            final_lines.append(l)

    print(f"New line count: {len(final_lines)}")

    with open('full_text_cleaned_goal.txt', 'w', encoding='utf-8') as f:
        for l in final_lines:
            f.write(l + '\n\n')

    print("Updated full_text_cleaned_goal.txt successfully!")

if __name__ == '__main__':
    fix_dups()
