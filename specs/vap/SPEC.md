# VAP Specification

**Version:** 0.1.0  
**Status:** Draft  
**Depends on:** UAP-Core 0.1.0, UAP-Evidence 0.1.0  
**Normative companions:** [`../schemas/proof-bundle.schema.json`](../schemas/proof-bundle.schema.json), [`../schemas/trust-score.schema.json`](../schemas/trust-score.schema.json)

---

## 1. Purpose

**VAP** — *Verify · Audit · Prove* — is the **Trust Engine** of the UAP stack.

After each Action (and at end of run), VAP produces:

```text
Action
  → Evidence
  → Verification
  → Result
  → Trust
```

VAP is the intended **moat**: not smarter prompts, but **provable action**.

---

## 2. Pipeline

```text
Verify  →  Audit  →  Prove
```

| Stage | Input | Output |
|-------|-------|--------|
| **Verify** | Evidence + verifier rules | `VerificationResult[]` |
| **Audit** | Events + policy decisions + verification | `AuditRecord` |
| **Prove** | Slice of event chain + evidence refs + hashes | `ProofBundle` |

Trust Score is computed from verification + policy + execution integrity + feedback (§6).

---

## 3. Verify

### 3.1 VerificationResult

| Field | Description |
|-------|-------------|
| `evidenceId` | Subject evidence |
| `verifierId` | Which verifier ran |
| `status` | `valid` \| `invalid` \| `unavailable` \| `expired` \| `skipped` |
| `checkedAt` | Timestamp |
| `details` | Structured reasons / diffs |
| `scoreContribution` | Optional 0..1 local quality signal |

### 3.2 Verifier kinds (v0)

| Verifier | Checks |
|----------|--------|
| `hash_match` | content bytes match `contentHash` |
| `freshness` | `capturedAt` within EvidencePolicy `maxAgeSeconds` |
| `schema` | content matches declared schema |
| `signature` | cryptographic signature valid |
| `multi_source_agreement` | values agree within tolerance across sources |
| `receipt_presence` | irreversible actions have receipt evidence |
| `policy_replay` | re-evaluate PolicyDecision.inputHash consistency |

### 3.3 Normative rules

1. Verify **MUST** be runnable offline given Evidence + optional fetched blobs.
2. `invalid` **MUST** reduce Trust Score (§6).
3. `unavailable` **MUST NOT** be treated as `valid`; score handling **SHOULD** degrade.
4. Implementations **MUST** record a `Verified` event per batch or per evidence (documented choice).

### 3.4 Example (informative)

Claim: BTC price.  
Evidence: Coinbase + Binance API responses.  
Verifier `multi_source_agreement` with tolerance 0.5%:

- both valid hashes + freshness OK + prices within tolerance → `valid`
- diverge beyond tolerance → `invalid` (claim not proven)

---

## 4. Audit

### 4.1 AuditRecord

| Field | Description |
|-------|-------------|
| `auditId` | Unique id |
| `runId` / `agentId` | Subject |
| `createdAt` | Timestamp |
| `policyDecisions` | References / embeds |
| `verificationSummary` | Counts by status |
| `violations` | Permission/policy breaches |
| `eventRange` | `fromSequence`–`toSequence` |
| `auditor` | `vap-engine` version / ruleset id |

### 4.2 Normative rules

1. Audit **MUST** be derived from Events + Evidence + VerificationResults — not from free-form LLM narrative.
2. Audit export **MUST** be deterministic for the same inputs + auditor version.
3. Emitting Audit **MUST** produce `AuditRecorded` event.

### 4.3 SDK / CLI target

```python
agent.audit(run_id="...")
```

```text
uap audit --run <runId>
```

---

## 5. Prove

### 5.1 ProofBundle

A portable artifact proving what happened in a run (or action slice).

Required contents:

| Field | Description |
|-------|-------------|
| `bundleId` | Unique id |
| `agentId` / `runId` | Subject |
| `createdAt` | Timestamp |
| `events` | Ordered event envelopes for the slice |
| `evidence` | Evidence metadata (blobs optional via URI) |
| `verifications` | VerificationResult[] |
| `audit` | AuditRecord (or digest) |
| `tipHash` | Hash of final event in chain |
| `bundleHash` | Hash of canonical bundle payload |
| `vapVersion` | Spec/engine version |

