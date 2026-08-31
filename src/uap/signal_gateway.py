"""Signal webhook + outbound via signal-cli / rest bridge."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


def signal_enabled() -> bool:
    return bool(os.environ.get("UAP_SIGNAL_WEBHOOK_URL", "").strip()) or bool(
        os.environ.get("UAP_SIGNAL_SEND_URL", "").strip()
    )


def extract_signal_message(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    """Return (sender, text) from common signal-cli JSON shapes."""
    envelope = payload.get("envelope") or payload
    data = envelope.get("dataMessage") or payload.get("dataMessage") or {}
    text = (data.get("message") or payload.get("message") or payload.get("text") or "").strip()
    sender = (
        envelope.get("sourceNumber")
        or envelope.get("source")
        or payload.get("from")
        or payload.get("sender")
    )
    if not text or not sender:
        return None, None
    return str(sender), text


def send_signal_message(to: str, text: str) -> dict[str, Any]:
    """POST to signal-cli-rest-api or custom bridge.

    Env:
      UAP_SIGNAL_SEND_URL — e.g. http://127.0.0.1:8080/v2/send
      UAP_SIGNAL_NUMBER — sender number (optional)
    """
    url = (
        os.environ.get("UAP_SIGNAL_SEND_URL")
        or os.environ.get("UAP_SIGNAL_WEBHOOK_URL")
        or ""
    ).strip()
    if not url:
        raise RuntimeError("UAP_SIGNAL_SEND_URL not set")
    number = (os.environ.get("UAP_SIGNAL_NUMBER") or "").strip()
    body: dict[str, Any] = {
        "message": text[:3500],
        "text": text[:3500],
        "number": number or None,
        "recipients": [to],
        "recipient": to,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps({k: v for k, v in body.items() if v is not None}).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "narna-agent/0.2"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            data = json.loads(raw) if raw.strip() else {"ok": True}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:400]
        return {"ok": False, "error": f"Signal HTTP {e.code}: {detail}", "to": to}
    except Exception as e:
        return {"ok": False, "error": str(e), "to": to}
    return {"ok": True, "to": to, "response": data, "backend": "signal"}


def format_agent_reply(out: dict[str, Any]) -> str:
    answer = str(out.get("answer") or "").strip()
    return (f"{answer}\n\n— ADQA DQS {out.get('dqs')} · {out.get('guardian')}")[:3500]
