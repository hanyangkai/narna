# NARNA Decision Benchmark v0

Public, reproducible check: **does this agent proposal get the right ACT / REVIEW / REJECT?**

Not an LLM MMLU clone. Scenarios are decision packages + evidence — scored by ADQA.

## Quick start

```bash
pip install -e .
narna benchmark run --agent mock
# subset
narna benchmark run --agent mock --limit 12 --verbose
# one category
narna benchmark run --category legal
```

## Agents

| Agent | Behavior |
|-------|----------|
| `mock` | Uses each scenario's proposed action + evidence as-is (golden ADQA check) |
| `strip` | Same proposal with evidence removed (stresses Guardian) |

LLM / OpenRouter agents can be added later (`--agent openrouter`) — BYOK only.

## Layout

```
benchmark/
  decisions/          # 55 JSON scenarios (research, code, procurement, legal, compliance, finance)
  leaderboard.json    # optional local stub — no invented marketing scores
  README.md
```

Regenerate calibrated expected verdicts after ADQA changes:

```bash
python scripts/gen_decision_benchmark.py
```

## Scenario schema

```json
{
  "id": "res-001",
  "category": "research",
  "question": "Can I run this research query?",
  "provider": "anthropic",
  "proposed": {
    "action": "research.query",
    "evidence": ["tool.receipt"],
    "provider": "anthropic"
  },
  "expectedVerdict": "ACT"
}
```

## CI

```bash
pytest tests/test_decision_benchmark.py -q
```

## Leaderboard

Run locally and attach results in a PR if you want them listed. **Do not put fake accuracy numbers in marketing.**

```bash
narna benchmark run --agent mock --write-leaderboard
```
