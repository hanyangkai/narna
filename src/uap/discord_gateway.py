"""Discord gateway — phone/desktop chat surface for Ask NARNA."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


def discord_enabled() -> bool:
    return bool(os.environ.get("UAP_DISCORD_BOT_TOKEN", "").strip())


def _token() -> str:
    return os.environ.get("UAP_DISCORD_BOT_TOKEN", "").strip()


def send_discord_message(channel_id: str, content: str) -> dict[str, Any]:
    token = _token()
    if not token:
        raise RuntimeError("UAP_DISCORD_BOT_TOKEN not set")
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    body = json.dumps({"content": content[:1900]}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bot {token}",
            "Content-Type": "application/json",
            "User-Agent": "NARNA-Agent (https://narna.org, 0.2)",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def extract_discord_message(payload: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    """Return (channel_id, text, author_id) for MESSAGE_CREATE-like payloads.

    Supports:
    - Interactions webhook type 0 style: { t: MESSAGE_CREATE, d: {...} }
    - Direct message object: { channel_id, content, author }
    """
    data = payload.get("d") if isinstance(payload.get("d"), dict) else payload
    if payload.get("t") and payload.get("t") not in {"MESSAGE_CREATE", "MESSAGE_UPDATE"}:
        # Ignore non-message gateway events if wrapped
        if "channel_id" not in data:
            return None, None, None
    channel_id = data.get("channel_id")
    content = (data.get("content") or "").strip()
    author = data.get("author") or {}
    if author.get("bot"):
        return None, None, None
    author_id = author.get("id")
    if not channel_id or not content:
        return None, None, None
    # Ignore slash-empty / attachments-only for v0
    if content.startswith("/"):
        return None, None, None
    return str(channel_id), content, str(author_id) if author_id else None


def format_agent_reply(out: dict[str, Any]) -> str:
    answer = str(out.get("answer") or "").strip()
    dqs = out.get("dqs")
    guardian = out.get("guardian")
    badge = f"\n\n— Verified by ADQA · DQS {dqs} · {guardian}"
    tools = out.get("toolsUsed") or []
    if tools:
        names = ", ".join(sorted({str(t.get("tool")) for t in tools}))
        badge += f"\nTools: {names}"
    return (answer[:1700] + badge)[:1900]
