#!/usr/bin/env python3
# [PRODUCTION] Local review-dashboard server for Part 1: JSON API + static
# frontend (review_frontend/). Replaces the old single-file, all-data-
# inlined review.html (see PROJECT-STATUS.md "Review dashboard
# rearchitecture") - that file embedded all 222 klalim's text and all 762
# correction candidates into one <script> tag and built every klal's DOM +
# listeners synchronously on load, which is the likely cause of both its
# sluggish feel and of the Chrome extension never successfully loading it
# all session.
#
# This server reads corrections_part1.json / klalim_demo_dataset.json /
# part1_header_anchored_alignment.json / klal_page_regions.json fresh off
# disk on every request and merges in review_decisions.jsonl's current
# human-decision state at serve time - it never needs restarting after
# ./rebuild_all.sh regenerates those files, and a pipeline rebuild can
# never clobber a human decision (that file lives entirely outside the
# corpus-build pipeline).
#
# Every write endpoint only INSERTs (via review_decisions.append_decision) -
# there is no update/delete anywhere in this API surface. Nothing here ever
# writes to part1.json; promoting an accepted decision into the corpus text
# is a separate, manually-run step (apply_reviewer_decisions.py).
#
# Run: python3 review_server.py [--port 8420]
# Then open http://127.0.0.1:8420/ in a browser.
import argparse
import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

import review_decisions as rd

REPO = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(REPO, "review_frontend")
IMAGES_DIR = os.path.join(REPO, "images", "pdf_pages")
PART1_MAX_KLAL = 222

FLAG_LABELS = {
    "current_text_may_be_wrong": ["May be wrong", "#e53e3e"],
    "possible_omission": ["Possibly missing", "#805ad5"],
    "current_text_confirmed": ["Confirmed", "#38a169"],
    "unverified_insertion": ["Unverified addition", "#a0aec0"],
    "ambiguous": ["Ambiguous", "#dd6b20"],
    "error": ["Check failed", "#718096"],
}

MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".png": "image/png",
    ".json": "application/json; charset=utf-8",
}


# ---------- data loading (fresh off disk every call, deliberately no cache) ----------

def _load_json(name, default=None):
    path = os.path.join(REPO, name)
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _load_klalim():
    demo = _load_json("klalim_demo_dataset.json", [])
    klalim = [k for k in demo if k["klal_id"] <= PART1_MAX_KLAL]
    klalim.sort(key=lambda k: k["klal_id"])
    return {k["klal_id"]: k for k in klalim}, klalim


def _load_alignment():
    align = _load_json("part1_header_anchored_alignment.json", [])
    return {r["klal_id"]: r for r in align}


def _load_corrections():
    return _load_json("corrections_part1.json", {})


def _load_regions():
    return _load_json("klal_page_regions.json", {})


def _trusted_page(alignment, klal_id):
    r = alignment.get(klal_id, {})
    return r.get("matched_page") if r.get("trusted") else None


def _merge_decision(entry, klal_id):
    """Overlay the current human decision (if any) on top of a raw
    corrections_part1.json entry - never mutates the source data, this is
    a display-time merge only."""
    entry = dict(entry)
    entry["current_decision"] = rd.current_for(klal_id, entry["word_index"], "candidate_choice")
    return entry


# ---------- API payload builders ----------

def api_flags():
    return FLAG_LABELS


def api_klalim():
    klalim_by_id, klalim = _load_klalim()
    alignment = _load_alignment()
    corrections = _load_corrections()
    flagged = set(rd.flagged_klalim())
    decided = rd.all_current("candidate_choice")  # {(klal_id, word_index): record}
    out = []
    for k in klalim:
        kid = k["klal_id"]
        entries = corrections.get(str(kid), [])
        decided_count = sum(1 for c in entries if (kid, c["word_index"]) in decided)
        out.append({
            "klal_id": kid,
            "title": k.get("title", ""),
            "section": k.get("section", ""),
            "page": _trusted_page(alignment, kid),
            "page_trusted": kid in alignment and bool(alignment[kid].get("trusted")),
            "correction_count": len(entries),
            # split so the nav badge can distinguish "still needs a look"
            # from "already decided" instead of one undifferentiated count
            # (2026-08-07, PROJECT-STATUS.md "review dashboard feedback").
            "decided_count": decided_count,
            "open_count": len(entries) - decided_count,
            "needs_revisit": kid in flagged,
            # lets the frontend size an unmounted placeholder block
            # proportionally instead of a fixed guess, so lazy-loading a
            # klal's real content doesn't cause a large layout jump.
            "text_length": len(k.get("clean_text", "")),
        })
    return out


def api_klal(klal_id):
    klalim_by_id, _ = _load_klalim()
    k = klalim_by_id.get(klal_id)
    if not k:
        return None
    alignment = _load_alignment()
    corrections = _load_corrections().get(str(klal_id), [])
    corrections = [_merge_decision(c, klal_id) for c in corrections]
    regions = _load_regions()
    region_entry = regions.get(str(klal_id), {})
    flag_state = rd.current_for(klal_id, decision_type="klal_flag")
    return {
        "klal_id": k["klal_id"],
        "title": k.get("title", ""),
        "section": k.get("section", ""),
        "gematria": k.get("gematria", ""),
        "clean_text": k.get("clean_text", ""),
        "page": _trusted_page(alignment, klal_id),
        "page_trusted": klal_id in alignment and bool(alignment[klal_id].get("trusted")),
        "region": region_entry.get("bbox"),
        # klal's content continues onto one or more later pages (e.g. klal 4:
        # starts on page 15's last line, most of its text is on page 16) -
        # a per-page bbox for each, so the scan-pane highlight can follow
        # the klal when the reviewer manually flips pages.
        "continuations": region_entry.get("continuations", []),
        "corrections": corrections,
        "needs_revisit": bool(flag_state and flag_state.get("needs_revisit")),
        "flag_note": flag_state.get("note") if flag_state else None,
    }


