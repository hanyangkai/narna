# NARNA / UAP Specification Set

**NARNA** — *The Governance Runtime for Autonomous AI.*  
**UAP** — *Understand · Act · Prove*  
**VAP** — *Verify · Audit · Prove*

**Strategy lock:** [`../docs/STRATEGY.md`](../docs/STRATEGY.md)  
**Brand:** [`../docs/BRAND.md`](../docs/BRAND.md)

**Status:** Draft v0.2  
**Scope of this repo:** normative specs + JSON Schemas (executable contracts)

---

## What this is

NARNA / UAP is **not** an IDE, agent framework, or model wrapper.

It is the **Universal AI Governance Runtime**:

| Layer | Name | Role |
|-------|------|------|
| Runtime | Constitution Runtime | Load · Execute · Verify · Audit · Version · Switch |
| Package | Governance Package | Constitution · Compliance · OrgPolicy · Risk · HumanApproval |
| Charter | Constitution | Who / may / must — `constitution.yaml` (a package kind) |
| Protocol | UAP | Understand → Act → Prove |
| Trust | VAP | Verify → Audit → Prove |
| Impl | `narna` SDK (reference) | Virus entry + adapters — not competing with host SDKs |

Design axiom:

```text
Package → Runtime (Load/Execute) → Evidence → Trust → Certification
```

Not:

```text
Model → Prompt → Tool
```

---

## Spec documents

| Spec | Path | Normative contents |
|------|------|--------------------|
| **Governance Package** | [`governance-package/SPEC.md`](governance-package/SPEC.md) | Distributable governance unit + kinds |
| **Constitution Runtime** | [`constitution-runtime/SPEC.md`](constitution-runtime/SPEC.md) | Load → Execute → Verify → Audit → Version → Switch |
| **Constitution** | [`constitution/SPEC.md`](constitution/SPEC.md) | `constitution.yaml` — Universal Identity, Capability, Permission, Policy, Evidence, Trust |
| **Universal Identity** | [`identity/SPEC.md`](identity/SPEC.md) | Portable birth record for every AI entity kind |
| **Manifest** | [`manifest/SPEC.md`](manifest/SPEC.md) | `narna.yaml` short-form → Constitution |
| **Compatibility** | [`compatibility/SPEC.md`](compatibility/SPEC.md) | Badge program incl. Constitution Compatible |
| **Governance (Fleet)** | [`governance/SPEC.md`](governance/SPEC.md) | Fleet governance (`fleet.yaml`) |
| **Certification** | [`certification/SPEC.md`](certification/SPEC.md) | L1 / L2 / Enterprise Ready levels |
| **UAP-Core** | [`uap-core/SPEC.md`](uap-core/SPEC.md) | AgentSpec, Identity, Passport, Capability, Permission, Policy, Event model |
| **UAP-Execution** | [`uap-execution/SPEC.md`](uap-execution/SPEC.md) | Run lifecycle (reference / adapter surface) |
| **UAP-Evidence** | [`uap-evidence/SPEC.md`](uap-evidence/SPEC.md) | Evidence object, hashing, provenance |
| **VAP** | [`vap/SPEC.md`](vap/SPEC.md) | Verify / Audit / Prove, ProofBundle, Trust Score |
| **Architecture** | [`ARCHITECTURE.md`](ARCHITECTURE.md) | Stack orientation (Governance Runtime above frameworks) |

---

## Canonical schemas

Machine-readable contracts live in [`schemas/`](schemas/):

| Schema | Object |
|--------|--------|
| `governance-package.schema.json` | Governance Package envelope |
| `constitution.schema.json` | NARNA Constitution charter |
| `universal-identity.schema.json` | Universal AI Identity |
| `agent-spec.schema.json` | Declarative agent definition |
| `identity.schema.json` | Cryptographic identity |
| `passport.schema.json` | Materialized trust view |
| `event.schema.json` | Append-only event |
| `tool.schema.json` | Tool boundary contract |
| `evidence.schema.json` | Verifiable evidence |
| `policy-decision.schema.json` | Allow/deny (+ reasons) |
| `proof-bundle.schema.json` | Portable proof artifact |
| `trust-score.schema.json` | Rule-based trust output |

Examples: [`examples/`](examples/) (includes `constitution.yaml`, `packages/`).

---

## Conformance language

Specs use RFC 2119 keywords:

- **MUST** / **MUST NOT** — required for conformance
- **SHOULD** / **SHOULD NOT** — strongly recommended
- **MAY** — optional

A system is **Constitution-Runtime-conformant** if it implements Load → Execute → Verify → Audit → Version → Switch.  
A system is **Governance-Package-conformant** if it loads/validates package schemas.  
A system is **Constitution-conformant** if it implements the Constitution Spec.  
A runtime/adapter is **UAP-conformant** if it implements UAP-Core + relevant Evidence bindings.  
A system is **VAP-conformant** if it additionally implements the VAP Spec.

---

## Versioning

- Spec set version: see [`VERSION`](VERSION)
- Schema `$id` URIs include major.minor
- Breaking changes bump **major**; additive clarifications bump **minor**

---

## Roadmap (spec-first)

| Milestone | Focus |
|-----------|--------|
| **C0** | Constitution Spec + schema + example | done |
| **C1** | Universal Identity across entity kinds | done |
| **C2** | Passport cites constitution hash | done |
| **C3** | Certification levels vs Constitution | done |
| **C4** | Governance / fleet | done (spec); runtime wire continuous |
| **C5** | Compatibility adapters | continuous |
| **G1** | Governance Package + Constitution Runtime | **now** |
| **G2** | Package Marketplace + Constitution Compatible | **now** |

---

## Design principles

1. **Spec before code** — product follows `specs/`.
2. **Deny by default** — no permission, no side effect.
3. **Constitution over prompt** — prompts instruct; constitutions govern.
4. **Evidence over eloquence** — claims without evidence lower trust.
5. **Rule-first trust** — Trust Score v0 is deterministic.
6. **Compatibility first** — never replace OTel / MCP / agent SDKs.
7. **Portable Governance** — vendor switch must not alone reset identity/trust.
8. **Packages over monoliths** — Constitution is one Governance Package kind; community RFCs own extensions.
