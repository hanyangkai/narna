"""narna-cmem — bridge CMEM continuity memory into NARNA Decision Quality."""

from __future__ import annotations

from typing import Any


def register(agent: Any) -> dict[str, Any]:
    agent._plugins = getattr(agent, "_plugins", {})
    agent._plugins["cmem"] = {
        "status": status,
        "search": search,
        "enrich": enrich,
        "ingest_local": ingest_local,
        "mcp_tools": mcp_tools,
    }
    return {"ok": True, "plugin": "narna-cmem", "role": "memory_feedstock"}


def _ws(agent: Any | None = None):
    if agent is not None and getattr(agent, "workspace", None):
        return agent.workspace
    from pathlib import Path

    return Path.cwd()


def status(agent: Any | None = None, **_kwargs: Any) -> dict[str, Any]:
    from uap.cmem_bridge import CmemBridge

    return CmemBridge(_ws(agent)).status()


def search(query: str, limit: int = 8, agent: Any | None = None, **_kwargs: Any) -> dict[str, Any]:
    from uap.cmem_bridge import CmemBridge

    hits = CmemBridge(_ws(agent)).search(query, limit=limit)
    return {"ok": True, "hits": hits, "count": len(hits)}


def enrich(action: str, limit: int = 8, agent: Any | None = None, **_kwargs: Any) -> dict[str, Any]:
    from uap.cmem_bridge import CmemBridge

    ctx = CmemBridge(_ws(agent)).enrich_context(action, limit=limit)
    return {"ok": True, "context": ctx}


def ingest_local(observation: dict[str, Any], agent: Any | None = None, **_kwargs: Any) -> dict[str, Any]:
    from uap.cmem_bridge import CmemBridge

    return CmemBridge(_ws(agent)).ingest_local(observation)


def mcp_tools(agent: Any | None = None, **_kwargs: Any) -> dict[str, Any]:
    from narna.mcp_tools import NarnaMcpTools

    tools = NarnaMcpTools(_ws(agent))
    return {"ok": True, "tools": tools.list_tools()}
