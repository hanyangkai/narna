# ADQA — Autonomous Decision Quality Assurance

**Status:** Active (product core)  
**Date:** 2026-07-31  
**Category:** Decision Quality Infrastructure for AI Agents & Autonomous Systems  
**Tagline:** The Trust Layer for AI Decisions.  
**Expand:** Autonomous Decision Quality Assurance (not only “Agent”)

**Related:** [`DECISION-OS.md`](./DECISION-OS.md) · [`STRATEGY.md`](./STRATEGY.md) · [`../specs/adqa/SPEC.md`](../specs/adqa/SPEC.md)

---

## 1. Positioning

> **NARNA is the Decision Quality Infrastructure for AI Agents.**

NARNA does **not** create the decision. NARNA **assures the quality** of the decision.

| Analog | Assures |
|--------|---------|
| GitHub / CI | Code quality |
| Stripe | Payment quality |
| Cloudflare | Access quality |
| **NARNA / ADQA** | **Decision quality** |

Scope: AI agent · AI model · robot · autonomous system · enterprise decision engine.

---

## 2. Architecture (NARNA v2)

```text
                 NARNA
     Agent / Autonomous Decision Quality Infrastructure
──────────────────────────────────────────────────────
           AI Agent / Model / System
                 │
          Proposed Decision
                 │
──────────────────────────────────────────────────────
               ADQA Core
──────────────────────────────────────────────────────
 Evidence · Policy · Context · Memory · Risk
 Alignment · Capability · Compliance · Confidence · Explanation
                 │
            Decision Quality Score (DQS)
                 │
──────────────────────────────────────────────────────
            Decision Guardian
         Approve · Revise · Escalate · Reject
                 │
──────────────────────────────────────────────────────
            Execution Layer
     MCP · Workflow · API · Human Approval · Automation
──────────────────────────────────────────────────────
         Audit + Learning + Reputation (DQS Network)
         Decision Memory (NGS-0025) · Outcome Learning
```

**Complement:** Long-term agent memory (e.g. CMEM) stores continuity; NARNA Decision Memory stores **decision quality** — see [`DECISION-INTELLIGENCE.md`](./DECISION-INTELLIGENCE.md).

---

## 3. Decision Quality Score (DQS)

Ten measurable attributes (0–100). KPI of an AI decision:

| Attribute | What it checks |
|-----------|----------------|
| Evidence | Required proofs present / valid |
| Policy | Package / rule compliance |
| Context | Knowledge / entity grounding |
| Memory | Durable scope freshness |
| Risk | Risk band vs thresholds |
| Alignment | Goals / Decision Constitution |
| Capability | Agent may attempt this action |
| Compliance | Pack / jurisdiction constraints |
| Confidence | Calibration of certainty |
| Explanation | Reasons / recommendation quality |

**DQS** = weighted mean → e.g. **89/100**.

---

## 4. Decision Constitution

Every consequential decision MUST pass:

| Principle | Question |
|-----------|----------|
| Truth | Grounded in correct data? |
| Logic | Reasoning coherent? |
| Alignment | Matches stated goals? |
| Safety | Harm bounded? |
| Authority | Agent has the right? |
| Accountability | Who is responsible? |

---

## 5. Decision Integrity Layer

NARNA protects the **formation** of the decision — not the model weights:

```text
Input → Reasoning → Evidence → Policy → Risk → Decision → Action
```

Each step is checkable. That is the Decision Integrity Layer.

---

## 6. Product sold

**ADQA** is the core SKU. Decision OS packages, Guardian Network, and UGS are how ADQA is delivered across tiers.

Vision one-liner:

> NARNA ensures every AI decision is evidence-based, policy-compliant, risk-aware, and human-aligned.
