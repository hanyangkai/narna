# NARNA MVP checklist — honest status

**As of 2026-08-31.** Legend: ✅ shipped · 🟡 partial · ❌ missing

**7-day launch:** [`docs/launch/`](./launch/) · [`ship-log/`](./ship-log/)

## Core product

| Item | Status | Notes |
|------|--------|-------|
| **NARNA Specification v0.1** | ✅ | [`specs/RELEASE-v0.1.md`](../specs/RELEASE-v0.1.md) |
| **`narna.yaml` manifest** | ✅ | `narna init` · [`templates/narna.yaml`](../templates/narna.yaml) |
| **Python SDK** | ✅ | `pip install narna` — **0.2.3** on PyPI |
| **CLI** | ✅ | `narna desktop` · `narna gateway channels` · skills |
| **MCP ADQA + ask** | ✅ | `https://api.narna.org/mcp` · OpenClaw skill |
| **Ask NARNA + Model Router** | ✅ | BYOK · `mockMode` surfaced when no key |
| **Desktop PC** | ✅ | v0.2.1+ zip · `narna desktop` |
| **Social channel registry** | ✅ | 12 channels · [`docs/SOCIAL-CHANNELS.md`](./SOCIAL-CHANNELS.md) |
| **X / Facebook / YouTube / IG** | 🟡 | Beta gateways + Cloud webhooks |
| **Prod agent parity** | 🟡 | Playwright on VPS · docker shell needs socket mount |
| **Decision Trace / Replay / Benchmark** | ✅ | moat path |

## GTM / business

| Item | Status | Notes |
|------|--------|-------|
| Landing + Download + Pricing | ✅ | AI Agent positioning refresh 2026-08-31 |
| OpenClaw + Hermes integration docs | ✅ | [`docs/PARITY-ROADMAP.md`](./PARITY-ROADMAP.md) |
| GitHub About / README (AI Agent) | ✅ | [`.github/REPOSITORY.md`](../.github/REPOSITORY.md) |
| Crypto billing (USDC/USDT) | 🟡 | Live bot on VPS · needs first paid E2E |
| `@narna/client` npm | ❌ |
| **≥1 paying customer** | ❌ | north-star KPI |
| Ship log / outbound rhythm | 🟡 | [`ship-log/2026-08-28.md`](./ship-log/2026-08-28.md) |
| Telegram gateway demo | 🟡 | Bot live on VPS — DM bot to verify |
| Second UGS implementer | ❌ |

## Quick verify

```bash
pip install "narna[desktop]==0.2.3"
narna gateway channels
narna desktop
curl -s https://api.narna.org/v1/health | jq '.version,.browser'
python -m pytest tests/test_social_channels.py tests/test_prod_parity.py -q
```
