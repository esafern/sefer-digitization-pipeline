#!/usr/bin/env python3
"""Export the reviewed Yad Malachi corpus in multiple archival formats.

Reads part1.json (the hand-edited source of truth), applies all current human
review decisions (candidate_choice + manual_correction) from review_decisions.jsonl
in exactly the same way apply_reviewer_decisions.py would, and writes the result
in the requested format.

Supported formats:
  plain   - plain UTF-8 text, one klal per file or concatenated in one file
  alto    - ALTO XML v4 (one file per page, word-level bboxes where available)
  page    - PAGE XML 2019 (one file per page, word-level bboxes where available)
  tei     - TEI P5 XML (one file for all, or one per klal with --by-klal)
  sefaria - Sefaria ingest pair: index.json (schema) + version_hebrew.json (text)

Scope: every format defaults to part1.json (klalim 1-222), the reviewed third.
`--all-parts` loads all three part files - klalim 1-667, the whole of Klalei
HaGemara - and is the DEFAULT for the sefaria format, which is a whole-work
deliverable rather than a review artifact. Human decisions are applied by
klal_id either way; klalim with no decisions pass through unchanged.

Usage:
  python3 tools/export_corpus.py --format {plain,alto,page,tei,sefaria} \\
      --output-dir OUTPUT_DIR [--by-klal] [--klal-id KLAL_ID] [--all-parts]
"""
import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Bootstrap: this file lives in tools/, one level below the repo root.
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pipeline"))

import apply_reviewer_decisions as ard
import corpus_io as cio
import review_decisions as rd


# ---------------------------------------------------------------------------
# Decision application (delegates to apply_reviewer_decisions.py logic, read-only)
# ---------------------------------------------------------------------------

def _apply_decisions_to_klalim(klalim):
    """Return a new list of klal dicts with clean_text updated to reflect all
    current human review decisions. Does not touch any files; pure in-memory.

    Replicates the logic from apply_reviewer_decisions.py exactly, including:
    - candidate_choice decisions (replace / insert / delete opcodes)
    - manual_correction decisions (word-level replacements and deletions)
    - The confirmed-no-op detection (chosen_text == snapshot final_text)
    - The one-word-count-change-per-klal guard (not strictly needed here since
      we process all decisions in one pass and don't loop, but kept for parity)

    Decisions that would be skipped by the apply script (drift, missing klal)
    are silently skipped here too — the export reflects the text as it would
    appear after a clean apply, not the raw part1.json.
    """
    import copy
    klalim = copy.deepcopy(klalim)

    # Normalize whitespace (same as apply_reviewer_decisions.py line 213).
    for k in klalim:
        k["clean_text"] = " ".join(k["clean_text"].split())

    by_klal = {k["klal_id"]: k for k in klalim}
    corrections = cio.load_json(os.path.join(REPO, "corrections_part1.json")) or {}
    decisions = rd.all_current("candidate_choice")
    manual_decisions = rd.all_current("manual_correction")
    already_applied = rd.applied_decision_ids()
    word_count_changed_klalim = set()

    # -- candidate_choice decisions --
    for (klal_id, word_index), decision in sorted(decisions.items()):
        if decision["id"] in already_applied:
            continue
        live_list = corrections.get(str(klal_id), [])
        live_entry = next((c for c in live_list if c["word_index"] == word_index), None)
        snapshot = decision.get("candidate_snapshot")
        if not _snapshot_matches(snapshot, live_entry):
            continue
        opcode = snapshot["opcode"]
        klal = by_klal.get(klal_id)
        if klal is None:
            continue

        if opcode in ("replace", "insert") and decision["chosen_text"] == snapshot.get("final_text"):
            # confirmed no-op
            continue

        if opcode == "replace":
            new_text = _apply_replace(klal["clean_text"], word_index,
                                      snapshot.get("final_text"), decision["chosen_text"])
            if new_text is not None:
                klal["clean_text"] = new_text

        elif opcode in ("insert", "delete"):
            if klal_id in word_count_changed_klalim:
                continue
            if opcode == "insert":
                new_text = _apply_insert_removal(klal["clean_text"], word_index,
                                                 snapshot.get("final_text"))
            else:
                new_text = _apply_delete_insertion(klal["clean_text"], word_index,
                                                   decision["chosen_text"])
            if new_text is not None:
                klal["clean_text"] = new_text
                word_count_changed_klalim.add(klal_id)

    # -- manual_correction decisions --
    for (klal_id, word_index), decision in sorted(manual_decisions.items()):
        if decision["id"] in already_applied:
            continue
        klal = by_klal.get(klal_id)
        if klal is None:
            continue
        original_word = decision.get("candidate_snapshot", {}).get("original_word")
        chosen_text = decision["chosen_text"]

        # PARITY with apply_reviewer_decisions.py, which has three manual cases,
        # not two. FIXED 2026-08-27 (audit finding, verified): this file handled
        # delete and replace but not the reviewer-initiated INSERT
        # (original_word is None, chosen_text non-empty), so such a decision was
        # silently dropped from the export while the apply script wrote it into
        # part1.json - the deliverable and the corpus disagreeing.
        #
        # Latent rather than live when found: the two existing inserts (klal 9
        # w23, klal 16 w163) are already APPLIED, and applied decisions are
        # skipped above because part1.json already carries their text. The gap
        # only opens in the window between recording an insert and applying it -
        # which is exactly the window an export is most likely to be taken in.
        if original_word is None and chosen_text:
            if klal_id in word_count_changed_klalim:
                continue
            new_text = ard.apply_delete_insertion(klal["clean_text"], word_index, chosen_text)
            if new_text is not None:
                klal["clean_text"] = new_text
                word_count_changed_klalim.add(klal_id)
        elif chosen_text == "":
            if klal_id in word_count_changed_klalim:
                continue
            new_text = _apply_manual_deletion(klal["clean_text"], word_index, original_word)
            if new_text is not None:
                klal["clean_text"] = new_text
                word_count_changed_klalim.add(klal_id)
        else:
            # A multi-word REPLACEMENT (`ב"ד` -> `בית דין`) re-joins into a
            # LONGER word list and shifts every later index in the klal, so it
            # takes the same one-per-klal-per-run gate as the insert and delete
            # branches directly above. Uses the canonical predicate rather than
            # a local `len(chosen_text.split()) > 1` - this file's whole
            # contract is "replicates apply_reviewer_decisions.py exactly", and
            # a second copy of the rule is how the two drifted in the first
            # place (Lesson 13).
            #
            # FIXED 2026-08-31 (re-sweep). CODE-REVIEW-2026-08-27.md's remedy #2
            # says the guard belongs "in both apply_reviewer_decisions.py and
            # tools/export_corpus.py". It landed only in the first; this branch
            # kept calling _apply_manual_correction with no word-count check
            # while its own two siblings guarded - Lesson 34, where the sibling
            # was named in the finding text itself.
            # The gate applies to EVERY manual replace, not only the multi-word
            # ones: a same-count replace shifts nothing itself, but its index
            # may already have been shifted by an earlier decision this run,
            # and the drift check is blind to that when the shifted-into
            # position holds the same word (a repeated word). See the longer
            # note at apply_reviewer_decisions.py's matching branch - this file
            # exists to mirror that one exactly, and the mirror is the point.
            if klal_id in word_count_changed_klalim:
                continue
            new_text = _apply_manual_correction(klal["clean_text"], word_index,
                                                original_word, chosen_text)
            if new_text is not None:
                klal["clean_text"] = new_text
                if ard.manual_correction_changes_word_count(chosen_text):
                    word_count_changed_klalim.add(klal_id)

    return klalim


