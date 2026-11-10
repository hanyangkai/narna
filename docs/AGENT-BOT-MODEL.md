# NARNA Agent Bot Model (canonical)

**Status:** Canonical product model for website + GitHub  
**Audience:** Users, contributors, store reviewers

---

## One sentence

**NARNA is an open-source AI agent bot:** it runs on your desktop (Claude / Codex CLI or BYOK), you remote it from phone, and **ADQA** scores every risky action before it runs.

---

## How it works (MausBot-style)

```
┌──────────────────────┐         QR pair          ┌─────────────────────┐
│  Phone / Telegram /  │ ◄──────────────────────► │  Desktop NARNA Bot  │
│  WhatsApp / Discord  │     chat · approve       │  Claude CLI / Codex │
└──────────────────────┘                          │  or BYOK API keys   │
                                                  │         │           │
                                                  │         ▼           │
                                                  │  ADQA · tools · mem │
                                                  └─────────────────────┘
```

1. **Desktop is the bot.** Install NARNA Desktop → login Claude Code CLI or Codex CLI (your subscription) **or** paste an API key (BYOK).
2. **Phone is the remote.** Pair with QR. Chat, approve, inbox — the heavy work stays on the PC.
3. **ADQA is the brake.** Before shell / pay / send / delete-class actions: score → ACT / REVIEW / REJECT.
4. **Channels optional.** Same bot can answer Telegram, WhatsApp, Discord, X, … via `narna gateway`.

---

## Two paths to intelligence

| Path | Where | Who pays the model |
|------|--------|--------------------|
| **A — Your AI (default)** | Desktop CLI login (Claude Pro / ChatGPT) or API key | You → Anthropic / OpenAI |
| **B — NARNA Pro** | Cloud always-on + sync + mobile inbox | You → NARNA ($20/mo) **plus** still BYOK for tokens |

**NARNA Pro does not replace Claude/GPT.** It hosts the bot when your PC is off and syncs devices. Model tokens stay BYOK / CLI.

Mobile apps **cannot** log into Claude/ChatGPT Pro inside the app. Subscriptions for models run on **Desktop CLI** (Path A).

Details: [`docs/AI_CONNECT_FLOW.md`](./AI_CONNECT_FLOW.md) · Pricing: [`docs/PRICING-UNIFIED.md`](./PRICING-UNIFIED.md)

---

## What is open source

| Open (MIT) | Hosted (optional) |
|------------|-------------------|
| Agent runtime, tools, ADQA, Decision Memory | Cloud backup / sync |
| Desktop app, CLI, gateway, MCP plugins | Always-on cloud brain |
| Mobile companion source (this monorepo) | App Store / Play Pro entitlement |
| Specs (UGS), governance packages | Enterprise SSO / SLA |

Repo: https://github.com/hanyangkai/narna · Site: https://narna.org

---

## Vs Hermes / OpenClaw / MausBot

| | Hermes / OpenClaw | MausBot | **NARNA** |
|--|-------------------|---------|-----------|
| Agent + tools | ✅ | ✅ (CLI engines) | ✅ |
| Desktop + phone remote | — | ✅ | ✅ |
| Claude/Codex CLI path | varies | ✅ | ✅ |
| **Decision quality gate (ADQA)** | ❌ | ❌ | ✅ |
| Open social gateway | varies | — | ✅ |

---

## Quick start

```bash
pip install "narna[desktop]"
# Claude Code CLI or Codex CLI → login with your subscription
narna desktop          # local bot UI + pairing QR
narna gateway run      # optional social channels
```

Mobile: install NARNA app → **Connect your AI** (pair Desktop) or **Subscribe NARNA Pro** (cloud + still BYOK).
