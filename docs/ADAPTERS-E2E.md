# Adapter e2e — OpenAI Agents SDK · MCP · OpenTelemetry

Copy-paste demos. No cloud keys required for the governance gate itself.

```bash
pip install -e .
# optional: openai mcp opentelemetry-sdk opentelemetry-exporter-otlp
```

---

## 1. OpenAI Agents SDK / OpenAI client

```python
# examples/e2e_openai.py
from narna import wrap, ConstitutionRuntime
from pathlib import Path

ws = Path("demo-openai")
ws.mkdir(exist_ok=True)

# Bind a Governance Package (deny biometric scrape, etc.)
ConstitutionRuntime(ws).load(provider="eu-ai-act", version="2.0.0")

class FakeOpenAIAgent:
    """Stand-in for agents.Agent / OpenAI client — replace with real SDK."""
    def run(self, prompt: str) -> str:
        return f"model-output:{prompt}"

FakeOpenAIAgent.__module__ = "agents.agent"

agent = wrap(FakeOpenAIAgent(), workspace=ws, vap=True, mode="enforce")
print(agent._adapter)  # narna-openai
print(agent._wrapped.run("hello"))  # allowed via external.invoke
```

Deny before side-effect:

```python
from narna.adapters.base import NarnaGovernanceDenied

# Package rule denies biometric.scrape — expose as tool name via MCP-style kwargs
# or load a package that denies external.invoke for your org.

try:
    # With fleet.yaml deny or package rule matching action openai.run
    agent._wrapped.run("x")
except NarnaGovernanceDenied as e:
    print("blocked:", e)
```

CLI:

```bash
narna init --name OpenAIDemo
narna governance load --provider eu-ai-act --version 2.0.0
narna validate
```

---

## 2. MCP

```python
# examples/e2e_mcp.py
from narna import wrap, ConstitutionRuntime
from pathlib import Path

ws = Path("demo-mcp")
ws.mkdir(exist_ok=True)
ConstitutionRuntime(ws).load(provider="hipaa", version="2.0.0")

class FakeMcpClient:
    def call_tool(self, name: str, arguments: dict | None = None):
        return {"ok": True, "tool": name, "args": arguments or {}}

FakeMcpClient.__module__ = "mcp.client"

client = FakeMcpClient()
agent = wrap(client, workspace=ws, vap=True, mode="enforce")
print(agent._adapter["package"])  # narna-mcp

# Allowed tool
print(client.call_tool("memory.read", {}))

# Denied by HIPAA package (phi.exfiltrate)
from narna.adapters.base import NarnaGovernanceDenied
try:
    # ConstitutionRuntime matches action tool.phi.exfiltrate or permission external.invoke
    # Force governance execute on package action:
    from uap.governance_runtime import ConstitutionRuntime as CR
    d = CR(ws).execute(action="phi.exfiltrate")
    assert d["decision"] == "deny"
    print("hipaa deny ok:", d["reasons"])
except Exception as e:
    print(e)
```

---

## 3. OpenTelemetry

```python
# examples/e2e_otel.py
from narna import wrap
from pathlib import Path

ws = Path("demo-otel")
ws.mkdir(exist_ok=True)

class FakeTracer:
    def start_as_current_span(self, name: str):
        class _Span:
            def __enter__(self): return self
            def __exit__(self, *a): return False
        return _Span()

FakeTracer.__module__ = "opentelemetry.trace"

tracer = FakeTracer()
agent = wrap(tracer, workspace=ws, vap=False, mode="observe")
print(agent._adapter["package"])  # narna-opentelemetry
with tracer.start_as_current_span("agent.run"):
    pass

# Export a NARNA run summary as OTel attributes / OTLP (optional deps)
# narna otel export --run <runId> --endpoint http://localhost:4318/v1/traces
```

---

## Enforce vs observe

| Mode | Behavior |
|------|----------|
| `enforce` (default) | Policy + active Governance Package evaluated **before** host method |
| `observe` | Meter + audit after call — migration path |

```bash
export NARNA_ADAPTER_MODE=enforce
```

## Prove locally

```bash
python -m unittest tests.test_adapter_enforce -v
narna conformance --workspace .
```
