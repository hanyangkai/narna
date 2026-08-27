# NARNA Agent — Ask NARNA

**Status:** Active  
**Date:** 2026-08-27  
**Specs:** NGS-0028 Model Router · NGS-0029 Agent Runtime · NGS-0030 Decision Trace  
**Surfaces:** https://narna.org/ask · https://narna.org/download · `narna desktop`

---

## Two products, one core

| Product | Who | Why pay |
|---------|-----|---------|
| **NARNA Agent** | Everyone | Distribution — Ask, tools, BYOK, Desktop |
| **NARNA ADQA** | Developers / agents | **Moat** — evaluate any agent's decisions |

**Market plan:** [`NARNA-MARKET-PLAN.md`](./NARNA-MARKET-PLAN.md) · **Runtime gaps:** [`HERMES-GAP-PLAN.md`](./HERMES-GAP-PLAN.md)

Users can **Ask on the web** or **download Desktop** for PC. Models are BYOK underneath.

---

## UX principles

1. One box: type a question → get an answer with **DQS**.  
2. No model names by default (power toggle optional).  
3. No MCP / RAG jargon on the Ask page.  
4. Soft upgrade when Free quota hits → USDC Billing.

---

## Architecture

```text
Ask UI / PWA / Desktop / Telegram
    →  /v1/agent/ask  (or local desktop server / webhook)
    →  Tools loop (~44 tools)
    →  Model Router  →  ADQA  →  Decision Trace + Memory + Skills
```

BYO LLM (all plans, Hermes-style): OpenRouter / OpenAI / Ollama.  
**No hosted LLM** — without a key, Ask runs **mock** (still ADQA-scored).

### Surfaces

1. **Web / PWA:** https://narna.org/ask  
2. **Desktop PC:** https://narna.org/download — `narna desktop` or portable Windows zip  
3. **CLI:** `narna chat` · `narna tui` · `narna gateway run`  
4. **Channels:** Telegram · Discord · Slack · WhatsApp (Twilio) · Signal/Email (bridge)  

### Honest capability matrix

| Capability | Hermes | NARNA now |
|------------|--------|-----------|
| Tools | 40–60+ | **44** (web, shell, browser, execute_code, skills, TTS, …) |
| Terminal | Docker/SSH/Modal/… | local · docker · ssh · modal/daytona stubs (BYOK URL) |
| Browser | Playwright | navigate/click/type/wait/screenshot/vision (on VPS with Playwright) |
| Skills | Hub | Skill Hub + SKILL.md zip + public index sync |
| Memory | Honcho | FTS5 + MEMORY.md / USER.md |
| Desktop | Native app | `narna desktop` + portable exe build |
| Decision quality | — | **ADQA · Trace · Replay · Benchmark** (moat) |

**Channels (honest):** Telegram = gold; Discord/Slack = poll when channel IDs set; WhatsApp = Twilio webhook; Signal = outbound webhook stub; Email = inbound Ask (SMTP mainly via job delivery).

Still intentionally skipped: Nous Portal clone, RL/trajectory, signed .msi/.dmg notarization.

See [`PROD-AGENT-PARITY.md`](./PROD-AGENT-PARITY.md) · [`HERMES-COMPARE.md`](./HERMES-COMPARE.md) · [`SECRETS.md`](./SECRETS.md) · [`DESKTOP.md`](./DESKTOP.md).

---

## Non-goals

- Train a foundation model  
- Replace ChatGPT via browser MITM (Guardian extension is separate)  
- Absolute correctness claims  
- Full Hermes Agent clone
