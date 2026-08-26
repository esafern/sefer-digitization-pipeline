#!/usr/bin/env python3
# [STANDALONE] Look a word list up in Sefaria's DICTIONARIES (Jastrow, Klein,
# BDB) via the public `/api/words/` endpoint - no key, no auth.
#
# WHY THIS IS A DIFFERENT SIGNAL FROM sefaria_reference_corpus/word_freq.json.
# That cache counts word occurrences in 166 BOOKS; this asks a LEXICOGRAPHER
# whether a form is a word at all. The two fail differently, which is the whole
# point (Directive #1, Lesson 9): a rare-but-real Rabbinic word can be absent
# from 6.18M words of running text and still have a Jastrow entry, and a form
# that is merely a common OCR corruption has neither. Jastrow in particular is
# THE dictionary of Talmudic Aramaic, which is this text's own register.
#
# WHAT IT CANNOT DO, stated plainly because it governs how to read the output:
# the endpoint matches DICTIONARY HEADWORDS, not inflected or prefixed forms.
# Measured while building this: `חידוש` resolves and `חידושיו` does not;
# `קאמר` resolves and `דקאמרא` does not. So **"no entry" is NOT evidence that a
# word is corrupt** - most real words in running text are inflected. Prefix
# stripping (below) recovers some of it, never all.
#
# The signal that IS sharp is COMPARATIVE: for a suspected OCR error and its
# proposed correction, does the correction resolve where the stored form does
# not? Both share the same inflection, so the inflection cancels out. Measured
# on 15 hand-verified pairs from 2026-08-26: 13 gave exactly that answer, 1 gave
# no signal, and 1 (`דאיך` vs `דאי`) reported BOTH as dictionary words - which
# was correct, and confirmed that `דאיך` = ד+איך is legitimate rather than an
# error. All 8 forms rejected by hand that day were independently confirmed
# legitimate here (`אוף`, `רבוותא`, `איך`, `בריתא`, `אמוראי` all have entries).
#
# Results are cached to disk ONE LINE AT A TIME (the standing incremental-flush
# rule) so a 429, a timeout or a Ctrl-C never costs more than the request in
# flight, and a re-run resumes rather than re-asking.
#
# Usage:
#   python3 tools/lookup_sefaria_dictionaries.py --words FILE      # one word per line
#   python3 tools/lookup_sefaria_dictionaries.py --report          # summarize the cache
import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pipeline"))

import corpus_io as cio  # noqa: E402

CACHE_PATH = cio.repo_path("sefaria_reference_corpus", "dictionary_lookups.jsonl")
API = "https://www.sefaria.org/api/words/"
# The one-letter particles that attach to the front of a Hebrew/Aramaic word.
# Stripping these recovers a headword often enough to be worth two attempts;
# it is a mitigation for the headword-only limitation above, not a fix.
PREFIXES = "דוהבכלמש"
REQUEST_PAUSE = 0.34   # be a polite guest on a free public API
TIMEOUT = 20


def variants(word):
    """The surface form, then it with one and two leading particles removed."""
    out = [word]
    for n in (1, 2):
        if len(word) > n + 1 and all(c in PREFIXES for c in word[:n]):
            out.append(word[n:])
    return out


def load_cache(path=CACHE_PATH):
    cache = {}
    if not os.path.exists(path):
        return cache
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue          # a torn last line from an interrupted run
            cache[r["form"]] = r
    return cache


def query(form):
    """(n_entries, [headwords], [lexicons]) or None when the request failed."""
    url = API + urllib.parse.quote(form)
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as resp:
            data = json.load(resp)
    except Exception:
        return None
    return (len(data),
            sorted({e.get("headword", "") for e in data if e.get("headword")}),
            sorted({e.get("parent_lexicon", "") for e in data if e.get("parent_lexicon")}))


def lookup_all(words, path=CACHE_PATH, pause=REQUEST_PAUSE, verbose=True):
    cache = load_cache(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    forms = []
    for w in words:
        for v in variants(w):
            if v not in cache and v not in forms:
                forms.append(v)
    if verbose:
        print(f"{len(words)} word(s); {len(forms)} distinct form(s) still to fetch "
              f"({len(cache)} already cached)")
    with open(path, "a", encoding="utf-8") as f:
        for i, form in enumerate(forms, 1):
            res = query(form)
            if res is None:
                if verbose:
                    print(f"  [{i}/{len(forms)}] {form}: REQUEST FAILED - not cached, "
                          f"re-run to retry")
                time.sleep(pause * 3)
                continue
            n, heads, lexicons = res
            rec = {"form": form, "entries": n, "headwords": heads, "lexicons": lexicons}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()             # per-item, deliberately: see the header
            cache[form] = rec
            if verbose and i % 50 == 0:
                print(f"  [{i}/{len(forms)}] cached")
            time.sleep(pause)
    return cache


def resolves(word, cache):
    """(True, form, headwords) if the word or a prefix-stripped variant is a
    dictionary headword."""
    for v in variants(word):
        r = cache.get(v)
        if r and r["entries"] > 0:
            return True, v, r["headwords"]
    return False, None, []


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--words", help="file with one word per line")
    ap.add_argument("--report", action="store_true", help="summarize the cache and exit")
    ap.add_argument("--pause", type=float, default=REQUEST_PAUSE)
    args = ap.parse_args()

    if args.report or not args.words:
        cache = load_cache()
        hit = sum(1 for r in cache.values() if r["entries"] > 0)
        print(f"cache: {len(cache)} form(s), {hit} with a dictionary entry, "
              f"{len(cache) - hit} without")
        return
    with open(args.words, encoding="utf-8") as f:
        words = [w.strip() for w in f if w.strip()]
    cache = lookup_all(words, pause=args.pause)
    res = [(w,) + resolves(w, cache)[1:] for w in words]
    found = [r for r in res if r[1]]
    print(f"\n{len(found)}/{len(words)} resolve to a dictionary headword "
          f"(directly or after stripping a prefix)")
    print(f"{len(words) - len(found)} do not - which is NOT proof they are corrupt; "
          f"see this file's header on inflected forms.")


if __name__ == "__main__":
    main()
