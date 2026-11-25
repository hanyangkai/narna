# Nana AI free-pool worker

Cloudflare Worker (free plan) that powers **Free cloud** chat in the Nana AI iOS app.

`POST /v1/chat` → normalized SSE (`data: {"delta":"…"}`).

## Upstreams (fallback order)

1. **Cloudflare Workers AI** (`env.AI` binding) — typically free-tier quota  
2. **Groq** free tier (`GROQ_API_KEY`)  
3. **OpenRouter `:free` models** (`OPENROUTER_API_KEY`)

## Limits

| Control | Default |
|---------|---------|
| Per-device messages / day | 10 |
| Global messages / day | 5000 |
| Per-IP soft multiplier | 3× device limit |
| `max_tokens` | 512 |

Counters live in KV. **Message content is never logged** — only hashed device id, engine name, and approx prompt size.

## Secrets (do not commit)

```bash
cd free-pool-worker
cp .dev.vars.example .dev.vars   # local only
npx wrangler secret put GROQ_API_KEY
npx wrangler secret put OPENROUTER_API_KEY
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

Then set iOS `FREE_POOL_URL` build setting / Info.plist to your `*.workers.dev` URL.

## Deploy

Not done by CI/agent — owner runs `npx wrangler deploy` after secrets + KV are configured.
