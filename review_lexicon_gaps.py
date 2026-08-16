#!/usr/bin/env python3
# [STANDALONE] Triage layer for validate_part1_corpus_integrity.py's check 5
# ("full-corpus lexicon coverage"). Check 5 reports every Part-1 word that is
# not in lexicon.txt - 951 distinct forms / 1104 occurrences as of 2026-08-16 -
# and its own docstring correctly calls that INFORMATIONAL, not a defect list:
# lexicon.txt is a ~19k-word list built from this corpus's own earlier OCR
# (archive/scripts/build_lexicon.py), so it was never going to cover a real
# author's full vocabulary, and "not in lexicon.txt" carries no evidence about
# whether a word is right or wrong. That is exactly why 951 uninvestigated
# words have sat there: the raw list is unreadable and nobody could tell which
# few of them are worth a scan check.
#
# This script does not decide anything. It attaches independent, cheap,
# no-LLM signals to each of the 951 so a human reads a short list instead of a
# long one, and it accounts for every one of the 951 in its output (`--json`)
# rather than printing a truncated "most interesting" sample - the standing
# concern in this project is items silently dropped from a report, not report
# length.
#
# THE FIVE SIGNALS, and what each is and is not evidence for:
#
#   1. SURFACE PUNCTUATION. check 5 compares `"".join(Hebrew letters only)`,
#      so `א"א` (eshet ish), `בא"א"ע`, `בפי'` all reach lexicon.txt as
#      `אא`/`באאע`/`בפי` - forms nothing would ever list. A word whose EVERY
#      surface occurrence carries a gershayim/geresh is a punctuation artifact
#      of the check, not a vocabulary gap. NOTE this is the same false-positive
#      class the dropped-lamed work already had to handle twice (the "~620
#      ambiguous" over-count, and the ad-hoc `אא`-prefix scan that pulled in 11
#      `אא"כ`), which is why it is checked FIRST here.
#   2. INDEPENDENT ATTESTATION. Frequency in sefaria_reference_corpus/ (Shulchan
#      Arukh + Talmud Bavli, 2,579,701 words, built 2026-08-16 by
#      validate_lexicon_independent.py, whose provenance check this script
#      reuses rather than reading the cache file directly - a stale table looks
#      byte-identical to a current one). This is the only signal here with no
#      lineage to this project's own OCR. Attestation says the form is a real
#      word of the language; it does NOT say it is the right word in this
#      sentence, and a corrupt form can be attested (7 of the 24 purged
#      dropped-lamed forms are - see PROJECT-STATUS.md 2026-08-16).
#   3. PREFIX-STRIPPED RESOLUTION. This print attaches ordinary proclitics
#      (ו/ב/ה/מ/כ/ל/ש/ד and 2-letter combinations) with no space. lexicon.txt
#      does not enumerate every inflected/prefixed form, so `ולכל` is absent
#      while `לכל` is present. Uses propose_abbreviation_expansions.
#      prefix_decompositions() (imported, not reimplemented - it carries the
#      longest-surviving-root ordering and the no-self-stacking guard that
#      2026-08-16's audit had to fix).
#   4. KNOWN-CORRUPTION SHAPE. Two checks, not one: (a) exact membership in the
#      24 confirmed dropped-lamed corrupt forms (expected to be zero - the 130
#      instances were fixed and a zero-tolerance test guards them - but
#      "expected zero" is checked here, not assumed); (b) the general SHAPE of
#      that bug, i.e. does inserting a ל after some א in this form yield a word
#      that is independently attested? The 2026-08-15 fix covered the specific
#      instances found, never a rule, so a form nobody enumerated can still
#      carry the same fingerprint. Scored against the INDEPENDENT table, not
#      this corpus's own frequencies, so the corpus is not validating itself.
#   5. SINGLE-EDIT NEIGHBOUR (added during this script's first use, after the
#      unresolved list turned out to be full of one-letter misreads: בכתיכת for
#      בכתיבת, בתלמור for בתלמוד, דנראח for דנראה, דברידם for דבריהם). Is the
#      form one substitution/deletion/insertion away from a word the independent
#      corpus uses regularly, while being unattested itself? A hit on a
#      letter pair this print's OCR is already known to confuse (CONFUSABLE_PAIRS)
#      is the strongest signal here. It is still only a hypothesis about the
#      ink - `להעיר` is one edit from `להעיד` and is simply a real word this
#      reference sample doesn't contain.
#
# BUCKETS. Every form gets exactly one, and the order is deliberate: the
# corruption-shape bucket is assigned FIRST, ahead of every benign explanation,
# because "there is a reason lexicon.txt wouldn't list this" is not evidence
# that the form is right. See bucket_for() for the two concrete cases that
# forced that ordering.
#
# The composite score is a READING ORDER, not a verdict (Lesson 2). It is
# deliberately additive and transparent: every point is printed with the word.
# Nothing here is a substitute for a scan check; textual triage cannot resolve
# a disputed reading, only decide which readings deserve one.
#
# KNOWN LIMITS:
#   - Attestation is a sample. 2.58M words of Talmud/Shulchan Arukh does not
#     contain every legitimate word Yad Malachi uses (medieval/early-modern
#     names and titles especially - the same long-tail effect that makes 31.8%
#     of lexicon.txt unattested). Zero attestation is a reason to read, not a
#     verdict of corruption.
#   - Prefix stripping tolerates a coincidence: stripping ו from a corrupt form
#     can land on a real word by accident. That is why a prefix hit lowers the
#     score rather than clearing the word outright, and why the corruption-shape
#     signal is scored independently of it.
#   - It cannot see a corrupt form that IS a real word (the whole dropped-lamed
#     class: every one of the 122 corrupt forms was in lexicon.txt, so check 5
#     never reported one). This script inherits that blind spot completely - it
#     only ever sees words check 5 already flagged. It is not a corpus sweep.
#
# Read-only: opens part1.json, lexicon.txt and the reference corpus, writes
# nothing except an optional --json report. Any real correction goes through
# review_decisions.py -> apply_reviewer_decisions.py, never this script.
#
# WHAT THE FIRST FULL READING PASS FOUND (2026-08-16, see PROJECT-STATUS.md):
# the reading list this produces is not noise. Reading the ocr_shape_to_read and
# unresolved buckets plus the zero-attestation half of prefix_resolved (377 of
# the 951 forms, every occurrence in context) yielded 109 candidates across 43
# klalim, recorded as klal_flag decisions - overwhelmingly single-letter misreads
# in a small set of pairs (ב/כ, ד/ר, ה/ח, ה/ד, ט/מ, ס/פ, ג/נ). Re-running this
# script after those are resolved should shrink those buckets, not the total.
#
# Usage: ./venv/bin/python review_lexicon_gaps.py [--json out.json] [--top N]
#        ./venv/bin/python review_lexicon_gaps.py --contexts --bucket unresolved
#          (every occurrence of the selected forms in its own klal's words -
#           the reading step; --min-score N narrows it further)
import argparse
import json
import os
from collections import Counter, defaultdict

