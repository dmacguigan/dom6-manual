#!/usr/bin/env bash
# Dump a page range in two-column reading order (left column then right column).
# Usage: scripts/cols.sh FIRST LAST   e.g. scripts/cols.sh 6 12
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PDF="$ROOT/assets/dom6manual.pdf"
first="$1"; last="$2"
for p in $(seq "$first" "$last"); do
  echo "########## PAGE $p (LEFT) ##########"
  pdftotext -f "$p" -l "$p" -x 0   -y 0 -W 300 -H 792 "$PDF" - 2>/dev/null | sed '/^[[:space:]]*$/d'
  echo "########## PAGE $p (RIGHT) ##########"
  pdftotext -f "$p" -l "$p" -x 305 -y 0 -W 307 -H 792 "$PDF" - 2>/dev/null | sed '/^[[:space:]]*$/d'
done
