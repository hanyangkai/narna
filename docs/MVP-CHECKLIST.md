# NARNA MVP checklist — honest status

**As of 2026-07-20.** Legend: ✅ shipped · 🟡 partial · ❌ missing

## Core product (your list)

| Item | Status | Notes |
|------|--------|-------|
| **NARNA Specification v0.1 (open standard)** | ✅ | Released — [`specs/RELEASE-v0.1.md`](../specs/RELEASE-v0.1.md); tag `ugs-v0.1.0` when merging |
| **`narna.yaml` manifest** | ✅ | `discover_manifest`, `load_manifest`, compile → constitution; `narna init`; [`templates/narna.yaml`](../templates/narna.yaml) |
| **Python SDK (light integration)** | 🟡 | `pip install -e .` works; **PyPI still pending** valid token |
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
| Paddle billing | ❌ account onboarding blocked |
| PyPI `pip install narna` | ❌ token failed |
| `@narna/client` npm publish | ❌ |
| ≥1 paying customer | ❌ |
| Second UGS implementer | ❌ |

## What's still missing for "done" MVP

1. ~~Freeze spec~~ ✅ `specs/RELEASE-v0.1.md`  
2. **PyPI** — valid token → `narna==0.1.0`  
3. ~~One e2e doc per adapter~~ ✅ `docs/ADAPTERS-E2E.md` + `examples/`  
4. **Paddle live** — seller approved (account)  
5. **Ship log rhythm** — daily file ✅ · Discussion post (today)  

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
