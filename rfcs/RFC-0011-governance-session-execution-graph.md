# RFC-0011: Governance Session, Execution Graph, and Governance Units

- **Status:** Accepted (v0)
- **Authors:** NARNA maintainers
- **Created:** 2026-07-17
- **Normative specs:** `governance-session`, `execution-graph`, `execution-unit`, `governor`, `metering`

---

## Summary

Introduce **Governance Session** and **Execution Graph** so NARNA meters **Governance Units (GU)** from **Execution Units (EU)** — not logical agent count.

**Logical Agent** = identity (Passport, Constitution, Policy).  
**Execution Unit** = metered action (tool, sub-agent, LLM step, MCP call, workflow node).

---

## Problem

Pricing by agent count is cheat-prone:

```text
1 Logical Agent → spawn 1000 workers → still "1 agent"
```

Pricing by raw events alone is opaque to developers. Pricing must reflect **governance surface area** of an execution tree.

---

## Decision

1. Every governed invocation opens a **Governance Session** (`session_*`).
2. Session contains an **Execution Graph** (parent/child nodes).
3. Each observable step mints an **Execution Unit** (`eu_*`) — default **1 GU**.
4. **Governor** enforces budgets, loop detection, recursion risk, and terminate.
5. Cloud bills on **GU/month**, not agent seats.

---

## Model

```text
Logical Agent (Sales Manager)     ← 1 Identity
└── Governance Session (session_123)
    ├── EU #1 Planner        (1 GU)
    ├── EU #2 Browser        (1 GU)
    ├── EU #3 Search         (1 GU)
    └── EU #4 Report         (1 GU)
```

Spawn tree inflates GU honestly — cannot collapse to "1 agent."

---

## Pricing (locked)

| Plan | GU / month |
|------|------------|
| Developer (local) | Unlimited local metering |
| Cloud Pro | 100,000 GU |
| Cloud Team | 500,000 GU |
| Enterprise | Custom / unlimited |

Legacy `events/mo` limits remain during migration; new limits are GU-primary.

---

## Implementation

| Layer | Path |
|-------|------|
| Specs | `specs/governance-session/`, `execution-graph/`, `execution-unit/`, `governor/`, `metering/` |
| Runtime | `src/uap/session.py`, `execution_graph.py`, `execution_unit.py`, `governor.py`, `metering.py` |
| Events | Extended `event.schema.json` with `sessionId`, `executionUnitId` |
| Cloud | `web/backend/app/billing.py` — `gu_limit` per plan |

---

## Non-goals (v0)

- Cross-region session replication
- ML-based risk scoring (rule-based recursion/loop only)
- Marketplace GU revenue share (separate from metering)
