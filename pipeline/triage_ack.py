# [PRODUCTION] ONE STORE FOR "A HUMAN CHECKED THIS AND IT IS FINE".
#
# WHY THIS EXISTS. The same concept had grown three different homes and two
# report types had none at all, found 2026-09-08 when the reviewer asked to clear
# a finding and then asked "where are these stored anyway?":
#
#   * structural_defect_acknowledged.json - a real data file, keyed on content
#     (klal | detector | stored | occurrence). This is the shape that was right.
#   * tools/list_ligature_words.py's KNOWN_FALSE_POSITIVES - a dict HARDCODED IN
#     SOURCE, keyed `(klal_id, word_index)`. Clearing a finding meant editing a
#     script, and the key DRIFTS: an insertion anywhere earlier in the klal moves
#     every later index, so the resolution silently lands on a different word.
#     That is the exact failure structural_defect_report._key's comment explains
#     it is avoiding, in a sibling file, in the opposite direction.
#   * review_decisions.jsonl - the ledger. Correct for a RULING (a change to the
#     text), wrong for "this detector is mistaken", which changes nothing.
#   * lexical_defect_report.json and title_defect_report.json - NOTHING. A
#     finding in either could not be cleared at all; it returned on every
#     rebuild forever.
#
# THE KEY IS CONTENT, NEVER AN INDEX. `klal | detector | stored | occurrence`:
#   - not word_index, because it moves on every earlier edit and an
#     acknowledgement that evaporates is worse than none - the finding comes back
#     looking new and the reviewer re-checks work they already did;
#   - `stored` IS in it, because acknowledging says "this text, here, is correct
#     as printed", so if the text changes the acknowledgement correctly lapses;
#   - `occurrence` disambiguates two findings alike in one klal, in word_index
#     ORDER, which survives a uniform shift because every index moves together.
#     Occurrence 0 carries no suffix so keys written before it existed still
#     match (item 0DE finding 7).
#
# It records a JUDGEMENT ABOUT A DETECTOR, not a decision about the corpus, so it
# is deliberately NOT the ledger: nothing here can change a word, and a rebuild
# regenerates every report from the corpus while these survive.
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import corpus_io as cio  # noqa: E402


# WHICH FIELD HOLDS THE TEXT, per report. The reports disagree and that is fine:
# the structural and lexical ones call it `stored`, the title one `title_word`.
# A parameter rather than a rename, because the field name is part of each
# report's published schema and something reads them.
def _text(row, text_field):
    return row[text_field]


def key(row, occurrence=0, text_field="stored"):
    """The identity an acknowledgement is recorded against. See the header."""
    base = f"{row['klal_id']}|{row['detector']}|{_text(row, text_field)}"
    return base if not occurrence else f"{base}|#{occurrence + 1}"


def keys_for(rows, text_field="stored"):
    """Keys for `rows`, IN THE SAME ORDER as rows.

    A LIST, not a dict keyed on id(row) - which is what this returned first.
    `id()` is only unique among objects that are simultaneously ALIVE, so a
    caller who built its rows inline and let them go could have two rows share a
    key, silently. Nothing did that, and nothing should have to know not to.
    Position is what the caller already has.

    The ORDINAL is still assigned in (klal, detector, text, word_index) order,
    which is the part that has to be stable across a shift; only the return
    shape changed.
    """
    order = sorted(range(len(rows)),
                   key=lambda i: (rows[i]["klal_id"], rows[i]["detector"],
                                  _text(rows[i], text_field), rows[i]["word_index"]))
    seen, out = {}, [None] * len(rows)
    for i in order:
        r = rows[i]
        base = (r["klal_id"], r["detector"], _text(r, text_field))
        n = seen.get(base, 0)
        seen[base] = n + 1
        out[i] = key(r, n, text_field)
    return out


def load(path):
    """{key: entry} from an acknowledgement file, or {} if it does not exist."""
    return {e["key"]: e for e in (cio.load_json(path, default=[]) or [])}


def annotate(rows, path, text_field="stored"):
    """Stamp `acknowledged` / `acknowledged_on` / `acknowledged_note` onto rows.

    Returns the rows, so a builder can `return ack.annotate(rows, ACK_PATH)`.
    """
    store = load(path)
    for r, k in zip(rows, keys_for(rows, text_field)):
        hit = store.get(k)
        r["acknowledged"] = bool(hit)
        if hit:
            r["acknowledged_on"] = hit.get("ts")
            r["acknowledged_note"] = hit.get("note")
    return rows


def record(rows, path, note, only=None, text_field="stored"):
    """Acknowledge `rows` (or the subset `only` selects) into `path`.

    `only` is a predicate on a row - the caller's filter, so this stays one
    mechanism rather than growing a flag per report. Returns how many were added;
    an already-acknowledged key is left exactly as it was, with its original
    timestamp and note, because re-stamping would erase when a thing was checked.
    """
    store = load(path)
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    added = 0
    for r, k in zip(rows, keys_for(rows, text_field)):
        if only is not None and not only(r):
            continue
        if k in store:
            continue
        store[k] = {"key": k, "ts": stamp, "note": note, "klal_id": r["klal_id"],
                    "detector": r["detector"], "stored": _text(r, text_field),
                    "word_index_when_recorded": r.get("word_index")}
        added += 1
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sorted(store.values(), key=lambda e: (e["klal_id"], e["detector"])),
                  f, ensure_ascii=False, indent=2)
        f.write("\n")
        f.flush()
    return added
