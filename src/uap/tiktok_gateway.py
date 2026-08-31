"""TikTok gateway — webhook stub (Business API messaging when enabled)."""

from __future__ import annotations

import os
from typing import Any


def tiktok_enabled() -> bool:
    return bool(
        os.environ.get("UAP_TIKTOK_CLIENT_KEY", "").strip()
        and os.environ.get("UAP_TIKTOK_CLIENT_SECRET", "").strip()
        and os.environ.get("UAP_TIKTOK_MESSAGING_ENABLED", "").strip().lower()
        in {"1", "true", "yes", "on"}
    )


def extract_tiktok_message(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    user = str(payload.get("open_id") or payload.get("user_id") or "").strip()
    text = str(payload.get("text") or payload.get("content") or "").strip()
    if user and text:
        return user, text
    return None, None


def send_tiktok_message(user_id: str, text: str) -> dict[str, Any]:
    if not tiktok_enabled():
        raise RuntimeError("TikTok messaging not enabled — set UAP_TIKTOK_MESSAGING_ENABLED=1")
    return {"ok": False, "error": "TikTok outbound not wired — webhook ingest only", "to": user_id}


def format_agent_reply(out: dict[str, Any]) -> str:
    return str(out.get("answer") or "")[:500]
