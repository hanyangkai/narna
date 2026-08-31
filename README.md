# NARNA

**Open-source AI Agent with Decision Quality built in.**

> Run on Telegram, WhatsApp, X, Discord, and more.  
> Every action scored by **ADQA** before it executes.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Website](https://img.shields.io/badge/narna.org-live-0a7ea4)](https://narna.org)
[![PyPI](https://img.shields.io/badge/PyPI-narna-0a7ea4)](https://pypi.org/project/narna/)
[![Spec](https://img.shields.io/badge/UGS-open%20standard-111)](./specs/README.md)

**NARNA is a standalone AI project** — not part of 99X or any exchange codebase.  
See [`docs/ABOUT.md`](./docs/ABOUT.md).

---

## What NARNA is

| Layer | What it does |
|-------|----------------|
| **NARNA Agent** | BYOK agent runtime — tools, browser, memory, skills, desktop, gateway |
| **NARNA ADQA** | Decision Quality Assurance — evidence, policy, risk, confidence |
| **UGS** | Open governance standard — portable packages, audit, prove |

**Unique vs Hermes / OpenClaw:** they optimize *how agents act*. NARNA adds *whether the decision is good enough to act* — then learns from outcomes.

```
User → NARNA Agent → proposed action → ADQA score → ACT / REVIEW / REJECT → Decision Memory
```

Compatible with **OpenClaw**, **Hermes**, LangGraph, CrewAI, MCP — plug in ADQA without replacing your stack.

---

## Quick start

```bash
pip install "narna[desktop]"
narna desktop          # local agent UI
narna gateway status   # social channel readiness
narna ask "Summarize Q3 risks"
```

**Cloud:** [narna.org](https://narna.org) · API health: `https://api.narna.org/v1/health`

### OpenClaw + NARNA ADQA

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

## Social channels (agent everywhere)

| Channel | Mode | Env |
|---------|------|-----|
| Telegram | poll / webhook | `UAP_TELEGRAM_BOT_TOKEN` |
| WhatsApp | webhook (Twilio) | `UAP_TWILIO_*` |
| Discord | poll / webhook | `UAP_DISCORD_BOT_TOKEN` |
| Slack | events webhook | `UAP_SLACK_BOT_TOKEN` |
| **X (Twitter)** | webhook | `UAP_X_BEARER_TOKEN` |
| **Facebook** | webhook | `UAP_FB_PAGE_ACCESS_TOKEN` |
| **YouTube** | poll comments | `UAP_YOUTUBE_*` |
| Instagram | webhook (beta) | `UAP_IG_PAGE_ACCESS_TOKEN` |
| TikTok | webhook (planned) | `UAP_TIKTOK_*` |
| Signal / Email | webhook | see [`docs/SOCIAL-CHANNELS.md`](./docs/SOCIAL-CHANNELS.md) |

```bash
narna gateway run    # long-poll Telegram + Discord + Slack + YouTube
narna gateway channels
```

Full setup: [`docs/SOCIAL-CHANNELS.md`](./docs/SOCIAL-CHANNELS.md)

---

## Agent capabilities

- **44+ tools** — shell, browser (Playwright), code, search, skills, cron, voice
- **BYOK** — OpenAI, Anthropic, Gemini, DeepSeek, Qwen, local models
- **Memory** — FTS5 + MEMORY.md / USER.md + Decision Memory
- **Skills** — SKILL.md hub, zip export/import, OpenClaw-compatible
- **Subagents** — `execute_code` RPC, delegate tasks
- **Desktop** — Windows / Mac / Linux ([download](https://narna.org/download))
- **MCP** — `narna evaluate`, `narna_agent_ask` for any agent

Hermes/OpenClaw parity tracker: [`docs/PARITY-ROADMAP.md`](./docs/PARITY-ROADMAP.md)

---

## Governance (enterprise)

```python
from narna import wrap

agent = wrap(my_langgraph_app, vap=True, mode="enforce")
agent.run("approve vendor contract")
```

```bash
narna decision evaluate --action contract.sign --question "Should we sign?"
```

| Concept | Role |
|---------|------|
| **VAP** | Verify · Audit · Prove |
| **GU** | Cloud metering unit |
| **Governance Package** | EU AI Act, HIPAA, GDPR… portable YAML |
| **Decision OS** | Evidence · risk · approval · audit trail |

Docs: [`docs/DECISION-OS.md`](./docs/DECISION-OS.md) · [`docs/DIFFERENTIATION.md`](./docs/DIFFERENTIATION.md)

---

## Links

| | |
|--|--|
| Site | https://narna.org |
| GitHub | https://github.com/hanyangkai/narna |
| API | https://api.narna.org/v1/health |
| MCP | https://api.narna.org/mcp |
| MVP status | [`docs/MVP-CHECKLIST.md`](./docs/MVP-CHECKLIST.md) |
| Social setup | [`docs/SOCIAL-CHANNELS.md`](./docs/SOCIAL-CHANNELS.md) |
| Hermes compare | [`docs/HERMES-COMPARE.md`](./docs/HERMES-COMPARE.md) |
| Ship log | [`docs/SHIP-LOG.md`](./docs/SHIP-LOG.md) |
| Install | [`docs/INSTALL.md`](./docs/INSTALL.md) |

## Compatibility

OpenAI · Anthropic · Google · MCP · OpenTelemetry · LangGraph · CrewAI · OpenClaw · Hermes · Docker

## License

MIT
