#!/usr/bin/env bash
# Configure NARNA transactional email via Resend on VPS.
# Uses RESEND_API_KEY from /opt/963x/.env if present, else $RESEND_API_KEY.
set -euo pipefail

ENV_FILE="${ENV_FILE:-/opt/narna/web/deploy/selfhost/.env}"
FROM_DEFAULT='NARNA <noreply@99x.exchange>'
SITE_URL="${UAP_SITE_URL:-https://narna.org}"

if [ -z "${RESEND_API_KEY:-}" ] && [ -f /opt/963x/.env ]; then
  RESEND_API_KEY=$(grep "^RESEND_API_KEY=" /opt/963x/.env | cut -d= -f2- | tr -d '"' | tr -d "'")
fi

if [ -z "${RESEND_API_KEY:-}" ]; then
  echo "RESEND_API_KEY missing — set env or add to /opt/963x/.env"
  exit 1
fi

FROM_ADDR="${UAP_RESEND_FROM:-$FROM_DEFAULT}"
mkdir -p "$(dirname "$ENV_FILE")"
touch "$ENV_FILE"

upsert() {
  local key="$1" val="$2"
  if grep -q "^${key}=" "$ENV_FILE"; then
    sed -i "s|^${key}=.*|${key}=${val}|" "$ENV_FILE"
  else
    echo "${key}=${val}" >> "$ENV_FILE"
  fi
}

upsert UAP_RESEND_API_KEY "$RESEND_API_KEY"
upsert UAP_RESEND_FROM "$FROM_ADDR"
upsert UAP_SITE_URL "$SITE_URL"

echo "patched $ENV_FILE (Resend from: $FROM_ADDR)"

# Show narna.org DNS status if domain exists in Resend
curl -sS -H "Authorization: Bearer $RESEND_API_KEY" https://api.resend.com/domains \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
for dom in d.get('data', []):
    if dom.get('name') == 'narna.org':
        print('narna.org Resend status:', dom.get('status'))
        break
else:
    print('narna.org not in Resend — add at https://resend.com/domains')
"

echo "Restart: cd /opt/narna/web/deploy/selfhost && docker compose -f docker-compose.vps.yml up -d api"
