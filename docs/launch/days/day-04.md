# Day 4 — Governance Packages (2026-07-24)

**Theme:** Portable compliance rules — the moat is Packages, not passports.

## Must ship (pick one backend item)

- [ ] Demo `ConstitutionRuntime().load(provider="eu-ai-act")` in ship log
- [ ] Screenshot of package marketplace on narna.org/packages (or API list)
- [ ] Document one package rule (what it blocks/allows)

## By role

### Backend (30 min)

```python
from narna import ConstitutionRuntime

rt = ConstitutionRuntime()
rt.load(provider="eu-ai-act")
# run validate or show active package in manifest
```

```bash
curl -sS "https://api.narna.org/v1/packages?limit=3"
```

### DevRel (15 min)

- [ ] Ship log `2026-07-24.md`
- [ ] Discussion: **Ship log 2026-07-24 — Governance Packages**
- [ ] Contrast line: "Not identity-only — portable YAML compliance"

### Founder (15 min)

**One-liner (draft):**

> Load EU AI Act / HIPAA / GDPR as Governance Packages — one YAML bundle, enforce across LangGraph, OpenAI, MCP. That's the NARNA wedge: UGS + Packages + GU.

- [ ] Post one-liner
- [ ] Link `docs/DIFFERENTIATION.md`
- [ ] 1 outbound to compliance-minded contact

## Proof block

```bash
narna init --name PkgDemo
# ensure narna.yaml references eu-ai-act@2.0.0
narna validate
curl -sS https://api.narna.org/v1/packages?limit=3
```

## Success metric

- [ ] Package load + validate green
- [ ] Differentiation doc linked
- [ ] Marketplace or API proof in ship log

## Tomorrow preview

Day 5: UGS Passport — public verify API, signed demo agent.
