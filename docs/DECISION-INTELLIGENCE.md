# Decision Intelligence OS — Memory feeds quality, not the destination

**Status:** Active  
**Date:** 2026-07-31  
**Related:** [`ADQA.md`](./ADQA.md) · [`DECISION-OS.md`](./DECISION-OS.md) · [`STRATEGY.md`](./STRATEGY.md)

---

## 1. CMEM vs NARNA (do not copy)

| | **CMEM** (memory continuity) | **NARNA** (decision intelligence) |
|--|------------------------------|-----------------------------------|
| Question | What does the agent **remember**? | How does the agent **decide correctly**? |
| Layer | Long-term / working memory | Decision Quality + Learning |
| Stores | Observations, decisions, fixes, dead ends | Verified decisions, outcomes, success, lessons |
| Role | Memory Layer | **Decision Intelligence Layer** |

CMEM (or any MCP memory) is a **complement**, not a competitor. Memory is feedstock for decision quality.

---

## 2. Stack

```text
AI Agent
   │  Perception
   │  Working Memory
   │  Long-term Memory (CMEM / MCP / DurableMemory)
   │  Planning
   │  Proposed Decision
══════════════════════════════
NARNA ADQA + Decision Memory
 Evidence · Context · Memory validation · Alignment
 Risk · Policy · Outcome prediction · DQS · Explain
══════════════════════════════
 Approved Decision → Action → Outcome
   │
 CMEM stores experience
 NARNA Decision Memory stores *quality of the decision*
   │
 Outcome Learning → future ADQA / policy hints
```

---

## 3. NARNA Cognitive Loop (5 tiers)

| Tier | Role |
|------|------|
| Perception | Receive data |
| Memory | Remember (CMEM / DurableMemory) |
| Reasoning | Plan / propose |
| Decision Guardian (ADQA) | Verify & score |
| Learning | Learn from outcomes |

This is a **cognitive architecture**, not governance-only.

---

## 4. Decision Memory (NGS-0025)

Beyond event recall — store **decision quality**:

```text
Decision #4817
Context: Customer A · Contract 2B
Reasoning: Payment terms anomaly
Action: Reject
Outcome: Fraud prevented
Confidence: 94%
Lesson: Check account changes within 48h
DQS: 91
```

Next time the agent retrieves **lessons**, not only facts.

---

## 5. Outcome Learning Engine

```text
Decision → Action → Outcome → Evaluation → Memory Update → Policy Hint → Future Decision
```

Over time: fewer repeated mistakes · better DQS priors · audited learning.

---

## 6. Product line

> **NARNA ADQA** — the cognitive layer that makes AI agents remember better *inputs*, decide better, and learn continuously.

Category: **Decision Intelligence OS**
