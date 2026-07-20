# Execution Unit — UGS

**Status:** Normative (v0.1)  
**RFC:** [RFC-0011](../../rfcs/RFC-0011-governance-session-execution-graph.md)

---

## 1. Definition

An **Execution Unit (EU)** is one metered governance action inside a session.

**Logical Agent** holds identity. **Execution Unit** holds usage.

---

## 2. Identifier

`eu_` + UUID hex.

---

## 3. Required fields

| Field | Description |
|-------|-------------|
| `unitId` | EU id |
| `sessionId` | Parent session |
| `logicalAgentId` | Identity owner (Passport / Constitution) |
| `unitKind` | `agent`, `sub_agent`, `tool`, `mcp`, `llm`, `workflow_step` |
| `parentUnitId` | Parent EU or null for root |
| `guCost` | Governance units consumed (default 1) |

Optional: `runId`, `toolName`, `label`.

---

## 4. GU mapping

Default: **1 EU = 1 GU**.

Weighted costs MAY be defined in `metering` spec (e.g. `llm` = 2 GU).

---

## 5. Events

EU lifecycle emits:

- `ExecutionUnitStarted`
- `ExecutionUnitCompleted`
- `BudgetExceeded`
- `LoopDetected`
- `RecursiveRiskScored`
