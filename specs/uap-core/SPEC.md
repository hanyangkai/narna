# UAP-Core Specification

**Version:** 0.1.0  
**Status:** Draft  
**Normative companions:** [`../schemas/`](../schemas/)

---

## 1. Purpose

UAP-Core defines the **shared object model** for autonomous agents:

- AgentSpec (declarative definition)
- Identity (birth certificate)
- Passport (materialized trust view)
- Capability & Permission
- Policy evaluation surface
- Event model (append-only ledger)

This document does **not** define how tools execute or how evidence is verified.
Those belong to UAP-Execution, UAP-Evidence, and VAP.

---

## 2. Philosophy

```text
Understand → Act → Prove
```

An agent that cannot **prove** what it did is not trustworthy under UAP.

Core starts from:

```text
Identity → Policy → Action → Evidence → Trust
```

---

## 3. AgentSpec

### 3.1 Definition

An **AgentSpec** is the declarative definition of an agent.  
Every conformant agent **MUST** be representable as an AgentSpec document.

### 3.2 Canonical fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `apiVersion` | string | MUST | e.g. `uap.dev/v1alpha1` |
| `kind` | string | MUST | `Agent` |
| `metadata.id` | string (ULID/UUID) | MUST | Stable agent id |
| `metadata.name` | string | MUST | Human-readable name |
| `metadata.version` | semver | MUST | Spec revision of this agent |
| `metadata.creator` | string | MUST | Creator identity (DID, email hash, org id…) |
| `metadata.createdAt` | RFC3339 | MUST | Creation timestamp |
| `spec.capability` | string[] | MUST | Declared capability classes |
| `spec.permissions` | PermissionGrant[] | MUST | Requested/declared permissions |
| `spec.tools` | ToolRef[] | SHOULD | Tools this agent may use |
| `spec.model` | ModelRef | MAY | Preferred model; runtime MAY override |
| `spec.memory` | MemoryRef | MAY | Memory adapter binding |
| `spec.policy` | PolicyRef | MUST | Policy pack / ruleset id |
| `spec.passport` | PassportRef | MAY | Link to current passport |

### 3.3 YAML shape (informative)

```yaml
apiVersion: uap.dev/v1alpha1
kind: Agent
metadata:
  id: 01JEXAMPLEAGENTID000000000
  name: Trading Agent
  version: 1.0.0
  creator: did:uap:creator:alice
  createdAt: "2026-07-16T00:00:00Z"
spec:
  capability: [search, trade]
  permissions:
    - name: market.read
      mode: allow
    - name: wallet.transfer
      mode: ask
      constraints:
        maxAmount: "100"
        currency: USDT
  tools:
    - name: binance.ticker
    - name: wallet.transfer
  model:
    provider: any
    preference: claude-opus
  memory:
    adapter: local-sqlite
  policy:
    ref: policies/trading-default@1.0.0
```

### 3.4 Normative rules

1. AgentSpec **MUST** validate against `agent-spec.schema.json`.
2. `metadata.id` **MUST NOT** change after first issuance.
3. Changing `spec.permissions`, `spec.capability`, or `spec.policy` **MUST** bump `metadata.version`.
4. Runtimes **MUST** reject AgentSpecs that fail schema validation.

---

## 4. Identity

### 4.1 Definition

**Identity** is the immutable birth record of an agent instance, analogous to a Git commit object for “who/what was born”.

### 4.2 Required fields

| Field | Description |
|-------|-------------|
| `agentId` | Same as `metadata.id` |
| `creator` | Issuer of the identity |
| `createdAt` | Issuance time |
| `version` | AgentSpec version at issuance |
| `specHash` | SHA-256 of canonical AgentSpec bytes |
| `signature` | Signature over the identity payload |

### 4.3 Normative rules

1. Identity **MUST** be signed by the creator (or issuance authority).
2. Identity **MUST NOT** be mutated; rotation creates a **new** identity linked via `supersedes`.
3. `specHash` **MUST** use canonical JSON (sorted keys, UTF-8, no insignificant whitespace) unless a documented alternative is declared.

### 4.4 Signature algorithms (v0)

Implementations **MUST** support at least one of:

- `ed25519`
- `ecdsa-p256-sha256`

The algorithm identifier **MUST** appear in `signature.alg`.

---

## 5. Passport

### 5.1 Definition

A **Passport** is a **materialized view** summarizing identity, capability, permissions, history, and trust.

Passport is **not** the source of truth.  
Events + Evidence are the source of truth. Passport **MAY** be regenerated from them.

### 5.2 Logical structure

```text
Passport
  Identity
    ↓
  Capability
    ↓
  Permission
    ↓
  History
    ↓
  Trust
```

### 5.3 Required sections

| Section | Contents |
|---------|----------|
| `identity` | Identity object (or digest + link) |
| `capability` | Declared + observed capabilities |
| `permissions` | Effective grants (after policy) |
| `history` | Aggregates: run counts, last run, violations |
| `trust` | Latest TrustScore (see VAP) + timestamp |

### 5.4 Normative rules

