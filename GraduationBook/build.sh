#!/usr/bin/env bash
# ============================================================
#  build.sh - compile the LaTeX book to PDF
#  Finds main.tex in this script's own folder and builds it.
#  Engine preference: tectonic -> latexmk -> pdflatex
# ============================================================
set -euo pipefail

# Directory this script lives in (so it works from anywhere)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
cd "$SCRIPT_DIR"

MAIN="main.tex"
if [[ ! -f "$MAIN" ]]; then
  echo "[ERROR] $MAIN not found in $SCRIPT_DIR" >&2
  exit 1
fi
echo "[build] Found $MAIN in $SCRIPT_DIR"

# ---- locate a compiler -------------------------------------
ENGINE=""
if command -v tectonic >/dev/null 2>&1; then
  ENGINE="tectonic"
elif [[ -x "/c/tmp/tectonic.exe" ]]; then
  ENGINE="/c/tmp/tectonic.exe"
elif command -v latexmk >/dev/null 2>&1; then
  ENGINE="latexmk"
elif command -v pdflatex >/dev/null 2>&1; then
  ENGINE="pdflatex"
fi

if [[ -z "$ENGINE" ]]; then
  echo "[ERROR] No LaTeX engine found (tectonic, latexmk, or pdflatex)." >&2
  echo "        Install one, or upload the folder to Overleaf." >&2
  exit 1
fi
echo "[build] Using engine: $ENGINE"

# ---- clean stale auxiliary files (deterministic pagination) -
rm -f main.aux main.toc main.lof main.lot main.out main.log main.xdv \
      chapters/*.aux 2>/dev/null || true

# ---- compile ------------------------------------------------
case "$ENGINE" in
  *tectonic*)
    "$ENGINE" -X compile "$MAIN" --outdir "$SCRIPT_DIR"
    ;;
  *latexmk*)
    latexmk -pdf -interaction=nonstopmode -halt-on-error "$MAIN"
    ;;
  *pdflatex*)
    # two passes for TOC + cross-references
    pdflatex -interaction=nonstopmode -halt-on-error "$MAIN"
    pdflatex -interaction=nonstopmode -halt-on-error "$MAIN"
    ;;
esac

if [[ -f "main.pdf" ]]; then
  echo "[build] SUCCESS -> $SCRIPT_DIR/main.pdf"
else
  echo "[build] FAILED - main.pdf was not produced. See the log above." >&2
  exit 1
fi
