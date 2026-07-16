# NARNA Score Specification

**Version:** 0.1.0  
**Status:** Draft  
**RFC:** [`../rfcs/RFC-0004-narna-score.md`](../rfcs/RFC-0004-narna-score.md)

---

## 1. Purpose

**NARNA Score** is a branded 0–100 composite rating of Agentic AI governance posture — analogous to CVSS (security), Lighthouse (web), or credit scores (finance).

It complements **VAP Trust Score** (per-run, 0–1).

---

## 2. Dimensions (v0)

| Dimension | Description |
|-----------|-------------|
| `identity` | Universal Identity issued and entity records present |
| `capability` | Manifest declares capabilities with sufficient breadth |
| `evidence` | VAP proof bundles and auditable run history |
| `governance` | Active Governance Package loaded and bound |
| `compliance` | Certification level (L1/L2/L3) |
| `operational` | Run success rate across history |

Each dimension **MUST** be scored 0.0–1.0.

---

## 3. Algorithm

```text
narna-score-v0:
  score_0_1 = mean(identity, capability, evidence, governance, compliance, operational)
  narnaScore = round(score_0_1 × 100)
```

Implementations **MUST** include `algorithm`, `breakdown`, `computedAt`, and `dimensions` in output.

---

## 4. CLI

```bash
narna score
narna benchmark --narna-score
```

---

## 5. API

```http
GET /v1/score/{agentId}
```

Returns latest computed score when agent workspace is available; otherwise derives from Registry passport + certification metadata.

---

## 6. Non-goals (v0)

- ML-based scoring  
- Paid score manipulation  
- Replacing vendor model safety benchmarks (MMLU, etc.)
