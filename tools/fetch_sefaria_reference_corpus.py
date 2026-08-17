#!/usr/bin/env python3
# [STANDALONE] Downloads Shulchan Arukh (4 chelekim) + Talmud Bavli (37
# tractates) + Mishneh Torah (88 books) + Tur (1) + Rashi on Talmud (36
# tractates - EXTENDED 2026-08-17, see below) Hebrew text from Sefaria's
# public export bucket, for use as a GENUINELY INDEPENDENT Rabbinic Hebrew/
# Aramaic reference corpus - i.e. one not derived from this project's own
# OCR of the Berlin scan, unlike lexicon.txt (see PROJECT-STATUS.md
# "`lexicon.txt` cannot catch the ligature corruption - it contains it").
# Same halachic-code/Talmudic-citation register as Yad Malachi, which cites
# all of these constantly - Rambam/Tur/Rashi aren't just more of the same
# genre, they're specifically the works Yad Malachi is ABOUT (Klalei
# HaPoskim is the rules governing how Rif/Rambam/Rosh/Tur/Shulchan Arukh
# get decided between), so their vocabulary/phrasing overlap is higher-value
# than generic Talmud text alone - added per user request 2026-08-17.
#
# Source: https://github.com/Sefaria/Sefaria-Export - a public GCS bucket,
# one merged Hebrew-text JSON per book, no API key/auth needed. `books.json`
# is the bucket's own index (title/language/versionTitle -> json_url); this
# script filters it down to the TARGETS set rather than hardcoding URLs, so
# a future bucket reorganization breaks loudly (find_urls() exits naming the
# missing titles) rather than silently fetching nothing. The exact title
# strings for Mishneh Torah/Tur/Rashi below were read directly off a live
# books.json fetch (2026-08-17), not guessed - Sefaria addresses each of
# Mishneh Torah's 14 sifrei as ~83 separate per-hilchot "books" (e.g.
# "Mishneh Torah, Human Dispositions"), not one book or 14; Tur is a single
# merged title unlike Shulchan Arukh's 4 chelekim; Rashi has no entry for
# Tamid (a known gap in the traditional Rashi corpus, not an omission here)
# and also covers Tanakh/Midrash under the same "Rashi on X" prefix, which
# RASHI_ON_TALMUD deliberately excludes - Rashi's Talmud-commentary register
# is what overlaps with Yad Malachi's own citations, not his Torah commentary.
#
# Downloading a book is NOT the same as that book reaching the frequency
# table - validate_lexicon_independent.py owns the extraction, and one book
# (Shulchan Arukh, Even HaEzer) sat downloaded-and-counted here while
# contributing zero words to it until 2026-08-16. That script now warns per
# book; this one only promises bytes on disk.
#
# Output: sefaria_reference_corpus/raw/<Title>.json (166 files, ~140MB) -
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

