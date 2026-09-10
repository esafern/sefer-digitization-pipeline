#!/usr/bin/env python3
"""
tools/experiment_scan_source.py

Does the full-tone scan beat the bitonal one on the error class that matters?

THE HYPOTHESIS (item 0FR). Our pipeline reads the Google Books scan because it
has the most pixels: 3528x5278, ~600 dpi. But it is 1 bit per pixel, and
cropping the same gimel from it and from NLI's RGB scan showed the leg of the
gimel WELDED to the neighbouring stroke in the bitonal copy and cleanly separate
in the full-tone one - at half the linear resolution. If that is general rather
than one lucky letter, the highest-pixel scan is the wrong input and the whole
nun/gimel class is an artifact of somebody else's thresholding.

THE TEST. Exactly the protocol of `tools/experiment_crop_resolution.py`, which
established the baseline: the same 66 positions where our OCR read nun and
Sefaria's reviewed text reads gimel, the same forced-choice prompt, the same
model, the same fixed-seed A/B assignment. Only the pixels change. Baseline to
beat: 18.2% correct from the bitonal scan at 300 dpi, 15.4% at 600.

Three sources are compared:
  `nli`       the full-tone RGB crop as scanned
  `nli_otsu`  the same crop binarized by us with Otsu - the test of whether OUR
              thresholding of a full-tone scan beats the scanner's
  (the bitonal baseline comes from the earlier run's cached results)

PAGE ALIGNMENT IS VALIDATED PER CASE, NOT ASSUMED. NLI's page images are not the
PDF's pages: they carry the full leaf with margins, the file numbering has its
own offset, and facing pages of solid text look alike. The offset is found per
page by correlating vertical ink profiles over a window, and a case is DROPPED
unless the best offset clears `--min-corr`. A mis-paired page would put a
different word in front of the model and quietly answer a different question.

Usage:
  GEMINI_API_KEY=... SEFER_CORPUS_ROOT=~/work/hashorashim \
    python3 tools/experiment_scan_source.py --cases /tmp/ng_located.json \
      --out ~/work/hashorashim/scan_source_experiment.json
"""

import argparse
import glob
import hashlib
import io
import json
import os
import random
import sys

import numpy as np
from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "pipeline"))
sys.path.insert(0, _HERE)
import fitz  # noqa: E402
import corpus_io as cio  # noqa: E402
import vision_adjudication_common as vac  # noqa: E402
from experiment_crop_resolution import PROMPT  # noqa: E402

TABLE = "scan_source_experiment"


def inkbox(im, thr, frac, inset=0.0):
    """The rectangle the printed text block occupies, ignoring scan borders."""
    W, H = im.size
    ox, oy = int(W * inset), int(H * inset)
    a = np.asarray(im.crop((ox, oy, W - ox, H - oy)).convert("L"), dtype=np.uint8)
    m = a < thr
    rows = np.where(m.mean(axis=1) > frac)[0]
    cols = np.where(m.mean(axis=0) > frac)[0]
    if len(rows) < 5 or len(cols) < 5:
        return None
    return (ox + int(cols[0]), oy + int(rows[0]), ox + int(cols[-1]), oy + int(rows[-1]))


def profile(im, box, n=200):
    a = np.asarray(im.crop(box).convert("L").resize((140, n)), dtype=float)
    r = (a < ((a.min() + a.max()) / 2)).astype(float).mean(axis=1)
    return (r - r.mean()) / (r.std() + 1e-9)


def find_nli_page(gb_img, nli_files, page, lo=-45, hi=-33):
    gbox = inkbox(gb_img, 170, 0.01)
    if gbox is None:
        return None, 0.0
    gp = profile(gb_img, gbox)
    best = (0.0, None)
    for off in range(lo, hi + 1):
        i = page + off
        if not (0 <= i < len(nli_files)):
            continue
        n = Image.open(nli_files[i])
        n.thumbnail((700, 1100))
        b = inkbox(n, 150, 0.02, inset=0.06)
        if b is None:
            continue
        s = float((gp * profile(n, b)).mean())
        if s > best[0]:
            best = (s, nli_files[i])
    return best[1], best[0]


def binarize_otsu(im):
    """Otsu's threshold, computed per crop.

    WHY OTSU AND NOT SAUVOLA. Sauvola is the usual recommendation, and it was
    tried first: at a 25 px window on a crop whose glyphs are ~40 px it HOLLOWED
    THE LETTERS OUT, turning solid strokes into outlines - it was reading letter
    interiors as background. Tuned to a sensible window it merely approaches what
    Otsu already does here, because a single word crop is small enough that a
    global threshold over it IS local with respect to the page. Two further
    traps, both hit: skimage's threshold_sauvola needs `r` matched to the input
    range (on 0-255 data with the default r=128 it returned thresholds above 1600
    and produced an all-black image), and the binarization must be computed on
    the ORIGINAL crop, not on an upscaled one, or the window no longer means what
    it says.

    This arm exists to test whether OUR binarization of a full-tone scan beats
    the scanner's binarization. It is not a claim that Otsu is the best possible
    pre-processing.
    """
    import cv2
    g = np.asarray(im.convert("L"), dtype=np.uint8)
    _t, out = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return Image.fromarray(out, mode="L")


