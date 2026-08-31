"""WhatsApp gateway — Meta Cloud API (native) + Twilio fallback."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


def whatsapp_cloud_enabled() -> bool:
    return bool(
        os.environ.get("UAP_WHATSAPP_TOKEN", "").strip()
        and os.environ.get("UAP_WHATSAPP_PHONE_NUMBER_ID", "").strip()
    )


def whatsapp_twilio_enabled() -> bool:
    return bool(
        os.environ.get("UAP_TWILIO_ACCOUNT_SID", "").strip()
        and os.environ.get("UAP_TWILIO_AUTH_TOKEN", "").strip()
        and os.environ.get("UAP_TWILIO_WHATSAPP_FROM", "").strip()
    )


def whatsapp_enabled() -> bool:
    return whatsapp_cloud_enabled() or whatsapp_twilio_enabled()


def whatsapp_backend() -> str:
    if whatsapp_cloud_enabled():
        return "cloud"
    if whatsapp_twilio_enabled():
        return "twilio"
    return "off"


def send_whatsapp_message(to: str, body: str) -> dict[str, Any]:
    if whatsapp_cloud_enabled():
        return _send_cloud(to, body)
    return _send_twilio(to, body)


def _send_cloud(to: str, body: str) -> dict[str, Any]:
    token = os.environ.get("UAP_WHATSAPP_TOKEN", "").strip()
    phone_id = os.environ.get("UAP_WHATSAPP_PHONE_NUMBER_ID", "").strip()
    ver = (os.environ.get("UAP_WHATSAPP_GRAPH_VERSION") or "v21.0").strip()
    to_digits = to.replace("whatsapp:", "").replace("+", "").replace(" ", "").strip()
    url = f"https://graph.facebook.com/{ver}/{phone_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to_digits,
        "type": "text",
        "text": {"body": body[:1500]},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "narna-agent/0.2",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"WhatsApp Cloud HTTP {e.code}: {detail}") from e


def _send_twilio(to: str, body: str) -> dict[str, Any]:
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


def extract_whatsapp_cloud(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    """Return (from_number, body) from Meta Cloud API webhook JSON."""
    try:
        entries = payload.get("entry") or []
        for entry in entries:
            for change in entry.get("changes") or []:
                value = change.get("value") or {}
                for msg in value.get("messages") or []:
                    if msg.get("type") != "text":
                        continue
                    frm = str(msg.get("from") or "").strip()
                    text = str((msg.get("text") or {}).get("body") or "").strip()
                    if frm and text:
                        return frm, text
    except Exception:
        pass
    return None, None


def format_agent_reply(out: dict[str, Any]) -> str:
    answer = str(out.get("answer") or "").strip()
    dqs = out.get("dqs")
    guardian = out.get("guardian")
    return (f"{answer}\n\n— ADQA DQS {dqs} · {guardian}")[:1500]