_snapshot_matches = ard.snapshot_matches
_apply_replace = ard.apply_replace
_apply_manual_correction = ard.apply_manual_correction
_apply_manual_deletion = ard.apply_manual_deletion
_apply_insert_removal = ard.apply_insert_removal
_apply_delete_insertion = ard.apply_delete_insertion


# ---------------------------------------------------------------------------
# Bbox helpers
# ---------------------------------------------------------------------------

def _load_word_bboxes():
    """Return {klal_id: {word_index: bbox_dict}} from corrections_part1.json.

    Only flagged (candidate) words have individual bboxes in this pipeline.
    """
    raw = cio.load_json(os.path.join(REPO, "corrections_part1.json")) or {}
    out = {}
    for klal_id_str, entries in raw.items():
        klal_id = int(klal_id_str)
        out[klal_id] = {}
        for entry in entries:
            wi = entry.get("word_index")
            bbox = entry.get("bbox")
            if wi is not None and bbox:
                out[klal_id][wi] = bbox
    return out


def _load_klal_regions():
    """Return {klal_id: {page, bbox}} from klal_page_regions.json."""
    raw = cio.load_json(os.path.join(REPO, "klal_page_regions.json")) or {}
    out = {}
    for klal_id_str, info in raw.items():
        out[int(klal_id_str)] = info
    return out


def _bbox_pixels(bbox, img_w=1.0, img_h=1.0):
    """Convert normalised [0,1] bbox to integer pixel coords.

    When image dimensions are unknown (default 1.0) returns normalised floats.
    For ALTO/PAGE we use the normalised values scaled to a nominal 10000-unit
    coordinate space so the output is integer-safe without needing real dims.
    """
    scale = 10000
    x = int(bbox["x1"] * scale)
    y = int(bbox["y1"] * scale)
    w = int((bbox["x2"] - bbox["x1"]) * scale)
    h = int((bbox["y2"] - bbox["y1"]) * scale)
    return x, y, w, h


