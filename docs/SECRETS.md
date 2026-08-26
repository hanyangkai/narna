# Secrets & keys needed for NARNA Ask Agent (prod / GitHub Actions)

**Status:** code is live on VPS; most LLM/channel features stay mock until secrets are set.

## 1) VPS `.env` (`/opt/narna/web/deploy/selfhost/.env`)

| Key | Required? | Purpose |
|-----|-----------|---------|
| `UAP_OPENROUTER_API_KEY` | **Yes for live LLM** | Hosted Ask models |
| `UAP_ROUTER_PROVIDER` | set `openrouter` when key present | mock \| openrouter \| openai \| ollama |
| `UAP_TELEGRAM_BOT_TOKEN` | optional | Telegram Ask |
| `UAP_TELEGRAM_WEBHOOK_SECRET` | optional | Telegram webhook auth |
| `UAP_DISCORD_BOT_TOKEN` | optional | Discord Ask |
| `UAP_DISCORD_WEBHOOK_SECRET` | optional | Discord webhook auth |
| `UAP_SLACK_BOT_TOKEN` | optional | Slack Events Ask |
| `UAP_TWILIO_ACCOUNT_SID` | optional | WhatsApp |
| `UAP_TWILIO_AUTH_TOKEN` | optional | WhatsApp |
| `UAP_TWILIO_WHATSAPP_FROM` | optional | e.g. `whatsapp:+14155238886` |
| `UAP_SIGNAL_WEBHOOK_URL` | optional | Signal outbound bridge URL |
| `UAP_SHELL_BACKEND` | optional | `local` (default) \| `docker` |
| `UAP_JOBS_TICK_SECRET` | optional | Protect `/v1/agent/jobs/tick-all` |
| `POSTGRES_PASSWORD` | already on VPS | DB |
| Crypto RPC / wallet | already for billing | USDC/USDT |

## 2) GitHub Actions secrets (for auto-deploy)

Repo → Settings → Secrets and variables → Actions:

| Secret | Purpose |
|--------|---------|
| `VPS_HOST` | `46.62.163.209` (or `root@46.62.163.209`) |
| `VPS_SSH_KEY` | Private key contents of working deploy key (`hetzner_963x_nopass`) |
| `VPS_SSH_USER` | `root` (if host is IP-only) |
| `OPENROUTER_API_KEY` | Optional: workflow can patch VPS env on deploy |
| `TELEGRAM_BOT_TOKEN` | Optional patch |
| `DISCORD_BOT_TOKEN` | Optional patch |
| `SLACK_BOT_TOKEN` | Optional patch |
| `TWILIO_ACCOUNT_SID` | Optional |
| `TWILIO_AUTH_TOKEN` | Optional |
| `TWILIO_WHATSAPP_FROM` | Optional |

Workflow: `.github/workflows/deploy-vps.yml` (manual `workflow_dispatch` + push to `main` on agent paths).

## 3) Webhook URLs to configure after tokens

- Telegram: `https://api.narna.org/v1/agent/telegram/webhook`
- Discord: `https://api.narna.org/v1/agent/discord/webhook`
- Slack Events: `https://api.narna.org/v1/agent/slack/events`
- WhatsApp Twilio: `https://api.narna.org/v1/agent/whatsapp/webhook`
- Signal inbound: `https://api.narna.org/v1/agent/signal/webhook`
- Email inbound: `https://api.narna.org/v1/agent/email/webhook`

## 4) Minimum to leave mock mode

Send at least:

1. **OpenRouter API key**
2. (Nice) **Telegram bot token** for phone chat

Paste here or put in GitHub secrets — do not commit into the repo.
