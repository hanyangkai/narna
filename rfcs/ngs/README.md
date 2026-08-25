# NARNA Governance Standards (NGS)

**Status:** Active  
**Date:** 2026-07-17  
**Brand:** NARNA = reference implementation · **UGS** = Universal Governance Specification · **NGS** = numbered standard RFCs (IETF-style)

> NARNA does not own the agent stack. NGS defines how Agentic AI is **identified, governed, evidenced, and trusted** — so any framework can implement the contracts.

---

## Core six (lock first)

| NGS | Title | Normative SPEC | Status |
|-----|-------|----------------|--------|
| [NGS-0001](./NGS-0001-ai-identity.md) | AI Identity | [`../../specs/identity/SPEC.md`](../../specs/identity/SPEC.md) | Accepted |
| [NGS-0002](./NGS-0002-capability.md) | Capability Specification | [`../../specs/capability/SPEC.md`](../../specs/capability/SPEC.md) | Accepted (v0) |
| [NGS-0003](./NGS-0003-permission.md) | Permission Model | [`../../specs/permission/SPEC.md`](../../specs/permission/SPEC.md) | Accepted |
| [NGS-0004](./NGS-0004-policy.md) | Policy Specification | [`../../specs/policy/SPEC.md`](../../specs/policy/SPEC.md) | Accepted (v0) |
| [NGS-0005](./NGS-0005-evidence.md) | Evidence Format | [`../../specs/uap-evidence/SPEC.md`](../../specs/uap-evidence/SPEC.md) | Accepted |
| [NGS-0006](./NGS-0006-trust-score.md) | Trust Score Model | [`../../specs/vap/SPEC.md`](../../specs/vap/SPEC.md) §6 | Accepted |

Derived standards (Passport, Package, Certification, Manifest, Registry, Governance API) **MUST** compose these six — they MUST NOT invent parallel identity/permission semantics.

---

## Derived standards

| NGS | Title | Normative |
|-----|-------|-----------|
| [NGS-0007](./NGS-0007-passport.md) | AI Passport | [`../../specs/passport/SPEC.md`](../../specs/passport/SPEC.md) |
| [NGS-0008](./NGS-0008-governance-package.md) | Governance Package | [`../../specs/governance-package/SPEC.md`](../../specs/governance-package/SPEC.md) |
| [NGS-0009](./NGS-0009-certification.md) | Certification | [`../../specs/certification/SPEC.md`](../../specs/certification/SPEC.md) |
| [NGS-0010](./NGS-0010-audit-report.md) | Audit Report | [`../../specs/audit/SPEC.md`](../../specs/audit/SPEC.md) |
| [NGS-0011](./NGS-0011-manifest.md) | Governance Manifest (`narna.yaml`) | [`../../specs/manifest/SPEC.md`](../../specs/manifest/SPEC.md) |
| [NGS-0012](./NGS-0012-registry.md) | Governance Registry | [`../../specs/registry/SPEC.md`](../../specs/registry/SPEC.md) |
| [NGS-0013](./NGS-0013-governance-api.md) | Governance API | [`../../specs/governance-api/SPEC.md`](../../specs/governance-api/SPEC.md) |
| [NGS-0014](./NGS-0014-decision-package.md) | Decision Package (Decision OS) | [`../../specs/decision-package/SPEC.md`](../../specs/decision-package/SPEC.md) |
| [NGS-0015](./NGS-0015-capability-passport.md) | Capability Passport (Guardian) | [`../../specs/capability-passport/SPEC.md`](../../specs/capability-passport/SPEC.md) |
| [NGS-0016](./NGS-0016-agent-container.md) | Agent Container | [`../../docs/GUARDIAN.md`](../../docs/GUARDIAN.md) |
| [NGS-0017](./NGS-0017-behavioral-threat.md) | Behavioral Threat Engine | [`../../docs/GUARDIAN.md`](../../docs/GUARDIAN.md) |
| [NGS-0018](./NGS-0018-agent-reputation.md) | Agent Reputation | [`../../docs/GUARDIAN.md`](../../docs/GUARDIAN.md) |
| [NGS-0019](./NGS-0019-emergency-kill.md) | Emergency Kill | [`../../docs/GUARDIAN.md`](../../docs/GUARDIAN.md) |
| [NGS-0020](./NGS-0020-collective-defense.md) | Collective Defense Network | [`../../docs/GUARDIAN.md`](../../docs/GUARDIAN.md) |
| [NGS-0021](./NGS-0021-ai-gateway.md) | AI Gateway (Citizen) | [`../../specs/ai-gateway/SPEC.md`](../../specs/ai-gateway/SPEC.md) |
| [NGS-0022](./NGS-0022-citizen-profile.md) | Citizen Profile | [`../../specs/citizen-profile/SPEC.md`](../../specs/citizen-profile/SPEC.md) |
| [NGS-0023](./NGS-0023-universal-ai-passport.md) | Universal AI Passport (Consumer) | [`../../specs/universal-ai-passport/SPEC.md`](../../specs/universal-ai-passport/SPEC.md) |
| [NGS-0024](./NGS-0024-adqa.md) | Autonomous Decision Quality Assurance | [`../../specs/adqa/SPEC.md`](../../specs/adqa/SPEC.md) |
| [NGS-0025](./NGS-0025-decision-memory.md) | Decision Memory + Outcome Learning | [`../../specs/decision-memory/SPEC.md`](../../specs/decision-memory/SPEC.md) |
| [NGS-0026](./NGS-0026-outcome-learning.md) | Outcome Learning | [`../../specs/outcome-learning/SPEC.md`](../../specs/outcome-learning/SPEC.md) |
| [NGS-0027](./NGS-0027-dqs-network.md) | DQS Network (multi-org priors) | [`../../src/uap/dqs_network.py`](../../src/uap/dqs_network.py) |
| [NGS-0028](./NGS-0028-model-router.md) | Model Router | [`../../specs/model-router/SPEC.md`](../../specs/model-router/SPEC.md) |
| [NGS-0029](./NGS-0029-narna-agent.md) | NARNA Agent Runtime | [`../../specs/narna-agent/SPEC.md`](../../specs/narna-agent/SPEC.md) |

---

## Relation to legacy RFC-000x

| Legacy | Maps to |
|--------|---------|
| RFC-0001 Universal AI Identity | NGS-0001 |
| RFC-0002 Permission Manifest | NGS-0003 |
| RFC-0003 Agent Passport | NGS-0007 |
| RFC-0004 NARNA Score | Brand composite (0–100) — **not** NGS-0006; see Trust Score note in NGS-0006 |
| RFC-0005 `narna.yaml` | NGS-0011 |
| RFC-0007 Governance Package | NGS-0008 |
| RFC-0008 Constitution Runtime | Runtime (implements NGS-0003/0004) |
| RFC-0011 Session / EU / GU | Metering plane (orthogonal to core six) |

Legacy `RFC-000x` files remain for history. **New normative work cites NGS ids.**

---

## Design law

1. Spec before code  
2. Deny by default  
3. Evidence over eloquence  
4. Identity ≠ permission ≠ capability  
5. Never replace host frameworks — adapters only  
6. Open standard (UGS/NGS) separate from brand (NARNA)
