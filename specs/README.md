# NARNA / UGS Specification Set

**NARNA** — *The Governance Runtime for Autonomous Intelligence.*  
**UGS** — *Universal Governance Specification* (open standard)  
**VAP** — *Verify · Audit · Prove* (trust engine)

**Primary:** Govern Once. Run Anywhere.  
**Strategy lock:** [`../docs/STRATEGY.md`](../docs/STRATEGY.md)  
**Positioning:** [`../docs/POSITIONING.md`](../docs/POSITIONING.md)  
**Brand:** [`../docs/BRAND.md`](../docs/BRAND.md)

**Status:** Draft v0.3  
**Scope:** normative specs + JSON Schemas (executable contracts)

---

## What this is

NARNA is an **infrastructure layer** (peer category: Docker, Kubernetes, OpenTelemetry) — not an IDE, agent framework, or model wrapper.

| Layer | Name | Role |
|-------|------|------|
| Brand / runtime | NARNA | Reference Universal AI Governance Runtime |
| Open standard | **UGS** | Universal Governance Specification |
| Runtime loop | Constitution Runtime | Load · Validate · Enforce · Audit · Verify · Certify |
| Package | Governance Package | Constitution · Compliance · OrgPolicy · Risk · HumanApproval |
| Trust | VAP | Verify → Audit → Prove |
| Impl | `narna` SDK | Reference client — Python package `uap` is a legacy path alias |

Design axiom:

```text
Governance Package → Runtime (Load/Enforce) → Evidence → Trust → Certification
```

**Legacy note:** Specs historically named *UAP (Understand → Act → Prove)*. Public standard is **UGS**. Filenames under `uap-*` remain until a major rename.

---

## Spec documents

| Spec | Path | Normative contents |
|------|------|--------------------|
| **Governance Package** | [`governance-package/SPEC.md`](governance-package/SPEC.md) | Distributable governance unit + kinds |
| **Constitution Runtime** | [`constitution-runtime/SPEC.md`](constitution-runtime/SPEC.md) | Load → Execute → Verify → Audit → Version → Switch |
| **Constitution** | [`constitution/SPEC.md`](constitution/SPEC.md) | `constitution.yaml` charter |
| **Universal Identity** | [`identity/SPEC.md`](identity/SPEC.md) | Portable birth record |
| **Manifest** | [`manifest/SPEC.md`](manifest/SPEC.md) | `narna.yaml` → Constitution |
| **Compatibility** | [`compatibility/SPEC.md`](compatibility/SPEC.md) | Badge program |
| **Governance (Fleet)** | [`governance/SPEC.md`](governance/SPEC.md) | Fleet governance |
| **Certification** | [`certification/SPEC.md`](certification/SPEC.md) | L1 / L2 / Enterprise Ready |
| **UGS Core** (legacy UAP-Core) | [`uap-core/SPEC.md`](uap-core/SPEC.md) | AgentSpec, Identity, Passport, Events |
| **UGS Execution** | [`uap-execution/SPEC.md`](uap-execution/SPEC.md) | Run lifecycle |
| **UGS Evidence** | [`uap-evidence/SPEC.md`](uap-evidence/SPEC.md) | Evidence hashing |
| **VAP** | [`vap/SPEC.md`](vap/SPEC.md) | ProofBundle, Trust Score |
| **Architecture** | [`ARCHITECTURE.md`](ARCHITECTURE.md) | Stack orientation |

---

## Conformance

A system is **UGS-conformant** if it implements the normative Identity / Package / Evidence / Trust contracts.  
A system is **Constitution-Runtime-conformant** if it implements Load → Enforce → Verify → Audit → Switch.  
**VAP-conformant** systems additionally implement ProofBundle + offline verify.

---

## Design principles

1. Spec before code  
2. Deny by default  
3. Constitution over prompt  
4. Evidence over eloquence  
5. Compatibility first — never replace host stacks  
6. Portable governance — vendor switch must not alone reset identity/trust  
7. Open standard (UGS) separate from brand (NARNA)
