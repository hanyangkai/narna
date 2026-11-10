# NARNA

**Open-source AI agent bot** — Desktop brain · phone remote · ADQA before it acts.

> Like MausBot: run **Claude Code CLI** / **Codex CLI** (your subscription) or BYOK on Desktop.  
> Pair iOS/Android. Every risky action scored by **ADQA** → ACT / REVIEW / REJECT.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Website](https://img.shields.io/badge/narna.org-live-0a7ea4)](https://narna.org)
[![PyPI](https://img.shields.io/badge/PyPI-narna-0a7ea4)](https://pypi.org/project/narna/)
[![Model](https://img.shields.io/badge/docs-AGENT--BOT--MODEL-111)](./docs/AGENT-BOT-MODEL.md)

**Canonical product model:** [`docs/AGENT-BOT-MODEL.md`](./docs/AGENT-BOT-MODEL.md)  
**Standalone AI project** — not part of 99X. See [`docs/ABOUT.md`](./docs/ABOUT.md).

---

## The model (read this first)

```
Phone / Telegram / Discord  ←QR / chat→  Desktop NARNA Bot
                                          Claude CLI · Codex · BYOK
                                                    │
                                                    ▼
                                           ADQA → Act / Review
```

| Layer | Role |
|-------|------|
| **Desktop bot** | Where intelligence runs (CLI subscription or API key) |
| **Mobile / channels** | Remote control — chat, approve, inbox |
| **ADQA** | Decision Quality Assurance — brake before dangerous tools |
| **Pro (optional)** | Cloud always-on + sync — **not** a Claude substitute |

**Mobile apps do not login Claude/ChatGPT Pro.** Subscriptions for models work on **Desktop CLI**.  
Details: [`docs/AI_CONNECT_FLOW.md`](./docs/AI_CONNECT_FLOW.md) · Pricing: [`docs/PRICING-UNIFIED.md`](./docs/PRICING-UNIFIED.md)

---

## Quick start

```bash
pip install "narna[desktop]"
# claude login   OR   codex login   OR paste API key in Desktop
narna desktop          # local bot UI + pairing QR
narna gateway run      # optional: Telegram, Discord, Slack, …
```

**Cloud / site:** [narna.org](https://narna.org) · API: `https://api.narna.org/v1/health`

---

## What is open source (MIT)

| In this repo | Optional hosted |
|--------------|-----------------|
| Agent runtime, tools, ADQA, Decision Memory | Cloud backup / sync |
| Desktop app, CLI, social gateway, MCP | Always-on Pro cloud |
| iOS / Android companion source | App Store / Play Pro SKUs |
| UGS specs, governance packages | Enterprise SSO / SLA |

---

## Social channels

| Channel | Mode | Env |
|---------|------|-----|
| Telegram | poll / webhook | `UAP_TELEGRAM_BOT_TOKEN` |
| WhatsApp | webhook (Twilio) | `UAP_TWILIO_*` |
| Discord | poll / webhook | `UAP_DISCORD_BOT_TOKEN` |
| Slack | events webhook | `UAP_SLACK_BOT_TOKEN` |
| X · Facebook · YouTube · … | see docs | [`docs/SOCIAL-CHANNELS.md`](./docs/SOCIAL-CHANNELS.md) |

---

## Agent capabilities

- **44+ tools** — shell, browser, code, search, skills, cron, voice  
- **Engines** — Claude CLI · Codex CLI · OpenAI / Anthropic / Gemini / local BYOK  
- **Memory** — FTS5 + MEMORY.md + Decision Memory  
- **ADQA** — evidence · risk · policy · confidence before act  
- **MCP** — `narna evaluate`, `narna_agent_ask`

Parity vs Hermes/OpenClaw: [`docs/PARITY-ROADMAP.md`](./docs/PARITY-ROADMAP.md)

---

## OpenClaw + NARNA ADQA

```json
"mcp": {
  "servers": {
    "narna": {
      "url": "https://api.narna.org/mcp",
      "headers": { "Authorization": "Bearer uap_live_…" }
    }
  }
}
```

Skill: [`plugins/narna-openclaw/`](./plugins/narna-openclaw/)

---

## Governance (enterprise)

```python
from narna import wrap
agent = wrap(my_langgraph_app, vap=True, mode="enforce")
```

Docs: [`docs/DECISION-OS.md`](./docs/DECISION-OS.md) · [`docs/DIFFERENTIATION.md`](./docs/DIFFERENTIATION.md)

---

## Links

| | |
|--|--|
| Site | https://narna.org |
| **Agent bot model** | [`docs/AGENT-BOT-MODEL.md`](./docs/AGENT-BOT-MODEL.md) |
| GitHub | https://github.com/hanyangkai/narna |
| AI connect | [`docs/AI_CONNECT_FLOW.md`](./docs/AI_CONNECT_FLOW.md) |
| Pricing | [`docs/PRICING-UNIFIED.md`](./docs/PRICING-UNIFIED.md) |
| Install | [`docs/INSTALL.md`](./docs/INSTALL.md) |
| Social | [`docs/SOCIAL-CHANNELS.md`](./docs/SOCIAL-CHANNELS.md) |

## License

MIT
