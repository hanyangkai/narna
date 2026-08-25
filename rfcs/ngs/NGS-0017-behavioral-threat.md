# NGS-0017: Behavioral Threat Engine

- **Status:** Draft  
- **Product:** [`../../docs/GUARDIAN.md`](../../docs/GUARDIAN.md)

## Abstract

Threat Engine scores **action chains** (not prompts) for dangerous patterns: replication, escalation, scanning, exfiltration, mass accounts, anomalous graphs, policy evasion.

## Output (informative)

```json
{
  "riskScore": 0.97,
  "patterns": ["spawn_storm", "credential_harvest"],
  "recommendation": "restrict|kill|signature",
  "graphRef": "session_…"
}
```

## Normative intent

1. Input MUST be Execution Graph / EU events (RFC-0011), not raw prompts alone.  
2. High risk MUST be able to trigger Capability restrict or Kill Token (NGS-0019).  
3. v0 MAY be rule-based heuristics; ML is optional later.
