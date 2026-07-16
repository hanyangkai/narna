# RFC-0010: Rename open standard UAP → UGS

- **Status:** Draft  
- **Authors:** NARNA maintainers  
- **Created:** 2026-07-16  
- **Strategy:** [`../docs/STRATEGY.md`](../docs/STRATEGY.md)

---

## Summary

Rename the public open specification from **UAP** (*Understand → Act → Prove*) to **UGS** (*Universal Governance Specification*).

- **NARNA** = brand + reference governance runtime  
- **UGS** = open standard anyone may implement  
- **VAP** = trust engine (unchanged)

---

## Motivation

UAP named a **workflow**. NARNA is evolving into an **infrastructure / governance standard** (Docker / OTel peer class). Linux Foundation–style adoption needs a clear split between brand and specification.

Alternatives considered: AGS, AIGS. **UGS** best matches “Universal AI Governance Runtime” and “Govern Once. Run Anywhere.”

---

## Detailed design

1. Public docs, website, and STRATEGY use **UGS**.  
2. Spec index (`specs/README.md`) documents UGS as the open standard.  
3. Legacy paths `specs/uap-*`, Python package `uap`, CLI aliases remain until a major version rename.  
4. Compatibility badges may keep `uap-compatible` id with display title “UGS Compatible” in a follow-up (non-breaking).

---

## Compatibility impact

**Never Replace check:** Pass. Naming-only for public surface; no host runtime replacement.

---

## Alternatives

1. Keep UAP forever (workflow name confuses category).  
2. AGS / AIGS (less aligned with “Universal”).  

---

## Unresolved questions

- When to rename Python package `uap` → `ugs` or nest under `narna.ugs`?  
- Badge id migration timeline for `uap-compatible` → `ugs-compatible`?

---

## Implementation plan

1. STRATEGY / BRAND / POSITIONING / website (**this wave**)  
2. Spec README + Architecture  
3. Later: package rename + badge id (semver major)
