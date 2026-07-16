# Universal AI Identity Specification

**Version:** 0.1.0  
**Status:** Draft (C1)  
**Normative companions:** [`../schemas/universal-identity.schema.json`](../schemas/universal-identity.schema.json)  
**Strategy:** [`../../docs/STRATEGY.md`](../../docs/STRATEGY.md)  
**Related:** [`../constitution/SPEC.md`](../constitution/SPEC.md)

---

## 1. Purpose

**Universal AI Identity** is a portable birth record for *any* autonomous AI entity — not only agents.

Today each framework invents its own id. NARNA defines one shape:

```yaml
id:
owner:
version:
kind:
origin:
license:
contentHash:
signature:
```

Identity answers: **who is this?**  
Constitution answers: **what may it do?**  
Passport answers: **why trust it now?**

---

## 2. Entity kinds

| `kind` | Examples |
|--------|----------|
| `Agent` | Research bot, trading agent |
| `Tool` | Browser tool, SQL tool |
| `McpServer` | MCP server process |
| `Workflow` | LangGraph / CrewAI graph |
| `Prompt` | System prompt pack |
| `Dataset` | RAG / training corpus binding |
| `Plugin` | `narna-*` plugin |
| `Memory` | Memory adapter / store |
| `ModelBinding` | Declared model slot (not weights) |

A conformant system **MUST** be able to issue identity for at least `Agent`, and **SHOULD** support the full table.

---

## 3. Normative fields

| Field | Required | Description |
|-------|----------|-------------|
| `identityId` | MUST | Stable id of this identity record (`idnt_…`) |
| `entityId` | MUST | Stable id of the entity (`agent_…`, `tool_…`, …) |
| `kind` | MUST | One of §2 |
| `owner` | MUST | Creator / org (DID, org id, …) |
| `version` | MUST | Semver of the entity charter/content |
| `createdAt` | MUST | RFC3339 |
| `contentHash` | MUST | `sha256:…` of canonical constitution or binding document |
| `origin` | SHOULD | Repo URI / registry URL |
| `license` | SHOULD | SPDX or URL |
| `constitutionId` | SHOULD | Id of governing Constitution |
| `signature` | MUST | Ed25519 (or listed alg) over canonical payload |
| `supersedes` | MAY | Previous `entityId` on rotation |
| `labels` | MAY | Free-form string map |

**Backward compatibility:** Agent-only identities using UAP `identity.schema.json` (`agentId`, `creator`, `specHash`) remain valid. New issuers **SHOULD** emit Universal Identity and **MAY** dual-write Agent fields (`agentId` = `entityId` when `kind=Agent`).

---

## 4. Portable Trust rule

Changing the underlying model vendor or agent framework **MUST NOT** alone require a new `entityId`.

Identity rotates only when the charter / content intentionally changes (new `contentHash` + version bump), or when `supersedes` is used for a deliberate re-birth.

---

## 5. Relation to Constitution & Passport

```text
Universal Identity  ←── who
        ↓
Constitution        ←── may / must
        ↓
Evidence + VAP
        ↓
Passport            ←── cites identity + constitutionId/hash
```

A Passport **SHOULD** include:

- `constitution.constitutionId`
- `constitution.constitutionHash`

when a Constitution is present.

---

## 6. Example

See [`../examples/universal-identity.json`](../examples/universal-identity.json).

---

## 7. Conformance

1. Issue schema-valid Universal Identity for `Agent`.  
2. Persist identity immutably (append-only or content-addressed).  
3. Do not recycle `entityId` for a different charter without `supersedes`.  
4. Passport issued after Constitution load **SHOULD** cite constitution id + hash.
