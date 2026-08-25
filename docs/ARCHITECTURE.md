# NARNA Architecture — Decision Intelligence OS

**Status:** Normative overview  
**Date:** 2026-07-31  
**Product docs:** [`ADQA.md`](./ADQA.md) · [`DECISION-INTELLIGENCE.md`](./DECISION-INTELLIGENCE.md) · [`GUARDIAN-NETWORK.md`](./GUARDIAN-NETWORK.md)

---

## 1. Layers (full stack)

```text
┌─────────────────────────────────────────────────────────────┐
│ Citizen / Console / Extension / Enterprise UI                 │
├─────────────────────────────────────────────────────────────┤
│ ADQA Core (NGS-0024)     Decision Quality Score · Guardian    │
│ Decision Memory (0025)   Outcomes · Lessons · Priors          │
│ Decision OS (0014)       Packages · Connect · Knowledge       │
├─────────────────────────────────────────────────────────────┤
│ UGS Core (0001–0013)     Identity · Policy · Evidence · Trust │
│ Guardian L2–L4 (0015–20) Capability · Threat · Kill · CTI     │
│ Citizen Gateway (0021–23) Protected Mode · Passport status    │
├─────────────────────────────────────────────────────────────┤
│ Host / MCP / LLM frameworks (adapters — never replace)        │
│ Optional Memory Layer (CMEM / DurableMemory / MCP)            │
│   → CmemBridge (narna-cmem) feeds ADQA memory attribute       │
└─────────────────────────────────────────────────────────────┘
```

Hot adapters: OpenAI · Anthropic · Google · LangGraph · CrewAI · AutoGen · Semantic Kernel · LlamaIndex · MCP · CMEM · OTel · Moltbook.

See [`INTEGRATIONS.md`](./INTEGRATIONS.md) · [`CMEM-BRIDGE.md`](./CMEM-BRIDGE.md).

---

## 2. Cognitive loop (normative)

| Tier | Module | Spec |
|------|--------|------|
| Perception | Connect / ingest | Decision OS |
| Memory | DurableMemory · external CMEM | NGS-0025 inputs |
| Reasoning | Host agent / package rules | NGS-0014 |
| Decision Guardian | ADQA | NGS-0024 |
| Learning | Outcome Learning | NGS-0026 |

---

## 3. Data plane

| Store | Path | Contents |
|-------|------|----------|
| Decision Memory | `.uap/decision-memory/` | dmem records |
| Learning priors | `.uap/learning/priors.json` | per-action hints |
| Durable memory | `.uap/memory/durable/` | context scopes |
| CTI hub | `.uap/guardian/cti-hub/` | signatures |
| Citizen devices | `.uap/citizen/` | free-tier keys |

Cloud (`api.narna.org`) persists the same contracts behind HTTP.

---

## 4. Commercial plane

| Plan | Price | Maps to |
|------|-------|---------|
| OSS | Free | Local ADQA + Decision Memory |
| Cloud | $20/mo | API + synced Decision Memory |
| Team | $99/seat/mo | Shared policies · audit |
| Enterprise | Custom | On-prem · packages · SSO |

---

## 5. Non-goals

- Replacing CMEM / vector memory products  
- Training foundation models on private prompts  
- Claiming absolute safety
