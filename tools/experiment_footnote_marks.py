#!/usr/bin/env python3
"""
tools/experiment_footnote_marks.py

[EXPERIMENT] Size reading raised footnote numerals from the image (item 0GO).

Sefer HaShorashim numbers its footnote references per page, 1, 2, 3 ..., and
prints them small and raised after a word. Our OCR reads some of them as a mark
(`"`, `'`, `*`). A gap in the page's sequence says which number is missing
where, but from OCR text alone that numbered only 15 of 20 checked marks
correctly: a misread neighbouring numeral shifts the count, and real
abbreviation marks (`אח׳`) and a small raised circle look the same in the text.

This asks a vision model what is printed at each mark, on a seeded sample: half
marks the sequence predicts a number for, half it cannot place. Its answers are
then scored against the ink and against the sequence before any full run.

  GEMINI_API_KEY=... SEFER_CORPUS_ROOT=~/work/hashorashim \\
      python3 tools/experiment_footnote_marks.py --n 20 \\
      --out footnote_marks_sample.json --montage /tmp/marks

The montage images are labelled by row number only, so whoever judges the crops
sees neither the model's answer nor the sequence's prediction first.
"""
import argparse
import bisect
import collections
import difflib
import hashlib
import io
import json
import os
import random
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "pipeline"))
import corpus_io as cio  # noqa: E402
import vision_adjudication_common as vac  # noqa: E402
import build_root_corpus as brc  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

NUM = cio.FOOTNOTE_REF
MARK = re.compile(r'^["״”\'׳`*]+$')
TABLE = "footnote_mark_reading"

PROMPT = """You are looking at a small crop of a page from a Hebrew book printed in
Berlin in 1896. A red box marks one spot, just after a Hebrew word.

This book marks its footnotes with small raised Arabic numerals (superscripts)
printed right after a word, numbered 1, 2, 3 ... on each page. It also prints
two things that can look similar: the geresh or gershayim of a Hebrew
abbreviation (a small stroke or double stroke), and a small raised circle.

What is printed at the red box? The box marks where our text recognition put
the mark, and it often covers only PART of a raised number: a two-digit number
such as 17 or 36 may have one digit inside the box and the other just outside
it. If there is a raised number there, read the WHOLE number, including any
digit that sits right next to the box. Judge only what you can see.

Reply with JSON only, and do not use quotation marks inside the reasoning:
{"kind": "numeral" or "geresh" or "gershayim" or "circle" or "nothing" or "other",
 "number": <the numeral as an integer if kind is numeral, otherwise null>,
 "confidence": <0.0-1.0>,
 "reasoning": "<one sentence about what you see>"}"""


def candidates(stream):
    """{page: [{"text", "tok", "prev"}]} - numerals and stray marks in reading order."""
    pages = collections.defaultdict(list)
    for page, _text, toks in stream:
        prev = None
        for t in toks:
            w = t["text"].strip()
            if NUM.match(w) or MARK.match(w):
                pages[page].append({"text": w, "tok": t, "prev": prev})
            prev = t
    return pages


def _rising_run(vals):
    """Indices of the longest strictly rising subsequence of `vals`."""
    tails, idx, back = [], [], [-1] * len(vals)
    for i, v in enumerate(vals):
        j = bisect.bisect_left(tails, v)
        if j == len(tails):
            tails.append(v)
            idx.append(i)
        else:
            tails[j] = v
            idx[j] = i
        back[i] = idx[j - 1] if j else -1
    out, k = [], idx[-1] if idx else -1
    while k != -1:
        out.append(k)
        k = back[k]
    return out[::-1]


def predict(cands):
    """({index in cands: number} where a gap's missing numbers equal its tokens,
    [(index, value)] of the page's rising run of numerals)."""
    nums = [k for k, c in enumerate(cands) if NUM.match(c["text"])]
    chain = [nums[i] for i in _rising_run([int(cands[k]["text"]) for k in nums])]
    out, pk, pv = {}, -1, 0
    for k in chain:
        v = int(cands[k]["text"])
        between = list(range(pk + 1, k))
        if between and v - pv - 1 == len(between):
            out.update(zip(between, range(pv + 1, v)))
        pk, pv = k, v
    return out, [(k, int(cands[k]["text"])) for k in chain]


