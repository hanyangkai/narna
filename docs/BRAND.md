# NARNA Brand

**NARNA** = Neural Autonomous **Rules** Native Architecture

> *The Constitution Layer for Autonomous AI.*

Second **N** = **Native** (protocol-native contracts) — not Network.  
**R** = **Rules** (constitution / governance) — not Runtime-as-product.

Do not let the acronym drive architecture. Architecture gives meaning to the acronym.

---

## Strategy lock

Canonical strategy: [`STRATEGY.md`](./STRATEGY.md)

North star:

> OpenTelemetry records what AI did. NARNA defines who AI is, what it is allowed to do, and why others can trust it.

---

## Three names

| Layer | Name | Role |
|-------|------|------|
| **Brand / company** | NARNA | AI Constitution Layer (Identity · Governance · Trust) |
| **Protocol** | UAP | Understand → Act → Prove |
| **Trust engine** | VAP | Verify → Audit → Prove |
| **Charter artifact** | Constitution | `constitution.yaml` |

---

## Positioning

- NARNA is **not** an AI model.
- NARNA is **not** an AI application.
- NARNA is **not** competing to own the agent runtime (LangGraph, OpenAI Agents, CrewAI, …).
- NARNA **is** the Constitution Layer that sits **above** those systems.

## Elevator pitch

> NARNA is the Constitution Layer for Autonomous AI — portable identity, policy, evidence, trust, passport, and certification that work across any model or agent framework.

## Taglines

| Use | Text |
|-----|------|
| Canonical | The Constitution Layer for Autonomous AI. |
| Enterprise | Identity, Governance and Trust for Autonomous Systems. |
| Contrast | OpenTelemetry records what AI did. NARNA defines who AI is, what it may do, and why you can trust it. |

---

## Product family (priority)

```text
NARNA Constitution     ← center
NARNA Identity
NARNA Passport
NARNA Policy
NARNA Evidence / VAP
NARNA Certification
NARNA Registry
NARNA Governance
NARNA Cloud            ← optional upsell
NARNA SDK              ← reference client / virus entry (not the USP)
UAP Specification
```

**Demoted as USP:** “NARNA Runtime” — may exist only as a thin reference executor.

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
