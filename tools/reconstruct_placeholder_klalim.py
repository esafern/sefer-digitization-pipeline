#!/usr/bin/env python3
"""Rebuild the text of klalim the chunker created but never filled.

115 of Klalei HaGemara's 667 klalim store nothing but a generated placeholder -
the gematria marker plus a synthesised "כלל N" title, e.g. `רנ כלל 250` - all of
them in klalim 223-667 (found 2026-08-25 by the Sefaria export, which would
otherwise have shipped them as text). They are real extraction gaps, not klalim
that are short in the source: page 247 prints klal 667's text in full.

The text is recoverable because the klal's own boundaries are already known. A
klal runs from its gematria marker to the next klal's marker, and
`build_gematria_trace.py` has located both for most of them - so the body is the
DocAI token stream between the two, in reading order.

WHAT THIS DOES NOT DO. It does not adjudicate, correct or normalise anything: it
lifts what Document AI read, exactly as read, between two known anchors. The
marker itself is taken from the CORPUS (the stored gematria), not from OCR,
because the numeral is frequently misread (klal 240's `רמ` comes back as `רם`)
and the corpus value is the one every citation address depends on.

Refuses rather than guesses. A span is skipped, with a reason, when:
  - either boundary is unknown (no marker position for this klal or the next)
  - the span is empty, or implausibly long for one klal
  - the reconstructed text overlaps a neighbour's stored text, which means a
    boundary is wrong and the neighbour would be duplicated

Usage:
  python3 tools/reconstruct_placeholder_klalim.py                # report only
  python3 tools/reconstruct_placeholder_klalim.py --apply        # write the corpus
  python3 tools/reconstruct_placeholder_klalim.py --out FILE     # save the report
"""
import argparse
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pipeline"))

import corpus_io as cio  # noqa: E402

sys.path.insert(0, os.path.join(REPO, "tools"))
from check_span_shortfall import FURNITURE_WORDS  # noqa: E402

PLACEHOLDER_RE = re.compile(r"^\S+\s+כלל\s+\d+\s*$")

# Lexical gates, CALIBRATED against the klalim that already have real text rather
# than picked by feel: both floors are the 2nd percentile of the real corpus, so
# a reconstruction is rejected only where it is worse than 98% of genuine klalim.
#
# Why two. Whole-text attestation catches a span that is broadly garbage, but it
# is diluted by length - klal 537's reconstruction opens with a scrambled run
# (`קולי יו ב"ש ביש פומפירוש`) and still scores 0.91 overall, better than the real
# median, because a thousand good words follow. The opening gate catches exactly
# that: 0.58 against a real-corpus 2nd percentile of 0.71. Neither gate can see a
# scramble buried mid-klal, which is why every reconstruction is reported and
# none is presented as reviewed text.
MIN_ATTESTED_OVERALL = 0.82
MIN_ATTESTED_OPENING = 0.71
OPENING_WORDS = 30
MIN_LETTERS_FOR_ATTESTATION = 4

# Page furniture, in the same vocabulary tools/check_span_shortfall.py already
# uses: the running header, its OCR variants, and the letter-section names.
# A span that crosses a page seam walks straight through the next page's header,
# and the first version of this tool carried it into 15 klalim - caught by
# tests/test_corpus_invariants.py::test_no_page_header_contamination, which is
# precisely why that invariant exists. Kept as one shared set rather than a
# private copy (the standing rule); imported below from the tool that owns it.
FURNITURE_RUN_MAX = 6      # a header is a short run; a long run of these is real text

# A klal longer than this is almost certainly two klalim run together by a bad
# boundary. The longest real klal in Part 1 is ~1,150 words.
MAX_PLAUSIBLE_WORDS = 1400
MIN_PLAUSIBLE_WORDS = 2


def is_placeholder(clean_text):
    return bool(PLACEHOLDER_RE.match(" ".join((clean_text or "").split())))


