#!/usr/bin/env python3
"""Build (or load) a Part 1 word-frequency table keyed to the current
content of part1.json.

Output: part1_word_freq.json  (sibling of part1.json in the repo root)

Schema:
  {
    "meta": {
      "part1_sha": "<git hash-object SHA of part1.json at build time>",
      "total_words": <int>,
      "unique_forms": <int>,
      "hapax_count": <int>   # forms with count == 1
    },
    "freq": {
      "<letters-only normalized form>": <count>,
      ...
    }
  }

Staleness is detected by comparing the stored part1_sha against the
current `git hash-object part1.json` — i.e. the file's content hash,
not the repo HEAD. That means the table is stale iff part1.json itself
changed, regardless of what else was committed.

Usage
-----
  # As a script — rebuild if stale, print summary:
  python3 tools/build_part1_freq.py

  # Force rebuild even if current:
  python3 tools/build_part1_freq.py --force

  # As a library — returns the freq dict, rebuilding only if stale:
  from tools.build_part1_freq import load_or_build
  freq = load_or_build()          # {normalized_form: count}
  hapax = {w for w, n in freq.items() if n == 1}
"""
import argparse
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pipeline"))
import corpus_io as cio  # noqa: E402

OUT_PATH = os.path.join(REPO, "part1_word_freq.json")


def _part1_sha():
    """Content SHA of part1.json (git hash-object, not repo HEAD)."""
    try:
        result = subprocess.run(
            ["git", "hash-object", cio.PART1_PATH],
            capture_output=True, text=True, check=True, cwd=REPO,
        )
        return result.stdout.strip()
    except Exception:
        return None


def _is_current():
    if not os.path.exists(OUT_PATH):
        return False
    try:
        with open(OUT_PATH, encoding="utf-8") as f:
            stored = json.load(f)
        return stored.get("meta", {}).get("part1_sha") == _part1_sha()
    except Exception:
        return False


def _build():
    from collections import Counter
    part1 = cio.load_part1()
    freq = Counter()
    for k in part1:
        for w in k["clean_text"].split():
            norm = cio.hebrew_letters_only(w)
            if norm:
                freq[norm] += 1
    sha = _part1_sha()
    hapax = sum(1 for c in freq.values() if c == 1)
    data = {
        "meta": {
            "part1_sha": sha,
            "total_words": sum(freq.values()),
            "unique_forms": len(freq),
            "hapax_count": hapax,
        },
        "freq": dict(freq),
    }
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    return data


def load_or_build(force=False):
    """Return the freq dict {normalized_form: count}, rebuilding if stale."""
    if not force and _is_current():
        with open(OUT_PATH, encoding="utf-8") as f:
            return json.load(f)["freq"]
    return _build()["freq"]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--force", action="store_true", help="rebuild even if current")
    args = ap.parse_args()

    if not args.force and _is_current():
        with open(OUT_PATH, encoding="utf-8") as f:
            data = json.load(f)
        m = data["meta"]
        print(f"Current (sha {m['part1_sha'][:12]}): "
              f"{m['unique_forms']} forms, {m['total_words']} words, "
              f"{m['hapax_count']} hapax. No rebuild needed.")
        return

    data = _build()
    m = data["meta"]
    print(f"Built {OUT_PATH}: sha {(m['part1_sha'] or 'unknown')[:12]}, "
          f"{m['unique_forms']} forms, {m['total_words']} words, "
          f"{m['hapax_count']} hapax legomena.")


if __name__ == "__main__":
    main()
