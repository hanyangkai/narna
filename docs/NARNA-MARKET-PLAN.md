# NARNA Market Plan — Borrow Runtime, Own Decision Layer

**Promise:** *NARNA Agent — an AI agent that gets better at making decisions.*

**Strategy:** Do not beat Hermes on tool count. Beat everyone on **Decision Quality**.

Refs: NGS-0024 ADQA · NGS-0025 Decision Memory · NGS-0026 Outcome Learning · NGS-0028 Model Router · NGS-0029 Agent  
Companion: [`HERMES-GAP-PLAN.md`](./HERMES-GAP-PLAN.md) (runtime parity track)

---

## Three layers (product architecture)

```text
                    NARNA
                      │
        ┌─────────────┴─────────────┐
        │                           │
   NARNA AGENT                NARNA ADQA
   "Do the work"              "Make it better"
   (distribution)             (moat)
        │                           │
        └─────────────┬─────────────┘
                      │
              DECISION MEMORY
                      │
                   OUTCOME
                      │
                   LEARN
```

| Layer | Today in repo | Gap vs vision |
|-------|---------------|---------------|
| **Agent** | `src/uap/narna_agent.py`, 32 tools, gateways, MCP ask | Hermes runtime ~80% — see HERMES-GAP-PLAN |
| **ADQA** | `src/uap/adqa.py`, `/v1/adqa/check`, MCP `narna_adqa_check` | Need universal evaluate API + ACT/REVIEW/REJECT gate |
| **Decision Memory** | `src/uap/decision_memory.py`, Ask records | Need **Decision Trace** schema (structured) |
| **Outcome Learning** | `src/uap/outcome_learning.py`, `/v1/learning/evaluate` | Wired; needs trace linkage |
| **Replay** | — | **Not built** — killer feature |
| **Benchmark** | `src/uap/benchmark.py` (partial) | Need public Decision Benchmark |
| **Model Router** | cheap/reason/challenge | Need **quality/critical consensus** modes |

---

## Track A — Agent runtime (Hermes parity)

Execute [`HERMES-GAP-PLAN.md`](./HERMES-GAP-PLAN.md) phases P1–P8.

**Rule:** Agent features ship only if they feed Decision Traces (tool use, evidence, alternatives logged).

**Current slice:** P1 browser_vision + P2 execute_code RPC (in progress).

---

## Track B — Decision layer (moat) — NEW phases

### B1 — Decision Trace v1 (3 days)

**Status:** ✅ Shipped — `decision_trace.py` · Ask emits `traceId` · API + CLI + MCP

**Goal:** Every Ask → structured trace, not just DQS number.

Schema `DecisionTrace` (store in `.uap/decision-traces/{id}.json`):

```json
{
  "traceId": "trace_…",
  "decisionId": "dec_…",
  "goal": "…",
  "context": {},
  "evidence": [{"type": "url", "ref": "…"}],
  "options": [{"id": "A", "label": "…"}],
  "chosen": "B",
  "rationale": "…",
  "adqa": {"dqs": 91, "guardian": "…"},
  "toolsUsed": [],
  "modelsUsed": [],
  "action": "recommend",
  "outcome": null,
  "lesson": null,
  "createdAt": "…"
}
```

**Tasks:**
1. `src/uap/decision_trace.py` — write/read/list
2. `narna_agent.ask` → emit trace after ADQA
3. API `GET /v1/decision/traces`, `GET /v1/decision/traces/{id}`
4. Ask UI: “View decision trace” link on each reply

**Verify:** Ask once → trace file exists with evidence + tools.

---

### B2 — Decision Replay v1 (3 days)

**Status:** ✅ Shipped — `decision_replay.py` · `narna replay` · `POST /v1/decision/replay`

**Goal:** “Replay this decision with today's knowledge.”

**Tasks:**
1. `src/uap/decision_replay.py` — load trace + current memory priors + re-ask
2. CLI `narna replay {traceId}` + API `POST /v1/decision/replay`
3. Output: `{original, replayed, changed: bool, delta}`

**Verify:** Record outcome FAIL on trace → replay suggests different option when lesson exists.

---

### B3 — ADQA Universal API (2 days)

**Status:** ✅ Shipped — `from narna import evaluate` · `POST /v1/adqa/evaluate` · MCP `narna_evaluate_action`

