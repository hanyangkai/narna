#!/usr/bin/env bash
# NARNA Agent installer — Hermes-style one-liner
#   curl -fsSL https://raw.githubusercontent.com/hanyangkai/narna/main/scripts/install.sh | bash
set -euo pipefail

echo "==> NARNA Agent install"
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3.11+ required. Install from python.org or brew install python@3.12" >&2
  exit 1
fi
python3 - <<'PY'
import sys
if sys.version_info < (3, 11):
    raise SystemExit("Python 3.11+ required")
PY

echo "==> pip install narna[desktop]"
python3 -m pip install --upgrade "narna[desktop]" || {
  echo "PyPI install failed — clone https://github.com/hanyangkai/narna and pip install -e '.[desktop]'" >&2
  exit 1
}

BIN="${HOME}/.local/bin"
mkdir -p "$BIN"
cat > "$BIN/narna-desktop" <<'EOF'
#!/usr/bin/env bash
exec narna desktop "$@"
EOF
chmod +x "$BIN/narna-desktop"

mkdir -p "${HOME}/.narna"
echo ""
echo "✓ NARNA Agent installed"
echo ""
echo "  Start:     narna desktop"
echo "  Daemon:    narna desktop --daemon --gateway"
echo "  Browser:   narna browser setup"
echo "  Service:   narna daemon install   (macOS/Linux)"
echo "  Data:      ~/.narna"
echo ""
if [[ ":$PATH:" != *":$BIN:"* ]]; then
  echo "Add to PATH:  export PATH=\"$BIN:\$PATH\""
fi
