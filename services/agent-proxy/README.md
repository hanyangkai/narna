# Nana Agent proxy

StoreKit-gated Worker for paid Nana Agent. **Ready, but do not deploy without owner approval. Do not put paid API keys in this repo.**

The iOS app posts to `AGENT_PROXY_URL/v1/agent` with the StoreKit 2 transaction JWS in `X-StoreKit-JWS`. Provider keys stay on the server.

## What this worker does

1. Verify the transaction JWS: `x5c` chain to the official Apple Root CA - G3, ES256 signature, bundle id `org.narna.mobile`, product id, expiry, revocation.
2. Optionally look up the transaction with the App Store Server API when an In-App Purchase key is configured (production, then sandbox). This is recommended at deploy time.
3. Map `nana.agent.basic.monthly` → 200 credits/month and `nana.agent.pro.monthly` → 800 credits/month. Ledger is keyed by `originalTransactionId` + period in KV.
4. Charge 1 credit per request, +1 for web search, +1 when a file is attached. Refund the reserve if the model call fails.
5. Call a cheap strong model with a server-side key. If no key is set, `/v1/agent` returns 503 after a valid subscription check and does **not** burn credits.

`DEV_ALLOW_UNVERIFIED` must stay off except in local tests.

`npm test` (Node 18+) covers JWS, credit caps, and the HTTP handler. `npm run deploy` is a hard no-op.

## Keys and budget required before a real deploy

None of these should be committed. Do not reuse the App Review OpenRouter key, and do not reuse the free-pool Gemini key for Agent (keep free-chat quota separate).

**Apple (required to accept real subscriptions)**

- App Store Server API / In-App Purchase `.p8` key, Key ID, and Issuer ID (`APPLE_IAP_KEY_ID`, `APPLE_IAP_ISSUER_ID`, `APPLE_IAP_PRIVATE_KEY`). This is the Integrations → In-App Purchase key, not the App Store Connect API key used for TestFlight uploads. Same Apple Developer team (7PSYZPFSUW), bundle `org.narna.mobile`, app id `6832895840`.
- A Cloudflare Workers KV namespace for `CREDITS` (free-plan KV is enough). Replace the placeholder id in `wrangler.toml` at deploy time.

**Paid model (required or Agent returns 503)**

Pick one, cheapest first so caps stay under net revenue after Apple's 15% fee:

| Plan  | List   | Net proceeds | Credit cap | Max API spend / credit | Worst-case monthly API spend / sub |
|-------|--------|--------------|------------|------------------------|------------------------------------|
| Basic | $4.99  | $4.24        | 200        | $0.0212                | $4.24                              |
| Pro   | $14.99 | $12.74       | 800        | $0.0159                | $12.74                             |

Recommended: `OPENAI_API_KEY` with `AGENT_MODEL=gpt-4o-mini`. At typical Agent request size (~2k input + 1k output tokens), 4o-mini is well under one cent per credit, so 200/800 caps stay far under $4.24 / $12.74. Alternatives: `ANTHROPIC_API_KEY` (Haiku) or a **paid** `AGENT_GEMINI_API_KEY`. Set a hard provider budget at or below the net proceeds above; do not enable a paid Cloudflare plan just to run this Worker.

**Also before go-live**

- Owner approval to deploy.
- Set `AGENT_PROXY_URL` in the iOS Info.plist / build settings on this branch only after the Worker URL exists.
- Confirm App Attest uses the `production` entitlement in Release (already set in `NARNA-Release.entitlements`).

## Endpoints

- `GET /health` → `{ ok, service: "nana-agent-proxy", modelsConfigured }`
- `POST /v1/agent` + `X-StoreKit-JWS` + `{ system, messages, webSearch, fileName, fileMIME, fileBase64 }`
  - 200 `{ content, modelDisplayName, creditsRemaining }`
  - 401 missing/invalid JWS
  - 403 unknown product, expired, or revoked
  - 429 credits exhausted
  - 503 no paid model key configured
