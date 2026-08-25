# NGS-0016: Agent Container (Sandbox)

- **Status:** Active (runtime v0 — policy contract)  
- **Product:** [`../../docs/GUARDIAN.md`](../../docs/GUARDIAN.md)  
- **Spec:** [`../../specs/agent-container/SPEC.md`](../../specs/agent-container/SPEC.md)

## Abstract

Agent Container is isolation for agent runtime: memory, network, tools, quotas — “Docker for AI.”

## Normative intent (v0)

1. New agents under Guardian profile SHOULD start with deny-by-default network.  
2. Tools available MUST be a subset of Capability Passport grants.  
3. Spawn depth MUST respect `quotas.maxSpawnDepth`.  
4. Full OS isolation is host-provided; NARNA defines the **policy contract**.
5. Kill cascade MUST set memoryFrozen · mcpDisconnected · networkIsolated on the container state.
