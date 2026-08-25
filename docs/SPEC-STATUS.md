# Spec & product status — honest snapshot

**Date:** 2026-07-31  
**Architecture:** [`ARCHITECTURE.md`](./ARCHITECTURE.md)

---

## Specs complete for Decision Intelligence stack

| NGS | Title | Status |
|-----|-------|--------|
| 0001–0014 | UGS core + Decision Package | Active / Accepted |
| 0015–0020 | Guardian L2–L4 | Active v0 |
| 0021–0023 | Gateway · Citizen · Passport consumer | Active v0 |
| 0024 | ADQA | Active |
| 0025 | Decision Memory | Active |
| 0026 | Outcome Learning | Active |

OpenAPI: ADQA / dmemory / learning / gateway / citizen paths synced in [`../specs/governance-api/openapi.yaml`](../specs/governance-api/openapi.yaml).

---

## Still open (ops / network)

1. ~~DQS Network multi-org~~ → **done v0** (NGS-0027 · `/v1/dqs/*`)  
2. Live multi-VPS CTI society mesh at scale  
3. Counsel-grade jurisdiction packs  
4. ~~CMEM MCP adapter~~ → done  
5. Chrome Web Store listing  
6. ~~Hard metering~~ → done  
7. Multi-region geo LB (HA single-region ready: Redis RL + `/v1/ready`) — see [`HA.md`](./HA.md)  
8. Paying design partners / Paddle seller approval  

**Drop-in SaaS v0.2+:** MCP `/mcp`, tenant memory, require-auth, DQS Network, thick e2e examples.
