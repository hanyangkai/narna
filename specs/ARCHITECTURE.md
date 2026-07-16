# Architecture (normative orientation)

**Status:** Draft aligned with UAP Spec Set **0.1.0**  
**Audience:** implementers of `uap-sdk`, `uap-runtime`, `vap-engine`

---

## Stack

```text
                         UAP
────────────────────────────────────────
 Application Layer
   Trading Agent · Research Agent · Coding Agent · …
────────────────────────────────────────
 UAP SDK
   Agent() · Tool() · Policy() · Identity() · Passport() · Evidence()
────────────────────────────────────────
 UAP Runtime
   Execution · Permission · Memory Adapter · Tool Adapter · Event Bus
────────────────────────────────────────
 VAP Engine
   Verify · Audit · Evidence check · Trust Score · Policy Check
────────────────────────────────────────
 Storage
   Identity · Execution (events) · Evidence · Benchmark
────────────────────────────────────────
 Any LLM
   GPT · Claude · Gemini · Llama · Ollama · …
```

---

## Control flow (single action)

```text
Model proposes intent
        ↓
Validate tool input schema          (UAP-Execution)
        ↓
PolicyDecision                      (UAP-Core Policy)
        ↓
  deny → stop + event
  ask  → AwaitingInput
  allow ↓
Tool.execute                        (Tool Adapter)
        ↓
EvidenceAttached                    (UAP-Evidence)
        ↓
VAP: Verify → Audit → (Trust)       (VAP)
        ↓
Continue / Complete
```

---

## Source of truth

| Artifact | Authoritative? | Notes |
|----------|----------------|-------|
| Event log (hash-chained) | **Yes** | Append-only |
| Evidence metadata + hashes | **Yes** | Blobs optional via URI |
| Identity | **Yes** (immutable) | Rotation = new identity |
| Passport | **No** | Materialized view |
| TrustScore | **Derived** | Pure function; record weights |
| Model prompts / CoT | **Not required** | Must not be needed for proof |

---

## Package boundaries (future impl)

| Package | Owns |
|---------|------|
| `uap` / `uap-sdk` | Agent API, load AgentSpec, call runtime |
| `uap-runtime` | Lifecycle, adapters, event bus, permission gate |
| `vap-engine` | Verify, Audit, ProofBundle, TrustScore |
| Specs (this tree) | Contracts only |

Company brand is **out of scope** for architecture; protocols remain **UAP** / **VAP**.

---

## Conformance layers

1. **Core-conformant** — AgentSpec, Identity, Events, Permissions  
2. **Execution-conformant** — lifecycle + tool gating + evidence attach for side effects  
3. **VAP-conformant** — ProofBundle + TrustScore + offline `verify`

Aim the reference implementation at layer 2 first, then layer 3.
