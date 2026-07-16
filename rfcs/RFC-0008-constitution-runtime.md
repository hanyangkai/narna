# RFC-0008: Constitution Runtime

- **Status:** Draft  
- **Authors:** NARNA maintainers  
- **Created:** 2026-07-16  
- **Normative:** [`../specs/constitution-runtime/SPEC.md`](../specs/constitution-runtime/SPEC.md)  
- **Strategy:** [`../docs/STRATEGY.md`](../docs/STRATEGY.md)

---

## Summary

Define **Constitution Runtime** as the core NARNA loop for Governance Packages:

```text
Load → Execute → Verify → Audit → Version → Switch
```

This is **not** an agent/model execution runtime. It is the governance enforcement + proof loop that sits above OpenAI / Claude / Gemini / LangGraph via `wrap()`.

---

## Motivation

Today Constitution is declared and certified against, but runtime authorize still leans on AgentSpec + policy packs. Portable Governance requires a single loop that:

1. **Loads** a package (path, provider@version, or registry ref)  
2. **Executes** (authorize) using package rules + fleet denies  
3. **Verifies** evidence / proof against package requirements  
4. **Audits** runs with packageId + packageHash  
5. **Versions** tracks package revisions  
6. **Switches** active binding without rewriting agent code  

---

## Detailed design

### Active binding

Workspace file `.uap/runtime/active-governance.json`:

```json
{
  "packageId": "pkg_eu_ai_act_v1",
  "provider": "eu-ai-act",
  "version": "1.0.0",
  "packageHash": "sha256:…",
  "source": "path|provider|registry",
  "switchedAt": "RFC3339"
}
```

### Execute

On tool/capability authorize, Constitution Runtime **MUST** evaluate:

1. Active package `rules` / embedded Constitution `policy.rules`  
2. Fleet role denies (deny wins)  
3. Existing PolicyEngine / AgentSpec permissions (compose; deny wins)

### Verify / Audit

ProofBundle and audit export **MUST** cite `packageId` + `packageHash`.

### Switch

`switch(provider, version | path)` updates active binding; next run uses new hash. Prior evidence remains valid for historical packageHash.

### Portable Governance

Same `entityId` + packageHash across vendor wrap (OpenAI → Anthropic) **MUST** remain valid.

---

## Compatibility impact

**Never Replace check:** Pass. Reference UAP executor remains optional. Host frameworks unchanged; Runtime only extends authorize/evidence.

---

## Alternatives

1. Keep policy packs only (no unified Runtime API).  
2. Build a full agent OS (violates Borrow-the-Wave).  

---

## Unresolved questions

- Hot-reload mid-run vs bound-at-run-start? (v0: bound at run start)  
- Compose multiple packages in one Execute?  

---

## Implementation plan

1. Spec  
2. `src/uap/governance_runtime.py`  
3. Wire `LocalRuntime` authorize path  
4. CLI `narna governance load|switch|verify|audit|list`
