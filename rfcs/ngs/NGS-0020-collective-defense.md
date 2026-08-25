# NGS-0020: Collective AI Defense Network

- **Status:** Active (runtime v0)  
- **Product:** [`../../docs/GUARDIAN.md`](../../docs/GUARDIAN.md)  
- **Spec:** [`../../specs/collective-defense/SPEC.md`](../../specs/collective-defense/SPEC.md)

## Abstract

Cross-organization sharing of privacy-preserving **Threat Signatures** (antivirus model for agent behavior). Detect in one org → restrict similar agents elsewhere.

## Normative intent

1. Signatures MUST NOT include raw secrets or personal data (HMAC / k-anon as in telemetry SPEC).  
2. Opt-in at org level (extends telemetry consent).  
3. Receiving a signature MUST allow automatic Capability restrict — not silent ignore under Guardian profile.  
4. False-positive appeal path SHOULD exist (human council).

## Runtime v0

- `CollectiveDefense` store under `.uap/guardian/collective/`
- CLI: `narna collective opt-in|publish|import|list|match|apply`
- API: `/v1/guardian/collective/*`
- Apply writes capability restriction overlay + optional local kill
