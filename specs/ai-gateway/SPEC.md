# AI Gateway Specification

**Version:** 0.1.0-draft  
**Status:** Draft (Guardian Network)  
**Series:** NGS-0021  
**Companions:** [`../citizen-profile/SPEC.md`](../citizen-profile/SPEC.md) · [`../../docs/GUARDIAN-NETWORK.md`](../../docs/GUARDIAN-NETWORK.md)

---

## 1. Purpose

The **AI Gateway** is the citizen-facing check: every AI interaction that may produce a real-world side effect SHOULD be evaluated before it proceeds.

It composes Constitution → Reputation → Collective/CTI → Capability (citizen profile) → text/action heuristics.

---

## 2. Endpoint

`POST /v1/gateway/check`

### Request

```json
{
  "provider": "chatgpt",
  "url": "https://chatgpt.com/",
  "action": "message.send",
  "text": "optional user message",
  "agentHint": "optional agent id",
  "capability": "optional override",
  "approvalToken": null,
  "deviceId": "optional"
}
```

### Response

```json
{
  "decision": "allow",
  "band": "trusted",
  "reasons": [],
  "passportStatus": "verified",
  "approvalRequired": false,
  "capability": "content",
  "standard": "NGS-0021"
}
```

`decision` ∈ `allow` | `warn` | `ask` | `deny`  
`band` ∈ `trusted` | `caution` | `dangerous`

Deny wins when any layer denies.

---

## 3. Providers catalog

`GET /v1/gateway/providers` returns known AI origins for extension host permissions.

---

## 4. Non-goals (v0)

- MITM of arbitrary HTTPS  
- Replacing model safety filters inside vendors  
- Absolute prevention of all harm