# Moved one level deeper (pipeline/ or tools/) 2026-08-16 - REPO now goes up
# two levels, not one, to keep resolving to the actual repo root where
# part1.json/docai_word_boxes/etc. live.
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
# ADDED 2026-08-17 (user request) - see the module docstring for why these
# three specifically, and why the exact lists below (read off a live
# books.json, not guessed).
MISHNEH_TORAH = [
    "Mishneh Torah, Admission into the Sanctuary", "Mishneh Torah, Agents and Partners",
    "Mishneh Torah, Appraisals and Devoted Property", "Mishneh Torah, Blessings",
    "Mishneh Torah, Borrowing and Deposit", "Mishneh Torah, Circumcision",
    "Mishneh Torah, Creditor and Debtor",
    "Mishneh Torah, Daily Offerings and Additional Offerings",
    "Mishneh Torah, Damages to Property", "Mishneh Torah, Defilement by Leprosy",
    "Mishneh Torah, Defilement by a Corpse", "Mishneh Torah, Defilement of Foods",
    "Mishneh Torah, Diverse Species", "Mishneh Torah, Divorce", "Mishneh Torah, Eruvin",
    "Mishneh Torah, Fasts", "Mishneh Torah, Festival Offering",
    "Mishneh Torah, First Fruits and other Gifts to Priests Outside the Sanctuary",
    "Mishneh Torah, Firstlings", "Mishneh Torah, Forbidden Foods",
    "Mishneh Torah, Forbidden Intercourse",
    "Mishneh Torah, Foreign Worship and Customs of the Nations",
    "Mishneh Torah, Foundations of the Torah", "Mishneh Torah, Fringes",
    "Mishneh Torah, Gifts to the Poor", "Mishneh Torah, Heave Offerings",
    "Mishneh Torah, Hiring", "Mishneh Torah, Human Dispositions",
    "Mishneh Torah, Immersion Pools", "Mishneh Torah, Inheritances",
    "Mishneh Torah, Kings and Wars", "Mishneh Torah, Leavened and Unleavened Bread",
    "Mishneh Torah, Levirate Marriage and Release", "Mishneh Torah, Marriage",
    "Mishneh Torah, Mourning", "Mishneh Torah, Murderer and the Preservation of Life",
    "Mishneh Torah, Nazariteship", "Mishneh Torah, Negative Mitzvot",
    "Mishneh Torah, Neighbors", "Mishneh Torah, Oaths",
    "Mishneh Torah, Offerings for Those with Incomplete Atonement",
    "Mishneh Torah, Offerings for Unintentional Transgressions",
    "Mishneh Torah, One Who Injures a Person or Property",
    "Mishneh Torah, Other Sources of Defilement",
    "Mishneh Torah, Overview of Mishneh Torah Contents",
    "Mishneh Torah, Ownerless Property and Gifts", "Mishneh Torah, Paschal Offering",
    "Mishneh Torah, Plaintiff and Defendant", "Mishneh Torah, Positive Mitzvot",
    "Mishneh Torah, Prayer and the Priestly Blessing", "Mishneh Torah, Reading the Shema",
    "Mishneh Torah, Rebels", "Mishneh Torah, Red Heifer", "Mishneh Torah, Repentance",
    "Mishneh Torah, Rest on a Holiday", "Mishneh Torah, Rest on the Tenth of Tishrei",
    "Mishneh Torah, Ritual Slaughter", "Mishneh Torah, Robbery and Lost Property",
    "Mishneh Torah, Sabbath", "Mishneh Torah, Sabbatical Year and the Jubilee",
    "Mishneh Torah, Sacrifices Rendered Unfit", "Mishneh Torah, Sacrificial Procedure",
    "Mishneh Torah, Sales", "Mishneh Torah, Sanctification of the New Month",
    "Mishneh Torah, Scroll of Esther and Hanukkah",
    "Mishneh Torah, Second Tithes and Fourth Year's Fruit",
    "Mishneh Torah, Service on the Day of Atonement", "Mishneh Torah, Sheqel Dues",
    "Mishneh Torah, Shofar, Sukkah and Lulav", "Mishneh Torah, Slaves",
    "Mishneh Torah, Substitution", "Mishneh Torah, Tefillin, Mezuzah and the Torah Scroll",
    "Mishneh Torah, Testimony", "Mishneh Torah, The Chosen Temple",
    "Mishneh Torah, The Order of Prayer",
    "Mishneh Torah, The Sanhedrin and the Penalties within Their Jurisdiction",
    "Mishneh Torah, Theft", "Mishneh Torah, Things Forbidden on the Altar",
    "Mishneh Torah, Those Who Defile Bed or Seat", "Mishneh Torah, Tithes",
    "Mishneh Torah, Torah Study", "Mishneh Torah, Transmission of the Oral Law",
    "Mishneh Torah, Trespass", "Mishneh Torah, Vessels",
    "Mishneh Torah, Vessels of the Sanctuary and Those Who Serve Therein",
    "Mishneh Torah, Virgin Maiden", "Mishneh Torah, Vows",
    "Mishneh Torah, Woman Suspected of Infidelity",
]
TUR = ["Tur"]
# Excludes Tamid (no Rashi commentary exists for it) and every "Rashi on X"
# outside Talmud (Tanakh, Bereshit Rabbah) - see module docstring.
RASHI_ON_TALMUD = [f"Rashi on {t}" for t in TRACTATES if t != "Tamid"]
TARGETS = set(TRACTATES) | set(SHULCHAN_ARUKH) | set(MISHNEH_TORAH) | set(TUR) | set(RASHI_ON_TALMUD)


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