import propose_abbreviation_expansions as abbrev
import validate_lexicon_independent as indep
import validate_part1_corpus_integrity as integrity

REPO = os.path.dirname(os.path.abspath(__file__))
PART1_PATH = os.path.join(REPO, "part1.json")

QUOTE_CHARS = abbrev.QUOTE_CHARS

# A form the independent corpus uses this often is ordinary vocabulary. Below
# it, attestation is weak enough to be a coincidence of a 2.58M-word sample
# (or the same corruption appearing in Sefaria's own text), so it lowers the
# score without clearing the word - cf. the 7 purged dropped-lamed forms that
# each have 1-48 independent occurrences and are still corrupt here.
MIN_STRONG_ATTESTATION = 25
# A prefix-stripped root has to be more than barely present to count as an
# explanation, for the same reason.
MIN_ROOT_ATTESTATION = 25
# A ל-insertion is only interesting if the resulting word is common enough that
# the print would plausibly contain it and this form is plausibly its damage.
MIN_LIGATURE_TARGET_ATTESTATION = 50


def load_part1():
    return json.load(open(PART1_PATH, encoding="utf-8"))


def clean_word(w):
    """Exactly check 5's normalisation - Hebrew letters only. Reproduced here
    (not imported) only because it is a closure inside check 5; kept in sync by
    reusing that module's own HEBREW_LETTERS constant."""
    return "".join(c for c in w if c in integrity.HEBREW_LETTERS)


