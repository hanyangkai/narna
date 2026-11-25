# Nana Agent proxy

Scaffold for the paid Agent backend. **Do not deploy without owner approval.**

The iOS app sends Agent requests only here (`AGENT_PROXY_URL/v1/agent`) with the StoreKit 2 transaction JWS in `X-StoreKit-JWS`. Provider keys stay on the server.

## Responsibilities

1. Verify the App Store JWS (App Store Server API). Reject unsigned or expired subscriptions.
2. Map product IDs `nana.agent.basic.monthly` (200 credits/month) and `nana.agent.pro.monthly` (800 credits/month).
3. Enforce credit caps so API cost stays below net revenue after Apple's 15% fee (proposed list prices 99.000đ and 249.000đ; actual prices come from App Store Connect).
4. Call strong models (OpenAI, Anthropic, Gemini paid) with server-side keys only.
5. Support multi-step tasks, file/image parts, and web search as requested by the client.

## Env (never commit secrets)

- `APPLE_BUNDLE_ID`, `APPLE_APP_ID`, App Store Server API key (`.p8`) — verification
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY` (paid) — model calls
- `BASIC_MONTHLY_CREDITS=200`, `PRO_MONTHLY_CREDITS=800`

This directory is a contract + placeholder. Implementation can land in a follow-up after the IAP products exist in App Store Connect.