# ---------------------------------------------------------------------------
# Plain text export
# ---------------------------------------------------------------------------

def export_plain(klalim, output_dir, by_klal=False):
    os.makedirs(output_dir, exist_ok=True)
    if by_klal:
        for k in klalim:
            path = os.path.join(output_dir, f"klal_{k['klal_id']:03d}.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"[כלל {k['gematria']}] {k.get('title', '')}\n\n")
                f.write(k["clean_text"])
                f.write("\n")
        return len(klalim)
    else:
        path = os.path.join(output_dir, "corpus.txt")
        with open(path, "w", encoding="utf-8") as f:
            for k in klalim:
                f.write(f"[כלל {k['gematria']}] {k.get('title', '')}\n\n")
                f.write(k["clean_text"])
                f.write("\n\n")
        return 1


# ---------------------------------------------------------------------------
# ALTO XML export
# ---------------------------------------------------------------------------

ALTO_NS = "http://www.loc.gov/standards/alto/ns-v4#"
ALTO_SCHEMA = "http://www.loc.gov/standards/alto/alto-4-4.xsd"

PAGE_W = 10000  # nominal coordinate space


def _alto_for_page(page_num, klalim_on_page, word_bboxes, klal_regions):
    """Build an ALTO XML ElementTree for one page."""
    ET.register_namespace("", ALTO_NS)
    ET.register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")
    root = ET.Element(f"{{{ALTO_NS}}}alto")
    root.set("{http://www.w3.org/2001/XMLSchema-instance}schemaLocation",
             f"{ALTO_NS} {ALTO_SCHEMA}")

    # Description block
    desc = ET.SubElement(root, f"{{{ALTO_NS}}}Description")
    mm = ET.SubElement(desc, f"{{{ALTO_NS}}}MeasurementUnit")
    mm.text = "pixel"
    src = ET.SubElement(desc, f"{{{ALTO_NS}}}sourceImageInformation")
    fn = ET.SubElement(src, f"{{{ALTO_NS}}}fileName")
    fn.text = f"page_{page_num}.png"

    # Layout
    layout = ET.SubElement(root, f"{{{ALTO_NS}}}Layout")
    page_el = ET.SubElement(layout, f"{{{ALTO_NS}}}Page")
    page_el.set("ID", f"P{page_num}")
    page_el.set("PHYSICAL_IMG_NR", str(page_num))
    page_el.set("WIDTH", str(PAGE_W))
    page_el.set("HEIGHT", str(PAGE_W))  # square nominal

    print_space = ET.SubElement(page_el, f"{{{ALTO_NS}}}PrintSpace")
    print_space.set("HPOS", "0")
    print_space.set("VPOS", "0")
    print_space.set("WIDTH", str(PAGE_W))
    print_space.set("HEIGHT", str(PAGE_W))

    for klal in klalim_on_page:
        kid = klal["klal_id"]
        region = klal_regions.get(kid, {})
        region_bbox = region.get("bbox", {})

        if region_bbox:
            rx, ry, rw, rh = _bbox_pixels(region_bbox)
        else:
            rx, ry, rw, rh = 0, 0, PAGE_W, PAGE_W

        block = ET.SubElement(print_space, f"{{{ALTO_NS}}}TextBlock")
        block.set("ID", f"TB_k{kid}")
        block.set("HPOS", str(rx))
        block.set("VPOS", str(ry))
        block.set("WIDTH", str(rw))
        block.set("HEIGHT", str(rh))

        # One TextLine per klal (no line segmentation available)
        line = ET.SubElement(block, f"{{{ALTO_NS}}}TextLine")
        line.set("ID", f"TL_k{kid}")
        line.set("HPOS", str(rx))
        line.set("VPOS", str(ry))
        line.set("WIDTH", str(rw))
        line.set("HEIGHT", str(rh))

        words = klal["clean_text"].split()
        kid_bboxes = word_bboxes.get(kid, {})
        for wi, word in enumerate(words):
            s = ET.SubElement(line, f"{{{ALTO_NS}}}String")
            s.set("ID", f"W_k{kid}_w{wi}")
            s.set("CONTENT", word)
            if wi in kid_bboxes:
                wx, wy, ww, wh = _bbox_pixels(kid_bboxes[wi])
                s.set("HPOS", str(wx))
                s.set("VPOS", str(wy))
                s.set("WIDTH", str(ww))
                s.set("HEIGHT", str(wh))
            else:
                # Fallback: use klal region bbox
                s.set("HPOS", str(rx))
                s.set("VPOS", str(ry))
                s.set("WIDTH", str(rw))
                s.set("HEIGHT", str(rh))

    return ET.ElementTree(root)


def export_alto(klalim, output_dir, klal_regions, word_bboxes):
    os.makedirs(output_dir, exist_ok=True)
    # Group klalim by page
    by_page = {}
    for k in klalim:
        page = k.get("page") or klal_regions.get(k["klal_id"], {}).get("page")
        if page is None:
            page = 0
        by_page.setdefault(page, []).append(k)

    files_written = 0
    for page_num, page_klalim in sorted(by_page.items()):
        tree = _alto_for_page(page_num, page_klalim, word_bboxes, klal_regions)
        path = os.path.join(output_dir, f"page_{page_num:04d}.xml")
        _write_pretty_xml(tree, path)
        files_written += 1
    return files_written


# ---------------------------------------------------------------------------
# PAGE XML export
# ---------------------------------------------------------------------------

PAGE_NS = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"
PAGE_SCHEMA = "https://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15/pagecontent.xsd"


def _points_from_bbox(bbox):
    """Convert a normalised bbox to a PAGE XML 'points' string in nominal coords."""
    x1, y1 = int(bbox["x1"] * PAGE_W), int(bbox["y1"] * PAGE_W)
    x2, y2 = int(bbox["x2"] * PAGE_W), int(bbox["y2"] * PAGE_W)
    return f"{x1},{y1} {x2},{y1} {x2},{y2} {x1},{y2}"


def _page_xml_for_page(page_num, klalim_on_page, word_bboxes, klal_regions):
    ET.register_namespace("", PAGE_NS)
    ET.register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")
    root = ET.Element(f"{{{PAGE_NS}}}PcGts")
    root.set("{http://www.w3.org/2001/XMLSchema-instance}schemaLocation",
             f"{PAGE_NS} {PAGE_SCHEMA}")

    N = PAGE_NS  # shorthand

    meta = ET.SubElement(root, f"{{{N}}}Metadata")
    creator = ET.SubElement(meta, f"{{{N}}}Creator")
    creator.text = "sefer-digitization-pipeline export_corpus.py"

    page_el = ET.SubElement(root, f"{{{N}}}Page")
    page_el.set("imageFilename", f"page_{page_num}.png")
    page_el.set("imageWidth", str(PAGE_W))
    page_el.set("imageHeight", str(PAGE_W))

    for klal in klalim_on_page:
        kid = klal["klal_id"]
        region_info = klal_regions.get(kid, {})
        region_bbox = region_info.get("bbox")

        region = ET.SubElement(page_el, f"{{{N}}}TextRegion")
        region.set("id", f"r_k{kid}")
        region.set("custom", f"klal_id:{kid}")

        if region_bbox:
            coords = ET.SubElement(region, f"{{{N}}}Coords")
            coords.set("points", _points_from_bbox(region_bbox))
        else:
            coords = ET.SubElement(region, f"{{{N}}}Coords")
            coords.set("points", f"0,0 {PAGE_W},0 {PAGE_W},{PAGE_W} 0,{PAGE_W}")

        # One TextLine per klal (no line segmentation)
        line = ET.SubElement(region, f"{{{N}}}TextLine")
        line.set("id", f"l_k{kid}")
        if region_bbox:
            lc = ET.SubElement(line, f"{{{N}}}Coords")
            lc.set("points", _points_from_bbox(region_bbox))
        else:
            lc = ET.SubElement(line, f"{{{N}}}Coords")
            lc.set("points", f"0,0 {PAGE_W},0 {PAGE_W},{PAGE_W} 0,{PAGE_W}")

        # Word elements
        words = klal["clean_text"].split()
        kid_bboxes = word_bboxes.get(kid, {})
        for wi, word in enumerate(words):
            word_el = ET.SubElement(line, f"{{{N}}}Word")
            word_el.set("id", f"w_k{kid}_{wi}")
            wc = ET.SubElement(word_el, f"{{{N}}}Coords")
            if wi in kid_bboxes:
                wc.set("points", _points_from_bbox(kid_bboxes[wi]))
            elif region_bbox:
                wc.set("points", _points_from_bbox(region_bbox))
            else:
                wc.set("points", f"0,0 {PAGE_W},0 {PAGE_W},{PAGE_W} 0,{PAGE_W}")
            ug = ET.SubElement(word_el, f"{{{N}}}TextEquiv")
            uv = ET.SubElement(ug, f"{{{N}}}Unicode")
            uv.text = word

        # Full TextEquiv for the line
        te = ET.SubElement(line, f"{{{N}}}TextEquiv")
        uv = ET.SubElement(te, f"{{{N}}}Unicode")
        uv.text = klal["clean_text"]

        # Full TextEquiv for the region
        rte = ET.SubElement(region, f"{{{N}}}TextEquiv")
        ruv = ET.SubElement(rte, f"{{{N}}}Unicode")
        ruv.text = klal["clean_text"]

    return ET.ElementTree(root)


def export_page(klalim, output_dir, klal_regions, word_bboxes):
    os.makedirs(output_dir, exist_ok=True)
    by_page = {}
    for k in klalim:
        page = k.get("page") or klal_regions.get(k["klal_id"], {}).get("page")
        if page is None:
            page = 0
        by_page.setdefault(page, []).append(k)

    files_written = 0
    for page_num, page_klalim in sorted(by_page.items()):
        tree = _page_xml_for_page(page_num, page_klalim, word_bboxes, klal_regions)
        path = os.path.join(output_dir, f"page_{page_num:04d}.xml")
        _write_pretty_xml(tree, path)
        files_written += 1
    return files_written


# ---------------------------------------------------------------------------
# TEI XML export
# ---------------------------------------------------------------------------

TEI_NS = "http://www.tei-c.org/ns/1.0"


def _build_tei(klalim, word_bboxes, all_corrections, all_manual):
    """Build a single TEI document for all klalim.

    Words that were corrected by the reviewer appear as:
      <choice><orig>ORIGINAL</orig><reg>CORRECTION</reg></choice>

    For candidate_choice decisions the original is snapshot["final_text"]
    (the pre-correction corpus text) and the reg is chosen_text.
    For manual_correction the original is snapshot["original_word"] and
    the reg is chosen_text.

    Already-applied decisions are excluded (they are already baked into
    clean_text via _apply_decisions_to_klalim).
    """
    ET.register_namespace("", TEI_NS)
    root = ET.Element(f"{{{TEI_NS}}}TEI")

    # --- teiHeader ---
    header = ET.SubElement(root, f"{{{TEI_NS}}}teiHeader")
    fd = ET.SubElement(header, f"{{{TEI_NS}}}fileDesc")
    tt = ET.SubElement(fd, f"{{{TEI_NS}}}titleStmt")
    title = ET.SubElement(tt, f"{{{TEI_NS}}}title")
    title.text = "יד מלאכי — Yad Malachi (Berlin 1851/2, Part 1)"
    pubstmt = ET.SubElement(fd, f"{{{TEI_NS}}}publicationStmt")
    p = ET.SubElement(pubstmt, f"{{{TEI_NS}}}p")
    p.text = "Digitization pipeline export. Human-reviewed corrections applied."
    srcstmt = ET.SubElement(fd, f"{{{TEI_NS}}}sourceDesc")
    sp = ET.SubElement(srcstmt, f"{{{TEI_NS}}}p")
    sp.text = "Berlin 1851/2 printing (Zittenfeld); scan via Google Books / NLI."

    # --- text body ---
    text = ET.SubElement(root, f"{{{TEI_NS}}}text")
    body = ET.SubElement(text, f"{{{TEI_NS}}}body")

    already_applied = rd.applied_decision_ids()

    # Build per-klal word-level correction maps (word_index -> (orig, reg))
    # for decisions NOT yet in part1.json (still pending)
    corrections_raw = cio.load_json(os.path.join(REPO, "corrections_part1.json")) or {}

    for klal in klalim:
        kid = klal["klal_id"]
        div = ET.SubElement(body, f"{{{TEI_NS}}}div")
        div.set("type", "klal")
        div.set("n", str(klal["gematria"]))
        div.set("xml:id", f"klal{kid}")

        head = ET.SubElement(div, f"{{{TEI_NS}}}head")
        head.text = klal.get("title", "")

        p_el = ET.SubElement(div, f"{{{TEI_NS}}}p")

        words = klal["clean_text"].split()

        # Build choice map: word_index -> (orig_text, reg_text)
        # These represent corrections visible to a reader (pending decisions)
        choice_map = {}
        candidate_decisions = all_corrections
        manual_decisions_map = all_manual

        for (d_klal, d_wi), dec in candidate_decisions.items():
            if d_klal != kid:
                continue
            if dec["id"] in already_applied:
                continue
            snap = dec.get("candidate_snapshot", {})
            orig = snap.get("final_text", "")
            reg = dec.get("chosen_text", "")
            if orig != reg:
                choice_map[d_wi] = (orig, reg)

        for (d_klal, d_wi), dec in manual_decisions_map.items():
            if d_klal != kid:
                continue
            if dec["id"] in already_applied:
                continue
            snap = dec.get("candidate_snapshot", {})
            orig = snap.get("original_word", "")
            reg = dec.get("chosen_text", "")
            if orig != reg:
                choice_map[d_wi] = (orig, reg)

        # Emit words
        first = True
        for wi, word in enumerate(words):
            if not first:
                p_el.text = (p_el.text or "") if p_el.text else ""
                # Append a space before each word (after the first) using tail
                # on the previous element — handled below via tail assignment.
            if wi in choice_map:
                orig, reg = choice_map[wi]
                choice_el = ET.SubElement(p_el, f"{{{TEI_NS}}}choice")
                orig_el = ET.SubElement(choice_el, f"{{{TEI_NS}}}orig")
                orig_el.text = orig
                reg_el = ET.SubElement(choice_el, f"{{{TEI_NS}}}reg")
                reg_el.text = reg
                if not first:
                    choice_el.tail = " "
                # Set tail for space after this element
                last_child = choice_el
            else:
                w_el = ET.SubElement(p_el, f"{{{TEI_NS}}}w")
                w_el.text = word
                if not first:
                    w_el.tail = " "
                last_child = w_el
            first = False

    return ET.ElementTree(root)


def export_tei(klalim, output_dir, word_bboxes, all_corrections, all_manual, by_klal=False):
    os.makedirs(output_dir, exist_ok=True)
    if by_klal:
        files = 0
        for k in klalim:
            tree = _build_tei([k], word_bboxes, all_corrections, all_manual)
            path = os.path.join(output_dir, f"klal_{k['klal_id']:03d}.xml")
            _write_pretty_xml(tree, path)
            files += 1
        return files
    else:
        tree = _build_tei(klalim, word_bboxes, all_corrections, all_manual)
        path = os.path.join(output_dir, "corpus.xml")
        _write_pretty_xml(tree, path)
        return 1


# ---------------------------------------------------------------------------
# XML pretty-print helper
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Sefaria ingest export
# ---------------------------------------------------------------------------

# Edition metadata for the scan this pipeline actually OCRs. Parameterised
# rather than inlined because a different digitization work needs its own -
# and because getting this wrong is not cosmetic: a version shipped under the
# wrong edition attaches the wrong text to the wrong printing in a public
# library. The previous hand-made export named the Livorno 1766 princeps via
# NLI; the scan is the Berlin reprint, sourced from Google Books (see
# START_HERE.md's scan section, confirmed 2026-08-18 against NLI catalog
# record 990011859020205171).
SEFARIA_TITLE = "Yad Malachi"
SEFARIA_HE_TITLE = "יד מלאכי"
SEFARIA_CATEGORIES = ["Rabbinic Thought", "Methodology"]
SEFARIA_NODE_EN = "Klalei HaGemara"
SEFARIA_NODE_HE = "כללי הגמרא"
SEFARIA_VERSION_TITLE = "Berlin 1851/2 (Zittenfeld) — OCR, vision-adjudicated"
SEFARIA_VERSION_SOURCE = "https://www.google.com/books/edition/_/OdiHjxI3I0EC"


def _sefaria_index():
    return {
        "title": SEFARIA_TITLE,
        "categories": list(SEFARIA_CATEGORIES),
        "schema": {
            "titles": [
                {"lang": "en", "title": SEFARIA_TITLE, "primary": True},
                {"lang": "he", "title": SEFARIA_HE_TITLE, "primary": True},
            ],
            "key": SEFARIA_TITLE,
            "nodes": [{
                "key": SEFARIA_NODE_EN,
                "titles": [
                    {"lang": "en", "title": SEFARIA_NODE_EN, "primary": True},
                    {"lang": "he", "title": SEFARIA_NODE_HE, "primary": True},
                ],
                "nodeType": "JaggedArrayNode",
                "depth": 2,
                "addressTypes": ["Integer", "Integer"],
                "sectionNames": ["Klal", "Segment"],
            }],
        },
    }


# A klal the chunker created but never filled: its whole stored text is the
# gematria marker plus a generated "כלל N" title, e.g. "רנ כלל 250". 115 of
# them exist in klalim 223-667 as of 2026-08-25. They are placeholders, not
# text, and shipping them as text would put fabricated content into a public
# library under a real citation address - the worst failure this pipeline can
# have. They export as an EMPTY segment instead: the klal keeps its address,
# and the absence is visible.
# The rule itself lives in corpus_io (moved there 2026-08-26, code review): it
# was byte-identical here and in tools/reconstruct_placeholder_klalim.py, and
# the two are one decision seen from both ends - what gets rebuilt, and what
# ships as empty. Re-exported under the local names so call sites and tests are
# unchanged.
_STUB_RE = cio.PLACEHOLDER_RE
is_placeholder = cio.is_placeholder


def _reconstructed_klal_ids():
    """klal_ids whose text was written by tools/reconstruct_placeholder_klalim.py.

    Read from the decision ledger, which is where that tool records one revisit
    flag per klal it fills - the only durable record that a klal's text is
    machine output rather than reviewed text.
    """
    out = set()
    for (kid, wi), rec in rd.all_current("klal_flag").items():
        if wi is None and rec.get("reviewer") == "tools/reconstruct_placeholder_klalim.py":
            out.add(kid)
    return out


def export_sefaria(klalim, output_dir, version_title=None, version_source=None):
    """Write Sefaria's ingest pair: index.json (schema) + version_hebrew.json.

    Depth 2 (Klal -> Segment) with ONE segment per klal. Splitting a klal into
    sentence-level segments would be an editorial act with no basis in the
    printed page, and success criterion #1 forbids silent transformation; the
    Segment level exists so a future segmentation can be added deliberately.

    The klal's own gematria marker is left at the head of its text, as printed.
    It duplicates the address, but removing it would edit the source.

    Klal numbering is dense and 1-based, so index i of the text array is klal
    i+1. Any gap would silently shift every later klal's address, so a missing
    klal_id is an error here, not an empty row.
    """
    os.makedirs(output_dir, exist_ok=True)
    by_id = {k["klal_id"]: k for k in klalim}
    expected = list(range(1, max(by_id) + 1))
    missing = [i for i in expected if i not in by_id]
    if missing:
        raise SystemExit(
            f"sefaria export: klal ids are not contiguous - missing {missing[:10]}"
            f"{'...' if len(missing) > 10 else ''}. Every later klal's citation "
            "address would be wrong. Export all parts (--all-parts) or fix the corpus."
        )

    text, placeholders = [], []
    for i in expected:
        clean = " ".join(by_id[i]["clean_text"].split())
        if is_placeholder(clean):
            placeholders.append(i)
            text.append([""])
        else:
            text.append([clean])

    if placeholders:
        print(f"  {len(placeholders)} klalim have no extracted text and export as an "
              f"EMPTY segment (placeholder rows are never shipped as text):")
        print(f"    {placeholders[:12]}{'...' if len(placeholders) > 12 else ''}")

    # FIXED 2026-08-26 (code review). Both sentences below used to be hardcoded:
    # the review sentence asserted "Klalim 1-222 ... 223-667 have not" even when
    # --part1-only shipped 222 klalim and 223-667 were not in the file at all,
    # and nothing disclosed that some klalim are UNREVIEWED MACHINE
    # RECONSTRUCTIONS lifted from the OCR token stream between two anchors and
    # never read by a human. For a public version file under a real citation
    # address that is the most load-bearing caveat there is. Both are now derived
    # from what the export actually contains.
    reviewed_here = sorted(i for i in expected if i <= cio.PART1_MAX_KLAL)
    unreviewed_here = sorted(i for i in expected if i > cio.PART1_MAX_KLAL)
    scope = []
    if reviewed_here:
        scope.append(f"klalim {reviewed_here[0]}-{reviewed_here[-1]} have been "
                     f"through word-level review")
    if unreviewed_here:
        scope.append(f"klalim {unreviewed_here[0]}-{unreviewed_here[-1]} have not")
    machine = sorted(set(_reconstructed_klal_ids()) & set(expected) - set(placeholders))
    machine_note = (
        f" {len(machine)} klalim ({machine[0]}-{machine[-1]}) carry text reconstructed "
        f"mechanically from the OCR token stream between two located markers; that text "
        f"has never been read by a human or checked against the scan."
    ) if machine else ""
    notes = (
        "OCR of the Berlin 1851/2 printing (Google Books scan), corrected through "
        "an image-grounded review pipeline: every change is adjudicated against the "
        "scan crop and recorded in an append-only decision ledger. "
        f"{len(text) - len(placeholders)} of {len(text)} klalim carry extracted text; "
        f"{len(placeholders)} are not yet extracted and are empty here. "
        + "; ".join(scope) + "." + machine_note
    )

    version = {
        "title": SEFARIA_TITLE,
        "versionTitle": version_title or SEFARIA_VERSION_TITLE,
        "versionSource": version_source or SEFARIA_VERSION_SOURCE,
        "versionNotes": notes,
        "language": "he",
        "license": "Public Domain",
        "text": text,
    }

    index_path = os.path.join(output_dir, "index.json")
    version_path = os.path.join(output_dir, "version_hebrew.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(_sefaria_index(), f, ensure_ascii=False, indent=2)
        f.write("\n")
    with open(version_path, "w", encoding="utf-8") as f:
        json.dump(version, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return len(text)


def _write_pretty_xml(tree, path):
    """Serialise an ElementTree to a file with pretty indentation.

    Uses minidom for pretty-printing since ET.indent() is only available in
    Python 3.9+. Validates well-formedness by parsing the serialised string
    before writing.
    """
    import io
    buf = io.BytesIO()
    tree.write(buf, encoding="utf-8", xml_declaration=True)
    xml_bytes = buf.getvalue()

    # Validate well-formedness (raises ParseError if malformed)
    ET.fromstring(xml_bytes)

    # Pretty-print via minidom
    dom = minidom.parseString(xml_bytes)
    pretty = dom.toprettyxml(indent="  ", encoding="utf-8")
    # minidom adds a redundant first line with <?xml ... ?> before the one we set;
    # strip the extra declaration minidom adds, since we write one explicitly.
    lines = pretty.decode("utf-8").splitlines()
    # Remove the extra standalone="no" xml declaration minidom inserts
    filtered = [l for i, l in enumerate(lines) if not (i == 0 and l.startswith("<?xml"))]
    output = "<?xml version='1.0' encoding='utf-8'?>\n" + "\n".join(filtered) + "\n"

    with open(path, "w", encoding="utf-8") as f:
        f.write(output)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Export the reviewed Yad Malachi corpus in multiple archival formats."
    )
    parser.add_argument("--format", required=True,
                        choices=["plain", "alto", "page", "tei", "sefaria"],
                        help="Output format")
    parser.add_argument("--output-dir", required=True,
                        help="Directory to write output files into")
    parser.add_argument("--by-klal", action="store_true",
                        help="Write one file per klal (plain and tei only)")
    parser.add_argument("--klal-id", type=int, default=None,
                        help="Export only this klal_id (for testing)")
    parser.add_argument("--all-parts", dest="all_parts", action="store_true", default=None,
                        help="Load klalim 1-667 (all three part files) instead of part1 only. "
                             "Default for --format sefaria.")
    parser.add_argument("--part1-only", dest="all_parts", action="store_false",
                        help="Force part1-only scope, even for --format sefaria")
    parser.add_argument("--version-title", default=None,
                        help="sefaria only: override the version title")
    parser.add_argument("--version-source", default=None,
                        help="sefaria only: override the version source URL")
    args = parser.parse_args()

    # Load corpus. The sefaria export is a whole-work deliverable, so it takes
    # all three part files unless explicitly told otherwise; the review-oriented
    # formats stay on part1 unless asked, since that is the reviewed scope.
    all_parts = args.all_parts if args.all_parts is not None else (args.format == "sefaria")
    if all_parts:
        klalim = []
        for path in (cio.PART1_PATH, cio.repo_path("part2.json"), cio.repo_path("part3.json")):
            klalim.extend(cio.load_klalim(path) or [])
        klalim.sort(key=lambda k: k["klal_id"])
    else:
        klalim = cio.load_part1_sorted()
    if not klalim:
        print("ERROR: corpus not found or empty.", file=sys.stderr)
        sys.exit(1)

    if args.klal_id is not None:
        if args.format == "sefaria":
            # FIXED 2026-08-26 (code review). The sefaria export derives every
            # klal's citation address from its POSITION in a dense 1..N array, so
            # a one-klal slice can only ever fail its own contiguity check - and
            # it failed with "missing [1, 2, 3, 4]... Export all parts
            # (--all-parts) or fix the corpus", which blames the corpus and
            # suggests a flag that was already on. Refuse it up front, for the
            # real reason.
            print("ERROR: --klal-id cannot be combined with --format sefaria - the "
                  "Sefaria version file addresses klalim by position in a dense "
                  "1..N array, so it is a whole-work deliverable. Use --by-klal "
                  "with a text/xml format to export a single klal.", file=sys.stderr)
            sys.exit(1)
        klalim = [k for k in klalim if k["klal_id"] == args.klal_id]
        if not klalim:
            source = ("part1.json + part2.json + part3.json" if all_parts else "part1.json")
            print(f"ERROR: klal_id {args.klal_id} not found in {source}.", file=sys.stderr)
            sys.exit(1)

    print(f"Loaded {len(klalim)} klal(im) from "
          f"{'part1.json + part2.json + part3.json' if all_parts else 'part1.json'}")

    # Apply review decisions (in-memory only, no file writes)
    klalim = _apply_decisions_to_klalim(klalim)

    # Load ancillary data for layout formats
    word_bboxes = _load_word_bboxes()
    klal_regions = _load_klal_regions()
    all_corrections = rd.all_current("candidate_choice")
    all_manual = rd.all_current("manual_correction")

    fmt = args.format
    out = args.output_dir

    if fmt == "plain":
        n = export_plain(klalim, out, by_klal=args.by_klal)
        label = "file(s)" if n > 1 else "file"
        print(f"plain: wrote {n} {label} to {out}")

    elif fmt == "sefaria":
        n = export_sefaria(klalim, out, args.version_title, args.version_source)
        print(f"sefaria: wrote index.json + version_hebrew.json ({n} klalim) to {out}")

    elif fmt == "alto":
        n = export_alto(klalim, out, klal_regions, word_bboxes)
        print(f"alto: wrote {n} page XML file(s) to {out}")

    elif fmt == "page":
        n = export_page(klalim, out, klal_regions, word_bboxes)
        print(f"page: wrote {n} page XML file(s) to {out}")

    elif fmt == "tei":
        n = export_tei(klalim, out, word_bboxes, all_corrections, all_manual,
                       by_klal=args.by_klal)
        label = "file(s)" if n > 1 else "file"
        print(f"tei: wrote {n} {label} to {out}")

    print("Done.")


if __name__ == "__main__":
    main()