def collect_unknown_forms(klalim, lexicon):
    """form -> {occurrences, klal_ids: Counter, surfaces: Counter, positions}.

    Reproduces check 5's selection exactly, plus the provenance check 5 throws
    away: which klal each occurrence is in, at which word index, and what the
    unnormalised token on the page actually looked like."""
    forms = defaultdict(lambda: {"occurrences": 0, "klal_ids": Counter(),
                                 "surfaces": Counter(), "positions": []})
    for k in klalim:
        for i, w in enumerate(k["clean_text"].split()):
            cw = clean_word(w)
            if not cw or cw in lexicon:
                continue
            rec = forms[cw]
            rec["occurrences"] += 1
            rec["klal_ids"][k["klal_id"]] += 1
            rec["surfaces"][w] += 1
            rec["positions"].append((k["klal_id"], i))
    return forms


def prefix_resolution(form, lexicon, freq):
    """Best (prefix, root, evidence) where stripping 1-2 proclitics lands on a
    word lexicon.txt knows or the independent corpus uses. Prefers a lexicon
    hit, then the most-attested root; ties broken by the longest root, which is
    prefix_decompositions()'s own ordering."""
    best = None
    for prefix, root in abbrev.prefix_decompositions(form):
        if len(root) < 2:
            continue  # a 1-letter "root" is not evidence of anything
        in_lex = root in lexicon
        attest = freq.get(root, 0)
        if not in_lex and attest < MIN_ROOT_ATTESTATION:
            continue
        rank = (1 if in_lex else 0, attest, len(root))
        if best is None or rank > best[0]:
            evidence = "lexicon" if in_lex else "independent"
            best = (rank, {"prefix": prefix, "root": root,
                           "evidence": evidence, "root_attestation": attest})
    return best[1] if best else None


def ligature_shape(form, freq):
    """Does inserting ל after some א in this form yield an independently
    attested word? The dropped-lamed fingerprint, scored against the
    independent table so this corpus is not validating itself. Returns the
    single best target, or None."""
    best = None
    for i, ch in enumerate(form):
        if ch != "א":
            continue
        candidate = form[: i + 1] + "ל" + form[i + 1:]
        n = freq.get(candidate, 0)
        if n >= MIN_LIGATURE_TARGET_ATTESTATION and (best is None or n > best[1]):
            best = (candidate, n)
    return {"target": best[0], "target_attestation": best[1]} if best else None


# Hebrew letter pairs this print's OCR actually confuses, read off the
# candidates this script's own first run surfaced (בכתיכת/בכתיבת, בתלמור/
# בתלמוד, דנראח/דנראה, דברידם/דבריהם) rather than from a general list of
# letters that look alike. Used only to LABEL an edit-1 neighbour as
# fingerprint-matching; the neighbour has to earn its place on attestation
# either way, so a confusion this list is missing costs a label, not a hit.
CONFUSABLE_PAIRS = {frozenset(p) for p in
                    [("ב", "כ"), ("ד", "ר"), ("ה", "ח"), ("ה", "ד"), ("ה", "ת"),
                     ("ג", "נ"), ("ו", "ז"), ("ו", "י"), ("ס", "ם"), ("נ", "ן"),
                     ("כ", "ן"), ("ר", "ת"), ("ט", "מ"), ("צ", "ע"), ("ף", "ץ")]}

MIN_NEIGHBOUR_ATTESTATION = 20


