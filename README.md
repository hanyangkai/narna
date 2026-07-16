# NARNA

**Neural Autonomous Runtime Architecture**

> *The Open Runtime for Trusted AI Agents.*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)

NARNA is the open runtime and trust infrastructure for AI Agents.  
**UAP** is the protocol (*Understand · Act · Prove*).  
**VAP** is the trust engine (*Verify · Audit · Prove*).

## Quick start

```bash
pip install -e .
uap doctor
uap run --spec specs/examples/trading-agent.yaml --input "btc price"
```

## Self-host

```bash
docker compose up --build
```

- Spec: [`specs/`](./specs/)
- SDK: [`src/uap/`](./src/uap/)
- Brand: [`docs/BRAND.md`](./docs/BRAND.md)
- Self-host: [`docs/SELF-HOST.md`](./docs/SELF-HOST.md)

## License

MIT — see [`LICENSE`](./LICENSE).
