# 7-Day Communication & Ship System

**NARNA wedge (repeat every day):** UGS · Governance Packages · GU · enforce-before adapters

**Time budget:** 45–75 min/day total. Skip filler days — no proof = no post.

---

## Roles

| Role | Who | Daily time | Responsibility |
|------|-----|------------|----------------|
| **Founder** | You | 15 min | One-liner post, 3 replies, 1 outbound DM/email |
| **Backend** | You / eng | 30–45 min | One shippable artifact (fix, endpoint, test, deploy) |
| **DevRel** | You | 15 min | Ship log file, Discussion post, update scorecard |

> Solo founder? Run all three blocks in sequence. Order: Backend → DevRel → Founder.

---

## Daily rhythm (same every day)

```
09:00  Backend   — pick ONE item from today's day file → ship + proof command
10:00  DevRel    — write ship-log/YYYY-MM-DD.md, commit, open Discussion
10:15  Founder   — copy One-liner → X/LinkedIn + pin Discussion link
EOD    Founder   — reply to 3 threads (GitHub, X, or LinkedIn)
```

### Commit message format

```
ship-log: YYYY-MM-DD — <short title>
```

### Discussion post format

Title: `Ship log YYYY-MM-DD — <title>`

Body:

```markdown
**Shipped:** <1–2 bullets>
**Proof:** <curl or link>
**Try it:** pip install narna · narna.org
**Wedge:** UGS + Packages + GU (not agent-passport clone)
```

---

## Rules

1. **Proof or skip** — every post needs a runnable command, URL, or screenshot.
2. **Lead with wedge** — UGS spec, Packages, GU metering; passport is one feature, not the brand.
3. **One theme per day** — see [`days/`](./days/).
4. **No duplicate channels** — same one-liner everywhere; link back to GitHub Discussion (canonical).
5. **Track metrics** — update [`SCORECARD.md`](./SCORECARD.md) EOD.

---

## Week-1 outcomes (definition of done)

| Metric | Target |
|--------|--------|
| Ship log entries | 7 (incl. day 0) |
| GitHub Discussions (Ship log) | ≥5 posts |
| PyPI install verified | `pip install narna` from clean venv |
| Conformance CLI demo | `narna conformance` green on fresh init |
| Adapter e2e | ≥1 screenshot or CI link shared |
| Passport verify live | `signatureValid: true` on demo agent |
| Outbound touches | ≥10 (DM, email, comment on related repos) |
| Paddle | ticket open OR checkout enabled |

---

## Pipe readiness score (end of day 7)

Rate 1–5 each; target **≥18/25** to call week 1 a success.

| Dimension | 1 | 5 |
|-----------|---|---|
| **Distribution** | source-only | `pip install` + docs + Discussion |
| **Spec stability** | draft | UGS v0.1 tagged + conformance |
| **Integration hook** | observe-only | enforce-before + e2e proof |
| **Trust network** | local only | public verify API + signed demo |
| **Monetization path** | none | Paddle ready or explicit blocker doc |

Record scores in [`SCORECARD.md`](./SCORECARD.md) on day 7.

---

## Escalation

| Blocker | Action |
|---------|--------|
| Paddle `transaction_checkout_not_enabled` | Email Paddle support; document in ship log; ship log mentions "Cloud waitlist" CTA |
| No engagement on Discussions | Comment on 3 related issues (LangGraph, MCP, OTel governance threads) |
| Nothing to ship | Run `narna doctor` + fix highest-severity item; still counts if merged |

---

## After day 7

- Publish retro in Discussion: "Week 1 — pipe score X/25"
- Extend ship log cadence (3×/week minimum)
- Pick **one** integration partner outreach for week 2
