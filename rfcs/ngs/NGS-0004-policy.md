# NGS-0004: Policy Specification

- **Status:** Accepted (v0)  
- **Series:** NARNA Governance Standards  
- **Normative:** [`../../specs/policy/SPEC.md`](../../specs/policy/SPEC.md)  
- **Schemas:** [`policy-pack.schema.json`](../../specs/schemas/policy-pack.schema.json), [`policy-decision.schema.json`](../../specs/schemas/policy-decision.schema.json)

---

## Abstract

Policy maps `(Identity, Permission request, Context)` → `PolicyDecision` (`allow` | `deny` | `ask`).

## Policy pack (minimum)

```yaml
apiVersion: narna.ai/v1alpha1
kind: PolicyPack
metadata:
  id: enterprise-v2
  version: 1.0.0
spec:
  default: deny
  rules:
    - match: { permission: "email.send" }
      decision: ask
      reasons: ["external communication"]
    - match: { permission: "wallet.transfer" }
      decision: deny
      when: { maxAmountExceeded: true }
```

## Normative rules

1. Evaluation MUST be deterministic for same inputs + policy version.  
2. `ask` MUST pause until explicit resolution.  
3. Every effectful action MUST emit a PolicyDecision event.  
4. Fleet / Governance Package denies MUST win over local allows.

## Conformance

Ship PolicyPack schema validation + Decision recording.
