#!/usr/bin/env bash
# Deploy NARNA Ask Agent to Hetzner VPS (/opt/narna).
# Usage:
#   SSH_KEY=path/to/key ./scripts/deploy_vps_agent.sh
#   HOST=root@46.62.163.209 SSH_KEY=... ./scripts/deploy_vps_agent.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOST="${HOST:-root@46.62.163.209}"
# Prefer working Hetzner key (963x); fall back to legacy name
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
REMOTE_DIR="${REMOTE_DIR:-/opt/narna}"

if [[ ! -f "$KEY" ]]; then
  echo "missing SSH key: $KEY" >&2
  exit 2
fi

echo "==> packing tree (no .git / node_modules / secrets)"
TAR="$(mktemp -t narna-deploy.XXXXXX.tar.gz)"
tar -C "$ROOT" -czf "$TAR" \
  --exclude='.git' \
  --exclude='node_modules' \
  --exclude='.deploy-secrets' \
  --exclude='**/__pycache__' \
  --exclude='.pytest_cache' \
  --exclude='web/frontend/dist' \
  .

SSH=(ssh -i "$KEY" -o BatchMode=yes -o StrictHostKeyChecking=accept-new)
SCP=(scp -i "$KEY" -o BatchMode=yes -o StrictHostKeyChecking=accept-new)

echo "==> upload + extract on $HOST:$REMOTE_DIR"
"${SCP[@]}" "$TAR" "$HOST:/tmp/narna-deploy.tar.gz"
"${SSH[@]}" "$HOST" "mkdir -p '$REMOTE_DIR' && tar -xzf /tmp/narna-deploy.tar.gz -C '$REMOTE_DIR' && rm -f /tmp/narna-deploy.tar.gz"
rm -f "$TAR"

echo "==> rebuild api + web (+ gateway profile if token set)"
"${SSH[@]}" "$HOST" "cd '$REMOTE_DIR/web/deploy/selfhost' && \
  if grep -qE '^UAP_TELEGRAM_BOT_TOKEN=.+' .env 2>/dev/null; then \
    docker compose -f docker-compose.vps.yml --profile gateway up -d --build api web gateway; \
  else \
    docker compose -f docker-compose.vps.yml up -d --build api web; \
  fi"

echo "==> wait health"
"${SSH[@]}" "$HOST" 'for i in $(seq 1 30); do
  st=$(docker inspect -f "{{.State.Health.Status}}" selfhost-api-1 2>/dev/null || echo starting)
  echo health=$st
  [ "$st" = healthy ] && exit 0
  sleep 3
done; exit 1'

echo "==> smoke Ask + gateway status"
"${SSH[@]}" "$HOST" 'python3 - <<"PY"
import json, urllib.request
req = urllib.request.Request(
    "http://127.0.0.1:8100/v1/agent/ask",
    data=json.dumps({"message": "prod smoke: should I proceed?"}).encode(),
    headers={"Content-Type": "application/json", "X-Narna-Device": "deploy-smoke"},
    method="POST",
)
with urllib.request.urlopen(req, timeout=60) as r:
    body = json.loads(r.read().decode())
print("dqs", body.get("dqs"), "tools", len(body.get("toolsUsed") or []), "session", body.get("sessionId"))
assert body.get("answer")
with urllib.request.urlopen("http://127.0.0.1:8100/v1/agent/gateway/status", timeout=15) as r:
    gw = json.loads(r.read().decode())
print("gateway tools", gw.get("toolCount"), "pairing", gw.get("pairingEnabled"), "tg", gw.get("telegramConfigured"))
assert int(gw.get("toolCount") or 0) >= 40
print("OK")
PY'

echo "done — set UAP_OPENROUTER_API_KEY + UAP_TELEGRAM_BOT_TOKEN on VPS for live LLM / phone"
# gateway profile: UAP_TELEGRAM_BOT_TOKEN in .env → compose --profile gateway
