# NGS-0030: Decision Trace & Replay

- **Status:** Active  
- **Product:** [`../../docs/NARNA-MARKET-PLAN.md`](../../docs/NARNA-MARKET-PLAN.md)

## Intent

Every agent decision is stored as a **Decision Trace** (goal, evidence, options, chosen, ADQA, tools, outcome).  
**Replay** re-evaluates a past trace with today's lessons.

## Surfaces

| Surface | Path |
|---------|------|
| Store | `src/uap/decision_trace.py` |
| Replay | `src/uap/decision_replay.py` |
| Ask emit | `NarnaAgent.ask` → `traceId` |
| API | `GET /v1/decision/traces`, `GET /v1/decision/traces/{id}`, `POST /v1/decision/replay` |
| Evaluate | `POST /v1/adqa/evaluate`, `from narna import evaluate` |
| CLI | `narna trace list|get`, `narna replay`, `narna evaluate` |
| MCP | `narna_trace_*`, `narna_replay`, `narna_evaluate_action` |

## Verdict mapping

| Guardian / DQS | Verdict |
|----------------|---------|
| reject/block | REJECT |
| review/ask or DQS &lt; 70 | REVIEW |
| else | ACT |
