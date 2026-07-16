# NARNA Strategy Lock — Infrastructure Layer

**Status:** Locked  
**Date:** 2026-07-16  
**Owner:** Product / Spec

NARNA is positioned like **Docker, Kubernetes, Git, or OpenTelemetry**: an **infrastructure layer**, not an AI application or startup product pitch.

Implementation follows the specs, not the other way around.

---

## North star

> **Every Agentic AI system gets Identity, Governance, and Trust.**

> **NARNA governs AI. Others execute it.**

Passport, NARNA Score, Registry, and Governance Packages are **consequences** of these three pillars — not separate product concepts.

**Category:** Governance Infrastructure for **Agentic AI** — first users are teams building multi-agent, long-running, tool-calling workflows.

---

## Vision

Build the universal governance layer that enables every agentic system to operate safely, transparently, and across any AI stack.

---

## Mission

Standardize how Agentic AI is identified, governed, verified, and trusted.

Not by replacing LangGraph, CrewAI, OpenAI SDK, or OpenTelemetry — by making them interoperable through portable governance.

---

## One-liners

| Use | Text |
|-----|------|
| **Primary slogan** | Govern Once. Run Anywhere. |
| **Product line** | The Governance Infrastructure for Agentic AI. |
| **Alt product line** | The Universal Governance Layer for Agentic AI. |
| **Hero** | Build Agentic AI that Enterprises Can Trust. |
| **Enterprise** | Trust Every Agentic Decision. |
| **Technical** | Identity. Governance. Evidence. Trust. |
| **Community** | Open Governance for the Agentic AI Era. |
| **Contrast** | OpenTelemetry records what AI did. NARNA proves what AI was allowed to do. |

---

## Law

> **Do not compete on layers Big Tech wants to own.**

| Company / layer | Owns |
|-----------------|------|
| OpenAI | Intelligence |
| Anthropic | Safety models |
| NVIDIA | Compute |
| LangGraph | Agent orchestration |
| CrewAI | Multi-agent crews |
| Docker | Containers |
| Kubernetes | Orchestration |
| OpenTelemetry | Observability |
| MCP | Tool protocol |
| **NARNA** | **Agentic AI Governance** |

---

## What NARNA is

```text
NARNA  = Brand + Governance Runtime (reference implementation)
UGS    = Universal Governance Specification (open standard)
VAP    = Verify → Audit → Prove (trust engine within UGS)
```

NARNA is the **Governance Infrastructure for Agentic AI**.

It provides a portable governance layer across every AI model, agent framework, runtime, and cloud — starting with multi-agent workflows that need identity, policy, and trust.

**Not** a model. **Not** LangGraph/CrewAI. **Not** an agent executor.  
**Is** infrastructure: Identity, Governance, Policy, Permission, Evidence, Trust, Certification, **Agent Passport**, **Governance Package Marketplace**.

---

## The AI stack (locked)

```text
                    Agentic AI
        LangGraph · CrewAI · AutoGen · OpenAI SDK
────────────────────────────────────────────
              ★ NARNA Runtime ★
     Identity · Governance · Agent Passport
     Evidence · Trust · Certification · Packages
────────────────────────────────────────────
     OpenTelemetry · MCP · OpenShell
────────────────────────────────────────────
     Docker · Kubernetes · Linux · Cloud
```

NARNA sits **between** frameworks/protocols and the OS/cloud — governing entities that run above, not replacing them.

---

## Architecture (Governance Runtime)

```text
              Governance Packages
     Enterprise · Government · Healthcare · Banking · Robotics
────────────────────────────────────────────
                 NARNA Runtime
     Load · Validate · Enforce · Audit · Verify · Certify
────────────────────────────────────────────
 OpenAI · Claude · Gemini · MCP · LangGraph
 CrewAI · OpenTelemetry · Docker · OpenShell
```

---

## Open specification: UGS

**UGS** = **Universal Governance Specification**

Defines: Identity, Capability, Permission, Policy, Governance Package, Evidence, Trust, Certification.

**NARNA Runtime** is the reference implementation of UGS.

> **Renamed from UAP.** *Understand → Act → Prove* described a workflow. UGS names the **governance standard**. Legacy docs/code may still say `uap` (Python package path, old filenames); public brand is **UGS**.

**VAP** remains the trust engine: Verify → Audit → Prove.

---

## Core philosophy

AI should not only be intelligent. It should be:

- Identifiable  
- Governable  
- Auditable  
- Portable  
- Trustworthy  

---

## Core principles

1. **Universal** — every AI stack; no vendor lock-in  
2. **Portable** — write governance once; run everywhere  
3. **Compatible** — integrate OTel, MCP, OpenAI, Anthropic, NVIDIA; never replace  
4. **Verifiable** — every autonomous decision can be verified  
5. **Open** — open specification, open SDK, community-driven  

---

## What NARNA does / does not

| Does | Does not |
|------|----------|
| Identity — who AI is | Train models |
| Policy — what AI may do | Build LLMs |
| Evidence — what AI did | Replace agent frameworks |
| Governance — org rules | Replace OpenTelemetry |
| Trust — confidence from evidence | Replace MCP |
| Certification — prove compliance | Replace Docker / K8s |

---

## Artifact of record

Governance Packages (`constitution.yaml` and peers). Write once. Run anywhere.

Normative: [`../specs/`](../specs/) · Brand: [`BRAND.md`](./BRAND.md) · Positioning: [`POSITIONING.md`](./POSITIONING.md)

---

## Success metric

> **1M autonomous entities bound to a NARNA / UGS Governance Package or Passport.**

Not “1M app users.”

---

## Change control

Amendments require an explicit strategy note + spec version bump.  
Growth: [`BORROW-THE-WAVE.md`](./BORROW-THE-WAVE.md).
