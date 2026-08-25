# Day 2 — UGS conformance (2026-07-22)

**Theme:** UGS v0.1 is frozen and checkable — "open standard" with teeth.

## Must ship (pick one backend item)

- [ ] Run `narna conformance` on fresh project; document output in ship log
- [ ] Add conformance section to README or `specs/RELEASE-v0.1.md` if thin
- [ ] CI badge or link to green `cloud-ci` run on main

## By role

### Backend (30 min)

```bash
narna init --name ConformanceDemo
narna conformance
narna validate
```

Ensure checks pass: OpenAPI, schemas, `narna.yaml`, runtime init.

### DevRel (15 min)

- [ ] Ship log `2026-07-22.md`
- [ ] Discussion: **Ship log 2026-07-22 — UGS v0.1 conformance**
- [ ] Comment on 1 issue/PR mentioning "governance standard" or "AI Act compliance"

### Founder (15 min)

**One-liner (draft):**

> UGS v0.1 isn't a PDF — run `narna conformance` to verify OpenAPI, schemas, and manifest on your project. Govern Once. Run Anywhere.

- [ ] Post one-liner
- [ ] Link `specs/RELEASE-v0.1.md` and tag `ugs-v0.1.0`
- [ ] 1 outbound: post in a compliance / platform engineering community

## Proof block

```bash
narna conformance
# expect all checks PASS
```

## Success metric

- [ ] Conformance green on fresh init
- [ ] Spec release linked from Discussion
- [ ] 3 outbound replies total for week ≥ 4

## Tomorrow preview

Day 3: Adapter e2e — enforce-before blocks a bad tool call (MCP HIPAA deny).
