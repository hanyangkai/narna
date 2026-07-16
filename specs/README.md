# NARNA / UAP Specification Set

**NARNA** — *The Constitution Layer for Autonomous AI.*  
**UAP** — *Understand · Act · Prove*  
**VAP** — *Verify · Audit · Prove*

**Strategy lock:** [`../docs/STRATEGY.md`](../docs/STRATEGY.md)  
**Brand:** [`../docs/BRAND.md`](../docs/BRAND.md)

**Status:** Draft v0.1  
**Scope of this repo:** normative specs + JSON Schemas (executable contracts)

---

## What this is

NARNA / UAP is **not** an IDE, agent framework, or model wrapper.

It is the **AI Constitution Layer**:

| Layer | Name | Role |
|-------|------|------|
| Charter | Constitution | Who / may / must — `constitution.yaml` |
| Protocol | UAP | Understand → Act → Prove |
| Trust | VAP | Verify → Audit → Prove |
| Impl | `narna` SDK (reference) | Virus entry + adapters — not the USP |

Design axiom:

```text
Identity → Capability → Policy → Evidence → Trust → Certification
```

Not:

```text
Model → Prompt → Tool
```

---

## Spec documents

| Spec | Path | Normative contents |
|------|------|--------------------|
| **Constitution** | [`constitution/SPEC.md`](constitution/SPEC.md) | `constitution.yaml` — Universal Identity, Capability, Permission, Policy, Evidence, Trust |
| **Universal Identity** | [`identity/SPEC.md`](identity/SPEC.md) | Portable birth record for every AI entity kind |
| **Certification** | [`certification/SPEC.md`](certification/SPEC.md) | L1 / L2 / Enterprise Ready levels |
| **UAP-Core** | [`uap-core/SPEC.md`](uap-core/SPEC.md) | AgentSpec, Identity, Passport, Capability, Permission, Policy, Event model |
| **UAP-Execution** | [`uap-execution/SPEC.md`](uap-execution/SPEC.md) | Run lifecycle (reference / adapter surface) |
| **UAP-Evidence** | [`uap-evidence/SPEC.md`](uap-evidence/SPEC.md) | Evidence object, hashing, provenance |
| **VAP** | [`vap/SPEC.md`](vap/SPEC.md) | Verify / Audit / Prove, ProofBundle, Trust Score |
| **Architecture** | [`ARCHITECTURE.md`](ARCHITECTURE.md) | Stack orientation (Constitution above frameworks) |

---

## Canonical schemas

Machine-readable contracts live in [`schemas/`](schemas/):

| Schema | Object |
|--------|--------|
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

Examples: [`examples/`](examples/) (includes `constitution.yaml`).

---

## Conformance language

Specs use RFC 2119 keywords:

- **MUST** / **MUST NOT** — required for conformance
- **SHOULD** / **SHOULD NOT** — strongly recommended
- **MAY** — optional

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
| **C1** | Universal Identity across entity kinds | **now** |
| **C2** | Passport cites constitution hash | done (with C1) |
| **C3** | Certification levels vs Constitution | **now** |
| **C4** | Governance / fleet | next |
| **C5** | Compatibility adapters (MCP, OTel, LangGraph, …) | continuous |

---

## Design principles

1. **Spec before code** — product follows `specs/`.
2. **Deny by default** — no permission, no side effect.
3. **Constitution over prompt** — prompts instruct; constitutions govern.
4. **Evidence over eloquence** — claims without evidence lower trust.
5. **Rule-first trust** — Trust Score v0 is deterministic.
6. **Compatibility first** — never replace OTel / MCP / agent SDKs.
7. **Portable Trust** — vendor switch must not alone reset identity/trust.
