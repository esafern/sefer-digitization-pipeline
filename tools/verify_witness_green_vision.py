#!/usr/bin/env python3
# [PRODUCTION] Vision-adjudicate the words that render GREEN in the dashboard on
# a `witness_choice` ruling - item 0EA.
#
# WHY THIS IS A DIFFERENT QUESTION FROM tools/verify_witness_vision.py. That
# script asks the ink to choose between two OCR ENGINES (DocAI vs Tesseract), to
# triage the witness queue before a human rules on it. This one runs AFTER the
# human has ruled, and asks the only question that matters once they have: THE
# CORPUS READS X AT THIS WORD - IS THAT WHAT IS PRINTED?
#
# It exists because a `witness_choice` colours a word green - settled, a human
# ruled here - and no script in this repo can promote one into part1.json:
# apply_reviewer_decisions.py promotes candidate_choice, manual_correction and
# title_correction, and a grep across pipeline/ and tools/ finds no writer for
# witness_choice. So the green is a claim nothing has ever checked.
#
# ADDRESSING. A witness ruling's `word_index` in the ledger is a
# docai_token_index (review_server.py's merge_word_ids docstring), so it is
# joined to reconstruction_witness_queue.json on (klal_id, docai_token_index) to
# get both the bbox to crop and the `word_index` that indexes the klal's words -
# the same mapping review_counts.word_states() uses to colour the word. Rows the
# queue cannot map (word_index null) are reported, not guessed at.
#
# TRIAGE ONLY, like every vision pass here: it records nothing into the ledger
# and writes no corpus text. Output is a report for a human.
#
# Usage: python3 tools/verify_witness_green_vision.py [--limit N] [--json PATH]
import argparse
import hashlib
import json
import os
import sys

import fitz  # PyMuPDF

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pipeline"))
import corpus_io as cio            # noqa: E402
import review_data as rdata        # noqa: E402
import review_decisions as rd      # noqa: E402
import review_server as rsrv       # noqa: E402 - api_word_states, in process
import vision_adjudication_common as vac  # noqa: E402
import verify_witness_vision as vwv       # noqa: E402 - build_context/dtoks, one copy

REPO = cio.REPO
PDF_PATH = os.path.join(REPO, "berlin_square_corrected.pdf")
CACHE_DB = os.path.join(REPO, "witness_vision_cache.db")
CACHE_TABLE = "witness_green_cache"
REPORT_PATH = os.path.join(REPO, "WITNESS-GREEN-VISION.md")

# ONE QUESTION, not two options. Where the corpus and the ruling agree - 21 of
# the 28 - a two-option prompt would be asking the model to choose between a
# string and itself, which verify_corrections_vision.py finding 7 records as the
# shape that always resolves to UNCERTAIN. Asking what is PRINTED answers both
# cases with the same prompt, so both go through one cache key and one wording.
PROMPT_TEMPLATE = """
You are an expert Talmudic and Rabbinic textual verification engine analyzing a Hebrew manuscript raster crop.

Surrounding raw OCR context (unverified, may include misreads on either side): "{context}"

The digitized corpus currently reads {corpus_desc} at the target position.
A human reviewer separately ruled, in the witness panel, that this position reads {chosen_desc}.

Report what the INK actually shows.

CONSTRAINTS:
1. Perform Rabbinic acronym and semantic analysis using the surrounding context.
2. Recognize standard Rabbinic acronyms and abbreviations.
3. Do NOT mistake Rabbinic acronyms for the literal spelled-out Hebrew letter name when context indicates an abbreviation.
4. Treat a geresh/gershayim (׳ ״) and a typewriter apostrophe/quote (' ") as THE SAME MARK; do not report a difference that is only which of those glyphs was used.
5. Judge only the target position, not the surrounding context words.
6. Output "UNCERTAIN" only if the crop is illegible or too ambiguous to read at all.

Respond ONLY with JSON using this structure:
{{
  "selected_option": "CORPUS" or "RULING" or "NEITHER" or "UNCERTAIN",
  "transcription_found": "exact text visible in image",
  "confidence": 0.0 to 1.0,
  "reasoning": "contextual Rabbinic paleographic explanation"
}}
"""
PROMPT_HASH = hashlib.sha256(PROMPT_TEMPLATE.encode("utf-8")).hexdigest()[:16]


def init_cache():
    vac.init_cache_table(CACHE_DB, CACHE_TABLE, PROMPT_HASH, has_model_column=False)


def get_cached(crop_bytes, word_a, word_b, context):
    return vac.get_cached_decision(CACHE_DB, CACHE_TABLE, PROMPT_HASH, crop_bytes, word_a, word_b, context)


def cache_put(crop_bytes, word_a, word_b, context, decision_text):
    vac.put_cached_decision(CACHE_DB, CACHE_TABLE, PROMPT_HASH, crop_bytes, word_a, word_b, context,
                            decision_text, has_model_column=False)


def green_word_indices():
    """{klal_id: {word_index}} for every Part 1 word that renders GREEN.

    Calls review_server.api_word_states() IN PROCESS rather than reimplementing
    "what is green". That endpoint's `decided` bucket comes from the same
    review_counts.word_states() pass the dashboard colours from, and it already
    maps a witness ruling's docai_token_index onto the klal's words - which is
    the whole difficulty here. A second definition of green in this file is
    Lesson 13's shape, and the tri-state is already encoded twice.
    """
    buckets = rsrv.api_word_states(part_num=1)
    out = {}
    for e in buckets["decided"]:
        out.setdefault(e["klal_id"], set()).add(e["word_index"])
    return out


