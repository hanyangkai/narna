#!/usr/bin/env bash
# Print NARNA social webhook URLs and optional VPS channel status.
# Usage: ./scripts/vps_social_webhooks.sh
#   HOST=root@46.62.163.209 SSH_KEY=… ./scripts/vps_social_webhooks.sh --check
set -euo pipefail

API_BASE="${NARNA_API_BASE:-https://api.narna.org}"
CHECK="${1:-}"

echo "NARNA social webhook URLs (register at each platform):"
echo ""
printf "  Telegram:   %s/v1/agent/telegram/webhook\n" "$API_BASE"
printf "  WhatsApp:   %s/v1/agent/whatsapp/webhook\n" "$API_BASE"
printf "  Discord:    %s/v1/agent/discord/webhook\n" "$API_BASE"
printf "  Slack:      %s/v1/agent/slack/events\n" "$API_BASE"
printf "  X:          %s/v1/agent/x/webhook\n" "$API_BASE"
printf "  Facebook:   %s/v1/agent/facebook/webhook\n" "$API_BASE"
printf "  Instagram:  %s/v1/agent/instagram/webhook\n" "$API_BASE"
printf "  YouTube:    %s/v1/agent/youtube/webhook\n" "$API_BASE"
echo ""
echo "Docs: docs/SOCIAL-CHANNELS.md"
echo "CLI:  narna gateway channels"

if [[ "$CHECK" != "--check" ]]; then
  exit 0
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOST="${HOST:-root@46.62.163.209}"
if [[ -z "${SSH_KEY:-}" ]]; then
  if [[ -f "$ROOT/.deploy-secrets/hetzner_963x_nopass" ]]; then
    KEY="$ROOT/.deploy-secrets/hetzner_963x_nopass"
  elif [[ -f "$HOME/.ssh/hetzner_963x_nopass" ]]; then
    KEY="$HOME/.ssh/hetzner_963x_nopass"
  else
    KEY="$ROOT/.deploy-secrets/hetzner_narna_deploy"
  fi
else
  KEY="$SSH_KEY"
fi

if [[ ! -f "$KEY" ]]; then
  echo "SSH key not found — skip VPS check" >&2
  exit 0
fi

echo ""
echo "==> VPS gateway status ($HOST)"
ssh -i "$KEY" -o BatchMode=yes -o StrictHostKeyChecking=accept-new "$HOST" \
  'python3 - <<"PY"
import json, urllib.request
try:
    with urllib.request.urlopen("http://127.0.0.1:8100/v1/agent/gateway/status", timeout=15) as r:
        g = json.loads(r.read().decode())
    print("configuredCount", g.get("configuredCount"), "/", g.get("totalCount"))
    for cid, ch in sorted((g.get("channels") or {}).items()):
        if ch.get("configured"):
            print(" ", cid, ch.get("mode"), ch.get("tier"))
except Exception as e:
    print("gateway status unavailable:", e)
PY'
