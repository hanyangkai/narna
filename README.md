# NARNA

**Governance Infrastructure for Agentic AI**

> **Govern Once. Run Anywhere.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Website](https://img.shields.io/badge/narna.org-live-0a7ea4)](https://narna.org)
[![Spec](https://img.shields.io/badge/UGS-open%20standard-111)](./specs/README.md)

NARNA makes Agentic AI **governable** — portable identity, policy, evidence, and trust across LangGraph, CrewAI, OpenAI, Anthropic, MCP, and OTel.

It does **not** replace those runtimes. It does **not** train models. It sits in the infrastructure layer and **enforces / audits / proves** what fleets may do.

| Name | Role |
|------|------|
| **NARNA** | Brand + reference runtime |
| **UGS** | Universal Governance Specification (open standard) |
| **VAP** | Verify · Audit · Prove |
| **GU** | Governance Unit (Cloud metering) |
| **Governance Package** | Portable compliance rules (EU AI Act, HIPAA, GDPR…) |

> **NARNA governs AI. Others execute it.**

**Not another “agent passport” clone.** See [`docs/DIFFERENTIATION.md`](./docs/DIFFERENTIATION.md) — wedge = **UGS + Packages + GU**, not identity-only protocols.

## Install

```bash
pip install -e .   # or: pip install narna  (when published)
```

```python
from narna import wrap

# Enforce before host side-effects (default). Use mode="observe" to migrate.
agent = wrap(my_langgraph_app, vap=True, mode="enforce")
agent.run("quarterly summary")
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

## Links

| | |
|--|--|
| Site | https://narna.org |
| API | https://api.narna.org/v1/health |
| **Ship log (daily)** | [`docs/SHIP-LOG.md`](./docs/SHIP-LOG.md) |
| MVP status | [`docs/MVP-CHECKLIST.md`](./docs/MVP-CHECKLIST.md) |
| Strategy | [`docs/STRATEGY.md`](./docs/STRATEGY.md) |
| Business | [`docs/BUSINESS-MODEL.md`](./docs/BUSINESS-MODEL.md) |
| Differentiation | [`docs/DIFFERENTIATION.md`](./docs/DIFFERENTIATION.md) |
| NGS RFCs | [`rfcs/ngs/`](./rfcs/ngs/) |
| Install | [`docs/INSTALL.md`](./docs/INSTALL.md) |

## Compatibility

OpenAI · Anthropic · Google · MCP · OpenTelemetry · LangGraph · CrewAI · Docker · Kubernetes

## License

MIT
