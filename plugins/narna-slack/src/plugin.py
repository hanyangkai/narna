"""narna-slack — notify Slack without replacing your agent runtime."""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Any


def register(agent: Any) -> dict[str, Any]:
    agent._plugins = getattr(agent, "_plugins", {})
    agent._plugins["slack"] = {"notify": notify}
    return {"ok": True, "plugin": "narna-slack"}


def notify(text: str, *, webhook_url: str | None = None) -> dict[str, Any]:
    url = webhook_url or os.environ.get("NARNA_SLACK_WEBHOOK", "")
    if not url:
        return {"ok": False, "error": "set NARNA_SLACK_WEBHOOK or pass webhook_url"}
    req = urllib.request.Request(
        url,
        data=json.dumps({"text": text}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return {"ok": True, "status": resp.status}
