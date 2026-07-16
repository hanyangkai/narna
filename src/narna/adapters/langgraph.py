"""narna-langgraph — Works with LangGraph compiled graphs."""

from __future__ import annotations

from typing import Any

from .base import BaseAdapter


class LangGraphAdapter(BaseAdapter):
    id = "langgraph"
    package = "narna-langgraph"

    def matches(self, obj: Any) -> bool:
        if obj is None:
            return False
        mod = (getattr(type(obj), "__module__", "") or "").lower()
        name = type(obj).__name__.lower()
        return "langgraph" in mod or "compiledstategraph" in name or "stategraph" in name

    def _install_hooks(self, agent: Any, foreign: Any) -> list[str]:
        hooks: list[str] = []
        for method in ("invoke", "ainvoke", "stream", "astream", "batch"):
            if self._wrap_method(foreign, method, agent):
                hooks.append(method)
        return hooks
