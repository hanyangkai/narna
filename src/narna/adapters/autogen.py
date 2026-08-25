"""narna-autogen — Works with Microsoft AutoGen / AG2 agent patterns."""

from __future__ import annotations

from typing import Any

from .base import BaseAdapter


class AutogenAdapter(BaseAdapter):
    id = "autogen"
    package = "narna-autogen"
    default_unit_kind = "agent"

    def matches(self, obj: Any) -> bool:
        if obj is None:
            return False
        mod = (getattr(type(obj), "__module__", "") or "").lower()
        name = type(obj).__name__.lower()
        blob = f"{mod}.{name}"
        return any(
            x in blob
            for x in (
                "autogen",
                "ag2",
                "conversableagent",
                "assistantagent",
                "userproxyagent",
                "groupchat",
            )
        )

    def _install_hooks(self, agent: Any, foreign: Any) -> list[str]:
        hooks: list[str] = []
        for method in (
            "generate_reply",
            "a_generate_reply",
            "initiate_chat",
            "a_initiate_chat",
            "run",
            "invoke",
            "__call__",
        ):
            if self._wrap_method(foreign, method, agent):
                hooks.append(method)
        return hooks
