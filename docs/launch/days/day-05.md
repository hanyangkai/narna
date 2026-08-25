# Day 5 — Trust layer / UGS Passport (2026-07-25)

**Theme:** Cryptographic trust — verify without trusting our marketing.

## Must ship (pick one backend item)

- [ ] Confirm `curl .../v1/passport/narna-demo-agent/verify` → `signatureValid: true`
- [ ] Passport page on narna.org shows verify status
- [ ] Fix if signature broken after deploy

## By role

### Backend (30 min)

```bash
curl -sS https://api.narna.org/v1/passport/narna-demo-agent/verify
curl -sS https://api.narna.org/v1/passport/narna-demo-agent
```

Verify live site: https://narna.org/passport/narna-demo-agent

### DevRel (15 min)

- [ ] Ship log `2026-07-25.md`
- [ ] Discussion: **Ship log 2026-07-25 — UGS Passport verify API**
- [ ] Frame as "one feature of UGS", not the whole product

### Founder (15 min)

**One-liner (draft):**

> UGS Passport: signed agent identity + capabilities + package binding. Verify publicly — no account needed. `curl api.narna.org/v1/passport/narna-demo-agent/verify`

- [ ] Post one-liner + verify JSON snippet
- [ ] Compare briefly to "passport-only" clones (link DIFFERENTIATION)
- [ ] 1 outbound to security / platform team

## Proof block

```bash
curl -sS https://api.narna.org/v1/passport/narna-demo-agent/verify
# signatureValid: true
```

## Success metric

- [ ] Live verify returns signatureValid true
- [ ] Passport page loads on narna.org
- [ ] Discussion explains passport ⊂ UGS (not passport = NARNA)

## Tomorrow preview

Day 6: Cloud + GU — metering story and Paddle status (honest blocker doc).