def crop_mark(page, cand, upscale=3):
    """The mark and the word before it, with a red box round the mark."""
    img = Image.open(cio.repo_path(os.path.join("images", "pdf_pages", f"page_{page}.png"))).convert("RGB")
    W, H = img.size
    t, prev = cand["tok"], cand["prev"] or cand["tok"]
    x1, x2 = min(t["x1"], prev["x1"]), max(t["x2"], prev["x2"])
    y1, y2 = min(t["y1"], prev["y1"]), max(t["y2"], prev["y2"])
    L, T = int(max(0, x1 - 0.05) * W), int(max(0, y1 - 0.015) * H)
    R, B = int(min(1, x2 + 0.05) * W), int(min(1, y2 + 0.015) * H)
    crop = img.crop((L, T, R, B))
    # The box is widened by the mark's own height on each side: the OCR's mark is
    # often ONE digit of a two-digit numeral, and a box drawn tight round it
    # got that one digit read back (item 0GO, first sample: 11 of 36).
    m = 3
    grow = int((t["y2"] - t["y1"]) * H)
    ImageDraw.Draw(crop).rectangle(
        (int(t["x1"] * W) - L - m - grow, int(t["y1"] * H) - T - m,
         int(t["x2"] * W) - L + m + grow, int(t["y2"] * H) - T + m),
        outline=(220, 0, 0), width=2)
    return crop.resize((crop.width * upscale, crop.height * upscale), Image.LANCZOS)


def parse(raw):
    try:
        return json.loads(vac.sanitize_json(raw))
    except Exception:                                    # noqa: BLE001
        get = lambda k, pat: (re.search(rf'"{k}"\s*:\s*{pat}', raw) or [None, None])[1]
        n = get("number", r"(\d+|null)")
        return {"kind": get("kind", r'"([a-z]+)"'),
                "number": int(n) if n and n.isdigit() else None,
                "confidence": float(get("confidence", r"([0-9.]+)") or 0),
                "reasoning": "(unparsed)"}


def decide(predicted, kind, number, lo=0, hi=None, page_numbers=(), neighbours=()):
    """The rule, sized on 40 marks read by eye and refined on the full run
    (item 0GO):
    * the model calls it a geresh, gershayim or circle: not a footnote;
    * the model reads no number: unread;
    * the page already has that number as a numeral - beside the mark, or in
      the page's rising run: a DUPLICATE. A page numbers each footnote once, so
      this is the same printed numeral read twice, once as a number and once as
      a mark. Nothing new to draw. On the full run this was 67 of the 132 rows
      a plain order check sent to review, and the model's reading was right on
      every one checked by eye;
    * the two agree: that number;
    * they disagree: review. On the sample each side was right in some;
    * the page's sequence has no number for it: the model's number, if it falls
      between the page's numerals either side of the mark (`lo`, `hi`),
      otherwise review;
    * an accepted number of which a numeral beside the mark is a part (`5`
      beside a mark read as 50): a SPLIT - one printed numeral read as two
      tokens. The mark shows the whole number and the digit beside it is
      folded into it.
    Returns (decision, number, absorbed), absorbed being the neighbour's text
    for a split and otherwise None."""
    if kind in ("geresh", "gershayim", "circle"):
        return "not_a_footnote", None, None
    if kind != "numeral" or number is None:
        return "unread", None, None
    s = str(number)
    part = next((x for x in neighbours
                 if len(x) < len(s) and (s.startswith(x) or s.endswith(x))), None)
    if number == predicted:
        return ("split" if part else "accepted"), number, part
    # A disagreement with the sequence is decided by a person BEFORE the
    # duplicate test: at p100 the sequence said 31, the model misread 21, 21 was
    # already on the page, and a duplicate verdict would have discarded the
    # mark the sequence had right.
    if predicted is not None:
        return "review", None, None
    if s in neighbours or number in page_numbers:
        return "duplicate", number, None
    if number > (lo or 0) and (hi is None or number < hi):
        return ("split" if part else "accepted"), number, part
    return "review", None, None