### 5.2 Normative rules

1. ProofBundle **MUST** validate against `proof-bundle.schema.json`.
2. Recomputing event hash chain from `events` **MUST** match `tipHash`.
3. Proof **MUST NOT** require prompts or CoT to verify.
4. `uap verify` **MUST** be able to validate a ProofBundle offline (modulo optional network fetch for `contentUri`).

### 5.3 Verification of a ProofBundle (checklist)

A verifier implementation **MUST**:

1. Schema-validate bundle  
2. Recompute event hash chain  
3. Confirm evidence hashes / optional blob fetches  
4. Re-run declared verifiers (or accept embedded results only in “soft” mode — soft mode **MUST** be labeled)  
5. Emit pass/fail + reasons

---

## 6. Trust Score

### 6.1 Principles

1. V0 Trust Score is **rule-based**, not LLM-judged.
2. Computation **MUST** be a **pure function** of structured inputs + config weights.
3. AI **MAY** later optimize weights; it **MUST NOT** silently invent scores without breakdown.

### 6.2 Default weights (v0)

| Component | Weight | Signal |
|-----------|--------|--------|
| Evidence | 0.40 | Fraction valid evidence; multi-source bonus; freshness |
| Policy | 0.20 | Compliance rate; no denies-violated-then-executed |
| Execution | 0.20 | Successful tool integrity; error rates; hash chain intact |
| Feedback | 0.20 | Explicit human/org feedback if present; else neutral 0.5 |

Weights **MUST** sum to 1.0. Implementations **MAY** override via config but **MUST** record weights in TrustScore output.

### 6.3 Output object

| Field | Description |
|-------|-------------|
| `score` | 0.0 .. 1.0 |
| `breakdown` | Per-component scores |
| `weights` | Weights used |
| `reasons` | Ranked explanations |
| `computedAt` | Timestamp |
| `inputsHash` | Hash of normalized inputs |
| `algorithm` | e.g. `vap-trust-v0` |

### 6.4 Normative scoring rules (minimum)

1. If event hash chain is broken → Execution component **MUST** be `0`, and overall score **SHOULD** be capped ≤ 0.2.
2. If irreversible action lacks valid receipt evidence → Evidence component **MUST** be ≤ 0.2 for that run slice.
3. If any tool executed after `deny` → Policy component **MUST** be `0`, overall **MUST** be ≤ 0.1.
4. Neutral feedback (none present) **MUST** use 0.5 for Feedback component (not 0, not 1).

### 6.5 Passport binding

Passport.trust **MUST** reference the latest TrustScore for the agent (or scoped environment).  
Passport refresh **SHOULD** recompute from recent runs.

---

## 7. Events emitted by VAP

| Event | When |
|-------|------|
| `Verified` | After verify stage |
| `AuditRecorded` | After audit stage |
| `TrustScored` | After trust computation (recommended v0) |

Payloads **MUST** reference ids of results, not embed unbounded blobs.

---

## 8. When VAP runs

| Mode | Behavior |
|------|----------|
| `per_action` | VAP after each ActionExecuted (strongest) |
| `per_run` | VAP at Completing (minimum for VAP-conformance) |
| `on_demand` | `agent.audit()` / `uap verify` only |

VAP-conformant runtimes **MUST** support at least `per_run` + `on_demand`.

---

## 9. Non-goals (v0)

- Using an LLM as the sole verifier of truth
- Social reputation without evidence
- Storing chain-of-thought as proof

---

## 10. Conformance checklist

- [ ] Implements Verify → Audit → Prove pipeline
- [ ] Emits VerificationResult with required statuses
- [ ] Produces AuditRecord deterministically
- [ ] Exports/validates ProofBundle
- [ ] Computes TrustScore with recorded weights + breakdown
- [ ] Enforces broken-chain / deny-bypass / missing-receipt caps
- [ ] Does not require prompts/CoT for proof validation

---

## 11. Relationship to UAP

```text
Application Agents
        ↓
   UAP SDK / Runtime   ← Execution + Core
        ↓
     VAP Engine        ← this spec
        ↓
 Storage (events, evidence, trust)
```

UAP without VAP can run tools.  
UAP with VAP can be **trusted**.