def api_klal_flag(klal_id):
    current = rd.current_for(klal_id, decision_type="klal_flag")
    history = rd.history_for(klal_id, decision_type="klal_flag")
    return {
        "needs_revisit": bool(current and current.get("needs_revisit")),
        "note": current.get("note") if current else None,
        "history": history,
    }


def api_decision_history(klal_id, word_index):
    return rd.history_for(klal_id, word_index, "candidate_choice")


def api_page(page_num):
    _, klalim = _load_klalim()
    alignment = _load_alignment()
    corrections = _load_corrections()
    out = []
    for k in klalim:
        kid = k["klal_id"]
        if _trusted_page(alignment, kid) != page_num:
            continue
        for c in corrections.get(str(kid), []):
            if not c.get("bbox"):
                continue
            entry = _merge_decision(c, kid)
            entry["klal_id"] = kid
            out.append(entry)
    return out


def api_post_candidate_decision(body):
    klal_id = int(body["klal_id"])
    word_index = int(body["word_index"])
    corrections = _load_corrections().get(str(klal_id), [])
    snapshot = next((c for c in corrections if c["word_index"] == word_index), None)
    record = rd.append_decision(
        "candidate_choice",
        klal_id=klal_id,
        word_index=word_index,
        chosen_source=body.get("chosen_source"),
        chosen_text=body.get("chosen_text"),
        candidate_snapshot=snapshot,
        note=body.get("note"),
    )
    return record


def api_post_klal_flag(body):
    klal_id = int(body["klal_id"])
    record = rd.append_decision(
        "klal_flag",
        klal_id=klal_id,
        needs_revisit=bool(body.get("needs_revisit")),
        note=body.get("note"),
    )
    return record


# ---------- HTTP plumbing ----------

ROUTE_KLAL = re.compile(r"^/api/klal/(\d+)$")
ROUTE_KLAL_FLAG = re.compile(r"^/api/klal/(\d+)/flag$")
ROUTE_DECISIONS = re.compile(r"^/api/decisions/(\d+)/(\d+)$")
ROUTE_PAGE = re.compile(r"^/api/page/(\d+)$")


class Handler(BaseHTTPRequestHandler):
    server_version = "YadMalachiReview/1.0"

    def log_message(self, fmt, *args):
        pass  # keep stdout clean; errors still raise/print via BaseHTTPRequestHandler's default hooks

    def _send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error_json(self, status, message):
        self._send_json({"error": message}, status=status)

    def _serve_static(self, base_dir, rel_path, default_file=None):
        if rel_path in ("", "/"):
            rel_path = default_file or "index.html"
        rel_path = rel_path.lstrip("/")
        full_path = os.path.realpath(os.path.join(base_dir, rel_path))
        base_real = os.path.realpath(base_dir)
        if not full_path.startswith(base_real + os.sep) and full_path != base_real:
            self._send_error_json(403, "forbidden")
            return
        if not os.path.isfile(full_path):
            self._send_error_json(404, "not found")
            return
        ext = os.path.splitext(full_path)[1]
        content_type = MIME_TYPES.get(ext, "application/octet-stream")
        with open(full_path, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        try:
            if path == "/api/flags":
                return self._send_json(api_flags())
            if path == "/api/klalim":
                return self._send_json(api_klalim())
            m = ROUTE_KLAL_FLAG.match(path)
            if m:
                return self._send_json(api_klal_flag(int(m.group(1))))
            m = ROUTE_KLAL.match(path)
            if m:
                payload = api_klal(int(m.group(1)))
                if payload is None:
                    return self._send_error_json(404, "klal not found")
                return self._send_json(payload)
            m = ROUTE_DECISIONS.match(path)
            if m:
                return self._send_json(api_decision_history(int(m.group(1)), int(m.group(2))))
            m = ROUTE_PAGE.match(path)
            if m:
                return self._send_json(api_page(int(m.group(1))))
            if path.startswith("/images/pdf_pages/"):
                return self._serve_static(IMAGES_DIR, path[len("/images/pdf_pages"):])
            if path.startswith("/api/"):
                return self._send_error_json(404, "unknown endpoint")
            return self._serve_static(FRONTEND_DIR, path)
        except Exception as e:  # noqa: BLE001 - surface as JSON, don't crash the server thread
            self._send_error_json(500, f"{type(e).__name__}: {e}")

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b"{}"
            body = json.loads(raw.decode("utf-8"))

            if path == "/api/decisions/candidate":
                return self._send_json(api_post_candidate_decision(body), status=201)
            if path == "/api/decisions/klal_flag":
                return self._send_json(api_post_klal_flag(body), status=201)
            return self._send_error_json(404, "unknown endpoint")
        except (KeyError, ValueError, TypeError) as e:
            return self._send_error_json(400, f"bad request: {e}")
        except Exception as e:  # noqa: BLE001
            self._send_error_json(500, f"{type(e).__name__}: {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8420)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Yad Malachi review server: http://{args.host}:{args.port}/")
    print(f"Decisions log: {rd.DECISIONS_PATH}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.shutdown()


if __name__ == "__main__":
    main()
