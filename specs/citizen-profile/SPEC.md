# Citizen Profile Specification

**Version:** 0.1.0-draft  
**Status:** Draft  
**Series:** NGS-0022  
**Parent:** NGS-0015 Capability Passport · [`../../docs/CITIZEN-GUARDIAN.md`](../../docs/CITIZEN-GUARDIAN.md)

---

## 1. Purpose

A **citizen profile** is a Capability Passport preset for public users: default-deny on dangerous real-world actions.

Profiles: `citizen` (free) · `family` (stricter) · `enterprise` (org packages — out of scope here).

---

## 2. Citizen grants (normative defaults)

| Capability | Mode |
|------------|------|
| `search` / `content` / `read` | allow |
| `email` | ask |
| `payment` / `wallet` / `trade` | deny |
| `contract` | deny |
| `create.agent` | deny |
| `device` / `terminal` | deny |
| `mcp` | restricted |

Family profile: `email` → deny; `content` may still allow with CTI warn.

---

## 3. Approval

Dangerous modes that are `ask` MAY proceed only with a short-lived `approvalToken` issued after explicit human confirm (extension modal). Biometrics/WebAuthn are non-goals for v0.