def attested_share(words, frequencies):
    """Share of substantial words that appear in the independent reference corpus.

    Short words are excluded: they are dominated by particles and abbreviations
    that are attested no matter how garbled their neighbours are, which flattens
    the signal exactly where it needs to be sharp."""
    forms = [cio.hebrew_letters_only(w) for w in words]
    forms = [w for w in forms if len(w) >= MIN_LETTERS_FOR_ATTESTATION]
    if not forms:
        return None
    return sum(1 for w in forms if frequencies.get(w, 0) > 0) / len(forms)


def load_reference_frequencies():
    path = cio.repo_path("sefaria_reference_corpus", "word_freq.json")
    data = cio.load_json(path)
    if not data:
        print("WARNING: sefaria_reference_corpus/word_freq.json is absent - the lexical "
              "gates are DISABLED and every located span will be accepted unchecked.")
        print("         See SETUP.md; this file is gitignored and migrated separately.")
        return {}
    return data


def load_traces():
    out = {}
    for part in (1, 2, 3):
        path = cio.repo_path(f"gematria_trace_part{part}.json")
        data = cio.load_json(path) or []
        rows = data if isinstance(data, list) else data.get("klalim", [])
        for row in rows:
            out[row["klal_id"]] = row
    return out


def page_words(page, cache):
    """Raw-array token texts for one scan page, cached.

    FIXED 2026-08-26 (code review). This returned the tokens re-sorted into
    READING ORDER and then sliced them with `marker_position` - which is an
    index into the RAW array, as build_gematria_trace states outright:
    "`marker_position` in the output is still the ARRAY index, because that is
    what every existing consumer indexes with". The two orders disagree on 23 of
    391 trace rows, and **6 of the 51 klalim this tool wrote on 2026-08-25 got a
    boundary from the wrong token** (287, 414, 443, 444, 487, 490).

    tools/check_span_shortfall.py::span_tokens_for already extracts this exact
    span, from the raw array, "so this explains that function's own number rather
    than a second opinion" - and this tool disagreeing with it meant the triage
    tool and the reconstruction tool described different spans for the same klal.
    """
    if page not in cache:
        cache[page] = [t["text"] for t in cio.load_docai_page(page)]
    return cache[page]


def reconstruct(klal_id, klal, traces, cache):
    """(text, note) - text is None when the span cannot be trusted."""
    here, nxt = traces.get(klal_id), traces.get(klal_id + 1)
    if not here or here.get("marker_position") is None or here.get("page") is None:
        return None, "no marker position for this klal"
    start_page, start = here["page"], here["marker_position"]
    words = page_words(start_page, cache)
    seam = None

    if nxt and nxt.get("page") == start_page and nxt.get("marker_position") is not None:
        body = words[start + 1:nxt["marker_position"]]
        note = f"page {start_page} tokens {start + 1}-{nxt['marker_position'] - 1}"
    elif nxt and nxt.get("page") == start_page + 1 and nxt.get("marker_position") is not None:
        # The klal crosses a page break: rest of this page plus the head of the next.
        tail = words[start + 1:]
        head = page_words(start_page + 1, cache)[:nxt["marker_position"]]
        seam = len(tail)
        body = tail + head
        note = (f"page {start_page} tokens {start + 1}-end + page {start_page + 1} "
                f"tokens 0-{nxt['marker_position'] - 1}")
    else:
        return None, "next klal's marker not located on this page or the next"

    body = [w for w in (t.strip() for t in body) if w]
    if seam is not None:
        # count furniture removed BEFORE the seam so the seam index still points
        # at the same word after stripping
        before = strip_page_furniture(body[:seam])
        after = strip_page_furniture(body[seam:])
        body = drop_seam_duplicate(before + after, len(before))
    else:
        body = strip_page_furniture(body)
    if len(body) < MIN_PLAUSIBLE_WORDS:
        return None, f"span holds only {len(body)} token(s)"
    if len(body) > MAX_PLAUSIBLE_WORDS:
        return None, f"span holds {len(body)} tokens - too long for one klal"
    return f"{klal['gematria']} " + " ".join(body), note


