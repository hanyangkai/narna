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

### Hermes gap (v1 → v1.5)

| Hermes-like | NARNA |
|-------------|-------|
| Tool loop | web_search, web_fetch, calculator, **code_exec**, datetime, memory, skills |
| Workspace | **workspace_list/read/write** under `.uap/agent-workspace` |
| Skills | auto-capture DQS≥75 + **improve_from_outcome** |
| Multi-turn | sessions (web + Telegram) |
| Cron | **Agent jobs** + `/v1/agent/jobs/tick` |
| Phone | PWA + Telegram + **SSE** `/v1/agent/ask/stream` |

Still not: full OS shell, Playwright browser bot, Discord/WhatsApp, unsupervised self-modify of runtime.

---

## Non-goals

- Train a foundation model  
- Replace ChatGPT via browser MITM (Guardian extension is separate)  
- Absolute correctness claims
- Full Hermes Agent clone (execution sandbox + every channel)