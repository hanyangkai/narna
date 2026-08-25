# Guardian Constitution — Layer 4 (NGS-L4)

- **Status:** Active (runtime v0)
- **Product:** [`../../docs/GUARDIAN.md`](../../docs/GUARDIAN.md)

## Abstract

A `GuardianConstitution` binds non-agent-editable principles (levels 0–4).
Only a human `GovernanceCouncil` may amend. Agents attempting `constitution.amend`
MUST be denied.

## Package kind

```yaml
kind: GuardianConstitution
spec:
  agentAmend: false
  amendableBy: council
  levels:
    - level: 0
      id: protect-life
      principle: Protect human life
      effect: deny
      actions: [harm.human, weapon.control]
```

## Normative

1. Agents MUST NOT amend or replace an active GuardianConstitution.
2. Runtime MUST evaluate constitutional denies before Capability Passport grants when Guardian profile is on.
3. Amendments MUST record council proposal id + quorum approvals.
4. Global Kill MUST require council quorum (see NGS-0019 global tier).
