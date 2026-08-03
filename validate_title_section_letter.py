# [PRODUCTION] Standing validation: every klal's `title` must start with its
# section's letter (א for כללי האלף, ב for כללי הבית, etc.) - the section
# boundary IS a first-letter grouping by the book's own acrostic structure, so
# a title that starts with a different letter is a structural red flag: either
# the title lost its distinguishing prefix (see klal 102-105, which dropped
# "בית דין"/"ב\"ד" and now start with "מ"), or something else is wrong. Cheap,
# mechanical, no LLM needed - run this any time titles change, the same way
# lexicon.txt validation gets run after a text cleanup pass (see CLAUDE.md
# Conventions: "zero flagged items" is the bar).
import json
import os
import glob

REPO = os.path.dirname(os.path.abspath(__file__))
NO_TEXT_TITLE = "(no text available)"

SECTION_LETTER = {
    "כללי האלף": "א",
    "כללי הבית": "ב",
    "כללי הגימל": "ג",
    "כללי הדלת": "ד",
    "כללי ההא": "ה",
}


def check_file(path):
    data = json.load(open(path, encoding="utf-8"))
    items = data if isinstance(data, list) else [data]
    violations = []
    for k in items:
        title = k.get("title", "")
        if title == NO_TEXT_TITLE or not title.strip():
            continue
        expected = SECTION_LETTER.get(k.get("section"))
        if not expected:
            continue
        if title.strip()[0] != expected:
            violations.append({
                "klal_id": k.get("klal_id"),
                "section": k.get("section"),
                "expected_letter": expected,
                "actual_letter": title.strip()[0],
                "title": title,
            })
    return violations


def main():
    targets = [
        os.path.join(REPO, "klalim_demo_dataset.json"),
        os.path.join(REPO, "part1.json"),
        os.path.join(REPO, "part2.json"),
        os.path.join(REPO, "part3.json"),
    ] + sorted(glob.glob(os.path.join(REPO, "aligned_klalim", "page_*.json")))

    total = 0
    for path in targets:
        if not os.path.exists(path):
            continue
        violations = check_file(path)
        if violations:
            total += len(violations)
            rel = os.path.relpath(path, REPO)
            print(f"{rel}: {len(violations)} violation(s)")
            for v in violations:
                print(f"  klal {v['klal_id']}: expected {v['expected_letter']!r}, "
                      f"got {v['actual_letter']!r} -> {v['title']!r}")

    print(f"\nTotal violations across all files: {total}")
    if total == 0:
        print("Clean - 0 flagged items.")


if __name__ == "__main__":
    main()
