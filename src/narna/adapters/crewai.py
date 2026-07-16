"""narna-crewai — Works with CrewAI crews/agents."""

from __future__ import annotations

from typing import Any

from .base import BaseAdapter


class CrewAIAdapter(BaseAdapter):
    id = "crewai"
    package = "narna-crewai"

    def matches(self, obj: Any) -> bool:
        if obj is None:
            return False
        mod = (getattr(type(obj), "__module__", "") or "").lower()
        return "crewai" in mod

    def _install_hooks(self, agent: Any, foreign: Any) -> list[str]:
        hooks: list[str] = []
        for method in ("kickoff", "run", "invoke", "__call__"):
            if self._wrap_method(foreign, method, agent):
                hooks.append(method)
        return hooks
