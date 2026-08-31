"""Email inbound webhook + SMTP reply."""

from __future__ import annotations

import os
import smtplib
from email.mime.text import MIMEText
from typing import Any


def email_enabled() -> bool:
    return bool(os.environ.get("UAP_SMTP_HOST", "").strip())


def extract_email_message(form_or_json: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    """Return (from_addr, subject, text)."""
    frm = str(
        form_or_json.get("from")
        or form_or_json.get("From")
        or form_or_json.get("sender")
        or ""
    ).strip()
    subject = str(form_or_json.get("subject") or form_or_json.get("Subject") or "").strip()
    text = str(
        form_or_json.get("text")
        or form_or_json.get("plain")
        or form_or_json.get("body-plain")
        or form_or_json.get("stripped-text")
        or ""
    ).strip()
    if not frm or not text:
        return None, None, None
    return frm, subject, text


def send_email_reply(to: str, body: str, *, subject: str = "NARNA") -> dict[str, Any]:
    host = os.environ.get("UAP_SMTP_HOST", "").strip()
    if not host:
        raise RuntimeError("UAP_SMTP_HOST not set")
    port = int(os.environ.get("UAP_SMTP_PORT") or 587)
    user = os.environ.get("UAP_SMTP_USER", "").strip()
    password = os.environ.get("UAP_SMTP_PASSWORD", "").strip()
    from_addr = os.environ.get("UAP_SMTP_FROM", "").strip() or user
    if not from_addr:
        raise RuntimeError("UAP_SMTP_FROM or UAP_SMTP_USER required")
    msg = MIMEText(body[:8000], "plain", "utf-8")
    msg["Subject"] = subject[:200]
    msg["From"] = from_addr
    msg["To"] = to
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
    return {"ok": True, "to": to, "backend": "smtp"}


def format_agent_reply(out: dict[str, Any], *, subject: str = "") -> str:
    answer = str(out.get("answer") or "").strip()
    header = f"Re: {subject}\n\n" if subject else ""
    return (header + f"{answer}\n\n— Verified by ADQA · DQS {out.get('dqs')} · {out.get('guardian')}")[
        :8000
    ]
