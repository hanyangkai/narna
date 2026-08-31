"""LinkedIn gateway — webhook ingest + Messaging API outbound (partner / BYOK)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


def linkedin_enabled() -> bool:
    return bool(os.environ.get("UAP_LINKEDIN_ACCESS_TOKEN", "").strip())


def extract_linkedin_message(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    sender = str(
        payload.get("senderUrn")
        or payload.get("from")
        or payload.get("actor")
        or ""
    ).strip()
    text = str(payload.get("text") or payload.get("body") or payload.get("message") or "").strip()
    elements = payload.get("elements") or payload.get("messages") or []
    if (not sender or not text) and isinstance(elements, list) and elements:
        first = elements[0] if isinstance(elements[0], dict) else {}
        sender = sender or str(first.get("from") or first.get("senderUrn") or "").strip()
        text = text or str(first.get("text") or first.get("body") or "").strip()
    if sender and text:
        return sender, text
    return None, None


def send_linkedin_message(recipient: str, text: str) -> dict[str, Any]:
    token = os.environ.get("UAP_LINKEDIN_ACCESS_TOKEN", "").strip()
    if not token:
        raise RuntimeError("UAP_LINKEDIN_ACCESS_TOKEN not set")
    relay = (os.environ.get("UAP_LINKEDIN_SEND_URL") or "").strip()
    base = (os.environ.get("UAP_LINKEDIN_API_BASE") or "https://api.linkedin.com").rstrip("/")
    url = relay or f"{base}/v2/messages"
    body = json.dumps(
        {
            "recipients": [recipient],
            "subject": "NARNA",
            "body": text[:3000],
            "messageType": "MEMBER_TO_MEMBER",
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
            "User-Agent": "NARNA-Agent (https://narna.org, 0.2)",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            data = json.loads(raw) if raw.strip() else {"ok": True}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:400]
        return {"ok": False, "error": f"LinkedIn HTTP {e.code}: {detail}", "to": recipient}
    except Exception as e:
        return {"ok": False, "error": str(e), "to": recipient}
    return {"ok": True, "to": recipient, "response": data, "backend": "linkedin"}


def format_agent_reply(out: dict[str, Any]) -> str:
    answer = str(out.get("answer") or "").strip()
    dqs = out.get("dqs")
    guardian = out.get("guardian")
    return (f"{answer}\n\n— ADQA DQS {dqs} · {guardian}")[:3000]
