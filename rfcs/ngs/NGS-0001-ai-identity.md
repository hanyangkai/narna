# NGS-0001: AI Identity

- **Status:** Accepted  
- **Series:** NARNA Governance Standards  
- **Normative:** [`../../specs/identity/SPEC.md`](../../specs/identity/SPEC.md)  
- **Schema:** [`../../specs/schemas/universal-identity.schema.json`](../../specs/schemas/universal-identity.schema.json)  
- **Alias:** RFC-0001

---

## Abstract

Every autonomous AI entity MUST have a portable identity record: who/what it is, who owns it, and a content hash that survives model-vendor switches.

## Minimum fields

```yaml
identityId: ...
entityId: ...
kind: Agent | Tool | McpServer | Workflow | ...
owner: ...
organization: ...
version: ...
publicKey: ...   # optional Ed25519
contentHash: sha256:...
```

## Normative rules

1. Identity is **not** permission.  
2. Identity is **not** capability.  
3. Switching LLM vendor MUST NOT alone mint a new identity.  
4. Conformant systems MUST validate against `universal-identity.schema.json`.

## Conformance

A system is **NGS-0001 conformant** if it issues and persists Universal Identity records offline-first.
