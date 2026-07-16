"""Example NARNA plugin entrypoint — extend, never replace."""

from __future__ import annotations

from typing import Any


def register(agent: Any) -> dict[str, Any]:
    """Called by host to attach plugin capabilities."""
    return {
        "ok": True,
        "plugin": "narna-example",
        "message": "Works with NARNA Agent. Add your integration here.",
    }
