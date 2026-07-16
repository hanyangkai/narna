# UAP MVP Definition

**Version:** 0.1.0  
**Verdict:** **MVP achieved** for reference implementation (local, single-agent, provable runs).

---

## What MVP means for UAP

An MVP is **not** a production platform. It is a **working proof** that the spec contract holds:

```text
Identity → Policy → Action → Evidence → Trust
```

A developer can install, run an agent, get hash-chained events, attach evidence, export a ProofBundle, and verify offline.

---

## MVP checklist (architecture)

| Requirement | Status |
|-------------|--------|
| AgentSpec + schema validation | ✅ |
| Signed Identity + specHash | ✅ |
| Deny-by-default Policy + ask flow | ✅ |
| Tool contract + permission gating | ✅ |
| Hash-chained event log | ✅ |
| Evidence capture (external/irreversible) | ✅ |
| VAP: Verify → Audit → Prove | ✅ |
| Trust Score (rule-based v0) | ✅ |
| Passport (materialized view) | ✅ |
| CLI: init, run, prove, verify, audit, passport | ✅ |
| Local registry (V5 foundation) | ✅ |
| Local marketplace index (V4 foundation) | ✅ |
| Multi-agent orchestrator (V6 foundation) | ✅ |
| Benchmark storage | ✅ |
| `uap doctor --full` conformance | ✅ |

---

## Beyond MVP (not required for MVP)

| Item | Status | Notes |
|------|--------|-------|
| Live HTTP tools | ✅ optional | `UAP_TOOL_MODE=live` (Coinbase/Binance public APIs) |
| Ollama model adapter | ✅ optional | `UAP_MODEL=ollama` |
| OpenAI / Anthropic adapters | ❌ | Next production layer |
| Remote registry / marketplace | ❌ | Local only |
| Production sandbox (Wasm/gVisor) | ❌ | Not in MVP scope |
| Dashboard UI | ❌ | CLI-first by design |
| Abort/cancel run API | ⚠️ partial | State exists, not wired to CLI |
| Event bus externalization (NATS/Kafka) | ❌ | In-process only |
| Identity signature verification on load | ⚠️ partial | Signs on issue, no verify API yet |
| Feedback ingestion API | ❌ | Neutral 0.5 default |

---

## How to validate MVP locally

```bash
pip install -e .
python -m unittest discover -s tests -v

uap init
uap doctor --full --spec specs/examples/trading-agent.yaml
uap run --spec specs/examples/trading-agent.yaml --input "btc price"
uap prove --spec specs/examples/trading-agent.yaml --run <runId>
uap verify --bundle .uap/runs/<runId>/proof-bundle.json
uap benchmark --avg --spec specs/examples/trading-agent.yaml
```

Optional live mode:

```bash
set UAP_TOOL_MODE=live
uap run --spec specs/examples/trading-agent.yaml --input "btc price"
```

Optional Ollama:

```bash
set UAP_MODEL=ollama
set UAP_MODEL_NAME=llama3.2
uap run --spec specs/examples/trading-agent.yaml --input "what is BTC price?"
```

---

## Conformance layers

| Layer | MVP |
|-------|-----|
| Core-conformant | ✅ |
| Execution-conformant | ✅ (reference impl) |
| VAP-conformant | ✅ (rule-based, offline verify) |

---

## Summary

**Yes — MVP is reached** for the reference SDK: the architecture stack is wired end-to-end with specs, schemas, runtime, trust engine, and CLI.

What remains is **production hardening** (cloud LLMs, remote registry, sandboxing, dashboard) — not spec or MVP gaps.