def strip_page_furniture(words):
    """Remove running-header runs, and the folio number that follows one.

    The header is `יד מלאכי כללי <letter-section>` (with OCR variants of the
    first word) followed by the printed folio, either as a Hebrew numeral or as
    Arabic digits. It appears mid-span only where the span crosses a page seam,
    so it is always a short contiguous run of furniture vocabulary - which is
    how this tells it from a klal that legitimately discusses `כללי הבית`."""
    out, i = [], 0
    while i < len(words):
        j = i
        while j < len(words) and cio.hebrew_letters_only(words[j]) in FURNITURE_WORDS:
            j += 1
        run = j - i
        if run >= 2 and run <= FURNITURE_RUN_MAX:
            # the folio number rides along with the header
            if j < len(words) and re.fullmatch(r"[\d\u05d0-\u05ea\"\'׳״]{1,5}", words[j] or ""):
                j += 1
            i = j
            continue
        out.append(words[i])
        i += 1
    return out


def drop_seam_duplicate(words, seam_index):
    """A word repeated across a page seam is the catchword, not the text.

    This print sets the next page's opening word at the foot of the current one;
    DocAI reads both, so a naive concatenation says it twice. Removes the
    repetition only AT the seam, where it is structural - a genuine repeated
    word elsewhere in the klal is left alone."""
    if seam_index is None or not (0 < seam_index < len(words)):
        return words
    if cio.hebrew_letters_only(words[seam_index - 1]) == cio.hebrew_letters_only(words[seam_index]):
        return words[:seam_index] + words[seam_index + 1:]
    return words


# The corpus's own invariants, applied here as REFUSAL GATES rather than as a
# cleanup target. The first version of this tool tried to scrub furniture out of
# a span and carried it into 15 klalim anyway; the second scrubbed better and
# still left one, plus eight duplicate-word pairs. Retuning a cleaner a third
# time is the signal to stop (Lesson 31): a reconstruction that would fail
# tests/test_corpus_invariants.py is simply not written, and is reported instead.
# Yield is the thing to sacrifice here - a klal left as a placeholder is honest,
# a klal filled with page furniture is corpus damage.
HEADER_CONTAMINATION_RE = re.compile(
    r"(?:י[דרך])\s+מלאכי|כללי\s+ה(?:אלף|בית|גימל|דלת|הא|וו|זין|חית|טית|יוד|כף|למד|"
    r"מם|נון|סמך|עין|פא|צדי|קוף|ריש|שין|תיו)")


def violates_corpus_invariants(text):
    """(reason, ...) - empty when the text is safe to write."""
    reasons = []
    if HEADER_CONTAMINATION_RE.search(text):
        reasons.append("carries page-header furniture")
    forms = [cio.hebrew_letters_only(w) for w in text.split()]
    dup = next((a for a, b in zip(forms, forms[1:]) if a and a == b), None)
    if dup:
        reasons.append(f"repeats a word consecutively ({dup!r})")
    return reasons


