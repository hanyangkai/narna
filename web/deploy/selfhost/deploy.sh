#!/usr/bin/env bash
# Deploy UAP Cloud on a VPS (Hetzner + Coolify or plain Docker).
# Usage: ./web/deploy/selfhost/deploy.sh [--build]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
COMPOSE_FILE="${ROOT}/web/deploy/selfhost/docker-compose.prod.yml"
ENV_FILE="${ROOT}/web/deploy/selfhost/.env"

cd "${ROOT}"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "[UAP] Missing ${ENV_FILE}"
  echo "      Copy web/deploy/selfhost/.env.production.example → web/deploy/selfhost/.env"
  exit 1
fi

BUILD_FLAG=""
if [[ "${1:-}" == "--build" ]]; then
  BUILD_FLAG="--build"
fi

echo "[UAP] Pulling images / building..."
docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" up -d ${BUILD_FLAG}

echo "[UAP] Waiting for API health..."
for i in $(seq 1 30); do
  if curl -sf http://127.0.0.1:8000/v1/health >/dev/null 2>&1; then
    echo "[UAP] API healthy"
    break
  fi
  sleep 2
  if [[ "$i" -eq 30 ]]; then
    echo "[UAP] API did not become healthy in time"
    docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" ps
    exit 1
  fi
done

echo "[UAP] Stack running:"
echo "  API:       http://127.0.0.1:8000/v1/health"
echo "  Dashboard: http://127.0.0.1:5173"
echo ""
echo "Coolify: point your domain to this VPS and use compose file:"
echo "  web/deploy/selfhost/docker-compose.prod.yml"
