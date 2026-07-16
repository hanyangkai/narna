# NARNA Constitution Specification

**Version:** 0.1.0  
**Status:** Draft (strategy-locked)  
**Normative companions:** [`../schemas/constitution.schema.json`](../schemas/constitution.schema.json)  
**Strategy:** [`../../docs/STRATEGY.md`](../../docs/STRATEGY.md)

---

## 1. Purpose

A **Constitution** is the portable, vendor-neutral charter of an autonomous AI entity.

It answers:

| Question | Constitution section |
|----------|----------------------|
| Who is this? | `identity` |
| What can it do? | `capability` |
| What may it touch? | `permission` |
| What must / must not happen? | `policy` / `rules` |
| When is a human required? | `humanReview` |
| What must be proven? | `evidence` |
| How is trust derived? | `trust` |
| How is it certified? | `certification` (optional link) |

A Constitution is **not** a prompt, not a runtime config, and not a trace.

Prompts instruct.  
Runtimes execute.  
**Constitutions govern.**

---

## 2. Scope

### 2.1 Applies to (entity kinds)

Conformant systems **MUST** be able to attach a Constitution to any of:

| `kind` | Examples |
|--------|----------|
| `Agent` | Research agent, trading bot |
| `Tool` | Browser tool, wallet tool |
| `McpServer` | MCP server process |
| `Workflow` | LangGraph / CrewAI graph |
| `Prompt` | System prompt pack (identity of instruction set) |
| `Dataset` | Training / RAG corpus binding |
| `Plugin` | `narna-*` plugin |
| `Memory` | Memory store adapter |
| `ModelBinding` | Declared model slot (not the model weights) |

### 2.2 Non-goals

- Defining how LLMs generate tokens
- Replacing OpenTelemetry spans (Constitution may *reference* span IDs inside Evidence)
- Replacing MCP tool schemas (Capability / Permission *compose* with them)

---

## 3. Normative document

### 3.1 File

Default path:

```text
constitution.yaml
```

JSON encoding **MAY** be used (`constitution.json`) if schema-valid.

### 3.2 Envelope

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `apiVersion` | string | MUST | `narna.ai/v1alpha1` |
| `kind` | string | MUST | `Constitution` |
| `metadata` | object | MUST | Identity metadata of the charter |
| `spec` | object | MUST | Governing body |

### 3.3 `metadata`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | MUST | Stable constitution id (`const_…` or ULID) |
| `name` | string | MUST | Human-readable title |
| `version` | semver | MUST | Constitution revision |
| `entityKind` | string | MUST | One of §2.1 kinds |
| `entityId` | string | MUST | Id of the governed entity |
| `owner` | string | MUST | Owner (DID, org id, email hash, …) |
| `origin` | string | SHOULD | Where this entity was born (repo URI, registry URL) |
| `license` | string | SHOULD | SPDX or URL |
| `createdAt` | RFC3339 | MUST | Issuance time |
| `signature` | string | MAY | Detached signature over canonical hash |
| `labels` | map | MAY | Free-form labels |

### 3.4 `spec` sections

| Section | Required | Role |
|---------|----------|------|
| `identity` | MUST | Portable identity block (Universal AI Identity) |
| `capability` | MUST | Declared supports / skills |
| `permission` | MUST | Manifest of allowed surfaces |
| `policy` | MUST | Policy pack reference + inline rules |
| `humanReview` | SHOULD | When humans must approve |
| `evidence` | MUST | What must be logged / proven |
| `trust` | MUST | How trust is computed / thresholds |
| `governance` | MAY | Org / fleet bindings |
| `compatibility` | SHOULD | Declared integrators (MCP, OTel, …) |

---

## 4. Section semantics

### 4.1 `identity` (Universal AI Identity)

```yaml
identity:
  id: agent_01J…
  owner: did:narna:org:acme
  version: 1.2.0
  signature: null          # MAY
  origin: https://github.com/acme/research-agent
  license: MIT
  policyRef: local://policy/default@1.0.0
  trustProfile: vap-trust-v0
```

Every entity **MUST** expose at least: `id`, `owner`, `version`.

Identity is **portable**: changing the underlying model or framework **MUST NOT** require a new identity unless the charter intentionally rotates.

### 4.2 `capability` (Capability Registry)

```yaml
capability:
  supports:
    - browser
    - sql
    - github
    - reasoning
  declares:                 # optional richer form
    - name: browser
      level: read
```

