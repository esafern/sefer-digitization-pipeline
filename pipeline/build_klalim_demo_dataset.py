# [PRODUCTION] klalim_demo_dataset.json is a BUILD ARTIFACT, not a source file -
# it is exactly part1.json + part2.json + part3.json concatenated (verified
# 2026-08-05: zero field-level diffs between the two representations). Never
# hand-edit klalim_demo_dataset.json directly; edit the relevant part*.json
# and regenerate this from it. See PROJECT-STATUS.md for why this split
# exists: before this script, both files were maintained by hand in parallel
# on every correction, which is exactly the kind of two-copies-of-the-truth
# setup that goes silently out of sync.
import json
import os

# Moved one level deeper (pipeline/ or tools/) 2026-08-16 - REPO now goes up
# two levels, not one, to keep resolving to the actual repo root where
# part1.json/docai_word_boxes/etc. live.
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS = ["part1.json", "part2.json", "part3.json"]
OUT_PATH = os.path.join(REPO, "klalim_demo_dataset.json")


def load_klalim(path):
    d = json.load(open(path, encoding="utf-8"))
    return d["klalim"] if isinstance(d, dict) and "klalim" in d else d


def main():
    by_part = {part: load_klalim(os.path.join(REPO, part)) for part in PARTS}
    combined = [k for part in PARTS for k in by_part[part]]
    combined.sort(key=lambda k: k["klal_id"])

    seen = set()
    dupes = sorted({k["klal_id"] for k in combined if k["klal_id"] in seen or seen.add(k["klal_id"])})
    if dupes:
        raise SystemExit(f"Duplicate klal_id across parts: {dupes}")

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)

    counts = ", ".join(f"{part.removesuffix('.json')}={len(by_part[part])}" for part in PARTS)
    print(f"Wrote {OUT_PATH}: {len(combined)} klalim ({counts})")


if __name__ == "__main__":
    main()
