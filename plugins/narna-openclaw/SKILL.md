---
name: narna-openclaw
description: Connect OpenClaw to NARNA Decision Quality via MCP — evaluate actions, Ask NARNA, probe runtime status. Use before irreversible agent actions.
---

# NARNA + OpenClaw

NARNA is **Decision Quality Infrastructure** (ADQA · Trace · Replay). It is **not** a full Hermes toolbelt over MCP.

MCP exposes: `narna_adqa_check`, `narna_evaluate_action`, `narna_agent_ask`, `narna_runtime_status`, traces/replay — **not** all 44 Ask tools.

## Prerequisites

1. OpenClaw installed (`openclaw --version`)
2. NARNA org API key (`uap_live_…`) from https://narna.org — BYOK LLM keys stay in OpenClaw/NARNA Ask separately

## Configure MCP (`~/.openclaw/openclaw.json`)

```json
{
  "mcp": {
    "servers": {
      "narna": {
        "url": "https://api.narna.org/mcp",
        "headers": {
          "Authorization": "Bearer uap_live_YOUR_KEY"
        }
      }
    }
  }
}
```

Self-host: replace URL with `https://YOUR_HOST/mcp`.

Probe:

```bash
openclaw mcp probe narna
```

## When to call which tool

| Situation | Tool |
|-----------|------|
| Before irreversible action | `narna_adqa_check` or `narna_evaluate_action` |
| Need reasoned answer + DQS | `narna_agent_ask` |
| Is Playwright/shell ready? | `narna_runtime_status` |
| Audit past decision | `narna_trace_get` / `narna_replay` |

## Local desktop (no cloud)

```bash
pip install "narna[desktop]"
narna desktop
# Ask UI on http://127.0.0.1:8765/ — paste OpenRouter/OpenAI key
```

Or portable Windows zip: https://github.com/hanyangkai/narna/releases

## Honest limits

- Signal/Email on NARNA cloud are bridge-level — use Telegram for production bots
- Modal/Daytona shell = stubs unless you bring exec URLs
- ClawHub marketplace ≠ NARNA Skills Hub (local zip + public index only)

See https://github.com/hanyangkai/narna/blob/main/docs/PROD-AGENT-PARITY.md
