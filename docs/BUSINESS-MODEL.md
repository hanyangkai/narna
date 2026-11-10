# NARNA Business Model — Agent-first

**Status:** Active · **Canonical prices:** [`PRICING-UNIFIED.md`](./PRICING-UNIFIED.md)  
**Product:** [`NARNA-AGENT.md`](./NARNA-AGENT.md)

---

## Ladder (Web = iOS = Android)

| Plan | Price | Plan ID | Agent | Hosted LLM | BYOK | Notes |
|------|------:|---------|-------|------------|------|-------|
| **Free** | $0 | `free` | Desktop + mobile basic | None | ✓ | Local forever |
| **Pro** | **$20/mo** (IAP $19.99) | `cloud` (alias `pro`) | Cloud + mobile full | None | ✓ | Always-on · sync · routines |
| **Pro Annual** | **~$160/yr** (IAP $159.99) | `cloud` | Same as Pro | None | ✓ | Store annual |
| **Team** | **$99/seat/mo** | `team` | Shared Decision Brain | None | ✓ | Min 3 seats |
| **Business** | **$199/mo** | `business` | Higher caps | None | ✓ | Web primary |
| **Enterprise** | Custom | — | Private + own LLM | — | ✓ | SSO · on-prem · SLA |

OSS runtime (`pip install narna`) remains free for local ADQA.

---

## Philosophy

**Ask NARNA is the funnel. ADQA Cloud is Decision Quality. Team is shared Decision Intelligence.**

NARNA does **not** sell foundation-model tokens — users BYOK. We sell **cloud connectivity + decision quality + team governance**.

---

## Payment

| Rail | Plans |
|------|-------|
| **USDC / USDT** (5 EVM chains) | Pro · Team · Business on web |
| **App Store / Play IAP** | Pro monthly · Pro yearly |
| Cards / Stripe / Paddle | **Removed** |

- Checkout: `POST /v1/billing/crypto/checkout-session` · UI: `/checkout` · `/billing`
- Paid Pro/Team lasts per `plan_expires_at` (default 30 days for monthly crypto)
- Team: **$99 × seats** (3–50)
- App and web share `Organization.plan` — restore via billing status / account

---

## Mobile

App is free to download. Upgrade to **Pro** or **Team** uses the **same** plan IDs and prices as web. See [`PRICING-UNIFIED.md`](./PRICING-UNIFIED.md).
