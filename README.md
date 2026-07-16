# NARNA

**Neural Autonomous Rules Native Architecture**

> *The Constitution Layer for Autonomous AI.*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)

NARNA is the **AI Constitution Layer** — identity, governance, and trust for autonomous systems.  
It does **not** replace OpenTelemetry, MCP, LangGraph, CrewAI, or model vendors. It sits **above** them.

**UAP** is the protocol (*Understand · Act · Prove*).  
**VAP** is the trust engine (*Verify · Audit · Prove*).  
**Constitution** is the charter artifact (`constitution.yaml`).

> OpenTelemetry records what AI did. NARNA defines who AI is, what it is allowed to do, and why others can trust it.

**Strategy lock:** [`docs/STRATEGY.md`](./docs/STRATEGY.md) · **Spec:** [`specs/constitution/SPEC.md`](./specs/constitution/SPEC.md)

## Spec first

```bash
# Read before coding
docs/STRATEGY.md
specs/constitution/SPEC.md
specs/examples/constitution.yaml
```

## Phase 1 — 30 seconds (reference SDK)

```bash
pip install -e .
```

```python
from narna import Agent

agent = Agent()
agent.run()
```

Offline. No account. No cloud. The SDK is a **virus entry / reference client** — not the strategic USP.

## Phase 2 — Verify every action

```python
agent = Agent("Researcher")
agent.enable_vap()
result = agent.run("btc price")
print(result.trust_score)
```

## Phase 3 — Publish to Registry

```python
agent.publish()
```

## Phase 4 — Certification levels

```python
agent.enable_vap()
agent.run("btc price")
cert = agent.certify(level="L3")
print(cert["level"], cert["badge"])
# L3  Enterprise Ready
```

| Level | Badge | Meaning |
|-------|-------|---------|
| L1 | NARNA Certified | Constitution + Identity + Passport |
| L2 | NARNA Certified+ | L1 + VAP proof + trust threshold |
| L3 | Enterprise Ready | L2 + governance + retention + human review |

```bash
narna certify --vap --level L3 --local
```

## Constitution (center)

```yaml
# narna.yaml — default metadata (compiles to constitution.yaml)
apiVersion: narna.ai/v1alpha1
kind: Manifest
identity:
  id: research-agent
capabilities: [web.search, github.read]
permissions:
  - name: browser
    mode: allow
policies: [human_approval, no_money_transfer]
trust:
  minimum_score: 0.9
```

```python
from narna import wrap, track, load_or_compile_constitution

load_or_compile_constitution("narna.yaml")
agent = wrap(my_existing_agent, vap=True)

@track
def research(q: str) -> str: ...
```

```bash
narna manifest --compile
```

## Compatibility

OpenTelemetry · MCP · OpenAI · Anthropic · Google · LangGraph · CrewAI · OpenShell · Docker · Kubernetes

- Program: [`/compatibility`](./web/frontend) · Spec: [`specs/compatibility/SPEC.md`](./specs/compatibility/SPEC.md)
- Adapters: `narna-openai` · `narna-langgraph` · `narna-mcp` · `narna-opentelemetry` · `narna-crewai`
- Plugins: [`plugins/`](./plugins/)
- Fleet: `narna fleet --path fleet.yaml`
- Benchmark: `narna benchmark --governance`
- Foundation: [`docs/FOUNDATION.md`](./docs/FOUNDATION.md)
- TypeScript stub: [`sdks/typescript`](./sdks/typescript)

## Docs

- Strategy: [`docs/STRATEGY.md`](./docs/STRATEGY.md)
- Borrow the Wave: [`docs/BORROW-THE-WAVE.md`](./docs/BORROW-THE-WAVE.md)
- Brand: [`docs/BRAND.md`](./docs/BRAND.md)
- Specs: [`specs/`](./specs/)
- RFCs: [`rfcs/`](./rfcs/)
- Self-host: [`docs/SELF-HOST.md`](./docs/SELF-HOST.md)

## License

MIT — see [`LICENSE`](./LICENSE).
