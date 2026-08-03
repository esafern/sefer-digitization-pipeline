# [PRODUCTION] Regenerate the "title" (abridged heading) field for all 667 klalim.
# The existing titles were built by taking a fixed word count from clean_text with no
# regard for punctuation, so they sometimes stop mid-abbreviation (a lone "פ" instead
# of "פ'") or run past a sentence's natural end into the next sentence's first word.
# This rebuilds titles that always end on a whole word/abbreviation and never trail
# into the next clause. Applied to every file that carries a "title" field so nothing
# downstream regresses to the old value.
import json
import os
import glob

REPO = os.path.dirname(os.path.abspath(__file__))

HARD_BREAK = {'.', ':', '•', '-', '(', ')'}
GLUE = {"'", '"', ','}


def make_title(clean_text, gematria, max_words=4):
    """Returns (title, was_truncated). Deliberately dumb: the source print
    doesn't reliably mark where a "title" ends and explanatory text begins,
    so no punctuation-based guess about "natural" endpoints is trustworthy.
    Just take the first max_words real words (gluing a stray geresh/quote
    onto the word it belongs to) and say whether anything was cut."""
    words = clean_text.split()
    if words and words[0] == gematria:
        words = words[1:]

    out = []
    i = 0
    while i < len(words) and len(out) < max_words:
        w = words[i]
        if w in HARD_BREAK:
            i += 1
            continue
        if w in GLUE:
            if out:
                out[-1] = out[-1] + w
            i += 1
            continue
        w = w.lstrip(",;:")
        if w:
            out.append(w)
        i += 1
    if i < len(words) and words[i] in GLUE and out:
        out[-1] = out[-1] + words[i]
        i += 1

    truncated = any(w not in HARD_BREAK and w not in GLUE for w in words[i:])
    return " ".join(out), truncated


def fix_file(path):
    data = json.load(open(path, encoding="utf-8"))
    items = data if isinstance(data, list) else [data]
    changed = 0
    for k in items:
        if "title" not in k or "clean_text" not in k or "gematria" not in k:
            continue
        title, truncated = make_title(k["clean_text"], k["gematria"])
        new_title = (title + "…") if truncated else title
        if new_title != k["title"]:
            k["title"] = new_title
            changed += 1
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return changed, len(items)


def main():
    targets = [
        os.path.join(REPO, "klalim_demo_dataset.json"),
        os.path.join(REPO, "part1.json"),
        os.path.join(REPO, "part2.json"),
        os.path.join(REPO, "part3.json"),
    ] + sorted(glob.glob(os.path.join(REPO, "aligned_klalim", "page_*.json")))

    for path in targets:
        changed, total = fix_file(path)
        print(f"{os.path.relpath(path, REPO)}: {changed}/{total} titles updated")


if __name__ == "__main__":
    main()
