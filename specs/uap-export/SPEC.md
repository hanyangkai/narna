# UAP Export Protocol

**Version:** 0.1.0  
**Status:** Draft  
**Purpose:** OTLP-like export from OSS SDK to Cloud control plane (optional, not required for UAP conformance)

---

## 1. Principles

1. **OSS SDK MUST work without cloud** — export is optional plugin (`uap-cloud`).
2. **Payloads use UAP canonical objects** — events, evidence, ProofBundle schemas unchanged.
3. **Idempotent ingest** — same `runId` + `eventId` may be retried.
4. **API key per organization** — `Authorization: Bearer uap_live_...`

---

## 2. Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/v1/ingest` | API key | Upsert run + events + optional proof |
| `GET` | `/v1/runs` | API key | List runs for org |
| `GET` | `/v1/runs/{runId}` | API key | Run detail + events |
| `GET` | `/v1/health` | None | Health check |

---

## 3. Ingest request

```json
{
  "agentId": "01JEXAMPLETRADINGAGENT00001",
  "agentName": "Trading Agent",
  "runId": "run_abc123",
  "state": "Completed",
  "tipHash": "sha256:...",
  "events": [ /* UAP Event envelopes */ ],
  "evidence": [ /* UAP Evidence metadata */ ],
  "proofBundle": { /* optional ProofBundle */ },
  "trustScore": { /* optional TrustScore */ }
}
```

### Normative rules

1. `events` MUST preserve `sequence` order.
2. Server SHOULD dedupe by `eventId`.
3. `proofBundle` if present MUST validate against `proof-bundle.schema.json` (server-side).
4. Server MUST NOT require prompts or CoT.

---

## 4. Response

```json
{
  "ok": true,
  "runId": "run_abc123",
  "eventsIngested": 12,
  "url": "/console/runs/run_abc123"
}
```

---

## 5. SDK integration

```python
from uap_cloud import CloudExporter

exporter = CloudExporter(api_key="uap_live_xxx", base_url="https://api.example.com")
exporter.push_run(workspace_path=".", run_id="run_abc")
```

CLI:

```bash
uap push --run run_abc --cloud-url https://api.example.com --cloud-key uap_live_xxx
```

---

## 6. Security

- TLS required in production
- API keys rotatable
- No PII required in export; evidence blobs MAY be omitted (metadata + hash only)
