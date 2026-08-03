# [PRODUCTION] Combine the vision-verified Part-1 correction candidates into the
# per-klal dataset review.html consumes: one entry per flagged word, with a
# human-readable flag classifying what the vision check implies.
import json
import os

REPO = os.path.dirname(os.path.abspath(__file__))
IN_PATH = os.path.join(REPO, "corrections_verified_part1.json")
OUT_PATH = os.path.join(REPO, "corrections_part1.json")


def classify(c):
    op = c["opcode"]
    sel = c.get("vision_selected")
    conf = c.get("vision_confidence")

    if op == "replace":
        if sel == "A":
            return "current_text_may_be_wrong"
        if sel == "B":
            return "current_text_confirmed"
        if sel == "UNCERTAIN":
            return "ambiguous"
        return "error"
    if op == "delete":
        if sel == "A" and conf and conf >= 0.7:
            return "possible_omission"
        if sel == "ERROR":
            return "error"
        return "ambiguous"
    if op == "insert":
        return "unverified_insertion"
    return "unverified"


def main():
    verified = json.load(open(IN_PATH))
    by_klal = {}
    for c in verified:
        entry = {
            "word_index": c["word_index_in_final_text"],
            "opcode": c["opcode"],
            "docai_reading": c["original_word"],
            "final_text": c["corrected_word"],
            "page": c["page"],
            "bbox": c["bbox"],
            "vision_selected": c.get("vision_selected"),
            "vision_transcription": c.get("vision_transcription"),
            "confidence": c.get("vision_confidence"),
            "reasoning": c.get("vision_reasoning"),
            "flag": classify(c),
        }
        by_klal.setdefault(str(c["klal_id"]), []).append(entry)

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(by_klal, f, ensure_ascii=False, indent=2)

    flags = {}
    for entries in by_klal.values():
        for e in entries:
            flags[e["flag"]] = flags.get(e["flag"], 0) + 1
    print(f"Wrote {OUT_PATH}: {sum(len(v) for v in by_klal.values())} items across {len(by_klal)} klalim")
    print("By flag:", flags)


if __name__ == "__main__":
    main()
