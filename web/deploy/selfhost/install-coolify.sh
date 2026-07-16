# Coolify one-time VPS bootstrap (Ubuntu 24.04+)
# Run on fresh Hetzner CX22 as root or sudo user.
set -euo pipefail

echo "[UAP] Installing Docker if missing..."
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
  usermod -aG docker "${SUDO_USER:-$USER}" || true
fi

echo "[UAP] Installing Coolify..."
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash

echo "[UAP] Coolify installed."
echo "Open Coolify UI on port 8000 (or configured port)."
echo ""
echo "Next steps in Coolify:"
echo "  1. Add Git repository"
echo "  2. Create Docker Compose resource"
echo "  3. Compose path: web/deploy/selfhost/docker-compose.prod.yml"
echo "  4. Env file: copy web/deploy/selfhost/.env.production.example"
echo "  5. Point Cloudflare DNS → this VPS IP"
echo "  6. Enable HTTPS via Coolify Traefik"
