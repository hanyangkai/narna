# User AI connect flow — Agent bot model

Canonical overview: [`docs/AGENT-BOT-MODEL.md`](./AGENT-BOT-MODEL.md)

## Two ways to power the bot

```
┌─────────────────────────────────────────────────────────┐
│  PATH A — Your AI on Desktop (default · MausBot-style)  │
│  Claude Code CLI / Codex CLI (subscription) or API key  │
│  → Pair phone (QR)                                      │
│  → You pay Anthropic / OpenAI for model use             │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  PATH B — NARNA Pro (App Store / Play / web crypto)     │
│  Cloud always-on, inbox, routines, voice, sync          │
│  → Still attach BYOK for tokens when cloud runs         │
│  → NARNA Pro ≠ Claude/GPT subscription                  │
└─────────────────────────────────────────────────────────┘
```

## What happens when user opens the app

1. **No** Claude/ChatGPT login inside the mobile app.  
2. Onboarding shows **2 cards**: Use your AI · Subscribe NARNA Pro.  
3. Path A → Desktop: CLI login → Pair QR.  
4. Path B → Apple/Google (or web crypto) → optional cloud API key.  
5. Desktop can `POST /v1/mobile/pairing/invite` to nudge the phone.

## APIs

| Endpoint | Role |
|----------|------|
| `GET /v1/mobile/onboarding/status` | Dual paths + `ai_ready` |
| `GET/POST/DELETE /v1/mobile/ai/providers…` | BYOK keys on org (cloud) |
| `GET /v1/mobile/subscription/products` | Store SKUs |
| `POST /v1/billing/store/verify` | IAP/Play → set `org.plan` |
| `POST /v1/mobile/pairing/invite` | Desktop notify phone |

## Money

| Who bills | For what |
|-----------|----------|
| Anthropic / OpenAI | Model tokens / CLI subscription |
| Apple / Google → NARNA | Pro hosting on mobile |
| Web crypto → NARNA | Pro/Team on web only — **not** inside apps |

## Desktop CLI (Path A)

```bash
# Claude
# install Claude Code / claude CLI → claude login

# ChatGPT / Codex
# install Codex CLI → login with ChatGPT account

narna desktop   # open Pairing → QR for phone
```
