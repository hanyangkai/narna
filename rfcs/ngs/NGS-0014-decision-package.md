# NGS-0014: Decision Package

- **Status:** Draft  
- **Series:** NARNA Governance Standards  
- **Normative:** [`../../specs/decision-package/SPEC.md`](../../specs/decision-package/SPEC.md)  
- **Schemas:** `decision-package.schema.json`, `decision-result.schema.json`  
- **Product:** [`../../docs/DECISION-OS.md`](../../docs/DECISION-OS.md)

---

## Abstract

Decision Package turns portable Governance Packages into an enterprise **Decision Result**: risk score, reasons, required approvals, evidence requirements, and audit binding — without replacing host executors.

## Normative rules

1. `kind` MUST be `DecisionPackage`.  
2. Evaluate MUST NOT auto-execute irreversible side effects on `deny` / `ask` / `require`.  
3. When `requireRiskScore` is true, result MUST include `riskScore` in `[0,1]`.  
4. Composed Governance Package denies MUST win over Decision Package allows.  
5. Decision Packages MAY be sold/installed via Marketplace like apps (Legal, Procurement, Finance…).

## Conformance

Schema-valid package + DecisionResult from `DecisionEngine.evaluate` / `POST /v1/decision/evaluate`.
