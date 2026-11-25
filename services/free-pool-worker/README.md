# Nana AI free-pool worker

Cloudflare Worker (free plan) that powers **Free cloud** chat in the Nana AI iOS app.

Path: `services/free-pool-worker` (scaffold only — **do not deploy** from this PR).

`POST /v1/chat` → normalized SSE (`data: {"delta":"…"}`).

## Upstream failover (on 429 / 503 / timeout)

1. **Cloudflare Workers AI** binding — `@cf/openai/gpt-oss-120b`, `gpt-oss-20b`, Gemma, Llama, Qwen (no external key)
2. **Google AI Studio free** — `GEMINI_API_KEY` + `GEMINI_MODEL` (skip for EEA / UK / CH via `CF-IPCountry` / `X-Region-Hint`)
3. **Groq free** — only if `GROQ_API_KEY` is set (`GROQ_MODEL`, default gpt-oss)
4. **OpenRouter `:free`** — `OPENROUTER_API_KEY`
5. **Z.AI GLM Flash** — `ZAI_API_KEY` last overflow

## Limits

| Control | Default |
|---------|---------|
| Per-device messages / day | **10** |
| Global messages / day | 5000 |
| Per-IP soft multiplier | 3× device limit |
| `max_tokens` | 512 |

Counters in KV. Prefer `X-Device-Check-Token` (DeviceCheck) when present; else Keychain device UUID. **Message content is never logged.**

## Secrets (do not commit)

```bash
cd services/free-pool-worker
cp .dev.vars.example .dev.vars   # local only
npx wrangler secret put GROQ_API_KEY
npx wrangler secret put OPENROUTER_API_KEY
npx wrangler secret put GEMINI_API_KEY
npx wrangler secret put ZAI_API_KEY
# Optional:
# npx wrangler secret put FREE_POOL_PAUSED
```

Create a KV namespace and put its id into `wrangler.toml` `[[kv_namespaces]]`.

## Local

```bash
npm install
npm test
npx wrangler dev
```

Set iOS `FREE_POOL_URL` to your worker URL. **Owner deploys** with `npx wrangler deploy` — not this agent.