def collect():
    """The witness rulings that are currently colouring a word green."""
    corpus = {int(kid): k[cio.TEXT_FIELD].split()
              for kid, k in cio.load_part1_by_id().items()}
    queue = {(w["klal_id"], w["docai_token_index"]): w for w in rdata.load_witness_queue()}
    green = green_word_indices()
    rows = []
    for (kid, tok), dec in sorted(rd.all_current_live("witness_choice").items()):
        q = queue.get((kid, tok))
        chosen = (dec.get("chosen_text") or "").strip()
        if q is None or q.get("word_index") is None:
            rows.append({"klal_id": kid, "docai_token_index": tok, "word_index": None,
                         "chosen_text": chosen, "corpus_span": None, "page": q["page"] if q else None,
                         "bbox": q.get("bbox") if q else None, "status": "unmapped"})
            continue
        wi = q["word_index"]
        if wi not in green.get(kid, ()):
            continue
        words = corpus.get(kid, [])
        span = " ".join(words[wi:wi + max(1, len(chosen.split()))])
        rows.append({"klal_id": kid, "docai_token_index": tok, "word_index": wi,
                     "chosen_text": chosen, "corpus_span": span, "page": q["page"],
                     "bbox": q.get("bbox"),
                     "status": "agree" if span == chosen else "disagree"})
    return rows


def adjudicate(client, crop_bytes, corpus_span, chosen, context):
    corpus_desc = f'"{corpus_span}"' if corpus_span else "(nothing - no word is stored at this position)"
    chosen_desc = f'"{chosen}"' if chosen else "(nothing - the reviewer ruled that no text belongs here)"
    prompt = PROMPT_TEMPLATE.format(context=context, corpus_desc=corpus_desc, chosen_desc=chosen_desc)
    return vac.adjudicate_with_retry(
        client, crop_bytes, prompt,
        cache_get=lambda: get_cached(crop_bytes, corpus_span, chosen, context),
        cache_put=lambda text, model_name: cache_put(crop_bytes, corpus_span, chosen, context, text),
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--json", default=None, help="also write the raw results here")
    args = ap.parse_args()

    init_cache()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("GEMINI_API_KEY not set")
    client = vac.make_client(api_key)

    rows = collect()
    todo = [r for r in rows if r["bbox"] and r["word_index"] is not None]
    if args.limit:
        todo = todo[:args.limit]
    print(f"{len(rows)} witness rulings colour a word green; {len(todo)} have a bbox to crop")

    doc = fitz.open(PDF_PATH)
    for i, r in enumerate(todo, 1):
        context = vwv.build_context(r["page"], r["docai_token_index"])
        crop = vac.crop_pdf_bounding_box(doc, r["page"], r["bbox"], padding=0.02, dpi=300)
        print(f"[{i}/{len(todo)}] klal {r['klal_id']} w{r['word_index']} p{r['page']}: "
              f"corpus {r['corpus_span']!r} / ruling {r['chosen_text']!r}")
        text = adjudicate(client, crop, r["corpus_span"], r["chosen_text"], context)
        try:
            d = json.loads(text)
        except json.JSONDecodeError:
            try:
                d = json.loads(vac.sanitize_json(text))
            except json.JSONDecodeError:
                d = vac.parse_decision_lenient(text)
        r["vision_selected"] = (d or {}).get("selected_option")
        r["vision_transcription"] = (d or {}).get("transcription_found")
        r["vision_confidence"] = (d or {}).get("confidence")
        r["vision_reasoning"] = (d or {}).get("reasoning")
        print(f"      -> {r['vision_selected']} ({r['vision_confidence']}) {r['vision_transcription']!r}")

    if args.json:
        json.dump(rows, open(args.json, "w"), ensure_ascii=False, indent=1)
    write_report(rows)
    return rows


def write_report(rows):
    done = [r for r in rows if r.get("vision_selected")]
    lines = ["# Witness rulings that colour a word green, adjudicated against the ink",
             "",
             "Generated by `tools/verify_witness_green_vision.py` (item 0EA). TRIAGE ONLY -",
             "nothing here is recorded as a decision or written into the corpus.",
             "",
             f"- witness rulings currently colouring a word green: {len(rows)}",
             f"- adjudicated: {len(done)}",
             f"- the ink agrees with the CORPUS: {sum(1 for r in done if r['vision_selected'] == 'CORPUS')}",
             f"- the ink agrees with the RULING instead: {sum(1 for r in done if r['vision_selected'] == 'RULING')}",
             f"- NEITHER: {sum(1 for r in done if r['vision_selected'] == 'NEITHER')}",
             f"- UNCERTAIN: {sum(1 for r in done if r['vision_selected'] == 'UNCERTAIN')}",
             ""]
    for r in sorted(rows, key=lambda x: (x["klal_id"], x["word_index"] if x["word_index"] is not None else -1)):
        if r["word_index"] is None:
            lines.append(f"- klal {r['klal_id']}, docai token {r['docai_token_index']}: "
                         f"UNMAPPED - the witness queue has no word_index, so this ruling "
                         f"cannot be placed on a word at all. Chose `{r['chosen_text']}`.")
            continue
        lines.append(f"- http://127.0.0.1:8420/klal/{r['klal_id']}/word/{r['word_index']} — "
                     f"corpus `{r['corpus_span']}`, ruling `{r['chosen_text']}` "
                     f"({r['status']}) → **{r.get('vision_selected')}** "
                     f"`{r.get('vision_transcription')}` conf {r.get('vision_confidence')}")
        if r.get("vision_reasoning"):
            lines.append(f"    - {r['vision_reasoning']}")
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
