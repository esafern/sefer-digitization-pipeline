#!/bin/bash
# Poll a RashiOCR job id until its .txt is ready, then save it.
# Usage: tools/fetch_dicta_result.sh <job-id> <output-name>
set -u
if [ $# -ne 2 ]; then
  echo "usage: $0 <job-id> <output-filename>" >&2
  echo "  job id is the ?id= on the RashiOCR status page" >&2
  exit 2
fi
ID="$1"; OUT="dicta_output/$2"
mkdir -p dicta_output
TMP=$(mktemp "${TMPDIR:-/tmp}/dicta.XXXXXX") || exit 1
trap 'rm -f "$TMP"' EXIT
for i in $(seq 1 30); do
  code=$(curl -sS -o "$TMP" -w "%{http_code}" --max-time 30 \
    "https://rashiocr.dicta.org.il/api/results/$ID/${ID}_ocr.txt")
  if [ "$code" = "200" ]; then
    # Only a non-empty body counts: a 200 carrying nothing would otherwise be
    # saved as a "successful" empty baseline and silently score as total failure.
    if [ -s "$TMP" ]; then
      # A 200 is not proof of OCR text: a maintenance or error page is also a
      # non-empty 200, and saving one as a "successful" result would score as a
      # total OCR failure with nothing to say why. Require actual Hebrew.
      # $'...' so the shell emits real bytes: Hebrew is U+05xx, whose UTF-8
      # lead byte is 0xD6 or 0xD7. A BRE '\xd7' would match the literal text.
      if ! LC_ALL=C grep -q $'[\xd6\xd7]' "$TMP"; then
        echo "FAILED: 200 but the body contains no Hebrew - not an OCR result" >&2
        head -c 200 "$TMP" >&2; echo >&2
        exit 1
      fi
      if ! mv "$TMP" "$OUT"; then
        echo "FAILED to save $OUT (missing directory, or not writable from $(pwd))" >&2
        exit 1
      fi
      trap - EXIT
      echo "OK $2 ($(wc -c <"$OUT" | tr -d ' ') bytes)"; exit 0
    fi
    echo "200 but empty body - still generating, waiting" >&2
  fi
  sleep 10
done
echo "TIMEOUT $ID (5 min); the job may still be running - re-run this script" >&2
exit 1
