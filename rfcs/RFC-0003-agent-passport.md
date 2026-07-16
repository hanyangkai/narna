# RFC-0003: Agent Passport

- **Status:** Accepted / Implemented  
- **Authors:** NARNA maintainers  
- **Created:** 2026-07-17  
- **Normative:** [`../specs/identity/SPEC.md`](../specs/identity/SPEC.md) · [`../specs/schemas/passport.schema.json`](../specs/schemas/passport.schema.json)

---

## Summary

Define a portable **Agent Passport** — a materialized trust view for any autonomous entity, analogous to GitHub Verified, Apple Developer ID, or Docker Official Image badges.

---

## Motivation

Agentic AI fleets span vendors and frameworks. Buyers and auditors need a single portable artifact answering:

- Who is this agent?
- What may it do?
- What trust evidence exists?
- Which governance package applies?

---

## Detailed design

Passport **MUST** include:

| Field | Required | Meaning |
|-------|----------|---------|
| `passportId` | yes | Unique passport instance |
| `identity` | yes | Agent identity + `specHash` |
| `capability` | yes | Declared + observed capabilities |
| `permissions` | yes | Effective permission grants |
| `history` | yes | Run counts and last run |
| `trust` | yes | VAP trust score snapshot |
| `constitution` | optional | Constitution id + hash |
| `governance` | optional | Active Governance Package citation |

Passports **MAY** be published to Registry and linked from Compatibility badges.

---

## Compatibility impact

**Never Replace check:** Pass. Passport cites host frameworks; does not replace LangGraph/OpenAI identity models.

---

## Alternatives

1. Cloud-only registry cards (rejected — not offline-first).  
2. OTel resource attributes only (rejected — observability ≠ governance proof).

---

## Unresolved questions

- Passport signing (Ed25519 over passport body)  
- Cross-registry passport federation  

---

## Implementation

Landed in `src/uap/passport.py`, `src/uap/passport_sign.py` (Ed25519 sign/verify), `narna passport --verify` CLI, `/v1/passport/verify` API, `/passport/:agentId` web viewer, Registry publish path.
