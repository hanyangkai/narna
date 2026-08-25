# Drop-in Global SaaS — NARNA Cloud

**Status:** Active v0.2  
**Date:** 2026-08-05  
**Goal:** CMEM-style one-link integrate → Decision Quality everywhere.

---

## Killer path (like CMEM private MCP link)

1. Create API key in Console / `POST /v1/keys`  
2. Point any MCP client at:

```text
https://api.narna.org/mcp
Authorization: Bearer uap_live_…
```

3. Tools available: `narna_adqa_check` · `narna_dmemory_query` · `narna_learning_prior` · `narna_cmem_enrich`

Discovery: `GET https://api.narna.org/mcp`  
SSE handshake: `GET https://api.narna.org/mcp/sse?api_key=uap_live_…`

Pair with [CMEM](https://cmem.ai/) for continuity memory — NARNA only scores decisions.

---

## Plans (hard metering)

| Plan | Price | ADQA soft / hard | Seats |
|------|-------|------------------|-------|
| free | $0 | 100 / 500 | 1 |
| cloud | $20/mo | 50k / unlimited | 1 |
| team | $99/seat/mo | 200k / unlimited | 3–50 |

`POST /v1/adqa/check` with Bearer meters `adqa_checks_in_period`. Free hits **402** past hard cap.

---

## Multi-tenant Decision Memory

Authenticated `/v1/dmemory/*` stores under `.uap/tenants/org_{id}/` with `tenantId` on every record.

---

## Health / SLO

- `GET /v1/health` — db + redis probes  
- `GET /v1/ready` — 503 if DB down  
- `GET /v1/metrics/slo` — accept rate, 429/402, latency  

Env: `UAP_ADQA_REQUIRE_AUTH=1` (prod default), `UAP_TENANT_ROOT=/data/tenants`, `UAP_CRYPTO_MODE=live|mock`, `UAP_BILLING_MODE=mock` (card rails removed), `UAP_REDIS_URL` for multi-replica rate limits.

DQS Network (opt-in): `POST /v1/dqs/opt-in` → export/import anonymized priors across orgs.

---

## Agent integrate (3 lines)

```python
from narna import wrap
import os
os.environ["NARNA_ADQA"] = "1"
agent = wrap(my_langgraph_app)  # enforce + optional ADQA gate
```

Cloud:

```bash
curl -X POST https://api.narna.org/v1/adqa/check \
  -H "Authorization: Bearer uap_live_…" \
  -H "Content-Type: application/json" \
  -d '{"action":"contract.sign","evidencePresent":["policy.decision"]}'
```