def near_attested(form, freq):
    """Is this form one edit (substitute/delete/insert one Hebrew letter) away
    from a word the INDEPENDENT corpus uses regularly, while being unattested
    itself? That is the classic shape of a single-letter OCR misread, and it is
    the signal that separates 'rare word this reference sample happens not to
    contain' from 'common word with one letter wrong'.

    Reports the best neighbour ONLY. This is a hypothesis to check against the
    scan, never a correction: an edit-1 neighbour is a guess about the ink, and
    Success Criterion 1 does not accept guesses. Several forms here have more
    than one plausible neighbour, which is itself a reason the human, not this
    script, decides."""
    if freq.get(form, 0):
        return None
    best = None
    letters = integrity.HEBREW_LETTERS
    variants = []
    for i in range(len(form)):
        for ch in letters:
            if ch != form[i]:
                variants.append((form[:i] + ch + form[i + 1:], "sub", form[i], ch))
        variants.append((form[:i] + form[i + 1:], "del", form[i], ""))
    for i in range(len(form) + 1):
        for ch in letters:
            variants.append((form[:i] + ch + form[i:], "ins", "", ch))
    for cand, kind, a, b in variants:
        n = freq.get(cand, 0)
        if n < MIN_NEIGHBOUR_ATTESTATION:
            continue
        confusable = kind == "sub" and frozenset((a, b)) in CONFUSABLE_PAIRS
        # Prefer a known-confusable substitution over a merely-more-frequent
        # neighbour: this print's failure mode is a misread letter, not a
        # random one-letter difference.
        rank = (1 if confusable else 0, n)
        if best is None or rank > best[0]:
            best = (rank, {"neighbour": cand, "edit": kind, "from": a, "to": b,
                           "neighbour_attestation": n, "known_confusable": confusable})
    return best[1] if best else None


def fused_split(form, freq):
    """Does this form split into two independently common words, while being
    unattested itself? The shape of the 2026-08-16 finding (`אלא`+`אמוראי`
    fused into `אאמוראי` after a dropped lamed ALSO lost the following space).

    Weak on its own - Hebrew is agglutinative enough that plenty of legitimate
    words split this way - so it is reported as a note and scored at 1 point,
    never as a resolution."""
    if len(form) < 5 or freq.get(form, 0):
        return None
    best = None
    for i in range(2, len(form) - 1):
        a, b = form[:i], form[i:]
        na, nb = freq.get(a, 0), freq.get(b, 0)
        if na >= 500 and nb >= 500 and (best is None or min(na, nb) > min(best[1], best[2])):
            best = (f"{a} + {b}", na, nb)
    return {"split": best[0], "left": best[1], "right": best[2]} if best else None


def analyse(form, rec, lexicon, freq):
    surfaces = list(rec["surfaces"])
    signals = {
        "form": form,
        "occurrences": rec["occurrences"],
        "klal_ids": sorted(rec["klal_ids"]),
        "positions": rec["positions"],  # (klal_id, word_index) - the coordinates a
                                        # klal_flag/manual_correction decision needs
        "surfaces": surfaces,
        "all_surfaces_quoted": all(any(c in QUOTE_CHARS for c in s) for s in surfaces),
        "independent_attestation": freq.get(form, 0),
        "prefix_resolution": prefix_resolution(form, lexicon, freq),
        "ligature_shape": ligature_shape(form, freq),
        "near_attested": near_attested(form, freq),
        "fused_split": fused_split(form, freq),
        "known_corrupt_form": form in indep.CORRUPT_TO_CORRECT,
    }
    # The corruption-shape flag that drives the reading list: this form is
    # unattested independently AND is one KNOWN-CONFUSABLE letter away from a
    # word the reference corpus uses regularly. Not a verdict - `להעיר` (a real
    # word, absent from a Talmud/Shulchan-Arukh sample) lands here next to
    # `וכתכ` (plainly `וכתב`) and only a context read separates them.
    signals["ocr_shape"] = bool(
        signals["near_attested"] and signals["near_attested"]["known_confusable"]
        and signals["independent_attestation"] == 0)
    signals["bucket"] = bucket_for(signals)
    signals["score"], signals["score_detail"] = score(signals)
    return signals


