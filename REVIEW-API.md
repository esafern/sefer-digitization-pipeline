# Review server API

The review dashboard in `review_frontend/` is one client of a local HTTP API
served by `pipeline/review_server.py`. This file documents that API for anyone
building a different client, a native macOS app for example. It covers what
each route returns, what each ruling route records, and the rules a client has
to keep.

Every sample response below is real. They were recorded on 2026-09-16 from the
synthetic fixture corpus described under "A server to develop against", and
shortened where marked `…`.

## TL;DR

- **Go through the server, never the data files.** The server re-reads the
  corpus files on every request, and it records a ruling only by appending one
  line to `review_decisions.jsonl`. A client that writes a JSON file itself
  skips the checks the server applies, and becomes a second copy of logic that
  already exists (START_HERE.md, Lesson 13).
- **Develop against the sandbox, not the real corpus.** A ruling clicked
  against Yad Malachi lands in the repo's own `review_decisions.jsonl`. Git
  tracks that file, and it is the owner's record of human rulings.
- **Recording a ruling changes no text.** A POST appends to the ledger, and the
  entry comes back with that ruling as its `current_decision`. `clean_text`
  changes only when the owner runs `pipeline/apply_reviewer_decisions.py` and
  rebuilds.
- **A word is addressed by `(klal_id, word_index)`.** `word_index` is a position
  in `clean_text.split(' ')`: the text is split on each single space, never on
  runs of whitespace. See "Conventions".
- **The server has no authentication and no CORS.** A native app is unaffected.
  A web page served from another origin cannot call the server as it stands.
- **Who a ruling is recorded as.** Send `X-Sefer-Reviewer: <name>` on a POST,
  percent-encoded UTF-8 (`encodeURIComponent`), and the ruling is recorded
  under that name. Without the header it is recorded under the server's
  `$SEFER_REVIEWER`, or `local` if that is unset. Letters of any script,
  digits, spaces and `._@-`, at most 64 characters; anything else is a `400`
  and nothing is written. The name is asserted, not proven: every actor
  carries `verified: false`.
- **Noticing other sessions.** `GET /api/changes` with no `since` returns
  `count` and `corpus_stamp` only. Keep `count`; later, `since=<count>` returns
  every row appended after it (`id`, `klal_id`, `word_index`,
  `decision_type`, `ts`, `who`), at most 500 with `truncated: true` beyond that.
  Your own saves are among them: the id each POST returned tells them apart.
  `reset: true` means the log was replaced; `corpus_stamp` changing means the
  served text was rebuilt.

| Method | Route | What for |
|---|---|---|
| GET | `/api/corpus` | The book that is loaded, what an entry is called, its parts |
| GET | `/api/flags` | A label and a colour for each `flag` value |
| GET | `/api/numerals` | Hebrew numerals from 1 to 400 |
| GET | `/api/klalim?part=1` | The navigation list: one row of counts per entry |
| GET | `/api/klal/<id>` | One entry: its text, disputes, scan geometry and rulings |
| GET | `/api/klal/<id>/versions` | The entry's other texts, for the compare toggle |
| GET | `/api/klal/<id>/flag` | The entry's revisit flag and its history |
| GET | `/api/klal/<id>/title-history` | Every heading ruling on the entry |
| GET | `/api/decisions/<klal_id>/<word_index>` | Every ruling on one word |
| GET | `/api/page/<n>` | Every box to draw on scan page `n` |
| GET | `/api/word-states?part=1` | Every counted word, listed by state |
| GET | `/api/witness` | The pages carrying witness disagreements, with counts |
| GET | `/api/witness/context/<page>/<token>` | The OCR words around one witness item |
| GET | `/api/reviewer` | Who a new session records as, and the roster (no emails) |
| GET | `/api/changes?since=<n>` | Rulings appended after row `n`, for spotting other sessions' work |
| GET | `/images/pdf_pages/page_<n>.png` | A scan page image |
| GET | `/entry/<id>/word/<w>` | A share link that redirects into the HTML dashboard |
| POST | `/api/decisions/disputed` | Rule on a word the machine flagged |
| POST | `/api/decisions/manual` | Correct or delete any word |
| POST | `/api/decisions/witness` | Rule on a witness disagreement |
| POST | `/api/decisions/punctuation` | Accept or reject a proposed sentence break |
| POST | `/api/decisions/klal_flag` | Set or clear a revisit flag on an entry or a word |
| POST | `/api/decisions/title` | Correct a heading, one word at a time or whole |

