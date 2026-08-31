# Changelog

## [0.2.5] — 2026-08-31

### Desktop agent (Hermes-style)
- Unified agent runtime on `~/.narna` for `desktop`, `chat`, `ask`, `gateway`
- Desktop UI: setup wizard, Chat/Tools/Skills/Settings tabs
- New APIs: `/v1/agent/status`, `/v1/agent/tools`, `/v1/agent/skills`, `/v1/agent/traces`
- macOS portable build (`NARNA-Desktop-macos.zip`) in CI
- Download page: Windows + macOS one-click zips

## [0.2.4] — 2026-08-31

### Agent + social gateway
- README repositioned: **AI Agent first**, ADQA as unique moat (separate from 99X — `docs/ABOUT.md`)
- **12-channel registry**: Telegram, WhatsApp, Discord, Slack, X, Facebook, YouTube, Instagram (+ TikTok/LinkedIn planned)
- New gateways: `x_gateway`, `facebook_gateway`, `youtube_gateway`, `instagram_gateway`
- Cloud webhooks: `/v1/agent/x|facebook|instagram|youtube/webhook`
- `narna gateway channels` CLI · YouTube comment poll in `gateway run`
- Docs: `SOCIAL-CHANNELS.md`, `PARITY-ROADMAP.md` · tests: `test_social_channels.py`

## [0.2.3] — 2026-08-28

### Fix
- PyPI wheel build: remove duplicate `desktop_static` force-include (hatchling conflict)

## [0.2.2] — 2026-08-28

### GTM
- Ask: BYOK banner, `mockMode` in API when no LLM key, removed silent mock dropdown
- Landing: Hermes/OpenClaw positioning, OpenClaw MCP snippet, Desktop CTA
- Pricing: “Why upgrade” section
- Docs: OpenClaw 2-min MCP setup
- PyPI publish workflow: `workflow_dispatch` + version align

## [0.2.1] — 2026-08-27

### Prod agent parity (Hermes + OpenClaw)
- VPS: `INSTALL_BROWSER=1` + `UAP_BROWSER_ENABLED=1`; `/v1/health` exposes `browser.ready`
- VPS shell default `docker` with clear error if daemon/socket missing (`UAP_SHELL_FALLBACK_LOCAL`)
- Gateway status: per-channel `mode` (`poll|webhook|stub`); Discord/Slack message dedupe
- Gateway profile: pairing default on
- MCP: `narna_runtime_status`; OpenClaw skill `plugins/narna-openclaw/SKILL.md`
- `narna config show|set` + `~/.narna/config.yaml` support
- Docs: [`PROD-AGENT-PARITY.md`](docs/PROD-AGENT-PARITY.md), honest channel matrix

## [0.2.0] — 2026-08-27

### Desktop (download for PC)
- `narna desktop` — local Ask UI on 127.0.0.1, BYOK keys in `~/.narna`
- Portable **NARNA-Desktop.exe** (PyInstaller) — no Python required on Windows
- Install scripts: `desktop/install.ps1`, `desktop/install.sh`
- Download page: https://narna.org/download

### Agent runtime (Hermes parity P1–P9)
- 44 tools including browser_vision, execute_code, shell backends (local/docker/ssh/modal/daytona)
- `narna tui`, `narna chat`, gateway compose profile + DM pairing
- TTS outbound + Telegram voice reply (BYOK)

### Decision moat (Track B)
- Decision Trace, Replay, universal `narna evaluate`, router modes (cheap/quality/critical)
- MEMORY.md / USER.md injection
- Decision Benchmark v0 (`narna benchmark run`)
- Skills Hub zip/sync + public index

### SDK
- `from narna.runtime import NarnaAgent` · `from narna.decision import DecisionTraceStore`

## [0.1.0] — 2026-07-20

- Initial PyPI release — UGS governance SDK, `pip install narna`
