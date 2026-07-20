# Policy Specification — UGS / NGS-0004

**Status:** Normative (v0.1)  
**RFC:** [NGS-0004](../../rfcs/ngs/NGS-0004-policy.md)  
**Schemas:** [`policy-pack.schema.json`](../schemas/policy-pack.schema.json), [`policy-decision.schema.json`](../schemas/policy-decision.schema.json)

---

## 1. Definition

**Policy** evaluates `(Identity, Permission request, Context)` → **PolicyDecision**.

A **PolicyPack** is a versioned artifact of rules (`default` + ordered `rules`).

---

## 2. PolicyDecision

See `policy-decision.schema.json`. Required: `decision`, `permission`, `reasons`, `policyRef`, `evaluatedAt`, `inputHash`.

---

## 3. PolicyPack

```yaml
apiVersion: narna.ai/v1alpha1
kind: PolicyPack
metadata:
  id: local-default
  version: 0.0.0
spec:
  default: deny
  rules:
    - id: allow-market-read
      match:
        permission: market.read
      decision: allow
      reasons: ["read-only market data"]
```

### Rule evaluation

1. First matching rule wins (unless Fleet/Package deny overrides).  
2. If no rule matches → `spec.default`.  
3. Deny from Governance Package / Fleet **MUST** override local allow.

---

## 4. Normative rules

1. Deterministic for same inputs + pack version.  
2. `ask` pauses until resolution event.  
3. Emit `PolicyEvaluated` event with Decision.  
4. `inputHash` MUST cover normalized permission + parameters.

---

## 5. Relation to Constitution

Constitution §4.4 MAY embed or reference PolicyPack ids. Manifest aliases (`strict`, `ask-all`) MUST expand to concrete packs.
