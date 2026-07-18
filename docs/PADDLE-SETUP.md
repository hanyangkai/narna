# Paddle Live Checkout — NARNA

## Error `transaction_checkout_not_enabled`

This is a **Paddle account** gate, not an app bug. Checkout API stays disabled until seller onboarding is **Approved**.

## Live checklist (vendors.paddle.com)

1. **Seller onboarding** → status **Approved / Selling** (business, identity, payout).
2. **Checkout → Checkout settings → Default payment link** → `https://narna.org/billing` (page must load Paddle.js via `PaddleCheckout` component).
3. **Checkout → Website approval** → add `https://narna.org` → wait **Approved**.
4. **Developer Tools → Authentication** → copy **Client-side token** (`live_…`) → `VITE_PADDLE_CLIENT_TOKEN` at frontend build time.
5. **Developer Tools → Notifications** → webhook `https://api.narna.org/v1/billing/paddle/webhook` → set `PADDLE_WEBHOOK_SECRET`.
6. **Catalog** → product id in `PADDLE_PRODUCT_ID` (live catalog, not sandbox).

## Environment (production)

```bash
UAP_BILLING_MODE=paddle
NARNA_PUBLIC_URL=https://narna.org
PADDLE_API_KEY=pdl_live_apikey_...
PADDLE_PRODUCT_ID=pro_...
PADDLE_SUCCESS_URL=https://narna.org/billing?paid=1
PADDLE_PACKAGE_SUCCESS_URL=https://narna.org/packages?paid=1
PADDLE_WEBHOOK_SECRET=...
```

Frontend build:

```bash
VITE_API_URL=https://api.narna.org
VITE_PADDLE_CLIENT_TOKEN=live_...
```

## Verify

```bash
curl -s https://api.narna.org/v1/billing/paddle/status
```

When ready: `checkoutEnabled: true` and test package purchase returns `checkoutUrl` with `_ptxn=`.

If still blocked after checklist → **sellers@paddle.com** with account email + Paddle `request_id`.
