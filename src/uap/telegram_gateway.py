"""Telegram gateway — run Ask NARNA from a phone chat."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


def telegram_enabled() -> bool:
    return bool(os.environ.get("UAP_TELEGRAM_BOT_TOKEN", "").strip())


def _token() -> str:
    return os.environ.get("UAP_TELEGRAM_BOT_TOKEN", "").strip()


def send_telegram_message(chat_id: int | str, text: str) -> dict[str, Any]:
    token = _token()
    if not token:
        raise RuntimeError("UAP_TELEGRAM_BOT_TOKEN not set")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    body = json.dumps(
        {
            "chat_id": chat_id,
            "text": text[:4000],
            "disable_web_page_preview": True,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def extract_telegram_text(update: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    """Return (chat_id, text, username)."""
    msg = update.get("message") or update.get("edited_message") or {}
    chat = msg.get("chat") or {}
    chat_id = chat.get("id")
    text = msg.get("text") or msg.get("caption")
    user = (msg.get("from") or {}).get("username")
    if chat_id is None or not text:
        return None, None, None
    return str(chat_id), str(text), str(user) if user else None


def format_agent_reply(out: dict[str, Any]) -> str:
    answer = str(out.get("answer") or "").strip()
    dqs = out.get("dqs")
    guardian = out.get("guardian")
    badge = f"\n\n— Verified by ADQA · DQS {dqs} · {guardian}"
    tools = out.get("toolsUsed") or []
    if tools:
        names = ", ".join(sorted({str(t.get("tool")) for t in tools}))
        badge += f"\nTools: {names}"
    return (answer[:3500] + badge)[:4000]
