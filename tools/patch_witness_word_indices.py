#!/usr/bin/env python3
"""One-time (idempotent) patch: add word_index to reconstruction_witness_queue.json.

witness items carry docai_token_index (an index into the page's DocAI token
list) but not a corpus word_index.  Reviewers need the corpus position so the
dashboard can highlight the word in the text pane alongside the scan boxes.

The mapping is computed via difflib.SequenceMatcher between the normalized
DocAI token stream and the normalized corpus word list for each klal.  Coverage
is high (873/880 tokens mapped for klal 30's page 24 in testing).  Items whose
token falls in an unmapped gap (rare - typically tokens that are pure furniture
or appear in a large-span skip) get word_index=null.

Multi-token DocAI segments (opcode 'replace' where the reading spans several
tokens, e.g. 'חטאת הוו' for token_index 29) map to the FIRST corpus word of
the span - enough to locate and highlight the word.

Safe to re-run: the script reads the existing queue, recomputes, and overwrites.
Any previously-computed word_index values are replaced with the freshly computed
ones (the computation is deterministic given the same corpus + DocAI pages).
"""
import difflib
import argparse
import json
import os
import sys

# THE SPLIT, and it is not cosmetic (item 0BI). `REPO` here used to be BOTH
# "where this code lives" and "where the corpus lives", and those are different
# questions the moment $SEFER_CORPUS_ROOT points somewhere else. A script that
# conflates them ignores the seam entirely and writes into the real repository
# no matter which corpus it was told to target - which is exactly what
# synthesize_multi_witness.py did on 2026-09-03, truncating 6,981 lines of
# tracked data to `{}` the first time anything exercised it. INSTALL_DIR is the
# checkout, for sys.path only; corpus data goes through cio.repo_path().
INSTALL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(INSTALL_DIR, "pipeline"))
sys.path.insert(0, os.path.join(INSTALL_DIR, "tools"))

import corpus_io as cio  # noqa: E402
import review_data as rdata  # noqa: E402

_LAZY = {
    "OUT_PATH": lambda: cio.repo_path("reconstruction_witness_queue.json"),
    "DOCAI_DIR": lambda: cio.DOCAI_DIR,
}

# INTERNAL CALLERS GO THROUGH cio DIRECTLY, not through the names below. A
# module-level `__getattr__` serves ATTRIBUTE access from outside
# (`mod.OUT_PATH`); it is NOT consulted for a bare global lookup inside this
# module's own functions, which raises NameError instead. Caught by pyflakes
# ("undefined name 'OUT_PATH'") immediately after the lazy conversion - the
# scripts would have died on their first run. So the lazy names exist for
# EXTERNAL readers and for monkeypatching, and everything in here resolves at
# the point of use.


def _out_path():
    return cio.repo_path("reconstruction_witness_queue.json")


# RESOLVED AT CALL TIME, not frozen at import - the other half of item 0BI's
# seam, and without it the conversion above is cosmetic. `cio.repo_path(...)`
# evaluated at module scope answers "where is the corpus" ONCE, at import, so a
# caller that sets the root afterwards (cio.set_corpus_root, which is what
# `--corpus` uses) changes nothing and gets no error - silently the old path.
# That is the exact defect corpus_io's own header warns about and the reason its
# constants became lazy; a module-level copy here reintroduces it one file over.
# Reading $SEFER_CORPUS_ROOT still worked, because the environment is read before
# import, which is why converting these scripts and testing them only that way
# looked like it had closed the seam.
#
# Same mechanism as corpus_io's: PEP 562 module __getattr__, so the NAMES stay
# exactly what they were for every reader and stay monkeypatchable (a
# setattr creates a real attribute, which shadows this hook).
def __getattr__(name):
    if name in _LAZY:
        return _LAZY[name]()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
norm = cio.hebrew_letters_only
FURNITURE = {"יד", "יר", "יך", "מלאכי", "כללי", "האלף", "הבית",
             "הגימל", "הדלת", "ההא", "Digitized", "by", "Google"}


