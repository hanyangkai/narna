# NGS-0027: DQS Network (multi-org Decision Quality priors)

- **Status:** Active v0  
- **Normative runtime:** [`../../src/uap/dqs_network.py`](../../src/uap/dqs_network.py)

## Purpose

Opt-in exchange of **anonymized action priors** (avgSuccess, count, hints) across organizations so ADQA memory quality compounds without sharing prompts or PII.

## API

- `GET /v1/dqs/status`
- `POST /v1/dqs/opt-in` `{ "enabled": true }`
- `POST /v1/dqs/export`
- `POST /v1/dqs/import` `{ digest }`

## Rules

1. Opt-in required before export/import  
2. Digest `kind` = `DqsNetworkDigest`  
3. `orgFingerprint` = sha256(org_id)[:16] — not reversible to customer name  
4. Imported priors enrich ADQA via `networkPrior` lessons — never overwrite local Outcome Learning
