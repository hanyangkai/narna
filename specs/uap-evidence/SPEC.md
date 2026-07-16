# UAP-Evidence Specification

**Version:** 0.1.0  
**Status:** Draft  
**Depends on:** UAP-Core 0.1.0  
**Normative companions:** [`../schemas/evidence.schema.json`](../schemas/evidence.schema.json)

---

## 1. Purpose

UAP-Evidence defines how agents **attach verifiable evidence** to actions so that claims can be audited without relying on prompts or chain-of-thought.

Evidence is the substrate of trust:

```text
Action → Evidence → Verification → Result → Trust
```

---

## 2. Principles

1. **Evidence is first-class** — not an afterthought log line.
2. **Separable** — metadata + content hash can live without large blobs.
3. **Independently verifiable** — a third party SHOULD be able to re-check claims using declared verifiers.
4. **No CoT required** — proof MUST NOT depend on hidden reasoning traces.
5. **Light storage** — prefer hash + metadata + URI over full transcript dumps.

---

## 3. Evidence object

### 3.1 Required fields

| Field | Description |
|-------|-------------|
| `evidenceId` | Unique id |
| `type` | Evidence type (see §4) |
| `source` | Provenance of capture (provider, endpoint, tool) |
| `capturedAt` | RFC3339 capture time |
| `contentHash` | SHA-256 of content bytes |
| `contentUri` | Optional locator (file://, s3://, ipfs://, https://…) |
| `provenance` | agentId, runId, toolName, permission, parentEventId |
| `verifiers` | List of verifier ids / rule packs that can check this evidence |

### 3.2 Optional fields

| Field | Description |
|-------|-------------|
| `expiresAt` | Soft expiry for time-sensitive facts |
| `mediaType` | MIME type of content |
| `sizeBytes` | Content size |
| `signature` | Optional signature over evidence envelope |
| `relatedEvidenceIds` | Cross-links (e.g. multi-source price quotes) |
| `redaction` | Whether content is redacted; hash still required |

### 3.3 Normative rules

1. Evidence **MUST** validate against `evidence.schema.json`.
2. `contentHash` **MUST** be hex-encoded SHA-256 of the canonical content bytes.
3. If `contentUri` is present, fetching content **MUST** match `contentHash` for verification to succeed.
4. Evidence **MUST** link to a parent event via `provenance.parentEventId` (typically `ActionExecuted` or `ToolCallExecuted`).

---

## 4. Evidence types (v0 registry)

| Type | Typical use | Minimum source fields |
|------|-------------|------------------------|
| `api_response` | Price quote, HTTP JSON | `provider`, `endpoint`, `requestFingerprint`, `statusCode` |
| `http_headers` | Cache/validator support | endpoint + selected headers |
| `receipt` | Transfer/tx receipt | tx id / provider receipt id |
| `screenshot` | UI/browser proof | viewport hash + url |
| `file_artifact` | Generated file | path/uri + hash |
| `signature` | Cryptographic attestation | alg + public key id |
| `attestation` | TEE / remote attestation | quote + verifier |
| `multi_source` | Aggregated corroboration | child evidence ids |
| `manual` | Human attestation | attester identity |

Implementations **MAY** define extension types under `x.<vendor>.*`.  
Conformance tests for Core Evidence **MUST** cover at least `api_response` and `receipt`.

---

## 5. Example (informative)

Agent claims: **BTC = 120,000 USD**.

Acceptable evidence set:

```json
{
  "type": "multi_source",
  "relatedEvidenceIds": ["ev_coinbase", "ev_binance"],
  "capturedAt": "2026-07-16T06:00:00Z"
}
```

Each child:

```json
{
  "type": "api_response",
  "source": {
    "provider": "coinbase",
    "endpoint": "GET /v2/prices/BTC-USD/spot",
    "requestFingerprint": "sha256:..."
  },
  "contentHash": "sha256:...",
  "capturedAt": "2026-07-16T06:00:00Z"
}
```

Without evidence (or with failed verification), Trust **MUST** decrease per VAP rules.

---

## 6. Evidence Policy (per tool / action class)

Tools declare an **Evidence Policy**:

| Field | Description |
|-------|-------------|
| `requiredTypes` | Evidence types that MUST be present |
| `minSources` | Minimum distinct providers (for multi_source) |
| `maxAgeSeconds` | Freshness bound |
| `onMissing` | `fail` \| `degrade` (default `fail` for external/irreversible) |

### Normative defaults

| Tool sideEffect | Default onMissing |
|-----------------|-------------------|
| `none` | `degrade` |
| `local` | `degrade` |
| `external` | `fail` |
| `irreversible` | `fail` |

---

## 7. Hashing & canonicalization

1. Hash algorithm for v0: **SHA-256** (`sha256:<hex>`).
2. For JSON content, hash **raw HTTP body bytes** when available; otherwise hash **canonical JSON**.
3. Canonical JSON rules (when used):
   - UTF-8
   - Objects: keys sorted lexicographically
   - No insignificant whitespace
   - Numbers: as produced by the source if preserving raw body; else shortest accurate decimal form documented by implementation

Implementations **MUST** document which mode was used in `source.canonicalization`.

---

## 8. Provenance requirements

`provenance` **MUST** include:

- `agentId`
- `runId`
- `toolName` (if applicable)
- `permission` (if gated)
- `parentEventId`

Optional: `policyDecisionId`, `modelArtifactHash`.

---

## 9. Storage & retention

### 9.1 What to store

| Store | Guidance |
|-------|----------|
| Evidence metadata | MUST |
| Content hash | MUST |
| Content blob | MAY (uri pointer preferred) |
| Events linking evidence | MUST |
| Prompts / CoT | MUST NOT be required |

### 9.2 Retention

1. Implementations **SHOULD** support retention policies (time-based, count-based).
2. Deleting blobs **MUST NOT** delete evidence metadata unless explicitly purged.
3. If blob is gone and hash cannot be re-fetched, verification status becomes `unavailable` (distinct from `invalid`).

---

## 10. Redaction

Evidence **MAY** be redacted for privacy (PII, secrets).

Rules:

1. Redacted evidence **MUST** set `redaction.applied = true`.
2. `contentHash` **MUST** refer to the redacted content that is actually stored/shared OR implementations **MUST** store `rawContentHash` + `redactedContentHash` separately.
3. Verification of public proofs **MUST** use the hash that matches shared content.

---

## 11. Attachment flow

Required sequence for effectful tools:

```text
ToolCallExecuted
    ↓
EvidenceAttached (one or more)
    ↓
(optional) Verified   ← VAP
```

`EvidenceAttached` event payload **MUST** include `evidenceId` and `contentHash`.

---

## 12. Conformance checklist

- [ ] Evidence schema validation
- [ ] SHA-256 content hashing
- [ ] Provenance linkage to events
- [ ] EvidencePolicy enforced for external/irreversible tools
- [ ] Storage works with metadata-only + URI
- [ ] Prompt/CoT not required for evidence validity

---

## 13. Out of scope

- Concrete verifier implementations for each exchange/API → VAP / adapters  
- Legal admissibility of evidence  
- Encrypted-at-rest key management details
