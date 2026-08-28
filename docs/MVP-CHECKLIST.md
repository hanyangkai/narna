# NARNA MVP checklist — honest status

**As of 2026-08-28.** Legend: ✅ shipped · 🟡 partial · ❌ missing

**7-day launch:** [`docs/launch/`](./launch/) · [`ship-log/`](./ship-log/)

## Core product

| Item | Status | Notes |
|------|--------|-------|
| **NARNA Specification v0.1** | ✅ | [`specs/RELEASE-v0.1.md`](../specs/RELEASE-v0.1.md) |
| **`narna.yaml` manifest** | ✅ | `narna init` · [`templates/narna.yaml`](../templates/narna.yaml) |
| **Python SDK** | ✅ | `pip install narna` — **target 0.2.2** (desktop + prod parity) |
| **CLI** | ✅ | `narna desktop` · `narna config` · gateway · skills |
| **MCP ADQA + ask** | ✅ | `https://api.narna.org/mcp` · OpenClaw skill |
| **Ask NARNA + Model Router** | ✅ | BYOK · `mockMode` surfaced when no key |
| **Desktop PC** | ✅ | v0.2.1+ zip · `narna desktop` |
| **Prod agent parity** | 🟡 | Playwright on VPS · docker shell needs socket mount |
| **Decision Trace / Replay / Benchmark** | ✅ | moat path |

## GTM / business

| Item | Status | Notes |
|------|--------|-------|
| Landing + Download + Pricing | ✅ | GTM pass 2026-08-28 |
| OpenClaw integration docs | ✅ | `plugins/narna-openclaw/SKILL.md` + `/docs/integrations` |
| Crypto billing (USDC/USDT) | 🟡 | Live bot on VPS · needs first paid E2E |
| PyPI **0.2.x** published | ✅ | `narna==0.2.3` on PyPI (CI `publish-pypi.yml`) |
| `@narna/client` npm | ❌ |
| **≥1 paying customer** | ❌ | north-star KPI |
| Ship log / outbound rhythm | 🟡 | [`ship-log/2026-08-28.md`](./ship-log/2026-08-28.md) |
| Telegram gateway demo | ❌ | needs `UAP_TELEGRAM_BOT_TOKEN` on VPS |
| Second UGS implementer | ❌ |

## Quick verify

```bash
pip install "narna[desktop]==0.2.2"
narna desktop
curl -s https://api.narna.org/v1/health | jq '.version,.browser'
python -m pytest tests/test_prod_parity.py -q
```
