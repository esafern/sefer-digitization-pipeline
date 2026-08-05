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

REPO = os.path.dirname(os.path.abspath(__file__))
PARTS = ["part1.json", "part2.json", "part3.json"]
OUT_PATH = os.path.join(REPO, "klalim_demo_dataset.json")


def load_klalim(path):
    d = json.load(open(path, encoding="utf-8"))
    return d["klalim"] if isinstance(d, dict) and "klalim" in d else d


def main():
    combined = []
    for part in PARTS:
        combined.extend(load_klalim(os.path.join(REPO, part)))

    combined.sort(key=lambda k: k["klal_id"])

    seen = set()
    dupes = [k["klal_id"] for k in combined if k["klal_id"] in seen or seen.add(k["klal_id"])]
    if dupes:
        raise SystemExit(f"Duplicate klal_id across parts: {dupes}")

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)

    print(f"Wrote {OUT_PATH}: {len(combined)} klalim (part1={len(load_klalim(os.path.join(REPO, 'part1.json')))}, "
          f"part2={len(load_klalim(os.path.join(REPO, 'part2.json')))}, "
          f"part3={len(load_klalim(os.path.join(REPO, 'part3.json')))})")


if __name__ == "__main__":
    main()
