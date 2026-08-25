# Model Router Specification

**Version:** 0.1.0-draft  
**Status:** Draft  
**Series:** NGS-0028  
**Product:** [`../../docs/NARNA-AGENT.md`](../../docs/NARNA-AGENT.md)

---

## 1. Purpose

The **Model Router** selects and invokes an LLM for a tagged cognitive task without coupling agents to a single vendor.

NARNA **MUST NOT** train foundation models. Models are interchangeable commodities.

---

## 2. Task tags

| Tag | Intent | Default policy |
|-----|--------|----------------|
| `cheap` | Fast / low-cost draft | cheapest configured model |
| `reason` | Primary analysis | reasoning-capable model |
| `challenge` | Adversarial critique | alternate or same model + challenge prompt |
| `decide` | Final synthesis | reason model |
| `analyze` | Structured breakdown | alias of `reason` |
| `plan` | Multi-step plan | alias of `reason` |

---

## 3. Providers

`UAP_ROUTER_PROVIDER` ∈ `mock` | `openrouter` | `openai` | `ollama`

All non-mock providers use OpenAI-compatible chat completions.

| Env | Role |
|-----|------|
| `UAP_OPENROUTER_API_KEY` | Hosted Free / default Cloud |
| `UAP_OPENAI_API_KEY` | Direct OpenAI |
| `UAP_OLLAMA_BASE_URL` | Local (default `http://127.0.0.1:11434/v1`) |
| `UAP_ROUTER_MODEL_CHEAP` | Override cheap model id |
| `UAP_ROUTER_MODEL_REASON` | Override reason model id |
| `UAP_ROUTER_MODEL_CHALLENGE` | Override challenge model id |

---

## 4. API

### `POST /v1/router/complete`

```json
{
  "task": "reason",
  "messages": [{"role": "user", "content": "…"}],
  "temperature": 0.2,
  "maxTokens": 1024
}
```

```json
{
  "content": "…",
  "model": "…",
  "provider": "openrouter",
  "task": "reason",
  "usage": {"promptTokens": 0, "completionTokens": 0},
  "standard": "NGS-0028"
}
```

### CLI

`narna reason --task reason --message "…"`

---

## 5. Non-goals

- Fine-tuning or hosting weights  
- Guaranteeing model correctness  
- Replacing ADQA (router generates; ADQA scores)