## A server to develop against

```bash
python3 tests/fixtures/build_fixture_corpus.py ~/fixture_sefer
SEFER_CORPUS_ROOT=~/fixture_sefer python3 pipeline/review_server.py --port 8424
```

The fixture is a made-up book of 4 entries on 2 scan pages. It is built by
running the pipeline's real stages over invented Hebrew. It carries every kind
of item the API serves:
- machine disputes, including an omission;
- a revisit flag and a punctuation proposal;
- witness disagreements;
- two human rulings.

The build takes about a second. Re-run it to wipe every ruling.

**Where rulings go.** The server keeps `review_decisions.jsonl` inside the
corpus root, so on the fixture they land in `~/fixture_sefer/`, outside the
repo. The server prints the path at startup as `Decisions log: …`. Check that
line before clicking anything.

**Real data without real rulings.** For real volume (Yad Malachi's Part 1 has
222 entries), run the real corpus against a copy of the ledger:

```bash
cp review_decisions.jsonl ~/scratch_ledger.jsonl
REVIEW_DECISIONS_PATH=~/scratch_ledger.jsonl python3 pipeline/review_server.py --port 8423
```

`REVIEW_DECISIONS_PATH` redirects both the reads and the writes of the ledger.
This was tested on the fixture on 2026-09-16: two rulings went to the override
file and none to the corpus's own ledger. The file has to exist before the
server starts, because the server refuses to start without a ledger. Port 8420
is the default and is usually taken by the owner's own server.

**Restarts.** Data changes are picked up on the next request. Changes to the
server's own code need a restart.

**Who a ruling is signed by.** The server reads `$SEFER_REVIEWER` from its own
environment, an id from `reviewers.json`, and prints that identity at startup.
If it is unset, rulings record `id: local`, displayed as "Unidentified local
reviewer". A client cannot send an identity with a request, and the identity
is asserted, not authenticated.

## Conventions

- **JSON in UTF-8**, with Hebrew as literal characters rather than `\u`
  escapes. A request carries a JSON body; the server does not check
  `Content-Type`.
- **Success** is `200` for a read and `201` for a recorded ruling.
- **Errors** come back as `{"error": "<message>"}`:
  - `400` for bad input. A missing field is named bare, as in
    `bad request: 'word_index'`.
  - `404` for an unknown route or entry.
  - `500` for a server fault, sent as `<ExceptionType>: <message>`.
  - An `OPTIONS` request gets `501`, which is why a cross-origin browser
    request fails its preflight.
- **Listening address.** The server listens on `127.0.0.1` by default. `--host`
  can widen that. Don't: any request that reaches the server can write rulings.
- **`part`** takes `1`, `2`, `3` or `all`, and defaults to `1`. `0` and `none`
  are old spellings of `all`, and anything else is a `400`. `/api/corpus`'s
  `parts` lists the parts the book has.
- **`klal_id`** is the entry's number. The API says "klal" throughout for
  historical reasons. `/api/corpus` gives the word to show (`unit` and
  `unit_he`, "Klal" for Yad Malachi and "Shorash" for Sefer HaShorashim). It
  also gives `entry_ref`: `number` or `root`, for how an entry is referred to.
- **`word_index`** is a position in `clean_text.split(' ')`, split on the single
  space character exactly. Two spaces in a row make an empty word, and that
  empty word takes a position.
  - Every ruling in the ledger is numbered this way (`corpus_io.words_of`).
  - Python's `split()`, JavaScript's `split(/\s+/)` and Swift's
    `split(separator: " ")` all drop empty words, and renumber every word after
    a double space.
  - In Swift, use `components(separatedBy: " ")`, or
    `split(separator: " ", omittingEmptySubsequences: false)`.
