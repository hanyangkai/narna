#!/usr/bin/env bash
# Build portable NARNA-Desktop macOS folder (PyInstaller)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> install build deps"
python3 -m pip install -q -e ".[desktop]" pyinstaller

echo "==> pyinstaller"
cd desktop
python3 -m PyInstaller --noconfirm --clean narna-desktop.spec
cd "$ROOT"

OUT="$ROOT/desktop/dist/NARNA-Desktop"
BIN="$OUT/NARNA-Desktop"
if [[ ! -f "$BIN" ]]; then
  echo "Build failed — binary missing at $BIN" >&2
  exit 1
fi

cp desktop/README.md "$OUT/README.md"
cat > "$OUT/START-HERE.txt" <<'EOF'
NARNA Desktop (portable)

1. Double-click NARNA-Desktop (or run ./NARNA-Desktop in Terminal)
2. Browser opens http://127.0.0.1:8765/
3. Paste OpenRouter / OpenAI / Ollama key (saved under ~/.narna)

No Python install required.
EOF

mkdir -p dist
ZIP="dist/NARNA-Desktop-macos.zip"
rm -f "$ZIP"
(cd desktop/dist && zip -r "$ROOT/$ZIP" NARNA-Desktop)
echo "OK: $ZIP"
echo "Run: $BIN"
