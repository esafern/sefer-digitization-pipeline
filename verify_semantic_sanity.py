# [PRODUCTION] Text-only semantic sanity pass, complementary to the vision checks
# in verify_titles_vision.py / verify_corrections_vision.py.
#
# Pixel-level image reading can be fooled by visually near-identical Hebrew
# letter pairs (ד/ר, ה/ח, ם/ס, ו/ז) - the single most common OCR failure mode
# in this corpus (see corrections sample: דנראח/דנראה, ארם/אדם, etc.). When two
# candidate readings differ by exactly this kind of confusion, "what does the
# crop look like" isn't the only useful question - "which candidate is a real,
# coherent Rabbinic-Hebrew phrase and which is gibberish" is an independent
# signal that needs no image at all, just linguistic judgment. This asks that
# question directly, in isolation, so it isn't anchored by having just read
# (and possibly misread) the same crop.
import json
import os
import sys
import time
import hashlib
import sqlite3
import re

from google import genai
from google.genai import types

REPO = os.path.dirname(os.path.abspath(__file__))
CACHE_DB = os.path.join(REPO, "adjudication_cache.db")


def init_cache():
    conn = sqlite3.connect(CACHE_DB)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS semantic_cache (query_hash TEXT PRIMARY KEY, decision_json TEXT)"
    )
    conn.commit()
    conn.close()


def get_cached(query_hash):
    conn = sqlite3.connect(CACHE_DB, timeout=10.0)
    row = conn.execute("SELECT decision_json FROM semantic_cache WHERE query_hash = ?", (query_hash,)).fetchone()
    conn.close()
    return row[0] if row else None


def cache_decision(query_hash, decision_json):
    conn = sqlite3.connect(CACHE_DB, timeout=10.0)
    conn.execute(
        "INSERT OR REPLACE INTO semantic_cache (query_hash, decision_json) VALUES (?, ?)",
        (query_hash, decision_json),
    )
    conn.commit()
    conn.close()


def sanitize_json(text):
    return re.sub(r'\\(?!["\\/bfnrtu])', '', text)


def extract_fields_lenient(text):
    sel_m = re.search(r'"sensible_candidate"\s*:\s*"(.*?)"', text)
    conf_m = re.search(r'"confidence"\s*:\s*([0-9.]+)', text)
    reasoning_m = re.search(r'"reasoning"\s*:\s*"(.*)"\s*\}\s*$', text, re.S)
    return {
        "sensible_candidate": sel_m.group(1) if sel_m else None,
        "confidence": float(conf_m.group(1)) if conf_m else None,
        "reasoning": reasoning_m.group(1) if reasoning_m else "(unparsable reasoning field)",
    }


def adjudicate(client, candidate_a, candidate_b, context):
    key = hashlib.sha256(f"{candidate_a}|{candidate_b}|{context}".encode("utf-8")).hexdigest()
    cached = get_cached(key)
    if cached:
        print("  -> cache hit")
        return json.loads(cached) if cached.strip().startswith("{") else extract_fields_lenient(cached)

    prompt = f"""
You are a Rabbinic-Hebrew linguistics expert reviewing a printed halachic-
methodology digest (Yad Malachi, Klalei HaGemara, 18th century). Two candidate
readings exist for the same short span of text:

Candidate A: "{candidate_a}"
Candidate B: "{candidate_b}"

Full surrounding context: "{context}"

Judge PURELY on Rabbinic-Hebrew grammar, semantics, and familiarity with
Talmudic idiom - NOT on any image or OCR confidence. Which candidate is a
coherent, meaningful phrase (possibly a well-known Talmudic/halachic
expression), and which looks like OCR noise producing a non-word or
non-sequitur? The single most common failure mode in this corpus is a
visually-similar-letter substitution (ד/ר, ה/ח, ם/ס, ו/ז) that produces
something that doesn't actually mean anything - actively check for that
pattern before concluding both are equally plausible.

Respond ONLY with JSON:
{{
  "sensible_candidate": "A" or "B" or "BOTH" or "NEITHER",
  "confidence": 0.0 to 1.0,
  "reasoning": "brief linguistic explanation"
}}
"""
    models_to_try = ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-2.5-flash"]
    max_retries = 3
    last_err = None
    for model_name in models_to_try:
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[prompt],
                    config=types.GenerateContentConfig(response_mime_type="application/json"),
                )
                print(f"  -> live call to {model_name} ok")
                cache_decision(key, response.text)
                try:
                    return json.loads(response.text)
                except json.JSONDecodeError:
                    try:
                        return json.loads(sanitize_json(response.text))
                    except json.JSONDecodeError:
                        return extract_fields_lenient(response.text)
            except Exception as e:
                last_err = e
                print(f"  -> {model_name} attempt {attempt} failed: {e}")
                if "503" in str(e) or "429" in str(e):
                    time.sleep((2 ** attempt) * 2)
                else:
                    break
    raise RuntimeError(f"All models failed: {last_err}")


def main():
    # ad hoc single-pair mode: python3 verify_semantic_sanity.py "<A>" "<B>" "<context>"
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("GEMINI_API_KEY not set")
    init_cache()
    client = genai.Client(api_key=api_key)

    a, b, context = sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else ""
    decision = adjudicate(client, a, b, context)
    print(json.dumps(decision, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