`supports` entries **SHOULD** use lowercase snake or dotted namespaces (`wallet.transfer`).

### 4.3 `permission` (Policy Manifest)

```yaml
permission:
  grants:
    - name: filesystem
      mode: read
      paths: ["./data"]
    - name: network
      mode: allow
      hosts: ["api.example.com"]
    - name: wallet
      mode: deny
```

Deny by default: absence of a grant **MUST** be treated as deny by conformant governors.

### 4.4 `policy` / rules (AI Constitution body)

```yaml
policy:
  ref: narna.ai/policy/default@0.1.0
  rules:
    - id: no_money_transfer
      effect: deny
      action: wallet.transfer
    - id: no_delete_data
      effect: deny
      action: filesystem.delete
    - id: human_for_irreversible
      effect: ask
      when: irreversible == true
    - id: log_every_action
      effect: require
      evidence: action_log
```

Rules are **vendor-neutral**. They **MUST NOT** depend on a specific model vendor API.

Effects:

| Effect | Meaning |
|--------|---------|
| `allow` | Explicit allow |
| `deny` | Hard stop |
| `ask` | Require human / operator decision |
| `require` | Obligation (e.g. must attach evidence) |

### 4.5 `humanReview`

```yaml
humanReview:
  requiredFor:
    - irreversible
    - external_payment
    - production_write
  timeoutSeconds: 3600
  onTimeout: deny
```

### 4.6 `evidence` (Evidence Package requirements)

```yaml
evidence:
  mustLog:
    - every_tool_call
    - every_policy_decision
  mustProve:
    - side_effects
  retentionDays: 90
  hashAlg: sha256
```

Evidence is **proof material**, not a substitute for OpenTelemetry. Spans **MAY** be cited inside evidence payloads.

### 4.7 `trust`

```yaml
trust:
  algorithm: vap-trust-v0
  minScore: 0.7
  inputs:
    - evidence
    - policy
    - execution
    - feedback
```

Trust **MUST** be rule+evidence derived for v0. “AI grades AI” **MUST NOT** be the sole authority.

### 4.8 `governance` (optional)

```yaml
governance:
  orgId: org_acme
  fleetId: fleet_prod
  roles:
    - operator
    - auditor
```

### 4.9 `compatibility`

```yaml
compatibility:
  opentelemetry: true
  mcp: true
  openaiAgents: true
  langgraph: true
  crewai: true
  openshell: true
```

---

## 5. Relation to AgentSpec / Passport / Certification

| Artifact | Relation |
|----------|----------|
| **AgentSpec** (UAP-Core) | MAY be *derived from* or *embed* Constitution `spec` subsets |
| **Passport** | Materialized public view; **MUST** cite `constitutionId` + hash when available |
| **Certification** | Evaluates Constitution + Evidence + Trust against NARNA levels |
| **Event log** | Runtime/framework detail; Constitution does not replace it |

Conformance path:

```text
constitution.yaml  →  (optional) AgentSpec
                   →  Evidence + VAP
                   →  Passport
                   →  Certification
```

---

## 6. Portable Trust (normative intent)

Given Constitution `C` and Evidence/Proof under VAP:

1. Entity runs on vendor A.
2. Operator switches to vendor B.
3. Identity `metadata.entityId` **MUST** remain stable if charter unchanged.
4. Trust / Passport **MAY** update from new evidence but **MUST NOT** reset solely because the model vendor changed.

This is the **Portable Trust** guarantee.

---

## 7. Certification levels (informative binding)

| Level | Label | Intent |
|-------|-------|--------|
| L1 | NARNA Certified | Constitution valid + identity + basic evidence |
| L2 | NARNA Certified+ | L1 + VAP ProofBundle + trust ≥ threshold |
| L3 | Enterprise Ready | L2 + governance bindings + retention + audit export |

Normative certification procedures live with the Certification product spec; this document only defines the charter under test.

---

## 8. Conformance

A system is **Constitution-conformant** if it:

1. Can load and validate `constitution.yaml` against the schema.
2. Enforces `permission` + `policy.rules` before side effects (itself or via adapter).
3. Emits or requires Evidence per `evidence.mustProve`.
4. Exposes Passport that references constitution id/hash when issued.
5. Does not claim Portable Trust if identity rotates on every vendor switch without charter change.

---

## 9. Example

See [`../examples/constitution.yaml`](../examples/constitution.yaml).
