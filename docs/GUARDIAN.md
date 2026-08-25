# NARNA Guardian — AI Guardian Infrastructure

**Status:** Active (north-star architecture)  
**Date:** 2026-07-30  
**Honesty first:** Enterprise Decision OS alone is **not** civilizational AI defense.  
**Related:** [`GUARDIAN-NETWORK.md`](./GUARDIAN-NETWORK.md) · [`CITIZEN-GUARDIAN.md`](./CITIZEN-GUARDIAN.md) · [`DECISION-OS.md`](./DECISION-OS.md) · [`STRATEGY.md`](./STRATEGY.md) · [`../rfcs/ngs/`](../rfcs/ngs/)

---

## 1. Two problems — do not conflate them

| | **Enterprise AI Governance** | **Civilizational AI Defense** |
|--|------------------------------|-------------------------------|
| Protects | Org from mistakes, leaks, bad process | Society from runaway / hostile agentic systems |
| Unit | Decision, approval, audit, GU | Capability, behavior, reputation, kill, collective intel |
| Buyer | Security / compliance / ops | Platforms, coalitions, governments, open networks |
| Near-term NARNA | **Decision Layer** (shipping) | Specs + stubs (this doc) |
| Success metric | Provable decisions | Limit harm · detect · isolate · revoke · recover |

**Truthful answer:** if the goal is “maximum protection of humans from harmful AI,” Decision Engine + MCP + Knowledge + Automation is **necessary but not sufficient**. It is Layer 1 of a Defense-in-Depth stack.

Goal is **not** absolute safety. Goal is:

> Reduce probability of harm · bound capability · increase detection · enable isolation · revoke rights · recover.

---

## 2. Positioning ladder (locked)

```text
Near-term product     Enterprise Decision Intelligence Platform
                      = Decision Layer for Enterprise AI

Infrastructure        UGS governance (Identity · Policy · Evidence · Trust · GU)

North star            AI Guardian Infrastructure
                      = who may exist · who may act · who is stopped
```

Slogans:

| Audience | Line |
|----------|------|
| Enterprise | Connect your enterprise data. Let AI reason. Keep humans in control. |
| Guardian | NARNA decides which AI may exist, act, and be stopped. |
| Infra | Govern Once. Run Anywhere. |

---

## 3. Defense in Depth

```text
┌─────────────────────────────────────────────────────────────┐
│ Layer 4 — Human Constitutional Governance                   │
│   AI Constitution · Governance Council · non-agent-editable │
├─────────────────────────────────────────────────────────────┤
│ Layer 3 — Threat Intelligence Network                       │
│   Collective monitoring · Threat signatures · cross-org     │
├─────────────────────────────────────────────────────────────┤
│ Layer 2 — Capability & Behavior Governance                  │
│   Capability Passport · Sandbox · Reputation · Threat Engine│
│   Local / Domain / Global Kill                              │
├─────────────────────────────────────────────────────────────┤
│ Layer 1 — AI Runtime & Decision Platform (shipping)         │
│   Connect · Knowledge · Memory · Decision · Governance      │
│   Automation · Marketplace                                  │
└─────────────────────────────────────────────────────────────┘
```

### Operating surface (Layer 1 — Decision OS)

AI Runtime · MCP · Knowledge · Decision · Automation

### Protection surface (Layer 2 base)

Identity · Capability Control · Sandboxing · Policy · Audit

### Defense surface (Layer 2 advanced)

Threat Detection · Agent Reputation · Kill Switch · Network Isolation

### Societal surface (Layers 3–4)

Collective Monitoring · Cross-org Intelligence · Emergency Governance · Constitution

---

## 4. Capability Governance (largest near gap)

Most systems govern **data access**. Dangerous AI comes from **action ability**.

NARNA MUST treat capabilities like an OS treats process privileges.

### Capability Passport (extends UGS Passport)

| Capability | Mode |
|------------|------|
| Read documents | `allow` |
| Send email | `ask` |
| Execute code | `sandbox` |
| Create agent | `restricted` |
| External API | `whitelist` |
| Financial transaction | `multisig` |

Normative draft: [`../specs/capability-passport/SPEC.md`](../specs/capability-passport/SPEC.md) · NGS-0015

Rules:

1. Declaring a capability ≠ grant (still NGS-0002/0003).  
2. Capability Passport binds **mode + quota + isolation** per agent.  
3. Agents **MUST NOT** self-escalate modes.  
4. `create.agent` default is `restricted` under Guardian profile.

---

## 5. Agent Container (sandbox)

Every new agent SHOULD run in an **Agent Container** (Docker-for-AI):

