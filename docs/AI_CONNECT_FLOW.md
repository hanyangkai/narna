# User AI connect flow — External AI vs NARNA Pro

## Two ways to use AI Agent

```
┌─────────────────────────────────────────────────────────┐
│  PATH A — AI ngoài (MausBot-style)                      │
│  Claude Pro / ChatGPT sub hoặc API key trên Desktop     │
│  → Pair app phone (QR)                                  │
│  → User trả phí model cho Anthropic/OpenAI              │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  PATH B — Mua NARNA Pro (App Store / Play only)         │
│  Mở cloud always-on, inbox, routines, voice, sync       │
│  → Gắn API key vào cloud (Settings) để agent chạy       │
│    khi máy tắt  HOẶC  vẫn pair Desktop CLI              │
│  → NARNA Pro ≠ hết phí Claude/GPT (vẫn BYOK)            │
└─────────────────────────────────────────────────────────┘
```

## What happens when user downloads the app

1. **Không** tự login Claude/ChatGPT trong app.  
2. Onboarding hiện **2 thẻ**: Dùng AI của bạn · Mua NARNA Pro.  
3. Path A → hướng dẫn Desktop login CLI → Pair QR.  
4. Path B → Subscribe Apple/Google → (optional) dán API key cloud.  
5. Desktop mở pairing có thể gọi `POST /v1/mobile/pairing/invite` để chuẩn bị push “Sẵn sàng ghép nối”.

## APIs

| Endpoint | Role |
|----------|------|
| `GET /v1/mobile/onboarding/status` | Dual paths + `ai_ready` |
| `GET/POST/DELETE /v1/mobile/ai/providers…` | BYOK keys on org (cloud) |
| `GET /v1/mobile/subscription/products` | Store SKUs |
| `POST /v1/billing/store/verify` | IAP/Play → set `org.plan` |
| `POST /v1/mobile/pairing/invite` | Desktop notify phone |

## Money

| Ai thu | Cái gì |
|--------|--------|
| Anthropic / OpenAI | Token / subscription model |
| Apple / Google → NARNA | Pro $19.99/mo · Team seats |
| Web crypto | Pro/Team trên web only — **không** trong app |

## Desktop CLI (Path A)

```bash
# Claude
# install Claude Code / claude CLI → claude login

# ChatGPT / Codex
# install Codex CLI → login with ChatGPT account

narna desktop   # open Pairing → QR for phone
```
