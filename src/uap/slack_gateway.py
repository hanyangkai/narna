"""Slack Events API gateway for Ask NARNA."""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Any


def slack_enabled() -> bool:
    return bool(os.environ.get("UAP_SLACK_BOT_TOKEN", "").strip())


def _token() -> str:
    return os.environ.get("UAP_SLACK_BOT_TOKEN", "").strip()


def send_slack_message(channel: str, text: str) -> dict[str, Any]:
    token = _token()
    if not token:
        raise RuntimeError("UAP_SLACK_BOT_TOKEN not set")
    url = "https://slack.com/api/chat.postMessage"
    body = json.dumps({"channel": channel, "text": text[:3500]}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def extract_slack_event(payload: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    """Return (channel, text, user) from Slack Events API payload."""
    if payload.get("type") == "url_verification":
        return None, None, None
    event = payload.get("event") or {}
    if event.get("bot_id") or event.get("subtype") in {"bot_message", "message_changed"}:
        return None, None, None
    if event.get("type") != "message":
        return None, None, None
    channel = event.get("channel")
    text = (event.get("text") or "").strip()
    user = event.get("user")
    if not channel or not text:
        return None, None, None
    return str(channel), text, str(user) if user else None


def format_agent_reply(out: dict[str, Any]) -> str:
    answer = str(out.get("answer") or "").strip()
    dqs = out.get("dqs")
    guardian = out.get("guardian")
    badge = f"\n\n_Verified by ADQA · DQS {dqs} · {guardian}_"
    tools = out.get("toolsUsed") or []
    if tools:
        names = ", ".join(sorted({str(t.get("tool")) for t in tools}))
        badge += f"\nTools: `{names}`"
    return (answer[:3000] + badge)[:3500]
