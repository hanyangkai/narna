# NARNA Unified Pricing — Web · iOS · Android · API

**Status:** Canonical (single source of truth)  
**Effective:** 2026-11-10  
**Backend:** `web/backend/app/billing.py` → `PLANS`

Everything customer-facing (narna.org, App Store, Google Play, checkout, restore) **must use this table**. Do not invent separate mobile prices.

---

## Catalog (locked)

| Display name | Plan ID (API) | Price | Billing | Channels |
|--------------|---------------|------:|---------|----------|
| **Free** | `free` | **$0** | — | Web · iOS · Android · Desktop |
| **Pro** | `cloud` (alias `pro`) | **$20 / mo** | 30-day period | Web (USDC/USDT) · iOS IAP · Play Billing |
| **Pro Annual** | `cloud` | **$160 / yr** (~$13.33/mo) | 365-day period | iOS IAP · Play Billing · Web crypto optional |
| **Team** | `team` | **$99 / seat / mo** | min **3** seats, max **50** | Web primary · App restore via account |
| **Business** | `business` | **$199 / mo** | fixed | Web primary · sales-assisted |

### IAP SKU mapping (must match dollars above)

| Store product ID (suggested) | Maps to plan | Store price |
|------------------------------|--------------|-------------|
| `narna_pro_monthly` | `cloud` | **$19.99** ≈ $20 |
| `narna_pro_yearly` | `cloud` | **$159.99** ≈ $160 |
| Team seats | `team` | **Web only (phase 1)** — App Store seat IAP later if needed |
| Business | `business` | Web only |

> Store list price uses .99 endings; entitlement is identical to web `$20` / `$160` Pro.

---

## What each plan includes

### Free — `$0` · `free`
- Desktop agent **forever** (Mac/Windows), BYOK
- Mobile companion: pair 1 desktop, chat, basic approvals
- Cloud Ask with BYOK (quota per `billing.py`)
- **No** always-on cloud agent, routines, voice, multi-seat

### Pro — `$20/mo` · `cloud`
- Everything in Free
- **Cloud brain** + backup / sync / multi-device
- Mobile: inbox, routines, voice UI, remote Tailscale/HTTPS, push approvals
- Higher GU / ADQA / agent-turn caps (see `PLANS["cloud"]`)
- BYOK still required for model tokens (NARNA does **not** resell Claude/GPT)

### Team — `$99/seat/mo` · `team`
- Everything in Pro
- Shared org, shared bots, shared inbox / approvals
- Seats 3–50 (`usd_per_seat: 99`)
- Checkout: `seats × $99` USDC/USDT on web; app restores via same org API key / account

### Business — `$199/mo` · `business`
- Higher caps, more seats baseline
- Web checkout / sales
- Not required on mobile store listing v1

---

## Payment rails (unified)

| Rail | Used for |
|------|----------|
| **USDC / USDT** (Ethereum, Polygon, Base, Arbitrum, BSC) | Web `/checkout` · `/billing` — source of truth today |
| **App Store IAP** | Pro monthly / yearly |
| **Google Play Billing** | Pro monthly / yearly |
| **Cards / Stripe / Paddle** | **Removed** — do not reintroduce without explicit decision |

**Rule:** Paying on **any** rail sets the same `Organization.plan` (`free` \| `cloud` \| `team` \| `business`) + `plan_expires_at`.  
App and web both call `GET /v1/billing/status` — one entitlement.

---

## Naming rules (no more confusion)

| ❌ Do not say | ✅ Say |
|---------------|--------|
| Personal $20 | **Pro** $20 (`cloud`) |
| Cloud $20 as display name | **Pro** (API id still `cloud`) |
| Pro $30–50 (old market doc) | **Pro $20** only |
| Mobile Pro $19.99 as different product | Same **Pro**; IAP cosmetic .99 |
| Team $12.99/seat on app | **Team $99/seat** (same as web) |

Aliases kept in code only: `pro` → `cloud`, `personal` → treat as `cloud` in UI prices.

---

## Entitlement check (all clients)

```
GET /v1/billing/status
→ plan, planExpiresAt, seatCount, features…
```

| Client | How user upgrades |
|--------|-------------------|
| Web | Crypto checkout → plan flipped on payment confirm |
| iOS / Android | IAP → server verify receipt → set `cloud` · **or** open web checkout + paste API key |
| Desktop | Free local; optional login to Pro cloud sync |

---

## Anti-patterns (forbidden)

1. Different feature matrix on web vs mobile for the same plan id  
2. Charging for Claude/ChatGPT tokens (BYOK only)  
3. “Lifetime forever” Pro license that bypasses `plan_expires_at` without finance sign-off  
4. Showing Team as “Soon” while API already bills `$99/seat`

---

## Doc / code sync checklist

- [x] `billing.py` — prices  
- [ ] `web/frontend/src/brand.ts` — show Team $99/seat (not Soon)  
- [ ] `docs/BUSINESS-MODEL.md` — align names to Free / Pro / Team / Business  
- [ ] `docs/NARNA-MARKET-PLAN.md` — remove Pro $30–50  
- [ ] Mobile paywall copy — use this doc only  
- [ ] App Store / Play listing — Pro $19.99 / $159.99  

---

**Owner:** Product + Billing  
**One line:** *Free $0 · Pro $20/mo · Team $99/seat · Business $199 — same everywhere.*