- **`bbox`** is `{x1, y1, x2, y2}`: fractions from 0 to 1 of the page image's
  width and height, measured from its top-left corner. It always comes with a
  `page`.
- **A page number** is the `n` in `page_<n>.png`, the pipeline's own page
  index. It is not the folio printed on the leaf, which is not stored anywhere.
- **`current_decision`** is `null`, or the newest ledger record for that item.
  Its shape is under "The ledger record".

## Reading

### `GET /api/corpus`

```json
{"title": "Fixture Sefer", "title_he": "ספר הבדיקה", "section": "Fixture Section",
 "section_he": "פרק הבדיקה", "edition": "Synthetic fixture - no scan, no edition",
 "unit": "Klal", "unit_plural": "Klalim", "unit_he": "כלל", "entry_ref": "number",
 "comparison_name": null, "has_ocr_baseline": false, "has_their_ocr": false,
 "has_their_corrected": false, "parts": [{"part": 1, "first_klal": 1, "last_klal": 4}]}
```

The three `has_…` flags say which of the other texts `/versions` can have.
Where one is false, the matching view is always `null`.

### `GET /api/flags`

```json
{"current_text_may_be_wrong": ["Disputed", "#e53e3e"],
 "possible_omission": ["Possibly missing", "#805ad5"],
 "current_text_confirmed": ["Machine-Resolved", "#38a169"],
 "ai_flag": ["Flagged for revisit", "#d69e2e"],
 "witness": ["Witness disagreement", "#805ad5"], …}
```

Every `flag` value on a queue entry or a page box is a key here.

### `GET /api/numerals`

`{"1": "א", "2": "ב", …, "15": "טו", "16": "טז", …}`, for 1 to 400, with string
keys. Use this table rather than writing your own. It carries the edge cases:
15 and 16 are טו and טז, never יה and יו, and final letter forms are handled.

### `GET /api/klalim?part=1`

One row per entry, in order:

```json
[{"klal_id": 2, "title": "וו.", "title_pending": false, "heading_concerns": [],
  "gematria": "ב", "section": "Fixture Section", "page": 2, "page_trusted": true,
  "correction_count": 3, "decided_count": 1, "open_count": 2,
  "machine_disputed_count": 0, "machine_resolved_count": 2, "ai_flag_count": 0,
  "recorded_decision_count": 1, "punctuation_count": 1,
  "punctuation_decided_count": 0, "punctuation_open_count": 1,
  "needs_revisit": false, "text_length": 20}, …]
```

- The counts drive the navigation badges and the legend. `/api/word-states`
  lists the words behind them.
- `title_pending` means a heading ruling is recorded but not yet applied.
- `text_length` is `clean_text`'s length in characters.

### `GET /api/klal/<id>`

The main payload: one entry with everything the text pane draws. An unknown
entry is `404 {"error": "klal not found"}`.

```json
{"klal_id": 2, "title": "וו.", "section": "Fixture Section", "gematria": "ב",
 "clean_text": "ב וו זין חית טית יוד",
 "title_word_start": 1, "title_word_count": 1,
 "footnote_refs": [], "footnote_marks": [], "title_decision": null,
 "page": 2, "page_trusted": true,
 "region": {"x1": 0.6556, "y1": 0.1, "x2": 0.91, "y2": 0.13},
 "continuations": [], "word_pages": {"0": 2, "1": 2, "2": 2, "4": 2, "5": 2},
 "queue": [
   {"word_index": 3, "opcode": "replace", "flag": "current_text_may_be_wrong",
    "final_text": "חית", "docai_reading": "חתי", "docai_repaired": null,
    "vision_selected": "A", "vision_transcription": "חית", "confidence": 0.99,
    "reasoning": "fixture: canned verdict, no vision call made",
    "vlm_reading": null, "surya_reading": null, "dicta_reading": null,
    "page": 2, "bbox": {"x1": 0.6167, "y1": 0.18, "x2": 0.6767, "y2": 0.21},
    "current_decision": {"id": "6b11d9c9c6ba", "decision_type": "manual_correction",
                         "chosen_text": "חית", …}},
   {"word_index": 4, "opcode": "replace", "flag": "current_text_confirmed",
    "final_text": "טית", "docai_reading": "טיס", "current_decision": null, …}],
 "punctuation": [{"before_word_index": 3, "reasoning": "fixture: a proposed sentence break",
                  "current_decision": null}],
 "stranded_rulings": [], "needs_revisit": false, "flag_note": null,
 "witness_count": 0, "witness_pages": []}
```

