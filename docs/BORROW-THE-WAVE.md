# Borrow the Wave — Growth Strategy Lock

**Status:** Locked  
**Date:** 2026-07-16  
**Companion:** [`STRATEGY.md`](./STRATEGY.md) (positioning) · this file (how we grow)

---

## Decision that makes or breaks NARNA

Do **not** compete with Big Tech.

> **Turn every OpenAI / Anthropic / Google / NVIDIA release into a growth event for NARNA.**

That is **Borrow the Wave** — ride their product launches; never race them on runtime, models, or SDKs.

---

## Principle #1 — Never Replace. Always Extend.

| Wrong | Right |
|-------|-------|
| We replace OpenAI | **Works with OpenAI** |
| We replace LangGraph | **Extends LangGraph** |
| We replace OpenTelemetry | **Reads OTel; owns Evidence + Trust** |

Success metric:

> OpenAI, Anthropic, Google, Microsoft can integrate NARNA **without changing their architecture**.

---

## Architecture (unchanged)

```text
                 NARNA
 Identity · Policy · Passport · Trust · Governance · Certification
────────────────────────────────────────────────────────────────
 OpenTelemetry · MCP · OpenAI · Claude · Gemini · Docker · K8s · OpenShell
```

Sit **above**. Do not invent another bottom layer.

---

## Ten tactics (locked)

| # | Tactic | What we ship |
|---|--------|----------------|
| 1 | Never Replace | Positioning + Compatibility badges |
| 2 | **Adapter First** | `narna-openai`, `narna-mcp`, `narna-langgraph`, … |
| 3 | **One-line integration** | `wrap(agent)` · `@narna.track` |
| 4 | Compatibility Program | Verified by NARNA · UAP Compatible · Enterprise Ready |
| 5 | Plugin Economy | Community plugins (`narna-slack`, …) |
| 6 | **RFC process** | Community-governed specs (KEP/PEP style) |
| 7 | Reference implementation | Thin Python SDK — others may implement .NET/Go/Rust |
| 8 | Foundation path | Open spec + open governance; Inc sells Enterprise |
| 9 | Governance benchmark | Trust/compliance rankings — not LLM MMLU |
| 10 | **Default metadata** | Every agent ships `narna.yaml` |

---

## Borrow-the-Wave matrix

| They ship | NARNA responds |
|-----------|----------------|
| OpenAI new Agents SDK | `narna-openai` adapter ≤ 1 week |
| Anthropic / MCP change | Adapter + Certification update |
| NVIDIA runtime | Runtime adapter only |
| OTel AI traces | Trust engine reads OTLP |
| LangGraph workflow | Workflow Passport |
| Docker AI container | `narna.yaml` / Manifest |

---

## Default metadata — `narna.yaml`

Like `Dockerfile` / `action.yml` / `deployment.yaml`.

If every agent eventually has:

```text
narna.yaml
```

we win on **metadata**, not SDK surface area.

Normative: [`../specs/manifest/SPEC.md`](../specs/manifest/SPEC.md)  
Developer short-form compiles to Constitution.

---

## What is done vs remaining

### Done (Constitution Layer core)

- Strategy + Constitution Spec  
- Universal Identity (C1)  
- Passport cites Constitution  
- Certification L1/L2/L3 (C3)  
- Registry / Passport / Cloud stamp  
- Reference SDK: `Agent`, VAP, `publish`, `certify`  
- Web aligned to Constitution Layer  

### Remaining (Borrow the Wave — priority order)

| Priority | Item | Status |
|----------|------|--------|
| P0 | `narna.yaml` Manifest Spec + loader | **this pass** |
| P0 | One-line `wrap` + `@track` | **this pass** |
| P0 | Adapter package scaffold + detect | **this pass** |
| P0 | RFC process + RFC-0001 | **this pass** |
| P1 | Real adapters: openai / mcp / langgraph / otel | next |
| P1 | Compatibility Program pages + badge SVG | next |
| P2 | Plugin repo template + marketplace listing | later |
| P2 | Governance benchmark leaderboard | later |
| P3 | Fleet Governance Spec (C4) | later |
| P3 | Foundation / open governance charter | later |
| P3 | TypeScript / Go reference SDKs | later |

---

## Non-goals (reinforce)

- Do not build “the” agent runtime  
- Do not aim to “beat OpenAI”  
- Do not invent another telemetry standard  

Aim: **be the default governance metadata layer they all attach to.**
