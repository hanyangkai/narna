# NARNA

**Neural Autonomous Runtime Architecture**

> *The Open Runtime for Trusted AI Agents.*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)

NARNA is the open runtime and trust infrastructure for AI Agents.  
**UAP** is the protocol (*Understand · Act · Prove*).  
**VAP** is the trust engine (*Verify · Audit · Prove*).

## Phase 1 — 30 seconds

```bash
pip install -e .
```

```python
from narna import Agent

agent = Agent()
agent.run()
```

Offline. No account. No cloud. No dashboard.

```python
agent = Agent("Researcher")
agent.enable_vap()   # Verify → Audit → Prove after each run
agent.run("hello")
```

```python
from narna import wrap

agent = wrap(my_existing_agent, name="Wrapped")
agent.run("task")
```

## CLI

```bash
narna init
narna doctor
narna verify
narna passport
narna benchmark
```

(`uap` remains as an alias for the protocol CLI.)

## Self-host (optional cloud)

```bash
docker compose up --build
```

## Docs

- Spec: [`specs/`](./specs/)
- Brand: [`docs/BRAND.md`](./docs/BRAND.md)
- Self-host: [`docs/SELF-HOST.md`](./docs/SELF-HOST.md)

## License

MIT — see [`LICENSE`](./LICENSE).
