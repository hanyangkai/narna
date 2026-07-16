# NARNA Brand

**NARNA** = Neural Autonomous **Rules** Native Architecture

> *The Governance Runtime for Autonomous AI.*

Second **N** = **Native** (protocol-native contracts) — not Network.  
**R** = **Rules** (constitution / governance) — Runtime here means **Governance Runtime**, not agent executor.

Do not let the acronym drive architecture. Architecture gives meaning to the acronym.

---

## Strategy lock

Canonical strategy: [`STRATEGY.md`](./STRATEGY.md)

North star:

> OpenTelemetry records what AI did. NARNA loads, enforces, and proves the governance that decides what AI may do.

---

## Three names

| Layer | Name | Role |
|-------|------|------|
| **Brand / company** | NARNA | Universal AI Governance Runtime |
| **Core loop** | Constitution Runtime | Load · Execute · Verify · Audit · Version · Switch |
| **Distributable unit** | Governance Package | Constitution is one kind |
| **Protocol** | UAP | Understand → Act → Prove |
| **Trust engine** | VAP | Verify → Audit → Prove |
| **Charter artifact** | Constitution | `constitution.yaml` |

---

## Positioning

- NARNA is **not** an AI model.
- NARNA is **not** an AI application.
- NARNA is **not** competing to own the agent execution runtime (LangGraph, OpenAI Agents, CrewAI, …).
- NARNA **is** the **Governance Runtime** that sits **above** those systems and runs Governance Packages.

## Elevator pitch

> NARNA is the Governance Runtime for Autonomous AI — portable Governance Packages (constitutions, compliance, org policy) that load, enforce, and prove across any model or agent framework.

## Taglines

| Use | Text |
|-----|------|
| Canonical | The Governance Runtime for Autonomous AI. |
| Charter surface | The Constitution Layer for Autonomous AI. |
| Enterprise | Identity, Governance and Trust for Autonomous Systems. |
| Contrast | OpenTelemetry records what AI did. NARNA proves what AI was allowed to do. |
| Moat | Portable Governance — switch vendors; keep the charter. |

---

## Product family (priority)

```text
NARNA Governance Runtime   ← center (USP)
NARNA Constitution Runtime ← core loop
NARNA Governance Packages  ← Constitution · Compliance · …
NARNA Constitution Marketplace
NARNA Identity
NARNA Passport
NARNA Evidence / VAP
NARNA Certification
NARNA Registry
NARNA Fleet Governance
NARNA Cloud                ← optional upsell
NARNA SDK                  ← reference client / virus entry
UAP Specification
```

**Demoted as USP:** “NARNA Runtime” as agent executor — may exist only as a thin reference UAP loop.

---

## Compatibility first

NARNA integrates with — does not replace:

OpenTelemetry · MCP · OpenAI · Anthropic · Google · LangGraph · CrewAI · OpenShell · Docker · Kubernetes

---

## SDK package

```bash
pip install narna
```

Protocol crates / modules may still use the `uap` name internally.
