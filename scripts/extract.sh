#!/usr/bin/env bash
# Extract source material from the Dominions 6 manual PDF for transcription.
# Outputs land under assets/raw/ (gitignored). Idempotent: skips download if present.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PDF="$ROOT/assets/dom6manual.pdf"
RAW="$ROOT/assets/raw"
URL="https://www.illwinter.com/dom6/dom6manual.pdf"

mkdir -p "$RAW"/{text,pages,images}

if [[ ! -f "$PDF" ]]; then
  echo "Downloading manual..."
  curl -fSL "$URL" -o "$PDF"
fi

echo "== pdfinfo =="
pdfinfo "$PDF" | tee "$RAW/info.txt"

echo "== outline / bookmarks =="
# Embedded TOC; drives chapter structure.
pdftotext -bbox-layout "$PDF" "$RAW/_bbox.html" >/dev/null 2>&1 || true
if pdfinfo -help 2>&1 | grep -q outline; then :; fi
# dump bookmarks via pdftk-free fallback using poppler's mutool if absent; use pdftotext page-by-page TOC instead
python3 "$ROOT/scripts/dump_outline.py" "$PDF" > "$RAW/outline.txt" || echo "(outline dump skipped)"

echo "== per-page text (-layout) =="
pages=$(pdfinfo "$PDF" | awk '/^Pages:/{print $2}')
echo "Pages: $pages"
for p in $(seq 1 "$pages"); do
  pdftotext -layout -f "$p" -l "$p" "$PDF" "$RAW/text/$(printf 'page%03d' "$p").txt"
done

echo "== per-page PNG reference (150 dpi) =="
pdftoppm -png -r 150 "$PDF" "$RAW/pages/page"

echo "== embedded images =="
pdfimages -png "$PDF" "$RAW/images/img"

echo "Done. text/$(ls "$RAW/text" | wc -l) pages, images/$(ls "$RAW/images" | wc -l) files."
