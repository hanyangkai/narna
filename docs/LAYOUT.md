# NARNA repo layout (vision → current)

Incremental map — **no big-bang rename**. Prefer docs + thin SDK aliases over moving `src/uap/`.

| Vision path | Current path | Status |
|-------------|--------------|--------|
| `agent/runtime/` | `src/uap/narna_agent.py` | alias: `from narna.runtime import NarnaAgent` |
| `adqa/` | `src/uap/adqa.py` | alias: `from narna import ADQAEngine, evaluate` |
| `decision/trace/` | `src/uap/decision_trace.py` | alias: `from narna.decision import DecisionTraceStore` |
| `decision/replay/` | `src/uap/decision_replay.py` | alias: `from narna.decision import replay_trace` |
| `models/` | `src/uap/model_router.py` | alias: `from narna.runtime import ModelRouter` |
| `benchmark/` | `benchmark/` + `src/uap/decision_benchmark.py` | keep public `benchmark/` |
| `sdk/` | `src/narna/` | keep |
| `cloud/` | `web/backend/` | keep |
| `skills/hub/` | `src/uap/skill_hub.py` | keep |

Physical moves only after B1–B5 stay green for a release cycle.

See also: [`NARNA-MARKET-PLAN.md`](./NARNA-MARKET-PLAN.md) § B6.
