# NARNA Business Model — Trust as a Service (TaaS)

**Status:** Locked  
**Date:** 2026-07-17  
**Related:** [`STRATEGY.md`](./STRATEGY.md) · [`WEB-BIZ-MVP.md`](./WEB-BIZ-MVP.md) · [`POSITIONING.md`](./POSITIONING.md)

---

## Core insight

Infrastructure startups rarely die from bad technology. They die when the **business model does not scale**.

Docker, GitHub, and HashiCorp all took years to find enterprise revenue. NARNA should learn from proven models — not invent monetization from scratch.

---

## Philosophy

**NARNA does not sell Runtime.**

**NARNA sells Trust as a Service (TaaS).**

| Audience | Gets | Pays for |
|----------|------|----------|
| **Developer** | Free runtime (`pip install narna`) | Nothing — local OSS |
| **Team / Cloud** | Registry, Passport, verification, history | Subscription |
| **Enterprise** | Compliance, SSO, org governance, audit | Contract |

Like Docker: Docker Engine is free. Docker Hub + Docker Business are the business.

---

## Architecture

```text
                 OSS (100%)

pip install narna → narna.yaml → Runtime → Audit → Policy → Identity
                                                              100% FREE

──────────────────────────────────────────────────────────────────────

                              Cloud Layer

Account → Registry → Passport → Verification → History → Certification
         → Organization → Compliance

──────────────────────────────────────────────────────────────────────

                              Enterprise

SSO · SOC2 · On-prem · Custom governance · Dedicated support
```

**OSS is the funnel. Cloud is revenue. Enterprise is margin.**

---

## User flow

### 1. Developer

```bash
pip install narna
```

No login. No account. No payment. Build agents locally.

### 2. Share / publish

```bash
narna publish
```

→ “Please login” → GitHub / Google / Apple

### 3. With account

Registry · Passport · Cloud history · Verification

### 4. Verify / certify

Paid Cloud features or one-time certification

---

## Pricing principle: Governance Units (GU), not Agents or raw Events

**Do not price by logical agent count** — spawn trees cheat (`1 agent → 1000 workers`).

**Do not price only by opaque event volume** — developers do not intuit `500k events`.

**Price by Governance Units (GU)** derived from **Execution Units (EU)**:

| Concept | Role |
|---------|------|
| **Logical Agent** | Identity — Passport, Constitution, Policy (1 per role) |
| **Execution Unit** | Metered action — tool, sub-agent, LLM step, MCP, workflow node |
| **Governance Session** | Container for one execution graph |
| **Governor** | Budget, loop detection, recursion risk, Cost Guard |

Default: **1 EU = 1 GU**. Spawn tree inflates GU honestly.

```text
CEO Agent (1 Logical Identity)
└── session_123
    ├── Planner     1 GU
    ├── Search    300 GU
    ├── Browser   200 GU
    └── SQL       400 GU
    = 901 GU  (cannot claim "1 agent")
```

Normative: [`../specs/metering/SPEC.md`](../specs/metering/SPEC.md) · RFC: [`../rfcs/RFC-0011-governance-session-execution-graph.md`](../rfcs/RFC-0011-governance-session-execution-graph.md)

---

## Plan summary (locked)

### Developer — FREE

- Unlimited local runtime & audit
- Unlimited local policies (local GU metering only)
- Community registry (read)
- Open SDK + CLI — **no account**

### Cloud Pro — $19/mo

- **100,000 GU / month**
- Private registry
- Cloud verification + Passport
- 90-day history
- Governance dashboard + API

### Cloud Team — $49/mo

- **500,000 GU / month**
- Organization + shared registry
- RBAC + Evidence Center
- 365-day history
- Priority support

### Enterprise — Custom

- Unlimited GU (or custom quota)
- SSO, SOC2, on-prem
- Compliance + custom governance
- Dedicated support + Cost Guard at org level

---

## Revenue streams

### 1. Cloud subscription (primary)

Monthly recurring — Pro $19, Team $49 (GU-metered).

### 2. Registry

Docker Hub model: public free, **private registry** on paid plans.

### 3. Passport Verification API (USP)

```http
GET /v1/passport/{agentId}
```

```json
{
  "verified": true,
  "trust": 96,
  "policy": "enterprise-v2"
}
```

Metered or included in Cloud tiers.

### 4. Certification

| Level | Price (indicative) |
|-------|-------------------|
| NARNA Certified Agent | $100 |
| NARNA Certified Package | $500 |
| Enterprise certification | $5,000 |

Comparable to Kubernetes certification / compliance badges.

### 5. Governance Package Marketplace

Third-party authors publish:

- EU AI Act Package
- HIPAA Healthcare Package
- PCI DSS Finance Package
- Internal Company Policy Package

**NARNA take rate:** 20%. Author keeps majority.

```text
Governance Author
        │
        ▼
  NARNA Marketplace  ← network effect
        │
        ▼
Enterprise / Developers
```

This is the **AWS Marketplace of Governance** — a revenue layer beyond SaaS.

### 6. Enterprise support

SOC2, ISO27001, RBAC, SSO, compliance packages — **$20k+/year**.

---

## Payment roadmap

| Phase | Methods |
|-------|---------|
| **V1** | Stripe — card, Apple Pay, Google Pay |
| **V2** | USDC / USDT (optional) |
| **V3** | Invoice / wire (Enterprise) |

Crypto is **not** day-one priority.

---

## Account model

| Need | Account required? |
|------|-------------------|
| Local runtime, CLI, policies | **No** |
| Registry, Passport, publish, certification | **Yes** |

```text
Developer (free) → pip install → local runtime → no login

Need cloud? → GitHub login → workspace → Stripe customer → subscription

Enterprise → sales → invoice → dedicated cluster (optional)
```

---

## Implementation note

Public pricing and docs reflect **Governance Units (GU)**. Legacy cloud APIs may still expose `events/mo` during migration; **GU limits are primary** (`gu_in_period` on ingest).

**Gaps closed (2026-07-17):**
- Orchestrator shares one Governance Session across child agents
- Adapters (LangGraph/MCP/OpenAI/CrewAI) emit Execution Units
- Console `/console/sessions` + Execution Graph UI
- DB migration: `gu_in_period`, `session_id`, marketplace price/take columns
- Marketplace purchase with **20% take rate** (`POST /v1/packages/purchase`, `narna package buy`)
- **Privacy-preserving Governance Telemetry** (opt-in, sanitized, k-anonymous aggregates) — see [`../specs/governance-telemetry/SPEC.md`](../specs/governance-telemetry/SPEC.md)

---

## Governance Intelligence (moat)

NARNA does **not** monetize prompts or customer content.

With explicit opt-in, Cloud may accept **Governance Metadata only** (agent class, capability family, policy family, decisions, approvals, outcomes, risk/failure bands, GU). Identifiers are HMAC-hashed; public reports are **k-anonymous**.

This yields a **Governance Knowledge Graph** moat: which policies work, which permissions get abused, which agent patterns need human approval — data Google/OpenAI do not have.

Products:
1. **Governance Intelligence** — in-product policy recommendations  
2. **Governance Benchmark** — cohort posture comparison  
3. **Governance Index** — published / enterprise reports  

---

## Change control

Pricing and revenue model changes require update to this doc + `web/frontend/src/brand.ts` (`PRICING`) + `/pricing` page.
