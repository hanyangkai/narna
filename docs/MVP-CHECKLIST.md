# NARNA MVP checklist — honest status

**As of 2026-07-21.** Legend: ✅ shipped · 🟡 partial · ❌ missing

**7-day launch:** [`docs/launch/`](./launch/) · track daily in [`launch/SCORECARD.md`](./launch/SCORECARD.md)

## Core product (your list)

| Item | Status | Notes |
|------|--------|-------|
| **NARNA Specification v0.1 (open standard)** | ✅ | Released — [`specs/RELEASE-v0.1.md`](../specs/RELEASE-v0.1.md); tag `ugs-v0.1.0` when merging |
| **`narna.yaml` manifest** | ✅ | `discover_manifest`, `load_manifest`, compile → constitution; `narna init`; [`templates/narna.yaml`](../templates/narna.yaml) |
| **Python SDK (light integration)** | ✅ | `pip install narna==0.1.0` on PyPI |
| **CLI** (`init`, `validate`, `verify`…) | ✅ | Full surface including `conformance` |
| **OpenTelemetry adapter** | ✅ | e2e stub + docs; optional OTLP deps |
| **OpenAI Agents SDK adapter** | ✅ | e2e stub + docs; enforce-before |
| **MCP adapter** | ✅ | e2e stub + HIPAA deny proof + docs |

## Also shipped (beyond your list)

| Item | Status |
|------|--------|
| LangGraph, CrewAI, Anthropic, Google, Moltbook adapters | 🟡 thin wrap |
| Enforce-before policy gate (`mode=enforce`) | ✅ |
| 13 Governance Packages (EU AI Act, GDPR, HIPAA…) | ✅ seed |
| Cloud API + site `narna.org` | ✅ |
| Public passport verify API | ✅ |
| GU / Governor / sessions | ✅ |
| **Decision OS / Decision Package** | ✅ | NGS-0014 · `narna decision evaluate` · `POST /v1/decision/evaluate` |
| **Capability Passport (Guardian L2)** | ✅ | NGS-0015 · evaluate + adapter enforce when `NARNA_GUARDIAN=1` |
| **Local Kill Token** | ✅ | NGS-0019 · `narna kill issue` · `POST /v1/guardian/kill` |
| **Threat Engine v0** | ✅ | NGS-0017 · graph heuristics · `narna threat analyze` |
| Guardian Domain/Global Kill · Collective | ❌ | NGS-0019/0020 remaining tiers — see [`GUARDIAN.md`](./GUARDIAN.md) |
| Crypto billing (USDC/USDT) | ✅ Cloud checkout · card/Stripe/Paddle removed |
| Ask NARNA + Model Router | ✅ `/ask` · NGS-0028/0029 · BYO LLM Personal+ |
| PyPI `pip install narna` | ✅ `narna==0.1.0` |
| `@narna/client` npm publish | ❌ |
| ≥1 paying customer | ❌ |
| Second UGS implementer | ❌ |

## What's still missing for "done" MVP

1. ~~Freeze spec~~ ✅ `specs/RELEASE-v0.1.md`  
2. ~~**PyPI**~~ ✅ `narna==0.1.0`  
3. ~~One e2e doc per adapter~~ ✅ `docs/ADAPTERS-E2E.md` + `examples/`  
4. ~~**Crypto live**~~ ✅ RPC + bot + mock locked · plan expires 30d · unique invoice amounts · team seats  
5. **Ship log rhythm** — 7-day system ✅ [`docs/launch/`](./launch/) · Discussion posts in progress  

## Quick verify commands

```bash
pip install -e .
narna init --name Demo
narna validate
narna doctor
python examples/e2e_openai.py
python examples/e2e_mcp.py
python examples/e2e_otel.py
python -m unittest tests.test_adapter_enforce -v
```
