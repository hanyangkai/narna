# Secrets & keys — Hermes-aligned (BYOK)

NARNA does **not** require a company OpenRouter key. Users bring their own LLM keys (Hermes/OpenClaw model).

## User keys (not GitHub secrets)

| Where | What |
|-------|------|
| Ask UI → “Add LLM key” | OpenRouter / OpenAI / Ollama key in browser localStorage |
| `/settings/models` | Persist BYO on org (any plan including Free) |

## GitHub Actions — deploy only

| Secret | Purpose |
|--------|---------|
| `VPS_HOST` | `46.62.163.209` |
| `VPS_SSH_KEY` | Private key (`hetzner_963x_nopass`) |
| `VPS_SSH_USER` | `root` (optional) |

Optional channel bot tokens (only if you run NARNA’s shared Telegram/Discord bots for users who chat there without the web UI):

| Secret | Purpose |
|--------|---------|
| `TELEGRAM_BOT_TOKEN` | Shared Telegram bot |
| `DISCORD_BOT_TOKEN` | Shared Discord bot |
| `SLACK_BOT_TOKEN` | Shared Slack bot |
| Twilio trio | Shared WhatsApp |

**Do not set `OPENROUTER_API_KEY` on the server** unless you explicitly want a company-paid demo model (not Hermes-default).

Workflow: `.github/workflows/deploy-vps.yml`