def one_number_each(rows):
    """A page numbers each footnote once. Two marks given the same number on one
    page are one printed numeral read as several tokens when they sit next to
    each other - the later becomes a duplicate - and otherwise a contradiction
    for a person (review). Found on the full run: entry 93 words 67 and 69, a
    `"` either side of a `4`, both read as the split 14 absorbing that `4`."""
    seen = {}
    for r in sorted(rows, key=lambda r: (r["page"], r["index_on_page"])):
        if r["decision"] not in ("accepted", "split"):
            continue
        first = seen.get((r["page"], r["number"]))
        if first is None:
            seen[(r["page"], r["number"])] = r
            continue
        if abs(r["index_on_page"] - first["index_on_page"]) <= 2:
            r["decision"] = "duplicate"
        else:
            r["decision"], r["number"] = "review", None
        r["absorbs"] = None


def token_places(stream):
    """{id(token): (klal_id, word_index)}, by aligning the build's token stream
    with the corpus words - the corpus IS that stream, cut into entries. The
    server's word boxes cannot do it: a punctuation-only word gets no box there
    (entry 15 word 6, the `"` on p61), and looking marks up that way placed 0
    of 577."""
    flat = [t for _page, _text, line in stream for t in line]
    words = [(k["klal_id"], i, w) for k in cio.load_part1_sorted()
             for i, w in enumerate(cio.words_of(k))]
    sm = difflib.SequenceMatcher(None, [t["text"].strip() for t in flat],
                                 [w for _kid, _i, w in words])
    where = {}
    for a, b, n in sm.get_matching_blocks():
        for j in range(n):
            where[id(flat[a + j])] = words[b + j][:2]
    return where