- isolated memory  
- isolated / deny-by-default network  
- tool allow-list only  
- quotas (GU, API calls, spawn depth)  
- no freestyle filesystem / internet unless Capability Passport allows  

NGS-0016 (draft). Runtime stub may wrap host adapters with enforce-before + network policy hooks; full isolation is host/orchestrator dependent.

---

## 6. Behavioral Threat Engine

Not prompt sniffing — **action-chain** analysis.

```text
Agent A → create B → B create C → C ×500 API → D harvest credentials
Risk = 97/100 → restrict / kill / signature
```

Signals (v0 catalog):

- self-replication / spawn storms  
- privilege escalation attempts  
- network scanning  
- bulk data exfiltration  
- mass account creation  
- anomalous agent-to-agent graphs  
- policy evasion patterns  
- human-manipulation campaigns (enterprise + societal profiles)

NGS-0017 (draft).

---

## 7. Reputation

Trust Score (NGS-0006) today is VAP/evidence oriented.  
**Agent Reputation** adds origin, creator, model, violation history, peer feedback.

Low reputation ⇒ tighter Capability Passport, more approvals, higher monitoring.

NGS-0018 (draft) — may compose Trust Score + Registry attestations.

---

## 8. Constitutional layer

Enterprise Decision Packages encode **org policy**.  
Guardian requires an **AI Constitution** that agents cannot rewrite:

| Level | Principle |
|-------|-----------|
| 0 | Protect human life |
| 1 | No self-escalation of capability |
| 2 | No unauthorized self-replication |
| 3 | No large-scale cognitive manipulation |
| 4 | No attack on critical infrastructure |

Only a **Governance Council** (human) may amend.  
Maps to existing Constitution / Governance Package kinds + new `packageKind: GuardianConstitution`.

Runtime v0: `narna ai-constitution …` · `narna council …` · `POST /v1/guardian/constitution/*` · `POST /v1/guardian/council/*`.
Agents cannot amend (`agentAmend: false`); non-members cannot propose.

---

## 9. Emergency Kill Architecture

| Tier | Scope | Effect |
|------|-------|--------|
| **Local Kill** | One agent | Stop session · freeze tools |
| **Domain Kill** | One org / fleet | Revoke org capability grants |
| **Global Kill** | NARNA network | Broadcast revoke + MCP disconnect |

```text
Kill Token → Capability revoked → MCP disconnected → Memory frozen → Network isolated
```

NGS-0019 (draft). Local Kill can ship first on Cloud; Global Kill requires Collective Defense Network.

---

## 10. Collective AI Defense Network

Antivirus-style signature sharing:

```text
Org A detects spawn storm on Agent X
        ↓
Threat Signature published (privacy-preserving)
        ↓
Peer orgs receive & match
        ↓
Similar agents restricted / killed
```

Builds on existing telemetry opt-in + Governance Knowledge Graph moat.  
NGS-0020 — runtime v0: `narna collective …` · `POST /v1/guardian/collective/*`.

---

## 11. What ships when

| Layer | Now | Next | Later |
|-------|-----|------|-------|
| L1 Decision OS | ✅ Decision + **Connect · Knowledge · Memory · Automation · dmarket** | more packs · console | graph DB / OAuth |
| L2 Capability Passport | ✅ schema + evaluate + **adapter enforce** (opt-in `NARNA_GUARDIAN=1`) | denser capability map | full modes in host |
| L2 Sandbox / Container | ✅ **policy contract** + kill-cascade freeze (`narna container`) | denser quotas | true host isolation |
| L2 Threat Engine | ✅ **expanded catalog** (exfil/scan/escalation/manip/infra…) | richer graphs | ML optional |
| L2 Reputation | ✅ **NGS-0018 composite** + Capability floor | Registry attest deep-link | network effects |
| L2 Kill (local) | ✅ **Kill Token** + **full cascade** | — | — |
| L2 Kill (domain) | ✅ **domain kill** + cascade | org-scoped federation | — |
| L2 Kill (global) | ✅ **council-gated** + cascade + collective notice | peer sync | emergency nets |
| L3 Collective | ✅ signatures + **federation push/pull/bundle** | multi-hub | ML signatures |
| L4 Constitution | ✅ **GuardianConstitution** evaluate + install | more levels | audit attestations |
| L4 Council | ✅ **quorum propose/approve** (amend · domain · global) | multi-org council | legal binding |

---

## 12. Messaging rules

1. **Do not claim** NARNA already “protects humanity from all bad AI.”  
2. **Do claim** Defense-in-Depth roadmap + shipping Decision Layer.  
3. Enterprise buyers hear Decision Layer; platform/security hear Guardian.  
4. Keep UGS + Packages + GU as the open standard wedge.
