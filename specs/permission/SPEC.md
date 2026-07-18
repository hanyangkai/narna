# Permission Model — UGS / NGS-0003

**Status:** Normative (v0.1)  
**RFC:** [NGS-0003](../../rfcs/ngs/NGS-0003-permission.md)  
**Alias docs:** RFC-0002, UAP-Core §7, Constitution §4.3

---

## 1. Definition

A **Permission** is a fine-grained, parameter-aware right to perform an action.

Default posture: **deny**.

---

## 2. Naming

```text
<domain>.<action>           # e.g. wallet.transfer
<domain>.<resource>.<action> # e.g. gmail.messages.read
```

Pattern: `^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$`

---

## 3. PermissionGrant

| Field | Required | Description |
|-------|----------|-------------|
| `name` | MUST | Permission string |
| `mode` | MUST | `allow` \| `deny` \| `ask` |
| `constraints` | MAY | Parameter bounds |
| `scope` | MAY | `local` \| `org` \| `prod` \| … |

---

## 4. Normative rules

1. Missing grant → deny.  
2. Evaluate constraints before execution.  
3. Record PolicyDecision (NGS-0004) for every effectful call.  
4. Passport MUST NOT be sole authority for grants.

---

## 5. Core domains (informative v0)

`wallet` · `browser` · `email` · `filesystem` · `code` · `camera` · `market` · `mcp` · `memory`