def to_png(im, upscale=1):
    if upscale != 1:
        im = im.resize((im.width * upscale, im.height * upscale), Image.LANCZOS)
    buf = io.BytesIO()
    im.convert("RGB").save(buf, format="PNG")
    return buf.getvalue()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cases", required=True)
    ap.add_argument("--nli-glob", default="~/work/hashorashim/dedupmrg*/*.jpg")
    ap.add_argument("--min-corr", type=float, default=0.80)
    ap.add_argument("--upscale", type=int, default=2,
                    help="the NLI scan is ~313 dpi against the PDF's ~600; "
                         "upscaling equalises the apparent size, not the detail")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--seed", type=int, default=17)
    ap.add_argument("--out")
    args = ap.parse_args()

    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise SystemExit("GEMINI_API_KEY is not set")
    with open(os.path.expanduser(args.cases), encoding="utf-8") as fh:
        cases = json.load(fh)
    if args.limit:
        cases = cases[:args.limit]
    nli_files = sorted(glob.glob(os.path.expanduser(args.nli_glob)))
    if not nli_files:
        raise SystemExit("no NLI page images found")

    doc = fitz.open(cio.SCAN_PDF_PATH)
    client = vac.make_client(key)
    prompt_hash = hashlib.sha256(PROMPT.encode("utf-8")).hexdigest()[:16]
    db = os.path.join(os.path.dirname(cio.LEXICON_PATH), "adjudication_cache.db")
    vac.init_cache_table(db, TABLE, prompt_hash)

    # The SAME seed and draw order as the bitonal run, so A/B assignment matches
    # case for case and the two experiments are directly comparable.
    rng = random.Random(args.seed)
    page_cache = {}
    rows, dropped = [], 0
    for i, c in enumerate(cases, 1):
        ours, theirs = c["corpus"], c["witness_reading"]
        ours_is_a = rng.random() < 0.5
        a, b = (ours, theirs) if ours_is_a else (theirs, ours)
        page = int(c.get("page_used", c["page"]))
        if page not in page_cache:
            pix = doc.load_page(page - 1).get_pixmap(dpi=110)
            gb = Image.frombytes("RGB" if pix.n >= 3 else "L",
                                 (pix.width, pix.height), pix.samples)
            page_cache[page] = (find_nli_page(gb, nli_files, page), gb)
        (nli_path, corr), gb_small = page_cache[page]
        if nli_path is None or corr < args.min_corr:
            dropped += 1
            print(f"[{i}/{len(cases)}] p{page} DROPPED (page match corr {corr:.2f})")
            continue
        gbox = inkbox(gb_small, 170, 0.01)
        GW, GH = gb_small.size
        u = lambda x: ((x * GW) - gbox[0]) / (gbox[2] - gbox[0])
        v = lambda y: ((y * GH) - gbox[1]) / (gbox[3] - gbox[1])
        n = Image.open(nli_path)
        nb = inkbox(n, 150, 0.02, inset=0.06)
        if nb is None:
            dropped += 1
            continue
        NW, NH = nb[2] - nb[0], nb[3] - nb[1]
        bb = c["bbox"]
        pad = 0.02
        crop = n.crop((int(nb[0] + (u(bb["x1"]) - pad) * NW),
                       int(nb[1] + (v(bb["y1"]) - pad) * NH),
                       int(nb[0] + (u(bb["x2"]) + pad) * NW),
                       int(nb[1] + (v(bb["y2"]) + pad) * NH)))
        if crop.width < 12 or crop.height < 8:
            dropped += 1
            continue
        variants = {"nli": to_png(crop, args.upscale),
                    "nli_otsu": to_png(binarize_otsu(crop), args.upscale)}
        rec = {"page": page, "root": c.get("root"), "ours": ours, "truth": theirs,
               "ours_is_a": ours_is_a, "page_corr": round(corr, 3),
               "nli_file": os.path.basename(nli_path), "by_source": {}}
        prompt = PROMPT.format(a=a, b=b)
        for name, png in variants.items():
            ctx = f"src={name}"
            get = lambda: vac.get_cached_decision(db, TABLE, prompt_hash, png, a, b, ctx)
            put = lambda t, m: vac.put_cached_decision(db, TABLE, prompt_hash, png,
                                                       a, b, ctx, t, m)
            print(f"[{i}/{len(cases)}] p{page} {name}  {ours} vs {theirs}")
            try:
                raw = vac.adjudicate_with_retry(client, png, prompt, get, put)
                d = vac.parse_decision_lenient(raw)
                sel = vac.normalize_selected_option(d.get("selected_option"))
            except Exception as exc:                       # noqa: BLE001
                print(f"  -> failed: {exc}")
                sel, d = None, {}
            correct = (sel == ("B" if ours_is_a else "A")) if sel in ("A", "B") else None
            rec["by_source"][name] = {"selected": sel, "correct": correct,
                                      "confidence": d.get("confidence"),
                                      "read": d.get("transcription_found"),
                                      "reasoning": (d.get("reasoning") or "")[:200]}
        rows.append(rec)

    print("\n" + "=" * 62)
    print(f"  cases run {len(rows)}   dropped for weak page alignment {dropped}")
    print(f"  ground truth is always the reviewed reading (a gimel)\n")
    print(f"  {'source':<14} {'correct':>10}   {'rate':>7}")
    print(f"  {'bitonal 300':<14} {'12/66':>10}   {'18.2%':>7}   (previous run)")
    print(f"  {'bitonal 600':<14} {'10/65':>10}   {'15.4%':>7}   (previous run)")
    for name in ("nli", "nli_otsu"):
        got = [r for r in rows if r["by_source"].get(name, {}).get("correct") is not None]
        ok = sum(1 for r in got if r["by_source"][name]["correct"])
        rate = 100.0 * ok / max(1, len(got))
        print(f"  {name:<14} {f'{ok}/{len(got)}':>10}   {rate:>6.1f}%")
    if args.out:
        with open(os.path.expanduser(args.out), "w", encoding="utf-8") as fh:
            json.dump({"prompt": PROMPT, "rows": rows, "dropped": dropped},
                      fh, ensure_ascii=False, indent=1)
            fh.flush()
            os.fsync(fh.fileno())
        print(f"\n  wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
