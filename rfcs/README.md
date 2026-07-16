# NARNA RFCs — Community Spec Process

**Status:** Active  
**Model:** Inspired by Kubernetes KEPs, Python PEPs, Rust RFCs

NARNA does not define the entire Constitution Layer alone.  
Significant changes go through an **RFC** so the community can comment before normative freeze.

---

## Principles

1. **Spec before code** for protocol changes.  
2. **Never Replace. Always Extend.** — RFCs must not invent competing runtimes.  
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
| RFC-0002 | Permission Manifest | Planned |
| RFC-0003 | Passport | Planned |
| RFC-0004 | Trust Score | Planned |
| RFC-0005 | Manifest `narna.yaml` | Draft (this wave) |
| RFC-0006 | Adapter Catalog | Planned |
