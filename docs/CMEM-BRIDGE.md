# CMEM Bridge — Continuity memory in; Decision Quality out

**Status:** Active  
**Date:** 2026-07-31  
**Rule:** NARNA never replaces [CMEM](https://cmem.ai/). CMEM answers *what do we remember?* ADQA answers *is this decision good enough to act?*

---

## Split

| Layer | Product | Question |
|-------|---------|----------|
| Memory continuity | CMEM / claude-mem | What happened? Why? |
| Decision quality | NARNA ADQA | May we act? DQS? |
| Learning | NARNA Outcome Learning | What should change next time? |

Cognitive loop: Perception → **CMEM** → Reasoning → **ADQA Guardian** → **Learning**

---

## Wire-up

```bash
# Point at your private CMEM MCP / HTTP link
export NARNA_CMEM_URL="https://mcp.cmem.ai/u/YOUR_LINK"
# optional
export NARNA_CMEM_TOKEN="…"

# Optional: ADQA gate on every adapter host call
export NARNA_ADQA=1
export NARNA_ADQA_STRICT=0   # 1 = block on reject/escalate
```

```python
from narna import wrap, ADQAEngine
from uap.cmem_bridge import CmemBridge

agent = wrap(my_langgraph_app, vap=True)
# CMEM feedstock auto-enriches DecisionEngine / ADQA when URL or local observations exist

ctx = CmemBridge().enrich_context("contract.sign")
out = ADQAEngine().check_proposed(action="contract.sign", context=ctx)
```

### MCP tools (any hot client)

`narna_adqa_check` · `narna_dmemory_query` · `narna_learning_prior` · `narna_cmem_enrich`

```python
from narna.mcp_tools import NarnaMcpTools
NarnaMcpTools().call_tool("narna_adqa_check", {"action": "contract.sign"})
```

### Plugin

`plugins/narna-cmem` — `register(agent)` exposes search / enrich / mcp_tools.

### Adapter

`narna-cmem` wraps CMEM MCP client methods (`call_tool`, `search`, `recall`, …).

---

## Local offline mode

Without `NARNA_CMEM_URL`, the bridge reads/writes `.uap/cmem-bridge/observations.jsonl` for tests and air-gapped demos.
