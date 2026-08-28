#!/usr/bin/env bash
set -euo pipefail
KEY="${1:-/c/DAO/.deploy-secrets/hetzner_963x_nopass}"
HOST="${2:-root@46.62.163.209}"
ssh -i "$KEY" -o BatchMode=yes "$HOST" bash -s <<'REMOTE'
for v in UAP_CRYPTO_MODE UAP_BILLING_MODE UAP_TELEGRAM_BOT_TOKEN UAP_ROUTER_PROVIDER UAP_CRYPTO_BOT_ENABLED; do
  len=$(docker exec selfhost-api-1 printenv "$v" 2>/dev/null | wc -c || echo 0)
  echo "$v length=$len"
done
grep -E '^UAP_TELEGRAM_BOT_TOKEN=' /opt/narna/web/deploy/selfhost/.env 2>/dev/null | awk -F= '{print ".env UAP_TELEGRAM_BOT_TOKEN length=" length($2)}' || echo ".env telegram line missing"
REMOTE