**Goal:** Any agent (Hermes, LangGraph, custom) calls NARNA without switching runtime.

**Tasks:**
1. Stabilize `POST /v1/adqa/evaluate` alias (action + evidence + context → DQS + verdict)
2. MCP tools: `narna_evaluate_action`, `narna_verify_evidence`, `narna_predict_outcome` (stub)
3. Python SDK one-liner: `narna.evaluate(decision_dict)` in `src/narna/sdk.py`
4. Docs: “Wrap your agent with ADQA in 5 lines”

**Verify:** External JSON decision → DQS without running full Ask.

---

### B4 — Model Router modes: Cheap / Quality / Critical (3 days)

**Status:** ✅ Shipped — `complete_mode()` · Ask `mode=` · UI Mode selector

Map to existing router tasks:

| Mode | Behavior |
|------|----------|
| **cheap** | 1 model → ADQA |
| **quality** | 2 models → merge → ADQA |
| **critical** | 3 models + critic + evidence validator → ADQA |

**Tasks:**
1. Extend `ModelRouter.complete` with `mode=quality|critical`
2. Ask flag `?mode=critical` (Team plan gate optional)
3. Log all model outputs in Decision Trace

**Verify:** critical mode produces 3 entries in trace.modelsUsed.

---

### B5 — NARNA Decision Benchmark v0 (5 days) ✅

**Goal:** Public reproducible “Does your agent make good decisions?”

**Shipped:**
1. `benchmark/decisions/` — 55 JSON scenarios (research, code, procurement, legal, compliance, finance)
2. `narna benchmark run --agent mock|strip` → accuracy + DQS stats (`src/uap/decision_benchmark.py`)
3. `benchmark/README.md` + empty `leaderboard.json` (no fake marketing numbers)
4. CI: `pytest tests/test_decision_benchmark.py` (subset + strip agent)

**Verify:** `pytest tests/test_decision_benchmark.py` green; README has run instructions.

---

### B6 — Repo layout (incremental, not big-bang)

Do **not** rename everything at once. Map vision → current paths:

| Vision | Current | Migration |
|--------|---------|-----------|
| `agent/runtime/` | `src/uap/narna_agent.py` | symlink/docs alias first |
| `adqa/` | `src/uap/adqa.py` | keep |
| `decision/trace/` | **new** `decision_trace.py` | B1 |
| `decision/replay/` | **new** `decision_replay.py` | B2 |
| `models/` | `src/uap/model_router.py` | B4 |
| `benchmark/` | `src/uap/benchmark.py` + `benchmark/` | B5 |
| `sdk/` | `src/narna/` | B3 |
| `cloud/` | `web/backend/` | keep |

Full physical move only after B1–B3 stable.

---

## Track C — Business / GTM (align with BUSINESS-MODEL.md)

| Tier | Agent | ADQA | Trace | Replay | Hosted |
|------|-------|------|-------|--------|--------|
| **Free OSS** | ✓ local BYOK | basic | basic trace | — | — |
| **Cloud $20** | hosted Ask | full ADQA API | cloud traces | — | memory sync |
| **Pro $30–50** | multi-model | advanced | replay | ✓ | routing |
| **Team $99/seat** | shared brain | governance | team traces | ✓ | SSO later |

**Free forever:** Agent + Memory + MCP + Basic ADQA + Basic Trace + BYOK.  
**Never:** company-hosted LLM as default.

---

## Flywheel (north star)

```text
FREE NARNA AGENT → developers → decisions → traces → outcomes
    → learning → better ADQA → better decisions → ecosystem
```

**Market position target:**

> “I use Hermes to work, Claude to think — NARNA to check whether the decision was good.”

---

## Execution order (combined)

```
DONE    B1 Trace · B2 Replay · B3 evaluate · B4 router modes · B5 Decision Benchmark
NOW     A: P4–P8 Hermes runtime (time-boxed) when needed
LATER   B6 repo layout migration
```

---

## Anti-patterns (from spec + product lock)

- ❌ “Hermes but different color” — no tool-count arms race
- ❌ Nous Portal clone
- ❌ Fake benchmark numbers in marketing
- ❌ Agent as moat — Agent is **distribution**
- ✅ ADQA + Trace + Replay + Benchmark as moat

Last updated: 2026-08-26
