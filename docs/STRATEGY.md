# NARNA Strategy Lock — AI Constitution Layer

**Status:** Locked  
**Date:** 2026-07-16  
**Owner:** Product / Spec

This document freezes positioning. Implementation follows the specs, not the other way around.

---

## North star (one sentence)

> **OpenTelemetry records what AI did. NARNA defines who AI is, what it is allowed to do, and why others can trust it.**

---

## Law

> **Do not compete on layers Big Tech wants to own.**

| They own / will own | We do **not** fight there |
|---------------------|---------------------------|
| Models | GPT · Claude · Gemini · Llama |
| Runtimes / agent SDKs | OpenAI Agents · LangGraph · CrewAI · AutoGen |
| Tool protocols | MCP · OpenShell |
| Telemetry | OpenTelemetry |
| Cloud compute | Their clouds |

| We own | Why they under-invest |
|--------|------------------------|
| **Identity** (universal, portable) | Vendor lock-in prefers siloed IDs |
| **Capability & Permission** | Each framework invents its own |
| **Policy / Constitution** | Not a model differentiator |
| **Evidence → Trust** | Compliance is “someone else’s problem” until enterprise |
| **Passport & Certification** | Cross-vendor trust dilutes walled gardens |
| **Governance (fleet)** | Starts after 100+ agents — late for them |

---

## What NARNA is

```text
NARNA = AI Constitution Layer
        Identity + Governance + Trust
```

Not a runtime. Not a model. Not a replacement for OpenTelemetry / MCP / LangGraph.

**Slogan (canonical):**

> The Constitution Layer for Autonomous AI.

**Alt (enterprise):**

> Identity, Governance and Trust for Autonomous Systems.

---

## Architecture (locked)

```text
                 NARNA
        AI Constitution Layer
────────────────────────────────────
 Identity · Capability · Permission
 Policy · Evidence · Trust
 Passport · Certification · Governance
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
| **NARNA** | Brand / company / Constitution Layer product |
| **UAP** | Protocol: Understand → Act → Prove |
| **VAP** | Trust engine: Verify → Audit → Prove |
| **Constitution** | Normative artifact: `constitution.yaml` |

---

## Ten USPs (priority order)

1. **Universal AI Identity** — every AI entity (prompt, agent, tool, MCP server, workflow, dataset, plugin, memory) has a portable identity.
2. **AI Passport** — public trust view (Apple Dev / GitHub Verified / SSL analog).
3. **Capability Registry** — declared `supports:` like `package.json`.
4. **Policy Manifest** — Android Manifest analog for permissions.
5. **AI Constitution** — `constitution.yaml` rules independent of any model vendor.
6. **Evidence Package** — proof, not mere traces.
7. **Trust Passport** — rule + evidence → trust (not “AI grades AI”).
8. **Certification** — NARNA Certified L1 / L2 / Enterprise Ready.
9. **Governance** — who may do what across hundreds of agents.
10. **Compatibility First** — integrate OTel, MCP, OpenAI, Anthropic, Google, Docker, K8s.

**Moat:** Portable Trust — switch OpenAI → Claude → Gemini; identity, policy, evidence, trust, passport remain.

---

## Artifact of record

Every autonomous system **SHOULD** ship:

```text
constitution.yaml
```

Normative definition: [`../specs/constitution/SPEC.md`](../specs/constitution/SPEC.md)

---

## What we demote

| Demote | Keep as |
|--------|---------|
| “NARNA Runtime” as product USP | Optional **reference** executor only |
| Competing with agent frameworks | Thin `narna.wrap()` adapters |
| “Runtime for AI Agents” slogan | Constitution Layer slogan |
| Building another OTel | Consume / annotate OTel; own Evidence + Trust |

Existing SDK (`Agent()`, VAP, Registry, Certification) remains a **reference implementation and virus entry** — not the strategic center.

---

## Spec → product order (locked)

```text
1. Constitution Spec + schemas     ← done
2. Universal Identity Spec         ← done (C1)
3. Passport cites constitution     ← done
4. Certification levels (C3)       ← done
5. Evidence + Trust (VAP)          ← keep
6. Governance (fleet) Spec         ← next
7. Compatibility adapters          ← continuous
8. Cloud / Enterprise              ← after spec gravity
```

Cloud is an **upsell of governance + certification**, not the core.

---

## Success metric

Not “1M users.”

> **1M autonomous entities with a NARNA Constitution / Passport.**

---

## Non-goals (explicit)

- Replacing LangGraph / CrewAI / OpenAI Agents SDK
- Owning model inference
- Being “the” agent runtime
- Forcing vendors off their SDKs

---

## Change control

Amendments to this lock require an explicit strategy note + spec version bump.  
Growth tactics: [`BORROW-THE-WAVE.md`](./BORROW-THE-WAVE.md).  
Code follows [`../specs/`](../specs/).
