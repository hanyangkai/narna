# Day 1 — Install path live (2026-07-21)

**Theme:** Prove `pip install narna` works for a stranger in <5 minutes.

## Must ship (pick one backend item)

- [ ] Fresh venv test: `pip install narna && narna init --name smoke && narna doctor`
- [ ] Fix any doctor failure from clean install
- [ ] Add `docs/INSTALL.md` "5-minute quickstart" if missing steps

## By role

### Backend (30 min)

```powershell
python -m venv .venv-smoke
.\.venv-smoke\Scripts\python -m pip install narna
.\.venv-smoke\Scripts\narna init --name SmokeTest
.\.venv-smoke\Scripts\narna doctor
.\.venv-smoke\Scripts\narna validate
```

Record output. If red → fix and redeploy docs only (no scope creep).

### DevRel (15 min)

- [ ] Create `docs/ship-log/2026-07-21.md` from template
- [ ] Open Discussion: **Ship log 2026-07-21 — pip install narna**
- [ ] Link INSTALL.md quickstart in Discussion body

### Founder (15 min)

**One-liner (draft):**

> NARNA is on PyPI: `pip install narna` → `narna init` → enforce-before governance in 5 min. Open UGS v0.1. narna.org

- [ ] Post one-liner on X or LinkedIn
- [ ] Reply to 3 posts about agent governance / LangGraph / MCP
- [ ] 1 outbound: share install link with 1 builder you know

## Proof block (paste in ship log)

```bash
pip install narna==0.1.0
narna init --name Demo
narna doctor
```

## Success metric

- [ ] Clean venv install green
- [ ] 1 Discussion post live
- [ ] Scorecard day 1 ticked

## Tomorrow preview

Day 2: `narna conformance` — show UGS v0.1 is a real standard, not marketing.
