"""narna-mcp — Works with MCP servers / clients."""

from __future__ import annotations

from typing import Any

from .base import BaseAdapter


class McpAdapter(BaseAdapter):
    id = "mcp"
    package = "narna-mcp"

    def matches(self, obj: Any) -> bool:
        if obj is None:
            return False
        mod = (getattr(type(obj), "__module__", "") or "").lower()
        name = type(obj).__name__.lower()
        blob = f"{mod}.{name}"
        return any(x in blob for x in ("mcp.", "mcp.server", "mcp.client", "clientsession", "fastmcp"))

    def _install_hooks(self, agent: Any, foreign: Any) -> list[str]:
        hooks: list[str] = []
        for method in ("call_tool", "callTool", "list_tools", "run", "invoke"):
            if self._wrap_method(foreign, method, agent):
                hooks.append(method)
        return hooks
