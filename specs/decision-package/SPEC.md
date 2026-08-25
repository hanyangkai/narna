# Decision Package Specification

**Version:** 0.1.0  
**Status:** Draft (Enterprise module)  
**Normative companions:**  
- [`../schemas/decision-package.schema.json`](../schemas/decision-package.schema.json)  
- [`../schemas/decision-result.schema.json`](../schemas/decision-result.schema.json)  
**RFC:** [`../../rfcs/ngs/NGS-0014-decision-package.md`](../../rfcs/ngs/NGS-0014-decision-package.md)  
**Product:** [`../../docs/DECISION-OS.md`](../../docs/DECISION-OS.md)

---

## 1. Purpose

A **Decision Package** is a portable, versioned unit that turns NARNA governance into an **enterprise decision**: recommendation + risk score + reasons + required approvals + evidence requirements + audit binding.

It **composes** one or more Governance Packages and adds a **decision output contract**.

```text
Governance Packages (Compliance · Risk · HumanApproval)
                    ↓ compose
            Decision Package
                    ↓ evaluate
     Decision Result (proveable, auditable)
```

---

## 2. Envelope

| Field | Required | Description |
|-------|----------|-------------|
| `apiVersion` | MUST | `narna.ai/v1alpha1` |
| `kind` | MUST | `DecisionPackage` |
| `metadata` | MUST | id, name, version, provider |
| `spec` | MUST | composes, decision, rules / risk / humanReview / evidence |

### 2.1 `metadata`

| Field | Required | Description |
|-------|----------|-------------|
| `id` | MUST | Stable id (`pkg_…`) |
| `name` | MUST | Human title |
| `version` | MUST | Semver |
| `provider` | MUST | Publisher slug (`legal-decision`, `procurement-decision`) |
| `industry` | SHOULD | `law-firm` \| `logistics` \| `finance` \| `hr` \| `hospital` \| `crypto` \| … |
| `license` | SHOULD | SPDX |
| `disclaimer` | SHOULD | Required when not official counsel |

---

## 3. `spec` (normative)

| Section | Required | Role |
|---------|----------|------|
| `composes` | SHOULD | List of `{provider, version?}` Governance Packages to load |
| `decision` | MUST | Output contract + target actions |
| `rules` | SHOULD | Decision-local allow/deny/ask/require rules |
| `riskLevel` | MAY | Default package risk: low\|medium\|high\|critical |
| `humanReview` | MAY | `requiredFor` actions / roles |
| `evidence` | MAY | `mustProve`, `mustLog`, retention |
| `principles` | MAY | Human-readable guidance |

### 3.1 `spec.decision`

| Field | Required | Description |
|-------|----------|-------------|
| `actions` | MUST | Actions this package evaluates (`contract.sign`, …) |
| `requireRiskScore` | SHOULD | default `true` |
| `requireReasons` | SHOULD | default `true` |
| `requireEvidence` | SHOULD | default `true` |
| `requireApprovals` | SHOULD | default `true` |
| `recommendationHints` | MAY | Map effect → recommendation template |

---

## 4. Decision Result

Evaluate **MUST** return a document conforming to `decision-result.schema.json`:

| Field | Required | Description |
|-------|----------|-------------|
| `decision` | MUST | `allow` \| `deny` \| `ask` \| `require` |
| `recommendation` | SHOULD | Human-readable next step |
| `riskScore` | MUST when requireRiskScore | 0.0–1.0 |
| `riskBand` | SHOULD | low\|medium\|high\|critical |
| `reasons` | MUST when requireReasons | Triggered rules / constraints |
| `requiredApprovals` | MUST when ask/require | Roles or gates |
| `evidence` | SHOULD | Required evidence types / refs |
| `auditRef` | SHOULD | packageId, packageHash, sessionId?, evaluatedAt |
| `action` | MUST | Evaluated action |
| `question` | MAY | Original natural-language question |

Deny **wins** over allow when composed rules conflict.  
`ask` / `require` **MUST NOT** auto-execute irreversible side effects.

---

## 5. Runtime binding

```bash
narna decision evaluate --action contract.sign --question "Should we sign?"
```

```http
POST /v1/decision/evaluate
```

Loaders **MAY** bind via Manifest:

```yaml
governance:
  decisionPackage: legal-decision@1.0.0
```

---

## 6. Conformance

A system is **Decision-Package-conformant** if it:

1. Schema-validates `kind: DecisionPackage`  
2. Produces `DecisionResult` with risk + reasons when required  
3. Does not execute host side-effects on `deny` / `ask` / `require` without approval resolution
