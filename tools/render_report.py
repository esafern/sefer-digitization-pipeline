#!/usr/bin/env python3
# [STANDALONE] Render any of this repo's finding reports as Markdown or HTML,
# with every klal/word turned into a clickable dashboard deep link.
#
# WHY. The reports are written as JSON because that is what the pipeline reads
# and diffs, but JSON is a poor way to HAND a list of findings to a person: the
# URLs are inert text. The reviewer put it plainly - "the json is not a good way
# to share the urls - it is not clickable". Same data, a form you can click.
#
# Markdown is the default because it renders as links in almost anything a
# finding gets pasted into. HTML is there for the case where you want to open the
# list in the browser you already have the dashboard in, since the links are
# same-origin and simply work.
#
# THE LINKS ARE LOCAL BY CONSTRUCTION. They point at 127.0.0.1:8420, so they
# resolve only on a machine running the dashboard. That is the right trade for a
# review tool and the wrong one for anything published - do not paste these into
# something outward-facing and expect them to work.
#
# Usage:
#   python3 tools/render_report.py cleared_flags_2026-08-26.json
#   python3 tools/render_report.py lexical_defect_report.json --format html
#   python3 tools/render_report.py ligature_words.json --section dropped_alef
import argparse
import html
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pipeline"))

import corpus_io as cio  # noqa: E402

DEFAULT_BASE = "http://127.0.0.1:8420"
# The same key under the several names the reports actually use, rather than
# forcing every report to be rewritten to one schema.
KLAL_KEYS = ("klal_id", "klal")
# `word` is genuinely ambiguous across these reports - an INDEX in
# cleared_flags_*.json, the word TEXT in lexicon_yad_malachi_only.json - so it is
# resolved by type, not by name. Guessing by name alone silently dropped every
# word index from the first run's links.
WORD_KEYS = ("word_index", "word_idx", "word")


def link(base, klal, word=None):
    """A PATH link, not the hash form the frontend routes on.

    `/#klal=66&word=135` travels badly: a terminal will not hyperlink Markdown
    link syntax at all, and several that DO linkify a bare URL stop at the `&` -
    which opens the right klal at the wrong word, worse than a link that plainly
    fails. `/klal/66/word/135` has no `#` and no `&`, so it survives being pasted
    into a terminal, a chat window or a plain-text note. The server 302s it to the
    hash form (ROUTE_SHARE in review_server.py).
    """
    return f"{base}/klal/{klal}" + ("" if word is None else f"/word/{word}")


def positions(row):
    """[(klal, word), ...] for a row, however that row happens to name them.

    Word-centric reports (one row per WORD, many occurrences) carry an
    `occurrences` list; position-centric reports carry the pair on the row
    itself. Both shapes exist in this repo and neither is wrong."""
    klal = next((row[k] for k in KLAL_KEYS if k in row), None)
    word = next((row[k] for k in WORD_KEYS
                 if k in row and isinstance(row[k], int)), None)
    if klal is not None:
        return [(klal, word)]
    out = []
    for occ in row.get("occurrences") or []:
        if isinstance(occ, (list, tuple)) and len(occ) >= 2:
            out.append((occ[0], occ[1]))
    return out


def describe(row):
    """A short human column: whatever the row says about itself."""
    head = ""
    for key in ("stored", "word"):
        if key in row and isinstance(row[key], str):
            head = row[key]
            break
    bits = []
    if row.get("repaired"):
        bits.append(f"→ {row['repaired']}")
    if row.get("lexical_proposal"):
        bits.append(f"→ {row['lexical_proposal']}")
    for p in (row.get("proposals") or [])[:2]:
        if p.get("form"):
            bits.append(f"→ {p['form']}" + (f" ({p['ref_count']}x)" if p.get("ref_count") else ""))
    for p in (row.get("nearest_attested") or [])[:2]:
        bits.append(f"→ {p['form']} ({p['ref_count']}x)")
    if row.get("reason"):
        bits.append(str(row["reason"]))
    if row.get("resolved_false_positive"):
        bits.append(f"RESOLVED FALSE POSITIVE: {row['resolved_false_positive']}")
    if row.get("count"):
        bits.append(f"{row['count']}x in this part")
    return head, "; ".join(bits)


def rows_of(data, section):
    if isinstance(data, list):
        return {"": data}
    if section:
        return {section: data.get(section) or []}
    return {k: v for k, v in data.items() if isinstance(v, list) and v}


