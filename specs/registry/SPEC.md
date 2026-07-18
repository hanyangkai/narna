# Governance Registry — UGS / NGS-0012

**Status:** Normative (v0.1)  
**RFC:** [NGS-0012](../../rfcs/ngs/NGS-0012-registry.md)  
**Ops:** [`../../docs/REGISTRY-PROD.md`](../../docs/REGISTRY-PROD.md)

---

## 1. Purpose

A **Governance Registry** is the discovery and verification plane for:

```text
Agent → Passport → Policy Pack → Governance Package → Certification
```

Like Docker Hub for images — but for governance artifacts.

---

## 2. Resource kinds

| Kind | Id field | Notes |
|------|----------|-------|
| Agent | `agentId` | NGS-0001 identity link |
| Passport | `agentId` | NGS-0007 view |
| Package | `packageId` | NGS-0008 |
| Plugin | `pluginId` | Community adapters |
| Certification | `agentId` + level | NGS-0009 |

---

## 3. Normative operations

| Op | Requirement |
|----|-------------|
| Publish | Authenticated; content-addressed hash recorded |
| Get | Public read for public artifacts |
| Verify | Passport / package hash check |
| Star / trending | MAY | Social signals |

URI scheme (informative): `registry://{host}/{kind}/{id}@{version}`

---

## 4. Offline-first

Local `.uap/registry` MUST work without network. Remote sync is optional (NARNA Cloud).

---

## 5. Non-goals

Runtime execution, model hosting, billing amounts (commercial layer).
