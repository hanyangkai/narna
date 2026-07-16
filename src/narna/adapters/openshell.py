"""narna-openshell — Works with OpenShell / shell tool hosts."""

from __future__ import annotations

from typing import Any

from .base import BaseAdapter


class OpenShellAdapter(BaseAdapter):
    id = "openshell"
    package = "narna-openshell"

    def matches(self, obj: Any) -> bool:
        if obj is None:
            return False
        mod = (getattr(type(obj), "__module__", "") or "").lower()
        name = type(obj).__name__.lower()
        blob = f"{mod}.{name}"
        return any(x in blob for x in ("openshell", "open_shell", "shellsession", "terminals"))

    def _install_hooks(self, agent: Any, foreign: Any) -> list[str]:
        hooks: list[str] = []
        for method in ("run", "exec", "execute", "invoke", "call"):
            if self._wrap_method(foreign, method, agent):
                hooks.append(method)
        return hooks
