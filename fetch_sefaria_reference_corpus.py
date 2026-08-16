#!/usr/bin/env python3
# [STANDALONE] Downloads Shulchan Arukh (all 4 chelekim) + Talmud Bavli (37
# tractates) Hebrew text from Sefaria's public export bucket, for use as a
# GENUINELY INDEPENDENT Rabbinic Hebrew/Aramaic reference corpus - i.e. one
# not derived from this project's own OCR of the Berlin scan, unlike
# lexicon.txt (see PROJECT-STATUS.md "`lexicon.txt` cannot catch the
# ligature corruption - it contains it"). Same halachic-code/Talmudic-
# citation register as Yad Malachi, which cites both constantly.
#
# Source: https://github.com/Sefaria/Sefaria-Export - a public GCS bucket,
# one merged Hebrew-text JSON per book, no API key/auth needed. `books.json`
# is the bucket's own index (title/language/versionTitle -> json_url); this
# script filters it down to the 41 targets rather than hardcoding URLs, so a
# future bucket reorganization breaks loudly (find_urls() exits naming the
# missing titles) rather than silently fetching nothing.
#
# Downloading a book is NOT the same as that book reaching the frequency
# table - validate_lexicon_independent.py owns the extraction, and one book
# (Shulchan Arukh, Even HaEzer) sat downloaded-and-counted here while
# contributing zero words to it until 2026-08-16. That script now warns per
# book; this one only promises bytes on disk.
#
# Output: sefaria_reference_corpus/raw/<Title>.json (41 files, ~45MB) -
# gitignored, same as this project's other scan-derived caches. Re-run to
# refresh; already-downloaded files are skipped (idempotent, no re-download
# unless deleted first).
#
# Usage: python3 fetch_sefaria_reference_corpus.py
import json
import os
import subprocess
import urllib.parse
import urllib.request

REPO = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(REPO, "sefaria_reference_corpus", "raw")
BOOKS_JSON_URL = "https://raw.githubusercontent.com/Sefaria/Sefaria-Export/master/books.json"
# A floor, not a size check: every real book here is >100KB, so anything at
# or under this is an error page or a truncated transfer, never a short text.
# It is the ONLY thing separating "downloaded" from "present on disk", which
# is why download() deletes rather than leaves a file that fails it.
MIN_VALID_BYTES = 1000

TRACTATES = [
    "Berakhot", "Shabbat", "Eruvin", "Pesachim", "Beitzah", "Rosh Hashanah",
    "Yoma", "Sukkah", "Taanit", "Megillah", "Moed Katan", "Chagigah",
    "Yevamot", "Ketubot", "Nedarim", "Nazir", "Sotah", "Gittin", "Kiddushin",
    "Bava Kamma", "Bava Metzia", "Bava Batra", "Sanhedrin", "Makkot",
    "Shevuot", "Avodah Zarah", "Horayot", "Zevachim", "Menachot", "Chullin",
    "Bekhorot", "Arakhin", "Temurah", "Keritot", "Meilah", "Niddah", "Tamid",
]
SHULCHAN_ARUKH = [
    "Shulchan Arukh, Orach Chayim", "Shulchan Arukh, Yoreh De'ah",
    "Shulchan Arukh, Even HaEzer", "Shulchan Arukh, Choshen Mishpat",
]
TARGETS = set(TRACTATES) | set(SHULCHAN_ARUKH)


def out_path(title):
    safe = title.replace("/", "_").replace(",", "").replace("'", "")
    return os.path.join(OUT_DIR, f"{safe}.json")


def find_urls():
    with urllib.request.urlopen(BOOKS_JSON_URL) as resp:
        books = json.load(resp)["books"]
    found = {}
    for b in books:
        if b["language"] == "Hebrew" and b["versionTitle"] == "merged" and b["title"] in TARGETS:
            found[b["title"]] = b["json_url"]
    missing = TARGETS - set(found)
    if missing:
        raise SystemExit(f"books.json is missing expected title(s): {sorted(missing)}")
    return found


def download(title, url):
    # The bucket has literal spaces in paths (e.g. ".../Seder Zeraim/...");
    # curl needs them percent-encoded or the request silently fails (exit
    # code 0, empty file) rather than erroring.
    scheme_host, path = url.split("storage.googleapis.com", 1)
    enc_path = "/".join(urllib.parse.quote(seg) for seg in path.split("/"))
    enc_url = scheme_host + "storage.googleapis.com" + enc_path
    dest = out_path(title)
    r = subprocess.run(["curl", "-s", "-o", dest, "-w", "%{http_code}", enc_url],
                        capture_output=True, text=True)
    size = os.path.getsize(dest) if os.path.exists(dest) else 0
    ok = r.returncode == 0 and r.stdout.strip() == "200" and size > MIN_VALID_BYTES
    if not ok and os.path.exists(dest):
        # FIXED 2026-08-16 (code audit): curl writes its output file whatever
        # happens, and main()'s "already have it" test is only
        # `exists and size > MIN_VALID_BYTES`. A failed fetch that left an
        # error page or a truncated transfer behind was therefore counted as
        # a successful download by the NEXT run - the failure is reported
        # once, then permanently invisible. curl's own exit status was also
        # ignored entirely, so an aborted transfer still reported http 200.
        os.remove(dest)
        size = 0
    return r.stdout.strip(), size, ok


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    urls = find_urls()
    ok, failed = 0, []
    for title, url in sorted(urls.items()):
        dest = out_path(title)
        if os.path.exists(dest) and os.path.getsize(dest) > MIN_VALID_BYTES:
            ok += 1
            continue
        status, size, succeeded = download(title, url)
        if succeeded:
            ok += 1
        else:
            failed.append((title, status, size))
    print(f"{ok}/{len(urls)} texts present in {OUT_DIR}")
    if failed:
        print("FAILED:")
        for title, status, size in failed:
            print(f"  {title}: http={status} size={size}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
