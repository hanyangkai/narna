# NARNA Business Model — Agent-first

**Status:** Active  
**Date:** 2026-08-25  
**Product:** [`NARNA-AGENT.md`](./NARNA-AGENT.md)

---

## Ladder

| Plan | Price | Agent | Hosted LLM | BYO | ADQA / Memory |
|------|------:|-------|------------|-----|---------------|
| **Free Ask** | $0 | Ask web | OpenRouter cheap · **50** turns/mo | — | Basic DQS + short memory |
| **Personal** (API: `cloud`) | **$20/mo** | ✓ | Higher cap | ✓ | Full Decision Memory + ADQA API |
| **Pro** | later | Multi-model challenge | ✓ | ✓ | Advanced ADQA |
| **Team** | **$99/seat/mo** | Shared Decision Brain | ✓ | ✓ | Shared priors · governance |
| **Enterprise** | Custom | Private + own LLM | — | ✓ | On-prem · SSO · SLA |

OSS runtime (`pip install narna`) remains free for local ADQA.

---

## Philosophy

**Ask NARNA is the funnel. ADQA Cloud is Decision Quality. Team is shared Decision Intelligence.**

Two products, one core: consumer Agent + paid ADQA infra. NARNA does not sell foundation-model tokens as the hero metric — it sells **decision quality**.

---

## Payment

**USDC / USDT only** (no Stripe / card / Paddle).

Chains: Ethereum · Polygon · Base · Arbitrum · BSC.

- Checkout: `POST /v1/billing/crypto/checkout-session` · UI: `/billing`
- Auto-confirm on-chain (exact amount + unique cents)
- Paid plan lasts **30 days** (`plan_expires_at`), then drops to free
- Team: **$99 × seats** (3–50)
