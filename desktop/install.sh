#!/usr/bin/env bash
# NARNA Desktop installer — macOS / Linux
set -euo pipefail
echo "==> NARNA Desktop install"
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3.11+ required" >&2
  exit 1
fi
python3 - <<'PY'
import sys
raise SystemExit(0 if sys.version_info >= (3, 11) else 1)
PY

echo "==> pip install narna[desktop]"
if ! python3 -m pip install --upgrade "narna[desktop]"; then
  ROOT="$(cd "$(dirname "$0")/.." && pwd)"
  if [[ -f "$ROOT/pyproject.toml" ]]; then
    python3 -m pip install -e "$ROOT[desktop]"
  else
    exit 1
  fi
fi

BIN="${HOME}/.local/bin"
mkdir -p "$BIN"
cat > "$BIN/narna-desktop" <<'EOF'
#!/usr/bin/env bash
exec python3 -m uap.desktop_app "$@"
EOF
chmod +x "$BIN/narna-desktop"

echo ""
echo "Installed. Run:  narna desktop"
echo "Or:              narna-desktop"
echo "Data folder:     ${HOME}/.narna"
if [[ ":$PATH:" != *":$BIN:"* ]]; then
  echo "Add to PATH:     export PATH=\"$BIN:\$PATH\""
fi
