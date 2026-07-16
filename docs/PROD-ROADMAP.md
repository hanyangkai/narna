# Production Roadmap — Web → Cloud → Prod

**Goal:** Ship billable Cloud MVP (OpenTelemetry for AI Agents)  
**Current:** OSS SDK MVP ✅ | Cloud + Web ⏳ this roadmap

---

## North star

```text
Week 1–2   Foundation     Export spec + API + ingest
Week 3–4   Console        Runs UI + API keys + uap push
Week 5–6   Monetization   Stripe + plans + limits
Week 7–8   Prod hardening Auth, HTTPS, deploy, monitoring
Week 9–12  Growth         Passport public, docs site, onboarding
```

---

## Phase map

| Phase | Deliverable | Revenue | Exit criteria |
|-------|-------------|---------|---------------|
| **P0** | OSS SDK (done) | $0 | `uap doctor --full` passes |
| **P1** | Export spec + ingest API | $0 | `POST /v1/ingest` accepts ProofBundle |
| **P2** | Web landing + pricing | $0 | Public site live |
| **P3** | Console (runs/audit) | Beta | User views runs in browser |
| **P4** | `uap-cloud` + `uap push` | Beta | One command sync local → cloud |
| **P5** | Stripe billing | **Day 1 $** | Pro $19/mo checkout works |
| **P6** | Prod deploy | **MRR** | HTTPS, backups, SLO 99.5% |
| **P7** | Passport verify | $99/yr | Public badge URL |
| **P8** | Enterprise pack | Sales | On-prem helm chart + SSO sketch |

---

## Architecture (prod target)

```text
[ React Console ] ── [ Landing / Pricing ]
         │
         ▼
[ FastAPI Cloud API ] ── SQLite/Postgres
         ▲
         │ UAP Export Protocol (HTTPS)
         │
[ uap SDK ] + [ uap-cloud exporter ]
```

---

## P1 — Foundation (NOW)

- [x] `specs/uap-export/SPEC.md`
- [x] `web/backend` FastAPI
- [x] `POST /v1/ingest`, `GET /v1/runs`, `GET /v1/runs/{id}`
- [x] API key auth
- [x] `web/frontend` Vite React (landing, pricing, console)
- [x] `src/uap_cloud` exporter
- [x] CLI `uap push --run <id>`
- [x] `docker-compose.yml`

---

## P2 — Console polish (week 3–4)

- [ ] Run timeline (event types color-coded)
- [ ] ProofBundle verify in UI
- [ ] Passport refresh view
- [ ] Org + multiple API keys
- [ ] Usage meter (events/month)

---

## P3 — Billing (week 5–6)

- [x] Stripe Checkout scaffold (Pro/Team/Business via env price IDs)
- [x] Crypto checkout (USDC/USDT multi-chain: Ethereum, Polygon, Base, Arbitrum, BSC)
- [x] Crypto payment bot (on-chain Transfer scan + plan upgrade)
- [x] Webhook endpoint scaffold for plan update
- [x] Enforce limits: events/mo (retention policy next)
- [x] Billing page in console (plan + usage + mock switch)

---

## P4 — Production (week 7–8)

- [x] Postgres (docker-compose production profile)
- [x] Redis in docker-compose (events/queue foundation)
- [x] Self-host first deploy guide (Coolify + Hetzner) — see `docs/SELF-HOST.md`
- [x] Fly.io / Railway / AWS deploy configs (optional, not primary)
- [ ] Custom domain + TLS
- [x] Sentry integration scaffold + structured request logging
- [x] CI: test pipeline (GitHub Actions)
- [x] Rate limiting + idempotent ingest

---

## P5 — Growth (week 9–12)

- [ ] docs.uap.dev (or /docs)
- [ ] GitHub Action: `uap verify` in CI
- [ ] Passport public `/passport/{agentId}`
- [ ] Waitlist → self-serve signup
- [ ] Benchmark dashboard (opt-in)

---

## KPI gates

| Gate | Metric |
|------|--------|
| **P3 done** | 10 beta users view runs in console |
| **P5 done** | 1 paying customer |
| **P6 done** | 99.5% API uptime 7 days |
| **P8** | 1 enterprise pilot conversation |

---

## Repo layout

```text
DAO/
  specs/uap-export/     Export protocol
  src/uap/              OSS SDK
  src/uap_cloud/        Cloud exporter (optional)
  web/
    backend/            FastAPI
    frontend/           React console
    docker-compose.yml
  docs/
    WEB-BIZ-MVP.md
    PROD-ROADMAP.md     (this file)
```

---

## Commands (target)

```bash
# Local prod-like stack (self-host)
docker compose up --build

# Push local run to cloud
export UAP_CLOUD_URL=http://localhost:8000
export UAP_CLOUD_KEY=uap_dev_key
uap push --run <runId>

# Open console
open http://localhost:5173/console
```
