# UGS v0.1 — Release notes

**Status:** Released  
**Version:** 0.1.0  
**Date:** 2026-07-20

## What is frozen

- Core six: Identity, Capability, Permission, Policy, Evidence, Trust (NGS-0001…0006)
- Manifest (`narna.yaml`), Passport, Governance Package, Certification, Audit, Registry, Governance API (NGS-0007…0013)
- JSON Schemas under `specs/schemas/`
- OpenAPI draft: `specs/governance-api/openapi.yaml`

## Compatibility

- Reference implementation: NARNA Python SDK / CLI (`narna` package)
- Adapter SPI: enforce-before host framework calls (`NARNA_ADAPTER_MODE=enforce`)

## Not frozen yet

- Governance Telemetry (Draft G1)
- Billing / marketplace take-rate commercial terms (product, not standard)

## Conformance

```bash
narna conformance --workspace .
```

Badge: **UGS Conformant** when OpenAPI schemas + manifest + runtime probe pass.