**The entry's fields:**

- **`title_word_start` and `title_word_count`.** The printed heading is not
  separate text. It is the entry's opening words, set large. Style that run of
  `clean_text` words, and don't print `title` above the body as a second copy.
- **`footnote_refs`** lists the word positions of the book's reference numerals,
  which are drawn raised.
- **`footnote_marks`** is a list of `{word_index, number, read_as, absorbs}`.
  Each is a stray mark in our text (`"`, `'`, `*`) that the scan shows is
  footnote number `number`.
- **`page`, `region` and `continuations`.** `page` and `region` give where the
  entry starts on the scan. `continuations` has one item, with its own box, per
  later page the entry runs onto. `page_trusted: false` comes with
  `page: null`: no trustworthy start page is known, so don't turn to one.
- **`word_pages`** maps `"<word_index>"` to a page, so a click on any word can
  turn to the right page. Its keys are strings, and a word the alignment never
  matched has no key (word 3 above).
- **`queue`** is the words to draw as items. It is described below.
- **`punctuation`** holds proposed sentence breaks. In a decided one,
  `current_decision` is `{accepted, note}`.
- **`stranded_rulings`** holds recorded rulings the server will not place on a
  word, because the word they name is no longer at their index. List them. Do
  not draw them on a word.
- **`needs_revisit` and `flag_note`** are the entry-level revisit flag.
- **`title_decision`** is `null`, or the current heading ruling as
  `{id, whole, word_index, chosen_text, note, ts, by_human, applied, stale}`.
  `applied: false` means recorded but not yet in the text.

**`queue` entries.** Every entry has `word_index`, `opcode`, `flag`, `page`,
`bbox` and `current_decision`. Most also carry these fields:
- `final_text`, the word stored now;
- `docai_reading`, the fresh OCR reading;
- `vision_selected`, `vision_transcription`, `confidence` and `reasoning`, the
  vision check's verdict;
- `vlm_reading`, `surya_reading` and `dicta_reading`, other engines' readings,
  where there are any.

What each `opcode` means:

| `opcode` | Meaning |
|---|---|
| `replace` | Our word and the OCR's reading differ. |
| `insert` | Our text has a word the OCR does not. `final_text` is our word. |
| `delete` | The OCR has a word our text lacks. It is a **gap** standing *before* `word_index`, not the word at `word_index`: both can exist at one index. `word_index` may equal the word count, for a gap after the last word. |
| `ai_flag` | A word flagged for revisit, with no machine candidate behind it. |
| `manual` | A word a reviewer corrected with no machine candidate behind it. It always has a `current_decision`. |
| `witness` | A disagreement with the witness OCR. Its key is `docai_token_index` (see the witness POST). `gap: true` marks words the witness has where ours has none, standing before `word_index`. |

Apart from gaps, there is at most one entry per word. Where two kinds of item
meet on one word, the server merges them into one entry and adds an overlay:
- `word_flag` is a revisit flag on the word, with `answered: true` once a later
  ruling has answered it;
- `witness_overlay` is the witness disagreement at the word.

### `GET /api/klal/<id>/versions`

```json
{"master": "ב וו זין חית טית יוד", "ours_ocr": null, "theirs_ocr": null,
 "theirs_corrected": null, "comparison_name": null, "theirs_covers": null,
 "layout": {"master": {"title_word_start": 1, "title_word_count": 1,
                       "footnote_refs": [], "footnote_marks": []}}}
```

The entry's four texts, for the compare toggle:

| View | Text |
|---|---|
| `master` | Our text now, with every applied ruling |
| `ours_ocr` | The frozen OCR baseline |
| `theirs_ocr` | The comparison digitization's unreviewed text |
| `theirs_corrected` | That digitization's corrected text |

