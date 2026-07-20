# Governance API — UGS / NGS-0013

**Status:** Normative (v0.1)  
**RFC:** [NGS-0013](../../rfcs/ngs/NGS-0013-governance-api.md)  
**OpenAPI:** [`openapi.yaml`](./openapi.yaml)

---

## 1. Purpose

Provide an **OpenTelemetry-shaped** API surface so any Agentic framework can call governance without forking NARNA:

```text
Identity API
Trust API
Policy API
Evidence API
Passport API
Certification API
Registry API
```

Host frameworks **execute**. Governance API **identifies, decides, proves, and certifies**.

---

## 2. Signal groups

| Group | Analogy (OTel) | Endpoints (v0) |
|-------|----------------|----------------|
| Identity | Resource attributes | `GET/POST /v1/identity` |
| Trust | Metrics | `GET /v1/score/{agentId}` · TrustScore body |
| Policy | Span events | `POST /v1/policy/evaluate` |
| Evidence | Log records | `POST /v1/evidence` · attach |
| Passport | Status | `GET /v1/passport/{agentId}` · `POST /v1/passport/verify` |
| Certification | Status | `POST /v1/certification/submit` |
| Registry | Discovery | `/v1/registry/*` · `/v1/packages/*` |
| Session / GU | Trace | `/v1/sessions` · ingest with EU events |
| Audit | Export | `GET /v1/runs/{runId}` (includes audit slice) |

---

## 3. Normative rules

1. APIs MUST accept/return schemas from NGS-0001…0010 where applicable.  
2. Auth: Bearer API key for write; public read MAY be unauthenticated for Passports.  
3. Errors MUST use HTTP 4xx/5xx with machine-readable `detail`.  
4. Export ingest (`POST /v1/ingest`) remains the OTLP-like bulk path for runs.

---

## 4. Versioning

Base path `/v1`. Breaking changes require `/v2`. OpenAPI file is the machine-readable contract.
