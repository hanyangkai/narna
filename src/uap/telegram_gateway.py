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


def send_telegram_voice(chat_id: int | str, audio_path: str, *, caption: str = "") -> dict[str, Any]:
    """Send a voice note via Telegram sendVoice (multipart)."""
    import mimetypes
    from pathlib import Path

    token = _token()
    if not token:
        raise RuntimeError("UAP_TELEGRAM_BOT_TOKEN not set")
    path = Path(audio_path)
    if not path.is_file():
        raise FileNotFoundError(f"audio not found: {audio_path}")
    boundary = "----narnaVoiceBoundary7MA4YWxkTrZu0gW"
    raw = path.read_bytes()
    filename = path.name
    ctype = mimetypes.guess_type(filename)[0] or "audio/mpeg"
    parts: list[bytes] = []

    def _field(name: str, value: str) -> None:
        parts.append(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
                f"{value}\r\n"
            ).encode("utf-8")
        )

    _field("chat_id", str(chat_id))
    if caption:
        _field("caption", caption[:1024])
    parts.append(
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="voice"; filename="{filename}"\r\n'
            f"Content-Type: {ctype}\r\n\r\n"
        ).encode("utf-8")
    )
    parts.append(raw)
    parts.append(f"\r\n--{boundary}--\r\n".encode("utf-8"))
    body = b"".join(parts)
    url = f"https://api.telegram.org/bot{token}/sendVoice"
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def build_telegram_voice_payload(chat_id: int | str, filename: str, *, caption: str = "") -> dict[str, Any]:
    """Shape used by tests / dry-run without hitting Telegram."""
    return {
        "method": "sendVoice",
        "chat_id": str(chat_id),
        "filename": filename,
        "caption": (caption or "")[:1024],
    }


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
