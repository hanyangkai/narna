# NARNA Brand

**NARNA** = Neural Autonomous **Rules** Native Architecture

> *The Governance Infrastructure for Agentic AI.*

**Primary:** Govern Once. Run Anywhere.

Second **N** = **Native** (protocol-native contracts).  
**R** = **Rules** / governance runtime — not agent executor.

Do not let the acronym drive architecture. Architecture gives meaning to the acronym.

---

## Category

**Governance infrastructure for Agentic AI** — peer class: Docker, Kubernetes, Git, OpenTelemetry.  
**Not** an AI app, chatbot, model company, or agent framework.

**First users:** teams building Agentic AI — multi-agent, long-running, tool-calling workflows.

---

## Strategy lock

Canonical: [`STRATEGY.md`](./STRATEGY.md) · Full copy: [`POSITIONING.md`](./POSITIONING.md)

---

## Name stack

| Layer | Name | Role |
|-------|------|------|
| **Brand / runtime** | NARNA | Governance Infrastructure for Agentic AI (reference impl) |
| **Open standard** | **UGS** | Universal Governance Specification |
| **Trust engine** | VAP | Verify → Audit → Prove |
| **Package** | Governance Package | Constitution · Compliance · OrgPolicy · … |
| **USP** | Agent Passport | Portable trust signal per agent |
| **USP** | Governance Package Marketplace | Healthcare · Finance · EU AI Act · … |
| **Charter kind** | Constitution | `constitution.yaml` |

**Legacy:** *UAP (Understand → Act → Prove)* was a workflow name. Public specification is **UGS**. Python module path `uap` remains as implementation alias until a major package rename.

---

## Positioning table

| Company | Owns |
|---------|------|
| OpenAI | Intelligence |
| Anthropic | Safety models |
| LangGraph | Agent orchestration |
| CrewAI | Multi-agent crews |
| Docker | Containers |
| Kubernetes | Orchestration |
| OpenTelemetry | Observability |
| MCP | Tool protocol |
| **NARNA** | **Agentic AI Governance** |

---

## Elevator

> NARNA is the Governance Infrastructure for Agentic AI. Portable Identity, Governance Packages, Agent Passports, and Trust across LangGraph, CrewAI, OpenAI SDK, and every model — without replacing them.

---

## Taglines

| Use | Text |
|-----|------|
| Primary | Govern Once. Run Anywhere. |
| Product | The Governance Infrastructure for Agentic AI. |
| Alt | The Universal Governance Layer for Agentic AI. |
| Hero | Build Agentic AI that Enterprises Can Trust. |
| Enterprise | Trust Every Agentic Decision. |
| Technical | Identity. Governance. Evidence. Trust. |
| Community | Open Governance for the Agentic AI Era. |
| Contrast | OpenTelemetry records what AI did. NARNA proves what AI was allowed to do. |

---

## Product family

```text
NARNA Runtime
NARNA SDK · CLI
Agent Passport
Governance Package Marketplace
NARNA Registry · Identity · Trust · Certification
NARNA Cloud · Enterprise
UGS (open specification)
```

---

## Official adapters (distribution)

```text
narna-langgraph · narna-crewai · narna-autogen
narna-openai · narna-anthropic · narna-semantic-kernel
```

Install adapter → Identity + Governance + Trust on existing Agentic AI stack.

---

## Compatibility first

✓ OpenAI · Anthropic · LangGraph · CrewAI · AutoGen · MCP · OpenTelemetry · Docker · Kubernetes · OpenShell

---

## Developer entry

```bash
pip install narna
```

```python
from narna import Agent, ConstitutionRuntime

rt = ConstitutionRuntime()
rt.load(provider="eu-ai-act", version="1.0.0")
agent = Agent()
agent.run()
```

No vendor lock-in. No runtime replacement. Works with your Agentic AI stack.
