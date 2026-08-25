# NGS-0018: Agent Reputation

- **Status:** Active (runtime v0)  
- **Product:** [`../../docs/GUARDIAN.md`](../../docs/GUARDIAN.md)  
- **Related:** NGS-0006 Trust Score  
- **Spec:** [`../../specs/agent-reputation/SPEC.md`](../../specs/agent-reputation/SPEC.md)

## Abstract

Reputation composites origin, creator, model, history, violations, audit, feedback — a credit score for agents. Low reputation tightens Capability Passport and monitoring.

## Normative intent

1. Reputation MUST be distinguishable from ephemeral Trust Score when published.  
2. Reputation MUST NOT be self-asserted without Registry attestation.  
3. Low band SHOULD auto-map to stricter Capability modes.