def overlaps_neighbour(text, neighbour):
    """True if this reconstruction swallows a neighbour's stored opening - the
    signature of a boundary landing in the wrong place."""
    if not neighbour or is_placeholder(neighbour.get("clean_text")):
        return False
    opening = " ".join((neighbour.get("clean_text") or "").split()[1:9])
    return bool(opening) and opening in text


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="write the reconstructions into the corpus")
    ap.add_argument("--no-flag", action="store_true",
                    help="skip recording a revisit flag per reconstructed klal (not recommended)")
    ap.add_argument("--out", default=None, help="write the full report as JSON")
    args = ap.parse_args()

    traces = load_traces()
    cache = {}
    files = {2: cio.repo_path("part2.json"), 3: cio.repo_path("part3.json")}
    loaded = {n: cio.load_klalim(p) for n, p in files.items()}
    by_id = {k["klal_id"]: k for ks in loaded.values() for k in ks}

    frequencies = load_reference_frequencies()
    filled, skipped = [], []
    for part, klalim in loaded.items():
        for klal in klalim:
            if not is_placeholder(klal.get("clean_text")):
                continue
            kid = klal["klal_id"]
            text, note = reconstruct(kid, klal, traces, cache)
            if text is None:
                skipped.append({"klal_id": kid, "reason": note})
                continue
            for neighbour in (by_id.get(kid - 1), by_id.get(kid + 1)):
                if overlaps_neighbour(text, neighbour):
                    text = None
                    skipped.append({"klal_id": kid,
                                    "reason": f"span swallows klal {neighbour['klal_id']}'s stored opening"})
                    break
            if text is None:
                continue
            body = text.split()[1:]
            overall = attested_share(body, frequencies) if frequencies else None
            opening = attested_share(body[:OPENING_WORDS], frequencies) if frequencies else None
            if overall is not None and overall < MIN_ATTESTED_OVERALL:
                skipped.append({"klal_id": kid,
                                "reason": f"text fails the lexical gate ({overall:.2f} attested)"})
                continue
            if opening is not None and len(body) >= 40 and opening < MIN_ATTESTED_OPENING:
                skipped.append({"klal_id": kid,
                                "reason": f"opening fails the lexical gate ({opening:.2f} attested)"})
                continue
            problems = violates_corpus_invariants(text)
            if problems:
                skipped.append({"klal_id": kid, "reason": "; ".join(problems)})
                continue
            filled.append({"klal_id": kid, "part": part, "words": len(body),
                           "source": note, "text": text,
                           "attested_overall": round(overall, 3) if overall is not None else None,
                           "attested_opening": round(opening, 3) if opening is not None else None})
            if args.apply:
                klal["clean_text"] = text

    print(f"placeholders reconstructed: {len(filled)}")
    print(f"skipped (boundary not trustworthy): {len(skipped)}")
    by_reason = {}
    for s in skipped:
        by_reason[s["reason"].split(" - ")[0]] = by_reason.get(s["reason"].split(" - ")[0], 0) + 1
    for reason, n in sorted(by_reason.items(), key=lambda x: -x[1]):
        print(f"    {n:>3}  {reason}")
    if filled:
        words = sorted(f["words"] for f in filled)
        print(f"reconstructed length: min {words[0]}, median {words[len(words)//2]}, max {words[-1]} words")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump({"filled": filled, "skipped": skipped}, f, ensure_ascii=False, indent=1)
        print(f"report -> {args.out}")

    if args.apply:
        for part, path in files.items():
            with open(path, "w", encoding="utf-8") as f:
                json.dump(loaded[part], f, ensure_ascii=False, indent=2)
        print("WROTE part2.json and part3.json - run ./rebuild_all.sh next")
        if not args.no_flag:
            # Every reconstructed klal is flagged for revisit, because that is
            # exactly what it is: text lifted from an OCR token stream between
            # two anchors, never read by a human and never adjudicated against
            # the scan. The lexical gates reject a span that is broadly wrong;
            # they cannot see a scramble buried inside an otherwise good klal
            # (klal 539 passes at 0.74 with a visibly interleaved opening). A
            # flag is the project's own way of saying "this needs eyes", and
            # leaving 51 klalim of unreviewed machine output in the corpus
            # unmarked would be the more dangerous half of that.
            import review_decisions as rd
            for item in filled:
                rd.append_decision(
                    "klal_flag",
                    klal_id=item["klal_id"],
                    word_index=None,
                    needs_revisit=True,
                    note=(f"Reconstructed 2026-08-25 from the DocAI token stream "
                          f"({item['source']}) because this klal stored only a placeholder. "
                          f"{item['words']} words, {item['attested_overall']:.2f} of substantial "
                          f"words attested in the independent reference corpus. NEVER READ BY A "
                          f"HUMAN and never adjudicated against the scan - the extraction is "
                          f"mechanical, the boundaries come from the gematria trace, and a "
                          f"scramble inside the body would not have been caught."),
                    reviewer="tools/reconstruct_placeholder_klalim.py",
                )
            print(f"recorded {len(filled)} revisit flags - these klalim are unreviewed machine output")
    else:
        print("(dry run - nothing written; pass --apply to write)")


if __name__ == "__main__":
    main()
