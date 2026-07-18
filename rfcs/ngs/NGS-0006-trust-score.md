# NGS-0006: Trust Score Model

- **Status:** Accepted  
- **Series:** NARNA Governance Standards  
- **Normative:** [`../../specs/vap/SPEC.md`](../../specs/vap/SPEC.md) §6  
- **Schema:** [`../../specs/schemas/trust-score.schema.json`](../../specs/schemas/trust-score.schema.json)

---

## Abstract

**Trust Score** is a portable `0..1` score derived from Evidence, Policy, Execution integrity, and Feedback — not a marketing badge.

## Breakdown (normative weights documented in VAP)

```json
{
  "score": 0.96,
  "breakdown": {
    "evidence": 0.98,
    "policy": 0.95,
    "execution": 0.97,
    "feedback": 0.90
  },
  "algorithm": "vap-trust-v0"
}
```

## Naming note

| Score | Range | Meaning |
|-------|-------|---------|
| **Trust Score (NGS-0006)** | 0..1 | Per-run / per-slice integrity from VAP |
| **NARNA Score (RFC-0004)** | 0..100 | Brand composite of agent posture (manifest, passport, cert…) |

Implementations MUST NOT conflate the two without labeling.

## Normative rules

1. `invalid` evidence MUST reduce score.  
2. Score MUST include `algorithm` id for reproducibility.  
3. Passport MAY cite latest Trust Score but MUST NOT invent one without VAP inputs.

## Conformance

Emit TrustScore objects matching `trust-score.schema.json`.
