# Fleet Governance Specification

**Version:** 0.1.0  
**Status:** Draft (C4)  
**Strategy:** [`../../docs/STRATEGY.md`](../../docs/STRATEGY.md)

---

## 1. Purpose

**Fleet Governance** answers: *in an org with hundreds of agents, who may do what?*

```text
Organization
    ↓
Fleet
    ↓
Agents / Tools / MCP Servers (each with Constitution + Identity)
    ↓
Policy overrides · Roles · Audit export
```

---

## 2. Artifact: `fleet.yaml`

```yaml
apiVersion: narna.ai/v1alpha1
kind: Fleet
metadata:
  id: fleet_prod
  orgId: org_acme
  name: Production Fleet
spec:
  members:
    - entityId: agent_research_01
      role: operator
    - entityId: agent_trading_01
      role: restricted
  roles:
    operator:
      can: [run, publish, certify]
    auditor:
      can: [read, export_audit]
    restricted:
      can: [run]
      deny: [wallet.transfer, filesystem.delete]
  defaults:
    minCertification: L2
    requireHumanReview: true
```

---

## 3. Normative rules

1. Fleet membership **MUST** reference Universal Identity `entityId`s.  
2. Role denies **MUST** override agent Constitution allows (deny wins).  
3. `minCertification` **SHOULD** block publish to production Registry if unmet.  
4. Audit export **MUST** include fleetId + orgId on every ProofBundle when governed.
5. Fleet **SHOULD** bind default Governance Packages (`defaults.packages`) that Constitution Runtime Loads for all members.
6. Role denies **MUST** be evaluated during Constitution Runtime Execute (not only CLI inspection).

---

## 4. Conformance

A system is **Fleet-conformant** if it loads `fleet.yaml`, enforces role deny lists, and exports fleet context on certification/passport.
