# NGS-0015: Capability Passport

- **Status:** Draft  
- **Normative:** [`../../specs/capability-passport/SPEC.md`](../../specs/capability-passport/SPEC.md)  
- **Product:** [`../../docs/GUARDIAN.md`](../../docs/GUARDIAN.md)

## Abstract

Capability Passport binds agent identity to capability **modes** (allow/ask/sandbox/whitelist/restricted/multisig/deny) with quotas and isolation — OS-style privilege governance for agents.

## Normative rules

1. Capability declaration (NGS-0002) MUST NOT alone grant action.  
2. Guardian-profile adapters MUST evaluate Capability Passport before side effects.  
3. Agents MUST NOT self-escalate grant modes.  
4. `create.agent` SHOULD default to `restricted` under Guardian profile.
