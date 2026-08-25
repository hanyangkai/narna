# Universal AI Passport (Consumer)

**Version:** 0.1.0-draft  
**Status:** Draft  
**Series:** NGS-0023  
**Builds on:** NGS-0001 Identity · NGS-0007 Passport

---

## 1. Purpose

Consumer-facing **status** for any AI the user meets:

| Status | Meaning |
|--------|---------|
| `verified` | Cryptographic / platform-attested identity known to NARNA |
| `unverified` | No passport or unattested |
| `blocked` | Kill token, critical reputation, or CTI blocklist |

Like HTTPS certificates for AI agents — not a permission grant by itself (still NGS-0007: Passport MUST NOT alone authorize).

---

## 2. Gateway mapping

| Passport status | Default band | Capability floor |
|-----------------|--------------|------------------|
| verified | trusted | citizen grants as-is |
| unverified | caution | tighten ask/deny on money/agent/device |
| blocked | dangerous | deny all side-effect actions |

---

## 3. Seed providers (v0)

Platform-verified stubs: `chatgpt`, `claude`, `gemini`, `deepseek`, `copilot`.  
Unknown `agentHint` → `unverified`.
