"""Email inbound webhook stub (SendGrid/Mailgun-style parse)."""

from __future__ import annotations

from typing import Any


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


def format_agent_reply(out: dict[str, Any], *, subject: str = "") -> str:
    answer = str(out.get("answer") or "").strip()
    header = f"Re: {subject}\n\n" if subject else ""
    return (header + f"{answer}\n\n— Verified by ADQA · DQS {out.get('dqs')} · {out.get('guardian')}")[
        :8000
    ]
