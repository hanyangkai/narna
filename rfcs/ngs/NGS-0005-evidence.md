# NGS-0005: Evidence Format

- **Status:** Accepted  
- **Series:** NARNA Governance Standards  
- **Normative:** [`../../specs/uap-evidence/SPEC.md`](../../specs/uap-evidence/SPEC.md)  
- **Schema:** [`../../specs/schemas/evidence.schema.json`](../../specs/schemas/evidence.schema.json)

---

## Abstract

Evidence is the hashed, typed proof that an action occurred — not LLM narrative.

## Minimum fields

```yaml
evidenceId: ...
type: api_response | receipt | approval | screenshot | ...
contentHash: sha256:...
capturedAt: ...
provenance:
  agentId: ...
  runId: ...
  parentEventId: ...
```

## Normative rules

1. Claims without evidence MUST NOT increase Trust Score.  
2. Evidence MUST be verifiable offline when blobs are available.  
3. Irreversible actions SHOULD attach receipt evidence.  
4. Extensions MUST register a type string (see Evidence SPEC type table).

## Conformance

Hash-addressed evidence + VAP verify pipeline.
