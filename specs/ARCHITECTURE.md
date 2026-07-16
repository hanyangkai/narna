# Architecture (normative orientation)

**Status:** Draft — aligned with strategy lock **Universal AI Governance Runtime**  
**Audience:** Spec authors and implementers  
**Strategy:** [`../docs/STRATEGY.md`](../docs/STRATEGY.md)

---

## Stack (locked)

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

NARNA does **not** replace the middle (host frameworks) or bottom (models) bands.  
It **governs** entities that run there via the Constitution Runtime.

---

## Control plane vs data plane

| Plane | Owns | Examples |
|-------|------|----------|
| **Governance Runtime (NARNA)** | Load / Execute / Verify / Audit / Version / Switch packages | `governance_runtime`, active binding |
| **Governance Packages** | Who / may / must / risk / human gates | Constitution, Compliance packs |
| **Execution (others)** | How tokens/tools run | LangGraph, OpenAI Agents, CrewAI, MCP |
| **Observability (others)** | What happened (spans/logs) | OpenTelemetry |
| **Proof (NARNA VAP)** | Whether it can be believed | Evidence Package, ProofBundle, Trust Score |

---

## Artifact flow

```text
Governance Package (or constitution.yaml)
        ↓
Constitution Runtime: Load → bind active package
        ↓
Execute (authorize via package rules + fleet denies)
        ↓
(side effect via any host runtime / tool / MCP)
        ↓
Evidence Package  →  Verify / Audit (VAP)
        ↓
Version / Switch (optional) → new packageHash on next run
        ↓
Passport  →  Certification  →  Registry / Marketplace
```

**Portable Governance:** changing model vendor **MUST NOT** alone invalidate identity or reset trust without package change.

---

## Source of truth

| Artifact | Authoritative? | Notes |
|----------|----------------|-------|
| Governance Package / Constitution | **Yes** (charter) | Versioned; signature optional |
| Active binding (`.uap/runtime/active-governance.json`) | **Yes** (what is enforced now) | Includes packageId + hash |
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
| `narna` / `uap` SDK | Constitution Runtime reference; Identity; Passport; certify; wrap adapters |
| Reference UAP executor | Optional local loop for demos — **not** the agent-runtime USP |
| `vap` / VAP modules | Verify, Audit, ProofBundle, TrustScore |
| Cloud | Package Marketplace, Registry, Certification stamp — optional |

Company brand is **NARNA**. Protocols remain **UAP** / **VAP**.  
Charter artifact **Constitution** is a **Governance Package** kind.

---

## Conformance layers

1. **Governance-Package-conformant** — load/validate package schema  
2. **Constitution-Runtime-conformant** — Load → Execute → Verify → Audit → Version → Switch  
3. **Constitution-conformant** — load/validate `constitution.yaml`; enforce permission/policy; evidence  
4. **UAP-Core-conformant** — AgentSpec / Identity / Events / Permissions  
5. **VAP-conformant** — ProofBundle + TrustScore + offline verify  
6. **Certified** — NARNA Certification levels against Constitution + Evidence  

Aim reference code at (2) then (3); treat host frameworks as execution adapters.