# Markdown has no stylesheet, so the `direction:rtl;unicode-bidi:isolate` that
# render_html() sets on `.heb` has no counterpart here - and measured
# 2026-09-01, `glow` and the terminals in use implement no bidi at all (Hebrew
# comes out byte-for-byte as it went in). Logical order therefore DISPLAYS
# BACKWARDS in the one place these reports are actually read, and bidi control
# characters are inert because nothing reads them. The only remaining lever is
# to bake the reordering into the characters. See PROJECT-STATUS.md item 0R.
#
# HTML must never get this treatment: it has a real bidi engine and would
# double-reverse.
HEBREW_RE = re.compile(r"[\u0590-\u05ff]")


def to_visual(text):
    """Reorder a line's Hebrew for a renderer that does none of it itself.

    python-bidi's implementation of the real algorithm, not a hand-rolled
    reverse: naive reversal mishandles gershayim, embedded digits and Latin,
    and these reports are full of `דף ג' ב'` and mixed Hebrew/English detail.
    Base direction stays L, so links, digits and ASCII are untouched.
    """
    from bidi.algorithm import get_display
    return get_display(text, base_dir="L") if HEBREW_RE.search(text) else text


def render_markdown(name, sections, base, limit, hebrew="visual"):
    out = [f"# {name}", ""]
    for title, rows in sections.items():
        if title:
            out += [f"## {title} ({len(rows)})", ""]
        out += ["| klal · word | text | detail |", "|---|---|---|"]
        n = 0
        for row in rows:
            head, detail = describe(row)
            for klal, word in positions(row):
                label = f"klal {klal}" + (f" w{word}" if word is not None else "")
                out.append(f"| [{label}]({link(base, klal, word)}) | {head} | {detail} |")
                n += 1
                if limit and n >= limit:
                    break
            if limit and n >= limit:
                out.append(f"| … | | _{len(rows) - rows.index(row) - 1} more rows omitted_ |")
                break
        out.append("")
    if hebrew == "visual":
        out = [to_visual(l) for l in out]
    return "\n".join(out)


def render_html(name, sections, base, limit):
    e = html.escape
    out = ["<!doctype html><meta charset='utf-8'>", f"<title>{e(name)}</title>",
           "<style>body{font-family:system-ui,sans-serif;margin:2rem;max-width:60rem}"
           "table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid #ddd;"
           "padding:6px 8px;text-align:left;vertical-align:top;font-size:14px}"
           "a{color:#2b6cb0}.heb{font-size:17px;direction:rtl;unicode-bidi:isolate}"
           "</style>", f"<h1>{e(name)}</h1>",
           "<p><em>Links open the local review dashboard and work only while it is "
           "running on this machine.</em></p>"]
    for title, rows in sections.items():
        if title:
            out.append(f"<h2>{e(title)} ({len(rows)})</h2>")
        out.append("<table><tr><th>klal · word</th><th>text</th><th>detail</th></tr>")
        n = 0
        for row in rows:
            head, detail = describe(row)
            for klal, word in positions(row):
                label = f"klal {klal}" + (f" w{word}" if word is not None else "")
                out.append(f"<tr><td><a href='{e(link(base, klal, word))}'>{e(label)}</a></td>"
                           f"<td class='heb'>{e(head)}</td><td class='heb'>{e(detail)}</td></tr>")
                n += 1
                if limit and n >= limit:
                    break
            if limit and n >= limit:
                break
        out.append("</table>")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report", help="a report .json in the repo root")
    ap.add_argument("--format", choices=("markdown", "html"), default="markdown")
    ap.add_argument("--hebrew", choices=("visual", "logical"), default="visual",
                    help="markdown only. visual (default): reorder Hebrew so it "
                         "reads correctly in a terminal that does no bidi, e.g. "
                         "glow - but do not copy Hebrew out of it. logical: "
                         "canonical order, correct in any bidi-aware reader. "
                         "HTML is always logical; it has its own bidi engine.")
    ap.add_argument("--section", default=None, help="one key, for a report that is a dict of lists")
    ap.add_argument("--limit", type=int, default=0, help="cap rows per section (0 = all)")
    ap.add_argument("--base", default=DEFAULT_BASE)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    path = args.report if os.path.isabs(args.report) else cio.repo_path(args.report)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    sections = rows_of(data, args.section)
    name = os.path.basename(path)
    # hebrew= is markdown-only: render_html relies on CSS bidi and would
    # double-reverse if handed pre-reordered characters.
    if args.format == "markdown":
        body = render_markdown(name, sections, args.base.rstrip("/"), args.limit,
                               hebrew=args.hebrew)
    else:
        body = render_html(name, sections, args.base.rstrip("/"), args.limit)
    out = args.out or os.path.splitext(path)[0] + (".md" if args.format == "markdown" else ".html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(body)
        f.flush()
    total = sum(len(v) for v in sections.values())
    print(f"Wrote {out} ({total} row(s) across {len(sections)} section(s))")


if __name__ == "__main__":
    main()
