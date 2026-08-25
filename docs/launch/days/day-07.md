# Day 7 — Week-1 retro + pipe score (2026-07-27)

**Theme:** Honest scorecard — what worked, what's still missing, week-2 focus.

## Must ship

- [ ] Fill [`SCORECARD.md`](../SCORECARD.md) pipe score (5 dimensions × 1–5)
- [ ] Ship log `2026-07-27.md` — retro format (see below)
- [ ] Discussion: **Week 1 retro — NARNA pipe score X/25**

## Retro template (ship log)

```markdown
## Week 1 shipped (bullets)
- 

## Pipe score (/25)
| Dimension | Score | Evidence |
|-----------|-------|----------|
| Distribution | | |
| Spec stability | | |
| Integration hook | | |
| Trust network | | |
| Monetization path | | |

## What didn't work
- 

## Week 2 — one focus
- Single integration target: ___
- Ship cadence: 3×/week ship log minimum
```

## By role

### Backend (30 min)

- [ ] Run full verify suite from MVP-CHECKLIST.md
- [ ] Fix top 1 red item if any
- [ ] Tag or note any release needed for week 2

```bash
pip install narna
narna doctor
narna conformance
python -m unittest discover -s tests -p "test_*.py" -q
```

### DevRel (20 min)

- [ ] Compile all 7 ship log links into Discussion retro post
- [ ] Update [`../ship-log/README.md`](../ship-log/README.md) index table
- [ ] Update [`../MVP-CHECKLIST.md`](../MVP-CHECKLIST.md) honest status

### Founder (20 min)

**One-liner (draft):**

> Week 1 NARNA: UGS v0.1 on PyPI, enforce-before adapters, signed Passport verify, 7 days build-in-public. Pipe score X/25 — week 2: [one sentence focus].

- [ ] Post retro thread (canonical on GitHub Discussions)
- [ ] Thank 3 people who engaged
- [ ] Pick week-2 integration partner (LangGraph shop, MCP server author, etc.)

## Success metric

- [ ] Pipe score ≥ 18/25 OR honest gap list with owners
- [ ] 7 ship log files exist (days 0–7)
- [ ] Week-2 single focus written in retro

## After day 7

Continue [`../7-DAY-SYSTEM.md`](../7-DAY-SYSTEM.md) "After day 7" section — 3×/week ship log, one partner outreach.
