# RFC-0007: Governance Package

- **Status:** Draft  
- **Authors:** NARNA maintainers  
- **Created:** 2026-07-16  
- **Normative:** [`../specs/governance-package/SPEC.md`](../specs/governance-package/SPEC.md)  
- **Strategy:** [`../docs/STRATEGY.md`](../docs/STRATEGY.md)

---

## Summary

Introduce **Governance Package** as the distributable unit of portable governance.  
A **Constitution** is one package kind. Other kinds: Compliance, OrgPolicy, RiskProfile, HumanApproval.

Providers (Anthropic-style stubs, banks, EU AI Act packs, medical orgs) publish packages; NARNA **loads** them via the Constitution Runtime.

---

## Motivation

Constitutions today are local YAML files. Enterprises need:

- Provider + version binding (`provider: eu-ai-act`, `version: 1.2.0`)
- Marketplace discovery (lawyers / banks / governments publish)
- Composition without locking NARNA to a single charter schema forever

NARNA must not invent every rule — community RFCs + packages own domain content.

---

## Detailed design

### Envelope

```yaml
apiVersion: narna.ai/v1alpha1
kind: GovernancePackage
metadata:
  id: pkg_eu_ai_act_v1
  name: EU AI Act (stub)
  version: "1.0.0"
  provider: eu-ai-act
  packageKind: Compliance
  license: MIT
  disclaimer: "Community stub — not an official EU publication."
spec:
  principles: []
  permissions: {}
  constraints: []
  humanReview: {}
  riskLevel: high
  evidence: {}
  rules: []
```

### Package kinds

| packageKind | Role |
|-------------|------|
| `Constitution` | Full charter (may embed or wrap `constitution.yaml` body) |
| `Compliance` | Regulatory pack (EU AI Act, HIPAA, PCI DSS…) |
| `OrgPolicy` | Internal org rules |
| `RiskProfile` | Risk level defaults |
| `HumanApproval` | Human review gates |

### Marketplace listing

Packages **MAY** be published to Registry (`/v1/packages`). Listing **MUST** include `provider`, `version`, `packageKind`, `disclaimer` when unofficial.

### Binding

Agents bind via Manifest / Constitution Runtime:

```yaml
constitution:
  provider: eu-ai-act
  version: "1.0.0"
# or
constitution:
  ref: registry://narna/packages/eu-ai-act@1.0.0
```

---

## Compatibility impact

**Never Replace check:** Pass. Does not replace host agent runtimes or model vendors. Packages are metadata + enforceable rules consumed by Constitution Runtime **above** hosts.

---

## Alternatives

1. Only `constitution.yaml` forever (no marketplace / provider).  
2. Embed all compliance in prompts (not portable, not verifiable).  

---

## Unresolved questions

- Multi-package bind (compose Compliance + OrgPolicy) — order of deny wins?  
- Signature / notarization of official government packages?  

---

## Implementation plan

1. Spec + JSON Schema  
2. Seed stub packages (disclaimer required)  
3. Registry + CLI publish/pull  
4. Constitution Runtime Load from provider@version
