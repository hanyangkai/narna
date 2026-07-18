# Governor — UGS

**Status:** Normative (v0.1)  
**RFC:** [RFC-0011](../../rfcs/RFC-0011-governance-session-execution-graph.md)

---

## 1. Definition

The **Governor** is the session supervisor — analogous to an OS kernel for agentic execution.

It watches:

- Permission / Constitution decisions (delegate to Constitution Runtime)
- **Budget** (org, session, per logical agent)
- **Loop** (cycle in execution graph)
- **Recursion** (repeated unit kinds in ancestry)
- **Terminate** when limits exceeded

---

## 2. Separation of concerns

| Component | Role |
|-----------|------|
| Constitution Runtime | Policy allow/deny/ask |
| Governor | Metering + graph safety + cost guard |
| Logical Agent | Identity + Passport |

---

## 3. Termination

When Governor terminates a session:

1. State → `terminated`
2. Emit `BudgetExceeded`, `LoopDetected`, or `RecursiveRiskScored`
3. Block new EUs
4. Surface reason to operator

---

## 4. Configuration

```yaml
governor:
  recursionDepthLimit: 4
  recursionRiskThreshold: 0.85
  defaultAgentBudgetGu: 100
  monthlyOrgLimitGu: 50000
```
