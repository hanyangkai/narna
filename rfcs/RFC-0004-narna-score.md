# RFC-0004: NARNA Score

- **Status:** Accepted / Implemented (v0)  
- **Authors:** NARNA maintainers  
- **Created:** 2026-07-17  
- **Normative:** [`../specs/narna-score/SPEC.md`](../specs/narna-score/SPEC.md) · [`../specs/vap/SPEC.md`](../specs/vap/SPEC.md)

---

## Summary

Introduce **NARNA Score** — a branded 0–100 composite rating of Agentic AI governance posture across six dimensions.

---

## Motivation

Trust Score (VAP) measures a single run. Enterprises need a **portfolio-level** signal comparable across agents, vendors, and compliance regimes — like CVSS, Lighthouse, or credit scores.

---

## Detailed design

### Dimensions (v0)

| Dimension | Weight (equal v0) | Signals |
|-----------|-------------------|---------|
| Identity | 1/6 | Universal Identity issued, entities present |
| Capability | 1/6 | Manifest capabilities richness |
| Evidence | 1/6 | VAP proof bundles, run history |
| Governance | 1/6 | Active Governance Package binding |
| Compliance | 1/6 | Certification level L1/L2/L3 |
| Operational | 1/6 | Run success rate |

```text
NARNA Score = round( mean(dimensions) × 100 )
```

Algorithm id: `narna-score-v0`.

### Relationship to VAP Trust Score

- **VAP Trust Score** — per-run, 0–1, evidence/policy/execution/feedback  
- **NARNA Score** — workspace/agent portfolio, 0–100, six governance dimensions  

Passport **MAY** embed both.

---

## Compatibility impact

**Never Replace check:** Pass. Score reads NARNA artifacts; does not replace vendor safety scores.

---

## Alternatives

1. Single trust number only (rejected — not actionable for compliance buyers).  
2. ML-based score (deferred — reproducibility required for v0).

---

## Unresolved questions

- Dimension weights by industry (healthcare vs startup)  
- Public leaderboard anti-gaming  

---

## Implementation

`src/uap/narna_score.py`, `narna score` CLI, `GET /v1/score/{agentId}` API (when workspace linked).
