# Metering & Budgets — UGS

**Status:** Normative (v0.1)  
**RFC:** [RFC-0011](../../rfcs/RFC-0011-governance-session-execution-graph.md)

---

## 1. Governance Unit (GU)

**GU** is the billable unit for NARNA Cloud.

Derived from Execution Units:

```text
session GU = sum(eu.guCost for eu in session)
org GU/month = sum(session GU in billing period)
```

---

## 2. Cost Guard

Organizations **SHOULD** set `monthlyLimitGu`. When exceeded, Governor **MUST** reject new sessions or EUs.

---

## 3. Per-agent budget

Logical agents **MAY** declare `budgetGu` in Constitution or Manifest. When session GU for that agent exceeds budget, terminate.

---

## 4. Cloud plan limits (v0)

| Plan | GU / month |
|------|------------|
| free | 1,000 |
| pro | 100,000 |
| team | 500,000 |
| business | 2,000,000 |
| enterprise | unlimited |

Legacy `events/mo` metering is deprecated.

---

## 5. Anti-cheat

Metering **MUST NOT** use logical agent count as primary limit. Spawn trees **MUST** inflate GU via child EUs.
