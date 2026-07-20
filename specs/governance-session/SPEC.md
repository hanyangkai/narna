# Governance Session — UGS

**Status:** Normative (v0.1)  
**RFC:** [RFC-0011](../../rfcs/RFC-0011-governance-session-execution-graph.md)

---

## 1. Definition

A **Governance Session** is the top-level container for one governed invocation tree.

It binds:

- One **root Logical Agent** (`logicalAgentId`)
- One **Execution Graph**
- Session-scoped **budget**, **evidence**, and **trust** rollup

---

## 2. Identifier

`sessions` use prefix `session_` + UUID hex.

---

## 3. Lifecycle

| State | Meaning |
|-------|---------|
| `open` | Accepting execution units |
| `closed` | Completed normally |
| `terminated` | Stopped by Governor (budget, loop, recursion) |

---

## 4. Relationship to Run

- A session **MAY** span multiple `runId` values (orchestrator children).
- A run **SHOULD** reference `sessionId` on all events when session governance is enabled.

---

## 5. Storage (reference impl)

```text
.uap/sessions/{sessionId}/
  session.json
  graph.json
  units.jsonl
  budget.json
```
