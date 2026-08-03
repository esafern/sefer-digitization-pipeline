# [PRODUCTION] Apply human/LLM-judged titles (JUDGED_TITLES below) for Part 1
# klalim (1-222), replacing the algorithmic title generator - the print doesn't
# reliably punctuate where a title ends, so this requires actual reading
# comprehension, not a word-count/punctuation heuristic.
#
# Also marks the title/explanation boundary in clean_text with an inserted
# period ONLY where the original print has no punctuation there at all -
# wrapped in square brackets, [.], the standard critical-edition convention
# for an editorial insertion, so it is never mistaken for part of the
# original print. This does NOT attempt a full corpus-wide repunctuation of
# every sentence - see CLAUDE.md Open Items for that larger, separate task.
import json
import os
import glob

REPO = os.path.dirname(os.path.abspath(__file__))
JUDGED_TITLES_PATH = os.path.join(REPO, "judged_titles_part1.json")

HARD_BREAK = {'.', ':', '•', '-', '(', ')'}
NO_TEXT_TITLE = "(no text available)"


def find_boundary(clean_text, gematria, title):
    """Return the index (into clean_text.split()) of the first word AFTER
    the judged title, or None if the title's content doesn't match the start
    of clean_text (a sanity check against stale/mismatched data). Compares
    ignoring incidental whitespace, since a geresh like "ר'" is sometimes one
    token and sometimes split into "ר" + "'" by earlier OCR/chunking passes."""
    words = clean_text.split()
    start = 1 if (words and words[0] == gematria) else 0
    target = title.replace(" ", "")

    consumed = ""
    i = start
    while i < len(words) and len(consumed) < len(target):
        if words[i] == ",":
            i += 1
            continue
        consumed += words[i]
        i += 1
    if consumed != target:
        return None
    return i


def apply_to_file(path, judged_titles):
    data = json.load(open(path, encoding="utf-8"))
    items = data if isinstance(data, list) else [data]
    changed = 0
    mismatches = []
    for k in items:
        kid = str(k.get("klal_id"))
        if kid not in judged_titles:
            continue
        title = judged_titles[kid]
        if title is None:
            if k.get("title") != NO_TEXT_TITLE:
                k["title"] = NO_TEXT_TITLE
                changed += 1
            continue

        boundary = find_boundary(k["clean_text"], k["gematria"], title)
        if boundary is None:
            mismatches.append(kid)
            continue

        words = k["clean_text"].split()
        needs_mark = not (boundary < len(words) and (words[boundary] in HARD_BREAK or words[boundary] == "[.]"))
        if needs_mark:
            new_text = " ".join(words[:boundary] + ["[.]"] + words[boundary:])
        else:
            new_text = k["clean_text"]

        if k.get("title") != title or k["clean_text"] != new_text:
            k["title"] = title
            k["clean_text"] = new_text
            changed += 1

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return changed, len(items), mismatches


def main():
    judged_titles = json.load(open(JUDGED_TITLES_PATH, encoding="utf-8"))

    targets = [
        os.path.join(REPO, "klalim_demo_dataset.json"),
        os.path.join(REPO, "part1.json"),
        os.path.join(REPO, "part2.json"),
        os.path.join(REPO, "part3.json"),
    ] + sorted(glob.glob(os.path.join(REPO, "aligned_klalim", "page_*.json")))

    for path in targets:
        changed, total, mismatches = apply_to_file(path, judged_titles)
        rel = os.path.relpath(path, REPO)
        print(f"{rel}: {changed}/{total} updated" + (f" | MISMATCHES: {mismatches}" if mismatches else ""))


if __name__ == "__main__":
    main()
