# Capability Passport Specification

**Version:** 0.1.0-draft  
**Status:** Draft (Guardian Layer 2)  
**Series:** NGS-0015  
**Companions:** [`../schemas/capability-passport.schema.json`](../schemas/capability-passport.schema.json) · [`../../docs/GUARDIAN.md`](../../docs/GUARDIAN.md)  
**Builds on:** NGS-0001 Identity · NGS-0002 Capability · NGS-0003 Permission · NGS-0007 Passport

---

## 1. Purpose

A **Capability Passport** binds an agent identity to **action privileges with modes** — like an OS process privilege table.

It answers: *what may this agent attempt, under what isolation and approval?*

Declaring a coarse capability (NGS-0002) remains discovery-only.  
**Capability Passport is the grant surface for Guardian profiles.**

---

## 2. Modes

| Mode | Meaning |
|------|---------|
| `allow` | Permitted under normal policy |
| `ask` | Human / council approval required |
| `sandbox` | Only inside Agent Container isolation |
| `whitelist` | Only listed targets (hosts, tools, APIs) |
| `restricted` | Deny by default; explicit council grant |
| `multisig` | N-of-M human approvals |
| `deny` | Hard deny |

Deny **wins** over allow when composed.

---

## 3. Envelope

```yaml
apiVersion: narna.ai/v1alpha1
kind: CapabilityPassport
metadata:
  agentId: agent_legal_01
  version: "1.0.0"
spec:
  grants:
    - capability: filesystem
      mode: allow
      constraints: { paths: ["/workspace/docs"] }
    - capability: email
      mode: ask
    - capability: terminal
      mode: sandbox
    - capability: create.agent
      mode: restricted
    - capability: trade
      mode: multisig
      approvalsRequired: 2
  quotas:
    maxSpawnDepth: 1
    maxApiCallsPerHour: 100
    maxGuPerDay: 10000
  isolation:
    network: deny-by-default
    filesystem: workspace-only
```

---

## 4. Evaluate

`CapabilityGovernor.evaluate(agentId, capability, context)` MUST return:

| Field | Description |
|-------|-------------|
| `decision` | allow \| ask \| sandbox \| whitelist \| restricted \| multisig \| deny |
| `reasons` | Why |
| `requiredApprovals` | If ask/multisig |
| `quotas` | Remaining / limits |
| `isolation` | Required container constraints |

Adapters in Guardian profile **MUST** call this **before** host side-effects (same timing as enforce-before).

---

## 5. Non-goals (v0)

- Full VM/container orchestration (host concern)  
- Automatic discovery of novel dangerous capabilities  
- Global kill (NGS-0019)
