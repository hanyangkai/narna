# Agent Container — NGS-0016

- **Status:** Active (runtime v0 — policy contract)
- **RFC:** [`../../rfcs/ngs/NGS-0016-agent-container.md`](../../rfcs/ngs/NGS-0016-agent-container.md)

## Contract

| Field | Default |
|-------|---------|
| network | deny-by-default (Passport decides when allowlist empty) |
| filesystem | workspace-only |
| memory | isolated |
| quotas.maxSpawnDepth | 1 |
| quotas.maxApiCallsPerHour | 100 |

Full OS isolation is **host-provided**. NARNA enforces the policy contract + kill-cascade freeze.

## CLI / API

- `narna container install|profile|check`
- `POST /v1/guardian/container/*`
