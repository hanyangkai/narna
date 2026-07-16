# NARNA Strategy Lock — Universal AI Governance Runtime

**Status:** Locked  
**Date:** 2026-07-16  
**Owner:** Product / Spec

This document freezes positioning. Implementation follows the specs, not the other way around.

---

## North star (one sentence)

> **OpenTelemetry records what AI did. NARNA loads, enforces, and proves the governance that decides what AI may do.**

---

## Law

> **Do not compete on layers Big Tech wants to own.**

| They own / will own | We do **not** fight there |
|---------------------|---------------------------|
| Models | GPT · Claude · Gemini · Llama |
| Agent / model execution runtimes | OpenAI Agents · LangGraph · CrewAI · AutoGen |
| Tool protocols | MCP · OpenShell |
| Telemetry | OpenTelemetry |
| Cloud compute | Their clouds |

| We own | Why they under-invest |
|--------|------------------------|
| **Governance Runtime** (Load → Execute → Verify → Audit → Version → Switch) | Not a model differentiator |
| **Governance Packages** (Constitution, Compliance, OrgPolicy, Risk, HumanApproval) | Each org invents siloed PDFs |
| **Identity** (universal, portable) | Vendor lock-in prefers siloed IDs |
| **Evidence → Trust** | Compliance is “someone else’s problem” until enterprise |
| **Passport & Certification** | Cross-vendor trust dilutes walled gardens |
| **Constitution Marketplace** | Network effects for lawyers / banks / governments |

---

## What NARNA is

```text
NARNA = Universal AI Governance Runtime
        Constitution Runtime + Governance Packages
        Identity + Trust + Passport + Certification
```

**Not** an agent/model execution runtime.  
**Not** a model.  
**Not** a replacement for OpenTelemetry / MCP / LangGraph.

**Is** the runtime that **loads, executes, verifies, audits, versions, and switches** Governance Packages on top of any host AI stack.

**Slogan (canonical):**

> The Governance Runtime for Autonomous AI.

**Alt (charter surface):**

> The Constitution Layer for Autonomous AI.

**Alt (enterprise):**

> Identity, Governance and Trust for Autonomous Systems.

**Moat phrase:**

> Portable Governance — switch OpenAI → Claude → Gemini; constitution, trust, and evidence remain.

---

## Architecture (locked)

```text
                 NARNA
     Universal AI Governance Runtime
────────────────────────────────────
 Identity · Passport · Trust · Certification
────────────────────────────────────
        Constitution Runtime
   Load · Execute · Verify · Audit · Version · Switch
────────────────────────────────────
        Governance Packages
 Constitution · Compliance · OrgPolicy · RiskProfile · HumanApproval
────────────────────────────────────
 OpenTelemetry · MCP · OpenAI SDK
 LangGraph · CrewAI · OpenShell · …
────────────────────────────────────
 GPT · Claude · Gemini · Llama · …
```

NARNA sits **above** frameworks. Compatibility first. Never replace them.

---

## Protocol stack (names)

| Name | Role |
|------|------|
| **NARNA** | Brand / Universal AI Governance Runtime |
| **Constitution Runtime** | Core loop: Load → Execute → Verify → Audit → Version → Switch |
| **Governance Package** | Distributable unit (Constitution is one kind) |
| **UAP** | Protocol: Understand → Act → Prove |
| **VAP** | Trust engine: Verify → Audit → Prove |
| **Constitution** | Normative charter artifact: `constitution.yaml` (a Governance Package kind) |

---

## Ten USPs (priority order)

1. **Universal AI Governance Runtime** — load / enforce / prove governance on any host.
2. **Constitution Runtime** — portable Load → Execute → Verify → Audit → Version → Switch.
3. **Governance Packages** — Constitution, Compliance (EU AI Act, HIPAA…), OrgPolicy, Risk, HumanApproval.
4. **Constitution-as-Code** — `constitution.yaml` / package YAML, community RFCs.
5. **Constitution Marketplace** — Anthropic / banks / WHO / EU publish; NARNA loads.
6. **Portable Governance** — vendor switch does not reset charter, trust, or evidence.
7. **Constitution Compatibility** — `supports:` multi-constitution + badge.
8. **Universal AI Identity + Passport** — portable birth + public trust view.
9. **Evidence Package + Certification** — proof, not eloquence; L1 / L2 / Enterprise Ready.
10. **Compatibility First** — integrate OTel, MCP, OpenAI, Anthropic, Google, Docker, K8s.

**Moat:** Portable Governance — same package hash across OpenAI → Claude → Gemini.

---

## Artifact of record

Every autonomous system **SHOULD** ship or bind:

```text
constitution.yaml   # or a Governance Package ref (provider@version)
```

Normative: [`../specs/constitution/SPEC.md`](../specs/constitution/SPEC.md),  
[`../specs/governance-package/SPEC.md`](../specs/governance-package/SPEC.md),  
[`../specs/constitution-runtime/SPEC.md`](../specs/constitution-runtime/SPEC.md).

---

## What we demote

| Demote | Keep as |
|--------|---------|
| “NARNA Runtime” as **agent executor** USP | Optional **reference** UAP executor only |
| Competing with agent frameworks | Thin `narna.wrap()` adapters |
| “Runtime for AI Agents” slogan | **Governance Runtime** slogan |
| Building another OTel | Consume / annotate OTel; own Evidence + Trust |

Clarification: **Governance Runtime is the USP.** “Not a runtime” means **not an agent/model execution runtime**.

Existing SDK (`Agent()`, VAP, Registry, Certification) remains a **reference implementation and virus entry**. Specs + Constitution Runtime semantics are the strategic center.

---

## Spec → product order (locked)

```text
1. Constitution Spec + schemas              ← done
2. Universal Identity Spec                  ← done
3. Passport cites constitution              ← done
4. Certification levels                     ← done
5. Evidence + Trust (VAP)                   ← keep
6. Governance Package + Constitution Runtime ← now
7. Package Marketplace + Compatibility      ← with (6)
8. Fleet wired into Execute                 ← with (6)
9. Cloud / Enterprise                       ← after spec gravity
```

Cloud is an **upsell of governance + certification**, not the core.

---

## Success metric

Not “1M users.”

> **1M autonomous entities bound to a NARNA Governance Package / Passport.**

---

## Non-goals (explicit)

- Replacing LangGraph / CrewAI / OpenAI Agents SDK
- Owning model inference
- Being “the” agent execution runtime
- Forcing vendors off their SDKs
- Claiming official endorsement of EU / Anthropic / bank packages unless they publish via RFC / Marketplace

---

## Change control

Amendments to this lock require an explicit strategy note + spec version bump.  
Growth tactics: [`BORROW-THE-WAVE.md`](./BORROW-THE-WAVE.md).  
Code follows [`../specs/`](../specs/).