A view is `null` where its source has nothing for the entry.
- `layout` gives each text's heading run and footnote positions, numbered in
  that text's own words, so each view can be drawn like `master`.
- `footnote_marks` appears for our two texts only.
- The other digitization matches entries by root. Where two of our entries
  share a root, they get the same text from it, and `theirs_covers` lists both
  entries.
- The HTML page offers each "theirs" view with its vowel points stripped. It
  does that on the client, in app.js's `withoutPoints`.

### `GET /api/klal/<id>/flag`

```json
{"needs_revisit": true, "note": "entry note",
 "history": [{"id": "75d821cebafa", "decision_type": "klal_flag", "word_index": null,
              "needs_revisit": true, "note": "entry note", …}]}
```

This is the entry-level flag only. Word-level flags come through `queue`.

### `GET /api/klal/<id>/title-history`

```json
{"klal_id": 2, "title": "וו.",
 "history": [{"id": "6f1ba0277f26", "ts": "…", "whole": true, "word_index": 0,
              "chosen_text": "כותרת חדשה.", "was": "וו.", "note": "sandbox",
              "applied": false, "by_human": true, "reviewer": "local", "actor": {…}}, …],
 "current": {…the first history row…}}
```

History is newest first. `was` is the heading, or the heading word, as it stood
when the ruling was recorded.

### `GET /api/decisions/<klal_id>/<word_index>`

This returns a bare list of ledger records about one word, oldest first. Each
record has two extra fields:
- `history_basis` is `"word_id"` when the word's stable id found the rows, and
  `"word_index"` when only the position did. With `"word_index"`, the rows are
  about that position, which may have held different words over time.
- `word_id` is the word's stable id, or `null`.

### `GET /api/page/<n>`

This returns a list of boxes for scan page `n`, covering every entry that
touches the page. Each box has a `kind`:

```json
[{"kind": "correction", "klal_id": 1, "word_index": 6, "opcode": "replace",
  "flag": "current_text_may_be_wrong", "final_text": "דלת", "docai_reading": "דלד",
  "page": 2, "bbox": {"x1": 0.5111, "y1": 0.1, "x2": 0.5711, "y2": 0.13},
  "current_decision": null, …},
 {"kind": "witness", "klal_id": 4, "word_index": 2, "docai_token_index": 16, "tier": "D",
  "docai_reading": "עין", "tesseract_reading": "עיו", "page": 2,
  "bbox": {"x1": 0.15, "y1": 0.42, "x2": 0.21, "y2": 0.45}, "current_decision": null, …},
 {"kind": "plain", "klal_id": 1, "word_index": 5, "page": 2,
  "bbox": {"x1": 0.85, "y1": 0.1, "x2": 0.91, "y2": 0.13}}, …]
```

- A `correction` box has a `queue` entry's shape plus `klal_id`.
- A `plain` box is every other word the alignment placed on the page. It lets a
  click on any word, flagged or not, find its ink.

### `GET /api/word-states?part=1`

```json
{"part": "1",
 "machine_disputed": [{"klal_id": 1, "word_index": 6, "word": "דלת", "gematria": "א"}, …],
 "machine_resolved": […], "decided": […], "ai_flag": […],
 "recorded": [{"klal_id": 2, "word_index": 3, "word": "חית", "decision_type": "manual_correction",
               "chosen_text": "חית", "status": "confirmed", "resolved_word_index": 3,
               "resolved_by": "index", "rendered": true, …}]}
```

- **The three state lists.** `machine_disputed`, `machine_resolved` and
  `decided` split the counted words between them.
- **`ai_flag`** overlaps them: an open flag renders its word as disputed.
- **`recorded`** is every ruling in the part:
  - `status` says whether the corpus holds the ruling;
  - `resolved_word_index` says where its word is now;
  - `resolved_by` says how that position was found.
- **`word`** is `null` for an omission, which sits one past the last word.

### `GET /api/witness`

