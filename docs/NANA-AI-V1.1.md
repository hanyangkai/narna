# Nana AI iOS v1.1 — free chat + Agent

## Engines (`LLMProvider` + `ProviderRouter`)

| Mode | Behavior |
|------|----------|
| **Auto (default)** | Apple on-device Foundation Models when `SystemLanguageModel.default.availability == .available`; else free-pool Worker |
| **Free cloud** | `POST {FREE_POOL_URL}/v1/chat` with DeviceCheck token (when available) + Keychain device UUID — **10 msgs/device/day** |
| **Agent** | StoreKit 2 `nana.agent.basic.monthly` / `nana.agent.pro.monthly` → backend JWS verify + credit caps |
| **Advanced BYOK** | User OpenRouter / OpenAI key in Keychain → direct provider SSE |

No platform OpenRouter / Groq / Gemini / Z.AI keys ship in the app bundle. No scraping of chatgpt.com / gemini.google.com / claude.ai.

## Worker upstream order (`services/free-pool-worker`)

1. Cloudflare Workers AI — gpt-oss-120b / 20b, Gemma, Llama, Qwen  
2. Google AI Studio free (`GEMINI_API_KEY`) — skip EEA / UK / CH  
3. Groq free if `GROQ_API_KEY`  
4. OpenRouter `:free` if `OPENROUTER_API_KEY`  
5. Z.AI GLM Flash if `ZAI_API_KEY`

**Do not deploy** the Worker from this PR — scaffold only.

## Build settings

- `MARKETING_VERSION` = **1.1**
- `CURRENT_PROJECT_VERSION` = **2**
- `FREE_POOL_URL` = Worker URL  
- `NANA_AGENT_API_URL` = backend base (StoreKit verify / agent chat)  
- Min iOS **16.0**; Foundation Models gated with `#available(iOS 26.0, *)`  
- StoreKit config: `NARNA/Configuration/NanaAI.storekit`

## Secrets / env

### Worker (`wrangler secret put`)

| Secret / var | Purpose |
|--------------|---------|
| `GROQ_API_KEY` | Optional Groq free |
| `OPENROUTER_API_KEY` | Optional OpenRouter `:free` |
| `GEMINI_API_KEY` | Optional Google AI Studio |
| `ZAI_API_KEY` | Optional Z.AI overflow |
| `GEMINI_MODEL` | e.g. `gemini-2.0-flash` (configurable) |
| `ZAI_MODEL` / `ZAI_BASE_URL` | GLM Flash endpoint |
| `DAILY_MSG_LIMIT_PER_DEVICE` | default `10` |
| KV `LIMITS` | counters |
| AI binding `AI` | Workers AI |

### Backend Agent

| Env | Purpose |
|-----|---------|
| `OPENROUTER_API_KEY` | Paid Agent upstream (server-side only) |
| `NANA_IAP_STRICT` | `1` to enforce stricter JWS checks |

## UI

- Model label under each assistant bubble (`Apple on-device`, `GPT-OSS`, `Gemini Flash`, …)  
- Daily free limit → friendly sheet + **Upgrade to Agent**  
- Paywall: Restore Purchases, Manage Subscription (App Review 3.1.2)
