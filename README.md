# NARNA

**Neural Autonomous Rules Native Architecture**

> **Govern Once. Run Anywhere.**  
> *The Governance Infrastructure for Agentic AI.*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)

NARNA is **governance infrastructure for Agentic AI** — peer category to Docker, Kubernetes, Git, and OpenTelemetry.

It does **not** replace LangGraph, CrewAI, OpenTelemetry, MCP, or model vendors. It sits with the infrastructure stack and **governs** multi-agent autonomous workflows.

| Name | Role |
|------|------|
| **NARNA** | Brand + Governance Infrastructure for Agentic AI (reference impl) |
| **UGS** | Universal Governance Specification (open standard) |
| **VAP** | Trust engine (*Verify · Audit · Prove*) |
| **Governance Package** | Portable rules (`constitution.yaml` and peers) |

> **NARNA governs AI. Others execute it.**

**Strategy:** [`docs/STRATEGY.md`](./docs/STRATEGY.md) · **Positioning:** [`docs/POSITIONING.md`](./docs/POSITIONING.md) · **Specs:** [`specs/`](./specs/)

## Spec first

```bash
docs/STRATEGY.md
docs/POSITIONING.md
specs/README.md
specs/examples/packages/
```

## 30 seconds

```bash
pip install -e .
```

```python
from narna import Agent, ConstitutionRuntime

rt = ConstitutionRuntime()
rt.load(provider="eu-ai-act", version="1.0.0")

agent = Agent()
agent.run()
```

## Compatibility first

OpenAI · Anthropic · Google · NVIDIA · MCP · OpenTelemetry · LangGraph · CrewAI · Docker · Kubernetes · OpenShell

## License

MIT