```json
{"pages": [{"page": 2, "klal_id": 4, "total": 4, "decided": 0}],
 "by_tier": {"D": 2, "one_side_empty": 2}, "total": 4,
 "tier_stats": null, "corrected_name": null, "reviewed_entries": null, "witness_name": null}
```

These pages matter because a witness item can sit on a continuation page with
no entry start of its own. Page-stepping by entry would skip it.

### `GET /api/witness/context/<page>/<token>`

```json
{"words": ["וו", "זין", "חתי", "טית", "יוד", "ג", "כף", "למד", "מם", "נון", "ד", "סמך", "עין", "פא"],
 "target_index": 12}
```

This returns up to 12 raw OCR words on each side of one witness item. For
`<token>`, pass the item's `page_token_index` if it has one, and its
`docai_token_index` otherwise (app.js does the same).

### Static routes

- **`/images/pdf_pages/page_<n>.png`** serves the scan images.
- **`/entry/<id>/word/<w>`** (or `/entry/<id>`, or the older `/klal/…`)
  answers `302` to `/#entry=<id>&word=<w>`. That fragment belongs to the HTML
  dashboard. A native app that wants to open such links should parse the path
  itself.
- **`/`, `/app.js` and `/app.css`** are the HTML dashboard.

## Recording

Each of the six routes takes a JSON body and returns `201` with the record it
appended.

- **The snapshot is the server's job.** The server builds the record's
  `candidate_snapshot` itself: what the item looked like when it was ruled on.
  The apply step checks the text against it, so a client never sends one.
- **Nothing is edited or removed.** A later ruling at the same address, of the
  same type, becomes the `current_decision`. The earlier one stays in the
  ledger.
- **`note` is optional on every route.** The ledger is permanent, though, and
  the note is how the owner later reads why a ruling was made.
- **Re-fetch after a POST.** Fetch `/api/klal/<id>` (and the page) again after
  one; the HTML page drops its copy of the entry and does the same.

### The ledger record

```json
{"id": "c65dad89921b", "ts": "2026-09-15T21:43:34.226438+00:00",
 "decision_type": "disputed_choice", "klal_id": 2, "word_index": 3,
 "chosen_source": "docai_reading", "chosen_text": "בדיקה",
 "candidate_snapshot": {"word_index": 3, "original_word": "חית", "word_occurrence": 1,
                        "docai_reading": "חתי", "final_text": "חית", "bbox": {…}, …},
 "needs_revisit": null, "note": "sandbox test", "reviewer": "local",
 "actor": {"kind": "human", "id": "local", "display": "Unidentified local reviewer",
           "via": "review-dashboard", "verified": false},
 "applied_decision_id": null, "supersedes": null}
```

- `ts` is in UTC.
- `decision_type` is one of `disputed_choice` (older records say
  `candidate_choice`, which means the same), `manual_correction`,
  `witness_choice`, `punctuation_choice`, `klal_flag` or `title_correction`.
- The ledger also holds `apply_event` records, written by the apply step and
  never by this API.

### `POST /api/decisions/disputed`

```json
{"klal_id": 2, "word_index": 3, "chosen_source": "docai_reading", "chosen_text": "חתי", "note": "…"}
```

This rules on a `queue` entry whose opcode is `replace`, `insert`, `delete` or
`ai_flag`.

- **`chosen_text` is required.** `null` is a `400`. An empty string is a real
  answer: the word is removed, or a proposed insertion is rejected.
- **`chosen_source`** names where the chosen reading came from. It is the name
  of the queue-entry field (`final_text`, `docai_reading`,
  `vision_transcription`, `vlm_reading`, `surya_reading`, `dicta_reading`,
  `lexical_proposal`), or `custom`.
- **What the HTML page sends** (`saveDisputedDecision` in app.js):

  | The reviewer chose | `chosen_source` | `chosen_text` |
  |---|---|---|
  | keep our word | `final_text` | our word |
  | an engine's reading | that field's name | that reading |
  | typed text, or a suggestion | `custom` | the text |
  | remove the word (`insert`) | `custom` | `""` |
  | reject the proposed insertion (`delete`) | `final_text` | `""` |
