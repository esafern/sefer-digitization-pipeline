# [PRODUCTION] Second-pass semantic sanity check over everything already flagged
# by the vision checks (verify_titles_vision.py's low-agreement titles,
# verify_corrections_vision.py's UNCERTAIN/replace-with-doubt candidates) - see
# verify_semantic_sanity.py for why this exists: vision reads pixels, this reads
# meaning, and the two catch different failure modes independently.
import json
import os
import sys

from google import genai

from verify_semantic_sanity import init_cache, adjudicate

REPO = os.path.dirname(os.path.abspath(__file__))
TITLE_VERIFICATION_PATH = os.path.join(REPO, "title_verification_part1.json")
PART1_PATH = os.path.join(REPO, "part1.json")
AGREEMENT_THRESHOLD = 0.7


def load_title_flags():
    if not os.path.exists(TITLE_VERIFICATION_PATH):
        return []
    results = json.load(open(TITLE_VERIFICATION_PATH, encoding="utf-8"))
    return [r for r in results if r.get("agreement_ratio") is not None and r["agreement_ratio"] < AGREEMENT_THRESHOLD]


def load_corrections_flags(path):
    """Candidates where vision didn't confidently confirm the current text:
    UNCERTAIN, or selected A (docai reading may be right instead)."""
    results = json.load(open(path, encoding="utf-8"))
    return [r for r in results if r.get("vision_selected") in ("UNCERTAIN", "A")]


def main():
    corrections_path = sys.argv[1] if len(sys.argv) > 1 else None
    out_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(REPO, "semantic_sanity_results.json")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("GEMINI_API_KEY not set")
    init_cache()
    client = genai.Client(api_key=api_key)

    klalim = {k["klal_id"]: k for k in json.load(open(PART1_PATH, encoding="utf-8"))}
    results = []

    title_flags = load_title_flags()
    print(f"Title-verification low-agreement items to check: {len(title_flags)}")
    for r in title_flags:
        kid = r["klal_id"]
        context = klalim.get(kid, {}).get("clean_text", "")[:300]
        print(f"Klal {kid} (title): {r['judged_title']!r} vs {r['vision_title_reading']!r}")
        # candidate_a is always the CURRENT value, candidate_b the alternative -
        # kept consistent with the corrections branch below so "B favored" means
        # "potential fix" uniformly, regardless of source.
        decision = adjudicate(client, r["judged_title"], r["vision_title_reading"] or "", context)
        results.append({
            "source": "title_verification",
            "klal_id": kid,
            "candidate_a_label": "current_title",
            "candidate_a": r["judged_title"],
            "candidate_b_label": "vision_title_reading",
            "candidate_b": r["vision_title_reading"],
            **decision,
        })

    if corrections_path:
        corr_flags = load_corrections_flags(corrections_path)
        print(f"\nCorrections UNCERTAIN/A items to check: {len(corr_flags)}")
        for r in corr_flags:
            kid = r["klal_id"]
            context = klalim.get(kid, {}).get("clean_text", "")[:300]
            docai_reading = r.get("original_word") or ""
            current_text = r.get("corrected_word") or ""
            print(f"Klal {kid} (correction): current={current_text!r} vs docai={docai_reading!r}")
            # candidate_a = current value (same convention as the title branch above)
            decision = adjudicate(client, current_text, docai_reading, context)
            results.append({
                "source": "corrections",
                "klal_id": kid,
                "candidate_a_label": "current_text",
                "candidate_a": current_text,
                "candidate_b_label": "docai_reading",
                "candidate_b": docai_reading,
                **decision,
            })

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # candidate_a is always the current value; "B" favored means the alternative
    # (docai reading / vision title reading) is the semantically sensible one -
    # i.e. a potential fix to the CURRENT data, regardless of source.
    flips = [r for r in results if r.get("sensible_candidate") == "B"]
    print(f"\nWrote {len(results)} results to {out_path}")
    print(f"{len(flips)} cases where the semantic pass favors the alternative over current text (potential fix):")
    for r in flips:
        print(" ", r["klal_id"], r["source"], "current:", r["candidate_a"], "-> alternative:", r["candidate_b"],
              "(conf", r.get("confidence"), ")")


if __name__ == "__main__":
    main()
