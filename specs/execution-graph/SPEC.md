# Execution Graph — UGS

**Status:** Normative (v0.1)  
**RFC:** [RFC-0011](../../rfcs/RFC-0011-governance-session-execution-graph.md)

---

## 1. Definition

An **Execution Graph** is a directed acyclic graph (DAG) of **nodes** within a Governance Session.

Cycles **MUST** be detected by the Governor and **MUST** trigger termination.

---

## 2. Node kinds

| `nodeKind` | Example |
|------------|---------|
| `agent` | Root logical agent run |
| `sub_agent` | Delegated child agent |
| `tool` | Tool invocation |
| `mcp` | MCP server call |
| `llm` | Model generation step |
| `workflow_step` | LangGraph / CrewAI node |

Each node maps to one **Execution Unit**.

---

## 3. Edges

Edges link `parentUnitId` → `unitId`. The graph is session-scoped.

---

## 4. Loop detection

If adding an edge would create a cycle in the agent/tool identity graph, emit `LoopDetected` and terminate session.

---

## 5. Recursion detection

If the same `unitKind` + `logicalAgentId` appears ≥ `recursionDepthLimit` (default 4) in an ancestry path, emit `RecursiveRiskScored` and terminate.
