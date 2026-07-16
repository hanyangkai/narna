# NARNA RFCs — Community Spec Process

**Status:** Active  
**Model:** Inspired by Kubernetes KEPs, Python PEPs, Rust RFCs

NARNA does not define the entire Governance Runtime alone.  
Significant changes go through an **RFC** so the community can comment before normative freeze.

---

## Principles

1. **Spec before code** for protocol changes.  
2. **Never Replace. Always Extend.** — RFCs must not invent competing **agent/model** runtimes. Governance Runtime RFCs are in-scope.  
3. **Compatibility first** — prefer adapters and metadata over breaking host frameworks.  
4. Anyone may propose; maintainers shepherd.

---

## Lifecycle

```text
Draft → Review → Accepted → Implemented → Final
         ↘ Rejected / Withdrawn
```

| State | Meaning |
|-------|---------|
| Draft | Author iterating |
| Review | Open for community comment (≥ 7 days recommended) |
| Accepted | Approved for implementation |
| Implemented | Landed in specs/ + reference SDK |
| Final | Stable; breaking changes need a new RFC |
| Rejected / Withdrawn | Not pursued |

---

## File layout

```text
rfcs/
  README.md          ← this file
  RFC-0001-agent-identity.md
  RFC-0002-….md
```

Numbered sequentially. Title slug after the number.

---

## Template

Every RFC **MUST** include:

1. Summary  
2. Motivation  
3. Detailed design  
4. Compatibility impact (Never Replace check)  
5. Alternatives  
6. Unresolved questions  

---

## Index

| RFC | Title | Status |
|-----|-------|--------|
| [RFC-0001](./RFC-0001-agent-identity.md) | Universal AI Identity | Accepted (C1 landed) |
| [RFC-0002](./RFC-0002-permission-manifest.md) | Permission Manifest | Accepted |
| [RFC-0003](./RFC-0003-agent-passport.md) | Agent Passport | Accepted |
| [RFC-0004](./RFC-0004-narna-score.md) | NARNA Score | Accepted (v0) |
| [RFC-0005](./RFC-0005-narna-yaml-manifest.md) | Manifest `narna.yaml` | Draft |
| [RFC-0006](./RFC-0006-adapter-catalog.md) | Adapter Catalog | Accepted (v0) |
| [RFC-0007](./RFC-0007-governance-package.md) | Governance Package | Draft (G1) |
| [RFC-0008](./RFC-0008-constitution-runtime.md) | Constitution Runtime | Draft (G1) |
| [RFC-0009](./RFC-0009-constitution-compatibility.md) | Constitution Compatibility | Draft (G2) |
| [RFC-0010](./RFC-0010-ugs-rename.md) | Rename open standard UAP → UGS | Draft |
