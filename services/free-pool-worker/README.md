# Nana AI free-pool Worker

Scaffold for the server that powers **free chat** inside Nana AI when the on-device Apple Foundation Model is not available. **Do not deploy this Worker as part of the 1.1 PR.** The owner must approve any production change.

The iOS app never embeds provider keys. It posts to `FREE_POOL_URL/v1/chat` with an App Attest / DeviceCheck token (and a debug device id only in development).

## Route order

Fail over on HTTP 429 and 503 (including Gemini "high demand"):

1. **Cloudflare Workers AI gpt-oss** — `@cf/openai/gpt-oss-120b`, then `@cf/openai/gpt-oss-20b`. This is the primary gpt-oss path and needs no external key (Workers AI binding only).
2. **Groq gpt-oss** — optional overflow (`openai/gpt-oss-120b`, `openai/gpt-oss-20b`). **Skipped entirely when `GROQ_API_KEY` is unset.**
3. **Google AI Studio** — `gemini-3.8-flash` (override with `GEMINI_MODEL` / `GEMINI_MODELS`), Flash-Lite, Gemma 4. **Skipped for users in the EEA, United Kingdom, or Switzerland.**
4. **Cloudflare Workers AI** — Llama, Gemma, Qwen (see `CF_MODELS`)
5. **OpenRouter `:free`** — Gemma 4 and `openrouter/free`
6. **Z.AI** — `glm-4.7-flash`

All model lists and the enabled-provider list are configurable through Worker env / secrets. Empty provider keys skip that provider.

## Per-device cap

100 messages per device per day (`DAILY_LIMIT`, default 100), counted in KV after App Attest or DeviceCheck verification. In development, `DEV_ALLOW_UNATTESTED=1` allows `X-Debug-Device-Id`.

## Secrets

```bash
wrangler secret put GEMINI_API_KEY
wrangler secret put GROQ_API_KEY
wrangler secret put OPENROUTER_API_KEY
wrangler secret put ZAI_API_KEY
```

Never commit keys, `.dev.vars`, `.p8`, or `.pem` files.

`GEMINI_MODEL` defaults to `gemini-3.8-flash` because `gemini-2.5-flash` is closed to new users.

## Privacy

Unpaid Google Gemini / Gemma quota may be used by Google to improve Google models. The iOS Settings screen discloses this. Users in EEA / UK / CH are not sent to that unpaid Google route.

## Local tests

```bash
npm test
```

Runs `node --test` on the pure router (no Wrangler, no keys required).
