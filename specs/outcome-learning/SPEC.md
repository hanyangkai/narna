# Outcome Learning Specification

**Version:** 0.1.0  
**Status:** Active  
**Series:** NGS-0026  
**Depends on:** NGS-0024 ADQA · NGS-0025 Decision Memory  
**Product:** [`../../docs/DECISION-INTELLIGENCE.md`](../../docs/DECISION-INTELLIGENCE.md)

---

## 1. Purpose

Outcome Learning closes the loop:

```text
Decision → Action → Outcome → Evaluation → Memory Update → Prior/Hint → Future ADQA
```

---

## 2. Prior object

```json
{
  "action": "contract.sign",
  "n": 12,
  "avgSuccess": 0.81,
  "avgDqs": 84.2,
  "hint": "favor_approve",
  "lessons": ["Check account changes within 48h"]
}
```

`hint` ∈ `neutral` | `escalate` | `favor_approve`

---

## 3. APIs

- `POST /v1/learning/evaluate` — attach outcome, refresh prior  
- `GET /v1/learning/prior/{action}` — fetch prior for ADQA enrichment  

ADQA MUST consume `enrich_adqa_context(action)` before scoring when available.

---

## 4. Outcome prediction (v0)

v0 MAY emit a heuristic `predictedSuccess` from prior averages.  
MUST NOT claim ML model guarantees. Trained predictors are a later revision.
