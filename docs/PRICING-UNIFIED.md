# NARNA Unified Pricing — Web · iOS · Android · API

**Status:** Canonical (single source of truth)  
**Effective:** 2026-11-10  
**Backend:** `web/backend/app/billing.py` → `PLANS`

Same **plan names & dollars** everywhere. **Payment rails differ by client** (see below).

---

## Catalog (locked)

| Display name | Plan ID (API) | Price | Period |
|--------------|---------------|------:|--------|
| **Free** | `free` | **$0** | — |
| **Pro** | `cloud` (alias `pro`) | **$20 / mo** | 30 days |
| **Pro Annual** | `cloud` | **$160 / yr** (~$13.33/mo) | 365 days |
| **Team** | `team` | **$99 / seat / mo** | min 3 · max 50 seats |
| **Business** | `business` | **$199 / mo** | fixed |

### Store product IDs (mobile)

| Product ID | Plan | Listed price |
|------------|------|--------------|
| `narna_pro_monthly` | `cloud` | **$19.99** |
| `narna_pro_yearly` | `cloud` | **$159.99** |
| `narna_team_seat_monthly` | `team` | **$99.99 / seat** (when Team sold in-app) |

---

## Payment rails (CRITICAL)

| Client | Allowed payment | Forbidden in that client |
|--------|-----------------|---------------------------|
| **Web** (narna.org) | **USDC / USDT** crypto checkout | — |
| **iOS app** | **App Store IAP / subscriptions only** | ❌ Crypto, ❌ USDC/USDT UI, ❌ open web crypto checkout to unlock |
| **Android app** | **Google Play Billing only** | ❌ Crypto, ❌ USDC/USDT UI, ❌ open web crypto checkout to unlock |
| **Desktop** | Free local; optional cloud via account entitlement | No crypto UI required |

### Mobile rule (Apple + Google)

1. Upgrade / subscribe / restore **only** through StoreKit 2 (iOS) or Play Billing Library (Android).  
2. **Do not** show wallet address, chain picker, USDC/USDT, or `/checkout` crypto flow inside the apps.  
3. Receipt / purchase token → server verifies → set `Organization.plan` (`cloud` / `team`) + expiry.  
4. Web crypto purchases remain for **web** customers; mobile apps must not push users into crypto paywalls.

---

## What each plan includes

### Free — `$0` · `free`
- Desktop agent forever, BYOK  
- Mobile: pair, chat, basic approvals  
- No always-on cloud, routines, voice, multi-seat  

### Pro — `$20/mo` · `cloud`
- Cloud brain, sync, multi-device  
- Mobile full: inbox, routines, voice, remote, push  
- BYOK for model tokens (NARNA does not resell Claude/GPT)  

### Team — `$99/seat/mo` · `team`
- Shared bots, org inbox, seats 3–50  
- **Web:** crypto checkout  
- **iOS/Android:** Play/App Store subscription products only (no crypto)  

### Business — `$199/mo` · `business`
- Web / sales primary  

---

## Entitlement

```
GET /v1/billing/status → plan, planExpiresAt, seatCount, features
```

| Client | How user upgrades |
|--------|-------------------|
| Web | Crypto checkout → plan on payment confirm |
| iOS | App Store subscription → verify transaction → `cloud` / `team` |
| Android | Play Billing → verify purchase token → `cloud` / `team` |
| Desktop | Free local; cloud features follow account plan |

---

## Anti-patterns (forbidden)

1. Crypto paywall or “Pay with USDC” inside iOS/Android  
2. Deep-link from app to web crypto checkout to unlock the same digital features (avoid App Review / Play policy risk)  
3. Different feature matrix for the same plan id on web vs app  
4. Selling Claude/GPT tokens  

---

## Doc sync

- [x] `billing.py` plan dollars  
- [x] Web Pricing (`brand.ts`) Free / Pro $20 / Team $99  
- [x] Mobile: IAP/Play only — no crypto  
- [ ] Implement StoreKit + Play Billing + server receipt verify  

---

**One line:** *Same plans everywhere — Web pays crypto; iOS pays Apple; Android pays Google Play.*
