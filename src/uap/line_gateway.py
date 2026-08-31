"""LINE Messaging API gateway (APAC)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


def line_enabled() -> bool:
    return bool(os.environ.get("UAP_LINE_CHANNEL_ACCESS_TOKEN", "").strip())


def extract_line_message(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    for event in payload.get("events") or []:
        if event.get("type") != "message":
            continue
        msg = event.get("message") or {}
        if msg.get("type") != "text":
            continue
        text = str(msg.get("text") or "").strip()
        source = event.get("source") or {}
        user = str(source.get("userId") or source.get("groupId") or "").strip()
        if user and text:
            return user, text
    # Flat relay
    user = str(payload.get("userId") or payload.get("from") or "").strip()
    text = str(payload.get("text") or payload.get("message") or "").strip()
    if user and text:
        return user, text
    return None, None


def send_line_message(user_id: str, text: str) -> dict[str, Any]:
    token = os.environ.get("UAP_LINE_CHANNEL_ACCESS_TOKEN", "").strip()
    if not token:
        raise RuntimeError("UAP_LINE_CHANNEL_ACCESS_TOKEN not set")
    url = "https://api.line.me/v2/bot/message/push"
    body = json.dumps(
        {
            "to": user_id,
            "messages": [{"type": "text", "text": text[:5000]}],
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "NARNA-Agent (https://narna.org, 0.2)",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return {"ok": True, "response": json.loads(raw) if raw.strip() else {}, "to": user_id}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:400]
        return {"ok": False, "error": f"LINE HTTP {e.code}: {detail}", "to": user_id}


def format_agent_reply(out: dict[str, Any]) -> str:
    answer = str(out.get("answer") or "").strip()
    return (f"{answer}\n\n— ADQA DQS {out.get('dqs')} · {out.get('guardian')}")[:5000]
