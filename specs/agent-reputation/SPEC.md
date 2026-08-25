# Agent Reputation — NGS-0018

- **Status:** Active (runtime v0)
- **RFC:** [`../../rfcs/ngs/NGS-0018-agent-reputation.md`](../../rfcs/ngs/NGS-0018-agent-reputation.md)

## Composite

origin · creator · model · violations · peer feedback · Registry attestation

Distinct from ephemeral Trust Score (`distinctFromTrustScore: true`).

## Bands → Capability floor

| Band | Score | modeFloor |
|------|-------|-----------|
| critical | <25 | deny |
| low | <45 | restricted |
| medium | <70 | ask |
| high | <90 | allow |
| excellent | ≥90 | allow |

Self-asserted feedback without attestation is forbidden.
