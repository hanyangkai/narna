# RFC-0006: Adapter Catalog

- **Status:** Accepted / Implemented (v0)  
- **Authors:** NARNA maintainers  
- **Created:** 2026-07-17  
- **Normative:** [`../docs/BORROW-THE-WAVE.md`](../docs/BORROW-THE-WAVE.md)

---

## Summary

Formalize the **NARNA Adapter Catalog** — official `narna-*` packages that extend Agentic AI frameworks without replacing them.

---

## Motivation

Borrow the Wave requires a discoverable, versioned list of supported hosts so every new framework release becomes a distribution channel.

---

## Catalog (v0)

| Adapter ID | Package | Works with |
|------------|---------|------------|
| `openai` | `narna-openai` | OpenAI Agents SDK / client |
| `anthropic` | `narna-anthropic` | Anthropic / Claude |
| `google` | `narna-google` | Google ADK / Gemini |
| `langgraph` | `narna-langgraph` | LangGraph |
| `crewai` | `narna-crewai` | CrewAI |
| `mcp` | `narna-mcp` | MCP servers/clients |
| `opentelemetry` | `narna-opentelemetry` | OpenTelemetry traces |
| `openshell` | `narna-openshell` | OpenShell |
| `moltbook` | `narna-moltbook` | Moltbook / OpenClaw |

### Planned

`narna-autogen`, `narna-semantic-kernel`, `narna-llamaindex`

---

## API

```python
from narna import wrap, ADAPTER_CATALOG
agent = wrap(my_langgraph_app, vap=True)
print(ADAPTER_CATALOG)
```

Adapters **MUST** set `agent._adapter` metadata and **MUST NOT** replace host execution models.

---

## OTLP bridge (v0.1)

```bash
narna otel export --run <runId>
```

Maps NARNA run summaries to OTel span attributes; optional OTLP HTTP export when SDK installed.

---

## Compatibility impact

**Never Replace check:** Pass by definition.

---

## Implementation

`src/narna/adapters/`, `ADAPTER_CATALOG` in `__init__.py`, website Compatibility + Landing adapter grid.
