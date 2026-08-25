# Autonomous Decision Quality Assurance (ADQA)

**Version:** 0.1.0-draft  
**Status:** Draft  
**Series:** NGS-0024  
**Product:** [`../../docs/ADQA.md`](../../docs/ADQA.md)

---

## 1. Purpose

ADQA scores a **proposed decision** before execution. Output includes:

- Attribute scores (10)
- **DQS** (0–100)
- **Decision Guardian** verdict: `approve` | `revise` | `escalate` | `reject`
- Constitution checks (Truth · Logic · Alignment · Safety · Authority · Accountability)

---

## 2. Endpoint

`POST /v1/adqa/check`

May also attach `adqa` onto `POST /v1/decision/evaluate` results.

### Response (excerpt)

```json
{
  "dqs": 89,
  "attributes": { "evidence": 92, "policy": 100 },
  "guardian": "approve",
  "constitution": { "truth": "pass", "safety": "pass" },
  "standard": "NGS-0024"
}
```

---

## 3. Guardian mapping

| DQS / signals | Guardian |
|---------------|----------|
| DQS ≥ 80 and no hard fail | approve |
| DQS 60–79 or soft gaps | revise |
| ask / missing approvals / medium risk | escalate |
| deny / constitution fail / DQS &lt; 60 | reject |

---

## 4. Non-goals

- Replacing the LLM’s reasoning tokens  
- Claiming absolute correctness of decisions  
- Executing side effects (Execution Layer is separate)
