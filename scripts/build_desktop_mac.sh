#!/usr/bin/env bash
# Build portable NARNA-Desktop macOS folder (PyInstaller)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PY="${NARNA_BUILD_PYTHON:-}"
if [[ -z "$PY" ]]; then
  for c in python3.12 python3.11 python3; do
    if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
      PY="$c"
      break
    fi
  done
fi
if [[ -z "$PY" ]]; then
  echo "Need Python 3.11+. Set NARNA_BUILD_PYTHON or install python3.11." >&2
  exit 1
fi
echo "==> using $PY ($($PY -V))"

echo "==> install build deps"
"$PY" -m pip install -q -e ".[desktop]" pyinstaller

echo "==> pyinstaller"
cd desktop
"$PY" -m PyInstaller --noconfirm --clean narna-desktop.spec
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

If macOS says the app is damaged / cannot be opened (Gatekeeper):
  the zip is not Apple-notarized yet. Clear quarantine first:

  xattr -cr "$(pwd)"
  chmod +x ./NARNA-Desktop
  ./NARNA-Desktop

Or: Right-click NARNA-Desktop → Open → Open.

Then:
1. Browser opens http://127.0.0.1:8765/
2. Login Claude CLI / Codex CLI, or paste API key (BYOK → ~/.narna)
3. Pair phone via QR (optional)

Alternative without zip:  pip install "narna[desktop]" && narna desktop
EOF

mkdir -p dist
ZIP="dist/NARNA-Desktop-macos.zip"
rm -f "$ZIP"
(cd desktop/dist && zip -r "$ROOT/$ZIP" NARNA-Desktop)
echo "OK: $ZIP"
echo "Run: $BIN"
