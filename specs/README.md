# NARNA / UGS Specification Set

**NARNA** — *The Governance Infrastructure for Agentic AI.*  
**UGS** — *Universal Governance Specification* (open standard)  
**NGS** — *NARNA Governance Standards* (numbered RFCs — IETF-style)  
**VAP** — *Verify · Audit · Prove* (trust engine)

**Primary:** Govern Once. Run Anywhere.  
**Strategy lock:** [`../docs/STRATEGY.md`](../docs/STRATEGY.md)  
**NGS index:** [`../rfcs/ngs/README.md`](../rfcs/ngs/README.md)

**Status:** Draft v0.4  
**Scope:** normative specs + JSON Schemas + OpenAPI

---

## Core six (NGS-0001…0006)

| NGS | Spec | Schema |
|-----|------|--------|
| Identity | [`identity/SPEC.md`](identity/SPEC.md) | `universal-identity.schema.json` |
| Capability | [`capability/SPEC.md`](capability/SPEC.md) | `capability.schema.json` |
| Permission | [`permission/SPEC.md`](permission/SPEC.md) | (AgentSpec / Manifest) |
| Policy | [`policy/SPEC.md`](policy/SPEC.md) | `policy-pack.schema.json`, `policy-decision.schema.json` |
| Evidence | [`uap-evidence/SPEC.md`](uap-evidence/SPEC.md) | `evidence.schema.json` |
| Trust | [`vap/SPEC.md`](vap/SPEC.md) §6 | `trust-score.schema.json` |

---

## Derived standards

| NGS | Spec |
|-----|------|
| Passport | [`passport/SPEC.md`](passport/SPEC.md) |
| Governance Package | [`governance-package/SPEC.md`](governance-package/SPEC.md) |
| Certification | [`certification/SPEC.md`](certification/SPEC.md) · `certification.schema.json` |
| Audit Report | [`audit/SPEC.md`](audit/SPEC.md) · `audit.schema.json` |
| Manifest | [`manifest/SPEC.md`](manifest/SPEC.md) |
| Registry | [`registry/SPEC.md`](registry/SPEC.md) |
| Governance API | [`governance-api/SPEC.md`](governance-api/SPEC.md) · [`openapi.yaml`](governance-api/openapi.yaml) |

---

## Runtime / metering (orthogonal)

| Spec | Path |
|------|------|
| Constitution | [`constitution/SPEC.md`](constitution/SPEC.md) |
| Constitution Runtime | [`constitution-runtime/SPEC.md`](constitution-runtime/SPEC.md) |
| Governance Session | [`governance-session/SPEC.md`](governance-session/SPEC.md) |
| Execution Graph / Unit | [`execution-graph/SPEC.md`](execution-graph/SPEC.md), [`execution-unit/SPEC.md`](execution-unit/SPEC.md) |
| Governor / Metering | [`governor/SPEC.md`](governor/SPEC.md), [`metering/SPEC.md`](metering/SPEC.md) |
| Governance Telemetry (privacy-preserving) | [`governance-telemetry/SPEC.md`](governance-telemetry/SPEC.md) · `governance-telemetry.schema.json` |
| UGS Execution / Core | [`uap-execution/SPEC.md`](uap-execution/SPEC.md), [`uap-core/SPEC.md`](uap-core/SPEC.md) |
| Export | [`uap-export/SPEC.md`](uap-export/SPEC.md) |

---

## Conformance

- **NGS-0001…0006 conformant** — implements the six core contracts + schemas.  
- **Governance-API conformant** — exposes OpenAPI paths or equivalent.  
- **VAP-conformant** — ProofBundle + offline verify + Trust Score.

Design axiom:

```text
Identity · Capability · Permission · Policy · Evidence · Trust
        ↓
Passport · Package · Certification · Manifest · Registry · API
```
