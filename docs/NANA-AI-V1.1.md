# Nana AI iOS v1.1 — free chat

## Engines

| Mode | Behavior |
|------|----------|
| **Auto (default)** | Apple on-device Foundation Models when available (`#available` / `canImport`); else free-pool Worker |
| **Free cloud** | `POST {FREE_POOL_URL}/v1/chat` with anonymous Keychain device UUID |
| **Advanced BYOK** | User OpenRouter / OpenAI key in Keychain → direct provider SSE |

No platform OpenRouter/Groq keys ship in the app bundle.

## Build settings

- `MARKETING_VERSION` = **1.1**
- `CURRENT_PROJECT_VERSION` = **2**
- `FREE_POOL_URL` = Worker URL (Info.plist / xcconfig)
- Min iOS remains **16.0**; Foundation Models gated with `#available(iOS 26.0, *)`

## Worker secrets

See [`free-pool-worker/README.md`](../free-pool-worker/README.md):

- `GROQ_API_KEY`
- `OPENROUTER_API_KEY`
- Optional `FREE_POOL_PAUSED`
- KV namespace binding `LIMITS`
- AI binding `AI`
