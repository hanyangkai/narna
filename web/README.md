# UAP Cloud — Web + API

OpenTelemetry for AI Agents — hosted audit console (optional). SDK runs fully local; self-host with `docker compose up`.

## Quick start (local)

### One command (self-host)

```bash
docker compose up --build
```

- API: http://localhost:8000/v1/health  
- Console: http://localhost:5173/console  

### Manual dev

```bash
cd web/backend && uvicorn app.main:app --reload --port 8000
cd web/frontend && npm install && npm run dev
```

Dev API key (first start): `uap_live_dev_local_key_change_in_prod`

### Push a run from SDK

```bash
pip install -e .
uap run --spec specs/examples/trading-agent.yaml --input "btc price"
uap push --run <runId> --cloud-key uap_live_dev_local_key_change_in_prod
```

## Deploy (production)

**Recommended:** Self-host on Hetzner VPS + Coolify (~$5–15/mo).  
See [`docs/SELF-HOST.md`](../docs/SELF-HOST.md).

Optional managed targets: [`docs/DEPLOYMENT.md`](../docs/DEPLOYMENT.md).

## Env

Copy `web/backend/.env.example` → `.env`.

| Variable | Description |
|----------|-------------|
| `UAP_DATABASE_URL` | Postgres URL |
| `UAP_REDIS_URL` | Redis URL |
| `UAP_BILLING_MODE` | `mock` (default) or `stripe` |
| `UAP_CRYPTO_MODE` | `mock` or `live` |
| `UAP_CRYPTO_RECEIVER_WALLET` | Wallet to receive USDC/USDT |
| `UAP_*_RPC_URL` | Per-chain RPC (Ethereum, Polygon, Base, Arbitrum, BSC) |
| `STRIPE_*` | Card payments (when billing mode = stripe) |

## Billing APIs

- `GET /v1/billing/status` — current plan/usage
- `POST /v1/billing/checkout-session` — Stripe card checkout
- `POST /v1/billing/crypto/checkout-session` — USDC/USDT multi-chain invoice
- `GET /v1/billing/crypto/networks` — supported chains
- `GET /v1/billing/crypto/invoices` — invoice history + status
- `POST /v1/billing/stripe/webhook` — Stripe webhook
- `POST /v1/billing/mock/set-plan` — dev mock plan switch

## Stripe local test

```bash
set UAP_BILLING_MODE=stripe
set STRIPE_API_KEY=sk_test_...
stripe listen --forward-to localhost:8000/v1/billing/stripe/webhook
```

## Crypto live test

```bash
set UAP_CRYPTO_MODE=live
set UAP_CRYPTO_RECEIVER_WALLET=0x24DAb37fd89222710ce1D5A4c4E81e26D51E34D5
set UAP_POLYGON_RPC_URL=https://polygon-mainnet.g.alchemy.com/v2/KEY
```

Bot polls every ~20s and upgrades plan after on-chain confirmation.

## Roadmap

See [`docs/PROD-ROADMAP.md`](../docs/PROD-ROADMAP.md) and [`docs/SELF-HOST.md`](../docs/SELF-HOST.md).
