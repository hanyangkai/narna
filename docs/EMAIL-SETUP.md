# NARNA email (Resend)

Transactional mail: signup API key, magic recovery link, Pro payment receipt.

## Production (current)

- **Provider:** [Resend](https://resend.com) — same account as 99X on VPS
- **From (interim):** `NARNA <noreply@99x.exchange>` (verified)
- **Target:** `NARNA <noreply@narna.org>` after DNS

## VPS setup

```bash
bash /opt/narna/scripts/setup_narna_email.sh
cd /opt/narna/web/deploy/selfhost && docker compose -f docker-compose.vps.yml up -d api
curl -s https://api.narna.org/v1/auth/config | jq .smtpConfigured
# expect true
```

## narna.org DNS (Hostinger)

Add these records at Hostinger → Domains → narna.org → DNS:

| Type | Name | Value | Priority |
|------|------|-------|----------|
| TXT | `resend._domainkey` | *(DKIM from Resend dashboard)* | — |
| MX | `send` | `feedback-smtp.us-east-1.amazonses.com` | 10 |
| TXT | `send` | `v=spf1 include:amazonses.com ~all` | — |

After verification in Resend, set:

```bash
UAP_RESEND_FROM=NARNA <noreply@narna.org>
```

## GitHub Actions (optional)

| Secret | Value |
|--------|-------|
| `RESEND_API_KEY` | Resend API key |
| `UAP_RESEND_FROM` | `NARNA <noreply@narna.org>` |

Deploy workflow patches `/opt/narna/web/deploy/selfhost/.env` automatically.

## Env vars

| Var | Purpose |
|-----|---------|
| `UAP_RESEND_API_KEY` | Resend API key |
| `UAP_RESEND_FROM` | From header |
| `UAP_SITE_URL` | Links in emails (`https://narna.org`) |
| `UAP_SMTP_*` | Optional SMTP fallback |
