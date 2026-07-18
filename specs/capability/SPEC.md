# Capability Specification — UGS / NGS-0002

**Status:** Normative (v0.1)  
**RFC:** [NGS-0002](../../rfcs/ngs/NGS-0002-capability.md)  
**Schema:** [`../schemas/capability.schema.json`](../schemas/capability.schema.json)

---

## 1. Definition

A **Capability** is a coarse class of agent ability used for discovery, marketplace indexing, and high-level policy matching.

Declaring a capability **MUST NOT** grant permission to act (see NGS-0003).

---

## 2. Naming

| Rule | Requirement |
|------|-------------|
| Pattern | `^[a-z][a-z0-9_]*$` for core names |
| Vendor extensions | `^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$` |
| Case | lowercase only |

---

## 3. Core vocabulary (v0)

| Capability | Description |
|------------|-------------|
| `browser` | Navigate / fetch web pages |
| `filesystem` | Read/write local or mounted files |
| `wallet` | Crypto or payment wallets |
| `github` | Source control / PR operations |
| `terminal` | Shell / process execution |
| `email` | Send/read email |
| `search` | Web or corpus search |
| `trade` | Market orders / brokerage |
| `code` | Code generation / analysis |
| `ocr` | Document / image text extraction |
| `memory` | Long-term memory stores |
| `mcp` | MCP tool hosts |

This table is the **v0 registry**. New core names require an NGS amendment.

---

## 4. Declaration

Agents / Constitutions declare capabilities as string arrays. Tools SHOULD set `capability` on their definition.

```yaml
capability:
  - browser
  - search
```

---

## 5. Conformance

1. Unknown capabilities MAY be stored but MUST NOT imply permissions.  
2. Policy MAY match on capability for coarse denies; fine-grained control remains Permission.
