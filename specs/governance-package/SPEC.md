# Governance Package Specification

**Version:** 0.1.0  
**Status:** Draft (G1)  
**Normative companions:** [`../schemas/governance-package.schema.json`](../schemas/governance-package.schema.json)  
**RFC:** [`../../rfcs/RFC-0007-governance-package.md`](../../rfcs/RFC-0007-governance-package.md)  
**Strategy:** [`../../docs/STRATEGY.md`](../../docs/STRATEGY.md)

---

## 1. Purpose

A **Governance Package** is a portable, versioned unit of rules that the **Constitution Runtime** can Load → Execute → Verify → Audit → Version → Switch.

A **Constitution** (`kind: Constitution`) is one package kind. Other kinds cover compliance, org policy, risk, and human approval without locking NARNA to a single charter forever.

---

## 2. Envelope

| Field | Required | Description |
|-------|----------|-------------|
| `apiVersion` | MUST | `narna.ai/v1alpha1` |
| `kind` | MUST | `GovernancePackage` |
| `metadata` | MUST | id, name, version, provider, packageKind |
| `spec` | MUST | rules / constraints / evidence requirements |

### 2.1 `metadata`

| Field | Required | Description |
|-------|----------|-------------|
| `id` | MUST | Stable package id (`pkg_…`) |
| `name` | MUST | Human title |
| `version` | MUST | Semver |
| `provider` | MUST | Publisher slug (`eu-ai-act`, `anthropic`, `acme-bank`) |
| `packageKind` | MUST | See §3 |
| `license` | SHOULD | SPDX |
| `disclaimer` | SHOULD | Required when not an official publication |
| `createdAt` | SHOULD | RFC3339 |

### 2.2 `packageKind`

| Kind | Role |
|------|------|
| `Constitution` | Full or partial charter body |
| `Compliance` | Regulatory pack |
| `OrgPolicy` | Internal org rules |
| `RiskProfile` | Default risk posture |
| `HumanApproval` | Human review gates |

---

## 3. `spec` (normative)

| Section | Required | Role |
|---------|----------|------|
| `rules` | SHOULD | List of `{id, effect, action?, when?, description?}` — effects: allow/deny/ask/require |
| `permissions` | MAY | Grant map or list |
| `constraints` | MAY | Hard constraints |
| `humanReview` | MAY | `requiredFor`, timeout |
| `riskLevel` | MAY | `low` \| `medium` \| `high` \| `critical` |
| `evidence` | MAY | `mustProve`, `mustLog`, retention |
| `principles` | MAY | Human-readable principles |
| `supports` | MAY | Compatibility ids this package claims (`eu-ai-act-v1`) |
| `constitution` | MAY | Embedded Constitution `spec` or `$ref` path |

Deny **wins** over allow when composed with Constitution / Fleet.

---

## 4. Binding

Agents **MAY** bind a package via Manifest:

```yaml
constitution:
  provider: eu-ai-act
  version: "1.0.0"
# or
constitution:
  ref: registry://narna/packages/eu-ai-act@1.0.0
# or
constitution:
  path: ./packages/eu-ai-act.yaml
```

---

## 5. Marketplace

Packages **MAY** be listed in the NARNA Package Registry. Unofficial stubs **MUST** include `metadata.disclaimer`.

---

## 6. Conformance

A system is **Governance-Package-conformant** if it loads and schema-validates `kind: GovernancePackage` documents and can bind them into the Constitution Runtime.
