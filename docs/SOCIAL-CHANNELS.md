# Social channels — NARNA Agent gateway

**Goal:** One agent, every social surface — with ADQA on every reply.

## Architecture

```
Inbound (webhook or poll) → UnifiedGateway / Cloud webhook → NarnaAgent.ask → ADQA → outbound reply
```

Registry: [`src/uap/channels/registry.py`](../src/uap/channels/registry.py)

```bash
narna gateway channels   # list channels + env keys
narna gateway status
narna gateway run        # poll Telegram, Discord, Slack, YouTube
```

Cloud webhooks base: `https://api.narna.org`

---

## Live channels

### Telegram
- **Env:** `UAP_TELEGRAM_BOT_TOKEN`
- **Webhook:** `POST /v1/agent/telegram/webhook`
- **Poll:** `narna gateway run`

### WhatsApp (Twilio)
- **Env:** `UAP_TWILIO_ACCOUNT_SID`, `UAP_TWILIO_AUTH_TOKEN`, `UAP_TWILIO_WHATSAPP_FROM`
- **Webhook:** `POST /v1/agent/whatsapp/webhook`

### Discord
- **Env:** `UAP_DISCORD_BOT_TOKEN`, `UAP_DISCORD_POLL_CHANNELS` (comma-separated)
- **Webhook:** `POST /v1/agent/discord/webhook`

### Slack
- **Env:** `UAP_SLACK_BOT_TOKEN`
- **Webhook:** `POST /v1/agent/slack/events`

---

## Beta channels (new)

### X (Twitter)
- **Env:** `UAP_X_BEARER_TOKEN`, `UAP_X_API_SECRET` (CRC), optional `UAP_X_BOT_USER_ID`
- **Webhook:** `GET|POST /v1/agent/x/webhook`
- **Outbound:** DM or reply-to-tweet (280 chars unless `UAP_X_DM_MODE=1`)

### Facebook Messenger
- **Env:** `UAP_FB_PAGE_ACCESS_TOKEN`, `UAP_FB_VERIFY_TOKEN`
- **Webhook:** `GET|POST /v1/agent/facebook/webhook`

### YouTube
- **Env:** `UAP_YOUTUBE_API_KEY`, `UAP_YOUTUBE_CHANNEL_ID` or `UAP_YOUTUBE_POLL_CHANNELS`
- **Reply auth:** `UAP_YOUTUBE_OAUTH_TOKEN`
- **Poll:** included in `narna gateway run`
- **Webhook relay:** `POST /v1/agent/youtube/webhook`

### Instagram
- **Env:** `UAP_IG_PAGE_ACCESS_TOKEN`, `UAP_FB_VERIFY_TOKEN` (shared Meta app)
- **Webhook:** `GET|POST /v1/agent/instagram/webhook`

---

## Planned

| Channel | Env prefix | Notes |
|---------|------------|--------|
| TikTok | `UAP_TIKTOK_*` | Business API messaging — ingest stub |
| LinkedIn | `UAP_LINKEDIN_ACCESS_TOKEN` | Partner messaging API |

---

## Cron delivery (`deliverTo`)

Scheduled jobs can fan out to any configured channel:

```json
{
  "deliverTo": "123456789",
  "channel": "telegram"
}
```

Supported: `telegram`, `discord`, `slack`, `email`, `whatsapp`, `x`, `facebook`, `youtube`, `instagram`

---

## Pairing (DM safety)

```bash
export UAP_GATEWAY_PAIRING=1
narna gateway pair --channel telegram --external-id CHAT_ID
```

---

## OpenClaw

Add NARNA MCP to `~/.openclaw/openclaw.json` — see [`plugins/narna-openclaw/SKILL.md`](../plugins/narna-openclaw/SKILL.md).

Hermes users: run NARNA gateway beside Hermes; ADQA scores Hermes tool plans via MCP.
