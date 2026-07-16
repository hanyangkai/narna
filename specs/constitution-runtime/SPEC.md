# Constitution Runtime Specification

**Version:** 0.1.0  
**Status:** Draft (G1)  
**RFC:** [`../../rfcs/RFC-0008-constitution-runtime.md`](../../rfcs/RFC-0008-constitution-runtime.md)  
**Strategy:** [`../../docs/STRATEGY.md`](../../docs/STRATEGY.md)

---

## 1. Purpose

The **Constitution Runtime** is the core loop of the Universal AI Governance Runtime:

```text
Load → Execute → Verify → Audit → Version → Switch
```

It governs **Governance Packages** (including Constitutions). It does **not** replace OpenAI / Claude / Gemini / LangGraph as agent executors.

---

## 2. Normative operations

### 2.1 Load

Load a package from:

- filesystem path  
- `provider` + `version` (local cache / examples / registry)  
- `ref` (`registry://…` or relative path)

Conformant implementations **MUST** validate against the Governance Package schema (or Constitution schema when loading `kind: Constitution`).

Load **MUST** compute `packageHash` (SHA-256 of canonical JSON) and write or update the **active binding**.

### 2.2 Execute

On authorize (before a side-effecting tool/capability):

1. Evaluate active package `spec.rules` (deny/ask/require matching `action` / permission)  
2. Evaluate Fleet role denies if `fleet.yaml` present (deny wins)  
3. Evaluate AgentSpec + policy packs via PolicyEngine (deny wins)  
4. Evaluate embedded / bound Constitution `policy.rules` if present  

Result: `allow` | `deny` | `ask`. Deny **MUST** block the side effect.

### 2.3 Verify

Verify ProofBundle / evidence against package `evidence` requirements when present. Attach `packageId` + `packageHash` to verification context.

### 2.4 Audit

Audit export **MUST** include `packageId`, `provider`, `version`, `packageHash`.

### 2.5 Version

Active binding **MUST** record `version`. Implementations **SHOULD** retain prior bindings for historical evidence.

### 2.6 Switch

Switch updates the active binding to another package (path or provider@version). Subsequent Execute uses the new hash. Historical evidence for the prior hash remains valid.

---

## 3. Active binding file

Default path: `.uap/runtime/active-governance.json`

| Field | Required |
|-------|----------|
| `packageId` | MUST |
| `provider` | MUST |
| `version` | MUST |
| `packageHash` | MUST |
| `source` | MUST (`path` \| `provider` \| `registry` \| `constitution`) |
| `path` | MAY |
| `switchedAt` | MUST |

---

## 4. Portable Governance

Changing the host model vendor (OpenAI → Anthropic → Google) **MUST NOT** alone change `packageHash` or invalidate identity. Only an explicit Switch or package edit changes governance hash.

---

## 5. Conformance

A system is **Constitution-Runtime-conformant** if it implements Load, Execute (authorize), Verify, Audit, Version recording, and Switch with active binding persistence.
