#!/usr/bin/env bash
# Enable Telegram gateway on Hetzner VPS.
# Usage:
#   TELEGRAM_BOT_TOKEN='123:ABC…' ./scripts/vps_enable_telegram.sh
# Optional:
#   UAP_TELEGRAM_WEBHOOK_SECRET=… HOST=root@46.62.163.209 SSH_KEY=…
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOST="${HOST:-root@46.62.163.209}"
TOKEN="${TELEGRAM_BOT_TOKEN:-}"
WEBHOOK_SECRET="${UAP_TELEGRAM_WEBHOOK_SECRET:-}"

if [[ -z "$TOKEN" ]]; then
  echo "Set TELEGRAM_BOT_TOKEN (from @BotFather)" >&2
  exit 1
fi

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
  echo "missing SSH key: $KEY" >&2
  exit 2
fi

SSH=(ssh -i "$KEY" -o BatchMode=yes -o StrictHostKeyChecking=accept-new)

echo "==> patch .env on $HOST"
"${SSH[@]}" "$HOST" \
  "TOKEN=$(printf '%q' "$TOKEN") WEBHOOK_SECRET=$(printf '%q' "$WEBHOOK_SECRET") bash -s" <<'REMOTE'
set -euo pipefail
ENV=/opt/narna/web/deploy/selfhost/.env
touch "$ENV"
python3 - <<'PY'
from pathlib import Path
import os
p = Path("/opt/narna/web/deploy/selfhost/.env")
lines = p.read_text(encoding="utf-8").splitlines() if p.exists() else []
kv = {}
for line in lines:
    s = line.strip()
    if not s or s.startswith("#") or "=" not in s:
        continue
    k, _, v = s.partition("=")
    kv[k.strip()] = v.strip()
kv["UAP_TELEGRAM_BOT_TOKEN"] = os.environ["TOKEN"]
if os.environ.get("WEBHOOK_SECRET"):
    kv["UAP_TELEGRAM_WEBHOOK_SECRET"] = os.environ["WEBHOOK_SECRET"]
out = []
seen = set()
for line in lines:
    s = line.strip()
    if not s or s.startswith("#") or "=" not in s:
        out.append(line)
        continue
    k = s.split("=", 1)[0].strip()
    if k in kv:
        out.append(f"{k}={kv[k]}")
        seen.add(k)
    else:
        out.append(line)
for k, v in kv.items():
    if k not in seen:
        out.append(f"{k}={v}")
p.write_text("\n".join(out) + "\n", encoding="utf-8")
print("patched", sorted(kv.keys()))
PY
REMOTE

echo "==> redeploy with gateway profile"
"${SSH[@]}" "$HOST" "cd /opt/narna/web/deploy/selfhost && docker compose -f docker-compose.vps.yml --profile gateway up -d --build api gateway"

echo "==> wait api healthy"
"${SSH[@]}" "$HOST" 'for i in $(seq 1 30); do
  st=$(docker inspect -f "{{.State.Health.Status}}" selfhost-api-1 2>/dev/null || echo starting)
  [ "$st" = healthy ] && break
  sleep 3
done'

echo "==> gateway status"
"${SSH[@]}" "$HOST" 'python3 - <<"PY"
import json, urllib.request
with urllib.request.urlopen("http://127.0.0.1:8100/v1/agent/gateway/status", timeout=15) as r:
    g = json.loads(r.read().decode())
print("telegram", g.get("channels", {}).get("telegram"))
print("running", g.get("running"))
PY'

echo "OK — open your bot in Telegram and send /start or a message"
