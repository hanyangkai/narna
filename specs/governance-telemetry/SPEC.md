# Privacy-Preserving Governance Telemetry

**Version:** 0.1.0  
**Status:** Draft (G1)  
**Normative schema:** [`../schemas/governance-telemetry.schema.json`](../schemas/governance-telemetry.schema.json)  
**Related:** [`../metering/SPEC.md`](../metering/SPEC.md) · [`../governance-session/SPEC.md`](../governance-session/SPEC.md) · [`../uap-export/SPEC.md`](../uap-export/SPEC.md)

---

## 1. Purpose

NARNA Cloud **MAY** accept **Governance Telemetry** — anonymized, sanitized metadata about agent governance graphs — to build **Governance Intelligence** (pattern detection, policy recommendations, benchmarks).

NARNA **MUST NOT** collect prompts, model outputs, tool arguments, customer content, or secrets as part of this telemetry channel.

```text
Local Runtime  →  Sanitizer  →  Opt-in Contribute  →  Aggregate  →  Intelligence
     │                 │                │                 │
  full audit      strip PII        consent only      k-anonymous
```

---

## 2. Principles (normative)

| # | Rule |
|---|------|
| P1 | **Local-first** — full EventLog / ProofBundle remain on the customer's machine by default. |
| P2 | **Explicit opt-in** — contribution requires org-level and/or env consent (`telemetryOptIn`). Default: **off**. |
| P3 | **Sanitize at source** — client **MUST** strip forbidden fields before transmit; server **MUST** re-sanitize. |
| P4 | **Pseudonymize** — tenant/session/agent identifiers **MUST** be hashed with a rotating salt; never store raw IDs in the contribution store. |
| P5 | **Aggregate-only publication** — public / sold reports **MUST** meet k-anonymity (`k ≥ 5` tenants default). |
| P6 | **No training without separate consent** — telemetry **MUST NOT** be used to train foundation models unless a distinct consent flag is set. |
| P7 | **Customer control** — org **MUST** be able to view contribution status, pause, and request deletion of its hashed contributions. |

---

## 3. Allowed vs forbidden fields

### 3.1 Allowed (Governance Metadata)

| Field | Description |
|-------|-------------|
| `agentClass` | Coarse class: `planner`, `browser`, `finance`, `research`, `robot`, `general`, … |
| `unitKind` | Execution Unit kind: `tool`, `llm`, `subagent`, `mcp`, `workflow` |
| `capabilityFamily` | Taxonomy bucket (e.g. `database.query`, `network.fetch`) — **not** raw tool name if identifying |
| `policyFamily` | Policy / package family id (e.g. `gdpr`, `enterprise-v2`) |
| `decision` | `allow` \| `deny` \| `ask` \| `require` |
| `humanApproval` | boolean |
| `outcome` | `success` \| `failure` \| `aborted` \| `unknown` |
| `riskBand` | `low` \| `medium` \| `high` \| `critical` |
| `failureClass` | Coarse: `policy_violation`, `permission_denied`, `timeout`, `loop`, `budget`, `other`, or null |
| `guCost` | integer ≥ 0 |
| `trustBand` | `low` \| `medium` \| `high` (from Trust Score buckets) |
| `graphShape` | Ordered list of `unitKind` / `capabilityFamily` edges (no payloads) |

### 3.2 Forbidden (MUST strip)

- Prompt / completion / message content  
- Tool arguments and results (bodies)  
- URLs, file paths, SQL text, email addresses, phone numbers  
- Raw `agentId`, `runId`, `sessionId`, customer names, org names  
- API keys, tokens, secrets  
- ProofBundle evidence blobs / raw receipts  

---

## 4. Contribution envelope

```yaml
apiVersion: narna.ai/v1alpha1
kind: GovernanceTelemetryContribution
metadata:
  schemaVersion: "0.1.0"
  contributedAt: "2026-07-17T00:00:00Z"
  consent:
    telemetryOptIn: true
    trainOptIn: false
spec:
  tenantHash: "th_…"          # HMAC(org_id, salt)
  sessionHash: "sh_…"         # HMAC(session_id, salt) or null
  nodes:
    - agentClass: finance
      unitKind: tool
      capabilityFamily: database.query
      policyFamily: financial-controls
      decision: ask
      humanApproval: true
      outcome: success
      riskBand: high
      failureClass: null
      guCost: 1
      trustBand: high
  edges:
    - from: 0
      to: 1
  totals:
    gu: 12
    nodes: 4
    humanApprovals: 1
    denies: 0
```

---

## 5. API

| Method | Path | Auth | Role |
|--------|------|------|------|
| `POST` | `/v1/telemetry/contribute` | API key + org `telemetryOptIn` | Accept sanitized contribution |
| `GET` | `/v1/telemetry/aggregate` | public or API key | k-anonymous aggregates |
| `GET` | `/v1/telemetry/consent` | API key | Read org consent |
| `POST` | `/v1/telemetry/consent` | API key | Set `telemetryOptIn` / `trainOptIn` |
| `DELETE` | `/v1/telemetry/contributions` | API key | Delete this org's hashed rows |

Ingest (`POST /v1/ingest`) remains the **private** org audit path and is independent of telemetry opt-in. Telemetry is a **separate, opt-in** channel.

---

## 6. Aggregation & k-anonymity

Public aggregates **MUST**:

1. Group by taxonomy fields only (never by `tenantHash`).  
2. Suppress buckets with fewer than `k` distinct `tenantHash` values (default `k=5`).  
3. Prefer rates and percentiles over absolute per-tenant counts in published reports.

Example aggregate row:

```json
{
  "agentClass": "finance",
  "capabilityFamily": "database.query",
  "humanApprovalRate": 0.87,
  "denyRate": 0.04,
  "loopFailureRate": 0.02,
  "tenantCount": 42,
  "sampleNodes": 12840
}
```

---

## 7. Conformance

A system is **Governance-Telemetry-conformant** if it:

1. Implements sanitizer rules §3 before contribution.  
2. Defaults consent to off and gates `/v1/telemetry/contribute`.  
3. Stores only hashed tenant/session identifiers in the contribution store.  
4. Applies k-anonymity on public aggregates.
