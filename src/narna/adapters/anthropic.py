"""narna-anthropic — Works with Anthropic / Claude SDK patterns."""

from __future__ import annotations

from typing import Any

from .base import BaseAdapter


class AnthropicAdapter(BaseAdapter):
    id = "anthropic"
    package = "narna-anthropic"

    def matches(self, obj: Any) -> bool:
        if obj is None:
            return False
        mod = (getattr(type(obj), "__module__", "") or "").lower()
        name = type(obj).__name__.lower()
        blob = f"{mod}.{name}"
        return any(
            x in blob
            for x in (
                "anthropic",
                "claude",
                "messages",
                "anthropic.resources",
            )
        )

    def _install_hooks(self, agent: Any, foreign: Any) -> list[str]:
        hooks: list[str] = []
        for method in ("create", "stream", "parse", "run", "invoke", "__call__"):
            if self._wrap_method(foreign, method, agent):
                hooks.append(method)
        # client.messages.create nesting
        messages = getattr(foreign, "messages", None)
        if messages is not None and self._wrap_method(messages, "create", agent):
            hooks.append("messages.create")
        if messages is not None and self._wrap_method(messages, "stream", agent):
            hooks.append("messages.stream")
        return hooks
