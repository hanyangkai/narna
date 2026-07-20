# NARNA MVP checklist — honest status

**As of 2026-07-20.** Legend: ✅ shipped · 🟡 partial · ❌ missing

## Core product (your list)

| Item | Status | Notes |
|------|--------|-------|
| **NARNA Specification v0.1 (open standard)** | 🟡 | `specs/VERSION` = `0.1.0`; NGS RFCs mostly Accepted; set README still **Draft v0.4** — not formally frozen as "v0.1 release" |
| **`narna.yaml` manifest** | ✅ | `discover_manifest`, `load_manifest`, compile → constitution; `narna init`; [`templates/narna.yaml`](../templates/narna.yaml) |
| **Python SDK (light integration)** | 🟡 | `pip install -e .` works; `wrap()`, `@policy`, `Agent`, `ConstitutionRuntime`; **not on PyPI yet** |
| **CLI** (`init`, `validate`, `verify`…) | ✅ | `init`, `validate`, `doctor`, `prove`, `verify`, `passport --verify`, `governance`, `conformance`, `push`, packages… |
| **OpenTelemetry adapter** | 🟡 | Span hooks + `narna otel export` OTLP bridge; optional deps not bundled |
| **OpenAI Agents SDK adapter** | 🟡 | `narna-openai` wraps `run`/`invoke`/`chat.completions.create`; enforce-before in base; no official upstream middleware PR |
| **MCP adapter** | 🟡 | `narna-mcp` hooks `call_tool` / `list_tools`; enforce-before; needs real MCP server e2e demo in docs |

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

1. **Freeze spec** — tag `ugs-v0.1.0`, update `specs/README` Draft → Released  
2. **PyPI** — valid token → `narna==0.1.0`  
3. **One e2e doc per adapter** — OpenAI + MCP + OTel with copy-paste repo  
4. **Paddle live** — seller approved  
5. **Ship log rhythm** — daily file + Discussion post  

## Quick verify commands

```bash
pip install -e .
narna init --name Demo
narna validate
narna doctor
python -c "from narna import wrap; print('ok')"
python -m unittest tests.test_adapter_enforce -v
```
