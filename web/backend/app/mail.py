"""Transactional email for signup, recovery, and payment (SMTP — no Stripe)."""

from __future__ import annotations

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger("narna-mail")


def smtp_configured() -> bool:
    return bool(os.environ.get("UAP_SMTP_HOST", "").strip())


def site_url() -> str:
    return os.environ.get("UAP_SITE_URL", "https://narna.org").rstrip("/")


def _send(to: str, subject: str, text: str, html: str | None = None) -> bool:
    host = os.environ.get("UAP_SMTP_HOST", "").strip()
    if not host:
        logger.info("smtp skip (not configured)", extra={"to": to, "subject": subject})
        return False
    port = int(os.environ.get("UAP_SMTP_PORT") or 587)
    user = os.environ.get("UAP_SMTP_USER", "").strip()
    password = os.environ.get("UAP_SMTP_PASSWORD", "").strip()
    from_addr = os.environ.get("UAP_SMTP_FROM", "").strip() or user or "noreply@narna.org"

    if html:
        msg = MIMEMultipart("alternative")
        msg.attach(MIMEText(text, "plain", "utf-8"))
        msg.attach(MIMEText(html, "html", "utf-8"))
    else:
        msg = MIMEText(text, "plain", "utf-8")

    msg["Subject"] = subject[:200]
    msg["From"] = from_addr
    msg["To"] = to

    try:
        use_ssl = str(os.environ.get("UAP_SMTP_SSL") or "").lower() in {"1", "true", "yes"}
        if use_ssl:
            with smtplib.SMTP_SSL(host, port, timeout=30) as smtp:
                if user and password:
                    smtp.login(user, password)
                smtp.sendmail(from_addr, [to], msg.as_string())
        else:
            with smtplib.SMTP(host, port, timeout=30) as smtp:
                smtp.ehlo()
                if str(os.environ.get("UAP_SMTP_STARTTLS") or "1").lower() in {
                    "1",
                    "true",
                    "yes",
                    "on",
                }:
                    try:
                        smtp.starttls()
                    except Exception:
                        pass
                if user and password:
                    smtp.login(user, password)
                smtp.sendmail(from_addr, [to], msg.as_string())
        return True
    except Exception:
        logger.exception("smtp send failed", extra={"to": to})
        return False


def send_welcome_email(*, to: str, api_key: str, name: str) -> bool:
    base = site_url()
    text = f"""Welcome to NARNA Cloud, {name}!

Your API key (save it — shown once on the website too):

{api_key}

Use it for:
- Ask: {base}/ask
- Pro upgrade (USDC/USDT): {base}/checkout
- Billing: {base}/billing
- MCP: {base}/docs/integrations

Lost your key? Request a new one: {base}/account

— NARNA
"""
    html = f"""<p>Welcome to NARNA Cloud, <strong>{name}</strong>!</p>
<p>Your API key (save it):</p>
<pre style="background:#041018;color:#a5f3fc;padding:12px;border-radius:8px;word-break:break-all">{api_key}</pre>
<p><a href="{base}/checkout">Upgrade Pro ($20/mo)</a> · <a href="{base}/ask">Open Ask</a></p>
<p>Lost your key? <a href="{base}/account">Email recovery</a></p>"""
    return _send(to, "Your NARNA Cloud API key", text, html)


def send_recovery_email(*, to: str, token: str) -> bool:
    base = site_url()
    link = f"{base}/account/recover?token={token}"
    text = f"""NARNA Cloud — sign-in link

Open this link to get a fresh API key (valid 1 hour, one-time use):

{link}

If you didn't request this, ignore this email.

— NARNA
"""
    html = f"""<p>Click to sign in and get your API key:</p>
<p><a href="{link}" style="display:inline-block;padding:12px 20px;background:#0e7490;color:#fff;border-radius:8px;text-decoration:none">Open NARNA Account</a></p>
<p style="color:#666;font-size:12px">Link expires in 1 hour. One-time use.</p>"""
    return _send(to, "Your NARNA sign-in link", text, html)


def send_payment_confirmed_email(
    *,
    to: str,
    plan: str,
    amount: str,
    asset: str,
    network: str,
    expires_at: str | None,
) -> bool:
    base = site_url()
    text = f"""Payment received — NARNA Pro active

Plan: {plan}
Amount: {amount} {asset.upper()} on {network}
Active until: {expires_at or '30 days'}

Open Ask: {base}/ask
Billing: {base}/billing

— NARNA
"""
    html = f"""<p><strong>Payment received</strong> — NARNA Pro is active.</p>
<ul><li>Plan: {plan}</li><li>{amount} {asset.upper()} on {network}</li></ul>
<p><a href="{base}/ask">Open Ask</a> · <a href="{base}/billing">Billing</a></p>"""
    return _send(to, "NARNA Pro — payment confirmed", text, html)
