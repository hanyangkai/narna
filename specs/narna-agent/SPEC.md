# NARNA Agent Runtime Specification

**Version:** 0.1.0-draft  
**Status:** Draft  
**Series:** NGS-0029  
**Product:** [`../../docs/NARNA-AGENT.md`](../../docs/NARNA-AGENT.md)

---

## 1. Purpose

**NARNA Agent** is the consumer-facing decision agent. Users ask in natural language; NARNA orchestrates memory, reasoning (via Model Router), ADQA, and Decision Memory — without requiring users to know MCP, RAG, or model names.

---

## 2. Pipeline

```text
User message (+ optional files)
        ↓
Session + Decision Memory priors
        ↓
Research stub (v0: package/context only)
        ↓
Model Router · reason
        ↓
Model Router · challenge (optional / Pro)
        ↓
ADQA check (DQS + Guardian)
        ↓
Answer + DQS badge + decisionId
        ↓
Outcome (later) → Learning
```

---

## 3. API

### `POST /v1/agent/ask`

Auth: optional API key; anonymous allowed with IP / device rate limits.

```json
{
  "message": "Should I sign this contract?",
  "sessionId": "optional",
  "files": [{"name": "c.txt", "text": "…"}],
  "challenge": false
}
```

```json
{
  "answer": "…",
  "dqs": 78,
  "guardian": "revise",
  "decisionId": "dmem_…",
  "modelsUsed": ["…"],
  "sources": [],
  "sessionId": "…",
  "standard": "NGS-0029"
}
```

### `POST /v1/agent/outcome`

Attach outcome to a prior `decisionId` for Outcome Learning.

---

## 4. Quotas

| Plan | Agent turns / month (hard) |
|------|----------------------------|
| free | 50 |
| cloud (Personal) | 5_000 |
| team | 50_000 |

Metered as `agent_turns_in_period` on the organization (anonymous → shared free bucket per IP hash).

---

## 5. Non-goals

- MITM of third-party chat UIs  
- Claiming absolute truth of recommendations  
- Full web browsing agent in v0  
- Requiring users to install local software for Ask
