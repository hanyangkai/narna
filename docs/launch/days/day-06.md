# Day 6 — Cloud + GU metering (2026-07-26)

**Theme:** Runtime free, Trust metered — show the business model without hiding Paddle blocker.

## Must ship (pick one backend item)

- [ ] Document GU model in ship log (1 paragraph + link BUSINESS-MODEL.md)
- [ ] `curl api.narna.org/v1/billing/paddle/status` — record response
- [ ] If Paddle still blocked: add "Cloud waitlist" CTA or email capture (optional)

## By role

### Backend (30 min)

```bash
curl -sS https://api.narna.org/v1/health
curl -sS "https://api.narna.org/v1/billing/paddle/status?live_probe=0"
# document transaction_checkout_not_enabled honestly if still blocked
```

Review `docs/PADDLE-SETUP.md` — any env gaps on VPS?

### DevRel (15 min)

- [ ] Ship log `2026-07-26.md`
- [ ] Discussion: **Ship log 2026-07-26 — GU metering + Cloud path**
- [ ] Link `docs/BUSINESS-MODEL.md` and `docs/PADDLE-SETUP.md`

### Founder (15 min)

**One-liner (draft):**

> NARNA OSS runtime is free. Cloud meters Trust in Governance Units (GU): Registry, Passport, Package verification. TaaS wedge — integrate the pipe, pay for scale.

- [ ] Post one-liner
- [ ] If Paddle blocked: "Checkout coming — OSS + API live today"
- [ ] Email Paddle support if no ticket yet (counts as outbound)

## Proof block

```bash
curl -sS https://api.narna.org/v1/health
curl -sS https://api.narna.org/v1/billing/paddle/status
```

## Success metric

- [ ] GU story published with link
- [ ] Paddle status documented (enabled OR explicit blocker + next step)
- [ ] BUSINESS-MODEL.md linked from Discussion

## Tomorrow preview

Day 7: Week-1 retro — pipe score /25, week-2 plan.
