# UAP Specification Set

**UAP** — *Understand · Act · Prove*  
The open protocol for autonomous agents.

**Brand / company:** [NARNA](../docs/BRAND.md) — Neural Autonomous Runtime Architecture  
**Trust engine:** VAP — Verify · Audit · Prove

**Status:** Draft v0.1  
**Scope of this repo:** normative specs + JSON Schemas (executable contracts)

---

## What this is

UAP is **not** an IDE, agent framework, or model wrapper.

UAP is:

| Layer | Name | Role |
|-------|------|------|
| Spec | UAP Specification | Interop contract for agents |
| Trust | VAP Specification | Verify → Audit → Prove |
| Impl (later) | `uap-sdk` / `uap-runtime` / `vap-engine` | Reference implementations |

Design axiom:

```text
Identity → Policy → Action → Evidence → Trust
```

Not:

```text
Model → Prompt → Tool
```

---

## Spec documents

| Spec | Path | Normative contents |
|------|------|--------------------|
| **UAP-Core** | [`uap-core/SPEC.md`](uap-core/SPEC.md) | AgentSpec, Identity, Passport, Capability, Permission, Policy, Event model |
| **UAP-Execution** | [`uap-execution/SPEC.md`](uap-execution/SPEC.md) | Run lifecycle, tool contract, permission gating, memory/tool adapters |
| **UAP-Evidence** | [`uap-evidence/SPEC.md`](uap-evidence/SPEC.md) | Evidence object, hashing, provenance, retention |
| **VAP** | [`vap/SPEC.md`](vap/SPEC.md) | Verify / Audit / Prove, ProofBundle, Trust Score |

---

## Canonical schemas

Machine-readable contracts live in [`schemas/`](schemas/):

| Schema | Object |
|--------|--------|
| `agent-spec.schema.json` | Declarative agent definition |
| `identity.schema.json` | Cryptographic identity |
| `passport.schema.json` | Materialized trust view |
| `event.schema.json` | Append-only event |
| `tool.schema.json` | Tool boundary contract |
| `evidence.schema.json` | Verifiable evidence |
| `policy-decision.schema.json` | Allow/deny (+ reasons) |
| `proof-bundle.schema.json` | Portable proof artifact |
| `trust-score.schema.json` | Rule-based trust output |

Examples: [`examples/`](examples/).

---

## Conformance language

Specs use RFC 2119 keywords:

- **MUST** / **MUST NOT** — required for conformance
- **SHOULD** / **SHOULD NOT** — strongly recommended
- **MAY** — optional

A runtime is **UAP-conformant** if it implements UAP-Core + UAP-Execution + UAP-Evidence.  
A runtime is **VAP-conformant** if it additionally implements the VAP Spec.

---

## Versioning

- Spec set version: see [`VERSION`](VERSION)
- Schema `$id` URIs include major.minor
- Breaking changes bump **major**; additive clarifications bump **minor**

---

## Roadmap (product, not branding)

| Milestone | Focus |
|-----------|--------|
| **V0** | Specs + schemas (this) → thin SDK surface |
| **V1** | Passport |
| **V2** | Audit |
| **V3** | Trust score |
| **V4** | Marketplace |
| **V5** | Registry |
| **V6** | Multi-agent |

---

## Design principles

1. **Deny by default** — no permission, no execution.
2. **Events are the source of truth** — Passport is a view.
3. **No prompt/CoT required for proof** — only events + evidence.
4. **Evidence over eloquence** — claims without evidence lower trust.
5. **Rule-first trust** — Trust Score v0 is deterministic; ML may optimize later.
6. **LLM-agnostic** — any model behind the runtime boundary.
