"""iMessage bridge via BlueBubbles / Beeper-style HTTP webhook."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


def imessage_enabled() -> bool:
    return bool(
        (
            os.environ.get("UAP_BLUEBUBBLES_URL")
            or os.environ.get("UAP_IMESSAGE_WEBHOOK_URL")
            or ""
        ).strip()
    )


def extract_imessage(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    data = payload.get("data") or payload
    if not isinstance(data, dict):
        data = payload
    frm = str(
        data.get("handle")
        or data.get("chatGuid")
        or data.get("from")
        or data.get("address")
        or payload.get("from")
        or ""
    ).strip()
    text = str(
        data.get("text")
        or data.get("message")
        or data.get("body")
        or payload.get("text")
        or ""
    ).strip()
    if frm and text:
        return frm, text
    return None, None


def send_imessage(to: str, text: str) -> dict[str, Any]:
    base = (
        os.environ.get("UAP_BLUEBUBBLES_URL")
        or os.environ.get("UAP_IMESSAGE_WEBHOOK_URL")
        or ""
    ).strip().rstrip("/")
    if not base:
        raise RuntimeError("UAP_BLUEBUBBLES_URL not set")
    password = (
        os.environ.get("UAP_BLUEBUBBLES_PASSWORD")
        or os.environ.get("UAP_IMESSAGE_PASSWORD")
        or ""
    ).strip()
    # BlueBubbles: POST /api/v1/message/text
    url = base if base.endswith("/message/text") or base.endswith("/send") else f"{base}/api/v1/message/text"
    body = json.dumps({"chatGuid": to, "address": to, "message": text[:4000], "text": text[:4000]}).encode(
        "utf-8"
    )
    headers = {"Content-Type": "application/json", "User-Agent": "narna-agent/0.2"}
    if password:
        headers["Authorization"] = f"Bearer {password}"
        # BlueBubbles often uses ?password=
        if "?" not in url:
            url = f"{url}?password={password}"
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            data = json.loads(raw) if raw.strip() else {"ok": True}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:400]
        return {"ok": False, "error": f"iMessage HTTP {e.code}: {detail}", "to": to}
    except Exception as e:
        return {"ok": False, "error": str(e), "to": to}
    return {"ok": True, "to": to, "response": data, "backend": "imessage"}


def format_agent_reply(out: dict[str, Any]) -> str:
    answer = str(out.get("answer") or "").strip()
    return (f"{answer}\n\n— ADQA DQS {out.get('dqs')} · {out.get('guardian')}")[:4000]
