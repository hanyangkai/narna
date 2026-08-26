"""Deliver scheduled Ask results to messaging channels (Hermes cron fan-out)."""

from __future__ import annotations

import os
import smtplib
from email.mime.text import MIMEText
from typing import Any


def format_job_reply(out: dict[str, Any], *, job_id: str = "") -> str:
    answer = str(out.get("answer") or "").strip()
    dqs = out.get("dqs")
    badge = f"\n\n— NARNA job {job_id} · ADQA DQS {dqs}"
    return (answer[:3500] + badge)[:4000]


def deliver_job_result(
    *,
    channel: str,
    deliver_to: str | None,
    out: dict[str, Any],
    job_id: str = "",
) -> dict[str, Any]:
    """Send job Ask result to telegram|discord|slack|email when deliver_to is set."""
    ch = (channel or "job").lower().strip()
    target = (deliver_to or "").strip()
    if not target or ch in {"job", "web", ""}:
        return {"ok": True, "delivered": False, "reason": "no deliverTo"}

    text = format_job_reply(out, job_id=job_id)
    try:
        if ch == "telegram":
            from .telegram_gateway import send_telegram_message

            send_telegram_message(target, text)
            return {"ok": True, "delivered": True, "channel": ch, "to": target}
        if ch == "discord":
            from .discord_gateway import send_discord_message

            send_discord_message(target, text)
            return {"ok": True, "delivered": True, "channel": ch, "to": target}
        if ch == "slack":
            from .slack_gateway import send_slack_message

            send_slack_message(target, text)
            return {"ok": True, "delivered": True, "channel": ch, "to": target}
        if ch == "email":
            return _send_email(target, text, job_id=job_id)
        return {"ok": False, "delivered": False, "error": f"unsupported channel: {ch}"}
    except Exception as e:
        return {"ok": False, "delivered": False, "error": str(e), "channel": ch, "to": target}


def _send_email(to_addr: str, body: str, *, job_id: str) -> dict[str, Any]:
    host = os.environ.get("UAP_SMTP_HOST", "").strip()
    user = os.environ.get("UAP_SMTP_USER", "").strip()
    password = os.environ.get("UAP_SMTP_PASSWORD", "").strip()
    from_addr = os.environ.get("UAP_SMTP_FROM", user or "noreply@narna.org")
    if not host:
        return {"ok": False, "delivered": False, "error": "UAP_SMTP_HOST not set"}
    port = int(os.environ.get("UAP_SMTP_PORT") or 587)
    msg = MIMEText(body)
    msg["Subject"] = f"NARNA job {job_id}"
    msg["From"] = from_addr
    msg["To"] = to_addr
    with smtplib.SMTP(host, port, timeout=30) as smtp:
        smtp.starttls()
        if user and password:
            smtp.login(user, password)
        smtp.sendmail(from_addr, [to_addr], msg.as_string())
    return {"ok": True, "delivered": True, "channel": "email", "to": to_addr}
