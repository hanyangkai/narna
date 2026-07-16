# NARNA Cloud (private)

Private repository for **NARNA Cloud** production ops:

- Production env files (never in public repo)
- Coolify / VPS deploy notes with real secrets placeholders
- Stripe / RPC keys runbooks
- Internal incident & billing ops

## Public counterpart

OSS + MIT: [narna-ai/narna](https://github.com/narna-ai/narna)

```text
Public  → Spec, SDK, CLI, docs, self-host compose (MIT)
Private → Production secrets, ops, billing runbooks
```

## Setup

1. Copy `../narna/web/deploy/selfhost/.env.production.example` → `.env` (this repo)
2. Fill Stripe, RPC, wallet, DB passwords
3. Deploy: `bash deploy.sh` (see public `docs/SELF-HOST.md`)

## Rule

**Never** commit live API keys, wallet private keys, or customer data here without encryption / vault.