def montage(rows, crops, path, per=10):
    paths = []
    for n in range(0, len(rows), per):
        chunk = list(zip(rows, crops))[n:n + per]
        w = max(c.width for _, c in chunk) + 70
        h = sum(c.height + 10 for _, c in chunk)
        m = Image.new("RGB", (w, h), "white")
        d = ImageDraw.Draw(m)
        y = 0
        for r, c in chunk:
            d.text((6, y + c.height // 2 - 6), f"#{r['row']}", fill=(200, 0, 0))
            m.paste(c, (70, y))
            y += c.height + 10
        out = f"{path}_{n // per + 1}.png"
        m.save(out)
        paths.append(out)
    return paths


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pages", default="58-151")
    ap.add_argument("--n", type=int, default=20, help="marks per half of the sample")
    ap.add_argument("--seed", type=int, default=17)
    ap.add_argument("--all", action="store_true",
                    help="read every stray mark, not a sample (the full run, item 0GO)")
    ap.add_argument("--out", required=True, help="results JSON, in the corpus root")
    ap.add_argument("--montage", help="path prefix for crop sheets (sample runs)")
    args = ap.parse_args()

    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise SystemExit("GEMINI_API_KEY is not set")
    lo, hi = (int(x) for x in args.pages.split("-"))
    stream, _ = brc.build(range(lo, hi + 1))
    pages = candidates(stream)

    placed, unplaced = [], []
    for page, cands in sorted(pages.items()):
        pred, anchors = predict(cands)
        page_numbers = {v for _kk, v in anchors}
        for k, c in enumerate(cands):
            if MARK.match(c["text"]):
                lo = max((v for kk, v in anchors if kk < k), default=0)
                hi = min((v for kk, v in anchors if kk > k), default=None)
                nbs = [cands[j] for j in (k - 1, k + 1)
                       if 0 <= j < len(cands) and NUM.match(cands[j]["text"])]
                (placed if k in pred else unplaced).append(
                    (page, k, c, pred.get(k), lo, hi, page_numbers, nbs))
    if args.all:
        sample = sorted(placed + unplaced, key=lambda s: (s[0], s[1]))
    else:
        rng = random.Random(args.seed)
        sample = rng.sample(placed, min(args.n, len(placed))) + \
            rng.sample(unplaced, min(args.n, len(unplaced)))
        rng.shuffle(sample)
    print(f"  marks: {len(placed)} with a predicted number, {len(unplaced)} without; "
          f"sampling {len(sample)}")

    client = vac.make_client(key)
    prompt_hash = hashlib.sha256(PROMPT.encode("utf-8")).hexdigest()[:16]
    db = os.path.join(os.path.dirname(cio.LEXICON_PATH), "adjudication_cache.db")
    vac.init_cache_table(db, TABLE, prompt_hash)

    rows, crops, toks, nb_toks, numbers_on_page = [], [], [], [], []
    for i, (page, k, c, pred, lo, hi, page_numbers, nbs) in enumerate(sample, 1):
        toks.append(c["tok"])
        nb_toks.append(nbs)
        numbers_on_page.append(page_numbers)
        crop = crop_mark(page, c)
        buf = io.BytesIO()
        crop.save(buf, format="PNG")
        png = buf.getvalue()
        ctx = f"p{page} k{k}"
        get = lambda: vac.get_cached_decision(db, TABLE, prompt_hash, png, "mark", c["text"], ctx)
        put = lambda t, m: vac.put_cached_decision(db, TABLE, prompt_hash, png, "mark",
                                                   c["text"], ctx, t, m)
        print(f"[{i}/{len(sample)}] p{page} mark {c['text']!r} predicted {pred}")
        try:
            d = parse(vac.adjudicate_with_retry(client, png, PROMPT, get, put))
        except Exception as exc:                          # noqa: BLE001
            print(f"  -> failed: {exc}")
            d = {}
        rows.append({"row": i, "page": page, "index_on_page": k, "mark": c["text"],
                     "prev_word": (c["prev"] or {}).get("text"), "predicted": pred,
                     "between": [lo, hi],
                     "neighbours": [n["text"] for n in nbs],
                     "bbox": {q: c["tok"][q] for q in ("x1", "y1", "x2", "y2")},
                     "model_kind": d.get("kind"), "model_number": d.get("number"),
                     "model_confidence": d.get("confidence"),
                     "model_reasoning": (d.get("reasoning") or "")[:200]})
        if args.montage:
            crops.append(crop)

    where = token_places(stream)
    for r, t, nbs, page_numbers in zip(rows, toks, nb_toks, numbers_on_page):
        r["decision"], r["number"], part = decide(
            r["predicted"], r["model_kind"], r["model_number"], *r["between"],
            page_numbers, r["neighbours"])
        r["klal_id"], r["word_index"] = where.get(id(t), (None, None))
        # The digit a split folds in, placed the same way; it must sit in the
        # same entry, or the split is not drawn as one.
        absorbed = next((n for n in nbs if n["text"] == part), None) if part else None
        kid, wi = where.get(id(absorbed["tok"]), (None, None)) if absorbed else (None, None)
        r["absorbs"] = wi if kid is not None and kid == r["klal_id"] else None
        if r["decision"] == "split" and r["absorbs"] is None:
            r["decision"], r["number"] = "review", None
    one_number_each(rows)
    sheets = montage(rows, crops, os.path.expanduser(args.montage)) if args.montage else []
    counts = collections.Counter(r["decision"] for r in rows)
    out = cio.repo_path(args.out)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"what_this_is": "Stray marks in the OCR text read from the page image as "
                                   "footnote reference numerals, or not (pipeline item 0GO). "
                                   "The text is unchanged; accepted rows are drawn as raised "
                                   "numerals by the dashboard.",
                   "prompt": PROMPT, "rule": decide.__doc__,
                   "seed": None if args.all else args.seed, "counts": dict(counts),
                   "rows": rows}, fh, ensure_ascii=False, indent=1)
        fh.flush()
        os.fsync(fh.fileno())
    print(f"\n  decisions       {dict(counts)}")
    print(f"  located         {sum(1 for r in rows if r['word_index'] is not None)} of {len(rows)} "
          f"at an entry word")
    for r in rows:
        if r["decision"] == "review" and r["word_index"] is not None:
            print(f"    review  http://127.0.0.1:8421/entry/{r['klal_id']}/word/{r['word_index']}"
                  f"  sequence {r['predicted']}, model {r['model_number']}")
    print(f"  wrote {out}")
    for s in sheets:
        print(f"  sheet {s}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
