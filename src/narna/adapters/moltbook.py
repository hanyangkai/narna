"""narna-moltbook — Works with Moltbook / OpenClaw agent social clients."""

from __future__ import annotations

from typing import Any

from .base import BaseAdapter


class MoltbookAdapter(BaseAdapter):
    id = "moltbook"
    package = "narna-moltbook"

    def matches(self, obj: Any) -> bool:
        if obj is None:
            return False
        mod = (getattr(type(obj), "__module__", "") or "").lower()
        name = type(obj).__name__.lower()
        blob = f"{mod}.{name}"
        return any(
            x in blob
            for x in (
                "moltbook",
                "moltbookclient",
                "openclaw",
                "clawhub",
            )
        )

    def _install_hooks(self, agent: Any, foreign: Any) -> list[str]:
        hooks: list[str] = []
        for method in ("create_post", "reply", "browse_hot", "browse_new", "post", "comment"):
            if self._wrap_method(foreign, method, agent):
                hooks.append(method)
        return hooks
