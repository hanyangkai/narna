# NGS-0002: Capability Specification

- **Status:** Accepted (v0)  
- **Series:** NARNA Governance Standards  
- **Normative:** [`../../specs/capability/SPEC.md`](../../specs/capability/SPEC.md)  
- **Schema:** [`../../specs/schemas/capability.schema.json`](../../specs/schemas/capability.schema.json)

---

## Abstract

A **Capability** is a coarse class of ability used for discovery and high-level policy — not a grant to act.

## Examples

```text
browser | filesystem | wallet | github | terminal | email | search | trade | code
```

## Normative rules

1. Capability names MUST match `^[a-z][a-z0-9_]*$`.  
2. Declaring a capability MUST NOT imply permission.  
3. Tools SHOULD declare which capability they belong to.  
4. The v0 vocabulary is versioned in the Capability SPEC — extensions MUST use namespaced names (`vendor.cap`).

## Conformance

Implementations MUST treat capabilities as discovery metadata and evaluate **permissions** (NGS-0003) before side effects.
