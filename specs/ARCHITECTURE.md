# Architecture (normative orientation)

**Status:** Draft — aligned with strategy lock **Constitution Layer**  
**Audience:** Spec authors and implementers  
**Strategy:** [`../docs/STRATEGY.md`](../docs/STRATEGY.md)

---

## Stack (locked)

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

NARNA does **not** replace the middle or bottom bands. It governs entities that run there.

---

## Control plane vs data plane

| Plane | Owns | Examples |
|-------|------|----------|
| **Constitution (NARNA)** | Who / may / must / trust | `constitution.yaml`, Passport, Certification |
| **Execution (others)** | How tokens/tools run | LangGraph, OpenAI Agents, CrewAI, MCP |
| **Observability (others)** | What happened (spans/logs) | OpenTelemetry |
| **Proof (NARNA VAP)** | Whether it can be believed | Evidence Package, ProofBundle, Trust Score |

---

## Artifact flow

```text
constitution.yaml
        ↓
Identity + Capability + Permission + Policy
        ↓
(side effect via any runtime / tool / MCP)
        ↓
Evidence Package  →  VAP (Verify → Audit → Prove)
        ↓
Passport  →  Certification  →  Registry / Governance
```

Portable Trust: changing model vendor **MUST NOT** alone invalidate identity or reset trust without charter change.

---

## Source of truth

| Artifact | Authoritative? | Notes |
|----------|----------------|-------|
| Constitution | **Yes** (charter) | Versioned; signature optional |
| Event / execution log | **Yes** (what ran) | May live in host runtime or OTel + NARNA evidence |
| Evidence metadata + hashes | **Yes** | Blobs optional via URI |
| Identity | **Yes** (immutable until rotation) | Universal AI Identity |
| Passport | **No** | Materialized public view |
| TrustScore | **Derived** | Rule + evidence (VAP) |
| Model prompts / CoT | **Not required for proof** | |

---

## Package boundaries

| Package | Owns |
|---------|------|
| Specs (`specs/`) | Contracts only — **source of product truth** |
| `narna` / `uap` SDK | Load Constitution, Identity, Passport, certify; thin wrap adapters |
| Reference executor | Optional local loop for demos — **not** the USP |
| `vap` / VAP modules | Verify, Audit, ProofBundle, TrustScore |
| Cloud | Registry, Certification stamp, Governance fleet — optional |

Company brand is **NARNA**. Protocols remain **UAP** / **VAP**. Charter artifact is **Constitution**.

---

## Conformance layers

1. **Constitution-conformant** — load/validate `constitution.yaml`; enforce permission/policy; evidence requirements  
2. **UAP-Core-conformant** — AgentSpec / Identity / Events / Permissions  
3. **VAP-conformant** — ProofBundle + TrustScore + offline verify  
4. **Certified** — NARNA Certification levels against Constitution + Evidence  

Aim reference code at (1) then (3); treat host frameworks as (execution) adapters.