- **A ruling on a flagged word answers the flag.** Its `word_flag.answered`
  turns true. To close the flag itself, see `klal_flag`.

### `POST /api/decisions/manual`

```json
{"klal_id": 2, "word_index": 2, "chosen_text": "זין", "original_word": "זין", "note": "…"}
```

This corrects any word, flagged or not.
- `chosen_text` is required and trimmed. An empty string deletes the word.
- `word_index` must be 0 or more.
- **Always send `original_word`**: the word you showed at `word_index`. It is
  the ruling's check against the text. If it is missing, or no longer matches
  the word now at that index, the ruling is not drawn on the word. It appears
  in `stranded_rulings` instead. This was tested on the fixture, with
  `original_word` left out.
- The server refuses this type unless its own identity is a human reviewer.

### `POST /api/decisions/witness`

```json
{"klal_id": 4, "docai_token_index": 16, "chosen_source": "docai_reading", "chosen_text": "עין", "note": "…"}
```

- **The key is the item's `docai_token_index`, not its `word_index`.** The
  stored record's top-level `word_index` holds that token index. The word's
  position in the text is `candidate_snapshot.word_index`. Reading the
  top-level `word_index` of a witness ruling as a word position points at the
  wrong word.
- **`chosen_source`** takes one of these values:

  | Value | Reading chosen |
  |---|---|
  | `docai_reading` | Keep ours |
  | `tesseract_reading` | The witness's reading. The field keeps that name whatever engine the witness is: see `witness_name`. |
  | `corrected_reading` | The witness's corrected text, for an entry it has reviewed |
  | `custom` | Typed text |
  | `unreadable` | Empty, and changes nothing |
  | `remove` | Empty, and deletes our word when applied |
- This route does not refuse a `null` `chosen_text` the way the others do.
  Always send a string.

### `POST /api/decisions/punctuation`

```json
{"klal_id": 2, "before_word_index": 3, "accepted": true, "note": "…"}
```

This accepts or rejects a proposed sentence break before a word.

### `POST /api/decisions/klal_flag`

```json
{"klal_id": 2, "word_index": 3, "needs_revisit": true, "note": "look again"}
```

- Leave out `word_index` (or send `null`) to flag the entry itself.
- To clear a flag, post to the same address with `needs_revisit: false`.

### `POST /api/decisions/title`

```json
{"klal_id": 2, "word_index": 0, "chosen_text": "וו.", "note": "…"}
{"klal_id": 2, "word_index": 0, "whole": true, "chosen_text": "וו זין.", "note": "…"}
```

- **A word-level ruling.** `word_index` counts the heading's words
  (`title.split(' ')`), not the body's: heading word 2 and body word 2 are
  different addresses. An index past the heading's last word is a `400`, and an
  empty `chosen_text` deletes the word. The last word carries the heading's
  closing period, so a retyped word without it is a different word.
- **A whole-heading ruling.** With `whole: true`, `chosen_text` is the entire
  new heading, which cannot be empty, and it is recorded at index 0. This is
  how a heading that swallowed body text gets trimmed.
- **Replacing a ruling.** A new heading ruling at the address of an earlier one
  fills in `supersedes` with the earlier one's id.

## The HTML dashboard, for reference

The HTML page's behaviour lives in `review_frontend/app.js`:

| Function | What it does |
|---|---|
| `renderKlalBody` | Draws the text pane |
| `wordState` | Picks each word's colour |
| `markTitleRun`, `markFootnoteRefs` | Draw the heading and the raised numerals |
| `renderAltBody` | Draws the compare views |
| `saveDisputedDecision`, `saveWitnessDecision`, `openManualCorrectionPanel` | Record rulings |

`tests/test_review_server.py` drives that page in a browser against the fixture
corpus. It is a record of expected behaviour, but it will not test another
client.

## Keeping this file true

`test_review_api_doc_names_every_route_and_only_real_ones` in
`tests/test_pipeline_logic.py` fails in two cases:
- a route is added to or removed from `review_server.py` without this file
  following;
- this file names an `/api/` route the server does not serve.

The samples are not checked. If a response shape changes, record them again
from the fixture.
