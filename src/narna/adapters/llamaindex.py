"""narna-llamaindex — Works with LlamaIndex workflows / query engines."""

from __future__ import annotations

from typing import Any

from .base import BaseAdapter


class LlamaIndexAdapter(BaseAdapter):
    id = "llamaindex"
    package = "narna-llamaindex"
    default_unit_kind = "workflow_step"

    def matches(self, obj: Any) -> bool:
        if obj is None:
            return False
        mod = (getattr(type(obj), "__module__", "") or "").lower()
        name = type(obj).__name__.lower()
        blob = f"{mod}.{name}"
        return any(
            x in blob
            for x in (
                "llama_index",
                "llamaindex",
                "queryengine",
                "workflow",
                "retrieverqueryengine",
            )
        )

    def _install_hooks(self, agent: Any, foreign: Any) -> list[str]:
        hooks: list[str] = []
        for method in ("query", "aquery", "run", "arun", "invoke", "chat", "achat"):
            if self._wrap_method(foreign, method, agent):
                hooks.append(method)
        return hooks
