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

## Phase 4 — Certification

```python
cert = agent.certify()
print(cert["badge"])  # Verified by NARNA
```

## Constitution (center)

```yaml
# constitution.yaml — see specs/examples/constitution.yaml
apiVersion: narna.ai/v1alpha1
kind: Constitution
metadata:
  entityKind: Agent
  entityId: agent_…
spec:
  identity: { … }
  capability: { supports: [browser, sql] }
  permission: { grants: […] }
  policy: { rules: […] }
  evidence: { mustProve: [side_effects] }
  trust: { algorithm: vap-trust-v0, minScore: 0.7 }
```

```python
from narna import load_constitution

c = load_constitution("constitution.yaml")
print(c["metadata"]["entityId"])
```

## Compatibility

OpenTelemetry · MCP · OpenAI · Anthropic · Google · LangGraph · CrewAI · OpenShell · Docker · Kubernetes

## Docs

- Strategy: [`docs/STRATEGY.md`](./docs/STRATEGY.md)
- Brand: [`docs/BRAND.md`](./docs/BRAND.md)
- Specs: [`specs/`](./specs/)
- Self-host: [`docs/SELF-HOST.md`](./docs/SELF-HOST.md)

## License

MIT — see [`LICENSE`](./LICENSE).
