# Decision Memory Specification

**Version:** 0.1.0-draft  
**Status:** Draft  
**Series:** NGS-0025  
**Product:** [`../../docs/DECISION-INTELLIGENCE.md`](../../docs/DECISION-INTELLIGENCE.md)

---

## 1. Purpose

**Decision Memory** persists verified decisions with outcomes and lessons so ADQA can improve future scores — distinct from general agent memory (observations / chat continuity).

---

## 2. Record

```json
{
  "decisionId": "dmem_…",
  "action": "contract.sign",
  "context": { "customer": "A" },
  "reasoning": ["payment terms"],
  "guardian": "reject",
  "dqs": 91,
  "outcome": { "status": "success", "detail": "fraud prevented", "successScore": 0.94 },
  "lesson": "Check account changes within 48h",
  "confidence": 0.94,
  "standard": "NGS-0025"
}
```

---

## 3. APIs

- `POST /v1/dmemory/record` — store proposed/approved decision  
- `POST /v1/dmemory/{id}/outcome` — attach outcome + lesson  
- `GET /v1/dmemory/query` — retrieve by action/context  
- `POST /v1/learning/evaluate` — Outcome Learning step  

---

## 4. Non-goals

- Replacing CMEM / MCP memory stores  
- Training foundation models on private prompts
