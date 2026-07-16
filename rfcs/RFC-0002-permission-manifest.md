# RFC-0002: Permission Manifest

- **Status:** Accepted / Implemented (v0)  
- **Authors:** NARNA maintainers  
- **Created:** 2026-07-17  
- **Normative:** [`../specs/manifest/SPEC.md`](../specs/manifest/SPEC.md) · [`../specs/constitution/SPEC.md`](../specs/constitution/SPEC.md)

---

## Summary

Define how **permissions** are declared in `narna.yaml` and compiled into Constitution `spec.permission.grants` — the portable "what may this agent do?" contract.

---

## Motivation

Agentic AI systems call tools across browsers, wallets, databases, and email. Without a portable permission manifest, each framework re-invents allow/deny/ask semantics.

---

## Detailed design

### Short form (`narna.yaml`)

```yaml
permissions:
  - name: browser.read
    mode: allow
  - name: wallet.transfer
    mode: deny
  - name: filesystem.delete
    mode: ask
```

Shorthand string entries **MAY** imply `mode: allow`.

### Compiled form (`constitution.yaml`)

```yaml
spec:
  permission:
    grants:
      - name: browser.read
        mode: allow
```

### Runtime

`PolicyEngine` + Constitution Runtime **MUST** evaluate grants before tool execution. Deny wins.

---

## Compatibility impact

**Never Replace check:** Pass. Permissions extend host frameworks; NARNA does not replace MCP tool lists or OpenAI tool schemas.

---

## Alternatives

1. Framework-native permissions only (rejected — not portable).  
2. RBAC-only without manifest (rejected — poor DX).

---

## Implementation

`src/uap/manifest.py` compiler, `src/uap/policy.py`, Constitution Runtime `execute()`.
