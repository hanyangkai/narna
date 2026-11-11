#!/usr/bin/env bash
# Clear Apple quarantine so unsigned NARNA-Desktop (GitHub zip) can launch.
# Usage:
#   bash scripts/macos_fix_gatekeeper.sh ~/Downloads/NARNA-Desktop
#   bash scripts/macos_fix_gatekeeper.sh ./NARNA-Desktop
set -euo pipefail

TARGET="${1:-}"
if [[ -z "$TARGET" ]]; then
  echo "Usage: $0 /path/to/NARNA-Desktop   # folder OR the NARNA-Desktop binary" >&2
  exit 2
fi

if [[ ! -e "$TARGET" ]]; then
  echo "Not found: $TARGET" >&2
  exit 1
fi

# If user pointed at the binary, use its parent folder too
if [[ -f "$TARGET" ]]; then
  DIR="$(cd "$(dirname "$TARGET")" && pwd)"
  BIN="$TARGET"
else
  DIR="$(cd "$TARGET" && pwd)"
  BIN="$DIR/NARNA-Desktop"
fi

echo "==> Removing quarantine from: $DIR"
xattr -cr "$DIR" 2>/dev/null || true

if [[ -f "$BIN" ]]; then
  chmod +x "$BIN"
  echo "==> Launching $BIN"
  exec "$BIN"
fi

echo "Binary not found at $BIN — quarantine cleared; open NARNA-Desktop manually."