def bucket_for(s):
    """One bucket per word, assigned in evidence-strength order so the counts
    sum to exactly the number of flagged forms (no word in two buckets, none
    dropped).

    ORDER MATTERS AND WAS CORRECTED DURING THIS SCRIPT'S FIRST USE. The three
    "benign explanation" buckets (abbreviation / attested / prefix-resolved)
    originally outranked the corruption-shape signal, which buried real
    candidates behind an explanation that happened to also apply: `וכלבד` for
    `ובלבד` decomposes as ו+כ+לבד, so a spurious prefix hit "explained" a
    misread ב; `וחרמב"ם` for `והרמב"ם` carries a gershayim, so the abbreviation
    rule "explained" a misread ה. An explanation for why a form is missing from
    lexicon.txt is not evidence that the form is right, and the bucket order has
    to reflect that or the triage hides exactly what it was built to surface
    (Lesson 16's shape: a check that only looks at the edges of a category).
    """
    if s["ocr_shape"]:
        return "ocr_shape_to_read"
    # Punctuation is tested BEFORE the corrupt-form list on purpose. `א"א` and
    # `א"ה` normalise to `אא`/`אה`, which ARE two of the 24 confirmed corrupt
    # forms - but only as an artifact of check 5 stripping the gershayim, and
    # calling them corrupt would repeat the exact false positive the
    # dropped-lamed work had to back out twice. main() reports the overlap
    # explicitly rather than letting the ordering hide it.
    if s["all_surfaces_quoted"]:
        return "abbreviation_artifact"
    if s["known_corrupt_form"]:
        return "known_corrupt_form"
    if s["independent_attestation"] >= MIN_STRONG_ATTESTATION:
        return "independently_attested"
    if s["prefix_resolution"]:
        return "prefix_resolved"
    if s["independent_attestation"] > 0:
        return "weakly_attested"
    return "unresolved"


def score(s):
    """Additive reading-order score. Every component is printed with the word so
    a reader can disagree with the arithmetic rather than the conclusion."""
    detail = []
    total = 0
    if s["known_corrupt_form"]:
        total += 10
        detail.append("+10 exact known-corrupt dropped-lamed form")
    if s["independent_attestation"] == 0:
        total += 3
        detail.append("+3 zero independent attestation")
    elif s["independent_attestation"] < MIN_STRONG_ATTESTATION:
        total += 1
        detail.append(f"+1 weak independent attestation ({s['independent_attestation']}x)")
    if not s["prefix_resolution"]:
        total += 2
        detail.append("+2 no prefix-stripped resolution")
    if s["occurrences"] == 1:
        total += 1
        detail.append("+1 hapax in Part 1")
    if s["ligature_shape"]:
        total += 3
        detail.append(f"+3 dropped-lamed shape -> {s['ligature_shape']['target']} "
                      f"({s['ligature_shape']['target_attestation']}x independent)")
    na = s["near_attested"]
    if na:
        total += 3 if na["known_confusable"] else 2
        detail.append(f"+{3 if na['known_confusable'] else 2} one edit from "
                      f"{na['neighbour']} ({na['neighbour_attestation']}x independent, "
                      f"{na['edit']} {na['from']}->{na['to']}"
                      + (", known OCR confusion)" if na["known_confusable"] else ")"))
    if s["fused_split"]:
        total += 1
        detail.append(f"+1 splits into two common words: {s['fused_split']['split']}")
    if len(s["form"]) >= 9:
        total += 1
        detail.append(f"+1 unusually long token ({len(s['form'])} letters)")
    if s["all_surfaces_quoted"]:
        total -= 4
        detail.append("-4 every occurrence carries gershayim/geresh "
                      "(abbreviation, not a vocabulary gap)")
    return total, detail


CONTEXT_WORDS = 7  # words either side; enough to see the clause, per Lesson 16
                   # (read the surrounding text, don't judge a token in isolation)


