# NGS-0003: Permission Model

- **Status:** Accepted  
- **Series:** NARNA Governance Standards  
- **Normative:** [`../../specs/permission/SPEC.md`](../../specs/permission/SPEC.md)  
- **Alias:** RFC-0002  
- **Related schema:** AgentSpec permissions · Manifest · PolicyDecision

---

## Abstract

Permissions are fine-grained, parameter-aware rights — Android-style. Default posture is **deny**.

## Examples

```text
wallet.transfer
browser.open
email.send
filesystem.write
code.execute
```

## Grant shape

```yaml
name: wallet.transfer
mode: allow | deny | ask
constraints:
  maxAmount: 100
scope: prod
```

## Normative rules

1. Missing permission MUST deny.  
2. Constraints MUST be evaluated before execution.  
3. Permission strings SHOULD use `<domain>.<action>`.  
4. Passport claims MUST NOT alone grant permission — Policy (NGS-0004) re-evaluates.

## Conformance

Deny-by-default + recorded PolicyDecision for every effectful action.
