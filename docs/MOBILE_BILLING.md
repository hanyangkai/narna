# Mobile Billing Policy — Apple & Google only

## Rule

| Platform | Payment |
|----------|---------|
| **iOS** | App Store In-App Purchase / Auto-renewable subscriptions **only** |
| **Android** | Google Play Billing **only** |
| **Web** | USDC/USDT crypto (unchanged) |

**Forbidden in iOS & Android apps:**
- USDC / USDT / any crypto checkout
- Wallet address / QR payment screens
- Buttons that open narna.org crypto `/checkout` to unlock Pro/Team inside the app

## Products

| SKU | Plan ID | Price |
|-----|---------|------:|
| `narna_pro_monthly` | `cloud` | $19.99/mo |
| `narna_pro_yearly` | `cloud` | $159.99/yr |
| `narna_team_seat_monthly` | `team` | $99.99/seat/mo |

## Server flow

1. Client completes StoreKit / Play Billing purchase  
2. App sends receipt / purchaseToken to backend (`POST /v1/billing/store/verify` — to implement)  
3. Backend verifies with Apple/Google → sets `org.plan` + `plan_expires_at`  
4. App reads `GET /v1/billing/status`

## UI copy

Settings → Subscription: “Manage plan via App Store” / “Manage plan via Google Play”  
Never: “Pay with USDC”.
