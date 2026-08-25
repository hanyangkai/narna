# NARNA Decision OS

**Status:** Active (Enterprise module)  
**Date:** 2026-07-29  
**Related:** [`STRATEGY.md`](./STRATEGY.md) · [`DIFFERENTIATION.md`](./DIFFERENTIATION.md) · [`../specs/decision-package/SPEC.md`](../specs/decision-package/SPEC.md)

---

## Positioning

**Category:** Decision Quality Infrastructure for AI Agents  
**Product core:** **ADQA** — Autonomous Decision Quality Assurance ([`ADQA.md`](./ADQA.md))  
**Primary:** The Trust Layer for AI Decisions.  
**Supporting:** NARNA does not create decisions — it assures their quality (DQS).

**Decision OS** is the enterprise **delivery surface** for ADQA (packages, connect, memory, automation) — not a chatbot.

> Every AI decision ships with a **Decision Quality Score**, evidence, risk, policy check, Decision Guardian verdict, and audit log.

---

## Module map (Enterprise platform)

```text
NARNA
├── Connect     — MCP · API · DB · Files · Email · ERP · CRM
├── Knowledge   — entities & relations from enterprise data
├── Memory      — durable project / customer / contract context
├── Decision ★  — flagship: reason → risk → recommend → prove
├── Governance  — Policy · Permission · Audit · Approval · Compliance
├── Automation  — Email → Decision → Approval → ERP → Done
└── Marketplace — Decision Packages · Agents · Policies · Workflows
```

Infrastructure lock still holds: **NARNA governs. Others execute.**  
Decision OS uses UGS Packages + VAP Evidence + GU metering; it does **not** replace LangGraph / OpenAI / MCP.

---

## Decision flow

```text
Input (email · contract · invoice · CRM · voice …)
        ↓
Context Engine (Knowledge · Memory · Policy · Prior decisions · Role)
        ↓
Decision Engine (Understand → Analyze → Compare → Score → Recommend)
        ↓
Governance gate (allow / deny / ask / require-approval)
        ↓
Execute (only if allowed) + Evidence + Audit
```

Example output:

```json
{
  "decision": "ask",
  "recommendation": "Do not sign as-is. Amend clause 5.",
  "riskScore": 0.92,
  "riskBand": "critical",
  "reasons": ["3 adverse clauses", "package rule legal-clause-5"],
  "requiredApprovals": ["legal.counsel", "finance.controller"],
  "evidence": ["mustProve: policy.decision", "mustProve: human.review"],
  "auditRef": { "sessionId": "session_…", "packageId": "pkg_legal_decision" }
}
```

---

## Decision Package

Customers do **not** buy “an AI”. They install industry packs:

| Package | Industry |
|---------|----------|
| Legal Decision Package | Law firm |
| Procurement Decision Package | Logistics / ops |
| Finance Decision Package | Controllership |
| HR Decision Package | People ops |
| Hospital Decision Package | Healthcare |
| Crypto Exchange Decision Package | Trading / compliance |

All six seed packages ship under `specs/examples/packages/*-decision.yaml` (install via `narna dmarket install <provider>`).

A **Decision Package** composes Governance Packages (RiskProfile, HumanApproval, Compliance) and defines the **decision output contract**.

Normative: [`../specs/decision-package/SPEC.md`](../specs/decision-package/SPEC.md)

---

## What ships now vs later

| Layer | Now (v0.1+) | Later |
|-------|-------------|-------|
| Positioning + docs | ✅ | — |
| Decision Package schema + evaluate CLI/API | ✅ | — |
| Risk score + reasons + approvals + evidence refs | ✅ | — |
| Full Knowledge graph / Memory store | ✅ v0 file graph + durable scopes | Enterprise graph DB |
| Connectors (ERP/CRM/Email) | ✅ Connect registry + probe | Live OAuth connectors |
| Marketplace Decision Packages | ✅ `dmarket list/install` | partner packs + billing |
| Automation | ✅ `automate run` plan stub | Host executors |

---

## Messaging rules

1. Lead with **Decision Layer / Decision OS** for enterprise buyers.  
2. Keep **UGS + Packages + GU** for developers / infra buyers.  
3. Never position NARNA as “another ChatGPT for business”.  
4. Passport is a **feature of UGS**, not the brand.  
5. For Guardian / civilizational claims: link [`GUARDIAN.md`](./GUARDIAN.md) and stay honest — Decision OS is Layer 1, not absolute defense.

---

## Beyond Decision OS

Decision OS is the **enterprise product**. The full **AI Guardian Infrastructure** (Capability Passport, sandbox, threat engine, kill tiers, collective defense) is documented in [`GUARDIAN.md`](./GUARDIAN.md).
