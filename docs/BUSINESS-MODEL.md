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

| Client | Rail | Plans |
|--------|------|-------|
| **Web** | **USDC / USDT** (5 EVM chains) | Pro · Team · Business |
| **iOS app** | **App Store IAP only** | Pro monthly/yearly · Team seat (store products) |
| **Android app** | **Google Play Billing only** | Pro monthly/yearly · Team seat (store products) |
| Cards / Stripe / Paddle | **Removed** | — |

- Web checkout: `POST /v1/billing/crypto/checkout-session` · UI: `/checkout` · `/billing`
- **Mobile apps: no crypto UI, no USDC/USDT, no web crypto deep-link paywall**
- Same `Organization.plan` after store receipt verify or web crypto confirm
- Team: **$99 × seats** (3–50)

---

## Mobile

App download free. Upgrades **only** via Apple / Google. Same plan IDs as web — see [`PRICING-UNIFIED.md`](./PRICING-UNIFIED.md).
