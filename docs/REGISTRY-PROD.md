# Production Registry — registry.narna.dev

Deploy the NARNA Registry API + web console for public Agent Passport and Governance Package discovery.

## Architecture

```text
registry.narna.dev     → Caddy / Cloudflare → web (static)
api.registry.narna.dev → Caddy → api:8000 (FastAPI)
```

## Quick deploy (VPS / Coolify)

1. Copy `web/deploy/selfhost/.env.production.example` → `.env`
2. Set domains:

```env
NARNA_PUBLIC_URL=https://registry.narna.dev
NARNA_REGISTRY_URL=https://api.registry.narna.dev
UAP_CLOUD_CORS_ORIGIN=https://registry.narna.dev
```

3. Deploy:

```bash
cd web/deploy/selfhost
docker compose -f docker-compose.prod.yml up -d --build
```

4. Point DNS:
   - `registry.narna.dev` → VPS IP (web on :5173 or reverse proxy :443)
   - `api.registry.narna.dev` → VPS IP (API on :8000)

## Caddy example

```caddyfile
registry.narna.dev {
  reverse_proxy web:80
}

api.registry.narna.dev {
  reverse_proxy api:8000
}
```

## Publish from CLI

```bash
export NARNA_REGISTRY_URL=https://api.registry.narna.dev
export NARNA_REGISTRY_KEY=narna_live_...
narna publish --vap
narna package publish specs/examples/packages/eu-ai-act.yaml
```

## Health checks

```bash
curl https://api.registry.narna.dev/v1/health
curl https://api.registry.narna.dev/v1/compatibility/badges
curl https://api.registry.narna.dev/v1/benchmark/governance
```

## Moat surfaces enabled

| Surface | Endpoint |
|---------|----------|
| Agent Registry | `POST /v1/registry/publish` |
| Passport | `GET /v1/passport/{agentId}` |
| NARNA Score | `GET /v1/score/{agentId}` |
| Governance Packages | `GET /v1/packages` |
| Playground | `POST /v1/playground/validate` |

Network effect requires **public write + read** on registry with API keys for publishers.
