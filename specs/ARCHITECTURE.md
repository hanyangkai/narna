# Architecture (normative orientation)

**Status:** Draft — infrastructure-layer lock  
**Strategy:** [`../docs/STRATEGY.md`](../docs/STRATEGY.md) · **Positioning:** [`../docs/POSITIONING.md`](../docs/POSITIONING.md)

---

## Stack (locked)

```text
                    Applications
────────────────────────────────────────────
            AI Products & AI Companies
────────────────────────────────────────────
        OpenAI · Claude · Gemini · Llama
────────────────────────────────────────────
 OpenAI SDK · LangGraph · CrewAI · AutoGen
────────────────────────────────────────────
     OpenTelemetry · MCP · OpenShell
────────────────────────────────────────────
              ★ NARNA Runtime ★
     Identity · Governance · Policy
     Permission · Evidence · Trust · Certification
────────────────────────────────────────────
     Docker · Kubernetes · Linux · Cloud
```

NARNA does **not** replace frameworks or models. It is the **governance infrastructure** they attach to.

---

## Open standard vs brand

| Name | Role |
|------|------|
| **UGS** | Universal Governance Specification — open contracts |
| **NARNA** | Brand + reference runtime implementing UGS |
| **VAP** | Trust engine (Verify → Audit → Prove) |

---

## Control plane vs data plane

| Plane | Owns | Examples |
|-------|------|----------|
| **Governance Runtime (NARNA)** | Load / Validate / Enforce / Audit / Verify / Certify | `governance_runtime`, active binding |
| **Governance Packages** | Who / may / must / risk / human gates | Constitution, Compliance packs |
| **Execution (others)** | How tokens/tools run | LangGraph, OpenAI Agents, CrewAI, MCP |
| **Observability (others)** | What happened | OpenTelemetry |
| **Proof (VAP)** | Whether it can be believed | Evidence, ProofBundle, Trust Score |
| **Decision OS (Enterprise)** | Whether / why to act | Decision Package → Decision Result |

---

## Artifact flow

```text
Governance Package (+ Decision Package composition)
        ↓
NARNA Runtime: Load → Validate → bind active package
        ↓
Enforce / Decision.evaluate (authorize + risk + approvals)
        ↓
Evidence → Verify / Audit (VAP)
        ↓
Passport → Certification → Registry / Marketplace
```

**Portable Governance:** changing model vendor **MUST NOT** alone invalidate identity or reset trust without package change.  
**Decision OS:** customers install industry Decision Packages; they do not buy “an AI chatbot”.

---

## Package boundaries

| Package | Owns |
|---------|------|
| Specs (`specs/`) | UGS contracts — source of truth |
| `narna` / `uap` SDK | Reference runtime + adapters (`uap` = legacy path) |
| Cloud | Marketplace, Registry, Certification stamp — optional |

---

## Conformance layers

1. **UGS-conformant** — Identity / Package / Evidence / Trust contracts  
2. **Constitution-Runtime-conformant** — Load → Enforce → Verify → Audit → Switch  
3. **VAP-conformant** — ProofBundle + TrustScore + offline verify  
4. **Certified** — NARNA Certification levels  

Aim reference code at (2); treat host frameworks as execution adapters.
