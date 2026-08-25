# NARNA Agent — Ask NARNA

**Status:** Active (VNext)  
**Date:** 2026-08-25  
**Specs:** NGS-0028 Model Router · NGS-0029 Agent Runtime  
**Surface:** https://narna.org/ask

---

## Two products, one core

| Product | Who | Why pay |
|---------|-----|---------|
| **NARNA Agent** | Everyone | Quota, BYO LLM, Team Decision Brain |
| **NARNA ADQA Cloud** | Developers / agents | API metering, Decision Memory sync |

Users should not need to “install NARNA to use AI.” They **Ask NARNA**; models are chosen underneath.

---

## UX principles

1. One box: type a question → get an answer with **DQS**.  
2. No model names by default (power toggle optional).  
3. No MCP / RAG jargon on the Ask page.  
4. Soft upgrade when Free quota hits → USDC Billing.

---

## Architecture

```text
Ask UI / PWA / Telegram
    →  /v1/agent/ask  (or telegram webhook)
    →  Tools loop (search, fetch, calc, memory, skills)
    →  Model Router  →  ADQA  →  Decision Memory + Skill capture
```

BYO LLM (Personal+): org stores provider + key; Free uses hosted OpenRouter only.

### Mobile

1. **PWA:** open https://narna.org/ask → Add to Home Screen (standalone Ask UX).
2. **Telegram:** set `UAP_TELEGRAM_BOT_TOKEN` and webhook to `/v1/agent/telegram/webhook`.

### Hermes / OpenClaw gap matrix (honest)

NARNA is **not** a clone of Hermes or OpenClaw. It is a **decision-quality agent**
(ADQA + Decision Memory) with a Hermes-like tool/skills loop and OpenClaw-like chat surfaces.

| Capability | Hermes | OpenClaw | NARNA now |
|------------|--------|----------|-----------|
| Tool loop | 40–60+ tools | 50+ skills/tools | ~14 tools (web, code_exec, workspace, memory, skills, delegate) |
| Terminal / OS shell | Docker/SSH/Modal sandboxes | Gateway approvals | **No** (sandbox Python only) |
| Browser automation | Playwright-class | Via skills | **No** |
| Skills | Auto-create + curator | ClawHub marketplace | Auto-capture DQS≥75 + outcome improve |
| Memory | FTS5 sessions + Honcho | Markdown + vectors | Decision Memory + session search |
| Channels | Many (TG/Discord/Slack/WA…) | **20+** gateway | Web PWA + Telegram + **Discord** |
| Cron / heartbeat | Native NL cron | Heartbeat | Agent jobs + ticker |
| Subagents | Parallel delegate | Multi-bot | `delegate_task` (single nested) |
| Model routing | OpenRouter etc. | BYOK many | Model Router (mock/OpenRouter/OpenAI/Ollama) |
| **Decision quality score** | — | — | **ADQA / DQS (unique)** |
| Marketplace skills | Skills Hub | ClawHub | **No** |

**Still open (big):** full shell sandbox, browser bot, WhatsApp/Slack/Signal, skill marketplace,
parallel multi-agent, FTS5/SQLite memory depth, desktop TUI.

**Prod ops still open:** `UAP_OPENROUTER_API_KEY` (live LLM), Telegram/Discord tokens.

### Hermes gap (v1.5 → v1.6)

| Hermes-like | NARNA |
|-------------|-------|
| Tool loop | web, calc, **code_exec**, workspace, memory, **memory_search**, skills, **delegate_task** |
| Channels | Web PWA + Telegram + **Discord** |
| Cron | Agent jobs + background ticker |
| Phone | PWA + chat gateways + SSE |

Still not: full OS shell, Playwright browser bot, WhatsApp/Slack, unsupervised self-modify of runtime.

---

## Non-goals

- Train a foundation model  
- Replace ChatGPT via browser MITM (Guardian extension is separate)  
- Absolute correctness claims
- Full Hermes Agent clone (execution sandbox + every channel)