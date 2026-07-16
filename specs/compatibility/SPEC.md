# Compatibility Program Specification

**Version:** 0.1.0  
**Status:** Draft  
**Strategy:** [`../../docs/BORROW-THE-WAVE.md`](../../docs/BORROW-THE-WAVE.md)

---

## 1. Purpose

The **NARNA Compatibility Program** issues public badges so projects can signal governance readiness — analogous to “Works with Kubernetes” / OCI Compatible.

| Badge | Code | Meaning |
|-------|------|---------|
| **UAP Compatible** | `uap-compatible` | Ships valid Manifest/Constitution + Identity |
| **Verified by NARNA** | `narna-certified` | Certification ≥ L1 |
| **NARNA Certified+** | `narna-certified-plus` | Certification ≥ L2 |
| **Enterprise Ready** | `enterprise-ready` | Certification = L3 |

---

## 2. Rules

1. Badges **MUST** be earned via deterministic checks (Certification Spec), not marketing claims alone.  
2. Badge SVGs **MAY** be embedded; linking to `/passport/{id}` or `/compatibility` **SHOULD** be preferred.  
3. **Never Replace:** Compatibility does not imply replacing host frameworks.

---

## 3. SVG assets

Reference SVGs live under `web/frontend/public/badges/`.

---

## 4. Program listing

Projects that ship `narna.yaml` and pass L1+ **MAY** be listed on the Compatibility Program page.
