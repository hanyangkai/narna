# Audit Report — UGS / NGS-0010

**Status:** Normative (v0.1)  
**RFC:** [NGS-0010](../../rfcs/ngs/NGS-0010-audit-report.md)  
**Schema:** [`../schemas/audit.schema.json`](../schemas/audit.schema.json)

---

## 1. Purpose

A portable **Audit Report** answers:

| Question | Field |
|----------|-------|
| Who | `actor` (logicalAgentId / identityId) |
| When | `occurredAt` |
| Why | `reasons` + `policyRef` |
| Evidence | `evidenceIds[]` |
| Decision | `decision` (`allow` \| `deny` \| `ask`) |

Independent of vendor log formats (CloudWatch, Datadog, etc.).

---

## 2. AuditRecord (minimum)

| Field | Required |
|-------|----------|
| `auditId` | MUST |
| `sessionId` | SHOULD |
| `runId` | MUST |
| `actor` | MUST |
| `occurredAt` | MUST |
| `decision` | MUST |
| `permission` | SHOULD |
| `reasons` | MUST (≥1) |
| `policyRef` | SHOULD |
| `evidenceIds` | SHOULD |
| `eventRange` | SHOULD |
| `trustScore` | MAY |

---

## 3. Normative rules

1. AuditRecord MUST be derivable from Events + PolicyDecisions + Evidence (VAP Audit stage).  
2. Implementations MUST NOT require proprietary log schemas for offline audit export.  
3. `AuditRecorded` events SHOULD reference `auditId`.

---

## 4. Export

`GET /v1/audit/{runId}` (Governance API) returns AuditReport JSON matching this schema.
