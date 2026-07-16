# RFC-0009: Constitution Compatibility

- **Status:** Draft  
- **Authors:** NARNA maintainers  
- **Created:** 2026-07-16  
- **Normative:** [`../specs/compatibility/SPEC.md`](../specs/compatibility/SPEC.md)  
- **Strategy:** [`../docs/STRATEGY.md`](../docs/STRATEGY.md)

---

## Summary

Add **Constitution Compatible** to the Compatibility Program and a `supports:` list for multi-constitution / multi-package readiness (OCI Compatible analog).

```yaml
supports:
  - anthropic-v2
  - eu-ai-act-v1
  - medical-v3
  - enterprise-v5
```

An agent **MAY** declare ability to run under multiple Governance Packages; Certification **SHOULD** validate that listed supports resolve to loadable packages.

---

## Motivation

Enterprises need a public signal that an agent (or tool) can operate under named constitutions / compliance packs — not only “NARNA Certified”.

---

## Detailed design

### Badge

| Code | Title | Meaning |
|------|-------|---------|
| `constitution-compatible` | Constitution Compatible | Ships valid package binding + `supports:` (or active Constitution) loadable by Constitution Runtime |

### Declaration sites

- Constitution `spec.compatibility.supports[]`  
- Governance Package `metadata.labels` / `spec.supports`  
- Manifest `compatibility.supports`

### Certification check

When `supports` is non-empty, certify **SHOULD** attempt Load for each id (local cache or registry). Missing package → warning at L1, fail at L3 if marked required.

---

## Compatibility impact

**Never Replace check:** Pass. Additive badge; does not replace host runtimes.

---

## Alternatives

1. Only existing UAP Compatible / Certified badges.  
2. Marketing-only badge without Load verification.  

---

## Unresolved questions

- Semver ranges in `supports:` (`eu-ai-act@^1`)? v0: exact ids.  

---

## Implementation plan

1. Extend Compatibility SPEC + SVG badge  
2. Schema fields  
3. Certify check + portable governance test (OpenAI wrap → Anthropic wrap, same package hash)
