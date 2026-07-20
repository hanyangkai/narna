"""narna-openai — Works with OpenAI Agents SDK / OpenAI client patterns."""

from __future__ import annotations

from typing import Any

from .base import AdapterResult, BaseAdapter


class OpenAIAdapter(BaseAdapter):
    id = "openai"
    package = "narna-openai"
    default_unit_kind = "llm"

    def matches(self, obj: Any) -> bool:
        if obj is None:
            return False
        mod = (getattr(type(obj), "__module__", "") or "").lower()
        name = type(obj).__name__.lower()
        blob = f"{mod}.{name}"
        return any(
            x in blob
            for x in (
                "openai",
                "agents.agent",
                "agents.run",
                "openai.agents",
                "chatcompletions",
                "responses",
            )
        )

    def _install_hooks(self, agent: Any, foreign: Any) -> list[str]:
        hooks: list[str] = []
        for method in ("run", "invoke", "ainvoke", "create", "__call__"):
            if self._wrap_method(foreign, method, agent):
                hooks.append(method)
        # OpenAI client.chat.completions.create nesting
        chat = getattr(foreign, "chat", None)
        comps = getattr(chat, "completions", None) if chat is not None else None
        if comps is not None and self._wrap_method(comps, "create", agent):
            hooks.append("chat.completions.create")
        return hooks
