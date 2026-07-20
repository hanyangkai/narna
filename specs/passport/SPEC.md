# AI Passport — UGS / NGS-0007

**Status:** Normative (v0.1)  
**RFC:** [NGS-0007](../../rfcs/ngs/NGS-0007-passport.md)  
**Schema:** [`../schemas/passport.schema.json`](../schemas/passport.schema.json)  
**Alias:** UAP-Core §5, RFC-0003

---

## 1. Definition

A **Passport** is a materialized view summarizing Identity, Capability, Permission posture, history, and Trust.

```text
Events + Evidence  →  (authoritative)
Passport           →  (derived, cacheable, signable)
```

---

## 2. Normative rules

1. Passport MUST include `issuedAt` and `expiresAt` (or `ttl`).  
2. Passport SHOULD include `derivedFrom` = event-log tip hash.  
3. Runtimes MUST NOT grant permissions solely from Passport claims.  
4. Optional Ed25519 signature (NARNA reference: `passport_sign.py`).  
5. Public verify: `GET /v1/passport/{agentId}` · `POST /v1/passport/verify`.

---

## 3. Relation to core six

Built only from NGS-0001…0006 artifacts — MUST NOT invent parallel trust semantics.
