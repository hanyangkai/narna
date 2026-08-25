"""narna-cmem — Works with CMEM / claude-mem MCP memory clients (complement, never replace)."""

from __future__ import annotations

from typing import Any

from .base import BaseAdapter


class CmemAdapter(BaseAdapter):
    id = "cmem"
    package = "narna-cmem"
    default_unit_kind = "mcp"

    def matches(self, obj: Any) -> bool:
        if obj is None:
            return False
        mod = (getattr(type(obj), "__module__", "") or "").lower()
        name = type(obj).__name__.lower()
        blob = f"{mod}.{name}"
        markers = (
            "cmem",
            "claude_mem",
            "claude-mem",
            "memoryclient",
            "memory_client",
            "observationstore",
        )
        if any(x in blob for x in markers):
            return True
        # MCP session pointed at CMEM via attribute
        for attr in ("cmem_url", "cmemUrl", "memory_url", "server_name", "serverName"):
            val = str(getattr(obj, attr, "") or "").lower()
            if any(x in val for x in ("cmem", "claude-mem", "claude_mem")):
                return True
        return False

    def _install_hooks(self, agent: Any, foreign: Any) -> list[str]:
        hooks: list[str] = []
        for method in (
            "call_tool",
            "callTool",
            "search",
            "recall",
            "query",
            "list_tools",
            "run",
            "invoke",
        ):
            if self._wrap_method(foreign, method, agent):
                hooks.append(method)
        return hooks
