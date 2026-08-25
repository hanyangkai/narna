# NARNA

**The Decision Layer for Enterprise AI.**

> **Connect your enterprise data. Let AI reason. Keep humans in control.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Website](https://img.shields.io/badge/narna.org-live-0a7ea4)](https://narna.org)
[![Spec](https://img.shields.io/badge/UGS-open%20standard-111)](./specs/README.md)

**Enterprise Decision Intelligence Platform** — Decision OS on open UGS governance infrastructure.  
**North star:** [ADQA](./docs/ADQA.md) · [Decision Intelligence OS](./docs/DECISION-INTELLIGENCE.md) — memory is feedstock; DQS is the KPI.  
**Slogan:** The Trust Layer for AI Decisions. · Remember better inputs. Decide better. Learn continuously.  
**Surfaces:** Decision OS · Decision Memory · [Guardian Network](./docs/GUARDIAN-NETWORK.md) · [`apps/guardian-extension/`](./apps/guardian-extension/).

NARNA does **not** replace CMEM-style memory — NARNA makes agents **decide better** and **learn from outcomes**.


| Name | Role |
|------|------|
| **NARNA** | Brand + Decision Layer + Guardian path + reference runtime |
| **UGS** | Universal Governance Specification (open standard) |
| **VAP** | Verify · Audit · Prove |
| **GU** | Governance Unit (Cloud metering) |
| **Governance Package** | Portable compliance rules (EU AI Act, HIPAA, GDPR…) |
| **Decision Package** | Industry decision apps (Legal, Procurement, Finance…) |
| **Decision OS** | Enterprise module — evidence · risk · approval · audit |
| **Capability Passport** | OS-style capability modes (Guardian L2) |
| **Guardian** | Defense-in-Depth north star ([docs/GUARDIAN.md](./docs/GUARDIAN.md)) |

> **NARNA is the Decision Layer for Enterprise AI.**  
> Developers: **Govern Once. Run Anywhere.** · Guardian: *who may exist · who may act · who is stopped.*

**Not another “agent passport” clone.** Not another enterprise chatbot. Not a claim of absolute civilizational safety — see honest scope in [`docs/GUARDIAN.md`](./docs/GUARDIAN.md).  
Product: [`docs/DECISION-OS.md`](./docs/DECISION-OS.md) · Differentiation: [`docs/DIFFERENTIATION.md`](./docs/DIFFERENTIATION.md).

## Install

```bash
pip install narna
```

```python
from narna import wrap

# Enforce before host side-effects (default). Use mode="observe" to migrate.
agent = wrap(my_langgraph_app, vap=True, mode="enforce")
agent.run("quarterly summary")
```

From source (dev):

```bash
pip install -e .
```

## 30 seconds — package + runtime

```python
from narna import Agent, ConstitutionRuntime

rt = ConstitutionRuntime()
rt.load(provider="eu-ai-act")  # Governance Package

agent = Agent(vap=True)
agent.run()
```

## Why teams integrate NARNA

1. **Compliance packages** — load once, enforce across frameworks  
2. **Enforce-before adapters** — deny tool/LLM calls before side effects  
3. **UGS Passport + Registry** — public verify at [narna.org](https://narna.org)  
4. **Cloud GU** — Runtime free; Trust (Registry / Passport / Packages) is the product  
5. **Decision OS** — every consequential decision ships with risk score, reasons, approvals, evidence, audit  

```bash
narna decision evaluate --action contract.sign --question "Should we sign?"
```

## Links

| | |
|--|--|
| Site | https://narna.org |
| API | https://api.narna.org/v1/health |
| **Decision OS** | [`docs/DECISION-OS.md`](./docs/DECISION-OS.md) |
| **Guardian (north star)** | [`docs/GUARDIAN.md`](./docs/GUARDIAN.md) |
| **Ship log (daily)** | [`docs/SHIP-LOG.md`](./docs/SHIP-LOG.md) |
| **7-day launch** | [`docs/launch/`](./docs/launch/) |
| MVP status | [`docs/MVP-CHECKLIST.md`](./docs/MVP-CHECKLIST.md) |
| Adapter e2e | [`docs/ADAPTERS-E2E.md`](./docs/ADAPTERS-E2E.md) |
| UGS v0.1 | [`specs/RELEASE-v0.1.md`](./specs/RELEASE-v0.1.md) |
| Decision Package | [`specs/decision-package/SPEC.md`](./specs/decision-package/SPEC.md) |
| Strategy | [`docs/STRATEGY.md`](./docs/STRATEGY.md) |
| Business | [`docs/BUSINESS-MODEL.md`](./docs/BUSINESS-MODEL.md) |
| Differentiation | [`docs/DIFFERENTIATION.md`](./docs/DIFFERENTIATION.md) |
| NGS RFCs | [`rfcs/ngs/`](./rfcs/ngs/) |
| Install | [`docs/INSTALL.md`](./docs/INSTALL.md) |

## Compatibility

OpenAI · Anthropic · Google · MCP · OpenTelemetry · LangGraph · CrewAI · Docker · Kubernetes

## License

MIT
