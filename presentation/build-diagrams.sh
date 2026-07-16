#!/usr/bin/env bash
# Render diagrams/*.mmd -> shots/*.svg with mermaid-cli.
#
# The .mmd files are the source of truth; the SVGs are generated. Uses the
# system chromium (mermaid-cli would otherwise download its own).
set -euo pipefail
cd "$(dirname "$0")"
MMDC="${MMDC:-$(command -v mmdc || true)}"
[ -z "$MMDC" ] && { echo "mmdc not found. npm i -g @mermaid-js/mermaid-cli (PUPPETEER_SKIP_DOWNLOAD=1)"; exit 1; }
export PUPPETEER_EXECUTABLE_PATH="${PUPPETEER_EXECUTABLE_PATH:-$(command -v chromium || command -v chromium-browser)}"
echo '{"args":["--no-sandbox","--disable-gpu"]}' > /tmp/pptr-vo.json
for f in diagrams/*.mmd; do
  n="$(basename "$f" .mmd)"
  "$MMDC" -i "$f" -o "shots/$n.svg" -c diagrams/mermaid-config.json -b transparent -p /tmp/pptr-vo.json --quiet
  echo "  shots/$n.svg"
done