1. Passport **MUST** include `issuedAt` and `expiresAt` (or explicit `ttl`).
2. Passport **SHOULD** include `derivedFrom` = hash of the event-log tip used to build it.
3. Consumers **MUST** treat an expired passport as untrusted until refresh.
4. Runtimes **MUST NOT** grant permissions solely because a passport claims them; they **MUST** re-evaluate Policy.

---

## 6. Capability

### 6.1 Definition

A **Capability** is a coarse class of agent ability used for discovery, marketplace, and high-level policy.

Examples (non-exhaustive registry; v0 informal):

```text
search | browser | wallet | email | ocr | trade | code | filesystem
```

### 6.2 Normative rules

1. Capability names **MUST** be lowercase `[a-z][a-z0-9_]*`.
2. Declaring a capability **MUST NOT** imply permission to act.
3. Tools **SHOULD** declare which capability they belong to.

---

## 7. Permission

### 7.1 Definition

A **Permission** is a fine-grained, parameter-aware right to perform an action — Android-style.

Examples:

```text
wallet.transfer
browser.open
gmail.read
camera.use
market.read
filesystem.write
```

### 7.2 PermissionGrant

| Field | Description |
|-------|-------------|
| `name` | Permission string |
| `mode` | `allow` \| `deny` \| `ask` |
| `constraints` | Optional parameter bounds (amount, domains, paths…) |
| `scope` | Optional environment scope (`local`, `org`, `prod`…) |

### 7.3 Normative rules

1. Default posture **MUST** be **deny**.
2. Missing permission **MUST** block the corresponding tool/action.
3. Constraints **MUST** be evaluated before execution (see UAP-Execution).
4. Permission strings **SHOULD** use dotted namespaces: `<domain>.<action>`.

---

## 8. Policy

### 8.1 Definition

**Policy** maps `(Identity, Permission request, Context)` → `PolicyDecision`.

Policy packs are versioned artifacts referenced by AgentSpec (`spec.policy.ref`).

### 8.2 PolicyDecision (minimum)

| Field | Description |
|-------|-------------|
| `decision` | `allow` \| `deny` \| `ask` |
| `permission` | Requested permission |
| `reasons` | Human/machine readable reasons |
| `policyRef` | Which policy produced the decision |
| `evaluatedAt` | Timestamp |
| `inputHash` | Hash of normalized request inputs |

### 8.3 Normative rules

1. Every effectful action **MUST** have a PolicyDecision recorded as an event.
2. `ask` **MUST** pause execution until an explicit human/org resolution is recorded.
3. Policy evaluation **MUST** be deterministic for the same inputs + policy version.

---

## 9. Event Model

### 9.1 Principles

1. Everything meaningful **MUST** be an Event.
2. Event logs are **append-only**.
3. Events within a run **MUST** form a hash chain (`hashPrev`).
4. Events **MUST NOT** require storing prompts or chain-of-thought for validity.

### 9.2 Common event envelope

| Field | Required | Description |
|-------|----------|-------------|
| `eventId` | MUST | Unique id |
| `eventType` | MUST | Type string |
| `apiVersion` | MUST | Schema version |
| `agentId` | MUST | Agent identity |
| `runId` | MUST | Run identifier |
| `ts` | MUST | RFC3339 timestamp |
| `sequence` | MUST | Monotonic uint per run |
| `hashPrev` | MUST | SHA-256 of previous event payload (genesis: `0…0`) |
| `payload` | MUST | Type-specific body |
| `schemaRef` | SHOULD | Link to event payload schema |

### 9.3 Core event types (v0)

| Type | When |
|------|------|
| `AgentStarted` | Run begins |
| `PolicyEvaluated` | Permission/policy decision made |
| `ToolCallRequested` | Tool invocation requested |
| `ToolCallExecuted` | Tool finished (success or failure) |
| `MemoryRead` / `MemoryWrite` | Memory adapter access |
| `ModelGenerated` | Model produced output (artifact ref only) |
| `ActionExecuted` | Business-level action completed |
| `EvidenceAttached` | Evidence linked to action/event |
| `Verified` | Verification result recorded |
| `AuditRecorded` | Audit record written |
| `Completed` | Run finished successfully |
| `Failed` | Run finished with failure |

### 9.4 Normative rules

1. `sequence` **MUST** start at `0` for each run and increase by 1.
2. Tampering with any event **MUST** break the hash chain.
3. Implementations **SHOULD** expose export of the full event stream for a `runId`.

---

## 10. Storage posture (Core-level)

UAP-Core **MUST NOT** require storing:

- raw prompts
- chain-of-thought / hidden reasoning

UAP-Core **MUST** allow storing:

- event envelopes
- hashes / metadata
- evidence references
- policy decisions

(See UAP-Evidence for retention details.)

---

## 11. Conformance checklist

A Core-conformant implementation:

- [ ] Accepts/validates AgentSpec
- [ ] Issues Identity with signature + `specHash`
- [ ] Emits append-only hash-chained Events
- [ ] Enforces deny-by-default Permissions
- [ ] Records PolicyDecision for effectful actions
- [ ] Treats Passport as derived, not authoritative

---

## 12. Out of scope

- Tool sandboxing details → UAP-Execution  
- Evidence verification algorithms → UAP-Evidence / VAP  
- Trust score formula → VAP  
- Marketplace / Registry → future versions
