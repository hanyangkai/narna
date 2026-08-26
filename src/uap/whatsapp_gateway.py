"""WhatsApp gateway via Twilio-compatible webhook."""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from typing import Any


def whatsapp_enabled() -> bool:
    return bool(
        os.environ.get("UAP_TWILIO_ACCOUNT_SID", "").strip()
        and os.environ.get("UAP_TWILIO_AUTH_TOKEN", "").strip()
        and os.environ.get("UAP_TWILIO_WHATSAPP_FROM", "").strip()
    )


def send_whatsapp_message(to: str, body: str) -> dict[str, Any]:
    sid = os.environ.get("UAP_TWILIO_ACCOUNT_SID", "").strip()
    token = os.environ.get("UAP_TWILIO_AUTH_TOKEN", "").strip()
    from_wa = os.environ.get("UAP_TWILIO_WHATSAPP_FROM", "").strip()
    if not (sid and token and from_wa):
        raise RuntimeError("Twilio WhatsApp env not set")
    if not to.startswith("whatsapp:"):
        to = f"whatsapp:{to}"
    if not from_wa.startswith("whatsapp:"):
        from_wa = f"whatsapp:{from_wa}"
    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    data = urllib.parse.urlencode(
        {"To": to, "From": from_wa, "Body": body[:1500]}
    ).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    # Basic auth
    import base64

    auth = base64.b64encode(f"{sid}:{token}".encode()).decode()
    req.add_header("Authorization", f"Basic {auth}")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def extract_whatsapp_form(form: dict[str, Any]) -> tuple[str | None, str | None]:
    """Return (from_number, body) from Twilio webhook form fields."""
    frm = str(form.get("From") or "").strip()
    body = str(form.get("Body") or "").strip()
    if not frm or not body:
        return None, None
    return frm, body


def format_agent_reply(out: dict[str, Any]) -> str:
    answer = str(out.get("answer") or "").strip()
    dqs = out.get("dqs")
    guardian = out.get("guardian")
    return (f"{answer}\n\n— ADQA DQS {dqs} · {guardian}")[:1500]
