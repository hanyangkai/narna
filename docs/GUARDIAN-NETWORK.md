# NARNA Guardian Network — Public Safety Infrastructure for AI

**Status:** Active (v1 target)  
**Date:** 2026-07-31  
**Slogan:** Every human protected. Every AI accountable. Every action governed.  
**Related:** [`GUARDIAN.md`](./GUARDIAN.md) · [`CITIZEN-GUARDIAN.md`](./CITIZEN-GUARDIAN.md) · [`DECISION-OS.md`](./DECISION-OS.md)

---

## 1. Category shift

| Before (v0) | After (v1) |
|-------------|------------|
| AI Governance Platform | **Public Safety Infrastructure for AI** |
| Protect when AI is already inside your system | Protect humans **by default** between people and every AI |
| Buyer: security / compliance | Buyer: citizens · families · enterprises · platforms |

Analogy: **HTTPS for the web** · **antivirus for the PC** · **Guardian Layer for AI**.

Honesty: Defense-in-Depth reduces harm. It does **not** claim absolute civilizational safety.

---

## 2. Design goal

> Every AI that acts in the real world goes through NARNA.

Users MUST NOT need to understand MCP, prompt injection, or capability graphs.  
They turn on **Protected Mode**. NARNA does the rest.

---

## 3. Five layers

```text
Citizen layer       Guardian App · Browser · Mobile · OS (later)
AI interaction      AI Gateway · Identity · Capability Passport
Safety              Threat Detection · Policy · Sandboxing · Approval
Intelligence        Reputation · Threat Sharing · Collective Defense
Governance          Constitution · Emergency Response · Audit
```

Enterprise Decision OS remains the **enterprise tier** of the same network — not a separate product.

---

## 4. Three-tier public utility

| Tier | Who | What |
|------|-----|------|
| **1 — Free** | Individuals | Guardian Extension / App · Protected Mode · citizen default-deny |
| **2 — Family** | Households | Child / elder profiles · bank & device guards |
| **3 — Enterprise** | Orgs | Decision · Governance · Automation · MCP · Audit · GU |

All tiers share the **Guardian Network** backend (CTI, reputation, constitution, kill).

---

## 5. Standards (new)

| NGS | Spec |
|-----|------|
| NGS-0021 | [`../specs/ai-gateway/SPEC.md`](../specs/ai-gateway/SPEC.md) |
| NGS-0022 | [`../specs/citizen-profile/SPEC.md`](../specs/citizen-profile/SPEC.md) |
| NGS-0023 | [`../specs/universal-ai-passport/SPEC.md`](../specs/universal-ai-passport/SPEC.md) |

Compose existing NGS-0001…0020 (identity, capability passport, collective, kill, reputation, constitution).

---

## 6. Ship surface (v1 Phase 1)

1. **AI Gateway** — `POST /v1/gateway/check`  
2. **Citizen register** — free device key  
3. **Chrome MV3 extension** — [`../apps/guardian-extension/`](../apps/guardian-extension/)  

Later: Universal Passport badges · approval UX · CTI device sync · emergency broadcast · family / mobile.
