# Deployment Guide

**Default recommendation: self-host first.** See [`SELF-HOST.md`](./SELF-HOST.md).

UAP Cloud is designed as optional hosted telemetry — the SDK runs fully local. Deploy on your own VPS with Coolify + Docker for **< $15/month**.

---

## Primary path: Self-host (recommended)

```bash
# From repo root
docker compose up --build
```

Stack: Postgres + Redis + API + Dashboard.

Production: Hetzner VPS + Coolify + Cloudflare. Full guide in [`SELF-HOST.md`](./SELF-HOST.md).

---

## Why not Fly.io first?

Fly.io is excellent for global edge and multi-region — but UAP at Stage 0 does not need that.

| Need | Stage 0 | Fly.io |
|------|---------|--------|
| Cost | < $15/mo | Usage-based, can grow |
| On-prem story | `docker compose up` | Cloud-only |
| Enterprise | Self-host option | Harder |
| Ops complexity | 1 VPS + Coolify | Platform-specific |

Use Fly/Railway/AWS **later** if you want managed hosting without running a VPS.

---

## Optional: managed cloud targets

Configs in `web/deploy/` (legacy / optional):

### Railway (fastest click-ops)

```bash
railway init
railway up
railway variables set UAP_DATABASE_URL=postgresql+psycopg2://...
railway variables set UAP_BILLING_MODE=mock
```

### Fly.io (if you want edge later)

```bash
fly launch --copy-config --config web/deploy/fly.toml
fly secrets set UAP_DATABASE_URL=postgresql+psycopg2://...
fly deploy --config web/deploy/fly.toml
```

### AWS App Runner (enterprise posture)

See `web/deploy/aws-apprunner.yaml`.

---

## Production env vars

### Core

- `UAP_DATABASE_URL` (Postgres)
- `UAP_REDIS_URL` (Redis)
- `UAP_BILLING_MODE` (`mock` | `stripe`)
- `UAP_RATE_LIMIT_PER_MIN`
- `UAP_CLOUD_CORS_ORIGIN`
- `SENTRY_DSN` (optional)

### Stripe (card)

- `STRIPE_API_KEY`
- `STRIPE_PRICE_ID_PRO` / `TEAM` / `BUSINESS`
- `STRIPE_SUCCESS_URL` / `STRIPE_CANCEL_URL`
- `STRIPE_WEBHOOK_SECRET`

### Crypto (multi-chain)

- `UAP_CRYPTO_MODE` (`mock` | `live`)
- `UAP_CRYPTO_RECEIVER_WALLET`
- `UAP_CRYPTO_BOT_ENABLED`
- `UAP_ETH_RPC_URL`
- `UAP_POLYGON_RPC_URL`
- `UAP_BASE_RPC_URL`
- `UAP_ARBITRUM_RPC_URL`
- `UAP_BSC_RPC_URL`

---

## Summary

| Priority | Target | Cost |
|----------|--------|------|
| **1 (now)** | Self-host (Hetzner + Coolify) | ~$5–15/mo |
| 2 | Railway | Usage-based |
| 3 | Fly.io | Edge / multi-region |
| 4 | AWS | Enterprise scale |

90% of value is in SDK + Spec. Cloud is the upsell — not the product.
