# Citizen Guardian — Protected Mode for everyone

**Status:** Active  
**Date:** 2026-07-31  
**Parent:** [`GUARDIAN-NETWORK.md`](./GUARDIAN-NETWORK.md) · Spec: [`../specs/citizen-profile/SPEC.md`](../specs/citizen-profile/SPEC.md)

---

## 1. Promise

People install the **Guardian Extension** (or App), turn on **Protected Mode**, and every interaction with known AI surfaces is checked by the NARNA AI Gateway before risky actions proceed.

No MCP literacy. No prompt-injection literacy. Default protection.

---

## 2. Protected Mode

When ON:

1. Content script marks the page **NARNA Protected**.
2. On send / dangerous intent, extension calls `POST /v1/gateway/check`.
3. Gateway returns `allow` | `warn` | `ask` | `deny`.
4. Deny/ask blocks submit until resolved; warn shows a banner.

When OFF: extension idle (no interception). User choice is respected.

---

## 3. Default-deny capability table (citizen)

| Capability | Mode |
|------------|------|
| Read / search / Q&A | `allow` |
| Create content (text, image prompts) | `allow` |
| Send money / wallet / payment | `deny` (or `ask` with approval) |
| Sign contract | `deny` / `ask` |
| Create agent / self-replicate | `deny` |
| Control device / OS | `deny` |
| External MCP tools | `restricted` |
| Email send | `ask` |

This is **Zero-Trust for AI** at the citizen edge. Spec: NGS-0022.

---

## 4. What users see

| Signal | Meaning |
|--------|---------|
| Green Trusted | Verified passport + good reputation |
| Yellow Caution | Unverified or medium reputation |
| Red Dangerous | Blocked passport, critical reputation, or CTI hit |

Users never see raw NGS ids in the happy path.

---

## 5. Known AI providers (Phase 1)

ChatGPT · Claude · Gemini · DeepSeek · Copilot · and local fixture pages for tests.  
Not a full-web MITM — host-permission list only.
