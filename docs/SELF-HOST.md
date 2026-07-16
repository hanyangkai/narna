# Self-Host First — UAP Cloud



**Philosophy:** SDK + Spec first. Cloud is optional. Enterprise can run on-prem with one command.



```text

UAP SDK

   │

   ├── Local mode (default, offline)

   ├── Optional cloud telemetry (paid hosted)

   └── Self-host (docker compose up)

```



Target cost at Stage 0: **< $15/month**.



---



## Recommended stack (Stage 0 → 1,000 developers)



```text

GitHub

  ↓ CI/CD

Coolify (free, self-hosted)

  ↓

Hetzner VPS CX22 (~$5–6/mo)

  ↓

Docker Compose

```



Services:



```text

Cloudflare (DNS + TLS)

  ↓

Traefik (via Coolify)

  ↓

Coolify

  ↓

Docker

  ├── Postgres

  ├── Redis

  ├── API (FastAPI)

  └── Dashboard (React)

```



**Do not use** Kubernetes, Kafka, Elastic, or ClickHouse at this stage.



---



## Quick start (local / on-prem)



From repo root:



```bash

docker compose up --build

```



- API: http://localhost:8000/v1/health

- Console: http://localhost:5173/console

- Dev API key (first boot): `uap_live_dev_local_key_change_in_prod`



Push a run:



```bash

pip install -e .

uap run --spec specs/examples/trading-agent.yaml --input "btc price"

uap push --run <runId> --cloud-key uap_live_dev_local_key_change_in_prod

```



---



## Coolify on Hetzner (production)



### 1) Provision VPS



- Hetzner CX22 (4GB RAM) is enough for early stage

- Ubuntu 24.04 LTS

- Open ports: 22, 80, 443



### 2) Install Coolify

```bash
bash web/deploy/selfhost/install-coolify.sh
```

Or follow [Coolify docs](https://coolify.io/docs) manually.

**Quick deploy (Docker only, no Coolify UI):**

```bash
cp web/deploy/selfhost/.env.production.example web/deploy/selfhost/.env
# Edit secrets + RPC URLs
bash web/deploy/selfhost/deploy.sh --build
```



### 3) Point domain



- Cloudflare DNS → VPS IP

- Enable proxy (orange cloud) for DDoS + TLS

- In Coolify: add domain for API + dashboard



### 4) Deploy from Git



In Coolify, create a **Docker Compose** resource:



- Repository: this repo

- Compose file: `web/docker-compose.yml`

- Set env vars from `web/backend/.env.example`



### 5) Production env (minimum)



| Variable | Value |

|----------|-------|

| `UAP_DATABASE_URL` | `postgresql+psycopg2://...` (Coolify Postgres service) |

| `UAP_REDIS_URL` | `redis://redis:6379/0` |

| `UAP_BILLING_MODE` | `stripe` (card) or `mock` (dev) |

| `UAP_CRYPTO_MODE` | `live` |

| `UAP_CRYPTO_RECEIVER_WALLET` | `0x24DAb37fd89222710ce1D5A4c4E81e26D51E34D5` |

| `UAP_ETH_RPC_URL` | Alchemy/Infura Ethereum mainnet |

| `UAP_POLYGON_RPC_URL` | Polygon RPC |

| `UAP_BASE_RPC_URL` | Base RPC |

| `UAP_ARBITRUM_RPC_URL` | Arbitrum RPC |

| `UAP_BSC_RPC_URL` | BSC RPC |

| `STRIPE_*` | Stripe keys + price IDs |

| `SENTRY_DSN` | Optional error tracking |



---



## Scaling phases



| Phase | Infra | When |

|-------|-------|------|

| **0** | 1 VPS (app + DB + Redis in Docker) | 0–1k developers |

| **1** | 2 VPS (app / DB split) | DB pressure |

| **2** | 3 VPS (app / DB / Redis) | Queue + cache load |

| **3** | Managed cloud | 10k+ developers |



Add ClickHouse / Kafka **only** when Postgres + Redis Streams are not enough.



---



## Payment setup



### Card (Stripe)



```bash

UAP_BILLING_MODE=stripe

STRIPE_API_KEY=sk_live_...

STRIPE_PRICE_ID_PRO=price_...

STRIPE_PRICE_ID_TEAM=price_...

STRIPE_PRICE_ID_BUSINESS=price_...

STRIPE_WEBHOOK_SECRET=whsec_...

```



Webhook URL: `https://api.yourdomain.com/v1/billing/stripe/webhook`



### Crypto (multi-chain)



Supported chains: **Ethereum, Polygon, Base, Arbitrum, BSC**  

Assets: **USDC, USDT**



```bash

UAP_CRYPTO_MODE=live

UAP_CRYPTO_RECEIVER_WALLET=0x24DAb37fd89222710ce1D5A4c4E81e26D51E34D5

UAP_CRYPTO_BOT_ENABLED=1

# Set all chain RPC URLs

```



Bot polls every ~20s, scans ERC-20 `Transfer` logs, confirms ≥3 blocks, upgrades plan.



---



## What we intentionally skip (for now)



- Fly.io / multi-region edge (not needed early)

- Kubernetes

- Kafka (use Redis Streams later if needed)

- Elastic (logs in Postgres first)



See also: [`DEPLOYMENT.md`](./DEPLOYMENT.md) for optional cloud targets.