def docai_tokens_for_page(page):
    toks = cio.load_docai_page(page, cio.DOCAI_DIR)
    if toks is None:
        raise FileNotFoundError(cio.docai_page_path(page, cio.DOCAI_DIR))
    return [t for t in toks if norm(t["text"])]


def build_mapping(klal_id, page):
    """Return dict: docai_token_index -> corpus_word_index for this page."""
    klalim_by_id, _ = rdata.load_klalim()
    k = klalim_by_id.get(klal_id)
    if not k:
        return {}
    corpus_words = cio.words_of(k)
    corpus_norm = [norm(w) for w in corpus_words]

    dtoks = docai_tokens_for_page(page)
    dwords = [norm(t["text"]) for t in dtoks]

    sm = difflib.SequenceMatcher(None, corpus_norm, dwords, autojunk=False)
    mapping = {}
    for corpus_start, dtok_start, size in sm.get_matching_blocks():
        for offset in range(size):
            mapping[dtok_start + offset] = corpus_start + offset
    return mapping


def main(argv=None):
    # THIS SCRIPT REWRITES A TRACKED FILE, AND USED TO DO IT ON ANY INVOCATION.
    # Recorded as a footgun 2026-09-01 and demonstrated twice on 2026-09-06, both
    # times by a `--help` run made to smoke-test an unrelated change: it
    # re-derived every index against the CURRENT corpus and nulled 6 of them
    # (klal 88 w310, w327 among them) because the corpus has shifted since the
    # queue was built. Both writes were reverted from git, which is the only
    # reason they cost nothing.
    #
    # corpus_io.detector_args' docstring already names this exact script as the
    # reason the six detectors got argument parsing ("had no argument parsing at
    # all and rewrote the witness queue when it was invoked with --help") - the
    # lesson was written down and never applied HERE, in the file it was about.
    # Now it is: --help exits before reading anything, and a write needs --apply.
    ap = argparse.ArgumentParser(
        description="Re-derive word_index for every row in the witness queue.")
    ap.add_argument("--apply", action="store_true",
                    help="write the re-derived indices back to "
                         "reconstruction_witness_queue.json (default: report only)")
    args = ap.parse_args(argv)

    with open(_out_path(), encoding="utf-8") as f:
        data = json.load(f)

    queue = data.get("queue", data) if isinstance(data, dict) else data
    if isinstance(data, dict):
        is_wrapped = True
    else:
        is_wrapped = False
        queue = data

    # Collect unique (klal_id, page) pairs
    pairs = {(w["klal_id"], w["page"]) for w in queue if w.get("page")}
    print(f"Computing word_index mappings for {len(pairs)} (klal, page) pairs:")

    mappings = {}
    for klal_id, page in sorted(pairs):
        mapping = build_mapping(klal_id, page)
        mappings[(klal_id, page)] = mapping
        covered = len(mapping)
        total_toks = len(docai_tokens_for_page(page))
        print(f"  klal={klal_id} page={page}: {covered}/{total_toks} tokens mapped")

    updated = 0
    for w in queue:
        page = w.get("page")
        klal_id = w.get("klal_id")
        ti = w.get("docai_token_index")
        if page is None or ti is None:
            w["word_index"] = None
            continue
        wi = mappings.get((klal_id, page), {}).get(ti)
        w["word_index"] = wi
        if wi is not None:
            updated += 1

    print(f"\nword_index set on {updated}/{len(queue)} items "
          f"({len(queue) - updated} unmapped → null)")

    if not args.apply:
        print("\nDRY RUN - nothing written. Re-run with --apply.\n"
              "(This tool rewrites a TRACKED file by re-deriving every index "
              "against the CURRENT corpus, so a run made for any other reason - "
              "including --help, before 2026-09-06 - silently degraded it.)")
        return

    with open(_out_path(), "w", encoding="utf-8") as f:
        if is_wrapped:
            json.dump(data, f, ensure_ascii=False, indent=2)
        else:
            json.dump(queue, f, ensure_ascii=False, indent=2)
    print(f"Wrote {_out_path()}")


if __name__ == "__main__":
    main()
