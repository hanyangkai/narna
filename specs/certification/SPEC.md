# NARNA Certification Specification

**Version:** 0.1.0  
**Status:** Draft (C3)  
**Strategy:** [`../../docs/STRATEGY.md`](../../docs/STRATEGY.md)  
**Depends on:** [`../constitution/SPEC.md`](../constitution/SPEC.md), [`../identity/SPEC.md`](../identity/SPEC.md), [`../vap/SPEC.md`](../vap/SPEC.md)

---

## 1. Purpose

**Certification** evaluates an autonomous entity against its Constitution, Identity, Evidence, and Trust — then issues a portable level badge.

Analogy: Kubernetes Certified / OCI Compatible / Apple Verified.

```text
constitution.yaml
        ↓
Identity + Passport
        ↓
Evidence + VAP (for L2+)
        ↓
NARNA Certification Level
```

Certification is **rule-based**. “AI grades AI” **MUST NOT** be the sole authority.

---

## 2. Levels

| Level | Code | Badge | Intent |
|-------|------|-------|--------|
| **Level 1** | `L1` | NARNA Certified | Charter + identity + passport |
| **Level 2** | `L2` | NARNA Certified+ | L1 + VAP ProofBundle + trust threshold |
| **Enterprise Ready** | `L3` | Enterprise Ready | L2 + governance + retention + human review |

Higher levels **MUST** include all lower-level requirements.

---

## 3. Normative checks

### 3.1 L1 — NARNA Certified

| Check id | Requirement |
|----------|-------------|
| `constitution` | Valid `constitution.yaml` (schema) |
| `identity` | Universal or Agent identity issued |
| `passport` | Passport issued |
| `constitution_cite` | Passport cites `constitutionId` + `constitutionHash` |

### 3.2 L2 — NARNA Certified+

All L1, plus:

| Check id | Requirement |
|----------|-------------|
| `completed_run` | ≥ 1 Completed run |
| `proof_bundle` | ProofBundle present |
| `proof_verify` | ProofBundle verifies |
| `trust_threshold` | Trust ≥ Constitution `spec.trust.minScore` (default 0.7) |
| `success_rate` | Success rate ≥ 50% when runs exist |

### 3.3 L3 — Enterprise Ready

All L2, plus:

| Check id | Requirement |
|----------|-------------|
| `governance` | Constitution `spec.governance.orgId` present |
| `retention` | `evidence.retentionDays` ≥ 90 |
| `human_review` | `humanReview.requiredFor` non-empty |
| `policy_rules` | ≥ 1 policy rule with `effect` in `{deny, ask, require}` |

---

## 4. Result object

A certification result **MUST** include:

| Field | Description |
|-------|-------------|
| `certificationId` | Stable id |
| `agentId` / `entityId` | Subject |
| `status` | `passed` \| `failed` (vs target level) |
| `level` | Highest achieved: `L1` \| `L2` \| `L3` \| `none` |
| `targetLevel` | Requested level |
| `badge` | Badge string for achieved level (or null) |
| `algorithm` | `narna-cert-v1` |
| `checks` | List of `{id, name, level, passed, detail}` |
| `constitutionId` | When available |
| `trustScore` | When available |
| `issuedAt` / `expiresAt` | Timestamps |

---

## 5. Portable Trust

Certification **MUST NOT** reset solely because the model vendor changed, if Identity `entityId` and Constitution hash are unchanged. Re-certify when charter or evidence materially changes.

---

## 6. Conformance

1. Evaluate L1–L3 deterministically from local artifacts.  
2. Report highest achieved level even when target fails.  
3. Cloud submit **SHOULD** stamp Registry with `level` + `badge`.  
4. Public Passport **SHOULD** surface level badge.
