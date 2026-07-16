# RFC-0001: Universal AI Identity

- **Status:** Accepted / Implemented (C1)  
- **Authors:** NARNA maintainers  
- **Created:** 2026-07-16  
- **Normative:** [`../specs/identity/SPEC.md`](../specs/identity/SPEC.md)

---

## Summary

Define a portable identity record for *every* autonomous AI entity — Agent, Tool, MCP Server, Workflow, Prompt, Dataset, Plugin, Memory, ModelBinding — not only agents.

---

## Motivation

Today each framework invents its own IDs. Portable Trust requires a stable `entityId` that survives model-vendor switches.

---

## Detailed design

See Universal Identity Spec. Key fields: `identityId`, `entityId`, `kind`, `owner`, `version`, `contentHash`, `signature`, optional `constitutionId`.

---

## Compatibility impact

**Never Replace check:** Pass. Identity sits above OpenAI/LangGraph/MCP; adapters may mint or link IDs without replacing host object models.

---

## Alternatives

1. Agent-only identity (rejected — too narrow).  
2. Rely solely on cloud registry IDs (rejected — not offline-first).

---

## Unresolved questions

- Cross-org DID resolution  
- Key rotation UX for hobbyists  

---

## Implementation

Landed in `src/uap/identity.py` (`issue_entity`) and Constitution / Passport citation path.
