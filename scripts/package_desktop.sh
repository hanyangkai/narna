#!/usr/bin/env bash
# Build a portable NARNA Desktop zip for GitHub Releases
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-$ROOT/dist/narna-desktop}"
rm -rf "$OUT"
mkdir -p "$OUT"
cp -R "$ROOT/desktop/"* "$OUT/"
cp "$ROOT/docs/DESKTOP.md" "$OUT/"
# strip CR for shell scripts
if command -v sed >/dev/null 2>&1; then
  sed -i 's/\r$//' "$OUT/install.sh" 2>/dev/null || true
fi
(cd "$(dirname "$OUT")" && zip -r "narna-desktop.zip" "$(basename "$OUT")")
echo "built: $(dirname "$OUT")/narna-desktop.zip"
