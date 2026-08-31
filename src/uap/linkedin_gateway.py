"""LinkedIn gateway — webhook stub (Messaging API partner program)."""

from __future__ import annotations

import os
from typing import Any


def linkedin_enabled() -> bool:
    return bool(os.environ.get("UAP_LINKEDIN_ACCESS_TOKEN", "").strip())


def extract_linkedin_message(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    sender = str(payload.get("senderUrn") or payload.get("from") or "").strip()
    text = str(payload.get("text") or payload.get("body") or "").strip()
    if sender and text:
        return sender, text
    return None, None


def send_linkedin_message(recipient: str, text: str) -> dict[str, Any]:
    if not linkedin_enabled():
        raise RuntimeError("UAP_LINKEDIN_ACCESS_TOKEN not set")
    return {"ok": False, "error": "LinkedIn outbound stub — configure partner webhook relay", "to": recipient}


def format_agent_reply(out: dict[str, Any]) -> str:
    return str(out.get("answer") or "")[:3000]
