"""Signal webhook stub (e.g. signal-cli / rest bridge)."""

from __future__ import annotations

import os
from typing import Any


def signal_enabled() -> bool:
    return bool(os.environ.get("UAP_SIGNAL_WEBHOOK_URL", "").strip())


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


def format_agent_reply(out: dict[str, Any]) -> str:
    answer = str(out.get("answer") or "").strip()
    return (f"{answer}\n\n— ADQA DQS {out.get('dqs')} · {out.get('guardian')}")[:3500]
