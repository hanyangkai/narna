# Integrations — NARNA + hot AI stacks

**Philosophy:** Never Replace. Always Extend.

NARNA is Decision Quality Infrastructure. It sits **beside** models, orchestrators, and memory layers.

---

## Memory partner

| Partner | Role | NARNA package |
|---------|------|----------------|
| [CMEM / claude-mem](https://cmem.ai/) | Continuity memory (MCP) | `narna-cmem` + `CmemBridge` |

See [`CMEM-BRIDGE.md`](./CMEM-BRIDGE.md).

---

## Hot stacks (adapters)

| Stack | Package | Status |
|-------|---------|--------|
| OpenAI / Agents | `narna-openai` | available |
| Anthropic / Claude | `narna-anthropic` | available |
| Google Gemini / ADK | `narna-google` | available |
| LangGraph | `narna-langgraph` | available |
| CrewAI | `narna-crewai` | available |
| AutoGen / AG2 | `narna-autogen` | available |
| Semantic Kernel | `narna-semantic-kernel` | available |
| LlamaIndex | `narna-llamaindex` | available |
| MCP | `narna-mcp` | available |
| CMEM | `narna-cmem` | available |
| OpenTelemetry | `narna-opentelemetry` | available |
| Moltbook / OpenClaw | `narna-moltbook` | available |
| OpenShell | `narna-openshell` | available |

```python
from narna import wrap
agent = wrap(foreign_runtime)  # auto-detects framework
```

Enable Decision Quality on every hooked call:

```bash
export NARNA_ADQA=1
```

---

## One MCP surface for every IDE / agent CLI

Cursor · Claude Code · Codex · Gemini CLI · OpenClaw can call:

1. CMEM MCP — recall observations  
2. NARNA MCP tools — `narna_adqa_check` before irreversible actions  

Catalog API: `GET /v1/integrations`
