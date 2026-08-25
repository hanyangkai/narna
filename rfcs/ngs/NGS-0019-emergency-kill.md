# NGS-0019: Emergency Kill Architecture

- **Status:** Active (runtime v0 + cascade)  
- **Product:** [`../../docs/GUARDIAN.md`](../../docs/GUARDIAN.md)

## Abstract

Three-tier kill: Local (agent) · Domain (org/fleet) · Global (network). Kill Token revokes capability, disconnects MCP, freezes memory, isolates network.

## Flow

```text
Kill Token → Capability revoked → MCP disconnected → Memory frozen → Network isolated
```

## Normative intent

1. Local Kill MUST stop new EUs in the target Governance Session / agent.  
2. Domain Kill MUST revoke org-scoped Capability Passports.  
3. Global Kill REQUIRES Collective Defense Network (NGS-0020) and council authority.  
4. Agents MUST NOT be able to forge or ignore Kill Tokens under Guardian profile.
5. Each issue_* MUST record cascade steps on the kill entry.
