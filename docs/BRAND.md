# NARNA Brand

**NARNA** = Neural Autonomous **Rules** Native Architecture

> *The Governance Runtime for Autonomous Intelligence.*

**Primary:** Govern Once. Run Anywhere.

Second **N** = **Native** (protocol-native contracts).  
**R** = **Rules** / governance runtime — not agent executor.

Do not let the acronym drive architecture. Architecture gives meaning to the acronym.

---

## Category

**Infrastructure layer** — peer class: Docker, Kubernetes, Git, OpenTelemetry.  
**Not** an AI app, chatbot, or model company.

---

## Strategy lock

Canonical: [`STRATEGY.md`](./STRATEGY.md) · Full copy: [`POSITIONING.md`](./POSITIONING.md)

---

## Name stack

| Layer | Name | Role |
|-------|------|------|
| **Brand / runtime** | NARNA | Universal AI Governance Runtime (reference impl) |
| **Open standard** | **UGS** | Universal Governance Specification |
| **Trust engine** | VAP | Verify → Audit → Prove |
| **Package** | Governance Package | Constitution · Compliance · OrgPolicy · … |
| **Charter kind** | Constitution | `constitution.yaml` |

**Legacy:** *UAP (Understand → Act → Prove)* was a workflow name. Public specification is **UGS**. Python module path `uap` remains as implementation alias until a major package rename.

---

## Positioning table

| Company | Owns |
|---------|------|
| OpenAI | Intelligence |
| Anthropic | Safety models |
| NVIDIA | Compute |
| Docker | Containers |
| Kubernetes | Orchestration |
| OpenTelemetry | Observability |
| MCP | Tool protocol |
| **NARNA** | **AI Governance** |

---

## Elevator

> NARNA governs AI. Others execute it. Portable Governance Packages load, enforce, and prove across every model and agent framework — without replacing them.

---

## Taglines

| Use | Text |
|-----|------|
| Primary | Govern Once. Run Anywhere. |
| Product | The Governance Runtime for Autonomous Intelligence. |
| Alt | Universal Governance for Autonomous Intelligence. |
| Enterprise | Trust Every Autonomous Decision. |
| Technical | Identity. Governance. Evidence. Trust. |
| Community | Open Governance for the AI Era. |
| Contrast | OpenTelemetry records what AI did. NARNA proves what AI was allowed to do. |

---

## Product family

```text
NARNA Runtime
NARNA SDK
NARNA CLI
NARNA Registry
NARNA Identity
NARNA Trust
NARNA Passport
NARNA Policy
NARNA Evidence
NARNA Certification
NARNA Cloud
NARNA Enterprise
UGS (open specification)
```

---

## Compatibility first

✓ OpenAI · Anthropic · Google · NVIDIA · MCP · OpenTelemetry · LangGraph · CrewAI · AutoGen · Docker · Kubernetes · OpenShell

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

No vendor lock-in. No runtime replacement. Works with your existing stack.