def print_contexts(results, klalim, buckets, min_score):
    """Every occurrence of the selected forms, in its own klal's own words.

    This is the step no score can replace: a form is only judgeable against the
    sentence it sits in. The klal text here is `clean_text` verbatim, so what is
    printed is exactly what the corpus holds - not a reconstruction."""
    text_by_id = {k["klal_id"]: k["clean_text"].split() for k in klalim}
    selected = [r for r in results
                if (not buckets or r["bucket"] in buckets) and r["score"] >= min_score]
    print(f"\n--- Contexts for {len(selected)} form(s) "
          f"(buckets={','.join(buckets) or 'all'}, score>={min_score}) ---")
    for r in selected:
        print(f"\n[{r['score']}] {r['form']}  ({r['occurrences']}x) bucket={r['bucket']} "
              f"attest={r['independent_attestation']}"
              + (f" near={r['near_attested']['neighbour']}"
                 f"({r['near_attested']['neighbour_attestation']}x)" if r["near_attested"] else ""))
        for klal_id, i in r["positions"]:
            words = text_by_id[klal_id]
            lo, hi = max(0, i - CONTEXT_WORDS), min(len(words), i + CONTEXT_WORDS + 1)
            before = " ".join(words[lo:i])
            after = " ".join(words[i + 1:hi])
            print(f"   klal {klal_id} w{i}: {before}  >>{words[i]}<<  {after}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="write the full per-word report (ALL flagged forms)")
    ap.add_argument("--top", type=int, default=40,
                    help="how many highest-score words to print individually")
    ap.add_argument("--contexts", action="store_true",
                    help="print every occurrence of the selected forms in context")
    ap.add_argument("--bucket", action="append", default=[],
                    help="restrict --contexts to a bucket (repeatable)")
    ap.add_argument("--min-score", type=int, default=0,
                    help="restrict --contexts to forms at or above this score")
    args = ap.parse_args()

    klalim = load_part1()
    lexicon = set(w.strip() for w in open(integrity.LEXICON_PATH, encoding="utf-8") if w.strip())
    # Goes through validate_lexicon_independent's own provenance check, which
    # rebuilds the table if it was built by an older extractor or a different
    # set of books - do not read word_freq.json directly.
    freq = indep.build_or_load_frequency_table()
    print(f"Independent reference corpus: {sum(freq.values())} words, "
          f"{len(freq)} unique forms.")

    forms = collect_unknown_forms(klalim, lexicon)
    total_words = sum(len(k["clean_text"].split()) for k in klalim)
    results = [analyse(f, rec, lexicon, freq) for f, rec in forms.items()]
    results.sort(key=lambda r: (-r["score"], -r["occurrences"], r["form"]))

    print(f"Part 1: {len(klalim)} klalim, {total_words} words, "
          f"{len(results)} distinct not-in-lexicon forms "
          f"({sum(r['occurrences'] for r in results)} occurrences).\n")

    # Signal 4a, reported as its own line because "expected zero" is a claim
    # that has to be checked. Any hit whose surfaces are all gershayim-bearing
    # is a normalisation artifact, not a survivor of the 2026-08-15 fix.
    corrupt_hits = [r for r in results if r["known_corrupt_form"]]
    genuine = [r for r in corrupt_hits if not r["all_surfaces_quoted"]]
    print(f"\nKnown dropped-lamed corrupt forms still present in Part 1: "
          f"{len(genuine)} genuine, {len(corrupt_hits) - len(genuine)} "
          f"gershayim-stripped artifact(s)"
          + (f" ({', '.join(r['form'] + '<-' + '/'.join(r['surfaces']) for r in corrupt_hits)})"
             if corrupt_hits else ""))

    print("\n--- Triage buckets (one bucket per form; counts sum to the total) ---")
    by_bucket = Counter(r["bucket"] for r in results)
    for name in ("ocr_shape_to_read", "abbreviation_artifact", "known_corrupt_form",
                 "independently_attested", "prefix_resolved", "weakly_attested",
                 "unresolved"):
        n = by_bucket.get(name, 0)
        occ = sum(r["occurrences"] for r in results if r["bucket"] == name)
        print(f"  {name:24s} {n:5d} form(s)  {occ:5d} occurrence(s)")
    print(f"  {'TOTAL':24s} {sum(by_bucket.values()):5d} form(s)  "
          f"{sum(r['occurrences'] for r in results):5d} occurrence(s)")

    print(f"\n--- Highest-suspicion forms (top {args.top} by score; "
          f"score is a reading order, not a verdict) ---")
    for r in results[: args.top]:
        klalim_str = ",".join(str(k) for k in r["klal_ids"])
        print(f"  [{r['score']:3d}] {r['form']}  ({r['occurrences']}x, klal {klalim_str}) "
              f"surfaces={'/'.join(r['surfaces'])} bucket={r['bucket']}")
        for d in r["score_detail"]:
            print(f"          {d}")

    if args.contexts:
        print_contexts(results, klalim, args.bucket, args.min_score)

    if args.json:
        json.dump({"generated_from": "part1.json",
                   "part1_total_words": total_words,
                   "independent_corpus_words": sum(freq.values()),
                   "buckets": dict(by_bucket),
                   "forms": results},
                  open(args.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"\nFull report ({len(results)} forms, all of them) -> {args.json}")


if __name__ == "__main__":
    main()
