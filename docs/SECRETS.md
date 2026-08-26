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

## Optional agent runtime (self-host / local)

| Env | Purpose |
|-----|---------|
| `UAP_SHELL_BACKEND` | `local` (default) · `docker` · `ssh` · `modal` · `daytona` |
| `UAP_SHELL_REQUIRE_APPROVAL` | `1` to require `approved=true` on `shell_exec` |
| `UAP_SHELL_SSH_HOST` / `UAP_SHELL_SSH_USER` | SSH backend |
| `UAP_MODAL_TOKEN` / `UAP_MODAL_APP` | Modal sandbox exec (opt-in) |
| `UAP_MODAL_EXEC_URL` | Override Modal exec HTTP endpoint |
| `UAP_DAYTONA_API_KEY` / `UAP_DAYTONA_WORKSPACE_ID` | Daytona exec (opt-in) |
| `UAP_DAYTONA_API_URL` | Default `https://api.daytona.io` |
| `UAP_OPENAI_API_KEY` | Whisper STT + TTS outbound (BYOK) |
| `UAP_GATEWAY_VOICE_REPLY` | `1` — reply to Telegram voice memos with TTS voice notes |
| `UAP_GATEWAY_PAIRING` | `1` — unknown DMs must `/pair CODE` before Ask |
| `UAP_SKILL_HUB_INDEX_URL` | Public skill index JSON URL (or local path) for `hub-sync` |
| `UAP_SKILL_HUB_AUTOPUBLISH` | `1` — publish skill to local hub when Ask DQS≥80 |
| `UAP_JOB_DELIVER_AUDIO` | `1` — job delivery prefers Telegram `sendVoice` when `audioPath` set |
| `UAP_BROWSER_ENABLED` | Playwright browser tools |

TUI: `pip install 'narna[tui]'` then `narna tui`. Compose gateway: `docker compose --profile gateway up -d`.

Skills Hub: `narna skills hub-sync --url …` · `narna skills export-zip` · `POST /v1/agent/skills/hub/sync`.

Workflow: `.github/workflows/deploy-vps.yml`
