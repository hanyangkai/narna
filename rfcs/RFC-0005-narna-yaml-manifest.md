# RFC-0005: Manifest `narna.yaml`

- **Status:** Draft  
- **Authors:** NARNA maintainers  
- **Created:** 2026-07-16  
- **Normative:** [`../specs/manifest/SPEC.md`](../specs/manifest/SPEC.md)

---

## Summary

Introduce `narna.yaml` as the default developer metadata file (Dockerfile / action.yml analog). Short-form Manifest compiles to full Constitution.

---

## Motivation

**Borrow the Wave / Default Metadata:** if every agent eventually ships `narna.yaml`, NARNA wins on metadata gravity — not SDK feature count.

---

## Detailed design

See Manifest Spec. Discovery order: `narna.yaml` → `.narna/narna.yaml` → `constitution.yaml`.

Compilation maps capabilities, permissions, policy aliases, trust.minimum_score → Constitution.

---

## Compatibility impact

**Never Replace check:** Pass. Does not replace MCP manifests, Dockerfiles, or AgentSpecs — composes with them. Host frameworks remain unchanged.

---

## Alternatives

1. Only `constitution.yaml` (harder DX).  
2. Embed metadata only in Passport (not author-time).  

---

## Unresolved questions

- Should `narna.yaml` be valid inside MCP server directories by convention?  
- Multi-document manifests for fleets?  

---

## Implementation plan

1. Schema + compiler in reference SDK (**this PR wave**)  
2. `wrap` / `Agent` auto-discover  
3. Compatibility Program badge for “ships narna.yaml”
