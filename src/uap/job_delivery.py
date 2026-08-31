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
    deliver_audio: bool | None = None,
    audio_path: str | None = None,
) -> dict[str, Any]:
    """Send job Ask result to telegram|discord|slack|email when deliver_to is set."""
    ch = (channel or "job").lower().strip()
    target = (deliver_to or "").strip()
    if not target or ch in {"job", "web", ""}:
        return {"ok": True, "delivered": False, "reason": "no deliverTo"}

    text = format_job_reply(out, job_id=job_id)
    want_audio = deliver_audio
    if want_audio is None:
        want_audio = str(os.environ.get("UAP_JOB_DELIVER_AUDIO") or "").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
    if want_audio is False and out.get("deliverAudio") is True:
        want_audio = True
    path = audio_path or str(out.get("audioPath") or "").strip() or None

    try:
        if ch == "telegram":
            from .telegram_gateway import send_telegram_message, send_telegram_voice

            if want_audio and path:
                send_telegram_voice(target, path, caption=text[:200])
                return {
                    "ok": True,
                    "delivered": True,
                    "channel": ch,
                    "to": target,
                    "audio": True,
                }
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
        if ch == "whatsapp":
            from .whatsapp_gateway import send_whatsapp_message

            send_whatsapp_message(target, text)
            return {"ok": True, "delivered": True, "channel": ch, "to": target}
        if ch == "x":
            from .x_gateway import deliver_x_reply

            deliver_x_reply(to=target, text=text)
            return {"ok": True, "delivered": True, "channel": ch, "to": target}
        if ch in {"facebook", "fb", "messenger"}:
            from .facebook_gateway import send_facebook_message

            send_facebook_message(target, text)
            return {"ok": True, "delivered": True, "channel": "facebook", "to": target}
        if ch == "youtube":
            from .youtube_gateway import reply_youtube_comment

            reply_youtube_comment(target, text)
            return {"ok": True, "delivered": True, "channel": ch, "to": target}
        if ch == "instagram":
            from .instagram_gateway import send_instagram_message

            send_instagram_message(target, text)
            return {"ok": True, "delivered": True, "channel": ch, "to": target}
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
